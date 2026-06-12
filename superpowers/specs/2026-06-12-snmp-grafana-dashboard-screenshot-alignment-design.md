# SNMP Grafana Dashboard Screenshot Alignment Design

Date: 2026-06-12

## Goal

Use the provided network-device monitoring screenshot as the visual and information-architecture baseline for the next SNMP Grafana dashboard generation phase.

This screenshot style is primarily for **network switches**. It should be treated as the switch dashboard variant, not as a universal SNMP dashboard for every device category.

The intent is not to copy the screenshot pixel by pixel. The intent is to make generated Grafana dashboards feel close in operating value:

- device identity is visible at first glance;
- current health is summarized before detailed charts;
- interface state, traffic, error, and hardware health are grouped by operator workflow;
- dense information remains scannable on one screen;
- panels are traceable back to SNMP metric groups and recording rules.

Primary target:

```text
catalog/category: switch
typical data: interface table, port state, throughput, errors/discards, broadcast ratio, CPU, memory, hardware health
operator workflow: locate saturated or faulty ports first, then correlate with device resource and event evidence
```

Non-primary targets:

```text
router/firewall/load-balancer: may reuse some sections, but needs routing/session/policy-specific variants
server/BMC/OOB: should not use the switch port-map/interface-first layout as the default
generic SNMP device: should fall back to a smaller capability-driven dashboard
```

This document extends the current dry-run materializer design in:

```text
docs/superpowers/specs/2026-06-11-snmp-grafana-dashboard-materialization-dry-run-design.md
```

## Primary Integration Principle

The screenshot style is less important than the data logic integration.

The switch dashboard must be generated from the already-built SNMP strategy system:

```text
target device
  -> strategy set
  -> strategy-set selector
  -> matched strategy or inherited child strategy
  -> effective SNMP metric capability contract
  -> panel capability support
  -> recording rule preview
  -> switch dashboard panel catalog
  -> Grafana JSON dry-run
  -> panel binding preview
```

The dashboard generator must not become a standalone hand-written Grafana template. It must consume the same backend authoritative answers that the strategy set preview and recording-rule lifecycle already use.

Non-negotiable integration rules:

- strategy selection stays in `StrategySetMatcher`;
- target identity stays in `platform_devices_v2` plus `deviceidentity.ResolveMetadata(...)`;
- metric availability comes from `effective_contract`, not hardcoded vendor assumptions;
- panel renderability comes from `supports[]` and `support_summary`;
- PromQL expressions come from recording-rule preview records;
- panel traceability stays in `panel_bindings[]`;
- frontend must not infer manufacturer, platform, model, catalog, version, or matched strategy.

This means the screenshot-inspired dashboard is a **strategy-set materialization view**, not an independent Grafana design artifact.

## Strategy And Dashboard Inheritance Baseline

The platform design treats both strategies and dashboards as family trees, but they should not be implemented with the same runtime semantics.

### Strategy Inheritance

SNMP strategies use true semantic inheritance.

The normal lifecycle is:

```text
generic strategy for a device category
  -> vendor/platform strategy
    -> model-specific child strategy
      -> concrete matched strategy copy
```

In real use, strategy-set selection should usually match the most specific strategy copy. That copy must not be expected to repeat every inherited metric. It should inherit parent and grandparent capabilities, then add or override only the model-specific differences.

Therefore all downstream metric logic must consume the **effective strategy**, not only the selected strategy row:

```text
selected strategy copy
  -> walk parent_id chain to root
  -> merge parameters from root to leaf
  -> parse effective SNMP metric contract
  -> derive panel support, recording rules, and dashboard panels
```

This is especially important for switch dashboards. A Huawei / VRP / S5735 copy may only declare a model-specific temperature OID, while fan, power, interface, CPU, and memory capabilities may live in its parent or grandparent strategy. The dashboard should still render all inherited supported panels.

The strategy apply path already has a complete parent-chain merge model. Grafana metric-contract resolution must align with that behavior. A one-level parent merge is not enough.

### Dashboard Inheritance

Dashboard families should also be modeled as trees inside OneOps, but the final Grafana dashboard should be a materialized artifact.

Grafana itself provides organization and reuse primitives, but not full dashboard inheritance:

- folders and nested folders organize dashboards and can carry permissions;
- library panels allow a panel to be reused across dashboards and updated centrally;
- a saved dashboard JSON is still an independent dashboard definition.

For this project, the recommended model is:

```text
OneOps dashboard family root
  -> device-category dashboard template
    -> vendor/platform dashboard variant
      -> model-specific dashboard variant
        -> matched target dashboard materialization
          -> independent Grafana dashboard JSON
```

OneOps may support dashboard inheritance at the template/spec layer, for example:

- inherit sections, variables, panel recipes, thresholds, and layout rules from parent templates;
- allow children to add, override, hide, or reorder panel recipes;
- resolve the effective dashboard template before Grafana JSON generation;
- store Grafana as the rendered output, not as the inheritance engine.

This keeps platform behavior consistent with strategy inheritance without depending on Grafana features that are not designed for full dashboard tree inheritance.

Initial template patch semantics:

```text
add      = insert a new panel recipe, optionally before/after another panel key
override = merge selected fields into an existing panel recipe, preserving position unless before/after is set
hide     = remove an inherited panel recipe from the effective template
move     = reposition an inherited panel recipe before/after another panel key
```

Layout coordinates need explicit override support. In Go, `0` is also the default value, so a child template that wants to move a panel to `x=0` cannot rely on plain integer fields alone. Patch-level layout overrides should use explicit fields, pointer values, or an equivalent "field is present" marker.

Current backend materialization anchor:

```text
target context: Huawei / VRP / S5735
  -> dashboard template chain:
     snmp.switch.root
     snmp.switch.huawei.vrp
     snmp.switch.huawei.vrp.s5735
  -> effective panel definitions
  -> Grafana dashboard JSON
```

The dry-run/save materializer should expose the selected template key and template chain in its summary. This is important because operators usually interact with the concrete copy, while the effective dashboard content may still come from root, vendor/platform, and model-level ancestors.

The OneOps-side template chain should remain the source of inheritance. Grafana receives one independent dashboard JSON after the chain is resolved.

The first storage anchor for this is `platform_snmp_grafana_dashboard_template`. It stores template keys, parent keys, target match fields, and panel patch JSON. The materializer should prefer matching DB templates and fall back to built-in defaults when no persisted template family exists. Quick env seeds the initial switch family with `snmp.switch.root`, `snmp.switch.huawei.vrp`, and `snmp.switch.huawei.vrp.s5735`.

The platform should expose this as a read path before it exposes editing. `GET /platform/metrics/teleabs/metric-contract/grafana/dashboard-templates` lets the UI inspect the available template family, and `POST /platform/metrics/teleabs/metric-contract/grafana/dashboard-templates/resolve/by-target` lets operators confirm which concrete target resolves to which inherited chain. These endpoints are not the inheritance engine; they are the visibility layer over the OneOps-side template resolver.

The first write path should stay equally narrow: `POST /platform/metrics/teleabs/metric-contract/grafana/dashboard-templates` upserts a single OneOps template node by `template_key`. It should validate parent existence and patch JSON shape, then leave materialization, dashboard persistence, and Grafana sync to the already separate by-target dashboard APIs.

The first frontend surface should begin diagnostic, then allow narrow raw edits. In the strategy-set detail drawer, the existing target input can drive both `加载模板树` and `解析模板链`, so operators can see whether `Huawei / VRP / S5735` lands on the expected concrete template chain before saving or syncing a dashboard. A lightweight template-node editor may expose parent key, match fields, sort order, enabled state, and raw `patches_json` with array-JSON validation. The list/upsert responses should include the actual patch JSON and keep stable snake_case field names, so existing overrides are not lost when a node is edited. It should refresh the list after save and let the operator resolve the target chain again. A visual panel/patch builder remains a later step.

Management and runtime visibility should be intentionally different. The template management list may request `include_disabled=true` so disabled nodes remain visible and recoverable in the editor. The resolver used by by-target template resolution, dry-run materialization, save, and Grafana sync should continue to ignore disabled template nodes unless a future diagnostic endpoint explicitly asks otherwise.

The save and save-and-sync UX should display the same resolved template identity that the materializer used. At minimum, the summary should include the selected `dashboard_template_key` and the full `dashboard_template_chain`, because operators normally work with the concrete copy while the effective dashboard may still be inherited from root and vendor/platform ancestors.

## Screenshot Analysis

The screenshot is effective because it combines three dashboard styles in one page:

1. **Device overview**

   The first row is a device header, not a metric chart. It answers: which device, online state, role, IP, vendor/model, firmware, location, uptime, and last poll time.

2. **Health command strip**

   The second row uses compact KPI tiles for overall health, availability, active alerts, CPU, memory, temperature, power, and fan status. Each tile has one main value, one status color, and at most one supporting line. This makes the page useful before the user reads any chart.

3. **Operational drill-down**

   The rest of the screen groups data by troubleshooting workflow:

   - interface utilization table plus port map;
   - resource performance time series;
   - traffic time series and traffic mix;
   - routing and layer-2 counters;
   - hardware health lists;
   - alerts, events, and configuration/compliance state.

The page uses a dense dark theme, small but consistent panel titles, restrained borders, and color as status language. Green means healthy/up, blue means throughput or primary activity, purple means memory, orange means warning/buffer pressure, red means error/critical, gray means disabled/down/unknown.

The strongest switch-specific signals in the screenshot are:

- interface utilization ranked by port;
- port map / port state;
- speed and duplex context;
- link flaps;
- in/out errors and CRC/discard style quality signals;
- broadcast/multicast traffic mix;
- layer-2 and routing-adjacent summaries such as MAC, ARP, VLAN, STP, and neighbors;
- hardware modules, fans, power, temperature sensors, and transceivers.

These should drive the switch variant. They should not be forced into dashboards for devices where ports are not the main operating surface.

## Operator Attention Model

The screenshot also shows an important network-operations rule: different metrics deserve different visual treatments.

Network operators do not inspect every metric the same way. Some values are decision states, some are trends, some are rankings, and some are evidence. Grafana generation should choose the panel type from the operator question, not only from the metric type.

The deeper pattern is:

```text
identify the device
  -> decide whether it is urgent
  -> locate the failing or saturated component
  -> inspect trend and correlation
  -> collect evidence for ownership and next action
```

Every panel should justify its place in that sequence. If a panel does not help one of those steps, it should not be generated by default.

### Instant State

Use instant state when the operator needs a quick yes/no or normal/warning/critical answer.

Good forms:

```text
Stat
Status history latest value
Small table cell with colored status
```

Examples from the screenshot:

- overall health;
- online state;
- availability;
- active alert count;
- temperature current value;
- power supply state;
- fan state;
- interface up/down;
- firmware/compliance/NTP/SNMP status.

Why: these values trigger immediate action. A large time-series panel would slow the operator down.

### Trend And Shape

Use curves when the operator cares about direction, volatility, peaks, or correlation with an incident window.

Good forms:

```text
Time series
Sparkline inside Stat only for compact context
```

Examples from the screenshot:

- CPU usage over 24 hours;
- memory usage over 24 hours;
- temperature over 24 hours;
- packet buffer usage;
- interface throughput;
- packets per second.

Why: the important question is not only "what is it now?" but "is it rising, spiking, oscillating, or correlated with another resource?"

### Ranking And Hotspot Discovery

Use tables or top-N bars when the operator needs to find the worst interface, noisiest error source, or highest utilization.

Good forms:

```text
Table
Bar gauge
Top-N time series only when history matters
```

Examples from the screenshot:

- top interface utilization by in/out traffic;
- interfaces with errors;
- link flap count;
- transceivers by Rx power.

Why: the question is "where is the problem?" not "what does one metric look like over time?"

### Composition

Use a pie or donut only when the total is meaningful and the operator needs relative mix.

Good forms:

```text
Pie chart
Stacked bar
```

Examples from the screenshot:

- traffic mix by unicast, broadcast, and multicast.

Why: the operator is checking whether abnormal broadcast/multicast share is stealing capacity.

### Event Evidence

Use lists when the operator needs sequence, ownership, or recent cause.

Good forms:

```text
Table
Logs-style table
Alert list
```

Examples from the screenshot:

- active alerts;
- recent events;
- suggested owner;
- config backup status;
- authentication failures.

Why: event order and severity matter more than numeric plotting.

## Decision Layers In The Screenshot

The screenshot is not a flat dashboard. It is a layered decision surface. Grafana should preserve these layers even when the exact visual widgets differ.

### Layer 1: Identity And Trust

The header answers whether the operator is looking at the right object and whether the data can be trusted.

Important fields:

```text
device name/code
role or catalog
management IP
vendor/model
firmware/platform
location
uptime
last polled
online state
```

Operational meaning:

- wrong device identity makes every metric dangerous;
- stale polling makes every metric suspect;
- uptime distinguishes chronic utilization from a recent reboot or failover;
- vendor/model/platform explains which later hardware panels are meaningful.

Grafana implication:

- identity should be generated from inventory/target context, not from PromQL when possible;
- freshness should be a first-class field, ideally from scrape timestamp or collection status;
- stale data should turn the dashboard into `unknown`, not `healthy`.

### Layer 2: Triage Strip

The KPI strip answers whether the operator should act now.

This layer intentionally compresses information. It should not include every available metric. It should include only high-signal state:

```text
overall health
availability
active alert count
CPU current value
memory current value
temperature current value
power state
fan state
```

Operational meaning:

- these are paging and escalation signals;
- they need strong thresholds and color;
- they should expose current value, not complex history.

Grafana implication:

- use Stat panels with thresholds;
- sparklines are acceptable only as secondary context;
- values should reduce to one number or one state per tile.

### Layer 3: Fault Localization

The interface table and port map answer where the fault or pressure is.

This layer is the main reason the screenshot should be considered switch-specific. Switch troubleshooting usually starts from the physical/logical port: which link is down, saturated, flapping, noisy, or mis-negotiated. The screenshot first lists top interfaces by utilization and state, then gives visual port status.

Operational meaning:

- an operator usually needs a port name before a chart;
- interface tables should sort by operational risk;
- up/down alone is not enough; utilization, errors, discards, speed, and flaps matter together.

Grafana implication:

- interface utilization should be a table or bar-gauge table before it is a time series;
- default sort should be risk-oriented, for example max of in/out utilization, then error/discard rate;
- interface variables should let the operator pivot from a row to a detailed chart.

### Layer 4: Trend And Correlation

The resource and traffic charts answer what changed over time.

Operational meaning:

- curves are for correlation, not inventory;
- CPU, memory, temperature, packet buffer, throughput, and pps are useful together because they indicate whether congestion is device-wide or interface-local;
- average and max annotations matter because operators compare normal load with incident spikes.

Grafana implication:

- time-series panels should use the same time range;
- legends should show avg/max/current where Grafana supports it;
- CPU and memory curves should sit close to traffic curves to support visual correlation.

### Layer 5: Evidence And Ownership

Alerts, events, routing, hardware, and compliance answer why this happened and who should act.

Operational meaning:

- recent events provide cause candidates;
- active alerts provide severity and owner;
- routing/layer-2 tables prove network-plane impact;
- compliance/config status tells whether the issue might come from a recent change or policy drift.

Grafana implication:

- event and alert blocks should be tables, not charts;
- these blocks need source attribution because they often come from OneOPS tables, Alertmanager, logs, or config services rather than SNMP;
- do not render them as empty placeholders when the source is unavailable.

## Metric Semantics Beyond Chart Type

A metric needs more metadata than unit and PromQL expression. The screenshot implies these additional semantics.

### Freshness

Every dashboard-level health decision depends on data freshness.

Recommended fields:

```text
freshness_record
freshness_threshold
stale_state = unknown
```

Example:

```text
last_poll_age_seconds <= 120 -> fresh
last_poll_age_seconds > 120 -> stale
```

If freshness is stale, health should degrade to unknown or warning even when CPU and memory look normal.

### Directionality

Network metrics often have direction. In/out should stay paired.

Examples:

```text
if_in_rate + if_out_rate
if_in_error_rate + if_out_error_rate
if_in_discard_rate + if_out_discard_rate
if_in_broadcast_ratio + if_out_broadcast_ratio
```

Grafana implication:

- paired directional metrics belong in the same panel or same table row;
- do not create separate in-only and out-only dashboard blocks unless the operator has selected one interface for deep drill-down.

### Scope

Each metric has a natural scope:

```text
device-wide
interface
sensor
module
neighbor
route
event
```

Grafana implication:

- device-wide metrics are good KPI and resource panels;
- interface metrics need table aggregation and top-N sorting;
- sensor/module metrics need compact hardware tables;
- neighbor metrics are topology evidence and should default to latest table rows;
- event metrics need time-ordered evidence tables.

### Stability

Some values are stateful and should not be averaged.

Examples:

- `if_oper_status` should show latest state and transition history, not average status;
- power/fan state should show latest and last change, not a line average;
- firmware/compliance state should show current value, not time-series.

Grafana implication:

- use `last_over_time` or latest instant query for state;
- use count/changes for transitions;
- avoid misleading averages for enum-like SNMP values.

### Cardinality

Network dashboards can explode when every interface and sensor is charted.

Grafana implication:

- default dashboard should aggregate to top-N;
- detailed per-interface curves should be driven by a variable;
- table rows can include many interfaces, but time-series should not draw all interfaces by default.

## Metric Display Classification

The next materializer should classify each panel by display intent.

| Display intent | Operator question | Grafana form | Example metrics |
| --- | --- | --- | --- |
| `state` | Is it healthy right now? | Stat, status table | health, up/down, power, fan, NTP, compliance |
| `trend` | Is it changing or spiking? | Time series | CPU, memory, temperature, throughput, pps |
| `hotspot` | Which interface/component is worst? | Table, bar gauge | top utilization, errors, discards, flaps |
| `composition` | What is the traffic mix? | Pie, stacked bar | unicast/broadcast/multicast ratios |
| `evidence` | What happened recently? | Alert/event table | alerts, events, config changes |

This classification should become part of panel specs. Suggested field:

```text
display_intent
```

Valid values:

```text
state
trend
hotspot
composition
evidence
identity
```

`panel_type` should be derived from `display_intent` plus available data. For example, `cpu_usage_direct` can appear twice:

- `state`: current CPU stat tile;
- `trend`: CPU usage time series.

That duplication is intentional. The stat answers "do I need to react now?", while the curve answers "what changed?"

## Grafana Approximation Strategy

Grafana should approximate the screenshot through standard panels first:

```text
Stat
Time series
Table
Bar gauge
Pie chart
State timeline or Status history
Text/HTML only if strictly needed
```

Avoid a custom plugin for the first implementation. The only screenshot element that Grafana cannot reproduce cleanly with default panels is the port map. For that, use a dense table or status history first, and consider a later Canvas panel only after the data model is stable.

Recommended approach:

- keep the current generated JSON dry-run path;
- introduce a switch dashboard variant key, for example `snmp.switch.operations`;
- add richer panel layout definitions;
- bind every panel to recording-rule names;
- include `device_code` as a dashboard variable;
- include `ifDescr` or `interface` as a variable for table/chart filtering;
- keep unsupported panels out of the generated dashboard, but include missing capability diagnostics in the dry-run response.

The materializer should receive these upstream facts:

```text
strategy_set_id
target
item_contracts[]
effective_contract
supports[]
support_summary
rule_group
rules[]
recording_rule_summary
```

It should produce:

```text
dashboard_json
panel_bindings[]
materialization
```

No panel should be rendered only because the screenshot contains it. A panel renders only when its strategy-derived capability and recording-rule data are available, or when the panel is identity-only and sourced from target context.

## Dashboard Layout

The switch dashboard variant should use this high-level structure.

### Row 1: Device Identity

Panel type:

```text
Stat or table-like text panel
```

Content:

```text
Device name/code
Online state
Device role or catalog
IP address
Vendor / model
Platform / firmware
Location
Uptime
Last polled
```

Current SNMP contract support:

- `uptime` can come from `snmp_uptime`;
- identity fields mostly come from `platform_devices_v2` target context, not SNMP metrics;
- last polled requires scrape freshness, such as `timestamp(up{...})` or a future collection status metric.

### Row 2: Health KPI Strip

Panel type:

```text
Stat panels
```

KPI tiles:

```text
Overall Health
Availability
Active Alerts
CPU Usage
Memory Usage
Temperature
Power Supply
Fan Status
```

Mapping:

| Tile | Current source | Notes |
| --- | --- | --- |
| Overall Health | derived | Aggregate from availability, alerts, CPU, memory, temperature, interface errors. |
| Availability | `up` or scrape success | Requires target/job label alignment. |
| Active Alerts | Alertmanager or OneOPS alert tables | Not from SNMP contract. Add later. |
| CPU Usage | `oneops:cpu_usage_direct:ratio` | Supported now. |
| Memory Usage | `oneops:memory_usage_direct:ratio` | Supported now. |
| Temperature | `device_temperature_celsius` | Supported when strategy exposes a compatible sensor field. |
| Power Supply | `device_power_status` | Optional status capability; non-`1` is treated as degraded. |
| Fan Status | `device_fan_status` | Optional status capability; non-`1` is treated as degraded. |

### Row 3: Interface Utilization

Panel type:

```text
Table
```

Columns:

```text
Port
Description
Status
In Utilization
Out Utilization
In Errors
Out Errors
CRC / Discards
Speed
Link Flaps
```

Current mapping:

- status: `oneops:if_oper_status`
- speed: `oneops:if_speed_bps`
- in/out rate: `oneops:if_in_rate:bps`, `oneops:if_out_rate:bps`
- utilization: rate divided by speed;
- errors/discards: `oneops:if_*_error_rate:pps`, `oneops:if_*_discard_rate:pps`

Needed later:

- link flaps require status transition count;
- description should prefer `ifAlias`, then `ifDescr`, then `ifName`;
- CRC needs vendor-specific mapping unless represented by discard/error counters.

Switch-specific rule: this section is mandatory for the switch variant when interface traffic and speed are supported. If those capabilities are missing, the switch variant should either render a reduced diagnostic dashboard or report that the target lacks enough switch interface data.

### Row 4: Port Map

Panel type for first implementation:

```text
Status history or compact table
```

Target behavior:

- one cell per interface;
- green for up;
- gray for down or disabled;
- orange for warning;
- red for error;
- tooltip contains interface name, status, speed, in/out utilization, and error rate.

Grafana default panels cannot easily draw the exact switch-front panel from the screenshot. A later Canvas-based port map can be added after the interface identity model is reliable.

### Row 5: Resource Performance

Panel type:

```text
Time series
```

Panels:

```text
CPU Usage (%)
Memory Usage (%)
Temperature (C)
Packet Buffer Usage (%)
```

Current mapping:

- CPU and memory exist in current recording rules;
- temperature and buffer usage should be rendered only when the capability contract marks them supported or config-driven.

### Row 6: Traffic

Panel type:

```text
Time series + pie chart
```

Panels:

```text
Throughput
Packets Per Second
Traffic Mix
```

Current mapping:

- throughput exists through in/out bps records;
- packet counters need packet-rate recording rules from `ifInUcastPkts`, `ifOutUcastPkts`, `ifInNUcastPkts`, and `ifOutNUcastPkts`;
- traffic mix can be approximated from unicast and non-unicast packet rates.

### Row 7: Routing, Layer 2, Hardware, Events, Compliance

These sections should be generated as optional blocks.

They are valuable in the screenshot, but they require data outside the current common SNMP metric contract:

- routing neighbors and route count may come from device collection tables or vendor MIBs;
- LLDP-style neighbors now have a contract and Grafana evidence-panel foundation through `l2_neighbors` / `l2_neighbors.summary`, normalized from passthrough SNMP tables into table-shaped, non-recordable dimensions such as `local_port`, `neighbor_name`, `neighbor_port`, `neighbor_chassis_id`, and `neighbor_management_ip`;
- MAC forwarding tables now have the same evidence-panel foundation through `l2_mac_table` / `l2_mac_table.summary`, normalized from BRIDGE-MIB / Q-BRIDGE-MIB passthrough tables into table-shaped, non-recordable dimensions such as `mac_address`, `bridge_port`, `mac_status`, and `vlan_id`;
- ARP tables now have the same evidence-panel foundation through `l3_arp_table` / `l3_arp_table.summary`, normalized from IP-MIB passthrough tables into table-shaped, non-recordable dimensions such as `ip_address`, `mac_address`, `if_index`, and `arp_type`;
- VLAN tables now have the same evidence-panel foundation through `l2_vlan_table` / `l2_vlan_table.summary`, normalized from Q-BRIDGE-MIB passthrough tables into table-shaped, non-recordable dimensions such as `vlan_id`, `vlan_name`, `vlan_status`, and `vlan_type`;
- STP port state now has the same evidence-panel foundation through `l2_stp_state` / `l2_stp_state.summary`, normalized from BRIDGE-MIB passthrough tables into table-shaped, non-recordable dimensions such as `stp_port`, `stp_state`, `stp_enable`, `stp_path_cost`, and `stp_designated_bridge`;
- hardware health needs power, fan, transceiver, and temperature sensor capabilities;
- active alerts and recent events now have a platform evidence-link foundation through `platform_alerts.active` and `platform_events.recent`, backed by OneOPS platform tables such as `alert_alarm`, `deployment_event_log`, `platform_config_change_event`, and `device_v2_change_event`;
- configuration backup and compliance now have a platform evidence-link foundation through `platform_config.backup` and `platform_config.compliance`, backed by OneOPS platform tables such as `platform_device_config_backup`, `platform_config_version`, and `platform_config_baseline_evaluation`.

For the next Grafana iteration, include placeholders only in the design. Do not render empty panels unless the backend has real data or a config-driven capability. LLDP, MAC table, ARP table, VLAN table, and STP state panels now use a narrow evidence-table render policy instead of a recording-rule policy; config backup and compliance use platform evidence-link panels instead of pretending to be Prometheus metrics. Forcing these rows into recording rules would lose the operator semantics.

## Panel Specification Additions

The materializer should move from a flat list of base panels to a richer panel catalog.

Suggested fields:

```text
panel_key
dashboard_variant
title
section_key
section_title
display_intent
panel_type
grid_pos
primary_unit
thresholds
required_capability_keys[]
optional_capability_keys[]
record_names[]
legend_templates[]
render_policy
required_strategy_context[]
```

`render_policy` values:

```text
required_only
supported_or_config_driven
optional_block
```

This keeps dashboard generation deterministic while allowing future hardware and event panels to appear only when the target supports them.

Panel specs must stay tied to the data model:

- `required_capability_keys[]` references semantic capability keys in the SNMP metric contract;
- `record_names[]` are resolved from recording-rule preview, not authored by the panel catalog directly;
- `metric_group_key` must match semantic groups such as `interface_basic` and `system_basic`;
- `panel_key` is the stable bridge between strategy semantics, recording rules, and Grafana panel binding.

For the switch variant, the first stable variant key should be:

```text
snmp.switch.operations
```

## Current SNMP Metric To Display Mapping

For the switch variant, the current common SNMP contract should map to dashboard panels as follows.

| Capability / record | Primary concern | Preferred display | Secondary display |
| --- | --- | --- | --- |
| `cpu_usage_direct` / `oneops:cpu_usage_direct:ratio` | current pressure and trend | Stat | Time series |
| `memory_usage_direct` / `oneops:memory_usage_direct:ratio` | current pressure and trend | Stat | Time series |
| `if_oper_status` / `oneops:if_oper_status` | link state | Table/status cells | Status history |
| `if_speed_bps` / `oneops:if_speed_bps` | capacity and duplex context | Table | Stat only for selected interface |
| `if_in_rate` / `oneops:if_in_rate:bps` | traffic trend and top talkers | Time series | Interface top-N table |
| `if_out_rate` / `oneops:if_out_rate:bps` | traffic trend and top talkers | Time series | Interface top-N table |
| `if_in_error_rate` / `oneops:if_in_error_rate:pps` | quality degradation | Top-N table | Time series for selected interface |
| `if_out_error_rate` / `oneops:if_out_error_rate:pps` | quality degradation | Top-N table | Time series for selected interface |
| `if_in_discard_rate` / `oneops:if_in_discard_rate:pps` | congestion or buffer pressure | Top-N table | Time series for selected interface |
| `if_out_discard_rate` / `oneops:if_out_discard_rate:pps` | congestion or buffer pressure | Top-N table | Time series for selected interface |
| `if_in_broadcast_ratio` / `oneops:if_in_broadcast_ratio:ratio` | abnormal broadcast share | Stat or top-N table | Traffic mix chart |
| `if_out_broadcast_ratio` / `oneops:if_out_broadcast_ratio:ratio` | abnormal broadcast share | Stat or top-N table | Traffic mix chart |
| `uptime` / `snmp_uptime` | device stability | Stat | none |

The key rule: counters and rates should not automatically become line charts. Interface error and discard rates are usually more useful as a ranked table first, because the operator needs to identify the bad port quickly.

## Priority Signals To Extract First

The screenshot contains many possible panels, but only a smaller set is essential for the first Grafana implementation. Extract these first because they map directly to high-frequency network operations questions.

### Device Trust Signals

| Signal | Question | Data source | Display |
| --- | --- | --- | --- |
| Device identity | Am I looking at the right device? | `platform_devices_v2` target context | Header/table |
| Online/scrape state | Is the device currently reachable? | `up` or collection status | Stat |
| Last polled/freshness | Can I trust the values? | scrape timestamp or collection status | Header/stat |
| Uptime | Did it reboot or fail over? | `snmp_uptime` | Stat |

### Capacity And Saturation Signals

| Signal | Question | Data source | Display |
| --- | --- | --- | --- |
| CPU current | Is the control plane under pressure now? | CPU recording rule | Stat |
| CPU trend | Was there a spike? | CPU recording rule | Time series |
| Memory current | Is memory near limit now? | memory recording rule | Stat |
| Memory trend | Is memory leaking or spiking? | memory recording rule | Time series |
| Interface utilization | Which links are saturated? | traffic rate / speed | Top-N table |
| Throughput trend | Is traffic rising or bursty? | in/out bps | Time series |

### Fault And Quality Signals

| Signal | Question | Data source | Display |
| --- | --- | --- | --- |
| Interface status | Which ports are down? | `if_oper_status` | Table/status cells |
| Error rate | Which ports are faulty? | error pps | Top-N table |
| Discard rate | Which ports are congested? | discard pps | Top-N table |
| Broadcast ratio | Is there abnormal L2 noise? | broadcast/non-unicast ratio | Stat/top-N/pie |
| Link flaps | Is the link unstable? | status transition count | Top-N table |

For switches, this is the highest-value block after the triage strip. Interface hotspot and quality signals should be implemented before broader routing, compliance, or generic SNMP panels.

### Physical Health Signals

| Signal | Question | Data source | Display |
| --- | --- | --- | --- |
| Temperature | Is hardware overheating? | vendor/system sensor | Stat + trend |
| Fan state | Is cooling degraded? | `device_fan_status` | Stat/table |
| Power state | Is redundancy lost? | `device_power_status` | Stat/table |
| Transceiver/module state | Is optical or line-card hardware degraded? | `device_transceiver_status`, `device_module_status` | Stat/table |
| Transceiver power | Is optical signal weak? | future DOM sensor | Top-N table |

These physical health signals should be optional until the SNMP capability contract can represent vendor-specific sensors safely.

## Threshold Semantics

The screenshot uses thresholds as operating language. The next materializer should define thresholds per signal type, not per panel.

Initial defaults:

| Signal | Warning | Critical | Notes |
| --- | --- | --- | --- |
| CPU usage | `> 70%` | `> 85%` | Device control-plane pressure. |
| Memory usage | `> 75%` | `> 90%` | Vendor memory semantics vary. |
| Interface utilization | `> 70%` | `> 90%` | Use max of in/out utilization. |
| Interface error rate | `> 0` sustained | high sustained rate | Threshold must be tuned by environment. |
| Interface discard rate | `> 0` sustained | high sustained rate | Often congestion or QoS pressure. |
| Broadcast ratio | `> 10%` | `> 20%` | Depends on network type. |
| Last poll age | `> 2 scrape intervals` | `> 5 scrape intervals` | Stale data should affect health. |
| Temperature | vendor threshold | vendor threshold | Prefer vendor sensor state when available. |

Thresholds should be overrideable later by strategy, device role, or environment. The generated dashboard should still have deterministic defaults for quick env and dry-run acceptance.

## PromQL Shape Guidance

Grafana panels should prefer recording rules, but the panel catalog should document the expected query shape.

Examples:

```text
Current CPU stat:
last_over_time(oneops:cpu_usage_direct:ratio{device_code="$device"}[$__rate_interval])

CPU trend:
oneops:cpu_usage_direct:ratio{device_code="$device"}

Top interface utilization:
topk(10, max by (ifDescr) (
  max(
    oneops:if_in_rate:bps{device_code="$device"} / oneops:if_speed_bps{device_code="$device"},
    oneops:if_out_rate:bps{device_code="$device"} / oneops:if_speed_bps{device_code="$device"}
  )
))

Interface traffic trend for selected interface:
oneops:if_in_rate:bps{device_code="$device", ifDescr=~"$interface"}
oneops:if_out_rate:bps{device_code="$device", ifDescr=~"$interface"}
```

The exact PromQL must match the final recording rule labels. The important design point is that top-N panels aggregate by interface and detailed panels filter by selected interface.

## Derived Operator Signals

Some screenshot-level values should be derived from multiple lower-level metrics.

### Interface Utilization

```text
in_utilization = if_in_rate_bps / if_speed_bps
out_utilization = if_out_rate_bps / if_speed_bps
```

Display:

- table bars for top interfaces;
- optional selected-interface time series.

### Interface Quality

```text
quality_warning = error_rate > threshold OR discard_rate > threshold OR link_flaps > threshold
```

Display:

- table with severity color;
- active alert integration later.

### Overall Health

Initial derived health can be conservative:

```text
critical if target is down or critical alerts exist
warning if CPU/memory/interface quality thresholds are exceeded
healthy otherwise
unknown if freshness is missing
```

Display:

- single stat tile;
- never as a time series in the first implementation.

### Traffic Mix

Approximate from available packet counters:

```text
unicast = ifInUcastPkts + ifOutUcastPkts
broadcast_or_non_unicast = ifInNUcastPkts + ifOutNUcastPkts
```

Display:

- pie chart only when both numerator and total are available;
- otherwise omit the panel and report missing capability.

## Dashboard Reading Order

The generated dashboard should preserve this operator reading order:

1. **Can I trust this device and is it alive?**
   Device identity, online state, uptime, last poll.

2. **Is anything urgent?**
   Health, alerts, CPU, memory, temperature, power, fan.

3. **Where is the traffic or fault hotspot?**
   Interface utilization table, error/discard top-N, port state.

4. **What changed over time?**
   CPU, memory, traffic, packet rate, temperature trends.

5. **What is the likely cause or next action?**
   Alerts, events, compliance, routing/layer-2 summaries.

This reading order is more important than exact visual matching. If data is missing, the dashboard should skip unsupported later sections but keep the earlier sections stable.

## Visual Rules

Use these as dashboard-generation defaults:

- dark theme compatible;
- 24-column grid;
- KPI row uses 8 compact stat panels, each 3 columns wide;
- large content panels use 12 columns or 24 columns;
- keep panel titles short;
- use units consistently:
  - ratios as percent;
  - traffic as bps;
  - packet rates as pps;
  - temperature as Celsius;
  - uptime as duration;
- use thresholds consistently:
  - green: healthy;
  - blue: normal utilization/activity;
  - orange: warning;
  - red: critical;
  - gray: unknown/down/disabled.

Avoid decorative visual work. The screenshot works because the density serves operations, not because it has ornamental styling.

## Data Model Implications

The screenshot makes one product requirement clear: Grafana generation should not be only a chart generator. It needs an operator-facing device dashboard model.

The backend should keep these layers separate:

```text
target context
SNMP metric contract
recording rules
panel capability support
dashboard section catalog
Grafana JSON materialization
```

Device identity and compliance fields should not be forced into the SNMP metric contract. They should come from platform inventory, alerting, or config-compliance services and be joined at dashboard materialization time.

The implemented strategy/strategy-set logic remains the source of truth:

```text
TeleabsStrategySet
  -> selected strategy items
  -> TeleabsStrategy parent/child inheritance
  -> parameters.metric_groups / passthrough_config / metric_manifest
  -> backend effective contract
```

The switch dashboard should consume the effective contract after this resolution. It should not reverse-parse raw SNMP config, re-run vendor matching, or duplicate strategy inheritance logic.

For a concrete Huawei / VRP / S5735 switch, the expected path is:

```text
generic switch strategy
  -> Huawei VRP child strategy
  -> Huawei S5735 child strategy
  -> one effective metric contract
```

Only the best concrete leaf strategy should be selected for the target family. The parent and grandparent strategies contribute inherited metric definitions through the effective contract; they should not appear as independent sibling dashboards or independent sibling policy hits for the same family.

Dashboard templates use the same tree idea at generation time:

```text
snmp.switch.root
  -> snmp.switch.huawei.vrp
  -> snmp.switch.huawei.vrp.s5735
  -> one materialized Grafana dashboard JSON
```

Grafana itself should not be asked to maintain runtime dashboard inheritance. The platform should resolve the template chain and save the resulting concrete dashboard. This keeps Grafana integration simple, keeps dashboard replacement/snapshot behavior deterministic, and still lets OneOPS preserve tree semantics in its own template records.

Panel bindings should preserve the full trace:

```text
dashboard_variant
panel_key
panel_id
section_key
display_intent
strategy_set_id
strategy_ids[]
metric_group_key
metric_keys[]
selected_capability_keys[]
record_names[]
content_hash
```

For recording-rule panels, `record_names[]` must be populated from the recording-rule preview. For evidence-table panels such as `l2_neighbors.summary`, `l2_mac_table.summary`, `l3_arp_table.summary`, `l2_vlan_table.summary`, and `l2_stp_state.summary`, `record_names[]` is intentionally empty and the trace is carried by `metric_group_key`, `metric_keys[]`, `selected_capability_keys[]`, `render_policy=evidence_table`, and the panel query shape.

For platform evidence-link panels such as `platform_config.backup`, `platform_config.compliance`, `platform_alerts.active`, and `platform_events.recent`, `record_names[]` is also intentionally empty. The trace is carried by `metric_group_key`, stable platform evidence keys, `selected_capability_keys[]`, and `render_policy=platform_evidence_link`; detailed rows remain owned by the OneOPS platform tables.

This trace is the bridge to later dashboard diff/sync and to the strategy editor. If a panel cannot be traced back to strategy-derived capabilities and either recording rules or an explicit evidence-table binding, it should not enter the product materializer.

## Near-Term Implementation Recommendation

Implement the next Grafana phase in two passes.

### Pass 1: Close The Common SNMP Dashboard

Render the switch-oriented panels that current contracts already support well:

- device identity header;
- CPU stat and time series;
- memory stat and time series;
- interface traffic time series;
- interface status table;
- interface speed table;
- interface error/discard quality panel;
- interface broadcast ratio panel;
- traffic mix if packet-rate recording rules are available.

This pass should make the generated dashboard feel much closer to the screenshot without adding unsupported hardware/compliance panels.

### Pass 2: Optional Hardware And Operations Blocks

Add optional panels only when their data sources are available:

- temperature sensors;
- fan status;
- power status;
- transceiver power;
- active alerts;
- recent events;
- config backup and compliance;
- routing and layer-2 summaries.

Each optional block must declare its source and missing-data behavior before being rendered.

## Acceptance Criteria

The next implementation should be accepted when:

- generated dashboard uses the screenshot-inspired section order;
- generated dashboard has a device header and KPI strip;
- supported common SNMP panels render with real recording-rule expressions;
- unsupported hardware/event/compliance sections are omitted, not empty;
- panel bindings still trace `panel -> metric group -> strategy -> record`;
- dry-run response reports rendered, skipped, and missing-capability panels;
- demo2 can import the generated dashboard into Grafana and show sample data through VictoriaMetrics.

Current automated acceptance adds one concrete closure case:

```text
TestMetricCapabilityContractResolverMaterializesHuaweiS5735ClosedLoopDashboardByTarget
```

It verifies the Huawei/S5735 leaf strategy inheritance, the dashboard template chain, SNMP evidence-table panels, platform evidence-link panels, and inherited recording-rule panels in a single materialized dashboard. The remaining acceptance is quick_env seed/sample-data enrichment and browser-level Grafana readback.

## Final Visual Contract For Remaining Grafana Closure

The screenshot is treated as an operational information-architecture reference, not a pixel-perfect design. The Grafana dashboard should preserve the network-operator reading order:

- top identity and instant state: device, vendor/model, location, uptime, last poll, health, availability, active alerts, CPU, memory, temperature, power and fan if present;
- investigation center: top interfaces, port map, resource curves, traffic curves, packet or traffic mix;
- network-layer evidence: L2 neighbors, MAC table, ARP table, VLAN and STP summaries when inherited strategy capabilities expose those metric groups;
- platform evidence: active alerts, recent events, config backup, compliance, and policy-generated links back to OneOPS evidence.

Panel keys are the compatibility contract. Layout and Grafana panel options can be tuned, but stable keys must remain traceable through:

```text
target concrete strategy
  -> inherited parent / ancestor strategies
  -> effective metric capability contract
  -> dashboard panel binding
  -> Grafana panel JSON
```

Remaining visual tuning is limited to the SNMP switch dashboard family. It should not introduce a custom Grafana plugin, a new dashboard editor, or Grafana-side dashboard inheritance. Dashboard inheritance remains a OneOPS materialization concern: OneOPS resolves the template tree and saves one concrete dashboard into Grafana.
