# 프로젝트 진행 LOG

> 발표 준비와 포트폴리오 작성을 위한 시간순 작업 기록이다. `AGENT_MEMORY.md`와 별도로 관리한다.

## 기록 원칙

- 모든 기록은 `YYYY-MM-DD HH:mm (KST)` 형식으로 월·일·시·분을 포함한다.
- 작업 결과, 결정, 검증 증거, 다음 단계에 영향을 주는 변경을 시간순으로 기록한다.
- 원본 데이터 내용, 비밀키, 개인정보, 전체 명령 출력은 기록하지 않는다.
- 과거 기록은 삭제하거나 의미를 바꾸지 않고, 정정이 필요하면 새 시각의 정정 기록을 추가한다.

## 진행 기록

| 일시 | 구분 | 진행 내용 | 결과·증거 |
| --- | --- | --- | --- |
| 2026-08-14 19:52 (KST) | 기획 | 서울 소상공인 AI 금융 생존 내비게이터의 MVP 범위와 서비스 구조를 기준 문서에 맞춰 정리하기 시작했다. | `프로젝트 계획서.md` |
| 2026-08-14 20:21 (KST) | 계획 | 데이터 수집부터 배포까지 13개 Stage, P0·P1·P2 우선순위, 단계별 Gate를 포함한 실행 체크리스트를 작성했다. | `MVP 단계별 구현 체크리스트.md` |
| 2026-08-14 20:34 (KST) | Stage 0 | Python·FastAPI 기반 프로젝트 구조, 환경 파일, 중앙 설정, 비밀키 분리, 최소 API와 테스트 구현을 시작했다. | `README.md`, `requirements.txt`, `config/settings.yaml`, `.env.example`, `app/`, `tests/` |
| 2026-08-14 20:40 (KST) | 검증 | Stage 0 초기 테스트 4개와 실제 Uvicorn `/health` HTTP 응답을 확인했다. | 테스트 `4 passed`, `/health` HTTP 200 |
| 2026-08-14 20:51 (KST) | 범위 결정 | 외부 데이터의 탐색·다운로드는 사용자가 직접 담당하고, Codex는 명시적 요청 없이 데이터를 수집하지 않기로 확정했다. | 데이터 수집 역할 분리 |
| 2026-08-14 21:00 (KST) | Stage 0 | Python 버전 고정, 검증 스크립트, 프로젝트 구조·설정·비밀값 검사를 보강했다. | `scripts/verify_stage0.ps1`, 테스트 `8 passed` |
| 2026-08-14 21:14 (KST) | 운영 결정 | 프로젝트가 1인 팀임을 확인했다. 팀 합의 항목은 본인 범위 확인으로 판단하고 자동 검증 결과를 Stage 0 기술 증거로 사용하기로 했다. | 1인 프로젝트 검증 기준 확정 |
| 2026-08-14 22:29 (KST) | 데이터 확인 | `data/raw/`에서 계획서 1~9번 상권 데이터의 존재를 확인했다. 핵심 범위 외에 `상권변화지표-자치구`, `직장인구-상권배후지` 파일도 별도로 확인했다. | 파일명·크기만 우선 확인, 전체 데이터 미로딩 |
| 2026-08-14 22:33 (KST) | 원본 분석 | CSV별 최대 64 KiB와 최대 5행, 공간 DBF 헤더와 최대 5개 레코드만 읽어 1~9번 데이터의 변수표를 작성했다. | `data/raw/README.md`, 전체 변수 행 232개 |
| 2026-08-14 22:33 (KST) | 원본 분석 | 추정매출 2021~2025년 헤더가 동일하고, 점포 데이터는 2025년부터 영문 헤더로 변경된 사실을 기록했다. 전처리는 수행하지 않았다. | `data/raw/README.md`의 데이터별 변수표와 주의사항 |
| 2026-08-14 22:33 (KST) | 향후 수집 | 정책추천·RAG 자료는 현재 수집하지 않고 Stage 8~9 시작 시 최신성 확인 후 필수·보조·선택 자료를 수집하도록 명시했다. | `data/raw/README.md`의 정책추천·RAG 후속 수집 목록 |
| 2026-08-14 22:35 (KST) | 검증 | 변수표 232행, 데이터 섹션 9개, 정책·RAG 링크 8개, LOG 시간 형식을 자동 대조했다. 원본 외 `interim`·`processed`·`models`에는 가공 산출물을 만들지 않았다. | 문서 검증 통과, 전처리 미수행 |
| 2026-08-14 22:44 (KST) | 정정 | 초기 인코딩 표본 함수가 결과는 64 KiB만 사용했지만 `read_bytes()`로 파일 전체를 메모리에 읽는 구현임을 발견했다. 스트림에서 앞 64 KiB와 뒤 64 KiB만 읽도록 수정했다. | `scripts/inspect_sample_schema.py`; 원본 수정·전처리는 없었음 |
| 2026-08-14 22:44 (KST) | Stage 0 | 1인 팀 기준으로 범위·환경·구조·보안·자동 검증 증거를 재판정하고 체크리스트의 Stage 0 Gate를 완료 처리했다. | `MVP 단계별 구현 체크리스트.md`, `reports/stage0/verification.md` |
| 2026-08-14 22:44 (KST) | Stage 1 | 1~9번 원본의 출처, 파일명, 경계 표본 기간, 크기, 형식, 인코딩, 변수 수와 원본·가공 폴더 분리를 기록했다. 원본 ZIP과 CSV 전체 행 수는 미확인으로 남겼다. | `data/raw/README.md` |
| 2026-08-14 22:44 (KST) | Stage 2 | 점포 2025년 영문 헤더, 데이터별 키, 기간 차이, 자치구·상권배후지 집계 단위, 결측·중복·이상치·공간·결합 검증 방법을 포함한 실행계획을 작성했다. | `reports/stage2/quality_validation_plan.md`; 실행·전처리 미수행 |
| 2026-08-14 23:05 (KST) | Stage 2 | 원본 CSV를 20,000행 청크로 순차 검사해 기간·행 수·키·결측·중복·논리값·코드 관계·결합률을 확정했다. 점포 2025년 헤더는 읽기 시점에만 표준화했다. | 매출·점포 기본키 중복 0건, 매출→점포·영역 미매칭 0건, 공통기간 2021Q1~2025Q4; `reports/stage2/` |
| 2026-08-14 23:05 (KST) | 공간 QA | 영역-상권의 CPG `UTF-8`, CRS EPSG:5181, 상권코드 1,650개, 빈·중복 도형 0건을 확인했다. 유효하지 않은 도형 6건은 삭제하지 않고 검토 대상으로 기록했다. | `reports/stage2/spatial_quality.csv` |
| 2026-08-14 23:13 (KST) | Stage 3 | 매출을 기준 테이블로 점포와 4~9번 상권 자료를 디스크 기반 left join하고 현재·과거 분기만 사용한 매출·점포 변화 Feature를 생성했다. | `data/processed/stage3_panel.parquet` — 439,141행 × 199열, 기본키 중복·결측 0건 |
| 2026-08-14 23:17 (KST) | 재현성 검증 | 같은 원본으로 Stage 3 빌드를 두 번 실행해 행 수·열 수·Parquet SHA-256이 동일함을 확인했다. 세 개 상권·업종 표본의 매출·점포·전분기 증감률도 원본과 일치했다. | SHA-256 `88370a02f592c020196613e69a9dc8e642cf3ba14a00003bb6cdd37198f40e07`; `reports/stage3/reproducibility_check.json`, `manual_spot_check.csv` |
| 2026-08-14 23:19 (KST) | 문서화 | Stage 1~3 상태, QA 결과, Panel 재생성 방법, 데이터 사전, Feature 식과 다음 Stage 전달사항을 문서에 반영했다. | `MVP 단계별 구현 체크리스트.md`, `README.md`, `data/raw/README.md`, `reports/stage3/` |
| 2026-08-14 23:28 (KST) | 운영 규칙 | Target·데이터 처리·기간 분할·평가 지표·최종 모델 등 결과를 실질적으로 바꾸는 선택이 필요하면 작업을 멈추고 사용자의 명시적 허락을 받은 뒤 재개하도록 세션 공통 규칙을 확정했다. | `AGENTS.md`, `AGENT_MEMORY.md`, `MVP 단계별 구현 체크리스트.md` |
| 2026-08-14 23:31 (KST) | 검증 원칙 | 필수 Stage Gate와 핵심 수치가 통과하면 비필수 검증 실패만으로 반복하지 않고 한계를 기록한 뒤 다음 단계로 진행하도록 세션 공통 규칙을 추가했다. | `AGENTS.md`, `AGENT_MEMORY.md`, `MVP 단계별 구현 체크리스트.md` |
| 2026-08-14 23:34 (KST) | Stage 4 | 다음 분기 전년동기 대비 매출증감률 기준 Target 후보 4개와 시간 분할 A·B의 클래스 비율을 계산했다. 최종 Target과 분할은 사용자 선택 전까지 확정하지 않았다. | 비교 가능 329,169행; `src/data/analyze_stage4_candidates.py`, `reports/stage4/` |
| 2026-08-14 23:47 (KST) | Stage 4 결정 | 단일 분기 악화 대신 향후 두 분기가 모두 전년동기보다 감소하고 두 분기 합산 매출도 기준 이상 감소하는 지속 악화 Target 구조를 채택했다. 4개 expanding-window Fold와 한 분기 Purge, 2025년 잠긴 테스트를 확정했다. | `config/stage4.yaml` |
| 2026-08-14 23:47 (KST) | Stage 4 분석 | 지속 악화 Target의 5~20% 합산 감소 임계값을 개발기간에서 비교했다. 임계값은 사용자 승인 전까지 확정하지 않았고 머신러닝 학습은 시작하지 않았다. | 전체 생성 가능 302,479행, 개발기간 222,973행; `reports/stage4/persistent_target_report.md` |
| 2026-08-14 23:49 (KST) | Stage 5 계획 | 특정 모델을 미리 확정하지 않고 여러 후보를 동일 조건으로 비교한 뒤 최종 후보 1개를 선택하고, 선택된 모델에만 Optuna 튜닝을 수행하기로 정했다. | `MVP 단계별 구현 체크리스트.md`; 후보 모델 목록 미정 |
| 2026-08-14 23:56 (KST) | Stage 4 준비 | 승인된 구조를 기준으로 개발 라벨·4개 Fold·라벨 없는 잠긴 테스트 Feature를 청크 단위로 생성하는 코드를 준비했다. 10% 임계값 확정 문구가 필요해 실행은 보류했고 결과 데이터는 생성하지 않았다. | `src/data/build_stage4_dataset.py`, `config/stage4.yaml`은 임계값 승인 대기 상태 |
| 2026-08-15 00:06 (KST) | Stage 4 완료 | 사용자가 두 분기 합산 전년동기 대비 10% 감소 기준을 확정해 개발 라벨과 4개 시간순 Fold를 생성했다. 개발 222,973행 중 양성 56,369행(25.28%)이며, 2025 잠긴 테스트 79,506행은 Feature만 저장해 Target 값·통계를 노출하지 않았다. 기본키·공식·Fold 기간·Feature 누수 필수 검증을 1회 통과해 Gate 4를 완료했다. | `data/processed/stage4_development.parquet`, `stage4_fold_membership.parquet`, `stage4_locked_test_features.parquet`, `reports/stage4/stage4_manifest.json` |
| 2026-08-15 00:08 (KST) | Stage 5 준비 | 설치된 모델 패키지를 확인하고 단순 기준선·Logistic Regression·LightGBM·XGBoost·CatBoost의 무튜닝 비교와 PR-AUC 우선 평가를 권장안으로 정리했다. 후보와 지표는 결과를 바꾸는 선택이므로 사용자 승인 전 학습은 시작하지 않았다. | scikit-learn·LightGBM·XGBoost·CatBoost·Optuna 사용 가능 확인 |
| 2026-08-15 00:12 (KST) | Stage 5 설계 변경 | 사용자 요청에 따라 선형·배깅·부스팅 기본 모델을 넓게 비교한 뒤 상위 3개를 선택해 각각 Optuna 튜닝하고, 이후 OOF 기반 Voting·Stacking을 검토하는 흐름으로 변경했다. 일반 회귀 Lasso·ElasticNet 대신 분류용 L1·Elastic-Net Logistic을 사용한다. | `MVP 단계별 구현 체크리스트.md`; 정확한 후보 목록과 지표 우선순위 승인 대기 |
| 2026-08-15 00:32 (KST) | Stage 5 일시 중단 | 9개 모델과 AUROC·AUPRC 공동 핵심 지표는 승인됐지만, 모델링 EDA·변수 중복 정리·파생변수·Feature contract가 선행돼야 한다는 사용자 지적에 따라 학습을 즉시 중단했다. 2025 잠긴 테스트는 열지 않았고 실제 후보 모델은 학습되지 않았으며, 중단 시 생성된 Dummy Fold 1 체크포인트는 비교 결과로 사용하지 않는다. | `config/stage5.yaml`을 Feature contract 승인 전 실행 차단 상태로 변경; `MVP 단계별 구현 체크리스트.md`에 사전 Feature 점검 추가 |
| 2026-08-15 00:39 (KST) | Stage 4.5 계획 | Stage 4와 5 사이에 플롯 없는 모델링 EDA·파생변수·Feature contract 단계를 별도로 추가했다. 변수 간 관계, 각 변수와 Target의 통계적·실질적 관계, 다중검정, 중복·공선성, 기간 Drift, 객단가·점포당 매출·구성비·밀도·Rolling 파생변수와 PCA 미적용 원칙을 명시했다. 현재 세션에서는 분석·플롯·Stage 4.5 산출물을 만들지 않았고 새 세션 시작 과제로 남겼다. | `MVP 단계별 구현 체크리스트.md` Stage 4.5; 2024 Validation Target과 2025 잠긴 테스트 미사용 |
| 2026-08-15 11:32 (KST) | Stage 4.5 분석 | Fold 1 Train 122,011행에서 원본 199개와 파생 134개의 분포·상관·Target 관계·FDR·기간 안정성·PSI·구조 제거 후 VIF를 플롯 없이 분석했다. 2024 Validation Target과 잠긴 2025 데이터는 사용하지 않았고 테스트 10개가 통과했다. 권장안 A는 원본 83개 유지, 116개 제거·치환, 비상수 파생 127개 추가이며, 선형 모델의 L1/L2/Elastic-Net과 별개로 승인된 트리 5종을 모두 유지한다. 사용자 승인 전 Stage 5는 계속 차단한다. | `reports/stage45/`, `src/analysis/run_stage45_eda.py`, `src/features/build_stage45_features.py`, `tests/test_stage45_features.py` |
| 2026-08-15 12:19 (KST) | Feature contract 승인 | 사용자가 D안인 공통 A형 기준선과 트리 원시 변수군 독립 Ablation을 승인했다. 선형은 log1p 10개를 추가하고, 트리 5종은 공통 기준선 후 매출금액·거래건수·유동·상주·직장인구 원시군을 하나씩 시험하도록 Stage 5 계획에 반영했다. 정확한 개선 허용오차는 실행 전 승인 대상으로 남겼고, 사용자 요청에 따라 Stage 5 실행은 시작하지 않았다. | Gate 4.5 통과; `reports/stage45/feature_contract.md`, `config/stage5.yaml`, `MVP 단계별 구현 체크리스트.md`; 실행 Guard `not_started_user_hold` |
| 2026-08-15 12:22 (KST) | Target 단위 재확인 | ML의 한 행과 Target은 개별 점포가 아니라 `기준분기 × 서울시 상권코드 × 서비스업종코드`에 속한 점포들의 집계 매출환경을 뜻함을 패널 키와 Target 생성 로직으로 재확인했다. | `reports/stage2/quality_validation_plan.md`, `src/data/build_stage3_panel.py`, `src/data/build_stage4_dataset.py`, `reports/stage4/target_definition.md`; Stage 5 실행 없음 |
| 2026-08-15 12:24 (KST) | Target 세분화 검토 | 현재 9종 원본에서 매출·점포 라벨의 최저 집계 단위가 분기×상권×업종이므로 이를 현 MVP의 주 ML 단위로 유지하는 것이 가장 효율적이라고 판단했다. 격자·도로·개별 점포 단위 예측에는 동일 단위의 별도 매출 또는 폐업 라벨이 필요하며, 기존 상권 라벨 복제는 사용하지 않는다. | 설계 변경·Stage 5 실행 없음; `data/raw/README.md`, `reports/stage2/schema_mapping.md`, `reports/stage2/qa_summary.md` |
