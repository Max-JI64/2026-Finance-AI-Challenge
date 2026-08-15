# Stage 6 상대 위험 순위·설명 모듈 검증

## 판정

**Gate 6 통과.** 저장된 `stage5_lightgbm_trial10_v1`을 재학습하지 않고 2025년 4분기 서울 `상권×서비스업종` 21,333행을 채점해 정책 v1 기준분포를 만들었다. 서비스는 원시 모델 점수나 위험/안전 판정 대신 두 비교집단의 Percentile·상위 비율·순위를 반환한다.

## 구현 계약

- 기준분기: `20254`(2025년 4분기), 원본 Panel의 최신 사용 가능 분기
- 주 비교집단: 같은 분기·같은 업종의 서울 상권
- 보조 비교집단: 같은 분기 서울 전체 상권·업종 조합
- 동점: 같은 점수에 같은 최상 경쟁순위(`competition min rank`)를 부여하고 다음 순위는 건너뛴다.
- Percentile: `100 × (비교집단 크기 - 우선순위) / 비교집단 크기`
- 상위 비율: `100 - Percentile`
- 운영 임계값: 없음
- 설명: LightGBM TreeSHAP 기여방향을 원본 Feature 단위로 합산하고 식별자·좌표를 제외한 뒤, 높이는 요인과 낮추는 요인을 각각 최대 3개 반환한다.

## 기준분포 QA

| 항목 | 결과 |
| --- | ---: |
| 기준행 | 21,333 |
| 상권 수 | 1,565 |
| 업종 수 | 62 |
| 업종별 비교집단 크기 | 최소 16, 최대 1,406 |
| 중복 `상권×업종` 키 | 0 |
| 유한한 내부 점수 | 전부 통과 |
| 원본 / 변환 Feature | 197 / 2,677 |
| 전체 Feature Importance 행 | 197 |
| 모델 SHA-256 | `0c87f8a568700ed72614f9b3732fc38f5e39678695d9cd188275e4f1638e9736` |

## 실제 입력 확인

입력 `이태원 관광특구(3001491) × 한식음식점(CS100001)`은 다음과 같이 반환됐다.

- 주 지표: 같은 업종 서울 상권 1,406개 중 1,280위, Percentile `8.96`, 상위 비율 `91.04%`
- 보조 지표: 서울 전체 21,333개 조합 중 21,154위, Percentile `0.84`, 상위 비율 `99.16%`
- 기준분기·정책: `2025년 4분기`, `v1`
- 모델 적용 범위: 기준분기 이후 두 분기의 매출환경 지속 악화를 서울 상권·업종 단위로 상대 정렬
- 설명: 높이는 요인 3개와 낮추는 요인 3개, 현재값, 같은 업종 중앙값, 비인과 문구 반환
- 별도 Python 프로세스 2회 결과 SHA-256: 두 번 모두 `dd132e385d7d614991971ccaff4288121fb81d4d8dfc2cfac6e9511e8fde0a50`

## 오류·회귀 테스트

`C:\Program Files\Python313\python.exe -m pytest` 결과는 `27 passed`이다.

- 정상 입력과 동일 입력 결정론
- 알려진 상권·업종이지만 최신분기 조합이 없는 데이터 부족 입력
- 빈 입력, 지원하지 않는 상권, 지원하지 않는 업종
- 동점 경쟁순위와 Percentile 공식
- 저장 전처리·모델이 기준분포의 내부 점수를 허용오차 `1e-12` 안에서 재현
- Manifest·Artifact 해시와 기준분포 계약
- 원시 점수 비노출, 운영 임계값 없음, 절대 폐업확률 오해 방지 문구
- 기존 Stage 0~5 테스트 회귀

## 산출물

- 실행 설정: `config/stage6.yaml`
- 기준분포 생성: `src/models/build_stage6_reference.py`, `scripts/build_stage6_reference.ps1`
- 조회·설명 서비스: `src/models/stage6_risk_service.py`
- 서비스 기준 Feature: `data/processed/stage6_reference_features.parquet`
- 입력 카탈로그: `reports/stage6/area_catalog.csv`, `industry_catalog.csv`
- 전체 중요도: `reports/stage6/global_feature_importance.csv`
- 무결성 Manifest: `reports/stage6/stage6_manifest.json`
- 테스트: `tests/test_stage6_risk_service.py`

## 해석 한계

Percentile과 상위 비율은 같은 기준분기의 두 비교집단 안에서 본 상대 위치다. 개별 점포의 폐업확률, 안전/위험 판정, 인과효과 또는 정책지원 자격을 뜻하지 않는다. 내부 모델 점수는 순위 계산과 감사에만 사용하며 서비스 반환에서 제외한다.
