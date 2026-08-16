# RE Stage 5 승인 계약

## 상태

- 승인일: 2026-08-16
- 상태: **LightGBM Quantile 사용자 직접 내부 Holdout 평가기 준비 완료·실행 대기**
- 재개일: 2026-08-16
- 완료 범위: Target v2·Panel v2·Quantile EDA·Feature contract·시간순 Fold·해시 Manifest
- 사용자 실행 조건: 실제 Holdout 학습·평가는 사용자가 `scripts/run_re_stage5_holdout.ps1 -ConfirmOpenHoldout`으로 직접 실행하고 터미널·파일 진행 로그를 확인한다.
- 현재 금지: Codex의 모델 fit, 명시적 확인 없는 내부 Holdout Target 개방, Holdout 결과를 본 뒤 모델 재선택, 기존 Stage 6 재활성화, 외부 데이터 수집·다운로드

## 관측 단위와 Target

- 관측 단위: 기준분기 × 서울 상권코드 × 서비스 업종코드
- Target A: 다음 1분기 전년동기 대비 매출증감률
- Target B: 다음 2분기 합산 전년동기 대비 매출증감률
- 보조 Target: 다음 2분기 중 최저 전년동기 대비 매출증감률
- QoQ: EDA·Challenger Target으로만 사용하고 기본 현금흐름에는 적용하지 않음

분모 0·결측은 해당 Target 결측으로 남기고 Panel 행과 사유 플래그를 보존한다. 누락된 미래 행을 0이나 폐업으로 추정하지 않는다. 명시적 미래 매출 0과 양수 분모가 함께 있을 때만 -100%로 계산한다. 극단값은 자동 절단하지 않는다.

## 시간 분할

```text
개발 기준분기: 2021Q4~2024Q4
Validation: 2024Q1·Q2·Q3·Q4 expanding-window 4개 Fold
Purge: 각 Validation 직전 기준분기 1개
내부 홀드아웃 전 Purge: 2025Q1
내부 홀드아웃 기준분기: 2025Q2
내부 홀드아웃 결과: Target A=2025Q3, Target B·보조 Target=2025Q3·Q4
```

2025Q1은 독립 학습 관측으로 사용하지 않지만 2024Q3·Q4 Target의 미래 결과와 2025Q2 홀드아웃의 과거 Feature로 사용할 수 있다. 2025Q3·Q4는 RE5의 Target·Feature·처리기준·모델 선택에서 격리하고 마지막 내부 홀드아웃에만 사용한다.

2025Q3·Q4는 이미 로컬에 존재한 자료이므로 새 독립 감사가 아니다. 2026Q1·Q2 추정매출이 현재 없어 신규 독립 감사는 미확보 상태이며, 확보 전 Quantile 모델은 독립검증 한계를 표시한 단일 ML 후보로 관리한다.

## 데이터와 모델

첫 실행은 기존 Stage 3 Panel만 사용한 Baseline으로 제한한다. 신규 외부 데이터는 Baseline 이후 별도 사용자 승인과 사용자 직접 다운로드를 거쳐 데이터군별 Ablation으로만 검토한다.

후보는 계절 단순 Baseline, 업종별 Median Baseline, Regularized Linear Quantile, LightGBM Quantile, CatBoost Quantile·MultiQuantile이며 XGBoost Quantile은 환경 지원 안정성 확인 후 조건부로 포함한다. 기존 LightGBM v1은 Feature·초기값·재학습 후보로 사용하지 않고 Artifact와 Stage 6 결과를 동결한다.

### 2026-08-16 모델 선택 기록

- 개발 CV 72/72 완료와 무결성 검증 후 사용자가 `LightGBM Quantile`을 내부 Holdout 평가 후보로 선택했다.
- 이 선택은 LightGBM 알고리즘 계열만 같을 뿐 기존 Stage 5·6 이진분류 Artifact를 재학습하거나 덮어쓰는 결정이 아니다.
- 기존 모델은 향후 두 분기 지속 악화 여부의 상대 위험순위를, RE5 모델은 다음 1분기·2분기 매출증감률의 P10·P50·P90 범위를 다룬다.
- 기존 Stage 5·6 이진모델은 새 데이터로 재학습하지 않고 서비스 추론·화면·Fallback에서 제외한다.
- 기존 코드·Artifact·평가보고서는 삭제하지 않고 과거 검증 근거와 재현용 `archived evidence`로 보존한다.
- 서비스에서 사용하는 ML 출력은 RE5 LightGBM Quantile 하나로 제한하며, 모델 사용 불가 시 사용자가 직접 매출충격률을 선택한다.
- 내부 Holdout 실행은 사용자의 다음 지시 전까지 보류한다.

## 평가

- 중앙 예측: MAE, Median AE, RMSE, Mean Error
- Quantile: P10·P50·P90 Pinball Loss와 실제 도달률
- 구간: P10~P90 Coverage, 평균 구간 폭, Interval Score
- 순위·방향: Spearman 상관계수, 상승·하락 방향 일치율
- 구조: Quantile Crossing 비율과 보정 전후 결과
- 안정성: Fold별 최악값·표준편차, 업종별 MAE·Pinball·Coverage
- 서비스: 현금 고갈 시점·정책 선택 민감도

기존 이진 Target v1과 LightGBM v1의 AUROC·AUPRC는 참고 부록에만 보존한다. 새 이진분류 모델을 학습하지 않으며 AUROC·AUPRC로 Quantile 모델을 선정하지 않는다.

## 서비스 경계

P10은 하방, P50은 기준, P90은 회복 집계환경이다. 개별 점포의 실제 매출이나 폐업확률로 표시하지 않는다. Target A는 약 13주, Target B는 약 6개월 환경을 설명하지만 개인 현금흐름 적용률과 월별 배분은 RE7에서 별도 승인한다.

기존 Stage 6은 서비스에서 사용하지 않으며 재학습하지 않는다. RE5 LightGBM Quantile을 유일한 ML 외부환경 후보로 사용하되 신규 독립 감사 미확보 상태를 명시한다. RE5가 사용 불가하거나 필요한 품질 Gate를 통과하지 못하면 기존 이진 위험순위로 되돌리지 않고 사용자 직접 매출충격률을 사용한다.
