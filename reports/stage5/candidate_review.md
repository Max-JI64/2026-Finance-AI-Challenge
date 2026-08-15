# Stage 5 상위 3개 후보 종합 검토안

> 상태: 사용자 승인 및 Optuna 튜닝 완료. 이 문서는 자동 순위 결과가 아니라 34개 변형의 전체 지표, 시간 Fold 안정성, 확률 품질, 복잡도와 모델 다양성을 함께 본 후보 선정 근거다.

## 비교 완료 사실

- 34개 모델·Feature-set 변형 × 4개 시간순 Fold = 136개 실행을 모두 완료했다.
- 실패는 0개이며 전처리는 각 Fold Train에만 Fit했다.
- 동일한 개발 행·Target·Fold를 사용했고 Feature-set별로 열 조합만 달랐다.
- 2025 잠긴 테스트는 열지 않았고 자동 순위·Feature 유지·탈락도 수행하지 않았다.

## 권장 상위 3개

| 권장 후보 | 평균 AUPRC | 평균 AUROC | 최악 Fold AUPRC | AUPRC 표준편차 | 평균 Brier | 총 학습초 | 종합 판단 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| LightGBM + `common_baseline` | 0.6344 | 0.8059 | 0.6021 | 0.0245 | 0.1580 | 43.3 | 전체 평균 AUPRC 최고, 빠른 학습, 원시 세부열 없이도 강함 |
| XGBoost + `tree_plus_transaction_count_raw_components` | 0.6333 | 0.8064 | 0.6002 | 0.0248 | 0.1579 | 66.3 | 전체 평균 AUROC 최고, 확률 품질도 최상위권 |
| CatBoost + `tree_plus_worker_population_raw_components` | 0.5913 | 0.7831 | 0.5674 | 0.0165 | 0.1673 | 252.8 | 상위 두 모델보다 평균 성능은 낮지만 Fold 안정성과 모델 다양성이 좋고 CatBoost 공통 기준선보다 전반적으로 개선 |

## Feature-set 판단 근거

- LightGBM은 공통 기준선이 평균 AUPRC 최고였다. 원시 변수군 추가형의 AUROC 차이는 매우 작고 평균 AUPRC는 같거나 낮아, 단순한 공통 기준선을 우선 권장한다.
- XGBoost 거래건수 추가형은 공통 기준선보다 평균 AUPRC `+0.0007`, 평균 AUROC `+0.0003`이고 Brier Score도 소폭 낮았다. 차이는 작지만 공동 핵심 지표와 확률 품질이 같은 방향이라 튜닝 후보로 권장한다.
- CatBoost 직장인구 추가형은 공통 기준선보다 평균 AUPRC `+0.0029`, 평균 AUROC `+0.0013`, 최악 Fold AUPRC `+0.0040`이며 AUPRC 표준편차도 감소했다. 세 번째 후보에서는 평균 성능뿐 아니라 시간 안정성과 모델군 다양성을 함께 고려했다.

## 선택하지 않은 주요 대안

- XGBoost 공통 기준선은 더 단순하면서 성능이 거의 같아, 복잡도 최소화를 우선하면 거래건수 추가형 대신 선택할 수 있다.
- CatBoost 유동인구 추가형은 CatBoost 내 평균 AUPRC·AUROC·Brier가 가장 좋지만, 직장인구 추가형보다 최악 Fold AUPRC와 표준편차가 불리하다.
- Random Forest 매출금액 추가형은 평균 AUPRC `0.5930`이지만 AUROC·확률 품질·Recall@0.5·학습시간에서 CatBoost 권장안보다 불리하다.
- Extra Trees 거래건수 추가형은 자체 기준선 대비 개선됐지만 절대 성능이 상위 부스팅 모델과 큰 차이가 난다.
- L2 Logistic은 설명 가능한 기준선으로 계속 보존하지만 평균 AUPRC `0.4339`로 튜닝 상위 3개 성능 후보에서는 제외하는 안이다.

## 승인 및 후속 실행 상태

사용자가 세 후보와 Feature-set을 승인해 후보마다 20 Trial×4개 시간순 Fold의 Optuna 다목적 튜닝을 완료했다. 튜닝 결과와 남은 대표 Trial Trade-off는 `optuna_report.md`와 `MVP 단계별 구현 체크리스트.md`에 기록했다. 다음에는 대표 Trial을 종합 승인한 뒤 개별 OOF 성능과 Soft Voting·Stacking을 비교하고, 별도 승인 후 F2 기반 운영 임계값·최종 모델·잠긴 테스트 평가로 진행한다.

전체 34개 수치는 `full_comparison.md`, 원자료는 `full_model_feature_summary.csv`와 `full_fold_metrics.csv`를 따른다.
