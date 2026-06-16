# SNMP Metric Contract First-Round Refactor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the current SNMP metric contract mechanism smoother and safer by removing format ambiguity, reducing scattered hardcoding, and surfacing silent fallback behavior without expanding supported metric domains or adding new dashboard capabilities.

**Architecture:** Treat this round as a boundary-hardening refactor, not a feature build. First lock one canonical explicit-contract wire format and a visible compatibility layer. Then split the current monolithic frontend contract helper into smaller units for wire codec, legacy import/export, validation, inheritance, and capability catalog logic. Finally, expose issue/degradation metadata explicitly in both frontend and backend so the workspace no longer relies on hidden defaults.

**Tech Stack:** TypeScript/Vue frontend under `/OneOPS/OneOps-UI`, Go backend under `/OneOPS/OneOps`, existing smoke tests, focused Go tests, `vue-tsc`, and repository docs under `/OneOPS/docs/superpowers`.

---

## Scope Lock

This refactor is intentionally narrow.

Allowed:

- unify explicit SNMP metric contract persistence shape;
- split oversized contract helper logic into focused modules;
- replace silent defaulting with surfaced validation/import/export issues;
- reduce duplicated hardcoding by extracting contract/capability catalogs and shared fixtures inside each runtime;
- add tests that prove frontend and backend stay aligned on current supported semantics.

Not allowed in this round:

- no new metric groups or capability families;
- no Grafana JSON generation changes;
- no Prometheus recording-rule feature expansion;
- no new dashboard layout work;
- no broad UI redesign;
- no database schema changes;
- no child-strategy migration beyond compatibility reads of already-saved data.

## Refactor Outcome

By the end of this round, the codebase should have these properties:

1. `parameters.metric_groups` has one documented canonical persisted shape.
2. Any compatibility read of old shapes is explicit and observable.
3. “Cannot export legacy passthrough config” is a first-class save mode, not a quiet fallback.
4. UI normalization is limited to draft/editing concerns, not persistence truth.
5. Frontend and backend both resolve the same current base capability set from reproducible fixtures.

## File Structure

Frontend files expected to change:

- Modify: `/OneOPS/OneOps-UI/src/typings/platform/snmp-metric-contract.ts`
- Modify: `/OneOPS/OneOps-UI/src/views/platform/StrategyTemplate/plugin-forms/PluginFormSnmp.vue`
- Modify: `/OneOPS/OneOps-UI/src/views/platform/StrategyTemplate/index.vue`
- Create: `/OneOPS/OneOps-UI/src/views/platform/StrategyTemplate/plugin-forms/snmp/snmpMetricContractWire.ts`
- Create: `/OneOPS/OneOps-UI/src/views/platform/StrategyTemplate/plugin-forms/snmp/snmpMetricLegacyCodec.ts`
- Create: `/OneOPS/OneOps-UI/src/views/platform/StrategyTemplate/plugin-forms/snmp/snmpMetricValidation.ts`
- Create: `/OneOPS/OneOps-UI/src/views/platform/StrategyTemplate/plugin-forms/snmp/snmpMetricInheritance.ts`
- Create: `/OneOPS/OneOps-UI/src/views/platform/StrategyTemplate/plugin-forms/snmp/snmpMetricCapabilityCatalog.ts`
- Modify: `/OneOPS/OneOps-UI/src/views/platform/StrategyTemplate/plugin-forms/snmp/snmpMetricContract.ts`
- Modify: `/OneOPS/OneOps-UI/scripts/snmp-metric-contract-smoke.ts`
- Create: `/OneOPS/OneOps-UI/scripts/snmp-metric-contract-wire-smoke.ts`

Backend files expected to change:

- Modify: `/OneOPS/OneOps/app/platform/dto/snmp_metric_contract.go`
- Modify: `/OneOPS/OneOps/app/platform/service/i_metric_capability_contract_resolver.go`
- Modify: `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver.go`
- Create: `/OneOPS/OneOps/app/platform/service/impl/snmp_metric_contract_wire.go`
- Create: `/OneOPS/OneOps/app/platform/service/impl/snmp_metric_contract_catalog.go`
- Modify: `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver_test.go`

Docs expected to change:

- Modify: `/OneOPS/docs/superpowers/handovers/2026-06-10-snmp-metric-groups-dashboard-family-handoff.md`
- Create: `/OneOPS/docs/superpowers/specs/2026-06-13-snmp-metric-contract-first-round-refactor-design.md`

## Canonical Decisions

These decisions are fixed for this plan:

- Canonical explicit contract persistence format is envelope:
  - `metric_groups: { version: 1, metric_groups: [...] }`
- Frontend may compatibility-read bare array shape during migration, but must record an issue.
- Backend may compatibility-read bare array shape during migration, but must record an issue.
- Frontend workspace editing continues to edit explicit contract only.
- Legacy `passthrough_config` and `metric_manifest` import/export remain supported, but only through dedicated codec helpers.
- `normalize*` functions are not allowed to invent persisted meaning silently; they may only normalize UI draft data and trim obvious string noise.

## Task 1: Freeze The Current Boundary With Tests

**Files:**

- Modify: `/OneOPS/OneOps-UI/scripts/snmp-metric-contract-smoke.ts`
- Create: `/OneOPS/OneOps-UI/scripts/snmp-metric-contract-wire-smoke.ts`
- Modify: `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver_test.go`

- [ ] **Step 1: Add a frontend smoke for explicit contract shapes**

Add coverage for:

- canonical envelope input;
- legacy bare-array input;
- malformed input;
- write path output shape.

Required assertions:

```text
readSnmpContract({ metric_groups: { version: 1, metric_groups: [...] } }) -> 1 group
readSnmpContract({ metric_groups: [...] }) -> compatibility-read succeeds with issue
writeSnmpContract(...) -> always writes envelope
```

- [ ] **Step 2: Add a backend test for explicit contract shapes**

Add focused tests for:

- `metric_groups` stored as envelope;
- `metric_groups` stored as bare array;
- empty envelope;
- malformed envelope.

Expected behavior:

```text
canonical envelope -> explicit contract, no shape issue
bare array -> explicit contract, compatibility issue
empty/malformed -> no explicit contract, structured issue
```

- [ ] **Step 3: Run the tests and capture baseline failures**

Run:

```bash
cd /OneOPS/OneOps-UI
npm run smoke:snmp-metric-contract
npm run smoke:snmp-metric-contract-wire
```

Run:

```bash
cd /OneOPS/OneOps
go test ./app/platform/service/impl -run 'TestMetricCapabilityContractResolver|TestReadExplicitSnmpMetricContract' -count=1
```

Expected: RED until the canonical wire codec exists.

## Task 2: Introduce Canonical Wire Codec And Compatibility Issues

**Files:**

- Create: `/OneOPS/OneOps-UI/src/views/platform/StrategyTemplate/plugin-forms/snmp/snmpMetricContractWire.ts`
- Modify: `/OneOPS/OneOps-UI/src/typings/platform/snmp-metric-contract.ts`
- Modify: `/OneOPS/OneOps-UI/src/views/platform/StrategyTemplate/plugin-forms/snmp/snmpMetricContract.ts`
- Create: `/OneOPS/OneOps/app/platform/service/impl/snmp_metric_contract_wire.go`
- Modify: `/OneOPS/OneOps/app/platform/dto/snmp_metric_contract.go`
- Modify: `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver.go`

- [ ] **Step 1: Add typed issue/result envelopes**

Add frontend and backend types for:

```text
SnmpMetricContractIssue
  code
  level
  message
  path

SnmpMetricContractReadResult
  contract
  source
  issues
  format
```

`format` must distinguish:

```text
canonical_envelope
legacy_bare_array
none
invalid
```

- [ ] **Step 2: Move explicit contract reading/writing into dedicated wire helpers**

Frontend wire helper responsibilities:

- read canonical envelope;
- compatibility-read bare array;
- return issues instead of silently returning empty contract;
- write canonical envelope only.

Backend wire helper responsibilities:

- same read compatibility contract behavior;
- no direct JSON guessing inside the resolver body.

- [ ] **Step 3: Replace direct `readSnmpContract` and raw `metric_groups` injection sites**

Update:

- `/OneOPS/OneOps-UI/src/views/platform/StrategyTemplate/index.vue`
- `/OneOPS/OneOps-UI/src/views/platform/StrategyTemplate/plugin-forms/PluginFormSnmp.vue`
- `/OneOPS/OneOps-UI/src/views/platform/StrategyTemplate/plugin-forms/snmp/snmpMetricContract.ts`

Required behavior:

```text
backend merge path must inject canonical envelope, not bare array
workspace load must preserve read issues
save path must always persist canonical envelope
```

- [ ] **Step 4: Re-run focused tests**

Run:

```bash
cd /OneOPS/OneOps-UI
npm run smoke:snmp-metric-contract
npm run smoke:snmp-metric-contract-wire
```

Run:

```bash
cd /OneOPS/OneOps
go test ./app/platform/service/impl -run 'TestMetricCapabilityContractResolver|TestReadExplicitSnmpMetricContract' -count=1
```

Expected: GREEN.

## Task 3: Split Legacy Codec From Contract Editing Logic

**Files:**

- Create: `/OneOPS/OneOps-UI/src/views/platform/StrategyTemplate/plugin-forms/snmp/snmpMetricLegacyCodec.ts`
- Modify: `/OneOPS/OneOps-UI/src/views/platform/StrategyTemplate/plugin-forms/snmp/snmpMetricContract.ts`
- Modify: `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver.go`

- [ ] **Step 1: Move legacy import/export helpers into a separate frontend codec**

Move these concerns out of the current monolith:

- TOML parsing;
- metric manifest parsing;
- passthrough import;
- passthrough export;
- exportability check.

Keep `snmpMetricContract.ts` as a shallow facade while callers are migrated.

- [ ] **Step 2: Surface codec degradations explicitly**

Replace “cannot export” boolean-only logic with:

```text
save_mode = full_sync | contract_only
issues[] describing why
```

Minimum surfaced reasons:

- missing field OID;
- synthetic field without raw source;
- panel-only semantic metric with no raw export path;
- malformed imported legacy shape.

- [ ] **Step 3: Mirror backend legacy import logic into named sections/helpers**

Backend resolver must separate:

- explicit contract read;
- legacy passthrough parse;
- legacy import to semantic groups;
- disabled-group filtering.

Do not leave all four concerns interleaved inside one resolver function.

- [ ] **Step 4: Add smoke coverage for save mode**

Add assertions proving:

```text
exportable contract -> full_sync
missing OID contract -> contract_only with issue
```

Run:

```bash
cd /OneOPS/OneOps-UI
npm run smoke:snmp-metric-contract
```

Expected: GREEN.

## Task 4: Limit Silent Defaults To Draft-Time Only

**Files:**

- Create: `/OneOPS/OneOps-UI/src/views/platform/StrategyTemplate/plugin-forms/snmp/snmpMetricValidation.ts`
- Modify: `/OneOPS/OneOps-UI/src/views/platform/StrategyTemplate/plugin-forms/snmp/snmpMetricContract.ts`
- Modify: `/OneOPS/OneOps-UI/src/views/platform/StrategyTemplate/plugin-forms/PluginFormSnmp.vue`

- [ ] **Step 1: Split `normalize` and `validate` responsibilities**

Keep draft-only normalization for:

- trim strings;
- default unchecked `enabled` to `true` in editor state;
- keep empty arrays stable for the UI.

Move persistence rules into strict validation:

- `group_key` required;
- `action` required;
- `metric_key` required;
- panel metric references must exist;
- explicit contract persistence shape must be canonical.

- [ ] **Step 2: Add strict validation result with levels**

Add:

```text
errors[]
warnings[]
degradations[]
```

Examples:

- warning: compatibility-read of bare-array explicit contract;
- degradation: save will be `contract_only`;
- error: duplicated `group_key`;
- error: panel references missing metric.

- [ ] **Step 3: Replace current warning-only UI messaging**

Update the SNMP form side panel so it can distinguish:

- contract valid;
- contract valid but degraded;
- contract invalid.

Do not add new layout sections. Reuse current alert area.

- [ ] **Step 4: Run checks**

Run:

```bash
cd /OneOPS/OneOps-UI
npm run smoke:snmp-metric-contract
npm run typecheck
```

Expected: GREEN.

## Task 5: Extract Capability Catalog From Scattered Hardcoding

**Files:**

- Create: `/OneOPS/OneOps-UI/src/views/platform/StrategyTemplate/plugin-forms/snmp/snmpMetricCapabilityCatalog.ts`
- Create: `/OneOPS/OneOps/app/platform/service/impl/snmp_metric_contract_catalog.go`
- Modify: `/OneOPS/OneOps-UI/src/views/platform/StrategyTemplate/plugin-forms/snmp/snmpMetricContract.ts`
- Modify: `/OneOPS/OneOps-UI/src/views/platform/StrategyTemplate/plugin-forms/snmp/snmpMibProfiles.ts`
- Modify: `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver.go`

- [ ] **Step 1: Extract current base capability definitions**

Catalog entries in this round must include only the already-supported base semantics:

- `system_basic`
- `interface_basic`
- current default panel capability requirements already in scope

Each catalog entry should centralize:

- raw field aliases;
- output `metric_key`;
- `concept_key`;
- `capability_key`;
- transform type;
- default unit;
- default recording-rule metadata;
- default panel membership when relevant.

- [ ] **Step 2: Refactor frontend importer/profile seed generation to consume the catalog**

Do not leave separate hand-written copies of:

- `if_in_rate`
- `if_out_rate`
- `if_oper_status`
- `if_speed_bps`
- CPU/memory capability metadata

inside both the importer and profile seed file.

- [ ] **Step 3: Refactor backend resolver/default requirement generation to consume the catalog**

Backend should stop manually re-stating the same base capability metadata in multiple branches where a catalog lookup is enough.

- [ ] **Step 4: Keep out-of-scope capability families untouched**

Do not try to catalog every Huawei/L2/L3/provider-specific branch in this round. Only touch the currently repeated base common semantics.

- [ ] **Step 5: Run focused tests**

Run:

```bash
cd /OneOPS/OneOps-UI
npm run smoke:snmp-metric-contract
npm run smoke:snmp-profile-resolution
```

Run:

```bash
cd /OneOPS/OneOps
go test ./app/platform/service/impl -run TestMetricCapabilityContractResolver -count=1
```

Expected: GREEN.

## Task 6: Make Backend Authority Explicit And Frontend Fallback Visible

**Files:**

- Modify: `/OneOPS/OneOps/app/platform/dto/snmp_metric_contract.go`
- Modify: `/OneOPS/OneOps/app/platform/service/i_metric_capability_contract_resolver.go`
- Modify: `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver.go`
- Modify: `/OneOPS/OneOps-UI/src/typings/platform/snmp-metric-contract.ts`
- Modify: `/OneOPS/OneOps-UI/src/views/platform/StrategyTemplate/index.vue`
- Modify: `/OneOPS/OneOps-UI/src/views/platform/StrategyTemplate/plugin-forms/PluginFormSnmp.vue`

- [ ] **Step 1: Extend resolver response metadata**

Add response metadata fields for:

```text
contract_source
read_issues[]
effective_issues[]
save_mode_hint
```

`contract_source` examples:

```text
explicit_contract
legacy_import
backend_resolver
frontend_fallback
```

- [ ] **Step 2: Make frontend fallback a visible degraded mode**

Current backend request failure must no longer silently look identical to authority mode.

Required UI message:

```text
backend authority unavailable, currently using local compatibility resolver
```

- [ ] **Step 3: Keep fallback behavior, but stop treating it as normal**

Do not remove the local fallback in this round. Just make it explicit and degrade the source note accordingly.

- [ ] **Step 4: Run smoke/type checks**

Run:

```bash
cd /OneOPS/OneOps-UI
npm run smoke:snmp-workspace-view
npm run typecheck
```

Expected: GREEN.

## Task 7: Add Cross-Surface Consistency Fixtures

**Files:**

- Create: `/OneOPS/docs/superpowers/specs/2026-06-13-snmp-metric-contract-first-round-refactor-design.md`
- Modify: `/OneOPS/OneOps-UI/scripts/snmp-metric-contract-smoke.ts`
- Modify: `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver_test.go`

- [ ] **Step 1: Add repository fixtures for current base cases**

Define at least these fixture scenarios:

- interface-only passthrough;
- top-level CPU/memory passthrough;
- explicit canonical contract;
- explicit legacy bare-array contract;
- non-exportable custom semantic field.

- [ ] **Step 2: Make frontend smoke and backend tests both consume the same expected outcomes**

Shared expected outcomes must cover:

- effective group keys;
- save mode;
- explicit read format;
- surfaced issues;
- current base panel capability support for shared cases.

- [ ] **Step 3: Run full focused verification**

Run:

```bash
cd /OneOPS/OneOps-UI
npm run smoke:snmp-metric-contract
npm run smoke:snmp-metric-contract-wire
npm run smoke:snmp-profile-resolution
npm run smoke:snmp-workspace-view
npm run typecheck
```

Run:

```bash
cd /OneOPS/OneOps
go test ./app/platform/service/impl -run TestMetricCapabilityContractResolver -count=1
go test ./app/platform/api ./app/platform/service/impl -run 'TestMetricCapabilityContractResolver|^$' -count=1
```

Expected: GREEN.

## Task 8: Documentation And Handoff Refresh

**Files:**

- Modify: `/OneOPS/docs/superpowers/handovers/2026-06-10-snmp-metric-groups-dashboard-family-handoff.md`
- Create: `/OneOPS/docs/superpowers/specs/2026-06-13-snmp-metric-contract-first-round-refactor-design.md`

- [ ] **Step 1: Write the narrow design addendum**

Document:

- canonical wire format;
- save mode semantics;
- issue/degradation model;
- authority vs fallback source model;
- why this round stops before new capability expansion.

- [ ] **Step 2: Refresh the SNMP handoff doc**

Update the handoff to say:

- what first-round refactor fixed;
- which compatibility reads remain temporary;
- which second-round items are intentionally deferred.

- [ ] **Step 3: Final verification pass**

Run:

```bash
cd /OneOPS/OneOps-UI
npm run typecheck
```

Run:

```bash
cd /OneOPS/OneOps
go test ./app/platform/service/impl -run TestMetricCapabilityContractResolver -count=1
```

Expected: GREEN.

## Execution Notes

Recommended implementation order:

1. Task 1 and Task 2 first, because wire-format ambiguity is the biggest source of hidden behavior.
2. Task 3 and Task 4 second, because legacy codec and silent-default cleanup are tightly coupled.
3. Task 5 third, because catalog extraction is much safer after boundaries are fixed.
4. Task 6 and Task 7 last, because source visibility and cross-surface fixtures depend on the earlier refactor points settling down.

## Risks To Watch

- frontend and backend may currently rely on different `metric_groups` persistence shapes;
- backend default panel requirement tests are already drifting from current expectations, so do not trust old expected counts blindly;
- splitting `snmpMetricContract.ts` too aggressively in one commit could make review harder;
- compatibility-read removal is out of scope for this round, so do not prematurely delete migration paths.

## Done Definition

This plan is complete only when all of the following are true:

- canonical explicit contract persistence shape is enforced on write;
- compatibility reads emit issues instead of disappearing into defaults;
- save mode clearly distinguishes `full_sync` vs `contract_only`;
- `snmpMetricContract.ts` no longer owns wire, legacy, validation, inheritance, and catalog logic in one file;
- current supported base capabilities are cataloged instead of repeated ad hoc in multiple paths;
- frontend smoke and backend tests agree on the same current base-case outcomes.
