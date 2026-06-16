# SNMP Strategy Node To Dashboard Node To Panel Ownership Mapping Note

Date: 2026-06-14

## Goal

This note defines one narrow definition-layer mapping:

```text
Strategy node
  -> Dashboard logical node
    -> Panel slot ownership
```

The purpose is to stop runtime materialization from being the place where business ownership is invented.

This note does not define:

- concrete storage schema
- concrete API fields
- final Grafana JSON rendering
- runtime save behavior

It defines only the ownership mapping that should already be true before runtime begins.

## Core Mapping

The minimum business mapping is:

```text
StrategySet
  -> Root Dashboard Logical Node

Strategy node
  -> Strategy Dashboard Logical Node

Dashboard Logical Node
  -> owned panel slots
```

This means:

- the strategy set owns one root dashboard logical node;
- each relevant strategy node owns one strategy dashboard logical node;
- each logical dashboard node owns a stable set of panel slots;
- runtime materialization should instantiate these nodes, not invent them from scratch.

## 1. Strategy Node To Dashboard Logical Node

### Rule 1.1 Root Is Not A Strategy Node

The root dashboard logical node is owned by the `StrategySet`, not by a synthetic strategy node.

Reason:

- it represents set-wide entry, overview, and navigation;
- it is not the semantic responsibility of one child strategy.

### Rule 1.2 Each Business Strategy Node Maps To One Strategy Dashboard Logical Node

For every strategy node that should be visible at dashboard level, there should be one corresponding strategy dashboard logical node.

Canonical mapping:

```text
strategy_id
  -> dashboard logical node owned by strategy_id
```

This is a logical ownership mapping.
It does not yet require one storage row per node, but it does require one business node per owner.

### Rule 1.3 Parent/Child Strategy Relationships Map To Parent/Child Dashboard Logical Relationships

If:

```text
Strategy A -> child Strategy B
```

then:

```text
DashboardNode(A) -> child DashboardNode(B)
```

unless a deliberate visibility rule says that one node is hidden from dashboard navigation.

Hidden-from-navigation is allowed later.
Implicit flattening is not.

## 2. Dashboard Logical Node Types

There are only two node types in the minimum model.

### 2.1 Root Dashboard Logical Node

Owner:

- `strategy_set_id`

Purpose:

- entry navigation
- strategy-node links
- cross-strategy summary
- top-level overview

### 2.2 Strategy Dashboard Logical Node

Owner:

- `strategy_id`

Purpose:

- represent one strategy responsibility
- carry the panels owned by that strategy
- preserve business hierarchy from the strategy tree

## 3. Panel Slot Ownership

### Rule 3.1 Panel Slots Belong To Logical Dashboard Nodes, Not Directly To Runtime Targets

Panel ownership should be decided at definition layer first.

Canonical shape:

```text
dashboard logical node
  -> panel slot
```

not:

```text
target-scoped materialization result
  -> infer where panel belongs
```

### Rule 3.2 Strategy Panels Belong To Strategy Dashboard Nodes

If a panel expresses one strategy node’s semantic responsibility, then the panel slot owner must be that `strategy_id`.

Examples:

- interface traffic owned by interface-monitoring strategy
- CPU panel owned by system-resource strategy
- sensor state panel owned by sensor-monitoring strategy
- topology evidence tables such as `l2_neighbors.summary` or `l2_mac_table.summary`
  remain strategy-owned when they expose one strategy node’s evidence scope

### Rule 3.3 Root Panels Belong To Strategy Set Only When They Are Truly Cross-Strategy

A root-owned panel slot is allowed only when the panel is one of:

- global overview
- set-wide summary
- navigation / entry panel
- cross-strategy aggregation

Root must not become the fallback owner for panels whose real semantic owner is a child strategy node.

### Rule 3.4 A Panel Slot Has Exactly One Primary Logical Owner

A panel slot may consume data influenced by inheritance or shared capabilities,
but its business owner must still be singular.

That means:

- one panel slot should not be simultaneously owned by both `strategy_set_id` and `strategy_id`;
- one panel slot should not be simultaneously owned by parent and child strategy nodes.

Aggregation inputs may be plural.
Logical owner must remain singular.

## 4. Ownership Resolution Order

Definition-layer ownership should be resolved in this order:

1. explicit root summary intent
2. explicit strategy-node semantic intent
3. inherited strategy ownership
4. transitional fallback heuristics

Interpretation:

- if a panel is explicitly root-level overview, root owns it;
- else if a panel clearly corresponds to one strategy node, that strategy owns it;
- else if ownership is inherited from parent strategy semantics, preserve the inherited strategy owner;
- only transitional pilot code may still use heuristics.

Important rule:

- heuristic fallback is implementation debt, not the definition model.

## 5. What Root May Own

The root dashboard logical node may own:

- fleet or device overview panel
- total health summary
- cross-strategy status rollup
- navigation links into child strategy dashboards
- top-level metadata/context blocks

The root dashboard logical node should not own:

- every detailed panel from all child strategies
- child-specific troubleshooting tables
- panels whose semantics clearly belong to one strategy node

## 6. What Strategy Dashboard Nodes May Own

A strategy dashboard logical node may own:

- panels derived from that strategy node’s metric groups
- panels derived from that strategy node’s capability set
- panels derived from inherited semantic responsibility that still belongs to that node
- local summary panels for that strategy responsibility

It should not own:

- set-wide navigation panels
- unrelated sibling strategy panels
- generic fallback panels that exist only because ownership was not modeled

## 7. Transitional Relationship To Current Pilot

Current pilot behavior is useful but not final.

The tree pilot today can be understood as a bridge:

```text
runtime tree pilot
  <- partially reconstructed from current strategy evidence
```

The target model should instead be:

```text
definition-layer ownership
  -> runtime tree materialization
```

So the pilot should be evaluated by one question:

- does it preserve the ownership that the definition layer already says should exist?

not:

- can it guess a plausible ownership late enough in the runtime path?

## 8. Immediate Consequence For Next Design Work

The next definition-layer question should be:

```text
for each current panel family,
which owner class is correct:
root strategy_set
or one specific strategy_id?
```

That question should be answered before adding more runtime ownership heuristics.

## 9. Minimum Checklist For Future Implementation

A future implementation should be rejected as incomplete if it cannot answer:

1. what root dashboard logical node exists for this strategy set?
2. what strategy dashboard logical node exists for this strategy node?
3. who owns this panel slot before target materialization?
4. why is this panel root-owned instead of strategy-owned?
5. what parent/child dashboard logical relationship exists before runtime save?

If those answers only exist after by-target materialization, the ownership model is still too late.
