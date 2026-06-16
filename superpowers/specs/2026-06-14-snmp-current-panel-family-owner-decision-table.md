# SNMP Current Panel Family Owner Decision Table

Date: 2026-06-14

## Goal

This note turns the definition-layer ownership rules into one practical decision table for the current known SNMP panel families.

It is intentionally narrow:

- only current known panel families are covered;
- it assigns the expected owner class;
- it explains why that owner is correct;
- it does not introduce new storage or runtime behavior.

This note should be used as the minimum ownership baseline for future dashboard-tree and panel-planning work.

## Scope

Current known panel families come from the existing dashboard-family design and current by-target preview/materialization work.

At minimum, the visible current panel families are:

- `interface_basic.traffic`
- `interface_basic.status`
- `interface_basic.speed`
- `interface_basic.quality`
- `interface_basic.broadcast`
- `system_basic.cpu`
- `system_basic.memory`

In addition, one already-observed special class exists:

- platform/config/evidence style panels

Those are currently visible in validation logic and pilot code even if they are not yet a fully normalized panel family set.

## Owner Classes

Only two owner classes are allowed in this decision table.

### 1. Root Owner

Owner key:

- `strategy_set_id`

Meaning:

- cross-strategy overview
- entry navigation
- set-wide summary
- platform/evidence metadata block

### 2. Strategy Owner

Owner key:

- `strategy_id`

Meaning:

- one strategy node’s semantic monitoring responsibility
- one strategy dashboard logical node
- detailed or local summary panels for that strategy responsibility

## Decision Table

| Panel family / class | Expected owner class | Why |
|---|---|---|
| `interface_basic.traffic` | `strategy_id` | interface traffic is a concrete interface-monitoring responsibility, not a set-wide overview |
| `interface_basic.status` | `strategy_id` | interface state belongs to the same interface strategy responsibility |
| `interface_basic.speed` | `strategy_id` | interface speed is part of interface-level semantic ownership |
| `interface_basic.quality` | `strategy_id` | error/discard quality is detailed interface responsibility, not root navigation |
| `interface_basic.broadcast` | `strategy_id` | interface broadcast ratio is still interface strategy detail |
| `system_basic.cpu` | `strategy_id` | CPU is one system-resource responsibility and should stay attached to that strategy node |
| `system_basic.memory` | `strategy_id` | memory is the sibling system-resource responsibility and should not be lifted to root by default |
| topology evidence table family (`l2_neighbors.summary`, `l2_mac_table.*`, `l3_arp_table.*`, `l2_vlan_table.*`, `l2_stp_state.*`) | `strategy_id` | these tables remain strategy-local evidence blocks in the current model; they expose one strategy node’s topology evidence rather than root navigation |
| platform/config/evidence panel | `strategy_set_id` by default | these panels act as root-level metadata/evidence/entry context unless a future note proves they belong to one specific strategy node |
| root navigation / child dashboard links | `strategy_set_id` | navigation is the job of the root dashboard logical node |
| cross-strategy total-health summary | `strategy_set_id` | this is a set-wide aggregation rather than one node’s semantic detail |

## Interpretation

The table above leads to one strong default:

```text
current detailed monitoring panels
  -> strategy-owned

current overview / evidence / navigation panels
  -> root-owned
```

That is the opposite of the old flat tendency where root becomes the easy fallback owner.

## Anti-Rules

The following ownership choices should be treated as wrong unless explicitly justified.

### 1. Interface Panels Defaulting To Root

These should not be root-owned only because:

- they are easy to aggregate;
- they appear in the first materialized dashboard;
- the runtime path has insufficient strategy evidence.

Lack of runtime certainty is not a definition-layer reason to move interface panels to root.

### 2. System Panels Automatically Moving To Root

`system_basic.cpu` and `system_basic.memory` should not be treated as root panels merely because they are device-level rather than interface-level.

Device-level does not mean set-level.

### 3. Root Becoming The “Unknown Owner” Bucket

If ownership is unknown, the answer should be:

- ownership is unresolved

not:

- put it under root for now

Root fallback is a temporary implementation heuristic, not a valid business decision.

## Current Default Mapping By Node Type

### Root Dashboard Logical Node Should Usually Own

- navigation panels
- child strategy entry links
- set-wide health summary
- cross-strategy overview
- platform/config/evidence context blocks

### Strategy Dashboard Logical Node Should Usually Own

- interface panel families
- system resource panel families
- sensor/module/port families when they are strategy-local
- topology evidence table families when they expose one strategy node’s evidence scope
- local summaries for one strategy responsibility

## Immediate Consequence For Tree Pilot Evaluation

Current tree pilot ownership should now be judged against this table.

The key question is not:

- did the pilot find any plausible owner?

The key question is:

- did the pilot keep `interface_basic.*` and `system_basic.*` on strategy-owned nodes,
  while limiting root ownership to summary/evidence/navigation roles?

## Open Items Still Not Decided Here

This decision table does not yet settle:

- whether `system_basic.cpu` and `system_basic.memory` belong to the same strategy node or two sibling strategy nodes in every product variant;
- whether some future cross-strategy aggregate panel should duplicate selected values at root while preserving strategy ownership in child dashboards;
- how future panel families such as sensor or environment should be classified.

Current routing families are intentionally excluded from the current closure denominator:

- `l3_route_table.*`
- `routing_bgp.*`
- `routing_ospf.*`

They should be re-opened only when a routing-capable class baseline or variant baseline is intentionally defined.

All future-scope families should be added only when they become active panel families in the current model.
