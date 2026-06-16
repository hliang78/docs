# SNMP Definition Closure Summary

Date: 2026-06-14

## Goal

This page is the one-page summary for the current definition-layer correction.

If someone needs the shortest path back into this work, start here first.

This page compresses the current conclusion into four parts:

1. boundary
2. objects
3. ownership
4. pilot gap

## 1. Boundary

The work must be split into two layers.

### Definition Layer

```text
StrategySet
  -> StrategyTree
    -> DashboardTree
      -> PanelSlot ownership
```

This layer answers:

- what `RootNode` exists
- what `StrategyNode` exists
- who owns each `PanelSlot`
- how business hierarchy works

This layer must not depend on `target_part`.
It also must not depend on whether a current runtime target happens to have data.

### Runtime Layer

```text
(strategy_set_id, target_part)
  -> rule preview / materialize / publish
  -> dashboard instance materialize / save / sync
```

This layer answers:

- what target is being rendered
- what runtime rule state exists
- what `DashboardInstance` exists
- what save/publish state exists

This layer may depend on `target_part`,
but it must consume the definition model instead of becoming the definition model.
It changes panel state, not panel-family existence.

## 2. Core Objects

Use these as the minimum object set.

| Object | Layer | Owner | Target-scoped? |
|---|---|---|---|
| `StrategyTree` | definition | `strategy_set_id` + `strategy_id` nodes | No |
| `DashboardTree` | definition | `strategy_set_id` root + `strategy_id` strategy nodes | No |
| `TemplateTree` | definition/layout | template system | No |
| `PanelSlot` | definition | `strategy_set_id` or `strategy_id` | No |
| `DashboardInstance` | runtime | `strategy_set_id` or `strategy_id` | Yes |
| `RuleRun` | runtime | `(strategy_set_id, target_part)` | Yes |

For class-level generation, keep one extra minimal split:

| Object | Meaning |
|---|---|
| `ClassBaseline` | what families exist for one target class |
| `VariantBaseline` | what one view/layout includes under that class |
| `PanelState` | what one rendered panel currently shows at runtime |

## 3. Ownership

### Root Owner

`RootNode` is owned by:

- `strategy_set_id`

`RootNode` should own only:

- navigation
- overview
- cross-strategy summary
- evidence/context blocks

### Strategy Owner

`StrategyNode` is owned by:

- `strategy_id`

`StrategyNode` should own:

- detailed strategy panels
- local strategy summaries
- panels derived from that strategy’s metric groups and capabilities

### Current Owner Baseline

Current default owner decision is:

- `interface_basic.*` -> `strategy_id`
- `system_basic.*` -> `strategy_id`
- topology evidence table families -> `strategy_id`
- platform/evidence/navigation/summary -> `strategy_set_id`

Hard rule:

- root is not the fallback bucket for weak runtime evidence

Hard rule:

- runtime data presence is not the gate for whether a family belongs to the baseline

## 4. Short Names

Prefer these names in docs and follow-up design:

- `RootNode`
- `StrategyNode`
- `NodeOwner`
- `PanelSlot`
- `DashboardInstance`
- `LeafMatch`
- `SaveBatch`

Key distinctions:

- `NodeOwner` is not `LeafMatch`
- `RootNode` is not `RootCode`
- `SaveBatch` is not part of the business model

## 5. Current Pilot

The current tree pilot is a bridge, not the final model.

### Already Good Enough In Pilot

- `dashboard_role = root` gives a visible `RootNode`
- `dashboard_role = strategy` gives a visible `StrategyNode`
- `owner_strategy_id` gives a usable `NodeOwner`
- `parent_dashboard_code` / `root_dashboard_code` give runtime parent links

### Still Transitional

- `matched_strategy_ids` is only `LeafMatch`
- `save_batch_id` is only `SaveBatch`
- `dashboard_content_changed` is only `ContentDiff`
- `panel_bindings_changed` is only `BindingDiff`
- `PanelSlot` ownership is still too implicit

## 6. Main Gap

The main remaining design gap is now simple:

```text
PanelSlot ownership is still weaker than NodeOwner.
```

That means:

- node ownership is partly explicit
- panel ownership is still too runtime-driven

## 7. What Not To Do Next

Do not prioritize:

- more by-target readiness states
- more save guards
- more replay UX
- more target-scoped runtime polish

Those are secondary now.

## 8. What To Do Next

The next primary task should still be definition-layer work.

Current status:

- current active switch family closure is now good enough to treat as closed;
- the switch line now lives under a generic SNMP target-class baseline model;
- `snmp.generic` is the common SNMP floor;
- `switch.current` and `switch.routing_capable` are additive class-baseline specializations over that floor.

The guiding rule is now formalized in:

- [2026-06-14-snmp-class-baseline-generation-rule.md](/OneOPS/docs/superpowers/specs/2026-06-14-snmp-class-baseline-generation-rule.md)

Best next question:

```text
Which next SNMP target class should enter the generic baseline model after switch?
```

The current model-correction phase is no longer blocked on “does SNMP need a generic baseline model”.
That model now exists.
Follow-up work should extend it rather than reopen the generation-vs-runtime argument.
