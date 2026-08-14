"""Compare fixed Stage 4 Target thresholds on development periods only.

The locked 2025 test is deliberately excluded. This script produces aggregate
evidence and does not select or materialize a final Target.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

from analyze_stage4_candidates import (
    DATABASE_PATH,
    REPORT_DIR,
    count_at_threshold,
    prepare_candidate_table,
)


THRESHOLDS = (0.05, 0.08, 0.10, 0.12, 0.15, 0.18, 0.20)
TRAIN_RANGE = ("20221", "20234")
VALIDATION_RANGE = ("20241", "20244")
DEVELOPMENT_RANGE = ("20221", "20244")
VALIDATION_QUARTERS = ("20241", "20242", "20243", "20244")


def range_result(
    connection: sqlite3.Connection,
    decline_threshold: float,
    start: str,
    end: str,
) -> tuple[int, int, float]:
    return count_at_threshold(
        connection,
        -decline_threshold,
        "target_period BETWEEN ? AND ?",
        (start, end),
    )


def industry_coverage(
    connection: sqlite3.Connection,
    decline_threshold: float,
) -> tuple[int, int, int]:
    rows = connection.execute(
        """
        SELECT
            industry,
            COUNT(*) AS total,
            SUM(CASE WHEN target_yoy_growth <= ? THEN 1 ELSE 0 END) AS positive
        FROM candidate_base
        WHERE target_period BETWEEN ? AND ?
        GROUP BY industry
        """,
        (-decline_threshold, *TRAIN_RANGE),
    ).fetchall()
    both_classes = sum(0 < positive < total for _, total, positive in rows)
    balanced_minimum = sum(
        positive >= 100 and total - positive >= 100
        for _, total, positive in rows
    )
    return len(rows), both_classes, balanced_minimum


def build_sensitivity(connection: sqlite3.Connection) -> pd.DataFrame:
    rows = []
    for threshold in THRESHOLDS:
        development = range_result(connection, threshold, *DEVELOPMENT_RANGE)
        train = range_result(connection, threshold, *TRAIN_RANGE)
        validation = range_result(connection, threshold, *VALIDATION_RANGE)
        quarter_results = [
            range_result(connection, threshold, quarter, quarter)
            for quarter in VALIDATION_QUARTERS
        ]
        industries, both_classes, balanced_minimum = industry_coverage(
            connection, threshold
        )
        rows.append(
            {
                "decline_threshold": threshold,
                "target_rule": f"next-quarter YoY <= -{threshold:.0%}",
                "development_rows": development[0],
                "development_positive_rows": development[1],
                "development_positive_rate": development[2],
                "train_rows_2022_2023": train[0],
                "train_positive_rate_2022_2023": train[2],
                "validation_rows_2024": validation[0],
                "validation_positive_rate_2024": validation[2],
                "validation_minus_train_pp": (validation[2] - train[2]) * 100,
                "minimum_validation_quarter_positive_rows": min(
                    result[1] for result in quarter_results
                ),
                "minimum_validation_quarter_negative_rows": min(
                    result[0] - result[1] for result in quarter_results
                ),
                "validation_quarter_rate_min": min(
                    result[2] for result in quarter_results
                ),
                "validation_quarter_rate_max": max(
                    result[2] for result in quarter_results
                ),
                "training_industries": industries,
                "training_industries_with_both_classes": both_classes,
                "training_industries_with_at_least_100_each_class": balanced_minimum,
            }
        )
    return pd.DataFrame(rows)


def build_by_year(
    connection: sqlite3.Connection,
) -> pd.DataFrame:
    rows = []
    for year in (2022, 2023, 2024):
        for threshold in THRESHOLDS:
            total, positive, rate = count_at_threshold(
                connection,
                -threshold,
                "target_year = ?",
                (year,),
            )
            rows.append(
                {
                    "target_year": year,
                    "decline_threshold": threshold,
                    "eligible_rows": total,
                    "positive_rows": positive,
                    "positive_rate": rate,
                }
            )
    return pd.DataFrame(rows)


def write_report(frame: pd.DataFrame) -> None:
    table = []
    for row in frame.itertuples(index=False):
        table.append(
            f"| {row.decline_threshold:.0%} | {row.development_positive_rate:.2%} | "
            f"{row.train_positive_rate_2022_2023:.2%} | "
            f"{row.validation_positive_rate_2024:.2%} | "
            f"{row.validation_minus_train_pp:.2f}%p | "
            f"{row.minimum_validation_quarter_positive_rows:,} / "
            f"{row.minimum_validation_quarter_negative_rows:,} |"
        )
    lines = [
        "# Stage 4 고정 Target 임계값 민감도",
        "",
        "- 분석 범위: Target 기간 2022Q1~2024Q4 개발 데이터만 사용",
        "- 제외 범위: 잠긴 최종 테스트 2025년은 임계값 선택 분석에서 제외",
        "- 목적: 10%를 임의 확정하지 않고 5~20% 고정 기준을 비교",
        "",
        "| 감소 기준 | 개발 전체 양성률 | 2022~2023 학습 양성률 | 2024 검증 양성률 | 시기 차이 | 2024 분기별 최소 양성/음성 행 |",
        "| ---: | ---: | ---: | ---: | ---: | ---: |",
        *table,
        "",
        "## 선택 원칙",
        "",
        "1. 서비스에서 설명 가능한 고정 기준이어야 한다.",
        "2. 학습·검증의 양성과 음성이 모두 충분해야 한다.",
        "3. 특정 연도나 분기에만 양성이 몰리는 기준은 피한다.",
        "4. 최종 선택은 모델 성능이나 2025 테스트 결과를 본 뒤 바꾸지 않는다.",
        "5. 통계만으로 유일한 정답은 정해지지 않으므로 비즈니스상 '중대한 감소' 의미를 사용자가 승인한다.",
        "",
    ]
    (REPORT_DIR / "threshold_sensitivity_report.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )


def main() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DATABASE_PATH)
    try:
        eligibility = prepare_candidate_table(connection)
        sensitivity = build_sensitivity(connection)
        by_year = build_by_year(connection)
        sensitivity.to_csv(
            REPORT_DIR / "threshold_sensitivity.csv",
            index=False,
            encoding="utf-8-sig",
        )
        by_year.to_csv(
            REPORT_DIR / "threshold_sensitivity_by_year.csv",
            index=False,
            encoding="utf-8-sig",
        )
        write_report(sensitivity)
        manifest = {
            "created_at_kst": datetime.now(
                ZoneInfo("Asia/Seoul")
            ).isoformat(timespec="minutes"),
            "status": "threshold_evidence_only",
            "development_target_period": list(DEVELOPMENT_RANGE),
            "locked_test_target_period_excluded": ["20251", "20254"],
            "thresholds": list(THRESHOLDS),
            "eligible_rows_all_periods": eligibility["eligible_rows"],
            "final_threshold_selected": False,
        }
        (REPORT_DIR / "threshold_sensitivity_manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(
            json.dumps(
                {
                    "status": "completed",
                    "rows": len(sensitivity),
                    "development_period": DEVELOPMENT_RANGE,
                    "locked_test_used": False,
                },
                ensure_ascii=False,
            )
        )
    finally:
        connection.close()


if __name__ == "__main__":
    main()
