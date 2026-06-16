# SNMP Switch Baseline Selection Rule

Date: 2026-06-14

## Goal

Define how OneOPS chooses:

- `current switch baseline`
or
- `routing-capable switch baseline`

This rule is generation-time only.
It does not inspect runtime data presence.

## Core Rule

Use this split:

```text
target class intent
  + matched strategy responsibility
  -> choose class baseline
```

Not:

```text
runtime data presence
  -> choose class baseline
```

## Inputs

Baseline selection should use only class-level and strategy-level inputs.

### 1. Target Profile

Use the target profile that already exists before dashboard materialization, such as:

- `catalog`
- `manufacturer`
- `platform`
- `model`
- version-range-compatible target metadata

These describe what class of switch the target belongs to.

### 2. Matched Strategy Tree

Use the strategy items that are selected for this target before dashboard generation.

This is important because the strategy tree already expresses monitoring responsibility.

In plain terms:

- if the matched strategy tree only expresses switching responsibility,
  use the current switch baseline;
- if the matched strategy tree expresses switching plus routing responsibility,
  use the routing-capable switch baseline.

### 3. Optional Explicit Baseline Key

If a later design adds an explicit baseline selector key,
that key may override the default rule.

But the first rule should not depend on that new field existing yet.

## Selection Rule

Use this priority order.

### Rule 1. Explicit Baseline Override Wins

If the strategy set / dashboard family layer explicitly says:

- use `routing-capable switch baseline`

then use it.

This is the highest-priority path.

### Rule 2. Routing Responsibility Selects Routing-Capable Baseline

If the matched strategy tree includes routing responsibility,
select:

- `routing-capable switch baseline`

Routing responsibility means the matched strategy side is intended to own routing families such as:

- `l3_route_table.*`
- `routing_bgp.*`
- `routing_ospf.*`

This is a strategy-meaning decision, not a runtime-data decision.

The narrow first mapping for that decision now lives in:

- [2026-06-14-snmp-routing-responsibility-mapping-table.md](/OneOPS/docs/superpowers/specs/2026-06-14-snmp-routing-responsibility-mapping-table.md)

### Rule 3. Otherwise Use Current Switch Baseline

If the target is a switch-class target and Rule 1 / Rule 2 do not apply,
select:

- `current switch baseline`

This remains the default switch path.

## Simplest Mental Model

Use this sentence:

```text
baseline follows responsibility, not current data
```

That means:

- routing-capable switch baseline is chosen because the target class is intended to carry routing responsibility;
- it is not chosen because one target currently exposed route metrics.

## What Counts As Routing Responsibility

For the first version, keep this narrow.

Routing responsibility exists when the matched strategy side is intended to cover:

- route-count responsibility
- routing protocol responsibility

In family terms, that means:

- `l3_route_table.*`
- `routing_bgp.*`
- `routing_ospf.*`

If none of these routing families belong to the matched strategy responsibility,
do not switch to the routing-capable baseline.

## What Must Not Be Used

Do not use:

- `has_data`
- `no_data`
- `not_exposed`
- one target's current SNMP success/failure
- one target's current push result

Those belong to `PanelState`, not baseline selection.

## Example

### Example A. Plain Access Switch

Inputs:

- target profile says switch
- matched strategy tree contains interface / system / topology evidence responsibilities
- no routing strategy responsibility

Result:

- `current switch baseline`

### Example B. Routing-Capable Switch

Inputs:

- target profile says switch
- matched strategy tree contains switching responsibility
- matched strategy tree also contains routing responsibility

Result:

- `routing-capable switch baseline`

Even if a concrete target later shows:

- `no_data`
or
- `not_exposed`

the baseline choice does not change.

## Immediate Consequence

This gives OneOPS one clean generation-time rule:

- resolve target class
- resolve matched strategy responsibility
- choose class baseline
- generate dashboard structure

Only after that should runtime decide panel state.
