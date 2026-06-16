# SNMP Suite Strategy Dashboard Tree Closure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Promote SNMP dashboard generation and persistence from class-level shared flat dashboards to a suite-root + strategy-node dashboard tree that reuses the same strategy selection result and gives every dashboard node explicit metric-display responsibility.

**Architecture:** Keep the existing target-class baseline machinery as a reusable generation floor, but move the business center of gravity to the dashboard tree. The new primary path should be `suite root -> matched strategy tree -> dashboard tree -> target binding`, while class baselines become downstream layout/panel-family reuse instead of the main semantic selector. Reuse the existing tree pilot tables and `dashboard_role / owner_strategy_id` persistence fields rather than inventing a second parallel model.

**Tech Stack:** Go service layer, existing GORM platform models, Grafana JSON generation, OneOPS quick env SQL/bootstrap scripts, Go tests, Python quick-env seed guard tests.

---

## File Structure

### Existing files to modify

- `/OneOPS/OneOps/app/platform/dto/snmp_metric_contract.go`
  - Expand tree responses so root/strategy dashboard nodes expose explicit metric-display scope.
- `/OneOPS/OneOps/app/platform/service/impl/snmp_grafana_target_class_module.go`
  - Demote class/baseline logic from business selector to generation floor.
- `/OneOPS/OneOps/app/platform/service/impl/snmp_grafana_switch_dashboard_service.go`
  - Replace flat-first generation assembly with dashboard-tree-first assembly.
- `/OneOPS/OneOps/app/platform/service/impl/snmp_grafana_switch_dashboard_persistence_service.go`
  - Make root + strategy dashboard tree persistence the primary save path.
- `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver.go`
  - Rewire public materialize/save/query methods onto the suite/strategy dashboard tree path.
- `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver_test.go`
  - Add/adjust failing tests for suite-root and strategy-node semantics.
- `/OneOPS/OneOps/app/platform/api/teleabs_metric_contract_http_test.go`
  - Verify API shape returns root + strategy dashboard tree semantics.
- `/OneOPS/quick_env/scripts/ensure_snmp_dashboard_instances.sh`
  - Rebuild quick env around visible root + strategy dashboards.
- `/OneOPS/quick_env/tests/test_seed_template_guard.py`
  - Guard the new root + strategy dashboard rows.
- `/OneOPS/docs/superpowers/plans/2026-06-14-snmp-definition-runtime-closure-correction.md`
  - Record the closure shift from class dashboard to suite/strategy dashboard tree.
- `/OneOPS/docs/superpowers/handovers/2026-06-10-snmp-metric-groups-dashboard-family-handoff.md`
  - Update the operational handoff after implementation.

### New files to create

- `/OneOPS/OneOps/app/platform/service/impl/snmp_grafana_suite_dashboard_tree_module.go`
  - One focused module that projects matched strategy selection into root/strategy dashboard tree nodes.
- `/OneOPS/docs/superpowers/specs/2026-06-14-snmp-suite-strategy-dashboard-tree-design.md`
  - Already written; this plan implements it.

## Task 1: Freeze The Tree Semantics In Tests First

**Files:**
- Modify: `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver_test.go`
- Test: `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver_test.go`

- [ ] **Step 1: Write the failing root/strategy semantic tests**

Add table-driven tests that lock these rules:

```go
func TestSnmpGrafanaSuiteDashboardTree_ProjectsMatchedStrategiesIntoDashboardNodes(t *testing.T) {
	resolver := newTestMetricCapabilityContractResolver(t)
	ctx := platformTenant.WithTenant(context.Background(), "tenant-test")

	result, err := resolver.ResolveStrategySetTargetGrafanaDashboardTreeMaterializationDryRun(
		ctx,
		"set-1",
		dto.SnmpStrategySetTargetGrafanaDashboardTreeDryRunRequest{
			TargetPart:       "target-a",
			DashboardVariant: "snmp.switch.operations",
		},
	)
	if err != nil {
		t.Fatalf("tree dry run: %v", err)
	}

	if len(result.Nodes) < 3 {
		t.Fatalf("expected root plus strategy dashboards, got %#v", result.Nodes)
	}
	if result.Nodes[0].Role != "root" {
		t.Fatalf("expected suite root dashboard first, got %#v", result.Nodes[0])
	}
	if strings.TrimSpace(result.Nodes[1].OwnerStrategyID) == "" {
		t.Fatalf("expected first strategy dashboard to have owner strategy id, got %#v", result.Nodes[1])
	}
}

func TestSnmpGrafanaSuiteDashboardTree_UsesStrategySelectionNotIndependentDashboardSelection(t *testing.T) {
	resolver := newTestMetricCapabilityContractResolver(t)
	ctx := platformTenant.WithTenant(context.Background(), "tenant-test")

	result, err := resolver.ResolveStrategySetTargetGrafanaDashboardTreeMaterializationDryRun(
		ctx,
		"set-1",
		dto.SnmpStrategySetTargetGrafanaDashboardTreeDryRunRequest{
			TargetPart:       "target-b",
			DashboardVariant: "snmp.switch.operations",
		},
	)
	if err != nil {
		t.Fatalf("tree dry run: %v", err)
	}

	if !reflect.DeepEqual(result.MatchedStrategyIDs, []string{"huawei-general-snmp", "snmp-network-monitoring-copy"}) {
		t.Fatalf("expected dashboard tree to reuse matched strategy ids, got %#v", result.MatchedStrategyIDs)
	}
}
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
go test ./app/platform/service/impl -run 'TestSnmpGrafanaSuiteDashboardTree_(ProjectsMatchedStrategiesIntoDashboardNodes|UsesStrategySelectionNotIndependentDashboardSelection)' -count=1
```

Expected:

- FAIL because the current path still centers on class-level shared dashboards and does not yet expose the full suite-root + strategy-node semantics as the primary path.

- [ ] **Step 3: Add the explicit metric-scope assertions**

Extend the failing tests so every dashboard node must carry explicit metric-display scope:

```go
func TestSnmpGrafanaSuiteDashboardTree_ExposesExplicitMetricScopePerDashboardNode(t *testing.T) {
	resolver := newTestMetricCapabilityContractResolver(t)
	ctx := platformTenant.WithTenant(context.Background(), "tenant-test")

	result, err := resolver.ResolveStrategySetTargetGrafanaDashboardTreeMaterializationDryRun(
		ctx,
		"set-1",
		dto.SnmpStrategySetTargetGrafanaDashboardTreeDryRunRequest{
			TargetPart:       "target-a",
			DashboardVariant: "snmp.switch.operations",
		},
	)
	if err != nil {
		t.Fatalf("tree dry run: %v", err)
	}

	for _, node := range result.Nodes {
		if len(node.PanelFamilies) == 0 {
			t.Fatalf("expected explicit metric-display scope for node %#v", node)
		}
	}
}
```

- [ ] **Step 4: Run the expanded failing set**

Run:

```bash
go test ./app/platform/service/impl -run 'TestSnmpGrafanaSuiteDashboardTree_(ProjectsMatchedStrategiesIntoDashboardNodes|UsesStrategySelectionNotIndependentDashboardSelection|ExposesExplicitMetricScopePerDashboardNode)' -count=1
```

Expected:

- FAIL because `PanelFamilies` does not yet exist in the DTO and current tree planning still infers too much late from flat assembly.

- [ ] **Step 5: Commit the red tests**

```bash
git add /OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver_test.go
git commit -m "test: lock suite strategy dashboard tree semantics"
```

## Task 2: Add An Explicit Suite/Strategy Dashboard Tree Module

**Files:**
- Create: `/OneOPS/OneOps/app/platform/service/impl/snmp_grafana_suite_dashboard_tree_module.go`
- Modify: `/OneOPS/OneOps/app/platform/dto/snmp_metric_contract.go`
- Modify: `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver.go`
- Test: `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver_test.go`

- [ ] **Step 1: Add the DTO fields for explicit metric scope**

In `/OneOPS/OneOps/app/platform/dto/snmp_metric_contract.go`, extend `SnmpGrafanaDashboardTreeNodePreview`:

```go
type SnmpGrafanaDashboardTreeNodePreview struct {
	NodeKey             string   `json:"node_key"`
	Role                string   `json:"role"`
	OwnerStrategyID     string   `json:"owner_strategy_id,omitempty"`
	PanelFamilies       []string `json:"panel_families,omitempty"`
	MetricGroupKeys     []string `json:"metric_group_keys,omitempty"`
	DisplayScopeSummary string   `json:"display_scope_summary,omitempty"`
	SlotOwners          []string `json:"slot_owners,omitempty"`
	UnownedFamilies     []string `json:"unowned_families,omitempty"`
	UnownedSlotCount    *int     `json:"unowned_slot_count,omitempty"`
	ParentNodeKey       string   `json:"parent_node_key,omitempty"`
	// existing fields stay as-is
}
```

- [ ] **Step 2: Create the new suite dashboard tree projection module**

Create `/OneOPS/OneOps/app/platform/service/impl/snmp_grafana_suite_dashboard_tree_module.go` with a focused interface:

```go
package impl

import (
	"context"
	"sort"
	"strings"

	"github.com/netxops/OneOps/app/platform/dto"
)

type snmpGrafanaSuiteDashboardTreeModule struct {
	resolver *MetricCapabilityContractResolver
}

func newSnmpGrafanaSuiteDashboardTreeModule(resolver *MetricCapabilityContractResolver) *snmpGrafanaSuiteDashboardTreeModule {
	return &snmpGrafanaSuiteDashboardTreeModule{resolver: resolver}
}

func (m *snmpGrafanaSuiteDashboardTreeModule) project(
	ctx context.Context,
	strategySetID string,
	materialized *snmpGrafanaSwitchDashboardGeneration,
	dashboardVariant string,
) ([]snmpGrafanaDashboardTreeNodePlan, error) {
	expanded, err := m.resolver.expandSnmpGrafanaTreeItemContracts(ctx, strategySetID, materialized)
	if err != nil {
		return nil, err
	}
	return m.resolver.planSnmpGrafanaDashboardTree(
		ctx,
		strategySetID,
		expanded,
		snmpGrafanaStrategyIDsFromItemContracts(expanded.ItemContracts),
		dashboardVariant,
	)
}

func snmpGrafanaPanelFamilies(bindings []dto.SnmpGrafanaPanelBindingPreview) []string {
	seen := map[string]struct{}{}
	out := make([]string, 0, len(bindings))
	for _, binding := range bindings {
		family := strings.TrimSpace(binding.MetricGroupKey)
		if family == "" {
			family = strings.TrimSpace(binding.PanelKey)
		}
		if family == "" {
			continue
		}
		if _, ok := seen[family]; ok {
			continue
		}
		seen[family] = struct{}{}
		out = append(out, family)
	}
	sort.Strings(out)
	return out
}
```

- [ ] **Step 3: Wire node preview conversion through the new explicit scope fields**

In `snmpGrafanaDashboardTreeNodePreviews(...)`, set:

```go
PanelFamilies:       snmpGrafanaPanelFamilies(node.PanelBindings),
MetricGroupKeys:     snmpGrafanaSortedGroupKeys(node.GroupKeys),
DisplayScopeSummary: snmpGrafanaDashboardNodeScopeSummary(node.Role, node.PanelBindings, node.GroupKeys),
```

and add helpers:

```go
func snmpGrafanaSortedGroupKeys(groupKeys map[string]struct{}) []string
func snmpGrafanaDashboardNodeScopeSummary(role string, bindings []dto.SnmpGrafanaPanelBindingPreview, groupKeys map[string]struct{}) string
```

- [ ] **Step 4: Route tree dry-run/save generation through the new module**

Replace direct planning calls in `/OneOPS/OneOps/app/platform/service/impl/snmp_grafana_switch_dashboard_service.go`:

```go
module := newSnmpGrafanaSuiteDashboardTreeModule(s.resolver)
nodes, err := module.project(ctx, strategySetID, treeMaterialized, resolvedVariant)
```

instead of open-coded `expandSnmpGrafanaTreeItemContracts + planSnmpGrafanaDashboardTree`.

- [ ] **Step 5: Run the semantic tests**

Run:

```bash
go test ./app/platform/service/impl -run 'TestSnmpGrafanaSuiteDashboardTree_(ProjectsMatchedStrategiesIntoDashboardNodes|UsesStrategySelectionNotIndependentDashboardSelection|ExposesExplicitMetricScopePerDashboardNode)' -count=1
```

Expected:

- PASS

- [ ] **Step 6: Commit**

```bash
git add /OneOPS/OneOps/app/platform/dto/snmp_metric_contract.go /OneOPS/OneOps/app/platform/service/impl/snmp_grafana_suite_dashboard_tree_module.go /OneOPS/OneOps/app/platform/service/impl/snmp_grafana_switch_dashboard_service.go /OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver.go /OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver_test.go
git commit -m "feat: project strategy selection into suite dashboard tree"
```

## Task 3: Make Tree Generation The Primary Save Path

**Files:**
- Modify: `/OneOPS/OneOps/app/platform/service/impl/snmp_grafana_switch_dashboard_persistence_service.go`
- Modify: `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver.go`
- Test: `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver_test.go`
- Test: `/OneOPS/OneOps/app/platform/api/teleabs_metric_contract_http_test.go`

- [ ] **Step 1: Write the failing persistence tests**

Add tests that lock the new primary semantics:

```go
func TestMetricCapabilityContractResolverSavesSuiteRootAndStrategyDashboards(t *testing.T) {
	resolver := newTestMetricCapabilityContractResolver(t)
	ctx := platformTenant.WithTenant(context.Background(), "tenant-test")

	saved, err := resolver.ResolveStrategySetTargetGrafanaDashboardTreeSaveByTarget(
		ctx,
		"set-1",
		dto.SnmpStrategySetTargetGrafanaDashboardTreeSaveByTargetRequest{
			TargetPart:       "target-a",
			DashboardVariant: "snmp.switch.operations",
		},
	)
	if err != nil {
		t.Fatalf("tree save: %v", err)
	}

	if len(saved.Nodes) < 3 {
		t.Fatalf("expected root plus strategy dashboards, got %#v", saved.Nodes)
	}
	if saved.Nodes[0].Role != "root" {
		t.Fatalf("expected root node first, got %#v", saved.Nodes[0])
	}
	if saved.Nodes[1].DashboardName == saved.Nodes[0].DashboardName {
		t.Fatalf("strategy dashboard must not collapse into root dashboard, got %#v", saved.Nodes)
	}
}
```

- [ ] **Step 2: Run the failing persistence test**

Run:

```bash
go test ./app/platform/service/impl -run 'TestMetricCapabilityContractResolverSavesSuiteRootAndStrategyDashboards' -count=1
```

Expected:

- FAIL if save path still treats flat shared dashboard as the main product object.

- [ ] **Step 3: Make flat save delegate to tree save semantics**

In `/OneOPS/OneOps/app/platform/service/impl/snmp_grafana_switch_dashboard_persistence_service.go`, change `saveDashboardByTarget(...)` to:

```go
func (s *snmpGrafanaSwitchDashboardPersistenceService) saveDashboardByTarget(
	ctx context.Context,
	strategySetID string,
	request dto.SnmpStrategySetTargetGrafanaDashboardSaveByTargetRequest,
) (*dto.SnmpStrategySetTargetGrafanaDashboardSaveByTargetResponse, error) {
	treeSaved, err := s.saveTreeByTarget(
		ctx,
		strategySetID,
		dto.SnmpStrategySetTargetGrafanaDashboardTreeSaveByTargetRequest{
			TargetPart:       request.TargetPart,
			DashboardVariant: request.DashboardVariant,
		},
	)
	if err != nil {
		return nil, err
	}
	root := snmpGrafanaFindRootNodePreview(treeSaved.Nodes)
	if root == nil {
		return nil, fmt.Errorf("root dashboard node not found after tree save")
	}
	return &dto.SnmpStrategySetTargetGrafanaDashboardSaveByTargetResponse{
		StrategySetID:   treeSaved.StrategySetID,
		Baseline:        treeSaved.Baseline,
		Target:          treeSaved.Target,
		Source:          treeSaved.Source,
		ItemContracts:   treeSaved.ItemContracts,
		EffectiveContract: treeSaved.EffectiveContract,
		DashboardCode:   root.DashboardCode,
		DashboardName:   root.DashboardName,
		DashboardUID:    "",
		Saved:           treeSaved.Saved,
		TargetBindingSaved: true,
	}, nil
}
```

- [ ] **Step 4: Keep root + strategy rows visible in tree save/query history**

Make sure:

```go
GetStrategySetGrafanaDashboardTreeSaveSummaryByBatch(...)
ListStrategySetGrafanaDashboardTreeSaveBatches(...)
```

continue returning node-level rows, but with the new `PanelFamilies`, `MetricGroupKeys`, and `DisplayScopeSummary` populated.

- [ ] **Step 5: Run service and API persistence tests**

Run:

```bash
go test ./app/platform/service/impl -run 'TestMetricCapabilityContractResolver(SavesSuiteRootAndStrategyDashboards|SavesStrategySetGrafanaDashboardByTarget|SavesStrategySetGrafanaDashboardTreeByTarget|GetsStrategySetGrafanaDashboardTreeSaveSummaryByBatch|ListsStrategySetGrafanaDashboardTreeSaveBatches)' -count=1
go test ./app/platform/api -run 'TestTeleabsAPI_(SaveStrategySetGrafanaDashboardByTarget_HTTP|SaveStrategySetGrafanaDashboardTreeByTarget_HTTP|GetStrategySetGrafanaDashboardTreeSaveSummaryByBatch_HTTP|ListStrategySetGrafanaDashboardTreeSaveBatches_HTTP)' -count=1
```

Expected:

- PASS

- [ ] **Step 6: Commit**

```bash
git add /OneOPS/OneOps/app/platform/service/impl/snmp_grafana_switch_dashboard_persistence_service.go /OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver.go /OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver_test.go /OneOPS/OneOps/app/platform/api/teleabs_metric_contract_http_test.go
git commit -m "feat: make suite strategy dashboard tree the primary save path"
```

## Task 4: Demote Class Baselines To Generation Floors

**Files:**
- Modify: `/OneOPS/OneOps/app/platform/service/impl/snmp_grafana_target_class_module.go`
- Modify: `/OneOPS/OneOps/app/platform/service/impl/snmp_grafana_switch_baseline_module.go`
- Test: `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver_test.go`

- [ ] **Step 1: Write the failing class-baseline demotion tests**

Add tests that prove dashboard selection is derived from strategy selection and class baseline only affects reusable floors:

```go
func TestSnmpGrafanaTargetClassModule_DoesNotReplaceStrategyDashboardSelection(t *testing.T) {
	resolver := newTestMetricCapabilityContractResolver(t)
	ctx := platformTenant.WithTenant(context.Background(), "tenant-test")

	baseline := newSnmpGrafanaSwitchBaselineModule(resolver).resolveForStrategyIDs(
		ctx,
		[]string{"huawei-general-snmp"},
		"snmp.switch.operations",
	)
	if strings.TrimSpace(baseline.ClassBaseline) == "" {
		t.Fatalf("expected class baseline floor")
	}

	result, err := resolver.ResolveStrategySetTargetGrafanaDashboardTreeMaterializationDryRun(
		ctx,
		"set-1",
		dto.SnmpStrategySetTargetGrafanaDashboardTreeDryRunRequest{
			TargetPart:       "target-a",
			DashboardVariant: "snmp.switch.operations",
		},
	)
	if err != nil {
		t.Fatalf("tree dry run: %v", err)
	}

	if len(result.Nodes) <= 1 {
		t.Fatalf("class baseline must not collapse strategy dashboards into one root node")
	}
}
```

- [ ] **Step 2: Run the failing baseline demotion test**

Run:

```bash
go test ./app/platform/service/impl -run 'TestSnmpGrafanaTargetClassModule_DoesNotReplaceStrategyDashboardSelection' -count=1
```

Expected:

- FAIL if baseline resolution is still effectively acting as a dashboard-side business selector.

- [ ] **Step 3: Refactor target-class and baseline modules to expose “generation floor only” language**

Refactor `snmp_grafana_target_class_module.go` and `snmp_grafana_switch_baseline_module.go` around:

```go
type snmpGrafanaGenerationFloor struct {
	ClassBaseline   snmpGrafanaClassBaseline
	VariantBaseline snmpGrafanaVariantBaseline
	Template        snmpGrafanaDashboardTemplateResolution
}

func (m *snmpGrafanaTargetClassModule) resolveGenerationFloor(...) (snmpGrafanaGenerationFloor, error)
```

and keep `Reason` values descriptive of floor selection, not business identity.

- [ ] **Step 4: Run baseline tests and tree tests together**

Run:

```bash
go test ./app/platform/service/impl -run 'TestSnmpGrafanaTargetClassModule_DoesNotReplaceStrategyDashboardSelection|TestSnmpGrafanaSuiteDashboardTree_.*|TestMetricCapabilityContractResolverSavesSuiteRootAndStrategyDashboards' -count=1
```

Expected:

- PASS

- [ ] **Step 5: Commit**

```bash
git add /OneOPS/OneOps/app/platform/service/impl/snmp_grafana_target_class_module.go /OneOPS/OneOps/app/platform/service/impl/snmp_grafana_switch_baseline_module.go /OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver_test.go
git commit -m "refactor: demote class baselines to generation floors"
```

## Task 5: Rebuild Quick Env Around Root + Strategy Dashboards

**Files:**
- Modify: `/OneOPS/quick_env/scripts/ensure_snmp_dashboard_instances.sh`
- Modify: `/OneOPS/quick_env/tests/test_seed_template_guard.py`
- Test: `/OneOPS/quick_env/tests/test_seed_template_guard.py`

- [ ] **Step 1: Write the failing quick env expectations**

Add guard assertions for visible dashboard rows:

```python
def test_snmp_dashboard_tree_seed_guard_requires_root_and_strategy_rows(self):
    content = self.seed_script_text
    self.assertIn("OneOPS SNMP Switch Ops", content)
    self.assertIn("Huawei通用SNMP网络监控策略", content)
    self.assertIn("SNMP网络监控策略 (副本)", content)
```

- [ ] **Step 2: Run the failing guard**

Run:

```bash
python3 -m unittest quick_env.tests.test_seed_template_guard
```

Expected:

- FAIL if quick env still only ensures flat shared switch rows.

- [ ] **Step 3: Update ensure script to materialize and keep visible root + strategy dashboards**

In `/OneOPS/quick_env/scripts/ensure_snmp_dashboard_instances.sh`, add functions like:

```bash
ensure_suite_root_dashboard() {
  :
}

ensure_strategy_dashboard_reference() {
  local strategy_name="$1"
  :
}

ensure_switch_dashboard_tree_rows() {
  ensure_suite_root_dashboard
  ensure_strategy_dashboard_reference "Huawei通用SNMP网络监控策略"
  ensure_strategy_dashboard_reference "SNMP网络监控策略 (副本)"
}
```

and call them from the main ensure flow after service restart / API readiness checks.

- [ ] **Step 4: Run quick env guard and ensure script**

Run:

```bash
python3 -m unittest quick_env.tests.test_seed_template_guard
bash /OneOPS/quick_env/scripts/ensure_snmp_dashboard_instances.sh
```

Expected:

- unit test PASS
- script exits 0 and reports root + strategy dashboard rows ensured

- [ ] **Step 5: Commit**

```bash
git add /OneOPS/quick_env/scripts/ensure_snmp_dashboard_instances.sh /OneOPS/quick_env/tests/test_seed_template_guard.py
git commit -m "chore: rebuild quick env around suite strategy dashboards"
```

## Task 6: Docs, Verification, And Handoff

**Files:**
- Modify: `/OneOPS/docs/superpowers/plans/2026-06-14-snmp-definition-runtime-closure-correction.md`
- Modify: `/OneOPS/docs/superpowers/handovers/2026-06-10-snmp-metric-groups-dashboard-family-handoff.md`

- [ ] **Step 1: Update the correction plan with the new completed closure**

Add a section recording that:

```text
suite root now determines root dashboard
matched strategy now determines strategy dashboard node
dashboard selection is now a projection of strategy selection
every dashboard node now carries explicit metric-display responsibility
```

- [ ] **Step 2: Update the handoff with operator-facing consequences**

Document that:

- `OneOPS SNMP Switch Ops` is the suite root
- `Huawei通用SNMP网络监控策略` and `SNMP网络监控策略 (副本)` are visible strategy dashboards
- target binding no longer implies flat-dashboard ownership

- [ ] **Step 3: Run full verification**

Run:

```bash
go test ./app/platform/service/impl -run 'TestSnmpGrafanaSuiteDashboardTree_.*|TestMetricCapabilityContractResolver(SavesSuiteRootAndStrategyDashboards|SavesStrategySetGrafanaDashboardByTarget|SavesStrategySetGrafanaDashboardTreeByTarget|GetsStrategySetGrafanaDashboardTreeSaveSummaryByBatch|ListsStrategySetGrafanaDashboardTreeSaveBatches)|TestSnmpGrafanaTargetClassModule_DoesNotReplaceStrategyDashboardSelection' -count=1
go test ./app/platform/api -run 'TestTeleabsAPI_(SaveStrategySetGrafanaDashboardByTarget_HTTP|SaveStrategySetGrafanaDashboardTreeByTarget_HTTP|GetStrategySetGrafanaDashboardTreeSaveSummaryByBatch_HTTP|ListStrategySetGrafanaDashboardTreeSaveBatches_HTTP)' -count=1
python3 -m unittest quick_env.tests.test_seed_template_guard
git -C /OneOPS/OneOps diff --check
git -C /OneOPS/quick_env diff --check
git -C /OneOPS/docs diff --check
```

Expected:

- all tests PASS
- all `diff --check` commands PASS with no whitespace errors

- [ ] **Step 4: Commit**

```bash
git add /OneOPS/docs/superpowers/plans/2026-06-14-snmp-definition-runtime-closure-correction.md /OneOPS/docs/superpowers/handovers/2026-06-10-snmp-metric-groups-dashboard-family-handoff.md
git commit -m "docs: record suite strategy dashboard tree closure"
```

## Self-Review

### Spec coverage

- Suite decides root: covered in Tasks 1-3.
- Strategy decides node: covered in Tasks 1-3.
- Dashboard selection follows strategy selection: covered in Tasks 1, 2, and 4.
- Dashboard tree mirrors strategy tree: covered in Tasks 2 and 3.
- Each dashboard has explicit metric-display responsibility: covered in Tasks 1 and 2.
- Quick env exposes real usable root + strategy dashboards: covered in Task 5.

### Placeholder scan

- No `TODO`, `TBD`, or “similar to above” placeholders remain.
- Every test/run/commit step has exact commands.

### Type consistency

- `PanelFamilies`, `MetricGroupKeys`, and `DisplayScopeSummary` are introduced first in DTO work, then consumed in persistence/query/tests.
- `snmpGrafanaSuiteDashboardTreeModule.project(...)` is introduced before service integration tasks mention it.

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-06-14-snmp-suite-strategy-dashboard-tree-closure-plan.md`. Two execution options:

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?
