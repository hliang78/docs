# 2026-06-14 SNMP Suite To Strategy Dashboard Tree Design

## 1. Goal

This spec defines the target product model for SNMP dashboards when:

- one monitoring suite is the user-facing entry point;
- one matched strategy tree is the semantic monitoring tree;
- one Grafana dashboard tree should mirror that semantic tree.

The immediate goal is to stop treating the shared class dashboard as the final business object.

The intended model is:

```text
Monitoring Suite
  -> Root Dashboard
    -> Strategy Dashboard
      -> child Strategy Dashboard
```

and:

```text
target
  -> binds to one dashboard tree
```

not:

```text
target
  -> gets one flat dashboard copy
```

An additional hard rule also applies:

```text
dashboard selection
= projection of strategy selection
```

The dashboard layer must not introduce an independent semantic selection path that can diverge from the matched strategy tree.

## 2. Problem Statement

The current implementation already has useful class-level baseline logic:

- `snmp.generic`
- `switch.current`
- `switch.routing_capable`

It also has shared dashboard persistence for those baselines.

That work solved two real problems:

- runtime data no longer decides whether a panel family exists;
- multiple targets no longer need separate per-target dashboard rows for the same class-level dashboard.

But it still leaves a business-model gap.

Today the visible product center of gravity is still too close to:

```text
target class
  -> one shared flat dashboard
```

The intended business model is richer:

```text
monitoring suite
  -> one root dashboard
    -> one strategy dashboard per matched strategy node
      -> child strategy dashboards
```

This distinction matters because:

- a suite root is not the same as a strategy dashboard;
- a strategy dashboard is not the same as a target binding;
- a high-quality device sample dashboard is not the same as a class baseline;
- a shared class dashboard should not replace the strategy tree.

## 3. Scope

This spec defines:

- the canonical relationship between monitoring suite, strategy tree, and dashboard tree;
- the requirement that dashboard selection reuse the same semantic selection mechanism as strategy selection;
- the requirement that every dashboard node carry explicit metric-display responsibility;
- what a root dashboard is;
- what a strategy dashboard is;
- how target binding should work after the dashboard tree exists;
- how existing shared class dashboards should be reinterpreted.

This spec does not define:

- final DB migration statements;
- every API field;
- final UI presentation details for tree navigation;
- complete layout rules for each strategy dashboard.

## 4. Canonical Mapping

### 4.1 Monitoring Suite

The monitoring suite is the user-facing business entry.

Its purpose is:

- define what monitoring bundle the user applies;
- define the suite-level dashboard root;
- provide the top-level user navigation object.

For the current switch line:

```text
网络监控套件
  -> OneOPS SNMP Switch Ops
```

Important rule:

- one suite maps to one root dashboard identity;
- suite identity must not be replaced by target identity.

### 4.2 Strategy Tree

The strategy tree is the semantic responsibility tree.

Canonical structure:

```text
StrategySet
  -> matched Strategy
    -> child Strategy
      -> child Strategy
```

Its purpose is to answer:

- what monitoring responsibilities are active;
- how those responsibilities decompose;
- what parent/child semantic relationships exist.

Important rule:

- strategy-node identity must remain visible through dashboard generation;
- strategy names or copies may differ, but semantic responsibility boundaries must remain explicit.

### 4.2.1 Shared Selection Mechanism

Dashboard selection must not be a second, separate business matching system.

The intended rule is:

```text
suite selection
  -> strategy selection
    -> dashboard tree selection
```

This means:

- the user selects a monitoring suite;
- the platform evaluates the suite's strategy-selection mechanism;
- the matched strategy tree becomes the input to dashboard-tree generation;
- dashboard nodes are selected because strategy nodes were selected.

Dashboard generation may still apply:

- class baseline reuse;
- layout profile reuse;
- variant reuse;

but those must be downstream consequences of strategy selection, not a second semantic selector.

Important rule:

- strategy selection and dashboard selection must share the same semantic source of truth.
- dashboard selection must be derived, not independently re-decided.

### 4.3 Dashboard Tree

The dashboard tree is the business dashboard structure derived from:

- one monitoring suite root;
- one matched strategy tree.

Canonical structure:

```text
Monitoring Suite
  -> Root Dashboard
    -> Strategy Dashboard
      -> child Strategy Dashboard
```

Important rule:

- root dashboard ownership comes from the suite / strategy set boundary;
- strategy dashboard ownership comes from the matched strategy node boundary.

### 4.3.1 Explicit Metric Responsibility

Every dashboard node must have explicit metric-display responsibility.

This means a dashboard node must answer:

- what metric groups it exists to show;
- what panel families it owns;
- what summary vs detail responsibility it carries;
- what it must render even when runtime data is currently absent.

Important rule:

- a dashboard node is not just a visual container;
- it is a semantic metric-display unit.

### 4.4 Target Binding

Target binding is runtime association, not business dashboard definition.

Canonical structure:

```text
target
  -> binds to root dashboard tree
  -> reads current runtime state through variables / queries
```

Important rule:

- a target must not become the primary identity of the logical dashboard;
- target-specific runtime state may change panel state, but must not redefine the dashboard tree.

## 5. Core Logic To Freeze

The core logic should be frozen as these four rules.

### Rule 5.1 Suite Determines Root Dashboard

```text
Monitoring Suite
  -> Root Dashboard
```

Example:

```text
网络监控套件
  -> OneOPS SNMP Switch Ops
```

### Rule 5.2 Matched Strategy Determines Strategy Dashboard Node

```text
matched Strategy
  -> Strategy Dashboard Node
```

Example:

```text
Huawei通用SNMP网络监控策略
  -> one strategy dashboard node

SNMP网络监控策略 (副本)
  -> another strategy dashboard node
```

This is not an analogy.
It is the actual selection rule:

```text
matched Strategy node
  -> matched Strategy Dashboard node
```

and:

```text
matched Strategy responsibility
  -> Strategy Dashboard metric scope
```

### Rule 5.3 Strategy Parent/Child Determines Dashboard Parent/Child

```text
parent Strategy
  -> parent Strategy Dashboard

child Strategy
  -> child Strategy Dashboard
```

The dashboard tree must mirror semantic hierarchy, not just panel grouping.

### Rule 5.4 Target Only Binds To A Dashboard Tree

```text
target
  -> binds to one existing dashboard tree
```

The target does not create:

- a new logical root dashboard;
- a new logical strategy dashboard;
- a new business hierarchy.

### Rule 5.5 Each Dashboard Node Has Explicit Display Scope

Every dashboard node must own a concrete display scope.

Examples:

- root dashboard:
  - suite summary
  - cross-strategy overview
  - navigation into child strategy dashboards
- interface strategy dashboard:
  - interface utilization
  - throughput
  - port state
- system strategy dashboard:
  - CPU
  - memory
  - health trend
- hardware strategy dashboard:
  - temperature
  - fan
  - power
  - optical transceiver summaries

This rule prevents:

- empty dashboard nodes with no semantic content;
- visually convenient but semantically mixed dashboards;
- panel ownership that only exists after layout assembly.

## 6. Worked Example

Assume:

- device A selects `网络监控套件`;
- device B selects `网络监控套件`;
- device A finally matches `Huawei通用SNMP网络监控策略`;
- device B finally matches `SNMP网络监控策略 (副本)`.

Then the correct dashboard model is:

```text
网络监控套件
  -> OneOPS SNMP Switch Ops
    -> Huawei通用SNMP网络监控策略 Dashboard
    -> SNMP网络监控策略 (副本) Dashboard
```

This means:

- device A and B share the same suite root;
- device A and B do not need separate per-device root dashboards;
- device A and B may bind to different strategy dashboard nodes under the same root;
- the business distinction is strategy-node based, not device-name based.

### 6.1 What Must Not Happen

The following are incorrect:

```text
device A
  -> one full flat dashboard

device B
  -> another full flat dashboard
```

and also:

```text
OneOPS SNMP Switch Ops
  -> one flat shared dashboard
  -> strategy differences survive only as metadata
```

The correct shape is a dashboard tree with explicit strategy nodes.

### 6.2 Dashboard Selection Must Follow The Same Selector Result

For device A and device B:

- both may select the same monitoring suite;
- both may still end up with different dashboard nodes if the final matched strategy nodes differ.

That difference must come from:

- the strategy selector result;

not from:

- an independent dashboard selector;
- target-name heuristics;
- runtime data presence;
- separate dashboard-only matching rules.

So the correct model is:

```text
device
  -> suite chosen
  -> strategy tree matched
  -> dashboard tree projected
```

not:

```text
device
  -> suite chosen
  -> strategy matched
  -> dashboard matched again by another mechanism
```

## 7. Relationship To Current Class Baselines

The existing class baselines remain useful, but their role changes.

### 7.1 What Class Baselines Still Mean

`snmp.generic`, `switch.current`, and `switch.routing_capable` should remain:

- generation baselines;
- profile / family selectors;
- layout and panel-family floors.

They are still appropriate for:

- deciding what family set is available;
- deciding what variant is used;
- deciding what class-level reusable layout pieces exist.

### 7.2 What Class Baselines Must Not Replace

They must not replace:

- suite root identity;
- strategy dashboard identity;
- dashboard tree structure.

Class baselines answer:

- what kind of dashboard components are available.

They do not answer:

- what strategy dashboard node exists for this matched strategy;
- what the root/child dashboard hierarchy is.
- what concrete metric-display responsibility each dashboard node owns.

## 8. Relationship To CE168 Reference Dashboard

The CE168 dashboard is a strong reference sample, but it must not be treated as the canonical switch root model.

It may serve as:

- a panel-family discovery source;
- a profile overlay example;
- a layout-quality reference.

It must not serve as:

- the root dashboard identity;
- the strategy dashboard tree;
- the universal switch baseline truth.

Important rule:

- a device sample may improve shared layout quality;
- it must not define the business dashboard tree.

## 9. Current Gap Analysis

Relative to this target model, current implementation is still incomplete.

### 9.1 Already Close

- suite-level root naming now exists in practice;
- target no longer decides family existence;
- shared persistence already prevents one-target-one-copy explosion;
- tree pilot already exposes root/strategy node signals such as `owner_strategy_id`.

### 9.2 Still Missing

- strategy dashboards are not yet first-class visible product objects;
- main generation still centers too much on class-level shared dashboards;
- main persistence still centers too much on flat shared rows instead of full dashboard tree identities;
- dashboard list / query paths do not yet expose root + strategy dashboard tree as the primary business view.
- class-baseline selection still acts too much like a dashboard-side selector instead of a derived projection from the matched strategy tree.
- explicit metric-display responsibility per dashboard node is still under-modeled and too often inferred late from flat panel assembly.

## 10. Required Next-Step Implementation Direction

Implementation should move in this order:

1. define root dashboard identity explicitly from monitoring suite;
2. define strategy dashboard identity explicitly from matched strategy nodes;
3. define explicit metric-display responsibility for each dashboard node;
4. make dashboard selection a strict projection of the matched strategy tree;
5. promote dashboard tree generation to the primary path;
6. reinterpret class baselines as reusable generation floors, not the business root object;
7. make persistence tree-first instead of flat-dashboard-first;
8. keep target binding runtime-only.

## 11. Acceptance Criteria

This model is correctly implemented only when all of the following become true:

1. one monitoring suite resolves to one explicit root dashboard object;
2. one matched strategy resolves to one explicit strategy dashboard object;
3. parent/child strategies resolve to parent/child dashboard nodes;
4. every dashboard node has explicit owned metric-display scope;
5. device A and device B can share the same root while binding to different strategy dashboard nodes;
6. dashboard selection is fully derived from strategy selection instead of running an independent semantic matching path;
7. class baseline logic remains reusable but no longer substitutes for the business dashboard tree;
8. target identity does not define logical dashboard identity.

## 12. Short Summary

The correct SNMP dashboard model is:

```text
suite decides root
strategy decides node
strategy selection decides dashboard selection
dashboard node owns explicit metrics
strategy tree decides dashboard tree
target only binds
```

That is the core logic this effort should now preserve.
