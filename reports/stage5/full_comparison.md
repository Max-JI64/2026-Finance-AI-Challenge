# Stage 5 전체 무튜닝 비교

- 계획 변형: 34개, 완료 변형: 34개
- 분할: Stage 4에서 고정한 4개 시간순 expanding-window Fold
- 전처리: 각 Fold Train에만 Fit
- 비교 정책: 사전 숫자 컷과 자동 순위 없이 모든 계획 결과를 공개한 뒤 종합 판단
- 공동 핵심 지표: AUPRC/AP와 AUROC
- 보조 관찰: 최악 Fold AUPRC, Fold 표준편차, Brier Score, Log Loss, 학습·추론 시간
- F2와 임계값 0.5 지표: 참고값이며 후보 선택 자동 규칙에 사용하지 않음
- 2025 잠긴 테스트: 미접근

## Feature-set 해석

- Feature-set은 서로 다른 표본 데이터셋이 아니라 동일한 개발 행에 적용하는 열 조합이다. Target과 4개 Fold는 모든 실행에서 동일하다.
- 공통 197개에도 인구 총계·구성비·인구 간 비율·점포당·면적당 지표가 포함된다. 트리 Ablation은 성별·연령별 원시 절대값 한 묶음만 독립적으로 추가한다.
- 실제 7개 Feature-set의 정확한 열 목록과 SHA-256은 `reports/stage5/feature_sets.json`에 기록했다.

| 모델 | Feature set | 완료 Fold | Feature 수 | 평균 AUPRC | 평균 AUROC | 최악 Fold AUPRC | AUPRC 표준편차 | 평균 Brier | 평균 Log Loss | 기준선 대비 AUPRC | 기준선 대비 AUROC | 총 학습초 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| dummy_prior | prior | 4/4 | 0 | 0.2992 | 0.5000 | 0.2798 | 0.0166 | 0.2144 | 0.6227 | - | - | 0.0 |
| logistic_l2 | linear_common_plus_log1p | 4/4 | 207 | 0.4339 | 0.6665 | 0.3965 | 0.0338 | 0.1973 | 0.5795 | - | - | 325.6 |
| logistic_l1 | linear_common_plus_log1p | 4/4 | 207 | 0.4284 | 0.6617 | 0.3929 | 0.0318 | 0.1992 | 0.5840 | - | - | 935.8 |
| logistic_elasticnet | linear_common_plus_log1p | 4/4 | 207 | 0.4284 | 0.6617 | 0.3929 | 0.0318 | 0.1992 | 0.5840 | - | - | 963.4 |
| random_forest | common_baseline | 4/4 | 197 | 0.5905 | 0.7797 | 0.5546 | 0.0285 | 0.1766 | 0.5256 | +0.0000 | +0.0000 | 332.8 |
| extra_trees | common_baseline | 4/4 | 197 | 0.4601 | 0.6784 | 0.4176 | 0.0367 | 0.2030 | 0.5925 | +0.0000 | +0.0000 | 96.2 |
| lightgbm | common_baseline | 4/4 | 197 | 0.6344 | 0.8059 | 0.6021 | 0.0245 | 0.1580 | 0.4792 | +0.0000 | +0.0000 | 43.3 |
| xgboost | common_baseline | 4/4 | 197 | 0.6326 | 0.8061 | 0.6004 | 0.0245 | 0.1580 | 0.4790 | +0.0000 | +0.0000 | 51.9 |
| catboost | common_baseline | 4/4 | 197 | 0.5885 | 0.7818 | 0.5634 | 0.0169 | 0.1674 | 0.5036 | +0.0000 | +0.0000 | 230.6 |
| random_forest | tree_plus_sales_amount_raw_components | 4/4 | 220 | 0.5930 | 0.7788 | 0.5555 | 0.0285 | 0.1763 | 0.5249 | +0.0025 | -0.0009 | 399.7 |
| extra_trees | tree_plus_sales_amount_raw_components | 4/4 | 220 | 0.4667 | 0.6841 | 0.4305 | 0.0354 | 0.2020 | 0.5900 | +0.0066 | +0.0058 | 112.8 |
| lightgbm | tree_plus_sales_amount_raw_components | 4/4 | 220 | 0.6323 | 0.8058 | 0.5989 | 0.0249 | 0.1582 | 0.4796 | -0.0021 | -0.0002 | 47.4 |
| xgboost | tree_plus_sales_amount_raw_components | 4/4 | 220 | 0.6336 | 0.8061 | 0.6009 | 0.0249 | 0.1580 | 0.4790 | +0.0010 | +0.0000 | 63.8 |
| catboost | tree_plus_sales_amount_raw_components | 4/4 | 220 | 0.5866 | 0.7807 | 0.5633 | 0.0168 | 0.1680 | 0.5051 | -0.0018 | -0.0011 | 246.7 |
| random_forest | tree_plus_transaction_count_raw_components | 4/4 | 220 | 0.5917 | 0.7793 | 0.5594 | 0.0271 | 0.1763 | 0.5248 | +0.0013 | -0.0004 | 412.7 |
| extra_trees | tree_plus_transaction_count_raw_components | 4/4 | 220 | 0.4681 | 0.6862 | 0.4332 | 0.0324 | 0.2014 | 0.5884 | +0.0080 | +0.0078 | 117.8 |
| lightgbm | tree_plus_transaction_count_raw_components | 4/4 | 220 | 0.6343 | 0.8058 | 0.6040 | 0.0236 | 0.1581 | 0.4795 | -0.0001 | -0.0002 | 46.8 |
| xgboost | tree_plus_transaction_count_raw_components | 4/4 | 220 | 0.6333 | 0.8064 | 0.6002 | 0.0248 | 0.1579 | 0.4787 | +0.0007 | +0.0003 | 66.3 |
| catboost | tree_plus_transaction_count_raw_components | 4/4 | 220 | 0.5855 | 0.7802 | 0.5506 | 0.0238 | 0.1682 | 0.5058 | -0.0030 | -0.0016 | 249.5 |
| random_forest | tree_plus_floating_population_raw_components | 4/4 | 218 | 0.5885 | 0.7788 | 0.5538 | 0.0271 | 0.1770 | 0.5264 | -0.0019 | -0.0009 | 404.0 |
| extra_trees | tree_plus_floating_population_raw_components | 4/4 | 218 | 0.4653 | 0.6816 | 0.4268 | 0.0371 | 0.2022 | 0.5906 | +0.0051 | +0.0032 | 119.5 |
| lightgbm | tree_plus_floating_population_raw_components | 4/4 | 218 | 0.6342 | 0.8061 | 0.6002 | 0.0251 | 0.1579 | 0.4790 | -0.0003 | +0.0002 | 46.6 |
| xgboost | tree_plus_floating_population_raw_components | 4/4 | 218 | 0.6327 | 0.8061 | 0.6008 | 0.0242 | 0.1581 | 0.4792 | +0.0001 | +0.0000 | 62.1 |
| catboost | tree_plus_floating_population_raw_components | 4/4 | 218 | 0.5913 | 0.7837 | 0.5600 | 0.0192 | 0.1667 | 0.5018 | +0.0029 | +0.0018 | 242.8 |
| random_forest | tree_plus_resident_population_raw_components | 4/4 | 217 | 0.5898 | 0.7789 | 0.5541 | 0.0276 | 0.1770 | 0.5266 | -0.0006 | -0.0007 | 398.2 |
| extra_trees | tree_plus_resident_population_raw_components | 4/4 | 217 | 0.4603 | 0.6793 | 0.4172 | 0.0384 | 0.2025 | 0.5913 | +0.0002 | +0.0010 | 118.9 |
| lightgbm | tree_plus_resident_population_raw_components | 4/4 | 217 | 0.6339 | 0.8063 | 0.5977 | 0.0262 | 0.1579 | 0.4790 | -0.0006 | +0.0003 | 50.5 |
| xgboost | tree_plus_resident_population_raw_components | 4/4 | 217 | 0.6335 | 0.8061 | 0.6003 | 0.0248 | 0.1580 | 0.4789 | +0.0009 | +0.0000 | 64.6 |
| catboost | tree_plus_resident_population_raw_components | 4/4 | 217 | 0.5867 | 0.7805 | 0.5683 | 0.0146 | 0.1686 | 0.5067 | -0.0017 | -0.0014 | 255.3 |
| random_forest | tree_plus_worker_population_raw_components | 4/4 | 217 | 0.5895 | 0.7785 | 0.5522 | 0.0290 | 0.1770 | 0.5264 | -0.0010 | -0.0012 | 393.6 |
| extra_trees | tree_plus_worker_population_raw_components | 4/4 | 217 | 0.4630 | 0.6809 | 0.4242 | 0.0365 | 0.2026 | 0.5915 | +0.0028 | +0.0025 | 118.2 |
| lightgbm | tree_plus_worker_population_raw_components | 4/4 | 217 | 0.6338 | 0.8059 | 0.6003 | 0.0245 | 0.1581 | 0.4794 | -0.0006 | -0.0001 | 46.9 |
| xgboost | tree_plus_worker_population_raw_components | 4/4 | 217 | 0.6329 | 0.8063 | 0.5995 | 0.0252 | 0.1579 | 0.4787 | +0.0003 | +0.0002 | 62.4 |
| catboost | tree_plus_worker_population_raw_components | 4/4 | 217 | 0.5913 | 0.7831 | 0.5674 | 0.0165 | 0.1673 | 0.5032 | +0.0029 | +0.0013 | 252.8 |

## 의사결정 상태

자동 유지·탈락 또는 상위 3개 선택을 수행하지 않았다. 전체 결과와 모델별 기준선 대비 차이를 사용자와 종합 검토한 뒤 Optuna 후보를 확정한다.
