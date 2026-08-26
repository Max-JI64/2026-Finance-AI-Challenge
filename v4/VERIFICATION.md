# V4 verification

- Verified: 2026-08-24T16:07+09:00
- Runtime: regular CPython 3.13
- Local URL: `http://127.0.0.1:8002`
- API version: `v4-api-v1.0`

## Passed gates

- V3 source inventory copied with immediate equality 10/10; baseline recorded in `V3_COPY_BASELINE_SHA256.md`.
- V3 source hashes remain unchanged 10/10 after V4 implementation.
- `git diff --name-only -- app src v3` is empty; V2, shared engines, and V3 were not edited.
- V4 and V3 focused regressions: 24/24 passed.
- JavaScript syntax: `app.js` and `v4-extension.js` passed `node --check`.
- Python syntax: `main.py`, `orchestrator.py`, `copilot.py`, and `test_v4.py` passed compilation.
- Whitespace: `git diff --check -- v4` passed.
- Live HTTP: `/health`, `/`, `/static/v4-extension.js`, and the preserved transaction CSV template returned 200.
- Existing RE9 fixed-persona oracle remains 8/8 and its prohibited-positive-claim list remains empty.

## Full-suite note

The complete suite produced 167 passes and one failure. The failure is the preserved RE9 Manifest hash test: three documents intentionally changed after the archived RE9 package (`reports/re_stage8_3/service_review_log.md`, `프로젝트 계획서.md`, and `MVP 단계별 구현 체크리스트.md`). The V4-focused and V3 regression sets pass completely. The archived Manifest was not rewritten and the later documents were not reverted.

## User-owned checks

- Final visual approval
- Mobile and keyboard presentation review
- Five-stage rehearsal with the selected contest persona

## User screen-review revision — 2026-08-24T16:18+09:00

- Removed the finance-sentence paste UI, local structured-input parser, and `/api/v4/input/structure`; the removed endpoint returns 404.
- Preserved the separate transaction and optional-loan CSV flow.
- Screenshot inspection found that the shared full-width `input` rule stretched the no-loan checkbox and forced its label into a narrow wrapped column.
- Moved the control into the loan-card heading and fixed its checkbox to 18×18px inside a compact selection chip.
- V4 and V3 focused regressions remain 24/24 and JavaScript syntax passes.
- The in-app browser automation connection failed because its local plugin asset path was unavailable, so post-change verification covered HTTP, DOM, CSS, API removal, and tests; final visual confirmation remains user-owned.

## Presentation preset unit revision — 2026-08-24T16:25+09:00

- Confirmed all five presentation presets define monthly revenue in 만원: `cash-rich` 1,680–1,800, `stable` 1,180–1,210, `sales-down` 700–1,000, `high-fixed` 1,000–1,100, and `debt-heavy` 1,100–1,200.
- Fixed the shared V4 session path that converted revenue inputs to won before saving and then restored those won values into fields labeled 만원.
- Advanced the session key to `buttimaiv4:session:v2`, so the earlier malformed tab snapshot is not restored after refresh.
- The input ledger now shows one row per month with its corresponding 만원 amount instead of one concatenated value string.
- Input-ledger plausibility warnings now compare monthly costs and average revenue in the same 만원 unit.
- V4 and V3 focused regressions pass 25/25; JavaScript syntax, whitespace, and live static-asset checks pass.

## What-if comparison copy revision — 2026-08-24T17:40+09:00

- The previous heading inserted the currently selected alternative label, producing `무대응의 결과 차이` when the baseline alternative was selected.
- This was technically the same alternative's before-and-after calculation, but the heading could be read as a comparison between two different no-action strategies.
- Replaced it with `현재 입력과 가정 적용 후 결과` and added a direct explanation that the left value is the current calculation and the right value is the temporary calculation after applying the assumption.

## Decision-page comparison grouping — 2026-08-24T17:46+09:00

- Kept policy selection on step 4 because step 5 already owns the application-preparation workflow; adding another selection page would duplicate navigation.
- Moved `모든 수치 한 번에 보기` inside the 13-week comparison chart panel and styled it as an internal divider instead of a separate card.
- Moved the application-policy launcher directly below the chart panel, producing the order: alternative cards, chart and detailed figures, application-policy selection, policy chat.
- V4 and V3 focused regressions pass 25/25; JavaScript syntax, whitespace, live DOM order, and versioned CSS delivery pass.

## Preparation-page contrast revision — 2026-08-24T17:51+09:00

- Removed light-theme-only backgrounds from the current-action card, completed and held tasks, and local draft output.
- Replaced undefined `--primary` and `--ink` tokens and other V4-only state colors with the shared semantic theme tokens.
- Empty draft output is hidden until a draft exists.
- Dark-theme contrast ratios are 12.26:1 for the current action, 11.81:1 for completed tasks, 11.57:1 for held tasks, and 13.28:1 for draft output.
- The explanatory document-sample copy proposed during review was reverted at the user's request; the feature rationale remains conversation-only.
- V4 and V3 focused regressions pass 25/25; JavaScript syntax, whitespace, versioned live CSS, and absence of undefined V4 color tokens pass.

## Reviewed document sample removal — 2026-08-24T18:06+09:00

- Removed the reviewed document-sample panel, sample-field checkboxes, sample loader, and related CSS.
- Removed `verifiedFields` from V4 client state and session snapshots.
- Removed the document-value confirmation task from the deterministic application plan.
- Simplified the inquiry draft contract to the user-entered question only; the removed `verified_fields` field now fails closed with HTTP 422.
- Updated the implementation plan to exclude the sample workflow until a real, approved document-processing path exists.
- V4 and V3 focused regressions pass 25/25; live health and the remaining draft endpoint return 200, removed UI and JavaScript are absent, and the old draft contract returns 422.

## Selected-policy graph and application route — 2026-08-24T19:15+09:00

- Added a conditional stability-voucher curve using up to 250,000 won of the user's monthly other fixed cost as a reviewed eligible-cost reduction. It creates no debt and remains outside recommendation rankings.
- Refinance previews now calculate the actual remaining principal immediately before the assumed four-week execution date, cap the refinanced segment at 50,000,000 won, and validate that the payoff does not exceed that execution-date balance.
- Preserved structural eligibility blocks: a structurally excluded policy receives no invented curve and instead exposes the failed condition, current answer, resolution direction, and answer-edit action.
- Reordered step 4 to comparison chart and detailed figures, policy-specific conditions and graph explanation, then the step-5 application launcher. Each policy journey card also links directly to step 5.
- The live three-policy request returns `dynamic_pol_semas_stability_voucher_2026`, `conditional_pol_semas_refinance_2026`, and `conditional_pol_semas_rechallenge_2026`; all three are conditional and ranking-ineligible. Voucher support is 250,000 won, refinance net new borrowing is 0, and all three readiness records report an available graph for the tested case.
- Policy Event, V4, V3, and shared integration regressions pass 93/93. Both V4 JavaScript files pass `node --check`; the refreshed service is healthy on `127.0.0.1:8002` under PID 21160.
- In-app browser automation remains unavailable because its local plugin asset path cannot be initialized. Live HTTP, API, DOM-order, source-contract, and test checks passed; final visual confirmation remains user-owned.

## Judge-focused comparison and preparation flow — 2026-08-25T23:01+09:00

- Reduced step 4 to an optional collapsed What-if, the no-action versus selected-policy graph, a policy-by-policy no-action delta strip, and one focused policy summary with three metrics and one step-5 action.
- Added policy tabs and manual previous/next controls. The comparison chart now renders only no action and the conditional alternatives mapped to the user's selected policies.
- Moved structural and remediable blockers, current answers, answer editing, official preparation tasks, local inquiry drafting, and policy-scoped chat to step 5.
- Targeted answer editing now recalculates and returns to the same policy's step-5 preparation screen instead of searching for the removed step-4 journey card.
- Removed the goal-card grid, ranking notice, alternative-card grid, all-values table, per-policy mini charts, policy detail dialog, action brief, duplicate action plan, stacked application launcher, and presentation-only policy-change panel.
- Removed the reviewed-document-sample capability from the health contract; `/health` now reports `application_document_upload: not_supported`.
- `node --check` passed for both V4 JavaScript files. Literal `byId` references all resolve to current HTML IDs, and obsolete feature identifiers are absent.
- Shared policy integration and V4 focused tests passed 67/67. Live `/health` and `/` returned 200, the four new page markers were present, and the service is running at `127.0.0.1:8002` under PID 1904.
- In-app browser control could not initialize its local runtime, so the final visual and presentation acceptance remains user-owned.

## Structured preparation tasks and provenance — 2026-08-26T10:28+09:00

- Replaced the flat `items_to_confirm` application-plan request with structured Rule results, editable conditions, preparation items, official checks, and remediable actions.
- Unknown Rule results now use their official condition as the task title. The generic internal reason `입력값이 없어 확인이 필요합니다.` is filtered from user-facing tasks.
- Rechallenge `general_any`, `hope`, and `leap_all` Rules are grouped into one `신청 가능한 재도전 자격경로 확인` task, so alternative paths are not presented as simultaneous mandatory work.
- Replaced the hardcoded `기존 Rule 결과` label with task-specific confirmation grounds: official notice, official eligibility conditions, user answer plus notice condition, official institution, user question, or official application screen.
- Notice-based tasks expose an `공고 열기` action. Task IDs are policy-scoped, and the client submits only the current policy's completion and hold state.
- `v4/tests/test_v4.py` passed 13/13 with regular CPython 3.13. `node --check v4/static/v4-extension.js` and `git diff --check -- v4` passed.
- Restarted the live V4 service under PID 1332. `/health`, `/`, and `/api/v4/application/plan` returned HTTP 200; the root serves `v4-extension.css?v=v4-007` and `v4-extension.js?v=v4-004`.
- A live rechallenge plan returned exactly one alternative-route task plus a separate availability check, with no generic missing-input title and no `기존 Rule 결과` source. Final rendered-layout acceptance remains user-owned.

## Independent task controls — 2026-08-26T10:42+09:00

- Removed the completion and hold controls from the top `지금 할 한 가지` summary. It now only identifies the next suggested pending task.
- Added independent complete and hold controls to every task card. Repeating the active control returns that task to pending, so users can correct completion state without following a forced sequence.
- Updated the delegated task handler to address a specific policy-scoped task ID instead of always mutating `next_task`.
- V4 tests passed 13/13 with regular CPython 3.13. JavaScript syntax and scoped whitespace checks passed.
- Restarted V4 under PID 25344. Live `/health`, `/`, and versioned JavaScript returned HTTP 200; the root serves `v4-extension.css?v=v4-008` and `v4-extension.js?v=v4-005`, contains no top task-control IDs, and the served JavaScript contains both per-card controls.
- Current completion still records status only in browser session storage. It does not record a confirmation value, read the stored notice, or call Luna; this separate product-scope decision remains with the user.

## Stored-notice evidence, confirmation records, and inquiry generation — 2026-08-26T11:09+09:00

- Replaced per-card complete and hold buttons with a required confirmation record containing result, confirmation route, confirmation date, and memo. `확인 완료` and `해당 없음` count as complete; `기관 문의 필요` stays held and becomes an inquiry target.
- Added deterministic, policy/version-filtered BM25 retrieval from the existing local SQLite notice database to every preparation task. Each matching task exposes the stored section, excerpt, source URL, and retrieval date.
- Added an explicit warning that stored evidence does not establish current application status or remaining budget. Mutable status tasks still require a user check against the official notice or institution.
- Removed the unconditional `기관 문의문 초안 검토` task and the free-form draft-question field. The draft endpoint now accepts only task records explicitly marked `기관 문의 필요` and generates one local inquiry containing those items.
- Added optional Luna wording behind a dedicated checkbox. It receives unresolved task titles and stored official excerpts only, never confirmation memos; no consent, missing API configuration, call failure, or rejected output returns the local template.
- Advanced the tab-session contract to `buttimaiv4:session:v3`, preserving policy-scoped confirmation records rather than bare completion/hold IDs.
- V4 tests passed 15/15 with regular CPython 3.13. Both V4 JavaScript files passed `node --check`, and `git diff --check -- v4` passed.
- Restarted V4 under regular Python 3.13 PID 17080. Live `/health`, `/`, versioned JavaScript, policy catalog, application plan, and local inquiry draft returned HTTP 200.
- A live rechallenge application plan returned three tasks and stored-notice evidence for all three. A `needs_inquiry` confirmation record returned held status with its date intact, and the local draft contained exactly that unresolved task with `external_ai_used=false`.
- The root now serves `v4-extension.css?v=v4-009` and `v4-extension.js?v=v4-006`. Final rendered-layout and presentation acceptance remain user-owned.

## Selected-policy full-notice Luna extraction — 2026-08-26T12:10+09:00

- Step 4's selected policies are the extraction scope. Entering step 5 sends the complete stored notice set for each of the selected maximum three policies to Luna in separate parallel requests, preventing cross-policy field mixing.
- Only public stored-notice chunks are transmitted. Store identity, financial inputs, eligibility answers, deterministic calculations, and confirmation records or memos are excluded from the Luna payload.
- The strict structured output contains only publication date, application period, application path, financing or support terms, required documents, and contact. Every found field must cite an existing chunk and a source quote; numeric tokens must be present in that field's cited evidence.
- OCR whitespace restoration is accepted during quote matching, but changed letters or numbers are not. A field that fails evidence validation becomes a direct-confirmation field without discarding other verified fields.
- Failed or unavailable results are retried on the next entry; only completed policy/version results remain in the client cache. The root serves `v4-extension.js?v=v4-010`.
- Regular CPython 3.13 V4 regressions pass 20/20. `node --check` passes for `v4/static/app.js` and `v4/static/v4-extension.js`.
- Live browser testing selected rechallenge, refinance, and stability voucher together. The page showed `선택한 3개 정책의 저장 공고 전체를 분석하고 있습니다`, and the server logged three HTTP 200 notice-extraction requests.
- Rechallenge and refinance each analyzed all 109 stored chunks. Stability voucher analyzed all 56 stored chunks and displayed verified publication date, application period, application path, support terms, required documents, and contact with per-field evidence.
- `/health` and `/` return HTTP 200. Regular Python 3.13 PID 18480 listens on `127.0.0.1:8002`.
- Browser automation verified the interaction and rendered DOM content. Final visual composition and presentation acceptance remain user-owned.

## Notice-field simplification and inquiry-button feedback — 2026-08-26T15:35+09:00

- Removed every per-field `추출 근거 n건 보기` disclosure and its raw quote/source rendering from the Luna notice-result cards. Chunk identity, quote support, and numeric-token validation remain enforced internally by the server.
- Updated the notice guide and official-notice task copy so the user is asked to review the structured fields rather than inspect raw extraction evidence.
- The inquiry-draft button is no longer disabled when zero tasks are marked `기관 문의 필요`. Clicking it now scrolls to and focuses the first pending task's result selector and displays the exact required action.
- The existing inquiry scope is unchanged: only saved `needs_inquiry` records are submitted to the draft endpoint. During a valid request the button is temporarily disabled to prevent duplicates, and failures now show a visible retry message.
- Regular CPython 3.13 V4 regressions pass 20/20. Both V4 JavaScript files pass `node --check`, and `git diff --check -- v4` passes.
- Live `/health`, `/`, and `v4-extension.js?v=v4-011` return HTTP 200. Browser verification found zero extraction-evidence toggles, an enabled draft button, focus on the first result selector after an empty click, and the expected guidance toast.
- Regular Python 3.13 PID 5404 listens on `127.0.0.1:8002`. Final visual composition and presentation acceptance remain user-owned.

## Single notice-confirmation task and automatic graph selection — 2026-08-26T16:00+09:00

- Removed the manual conditional-graph enable/remove button from policy cards. Selected policies with supported conditional calculations continue to be enabled automatically before comparison; deterministic scenario calculations and ranking exclusion are unchanged.
- Reduced the step-5 application plan to one task: `AI가 정리한 공고 핵심정보 확인`. The API no longer creates separate cards from raw Rule operands, previously entered answers, generic representative/status/budget checks, or a placeholder final review.
- Kept Rule and answer interpretation in the existing top condition panel. Its clear state now says that the entered answers do not match an exclusion condition, while explicitly withholding any claim about unasked conditions or official review.
- Confirmation result, route, and date remain required; the confirmation memo is optional in both the API schema and the browser form. Inquiry drafts omit the memo line when it is empty.
- Regular CPython 3.13 V4 regressions pass 21/21. Shared policy integration plus V4 regressions pass 76/76. Both V4 JavaScript files pass `node --check`, and `git diff --check -- v4` passes.
- Live `/health` and `/` return HTTP 200, the root references `v4-013`, and a live plan request containing noisy Rule and official-check inputs returns exactly one official-notice task. Regular Python 3.13 PID 26660 listens on `127.0.0.1:8002`.
- Browser and visual verification were intentionally not performed for this change at the user's request. Final visual and presentation acceptance remain user-owned.

## Persistent notice cache, field confirmations, and inquiry removal — 2026-08-26T16:31+09:00

- The complete public notice still comes from the existing `rag/index/policy_re8.sqlite3` `policy_chunks` table. The new `v4/runtime/notice_extraction_cache.sqlite` stores only completed, source-validated Luna extraction responses; it is not a second notice source.
- Persistent cache identity includes policy ID, policy version, complete-notice content digest, model, and extraction-schema version. A changed notice therefore misses the old cache automatically, while `공고 다시 분석` sends `force_refresh=true`.
- Cache reads survive server-process memory loss. Cache-write failure is non-fatal: a successfully validated Luna result is returned to the user and can be analyzed again later.
- Replaced the single `1 / 1` preparation progress and task card with independent confirmation buttons on each extracted field. Confirmation state is browser-session-only and includes the source digest, preventing stale confirmation reuse after a notice change.
- Removed the institution-inquiry draft panel, checkbox, client handler, local/Luna draft generation code, `/api/v4/application/plan`, and `/api/v4/application/draft`. Both removed routes return HTTP 404.
- Regular CPython 3.13 V4 regressions pass 16/16. Shared policy integration plus V4 regressions pass 71/71. Both V4 JavaScript files pass `node --check`, and `git diff --check -- v4` passes.
- The live root returns HTTP 200 and references `v4-014`; `/health` reports `notice_extraction_cache: local_persistent_public_notice_only`. The persistent cache currently contains one extraction row for one policy.
- After the final restart, the same 109-chunk rechallenge notice returned `analysis_status=completed` and `cache_status=persistent`, proving disk-cache reuse with an empty process-memory cache.
- Regular Python 3.13 PID 3880 listens on `127.0.0.1:8002`. Browser and visual verification were not performed; final visual acceptance remains user-owned.
