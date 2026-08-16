"""Collect SME24 announcements and cross-check the Bizinfo collection.

The SME24 token is read at runtime from the project-local ``API정보.md``.
It is not written to outputs or printed. SME24 remains a cross-check source,
not standalone eligibility evidence.
"""

from __future__ import annotations

import argparse
import calendar
import csv
import hashlib
import json
import re
import time
import unicodedata
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


KST = timezone(timedelta(hours=9))
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_API_INFO = (
    PROJECT_ROOT
    / "RE 데이터 API 원본 다운로드"
    / "중소벤처24 공고 API"
    / "API정보.md"
)
DEFAULT_OUTPUT_ROOT = PROJECT_ROOT / "data" / "raw_re" / "policy" / "sme24"
DEFAULT_BIZINFO_DIR = PROJECT_ROOT / "data" / "raw_re" / "policy" / "bizinfo" / "2026-08-15"

SME24_FIELDS = [
    "pblancSeq", "creatDt", "pblancDtlUrl", "pblancNm", "detailBsnsNm",
    "policyCnts", "sportMg", "sportCnts", "sportTrget", "reqstRcept",
    "sportInsttNm", "sportInsttCd", "refrnc", "refrncUrl", "refrncDept",
    "refrncTel", "updDt", "pblancBgnDt", "pblancEndDt", "pblancAttach",
    "pblancAttachNm", "reqstLinkInfo", "bizType", "bizTypeCd", "sportType",
    "sportTypeCd", "lifeCyclDvsn", "lifeCyclDvsnCd", "areaNm", "areaCd",
    "salsAmt", "salsAmtCd", "minSalsAmt", "maxSalsAmt", "ablbiz", "ablbizCd",
    "minAblbiz", "maxAblbiz", "emplyCnt", "emplyCntCd", "minEmplyCnt",
    "mixEmplyCnt", "cmpScale", "cmpScaleCd", "needCrtfn", "needCrtfnCd",
    "cntcInsttNm", "cntcInsttCd", "induty", "rpsntAge", "minRpsntAge",
    "maxRpsntAge", "minInrst", "maxInrst", "minSportAmt", "maxSportAmt",
    "refntnYn", "fntnYn", "fmleRpsntYn", "pblancFileUrl", "pblancFileNm",
]

SMALL_BUSINESS_CODE_RULES = {
    "cmpScaleCd": {"CC30"},
    "needCrtfnCd": {"EC05"},
    "bizTypeCd": {"PC80"},
    "sportTypeCd": {"RT06"},
    "sportInsttCd": {"SP05"},
}
SMALL_BUSINESS_TEXT_FIELDS = (
    "cmpScale", "needCrtfn", "bizType", "sportType", "sportTrget",
    "sportInsttNm", "pblancNm", "detailBsnsNm", "policyCnts", "sportCnts",
)


def parse_args() -> argparse.Namespace:
    today = datetime.now(KST).date()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api-info", type=Path, default=DEFAULT_API_INFO)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--bizinfo-dir", type=Path, default=DEFAULT_BIZINFO_DIR)
    parser.add_argument("--start-date", default=f"{today.year}-01-01")
    parser.add_argument("--end-date", default=today.isoformat())
    parser.add_argument("--collection-date", default=today.isoformat())
    parser.add_argument(
        "--collected-at-kst",
        help="Preserve the actual API collection timestamp when rebuilding derivatives",
    )
    parser.add_argument("--timeout", type=float, default=45.0)
    parser.add_argument("--retries", type=int, default=4)
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Reuse validated window JSON files from a partial run",
    )
    parser.add_argument(
        "--rebuild-derived",
        action="store_true",
        help="Rebuild derived files from complete existing windows without API calls",
    )
    return parser.parse_args()


def parse_iso_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def read_api_config(path: Path) -> tuple[str, str]:
    text = path.read_text(encoding="utf-8")
    endpoint_match = re.search(
        r"https://portal\.smes\.go\.kr/ione-gw/api/pblanc/list", text
    )
    token_match = re.search(r"(?m)^인증키\s*:\s*(\S+)\s*$", text)
    if not endpoint_match or not token_match:
        raise ValueError(f"Endpoint or token was not found in {path}")
    return endpoint_match.group(0), token_match.group(1)


def month_windows(start: date, end: date) -> list[tuple[date, date]]:
    windows: list[tuple[date, date]] = []
    cursor = start
    while cursor <= end:
        month_end = date(
            cursor.year, cursor.month, calendar.monthrange(cursor.year, cursor.month)[1]
        )
        window_end = min(month_end, end)
        windows.append((cursor, window_end))
        cursor = window_end + timedelta(days=1)
    return windows


def request_window(
    endpoint: str,
    token: str,
    start: date,
    end: date,
    timeout: float,
    retries: int,
) -> tuple[bytes, dict[str, Any]]:
    params = {
        "token": token,
        "strDt": start.strftime("%Y%m%d"),
        "endDt": end.strftime("%Y%m%d"),
        "html": "yes",
    }
    request = Request(
        endpoint + "?" + urlencode(params),
        headers={"User-Agent": "financial-ai-challenge-sme24/1.0"},
    )
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            with urlopen(request, timeout=timeout) as response:
                raw = response.read()
            payload = json.loads(raw.decode("utf-8-sig"))
            if not isinstance(payload, dict):
                raise ValueError("SME24 response root is not an object")
            result = payload.get("result", payload)
            if not isinstance(result, dict):
                raise ValueError("SME24 response result is not an object")
            return raw, result
        except (HTTPError, URLError, TimeoutError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            last_error = exc
            if attempt < retries:
                time.sleep(min(2 ** (attempt - 1), 8))
    raise RuntimeError(
        f"SME24 request failed for {start}..{end} after {retries} attempts: "
        f"{type(last_error).__name__}"
    ) from last_error


def collect_successful_windows(
    endpoint: str,
    token: str,
    initial_windows: list[tuple[date, date]],
    windows_dir: Path,
    timeout: float,
    retries: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    queue = list(initial_windows)
    items: list[dict[str, Any]] = []
    records: list[dict[str, Any]] = []
    while queue:
        start, end = queue.pop(0)
        path = windows_dir / f"window_{start:%Y%m%d}_{end:%Y%m%d}.json"
        reused = path.is_file()
        if reused:
            raw = path.read_bytes()
            root = json.loads(raw.decode("utf-8-sig"))
            payload = root.get("result", root)
            if not isinstance(payload, dict):
                raise ValueError(f"Existing window has an invalid result object: {path}")
        else:
            raw, payload = request_window(endpoint, token, start, end, timeout, retries)
        result_code = str(payload.get("resultCd", ""))
        if result_code == "13" and start < end:
            midpoint = start + (end - start) // 2
            queue[0:0] = [(start, midpoint), (midpoint + timedelta(days=1), end)]
            print(f"Split rejected date range {start}..{end}")
            continue
        if result_code != "0":
            raise RuntimeError(
                f"SME24 API error for {start}..{end}: "
                f"resultCd={result_code!r}, resultMsg={payload.get('resultMsg', '')!r}"
            )
        data = payload.get("data") or []
        if not isinstance(data, list) or not all(isinstance(row, dict) for row in data):
            raise ValueError(f"Unexpected SME24 data structure for {start}..{end}")
        if not reused:
            path.write_bytes(raw)
        items.extend(data)
        records.append(
            {
                "start_date": start.isoformat(),
                "end_date": end.isoformat(),
                "item_count": len(data),
                "result_code": result_code,
                "result_message": str(payload.get("resultMsg", "")),
                "creat_date_in_window_count": sum(
                    date_in_window(row.get("creatDt"), start, end) for row in data
                ),
                "update_date_in_window_count": sum(
                    date_in_window(row.get("updDt"), start, end) for row in data
                ),
                "file": path.name,
                "sha256": sha256(path),
            }
        )
        action = "Reused" if reused else "Saved"
        print(f"{action} {start}..{end}: {len(data)} items")
    records.sort(key=lambda row: row["start_date"])
    return items, records


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize_scalar(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (list, dict)):
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    return str(value)


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: normalize_scalar(row.get(field)) for field in fields})


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")


def split_codes(value: Any) -> set[str]:
    return {
        part.strip()
        for part in re.split(r"[|,;/\s]+", str(value or ""))
        if part.strip()
    }


def classify_small_business(row: dict[str, Any]) -> dict[str, str] | None:
    code_matches: list[str] = []
    for field, expected in SMALL_BUSINESS_CODE_RULES.items():
        found = split_codes(row.get(field)) & expected
        if found:
            code_matches.append(f"{field}:{'|'.join(sorted(found))}")
    text_matches = [
        field
        for field in SMALL_BUSINESS_TEXT_FIELDS
        if "소상공인" in str(row.get(field) or "")
    ]
    if code_matches:
        tier = "explicit_code"
    elif text_matches:
        tier = "explicit_text"
    else:
        return None
    area_codes = split_codes(row.get("areaCd"))
    if "1100" in area_codes:
        seoul_scope = "seoul_explicit"
    elif "1000" in area_codes:
        seoul_scope = "nationwide_possible"
    elif area_codes:
        seoul_scope = "other_region_or_review"
    else:
        seoul_scope = "area_unspecified_review"
    return {
        "candidate_tier": tier,
        "candidate_code_matches": ";".join(code_matches),
        "candidate_text_fields": "|".join(text_matches),
        "seoul_scope": seoul_scope,
        "eligibility_status": "교차확인용_공식원문재검증필요",
    }


def normalize_title(value: Any) -> str:
    text = unicodedata.normalize("NFKC", str(value or "")).casefold()
    return "".join(character for character in text if character.isalnum())


def date_part(value: Any) -> str:
    match = re.search(r"(20\d{2})[-./]?(\d{2})[-./]?(\d{2})", str(value or ""))
    return "-".join(match.groups()) if match else ""


def date_in_window(value: Any, start: date, end: date) -> bool:
    parsed = date_part(value)
    if not parsed:
        return False
    current = parse_iso_date(parsed)
    return start <= current <= end


def bizinfo_period(value: Any) -> tuple[str, str]:
    dates = re.findall(r"(20\d{2})[-./]?(\d{2})[-./]?(\d{2})", str(value or ""))
    normalized = ["-".join(parts) for parts in dates]
    return (
        normalized[0] if normalized else "",
        normalized[1] if len(normalized) > 1 else "",
    )


def same_agency(sme: dict[str, Any], biz: dict[str, Any]) -> str:
    left = normalize_title(sme.get("sportInsttNm"))
    rights = [normalize_title(biz.get("jrsdInsttNm")), normalize_title(biz.get("excInsttNm"))]
    if not left or not any(rights):
        return "unknown"
    return "yes" if any(left == right or left in right or right in left for right in rights if right) else "no"


def derived_application_status(row: dict[str, Any], as_of: date) -> str:
    start_text = date_part(row.get("pblancBgnDt"))
    end_text = date_part(row.get("pblancEndDt"))
    if not start_text or not end_text:
        return "unknown"
    start, end = parse_iso_date(start_text), parse_iso_date(end_text)
    if as_of < start:
        return "scheduled_by_date"
    if as_of > end:
        return "closed_by_date"
    return "open_by_date"


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def build_crosswalk(
    sme_items: list[dict[str, Any]],
    bizinfo_items: list[dict[str, str]],
    bizinfo_candidate_ids: set[str],
    as_of: date,
) -> list[dict[str, Any]]:
    biz_by_title: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in bizinfo_items:
        key = normalize_title(row.get("pblancNm"))
        if key:
            biz_by_title[key].append(row)
    rows: list[dict[str, Any]] = []
    for sme in sme_items:
        key = normalize_title(sme.get("pblancNm"))
        for biz in biz_by_title.get(key, []):
            biz_start, biz_end = bizinfo_period(biz.get("reqstBeginEndDe"))
            sme_start = date_part(sme.get("pblancBgnDt"))
            sme_end = date_part(sme.get("pblancEndDt"))
            rows.append(
                {
                    "title_match_method": "nfkc_casefold_alnum_exact",
                    "normalized_title": key,
                    "sme24_pblancSeq": sme.get("pblancSeq"),
                    "sme24_pblancNm": sme.get("pblancNm"),
                    "bizinfo_pblancId": biz.get("pblancId"),
                    "bizinfo_pblancNm": biz.get("pblancNm"),
                    "is_bizinfo_small_business_candidate": (
                        "yes" if str(biz.get("pblancId")) in bizinfo_candidate_ids else "no"
                    ),
                    "sme24_creatDt": sme.get("creatDt"),
                    "bizinfo_creatPnttm": biz.get("creatPnttm"),
                    "created_date_match": (
                        "yes"
                        if date_part(sme.get("creatDt"))
                        and date_part(sme.get("creatDt")) == date_part(biz.get("creatPnttm"))
                        else "no_or_unknown"
                    ),
                    "sme24_sportInsttNm": sme.get("sportInsttNm"),
                    "bizinfo_jrsdInsttNm": biz.get("jrsdInsttNm"),
                    "bizinfo_excInsttNm": biz.get("excInsttNm"),
                    "agency_match": same_agency(sme, biz),
                    "sme24_application_start": sme_start,
                    "bizinfo_application_start": biz_start,
                    "application_start_match": (
                        "yes" if sme_start and sme_start == biz_start else "no_or_unknown"
                    ),
                    "sme24_application_end": sme_end,
                    "bizinfo_application_end": biz_end,
                    "application_end_match": (
                        "yes" if sme_end and sme_end == biz_end else "no_or_unknown"
                    ),
                    "sme24_status_derived_from_dates": derived_application_status(sme, as_of),
                    "sme24_attachment_present": (
                        "yes" if sme.get("pblancAttach") or sme.get("pblancFileUrl") else "no"
                    ),
                    "bizinfo_attachment_present": (
                        "yes" if biz.get("fileNm") or biz.get("printFileNm") else "no"
                    ),
                    "sme24_detail_url": sme.get("pblancDtlUrl"),
                    "bizinfo_detail_url": biz.get("pblancUrl"),
                    "crosscheck_status": "exact_title_candidate_not_official_validation",
                }
            )
    return rows


def main() -> int:
    args = parse_args()
    start_date, end_date = parse_iso_date(args.start_date), parse_iso_date(args.end_date)
    if start_date > end_date:
        raise ValueError("start-date must not be after end-date")
    output_dir = args.output_root.resolve() / args.collection_date
    windows_dir = output_dir / "windows"
    allow_existing = args.resume or args.rebuild_derived
    if output_dir.exists() and any(output_dir.iterdir()) and not allow_existing:
        raise FileExistsError(f"Refusing to overwrite non-empty directory: {output_dir}")
    if args.resume and not args.rebuild_derived and (output_dir / "manifest.json").is_file():
        raise FileExistsError(f"Collection already has a manifest and is complete: {output_dir}")
    windows_dir.mkdir(parents=True, exist_ok=True)

    collected_at_iso = args.collected_at_kst or datetime.now(KST).isoformat(timespec="seconds")
    previous_manifest_path = output_dir / "manifest.json"
    if args.rebuild_derived and args.collected_at_kst is None and previous_manifest_path.is_file():
        previous_manifest = json.loads(previous_manifest_path.read_text(encoding="utf-8"))
        collected_at_iso = str(previous_manifest.get("collected_at_kst") or collected_at_iso)

    endpoint, token = read_api_config(args.api_info.resolve())
    raw_items, window_records = collect_successful_windows(
        endpoint,
        token,
        month_windows(start_date, end_date),
        windows_dir,
        args.timeout,
        args.retries,
    )
    raw_count = len(raw_items)
    sequence_values = [str(row.get("pblancSeq") or "").strip() for row in raw_items]
    nonempty_sequences = [value for value in sequence_values if value]
    duplicate_sequence_count = len(nonempty_sequences) - len(set(nonempty_sequences))
    unique_by_sequence: dict[str, dict[str, Any]] = {}
    rows_without_sequence: list[dict[str, Any]] = []
    for row in raw_items:
        sequence = str(row.get("pblancSeq") or "").strip()
        if sequence:
            unique_by_sequence.setdefault(sequence, row)
        else:
            rows_without_sequence.append(row)
    all_items = list(unique_by_sequence.values()) + rows_without_sequence
    all_items.sort(key=lambda row: (str(row.get("creatDt") or ""), str(row.get("pblancSeq") or "")))

    candidates: list[dict[str, Any]] = []
    for row in all_items:
        classification = classify_small_business(row)
        if classification is not None:
            enriched = dict(row)
            enriched.update(classification)
            candidates.append(enriched)

    all_jsonl = output_dir / "all_items.jsonl"
    all_csv = output_dir / "all_items.csv"
    candidate_jsonl = output_dir / "small_business_candidates.jsonl"
    candidate_csv = output_dir / "small_business_candidates.csv"
    write_jsonl(all_jsonl, all_items)
    write_csv(all_csv, all_items, SME24_FIELDS)
    candidate_extra = [
        "candidate_tier", "candidate_code_matches", "candidate_text_fields",
        "seoul_scope", "eligibility_status",
    ]
    write_jsonl(candidate_jsonl, candidates)
    write_csv(candidate_csv, candidates, SME24_FIELDS + candidate_extra)

    bizinfo_dir = args.bizinfo_dir.resolve()
    bizinfo_items = load_csv(bizinfo_dir / "current_year_2026_items.csv")
    bizinfo_candidate_rows = load_csv(bizinfo_dir / "small_business_candidates.csv")
    bizinfo_candidate_ids = {row["pblancId"] for row in bizinfo_candidate_rows}
    crosswalk = build_crosswalk(all_items, bizinfo_items, bizinfo_candidate_ids, end_date)
    crosswalk_fields = list(crosswalk[0].keys()) if crosswalk else [
        "title_match_method", "normalized_title", "sme24_pblancSeq", "sme24_pblancNm",
        "bizinfo_pblancId", "bizinfo_pblancNm", "is_bizinfo_small_business_candidate",
        "crosscheck_status",
    ]
    crosswalk_csv = output_dir / "bizinfo_exact_title_crosswalk.csv"
    write_csv(crosswalk_csv, crosswalk, crosswalk_fields)
    candidate_crosswalk = [
        row for row in crosswalk if row["is_bizinfo_small_business_candidate"] == "yes"
    ]
    candidate_crosswalk_csv = output_dir / "bizinfo_candidate_exact_title_crosswalk.csv"
    write_csv(candidate_crosswalk_csv, candidate_crosswalk, crosswalk_fields)

    matched_bizinfo_candidate_ids = {
        str(row["bizinfo_pblancId"]) for row in candidate_crosswalk
    }
    unmatched_bizinfo_candidates = [
        dict(row, crosscheck_status="no_exact_normalized_title_match_in_sme24")
        for row in bizinfo_candidate_rows
        if row["pblancId"] not in matched_bizinfo_candidate_ids
    ]
    unmatched_bizinfo_csv = output_dir / "bizinfo_candidates_without_exact_sme24_match.csv"
    write_csv(
        unmatched_bizinfo_csv,
        unmatched_bizinfo_candidates,
        list(bizinfo_candidate_rows[0].keys()) + ["crosscheck_status"],
    )

    matched_sme_sequences = {str(row["sme24_pblancSeq"]) for row in crosswalk}
    unmatched_sme_candidates = [
        dict(row, crosscheck_status="no_exact_normalized_title_match_in_bizinfo")
        for row in candidates
        if str(row.get("pblancSeq") or "") not in matched_sme_sequences
    ]
    unmatched_sme_csv = output_dir / "sme24_small_business_candidates_without_exact_bizinfo_match.csv"
    write_csv(
        unmatched_sme_csv,
        unmatched_sme_candidates,
        SME24_FIELDS + candidate_extra + ["crosscheck_status"],
    )

    year_counts = Counter(date_part(row.get("creatDt"))[:4] or "unknown" for row in all_items)
    update_year_counts = Counter(date_part(row.get("updDt"))[:4] or "unknown" for row in all_items)
    candidate_tier_counts = Counter(row["candidate_tier"] for row in candidates)
    seoul_scope_counts = Counter(row["seoul_scope"] for row in candidates)
    field_nonempty_counts = {
        field: sum(bool(str(row.get(field) or "").strip()) for row in all_items)
        for field in SME24_FIELDS
    }
    derived_files = [
        all_jsonl, all_csv, candidate_jsonl, candidate_csv, crosswalk_csv,
        candidate_crosswalk_csv, unmatched_bizinfo_csv, unmatched_sme_csv,
    ]
    manifest = {
        "source_name": "중소기업기술정보진흥원_중소벤처24 공고정보",
        "source_role": "P1 cross-check only; not standalone eligibility evidence",
        "endpoint": endpoint,
        "collected_at_kst": collected_at_iso,
        "collection_date": args.collection_date,
        "requested_date_range": {"start": start_date.isoformat(), "end": end_date.isoformat()},
        "request_parameters_without_token": {"html": "yes"},
        "access_validation": "success_with_provided_token",
        "daily_call_limit": None,
        "daily_call_limit_status": "not specified in the provided API information",
        "successful_windows": len(window_records),
        "raw_item_count": raw_count,
        "unique_item_count": len(all_items),
        "nonempty_sequence_count": len(nonempty_sequences),
        "duplicate_sequence_count": duplicate_sequence_count,
        "registration_year_counts": dict(sorted(year_counts.items())),
        "update_year_counts": dict(sorted(update_year_counts.items())),
        "query_date_field_observation": (
            "All returned records had updDt inside their request window; strDt/endDt behaves as an update-date filter."
        ),
        "all_update_dates_inside_request_windows": all(
            row["update_date_in_window_count"] == row["item_count"]
            for row in window_records
        ),
        "small_business_candidate_count": len(candidates),
        "candidate_tier_counts": dict(candidate_tier_counts),
        "candidate_seoul_scope_counts": dict(seoul_scope_counts),
        "bizinfo_2026_count": len(bizinfo_items),
        "bizinfo_small_business_candidate_count": len(bizinfo_candidate_rows),
        "exact_title_crosswalk_row_count": len(crosswalk),
        "matched_unique_bizinfo_ids": len({row["bizinfo_pblancId"] for row in crosswalk}),
        "matched_unique_sme24_sequences": len({str(row["sme24_pblancSeq"]) for row in crosswalk}),
        "matched_bizinfo_candidate_id_count": len(matched_bizinfo_candidate_ids),
        "unmatched_bizinfo_candidate_count": len(unmatched_bizinfo_candidates),
        "unmatched_sme24_small_business_candidate_count": len(unmatched_sme_candidates),
        "match_policy": (
            "NFKC + casefold + remove non-alphanumeric, then exact title match only; no fuzzy matching"
        ),
        "status_notice": (
            "Application status is derived from start/end dates as of range end; it is not an explicit API status field."
        ),
        "field_nonempty_counts": field_nonempty_counts,
        "windows": window_records,
        "derived_files": {
            path.name: {"sha256": sha256(path), "bytes": path.stat().st_size}
            for path in derived_files
        },
        "token_stored_in_output": False,
    }
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    qa_lines = [
        "# 중소벤처24 공고 API 수집·교차확인 QA",
        "",
        f"- 수집시각(KST): `{manifest['collected_at_kst']}`",
        f"- 요청기간: `{start_date}` ~ `{end_date}`",
        f"- 성공 구간: `{len(window_records)}`",
        f"- 원본 응답 항목: `{raw_count}`",
        f"- 고유 공고: `{len(all_items)}`",
        f"- 공고SEQ 중복: `{duplicate_sequence_count}`",
        f"- 등록연도 분포: `{json.dumps(dict(sorted(year_counts.items())), ensure_ascii=False)}`",
        f"- 수정연도 분포: `{json.dumps(dict(sorted(update_year_counts.items())), ensure_ascii=False)}`",
        "- 날짜 파라미터 관찰: 모든 응답의 `updDt`가 해당 요청 구간 안에 있어 `strDt/endDt`는 수정일 필터로 동작함",
        "- 따라서 등록일이 과거이거나 비어 있는 공고도 2026년에 갱신됐다면 원본 범위에 포함함",
        f"- 중소벤처24 소상공인 검토 후보: `{len(candidates)}`",
        f"- 기업마당 전체 정확 제목 교차일치: `{len(crosswalk)}`행",
        f"- 기업마당 소상공인 후보 중 정확 제목 교차일치: `{len(matched_bizinfo_candidate_ids)}`/`{len(bizinfo_candidate_rows)}`건",
        f"- 기업마당 후보 미일치: `{len(unmatched_bizinfo_candidates)}`건",
        "- 매칭은 제목의 유니코드·대소문자·공백·문장부호만 정규화한 정확 일치이며 유사도 추정은 하지 않음",
        "- 접수상태는 명시 필드가 없어 조회 종료일 기준 신청 시작·종료일로만 파생하며 공식 상태로 간주하지 않음",
        "- 중소벤처24 응답은 교차확인용이며 단독 자격근거로 사용하지 않음",
        "- 인증키는 산출물에 저장하지 않음",
        "",
    ]
    (output_dir / "QA.md").write_text("\n".join(qa_lines), encoding="utf-8")
    print(
        json.dumps(
            {
                "output_dir": str(output_dir),
                "unique_items": len(all_items),
                "small_business_candidates": len(candidates),
                "exact_crosswalk_rows": len(crosswalk),
                "matched_bizinfo_candidates": len(matched_bizinfo_candidate_ids),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
