# D2 FE Compact Context

UpdatedAt: 2026-05-14T09:48:00+0800
Owner: d2-fe
Purpose: compact context pack for agent-loop turns. Prefer this file over broad doc reads.

## Current State

- Active scope: D2 redesign real production rollout from `D2_REDESIGN_AI_AUTODEV_GUIDE.md`.
- Latest FE baseline: DVR-007 validation completed, `npm run typecheck:d2` passed, browser policy was fixed, and no DVR-007 work remains.
- Current active story: `D2FE-UI-PRO-POLISH-002` Device V2 前端页面专业化视觉改造.
- 2026-05-14 unblock: operator supplied the missing `$impeccable` product/design context and task brief. `OneOPS-UI/docs/PRODUCT.md` and `OneOPS-UI/docs/DESIGN.md` now exist and are authoritative for this UI polish story. Treat the `DESIGN.md` "Confirmed Shape Brief For D2FE-UI-PRO-POLISH-002" section as the approved task-specific shape brief.
- 2026-05-14 split: `D2FE-UI-PRO-POLISH-002` was closed as a split parent after repeated turn-budget / PromptStuck exits. Continue only with the smaller follow-ups: `D2FE-UI-PRO-POLISH-002A` real-operation smoke timeout diagnosis, `002B` responsive evidence matrix, and `002C` closure summary.
- New rollout starts from phase A field-model foundation, then phases B/C/D/E/F.
- Runtime precheck: before browser validation, `scripts/openclaw-d2-runtime.sh ensure-backend` verifies or starts the backend with `cd /Users/huangliang/project/OneOPS-ALL/OneOPS && go run main.go`; Vite proxies `/api` to `http://127.0.0.1:8080`.
- Browser login for validation: username `admin`, password `admin@123`.
- Do not mark visible production behavior complete until page/network/console/interaction validation succeeds when the story changes UI behavior.
- Browser validation should use `npm run smoke:d2-redesign-browser` first. This deterministic CDP script starts/uses Vite on `127.0.0.1:3002`, launches Chrome with remote debugging, logs in with `admin/admin@123`, records management and ingest route page/network/console/interaction evidence, and writes evidence under `docs/openclaw-autodev/evidence/d2-fe/D2RED-F-GO-LIVE-CLOSURE/`.

## Operator Decisions

- Hide, disable, or relabel unconfirmed production controls/counts that are not backed by confirmed backend contracts.
- Do not derive production saved-view counts from only current-page rows.
- Unconfirmed management actions must not expose mock handlers, pseudo-success, fallback branches, swallowed errors, or silent defaults.
- `keyword` route query handoff is required and should pass through to `GET /api/v1/device/v2/list`.
- Upload is Excel-only for production: multipart field `excel`, template `device_v2_ingest_template.xlsx`. CSV is not confirmed/supported.
- Ingest enum handling follows `OneOPS/docs/device-v2-ui-autodev/D2BE-006_FIELD_CONTRACT.md`.

## Relevant FE Files

- `src/views/device/DeviceV2ManagementRedesign.vue`
- `src/views/device/DeviceV2IngestPipelineRedesign.vue`
- `src/views/device/device-v2-redesign/**`
- `src/views/device/device-v2-import/useDeviceV2IngestDraft.ts`
- `src/views/device/device-v2-import/draft-parser.ts`
- `src/api/device/device-v2.ts`
- `src/api/device/device-v2-ingest.ts`
- `src/api/device/device-v2-import.ts`
- `docs/device-v2-ui-autodev/COORDINATION.md`
- `/Users/huangliang/project/OneOPS-ALL/docs/openclaw-autodev/context/d2-redesign-rollout.md`
- `/Users/huangliang/project/OneOPS-ALL/docs/openclaw-autodev/D2_INGEST_BASE_FIELD_TABLE.md`
- `/Users/huangliang/project/OneOPS-ALL/docs/openclaw-autodev/evidence/d2-fe/DVR-007/summary.md`
- `docs/PRODUCT.md`
- `docs/DESIGN.md`

## Read Budget

- Start from this context, current handoff, and last report.
- For `D2FE-UI-PRO-POLISH-002`, load `$impeccable` context from `docs/PRODUCT.md` and `docs/DESIGN.md` before code edits. Do not re-block on missing PRODUCT/DESIGN unless the loader cannot read these files.
- Read `d2-redesign-rollout.md` before the full redesign guide. Open the full guide only for a precise missing detail.
- Use `rg` first, then read at most 160 nearby lines for a target symbol.
- Do not read entire Vue files in one call.
- Do not open full automation/runtime/backlog/checklist docs unless a specific story needs a line.
- Work only on the current story; do not start phases whose dependencies are not done.

## Validation

- Primary deterministic gate: `npm run typecheck:d2`.
- Backend runtime gate: `/Users/huangliang/project/OneOPS-ALL/scripts/openclaw-d2-runtime.sh ensure-backend`.
- Browser evidence gate: `npm run smoke:d2-redesign-browser`.
