# SNMP Family Closure Matrix

Date: 2026-06-14

## Goal

Stop advancing the definition-layer closure one tiny patch at a time.

This note turns the current dashboard family work into one batch-oriented matrix:

- what family is active now;
- what owner it should have;
- whether that family is already closed;
- what still remains open.

This is the new execution surface for the remaining `20%-30%`.

## Rule

Use only three states:

- `closed`
- `partial`
- `open`

Use only two owner classes:

- `root`
- `strategy`

If a family still needs a real owner decision, mark it `open`.
Do not hide uncertainty behind runtime fallback.

## Current Matrix

| Family | Owner | Status | Notes |
|---|---|---|---|
| `device.identity` | `root` | `closed` | explicit root summary / context block |
| `device.overall_health` | `root` | `closed` | now explicitly fixed as root summary |
| `device.active_alerts` | `root` | `closed` | now explicitly fixed as root summary |
| `routing_l2.summary` | `root` | `closed` | now treated as compact root rollup |
| `platform_config.*` | `root` | `closed` | explicit platform evidence |
| `platform_alerts.*` | `root` | `closed` | explicit platform evidence |
| `platform_events.*` | `root` | `closed` | explicit platform evidence |
| `interface_basic.utilization` | `strategy` | `closed` | explicit strategy owner path already stable |
| `interface_basic.port_state` | `strategy` | `closed` | explicit / capability fallback stable |
| `interface_basic.port_state.board.*` | `strategy` | `closed` | capability fallback now stable |
| `interface_basic.port_up_count` | `strategy` | `closed` | same interface family path |
| `interface_basic.port_down_count` | `strategy` | `closed` | same interface family path |
| `interface_basic.traffic_mix` | `strategy` | `closed` | same interface family path |
| `interface_basic.throughput` | `strategy` | `closed` | same interface family path |
| `interface_basic.packet_rate` | `strategy` | `closed` | same interface family path |
| `interface_basic.quality_hotspots` | `strategy` | `closed` | same interface family path |
| `interface_basic.broadcast` | `strategy` | `closed` | decision already fixed in owner baseline |
| `interface_basic.error_port_count` | `strategy` | `closed` | same interface family path |
| `interface_basic.discard_port_count` | `strategy` | `closed` | same interface family path |
| `system_basic.cpu.stat` | `strategy` | `closed` | explicit strategy owner already asserted |
| `system_basic.memory.stat` | `strategy` | `closed` | same system family path |
| `system_basic.cpu_memory.trend` | `strategy` | `closed` | capability fallback now stable |
| `device_metrics.temperature.stat` | `strategy` | `closed` | same hardware-detail path |
| `device_metrics.temperature.trend` | `strategy` | `closed` | same hardware-detail path |
| `device_metrics.temperature.sensors` | `strategy` | `closed` | now asserted as strategy-owned |
| `device_metrics.fan_status.stat` | `strategy` | `closed` | same hardware-detail path |
| `device_metrics.fan_status.components` | `strategy` | `closed` | now asserted as strategy-owned |
| `device_metrics.power_status.stat` | `strategy` | `closed` | same hardware-detail path |
| `device_metrics.power_status.components` | `strategy` | `closed` | now asserted as strategy-owned |
| `device_metrics.transceiver_status.stat` | `strategy` | `closed` | same hardware-detail path |
| `device_metrics.transceiver.rx_top4` | `strategy` | `closed` | now asserted as strategy-owned |
| `device_metrics.transceiver.rx_last4` | `strategy` | `closed` | now asserted as strategy-owned |
| `device_metrics.module_status.stat` | `strategy` | `closed` | same hardware-detail path |
| `l2_neighbors.summary` | `strategy` | `closed` | definition-layer note now freezes topology evidence as strategy-local |
| `l2_mac_table.summary` | `strategy` | `closed` | same topology evidence rule |
| `l2_mac_table.count` | `strategy` | `closed` | same topology evidence rule |
| `l3_arp_table.summary` | `strategy` | `closed` | same topology evidence rule |
| `l3_arp_table.count` | `strategy` | `closed` | same topology evidence rule |
| `l2_vlan_table.summary` | `strategy` | `closed` | same topology evidence rule |
| `l2_vlan_table.count` | `strategy` | `closed` | same topology evidence rule |
| `l2_stp_state.summary` | `strategy` | `closed` | same topology evidence rule |
| `l2_stp_state.port_count` | `strategy` | `closed` | same topology evidence rule |
| `l2_stp_state.forwarding_count` | `strategy` | `closed` | same topology evidence rule |
| `l2_stp_state.blocking_count` | `strategy` | `closed` | same topology evidence rule |
## What Is Already Good Enough

The core interface, system, hardware-detail, and root-summary families are no longer the main blocker.

That means the remaining closure risk is no longer spread everywhere.

For the current switch dashboard-tree denominator, the active family set is now fully covered by an explicit owner baseline.

## Future Scope, Not Current Denominator

The following families remain visible in capability requirements or panel contracts,
but they are not counted inside the current definition-layer closure denominator:

- `l3_route_table.*`
- `routing_bgp.*`
- `routing_ospf.*`

Reason:

- they are not part of the current switch class baseline;
- they belong to a possible future routing-capable class or variant baseline, not the current switch baseline;
- forcing them into the current denominator would mix a future class-definition problem into the already-active switch dashboard-tree closure.

They stay future-scope until both are true:

- a routing-capable class or variant baseline is intentionally defined;
- routing families are explicitly included in that baseline design.

## Batch Plan

Keep doing the remainder in batches, not one patch at a time.

### Current Closure Result

Target result reached:

- no active family remains in `open`;
- current switch dashboard-tree closure no longer depends on future routing scope.

### Next Batch, Separate Track

When routing families become active, treat them as a new batch:

- `l3_route_table.*`
- `routing_bgp.*`
- `routing_ospf.*`

That routing batch should not re-open the current closure denominator.

## Execution Rule

From this point on, do not measure progress by:

- one patch
- one helper
- one warning

Measure progress by:

- how many family rows moved from `partial/open` to `closed`.

## Current Fastest Path

The fastest path now is:

1. treat the current switch family denominator as closed;
2. keep routing families on a separate future-scope track;
3. only re-open family closure when a routing-capable class or variant baseline is intentionally defined.

That is the shortest route from the current `80%+` to a real current-scope definition-layer closure.
