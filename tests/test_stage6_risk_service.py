from __future__ import annotations

import warnings

import pandas as pd
import pytest

from src.models.stage6_risk_service import (
    INTERNAL_SCORE,
    RiskRankingService,
    RiskServiceError,
    rank_reference_scores,
    safe_predict,
    transform_with_saved_preprocessor,
)


def test_rank_policy_uses_shared_competition_rank_for_ties() -> None:
    source = pd.DataFrame(
        {
            "서비스_업종_코드": ["A", "A", "A", "B"],
            INTERNAL_SCORE: [0.9, 0.9, 0.3, 0.5],
        }
    )
    result = rank_reference_scores(source)

    assert result["primary_priority_rank"].tolist() == [1, 1, 3, 1]
    assert result["primary_relative_risk_percentile"].round(6).tolist() == [
        66.666667,
        66.666667,
        0.0,
        0.0,
    ]
    assert result["overall_priority_rank"].tolist() == [1, 1, 4, 3]


@pytest.fixture(scope="module")
def service() -> RiskRankingService:
    return RiskRankingService()


def test_normal_input_is_deterministic_and_returns_relative_results(
    service: RiskRankingService,
) -> None:
    row = service.reference.iloc[0]
    first = service.predict(str(row["상권_코드"]), str(row["서비스_업종_코드"]))
    second = service.predict(str(row["상권_코드"]), str(row["서비스_업종_코드"]))

    assert first == second
    assert first["status"] == "ok"
    assert first["reference_quarter"] == "2025년 4분기"
    assert first["service_ranking_policy_version"] == "v1"
    assert first["model"]["operating_threshold"] is None
    assert first["primary_relative_risk"]["population_size"] > 1
    assert first["overall_relative_risk"]["population_size"] == 21333
    assert INTERNAL_SCORE not in str(first)
    assert "위험/안전" not in str(first)
    factors = first["risk_factors"]
    assert len(factors["increasing"]) + len(factors["decreasing"]) >= 3
    assert "원인·결과" in factors["causality_note"]


def test_saved_pipeline_reproduces_internal_reference_score(
    service: RiskRankingService,
) -> None:
    row = service.reference.iloc[0]
    columns = service.artifact["source_feature_columns"]
    frame = pd.DataFrame([{column: row[column] for column in columns}])
    matrix = transform_with_saved_preprocessor(frame, service.artifact["preprocessor"])
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        score = service.artifact["model"].predict_proba(matrix)[0, 1]

    assert score == pytest.approx(float(row[INTERNAL_SCORE]), abs=1e-12)


def test_known_codes_without_latest_pair_return_data_shortage(
    service: RiskRankingService,
) -> None:
    existing = set(
        zip(service.reference["상권_코드"], service.reference["서비스_업종_코드"])
    )
    missing_pair = next(
        (area, industry)
        for area in sorted(service._area_codes)
        for industry in sorted(service._industry_codes)
        if (area, industry) not in existing
    )

    result = safe_predict(*missing_pair, service=service)
    assert result["status"] == "error"
    assert result["error_code"] == "INSUFFICIENT_REFERENCE_DATA"
    assert "계산할 수 없습니다" in result["message"]


@pytest.mark.parametrize(
    ("area", "industry", "expected_code"),
    [
        ("", "", "INVALID_INPUT"),
        ("9999999", "CS100001", "UNSUPPORTED_AREA"),
        ("3001491", "CS999999", "UNSUPPORTED_INDUSTRY"),
    ],
)
def test_invalid_inputs_fail_safely(
    service: RiskRankingService,
    area: str,
    industry: str,
    expected_code: str,
) -> None:
    with pytest.raises(RiskServiceError) as caught:
        service.predict(area, industry)
    assert caught.value.code == expected_code


def test_manifest_and_reference_contract_are_consistent(
    service: RiskRankingService,
) -> None:
    manifest = service.manifest
    assert manifest["status"] == "completed"
    assert manifest["reference_rows"] == len(service.reference)
    assert manifest["duplicate_reference_keys"] == 0
    assert manifest["finite_internal_scores"] is True
    assert manifest["feature_count"] == 197
    assert manifest["global_importance_rows"] == 197
    assert manifest["raw_score_exposure"] == "internal_only"
    assert manifest["binary_operating_threshold"] is None
