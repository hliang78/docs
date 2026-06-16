# 2026-06-13 Strategy Dashboard Current Mechanism Issues

## 1. Purpose

This note turns the current dashboard-generation concerns into an explicit issue list.

The goal is not to restate the whole target design.
The goal is to make the current mechanism’s problems concrete enough that implementation can be prioritized and scoped.

## 2. Current Generation Unit Is Wrong

### Issue

The current Grafana generation unit is:

```text
strategy_set_id + target_part + dashboard_variant
  -> one dashboard instance
```

### Why This Is A Problem

This makes the strategy set the only first-class business owner at dashboard-instance level.
It does not let one strategy set expand into a dashboard tree.

### Consequence

- one strategy set tends toward one large dashboard per variant;
- strategy nodes cannot own their own dashboards;
- root/child dashboard hierarchy cannot emerge naturally.

### Priority

`P0`

## 3. Strategy Tree Is Flattened Too Early

### Issue

The current resolver first aggregates matched strategy items into one `effective_contract`, then uses that aggregate as the primary dashboard-generation input.

### Why This Is A Problem

`effective_contract` is useful for aggregate capability and recording-rule logic, but it weakens node-level ownership.
Dashboard generation loses strong visibility into:

- which strategy node owns which dashboard node;
- which panels belong to which strategy dashboard;
- how parent/child strategy relationships should map to dashboard hierarchy.

### Consequence

- panel traceability can still mention `strategy_ids`;
- dashboard ownership no longer follows the strategy tree;
- future splitting into child dashboards becomes harder.

### Priority

`P0`

## 4. Template Tree Is Being Mistaken For Dashboard Tree

### Issue

`SnmpGrafanaDashboardTemplate.parent_key` forms a template inheritance chain, but it is too easy to treat it as if it were a business dashboard tree.

### Why This Is A Problem

Template inheritance answers:

- how layout patches compose;
- how vendor/model-specific template overrides work.

It does not answer:

- which dashboard is the root dashboard for a strategy set;
- which dashboard belongs to which strategy node;
- which materialized dashboard should be a child of which parent dashboard.

### Consequence

- implementation discussions blur layout inheritance with business hierarchy;
- root/child dashboard ownership stays undefined;
- persistence remains flat.

### Priority

`P0`

## 5. Current Dashboard Instances Are Parentless

### Issue

Current save flow persists dashboard target bindings, panel bindings, and snapshots, but not a true parent/child dashboard relationship.

### Why This Is A Problem

The platform can record:

- dashboard code;
- target part;
- variant;
- panel traceability.

It cannot record:

- parent dashboard instance;
- root dashboard instance;
- strategy-node owner of a child dashboard.

### Consequence

- dashboards remain effectively flat records;
- hierarchy cannot be reconstructed from persistence;
- future root/child navigation would need ad hoc conventions instead of explicit ownership.

### Priority

`P0`

## 6. The Existing Strategy-Set Dashboard Binding Is Too Narrow

### Issue

`TeleabsStrategySetDashboardBinding` currently behaves like a single-value entry binding.

### Why This Is A Problem

It is suited to:

- “this strategy set currently points at this dashboard code”

It is not suited to:

- “this strategy set owns one root dashboard and many child strategy dashboards”

### Consequence

- one strategy set can only look like one dashboard binding at the top level;
- root dashboard versus strategy dashboard is not represented cleanly;
- rebinding tends to replace instead of grow into a tree.

### Priority

`P1`

## 7. Panel Bindings Preserve Traceability But Not Dashboard Ownership

### Issue

Current `panel_binding` rows can preserve `strategy_ids`, `metric_keys`, `capability_keys`, and `record_names`, but they do not define dashboard-node ownership strongly enough.

### Why This Is A Problem

This is good for debugging and traceability.
It is not enough for tree generation because the system still cannot say:

- this panel belongs to the root dashboard;
- this panel belongs to strategy dashboard A;
- strategy dashboard A is a child of strategy dashboard B.

### Consequence

- strategy is preserved only as metadata;
- tree structure is not preserved as model truth.

### Priority

`P1`

## 8. Root Dashboard Content Boundary Is Undefined

### Issue

The current mechanism has no explicit product boundary for what belongs in the root dashboard versus a strategy dashboard.

### Why This Is A Problem

Without this boundary, any future tree model still risks collapsing into:

- a root dashboard that becomes another oversized “everything board”.

### Consequence

- hierarchy exists on paper but not in user experience;
- dashboards remain difficult to navigate;
- root dashboards become overloaded.

### Priority

`P1`

## 9. Automatic Generation Naturally Produces Oversized Dashboards

### Issue

Because generation is set-wide and variant-wide, the system naturally accumulates more panels into one dashboard as more strategies and metric groups are added.

### Why This Is A Problem

This is the opposite of the desired product direction, which is:

- root dashboard for overview and navigation;
- strategy dashboards for focused responsibility views.

### Consequence

- poor information architecture;
- weak ownership boundaries;
- harder future maintenance and user comprehension.

### Priority

`P1`

## 10. Target Materialization Is Too Early In The Ownership Model

### Issue

Current ownership begins directly at target-scoped materialization instead of first defining a logical dashboard tree.

### Why This Is A Problem

The cleaner progression should be:

```text
strategy tree
-> dashboard logical tree
-> target-scoped dashboard instance tree
```

The current progression is closer to:

```text
strategy set aggregate
-> target + variant
-> one dashboard
```

### Consequence

- target dimension is overemphasized;
- logical root/child dashboard structure is under-modeled;
- future hierarchy has to be retrofitted into target bindings.

### Priority

`P1`

## 11. Current Mechanism Summary

The current system is not missing all the raw pieces.
It already has:

- strategy-set contract resolution;
- template chain resolution;
- target binding;
- panel binding;
- snapshot persistence.

The problem is that these pieces are wired around the wrong primary unit.

Today the system is optimized for:

```text
one strategy set
-> one effective contract
-> one dashboard per target + variant
```

The product direction requires:

```text
one strategy set
-> one strategy tree
-> one dashboard logical tree
-> one target-scoped dashboard instance tree
```

## 12. Recommended Next Step

Do not immediately expand more generation logic on top of the current flat model.

Instead:

1. introduce explicit root-dashboard versus strategy-dashboard concepts;
2. preserve strategy-node ownership into dashboard planning;
3. pilot one small tree end-to-end;
4. only then generalize materialization and persistence.
