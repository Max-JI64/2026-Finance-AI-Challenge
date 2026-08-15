"""Leakage-safe Stage 4.5 derived features.

The builder uses only columns available at the feature reference quarter.  Any
rolling feature is calculated within commercial-area and industry, in quarter
order, and is emitted only when the required quarters are consecutive.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


ENTITY = ["상권_코드", "서비스_업종_코드"]
PERIOD = "기준_년분기_코드"
SALES = "당월_매출_금액"
TRANSACTIONS = "당월_매출_건수"


@dataclass(frozen=True)
class DerivedDefinition:
    feature: str
    group: str
    formula: str
    available_at: str = "기준 분기 말"


def _period_index(series: pd.Series) -> pd.Series:
    text = series.astype("string")
    return (
        pd.to_numeric(text.str.slice(0, 4), errors="coerce") * 4
        + pd.to_numeric(text.str.slice(4, 5), errors="coerce")
        - 1
    )


def _safe_ratio(
    frame: pd.DataFrame,
    numerator: str,
    denominator: str,
    output: str,
    group: str,
    definitions: list[DerivedDefinition],
) -> None:
    denominator_values = pd.to_numeric(frame[denominator], errors="coerce")
    numerator_values = pd.to_numeric(frame[numerator], errors="coerce")
    zero_flag = f"{denominator}__분모0"
    if zero_flag not in frame:
        frame[zero_flag] = denominator_values.eq(0).astype("int8")
        definitions.append(
            DerivedDefinition(
                zero_flag,
                "denominator_flag",
                f"1 if {denominator} == 0 else 0",
            )
        )
    frame[output] = (numerator_values / denominator_values.mask(denominator_values.eq(0))).astype(
        "float32"
    )
    definitions.append(
        DerivedDefinition(output, group, f"{numerator} / {denominator}; 분모 0은 결측")
    )


def _add_share_group(
    frame: pd.DataFrame,
    columns: list[str],
    denominator: str,
    prefix: str,
    group: str,
    definitions: list[DerivedDefinition],
) -> None:
    for column in columns:
        label = column.replace(prefix, "", 1)
        _safe_ratio(
            frame,
            column,
            denominator,
            f"구성비__{label}",
            group,
            definitions,
        )


def _add_rolling_sales(
    frame: pd.DataFrame, definitions: list[DerivedDefinition]
) -> None:
    original_order = frame.index
    work = frame.assign(_원래순서=np.arange(len(frame)), _분기인덱스=_period_index(frame[PERIOD]))
    work = work.sort_values([*ENTITY, "_분기인덱스", "_원래순서"], kind="stable")
    grouped_sales = work.groupby(ENTITY, observed=True, sort=False)[SALES]
    grouped_period = work.groupby(ENTITY, observed=True, sort=False)["_분기인덱스"]

    for window in (2, 4):
        rolling = grouped_sales.rolling(window, min_periods=window)
        period_rolling = grouped_period.rolling(window, min_periods=window)
        count = rolling.count().reset_index(level=ENTITY, drop=True)
        period_span = (
            period_rolling.max().reset_index(level=ENTITY, drop=True)
            - period_rolling.min().reset_index(level=ENTITY, drop=True)
        )
        valid = count.eq(window) & period_span.eq(window - 1)
        values = {
            "평균": rolling.mean().reset_index(level=ENTITY, drop=True),
            "표준편차": rolling.std(ddof=0).reset_index(level=ENTITY, drop=True),
            "최소": rolling.min().reset_index(level=ENTITY, drop=True),
            "최대": rolling.max().reset_index(level=ENTITY, drop=True),
        }
        for statistic, series in values.items():
            name = f"최근_{window}분기_매출_{statistic}"
            work[name] = series.where(valid).astype("float32")
            definitions.append(
                DerivedDefinition(
                    name,
                    "rolling_sales",
                    f"현재 포함 최근 {window}개 연속 분기 {SALES}의 {statistic}",
                )
            )
        mean_name = f"최근_{window}분기_매출_평균"
        std_name = f"최근_{window}분기_매출_표준편차"
        cv_name = f"최근_{window}분기_매출_변동계수"
        diff_name = f"현재값_대비_최근_{window}분기_매출_평균_차이"
        work[cv_name] = (
            work[std_name] / work[mean_name].mask(work[mean_name].eq(0))
        ).astype("float32")
        work[diff_name] = (work[SALES] - work[mean_name]).astype("float32")
        definitions.extend(
            [
                DerivedDefinition(
                    cv_name,
                    "rolling_sales",
                    f"{std_name} / {mean_name}; 분모 0은 결측",
                ),
                DerivedDefinition(
                    diff_name,
                    "rolling_sales",
                    f"{SALES} - {mean_name}",
                ),
            ]
        )

    new_columns = [definition.feature for definition in definitions if definition.feature in work]
    restored = work.sort_values("_원래순서", kind="stable")
    for column in new_columns:
        if column not in frame:
            frame[column] = restored[column].to_numpy()
    frame.index = original_order


def build_stage45_features(
    source: pd.DataFrame,
) -> tuple[pd.DataFrame, list[DerivedDefinition]]:
    """Return a copy with candidate features and their auditable definitions."""
    frame = source.copy(deep=False)
    definitions: list[DerivedDefinition] = []

    _safe_ratio(frame, SALES, TRANSACTIONS, "평균_객단가", "unit_economics", definitions)
    _safe_ratio(frame, SALES, "점포_수", "점포당_매출", "unit_economics", definitions)
    _safe_ratio(
        frame, TRANSACTIONS, "점포_수", "점포당_거래건수", "unit_economics", definitions
    )
    _safe_ratio(
        frame, "개업_점포_수", "유사_업종_점포_수", "개업_강도", "store_dynamics", definitions
    )
    _safe_ratio(
        frame, "폐업_점포_수", "유사_업종_점포_수", "폐업_강도", "store_dynamics", definitions
    )

    amount_groups = [
        # 주말 비중은 Stage 3의 `주말_매출_비중`을 재사용한다.
        ["주중_매출_금액"],
        [f"{day}_매출_금액" for day in "월요일 화요일 수요일 목요일 금요일 토요일 일요일".split()],
        [f"시간대_{slot}_매출_금액" for slot in ["00~06", "06~11", "11~14", "14~17", "17~21", "21~24"]],
        ["남성_매출_금액", "여성_매출_금액"],
        [f"연령대_{age}_매출_금액" for age in ["10", "20", "30", "40", "50", "60_이상"]],
    ]
    count_groups = [
        ["주중_매출_건수", "주말_매출_건수"],
        [f"{day}_매출_건수" for day in "월요일 화요일 수요일 목요일 금요일 토요일 일요일".split()],
        [f"시간대_건수~{slot}_매출_건수" for slot in ["06", "11", "14", "17", "21", "24"]],
        ["남성_매출_건수", "여성_매출_건수"],
        [f"연령대_{age}_매출_건수" for age in ["10", "20", "30", "40", "50", "60_이상"]],
    ]
    for columns in amount_groups:
        _add_share_group(frame, columns, SALES, "", "sales_composition", definitions)
    for columns in count_groups:
        _add_share_group(frame, columns, TRANSACTIONS, "", "transaction_composition", definitions)

    population_groups = {
        "유동": [
            ["유동__남성_유동인구_수", "유동__여성_유동인구_수"],
            [f"유동__연령대_{age}_유동인구_수" for age in ["10", "20", "30", "40", "50", "60_이상"]],
            [f"유동__시간대_{slot}_유동인구_수" for slot in ["00_06", "06_11", "11_14", "14_17", "17_21", "21_24"]],
            [f"유동__{day}_유동인구_수" for day in "월요일 화요일 수요일 목요일 금요일 토요일 일요일".split()],
        ],
        "상주": [
            ["상주__남성_상주인구_수", "상주__여성_상주인구_수"],
            [f"상주__연령대_{age}_상주인구_수" for age in ["10", "20", "30", "40", "50", "60_이상"]],
        ],
        "직장": [
            ["직장__남성_직장_인구_수", "직장__여성_직장_인구_수"],
            [f"직장__연령대_{age}_직장_인구_수" for age in ["10", "20", "30", "40", "50", "60_이상"]],
        ],
    }
    totals = {
        "유동": "유동__총_유동인구_수",
        "상주": "상주__총_상주인구_수",
        "직장": "직장__총_직장_인구_수",
    }
    for population_type, groups in population_groups.items():
        for columns in groups:
            _add_share_group(
                frame,
                columns,
                totals[population_type],
                "",
                f"{population_type}_population_composition",
                definitions,
            )

    for numerator, denominator, name in [
        (totals["유동"], totals["상주"], "유동인구_대비_상주인구_비율"),
        (totals["유동"], totals["직장"], "유동인구_대비_직장인구_비율"),
        (totals["상주"], totals["직장"], "상주인구_대비_직장인구_비율"),
    ]:
        _safe_ratio(frame, numerator, denominator, name, "population_ratio", definitions)

    for label, total in totals.items():
        _safe_ratio(frame, total, "점포_수", f"점포당_{label}인구", "population_per_store", definitions)
        _safe_ratio(frame, total, "공간__면적", f"면적당_{label}인구", "density", definitions)
    for numerator, name in [
        ("시설__집객시설_수", "면적당_집객시설"),
        ("아파트__아파트_단지_수", "면적당_아파트단지"),
        ("상주__총_가구_수", "면적당_가구"),
    ]:
        _safe_ratio(frame, numerator, "공간__면적", name, "density", definitions)
        _safe_ratio(frame, numerator, "점포_수", name.replace("면적당", "점포당"), "density", definitions)

    qoq = pd.to_numeric(frame["전분기_매출_증감률"], errors="coerce")
    yoy = pd.to_numeric(frame["전년동기_매출_증감률"], errors="coerce")
    valid_growth = qoq.notna() & yoy.notna()
    frame["매출_변화방향_일치"] = np.where(valid_growth, np.sign(qoq).eq(np.sign(yoy)), np.nan).astype("float32")
    frame["매출_감소_지속"] = np.where(valid_growth, qoq.lt(0) & yoy.lt(0), np.nan).astype("float32")
    definitions.extend(
        [
            DerivedDefinition(
                "매출_변화방향_일치", "persistence", "sign(전분기_매출_증감률) == sign(전년동기_매출_증감률)"
            ),
            DerivedDefinition(
                "매출_감소_지속", "persistence", "전분기_매출_증감률 < 0 and 전년동기_매출_증감률 < 0"
            ),
        ]
    )

    _add_rolling_sales(frame, definitions)

    log_sources = [
        SALES,
        TRANSACTIONS,
        "점포_수",
        totals["유동"],
        totals["상주"],
        totals["직장"],
        "시설__집객시설_수",
        "아파트__아파트_단지_수",
        "상주__총_가구_수",
        "아파트__아파트_평균_시가",
    ]
    for column in log_sources:
        values = pd.to_numeric(frame[column], errors="coerce")
        name = f"log1p__{column}"
        frame[name] = np.log1p(values.where(values.ge(0))).astype("float32")
        definitions.append(
            DerivedDefinition(name, "log_transform", f"log(1 + {column}); 음수는 결측")
        )

    return frame, definitions


def definitions_frame(definitions: list[DerivedDefinition]) -> pd.DataFrame:
    return pd.DataFrame([definition.__dict__ for definition in definitions]).drop_duplicates(
        "feature", keep="first"
    )
