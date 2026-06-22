# OneOPS NetPath Monitor Probe Draft Compare Context Design

Date: 2026-06-22

## Purpose

This design defines the next NetPath consumer slice after ticket draft compare context:

- let `monitor-probe-draft` consume baseline compare results without replacing current probe-draft semantics;
- keep `workflow-handoff` as the producer of durable compare context;
- expose compare-driven change risk in a probe-oriented shape that can guide human review before `maintenance/monitor_probe` push.

The goal is to move monitor probe draft from:

```text
current analyze run
  -> derive workflow handoff + probe plan
  -> emit monitor_probe draft
```

to:

```text
current analyze run
  -> derive workflow handoff
  -> optionally derive baseline compare context
  -> derive probe draft from workflow + plan
  -> surface compare risk in compare_context + summary + notes
  -> emit monitor_probe draft
```

This keeps monitor probe draft focused on mapping and dispatch preparation while making baseline deltas visible before operators push probe settings downstream.

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
- monitor probe draft that currently derives:
  - `status`
  - `summary`
  - `probe_type`
  - `required_placeholders`
  - `supported_items`
  - `unsupported_directions`
  - `push_info`;
- item-level probe notes from current plan evidence only.

Current gap:

- `monitor-probe-draft` cannot explain how the current run differs from a chosen baseline run;
- compare-driven risk visible in `workflow-handoff` does not flow into monitor probe preparation;
- operators may see a valid ping draft without realizing the path or blockers changed versus the previous run;
- callers that want both probe draft and baseline delta must currently call workflow handoff separately and reconcile the payloads themselves.

Important design context:

- `docs/superpowers/specs/2026-06-22-oneops-netpath-workflow-handoff-compare-context-design.md`
- `docs/superpowers/specs/2026-06-22-oneops-netpath-ticket-draft-compare-context-design.md`

## Scope

In scope:

- extend `GET /netpath/analysis-runs/:code/monitor-probe-draft` with optional baseline compare behavior;
- add a compare-context sub-structure to `AnalyzeMonitorProbeDraftResp`;
- keep current draft item mapping and maintenance payload semantics intact;
- map workflow-handoff compare context into monitor-probe-oriented review hints;
- let compare context tune top-level `summary` and item `notes`;
- degrade safely when compare is unavailable.

Out of scope:

- changing workflow-handoff compare semantics again;
- changing `maintenance/monitor_probe` request or push contract in this phase;
- inventing a probe-specific delta taxonomy;
- direction-precise compare-to-item matching heuristics;
- auto-selecting a baseline run heuristically;
- persisting compare metadata into maintenance tables in this phase.

## Confirmed Product Decisions

This design fixes the following decisions for this phase:

1. `monitor-probe-draft` may accept `baseline_run_code`, but compare remains optional.
2. Probe compare data is exposed through a dedicated `compare_context` field rather than being hidden only inside `summary`.
3. The monitor-probe compare payload should reuse the delta model already stabilized in workflow handoff instead of inventing a new one.
4. Compare context may tune `summary` and item `notes`, but it does not replace current `supported_items` derivation from the probe plan.
5. If compare is unavailable, monitor probe draft still returns the current run draft and surfaces degradation through `compare_context`.
6. Compare guidance stops at the NetPath draft boundary in this phase and does not change `maintenance/monitor_probe` payload shape.

## Recommended Approach

Use workflow handoff as the compare producer and monitor probe draft as the compare consumer.

Recommended flow:

```text
GET /netpath/analysis-runs/:code/monitor-probe-draft?tenant_code=...&baseline_run_code=...
  -> build workflow handoff with same baseline input
  -> load current analyze run and probe plan as today
  -> build monitor probe draft from handoff + plan
  -> if handoff compare_context exists:
       attach compare_context to probe draft
       tune summary wording by delta_status
       append compare-aware review notes to supported items
  -> return monitor probe draft
```

This keeps compare orchestration centralized in workflow handoff and avoids duplicating baseline compare rules inside monitor probe draft.

## Why This Approach

### Why not call run compare directly from monitor probe draft

Monitor probe draft already depends on workflow-oriented interpretation of the run. Reusing workflow handoff avoids duplicating compare fallback rules and keeps one source of truth for degradation behavior.

### Why not hide compare data only in `summary` or `notes`

Text hints are useful for humans but unstable for downstream consumers. A structured `compare_context` gives UI and automation a stable place to read delta state while keeping human-readable guidance in summary text.

### Why not push compare metadata into maintenance payload now

The current problem is NetPath-side reviewability, not downstream contract expansion. Extending `maintenance/monitor_probe` too early would spread compare semantics across module boundaries before they are proven useful.

## API Contract

This phase extends the existing endpoint:

```text
GET /netpath/analysis-runs/:code/monitor-probe-draft?tenant_code=...&baseline_run_code=...
```

### Request Rules

- `tenant_code` remains required.
- `baseline_run_code` is optional.
- if `baseline_run_code` is absent, monitor probe draft behaves like the current API.
- if `baseline_run_code` is present, monitor probe draft passes it through to workflow handoff compare behavior.

## Monitor Probe Draft Response Contract

Existing fields keep their current meaning:

- `status`
- `summary`
- `probe_type`
- `required_placeholders`
- `supported_items`
- `unsupported_directions`
- `push_info`

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

For this phase the payload may be field-for-field compatible with workflow handoff compare context. The contract difference is not in field shape, but in how monitor probe draft uses the compare signal.

## Probe Draft Behavior

This phase should keep current draft-building behavior stable, then layer compare behavior on top.

### No baseline compare

- monitor probe draft remains behaviorally identical to today;
- no `compare_context` is returned;
- item notes remain current-plan-only.

### `delta_status = none`

- attach `compare_context`;
- keep current summary and item-note behavior;
- do not add extra review warnings.

### `delta_status = context_only`

- attach `compare_context`;
- append a short compare note to `summary`;
- optionally append a lightweight note to each supported item reminding operators that baseline context exists but no high-risk delta was detected.

### `delta_status = review_recommended`

- attach `compare_context`;
- make `summary` explicitly recommend baseline-delta review before direct push;
- append a compare-aware review note to each supported item;
- keep current supported/unsupported direction classification unchanged.

### `delta_status = risk_changed`

- attach `compare_context`;
- make `summary` explicitly mention changed disposition or new blockers;
- append stronger “review before push” wording to each supported item;
- keep draft payload generation available, but frame it as reference material rather than direct push input.

## Summary and Notes Strategy

This phase should not attempt precise direction-level compare attribution.

Recommended rule:

- top-level `summary` carries the main compare posture;
- item `notes` carry stable operator guidance derived from the same compare posture;
- compare notes are additive and do not replace existing gateway, device, or interface hints.

Recommended note style by delta state:

- `context_only`
  - mention that a baseline compare exists and operators may review it before final tag and host mapping;
- `review_recommended`
  - mention that path or snapshot context changed and tag / target mapping should be rechecked before push;
- `risk_changed`
  - mention that blockers or disposition changed and the draft should not be pushed without manual review.

This keeps the implementation simple and avoids brittle attempts to infer which exact supported direction caused the compare delta.

## Compare Failure Handling

Monitor probe draft should degrade gracefully the same way workflow handoff does.

Recommended behavior:

- if compare succeeds:
  - return current monitor probe draft plus `compare_context`;
- if compare fails:
  - return current monitor probe draft;
  - attach degraded `compare_context` from workflow handoff;
  - bias `summary` toward review wording because baseline reconciliation is incomplete.

Compare failure should not fail the entire endpoint.

## Data Flow

Recommended flow:

```text
NetPath API
  -> GetAnalyzeRunMonitorProbeDraft(tenant_code, analyze_run_code, baseline_run_code?)
     -> GetAnalyzeRunWorkflowHandoff(..., baseline_run_code)
     -> GetAnalyzeRun(...)
     -> lookupAnalyzeRunProbePlan(...)
     -> buildAnalyzeMonitorProbeDraft(handoff, plan)
        -> attach handoff compare_context when present
        -> adjust summary/notes by delta_status
  -> return AnalyzeMonitorProbeDraftResp
```

No new storage or background job is needed in this phase.

## Testing Strategy

Cover at least:

1. service behavior without baseline:
   - response remains backward-compatible;
   - no `compare_context` is returned.
2. service behavior with successful baseline compare:
   - `compare_context` is attached;
   - `summary` changes according to `delta_status`;
   - compare notes are appended to supported items.
3. service behavior with compare degradation:
   - draft still returns successfully;
   - degraded `compare_context` is present;
   - review-oriented summary wording is used.
4. API behavior:
   - `baseline_run_code` is accepted and passed through;
   - response JSON includes `compare_context` when expected.
5. adapter regression:
   - `BuildMonitorProbeDraftPayload` remains unchanged and ignores the new compare-only fields.

## Implementation Notes

Recommended implementation shape:

- extend monitor-probe draft request handling to accept `baseline_run_code`;
- reuse `GetAnalyzeRunWorkflowHandoff` as the only compare orchestrator;
- attach `handoff.CompareContext` to the monitor probe draft response;
- add small helper functions for:
  - summary tuning by compare delta;
  - compare-aware item note appending;
- keep adapter and maintenance payload code unchanged unless tests show accidental coupling.

## Risks and Non-Goals

Known risks:

- operators may over-interpret compare notes as direction-specific facts if wording is too strong;
- repeating the same compare note on every item can be slightly verbose;
- future consumers may want more precise compare-to-direction mapping than this phase provides.

Non-goals for this phase:

- exact per-direction compare attribution;
- durable persistence of compare metadata in maintenance records;
- automatic suppression of draft payload generation when compare risk exists.

## Success Criteria

This phase is successful when:

- callers can request `monitor-probe-draft` with `baseline_run_code`;
- the response carries stable `compare_context` semantics aligned with workflow handoff;
- compare risk is visible to both humans and structured consumers;
- existing monitor probe payload generation remains backward-compatible;
- compare failures degrade gracefully instead of breaking the probe draft endpoint.
