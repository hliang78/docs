# OneOPS Fact Application Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a shared fact-to-application foundation so L2 snapshot, IPAM, NetPath, RCA, and topology features consume consistent facts, batches, snapshots, readiness, provenance, and quality semantics.

**Architecture:** Use existing OneOPS foundations instead of creating a parallel platform. DC2 canonical facts become the shared fact layer, obsflow remains the batch and snapshot mainline, IPAM becomes the first business application projection, L2 snapshot remains the reference publish/apply path, and NetPath consumes engine-ready snapshots after route facts are available.

**Tech Stack:** Go, Gin, GORM, MySQL, Vue, Ant Design Vue, existing `OneOPS/app/device_collection2`, `OneOPS/app/obsflow`, `OneOPS/app/ipam`, `OneOPS/app/topology`, `OneOPS/app/netpath`, and `oneops-netpath`.

---

## Tracking Rules

- This is a master tracking plan, not one giant implementation story.
- Every phase must get its own focused design or implementation plan before code changes.
- Keep all follow-up plans under `docs/superpowers/plans/`.
- Keep design decisions under `docs/superpowers/specs/` unless they are short phase notes in this file.
- Do not publish OpenClaw stories from this document. This track is managed through superpowers docs and execution modes.
- Report progress with this structure:

```text
Current phase:
- Phase N: <name>

Code facts used:
- ...

Completed:
- ...

Validation:
- ...

Next:
- ...
```

## Current Baseline

### Completed Foundations

- Obsflow has `collection_run`, `observation_batch`, `processing_run`, and `l2_topology_snapshot` models and APIs.
- Obsflow kernel validates batches, starts processing runs, executes registered tasks, saves snapshots, and updates run state.
- Device Collection 2 has canonical fact records, latest projections, quality, provenance, issue records, and processors for several network facts.
- IPAM has address planning, pools, reserved ranges, request/allocation/release/reclaim, facts, audit findings, statistics, and frontend work areas.
- Topology can read ready L2 snapshots and merge them with existing topology, overlays, manual edges, and coordinates.
- NetPath has standalone engine, OneOPS service/API skeleton, engine port, SDK adapter scaffold, and preview snapshot builder.

### Main Gaps

- Canonical fact registry is implicit in code, not documented or enforced as a shared contract.
- IPAM observed facts are not yet clearly a projection from canonical DC2 facts.
- `route_table` canonical fact and the first NetPath tenant-safe latest-fact reader seam now exist in the worktree; production NetPath use is still blocked by tenant-authorized device scope resolution and SnapshotProvider durable-run wiring.
- Snapshot semantics are still L2-specific; reuse rules for IPAM and NetPath are not settled.
- Tenant scoping for latest facts needs explicit design and tests.
- NetPath OneOPS integration lacks full router registration, durable run persistence, and frontend result workflow.

## File Map

Primary design and tracking files:

- `docs/superpowers/specs/2026-06-19-oneops-fact-application-foundation-design.md`: shared design.
- `docs/superpowers/plans/2026-06-19-oneops-fact-application-foundation-master-plan.md`: this master plan.

Core code areas:

- `OneOPS/app/device_collection2/fact/`: canonical fact processors.
- `OneOPS/app/device_collection2/model/fact.go`: canonical fact persistence models.
- `OneOPS/app/device_collection2/api/device_collection2.go`: fact query APIs.
- `OneOPS/app/obsflow/`: batch, processing, snapshot, workflow mainline.
- `OneOPS/app/ipam/`: IPAM application models and workflows.
- `OneOPS/app/topology/`: topology consumption of L2 snapshots.
- `OneOPS/app/netpath/`: OneOPS path analysis integration.
- `oneops-netpath/`: standalone deterministic path engine.

## Phase 1: Canonical Fact Contract Freeze

Status: implemented in isolated worktree; pending integration.

Purpose:

- Turn the existing DC2 fact shape into an explicit shared contract that upper applications can rely on.

Scope:

- Document fact identity rules.
- Define required fields for initial fact types.
- Add tests for processor identity, quality, provenance, and latest projection behavior where gaps exist.

Fact types:

- `device_identity`
- `interface`
- `interface_ip`
- `topology_neighbor`
- `mac_table`
- `arp_entry`
- `route_table`

Deliverables:

- [ ] Phase design note under `docs/superpowers/specs/`.
- [ ] Fact type registry document.
- [ ] Test inventory for existing processors.
- [ ] Gaps list for missing processors and weak identity keys.

Exit criteria:

- Every initial fact type has documented identity key rules.
- Every fact type states which application can consume it.
- Existing processor tests confirm quality and provenance are not silently omitted.

## Phase 2: IPAM Fact Projection

Status: planned.

Purpose:

- Make IPAM the first complete business application over shared canonical facts.

Scope:

- Define projection from canonical facts to `ipam_address_fact`.
- Preserve IPAM workflow ownership of planning, allocation, reclaim, and audit decisions.
- Keep source references visible for audit findings.

Projection sources:

- `interface_ip`
- `mac_table`
- future `arp_entry`
- optional existing `IPAMAgg`

Deliverables:

- [ ] Phase implementation plan under `docs/superpowers/plans/`.
- [ ] Projection service design.
- [ ] Backend tests for projection idempotency and source metadata.
- [ ] IPAM audit generation tests from projected facts.
- [ ] Frontend evidence that fact source context is visible in `IPFactAuditFlow`.

Exit criteria:

- A canonical `interface_ip` fact can create or update an IPAM observed fact.
- Re-running projection is idempotent.
- Audit findings include source fact or raw reference context.
- IPAM statistics update after projection and finding resolution.

## Phase 3: L2 Snapshot As Reference Publish Path

Status: planned.

Purpose:

- Keep L2 snapshot as the model implementation of batch-to-snapshot publication.

Scope:

- Tighten snapshot summary contracts for DevicePorts, L2nodeMapServer, and ArpMac.
- Ensure topology consumers can display source snapshot and readiness.
- Keep apply behavior explicit and fail loudly when snapshot is not ready.

Deliverables:

- [ ] Snapshot contract document for L2 application consumers.
- [ ] Tests for required snapshot fields.
- [ ] UI evidence showing selected snapshot, readiness, and source batch.
- [ ] Apply-path validation for unsupported snapshot tasks.

Exit criteria:

- Topology can identify whether data came from physical relation, manual overlay, or ready L2 snapshot.
- Consumers can rely on stable fields for edge count, device codes, collections used, and association issues.
- Snapshot apply never treats non-ready data as successful.

## Phase 4: Route Table Canonical Fact

Status: planned.

Purpose:

- Fill the largest missing fact required by NetPath and future L3 topology work.

Required fields:

```text
vrf
destination
next_hop_ip
out_interface
protocol
metric
preference
null_route
raw
```

Deliverables:

- [x] Route table fact schema design.
- [x] Processor tests for normalized route rows.
- [x] Dataset contract for at least one network-device route source.
- [x] Latest route fact history/latest/issue tests.
- [x] DC2-shaped fixture that can feed NetPath snapshot assembly.
- [ ] Tenant-safe latest-fact reader/provider seam for production consumption.

Exit criteria:

- OneOPS can ingest or collect route rows into canonical `route_table` facts.
- Invalid route prefixes become fact issues, not accepted facts.
- NetPath snapshot provider can assemble DC2-shaped route facts without hand-written route models.
- Production NetPath route consumption does not use unscoped latest-fact reads.

## Phase 5: NetPath Engine-Ready Snapshot And Run Persistence

Status: planned after Phase 4.

Purpose:

- Turn NetPath from skeleton integration into a durable OneOPS application.

Scope:

- Build production snapshot provider from canonical facts.
- Wire analysis engine path explicitly.
- Persist analysis runs, traces, hops, steps, diagnostics, and disposition.
- Register routes only after service wiring is production-safe.

Deliverables:

- [ ] Phase implementation plan under `docs/superpowers/plans/`.
- [ ] Durable run persistence model review.
- [ ] Snapshot provider tests for ready, degraded, and blocked states.
- [ ] API tests for create/get analysis run.
- [ ] Smoke fixture from facts to path result.

Exit criteria:

- A user can submit a concrete flow and retrieve a persisted path result.
- Result includes snapshot ID, flow, disposition, hops, route lookup steps, and diagnostics.
- Missing route or topology data produces blocked/degraded diagnostics instead of fake success.

## Phase 6: Cross-Application Evidence Drilldown

Status: future.

Purpose:

- Make fact provenance visible to operators across IPAM, topology, NetPath, and RCA.

Scope:

- Shared evidence DTOs.
- Fact source lookup by application result.
- UI entry points from IPAM audit and NetPath trace steps.

Deliverables:

- [ ] Evidence DTO design.
- [ ] Backend lookup API plan.
- [ ] IPAM fact drilldown smoke.
- [ ] NetPath route-step evidence smoke.

Exit criteria:

- Operator can trace an application result back to collection run, fact type, identity key, source fields, and observed time.

## Phase 7: RCA And Network Ops Agent Consumption

Status: future.

Purpose:

- Let RCA and network ops AI consume published snapshots and evidence instead of raw, unstable intermediate data.

Scope:

- RCA input bundles reference snapshots and canonical facts.
- Network ops agent can ask for topology, path, IPAM, and evidence through stable application APIs.

Deliverables:

- [ ] RCA input contract update.
- [ ] Agent read-only query contract.
- [ ] End-to-end diagnostic scenario using L2 snapshot, IPAM fact, and NetPath result.

Exit criteria:

- RCA and agent flows can explain which facts and snapshots were used.

## Risk Register

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Applications keep inventing local facts | Duplicate models and inconsistent results | Freeze canonical fact contract before new application projections |
| IPAM facts diverge from DC2 facts | Audit becomes hard to trust | Make `ipam_address_fact` a projection with source metadata |
| Route facts are delayed | NetPath remains demo-only | Prioritize Phase 4 before NetPath UI work |
| Snapshot abstraction becomes too generic too early | Over-design slows delivery | Keep typed snapshots until reuse pressure is concrete |
| Tenant scoping is implicit | Data leakage or wrong analysis | Add explicit tenant tests for latest fact readers |
| NetPath engine is wired before data quality is ready | False confidence in path results | Use ready/degraded/blocked snapshot quality gates |

## Current Tracking Board

| Phase | Status | Owner Mode | Next Document |
| --- | --- | --- | --- |
| Phase 1: Canonical Fact Contract Freeze | in progress | superpowers design + plan | `docs/superpowers/plans/2026-06-19-oneops-canonical-fact-contract-hardening-phase1.md` |
| Phase 2: IPAM Fact Projection | planning | gpt-5.4 worker | `docs/superpowers/plans/2026-06-19-oneops-ipam-fact-projection-phase2.md` |
| Phase 3: L2 Snapshot Reference Path | planned | superpowers implementation plan | `docs/superpowers/plans/*l2-snapshot-reference*` |
| Phase 4: Route Table Canonical Fact | implemented in worktree; pending integration | gpt-5.4 worker + reviewer | `docs/superpowers/plans/2026-06-19-oneops-route-table-canonical-fact-phase4.md` |
| Phase 5: NetPath Engine-Ready Snapshot | planned | superpowers implementation plan | `docs/superpowers/plans/*netpath-engine-ready-snapshot*` |
| Phase 6: Evidence Drilldown | future | design first | name the follow-up design after Phase 5 evidence requirements are confirmed |
| Phase 7: RCA And Agent Consumption | future | design first | name the follow-up design after Phase 6 evidence APIs are stable |

## First Recommended Next Step

Start with Phase 1.

Reason:

- It is the smallest shared foundation.
- It prevents IPAM, L2 snapshot, and NetPath from drifting further.
- It can be validated mostly with documents and unit tests around existing processors.

Recommended next file:

```text
docs/superpowers/specs/2026-06-19-oneops-canonical-fact-contract-design.md
```
