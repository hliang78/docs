# Device V2 Flexible Search Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement multi-condition AND search for the Device V2 management page with dropdown-aware field/value controls.

**Architecture:** Add a structured `filters` JSON query parameter to the existing Device V2 list endpoint. The backend validates and applies clauses against root columns plus first-level `attributes`, `labels`, and `metadata` JSON keys; the frontend replaces the fixed legacy query form with a condition builder that derives field options from schema and existing option sources.

**Tech Stack:** Go, Gin, GORM, Vue 3, TypeScript, Ant Design Vue.

---

## File Structure

- `OneOps/app/device/v2/dto/device_v2.go`: add structured filter clause DTO fields.
- `OneOps/app/device/v2/api/device_v2.go`: parse `filters` JSON from query and pass clauses to service filter.
- `OneOps/app/device/v2/service/impl/device_v2_minimal_read.go`: validate and apply structured clauses.
- `OneOps/app/device/v2/service/impl/device_v2_projection_test.go`: cover service-level structured filter behavior.
- `OneOps/app/device/v2/api/device_v2_migration_api_test.go`: cover API parsing and validation.
- `OneOPS-UI/src/api/device/device-v2.ts`: add filter clause types and serialize `filters`.
- `OneOPS-UI/src/views/device/DeviceV2ManagementGrouped.vue`: replace legacy query state/UI with structured condition rows, dropdown adaptation, active tags, reset/query flow.

## Tasks

### Task 1: Backend DTO and Service Tests

**Files:**
- Modify: `OneOps/app/device/v2/dto/device_v2.go`
- Modify: `OneOps/app/device/v2/service/impl/device_v2_projection_test.go`

- [ ] Add `DeviceV2FilterClause` and `FiltersJSON` fields to DTOs.
- [ ] Add failing service tests for multiple structured clauses, metadata contains, root contains, `in`, `exists`, and invalid keys.
- [ ] Run: `go test ./app/device/v2/service/impl -run 'TestDeviceV2SrvListPageFilters|TestDeviceV2SrvListPageStructuredFilters' -count=1`
- [ ] Expected before implementation: tests fail because structured clauses are not applied.

### Task 2: Backend Structured Filter Implementation

**Files:**
- Modify: `OneOps/app/device/v2/service/impl/device_v2_minimal_read.go`
- Modify: `OneOps/app/device/v2/api/device_v2.go`

- [ ] Implement safe clause validation for source/operator/key/value shape.
- [ ] Implement root allowlist mapping for `code`, `name`, `status`, and `manage_status`.
- [ ] Implement JSON source filtering for `attributes`, `labels`, and `metadata`.
- [ ] Parse URL query `filters` JSON in API and attach it to `DeviceV2Filter`.
- [ ] Run backend service tests and API migration tests.

### Task 3: Frontend API Contract

**Files:**
- Modify: `OneOPS-UI/src/api/device/device-v2.ts`

- [ ] Add `DeviceV2FilterClauseSource`, `DeviceV2FilterOperator`, and `DeviceV2FilterClause`.
- [ ] Add optional `filters?: DeviceV2FilterClause[]` to `DeviceV2ListReq`.
- [ ] Serialize non-empty `filters` as JSON through `URLSearchParams`.
- [ ] Run TypeScript check after the page implementation.

### Task 4: Frontend Condition Builder

**Files:**
- Modify: `OneOPS-UI/src/views/device/DeviceV2ManagementGrouped.vue`

- [ ] Replace fixed legacy query fields with condition rows.
- [ ] Build a field catalog from root fields, schema attributes, schema labels, known metadata keys, and existing option sources.
- [ ] Choose value controls by field: select for enum/status/boolean/location/platform/catalog/credential fields with options, text input for free-form fields.
- [ ] Keep monitor quick filters and handoff `codes` behavior.
- [ ] Render active structured filter tags.
- [ ] Reset clears monitor state and all condition rows.

### Task 5: Verification

**Files:**
- Verify code repositories only; no production docs changes are required beyond this plan.

- [ ] Run backend targeted tests:
  `go test ./app/device/v2/service/impl -run 'TestDeviceV2SrvListPageFilters|TestDeviceV2SrvListPageStructuredFilters' -count=1`
- [ ] Run backend API targeted tests:
  `go test ./app/device/v2/api -run 'TestDeviceV2APIList|TestDeviceV2Migration' -count=1`
- [ ] Run frontend type check:
  `npm run typecheck:d2`
- [ ] Inspect `git diff -- OneOps OneOPS-UI` from the top-level workspace.

## Self-Review

- Spec coverage: multi-condition AND, dropdown preference, root/attributes/labels/metadata, compatibility, safety validation, active tags, and route handoff are covered.
- Placeholder scan: no placeholder work items; each task names files and commands.
- Type consistency: frontend and backend both use `source`, `key`, `operator`, and `value`.
