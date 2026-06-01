# D2 BE Compact Context

UpdatedAt: 2026-05-13T20:30:00+0800
Owner: d2-be
Purpose: compact context pack for agent-loop turns. Prefer this file over broad doc reads.

## Current State

- Active scope: D2 redesign real production rollout backend contract gate.
- Latest BE result: D2BE-006 was revalidated; no FE code touched.
- PCRE blocker is fixed at the Go toolchain level:
  `go env -w CGO_CFLAGS=-I/opt/homebrew/include CGO_LDFLAGS=-L/opt/homebrew/lib`.
- Verification passed even with process env removed:
  `env -u CGO_CFLAGS -u CGO_LDFLAGS -u PKG_CONFIG_PATH go test ./app/device/v2/...`.
- OpenClaw global env now includes:
  `CGO_CFLAGS=-I/opt/homebrew/include`, `CGO_LDFLAGS=-L/opt/homebrew/lib`, `PKG_CONFIG_PATH=/opt/homebrew/lib/pkgconfig`.

## FE/Product Decisions Already Recorded

- Saved-view/source/collection/action contract decisions are recorded in `OneOPS-UI/docs/device-v2-ui-autodev/COORDINATION.md` under Operator Decisions.
- FE is approved to hide/disable unconfirmed filters/counts/actions rather than inventing backend behavior.
- `keyword` handoff is required.
- Upload is Excel-only; CSV is not confirmed.
- New D2 redesign rollout phases A-F are summarized in `/Users/huangliang/project/OneOPS-ALL/docs/openclaw-autodev/context/d2-redesign-rollout.md`.
- Backend should verify real API contracts for ingest/import batch/management/store-collection and only implement concrete gaps required by FE rollout stories.

## Relevant BE Files

- `app/device/v2/**`
- `app/device/v2/ingest/**`
- `docs/device-v2-ui-autodev/D2BE-006_FIELD_CONTRACT.md`
- `/Users/huangliang/project/OneOPS-ALL/docs/openclaw-autodev/context/d2-redesign-rollout.md`
- `/Users/huangliang/project/OneOPS-ALL/docs/openclaw-autodev/D2_BACKEND_DEVICE_V2_INGEST_FIELD_AUDIT.md`
- `/Users/huangliang/project/OneOPS-ALL/docs/openclaw-autodev/evidence/d2-be/D2BE-006/summary.md`
- `/Users/huangliang/project/OneOPS-ALL/docs/openclaw-autodev/shared-d2.md`

## Read Budget

- Start from this context, current handoff, and last report.
- Read `d2-redesign-rollout.md` before the full redesign guide. Open the full guide only for a precise missing detail.
- For Go source, use failing test output or `rg` first, then read at most 160 nearby lines.
- If the task is environment-only, verify env/test behavior and update evidence; do not browse unrelated packages.
- Do not read full FE coordination docs unless the context pack says a precise section is stale.
- Do not modify frontend code; record FE-facing contract answers in shared docs/evidence.

## Validation

- Primary deterministic gate: `go test ./app/device/v2/...`.
- If default test still misses `pcre.h`, report gateway/tool environment mismatch and include `go env CGO_CFLAGS CGO_LDFLAGS PKG_CONFIG_PATH GOENV`.
