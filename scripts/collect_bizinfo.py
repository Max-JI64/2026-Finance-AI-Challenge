"""Collect the current-year Bizinfo support-announcement feed.

The data.go.kr service key is read at runtime from the project-local
``API정보.md`` file. It is never copied into output files or logs.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import unquote, urlencode
from urllib.request import Request, urlopen


KST = timezone(timedelta(hours=9))
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_API_INFO = (
    PROJECT_ROOT
    / "RE 데이터 API 원본 다운로드"
    / "기업마당 중소기업 지원사업 공고 API"
    / "API정보.md"
)
DEFAULT_OUTPUT_ROOT = PROJECT_ROOT / "data" / "raw_re" / "policy" / "bizinfo"
SOURCE_FIELDS = [
    "pblancNm",
    "pblancUrl",
    "pblancId",
    "jrsdInsttNm",
    "excInsttNm",
    "bsnsSumryCn",
    "pldirSportRealmLclasCodeNm",
    "creatPnttm",
    "reqstBeginEndDe",
    "updtPnttm",
    "trgetNm",
    "inqireCo",
    "flpthNm",
    "fileNm",
    "printFlpthNm",
    "printFileNm",
    "hashtags",
    "reqstMthPapersCn",
    "refrncNm",
    "rceptEngnHmpgUrl",
]

# These rules only identify records for later manual source verification.
# They do not establish policy eligibility.
EXPLICIT_TERM = "소상공인"
AGENCY_TERMS = ("소상공인시장진흥공단", "소진공")
ADJACENT_TERMS = ("자영업", "영세사업자", "전통시장", "상점가", "골목상권")
CORE_FILTER_FIELDS = (
    "trgetNm",
    "hashtags",
    "pldirSportRealmLclasCodeNm",
    "jrsdInsttNm",
    "excInsttNm",
)
DISCOVERY_FIELDS = ("pblancNm", "bsnsSumryCn", "reqstMthPapersCn")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api-info", type=Path, default=DEFAULT_API_INFO)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--collection-date", help="KST date in YYYY-MM-DD form")
    parser.add_argument(
        "--collected-at-kst",
        help="Preserve an actual collection timestamp when rebuilding existing derivatives",
    )
    parser.add_argument("--expected-year", type=int, default=datetime.now(KST).year)
    parser.add_argument("--num-rows", type=int, default=1000)
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--retries", type=int, default=4)
    parser.add_argument(
        "--from-existing",
        type=Path,
        help="Rebuild derived files and QA from an existing pages directory without API calls",
    )
    return parser.parse_args()


def read_api_config(path: Path) -> tuple[str, str]:
    text = path.read_text(encoding="utf-8")
    endpoint_match = re.search(r"https://apis\.data\.go\.kr/1421000/bizinfo", text)
    key_match = re.search(r"(?m)^([A-Za-z0-9_%+-]+%3D%3D)\s*$", text)
    if not endpoint_match or not key_match:
        raise ValueError(f"Endpoint or service key was not found in {path}")
    endpoint = endpoint_match.group(0).rstrip("/") + "/pblancBsnsService"
    return endpoint, unquote(key_match.group(1))


def fetch_page(
    endpoint: str,
    service_key: str,
    page_no: int,
    num_rows: int,
    timeout: float,
    retries: int,
) -> bytes:
    params = {
        "serviceKey": service_key,
        "dataType": "json",
        "pageNo": str(page_no),
        "numOfRows": str(num_rows),
    }
    url = endpoint + "?" + urlencode(params)
    request = Request(url, headers={"User-Agent": "financial-ai-challenge-bizinfo/1.0"})
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            with urlopen(request, timeout=timeout) as response:
                return response.read()
        except (HTTPError, URLError, TimeoutError) as exc:
            last_error = exc
            if attempt < retries:
                time.sleep(min(2 ** (attempt - 1), 8))
    raise RuntimeError(
        f"Page {page_no} failed after {retries} attempts: "
        f"{type(last_error).__name__}"
    ) from last_error


def response_parts(raw: bytes) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]]]:
    try:
        payload = json.loads(raw.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("The API response was not valid UTF-8 JSON") from exc

    response = payload.get("response", payload)
    header = response.get("header") or {}
    body = response.get("body") or {}
    result_code = str(header.get("resultCode", ""))
    if result_code not in {"0", "00"}:
        raise RuntimeError(
            f"API error resultCode={result_code!r}, "
            f"resultMsg={header.get('resultMsg', '')!r}"
        )

    items_container = body.get("items") or {}
    items: Any
    if isinstance(items_container, dict):
        items = items_container.get("item", [])
    else:
        items = items_container
    if items is None:
        items = []
    if isinstance(items, dict):
        items = [items]
    if not isinstance(items, list) or not all(isinstance(item, dict) for item in items):
        raise ValueError("Unexpected body.items.item structure")
    return header, body, items


def as_int(value: Any, default: int = 0) -> int:
    try:
        return int(str(value).replace(",", ""))
    except (TypeError, ValueError):
        return default


def classify_candidate(item: dict[str, Any]) -> dict[str, str] | None:
    explicit_core_fields: list[str] = []
    explicit_discovery_fields: list[str] = []
    agency_fields: list[str] = []
    adjacent_matches: list[str] = []

    for field in CORE_FILTER_FIELDS:
        value = str(item.get(field) or "")
        if EXPLICIT_TERM in value:
            explicit_core_fields.append(field)
        if any(term in value for term in AGENCY_TERMS):
            agency_fields.append(field)

    for field in DISCOVERY_FIELDS:
        value = str(item.get(field) or "")
        if EXPLICIT_TERM in value:
            explicit_discovery_fields.append(field)
        for term in ADJACENT_TERMS:
            if term in value:
                adjacent_matches.append(f"{field}:{term}")

    if explicit_core_fields or agency_fields:
        tier = "explicit_core"
    elif explicit_discovery_fields:
        tier = "explicit_discovery"
    elif adjacent_matches:
        tier = "adjacent_review"
    else:
        return None

    fields = sorted(set(explicit_core_fields + explicit_discovery_fields + agency_fields))
    reasons: list[str] = []
    if explicit_core_fields:
        reasons.append("소상공인 명시:" + ",".join(explicit_core_fields))
    if agency_fields:
        reasons.append("소진공 기관 일치:" + ",".join(agency_fields))
    if explicit_discovery_fields:
        reasons.append("탐색본문 소상공인 일치:" + ",".join(explicit_discovery_fields))
    if adjacent_matches:
        reasons.append("인접키워드:" + ",".join(sorted(set(adjacent_matches))))
    return {
        "candidate_tier": tier,
        "candidate_match_fields": "|".join(fields),
        "candidate_reason": "; ".join(reasons),
        "eligibility_status": "미확정_공식원문재검증필요",
    }


def normalize_for_csv(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    return str(value)


def write_csv(path: Path, items: list[dict[str, Any]], extra_fields: list[str] | None = None) -> None:
    fields = SOURCE_FIELDS + (extra_fields or [])
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for item in items:
            writer.writerow({field: normalize_for_csv(item.get(field)) for field in fields})


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def extract_year(value: Any) -> str:
    match = re.search(r"(20\d{2})", str(value or ""))
    return match.group(1) if match else "unknown"


def main() -> int:
    args = parse_args()
    collected_at = datetime.now(KST)
    collected_at_iso = args.collected_at_kst or collected_at.isoformat(timespec="seconds")
    collection_date = args.collection_date or collected_at.date().isoformat()
    output_dir = (
        args.from_existing.resolve()
        if args.from_existing is not None
        else args.output_root.resolve() / collection_date
    )
    pages_dir = output_dir / "pages"
    if args.from_existing is None and output_dir.exists() and any(output_dir.iterdir()):
        raise FileExistsError(
            f"Refusing to overwrite a non-empty collection directory: {output_dir}"
        )
    if args.from_existing is not None and not pages_dir.is_dir():
        raise FileNotFoundError(f"Existing pages directory was not found: {pages_dir}")
    previous_manifest_path = output_dir / "manifest.json"
    if (
        args.from_existing is not None
        and args.collected_at_kst is None
        and previous_manifest_path.is_file()
    ):
        previous_manifest = json.loads(previous_manifest_path.read_text(encoding="utf-8"))
        collected_at_iso = str(previous_manifest.get("collected_at_kst") or collected_at_iso)
    pages_dir.mkdir(parents=True, exist_ok=True)

    endpoint = "https://apis.data.go.kr/1421000/bizinfo/pblancBsnsService"
    all_items: list[dict[str, Any]] = []
    page_records: list[dict[str, Any]] = []

    if args.from_existing is not None:
        page_paths = sorted(pages_dir.glob("page_*.json"))
        if not page_paths:
            raise FileNotFoundError(f"No page_*.json files were found in {pages_dir}")
        total_count = 0
        response_page_size = 0
        for page_no, page_path in enumerate(page_paths, start=1):
            raw = page_path.read_bytes()
            header, body, items = response_parts(raw)
            if page_no == 1:
                total_count = as_int(body.get("totalCount"))
                response_page_size = as_int(body.get("numOfRows"), len(items))
            all_items.extend(items)
            page_records.append(
                {
                    "page_no": page_no,
                    "item_count": len(items),
                    "result_code": str(header.get("resultCode", "")),
                    "reported_total_count": as_int(body.get("totalCount")),
                    "sha256": sha256(page_path),
                }
            )
            print(f"Read existing page {page_no}/{len(page_paths)}: {len(items)} items")
    else:
        endpoint, service_key = read_api_config(args.api_info.resolve())
        first_raw = fetch_page(
            endpoint, service_key, 1, args.num_rows, args.timeout, args.retries
        )
        first_header, first_body, first_items = response_parts(first_raw)
        total_count = as_int(first_body.get("totalCount"))
        response_page_size = as_int(first_body.get("numOfRows"), len(first_items))
        if response_page_size <= 0:
            response_page_size = args.num_rows
        total_pages = max(1, math.ceil(total_count / response_page_size))

        for page_no in range(1, total_pages + 1):
            if page_no == 1:
                raw, header, body, items = first_raw, first_header, first_body, first_items
            else:
                raw = fetch_page(
                    endpoint,
                    service_key,
                    page_no,
                    args.num_rows,
                    args.timeout,
                    args.retries,
                )
                header, body, items = response_parts(raw)
            page_path = pages_dir / f"page_{page_no:04d}.json"
            page_path.write_bytes(raw)
            all_items.extend(items)
            page_records.append(
                {
                    "page_no": page_no,
                    "item_count": len(items),
                    "result_code": str(header.get("resultCode", "")),
                    "reported_total_count": as_int(body.get("totalCount")),
                    "sha256": sha256(page_path),
                }
            )
            print(f"Saved page {page_no}/{total_pages}: {len(items)} items")

    ids = [str(item.get("pblancId") or "").strip() for item in all_items]
    nonempty_ids = [value for value in ids if value]
    duplicate_id_count = len(nonempty_ids) - len(set(nonempty_ids))

    current_year_items = [
        item
        for item in all_items
        if extract_year(item.get("creatPnttm")) == str(args.expected_year)
    ]
    all_response_candidate_count = sum(
        classify_candidate(item) is not None for item in all_items
    )
    candidates: list[dict[str, Any]] = []
    tier_counts: dict[str, int] = {}
    for item in current_year_items:
        classification = classify_candidate(item)
        if classification is None:
            continue
        enriched = dict(item)
        enriched.update(classification)
        candidates.append(enriched)
        tier = classification["candidate_tier"]
        tier_counts[tier] = tier_counts.get(tier, 0) + 1

    all_jsonl = output_dir / "all_items.jsonl"
    with all_jsonl.open("w", encoding="utf-8", newline="\n") as handle:
        for item in all_items:
            handle.write(json.dumps(item, ensure_ascii=False, separators=(",", ":")) + "\n")
    all_csv = output_dir / "all_items.csv"
    write_csv(all_csv, all_items)

    current_year_jsonl = output_dir / f"current_year_{args.expected_year}_items.jsonl"
    with current_year_jsonl.open("w", encoding="utf-8", newline="\n") as handle:
        for item in current_year_items:
            handle.write(json.dumps(item, ensure_ascii=False, separators=(",", ":")) + "\n")
    current_year_csv = output_dir / f"current_year_{args.expected_year}_items.csv"
    write_csv(current_year_csv, current_year_items)

    candidate_jsonl = output_dir / "small_business_candidates.jsonl"
    with candidate_jsonl.open("w", encoding="utf-8", newline="\n") as handle:
        for item in candidates:
            handle.write(json.dumps(item, ensure_ascii=False, separators=(",", ":")) + "\n")
    candidate_csv = output_dir / "small_business_candidates.csv"
    extra_fields = [
        "candidate_tier",
        "candidate_match_fields",
        "candidate_reason",
        "eligibility_status",
    ]
    write_csv(candidate_csv, candidates, extra_fields)

    year_counts: dict[str, int] = {}
    for item in all_items:
        year = extract_year(item.get("creatPnttm"))
        year_counts[year] = year_counts.get(year, 0) + 1

    field_nonempty_counts = {
        field: sum(bool(str(item.get(field) or "").strip()) for item in all_items)
        for field in SOURCE_FIELDS
    }
    derived_paths = [
        all_jsonl,
        all_csv,
        current_year_jsonl,
        current_year_csv,
        candidate_jsonl,
        candidate_csv,
    ]
    manifest = {
        "source_name": "중소벤처기업부_중소기업 지원사업 공고 조회 서비스",
        "endpoint": endpoint,
        "collected_at_kst": collected_at_iso,
        "collection_date": collection_date,
        "expected_current_year": args.expected_year,
        "request_scope": (
            "all advertised response pages preserved; expected-year records separately derived"
        ),
        "request_parameters_without_service_key": {
            "dataType": "json",
            "numOfRows": args.num_rows,
        },
        "access_validation": "success_with_provided_key",
        "daily_call_limit": None,
        "daily_call_limit_status": "not specified in the provided API information",
        "reported_total_count": total_count,
        "response_page_size": response_page_size,
        "pages_saved": len(page_records),
        "raw_item_count": len(all_items),
        "nonempty_id_count": len(nonempty_ids),
        "unique_nonempty_id_count": len(set(nonempty_ids)),
        "duplicate_id_count": duplicate_id_count,
        "registration_year_counts": year_counts,
        "expected_year_item_count": len(current_year_items),
        "out_of_scope_year_item_count": len(all_items) - len(current_year_items),
        "all_response_candidate_count": all_response_candidate_count,
        "candidate_count": len(candidates),
        "candidate_tier_counts": tier_counts,
        "candidate_filter_notice": (
            "Discovery-only filter. Eligibility and financial terms require official notice validation."
        ),
        "field_nonempty_counts": field_nonempty_counts,
        "pages": page_records,
        "derived_files": {
            path.name: {"sha256": sha256(path), "bytes": path.stat().st_size}
            for path in derived_paths
        },
        "service_key_stored_in_output": False,
    }
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    qa_lines = [
        "# 기업마당 API 수집 QA",
        "",
        f"- 수집시각(KST): `{manifest['collected_at_kst']}`",
        f"- 공식 총건수: `{total_count}`",
        f"- 저장 원본 페이지: `{len(page_records)}`",
        f"- 저장 항목 수: `{len(all_items)}`",
        f"- 공고ID 중복: `{duplicate_id_count}`",
        f"- 등록연도 분포: `{json.dumps(year_counts, ensure_ascii=False)}`",
        f"- 필요 범위({args.expected_year}년) 항목: `{len(current_year_items)}`",
        f"- 범위 밖 연도 항목(원본에만 보존): `{len(all_items) - len(current_year_items)}`",
        f"- {args.expected_year}년 소상공인 검토 후보: `{len(candidates)}`",
        f"- 후보 등급 분포: `{json.dumps(tier_counts, ensure_ascii=False)}`",
        "- 후보는 검토용이며 자격·금리·한도·접수상태를 확정하지 않음",
        "- 인증키는 산출물에 저장하지 않음",
        "",
    ]
    (output_dir / "QA.md").write_text("\n".join(qa_lines), encoding="utf-8")

    print(
        json.dumps(
            {
                "output_dir": str(output_dir),
                "items": len(all_items),
                "current_year_items": len(current_year_items),
                "candidates": len(candidates),
                "duplicate_ids": duplicate_id_count,
                "registration_year_counts": year_counts,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
