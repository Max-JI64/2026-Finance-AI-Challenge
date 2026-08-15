# Stage 5 Optuna 다목적 튜닝 결과

- 생성 시각: 2026-08-15T17:23+09:00
- 범위: 사용자 승인 후보 3개, 후보별 20회, Trial마다 고정 4개 시간순 Fold
- 목적함수: 평균 AUPRC와 평균 AUROC 동시 최대화(단일 가중합 없음)
- 안정성·확률 품질: 최악 Fold, Fold 표준편차, Brier Score, Log Loss를 함께 공개
- 2025 잠긴 테스트: 접근하지 않음
- 이 보고서는 Pareto 결과를 공개하며 최종 모델이나 대표 Trial을 자동 확정하지 않음

## 후보별 완료 상태

| 모델 | Feature-set | 무튜닝 AP | 무튜닝 AUC | 완료 Trial | Pareto Trial |
| --- | --- | ---: | ---: | ---: | ---: |
| lightgbm | `common_baseline` | 0.6344 | 0.8059 | 20 / 20 | 1 |
| xgboost | `tree_plus_transaction_count_raw_components` | 0.6333 | 0.8064 | 20 / 20 | 1 |
| catboost | `tree_plus_worker_population_raw_components` | 0.5913 | 0.7831 | 20 / 20 | 1 |

## Pareto Trial 전체

어느 한 지표를 높이려면 다른 지표가 낮아지는 비지배 해만 표시한다. 아래 표의 수치와 전체 CSV를 함께 보고 대표 설정을 결정한다.

| 모델 | Trial | 평균 AP | 평균 AUC | 최악 Fold AP | AP 표준편차 | Brier | Log Loss | Fit 초 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| catboost | 18 | 0.6364 | 0.8057 | 0.6012 | 0.0245 | 0.1577 | 0.4789 | 108.8 |
| lightgbm | 10 | 0.6436 | 0.8104 | 0.6120 | 0.0237 | 0.1565 | 0.4749 | 99.6 |
| xgboost | 16 | 0.6421 | 0.8100 | 0.6116 | 0.0232 | 0.1568 | 0.4758 | 196.3 |

## 무튜닝 대비 변화와 종합 검토

| 모델 | Pareto Trial | AP 변화 | AUC 변화 | 최악 Fold AP 변화 | Brier 변화 | 종합 검토 |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| LightGBM | 10 | +0.0092 | +0.0045 | +0.0099 | -0.0015 | 평균·최악 Fold·확률 품질이 함께 개선된 모델 내부 권장안 |
| XGBoost | 16 | +0.0087 | +0.0035 | +0.0114 | -0.0011 | 평균·최악 Fold·확률 품질이 함께 개선된 모델 내부 권장안 |
| CatBoost | 18 | +0.0451 | +0.0226 | +0.0338 | -0.0095 | 평균 성능과 확률 품질 우선 권장안이나 Trial 16과 안정성 Trade-off 존재 |

- LightGBM Trial 2는 Trial 10보다 AP 표준편차와 시간이 작지만 평균 AP·AUC, 최악 Fold AP, Brier, Log Loss가 모두 불리하다.
- XGBoost Trial 11도 Trial 16보다 AP 표준편차와 시간은 작지만 평균·최악 Fold 성능과 확률 품질이 불리하다.
- CatBoost Trial 16은 평균 AP `0.6350`, 평균 AUC `0.8041`로 Trial 18보다 낮지만 최악 Fold AP `0.6026`, AP 표준편차 `0.0241`, Fit `90.8초`로 더 낫다. 평균 성능 우선이면 Trial 18, 최악 Fold·시간 우선이면 Trial 16이므로 대표 설정은 사용자 종합 승인 후 확정한다.
- Pareto Trial은 각 모델 내부의 20개 Trial 중 평균 AP와 평균 AUC에 대해 비지배인 설정이다. 모델 간 최종 순위나 최종 모델을 뜻하지 않는다.

## 하이퍼파라미터 확인 방법

- 모든 Trial의 파라미터와 Fold별 지표: `optuna_trials.csv`
- Pareto Trial만 모은 표: `optuna_pareto_trials.csv`
- 중단 후 재개 가능한 원본 Study: `optuna_studies.db`
- 다음 단계: 사용자와 모델별 대표 Trial을 종합 선택한 뒤 동일 OOF 예측으로 개별 모델, Soft Voting, Stacking을 비교
