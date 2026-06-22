# OneOPS NetPath Demo Closure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close NetPath to `demo-ready` by completing result/evidence closure, minimal policy closure, and one demonstrable probe/ticket consumer chain.

**Architecture:** Reuse the existing snapshot-first analyze baseline and consumer seams already present in NetPath. Close the remaining demo chain in three focused areas: result/evidence presentation, minimal policy semantics, and one downstream action chain with reviewable output.

**Tech Stack:** OneOPS Go backend, NetPath service/runtime packages, future/actual frontend result pages, smoke/acceptance docs.

---

## File Structure

- `OneOps/app/netpath/dto/netpath.go`
  - API payloads for runs, workflow handoff, ticket draft, and monitor probe draft.
- `OneOps/app/netpath/api/netpath.go`
  - HTTP surface for run detail, workflow handoff, ticket draft, and monitor probe draft.
- `OneOps/app/netpath/api/netpath_test.go`
  - API regression coverage for result/evidence and downstream draft surfaces.
- `OneOps/app/netpath/service/impl/netpath.go`
  - Run retrieval, workflow handoff, and draft-generation orchestration.
- `OneOps/app/netpath/service/impl/netpath_test.go`
  - Service regression coverage for result presentation and downstream draft behavior.
- `OneOps/app/netpath/service/impl/evidence_summary.go`
  - Evidence summarization that the UI and downstream consumers can read directly.
- `OneOps/app/netpath/snapshot/provider/assembler.go`
  - Snapshot assembly of route and policy evidence.
- `OneOps/app/netpath/snapshot/provider/validator.go`
  - Snapshot blocking/degraded semantics for missing policy facts.
- `OneOps/app/netpath/snapshot/provider/types.go`
  - Internal snapshot evidence and diagnostics structures.
- `OneOps/app/netpath/snapshot/provider/*_test.go`
  - Provider-side regression coverage for blocked/degraded policy scenarios.
- `OneOps/app/netpath/adapter/oneopsnetpath/monitor_probe_draft.go`
  - Monitor-probe demonstrable downstream draft surface.
- `OneOps/app/netpath/adapter/oneopsnetpath/monitor_probe_draft_test.go`
  - Backward-compatibility coverage for downstream monitor-probe payload generation.
- `OneOPS-UI/src/views/topology/NetPathMvp.vue`
  - Current NetPath result page / MVP viewer.
- `OneOPS-UI/src/views/topology/netpath-graph.ts`
  - Path rendering and node-edge mapping.
- `OneOPS-UI/src/views/topology/netpath-evidence-helpers.ts`
  - Evidence drill-down helpers.
- `OneOPS-UI/src/views/platform/netpath-task-prefill.ts`
  - Demo-friendly downstream task/prefill surface for the chosen consumer chain.
- `OneOPS-UI/src/api/netpath/netpath.ts`
  - Frontend NetPath API bindings.
- `OneOPS-UI/src/typings/netpath/netpath.ts`
  - Frontend payload typings for result and draft surfaces.
- `OneOPS-UI/scripts/netpath-mvp-smoke.ts`
  - Browser smoke for result-view entry and rendering.
- `OneOPS-UI/scripts/netpath-route-smoke.ts`
  - Route/result visualization smoke.
- `OneOPS-UI/scripts/netpath-task-prefill-smoke.ts`
  - Demonstrable downstream consumer smoke.
- `docs/superpowers/acceptance/2026-06-19-oneops-netpath-user-journeys-checklist.md`
  - Existing acceptance checklist that should be used as the demo-ready gate.
- Create: `docs/evidence/netpath/demo-closure/2026-06-22-readiness-summary.md`
  - One short readiness note collecting the final demo-ready commands, evidence, and blockers.

### Task 1: Result And Evidence Closure

**Files:**
- Modify: `OneOps/app/netpath/dto/netpath.go`
- Modify: `OneOps/app/netpath/api/netpath.go`
- Modify: `OneOps/app/netpath/api/netpath_test.go`
- Modify: `OneOps/app/netpath/service/impl/netpath.go`
- Modify: `OneOps/app/netpath/service/impl/netpath_test.go`
- Modify: `OneOps/app/netpath/service/impl/evidence_summary.go`
- Modify: `OneOPS-UI/src/views/topology/NetPathMvp.vue`
- Modify: `OneOPS-UI/src/views/topology/netpath-graph.ts`
- Modify: `OneOPS-UI/src/views/topology/netpath-evidence-helpers.ts`
- Modify: `OneOPS-UI/src/api/netpath/netpath.ts`
- Modify: `OneOPS-UI/src/typings/netpath/netpath.ts`

- [ ] **Step 1: Freeze the result-view contract**

Use the current API/service tests and UI smoke as the baseline, then make the run detail surface explicitly support:
- run summary and terminal disposition;
- hop-by-hop path rendering;
- diagnostics and confidence/risk wording;
- evidence drill-down entry points that can be consumed by the UI without ad-hoc payload stitching.

- [ ] **Step 2: Implement the minimal backend and UI closure**

Adjust only the fields and helpers needed for demo-ready result/evidence closure in:
- `dto/netpath.go`
- `api/netpath.go`
- `service/impl/netpath.go`
- `service/impl/evidence_summary.go`
- `NetPathMvp.vue`
- `netpath-graph.ts`
- `netpath-evidence-helpers.ts`

Do not start production-grade rollout, writeback, or multi-consumer orchestration in this task.

- [ ] **Step 3: Verify the focused backend result surface**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps && go test ./app/netpath/api ./app/netpath/service/impl -count=1
```

Expected:
- API and service NetPath tests PASS;
- run detail, workflow handoff, ticket draft, and monitor-probe draft regressions remain green.

- [ ] **Step 4: Verify the frontend result/evidence surface**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOPS-UI && npm run smoke:netpath-mvp && npm run smoke:netpath-route
```

Expected:
- the result page renders without breaking route/view entry;
- route/result smoke proves visible path output rather than backend-only success.

### Task 2: Minimal Policy Closure

**Files:**
- Modify: `OneOps/app/netpath/snapshot/provider/assembler.go`
- Modify: `OneOps/app/netpath/snapshot/provider/validator.go`
- Modify: `OneOps/app/netpath/snapshot/provider/types.go`
- Modify: `OneOps/app/netpath/snapshot/provider/assembler_test.go`
- Modify: `OneOps/app/netpath/snapshot/provider/validator_test.go`
- Modify if needed: `OneOps/app/netpath/service/impl/netpath.go`
- Modify if needed: `OneOPS-UI/src/views/topology/NetPathMvp.vue`

- [ ] **Step 1: Lock the fail-closed policy baseline in tests**

Add or finish provider coverage proving:
- missing policy facts on a policy-relevant hop block or degrade confidence;
- unsupported policy parsing is visible as diagnostics/evidence;
- NetPath never reports a confidently allowed path when required policy facts are missing.

- [ ] **Step 2: Implement the minimal blocked/degraded semantics**

Update the provider and service layers so policy gaps are surfaced through:
- snapshot validator status;
- result diagnostics/evidence summaries;
- UI-visible wording that is no longer silently over-optimistic.

Prefer reuse of the existing provider diagnostic model over inventing a second policy-status channel.

- [ ] **Step 3: Verify provider and service policy coverage**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps && go test ./app/netpath/snapshot/provider ./app/netpath/service/impl -count=1
```

Expected:
- provider tests PASS;
- policy-gap scenarios appear as blocked or degraded, not allowed.

- [ ] **Step 4: Re-run the demo result smoke after policy hardening**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOPS-UI && npm run smoke:netpath-mvp && npm run smoke:netpath-route
```

Expected:
- result rendering still works after policy-risk semantics change;
- diagnostics remain visible to the demo user.

### Task 3: Probe/Ticket Demo Chain

**Files:**
- Modify: `OneOps/app/netpath/dto/netpath.go`
- Modify: `OneOps/app/netpath/api/netpath.go`
- Modify: `OneOps/app/netpath/api/netpath_test.go`
- Modify: `OneOps/app/netpath/service/impl/netpath.go`
- Modify: `OneOps/app/netpath/service/impl/netpath_test.go`
- Modify: `OneOps/app/netpath/adapter/oneopsnetpath/monitor_probe_draft.go`
- Modify: `OneOps/app/netpath/adapter/oneopsnetpath/monitor_probe_draft_test.go`
- Modify: `OneOPS-UI/src/views/platform/netpath-task-prefill.ts`
- Modify: `OneOPS-UI/scripts/netpath-task-prefill-smoke.ts`

- [ ] **Step 1: Choose one demo chain and keep the other secondary**

Use `monitor-probe-draft` as the primary demo chain unless a hard blocker appears.

This demo chain should be visibly:
- `analysis run`
  -> `workflow handoff`
  -> `monitor-probe draft`
  -> prefill/push-ready downstream payload

Do not attempt to close both ticket and monitor-probe execution feedback in the same phase.

- [ ] **Step 2: Make the chosen downstream chain reviewable end to end**

Ensure the chosen chain exposes:
- run identity and snapshot identity;
- compare-aware notes when baseline compare is available;
- enough evidence summary for a human to decide whether to push downstream;
- a stable payload that remains backward-compatible with the downstream maintenance contract.

- [ ] **Step 3: Verify backend draft-chain regression coverage**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps && go test ./app/netpath/api ./app/netpath/service/impl ./app/netpath/adapter/oneopsnetpath -count=1
```

Expected:
- workflow handoff, monitor-probe draft, and ticket-draft regressions PASS;
- monitor-probe payload generation remains backward-compatible.

- [ ] **Step 4: Verify the frontend/prefill demo chain**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOPS-UI && npm run smoke:netpath-task-prefill
```

Expected:
- the chosen downstream chain is visible from the demo surface;
- prefill logic consumes NetPath output without manual JSON surgery.

### Task 4: Demo Evidence And Gate Review

**Files:**
- Modify: `docs/superpowers/acceptance/2026-06-19-oneops-netpath-user-journeys-checklist.md`
- Create: `docs/evidence/netpath/demo-closure/2026-06-22-readiness-summary.md`

- [ ] **Step 1: Run the full demo-ready verification set**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps && go test ./app/netpath/... -count=1
```

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOPS-UI && npm run smoke:netpath-mvp && npm run smoke:netpath-route && npm run smoke:netpath-task-prefill
```

Expected:
- backend NetPath package tests PASS;
- all three demo-smoke commands PASS in one fresh round.

- [ ] **Step 2: Mark the relevant demo-ready acceptance items**

Update `docs/superpowers/acceptance/2026-06-19-oneops-netpath-user-journeys-checklist.md` only for items actually proven in this phase:
- result page and evidence drill-down visibility;
- fail-closed policy semantics for missing required policy facts;
- one demonstrable downstream consumer chain.

Leave production-only or not-yet-proven items unchecked.

- [ ] **Step 3: Write the demo readiness summary**

Create `docs/evidence/netpath/demo-closure/2026-06-22-readiness-summary.md` with:
- exact commands run;
- pass/fail status;
- which acceptance checklist items were proven;
- any remaining blockers that still prevent marking NetPath `demo-ready`.

- [ ] **Step 4: Mark the phase complete only if all demo gates are satisfied**

Do not treat this phase as closed unless all of these are true:
- snapshot -> analyze -> result -> evidence is visible and reviewable;
- policy semantics are no longer silently over-optimistic;
- one downstream consumer chain is demonstrable end to end;
- backend tests and frontend smoke pass in one fresh round.
