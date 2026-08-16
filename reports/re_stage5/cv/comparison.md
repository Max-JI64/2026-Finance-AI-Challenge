# RE5 Quantile 후보 모델 시간순 CV 비교

- 이 결과는 2024Q1~Q4 expanding-window 개발검증이다.
- 2025Q2 내부 홀드아웃 Target은 아직 열지 않았다.
- 새 독립 감사기간이 없으므로 어떤 후보도 운영 기본모델로 자동 승격하지 않는다.
- 최종 후보 선택은 평균뿐 아니라 최악 Fold·업종별 붕괴·Coverage·구간 폭을 함께 검토해야 한다.

## Target별 평균 핵심 지표

| Target | 모델 | MAE | P50 Pinball | P10~P90 Coverage | 구간 폭 | 최악 Fold MAE |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `target_a_next_quarter_yoy` | `xgboost` | 0.7463 | 0.3731 | 0.7689 | 2.9748 | 1.0908 |
| `target_a_next_quarter_yoy` | `lightgbm` | 0.7501 | 0.3750 | 0.7778 | 1.3508 | 1.0941 |
| `target_a_next_quarter_yoy` | `catboost` | 0.7701 | 0.3850 | 0.8121 | 1.2655 | 1.1434 |
| `target_a_next_quarter_yoy` | `industry_median` | 0.8679 | 0.4339 | 0.8101 | 1.2717 | 1.2196 |
| `target_a_next_quarter_yoy` | `seasonal_naive` | 1.1475 | 0.5737 | 0.8421 | 1.1617 | 1.3717 |
| `target_a_next_quarter_yoy` | `regularized_linear` | 77.0855 | 38.5427 | 0.7480 | 147.0668 | 191.8601 |
| `target_aux_min_next_two_quarters_yoy` | `xgboost` | 0.2809 | 0.1405 | 0.7711 | 0.6641 | 0.3567 |
| `target_aux_min_next_two_quarters_yoy` | `lightgbm` | 0.2816 | 0.1408 | 0.7813 | 0.6235 | 0.3571 |
| `target_aux_min_next_two_quarters_yoy` | `catboost` | 0.2856 | 0.1428 | 0.7948 | 0.6451 | 0.3619 |
| `target_aux_min_next_two_quarters_yoy` | `industry_median` | 0.3452 | 0.1726 | 0.8180 | 0.8272 | 0.4214 |
| `target_aux_min_next_two_quarters_yoy` | `seasonal_naive` | 0.8011 | 0.4005 | 0.8374 | 1.0457 | 1.1641 |
| `target_aux_min_next_two_quarters_yoy` | `regularized_linear` | 63.1848 | 31.5924 | 0.4979 | 222.6402 | 192.1183 |
| `target_b_next_two_quarters_yoy` | `xgboost` | 0.3434 | 0.1717 | 0.7652 | 0.8483 | 0.4223 |
| `target_b_next_two_quarters_yoy` | `lightgbm` | 0.3440 | 0.1720 | 0.7797 | 0.7629 | 0.4213 |
| `target_b_next_two_quarters_yoy` | `catboost` | 0.3502 | 0.1751 | 0.7911 | 0.7980 | 0.4283 |
| `target_b_next_two_quarters_yoy` | `industry_median` | 0.4297 | 0.2148 | 0.8058 | 0.9690 | 0.5149 |
| `target_b_next_two_quarters_yoy` | `seasonal_naive` | 0.8386 | 0.4193 | 0.8394 | 1.0705 | 1.1891 |
| `target_b_next_two_quarters_yoy` | `regularized_linear` | 108.8924 | 54.4462 | 0.7770 | 296.5047 | 227.2860 |

## 아직 하지 않은 결정

- 모델 최종 선택·Stage 6 교체 여부는 자동 결정하지 않았다.
- 2025Q2 내부 홀드아웃은 사용자 모델 승인 뒤 별도 실행한다.
- 2026Q1·Q2 결과를 쓰는 새 독립 감사는 자료 미확보 상태다.
- 개인 현금흐름 적용률·분기 변화율의 월별 배분은 RE7 승인 전 적용하지 않는다.
