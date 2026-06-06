# Firewall Platform Upgrade MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first OneOps firewall upgrade MVP by turning firewall configuration collection and snapshot confirmation into a platform asset loop connected to Device V2, task execution, readiness, and audit views.

**Architecture:** Keep the existing firewall module and Controller snapshot path. Add the smallest platform-facing layer around `FirewallNode`, `FirewallConfigSnapshot`, and task/runtime records so firewall facts become queryable assets and later policy tools can reuse the same baseline.

**Tech Stack:** Go, GORM/MySQL, existing OneOps firewall services, Device V2, platform task center, Controller firewall snapshot API, Vue/TypeScript UI.

---

## 1. MVP Principle

This MVP must prove one closed loop:

```text
Device/FirewallNode
  -> collect or upload config
  -> Controller generates FirewallConfigSnapshot
  -> OneOps compares against confirmed baseline
  -> user confirms or rejects baseline change
  -> snapshot becomes a versioned platform asset
  -> device/firewall detail shows latest readiness and snapshot status
  -> task/audit records show who did what and what changed
```

The MVP should not try to solve full firewall policy automation yet. The first release only makes firewall facts trustworthy, visible, versioned, and reusable.

## 2. MVP Scope

In scope:

1. Link `FirewallNode` more clearly to Device V2.
2. Version `FirewallConfigSnapshot` instead of treating it only as the latest node field.
3. Keep current upload/online-collection paths, but record each snapshot generation as a task-like operation.
4. Preserve current baseline confirmation semantics.
5. Add device/firewall summary views for latest snapshot, readiness, and baseline state.
6. Add a parent-level audit/report view for each collection or upload run.

Out of scope:

1. Full policy intent orchestration.
2. Automatic firewall policy changes.
3. AI auto-remediation.
4. Multi-vendor config translation.
5. Full historical diff UI.
6. Refactoring all firewall routers and services.
7. Replacing existing `SecurityPlanning.vue` in one pass.

## 3. Target User Story

As a network operator:

1. I select a firewall device or firewall node.
2. I upload or collect the running configuration.
3. OneOps generates a standardized `FirewallConfigSnapshot`.
4. OneOps tells me whether the snapshot is healthy and whether it differs materially from the confirmed baseline.
5. I confirm the new baseline if appropriate.
6. The firewall detail page shows the latest baseline, readiness, collection time, and important changes.
7. Policy validation, zone mapping, black/white list, and later automation can all reference the same confirmed snapshot.

## 4. Existing Capabilities To Reuse

Reuse these current foundations:

1. `OneOps/app/firewall/firewall_model/firewall_node.go`
   - Existing node fields, config text, config file object, associated device fields, readiness fields, edit lock fields.

2. `OneOps/app/firewall/service/impl/config_fact_snapshot.go`
   - Existing `FirewallConfigSnapshot` DTO.
   - Controller call to `/api/v1/firewall/config_snapshot`.
   - Baseline comparison and confirm-required error flow.

3. `OneOps/app/firewall/service/impl/firewall_online_collection.go`
   - Existing online SSH collection path.
   - Controller async execution integration.

4. `OneOps/app/firewall/FIREWALL_READINESS_LOCK_MINIMAL_PLAN.md`
   - Existing readiness and edit-lock semantics.

5. `OneOps/app/platform`
   - Existing task center, execution envelope, task logs, runtime artifacts.

6. `OneOps/app/device/v2`
   - Device V2 as the long-term asset entry.

## 5. MVP Data Additions

### 5.1 Firewall Snapshot Version

Add a table or model equivalent:

```text
firewall_config_snapshot_version
  id
  firewall_node_id
  firewall_node_code
  device_code
  source_type              upload | online_collect
  source_task_id
  source_file_object_name
  platform
  hostname
  fingerprint
  snapshot_json
  health_ok
  vendor_confidence
  needs_manual_review
  policy_count
  nat_count
  high_risk_diagnostics_count
  skipped_policy_count
  skipped_nat_count
  baseline_status          pending | confirmed | rejected | superseded
  diff_summary_json
  confirmed_by
  confirmed_at
  created_at
  updated_at
```

MVP rule:

1. `firewall_node.config_fact_snapshot` may remain the fast latest confirmed snapshot field.
2. The new table is the historical record and audit anchor.
3. Only confirmed snapshots should drive planning, mapping, and policy checks by default.

### 5.2 Firewall Operation Run

Use existing platform task records where possible. If the action is not yet routed through task center, write a minimal operation record:

```text
firewall_operation_run
  id
  operation_type           upload_config | collect_online | confirm_baseline
  firewall_node_id
  firewall_node_code
  device_code
  task_id
  status
  started_at
  finished_at
  operator
  summary_json
  error_message
```

MVP rule:

1. Prefer `platform_task` if the operation already has task context.
2. Use this lightweight table only for firewall-specific actions that are currently synchronous API calls.

## 6. API Plan

### 6.1 Snapshot History

Add:

```http
GET /api/v1/firewall/planning/firewall-node/:id/config-snapshots
```

Returns:

```json
{
  "latest_confirmed": {},
  "latest_pending": {},
  "list": []
}
```

### 6.2 Snapshot Confirmation

Add or standardize:

```http
POST /api/v1/firewall/planning/firewall-node/:id/config-snapshots/:snapshot_id/confirm
POST /api/v1/firewall/planning/firewall-node/:id/config-snapshots/:snapshot_id/reject
```

Confirm behavior:

1. Mark selected snapshot as `confirmed`.
2. Mark previous confirmed snapshot as `superseded`.
3. Update `firewall_node.config_fact_snapshot`.
4. Recalculate readiness or mark readiness as `stale`, depending on existing lock semantics.

Reject behavior:

1. Mark selected snapshot as `rejected`.
2. Do not update `firewall_node.config_fact_snapshot`.
3. Keep current planning facts unchanged.

### 6.3 Firewall Asset Summary

Add:

```http
GET /api/v1/firewall/planning/firewall-node/:id/platform-summary
```

Returns:

```json
{
  "firewall_node_code": "FW001",
  "device_code": "DEV001",
  "platform": "fortinet",
  "readiness_status": "ready",
  "edit_lock_status": "locked",
  "latest_confirmed_snapshot": {
    "snapshot_id": "snap-001",
    "created_at": "2026-06-06T10:00:00Z",
    "fingerprint": "sha256:..."
  },
  "latest_operation": {
    "operation_type": "collect_online",
    "status": "completed",
    "task_id": "task-001"
  }
}
```

## 7. Backend Tasks

### Task 1: Snapshot Version Model And Migration

**Files:**
- Create: `OneOps/migrations/add_firewall_config_snapshot_versions_20260606.sql`
- Create: `OneOps/app/firewall/firewall_model/config_snapshot_version.go`
- Modify: `OneOps/cmd/gen/mysql/gen.go`

- [ ] Add `firewall_config_snapshot_version` migration with fields listed in section 5.1.
- [ ] Add GORM model using existing `commonModel.Common`.
- [ ] Register model in code generation list.
- [ ] Add a focused model test if the repo has existing model-level test conventions.

Verification:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
go test ./app/firewall/firewall_model
```

Expected: package passes or reports no test files.

### Task 2: Snapshot Version Repository/Service

**Files:**
- Create: `OneOps/app/firewall/service/i_config_snapshot_version.go`
- Create: `OneOps/app/firewall/service/impl/config_snapshot_version.go`
- Test: `OneOps/app/firewall/service/impl/config_snapshot_version_test.go`

- [ ] Implement create/list/find-latest-confirmed/find-latest-pending operations.
- [ ] Implement confirm operation.
- [ ] Implement reject operation.
- [ ] Confirm operation must supersede previous confirmed snapshot.
- [ ] Reject operation must not mutate `firewall_node.config_fact_snapshot`.

Verification:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
go test ./app/firewall/service/impl -run 'Test.*ConfigSnapshotVersion' -count=1
```

Expected: all snapshot version tests pass.

### Task 3: Integrate Snapshot Versioning Into Upload/Parse/Collect

**Files:**
- Modify: `OneOps/app/firewall/service/impl/config_fact_snapshot.go`
- Modify: `OneOps/app/firewall/service/impl/firewall_node.go`
- Modify: `OneOps/app/firewall/service/impl/firewall_online_collection.go`
- Test: `OneOps/app/firewall/service/impl/config_fact_snapshot_test.go`
- Test: `OneOps/app/firewall/service/impl/firewall_online_collection_test.go`

- [ ] When snapshot generation succeeds, persist a snapshot version record.
- [ ] If no baseline exists, allow first snapshot to become confirmed through explicit confirmation.
- [ ] If baseline diff is normal, preserve current behavior but also store history.
- [ ] If baseline diff requires confirmation, store pending snapshot and return structured precheck display.
- [ ] Ensure planning still reads confirmed snapshot, not pending snapshot.

Verification:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
go test ./app/firewall/service/impl -run 'Test.*ConfigFactSnapshot|Test.*FirewallOnlineCollection' -count=1
```

Expected: existing baseline and collection tests pass, with added snapshot-version assertions.

### Task 4: Snapshot API Endpoints

**Files:**
- Create or modify: `OneOps/app/firewall/api/config_snapshot_version.go`
- Modify: `OneOps/app/firewall/router/planning.go`
- Test: `OneOps/app/firewall/api/config_snapshot_version_test.go`

- [ ] Add list endpoint.
- [ ] Add confirm endpoint.
- [ ] Add reject endpoint.
- [ ] Return `precheck_display` for invalid state transitions.
- [ ] Ensure locked node semantics are respected when confirmation would change planning facts.

Verification:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
go test ./app/firewall/api -run 'Test.*ConfigSnapshotVersion' -count=1
```

Expected: API tests pass.

### Task 5: Platform Summary API

**Files:**
- Create: `OneOps/app/firewall/dto/platform_summary.go`
- Create or modify: `OneOps/app/firewall/api/platform_summary.go`
- Create or modify: `OneOps/app/firewall/service/impl/platform_summary.go`
- Modify: `OneOps/app/firewall/router/planning.go`
- Test: `OneOps/app/firewall/service/impl/platform_summary_test.go`

- [ ] Return firewall node identity.
- [ ] Return associated Device V2 code if available.
- [ ] Return readiness and edit lock status.
- [ ] Return latest confirmed snapshot summary.
- [ ] Return latest pending snapshot summary.
- [ ] Return latest operation summary when available.

Verification:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
go test ./app/firewall/service/impl -run 'Test.*PlatformSummary' -count=1
```

Expected: platform summary tests pass.

## 8. Frontend Tasks

### Task 6: Snapshot History API Client

**Files:**
- Modify: `OneOPS-UI/src/api/firewall/security_planning.ts`
- Modify or create: `OneOPS-UI/src/typings/firewall/security_planning.ts`

- [ ] Add snapshot history query API.
- [ ] Add snapshot confirm API.
- [ ] Add snapshot reject API.
- [ ] Add platform summary API.

Verification:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOPS-UI
yarn type-check
```

Expected: type check passes.

### Task 7: Node Baseline UI Enhancement

**Files:**
- Modify: `OneOPS-UI/src/views/firewall/SecurityPlanning.vue`
- Modify: `OneOPS-UI/src/views/firewall/components/planning/SecurityPlanningNodeBaselineTab.vue`
- Create: `OneOPS-UI/src/views/firewall/components/planning/FirewallSnapshotHistoryDrawer.vue`

- [ ] Show latest confirmed snapshot.
- [ ] Show latest pending snapshot.
- [ ] Show readiness and edit lock status together.
- [ ] Add confirm/reject actions for pending snapshot.
- [ ] Add snapshot history drawer.
- [ ] Preserve existing online collection and upload flows.

Verification:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOPS-UI
yarn type-check
```

Expected: type check passes.

### Task 8: Device/Firewall Summary Entry

**Files:**
- Modify existing firewall detail or planning component that owns firewall node detail.
- If Device V2 detail integration is in scope for this iteration, modify the relevant Device V2 detail panel instead of creating a new firewall-only page.

- [ ] Surface firewall platform summary.
- [ ] Show latest baseline time, readiness, and pending confirmation count.
- [ ] Link to snapshot history.
- [ ] Link to policy validation and black/white list pages with node context.

Verification:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOPS-UI
yarn type-check
```

Expected: type check passes.

## 9. MVP Acceptance Criteria

The MVP is complete when:

1. A firewall config upload creates a snapshot version.
2. Online collection creates a snapshot version.
3. Confirm-required baseline changes are stored as pending snapshots.
4. Confirming a pending snapshot updates the node confirmed baseline.
5. Rejecting a pending snapshot leaves the old confirmed baseline active.
6. The firewall node UI shows latest confirmed snapshot, pending snapshot, readiness, and edit lock.
7. Snapshot history can be queried.
8. Planning/mapping still uses the confirmed snapshot only.
9. Tests cover normal, confirm-required, confirm, and reject flows.
10. Existing firewall precheck behavior remains structured through `precheck_display`.

## 10. Suggested Delivery Sequence

1. Backend snapshot version model.
2. Backend snapshot version service.
3. Integrate upload/collect snapshot persistence.
4. Add confirm/reject/list APIs.
5. Add platform summary API.
6. Add frontend API clients.
7. Add node baseline UI.
8. Add snapshot history UI.
9. Run backend and frontend smoke tests.
10. Update status documentation.

## 11. Keep For Later

After this MVP lands, plan separate MVPs for:

1. Firewall task assetization through task center.
2. Policy intent unification.
3. Black/white list lifecycle governance.
4. Config diff and drift detection.
5. AIOps explanation and recommended remediation.
