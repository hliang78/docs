# Strategy Dashboard Tree Pilot Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a minimal root-dashboard plus strategy-dashboard tree pilot so one strategy set can materialize a target-scoped dashboard tree instead of only one flat dashboard per variant.

**Architecture:** Keep the existing flat dashboard generation path intact while introducing a new pilot path for a tree-shaped dashboard model. The pilot adds explicit logical dashboard nodes, preserves strategy-node ownership into dashboard planning, and persists target-scoped root/child dashboard instance relationships without trying to redesign every existing endpoint at once.

**Tech Stack:** Go backend in `/OneOPS/OneOps`, existing Teleabs/Grafana DTOs and resolver flow, GORM platform models in `app/platform/platform_model`, API/router wiring in `app/platform/api` and `app/platform/router`, tests in `app/platform/service/impl` and `app/platform/api`, docs in `/OneOPS/docs/superpowers`.

---

## Scope Lock

Allowed in this pilot:

- introduce explicit root-dashboard versus strategy-dashboard concepts;
- preserve strategy-node ownership into dashboard planning;
- add a new tree-shaped dry-run/save pilot path instead of mutating every old endpoint immediately;
- persist parent/child dashboard instance relationships for the pilot;
- keep current single-dashboard flow available for compatibility.

Not allowed in this pilot:

- no full frontend tree UI;
- no deletion of the old flat dashboard endpoints;
- no full migration of all variants and all template families;
- no recording-rule redesign;
- no multi-parent dashboard hierarchy.

## File Structure

Backend expected to change:

- Modify: `/OneOPS/OneOps/app/platform/platform_model/teleabs_strategy_set.go`
- Modify: `/OneOPS/OneOps/app/platform/dto/snmp_metric_contract.go`
- Modify: `/OneOPS/OneOps/app/platform/service/i_metric_capability_contract_resolver.go`
- Modify: `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver.go`
- Modify: `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver_test.go`
- Modify: `/OneOPS/OneOps/app/platform/api/teleabs.go`
- Modify: `/OneOPS/OneOps/app/platform/api/teleabs_metric_contract_http_test.go`
- Modify: `/OneOPS/OneOps/app/platform/router/platform.go`
- Modify: `/OneOPS/OneOps/app/platform/router/platform_bidi.go`
- Modify: `/OneOPS/OneOps/app/platform/router/teleabs_routes_consistency_test.go`

Docs expected to change:

- Modify: `/OneOPS/docs/superpowers/handovers/2026-06-10-snmp-metric-groups-dashboard-family-handoff.md`

## Canonical Decisions

These decisions are fixed for this pilot:

- the pilot introduces a new dashboard-tree dry-run/save path instead of rewriting the old flat path in place;
- `strategy_set` owns the root dashboard node;
- each matched `strategy` owns one strategy dashboard node in the pilot;
- target-specific materialization produces a dashboard instance tree, not only one flat dashboard;
- template inheritance remains layout logic only and does not define business parent/child ownership.

## Task 1: Freeze The Flat-Model Limitation With New Tree-Pilot Tests

**Files:**

- Modify: `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver_test.go`
- Modify: `/OneOPS/OneOps/app/platform/api/teleabs_metric_contract_http_test.go`
- Modify: `/OneOPS/OneOps/app/platform/router/teleabs_routes_consistency_test.go`

- [ ] **Step 1: Add a failing resolver test for dashboard-tree planning**

Add a test that builds:

- one strategy set;
- one parent strategy item;
- one child strategy item;
- one target context;
- one dashboard variant.

Expected tree plan shape:

```go
if len(result.Nodes) != 3 {
	t.Fatalf("expected root + 2 strategy dashboard nodes, got %#v", result.Nodes)
}
if result.Nodes[0].Role != "root" || result.Nodes[1].Role != "strategy" {
	t.Fatalf("unexpected node roles: %#v", result.Nodes)
}
if result.Nodes[2].ParentNodeKey != result.Nodes[1].NodeKey {
	t.Fatalf("expected child strategy dashboard to point at parent strategy dashboard, got %#v", result.Nodes[2])
}
```

- [ ] **Step 2: Add a failing resolver test for instance persistence**

Add a test that saves the pilot tree and asserts:

- one root target binding row exists;
- two strategy dashboard target binding rows exist;
- child rows preserve `parent_dashboard_code` and `root_dashboard_code`.

Expected assertions:

```go
if rootBinding.DashboardRole != "root" {
	t.Fatalf("expected root dashboard role, got %#v", rootBinding)
}
if childBinding.ParentDashboardCode == "" || childBinding.RootDashboardCode == "" {
	t.Fatalf("expected persisted parent/root dashboard links, got %#v", childBinding)
}
```

- [ ] **Step 3: Add failing API tests for tree dry-run/save routes**

Add HTTP tests for:

- tree dry-run by target;
- tree save by target;
- missing `dashboard_variant` rejected.

Expected request example:

```go
req := httptest.NewRequest(
	http.MethodPost,
	"/platform/metrics/teleabs/strategy-sets/set-1/metric-contract/grafana/dashboard-tree/materialize/dry-run/by-target",
	strings.NewReader(`{"target_part":"SW-1","dashboard_variant":"snmp.switch.operations"}`),
)
```

- [ ] **Step 4: Add route consistency test expectations**

Extend route consistency expectations with:

- `POST strategy-sets/:id/metric-contract/grafana/dashboard-tree/materialize/dry-run/by-target`
- `POST strategy-sets/:id/metric-contract/grafana/dashboard-tree/save/by-target`

- [ ] **Step 5: Run focused tests to verify RED**

Run:

```bash
cd /OneOPS/OneOps
go test ./app/platform/service/impl -run 'TestMetricCapabilityContractResolver.*DashboardTree.*' -count=1
go test ./app/platform/api -run 'TestTeleabsAPI_.*DashboardTree.*' -count=1
go test ./app/platform/router -run TestTeleabsRoutes_ConsistentBetweenPlatformAndBidi -count=1
```

Expected: RED until the tree pilot types, routes, resolver, and persistence exist.

## Task 2: Add Dashboard-Tree DTOs And Ownership Fields

**Files:**

- Modify: `/OneOPS/OneOps/app/platform/platform_model/teleabs_strategy_set.go`
- Modify: `/OneOPS/OneOps/app/platform/dto/snmp_metric_contract.go`

- [ ] **Step 1: Extend dashboard target binding model with tree fields**

Add the following pilot fields to `TeleabsStrategySetDashboardTargetBinding`:

```go
DashboardRole       string `gorm:"type:varchar(32);not null;default:'';comment:root|strategy"`
OwnerStrategyID     string `gorm:"type:varchar(64);index;not null;default:'';comment: owning strategy id for strategy dashboard"`
ParentDashboardCode string `gorm:"type:varchar(32);index;not null;default:'';comment: parent dashboard code"`
RootDashboardCode   string `gorm:"type:varchar(32);index;not null;default:'';comment: root dashboard code"`
```

- [ ] **Step 2: Extend panel binding and snapshot models with tree fields**

Add the same ownership context to:

- `TeleabsStrategySetDashboardPanelBinding`
- `TeleabsStrategySetDashboardSnapshot`

Minimum fields:

```go
DashboardRole       string
OwnerStrategyID     string
ParentDashboardCode string
RootDashboardCode   string
```

- [ ] **Step 3: Add dashboard-tree pilot DTOs**

In `snmp_metric_contract.go`, add:

- `SnmpStrategySetTargetGrafanaDashboardTreeDryRunRequest`
- `SnmpStrategySetTargetGrafanaDashboardTreeDryRunResponse`
- `SnmpGrafanaDashboardTreeNodePreview`
- `SnmpStrategySetTargetGrafanaDashboardTreeSaveByTargetRequest`
- `SnmpStrategySetTargetGrafanaDashboardTreeSaveByTargetResponse`

Minimum preview node shape:

```go
type SnmpGrafanaDashboardTreeNodePreview struct {
	NodeKey              string `json:"node_key"`
	Role                 string `json:"role"`
	OwnerStrategyID      string `json:"owner_strategy_id,omitempty"`
	ParentNodeKey        string `json:"parent_node_key,omitempty"`
	DashboardCode        string `json:"dashboard_code,omitempty"`
	DashboardName        string `json:"dashboard_name,omitempty"`
	DashboardVariant     string `json:"dashboard_variant"`
	PanelBindingCount    int    `json:"panel_binding_count"`
}
```

- [ ] **Step 4: Run a focused compile test**

Run:

```bash
cd /OneOPS/OneOps
go test ./app/platform/dto -run '^$' -count=1
go test ./app/platform/platform_model -run '^$' -count=1
```

Expected: PASS or no-package-test success without compile errors.

## Task 3: Build A Strategy-Node Dashboard Tree Planner

**Files:**

- Modify: `/OneOPS/OneOps/app/platform/service/i_metric_capability_contract_resolver.go`
- Modify: `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver.go`
- Modify: `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver_test.go`

- [ ] **Step 1: Add resolver interface methods**

Add:

```go
ResolveStrategySetTargetGrafanaDashboardTreeMaterializationDryRun(
	ctx context.Context,
	strategySetID string,
	request dto.SnmpStrategySetTargetGrafanaDashboardTreeDryRunRequest,
) (*dto.SnmpStrategySetTargetGrafanaDashboardTreeDryRunResponse, error)

ResolveStrategySetTargetGrafanaDashboardTreeSaveByTarget(
	ctx context.Context,
	strategySetID string,
	request dto.SnmpStrategySetTargetGrafanaDashboardTreeSaveByTargetRequest,
) (*dto.SnmpStrategySetTargetGrafanaDashboardTreeSaveByTargetResponse, error)
```

- [ ] **Step 2: Introduce an internal logical node plan**

In resolver implementation, add an internal planner type:

```go
type snmpGrafanaDashboardTreeNodePlan struct {
	NodeKey           string
	Role              string
	OwnerStrategyID   string
	ParentNodeKey     string
	DashboardVariant  string
	MetricGroupKeys   []string
	PanelBindings     []dto.SnmpGrafanaPanelBindingPreview
}
```

- [ ] **Step 3: Create a root node plus strategy nodes**

Implement a planner that:

- creates one root node for the strategy set;
- creates one node per matched strategy item;
- derives parent-child node relationships from the strategy tree;
- keeps root node separate from strategy nodes.

Minimum rule:

```go
rootNode := snmpGrafanaDashboardTreeNodePlan{
	NodeKey:          "root",
	Role:             "root",
	DashboardVariant: dashboardVariant,
}
```

Strategy nodes must retain `OwnerStrategyID`.

- [ ] **Step 4: Keep aggregate support, but split panel ownership**

Reuse existing aggregate preview/materialization helpers only where they remain valid.
Do not reuse the old flat final grouping.

Implement minimal panel assignment rules:

- root node gets overview/identity/navigation-intent panels only;
- strategy node gets panels whose `strategy_ids` resolve to that owner strategy;
- child strategy node inherits no parent ownership by default.

- [ ] **Step 5: Run focused planner tests**

Run:

```bash
cd /OneOPS/OneOps
go test ./app/platform/service/impl -run 'TestMetricCapabilityContractResolver.*DashboardTree.*' -count=1
```

Expected: PASS.

## Task 4: Add Tree Dry-Run And Save Endpoints

**Files:**

- Modify: `/OneOPS/OneOps/app/platform/api/teleabs.go`
- Modify: `/OneOPS/OneOps/app/platform/router/platform.go`
- Modify: `/OneOPS/OneOps/app/platform/router/platform_bidi.go`
- Modify: `/OneOPS/OneOps/app/platform/router/teleabs_routes_consistency_test.go`
- Modify: `/OneOPS/OneOps/app/platform/api/teleabs_metric_contract_http_test.go`

- [ ] **Step 1: Add pilot routes**

Add:

```go
teleabsGroup.POST("strategy-sets/:id/metric-contract/grafana/dashboard-tree/materialize/dry-run/by-target", teleabsAPI.MaterializeTeleabsStrategySetGrafanaDashboardTreeByTarget)
teleabsGroup.POST("strategy-sets/:id/metric-contract/grafana/dashboard-tree/save/by-target", teleabsAPI.SaveTeleabsStrategySetGrafanaDashboardTreeByTarget)
```

in both `platform.go` and `platform_bidi.go`.

- [ ] **Step 2: Add API handlers**

Add handlers that:

- bind request body;
- require `target_part`;
- require `dashboard_variant`;
- delegate to new resolver methods;
- return JSON response directly.

Minimum validation:

```go
if strings.TrimSpace(body.DashboardVariant) == "" {
	response.FailWithMsg("dashboard_variant is required", ctx)
	return
}
```

- [ ] **Step 3: Run API and router verification**

Run:

```bash
cd /OneOPS/OneOps
go test ./app/platform/api -run 'TestTeleabsAPI_.*DashboardTree.*' -count=1
go test ./app/platform/router -run TestTeleabsRoutes_ConsistentBetweenPlatformAndBidi -count=1
```

Expected: PASS.

## Task 5: Persist The Dashboard Instance Tree

**Files:**

- Modify: `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver.go`
- Modify: `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver_test.go`

- [ ] **Step 1: Save root dashboard instance first**

Implement root-node save so it writes:

- `dashboard_role = root`
- `owner_strategy_id = ""`
- `parent_dashboard_code = ""`
- `root_dashboard_code = root dashboard code`

- [ ] **Step 2: Save strategy dashboard instances with parent/root links**

For each strategy node, persist:

```go
DashboardRole:       "strategy",
OwnerStrategyID:     ownerStrategyID,
ParentDashboardCode: parentDashboardCode,
RootDashboardCode:   rootDashboardCode,
```

Child strategy nodes should reference their parent strategy dashboard code if one exists; otherwise they should hang directly under root.

- [ ] **Step 3: Save tree-aware panel bindings**

Each panel binding row for the pilot must preserve:

- `dashboard_role`
- `owner_strategy_id`
- `parent_dashboard_code`
- `root_dashboard_code`

This keeps traceability aligned with the new tree ownership.

- [ ] **Step 4: Save tree-aware snapshots**

When overwriting an existing dashboard node, snapshots must also preserve:

- root/strategy role;
- owner strategy id;
- parent/root dashboard codes.

- [ ] **Step 5: Run persistence verification**

Run:

```bash
cd /OneOPS/OneOps
go test ./app/platform/service/impl -run 'TestMetricCapabilityContractResolver.*DashboardTree.*Save.*|TestMetricCapabilityContractResolver.*DashboardTree.*Snapshot.*' -count=1
```

Expected: PASS.

## Task 6: Document The Pilot And Verification Boundary

**Files:**

- Modify: `/OneOPS/docs/superpowers/handovers/2026-06-10-snmp-metric-groups-dashboard-family-handoff.md`

- [ ] **Step 1: Add handoff notes for the tree pilot**

Document:

- tree pilot routes;
- root versus strategy dashboard roles;
- current compatibility boundary between old flat save and new tree save;
- what is still intentionally not migrated.

- [ ] **Step 2: Run final verification**

Run:

```bash
cd /OneOPS/OneOps
go test ./app/platform/service/impl -run 'TestMetricCapabilityContractResolver.*DashboardTree.*' -count=1
go test ./app/platform/api -run 'TestTeleabsAPI_.*DashboardTree.*' -count=1
go test ./app/platform/router -run TestTeleabsRoutes_ConsistentBetweenPlatformAndBidi -count=1
git -C /OneOPS/OneOps diff --check
git -C /OneOPS/docs diff --check
```

Expected: PASS.

## Self-Review

Spec coverage:

- root dashboard versus strategy dashboard is covered in Tasks 2 and 3;
- target-scoped dashboard instance tree is covered in Task 5;
- current flat-path compatibility is preserved by the pilot route strategy in Task 4;
- parent/child persistence is covered in Task 5.

Placeholder scan:

- no `TODO` / `TBD` placeholders remain;
- every task contains exact files, commands, and concrete model/code snippets.

Type consistency:

- pilot naming consistently uses `dashboard tree`, `root`, `strategy`, `owner_strategy_id`, `parent_dashboard_code`, and `root_dashboard_code`;
- tree dry-run/save methods are named consistently across resolver, API, and routes.
