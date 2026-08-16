# RE5 Feature contract v2

## 범위

- 원천: `data/processed/stage3_panel.parquet`
- 관측 단위: 기준분기 × 서울 상권코드 × 서비스 업종코드
- 후보 집합: `reports/stage5/feature_sets.json`의 `common_baseline` 197개 열
- 새 외부데이터: 없음
- 기존 LightGBM v1의 모델값·예측값·SHAP·이진 Target: 입력 금지

## 시점 규칙

- 각 행의 기준분기 현재값과 그 시점까지 만들어진 과거 파생값만 입력한다.
- 미래 매출, Target A·B·보조·QoQ Challenger, Target 유효성·결측 사유·극단 꼬리 플래그는 Feature로 사용하지 않는다.
- Fold마다 결측 대체값, 수치 Scale, 범주 One-hot 사전을 Train partition에서만 적합한다.
- Validation에 처음 나타난 범주는 unknown으로 처리한다.

## 모델별 공통 입력

- 계절 단순 Baseline은 현재 행의 `전년동기_매출_증감률`과 Train residual 분위수만 사용한다.
- 업종 Median Baseline은 Train partition의 업종별 Target 분위수와 미등록 업종용 전체 분위수만 사용한다.
- Regularized Linear, LightGBM, CatBoost, XGBoost는 동일한 197개 후보와 Train-only 전처리 행렬을 사용한다.
- Target 원값은 clipping·winsorization하지 않는다.

## 학습·평가 경계

- 2024Q1~Q4 4개 expanding-window Fold와 각 직전 1분기 Purge를 사용한다.
- 2025Q1은 2025Q2 내부 홀드아웃 직전 Purge다.
- CV 단계는 `holdout_features.parquet`과 2025Q3·Q4 결과를 읽지 않는다.
- Quantile Crossing은 원 비율을 기록한 뒤 행별 P10·P50·P90 정렬로 보정하며 보정 전·후 결과를 함께 보존한다.
- CV 결과만으로 운영모델을 자동 선택하지 않는다.
