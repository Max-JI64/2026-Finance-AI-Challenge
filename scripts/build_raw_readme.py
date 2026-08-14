"""Build the raw-data README from bounded schema samples only."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from inspect_sample_schema import PROJECT_ROOT, build_report, inspect_csv


README_PATH = PROJECT_ROOT / "data" / "raw" / "README.md"

DATASET_META = {
    "추정매출-상권": {
        "number": 1,
        "priority": "P0 필수",
        "role": "상권·업종별 매출환경과 향후 Target 구성의 기준",
        "url": "https://data.seoul.go.kr/dataList/OA-15572/S/1/datasetView.do",
    },
    "점포-상권": {
        "number": 2,
        "priority": "P0 필수",
        "role": "점포 수, 개업·폐업, 프랜차이즈 등 경쟁환경",
        "url": "https://data.seoul.go.kr/dataList/OA-15577/S/1/datasetView.do",
    },
    "영역-상권": {
        "number": 3,
        "priority": "P0 필수",
        "role": "상권코드와 공간영역 연결",
        "url": "https://data.seoul.go.kr/dataList/OA-15560/S/1/datasetView.do",
    },
    "길단위인구-상권": {
        "number": 4,
        "priority": "P1 권장",
        "role": "성별·연령·시간대·요일별 유동인구",
        "url": "https://data.seoul.go.kr/dataList/OA-15568/S/1/datasetView.do",
    },
    "상권변화지표-상권": {
        "number": 5,
        "priority": "P1 권장",
        "role": "상권 변화 유형과 운영·폐업 영업기간",
        "url": "https://data.seoul.go.kr/dataList/OA-15576/S/1/datasetView.do",
    },
    "상주인구-상권": {
        "number": 6,
        "priority": "P2 선택",
        "role": "상권 내 거주 인구와 가구 구성",
        "url": "https://data.seoul.go.kr/dataList/OA-15584/S/1/datasetView.do",
    },
    "직장인구-상권": {
        "number": 7,
        "priority": "P2 선택",
        "role": "상권 내 직장인구의 성별·연령 구성",
        "url": "https://data.seoul.go.kr/dataList/OA-15569/S/1/datasetView.do",
    },
    "집객시설-상권": {
        "number": 8,
        "priority": "P2 선택",
        "role": "교통·교육·의료·유통 등 집객시설 수",
        "url": "https://data.seoul.go.kr/dataList/OA-15580/S/1/datasetView.do",
    },
    "아파트-상권": {
        "number": 9,
        "priority": "P2 선택",
        "role": "아파트 단지·면적·가격대·평균 시가",
        "url": "https://data.seoul.go.kr/dataList/OA-15566/S/1/datasetView.do",
    },
}

ENGLISH_STORE_DESCRIPTIONS = {
    "stdr_yyqu_cd": "기준 년분기 코드",
    "trdar_se_cd": "상권 구분 코드",
    "trdar_se_cd_nm": "상권 구분 코드명",
    "trdar_cd": "상권 코드",
    "trdar_cd_nm": "상권 코드명",
    "svc_induty_cd": "서비스 업종 코드",
    "svc_induty_cd_nm": "서비스 업종 코드명",
    "stor_co": "점포 수",
    "similr_induty_stor_co": "유사 업종 점포 수",
    "opbiz_rt": "개업률",
    "opbiz_stor_co": "개업 점포 수",
    "clsbiz_rt": "폐업률",
    "clsbiz_stor_co": "폐업 점포 수",
    "frc_stor_co": "프랜차이즈 점포 수",
}

DBF_DESCRIPTIONS = {
    "TRDAR_SE_C": "상권 구분 코드",
    "TRDAR_SE_1": "상권 구분 코드명",
    "TRDAR_CD": "상권 코드",
    "TRDAR_CD_N": "상권 코드명",
    "XCNTS_VALUE": "상권 중심점 X 좌표",
    "YDNTS_VALUE": "상권 중심점 Y 좌표",
    "SIGNGU_CD": "시군구 코드",
    "ADSTRD_CD": "행정동 코드",
}


def escape_cell(value: Any) -> str:
    text = str(value).replace("\n", " ").replace("\r", " ").replace("|", "\\|")
    return text if text else "—"


def humanize_variable(name: str) -> str:
    if name in ENGLISH_STORE_DESCRIPTIONS:
        return ENGLISH_STORE_DESCRIPTIONS[name]
    if name in DBF_DESCRIPTIONS:
        return DBF_DESCRIPTIONS[name]
    return name.replace("_", " ")


def format_size(size_bytes: int) -> str:
    return f"{size_bytes:,} B ({size_bytes / 1024 / 1024:.2f} MiB)"


def period_label(file_detail: dict[str, Any]) -> str:
    filename = Path(file_detail["path"]).name
    for year in range(2021, 2031):
        if f"{year}년" in filename:
            return f"{year}년 (파일명 기준)"
    period_codes = file_detail.get("boundary_period_codes", [])
    if not period_codes:
        return "미확인"
    if len(period_codes) == 1:
        return f"{period_codes[0]} (앞·뒤 표본 기준)"
    return f"{period_codes[0]}~{period_codes[-1]} (앞·뒤 표본 기준)"


def variable_table(columns: list[dict[str, Any]]) -> list[str]:
    lines = [
        "| 번호 | 원본 변수명 | 표본 추정형 | 표본값 | 원본명 기준 의미 |",
        "| ---: | --- | --- | --- | --- |",
    ]
    for index, column in enumerate(columns, start=1):
        lines.append(
            "| "
            + " | ".join(
                (
                    str(index),
                    f"`{escape_cell(column['name'])}`",
                    escape_cell(column["inferred_type"]),
                    escape_cell(column["example"]),
                    escape_cell(humanize_variable(column["name"])),
                )
            )
            + " |"
        )
    return lines


def build_readme() -> str:
    report = build_report()
    datasets = sorted(
        report["datasets"], key=lambda dataset: DATASET_META[dataset["dataset_name"]]["number"]
    )
    generated_at = datetime.now().astimezone().isoformat(timespec="minutes")

    lines = [
        "# 원본 데이터 목록과 변수표",
        "",
        f"- 최종 갱신: {generated_at}",
        "- 대상: 서울시 상권분석서비스 데이터 1~9번",
        "- 상태: 1~9번 원본 파일 수집 확인",
        "",
        "## 원본 데이터 확인 원칙",
        "",
        "- 현재 단계에서는 **전처리하지 않는다**. 컬럼명 변경, 결측 처리, 형 변환, JOIN, 파생변수 생성, 이상치 제거를 수행하지 않는다.",
        "- 원본 CSV는 수정하지 않고 `data/raw/`에 보존한다.",
        "- 대용량 파일을 전체 로딩하지 않는다. 이번 변수표는 CSV별 최대 64 KiB와 최대 5개 데이터 행만 읽어 작성했다.",
        "- 표본 추정형과 표본값은 전체 데이터의 자료형·분포·결측을 확정하지 않는다.",
        "- 공간 데이터는 DBF 헤더와 최대 5개 속성 레코드, CPG, PRJ만 확인했다. SHP 전체 도형은 읽지 않았다.",
        "- 전체 행 수, 결측률, 중복률, 값 범위, 코드 일관성은 추후 Stage 2 품질검증에서 청크 또는 필요한 컬럼만 읽어 계산한다.",
        "",
        "## 수집 현황",
        "",
        "| 번호 | 데이터 | 우선순위 | 확인 파일 수 | 원본 변수 수 | 인코딩 | 스키마 상태 | 용도 | 공식 링크 |",
        "| ---: | --- | --- | ---: | ---: | --- | --- | --- | --- |",
    ]

    for dataset in datasets:
        meta = DATASET_META[dataset["dataset_name"]]
        file_count = dataset.get("file_count", 1)
        schema_status = (
            "연도별 동일"
            if dataset.get("headers_match_across_files") is True
            else "2025년 헤더 변경"
            if dataset.get("headers_match_across_files") is False
            else "공간 DBF"
        )
        lines.append(
            f"| {meta['number']} | {dataset['dataset_name']} | {meta['priority']} | {file_count} | "
            f"{dataset['column_count']} | {dataset['encoding']} | {schema_status} | {meta['role']} | "
            f"[공식 페이지]({meta['url']}) |"
        )

    lines.extend(
        [
            "",
            "## 원본 파일 인벤토리",
            "",
            "기간은 연도가 파일명에 있으면 파일명을 우선 사용했다. 연도 표기가 없는 CSV는 파일 앞·뒤 각각 최대 5행에서 관찰한 기준년분기 코드 범위이며 전체 스캔으로 확정한 기간이 아니다.",
            "",
            "| 데이터 번호 | 데이터 | 원본 파일명 | 기간 | 크기 | 형식 | 인코딩 | 변수 수 | 출처 |",
            "| ---: | --- | --- | --- | ---: | --- | --- | ---: | --- |",
        ]
    )

    for dataset in datasets:
        meta = DATASET_META[dataset["dataset_name"]]
        if dataset["dataset_name"] == "영역-상권":
            component_names = ", ".join(Path(path).name for path in dataset["component_files"])
            lines.append(
                f"| {meta['number']} | {dataset['dataset_name']} | {component_names} | 공간 Snapshot(파일명에 기준시점 미표기) | "
                f"{format_size(dataset['size_bytes'])} | CPG/DBF/PRJ/SHP/SHX | {dataset['encoding']} | {dataset['column_count']} | "
                f"[서울 열린데이터광장]({meta['url']}) |"
            )
            continue

        for file_detail in dataset["file_details"]:
            lines.append(
                f"| {meta['number']} | {dataset['dataset_name']} | `{Path(file_detail['path']).name}` | "
                f"{period_label(file_detail)} | {format_size(file_detail['size_bytes'])} | CSV | "
                f"{file_detail['encoding']} | {file_detail['column_count']} | [서울 열린데이터광장]({meta['url']}) |"
            )

    lines.extend(
        [
            "",
            "### 핵심 1~9 외 참고 파일",
            "",
            "| 파일명 | 경계 표본 기간 | 크기 | 형식 | 인코딩 | 변수 수 | 현재 처리 |",
            "| --- | --- | ---: | --- | --- | ---: | --- |",
        ]
    )
    for extra_path_text in report["extra_files"]:
        extra_path = PROJECT_ROOT / extra_path_text
        extra = inspect_csv(extra_path)
        lines.append(
            f"| `{extra_path.name}` | {period_label(extra)} | {format_size(extra['size_bytes'])} | CSV | "
            f"{extra['encoding']} | {extra['column_count']} | 집계 단위가 달라 원본 참고용으로만 보존 |"
        )

    lines.extend(
        [
            "",
            "## 수집·갱신 기록",
            "",
            f"- 작업공간 확인 시각: {generated_at}",
            "- 수집 방식: 재현 가능한 시점 고정을 위해 서울 열린데이터광장의 파일 Snapshot을 사용했다. API 실시간 조회는 현재 원본 수집 방식으로 사용하지 않는다.",
            "- 다운로드일은 파일 내부나 파일명으로 확정할 수 없어 작업공간 확인 시각과 구분한다. 운영체제 수정시각을 다운로드일로 간주하지 않는다.",
            "- 현재 `data/raw/`에는 해제된 CSV와 공간파일 구성요소가 있으며 원본 ZIP은 확인되지 않는다. 향후 압축파일을 다시 받을 경우 ZIP과 해제본을 별도 하위 경로에 함께 보존한다.",
            "- 데이터 갱신 시 기존 파일을 덮어쓰지 않고 기준연도 또는 확인일이 드러나는 파일명·하위 폴더로 버전을 구분한다.",
            "- `data/raw/`는 원본 전용이며 `data/interim/`, `data/processed/`와 물리적으로 분리되어 있다. 현재 두 가공 폴더에는 데이터 산출물이 없다.",
            "",
            "## 원본 파일 구성에서 확인된 주의사항",
            "",
            "- `추정매출-상권`은 2021~2025년 5개 CSV이며 헤더 55개가 동일하다.",
            "- `점포-상권`은 2021~2025년 5개 CSV지만 2025년만 영문 헤더를 사용한다. 원본 상태를 그대로 기록하며 이름 통일은 전처리 단계에서 수행한다.",
            "- `영역-상권`은 CPG·DBF·PRJ·SHP·SHX 다섯 파일이 한 묶음이다.",
            "- `상권변화지표-자치구`, `직장인구-상권배후지`는 추가로 존재하지만 핵심 1~9번의 `상권` 단위 파일과 집계 단위가 다르므로 현재 변수표 대상에서 제외한다.",
            "",
        ]
    )

    for dataset in datasets:
        meta = DATASET_META[dataset["dataset_name"]]
        lines.extend(
            [
                f"## {meta['number']}. {dataset['dataset_name']}",
                "",
                f"- 역할: {meta['role']}",
                f"- 대표 확인 경로: `{dataset['path']}`",
                f"- 원본 인코딩: {dataset['encoding']}",
                f"- 표본 확인 행: 최대 {dataset['sample_rows']}행",
                "",
            ]
        )

        if dataset["dataset_name"] == "점포-상권":
            variants = dataset["schema_variants"]
            for variant_index, variant in enumerate(variants, start=1):
                label = "2021~2024년 한글 헤더" if variant_index == 1 else "2025년 영문 헤더"
                lines.extend(
                    [
                        f"### {label}",
                        "",
                        f"확인 파일: `{variant['path']}`",
                        "",
                        *variable_table(variant["columns"]),
                        "",
                    ]
                )
        else:
            lines.extend([*variable_table(dataset["columns"]), ""])

        if dataset["dataset_name"] == "영역-상권":
            lines.extend(
                [
                    "공간파일 PRJ 원문에 기록된 좌표계 이름은 `Korea_2000_Korea_Central_Belt`이다. EPSG 코드 확인과 도형 유효성 검사는 Stage 2에서 수행한다.",
                    "",
                ]
            )

    lines.extend(
        [
            "## 정책추천·RAG 단계에서 나중에 수집할 자료",
            "",
            "> 아래 자료는 현재 수집·분석하지 않는다. **Stage 8~9 시작 시 최신 문서와 기준일을 확인해 반드시 별도로 수집한다.**",
            "",
            "### 필수 후보",
            "",
            "- [기업마당 지원사업 공고 API](https://www.data.go.kr/data/15157820/openapi.do): 정책 공고 수집",
            "- [서울시 2026년 중소기업육성자금](https://news.seoul.go.kr/economy/rearing-funds): 서울시 정책자금 원문",
            "- [서울시 중소기업육성자금 변경공고](https://www.seoul.go.kr/news/news_notice.do?nttNo=457365): 최신 변경내용 반영",
            "- [정책자금 지원 제외업종](https://ols.semas.or.kr/ols/pfa/SPFA207P/page.do): 업종 조건 필터",
            "",
            "### 보조 자료",
            "",
            "- [금융위원회 서민금융상품 API](https://www.data.go.kr/data/15094787/openapi.do)",
            "- [서민금융진흥원 FAQ 데이터](https://www.data.go.kr/data/15151953/fileData.do)",
            "",
            "### 선택 자료",
            "",
            "- [소상공인시장진흥공단 상가정보 API](https://www.data.go.kr/data/15012005/openapi.do)",
            "- [서울시 소상공인 종합지원 안내](https://news.seoul.go.kr/economy/small-business-supports)",
            "",
            "## 다음 작업",
            "",
            "현재 README 작성 뒤에는 원본을 그대로 보존한다. 전처리는 별도 요청이 있을 때 Stage 2의 구조·기간·연결성·값 품질 검증 계획부터 확정한 후 시작한다.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    README_PATH.write_text(build_readme(), encoding="utf-8")
    print(f"updated={README_PATH}")


if __name__ == "__main__":
    main()
