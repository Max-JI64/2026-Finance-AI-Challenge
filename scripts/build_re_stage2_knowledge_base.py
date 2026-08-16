"""Build the reviewed RE Stage 2 policy knowledge-base tables.

This is a curated transformation of the official documents collected on
2026-08-15. Missing official terms stay ``미확인``; the script never infers a
financial value from a neighbouring policy or from a service assumption.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.guards.re_stage2_guard import assert_stage2_action_allowed, load_stage2_config


KST = timezone(timedelta(hours=9))
AS_OF = "2026-08-15"
REVIEWED_AT = "2026-08-15T23:59:00+09:00"
UNKNOWN = "미확인"
NA = "해당 없음"

OUT = ROOT / "data" / "processed_re" / "policy" / "re_stage2"
REPORTS = ROOT / "reports" / "re_stage2"
RAW_SELECTED = ROOT / "data" / "raw_re" / "policy" / "selected" / AS_OF


URLS = {
    "fund": "https://www.seoul.go.kr/news/news_notice.do?nttNo=457365",
    "crisis": "https://www.bizinfo.go.kr/sii/siia/selectSIIA200Detail.do?pblancId=PBLN_000000000123842",
    "closure": "https://www.bizinfo.go.kr/sii/siia/selectSIIA200Detail.do?pblancId=PBLN_000000000119017",
    "digital": "https://www.bizinfo.go.kr/sii/siia/selectSIIA200Detail.do?pblancId=PBLN_000000000123844",
    "zero": "https://www.bizinfo.go.kr/sii/siia/selectSIIA200Detail.do?pblancId=PBLN_000000000123336",
    "safety": "https://www.bizinfo.go.kr/sii/siia/selectSIIA200Detail.do?pblancId=PBLN_000000000124676",
    "restart": "https://news.seoul.go.kr/economy/archives/573571",
    "loans": "https://www.bizinfo.go.kr/sii/siia/selectSIIA200Detail.do?pblancId=PBLN_000000000124909",
    "voucher": "https://www.bizinfo.go.kr/sii/siia/selectSIIA200Detail.do?pblancId=PBLN_000000000117908",
}


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        raise ValueError(f"Refusing to write empty CSV: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def policy(
    policy_id: str,
    version: str,
    name: str,
    provider: str,
    policy_type: str,
    purpose_tags: str,
    region: str,
    industry: str,
    age_rule: str,
    revenue_rule: str,
    employee_rule: str,
    credit_rule: str,
    start: str,
    end: str,
    exhaustion: str,
    status: str,
    notice_url: str,
    attachment_url: str,
    application_url: str,
    inquiry: str,
    effective_from: str,
    effective_to: str,
    source_path: str,
    locator: str,
    notes: str = "",
) -> dict[str, object]:
    return {
        "policy_id": policy_id,
        "policy_version": version,
        "policy_name": name,
        "provider": provider,
        "policy_type": policy_type,
        "purpose_tags": purpose_tags,
        "region_scope": region,
        "industry_scope": industry,
        "business_age_rule": age_rule,
        "revenue_rule": revenue_rule,
        "employee_rule": employee_rule,
        "credit_or_delinquency_rule": credit_rule,
        "application_start": start,
        "application_end": end,
        "budget_exhaustion_rule": exhaustion,
        "application_status_as_of": status,
        "official_notice_url": notice_url,
        "attachment_url": attachment_url,
        "application_url": application_url,
        "inquiry": inquiry,
        "effective_from": effective_from,
        "effective_to": effective_to,
        "retrieved_at": AS_OF,
        "reviewed_at": REVIEWED_AT,
        "source_status": "공식 첨부문서 확인" if attachment_url != NA else "공식 공고 확인",
        "source_path": source_path,
        "source_locator": locator,
        "official_small_business_applicability": "확인",
        "notes": notes,
    }


POLICIES = [
    policy(
        "POL_SEOUL_FUND_2026", "2026-05-04-change", "2026년도 서울특별시 중소기업육성자금 융자지원 변경계획",
        "서울특별시·서울신용보증재단", "융자;이차보전;보증연계", "경영안정;시설;창업;취약;재기",
        "서울특별시", "서울 소재 중소기업 및 소상공인; 융자제한업종 제외", NA, "세부 자금별 상이", "소기업·소상공인 기준 또는 세부 자금별 상이",
        "세부 자금별 NICE·피해·재기 조건 상이", "2026-01-02", "자금소진시", "자금 소진 시 마감; 일부 자금 분기별 한도 배분", "접수 가능 여부 개별 상담 필요",
        URLS["fund"], URLS["fund"], "https://www.seoulshinbo.co.kr", "서울신용보증재단 1577-6119", "2026-05-04", UNKNOWN,
        "data/raw_re/policy/seoul_fund/2026/2026년도 서울특별시 중소기업육성자금 융자지원 변경계획 공고/2026년_중소기업육성자금_융자지원_변경계획_공고.md",
        "본문 1~3절·붙임1", "하위 자금별 자격·한도·이차보전율을 별도 금융 이벤트로 분리",
    ),
    policy(
        "POL_SEOUL_CRISIS_TRACK2_2026H2", "2026-06-30", "2026년 하반기 위기 소상공인 조기발굴 및 선제지원(Track2)",
        "서울신용보증재단", "보조금;컨설팅", "매출감소;재해;경영개선;사업정리", "서울특별시", "점포형 소상공인; 지원제한업종 제외", "개업 후 2년 이상",
        "2024년 대비 2025년 또는 2025년 상반기 대비 하반기 매출 감소; 재해피해는 확인서로 대체", "소상공인 기준", "재단 구상채권·특수채권·관리종결 상태 제외",
        "2026-07-02 10:00", "예산소진시", "선착 접수·예산 소진 시 마감", "접수 중으로 공고됐으나 현재 잔여예산 재확인 필요", URLS["crisis"],
        "https://www.bizinfo.go.kr/cmm/fms/fileDown.do?atchFileId=FILE_000000000762454&fileSn=1", "https://www.seoulsbdc.or.kr", "서울신용보증재단 1577-6119", "2026-07-02", "2026-11-30",
        "data/raw_re/policy/selected/2026-08-15/POL_SEOUL_CRISIS_TRACK2_2026H2/2026_하반기_위기_소상공인_Track2_공고.pdf", "PDF 1~7쪽",
    ),
    policy(
        "POL_SEOUL_CLOSURE_2026", "2026-02", "2026년 새 길 여는 폐업지원", "서울신용보증재단", "보조금;컨설팅;교육",
        "폐업;재취업;재창업", "서울특별시", "폐업 예정 점포형 소상공인; 지원제한업종 제외", "개업 후 6개월 이상", "소상공인 업종별 평균매출액 기준", "소상공인 기준",
        "재단 구상채권·특수채권·관리종결 상태 제외", "2026-02-12", "예산소진시", "예산 소진 시 자동 마감", "접수 중으로 공고됐으나 현재 잔여예산 재확인 필요", URLS["closure"],
        "https://www.bizinfo.go.kr/cmm/fms/fileDown.do?atchFileId=FILE_000000000745140&fileSn=0", "https://www.seoulsbdc.or.kr", "서울신용보증재단 1577-6119", "2026-02-12", "2026-11-30",
        "data/raw_re/policy/selected/2026-08-15/POL_SEOUL_CLOSURE_2026/2026_새_길_여는_폐업지원_공고.pdf", "PDF 1~6쪽", "2026년 10월 이내 폐업 신고 완료 예정자",
    ),
    policy(
        "POL_SEOUL_DIGITAL_MIDLIFE_2026H2", "2026-06-30", "2026년 하반기 중장년 소상공인 디지털 전환지원", "서울신용보증재단", "보조금;컨설팅;교육",
        "디지털전환;온라인진출;마케팅", "서울특별시", "소상공인; 지원제한업종 제외", "개업일 2025-07-01 이전", "소상공인 업종별 평균매출액 기준", "소상공인 기준",
        "재단 구상채권·특수채권·관리종결 상태 제외", "2026-07-02 10:00", "예산소진시", "예산 소진 시 마감", "접수 중으로 공고됐으나 현재 잔여예산 재확인 필요", URLS["digital"],
        "https://www.bizinfo.go.kr/cmm/fms/fileDown.do?atchFileId=FILE_000000000762474&fileSn=1", "https://www.seoulsbdc.or.kr", "서울신용보증재단 1577-6119", "2026-07-02", "2027-11-30",
        "data/raw_re/policy/selected/2026-08-15/POL_SEOUL_DIGITAL_MIDLIFE_2026H2/2026_하반기_중장년_디지털전환_공고.pdf", "PDF 1~6쪽", "대표자 만 40세 이상; 만 50세 이상·취약업종 우대",
    ),
    policy(
        "POL_SEOUL_ZERO_MARKET_2026_2", "2026-06-17-2nd", "2026년 서울제로마켓 활성화 사업 참여자 2차 모집", "서울특별시·서울디자인재단", "보조금",
        "제로웨이스트;친환경포장;다회용기", "서울특별시", "기업·소상공인·단체; 온·오프라인 가능", NA, NA, NA, NA,
        "2026-06-17", "모집마감시", "63개소 모집 완료 시 마감", "접수 중으로 공고됐으나 모집 완료 여부 재확인 필요", URLS["zero"],
        "https://www.bizinfo.go.kr/cmm/fms/fileDown.do?atchFileId=FILE_000000000760508&fileSn=1", "mailto:sup_zero@seouldesign.or.kr", "서울디자인재단 02-2153-0426·0423", "2026-06-17", UNKNOWN,
        "data/raw_re/policy/selected/2026-08-15/POL_SEOUL_ZERO_MARKET_2026_2/2026_서울제로마켓_2차_공고.hwpx", "HWPX 공모개요·지원금액·지원방법",
    ),
    policy(
        "POL_SEOUL_SAFETY_TEST_2026H2", "2026-07-23", "2026년 하반기 소상공인 안전검사 지원사업", "서울특별시·한국건설생활환경시험연구원", "보조금",
        "안전검사;생활용품;어린이제품", "서울특별시", "제조·유통 관련 소상공인", NA, "어린이제품은 2025년 연매출 1억400만원 미만", "소상공인 기준", "국세·지방세 완납",
        UNKNOWN, "예산소진시", "예산 소진 시 마감", "접수 중으로 공고됐으나 잔여예산 재확인 필요", URLS["safety"],
        "https://www.bizinfo.go.kr/cmm/fms/fileDown.do?atchFileId=FILE_000000000765823&fileSn=1", NA, "서울시 02-2133-5375; KCL 02-2102-2565", "2026-07-23", UNKNOWN,
        "data/raw_re/policy/selected/2026-08-15/POL_SEOUL_SAFETY_TEST_2026H2/2026_서울_소상공인_안전검사_하반기.pdf", "PDF 1쪽 포스터·공식 HTML 본문", "전화 접수; PDF가 이미지형이라 공식 HTML도 병행 근거로 사용",
    ),
    policy(
        "POL_SEOUL_RESTART_2026", "2026-07-16", "서울형 다시서기 프로젝트", "서울특별시·서울신용보증재단", "보조금;보증;이차보전;교육;컨설팅",
        "재기;재창업;채무종결", "서울특별시", "성실실패·성실상환·재창업 소상공인", NA, NA, "소상공인 기준", "신용회복·회생·파산면책 완료, 재단채무 상환완료 등 유형별 조건",
        "2026-07-08", "2026-10-30", "600명 모집 완료 시 조기마감", "접수기간 내; 모집 완료 여부 재확인 필요", URLS["restart"], NA,
        "https://www.seoulsbdc.or.kr", "서울시 소상공인정책과 02-2133-5549", "2026-07-08", "2026-10-30",
        "data/raw_re/policy/selected/2026-08-15/POL_SEOUL_RESTART_2026/official_page.html", "공식 본문 지원대상·지원내용·신청기간", "대출 보증의 보증한도는 공식 현재 페이지에서 미확인",
    ),
    policy(
        "POL_SEMAS_REFINANCE_2026", "2026-07-29-change4", "2026년 소상공인 정책자금 대환대출", "중소벤처기업부·소상공인시장진흥공단", "정책자금 융자;대환",
        "고금리대환;만기연장", "전국", "소상공인; 융자제외업종 제외", NA, NA, "소상공인 기준", "원칙적으로 NCB 919점 이하; 공고상 예외 유형 존재",
        "2026-01-05", "예산소진시", "접수 순서 처리·예산 소진 시 마감", "세부 자금 접수상태를 접수시스템에서 재확인 필요", URLS["loans"],
        "https://www.bizinfo.go.kr/cmm/fms/fileDown.do?atchFileId=FILE_000000000766857&fileSn=1", "https://ols.semas.or.kr", "소상공인통합콜센터 1533-0100 내선 1", "2026-07-29", UNKNOWN,
        "data/raw_re/policy/selected/2026-08-15/POL_SEMAS_POLICY_LOANS_2026_CHANGE4/2026_소상공인_정책자금_융자사업_4차변경.pdf", "PDF 2~5쪽·11~12쪽",
    ),
    policy(
        "POL_SEMAS_RECHALLENGE_2026", "2026-07-29-change4", "2026년 소상공인 정책자금 재도전특별자금", "중소벤처기업부·소상공인시장진흥공단", "정책자금 융자",
        "재창업;채무조정;재기사업화", "전국", "소상공인; 융자제외업종 제외", "유형별 재창업 업력 조건 상이", "도약형은 전년 대비 또는 최근 2분기 매출 5% 이상 증가 조건 중 하나", "도약형은 고용 증가 또는 2인 이상 조건도 성장요건으로 선택 가능",
        "채무조정·정책자금 성실상환 조건이 유형별 적용", "2026-01-12", "예산소진시", "접수 순서 처리·예산 소진 시 마감", "세부 자금 접수상태를 접수시스템에서 재확인 필요", URLS["loans"],
        "https://www.bizinfo.go.kr/cmm/fms/fileDown.do?atchFileId=FILE_000000000766857&fileSn=1", "https://ols.semas.or.kr", "소상공인통합콜센터 1533-0100 내선 1", "2026-07-29", UNKNOWN,
        "data/raw_re/policy/selected/2026-08-15/POL_SEMAS_POLICY_LOANS_2026_CHANGE4/2026_소상공인_정책자금_융자사업_4차변경.pdf", "PDF 2~5쪽·13~14쪽",
    ),
    policy(
        "POL_SEMAS_STABILITY_VOUCHER_2026", "2026-01-28", "소상공인 경영안정 바우처 지원사업", "중소벤처기업부·소상공인시장진흥공단", "바우처",
        "고정비;공과금;사회보험;연료비", "전국", "소상공인; 정책자금 융자제외업종 제외", "2025-12-31 이전 개업", "2025년 연매출 0원 초과 1억400만원 미만", "소상공인 기준", NA,
        "2026-02-09 09:00", "2026-12-18 18:00", "예산 소진 시 조기마감", "접수기간 내; 예산 소진 여부 재확인 필요", URLS["voucher"],
        "https://www.bizinfo.go.kr/cmm/fms/fileDown.do?atchFileId=FILE_000000000741999&fileSn=0", "https://www.sbiz24.kr", "경영안정 바우처 1533-0600", "2026-02-09", "2026-12-31",
        "data/raw_re/policy/selected/2026-08-15/POL_SEMAS_STABILITY_VOUCHER_2026/2026_소상공인_경영안정_바우처_공고.pdf", "PDF 1~5쪽", "바우처 사용기한은 2026-12-31",
    ),
]


def event(policy_id: str, event_id: str, event_name: str, support_form: str, maximum: object,
          support_rate: str, interest: str, subsidy: str, guarantee_fee: str, grace: str,
          repayment: str, repayment_method: str, matching: str, expenses: str,
          payment: str, delay: str, combinability: str, unquantifiable: str,
          source_path: str, locator: str) -> dict[str, object]:
    return {
        "policy_id": policy_id, "event_id": event_id, "event_name": event_name,
        "support_form": support_form, "currency": "KRW", "minimum_amount": UNKNOWN,
        "maximum_amount": maximum, "support_rate": support_rate,
        "interest_rate_rule": interest, "interest_subsidy_rule": subsidy,
        "guarantee_fee_rule": guarantee_fee, "grace_period": grace,
        "repayment_period": repayment, "repayment_method": repayment_method,
        "matching_fund_rate": matching, "eligible_expense_types": expenses,
        "payment_method": payment, "reimbursement_delay_rule": delay,
        "combinability_rule": combinability, "unquantifiable_conditions": unquantifiable,
        "source_status": "공식 첨부문서 확인", "source_path": source_path,
        "source_locator": locator, "reviewed_at": REVIEWED_AT,
    }


FUND_SOURCE = "data/raw_re/policy/seoul_fund/2026/2026년도 서울특별시 중소기업육성자금 융자지원 변경계획 공고/2026년_중소기업육성자금_융자지원_변경계획_공고.md"
LOAN_SOURCE = "data/raw_re/policy/selected/2026-08-15/POL_SEMAS_POLICY_LOANS_2026_CHANGE4/2026_소상공인_정책자금_융자사업_4차변경.pdf"


FINANCIAL_EVENTS = [
    event("POL_SEOUL_FUND_2026", "SEOUL_FACILITY", "시설자금", "직접융자", "별표3 세부사업별 상이", NA, "연 2.8%", NA, NA, "별표3 세부사업별 상이", "별표3 세부사업별 상이", "별표3 세부사업별 상이", NA, "시설·입지·유통구조개선 등", "대출 실행", UNKNOWN, UNKNOWN, "세부사업 선택 전 단일 현금이벤트 계산 불가", FUND_SOURCE, "붙임1 시설자금·별표3"),
    event("POL_SEOUL_FUND_2026", "SEOUL_GROWTH", "성장기반자금", "직접융자", 500_000_000, NA, "연 3.0%", NA, NA, "1년 또는 2년", "총 5년 또는 2년 만기", "1년거치 4년·2년거치 3년 균분 또는 2년 만기 일시", NA, "경영안정자금", "대출 실행", UNKNOWN, UNKNOWN, "실제 승인금액·실행일", FUND_SOURCE, "붙임1 성장기반자금"),
    event("POL_SEOUL_FUND_2026", "SEOUL_EMERGENCY", "긴급자영업자금", "직접융자", 50_000_000, NA, "연 2.5%", NA, NA, "1년", "총 5년", "1년거치 4년 균분", NA, "경영안정자금", "대출 실행", UNKNOWN, UNKNOWN, "실제 승인금액·실행일", FUND_SOURCE, "붙임1 긴급자영업자금"),
    event("POL_SEOUL_FUND_2026", "SEOUL_INNOVATION", "혁신형기업도약자금", "직접융자", 300_000_000, NA, "연 3.0%", NA, NA, "1년 또는 해당 없음", "총 5년 또는 2년 만기", "1년거치 4년 균분 또는 2년 만기 일시", NA, "경영안정자금", "대출 실행", UNKNOWN, UNKNOWN, "실제 승인금액·실행일", FUND_SOURCE, "붙임1 혁신형기업도약자금"),
    event("POL_SEOUL_FUND_2026", "SEOUL_DISASTER", "재해중소기업자금", "직접융자", 200_000_000, NA, "연 2.0%", NA, NA, "1년 또는 해당 없음", "총 5년 또는 2년 만기", "1년거치 4년 균분 또는 2년 만기 일시", NA, "재해 복구·경영안정", "대출 실행", UNKNOWN, UNKNOWN, "실제 승인금액·실행일", FUND_SOURCE, "붙임1 재해중소기업자금"),
    event("POL_SEOUL_FUND_2026", "SEOUL_ECONOMY", "경제활성화자금", "은행협력자금", 500_000_000, NA, "은행 심사금리", "1.8%p·대출일부터 4년 이내", NA, "선택형", "최대 5년", "1년거치 2·3·4년 균분, 2년 만기 일시, 2년거치 3년 균분 중 선택", NA, "경영안정", "은행 대출 실행", UNKNOWN, UNKNOWN, "은행 적용금리·승인금액", FUND_SOURCE, "붙임1 경제활성화자금"),
    event("POL_SEOUL_FUND_2026", "SEOUL_INCLUSIVE", "포용금융자금", "은행협력자금", 30_000_000, NA, "은행 심사금리", "1.8%p·대출일부터 4년 이내", NA, "1년 또는 2년", "총 5년", "1년거치 4년 또는 2년거치 3년 균분", NA, "경영안정", "은행 대출 실행", UNKNOWN, UNKNOWN, "은행 적용금리·승인금액", FUND_SOURCE, "붙임1 포용금융자금"),
    event("POL_SEOUL_FUND_2026", "SEOUL_STARTUP", "창업기업자금", "은행협력자금", 100_000_000, NA, "은행 심사금리", "1.8%p·대출일부터 4년 이내", NA, "선택형", "최대 5년", "선택형", NA, "창업·임차·경영", "은행 대출 실행", UNKNOWN, UNKNOWN, "일반 5천만원·특화 7천만원·임차 5천만원의 세부한도 조합", FUND_SOURCE, "붙임1 창업기업자금"),
    event("POL_SEOUL_FUND_2026", "SEOUL_FAST_DREAM", "신속드림자금", "은행협력자금", 30_000_000, NA, "은행 심사금리", "1.8%p·대출일부터 4년 이내", NA, "1년", "총 5년", "1년거치 4년 균분", NA, "경영안정", "인터넷전문은행 대출 실행", UNKNOWN, UNKNOWN, "카카오뱅크·케이뱅크 심사 결과", FUND_SOURCE, "붙임1 신속드림자금"),
    event("POL_SEOUL_FUND_2026", "SEOUL_VULNERABLE", "취약사업자지원자금", "은행협력자금", 50_000_000, NA, "은행 심사금리", "최대 2.5%p·대출일부터 5년 이내", NA, "1년 또는 2년", "총 5년", "1년거치 4년 또는 2년거치 3년 균분", NA, "경영안정", "은행 대출 실행", UNKNOWN, UNKNOWN, "취약사업자 세부기준은 재단 별도 공고", FUND_SOURCE, "붙임1 취약사업자지원자금"),
    event("POL_SEOUL_FUND_2026", "SEOUL_DELIVERY", "서울배달상생자금", "은행협력자금", 100_000_000, NA, "은행 심사금리", "2.5%p·대출일부터 5년 이내", NA, "1년", "총 5년", "1년거치 4년 균분", NA, "경영안정", "은행 대출 실행", UNKNOWN, UNKNOWN, "땡겨요 주문실적·은행 승인", FUND_SOURCE, "붙임1 서울배달상생자금"),
    event("POL_SEOUL_FUND_2026", "SEOUL_HOPE", "희망동행자금", "은행협력자금", 100_000_000, NA, "은행 심사금리", "1.8%p·대출일부터 7년 이내", NA, "1년 또는 2년", "총 5년 또는 7년", "1년거치 4년 또는 2년거치 5년 균분", NA, "경영애로·대환성 지원", "은행 대출 실행", UNKNOWN, UNKNOWN, "은행 적용금리·승인금액", FUND_SOURCE, "붙임1 희망동행자금"),
    event("POL_SEOUL_FUND_2026", "SEOUL_JOBS", "일자리창출우수기업자금", "은행협력자금", 500_000_000, NA, "은행 심사금리", "2.5%p·대출일부터 5년 이내", NA, "1년 또는 2년", "총 5년", "1년거치 4년 또는 2년거치 3년 균분", NA, "고용·경영안정", "은행 대출 실행", UNKNOWN, UNKNOWN, "사회보험가입촉진 유형은 5천만원 한도", FUND_SOURCE, "붙임1 일자리창출우수기업자금"),
    event("POL_SEOUL_FUND_2026", "SEOUL_ESG", "ESG자금", "은행협력자금", 100_000_000, NA, "은행 심사금리", "2.5%p·대출일부터 5년 이내", NA, "1년 또는 2년", "총 5년", "1년거치 4년 또는 2년거치 3년 균분", NA, "ESG 실천·경영안정", "은행 대출 실행", UNKNOWN, UNKNOWN, "ESG 인정 기준·은행 승인", FUND_SOURCE, "붙임1 ESG자금"),
    event("POL_SEOUL_FUND_2026", "SEOUL_RESTART_FUND", "재기지원자금", "은행협력자금", 100_000_000, NA, "은행 심사금리", "2.5%p·대출일부터 5년 이내", NA, "1년 또는 2년", "총 5년", "1년거치 4년 또는 2년거치 3년 균분", NA, "재기·경영안정", "은행 대출 실행", UNKNOWN, "다시서기·위기지원 참여기업 연계; 중복효과 이중계상 금지", "은행 적용금리·승인금액", FUND_SOURCE, "붙임1 재기지원자금"),
    event("POL_SEOUL_FUND_2026", "SEOUL_MIDEAST", "중동피해위기대응자금", "은행협력자금", 50_000_000, NA, "은행 심사금리", "2년간 2.5%p·3년간 1.8%p", NA, "1년", "총 5년", "1년거치 4년 균분", NA, "중동전쟁 직접피해 대응", "은행 대출 실행", UNKNOWN, UNKNOWN, "직접피해업종은 별도 공고", FUND_SOURCE, "붙임1 중동피해위기대응자금"),
    event("POL_SEOUL_FUND_2026", "SEOUL_SAFE_ACCOUNT", "안심통장 하반기", "한도대출", UNKNOWN, UNKNOWN, UNKNOWN, UNKNOWN, UNKNOWN, UNKNOWN, UNKNOWN, UNKNOWN, UNKNOWN, UNKNOWN, UNKNOWN, UNKNOWN, UNKNOWN, "하반기 3천억원 별도 공고 예정으로 조건 미확인", FUND_SOURCE, "본문 1절 안심통장"),
    event("POL_SEOUL_CRISIS_TRACK2_2026H2", "CRISIS_SOLUTION", "솔루션 이행비용", "사후정산 보조금", 3_000_000, "부가세 제외 100%; 간이·면세 공급자 거래는 총비용 90% 이내", NA, NA, NA, NA, NA, NA, "자부담은 부가세 및 지원초과분", "경영개선 또는 사업정리 항목", "선지급 후 증빙·정산", "비용지원 2026년 11월까지; 개별 지급일 미확인", "2025~2026 서울시 종합지원 비용지원과 중복 제한", "경영진단 결과와 항목 연계 필요", POLICIES[1]["source_path"], "PDF 2~7쪽"),
    event("POL_SEOUL_CLOSURE_2026", "CLOSURE_SOLUTION", "폐업 솔루션 이행비용", "사후정산 보조금", 3_000_000, "부가세 제외 100%; 간이·면세 공급자 거래는 총비용 90% 이내", NA, NA, NA, NA, NA, NA, "자부담은 부가세 및 지원초과분", "임차료·원상복구·보관·수리·양도수수료·광고·교육", "선지급 후 폐업완료 확인·정산", UNKNOWN, "희망리턴패키지 철거비·국민내일배움카드와 항목별 중복 제한", "교육·컨설팅 이수 및 폐업사실증명 필요", POLICIES[2]["source_path"], "PDF 1~6쪽"),
    event("POL_SEOUL_DIGITAL_MIDLIFE_2026H2", "DIGITAL_SOLUTION", "디지털 솔루션 이행비용", "사후정산 보조금", 3_000_000, "부가세 제외 100%; 간이·면세 공급자 거래는 총비용 90% 이내", NA, NA, NA, NA, NA, NA, "자부담은 부가세 및 지원초과분", "온라인진출·온라인마케팅·디지털환경구축", "승인 후 선지급·완료증빙 후 정산", UNKNOWN, "2026 서울시 종합지원 비용지원과 중복 제한", "교육 수료·컨설팅·사전 승인 필요", POLICIES[3]["source_path"], "PDF 2~5쪽"),
    event("POL_SEOUL_DIGITAL_MIDLIFE_2026H2", "DIGITAL_EXCELLENCE", "우수기업 정착비용", "보조금", 1_000_000, UNKNOWN, NA, NA, NA, NA, NA, NA, UNKNOWN, "디지털 전환 정착", UNKNOWN, "2027년 우수기업 선발 후 지급시점 미확인", UNKNOWN, "우수기업 선발 기준·세부 집행조건 미확인", POLICIES[3]["source_path"], "PDF 2·5쪽"),
    event("POL_SEOUL_ZERO_MARKET_2026_2", "ZERO_MARKET_GRANT", "매장별 보조금", "보조금", 1_200_000, UNKNOWN, NA, NA, NA, NA, NA, NA, "프랜차이즈 본점·직영점은 총사업비 50% 이상 자부담", "친환경·다회용 포장재·홍보·교육·시설장비 임차·제한적 인건비·대여비", "결과보고·증빙 후 사후정산", UNKNOWN, "동일·유사 국비·시비 지원 결정 사업자 제외", "인건비·대여비는 각각 사업비 50% 이내; 판매물품·경상비 등 제외", POLICIES[4]["source_path"], "HWPX 지원금액·지원항목"),
    event("POL_SEOUL_SAFETY_TEST_2026H2", "SAFETY_TEST", "안전검사 비용", "검사비 지원", 2_000_000, UNKNOWN, NA, NA, NA, NA, NA, NA, UNKNOWN, "생활용품·어린이제품 검사비", UNKNOWN, UNKNOWN, UNKNOWN, "검사기관별 신청·지급 절차 미확인", POLICIES[5]["source_path"], "PDF 1쪽·공식 HTML"),
    event("POL_SEOUL_RESTART_2026", "RESTART_SEED", "재도전 초기자금", "보조금", 2_000_000, "부가세 본인 부담", NA, NA, NA, NA, NA, NA, "부가세·초과분", "임차료·물품구입·마케팅·홍보 등", UNKNOWN, UNKNOWN, "재기지원자금 대출과 연결 가능하나 이중계상 금지", "현재 공식 페이지에서 지급시점·세부 정산절차 미확인", POLICIES[6]["source_path"], "공식 본문 지원내용"),
    event("POL_SEOUL_RESTART_2026", "RESTART_GUARANTEE", "저금리 대출보증", "보증·이차보전 연계", 100_000_000, NA, "은행 심사금리", "연계 재기지원자금은 2.5%p·5년 이내", "1인당 최대 40만원 보증료 지원", "1년 또는 2년", "총 5년", "1년거치 4년 또는 2년거치 3년 균분", NA, "운전자금", "은행 대출 실행", UNKNOWN, "서울시 재기지원자금과 동일 대출 이벤트로 취급", "최종 보증·대출 승인금액은 심사 결과", FUND_SOURCE, "붙임1 재기지원자금·붙임3 다시서기"),
    event("POL_SEMAS_REFINANCE_2026", "SEMAS_REFINANCE", "대환대출", "대리대출", 50_000_000, NA, "연 4.5% 고정", NA, NA, "0년 또는 2년", "총 10년", "10년 분할 또는 2년거치 8년 분할", NA, "2025-06-30 이전 사업자대출·사업용도 가계대출 대환", "금융기관 대환 실행", UNKNOWN, "기존 대환실행액은 한도에서 차감", "실제 승인액·대환 실행일", LOAN_SOURCE, "PDF 11~12쪽"),
    event("POL_SEMAS_RECHALLENGE_2026", "SEMAS_RECHALLENGE_GENERAL", "재도전특별자금 일반형", "직접대출", 70_000_000, NA, "정책자금 기준금리 +1.6%p", NA, NA, "2년", "총 5년", "거치 후 분할상환", NA, "운전자금", "소진공 직접대출", UNKNOWN, UNKNOWN, "분기별 기준금리·승인액", LOAN_SOURCE, "PDF 13~14쪽"),
    event("POL_SEMAS_RECHALLENGE_2026", "SEMAS_RECHALLENGE_HOPE", "재도전특별자금 희망형", "직접대출", 100_000_000, NA, "정책자금 기준금리 +0.6%p", NA, NA, "2년", "총 5년", "거치 후 분할상환", NA, "운전자금", "소진공 직접대출", UNKNOWN, UNKNOWN, "분기별 기준금리·승인액", LOAN_SOURCE, "PDF 13~14쪽"),
    event("POL_SEMAS_RECHALLENGE_2026", "SEMAS_RECHALLENGE_LEAP", "재도전특별자금 도약형", "직접대출", 200_000_000, NA, "정책자금 기준금리 +0.4%p", NA, NA, "2년", "총 5년", "거치 후 분할상환", NA, "운전자금", "소진공 직접대출", UNKNOWN, UNKNOWN, "분기별 기준금리·승인액", LOAN_SOURCE, "PDF 13~14쪽"),
    event("POL_SEMAS_STABILITY_VOUCHER_2026", "STABILITY_VOUCHER", "경영안정 바우처", "카드 바우처", 250_000, "지정 사용처 결제액 100%, 25만원 한도", NA, NA, NA, NA, NA, NA, NA, "전기·가스·수도·4대보험·사업용 차량연료·전통시장 화재공제", "등록 카드 결제 시 자동 선차감", "선정 후 카드사 등록 일정", "동일 비용의 타 지원사업 중복 시 환수 가능", "2026-12-31 미사용 잔액 회수", POLICIES[9]["source_path"], "PDF 2~5쪽"),
]


def rule(policy_id: str, rule_id: str, group: str, category: str, operator: str,
         value: str, source_path: str, locator: str, note: str = "") -> dict[str, object]:
    return {
        "policy_id": policy_id, "rule_id": rule_id, "rule_group": group,
        "category": category, "operator": operator, "value": value,
        "source_status": "공식 공고 확인" if source_path.endswith(".html") else "공식 첨부문서 확인",
        "source_locator": locator, "reviewed_at": REVIEWED_AT, "notes": note,
    }


ELIGIBILITY_RULES = [
    rule("POL_SEOUL_FUND_2026", "FUND_ALL_01", "all", "region", "equals", "서울특별시", FUND_SOURCE, "본문 2절"),
    rule("POL_SEOUL_FUND_2026", "FUND_ALL_02", "all", "business_scale", "in", "중소기업 또는 소상공인", FUND_SOURCE, "본문 2절·붙임1"),
    rule("POL_SEOUL_FUND_2026", "FUND_EX_01", "exclude", "industry", "in", "붙임2 융자지원 제한업종", FUND_SOURCE, "붙임2"),
    rule("POL_SEOUL_FUND_2026", "FUND_VARIANT", "variant", "subfund", "requires", "세부 자금별 추가요건", FUND_SOURCE, "붙임1", "단일 적격판정 전 하위 자금 선택 필요"),
    rule("POL_SEOUL_CRISIS_TRACK2_2026H2", "CRISIS_ALL_01", "all", "region", "equals", "서울특별시", POLICIES[1]["source_path"], "PDF 1쪽"),
    rule("POL_SEOUL_CRISIS_TRACK2_2026H2", "CRISIS_ALL_02", "all", "business_place", "equals", "유상 임대차계약을 맺은 독점적 고정 점포", POLICIES[1]["source_path"], "PDF 1쪽"),
    rule("POL_SEOUL_CRISIS_TRACK2_2026H2", "CRISIS_ALL_03", "all", "business_age", ">=", "2년", POLICIES[1]["source_path"], "PDF 1쪽"),
    rule("POL_SEOUL_CRISIS_TRACK2_2026H2", "CRISIS_ANY_01", "any", "sales", "decreased", "2024→2025 또는 2025 상반기→하반기; 신고 완료 시 2025 하반기→2026 상반기", POLICIES[1]["source_path"], "PDF 1쪽"),
    rule("POL_SEOUL_CRISIS_TRACK2_2026H2", "CRISIS_ANY_02", "any", "disaster", "has_document", "유효한 재해중소기업 확인증 또는 피해사실확인서", POLICIES[1]["source_path"], "PDF 1쪽"),
    rule("POL_SEOUL_CRISIS_TRACK2_2026H2", "CRISIS_EX_01", "exclude", "status", "in", "휴업·폐업", POLICIES[1]["source_path"], "PDF 2쪽"),
    rule("POL_SEOUL_CRISIS_TRACK2_2026H2", "CRISIS_EX_02", "exclude", "prior_support", "in", "2025~2026 서울시 소상공인 종합지원 4개 비용지원사업", POLICIES[1]["source_path"], "PDF 2쪽"),
    rule("POL_SEOUL_CLOSURE_2026", "CLOSE_ALL_01", "all", "region", "equals", "서울특별시", POLICIES[2]["source_path"], "PDF 2쪽"),
    rule("POL_SEOUL_CLOSURE_2026", "CLOSE_ALL_02", "all", "status", "equals", "신청일 현재 영업 중인 폐업 예정자", POLICIES[2]["source_path"], "PDF 2쪽"),
    rule("POL_SEOUL_CLOSURE_2026", "CLOSE_ALL_03", "all", "business_age", ">=", "6개월", POLICIES[2]["source_path"], "PDF 2쪽"),
    rule("POL_SEOUL_CLOSURE_2026", "CLOSE_ALL_04", "all", "closure_date", "<=", "2026-10-31", POLICIES[2]["source_path"], "PDF 2쪽"),
    rule("POL_SEOUL_CLOSURE_2026", "CLOSE_EX_01", "exclude", "business_place", "equals", "자가 사업장", POLICIES[2]["source_path"], "PDF 2쪽", "가족 소유라도 정상 임대차·지급증빙 시 예외"),
    rule("POL_SEOUL_CLOSURE_2026", "CLOSE_EX_02", "exclude", "prior_support", "in", "2025~2026 재단 비용지원사업", POLICIES[2]["source_path"], "PDF 3쪽"),
    rule("POL_SEOUL_DIGITAL_MIDLIFE_2026H2", "DIGI_ALL_01", "all", "region", "equals", "서울특별시", POLICIES[3]["source_path"], "PDF 1쪽"),
    rule("POL_SEOUL_DIGITAL_MIDLIFE_2026H2", "DIGI_ALL_02", "all", "representative_age", ">=", "만 40세", POLICIES[3]["source_path"], "PDF 1쪽"),
    rule("POL_SEOUL_DIGITAL_MIDLIFE_2026H2", "DIGI_ALL_03", "all", "opening_date", "<", "2025-07-01", POLICIES[3]["source_path"], "PDF 1쪽"),
    rule("POL_SEOUL_DIGITAL_MIDLIFE_2026H2", "DIGI_PREF_01", "preference", "representative_age", ">=", "만 50세", POLICIES[3]["source_path"], "PDF 1쪽"),
    rule("POL_SEOUL_DIGITAL_MIDLIFE_2026H2", "DIGI_PREF_02", "preference", "industry", "in", "숙박·음식점업; 제조업; 수리·기타서비스업", POLICIES[3]["source_path"], "PDF 1쪽"),
    rule("POL_SEOUL_DIGITAL_MIDLIFE_2026H2", "DIGI_EX_01", "exclude", "prior_support", "in", "2023~2025 동일사업 또는 2026 서울시 종합지원 4개 사업", POLICIES[3]["source_path"], "PDF 1쪽"),
    rule("POL_SEOUL_ZERO_MARKET_2026_2", "ZERO_ALL_01", "all", "region", "equals", "서울특별시", POLICIES[4]["source_path"], "HWPX 공모개요"),
    rule("POL_SEOUL_ZERO_MARKET_2026_2", "ZERO_ALL_02", "all", "operation", "contains_any", "다회용기 배달 또는 무포장·소분·리필·친환경포장·포장재 감축", POLICIES[4]["source_path"], "HWPX 지원자격"),
    rule("POL_SEOUL_ZERO_MARKET_2026_2", "ZERO_ALL_03", "all", "business_registration", "has", "물품판매 또는 음식 조리·판매 가능 업종", POLICIES[4]["source_path"], "HWPX 지원자격"),
    rule("POL_SEOUL_ZERO_MARKET_2026_2", "ZERO_EX_01", "exclude", "status", "in", "폐업·사실상 폐업·휴업", POLICIES[4]["source_path"], "HWPX 부적격대상"),
    rule("POL_SEOUL_ZERO_MARKET_2026_2", "ZERO_EX_02", "exclude", "online_operation", "equals", "주소만 공유오피스 또는 위탁판매", POLICIES[4]["source_path"], "HWPX 부적격대상"),
    rule("POL_SEOUL_ZERO_MARKET_2026_2", "ZERO_EX_03", "exclude", "duplicate_support", "equals", "동일·유사 국비·시비 지원 결정", POLICIES[4]["source_path"], "HWPX 부적격대상"),
    rule("POL_SEOUL_SAFETY_TEST_2026H2", "SAFE_ALL_01", "all", "region", "equals", "서울특별시", POLICIES[5]["source_path"], "공식 HTML"),
    rule("POL_SEOUL_SAFETY_TEST_2026H2", "SAFE_ALL_02", "all", "industry", "in", "생활용품·어린이제품 제조 또는 유통 관련", POLICIES[5]["source_path"], "공식 HTML"),
    rule("POL_SEOUL_SAFETY_TEST_2026H2", "SAFE_ALL_03", "all", "tax", "equals", "국세·지방세 완납", POLICIES[5]["source_path"], "공식 HTML"),
    rule("POL_SEOUL_SAFETY_TEST_2026H2", "SAFE_CHILD_01", "child_product", "annual_sales_2025", "<", "104000000원", POLICIES[5]["source_path"], "공식 HTML", "어린이제품에만 적용"),
    rule("POL_SEOUL_RESTART_2026", "RESTART_ALL_01", "all", "region", "equals", "서울특별시", POLICIES[6]["source_path"], "공식 본문"),
    rule("POL_SEOUL_RESTART_2026", "RESTART_ANY_01", "any", "recovery_status", "in", "신용회복·회생·파산면책 완료 등 성실실패", POLICIES[6]["source_path"], "공식 본문"),
    rule("POL_SEOUL_RESTART_2026", "RESTART_ANY_02", "any", "repayment_status", "equals", "서울신용보증재단 채무 전액 성실상환", POLICIES[6]["source_path"], "공식 본문"),
    rule("POL_SEOUL_RESTART_2026", "RESTART_ANY_03", "any", "restart_status", "equals", "과거 폐업 후 재창업", POLICIES[6]["source_path"], "공식 본문"),
    rule("POL_SEMAS_REFINANCE_2026", "REFI_ALL_01", "all", "credit_score", "<=", "NCB 919점", LOAN_SOURCE, "PDF 11쪽", "공고상 개인신용평점 미적용 예외 2종 존재"),
    rule("POL_SEMAS_REFINANCE_2026", "REFI_ALL_02", "all", "loan_origination_date", "<=", "2025-06-30", LOAN_SOURCE, "PDF 11쪽"),
    rule("POL_SEMAS_REFINANCE_2026", "REFI_ANY_01", "any", "existing_interest_rate", ">=", "연 7%", LOAN_SOURCE, "PDF 11쪽"),
    rule("POL_SEMAS_REFINANCE_2026", "REFI_ANY_02", "any", "maturity_extension", "equals", "은행권 만기연장 애로 확인", LOAN_SOURCE, "PDF 11쪽"),
    rule("POL_SEMAS_REFINANCE_2026", "REFI_EX_01", "exclude", "common_loan_restriction", "in", "세금체납·신용정보등록·휴폐업·융자제외업종 등", LOAN_SOURCE, "PDF 4쪽"),
    rule("POL_SEMAS_RECHALLENGE_2026", "RECH_ANY_01", "general_any", "restart_education", "equals", "최근 1년 내 희망리턴패키지 재창업교육 25시간 이상 수료", LOAN_SOURCE, "PDF 13쪽"),
    rule("POL_SEMAS_RECHALLENGE_2026", "RECH_ANY_02", "general_any", "restart_status", "equals", "공고상 재창업 초기단계 요건 충족", LOAN_SOURCE, "PDF 13쪽"),
    rule("POL_SEMAS_RECHALLENGE_2026", "RECH_ANY_03", "general_any", "debt_adjustment", "equals", "채무조정 후 성실상환·교육 등 요건 충족", LOAN_SOURCE, "PDF 13쪽"),
    rule("POL_SEMAS_RECHALLENGE_2026", "RECH_HOPE_01", "hope", "recovery_program", "in", "2025 재기사업화 완료 또는 2026 선정·협약완료", LOAN_SOURCE, "PDF 14쪽"),
    rule("POL_SEMAS_RECHALLENGE_2026", "RECH_LEAP_01", "leap_all", "restart_business_age", ">=", "2년", LOAN_SOURCE, "PDF 14쪽"),
    rule("POL_SEMAS_RECHALLENGE_2026", "RECH_LEAP_02", "leap_all", "growth", "contains_any", "매출 5% 이상 증가 또는 고용 증가·2인 이상", LOAN_SOURCE, "PDF 14쪽"),
    rule("POL_SEMAS_RECHALLENGE_2026", "RECH_LEAP_03", "leap_all", "repayment", "equals", "최근 3년 내 연속 10일 이상 연체 없이 직접대출 분할상환 또는 완제", LOAN_SOURCE, "PDF 14쪽"),
    rule("POL_SEMAS_RECHALLENGE_2026", "RECH_EX_01", "exclude", "common_loan_restriction", "in", "세금체납·신용정보등록·휴폐업·융자제외업종 등", LOAN_SOURCE, "PDF 4쪽"),
    rule("POL_SEMAS_STABILITY_VOUCHER_2026", "VOUCH_ALL_01", "all", "annual_sales_2025", ">", "0원", POLICIES[9]["source_path"], "PDF 1쪽"),
    rule("POL_SEMAS_STABILITY_VOUCHER_2026", "VOUCH_ALL_02", "all", "annual_sales_2025", "<", "104000000원", POLICIES[9]["source_path"], "PDF 1쪽"),
    rule("POL_SEMAS_STABILITY_VOUCHER_2026", "VOUCH_ALL_03", "all", "opening_date", "<=", "2025-12-31", POLICIES[9]["source_path"], "PDF 2쪽"),
    rule("POL_SEMAS_STABILITY_VOUCHER_2026", "VOUCH_ALL_04", "all", "status", "equals", "신청일 현재 영업 중", POLICIES[9]["source_path"], "PDF 2쪽"),
    rule("POL_SEMAS_STABILITY_VOUCHER_2026", "VOUCH_EX_01", "exclude", "industry", "in", "소상공인 정책자금 융자제외업종", POLICIES[9]["source_path"], "PDF 2·6쪽"),
    rule("POL_SEMAS_STABILITY_VOUCHER_2026", "VOUCH_LIMIT_01", "limit", "multiple_businesses", "equals", "대표자 1인당 1개 사업체", POLICIES[9]["source_path"], "PDF 2쪽"),
]


def example(example_id: str, policy_id: str, scenario: str, expected_status: str,
            decisive_inputs: str, expected_rule_ids: str, reason: str,
            source_path: str, source_locator: str) -> dict[str, object]:
    return {
        "example_id": example_id, "policy_id": policy_id, "scenario": scenario,
        "expected_status": expected_status, "decisive_inputs": decisive_inputs,
        "expected_rule_ids": expected_rule_ids, "reason": reason,
        "source_path": source_path, "source_locator": source_locator,
        "review_status": "수작업정답_구현전",
    }


ELIGIBILITY_EXAMPLES = [
    example("EX_FUND_01", "POL_SEOUL_FUND_2026", "서울 소재 소상공인이지만 하위 자금을 고르지 않음", "추가 확인 필요", "서울=yes;소상공인=yes;하위자금=모름", "FUND_ALL_01;FUND_ALL_02;FUND_VARIANT", "공통대상은 맞지만 하위 자금별 요건·조건이 달라 단일 적격판정 불가", FUND_SOURCE, "본문 2절·붙임1"),
    example("EX_FUND_02", "POL_SEOUL_FUND_2026", "서울 소재 일반 유흥주점", "부적격", "서울=yes;업종=56211", "FUND_EX_01", "융자지원 제한업종", FUND_SOURCE, "붙임2"),
    example("EX_CRISIS_01", "POL_SEOUL_CRISIS_TRACK2_2026H2", "서울 임차 점포·업력 3년·2025년 매출 감소", "입력 기준 적격 후보", "서울=yes;임차점포=yes;업력=3년;매출감소=yes", "CRISIS_ALL_01;CRISIS_ALL_02;CRISIS_ALL_03;CRISIS_ANY_01", "공개된 필수조건과 매출감소 경로 충족", POLICIES[1]["source_path"], "PDF 1~2쪽"),
    example("EX_CRISIS_02", "POL_SEOUL_CRISIS_TRACK2_2026H2", "자가 사업장에서 영업", "부적격", "임차점포=no", "CRISIS_ALL_02", "유상 임대차계약의 고정 점포 조건 불충족", POLICIES[1]["source_path"], "PDF 1쪽"),
    example("EX_CLOSE_01", "POL_SEOUL_CLOSURE_2026", "서울 임차 점포·업력 1년·2026년 9월 폐업 예정", "입력 기준 적격 후보", "서울=yes;영업중=yes;업력=1년;폐업예정=2026-09", "CLOSE_ALL_01;CLOSE_ALL_02;CLOSE_ALL_03;CLOSE_ALL_04", "공개된 필수조건 충족", POLICIES[2]["source_path"], "PDF 2쪽"),
    example("EX_CLOSE_02", "POL_SEOUL_CLOSURE_2026", "신청 전에 이미 폐업", "부적격", "영업중=no", "CLOSE_ALL_02", "기폐업자는 지원대상이 아님", POLICIES[2]["source_path"], "PDF 2쪽"),
    example("EX_DIGI_01", "POL_SEOUL_DIGITAL_MIDLIFE_2026H2", "서울 소재 만 45세·2024년 개업 소상공인", "입력 기준 적격 후보", "서울=yes;나이=45;개업일=2024-01-01", "DIGI_ALL_01;DIGI_ALL_02;DIGI_ALL_03", "공개된 필수조건 충족", POLICIES[3]["source_path"], "PDF 1쪽"),
    example("EX_DIGI_02", "POL_SEOUL_DIGITAL_MIDLIFE_2026H2", "대표자 만 39세", "부적격", "나이=39", "DIGI_ALL_02", "만 40세 이상 조건 불충족", POLICIES[3]["source_path"], "PDF 1쪽"),
    example("EX_ZERO_01", "POL_SEOUL_ZERO_MARKET_2026_2", "서울 리필스테이션 운영 소상공인", "입력 기준 적격 후보", "서울=yes;리필스테이션=yes;사업자등록=yes", "ZERO_ALL_01;ZERO_ALL_02;ZERO_ALL_03", "공개된 참여자격 충족", POLICIES[4]["source_path"], "HWPX 지원자격"),
    example("EX_ZERO_02", "POL_SEOUL_ZERO_MARKET_2026_2", "공유오피스 주소만 둔 온라인 위탁판매자", "부적격", "공유오피스주소만=yes;위탁판매=yes", "ZERO_EX_02", "온라인 사업자 제한조건에 해당", POLICIES[4]["source_path"], "HWPX 부적격대상"),
    example("EX_SAFE_01", "POL_SEOUL_SAFETY_TEST_2026H2", "서울 어린이제품 제조 소상공인·2025 매출 8천만원·세금 완납", "입력 기준 적격 후보", "서울=yes;어린이제품=yes;매출=80000000;세금완납=yes", "SAFE_ALL_01;SAFE_ALL_02;SAFE_ALL_03;SAFE_CHILD_01", "공개된 조건 충족", POLICIES[5]["source_path"], "공식 HTML"),
    example("EX_SAFE_02", "POL_SEOUL_SAFETY_TEST_2026H2", "국세 체납 상태", "부적격", "국세완납=no", "SAFE_ALL_03", "국세·지방세 완납 필수조건 불충족", POLICIES[5]["source_path"], "공식 HTML"),
    example("EX_RESTART_01", "POL_SEOUL_RESTART_2026", "서울에서 과거 폐업 후 재창업한 소상공인", "입력 기준 적격 후보", "서울=yes;과거폐업=yes;재창업=yes", "RESTART_ALL_01;RESTART_ANY_03", "재창업자 공개조건 충족", POLICIES[6]["source_path"], "공식 본문"),
    example("EX_RESTART_02", "POL_SEOUL_RESTART_2026", "실패·채무상환·재창업 이력 확인 불가", "추가 확인 필요", "성실실패=모름;성실상환=모름;재창업=모름", "RESTART_ANY_01;RESTART_ANY_02;RESTART_ANY_03", "세 가지 대상 경로 중 어느 것도 확인되지 않음", POLICIES[6]["source_path"], "공식 본문"),
    example("EX_REFI_01", "POL_SEMAS_REFINANCE_2026", "NCB 900점·2025년 6월 실행·금리 8% 사업자대출", "입력 기준 적격 후보", "NCB=900;실행일=2025-06-01;기존금리=8%", "REFI_ALL_01;REFI_ALL_02;REFI_ANY_01", "공개된 신용·실행일·고금리 경로 충족", LOAN_SOURCE, "PDF 11쪽"),
    example("EX_REFI_02", "POL_SEMAS_REFINANCE_2026", "2025년 7월 실행 대출", "부적격", "실행일=2025-07-01", "REFI_ALL_02", "2025-06-30 이전 대출 조건 불충족", LOAN_SOURCE, "PDF 11쪽"),
    example("EX_RECH_01", "POL_SEMAS_RECHALLENGE_2026", "최근 1년 내 희망리턴패키지 재창업교육 25시간 수료", "입력 기준 적격 후보", "교육수료=yes;수료시점=최근1년;시간=25", "RECH_ANY_01", "일반형 재창업 준비단계 공개조건 충족", LOAN_SOURCE, "PDF 13쪽"),
    example("EX_RECH_02", "POL_SEMAS_RECHALLENGE_2026", "재창업·채무조정·재기사업화 근거가 모두 미확인", "추가 확인 필요", "재창업=모름;채무조정=모름;재기사업화=모름", "RECH_ANY_01;RECH_ANY_02;RECH_ANY_03;RECH_HOPE_01", "하위 유형 적격경로를 확정할 입력이 없음", LOAN_SOURCE, "PDF 13~14쪽"),
    example("EX_VOUCH_01", "POL_SEMAS_STABILITY_VOUCHER_2026", "2025년 매출 5천만원·2024년 개업·영업 중", "입력 기준 적격 후보", "매출=50000000;개업일=2024-01-01;영업중=yes", "VOUCH_ALL_01;VOUCH_ALL_02;VOUCH_ALL_03;VOUCH_ALL_04", "공개된 매출·개업·영업 조건 충족", POLICIES[9]["source_path"], "PDF 1~2쪽"),
    example("EX_VOUCH_02", "POL_SEMAS_STABILITY_VOUCHER_2026", "2025년 매출 2억원", "부적격", "매출=200000000", "VOUCH_ALL_02", "연매출 상한 조건 불충족", POLICIES[9]["source_path"], "PDF 1쪽"),
]


SOURCE_MAP = {
    "POL_SEOUL_FUND_2026": [
        "data/raw_re/policy/seoul_fund/2026/2026년도 서울특별시 중소기업육성자금 융자지원 변경계획 공고/2026년_중소기업육성자금_융자지원_변경계획_공고.md",
        "data/raw_re/policy/seoul_fund/2026/2026년도 서울특별시 중소기업육성자금 융자지원 변경계획 공고/별표1_경영안정자금_융자대상.md",
        "data/raw_re/policy/seoul_fund/2026/2026년도 서울특별시 중소기업육성자금 융자지원 변경계획 공고/별표2_시설자금_융자대상.md",
        "data/raw_re/policy/seoul_fund/2026/2026년도 서울특별시 중소기업육성자금 융자지원 변경계획 공고/별표3_시설자금_지원사업별_융자조건_및_한도.md",
    ],
    "POL_SEOUL_CRISIS_TRACK2_2026H2": ["official_page.html", "2026_하반기_위기_소상공인_Track2_공고.pdf"],
    "POL_SEOUL_CLOSURE_2026": ["official_page.html", "2026_새_길_여는_폐업지원_공고.pdf"],
    "POL_SEOUL_DIGITAL_MIDLIFE_2026H2": ["official_page.html", "2026_하반기_중장년_디지털전환_공고.pdf"],
    "POL_SEOUL_ZERO_MARKET_2026_2": ["official_page.html", "2026_서울제로마켓_2차_공고.hwpx"],
    "POL_SEOUL_SAFETY_TEST_2026H2": ["official_page.html", "2026_서울_소상공인_안전검사_하반기.pdf"],
    "POL_SEOUL_RESTART_2026": [
        "official_page.html",
        "data/raw_re/policy/seoul_fund/2026/소상공인 종합지원 사업/소상공인_종합지원_사업.md",
        FUND_SOURCE,
    ],
    "POL_SEMAS_REFINANCE_2026": [
        "data/raw_re/policy/selected/2026-08-15/POL_SEMAS_POLICY_LOANS_2026_CHANGE4/official_page.html",
        LOAN_SOURCE,
        "data/raw_re/policy/semas/정책자금 한눈에 보기.md",
        "data/raw_re/policy/semas/정책자금_지원_제외업종.md",
    ],
    "POL_SEMAS_RECHALLENGE_2026": [
        "data/raw_re/policy/selected/2026-08-15/POL_SEMAS_POLICY_LOANS_2026_CHANGE4/official_page.html",
        LOAN_SOURCE,
        "data/raw_re/policy/semas/정책자금 한눈에 보기.md",
        "data/raw_re/policy/semas/정책자금_지원_제외업종.md",
    ],
    "POL_SEMAS_STABILITY_VOUCHER_2026": ["official_page.html", "2026_소상공인_경영안정_바우처_공고.pdf"],
}


VERSIONS = [
    {"policy_id": "POL_SEOUL_FUND_2026", "policy_version": "2026-initial", "publication_date": "2025-12", "effective_from": "2026-01-02", "effective_to": "2026-05-03", "is_current": "no", "change_summary": "최초 공고", "source_url": "https://news.seoul.go.kr/economy/rearing-funds", "source_path": "data/raw_re/policy/seoul_fund/2026/2026년 중소기업육성자금 융자지원/경영안정자금_융자대상.md"},
    {"policy_id": "POL_SEOUL_FUND_2026", "policy_version": "2026-05-04-change", "publication_date": "2026-05-04", "effective_from": "2026-05-04", "effective_to": UNKNOWN, "is_current": "yes", "change_summary": "융자규모·하위자금 조건 변경 및 중동피해위기대응자금 신설", "source_url": URLS["fund"], "source_path": FUND_SOURCE},
]
PUBLICATION_DATES = {
    "POL_SEOUL_CRISIS_TRACK2_2026H2": "2026-06-30",
    "POL_SEOUL_CLOSURE_2026": "2026-02",
    "POL_SEOUL_DIGITAL_MIDLIFE_2026H2": "2026-06-30",
    "POL_SEOUL_ZERO_MARKET_2026_2": "2026-06-17",
    "POL_SEOUL_SAFETY_TEST_2026H2": "2026-07-23",
    "POL_SEOUL_RESTART_2026": "2026-07-16",
    "POL_SEMAS_REFINANCE_2026": "2026-07-29",
    "POL_SEMAS_RECHALLENGE_2026": "2026-07-29",
    "POL_SEMAS_STABILITY_VOUCHER_2026": "2026-01-28",
}
for item in POLICIES[1:]:
    VERSIONS.append({
        "policy_id": item["policy_id"], "policy_version": item["policy_version"],
        "publication_date": PUBLICATION_DATES[str(item["policy_id"])],
        "effective_from": item["effective_from"], "effective_to": item["effective_to"],
        "is_current": "yes", "change_summary": "현재 수집·검수한 공식 버전",
        "source_url": item["official_notice_url"], "source_path": item["source_path"],
    })


def resolve_source(policy_id: str, value: str) -> Path:
    if value.startswith("data/"):
        return ROOT / value
    return RAW_SELECTED / policy_id / value


def build_source_manifest() -> list[dict[str, object]]:
    url_by_policy = {item["policy_id"]: item["official_notice_url"] for item in POLICIES}
    rows: list[dict[str, object]] = []
    for policy_id, sources in SOURCE_MAP.items():
        for order, source in enumerate(sources, start=1):
            path = resolve_source(policy_id, source)
            if not path.exists():
                raise FileNotFoundError(path)
            suffix = path.suffix.lower()
            signature = path.read_bytes()[:4]
            signature_status = "valid"
            if suffix == ".pdf" and not signature.startswith(b"%PDF"):
                signature_status = "invalid"
            if suffix == ".hwpx" and not signature.startswith(b"PK"):
                signature_status = "invalid"
            rows.append({
                "policy_id": policy_id, "source_order": order, "source_role": "primary" if order == 1 else "supporting",
                "source_path": rel(path), "source_url": url_by_policy[policy_id], "file_type": suffix.lstrip("."),
                "bytes": path.stat().st_size, "sha256": sha256(path), "signature_status": signature_status,
                "retrieved_at": AS_OF, "reviewed_at": REVIEWED_AT,
            })
    return rows


def chunk_text(policy_id: str, path: Path) -> Iterable[dict[str, object]]:
    if path.suffix.lower() not in {".md", ".txt"}:
        extracted = OUT / "extracted_text" / path.parent.name / f"{path.name}.txt"
        if not extracted.exists():
            return []
        path = extracted
    text = path.read_text(encoding="utf-8", errors="replace")
    if "===== PAGE " in text:
        parts = re.split(r"(?=^===== PAGE \d+ =====$)", text, flags=re.MULTILINE)
    else:
        parts = re.split(r"(?=^#{1,3} )", text, flags=re.MULTILINE)
    chunks = []
    seq = 0
    for part in parts:
        clean = part.strip()
        if len(clean) < 20:
            continue
        seq += 1
        heading = clean.splitlines()[0][:160]
        chunks.append({
            "policy_id": policy_id, "chunk_id": f"{policy_id}::chunk::{seq:03d}",
            "source_path": rel(path), "locator": heading, "text": clean,
            "review_status": "원문전처리완료_검색인덱스미생성",
        })
    return chunks


def build_chunks(source_manifest: list[dict[str, object]]) -> list[dict[str, object]]:
    chunks: list[dict[str, object]] = []
    seen: set[tuple[str, str]] = set()
    for item in source_manifest:
        key = (str(item["policy_id"]), str(item["source_path"]))
        if key in seen:
            continue
        seen.add(key)
        chunks.extend(chunk_text(str(item["policy_id"]), ROOT / str(item["source_path"])))
    return chunks


def validate(source_manifest: list[dict[str, object]], chunks: list[dict[str, object]]) -> dict[str, object]:
    approved_ids = set(load_stage2_config()["portfolio"]["policy_ids"])
    policy_ids = {str(item["policy_id"]) for item in POLICIES}
    event_ids = {str(item["policy_id"]) for item in FINANCIAL_EVENTS}
    rule_ids = {str(item["policy_id"]) for item in ELIGIBILITY_RULES}
    source_ids = {str(item["policy_id"]) for item in source_manifest}
    chunk_ids = {str(item["policy_id"]) for item in chunks}
    example_ids = {str(item["policy_id"]) for item in ELIGIBILITY_EXAMPLES}
    checks = {
        "approved_policy_count_is_10": len(approved_ids) == 10,
        "metadata_exactly_matches_approved_ids": policy_ids == approved_ids,
        "every_policy_has_financial_event": event_ids == approved_ids,
        "every_policy_has_eligibility_rule": rule_ids == approved_ids,
        "every_policy_has_source_manifest": source_ids == approved_ids,
        "every_policy_has_text_chunk": chunk_ids == approved_ids,
        "every_policy_has_eligibility_examples": example_ids == approved_ids,
        "all_source_signatures_valid": all(row["signature_status"] == "valid" for row in source_manifest),
        "all_source_hashes_present": all(len(str(row["sha256"])) == 64 for row in source_manifest),
        "all_metadata_source_paths_exist": all((ROOT / str(row["source_path"])).exists() for row in POLICIES),
        "all_required_values_use_explicit_unknown_token": all(
            value is not None and (key == "notes" or value != "")
            for row in POLICIES + FINANCIAL_EVENTS + ELIGIBILITY_RULES
            for key, value in row.items()
        ),
        "no_unapproved_policy": policy_ids.issubset(approved_ids),
    }
    if not all(checks.values()):
        failed = [name for name, passed in checks.items() if not passed]
        raise ValueError(f"RE Stage 2 validation failed: {failed}")
    return {
        "stage": "RE Stage 2", "as_of": AS_OF, "result": "pass", "checks": checks,
        "counts": {
            "policies": len(POLICIES), "financial_events": len(FINANCIAL_EVENTS),
            "eligibility_rules": len(ELIGIBILITY_RULES), "source_files": len(source_manifest),
            "versions": len(VERSIONS), "text_chunks": len(chunks),
            "eligibility_examples": len(ELIGIBILITY_EXAMPLES),
        },
        "known_limits": [
            "예산소진형 정책의 실시간 잔여예산은 재확인 필요",
            "안전검사 지원사업은 이미지형 1쪽 PDF여서 공식 HTML을 병행 근거로 사용",
            "서울시 육성자금은 하위 자금 선택 전 단일 금융 이벤트로 계산하지 않음",
            "RAG 검색 인덱스는 RE Stage 6 전 승인 전이므로 생성하지 않음",
        ],
    }


def main() -> None:
    assert_stage2_action_allowed("structure_policy_metadata")
    assert_stage2_action_allowed("draft_eligibility_rules_from_official_text")
    assert_stage2_action_allowed("structure_financial_metadata")
    assert_stage2_action_allowed("qa_structured_policy_data")
    OUT.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)

    source_manifest = build_source_manifest()
    chunks = build_chunks(source_manifest)
    qa = validate(source_manifest, chunks)

    write_csv(OUT / "policy_metadata.csv", POLICIES)
    write_csv(OUT / "eligibility_rules.csv", ELIGIBILITY_RULES)
    write_csv(OUT / "eligibility_examples.csv", ELIGIBILITY_EXAMPLES)
    write_csv(OUT / "financial_metadata.csv", FINANCIAL_EVENTS)
    write_csv(OUT / "policy_versions.csv", VERSIONS)
    write_csv(OUT / "source_manifest.csv", source_manifest)
    with (OUT / "policy_chunks.jsonl").open("w", encoding="utf-8") as stream:
        for item in chunks:
            stream.write(json.dumps(item, ensure_ascii=False) + "\n")
    (REPORTS / "structured_qa.json").write_text(
        json.dumps(qa, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    selected_path = OUT / "selected_policies.csv"
    with selected_path.open("r", encoding="utf-8-sig", newline="") as stream:
        selected_rows = list(csv.DictReader(stream))
    for row in selected_rows:
        row["official_validation_status"] = "공식원문검증완료_RE2"
    write_csv(selected_path, selected_rows)
    selection_manifest_path = OUT / "selection_manifest.json"
    selection_manifest = json.loads(selection_manifest_path.read_text(encoding="utf-8"))
    selection_manifest["output_sha256"] = sha256(selected_path)
    selection_manifest["official_validation_status"] = "공식원문검증완료_RE2"
    selection_manifest["validated_at"] = REVIEWED_AT
    selection_manifest_path.write_text(
        json.dumps(selection_manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    artifact_manifest = {
        "generated_at": datetime.now(KST).isoformat(timespec="seconds"),
        "stage": "RE Stage 2", "portfolio": "A+C", "qa_result": qa["result"],
        "artifacts": {},
    }
    for path in sorted(OUT.glob("*")):
        if path.is_file():
            artifact_manifest["artifacts"][rel(path)] = {
                "bytes": path.stat().st_size, "sha256": sha256(path)
            }
    (OUT / "knowledge_base_manifest.json").write_text(
        json.dumps(artifact_manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"POLICIES={len(POLICIES)}")
    print(f"ELIGIBILITY_RULES={len(ELIGIBILITY_RULES)}")
    print(f"ELIGIBILITY_EXAMPLES={len(ELIGIBILITY_EXAMPLES)}")
    print(f"FINANCIAL_EVENTS={len(FINANCIAL_EVENTS)}")
    print(f"SOURCE_FILES={len(source_manifest)}")
    print(f"TEXT_CHUNKS={len(chunks)}")
    print("QA=PASS")


if __name__ == "__main__":
    main()
