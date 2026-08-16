# 서울 소상공인 정책금융 영향 시뮬레이터

## MVP 단계별 구현 체크리스트

> 문서 상태: Stage 0~6·RE Stage 1~6 완료, RE Stage 7 계약 승인 완료·사용자 지시에 따라 구현 미착수
> 기준일: 2026-08-16
> 실행 체계: `Stage 0~6 + RE Stage 1~9`
> 기준 계획서: `프로젝트 계획서.md`
> 재설계 근거: `프로젝트 차별화 구상.md`
> 다음 실행 단계: 사용자에게서 별도 구현 요청을 받기 전 RE Stage 7 미착수 유지

> 데이터 다운로드 기준: [`향후 데이터 다운로드 가이드.md`](./data/raw_re/향후%20데이터%20다운로드%20가이드.md)
> 수집 역할 고정: 외부 데이터가 필요하면 Codex가 먼저 필요 이유·시점·정확한 범위와 공식 링크를 검색해 안내한다. 다운로드와 프로젝트 원본 폴더 적재는 사용자가 수행하며, Codex는 적재 완료 확인 후 로컬 파일만 전처리·통합·QA·분석한다. 포괄적인 단계 진행 요청은 다운로드·적재 허가가 아니다.

---

## 1. 문서 사용 방법

### 1.1 체크 표기

- `[x]`: 구현·검증·증거 기록까지 완료
- `[ ]`: 미완료
- `보류`: 사용자 결정이나 외부조건이 필요해 실행하지 않음
- `제외`: 승인된 MVP 범위에서 구현하지 않음
- `동결`: 과거 결과를 수정하지 않고 기준선으로 보존

### 1.2 우선순위

- `P0`: 해당 Gate 통과에 반드시 필요
- `P1`: 품질과 신뢰성을 위해 권장
- `P2`: 기본 기능이 완료된 뒤 검토하는 확장

### 1.3 필수 기록

각 단계는 최소 다음을 남긴다.

```text
담당자
시작일
완료일
상태
사용한 데이터와 기준일
실행 명령
완료 산출물
검증 결과
남은 한계
다음 단계 전달사항
사용자 승인 기록
```

### 1.4 사용자 승인 규칙

다음 선택은 실행 전에 멈추고 선택지·영향·권장안을 제시한 뒤 사용자의 명시적 승인을 받는다.

- 서비스 범위 변경
- 정책 8~12개 최종 선정
- 개인 입력의 저장·외부 전송
- Target 정의
- 데이터 포함·제외
- 결측·이상치 처리
- 학습·검증 기간
- 평가 지표
- 모델 후보와 최종 모델
- 기존 Stage 6 서비스 유지·제외·보존 범위
- 대안 비교 목표와 안전현금 기준
- 외부 배포
- 되돌리기 어려운 삭제·덮어쓰기

결과 의미를 바꾸지 않는 파일명·함수 분리·테스트 구조 등 통상적인 구현 세부사항은 반복 승인 없이 진행한다.

### 1.5 비례 검증

- 필수 Gate와 결과 정확성에 직접 영향을 주는 항목을 우선한다.
- 필수 Gate가 통과하면 미관·부가 검증 실패만으로 같은 작업을 반복하지 않는다.
- 핵심 수치 불일치, 재현 불가, 누수, 손상, 필수 Gate 실패가 있을 때만 재검증한다.
- 이미 통과한 Stage 0~6 검증은 관련 Artifact를 변경하지 않았다면 반복하지 않는다.

### 1.6 전 단계 공통 종료·환류 규칙

각 Stage는 Gate 검증 직후 반드시 다음 절차를 수행한다.

- 실제 결과와 당초 계획·가정의 차이 확인
- 후속 Stage의 데이터·Target·Feature·모델·평가지표·정책범위·서비스 출력·일정 영향 확인
- 수정이 없으면 `후속 단계 수정 없음`과 근거를 보고서·체크리스트·LOG에 기록
- 수정이 필요하면 다음 Stage 착수 전에 계획서·체크리스트·설정·계약·테스트를 갱신
- 결과 의미나 범위를 바꾸는 수정은 사용자 승인 후 반영
- 환류 검토와 필수 수정이 끝나기 전에는 다음 Stage 착수 금지

이 규칙은 Stage 0~6 결과를 다시 사용할 때와 RE Stage 1~9 각각에 동일하게 적용한다. 모든 RE Gate에는 `후속 단계 영향 검토와 필요 수정 완료`를 필수 항목으로 둔다.

---

## 2. 최종 MVP 최소 구현선

### 반드시 구현

- [ ] 서울 사업장 상권·업종 선택
- [x] 간편 개인 현금흐름 입력
- [x] 상세 CSV 입력 템플릿
- [x] 13주 주별 현금흐름
- [x] 6개월 월별 현금흐름
- [x] 무대응 시나리오
- [ ] 하방·기준·회복 매출환경 시나리오 또는 검증된 사용자 충격률 Fallback
- [x] 공식 정책 10개 구조화
- [ ] 적격·부적격·추가 확인 필요 자격판정
- [x] 보조금·바우처·이차보전·융자·대환·보증의 지원유형 구분
- [x] 정책 적용 전후 현금잔액·부채·이자 비교
- [ ] 최소부채·최장생존·최소상환·빠른실행 목표 중 선택
- [ ] 공식 근거 RAG
- [ ] 생성형 AI의 근거·Trade-off 설명
- [ ] 실제 접근 가능한 웹 URL
- [ ] 기능명세서와 샘플 검증 절차
- [ ] 13주 생존 시뮬레이션 Hero 화면
- [ ] 가상 페르소나 8개 시나리오 모의 검증과 입력·정답 계약·실행 Trace

### 구현하지 않음

- [x] 개인 점포 폐업확률 제외
- [x] 개인 부도확률 제외
- [x] 신용평가 제외
- [x] 대출 승인확률 제외
- [x] 실제 대출 실행 제외
- [x] 정책 신청대행 제외
- [x] 계좌·카드·POS 자동연동 제외
- [x] 주민등록번호·계좌번호 수집 제외
- [x] 정책 수혜 인과효과 예측 제외
- [x] 전국 모든 정책 완전 수집 제외

---

## 3. 전체 단계와 상태

| 단계 | 상태 | 다음 행동 |
| --- | --- | --- |
| Stage 0 | 완료 | 보존 |
| Stage 1 | 완료 | 기존 원본 보존 |
| Stage 2 | 완료 | 기존 QA 보존 |
| Stage 3 | 완료 | Panel v1 동결 |
| Stage 4 | 완료 | 이진 Target v1 동결 |
| Stage 4.5 | 완료 | 분류 EDA·Feature contract 동결 |
| Stage 5 | 완료 | LightGBM v1·2025 평가 동결 |
| Stage 6 | 완료 | 상대 위험순위·설명 보존 |
| RE Stage 1 | 완료 | 서비스 계약·Artifact 동결·Guard·6개 비교안 |
| RE Stage 2 | 완료 | A+C 10개·자격 Rule 56개·금융 Event 30개 |
| RE Stage 3 | 완료 | `re3-v1` 기준 현금흐름 엔진 보존 |
| RE Stage 4 | 완료 | `re4-v1` 정책 금융 이벤트 엔진 보존 |
| RE Stage 5 | 완료 | LightGBM을 내부 시나리오 생성기로 승인, 화면에는 하방·기준·회복만 표시 |
| RE Stage 6 | 완료 | 56개 공식 Rule 판정·227개 공식 Chunk 검색·Fact-lock 설명 |
| RE Stage 7 | 계약 완료·구현 보류 | 후보상태·정책조합·시나리오 적용·안전현금 계약 승인, 사용자 지시에 따라 미착수 |
| RE Stage 8 | 대기 | API·웹 통합 |
| RE Stage 9 | 대기 | 배포·제출 QA |

### 의존 관계

```text
Stage 0~6 완료
      ↓
RE 1 서비스 계약
      ├─────────────┐
      ↓             ↓
RE 2 정책데이터    RE 3 개인 현금흐름
      ↓             ↓
RE 4 정책 금융이벤트
      ├─────────────┐
      ↓             ↓
RE 5 외부모델 v2   RE 6 자격·RAG
      └──────┬──────┘
             ↓
RE 7 대안 비교
             ↓
RE 8 API·웹
             ↓
RE 9 배포·제출
```

---

# Part 1. 완료된 Stage 0~6

## Stage 0 — 범위 확정과 개발 기반 준비

### 상태

| 항목 | 기록 |
| --- | --- |
| 시작일 | 2026-08-14 |
| 완료일 | 2026-08-14 |
| 상태 | 완료·동결 |
| 기존 Gate | 통과 |
| 다음 적용 | RE 공통 개발기반으로 재사용 |

### 완료 체크

- [x] 1인 팀 사용자와 Codex 지원 구조 확정
- [x] Python 3.13.1 환경 기록
- [x] ML과 RAG를 기존 제출 범위에 포함
- [x] 개별 점포 폐업확률을 예측하지 않는 범위 확정
- [x] 실제 대출 승인·신용평가·부도확률 제외
- [x] 비밀키를 코드에 저장하지 않는 방식 확정
- [x] 원본·중간·가공 데이터 분리
- [x] 모델·RAG·앱·테스트·보고서 분리
- [x] 중앙 설정과 난수 시드 관리
- [x] `/health`와 `/scope` 구현
- [x] README와 검증 명령 확인

### 완료 증거

- [x] `README.md`
- [x] `.python-version`
- [x] `requirements.txt`
- [x] `pyproject.toml`
- [x] `.env.example`
- [x] `config/settings.yaml`
- [x] `src/settings.py`
- [x] `app/main.py`
- [x] `reports/stage0/mvp_scope.md`
- [x] `scripts/verify_stage0.ps1`
- [x] Stage 0 테스트 `8 passed`
- [x] 실제 `GET /health` HTTP 200

### RE 전달사항

- [ ] 기존 경로와 충돌하지 않는 RE 전용 경로 승인
- [ ] `src/cashflow/`, `src/policy/`, `src/scenario/`, `src/decision/` 후보 검토
- [ ] `data/raw_re/`, `data/processed_re/`, `reports/re_stage*/` 후보 검토
- [ ] 기존 Stage 0~6 파일 이동·덮어쓰기 금지 Guard 확인

---

## Stage 1 — 서울 상권 원본데이터 확보와 보존

### 상태

| 항목 | 기록 |
| --- | --- |
| 시작일 | 2026-08-14 |
| 완료일 | 2026-08-14 |
| 상태 | 완료·원본 보존 |
| 기존 Gate | 통과 |
| 다음 적용 | Quantile Baseline 후보 데이터 |

### 완료 체크

- [x] 추정매출-상권 확보
- [x] 점포-상권 확보
- [x] 영역-상권 확보
- [x] 길단위인구-상권 확보
- [x] 상권변화지표-상권 확보
- [x] 상주인구-상권 확보
- [x] 직장인구-상권 확보
- [x] 집객시설-상권 확보
- [x] 아파트-상권 확보
- [x] `data/raw/` 원본 수정 금지
- [x] 출처·확인일·기간·파일명·크기 기록
- [x] 인코딩·구분자·좌표계·형식 확인
- [x] 현재 제공본의 원본 ZIP 부재 기록
- [x] 향후 갱신 시 덮어쓰지 않는 규칙 확정

### 완료 증거

- [x] `data/raw/README.md`
- [x] `data/raw/` 1~9번 원본
- [x] `reports/stage2/period_coverage.csv`
- [x] `reports/stage2/key_quality.csv`

### RE 전달사항

- [ ] 신규 정책 데이터는 기존 상권 원본과 분리
- [ ] 신규 상가·인허가·날씨 데이터는 RE Stage 5 전에는 대량수집하지 않음
- [ ] 기존 1~9번 원본 해시·경로 보존

---

## Stage 2 — 기존 데이터 품질검증

### 상태

| 항목 | 기록 |
| --- | --- |
| 시작일 | 2026-08-14 |
| 완료일 | 2026-08-14 |
| 상태 | 완료·QA 보존 |
| 기존 Gate | 통과 |
| 사용 기간 | 2021Q1~2025Q4 |

### 완료 체크

- [x] 실제 컬럼과 표준 컬럼 매핑
- [x] 연도·분기 자료형과 범위 확인
- [x] 상권·업종 코드와 명칭 관계 확인
- [x] 기본키 중복 확인
- [x] EPSG:5181 좌표계 확인
- [x] 유효하지 않은 도형 확인
- [x] 2021~2025 기간 커버리지 확인
- [x] 상권·업종 신규·소멸 코드 확인
- [x] 분기 누락률 확인
- [x] 매출·점포·영역 결합률 확인
- [x] 결측·음수·극단값·비율 단위 확인
- [x] 매출 0과 결측 구분
- [x] 극단값 자동삭제 금지

### 핵심 결과

- [x] 기본키 중복 0건
- [x] 매출→영역 미매칭 0건
- [x] 전체 20분기 누락률 18.1013%
- [x] 활성기간 내부 누락률 3.4592%
- [x] 매출·점포 핵심 기본키 결측 0건
- [x] 유효하지 않은 도형 6건 기록
- [x] 개·폐업률 100 초과 원본값 자동수정 없이 보존

### 완료 증거

- [x] `src/data/run_stage2_quality.py`
- [x] `reports/stage2/quality_validation_plan.md`
- [x] `reports/stage2/qa_summary.md`
- [x] `reports/stage2/schema_mapping.md`
- [x] `reports/stage2/period_coverage.csv`
- [x] `reports/stage2/key_quality.csv`
- [x] `reports/stage2/missingness.csv`
- [x] `reports/stage2/logical_checks.csv`
- [x] `reports/stage2/join_coverage.csv`
- [x] `reports/stage2/panel_gap_summary.csv`
- [x] `reports/stage2/outlier_summary.csv`
- [x] `reports/stage2/spatial_quality.csv`
- [x] `reports/stage2/code_coverage.csv`

### RE 전달사항

- [ ] 정책 데이터 QA는 RE Stage 2에서 별도 수행
- [ ] 개인 입력 QA는 RE Stage 3에서 별도 수행
- [ ] 신규 외부환경 데이터 QA는 RE Stage 5에서 별도 수행
- [ ] 기존 QA를 새 데이터의 품질 근거로 대신하지 않음

---

## Stage 3 — 상권×업종×분기 Panel 구축

### 상태

| 항목 | 기록 |
| --- | --- |
| 시작일 | 2026-08-14 |
| 완료일 | 2026-08-14 |
| 상태 | 완료·Panel v1 동결 |
| 기존 Gate | 통과 |
| 결과 | 439,141행 × 199열 |

### 완료 체크

- [x] 기본키 `연도 + 분기 + 상권 + 업종` 확정
- [x] 추정매출 기준 left join
- [x] 점포 데이터 동일 키 결합
- [x] 보조 데이터 분기×상권 결합
- [x] 결합 전후 행 수 기록
- [x] 1:1 JOIN 검증
- [x] 상권명·업종명 보존
- [x] 현재·과거 Feature만 생성
- [x] 미래정보 Feature 제외
- [x] 변화율 분모 0 처리
- [x] 과거 이력 부족 플래그
- [x] P0·P1·P2 데이터군 포함
- [x] 기본키 중복 0건
- [x] 두 번 실행해 동일 행·열·SHA-256
- [x] 상권·업종 3개 수작업 대조

### 완료 증거

- [x] `src/data/build_stage3_panel.py`
- [x] `data/processed/stage3_panel.parquet`
- [x] `reports/stage3/data_dictionary.csv`
- [x] `reports/stage3/feature_definitions.md`
- [x] `reports/stage3/join_row_counts.csv`
- [x] `reports/stage3/manual_spot_check.csv`
- [x] `reports/stage3/feature_quality.csv`
- [x] `reports/stage3/reproducibility_check.json`
- [x] `reports/stage3/panel_manifest.json`

### RE 전달사항

- [ ] Panel v1 덮어쓰기 금지
- [ ] Target v2 승인 후에만 Panel v2 생성
- [ ] 기존 Feature Baseline과 신규 데이터 Ablation 분리
- [ ] Panel v2 별도 Manifest·해시 생성

---

## Stage 4 — 이진 지속악화 Target과 시간순 검증

### 상태

| 항목 | 기록 |
| --- | --- |
| 시작일 | 2026-08-14 |
| 완료일 | 2026-08-15 |
| 상태 | 완료·모델 v1 전용 동결 |
| 기존 Gate | 통과 |
| 개발행 | 222,973 |
| 양성 | 56,369·25.28% |

### 완료 체크

- [x] 향후 2개 분기 연결
- [x] 두 미래 분기 각각 전년동기 대비 감소 조건
- [x] 두 미래 분기 합산 -10% 이하 조건
- [x] 개발기간에서 -5%~-20% 민감도 검토
- [x] Target 선택에 잠긴 2025 통계 미사용
- [x] 랜덤 분할 금지
- [x] 2024Q1~Q4 expanding-window 4개 Fold
- [x] Target 창 겹침 방지 1분기 Purge
- [x] 2025Q1~Q4 잠긴 테스트 지정
- [x] Feature·Target 시점 예시 문서화

### 완료 증거

- [x] `config/stage4.yaml`
- [x] `src/data/build_stage4_dataset.py`
- [x] `data/processed/stage4_development.parquet`
- [x] `data/processed/stage4_fold_membership.parquet`
- [x] `reports/stage4/target_definition.md`
- [x] `reports/stage4/stage4_manifest.json`

### RE 전달사항

- [ ] 이진 Target v1 삭제 금지
- [ ] 새 현금흐름의 충격 크기에 이진 Target을 직접 사용하지 않음
- [ ] RE Stage 5에서 연속형 Target v2 별도 승인
- [ ] 기존 2025 잠긴 테스트를 새 모델 선택에 재사용하지 않음

---

## Stage 4.5 — 분류모델 EDA와 Feature contract

### 상태

| 항목 | 기록 |
| --- | --- |
| 시작일 | 2026-08-15 |
| 완료일 | 2026-08-15 |
| 상태 | 완료·모델 v1 연구기록 |
| 기존 Gate | 통과 |

### 완료 체크

- [x] Fold 1 Train 122,011행만 사용
- [x] 원본 199개·파생 134개 분석
- [x] 분포·상관·Target 관계
- [x] 다중검정 FDR
- [x] 기간 안정성과 PSI
- [x] 중복·공선성·조건수
- [x] 구조 제거 후 VIF
- [x] 2024 Validation Target 미사용
- [x] 잠긴 2025 미사용
- [x] 테스트 10개 통과
- [x] D안 Feature contract 승인
- [x] PCA 미적용

### Feature-set 완료

- [x] 공통 197개
- [x] 선형 207개
- [x] 매출금액 원시군 220개
- [x] 거래건수 원시군 220개
- [x] 유동인구 원시군 218개
- [x] 상주인구 원시군 217개
- [x] 직장인구 원시군 217개

### 완료 증거

- [x] `reports/stage45/feature_contract.md`
- [x] `reports/stage45/`
- [x] `src/analysis/run_stage45_eda.py`
- [x] `src/features/build_stage45_features.py`
- [x] `tests/test_stage45_features.py`

### RE 전달사항

- [ ] 연속형 Target v2에서 EDA 재수행
- [ ] 기존 Feature contract를 Quantile 모델에 자동 적용하지 않음
- [ ] 신규 데이터의 누수·Drift·증분효과 검토

---

## Stage 5 — 분류모델 비교·튜닝·최종평가

### 상태

| 항목 | 기록 |
| --- | --- |
| 시작일 | 2026-08-15 |
| 완료일 | 2026-08-15 |
| 상태 | 완료·LightGBM v1 동결 |
| 기존 Gate | 통과 |

### 완료 체크

- [x] Dummy 1개
- [x] Logistic Regression 3개
- [x] Random Forest
- [x] Extra Trees
- [x] LightGBM
- [x] XGBoost
- [x] CatBoost
- [x] 34개 변형×4 Fold=136회 무튜닝 비교
- [x] 상위 3개×20 Trial×4 Fold=240 Fit
- [x] 대표 모델·Voting·Nested Stacking 52단계
- [x] 동일 Fold·Target·지표 비교
- [x] 업종별 성능 확인
- [x] 전처리 Train-only Fit

### OOF 결과

- [x] LightGBM 전체 OOF AUPRC 0.6454
- [x] LightGBM 전체 OOF AUROC 0.8108
- [x] Soft Voting 전체 OOF AUPRC 0.6474
- [x] Soft Voting 전체 OOF AUROC 0.8115
- [x] 단순 운영을 우선해 LightGBM Trial 10 최종 선택
- [x] 운영 임계값 미사용

### 잠긴 2025 평가

- [x] 모델·Feature를 평가 전 고정
- [x] Refit 202,918행
- [x] 잠긴 테스트 79,506행
- [x] AUPRC 0.625695
- [x] AUROC 0.791821
- [x] Brier 0.164177
- [x] Log Loss 0.495829
- [x] 2025 임계값·Precision·Recall·F2 미탐색
- [x] 저장 예측 재계산
- [x] 모델 재로딩 재현
- [x] 핵심 Artifact 해시 검증
- [x] 재실행 차단

### 완료 증거

- [x] `reports/stage5/full_comparison.md`
- [x] `reports/stage5/optuna_report.md`
- [x] `reports/stage5/selected_oof_report.md`
- [x] `reports/stage5/final_2025_report.md`
- [x] `reports/stage5/final_2025_metrics.json`
- [x] `reports/stage5/final_2025_manifest.json`
- [x] `reports/stage5/final_2025_predictions.parquet`
- [x] `artifacts/stage5_lightgbm_trial10.joblib`
- [x] `artifacts/stage5_lightgbm_trial10_metadata.json`

### RE 전달사항

- [x] LightGBM v1 코드·Artifact·보고서 삭제·덮어쓰기 금지
- [x] 서비스 추론·화면·Fallback에서 제외하고 과거 검증 근거로만 보존
- [x] 기존 이진모델을 새 데이터로 재학습하지 않음
- [x] 2025 결과를 새 모델 선택에 사용 금지
- [x] 새 독립 감사기간 없음을 RE5 모델 한계로 표시

---

## Stage 6 — 상대 위험순위와 TreeSHAP 설명

### 상태

| 항목 | 기록 |
| --- | --- |
| 시작일 | 2026-08-15 |
| 완료일 | 2026-08-15 |
| 상태 | 완료·서비스 제외·감사 증거로 보존 |
| 기존 Gate | 통과 |

### 완료 체크

- [x] 2025Q4 기준분포 생성
- [x] 21,333개 상권×업종
- [x] 상권 1,565개
- [x] 업종 62개
- [x] 같은 업종 내 주 Percentile
- [x] 서울 전체 보조 Percentile
- [x] 상위 비율과 경쟁순위
- [x] 동점 규칙
- [x] 원시 모델 점수 비노출
- [x] 이진 위험·안전 판정 없음
- [x] TreeSHAP 양·음 요인
- [x] 현재값과 같은 업종 중앙값
- [x] 입력 오류와 데이터 부족 처리
- [x] 별도 프로세스 결정론 검증
- [x] 기존 Stage 0~5 회귀 포함 `27 passed`

### 완료 증거

- [x] `config/stage6.yaml`
- [x] `src/models/build_stage6_reference.py`
- [x] `scripts/build_stage6_reference.ps1`
- [x] `src/models/stage6_risk_service.py`
- [x] `data/processed/stage6_reference_features.parquet`
- [x] `reports/stage6/area_catalog.csv`
- [x] `reports/stage6/industry_catalog.csv`
- [x] `reports/stage6/global_feature_importance.csv`
- [x] `reports/stage6/stage6_manifest.json`
- [x] `reports/stage6/verification.md`
- [x] `tests/test_stage6_risk_service.py`

### RE 전달사항

- [x] 개인 점포 매출·폐업·정책 수혜 인과효과로 해석 금지
- [x] 기존 Stage 6 서비스 추론·화면에서 제외
- [x] 새 데이터 재학습 금지
- [x] 코드·Artifact·평가보고서는 `archived evidence`로 보존
- [x] 모델 장애 Fallback은 사용자 직접 매출충격률로 분리

---

# Part 2. RE Stage 1~9

## RE Stage 1 — 서비스 전환 계약과 Guard

### 목표

새 서비스의 입력·출력·제외범위와 기존 산출물의 지위를 확정하고, 옛 Stage 7 작업이 실행되지 않도록 한다.

### 상태 기록

| 항목 | 기록 |
| --- | --- |
| 담당자 | 사용자 결정 / Codex 문서·구현 지원 |
| 시작일 | 2026-08-15 |
| 완료일 | 2026-08-15 |
| 상태 | 완료 — Gate RE1 통과, 정책 최종선택은 RE2 착수 전 대기 |
| 선행조건 | 새 계획서와 체크리스트 승인 |

### P0 — 기존 계획 충돌 해소

- [x] 기존 금융부담지수 0~100점 구현 취소 승인
- [x] 기존 20/20/35/25 가중치 사용 중단 승인
- [x] 낮음·주의·높음 등급 사용 중단 승인
- [x] 단순 정책 적합도 백분율 사용 금지
- [x] 정책 1·2·3위 단순 Ranking 사용 금지
- [x] 기존 Stage 7~12 실행 Guard 설정
- [x] 기존 Stage 0~6 Artifact 503개 SHA-256 동결 목록 생성

### P0 — 새 서비스 계약

- [x] 서비스 명칭 확정
- [x] 서울 소상공인 대상 유지
- [x] 정책금융 영향 시뮬레이터 전환 승인
- [x] 13주 주별 계산범위 승인
- [x] 6개월 월별 계산범위 승인
- [x] 무대응 시나리오 필수화
- [x] 비차입 지원 우선 비교
- [x] 최소부채 기본 목표 승인
- [x] 최장생존·최소상환·빠른실행 선택목표 승인
- [x] 안전현금 기준의 정의 후보 작성 — RE3 사용자 입력 우선 원칙 유지, RE7에서 4주 필수지출 기반 수정 가능 제안값 승인
- [x] 정책 범위 8~12개 원칙 승인
- [x] 간편 입력 + CSV 업로드 원칙 승인

### P0 — 역할 경계

- [x] ML은 상권×업종 집계환경 시나리오만 생성
- [x] 규칙 엔진은 공식 자격판정
- [x] 현금흐름 엔진은 금액·날짜·상환 계산
- [x] 대안 비교 엔진은 사용자 목표별 결과 비교
- [x] RAG는 공식 근거 검색
- [x] LLM은 설명만 수행
- [x] LLM의 계산·자격·순위 변경 금지

### P0 — 개인정보 계약

- [x] 주민등록번호 수집 금지
- [x] 계좌번호 수집 금지
- [x] 신용점수 수집 금지
- [x] 사업자등록번호 필수화 금지
- [x] 세션 내 계산 우선
- [x] 명시적 동의 없는 영구저장 금지
- [x] 원금액 로그 금지
- [x] 외부 LLM 전송 필드 최소화

### P0 — RE 경로와 버전

- [x] RE 전용 설정 파일 명명규칙
- [x] RE 보고서 경로
- [x] RE 원본·가공 데이터 경로
- [x] 현금흐름 엔진 버전 형식
- [x] 정책 데이터 버전 형식
- [x] 모델 v2 버전 형식
- [x] 기존 파일 덮어쓰기 차단 테스트

### 완료 산출물

- [x] `reports/re_stage1/service_contract.md`
- [x] `reports/re_stage1/artifact_disposition.csv`
- [x] `reports/re_stage1/privacy_scope.md`
- [x] `reports/re_stage1/input_output_contract.md`
- [x] `config/re_stage1.yaml`
- [x] `reports/re_stage1/policy_portfolio_comparison.md`
- [x] `reports/re_stage1/verification.md`
- [x] 실행 Guard 테스트

### Gate RE1

- [x] 서비스 전환을 사용자가 승인
- [x] 기존 금융부담점수 구현 취소가 명시됨
- [x] Stage 0~6 동결 대상 503개가 해시와 함께 기록됨
- [x] 정책 수·입력범위·기본 목표가 승인됨
- [x] 미승인 데이터·Target·모델 실행이 차단됨
- [x] 후속 단계 영향 검토와 필요 수정 완료 — RE2를 `6안 검토 → 최종 승인 → 정책별 원문 수집` 순서로 수정

---

## RE Stage 2 — 소상공인 정책 데이터와 지식베이스

### 목표

소상공인에게 적용 가능한 공식 정책 8~12개의 자격·금액·지급·상환조건을 원문과 연결해 구조화한다.

### 상태 기록

| 항목 | 기록 |
| --- | --- |
| 담당자 | 사용자 정책 범위 승인 / Codex 수집·구조화·QA — 완료된 과거 이력이며, 이후 외부 수집은 사용자 전담 |
| 시작일 | 2026-08-15 |
| 완료일 | 2026-08-16 |
| 상태 | 완료 — A+C 10개, Gate RE2 통과 |
| 선행조건 | Gate RE1 |

### RE1 전 선행수집·QA 기록

사용자가 먼저 확보한 P-01·P-03·P-04·P-05 자료에는 원본 보존과 형식 QA, 공통 스키마 변환, 정확 제목 그룹화까지만 적용했다. 이 작업은 RE Stage 2의 입력을 준비한 것이며, Gate RE1 통과나 RE Stage 2 착수·완료로 간주하지 않는다.

- 선행 통합 결과: 1,005개 소스 레코드 → 827개 정확 제목 후보 그룹
- 복수 출처 그룹: 174개
- RE1 비교 결과: 25개 고유 후보로 A·B·C·A+C·A+B·A+B+C 6개 안, 총 62행 생성
- RE1 당시 보류였던 최종 정책 선정과 Rule·Event 구조화를 RE2에서 완료했다. 퍼지매칭과 후보 삭제는 필요성이 없어 수행하지 않았다.
- 사전 QA: [`reports/pre_re1/policy/QA.md`](./reports/pre_re1/policy/QA.md)
- 통합 후보 그룹: [`candidate_groups.csv`](./data/processed_re/policy/pre_re1/candidate_groups.csv)
- 6개 안 비교: [`policy_portfolio_comparison.md`](./reports/re_stage1/policy_portfolio_comparison.md)
- 비교 후보 원본표: [`portfolio_candidates.csv`](./data/processed_re/policy/re_stage1/portfolio_candidates.csv)

### RE2 완료 결과

- 최종 선택: `A+C`, 정책 10개
- 공식 원문 Manifest: 27행
- 정책 Metadata: 10행
- 자격 Rule: 56행
- 자격 정답사례: 20행
- 금융 Event: 30행
- 버전 이력: 11행
- 검색 전처리 Chunk: 217개, 검색 인덱스는 아직 미생성
- 자동 테스트: `9 passed`
- 상세 보고서: [`reports/re_stage2/structured_qa.md`](./reports/re_stage2/structured_qa.md)

### 중요 — 기업마당 API의 정확한 역할

`중소벤처기업부_중소기업 지원사업 공고 조회 서비스`는 소상공인 전용 API가 아니다.

공식 설명상 중앙행정기관·지방자치단체·유관기관의 중소기업 지원 공고를 제공하며, `지원대상` 필드와 `소상공인지원·소상공인지원사업공고` 키워드를 포함한다. 따라서 소상공인 공고도 포함될 수 있지만 중소기업·창업·벤처 등 다른 대상 공고도 함께 들어온다.

체크리스트에서의 역할은 다음과 같다.

| 출처 | 역할 | 단독 자격근거 사용 |
| --- | --- | --- |
| 기업마당 공고 API | 광역 후보 수집 | 금지 |
| 소상공인24·소진공 공식 공고 | 소상공인 대상 확인·원문 검증 | 가능 |
| 서울시 공식 공고 | 서울 지역 정책 원문 검증 | 가능 |
| 중소벤처24 공고 API | 중기부 유관기관 공고 교차확인 | 단독 사용 금지 |
| 정책 공식 신청페이지·첨부문서 | 최종 자격·금융조건 근거 | 필수 |

### 공식 출처

- [x] 전체 다운로드 목록·절차: [`향후 데이터 다운로드 가이드.md`](./data/raw_re/향후%20데이터%20다운로드%20가이드.md)
- [x] 기업마당 API: https://www.data.go.kr/data/15157820/openapi.do
- [x] 소상공인24: https://www.sbiz24.kr/landing/
- [x] 소상공인 정책자금 접수·공지: https://ols.semas.or.kr/ols/man/SMAN010M/page.do
- [x] 소상공인 정책자금 조건 요약: https://ols.semas.or.kr/ols/man/SMAN018M/page.do
- [x] 정책자금 지원 제외업종: https://ols.semas.or.kr/ols/pfa/SPFA207P/page.do
- [x] 2026년 서울시 중소기업육성자금: https://news.seoul.go.kr/economy/rearing-funds
- [x] 2026년 서울시 육성자금 변경공고: https://www.seoul.go.kr/news/news_notice.do?nttNo=457365
- [x] 서울시 소상공인 종합지원: https://news.seoul.go.kr/economy/small-business-supports
- [x] 중소벤처24 공고 API: https://www.data.go.kr/data/15113191/openapi.do
- [x] 선정 정책별 공식 신청페이지·신청경로 또는 전화·이메일 접수경로 기록

### P0 — 다운로드한 정책 데이터의 사용 계약

- [x] 모든 API 응답·공고 원문·첨부문서·신청 페이지를 `data/raw_re/policy/<source>/<수집일>/`에 원본 그대로 보존
- [x] 원본 URL·공고일·적용기간·수집일·SHA-256을 Manifest에 기록하고 원문에 없는 값은 `미확인` 유지
- [x] 기업마당 API는 당해 연도 광역 후보 목록과 공식 공고 URL 추출에만 사용
- [x] 기업마당 API 값을 자격·금리·한도·접수상태의 최종값으로 직접 사용하지 않음
- [x] 소상공인24·소진공·서울시·공식 수행기관 원문으로 소상공인 적용과 조건 검증
- [x] 소진공 공고를 정책 Metadata·자격 Rule·금융 Event·검색 전처리 Chunk에 사용
- [x] 서울시 최초공고와 변경공고를 별도 버전으로 보존하고 최신 변경공고 조건 선택
- [x] 중소벤처24 API를 공고명·기간·기관·첨부파일 교차검증에만 사용
- [x] 정책 원문을 `Metadata → Rule → Event → Chunk` 순서로 변환
- [x] RE4에는 검수된 금융 Event만 전달
- [x] RE6에는 검수된 자격 Rule과 Chunk만 전달
- [x] RAG·LLM이 Rule·Event 값을 생성하거나 수정하지 못하도록 Guard 유지
- [x] RE7에는 정책별 현금흐름 결과와 공식 근거만 전달하도록 계약 유지
- [x] RE9 데모 직전 접수상태·변경공고 재수집을 필수 후속 작업으로 유지

### P0 — API 접근성 검증

- [x] 기업마당 API 활용신청 후 제공받은 키로 실제 접근 확인
- [x] 개발계정 승인상태와 응답 성공 확인
- [x] 실제 Endpoint와 요청 파라미터 확인
- [x] 실제 JSON 응답 확인
- [x] 공고ID·등록일·수정일 필드 확인
- [x] 지원대상 필드 확인
- [x] 공고 URL과 첨부파일 필드 확인
- [x] 신청기간·신청방법·문의처 확인
- [x] 당해연도 범위 확인
- [x] 호출량 제한이 제공받은 정보에 미기재임을 기록
- [x] 운영 전 계정·호출한도 재확인이 필요함을 기록

### P0 — 소상공인 후보 필터

- [x] `지원대상`에 소상공인 명시 여부 확인
- [x] 해시태그·분야의 소상공인 관련 키워드 확인
- [x] 수행기관과 소진공 여부 확인
- [x] 서울 지역 적용 여부 확인
- [x] 업종 제한 확인
- [x] 매출·상시근로자·업력 조건 확인
- [x] 소기업에는 적용되지만 소상공인에는 적용되지 않는 공고 분리
- [x] 창업기업·벤처기업 전용 공고 분리
- [x] 중소기업 전용 공고를 소상공인 공고로 자동 간주하지 않음
- [x] 키워드만 일치하고 자격에 소상공인이 없는 공고를 최종 10개에서 제외

### P0 — 공식 원문 검증

- [x] 소상공인24·소진공·중기부·공식 수행기관 원문 존재 확인
- [x] 서울시 정책은 서울시·서울신용보증재단·공식 수행기관 원문 확인
- [x] 공고번호와 공고일 확인, 원문에 없는 번호는 `미확인`
- [x] 신청 시작·종료일 확인
- [x] 예산 소진형 여부 확인
- [x] 대상 정의 확인
- [x] 제외업종 확인
- [x] 체납·연체·신용조건 확인
- [x] 지원한도 확인
- [x] 금리·이차보전율 확인
- [x] 거치·상환기간 확인
- [x] 상환방식 확인
- [x] 자부담 확인
- [x] 지급·사후환급 방식 확인, 미기재 절차는 `미확인`
- [x] 중복수혜 제한 확인
- [x] 문의처와 신청 URL·전화·이메일 경로 확인

### P0 — 정책 8~12개 선정

- [x] 보조금 후보 최소 1개
- [x] 바우처 후보 최소 1개
- [x] 이차보전 후보 최소 1개
- [x] 정책자금 융자 후보 최소 2개
- [x] 대환·상환부담 완화 후보 최소 1개
- [x] 보증 후보 최소 1개
- [x] 서울 지역정책 포함
- [x] 소진공 전국정책 포함
- [x] 각 정책의 금융효과 계산 가능성 평가
- [x] A·B·C·A+C·A+B·A+B+C 비교표 작성
- [x] 최종 A+C 10개 사용자 승인

### P0 — 정책 Metadata

- [x] `policy_id`
- [x] `policy_version`
- [x] `policy_name`
- [x] `provider`
- [x] `policy_type`
- [x] `purpose_tags`
- [x] `region_scope`
- [x] `industry_scope`
- [x] `business_age_rule`
- [x] `revenue_rule`
- [x] `employee_rule`
- [x] `credit_or_delinquency_rule`
- [x] `application_start`
- [x] `application_end`
- [x] `budget_exhaustion_rule`
- [x] `official_notice_url`
- [x] `attachment_url`
- [x] `effective_from`
- [x] `effective_to`
- [x] `retrieved_at`
- [x] `reviewed_at`

### P0 — 금융조건 Metadata

- [x] `support_form`
- [x] `minimum_amount`
- [x] `maximum_amount`
- [x] `support_rate`
- [x] `interest_rate_rule`
- [x] `interest_subsidy_rule`
- [x] `guarantee_fee_rule`
- [x] `grace_period`
- [x] `repayment_period`
- [x] `repayment_method`
- [x] `matching_fund_rate`
- [x] `eligible_expense_types`
- [x] `payment_method`
- [x] `reimbursement_delay_rule`
- [x] `combinability_rule`
- [x] `unquantifiable_conditions`

### P0 — 출처 상태

- [x] 공식 API 확인
- [x] 공식 공고 확인
- [x] 공식 첨부문서 확인
- [x] 사용자 입력 상태값 계약 정의
- [x] 서비스 가정 상태값 계약 정의
- [x] `미확인` 사용
- [x] `해당 없음` 사용

### P0 — 버전·원문 보존

- [x] 원문 URL 기록
- [x] 원문 파일 또는 내용 식별자 기록
- [x] SHA-256 기록
- [x] 수집일 기록
- [x] 검수일 기록
- [x] 적용기간 기록
- [x] 변경공고 별도 버전
- [x] 종료·현재성 불확실 정책 상태 구분
- [x] 과거 버전 덮어쓰기 금지

### 검증

- [x] 구조화 값과 원문 수작업 대조
- [x] 두 명칭이 같은 정책의 버전 구분
- [x] 예산소진·현재성 불확실 정책을 확정적인 `접수 중`으로 표시하지 않음
- [x] 지원대상 없는 후보 자동채택 0건
- [x] 중소기업 전용 공고의 소상공인 오분류 0건
- [x] 공식 근거 없는 금리·한도·지급일 생성 0건
- [x] 금융효과 계산 불가조건을 `미확인` 처리

### 완료 산출물

- [x] API 접근성 보고서
- [x] 전체 후보 공고 목록
- [x] 소상공인 후보 필터 결과
- [x] 최종 정책 선정표
- [x] 원문 Manifest
- [x] 정책 Metadata
- [x] 자격 Rule
- [x] 정책별 자격 정답사례 2개
- [x] 금융조건 Metadata
- [x] 구조화 QA 보고서
- [x] 정책 버전 변경이력
- [x] 검색 전처리 Chunk — 검색 인덱스는 RE6까지 보류

### Gate RE2

- [x] 기업마당을 소상공인 전용 API로 표현하지 않음
- [x] 모든 선정 정책이 공식 원문에서 소상공인 적용 확인
- [x] A+C 정책 10개 사용자 승인
- [x] 자격·금융조건이 원문과 추적 가능
- [x] 미확인 값이 추측으로 채워지지 않음
- [x] 후속 단계 영향 검토와 필요 수정 완료

### RE2 종료 환류

- [x] RE3 상세 입력에 공과금·4대보험·차량연료비 유형과 `expense_type` 추가
- [x] RE4 공통 계약에 `event_id`와 연결 이벤트 중복방지 추가
- [x] RE6에 세션 한정 자격 프로필과 신용구간 3상태 입력 추가
- [x] RE5는 Target·데이터·모델 정의 수정 없음으로 기록
- [x] 상세 근거: [`downstream_impact_review.md`](./reports/re_stage2/downstream_impact_review.md)

---

## RE Stage 3 — 개인 현금흐름 입력과 기준 엔진

### 목표

ML·정책·RAG 없이도 개인 사업장의 13주·6개월 기준 현금흐름을 결정론적으로 계산한다.

### 상태 기록

| 항목 | 기록 |
| --- | --- |
| 담당자 | 사용자 입력 계약 승인 / Codex 구현·검산 |
| 시작일 | 2026-08-16 |
| 완료일 | 2026-08-16 |
| 상태 | 완료 — Gate RE3 통과 |
| 선행조건 | Gate RE1 |

### 승인된 구현 계약 — 2026-08-16

- [x] 간편 입력과 상세 CSV를 모두 지원
- [x] 계산된 현금잔액은 음수 허용, 0원 보정 금지
- [x] 입력 금액의 음수 거부와 계산 결과의 음수 허용을 분리
- [x] 간편 입력의 월 대출상환액은 원금·이자 합계 현금유출로 처리
- [x] 대출별 상세 입력에만 원금균등·원리금균등·만기일시상환 계산 적용
- [x] 상세 대출 이자는 월 단위 계산, 일할계산 제외
- [x] 각 금융 이벤트 계산값을 원 단위 반올림
- [x] 안전현금 기준은 사용자 입력 필수, 미입력 시 임의 기본값 금지
- [x] 13주 계산의 매출 입금일·비용 지급일 누락 시 임의 날짜 생성 금지 및 입력 오류 반환
- [x] RE3에는 새 외부 데이터가 필요하지 않으며 로컬 코드·가상 사례만 사용
- [x] 사용자 재개 요청 후 승인 계약대로 구현 완료

### P0 — 간편 입력 계약

- [x] 기준일
- [x] 현재 보유현금
- [x] 최근 월평균 매출 또는 월별 매출
- [x] 월 임대료
- [x] 월 인건비
- [x] 월 변동비 또는 변동비율
- [x] 기타 고정비
- [x] 대출잔액
- [x] 월 대출상환액 또는 대출별 상세
- [x] 모든 금액 원 단위
- [x] 기준 기간 표시

### 승인된 후속 웹 표시 계약 — 구현 미완료

- [ ] 월 금액만 받는 간편모드는 특정 고갈 주차 확정 대신 추정 범위 표시
- [x] 간편 추정 범위 산출법 사용자 승인 — 2026-08-16
- [ ] 매출 입금유형 `매일·매주·월초·월중·월말` 입력
- [ ] 주요 비용·대출상환 시기 `초·중·말` 입력
- [ ] `초=1~10일`, `중=11~20일`, `말=21일~월말` 변환
- [ ] 보수적 일정은 유입 늦게·유출 일찍 배치
- [ ] 기준 일정은 허용구간 중앙일 배치
- [ ] 완화 일정은 유입 일찍·유출 늦게 배치
- [ ] 세 일정을 날짜별 이벤트로 변환해 기존 `re3-v1`을 반복 호출
- [ ] 정확한 날짜 입력은 범주형 가정보다 우선
- [ ] 기준 현금곡선과 보수적~완화 범위를 함께 표시
- [ ] 현재 `re3-v1`처럼 주요 입금일·지급일을 받은 경우 `반복일정 가정 기반 계산` 표시
- [ ] 날짜별 이벤트·대출 CSV는 `상세 일정 기반 계산` 표시
- [ ] 입력 수준·일정 가정·불확실성·계산 버전 공통 표시
- [ ] 임의의 `9~11주` 범위 생성 금지

### P1 — 상세 CSV

- [x] 최근 6~12개월 매출
- [x] 매출 입금 예정일
- [x] 임대료 지급일
- [x] 인건비 지급일
- [x] 매입비 지급일
- [x] 세금·공과금 일정
- [x] 공과금·4대보험·차량연료비 비용 유형
- [x] 외상매출금
- [x] 외상매입금
- [x] 일회성 지출
- [x] 일회성 지출 `expense_type`
- [x] 대출별 잔액
- [x] 대출별 금리
- [x] 상환방식
- [x] 거치기간
- [x] 만기

### P0 — 입력 검증

- [x] 음수 금액 거부
- [x] 문자열 금액 거부
- [x] NaN·무한대 거부
- [x] 원·만원 단위 혼동 경고
- [x] 동일 비용 중복 탐지
- [x] 변동비 금액과 비율 중복 금지
- [x] 대출잔액 0·상환액 양수 확인
- [x] 금리 백분율 단위 확인
- [x] 만기·거치기간 논리 확인
- [x] 매출 0원에서도 현금계산 가능
- [x] 비정상 비율 입력확인 경고

### P0 — 계산 엔진

- [x] 주별 13주 타임라인
- [x] 월별 6개월 타임라인
- [x] 기초현금
- [x] 영업현금유입
- [x] 고정비
- [x] 변동비
- [x] 세금·공과금
- [x] 기존부채 원금
- [x] 기존부채 이자
- [x] 일회성 지출
- [x] 기말현금
- [x] 최저 현금잔액
- [x] 최초 현금 고갈 시점
- [x] 기간 말 현금잔액

### P0 — 대출 상환

- [x] 원금균등
- [x] 원리금균등
- [x] 만기일시상환
- [x] 거치기간
- [x] 월 단위 이자 계산·일할계산 제외
- [x] 금융 이벤트별 원 단위 반올림
- [x] 잔여원금
- [x] 총이자
- [x] 월별 상환액

### P0 — 개인정보

- [x] 주민등록번호 필드 없음
- [x] 계좌번호 필드 없음
- [x] 신용점수 필드 없음
- [x] 세션 내 계산
- [x] 원금액 로그 없음
- [x] 명시적 동의 없는 DB 저장 없음
- [x] 샘플 모드와 실제 입력 분리

### 대표 가상 사업장

- [x] 상권 하락·낮은 부채
- [x] 안정 상권·높은 상환부담
- [x] 상권 하락·현금 부족·기존 부채
- [x] 매출 0원
- [x] 신규 사업장
- [x] 단위 오류
- [x] CSV 오류

### 검증

- [x] 손계산 예제와 주별 결과 일치
- [x] 손계산 예제와 월별 결과 일치
- [x] 주·월 집계 관계 확인
- [x] 지급일 경계 확인
- [x] 상환방식별 정답 확인
- [x] 거치 종료 직전·직후 확인
- [x] 동일 입력 동일 결과
- [x] 오류 입력에 수정 필드 반환
- [x] 엔진 단독 테스트에서 LLM 호출 없음

### 완료 산출물

- [x] 입력 스키마
- [x] CSV 템플릿
- [x] 현금흐름 모듈
- [x] 대출 상환표 모듈
- [x] 샘플 사업장 JSON
- [x] 손계산 정답표
- [x] 입력 오류코드
- [x] 검증 보고서

### Gate RE3

- [x] 정책·ML 없이 기준 현금흐름 재현
- [x] 손계산 사례 전부 통과
- [x] 비용 중복 없음
- [x] 민감정보 비저장 확인
- [x] 계산식·반올림·날짜 규칙 문서화
- [x] 후속 단계 영향 검토와 필요 수정 완료

---

## RE Stage 4 — 정책 금융 이벤트 엔진

### 목표

공식 정책조건을 현금흐름에 적용할 수 있는 지급·비용감면·자부담·상환 이벤트로 변환한다.

### 상태 기록

| 항목 | 기록 |
| --- | --- |
| 담당자 | Codex 구현·검산 / 사용자 정책 가정 승인 |
| 시작일 | 2026-08-16 |
| 완료일 | 2026-08-16 |
| 상태 | 완료 — Gate RE4 통과 |
| 선행조건 | Gate RE2·RE3 |

### P0 — 공통 이벤트 계약

- [x] 정책 ID·버전
- [x] 정책 내부 하위상품 `event_id`
- [x] 연결 이벤트 `linked_event_id`·중복방지 키
- [x] 지원유형
- [x] 이벤트 날짜
- [x] 현금유입
- [x] 비용감면
- [x] 자부담
- [x] 신규부채 원금
- [x] 이자
- [x] 보증료·수수료
- [x] 공식값·사용자값·가정값 출처
- [x] 미확인 조건
- [x] 하위상품 미선택 시 대표 한도·평균 금리 생성 금지

### P0 — 보조금

- [x] 지급일 현금유입
- [x] 선지급·사후정산
- [x] 지원한도
- [x] 자부담
- [x] 적격 비용
- [x] 사용기간
- [x] 사후환급 전 선행현금

### P0 — 바우처

- [x] 현금유입으로 오처리 금지
- [x] 적격 비용 감소
- [x] 바우처 한도
- [x] 자부담률
- [x] 사용기한
- [x] 잔액 소멸 처리

### P0 — 이차보전

- [x] 적용 전 이자
- [x] 지원기간 이자
- [x] 지원 종료 후 이자
- [x] 월 이자절감액
- [x] 총이자절감액

### P0 — 정책자금 융자

- [x] 실행일 현금유입
- [x] 대출원금
- [x] 금리
- [x] 거치기간
- [x] 상환기간
- [x] 상환방식
- [x] 보증료·부대비용
- [x] 월 원리금
- [x] 잔여원금
- [x] 총이자

### P0 — 대환·만기 연장

- [x] 기존 상환일정
- [x] 변경 상환일정
- [x] 월 상환액 감소
- [x] 총기간 증가
- [x] 총이자 변화
- [x] 수수료

### P0 — 보증

- [x] 보증 자체 현금유입 금지
- [x] 실제 대출조건 없으면 금액효과 미산정
- [x] 보증한도·대상 표시
- [x] 금융접근 지원으로 분리

### P0 — 조건부 시나리오

- [x] 승인·지급 가정
- [x] 공고상 가장 이른 지급일
- [x] 사용자 지정 지급일
- [x] 지연 지급
- [x] 최대 지원액
- [x] 사용자 필요액
- [x] 승인되지 않음

### 검증

- [x] 보조금 손계산
- [x] 바우처 손계산
- [x] 이차보전 손계산
- [x] 정책융자 손계산
- [x] 대환 손계산
- [x] 사후환급 전 현금부족
- [x] 거치 종료
- [x] 정책기간 밖 이벤트 차단
- [x] 공식값·가정값 혼합 방지
- [x] 승인확률 출력 없음

### 완료 산출물

- [x] 금융 이벤트 스키마
- [x] 지원유형별 변환기
- [x] 지급·상환 스케줄
- [x] 정책 금융 이벤트 적용 계산 테스트
- [x] 가정 원장
- [x] 검산 보고서

### Gate RE4

- [x] 선정 정책의 금융 이벤트 재현
- [x] 공식조건과 가정값 분리
- [x] 대출 현금유입과 미래상환 동시 반영
- [x] 미확인 조건 임의 보완 없음
- [x] 승인·인과효과로 오해할 출력 없음
- [x] 후속 단계 영향 검토와 필요 수정 완료

---

## RE Stage 5 — 신규 외부데이터·Target v2·Quantile 모델

### 목표

상권×업종 집계 매출환경의 하방·기준·회복 범위를 생성하고 기존 Stage 6과 비교한다.

### 상태 기록

| 항목 | 기록 |
| --- | --- |
| 담당자 | 사용자 Target·데이터·모델 승인 / Codex 분석·구현 |
| 시작일 | 2026-08-16 |
| 완료일 | 2026-08-16 |
| 상태 | LightGBM Quantile 내부 시나리오 생성기 승인·사용자 화면의 평가 세부정보 제외·Gate RE5 통과 |
| 선행조건 | Gate RE1, RE3 엔진 사용 가능 |
| 학습 실행자 | 사용자 직접 실행, Codex의 모델 fit 금지 |
| 내부 홀드아웃 | 2025Q2 Feature·2025Q3~Q4 결과로 1회 평가 완료, Target 개방·모델 재선택 금지 |

### 필수 사용자 결정

- [x] 관측 단위: 기준분기×서울 상권코드×서비스 업종코드 유지
- [x] Target A: 다음 1분기 YoY 매출증감률
- [x] Target B: 다음 2분기 합산 YoY 매출증감률
- [x] 보조 Target: 다음 2분기 중 최저 YoY 매출증감률
- [x] 분모 0·결측: 해당 Target 결측, Panel 행·사유 플래그 보존
- [x] 극단값: 자동 Clipping·Winsorization 금지, 원값·플래그 보존
- [x] 신규·소멸: 누락을 0·폐업으로 추정하지 않고 Target·추론 가능성 분리
- [x] 개발 기준분기: 2021Q4~2024Q4
- [x] Validation Fold: 2024Q1~Q4 4개 expanding-window
- [x] Purge: 직전 기준분기 1개, 2025Q1은 2025Q2 홀드아웃 전 Purge
- [x] 평가 지표: 연속형·Quantile 지표 주평가, AUROC·AUPRC는 동결 v1 참고 부록
- [x] 모델 후보: 단순·업종 Median·정규화 선형·LightGBM·CatBoost, XGBoost 조건부
- [x] 내부 홀드아웃: 기준 2025Q2, 결과 2025Q3·Q4
- [x] 새 독립 감사기간: 현재 미확보, RE5는 한계를 표시한 단일 ML 후보이며 기존 Stage 6과 병행하지 않음

### Target v2 후보

- [x] 다음 1분기 전년동기 대비 매출증감률 정의 승인
- [x] 다음 2분기 합산 전년동기 대비 매출증감률 정의 승인
- [x] 다음 2분기 중 최저 전년동기 대비 매출증감률 정의 승인
- [x] 전분기 대비 Target은 EDA·Challenger로만 비교
- [x] Target별 업종·기간 분포 확인 — `reports/re_stage5/target_distribution_by_*.csv`
- [x] A는 13주, B는 6개월 집계환경으로 해석하고 RE7에서 기본 100% 참고 적용·사용자 조정·직접 충격률을 승인

### 승인된 기간·평가·비교 계약

- [x] 2025Q1은 독립 학습 관측에서 제외하지만 이전 Target 결과·홀드아웃 과거 Feature 사용은 허용
- [x] 2025Q3·Q4는 RE5 처리·Feature·모델 선택에서 격리하고 마지막 내부 홀드아웃에만 사용
- [x] 2025Q3·Q4를 새 독립 감사라고 표현하지 않음
- [x] MAE·Median AE·RMSE·Mean Error
- [x] P10·P50·P90 Pinball Loss와 실제 도달률
- [x] P10~P90 Coverage·평균 구간 폭·Interval Score
- [x] Spearman·상승하락 방향 일치율·Quantile Crossing 비율
- [x] Fold·업종 안정성과 현금흐름·정책선택 민감도
- [x] 기존 LightGBM은 재학습·서비스 입력 없이 과거 Benchmark·감사 증거로만 보존
- [x] 기존 AUROC·AUPRC는 참고 부록이며 Quantile 모델 선택 기준이 아님

### P0 — 기존 데이터 Baseline

- [x] Stage 3 Panel v1 읽기
- [x] 기존 197개 Feature Baseline 후보 계약·실행기 생성
- [x] Stage 4.5 파생 Feature 정의 134개 재생성·승인 197개 Feature 개발/홀드아웃 스키마 확인
- [x] 단순 계절 Baseline
- [x] 업종별 Median Baseline
- [x] 시간순 Fold
- [x] 준비단계 누수검증 — 개발 최대 2024Q4·Holdout Target 미개방
- [x] Panel v1 해시 보존

### P0 — 서울 상권 1~9종 재사용 계약

- [x] S-01 추정매출은 사용자 승인 전 Target v2를 생성하지 않음
- [x] S-01은 승인 후 분기×상권×업종 단위에서 다음 1분기 YoY·다음 2분기 합산 YoY·미래 최저 YoY 후보를 각각 생성
- [ ] S-02 점포는 같은 분기×상권×업종 키로 Left Join하고 점포수·유사업종점포수·개폐업·프랜차이즈 및 과거 변화 후보 생성
- [ ] S-03 영역은 좌표계·도형 유효성을 검사한 상권 Polygon으로 보존하고 상가·인허가·행사의 Point-in-Polygon에 사용
- [ ] S-04 길단위인구는 분기×상권 집계 후 해당 상권의 모든 업종행에 Left Join하고 시간대·요일·성별·연령별 변화 후보 생성
- [ ] S-05 상권변화지표는 분기×상권 Left Join 후 변화유형·운영기간·폐업기간과 과거 변화 후보 생성
- [ ] S-06 상주인구는 분기×상권 Left Join 후 인구·가구 구성과 과거 변화 후보 생성
- [ ] S-07 직장인구는 분기×상권 Left Join 후 성별·연령별 직장인구와 과거 변화 후보 생성
- [ ] S-08 집객시설은 분기×상권 Left Join 후 교통·교육·의료·유통시설 수와 과거 변화 후보 생성
- [ ] S-09 아파트는 분기×상권 Left Join 후 단지·세대·면적·가격대·평균시가와 과거 변화 후보 생성
- [ ] S-02~S-09는 예측시점까지 공개된 현재·과거 값만 사용하고 미래정보 Feature 제거
- [x] Panel v1을 덮어쓰지 않고 Panel v2·Manifest·해시를 별도 생성

### P1 — 소진공 상가정보 과거 Snapshot·운영 API 분리

- [ ] 과거 분기 Snapshot 파일: https://www.data.go.kr/data/15083033/fileData.do
- [ ] 상가정보 업종코드: https://www.data.go.kr/data/15067631/fileData.do
- [ ] 운영 API: https://www.data.go.kr/data/15012005/openapi.do
- [ ] 활용신청·호출량 확인
- [ ] 기준시점 확인
- [ ] 상가업소번호 변경이력 확인
- [ ] 업종코드 체계 확인
- [ ] 서울 상권업종과 매핑표 생성
- [ ] 좌표 품질 확인
- [ ] 중복 업소 확인
- [ ] 시간순 사용 가능성 확인
- [ ] Snapshot 기준일을 분기로 변환
- [ ] 좌표를 S-03 상권 Polygon에 공간결합
- [ ] 상가정보 업종코드를 서울 서비스업종 코드로 매핑
- [ ] 분기×상권×업종별 영업업소수·업소밀도·분기 순증감·업종다양성 후보 생성
- [ ] 최신 운영 API 응답을 과거분기 Feature로 소급 사용하지 않음
- [ ] 운영 API는 RE8의 요청시점 최신 주변 업소 Context로 별도 전달
- [ ] Baseline 대비 단독 Ablation

### P1 — LOCALDATA 인허가 변화

- [ ] 2026년 공공데이터포털 업종별 API 목록·매핑자료: https://www.data.go.kr/bbs/ntc/selectNotice.do?originId=NOTICE_0000000004566
- [ ] LOCALDATA 전체분·업종별·지역별 CSV: https://www.localdata.go.kr/devcenter/dataDown.do?selectCategoryId=05&selectGroupId=31
- [ ] 일반음식점 API: https://www.data.go.kr/data/15154916/openapi.do
- [ ] 휴게음식점 API: https://www.data.go.kr/data/15154921/openapi.do
- [ ] 미용업 API: https://www.data.go.kr/data/15154918/openapi.do
- [ ] 세탁업 API: https://www.data.go.kr/data/15154927/openapi.do
- [ ] 통신판매업 API: https://www.data.go.kr/data/15154963/openapi.do
- [ ] 전체분과 변화분 구분
- [ ] 영업상태 코드 확인
- [ ] 개업일·폐업일 확인
- [ ] 업종별 커버리지
- [ ] 중복 변화 이벤트
- [ ] 서울 상권 공간매핑
- [ ] 예측시점 이후 이벤트 제거
- [ ] 인허가일·폐업일·변경일을 분기로 변환
- [ ] 좌표 우선·주소 보조 방식으로 S-03 상권 Polygon에 결합
- [ ] 인허가 업종을 서울 서비스업종으로 매핑
- [ ] 분기×상권×업종별 신규 인허가수·폐업수·순증감·활성업소 추정·최근 폐업증가 후보 생성
- [ ] 늦은 행정등록과 과거상태 재구성 실패가 만드는 누수 검사
- [ ] Baseline 대비 단독 Ablation

### P2 — 날씨·공휴일·행사

- [ ] ASOS 브라우저 다운로드: https://data.kma.go.kr/data/grnd/selectAsosRltmList.do?pgmNo=36
- [ ] ASOS 일자료 API: https://www.data.go.kr/data/15059093/openapi.do
- [ ] 한국천문연구원 특일·공휴일 API: https://www.data.go.kr/data/15012690/openapi.do
- [ ] 서울시 문화행사 API: https://data.seoul.go.kr/dataList/OA-15486/A/1/datasetView.do
- [ ] 출처와 라이선스
- [ ] 기준시점
- [ ] ASOS 서울 108 지점 일자료를 분기로 집계하고 같은 분기의 모든 상권행에 Join
- [ ] ASOS 평균·극한기온·강수량·강수일수·폭염·한파일수·습도·일조 후보 생성
- [ ] 공휴일 날짜를 분기로 집계하고 주말중복·대체공휴일·연속휴일 계산
- [ ] 공휴일수·평일공휴일수·최장연휴 후보 생성
- [ ] 문화행사 기간을 분기에 배분하고 좌표·주소를 S-03 상권 Polygon에 결합
- [ ] 문화행사 중복을 제거하고 행사수·행사일수·무료행사수·인접행사 노출 후보 생성
- [ ] 업종별 영향 방향을 사전에 확정값으로 주입하지 않고 검증 결과로 판단
- [ ] 누수검증
- [ ] ASOS 단독 Ablation
- [ ] 공휴일 단독 Ablation
- [ ] 문화행사 단독 Ablation
- [ ] 검증된 후보의 결합 Ablation

### P2 — 서울 실시간 도시데이터

- [ ] 공식 API·파일 페이지: https://data.seoul.go.kr/dataList/OA-21285/A/1/datasetView.do
- [ ] 주요 121개 장소 목록 확인
- [ ] 장소 영역과 S-03 상권 Polygon 매핑
- [ ] 과거 데이터 확보 가능성
- [ ] 수집주기·지연
- [ ] 비대상 상권 처리
- [ ] 호출시각·지연·장소 Coverage를 응답 Metadata에 포함
- [ ] 혼잡·교통·날씨·행사 값을 운영 Context로만 별도 전달
- [ ] 서울 전체 핵심 Feature로 사용 금지
- [ ] 제한 지역 실험 표시

### 데이터 Ablation 순서

- [ ] 기존 Panel Baseline
- [ ] + 상가정보
- [ ] + 인허가 변화
- [ ] + ASOS
- [ ] + 공휴일
- [ ] + 문화행사
- [ ] 실시간 도시데이터는 모델 Ablation과 분리한 운영 Context 평가
- [ ] 각 단계 동일 Fold·Target·지표
- [ ] 각 단계 성능·최악 Fold·업종별 안정성·Coverage·처리시간 비교
- [ ] 각 단계의 P10·P50·P90 변화가 13주·6개월 현금흐름에 주는 민감도 비교
- [ ] 증분효과 없는 데이터 제거
- [ ] 누수·Coverage 문제 데이터 제거

### 데이터별 최종 전달·제외 확인

- [ ] 정책 원문·API가 RE2에서 Metadata·Rule·Event·RAG Chunk로 변환되어 RE4·RE6·RE7에 전달됨
- [ ] 사용자 입력이 RE3에서 날짜별 기준 현금흐름으로 변환되어 RE4·RE7에 전달됨
- [ ] 서울 상권 1~9종이 RE5에서 Panel v2·Target v2 후보로 분리 생성됨
- [ ] 상가·인허가·날씨·공휴일·행사는 데이터군별 Ablation Panel과 Manifest로 분리됨
- [ ] 실시간 도시데이터가 RE8 제한지역 운영 Context로만 전달됨
- [ ] 다운로드 원본과 모델 채택 여부가 별도 상태로 기록됨
- [ ] QA·누수검증·Ablation·Gate 탈락 데이터는 원본과 검증기록만 보존하고 서비스 계산에서 제외됨

### 모델 후보

- [x] 계절 단순 Baseline
- [x] 업종별 Median Baseline
- [x] Regularized Linear Quantile — 현재 Feature 조합에서 수치 붕괴 확인
- [x] LightGBM Quantile
- [x] CatBoost Quantile 또는 MultiQuantile
- [x] 지원 안정성 확인 후 XGBoost Quantile
- [ ] 후보 목록 사용자 승인 후 학습
- [x] 후보 목록 사용자 승인 완료
- [x] 사용자 직접 실행 CV Runner·터미널 진행 로그·checkpoint 재개 구현
- [x] 최초 인계 시 Codex 모델 fit 0회·`--dry-run` 검증
- [x] 사용자 요청에 따른 1-task 제한 실행 — 계절 Baseline Fold 1 `1/72` 완료 후 자동 중단
- [x] 사용자 직접 재개로 전체 `72/72` 완료·Checkpoint JSON/Parquet 각 72개 무결성 검증
- [x] LightGBM Quantile 내부 Holdout 평가 후보 사용자 승인
- [x] 기존 Stage 6과 RE5 Quantile의 최종 서비스 역할 사용자 승인 — RE5 단일 ML 후보, 기존 모델 서비스 제외·미재학습
- [x] 내부 Holdout 실행 요청·평가기 준비 — 학습·평가는 사용자 직접 실행
- [x] `-DryRun` — LightGBM 9개 회귀기·197개 Feature·CV checkpoint 12개 확인, Target 개방·학습 0회
- [x] 명시적 `-ConfirmOpenHoldout`·개방 전 접근기록·동일 계약 재개·완료 후 재실행 금지
- [x] 사용자가 내부 Holdout 실제 실행 완료 — 2026-08-16 21:11 KST, 3개 Target·9개 회귀기 완료

### 내부 Holdout 결과 요약

- [x] Target A: MAE `0.8963`, Median AE `0.1338`, P10~P90 Coverage `69.39%`, Spearman `0.5686`
- [x] Target B: MAE `0.4554`, Median AE `0.1187`, P10~P90 Coverage `71.03%`, Spearman `0.5190`
- [x] 보조 Target: MAE `0.3250`, Median AE `0.1158`, P10~P90 Coverage `70.16%`, Spearman `0.5334`
- [x] 개발 CV 대비 Holdout MAE `15.40~32.36%` 증가, Coverage `6.93~8.39%p` 감소
- [x] P10 실제 도달률 `8.20~9.84%`는 명목 10%와 가깝지만 P50 `36.09~39.99%`, P90 `77.55~80.21%`로 중앙·상단이 실제보다 낮은 방향의 편향 확인
- [x] 예측 64,356행·중복 0·비유한값 0·보정 후 Crossing 0, 지표 재계산 오차 `4.5e-16` 이하
- [x] 7개 Manifest 출력·3개 Checkpoint·3개 Artifact 해시·바이트·계약 일치, 독립 프로세스 호환 로더 검증 통과
- [x] 상세 검증: [`verification.md`](./reports/re_stage5/holdout/verification.md)

### 개발 CV 결과 요약

- [x] Target A 평균 MAE: XGBoost `0.7463`, LightGBM `0.7501`, CatBoost `0.7701`
- [x] Target B 평균 MAE: XGBoost `0.3434`, LightGBM `0.3440`, CatBoost `0.3502`
- [x] 보조 Target 평균 MAE: XGBoost `0.2809`, LightGBM `0.2816`, CatBoost `0.2856`
- [x] LightGBM은 업종 Median 대비 평균 MAE `13.57~19.93%` 개선, 세 Target의 4개 Fold 모두 개선
- [x] XGBoost의 LightGBM 대비 MAE 이득은 `0.17~0.51%`; LightGBM은 세 Target 모두 Interval Score가 낮고 총 Fit 시간이 약 8.4배 짧음
- [x] Holdout 개방 전 계약/Feature 잠금 및 완료 후 계약/예측 SHA-256·행 수·중복·유한값·보정 후 순서 검증 통과
- [x] 상세 검증: [`verification.md`](./reports/re_stage5/cv/verification.md)

### Quantile 출력

- [x] P10 하방
- [x] P50 기준
- [x] P90 회복
- [x] P10≤P50≤P90 확인
- [x] Quantile crossing 처리규칙
- [x] 업종별 구간폭 확인
- [x] P10·P50·P90 산출·Quantile Crossing 기록·행별 정렬 보정 코드 단위 테스트

### 평가

- [x] MAE
- [x] Median Absolute Error
- [x] P10 Pinball Loss
- [x] P50 Pinball Loss
- [x] P90 Pinball Loss
- [x] P10~P90 Coverage
- [x] 평균 구간폭
- [x] Fold별 최악값
- [x] Fold 표준편차
- [x] 업종별 MAE·Pinball·Coverage
- [ ] 현금 고갈 시점 민감도
- [ ] 정책 선택 변화 민감도
- [x] 전체 연속형·Quantile·구간·순위·방향·교차 지표 계산 코드 단위 테스트

### 개인 사업장 적용 경계

- [x] 상권×업종 집계환경 문구
- [x] 개별 점포 매출예측 표현 금지
- [x] 사용자-facing 명칭을 `상권환경 스트레스 시나리오`로 고정
- [x] `내 가게 예상매출` 표현 금지
- [x] 사용자 화면에는 `하방·기준·회복`만 표시하고 P10·P50·P90·Coverage·Pinball Loss·Holdout 수치는 내부 QA로만 보존
- [ ] 집계 변화율 100% 적용 시나리오
- [ ] 사용자 조정 적용률
- [ ] 사용자 직접 충격률
- [ ] 적용방법과 가정 기록

### 독립 테스트

- [x] 기존 이진 Target·평가지표를 Quantile 모델 선택에 재사용 금지
- [x] 2025Q3·Q4는 Target v2 내부 시간 홀드아웃으로만 사용 승인
- [x] 최신 추가분기 확인: 추정매출은 2025Q4까지, 2026Q1·Q2 미확보
- [x] 새 독립기간 미확보 상태 사용자 확인
- [x] 모델 선택 전 2025Q2 내부 홀드아웃 Feature 잠금·Target 미개방
- [x] 독립기간 미확보 상태 표시
- [x] 내부 Holdout 결과를 본 뒤 모델 재선택 금지 — LightGBM 고정, Stage 6 재활성화 금지

### 기존 Stage 6 서비스 제외·RE5 활성화 Gate

- [x] 단순 Baseline보다 오차 개선
- [x] Fold 전반 개선 재현
- [x] Coverage 한계를 내부 QA로 수용 — 사용자 화면·자격·승인·정책순위에는 사용하지 않고 시나리오 초기값에만 사용
- [x] 업종별 불안정성은 사용자 직접 충격률 Fallback과 내부 모니터링 대상으로 격리
- [x] 신규 데이터 증분효과는 현재 Baseline 모델의 MVP 사용을 막지 않는 후속 개선으로 분리
- [x] 현금흐름에는 하방·기준·회복 초기값으로만 전달하고 사용자가 직접 조정 가능
- [x] 배포 시 호환 로더·Fallback·내부 지표 비노출을 필수 조건으로 승인
- [x] 새 독립 감사 미확보를 공개 주장 한계와 후속 개선으로 유지하고 MVP 구현 차단조건에서 제외
- [x] 서비스 역할 사용자 승인 — 병행하지 않음, 기존 Stage 6 미재학습·감사 증거 보존

### 완료 산출물

- [x] Target v2 정의서
- [x] Panel v2
- [x] Panel v2 Manifest
- [x] Quantile EDA
- [x] Feature contract v2
- [x] Fold membership
- [x] Baseline 비교
- [x] 후보 모델 비교
- [ ] 데이터 Ablation
- [x] Quantile 보정
- [ ] 서비스 민감도 보고서
- [x] 모델 v2 Artifact — Target별 P10·P50·P90 3개씩 총 9개 추정기, 해시·계약·독립 프로세스 로딩 검증
- [ ] Model Card
- [x] 사용자 직접 내부 Holdout 실행기·Runbook

### Gate RE5

- [x] Target·기간·지표·모델 후보 승인
- [x] 누수검증 통과
- [x] 기존 Panel Baseline 완료·신규 외부데이터 Ablation은 후속 개선으로 분리
- [x] 독립검증 상태 정직하게 표시 — 새 독립기간 미확보·RE5 단일 후보의 검증 한계 표시
- [x] 기존 Stage 6의 최종 지위 승인 — 서비스 제외·미재학습·감사 증거 보존
- [x] 후속 단계 영향 검토와 필요 수정 완료 — `reports/re_stage5/downstream_impact_review.md`

---

## RE Stage 6 — 공식 자격판정·RAG·금융 AI 설명

### 목표

공식 조건으로 정책 후보를 판정하고, 공식 근거를 검색해 계산결과와 Trade-off를 설명한다.

### 상태 기록

| 항목 | 기록 |
| --- | --- |
| 담당자 | Codex 구현·평가 / 사용자 답변범위 승인 |
| 시작일 | 2026-08-16 |
| 완료일 | 2026-08-16 |
| 상태 | `re6-v1` 구현·검증 완료, Gate 통과 |
| 선행조건 | Gate RE2·RE4 |

### P0 — 자격상태

- [x] 적격
- [x] 부적격
- [x] 추가 확인 필요
- [x] 접수기간 종료
- [x] 현재성 확인 불가
- [x] `적격`이 승인 가능성이 아니라는 문구

### P0 — 자격규칙

- [x] 지역
- [x] 업종
- [x] 업력
- [x] 매출
- [x] 상시근로자
- [x] 자금용도
- [x] 기존 수혜
- [x] 체납
- [x] 연체·신용조건
- [x] 신청기간
- [x] 예산 소진
- [x] 확인 불가능 조건

### P0 — 세션 한정 자격 프로필

- [x] 현금흐름 입력과 자격판정 입력 분리
- [x] 소재지·업종·개업일·대표자 연령구간
- [x] 2024·2025 및 반기 매출 비교·2025 연매출 구간
- [x] 상시근로자수·임차/점포형 여부
- [x] 휴폐업 상태·폐업예정일
- [x] 세금 완납·재해확인서·기존 지원이력
- [x] 재창업·채무조정·성실상환 상태
- [x] 기존 대출 실행일·금리·만기연장 애로
- [x] 정확한 신용점수 대신 `NCB 839 이하`, `NCB 919 이하`를 `예/아니오/모름`으로 입력
- [x] 세션 종료 시 원값 폐기·로그 및 DB 저장 금지

### P0 — RAG 문서

- [x] 공식 공고 본문
- [x] 공식 첨부문서
- [x] 공식 신청페이지
- [x] 공식 FAQ — 공식 문서에 포함된 문답 Chunk만 사용, 없는 정책은 생성하지 않음
- [x] 공식 문의처
- [x] 민간 블로그를 자격근거에서 제외

### P0 — Chunk Metadata

- [x] `policy_id`
- [x] `policy_version`
- [x] `source_type`
- [x] `source_url`
- [x] `page_or_section`
- [x] `effective_from`
- [x] `effective_to`
- [x] `retrieved_at`
- [x] `content_hash`

### P0 — 검색

- [x] 정책 ID 필터
- [x] 버전 필터
- [x] 적용기간 필터
- [x] 지원대상 질의
- [x] 금리·상환 질의
- [x] 지급·환급 질의
- [x] 제외조건 질의
- [x] 신청방법 질의
- [x] 근거 없는 경우 `확인 불가`

### P0 — LLM 출력

- [x] 결론
- [x] 사용한 사용자 입력
- [x] 적용한 정책조건
- [x] 현금흐름 변화
- [x] 부채·이자 변화
- [x] 미확인 조건
- [x] 공식 근거
- [x] 기준일
- [x] 최종 기관 확인 안내

### 금지 기능

- [x] LLM 산술계산 금지 테스트
- [x] LLM 상환표 생성 금지 테스트
- [x] LLM 자격조건 생성 금지 테스트
- [x] LLM 승인확률 생성 금지 테스트
- [x] LLM 정책 수혜 인과효과 주장 금지 테스트
- [x] LLM 순위 변경 금지 테스트

### 평가세트

- [x] 적격 사례
- [x] 부적격 사례
- [x] 추가 확인 사례
- [x] 접수 종료 사례
- [x] 근거 조항 질문
- [x] 지급·상환 질문
- [x] 원문에 없는 조건 질문
- [x] 오래된 정책 질문

### 평가

- [x] 자격 규칙 정답률 — 수작업 정답 `20/20`
- [x] 근거 검색 적중률 — Hit@3 `8/8`, MRR `0.7917`
- [x] 인용 정확성 — 기대 공식 Chunk Hit@3 `8/8`, URL·위치·해시 필수
- [x] 공식 문서에 없는 조건 생성 0건
- [x] 계산값 변경 0건
- [x] 기준일·버전 누락 0건
- [x] 승인 확정표현 0건

### 완료 산출물

- [x] 자격 규칙 엔진
- [x] 문서 전처리기
- [x] 검색 인덱스
- [x] 평가 질문·정답
- [x] RAG 평가보고서
- [x] LLM 출력 스키마
- [x] 안전 테스트

### Gate RE6

- [x] 자격 정답사례 통과
- [x] 공식 근거·기준일·버전 반환
- [x] LLM이 계산·자격·순위를 변경하지 않음
- [x] 미확인 조건 추측 없음
- [x] 후속 단계 영향 검토와 필요 수정 완료 — `reports/re_stage6/downstream_impact_review.md`

---

## RE Stage 7 — 정책 개입안 비교와 의사결정 엔진

### 목표

무대응과 정책 개입안을 같은 현금흐름 기준에서 비교하고 사용자 목표별 대안을 제시한다.

### 상태 기록

| 항목 | 기록 |
| --- | --- |
| 담당자 | 사용자 목표 승인 / Codex 구현·검산 |
| 시작일 | 미정 |
| 완료일 | 미정 |
| 상태 | `re7-contract-v1` 승인 완료·사용자 지시에 따라 비교엔진 구현 미착수 |
| 선행조건 | Gate RE3·RE4·RE6, RE5 결과 또는 사용자 직접 충격률 Fallback |

### P0 — RE6 결과 전달·후보상태 계약

- [x] 자격판정과 접수상태를 별도 값으로 보존
- [x] `입력 기준 적격 후보 + 기준일상 접수 가능`은 `지금 비교 가능`
- [x] `추가 확인 필요` 또는 `접수 가능 여부 확인 필요`는 `확인 후 비교`
- [x] `부적격` 또는 `접수기간 종료`는 `제외`
- [x] `확인 후 비교`는 사용자가 조건충족 가정을 명시한 경우에만 시뮬레이션
- [x] 조건부 정책은 기본 1순위·빠른실행 1순위에서 제외
- [x] Rule ID·Chunk ID·BM25 점수·검색순위는 사용자 화면에서 숨김
- [ ] RE7 시나리오 생성기와 정렬 엔진에 후보상태 적용

### P0 — 승인된 정책조합·시나리오·안전현금 계약

- [x] 정책 조합 상태를 `조합 가능·확인 필요·조합 불가`로 고정
- [x] 공식 근거로 확인된 조합만 기본 복합안에 포함
- [x] 확인되지 않은 조합은 사용자 명시적 가정이 있을 때만 조건부 비교
- [x] 확인 필요 조합의 기본 1순위·빠른실행 1순위 차단
- [x] 중복지원 금지 또는 같은 지출 중복 보전 조합 제외
- [x] 13주는 RE5 Target A, 6개월은 RE5 Target B 사용
- [x] 상권환경 변화율 기본 적용률 100%·참고 스트레스 계산 표시
- [x] 사용자 적용률 조정·직접 충격률 덮어쓰기·가정 기록 허용
- [x] 안전현금 권장값을 향후 4주 필수지출 합계로 정의
- [x] 상세 입력은 향후 28일 필수지출 일정, 간편 입력은 월 고정비·월 대출상환액·필수 변동비 추정액 사용
- [x] 안전현금 권장값 사용자 수정 허용·입력 부족 시 직접 입력 요청
- [x] 사용자 지시에 따라 계약만 확정하고 RE7 구현은 시작하지 않음

### P0 — 최소 비교안

- [ ] 무대응
- [ ] 비용절감
- [ ] 보조금 또는 바우처
- [ ] 이차보전 또는 대환
- [ ] 신규 운영자금
- [ ] 비차입 지원 + 최소대출 복합안

### P0 — 13주 생존 시뮬레이션 Hero 데이터

- [x] Hero 구성 권장안 사용자 승인 — 2026-08-16
- [ ] 지급일정이 포함된 검증 가상 사업장 사용
- [ ] `03_declining_cash_shortage.json`을 출발점으로 상세 대출·지급일정 보완
- [ ] 정책 적용 전 서로 다른 현실적 상세 샘플 2~3개 입력 동결
- [ ] `생존`을 현금잔액 0원 이상 유지기간으로 정의하고 실제 존속·폐업 예측과 구분
- [ ] 무대응·보조금·비용절감·대환·정책자금·복합안을 같은 현금흐름 축에서 비교
- [ ] 비차입 후보로 위기 소상공인 Track2 사후정산 보조금 검토
- [ ] 부채구조 개선 후보로 소상공인 정책자금 대환대출 검토
- [ ] 신규자금 후보로 서울시 긴급자영업자금 검토
- [ ] 복합안은 비차입 지원 + 비용 5% 절감 + 안전현금 최소대출
- [ ] 자격·동시수혜·중복지원·지급일·승인금액 가정 검증 후 조합 확정
- [ ] 동시 현금곡선은 무대응·비차입·신규자금·복합안 최대 4개
- [ ] 대환·비용절감은 토글 제공
- [ ] 13주 현금곡선을 중심에 표시
- [ ] 6개월 유지 여부·신규부채·월상환·총이자를 함께 표시
- [ ] 월 금액만 입력한 간편모드 결과를 정확한 주차 데모로 사용 금지
- [ ] 원하는 홍보 숫자에 맞춘 샘플 입력 역산 금지

### P0 — 비교 지표

- [ ] 13주 말 현금
- [ ] 6개월 말 현금
- [ ] 최저 현금
- [ ] 현금 고갈 시점
- [ ] 신규 차입액
- [ ] 월 원리금
- [ ] 총이자
- [ ] 총상환의무
- [ ] 지원금·비용감면
- [ ] 지급 지연
- [ ] 신청 마감일
- [ ] 추가 확인조건 수

### P0 — 사용자 목표

- [ ] 최소부채
- [ ] 최장생존
- [ ] 최소상환
- [ ] 빠른실행
- [ ] 승인된 4주 필수지출 기반 안전현금 제안값과 직접 입력 UI 구현
- [ ] 목표별 결과 의미 설명

### P0 — 비교규칙

- [ ] 임의 100점 가중합 금지
- [ ] 신규대출 자동 우선 금지
- [ ] 비차입 지원 우선 비교
- [ ] 지배되는 대안 식별
- [ ] Trade-off 복수 표시
- [ ] 동시수혜 제한
- [ ] 중복지원 제한
- [ ] 승인되지 않음 시나리오
- [ ] 지급 지연 시나리오
- [ ] 부적격·접수 종료 정책 비교·정렬 제외
- [ ] 추가 확인·현재성 미확인 정책의 명시적 조건부 시뮬레이션
- [ ] 조건부 정책의 기본 1순위·빠른실행 1순위 차단

### P1 — 실행계획

- [ ] 지금 확인할 조건
- [ ] 신청기한
- [ ] 준비서류
- [ ] 지급 전 필요한 현금
- [ ] 정책 실패 시 대안
- [ ] 대출이 필요한 경우 최소 규모
- [ ] 공식 문의처

### 검증

- [ ] 최소부채 정답
- [ ] 최장생존 정답
- [ ] 최소상환 정답
- [ ] 빠른실행 정답
- [ ] 지배되는 대안 처리
- [ ] 정책조합 중복
- [ ] 지급지연
- [ ] 승인실패
- [ ] 대출 현금유입과 미래상환 동시 표시
- [ ] 목표 변경 시 결과 재현

### 완료 산출물

- [ ] 시나리오 생성기
- [ ] 대안 비교표
- [ ] 목표별 정렬 엔진
- [ ] Pareto 엔진
- [ ] 실행계획 생성기
- [ ] 대표 시나리오 보고서

### Gate RE7

- [ ] 무대응 포함 동일 기준 비교
- [ ] 목표별 결과 검산
- [ ] 대출 미래부담 누락 없음
- [ ] 공식값·사용자값·가정값 구분
- [ ] 임의 적합도 백분율 없음
- [ ] 후속 단계 영향 검토와 필요 수정 완료

---

## RE Stage 8 — API·웹 화면·전체 통합

### 목표

심사자가 웹에서 입력부터 정책금융 영향 비교와 실행계획까지 완료하고, 첫 화면의 13주 생존 시뮬레이션에서 핵심 차이를 30초 안에 이해할 수 있게 한다.

### 상태 기록

| 항목 | 기록 |
| --- | --- |
| 담당자 | Codex 구현·테스트 / 사용자 화면 승인 |
| 시작일 | 미정 |
| 완료일 | 미정 |
| 상태 | 미착수 |
| 선행조건 | Gate RE3·RE4·RE6·RE7 |

### P0 — API 계약

- [ ] Health
- [ ] 서비스 계약
- [ ] 동결된 RE1의 옛 명칭을 보존하되 현재 API·화면 서비스명은 `정책금융 영향 시뮬레이터`로 이관
- [ ] 상권 목록
- [ ] 업종 목록
- [ ] 기준 현금흐름
- [ ] 외부환경 시나리오
- [ ] 정책 자격
- [ ] 정책금융 영향 시뮬레이션
- [ ] 대안 비교
- [ ] AI 질의응답

### P0 — 공통 반환

- [ ] 요청 ID
- [ ] 기준일
- [ ] 현금흐름 엔진 버전
- [ ] 정책 데이터 버전
- [ ] 모델 버전
- [ ] 가정 원장
- [ ] 기준 현금흐름
- [ ] 외부 시나리오
- [ ] 자격결과
- [ ] 개입결과
- [ ] 비교결과
- [ ] 실행계획
- [ ] 공식 근거
- [ ] 한계
- [ ] 자격판정과 접수상태를 `eligibility_status`·`availability_status`로 분리
- [ ] `candidate_state`·`reason_summary`·`items_to_confirm`
- [ ] `as_of_date`·`policy_version`·공식 공고/신청 URL
- [ ] Rule ID·Chunk ID·BM25 점수·검색순위는 사용자 응답에서 제외

### P0 — 화면 1 서비스 안내

- [ ] 서비스가 하는 일
- [ ] 하지 않는 일
- [ ] 개인정보 비저장
- [ ] 샘플 모드
- [ ] `AI가 미래를 예측하고 최적 정책을 추천` 금지
- [ ] 기존 서비스 대비 차별화 두 문장 표시

### P0 — 화면 2 사업장 선택

- [ ] 서울 상권
- [ ] 업종
- [ ] 주소 자동매핑 또는 직접 선택
- [ ] 영업기간

### P0 — 화면 3 재무 입력

- [ ] 간편 입력
- [ ] CSV 업로드
- [ ] 단위 안내
- [ ] 입력 오류 수정
- [ ] 월 금액만 입력·일정 보완 입력·상세 CSV의 결과 정밀도 차이 안내

### P0 — 화면 4 기준 현금흐름

- [ ] 13주 생존 시뮬레이션 Hero 그래프
- [ ] 6개월 그래프
- [ ] 최저 현금
- [ ] 간편 추정 범위 또는 일정 기반 현금 고갈 시점
- [ ] 기존 상환일정
- [ ] 입력 수준·일정 가정·불확실성

### P0 — 화면 5 상권환경 스트레스 시나리오

- [ ] 하방·기준·회복 시나리오 또는 사용자 직접 충격률
- [ ] P10·P50·P90·Coverage·내부 Holdout 수치가 사용자 화면에 노출되지 않음
- [ ] 집계모델 한계
- [ ] `내 가게 예상매출` 표현 금지
- [x] 기존 Stage 6 보조표시 안 함
- [ ] 모델 사용 불가 시 사용자 직접 충격률 Fallback

### P0 — 화면 6 정책 자격

- [ ] 지금 비교 가능한 정책
- [ ] 확인 후 비교할 정책
- [ ] 제외된 정책
- [ ] 판정 이유·확인할 항목
- [ ] 접수기간·공식 근거·공식 링크
- [ ] `조건을 충족했다고 가정하고 비교` 선택

### P0 — 화면 7 정책금융 영향 비교

- [ ] 무대응 현금곡선
- [ ] 개입안 현금곡선
- [ ] 신규부채
- [ ] 월상환
- [ ] 총이자
- [ ] 지급지연
- [ ] 목표 선택

### P0 — 화면 8 실행계획·AI

- [ ] 우선 확인조건
- [ ] 신청기한
- [ ] 필요서류
- [ ] 공식 링크
- [ ] 가정과 한계
- [ ] 후속 질문

### P0 — 오류와 Fallback

- [ ] 지원하지 않는 상권·업종
- [ ] 최신 Feature 없음
- [ ] 정책 접수 종료
- [ ] 정책조건 미확인
- [ ] CSV 오류
- [ ] 단위 오류
- [ ] 현금흐름 계산 불가
- [ ] 외부모델 실패 시 사용자 충격률
- [ ] RAG 실패 시 계산결과·공식링크 유지
- [ ] LLM 실패 시 구조화 결과 유지
- [ ] Fact-lock 검증 실패 LLM 응답 폐기

### P0 — 보안·로그

- [ ] 환경변수 비밀키
- [ ] 민감 입력 로그 제외
- [ ] 세션 자격 프로필 원값·정확한 신용점수 로그/DB/검색 인덱스 저장 금지
- [ ] 요청 크기 제한
- [ ] CSV 파일 형식 제한
- [ ] Prompt Injection 방어
- [ ] 정책 문서와 사용자 지시 분리
- [ ] 오류에 내부 경로·키 노출 금지

### 검증

- [ ] End-to-End 정상 흐름
- [ ] 동일 입력 결정론
- [ ] API·그래프 숫자 일치
- [ ] 모바일 핵심 화면
- [ ] 데스크톱 핵심 화면
- [ ] 민감정보 로그 미기록
- [ ] 외부서비스 장애 Fallback
- [ ] 샘플 모드 재현

### 완료 산출물

- [ ] 통합 API
- [ ] 웹 프론트엔드
- [ ] API 명세
- [ ] 기능명세서 초안
- [ ] End-to-End 테스트
- [ ] 화면별 샘플
- [ ] 버전 Manifest

### Gate RE8

- [ ] 입력부터 실행계획까지 한 흐름으로 완료
- [ ] 계산·정책·모델·RAG 버전 추적
- [ ] 핵심 오류·Fallback 동작
- [ ] 점수·승인확률로 오해할 표현 없음
- [ ] 민감정보 비저장 확인
- [ ] 후속 단계 영향 검토와 필요 수정 완료

---

## RE Stage 9 — 배포·최종 QA·제출 준비

### 목표

배포 URL, 기능명세서, 기획서와 실제 구현을 일치시킨다.

### 상태 기록

| 항목 | 기록 |
| --- | --- |
| 담당자 | 사용자 최종 승인 / Codex 배포·QA 지원 |
| 시작일 | 미정 |
| 완료일 | 미정 |
| 상태 | 미착수 |
| 선행조건 | Gate RE8 |

### P0 — 배포

- [ ] 외부 공개 URL
- [ ] 제출 검증기간 접근
- [ ] Health Check
- [ ] 재시작 후 샘플 정상
- [ ] 환경변수 안전관리
- [ ] 오류 로그와 개인정보 분리
- [ ] 의존성 고정
- [ ] 배포 Runbook

### P0 — 대표 시나리오

- [ ] 상권 하락·낮은 부채
- [ ] 안정 상권·높은 상환부담
- [ ] 상권 하락·현금 부족·기존 부채
- [ ] 자격은 있지만 효과가 부족한 정책
- [ ] 추가 확인조건이 있는 정책
- [ ] 지급 지연
- [ ] 외부모델 없는 상권·업종
- [ ] 잘못된 입력
- [ ] Hero 수치는 상세 일정이 있는 검증 샘플에서 재생성
- [ ] 실제 사용자 사례가 아닌 가상 사업장임을 표시

### P0 — 기능명세서

- [ ] 실제 구현범위
- [ ] 주요 기능 목록
- [ ] 관련 화면
- [ ] 구현상태
- [ ] 사용자 이용 흐름
- [ ] AI 역할
- [ ] 입력·출력 데이터
- [ ] 개인정보 처리
- [ ] 샘플 입력
- [ ] 예상 결과
- [ ] 브라우저 제한
- [ ] MVP 한계

### P0 — 최종 QA

- [ ] 외부 URL 접근
- [ ] 샘플 결과 재현
- [ ] 공식 링크 유효성
- [ ] 정책 접수기간·기준일
- [ ] 금융계산 재검산
- [ ] 그래프·표·AI 설명 일치
- [ ] 모델 한계 문구
- [ ] 승인확률 오해 방지
- [ ] 민감정보 비저장
- [ ] 모바일·데스크톱 확인
- [ ] 제출문서·실제기능 일치
- [ ] 10개 정책별 최소 2문항·총 20문항 이상 공식근거 검색 평가
- [ ] 데모 직전 10개 정책 접수상태·변경공고·공식 링크 재확인
- [ ] Rule ID·Chunk ID·검색점수 사용자 화면 노출 0건

### P0 — 발표자료 근거

- [ ] 기존 서비스와의 차이
- [ ] `지원조건 적용 시 돈이 언제까지 버티고 부채가 얼마나 늘어나는가` 핵심 문장
- [ ] 대출 우선이 아닌 여섯 대응안의 동일 기준 비교
- [ ] 대표 10개 정책을 금융구조별로 깊게 구현했다는 선정 이유
- [ ] 무대응·개입 전후 데모
- [ ] 신규대출의 현금·부채 동시효과
- [ ] 최소부채 대응안
- [ ] 공식 근거·가정 원장
- [ ] Stage 0~6 기준선 보존 이유
- [ ] 모델 교체 시 Gate 결과
- [ ] 모델 미교체 시 한계·Fallback
- [ ] 개인정보 보호
- [ ] 확장 가능성
- [ ] `AI가 미래를 예측하고 최적 정책을 추천` 표현 없음

### P0 — 가상 페르소나 시나리오 모의 검증

- [x] 실제 소상공인 모집 불가에 따라 모의 검증 대체 승인 — 2026-08-16
- [ ] 고정 가상 페르소나 8개와 원천 입력 작성
- [ ] 현금부족·고부채·사후환급·자격 미확인·지원 부족·Fallback·오류 입력 포함
- [ ] 기존 정책 목록 화면과 13주 생존 시뮬레이션 화면에 동일 입력 적용
- [ ] 규칙·계산 엔진으로 기대 최소부채 대안과 핵심 수치를 먼저 산출
- [ ] 비교 전 정답 계약·입력 해시 동결
- [ ] 현금 고갈 범위·시점, 신규부채, 월상환, 총이자, 확인조건 대조
- [ ] 핵심 결과까지 필요한 화면 단계 수 기록
- [ ] 그래프·표·AI 설명의 숫자·의미 일치
- [ ] 개인 매출예측·인과효과·승인확률·최적 정책 금지 표현 0건
- [ ] 입력·정답 계약·실행 Trace·집계표 보존
- [ ] 가상 만족도·이해도·자유 의견 생성 금지
- [ ] LLM 가상 사용자 반응을 실제 사용자 근거로 사용 금지
- [ ] 8개 상황 기대 대안·핵심 계산값 `8/8` 일치
- [ ] 금지 표현 `0건`
- [ ] 하나라도 실패하면 Gate 실패와 원인·수정사항 보존
- [ ] 실제 사용성 향상·정책 현실 효과로 확대 주장 금지
- [ ] 불리한 모의 결과와 실패 사례도 보존·보고

### 완료 산출물

- [ ] 배포 URL
- [ ] 기능명세서 PDF
- [ ] 기획서 최종본
- [ ] 샘플 입력
- [ ] 예상 결과표
- [ ] 배포 Runbook
- [ ] 최종 QA 보고서
- [ ] 발표자료용 근거표

### Gate RE9

- [ ] 제출기간 외부 접근
- [ ] 대표 시나리오 전부 통과
- [ ] 제출문서와 실제 기능 일치
- [ ] 계산·정책·모델·근거 재현
- [ ] 미구현·미검증 기능 과장 없음
- [ ] 종료 결과의 계획·체크리스트·제출문서 최종 환류 완료

---

## 4. 시간이 부족할 때의 축소 순서

### 절대 제거하지 않음

- [ ] 기준 현금흐름
- [ ] 무대응 시나리오
- [ ] 정책 공식 자격근거
- [ ] 정책 전후 현금·부채 비교
- [ ] 공식값·가정값 구분
- [ ] 개인정보 비저장
- [ ] 실제 배포 URL
- [ ] 샘플 검증 절차

### 먼저 축소

1. 서울 실시간 도시데이터
2. 날씨·공휴일·행사
3. 상가정보·LOCALDATA 추가 Feature
4. Quantile 후보모델 수
5. 정책 조합 수
6. 상세 CSV의 선택필드
7. 사용자 계정·저장
8. 고급 지도 시각화

### 모델 v2가 미완성일 때

- [x] 기존 Stage 6 상대 위험순위를 서비스에 표시하지 않음
- [ ] 사용자 직접 매출충격률 제공
- [ ] Quantile 모델을 구현된 것으로 표시하지 않음
- [ ] 현금흐름·정책 금융 이벤트 엔진을 중심 MVP로 유지

### 정책 구조화가 지연될 때

- [ ] 정책 수를 8개까지 축소
- [ ] 금융효과가 명확한 정책 우선
- [ ] 미확인 조건 많은 정책 제외
- [ ] 보조·바우처·이차보전·융자 유형은 유지

---

## 5. 최종 승인 체크리스트

### 서비스

- [ ] 정책금융 영향 시뮬레이터 정의 유지
- [ ] 실제 정책수혜의 매출회복 인과효과로 오해할 표현 없음
- [ ] 금융부담 100점 미사용
- [ ] 정책 적합도 백분율 미사용
- [ ] 무대응 비교 포함
- [ ] 최소부채 기본 목표

### 데이터

- [ ] 기업마당을 소상공인 전용으로 오표현하지 않음
- [ ] 선정 정책의 소상공인 대상 원문 확인
- [ ] 정책 버전·기준일
- [ ] 개인 입력 최소수집
- [ ] 신규 데이터 Ablation

### 모델

- [ ] 상권×업종 집계단위 표시
- [ ] 개인 점포 예측 표현 금지
- [ ] `상권환경 스트레스 시나리오` 명칭 사용
- [ ] 시간순 검증
- [ ] 새 독립검증 상태 표시
- [x] 기존 Stage 6 지위 기록 — 서비스 제외·미재학습·감사 증거 보존

### 금융계산

- [ ] 손계산 검산
- [ ] 지급·상환 일정
- [ ] 총이자·잔여원금
- [ ] 지급 지연
- [ ] 승인되지 않음

### 정책·RAG

- [ ] 공식 자격근거
- [ ] 적격·부적격·추가 확인
- [ ] LLM 계산 금지
- [ ] 환각 조건 0건
- [ ] 공식 링크·문의처

### 개인정보·보안

- [ ] 주민등록번호 없음
- [ ] 계좌번호 없음
- [ ] 원금액 로그 없음
- [ ] 무동의 영구저장 없음
- [ ] 외부 전송 고지

### 웹·제출

- [ ] End-to-End 완료
- [ ] 외부 URL 접근
- [ ] 샘플 재현
- [ ] 입력 정밀도에 맞는 범위·일정 기반 표시
- [ ] 가상 페르소나 8개 모의 검증 근거와 실제 사용자 미검증 한계
- [ ] 기능명세서 일치
- [ ] 한계·안전문구

---

## 6. MVP 완료 선언

다음 조건을 모두 충족할 때만 완료로 선언한다.

- [ ] Stage 0~6 Artifact 보존
- [ ] Gate RE1~RE9 통과
- [ ] 확정한 대표 정책 10개 공식 근거 추적
- [ ] 13주·6개월 계산 검산
- [ ] 무대응과 정책안 비교
- [ ] 대출 미래부담 표시
- [ ] 개인 폐업·승인확률 오해 없음
- [ ] 모델 검증상태 정직한 표시
- [ ] RAG가 계산·자격을 변경하지 않음
- [ ] 배포 URL 외부 접근
- [ ] 제출문서와 실제 기능 일치
- [ ] 가상 페르소나 8개 입력·정답 계약·실행 Trace·집계근거 보존

완료 선언에는 다음을 함께 기록한다.

```text
완료일
배포 URL
Git Commit
현금흐름 엔진 버전
정책 데이터 버전
외부모델 버전
대표 시나리오 결과
남은 한계
최종 사용자 승인
```
