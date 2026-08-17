"""Read-only RE5 LightGBM scenario inference for one area-industry pair."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from src.models.re_stage5_artifact import load_re_stage5_artifact
from src.settings import PROJECT_ROOT


FEATURE_PATH = PROJECT_ROOT / "data/processed_re/re_stage8/market_features_2025q4.parquet"
ARTIFACT_DIR = PROJECT_ROOT / "artifacts/re_stage5_lightgbm_quantile"
TARGETS = {
    "thirteen_week": "target_a_next_quarter_yoy",
    "six_month": "target_b_next_two_quarters_yoy",
}
SCENARIO_INDEX = {"downside": 0, "central": 1, "recovery": 2}


@lru_cache(maxsize=1)
def _features() -> pd.DataFrame:
    if not FEATURE_PATH.is_file():
        raise FileNotFoundError(FEATURE_PATH)
    frame = pd.read_parquet(FEATURE_PATH)
    return frame.set_index(["상권_코드", "서비스_업종_코드"], drop=False)


@lru_cache(maxsize=3)
def _artifact(target: str) -> dict[str, Any]:
    path = ARTIFACT_DIR / f"{target}__lightgbm_quantile.joblib"
    return load_re_stage5_artifact(path)


def _predict_target(row: pd.DataFrame, target: str) -> list[float]:
    artifact = _artifact(target)
    columns = list(artifact["feature_columns"])
    matrix = artifact["preprocessor"].transform(row[columns])
    predictions = np.array(
        [artifact["models"][name].predict(matrix)[0] for name in ("p10", "p50", "p90")],
        dtype=float,
    )
    predictions.sort()
    return [round(float(value) * 100, 2) for value in predictions]


def predict_market_scenarios(area_code: str, industry_code: str) -> dict[str, Any]:
    frame = _features()
    key = (str(area_code), str(industry_code))
    if key not in frame.index:
        return {
            "available": False,
            "reason": "선택한 상권과 업종 조합의 최신 집계자료가 없습니다.",
            "area_code": str(area_code),
            "industry_code": str(industry_code),
        }
    row = frame.loc[[key]]
    predicted = {
        horizon: _predict_target(row, target)
        for horizon, target in TARGETS.items()
    }
    scenarios = {
        name: {
            "thirteen_week_percent": predicted["thirteen_week"][index],
            "six_month_percent": predicted["six_month"][index],
        }
        for name, index in SCENARIO_INDEX.items()
    }
    first = row.iloc[0]
    return {
        "available": True,
        "model_version": "re5-lightgbm-quantile-v1",
        "reference_period": str(first["기준_년분기_코드"]),
        "area_code": str(first["상권_코드"]),
        "area_name": str(first["상권_코드_명"]),
        "industry_code": str(first["서비스_업종_코드"]),
        "industry_name": str(first["서비스_업종_코드_명"]),
        "scenarios": scenarios,
        "meaning": "선택한 상권과 업종 전체의 전년 같은 기간 대비 매출환경 변화율",
        "limitation": "개별 점포의 실제 미래매출 예측이 아닙니다.",
    }
