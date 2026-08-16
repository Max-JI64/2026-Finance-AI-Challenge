# RE5 LightGBM 내부 Holdout 사용자 실행 안내

## 현재 상태

- 선택 모델: `LightGBM Quantile`
- 평가 기준 Feature 분기: 2025Q2
- 결과 분기: Target A는 2025Q3, Target B·보조 Target은 2025Q3~Q4
- 예정 작업: Target 3개 × Quantile 3개 = LightGBM 회귀기 9개
- Holdout Feature 행: 21,452행
- 현재 Target 개방: **아니오**
- Codex가 수행한 실제 모델 학습: **없음**

## 1. 실행 전 확인

다음 명령은 Target을 열거나 모델을 학습하지 않는다.

```powershell
.\scripts\run_re_stage5_holdout.ps1 -DryRun
```

현재 진행 상태는 다음 명령으로 확인한다.

```powershell
.\scripts\run_re_stage5_holdout.ps1 -Status
```

## 2. 실제 평가 실행

다음 명령만 2025Q3·Q4 결과를 열고 LightGBM을 학습한다.

```powershell
.\scripts\run_re_stage5_holdout.ps1 -ConfirmOpenHoldout
```

`-ConfirmOpenHoldout`은 다음 사항에 대한 명시적 확인이다.

1. 선택 모델은 LightGBM으로 고정한다.
2. Holdout 결과를 본 뒤 다른 모델로 재선택하지 않는다.
3. 기존 Stage 5·6 이진모델을 재학습하거나 서비스에 복귀시키지 않는다.
4. 실행 실패 시에도 같은 LightGBM 계약으로만 checkpoint 이후 재개한다.

## 3. 진행 로그

터미널에는 Target `1/3~3/3`, 각 Target의 Quantile `1/3~3/3`, 50 iteration 간격 Train-only 지표, MAE·Coverage·소요시간이 출력된다.

동일한 로그는 다음 파일에 누적된다.

- `reports/re_stage5/holdout/evaluation.log`
- `reports/re_stage5/holdout/progress.json`
- `reports/re_stage5/holdout/access.json`

## 4. 완료 산출물

- `reports/re_stage5/holdout/holdout_metrics.csv`
- `reports/re_stage5/holdout/holdout_industry_metrics.csv`
- `reports/re_stage5/holdout/holdout_predictions.parquet`
- `reports/re_stage5/holdout/holdout_report.md`
- `reports/re_stage5/holdout/holdout_manifest.json`
- `artifacts/re_stage5_lightgbm_quantile/*.joblib`

완료된 Holdout은 재실행하지 않는다. 기술적 실패 상태에서는 같은 명령으로 동일 LightGBM 계약만 재개한다.
