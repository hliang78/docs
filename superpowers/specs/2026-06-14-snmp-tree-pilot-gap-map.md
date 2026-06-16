# SNMP Tree Pilot Gap Map

Date: 2026-06-14

## Goal

This note maps the current tree pilot to the intended definition-layer model.

It answers three questions:

1. what current pilot objects already line up with the model?
2. what current pilot objects are only runtime or audit artifacts?
3. what current pilot behaviors are still heuristic gaps?

This note uses short names on purpose.

## Short Names

Use these names in follow-up discussion.

- `StrategyTree`
- `DashboardTree`
- `TemplateTree`
- `RootNode`
- `StrategyNode`
- `NodeOwner`
- `PanelSlot`
- `DashboardInstance`
- `LeafMatch`
- `SaveBatch`

## Target Model

The intended shape remains:

```text
StrategyTree
  -> DashboardTree
    -> DashboardInstance
```

Current pilot does not fully implement that model.
It implements a bridge.

## Current Pilot Surface

The current tree pilot exposes or persists these main fields:

- `dashboard_role`
- `owner_strategy_id`
- `parent_dashboard_code`
- `root_dashboard_code`
- `matched_strategy_ids`
- `save_batch_id`
- `dashboard_content_changed`
- `panel_bindings_changed`

These fields are useful, but they do not all belong to the same layer.

## Mapping Table

| Current field / behavior | Short meaning | Layer | Status |
|---|---|---|---|
| `dashboard_role = root` | `RootNode` marker | definition -> runtime bridge | aligned enough for pilot |
| `dashboard_role = strategy` | `StrategyNode` marker | definition -> runtime bridge | aligned enough for pilot |
| `owner_strategy_id` | `NodeOwner` for strategy node | definition-layer ownership signal | aligned enough for pilot |
| empty `owner_strategy_id` on root | root owned by set | definition-layer ownership signal | aligned enough for pilot |
| `parent_dashboard_code` | parent `DashboardInstance` link | runtime instance tree | aligned enough for pilot |
| `root_dashboard_code` | root `DashboardInstance` link | runtime instance tree | aligned enough for pilot |
| `matched_strategy_ids` | `LeafMatch` | runtime selection evidence | not a logical owner by itself |
| `save_batch_id` | `SaveBatch` | runtime audit only | not part of definition model |
| `dashboard_content_changed` | dashboard content diff | runtime audit only | not part of definition model |
| `panel_bindings_changed` | binding diff | runtime audit only | not part of definition model |

## What Already Aligns

These pilot parts already point in the right direction.

### 1. RootNode Exists

The pilot now has an explicit root-vs-strategy split.

That matters because:

- `RootNode` is no longer implicit;
- the model no longer collapses everything into one flat dashboard unit.

### 2. StrategyNode Exists

The pilot now exposes strategy-owned nodes instead of only one target-scoped flat dashboard.

That is the first real structural sign of `DashboardTree`.

### 3. NodeOwner Exists

`owner_strategy_id` is the strongest current hint that a node is owned by one strategy instead of by the whole set.

This is closer to the intended definition model than anything in the old flat path.

### 4. Runtime Parent Links Exist

`parent_dashboard_code` and `root_dashboard_code` mean the runtime layer can already express a simple `DashboardInstance` tree.

That is good, but it is still instance-level, not the full definition model.

## What Is Only Runtime Evidence

These pilot fields are useful but should not be mistaken for definition-layer objects.

### 1. LeafMatch

`matched_strategy_ids` tells us which leaf strategy was selected in the current runtime path.

It is:

- runtime selection evidence
- useful for audit
- useful for tie-break

It is not:

- the owner of every panel
- the identity of a logical dashboard node
- a substitute for `StrategyTree`

### 2. SaveBatch

`save_batch_id` is only a runtime audit grouping key.

It is helpful for:

- replay
- audit
- debugging

It says nothing about:

- logical ownership
- dashboard definition identity
- panel slot identity

### 3. Change Flags

`dashboard_content_changed` and `panel_bindings_changed` are runtime diff results.

They help answer:

- what changed in this save?

They do not answer:

- who should own this node?
- who should own this panel?

## Current Gaps

These are the main remaining gaps.

### Gap 1. PanelSlot Is Still Too Late

Current pilot can persist node ownership better than before,
but `PanelSlot` ownership is still not a fully first-class definition-layer object.

In other words:

- node ownership is partially explicit;
- panel ownership is still partly inferred late.

### Gap 2. LeafMatch Can Still Be Overused

Because `LeafMatch` is visible and concrete,
there is a risk that people treat it like the real owner.

That would be wrong.

`LeafMatch` helps runtime selection.
It does not replace logical ownership.

### Gap 3. RootNode Can Still Become A Fallback Bucket

Even with the owner decision table in place,
the pilot can still drift toward:

- “root owns it because we could not prove a better owner”

That is still a transitional heuristic, not a valid model rule.

### Gap 4. Audit Signals Can Distract From Model Gaps

The pilot now has rich audit fields:

- `SaveBatch`
- content change
- binding change
- replay

These are useful,
but they can create the illusion that ownership is already settled.

It is not.

## Current Evaluation Rule

The pilot should now be judged by this rule:

```text
Does the pilot preserve the owner that the definition layer already says should exist?
```

It should not be judged by:

```text
Did the pilot find some plausible runtime owner after the fact?
```

## Minimal Alignment Checklist

The current pilot is aligned only if all of these are true.

1. `RootNode` remains limited to summary, navigation, or evidence roles.
2. `StrategyNode` remains the default owner for detailed panel families like `interface_basic.*` and `system_basic.*`.
3. `NodeOwner` is treated as stronger than runtime fallback heuristics.
4. `LeafMatch` is treated as runtime evidence, not as the full logical owner.
5. `SaveBatch` and change flags are treated as audit-only fields.

## Next Design Question

The next definition-layer question is no longer:

```text
how do we add more runtime save or replay detail?
```

It is:

```text
how do we make PanelSlot ownership as explicit as NodeOwner?
```

That is the main gap between the current pilot and the intended model.
