import pandas as pd

from src.features.build_stage45_features import _add_rolling_sales


def test_rolling_features_do_not_change_when_future_sales_changes() -> None:
    base = pd.DataFrame(
        {
            "상권_코드": ["A"] * 5,
            "서비스_업종_코드": ["S"] * 5,
            "기준_년분기_코드": ["20211", "20212", "20213", "20214", "20221"],
            "당월_매출_금액": [10.0, 20.0, 30.0, 40.0, 50.0],
        }
    )
    changed = base.copy()
    changed.loc[4, "당월_매출_금액"] = 5000.0
    first_definitions = []
    second_definitions = []
    _add_rolling_sales(base, first_definitions)
    _add_rolling_sales(changed, second_definitions)

    rolling_columns = [definition.feature for definition in first_definitions]
    pd.testing.assert_frame_equal(
        base.loc[:3, rolling_columns],
        changed.loc[:3, rolling_columns],
    )


def test_rolling_features_require_consecutive_quarters() -> None:
    frame = pd.DataFrame(
        {
            "상권_코드": ["A"] * 4,
            "서비스_업종_코드": ["S"] * 4,
            "기준_년분기_코드": ["20211", "20212", "20214", "20221"],
            "당월_매출_금액": [10.0, 20.0, 40.0, 50.0],
        }
    )
    definitions = []
    _add_rolling_sales(frame, definitions)

    assert pd.isna(frame.loc[2, "최근_2분기_매출_평균"])
    assert frame.loc[3, "최근_2분기_매출_평균"] == 45.0
    assert frame["최근_4분기_매출_평균"].isna().all()
