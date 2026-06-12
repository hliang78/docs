# SNMP Grafana Screenshot Style Materializer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade the SNMP Grafana dry-run materializer from a flat seven-panel chart generator into a screenshot-inspired **network switch** operations dashboard variant that uses identity, KPI, hotspot, trend, composition, and evidence-style panels.

**Architecture:** Keep the existing strict by-target dry-run API and do not write `grafana_dashboard` rows or call Grafana sync. Add a switch-oriented panel catalog with `dashboard_variant`, `display_intent`, section metadata, render policy, grid positions, and Grafana query builders. The generated dashboard should render only panels supported by target capability/recording-rule data, while preserving panel binding traceability.

**Tech Stack:** Go service/API tests in `OneOps`; TypeScript smoke in `OneOPS-UI`; Grafana JSON using built-in panel types (`text`, `stat`, `timeseries`, `table`, `status-history`, `piechart`); VictoriaMetrics/PromQL recording-rule names from the existing SNMP recording-rule preview.

---

## Scope Lock

Implement only screenshot-style **switch dashboard dry-run materialization**:

```text
strategy_set_id + target_part
  -> strict target context
  -> StrategySetMatcher strategy selection
  -> effective SNMP metric capability contract
  -> panel capability preview
  -> recording rule preview
  -> screenshot-style Grafana dashboard JSON
  -> panel binding preview
```

Do not implement:

- `grafana_dashboard` persistence;
- `syncToGrafana`;
- dashboard diff;
- automatic publish;
- real alert/event/compliance data joins;
- Canvas/custom plugin port map;
- inventory-wide dashboard generation.

The first generated dashboard should focus on common SNMP data:

- device identity header from target context;
- CPU and memory stat tiles;
- CPU and memory trends;
- interface utilization top-N;
- interface status map via `status-history`;
- interface throughput trend;
- interface quality hotspot table;
- broadcast ratio when available.

Hardware, alert, event, routing, and compliance blocks must be omitted unless backed by real data or represented as clearly static demo-only text outside the product materializer.

This plan is not a generic SNMP dashboard template. It targets switch-like devices where interface table, port state, traffic, errors, discards, broadcast ratio, speed, and hardware module health are the primary operating surface. Routers, firewalls, load balancers, servers, BMC/OOB devices, and generic SNMP devices should use separate future variants or a smaller capability-driven fallback.

The most important implementation constraint is data-logic integration. The materializer must not introduce a parallel strategy matcher, vendor matcher, raw SNMP parser, or hand-written PromQL catalog. It must consume the same authoritative backend outputs that already exist:

```text
target
item_contracts[]
effective_contract
supports[]
support_summary
rule_group
rules[]
recording_rule_summary
```

Only the final `dashboard_json`, `panel_bindings[]`, and `materialization` summary are new presentation outputs.

## File Structure

Backend materializer:

- Modify `OneOps/app/platform/service/impl/metric_capability_contract_resolver.go`
  - Extend `snmpGrafanaPanelDefinition`.
  - Replace the flat panel loop with section-aware renderers.
  - Add Grafana target/query helper functions.
  - Add identity/header and KPI panels.

Backend DTO:

- Modify `OneOps/app/platform/dto/snmp_metric_contract.go`
  - Extend panel binding preview with optional `section_key`, `display_intent`, and `render_policy`.
  - Extend materialization summary with optional rendered/skipped panel keys.

Backend tests:

- Modify `OneOps/app/platform/service/impl/metric_capability_contract_resolver_test.go`
  - Add screenshot-style materializer tests.
  - Keep existing dry-run tests passing.

Frontend smoke:

- Modify `OneOPS-UI/scripts/snmp-strategy-set-grafana-dashboard-materialization-dry-run-smoke.ts`
  - Assert response types include the new optional fields.

Docs:

- Modify `docs/superpowers/handovers/2026-06-10-snmp-metric-groups-dashboard-family-handoff.md`
  - Record the new Grafana direction and verification.

---

### Task 1: Extend DTOs For Section-Aware Panel Bindings

**Files:**

- Modify: `OneOps/app/platform/dto/snmp_metric_contract.go`

- [ ] **Step 1: Add optional binding metadata fields**

In `SnmpGrafanaPanelBindingPreview`, add these fields after `Title`:

```go
DashboardVariant string `json:"dashboard_variant,omitempty"`
SectionKey    string `json:"section_key,omitempty"`
DisplayIntent string `json:"display_intent,omitempty"`
VisualType    string `json:"visual_type,omitempty"`
RenderPolicy  string `json:"render_policy,omitempty"`
```

- [ ] **Step 2: Add rendered/skipped keys to materialization summary**

In `SnmpGrafanaDashboardMaterializationSummary`, add:

```go
RenderedPanelKeys []string `json:"rendered_panel_keys,omitempty"`
SkippedPanelKeys  []string `json:"skipped_panel_keys,omitempty"`
```

- [ ] **Step 3: Run DTO compile check**

Run:

```bash
cd OneOps
go test ./app/platform/dto -run '^$' -count=1
```

Expected: PASS.

### Task 2: Expand The Internal Panel Definition Model

**Files:**

- Modify: `OneOps/app/platform/service/impl/metric_capability_contract_resolver.go`

- [ ] **Step 1: Replace `snmpGrafanaPanelDefinition` fields**

Change the struct to:

```go
type snmpGrafanaPanelDefinition struct {
	PanelKey       string
	DashboardVariant string
	Title          string
	SectionKey     string
	SectionTitle   string
	DisplayIntent  string
	VisualType     string
	RenderPolicy   string
	MetricGroupKey string
	CapabilityKeys []string
	MetricKeys     []string
	GridX          int
	GridY          int
	GridW          int
	GridH          int
	Unit           string
}
```

- [ ] **Step 2: Add stable render policy constants**

Near the struct, add:

```go
const (
	snmpGrafanaRenderAlways                  = "always"
	snmpGrafanaRenderSupportedOrConfigDriven = "supported_or_config_driven"
)
```

- [ ] **Step 3: Add stable display intent constants**

Add:

```go
const (
	snmpGrafanaSwitchDashboardVariant = "snmp.switch.operations"
	snmpGrafanaIntentIdentity    = "identity"
	snmpGrafanaIntentState       = "state"
	snmpGrafanaIntentTrend       = "trend"
	snmpGrafanaIntentHotspot     = "hotspot"
	snmpGrafanaIntentComposition = "composition"
)
```

- [ ] **Step 4: Run focused compile**

Run:

```bash
cd OneOps
go test ./app/platform/service/impl -run '^$' -count=1
```

Expected: PASS.

### Task 3: Write Screenshot-Style Materializer Test First

**Files:**

- Modify: `OneOps/app/platform/service/impl/metric_capability_contract_resolver_test.go`

- [ ] **Step 1: Add test `TestMetricCapabilityContractResolverMaterializesScreenshotStyleGrafanaDashboard`**

Add a test that builds a switch target:

- target device code `SW-1`;
- target context catalog name `SWITCH`;
- full default supports for CPU, memory, traffic, status, speed, quality, and broadcast;
- recording rules for all common SNMP records.

Assert:

```go
if dashboard["title"] != "OneOPS SNMP SW-1" {
	t.Fatalf("unexpected dashboard title: %#v", dashboard["title"])
}
if summary.PanelCount < 10 {
	t.Fatalf("expected screenshot-style dashboard to render at least 10 panels, got %d", summary.PanelCount)
}
if !containsString(summary.RenderedPanelKeys, "device.identity") {
	t.Fatalf("expected identity panel to render: %#v", summary.RenderedPanelKeys)
}
for _, want := range []string{"system_basic.cpu.stat", "system_basic.cpu.trend", "interface_basic.utilization", "interface_basic.port_state", "interface_basic.quality_hotspots"} {
	if !containsString(summary.RenderedPanelKeys, want) {
		t.Fatalf("expected rendered panel %s, got %#v", want, summary.RenderedPanelKeys)
	}
}
types := grafanaPanelTypesForTest(dashboard)
for _, want := range []string{"text", "stat", "timeseries", "table", "status-history"} {
	if !containsString(types, want) {
		t.Fatalf("expected panel type %s, got %#v", want, types)
	}
}
for _, binding := range bindings {
	if binding.PanelKey == "" || binding.SectionKey == "" || binding.DisplayIntent == "" || binding.RenderPolicy == "" {
		t.Fatalf("binding missing screenshot metadata: %#v", binding)
	}
	if binding.DashboardVariant != "snmp.switch.operations" {
		t.Fatalf("binding missing switch dashboard variant: %#v", binding)
	}
}
```

- [ ] **Step 2: Add test helpers**

Add helpers near existing materializer tests:

```go
func containsString(values []string, want string) bool {
	for _, value := range values {
		if value == want {
			return true
		}
	}
	return false
}

func grafanaPanelTypesForTest(dashboard map[string]interface{}) []string {
	rawPanels, _ := dashboard["panels"].([]interface{})
	seen := map[string]struct{}{}
	out := make([]string, 0)
	for _, raw := range rawPanels {
		panel, _ := raw.(map[string]interface{})
		panelType, _ := panel["type"].(string)
		if panelType == "" {
			continue
		}
		if _, ok := seen[panelType]; ok {
			continue
		}
		seen[panelType] = struct{}{}
		out = append(out, panelType)
	}
	sort.Strings(out)
	return out
}
```

- [ ] **Step 3: Run failing test**

Run:

```bash
cd OneOps
go test ./app/platform/service/impl -run TestMetricCapabilityContractResolverMaterializesScreenshotStyleGrafanaDashboard -count=1
```

Expected: FAIL because the current materializer only produces the old flat seven-panel layout and has no new binding metadata.

### Task 3A: Protect Strategy-Set Data Logic Integration

**Files:**

- Modify: `OneOps/app/platform/service/impl/metric_capability_contract_resolver_test.go`

- [ ] **Step 1: Extend by-target Grafana resolver test**

In `TestMetricCapabilityContractResolverMaterializesStrategySetGrafanaDashboardByTarget`, assert that the generated switch dashboard still carries upstream strategy-set facts:

```go
if materialized.Target.DeviceCode != "SW-1" {
	t.Fatalf("unexpected target: %#v", materialized.Target)
}
if len(materialized.ItemContracts) != 1 || materialized.ItemContracts[0].StrategyID != "h3c-device" {
	t.Fatalf("expected matched strategy item to flow into materialization: %#v", materialized.ItemContracts)
}
if len(materialized.EffectiveContract.MetricGroups) == 0 {
	t.Fatalf("expected effective contract to flow into materialization")
}
if materialized.SupportSummary.Total == 0 {
	t.Fatalf("expected support summary to flow into materialization: %#v", materialized.SupportSummary)
}
if len(materialized.Rules) == 0 {
	t.Fatalf("expected recording rules to flow into materialization")
}
for _, binding := range materialized.PanelBindings {
	if !containsString(binding.StrategyIDs, "h3c-device") {
		t.Fatalf("binding lost strategy traceability: %#v", binding)
	}
	if binding.MetricGroupKey == "" || len(binding.SelectedCapabilityKeys) == 0 || len(binding.RecordNames) == 0 {
		t.Fatalf("binding lost metric/record traceability: %#v", binding)
	}
}
```

- [ ] **Step 2: Run integration test**

Run:

```bash
cd OneOps
go test ./app/platform/service/impl -run TestMetricCapabilityContractResolverMaterializesStrategySetGrafanaDashboardByTarget -count=1
```

Expected: PASS after screenshot-style binding metadata is implemented. The resolver call chain must still go through `ResolveStrategySetTargetPanelCapabilityPreview(...)` and `ResolveStrategySetTargetRecordingRulePreview(...)`.

### Task 4: Implement Screenshot-Style Panel Catalog

**Files:**

- Modify: `OneOps/app/platform/service/impl/metric_capability_contract_resolver.go`

- [ ] **Step 1: Replace `snmpGrafanaPanelDefinitions()`**

Return definitions in this order:

```go
return []snmpGrafanaPanelDefinition{
	{
		PanelKey:      "device.identity",
		DashboardVariant: snmpGrafanaSwitchDashboardVariant,
		Title:         "Device Identity",
		SectionKey:    "identity",
		SectionTitle:  "Device",
		DisplayIntent: snmpGrafanaIntentIdentity,
		VisualType:    "text",
		RenderPolicy:  snmpGrafanaRenderAlways,
		GridX:         0, GridY: 0, GridW: 24, GridH: 3,
	},
	{
		PanelKey:       "system_basic.cpu.stat",
		DashboardVariant: snmpGrafanaSwitchDashboardVariant,
		Title:          "CPU Now",
		SectionKey:     "triage",
		DisplayIntent:  snmpGrafanaIntentState,
		VisualType:     "stat",
		RenderPolicy:   snmpGrafanaRenderSupportedOrConfigDriven,
		MetricGroupKey: "system_basic",
		CapabilityKeys: []string{"cpu_usage_direct"},
		MetricKeys:     []string{"cpu_usage_direct"},
		GridX:          0, GridY: 3, GridW: 4, GridH: 4,
		Unit:           "percentunit",
	},
	{
		PanelKey:       "system_basic.memory.stat",
		DashboardVariant: snmpGrafanaSwitchDashboardVariant,
		Title:          "Memory Now",
		SectionKey:     "triage",
		DisplayIntent:  snmpGrafanaIntentState,
		VisualType:     "stat",
		RenderPolicy:   snmpGrafanaRenderSupportedOrConfigDriven,
		MetricGroupKey: "system_basic",
		CapabilityKeys: []string{"memory_usage_direct"},
		MetricKeys:     []string{"memory_usage_direct"},
		GridX:          4, GridY: 3, GridW: 4, GridH: 4,
		Unit:           "percentunit",
	},
	{
		PanelKey:       "interface_basic.utilization",
		DashboardVariant: snmpGrafanaSwitchDashboardVariant,
		Title:          "Interface Utilization Top 10",
		SectionKey:     "interfaces",
		DisplayIntent:  snmpGrafanaIntentHotspot,
		VisualType:     "table",
		RenderPolicy:   snmpGrafanaRenderSupportedOrConfigDriven,
		MetricGroupKey: "interface_basic",
		CapabilityKeys: []string{"if_in_rate", "if_out_rate", "if_speed_bps"},
		MetricKeys:     []string{"if_in_rate", "if_out_rate", "if_speed_bps"},
		GridX:          0, GridY: 7, GridW: 12, GridH: 8,
		Unit:           "percentunit",
	},
	{
		PanelKey:       "interface_basic.port_state",
		DashboardVariant: snmpGrafanaSwitchDashboardVariant,
		Title:          "Port State Map",
		SectionKey:     "interfaces",
		DisplayIntent:  snmpGrafanaIntentState,
		VisualType:     "status-history",
		RenderPolicy:   snmpGrafanaRenderSupportedOrConfigDriven,
		MetricGroupKey: "interface_basic",
		CapabilityKeys: []string{"if_oper_status"},
		MetricKeys:     []string{"if_oper_status"},
		GridX:          12, GridY: 7, GridW: 12, GridH: 8,
	},
	{
		PanelKey:       "system_basic.cpu_memory.trend",
		DashboardVariant: snmpGrafanaSwitchDashboardVariant,
		Title:          "CPU / Memory Trend",
		SectionKey:     "resources",
		DisplayIntent:  snmpGrafanaIntentTrend,
		VisualType:     "timeseries",
		RenderPolicy:   snmpGrafanaRenderSupportedOrConfigDriven,
		MetricGroupKey: "system_basic",
		CapabilityKeys: []string{"cpu_usage_direct", "memory_usage_direct"},
		MetricKeys:     []string{"cpu_usage_direct", "memory_usage_direct"},
		GridX:          0, GridY: 15, GridW: 12, GridH: 8,
		Unit:           "percentunit",
	},
	{
		PanelKey:       "interface_basic.throughput",
		DashboardVariant: snmpGrafanaSwitchDashboardVariant,
		Title:          "Traffic Throughput",
		SectionKey:     "traffic",
		DisplayIntent:  snmpGrafanaIntentTrend,
		VisualType:     "timeseries",
		RenderPolicy:   snmpGrafanaRenderSupportedOrConfigDriven,
		MetricGroupKey: "interface_basic",
		CapabilityKeys: []string{"if_in_rate", "if_out_rate"},
		MetricKeys:     []string{"if_in_rate", "if_out_rate"},
		GridX:          12, GridY: 15, GridW: 12, GridH: 8,
		Unit:           "bps",
	},
	{
		PanelKey:       "interface_basic.quality_hotspots",
		DashboardVariant: snmpGrafanaSwitchDashboardVariant,
		Title:          "Interface Quality Hotspots",
		SectionKey:     "interfaces",
		DisplayIntent:  snmpGrafanaIntentHotspot,
		VisualType:     "table",
		RenderPolicy:   snmpGrafanaRenderSupportedOrConfigDriven,
		MetricGroupKey: "interface_basic",
		CapabilityKeys: []string{"if_in_error_rate", "if_out_error_rate", "if_in_discard_rate", "if_out_discard_rate"},
		MetricKeys:     []string{"if_in_error_rate", "if_out_error_rate", "if_in_discard_rate", "if_out_discard_rate"},
		GridX:          0, GridY: 23, GridW: 12, GridH: 8,
		Unit:           "pps",
	},
	{
		PanelKey:       "interface_basic.broadcast",
		DashboardVariant: snmpGrafanaSwitchDashboardVariant,
		Title:          "Broadcast Ratio",
		SectionKey:     "traffic",
		DisplayIntent:  snmpGrafanaIntentComposition,
		VisualType:     "timeseries",
		RenderPolicy:   snmpGrafanaRenderSupportedOrConfigDriven,
		MetricGroupKey: "interface_basic",
		CapabilityKeys: []string{"if_in_broadcast_ratio", "if_out_broadcast_ratio"},
		MetricKeys:     []string{"if_in_broadcast_ratio", "if_out_broadcast_ratio"},
		GridX:          12, GridY: 23, GridW: 12, GridH: 8,
		Unit:           "percentunit",
	},
}
```

- [ ] **Step 2: Keep old seven-panel keys out of product output**

Do not keep old keys like `system_basic.cpu` as generated product panels. The screenshot-style catalog replaces them with `system_basic.cpu.stat` and `system_basic.cpu_memory.trend`.

- [ ] **Step 3: Run screenshot test**

Run:

```bash
cd OneOps
go test ./app/platform/service/impl -run TestMetricCapabilityContractResolverMaterializesScreenshotStyleGrafanaDashboard -count=1
```

Expected: still FAIL until renderers are implemented.

### Task 5: Implement Panel Renderers

**Files:**

- Modify: `OneOps/app/platform/service/impl/metric_capability_contract_resolver.go`

- [ ] **Step 1: Split panel creation into helper**

Add:

```go
func snmpGrafanaBuildPanel(def snmpGrafanaPanelDefinition, panelID int, target dto.SnmpMetricResolvedTargetContext, targets []interface{}) map[string]interface{} {
	panel := map[string]interface{}{
		"id":      panelID,
		"title":   def.Title,
		"type":    snmpGrafanaPanelType(def.VisualType),
		"targets": targets,
		"gridPos": map[string]interface{}{
			"h": def.GridH,
			"w": def.GridW,
			"x": def.GridX,
			"y": def.GridY,
		},
		"fieldConfig": map[string]interface{}{
			"defaults": snmpGrafanaFieldDefaults(def),
			"overrides": []interface{}{},
		},
		"options": snmpGrafanaPanelOptions(def, target),
	}
	if def.VisualType == "text" {
		panel["targets"] = []interface{}{}
	}
	return panel
}
```

- [ ] **Step 2: Add field defaults**

Add:

```go
func snmpGrafanaFieldDefaults(def snmpGrafanaPanelDefinition) map[string]interface{} {
	defaults := map[string]interface{}{}
	if strings.TrimSpace(def.Unit) != "" {
		defaults["unit"] = strings.TrimSpace(def.Unit)
	}
	defaults["thresholds"] = map[string]interface{}{
		"mode": "absolute",
		"steps": []interface{}{
			map[string]interface{}{"color": "green", "value": nil},
			map[string]interface{}{"color": "orange", "value": 0.7},
			map[string]interface{}{"color": "red", "value": 0.9},
		},
	}
	return defaults
}
```

- [ ] **Step 3: Add panel options**

Add:

```go
func snmpGrafanaPanelOptions(def snmpGrafanaPanelDefinition, target dto.SnmpMetricResolvedTargetContext) map[string]interface{} {
	switch def.VisualType {
	case "text":
		return map[string]interface{}{
			"mode": "markdown",
			"content": snmpGrafanaDeviceIdentityMarkdown(target),
		}
	case "stat":
		return map[string]interface{}{
			"reduceOptions": map[string]interface{}{"values": false, "calcs": []interface{}{"lastNotNull"}, "fields": ""},
			"orientation": "auto",
			"textMode": "auto",
			"colorMode": "background",
			"graphMode": "area",
			"justifyMode": "auto",
		}
	case "status-history":
		return map[string]interface{}{
			"showValue": "never",
			"legend": map[string]interface{}{"showLegend": true, "displayMode": "list", "placement": "bottom"},
			"rowHeight": 0.8,
		}
	case "table":
		return map[string]interface{}{"showHeader": true, "cellHeight": "sm"}
	default:
		return map[string]interface{}{
			"legend": map[string]interface{}{"showLegend": true, "displayMode": "list", "placement": "bottom"},
			"tooltip": map[string]interface{}{"mode": "multi"},
		}
	}
}
```

- [ ] **Step 4: Add identity markdown helper**

Add:

```go
func snmpGrafanaDeviceIdentityMarkdown(target dto.SnmpMetricResolvedTargetContext) string {
	ctx := target.Context
	deviceCode := firstNonEmptyString(target.DeviceCode, target.TargetPart, target.DeviceID)
	return fmt.Sprintf("## %s  `%s`\\nCatalog `%s`  Vendor/Platform `%s / %s`  Model `%s`  Version `%s`",
		deviceCode,
		firstNonEmptyString(ctx.CatalogName, ctx.CatalogID, "SNMP Device"),
		firstNonEmptyString(ctx.CatalogName, ctx.CatalogID, "-"),
		firstNonEmptyString(ctx.ManufacturerName, "-"),
		firstNonEmptyString(ctx.PlatformName, "-"),
		firstNonEmptyString(ctx.DeviceModelName, "-"),
		firstNonEmptyString(ctx.SystemVersion, "-"),
	)
}
```

If `firstNonEmptyString` does not exist in this file, add:

```go
func firstNonEmptyString(values ...string) string {
	for _, value := range values {
		if trimmed := strings.TrimSpace(value); trimmed != "" {
			return trimmed
		}
	}
	return ""
}
```

- [ ] **Step 5: Run screenshot test**

Run:

```bash
cd OneOps
go test ./app/platform/service/impl -run TestMetricCapabilityContractResolverMaterializesScreenshotStyleGrafanaDashboard -count=1
```

Expected: may still FAIL until query rendering is updated.

### Task 6: Implement Screenshot Query Builders

**Files:**

- Modify: `OneOps/app/platform/service/impl/metric_capability_contract_resolver.go`

- [ ] **Step 1: Add record lookup helper**

Add:

```go
func snmpGrafanaRecordForCapability(rulesByCapability map[string]dto.SnmpRecordingRulePreviewRule, capabilityKey string) string {
	rule := rulesByCapability[strings.TrimSpace(capabilityKey)]
	return strings.TrimSpace(rule.Record)
}
```

- [ ] **Step 2: Add expression builder**

Add:

```go
func snmpGrafanaExpressionsForDefinition(def snmpGrafanaPanelDefinition, rulesByCapability map[string]dto.SnmpRecordingRulePreviewRule) []string {
	record := func(key string) string {
		return snmpGrafanaRecordForCapability(rulesByCapability, key)
	}
	switch def.PanelKey {
	case "interface_basic.utilization":
		inRate, outRate, speed := record("if_in_rate"), record("if_out_rate"), record("if_speed_bps")
		if inRate == "" || outRate == "" || speed == "" {
			return nil
		}
		return []string{
			fmt.Sprintf("topk(10, max by (ifDescr, ifAlias) (%s / %s))", inRate, speed),
			fmt.Sprintf("topk(10, max by (ifDescr, ifAlias) (%s / %s))", outRate, speed),
		}
	case "interface_basic.quality_hotspots":
		records := []string{record("if_in_error_rate"), record("if_out_error_rate"), record("if_in_discard_rate"), record("if_out_discard_rate")}
		parts := make([]string, 0, len(records))
		for _, one := range records {
			if one != "" {
				parts = append(parts, one)
			}
		}
		if len(parts) == 0 {
			return nil
		}
		return []string{fmt.Sprintf("topk(10, max by (ifDescr, ifAlias) (%s))", strings.Join(parts, " + "))}
	case "interface_basic.throughput":
		inRate, outRate := record("if_in_rate"), record("if_out_rate")
		exprs := []string{}
		if inRate != "" {
			exprs = append(exprs, fmt.Sprintf("sum(%s)", inRate))
		}
		if outRate != "" {
			exprs = append(exprs, fmt.Sprintf("sum(%s)", outRate))
		}
		return exprs
	default:
		exprs := make([]string, 0, len(def.CapabilityKeys))
		for _, key := range def.CapabilityKeys {
			if one := record(key); one != "" {
				exprs = append(exprs, one)
			}
		}
		return exprs
	}
}
```

- [ ] **Step 3: Build Grafana targets from expressions**

Add:

```go
func snmpGrafanaTargetsForExpressions(exprs []string, def snmpGrafanaPanelDefinition) []interface{} {
	targets := make([]interface{}, 0, len(exprs))
	for idx, expr := range exprs {
		targets = append(targets, map[string]interface{}{
			"expr": expr,
			"legendFormat": snmpGrafanaLegendForExpression(def, idx),
			"refId": string(rune('A' + idx)),
			"range": def.VisualType != "table" && def.VisualType != "stat",
			"instant": def.VisualType == "table" || def.VisualType == "stat",
		})
	}
	return targets
}

func snmpGrafanaLegendForExpression(def snmpGrafanaPanelDefinition, idx int) string {
	if def.PanelKey == "interface_basic.utilization" && idx == 0 {
		return "In Utilization"
	}
	if def.PanelKey == "interface_basic.utilization" && idx == 1 {
		return "Out Utilization"
	}
	if def.PanelKey == "interface_basic.throughput" && idx == 0 {
		return "In"
	}
	if def.PanelKey == "interface_basic.throughput" && idx == 1 {
		return "Out"
	}
	if idx >= 0 && idx < len(def.CapabilityKeys) {
		return snmpGrafanaLegendForCapability(def.CapabilityKeys[idx])
	}
	return def.Title
}
```

- [ ] **Step 4: Run screenshot test**

Run:

```bash
cd OneOps
go test ./app/platform/service/impl -run TestMetricCapabilityContractResolverMaterializesScreenshotStyleGrafanaDashboard -count=1
```

Expected: PASS.

### Task 7: Update Main Materializer Loop

**Files:**

- Modify: `OneOps/app/platform/service/impl/metric_capability_contract_resolver.go`

- [ ] **Step 1: Track rendered and skipped panel keys**

Inside `MaterializeGrafanaDashboardDryRun`, add:

```go
renderedPanelKeys := []string{}
skippedPanelKeys := []string{}
```

- [ ] **Step 2: Use render policy**

Replace the old support-state gate with:

```go
support, hasSupport := supportByPanel[def.PanelKey]
if def.RenderPolicy != snmpGrafanaRenderAlways {
	if !hasSupport || (support.State != "supported" && support.State != "config_driven") {
		skippedPanelKeys = append(skippedPanelKeys, def.PanelKey)
		continue
	}
}
```

- [ ] **Step 3: Use new panel/query helpers**

For each definition:

```go
exprs := snmpGrafanaExpressionsForDefinition(def, rulesByCapability)
targets := snmpGrafanaTargetsForExpressions(exprs, def)
if def.RenderPolicy != snmpGrafanaRenderAlways && len(targets) == 0 {
	skippedPanelKeys = append(skippedPanelKeys, def.PanelKey)
	continue
}
panelID := len(panels) + 1
panel := snmpGrafanaBuildPanel(def, panelID, target, targets)
```

- [ ] **Step 4: Populate new binding metadata**

When appending `SnmpGrafanaPanelBindingPreview`, set:

```go
DashboardVariant: def.DashboardVariant,
SectionKey:    def.SectionKey,
DisplayIntent: def.DisplayIntent,
VisualType:    def.VisualType,
RenderPolicy:  def.RenderPolicy,
```

- [ ] **Step 5: Populate summary keys**

When creating `summary`, set:

```go
RenderedPanelKeys: cloneTrimmedStrings(renderedPanelKeys),
SkippedPanelKeys:  cloneTrimmedStrings(skippedPanelKeys),
```

- [ ] **Step 6: Run all Grafana materializer tests**

Run:

```bash
cd OneOps
go test ./app/platform/service/impl -run 'TestMetricCapabilityContractResolver.*GrafanaDashboard' -count=1
```

Expected: PASS. If the existing seven-panel test expects `PanelCount >= 7`, keep it passing by updating its assertions to screenshot-style panel keys rather than old titles.

### Task 7A: Verify Panels Are Capability-Gated

**Files:**

- Modify: `OneOps/app/platform/service/impl/metric_capability_contract_resolver_test.go`

- [ ] **Step 1: Add test `TestMetricCapabilityContractResolverSkipsUnsupportedSwitchPanels`**

Create supports that include only CPU and memory, plus recording rules only for CPU and memory. Call `MaterializeGrafanaDashboardDryRun`.

Assert:

```go
if !containsString(summary.RenderedPanelKeys, "device.identity") {
	t.Fatalf("identity panel should always render: %#v", summary.RenderedPanelKeys)
}
if !containsString(summary.RenderedPanelKeys, "system_basic.cpu.stat") {
	t.Fatalf("cpu stat should render: %#v", summary.RenderedPanelKeys)
}
if containsString(summary.RenderedPanelKeys, "interface_basic.utilization") {
	t.Fatalf("interface utilization must not render without interface capabilities: %#v", summary.RenderedPanelKeys)
}
if !containsString(summary.SkippedPanelKeys, "interface_basic.utilization") {
	t.Fatalf("expected skipped interface utilization diagnostic: %#v", summary.SkippedPanelKeys)
}
```

- [ ] **Step 2: Run capability gate test**

Run:

```bash
cd OneOps
go test ./app/platform/service/impl -run TestMetricCapabilityContractResolverSkipsUnsupportedSwitchPanels -count=1
```

Expected: PASS.

### Task 8: Frontend Smoke Contract

**Files:**

- Modify: `OneOPS-UI/src/typings/platform/snmp-metric-contract.ts`
- Modify: `OneOPS-UI/scripts/snmp-strategy-set-grafana-dashboard-materialization-dry-run-smoke.ts`

- [ ] **Step 1: Add optional TS fields**

In `SnmpGrafanaDashboardMaterializationSummary`, add:

```ts
rendered_panel_keys?: string[];
skipped_panel_keys?: string[];
```

In `SnmpGrafanaPanelBindingPreview`, add:

```ts
dashboard_variant?: string;
section_key?: string;
display_intent?: string;
visual_type?: string;
render_policy?: string;
```

- [ ] **Step 2: Extend smoke assertions**

In the smoke script, assert the source contains:

```ts
'dashboard_variant'
'rendered_panel_keys'
'display_intent'
'section_key'
'visual_type'
'render_policy'
```

- [ ] **Step 3: Run frontend smoke and typecheck**

Run:

```bash
cd OneOPS-UI
npm run smoke:snmp-strategy-set-grafana-dashboard-materialization-dry-run
npm run typecheck
```

Expected: both PASS.

### Task 9: Real Demo Acceptance

**Files:**

- No product code changes.

- [ ] **Step 1: Call dry-run API against demo2 backend**

Run:

```bash
curl -sS \
  -H 'X-Auth-Token: abc123' \
  -H 'Content-Type: application/json' \
  -d '{"target_part":"AST20260603174801664"}' \
  'http://127.0.0.1:8380/api/v1/platform/metrics/teleabs/strategy-sets/4284353d-1233-4022-ad18-871b3d8444c7/metric-contract/grafana/dashboards/materialize/dry-run/by-target' \
  > /tmp/oneops-snmp-screenshot-style-dry-run.json
```

Expected: top-level `code` is `0`.

- [ ] **Step 2: Inspect generated dashboard shape**

Run:

```bash
python3 - <<'PY'
import json
with open('/tmp/oneops-snmp-screenshot-style-dry-run.json') as f:
    payload=json.load(f)
data=payload['data']
dash=json.loads(data['dashboard_json'])
print('panels=', len(dash['panels']))
print('types=', sorted({p['type'] for p in dash['panels']}))
print('rendered=', data['materialization'].get('rendered_panel_keys'))
PY
```

Expected:

```text
types include text, stat, timeseries, table
rendered includes device.identity
```

- [ ] **Step 3: Optionally import into demo2 Grafana**

Run:

```bash
python3 - <<'PY'
import json
with open('/tmp/oneops-snmp-screenshot-style-dry-run.json') as f:
    payload=json.load(f)
dash=json.loads(payload['data']['dashboard_json'])
dash['id']=None
dash['uid']='oneops-snmp-screenshot-style-generated'
for panel in dash.get('panels', []):
    panel['datasource']={'type':'prometheus','uid':'victoriametrics'}
    for target in panel.get('targets', []):
        target['datasource']={'type':'prometheus','uid':'victoriametrics'}
with open('/tmp/oneops-snmp-screenshot-style-generated-import.json','w') as f:
    json.dump({'dashboard':dash,'folderId':0,'overwrite':True},f)
PY
curl -sS -u admin:admin -H 'Content-Type: application/json' \
  -X POST --data-binary @/tmp/oneops-snmp-screenshot-style-generated-import.json \
  http://127.0.0.1:3300/api/dashboards/db
```

Expected: Grafana returns `status: success`.

### Task 10: Verification And Handoff

**Files:**

- Modify: `docs/superpowers/handovers/2026-06-10-snmp-metric-groups-dashboard-family-handoff.md`

- [ ] **Step 1: Run backend verification**

Run:

```bash
cd OneOps
go test ./app/platform/service/impl -run 'TestMetricCapabilityContractResolver.*GrafanaDashboard|TestMetricCapabilityContractResolver.*RecordingRule' -count=1
go test ./app/platform/api -run 'TestTeleabsAPI_.*GrafanaDashboard' -count=1
go test ./app/platform/router -run TestTeleabsRoutes_ConsistentBetweenPlatformAndBidi -count=1
go test ./cmd -run '^$' -count=1
```

Expected: all PASS.

- [ ] **Step 2: Run frontend verification**

Run:

```bash
cd OneOPS-UI
npm run smoke:snmp-strategy-set-grafana-dashboard-materialization-dry-run
npm run typecheck
```

Expected: all PASS.

- [ ] **Step 3: Run diff hygiene**

Run:

```bash
git -C OneOps diff --check
git -C OneOPS-UI diff --check
git -C docs diff --check
```

Expected: all commands produce no output and exit `0`.

- [ ] **Step 4: Update handoff**

Append a short note with:

```text
Screenshot-style switch materializer implemented.
Generated switch dashboard now includes identity, KPI, hotspot, trend, and status panels.
Route remains strict by-target dry-run.
No Grafana DB persistence or syncToGrafana was added.
```
