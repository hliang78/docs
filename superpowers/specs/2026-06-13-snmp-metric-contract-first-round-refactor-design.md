# SNMP Metric Contract First-Round Refactor Design

Date: 2026-06-13

## Goal

Refactor the current SNMP metric contract mechanism so it is easier to reason about and safer to evolve, without expanding metric scope, dashboard scope, or UI scope.

This round is about:

- boundary clarity,
- contract persistence clarity,
- fallback visibility,
- reducing repeated hardcoding,
- reducing silent default behavior.

This round is not about:

- adding new capability families,
- adding new dashboard generation behavior,
- expanding recording-rule features,
- redesigning the SNMP workspace.

## Current Problems

The existing implementation is already functionally meaningful, but the mechanism is difficult to trust because several concerns are mixed together:

1. explicit contract persistence shape is ambiguous;
2. frontend and backend both guess contract shape in different ways;
3. legacy import/export and semantic editing logic live in the same frontend file;
4. many defaults are silently applied instead of surfaced as issues;
5. current base capability metadata is repeated across importer, profile seeds, backend resolver, and default panel requirement logic.

The result is that the page often still “works”, but it is hard to tell whether it is operating in authority mode, fallback mode, degraded save mode, or compatibility-read mode.

## Fixed Decisions

These decisions are the design baseline for this refactor:

### 1. Canonical explicit contract shape

Explicit contract persistence uses one canonical envelope:

```json
{
  "metric_groups": {
    "version": 1,
    "metric_groups": []
  }
}
```

Legacy bare-array shape may still be read temporarily for compatibility, but it is no longer considered normal.

### 2. Compatibility reads must be visible

If the system reads a legacy explicit contract shape, malformed explicit contract shape, or degraded legacy import/export path, it must surface a structured issue instead of silently falling back.

### 3. Save mode is explicit

Saving must expose one of these modes:

- `full_sync`
- `contract_only`

`contract_only` is valid, but it is a degraded path and must include reasons.

### 4. Draft normalization is not persistence truth

UI draft normalization may still trim strings and stabilize empty arrays, but it must not silently invent persisted meaning for malformed contract data.

### 5. Backend authority remains preferred

The backend resolver remains the preferred authority for strategy-side contract answers. Frontend local resolution remains as a temporary fallback only, and that fallback state must be visible.

## Implemented Status So Far

As of 2026-06-13, a meaningful part of this design is already landed.

### Already landed

- explicit contract wire format is now canonically written as:
  - `metric_groups: { version: 1, metric_groups: [...] }`
- frontend and backend both compatibility-read legacy bare-array explicit contract shapes;
- compatibility reads and malformed explicit shapes now produce structured `issues`;
- backend strategy-level contract resolution now returns:
  - `contract_source`
  - `read_issues[]`
  - `effective_issues[]`
  - `save_mode_hint`
- frontend SNMP workspace now visibly distinguishes:
  - backend authority mode
  - frontend fallback mode
- frontend legacy raw import/export logic has been split into a dedicated legacy codec module;
- frontend strict validation has been split into a dedicated validation module;
- validation now distinguishes:
  - `errors`
  - `warnings`
  - `degradations`
- explicit-contract reads now warn when draft-only defaults are being inferred for missing semantic fields;
- explicit-contract writes no longer silently persist invented semantic defaults for missing `action`, `role`, `value_type`, `calculation`, or `visual_type`.

### Not landed yet

- capability catalog extraction is still incomplete;
- frontend inheritance logic is still not split into its own dedicated module;
- backend helper separation is improved, but not yet fully catalog-driven;
- shared cross-surface fixtures are still incomplete;
- `vue-tsc` / full `npm run typecheck` status remains unconfirmed because recent runs did not finish within the available waiting window.

## Target Structure

The first-round target structure is:

- wire codec:
  - explicit contract read/write
  - shape compatibility handling
- legacy codec:
  - `passthrough_config` parse/import/export
  - `metric_manifest` parse/import/export
- validation:
  - strict persistence validation
  - degradation detection
- inheritance:
  - parent/child effective-state logic
- capability catalog:
  - current base common capability definitions only

This applies most directly to the frontend, where one file currently owns almost all of these responsibilities. The backend should mirror the same separation at least at the helper/module level.

## Success Criteria

The refactor is successful when:

1. explicit contract write path always emits the canonical envelope;
2. compatibility reads return structured issues;
3. save mode distinguishes `full_sync` from `contract_only`;
4. the SNMP workspace clearly indicates backend-authority mode vs frontend-fallback mode;
5. current base common capability metadata is no longer manually duplicated in multiple primary paths;
6. frontend smoke and backend tests agree on current base-case contract outcomes.

## Intentional Deferrals

These are explicitly deferred to later rounds:

- broader vendor capability catalog cleanup beyond current repeated base common semantics;
- removal of all compatibility reads;
- migration of already-saved old explicit contract shapes;
- new Grafana or recording-rule behavior;
- wider UI redesign of the SNMP editor.
