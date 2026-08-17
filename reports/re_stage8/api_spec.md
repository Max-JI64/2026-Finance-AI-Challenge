# RE Stage 8 API 명세

## 공통 계약

- Base URL: `/api/v1`
- 현재 서비스명: `정책금융 영향 시뮬레이터`
- 공통 추적값: `request_id`, `as_of_date`, `versions`
- 사용자 응답 제외값: Rule ID, Chunk ID, BM25 점수, 검색순위
- 요청 크기 상한: 2MB
- 재무 입력·자격 프로필·질문은 애플리케이션 DB와 검색 인덱스에 저장하지 않는다.
- 실제 JSON Schema는 `reports/re_stage8/openapi.json`과 실행 중인 `/docs`에서 확인한다.

## Endpoint

| Method | Path | 역할 | 주요 Fallback |
| --- | --- | --- | --- |
| GET | `/health` | 전체 엔진 버전과 Liveness | 외부 의존 없음 |
| GET | `/api/v1/service-contract` | 서비스 범위·금지주장·개인정보 계약 | 외부 의존 없음 |
| GET | `/api/v1/catalog/areas` | 서울 상권 목록 | 지원 목록 밖 직접입력 거절 |
| GET | `/api/v1/catalog/industries` | 서비스업종 목록 | 지원 목록 밖 직접입력 거절 |
| POST | `/api/v1/cashflow/baseline` | 월 금액과 날짜 기반 기준 현금흐름 | 입력 오류를 값 미반사 422로 반환 |
| POST | `/api/v1/cashflow/csv` | 메모리 내 상세 CSV 기준 현금흐름 | UTF-8-SIG·만원 헤더 권장, 기존 원 단위·영문 헤더 호환, CSV 원문 비저장 |
| POST | `/api/v1/policies/eligibility` | 자격과 접수상태 분리 판정 | 미확인값을 추정하지 않고 확인항목 반환 |
| POST | `/api/v1/simulations/policy-impact` | 정책 개입 영향 시뮬레이션 | 직접 충격률 사용 |
| POST | `/api/v1/alternatives/compare` | 무대응 포함 6개 대응안 비교와 실행계획 | 조건부 가정 해제 시 비교·순위 제외 |
| POST | `/api/v1/ai/ask` | 로컬 공식근거 검색과 Luna 설명 | DB·API·Fact-lock 실패 시 로컬 요약 유지 |

## 대안 비교 요청

`sample_id`, `simple_input`, `quick_input` 가운데 하나를 사용한다. `quick_input`은 매일·매주·월초·월중·월말 매출유형과 초·중·말 비용·상환시기를 받아 보수적·기준·완화의 세 날짜별 일정을 생성한다. 초는 1-10일, 중은 11-20일, 말은 21일-월말이다. 정책 비교는 세 일정 중 기준 일정을 사용하고 화면에는 범위를 함께 표시한다. `direct_shock_13_week_percent`와 `direct_shock_6_month_percent`는 집계 상권환경 충격을 사용자가 직접 지정하는 Fallback이다. `assume_conditional=false`이면 추가 확인 정책은 계산·순위에서 제외된다.

## 공통 비교 반환

- 기준 현금흐름 입력과 정밀도
- 외부환경 시나리오와 한계
- `eligibility_status`, `availability_status`, `candidate_state`
- `reason_summary`, `items_to_confirm`, 정책 버전·기준일·공식 URL
- 무대응과 개입안의 13주·6개월 현금곡선
- 신규부채·월상환·총이자·총상환의무·지급지연
- 목표별 비교결과·Pareto·실행계획
- 가정 원장·공식 근거·한계

## Luna 경계

- 모델 ID 기본값은 `gpt-5.6-luna`이며 `OPENAI_MODEL`로만 덮어쓴다.
- `OPENAI_API_KEY`가 없으면 외부 호출을 하지 않는다.
- 외부 전송은 사용자 질문과 검색된 공식근거 텍스트뿐이다.
- `store=false`로 Responses API를 호출한다.
- Luna 출력은 구조화 계산·자격·순위·근거 URL을 만들거나 수정할 수 없다.
- 근거 밖 숫자 또는 금지주장이 발견되면 출력을 폐기하고 로컬 요약을 반환한다.
