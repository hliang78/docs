# 2026-06-14 SNMP Network Strategy Generic Dashboard Panel Design

## 1. Goal

This spec defines the generic strategy dashboard panel design for `SNMP网络监控策略`.

The goal is to keep the dashboard reading rhythm and operations ergonomics inspired by the CE168 layout, while rewriting the panel semantics into a vendor-neutral, generic network-device dashboard.

This spec is specifically about:

- fixed dashboard structure;
- fixed panel families;
- panel semantics and capability mapping;
- stable degradation behavior when capabilities are missing.

This spec is not about:

- CE168 chassis-specific panel carryover;
- Grafana JSON implementation details;
- DB schema changes;
- final PromQL or recording rule definitions.

## 2. Core Direction

The dashboard must follow these fixed product rules:

- layout rhythm may reference CE168;
- macro layout should preserve the CE168-style skeleton: full-width identity strip, one-row triage ribbon, upper analytics band, lower-left module operations band, and lower-right compact health cluster;
- panel semantics must be rewritten for generic network devices;
- CE168-specific board labels, chassis slot names, and Huawei-only titles must not be carried over;
- `Huawei control plane CPU/Memory` must be normalized into generic `CPU Now` and `Memory Now`;
- interface status must always be displayed;
- interface status must always use the `Interface State by Module` presentation model;
- `Error Ports`, `Discard Ports`, `Temperature`, `Fan Status`, and `Power Supply` are fixed panels, not optional add-ons;
- `MAC / ARP / VLAN / STP` and `Route / OSPF / BGP` should be rendered as compact summary panels instead of lower-half detail tables.

## 3. Design Principles

### 3.1 Stable Reading Order

The dashboard should preserve a stable operations scan path:

1. identify the device;
2. check overall health and current alarms;
3. inspect interface operations and traffic;
4. inspect resource, quality, and hardware health;
5. inspect L2/L3 summary and optical edge signals.

This scan order should not drift by vendor or device model.

### 3.2 Fixed Structure, Capability-Filled Values

The dashboard should be structurally stable.

That means:

- panel positions stay fixed;
- panel titles stay fixed;
- missing capabilities degrade panel content, not the whole layout.

The dashboard should not reflow based on which SNMP metrics happen to exist on one target.

### 3.3 Generic Semantics, Not Device Copying

This dashboard is not a reduced CE168 clone.

CE168 contributes:

- layout rhythm;
- summary-first organization;
- operational scanning discipline.

CE168 must not contribute:

- hard-coded chassis slot labels such as `100GE5/0`;
- vendor-specific titles such as `Huawei VRP Control Plane CPU`;
- fixed optical ranking titles such as `Top 4 by Rx Power`;
- device-specific lower-half panel semantics.

### 3.4 Summary Before Detail

The main strategy dashboard should prefer:

- health summaries;
- hotspot rankings;
- trend panels;
- compact L2/L3 summaries.

It should not default to large MAC/ARP/VLAN/STP/BGP/OSPF evidence tables in the primary strategy view.

Those can remain secondary or drill-down responsibilities elsewhere.

### 3.5 CE168 Layout Anchors

CE168 should be treated as a layout anchor, not a content template and not a screenshot to be recopied.

The generic dashboard should preserve these structural cues:

- a full-width `Device Identity` strip at the top;
- one continuous triage ribbon directly below it using same-height summary cards;
- an upper analytics band where utilization, packet mix, compact network summary, packet rate, and throughput are read left-to-right;
- a lower-left module-oriented operations area where interface state is rendered as stacked board/module strips rather than one centered stat card;
- a lower-right compact health cluster for temperature, power, fan, optical, and error/discard counters.

CE168 should therefore influence:

- hierarchy;
- row rhythm;
- panel density;
- left-versus-right visual weight;
- the placement of summary versus detail zones.

CE168 must not directly dictate:

- vendor text;
- CE168 board names;
- Huawei-specific resource wording;
- exact panel titles or device-only evidence blocks.

## 4. Fixed Dashboard Structure

The strategy dashboard should use a fixed 24-column layout with CE168-style bands and nested zones.
It should not be modeled as five unrelated equal-weight rows.

### 4.1 Layout Map

```text
24-column dashboard skeleton

+----------------------------------------------------------------------------------+
| Device Identity                                                                  |
+----------------------------------------------------------------------------------+
| Overall | Alerts | CPU Now | Memory Now | Ports Up | Ports Down triage zone      |
+----------------------------------------------------------------------------------+
| Interface Utilization | Traffic Mix | L2/Routing compact stack | PPS | Throughput|
+----------------------------------------------------------------------------------+
| Interface State by Module + Interface Quality | CPU / Memory Trend | Health Cluster|
|                                                |                    | Err/Discards  |
|                                                |                    | Temp / Power  |
|                                                |                    | Fan / Optics  |
+----------------------------------------------------------------------------------+
| Interface Traffic            | Interface Discards           | Interface Broadcast |
+----------------------------------------------------------------------------------+
```

This map is the required layout reference.
It is intentionally schematic:

- it defines placement and visual priority;
- it does not copy CE168 titles or slot labels;
- it allows small renderer-level adjustments inside each zone without changing the scan path.

### 4.2 Band A: Identity Strip

- `Device Identity` at `24x3`

Purpose:

- identify the device immediately;
- preserve the CE168 full-width header behavior;
- keep metadata above all live-state panels.

### 4.3 Band B: Triage Ribbon

- `Overall Health` at `4x4`
- `Active Alerts` at `4x4`
- `CPU Now` at `4x4`
- `Memory Now` at `4x4`
- `Ports Up` at `4x4`
- `Ports Down` at `4x4`

Purpose:

- show the current state at a glance;
- visually match the CE168 top summary-card ribbon pattern;
- support quick first-level triage.

Notes:

- the rightmost triage slot should behave like a CE168-style down-state zone;
- `Ports Down` remains the fixed generic panel title even if the renderer internally shows one or more red sub-stats inside that slot.

### 4.4 Band C: Upper Analytics Band

- `Interface Utilization Top N` at `8x9`
- `Traffic Mix` at `4x9`
- `L2 Summary` + `Routing Summary` in one compact shared summary lane at roughly `3x9`
- `Packets Per Second` at roughly `4x9`
- `Traffic Throughput` at roughly `5x9`

Purpose:

- show the busiest interfaces;
- show packet composition;
- place compact L2/L3 summary in the same upper-band position that CE168 uses for `Routing & Layer 2`;
- keep the left side operationally heavier than the right side, as in the CE168 layout;
- keep packet-rate and byte-throughput trends adjacent, not separated by a whole row;
- show total traffic trend.

Rules:

- `L2 Summary` and `Routing Summary` should render as two compact stacked summaries inside one narrow lane, not as two wide bottom-row cards;
- this band is summary-first and trend-first;
- `Interface State by Module` does not belong here.

### 4.5 Band D: Lower Operations + Health Band

- left operations zone at roughly `8x10`
  - `Interface State by Module`
  - `Interface Quality Hotspots` as a compact secondary list/table in the same zone
- center trend zone at roughly `6x10`
  - `CPU / Memory Trend`
- right health cluster at roughly `10x10`
  - `Error Ports`
  - `Discard Ports`
  - `Temperature`
  - `Power Supply`
  - `Fan Status`
  - `Optical Rx/Tx Ranking`

Purpose:

- render module-oriented interface state where CE168 actually places it;
- keep CPU/memory trend visible beside interface operations rather than moving it into a separate bottom analytics row;
- group hardware and edge-health panels into one compact right-hand cluster;
- provide fixed hardware status visibility across device families.

Rules:

- `Interface State by Module` is the primary occupant of the lower-left zone and should render as stacked module strips or grouped slot blocks, not as a centered stat-only card;
- `Interface Quality Hotspots` should no longer occupy an isolated full-width row; it belongs beside or below the module state inside the left operations zone;
- `Error Ports` and `Discard Ports` are fixed panel families, but in this CE168-derived layout they render as compact health counters inside the right cluster rather than full-width standalone row cards;
- `Optical Rx/Tx Ranking` should anchor the far-right edge of the lower cluster as a slim ranking strip or paired compact ranking lists.

### 4.6 Exact 24-Column Allocation

The following grid is the normative placement contract for the generic CE168-derived layout.

| Panel or Zone | x | y | w | h | Notes |
| --- | ---: | ---: | ---: | ---: | --- |
| `Device Identity` | 0 | 0 | 24 | 3 | Full-width identity strip |
| `Overall Health` | 0 | 3 | 4 | 4 | Triage ribbon |
| `Active Alerts` | 4 | 3 | 4 | 4 | Triage ribbon |
| `CPU Now` | 8 | 3 | 4 | 4 | Triage ribbon |
| `Memory Now` | 12 | 3 | 4 | 4 | Triage ribbon |
| `Ports Up` | 16 | 3 | 4 | 4 | Triage ribbon |
| `Ports Down` | 20 | 3 | 4 | 4 | Triage ribbon; may contain internal red sub-stats |
| `Interface Utilization Top N` | 0 | 7 | 8 | 9 | Upper analytics band |
| `Traffic Mix` | 8 | 7 | 4 | 9 | Upper analytics band |
| `L2 / Routing Summary Lane` | 12 | 7 | 3 | 9 | Shared compact summary lane |
| `Packets Per Second` | 15 | 7 | 4 | 9 | Upper analytics band |
| `Traffic Throughput` | 19 | 7 | 5 | 9 | Upper analytics band |
| `Left Operations Zone` | 0 | 16 | 8 | 10 | Lower-left compound zone |
| `CPU / Memory Trend` | 8 | 16 | 6 | 10 | Lower center trend zone |
| `Right Health Cluster` | 14 | 16 | 10 | 10 | Lower-right compound zone |

### 4.7 Compound Zone Subgrid

The compound zones above must resolve into the following internal allocations.

| Panel | x | y | w | h | Parent Zone |
| --- | ---: | ---: | ---: | ---: | --- |
| `L2 Summary` | 12 | 7 | 3 | 4 | `L2 / Routing Summary Lane` |
| `Routing Summary` | 12 | 11 | 3 | 5 | `L2 / Routing Summary Lane` |
| `Interface State by Module` | 0 | 16 | 8 | 7 | `Left Operations Zone` |
| `Interface Quality Hotspots` | 0 | 23 | 8 | 3 | `Left Operations Zone` |
| `Error Ports` | 14 | 16 | 2 | 2 | `Right Health Cluster` |
| `Discard Ports` | 14 | 18 | 2 | 2 | `Right Health Cluster` |
| `Temperature` | 14 | 20 | 2 | 6 | `Right Health Cluster` |
| `Power Supply` | 16 | 16 | 3 | 10 | `Right Health Cluster` |
| `Fan Status` | 19 | 16 | 3 | 10 | `Right Health Cluster` |
| `Optical Rx/Tx Ranking` | 22 | 16 | 2 | 10 | `Right Health Cluster` |

### 4.8 Placement Invariants

- `L2 Summary` and `Routing Summary` must remain in the shared upper summary lane and must not be promoted into separate wide bottom cards.
- `Interface State by Module` must remain the dominant element of the lower-left zone and must not migrate into the upper analytics band.
- `Interface Quality Hotspots` must remain attached to the module zone and must not reappear as a standalone middle-row panel.
- `Error Ports`, `Discard Ports`, `Temperature`, `Power Supply`, `Fan Status`, and `Optical Rx/Tx Ranking` must remain members of one right-side health cluster.
- small renderer-level padding changes are allowed, but changes that alter this scan path are out of contract.
- the existing CE168-derived 24-column skeleton must remain unchanged; new switch capability panels may only be added below the current bottom edge.

### 4.9 Band E: Bottom Extension Band

- `Interface Traffic`
- `Interface Discards`
- `Interface Broadcast`

Purpose:

- copy the three interface-observability sections from the network-device monitoring dashboard into every `OneOPS SNMP Switch Ops` dashboard family;
- expand switch dashboard capability without moving any existing panel;
- keep the added interface sections visually separate from the locked CE168-derived skeleton.

Rules:

- this band is additive only and must not replace `Traffic Throughput`, `Discard Ports`, or `Traffic Mix (by Packets)`;
- it must render below the current dashboard bottom edge;
- root shared dashboard and all `OneOPS SNMP Switch Ops/*` child dashboards must inherit the same three extra panels;
- missing capability should leave the panel visible but empty.

### 4.10 Bottom Extension Allocation

The bottom extension band begins after the fixed skeleton and uses the next available row block.

| Panel | x | y | w | h | Notes |
| --- | ---: | ---: | ---: | ---: | --- |
| `Interface Traffic` | 0 | 26 | 8 | 6 | Bottom extension band |
| `Interface Discards` | 8 | 26 | 8 | 6 | Bottom extension band |
| `Interface Broadcast` | 16 | 26 | 8 | 6 | Bottom extension band |

## 5. Panel Definitions

### 5.1 Device Identity

- Title: `Device Identity`
- Role: show device name, model, vendor, platform, version, location, and uptime.
- Visual type: `text` or compact `stat list`
- Intent: identity

### 5.2 Overall Health

- Title: `Overall Health`
- Role: summarize whole-device health for first-look triage.
- Visual type: `stat`
- Intent: state
- Notes: should aggregate CPU, memory, interface state, and interface quality signals where available.

### 5.3 Active Alerts

- Title: `Active Alerts`
- Role: show current alert count.
- Visual type: `stat`
- Intent: state
- Notes: platform alert evidence is preferred; local threshold aggregation is a fallback.

### 5.4 CPU Now

- Title: `CPU Now`
- Role: show current CPU utilization.
- Visual type: `stat`
- Intent: state
- Notes: this is the generic replacement for vendor-specific control-plane CPU wording.

### 5.5 Memory Now

- Title: `Memory Now`
- Role: show current memory utilization.
- Visual type: `stat`
- Intent: state
- Notes: this is the generic replacement for vendor-specific control-plane memory wording.

### 5.6 Ports Up

- Title: `Ports Up`
- Role: count currently up monitored ports.
- Visual type: `stat`
- Intent: state

### 5.7 Ports Down

- Title: `Ports Down`
- Role: count currently down monitored ports.
- Visual type: `stat`
- Intent: state

### 5.8 Interface Utilization Top N

- Title: `Interface Utilization Top N`
- Role: rank busiest interfaces by utilization.
- Visual type: horizontal `bargauge`
- Intent: hotspot
- Notes: should prefer utilization over raw throughput ranking.

### 5.9 Traffic Mix

- Title: `Traffic Mix (by Packets)`
- Role: show packet composition by traffic class.
- Visual type: `piechart`
- Intent: composition

### 5.10 Interface State by Module

- Title: `Interface State by Module`
- Role: always show interface-state distribution in module-oriented form.
- Visual type: grouped module strip matrix, grouped `stat grid`, or grouped compact `stat list`
- Intent: state

This panel is mandatory and has special behavior:

- it always exists;
- it always keeps this title;
- it does not fall back to `Port State` naming;
- in CE168-derived layout it belongs to the lower-left operations zone rather than the upper analytics band;
- with module recognition, it groups interfaces by real board/module/slot;
- without module recognition, it still renders the same panel shape using a virtual `Default Module`.

### 5.11 Traffic Throughput

- Title: `Traffic Throughput`
- Role: show total input/output traffic trend.
- Visual type: `timeseries`
- Intent: trend

### 5.12 CPU / Memory Trend

- Title: `CPU / Memory Trend`
- Role: show resource trend over time.
- Visual type: `timeseries`
- Intent: trend

### 5.13 Interface Quality Hotspots

- Title: `Interface Quality Hotspots`
- Role: rank interfaces by error/discard severity.
- Visual type: compact `table` or compact ranked `stat list`
- Intent: hotspot
- Notes: in CE168-derived layout this panel should be folded into the lower-left operations zone rather than taking a dedicated full-width row.

### 5.14 Packets Per Second

- Title: `Packets Per Second`
- Role: show aggregated packet-rate trend.
- Visual type: `timeseries`
- Intent: trend

### 5.15 Error Ports

- Title: `Error Ports`
- Role: count ports currently showing error activity.
- Visual type: `stat`
- Intent: state
- Notes: fixed panel family, but should render as a compact counter inside the right-side health cluster.

### 5.16 Discard Ports

- Title: `Discard Ports`
- Role: count ports currently showing discard activity.
- Visual type: `stat`
- Intent: state
- Notes: fixed panel family, but should render as a compact counter inside the right-side health cluster.

### 5.17 Temperature

- Title: `Temperature`
- Role: show device or module temperature state.
- Visual type: compact `stat list`
- Intent: state
- Notes: belongs to the lower-right health cluster.

### 5.18 Fan Status

- Title: `Fan Status`
- Role: show fan component state.
- Visual type: compact `stat list`
- Intent: state
- Notes: belongs to the lower-right health cluster.

### 5.19 Power Supply

- Title: `Power Supply`
- Role: show PSU component state.
- Visual type: compact `stat list`
- Intent: state
- Notes: belongs to the lower-right health cluster.

### 5.20 L2 Summary

- Title: `L2 Summary`
- Role: summarize MAC, ARP, VLAN, and STP state.
- Visual type: compact `stat list`
- Intent: summary
- Notes: should render in the narrow upper-band summary lane, stacked with `Routing Summary`.

### 5.21 Routing Summary

- Title: `Routing Summary`
- Role: summarize route, OSPF, and BGP state.
- Visual type: compact `stat list`
- Intent: summary
- Notes: should render in the narrow upper-band summary lane, stacked with `L2 Summary`.

### 5.22 Optical Rx/Tx Ranking

- Title: `Optical Rx/Tx Ranking`
- Role: show best/worst optical power signals where available.
- Visual type: compact ranking `stat list`
- Intent: hotspot
- Notes: should render as a slim far-right ranking strip inside the lower-right health cluster.

### 5.23 Interface Traffic

- Title: `接口流量`
- Role: copy the interface traffic section from the network-device monitoring dashboard into the switch dashboard family.
- Visual type: `timeseries`
- Intent: trend
- Notes: additive bottom-band panel; it must not replace `Traffic Throughput`.

### 5.24 Interface Discards

- Title: `接口丢包`
- Role: copy the interface discard section from the network-device monitoring dashboard into the switch dashboard family.
- Visual type: `timeseries`
- Intent: trend
- Notes: additive bottom-band panel; it must not replace `Discard Ports`.

### 5.25 Interface Broadcast

- Title: `接口广播`
- Role: copy the interface broadcast section from the network-device monitoring dashboard into the switch dashboard family.
- Visual type: `timeseries`
- Intent: trend
- Notes: additive bottom-band panel; it must not replace `Traffic Mix (by Packets)`.

## 6. Capability Mapping

Panel existence is fixed.
Capability controls whether the panel is live, partial, unsupported, or empty.

### 6.1 Identity And Triage Panels

`Device Identity`

- preferred capabilities: `sys_name`, `sys_descr`, `sys_object_id`, `sys_uptime`, `sys_location`

`Overall Health`

- aggregate capabilities: `cpu_usage_direct`, `memory_usage_direct`, `if_oper_status`, `if_in_error_rate`, `if_out_error_rate`, `if_in_discard_rate`, `if_out_discard_rate`

`Active Alerts`

- preferred capability: `platform_active_alert_evidence`
- fallback: local threshold-based abnormal count

`CPU Now`

- preferred capability: `cpu_usage_direct`
- fallback: `cpu_usage_from_idle`

`Memory Now`

- preferred capability: `memory_usage_direct`
- fallback: `memory_usage_used_total`, `memory_usage_free_total`

`Ports Up` / `Ports Down`

- required capability: `if_oper_status`

### 6.2 Interface Operation Panels

`Interface Utilization Top N`

- required capabilities: `if_in_rate`, `if_out_rate`, `if_speed_bps`
- filtering assist: `if_admin_status`
- labeling assist: `if_name`, `if_alias`

`Traffic Mix (by Packets)`

- preferred capabilities:
  - `if_in_unicast_pps`
  - `if_in_multicast_pps`
  - `if_in_broadcast_pps`
  - `if_out_unicast_pps`
  - `if_out_multicast_pps`
  - `if_out_broadcast_pps`

`Interface State by Module`

- required capability: `if_oper_status`
- labeling assist: `if_name`, `if_alias`
- module grouping assist: `entity_name`, `entity_class`, or equivalent module mapping

`Traffic Throughput`

- required capabilities: `if_in_rate`, `if_out_rate`

### 6.3 Resource And Quality Panels

`CPU / Memory Trend`

- preferred capabilities: `cpu_usage_direct`, `memory_usage_direct`

`Interface Quality Hotspots`

- preferred capabilities:
  - `if_in_error_rate`
  - `if_out_error_rate`
  - `if_in_discard_rate`
  - `if_out_discard_rate`
- optional enhancement: `if_crc_error_rate`

`Interface Traffic`

- required capabilities: `if_in_rate`, `if_out_rate`

`Interface Discards`

- required capabilities: `if_in_discard_rate`, `if_out_discard_rate`

`Interface Broadcast`

- preferred capabilities: `if_in_broadcast_ratio`, `if_out_broadcast_ratio`

`Packets Per Second`

- required packet-rate capability derived from interface packet counters

`Error Ports`

- required capabilities: `if_in_error_rate`, `if_out_error_rate`
- optional enhancement: `if_crc_error_rate`

`Discard Ports`

- required capabilities: `if_in_discard_rate`, `if_out_discard_rate`

### 6.4 Hardware Panels

`Temperature`

- preferred capabilities: `device_temperature_celsius`, `sensor_temperature_celsius`

`Fan Status`

- preferred capability: `device_fan_status`

`Power Supply`

- preferred capability: `device_power_status`

### 6.5 Summary Panels

`L2 Summary`

- preferred capabilities:
  - `l2_mac_identity` or equivalent MAC count support
  - `l3_arp_identity` or equivalent ARP count support
  - `l2_vlan_identity` or equivalent VLAN count support
  - `l2_stp_identity` or equivalent STP count/state support

`Routing Summary`

- preferred capabilities:
  - `ipv4_route_count`
  - `ipv6_route_count`
  - `ospf_neighbor_total`
  - `ospf_full_total`
  - `bgp_neighbor_total`
  - `bgp_established_total`

`Optical Rx/Tx Ranking`

- preferred capabilities:
  - `optical_rx_power_dbm`
  - `optical_tx_power_dbm`

## 7. Panel State Model

Every panel should resolve into one of four states:

- `Live`
- `Partial`
- `Unsupported`
- `Empty`

Definitions:

- `Live`: the panel has the required capabilities and renders full value.
- `Partial`: the panel has some, but not all, useful capabilities and renders a reduced result.
- `Unsupported`: the current SNMP strategy does not expose the needed capability.
- `Empty`: the capability exists, but there is no relevant current sample, such as no optical modules or no routing neighbors.

## 8. Degradation Rules

### 8.1 Global Rule

Missing capability should degrade the panel content, not remove the panel from layout.

The strategy dashboard should preserve:

- fixed structure;
- fixed visual reading order;
- fixed panel titles.

### 8.2 Selected Panel-Specific Rules

`Overall Health`

- if CPU/memory are absent, derive a weaker summary from interface state and quality signals;
- if too little data exists, render `Insufficient Metrics`.

`CPU Now` / `Memory Now`

- if absent, render `Not Supported`.

`Interface Utilization Top N`

- if `if_speed_bps` is absent but rates exist, degrade to throughput ranking while keeping the panel position and title stable.

`CPU / Memory Trend`

- if only one of CPU or memory exists, render the single trend and mark the panel `Partial`.

`Interface Quality Hotspots`

- if only errors or only discards exist, still render as `Partial`.

`Temperature` / `Fan Status` / `Power Supply`

- if only device-level status exists, render a compact single summary;
- if component rows exist, render component list;
- if unsupported, show `Unsupported by current device strategy`.

`L2 Summary`

- keep fixed summary rows for `MAC`, `ARP`, `VLAN`, and `STP`;
- unsupported sub-items should show `Unsupported`, not disappear.

`Routing Summary`

- keep fixed summary rows for `IPv4 Routes`, `IPv6 Routes`, `OSPF`, and `BGP`;
- if OSPF or BGP is not exposed, show `Not Exposed`.

`Optical Rx/Tx Ranking`

- if optical metrics do not exist, show `No Optical Metrics`.

## 9. Interface State By Module Rules

This panel has a stronger contract than the others.

### 9.1 Name Contract

The title must always remain:

- `Interface State by Module`

It should not rename itself to `Port State` or other fallback wording.

### 9.2 Grouping Priority

Module grouping should resolve in this order:

1. explicit entity/module mapping;
2. parsing from interface naming patterns;
3. fallback virtual grouping.

### 9.3 Fallback Group

If no real module boundary can be resolved, the panel should still render with one virtual group:

- `Default Module`

### 9.4 Suggested Output Shape

The panel should render stable group summaries such as:

- `module_name`
- `ports_total`
- `ports_up`
- `ports_down`
- `health_state`

This keeps panel structure stable across devices with and without explicit chassis/module metadata.

## 10. Naming Rules

The generic dashboard must use vendor-neutral titles.

Preferred titles:

- `CPU Now`
- `Memory Now`
- `Interface State by Module`
- `Traffic Mix (by Packets)`
- `L2 Summary`
- `Routing Summary`
- `Optical Rx/Tx Ranking`

Forbidden carryover examples:

- `Huawei VRP Control Plane CPU`
- `Huawei VRP Control Plane Memory`
- `100GE5/0`
- `100GE6/0`
- `40GE7/0`
- `10GE8/0`
- `Top 4 by Rx Power`
- `Last 4 by Rx Power`

Those CE168 strings may remain implementation or drill-down details, but they should not define the generic strategy dashboard surface.

## 11. Recommended Outcome

The `SNMP网络监控策略` dashboard should be defined as:

- one fixed CE168-derived banded strategy dashboard;
- one fixed set of twenty-two core panels plus one additive bottom extension band;
- one fixed 24-column placement contract with locked compound-zone subgrids;
- one fixed bottom extension row for `接口流量` / `接口丢包` / `接口广播`;
- one fixed `Interface State by Module` contract;
- one fixed lower-left module operations zone and lower-right compact health cluster;
- fixed compact summary placement in the upper analytics band;
- capability-driven values with stable degradation;
- CE168-inspired layout rhythm without CE168-specific panel semantics.

This should become the generic dashboard contract for network-device SNMP strategies before any vendor/model overlays add device-specific refinements.

## 12. Implementation Contract

The implementation should follow the simplest possible static model.

### 12.1 Static Dashboard Ownership

- one strategy set binds one root dashboard through `platform_teleabs_strategy_set_dashboard_binding`;
- one strategy owns one static strategy dashboard;
- strategy dashboards are stored in `grafana_dashboard`;
- strategy dashboards are not generated per target device.

### 12.2 Static Tree Contract

- the root dashboard remains the strategy-set entry dashboard;
- strategy dashboards form a static tree through `grafana_dashboard.parent_id`;
- dashboard tree shape follows strategy parent-child relationships;
- target/device context is only used to select the best existing dashboard.

### 12.3 Dashboard Resource Scope Contract

Each strategy dashboard must persist the same resource scope carried by its owning strategy:

- `manufacturer_id`
- `catalog_id`
- `platform_id`
- `device_model_ids`

The root dashboard should remain broad:

- `parent_id = ''`
- `manufacturer_id = ''`
- `platform_id = ''`
- `device_model_ids = []`
- `catalog_id` may stay as the strategy-set catalog anchor, such as `SWITCH`

### 12.4 Runtime Selection Contract

When `OneOPS SNMP Switch Ops` or another strategy-set root dashboard is opened for one device:

1. locate the bound root dashboard from the strategy set;
2. traverse the static child dashboard tree;
3. select the most specific matching dashboard by:
   - `device_model`
   - `platform`
   - `manufacturer`
   - `catalog`
   - fallback to `root`

If a more specific child dashboard is matched under one root, the UI should prefer that child and should not surface the same root again as a redundant fallback option.

### 12.5 Non-Goal

The main product path should not depend on:

- target-time dashboard cloning;
- target-time dashboard tree materialization;
- per-target duplicated dashboard instances as the source of truth.

### 12.6 API Compatibility Note

Some existing API routes may still keep historical names such as:

- `.../grafana/dashboards/save/by-target`
- `.../grafana/dashboards/save-and-sync/by-target`
- `.../grafana/dashboard-tree/materialize/dry-run/by-target`
- `.../grafana/dashboard-tree/save/by-target`

Those route names are compatibility shells only.

They should be interpreted as:

- resolve which static strategy dashboard tree applies to the target;
- save or sync that static tree;
- return the root dashboard entry plus tree-level persistence metadata.

They should not be interpreted as:

- creating one duplicated dashboard instance per target device.

The same compatibility principle applies to auxiliary persistence tables such as:

- `platform_teleabs_strategy_set_dashboard_target_binding`
- `platform_teleabs_strategy_set_dashboard_save_summary`
- `platform_teleabs_strategy_set_dashboard_snapshot`

Those tables may still be written for compatibility, audit, or debugging, but they are no longer the source of truth for whether the static dashboard tree exists or can be selected at runtime.

If those compatibility audit tables are absent, static dashboard save/sync/open flows must continue to work. Only audit-oriented endpoints such as save-batch history or save-batch detail may return an explicit "compatibility audit unavailable" style error.

The same rule applies to dashboard content snapshots: snapshot rows are optional audit artifacts for change history, not a prerequisite for saving, syncing, selecting, or opening the static dashboard tree.

### 12.7 Customer-Facing Presentation Contract

Customer-facing pages should present the monitoring choice in business language, not dashboard-engine language.

That means:

- the `监控方案` selector should display applied strategy sets, not raw dashboard names;
- the selected option should represent `one applied strategy set -> one resolved dashboard result`;
- the UI may open one matched static dashboard behind the scenes, but it should not force the customer to understand root/child dashboard topology;
- customer-facing pages should not display internal labels such as `Root Dashboard`, `Root fallback`, `Root 兜底`, `dashboard_role`, `owner_strategy_id`, or similar implementation hints;
- matching/granularity text such as `device_model/platform/manufacturer/catalog/root` is useful for debugging, but should not appear in the normal customer view.

The intended product wording is:

- customer chooses a `监控方案` = one applied strategy set;
- system opens the dashboard resolved for that strategy set and that device;
- dashboard selection mechanics remain internal.

## 13. Next-Phase Simplification: Strategy Set to Real Collection Content

The next cleanup target is not the dashboard surface itself, but the strategy and strategy-set pipeline that produces real collection content.

That pipeline is currently too mixed:

- some parts behave like selector logic;
- some parts behave like inheritance logic;
- some parts behave like runtime materialization;
- some parts behave like persistence/audit side effects;
- some parts blur `dashboard selection`, `collection definition`, and `target-time projection`.

The next phase should separate those concerns into one simple contract.

### 13.1 Desired Responsibility Split

`策略` should become the atomic collection-definition unit.

One strategy should define:

- what capability family it represents;
- what resource scope it applies to;
- what collection semantics it contributes;
- what dashboard it owns.

`策略集` should become the selection and composition unit.

One strategy set should define:

- which catalog/domain it applies to;
- how one device is matched into the set;
- which strategy tree is composed for that device;
- which root dashboard is bound to that set.

`目标设备` should not create new definitions.

The device should only provide runtime context used to:

- decide which strategy set applies;
- decide which branch in the strategy tree applies;
- fill variables for execution and dashboard opening.

### 13.2 Single Authoritative Resolution Pipeline

The long-term authoritative flow should be:

1. resolve target device context;
2. match the target to one applicable strategy set;
3. load the static strategy tree from that set;
4. resolve parent-child inheritance inside the strategy tree;
5. materialize one final collection contract for execution;
6. open the statically owned dashboard resolved for that same branch.

That final collection contract should be the only object used to drive:

- collection targets;
- Telegraf or collector inputs;
- SNMP OID groups and walk scope;
- recording rules or derived rules;
- alert-relevant metric availability;
- dashboard selection.

The system should not maintain separate contradictory truths for:

- strategy matching;
- collector content generation;
- dashboard selection;
- target-time dashboard instances.

### 13.3 Strategy as Collection Contract, Not Runtime Artifact Bag

One strategy should no longer be treated as a loose container of mixed concerns.

It should become a clean collection contract with these dimensions:

- `scope`
  - manufacturer
  - catalog
  - platform
  - device_model
- `capabilities`
  - which metric families are expected
  - which optional metric families can degrade
- `collection content`
  - which collector/input templates are enabled
  - which OID/profile fragments are enabled
  - which rule fragments are enabled
- `dashboard ownership`
  - which static dashboard belongs to this strategy

This keeps one strategy readable and testable without requiring target-time side tables to reconstruct its meaning.

### 13.4 Strategy Set as Selector + Composer

One strategy set should not directly behave like a target-time generated output object.

It should do only two jobs:

1. decide whether this target belongs to this strategy set;
2. provide the strategy tree that will be composed for that target.

That means the strategy set is responsible for:

- selector constraints;
- catalog/domain boundaries;
- strategy ordering and parent-child structure;
- root dashboard binding.

It is not responsible for:

- creating per-target dashboard copies;
- becoming a second collector-definition language;
- carrying duplicated runtime persistence facts that can be derived from the static tree.

### 13.5 Real Collection Content Must Converge With Dashboard Branch

The branch used to choose the final dashboard must be the same branch used to choose the final collection content.

For example:

- if a Huawei VRP branch is selected for dashboard display, the same Huawei VRP branch must define the effective SNMP collection content;
- if only a generic switch branch matches, the generic switch collection contract must be the effective collector content;
- dashboard resolution and collection resolution must never diverge into two different branches for the same target.

This is the most important simplification rule for the next phase.

### 13.6 Cleanup Targets for the Next Phase

The next phase should explicitly reduce or remove logic that keeps multiple parallel truths alive.

Priority cleanup targets:

- target-time dashboard materialization logic that still survives under compatibility route names;
- old binding/audit tables being consulted as if they were runtime facts;
- collector-content generation paths that do not clearly derive from the chosen strategy branch;
- mixed ownership logic where strategy, strategy set, and runtime target all compete to define the final effective content.

### 13.7 Deliverable for the Next Spec

The next design/cleanup spec should focus on:

- how one strategy maps to one atomic collection contract;
- how one strategy set maps to one selectable strategy tree;
- how the chosen strategy branch becomes one final effective collector payload;
- how the same branch owns the final static dashboard;
- which existing tables, APIs, and services stop being authoritative.

In short:

- current phase: simplify static dashboard ownership and customer-facing dashboard selection;
- next phase: simplify strategy and strategy-set resolution into one authoritative collection-content pipeline.

## 14. SNMP Monitoring Task Generation Simplification

This section narrows the next-phase cleanup to the SNMP monitoring pipeline only.

### 14.1 Goal

For SNMP monitoring, the system must stop letting multiple layers compete to define the final collection payload.

The authoritative rule becomes:

`target device -> one strategy set -> one matched leaf branch -> parent-chain inheritance -> one final SNMP collection payload`

That same matched branch must also own:

- the static dashboard branch;
- the fixed recording-rule capability set;
- the final SNMP collection payload sent to Agent or Controller.

### 14.2 Branch Selection Rule

Inside one SNMP strategy set:

- sibling strategies at the same level no longer co-compose one final payload;
- only one matched branch remains effective for one target;
- the final payload is produced from:
  - the matched leaf strategy;
  - plus its parent-chain inheritance.

This explicitly forbids:

- Huawei + H3C + Maipu sibling branches being merged together;
- one branch deciding dashboard while another branch decides payload;
- target-time projection tables becoming a second source of truth.

### 14.3 Responsibility Boundaries

For SNMP:

`strategy set`

- owns selector logic;
- owns static tree structure;
- owns root dashboard binding;
- may own only public runtime parameters such as interval, timeout, retries, credential reference.

`parent strategy`

- owns generic SNMP capabilities;
- owns cross-vendor baseline payload fragments;
- must not own vendor-specific CPU/memory/OID sources.

`child strategy`

- owns vendor/platform/model-specific payload fragments;
- may override same-name capabilities inherited from parent;
- owns the final branch-specific static dashboard.

### 14.4 Final Resolved Payload Contract

SNMP runtime resolution should converge into one explicit object:

`ResolvedSnmpCollectionPayload`

Minimum fields:

- `target`
  - device_id
  - device_code
  - address
  - port
  - credential reference
- `branch_identity`
  - strategy_set_id
  - matched_leaf_strategy_id
  - matched_strategy_chain
- `runtime_params`
  - interval
  - timeout
  - retries
  - walk mode
  - max repetitions
- `collection_definition`
  - enabled metric groups
  - enabled capability keys
  - enabled OID/profile fragments
  - final collector/input template config
  - final walk/get object set
- `derived_outputs`
  - recording-rule capability set
  - static dashboard ownership
  - alert-relevant metric availability

This payload becomes the only object allowed to define final SNMP collection content.

In the first implementation phase, the system must at least persist the branch identity pieces below through the apply pipeline:

- `strategy_set_id`
- `selected_strategy_id`
- `strategy_chain_ids`

And when `CreateTargets=true`, those same identity fields should be written into collection-target labels so downstream task generation, audit, and troubleshooting see the same resolved branch identity.

### 14.5 Existing Layer Re-mapping

The following layers should stop owning final-definition power for SNMP:

- `ApplyCommandV3`
  It may still carry orchestration input, but it must not remain the final source of SNMP content identity.
- `StrategyApplyPlan`
  It should become an execution translator, not the final content decider.
- `CollectionTarget`
  It should become a projection of the resolved payload, not a place that re-derives strategy meaning.
- `CollectionTaskGenerator`
  It should only transform resolved payload projections into task bundles.

The new single authoritative layer should be:

`SnmpCollectionPayloadResolver`

Its job:

1. resolve target device context;
2. match one strategy set;
3. select one leaf branch;
4. expand parent-chain inheritance;
5. build one final resolved SNMP payload.

### 14.6 First-Phase Execution Strategy

The first implementation phase should avoid rewriting the whole monitoring stack.

Instead, it should:

1. keep `CollectionTask`, `CollectionTaskDistribution`, Agent or Controller dispatch, and output or processor mechanisms unchanged;
2. keep `GenerateFromStrategySet(...)` as the downstream renderer;
3. move branch selection authority upward so SNMP selector sets always resolve one `selected_strategy_id`;
4. reject mixed-vendor multi-branch SNMP apply attempts inside one execution when they would otherwise require more than one payload branch;
5. let downstream rendering consume the already-resolved branch instead of re-composing siblings.

This allows SNMP to adopt the new single-branch model without forcing an immediate platform-wide rewrite.
