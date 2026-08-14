# Agent Memory

> Codex-maintained project memory. Verify time-sensitive facts against the
> current workspace.

## Project snapshot

- Last updated: 2026-08-14T21:14+09:00
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
  - Updated: 2026-08-14T21:14+09:00
  - Status: active
  - Content: This is a one-person project; Stage 0 team-scope confirmation is the user's own review, and separate-environment verification may use a clean virtual environment on the same machine.
  - Evidence: User clarification on 2026-08-14 and `scripts/verify_stage0.ps1`.

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

## Known issues and fixes

## Current handoff

- `handoff:current`
  - Updated: 2026-08-14T21:14+09:00
  - Current state: Stage 0 structure, pinned environment, central settings, secret handling, minimal FastAPI app, and automated verification are implemented; `scripts/verify_stage0.ps1` passes 8 tests.
  - Next step: The user should self-confirm the frozen scope and run `scripts/verify_stage0.ps1` in a clean virtual environment; data work starts only after the user supplies data.
  - Blockers: Previously downloaded ZIPs, extracted copies, Stage 1 reports, and the audit script remain because irreversible deletion was not approved; they are excluded from current work.

## Session log

- `session:20260814-1952`
  - Started: 2026-08-14T19:52+09:00
  - Last activity: 2026-08-14T20:21+09:00
  - Focus: Reformat the MVP plan and create an implementation checkpoint document without browsing embedded links.
  - Updated keys: `decision:mvp-scope`, `decision:implementation-checklist`, `convention:plan-source-preservation`, `handoff:current`
  - Summary: Reorganized the plan, then created a 13-stage implementation checklist with 449 tasks covering data, ML, finance diagnosis, recommendation, RAG, integration, deployment, and final acceptance.

- `session:20260814-2034`
  - Started: 2026-08-14T20:34+09:00
  - Last activity: 2026-08-14T21:14+09:00
  - Focus: Execute the MVP checklist from Stage 0 and leave evidence-backed progress for Stage 1.
  - Updated keys: `decision:stage0-stack`, `decision:solo-team-validation`, `convention:user-owned-data-acquisition`, `handoff:current`
  - Summary: Completed and verified the Stage 0 technical foundation, excluded data preparation, and adapted the remaining confirmation gates for a one-person team using self-review plus a clean virtual environment.

## Session archive
