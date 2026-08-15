"""Stage 6 relative-risk ranking and explanation service.

The saved LightGBM score is used only to order a versioned reference
population.  Public results deliberately omit the raw score and any binary
risk/safe label because the model does not estimate an individual store's
failure probability.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import yaml
from scipy import sparse


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config" / "stage6.yaml"
INTERNAL_SCORE = "_model_ranking_score"

IDENTIFIER_FEATURES = {
    "기준_연도",
    "기준_분기",
    "기준_년분기_코드",
    "상권_구분_코드",
    "상권_코드",
    "서비스_업종_코드",
    "공간__상권_구분_코드",
    "공간__상권_코드_명",
    "공간__자치구_코드",
    "공간__자치구_명",
    "공간__행정동_코드",
    "공간__행정동_명",
    "공간__중심_X",
    "공간__중심_Y",
}

FRIENDLY_NAMES = {
    "당월_매출_금액": "현재 분기 매출",
    "당월_매출_건수": "현재 분기 거래 건수",
    "점포_수": "현재 점포 수",
    "유사_업종_점포_수": "유사 업종 점포 수",
    "전분기_매출_증감률": "전 분기 대비 매출 변화율",
    "전년동기_매출_증감률": "전년 동기 대비 매출 변화율",
    "최근_4분기_매출_선형기울기": "최근 4분기 매출 추세",
    "최근_4분기_매출_평균": "최근 4분기 평균 매출",
    "최근_4분기_매출_변동계수": "최근 4분기 매출 변동성",
    "현재값_대비_최근_4분기_매출_평균_차이": "현재 매출과 최근 4분기 평균의 차이",
    "매출_감소_지속": "전 분기·전년 동기 매출 동반 감소 여부",
    "점포_증감률": "점포 수 변화율",
    "폐업_률": "상권·업종 폐업 점포 비율",
    "개업_율": "상권·업종 개업 점포 비율",
    "유동__총_유동인구_수": "총 유동인구",
    "상주__총_상주인구_수": "총 상주인구",
    "직장__총_직장_인구_수": "총 직장인구",
    "시설__집객시설_수": "집객시설 수",
    "변화__서울_운영_영업_개월_평균": "서울 평균 운영 영업개월",
    "변화__서울_폐업_영업_개월_평균": "서울 평균 폐업 영업개월",
    "평균_객단가": "평균 객단가",
    "점포당_매출": "점포당 매출",
    "점포당_거래건수": "점포당 거래 건수",
}


class RiskServiceError(ValueError):
    """A safe, structured Stage 6 input or data-availability error."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message

    def as_dict(self) -> dict[str, str]:
        return {"status": "error", "error_code": self.code, "message": self.message}


@dataclass(frozen=True)
class ReferencePaths:
    model: Path
    reference: Path
    area_catalog: Path
    industry_catalog: Path
    manifest: Path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_stage6_config(path: Path = DEFAULT_CONFIG_PATH) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def transform_with_saved_preprocessor(
    frame: pd.DataFrame, state: dict[str, Any]
) -> sparse.csr_matrix:
    """Apply the exact Stage 5 median/scale/one-hot transformation."""
    numeric_columns = list(state["numeric_columns"])
    categorical_columns = list(state["categorical_columns"])
    numeric = np.empty((len(frame), len(numeric_columns)), dtype=np.float32)
    for index, column in enumerate(numeric_columns):
        values = pd.to_numeric(frame[column], errors="coerce").to_numpy(
            dtype=np.float32, copy=True
        )
        values[~np.isfinite(values)] = np.nan
        values[np.isnan(values)] = float(state["numeric_medians"][column])
        values /= float(state["numeric_scales"][column])
        numeric[:, index] = values
    parts: list[sparse.spmatrix] = [sparse.csr_matrix(numeric)]
    if categorical_columns:
        categories = (
            frame[categorical_columns].astype("string").fillna("__MISSING__")
        )
        parts.append(state["categorical_encoder"].transform(categories))
    matrix = sparse.hstack(parts, format="csr").astype(np.float32)
    expected = int(state["output_feature_count"])
    if matrix.shape[1] != expected:
        raise RuntimeError(
            f"Saved preprocessor expected {expected} columns, got {matrix.shape[1]}."
        )
    return matrix


def transformed_source_columns(state: dict[str, Any]) -> list[str]:
    """Map every transformed column back to one of the 197 source features."""
    result = list(state["numeric_columns"])
    encoder = state.get("categorical_encoder")
    if encoder is not None:
        for column, categories in zip(state["categorical_columns"], encoder.categories_):
            result.extend([column] * len(categories))
    if len(result) != int(state["output_feature_count"]):
        raise RuntimeError("Transformed-to-source feature mapping is inconsistent.")
    return result


def rank_reference_scores(frame: pd.DataFrame) -> pd.DataFrame:
    """Apply policy v1 ranks; tied scores share the best occupied rank."""
    ranked = frame.copy()
    primary = ranked.groupby("서비스_업종_코드", observed=True)[INTERNAL_SCORE]
    ranked["primary_priority_rank"] = primary.rank(
        method="min", ascending=False
    ).astype("int32")
    ranked["primary_population_size"] = primary.transform("size").astype("int32")
    ranked["primary_relative_risk_percentile"] = (
        100.0
        * (ranked["primary_population_size"] - ranked["primary_priority_rank"])
        / ranked["primary_population_size"]
    )
    ranked["primary_top_share_percent"] = (
        100.0 - ranked["primary_relative_risk_percentile"]
    )

    overall_size = len(ranked)
    ranked["overall_priority_rank"] = ranked[INTERNAL_SCORE].rank(
        method="min", ascending=False
    ).astype("int32")
    ranked["overall_population_size"] = np.int32(overall_size)
    ranked["overall_relative_risk_percentile"] = (
        100.0 * (overall_size - ranked["overall_priority_rank"]) / overall_size
    )
    ranked["overall_top_share_percent"] = (
        100.0 - ranked["overall_relative_risk_percentile"]
    )
    return ranked


def friendly_feature_name(feature: str) -> str:
    if feature in FRIENDLY_NAMES:
        return FRIENDLY_NAMES[feature]
    time_count_labels = {
        "구성비__시간대_건수~06_매출_건수": "00~06시 거래 비중",
        "구성비__시간대_건수~11_매출_건수": "06~11시 거래 비중",
        "구성비__시간대_건수~14_매출_건수": "11~14시 거래 비중",
        "구성비__시간대_건수~17_매출_건수": "14~17시 거래 비중",
        "구성비__시간대_건수~21_매출_건수": "17~21시 거래 비중",
        "구성비__시간대_건수~24_매출_건수": "21~24시 거래 비중",
    }
    if feature in time_count_labels:
        return time_count_labels[feature]
    label = feature.replace("구성비__", "구성 비중: ")
    label = label.replace("유동__", "유동인구: ")
    label = label.replace("상주__", "상주인구: ")
    label = label.replace("직장__", "직장인구: ")
    label = label.replace("시설__", "시설: ")
    label = label.replace("아파트__", "아파트: ")
    label = label.replace("_", " ")
    return " ".join(label.split())


def _json_value(value: Any) -> Any:
    if pd.isna(value):
        return None
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        number = float(value)
        return round(number, 6) if math.isfinite(number) else None
    return str(value)


class RiskRankingService:
    """Read-only lookup and explanation service for one reference quarter."""

    def __init__(self, config_path: Path = DEFAULT_CONFIG_PATH) -> None:
        self.config = load_stage6_config(config_path)
        artifacts = self.config["artifacts"]
        self.paths = ReferencePaths(
            model=PROJECT_ROOT / artifacts["model"],
            reference=PROJECT_ROOT / artifacts["reference_features"],
            area_catalog=PROJECT_ROOT / artifacts["area_catalog"],
            industry_catalog=PROJECT_ROOT / artifacts["industry_catalog"],
            manifest=PROJECT_ROOT / artifacts["manifest"],
        )
        for path in self.paths.__dict__.values():
            if not path.exists():
                raise RuntimeError(f"Stage 6 artifact is missing: {path}")
        self.manifest = json.loads(self.paths.manifest.read_text(encoding="utf-8"))
        self._verify_contract()
        self.artifact = joblib.load(self.paths.model)
        self.reference = pq.read_table(self.paths.reference).to_pandas()
        self.reference["상권_코드"] = self.reference["상권_코드"].astype(str)
        self.reference["서비스_업종_코드"] = self.reference[
            "서비스_업종_코드"
        ].astype(str)
        self.area_catalog = pd.read_csv(
            self.paths.area_catalog, dtype=str, encoding="utf-8-sig"
        )
        self.industry_catalog = pd.read_csv(
            self.paths.industry_catalog, dtype=str, encoding="utf-8-sig"
        )
        self._area_codes = set(self.area_catalog["상권_코드"])
        self._industry_codes = set(self.industry_catalog["서비스_업종_코드"])
        self._source_map = transformed_source_columns(self.artifact["preprocessor"])

    def _verify_contract(self) -> None:
        policy = self.config["service_ranking_policy"]
        if policy["version"] != self.manifest["service_ranking_policy_version"]:
            raise RuntimeError("Stage 6 ranking-policy version mismatch.")
        if str(policy["reference_quarter"]) != str(self.manifest["reference_quarter"]):
            raise RuntimeError("Stage 6 reference-quarter mismatch.")
        hashes = self.manifest["sha256"]
        if sha256_file(self.paths.model) != hashes["model"]:
            raise RuntimeError("Stage 6 model hash does not match its manifest.")
        if sha256_file(self.paths.reference) != hashes["reference_features"]:
            raise RuntimeError("Stage 6 reference distribution hash mismatch.")

    def _validate_and_lookup(self, area_code: str, industry_code: str) -> pd.Series:
        area = str(area_code).strip()
        industry = str(industry_code).strip().upper()
        if not area or not industry:
            raise RiskServiceError(
                "INVALID_INPUT", "상권코드와 서비스업종코드를 모두 입력해 주세요."
            )
        if area not in self._area_codes:
            raise RiskServiceError(
                "UNSUPPORTED_AREA", f"지원하지 않는 서울 상권코드입니다: {area}"
            )
        if industry not in self._industry_codes:
            raise RiskServiceError(
                "UNSUPPORTED_INDUSTRY", f"지원하지 않는 서비스업종코드입니다: {industry}"
            )
        matched = self.reference[
            self.reference["상권_코드"].eq(area)
            & self.reference["서비스_업종_코드"].eq(industry)
        ]
        if matched.empty:
            raise RiskServiceError(
                "INSUFFICIENT_REFERENCE_DATA",
                "입력한 상권·업종 조합은 최신 기준분기의 Feature가 없어 상대 순위를 계산할 수 없습니다.",
            )
        if len(matched) != 1:
            raise RuntimeError("Reference distribution contains a duplicate key.")
        return matched.iloc[0]

    def _comparison_value(self, feature: str, industry: str) -> tuple[Any, str]:
        peers = self.reference[self.reference["서비스_업종_코드"].eq(industry)]
        series = peers[feature]
        if pd.api.types.is_numeric_dtype(series.dtype):
            return _json_value(pd.to_numeric(series, errors="coerce").median()), "같은 분기·같은 업종 서울 상권의 중앙값"
        mode = series.dropna().astype(str).mode()
        return (_json_value(mode.iloc[0]) if not mode.empty else None), "같은 분기·같은 업종 서울 상권의 최빈값"

    def _explain(self, row: pd.Series) -> dict[str, Any]:
        columns = list(self.artifact["source_feature_columns"])
        one = pd.DataFrame([{column: row[column] for column in columns}])
        matrix = transform_with_saved_preprocessor(one, self.artifact["preprocessor"])
        contribution_output = self.artifact["model"].booster_.predict(
            matrix, pred_contrib=True
        )
        if sparse.issparse(contribution_output):
            contributions = contribution_output.toarray()[0][:-1]
        else:
            contributions = np.asarray(contribution_output)[0][:-1]
        aggregated: dict[str, float] = {}
        for source, contribution in zip(self._source_map, contributions):
            aggregated[source] = aggregated.get(source, 0.0) + float(contribution)
        if self.config["explanation"].get("exclude_identifier_features", True):
            aggregated = {
                feature: value
                for feature, value in aggregated.items()
                if feature not in IDENTIFIER_FEATURES
            }
        maximum = int(self.config["explanation"]["maximum_factors_per_direction"])
        increasing = sorted(
            ((feature, value) for feature, value in aggregated.items() if value > 0),
            key=lambda pair: (-pair[1], pair[0]),
        )[:maximum]
        decreasing = sorted(
            ((feature, value) for feature, value in aggregated.items() if value < 0),
            key=lambda pair: (pair[1], pair[0]),
        )[:maximum]

        def make_factor(feature: str, direction: str) -> dict[str, Any]:
            comparison, basis = self._comparison_value(
                feature, str(row["서비스_업종_코드"])
            )
            return {
                "feature": feature,
                "label": friendly_feature_name(feature),
                "direction": direction,
                "current_value": _json_value(row[feature]),
                "comparison_value": comparison,
                "comparison_basis": basis,
            }

        return {
            "increasing": [
                make_factor(feature, "상대 순위를 높이는 방향")
                for feature, _ in increasing
            ],
            "decreasing": [
                make_factor(feature, "상대 순위를 낮추는 방향")
                for feature, _ in decreasing
            ],
            "method": "LightGBM TreeSHAP 기여방향; 식별자·좌표 Feature 제외",
            "causality_note": self.config["messages"]["causality"],
        }

    def predict(self, area_code: str, industry_code: str) -> dict[str, Any]:
        row = self._validate_and_lookup(area_code, industry_code)
        decimals = int(self.config["ranking"]["display_decimals"])

        def metric(prefix: str, label: str) -> dict[str, Any]:
            percentile = round(float(row[f"{prefix}_relative_risk_percentile"]), decimals)
            top_share = round(float(row[f"{prefix}_top_share_percent"]), decimals)
            rank = int(row[f"{prefix}_priority_rank"])
            size = int(row[f"{prefix}_population_size"])
            return {
                "relative_risk_percentile": percentile,
                "top_share_percent": top_share,
                "priority_rank": rank,
                "population_size": size,
                "comparison_group": label,
                "display": f"{label} 중 상대 위험순위 상위 {top_share:.{decimals}f}% ({rank:,}/{size:,}위)",
            }

        primary_label = "같은 분기·같은 업종의 서울 상권"
        overall_label = "같은 분기 서울 전체 상권·업종 조합"
        return {
            "status": "ok",
            "commercial_area": {
                "code": str(row["상권_코드"]),
                "name": str(row["상권_코드_명"]),
            },
            "business_type": {
                "code": str(row["서비스_업종_코드"]),
                "name": str(row["서비스_업종_코드_명"]),
            },
            "reference_quarter": self.manifest["reference_quarter_display"],
            "primary_relative_risk": metric("primary", primary_label),
            "overall_relative_risk": metric("overall", overall_label),
            "comparison_groups": [primary_label, overall_label],
            "service_ranking_policy_version": self.manifest[
                "service_ranking_policy_version"
            ],
            "model": {
                "version": self.artifact["artifact_version"],
                "target_horizon": "기준분기 이후 두 분기의 매출환경 지속 악화",
                "application_scope": "서울 상권×서비스업종 단위 상대 우선순위",
                "operating_threshold": None,
            },
            "risk_factors": self._explain(row),
            "limitations": self.config["messages"]["limitation"],
        }


def safe_predict(
    area_code: str,
    industry_code: str,
    service: RiskRankingService | None = None,
) -> dict[str, Any]:
    """Return structured expected errors without fabricating a result."""
    instance = service or RiskRankingService()
    try:
        return instance.predict(area_code, industry_code)
    except RiskServiceError as error:
        return error.as_dict()
