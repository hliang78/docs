# SNMP PanelSlot Owner First-Cut Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `PanelSlot` ownership explicit in panel bindings, so tree planning consumes definition-layer owner data before falling back to runtime heuristics.

**Architecture:** Add one small owner model directly onto `SnmpGrafanaPanelBindingPreview`, resolve that owner during dashboard materialization, and let tree planning trust the explicit owner first. Keep this first cut narrow: no DB schema change, no new tree UI, no new by-target runtime flow.

**Tech Stack:** Go, Vue 3, TypeScript, existing SNMP metric-contract resolver/tests, existing dashboard-tree pilot DTOs

---

## File Map

- Modify: `/OneOPS/OneOps/app/platform/dto/snmp_metric_contract.go`
  Purpose: add short, explicit `PanelSlot` owner fields to panel-binding DTOs.
- Modify: `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver.go`
  Purpose: resolve `PanelSlot` owner during materialization and consume it in tree planning.
- Modify: `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver_test.go`
  Purpose: lock owner rules with service-level red/green tests.
- Modify: `/OneOPS/OneOps/app/platform/api/teleabs_metric_contract_http_test.go`
  Purpose: keep HTTP response assertions aligned with new binding fields.
- Modify: `/OneOPS/OneOps-UI/src/typings/platform/snmp-metric-contract.ts`
  Purpose: sync frontend types only; no new UI in this first cut.
- Modify: `/OneOPS/docs/superpowers/handovers/2026-06-10-snmp-metric-groups-dashboard-family-handoff.md`
  Purpose: register this plan as the next implementation entry.

## Naming Baseline

Use short names only.

- `OwnerKind`
- `OwnerKey`
- `PanelSlot`
- `RootNode`
- `StrategyNode`

Do not introduce longer names such as:

- `panel_slot_owner_strategy_identifier`
- `resolved_dashboard_tree_binding_owner`
- `recordingRuleReadinessVersionMismatchForCurrentTarget`

For this first cut:

- `OwnerKind = "root"` means the `PanelSlot` belongs to `strategy_set_id`
- `OwnerKind = "strategy"` means the `PanelSlot` belongs to one `strategy_id`
- `OwnerKey` carries the actual owner key

## Scope Guard

This plan intentionally does **not** do the following:

- no DB migration
- no persistence of panel-slot owner rows
- no new runtime readiness logic
- no tree replay/UI expansion
- no attempt to solve every future panel family

This plan only makes current owner intent explicit for materialized panel bindings and tree planning.

### Task 1: Add Explicit Owner Fields To Panel Bindings

**Files:**
- Modify: `/OneOPS/OneOps/app/platform/dto/snmp_metric_contract.go`
- Modify: `/OneOPS/OneOps/app/platform/api/teleabs_metric_contract_http_test.go`
- Modify: `/OneOPS/OneOps-UI/src/typings/platform/snmp-metric-contract.ts`

- [ ] **Step 1: Write the failing DTO/API test**

Add response assertions that expect short owner fields on `panel_bindings`.

```go
type bindingDTO struct {
	PanelKey   string `json:"panel_key"`
	OwnerKind  string `json:"owner_kind"`
	OwnerKey   string `json:"owner_key"`
}

if got := response.PanelBindings[0].OwnerKind; got != "strategy" {
	t.Fatalf("expected owner_kind=strategy, got %q", got)
}
if got := response.PanelBindings[0].OwnerKey; got != "iface-strategy" {
	t.Fatalf("expected owner_key=iface-strategy, got %q", got)
}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /OneOPS/OneOps && go test ./app/platform/api -run 'TestTeleabsAPI_.*Grafana.*' -count=1`

Expected: FAIL because `owner_kind` / `owner_key` do not exist yet.

- [ ] **Step 3: Add the minimal DTO fields**

Extend `SnmpGrafanaPanelBindingPreview` with short explicit owner fields.

```go
type SnmpGrafanaPanelBindingPreview struct {
	PanelKey   string `json:"panel_key"`
	PanelID    int    `json:"panel_id"`
	Title      string `json:"title"`
	OwnerKind  string `json:"owner_kind,omitempty"`
	OwnerKey   string `json:"owner_key,omitempty"`
	// existing fields stay unchanged
}
```

Sync the frontend type with the same short names.

```ts
export interface SnmpGrafanaPanelBindingPreview {
  panel_key: string;
  panel_id: number;
  title: string;
  owner_kind?: string;
  owner_key?: string;
}
```

- [ ] **Step 4: Run tests to verify DTO/API shape passes**

Run:
- `cd /OneOPS/OneOps && go test ./app/platform/api -run 'TestTeleabsAPI_.*Grafana.*' -count=1`
- `cd /OneOPS/OneOps-UI && npm run typecheck`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add /OneOPS/OneOps/app/platform/dto/snmp_metric_contract.go \
        /OneOPS/OneOps/app/platform/api/teleabs_metric_contract_http_test.go \
        /OneOPS/OneOps-UI/src/typings/platform/snmp-metric-contract.ts
git commit -m "feat: add explicit panel slot owner fields"
```

### Task 2: Resolve Owner During Materialization

**Files:**
- Modify: `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver.go`
- Modify: `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver_test.go`

- [ ] **Step 1: Write failing service tests for the first-cut owner rules**

Add focused tests at the materialization layer.

```go
func TestMetricCapabilityContractResolverAssignsStrategyOwnerToInterfacePanel(t *testing.T) {
	materialized, err := resolver.ResolveStrategySetTargetGrafanaDashboardMaterializationDryRun(
		context.Background(),
		"set-1",
		dto.SnmpStrategySetTargetGrafanaDashboardMaterializationDryRunRequest{TargetPart: "Core-SW-01"},
	)
	if err != nil {
		t.Fatal(err)
	}
	bindingsByPanel := map[string]dto.SnmpGrafanaPanelBindingPreview{}
	for _, binding := range materialized.PanelBindings {
		bindingsByPanel[binding.PanelKey] = binding
	}
	if got := bindingsByPanel["interface_basic.traffic"].OwnerKind; got != "strategy" {
		t.Fatalf("expected strategy owner, got %q", got)
	}
	if got := bindingsByPanel["interface_basic.traffic"].OwnerKey; got == "" {
		t.Fatal("expected non-empty strategy owner_key")
	}
}

func TestMetricCapabilityContractResolverAssignsRootOwnerToEvidencePanel(t *testing.T) {
	materialized, err := resolver.ResolveStrategySetTargetGrafanaDashboardMaterializationDryRun(
		context.Background(),
		"set-1",
		dto.SnmpStrategySetTargetGrafanaDashboardMaterializationDryRunRequest{TargetPart: "Core-SW-01"},
	)
	if err != nil {
		t.Fatal(err)
	}
	bindingsByPanel := map[string]dto.SnmpGrafanaPanelBindingPreview{}
	for _, binding := range materialized.PanelBindings {
		bindingsByPanel[binding.PanelKey] = binding
	}
	if got := bindingsByPanel["platform_config.backup"].OwnerKind; got != "root" {
		t.Fatalf("expected root owner, got %q", got)
	}
	if got := bindingsByPanel["platform_config.backup"].OwnerKey; got != "set-1" {
		t.Fatalf("expected root owner_key=set-1, got %q", got)
	}
}

func TestMetricCapabilityContractResolverLeavesAmbiguousOwnerEmpty(t *testing.T) {
	kind, key := snmpGrafanaBindingOwner(
		"set-1",
		[]dto.SnmpMetricStrategySetItemContract{
			{
				StrategyID: "iface-strategy",
				Contract: dto.SnmpMetricContractEnvelope{
					Capabilities: []dto.SnmpMetricCapability{{Key: "if_in_rate"}},
				},
			},
			{
				StrategyID: "system-strategy",
				Contract: dto.SnmpMetricContractEnvelope{
					Capabilities: []dto.SnmpMetricCapability{{Key: "cpu_usage_direct"}},
				},
			},
		},
		dto.SnmpGrafanaPanelBindingPreview{
			PanelKey:               "shared.summary",
			SelectedCapabilityKeys: []string{"if_in_rate", "cpu_usage_direct"},
		},
	)
	if kind != "" || key != "" {
		t.Fatalf("expected empty owner for ambiguous slot, got kind=%q key=%q", kind, key)
	}
}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /OneOPS/OneOps && go test ./app/platform/service/impl -run 'TestMetricCapabilityContractResolverAssigns.*Owner.*|TestMetricCapabilityContractResolverLeavesAmbiguousOwnerEmpty' -count=1`

Expected: FAIL because owner resolution does not exist yet.

- [ ] **Step 3: Add a small owner resolver right after panel binding creation**

Keep the logic near existing binding generation.

```go
func snmpGrafanaAssignBindingOwners(
	strategySetID string,
	itemContracts []dto.SnmpMetricStrategySetItemContract,
	bindings []dto.SnmpGrafanaPanelBindingPreview,
) []dto.SnmpGrafanaPanelBindingPreview {
	out := make([]dto.SnmpGrafanaPanelBindingPreview, 0, len(bindings))
	for _, binding := range bindings {
		binding.OwnerKind, binding.OwnerKey = snmpGrafanaBindingOwner(strategySetID, itemContracts, binding)
		out = append(out, binding)
	}
	return out
}

func snmpGrafanaBindingOwner(
	strategySetID string,
	itemContracts []dto.SnmpMetricStrategySetItemContract,
	binding dto.SnmpGrafanaPanelBindingPreview,
) (string, string) {
	if snmpGrafanaDashboardTreeRootPanel(binding.PanelKey, binding.MetricGroupKey) ||
		binding.RenderPolicy == snmpGrafanaRenderPlatformEvidenceLink {
		return "root", strings.TrimSpace(strategySetID)
	}
	strategyIDs := snmpGrafanaStrategyIDsForSelectedCapabilities(binding.SelectedCapabilityKeys, itemContracts)
	if len(strategyIDs) == 1 {
		return "strategy", strings.TrimSpace(strategyIDs[0])
	}
	return "", ""
}
```

Call it immediately before materialization responses are returned.

```go
bindings = snmpGrafanaAssignBindingOwners(strategySetID, itemContracts, bindings)
```

First-cut rule set:

- root overview/evidence/navigation -> `OwnerKind=root`
- one clear strategy semantic owner -> `OwnerKind=strategy`
- ambiguous multi-owner -> unresolved, not root fallback

- [ ] **Step 4: Run service tests to verify owner resolution passes**

Run:
- `cd /OneOPS/OneOps && go test ./app/platform/service/impl -run 'TestMetricCapabilityContractResolverAssigns.*Owner.*|TestMetricCapabilityContractResolverLeavesAmbiguousOwnerEmpty' -count=1`
- `cd /OneOPS/OneOps && go test ./app/platform/service/impl -run 'TestMetricCapabilityContractResolver.*GrafanaDashboardMaterialization.*' -count=1`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add /OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver.go \
        /OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver_test.go
git commit -m "feat: resolve explicit panel slot owners"
```

### Task 3: Let Tree Planning Consume Explicit Owner First

**Files:**
- Modify: `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver.go`
- Modify: `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver_test.go`

- [ ] **Step 1: Write the failing tree-planning test**

Add a tree-planning test that proves explicit owner data beats late heuristics.

```go
func TestMetricCapabilityContractResolverPlansDashboardTreeFromExplicitOwner(t *testing.T) {
	materialized := &dto.SnmpStrategySetTargetGrafanaDashboardMaterializationDryRunResponse{
		StrategySetID: "set-1",
		ItemContracts: itemContracts,
		PanelBindings: []dto.SnmpGrafanaPanelBindingPreview{
			{
				PanelKey:   "interface_basic.traffic",
				OwnerKind:  "strategy",
				OwnerKey:   "iface-strategy",
				MetricGroupKey: "system_basic",
			},
		},
	}
	nodes, err := resolver.planSnmpGrafanaDashboardTree(context.Background(), "set-1", materialized, []string{"iface-strategy"})
	if err != nil {
		t.Fatal(err)
	}
	if len(nodes[1].PanelBindings) != 1 {
		t.Fatalf("expected binding on strategy node, got %#v", nodes)
	}
}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /OneOPS/OneOps && go test ./app/platform/service/impl -run 'TestMetricCapabilityContractResolverPlansDashboardTreeFromExplicitOwner|TestMetricCapabilityContractResolver.*DashboardTree.*' -count=1`

Expected: FAIL because tree planning still relies on inferred strategy IDs / heuristics first.

- [ ] **Step 3: Add explicit-owner routing before heuristic routing**

Introduce one small helper before `snmpGrafanaDashboardTreeBindingNodeIndex`.

```go
func snmpGrafanaDashboardTreeOwnerNodeIndex(
	binding dto.SnmpGrafanaPanelBindingPreview,
	nodes []snmpGrafanaDashboardTreeNodePlan,
	nodeIndexByStrategyID map[string]int,
) (int, bool) {
	switch strings.TrimSpace(binding.OwnerKind) {
	case "root":
		return 0, true
	case "strategy":
		idx, ok := nodeIndexByStrategyID[strings.TrimSpace(binding.OwnerKey)]
		return idx, ok
	default:
		return 0, false
	}
}
```

Use it like this:

```go
if resolvedIndex, ok := snmpGrafanaDashboardTreeOwnerNodeIndex(binding, nodes, nodeIndexByStrategyID); ok {
	targetIndex = resolvedIndex
} else if resolvedIndex, ok := snmpGrafanaDashboardTreeBindingNodeIndex(...); ok {
	targetIndex = resolvedIndex
} else {
	// keep existing transitional fallback
}
```

This preserves backward compatibility:

- explicit owner first
- current strategy-id inference second
- metric-group fallback last

- [ ] **Step 4: Run tree tests to verify the new order**

Run:
- `cd /OneOPS/OneOps && go test ./app/platform/service/impl -run 'TestMetricCapabilityContractResolverPlansDashboardTreeFromExplicitOwner|TestMetricCapabilityContractResolver.*DashboardTree.*' -count=1`
- `cd /OneOPS/OneOps && go test ./app/platform/api -run 'TestTeleabsAPI_.*DashboardTree.*' -count=1`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add /OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver.go \
        /OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver_test.go
git commit -m "feat: let tree planning consume explicit panel owners"
```

### Task 4: Keep The Change Small And Visible

**Files:**
- Modify: `/OneOPS/docs/superpowers/handovers/2026-06-10-snmp-metric-groups-dashboard-family-handoff.md`

- [ ] **Step 1: Update handoff with the new boundary**

Add one short note that says:

```text
PanelSlot ownership first cut is now the main implementation line.
The first cut adds explicit OwnerKind / OwnerKey on panel bindings,
and tree planning consumes those fields before runtime heuristics.
```

- [ ] **Step 2: Run verification**

Run:
- `cd /OneOPS/OneOps && go test ./app/platform/service/impl -run 'TestMetricCapabilityContractResolverAssigns.*Owner.*|TestMetricCapabilityContractResolverLeavesAmbiguousOwnerEmpty|TestMetricCapabilityContractResolverPlansDashboardTreeFromExplicitOwner|TestMetricCapabilityContractResolver.*DashboardTree.*|TestMetricCapabilityContractResolver.*GrafanaDashboardMaterialization.*' -count=1`
- `cd /OneOPS/OneOps && go test ./app/platform/api -run 'TestTeleabsAPI_.*Grafana.*|TestTeleabsAPI_.*DashboardTree.*' -count=1`
- `cd /OneOPS/OneOps-UI && npm run typecheck`
- `git -C /OneOPS/OneOps diff --check`
- `git -C /OneOPS/OneOps-UI diff --check`
- `git -C /OneOPS/docs diff --check`

Expected: PASS.

- [ ] **Step 3: Commit**

```bash
git add /OneOPS/docs/superpowers/handovers/2026-06-10-snmp-metric-groups-dashboard-family-handoff.md
git commit -m "docs: record panel slot owner first-cut plan"
```

## Self-Review

### Spec coverage

This plan covers the current summary-page gap directly:

- `PanelSlot ownership is still weaker than NodeOwner`

It does so without reopening runtime/readiness work.

### Placeholder scan

No `TODO`, `TBD`, or "handle appropriately" placeholders are left in task steps.

### Type consistency

The short names stay consistent across the plan:

- `OwnerKind`
- `OwnerKey`
- `PanelSlot`

Plan complete and saved to `docs/superpowers/plans/2026-06-14-snmp-panel-slot-owner-first-cut.md`. Two execution options:

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**
