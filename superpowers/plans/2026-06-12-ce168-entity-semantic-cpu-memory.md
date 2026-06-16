# CE168 Lower-Half Dashboard Refresh Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild the CE168 dashboard lower half into a left-heavy interface operations zone, a right-side resource and hardware zone, and a bottom events zone that removes large sparse panels and presents interface-heavy data in a more operationally useful form.

**Architecture:** Keep the existing SNMP Grafana dashboard materialization pipeline, but change the CE168 chassis template so it composes the lower half from grouped operational panels instead of generic independent charts. Reuse existing metric capabilities and scoped PromQL records where possible, add panel-type and field-override support only where the new interface table and compact summary cards require it, and keep quick_env seed templates in lockstep with the Go-side built-in template chain.

**Tech Stack:** Go, Grafana dashboard JSON generation, PromQL, quick_env SQL seed templates, Go tests, Python seed guard tests, shell smoke scripts.

---

## Repository Layout

- `/OneOPS/OneOps` is the backend Go repository.
- `/OneOPS/quick_env` is the quick_env repository.
- `/OneOPS/docs` is the documentation repository.
- Commit commands must run in the repository that owns the changed files.

## File Structure

- Modify `OneOps/app/platform/service/impl/metric_capability_contract_resolver.go`
  - Rework CE168 lower-half panel definitions and grid positions.
  - Change `Interface Utilization Top 10` from the current one-query bar gauge experiment to a compact operations table with inline utilization presentation.
  - Remove the large standalone `Interface Quality Hotspots` lower-half panel from the CE168 layout and fold quality signals into the interface operations table.
  - Replace or shrink sparse lower-half hardware/module panels into compact right-side summaries.
  - Add any panel option or field override helpers needed for compact tables and summary cards.
- Modify `OneOps/app/platform/service/impl/metric_capability_contract_resolver_test.go`
  - Update CE168 dashboard layout expectations.
  - Add assertions for the new left `14` / right `10` / bottom full-width lower-half grid.
  - Assert the large standalone quality-hotspot panel is removed from the CE168 lower-half layout.
  - Assert the interface operations table, port-map rows, traffic trio, and right-side resource group are rendered with the intended panel types and positions.
- Modify `quick_env/docker-entrypoint-initdb.d/zzzzzzzzzz-snmp-grafana-dashboard-template-bootstrap.sql`
  - Mirror the new CE168 chassis template patches into quick_env seed SQL.
- Modify `quick_env/tests/test_seed_template_guard.py`
  - Assert the seed contains the new CE168 lower-half layout patches and no longer seeds the old lower-half structure for chassis dashboards.
- Validate runtime with:
  - `quick_env/scripts/smoke_snmp_switch_dashboard_save.sh`
  - live Grafana dashboard JSON inspection for `snmp-switch-ce16808-172-21-16-d79d38278d`

## Follow-On Phase: Layer 2 Summary Data First

After the lower-half refresh, the next CE168 phase should prepare summary data before changing the `Routing & Layer 2` presentation.

- Add summary-ready data hooks for:
  - `l2_mac_table.count`
  - `l3_arp_table.count`
  - `l2_vlan_table.count`
  - `l2_stp_state.port_count`
  - `l2_stp_state.forwarding_count`
  - `l2_stp_state.blocking_count`
- Keep these metrics presentation-agnostic first so the UI can later choose:
  - compact stat list
  - grouped summary card
  - right-side summary block
- Do not design a `Routing & Layer 2` block around `BGP`, `OSPF`, or route counts until those data sources exist in the active SNMP pipeline.
- Treat `LLDP / L2 neighbors` as a separate readiness item because Huawei quick_env currently disables that metric group.

## Follow-On Phase: Routing Data Exploration And Modeling

Routing should be introduced as a generic summary contract with a Huawei VRP-first provider implementation.

- Define generic summary-ready capability names:
  - `bgp_neighbor_total`
  - `bgp_established_total`
  - `ospf_neighbor_total`
  - `ospf_full_total`
  - `ipv4_route_count`
  - `ipv6_route_count`
- Keep the contract generic, but do not force the first collection path to be vendor-neutral.
- Implement the first provider against Huawei CE168 / VRP evidence, then generalize other vendors later.

### Current Evidence

- `IPv4 route count` is the only routing summary signal already supported by historical CE168 evidence.
  - `ipCidrRouteNumber (.1.3.6.1.2.1.4.24.3.0)` returned a scalar value.
  - The `IP-FORWARD-MIB` table family was reachable in the prior CE168 SNMP walk.
- `IPv6 route count` is now proven on this CE168.
  - `ipv6RouteNumber (.1.3.6.1.2.1.55.1.9.0)` returned a live scalar value of `3` on `2026-06-13`.
- Live route-table protocol evidence currently shows no dynamic-routing entries:
  - `ipCidrRouteProto` entries only returned `local(2)` and `netmgmt(3)`.
  - no `ospf(13)` or `bgp(14)` IPv4 route entries were observed.
  - `ipv6RouteProtocol` entries observed in the live `ipv6RouteTable` returned `local(2)`.
- Standard `OSPF-MIB (.1.3.6.1.2.1.14)` returned `No Such Object`.
- Standard `BGP4-MIB (.1.3.6.1.2.1.15)` returned `No Such Object`.
- Huawei-private routing candidates are also blocked on the current CE168 runtime view.
  - `hwBgpPeerSessionNum (.1.3.6.1.4.1.2011.5.25.177.1.4.1.0)` returned `No Such Instance` on `2026-06-13`.
  - `hwBgpPeerTable (.1.3.6.1.4.1.2011.5.25.177.1.1.2)` walk returned `No Such Object` on `2026-06-13`.
  - `hwospfv2ProcessFullPeerNumber (.1.3.6.1.4.1.2011.5.25.155.33.1.1.2.0)` returned `No Such Object` on `2026-06-13`.
  - `hwospfv2` process/interface subtrees `.1.3.6.1.4.1.2011.5.25.155.33.1` and `.33.2` both returned `No Such Object` on `2026-06-13`.
- Local MIB metadata contains many `ospf` and `route` names, but those names are only candidates until the live CE168 SNMP view is proven to expose them.

### Delivery Order

- Phase A: add `ipv4_route_count` using standard `IP-FORWARD-MIB`
- Phase B: add `ipv6_route_count` using the proven `ipv6RouteNumber` scalar
- Phase C: run Huawei VRP private-MIB exploration for `BGP / OSPF`
- Phase D: only after proven collection exists, add `BGP / OSPF` summary rows into the compact routing panel

### Updated Routing Readiness After 2026-06-13 Private-MIB Probe

- `IPv4 Routes` is ready and already delivered through `ipCidrRouteNumber`.
- `IPv6 Routes` is ready and already delivered through `ipv6RouteNumber`.
- `BGP / OSPF` is still not provider-ready for Huawei VRP on this CE168.
  - The blocker is no longer “we have not checked Huawei private MIBs”.
  - The blocker is now “both standard and first-pass Huawei-private protocol trees are not exposed in the current runtime view, and the live route tables currently show no dynamic-routing protocol entries”.
- The next investigation steps should be operational:
  - verify whether `BGP / OSPF` are configured on the device
  - verify whether the active SNMP view includes the relevant Huawei branches
  - only then retry provider modeling

### Implementation Notes

- Prefer scalar route-count objects over counting route tables when both exist.
- Do not block `IPv4 Routes` delivery on `BGP / OSPF` readiness.
- Do not emit empty `BGP`, `OSPF`, or `IPv6 Routes` rows in the summary panel for CE168 before the provider actually supports them.
- Treat SNMP-view restrictions as part of provider readiness, not as a dashboard concern.

### Routing Implementation Tasks

#### Task R1: Define Generic Routing Summary Capabilities

**Files:**
- Modify: `OneOps/app/platform/service/impl/metric_capability_contract_resolver.go`
- Modify: `OneOps/app/platform/service/impl/metric_capability_contract_resolver_test.go`

- [ ] Add generic routing-summary panel and capability definitions for:
  - `l3_route_table.ipv4_count`
  - `l3_route_table.ipv6_count`
  - `routing_bgp.neighbor_total`
  - `routing_bgp.established_total`
  - `routing_ospf.neighbor_total`
  - `routing_ospf.full_total`
- [ ] Keep these definitions provider-agnostic at the contract layer.
- [ ] Add failing tests that assert:
  - the new panel keys are registered
  - each new panel key declares the expected acceptable capability
  - no CE168 dashboard template row is added for unsupported routing metrics yet

#### Task R2: Implement Huawei VRP IPv4 Route Count Provider

**Files:**
- Modify: `quick_env/docker-entrypoint-initdb.d/zzzzzzzzzz-huawei-snmp-network-strategy-bootstrap.sql`
- Modify: `OneOps/app/platform/service/impl/metric_capability_contract_resolver.go`
- Modify: `OneOps/app/platform/service/impl/metric_capability_contract_resolver_test.go`
- Modify: `quick_env/tests/test_seed_template_guard.py`

- [ ] Add Huawei VRP SNMP collection for the standard `IP-FORWARD-MIB` scalar `ipForwardNumber (.1.3.6.1.2.1.4.24.1)`.
- [ ] Register a metric-manifest entry and passthrough field so the raw series is collected in quick_env.
- [ ] Map the collected metric into the generic `ipv4_route_count` capability for Huawei VRP targets.
- [ ] Add a Grafana expression path for `l3_route_table.ipv4_count` that scopes the raw metric to `agent_host`.
- [ ] Add tests that assert:
  - the Huawei seed contains the new `ipForwardNumber` field
  - the provider maps that field to `ipv4_route_count`
  - the Grafana expression resolves to the scoped raw scalar rather than table counting

#### Task R3: Validate And Conditionally Model IPv6 Route Count

**Files:**
- Modify: `docs/superpowers/plans/2026-06-12-ce168-entity-semantic-cpu-memory.md`
- Modify: `docs/superpowers/specs/2026-06-12-ce168-entity-semantic-cpu-memory-design.md`
- Potentially modify later:
  - `quick_env/docker-entrypoint-initdb.d/zzzzzzzzzz-huawei-snmp-network-strategy-bootstrap.sql`
  - `OneOps/app/platform/service/impl/metric_capability_contract_resolver.go`
  - `OneOps/app/platform/service/impl/metric_capability_contract_resolver_test.go`

- [ ] Run a read-only CE168 probe for:
  - `ipv6RouteNumber (.1.3.6.1.2.1.55.1.9)`
  - any adjacent standard IPv6 route-count objects if needed
- [ ] Record whether the CE168 runtime SNMP view exposes a usable IPv6 scalar count.
- [ ] Only if the probe succeeds:
  - add the Huawei seed field
  - map it to `ipv6_route_count`
  - add the `l3_route_table.ipv6_count` provider implementation and tests
- [ ] If the probe fails, explicitly document `IPv6 Routes` as deferred rather than silently leaving a dead contract path.

#### Task R4: Explore Huawei VRP BGP Provider Candidates

**Files:**
- Modify: `docs/superpowers/plans/2026-06-12-ce168-entity-semantic-cpu-memory.md`
- Potentially add or modify:
  - Huawei exploration notes under `docs/superpowers/testing/...`
  - `quick_env/init-data/mib_tree.json` is read-only evidence, not a source of truth

- [ ] Confirm again that standard `BGP4-MIB (.1.3.6.1.2.1.15)` remains blocked by the CE168 SNMP view.
- [ ] Run candidate-name exploration against Huawei private MIB branches for BGP summary data.
- [ ] Prioritize finding provider-ready objects for:
  - total peer count
  - established peer count
- [ ] Record candidate OIDs, raw outputs, and whether they are:
  - exposed
  - blocked by view
  - absent on this software version
- [ ] Do not add collection seed or contract mapping until at least one provider-ready Huawei BGP signal is proven.

#### Task R5: Explore Huawei VRP OSPF Provider Candidates

**Files:**
- Modify: `docs/superpowers/plans/2026-06-12-ce168-entity-semantic-cpu-memory.md`
- Potentially add or modify:
  - Huawei exploration notes under `docs/superpowers/testing/...`

- [ ] Confirm again that standard `OSPF-MIB (.1.3.6.1.2.1.14)` remains blocked by the CE168 SNMP view.
- [ ] Run candidate-name exploration against Huawei private MIB branches for OSPF summary data.
- [ ] Prioritize finding provider-ready objects for:
  - total neighbor count
  - full-state neighbor count
- [ ] Record candidate OIDs, raw outputs, and whether they are:
  - exposed
  - blocked by view
  - absent on this software version
- [ ] Do not add collection seed or contract mapping until at least one provider-ready Huawei OSPF signal is proven.

#### Task R6: Promote Proven Routing Metrics Into The Compact Summary Panel

**Files:**
- Modify: `OneOps/app/platform/service/impl/metric_capability_contract_resolver.go`
- Modify: `OneOps/app/platform/service/impl/metric_capability_contract_resolver_test.go`
- Modify: `quick_env/docker-entrypoint-initdb.d/zzzzzzzzzz-snmp-grafana-dashboard-template-bootstrap.sql`
- Modify: `quick_env/tests/test_seed_template_guard.py`

- [ ] Extend `routing_l2.summary` only with routing rows that are already provider-backed.
- [ ] Keep summary rendering compact and count-oriented:
  - `IPv4 Routes`
  - `IPv6 Routes`
  - `BGP Established / Total`
  - `OSPF Full / Total`
- [ ] Preserve the rule that unsupported rows must not be rendered as empty placeholders for CE168.
- [ ] Validate the final panel against both code-generated JSON and live Grafana after `save-and-sync`.

## Follow-On Exploration: Optical Transceiver Power Data

The CE168 transceiver / optical domain should be treated as a separate data-preparation track rather than a dashboard-only task.

- Huawei official documentation `EDOC1100420459/f1e18928` describes a dedicated optical module table that includes:
  - module mode
  - wavelength
  - transfer distance
  - vendor serial number
  - temperature
  - voltage
  - bias current
  - RX optical power
  - TX optical power
- Local Huawei MIB metadata in `quick_env/init-data/mib_tree.json` confirms the dedicated table root:
  - `hwOpticalModuleInfoTable = .1.3.6.1.4.1.2011.5.25.31.1.1.3`
  - key columns:
    - `hwEntityOpticalTemperature = ...3.1.5`
    - `hwEntityOpticalVoltage = ...3.1.6`
    - `hwEntityOpticalBiasCurrent = ...3.1.7`
    - `hwEntityOpticalRxPower = ...3.1.8`
    - `hwEntityOpticalTxPower = ...3.1.9`
    - `hwEntityOpticalSupportDDM = ...3.1.57`
    - `hwEntityOpticalPortName = ...3.1.58`
    - lane-level optics:
      - `hwEntityOpticalLaneBiasCurrent = ...3.1.31`
      - `hwEntityOpticalLaneRxPower = ...3.1.32`
      - `hwEntityOpticalLaneTxPower = ...3.1.33`
- Current OneOps Huawei bootstrap does **not** collect any of these optical fields.
- Current Prometheus runtime also shows no CE168 `device_transceiver_status`, optical temperature, RX power, or TX power time series.
- Historical CE168 raw walk under the older Huawei entity-state table (`...1.1.1.1`) did not expose the previously guessed RX power column; the dedicated optical table root above is the more credible next probe target.
- Runtime task inspection for `collect_agent-001_snmp-passthrough_172_21_165_11_161` confirms the live read-only parameters:
  - target: `udp://172.21.165.11:161`
  - version: `SNMPv2c`
  - community: `CmsrOsp123`
- With the real runtime community above, direct probing from the current workspace **does** reach the optical table:
  - baseline probe `sysDescr.0` returns `Huawei Versatile Routing Platform Software / CE16808`
  - `hwEntityOpticalTemperature / BiasCurrent / RxPower / TxPower / PortName` all return data
- Current live CE168 optical-table shape:
  - total rows under `hwOpticalModuleInfoTable`: `328`
  - rows with non-empty `hwEntityOpticalPortName`: `130`
  - rows with non-sentinel RX values: `34`
  - rows with non-sentinel TX values: `32`
  - rows with non-sentinel bias current values: `34`
  - rows with non-sentinel temperature values: `130`
- Sentinel patterns observed on this device:
  - `hwEntityOpticalTemperature = -255` behaves like `not present / invalid`
  - `hwEntityOpticalRxPower = -1` and `hwEntityOpticalTxPower = -1` behave like `unsupported / unavailable`
  - `hwEntityOpticalRxPower = -4000` and `hwEntityOpticalTxPower = -4000` behave like a low-floor optical reading, effectively `-40.00 dBm`
- `hwEntityOpticalSupportDDM (...3.1.57)` returns `No Such Object` on this CE168 software version, so DDM capability cannot be gated by that column here.
- `hwEntityOpticalPortName (...3.1.58)` is populated only for the subset of ports that expose meaningful optical telemetry. Example mappings:
  - `17109249 -> 100GE5/0/0`
  - `17174785 -> 100GE6/0/0`
  - `17305857 -> 10GE8/0/0`
- Current highest live RX-power rows on this CE168 are:
  - `100GE6/0/3` raw `221`
  - `100GE5/0/35` raw `215`
  - `100GE5/0/5` raw `198`
  - `100GE5/0/3` raw `184`
- Current weakest non-sentinel RX-power rows include:
  - `100GE5/0/7` raw `-3045`
  - `10GE8/0/8` raw `-314`
  - `10GE8/0/2` raw `-275`
- Unit interpretation needs to follow **live CE168 data first**:
  - Huawei support pages contain conflicting summaries for `hwEntityOpticalRxPower / hwEntityOpticalTxPower`
  - on this CE168, the values clearly behave like `0.01 dBm`, not pure `uW`, because the same column contains positive values, negative values, and a stable `-4000 -> -40.00 dBm` floor
  - therefore dashboard-side conversion for this device family should currently assume:
    - `rx_power_dbm = raw / 100`
    - `tx_power_dbm = raw / 100`
  - `hwEntityOpticalTemperature` behaves like direct `°C`
  - `hwEntityOpticalBiasCurrent` behaves like `uA` on this platform; converting to `mA` should use `/1000`
- Lane-level columns `...3.1.31/.32/.33` are still not useful on this device in the current form:
  - current walks return empty strings rather than usable lane telemetry
  - the first dashboard-ready milestone should therefore stay on port-level optics, not lane-level QSFP heatmaps
- Metadata richness on this CE168 software version is mixed:
  - usable today:
    - vendor serial number `...3.1.4`
    - part number `...3.1.25`
    - wavelength `...3.1.2`
    - voltage `...3.1.6`
  - currently missing / unstable on this software build:
    - module mode `...3.1.1`
    - transfer distance `...3.1.3`
    - support-DDM flag `...3.1.57`
- That means a first transceiver dashboard can already show:
  - port name
  - Rx power
  - Tx power
  - temperature
  - bias current
  - wavelength
  - module SN / PN
  but should **not** yet assume reliable mode, distance, or DDM-capability flags on this CE168 release.

Recommended next read-only probes once SNMP reachability is stable:

- `snmpwalk` / `snmpbulkwalk` on `.1.3.6.1.4.1.2011.5.25.31.1.1.3`
- targeted columns:
  - `.1.3.6.1.4.1.2011.5.25.31.1.1.3.1.5`
  - `.1.3.6.1.4.1.2011.5.25.31.1.1.3.1.7`
  - `.1.3.6.1.4.1.2011.5.25.31.1.1.3.1.8`
  - `.1.3.6.1.4.1.2011.5.25.31.1.1.3.1.9`
  - `.1.3.6.1.4.1.2011.5.25.31.1.1.3.1.57`
  - `.1.3.6.1.4.1.2011.5.25.31.1.1.3.1.58`
- if lane-level QSFP telemetry is required, also probe:
  - `.1.3.6.1.4.1.2011.5.25.31.1.1.3.1.31`
  - `.1.3.6.1.4.1.2011.5.25.31.1.1.3.1.32`
  - `.1.3.6.1.4.1.2011.5.25.31.1.1.3.1.33`

## Task 1: Lock The New Lower-Half Layout In Tests First

**Files:**
- Modify: `OneOps/app/platform/service/impl/metric_capability_contract_resolver_test.go`

- [ ] **Step 1: Write the failing CE168 layout assertions**

Add or update assertions inside `TestMetricCapabilityContractResolverAggregatesEntityScopedMetricsForOperationsDashboard` so the CE168 lower half is checked explicitly:

```go
utilPanel := grafanaPanelByTitleForTest(t, dashboard, "Interface Utilization Top 10")
if got, _ := utilPanel["type"].(string); got != "table" {
	t.Fatalf("expected Interface Utilization Top 10 to render as compact table, got %#v", utilPanel["type"])
}
if got := grafanaPanelGridPosIntForTest(utilPanel, "x"); got != 0 {
	t.Fatalf("expected interface operations table to start at x=0, got %#v", utilPanel["gridPos"])
}
if got := grafanaPanelGridPosIntForTest(utilPanel, "w"); got != 14 {
	t.Fatalf("expected interface operations table width 14, got %#v", utilPanel["gridPos"])
}

trafficPanel := grafanaPanelByTitleForTest(t, dashboard, "Traffic Throughput")
if got := grafanaPanelGridPosIntForTest(trafficPanel, "x"); got != 0 {
	t.Fatalf("expected traffic section in left zone, got %#v", trafficPanel["gridPos"])
}
if got := grafanaPanelGridPosIntForTest(trafficPanel, "w"); got != 14 {
	t.Fatalf("expected traffic section width 14, got %#v", trafficPanel["gridPos"])
}

cpuTrend := grafanaPanelByTitleForTest(t, dashboard, "CPU / Memory Trend")
if got := grafanaPanelGridPosIntForTest(cpuTrend, "x"); got != 14 {
	t.Fatalf("expected resource zone to start at x=14, got %#v", cpuTrend["gridPos"])
}
if got := grafanaPanelGridPosIntForTest(cpuTrend, "w"); got != 10 {
	t.Fatalf("expected resource zone width 10, got %#v", cpuTrend["gridPos"])
}
```

Also assert the old standalone lower-half quality panel is absent from the CE168 rendered panel list:

```go
for _, key := range summary.RenderedPanelKeys {
	if key == "interface_basic.quality_hotspots" {
		t.Fatalf("expected CE168 chassis layout to fold quality hotspots into the interface operations zone, got %#v", summary.RenderedPanelKeys)
	}
}
```

And assert the old large sparse module hotspot table is not left as-is:

```go
if containsString(summary.RenderedPanelKeys, "device_metrics.module_hotspots") {
	t.Fatalf("expected CE168 lower-half layout to replace the sparse module hotspot table with compact summaries, got %#v", summary.RenderedPanelKeys)
}
```

- [ ] **Step 2: Run the targeted test and verify it fails**

Run:

```bash
cd /OneOPS/OneOps
go test ./app/platform/service/impl -run 'TestMetricCapabilityContractResolverAggregatesEntityScopedMetricsForOperationsDashboard' -count=1
```

Expected: FAIL because the current CE168 layout still renders the pre-refresh lower-half structure.

- [ ] **Step 3: Add generic lower-half layout regression coverage**

Extend `TestMetricCapabilityContractResolverMaterializesScreenshotStyleGrafanaDashboard` with expectations that keep the generic switch layout unchanged while CE168 gets the chassis-specific lower-half refresh:

```go
if !containsString(summary.RenderedPanelKeys, "interface_basic.quality_hotspots") {
	t.Fatalf("expected generic switch layout to keep interface quality hotspots, got %#v", summary.RenderedPanelKeys)
}
```

This ensures the CE168-specific changes do not accidentally remove generic switch panels.

- [ ] **Step 4: Run the targeted test bundle and verify the failures are the expected ones**

Run:

```bash
cd /OneOPS/OneOps
go test ./app/platform/service/impl -run 'TestMetricCapabilityContractResolver(MaterializesScreenshotStyleGrafanaDashboard|AggregatesEntityScopedMetricsForOperationsDashboard)' -count=1
```

Expected: FAIL only on the newly-added lower-half layout assertions.

- [ ] **Step 5: Commit**

```bash
cd /OneOPS/OneOps
git add app/platform/service/impl/metric_capability_contract_resolver_test.go
git commit -m "test: lock ce168 lower-half dashboard layout"
```

## Task 2: Rebuild The CE168 Lower-Half Panel Definition Set

**Files:**
- Modify: `OneOps/app/platform/service/impl/metric_capability_contract_resolver.go`

- [ ] **Step 1: Add a chassis-specific lower-half grid plan in code**

In `snmpGrafanaSwitchDashboardHuaweiChassisTemplate()`, replace the existing lower-half patch set with a left `14` / right `10` / bottom-row structure. Use explicit chassis patch entries instead of relying on inherited generic positions.

Add or update patch definitions along these lines:

```go
{
	Action:   snmpGrafanaPanelPatchOverride,
	PanelKey: "interface_basic.utilization",
	Definition: snmpGrafanaPanelDefinition{
		Title:      "Interface Utilization (Top 10 by In/Out)",
		VisualType: "table",
		GridX:      0,
		GridY:      19,
		GridW:      14,
		GridH:      10,
	},
},
{
	Action:   snmpGrafanaPanelPatchMove,
	PanelKey: "interface_basic.throughput",
	GridX:    intPtr(0),
	GridY:    intPtr(37),
	GridW:    intPtr(14),
	GridH:    intPtr(8),
},
{
	Action:   snmpGrafanaPanelPatchMove,
	PanelKey: "system_basic.cpu_memory.trend",
	GridX:    intPtr(14),
	GridY:    intPtr(19),
	GridW:    intPtr(10),
	GridH:    intPtr(10),
},
```

Use the existing board-row `interface_basic.port_state.board.*` panels as the left-zone spatial map and move them under the utilization table:

```go
GridX: 0,
GridW: 14,
GridY: 29, // then 31, 33, 35 for the remaining rows
GridH: 2,
```

- [ ] **Step 2: Remove large sparse lower-half panels from the CE168 layout**

Hide panels that no longer belong in the refreshed CE168 lower half:

```go
{
	Action:   snmpGrafanaPanelPatchHide,
	PanelKey: "interface_basic.quality_hotspots",
},
{
	Action:   snmpGrafanaPanelPatchHide,
	PanelKey: "device_metrics.module_hotspots",
},
```

Keep the generic root definitions intact; only the CE168 chassis template should hide or replace them.

- [ ] **Step 3: Fold quality and state into the interface operations table**

Revert `interface_basic.utilization` to a compact table-oriented panel contract and keep the interface quality data within the table instead of a standalone chassis panel. Make sure the definition uses the capability set required for:

```go
CapabilityKeys: []string{
	"if_in_rate",
	"if_out_rate",
	"if_speed_bps",
	"if_admin_status",
	"if_oper_status",
	"if_in_error_rate",
	"if_out_error_rate",
},
```

If the existing expression builder only returns a single utilization series, add a chassis-only table builder path that prepares separate table-friendly queries for:

```go
[]string{
	snmpGrafanaTopUtilizationExpr(record("if_in_rate"), record("if_out_rate"), record("if_speed_bps"), record("if_admin_status")),
	snmpGrafanaPortStateExpr(record("if_oper_status"), record("if_admin_status"), ""),
	snmpGrafanaQualityHotspotsExpr([]string{record("if_in_error_rate"), record("if_out_error_rate")}, record("if_admin_status")),
}
```

Do not create a new large standalone quality panel for CE168.

- [ ] **Step 4: Add compact right-side summary panels in place of sparse lower-half cards**

Use existing compact panels where possible instead of adding empty placeholder charts. For example, move or resize:

```go
"device_metrics.temperature.stat"
"device_metrics.fan_status.stat"
"device_metrics.power_status.stat"
"device_metrics.transceiver_status.stat"
"device_metrics.module_status.stat"
```

Place them in the right-side resource and hardware zone with compact heights:

```go
GridX: 14,
GridW: 5, // or 10 for wider summary blocks
GridH: 4,
```

Do not leave any primary lower-half panel occupying more than `10x8` if it only renders `No data`.

- [ ] **Step 5: Run the targeted dashboard test and verify it passes**

Run:

```bash
cd /OneOPS/OneOps
go test ./app/platform/service/impl -run 'TestMetricCapabilityContractResolverAggregatesEntityScopedMetricsForOperationsDashboard' -count=1
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
cd /OneOPS/OneOps
git add app/platform/service/impl/metric_capability_contract_resolver.go
git commit -m "feat: rebuild ce168 lower-half dashboard layout"
```

## Task 3: Add Table Overrides And Compact Presentation Rules

**Files:**
- Modify: `OneOps/app/platform/service/impl/metric_capability_contract_resolver.go`
- Modify: `OneOps/app/platform/service/impl/metric_capability_contract_resolver_test.go`

- [ ] **Step 1: Write failing expectations for compact table presentation**

Add assertions that the CE168 interface operations table uses table options and field presentation appropriate for compact ranked operations data:

```go
utilPanel := grafanaPanelByTitleForTest(t, dashboard, "Interface Utilization (Top 10 by In/Out)")
options, _ := utilPanel["options"].(map[string]interface{})
if got, _ := options["showHeader"].(bool); !got {
	t.Fatalf("expected interface operations table to show a header, got %#v", options)
}

fieldConfig, _ := utilPanel["fieldConfig"].(map[string]interface{})
overrides, _ := fieldConfig["overrides"].([]interface{})
if len(overrides) == 0 {
	t.Fatalf("expected interface operations table to define field overrides for compact utilization rendering, got %#v", fieldConfig)
}
```

- [ ] **Step 2: Run the targeted table test and verify it fails**

Run:

```bash
cd /OneOPS/OneOps
go test ./app/platform/service/impl -run 'TestMetricCapabilityContractResolverAggregatesEntityScopedMetricsForOperationsDashboard' -count=1
```

Expected: FAIL because compact field overrides are not yet emitted for the interface operations table.

- [ ] **Step 3: Implement field overrides for compact interface table rendering**

Add a helper that returns overrides for the CE168 interface operations table:

```go
func snmpGrafanaFieldOverrides(def snmpGrafanaPanelDefinition) []interface{} {
	if def.PanelKey != "interface_basic.utilization" {
		return []interface{}{}
	}
	return []interface{}{
		map[string]interface{}{
			"matcher": map[string]interface{}{"id": "byName", "options": "In Utilization"},
			"properties": []interface{}{
				map[string]interface{}{"id": "custom.cellOptions", "value": map[string]interface{}{"type": "gradient-gauge"}},
				map[string]interface{}{"id": "unit", "value": "percentunit"},
			},
		},
		map[string]interface{}{
			"matcher": map[string]interface{}{"id": "byName", "options": "Out Utilization"},
			"properties": []interface{}{
				map[string]interface{}{"id": "custom.cellOptions", "value": map[string]interface{}{"type": "gradient-gauge"}},
				map[string]interface{}{"id": "unit", "value": "percentunit"},
			},
		},
	}
}
```

Wire it into `snmpGrafanaBuildPanel`:

```go
"fieldConfig": map[string]interface{}{
	"defaults":  snmpGrafanaFieldDefaults(def),
	"overrides": snmpGrafanaFieldOverrides(def),
},
```

- [ ] **Step 4: Run the targeted test bundle and verify it passes**

Run:

```bash
cd /OneOPS/OneOps
go test ./app/platform/service/impl -run 'TestMetricCapabilityContractResolver(MaterializesScreenshotStyleGrafanaDashboard|AggregatesEntityScopedMetricsForOperationsDashboard)' -count=1
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
cd /OneOPS/OneOps
git add app/platform/service/impl/metric_capability_contract_resolver.go app/platform/service/impl/metric_capability_contract_resolver_test.go
git commit -m "feat: add compact ce168 interface table presentation"
```

## Task 4: Mirror The CE168 Layout In quick_env Seed Templates

**Files:**
- Modify: `quick_env/docker-entrypoint-initdb.d/zzzzzzzzzz-snmp-grafana-dashboard-template-bootstrap.sql`
- Modify: `quick_env/tests/test_seed_template_guard.py`

- [ ] **Step 1: Write failing seed guard assertions for the new CE168 lower half**

Add checks that the quick_env chassis seed contains the new lower-half structure and no longer seeds the obsolete standalone quality-hotspot panel for CE168:

```python
self.assertIn('"panel_key":"interface_basic.utilization","definition":{"title":"Interface Utilization (Top 10 by In/Out)"', seed_sql)
self.assertIn('"panel_key":"interface_basic.utilization","definition":{"title":"Interface Utilization (Top 10 by In/Out)"},"grid_x":0,"grid_y":19,"grid_w":14', seed_sql)
self.assertIn('"action":"hide","panel_key":"interface_basic.quality_hotspots"', seed_sql)
self.assertIn('"action":"hide","panel_key":"device_metrics.module_hotspots"', seed_sql)
self.assertIn('"panel_key":"interface_basic.throughput","grid_x":0,"grid_y":37,"grid_w":14', seed_sql)
self.assertIn('"panel_key":"system_basic.cpu_memory.trend","grid_x":14,"grid_y":19,"grid_w":10', seed_sql)
```

- [ ] **Step 2: Run the seed guard and verify it fails**

Run:

```bash
cd /OneOPS/quick_env
python3 tests/test_seed_template_guard.py
```

Expected: FAIL because the chassis seed still contains the old lower-half layout.

- [ ] **Step 3: Update the chassis seed patch list**

Mirror the Go-side CE168 chassis patch set in `zzzzzzzzzz-snmp-grafana-dashboard-template-bootstrap.sql`. Add or update the JSON patches so the seed:

```sql
{"action":"hide","panel_key":"interface_basic.quality_hotspots"}
{"action":"hide","panel_key":"device_metrics.module_hotspots"}
{"action":"override","panel_key":"interface_basic.utilization","definition":{"title":"Interface Utilization (Top 10 by In/Out)","visual_type":"table"},"grid_x":0,"grid_y":19,"grid_w":14,"grid_h":10}
{"action":"move","panel_key":"interface_basic.throughput","grid_x":0,"grid_y":37,"grid_w":14,"grid_h":8}
{"action":"move","panel_key":"system_basic.cpu_memory.trend","grid_x":14,"grid_y":19,"grid_w":10,"grid_h":10}
```

Also move the board-row `interface_basic.port_state.board.*` patches into the left-side lower-half map area.

- [ ] **Step 4: Run the seed guard and verify it passes**

Run:

```bash
cd /OneOPS/quick_env
python3 tests/test_seed_template_guard.py
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
cd /OneOPS/quick_env
git add docker-entrypoint-initdb.d/zzzzzzzzzz-snmp-grafana-dashboard-template-bootstrap.sql tests/test_seed_template_guard.py
git commit -m "feat: seed ce168 lower-half dashboard refresh"
```

## Task 5: Verify Save-And-Sync Uses The Refreshed Layout End-To-End

**Files:**
- Modify: `OneOps/app/platform/service/impl/metric_capability_contract_resolver_test.go`
- Validate with: `quick_env/scripts/smoke_snmp_switch_dashboard_save.sh`

- [ ] **Step 1: Add a regression test for saved dashboard content**

In the existing saved-dashboard tests around the `save grafana dashboard by target` flow, add assertions that the saved dashboard JSON contains the new CE168 lower-half layout markers:

```go
if !strings.Contains(saved.Content, `"title":"Interface Utilization (Top 10 by In/Out)"`) {
	t.Fatalf("expected saved dashboard content to contain refreshed interface operations table, got %s", saved.Content)
}
if strings.Contains(saved.Content, `"title":"Interface Quality Hotspots"`) {
	t.Fatalf("expected CE168 saved dashboard content to omit standalone quality hotspots panel, got %s", saved.Content)
}
```

- [ ] **Step 2: Run the targeted saved-dashboard tests and verify they fail if the saved content is stale**

Run:

```bash
cd /OneOPS/OneOps
go test ./app/platform/service/impl -run 'TestMetricCapabilityContractResolver.*save grafana dashboard' -count=1
```

Expected: FAIL until the saved dashboard materialization path emits the refreshed layout content.

- [ ] **Step 3: Fix any saved-content mismatch in the dashboard materialization path**

If the saved dashboard content still reflects old lower-half panel types or positions, adjust the save path to use the resolved CE168 template definitions directly before persistence. Keep the change inside the existing resolver/save flow near:

```go
materialized, err := r.MaterializeGrafanaDashboardByTarget(...)
saved, err := r.saveSnmpGrafanaDashboardTargetBinding(...)
```

Do not patch live Grafana JSON manually in code. The saved dashboard content must already contain the final intended lower-half layout.

- [ ] **Step 4: Run the full verification bundle**

Run:

```bash
cd /OneOPS/OneOps
go test ./app/platform/service/impl -run 'TestMetricCapabilityContractResolver(MaterializesScreenshotStyleGrafanaDashboard|AggregatesEntityScopedMetricsForOperationsDashboard|FallsBackToStatusOnlyPortCountsWithoutSpeedRule)|TestSnmpGrafana(ControlPlaneMaxExprUsesMpuIdentity|EntityMatcherExprInjectsIntoScopedRecord)' -count=1
cd /OneOPS/quick_env
python3 tests/test_seed_template_guard.py
SAVE_AND_SYNC=true SNMP_TARGET_VENDOR=Huawei SNMP_TARGET_OS=VRP SNMP_TARGET_MODEL=CE16808 TARGET_PART=CE16808-172-21-165-11 SNMP_TARGET_DEVICE_CODE=CE16808-172-21-165-11 MYSQL_PORT=3306 MYSQL_CONTAINER=demo-core-mysql bash scripts/smoke_snmp_switch_dashboard_save.sh
```

Expected:

- Go tests: PASS
- Python seed guard: PASS
- Smoke script: `dashboard save smoke passed`

- [ ] **Step 5: Inspect live Grafana JSON**

Run:

```bash
curl -s http://127.0.0.1:3000/api/dashboards/uid/snmp-switch-ce16808-172-21-16-d79d38278d -u admin:admin | jq '.dashboard.panels[] | {title, type, gridPos}'
```

Expected:

- `Interface Utilization (Top 10 by In/Out)` appears as a `table`
- no large standalone `Interface Quality Hotspots` panel remains in the CE168 lower half
- lower-half panel positions match the left `14` / right `10` / bottom row structure

- [ ] **Step 6: Commit**

```bash
cd /OneOPS/OneOps
git add app/platform/service/impl/metric_capability_contract_resolver_test.go
git commit -m "test: verify ce168 lower-half dashboard save-and-sync"
```

## Self-Review

- Spec coverage:
  - lower-half three-zone layout: covered by Tasks 1, 2, 4, 5
  - interface operations table replacing standalone bar gauge: covered by Tasks 1, 2, 3, 4
  - quality panel folded into interface operations zone: covered by Tasks 1, 2, 4, 5
  - sparse module hotspot table removal: covered by Tasks 1, 2, 4
  - runtime verification and saved-dashboard correctness: covered by Task 5
- Placeholder scan:
  - no `TODO`, `TBD`, or “implement later” placeholders remain
  - all code steps include concrete file paths, commands, or snippets
- Type consistency:
  - CE168 lower-half primary interface panel title is `Interface Utilization (Top 10 by In/Out)` throughout the plan
  - saved dashboard verification uses the same title and expects `table`
  - CE168 standalone `interface_basic.quality_hotspots` removal is consistently treated as chassis-specific
