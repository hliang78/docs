# OneOPS NetPath And IPAM Dual-Closure Master Design

Date: 2026-06-22

## Purpose

This design defines the control plane for closing both OneOPS application lines:

- `IPAM` as the first launch-ready business closure sample;
- `NetPath` as the first analysis-closure sample, first at demo level and later at production level.

This is not a feature implementation spec. It is a sequencing, dependency, and gating design that keeps both lines converging without letting the work expand into an uncontrolled shared-foundation program.

The core question is:

```text
How do we close both IPAM and NetPath end to end
without turning the work into a giant parallel bottom-up platform rewrite?
```

## Current Context

Observed project direction from the current docs and codebase:

- OneOPS is converging around a shared fact foundation rather than parallel application-local fact models.
- `IPAM` has moved beyond page construction into resource, allocation, reclaim, and audit closure planning.
- `NetPath` has moved beyond engine porting into durable snapshot persistence, snapshot-first analyze, workflow handoff, ticket draft, and monitor-probe draft progression.
- `dc2` canonical contracts are directionally correct but still too thin to serve as a fully stabilized multi-application contract dictionary.

Current risk:

- design convergence is ahead of integration convergence;
- both applications depend on the same shared fact layer;
- if both application closures and the full shared contract are expanded in parallel, execution scope will widen faster than integration.

## Design Goal

This master design must do four things:

1. define what “closure complete” means for `IPAM` and `NetPath`;
2. separate demo-ready and production-ready goals where they are not equivalent;
3. define a small number of phases with explicit dependencies and gates;
4. defer broad shared-contract hardening until real application closure work proves what must become stable.

## Non-Goals

This design does not:

- define the full `dc2` contract dictionary;
- replace detailed application specs and implementation plans;
- prescribe exact backend/frontend file changes;
- flatten `IPAM` and `NetPath` into the same delivery shape;
- require every shared-foundation issue to be solved before application closure continues.

## Closure Definitions

### IPAM Closure Definition

`IPAM` is considered closed only when a user can move through:

```text
planning / prefix / pool
  -> allocation
  -> release / reclaim
  -> observed fact projection
  -> audit finding
  -> resolve / launch acceptance
```

This means IPAM closure is not “the pool page works” or “allocation API exists.” It means the resource, allocation, reclaim, fact, and audit chain is operational, visible, and verifiable.

### NetPath Closure Definition

`NetPath` is considered closed only when a user can move through:

```text
snapshot
  -> analyze
  -> result
  -> evidence
  -> downstream probe/ticket action
  -> action feedback / review outcome
```

This means NetPath closure is not “the engine returns a trace” or “a draft payload exists.” It means analysis output is consumable, traceable, and connected to downstream action and review.

## Readiness Levels

`IPAM` and `NetPath` should not be forced into the same final gate.

Recommended readiness model:

- `IPAM`
  - `launch-ready`
- `NetPath`
  - `demo-ready`
  - `production-ready`

This reflects actual product reality:

- `IPAM` is already closer to a launch-hardening problem;
- `NetPath` is closer to an analysis-product closure problem that needs a staged transition from demo to production.

## Recommended Phase Model

The master design should use four phases.

### Phase A: IPAM Launch Closure

Purpose:

- make `IPAM` the first launch-ready closure sample on top of the shared fact foundation.

Primary focus:

- resource closure;
- allocation closure;
- reclaim closure;
- fact projection to `ipam_address_fact`;
- audit finding generation and resolution;
- smoke and evidence suitable for launch gate use.

Expected output:

- first application line that can reasonably claim launch-ready closure.

### Phase B: NetPath Demo Closure

Purpose:

- make `NetPath` the first demo-ready analysis closure sample.

Primary focus:

- durable snapshot list/detail;
- snapshot-first analyze user flow;
- result presentation;
- evidence drill-down;
- minimal policy closure;
- at least one downstream probe or ticket consumer chain that is demonstrable end to end.

Expected output:

- first application line that can reasonably claim demo-ready analysis closure.

### Phase C: NetPath Production Closure

Purpose:

- move `NetPath` from demonstrable closure to production-grade closure.

Primary focus:

- downstream execution feedback;
- review outcome/state writeback;
- rollout strategy;
- observability;
- fail-closed guardrails;
- operational hardening beyond happy-path demonstration.

Expected output:

- production-ready NetPath closure, not just a result viewer plus downstream drafts.

### Phase D: Shared Contract Hardening

Purpose:

- stabilize only the shared contracts that the two application lines have already proven they must depend on.

Primary focus:

- smallest stable `dc2` contract and dataset set required by `IPAM` and `NetPath`;
- field-level quality and provenance rules for application-critical facts;
- version boundaries for shared application dependencies.

Expected output:

- a hardened minimal shared contract, informed by real application closure work rather than broad up-front theory.

## Dependency Matrix

This design should explicitly distinguish three dependency classes.

### Shared Foundation Dependencies

These are common to both application lines:

- `dc2 canonical facts`
- latest fact read seam
- quality / validity / confidence semantics
- provenance semantics
- tenant-safe scope enforcement

Important rule:

- both applications depend on a minimal usable shared fact layer;
- neither application should be blocked on a full shared-contract expansion.

### Application Closure Dependencies

`IPAM` depends on:

- address-bearing fact projection inputs such as `interface_ip`, `arp`, and selected `mac` evidence;
- `ipam_address_fact`;
- audit finding generation;
- frontend-operable allocation, reclaim, and audit journeys.

`NetPath` depends on:

- durable snapshot persistence and retrieval;
- snapshot-first analyze;
- result presentation;
- evidence drill-down;
- minimal policy fact consumption;
- downstream probe/ticket closure surface.

### Release-Level Dependencies

These apply only at the relevant closure gate:

- smoke coverage
- acceptance evidence
- rollback/guardrail posture
- observability
- launch or demo gate criteria

## Phase Dependencies

Recommended dependency structure:

```text
Phase A: IPAM Launch Closure
  depends on:
    - minimal dc2 fact projection inputs
    - current IPAM frontend/backend operational flows
  does not depend on:
    - NetPath policy closure
    - NetPath downstream execution feedback

Phase B: NetPath Demo Closure
  depends on:
    - durable snapshot persistence
    - snapshot-first analyze
    - minimal policy closure
    - result/evidence presentation chain
  does not depend on:
    - full production rollout hardening
    - full shared contract dictionary

Phase C: NetPath Production Closure
  depends on:
    - Phase B complete
    - downstream execution feedback
    - review writeback
    - guardrail and observability posture

Phase D: Shared Contract Hardening
  depends on:
    - Phase A and B exposing real stable consumer needs
```

Core design principle:

- applications should expose stable contract needs;
- the shared contract should then be hardened around those proven needs.

## Unified Delivery Gates

Use one shared status vocabulary across both lines, but allow different final readiness labels.

### Common Status Vocabulary

- `planned`
- `source-level complete`
- `verified`
- `integrated`
- `ready`

Meaning:

#### `planned`

- direction exists;
- no trustworthy implemented chain exists yet.

#### `source-level complete`

- the main source path exists;
- code or UI surface is present;
- but closure evidence is still incomplete.

#### `verified`

- targeted tests, smokes, or evidence confirm the intended behavior;
- validation is still potentially local or partial.

#### `integrated`

- the upstream and downstream chain is connected;
- the feature does not only work in isolation.

#### `ready`

- final release gate for that application level is satisfied.

### Application-Specific Ready States

#### IPAM `launch-ready`

Requirements:

- resource, allocation, reclaim, and audit flows are all frontend-operable;
- fact projection to findings is visible and meaningful;
- smoke is repeatable;
- evidence is sufficient for launch review.

#### NetPath `demo-ready`

Requirements:

- snapshot -> analyze -> result -> evidence chain is complete;
- at least one downstream probe/ticket consumer chain is demonstrable;
- minimal policy closure is in place so the system does not silently over-claim “allowed.”

#### NetPath `production-ready`

Requirements:

- demo-ready chain already exists;
- downstream execution feedback is visible;
- review outcome or action state is written back;
- rollout, guardrail, and observability posture are acceptable for production use.

## Recommended Execution Order

Recommended sequence:

```text
Step 1: close IPAM to launch-ready
  -> produce the first launch-ready business closure sample

Step 2: close NetPath to demo-ready
  -> produce the first demo-ready analysis closure sample

Step 3: close NetPath to production-ready
  -> add execution feedback, rollout, guardrails, observability

Step 4: harden the minimal shared contract
  -> stabilize only the application-proven shared facts and fields
```

This ordering is intentional.

It avoids the less effective sequence:

```text
first finish the full dc2 contract
  -> then finish IPAM
  -> then finish NetPath
```

Why that sequence is not recommended:

- it turns closure work into a bottom-up platform rewrite;
- it delays visible application closure outcomes;
- it encourages a contract dictionary broader than what current applications can actually justify.

## Parallelism Policy

This master design still allows partial parallel work, but only inside boundaries.

Safe parallelism:

- `IPAM` launch-hardening work may continue while `NetPath` demo-closure design progresses;
- `NetPath` result/evidence work may progress while downstream execution-feedback work remains deferred;
- shared-contract note-taking may happen in parallel, but hardening should wait for proven application needs.

Unsafe parallelism:

- broadening `dc2` into a full dictionary while both application closures are still moving;
- simultaneously expanding NetPath policy scope, result UX, downstream execution, and production hardening with no phase boundary;
- letting IPAM and NetPath each define their own new fact semantics during closure work.

## Minimal Shared Contract Set

When Phase D begins, the first hardened set should stay intentionally small.

Recommended first set:

- `route_table`
- `interface_ip`
- `arp / mac`
- `topology adjacency`
- `policy seed`

This set is recommended because it directly supports the two application lines being closed now.

## Risks

### Risk 1: Documents Expand Faster Than Integration

If each phase creates more planning artifacts than integrated outcomes, the program will appear aligned while implementation remains fragmented.

Mitigation:

- keep the master design short;
- require each phase to produce its own focused spec and plan;
- maintain status using shared gate vocabulary.

### Risk 2: Shared Contract Becomes The New Bottleneck

If `dc2` hardening is treated as a precondition for all application closure, both application lines will stall behind platform design work.

Mitigation:

- harden only the minimal contract set;
- let applications prove what must be stable first.

### Risk 3: NetPath Scope Expands In Too Many Directions

NetPath can easily widen into policy, UI, evidence, probes, tickets, rollout, and runtime hardening all at once.

Mitigation:

- separate demo-ready and production-ready;
- do not mix them in the same implementation plan.

### Risk 4: IPAM Appears Closer Than It Really Is

IPAM already has many visible flows, which can hide remaining launch-hardening gaps around projection, audit stability, and repeatable smoke.

Mitigation:

- treat launch gate and evidence as first-class closure work, not final polish.

## Recommended Next Documents

After this master design is approved, the next design documents should be:

1. `IPAM launch closure` focused spec
2. `NetPath demo closure` focused spec
3. later, `NetPath production closure` focused spec
4. after those, a `minimal dc2 contract hardening` spec

Each one should stay phase-local and should not re-open the full dual-line control-plane discussion.

## Final Recommendation

The most effective closure strategy is:

```text
IPAM first as the launch-ready sample
  -> NetPath second as the demo-ready sample
  -> NetPath third as the production-ready sample
  -> shared contract hardening last as a minimal proven foundation
```

This gives OneOPS two clearer platform stories:

- a resource-governance closure sample
- an analysis-closure sample

And it keeps the shared fact foundation tied to real application closure rather than speculative platform breadth.
