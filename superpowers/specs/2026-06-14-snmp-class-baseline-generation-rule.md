# SNMP Class Baseline Generation Rule

Date: 2026-06-14

## Goal

Make one rule explicit:

```text
generation decides what exists
runtime decides what state it shows
```

This note is intentionally small.
It does not add new runtime gates, new readiness logic, or per-device dashboard branching.

## Core Split

There are only two stages here.

### 1. Generation Stage

The generation stage decides:

- what `PanelFamily` exists;
- which `VariantBaseline` includes that family;
- whether that family belongs to `root` or `strategy`.

The generation stage is class-level, not device-instance-level.

It should use:

- strategy meaning;
- class-level device intent;
- variant design.

It should not use:

- whether one target currently has data;
- whether one target currently exposes an OID;
- whether one runtime push succeeded or failed.

### 2. Runtime Stage

The runtime stage decides only:

- does the panel currently have data;
- does the panel currently have no data;
- is the source currently not exposed.

Runtime changes panel state.
Runtime does not decide whether the family exists in the baseline.

## Minimum Objects

Use the smallest possible set of names.

### `ClassBaseline`

Meaning:

- the baseline dashboard family set for one class of targets

Examples:

- current switch baseline
- future routing-capable switch baseline

### `VariantBaseline`

Meaning:

- one layout/view baseline under a class baseline

Examples:

- operations variant
- capacity variant

### `PanelFamily`

Meaning:

- one stable semantic panel family

Examples:

- `interface_basic.*`
- `system_basic.*`
- `l2_mac_table.*`
- `l3_route_table.*`

### `PanelState`

Meaning:

- current runtime state for one rendered panel

Allowed meanings:

- `has_data`
- `no_data`
- `not_exposed`

## Rule For Adding A New Family

When deciding whether a new family belongs in a dashboard baseline, ask only:

1. does this family belong to the class baseline?
2. if yes, which variant baseline includes it?
3. if included, is its owner `root` or `strategy`?

Do not ask:

- does target `A` currently have data?
- did the last push succeed?
- does one device expose the OID right now?

Those are runtime-state questions, not generation questions.

## Routing Example

This is why routing should be discussed as a class/variant problem, not a runtime gate problem.

The correct question is:

```text
Should a routing-capable switch baseline include routing families?
```

Not:

```text
Did one target currently collect route metrics, so can we generate routing panels?
```

If a future routing-capable switch baseline includes:

- `l3_route_table.*`
- `routing_bgp.*`
- `routing_ospf.*`

then those families should exist in that baseline even if:

- target A currently has no route data;
- target B does not expose BGP;
- target C has `not_exposed` state.

Those differences belong to `PanelState`, not `ClassBaseline`.

## What This Removes

This rule removes several wrong directions:

- no runtime data gate for baseline existence;
- no per-device dashboard structure;
- no forced code path where dashboard generation waits for push-time proof;
- no confusion between class design and target state.

## Immediate Consequence

Current switch closure can stay closed.

Future routing work should start by defining:

- whether there is a routing-capable switch class baseline;
- which variant baseline includes routing families;
- which routing families belong to `root` or `strategy`.

The next selection layer is now captured in:

- [2026-06-14-snmp-switch-baseline-selection-rule.md](/OneOPS/docs/superpowers/specs/2026-06-14-snmp-switch-baseline-selection-rule.md)

Only after that should runtime presentation decide whether panels show:

- data
- no data
- not exposed
