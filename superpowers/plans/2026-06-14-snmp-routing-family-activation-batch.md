# SNMP Routing Family Activation Batch

Date: 2026-06-14

## Goal

Open the next closure batch without re-opening the current switch dashboard-tree closure.

This batch is only about when routing families should be intentionally included in a routing-capable class or variant baseline.

The class-level definition for that baseline now lives in:

- `/OneOPS/docs/superpowers/specs/2026-06-14-snmp-routing-capable-switch-baseline.md`

It does **not**:

- change the current closed switch family baseline;
- add speculative routing owners right now;
- use runtime data presence as a gate for baseline family existence.

## Families

Current future-scope routing families are:

- `l3_route_table.*`
- `routing_bgp.*`
- `routing_ospf.*`

## Rule

These families enter a class-level baseline only when both are true:

1. a routing-capable target class or variant baseline is intentionally defined;
2. those routing families are explicitly included in that baseline design.

Until then, they stay future-scope.

## Why They Stay Separate Now

The current switch closure is already good enough for:

- `root` summary families
- `interface_basic.*`
- `system_basic.*`
- `device_metrics.*`
- topology evidence families

Routing is different because the current evidence is asymmetric:

- `IPv4 Routes` and `IPv6 Routes` have scalar evidence;
- `BGP` and `OSPF` still do not have strong live/runtime evidence on the current CE168 path.

If we force routing into the current denominator now, we mix:

- active switch dashboard-tree closure
with
- future routing class-definition work

That would slow closure again.

## Design Rule

Use one hard split:

- generation decides what families exist in the baseline;
- runtime decides what state those panels currently show.

That means:

- route-count or protocol panels may exist in a baseline even when a given target currently has no data;
- lack of runtime data is not a reason to remove a family from the baseline;
- runtime only affects states such as `has_data`, `no_data`, or `not_exposed`.

## Batch Order

Do this batch in three steps.

### Step 1. Route Counts

Prioritize:

- `l3_route_table.ipv4_count`
- `l3_route_table.ipv6_count`

Reason:

- they are the simplest routing families to include in a routing-capable class baseline;
- they do not require protocol-neighbor semantics.

Success means:

- a routing-capable class or variant baseline explicitly includes route-count panels;
- route-count owner class is frozen;
- route-count family rows can move into the closure matrix.

### Step 2. Protocol Families

Evaluate separately:

- `routing_bgp.*`
- `routing_ospf.*`

Reason:

- both need a clearer routing-capable class story than route-count families do.

Success means:

- a routing-capable class or variant baseline explicitly includes them;
- owner rules are no longer speculative.

### Step 3. Re-enter The Closure Matrix

Only after Step 1 or Step 2 passes:

- add the family to the active denominator;
- assign owner class;
- add owner regression;
- update the family closure matrix.

## What Not To Do

Do not:

- re-open the current switch closure denominator;
- mark routing as `open` inside the current matrix again;
- assign `root` just because routing sounds device-wide;
- use absent runtime evidence as a reason to invent new baseline gating logic.

## Fastest Path

The fastest next move is:

1. treat `l3_route_table.*` as the first routing activation candidate;
2. keep `routing_bgp.*` and `routing_ospf.*` as the second routing design step;
3. decide routing inclusion at the class/variant level, not from target runtime results.

With the baseline note in place, the next real design question becomes:

- how OneOPS decides that a target uses `current switch baseline` versus `routing-capable switch baseline`.
