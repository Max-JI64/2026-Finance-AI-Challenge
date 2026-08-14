# Agent Memory

> Codex-maintained project memory. Verify time-sensitive facts against the
> current workspace.

## Project snapshot

- Last updated: 2026-08-15T00:06+09:00
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
  - Updated: 2026-08-14T23:49+09:00
  - Status: active
  - Content: Do not preselect LightGBM or any final model. After Stage 4 is fixed, compare multiple untuned candidate models with Logistic Regression and a simple baseline under the same four folds, select one final tuning candidate, then run Optuna only for that selected model.
  - Evidence: User instruction and Stage 5 in `MVP 단계별 구현 체크리스트.md`.

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

## Current handoff

- `handoff:current`
  - Updated: 2026-08-15T00:06+09:00
  - Current state: Stage 4 Gate is complete with a fixed 10% persistent-decline Target, 222,973 labeled development rows, 690,307 four-fold membership rows, and 79,506 label-free locked-test Feature rows. Mandatory checks passed once; locked 2025 Target values and statistics remain unmaterialized.
  - Next step: Propose the Stage 5 untuned candidate-model list and evaluation metrics for user approval, then fit preprocessing inside each of the same four chronological folds and compare candidates before any Optuna tuning.
  - Blockers: Stage 5 candidate models, evaluation metric priority, and final tuning candidate are not selected; no machine-learning model has been trained.

## Session log

- `session:20260814-1952`
  - Started: 2026-08-14T19:52+09:00
  - Last activity: 2026-08-14T20:21+09:00
  - Focus: Reformat the MVP plan and create an implementation checkpoint document without browsing embedded links.
  - Updated keys: `decision:mvp-scope`, `decision:implementation-checklist`, `convention:plan-source-preservation`, `handoff:current`
  - Summary: Reorganized the plan, then created a 13-stage implementation checklist with 449 tasks covering data, ML, finance diagnosis, recommendation, RAG, integration, deployment, and final acceptance.

- `session:20260814-2034`
  - Started: 2026-08-14T20:34+09:00
  - Last activity: 2026-08-15T00:06+09:00
  - Focus: Complete Stages 0-3 from project setup through chunk-based raw QA and a reproducible panel build.
  - Updated keys: `decision:stage0-stack`, `decision:solo-team-validation`, `decision:stage3-panel-contract`, `decision:stage4-persistent-target-structure`, `decision:stage4-cv-design`, `decision:stage5-model-selection-workflow`, `convention:user-owned-data-acquisition`, `convention:bounded-raw-inspection`, `convention:chronological-project-log`, `convention:mandatory-user-decision`, `convention:proportional-verification`, `issue:bounded-reader-full-file-call`, `issue:store-2025-header-language`, `handoff:current`
  - Summary: Completed Stages 2-4, fixed the persistent two-quarter decline threshold at 10%, created and verified development/Fold/locked-test Feature artifacts without exposing locked labels, and left Stage 5 model and metric choices undecided.

## Session archive
