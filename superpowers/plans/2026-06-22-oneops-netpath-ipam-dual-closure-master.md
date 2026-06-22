# OneOPS NetPath And IPAM Dual-Closure Master Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the dual-closure master design into an executable delivery control plane by creating the shared status surface and the next focused phase documents for IPAM launch closure and NetPath demo closure.

**Architecture:** Treat the master design as orchestration, not a direct code-change spec. This plan first creates a durable control surface, then decomposes the work into phase-local specs and implementation plans, so IPAM and NetPath can close in sequence without collapsing back into one oversized parallel program.

**Tech Stack:** Markdown docs under `docs/superpowers`, existing OneOPS specs/plans, git commits for document checkpoints.

---

## Scope Check

The approved master design covers multiple independent subsystems:

- `IPAM launch closure`
- `NetPath demo closure`
- later `NetPath production closure`
- later `shared contract hardening`

So this master plan must not attempt to implement those subsystems directly. Instead, it should produce the minimal orchestration assets that make the next implementation rounds unambiguous.

This plan therefore produces:

1. a shared status board;
2. a focused IPAM launch-closure spec;
3. a focused IPAM launch-closure implementation plan;
4. a focused NetPath demo-closure spec;
5. a focused NetPath demo-closure implementation plan;
6. a short deferred note describing when to open NetPath production-closure and shared-contract-hardening work.

## File Structure

### New files to create

- `docs/superpowers/2026-06-22-oneops-dual-closure-status-board.md`
  - Shared status board for `IPAM`, `NetPath`, and deferred `dc2` hardening phases.
- `docs/superpowers/specs/2026-06-22-oneops-ipam-launch-closure-design.md`
  - Focused design for closing IPAM to `launch-ready`.
- `docs/superpowers/plans/2026-06-22-oneops-ipam-launch-closure.md`
  - Actionable implementation plan for IPAM launch closure.
- `docs/superpowers/specs/2026-06-22-oneops-netpath-demo-closure-design.md`
  - Focused design for closing NetPath to `demo-ready`.
- `docs/superpowers/plans/2026-06-22-oneops-netpath-demo-closure.md`
  - Actionable implementation plan for NetPath demo closure.
- `docs/superpowers/2026-06-22-oneops-dual-closure-phase-open-criteria.md`
  - Deferred phase-open criteria for NetPath production closure and shared contract hardening.

### Existing files to read and align with

- `docs/superpowers/specs/2026-06-22-oneops-netpath-ipam-dual-closure-master-design.md`
  - Master control-plane design that this plan executes.
- `docs/superpowers/2026-06-22-netpath-ipam-closure-gap-comparison.md`
  - Closure-gap baseline and relative priority reasoning.
- `docs/superpowers/plans/2026-06-19-ipam-production-launch-journey-plan.md`
  - Existing IPAM launch framing and user-journey expectations.
- `docs/superpowers/plans/2026-06-19-oneops-netpath-master-roadmap.md`
  - Existing NetPath phase naming and reporting conventions.

## Task 1: Create The Shared Dual-Closure Status Board

**Files:**
- Create: `docs/superpowers/2026-06-22-oneops-dual-closure-status-board.md`

- [ ] **Step 1: Write the initial status-board content**

Create `docs/superpowers/2026-06-22-oneops-dual-closure-status-board.md` with:

```md
# OneOPS Dual-Closure Status Board

Date: 2026-06-22

## Purpose

This board tracks the closure status of:

- `IPAM launch closure`
- `NetPath demo closure`
- `NetPath production closure`
- `Shared contract hardening`

Status vocabulary:

- `planned`
- `source-level complete`
- `verified`
- `integrated`
- `ready`

NetPath ready states:

- `demo-ready`
- `production-ready`

IPAM ready state:

- `launch-ready`

## Current Board

| Line | Phase | Status | Target Ready State | Notes |
| --- | --- | --- | --- | --- |
| `IPAM` | Launch closure | `planned` | `launch-ready` | Waiting for focused closure spec and plan |
| `NetPath` | Demo closure | `planned` | `demo-ready` | Waiting for focused closure spec and plan |
| `NetPath` | Production closure | `planned` | `production-ready` | Opens only after demo closure is integrated |
| `dc2` | Shared contract hardening | `planned` | minimal hardened contract | Opens only after IPAM and NetPath prove stable consumer needs |

## Operating Rule

When a phase changes status, update this board in the same round as the phase-local spec/plan or implementation checkpoint.
```

- [ ] **Step 2: Verify the board file exists and is readable**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL && sed -n '1,220p' docs/superpowers/2026-06-22-oneops-dual-closure-status-board.md
```

Expected: the new status-board file prints with the four tracked lines and shared vocabulary.

- [ ] **Step 3: Commit the status board**

```bash
cd /home/jacky/project/OneOPS-ALL/docs
git add superpowers/2026-06-22-oneops-dual-closure-status-board.md
git commit -m "docs: add dual closure status board"
```

## Task 2: Write The Focused IPAM Launch-Closure Spec

**Files:**
- Create: `docs/superpowers/specs/2026-06-22-oneops-ipam-launch-closure-design.md`

- [ ] **Step 1: Write the focused IPAM launch-closure spec**

Create `docs/superpowers/specs/2026-06-22-oneops-ipam-launch-closure-design.md` with sections covering:

```md
# OneOPS IPAM Launch Closure Design

Date: 2026-06-22

## Purpose

Define the smallest remaining scope needed to move IPAM from closure-in-progress to `launch-ready`.

## Scope

In scope:

- projection -> `ipam_address_fact` -> audit finding stabilization
- allocation / release / reclaim / audit journey hardening
- repeatable smoke and launch evidence
- launch gate semantics and blockers

Out of scope:

- broad new IPAM features
- cross-module fact-contract expansion beyond what IPAM must consume now
- formal approval workflow expansion

## Closure Target

`launch-ready` means:

- resource, allocation, reclaim, and audit chains are frontend-operable;
- projection/finding behavior is stable and explainable;
- smoke is repeatable and evidence is sufficient for launch review.

## Remaining Gaps

- projection/finding stabilization
- allocation/reclaim/audit final smoke reliability
- launch-gate evidence and feedback hardening

## Recommended Work Buckets

1. Fact projection and audit stabilization
2. Allocation and reclaim operational hardening
3. Smoke and evidence hardening
4. Launch gate review
```

- [ ] **Step 2: Verify the spec file exists and is readable**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL && sed -n '1,260p' docs/superpowers/specs/2026-06-22-oneops-ipam-launch-closure-design.md
```

Expected: the spec prints with purpose, scope, closure target, remaining gaps, and work buckets.

- [ ] **Step 3: Commit the IPAM closure spec**

```bash
cd /home/jacky/project/OneOPS-ALL/docs
git add superpowers/specs/2026-06-22-oneops-ipam-launch-closure-design.md
git commit -m "docs: design ipam launch closure"
```

## Task 3: Write The IPAM Launch-Closure Implementation Plan

**Files:**
- Create: `docs/superpowers/plans/2026-06-22-oneops-ipam-launch-closure.md`

- [ ] **Step 1: Write the focused IPAM launch-closure implementation plan**

Create `docs/superpowers/plans/2026-06-22-oneops-ipam-launch-closure.md` with:

```md
# OneOPS IPAM Launch Closure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close IPAM to `launch-ready` by stabilizing projection-to-finding behavior, hardening allocation/reclaim/audit journeys, and proving repeatable launch evidence.

**Architecture:** Keep existing IPAM vertical slices intact and close the remaining gaps through focused closure work: fact projection/audit stabilization, operational-flow hardening, and launch-gate evidence. Avoid broad new feature work while this closure phase is active.

**Tech Stack:** OneOPS Go backend, Vue frontend, IPAM service tests, smoke scripts, evidence docs.

---

## File Structure

- existing IPAM service impl files for projection, request, reclaim, statistics, and audit
- existing frontend journey pages
- smoke scripts and evidence docs

### Task 1: Projection And Finding Stabilization
### Task 2: Allocation/Reclaim/Audit Journey Hardening
### Task 3: Launch Evidence And Gate Review
```

- [ ] **Step 2: Verify the IPAM plan file exists and is readable**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL && sed -n '1,260p' docs/superpowers/plans/2026-06-22-oneops-ipam-launch-closure.md
```

Expected: the plan prints with the required header, focused goal, and the three task groups.

- [ ] **Step 3: Commit the IPAM plan**

```bash
cd /home/jacky/project/OneOPS-ALL/docs
git add superpowers/plans/2026-06-22-oneops-ipam-launch-closure.md
git commit -m "docs: plan ipam launch closure"
```

## Task 4: Write The Focused NetPath Demo-Closure Spec

**Files:**
- Create: `docs/superpowers/specs/2026-06-22-oneops-netpath-demo-closure-design.md`

- [ ] **Step 1: Write the focused NetPath demo-closure spec**

Create `docs/superpowers/specs/2026-06-22-oneops-netpath-demo-closure-design.md` with sections covering:

```md
# OneOPS NetPath Demo Closure Design

Date: 2026-06-22

## Purpose

Define the smallest remaining scope needed to move NetPath from productization-in-progress to `demo-ready`.

## Scope

In scope:

- result and evidence closure
- minimal policy closure
- at least one downstream probe/ticket consumer chain
- demo gate semantics and blockers

Out of scope:

- full production rollout hardening
- broad policy-family expansion beyond minimal closure
- full shared-contract hardening

## Closure Target

`demo-ready` means:

- snapshot -> analyze -> result -> evidence chain is complete;
- at least one downstream consumer chain is demonstrable;
- policy semantics are no longer silently over-optimistic.

## Remaining Gaps

- result/evidence UX closure
- minimal policy closure
- probe/ticket demonstrable end-to-end chain

## Recommended Work Buckets

1. Result and evidence closure
2. Minimal policy closure
3. Probe/ticket demo chain
4. Demo evidence and gate review
```

- [ ] **Step 2: Verify the NetPath spec file exists and is readable**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL && sed -n '1,260p' docs/superpowers/specs/2026-06-22-oneops-netpath-demo-closure-design.md
```

Expected: the spec prints with purpose, scope, closure target, remaining gaps, and work buckets.

- [ ] **Step 3: Commit the NetPath closure spec**

```bash
cd /home/jacky/project/OneOPS-ALL/docs
git add superpowers/specs/2026-06-22-oneops-netpath-demo-closure-design.md
git commit -m "docs: design netpath demo closure"
```

## Task 5: Write The NetPath Demo-Closure Implementation Plan

**Files:**
- Create: `docs/superpowers/plans/2026-06-22-oneops-netpath-demo-closure.md`

- [ ] **Step 1: Write the focused NetPath demo-closure implementation plan**

Create `docs/superpowers/plans/2026-06-22-oneops-netpath-demo-closure.md` with:

```md
# OneOPS NetPath Demo Closure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close NetPath to `demo-ready` by completing result/evidence closure, minimal policy closure, and one demonstrable probe/ticket consumer chain.

**Architecture:** Reuse the existing snapshot-first analyze baseline and consumer seams already present in NetPath. Close the remaining demo chain in three focused areas: result/evidence presentation, minimal policy semantics, and one downstream action chain with reviewable output.

**Tech Stack:** OneOPS Go backend, NetPath service/runtime packages, future/actual frontend result pages, smoke/acceptance docs.

---

## File Structure

- existing netpath service, api, snapshot, runtime, and future/actual frontend result files
- smoke or acceptance evidence docs

### Task 1: Result And Evidence Closure
### Task 2: Minimal Policy Closure
### Task 3: Probe/Ticket Demo Chain
### Task 4: Demo Evidence And Gate Review
```

- [ ] **Step 2: Verify the NetPath plan file exists and is readable**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL && sed -n '1,260p' docs/superpowers/plans/2026-06-22-oneops-netpath-demo-closure.md
```

Expected: the plan prints with the required header, focused goal, and the four task groups.

- [ ] **Step 3: Commit the NetPath plan**

```bash
cd /home/jacky/project/OneOPS-ALL/docs
git add superpowers/plans/2026-06-22-oneops-netpath-demo-closure.md
git commit -m "docs: plan netpath demo closure"
```

## Task 6: Write Deferred Phase-Open Criteria

**Files:**
- Create: `docs/superpowers/2026-06-22-oneops-dual-closure-phase-open-criteria.md`

- [ ] **Step 1: Write the deferred phase-open note**

Create `docs/superpowers/2026-06-22-oneops-dual-closure-phase-open-criteria.md` with:

```md
# OneOPS Dual-Closure Deferred Phase-Open Criteria

Date: 2026-06-22

## Purpose

Define when it is valid to open:

- `NetPath production closure`
- `shared contract hardening`

## NetPath Production Closure Opens When

- NetPath demo closure is at least `integrated`
- a probe/ticket demo chain is visible end to end
- unresolved work is mostly runtime/ops hardening, not missing core UX chain

## Shared Contract Hardening Opens When

- IPAM launch closure is at least `verified`
- NetPath demo closure is at least `verified`
- both lines can point to a concrete minimal shared fact set that must become stable

## Explicit Rule

Do not open either deferred phase because the topic feels important in abstract. Open only when the earlier application closure phases have exposed stable, concrete needs.
```

- [ ] **Step 2: Verify the deferred phase-open note exists and is readable**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL && sed -n '1,220p' docs/superpowers/2026-06-22-oneops-dual-closure-phase-open-criteria.md
```

Expected: the note prints the open criteria for NetPath production closure and shared contract hardening.

- [ ] **Step 3: Commit the deferred phase-open note**

```bash
cd /home/jacky/project/OneOPS-ALL/docs
git add superpowers/2026-06-22-oneops-dual-closure-phase-open-criteria.md
git commit -m "docs: define dual closure phase open criteria"
```

## Task 7: Update The Shared Status Board With New Planning Artifacts

**Files:**
- Modify: `docs/superpowers/2026-06-22-oneops-dual-closure-status-board.md`

- [ ] **Step 1: Update the board after the focused docs exist**

Modify `docs/superpowers/2026-06-22-oneops-dual-closure-status-board.md` so the `Current Board` section becomes:

```md
## Current Board

| Line | Phase | Status | Target Ready State | Notes |
| --- | --- | --- | --- | --- |
| `IPAM` | Launch closure | `planned` | `launch-ready` | Focused design and implementation plan now exist; execution not started |
| `NetPath` | Demo closure | `planned` | `demo-ready` | Focused design and implementation plan now exist; execution not started |
| `NetPath` | Production closure | `planned` | `production-ready` | Deferred until demo closure reaches the open criteria |
| `dc2` | Shared contract hardening | `planned` | minimal hardened contract | Deferred until IPAM and NetPath expose stable shared-fact needs |
```

- [ ] **Step 2: Verify the updated board**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL && sed -n '1,220p' docs/superpowers/2026-06-22-oneops-dual-closure-status-board.md
```

Expected: the board shows the focused docs now exist for IPAM and NetPath, while deferred phases remain unopened.

- [ ] **Step 3: Commit the board update**

```bash
cd /home/jacky/project/OneOPS-ALL/docs
git add superpowers/2026-06-22-oneops-dual-closure-status-board.md
git commit -m "docs: update dual closure status board"
```
