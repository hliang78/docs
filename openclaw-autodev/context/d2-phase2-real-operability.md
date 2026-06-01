# D2 Phase 2 Real Operability Gate

Updated: 2026-05-15

## Why Phase 2 Exists

D2 first-phase closure proved that the redesigned pages can be opened, logged into, typechecked, and lightly smoke-tested against a local backend. It did not prove that the pages are truly usable for day-to-day D2 work.

The current D2 state must be treated as "reachability complete, operability incomplete" until Phase 2 evidence proves otherwise.

## Current Evidence Gap

- `npm run smoke:d2-redesign-browser` logs in with `admin/admin@123`, opens the management page, clicks a refresh button, opens the ingest page, checks the upload `accept` attribute, clicks a refresh-like button, and captures screenshots.
- The smoke evidence does not perform a real business flow: create device, edit device, delete device, manual ingest submit, Excel import batch upload, validate, apply, retry, handoff to management, store/start, task drawer verification, observations, collection plans, or DC2 evidence.
- The latest go-live closure evidence shows the management page with zero devices and many disabled or pending-contract controls. This is not sufficient for real operability.
- `DeviceV2ManagementRedesign.vue` and `DeviceV2IngestPipelineRedesign.vue` are both large monolithic files. Future work should prefer small, testable helpers/composables/components when touching behavior.

## Hard Rules For Phase 2

- Do not close a D2 Phase 2 story using only screenshots, HTTP 200, page title checks, typecheck, or refresh-button evidence.
- Do not add fallback branches, mock data, pseudo-success, swallowed errors, or silent defaults for missing backend capability.
- Do not infer missing product behavior. If the backend contract, enum meaning, route semantics, destructive action boundary, tenant/auth meaning, or old-code behavior boundary is unclear, return `LoopControl: BLOCKED` with the exact question.
- D2/device-related old frontend/backend code may be modified only when existing old-code behavior is preserved. Any behavior change still requires explicit approval.
- Every visible enabled operation must be backed by one of: real API response, user input, deterministic validation result, or explicit business-empty state.
- Every disabled visible operation must have a tracked contract/product blocker or be removed from the production path.

## Required Real Operation Chain

Phase 2 must build deterministic evidence for this chain, using local backend from `/Users/huangliang/project/OneOPS-ALL/OneOPS` and frontend from `/Users/huangliang/project/OneOPS-ALL/OneOPS-UI`:

1. Login with `admin/admin@123`.
2. Management list loads with real `/api/v1/device/v2/list` network evidence.
3. Create a namespaced test device record through the UI and verify it appears in the list and detail rail.
4. Edit the same device through the UI and verify the persisted detail reload.
5. Delete or clean up the same namespaced test device through the UI; if deletion is not permitted by backend policy, record the exact backend error and provide a non-destructive cleanup policy.
6. Submit a manual ingest draft and verify task detail, stages, execution summary, execution rows, and management handoff query.
7. Exercise import batch create, Excel upload, validate, apply, retry-failed-records where backend contracts allow it; otherwise record exact blocker.
8. Start store collection for an eligible namespaced device, open the task evidence drawer, and verify task summary, runs, observations, collection plans, and latest DC2 evidence or explicit backend empty/error state.
9. Produce compact network, console, screenshot, and text evidence under `docs/openclaw-autodev/evidence/d2-fe/`.

## Backend Phase 2 Evidence

- 2026-05-15 `D2P2-FE-005-STORE-EVIDENCE-OPERABILITY`: `D2_CHROME_PORT=9226 npm run smoke:d2-real-ops` passed against local backend/frontend and recorded the full real-operation chain at `docs/openclaw-autodev/evidence/d2-fe/D2P2-FE-005-STORE-EVIDENCE-OPERABILITY/20260514-193949-real-operation-harness.md` (JSON sibling has full network/console/page proof). Earlier passing evidence includes `20260514-192725-real-operation-harness.md`, `20260514-192535-real-operation-harness.md`, `20260514-191614-real-operation-harness.md`, `20260514-190244-real-operation-harness.md`, `20260514-190021-real-operation-harness.md`, `20260514-184947-real-operation-harness.md`, `20260514-175438-real-operation-harness.md`, `20260514-175226-real-operation-harness.md`, `20260514-175038-real-operation-harness.md`, `20260514-173145-real-operation-harness.md`, `20260514-172049-real-operation-harness.md`, `20260514-171840-real-operation-harness.md`, `20260514-171629-real-operation-harness.md`, `20260514-165138-real-operation-harness.md`, `20260514-164931-real-operation-harness.md`, `20260514-164713-real-operation-harness.md`, `20260514-164428-real-operation-harness.md`, `20260514-162856-real-operation-harness.md`, `20260514-162642-real-operation-harness.md`, `20260514-160732-real-operation-harness.md`, `20260514-160511-real-operation-harness.md`, `20260514-155420-real-operation-harness.md`, `20260514-152117-real-operation-harness.md`, `20260514-151717-real-operation-harness.md`, `20260514-151321-real-operation-harness.md`, and `20260514-144529-real-operation-harness.md`.
- 2026-05-14 `D2P2-BE-001-REAL-OPS-CONTRACT-FIXTURE`: backend contract map for list/get/create/update/delete, manual ingest submit/detail/upload, import batch lifecycle, store start/retry/detail/summary/runs/observations/collection-plans, and latest DC2 is recorded at `docs/openclaw-autodev/evidence/d2-be/D2P2-BE-001-REAL-OPS-CONTRACT-FIXTURE/summary.md`.
- Deterministic FE smoke fixture policy: prefix exact codes/batches with `D2P2_SMOKE_YYYYMMDD_HHMMSS_`, namespace metadata `openclaw/d2p2/smoke`, create with `base_ref_mode=warn`, and clean up only the exact created device code with `DELETE /api/v1/device/v2/:code`. Import batch purge remains destructive and needs separate approval outside local-only cleanup.
- Validation: `go test ./app/device/...` and `go test ./app/device/v2/...` pass after a behavior-preserving old-code vet fix in `app/device/validator/result.go` (`fmt.Errorf("%s", errorMsg)`).

## Backend Phase 2 Responsibilities

- Provide or verify contract tests for list/get/create/update/delete, ingest submit/task detail, import batches, store/start, task summary, runs, observations, collection plans, and latest DC2.
- Provide deterministic test fixture or cleanup guidance for FE real-operation smoke. Do not expose production-only destructive behavior without approval.
- If frontend needs facets, saved views, source distribution, change history status transitions, access/credential editing, or monitoring handoff, either implement the confirmed contract or block with the exact product/API question.

## Frontend Phase 2 Responsibilities

- Replace the current reachability smoke with a real-operation smoke. The old smoke can remain as a fast reachability check, but it is not a completion gate.
- Split new behavior into focused helpers/composables/components instead of expanding the existing monolithic Vue files whenever practical.
- Convert disabled controls into one of: real wired operation, hidden non-production affordance, or tracked explicit blocker.
- Ensure UI operations expose backend failures directly and do not silently treat missing data as success.

## Completion Definition

D2 is not complete until the final Phase 2 story records:

- `npm run typecheck:d2` pass.
- Backend D2 tests pass for the relevant package paths.
- Real-operation browser smoke pass with evidence for the full operation chain above, or a precise `BLOCKED` item for each missing product/backend decision.
- No visible enabled D2 operation is fake, screenshot-only, or based on unverified page-local state.
