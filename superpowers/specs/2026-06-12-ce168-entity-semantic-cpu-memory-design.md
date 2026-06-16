# CE168 Entity Semantic CPU/Memory Design

## Background

Target device `172.21.165.11` is a Huawei CE16808 chassis switch. The current SNMP collection exposes Huawei Entity State metrics as entity-scoped rows. The runtime metric `snmp_huawei_entity_state_hwEntityCpuUsage` has 387 series for this target and only carries `index`, `hwEntityPhysicalIndex`, `agent_host`, `agent_code`, and `source` labels. It does not carry `entPhysicalName`, `entPhysicalDescr`, or an entity role label.

The existing dashboard-side `max(...)` aggregation reduces visual noise, but it is only an interim readability fix. It can report an LPU line card CPU value as the device-level CPU value, which is not the desired operational meaning for CE168-class chassis devices.

## Evidence

The raw ENTITY-MIB walk for `172.21.165.11` contains the hardware identity needed to classify the Huawei Entity State rows:

- MPU control-plane boards:
  - `17367041`: `CE-MPUD-HALF 9`, CPU `3`, memory `9`, temperature `28`
  - `17432577`: `CE-MPUD-HALF 10`, CPU `1`, memory `6`, temperature `28`
- LPU line cards:
  - `17104897`: `CEL36CQFD-G 5`, CPU `16`, memory `14`
  - `17170433`: `CEL36CQFD-G 6`, CPU `17`, memory `14`
  - `17235969`: `CEL36LQFD-G 7`, CPU `11`, memory `23`
  - `17301505`: `CEL48XSFD-G 8`, CPU `9`, memory `19`
- SFU fabric boards:
  - `18284545`, `18350081`, `18415617`, `18481153`, `18546689`, `18612225`
  - observed CPU range `5-6`, memory `16`

This means a plain device-level max CPU reports `17%` from LPU slot 6, while the MPU control-plane max is `3%`.

## Desired Semantics

For CE168 and similar chassis switches:

- Top-level device CPU should mean control-plane CPU from MPU boards.
- Top-level device memory should mean control-plane memory from MPU boards.
- LPU and SFU CPU, memory, and temperature should be shown as module hotspots, not collapsed into device-level CPU/memory.
- Hardware health should still count abnormal fan, power, module, and sensor state independently.

## Metric Model

Introduce an entity semantic layer that maps Huawei Entity State rows to ENTITY-MIB hardware identity:

- `entity_index`: ENTITY-MIB / Huawei Entity State index.
- `entity_name`: `entPhysicalName`.
- `entity_descr`: `entPhysicalDescr`.
- `entity_class`: `entPhysicalClass`.
- `entity_parent_index`: `entPhysicalContainedIn`.
- `entity_role`: one of `mpu_control_plane`, `lpu_line_card`, `sfu_fabric`, `power`, `fan`, `port`, `chassis`, `other`.

The preferred long-term Prometheus shape is to carry at least `entity_name` and `entity_role` on the Huawei Entity State series, so queries can use stable semantic selectors:

```promql
max(oneops:cpu_usage_direct:ratio{agent_host="$agent_host", entity_role="mpu_control_plane"})
max(oneops:memory_usage_direct:ratio{agent_host="$agent_host", entity_role="mpu_control_plane"})
topk(10, oneops:cpu_usage_direct:ratio{agent_host="$agent_host", entity_role=~"mpu_control_plane|lpu_line_card|sfu_fabric"})
```

If labels cannot be joined inside Telegraf directly, a controlled interim implementation may generate role-specific recording rules for known indexes discovered from ENTITY-MIB. That interim path must remain target-scoped and should be replaced by semantic labels when the collection pipeline can enrich table rows.

## Dashboard Model

The operations dashboard should use:

- `Control Plane CPU`: stat panel, max MPU CPU.
- `Control Plane Memory`: stat panel, max MPU memory.
- `CPU / Memory Trend`: two lines, max MPU CPU and max MPU memory.
- `Module Hotspots`: table or bar gauge for MPU/LPU/SFU CPU, memory, and temperature by entity name.
- `Thermal Hotspots`: top temperature entities, excluding empty port/noise rows.
- Existing fan, power, and traffic panels remain, with their expressions scoped by `agent_host`.

## Interface Visualization Refresh

The lower half of CE168-class dashboards should prioritize fast operational triage and spatial context over generic panel symmetry. Large chassis devices have too many interfaces and module signals for isolated single-purpose charts to remain readable.

### Lower Layout Strategy

Use a three-zone lower layout:

- Left `14` columns: interface operations zone.
- Right `10` columns: resource and hardware zone.
- Bottom full-width row: alerts, events, and compliance zone.

This layout should mirror common troubleshooting flow:

1. identify the busiest or most suspect interfaces
2. locate the interface on the chassis
3. inspect traffic and device resource behavior
4. review hardware state, alerts, and recent events

### Current Grafana Baseline

The current live CE168 Grafana dashboard was read directly from the Grafana API on `2026-06-13` and should be treated as the layout source of truth unless a deliberate redesign is agreed first. The live panel grid is:

- Top summary row
  - `Overall Health`: `x=0 y=3 w=4 h=4`
  - `Active Alerts`: `x=4 y=3 w=4 h=4`
  - `Huawei VRP Control Plane CPU`: `x=8 y=3 w=4 h=4`
  - `Huawei VRP Control Plane Memory`: `x=12 y=3 w=4 h=4`
  - `Ports Up`: `x=16 y=3 w=4 h=4`
  - `Ports Down`: `x=20 y=3 w=4 h=4`
- Left interface zone
  - `Interface Utilization Top 10`: `x=0 y=19 w=14 h=10`
  - `100GE5/0`: `x=0 y=29 w=14 h=2`
  - `100GE6/0`: `x=0 y=31 w=14 h=2`
  - `40GE7/0`: `x=0 y=33 w=14 h=2`
  - `10GE8/0`: `x=0 y=35 w=14 h=2`
  - `Traffic Throughput`: `x=0 y=37 w=14 h=8`
  - `MAC Entries`: `x=0 y=47 w=4 h=4`
  - `ARP Entries`: `x=4 y=47 w=4 h=4`
  - `VLANs`: `x=8 y=47 w=4 h=4`
  - `STP Ports`: `x=0 y=51 w=4 h=4`
  - `STP FWD`: `x=4 y=51 w=4 h=4`
  - `STP BLK`: `x=8 y=51 w=4 h=4`
- Right resource and hardware zone
  - `CPU / Memory Trend`: `x=14 y=19 w=10 h=8`
  - `Temperature Sensors`: `x=14 y=27 w=10 h=8`
  - `Fans`: `x=14 y=35 w=5 h=6`
  - `Power Supplies`: `x=19 y=35 w=5 h=6`
  - `Top 4 by Rx Power`: `x=14 y=41 w=5 h=6`
  - `Last 4 by Rx Power`: `x=19 y=41 w=5 h=6`
  - `Packets Per Second`: `x=14 y=47 w=10 h=6`

Template and seed updates should follow this baseline rather than reinterpreting the layout from screenshots.

### Interface Operations Zone

The left side should be the dominant visual area because CE168 troubleshooting is interface-heavy.

### Hardware Health Zone

- Replace the old aggregate `Temperature Now`, `Fan Status`, and `Power Supply` stat cards with component-oriented current-state views.
- `Temperature Sensors` should show only high-value chassis entities such as MPU, SFU, line-card, and power-module temperatures.
- Exclude optical transceiver temperature noise from the main chassis temperature view.
- `Fans` should render the live per-component status list from the current fan-status series.
- `Power Supplies` should render the live per-component status list from the current power-status series.
- When friendly component names are unavailable, use stable index-backed labels instead of invented names.
- `Transceiver Status` and `Module Status` should remain hidden for CE168 when no live data is available.

### Port State

- Replace the generic time-series `Port State Map` with current-state tiles.
- Render one tile per physical interface and exclude logical interfaces such as `Vlanif`, `Eth-Trunk`, `LoopBack`, `InLoopBack`, `NULL`, `MEth`, `Sip`, `Tunnel`, and `Nve`.
- Group tiles by board or slot so one board occupies one row.
- Cap each board row at 48 interfaces and preserve numeric interface ordering.
- Keep panel text hidden and show interface identity through tooltip or hover.
- Distinguish at least these states:
  - `Admin Down`
  - `Admin UP / Oper Down`
  - `Admin UP / Oper UP`

### Interface Utilization Top 10

- Keep `Interface Utilization Top 10` as a horizontal ranked bar gauge.
- Keep only the top 10 physical interfaces ranked by current utilization.
- The panel should remain a fast-glance hotspot view rather than a dense operations table.
- Use the bar length and threshold color to express urgency first, and keep interface identity readable through the left-hand label.
- Tooltip or hover may still expose:
  - `ifAlias`
  - short recent trend such as `5m`
  - additional rate context when available

### Interface Quality Hotspots

- Do not keep `Interface Quality Hotspots` as a large standalone lower-half panel.
- Fold current quality signals into the interface operations table through the `In Errors` and `Out Errors` columns, plus the `Status` column where appropriate.
- If a dedicated exception list is still needed, render it as a small secondary list inside the right-side resource and hardware zone rather than consuming a full-width primary panel.
- Any dedicated quality list should still use:
  - physical interfaces only
  - `admin up`
  - current `error` or `discard` rate greater than zero

### Traffic Section

- Keep `Traffic` in the left-side interface operations zone below the utilization table and port map.
- Present traffic as three compact adjacent views:
  - `Throughput`
  - `Packets Per Second`
  - `Traffic Mix`
- These should support interface troubleshooting context rather than act as primary ranking panels.

### Resource and Hardware Zone

The right side should summarize device-level behavior without competing with the interface-heavy left side.

- `Resource Performance` should be a `2 x 2` matrix of compact trends:
  - `CPU`
  - `Memory`
  - `Temperature`
  - `Buffer` or another traffic-pressure proxy if available
- `Hardware Health` should be a compact card or summary area covering:
  - power
  - fans
  - modules
  - sensors
- `Routing & Layer 2` should remain a summary list, not a large table.
- `Module CPU Hotspots` should not remain as a large sparse table. Replace it with a compact `Module / Transceiver Summary` style panel in the right-side zone.

### Layer 2 And Routing Summary Readiness

The summary panel in this zone must follow actual data availability rather than the reference layout.

- Phase 1 should use a `Layer 2 Summary` or `Switching Summary` label, not `Routing & Layer 2`.
- Phase 1 data should come from currently available switch-state sources:
  - MAC entry count
  - ARP entry count
  - VLAN count
  - STP port count
  - STP forwarding port count
  - STP blocking port count
- Existing raw evidence tables for `MAC`, `ARP`, `VLAN`, and `STP` should remain available as secondary detail panels below the summary.
- `L2 Neighbors` should not be promoted into the summary until Huawei LLDP collection is re-enabled and validated for CE168.
- `BGP`, `OSPF`, `IPv4 Routes`, and `IPv6 Routes` should not appear in the summary until their SNMP data pipeline exists end-to-end.
- Phase 2 may rename the panel to `Routing & Layer 2` only after routing-protocol and route-count metrics are genuinely available.

### Routing Capability Model

Routing data should be modeled as a generic switch-routing contract with platform-specific providers.

- The contract layer should define stable summary capabilities:
  - `bgp_neighbor_total`
  - `bgp_established_total`
  - `ospf_neighbor_total`
  - `ospf_full_total`
  - `ipv4_route_count`
  - `ipv6_route_count`
- The first provider implementation should target Huawei CE168 / VRP rather than trying to make the collection path fully vendor-neutral on day one.
- This keeps the dashboard and contract semantics stable while acknowledging that routing SNMP exposure is strongly platform- and view-dependent.

### Huawei CE168 Routing Evidence

Current CE168 routing evidence is asymmetric and should drive the delivery order.

- Standard `IP-FORWARD-MIB` is partially usable on this device:
  - `ipCidrRouteNumber (.1.3.6.1.2.1.4.24.3.0)` returned a scalar value in the historical CE168 exploration and again in the live 2026-06-13 validation.
  - `ipCidrRouteTable`, `inetCidrRouteTable`, and `ipRouteTable` all exist in local MIB metadata and are valid standard candidates.
- Standard `IPV6-MIB` route count is also exposed on this device:
  - `ipv6RouteNumber (.1.3.6.1.2.1.55.1.9.0)` returned a live scalar value of `3` on `2026-06-13`.
- Live route-table protocol evidence on `2026-06-13` also points away from active dynamic-routing exposure:
  - `ipCidrRouteProto` entries on the CE168 only returned `local(2)` and `netmgmt(3)`.
  - no `ospf(13)` or `bgp(14)` IPv4 route entries were observed in the live `ipCidrRouteTable`.
  - `ipv6RouteProtocol` entries observed in the live `ipv6RouteTable` returned `local(2)`.
- Standard `BGP4-MIB` is not exposed by the current CE168 SNMP view:
  - raw walk `.1.3.6.1.2.1.15` returned `No Such Object`.
- Standard `OSPF-MIB` is not exposed by the current CE168 SNMP view:
  - raw walk `.1.3.6.1.2.1.14` returned `No Such Object`.
- Huawei VRP private `BGP / OSPF` candidates are also not currently exposed on this CE168:
  - `hwBgpPeerSessionNum (.1.3.6.1.4.1.2011.5.25.177.1.4.1.0)` returned `No Such Instance` on `2026-06-13`.
  - `hwBgpPeerTable (.1.3.6.1.4.1.2011.5.25.177.1.1.2)` walk returned `No Such Object` on `2026-06-13`.
  - `hwospfv2ProcessFullPeerNumber (.1.3.6.1.4.1.2011.5.25.155.33.1.1.2.0)` returned `No Such Object` on `2026-06-13`.
  - `hwospfv2` process/interface subtrees `.1.3.6.1.4.1.2011.5.25.155.33.1` and `.33.2` both returned `No Such Object` on `2026-06-13`.
- The current evidence therefore suggests that routing-protocol visibility is blocked not only for standard MIBs but also for the first Huawei-private candidates. The remaining likely causes are:
  - the device is not currently carrying active BGP / OSPF routes
  - the CE168 SNMP view does not include those branches
  - the device software build does not expose those objects
  - the routing features are not enabled in a way that instantiates those objects
- Standard `LLDP-MIB` is also blocked in the current SNMP view, which reinforces that routing-protocol visibility must not be assumed from MIB availability alone.
- Local `mib_tree.json` contains standard routing symbols and many vendor-private `ospf` / `route` names, but their presence in metadata is not proof that the CE168 runtime view exposes them.

### Routing Delivery Phases

The routing work should ship in phases ordered by operational certainty.

- Phase 2A: `IPv4 Routes`
  - Build `ipv4_route_count` first from standard `IP-FORWARD-MIB`.
  - Prefer a scalar count such as `ipCidrRouteNumber` when available.
  - Fall back to table-counting only if the scalar is absent or unreliable.
- Phase 2B: `IPv6 Routes`
  - Use `ipv6RouteNumber` because the live CE168 has already proven the scalar exists.
  - Keep table-based IPv6 route detail as a later concern; the first routing summary only needs the scalar count.
- Phase 2C: `BGP / OSPF`
  - Treat `BGP` and `OSPF` as exploration-first items.
  - Try standard tables first only as a baseline check.
  - Then identify Huawei VRP private MIB branches or SNMP-view requirements that can provide neighbor counts and healthy-state counts.
  - If neither SNMP view changes nor private MIB exposure is available, the contract should remain defined but unimplemented for this provider.
  - The next evidence step after the `2026-06-13` private-MIB probe should be operational, not dashboard-side:
    - confirm whether `BGP / OSPF` are actually configured on the CE168
    - inspect or widen the SNMP view on the device
    - only then retry Huawei-private `BGP / OSPF` probes

### Routing Summary Rendering Rule

When the routing data pipeline becomes available, the summary panel should still stay compact and count-oriented.

- `IPv4 Routes` and `IPv6 Routes` should render as counts, not route-detail tables, in the primary summary panel.
- `BGP` should render as `established / total`.
- `OSPF` should render as `full / total`.
- If only some routing capabilities are implemented for a provider, the summary should render only the proven metrics and should not show placeholder rows for unavailable ones.

### Alerts and Events Zone

- Reserve the bottom full-width row for:
  - `Active Alerts`
  - `Recent Events`
  - `Configuration & Compliance`
- These panels should sit below the main operational triage area so they enrich investigation without displacing core device state.

### Rendering Rules

- Interface-heavy panels should prefer compact current-state operational views over long time axes on high-density chassis devices.
- All interface hotspot panels should use the physical-interface filter to avoid logical-interface noise.
- Tooltip detail is preferred over on-panel labels when the panel needs to remain dense and scannable.
- Current-value triage panels should be designed for fast identification first and historical explanation second.
- Large empty `No data` panels should be removed from the primary lower layout. Empty states are acceptable only in compact secondary cards or lists.
- The lower-half composition should favor semantic grouping over symmetrical card counts.

## Acceptance Criteria

- CE168 dashboard no longer renders hundreds of CPU series.
- Device CPU and memory stat panels use MPU/control-plane semantics.
- LPU and SFU utilization remains visible in a dedicated module hotspot panel.
- Runtime queries for `172.21.165.11` can identify MPU/LPU/SFU by label or by generated target-scoped rules.
- Tests cover dashboard expression generation and the CE168 entity classification rules.
- The lower half uses a left-heavy interface operations zone, a right-side resource and hardware zone, and a bottom events zone.
- `Port State` uses current-state board-grouped tiles instead of dense status history.
- `Interface Utilization Top 10` renders as a horizontal ranked bar gauge.
- `Interface Quality Hotspots` no longer occupies a large standalone lower-half panel.
- Large sparse `No data` panels are removed from the primary lower layout.
