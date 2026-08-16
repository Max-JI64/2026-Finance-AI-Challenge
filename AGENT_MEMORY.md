# Agent Memory

> Codex-maintained project memory. Verify time-sensitive facts against the
> current workspace.

## Project snapshot

- Last updated: 2026-08-16T11:08+09:00
- Purpose: Build a working Seoul small-business policy-impact simulator that combines area-industry sales-environment scenarios, deterministic 13-week and 6-month cash flow, official policy eligibility and financial terms, intervention comparison, and evidence-grounded AI explanations.
- Important paths: `프로젝트 계획서.md` is the main MVP plan; `MVP 단계별 구현 체크리스트.md` is the execution and completion-gate document; `reports/re_stage1/` and `reports/re_stage2/` preserve the service and 10-policy contracts; `src/cashflow/`, `config/re_stage3.yaml`, and `reports/re_stage3/` contain the completed deterministic baseline cash-flow engine; `src/policy/`, `config/re_stage4.yaml`, `data/processed_re/policy/re_stage4/`, and `reports/re_stage4/` contain the completed policy financial-event engine and Gate RE4 evidence; `data/raw_re/향후 데이터 다운로드 가이드.md` is the acquisition guide.

## Durable decisions

- `decision:mvp-scope`
  - Created: 2026-08-14T19:55+09:00
  - Updated: 2026-08-15T23:40+09:00
  - Status: active
  - Content: The MVP targets Seoul small businesses and compares no action, non-debt support, debt relief, new borrowing, and mixed interventions through deterministic 13-week and 6-month cash-flow effects. Area-industry ML supplies aggregate external scenarios, official rules determine eligibility, policy terms become financial events, and RAG/LLM only explains official evidence and trade-offs; individual closure probability, credit scoring, approval probability, account/POS integration, and causal policy impact are excluded.
  - Evidence: User-approved rewrite of `프로젝트 계획서.md`, completed `reports/re_stage1/service_contract.md`, and `config/re_stage1.yaml`.

- `decision:implementation-checklist`
  - Created: 2026-08-14T20:21+09:00
  - Updated: 2026-08-16T10:47+09:00
  - Status: active
  - Content: The implementation checklist mirrors completed Stage 0-6 and RE Stage 1-4 plus pending RE Stage 5-9. It records the A+C 10-policy knowledge base, completed `re3-v1` baseline cash-flow engine, and completed RE4 policy financial-event engine, and requires a downstream-impact review plus necessary plan/config/test updates before every next Stage starts.
  - Evidence: `MVP 단계별 구현 체크리스트.md` and Gate evidence under `reports/re_stage1/`, `reports/re_stage2/`, `reports/re_stage3/`, and `reports/re_stage4/`.

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
  - Updated: 2026-08-16T09:57+09:00
  - Status: active
  - Content: Gate RE3 passed with engine `re3-v1`. It supports simple input and detailed CSV; preserves negative calculated cash; treats simple monthly debt payment as combined principal-plus-interest outflow; calculates equal-principal, equal-payment, and bullet schedules only for detailed loans; uses monthly interest without daily accrual and won-level half-up rounding; and requires user-set safe cash plus actual receipt/payment dates without defaults.
  - Evidence: `src/cashflow/`, `config/re_stage3.yaml`, `reports/re_stage3/verification.md`, `reports/re_stage3/manifest.json`, and `tests/test_re_stage3_cashflow.py`; hand checks 26/26 and full tests 52 passed.

- `decision:re-stage4-policy-financial-event-engine`
  - Created: 2026-08-16T10:47+09:00
  - Updated: 2026-08-16T10:47+09:00
  - Status: active
  - Content: Gate RE4 passed with contract `re4-v1`. All 30 reviewed RE2 financial Events across 10 policies remain represented: 27 are calculable only with explicit user scenario values, `SEOUL_SAFE_ACCOUNT` and `SAFETY_TEST` are blocked because official financial terms are missing, and `SEOUL_FACILITY` requires a subproduct selection. The engine supports grants, reimbursements, vouchers, direct and interest-subsidized loans, refinancing, and guarantees with linked-event deduplication, source provenance, approved/not-approved scenarios, and no approval probability or causal-effect claim.
  - Evidence: `src/policy/`, `config/re_stage4.yaml`, `data/processed_re/policy/re_stage4/policy_event_profiles.csv`, `reports/re_stage4/verification.md`, `reports/re_stage4/manifest.json`, and `tests/test_re_stage4_policy_events.py`; hand checks 26/26, RE4 tests 12 passed, and full tests 64 passed.

- `decision:re-stage5-partial-contract`
  - Created: 2026-08-16T11:00+09:00
  - Updated: 2026-08-16T11:08+09:00
  - Status: active
  - Content: The RE5 contract is fully approved but implementation is explicitly paused until a new user request. It fixes the existing observation unit; YoY Target A/B plus minimum-YoY auxiliary; QoQ as EDA/challenger only; no automatic clipping; 2021Q4-2024Q4 development with 2024Q1-Q4 expanding Validation; one-quarter Purge with 2025Q1 before the 2025Q2 reference holdout; 2025Q3-Q4 holdout outcomes; continuous and quantile metrics; and frozen LightGBM v1 only as a non-training benchmark/Fallback whose AUROC/AUPRC stays in an appendix.
  - Evidence: `reports/re_stage5/approved_contract.md`, `프로젝트 계획서.md`, and `MVP 단계별 구현 체크리스트.md`; no Target, EDA, Panel, Fold, model, evaluation, external collection, or download was executed.

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
  - Updated: 2026-08-16T00:08+09:00
  - Status: active
  - Content: The user approved A+C as the final 10-policy MVP portfolio. RE2 preserves 27 official source records and structures 10 Metadata rows, 56 eligibility Rules, 20 reviewed eligibility examples, 30 financial Events, 11 versions, and 217 pre-index text chunks. Seoul funding is split into 17 sub-events, rechallenge into three types, and any missing amount, date, status, or process stays `미확인`; no RAG index was built.
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
  - Updated: 2026-08-15T21:02+09:00
  - Status: active_plan
  - Content: The policy-impact simulator is now the approved project-plan direction. `프로젝트 계획서.md` preserves completed Stage 0-6 and replaces the old Stage 7 onward plan with RE Stage 1-9: service contract, policy knowledge base, personal cash flow, policy financial events, new data and quantile model, eligibility and RAG, intervention comparison, web integration, and deployment QA. The existing LightGBM and Stage 6 remain frozen baseline and fallback evidence; a new quantile challenger replaces them only after time-based error, coverage, industry stability, service utility, and a new independent audit Gate pass.
  - Evidence: User instruction and the rewritten `프로젝트 계획서.md`; no data, Target, model, or application implementation was executed in the rewrite turn.

- `decision:stage7-finance-burden-policy-v1`
  - Created: 2026-08-15T20:19+09:00
  - Updated: 2026-08-15T21:02+09:00
  - Status: superseded
  - Content: The previously approved 20/20/35/25 heuristic finance-burden index and low/caution/high bands were never implemented and are removed from the active plan. Individual ratios may remain as descriptive inputs, but service decisions use dated cash-flow balances, runway, debt service, total obligation, and intervention comparisons instead of a composite score.
  - Evidence: User-directed replacement of the old Stage 7 onward plan in `프로젝트 계획서.md`; the historical approval remains recorded here and in `LOG.md`.

## Working conventions

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

## Current handoff

- `handoff:current`
  - Updated: 2026-08-16T11:08+09:00
  - Current state: Gates RE1-RE4 have passed. `re4-v1` preserves all 30 reviewed policy Events and applies user-specified intervention scenarios to the RE3 baseline with dated cash, cost-reduction, debt, interest, fee, and guarantee-fee effects; hand checks 26/26 and all 64 project tests passed.
  - Next step: Do not start RE5 until the user explicitly asks to resume. On resumption, begin only with the approved existing-Panel Target QA and Baseline contract; do not collect new external data, and stop for approval if observed Target distributions would require a semantic processing change.
  - Blockers: No RE5 contract decision remains, but execution is intentionally paused by user instruction. A new independent audit remains unavailable because estimated sales ends at 2025Q4; 2025Q3-Q4 is only an internal temporal holdout, and external downloads remain user-owned.

## Session log

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

- `session:20260814-1952`
  - Started: 2026-08-14T19:52+09:00
  - Last activity: 2026-08-14T20:21+09:00
  - Focus: Reformat the MVP plan and create an implementation checkpoint document without browsing embedded links.
  - Updated keys: `decision:mvp-scope`, `decision:implementation-checklist`, `convention:plan-source-preservation`, `handoff:current`
  - Summary: Reorganized the plan, then created a 13-stage implementation checklist with 449 tasks covering data, ML, finance diagnosis, recommendation, RAG, integration, deployment, and final acceptance.

- `session:20260814-2034`
  - Started: 2026-08-14T20:34+09:00
  - Last activity: 2026-08-15T00:39+09:00
  - Focus: Complete Stages 0-3 from project setup through chunk-based raw QA and a reproducible panel build.
  - Updated keys: `decision:stage0-stack`, `decision:solo-team-validation`, `decision:stage3-panel-contract`, `decision:stage4-persistent-target-structure`, `decision:stage4-cv-design`, `decision:stage45-modeling-eda-plan`, `decision:stage5-model-selection-workflow`, `decision:stage5-comparison-contract`, `convention:user-owned-data-acquisition`, `convention:bounded-raw-inspection`, `convention:chronological-project-log`, `convention:mandatory-user-decision`, `convention:proportional-verification`, `issue:bounded-reader-full-file-call`, `issue:store-2025-header-language`, `issue:stage5-preprocessing-memory`, `handoff:current`
  - Summary: Completed Stages 2-4, then inserted a detailed plot-free Stage 4.5 plan for modeling EDA, derived Features, and Feature-contract approval; no analysis was run, Stage 5 remains blocked, and the new session should begin from this plan.

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
