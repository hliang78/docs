# OneOPS NetPath Workflow Handoff Compare Context Design

Date: 2026-06-22

## Purpose

This design defines the next NetPath workflow-readiness slice after durable snapshot rerun and compare:

- let `workflow-handoff` consume run-compare context without replacing the current run-level readiness decision;
- keep workflow readiness and baseline delta semantics separate;
- expose compare-driven change risk to downstream consumers such as ticket and probe workflows through a stable handoff contract.

The goal is to move workflow handoff from:

```text
current analyze run
  -> derive readiness/status/blockers
  -> recommend next integrations
```

to:

```text
current analyze run
  -> derive readiness/status/blockers
  -> optionally compare against a baseline run
  -> attach compare_context with delta risk
  -> adjust downstream recommendation priority
```

This keeps `workflow-handoff` as the main orchestration entrypoint while making durable compare results available to downstream consumers in a controlled way.

## Current State

Current NetPath work already provides:

- durable `netpath_analysis_run` persistence;
- durable `netpath_snapshot` persistence;
- durable-snapshot-only rerun semantics;
- run-to-run compare with durable snapshot context;
- snapshot-to-snapshot compare;
- workflow handoff that derives:
  - `ready`
  - `status`
  - `blockers`
  - `recommended_integrations`

Current gap:

- `workflow-handoff` only reflects the current run state;
- callers cannot ask handoff to explain how the current run differs from a baseline run;
- downstream consumers do not have a stable handoff-level field for “change risk versus baseline”;
- compare failure should not take down handoff entirely, but the current contract has no place to carry partial compare availability.

Important design context:

- `docs/superpowers/specs/2026-06-22-oneops-netpath-durable-snapshot-rerun-compare-design.md`
- `docs/superpowers/specs/2026-06-22-oneops-netpath-snapshot-persistence-and-selection-design.md`

## Scope

In scope:

- extend `GET /netpath/analysis-runs/:code/workflow-handoff` with optional baseline compare behavior;
- add a compare-context sub-structure to `AnalyzeWorkflowHandoffResp`;
- keep current run readiness as the primary workflow gate;
- derive a lightweight compare-driven `delta_status`;
- let compare context influence downstream recommendation priority and mode;
- degrade gracefully when compare context is unavailable.

Out of scope:

- changing ticket draft or monitor probe draft response contracts in this phase;
- adding a separate workflow-handoff compare endpoint;
- changing the meaning of `ready` to include baseline deltas;
- full compare propagation into all downstream workflow DTOs;
- auto-selecting a baseline run heuristically.

## Confirmed Product Decisions

This design fixes the following decisions for this phase:

1. `workflow-handoff` keeps the current run as the source of truth for `ready`, `status`, and core blockers.
2. Baseline compare is optional and is enabled only when callers pass `baseline_run_code`.
3. Compare results are exposed through a dedicated `compare_context` sub-structure rather than flattening new fields into the handoff root.
4. Compare-driven change risk does not directly rewrite `ready`; it only influences compare context and recommendation ordering/mode.
5. If compare is unavailable, handoff still returns the current run result and surfaces compare degradation through `compare_context`.
6. Baseline compare remains tenant-scoped and durable-snapshot-safe through the existing run compare rules.

## Recommended Approach

Add a secondary compare layer to workflow handoff instead of folding compare into the existing readiness gate.

Recommended flow:

```text
GET /netpath/analysis-runs/:code/workflow-handoff?tenant_code=...&baseline_run_code=...
  -> load current run
  -> build current handoff readiness/status/blockers
  -> if baseline_run_code absent:
       return normal handoff
  -> if baseline_run_code present:
       compare baseline run vs current run
       map compare result into compare_context
       lightly adjust integration priority/mode
       return handoff + compare_context
```

This creates two distinct layers:

- readiness layer
  - answers: “is the current run ready to feed downstream actions?”
- delta layer
  - answers: “what changed versus the chosen baseline, and how risky is that change?”

## Why This Approach

### Why not let compare rewrite `ready`

`ready` answers whether the current run itself is sufficient to proceed. Compare answers whether the current run changed relative to a baseline. Mixing them makes the API harder to reason about and would confuse downstream consumers.

### Why not create a new workflow compare endpoint

The main value is contextualizing the existing workflow handoff contract. A separate endpoint would force downstream consumers to perform two independent calls and reconcile the results themselves.

### Why not auto-discover the baseline run

Baseline meaning depends on product context:

- previous run;
- pre-change run;
- manually selected reference run.

This phase should keep baseline explicit so the semantics are stable and testable.

## API Contract

This phase extends the existing endpoint:

```text
GET /netpath/analysis-runs/:code/workflow-handoff?tenant_code=...&baseline_run_code=...
```

### Request Rules

- `tenant_code` remains required.
- `baseline_run_code` is optional.
- if `baseline_run_code` is absent, handoff behaves like the current API.
- if `baseline_run_code` is present, it must resolve within the same tenant scope.

## Handoff Response Contract

The existing fields keep their current meaning:

- `ready`
- `status`
- `summary`
- `blockers`
- `recommended_integrations`

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

This structure should be omitted when no baseline is supplied.

## Delta Status Model

Use a lightweight four-state model:

- `none`
- `context_only`
- `review_recommended`
- `risk_changed`

Recommended meaning:

### `none`

- no baseline provided; or
- compare result shows no meaningful delta.

### `context_only`

- compare is available;
- no blocker or disposition change exists;
- only low-impact summary-level context is being added.

### `review_recommended`

- compare is unavailable; or
- compare shows scope/context changes such as hop movement or snapshot-quality change that should be reviewed but do not automatically imply changed blocking risk.

### `risk_changed`

- disposition changed; or
- new blockers were added relative to baseline.

This keeps the model small while making downstream recommendation tuning practical.

## Recommendation Behavior

`recommended_integrations` should not be rebuilt from scratch. This phase should only tune priority and mode.

Recommended rules:

### `delta_status = none`

- keep current recommendation ordering and modes.

### `delta_status = context_only`

- keep current recommendation ordering;
- optionally mention compare context in the handoff summary.

### `delta_status = review_recommended`

- keep existing recommendations;
- move `manual_review` earlier in the list;
- preserve automation-oriented hints, but do not remove them.

### `delta_status = risk_changed`

- move `manual_review` to the first position;
- downgrade automation-oriented hints such as `monitor_probe` or ticket-related actions from `recommended` to `conditional`;
- keep them visible so the caller still sees the next possible path after review.

## Compare Failure Handling

Handoff should degrade gracefully.

### If baseline compare succeeds

- attach full `compare_context`;
- adjust recommendation priority/mode according to `delta_status`.

### If baseline compare fails

Do not fail the whole handoff when the current run itself is readable.

Instead:

- return the normal handoff root fields from the current run;
- attach `compare_context` with:
  - `baseline_run_code`
  - `target_run_code`
  - `delta_status = review_recommended`
  - `delta_summary` describing that baseline compare was unavailable

This preserves workflow continuity while making the compare degradation explicit.

## Tenant And Durability Rules

The compare portion should inherit current compare safety rules:

- baseline and target runs must belong to the same tenant;
- run compare remains durable-snapshot-safe;
- preview or non-durable snapshot references must not silently degrade into live rebuild behavior.

If compare cannot proceed because the baseline references a non-durable snapshot, handoff should still return the current run plus degraded compare context, not a successful compare.

## Testing Requirements

This phase should add or harden tests for:

1. handoff without baseline remains behaviorally identical to today;
2. handoff with a valid baseline returns `compare_context`;
3. compare context correctly maps disposition, blocker, and hop deltas;
4. compare-unavailable scenarios keep current handoff fields and emit `delta_status = review_recommended`;
5. `risk_changed` moves `manual_review` ahead of automation-oriented hints;
6. cross-tenant baseline lookup does not leak data and degrades safely.

## Implementation Notes

This phase should prefer a minimal extension:

- add an optional `baseline_run_code` query parameter in the API layer;
- extend `GetAnalyzeRunWorkflowHandoff` service behavior;
- keep `buildAnalyzeWorkflowHandoff` focused on current-run semantics and layer compare mapping around it;
- avoid touching ticket/probe DTO contracts in this phase.

The highest-value outcome is a stable orchestration contract where callers can understand both:

- whether the current run is actionable;
- whether it changed meaningfully versus a chosen durable baseline.
