# SNMP Shared Dashboard Persistence Closure Plan

Date: 2026-06-14

## Goal

Close the next real SNMP dashboard gap by moving persistence from:

```text
class-level generation + by-target dashboard save
```

to:

```text
class-level generation + shared dashboard persistence + target binding
```

This batch is not about changing what families exist.
It is about changing what gets persisted as the primary dashboard object.

## Problem Statement

Current backend behavior is already better than before:

- dashboard generation is decided by `TargetClass / ClassBaseline / VariantBaseline`;
- runtime data does not decide whether a family exists;
- switch, routing-capable switch, and generic SNMP now all resolve through the same definition-layer model.

But persistence still breaks the model:

- the final saved dashboard object is still a `by-target` instance;
- the dashboard list still reflects target-specific copies;
- target binding and dashboard object identity are still collapsed into one thing.

That means the platform currently says:

```text
generation is class-level
persistence is target-level
```

This batch closes that mismatch.

## Closure Target

After this batch, SNMP dashboard persistence should be explainable as:

```text
TargetClass
  -> ClassBaseline
    -> VariantBaseline
      -> SharedDashboard
        -> TargetBinding
```

Meaning:

- `SharedDashboard` is the persistent dashboard object;
- `TargetBinding` links one target to one shared dashboard;
- target no longer owns a private dashboard copy.

## Scope Lock

Allowed in this batch:

- introduce one shared SNMP dashboard persistence model;
- keep current generation/baseline logic;
- preserve current `save/by-target` API entrypoints;
- change `save/by-target` semantics so it binds a target to a shared dashboard;
- change dashboard list/query paths to expose shared dashboards as first-class objects;
- keep target-level lookup/query capability;
- migrate quick env startup/runtime ensure flow to shared persistence semantics;
- update save/replay/history semantics so they refer to shared dashboard identity plus target binding where needed.

Not allowed in this batch:

- no new panel families;
- no runtime `has_data / no_data / not_exposed` redesign;
- no per-device structure decisions;
- no target-specific dashboard branching;
- no UI redesign beyond what is strictly needed to stop showing per-target duplicates;
- no attempt to generalize beyond SNMP in this batch.

## Canonical Decisions

These are fixed:

1. **Generation remains class-level.**
   Persistence must not reintroduce target-level dashboard structure.

2. **Shared dashboard identity is definition-layer identity.**
   It should be uniquely determined by:
   - `class_baseline`
   - `variant_baseline`
   - `template_key`
   - and, if still needed, one stable content-generation discriminator

3. **Target remains binding-only.**
   A target may influence:
   - which baseline it selects
   - which variables it supplies when viewing

   A target must not cause creation of a private dashboard copy.

4. **`save/by-target` remains as a public API shape.**
   But its meaning changes from:
   - “save one dashboard for this target”

   to:
   - “resolve this target’s shared dashboard and bind this target to it”

5. **Dashboard list pages should show shared dashboards.**
   Not target-suffixed duplicates.

## Expected Model

### `SharedDashboard`

Persistent business object for SNMP dashboard definitions.

Minimum semantics:

- one row per shared dashboard identity;
- owns dashboard code / uid / content / baseline metadata;
- not named by target code.

Examples:

- `OneOPS SNMP Generic Ops`
- `OneOPS SNMP Switch Ops`
- `OneOPS SNMP Routing-Capable Switch Ops`

### `TargetBinding`

Persistent relation:

```text
target_part -> shared_dashboard
```

Meaning:

- which shared dashboard a target currently uses;
- optional audit fields for first/last bind, current variant, save source, etc.

### `SaveBatch`

Still useful, but should now audit:

- shared dashboard updates;
- binding updates;
- not target-private dashboard creation.

## Behavioral Changes

### 1. Save Path

Current:

```text
target -> materialize -> save dashboard instance for target
```

Target:

```text
target
  -> resolve baseline
  -> materialize shared dashboard
  -> find or update shared dashboard object
  -> bind target to shared dashboard
```

### 2. Dashboard Naming

Current names often include target code.

Target state:

- shared dashboard name should be class/variant oriented;
- target code should live in binding/query context, not dashboard name.

### 3. List Queries

Current:

- list shows target-scoped saved instances.

Target:

- list shows shared dashboards;
- optional drill-down shows bound targets.

### 4. Replay / History

Current history is close to target-oriented save replay.

Target:

- replay should identify which shared dashboard changed;
- and, separately, what target bindings were affected.

## Long Task Breakdown

### Task 1: Freeze Shared Persistence Contract With Failing Tests

Add failing tests that define:

- a save for two targets with the same `class_baseline + variant_baseline + template_key` does **not** create two persistent dashboards;
- only one shared dashboard row exists;
- two target bindings point to that row;
- dashboard list query returns one shared dashboard, not two target copies;
- routing-capable switch follows the same rule.

### Task 2: Introduce Shared SNMP Dashboard Persistence Object

Add or repurpose a persistence model so the primary object is:

- shared dashboard identity;
- baseline metadata;
- dashboard content;
- template identity.

This object becomes the owner of:

- dashboard code / uid / json content;
- baseline metadata;
- content hash and update metadata.

### Task 3: Split Target Binding Out Of Dashboard Identity

Refactor binding storage so target linkage is separate from dashboard ownership.

Required behavior:

- re-saving a second target in the same class does not clone the dashboard;
- only a binding row is added or updated.

### Task 4: Change Save Semantics Without Breaking API Entry

Keep existing API entrypoints:

- `save/by-target`
- `save-and-sync/by-target`
- tree save if still in scope

But change internal behavior to:

- shared dashboard resolve or create;
- target bind or update;
- response includes shared dashboard identity plus current binding result.

### Task 5: Change List / Query Paths To Shared Dashboard Semantics

List APIs and UI-facing query paths should:

- return shared dashboards as top-level rows;
- stop surfacing target-private duplicates as if they are separate dashboards;
- provide an optional bound-targets view when needed.

### Task 6: Reframe Save History And Replay

History should now reflect:

- shared dashboard content changes;
- binding changes;
- baseline changes where applicable.

Do not keep the old mental model where every save batch implies one new target-specific dashboard object.

### Task 7: Migrate Quick Env To Shared Persistence

Quick env startup/runtime ensure should:

- ensure shared dashboards exist for:
  - generic SNMP
  - current switch
  - routing-capable switch
- ensure live targets bind to them;
- stop creating one persistent dashboard per target.

## Verification Standard

This batch is complete only if all of these are true:

1. Two targets in the same SNMP class/variant resolve to one shared dashboard object.
2. Dashboard list returns one shared dashboard row, not duplicated target instances.
3. Target binding lookup still works.
4. Generic SNMP, current switch, and routing-capable switch all follow the same persistence rule.
5. Quick env current environment shows real usable shared dashboards, not target-suffixed copies.

## Risks

### 1. Audit Model Drift

Current `save-batch / replay` behavior is target-oriented.
This batch must deliberately move it to:

- shared dashboard audit
- plus binding audit

instead of preserving old semantics implicitly.

### 2. Backward Compatibility

Existing UI and callers may assume:

- one saved row == one target dashboard

This assumption must be isolated and rewritten where necessary.

### 3. Naming Transition

Old dashboards already saved with target-specific names may require:

- migration;
- mapping;
- or one transition compatibility layer.

## Recommended Implementation Order

1. Freeze tests for shared persistence semantics.
2. Add shared dashboard model.
3. Split binding persistence.
4. Change backend save path.
5. Change list/query path.
6. Update quick env runtime ensure flow.
7. Update docs and handoff.

## Done Definition

This batch is done when SNMP dashboard persistence is no longer meaningfully `by-target`.

At that point the system should be describable as:

- class-level generation
- shared dashboard persistence
- target binding

and not as:

- class-level generation
- target-level dashboard duplication
