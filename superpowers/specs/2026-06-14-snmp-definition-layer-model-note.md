# SNMP Definition-Layer Model Note

Date: 2026-06-14

## Goal

This note defines the minimum business objects that must exist before any target-scoped runtime materialization is considered complete.

It is intentionally narrower than a full implementation spec.
It does not define:

- DB migrations
- API shapes
- Grafana JSON layout details
- recording-rule content rules

It defines only:

- core objects
- ownership
- identity
- whether each object is target-scoped

## Core Rule

The definition layer must remain valid without `target_part`.

That means:

- business ownership is established before runtime materialization;
- `target_part` may create runtime instances;
- `target_part` must not become the primary identity of definition-layer objects.

## Object Set

The minimum object set is:

1. `StrategyTree`
2. `Dashboard Logical Tree`
3. `Template Tree`
4. `Dashboard Instance Tree`
5. `Recording Rule Runtime`

## 1. StrategyTree

### Purpose

This is the semantic control tree for monitoring responsibilities.

### Canonical Structure

```text
StrategySet
  -> Strategy node
    -> Strategy node
      -> Strategy node
```

### It Must Answer

- what strategy responsibilities exist
- what parent/child strategy relationships exist
- what inheritance path exists between strategies

### Identity

- root container identity: `strategy_set_id`
- node identity: `strategy_id`

### Ownership

- `StrategySet` owns the tree container
- each `Strategy` owns its own semantic node

### Target Scope

- not target-scoped

## 2. Dashboard Logical Tree

### Purpose

This is the business dashboard tree.
It is not the Grafana template inheritance chain.

### Canonical Structure

```text
StrategySet
  -> Root Dashboard Definition
    -> Strategy Dashboard Definition
      -> Strategy Dashboard Definition
```

### It Must Answer

- what root dashboard definition exists for a strategy set
- what strategy dashboard definition exists for each strategy node
- how parent/child strategy relationships map to parent/child dashboard definitions
- which panels belong to which logical dashboard node

### Identity

- root dashboard definition identity: `(strategy_set_id, root_dashboard_key)`
- strategy dashboard definition identity: `(strategy_id, dashboard_key)`

`dashboard_key` here is a logical key, not necessarily a persisted table field yet.
The important rule is that root-definition identity and strategy-definition identity must be different.

### Ownership

- root dashboard definition owner: `strategy_set_id`
- strategy dashboard definition owner: `strategy_id`

### Target Scope

- not target-scoped

## 3. Template Tree

### Purpose

This is the visual/layout inheritance chain used for:

- layout inheritance
- patch layering
- vendor/model-specific presentation selection

### Canonical Structure

```text
Template
  -> child template
    -> child template
```

### It Must Answer

- how dashboard layout is inherited
- how vendor/model patches are applied

### It Must Not Answer

- business dashboard ownership
- root dashboard vs strategy dashboard meaning
- parent/child business hierarchy between dashboard nodes

### Identity

- template identity: `template_key`

### Ownership

- owned by template catalog / template system, not by `target_part`

### Target Scope

- not target-scoped by identity
- may be selected using target context at runtime

## 4. Dashboard Instance Tree

### Purpose

This is the runtime tree materialized for one target.

### Canonical Structure

```text
(strategy_set_id, target_part)
  -> root dashboard instance
    -> strategy dashboard instance
      -> strategy dashboard instance
```

### It Must Answer

- what concrete dashboard instances exist for one target
- what parent/child instance relationships exist
- what logical definition each instance came from
- what overwrite/snapshot state exists

### Identity

- root dashboard instance identity: `(strategy_set_id, target_part, root_dashboard_variant)`
- strategy dashboard instance identity: `(strategy_id, target_part, dashboard_variant)`

### Ownership

- root instance owner: `strategy_set_id`
- strategy instance owner: `strategy_id`

### Target Scope

- target-scoped

## 5. Recording Rule Runtime

### Purpose

This is the runtime rule-generation and publish loop.

### It Must Answer

- what rules are previewed for a target
- what YAML is materialized for a target
- what publish record exists for a target
- whether the current target runtime is ready for dashboard instance save/sync

### Identity

- preview/materialization runtime identity: `(strategy_set_id, target_part)`
- publish record identity: `publish_id`
- publish ownership key: `(strategy_set_id, target_part)`

### Ownership

- runtime publish ownership is set-scoped plus target-scoped
- it is not the owner of dashboard logical definitions

### Target Scope

- target-scoped

## Ownership Matrix

| Object | Primary Owner | Identity | Target-Scoped? | Notes |
|---|---|---|---|---|
| StrategyTree container | `strategy_set_id` | `strategy_set_id` | No | semantic root |
| StrategyTree node | `strategy_id` | `strategy_id` | No | semantic responsibility |
| Root Dashboard Definition | `strategy_set_id` | `(strategy_set_id, root_dashboard_key)` | No | business root dashboard |
| Strategy Dashboard Definition | `strategy_id` | `(strategy_id, dashboard_key)` | No | business strategy dashboard |
| Panel Slot Ownership | `strategy_id` or `strategy_set_id` | `(owner_id, panel_slot_key)` | No | root summary panels may belong to set; strategy panels belong to strategy |
| Template Node | `template_key` | `template_key` | No | layout inheritance only |
| Root Dashboard Instance | `strategy_set_id` | `(strategy_set_id, target_part, root_dashboard_variant)` | Yes | runtime materialization |
| Strategy Dashboard Instance | `strategy_id` | `(strategy_id, target_part, dashboard_variant)` | Yes | runtime materialization |
| Recording Rule Preview/Materialization | `strategy_set_id` | `(strategy_set_id, target_part)` | Yes | runtime computation |
| Recording Rule Publish Record | `publish_id` with `(strategy_set_id, target_part)` ownership | `publish_id` | Yes | runtime audit record |

## Interpretation Rules

### Rule 1. Target Scope Belongs To Runtime Objects

If an object cannot exist without `target_part`, it is runtime-layer by default.

### Rule 2. Strategy Ownership Must Survive Materialization

If a dashboard or panel is semantically owned by a strategy node, runtime materialization must preserve that owner instead of collapsing everything to `strategy_set_id + target_part`.

### Rule 3. Template Selection Does Not Define Business Ownership

Template choice may be driven by target context.
Business ownership must not be.

### Rule 4. Root And Strategy Nodes Need Separate Identities

The root dashboard definition and a strategy dashboard definition cannot share the same ownership key shape.
Otherwise the model collapses back into one flat unit.

## Immediate Design Consequence

The next implementation question should no longer be:

```text
how do we further harden one by-target publish/save path?
```

It should be:

```text
what definition-layer object do current tree pilot nodes correspond to,
and what identity/ownership is still missing?
```

## What This Note Does Not Yet Decide

This note deliberately does not yet decide:

- exact storage tables for dashboard logical definitions
- whether dashboard logical definitions are first-class persisted rows or a derived planning model first
- whether panel slot ownership is stored independently or derived from strategy dashboard definitions

Those are next-step design decisions, not prerequisites for boundary clarity.
