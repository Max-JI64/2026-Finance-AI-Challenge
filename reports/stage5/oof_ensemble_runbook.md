# Stage 5 OOF·Ensemble 사용자 실행 가이드

## 실행 범위

- 대표 설정: LightGBM Trial 10, XGBoost Trial 16, CatBoost Trial 18
- 비교 대상: 세 개별 모델, 동일 가중 Soft Voting, nested OOF Logistic Stacking
- Outer 평가: Stage 4에서 고정한 4개 시간순 Fold
- Stacking 학습: 각 Outer Train 내부의 마지막 3개 기간에 대해 별도 OOF 예측을 생성한다.
- 총 진행 단위: 모델 Fit 48개 + Fold별 Ensemble 생성 4개 = 52단계
- 2025 잠긴 테스트는 열지 않는다.

## 1. 실행 전 검증만 하기

프로젝트 루트 PowerShell에서 다음 명령을 실행한다.

```powershell
& '.\scripts\run_stage5_oof_ensemble.ps1' -ValidateOnly
```

`validation_passed`, 대표 Trial 3개, Outer Fold 4개, Inner 기간, `planned_total_steps: 52`, `locked_test_opened: false`가 출력되면 실행 계약 검증이 통과한 것이다. 이 명령은 모델을 학습하지 않는다.

## 2. 실제 실행

```powershell
& '.\scripts\run_stage5_oof_ensemble.ps1'
```

PowerShell 실행 정책으로 `.ps1` 실행이 차단된 경우에는 같은 위치에서 Python을 직접 실행한다.

```powershell
& 'C:\Program Files\Python313\python.exe' -u -m src.models.run_stage5_oof_ensemble
```

터미널에 다음 정보가 계속 출력된다.

- 현재 단계와 전체 단계: `step=5/52 (9.6%)`
- 현재 Outer Fold·Inner 기간·모델·Trial
- 완료 또는 체크포인트 재사용 여부: `DONE`, `SKIP`
- Fold별 AUPRC, AUROC, Brier Score, Fit 시간
- 최종 산출물 저장 완료 또는 오류 Stack trace

PowerShell 창을 닫지 않으면 실행 로그를 실시간으로 볼 수 있다. 같은 실행을 두 터미널에서 동시에 시작하지 않는다.

## 3. 별도 터미널에서 현재 상태만 확인

```powershell
& '.\scripts\run_stage5_oof_ensemble.ps1' -Status
```

`reports/stage5/ensemble_progress.json`의 상태, 완료 단계, 백분율, 현재 작업을 출력한다. 상태 확인 명령은 진행 중인 학습을 중단하지 않는다.

로그 파일을 실시간으로 따라가려면 다음 명령을 사용한다.

```powershell
Get-Content -Encoding UTF8 -Wait -LiteralPath '.\reports\stage5\ensemble_run.log'
```

진행 JSON을 직접 확인할 수도 있다.

```powershell
Get-Content -Encoding UTF8 -Raw -LiteralPath '.\reports\stage5\ensemble_progress.json'
```

## 4. 중단 후 재개

동일한 실제 실행 명령을 다시 사용한다.

```powershell
& '.\scripts\run_stage5_oof_ensemble.ps1'
```

완료된 모델·Fold 예측은 `reports/stage5/ensemble_checkpoints/`에서 검증 후 `SKIP`하고, 미완료 작업만 이어서 실행한다. 체크포인트를 수동으로 수정하거나 일부 파일만 옮기지 않는다.

## 완료 시 생성되는 산출물

- `selected_oof_report.md` — 개별 모델·Voting·Stacking 종합 비교표
- `selected_oof_summary.csv` — 전체 OOF와 Fold 안정성 요약
- `selected_oof_fold_metrics.csv` — 5개 실행×4개 Fold 지표
- `selected_oof_predictions.parquet` — 선택 모델·Ensemble OOF 확률
- `selected_oof_industry_metrics.csv` — 업종별 주요 지표
- `selected_oof_manifest.json` — 실행 계약과 완료 상태
- `ensemble_run.log` — 콘솔과 동일한 전체 실행 로그
- `ensemble_progress.json` — 현재 단계와 완료율

이 실행은 최종 모델이나 F2 임계값을 자동 선택하지 않는다. 모든 결과를 확인한 뒤 사용자 승인으로 최종 모델·임계값을 고정하고, 그 다음에만 2025 잠긴 테스트를 한 번 평가한다.
