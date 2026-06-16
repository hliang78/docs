# SNMP Baseline Selection First-Cut Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Introduce a first-cut class-baseline selection path so switch dashboard generation can choose `current switch baseline` or `routing-capable switch baseline` from target class intent plus matched strategy responsibility, without using runtime data presence as a gate.

**Architecture:** Keep the current dashboard generation flow and `dashboard_variant` contract intact, but add one small definition-layer selection layer before panel-definition resolution. The first cut stays backend-only, uses helper functions inside the existing resolver, and changes generation structure only for switch-class baselines. Runtime panel state and push-time behavior remain untouched.

**Tech Stack:** Go backend in `/OneOPS/OneOps`, existing Teleabs/Grafana resolver flow in `app/platform/service/impl`, existing target-context and panel-definition helpers, focused Go tests, docs in `/OneOPS/docs/superpowers`.

---

## Scope Lock

Allowed in this first cut:

- add one internal baseline-selection helper for switch generation;
- distinguish `current switch baseline` vs `routing-capable switch baseline`;
- use matched strategy responsibility as the trigger;
- keep `dashboard_variant` names unchanged;
- keep runtime state handling unchanged.

Not allowed in this first cut:

- no runtime `has_data / no_data / not_exposed` logic;
- no new API fields;
- no UI changes;
- no per-device dashboard branching;
- no new root-owned routing rollups;
- no expansion beyond switch-family generation.

## File Structure

Backend expected to change:

- Modify: `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver.go`
- Modify: `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver_test.go`

Docs expected to change:

- Modify: `/OneOPS/docs/superpowers/handovers/2026-06-10-snmp-metric-groups-dashboard-family-handoff.md`
- Modify: `/OneOPS/docs/superpowers/plans/2026-06-14-snmp-definition-runtime-closure-correction.md`

Reference docs to keep open while implementing:

- `/OneOPS/docs/superpowers/specs/2026-06-14-snmp-class-baseline-generation-rule.md`
- `/OneOPS/docs/superpowers/specs/2026-06-14-snmp-routing-capable-switch-baseline.md`
- `/OneOPS/docs/superpowers/specs/2026-06-14-snmp-switch-baseline-selection-rule.md`
- `/OneOPS/docs/superpowers/specs/2026-06-14-snmp-routing-responsibility-mapping-table.md`

## Canonical Decisions

These decisions are fixed for this first cut:

- baseline selection happens at generation time, before panel-definition resolution;
- baseline selection uses target profile plus matched strategy responsibility;
- runtime data presence does not affect baseline selection;
- routing responsibility is narrow and currently means only:
  - `l3_route_table.*`
  - `routing_bgp.*`
  - `routing_ospf.*`
- if routing responsibility is absent, generation stays on the current switch baseline.

## Task 1: Freeze The Selection Rule With Failing Tests

**Files:**

- Modify: `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver_test.go`

- [ ] **Step 1: Add a failing unit test for baseline selection without routing responsibility**

Add a focused helper-level test:

```go
func TestSnmpGrafanaSelectSwitchBaseline_Current(t *testing.T) {
	target := dto.SnmpMetricResolvedTargetContext{
		Context: dto.SnmpMetricStrategySetContractOptions{
			CatalogName:  "SWITCH",
			Manufacturer: "Huawei",
			PlatformName: "VRP",
			DeviceModel:  "S5735",
		},
	}
	itemContracts := []dto.SnmpMetricStrategySetItemContract{
		{
			StrategyID: "switching",
			Contract: dto.SnmpMetricContractEnvelope{
				Version: 1,
				MetricGroups: []dto.SnmpMetricGroupContract{
					{
						GroupKey: "interface_basic",
						PanelSpecs: []dto.SnmpPanelSpecContract{
							{PanelKey: "interface_basic.utilization"},
						},
					},
				},
			},
		},
	}

	got := snmpGrafanaSelectSwitchBaseline(target, itemContracts)
	if got != snmpGrafanaClassBaselineCurrentSwitch {
		t.Fatalf("expected current switch baseline, got %q", got)
	}
}
```

- [ ] **Step 2: Add a failing unit test for routing-capable selection**

Add the routing trigger case:

```go
func TestSnmpGrafanaSelectSwitchBaseline_RoutingCapable(t *testing.T) {
	target := dto.SnmpMetricResolvedTargetContext{
		Context: dto.SnmpMetricStrategySetContractOptions{
			CatalogName:  "SWITCH",
			Manufacturer: "Huawei",
			PlatformName: "VRP",
			DeviceModel:  "S5735",
		},
	}
	itemContracts := []dto.SnmpMetricStrategySetItemContract{
		{
			StrategyID: "routing",
			Contract: dto.SnmpMetricContractEnvelope{
				Version: 1,
				MetricGroups: []dto.SnmpMetricGroupContract{
					{
						GroupKey: "routing_summary",
						PanelSpecs: []dto.SnmpPanelSpecContract{
							{PanelKey: "l3_route_table.ipv4_count"},
						},
					},
				},
			},
		},
	}

	got := snmpGrafanaSelectSwitchBaseline(target, itemContracts)
	if got != snmpGrafanaClassBaselineRoutingCapableSwitch {
		t.Fatalf("expected routing-capable switch baseline, got %q", got)
	}
}
```

- [ ] **Step 3: Add a failing unit test that topology evidence does not trigger routing**

Add the regression guard:

```go
func TestSnmpGrafanaSelectSwitchBaseline_TopologyEvidenceDoesNotTriggerRouting(t *testing.T) {
	target := dto.SnmpMetricResolvedTargetContext{
		Context: dto.SnmpMetricStrategySetContractOptions{
			CatalogName:  "SWITCH",
			Manufacturer: "Huawei",
			PlatformName: "VRP",
			DeviceModel:  "S5735",
		},
	}
	itemContracts := []dto.SnmpMetricStrategySetItemContract{
		{
			StrategyID: "topology",
			Contract: dto.SnmpMetricContractEnvelope{
				Version: 1,
				MetricGroups: []dto.SnmpMetricGroupContract{
					{
						GroupKey: "l3_arp_table",
						PanelSpecs: []dto.SnmpPanelSpecContract{
							{PanelKey: "l3_arp_table.summary"},
						},
					},
				},
			},
		},
	}

	got := snmpGrafanaSelectSwitchBaseline(target, itemContracts)
	if got != snmpGrafanaClassBaselineCurrentSwitch {
		t.Fatalf("expected topology-only target to stay on current switch baseline, got %q", got)
	}
}
```

- [ ] **Step 4: Run the focused tests to verify RED**

Run:

```bash
cd /OneOPS/OneOps
go test ./app/platform/service/impl -run 'TestSnmpGrafanaSelectSwitchBaseline.*' -count=1
```

Expected: FAIL until the new selection helpers exist.

## Task 2: Add Internal Baseline Selection Helpers

**Files:**

- Modify: `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver.go`

- [ ] **Step 1: Add the internal baseline constants**

Add near the other SNMP Grafana constants:

```go
type snmpGrafanaClassBaseline string

const (
	snmpGrafanaClassBaselineCurrentSwitch         snmpGrafanaClassBaseline = "switch.current"
	snmpGrafanaClassBaselineRoutingCapableSwitch  snmpGrafanaClassBaseline = "switch.routing_capable"
)
```

- [ ] **Step 2: Add a helper that detects routing responsibility from matched strategy contracts**

Add a narrow helper:

```go
func snmpGrafanaStrategyCarriesRoutingResponsibility(itemContracts []dto.SnmpMetricStrategySetItemContract) bool {
	for _, item := range itemContracts {
		for _, group := range item.Contract.MetricGroups {
			for _, spec := range group.PanelSpecs {
				panelKey := strings.TrimSpace(spec.PanelKey)
				switch {
				case strings.HasPrefix(panelKey, "l3_route_table."):
					return true
				case strings.HasPrefix(panelKey, "routing_bgp."):
					return true
				case strings.HasPrefix(panelKey, "routing_ospf."):
					return true
				}
			}
		}
	}
	return false
}
```

- [ ] **Step 3: Add the main switch baseline selection helper**

Add:

```go
func snmpGrafanaSelectSwitchBaseline(target dto.SnmpMetricResolvedTargetContext, itemContracts []dto.SnmpMetricStrategySetItemContract) snmpGrafanaClassBaseline {
	if snmpGrafanaStrategyCarriesRoutingResponsibility(itemContracts) {
		return snmpGrafanaClassBaselineRoutingCapableSwitch
	}
	return snmpGrafanaClassBaselineCurrentSwitch
}
```

- [ ] **Step 4: Run focused tests to verify GREEN**

Run:

```bash
cd /OneOPS/OneOps
go test ./app/platform/service/impl -run 'TestSnmpGrafanaSelectSwitchBaseline.*' -count=1
```

Expected: PASS.

## Task 3: Thread Baseline Selection Into Switch Panel Definition Resolution

**Files:**

- Modify: `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver.go`
- Modify: `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver_test.go`

- [ ] **Step 1: Add a new panel-definition entry point that accepts the selected baseline**

Add a helper:

```go
func snmpGrafanaPanelDefinitionsForTargetAndBaseline(target dto.SnmpMetricResolvedTargetContext, baseline snmpGrafanaClassBaseline) snmpGrafanaDashboardTemplateResolution {
	switch baseline {
	case snmpGrafanaClassBaselineRoutingCapableSwitch:
		return snmpGrafanaRoutingCapableSwitchPanelDefinitions(target)
	default:
		return snmpGrafanaPanelDefinitionsForTarget(target)
	}
}
```

- [ ] **Step 2: Implement the routing-capable baseline as an additive overlay**

Add a helper that starts from the current switch definitions and appends only the routing families:

```go
func snmpGrafanaRoutingCapableSwitchPanelDefinitions(target dto.SnmpMetricResolvedTargetContext) snmpGrafanaDashboardTemplateResolution {
	base := snmpGrafanaPanelDefinitionsForTarget(target)
	defs := append([]snmpGrafanaPanelDefinition{}, base.Definitions...)

	defs = append(defs,
		snmpGrafanaPanelDefinition{
			PanelKey:        "l3_route_table.ipv4_count",
			DashboardVariant:"snmp.switch.operations",
			SectionKey:      "routing_summary",
			DisplayIntent:   "summary_card",
			RenderPolicy:    "routing_summary",
			MetricGroupKey:  "routing_summary",
		},
		snmpGrafanaPanelDefinition{
			PanelKey:        "l3_route_table.ipv6_count",
			DashboardVariant:"snmp.switch.operations",
			SectionKey:      "routing_summary",
			DisplayIntent:   "summary_card",
			RenderPolicy:    "routing_summary",
			MetricGroupKey:  "routing_summary",
		},
		snmpGrafanaPanelDefinition{
			PanelKey:        "routing_bgp.neighbor_total",
			DashboardVariant:"snmp.switch.operations",
			SectionKey:      "routing_summary",
			DisplayIntent:   "summary_card",
			RenderPolicy:    "routing_summary",
			MetricGroupKey:  "routing_summary",
		},
		snmpGrafanaPanelDefinition{
			PanelKey:        "routing_bgp.established_total",
			DashboardVariant:"snmp.switch.operations",
			SectionKey:      "routing_summary",
			DisplayIntent:   "summary_card",
			RenderPolicy:    "routing_summary",
			MetricGroupKey:  "routing_summary",
		},
		snmpGrafanaPanelDefinition{
			PanelKey:        "routing_ospf.neighbor_total",
			DashboardVariant:"snmp.switch.operations",
			SectionKey:      "routing_summary",
			DisplayIntent:   "summary_card",
			RenderPolicy:    "routing_summary",
			MetricGroupKey:  "routing_summary",
		},
		snmpGrafanaPanelDefinition{
			PanelKey:        "routing_ospf.full_total",
			DashboardVariant:"snmp.switch.operations",
			SectionKey:      "routing_summary",
			DisplayIntent:   "summary_card",
			RenderPolicy:    "routing_summary",
			MetricGroupKey:  "routing_summary",
		},
	)

	base.Definitions = defs
	return base
}
```

- [ ] **Step 3: Use the selected baseline in the switch materialization path**

In the by-target switch materialization flow, after matched strategy contracts are known and before panel-definition resolution, thread:

```go
baseline := snmpGrafanaSelectSwitchBaseline(target, itemContracts)
definitions := snmpGrafanaPanelDefinitionsForTargetAndBaseline(target, baseline)
```

Replace the old direct call path only for switch-family generation. Do not change non-switch paths.

- [ ] **Step 4: Add a failing-then-passing integration test for routing-capable panel inclusion**

Add a focused materialization test that uses matched routing responsibility and asserts:

```go
if !containsString(materialized.Materialization.RenderedPanelKeys, "l3_route_table.ipv4_count") {
	t.Fatalf("expected routing-capable baseline to render ipv4 route count, got %#v", materialized.Materialization.RenderedPanelKeys)
}
```

Also assert the topology-only case does **not** include the routing family:

```go
if containsString(materialized.Materialization.RenderedPanelKeys, "routing_bgp.neighbor_total") {
	t.Fatalf("did not expect topology-only baseline to render routing protocol panels, got %#v", materialized.Materialization.RenderedPanelKeys)
}
```

- [ ] **Step 5: Run focused tests**

Run:

```bash
cd /OneOPS/OneOps
go test ./app/platform/service/impl -run 'TestSnmpGrafanaSelectSwitchBaseline.*|TestMetricCapabilityContractResolver.*Routing.*|TestMetricCapabilityContractResolver.*GrafanaDashboardMaterialization.*' -count=1
```

Expected: PASS.

## Task 4: Keep Owner Behavior Narrow And Explicit

**Files:**

- Modify: `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver_test.go`

- [ ] **Step 1: Add a focused owner assertion for the first routing-capable path**

In the routing-capable materialization test, assert the first-cut rule:

```go
binding := bindingsByPanel["l3_route_table.ipv4_count"]
if binding.OwnerKind != "strategy" {
	t.Fatalf("expected routing family to stay strategy-owned, got %#v", binding)
}
```

Keep the first cut narrow:

- assert `strategy`
- do not introduce root-routing expectations

- [ ] **Step 2: Add a guard that topology evidence still stays outside the routing trigger**

In the topology evidence path, assert:

```go
if containsString(materialized.Materialization.RenderedPanelKeys, "l3_route_table.ipv4_count") {
	t.Fatalf("topology evidence must not promote baseline into routing-capable path")
}
```

- [ ] **Step 3: Run focused tests**

Run:

```bash
cd /OneOPS/OneOps
go test ./app/platform/service/impl -run 'TestSnmpGrafanaSelectSwitchBaseline.*|TestMetricCapabilityContractResolver.*Routing.*' -count=1
```

Expected: PASS.

## Task 5: Update Docs And Handoff

**Files:**

- Modify: `/OneOPS/docs/superpowers/handovers/2026-06-10-snmp-metric-groups-dashboard-family-handoff.md`
- Modify: `/OneOPS/docs/superpowers/plans/2026-06-14-snmp-definition-runtime-closure-correction.md`

- [ ] **Step 1: Record where baseline selection now lives in code**

Add one short handoff note that the first-cut backend path now selects:

- `switch.current`
- `switch.routing_capable`

from matched strategy responsibility, not runtime data presence.

- [ ] **Step 2: Record scope lock**

Document that the first cut:

- does not add new API shape;
- does not change runtime panel-state logic;
- does not add per-device branching.

- [ ] **Step 3: Run docs diff check**

Run:

```bash
git -C /OneOPS/docs diff --check
```

Expected: no output.

## Final Verification

- [ ] **Step 1: Run the full focused backend suite**

Run:

```bash
cd /OneOPS/OneOps
go test ./app/platform/service/impl -run 'TestSnmpGrafanaSelectSwitchBaseline.*|TestMetricCapabilityContractResolver.*Routing.*|TestMetricCapabilityContractResolver.*GrafanaDashboardMaterialization.*|TestMetricCapabilityContractResolver.*DashboardTree.*' -count=1
```

Expected: PASS.

- [ ] **Step 2: Run diff checks**

Run:

```bash
git -C /OneOPS/OneOps diff --check
git -C /OneOPS/docs diff --check
```

Expected: no output.

- [ ] **Step 3: Commit**

Run:

```bash
git -C /OneOPS/OneOps add app/platform/service/impl/metric_capability_contract_resolver.go app/platform/service/impl/metric_capability_contract_resolver_test.go
git -C /OneOPS/docs add docs/superpowers/handovers/2026-06-10-snmp-metric-groups-dashboard-family-handoff.md docs/superpowers/plans/2026-06-14-snmp-definition-runtime-closure-correction.md
git -C /OneOPS/OneOps commit -m "feat: add first-cut switch baseline selection"
git -C /OneOPS/docs commit -m "docs: record switch baseline selection first cut"
```

Expected: two clean commits, one per repo.
