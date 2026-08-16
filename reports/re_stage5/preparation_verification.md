# RE5 Baseline 준비 검증

## 판정

**준비 Gate 통과, 모델 학습 대기.** 기존 Stage 3 Panel만 사용한 Target·Panel·Fold·EDA 준비가 재현되었고 모델 적합은 실행하지 않았다.

## 핵심 결과

- 원천 Panel: 439,141행·199열, SHA-256 `88370a02f592c020196613e69a9dc8e642cf3ba14a00003bb6cdd37198f40e07`
- Stage 4.5 파생 Feature 정의 134개를 재생성했으며 승인된 `common_baseline` 197개가 개발·홀드아웃 양쪽에 모두 존재한다.
- 개발자료: 2021Q4~2024Q4, 286,613행
- Target A 유효: 268,541행
- Target B·보조 Target 유효: 각각 262,869행
- QoQ Challenger 유효: 278,883행
- 내부 홀드아웃 Feature: 2025Q2, 21,452행
- Fold membership: 1,146,452행, Validation 2024Q1·Q2·Q3·Q4와 직전 1분기 Purge 확인

## Target 진단

Target을 절단하지 않았기 때문에 작은 전년동기 분모를 가진 일부 관측의 큰 양의 변화율이 평균에 강하게 영향을 준다. Target A의 평균은 4.7300이지만 P50은 0.0000이고 P90은 0.7405다. 따라서 후보 비교에서는 MAE·RMSE뿐 아니라 Median AE·Pinball·Coverage·업종/Fold 안정성을 함께 봐야 한다. 이 진단으로 승인된 무절단 계약을 변경하지 않았다.

## 잠금·누수 확인

- Panel v1을 덮어쓰지 않고 별도 `processed_re/model/re_stage5`에 저장했다.
- Panel 키 중복은 0건이다.
- 개발자료의 최대 기준분기는 2024Q4다.
- 2025Q2 파일에는 Feature만 있으며 `target_` 열이 없다.
- 2025Q3·Q4 결과 Target은 생성하거나 열지 않았다.
- Target 결측은 0·폐업으로 보정하지 않고 사유를 보존했다.
- Target 원값의 clipping·winsorization은 0건이다.
- 모든 산출물의 존재와 Manifest SHA-256 일치를 검증했다.
- 사용자 실행 `DryRun`이 개발 Parquet 스키마에서 승인된 197개 Feature를 직접 확인한다.

## 검증 실행

- RE5 단위 테스트: `4 passed`
- 전체 회귀 테스트: `68 passed`
- 준비 산출물 검증: 모든 필수 검사 통과
- 학습 실행기 dry-run: 3 Target × 4 Fold × 6 후보 = 72 task, 패키지 가용성 확인
- 실제 모델 fit: `0회`
- 내부 홀드아웃 Target 접근: `0회`
