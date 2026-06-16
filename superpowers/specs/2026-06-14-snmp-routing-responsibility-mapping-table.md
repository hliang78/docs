# SNMP Routing Responsibility Mapping Table

Date: 2026-06-14

## Goal

Turn one abstract rule into a short mapping table:

```text
which strategy responsibility counts as routing responsibility
and
which does not
```

This note exists only to support baseline selection.

## Core Rule

Use this sentence:

```text
baseline follows responsibility
```

So the real question is:

```text
does the matched strategy side carry routing responsibility?
```

This table answers that question directly.

## Positive Mapping

These responsibilities count as routing responsibility.

| Family / responsibility | Counts as routing responsibility? | Why |
|---|---|---|
| `l3_route_table.ipv4_count` | `yes` | route-count responsibility is routing responsibility |
| `l3_route_table.ipv6_count` | `yes` | same as above |
| `routing_bgp.neighbor_total` | `yes` | BGP neighbor count is protocol-level routing responsibility |
| `routing_bgp.established_total` | `yes` | same as above |
| `routing_ospf.neighbor_total` | `yes` | OSPF neighbor count is protocol-level routing responsibility |
| `routing_ospf.full_total` | `yes` | same as above |

## Negative Mapping

These responsibilities do **not** count as routing responsibility for baseline selection.

| Family / responsibility | Counts as routing responsibility? | Why |
|---|---|---|
| `interface_basic.*` | `no` | interface responsibility is still switching/interface responsibility |
| `system_basic.*` | `no` | system resource responsibility is device/system responsibility, not routing |
| `device_metrics.*` | `no` | hardware health is not routing responsibility |
| `l2_neighbors.summary` | `no` | topology evidence is not routing responsibility by itself |
| `l2_mac_table.*` | `no` | MAC evidence is L2 switching responsibility |
| `l3_arp_table.*` | `no` | ARP evidence is still neighbor/address evidence, not enough to classify the target as routing-capable |
| `l2_vlan_table.*` | `no` | VLAN evidence is switching responsibility |
| `l2_stp_state.*` | `no` | STP evidence is switching responsibility |
| `platform_config.*` | `no` | platform evidence is root context, not routing |
| `platform_alerts.*` | `no` | platform evidence is root context, not routing |
| `platform_events.*` | `no` | platform evidence is root context, not routing |
| `routing_l2.summary` | `no` | current root rollup for L2 topology is still not routing responsibility |

## Selection Shortcut

Use this shortcut when selecting a switch baseline:

### Choose `routing-capable switch baseline`

Only if the matched strategy side includes at least one of:

- `l3_route_table.*`
- `routing_bgp.*`
- `routing_ospf.*`

### Keep `current switch baseline`

If the matched strategy side includes only:

- interface families
- system families
- hardware-detail families
- topology evidence families
- platform evidence families

## Important Non-Rule

Do not promote a target into the routing-capable baseline just because:

- one device has ARP data;
- one device has L2 neighbor data;
- one device currently has more topology evidence than others.

Those may be valuable families,
but they are not the routing trigger for baseline selection.

## Immediate Consequence

This note keeps the first routing trigger narrow.

That is good because it avoids:

- over-classifying ordinary switches as routing-capable;
- letting L2/L3 evidence blur into routing responsibility;
- reopening the current switch closure with weak class boundaries.
