# Agent Memory

> Codex-maintained project memory. Verify time-sensitive facts against the
> current workspace.

## Project snapshot

- Last updated: 2026-09-05T13:04+09:00
- Purpose: Build a bounded-AI Seoul small-business finance copilot that separates store trends from aggregate market scenarios, shows policy candidates without an upfront question gate, lets users choose each selected policy's reviewed conditions in its preparation screen, and compares no action with confirmed or explicitly conditional policy effects on deterministic 13-week and 6-month cash/debt horizons.
- Important paths: `V2 단계별 구현 계획표.md` and `V3 사용자 경험 구성안.md` preserve earlier versions; `V4 구현 계획표.md` and `v4/` preserve the implemented V4; `V5 구현 계획표.md`, `V5 사용자 경험 흐름.md`, `v5/`, `v5/VERIFICATION.md`, and `reports/v5/evaluation/` describe the implemented V5, its V6 comparison baseline, verification evidence, and fixed evaluation Oracles. `포트폴리오/2026 금융 AI Challenge - 버팀AI/` contains the final-service portfolio case study, two detail pages, eight HWPX-embedded images converted to PNG, and exact copies of the final proposal and function-specification PDFs. `데모 사이트/index.html` is the self-contained offline portfolio demo derived from the current V5 UI.

## Durable decisions

- `decision:offline-portfolio-demo`
  - Created: 2026-08-31T17:12+09:00
  - Updated: 2026-08-31T18:04+09:00
  - Status: active
  - Content: GitHub 블로그용 공개 데모는 현재 `v5/static/` 화면을 복사한 독립 파생본 `데모 사이트/index.html` 한 파일로 유지한다. 원본 V5는 변경하지 않는다. 데모는 2026-08-31에 계산해 저장한 이태원 관광특구 한식음식점의 고정 가상 사례, 하방·기준·회복 세 범위와 정책 3개만 보여주며 입력과 정책 선택은 고정한다. 런타임 LightGBM, 서버·API 호출, 외부 AI, 공고 자동 분석, 외부 링크·자원과 데이터 전송은 사용하지 않고 CSP `connect-src 'none'`으로 연결도 차단한다. 저장 수치는 개인 점포 예측이나 현재 공고 상태가 아니며 최종 시각 확인은 사용자 소유다.
  - Evidence: `데모 사이트/index.html`; 인라인 JavaScript 4개 구문 검사, 인라인 스타일 3개와 고정 사례·정책 3개·시나리오 3개 계약 검사, 외부 자원·URL·통신 API·런타임 모델명·API 키 패턴 부재 확인. 앱 내 브라우저의 `file://` 접근은 보안 정책으로 차단되어 실제 브라우저 시각 검사는 수행하지 않았다.

- `decision:portfolio-final-service-case-study`
  - Created: 2026-08-31T14:12+09:00
  - Updated: 2026-08-31T14:12+09:00
  - Status: active
  - Content: 버팀AI 포트폴리오는 개발 버전·단계 이력, 로컬 주소와 테스트 건수를 노출하지 않고 최종 공개 서비스만 설명한다. 메인 사례 페이지는 문제 정의, 진단-비교-준비 흐름, 무대응 대비 13주 현금과 6개월 부채·상환 비교, 데이터·AI 역할 분리, 개인정보와 한계를 다룬다. 별도 세부 페이지는 금융 계산과 AI·데이터 안전장치를 설명한다. 화면 자료는 폐기된 별도 이미지가 아니라 사용자가 최종 `기획서.hwpx`와 `기능명세서.hwpx`에 삽입한 원본만 사용한다.
  - Evidence: `포트폴리오/2026 금융 AI Challenge - 버팀AI/`; 최종 HWPX `BinData` 원본 확인, 이미지 8개 PNG 로드, Markdown 상대 링크 16개, 대표 사례 수치 대조, PDF 7쪽·12쪽과 원본 SHA-256 일치, 공개 URL 현재 화면과 금융보안원·DAKER·중소벤처기업부·서울 열린데이터광장 공식 페이지 확인.

- `decision:v5-market-scenario-copy`
  - Created: 2026-08-30T16:21+09:00
  - Updated: 2026-08-30T16:52+09:00
  - Status: active
  - Content: V5의 하방·기준·회복 범위는 선택한 상권·업종 전체 매출이 앞으로 13주와 6개월 동안 각 경로로 움직인다고 가정해 현금흐름에 적용하는 시나리오다. 내 점포 매출 예측으로 표현하지 않으며, 카드의 수치는 전년 같은 기간 대비 상권·업종 전체 매출 변화율이다. 데스크톱에서는 설명 한 줄과 개인 점포 예측이 아니라는 주의문 한 줄의 정확한 2줄 구조로 표시한다.
  - Evidence: `v5/static/index.html`, `v5/static/v5-extension.css`, `v5/tests/test_v5.py`; `git diff --check`, V5 테스트 18/18, 로컬 브라우저에서 두 문장 각각 한 줄 렌더링 확인.

- `decision:v5-diagnosis-information-clarity`
  - Created: 2026-08-30T16:52+09:00
  - Updated: 2026-08-30T17:37+09:00
  - Status: active
  - Content: 진단 결과는 `내 가게·입력한 매출`의 과거 변화와 `상권·업종·앞으로 13주`의 미래 가정을 다른 정보로 명시한다. 상권 전망 값은 `상권·업종 매출 전년 동기 대비`를 붙여 변화 대상과 비교 기준을 함께 표시한다. 검토 기준은 중복 신호를 나열하지 않으며 28일 필요현금 팝업은 현재 스크롤 위치 위에 고정한다.
  - Evidence: `v5/static/index.html`, `v5/static/app.js`, `v5/static/styles.css`, `v5/static/v5-extension.js`, `v5/static/v5-extension.css`, `v5/tests/test_v5.py`; JavaScript 구문 검사, `git diff --check`, V5 테스트 18/18, 로컬 브라우저 문구와 팝업 열기 전후 배경 위치 확인.

- `decision:v5-official-notice-positive-handoff-copy`
  - Created: 2026-08-30T17:50+09:00
  - Updated: 2026-08-30T17:50+09:00
  - Status: active
  - Content: 준비 화면에서 공고 항목을 자동 확인할 수 없는 경우 `실패`, `검증 실패`, `자동 확정하지 않음`, `찾지 못함` 같은 부정적 상태 문구를 노출하지 않고 `공식 공고에서 직접 확인해 주세요`와 공식 공고 링크로 안내한다. 정책 상담 진입 제목은 `AI와 채팅으로 이 정책 더 물어보기`로 AI 채팅 기능을 명시한다.
  - Evidence: `v5/static/index.html`, `v5/static/v5-extension.js`, `v5/tests/test_v5.py`; JavaScript 구문 및 관련 V5 테스트 1건 통과.

- `issue:v5-preparation-answer-scroll-jump`
  - Created: 2026-08-30T17:54+09:00
  - Updated: 2026-08-30T17:54+09:00
  - Status: resolved
  - Symptom: 준비 화면의 정책 조건을 선택할 때마다 재계산 후 화면이 맨 위로 이동했다.
  - Cause: 조건 재계산 뒤 이미 활성화된 준비 화면에 `showStep("preparation")`을 다시 호출하면서 공통 단계 전환의 상단 스크롤이 실행됐다.
  - Fix: 준비 화면이 이미 활성화된 경우 단계 전환을 생략하고, 선택 전 스크롤 위치와 조건 패널의 화면상 위치를 저장해 재렌더링 높이 변화까지 보정한 뒤 복원한다.
  - Evidence: `v5/static/v5-extension.js`, `v5/static/index.html`, `v5/tests/test_v5.py`; JavaScript 구문 및 관련 V5 테스트 1건 통과.

- `issue:v5-input-ledger-scroll-jump`
  - Created: 2026-08-30T17:56+09:00
  - Updated: 2026-08-30T17:59+09:00
  - Status: superseded
  - Symptom: 재무 입력 하단에서 `현금 진단 보기`로 입력 원장을 열 때 현재 스크롤 위치가 바뀌었다.
  - Cause: 입력 원장 모달을 열고 닫는 과정에서 배경 문서의 위치를 별도로 보존하지 않았다.
  - Fix: 2026-08-30T17:59+09:00 사용자 요청으로 입력 원장 전용 스크롤 저장·복원 변경을 전부 롤백했다. 입력 원장은 변경 전 동작을 사용하며, 준비 화면의 정책 조건 선택 스크롤 유지 수정은 별도로 유지한다.
  - Evidence: `v5/static/v5-extension.js`, `v5/static/index.html`, `v5/tests/test_v5.py`; 전용 식별자 부재와 JavaScript 구문 확인.

- `decision:v5-finance-form-clarity`
  - Created: 2026-08-30T16:05+09:00
  - Updated: 2026-08-30T16:11+09:00
  - Status: active
  - Content: V5의 최근 월매출, 현재 현금·월 지출, 현재 대출 입력은 다크·화이트 모드별로 섹션 면과 구분되는 공통 입력 배경·테두리·단위 위계를 사용한다. 현금·지출과 대출은 데스크톱 2열의 동일 높이 행이며 `임대료 없음`과 `직원 없음`은 전체 폭 선택 컨트롤이다. 진단 전 입력 원장은 최대 1040px의 항목명+값 2열만 표시하고, 최근 월매출은 3열과 줄바꿈 없는 `YYYY년 M월`을 사용한다. 출처·입력 방식·확인 상태 메타정보와 하단 `확인 권장` 안내는 표시하지 않는다.
  - Evidence: `v5/static/index.html`, `v5/static/v5-extension.css`, `v5/static/v5-extension.js`, `v5/tests/test_v5.py`; JavaScript 구문 검사, `git diff --check`, V5 테스트 18/18, 로컬 HTML/CSS/JS HTTP 200 및 입력 토큰·2열 렌더링·메타정보 제거 확인.

- `decision:v5-demo-mode-launcher`
  - Created: 2026-08-30T14:35+09:00
  - Updated: 2026-08-30T17:05+09:00
  - Status: active
  - Content: `?demo=1`에서만 발표용 예시 선택판을 사업장 입력 화면 맨 위로 옮겨 자동으로 열고, 헤더에 `발표 모드` 배지를 표시한다. 카탈로그 로딩이 끝나기 전에는 5개 예시 선택을 잠그며, 선택 후에도 자동 계산하지 않고 `입력값 확인하기`로 재무 입력 단계에 이동한다. 예시 선택 시 현금 여유·안정 운영은 정책 유형 비교, 매출 감소는 현금 생존, 고정비 부담은 고정비 절감, 대출 부담은 상환 부담 완화를 주된 해결 목적으로 자동 선택한다. 발표 조작부는 기본 초록과 분리된 다크/화이트 대응 앰버·골드 토큰을 쓰며 일반 URL에서는 계속 숨긴다.
  - Evidence: `v5/static/index.html`, `v5/static/app.js`, `v5/static/styles.css`, `v5/static/v5-extension.css`, `v5/tests/test_v5.py`; JavaScript 구문 검사, `git diff --check`, V5 테스트 18/18. 이번 자동 선택 변경은 사용자 소유 시각 확인을 존중해 브라우저·이미지 검사를 수행하지 않았다.

- `decision:v5-user-selectable-theme`
  - Created: 2026-08-30T12:17+09:00
  - Updated: 2026-08-30T22:06+09:00
  - Status: active
  - Content: V5 provides a top-right light/dark theme toggle. The explicit choice persists only as the non-sensitive `buteomai:theme` localStorage key; without a saved choice the site starts in dark mode regardless of the browser or operating-system color preference. Both themes use centralized semantic CSS tokens, theme-specific logo/favicon assets, and chart redraw after a theme change.
  - Evidence: `v5/static/index.html`, `v5/static/styles.css`, `v5/static/v5-extension.css`, `v5/static/theme.js`, and `v5/tests/test_v5.py`; JavaScript syntax check, `git diff --check`, and V5 tests 18/18.

- `decision:v5-dark-surface-contrast`
  - Created: 2026-08-30T18:06+09:00
  - Updated: 2026-08-30T18:06+09:00
  - Status: active
  - Content: V5 다크모드의 페이지 배경, 공통 박스 표면, 중첩 보조면, 공통 테두리 사이의 밝기 차이를 확대한다. 개별 비교 박스에만 예외 스타일을 붙이지 않고 의미 기반 `--bg`, `--surface`, `--soft`, `--line` 토큰을 조정해 진단·정책 비교·준비 화면의 같은 계층 박스에 일관되게 적용하며 라이트모드는 유지한다.
  - Evidence: `v5/static/styles.css`, `v5/static/theme.js`, `v5/static/index.html`, `v5/tests/test_v5.py`; `git diff --check`, JavaScript 구문 검사, 관련 V5 테스트 1건, 실행 중 서버의 갱신 CSS·테마 스크립트 확인.

- `decision:v5-policy-bulk-selection`
  - Created: 2026-08-30T18:16+09:00
  - Updated: 2026-08-30T18:16+09:00
  - Status: active
  - Content: 진단 화면의 정책 후보는 사용자에게 실제로 노출하는 최대 3개만 기준으로 안내한다. `정책 모두 선택`은 현재 보이는 정책을 최대 선택 한도 3개까지 한 번에 선택하고, 전부 선택되면 `모두 선택됨`으로 비활성화한다. 내부 검색 후보 전체 개수는 선택 안내에 노출하지 않는다.
  - Evidence: `v5/static/index.html`, `v5/static/app.js`, `v5/static/styles.css`, `v5/tests/test_v5.py`; JavaScript 구문 검사, `git diff --check`, 관련 V5 테스트 2건, 실행 중 서버의 갱신 HTML·CSS·JavaScript 확인.

- `decision:v5-submission-doc-ui-sync`
  - Created: 2026-08-30T17:27+09:00
  - Updated: 2026-08-30T21:04+09:00
  - Status: active
  - Content: 최신 V5 UI 변경은 제출용 Markdown에 화면 테마 전환, 발표 예시별 해결 목적 자동 선택, 간소화된 입력 원장, 현재 위치의 28일 필요현금 팝업, `가상 예시`, 정책 후보 일괄 선택, 준비 조건 선택 시 화면 위치 유지와 AI 채팅 명칭을 동기화한다. 일반 이용 흐름은 일반 URL 기준으로 두고, 심사위원 확인 절에는 `/?demo=1` 전체 주소와 가상 입력 선택 화면 캡처 지침을 둔다. 그림 1은 MVP 첫 문단과 서비스 구성 문단 사이에서 대표 사례의 비교 내용을 본문으로 설명하고 캡션은 `그림 1. 대표 사례 30초 보기`로 짧게 쓴다. What-if는 핵심 설명과 이용 흐름에서 제외하고 `가정 변경 비교`라는 이름으로 기능 목록, AI 처리와 개인정보 절에만 실제 역할과 외부 전송 한계를 남기며, 중복된 일반 `선택형 기능` 설명 문단은 두지 않는다. 상권환경 모델 절은 P10·P50·P90의 의미, 4개 expanding-window Fold, 직전 1분기 제외, 후보 비교, 2025Q2 내부 시간 Holdout과 새 미래기간 독립검증 미완료를 설명한다. 활용 데이터 절은 서울시 상권분석서비스 9개 공개자료의 개별 공식 링크와 2021Q1~2025Q4 사용기간을 밝힌다. HWPX·PDF와 공개 배포는 사용자의 별도 작업 전까지 수정하지 않는다.
  - Evidence: `제출/08_공모전_기획서_원고_및_시각자료_2차수정본.md`, `제출/09_기능명세서_원고_및_시각자료_2차수정본.md`; 2026-08-30 문구 대조.

- `decision:mvp-scope`
  - Created: 2026-08-14T19:55+09:00
  - Updated: 2026-08-16T11:28+09:00
  - Status: active
  - Content: The MVP is named `서울 소상공인 정책금융 영향 시뮬레이터` and compares no action, grants, cost reduction, refinancing, policy loans, and mixed interventions through 13-week cash survival plus 6-month debt effects. Aggregate ML outputs are labeled area-environment stress scenarios; personal sales/closure, credit or approval probability, account/POS integration, causal policy impact, and claims of AI optimal recommendation are excluded.
  - Evidence: User-approved updates to `프로젝트 계획서.md`, `프로젝트 차별화 구상.md`, and `MVP 단계별 구현 체크리스트.md`; the completed RE1 contract/config retain the historical former name and are migrated only in current RE8 API/UI work.

- `decision:submission-differentiation-frontload`
  - Created: 2026-08-30T10:40+09:00
  - Updated: 2026-08-30T10:40+09:00
  - Status: active
  - Content: The current proposal and function-specification Markdown drafts lead with the service's primary differentiation: using the current financial state as one baseline to compare no policy with non-debt support or up to three policy alternatives, each applied separately, across 13-week cash flow and six-month debt and repayment burden. The proposal's differentiation section also contrasts this decision question with the discovery and diagnosis questions answered by other service types.
  - Evidence: User approval on 2026-08-30; `제출/08_공모전_기획서_원고_및_시각자료_2차수정본.md` sections 1 and 4; `제출/09_기능명세서_원고_및_시각자료_2차수정본.md` section 1.

- `decision:implementation-checklist`
  - Created: 2026-08-14T20:21+09:00
  - Updated: 2026-08-21T14:06+09:00
  - Status: active
  - Content: The checklist records completed Stage 0-6 and RE Stage 1-8.3 with Gate evidence. RE8.3 was permanently closed on 2026-08-21 and must not be reopened; all current user-directed service revisions use the separate V2 plan and ledger. Existing RE9 artifacts remain a preserved pre-V2 baseline, and deployment remains paused pending V2 completion and separate approval.
  - Evidence: `MVP 단계별 구현 체크리스트.md`, `프로젝트 계획서.md`, `reports/re_stage8_3/service_review_log.md`, `V2 단계별 구현 계획표.md`, and `reports/v2/service_review_log.md`.

- `decision:re-stage9-local-submission-package`
  - Created: 2026-08-17T14:24+09:00
  - Updated: 2026-08-17T14:24+09:00
  - Status: active
  - Content: The user approved partial refinancing for the 80 million won high-debt persona: refinance only the official 50 million won cap and retain the remaining 30 million won on its original schedule. RE9 local QA passed 8/8 personas, 20/20 BM25 official-evidence cases, zero prohibited positive claims, two-attempt Embedding fallback, safe invalid-input handling, and 149 project tests; screenshot image analysis was not performed by user request.
  - Evidence: `scripts/build_re_stage7_examples.py`, `data/samples/re_stage9/`, `scripts/build_re_stage9_evidence.py`, `tests/test_re_stage9.py`, `reports/re_stage9/manifest.json`, and `output/pdf/RE9_기능명세서.pdf`.

- `decision:re-stage8-3-user-review-cycle`
  - Created: 2026-08-17T14:33+09:00
  - Updated: 2026-08-21T14:06+09:00
  - Status: superseded
  - Content: RE8.3 is complete and permanently closed by explicit user instruction. It must not be resumed; the replacement is the active V2 review cycle in `reports/v2/service_review_log.md`, beginning with the next ID `V2-006`.
  - Evidence: `reports/re_stage8_3/service_review_log.md`, `MVP 단계별 구현 체크리스트.md`, `프로젝트 계획서.md`, and `reports/v2/service_review_log.md`.

- `decision:v2-user-experience-traceability-baseline`
  - Created: 2026-08-23T11:55+09:00
  - Updated: 2026-08-23T11:55+09:00
  - Status: active
  - Content: Sections 3.10-3.15 of `V2 단계별 구현 계획표.md` are the authoritative current UX and code-traceability baseline for the next competition-purpose and AI-strength comparison. They distinguish user-visible question-first flow from the server's search-first question construction, candidate-specific staged questions from answer-adaptive branching, and live LightGBM from the current BM25 and local-brief fallbacks.
  - Evidence: `V2 단계별 구현 계획표.md`, `reports/v2/service_review_log.md` V2-012, `app/static/index.html`, `app/static/app.js`, `app/main.py`, `src/integration/re_stage8.py`, model/search/rule/cash/Event/recommendation modules, and a local comparison API probe.

- `decision:conditional-policy-ui-placement`
  - Created: 2026-08-21T08:52+09:00
  - Updated: 2026-08-21T09:18+09:00
  - Status: active
  - Content: Step 3 cash diagnosis has no conditional-policy control. Step 4 always restores the six original comparison alternatives, labels unconfirmed policy effects as assumptions, and excludes those alternatives from recommendation rankings; there is no extra toggle or questionnaire blocking the comparison.
  - Evidence: User correction in RE8.3-002; `app/static/index.html`, `app/static/app.js`, `src/integration/re_stage8.py`, and focused tests.

- `decision:financial-policy-service-scope`
  - Created: 2026-08-21T09:18+09:00
  - Updated: 2026-08-21T09:18+09:00
  - Status: active
  - Content: Default step-4 discovery and all-policy chat are limited to 10 policies whose effects directly concern business cash, debt, operating cost, or restart. Hospital living expense, private childcare, restricted savings, effects outside six months, closed programs, and financially unverified programs remain in the 17-policy audit database but are hidden from the default service flow.
  - Evidence: `대회개요.md`, `FINANCIAL_POLICY_NEEDS` in `src/integration/re_stage8.py`, `app/static/app.js`, and `tests/test_re_stage8_2.py`.

- `decision:goal-ranking-precompute`
  - Created: 2026-08-21T09:45+09:00
  - Updated: 2026-08-21T10:38+09:00
  - Status: active
  - Content: Each scenario response exposes all four deterministic goal rankings already produced by RE7. Step 4 shows the first alternative and key metric inside all four result cards; selecting a criterion only reorders alternatives and the table locally, while preserving the user's selected alternative, graph/card emphasis, and linked policy-chat scope whenever that alternative remains available.
  - Evidence: `src/integration/re_stage8.py`, `app/static/app.js`, `tests/test_re_stage8.py`, and live `127.0.0.1:8000` comparison response with four goal keys.

- `decision:policy-discovery-goal-independence`
  - Created: 2026-08-21T10:02+09:00
  - Updated: 2026-08-21T10:02+09:00
  - Status: active
  - Content: Step-4 policy discovery depends on store inputs such as area, industry, sales, costs, debt, and cash risk, but not on the four alternative-ordering goals. With the same store inputs, changing a goal must preserve candidate IDs and situation labels.
  - Evidence: User approval in RE8.3-003; `_situation_summary` in `src/integration/re_stage8.py`, the policy-search explanation in `app/static/app.js`, focused regression tests, and live paired goal requests.

- `decision:policy-chat-actionable-plain-text`
  - Created: 2026-08-21T10:24+09:00
  - Updated: 2026-08-21T10:24+09:00
  - Status: active
  - Content: Step-4 alternative selection synchronizes the policy-chat scope: no-action and cost-only choices use all financial policies, while directly linked policy alternatives select that policy. Eligibility questions must name missing policy checks and the next action rather than stop at indeterminate; Luna output is constrained and normalized to plain text on both server and client.
  - Evidence: `app/static/app.js`, `src/integration/re_stage8.py`, `src/rag/luna_client.py`, `tests/test_re_stage8.py`, and static asset version `re8.3-005.1`.

- `decision:market-scenario-cross-step-continuity`
  - Created: 2026-08-21T10:38+09:00
  - Updated: 2026-08-21T10:38+09:00
  - Status: active
  - Content: The step-3 market-sales range is the calculation assumption for both the current cash diagnosis and every step-4 alternative. Both screens show the active range and 13-week rate, and the step-4 status returns directly to the step-3 selector for changes.
  - Evidence: `app/static/index.html`, `app/static/app.js`, `app/static/styles.css`, `tests/test_re_stage8.py`, and static asset version `re8.3-006.1`.

- `decision:cash-threshold-user-language`
  - Created: 2026-08-21T10:56+09:00
  - Updated: 2026-08-21T11:04+09:00
  - Status: active
  - Content: User-facing `안전현금` is `앞으로 28일 필요현금`, a single minimum threshold equal to upcoming essential costs and debt payments. The yellow 0-to-threshold band is `28일 필요현금 미달 구간`; the unfilled area below zero is `현금 적자 구간`. No point marker or additional negative-zone fill is used, and both band labels render after chart lines so the text remains in front.
  - Evidence: `app/static/index.html`, `app/static/app.js`, `tests/test_re_stage8.py`, and static asset version `re8.3-008.2`; the internal `safe_cash` calculation contract is unchanged.

- `decision:policy-card-content-hierarchy`
  - Created: 2026-08-21T11:12+09:00
  - Updated: 2026-08-21T11:12+09:00
  - Status: active
  - Content: Step-4 policy cards show eligibility and application readiness only in the existing top badge. The body no longer repeats generic readiness or Event/simulation phrases; it shows one policy-specific sentence describing the core support from the reviewed local notice.
  - Evidence: `app/static/app.js`, `tests/test_re_stage8.py`, the reviewed local policy Markdown files under `data/raw_re/policy/`, and static asset version `re8.3-009.1`.

- `decision:comparison-loading-feedback`
  - Created: 2026-08-21T11:23+09:00
  - Updated: 2026-08-21T11:28+09:00
  - Status: active
  - Content: The centered blocking loading overlay appears only after the step-2 `현금 진단 보기` action passes validation and remains through market-range retrieval plus all three cash comparisons. It displays actual elapsed time from `경과 시간 0초`, updates once per second without repeated screen-reader announcements, and clears and resets on success or failure. Presentation presets fill inputs and invalidate prior results but perform no range fetch or comparison until that same step-2 action.
  - Evidence: `app/static/index.html`, `app/static/styles.css`, `app/static/app.js`, `tests/test_re_stage8.py`, and static asset version `re8.3-010.3`.

- `decision:policy-source-hierarchy`
  - Created: 2026-08-15T21:23+09:00
  - Updated: 2026-08-15T22:01+09:00
  - Status: active
  - Content: Bizinfo is the broad automated policy-candidate feed. Small Business 24, SEMAS policy-fund pages, and Seoul notices are bounded official verification sources for only the user-approved 8-12 policies: do not crawl every notice and do not submit a real policy application; preserve each selected policy's detail URL, notice and attachments, dates/status, and application URL for service handoff.
  - Evidence: Official Small Business 24, SEMAS, and Seoul pages checked on 2026-08-15; SEMAS explicitly directs users from overview terms to detailed notices, and the Seoul change notice provides the operative HWP notice and annexes.

- `decision:data-download-catalog`
  - Created: 2026-08-15T21:39+09:00
  - Updated: 2026-08-16T00:25+09:00
  - Status: active
  - Content: `data/raw_re/향후 데이터 다운로드 가이드.md` is the current links-and-instructions guide. Historically, Codex collected P-01/P-05 and 15 selected-policy files while P-03/P-04 were user-provided. For future needs, Codex must proactively report the reason, timing, exact scope, official links, and target paths; link research is allowed, but the user performs downloads and project raw-data loading before Codex processes local files.
  - Evidence: `data/raw_re/policy/`, `data/processed_re/policy/re_stage2/source_manifest.csv`, `reports/re_stage2/api_accessibility.md`, and `reports/re_stage2/structured_qa.md`.

- `decision:re-stage3-input-calculation-contract`
  - Created: 2026-08-16T00:25+09:00
  - Updated: 2026-08-17T12:37+09:00
  - Status: active
  - Content: Gate RE3 passed with `re3-v1`. RE8.1 now takes six recent monthly revenues by default and up to 12, with newest month first; it uses the rounded mean for the cash-flow baseline and newest-versus-oldest direction only for categorical policy discovery. Six months improve the stability of user-input cash context but do not retrain or increase the intrinsic precision of the independent area-industry LightGBM. All guided amounts are ten-thousand-won units and UTF-8-SIG Korean CSV remains supported.
  - Evidence: `src/cashflow/quick_mode.py`, `app/static/templates/`, `src/integration/re_stage8.py`, `tests/test_re_stage8.py`, and `reports/re_stage8/verification.md`; full tests 125 passed.

- `decision:re-stage8-api-web-local-rag`
  - Created: 2026-08-17T08:19+09:00
  - Updated: 2026-08-17T13:54+09:00
  - Status: active
  - Content: Gate RE8 remains complete and the current API is `re8-api-v1.4`. Presentation presets and the four-step flow remain, while the decision screen now adds Hybrid policy discovery, staged questions, availability and eligibility separation, and reviewed dynamic alternatives. The five-turn page-memory chat remains explanation-only and locally redacts approved sensitive patterns before external calls.
  - Evidence: `app/static/`, `src/integration/re_stage8.py`, `config/re_stage8.yaml`, `reports/re_stage8_2/`, and `tests/test_re_stage8_2.py`; all 144 tests, JavaScript syntax, whitespace checks, and current-code local browser rendering passed.

- `decision:re-stage8-2-hybrid-policy-discovery-plan`
  - Created: 2026-08-17T11:41+09:00
  - Updated: 2026-08-17T13:54+09:00
  - Status: complete
  - Content: RE8.2 indexes 17 user-reviewed Markdown policies as 817 chunks plus complete small 1536D and large 3072D vectors, while HTML remains link-only. The approved runtime is large 3072D Hybrid with five-second timeout, no more than two attempts, and BM25 fallback. Seventeen policies have district, industry, availability, effective-date, version, Rule-engine, and Event-status metadata; ten use frozen RE6 Rules and seven use a separate deterministic overlay. Candidate-specific questions preserve unknown states, and only reviewed business-cash Events with explicit user financial inputs become dynamic RE7 alternatives. Personal living cash, restricted savings, service subsidies, out-of-horizon effects, and closed calls are not promoted.
  - Evidence: `reports/re_stage8_2/approved_contract.md`, `reports/re_stage8_2/manifest.json`, `data/processed_re/policy/re_stage8_2/`, `src/policy/discovery.py`, `src/policy/re_stage8_2_events.py`, and `tests/test_re_stage8_2.py`; 40-case evaluation passed with Hybrid-large Recall@5 and Hit@5 1.000, MRR 0.872, new-policy Hit@5 1.000, safety 8/8, and all 144 project tests passed.

- `decision:policy-pdf-text-only`
  - Created: 2026-08-17T11:04+09:00
  - Updated: 2026-08-17T11:04+09:00
  - Status: active
  - Content: Policy PDFs are converted to UTF-8 page-delimited text with `pypdf` and only text is chunked into the local SQLite RAG database. Future extraction must not render PDF pages, create contact sheets, OCR, or analyze PDF images. Historical temporary renders may exist but are not RAG inputs and were not inspected in this follow-up.
  - Evidence: `scripts/extract_re_stage2_policy_docs.py`, `scripts/build_re_stage2_knowledge_base.py`, `reports/re_stage2/document_inventory.csv`, `data/processed_re/policy/re_stage2/extracted_text/`, and `tests/test_re_stage8.py`.

- `decision:presentation-and-user-validation`
  - Created: 2026-08-16T11:28+09:00
  - Updated: 2026-08-16T16:47+09:00
  - Status: active
  - Content: Competition messaging centers the 13-week survival Hero and never claims personal future prediction or optimal recommendation. Because the user cannot recruit real small-business owners, the approved substitute is 8 fixed synthetic personas with frozen inputs and oracle outputs comparing policy-list and simulator screens; pass requires 8/8 expected actions and core values plus zero prohibited claims. It is functional mock validation only, so no synthetic satisfaction, comprehension, quotes, real-usability, or real-policy-effect claims are allowed.
  - Evidence: `프로젝트 계획서.md` Parts 7-9, `프로젝트 차별화 구상.md` sections 18-20, and RE7-RE9 items in `MVP 단계별 구현 체크리스트.md`.

- `decision:re-stage4-policy-financial-event-engine`
  - Created: 2026-08-16T10:47+09:00
  - Updated: 2026-08-16T10:47+09:00
  - Status: active
  - Content: Gate RE4 passed with contract `re4-v1`. All 30 reviewed RE2 financial Events across 10 policies remain represented: 27 are calculable only with explicit user scenario values, `SEOUL_SAFE_ACCOUNT` and `SAFETY_TEST` are blocked because official financial terms are missing, and `SEOUL_FACILITY` requires a subproduct selection. The engine supports grants, reimbursements, vouchers, direct and interest-subsidized loans, refinancing, and guarantees with linked-event deduplication, source provenance, approved/not-approved scenarios, and no approval probability or causal-effect claim.
  - Evidence: `src/policy/`, `config/re_stage4.yaml`, `data/processed_re/policy/re_stage4/policy_event_profiles.csv`, `reports/re_stage4/verification.md`, `reports/re_stage4/manifest.json`, and `tests/test_re_stage4_policy_events.py`; hand checks 26/26, RE4 tests 12 passed, and full tests 64 passed.

- `decision:re-stage5-partial-contract`
  - Created: 2026-08-16T11:00+09:00
  - Updated: 2026-08-16T22:21+09:00
  - Status: active
  - Content: Gate RE5 passed by explicit user approval. The frozen LightGBM Quantile model is the internal aggregate-scenario generator; screens expose only `하방·기준·회복` and cash-flow effects, while P10/P50/P90, Coverage, Pinball Loss, and Holdout statistics remain internal QA. It never determines eligibility, approval, or policy rank; direct shock input is the fallback, and frozen Stage 6 remains retired.
  - Evidence: `reports/re_stage5/holdout/verification.md`, `reports/re_stage5/holdout/holdout_manifest.json`, `scripts/verify_re_stage5_holdout.py`, `src/models/re_stage5_artifact.py`, and `config/re_stage5.yaml`; predictions 64,356, duplicate/nonfinite/corrected-crossing errors 0, manifest outputs 7/7 and artifacts 3/3 verified, full tests 73 passed.

- `decision:re-stage6-eligibility-rag-safety`
  - Created: 2026-08-16T22:21+09:00
  - Updated: 2026-08-17T11:30+09:00
  - Status: active
  - Content: Gate RE6 passed with `re6-v1`. A deterministic engine evaluates 56 reviewed official rules and separates eligibility from application availability. Retrieval is lexical BM25 over word and Korean-character-bigram tokens in 227 SQLite text chunks with policy/version/effective-date filters; it does not create or store vector embeddings and uses no vector database or cosine search. `SafeExplanation` fact-locks calculations, eligibility, approval probability, effects, and rank before Luna explains retrieved evidence.
  - Evidence: `src/policy/eligibility.py`, `src/rag/policy_index.py`, `src/rag/local_db.py`, `src/rag/safe_explanation.py`, `config/re_stage8.yaml`, and `reports/re_stage6/`; reviewed examples 20/20, retrieval Hit@3 8/8, MRR 0.7917, unique official chunks 227/227, with no embedding API, vector column, FAISS/Chroma, model training, or raw session-profile persistence.

- `decision:re-stage7-candidate-routing-partial-contract`
  - Created: 2026-08-16T22:28+09:00
  - Updated: 2026-08-16T23:00+09:00
  - Status: active
  - Content: Gate RE7 passed with `re7-v1` under the unchanged `re7-contract-v1`: separate eligibility/availability routing, conservative pair compatibility, Target A/B horizon mapping with direct override, 28-day editable safe cash, no-action plus five intervention forms, lexicographic four-goal ranking, actionable-only Pareto, and execution plans. Conditional policies may be simulated only by explicit assumption and never receive a default or fast-execution top rank.
  - Evidence: `src/recommendation/`, `config/re_stage7.yaml`, `tests/test_re_stage7.py`, `data/samples/re_stage7/`, `data/processed_re/re_stage7/`, and `reports/re_stage7/`; three detailed samples, six Hero alternatives, RE7 tests 14 and full tests 103 passed, deterministic Manifest SHA-256 `609FDD3274BA4C1605010551B2C1EEEB77C2EA7638B1EE350A86D43650A10699` matched across reruns.

- `decision:pre-re1-policy-qa`
  - Created: 2026-08-15T23:18+09:00
  - Updated: 2026-08-15T23:18+09:00
  - Status: superseded
  - Content: Before RE1 approval, downloaded P-01/P-03/P-04/P-05 policy material may undergo source preservation, inventory, format QA, lossless common-schema conversion, and exact normalized-title grouping only. The verified pool contains 1,005 source records in 827 groups, including 174 multi-source groups. Fuzzy matching, exclusions, ranking, an 8-12-policy representative selection, eligibility Rules, financial Events, and RAG chunks require RE1 and explicit selection-criteria approval.
  - Evidence: `scripts/qa_integrate_policy_candidates.py`, `reports/pre_re1/policy/QA.md`, `reports/pre_re1/policy/selection_decision_needed.md`, and `data/processed_re/policy/pre_re1/`.

- `decision:re-stage1-contract`
  - Created: 2026-08-15T23:40+09:00
  - Updated: 2026-08-15T23:40+09:00
  - Status: active
  - Content: RE Stage 1 is complete. The service targets Seoul small businesses, compares 13-week and 6-month no-action and policy-intervention cash flows, uses minimum debt as the default goal, accepts simple input plus CSV, retires the old financial-burden score and simple policy ranking, and freezes Stage 0-6 as a baseline. Its pending portfolio decision was resolved in RE2 by explicit A+C approval.
  - Evidence: `reports/re_stage1/service_contract.md`, `config/re_stage1.yaml`, `reports/re_stage1/policy_portfolio_comparison.md`, and `reports/re_stage1/verification.md`.

- `decision:re-stage2-policy-knowledge-base`
  - Created: 2026-08-16T00:08+09:00
  - Updated: 2026-08-17T13:16+09:00
  - Status: active
  - Content: The user approved A+C as the final 10-policy Rule/Event portfolio. RE2 preserves 27 source records and structures 10 Metadata rows, 56 eligibility Rules, 20 reviewed eligibility examples, 30 financial Events, 11 versions, and 217 pre-index text chunks. The user later deleted seven obsolete PDF/HWPX originals and approved reviewed Markdown as sufficient; eight affected manifest rows now point to the exact Markdown files with recomputed size and SHA-256. Missing amounts, dates, status, or processes remain `미확인`.
  - Evidence: `config/re_stage2.yaml`, `data/processed_re/policy/re_stage2/`, `reports/re_stage2/structured_qa.md`, `reports/re_stage2/verification.md`, and nine passing RE2 tests.

- `convention:stage-result-feedback-loop`
  - Created: 2026-08-15T23:40+09:00
  - Updated: 2026-08-15T23:40+09:00
  - Status: active
  - Content: After every Stage Gate, compare actual results with assumptions and assess downstream data, Target, Feature, model, metric, policy, service, schedule, and test impacts. Record either no change with evidence or update affected plans/contracts/config/tests, obtain user approval for material meaning or scope changes, and do not start the next Stage until this feedback review is complete.
  - Evidence: `프로젝트 계획서.md` section 5.2, `MVP 단계별 구현 체크리스트.md` section 1.6 and all Gate RE1-RE9 items, and `reports/re_stage1/service_contract.md`.

- `decision:stage0-stack`
  - Created: 2026-08-14T20:34+09:00
  - Updated: 2026-08-14T21:00+09:00
  - Status: active
  - Content: Use Python 3.13.1, FastAPI, YAML central settings, environment-variable secrets, and pytest; do not emit fabricated risk or policy results before verified data, model, and policy evidence exist.
  - Evidence: `requirements.txt`, `.python-version`, `config/settings.yaml`, `.env.example`, `app/main.py`, `scripts/verify_stage0.ps1`, and `tests/`.

- `decision:solo-team-validation`
  - Created: 2026-08-14T21:14+09:00
  - Updated: 2026-08-14T22:45+09:00
  - Status: active
  - Content: This is a one-person project; Stage 0 team-scope confirmation is the user's own review, and separate-environment verification may use a clean virtual environment on the same machine.
  - Evidence: User clarification, `scripts/verify_stage0.ps1`, `reports/stage0/verification.md`, and the completed Stage 0 checklist.

- `decision:stage3-panel-contract`
  - Created: 2026-08-14T23:13+09:00
  - Updated: 2026-08-14T23:17+09:00
  - Status: active
  - Content: Use estimated sales as the 2021Q1-2025Q4 panel base, left-join stores on quarter-area-industry and datasets 4-9 on quarter-area, preserve unmatched and extreme values with flags, and derive only current-or-past features; Target remains Stage 4 work.
  - Evidence: `src/data/build_stage3_panel.py`, `reports/stage3/panel_manifest.json`, and `data/processed/stage3_panel.parquet`.

- `decision:stage4-persistent-target-structure`
  - Created: 2026-08-14T23:47+09:00
  - Updated: 2026-08-15T00:06+09:00
  - Status: active
  - Content: Predict persistent deterioration over two future quarters: both quarters must have negative YoY sales growth and their combined YoY sales growth must be at or below -10%. This keeps development prevalence at 25.28% while excluding minor declines; locked 2025 Target statistics were not used.
  - Evidence: User approval, `config/stage4.yaml`, `reports/stage4/target_definition.md`, and `reports/stage4/stage4_manifest.json`.

- `decision:stage4-cv-design`
  - Created: 2026-08-14T23:47+09:00
  - Updated: 2026-08-14T23:47+09:00
  - Status: active
  - Content: Use four chronological expanding-window folds over 2024, purge one quarter so two-quarter outcome windows do not overlap train and validation, refit through target-end 2024Q3, and lock target-end 2025Q1-Q4 for one final evaluation.
  - Evidence: User approval and `config/stage4.yaml`.

- `decision:stage5-model-selection-workflow`
  - Created: 2026-08-14T23:49+09:00
  - Updated: 2026-08-15T00:12+09:00
  - Status: active
  - Content: Do not preselect a final model. Compare a broad untuned set spanning simple, L2/L1/Elastic-Net logistic, bagging, and boosting families under the same four folds; select the top three candidates, run Optuna only on those three, then consider OOF-based voting or stacking.
  - Evidence: User instruction and Stage 5 in `MVP 단계별 구현 체크리스트.md`.

- `decision:stage5-comparison-contract`
  - Created: 2026-08-15T00:32+09:00
  - Updated: 2026-08-15T00:32+09:00
  - Status: active
  - Content: The approved base screen covers Dummy, L2/L1/Elastic-Net Logistic, Random Forest, Extra Trees, LightGBM, XGBoost, and CatBoost. AUROC and AUPRC/AP are co-primary; probability quality and fold stability are secondary, while F2 is reserved for OOF operating-threshold selection after tuning.
  - Evidence: User approval and `config/stage5.yaml`.

- `decision:stage45-modeling-eda-plan`
  - Created: 2026-08-15T00:39+09:00
  - Updated: 2026-08-15T14:59+09:00
  - Status: active
  - Content: Stage 4.5 plot-free EDA is complete on 122,011 Fold 1 Train rows from target-end 2022Q2-2023Q3, covering 199 originals and 134 derived candidates; 2024 Validation Target and locked 2025 were not accessed. Gate 4.5 passed and approved option D was subsequently executed in Stage 5.
  - Evidence: `reports/stage45/`, `src/analysis/run_stage45_eda.py`, `src/features/build_stage45_features.py`, and `MVP 단계별 구현 체크리스트.md`.

- `decision:stage45-feature-contract-d`
  - Created: 2026-08-15T12:17+09:00
  - Updated: 2026-08-15T13:10+09:00
  - Status: active
  - Content: Option D was implemented with an A-style common baseline, linear-only log1p Features, and five independent tree raw-detail Ablations. The user rejected precommitted numeric retention cutoffs: disclose every fixed metric and baseline delta first, then make a holistic user-approved choice without automatic ranking.
  - Evidence: User approval, `reports/stage45/feature_contract.md`, `config/stage5.yaml`, and Stage 5 in `MVP 단계별 구현 체크리스트.md`.

- `decision:ml-observation-unit`
  - Created: 2026-08-15T12:22+09:00
  - Updated: 2026-08-15T12:22+09:00
  - Status: active
  - Content: One ML observation and Target is one reference quarter x official Seoul commercial-area code x service-industry code; it represents the aggregate sales environment of all stores in that area-industry cell, not one store and not the whole commercial area across industries.
  - Evidence: `reports/stage2/quality_validation_plan.md`, `src/data/build_stage3_panel.py`, `src/data/build_stage4_dataset.py`, and `reports/stage4/target_definition.md`.

- `decision:stage5-full-comparison-result`
  - Created: 2026-08-15T14:59+09:00
  - Updated: 2026-08-15T17:25+09:00
  - Status: active
  - Content: Completed all 34 untuned model-Feature variants over four fixed chronological Folds (136 successful runs, zero failures) without locked-2025 access or automatic ranking. The user subsequently approved LightGBM common, XGBoost plus transaction raw components, and CatBoost plus worker raw components as the three Optuna candidates.
  - Evidence: `reports/stage5/full_comparison.md`, `full_model_feature_summary.csv`, `full_manifest.json`, and `checkpoints_v2/`.

- `decision:stage5-optuna-result`
  - Created: 2026-08-15T17:25+09:00
  - Updated: 2026-08-15T17:43+09:00
  - Status: active
  - Content: Completed 20 multi-objective Optuna Trials per approved candidate over the same four chronological Folds: 60 Trials and 240 Fits, zero failures, with no locked-2025 access. The user approved the mean-performance representatives LightGBM 10 (AP 0.6436, AUC 0.8104), XGBoost 16 (0.6421, 0.8100), and CatBoost 18 (0.6364, 0.8057) for the next OOF ensemble comparison.
  - Evidence: `reports/stage5/optuna_report.md`, `optuna_trials.csv`, `optuna_pareto_trials.csv`, and `optuna_manifest.json`.

- `decision:stage5-oof-ensemble-run-plan`
  - Created: 2026-08-15T17:43+09:00
  - Updated: 2026-08-15T18:10+09:00
  - Status: active
  - Content: Compare the three approved representative models, fixed equal-weight Soft Voting, and leakage-safe nested OOF L2-Logistic Stacking over the four fixed Outer Folds. The user completed all 48 model Fits plus four ensemble steps in PowerShell with no failure, final selection, or locked-2025 access.
  - Evidence: `src/models/run_stage5_oof_ensemble.py`, `scripts/run_stage5_oof_ensemble.ps1`, `reports/stage5/oof_ensemble_runbook.md`, and `config/stage5.yaml`.

- `decision:stage5-oof-ensemble-result`
  - Created: 2026-08-15T18:10+09:00
  - Updated: 2026-08-15T18:29+09:00
  - Status: active
  - Content: Equal-weight Soft Voting was the performance-first recommendation: mean Fold AP 0.6456, mean AUC 0.8111, overall OOF AP 0.6474, worst-Fold AP 0.6147, Brier 0.1562, and Log Loss 0.4742. Its overall OOF AP/AUC gains over LightGBM 10 were only 0.0020/0.0007; the later service-first decision selected LightGBM.
  - Evidence: `reports/stage5/selected_oof_report.md`, `selected_oof_summary.csv`, `selected_oof_fold_metrics.csv`, `selected_oof_industry_metrics.csv`, and `selected_oof_manifest.json`.

- `decision:stage5-service-first-policy`
  - Created: 2026-08-15T18:21+09:00
  - Updated: 2026-08-15T18:29+09:00
  - Status: active
  - Content: The user selected LightGBM Trial 10 with the 197-feature common baseline as the final model before locked 2025. A single deployable and maintainable model better serves the working AI financial-service MVP than Soft Voting's small OOF gain; locked 2025 is a one-time audit and cannot be used to switch models.
  - Evidence: User direction, `대회개요.md`, `프로젝트 계획서.md`, `MVP 단계별 구현 체크리스트.md`, and `config/stage5.yaml`.

- `decision:stage5-threshold-service-policy`
  - Created: 2026-08-15T18:21+09:00
  - Updated: 2026-08-15T19:08+09:00
  - Status: active
  - Content: The primary service output is relative ranking, so no binary operating threshold is required now. Consider a threshold or fixed Top-k only if the service later adds an actual inclusion/exclusion action; use pre-2025 OOF plus intervention capacity and explicit user approval, never locked-2025 labels.
  - Evidence: User proposal, `reports/stage5/selected_oof_predictions.parquet`, `MVP 단계별 구현 체크리스트.md`, and `config/stage5.yaml`.

- `decision:stage5-final-2025-result`
  - Created: 2026-08-15T18:57+09:00
  - Updated: 2026-08-15T18:57+09:00
  - Status: active
  - Content: The one-time locked-2025 audit refit LightGBM Trial 10 on 202,918 rows and evaluated 79,506 rows: AP 0.625695, AUC 0.791821, Brier 0.164177, and Log Loss 0.495829. The model remains suitable for area-industry risk prioritization, not automatic decisions or individual-store failure probability; no threshold metrics were computed.
  - Evidence: `reports/stage5/final_2025_report.md`, `final_2025_manifest.json`, `final_2025_metrics.json`, `final_2025_predictions.parquet`, and `artifacts/stage5_lightgbm_trial10.joblib`.

- `decision:stage6-relative-ranking-output`
  - Created: 2026-08-15T19:08+09:00
  - Updated: 2026-08-15T20:08+09:00
  - Status: active
  - Content: Stage 6 is implemented on the 2025Q4 reference distribution of 21,333 area-industry rows. Policy v1 returns same-industry and Seoul-wide Percentiles, top shares, competition ranks, and TreeSHAP directions without exposing the internal score, a binary label, or an operating threshold.
  - Evidence: `config/stage6.yaml`, `src/models/stage6_risk_service.py`, `reports/stage6/stage6_manifest.json`, `reports/stage6/verification.md`, and `tests/test_stage6_risk_service.py`.

- `decision:recommendation-role-boundary`
  - Created: 2026-08-15T19:32+09:00
  - Updated: 2026-08-15T21:02+09:00
  - Status: active
  - Content: ML supplies aggregate area-industry downside, median, and recovery scenarios; official rules exclusively determine eligibility; a deterministic cash-flow engine calculates policy inflows, cost reductions, user contributions, and debt schedules; the decision engine compares outcomes for minimum debt, longest runway, minimum payment, or fastest action without an arbitrary universal score; RAG/LLM only retrieves and explains official evidence and trade-offs and cannot alter calculations, eligibility, or ordering.
  - Evidence: User-approved `프로젝트 계획서.md` rewrite, especially RE Stages 4 through 7.

- `decision:competitive-positioning`
  - Created: 2026-08-15T20:14+09:00
  - Updated: 2026-08-15T20:32+09:00
  - Status: active
  - Content: Do not claim novelty from commercial-district analysis, store diagnosis, AI sales forecasting, policy matching, proactive risk alerts, or one-stop recovery routing. The 2026 MSS Small Business Crisis AlertTalk already detects high-risk, delinquent, and closed borrowers and links diagnosis, debt counseling, and recovery support. A defensible service distinction must therefore expose the financial consequence of each intervention, not merely detect risk or list programs; do not claim a market first without a formal prior-art search.
  - Evidence: Public web research on 2026-08-15 against official Seoul, MSS, public-data, KB, and KCD sources; no reviewed public source showed a Korean official-policy cash-flow intervention simulator, but absence was not proven.

- `proposal:policy-intervention-digital-twin`
  - Created: 2026-08-15T20:32+09:00
  - Updated: 2026-08-16T20:40+09:00
  - Status: active_plan
  - Content: The policy-impact simulator is the approved project-plan direction. `프로젝트 계획서.md` preserves completed Stage 0-6 as archived evidence and uses RE Stage 1-9 for the service. The existing binary LightGBM and Stage 6 are removed from service inference and display and will not be retrained; RE5 LightGBM Quantile is the sole service-ML candidate, with user direct shock rates as the non-model fallback.
  - Evidence: User instruction and the rewritten `프로젝트 계획서.md`; no data, Target, model, or application implementation was executed in the rewrite turn.

- `proposal:v3-bounded-agentic-orchestrator`
  - Created: 2026-08-23T12:07+09:00
  - Updated: 2026-08-24T14:27+09:00
  - Status: implemented
  - Content: The V2-copy-based V3 preserves the four-step UI and hierarchical circle map while adding confirmed situation context, no automatic policy selection, deterministic action plans, and engine-backed What-if. Policy questions remain one at a time on screen but are recalculated in at most two server batches of four then three; What-if supports revenue changes, cost reductions, market scenarios, and goals, rejects cost increases before Luna, and permits at most one clarification without accumulating replies.
  - Evidence: `V3 사용자 경험 구성안.md` now records the complete current four-stage experience, AI/tool boundaries, file wiring, 14 regression contracts, V3 limitations, and V4 experience choices across 18 sections; implementation evidence remains `v3/V2_BASELINE_SHA256.md`, `v3/orchestrator.py`, `v3/static/`, `v3/tests/test_v3.py`, and `v3/README.md`.

- `decision:stage6-service-retirement`
  - Created: 2026-08-16T20:40+09:00
  - Updated: 2026-08-16T20:40+09:00
  - Status: approved
  - Content: Do not run the frozen binary Stage 5 model and RE5 Quantile together. Do not retrain the binary model on newer data because its persistent-decline Target does not supply the continuous shock magnitude required by the cash-flow simulator. Remove Stage 6 inference, badges, relative-risk output, and TreeSHAP from the new service; preserve its files unchanged as audit and reproducibility evidence. Use RE5 Quantile as the only ML output and a user direct shock rate when it is unavailable.
  - Evidence: User direction, `config/re_stage5.yaml`, `reports/re_stage5/approved_contract.md`, `프로젝트 계획서.md`, `프로젝트 차별화 구상.md`, and `MVP 단계별 구현 체크리스트.md`.

- `decision:stage7-finance-burden-policy-v1`
  - Created: 2026-08-15T20:19+09:00
  - Updated: 2026-08-15T21:02+09:00
  - Status: superseded
  - Content: The previously approved 20/20/35/25 heuristic finance-burden index and low/caution/high bands were never implemented and are removed from the active plan. Individual ratios may remain as descriptive inputs, but service decisions use dated cash-flow balances, runway, debt service, total obligation, and intervention comparisons instead of a composite score.
  - Evidence: User-directed replacement of the old Stage 7 onward plan in `프로젝트 계획서.md`; the historical approval remains recorded here and in `LOG.md`.

## Working conventions

- `convention:user-owned-screen-validation`
  - Created: 2026-08-21T14:06+09:00
  - Updated: 2026-08-23T17:01+09:00
  - Status: active
  - Content: During V3 review, the user performs final visual validation. Codex may validate HTML, CSS, JavaScript, API responses, calculations, state contracts, tests, and DOM behavior, but must not create screenshots, upload images, or analyze images unless separately needed and authorized; user comments should be handled from their text and target metadata when image analysis is unnecessary.
  - Evidence: User instructions on 2026-08-21 and 2026-08-23; `reports/v2/service_review_log.md` and the V3 review session.

- `convention:user-owned-submission-document-editing`
  - Created: 2026-08-27T15:12+09:00
  - Updated: 2026-08-28T11:11+09:00
  - Status: active
  - Content: Preserve the official HWPX templates unchanged. Submission copy must omit version labels, development stages and internal work history, and contain only judge-facing problem, service, AI, data, expected-effect, safety and verification content. Each official document's next draft must contain its own screenshot placement, state, crop, caption and filename guidance rather than use a separate photo-guide document. Pipeline assets are content wireframes only: Codex defines the required inputs, processing, output, storage, transmission and authority boundaries, while the user may redesign their visual styling and retains HWPX/PDF layout and final visual approval.
  - Evidence: User instructions on 2026-08-27 and 2026-08-28; official templates; `제출/06_공모전_기획서_원고_및_시각자료_통합초안.md`; `제출/07_기능명세서_원고_및_시각자료_통합초안.md`; and their pipeline wireframes under `제출/assets/`.

- `convention:judge-readable-submission-prose`
  - Created: 2026-08-28T14:20+09:00
  - Updated: 2026-08-28T19:41+09:00
  - Status: active
  - Content: Revise proposal and function-specification copy from the judge's perspective. Every passage must be understandable on first reading and contain only the facts needed to explain the user task, inputs, processing, outputs, evidence, limits and responsibility boundary; remove development history, internal terminology, repetition and explanatory asides that do not help the judge evaluate the service. Prefer user-facing names, explicit source/input/use relationships and plain Korean, while keeping detailed operational information only where the official document requires it.

- `convention:image-analysis-contact-sheets`
  - Created: 2026-08-21T08:13+09:00
  - Updated: 2026-08-21T08:13+09:00
  - Status: active
  - Content: Whenever image analysis is authorized and needed, resize every source image to 50% of both width and height, combine at most four resized images into one contact sheet, and analyze the contact sheet. For more than four images, create additional sheets in groups of four. This workflow does not itself authorize image analysis in scopes where it remains explicitly excluded.
  - Evidence: User instruction on 2026-08-21.

- `convention:plan-source-preservation`
  - Created: 2026-08-14T19:55+09:00
  - Updated: 2026-08-14T19:55+09:00
  - Status: active
  - Content: When reorganizing the project plan, preserve all source information; treat embedded URLs as download references and do not browse or analyze them unless the user later asks.

- `convention:user-owned-data-acquisition`
  - Created: 2026-08-14T20:51+09:00
  - Updated: 2026-08-16T00:25+09:00
  - Status: active
  - Content: Codex must tell the user whenever a future Stage needs external data and may search official sites for exact source links. Codex must not call data APIs, crawl, download, save source files, or load them into project raw folders; the user performs download and loading, then confirms completion before Codex processes local files. Broad Stage authorization is not acquisition authorization, and this rule remains until explicitly revoked.
  - Evidence: User correction on 2026-08-16, root `AGENTS.md`, `프로젝트 계획서.md`, and `MVP 단계별 구현 체크리스트.md`.

- `convention:bounded-raw-inspection`
  - Created: 2026-08-14T22:35+09:00
  - Updated: 2026-08-14T23:05+09:00
  - Status: active
  - Content: Never load a large raw dataset into memory in full. Before preprocessing approval use bounded front-tail samples; after the user's Stage 2-3 approval, use at most 20,000-row CSV chunks and disk-backed joins, retaining only aggregate QA or generated panel outputs.

- `convention:chronological-project-log`
  - Created: 2026-08-14T22:35+09:00
  - Updated: 2026-08-14T22:35+09:00
  - Status: active
  - Content: Maintain root `LOG.md` separately from agent memory for presentation and portfolio provenance, with every entry timestamped to year, month, day, hour, and minute in KST.

- `convention:mandatory-user-decision`
  - Created: 2026-08-14T23:28+09:00
  - Updated: 2026-08-14T23:28+09:00
  - Status: active
  - Content: Stop before any choice that materially changes target meaning, data treatment, time split, metric, final model, scope, external publication, or an irreversible action; present options and a recommendation, then resume only after explicit user approval. Continue routine implementation without repetitive confirmation when no such choice exists.
  - Evidence: User instruction and root `AGENTS.md`.

- `convention:proportional-verification`
  - Created: 2026-08-14T23:31+09:00
  - Updated: 2026-08-14T23:31+09:00
  - Status: active
  - Content: Verify mandatory Stage Gates and result-critical facts once; when they pass, record nonessential failures and continue instead of repeating checks until perfect. Repeat only for a mandatory Gate failure, damaged output, core-number inconsistency, or reproducibility failure.
  - Evidence: User instruction, root `AGENTS.md`, and `MVP 단계별 구현 체크리스트.md`.

## Known issues and fixes

- `issue:re5-pandas-readonly-array`
  - Created: 2026-08-16T18:05+09:00
  - Updated: 2026-08-16T18:10+09:00
  - Status: resolved
  - Symptom: The second user CV attempt reached task 1 but failed before checkpoint creation with `ValueError: assignment destination is read-only` while filling the seasonal baseline's missing values.
  - Cause: Pandas 3 Copy-on-Write returned read-only NumPy views from `to_numpy`, while the seasonal baseline and later numeric preprocessor performed in-place finite/missing-value replacement.
  - Fix: Request explicit writable copies for every NumPy array mutated by seasonal and Train-only preprocessing; add regression tests, resumable failure-state recording, and a bounded `--max-new-tasks` smoke-run option.
  - Evidence: `src/models/run_re_stage5_quantile.py` and `tests/test_re_stage5.py`; 70 tests passed and the bounded first task completed with 20,600 prediction rows and a matching checkpoint hash.

- `issue:re5-derived-feature-materialization`
  - Created: 2026-08-16T17:59+09:00
  - Updated: 2026-08-16T18:04+09:00
  - Status: resolved
  - Symptom: The user's first RE5 CV command stopped before any fit because 117 of the approved 197 common-baseline features were absent from the prepared development Parquet.
  - Cause: The RE5 preparation script copied Stage 3's 199 original columns but the training contract referenced the Stage 4.5 feature-set manifest, whose 197 selected inputs include derived ratios, shares, densities, persistence, and rolling-sales features.
  - Fix: Run the existing leakage-safe `build_stage45_features` over the full chronological Panel before splitting RE5 development and holdout files; make prepare, verifier, and DryRun assert that all 197 approved features exist in both schemas.
  - Evidence: `src/data/build_re_stage5_baseline.py`, `src/models/run_re_stage5_quantile.py`, `scripts/verify_re_stage5.py`, and `reports/re_stage5/manifest.json`; regeneration, hashes, 197-feature schema checks, DryRun, and all 68 tests passed with zero model fits.

- `issue:bounded-reader-full-file-call`
  - Created: 2026-08-14T22:44+09:00
  - Updated: 2026-08-14T22:45+09:00
  - Status: resolved
  - Symptom: The initial encoding detector sliced the first 64 KiB only after `Path.read_bytes()` had loaded the complete CSV into memory.
  - Cause: The byte limit was applied after the full-file read instead of on the file stream.
  - Fix: Replace it with bounded stream reads from the first and last 64 KiB; verify that no `read_bytes`, `read_csv`, or `read_parquet` call remains in the schema scripts.
  - Evidence: `scripts/inspect_sample_schema.py`, `LOG.md`, and final `BOUNDED_READER=PASSED` validation.

- `issue:store-2025-header-language`
  - Created: 2026-08-14T22:35+09:00
  - Updated: 2026-08-14T23:05+09:00
  - Status: resolved
  - Symptom: `점포-상권` uses Korean headers in 2021 through 2024 but English headers in 2025.
  - Cause: The source file schema changed in the 2025 release.
  - Fix: Preserve both raw schemas and apply a verified 14-column English-to-Korean mapping only while reading the 2025 file during Stage 2-3 processing.
  - Evidence: `reports/stage2/schema_mapping.md`, `src/data/run_stage2_quality.py`, and `src/data/build_stage3_panel.py`.

- `issue:stage5-preprocessing-memory`
  - Created: 2026-08-15T00:32+09:00
  - Updated: 2026-08-15T14:59+09:00
  - Status: resolved
  - Symptom: Two pre-training attempts stopped before any real model fit because pandas numeric conversion and scikit-learn median imputation created large temporary arrays; a later run reached only the Dummy Fold 1 checkpoint before the user paused it.
  - Cause: Full-width 199-column preprocessing produced avoidable float64/int64 copies despite the compressed development Parquet being only 162.3 MiB in memory.
  - Fix: Implemented deterministic common/linear/tree-ablation Feature sets, union preprocessing with float32/category loading, per-set sparse slicing, and isolated `checkpoints_v2`; actual execution completed all 136 Fold runs without a memory failure.
  - Evidence: `src/models/run_stage5_base_comparison.py`, `src/features/build_stage5_feature_sets.py`, `reports/stage5/feature_sets.json`, and `reports/stage5/checkpoints_v2/`.

- `issue:bizinfo-mixed-registration-years`
  - Created: 2026-08-15T22:00+09:00
  - Updated: 2026-08-15T22:00+09:00
  - Status: resolved
  - Symptom: The API advertises a current-year feed but returned 1,521 records registered in 2026 plus 23 from 2025 and one from 2023.
  - Cause: The provider's unfiltered response contains older registration years even though all 1,545 records were advertised as the available feed.
  - Fix: Preserve every response page unchanged, derive a separate 2026-only dataset, and run the small-business candidate filter only on that required-year subset.
  - Evidence: `data/raw_re/policy/bizinfo/2026-08-15/manifest.json`, `current_year_2026_items.csv`, and `small_business_candidates.csv`.

- `issue:sme24-date-filter-semantics`
  - Created: 2026-08-15T22:19+09:00
  - Updated: 2026-08-15T22:19+09:00
  - Status: resolved
  - Symptom: The 2026 date-range queries returned 523 records registered in 2025 and 2,667 records with no `creatDt`, so treating the result as 2026 registrations would be incorrect.
  - Cause: In every one of the 8 request windows, all returned records had `updDt` inside the requested dates; observed API behavior applies `strDt/endDt` as an update-date filter.
  - Fix: Describe the P-05 collection as announcements updated during 2026-01-01 through 2026-08-15, retain older or missing registration dates, and record per-window registration-date and update-date counts in the Manifest.
  - Evidence: `data/raw_re/policy/sme24/2026-08-15/manifest.json`, `QA.md`, and the 8 raw files under `windows/`.

- `issue:re8-user-facing-ux`
  - Created: 2026-08-17T08:41+09:00
  - Updated: 2026-08-17T09:18+09:00
  - Status: resolved
  - Symptom: The RE8 eight-screen flow exposes internal terms, synthetic sample language, raw CSV schema, direct shock rates, unlabeled charts, and dense metric tables, so a real small-business user cannot easily connect inputs, recommendations, and next actions.
  - Cause: The first RE8 interface mirrored engine stages and verification artifacts instead of a user task model; it also advertises the RE5 model while the current comparison route actually applies user-supplied direct shocks and hardcoded Hero candidates.
  - Fix: Replaced the interface with the approved four-step workspace, 3-12-month guided finance input, RE5 live area-industry scenarios, result-first cards, selected-alternative modal, and execution/AI shortcuts. The user chose official center coordinates plus area-proportional circles rather than polygons; district and area lists remain available and synchronized with the map.
  - Evidence: `app/static/`, `src/integration/re_stage8.py`, `src/models/re_stage5_scenario_service.py`, `data/processed_re/re_stage8/`, and `reports/re_stage8/verification.md`; desktop and 390x844 browser flows passed with matching diagnosis/no-action values and zero console errors.

- `issue:re8-fixed-policy-candidate-routing`
  - Created: 2026-08-17T11:33+09:00
  - Updated: 2026-08-21T12:29+09:00
  - Status: resolved
  - Symptom: The current RE8.3 UI retrieves situation-based policy cards but provides no control that fills `eligibilityAnswers` or `policyScenarioValues`; therefore retrieved policies cannot be promoted to dynamic, ranking-eligible cash alternatives, and a live declining-sales example ranks only no-action and the fixed 5% cost-reduction assumption for all four goals.
  - Cause: RE8.3 removed the staged eligibility and policy amount/date controls while retaining empty client state and a fixed six-alternative comparison; server-side dynamic routing still requires explicit policy scenarios and actionable Rule status.
  - Fix: Implemented the approved architecture-preserving V2 flow. The UI now selects at most three retrieved policies, renders only their adaptive questions and supported amount/date inputs, and posts explicit selection state. V2 comparison removes the legacy fixed 5% and hardcoded Hero policies, creates a custom cost alternative only from category amounts, and creates policy alternatives only from complete user scenarios. A consent-gated Luna brief can rewrite recomputed locked facts, with local fallback.
  - Evidence: `V2 단계별 구현 계획표.md`, `app/static/`, `src/integration/re_stage8.py`, `src/cashflow/quick_mode.py`, `src/policy/re_stage8_2_events.py`, `src/rag/luna_client.py`; RE9-excluded full suite 152/152 and JavaScript syntax passed on 2026-08-21.

- `decision:v2-bounded-ai-copilot`
  - Created: 2026-08-21T12:29+09:00
  - Decision: Preserve the MVP engines, map, five presentation presets, chart interaction, loading overlay, CSV path, and accessibility contracts while making the V2 normal path diagnosis-first and policy-selective. Other fixed cost is a real cash Event. Cost reduction must be user-entered by category. Missing policy conditions remain conditional, and only complete user amount/date scenarios can enter the comparison. External LLM wording is optional and requires explicit on-screen consent.
  - Rationale: This closes the judge-visible AI integration gap without discarding validated finance, policy, model, and interaction assets or allowing an LLM to decide eligibility, money, or ranks.
  - Evidence: `V2 단계별 구현 계획표.md`, V2 API response key, `/api/v2/ai/action-brief`, and V2 regression tests in `tests/test_re_stage8_2.py`.

- `decision:v2-question-first-wizard`
  - Created: 2026-08-21T14:35+09:00
  - Updated: 2026-08-21T14:35+09:00
  - Status: active
  - Content: V2 step 3 asks one adaptive question at a time before showing policy results. Boolean choices are ordered `아니오 → 모르겠음 → 예` and advance immediately; date and numeric questions support an explicit unknown answer, and users can go back or restart answer review. The final answer reruns the existing comparison with the collected answers and then reveals the existing policy cards, amount/date inputs, cost reduction, recalculation, and step-4 comparison without redesigning those downstream screens. Until a dedicated pre-search intake API is separately reviewed, the initial discovery response may supply the reviewed question catalog internally while policy results remain hidden.
  - Evidence: `V2 단계별 구현 계획표.md`, `reports/v2/service_review_log.md`, `app/static/index.html`, `app/static/app.js`, `app/static/styles.css`, and focused V2 regression tests.

- `experiment:v2-optional-scenario-inputs`
  - Created: 2026-08-21T15:01+09:00
  - Updated: 2026-08-21T15:01+09:00
  - Status: evaluating
  - Content: V2-008 is a user-requested trial, not a frozen decision. The core path no longer shows policy amount/date or category cost-reduction forms. It displays the existing safe-cash gap `max(0, 28-day required cash - 13-week minimum cash)`, official policy ranges, and unquantified policy actions. Existing scenario and cost inputs remain available only after the user explicitly opens optional detailed calculation. Unquantified selected policies remain visible in step 4 but are excluded from numeric ranking; when no confirmed alternative exists beyond no-action, duplicate goal rankings, graph, and detail table are hidden. The user may keep, change, or discard this experiment after direct use.
  - Evidence: `reports/v2/service_review_log.md` V2-008, `V2 단계별 구현 계획표.md` sections 3.6.6 and V2-5, `app/static/index.html`, `app/static/app.js`, `app/static/styles.css`, and focused regressions.

- `issue:v2-selected-policy-impact-and-readiness-gap`
  - Created: 2026-08-22T23:12+09:00
  - Updated: 2026-08-23T00:44+09:00
  - Status: resolved
  - Symptom: V2-008 keeps selected but unquantified or ineligible policies visible without a cash graph or an application-readiness path, so users cannot compare likely impact or learn how to progress toward an application.
  - Cause: V2 currently couples graph visibility to confirmed amount/date Events and maps every failed hard/variant eligibility Rule to exclusion. For `POL_SEOUL_FUND_2026`, answering that no subfund has been selected fails `FUND_VARIANT`, producing `부적격 → 제외`, although selecting a subfund is a preparation step in this user journey.
  - Fix: V2-009 first separated hard failures, preparation, and official checks. V2-010 then integrates each selected policy's failed official condition, current answer, resolution action, application preparation, and automatically calculated no-action-versus-conditional cash preview in one page-4 work unit. Disclosed conditional assumptions are available regardless of current eligibility but remain outside eligibility prediction, all goal rankings, and Pareto. Rechallenge uses the reviewed general-type assumption of 2026 Q3 base rate 3.85% plus 1.6%p, five years with two-year grace.
  - Evidence: `reports/v2/service_review_log.md` V2-009 and V2-010, `V2 단계별 구현 계획표.md`, `src/integration/re_stage8.py`, `app/static/app.js`, `app/static/index.html`, `app/static/styles.css`, and focused regressions 38/38.

- `issue:v2-stale-server-request-schema`
  - Created: 2026-08-22T23:58+09:00
  - Updated: 2026-08-23T00:07+09:00
  - Status: resolved
  - Symptom: After choosing a page-1 presentation preset, page 2 `현금 진단 보기` shows the generic server validation message `입력값을 수정해 주세요.`
  - Cause: The current source request model accepts `conditional_policy_ids`, but the running FastAPI process was started before that model change. The live OpenAPI schema omits the field, so every current frontend comparison request receives HTTP 422 with `body.conditional_policy_ids: Extra inputs are not permitted`. The preset values themselves validate.
  - Resolution: Restarted the local Uvicorn process from the project `.venv`; live health is HTTP 200, live OpenAPI now includes both `selected_policy_ids` and `conditional_policy_ids`, and all five presentation preset payloads pass `SampleCompareRequest` validation. No input value or validation rule changed.

- `issue:v2-page4-policy-explanation-and-graph-scope`
  - Created: 2026-08-23T00:53+09:00
  - Updated: 2026-08-23T01:48+09:00
  - Status: resolved
  - Symptom: Page 4 shows a silently defaulted debt goal on unranked conditional cards, repeats evaluator prose instead of the user's exact answer, restarts all questions for one policy correction, and does not explain why only some selected policies appear in the combined graph.
  - Cause: Client state defaults to `최소부채` and reuses the active-goal component for all alternatives; `RuleEvaluation` omits the source input field and raw answer; the review action resets the whole wizard; conditional lines exist only for four mapped reviewed Events and their cash-need or existing-loan prerequisites, independent of eligibility likelihood.
  - Resolution: With user approval, conditional effects are now separate from recommendation goals. Readiness data preserves each original question, actual answer, and editable field; page 4 edits only the failed or unknown answer and returns to the same policy. Only remediable or official-confirmation cases with reviewed calculation assumptions can produce conditional graph alternatives. Structural exclusions explicitly suppress the graph and direct the user to other candidates, while calculation-unavailable policies explain the missing basis. A defensive server filter rejects forced structural conditional IDs.
  - Evidence: `reports/v2/service_review_log.md` V2-011, `V2 단계별 구현 계획표.md`, `app/static/app.js`, `app/static/index.html`, `app/static/styles.css`, `src/integration/re_stage8.py`, `src/policy/discovery.py`, and focused tests; 77 regressions, JavaScript syntax, whitespace, live HTTP, and live structural/remediable API probes passed.

- `issue:v3-page4-refinance-preview-alignment`
  - Created: 2026-08-23T16:26+09:00
  - Updated: 2026-08-23T16:32+09:00
  - Status: resolved
  - Symptom: After completing page 3 and selecting three policies, `다음 행동 확인` issued three `/api/v3/orchestrate` requests that returned HTTP 400 and showed only `입력 형식과 범위를 확인해 주세요.`
  - Cause: The selected refinance policy's reviewed conditional preview assumed execution after 28 days, while the shared cash engine intentionally permits automatic refinance before/after comparison only on the baseline reference date; this raised `REFINANCE_BASELINE_ALIGNMENT_REQUIRED`.
  - Fix: V3 now suppresses only that incompatible conditional refinance preview, marks its card as calculation unavailable with an actionable reason, synchronizes the client conditional-ID set to the sanitized server result, and keeps the selected policy visible for official follow-up. V3 also suppresses the harmless sklearn feature-name warning on its own scenario/orchestration paths without changing predictions or V2.
  - Evidence: `v3/orchestrator.py`, `v3/main.py`, `v3/static/app.js`, and `v3/tests/test_v3.py`; eight tests, JavaScript syntax, and whitespace passed. Live browser reuse of the exact failing page state reached page 4, retained the rechallenge conditional graph, and displayed the refinance calculation-unavailable explanation.

- `issue:v4-conditional-policy-graph-coverage`
  - Created: 2026-08-24T18:37+09:00
  - Updated: 2026-08-24T19:15+09:00
  - Status: resolved
  - Symptom: Step 4 repeatedly graphs the rechallenge loan but not the stability voucher or refinance policy, which can make a selected but ungraphed policy look impossible or irrelevant.
  - Cause: Conditional graph visibility is a separate calculation-coverage gate, not an eligibility verdict. The voucher is omitted from the four-policy preview allowlist despite its reviewed 250,000-won Event; V4 suppresses every refinance preview because the shared engine cannot yet align a four-week execution date with the remaining loan balance. Rechallenge additionally requires a positive safe-cash gap.
  - Fix: V4 now injects a reviewed voucher scenario using up to 250,000 won of monthly other fixed cost, and the shared refinance application guard validates the actual loan balance immediately before a future execution date. The conditional refinance builder uses that remaining balance, while structurally blocked policies keep no curve and expose the failed condition, current answer, resolution, and editable field. Step 4 now flows from graph to policy conditions to step 5.
  - Evidence: Live three-policy `/api/v4/orchestrate` response contains voucher, refinance, and rechallenge conditional alternatives with all three outside rankings; 93 focused regressions and JavaScript syntax pass. `v4/VERIFICATION.md` records the exact live values.

- `issue:v4-policy-effect-scale-compression`
  - Created: 2026-08-25T22:24+09:00
  - Updated: 2026-08-25T23:01+09:00
  - Status: resolved
  - Symptom: When the stability voucher, refinance, and rechallenge loan share one absolute-cash chart, the first two curves appear indistinguishable from no action while the rechallenge curve dominates the scale.
  - Cause: The three policies act through different financial mechanisms and magnitudes: the voucher offsets at most 250,000 won once, refinance adds no cash and only reduces future debt service, while rechallenge injects a new loan sized to the cash gap. The chart also visually de-emphasizes unselected curves.
  - Fix: Kept the absolute 13-week comparison and added a separate no-action delta card for every selected policy plus focused-policy metrics for week-13 cash, net new debt, and maximum monthly repayment. The graph is limited to no action and the user's selected policy alternatives, so unselected legacy alternatives no longer add visual noise.
  - Evidence: Live V4 API replay of the high-fixed-cost preset returned week-13 cash of -4,379,745 won for no action, -4,129,745 won for the voucher, -3,619,614 won for refinance, and 20,463,115 won for rechallenge; the new rendering is in `v4/static/app.js` and `v4/static/index.html`, with focused regressions in `v4/tests/test_v4.py`.

- `issue:v4-application-task-label-and-provenance`
  - Created: 2026-08-26T10:18+09:00
  - Updated: 2026-08-26T16:00+09:00
  - Status: resolved
  - Symptom: Step 5 shows the non-actionable task `입력값이 없어 확인이 필요합니다.` across policies and labels every generated confirmation task `출처: 기존 Rule 결과`, without naming the missing condition or a concrete confirmation route.
  - Cause: The eligibility helper returns the same generic reason for every unknown tri-state Rule; discovery exports reasons rather than condition and Rule identity, and V4 deduplicates candidate reasons with readiness actions before the application-plan API hardcodes one source label. For rechallenge, several alternative-route Rules therefore collapse into one generic card even though they do not all represent one required task.
  - Fix: The final V4 design no longer turns Rule operands, prior answers, generic readiness strings, mutable status checks, or a placeholder final review into separate tasks. The application plan now contains only the policy-scoped `AI가 정리한 공고 핵심정보 확인`; Rule and answer meaning stays in the top condition panel.
  - Evidence: `v4/copilot.py`, `v4/static/v4-extension.js`, `v4/tests/test_v4.py`, and `v4/VERIFICATION.md`; a live request containing noisy Rule and official-check inputs returns one task, V4 tests pass 21/21, and related shared/V4 regressions pass 76/76 under PID 26660.

- `issue:v4-preparation-evidence-and-draft-gap`
  - Created: 2026-08-26T10:42+09:00
  - Updated: 2026-08-26T16:31+09:00
  - Status: resolved
  - Symptom: Completing an official-check task records only a status and no checked value, date, or evidence. The mandatory inquiry-draft task and separate draft panel do not derive a question from unresolved conditions, so their purpose is unclear.
  - Cause: Application progress stores only policy-scoped task IDs in browser session state. The draft endpoint only wraps the user's own question in a local greeting template; stored notice retrieval and optional Luna explanation are connected solely to the separate policy chat.
  - Fix: The separate preparation-task, progress, confirmation-form, and inquiry-draft layers were removed. Each Luna-extracted notice field now has its own browser-session confirmation toggle, while fields absent from the stored notice remain explicit direct-confirmation items. The institution-inquiry UI, local/Luna draft code, and both application-plan and draft APIs were removed rather than preserved behind unusable preconditions.
  - Evidence: `v4/copilot.py`, `v4/main.py`, `v4/static/v4-extension.js`, `v4/static/index.html`, `v4/tests/test_v4.py`, and `v4/VERIFICATION.md`; removed APIs return 404 and related shared/V4 regressions pass 71/71.

- `issue:v4-selected-policy-full-notice-extraction`
  - Created: 2026-08-26T11:31+09:00
  - Updated: 2026-08-26T16:31+09:00
  - Status: resolved
  - Symptom: Step 5 initially showed raw stored-notice excerpts or analyzed only the currently opened policy, forcing the user to interpret long notice tables and leaving the other two selected graph policies unanalyzed.
  - Cause: The first V4 extraction path was keyed to `currentPolicy` and made one request. Strict output validation also discarded an entire policy when one field exceeded the evidence limit or normalized OCR whitespace.
  - Fix: Entering step 5 submits every selected policy, up to three, as separate full-notice extraction requests. The source remains the existing `rag/index/policy_re8.sqlite3` `policy_chunks` table. The server validates chunk identity, quote support, and numbers internally and fails closed per field, while the user-facing cards show only extracted fields. Completed results are persisted in `v4/runtime/notice_extraction_cache.sqlite` under policy ID, version, complete-notice digest, model, and schema version, so unchanged notices do not call Luna again after a server restart. Changed notice content or explicit `공고 다시 분석` invalidates or bypasses the cache.
  - Evidence: `v4/copilot.py`, `v4/static/v4-extension.js`, `v4/tests/test_v4.py`, and `v4/VERIFICATION.md`; persistent-cache restart and force-refresh regression passes, live cache contains one row for one policy, and related shared/V4 tests pass 71/71.

- `proposal:v4-policy-change-action-twin`
  - Created: 2026-08-24T14:33+09:00
  - Updated: 2026-08-24T16:18+09:00
  - Status: active
  - Content: Competition-first V4 remains a policy-change-responsive action twin. The user approved page 1 as the preserved area/industry selector plus separate worry buttons, explicitly excluding natural-language entry and keeping presentation presets as independent prefilled demo data. Page 2 uses recent-sales, cash/essential-cost, and loan cards; no-loan branching, visible timing assumptions, field-level messages, and a pre-diagnosis input ledger are included. The finance-sentence paste and structured-input feature was removed after user screen review and is not deferred automatically.
    Suspected mistakes never block a calculable value and show only `확인 권장`; only missing/invalid values that prevent calculation block progress. The user approved the five-stage action-first experience: page 4 compares multiple policy effects in the existing graph, and page 5 turns the selected policy's conditions, data, and documents into one guided task at a time, supports source-marked extraction and drafting, and tracks readiness without predicting approval. Automatic application, fabricated data, and unreviewed external transfer remain excluded; deterministic privacy/schema/Rule/Event/cash/ranking verification stays authoritative.
  - Evidence: `V4 구현 계획표.md` is the authoritative V4 implementation contract, `V4 사용자 경험 흐름.md` is the end-to-end journey, and the independent implementation is under `v4/`.

- `proposal:v4-step4-policy-focus-flow`
  - Created: 2026-08-25T22:32+09:00
  - Updated: 2026-08-26T16:00+09:00
  - Status: implemented
  - Content: The user approved the judge-focused product thesis `13-week cash diagnosis -> policy effect comparison -> one application action`. Step 4 contains a collapsed optional What-if, the multi-policy graph, no-action deltas, and one selected-policy summary with three metrics, one plain status, and the step-5 action. Supported selected-policy graphs are enabled automatically; the redundant manual graph enable/remove toggle is absent. Blockers, current answers, answer editing, official preparation, and policy-scoped chat are in step 5. There is no sixth page, dense ranking layer, duplicate mini graph, policy modal, action brief, or duplicate execution plan.
  - Evidence: `v4/static/index.html`, `v4/static/app.js`, `v4/static/v4-extension.js`, `v4/static/v4-extension.css`, `v4/tests/test_v4.py`, and `v4/VERIFICATION.md`; related shared/V4 regressions pass 76/76 and both JavaScript syntax checks pass.

- `decision:v4-copy-forward-implementation`
  - Created: 2026-08-24T15:35+09:00
  - Updated: 2026-08-24T15:35+09:00
  - Status: active
  - Content: V4 must not be built from an empty frontend or by editing V3 in place. At implementation start, record the current `v3/` inventory and hashes, copy the full V3 service structure into a new independent `v4/`, verify copy equality, then make V4 UI, CSS, orchestration, tests, storage keys, and runtime changes only inside `v4/`; shared-engine changes require a separate decision.
  - Evidence: User instruction on 2026-08-24; `V4 구현 계획표.md` sections 23-25 and `V4 사용자 경험 흐름.md`.

- `decision:v4-competition-mvp-implementation`
  - Created: 2026-08-24T15:48+09:00
  - Updated: 2026-08-26T16:31+09:00
  - Status: active
  - Content: The user approved the V4 competition-MVP bundle, then removed finance-sentence paste/structured input and the reviewed document-sample workflow after screen review. V4 preserves the existing transaction and optional-loan CSV diagnosis, uses five concern buttons with at most two selections, bounded orchestration rather than free agent discussion, tab-scoped sessionStorage, V3-bounded What-if, in-app notices, official links, and unchanged shared Rule/Event/cash/eligibility/ranking contracts.
    The independent five-stage `v4/` service adds the input ledger, a judge-focused step-4 comparison with one-policy focus controls and no-action deltas, then a step-5 condition-and-answer review plus field-level confirmation of Luna-structured public notice facts. For official-notice structuring, every selected policy's complete public stored-notice set, up to three policies, is read from the existing policy SQLite database and sent to Luna; no store, finance, answer, calculation, memo, or confirmation-state data is included. Six application fields are source-validated and fail closed per field. Completed public-notice extractions are the only server-persistent V4 data and are keyed by the complete-notice digest; user input and confirmation state remain browser-session-only. Step 5 has no generated task list, 1/1 progress, next-action card, or inquiry-letter feature. Presentation-only policy-change UI and duplicate action-brief/action-plan layers remain removed; reviewed sample documents, arbitrary application-document upload/OCR, user-data long-term storage, external alerts, automatic data collection, institution transfer, and automatic application remain excluded.
  - Evidence: User approval on 2026-08-24; `v4/`, `v4/tests/test_v4.py`, `v4/VERIFICATION.md`, and `V4 구현 계획표.md` section 26.

- `proposal:v5-concern-driven-review-priority`
  - Created: 2026-08-26T15:42+09:00
  - Updated: 2026-08-26T16:53+09:00
  - Status: superseded by `decision:v5-copy-forward-implementation-plan`
  - Content: Preserve V4's current concern-selection feature for now, but redesign it in V5 as one primary review lens rather than two equally weighted tags. The lens may visibly change metric emphasis, question priority, policy-card review order/default focus, explanation order, and notice-field confirmation order, but it must not alter official eligibility, policy amounts, simulated effects, or the underlying ranking score. After finance input, show an editable AI review plan that states what was detected, what will be checked first, and why. The current `policy_search_concern` signal must gain an explicit behavior or be removed, and the fixed 4+3 question batch should become one or two questions whose answers can change a route or material calculation.
  - Evidence: User decision during V4 screen review on 2026-08-26 plus the 2026-08-26 desktop walkthrough. Selecting cash shortage and loan repayment burden changed only guidance bullets and weak question-order tie-breaking; the first question still concerned company size and Step 4 still focused the first inserted candidate rather than the refinance candidate.

- `proposal:v5-bounded-ai-decision-copilot`
  - Created: 2026-08-26T16:53+09:00
  - Updated: 2026-08-26T16:53+09:00
  - Status: superseded by `decision:v5-copy-forward-implementation-plan`
  - Content: Position V5 as a bounded financial decision copilot, not a framework showcase. Keep deterministic Rule, Event, cash, eligibility, amount, effect, and ranking authority; use AI only where it reduces uncertainty through intent framing, decision-impact question planning, public-notice structuring, and fact-locked explanation. Prefer one coordinator with typed tool contracts, provenance, immutable financial outputs, fail-closed validation, retry/fallback rules, trace logs, and fixed evaluation cases. Do not make multi-agent or LangGraph a P0 requirement; introduce them only if durable asynchronous state, human approval, retries, or independently evaluated parallel roles create a measured product benefit.
  - Evidence: Current V4 code already combines LightGBM market scenarios, bounded orchestration, deterministic financial/policy engines, and Luna full-notice extraction with chunk, quote, and number validation. The competition asks for a working AI-based financial service and an explanation of AI use and role, not a particular orchestration framework.

- `decision:v5-copy-forward-implementation-plan`
  - Created: 2026-08-26T18:36+09:00
  - Updated: 2026-08-26T23:26+09:00
  - Status: implemented
  - Content: `V5 구현 계획표.md` remains the authoritative V5 contract and is implemented in the independent `v5/` service. V5 records 16/16 V4 copy hashes, uses port 8003, `/api/v5`, `v5-api-v1.0`, `buttimaiv5:session:v1`, and its own public-notice extraction cache. Its visible P0 connects one confirmed review lens to a short local review plan, shows policy candidates immediately without an upfront question gate, keeps separate review and ranking positions, and uses lens-specific selected-policy review and metric order. The current notice-field order is fixed across lenses as application period, financing terms, application path, required documents, contact, and publication date. After comparison, the selected policy's preparation screen shows every reviewed condition linked by the shared `POLICY_FIELDS` contract as direct choices and recalculates eligibility and supported conditional effects in place; reception status, remaining budget, and other user-unanswerable checks stay in a separate institution-check section. Internal design explanation cards, signal or mechanism keys, public-notice chunk counts, and notice digests are not user-facing. Six notice confirmations mean six extracted fields for one selected policy, not six policies. Completion ends only the on-screen review and routes the user to current official reception checks or back to comparison. Policy selection remains capped at three from V2 through V5, and the amount graph contains no action plus only supported selected-policy alternatives. Deterministic Rule, Event, cash, eligibility, amount, effect, and ranking authority remain unchanged; multi-agent, LangGraph, OCR, external data acquisition, automatic application, and user financial-data persistence remain excluded.
  - Evidence: `V5 구현 계획표.md`, `v5/V4_COPY_BASELINE_SHA256.md`, `v5/`, `v5/VERIFICATION.md`, and `reports/v5/evaluation/`; V5 tests pass 17/17, post-feedback V3/V4 tests pass 30/30, the review-lens Oracle passes 25/25, fixed personas pass 8/8, every candidate's preparation conditions match the shared policy contract, the in-app browser verified the direct preparation-choice flow, and V4 source hashes remain 16/16 unchanged.

- `baseline:v5-user-experience-flow`
  - Created: 2026-08-26T23:26+09:00
  - Updated: 2026-08-27T11:00+09:00
  - Status: active
  - Content: `V5 사용자 경험 흐름.md` is the implemented V5 Final UX baseline. It records the optional fictional three-scenario demo, final target copy and limits, three visible stages, suggested `unsure` lens default across five choices, current-contract input conveniences, zero upfront policy questions, three initially visible policy cards, a maximum of three selected policies, variable policy-specific preparation conditions, six notice fields for one policy, page-local five-turn policy chat, sessionStorage-only user state, deterministic financial authority, all main branches and failures, and the separation between code verification and user-owned visual approval. The five presentation input presets are preserved on the same V5 port and shown only with `/?demo=1`; they are not a separate server.
  - Evidence: `V5 사용자 경험 흐름.md` cross-checked against `v5/static/index.html`, `v5/static/app.js`, `v5/static/v5-extension.js`, `v5/orchestrator.py`, `v5/copilot.py`, `v5/README.md`, and `v5/VERIFICATION.md`; V5 18/18 and related shared regressions 83/83 pass, including static contracts for final copy, controls, the deterministic representative-demo endpoint, and the query-gated five presentation presets.

- `proposal:v6-crisis-golden-time-navigator`
  - Created: 2026-08-26T23:47+09:00
  - Updated: 2026-08-27T08:56+09:00
  - Status: superseded
  - Content: The desk-research V6 candidate would have preserved the deterministic policy Event and 13-week/6-month engine while narrowing the target to pre-delinquency businesses with existing debt and roughly 4-12 weeks of cash runway. The user chose not to implement this candidate in the current project; `decision:v5-finalization-and-project-close` replaces it.
  - Evidence: `V6 실제 수요 검증 보고서.md` preserves the candidate as future research, while the 2026-08-27 user decision and updated V5/project documents set V5 Final as the current project endpoint.

- `baseline:v6-need-validation-research`
  - Created: 2026-08-27T08:35+09:00
  - Updated: 2026-08-27T08:35+09:00
  - Status: active
  - Content: Desk research is complete for the problem, incumbent public descriptions, adjacent pivot candidates, and keep/pivot criteria. It confirms material cash/debt distress, delayed crisis decisions, fragmented application behavior, and the risk that new lending only postpones failure. Public descriptions of Small Business 365, Seoul's commercial-district service, and Cashnote cover diagnosis, policy discovery, alerts, cash records, or loan comparison, but did not establish the same individual no-action versus policy cash/debt simulation. This absence is not proof that no hidden or counselor-only equivalent exists. Actual need remains unvalidated until target users or experienced counselors demonstrate changed borrowing amount, policy choice, timing, or referral path.
  - Evidence: `V6 실제 수요 검증 보고서.md`; `V5 사용자 경험 흐름.md` lines 478-554; `프로젝트 계획서.md` lines 2413-2425; official sources linked in the report. No external file was downloaded and no service code, financial contract, server, dataset, or deployment changed.

- `decision:v5-finalization-and-project-close`
  - Created: 2026-08-27T08:44+09:00
  - Updated: 2026-08-31T20:46+09:00
  - Status: active
  - Content: The user closed the project after completing the proposal, function specification, final-service portfolio package, offline demo and Cloud billing safeguards. The existing all-service KRW 10,000 alerts-only budget is retained and the separate Cloud Run Spend Cap setup is user-confirmed complete. No implementation, document, deployment, review, portfolio or cost-control task is active; keep the project completed until the user makes a separate new work request. V5 remains the final implemented scope, ending at official-application handoff without V6, automatic application or a new service contract.
  - Evidence: User closeout and Cloud budget completion confirmations on 2026-08-31; `프로젝트 계획서.md` section 38.1; `V5 사용자 경험 흐름.md` section 18.1; current submission artifacts under `제출/`; final portfolio package under `포트폴리오/2026 금융 AI Challenge - 버팀AI/`; offline demo `데모 사이트/index.html`; public root and `/health` returned HTTP 200 with `v5-api-v1.0` at 2026-08-31T20:46+09:00. Billing-console configuration itself was not independently read by Codex.

- `baseline:v5-final-unexplored-angle-recheck`
  - Created: 2026-08-27T09:15+09:00
  - Updated: 2026-08-27T09:33+09:00
  - Status: active
  - Content: A final external recheck from previously unused angles supports the 13-week no-action versus intervention calculation as a credible distress decision aid, but weakens the case for V5 as a self-serve consumer product because financial stress, multi-step policy applications, and follow-up burdens can prevent information from becoming action. Future real-service potential is stronger as a repeated counselor/accountant/support-institution tool than as a broader V6 feature expansion; this is a research-grounded hypothesis, not Korean user or partner validation.
  - Evidence: UK Pensions Regulator rolling 13-week distress guidance; FCA Occasional Paper 61 robo-advice RCT; AEJ Economic Policy 2026 application-assistance RCT; 2026 Spanish minimum-income take-up RCT; KOSME six-step application flow; IFAC/World Bank SME advisory guidance; current Financial Consumer Protection Act registration boundary. The sourced interpretation and limits are now recorded in `V6 실제 수요 검증 보고서.md` section 9 and summarized in `프로젝트 계획서.md` section 39. No external file was downloaded and no code, financial contract, dataset, server, project scope, or closeout decision changed.

- `proposal:v5-input-burden-mitigation`
  - Created: 2026-08-27T09:33+09:00
  - Updated: 2026-08-27T10:41+09:00
  - Status: implemented
  - Content: V5 Final implements the optional 30-second fictional demo, the suggested `unsure` review-lens default, user-confirmed no-rent/no-employees/no-loan zero shortcuts, pasted 3-12-month revenue values, recent-value copy to three months, required-field progress, first-invalid-field focus, visible timing assumptions, and optional precision CSV. It never silently substitutes zero, industry averages, or AI guesses. An ultra-light aggregate-expense check, automatic finance-data import, or counselor product remains separate follow-up scope.
  - Evidence: `v5/static/index.html`, `v5/static/app.js`, `v5/static/v5-extension.js`, `v5/static/v5-extension.css`, `v5/orchestrator.py`, and `v5/tests/test_v5.py`; V5 18/18, related shared regressions 83/83, static links 7/7, syntax checks, and live representative-demo response pass.

- `baseline:competition-submission-and-hosting-readiness`
  - Created: 2026-08-27T11:39+09:00
  - Updated: 2026-08-27T14:23+09:00
  - Status: active
  - Content: The 2026-09-07 10:00 first submission requires a proposal PDF, function-specification PDF, and executable web-service URL; the URL must remain accessible from 2026-09-07 11:00 through 2026-09-11 23:59. A presentation PDF and source ZIP are required only after selection for the presentation round, by 2026-10-08 23:59. Cloud Run service `finance-ai-challenge` is deployed in `asia-northeast3` with 1 GiB, one CPU, minimum zero and maximum one instance, and the public URL is `https://finance-ai-challenge-232883421735.asia-northeast3.run.app`.
  - Evidence: Official DAKER and Cloud Run requirements checked 2026-08-27; project `max-finance-ai-challenge`; final deployment commit `cb4bc35`; Cloud Build `04206ce6-ff67-48ba-b018-91a6ad96f2c8`; revision `finance-ai-challenge-00006-9rl`; live HTTP 200 checks for root, health `v5-api-v1.0`, three catalogs, market scenario, representative demo, and `/?demo=1`.

- `issue:cloud-run-v5-runtime-packaging`
  - Created: 2026-08-27T14:23+09:00
  - Updated: 2026-08-27T14:23+09:00
  - Status: resolved
  - Symptom: Initial Cloud Run revisions could not read the OpenAI secret, later Docker builds missed ignored policy data, and deployed model or demo endpoints returned HTTP 500.
  - Cause: The revision service account lacked secret accessor permission; required CSV and Parquet runtime assets were excluded by global Git ignore rules; the slim Linux image lacked LightGBM's `libgomp.so.1` dependency.
  - Fix: Grant `roles/secretmanager.secretAccessor` on `openai-api-key`, track only the required runtime CSV and Parquet files through explicit `.gitignore` exceptions, and install Debian `libgomp1` in `Dockerfile`; no secret value was committed or logged.
  - Evidence: Cloud Run and Cloud Build logs; commits `6ad1ffb`, `24f5365`, `bc99ae5`, and `cb4bc35`; final live endpoint checks all returned HTTP 200.

- `issue:v5-comparison-policy-fallback`
  - Created: 2026-09-04T17:52+09:00
  - Updated: 2026-09-04T17:52+09:00
  - Status: resolved
  - Symptom: 2026-10-01 기준 재무 입력에서 대환 계약이 `(119, 0, equal_principal)`로 계산돼 공식 120개월 옵션 검증에 실패하고 비교 화면으로 넘어가지 못했다.
  - Cause: 비선택 매출 범위의 무대응 경로만 필요했지만 고정 만기일 `2036-08-05`를 쓰는 전체 Hero 정책 대안까지 만들었고, 개별 조건부 정책 오류가 전체 응답을 중단했다.
  - Fix: 비선택 범위는 무대응만 계산하고, V5 대환 만기는 첫 납부일부터 정확히 120회가 되도록 만들었다. 정책별 `CashflowInputError`는 해당 정책만 제외하고 무대응과 나머지 정책으로 계속 진행하며 fallback 상태를 응답에 남긴다.
  - Evidence: `src/integration/re_stage8.py`, `v5/orchestrator.py`, `v5/tests/test_v5.py`, `tests/test_re_stage8.py`; 현재 시연 기준일·강제 오류·120회 계약 회귀 3/3 및 관련 전체 54/54 테스트 통과, `git diff --check` 통과. 공개 배포와 브라우저 시각 검사는 수행하지 않았다.

## Current handoff

- First-chart recovery extension (2026-09-05): 2차 저장 사례와 3차 내장 사례 모두 하방·기준·회복 3선 그래프 및 무대응·정책 4선 그래프를 제공한다. 상단 범위 선택은 하단 정책 현금선과 13주 현금 수치를 함께 변경한다. 가상 시연 경로이며 개인화 예측이 아니다. Node 복구·전환 검사 통과, 배포와 시각 승인은 미수행.

- Recovery extension (2026-09-05T13:04+09:00): 사용자 요청으로 정책 제외 이후 저장 예시 JSON을 사용하는 2차 fallback과 네트워크·파일 장애 시 브라우저 내장 예시를 사용하는 3차 fallback을 추가했다. 전체 비교를 독립 가상 시연 화면으로 전환하며 무대응·비차입 지원·대환·신규 융자 4개 현금 선과 금액 표, 정책 탭, 입력 복귀 버튼을 제공한다. 원래 선택 정책에 대한 개인화 결과로 표시하지 않는다. API에는 20초 제한, 예시 요청에는 3초 제한을 두었고 정상 JSON·offline·손상·timeout Node 검증이 통과했다. 공개 배포와 실제 브라우저 시각 검사는 미수행이다.

- `handoff:current`
  - Updated: 2026-09-04T17:52+09:00
  - Current state: V5의 2026-10-01 대환 119개월 오류를 수정했고, 개별 조건부 정책 계산 실패 시 해당 정책만 제외한 채 무대응 기준선과 나머지 정책으로 비교 화면에 진입하는 규칙기반 fallback을 구현했다. 관련 전체 54개 테스트가 통과했다.
  - Next step: 사용자가 공개 반영을 명시적으로 승인하면 현재 변경을 Cloud Run에 배포하고 실제 1→2페이지 흐름을 확인한다.
  - Blockers: 로컬 코드는 완료됐지만 공개 Cloud Run에는 아직 배포하지 않았고 현재 로컬 V5 서버도 실행 중이지 않다.

## Session log

- `session:20260904-1742`
  - Started: 2026-09-04T17:42+09:00
  - Last activity: 2026-09-04T17:52+09:00
  - Focus: Diagnose the V5 finance-input transition failure and make the MVP comparison screen reachable through a bounded deterministic fallback.
  - Updated keys: `issue:v5-comparison-policy-fallback`, `handoff:current`
  - Summary: Reproduced the 2026-10-01 `(119, 0, equal_principal)` failure, limited non-selected market ranges to no-action calculation, made V5 refinance exactly 120 payments, and isolated policy-specific cash-flow errors so the baseline and remaining policies still return HTTP 200. Three targeted and 54 related tests passed; no deployment or visual approval was performed.

- `session:20260831-2149`
  - Started: 2026-08-31T21:49+09:00
  - Last activity: 2026-08-31T23:18+09:00
  - Focus: Check whether the 17-day solo-development challenge story already exists and separate documented facts from personal answers only the user can provide.
  - Updated keys: `handoff:current`
  - Summary: Drafted challenge and weakness-mitigation answers, then completed seven persuasion-and-communication answers. The latest copy attributes judge-facing order, virtual-case design, and first drafts to AI, while preserving the user's problem recognition, revision instructions, final wording, HWPX entry, screenshot placement, PDF conversion, and final visual review.

- `session:20260831-2019`
  - Started: 2026-08-31T20:19+09:00
  - Last activity: 2026-08-31T20:46+09:00
  - Focus: Determine whether the deployed Cloud Run service can automatically stop near a monthly KRW 10,000 charge threshold.
  - Updated keys: `decision:v5-finalization-and-project-close`, `handoff:current`
  - Summary: Reconfirmed the deployment baseline and current official Google Cloud rules, then the user retained the existing all-service KRW 10,000 alert budget and confirmed completion of the separate Cloud Run Spend Cap. Final read-only checks returned HTTP 200 for the public root and `/health`, with `v5-api-v1.0`. Closed the entire project again with no active or pending work; no code, service, data or submission artifact changed.

- `session:20260831-1712`
  - Started: 2026-08-31T17:12+09:00
  - Last activity: 2026-08-31T18:04+09:00
  - Focus: Create a self-contained GitHub-blog demo by copying the current V5 UI and replacing model, server, API, external-AI, and external-resource dependencies with one fixed offline snapshot.
  - Updated keys: `decision:offline-portfolio-demo`, `handoff:current`
  - Summary: Preserved `v5/`, created only `데모 사이트/index.html`, embedded the copied V5 UI, CSS, brand SVGs, three policy records, and precomputed downside/central/recovery results for one synthetic case. Removed runtime communication and external resources, disabled mutable assumptions, enforced CSP network blocking, and passed JavaScript, snapshot-contract, and self-contained-resource checks; browser visual approval remains user-owned because local `file://` navigation was blocked by the app browser policy.

- `session:20260831-1746`
  - Started: 2026-08-31T17:46+09:00
  - Last activity: 2026-08-31T20:20+09:00
  - Focus: Reconstruct major 버팀AI pivots, failures, scope cuts, Quantile time-series design, and policy-retrieval model evaluation from project records.
  - Updated keys: none; read-only retrospective
  - Summary: Verified the main product and implementation pivots plus the finance-engine record: no silent core amortization error was found; the largest incident was future-date refinance balance alignment that first failed closed and was later extended with execution-date remaining-principal calculation, targeted regression, 93 integrated tests, and live API checks. Also separated a V4 preset won-versus-ten-thousand-won input-conversion bug from core engine math. For generative AI, found no recorded live incident where Luna invented official terms, changed eligibility or ranking, altered finance results, or blocked the whole service. The authority split was preventive before live LLM use: deterministic Rule/Event/cash/ranking facts were locked, unsupported claims and numbers were rejected, and failures fell back locally. A synthetic notice test deliberately added unsupported contact number `1357` and correctly failed that field closed; simulated embedding outages returned BM25 results, while the recorded live Luna query passed Fact-lock. The largest concrete 17-day scope cut was the full AI application copilot: document sample/extraction/comparison, progress tasks, and inquiry-draft layers were partly built, then removed when they proved presentation-like, evidence-poor, and dependent on unapproved sensitive-document/OCR/storage/institution-transfer contracts. The finished core retained deterministic 13-week/6-month policy-effect comparison, condition review, and field-level evidence-validated public-notice extraction, ending at the official application route rather than automatic submission. The model retrospective confirmed the binary persistent-decline model could rank risk but not provide cash-flow shock magnitude, so RE5 compared six Quantile families over three continuous YoY targets and four purged expanding-window folds. XGBoost had 0.17-0.51% lower MAE, but LightGBM had lower Interval Score on all targets and about 8.4x lower fit time; its later internal Holdout was artifact-clean but undercovered at 69.39-71.03%, so it remained an aggregate scenario generator with explicit limits. The retrieval retrospective confirmed 40 cases means 32 search plus 8 safety, and hybrid-large was selected for perfect Recall@5 and Hit@5 despite hybrid-small's higher MRR; BM25 fallback and a five-second, two-attempt maximum were part of the selection. No product, calculation, deployment, or submission artifact changed.

- `session:20260831-1346`
  - Started: 2026-08-31T13:46+09:00
  - Last activity: 2026-08-31T16:32+09:00
  - Focus: Build the final-service portfolio package and close the project until a separate future work request.
  - Updated keys: `decision:portfolio-final-service-case-study`, `decision:v5-finalization-and-project-close`, `handoff:current`
  - Summary: Created and verified the external-reader portfolio package using eight images embedded in the final HWPX documents and exact copies of both final PDFs. After delivery, the user explicitly marked the project complete; no work remains active and it will resume only on a separate new request.

- `session:20260831-0942`
  - Started: 2026-08-31T09:42+09:00
  - Last activity: 2026-08-31T09:43+09:00
  - Focus: Record the user's final project closeout and explicit restart conditions.
  - Updated keys: `decision:v5-finalization-and-project-close`, `handoff:current`
  - Summary: Marked the project complete after the user confirmed that the proposal and function specification are finished. No code or submission artifact changed; future work resumes only for requested site revisions or advancement to the final round.

- `session:20260830-2204`
  - Started: 2026-08-30T22:04+09:00
  - Last activity: 2026-08-30T22:06+09:00
  - Focus: Make dark mode the V5 first-visit default while preserving explicit user theme choices.
  - Updated keys: `decision:v5-user-selectable-theme`, `handoff:current`
  - Summary: Replaced the system-color default with a synchronous dark default, removed automatic reactions to system-theme changes, aligned the initial browser theme color, bumped the theme-script cache key, and added regression assertions. JavaScript syntax, `git diff --check`, and all 18 V5 tests passed; public deployment and browser visual approval remain unchanged.

- `session:20260830-2157`
  - Started: 2026-08-30T21:57+09:00
  - Last activity: 2026-08-30T21:57+09:00
  - Focus: Explain how to keep the deployed Cloud Run service at one warm 1-vCPU instance without changing external deployment settings.
  - Updated keys: none
  - Summary: Confirmed the recorded deployment baseline of 1 vCPU, 1 GiB, minimum zero and maximum one; recommended service-level minimum one with request-based billing for cold-start reduction, and distinguished it from instance-based billing required for CPU execution outside requests. No Cloud Run setting, code, data, or document was changed.

- `session:20260830-1114`
  - Started: 2026-08-30T11:14+09:00
  - Last activity: 2026-08-30T21:04+09:00
  - Focus: Revise the local V5 service and synchronize only the resulting submission-document wording while preserving rollback and user-owned visual boundaries.
  - Updated keys: `decision:v5-user-selectable-theme`, `decision:v5-dark-surface-contrast`, `decision:v5-policy-bulk-selection`, `decision:v5-demo-mode-launcher`, `decision:v5-finance-form-clarity`, `decision:v5-market-scenario-copy`, `decision:v5-diagnosis-information-clarity`, `decision:v5-submission-doc-ui-sync`, `decision:v5-official-notice-positive-handoff-copy`, `issue:v5-preparation-answer-scroll-jump`, `issue:v5-input-ledger-scroll-jump`, `handoff:current`
  - Summary: Revised the V5 brand, theme, presentation presets, finance form, ledger, scenario explanation, diagnosis and preparation copy, then synchronized the current Markdown drafts. Preparation extraction gaps hand off directly to official notices, AI chat is explicit, preparation-condition recalculation preserves scroll, dark-mode semantic surfaces are clearer, and the three visible policy candidates can now be selected together without exposing the larger internal candidate count. The function specification reflects bulk selection, scroll-preserving answers, AI chat naming and updated capture guidance. It keeps the normal URL in the general user flow while adding the full `/?demo=1` URL and synthetic-input verification. Figure 1 now has a concise representative-case explanation and caption. What-if was de-emphasized and the generic selection paragraph removed. The pipeline block was judged sufficient, but its image label still needs term alignment. The model section now defines P10/P50/P90 and discloses four chronological expanding-window Folds, one-quarter exclusion, model comparison, the fixed 2025Q2 internal time Holdout and lack of a later independent future-period audit. The data section links the nine official Seoul datasets and states the 2021Q1~2025Q4 period. The proposal needed no change. Calculations, APIs, HWPX, PDF and public deployment remain unchanged.

- `session:20260830-0031`
  - Started: 2026-08-30T00:31+09:00
  - Last activity: 2026-08-30T10:40+09:00
  - Focus: Judge- and AI-screening review of whether the two current Markdown submission drafts make the service differentiation immediately visible.
  - Updated keys: `decision:submission-differentiation-frontload`, `handoff:current`
  - Summary: Reviewed only the two current Markdown drafts and the named competitors' current official public descriptions, then front-loaded the approved no-policy-versus-policy financial-outcome definition in both drafts and added a compact three-row comparison table to proposal section 4. Humanizer and whitespace checks passed; no HWPX, PDF, service or calculation file changed.

- `session:20260829-1744`
  - Started: 2026-08-29T17:44+09:00
  - Last activity: 2026-08-29T21:53+09:00
  - Focus: Clarify the proposal's policy-fund wording, prepare Figure 2, align the document structure, and review the user's first proposal PDF.
  - Updated keys: `handoff:current`
  - Summary: Clarified and revised policy-fund wording and created a pixel-preserving Figure 2 composite with labeled panels and preserved sources. Four tables were temporarily converted to prose for one HWP layout, then restored verbatim when the user changed templates. The proposal role table was retained while its redundant Figure 3 pipeline-like diagram block was removed in favor of the completed function-specification pipeline; source assets remain preserved. Proposal section 7 was retitled around MVP scope and future enhancement without changing its evidence boundary. Corrected the initial false screenshot critique after code review. The subsequent six-page PDF review confirmed all seven sections and 12 embedded links, but found a `거치기간` wording regression, one missing no-invention sentence, reduced dataset-link traceability, unresolved Figure 2 cross-policy continuity, and several mandatory page-break/orphan fixes. No HWP or PDF was modified.

- `session:20260829-1120`
  - Started: 2026-08-29T11:20+09:00
  - Last activity: 2026-08-29T17:11+09:00
  - Focus: Finalize the second-pass submission copy, establish Figure 6 boundaries, produce reference-only ImageGen drafts, prepare Canva-ready pipeline icons, and review the user's completed Figure 6 replacement.
  - Updated keys: `handoff:current`
  - Summary: Finalized the approved 08 and 09 copy, replaced Figure 6 edit instructions with final boundary prose, generated a concise icon-led pipeline and reusable icon assets, reviewed the user's completed Canva reconstruction, and updated the Figure 6 target, caption and two adjacent AI-boundary paragraphs after approval. The processing table, service, calculation, HWPX and PDF remain unchanged.

- `session:20260828-1731`
  - Started: 2026-08-28T17:31+09:00
  - Last activity: 2026-08-28T22:09+09:00
  - Focus: Complete the proposal first-pass revision and begin the function-specification first-pass revision under a consistent judge-readability standard.
  - Updated keys: `convention:judge-readable-submission-prose`, `handoff:current`
  - Summary: Completed the proposal first-pass revision and function-specification sections 1 through 5. Section 5 was reduced to the official judge-facing URL reproduction needs while preserving the representative inputs and exact expected results; its full-flow check was reduced from seven steps to four and its limitations from eleven items to six. Figure 6 remains deferred to tomorrow, and no service, calculation, official HWPX or PDF change was made.

- `session:20260828-1126`
  - Started: 2026-08-28T11:26+09:00
  - Last activity: 2026-08-28T16:36+09:00
  - Focus: Simplify proposal language, separate problem background from service differentiation, and refresh competitor evidence from official public sources.
  - Updated keys: `convention:judge-readable-submission-prose`, `handoff:current`
  - Summary: User-approved edits clarified and template-aligned the proposal and function specification. Proposal section 5 now explains its three data classes, collection methods, all nine Seoul sources, notice-to-schedule conversion, LightGBM training unit and two sales-change dependent variables. It also makes explicit that the three outputs are numeric rates used as inputs to cash-flow calculations, while the deterministic financial engine—not the model—calculates weekly balances. The model/AI role table, privacy boundary and Figure 3 were simplified and synchronized, and the revised figure PNG was rendered and visually checked. No service, calculation or official HWPX change was made.

- `session:20260828-1032`
  - Started: 2026-08-28T10:32+09:00
  - Last activity: 2026-08-28T11:11+09:00
  - Focus: Merge proposal, function-specification and screenshot-placement drafts into the next document versions and define the pipeline content without treating its visual design as final.
  - Updated keys: `convention:user-owned-submission-document-editing`, `handoff:current`
  - Summary: Created `제출/06_공모전_기획서_원고_및_시각자료_통합초안.md` and `제출/07_기능명세서_원고_및_시각자료_통합초안.md`, embedding all planned screenshot directions in their owning official document. Added high-level and detailed SVG/PNG pipeline wireframes plus explicit must-keep content for inputs, local processing, optional external AI, verification, outputs, storage, transmission and deterministic financial authority. Rechecked the public root, health and representative demo on 2026-08-28, validated SVG XML and PNG rendering, and preserved both official HWPX files; automated regression suites were not rerun and pipeline aesthetics remain user-owned.

- `session:20260828-0948`
  - Started: 2026-08-28T09:48+09:00
  - Last activity: 2026-08-28T10:06+09:00
  - Focus: Draft all five official function-specification fields as judge-facing submission copy without internal version or development-history language.
  - Updated keys: `handoff:current`
  - Summary: Created `제출/04_기능명세서_항목별_원고_초안.md` and `제출/05_기능명세서_사진_삽입_가이드.md`. The official copy covers five required fields and ten functions, while the guide specifies six exact visuals with insertion points, capture states, crops, captions, filenames, a pipeline layout and PDF checks. Rechecked the public root, health and representative demo on 2026-08-28; static checks found no prohibited version, internal endpoint, local-address or development-history wording in the official copy. No service, deployment, official HWPX or PDF changed.

- `session:20260827-2353`
  - Started: 2026-08-27T23:50+09:00
  - Last activity: 2026-08-27T23:53+09:00
  - Focus: Explain the proposal's numeric source markers and restore the planned screenshot, placement and caption handoff.
  - Updated keys: `convention:user-owned-submission-document-editing`, `handoff:current`
  - Summary: Replaced all `[1]` through `[5]` body markers with named inline official links and created `제출/04_공모전_기획서_사진_삽입_가이드.md`. The guide covers the representative comparison, three-panel diagnosis-to-preparation flow and AI-versus-deterministic authority diagram using only synthetic inputs. Static checks found no unexplained numeric markers or internal version and development language in the official copy; no screenshot, HWPX or PDF was produced.

- `session:20260827-2347`
  - Started: 2026-08-27T23:47+09:00
  - Last activity: 2026-08-27T23:47+09:00
  - Focus: Draft all seven official proposal fields as judge-facing submission copy while removing version labels and internal work history.
  - Updated keys: `convention:user-owned-submission-document-editing`, `handoff:current`
  - Summary: Created `제출/03_공모전_기획서_항목별_원고_초안.md` with the service name, summary, problem, differentiation, data and AI roles, expected effects, safety and verification limits, plus five public sources. Rechecked the 2026 MSS survey scope and statistics on the official page. The draft contains no version, Stage, Gate, copy-forward or development-history language; no service, deployment, HWPX or PDF changed.

- `session:20260827-1458`
  - Started: 2026-08-27T14:58+09:00
  - Last activity: 2026-08-27T15:52+09:00
  - Focus: Confirm the first-round document requirements and prepare separate execution plans for drafting the official proposal and function-specification templates in later sessions.
  - Updated keys: `convention:user-owned-submission-document-editing`, `handoff:current`
  - Summary: Read both HWPX templates without modifying them, mapped all 7 proposal and 5 function-specification fields to V5 sources, and created two standalone plans under `제출/`. Later clarified both plans with the screenshot ownership split: Codex supplies shot lists, states, crops and captions; the user captures synthetic deployed screens, inserts them into HWPX, adjusts layout, converts to PDF, and owns final visual approval. No service, deployment, HWPX, or PDF was changed.

- `session:20260827-1136`
  - Started: 2026-08-27T11:36+09:00
  - Last activity: 2026-08-27T14:23+09:00
  - Focus: Confirm the competition submission package, prepare V5 for Cloud Run, deploy it, and verify the public service.
  - Updated keys: `decision:v5-finalization-and-project-close`, `baseline:competition-submission-and-hosting-readiness`, `issue:cloud-run-v5-runtime-packaging`, `handoff:current`
  - Summary: Verified that the first deadline requires two PDFs and a live URL, then deployed V5 to Cloud Run in project `max-finance-ai-challenge`. Corrected the V5 entry point and container path, secret-access permission, ignored runtime CSV and Parquet assets, and missing LightGBM `libgomp1`; final commit `cb4bc35` and revision `finance-ai-challenge-00006-9rl` serve 100 percent of traffic. The public root, health, catalogs, market scenario, representative demo, and demo route all return HTTP 200; no report or presentation artifact was drafted.

- `session:20260827-0948`
  - Started: 2026-08-27T09:48+09:00
  - Last activity: 2026-08-27T11:29+09:00
  - Focus: Complete and verify the V5 Final closeout, assess its competition narrative, and document why the service intentionally hands off to official application instead of adding automatic submission.
  - Updated keys: `decision:v5-finalization-and-project-close`, `proposal:v5-input-burden-mitigation`, `baseline:v5-user-experience-flow`, `handoff:current`
  - Summary: Implemented the final positioning, deterministic fictional demo, input conveniences, limits, and semantic number emphasis; confirmed the five presentation presets remain at `/?demo=1`; and reran V5 and JavaScript checks successfully. After the user review, withdrew the optional summary-artifact suggestion and documented the approved official-application handoff rationale in three current project reports. Deployment is deferred by the user, and no V6, external data, model, service feature, automatic application, or institutional transmission was added.

- `session:20260827-0926`
  - Started: 2026-08-27T09:26+09:00
  - Last activity: 2026-08-27T09:44+09:00
  - Focus: Record the final external recheck, define the optional representative demo, and classify input-friction edits between V5 Final and future-version scope.
  - Updated keys: `decision:v5-finalization-and-project-close`, `baseline:v5-final-unexplored-angle-recheck`, `proposal:v5-input-burden-mitigation`, `handoff:current`
  - Summary: Added the new research axes, sources, and limits to the authoritative report and synchronized the plan and UX documents. Defined the representative demo as an optional 30-second fictional case whose no-action, non-debt, and policy-loan results come from the V5 engine rather than hardcoded or personal estimates. Classified all current-contract-preserving input-friction edits as V5 Final, listed their actual implementation state, and kept ultra-light aggregate-input diagnosis, automatic imports, counselor products, and V6 outside the closeout. No service code, tests, server, finance authority, dataset, or visual acceptance changed.

- `session:20260827-0911`
  - Started: 2026-08-27T09:11+09:00
  - Last activity: 2026-08-27T09:15+09:00
  - Focus: Recheck the V5 Final decision through external research angles not used in the earlier demand and competitor review.
  - Updated keys: `baseline:v5-final-unexplored-angle-recheck`, `handoff:current`
  - Summary: Reviewed behavioral decision evidence, administrative take-up experiments, 13-week distress cash-flow practice, SME adviser channels, the current Korean policy-fund application flow, and financial-product intermediation boundaries. The evidence supports V5's deterministic no-action comparison but not its direct-to-consumer demand or policy-success claims, so the approved V5 Final closeout remains correct and any future growth should first test a counselor-embedded decision aid rather than add V6 features. No code, tests, external acquisition, deployment, financial contract, server, dataset, or closeout scope changed.

- `session:20260826-2342`
  - Started: 2026-08-26T23:42+09:00
  - Last activity: 2026-08-27T08:56+09:00
  - Focus: Reassess whether V5 solves a real user need, compare current public services and financial distress evidence, then convert the result into an honest student-project finalization decision without changing implementation.
  - Updated keys: `proposal:v6-crisis-golden-time-navigator`, `baseline:v6-need-validation-research`, `decision:v5-finalization-and-project-close`, `handoff:current`
  - Summary: Completed the desk research, integrated its evidence and limits, and received user approval to finish the current project as `V5 Final` instead of implementing V6 or switching topics. Updated `프로젝트 계획서.md`, `V5 구현 계획표.md`, `V5 사용자 경험 흐름.md`, and `V6 실제 수요 검증 보고서.md` so they consistently define the bounded closeout and preserve the absence of real-user demand evidence. The former V6 candidate is now a superseded future-research option. No code, tests, external file acquisition, deployment, financial contract, server, or dataset changed.

- `session:20260826-1902`
  - Started: 2026-08-26T19:02+09:00
  - Last activity: 2026-08-26T23:26+09:00
  - Focus: Implement and refine the approved V5 copy-forward contract, then document the actual V5 user journey as the baseline for V6 comparison while preserving V4 and deterministic financial authority.
  - Updated keys: `decision:v5-copy-forward-implementation-plan`, `baseline:v5-user-experience-flow`, `handoff:current`
  - Summary: Copied and hashed the 16 approved V4 files into independent V5, implemented the three-stage user shell, single review lens, local review plan, review-versus-ranking separation, metric prioritization, one-next-confirmation UI, strict traces and authority hashes, and fixed review/persona evaluations. User screen feedback replaced internal identifiers with Korean meaning, added notice loading feedback, hid chunk/digest metadata, distinguished six notice fields from selected policies, and added post-confirmation official-check and comparison-return actions. The follow-up removed the internal order/criteria cards and the at-most-two upfront question gate, then moved all selected-policy conditions into direct preparation-screen choices with in-place recalculation and separate institution checks. `V5 사용자 경험 흐름.md` now documents the actual entry, diagnosis, comparison, preparation, loading, failure, persistence, and completion paths; V4 carryovers and V5 changes; current UX burdens; representative comparison scenarios; and a fill-in V6 measurement table. The code check also corrected an earlier assumption: notice-field order is currently fixed across lenses. V5 17/17 and V3/V4 30/30 tests remain the latest code results; this documentation-only update did not rerun tests or change service code. External AI, external data, deployment, final visual acceptance, mobile acceptance, and presentation rehearsal were not performed.

- `session:20260826-1826`
  - Started: 2026-08-26T18:26+09:00
  - Last activity: 2026-08-26T18:36+09:00
  - Focus: Write the complete V5 implementation contract for a fresh-session copy-forward build that preserves V4 and CSS continuity.
  - Updated keys: `proposal:v5-concern-driven-review-priority`, `proposal:v5-bounded-ai-decision-copilot`, `decision:v5-copy-forward-implementation-plan`, `handoff:current`
  - Summary: Created the 1,671-line `V5 구현 계획표.md` with a V4-source copy manifest, runtime and cache separation, one-lens UX, decision-impact questioning, review-versus-ranking invariants, one-next-confirmation flow, harness contracts, Stage V5-0 through V5-7 Gates, fixed evaluation sets, and a ready-to-paste new-session prompt. Static completeness and whitespace checks passed; implementation, tests, servers, external AI, and external data were not run.

- `session:20260826-1640`
  - Started: 2026-08-26T16:40+09:00
  - Last activity: 2026-08-26T16:53+09:00
  - Focus: Audit V4 for a bold V5 direction that makes AI materially visible without sacrificing the financial-service user experience.
  - Updated keys: `proposal:v5-concern-driven-review-priority`, `proposal:v5-bounded-ai-decision-copilot`, `handoff:current`
  - Summary: Compared current code, implementation documents, competition framing, and a live desktop walkthrough. Concluded that V4 already has substantive bounded AI but lacks a visible causal chain from the first concern choice to question planning, comparison focus, and preparation. Proposed a V5 P0 centered on one primary review lens, one or two decision-impact questions, concern-aware default focus, one evidence-backed next confirmation, and measurable harness evaluations; no code or service contract changed.

- `session:20260826-1002`
  - Started: 2026-08-26T10:02+09:00
  - Last activity: 2026-08-26T16:31+09:00
  - Focus: Restart V4, implement selected-policy full-notice Luna extraction, then simplify and persist the step-5 notice review through user-led screen feedback.
  - Updated keys: `issue:v4-application-task-label-and-provenance`, `issue:v4-preparation-evidence-and-draft-gap`, `issue:v4-selected-policy-full-notice-extraction`, `decision:v4-competition-mvp-implementation`, `proposal:v5-concern-driven-review-priority`, `handoff:current`
  - Summary: Kept the existing SQLite notice source and strict server-side evidence checks, added a content-addressed persistent cache for completed Luna extraction results, and replaced the single task/progress form with independent extracted-field confirmations. Removed the inquiry-letter feature and its plan/draft APIs entirely. V4 16/16 and related shared/V4 71/71 pass; disk-cache reuse was verified after restart and PID 3880 is live, while browser and visual acceptance remain user-owned.

- `session:20260825-2313`
  - Started: 2026-08-25T23:13+09:00
  - Last activity: 2026-08-25T23:18+09:00
  - Focus: Re-establish the V4 screen-review handoff from current documents, code, dirty-worktree state, and live server without changing implementation.
  - Updated keys: `handoff:current`
  - Summary: Confirmed the step-4 comparison and step-5 preparation code paths, deterministic policy boundary, document-upload exclusion, V3 10/10 source hashes, live PID 1904 ownership of port 8002, and HTTP 200 health/root markers. No service code, calculation, API contract, V4 plan, or verification result changed; the next input is the user's screen-specific feedback.

- `session:20260825-2224`
  - Started: 2026-08-25T22:24+09:00
  - Last activity: 2026-08-25T23:01+09:00
  - Focus: Diagnose policy-curve scale compression, approve the judge-facing flow, and implement the simplified comparison-to-preparation experience.
  - Updated keys: `issue:v4-policy-effect-scale-compression`, `proposal:v4-step4-policy-focus-flow`, `decision:v4-competition-mvp-implementation`, `handoff:current`
  - Summary: Implemented the approved simplification: step 4 now shows optional What-if, selected-policy cash curves, no-action deltas, and one concise policy summary; step 5 owns blockers, editable answers, preparation, draft, and scoped chat. Removed redundant cards, tables, mini charts, modal, action layers, stacked launcher, and presentation-only change sample. Focused tests passed 67/67, live HTTP is healthy, and PID 1904 serves the updated V4.

- `session:20260824-1542`
  - Started: 2026-08-24T15:42+09:00
  - Last activity: 2026-08-24T19:15+09:00
  - Focus: Implement and screen-review the independent five-stage V4 MVP, then fix selected-policy graph coverage and the step-4 to step-5 application route.
  - Updated keys: `decision:v4-competition-mvp-implementation`, `issue:v4-conditional-policy-graph-coverage`, `handoff:current`
  - Summary: After diagnosing the five-preset graph gap, implemented the user-approved correction: stability voucher uses a reviewed eligible-cost offset, refinance uses its four-week execution-date remaining balance, and structural ineligibility stays ungraphed with exact reasons and editable answers. Reordered step 4 from graph to conditions to step 5, added direct preparation actions, passed 93 regressions and JavaScript syntax, and verified all three conditional policies together on the refreshed live server.

- `session:20260824-1433`
  - Started: 2026-08-24T14:33+09:00
  - Last activity: 2026-08-24T15:39+09:00
  - Focus: Finalize the V4 roadmap, five-stage action-first application copilot, full user journey, copy-forward implementation boundary, and presentation infographic.
  - Updated keys: `proposal:v4-policy-change-action-twin`, `decision:v4-copy-forward-implementation`, `handoff:current`
  - Summary: Renamed the authoritative V4 source to `V4 구현 계획표.md`, confirmed five screens and the application-copilot P0, added eight implementation stages and Gates, created the full journey document, and generated `V4 사용자 경험 흐름.png` as a Korean presentation infographic. Future implementation must copy `v3/` to an independent `v4/`; no code folder, service, data, server, browser, or deployment changed.

- `session:20260824-1419`
  - Started: 2026-08-24T14:19+09:00
  - Last activity: 2026-08-24T14:27+09:00
  - Focus: Replace the outdated V3 proposal with a complete current-state user experience document that can serve as the V4 design baseline.
  - Updated keys: `proposal:v3-bounded-agentic-orchestrator`, `handoff:current`
  - Summary: Rewrote `V3 사용자 경험 구성안.md` into 18 implementation-based sections covering the full four-stage V3 flow, AI and deterministic boundaries, question batching, What-if scope and retry guard, safeguards, file routing, 14 regression contracts, current limits, V4 experience directions, screen review points, and approval decisions. Only documentation and required project records changed; no service code, browser interaction, image analysis, external call, or deployment occurred.

- `session:20260824-1411`
  - Started: 2026-08-24T14:11+09:00
  - Last activity: 2026-08-24T14:16+09:00
  - Focus: Finish V3 with sequential policy questions, batched recalculation, and a bounded What-if clarification flow that cannot repeat answers.
  - Updated keys: `proposal:v3-bounded-agentic-orchestrator`, `handoff:current`
  - Summary: Kept policy questions one at a time while limiting server recalculation to two batches, exposed supported What-if conditions and editable examples, blocked cost increases locally before Luna, and limited ambiguous input to one clarification based on the original prompt. Fourteen tests, JavaScript syntax, whitespace, and live health passed; the server runs on port 8001, and no browser manipulation or image analysis was performed.

- `session:20260823-1639`
  - Started: 2026-08-23T16:39+09:00
  - Last activity: 2026-08-23T17:01+09:00
  - Focus: Establish the V3 user-review boundary and turn the disconnected situation-text helper into a confirmed downstream input and orchestration path.
  - Updated keys: `proposal:v3-bounded-agentic-orchestrator`, `convention:user-owned-screen-validation`, `handoff:current`
  - Summary: Replaced the vague candidate button with five editable examples and a structured confirmation/apply flow. Confirmed exact area, industry, and goal fill their existing controls; concern signals reach finance guidance, adaptive question selection, action plans, and What-if recalculation without changing deterministic money, eligibility, effect, or ranking rules. Ten tests, JavaScript syntax, whitespace, V2 hashes, live API, and DOM flow passed; Luna and image analysis were not used, and the updated V3 server runs on port 8001.

- `session:20260823-1626`
  - Started: 2026-08-23T16:26+09:00
  - Last activity: 2026-08-23T16:32+09:00
  - Focus: Reproduce and fix the V3 page-3 to page-4 HTTP 400 failure after policy selection.
  - Updated keys: `issue:v3-page4-refinance-preview-alignment`, `handoff:current`
  - Summary: Reused the user's live page state to identify the selected voucher, rechallenge, and refinance policies, reproduced the exact `REFINANCE_BASELINE_ALIGNMENT_REQUIRED` exception, and fixed it inside V3 without changing the shared V2 engine. The same live state then reached page 4 with the valid rechallenge graph and a clear refinance non-calculation reason; eight tests, JavaScript syntax, and whitespace passed, and the updated server is running on port 8001.

- `session:20260823-1205`
  - Started: 2026-08-23T12:05+09:00
  - Last activity: 2026-08-23T16:17+09:00
  - Focus: Define, document, implement, and verify the independent V3 bounded-agent service while preserving V2.
  - Updated keys: `proposal:v3-bounded-agentic-orchestrator`, `handoff:current`
  - Summary: After the user rejected the visually independent first V3 shell, copied the three actual V2 static files into `v3/static` with matching hashes and rebuilt V3 only as extensions over that copy. The current build preserves the V2 four-step layout and hierarchical circle map, removes automatic first-two policy selection, adds answer-adaptive next-question orchestration, an optional bounded situation interpreter, deterministic action plan, and engine-backed What-if. Seven focused tests and JavaScript syntax passed; browser QA confirmed the V2 district-circle map and a real adaptive question transition. V2 source hashes stayed unchanged, with no deployment or external data acquisition.

- `session:20260822-2312`
  - Started: 2026-08-22T23:12+09:00
  - Last activity: 2026-08-23T11:55+09:00
  - Focus: Implement V2-009/V2-010/V2-011, restore the local server, and establish the current V2 UX and full code/data/AI traceability baseline for contest and AI-strength comparison.
  - Updated keys: `issue:v2-selected-policy-impact-and-readiness-gap`, `issue:v2-stale-server-request-schema`, `issue:v2-page4-policy-explanation-and-graph-scope`, `decision:v2-user-experience-traceability-baseline`, `handoff:current`
  - Summary: V2-009 through V2-011 remain implemented and verified. V2-012 audited the active plan against current DOM, JavaScript, FastAPI, integration, model, retrieval, rule, cash, Event, recommendation, and test files, then documented the visible and internal flows, policy depth counts, state transitions, AI boundaries, contest-comparison baseline, and limitations. It corrected the stale policy-first summary and records that questions are candidate-specific but not answer-adaptive, the first two policies are auto-selected, and the current local runtime uses LightGBM plus BM25/local fallbacks. No service code, calculation, policy, model, data, screen, deployment, or image processing changed.

- `session:20260821-1356`
  - Started: 2026-08-21T13:56+09:00
  - Last activity: 2026-08-21T15:01+09:00
  - Focus: Permanently close stale RE8.3 records, establish the V2-only review boundary, replace the policy-first V2 flow with a connected single-question wizard, and decide how to remove pre-known intervention inputs from the core experience.
  - Updated keys: `decision:implementation-checklist`, `decision:re-stage8-3-user-review-cycle`, `decision:v2-question-first-wizard`, `experiment:v2-optional-scenario-inputs`, `convention:user-owned-screen-validation`, `handoff:current`
  - Summary: Closed every authoritative RE8.3 status and Gate and made the V2 ledger exclusive. V2-007 introduced the connected one-question flow. V2-008 is now an evaluation build: intervention inputs are optional, the existing safe-cash gap and official policy bounds appear by default, and unquantified policies remain actionable but outside numeric rank. Existing Event payloads remain available behind explicit detailed calculation. Focused tests 55/55, JavaScript syntax, and whitespace passed; the user owns visual and final product judgment.

- `session:20260821-1346`
  - Started: 2026-08-21T13:46+09:00
  - Last activity: 2026-08-21T13:53+09:00
  - Focus: Expand the V2 plan into a concrete user-service journey that another page-revision session can use directly.
  - Updated keys: `handoff:current`
  - Summary: Replaced the short nine-step outline with a detailed four-screen UX contract covering first-contact messaging, manual and five-preset entry, all revenue/cash/four-cost/loan inputs, loading and error behavior, store-versus-market signals, simultaneous policy discovery, selected-policy adaptive questions, confirmed scenarios, deterministic comparison, optional fact-locked LLM wording, chat boundaries, and branch-state handling. No service code, calculation, model, policy data, deployment, or RE9 artifact changed.

- `session:20260821-1326`
  - Started: 2026-08-21T13:26+09:00
  - Last activity: 2026-08-21T13:57+09:00
  - Focus: Re-establish the V2 user-directed local review baseline, separate V2 revisions from MVP history, and implement user annotations under the V2 ledger.
  - Updated keys: `handoff:current`
  - Summary: Implemented V2-001 through V2-005 and closed V2 page 1 after the user's direct confirmation. The separate V2 ledger records the completed internal-role removal, five-area presets, `버팀AI` naming, header-note removal, and full Hero name; the next review item is V2-006. No image analysis, external API call, deployment, or RE9 work occurred.

- `session:20260821-1136`
  - Started: 2026-08-21T11:36+09:00
  - Last activity: 2026-08-21T12:29+09:00
  - Focus: Judge RE8.3, choose refactor over restart, specify the bounded-AI user journey, and implement the approved V2 while preserving reusable MVP assets.
  - Updated keys: `decision:v2-bounded-ai-copilot`, `issue:re8-fixed-policy-candidate-routing`, `handoff:current`
  - Summary: Created a separate active V2 plan and implemented a trust-first landing, other fixed cost, separated store versus market signals, three-policy selection, adaptive questions, explicit cost and reviewed policy scenarios, V2-only confirmed-alternative comparison, and consent-gated fact-locked action brief. Preserved map selection, five presets, both interactive charts, loading timer, CSV, four-step shell, and legacy RE7 Hero path. RE9-excluded full tests passed 152/152, JavaScript syntax and whitespace passed, and live health reported `v2-api-v1.0`; in-app browser screenshot/mobile QA remains pending due plugin trust-path initialization failure. No external data, deployment, RE9, or live LLM call occurred.

- `session:20260821-0729`
  - Started: 2026-08-21T07:29+09:00
  - Last activity: 2026-08-21T11:28+09:00
  - Focus: Prepare RE8.3 review, record the image-analysis convention, and implement the user-annotated step-3 and step-4 revisions.
  - Updated keys: `decision:conditional-policy-ui-placement`, `decision:financial-policy-service-scope`, `decision:goal-ranking-precompute`, `decision:policy-discovery-goal-independence`, `decision:policy-chat-actionable-plain-text`, `decision:market-scenario-cross-step-continuity`, `decision:cash-threshold-user-language`, `decision:policy-card-content-hierarchy`, `decision:comparison-loading-feedback`, `handoff:current`, `convention:image-analysis-contact-sheets`
  - Summary: Finally closed by user request after RE8.3-001 through RE8.3-010. The final change adds an actual elapsed-seconds display to the accessible centered loading overlay used by the step-2 diagnosis action for both manual and preset-filled inputs; preset selection itself performs no range fetch or comparison and clears stale results. Live HTTP checks, JavaScript syntax, whitespace, and 46 focused tests passed; no external API, model, policy source, raw data, image analysis, or deployment action occurred.

- `session:20260821-0726`
  - Started: 2026-08-21T07:26+09:00
  - Last activity: 2026-08-21T07:26+09:00
  - Focus: Begin RE8.3 with a read-only repository, contract, review-ledger, environment, route, and health readiness check.
  - Updated keys: `handoff:current`
  - Summary: Confirmed all requested core artifacts exist, Gate RE8.3 remains open, no actual modification ID exists, static HTML/CSS/JS and FastAPI routes are connected, and the rebuilt `.venv` returns HTTP 200 from `/health`; no source, test, model, policy, data, RAG, deployment, screenshot, image, or external API action occurred.

- `session:20260821-0717`
  - Started: 2026-08-21T07:17+09:00
  - Last activity: 2026-08-21T07:17+09:00
  - Focus: Rebuild the local Python environment and prepare an exact fresh-session prompt for RE8.3 web-service revisions.
  - Updated keys: `handoff:current`
  - Summary: Confirmed the old project `.venv` lacked Uvicorn, removed it at the user's request, and supplied clean rebuild commands after sandboxed venv creation failed. Mapped the current frontend, FastAPI integration, cash-flow, frozen LightGBM inference, policy rules and events, recommendation, Hybrid RAG, processed data, configuration, review ledger, and focused tests for the next session; no service source or contract was changed.

- `session:20260817-2045`
  - Started: 2026-08-17T20:45+09:00
  - Last activity: 2026-08-17T23:46+09:00
  - Focus: Choose a low-usage, precise feedback channel for RE8.3 UI and server revisions.
  - Updated keys: `handoff:current`
  - Summary: Verified the current RE8.3 contract and local run route, then clarified that image analysis is unnecessary for functional and server validation but is needed if Codex must independently judge rendered layout; text-only review can keep visual acceptance with the user. No service code, checklist, review ledger, model, policy scope, or deployment state was changed.

- `session:20260817-1433`
  - Started: 2026-08-17T14:33+09:00
  - Last activity: 2026-08-17T14:33+09:00
  - Focus: Pause deployment and establish a user-directed local service review and revision stage before RE9.
  - Updated keys: `decision:implementation-checklist`, `decision:re-stage8-3-user-review-cycle`, `handoff:current`
  - Summary: Added RE Stage 8.3 and its change ledger, made explicit user recheck and revision-complete approval the Gate, paused all external deployment, restricted future hosting to a sustained free tier, and reclassified existing RE9 QA as a pre-revision baseline. No platform account, public URL, screenshot analysis, service code, model, or policy logic was changed.

- `session:20260817-1402`
  - Started: 2026-08-17T14:02+09:00
  - Last activity: 2026-08-17T14:24+09:00
  - Focus: Complete RE9 local submission preparation, including the approved partial refinance, frozen personas, retrieval QA, deployment package, and submission documents.
  - Updated keys: `decision:implementation-checklist`, `decision:re-stage9-local-submission-package`, `handoff:current`
  - Summary: Implemented the approved 50 million won partial-refinance segment while retaining 30 million won on the existing schedule; built and froze eight persona inputs, traces, hashes, and twenty retrieval cases; created a Docker contract, Runbook, QA report, presentation evidence, final proposal, and three-page functional-spec PDF. Local QA passed 8/8, 20/20, zero prohibited claims, 149 tests, PDF structure checks, JavaScript syntax, and 14/14 Manifest hashes; Docker Build and browser DOM QA remain unverified because their local tools are unavailable, and no screenshot image analysis was performed.

- `session:20260817-1318`
  - Started: 2026-08-17T13:18+09:00
  - Last activity: 2026-08-17T13:54+09:00
  - Focus: Complete the user-approved RE8.2 Hybrid policy-discovery contract and close its Gate with executable evidence.
  - Updated keys: `decision:implementation-checklist`, `decision:re-stage8-api-web-local-rag`, `decision:re-stage8-2-hybrid-policy-discovery-plan`, `issue:re8-fixed-policy-candidate-routing`, `handoff:current`
  - Summary: Activated large 3072D Hybrid with a strict two-attempt maximum and BM25 fallback, added 17-policy metadata, staged questions, ten RE6 plus seven overlay Rule paths, and reviewed Event-to-RE7 dynamic alternatives while keeping personal or closed benefits out of business cash. Froze the privacy/cost contract and 40-case oracle; Hybrid-large reached Recall@5 1.000, Hit@5 1.000, MRR 0.872, new-policy Hit@5 1.000, and safety 8/8. All 144 tests, JavaScript syntax, whitespace checks, Manifest checks, and current-code local browser rendering passed; Gate RE8.2 is complete and RE9 is next.

- `session:20260817-1152`
  - Started: 2026-08-17T11:52+09:00
  - Last activity: 2026-08-17T13:16+09:00
  - Focus: Preserve and extend RE8.2 with user-reviewed policy Markdown, whole-catalog policy chat, and an exact implemented-versus-pending handoff.
  - Updated keys: `decision:implementation-checklist`, `decision:re-stage3-input-calculation-contract`, `decision:re-stage8-api-web-local-rag`, `decision:re-stage8-2-hybrid-policy-discovery-plan`, `handoff:current`
  - Summary: Migrated obsolete PDF/HWPX provenance to reviewed Markdown, deleted one misfiled duplicate, indexed four valid new policies for a total of 17 policies and 817 chunks with both vector sets, and replaced one-shot QA with a five-turn page-memory chat that searches the whole catalog and returns distinct policy links. Added illness and childcare examples plus deterministic query expansion; live Luna returned hospital living expense first with fact-lock passed, all 135 tests and JavaScript syntax passed, and the checklist/guide/Manifest now preserve the remaining RE8.2 Gate work.

- `session:20260817-1130`
  - Started: 2026-08-17T11:30+09:00
  - Last activity: 2026-08-17T11:51+09:00
  - Focus: Verify the current retrieval architecture, plan Hybrid user-situation policy discovery, and assess whether the LightGBM, Luna, and planned OpenAI Embedding roles satisfy the Finance AI Challenge brief.
  - Updated keys: `decision:implementation-checklist`, `decision:re-stage6-eligibility-rag-safety`, `decision:re-stage8-2-hybrid-policy-discovery-plan`, `issue:re8-fixed-policy-candidate-routing`, `handoff:current`
  - Summary: Added RE8.2 before RE9 in both active plans, selected OpenAI Embeddings as the provider, and fixed a common BM25-only, Vector-only, and Hybrid Korean evaluation principle. Confirmed from the competition brief that the submission must explain its generative-AI role; current LightGBM is valid ML but fixed candidates make the present AI story incomplete, so RE8.2 must be implemented and evaluated as the material AI expansion. No API call or implementation change was made.

- `session:20260817-1122`
  - Started: 2026-08-17T11:22+09:00
  - Last activity: 2026-08-17T11:22+09:00
  - Focus: Make four-goal ranking changes visible and bind warnings and cautions to the currently selected alternative.
  - Updated keys: `decision:re-stage8-api-web-local-rag`, `handoff:current`
  - Summary: Reordered eligible alternatives from the selected goal's deterministic result, added goal-specific judgment values and explicit table ranks, and replaced the top-only yellow warning with selected-alternative rank, minimum-cash, eligibility, and confirmation guidance. Updated RE8 specifications and Manifest, passed RE7+RE8 tests 38 and JavaScript syntax, and left visual validation to the user as requested.

- `session:20260817-1104`
  - Started: 2026-08-17T10:42+09:00
  - Last activity: 2026-08-17T11:04+09:00
  - Focus: Diagnose RAG links, region sensitivity, deterministic policy curves, OpenAI usage visibility, and policy-source processing while applying the user's additional map and decision-modal corrections.
  - Updated keys: `decision:implementation-checklist`, `decision:re-stage8-api-web-local-rag`, `decision:policy-pdf-text-only`, `handoff:current`
  - Summary: Grouped identical evidence URLs by source and page, made area labels and search global, synchronized zoom-center selections, recalculated existing results after market selection changes, added backdrop modal dismissal and transparent rank/negative-cash warnings, and removed all future PDF rendering from extraction. Reproduced the high-fixed-cost case, confirmed two districts yield different LightGBM scenarios, verified the SQLite DB stores text only, found three official policy expansion candidates without downloading them, and passed 24 RE8 tests plus syntax/whitespace checks; no PDF image inspection, browser validation, external data download, or live OpenAI call occurred.

- `session:20260817-0848`
  - Started: 2026-08-17T08:48+09:00
  - Last activity: 2026-08-17T10:42+09:00
  - Focus: Implement and verify the approved RE8.1 actual-user redesign and the follow-up usability corrections using the user-provided Seoul commercial-area source.
  - Updated keys: `decision:re-stage3-input-calculation-contract`, `decision:re-stage8-api-web-local-rag`, `issue:re8-user-facing-ux`, `handoff:current`
  - Summary: Extended the four-step workspace with 25 district to administrative-dong to area circle drilldown, official-code industry grouping, ten-thousand-won inputs, UTF-8-SIG templates, clearer scenario and timing labels, five one-click presentation cases, all-alternative graph selection, and a green-button-only modal containing humanized execution details and named official links. Replaced the orange/pink map with a cobalt-and-white high-contrast palette, added permanent district/dong labels, limited dong and area layers to the current map region, swapped regions on pan, and reset to parent levels on zoom-out. Cleared a secret-shaped value from `.env.example`, passed RE8.1 tests 23 and all 126 tests, completed desktop browser checks including Yong-san to Gang-dong pan and 16-dong to 25-district zoom reset with zero console errors, and made no external AI call.

- `session:20260817-0841`
  - Started: 2026-08-17T08:41+09:00
  - Last activity: 2026-08-17T08:43+09:00
  - Focus: Audit the rejected RE8 interface from an actual-user perspective, configure the Luna model safely, and define the required RE8.1 redesign boundary before RE9.
  - Updated keys: `issue:re8-user-facing-ux`, `handoff:current`
  - Summary: Created ignored `.env` with only the Luna model name, connected safe local loading for OpenAI settings, removed unused public-data key placeholders, and passed all 16 RE8 tests without a live key. Verified no local commercial-area geometry and rejected the proposed `sig.shp` code because it joins municipality polygons to administrative-district data rather than seven-digit commercial-area codes; recommended a four-step pre-RE9 redesign that awaits material rule approval and matching user-supplied boundary data.

- `session:20260817-0740`
  - Started: 2026-08-17T07:40+09:00
  - Last activity: 2026-08-17T08:19+09:00
  - Focus: Implement and verify RE Stage 8 as a local FastAPI web/API product with local SQLite RAG and optional GPT-5.6 Luna explanations.
  - Updated keys: `decision:implementation-checklist`, `decision:re-stage3-input-calculation-contract`, `decision:re-stage8-api-web-local-rag`, `handoff:current`
  - Summary: Built the responsive eight-screen flow, 11-path API contract, approved three-schedule quick mode, detailed CSV baseline route, local 227-chunk policy index, eligibility/comparison/plan integration, and privacy-safe Luna client with deterministic fallback and Fact-lock; generated specs, manifest, verification, and 10 screenshots, passed RE8 tests 16 and all 119 tests, stored no API key, and passed Gate RE8.

- `session:20260816-2241`
  - Started: 2026-08-16T22:41+09:00
  - Last activity: 2026-08-16T23:00+09:00
  - Focus: Implement and verify RE Stage 7 against the approved contract without changing policy, model, or data scope.
  - Updated keys: `decision:implementation-checklist`, `decision:re-stage7-candidate-routing-partial-contract`, `handoff:current`
  - Summary: Built `re7-v1` candidate routing, conservative combination checks, Target A/B cash-flow scenarios, safe cash, six alternatives, four lexicographic goals, Pareto and execution plans; froze three detailed samples, passed RE7 tests 14 and all 103 tests, verified deterministic hashes, passed Gate RE7, and handed actual screen controls to RE8.

- `session:20260816-2237`
  - Started: 2026-08-16T22:37+09:00
  - Last activity: 2026-08-16T22:37+09:00
  - Focus: Finalize the three remaining RE7 decisions as documentation only and preserve an explicit no-implementation boundary.
  - Updated keys: `decision:re-stage7-candidate-routing-partial-contract`, `handoff:current`
  - Summary: Created `re7-contract-v1`, superseded the partial contract as history, and aligned the plan, redesign concept, checklist, RE6 downstream review, config, log, and handoff with confirmed-only default policy combinations, Target A/B horizon mapping at a 100% adjustable reference rate, and a 28-day required-outflow safe-cash suggestion. YAML and diff checks passed; no code, tests, simulations, model runs, or data generation occurred.

- `session:20260816-2233`
  - Started: 2026-08-16T22:33+09:00
  - Last activity: 2026-08-16T22:33+09:00
  - Focus: Explain the three remaining material RE7 choices and provide a concrete recommendation for user approval.
  - Updated keys: `handoff:current`
  - Summary: Verified the existing partial contract and RE3 safe-cash boundary, then prepared recommendations for conservative policy-pair compatibility, transparent horizon-specific scenario application with user control, and a user-data-derived four-week editable safe-cash suggestion. No decision, plan, code, model, or data was changed.

- `session:20260816-2228`
  - Started: 2026-08-16T22:28+09:00
  - Last activity: 2026-08-16T22:28+09:00
  - Focus: Apply the user-approved RE7-RE9 usability and safety amendments without starting model training or the RE7 engine.
  - Updated keys: `decision:implementation-checklist`, `decision:re-stage7-candidate-routing-partial-contract`, `handoff:current`
  - Summary: Updated the plan, redesign concept, checklist, RE6 downstream review, RE7 partial contract, and new RE7 config with the three visible policy groups, explicit conditional-simulation gate, ranking restrictions, hidden internal retrieval details, separated API status fields, deterministic explanation fallback, privacy constraints, and 20-case all-policy retrieval QA. The three material RE7 comparison rules remain pending and implementation authorization is false; no training or model execution occurred.

- `session:20260816-2224`
  - Started: 2026-08-16T22:24+09:00
  - Last activity: 2026-08-16T22:24+09:00
  - Focus: Turn the RE6 downstream findings into a concrete, user-centered RE7-RE9 plan amendment proposal.
  - Updated keys: `handoff:current`
  - Summary: Recommended a three-bucket policy flow, conditional-simulation rules, simplified screen labels, separate API eligibility/availability objects, internal-only Rule/search details, deterministic explanation fallback, session privacy, and bounded 20-case all-policy retrieval QA; no project plan or implementation files were changed pending approval.

- `session:20260816-2223`
  - Started: 2026-08-16T22:22+09:00
  - Last activity: 2026-08-16T22:23+09:00
  - Focus: Review whether actual RE6 results require downstream plan changes before RE7.
  - Updated keys: `handoff:current`
  - Summary: Found no Target, model, cash-flow, or financial-event redesign need, but recommended small RE7-RE9 contract edits for separate eligibility/availability handling, conditional-candidate gating, internal-only retrieval details, deterministic explanation fallback, privacy, and bounded broader retrieval/current-status QA before deployment; no implementation or plan file edits were made.

- `session:20260816-2221`
  - Started: 2026-08-16T21:47+09:00
  - Last activity: 2026-08-16T22:21+09:00
  - Focus: Finalize RE5 service approval and implement the complete RE6 official eligibility, retrieval, and safe-explanation layer.
  - Updated keys: `decision:implementation-checklist`, `decision:re-stage5-partial-contract`, `decision:re-stage6-eligibility-rag-safety`, `handoff:current`
  - Summary: Passed Gate RE5 with internal-only scenario labels, then completed RE6 across 56 rules, 20 reviewed examples, 227 unique official chunks, eight retrieval cases, two JSON schemas, safety guards, reports, and downstream contracts; all 89 tests passed without model training, external LLM calls, or profile persistence.

- `session:20260816-2146`
  - Started: 2026-08-16T21:42+09:00
  - Last activity: 2026-08-16T21:46+09:00
  - Focus: Separate RE5 internal model-quality diagnostics from the minimal information needed by end users.
  - Updated keys: `decision:re-stage5-partial-contract`, `handoff:current`
  - Summary: Confirmed that sub-nominal Holdout Coverage is not a downstream implementation blocker because RE5 only initializes aggregate stress scenarios, and updated the plan, differentiation design, and checklist so screens expose only `하방·기준·회복` plus cash-flow effects while all quantile and Holdout statistics remain internal QA.

- `session:20260816-2124`
  - Started: 2026-08-16T21:11+09:00
  - Last activity: 2026-08-16T21:24+09:00
  - Focus: Verify and interpret the user-completed RE5 LightGBM internal Holdout without training, reselection, or Stage 6 reactivation.
  - Updated keys: `decision:implementation-checklist`, `decision:re-stage5-partial-contract`, `handoff:current`
  - Summary: Verified all 64,356 predictions, recomputed metrics, matched seven Manifest outputs and three checkpoints/artifacts, added a compatibility loader for the immutable `__main__`-serialized preprocessor, documented 69.39-71.03% Coverage and CV degradation, and passed all 73 tests; service activation remains a required user decision.

- `session:20260816-2052`
  - Started: 2026-08-16T20:42+09:00
  - Last activity: 2026-08-16T20:52+09:00
  - Focus: Build a user-operated, LightGBM-only one-time RE5 internal holdout evaluator without fitting a model or opening targets in Codex.
  - Updated keys: `decision:implementation-checklist`, `decision:re-stage5-partial-contract`, `handoff:current`
  - Summary: Added explicit-confirmation PowerShell/Python runners, access and resume guards, terminal/file iteration logs, target checkpoints, final artifact reload checks, metrics/report manifests, and CV/preparation post-open guards. DryRun reported 3 targets, 9 estimators, 197 features, 12 verified CV checkpoints, and 21,452 holdout rows; RE5 tests 9 and full tests 73 passed with target unopened and no fit.

- `session:20260816-2040`
  - Started: 2026-08-16T20:40+09:00
  - Last activity: 2026-08-16T20:40+09:00
  - Focus: Resolve whether the frozen binary model and RE5 Quantile should run together and whether the binary model should be retrained.
  - Updated keys: `decision:implementation-checklist`, `proposal:policy-intervention-digital-twin`, `decision:re-stage5-partial-contract`, `decision:stage6-service-retirement`, `handoff:current`
  - Summary: Chose a single-model service architecture: RE5 LightGBM Quantile only. The binary model and Stage 6 will not be retrained or exposed and are archived for audit/reproducibility; user direct shock rates are the operational fallback. No artifacts were deleted, no model was fit, and the holdout remained unopened.

- `session:20260816-2030`
  - Started: 2026-08-16T20:30+09:00
  - Last activity: 2026-08-16T20:30+09:00
  - Focus: Record the user's RE5 LightGBM choice and clarify whether it replaces the existing Stage 6 model.
  - Updated keys: `decision:implementation-checklist`, `decision:re-stage5-partial-contract`, `handoff:current`
  - Summary: Recorded LightGBM Quantile as the approved internal-holdout candidate only. Confirmed that the frozen model is a binary persistent-decline classifier and RE5 is a continuous quantile-regression family using the same source Panel and 197-feature baseline but different labels and eligible rows; Stage 6 role and holdout execution remain pending clarification.

- `session:20260816-2017`
  - Started: 2026-08-16T20:17+09:00
  - Last activity: 2026-08-16T20:21+09:00
  - Focus: Verify the user's completed RE5 development CV and prepare an evidence-based model recommendation without opening the holdout or selecting a model automatically.
  - Updated keys: `decision:implementation-checklist`, `decision:re-stage5-partial-contract`, `handoff:current`
  - Summary: Verified all 72 Target-Fold-model tasks and 144 paired checkpoint files with no integrity failures. LightGBM beat both simple baselines on every Fold and has the best overall error-interval-runtime balance; XGBoost's mean-MAE edge is only 0.17-0.51%. Documented the result while leaving LightGBM candidate approval, Stage 6 status, and holdout execution pending explicit user approval.

- `session:20260816-1805`
  - Started: 2026-08-16T18:05+09:00
  - Last activity: 2026-08-16T18:10+09:00
  - Focus: Fix the Pandas read-only-array failure and, with explicit user authorization, run exactly one RE5 CV task before stopping.
  - Updated keys: `decision:re-stage5-partial-contract`, `issue:re5-pandas-readonly-array`, `handoff:current`
  - Summary: Added writable array copies, two regression tests, resumable failure status, and a one-task safety limit. All 70 tests passed; task 1/72 completed with MAE 1.371667 and Coverage 0.8367, its 20,600-row checkpoint hash verified, and execution stopped with holdout unopened.

- `session:20260816-1759`
  - Started: 2026-08-16T17:59+09:00
  - Last activity: 2026-08-16T18:04+09:00
  - Focus: Diagnose and fix the user's RE5 pre-fit missing-feature failure without running any model training.
  - Updated keys: `decision:re-stage5-partial-contract`, `issue:re5-derived-feature-materialization`, `handoff:current`
  - Summary: Connected the existing leakage-safe Stage 4.5 feature builder to RE5 preparation, regenerated both Parquets, and added direct 197-feature checks to prepare, verify, and DryRun. Hashes and all 68 tests passed; CV remains not started and the same user command can now be rerun.

- `session:20260816-1712`
  - Started: 2026-08-16T17:12+09:00
  - Last activity: 2026-08-16T17:18+09:00
  - Focus: Resume RE5 through leakage-safe baseline preparation and provide user-operated, progress-visible model training without Codex fitting any model.
  - Updated keys: `decision:implementation-checklist`, `decision:re-stage5-partial-contract`, `handoff:current`
  - Summary: Built and verified Target v2, Panel v2, 4 chronological Folds, EDA, Feature contract, hashes, and a 72-task resumable CV runner. All 68 tests passed; actual model fits and holdout Target accesses remained zero, so RE5 awaits the user's terminal run and subsequent model approval.

- `session:20260816-1121`
  - Started: 2026-08-16T11:21+09:00
  - Last activity: 2026-08-16T16:47+09:00
  - Focus: Incorporate security/review feedback into product naming, precision boundaries, presentation positioning, Hero design, policy-depth rationale, and user validation.
  - Updated keys: `decision:mvp-scope`, `decision:implementation-checklist`, `decision:re-stage3-input-calculation-contract`, `decision:presentation-and-user-validation`, `handoff:current`
  - Summary: Updated the three planning documents and approved future contracts for categorical timing bands over the unchanged engine and a verified declining-cash Hero. Replaced infeasible real-user recruitment with 8 fixed synthetic personas, frozen oracle outputs, 8/8 functional consistency and zero-prohibited-claim Gates, and explicit bans on fabricated satisfaction or real-usability claims; no implementation was run.

- `session:20260816-1100`
  - Started: 2026-08-16T11:00+09:00
  - Last activity: 2026-08-16T11:08+09:00
  - Focus: Present the RE5 approval contract, record partial approval, and verify 2026Q1-Q2 estimated-sales availability and evaluation-metric applicability.
  - Updated keys: `decision:re-stage5-partial-contract`, `handoff:current`
  - Summary: The user fully approved the RE5 contract, including 2025Q1 Purge, 2025Q2 holdout reference with 2025Q3-Q4 outcomes, QoQ challenger-only use, expanded continuous/quantile metrics, and frozen LightGBM benchmark/Fallback status, while explicitly instructing that RE5 not start now. The plan, checklist, standalone contract, and handoff were updated; no implementation or external acquisition occurred.

- `session:20260816-1026`
  - Started: 2026-08-16T10:26+09:00
  - Last activity: 2026-08-16T10:47+09:00
  - Focus: Implement and verify RE Stage 4 policy financial-event conversion and baseline impact application.
  - Updated keys: `decision:implementation-checklist`, `decision:re-stage4-policy-financial-event-engine`, `handoff:current`
  - Summary: Completed `re4-v1` across all 10 policies and 30 reviewed Events, produced 561 representative dated Events, preserved missing official terms without invention, passed hand checks 26/26, RE4 tests 12, and all 64 project tests, and recorded no downstream Target, data, model, metric, policy, service, or schedule change.

- `session:20260816-0943`
  - Started: 2026-08-16T09:43+09:00
  - Last activity: 2026-08-16T09:57+09:00
  - Focus: Implement and verify the approved RE Stage 3 personal baseline cash-flow contract.
  - Updated keys: `decision:implementation-checklist`, `decision:re-stage3-input-calculation-contract`, `handoff:current`
  - Summary: Completed `re3-v1` simple and detailed inputs, 13-week and 6-month cash flow, three detailed loan methods, validation, templates, five synthetic cases, hand checks 26/26, and all 52 project tests; Gate RE3 passed with no downstream Target, data, model, metric, policy, or schedule change.

- `session:20260816-0018`
  - Started: 2026-08-16T00:18+09:00
  - Last activity: 2026-08-16T00:25+09:00
  - Focus: Audit existing downloads, correct the future acquisition boundary, and record RE3 contract approval without implementation.
  - Updated keys: `decision:data-download-catalog`, `decision:re-stage3-input-calculation-contract`, `convention:user-owned-data-acquisition`, `handoff:current`
  - Summary: Confirmed historical acquisition roles, allowed Codex to search and report exact official links while keeping download and raw loading user-owned, recorded the eight approved RE3 rules, and left RE3 code and tests completely unstarted until a new user request.

- `session:20260815-2341`
  - Started: 2026-08-15T23:41+09:00
  - Last activity: 2026-08-16T00:08+09:00
  - Focus: Finalize A+C, complete RE Stage 2 official-source collection and policy knowledge-base QA, and apply the mandatory downstream feedback review.
  - Updated keys: `decision:implementation-checklist`, `decision:data-download-catalog`, `decision:re-stage1-contract`, `decision:re-stage2-policy-knowledge-base`, `handoff:current`
  - Summary: Completed RE2 with 10 policies, 27 official source records, 56 eligibility Rules, 20 reviewed eligibility examples, 30 financial Events, 11 versions, 217 pre-index chunks, and nine passing tests; updated RE3 expense inputs, RE4 event identity/deduplication, and RE6 session-only eligibility inputs without starting RE3, RAG, Target v2, or model v2.

- `session:20260815-2307`
  - Started: 2026-08-15T23:07+09:00
  - Last activity: 2026-08-15T23:40+09:00
  - Focus: QA and integrate P-01/P-03/P-04/P-05, complete RE Stage 1, compare six provisional policy portfolios, and establish the mandatory end-of-Stage feedback loop.
  - Updated keys: `decision:mvp-scope`, `decision:implementation-checklist`, `decision:data-download-catalog`, `decision:pre-re1-policy-qa`, `decision:re-stage1-contract`, `convention:stage-result-feedback-loop`, `handoff:current`
  - Summary: Completed the 1,005-record to 827-group policy integration, generated six provisional portfolios with 62 rows and 25 unique candidates, froze 503 Stage 0-6 files by hash, passed the RE1 guard and eight tests, updated the plan/checklist/guide/log, and changed RE2 to begin only after final policy approval. No new external data, final policy selection, Target, model, Rule, Event, or RAG build occurred.

- `session:20260815-2205`
  - Started: 2026-08-15T22:05+09:00
  - Last activity: 2026-08-15T22:58+09:00
  - Focus: Collect and document P-01 Bizinfo and P-05 SME24 data, including conservative cross-checks, complete variable dictionaries, and verified usage limitations.
  - Updated keys: `decision:data-download-catalog`, `issue:sme24-date-filter-semantics`, `handoff:current`
  - Summary: Preserved and verified the SME24 collection and exact Bizinfo crosswalk, then added API-root README files documenting 20 Bizinfo source fields plus 4 candidate fields and 61 SME24 source fields plus 5 candidate and 26 crosswalk fields. Header coverage, core counts, code fences, local links, and trailing whitespace all passed validation.

- `session:20260815-2153`
  - Started: 2026-08-15T21:53+09:00
  - Last activity: 2026-08-15T22:00+09:00
  - Focus: Collect the required Bizinfo current-year announcement feed and produce a bounded small-business candidate dataset with reproducible QA.
  - Updated keys: `decision:data-download-catalog`, `issue:bizinfo-mixed-registration-years`, `handoff:current`
  - Summary: Downloaded both advertised API pages without exposing the key, preserved 1,545 raw records, separated 1,521 registrations from 2026, generated 257 discovery-only small-business candidates, and verified response counts, IDs, years, file rows, result codes, and key absence.

- `session:20260815-2014`
  - Started: 2026-08-15T20:14+09:00
  - Last activity: 2026-08-15T22:08+09:00
  - Focus: Research competitive differentiation, replace the plan and checklist, correct the policy-source hierarchy, and create a verified future-data acquisition catalog while preserving Stage 0-6.
  - Updated keys: `decision:mvp-scope`, `decision:implementation-checklist`, `decision:policy-source-hierarchy`, `decision:data-download-catalog`, `decision:competitive-positioning`, `decision:recommendation-role-boundary`, `proposal:policy-intervention-digital-twin`, `decision:stage7-finance-burden-policy-v1`, `handoff:current`
  - Summary: Expanded the plan and checklist, corrected guide links, and clarified the acquisition order: finish P-05 and deduplicate it with P-01 first; P-04 fixed attachments and P-03 shared references can be captured immediately, while P-02 and policy-specific P-03 documents are collected only after approving the 8-12-policy shortlist. No policy application is submitted.

- `session:20260815-1106`
  - Started: 2026-08-15T11:06+09:00
  - Last activity: 2026-08-15T12:19+09:00
  - Focus: Execute Stage 4.5 plot-free modeling EDA, leakage-safe derived Features, and a user-reviewable Feature contract.
  - Updated keys: `decision:stage45-modeling-eda-plan`, `decision:stage45-feature-contract-d`, `issue:stage5-preprocessing-memory`, `handoff:current`
  - Summary: Completed the plot-free Stage 4.5 analysis, then recorded the user's D approval across the contract, manifest, config, checklist, and execution guard; Gate 4.5 passed while Stage 5 remained unstarted and blocked pending a future request and exact Ablation tolerance approval.

- `session:20260815-1221`
  - Started: 2026-08-15T12:21+09:00
  - Last activity: 2026-08-15T12:24+09:00
  - Focus: Verify the ML observation unit and assess whether a finer Target would be valid and efficient.
  - Updated keys: `decision:ml-observation-unit`, `handoff:current`
  - Summary: Confirmed that the current unit is the finest defensible supervised Target in the nine aggregated datasets; finer grids or stores would require new matching outcome labels, so the recommendation is to retain the current external-risk model and differentiate individual businesses in the separate financial-diagnosis layer. No design change or model run occurred.

- `session:20260815-1229`
  - Started: 2026-08-15T12:29+09:00
  - Last activity: 2026-08-15T19:32+09:00
  - Focus: Complete Stage 5 evaluation and align final model/threshold decisions with the competition's working-service MVP objective.
  - Updated keys: `decision:stage45-modeling-eda-plan`, `decision:stage45-feature-contract-d`, `decision:stage5-full-comparison-result`, `decision:stage5-optuna-result`, `decision:stage5-oof-ensemble-run-plan`, `decision:stage5-oof-ensemble-result`, `decision:stage5-service-first-policy`, `decision:stage5-threshold-service-policy`, `decision:stage5-final-2025-result`, `decision:stage6-relative-ranking-output`, `decision:recommendation-role-boundary`, `issue:stage5-preprocessing-memory`, `handoff:current`
  - Summary: Completed and documented Stage 5, approved dual relative-risk comparisons, and fixed the service role boundary: ML drives risk discovery and urgency, official rules drive eligibility, the deterministic engine ranks eligible policies, and RAG only explains. The plan and Stage 8 checklist now remove arbitrary preset weights and defer them until policy data and evaluation cases exist.

- `session:20260815-1956`
  - Started: 2026-08-15T19:56+09:00
  - Last activity: 2026-08-15T20:19+09:00
  - Focus: Complete Stage 6, then prepare the mandatory user decision contract for Stage 7 financial-burden scoring.
  - Updated keys: `decision:stage6-relative-ranking-output`, `decision:stage7-finance-burden-policy-v1`, `handoff:current`
  - Summary: Stage 6 passed with all 27 tests; the user approved finance-burden policy v1 and requested documentation only, so the exact formula, bands, edge cases, example result, and non-DSR limitations were added to the plan without implementation.

## Session archive

- `session:20260814-1952` — 2026-08-14T19:52+09:00 to 2026-08-14T20:21+09:00; plan/checklist reformat; updated `decision:mvp-scope`, `decision:implementation-checklist`, `convention:plan-source-preservation`, `handoff:current`; created the original 13-stage execution checklist.
- `session:20260814-2034` — 2026-08-14T20:34+09:00 to 2026-08-15T00:39+09:00; Stage 0-4 and Stage 4.5 planning; updated project decisions, conventions, issues, and `handoff:current`; completed the early data pipeline and left Stage 5 blocked pending feature work.
