# Agent Memory

> Codex-maintained project memory. Verify time-sensitive facts against the
> current workspace.

## Project snapshot

- Last updated: 2026-08-27T13:30+09:00
- Purpose: Build a bounded-AI Seoul small-business finance copilot that separates store trends from aggregate market scenarios, shows policy candidates without an upfront question gate, lets users choose each selected policy's reviewed conditions in its preparation screen, and compares no action with confirmed or explicitly conditional policy effects on deterministic 13-week and 6-month cash/debt horizons.
- Important paths: `V2 단계별 구현 계획표.md` and `V3 사용자 경험 구성안.md` preserve earlier versions; `V4 구현 계획표.md` and `v4/` preserve the implemented V4; `V5 구현 계획표.md`, `V5 사용자 경험 흐름.md`, `v5/`, `v5/VERIFICATION.md`, and `reports/v5/evaluation/` describe the implemented V5, its V6 comparison baseline, verification evidence, and fixed evaluation Oracles.

## Durable decisions

- `decision:mvp-scope`
  - Created: 2026-08-14T19:55+09:00
  - Updated: 2026-08-16T11:28+09:00
  - Status: active
  - Content: The MVP is named `서울 소상공인 정책금융 영향 시뮬레이터` and compares no action, grants, cost reduction, refinancing, policy loans, and mixed interventions through 13-week cash survival plus 6-month debt effects. Aggregate ML outputs are labeled area-environment stress scenarios; personal sales/closure, credit or approval probability, account/POS integration, causal policy impact, and claims of AI optimal recommendation are excluded.
  - Evidence: User-approved updates to `프로젝트 계획서.md`, `프로젝트 차별화 구상.md`, and `MVP 단계별 구현 체크리스트.md`; the completed RE1 contract/config retain the historical former name and are migrated only in current RE8 API/UI work.

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
  - Updated: 2026-08-27T11:39+09:00
  - Status: active
  - Content: The user approved ending feature development with `V5 Final` instead of building V6 or switching topics. The application-readiness summary proposal remains withdrawn and no new feature is added. V5 intentionally ends at official-application handoff for the recorded policy, privacy, and authority reasons. On 2026-08-27 the user resumed submission and deployment preparation, but no hosting provider or external deployment has yet been approved or executed.
  - Evidence: `프로젝트 계획서.md` section 38.1, `V5 사용자 경험 흐름.md` section 18.1, `V6 실제 수요 검증 보고서.md` section 12, the current user request, and the official DAKER submission page checked on 2026-08-27. V5 tests pass 18/18 and both JavaScript entry files pass syntax checks; no service code, model, data, automatic application, or V6 work changed in this check.

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
  - Updated: 2026-08-27T13:30+09:00
  - Status: active
  - Content: The 2026-09-07 10:00 first submission requires a proposal PDF, function-specification PDF, and executable web-service URL; the URL must remain accessible from 2026-09-07 11:00 through 2026-09-11 23:59. A presentation PDF and source ZIP are required only after selection for the presentation round, by 2026-10-08 23:59. Cloud Run with 1 GiB and scale-to-zero is the preferred submission host if the user can attach a billing account; Render free is simpler but its 512 MB/0.1 CPU instance, 15-minute sleep, roughly one-minute wake, and ephemeral storage create more judging risk.
  - Evidence: Official DAKER, Render, Hugging Face, and Cloud Run documentation checked 2026-08-27; `대회개요.md` lines 77-156; the local V5 server used 293.8 MiB working set after a successful 0.71-second market-scenario request. Current `Dockerfile` runs `app.main:app` and does not copy or launch `v5/`, whose final entry point is `v5.main:app`.

## Current handoff

- `handoff:current`
  - Updated: 2026-08-27T13:30+09:00
  - Current state: V5 functionality remains frozen, and submission preparation is active. Official requirements confirm that the first deadline needs two PDFs and a live URL, not a presentation. The repository is clean and matches `origin/main`; the current Dockerfile still launches pre-V5 `app.main:app`. A local deployment probe passed health, representative demo, and market-scenario requests, measured 293.8 MiB working set after model use, and was stopped after measurement.
  - Next step: Obtain the user's Cloud Run versus Render choice, then create a V5-specific deployment path, deploy it, and verify the public root, health endpoint, representative demo, main user flow, cold start, and required availability window before drafting the proposal and function specification from the official templates.
  - Blockers: Cloud Run is recommended but requires the user's Google Cloud billing-account and project authorization even when usage is intended to stay within the free tier. Render avoids that setup but has tighter 512 MB/0.1 CPU resources and a longer free-tier wake delay. No external service has been created.

## Session log

- `session:20260827-1136`
  - Started: 2026-08-27T11:36+09:00
  - Last activity: 2026-08-27T13:30+09:00
  - Focus: Confirm the competition submission package and assess a free deployment route for V5 Final.
  - Updated keys: `decision:v5-finalization-and-project-close`, `baseline:competition-submission-and-hosting-readiness`, `handoff:current`
  - Summary: Verified from the official DAKER page that the first deadline requires a proposal PDF, function-specification PDF, and executable URL, while the presentation PDF and source ZIP apply only after presentation-round selection. Compared current free-hosting conditions, measured the local V5 server at 293.8 MiB working set after a successful model request, and changed the recommendation to Cloud Run 1 GiB scale-to-zero when billing setup is acceptable; Render free remains the simpler but riskier fallback. Confirmed the repository is clean and up to date and that its Dockerfile launches `app.main:app` rather than `v5.main:app`; no external deployment or service-code change was made.

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
