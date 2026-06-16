# SNMP Baseline Module Closure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Finish the next closure phase by turning `ClassBaseline / VariantBaseline / baseline selection` into one explicit internal switch-baseline module, so baseline logic no longer lives partly in the large resolver and partly in generator/service callers.

**Architecture:** Keep current API behavior, response fields, and switch/routing-capable generation behavior unchanged. The change is structural: introduce a dedicated switch-baseline module that owns class-baseline types, baseline resolution, template/panel-set selection, and strategy-ID-to-baseline derivation, then make generator/service/history paths consume that boundary instead of directly calling scattered resolver helpers.

**Tech Stack:** Go backend in `/OneOPS/OneOps`, existing SNMP/Grafana resolver flow, focused service/API tests, docs in `/OneOPS/docs/superpowers`.

---

## Scope Lock

Allowed in this batch:

- extract baseline-related types and helpers out of `metric_capability_contract_resolver.go`;
- add one dedicated internal switch-baseline module file;
- keep `switch.current` and `switch.routing_capable` behavior unchanged;
- keep `baseline.class_baseline / variant_baseline / reason` response shape unchanged;
- update generator/service/history callers to consume the module.

Not allowed in this batch:

- no new dashboard families;
- no UI changes;
- no runtime `has_data / no_data / not_exposed` logic;
- no route-data gating;
- no per-device dashboard branching;
- no save/persistence redesign beyond baseline caller rewiring.

## File Structure

Backend expected to change:

- Create: `/OneOPS/OneOps/app/platform/service/impl/snmp_grafana_switch_baseline_module.go`
- Modify: `/OneOPS/OneOps/app/platform/service/impl/snmp_grafana_switch_dashboard_generator.go`
- Modify: `/OneOPS/OneOps/app/platform/service/impl/snmp_grafana_switch_dashboard_service.go`
- Modify: `/OneOPS/OneOps/app/platform/service/impl/snmp_grafana_switch_dashboard_persistence_service.go`
- Modify: `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver.go`
- Modify: `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver_test.go`
- Modify: `/OneOPS/OneOps/app/platform/api/teleabs_metric_contract_http_test.go`

Docs expected to change:

- Modify: `/OneOPS/docs/superpowers/plans/2026-06-14-snmp-definition-runtime-closure-correction.md`
- Modify: `/OneOPS/docs/superpowers/handovers/2026-06-10-snmp-metric-groups-dashboard-family-handoff.md`

Reference docs to keep open:

- `/OneOPS/docs/superpowers/specs/2026-06-14-snmp-class-baseline-generation-rule.md`
- `/OneOPS/docs/superpowers/specs/2026-06-14-snmp-routing-capable-switch-baseline.md`
- `/OneOPS/docs/superpowers/specs/2026-06-14-snmp-switch-baseline-selection-rule.md`
- `/OneOPS/docs/superpowers/specs/2026-06-14-snmp-routing-responsibility-mapping-table.md`
- `/OneOPS/docs/superpowers/plans/2026-06-14-snmp-switch-dashboard-final-closure-batch.md`

## Canonical Decisions

These decisions are fixed for this batch:

- baseline resolution belongs to the definition layer, not runtime state;
- `ClassBaseline` and `VariantBaseline` remain short internal concepts;
- current supported class baselines stay:
  - `switch.current`
  - `switch.routing_capable`
- routing responsibility remains narrow:
  - `l3_route_table.*`
  - `routing_bgp.*`
  - `routing_ospf.*`
- tree history baseline derivation continues to use matched strategy IDs, but the derivation logic must move behind the baseline module.

## Task 1: Freeze The Baseline Module Contract With Failing Tests

**Files:**
- Modify: `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver_test.go`

- [ ] **Step 1: Add a failing module-level test for current baseline resolution**

Add:

```go
func TestSnmpGrafanaSwitchBaselineModuleResolvesCurrent(t *testing.T) {
	module := newSnmpGrafanaSwitchBaselineModule(nil)
	target := dto.SnmpMetricResolvedTargetContext{}
	items := []dto.SnmpMetricStrategySetItemContract{
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

	generation, err := module.resolve(target, items, "snmp.switch.operations")
	if err != nil {
		t.Fatalf("resolve current baseline through module: %v", err)
	}
	if generation.ClassBaseline != snmpGrafanaClassBaselineCurrentSwitch {
		t.Fatalf("expected current class baseline, got %q", generation.ClassBaseline)
	}
	if generation.Baseline.ClassBaseline != "switch.current" || generation.Baseline.Reason != "current_switch_default" {
		t.Fatalf("unexpected current baseline resolution: %#v", generation.Baseline)
	}
}
```

- [ ] **Step 2: Add a failing module-level test for routing-capable baseline resolution**

Add:

```go
func TestSnmpGrafanaSwitchBaselineModuleResolvesRoutingCapable(t *testing.T) {
	module := newSnmpGrafanaSwitchBaselineModule(nil)
	target := dto.SnmpMetricResolvedTargetContext{}
	items := []dto.SnmpMetricStrategySetItemContract{
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

	generation, err := module.resolve(target, items, "snmp.switch.operations")
	if err != nil {
		t.Fatalf("resolve routing baseline through module: %v", err)
	}
	if generation.ClassBaseline != snmpGrafanaClassBaselineRoutingCapableSwitch {
		t.Fatalf("expected routing-capable class baseline, got %q", generation.ClassBaseline)
	}
	if generation.Baseline.ClassBaseline != "switch.routing_capable" || generation.Baseline.Reason != "routing_responsibility" {
		t.Fatalf("unexpected routing baseline resolution: %#v", generation.Baseline)
	}
}
```

- [ ] **Step 3: Add a failing module-level test for strategy-ID baseline derivation**

Add:

```go
func TestSnmpGrafanaSwitchBaselineModuleResolvesBaselineForStrategyIDs(t *testing.T) {
	module := newSnmpGrafanaSwitchBaselineModule(&MetricCapabilityContractResolver{
		StrategySrv: metricContractResolverHuaweiClosedLoopStrategySrvForTest(),
	})

	got := module.resolveForStrategyIDs(context.Background(), []string{"huawei-s5735-switch"}, "snmp.switch.operations")
	if got.ClassBaseline != "switch.current" || got.VariantBaseline != "snmp.switch.operations" {
		t.Fatalf("unexpected strategy-id baseline resolution: %#v", got)
	}
}
```

- [ ] **Step 4: Run focused tests to verify RED**

Run:

```bash
cd /OneOPS/OneOps
go test ./app/platform/service/impl -run 'TestSnmpGrafanaSwitchBaselineModuleResolves(Current|RoutingCapable|BaselineForStrategyIDs)' -count=1
```

Expected: FAIL because the baseline module does not exist yet.

## Task 2: Create The Dedicated Switch Baseline Module

**Files:**
- Create: `/OneOPS/OneOps/app/platform/service/impl/snmp_grafana_switch_baseline_module.go`

- [ ] **Step 1: Add the internal module type and result**

Create:

```go
package impl

import (
	"context"
	"strings"

	"github.com/netxops/OneOps/app/platform/dto"
)

type snmpGrafanaSwitchBaselineModule struct {
	resolver *MetricCapabilityContractResolver
}

type snmpGrafanaSwitchBaselineGeneration struct {
	ClassBaseline snmpGrafanaClassBaseline
	Baseline      dto.SnmpGrafanaBaselineResolution
	Template      snmpGrafanaDashboardTemplateResolution
}

func newSnmpGrafanaSwitchBaselineModule(resolver *MetricCapabilityContractResolver) *snmpGrafanaSwitchBaselineModule {
	return &snmpGrafanaSwitchBaselineModule{resolver: resolver}
}
```

- [ ] **Step 2: Move routing responsibility detection and baseline selection into the module**

Add:

```go
func (m *snmpGrafanaSwitchBaselineModule) carriesRoutingResponsibility(itemContracts []dto.SnmpMetricStrategySetItemContract) bool {
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

func (m *snmpGrafanaSwitchBaselineModule) selectClassBaseline(target dto.SnmpMetricResolvedTargetContext, itemContracts []dto.SnmpMetricStrategySetItemContract) snmpGrafanaClassBaseline {
	_ = target
	if m.carriesRoutingResponsibility(itemContracts) {
		return snmpGrafanaClassBaselineRoutingCapableSwitch
	}
	return snmpGrafanaClassBaselineCurrentSwitch
}
```

- [ ] **Step 3: Move baseline resolution and panel-definition selection into the module**

Add:

```go
func (m *snmpGrafanaSwitchBaselineModule) resolve(target dto.SnmpMetricResolvedTargetContext, itemContracts []dto.SnmpMetricStrategySetItemContract, dashboardVariant string) (snmpGrafanaSwitchBaselineGeneration, error) {
	classBaseline := m.selectClassBaseline(target, itemContracts)
	baseline := dto.SnmpGrafanaBaselineResolution{
		ClassBaseline:   string(classBaseline),
		VariantBaseline: normalizeSnmpGrafanaDashboardVariant(dashboardVariant),
		Reason:          "current_switch_default",
	}
	if classBaseline == snmpGrafanaClassBaselineRoutingCapableSwitch {
		baseline.Reason = "routing_responsibility"
	}
	template, err := m.resolveTemplate(target, dashboardVariant, classBaseline)
	if err != nil {
		return snmpGrafanaSwitchBaselineGeneration{}, err
	}
	return snmpGrafanaSwitchBaselineGeneration{
		ClassBaseline: classBaseline,
		Baseline:      baseline,
		Template:      template,
	}, nil
}
```

- [ ] **Step 4: Add strategy-ID derivation into the module**

Add:

```go
func (m *snmpGrafanaSwitchBaselineModule) resolveForStrategyIDs(ctx context.Context, strategyIDs []string, dashboardVariant string) dto.SnmpGrafanaBaselineResolution {
	resolution := dto.SnmpGrafanaBaselineResolution{
		ClassBaseline:   string(snmpGrafanaClassBaselineCurrentSwitch),
		VariantBaseline: normalizeSnmpGrafanaDashboardVariant(dashboardVariant),
		Reason:          "current_switch_default",
	}
	normalizedStrategyIDs := cloneTrimmedStrings(strategyIDs)
	if m == nil || m.resolver == nil || len(normalizedStrategyIDs) == 0 {
		return resolution
	}
	itemContracts := make([]dto.SnmpMetricStrategySetItemContract, 0, len(normalizedStrategyIDs))
	for _, strategyID := range normalizedStrategyIDs {
		contractResolution, err := m.resolver.ResolveStrategyContract(ctx, strategyID)
		if err != nil || contractResolution == nil {
			continue
		}
		itemContracts = append(itemContracts, dto.SnmpMetricStrategySetItemContract{
			StrategyID: strategyID,
			Enabled:    true,
			Contract:   contractResolution.EffectiveContract,
		})
	}
	if len(itemContracts) == 0 {
		return resolution
	}
	generation, err := m.resolve(dto.SnmpMetricResolvedTargetContext{}, itemContracts, dashboardVariant)
	if err != nil {
		return resolution
	}
	return generation.Baseline
}
```

- [ ] **Step 5: Run focused tests to verify GREEN**

Run:

```bash
cd /OneOPS/OneOps
go test ./app/platform/service/impl -run 'TestSnmpGrafanaSwitchBaselineModuleResolves(Current|RoutingCapable|BaselineForStrategyIDs)' -count=1
```

Expected: PASS.

## Task 3: Make Generator, Service, And History Callers Use The Module

**Files:**
- Modify: `/OneOPS/OneOps/app/platform/service/impl/snmp_grafana_switch_dashboard_generator.go`
- Modify: `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver.go`

- [ ] **Step 1: Replace generator-local baseline selection with the new module**

In `snmp_grafana_switch_dashboard_generator.go`, replace the baseline logic with:

```go
func (g *snmpGrafanaSwitchDashboardGenerator) resolveSwitchGeneration(ctx context.Context, target dto.SnmpMetricResolvedTargetContext, itemContracts []dto.SnmpMetricStrategySetItemContract, dashboardVariant string) (snmpGrafanaSwitchGenerationResolution, error) {
	baselineGeneration, err := newSnmpGrafanaSwitchBaselineModule(g.resolver).resolve(target, itemContracts, dashboardVariant)
	if err != nil {
		return snmpGrafanaSwitchGenerationResolution{}, err
	}
	return snmpGrafanaSwitchGenerationResolution{
		ClassBaseline: baselineGeneration.ClassBaseline,
		Baseline:      baselineGeneration.Baseline,
		Template:      baselineGeneration.Template,
	}, nil
}
```

- [ ] **Step 2: Replace strategy-ID baseline derivation with the new module**

In `metric_capability_contract_resolver.go`, change:

```go
func (r *MetricCapabilityContractResolver) resolveSnmpGrafanaBaselineForStrategyIDs(ctx context.Context, strategyIDs []string, dashboardVariant string) dto.SnmpGrafanaBaselineResolution {
	return newSnmpGrafanaSwitchBaselineModule(r).resolveForStrategyIDs(ctx, strategyIDs, dashboardVariant)
}
```

- [ ] **Step 3: Remove duplicated baseline helpers from the large resolver file**

Delete or move these out of `metric_capability_contract_resolver.go` once callers are switched:

- `snmpGrafanaStrategyCarriesRoutingResponsibility`
- `snmpGrafanaSelectSwitchBaseline`
- `snmpGrafanaResolveSwitchBaseline`

- [ ] **Step 4: Run focused generation/history tests**

Run:

```bash
cd /OneOPS/OneOps
go test ./app/platform/service/impl -run 'TestSnmpGrafanaSwitchBaselineModuleResolves(Current|RoutingCapable|BaselineForStrategyIDs)|TestSnmpGrafanaSwitchDashboardGeneratorResolvesDashboardGeneration_Current|TestMetricCapabilityContractResolverResolvesSnmpGrafanaSwitchDashboardGeneration_(Current|RoutingCapable)|TestMetricCapabilityContractResolver(GetsStrategySetGrafanaDashboardTreeSaveSummaryByBatch|ListsStrategySetGrafanaDashboardTreeSaveBatches)' -count=1
```

Expected: PASS.

## Task 4: Move Template/Panel-Set Resolution Behind The Same Baseline Module

**Files:**
- Modify: `/OneOPS/OneOps/app/platform/service/impl/snmp_grafana_switch_baseline_module.go`
- Modify: `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver.go`
- Modify: `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver_test.go`

- [ ] **Step 1: Move baseline-aware template resolution into the module**

Add to the module:

```go
func (m *snmpGrafanaSwitchBaselineModule) resolveTemplate(target dto.SnmpMetricResolvedTargetContext, dashboardVariant string, baseline snmpGrafanaClassBaseline) (snmpGrafanaDashboardTemplateResolution, error) {
	if m == nil || m.resolver == nil {
		return snmpGrafanaDashboardTemplateResolution{}, fmt.Errorf("switch baseline module is not initialized")
	}
	return m.resolver.resolveSnmpGrafanaDashboardTemplateResolutionWithBaseline(context.Background(), target, dashboardVariant, baseline)
}
```

Then tighten it so `context.Context` is passed explicitly instead of using `context.Background()`.

- [ ] **Step 2: Add a focused test that current vs routing-capable template selection still differs only by baseline**

Add:

```go
func TestSnmpGrafanaSwitchBaselineModuleResolvesRoutingTemplateDelta(t *testing.T) {
	target := dto.SnmpMetricResolvedTargetContext{
		Context: dto.SnmpMetricStrategySetContractOptions{
			CatalogName:      "SWITCH",
			ManufacturerName: "Huawei",
			PlatformName:     "VRP",
			DeviceModelName:  "S5735",
		},
	}
	module := newSnmpGrafanaSwitchBaselineModule(&MetricCapabilityContractResolver{})

	current, err := module.resolve(target, nil, "snmp.switch.operations")
	if err != nil {
		t.Fatalf("resolve current template: %v", err)
	}
	routing, err := module.resolve(target, []dto.SnmpMetricStrategySetItemContract{
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
	}, "snmp.switch.operations")
	if err != nil {
		t.Fatalf("resolve routing template: %v", err)
	}
	if current.Template.TemplateKey == routing.Template.TemplateKey {
		t.Fatalf("expected routing-capable baseline to resolve a distinct template key")
	}
}
```

- [ ] **Step 3: Run focused baseline/template tests**

Run:

```bash
cd /OneOPS/OneOps
go test ./app/platform/service/impl -run 'TestSnmpGrafanaSwitchBaselineModuleResolves(Current|RoutingCapable|BaselineForStrategyIDs|RoutingTemplateDelta)|TestSnmpGrafanaPanelDefinitionsForTargetAndBaseline_RoutingCapableAddsRoutingFamilies' -count=1
```

Expected: PASS.

## Task 5: Update Docs And Verify The Full Closure Phase

**Files:**
- Modify: `/OneOPS/docs/superpowers/plans/2026-06-14-snmp-definition-runtime-closure-correction.md`
- Modify: `/OneOPS/docs/superpowers/handovers/2026-06-10-snmp-metric-groups-dashboard-family-handoff.md`

- [ ] **Step 1: Record the new baseline-module boundary**

Document that the active internal split is now:

- resolver
- baseline module
- generator
- service
- persistence service

and that `ClassBaseline / VariantBaseline / baseline selection / baseline-for-strategyIDs / baseline-aware template selection` now live behind the baseline module.

- [ ] **Step 2: Run the complete focused backend verification**

Run:

```bash
cd /OneOPS/OneOps
go test ./app/platform/service/impl -run 'TestSnmpGrafanaSwitchBaselineModuleResolves(Current|RoutingCapable|BaselineForStrategyIDs|RoutingTemplateDelta)|TestSnmpGrafanaSwitchDashboard(PersistenceServiceSaves(Dashboard|Tree)_Current|ServiceResolves(DryRun|TreeDryRun)_Current|GeneratorResolvesDashboardGeneration_Current)|TestMetricCapabilityContractResolver(ResolvesSnmpGrafanaSwitchDashboardGeneration_(Current|RoutingCapable)|MaterializesStrategySetGrafanaDashboardTreeByTarget|SavesStrategySetGrafanaDashboardByTarget|SavesStrategySetGrafanaDashboardTreeByTarget|GetsStrategySetGrafanaDashboardTreeSaveSummaryByBatch|ListsStrategySetGrafanaDashboardTreeSaveBatches)' -count=1
go test ./app/platform/api -run 'TestTeleabsAPI_(MaterializeStrategySetGrafanaDashboardByTarget_HTTP|MaterializeStrategySetGrafanaDashboardTreeByTarget_HTTP|SaveStrategySetGrafanaDashboardTreeByTarget_HTTP|GetStrategySetGrafanaDashboardTreeSaveSummaryByBatch_HTTP|ListStrategySetGrafanaDashboardTreeSaveBatches_HTTP)' -count=1
git -C /OneOPS/OneOps diff --check
git -C /OneOPS/docs diff --check
```

Expected:

- both Go test commands PASS
- both `diff --check` commands return no output

## Self-Review

Spec coverage:

- closes the next structural phase after generator/service/persistence extraction;
- keeps current switch/routing-capable behavior intact;
- moves baseline logic into one explicit internal module;
- keeps history derivation and response `Baseline` behavior intact.

Placeholder scan:

- no `TODO`, `TBD`, or “similar to above” shortcuts remain;
- each task names exact files and exact commands.

Type consistency:

- continue using existing short names:
  - `ClassBaseline`
  - `VariantBaseline`
  - `Baseline`
  - `reason`
  - `switch.current`
  - `switch.routing_capable`
