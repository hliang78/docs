# Device V2 Flexible Search Detailed Testing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add and run detailed regression tests for Device V2 flexible search across backend structured filters and frontend query-builder behavior.

**Architecture:** Backend tests exercise `GET /device/v2/list?filters=...` parsing plus `DeviceV2Srv.ListPage` filter semantics on in-memory projection data. Frontend Playwright tests seed deterministic Device V2 rows through authenticated API helpers, drive the real `/device/device-v2-management` query builder, and assert request payloads, active tags, results, reset behavior, and route handoff.

**Tech Stack:** Go testing, Gin httptest, SQLite/GORM projection tests, Vue 3, Ant Design Vue, Playwright, TypeScript.

---

## Task 1: Expand Backend Structured Filter Coverage

**Files:**
- Modify: `OneOps/app/device/v2/service/impl/device_v2_projection_test.go`
- Modify: `OneOps/app/device/v2/api/device_v2_migration_api_test.go`

- [x] Add service cases for attribute `exists`, label `contains`, metadata `eq`, root `prefix`, and legacy filter plus structured filter AND behavior.
- [x] Add service rejection cases for incomplete structured clauses, unsupported operator, unsafe JSON key, excessive `in` values, empty `in`, and missing scalar values.
- [x] Add API transport cases for invalid structured filter JSON and non-array filter shape.
- [x] Run:

```bash
cd OneOps
go test ./app/device/v2/api ./app/device/v2/service/impl -run 'TestList_.*Structured|TestDeviceV2Srv_ListPageStructured|TestDeviceV2Srv_ListPageRejectsInvalidStructured|TestDeviceV2Srv_ListPageLegacyAndStructured' -count=1
```

Result: PASS.

## Task 2: Add Frontend Flexible Search Playwright Coverage

**Files:**
- Create: `OneOps/scripts/platform2_multi_agent_test/agents/device_v2_flexible_search.spec.ts`
- Modify: `OneOps/scripts/platform2_multi_agent_test/package.json`

- [x] Seed three deterministic Device V2 records with distinct attributes, labels, and metadata.
- [x] Test multi-condition AND search: `root.code contains <code>` plus `metadata.owner = network-team`.
- [x] Test text fallback field: `in_band_ip contains 192.0.2.101`.
- [x] Test metadata search and active filter tags.
- [x] Test reset clears filters and sends a list request without `filters`.
- [x] Test route handoff `codes=<code>` remains a scope constraint when structured filters are present.
- [x] Test select-based monitor status serializes `root.monitor_status = done`.
- [x] Run:

```bash
cd OneOps/scripts/platform2_multi_agent_test
ONEOPS_UI_URL=http://127.0.0.1:3001 ONEOPS_API_URL=http://127.0.0.1:8280/api/v1 npm run test:device-v2:flexible-search
```

Result: PASS.

## Task 3: Full Verification Matrix

**Files:**
- Verify only.

- [x] Run TypeScript check for new Playwright files.
- [x] Run `npm run typecheck:d2`.
- [x] Run `go test ./app/device/v2/... -count=1`.
- [x] Run targeted `/app/platform` regression around Device V2 consumers.
- [x] Query for `E2E_D2_FLEX_` leftovers and confirm none remain.

## Self-Review

- Spec coverage target: backend structured parsing/validation/semantics plus frontend query builder, active filters, reset, and route handoff.
- Frontend label field selection depends on schema labels, so label `contains/exists` is covered at service level rather than UI level in this run.
- Placeholder scan: no TBD or unresolved commands.
- Type consistency: frontend tests use existing `device_v2_api.ts` helpers and `DeviceV2Seed` shape.
