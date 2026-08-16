from __future__ import annotations

import csv
import difflib
import hashlib
import html
import json
import re
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RAW_ROOT = ROOT / "data" / "raw_re" / "policy"
REPORT_DIR = ROOT / "reports" / "pre_re1" / "policy"
OUTPUT_DIR = ROOT / "data" / "processed_re" / "policy" / "pre_re1"

BIZINFO_DIR = RAW_ROOT / "bizinfo" / "2026-08-15"
SME24_DIR = RAW_ROOT / "sme24" / "2026-08-15"
SEMAS_DIR = RAW_ROOT / "semas"
SEOUL_DIR = RAW_ROOT / "seoul_fund" / "2026"

SEMAS_OVERVIEW = SEMAS_DIR / "정책자금 한눈에 보기.md"
SEMAS_EXCLUSIONS = SEMAS_DIR / "정책자금_지원_제외업종.md"
SEOUL_INITIAL_DIR = SEOUL_DIR / "2026년 중소기업육성자금 융자지원"
SEOUL_CHANGE_DIR = SEOUL_DIR / "2026년도 서울특별시 중소기업육성자금 융자지원 변경계획 공고"
SEOUL_SUPPORT = SEOUL_DIR / "소상공인 종합지원 사업" / "소상공인_종합지원_사업.md"

SOURCE_URLS = {
    SEMAS_OVERVIEW: "https://ols.semas.or.kr/ols/man/SMAN018M/page.do",
    SEMAS_EXCLUSIONS: "https://ols.semas.or.kr/ols/pfa/SPFA207P/page.do",
    SEOUL_INITIAL_DIR / "경영안정자금_융자대상.md": "https://news.seoul.go.kr/economy/rearing-funds",
    SEOUL_INITIAL_DIR / "시설자금_융자대상.md": "https://news.seoul.go.kr/economy/rearing-funds",
    SEOUL_INITIAL_DIR / "시설자금_지원사업별_융자조건_및_한도.md": "https://news.seoul.go.kr/economy/rearing-funds",
    SEOUL_CHANGE_DIR / "2026년_중소기업육성자금_융자지원_변경계획_공고.md": "https://www.seoul.go.kr/news/news_notice.do?nttNo=457365",
    SEOUL_CHANGE_DIR / "별표1_경영안정자금_융자대상.md": "https://www.seoul.go.kr/news/news_notice.do?nttNo=457365",
    SEOUL_CHANGE_DIR / "별표2_시설자금_융자대상.md": "https://www.seoul.go.kr/news/news_notice.do?nttNo=457365",
    SEOUL_CHANGE_DIR / "별표3_시설자금_지원사업별_융자조건_및_한도.md": "https://www.seoul.go.kr/news/news_notice.do?nttNo=457365",
    SEOUL_SUPPORT: "https://news.seoul.go.kr/economy/small-business-supports",
}

SOURCE_ROLE = {
    SEMAS_OVERVIEW: "P-03 official overview; policy-specific notices still required",
    SEMAS_EXCLUSIONS: "P-03 common excluded-industry rule source",
    SEOUL_INITIAL_DIR / "경영안정자금_융자대상.md": "P-04 initial notice attachment",
    SEOUL_INITIAL_DIR / "시설자금_융자대상.md": "P-04 initial notice attachment",
    SEOUL_INITIAL_DIR / "시설자금_지원사업별_융자조건_및_한도.md": "P-04 initial notice attachment",
    SEOUL_CHANGE_DIR / "2026년_중소기업육성자금_융자지원_변경계획_공고.md": "P-04 operative change notice",
    SEOUL_CHANGE_DIR / "별표1_경영안정자금_융자대상.md": "P-04 change-notice annex 1",
    SEOUL_CHANGE_DIR / "별표2_시설자금_융자대상.md": "P-04 change-notice annex 2",
    SEOUL_CHANGE_DIR / "별표3_시설자금_지원사업별_융자조건_및_한도.md": "P-04 change-notice annex 3",
    SEOUL_SUPPORT: "P-04 Seoul small-business support overview",
}

COMMON_FIELDS = [
    "source_record_id",
    "group_id",
    "source_code",
    "source_native_id",
    "title",
    "normalized_title",
    "agency",
    "region",
    "detail_url",
    "application_url",
    "application_period",
    "source_basis",
    "source_status",
    "discovery_tags",
    "selection_status",
    "source_file",
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize_title(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value or "").casefold()
    return "".join(char for char in normalized if char.isalnum())


def clean_text(value: str) -> str:
    text = html.unescape(value or "")
    text = re.sub(r"<br\s*/?>", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = text.replace("**", "").replace("&nbsp;", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def discovery_tags(text: str) -> str:
    lowered = clean_text(text).casefold()
    definitions = {
        "loan_or_finance": ("융자", "대출", "금리", "보증료", "이차보전", "자금"),
        "debt_relief_or_refinance": ("대환", "상환연장", "채무", "고금리"),
        "nondebt_cash_or_cost": ("보조금", "바우처", "지원금", "실비지원", "비용 지원", "환급"),
        "crisis_or_recovery": ("위기", "경영애로", "재기", "재도전", "폐업", "재창업"),
        "sales_or_digital": ("판로", "마케팅", "디지털", "온라인", "스마트", "커머스"),
        "education_or_consulting": ("교육", "컨설팅", "멘토링", "클리닉"),
        "seoul_explicit": ("서울",),
        "small_business_explicit": ("소상공인",),
    }
    return ";".join(
        label for label, keywords in definitions.items() if any(keyword in lowered for keyword in keywords)
    )


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def count_csv_rows(path: Path) -> int:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.reader(stream)
        next(reader, None)
        return sum(1 for _ in reader)


def split_markdown_row(line: str) -> list[str]:
    return [part.strip() for part in line.strip().strip("|").split("|")]


def parse_semas_overview() -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    section = ""
    for line in SEMAS_OVERVIEW.read_text(encoding="utf-8").splitlines():
        if line.startswith("# 2026년 정책자금 직접대출"):
            section = "direct_loan"
        elif line.startswith("# 2026년 정책자금 대리대출"):
            section = "agency_loan"
        if not line.startswith("|") or line.startswith("|---") or "자금명" in line:
            continue
        cells = split_markdown_row(line)
        if len(cells) != 5 or not section:
            continue
        title, eligibility, term, limit, rate = map(clean_text, cells)
        native_id = f"SEMAS_{len(records) + 1:02d}"
        records.append(
            make_record(
                source_code="P03_SEMAS_OVERVIEW",
                source_native_id=native_id,
                title=title,
                agency="소상공인시장진흥공단",
                region="전국",
                detail_url=SOURCE_URLS[SEMAS_OVERVIEW],
                application_url="",
                application_period="예산 소진 시 마감; 정책별 공지 확인 필요",
                source_basis=f"{section}; 신청요건={eligibility}; 기간={term}; 한도={limit}; 금리={rate}",
                source_status="공식 요약 후보; 정책별 공지 미검증",
                source_file=SEMAS_OVERVIEW.relative_to(ROOT).as_posix(),
                tag_text=" ".join((title, eligibility, term, limit, rate)),
            )
        )
    return records


def parse_seoul_support() -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    for line in SEOUL_SUPPORT.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|") or line.startswith("|---") or "사업명" in line:
            continue
        cells = split_markdown_row(line)
        if len(cells) != 4:
            continue
        title, support, target, direct = map(clean_text, cells)
        urls = re.findall(r"https?://[^\s<]+", line)
        detail_url = urls[0].rstrip("|") if urls else SOURCE_URLS[SEOUL_SUPPORT]
        native_id = f"SEOUL_SUPPORT_{len(records) + 1:02d}"
        records.append(
            make_record(
                source_code="P04_SEOUL_SUPPORT",
                source_native_id=native_id,
                title=title,
                agency="서울특별시·서울신용보증재단",
                region="서울",
                detail_url=detail_url,
                application_url=detail_url,
                application_period="운영상황에 따라 변경; 사업별 공고 확인 필요",
                source_basis=f"지원내용={support}; 지원대상={target}; 원문 바로가기={direct}",
                source_status="서울시 공식 종합안내 후보; 사업별 공지 미검증",
                source_file=SEOUL_SUPPORT.relative_to(ROOT).as_posix(),
                tag_text=" ".join((title, support, target)),
            )
        )
    return records


def make_record(
    *,
    source_code: str,
    source_native_id: str,
    title: str,
    agency: str,
    region: str,
    detail_url: str,
    application_url: str,
    application_period: str,
    source_basis: str,
    source_status: str,
    source_file: str,
    tag_text: str,
) -> dict[str, str]:
    normalized = normalize_title(title)
    record_id = f"{source_code}:{source_native_id}"
    group_id = "GRP_" + hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]
    return {
        "source_record_id": record_id,
        "group_id": group_id,
        "source_code": source_code,
        "source_native_id": source_native_id,
        "title": clean_text(title),
        "normalized_title": normalized,
        "agency": clean_text(agency),
        "region": clean_text(region),
        "detail_url": detail_url.strip(),
        "application_url": application_url.strip(),
        "application_period": clean_text(application_period),
        "source_basis": clean_text(source_basis),
        "source_status": source_status,
        "discovery_tags": discovery_tags(tag_text),
        "selection_status": "미선정_RE1및선정기준승인대기",
        "source_file": source_file,
    }


def build_source_records() -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    for row in read_csv(BIZINFO_DIR / "small_business_candidates.csv"):
        records.append(
            make_record(
                source_code="P01_BIZINFO",
                source_native_id=row.get("pblancId", ""),
                title=row.get("pblancNm", ""),
                agency=row.get("excInsttNm", "") or row.get("jrsdInsttNm", ""),
                region=row.get("jrsdInsttNm", ""),
                detail_url=row.get("pblancUrl", ""),
                application_url=row.get("rceptEngnHmpgUrl", ""),
                application_period=row.get("reqstBeginEndDe", ""),
                source_basis=row.get("candidate_reason", ""),
                source_status=row.get("eligibility_status", "") or "후보 탐색 전용",
                source_file=(BIZINFO_DIR / "small_business_candidates.csv").relative_to(ROOT).as_posix(),
                tag_text=" ".join(
                    row.get(field, "")
                    for field in ("pblancNm", "bsnsSumryCn", "trgetNm", "hashtags", "pldirSportRealmLclasCodeNm")
                ),
            )
        )

    for row in read_csv(SME24_DIR / "small_business_candidates.csv"):
        records.append(
            make_record(
                source_code="P05_SME24",
                source_native_id=row.get("pblancSeq", ""),
                title=row.get("pblancNm", ""),
                agency=row.get("sportInsttNm", ""),
                region=row.get("areaNm", ""),
                detail_url=row.get("pblancDtlUrl", ""),
                application_url=row.get("reqstLinkInfo", ""),
                application_period=" ~ ".join(
                    value for value in (row.get("pblancBgnDt", ""), row.get("pblancEndDt", "")) if value
                ),
                source_basis=";".join(
                    value
                    for value in (
                        row.get("candidate_tier", ""),
                        row.get("candidate_code_matches", ""),
                        row.get("candidate_text_fields", ""),
                    )
                    if value
                ),
                source_status=row.get("eligibility_status", "") or "교차확인 후보",
                source_file=(SME24_DIR / "small_business_candidates.csv").relative_to(ROOT).as_posix(),
                tag_text=" ".join(
                    row.get(field, "")
                    for field in ("pblancNm", "detailBsnsNm", "policyCnts", "sportCnts", "sportTrget", "bizType", "sportType")
                ),
            )
        )

    records.extend(parse_semas_overview())
    records.append(
        make_record(
            source_code="P04_SEOUL_FUND",
            source_native_id="SEOUL_2026_FUND_CHANGE_1433",
            title="2026년도 서울특별시 중소기업육성자금 융자지원 변경계획",
            agency="서울특별시",
            region="서울",
            detail_url="https://www.seoul.go.kr/news/news_notice.do?nttNo=457365",
            application_url="https://www.seoulsbdc.or.kr",
            application_period="자금별·예산별 상이; 공식 공고 확인 필요",
            source_basis="서울특별시공고 제2026-1433호; 2026-05-04 변경공고와 별표 1~3",
            source_status="공식 변경공고 묶음 확보; 적용조건 구조화 전",
            source_file=(
                SEOUL_CHANGE_DIR / "2026년_중소기업육성자금_융자지원_변경계획_공고.md"
            ).relative_to(ROOT).as_posix(),
            tag_text="서울 중소기업 소상공인 융자 대출 자금 재기지원 희망동행 대환 위기",
        )
    )
    records.extend(parse_seoul_support())
    return records


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def build_groups(records: list[dict[str, str]]) -> list[dict[str, object]]:
    by_group: dict[str, list[dict[str, str]]] = defaultdict(list)
    for record in records:
        by_group[record["group_id"]].append(record)

    source_priority = {
        "P04_SEOUL_FUND": 0,
        "P04_SEOUL_SUPPORT": 1,
        "P03_SEMAS_OVERVIEW": 2,
        "P01_BIZINFO": 3,
        "P05_SME24": 4,
    }
    groups: list[dict[str, object]] = []
    for group_id, items in by_group.items():
        ordered = sorted(items, key=lambda item: (source_priority[item["source_code"]], item["title"]))
        sources = sorted({item["source_code"] for item in items})
        tags = sorted(
            {
                tag
                for item in items
                for tag in item["discovery_tags"].split(";")
                if tag
            }
        )
        groups.append(
            {
                "group_id": group_id,
                "canonical_title": ordered[0]["title"],
                "normalized_title": ordered[0]["normalized_title"],
                "source_record_count": len(items),
                "source_codes": ";".join(sources),
                "source_native_ids": ";".join(sorted(item["source_native_id"] for item in items)),
                "title_variants": " || ".join(sorted({item["title"] for item in items})),
                "agencies": " || ".join(sorted({item["agency"] for item in items if item["agency"]})),
                "regions": " || ".join(sorted({item["region"] for item in items if item["region"]})),
                "discovery_tags": ";".join(tags),
                "has_p01": "yes" if any(item["source_code"] == "P01_BIZINFO" for item in items) else "no",
                "has_p03": "yes" if any(item["source_code"] == "P03_SEMAS_OVERVIEW" for item in items) else "no",
                "has_p04": "yes" if any(item["source_code"].startswith("P04_") for item in items) else "no",
                "has_p05": "yes" if any(item["source_code"] == "P05_SME24" for item in items) else "no",
                "official_manual_seed": (
                    "yes"
                    if any(item["source_code"] in {"P03_SEMAS_OVERVIEW", "P04_SEOUL_FUND", "P04_SEOUL_SUPPORT"} for item in items)
                    else "no"
                ),
                "selection_status": "미선정_RE1및선정기준승인대기",
                "validation_status": "정확제목그룹화만완료_공식원문검증필요",
            }
        )
    return sorted(groups, key=lambda row: (str(row["canonical_title"]), str(row["group_id"])))


def manual_source_manifest() -> dict[str, object]:
    entries: list[dict[str, object]] = []
    for path in sorted(SOURCE_URLS, key=lambda item: item.as_posix()):
        stat = path.stat()
        text = path.read_text(encoding="utf-8")
        entries.append(
            {
                "path": path.relative_to(ROOT).as_posix(),
                "source_url": SOURCE_URLS[path],
                "role": SOURCE_ROLE[path],
                "bytes": stat.st_size,
                "sha256": sha256_file(path),
                "file_mtime_local": datetime.fromtimestamp(stat.st_mtime).astimezone().isoformat(timespec="seconds"),
                "utf8_decode": "passed",
                "heading_count": len(re.findall(r"(?m)^#{1,6} ", text)),
                "table_row_count": sum(
                    1
                    for line in text.splitlines()
                    if line.startswith("|") and not line.startswith("|---")
                ),
                "embedded_source_url": bool(re.search(r"https?://", text)),
                "embedded_retrieved_at": bool(re.search(r"확인일|수집일|retrieved_at", text, re.IGNORECASE)),
            }
        )
    return {
        "generated_at_local": datetime.now().astimezone().isoformat(timespec="seconds"),
        "status": "pre_RE1_QA_only_not_policy_approval",
        "downloaded_source_files_modified": False,
        "files": entries,
    }


def build_inventory() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for path in sorted(RAW_ROOT.rglob("*"), key=lambda item: item.as_posix()):
        if not path.is_file():
            continue
        stat = path.stat()
        rows.append(
            {
                "relative_path": path.relative_to(ROOT).as_posix(),
                "source_family": path.relative_to(RAW_ROOT).parts[0],
                "extension": path.suffix.lower(),
                "bytes": stat.st_size,
                "sha256": sha256_file(path),
                "mtime_local": datetime.fromtimestamp(stat.st_mtime).astimezone().isoformat(timespec="seconds"),
            }
        )
    return rows


def build_seoul_diff_report() -> tuple[str, list[dict[str, object]]]:
    pairs = [
        (
            "별표1 경영안정자금 융자대상",
            SEOUL_INITIAL_DIR / "경영안정자금_융자대상.md",
            SEOUL_CHANGE_DIR / "별표1_경영안정자금_융자대상.md",
        ),
        (
            "별표2 시설자금 융자대상",
            SEOUL_INITIAL_DIR / "시설자금_융자대상.md",
            SEOUL_CHANGE_DIR / "별표2_시설자금_융자대상.md",
        ),
        (
            "별표3 시설자금 지원사업별 융자조건 및 한도",
            SEOUL_INITIAL_DIR / "시설자금_지원사업별_융자조건_및_한도.md",
            SEOUL_CHANGE_DIR / "별표3_시설자금_지원사업별_융자조건_및_한도.md",
        ),
    ]
    summaries: list[dict[str, object]] = []
    sections = [
        "# 서울시 중소기업육성자금 최초본·변경본 차이",
        "",
        "> 이 문서는 원본 Markdown을 수정하지 않고 줄 단위로 비교한 QA 산출물이다. 차이가 있다는 사실만 보여주며, 어느 조건을 서비스에 적용할지는 변경공고의 적용일과 공식 원문 검수 후 결정한다.",
        "",
    ]
    for label, initial, changed in pairs:
        initial_lines = initial.read_text(encoding="utf-8").splitlines()
        changed_lines = changed.read_text(encoding="utf-8").splitlines()
        diff = list(
            difflib.unified_diff(
                initial_lines,
                changed_lines,
                fromfile=initial.relative_to(ROOT).as_posix(),
                tofile=changed.relative_to(ROOT).as_posix(),
                lineterm="",
            )
        )
        added = sum(1 for line in diff if line.startswith("+") and not line.startswith("+++"))
        removed = sum(1 for line in diff if line.startswith("-") and not line.startswith("---"))
        exact = sha256_file(initial) == sha256_file(changed)
        summaries.append(
            {
                "document": label,
                "exact_sha256_duplicate": exact,
                "added_lines": added,
                "removed_lines": removed,
                "initial_sha256": sha256_file(initial),
                "changed_sha256": sha256_file(changed),
            }
        )
        sections.extend(
            [
                f"## {label}",
                "",
                f"- SHA-256 완전 동일: {'예' if exact else '아니오'}",
                f"- 변경본 추가 줄: {added}",
                f"- 변경본 제거 줄: {removed}",
                "",
            ]
        )
        if diff:
            sections.extend(["```diff", *diff, "```", ""])
        else:
            sections.extend(["두 파일은 바이트 단위로 동일하다.", ""])
    return "\n".join(sections).rstrip() + "\n", summaries


def write_selection_decision(groups: list[dict[str, object]], records: list[dict[str, str]]) -> None:
    tag_counts = Counter(
        tag
        for group in groups
        for tag in str(group["discovery_tags"]).split(";")
        if tag
    )
    source_counts = Counter(record["source_code"] for record in records)
    text = f"""# 대표 정책 선정 전 사용자 결정 패키지

## 현재 상태

- RE Stage 1은 아직 승인되지 않았다.
- 원본 보존, 형식 QA, 출처별 후보의 공통 스키마 변환, 정확 제목 그룹화까지만 수행했다.
- 총 소스 레코드: {len(records):,}건
- 정확 제목 후보 그룹: {len(groups):,}개
- 모든 후보의 상태: `미선정_RE1및선정기준승인대기`
- 퍼지매칭, 후보 제외, 순위화, 대표 정책 8~12개 확정은 수행하지 않았다.

## 출처별 소스 레코드

| 출처 | 건수 | 의미 |
| --- | ---: | --- |
| P-01 기업마당 | {source_counts['P01_BIZINFO']:,} | 소상공인 후보 탐색 |
| P-05 중소벤처24 | {source_counts['P05_SME24']:,} | 소상공인 후보·교차확인 |
| P-03 소진공 요약 | {source_counts['P03_SEMAS_OVERVIEW']:,} | 정책자금 공식 요약 Seed |
| P-04 서울시 육성자금 | {source_counts['P04_SEOUL_FUND']:,} | 서울시 변경공고 묶음 |
| P-04 서울시 종합지원 | {source_counts['P04_SEOUL_SUPPORT']:,} | 서울 소상공인 지원 Seed |

## 설명용 키워드 태그 분포

| 태그 | 그룹 수 |
| --- | ---: |
| 대출·금융 | {tag_counts['loan_or_finance']:,} |
| 대환·채무완화 | {tag_counts['debt_relief_or_refinance']:,} |
| 비차입 현금·비용지원 | {tag_counts['nondebt_cash_or_cost']:,} |
| 위기·재기·폐업 | {tag_counts['crisis_or_recovery']:,} |
| 판로·디지털 | {tag_counts['sales_or_digital']:,} |
| 교육·컨설팅 | {tag_counts['education_or_consulting']:,} |
| 서울 명시 | {tag_counts['seoul_explicit']:,} |

태그는 제목·요약의 키워드 탐색값이며 공식 정책유형이나 자격판정이 아니다.

## 승인이 필요한 선택

### 선택안 A — 현금흐름 비교 가능성 중심 균형 포트폴리오 (권장)

- 서울 소재 소상공인이 실제 검토할 수 있는 전국·서울 정책만 포함
- 비차입 지원, 비용절감·이차보전, 대환·채무완화, 신규융자, 위기·재기 유형을 함께 포함
- 금액, 지급시점, 자부담, 금리, 거치·상환 중 하나 이상을 공식 문서에서 구조화할 수 있는 정책 우선
- 대표 정책 8~12개를 선정한 뒤 공식 공고와 첨부문서를 수작업 검증
- 장점: 현재 서비스의 무대응 대비 정책 개입 현금흐름 비교와 직접 연결됨
- 단점: 교육·행사·일반 컨설팅 정책의 대표성이 낮아질 수 있음

### 선택안 B — 지원서비스 유형 다양성 중심

- 금융, 교육, 컨설팅, 판로, 디지털, 폐업·재기를 고르게 포함
- 장점: 소상공인 지원 생태계의 폭을 보여주기 쉬움
- 단점: 금액·시점이 없는 정책은 현금흐름 효과를 계산하기 어려워 핵심 서비스 데모가 약해질 수 있음

### 선택안 C — 서울 정책 우선

- 서울 명시 정책과 서울시·서울신용보증재단 정책을 우선 선정
- 장점: 서비스 지역과 데이터 범위가 일치함
- 단점: 전국 소진공 정책자금과 대환·재기 정책의 비교폭이 줄어들 수 있음

## 권장 다음 순서

1. RE Stage 1에서 서비스 범위와 정책 선정 원칙을 승인한다.
2. 위 선택안 중 하나를 승인하거나 조합 기준을 지정한다.
3. 승인 기준으로만 8~12개 후보를 제안한다.
4. 사용자가 최종 목록을 승인한 뒤 P-02·P-03·P-04의 정책별 원문을 수집한다.
5. 공식 원문 검수 후에만 자격 Rule·금융 Event·RAG Chunk를 만든다.
"""
    (REPORT_DIR / "selection_decision_needed.md").write_text(text, encoding="utf-8")


def main() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    required = [
        BIZINFO_DIR / "manifest.json",
        BIZINFO_DIR / "QA.md",
        BIZINFO_DIR / "small_business_candidates.csv",
        SME24_DIR / "manifest.json",
        SME24_DIR / "QA.md",
        SME24_DIR / "small_business_candidates.csv",
        SME24_DIR / "bizinfo_candidate_exact_title_crosswalk.csv",
        SEMAS_OVERVIEW,
        SEMAS_EXCLUSIONS,
        SEOUL_CHANGE_DIR / "2026년_중소기업육성자금_융자지원_변경계획_공고.md",
        SEOUL_CHANGE_DIR / "별표1_경영안정자금_융자대상.md",
        SEOUL_CHANGE_DIR / "별표2_시설자금_융자대상.md",
        SEOUL_CHANGE_DIR / "별표3_시설자금_지원사업별_융자조건_및_한도.md",
        SEOUL_SUPPORT,
    ]
    missing = [path.relative_to(ROOT).as_posix() for path in required if not path.is_file()]
    if missing:
        raise FileNotFoundError("Missing required policy files: " + ", ".join(missing))

    bizinfo_manifest = json.loads((BIZINFO_DIR / "manifest.json").read_text(encoding="utf-8"))
    sme24_manifest = json.loads((SME24_DIR / "manifest.json").read_text(encoding="utf-8"))

    verified_counts = {
        "bizinfo_candidate_csv_rows": count_csv_rows(BIZINFO_DIR / "small_business_candidates.csv"),
        "bizinfo_manifest_candidate_count": bizinfo_manifest["candidate_count"],
        "sme24_candidate_csv_rows": count_csv_rows(SME24_DIR / "small_business_candidates.csv"),
        "sme24_manifest_candidate_count": sme24_manifest["small_business_candidate_count"],
        "existing_exact_crosswalk_rows": count_csv_rows(
            SME24_DIR / "bizinfo_candidate_exact_title_crosswalk.csv"
        ),
        "existing_unmatched_bizinfo_rows": count_csv_rows(
            SME24_DIR / "bizinfo_candidates_without_exact_sme24_match.csv"
        ),
    }
    if verified_counts["bizinfo_candidate_csv_rows"] != verified_counts["bizinfo_manifest_candidate_count"]:
        raise ValueError("Bizinfo candidate row count differs from its manifest")
    if verified_counts["sme24_candidate_csv_rows"] != verified_counts["sme24_manifest_candidate_count"]:
        raise ValueError("SME24 candidate row count differs from its manifest")

    manual_manifest = manual_source_manifest()
    (SEMAS_DIR / "manifest.json").write_text(
        json.dumps(
            {
                **{key: value for key, value in manual_manifest.items() if key != "files"},
                "source_family": "P-03 SEMAS",
                "files": [item for item in manual_manifest["files"] if "/semas/" in item["path"]],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    (SEOUL_DIR / "manifest.json").write_text(
        json.dumps(
            {
                **{key: value for key, value in manual_manifest.items() if key != "files"},
                "source_family": "P-04 Seoul",
                "files": [item for item in manual_manifest["files"] if "/seoul_fund/" in item["path"]],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    inventory = build_inventory()
    write_csv(
        REPORT_DIR / "source_inventory.csv",
        inventory,
        ["relative_path", "source_family", "extension", "bytes", "sha256", "mtime_local"],
    )

    diff_text, diff_summary = build_seoul_diff_report()
    (REPORT_DIR / "seoul_version_diff.md").write_text(diff_text, encoding="utf-8")

    records = build_source_records()
    groups = build_groups(records)
    write_csv(OUTPUT_DIR / "source_records.csv", records, COMMON_FIELDS)
    group_fields = [
        "group_id",
        "canonical_title",
        "normalized_title",
        "source_record_count",
        "source_codes",
        "source_native_ids",
        "title_variants",
        "agencies",
        "regions",
        "discovery_tags",
        "has_p01",
        "has_p03",
        "has_p04",
        "has_p05",
        "official_manual_seed",
        "selection_status",
        "validation_status",
    ]
    write_csv(OUTPUT_DIR / "candidate_groups.csv", groups, group_fields)

    source_counts = Counter(record["source_code"] for record in records)
    multi_source_groups = sum(1 for group in groups if int(group["source_record_count"]) > 1)
    manual_entries = manual_manifest["files"]
    no_embedded_url = sum(1 for item in manual_entries if not item["embedded_source_url"])
    no_embedded_retrieved_at = sum(1 for item in manual_entries if not item["embedded_retrieved_at"])

    qa_summary = {
        "generated_at_local": datetime.now().astimezone().isoformat(timespec="seconds"),
        "execution_scope": "pre_RE1_QA_and_lossless_candidate_integration_only",
        "downloaded_source_files_modified": False,
        "final_policy_selection_performed": False,
        "fuzzy_matching_performed": False,
        "candidate_exclusion_performed": False,
        "verified_counts": verified_counts,
        "raw_inventory_file_count": len(inventory),
        "manual_source_file_count": len(manual_entries),
        "manual_files_without_embedded_source_url": no_embedded_url,
        "manual_files_without_embedded_retrieved_at": no_embedded_retrieved_at,
        "source_record_count": len(records),
        "source_record_counts": dict(sorted(source_counts.items())),
        "candidate_group_count": len(groups),
        "multi_source_exact_title_group_count": multi_source_groups,
        "seoul_version_diff_summary": diff_summary,
        "warnings": [
            "P-03 and P-04 Markdown files do not all embed source URL and retrieval time; separate manifests preserve provenance without editing raw files.",
            "P-03 policy-fund overview is not a substitute for each selected policy's detailed notice and attachments.",
            "P-04 initial and change-notice annexes must be interpreted by official effective date; text differences are not automatically resolved.",
            "Only NFKC/casefold/alphanumeric exact-title grouping was used; no fuzzy match or semantic merge was applied.",
            "All groups remain unselected until RE Stage 1 and policy-selection criteria are approved.",
        ],
    }
    (REPORT_DIR / "qa_summary.json").write_text(
        json.dumps(qa_summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    qa_text = f"""# P-01·P-03·P-04·P-05 사전 QA 보고서

## 판정

- 결과: **사전 QA 및 무손실 후보 통합 통과**
- RE Stage 1 상태: **미승인**
- 허용 범위: 원본 보존, 출처·형식·중복·건수 QA, 공통 스키마 변환, 정확 제목 그룹화
- 수행하지 않은 것: 퍼지매칭, 후보 제외, 대표 정책 순위화, 최종 8~12개 선정, 자격 Rule·금융 Event 확정

## 전수 확인 결과

| 항목 | 결과 |
| --- | ---: |
| 원본 인벤토리 파일 | {len(inventory):,}개 |
| P-01 후보 CSV | {verified_counts['bizinfo_candidate_csv_rows']:,}건 |
| P-05 후보 CSV | {verified_counts['sme24_candidate_csv_rows']:,}건 |
| 기존 P-01↔P-05 정확 제목 교차행 | {verified_counts['existing_exact_crosswalk_rows']:,}건 |
| 기존 P-01 정확제목 미매칭 후보 | {verified_counts['existing_unmatched_bizinfo_rows']:,}건 |
| P-03 정책자금 공식 요약 Seed | {source_counts['P03_SEMAS_OVERVIEW']:,}건 |
| P-04 서울시 육성자금 Seed | {source_counts['P04_SEOUL_FUND']:,}건 |
| P-04 서울시 종합지원 Seed | {source_counts['P04_SEOUL_SUPPORT']:,}건 |
| 통합 소스 레코드 | {len(records):,}건 |
| 정확 제목 후보 그룹 | {len(groups):,}개 |
| 둘 이상 소스가 연결된 그룹 | {multi_source_groups:,}개 |

## P-01·P-05

- 기존 Manifest와 후보 CSV 행 수가 일치한다.
- 기존 원본 응답, 파생 CSV·JSONL, QA와 정확 제목 Crosswalk를 재사용했다.
- P-05 날짜 필터는 등록일이 아니라 수정일 기준이라는 기존 제한을 유지했다.
- 정확 제목 일치는 공식 자격 검증이 아니다.

## P-03 소진공

- `정책자금 한눈에 보기.md`에서 직접대출·대리대출 13종을 파싱했다.
- 기준금리와 가산금리·고정금리 표현이 구분되어 있다.
- 제외업종과 재해자금 허용 예외가 함께 보존되어 있다.
- 정책별 세부 공지와 첨부파일은 아직 없으므로 자격 Rule·상환 Event를 확정할 수 없다.
- 원본 Markdown을 수정하지 않고 `data/raw_re/policy/semas/manifest.json`에 URL·파일시각·SHA-256을 추가했다.

## P-04 서울시

- 최초 안내 첨부 3개, 변경공고와 별표 3개, 소상공인 종합지원 안내 1개를 확인했다.
- 변경공고 본문에 서울특별시공고 제2026-1433호와 2026-05-04가 기록되어 있다.
- 별표 1은 최초본과 변경공고본이 SHA-256까지 동일하다.
- 별표 2와 별표 3은 차이가 있어 자동으로 어느 값을 채택하지 않았다.
- 전체 줄 차이는 `reports/pre_re1/policy/seoul_version_diff.md`에 보존했다.
- 원본 Markdown을 수정하지 않고 `data/raw_re/policy/seoul_fund/2026/manifest.json`에 URL·파일시각·SHA-256을 추가했다.

## 알려진 품질 제한

- 수동 저장 Markdown에는 출처 URL과 확인일이 본문에 없는 파일이 있어 별도 Manifest로 보완했다.
- 파일 수정시각은 로컬 저장시각 근거이며, 웹페이지 게시·적용일과 같은 의미가 아니다.
- P-03은 요약 페이지이고 P-04 종합지원 페이지도 개별 사업 공고가 아니므로 최종 원문 묶음이 아니다.
- 퍼지매칭과 의미기반 통합은 사용자 승인 전 수행하지 않았다.
- 다운로드 완료는 RE Stage 1 승인이나 최종 정책 채택을 의미하지 않는다.

## 산출물

- `reports/pre_re1/policy/source_inventory.csv`
- `reports/pre_re1/policy/qa_summary.json`
- `reports/pre_re1/policy/seoul_version_diff.md`
- `reports/pre_re1/policy/selection_decision_needed.md`
- `data/processed_re/policy/pre_re1/source_records.csv`
- `data/processed_re/policy/pre_re1/candidate_groups.csv`
- `data/raw_re/policy/semas/manifest.json`
- `data/raw_re/policy/seoul_fund/2026/manifest.json`
"""
    (REPORT_DIR / "QA.md").write_text(qa_text, encoding="utf-8")
    write_selection_decision(groups, records)

    output_manifest = {
        "generated_at_local": datetime.now().astimezone().isoformat(timespec="seconds"),
        "script": Path(__file__).relative_to(ROOT).as_posix(),
        "scope": "pre_RE1_lossless_integration",
        "source_record_count": len(records),
        "candidate_group_count": len(groups),
        "source_records_sha256": sha256_file(OUTPUT_DIR / "source_records.csv"),
        "candidate_groups_sha256": sha256_file(OUTPUT_DIR / "candidate_groups.csv"),
        "selection_status": "not_started_requires_user_approval",
        "downloaded_source_files_modified": False,
    }
    (OUTPUT_DIR / "manifest.json").write_text(
        json.dumps(output_manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    print(json.dumps(qa_summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
