# 2026-06-13 Strategy Tree To Dashboard Tree Mapping Design

## 1. Goal

This spec defines the missing business relationship between:

- the Teleabs strategy tree;
- the Grafana dashboard tree;
- the target-scoped materialized dashboard instances.

The immediate goal is not to add more dashboard features.
The goal is to correct the modeling direction before more generation logic is added.

Today, the system can already:

- resolve a strategy-set effective contract;
- preview panel capability support;
- preview and publish recording rules;
- resolve a dashboard template chain;
- materialize and save a Grafana dashboard by target.

But the current generation unit is still too flat.
It behaves like:

```text
one strategy set
-> one effective contract
-> one target-scoped dashboard instance
```

The intended product model is richer:

```text
one strategy set
-> one strategy tree
-> one dashboard tree
-> one target-scoped dashboard instance tree
```

This spec defines that mapping.

## 2. Problem Statement

The current automatic dashboard mechanism has a structural mismatch.

The user expectation is:

- `策略集` maps to a root dashboard;
- each `策略` maps to a concrete dashboard;
- parent/child strategy relationships map to parent/child dashboard relationships;
- target-specific generation materializes the whole tree for one device.

The current codebase does not do that.

Instead, it does the following:

1. resolve matched strategies into one `effective_contract`;
2. derive capability support and recording rules from that aggregate result;
3. resolve one `dashboard_variant`;
4. materialize one dashboard JSON per `(strategy_set_id, target_part, dashboard_variant)`.

This means the strategy tree is flattened too early.
By the time dashboard materialization happens, strategy-node ownership is no longer the primary structure.

The consequence is:

- one strategy set tends toward one large dashboard per variant;
- panel traceability can still mention `strategy_ids`, but dashboard ownership does not follow strategy nodes;
- no real dashboard parent/child tree exists at the instance level;
- template inheritance is too easily mistaken for business dashboard hierarchy.

## 3. Scope

This spec defines:

- the intended mapping from strategy tree to dashboard tree;
- the difference between strategy tree, template tree, and instance tree;
- the structural problems in the current generation mechanism;
- the minimum target model that should replace the current flat ownership model.

This spec does not define:

- final DB migrations;
- concrete API fields for every new model;
- detailed Grafana JSON layout rules;
- recording-rule generation rules;
- full implementation plan.

## 4. Canonical Business Mapping

The system should be understood in three distinct layers.

### 4.1 Strategy Tree

This is the semantic control tree.

Canonical structure:

```text
StrategySet
  -> Strategy root / selector-matched strategies
    -> child Strategy
      -> child Strategy
```

Its purpose is to answer:

- what semantic monitoring responsibilities exist;
- how strategy responsibilities are decomposed;
- what parent/child inheritance relationships exist between strategies.

Important rule:

- strategy tree boundaries must stay visible to dashboard generation;
- they must not disappear completely into one undifferentiated `effective_contract`.

### 4.2 Dashboard Logical Tree

This is the business dashboard tree, not the template tree.

Canonical structure:

```text
StrategySet
  -> Root Dashboard Definition
    -> Strategy Dashboard Definition
      -> Strategy Dashboard Definition
```

Required business meaning:

- `StrategySet` owns one root dashboard definition;
- each `Strategy` owns one strategy dashboard definition;
- parent strategy maps to parent dashboard definition;
- child strategy maps to child dashboard definition.

This tree exists before target-specific materialization.

### 4.3 Dashboard Instance Tree

This is the runtime/materialized tree for one target.

Canonical structure:

```text
(strategy_set_id, target_part)
  -> root dashboard instance
    -> strategy dashboard instance
      -> strategy dashboard instance
```

Each instance node should preserve:

- logical owner;
- parent dashboard instance;
- target identity;
- current publish state;
- snapshot history on overwrite.

## 5. Root Dashboard Versus Strategy Dashboard

This boundary must be explicit.

### 5.1 Root Dashboard

The root dashboard is owned by the strategy set.

Its role is:

- provide entry navigation;
- provide total overview;
- provide cross-strategy summary;
- provide links or hierarchy entry points to strategy dashboards.

It should not become a dumping ground for every panel from every strategy.

### 5.2 Strategy Dashboard

A strategy dashboard is owned by one specific strategy node.

Its role is:

- represent the dashboard view for one strategy responsibility;
- carry the panels that belong to that strategy’s metric groups and capabilities;
- inherit business hierarchy from the strategy tree.

A strategy dashboard may still use one or more dashboard variants for layout, but its ownership is strategy-based, not set-wide only.

## 6. What The Current Mechanism Gets Wrong

### 6.1 Current Generation Unit Is Too Flat

The current save/materialize flow is effectively:

```text
strategy_set_id + target_part + dashboard_variant
  -> one dashboard instance
```

This is too coarse.

It means:

- strategy set is the only business owner at dashboard-instance level;
- strategy nodes do not get their own dashboard nodes;
- the tree becomes one dashboard per variant instead of one dashboard tree per strategy set.

### 6.2 Strategy Tree Is Flattened Too Early

The current resolver first builds:

- `item_contracts`
- `effective_contract`

and then dashboard materialization consumes the effective result.

That is appropriate for:

- capability preview;
- recording-rule preview;
- some aggregate materialization decisions.

It is not sufficient for business dashboard ownership, because:

- it weakens strategy-node identity;
- dashboard generation sees final merged capability but not strong node ownership;
- panel bindings can record `strategy_ids`, but dashboard grouping by strategy node is lost.

### 6.3 Template Tree Is Not Dashboard Tree

`SnmpGrafanaDashboardTemplate.parent_key` forms a template inheritance chain.

That solves:

- layout inheritance;
- patch layering;
- target-specific template selection.

It does not solve:

- root dashboard versus strategy dashboard;
- parent dashboard versus child dashboard;
- target-scoped dashboard instance hierarchy.

Current confusion comes from treating template parent/child as if it were business dashboard parent/child.

Those are different trees.

### 6.4 Current Instance Persistence Is Parentless

The current save path persists:

- one target binding;
- many panel bindings;
- snapshots on overwrite.

But the saved dashboard itself is still effectively parentless.

In practical terms:

- current generated dashboards are not explicitly hung under a root dashboard;
- current target binding ownership is variant-scoped, not strategy-node-scoped;
- the saved platform dashboard record does not represent a business dashboard tree.

### 6.5 The Mechanism Naturally Produces Oversized Dashboards

Because ownership is set-wide and flattened, more strategies tend to produce:

- more panels in one dashboard;
- less navigable structure;
- weaker separation of responsibility;
- harder user understanding of which dashboard corresponds to which strategy.

This is the opposite of the intended product behavior.

## 7. Recommended Target Model

### 7.1 Keep Three Trees Distinct

The system should explicitly preserve:

1. strategy tree;
2. dashboard logical tree;
3. dashboard instance tree.

Template chain remains a fourth concern, but only as layout inheritance.
It must not replace the logical or instance tree.

### 7.2 Change The Dashboard Generation Unit

Instead of:

```text
strategy_set -> one dashboard per variant
```

move toward:

```text
strategy_set -> root dashboard
strategy node -> strategy dashboard
target -> materialized instance tree
```

This does not necessarily require all dashboards to be saved in one transaction initially.
But it does require the data model and ownership model to support it.

### 7.3 Preserve Strategy Ownership Into Dashboard Materialization

Dashboard generation must retain a structure like:

```text
strategy node
  -> owned metric groups
  -> owned panel slots
  -> owned dashboard definition
```

The system may still derive aggregate support information from the full `effective_contract`, but final dashboard grouping should not be based only on the flattened aggregate.

### 7.4 Root And Child Relationships Must Be Persisted

At minimum, the runtime model must be able to express:

- root dashboard instance;
- child dashboard instance;
- parent dashboard link;
- owning strategy or owning strategy set;
- target identity.

Without these relationships, the system still has only flat dashboard records, not a tree.

## 8. Suggested Ownership Model

Recommended logical ownership:

- root dashboard owner: `strategy_set_id`
- strategy dashboard owner: `strategy_id`

Recommended target materialization ownership:

- root instance owner: `(strategy_set_id, target_part, root_dashboard_variant)`
- strategy instance owner: `(strategy_id, target_part, dashboard_variant)`

The exact storage schema may vary, but the key rule is:

- strategy-set ownership and strategy-node ownership must both exist;
- they must not be collapsed into only `strategy_set_id + target_part + dashboard_variant`.

## 9. What Should Be Generated From What

### 9.1 Root Dashboard Inputs

Root dashboard generation should consume:

- strategy-set level overview metadata;
- selected cross-strategy capabilities;
- strategy-node links;
- summary panels.

### 9.2 Strategy Dashboard Inputs

Strategy dashboard generation should consume:

- one strategy node’s owned contract slice;
- that node’s metric groups and panel slots;
- inherited strategy context if needed;
- recording-rule outputs relevant to that node.

### 9.3 Template Use

Template chain should still decide:

- visual arrangement;
- section composition;
- vendor/model variant patching.

But template choice should not decide business ownership.

Ownership comes from the strategy tree to dashboard tree mapping.

## 10. Minimum Migration Direction

The safest direction is not a full rewrite first.
It is a controlled migration.

Recommended order:

1. define root dashboard and strategy dashboard concepts explicitly in the model;
2. preserve strategy-node ownership into dashboard planning;
3. generate a root dashboard plus one or more strategy dashboards for a small pilot case;
4. add parent/child persistence to dashboard instances;
5. then expand to more variants and strategy shapes.

## 11. Minimum Pilot Scope

A good pilot should be intentionally small:

- one strategy set;
- one parent strategy;
- one child strategy;
- one target device;
- one dashboard variant family.

The pilot is successful if the system can produce:

- one root dashboard instance for the strategy set;
- one dashboard instance for the parent strategy;
- one dashboard instance for the child strategy;
- explicit parent/child dashboard relationships;
- stable target-scoped ownership for all three nodes.

## 12. Success Criteria

This design is successful when:

1. strategy set and strategy nodes no longer collapse into only one dashboard ownership unit;
2. the system can represent a root dashboard plus child strategy dashboards;
3. template inheritance is no longer confused with business dashboard hierarchy;
4. target materialization can produce a dashboard tree, not only one flat dashboard per variant;
5. future automatic generation becomes easier to reason about, not more opaque.
