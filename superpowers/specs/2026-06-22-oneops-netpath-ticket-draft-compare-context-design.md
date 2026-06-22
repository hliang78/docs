# OneOPS NetPath Ticket Draft Compare Context Design

Date: 2026-06-22

## Purpose

This design defines the next NetPath consumer slice after workflow handoff compare context:

- let `ticket-draft` consume baseline compare results without replacing current ticket-draft semantics;
- keep workflow-handoff as the producer of durable compare context;
- expose compare-driven change risk in a ticket-oriented shape that can be carried into downstream task and ticket systems.

The goal is to move ticket draft from:

```text
current analyze run
  -> derive owner/action/evidence
  -> emit ticket draft
```

to:

```text
current analyze run
  -> derive workflow handoff
  -> optionally derive baseline compare context
  -> map compare context into ticket-oriented delta fields
  -> emit ticket draft + task metadata with compare signal
```

This keeps ticket draft focused on actionability while making baseline delta risk visible to humans and downstream automation.

## Current State

Current NetPath work already provides:

- durable `netpath_analysis_run` persistence;
- durable `netpath_snapshot` persistence;
- run-to-run compare and snapshot-to-snapshot compare;
- workflow handoff with optional `baseline_run_code`;
- workflow handoff `compare_context` with:
  - `delta_status`
  - blocker delta
  - hop delta
  - compare degradation behavior;
- ticket draft that currently derives:
  - `status`
  - `summary`
  - `suggested_owner`
  - `suggested_action`
  - `path_summary`
  - `evidence`
  - `probe_execution`
  - `links`;
- task creation metadata derived from ticket draft and analyze run.

Current gap:

- `ticket-draft` cannot explain how the current run differs from a chosen baseline run;
- baseline delta risk visible in `workflow-handoff` does not flow into ticket-oriented fields;
- task metadata produced from ticket draft has no stable location for compare-driven change context;
- callers that want both ticket draft and baseline delta must currently call handoff separately and reconcile the payloads themselves.

Important design context:

- `docs/superpowers/specs/2026-06-22-oneops-netpath-workflow-handoff-compare-context-design.md`
- `docs/superpowers/specs/2026-06-22-oneops-netpath-durable-snapshot-rerun-compare-design.md`

## Scope

In scope:

- extend `GET /netpath/analysis-runs/:code/ticket-draft` with optional baseline compare behavior;
- add a small compare-context sub-structure to `AnalyzeTicketDraftResp`;
- keep current ticket draft owner/action/evidence semantics intact;
- map workflow-handoff compare context into a ticket-oriented delta payload;
- let compare context lightly tune summary/action wording;
- extend task metadata with compare-aware fields derived from ticket draft.

Out of scope:

- changing `workflow-handoff` compare semantics again;
- changing `monitor-probe-draft` in this phase;
- creating a separate ticket-compare endpoint;
- inventing a second, different risk taxonomy just for ticket draft;
- auto-discovering baseline runs heuristically;
- changing the core `suggested_owner` routing heuristic in this phase.

## Confirmed Product Decisions

This design fixes the following decisions for this phase:

1. `ticket-draft` may accept `baseline_run_code`, but compare remains optional.
2. Ticket compare data is exposed through a dedicated `compare_context` field rather than being hidden only inside `summary`.
3. The ticket-draft compare payload should reuse the same delta model already stabilized in workflow handoff instead of inventing a new one.
4. Compare context may tune ticket summary and suggested action wording, but it does not replace current owner/action derivation logic.
5. If compare is unavailable, ticket draft still returns the current run draft and surfaces degradation through `compare_context`.
6. Task metadata should carry compare context so downstream automation can consume the same signal without reparsing ticket summary text.

## Recommended Approach

Use workflow handoff as the compare producer and ticket draft as the compare consumer.

Recommended flow:

```text
GET /netpath/analysis-runs/:code/ticket-draft?tenant_code=...&baseline_run_code=...
  -> load current analyze run
  -> build workflow handoff with same baseline input
  -> build probe execution as today
  -> build ticket draft from run + handoff + probe execution
  -> if handoff compare_context exists:
       map it into ticket compare_context
       lightly adjust ticket summary/action wording
  -> return ticket draft
```

Task creation continues to use ticket draft, but now receives richer compare-aware metadata:

```text
current run + ticket draft
  -> build oneops_netpath task metadata
  -> include compare summary/risk fields when present
```

This approach keeps compare logic centralized in workflow handoff and avoids duplicating compare orchestration inside ticket draft.

## Why This Approach

### Why not call run compare directly from ticket draft

Ticket draft already depends on workflow-oriented interpretation of the run. Reusing workflow handoff avoids duplicating compare fallback rules and keeps one source of truth for degradation behavior.

### Why not hide compare data only in `summary`

Summary text is useful for humans but unstable for downstream consumers. A structured `compare_context` gives human-readable and machine-readable surfaces at the same time.

### Why not create a ticket-specific risk taxonomy

Workflow handoff already established a small delta model:

- `none`
- `context_only`
- `review_recommended`
- `risk_changed`

Reusing it keeps semantics aligned across orchestration layers and reduces translation errors.

## API Contract

This phase extends the existing endpoint:

```text
GET /netpath/analysis-runs/:code/ticket-draft?tenant_code=...&baseline_run_code=...
```

### Request Rules

- `tenant_code` remains required.
- `baseline_run_code` is optional.
- if `baseline_run_code` is absent, ticket draft behaves like the current API.
- if `baseline_run_code` is present, ticket draft passes it through to workflow handoff compare behavior.

## Ticket Draft Response Contract

Existing fields keep their current meaning:

- `status`
- `summary`
- `suggested_owner`
- `suggested_action`
- `path_summary`
- `blockers`
- `evidence`
- `probe_execution`
- `links`

Add:

```text
compare_context
```

Recommended structure:

- `baseline_run_code`
- `baseline_snapshot_id`
- `target_run_code`
- `target_snapshot_id`
- `delta_status`
- `delta_summary`
- `disposition_changed`
- `added_blockers`
- `removed_blockers`
- `added_hops`
- `removed_hops`

This structure should be omitted when no baseline is supplied and should degrade safely when compare is unavailable.

The payload may be field-for-field compatible with workflow handoff compare context for this phase, but it is attached under ticket draft because the consumer contract is different.

## Ticket Behavior

This phase should keep existing ticket-draft behavior stable, then layer compare behavior on top.

### No baseline compare

- ticket draft remains behaviorally identical to today;
- no `compare_context` is returned;
- task metadata remains compare-free.

### `delta_status = none`

- attach `compare_context`;
- keep current `summary` and `suggested_action` behavior;
- include compare fields in task metadata for traceability.

### `delta_status = context_only`

- attach `compare_context`;
- append a short compare note to `summary`;
- keep `suggested_owner` and `suggested_action` unchanged.

### `delta_status = review_recommended`

- attach `compare_context`;
- append a review-oriented compare note to `summary`;
- prefix or extend `suggested_action` so it clearly recommends baseline-delta review before downstream execution;
- add a compare-oriented link when appropriate.

### `delta_status = risk_changed`

- attach `compare_context`;
- make `summary` explicitly mention changed disposition or new blockers;
- bias `suggested_action` toward human review before firewall/routing/task execution;
- preserve the existing `suggested_owner` heuristic instead of replacing it.

## Compare Failure Handling

Ticket draft should degrade gracefully the same way workflow handoff does.

### If compare succeeds

- return full ticket draft;
- attach `compare_context`;
- tune summary/action wording according to `delta_status`;
- carry compare signal into task metadata.

### If compare fails

Do not fail the whole ticket draft when the current run itself is readable.

Instead:

- return the normal ticket-draft root fields from the current run;
- attach `compare_context` with:
  - `baseline_run_code`
  - `target_run_code`
  - `delta_status = review_recommended`
  - `delta_summary` describing that baseline compare was unavailable.

This preserves draft continuity while making compare degradation explicit.

## Task Metadata Contract

`buildAnalyzeTaskMetadata(...)` should include compare-aware metadata when ticket draft compare context exists.

Recommended additions under `oneops_netpath`:

- `baseline_run_code`
- `baseline_snapshot_id`
- `target_run_code`
- `target_snapshot_id`
- `delta_status`
- `delta_summary`
- `disposition_changed`
- `added_blocker_codes`
- `removed_blocker_codes`
- `added_hop_devices`
- `removed_hop_devices`

This keeps downstream systems from having to scrape compare meaning out of summary text.

## Links

This phase may add one or more lightweight links when compare context exists, such as:

- workflow handoff URL with the same `baseline_run_code`;
- run compare URL between baseline and target.

These links should be additive and must not remove current `path_view` / `probe_execution` links.

## Tenant And Durability Rules

The compare portion inherits current workflow handoff compare safety rules:

- baseline and target runs must remain tenant-scoped;
- compare remains durable-snapshot-safe;
- preview or non-durable snapshot references must not silently trigger rebuild behavior;
- compare-unavailable conditions degrade to ticket compare context rather than failing the entire draft.

## Testing Requirements

This phase should add or harden tests for:

1. ticket draft without baseline remains behaviorally identical to today;
2. ticket draft with valid baseline returns `compare_context`;
3. compare-unavailable scenarios keep current draft fields and emit `delta_status = review_recommended`;
4. `risk_changed` influences summary/action wording without rewriting suggested owner;
5. task metadata carries compare-aware fields when ticket compare context exists;
6. baseline compare remains tenant-scoped through the inherited workflow-handoff rules.

## Implementation Notes

This phase should prefer a minimal extension:

- add optional `baseline_run_code` query binding in the ticket-draft API layer;
- extend `GetAnalyzeRunTicketDraft` service behavior to request workflow handoff with the same baseline input;
- keep compare orchestration inside workflow handoff;
- add small helpers to map handoff compare context into ticket draft compare context and task metadata fields;
- avoid broad owner/routing heuristic changes while compare semantics are still being stabilized.

The highest-value outcome is a stable ticket-oriented contract where callers can understand both:

- what action the current run suggests;
- how that action context changed relative to a chosen durable baseline.
