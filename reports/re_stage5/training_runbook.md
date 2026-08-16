# RE5 사용자 직접 학습 Runbook

## 현재 상태

- Panel v2·Target v2·시간순 Fold·Quantile EDA 준비 완료
- 실제 모델 학습 0회
- 2025Q2 내부 홀드아웃 Target 미개방
- CV 계획: 3개 Target × 4개 Fold × 6개 후보 = 72개 task

## 실행 전 확인

```powershell
.\scripts\run_re_stage5_cv.ps1 -DryRun
```

이 명령은 입력·패키지·task 수만 확인하고 모델을 학습하지 않는다.
또한 개발 Parquet에 승인된 `common_baseline` 197개 Feature가 모두 존재하지
않으면 학습 전에 재준비 명령을 안내하며 중단한다.

## 학습 실행

```powershell
.\scripts\run_re_stage5_cv.ps1
```

터미널에는 다음 정보가 계속 출력된다.

- 전체 진행 위치: `[현재 task/72]`
- Target, Fold, Validation 분기, 모델
- Train·Validation 행 수와 전처리 행렬 크기
- Linear epoch 또는 Boosting iteration
- task별 MAE, Coverage, Quantile Crossing, 경과시간
- 완료율과 현재까지의 평균 task 시간에 근거한 대략적 ETA

동일 로그는 `reports/re_stage5/cv/training.log`에도 누적된다.

## 별도 터미널에서 상태 확인

```powershell
.\scripts\run_re_stage5_cv.ps1 -Status
```

`reports/re_stage5/cv/progress.json`에는 완료 task 수, 전체 task 수, 완료율,
현재 Target·Fold·모델, holdout 미개방 상태가 기록된다.

## 중단 후 재개

`Ctrl+C`로 중단한 뒤 같은 학습 명령을 다시 실행하면 완료된 JSON·Parquet
checkpoint를 검증하고 건너뛴다. 중단 당시 적합 중이던 task만 처음부터 다시
실행한다. 설정이나 준비자료 해시가 달라진 checkpoint는 섞지 않고 오류로
중단한다.

실패 시 `progress.json`의 상태는 `failed_resumable`로 바뀌고 오류 유형·메시지와
재개 명령을 보존한다. 완료 checkpoint가 없는 첫 task 실패는 다음 실행에서
`[1/72]`부터 다시 시작한다.

## CV 완료 후

CV가 끝나면 다음 파일이 생성된다.

- `reports/re_stage5/cv/fold_metrics.csv`
- `reports/re_stage5/cv/industry_metrics.csv`
- `reports/re_stage5/cv/model_summary.csv`
- `reports/re_stage5/cv/comparison.md`

CV 완료만으로 모델을 자동 선택하거나 Stage 6을 교체하지 않는다. 결과 검토 후
사용자가 모델과 기존 Stage 6의 유지·병행·교체 지위를 승인해야 한다. 그 승인
전에는 2025Q2 내부 홀드아웃 Target을 열지 않는다.
