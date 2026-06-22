# OneOPS NetPath Durable Run Design

Date: 2026-06-21

## Purpose

This design defines the smallest production-safe persistence layer for OneOPS NetPath analysis runs.

The goal is not to turn NetPath into a full async task system yet. The goal is to upgrade the current in-memory analysis run flow into a durable backend capability:

```text
CreateAnalyzeRun
  -> analyze synchronously
  -> persist the run result
  -> return the full response

GetAnalyzeRun
  -> read the persisted run result
  -> return the same response shape
```

This phase should make analysis runs survive process restarts, preserve tenant-safe scope, and create a stable foundation for later result drilldown and UI closure.

## Current State

Existing NetPath work already provides:

- OneOPS NetPath service and API shape.
- An engine port and optional SDK-backed analysis path.
- A SnapshotProvider direction based on tenant-scoped latest facts.
- In-memory run storage for MVP behavior.
- User journey and acceptance documents for broader product scope.

Important existing design context:

- `docs/superpowers/specs/2026-06-18-netpath-engine-runner-design.md`
- `docs/superpowers/specs/2026-06-19-oneops-netpath-snapshot-provider-design.md`
- `docs/superpowers/specs/2026-06-19-oneops-netpath-user-journeys-acceptance-design.md`
- `docs/superpowers/plans/2026-06-19-oneops-netpath-master-roadmap.md`

Current gap:

- analysis results are not yet durably stored as a OneOPS-owned persistent run record;
- process restarts should not erase completed analysis history;
- run retrieval should not depend on in-memory state as the primary source of truth.

## Scope

In scope:

- keep `CreateAnalyzeRun` synchronous;
- persist successful and failed analysis runs;
- make `GetAnalyzeRun` read from durable storage;
- preserve tenant-safe run isolation;
- store enough structured fields for future filtering and audit;
- store the full mapped result JSON for response reconstruction.

Out of scope:

- async task execution;
- pending/running retry lifecycle;
- hop/step/trace child tables;
- frontend result page changes;
- evidence drilldown UI;
- full history/list/filter APIs;
- probe orchestration;
- ticket or workflow closure.

## Recommended Approach

Use a minimal OneOPS-owned run table as the first durable persistence layer.

Keep the current synchronous request behavior:

1. validate tenant and explicit device scope;
2. build or fetch an analysis snapshot;
3. execute the analysis engine synchronously;
4. map the engine result into the existing OneOPS response model;
5. persist a durable run record;
6. return the full response.

`GetAnalyzeRun` should then:

1. validate tenant scope;
2. read the durable run record from the database;
3. deserialize the stored result payload;
4. return the current API response shape.

This keeps the current user-facing behavior stable while making the backend durable.

## Why This Approach

### Why not stay in memory

In-memory runs are acceptable for preview-stage development, but they do not meet the minimum standard for a platform capability. Operators need analysis results to survive process restarts and remain queryable by tenant-safe run ID.

### Why not switch to async now

Async execution is a valid later direction, but it would expand the scope into lifecycle states, queueing, timeout recovery, retries, and UI polling. That is larger than the current need.

### Why not split hops and steps now

The first durable phase should optimize for low risk and a stable contract. A structured run summary plus full `result_json` is enough to support `create -> persist -> get` without forcing an early schema commitment for trace internals.

## Durable Run Data Model

This phase should add one main persistent record owned by OneOPS, for example:

```text
NetPathAnalyzeRunRecord
```

Recommended field groups:

### Identity and tenancy

- `id`
- `tenant_code`
- `created_at`
- `updated_at`

### Request input

- `src_ip`
- `dst_ip`
- `src_device_code`
- `dst_device_code`
- `protocol`
- `dst_port`
- `vrf`
- `device_codes_json`

These fields preserve the original analysis scope and make future filtering possible without parsing the full payload.

### Snapshot and source context

- `snapshot_id`
- `snapshot_quality`
- `source_run_ids_json`

This phase does not need full provenance tables, but it should at least preserve which snapshot and source runs the analysis depended on.

### Result summary

- `status`
- `disposition`
- `summary`
- `diagnostics_json`
- `error_message`

Minimum status values:

- `completed`
- `failed`

This is enough for the synchronous durable phase and leaves room for future `pending` or `running` states.

### Full mapped result

- `result_json`

This stores the OneOPS-mapped response payload, not the engine's internal object graph.

`GetAnalyzeRun` should rebuild the response from this payload so DB becomes the primary source of truth.

## Service Boundary

The persistence boundary should remain in OneOPS NetPath service code.

Recommended separation:

- SnapshotProvider builds or retrieves analysis snapshot data.
- Engine executes deterministic path analysis.
- Service maps the result into OneOPS DTOs and persists the durable run record.
- Database stores OneOPS-owned run view data.

The engine should not know about database persistence.

The snapshot provider should not own run persistence.

This preserves a clean boundary:

```text
provider builds snapshot
  -> engine analyzes
  -> service maps and persists
  -> API returns durable run result
```

## Create Flow

Recommended `CreateAnalyzeRun` flow:

1. validate request input;
2. resolve and authorize tenant-safe device scope;
3. build or fetch the analysis snapshot;
4. execute the engine synchronously;
5. map the engine result into the existing OneOPS run/result DTO;
6. persist a `completed` run record with summary fields and `result_json`;
7. return the mapped response.

If snapshot or engine execution fails:

1. capture the failure as a OneOPS run result boundary error;
2. persist a `failed` run record once request validation and tenant authorization have passed and snapshot assembly has started;
3. return the failure to the caller.

If persistence itself fails, the API should return failure rather than silently succeed. In this phase, durable storage is part of the contract, not best-effort side behavior.

## Get Flow

Recommended `GetAnalyzeRun` flow:

1. require tenant-safe lookup inputs;
2. read by `tenant_code + run_id`;
3. reconstruct the current API response from `result_json` and summary fields;
4. return not found when no durable record exists in the tenant scope.

This phase should not keep an in-memory fallback as the normal read path:

- database is the primary source;
- memory is not the durable source of truth;
- missing durable records should fail explicitly rather than silently reading stale process-local state.

## Error Handling

Use a narrow failure model in this phase.

### Input or scope validation failure

Examples:

- invalid input IPs;
- missing required request fields;
- unauthorized `device_codes` scope.

These may return directly without a persisted run if the request never entered real analysis execution. This keeps the phase small.

### Snapshot build failure

Examples:

- blocked snapshot quality;
- missing critical route or topology data;
- tenant-scoped snapshot assembly error.

These should persist a `failed` run record when practical, because they represent a real analysis attempt that operators may need to inspect later.
These should persist a `failed` run record because they represent a real analysis attempt that operators may need to inspect later.

### Engine or result mapping failure

Persist:

- `status=failed`
- `error_message`

This keeps failed analysis visible rather than disappearing into logs.

### Persistence failure

If analysis succeeded but saving the durable run fails, the API should return failure.

This phase is explicitly about durable runs. Returning a successful analysis without persistence would violate the purpose of the change.

## Testing

Minimum tests should cover:

1. successful create persists a completed run record;
2. `GetAnalyzeRun` reads from DB and reconstructs the current response;
3. tenant A cannot read tenant B's run;
4. snapshot or engine failure persists a failed run record with message;
5. persistence failure returns API failure rather than fake success.

The first phase does not need list/history coverage or child-table trace reconstruction tests.

## Acceptance Criteria

This phase is complete when:

1. `CreateAnalyzeRun` still returns a synchronous result.
2. successful analysis runs are durably persisted.
3. failed analysis runs are durably persisted for real execution-path failures.
4. `GetAnalyzeRun` reads durable storage as the primary source.
5. run retrieval is tenant-safe.
6. process restart does not erase persisted analysis results.

## Follow-On Work

This design intentionally sets up, but does not implement:

- list/history/filter APIs;
- richer run status lifecycle;
- hop/step/diagnostic child tables;
- evidence drilldown DTOs;
- frontend result workflow;
- async execution and retry semantics.

Those should be handled as later focused phases after the minimal durable run contract is stable.
