# Stage 4.5 Feature contract — D안 승인 완료

> 사용자가 2026-08-15 12:17 KST에 D안(공통 기준선 + 트리 원시 변수군 Ablation)을 승인했다. 계약과 다음 단계 계획만 갱신했으며 Stage 5 학습·Ablation은 시작하지 않았다.

## 승인된 D안 — 공통 기준선 + 트리 Ablation

### 1. 모든 모델의 공통 기준선

- 코드와 코드명은 코드만 유지하고, 시간은 `기준_연도`와 `기준_분기`만 유지한다.
- 총매출·총거래·총인구는 유지하되 요일·시간대·성별·연령별 원시 구성요소는 구성비로 치환한다.
- 평균 객단가, 점포당 지표, 개·폐업 강도, 인구 상호비율·밀도, 과거 Rolling, 변화 지속성 Indicator를 공통 Feature로 추가한다.
- 유동·상주·직장인구, 시설, 아파트, 공간 변수는 보조 Feature군으로 유지해 Stage 5에서 데이터군별 Ablation을 가능하게 한다.
- PCA는 적용하지 않는다.

### 2. 선형 모델 확장

- L2·L1·Elastic-Net Logistic에만 `log1p` 후보 10개를 추가한다.
- 구조 제거 후 조건수가 높으므로 비정규화 Logistic은 사용하지 않는다.
- 이 규제는 선형 모델군에만 해당하며 트리 모델을 제외하지 않는다.

### 3. 트리 모델 원시 변수군 Ablation

- Feature-set은 서로 다른 행이나 Target 데이터셋이 아니라 동일한 개발 행에서 사용하는 열 조합이다. 행, Target, 4개 시간순 Fold는 모든 비교에서 동일하다.
- 공통 기준선에도 유동·상주·직장인구의 총계, 구성비, 인구 간 비율, 점포당·면적당 지표가 들어간다. Ablation은 이 정보를 대체하지 않고 성별·연령별 원시 인원수 같은 세부 절대값만 추가한다.
- Random Forest, Extra Trees, LightGBM, XGBoost, CatBoost를 모두 유지한다.
- 각 트리는 공통 기준선으로 먼저 평가한다.
- 매출금액, 거래건수, 유동인구, 상주인구, 직장인구의 원시 세부변수군을 공통 기준선에 한 번에 하나씩 독립적으로 추가한다.
- `replace`로 분류된 원시 구성요소만 재추가할 수 있다. 코드명·상수·완전 중복처럼 `remove`인 변수는 되살리지 않는다.
- 여러 원시 변수군을 자동 누적하지 않으며 Feature-set ID와 정확한 열 목록을 남긴다.

실제 생성된 Feature-set은 공통 197개, 선형용 공통+log1p 207개, 트리용 매출금액 220개, 거래건수 220개, 유동인구 218개, 상주인구 217개, 직장인구 217개의 7종이다. 실행 조합은 Dummy 1개 + Logistic 3개 + 트리 5종×6개로 Fold당 총 34개다. 정확한 열 목록과 해시는 `reports/stage5/feature_sets.json`에 저장한다.

### 4. 비교와 의사결정 조건

- 공통 기준선 전체 모델 비교 후 트리 원시 변수군 Ablation을 수행하고, 적격 변형을 포함해 상위 3개 튜닝 후보를 정한다.
- 평균 AUPRC, 평균 AUROC, 최악 Fold AUPRC, Fold 표준편차, Brier Score, Log Loss, 학습·추론 시간을 고정 관찰 항목으로 함께 본다.
- 사전 숫자 허용오차로 원시 변수군을 자동 유지·탈락시키지 않는다. 계획된 모든 독립 Ablation을 실행해 공통 기준선 대비 차이를 공개한 뒤 사용자와 종합 판단한다.
- 결과 공개 전 자동 순위나 상위 3개를 확정하지 않으며, 기존 불완전 체크포인트는 재사용하지 않는다.

## 검토했던 다른 안

- A 구조 중복 축소형: D안의 공통 기준선으로 채택했다.
- B 보수형: 원값과 파생값을 모두 유지하는 안으로, 메모리·공선성 부담 때문에 단독 채택하지 않았다.
- C 모델군 분리형: 모델마다 처음부터 다른 Feature를 쓰는 안으로, 공통 기준 비교가 약해 단독 채택하지 않았다.

## D안 공통 기준선 규모

- 원본 Feature: 199개
- 유지 제안: 83개
- 제거·치환 제안: 116개
- 파생 생성 후보: 134개, 상수 제외 후 추가 제안: 127개(그중 선형 전용 log1p 10개)
- 발견 구간 절대 Pearson 0.98 이상 쌍: 189개 — 자동 제거하지 않고 관계표에 보존
- 구조 제거 후 상관행렬 조건수: 5.8495e+17 — 선형 모델군에서는 비정규화 Logistic을 제외하고 L1/L2/Elastic-Net Logistic을 비교하며, 트리 모델군은 모두 유지
- 아래 표의 `replace`는 공통 기준선에서 구성비로 치환한다는 뜻이며, D안의 트리 원시 변수군 Ablation 후보가 될 수 있다.

## Feature별 제안

| Feature | 출처 | 제안 | 모델 범위 | 근거 |
| --- | --- | --- | --- | --- |
| 기준_연도 | original | keep | common | 원천 수준/추세/가용성 정보 유지 |
| 기준_분기 | original | keep | common | 원천 수준/추세/가용성 정보 유지 |
| 기준_년분기_코드 | original | remove | all | 기준 연도와 분기로 완전히 복원 가능 |
| 상권_구분_코드 | original | keep | common | 원천 수준/추세/가용성 정보 유지 |
| 상권_구분_코드_명 | original | remove | all | 코드와 중복되는 이름/공간 조인 중복 |
| 상권_코드 | original | keep | common | 원천 수준/추세/가용성 정보 유지 |
| 상권_코드_명 | original | remove | all | 코드와 중복되는 이름/공간 조인 중복 |
| 서비스_업종_코드 | original | keep | common | 원천 수준/추세/가용성 정보 유지 |
| 서비스_업종_코드_명 | original | remove | all | 코드와 중복되는 이름/공간 조인 중복 |
| 당월_매출_금액 | original | keep | common | 원천 수준/추세/가용성 정보 유지 |
| 당월_매출_건수 | original | keep | common | 원천 수준/추세/가용성 정보 유지 |
| 주중_매출_금액 | original | replace | all | 원시 구성요소를 총계+구성비로 치환해 산술 중복 축소 |
| 주말_매출_금액 | original | replace | all | 원시 구성요소를 총계+구성비로 치환해 산술 중복 축소 |
| 월요일_매출_금액 | original | replace | all | 원시 구성요소를 총계+구성비로 치환해 산술 중복 축소 |
| 화요일_매출_금액 | original | replace | all | 원시 구성요소를 총계+구성비로 치환해 산술 중복 축소 |
| 수요일_매출_금액 | original | replace | all | 원시 구성요소를 총계+구성비로 치환해 산술 중복 축소 |
| 목요일_매출_금액 | original | replace | all | 원시 구성요소를 총계+구성비로 치환해 산술 중복 축소 |
| 금요일_매출_금액 | original | replace | all | 원시 구성요소를 총계+구성비로 치환해 산술 중복 축소 |
| 토요일_매출_금액 | original | replace | all | 원시 구성요소를 총계+구성비로 치환해 산술 중복 축소 |
| 일요일_매출_금액 | original | replace | all | 원시 구성요소를 총계+구성비로 치환해 산술 중복 축소 |
| 시간대_00~06_매출_금액 | original | replace | all | 원시 구성요소를 총계+구성비로 치환해 산술 중복 축소 |
| 시간대_06~11_매출_금액 | original | replace | all | 원시 구성요소를 총계+구성비로 치환해 산술 중복 축소 |
| 시간대_11~14_매출_금액 | original | replace | all | 원시 구성요소를 총계+구성비로 치환해 산술 중복 축소 |
| 시간대_14~17_매출_금액 | original | replace | all | 원시 구성요소를 총계+구성비로 치환해 산술 중복 축소 |
| 시간대_17~21_매출_금액 | original | replace | all | 원시 구성요소를 총계+구성비로 치환해 산술 중복 축소 |
| 시간대_21~24_매출_금액 | original | replace | all | 원시 구성요소를 총계+구성비로 치환해 산술 중복 축소 |
| 남성_매출_금액 | original | replace | all | 원시 구성요소를 총계+구성비로 치환해 산술 중복 축소 |
| 여성_매출_금액 | original | replace | all | 원시 구성요소를 총계+구성비로 치환해 산술 중복 축소 |
| 연령대_10_매출_금액 | original | replace | all | 원시 구성요소를 총계+구성비로 치환해 산술 중복 축소 |
| 연령대_20_매출_금액 | original | replace | all | 원시 구성요소를 총계+구성비로 치환해 산술 중복 축소 |
| 연령대_30_매출_금액 | original | replace | all | 원시 구성요소를 총계+구성비로 치환해 산술 중복 축소 |
| 연령대_40_매출_금액 | original | replace | all | 원시 구성요소를 총계+구성비로 치환해 산술 중복 축소 |
| 연령대_50_매출_금액 | original | replace | all | 원시 구성요소를 총계+구성비로 치환해 산술 중복 축소 |
| 연령대_60_이상_매출_금액 | original | replace | all | 원시 구성요소를 총계+구성비로 치환해 산술 중복 축소 |
| 주중_매출_건수 | original | replace | all | 원시 구성요소를 총계+구성비로 치환해 산술 중복 축소 |
| 주말_매출_건수 | original | replace | all | 원시 구성요소를 총계+구성비로 치환해 산술 중복 축소 |
| 월요일_매출_건수 | original | replace | all | 원시 구성요소를 총계+구성비로 치환해 산술 중복 축소 |
| 화요일_매출_건수 | original | replace | all | 원시 구성요소를 총계+구성비로 치환해 산술 중복 축소 |
| 수요일_매출_건수 | original | replace | all | 원시 구성요소를 총계+구성비로 치환해 산술 중복 축소 |
| 목요일_매출_건수 | original | replace | all | 원시 구성요소를 총계+구성비로 치환해 산술 중복 축소 |
| 금요일_매출_건수 | original | replace | all | 원시 구성요소를 총계+구성비로 치환해 산술 중복 축소 |
| 토요일_매출_건수 | original | replace | all | 원시 구성요소를 총계+구성비로 치환해 산술 중복 축소 |
| 일요일_매출_건수 | original | replace | all | 원시 구성요소를 총계+구성비로 치환해 산술 중복 축소 |
| 시간대_건수~06_매출_건수 | original | replace | all | 원시 구성요소를 총계+구성비로 치환해 산술 중복 축소 |
| 시간대_건수~11_매출_건수 | original | replace | all | 원시 구성요소를 총계+구성비로 치환해 산술 중복 축소 |
| 시간대_건수~14_매출_건수 | original | replace | all | 원시 구성요소를 총계+구성비로 치환해 산술 중복 축소 |
| 시간대_건수~17_매출_건수 | original | replace | all | 원시 구성요소를 총계+구성비로 치환해 산술 중복 축소 |
| 시간대_건수~21_매출_건수 | original | replace | all | 원시 구성요소를 총계+구성비로 치환해 산술 중복 축소 |
| 시간대_건수~24_매출_건수 | original | replace | all | 원시 구성요소를 총계+구성비로 치환해 산술 중복 축소 |
| 남성_매출_건수 | original | replace | all | 원시 구성요소를 총계+구성비로 치환해 산술 중복 축소 |
| 여성_매출_건수 | original | replace | all | 원시 구성요소를 총계+구성비로 치환해 산술 중복 축소 |
| 연령대_10_매출_건수 | original | replace | all | 원시 구성요소를 총계+구성비로 치환해 산술 중복 축소 |
| 연령대_20_매출_건수 | original | replace | all | 원시 구성요소를 총계+구성비로 치환해 산술 중복 축소 |
| 연령대_30_매출_건수 | original | replace | all | 원시 구성요소를 총계+구성비로 치환해 산술 중복 축소 |
| 연령대_40_매출_건수 | original | replace | all | 원시 구성요소를 총계+구성비로 치환해 산술 중복 축소 |
| 연령대_50_매출_건수 | original | replace | all | 원시 구성요소를 총계+구성비로 치환해 산술 중복 축소 |
| 연령대_60_이상_매출_건수 | original | replace | all | 원시 구성요소를 총계+구성비로 치환해 산술 중복 축소 |
| 점포_수 | original | keep | common | 원천 수준/추세/가용성 정보 유지 |
| 유사_업종_점포_수 | original | keep | common | 원천 수준/추세/가용성 정보 유지 |
| 개업_율 | original | keep | common | 원천 수준/추세/가용성 정보 유지 |
| 개업_점포_수 | original | keep | common | 원천 수준/추세/가용성 정보 유지 |
| 폐업_률 | original | keep | common | 원천 수준/추세/가용성 정보 유지 |
| 폐업_점포_수 | original | keep | common | 원천 수준/추세/가용성 정보 유지 |
| 프랜차이즈_점포_수 | original | keep | common | 원천 수준/추세/가용성 정보 유지 |
| 점포_결합_여부 | original | remove | all | 발견 구간 상수 |
| 전분기_연속_여부 | original | keep | common | 원천 수준/추세/가용성 정보 유지 |
| 최근_4분기_연속_여부 | original | keep | common | 원천 수준/추세/가용성 정보 유지 |
| 전분기_매출_증감률 | original | keep | common | 원천 수준/추세/가용성 정보 유지 |
| 전년동기_매출_증감률 | original | keep | common | 원천 수준/추세/가용성 정보 유지 |
| 최근_2분기_매출_변화액 | original | keep | common | 원천 수준/추세/가용성 정보 유지 |
| 최근_4분기_매출_선형기울기 | original | keep | common | 원천 수준/추세/가용성 정보 유지 |
| 주말_매출_비중 | original | keep | common | 원천 수준/추세/가용성 정보 유지 |
| 점포_증감률 | original | keep | common | 원천 수준/추세/가용성 정보 유지 |
| 프랜차이즈_점포_비율 | original | keep | common | 원천 수준/추세/가용성 정보 유지 |
| 유동__총_유동인구_수 | original | keep | auxiliary_ablation | 원천 수준/추세/가용성 정보 유지 |
| 유동__남성_유동인구_수 | original | replace | all | 원시 구성요소를 총계+구성비로 치환해 산술 중복 축소 |
| 유동__여성_유동인구_수 | original | replace | all | 원시 구성요소를 총계+구성비로 치환해 산술 중복 축소 |
| 유동__연령대_10_유동인구_수 | original | replace | all | 원시 구성요소를 총계+구성비로 치환해 산술 중복 축소 |
| 유동__연령대_20_유동인구_수 | original | replace | all | 원시 구성요소를 총계+구성비로 치환해 산술 중복 축소 |
| 유동__연령대_30_유동인구_수 | original | replace | all | 원시 구성요소를 총계+구성비로 치환해 산술 중복 축소 |
| 유동__연령대_40_유동인구_수 | original | replace | all | 원시 구성요소를 총계+구성비로 치환해 산술 중복 축소 |
| 유동__연령대_50_유동인구_수 | original | replace | all | 원시 구성요소를 총계+구성비로 치환해 산술 중복 축소 |
| 유동__연령대_60_이상_유동인구_수 | original | replace | all | 원시 구성요소를 총계+구성비로 치환해 산술 중복 축소 |
| 유동__시간대_00_06_유동인구_수 | original | replace | all | 원시 구성요소를 총계+구성비로 치환해 산술 중복 축소 |
| 유동__시간대_06_11_유동인구_수 | original | replace | all | 원시 구성요소를 총계+구성비로 치환해 산술 중복 축소 |
| 유동__시간대_11_14_유동인구_수 | original | replace | all | 원시 구성요소를 총계+구성비로 치환해 산술 중복 축소 |
| 유동__시간대_14_17_유동인구_수 | original | replace | all | 원시 구성요소를 총계+구성비로 치환해 산술 중복 축소 |
| 유동__시간대_17_21_유동인구_수 | original | replace | all | 원시 구성요소를 총계+구성비로 치환해 산술 중복 축소 |
| 유동__시간대_21_24_유동인구_수 | original | replace | all | 원시 구성요소를 총계+구성비로 치환해 산술 중복 축소 |
| 유동__월요일_유동인구_수 | original | replace | all | 원시 구성요소를 총계+구성비로 치환해 산술 중복 축소 |
| 유동__화요일_유동인구_수 | original | replace | all | 원시 구성요소를 총계+구성비로 치환해 산술 중복 축소 |
| 유동__수요일_유동인구_수 | original | replace | all | 원시 구성요소를 총계+구성비로 치환해 산술 중복 축소 |
| 유동__목요일_유동인구_수 | original | replace | all | 원시 구성요소를 총계+구성비로 치환해 산술 중복 축소 |
| 유동__금요일_유동인구_수 | original | replace | all | 원시 구성요소를 총계+구성비로 치환해 산술 중복 축소 |
| 유동__토요일_유동인구_수 | original | replace | all | 원시 구성요소를 총계+구성비로 치환해 산술 중복 축소 |
| 유동__일요일_유동인구_수 | original | replace | all | 원시 구성요소를 총계+구성비로 치환해 산술 중복 축소 |
| 유동__결합_여부 | original | keep | auxiliary_ablation | 원천 수준/추세/가용성 정보 유지 |
| 변화__상권_변화_지표 | original | keep | common | 원천 수준/추세/가용성 정보 유지 |
| 변화__상권_변화_지표_명 | original | remove | all | 코드와 중복되는 이름/공간 조인 중복 |
| 변화__운영_영업_개월_평균 | original | keep | common | 원천 수준/추세/가용성 정보 유지 |
| 변화__폐업_영업_개월_평균 | original | keep | common | 원천 수준/추세/가용성 정보 유지 |
| 변화__서울_운영_영업_개월_평균 | original | keep | common | 원천 수준/추세/가용성 정보 유지 |
| 변화__서울_폐업_영업_개월_평균 | original | keep | common | 원천 수준/추세/가용성 정보 유지 |
| 변화__결합_여부 | original | remove | all | 발견 구간 상수 |
| 상주__총_상주인구_수 | original | keep | auxiliary_ablation | 원천 수준/추세/가용성 정보 유지 |
| 상주__남성_상주인구_수 | original | replace | all | 원시 구성요소를 총계+구성비로 치환해 산술 중복 축소 |
| 상주__여성_상주인구_수 | original | replace | all | 원시 구성요소를 총계+구성비로 치환해 산술 중복 축소 |
| 상주__연령대_10_상주인구_수 | original | replace | all | 원시 구성요소를 총계+구성비로 치환해 산술 중복 축소 |
| 상주__연령대_20_상주인구_수 | original | replace | all | 원시 구성요소를 총계+구성비로 치환해 산술 중복 축소 |
| 상주__연령대_30_상주인구_수 | original | replace | all | 원시 구성요소를 총계+구성비로 치환해 산술 중복 축소 |
| 상주__연령대_40_상주인구_수 | original | replace | all | 원시 구성요소를 총계+구성비로 치환해 산술 중복 축소 |
| 상주__연령대_50_상주인구_수 | original | replace | all | 원시 구성요소를 총계+구성비로 치환해 산술 중복 축소 |
| 상주__연령대_60_이상_상주인구_수 | original | replace | all | 원시 구성요소를 총계+구성비로 치환해 산술 중복 축소 |
| 상주__남성연령대_10_상주인구_수 | original | replace | all | 원시 구성요소를 총계+구성비로 치환해 산술 중복 축소 |
| 상주__남성연령대_20_상주인구_수 | original | replace | all | 원시 구성요소를 총계+구성비로 치환해 산술 중복 축소 |
| 상주__남성연령대_30_상주인구_수 | original | replace | all | 원시 구성요소를 총계+구성비로 치환해 산술 중복 축소 |
| 상주__남성연령대_40_상주인구_수 | original | replace | all | 원시 구성요소를 총계+구성비로 치환해 산술 중복 축소 |
| 상주__남성연령대_50_상주인구_수 | original | replace | all | 원시 구성요소를 총계+구성비로 치환해 산술 중복 축소 |
| 상주__남성연령대_60_이상_상주인구_수 | original | replace | all | 원시 구성요소를 총계+구성비로 치환해 산술 중복 축소 |
| 상주__여성연령대_10_상주인구_수 | original | replace | all | 원시 구성요소를 총계+구성비로 치환해 산술 중복 축소 |
| 상주__여성연령대_20_상주인구_수 | original | replace | all | 원시 구성요소를 총계+구성비로 치환해 산술 중복 축소 |
| 상주__여성연령대_30_상주인구_수 | original | replace | all | 원시 구성요소를 총계+구성비로 치환해 산술 중복 축소 |
| 상주__여성연령대_40_상주인구_수 | original | replace | all | 원시 구성요소를 총계+구성비로 치환해 산술 중복 축소 |
| 상주__여성연령대_50_상주인구_수 | original | replace | all | 원시 구성요소를 총계+구성비로 치환해 산술 중복 축소 |
| 상주__여성연령대_60_이상_상주인구_수 | original | replace | all | 원시 구성요소를 총계+구성비로 치환해 산술 중복 축소 |
| 상주__총_가구_수 | original | keep | auxiliary_ablation | 원천 수준/추세/가용성 정보 유지 |
| 상주__아파트_가구_수 | original | keep | auxiliary_ablation | 원천 수준/추세/가용성 정보 유지 |
| 상주__비_아파트_가구_수 | original | keep | auxiliary_ablation | 원천 수준/추세/가용성 정보 유지 |
| 상주__결합_여부 | original | keep | auxiliary_ablation | 원천 수준/추세/가용성 정보 유지 |
| 직장__총_직장_인구_수 | original | keep | auxiliary_ablation | 원천 수준/추세/가용성 정보 유지 |
| 직장__남성_직장_인구_수 | original | replace | all | 원시 구성요소를 총계+구성비로 치환해 산술 중복 축소 |
| 직장__여성_직장_인구_수 | original | replace | all | 원시 구성요소를 총계+구성비로 치환해 산술 중복 축소 |
| 직장__연령대_10_직장_인구_수 | original | replace | all | 원시 구성요소를 총계+구성비로 치환해 산술 중복 축소 |
| 직장__연령대_20_직장_인구_수 | original | replace | all | 원시 구성요소를 총계+구성비로 치환해 산술 중복 축소 |
| 직장__연령대_30_직장_인구_수 | original | replace | all | 원시 구성요소를 총계+구성비로 치환해 산술 중복 축소 |
| 직장__연령대_40_직장_인구_수 | original | replace | all | 원시 구성요소를 총계+구성비로 치환해 산술 중복 축소 |
| 직장__연령대_50_직장_인구_수 | original | replace | all | 원시 구성요소를 총계+구성비로 치환해 산술 중복 축소 |
| 직장__연령대_60_이상_직장_인구_수 | original | replace | all | 원시 구성요소를 총계+구성비로 치환해 산술 중복 축소 |
| 직장__남성연령대_10_직장_인구_수 | original | replace | all | 원시 구성요소를 총계+구성비로 치환해 산술 중복 축소 |
| 직장__남성연령대_20_직장_인구_수 | original | replace | all | 원시 구성요소를 총계+구성비로 치환해 산술 중복 축소 |
| 직장__남성연령대_30_직장_인구_수 | original | replace | all | 원시 구성요소를 총계+구성비로 치환해 산술 중복 축소 |
| 직장__남성연령대_40_직장_인구_수 | original | replace | all | 원시 구성요소를 총계+구성비로 치환해 산술 중복 축소 |
| 직장__남성연령대_50_직장_인구_수 | original | replace | all | 원시 구성요소를 총계+구성비로 치환해 산술 중복 축소 |
| 직장__남성연령대_60_이상_직장_인구_수 | original | replace | all | 원시 구성요소를 총계+구성비로 치환해 산술 중복 축소 |
| 직장__여성연령대_10_직장_인구_수 | original | replace | all | 원시 구성요소를 총계+구성비로 치환해 산술 중복 축소 |
| 직장__여성연령대_20_직장_인구_수 | original | replace | all | 원시 구성요소를 총계+구성비로 치환해 산술 중복 축소 |
| 직장__여성연령대_30_직장_인구_수 | original | replace | all | 원시 구성요소를 총계+구성비로 치환해 산술 중복 축소 |
| 직장__여성연령대_40_직장_인구_수 | original | replace | all | 원시 구성요소를 총계+구성비로 치환해 산술 중복 축소 |
| 직장__여성연령대_50_직장_인구_수 | original | replace | all | 원시 구성요소를 총계+구성비로 치환해 산술 중복 축소 |
| 직장__여성연령대_60_이상_직장_인구_수 | original | replace | all | 원시 구성요소를 총계+구성비로 치환해 산술 중복 축소 |
| 직장__결합_여부 | original | keep | auxiliary_ablation | 원천 수준/추세/가용성 정보 유지 |
| 시설__집객시설_수 | original | keep | auxiliary_ablation | 원천 수준/추세/가용성 정보 유지 |
| 시설__관공서_수 | original | keep | auxiliary_ablation | 원천 수준/추세/가용성 정보 유지 |
| 시설__은행_수 | original | keep | auxiliary_ablation | 원천 수준/추세/가용성 정보 유지 |
| 시설__종합병원_수 | original | keep | auxiliary_ablation | 원천 수준/추세/가용성 정보 유지 |
| 시설__일반_병원_수 | original | keep | auxiliary_ablation | 원천 수준/추세/가용성 정보 유지 |
| 시설__약국_수 | original | keep | auxiliary_ablation | 원천 수준/추세/가용성 정보 유지 |
| 시설__유치원_수 | original | keep | auxiliary_ablation | 원천 수준/추세/가용성 정보 유지 |
| 시설__초등학교_수 | original | keep | auxiliary_ablation | 원천 수준/추세/가용성 정보 유지 |
| 시설__중학교_수 | original | keep | auxiliary_ablation | 원천 수준/추세/가용성 정보 유지 |
| 시설__고등학교_수 | original | keep | auxiliary_ablation | 원천 수준/추세/가용성 정보 유지 |
| 시설__대학교_수 | original | keep | auxiliary_ablation | 원천 수준/추세/가용성 정보 유지 |
| 시설__백화점_수 | original | keep | auxiliary_ablation | 원천 수준/추세/가용성 정보 유지 |
| 시설__슈퍼마켓_수 | original | keep | auxiliary_ablation | 원천 수준/추세/가용성 정보 유지 |
| 시설__극장_수 | original | keep | auxiliary_ablation | 원천 수준/추세/가용성 정보 유지 |
| 시설__숙박_시설_수 | original | keep | auxiliary_ablation | 원천 수준/추세/가용성 정보 유지 |
| 시설__공항_수 | original | keep | auxiliary_ablation | 원천 수준/추세/가용성 정보 유지 |
| 시설__철도_역_수 | original | remove | all | 발견 구간 상수 |
| 시설__버스_터미널_수 | original | keep | auxiliary_ablation | 원천 수준/추세/가용성 정보 유지 |
| 시설__지하철_역_수 | original | keep | auxiliary_ablation | 원천 수준/추세/가용성 정보 유지 |
| 시설__버스_정거장_수 | original | keep | auxiliary_ablation | 원천 수준/추세/가용성 정보 유지 |
| 시설__결합_여부 | original | keep | auxiliary_ablation | 원천 수준/추세/가용성 정보 유지 |
| 아파트__아파트_단지_수 | original | keep | auxiliary_ablation | 원천 수준/추세/가용성 정보 유지 |
| 아파트__아파트_면적_66_제곱미터_미만_세대_수 | original | keep | auxiliary_ablation | 원천 수준/추세/가용성 정보 유지 |
| 아파트__아파트_면적_66_제곱미터_세대_수 | original | keep | auxiliary_ablation | 원천 수준/추세/가용성 정보 유지 |
| 아파트__아파트_면적_99_제곱미터_세대_수 | original | keep | auxiliary_ablation | 원천 수준/추세/가용성 정보 유지 |
| 아파트__아파트_면적_132_제곱미터_세대_수 | original | keep | auxiliary_ablation | 원천 수준/추세/가용성 정보 유지 |
| 아파트__아파트_면적_165_제곱미터_세대_수 | original | keep | auxiliary_ablation | 원천 수준/추세/가용성 정보 유지 |
| 아파트__아파트_가격_1_억_미만_세대_수 | original | keep | auxiliary_ablation | 원천 수준/추세/가용성 정보 유지 |
| 아파트__아파트_가격_1_억_세대_수 | original | keep | auxiliary_ablation | 원천 수준/추세/가용성 정보 유지 |
| 아파트__아파트_가격_2_억_세대_수 | original | keep | auxiliary_ablation | 원천 수준/추세/가용성 정보 유지 |
| 아파트__아파트_가격_3_억_세대_수 | original | keep | auxiliary_ablation | 원천 수준/추세/가용성 정보 유지 |
| 아파트__아파트_가격_4_억_세대_수 | original | keep | auxiliary_ablation | 원천 수준/추세/가용성 정보 유지 |
| 아파트__아파트_가격_5_억_세대_수 | original | keep | auxiliary_ablation | 원천 수준/추세/가용성 정보 유지 |
| 아파트__아파트_가격_6_억_이상_세대_수 | original | keep | auxiliary_ablation | 원천 수준/추세/가용성 정보 유지 |
| 아파트__아파트_평균_면적 | original | keep | auxiliary_ablation | 원천 수준/추세/가용성 정보 유지 |
| 아파트__아파트_평균_시가 | original | keep | auxiliary_ablation | 원천 수준/추세/가용성 정보 유지 |
| 아파트__결합_여부 | original | keep | auxiliary_ablation | 원천 수준/추세/가용성 정보 유지 |
| 공간__상권_구분_코드 | original | remove | all | 코드와 중복되는 이름/공간 조인 중복 |
| 공간__상권_구분_코드_명 | original | remove | all | 코드와 중복되는 이름/공간 조인 중복 |
| 공간__상권_코드_명 | original | remove | all | 코드와 중복되는 이름/공간 조인 중복 |
| 공간__중심_X | original | keep | auxiliary_ablation | 원천 수준/추세/가용성 정보 유지 |
| 공간__중심_Y | original | keep | auxiliary_ablation | 원천 수준/추세/가용성 정보 유지 |
| 공간__자치구_코드 | original | keep | auxiliary_ablation | 원천 수준/추세/가용성 정보 유지 |
| 공간__자치구_명 | original | keep | auxiliary_ablation | 원천 수준/추세/가용성 정보 유지 |
| 공간__행정동_코드 | original | keep | auxiliary_ablation | 원천 수준/추세/가용성 정보 유지 |
| 공간__행정동_명 | original | keep | auxiliary_ablation | 원천 수준/추세/가용성 정보 유지 |
| 공간__면적 | original | keep | auxiliary_ablation | 원천 수준/추세/가용성 정보 유지 |
| 공간__결합_여부 | original | remove | all | 발견 구간 상수 |
| 당월_매출_건수__분모0 | derived | remove | all | 발견 구간 상수 |
| 평균_객단가 | derived | add | common | Stage 4.5 unit_economics 후보 |
| 점포_수__분모0 | derived | add | common | Stage 4.5 denominator_flag 후보 |
| 점포당_매출 | derived | add | common | Stage 4.5 unit_economics 후보 |
| 점포당_거래건수 | derived | add | common | Stage 4.5 unit_economics 후보 |
| 유사_업종_점포_수__분모0 | derived | remove | all | 발견 구간 상수 |
| 개업_강도 | derived | add | common | Stage 4.5 store_dynamics 후보 |
| 폐업_강도 | derived | add | common | Stage 4.5 store_dynamics 후보 |
| 당월_매출_금액__분모0 | derived | remove | all | 발견 구간 상수 |
| 구성비__주중_매출_금액 | derived | add | common | Stage 4.5 sales_composition 후보 |
| 구성비__월요일_매출_금액 | derived | add | common | Stage 4.5 sales_composition 후보 |
| 구성비__화요일_매출_금액 | derived | add | common | Stage 4.5 sales_composition 후보 |
| 구성비__수요일_매출_금액 | derived | add | common | Stage 4.5 sales_composition 후보 |
| 구성비__목요일_매출_금액 | derived | add | common | Stage 4.5 sales_composition 후보 |
| 구성비__금요일_매출_금액 | derived | add | common | Stage 4.5 sales_composition 후보 |
| 구성비__토요일_매출_금액 | derived | add | common | Stage 4.5 sales_composition 후보 |
| 구성비__일요일_매출_금액 | derived | add | common | Stage 4.5 sales_composition 후보 |
| 구성비__시간대_00~06_매출_금액 | derived | add | common | Stage 4.5 sales_composition 후보 |
| 구성비__시간대_06~11_매출_금액 | derived | add | common | Stage 4.5 sales_composition 후보 |
| 구성비__시간대_11~14_매출_금액 | derived | add | common | Stage 4.5 sales_composition 후보 |
| 구성비__시간대_14~17_매출_금액 | derived | add | common | Stage 4.5 sales_composition 후보 |
| 구성비__시간대_17~21_매출_금액 | derived | add | common | Stage 4.5 sales_composition 후보 |
| 구성비__시간대_21~24_매출_금액 | derived | add | common | Stage 4.5 sales_composition 후보 |
| 구성비__남성_매출_금액 | derived | add | common | Stage 4.5 sales_composition 후보 |
| 구성비__여성_매출_금액 | derived | add | common | Stage 4.5 sales_composition 후보 |
| 구성비__연령대_10_매출_금액 | derived | add | common | Stage 4.5 sales_composition 후보 |
| 구성비__연령대_20_매출_금액 | derived | add | common | Stage 4.5 sales_composition 후보 |
| 구성비__연령대_30_매출_금액 | derived | add | common | Stage 4.5 sales_composition 후보 |
| 구성비__연령대_40_매출_금액 | derived | add | common | Stage 4.5 sales_composition 후보 |
| 구성비__연령대_50_매출_금액 | derived | add | common | Stage 4.5 sales_composition 후보 |
| 구성비__연령대_60_이상_매출_금액 | derived | add | common | Stage 4.5 sales_composition 후보 |
| 구성비__주중_매출_건수 | derived | add | common | Stage 4.5 transaction_composition 후보 |
| 구성비__주말_매출_건수 | derived | add | common | Stage 4.5 transaction_composition 후보 |
| 구성비__월요일_매출_건수 | derived | add | common | Stage 4.5 transaction_composition 후보 |
| 구성비__화요일_매출_건수 | derived | add | common | Stage 4.5 transaction_composition 후보 |
| 구성비__수요일_매출_건수 | derived | add | common | Stage 4.5 transaction_composition 후보 |
| 구성비__목요일_매출_건수 | derived | add | common | Stage 4.5 transaction_composition 후보 |
| 구성비__금요일_매출_건수 | derived | add | common | Stage 4.5 transaction_composition 후보 |
| 구성비__토요일_매출_건수 | derived | add | common | Stage 4.5 transaction_composition 후보 |
| 구성비__일요일_매출_건수 | derived | add | common | Stage 4.5 transaction_composition 후보 |
| 구성비__시간대_건수~06_매출_건수 | derived | add | common | Stage 4.5 transaction_composition 후보 |
| 구성비__시간대_건수~11_매출_건수 | derived | add | common | Stage 4.5 transaction_composition 후보 |
| 구성비__시간대_건수~14_매출_건수 | derived | add | common | Stage 4.5 transaction_composition 후보 |
| 구성비__시간대_건수~17_매출_건수 | derived | add | common | Stage 4.5 transaction_composition 후보 |
| 구성비__시간대_건수~21_매출_건수 | derived | add | common | Stage 4.5 transaction_composition 후보 |
| 구성비__시간대_건수~24_매출_건수 | derived | add | common | Stage 4.5 transaction_composition 후보 |
| 구성비__남성_매출_건수 | derived | add | common | Stage 4.5 transaction_composition 후보 |
| 구성비__여성_매출_건수 | derived | add | common | Stage 4.5 transaction_composition 후보 |
| 구성비__연령대_10_매출_건수 | derived | add | common | Stage 4.5 transaction_composition 후보 |
| 구성비__연령대_20_매출_건수 | derived | add | common | Stage 4.5 transaction_composition 후보 |
| 구성비__연령대_30_매출_건수 | derived | add | common | Stage 4.5 transaction_composition 후보 |
| 구성비__연령대_40_매출_건수 | derived | add | common | Stage 4.5 transaction_composition 후보 |
| 구성비__연령대_50_매출_건수 | derived | add | common | Stage 4.5 transaction_composition 후보 |
| 구성비__연령대_60_이상_매출_건수 | derived | add | common | Stage 4.5 transaction_composition 후보 |
| 유동__총_유동인구_수__분모0 | derived | remove | all | 발견 구간 상수 |
| 구성비__유동__남성_유동인구_수 | derived | add | common | Stage 4.5 유동_population_composition 후보 |
| 구성비__유동__여성_유동인구_수 | derived | add | common | Stage 4.5 유동_population_composition 후보 |
| 구성비__유동__연령대_10_유동인구_수 | derived | add | common | Stage 4.5 유동_population_composition 후보 |
| 구성비__유동__연령대_20_유동인구_수 | derived | add | common | Stage 4.5 유동_population_composition 후보 |
| 구성비__유동__연령대_30_유동인구_수 | derived | add | common | Stage 4.5 유동_population_composition 후보 |
| 구성비__유동__연령대_40_유동인구_수 | derived | add | common | Stage 4.5 유동_population_composition 후보 |
| 구성비__유동__연령대_50_유동인구_수 | derived | add | common | Stage 4.5 유동_population_composition 후보 |
| 구성비__유동__연령대_60_이상_유동인구_수 | derived | add | common | Stage 4.5 유동_population_composition 후보 |
| 구성비__유동__시간대_00_06_유동인구_수 | derived | add | common | Stage 4.5 유동_population_composition 후보 |
| 구성비__유동__시간대_06_11_유동인구_수 | derived | add | common | Stage 4.5 유동_population_composition 후보 |
| 구성비__유동__시간대_11_14_유동인구_수 | derived | add | common | Stage 4.5 유동_population_composition 후보 |
| 구성비__유동__시간대_14_17_유동인구_수 | derived | add | common | Stage 4.5 유동_population_composition 후보 |
| 구성비__유동__시간대_17_21_유동인구_수 | derived | add | common | Stage 4.5 유동_population_composition 후보 |
| 구성비__유동__시간대_21_24_유동인구_수 | derived | add | common | Stage 4.5 유동_population_composition 후보 |
| 구성비__유동__월요일_유동인구_수 | derived | add | common | Stage 4.5 유동_population_composition 후보 |
| 구성비__유동__화요일_유동인구_수 | derived | add | common | Stage 4.5 유동_population_composition 후보 |
| 구성비__유동__수요일_유동인구_수 | derived | add | common | Stage 4.5 유동_population_composition 후보 |
| 구성비__유동__목요일_유동인구_수 | derived | add | common | Stage 4.5 유동_population_composition 후보 |
| 구성비__유동__금요일_유동인구_수 | derived | add | common | Stage 4.5 유동_population_composition 후보 |
| 구성비__유동__토요일_유동인구_수 | derived | add | common | Stage 4.5 유동_population_composition 후보 |
| 구성비__유동__일요일_유동인구_수 | derived | add | common | Stage 4.5 유동_population_composition 후보 |
| 상주__총_상주인구_수__분모0 | derived | remove | all | 발견 구간 상수 |
| 구성비__상주__남성_상주인구_수 | derived | add | common | Stage 4.5 상주_population_composition 후보 |
| 구성비__상주__여성_상주인구_수 | derived | add | common | Stage 4.5 상주_population_composition 후보 |
| 구성비__상주__연령대_10_상주인구_수 | derived | add | common | Stage 4.5 상주_population_composition 후보 |
| 구성비__상주__연령대_20_상주인구_수 | derived | add | common | Stage 4.5 상주_population_composition 후보 |
| 구성비__상주__연령대_30_상주인구_수 | derived | add | common | Stage 4.5 상주_population_composition 후보 |
| 구성비__상주__연령대_40_상주인구_수 | derived | add | common | Stage 4.5 상주_population_composition 후보 |
| 구성비__상주__연령대_50_상주인구_수 | derived | add | common | Stage 4.5 상주_population_composition 후보 |
| 구성비__상주__연령대_60_이상_상주인구_수 | derived | add | common | Stage 4.5 상주_population_composition 후보 |
| 직장__총_직장_인구_수__분모0 | derived | remove | all | 발견 구간 상수 |
| 구성비__직장__남성_직장_인구_수 | derived | add | common | Stage 4.5 직장_population_composition 후보 |
| 구성비__직장__여성_직장_인구_수 | derived | add | common | Stage 4.5 직장_population_composition 후보 |
| 구성비__직장__연령대_10_직장_인구_수 | derived | add | common | Stage 4.5 직장_population_composition 후보 |
| 구성비__직장__연령대_20_직장_인구_수 | derived | add | common | Stage 4.5 직장_population_composition 후보 |
| 구성비__직장__연령대_30_직장_인구_수 | derived | add | common | Stage 4.5 직장_population_composition 후보 |
| 구성비__직장__연령대_40_직장_인구_수 | derived | add | common | Stage 4.5 직장_population_composition 후보 |
| 구성비__직장__연령대_50_직장_인구_수 | derived | add | common | Stage 4.5 직장_population_composition 후보 |
| 구성비__직장__연령대_60_이상_직장_인구_수 | derived | add | common | Stage 4.5 직장_population_composition 후보 |
| 유동인구_대비_상주인구_비율 | derived | add | common | Stage 4.5 population_ratio 후보 |
| 유동인구_대비_직장인구_비율 | derived | add | common | Stage 4.5 population_ratio 후보 |
| 상주인구_대비_직장인구_비율 | derived | add | common | Stage 4.5 population_ratio 후보 |
| 점포당_유동인구 | derived | add | common | Stage 4.5 population_per_store 후보 |
| 공간__면적__분모0 | derived | remove | all | 발견 구간 상수 |
| 면적당_유동인구 | derived | add | common | Stage 4.5 density 후보 |
| 점포당_상주인구 | derived | add | common | Stage 4.5 population_per_store 후보 |
| 면적당_상주인구 | derived | add | common | Stage 4.5 density 후보 |
| 점포당_직장인구 | derived | add | common | Stage 4.5 population_per_store 후보 |
| 면적당_직장인구 | derived | add | common | Stage 4.5 density 후보 |
| 면적당_집객시설 | derived | add | common | Stage 4.5 density 후보 |
| 점포당_집객시설 | derived | add | common | Stage 4.5 density 후보 |
| 면적당_아파트단지 | derived | add | common | Stage 4.5 density 후보 |
| 점포당_아파트단지 | derived | add | common | Stage 4.5 density 후보 |
| 면적당_가구 | derived | add | common | Stage 4.5 density 후보 |
| 점포당_가구 | derived | add | common | Stage 4.5 density 후보 |
| 매출_변화방향_일치 | derived | add | common | Stage 4.5 persistence 후보 |
| 매출_감소_지속 | derived | add | common | Stage 4.5 persistence 후보 |
| 최근_2분기_매출_평균 | derived | add | common | Stage 4.5 rolling_sales 후보 |
| 최근_2분기_매출_표준편차 | derived | add | common | Stage 4.5 rolling_sales 후보 |
| 최근_2분기_매출_최소 | derived | add | common | Stage 4.5 rolling_sales 후보 |
| 최근_2분기_매출_최대 | derived | add | common | Stage 4.5 rolling_sales 후보 |
| 최근_2분기_매출_변동계수 | derived | add | common | Stage 4.5 rolling_sales 후보 |
| 현재값_대비_최근_2분기_매출_평균_차이 | derived | add | common | Stage 4.5 rolling_sales 후보 |
| 최근_4분기_매출_평균 | derived | add | common | Stage 4.5 rolling_sales 후보 |
| 최근_4분기_매출_표준편차 | derived | add | common | Stage 4.5 rolling_sales 후보 |
| 최근_4분기_매출_최소 | derived | add | common | Stage 4.5 rolling_sales 후보 |
| 최근_4분기_매출_최대 | derived | add | common | Stage 4.5 rolling_sales 후보 |
| 최근_4분기_매출_변동계수 | derived | add | common | Stage 4.5 rolling_sales 후보 |
| 현재값_대비_최근_4분기_매출_평균_차이 | derived | add | common | Stage 4.5 rolling_sales 후보 |
| log1p__당월_매출_금액 | derived | add | linear_only | 양수 왜도 완화 |
| log1p__당월_매출_건수 | derived | add | linear_only | 양수 왜도 완화 |
| log1p__점포_수 | derived | add | linear_only | 양수 왜도 완화 |
| log1p__유동__총_유동인구_수 | derived | add | linear_only | 양수 왜도 완화 |
| log1p__상주__총_상주인구_수 | derived | add | linear_only | 양수 왜도 완화 |
| log1p__직장__총_직장_인구_수 | derived | add | linear_only | 양수 왜도 완화 |
| log1p__시설__집객시설_수 | derived | add | linear_only | 양수 왜도 완화 |
| log1p__아파트__아파트_단지_수 | derived | add | linear_only | 양수 왜도 완화 |
| log1p__상주__총_가구_수 | derived | add | linear_only | 양수 왜도 완화 |
| log1p__아파트__아파트_평균_시가 | derived | add | linear_only | 양수 왜도 완화 |

## 승인 후 다음 단계 반영 상태

- `config/stage5.yaml`에 D안, 비교 순서, 트리 원시 변수군 5개와 전체 비교 실행 승인 상태를 기록했다.
- `MVP 단계별 구현 체크리스트.md`의 Stage 5에 공통 기준선과 트리 Ablation 절차를 추가했다.
- Stage 5 로더의 실제 Feature-set 생성·저장 구현은 다음 단계 작업으로 남겼다.
- L1·Elastic-Net 선택과 트리 Importance는 실행 시 각 Fold Train 안에서만 Fit한다.
- 사용자의 2026-08-15 요청에 따라 사전 수치 컷 없이 전체 지표를 본 뒤 종합 판단하는 방식으로 Stage 5 비교를 실행한다.
