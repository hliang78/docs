# OneOPS NetPath Snapshot Persistence And Selection Design

Date: 2026-06-22

## Purpose

This design defines the next NetPath production-readiness slice after durable analysis runs:

- make NetPath analysis snapshots into a OneOPS-owned durable object;
- separate snapshot persistence from analysis-run persistence;
- let analysis runs reference an explicit stored snapshot instead of relying on implicit latest-fact reads at execution time.

The goal is to move NetPath from:

```text
latest facts
  -> build transient snapshot
  -> analyze
  -> persist only run result
```

to:

```text
latest facts
  -> build durable snapshot
  -> persist snapshot
  -> analyze from persisted snapshot
  -> persist durable run
```

This creates a stable input boundary for rerun, compare, audit, and future UI closure.

## Current State

Current NetPath work already provides:

- a OneOPS-owned internal `AnalysisSnapshot` assembler and validator path;
- a build-tagged SDK runtime/provider path;
- durable `netpath_analysis_run` persistence for successful and failed runs;
- tenant-safe device-scope authorization at the service/runtime boundary.

Current gap:

- analysis input is still not durable;
- `CreateAnalyzeRun` still synthesizes a fake `preview-<tenant>` snapshot ID when callers omit `snapshot_id`;
- the SDK-backed provider still rebuilds from latest facts rather than loading a frozen stored snapshot;
- rerun/compare/audit behavior is weaker because run inputs are not frozen independently from run outputs.

Important design context:

- `docs/superpowers/specs/2026-06-19-oneops-netpath-snapshot-provider-design.md`
- `docs/superpowers/specs/2026-06-21-oneops-netpath-durable-run-design.md`
- `docs/superpowers/plans/2026-06-19-oneops-netpath-master-roadmap.md`

## Scope

In scope:

- add a durable OneOPS-owned `netpath_snapshot` record;
- persist OneOPS `AnalysisSnapshot` payload as `snapshot_json` plus summary fields;
- add `POST /netpath/snapshots`;
- add `GET /netpath/snapshots/:code`;
- let `CreateAnalyzeRun` load a persisted snapshot when `snapshot_id` is provided;
- let `CreateAnalyzeRun` create and persist a new snapshot first when `snapshot_id` is omitted;
- fail closed on `blocked` snapshots and persist a failed run;
- preserve tenant-safe snapshot lookup and snapshot creation scope.

Out of scope:

- snapshot child tables for devices/interfaces/routes/diagnostics;
- snapshot history diffing/version browsing;
- generic DC2 contract redesign;
- direct snapshot payload upload;
- source-run-driven snapshot build modes;
- frontend result pages or snapshot pages;
- async analysis execution;
- probe/ticket workflow changes.

## Confirmed Product Decisions

This design fixes the following decisions for this phase:

1. `CreateAnalyzeRun` without `snapshot_id` builds a real snapshot from latest facts, persists it, then analyzes from that stored snapshot.
2. Snapshot persistence uses one main table with `snapshot_json` plus a small number of structured summary/provenance fields.
3. OneOPS exposes an explicit `POST /netpath/snapshots` API.
4. `GET /netpath/snapshots/:code` returns summary by default, with an explicit debug view to expose full payload when needed.
5. `blocked` snapshots are fail-closed: they may be persisted, but they cannot be analyzed. If used for analysis, the service persists a failed run and returns error.
6. `POST /netpath/snapshots` only supports `tenant_code + device_codes + optional ingress_device_code/ingress_vrf`, and always builds from latest facts.

## Recommended Approach

Introduce a durable snapshot layer between latest-fact reading and engine execution.

Recommended main flows:

```text
POST /netpath/snapshots
  -> normalize request
  -> authorize tenant-safe device scope
  -> read latest facts
  -> assemble AnalysisSnapshot
  -> validate quality
  -> persist netpath_snapshot
  -> return snapshot summary

POST /netpath/analysis-runs
  -> if snapshot_id provided:
       load persisted snapshot
     else:
       create and persist new snapshot first
  -> if snapshot quality is blocked:
       persist failed run
       return fail-closed error
  -> map stored snapshot to engine snapshot
  -> execute analysis
  -> persist durable run
  -> return run response
```

This keeps OneOPS in control of:

- snapshot creation;
- snapshot quality;
- snapshot persistence;
- run persistence.

The engine remains responsible only for deterministic analysis over a provided snapshot.

## Why This Approach

### Why not keep transient snapshots

Durable runs without durable inputs only solve half the problem. Operators can see a stored result, but they cannot reliably prove which exact input snapshot produced it.

### Why not require callers to create snapshots first

That would force all current callers to adopt a two-step workflow immediately. This phase should support both:

- explicit snapshot-first use through `POST /netpath/snapshots`;
- compatible `CreateAnalyzeRun` behavior that auto-creates a stored snapshot when needed.

### Why not model snapshot internals in child tables now

That would expand this phase from “freeze the input boundary” into “fully relationalize NetPath snapshot internals”. The current highest-value outcome is freezing and reusing the whole snapshot object with enough structured metadata for filtering and audit.

## Snapshot Data Model

This phase should add one new OneOPS-owned model, for example:

```text
NetPathSnapshot
```

Recommended fields:

### Identity and tenancy

- `id`
- `code`
- `tenant_code`
- `created_at`
- `updated_at`

### Request scope

- `device_codes_json`
- `ingress_device_code`
- `ingress_vrf`

These fields describe the scope used to assemble the snapshot.

### Quality and summary

- `quality`
  - values: `ready`, `degraded`, `blocked`
- `summary`
- `diagnostics_json`

### Source context

- `source_run_ids_json`

This is the minimum structured provenance that should be separately queryable in this phase. More detailed fact-level provenance may remain inside `snapshot_json`.

### Full payload

- `snapshot_json`

This stores the full OneOPS-owned internal `AnalysisSnapshot`, not the SDK type.

## API Contract

This phase should add two HTTP APIs:

```text
POST /netpath/snapshots
GET  /netpath/snapshots/:code
```

### Create snapshot request

Recommended request shape:

```json
{
  "tenant_code": "tenant-a",
  "device_codes": ["r1", "r2"],
  "ingress_device_code": "r1",
  "ingress_vrf": "default"
}
```

Rules:

- `tenant_code` is required;
- `device_codes` must be explicit and tenant-authorized;
- `ingress_device_code` and `ingress_vrf` are optional for snapshot creation, but they improve quality validation and later analysis selection;
- no direct payload upload in this phase.

### Snapshot response

Default response should be summary-oriented:

```json
{
  "code": "nps-...",
  "tenant_code": "tenant-a",
  "quality": "degraded",
  "summary": "2 devices | route ready | policy partial",
  "device_codes": ["r1", "r2"],
  "ingress_device_code": "r1",
  "ingress_vrf": "default",
  "source_run_ids": ["collect-1", "fact-2"],
  "diagnostics": [],
  "created_at": 1760000000,
  "updated_at": 1760000000
}
```

`GET /netpath/snapshots/:code` should return the same summary view by default.

Recommended debug contract:

```text
GET /netpath/snapshots/:code?view=debug
```

When `view=debug`, include the parsed full `snapshot_json` payload in addition to the summary fields.

## Snapshot Creation Flow

Recommended `POST /netpath/snapshots` flow:

1. normalize request input;
2. authorize tenant-safe device scope;
3. read latest facts for the requested device scope;
4. assemble internal `AnalysisSnapshot`;
5. validate quality with current assembler/validator rules;
6. persist the snapshot regardless of whether quality is `ready`, `degraded`, or `blocked`;
7. return snapshot summary.

Why persist `blocked` snapshots:

- they are still useful audit artifacts;
- they let operators inspect why input assembly failed;
- they preserve a clear object boundary between “input snapshot creation” and “analysis execution”.

## Analysis Run Flow

Recommended `CreateAnalyzeRun` behavior:

### Case 1: caller provides `snapshot_id`

1. lookup `netpath_snapshot` by `tenant_code + snapshot_id`;
2. reject if not found;
3. if `quality=blocked`, persist failed run and return fail-closed error;
4. map stored snapshot to engine snapshot;
5. run analysis;
6. persist durable run referencing the snapshot.

### Case 2: caller omits `snapshot_id`

1. normalize and authorize the analysis request;
2. create and persist a fresh snapshot through the same snapshot-create path;
3. if the new snapshot is `blocked`, persist failed run and return fail-closed error;
4. analyze from the newly stored snapshot;
5. persist durable run referencing that snapshot.

This removes the old fake `preview-<tenant>` analysis snapshot behavior.

## Provider And Runtime Boundary

The build-tagged SDK provider should stop behaving like the primary business entry point for latest-fact assembly.

Current provider behavior is effectively:

```text
authorize
  -> read latest facts
  -> assemble snapshot
  -> validate
  -> map to SDK snapshot
```

Recommended provider/runtime behavior after this phase:

```text
authorize
  -> resolve snapshot selection
  -> if snapshot_id exists:
       load stored snapshot
     else:
       ask snapshot service to create/store one
  -> if quality is blocked:
       return blocked error
  -> map stored OneOPS snapshot to SDK snapshot
```

This keeps responsibilities cleaner:

- snapshot service owns latest-fact assembly and snapshot persistence;
- provider/runtime owns loading a selected snapshot and mapping it to the SDK type;
- engine owns deterministic path analysis only.

## Quality Gate Semantics

This phase fixes the following quality behavior:

### `ready`

- snapshot may be analyzed;
- snapshot may be reused freely;
- diagnostics may still exist, but no blocking condition is present.

### `degraded`

- snapshot may be analyzed;
- diagnostics must be preserved on both snapshot and run surfaces where relevant;
- result consumers should be able to explain that the analysis was performed on degraded input.

### `blocked`

- snapshot may be persisted;
- snapshot may be fetched and inspected;
- snapshot may not be analyzed;
- `CreateAnalyzeRun` using a blocked snapshot must persist a failed run and return error.

This keeps NetPath fail-closed for known-bad inputs.

## Error Handling

### Validation and authorization failure

Examples:

- missing `tenant_code`;
- empty `device_codes`;
- unauthorized device scope.

These return directly and do not create snapshot or run records.

### Snapshot build failure before persistence

Examples:

- latest-fact read error;
- assembler hard failure;
- serialization failure.

These return error and do not create a snapshot record. If the request path is `CreateAnalyzeRun`, persist a failed run only after the flow has crossed into actual analysis-attempt territory and there is enough normalized request context to store meaningfully.

### Blocked snapshot used for analysis

Persist failed run with:

- `status=failed`;
- `snapshot_id=<blocked snapshot>`;
- durable request fields;
- error explaining blocked snapshot quality.

### Analysis failure

Persist failed run referencing the stored snapshot.

### Snapshot persistence failure

Return failure. Snapshot durability is part of the contract in this phase, not best-effort side behavior.

## Testing Strategy

This phase should use three verification layers.

### 1. Schema and migration tests

Targets:

- `initialize`
- snapshot model AutoMigrate coverage
- companion migration static-compatibility coverage

Focus:

- `netpath_snapshot` columns and indexes exist;
- companion migration stays within the chosen SQL compatibility boundary;
- run and snapshot schema remain aligned.

### 2. Service tests

Targets:

- snapshot create/get behavior;
- run create/get behavior with stored snapshots;
- blocked snapshot fail-closed behavior;
- latest facts change does not affect analysis when the same stored snapshot is reused.

Focus:

- ready snapshot can be created and retrieved;
- degraded snapshot persists diagnostics;
- blocked snapshot persists but analysis fails closed;
- omitted `snapshot_id` creates a fresh stored snapshot first;
- provided `snapshot_id` reuses stored snapshot instead of rebuilding from latest facts.

### 3. API tests

Targets:

- `POST /netpath/snapshots`
- `GET /netpath/snapshots/:code`
- `CreateAnalyzeRun` with and without `snapshot_id`

Focus:

- HTTP contract shape;
- tenant-safe lookup behavior;
- summary vs debug view behavior;
- no regression to durable run API behavior.

## Recommended Delivery Slices

Implement this phase in four slices.

### Slice A: Snapshot persistence skeleton

- add `netpath_snapshot` model;
- add migration and AutoMigrate coverage;
- add snapshot DTO/service/API skeleton for create/get;
- persist `snapshot_json` plus summary fields.

### Slice B: Latest-fact-backed snapshot creation

- connect snapshot create service to existing assembler/validator;
- persist `ready`, `degraded`, and `blocked` snapshots from latest facts;
- preserve diagnostics and source run IDs.

### Slice C: Snapshot-first analysis runs

- make `CreateAnalyzeRun` load by `snapshot_id` when provided;
- auto-create/persist snapshot when omitted;
- fail closed on blocked snapshots and persist failed runs.

### Slice D: Runtime/provider cleanup

- make provider/runtime prefer stored snapshot loading;
- keep provider focused on snapshot selection + SDK mapping rather than primary latest-fact assembly.

## Acceptance Criteria

- NetPath can persist and fetch a durable snapshot object owned by OneOPS.
- `POST /netpath/snapshots` builds from latest facts with tenant-safe device scope.
- `CreateAnalyzeRun` without `snapshot_id` no longer depends on fake preview snapshot IDs.
- `CreateAnalyzeRun` with `snapshot_id` analyzes from stored snapshot rather than rebuilding from latest facts.
- `blocked` snapshots are persisted but fail closed for analysis.
- Durable runs continue to persist and reference snapshot identity.
- Default snapshot fetch returns summary; debug fetch can expose full payload.

## Main Risks

- Snapshot payload size may grow, so summary fields must remain useful enough for normal lookup without parsing `snapshot_json`.
- A static migration compatibility check is weaker than a real MySQL migration parity test.
- Large-table release operations for snapshot/run schema still need release-window discipline.
- The exact future contract for richer source provenance is deferred; this phase should avoid over-committing to a fact-level relational model.
