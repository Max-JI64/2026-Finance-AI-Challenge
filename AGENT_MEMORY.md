# Agent Memory

> Codex-maintained project memory. Verify time-sensitive facts against the
> current workspace.

## Project snapshot

- Last updated: 2026-08-21T11:28+09:00
- Purpose: Build a working Seoul small-business policy-finance impact simulator whose hero compares 13-week survival and 6-month debt consequences across no action and representative interventions, using area-industry stress scenarios, schedule-based cash flow, official policy terms, and evidence-grounded AI explanations without causal-effect or personal-sales claims.
- Important paths: `프로젝트 계획서.md` is the main MVP plan; `MVP 단계별 구현 체크리스트.md` is the execution and completion-gate document; `src/cashflow/` and `src/policy/` hold the completed RE3-RE4 engines; `config/re_stage5.yaml` and `reports/re_stage5/` hold the completed aggregate scenario model evidence; `src/policy/eligibility.py`, `src/rag/`, and `reports/re_stage6/` hold RE6; `src/recommendation/` and `reports/re_stage7/` hold the RE7 decision engine; `app/`, `src/integration/re_stage8.py`, `src/policy/discovery.py`, `src/policy/re_stage8_2_events.py`, `src/rag/hybrid_search.py`, `config/re_stage8.yaml`, and `reports/re_stage8_2/` hold the completed RE8.2 integration; `reports/re_stage9/`, `output/pdf/RE9_기능명세서.pdf`, `Dockerfile`, and `requirements-runtime.txt` hold the RE9 local submission package; `data/raw_re/향후 데이터 다운로드 가이드.md` is the acquisition guide.

## Durable decisions

- `decision:mvp-scope`
  - Created: 2026-08-14T19:55+09:00
  - Updated: 2026-08-16T11:28+09:00
  - Status: active
  - Content: The MVP is named `서울 소상공인 정책금융 영향 시뮬레이터` and compares no action, grants, cost reduction, refinancing, policy loans, and mixed interventions through 13-week cash survival plus 6-month debt effects. Aggregate ML outputs are labeled area-environment stress scenarios; personal sales/closure, credit or approval probability, account/POS integration, causal policy impact, and claims of AI optimal recommendation are excluded.
  - Evidence: User-approved updates to `프로젝트 계획서.md`, `프로젝트 차별화 구상.md`, and `MVP 단계별 구현 체크리스트.md`; the completed RE1 contract/config retain the historical former name and are migrated only in current RE8 API/UI work.

- `decision:implementation-checklist`
  - Created: 2026-08-14T20:21+09:00
  - Updated: 2026-08-17T14:33+09:00
  - Status: active
  - Content: The checklist records completed Stage 0-6 and RE Stage 1-8.2 with Gate evidence. RE8.3 is now the active user-directed service review and revision cycle; the existing RE9 8-persona and 20-case package is a pre-revision baseline, and external deployment is paused until the user explicitly closes RE8.3 and separately approves a free-only platform.
  - Evidence: `MVP 단계별 구현 체크리스트.md`, `프로젝트 계획서.md`, `reports/re_stage8_3/service_review_log.md`, Gate evidence under `reports/re_stage1/` through `reports/re_stage9/`, and `config/re_stage9.yaml`.

- `decision:re-stage9-local-submission-package`
  - Created: 2026-08-17T14:24+09:00
  - Updated: 2026-08-17T14:24+09:00
  - Status: active
  - Content: The user approved partial refinancing for the 80 million won high-debt persona: refinance only the official 50 million won cap and retain the remaining 30 million won on its original schedule. RE9 local QA passed 8/8 personas, 20/20 BM25 official-evidence cases, zero prohibited positive claims, two-attempt Embedding fallback, safe invalid-input handling, and 149 project tests; screenshot image analysis was not performed by user request.
  - Evidence: `scripts/build_re_stage7_examples.py`, `data/samples/re_stage9/`, `scripts/build_re_stage9_evidence.py`, `tests/test_re_stage9.py`, `reports/re_stage9/manifest.json`, and `output/pdf/RE9_기능명세서.pdf`.

- `decision:re-stage8-3-user-review-cycle`
  - Created: 2026-08-17T14:33+09:00
  - Updated: 2026-08-17T14:33+09:00
  - Status: active
  - Content: External deployment is paused while the user directly reviews the local service and identifies changes. Each request is logged with a stable ID, desired result, acceptance criteria, implementation evidence, and user recheck; Gate RE8.3 closes only after the user explicitly says revisions are complete. Screenshot and image analysis remain excluded. Any later hosting must use a sustained free tier and still requires separate platform and deployment approval.
  - Evidence: `reports/re_stage8_3/service_review_log.md`, `MVP 단계별 구현 체크리스트.md`, `프로젝트 계획서.md`, `config/re_stage9.yaml`, and `reports/re_stage9/deployment_runbook.md`.

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
  - Updated: 2026-08-17T13:16+09:00
  - Status: resolved
  - Symptom: User area, industry, revenue, cash, and debt inputs change the market scenario and cash flow, but do not dynamically discover policies across the approved portfolio; the comparison screen always builds the fixed Hero alternatives.
  - Cause: `compare_sample` calls `build_hero` and maps only hardcoded `HERO_POLICY_BY_ALTERNATIVE` policies, while the full deterministic eligibility engine is exposed through a separate API and the UI does not collect its broader profile fields.
  - Fix: RE8.2 now uses approved Hybrid retrieval across all 17 policies, asks only candidate-specific missing questions, applies frozen RE6 or separate reviewed overlay Rules, and feeds only verified business-cash Events with explicit user amounts and dates into the deterministic four-goal ranking. Embeddings and Luna never override eligibility or cash-flow outcomes.
  - Evidence: `src/integration/re_stage8.py`, `src/policy/discovery.py`, `src/policy/re_stage8_2_events.py`, `src/rag/hybrid_search.py`, and `src/recommendation/engine.py`.

## Current handoff

- `handoff:current`
  - Updated: 2026-08-21T11:28+09:00
  - Current state: The user ended this RE8.3 revision session after `RE8.3-001` through `RE8.3-010`. The latest step-2 diagnosis action shows a centered loading overlay with actual elapsed seconds while market ranges and all three comparisons run; presentation presets only fill inputs, clear stale results, and wait for the step-2 action. Static asset `re8.3-010.3`, live HTTP checks, JavaScript syntax, whitespace checks, and 46 focused tests pass.
  - Next step: In a new session, read this memory and `reports/re_stage8_3/service_review_log.md`, start from static asset `re8.3-010.3`, and continue only the user's next review request. If visual acceptance is requested, first recheck the step-2 loading overlay and elapsed timer for both manual and preset-filled inputs.
  - Blockers: Gate RE9 cannot resume until Gate RE8.3 closes and the user separately approves a viable sustained-free platform and external deployment. Screenshot and image analysis remain excluded; industrial-accident insurance remains outside the frozen 17-policy set.

## Session log

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
