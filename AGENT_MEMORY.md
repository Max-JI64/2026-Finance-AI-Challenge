# Agent Memory

> Codex-maintained project memory. Verify time-sensitive facts against the
> current workspace.

## Project snapshot

- Last updated: 2026-08-15T20:19+09:00
- Purpose: Build a working MVP that predicts Seoul commercial-district sales-environment risk, diagnoses a small business's financial burden, and recommends policy support with official-document-grounded RAG explanations.
- Important paths: `프로젝트 계획서.md` is the main MVP plan; `MVP 단계별 구현 체크리스트.md` is the execution and completion-gate document; `대회개요.md` contains the competition overview.

## Durable decisions

- `decision:mvp-scope`
  - Created: 2026-08-14T19:55+09:00
  - Updated: 2026-08-14T19:55+09:00
  - Status: active
  - Content: The MVP targets Seoul small businesses and separates external commercial-district risk from internal financial burden before policy-support ranking and RAG explanation.
  - Evidence: `프로젝트 계획서.md`, sections 1 through 41.

- `decision:implementation-checklist`
  - Created: 2026-08-14T20:21+09:00
  - Updated: 2026-08-14T20:21+09:00
  - Status: active
  - Content: Track implementation with P0 mandatory tasks, P1 quality work, P2 extensions, and evidence-based Gates from data acquisition through deployment; ML and RAG remain mandatory when scope is reduced.
  - Evidence: `MVP 단계별 구현 체크리스트.md`.

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
  - Updated: 2026-08-15T19:32+09:00
  - Status: active
  - Content: ML is the core engine for risk discovery and intervention urgency, official rules exclusively determine policy eligibility, the Recommendation Engine ranks eligible policies using user need, financial burden, policy-purpose fit and ML urgency, and RAG/LLM only explains official evidence. ML urgency is important for officially relevant stabilization or recovery policies but never changes eligibility or claims approval probability; exact weights and bands are deferred until policy metadata and evaluation cases exist.
  - Evidence: User approval, `프로젝트 계획서.md` sections 4, 24, 33, 34, 38, and 41, and Stage 8 in `MVP 단계별 구현 체크리스트.md`.

- `decision:competitive-positioning`
  - Created: 2026-08-15T20:14+09:00
  - Updated: 2026-08-15T20:32+09:00
  - Status: active
  - Content: Do not claim novelty from commercial-district analysis, store diagnosis, AI sales forecasting, policy matching, proactive risk alerts, or one-stop recovery routing. The 2026 MSS Small Business Crisis AlertTalk already detects high-risk, delinquent, and closed borrowers and links diagnosis, debt counseling, and recovery support. A defensible service distinction must therefore expose the financial consequence of each intervention, not merely detect risk or list programs; do not claim a market first without a formal prior-art search.
  - Evidence: Public web research on 2026-08-15 against official Seoul, MSS, public-data, KB, and KCD sources; no reviewed public source showed a Korean official-policy cash-flow intervention simulator, but absence was not proven.

- `proposal:policy-intervention-digital-twin`
  - Created: 2026-08-15T20:32+09:00
  - Updated: 2026-08-15T20:47+09:00
  - Status: documented
  - Content: The comprehensive redesign blueprint recommends a policy-intervention simulator that compares no action, cost reduction, grants or vouchers, interest support or refinancing, new borrowing, and mixed plans through deterministic 13-week and 6-month cash-flow scenarios. It retires the planned opaque finance score and policy-fit ranking, prioritizes official policy terms and personal cash-flow inputs, freezes Stage 0-6 as evidence and a baseline, and develops a new multi-horizon quantile sales-environment challenger because the current binary rank does not supply shock magnitude. The challenger replaces Stage 6 only after time-based error, interval coverage, industry stability, service utility, and a new independent audit Gate pass.
  - Evidence: User requested the full keep, rebuild, replace, and data-timing plan in `프로젝트 차별화 구상.md`; the 1,648-line document was created and structurally checked, while the current project plan and implementation remain unchanged until the next authorized rewrite.

- `decision:stage7-finance-burden-policy-v1`
  - Created: 2026-08-15T20:19+09:00
  - Updated: 2026-08-15T20:19+09:00
  - Status: active
  - Content: The user approved the documented Stage 7 heuristic index: rent/labor/repayment/debt-stock weights 20/20/35/25 with component caps at 30%/50%/20%/100%, display bands below 40/40-69.99/70+ as low/caution/high, zero-sales unavailable handling, optional-field exclusion, and no composite risk type yet.
  - Evidence: User approval and `프로젝트 계획서.md`, section 22 `승인된 금융부담 정책 v1`; documentation only, not implemented.

## Working conventions

- `convention:plan-source-preservation`
  - Created: 2026-08-14T19:55+09:00
  - Updated: 2026-08-14T19:55+09:00
  - Status: active
  - Content: When reorganizing the project plan, preserve all source information; treat embedded URLs as download references and do not browse or analyze them unless the user later asks.

- `convention:user-owned-data-acquisition`
  - Created: 2026-08-14T20:51+09:00
  - Updated: 2026-08-14T20:51+09:00
  - Status: active
  - Content: The user will download competition data directly; do not browse, download, extract, or audit external datasets unless the user explicitly reverses this instruction.

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

## Current handoff

- `handoff:current`
  - Updated: 2026-08-15T20:47+09:00
  - Current state: Stage 6 and the existing plan remain intact, but `프로젝트 차별화 구상.md` now contains the complete recommended redesign: policy-intervention cash-flow simulation, a keep/freeze/rebuild/retire matrix, new policy and personal-finance data timing, a quantile-model challenger, R0-R8 implementation stages, validation Gates, and submission wording. No data collection, Target regeneration, model training, plan rewrite, or checklist rewrite was performed in this turn.
  - Next step: When the user requests the plan change, rewrite `프로젝트 계획서.md` around the approved redesign while preserving the executed Stage 0-6 record, then separately realign `MVP 단계별 구현 체크리스트.md`. Before executing R1 or R4, obtain the exact approvals for the 8-12 policy scope, personal cash-flow input contract, Target v2 definition, time split, metrics, and new independent audit period.
  - Blockers: The current plan still authorizes Stage 7 finance-burden v1, while the redesign recommends retiring it; implementation must not start until the plan rewrite explicitly resolves that conflict.

## Session log

- `session:20260815-2014`
  - Started: 2026-08-15T20:14+09:00
  - Last activity: 2026-08-15T20:47+09:00
  - Focus: Research competitive differentiation and produce a complete clean-slate-capable redesign blueprint without protecting sunk costs.
  - Updated keys: `decision:competitive-positioning`, `proposal:policy-intervention-digital-twin`, `handoff:current`
  - Summary: Confirmed that proactive risk alerts and generic AI bookkeeping overlap current services, then wrote `프로젝트 차별화 구상.md` as a full redesign source document. It recommends deterministic policy cash-flow impact comparison, retires the opaque finance score, freezes Stage 0-6 as baseline evidence, rebuilds a quantile external-scenario model only if it passes a head-to-head Gate, specifies when each new dataset is needed, and defines R0-R8 execution and verification; the current plan, checklist, data, and implementation were not changed.

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
