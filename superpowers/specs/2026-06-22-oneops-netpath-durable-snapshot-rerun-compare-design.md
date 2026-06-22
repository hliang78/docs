# OneOPS NetPath Durable Snapshot Rerun And Compare Design

Date: 2026-06-22

## Purpose

This design defines the next NetPath slice after durable run persistence and snapshot persistence:

- make `rerun` explicitly target a stored durable snapshot;
- make run-to-run `compare` depend on durable snapshot context instead of only run payloads;
- add snapshot-to-snapshot compare as a first-class durable-input workflow.

The goal is to move NetPath from:

```text
baseline run
  -> rerun with another snapshot_id
  -> compare only run results
```

to:

```text
baseline run
  -> rerun against a required durable snapshot
  -> compare run deltas with durable snapshot context

durable snapshot A
  -> compare durable snapshot B
  -> inspect input-version delta without requiring runs first
```

This keeps durable snapshots as the frozen input boundary for rerun, audit, and later UI diff workflows.

## Current State

Current NetPath work already provides:

- durable `netpath_analysis_run` persistence;
- durable `netpath_snapshot` persistence;
- snapshot-first `CreateAnalyzeRun`;
- `RerunAnalyzeRun` that reuses a baseline run request and substitutes `snapshot_id`;
- `CompareAnalyzeRuns` that compares two stored run results and returns run-level deltas.

Current gap:

- `rerun` semantics are not yet stated as strictly durable-snapshot-only;
- run compare exposes `baseline_snapshot_id` and `target_snapshot_id`, but it does not require loading durable snapshot summaries as part of the response contract;
- there is no snapshot-first compare entrypoint for comparing two frozen inputs without first creating two runs;
- legacy or non-durable snapshot references need fail-closed behavior rather than implicit compatibility.

Important design context:

- `docs/superpowers/specs/2026-06-21-oneops-netpath-durable-run-design.md`
- `docs/superpowers/specs/2026-06-22-oneops-netpath-snapshot-persistence-and-selection-design.md`

## Scope

In scope:

- tighten `POST /netpath/analysis-runs/:code/rerun` so the target `snapshot_id` must resolve to a durable stored snapshot;
- tighten `GET /netpath/analysis-runs/:code/compare` so both runs must resolve to durable stored snapshots;
- extend run compare responses to include snapshot summary context for baseline and target runs;
- add `GET /netpath/snapshots/compare`;
- compare durable snapshot metadata including quality, scope, diagnostics, and source-run provenance;
- fail closed when rerun/compare encounter preview or non-durable snapshot references.

Out of scope:

- relational snapshot child-table diffing;
- automatic “reanalyze both snapshots then diff hops” behavior for snapshot compare;
- historical backfill or migration repair for legacy preview runs;
- UI pages for snapshot compare;
- generic run history redesign.

## Confirmed Product Decisions

This design fixes the following decisions for this phase:

1. `RerunAnalyzeRun` must load the requested target durable snapshot before analysis. It must not fall back to latest-fact rebuild.
2. `CompareAnalyzeRuns` remains a run-to-run API, but it now explicitly loads and returns durable snapshot context for both runs.
3. `CompareSnapshots` is added as a separate snapshot-first API and does not require existing runs.
4. `CompareSnapshots` compares frozen input metadata only in this phase. It does not synthesize hop deltas by re-running analysis.
5. If a run references `preview-*` or another non-durable snapshot identifier, rerun/compare fail closed with a clear error instead of silently degrading.
6. `blocked` snapshots are allowed in snapshot compare, but they are rejected as rerun targets.

## Recommended Approach

Use a two-layer compare model:

- keep run compare for outcome deltas;
- add snapshot compare for frozen-input deltas.

Recommended flows:

```text
POST /netpath/analysis-runs/:code/rerun
  -> load baseline run
  -> load target durable snapshot
  -> reject if target snapshot is blocked
  -> reuse baseline request flow
  -> replace snapshot_id with target snapshot code
  -> create new analyze run
  -> return rerun response plus compare link

GET /netpath/analysis-runs/:code/compare
  -> load baseline run
  -> load target run
  -> load baseline durable snapshot
  -> load target durable snapshot
  -> compute run deltas
  -> attach baseline/target snapshot summary context
  -> return combined compare response

GET /netpath/snapshots/compare
  -> load baseline durable snapshot
  -> load target durable snapshot
  -> diff snapshot quality, scope, diagnostics, and provenance
  -> return snapshot compare response
```

This preserves current run-level workflows while making durable snapshots the required source of truth behind them.

## Why This Approach

### Why not replace run compare with snapshot compare only

Run compare and snapshot compare answer different questions:

- run compare explains what changed in analysis outcome;
- snapshot compare explains what changed in the frozen input version.

Keeping both avoids overloading one API with two responsibilities.

### Why not let rerun rebuild from latest facts when snapshot lookup fails

That would break the durable-input guarantee. A rerun that silently rebuilds from current facts is no longer a rerun against a known frozen snapshot.

### Why not make snapshot compare perform analysis automatically

That would turn a read-style comparison endpoint into an execution workflow. This phase should keep snapshot compare lightweight and deterministic over already stored input objects.

## API Contract

This phase keeps two existing APIs and adds one new API:

```text
POST /netpath/analysis-runs/:code/rerun
GET  /netpath/analysis-runs/:code/compare?tenant_code=...&target_run_code=...
GET  /netpath/snapshots/compare?tenant_code=...&baseline_snapshot_id=...&target_snapshot_id=...
```

## Rerun Contract

### Request

No major shape change is required:

```json
{
  "tenant_code": "tenant-a",
  "snapshot_id": "snapshot-followup"
}
```

Rules:

- `tenant_code` is required;
- `snapshot_id` is required;
- `snapshot_id` must resolve to a durable stored snapshot in the same tenant scope;
- target snapshot quality must not be `blocked`.

### Behavior

The service:

1. loads the baseline run by tenant and run code;
2. loads the target durable snapshot by tenant and snapshot code;
3. copies the baseline run request flow and business metadata;
4. replaces `snapshot_id` with the target durable snapshot code;
5. creates a new analyze run from that stored snapshot.

No fallback to latest-fact rebuild is allowed in this phase.

## Run Compare Contract

### Request

The API remains:

```text
GET /netpath/analysis-runs/:code/compare?tenant_code=tenant-a&target_run_code=run-2
```

### Response

`AnalyzeRunCompareResp` should continue to return run-level deltas, and it should gain snapshot summary objects for both sides.

Recommended added fields:

- `baseline_snapshot`
- `target_snapshot`

Each summary object should include at least:

- `code`
- `quality`
- `summary`
- `device_codes`
- `source_run_ids`

This keeps the run compare response self-contained for clients that want both outcome deltas and frozen-input context.

### Behavior

The service:

1. loads the baseline and target runs;
2. loads the durable snapshots referenced by both runs;
3. rejects the compare if either snapshot reference is missing or non-durable;
4. computes existing run deltas:
   - disposition delta;
   - hop delta;
   - blocker delta;
   - path summary delta;
5. attaches baseline and target snapshot summary context.

## Snapshot Compare Contract

### Request

Recommended request shape:

```text
GET /netpath/snapshots/compare?tenant_code=tenant-a&baseline_snapshot_id=snapshot-base&target_snapshot_id=snapshot-followup
```

Rules:

- `tenant_code` is required;
- `baseline_snapshot_id` is required;
- `target_snapshot_id` is required;
- both snapshot IDs must resolve within the same tenant scope.

### Response

Recommended response fields:

- `tenant_code`
- `baseline_snapshot_id`
- `target_snapshot_id`
- `baseline_quality`
- `target_quality`
- `quality_changed`
- `baseline_summary`
- `target_summary`
- `baseline_device_codes`
- `target_device_codes`
- `added_device_codes`
- `removed_device_codes`
- `baseline_diagnostics`
- `target_diagnostics`
- `added_diagnostics`
- `removed_diagnostics`
- `baseline_source_run_ids`
- `target_source_run_ids`
- `summary`

This response is intentionally metadata-first. It compares frozen input scope and quality, not analysis output.

## Error Handling

Use fail-closed behavior.

### Missing tenant or identifiers

Return direct validation errors such as:

- `tenant_code is required`
- `snapshot_id is required`
- `baseline_snapshot_id is required`
- `target_snapshot_id is required`

### Non-durable or missing snapshot reference

If rerun or run compare encounters a run-linked snapshot reference that does not resolve to a durable snapshot, fail explicitly with an error such as:

```text
run references non-durable snapshot: preview-tenant-a
```

This is preferred over any implicit compatibility path.

### Cross-tenant lookup

Treat cross-tenant access as not found in the current tenant scope.

### Blocked snapshot

- `rerun`: reject when target snapshot quality is `blocked`;
- `snapshot compare`: allow compare and surface the blocked quality normally.

## Testing Requirements

This phase should add or harden tests for:

1. rerun succeeds only when the target durable snapshot exists;
2. rerun rejects preview or missing snapshot references;
3. rerun does not fall back to latest-fact snapshot rebuild;
4. run compare rejects runs that reference missing or non-durable snapshots;
5. run compare returns baseline and target snapshot summary context;
6. snapshot compare returns quality, device-scope, diagnostics, and source-run deltas;
7. snapshot compare enforces tenant isolation;
8. blocked snapshots are rejected by rerun but allowed in snapshot compare.

## Implementation Notes

This phase should prefer extending existing service logic rather than introducing a new subsystem:

- reuse current `GetSnapshot` durable lookup behavior;
- keep `RerunAnalyzeRun` and `CompareAnalyzeRuns` in the same service boundary;
- add a new snapshot-compare DTO and service/API method pair;
- avoid introducing extra persistence tables.

The highest-value outcome is semantic tightening: rerun and compare should now clearly depend on durable stored snapshots, not just carry snapshot IDs as passive metadata.
