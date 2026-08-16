"""Build six provisional policy portfolios from the verified pre-RE1 pool.

The script performs no fuzzy matching, candidate deletion, eligibility ruling,
or final selection. Each row is a decision-support candidate that still needs
policy-specific official-document verification after user approval.
"""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.guards.re_stage_guard import assert_action_allowed


SOURCE = ROOT / "data" / "processed_re" / "policy" / "pre_re1" / "candidate_groups.csv"
OUTPUT_DIR = ROOT / "data" / "processed_re" / "policy" / "re_stage1"
REPORT_DIR = ROOT / "reports" / "re_stage1"
OUTPUT_CSV = OUTPUT_DIR / "portfolio_candidates.csv"
MANIFEST = OUTPUT_DIR / "manifest.json"
REPORT = REPORT_DIR / "policy_portfolio_comparison.md"


PORTFOLIOS: dict[str, dict[str, Any]] = {
    "A": {
        "name": "현금흐름 비교 가능성 중심",
        "lens": "금액·지급·감면·금리·상환 이벤트로 변환할 가능성을 우선",
        "ids": [
            "GRP_986459037b76bc05", "GRP_b2fae65b4e109c08",
            "GRP_8a8a930f24156e8c", "GRP_b73a3aa814bbdc09",
            "GRP_f4cbde9fb2de5a02", "GRP_03ae6359cab4f285",
            "GRP_5c8130070c7bb48f", "GRP_edb30c540ed4b2fa",
            "GRP_3698c9fce692f966", "GRP_eebf82e34fa3bb67",
        ],
    },
    "B": {
        "name": "지원서비스 유형 다양성 중심",
        "lens": "금융·비용지원·교육·컨설팅·판로·권리구제·폐업재기를 고르게 포함",
        "ids": [
            "GRP_986459037b76bc05", "GRP_5c8130070c7bb48f",
            "GRP_c4c254c5365e8ffa", "GRP_e410a7f8e038e69b",
            "GRP_bd7393b7a437f448", "GRP_5200814c6f50beec",
            "GRP_3698c9fce692f966", "GRP_9d0d0923fec787b8",
            "GRP_5b2ba51d6c9021f8", "GRP_3925342f936f987b",
        ],
    },
    "C": {
        "name": "서울 정책 우선",
        "lens": "서울시·서울신용보증재단 및 서울 명시 공고를 우선",
        "ids": [
            "GRP_986459037b76bc05", "GRP_059661575f800512",
            "GRP_3e9edccb0ee86990", "GRP_8addc5b8a4605054",
            "GRP_9952c69b120ce343", "GRP_de6419e9b5488c04",
            "GRP_a5b04ace04a4234b", "GRP_e410a7f8e038e69b",
            "GRP_eebf82e34fa3bb67", "GRP_0be0efbab66397c6",
        ],
    },
    "A+C": {
        "name": "현금흐름 비교 + 서울 우선",
        "lens": "서울 정책을 중심으로 두고 전국 대환·재기 정책으로 금융 비교폭을 보완",
        "ids": [
            "GRP_986459037b76bc05", "GRP_059661575f800512",
            "GRP_8addc5b8a4605054", "GRP_3e9edccb0ee86990",
            "GRP_9952c69b120ce343", "GRP_0437d4b877340e15",
            "GRP_eebf82e34fa3bb67", "GRP_b2fae65b4e109c08",
            "GRP_8a8a930f24156e8c", "GRP_5c8130070c7bb48f",
        ],
    },
    "A+B": {
        "name": "현금흐름 비교 + 유형 다양성",
        "lens": "금융 이벤트를 확보하면서 디지털·컨설팅·판로·권리 지원을 함께 제시",
        "ids": [
            "GRP_986459037b76bc05", "GRP_b2fae65b4e109c08",
            "GRP_8a8a930f24156e8c", "GRP_5c8130070c7bb48f",
            "GRP_edb30c540ed4b2fa", "GRP_3698c9fce692f966",
            "GRP_c4c254c5365e8ffa", "GRP_e410a7f8e038e69b",
            "GRP_bd7393b7a437f448", "GRP_5200814c6f50beec",
        ],
    },
    "A+B+C": {
        "name": "서울 중심 종합 균형",
        "lens": "서울 실행 가능성·현금흐름 비교·지원유형 다양성을 12개 안에서 함께 확보",
        "ids": [
            "GRP_986459037b76bc05", "GRP_b2fae65b4e109c08",
            "GRP_8a8a930f24156e8c", "GRP_b73a3aa814bbdc09",
            "GRP_5c8130070c7bb48f", "GRP_059661575f800512",
            "GRP_8addc5b8a4605054", "GRP_eebf82e34fa3bb67",
            "GRP_3e9edccb0ee86990", "GRP_e410a7f8e038e69b",
            "GRP_bd7393b7a437f448", "GRP_5200814c6f50beec",
        ],
    },
}


ROLES: dict[str, tuple[str, str, str]] = {
    "GRP_986459037b76bc05": ("서울 금융·이차보전·융자", "high", "서울 금융정책의 금리·한도·상환 이벤트 후보"),
    "GRP_b2fae65b4e109c08": ("대환·채무완화", "high", "기존 고금리 부채 대체 전후를 비교할 핵심 후보"),
    "GRP_8a8a930f24156e8c": ("재기 금융", "high", "재창업·채무조정 연계 상황의 금융 이벤트 후보"),
    "GRP_b73a3aa814bbdc09": ("위기 긴급융자", "high", "일시적 매출충격 시 유동성 보완 후보"),
    "GRP_f4cbde9fb2de5a02": ("일반 운영자금", "high", "일반 경영안정 목적의 기준 융자 후보"),
    "GRP_03ae6359cab4f285": ("취약차주 금융", "high", "신용취약 소상공인 대상 금융경로 후보"),
    "GRP_5c8130070c7bb48f": ("비차입 비용지원", "high", "고정비·운영비 감소 이벤트 후보"),
    "GRP_edb30c540ed4b2fa": ("위기 선제지원", "medium", "위기진단 뒤 비차입 지원 연결 후보"),
    "GRP_3698c9fce692f966": ("폐업·정리 지원", "medium", "철거·정리·재기 비용 경감 후보"),
    "GRP_eebf82e34fa3bb67": ("서울 재기 복합지원", "high", "금융·비차입·컨설팅이 결합된 서울 복합안 후보"),
    "GRP_c4c254c5365e8ffa": ("디지털 전환", "medium", "지원금·자부담 확인 후 비용 이벤트로 변환할 후보"),
    "GRP_e410a7f8e038e69b": ("경영 컨설팅", "low", "현금효과보다 실행계획 다양성을 보완"),
    "GRP_bd7393b7a437f448": ("온라인 판로", "medium", "판로지원 금액·자부담 확인 후 비교할 후보"),
    "GRP_5200814c6f50beec": ("법률·세무·노무", "low", "무료 전문상담을 비금융 실행경로로 제시"),
    "GRP_9d0d0923fec787b8": ("폐업 후 취업", "medium", "폐업 이후 소득회복 경로를 보완"),
    "GRP_5b2ba51d6c9021f8": ("디지털 교육", "low", "역량강화 지원유형을 대표"),
    "GRP_3925342f936f987b": ("권리구제", "low", "불공정거래 피해 대응 지원유형을 대표"),
    "GRP_059661575f800512": ("서울 위기 선제지원", "medium", "2026년 서울 Track2 구체 공고 검증 후보"),
    "GRP_3e9edccb0ee86990": ("서울 디지털 전환", "medium", "2026년 하반기 서울 구체 공고 검증 후보"),
    "GRP_8addc5b8a4605054": ("서울 폐업지원", "medium", "2026년 서울 구체 폐업지원 공고 후보"),
    "GRP_9952c69b120ce343": ("서울 친환경 판로", "medium", "지원금·비용지원 여부를 확인할 서울 판로 후보"),
    "GRP_de6419e9b5488c04": ("서울 온라인 유통상담", "low", "서울 판로·상담 유형을 대표"),
    "GRP_a5b04ace04a4234b": ("서울 창업 클리닉", "low", "지역 밀착형 창업 컨설팅 후보"),
    "GRP_0be0efbab66397c6": ("서울 현장 멘토링", "low", "현장형 컨설팅 지원을 대표"),
    "GRP_0437d4b877340e15": ("서울 검사비 지원", "high", "검사비 보조를 비용감면 이벤트로 비교할 후보"),
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_groups() -> dict[str, dict[str, str]]:
    with SOURCE.open("r", encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    groups = {row["group_id"]: row for row in rows}
    if len(groups) != len(rows):
        raise ValueError("candidate_groups.csv contains duplicate group_id values")
    return groups


def is_seoul_candidate(row: dict[str, str]) -> bool:
    return (
        row["source_codes"].startswith("P04_")
        or row["canonical_title"].startswith("[서울]")
        or "서울" in row["regions"]
        or "서울" in row["agencies"]
    )


def build_rows(groups: dict[str, dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for code, portfolio in PORTFOLIOS.items():
        ids = portfolio["ids"]
        if not 8 <= len(ids) <= 12:
            raise ValueError(f"Portfolio {code} must contain 8-12 candidates")
        if len(ids) != len(set(ids)):
            raise ValueError(f"Portfolio {code} contains duplicate group IDs")
        for rank, group_id in enumerate(ids, start=1):
            if group_id not in groups:
                raise KeyError(f"Missing group ID in source pool: {group_id}")
            if group_id not in ROLES:
                raise KeyError(f"Missing role definition: {group_id}")
            source = groups[group_id]
            role, cashflow_potential, rationale = ROLES[group_id]
            rows.append(
                {
                    "portfolio_code": code,
                    "portfolio_name": portfolio["name"],
                    "rank": rank,
                    "group_id": group_id,
                    "title": source["canonical_title"],
                    "role": role,
                    "cashflow_potential": cashflow_potential,
                    "seoul_focus": "yes" if is_seoul_candidate(source) else "no",
                    "source_codes": source["source_codes"],
                    "source_record_count": source["source_record_count"],
                    "official_manual_seed": source["official_manual_seed"],
                    "rationale": rationale,
                    "selection_status": "비교후보_최종선정대기",
                    "validation_status": "정책별공식원문검증필요",
                }
            )
    return rows


def write_csv(rows: list[dict[str, Any]]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with OUTPUT_CSV.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def metrics(rows: list[dict[str, Any]], code: str) -> dict[str, int]:
    selected = [row for row in rows if row["portfolio_code"] == code]
    return {
        "count": len(selected),
        "cashflow_high": sum(row["cashflow_potential"] == "high" for row in selected),
        "cashflow_medium": sum(row["cashflow_potential"] == "medium" for row in selected),
        "cashflow_low": sum(row["cashflow_potential"] == "low" for row in selected),
        "seoul": sum(row["seoul_focus"] == "yes" for row in selected),
        "manual_seed": sum(row["official_manual_seed"] == "yes" for row in selected),
        "multi_source": sum(int(row["source_record_count"]) >= 2 for row in selected),
        "role_count": len({row["role"] for row in selected}),
    }


def write_report(rows: list[dict[str, Any]]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    lines = [
        "# RE Stage 1 정책 포트폴리오 6안 비교",
        "",
        "## 상태와 사용 제한",
        "",
        "- 입력: 사전 QA를 통과한 827개 정확 제목 후보 그룹",
        "- 출력: A·B·C·A+C·A+B·A+B+C 비교용 임시 후보",
        "- 최종 정책 포트폴리오: **미선정**",
        "- 모든 후보는 정책별 공식 공고·첨부문서로 자격·금액·기간을 다시 검증해야 한다.",
        "- 배열 순서는 단순 추천순위가 아니라 각 안에서 담당하는 비교 역할의 표시다.",
        "- 이 결과로 후보를 원본 풀에서 삭제하지 않는다.",
        "",
        "## 공통 선정 경계",
        "",
        "1. 서울 소재 소상공인이 검토 가능한 전국 또는 서울 정책을 우선한다.",
        "2. P-03·P-04 공식 Seed 또는 P-01·P-05 정확 제목 교차확인 공고를 우선한다.",
        "3. 같은 정책의 요약 Seed와 구체 공고가 중복되면 한 포트폴리오 안에서 하나만 둔다.",
        "4. 현금흐름 가능성은 제목·요약 기반 탐색값이며 금액 계산 가능성을 확정하지 않는다.",
        "5. 최종 선택은 사용자 비교 승인 후에만 수행한다.",
        "",
        "## 정량 비교",
        "",
        "| 안 | 후보 수 | 현금흐름 High | Medium | Low | 서울 후보 | 공식 수동 Seed | 복수 출처 | 역할 수 |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for code in PORTFOLIOS:
        value = metrics(rows, code)
        lines.append(
            f"| {code} | {value['count']} | {value['cashflow_high']} | "
            f"{value['cashflow_medium']} | {value['cashflow_low']} | "
            f"{value['seoul']} | {value['manual_seed']} | "
            f"{value['multi_source']} | {value['role_count']} |"
        )

    for code, portfolio in PORTFOLIOS.items():
        lines.extend(
            [
                "",
                f"## {code} — {portfolio['name']}",
                "",
                f"선정 관점: {portfolio['lens']}",
                "",
                "| 역할 | 정책 후보 | 현금흐름 가능성 | 서울 | 출처 | 검증상태 |",
                "| --- | --- | --- | --- | --- | --- |",
            ]
        )
        for row in (item for item in rows if item["portfolio_code"] == code):
            lines.append(
                f"| {row['role']} | {row['title']} | {row['cashflow_potential']} | "
                f"{row['seoul_focus']} | {row['source_codes']} | 정책별 원문 필요 |"
            )

    membership = {
        code: set(PORTFOLIOS[code]["ids"])
        for code in PORTFOLIOS
    }
    lines.extend(
        [
            "",
            "## 안별 후보 중복 수",
            "",
            "| 안 | " + " | ".join(PORTFOLIOS) + " |",
            "| --- | " + " | ".join("---:" for _ in PORTFOLIOS) + " |",
        ]
    )
    for left in PORTFOLIOS:
        overlaps = [str(len(membership[left] & membership[right])) for right in PORTFOLIOS]
        lines.append(f"| {left} | " + " | ".join(overlaps) + " |")

    frequency = Counter(group_id for ids in membership.values() for group_id in ids)
    consensus = sorted(
        (
            (count, groups_title)
            for group_id, count in frequency.items()
            if count >= 4
            for groups_title in [next(row["title"] for row in rows if row["group_id"] == group_id)]
        ),
        key=lambda item: (-item[0], item[1]),
    )
    lines.extend(["", "## 4개 이상 안에 공통으로 포함된 후보", ""])
    if consensus:
        for count, title in consensus:
            lines.append(f"- {title}: {count}개 안")
    else:
        lines.append("- 없음")

    lines.extend(
        [
            "",
            "## 최종 선택 시 확인할 질문",
            "",
            "1. 핵심 데모를 현금흐름 계산에 둘지, 지원서비스 탐색 폭에 둘지 결정한다.",
            "2. 서울 정책 비중을 최소 몇 개로 둘지 결정한다.",
            "3. 현금효과가 낮은 교육·상담 정책을 최종 8~12개 안에 몇 개 허용할지 결정한다.",
            "4. 선택한 안의 각 후보에 대해 최신 공식 원문과 신청상태를 확인한다.",
            "5. 공식 원문 검증에서 금액·시점·자격을 구조화할 수 없는 후보는 대체 후보와 함께 재승인한다.",
            "",
            "최종 포트폴리오는 이 문서 검토 후 사용자의 명시적 승인으로만 확정한다.",
            "",
        ]
    )
    REPORT.write_text("\n".join(lines), encoding="utf-8")


def write_manifest(rows: list[dict[str, Any]]) -> None:
    payload = {
        "stage": "RE Stage 1",
        "status": "comparison_complete_final_selection_pending",
        "source": SOURCE.relative_to(ROOT).as_posix(),
        "source_sha256": sha256(SOURCE),
        "source_group_count": 827,
        "portfolio_codes": list(PORTFOLIOS),
        "portfolio_row_count": len(rows),
        "unique_candidate_count": len({row["group_id"] for row in rows}),
        "selection_status_values": sorted({row["selection_status"] for row in rows}),
        "prohibited_operations_performed": [],
        "outputs": {
            OUTPUT_CSV.relative_to(ROOT).as_posix(): sha256(OUTPUT_CSV),
            REPORT.relative_to(ROOT).as_posix(): sha256(REPORT),
        },
    }
    MANIFEST.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    assert_action_allowed("build_provisional_portfolio_comparison")
    groups = load_groups()
    if len(groups) != 827:
        raise ValueError(f"Expected 827 source groups, found {len(groups)}")
    rows = build_rows(groups)
    write_csv(rows)
    write_report(rows)
    write_manifest(rows)
    print(f"PORTFOLIO_ROWS={len(rows)}")
    print(f"UNIQUE_CANDIDATES={len({row['group_id'] for row in rows})}")
    print("FINAL_SELECTION=pending_user_approval")


if __name__ == "__main__":
    main()
