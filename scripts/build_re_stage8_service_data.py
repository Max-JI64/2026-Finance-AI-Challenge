"""Build local RE8.1 map points and latest market-scenario feature rows.

The downloaded Shapefile remains untouched. Only the official center
coordinates, administrative labels and area size are exported for the web
map. Polygon geometry is deliberately not published to the browser.
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path

import geopandas as gpd
import pandas as pd
from pyproj import Transformer


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.models.re_stage5_artifact import load_re_stage5_artifact


SOURCE_DIR = PROJECT_ROOT / "data/raw/서울시 상권분석서비스(영역-상권)"
SOURCE_SHP = SOURCE_DIR / "서울시 상권분석서비스(영역-상권).shp"
AREA_CATALOG = PROJECT_ROOT / "reports/stage6/area_catalog.csv"
PANEL_PATH = PROJECT_ROOT / "data/processed_re/model/re_stage5/panel_v2.parquet"
TARGET_A_ARTIFACT = (
    PROJECT_ROOT
    / "artifacts/re_stage5_lightgbm_quantile/target_a_next_quarter_yoy__lightgbm_quantile.joblib"
)
OUTPUT_DIR = PROJECT_ROOT / "data/processed_re/re_stage8"
MAP_PATH = OUTPUT_DIR / "commercial_area_points.json"
FEATURE_PATH = OUTPUT_DIR / "market_features_2025q4.parquet"
MANIFEST_PATH = OUTPUT_DIR / "service_data_manifest.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_map_points() -> dict[str, object]:
    source = gpd.read_file(SOURCE_SHP, encoding="utf-8")
    if source.crs is None or source.crs.to_epsg() != 5181:
        raise RuntimeError(f"Unexpected commercial-area CRS: {source.crs}")
    catalog = pd.read_csv(AREA_CATALOG, dtype=str, encoding="utf-8-sig")
    current_codes = set(catalog["상권_코드"])
    source["TRDAR_CD"] = source["TRDAR_CD"].astype(str)
    current = source[source["TRDAR_CD"].isin(current_codes)].copy()
    missing = sorted(current_codes.difference(current["TRDAR_CD"]))
    if missing:
        raise RuntimeError(f"Commercial-area map is missing {len(missing)} service codes")
    if current["TRDAR_CD"].duplicated().any():
        raise RuntimeError("Commercial-area map contains duplicate codes")

    transformer = Transformer.from_crs(5181, 4326, always_xy=True)
    longitudes, latitudes = transformer.transform(
        current["XCNTS_VALU"].astype(float).to_numpy(),
        current["YDNTS_VALU"].astype(float).to_numpy(),
    )
    current["longitude"] = longitudes
    current["latitude"] = latitudes
    current["area_m2"] = current["RELM_AR"].astype(float)
    current["radius_m"] = current["area_m2"].map(
        lambda value: math.sqrt(max(value, 1.0) / math.pi)
    )
    current = current.sort_values(
        ["SIGNGU_CD_", "ADSTRD_CD_", "TRDAR_CD_N", "TRDAR_CD"], kind="stable"
    )
    items = [
        {
            "code": row.TRDAR_CD,
            "name": row.TRDAR_CD_N,
            "category": row.TRDAR_SE_1,
            "district_code": str(row.SIGNGU_CD),
            "district": row.SIGNGU_CD_,
            "administrative_dong_code": str(row.ADSTRD_CD),
            "administrative_dong": row.ADSTRD_CD_,
            "latitude": round(float(row.latitude), 7),
            "longitude": round(float(row.longitude), 7),
            "area_m2": round(float(row.area_m2), 1),
            "radius_m": round(float(row.radius_m), 1),
        }
        for row in current.itertuples(index=False)
    ]
    MAP_PATH.write_text(
        json.dumps({"crs": "EPSG:4326", "items": items}, ensure_ascii=False, separators=(",", ":"))
        + "\n",
        encoding="utf-8",
    )
    return {
        "source_rows": int(len(source)),
        "service_rows": len(items),
        "excluded_historical_rows": int(len(source) - len(items)),
        "districts": int(current["SIGNGU_CD_"].nunique()),
        "administrative_dongs": int(current["ADSTRD_CD_"].nunique()),
        "minimum_area_m2": float(current["area_m2"].min()),
        "maximum_area_m2": float(current["area_m2"].max()),
    }


def build_market_features() -> dict[str, object]:
    artifact = load_re_stage5_artifact(TARGET_A_ARTIFACT)
    feature_columns = list(artifact["feature_columns"])
    keys = ["기준_년분기_코드", "상권_코드", "상권_코드_명", "서비스_업종_코드", "서비스_업종_코드_명"]
    requested_columns = list(dict.fromkeys([*keys, *feature_columns]))
    panel = pd.read_parquet(PANEL_PATH, columns=requested_columns)
    panel["기준_년분기_코드"] = panel["기준_년분기_코드"].astype(str)
    latest_period = max(panel["기준_년분기_코드"])
    latest = panel.loc[panel["기준_년분기_코드"] == latest_period].copy()
    if latest.duplicated(["상권_코드", "서비스_업종_코드"]).any():
        raise RuntimeError("Latest market features contain duplicate area-industry keys")
    latest.to_parquet(FEATURE_PATH, index=False)
    return {
        "reference_period": latest_period,
        "rows": int(len(latest)),
        "feature_count": len(feature_columns),
        "area_count": int(latest["상권_코드"].nunique()),
        "industry_count": int(latest["서비스_업종_코드"].nunique()),
    }


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    map_summary = build_map_points()
    market_summary = build_market_features()
    manifest = {
        "version": "re8-service-data-v2",
        "map": map_summary,
        "market_features": market_summary,
        "sources": {
            str(SOURCE_SHP.relative_to(PROJECT_ROOT)).replace("\\", "/"): sha256(SOURCE_SHP),
            str(AREA_CATALOG.relative_to(PROJECT_ROOT)).replace("\\", "/"): sha256(AREA_CATALOG),
            str(PANEL_PATH.relative_to(PROJECT_ROOT)).replace("\\", "/"): sha256(PANEL_PATH),
            str(TARGET_A_ARTIFACT.relative_to(PROJECT_ROOT)).replace("\\", "/"): sha256(TARGET_A_ARTIFACT),
        },
        "outputs": {
            str(MAP_PATH.relative_to(PROJECT_ROOT)).replace("\\", "/"): sha256(MAP_PATH),
            str(FEATURE_PATH.relative_to(PROJECT_ROOT)).replace("\\", "/"): sha256(FEATURE_PATH),
        },
    }
    MANIFEST_PATH.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({"map": map_summary, "market": market_summary}, ensure_ascii=False))


if __name__ == "__main__":
    main()
