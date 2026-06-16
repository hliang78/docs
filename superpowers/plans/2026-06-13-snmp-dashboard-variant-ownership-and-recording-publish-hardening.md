# SNMP Dashboard Variant Ownership And Recording Publish Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the existing SNMP Grafana and recording-rule delivery path safe enough to build on by hardening dashboard variant ownership, template resolution boundaries, and recording-rule file publish behavior without expanding dashboard product scope or introducing a new DashboardFamily entity.

**Architecture:** Treat this round as boundary hardening, not feature expansion. First make `dashboard_variant` explicit across Grafana dry-run/save flows and make owner replacement logic variant-aware in the backend. Then tighten template-chain and panel-binding resolution around `panel_key` so the strategy tree, template tree, and instance tree stop bleeding into each other. Finally, harden the recording-rule publish path by replacing truncate-write with true temp-file replacement and by making publish conflict/error behavior more visible.

**Tech Stack:** Go backend under `/OneOPS/OneOps`, TypeScript/Vue frontend under `/OneOPS/OneOps-UI`, existing HTTP and resolver tests, existing smoke scripts, Grafana/platform persistence models, and docs under `/OneOPS/docs/superpowers`.

---

## Scope Lock

Allowed in this slice:

- require explicit `dashboard_variant` in Grafana materialize/save requests and responses;
- make dashboard instance replacement logic variant-aware in backend save paths;
- harden by-target template resolution to one deterministic chain per target+variant;
- enforce `panel_key` as the semantic binding key between effective contract and dashboard materialization;
- replace recording-rule truncate-write with temp-file write plus rename;
- improve publish conflict/error visibility where already supported by current APIs;
- update frontend API wrappers, typings, and dry-run/save callers to pass and display explicit variant information.

Not allowed in this slice:

- no new DashboardFamily table or migration-heavy family normalization;
- no new dashboard variants beyond current defaults;
- no broad SNMP page redesign;
- no cross-strategy-set dashboard sharing model;
- no generic multi-backend recording-rule publish framework;
- no manual Grafana editor round-trip;
- no large database migration project in this plan.

## Outcome

By the end of this plan, the codebase should have these properties:

1. Grafana materialize/save requests always know which `dashboard_variant` they are operating on.
2. One target under one strategy set can only have one current dashboard instance per variant at the application-logic level.
3. Grafana materialization binds through `panel_key`, not implicit metric guessing.
4. Template resolution either returns one chain or fails explicitly.
5. Recording-rule publish uses a real temp-file replace path instead of truncating the managed file in place.
6. Existing dry-run/publish/save endpoints remain compatible enough for current consumers while exposing the hardened boundaries.

## File Structure

Backend files expected to change:

- Modify: `/OneOPS/OneOps/app/platform/dto/snmp_metric_contract.go`
- Modify: `/OneOPS/OneOps/app/platform/api/teleabs.go`
- Modify: `/OneOPS/OneOps/app/platform/api/teleabs_metric_contract_http_test.go`
- Modify: `/OneOPS/OneOps/app/platform/service/i_metric_capability_contract_resolver.go`
- Modify: `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver.go`
- Modify: `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver_test.go`
- Modify: `/OneOPS/OneOps/app/platform/platform_model/teleabs_strategy_set.go`

Frontend files expected to change:

- Modify: `/OneOPS/OneOps-UI/src/typings/platform/snmp-metric-contract.ts`
- Modify: `/OneOPS/OneOps-UI/src/api/platform/teleabs.ts`
- Modify: `/OneOPS/OneOps-UI/src/views/platform/StrategyTemplate/snmpStrategySetGrafanaDashboardSave.ts`
- Modify: `/OneOPS/OneOps-UI/scripts/snmp-strategy-set-grafana-dashboard-materialization-dry-run-smoke.ts`
- Modify: `/OneOPS/OneOps-UI/scripts/snmp-strategy-set-grafana-dashboard-save-action-smoke.ts`
- Modify: `/OneOPS/OneOps-UI/scripts/snmp-strategy-set-grafana-dashboard-open-link-smoke.ts`

Docs expected to change:

- Modify: `/OneOPS/docs/superpowers/handovers/2026-06-10-snmp-metric-groups-dashboard-family-handoff.md`
- Create: `/OneOPS/docs/superpowers/specs/2026-06-13-snmp-dashboard-tree-and-recording-publish-boundaries-design.md`

## Canonical Decisions

These decisions are fixed for this plan:

- `dashboard_variant` is a first-class input to Grafana materialize/save.
- `DashboardFamily` remains a naming convention prefix, not a new stored entity.
- application-level dashboard owner key is:
  - `strategy_set_id + target_part + dashboard_variant`
- dashboard template resolution must produce exactly one chain for one `target + dashboard_variant`.
- dashboard materialization binds contract semantics to template slots through `panel_key`.
- recording-rule publish remains `vmalert_file`-backed in this slice.
- the recording-rule write path must become temp-file plus rename before reload.

## Task 1: Freeze Current Behavior With Variant-Aware Failing Tests

**Files:**

- Modify: `/OneOPS/OneOps/app/platform/api/teleabs_metric_contract_http_test.go`
- Modify: `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver_test.go`
- Modify: `/OneOPS/OneOps-UI/scripts/snmp-strategy-set-grafana-dashboard-materialization-dry-run-smoke.ts`
- Modify: `/OneOPS/OneOps-UI/scripts/snmp-strategy-set-grafana-dashboard-save-action-smoke.ts`

- [ ] **Step 1: Add failing backend tests for explicit dashboard variant propagation**

Add HTTP and resolver coverage for:

- Grafana materialization dry-run receiving explicit `dashboard_variant`;
- Grafana save-by-target receiving explicit `dashboard_variant`;
- target save behavior distinguishing two variants for the same `strategy_set_id + target_part`.

Expected test intent:

```go
request := dto.SnmpStrategySetTargetGrafanaDashboardMaterializationDryRunRequest{
    TargetPart: "SW-1",
    DashboardVariant: "snmp.switch.operations",
}
```

```go
request := dto.SnmpStrategySetTargetGrafanaDashboardSaveByTargetRequest{
    TargetPart: "SW-1",
    DashboardVariant: "snmp.switch.capacity",
}
```

Assertions:

- request body must bind `dashboard_variant`;
- response `materialization.dashboard_template_key` still resolves;
- save logic must not treat `snmp.switch.operations` and `snmp.switch.capacity` as the same current instance.

- [ ] **Step 2: Add failing backend tests for recording-rule atomic replace behavior**

Add a focused unit test around the write helper that proves:

- publish writes through a temporary file path in the same directory;
- the target file content is replaced only after successful temp write;
- reload is called only after the replacement step succeeds.

Suggested test shape:

```go
func TestPublishManagedRecordingRuleFileUsesTempReplace(t *testing.T) {
    // start with existing YAML file
    // publish managed group
    // assert resulting file contains unmanaged group + managed group
    // assert no direct truncate-write helper remains in use
}
```

- [ ] **Step 3: Add failing frontend smoke for explicit dashboard variant**

Update the Grafana dry-run/save smokes so they pass explicit variant and assert it round-trips.

Required smoke assertions:

```ts
assert.equal(request.dashboard_variant, 'snmp.switch.operations');
assert.equal(response.panel_bindings[0].dashboard_variant, 'snmp.switch.operations');
```

- [ ] **Step 4: Run the focused tests to capture RED baseline**

Run:

```bash
cd /OneOPS/OneOps
go test ./app/platform/api -run 'TestTeleabsAPI_.*Grafana.*|TestTeleabsAPI_PublishStrategySetRecordingRulesByTarget' -count=1
go test ./app/platform/service/impl -run 'TestMetricCapabilityContractResolver.*Grafana.*|TestMetricCapabilityContractResolverPublishesStrategySetRecordingRulesByTarget' -count=1
```

Run:

```bash
cd /OneOPS/OneOps-UI
npm run smoke:snmp-strategy-set-grafana-dashboard-materialization-dry-run
npm run smoke:snmp-strategy-set-grafana-dashboard-save-action
```

Expected: RED until explicit variant propagation and atomic publish behavior are implemented.

## Task 2: Make Dashboard Variant Explicit Across DTOs, APIs, And Frontend Callers

**Files:**

- Modify: `/OneOPS/OneOps/app/platform/dto/snmp_metric_contract.go`
- Modify: `/OneOPS/OneOps/app/platform/api/teleabs.go`
- Modify: `/OneOPS/OneOps/app/platform/api/teleabs_metric_contract_http_test.go`
- Modify: `/OneOPS/OneOps/app/platform/service/i_metric_capability_contract_resolver.go`
- Modify: `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver.go`
- Modify: `/OneOPS/OneOps-UI/src/typings/platform/snmp-metric-contract.ts`
- Modify: `/OneOPS/OneOps-UI/src/api/platform/teleabs.ts`
- Modify: `/OneOPS/OneOps-UI/src/views/platform/StrategyTemplate/snmpStrategySetGrafanaDashboardSave.ts`

- [ ] **Step 1: Add `dashboard_variant` to Grafana request DTOs and TS types**

Update backend DTOs and frontend typings so these requests carry explicit variant:

```go
type SnmpStrategySetTargetGrafanaDashboardMaterializationDryRunRequest struct {
    TargetPart string `json:"target_part"`
    DashboardVariant string `json:"dashboard_variant"`
}

type SnmpStrategySetTargetGrafanaDashboardSaveByTargetRequest struct {
    TargetPart string `json:"target_part"`
    DashboardVariant string `json:"dashboard_variant"`
}
```

```ts
export interface SnmpStrategySetTargetGrafanaDashboardMaterializationDryRunRequest {
  target_part: string;
  dashboard_variant: string;
}

export interface SnmpStrategySetTargetGrafanaDashboardSaveByTargetRequest {
  target_part: string;
  dashboard_variant: string;
}
```

- [ ] **Step 2: Thread `dashboard_variant` through HTTP handlers and resolver interfaces**

Make the API layer validate that `dashboard_variant` is non-empty for Grafana materialize/save endpoints.

Validation target:

```go
if strings.TrimSpace(body.DashboardVariant) == "" {
    ctx.JSON(http.StatusBadRequest, gin.H{"code": 1, "msg": "dashboard_variant is required"})
    return
}
```

Update resolver interface signatures only through the request DTOs, not new method overloads.

- [ ] **Step 3: Update frontend callers to pass explicit variant**

In the current save/dry-run state helper, make the selected/default variant explicit in API calls.

Target call shape:

```ts
await materializeTeleabsStrategySetGrafanaDashboardByTarget(strategySetId, {
  target_part: currentTarget,
  dashboard_variant: currentDashboardVariant,
});
```

```ts
await saveTeleabsStrategySetGrafanaDashboardByTarget(strategySetId, {
  target_part: currentTarget,
  dashboard_variant: currentDashboardVariant,
});
```

- [ ] **Step 4: Re-run focused tests**

Run:

```bash
cd /OneOPS/OneOps
go test ./app/platform/api -run 'TestTeleabsAPI_.*Grafana.*' -count=1
go test ./app/platform/service/impl -run 'TestMetricCapabilityContractResolver.*Grafana.*' -count=1
```

Run:

```bash
cd /OneOPS/OneOps-UI
npm run smoke:snmp-strategy-set-grafana-dashboard-materialization-dry-run
npm run smoke:snmp-strategy-set-grafana-dashboard-save-action
```

Expected: GREEN for explicit-variant propagation.

## Task 3: Harden Template Resolution And Panel-Key Binding Semantics

**Files:**

- Modify: `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver.go`
- Modify: `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver_test.go`
- Modify: `/OneOPS/OneOps-UI/src/typings/platform/snmp-metric-contract.ts`

- [ ] **Step 1: Add failing tests for single-chain template resolution**

Cover at least:

- one target and one variant resolving a single chain;
- no matched template returning explicit failure;
- ambiguous same-level template matches returning explicit failure.

Suggested test assertions:

```go
if err == nil || !strings.Contains(err.Error(), "ambiguous dashboard template resolution") {
    t.Fatalf("expected ambiguous template resolution error, got %v", err)
}
```

- [ ] **Step 2: Make resolver accept explicit variant and fail on ambiguous chain selection**

The internal template-resolution helper must operate on:

```go
target dto.SnmpMetricResolvedTargetContext
dashboardVariant string
```

and return exactly one resolved chain:

```go
type snmpGrafanaTemplateResolution struct {
    TemplateKey string
    TemplateChain []string
}
```

Behavior:

- zero matches -> explicit error;
- one deterministic chain -> success;
- multiple same-priority matches -> explicit error.

- [ ] **Step 3: Enforce `panel_key` as the primary binding key**

During Grafana materialization:

- template slot lookup must bind through `panel_key`;
- panel binding preview must record the matched `panel_key`;
- missing `panel_key` match should move the panel into skipped/unsupported output instead of implicit metric guessing.

Target behavior note:

```go
binding.PanelKey = strings.TrimSpace(templatePanel.PanelKey)
if binding.PanelKey == "" {
    return nil, fmt.Errorf("template panel_key is required")
}
```

- [ ] **Step 4: Re-run focused resolver tests**

Run:

```bash
cd /OneOPS/OneOps
go test ./app/platform/service/impl -run 'TestMetricCapabilityContractResolver.*Grafana.*' -count=1
```

Expected: GREEN with deterministic chain resolution and panel-key-based binding.

## Task 4: Make Dashboard Save Paths Variant-Aware And Snapshot-Safe

**Files:**

- Modify: `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver.go`
- Modify: `/OneOPS/OneOps/app/platform/platform_model/teleabs_strategy_set.go`
- Modify: `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver_test.go`

- [ ] **Step 1: Add failing tests for variant-aware current-instance replacement**

Cover:

- same strategy set + same target + same variant => replace current instance;
- same strategy set + same target + different variant => keep separate current instance records;
- content SHA unchanged => snapshot not duplicated.

Suggested assertions:

```go
if got != 2 {
    t.Fatalf("expected two target bindings for two variants, got %d", got)
}
```

- [ ] **Step 2: Update target-binding replacement logic to include variant**

Current replacement logic uses `dashboard_code` and `strategy_set_id + target_part`.

Adjust it to variant-aware owner semantics:

```go
Where("dashboard_code = ?", dashboardCode).
Or("strategy_set_id = ? AND target_part = ? AND dashboard_variant = ?", strategySetID, targetPart, dashboardVariant)
```

Apply the same principle to panel-binding replacement.

- [ ] **Step 3: Ensure snapshot rows capture explicit variant**

Snapshot save logic must store the request/materialized `dashboard_variant`, not a constant switch-dashboard variant.

Target change shape:

```go
DashboardVariant: strings.TrimSpace(dashboardVariant),
```

- [ ] **Step 4: Re-run save-path tests**

Run:

```bash
cd /OneOPS/OneOps
go test ./app/platform/service/impl -run 'TestMetricCapabilityContractResolver.*Grafana.*Save.*|TestMetricCapabilityContractResolver.*Snapshot.*' -count=1
```

Expected: GREEN with variant-aware replacement.

## Task 5: Harden Recording-Rule File Publish To True Temp-File Replacement

**Files:**

- Modify: `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver.go`
- Modify: `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver_test.go`
- Modify: `/OneOPS/docs/superpowers/handovers/2026-06-10-snmp-metric-groups-dashboard-family-handoff.md`

- [ ] **Step 1: Add failing tests around temp-file replacement**

Tests should prove:

- target file is not opened with truncate-before-success semantics;
- publish writes a temp file in the same directory;
- successful publish replaces the final file content and reloads;
- failed temp-file write leaves the original managed file intact.

- [ ] **Step 2: Replace truncate-write helper with temp-file + rename helper**

Implementation target:

```go
func writeRecordingRuleFileAtomically(path string, data []byte) error {
    dir := filepath.Dir(path)
    base := filepath.Base(path)
    temp, err := os.CreateTemp(dir, base+".*.tmp")
    if err != nil {
        return err
    }
    tempPath := temp.Name()
    defer os.Remove(tempPath)
    if _, err := temp.Write(data); err != nil {
        temp.Close()
        return err
    }
    if err := temp.Sync(); err != nil {
        temp.Close()
        return err
    }
    if err := temp.Close(); err != nil {
        return err
    }
    return os.Rename(tempPath, path)
}
```

- [ ] **Step 3: Preserve explicit reload-failure semantics**

Do not add silent rollback in this slice.

Required behavior:

- write success + reload failure => `failed_reload`
- publish record still persists
- file content remains the newly written managed content

- [ ] **Step 4: Re-run publish tests**

Run:

```bash
cd /OneOPS/OneOps
go test ./app/platform/service/impl -run 'TestMetricCapabilityContractResolverPublishesStrategySetRecordingRulesByTarget|TestMetricCapabilityContractResolverPublishesManagedRuleFileAndReloads|TestMetricCapabilityContractResolverMergesManagedRecordingRuleGroup' -count=1
go test ./app/platform/api -run 'TestTeleabsAPI_PublishStrategySetRecordingRulesByTarget' -count=1
```

Expected: GREEN with temp-file replacement still preserving managed-group merge and reload behavior.

## Task 6: Align Frontend Dry-Run/Save UX With The Hardened Boundaries

**Files:**

- Modify: `/OneOPS/OneOps-UI/src/views/platform/StrategyTemplate/snmpStrategySetGrafanaDashboardSave.ts`
- Modify: `/OneOPS/OneOps-UI/scripts/snmp-strategy-set-grafana-dashboard-open-link-smoke.ts`
- Modify: `/OneOPS/OneOps-UI/scripts/snmp-strategy-set-grafana-dashboard-save-action-smoke.ts`
- Modify: `/OneOPS/OneOps-UI/scripts/snmp-strategy-set-grafana-dashboard-materialization-dry-run-smoke.ts`

- [ ] **Step 1: Surface explicit variant in frontend save state**

Make the frontend state helper keep one clear current variant value and include it in:

- dry-run requests;
- save requests;
- open-link/save summaries.

Suggested state shape:

```ts
const currentDashboardVariant = ref('snmp.switch.operations');
```

- [ ] **Step 2: Update dry-run/save summaries to display variant**

At minimum, add variant to the summary rows/state so operators can tell which dashboard type they are previewing or saving.

Suggested summary row:

```ts
{ label: '仪表盘类型', value: current.dashboard_variant || 'snmp.switch.operations' }
```

- [ ] **Step 3: Re-run frontend smokes**

Run:

```bash
cd /OneOPS/OneOps-UI
npm run smoke:snmp-strategy-set-grafana-dashboard-materialization-dry-run
npm run smoke:snmp-strategy-set-grafana-dashboard-save-action
npm run smoke:snmp-strategy-set-grafana-dashboard-open-link
```

Expected: GREEN with explicit-variant flow visible end to end.

## Task 7: Close The Loop In Handoff Docs

**Files:**

- Modify: `/OneOPS/docs/superpowers/handovers/2026-06-10-snmp-metric-groups-dashboard-family-handoff.md`

- [ ] **Step 1: Document the new canonical boundaries**

Add/update sections that state explicitly:

- Grafana uses three trees:
  - strategy tree
  - template tree
  - instance tree
- current owner key is application-level:
  - `strategy_set_id + target_part + dashboard_variant`
- recording-rule publish currently uses:
  - `vmalert_file`
  - managed-group replacement
  - temp-file + rename
  - reload endpoint

- [ ] **Step 2: Record known deferred work**

List as still deferred:

- normalized DashboardFamily entity;
- DB-level unique constraints/migration project for dashboard owner semantics;
- generic multi-backend recording-rule publisher;
- rollback-on-reload-failure design.

## Self-Review Checklist

Spec coverage review:

- explicit `dashboard_variant` input: covered in Tasks 1, 2, 6;
- three-tree boundary hardening: covered in Tasks 3, 4, 7;
- owner-key semantics: covered in Task 4 and documented in Task 7;
- panel-key-based binding: covered in Task 3;
- recording-rule stability hardening: covered in Task 5 and documented in Task 7.

Placeholder scan:

- no `TODO` / `TBD` markers remain;
- each task names exact files and commands;
- each implementation task includes required code shape or validation target.

Type consistency reminders:

- use `dashboard_variant` consistently in Go DTOs, TS request types, and save-state helpers;
- keep owner semantics phrased as `strategy_set_id + target_part + dashboard_variant`;
- do not reintroduce `root_dashboard_code` as the primary owner concept in new code.
