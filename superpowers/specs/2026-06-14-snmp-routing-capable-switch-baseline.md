# SNMP Routing-Capable Switch Baseline

Date: 2026-06-14

## Goal

Define the next class-level baseline after the current switch baseline:

```text
current switch baseline
  + routing families
  = routing-capable switch baseline
```

This note defines the baseline at generation time.
It does not use runtime data presence as a gate.

## Core Rule

Use the already-fixed split:

```text
generation decides what exists
runtime decides what state it shows
```

That means:

- this baseline is for one class of targets;
- one target may show `has_data`;
- another may show `no_data`;
- another may show `not_exposed`;
- all of them still use the same class baseline.

## Baseline Relationship

### 1. Current Switch Baseline

The current switch baseline already includes:

- root summary families
- interface families
- system families
- hardware-detail families
- topology evidence families

That baseline stays unchanged.

### 2. Routing-Capable Switch Baseline

The routing-capable switch baseline is an additive baseline.

It means:

- inherit the full current switch baseline;
- add routing families for targets whose class is intended to carry routing responsibility.

This is still one class baseline, not one device-specific dashboard.

## Added Families

The first routing-capable switch baseline should add only:

- `l3_route_table.ipv4_count`
- `l3_route_table.ipv6_count`
- `routing_bgp.neighbor_total`
- `routing_bgp.established_total`
- `routing_ospf.neighbor_total`
- `routing_ospf.full_total`

These families belong to the class baseline even when some concrete targets currently show:

- no data
- not exposed

## Owner Rule

Default owner class for routing families is:

- `strategy`

Reason:

- route and protocol counts describe one routing responsibility;
- they are not root navigation;
- they are not cross-strategy overview by default.

So the baseline should assume:

```text
routing family
  -> routing strategy node
  -> strategy dashboard
```

Not:

```text
routing family
  -> root dashboard
```

### Root Exception

Do not introduce root-owned routing panels in the first routing-capable baseline.

If a future product wants:

- cross-strategy route rollup
- root-level routing navigation
- multi-routing-domain total overview

that should be a later explicit root-summary design,
not part of this first baseline.

## Variant Rule

Keep the first routing-capable baseline simple.

### Operations Variant

The operations variant should include:

- `l3_route_table.ipv4_count`
- `l3_route_table.ipv6_count`
- `routing_bgp.neighbor_total`
- `routing_bgp.established_total`
- `routing_ospf.neighbor_total`
- `routing_ospf.full_total`

Purpose:

- give one compact routing responsibility view;
- stay count-oriented;
- avoid introducing detail tables in the first step.

### Capacity Variant

Do not define routing-specific capacity panels yet.

The first routing-capable baseline should reuse the current capacity structure unchanged.

If routing trends or route-growth panels are needed later,
they should be added as a second-step variant change, not bundled into the first baseline definition.

## What This Baseline Does Not Do

It does not:

- create per-device dashboards;
- require every target to have route/protocol data;
- require BGP/OSPF to be exposed on every target;
- change the current non-routing switch baseline;
- decide runtime empty-state wording.

## Class Boundary

Use this baseline only for targets whose intended class includes routing responsibility.

In plain terms:

- plain switch baseline = switching-first targets
- routing-capable switch baseline = switching targets that also carry routing responsibility

This boundary is class design, not runtime observation.

## Immediate Consequence

Routing no longer needs to be discussed as:

- “did one target collect it?”

It should now be discussed as:

- “does this target class use the current switch baseline or the routing-capable switch baseline?”

That is the correct generation-time decision.

The first selection rule for that decision now lives in:

- [2026-06-14-snmp-switch-baseline-selection-rule.md](/OneOPS/docs/superpowers/specs/2026-06-14-snmp-switch-baseline-selection-rule.md)
