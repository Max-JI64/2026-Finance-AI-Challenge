# RE5 Quantile 시간순 CV 완료 검증

- 검증 시각: 2026-08-16 20:21 KST
- 검증 범위: 사용자가 완료한 72개 CV Task의 산출물 무결성·개발검증 지표·Holdout 잠금 상태
- 검증 중 추가 모델 학습: 없음
- 2025Q2 내부 Holdout Target 접근: 없음

## 1. 완료·무결성 Gate

| 항목 | 결과 |
| --- | --- |
| 진행 상태 | `72/72`, `cv_completed_waiting_for_user_model_approval` |
| Checkpoint JSON | 72개 |
| 예측 Parquet | 72개 |
| Target×Fold×Model 고유 조합 | 72개, 누락 0·중복 0·초과 0 |
| 계약 SHA-256 | 72개 모두 `ee0c67038c6e34a5325e18546e9d16fbef55cbfcd44801dd900ca53f70d42674` |
| 예측 파일 SHA-256 | Checkpoint 기록과 72개 모두 일치 |
| 예측 행 수 | 72개 모두 Checkpoint 기록과 일치 |
| 행 ID 중복 | 0건 |
| Actual·P10·P50·P90 비유한 값 | 0건 |
| 보정 후 P10≤P50≤P90 위반 | 0건 |
| 완료 후 로그 실패 표식 | 0건 |
| Holdout 잠금 | Progress와 72개 Checkpoint 모두 `holdout_target_opened=false` |

모델 6종, Target 3종, 2024Q1~Q4 Fold 4개의 전체 조합이 정확히 한 번씩 완료됐다. 각 모델 때문에 반복되는 Validation 행을 합산하면 1,452,366행이며, 이는 고유 관측 수가 아니라 72개 Task의 검증 행 수 합계다.

## 2. Tree 후보 비교

| Target | 모델 | 평균 MAE | 최악 Fold MAE | Coverage | 평균 구간 폭 | Interval Score | Spearman | 방향 일치율 | 총 Fit 시간(초) |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| A: 다음 1분기 YoY | XGBoost | 0.7463 | 1.0908 | 0.7689 | 2.9748 | 6.0975 | 0.6225 | 0.7381 | 1,512.1 |
| A: 다음 1분기 YoY | LightGBM | 0.7501 | 1.0941 | 0.7778 | 1.3508 | 4.9546 | 0.6184 | 0.7365 | 186.9 |
| A: 다음 1분기 YoY | CatBoost | 0.7701 | 1.1434 | 0.8121 | 1.2655 | 5.7658 | 0.5946 | 0.7314 | 732.7 |
| B: 다음 2분기 합산 YoY | XGBoost | 0.3434 | 0.4223 | 0.7652 | 0.8483 | 2.2087 | 0.5848 | 0.7263 | 1,434.7 |
| B: 다음 2분기 합산 YoY | LightGBM | 0.3440 | 0.4213 | 0.7797 | 0.7629 | 2.1335 | 0.5816 | 0.7241 | 170.0 |
| B: 다음 2분기 합산 YoY | CatBoost | 0.3502 | 0.4283 | 0.7911 | 0.7980 | 2.2091 | 0.5700 | 0.7230 | 693.1 |
| 보조: 향후 2분기 최저 YoY | XGBoost | 0.2809 | 0.3567 | 0.7711 | 0.6641 | 1.6918 | 0.5959 | 0.7787 | 1,389.0 |
| 보조: 향후 2분기 최저 YoY | LightGBM | 0.2816 | 0.3571 | 0.7813 | 0.6235 | 1.6842 | 0.5925 | 0.7782 | 162.3 |
| 보조: 향후 2분기 최저 YoY | CatBoost | 0.2856 | 0.3619 | 0.7948 | 0.6451 | 1.7483 | 0.5823 | 0.7752 | 661.1 |

LightGBM은 업종 Median Baseline보다 평균 MAE가 Target A `13.57%`, Target B `19.93%`, 보조 Target `18.40%` 낮았고, 세 Target 모두 4개 Fold 전부에서 계절 Baseline과 업종 Median Baseline을 이겼다.

XGBoost의 평균 MAE는 LightGBM보다 Target A `0.51%`, Target B `0.17%`, 보조 Target `0.26%` 낮다. 반면 LightGBM은 세 Target 모두 XGBoost보다 Interval Score가 낮고, 특히 Target A의 평균 구간 폭이 `1.3508`로 XGBoost `2.9748`의 절반 미만이다. 세 Target 총 Fit 시간도 LightGBM 약 `519초`, XGBoost 약 `4,336초`로 LightGBM이 약 8.4배 빠르다. CatBoost는 Coverage가 목표 0.8에 가장 가깝지만 MAE·Interval Score·시간의 종합 우위는 없다.

Regularized Linear는 평균 MAE가 `63.18~108.89`, Raw Quantile Crossing이 Target에 따라 `50~100%`여서 현재 구현·Feature 조합에서는 후보로 채택할 수 없는 붕괴 상태다.

## 3. 극단값·업종 안정성 주의사항

- Target A의 2024Q1 `CS300009` 267행은 LightGBM MAE `28.2439`, Median AE `0.1301`, Mean Error `-28.0031`이다. 세 Tree 모델이 같은 업종·Fold에서 거의 같은 큰 MAE를 보여 특정 모델만의 붕괴라기보다 보존된 극단 Target의 영향으로 해석해야 한다.
- Target B와 보조 Target의 최악 업종은 2024Q1 `CS300032` 43행이며 LightGBM MAE는 각각 `4.9463`, `4.0916`이다. 표본이 작고 세 Tree 모델 결과가 유사하다.
- 승인 계약에 따라 Target Clipping·Winsorization을 하지 않았으므로 위 결과를 제거하거나 보정하지 않았다. 따라서 `주요 업종 붕괴 없음`과 현금흐름 민감도 Gate는 아직 통과로 표시하지 않는다.

## 4. 권장안과 승인 대기

현재 개발 CV만 놓고 보면 **LightGBM Quantile을 RE5의 내부 Holdout 평가 후보로 승인**하는 안을 권장한다. XGBoost의 MAE 이득은 0.17~0.51%로 작고, LightGBM은 구간 품질과 처리시간의 균형이 더 좋다.

사용자 후속 결정에 따라 두 모델을 동시에 서비스하지 않는다. 운영 지위는 다음과 같이 확정했다.

1. 기존 Stage 6 LightGBM v1: 재학습·서비스 사용 없이 `archived evidence`로만 보존
2. RE5 LightGBM Quantile: 독립검증 한계를 표시한 단일 ML 서비스 후보
3. 모델 장애·미완성 시 Fallback: 기존 위험순위가 아니라 사용자 직접 매출충격률
4. 사용자 실행 요청 후에만 2025Q2 기준 내부 Holdout 1회 평가
5. Holdout 결과를 본 뒤 모델 재선택하지 않음

현재 RE5 Gate는 완료가 아니다. LightGBM 후보와 기존 Stage 6 서비스 제외는 승인됐지만, 내부 Holdout·신규 데이터 Ablation·서비스 민감도·새 독립 감사가 아직 미완료다.
