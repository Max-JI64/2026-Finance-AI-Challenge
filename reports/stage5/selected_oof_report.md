# Stage 5 선택 Trial OOF·Ensemble 비교

- 생성 시각: 2026-08-15T18:06:54+09:00
- 대표 설정: LightGBM Trial 10, XGBoost Trial 16, CatBoost Trial 18
- Outer 평가: Stage 4 고정 4개 시간순 Fold
- Soft Voting: 세 모델 확률의 사전 고정 동일 가중 평균
- Stacking: 각 Outer Train 안에서 마지막 3개 기간의 nested OOF를 생성해 L2 Logistic meta-model을 Fit
- 누수 방지: Inner Train의 Target 종료분기는 Inner Validation보다 최소 2분기 앞서며 Outer Validation은 meta-model Fit에 사용하지 않음
- 임계값 0.5 지표는 참고용이며 최종 F2 임계값은 아직 선택하지 않음
- 자동 최종 순위·최종 모델 선택 없음
- 2025 잠긴 테스트: 미접근

| 실행 | 평균 Fold AUPRC | 평균 Fold AUROC | 전체 OOF AUPRC | 전체 OOF AUROC | 최악 Fold AUPRC | AP 표준편차 | Brier | Log Loss | 추론 Base 모델 수 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| lightgbm__trial10 | 0.6436 | 0.8104 | 0.6454 | 0.8108 | 0.6120 | 0.0237 | 0.1565 | 0.4749 | 1 |
| xgboost__trial16 | 0.6421 | 0.8100 | 0.6439 | 0.8103 | 0.6116 | 0.0232 | 0.1568 | 0.4758 | 1 |
| catboost__trial18 | 0.6364 | 0.8057 | 0.6384 | 0.8061 | 0.6012 | 0.0245 | 0.1577 | 0.4789 | 1 |
| soft_voting_equal | 0.6456 | 0.8111 | 0.6474 | 0.8115 | 0.6147 | 0.0230 | 0.1562 | 0.4742 | 3 |
| stacking_nested_logistic | 0.6455 | 0.8113 | 0.6446 | 0.8104 | 0.6144 | 0.0233 | 0.1566 | 0.4792 | 3 |

## 종합 검토

- 동일 가중 Soft Voting은 LightGBM 단일 모델보다 평균 Fold AUPRC `+0.0020`, 평균 Fold AUROC `+0.0007`, 최악 Fold AUPRC `+0.0026` 개선됐다.
- Soft Voting은 전체 OOF AUPRC `0.6474`, 전체 OOF AUROC `0.8115`, Brier `0.1562`, Log Loss `0.4742`로 다섯 실행 중 가장 균형이 좋다.
- Soft Voting의 Fold별 AUPRC는 네 Fold 모두 LightGBM보다 높았고, 비교 가능한 62개 업종 중 37개에서 LightGBM보다 높았다. 업종별 AUPRC 차이의 중앙값은 `+0.0007`이다.
- Stacking은 평균 Fold AUROC `0.8113`이 가장 높지만 Soft Voting보다 전체 OOF AUPRC·AUROC와 확률 품질이 낮아 추가 복잡도를 정당화하지 못했다.
- 성능 우선 권장안은 동일 가중 Soft Voting이고, 단일 모델 운영 단순성을 우선하면 성능 차이가 작은 LightGBM Trial 10이 대안이다.

전체 Fold·업종별 지표와 확률은 CSV·Parquet 산출물에 보존했다. 이 표를 사용자와 종합 검토한 뒤에만 최종 모델과 F2 운영 임계값을 확정한다.
