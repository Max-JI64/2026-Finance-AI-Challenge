# RE5 LightGBM Quantile 내부 Holdout 평가

- 기준 Feature 분기: 2025Q2
- 결과 분기: Target A=2025Q3, Target B·보조=2025Q3~Q4
- 이 평가는 새 독립 감사가 아닌 사전 승인된 내부 시간 Holdout이다.
- 결과를 본 뒤 모델을 재선택하지 않는다.
- 기존 Stage 5·6 이진모델은 재학습·서비스 사용하지 않는다.

## Target별 결과

| Target | 유효행 | MAE | Median AE | Coverage | 구간 폭 | Interval Score | Spearman | 방향 일치율 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `target_a_next_quarter_yoy` | 20,186 | 0.896258 | 0.133753 | 0.6939 | 1.332767 | 6.361924 | 0.5686 | 0.6938 |
| `target_aux_min_next_two_quarters_yoy` | 19,753 | 0.325032 | 0.115822 | 0.7016 | 0.595497 | 2.053495 | 0.5334 | 0.7303 |
| `target_b_next_two_quarters_yoy` | 19,753 | 0.455367 | 0.118675 | 0.7103 | 0.737602 | 3.107992 | 0.5190 | 0.6859 |

## 상태 경계

이 결과는 RE5 LightGBM의 고정된 1회 내부 Holdout이다. 2026Q1·Q2 결과를 사용하는 새 독립 감사가 확보되기 전에는 독립검증 완료라고 표현하지 않는다.
