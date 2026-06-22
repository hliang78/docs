# OneOPS IPAM Launch Closure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close IPAM to `launch-ready` by stabilizing projection-to-finding behavior, hardening allocation/reclaim/audit journeys, and proving repeatable launch evidence.

**Architecture:** Keep existing IPAM vertical slices intact and close the remaining gaps through focused closure work: fact projection/audit stabilization, operational-flow hardening, and launch-gate evidence. Avoid broad new feature work while this closure phase is active.

**Tech Stack:** OneOPS Go backend, Vue frontend, IPAM service tests, smoke scripts, evidence docs.

---

## File Structure

- `OneOps/app/ipam/service/impl/ip_address_fact.go`
  - Canonical fact projection into `ipam_address_fact`, provenance persistence, and request normalization.
- `OneOps/app/ipam/service/impl/ip_address_fact_test.go`
  - Focused projection and provenance regression coverage.
- `OneOps/app/ipam/service/impl/ip_address_audit_finding.go`
  - Finding generation, duplicate-open suppression, and explainable mismatch handling.
- `OneOps/app/ipam/service/impl/ip_address_audit_finding_test.go`
  - Focused finding-generation and duplicate-noise regression coverage.
- `OneOps/app/ipam/service/impl/ip_address_request.go`
  - Allocation, release, reclaim, and request lifecycle hardening.
- `OneOps/app/ipam/service/impl/ip_address_request_test.go`
  - Allocation/reclaim lifecycle and guardrail regression coverage.
- `OneOps/app/ipam/service/impl/ipam_statistics.go`
  - Launch-facing statistics semantics, especially `releasing` and unresolved audit visibility.
- `OneOps/app/ipam/service/impl/ipam_statistics_test.go`
  - Statistics semantics regression coverage.
- `OneOPS-UI/src/views/ipam/IPAllocationFlow.vue`
  - Allocation request UX, status wording, and error feedback.
- `OneOPS-UI/src/views/ipam/IPReclaimFlow.vue`
  - Release/reclaim UX and visibility of reclaim consequences.
- `OneOPS-UI/src/views/ipam/IPFactAuditFlow.vue`
  - Fact upsert, finding list, resolve action, and frontend-operable audit loop.
- `OneOPS-UI/src/views/ipam/IPAMOverview.vue`
  - Launch-facing risk and statistics visibility after operational mutations.
- `OneOPS-UI/scripts/ipam-journey-smoke.cjs`
  - Browser smoke for end-user IPAM flows.
- `OneOPS-UI/scripts/ipam-operation-smoke.cjs`
  - Mutation-safe operational smoke for allocation, reclaim, fact, and finding flows.
- `docs/evidence/ipam/frontend-journeys/`
  - Existing UI evidence snapshots that should be refreshed when launch closure is re-verified.
- `docs/evidence/ipam/operation-smoke/`
  - Existing mutation-smoke evidence that should be refreshed with a final launch-ready run.
- Create: `docs/evidence/ipam/launch-closure/2026-06-22-readiness-summary.md`
  - One short readiness note collecting the final backend, frontend, and evidence results for the launch gate.

### Task 1: Projection And Finding Stabilization

**Files:**
- Modify: `OneOps/app/ipam/service/impl/ip_address_fact.go`
- Modify: `OneOps/app/ipam/service/impl/ip_address_fact_test.go`
- Modify: `OneOps/app/ipam/service/impl/ip_address_audit_finding.go`
- Modify: `OneOps/app/ipam/service/impl/ip_address_audit_finding_test.go`
- Modify if needed: `OneOPS-UI/src/views/ipam/IPFactAuditFlow.vue`

- [ ] **Step 1: Lock the projection/finding contract in tests**

Read the current focused coverage in:
- `OneOps/app/ipam/service/impl/ip_address_fact_test.go`
- `OneOps/app/ipam/service/impl/ip_address_audit_finding_test.go`

Then extend the tests so this closure phase explicitly proves:
- canonical `interface_ip` projection keeps source provenance visible;
- canonical `arp` projection keeps source provenance visible;
- duplicate open findings are updated or suppressed instead of multiplied;
- ambiguous planned matches still produce explainable finding output instead of silent success.

- [ ] **Step 2: Implement the minimal backend stabilization**

Adjust only the projection and finding paths needed to make the new tests pass:
- `projectCanonical*` helpers in `ip_address_fact.go`;
- provenance/raw-ref handling in `ip_address_fact.go`;
- duplicate-open finding and candidate-generation logic in `ip_address_audit_finding.go`.

Do not add new fact families or new audit workflows in this phase.

- [ ] **Step 3: Verify the focused backend regression set**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps && go test ./app/ipam/service/impl -run 'Test(ProjectCanonicalInterfaceIPFactToIPAddressFactReq|ProjectCanonicalARPFactToIPAddressFactReq|ProjectDC2FactRecordPreservesLatestFactProvenance|IsDuplicateOpenFinding|IPAddressAuditFindingGenerateCandidatesAmbiguousPlannedMatchStillReportsDuplicateObservation)' -count=1
```

Expected:
- all listed projection/finding tests PASS;
- no new duplicate-finding or provenance regressions appear in the targeted run.

- [ ] **Step 4: Verify the frontend audit surface still matches the backend**

If backend payload or semantics changed, update only the minimal corresponding logic in:
- `OneOPS-UI/src/views/ipam/IPFactAuditFlow.vue`

Then run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOPS-UI && npm run smoke:ipam-operation
```

Expected:
- fact validation feedback remains visible;
- finding creation and resolve flow still complete without UI contract breakage.

### Task 2: Allocation/Reclaim/Audit Journey Hardening

**Files:**
- Modify: `OneOps/app/ipam/service/impl/ip_address_request.go`
- Modify: `OneOps/app/ipam/service/impl/ip_address_request_test.go`
- Modify: `OneOps/app/ipam/service/impl/ipam_statistics.go`
- Modify: `OneOps/app/ipam/service/impl/ipam_statistics_test.go`
- Modify: `OneOPS-UI/src/views/ipam/IPAllocationFlow.vue`
- Modify: `OneOPS-UI/src/views/ipam/IPReclaimFlow.vue`
- Modify: `OneOPS-UI/src/views/ipam/IPFactAuditFlow.vue`
- Modify: `OneOPS-UI/src/views/ipam/IPAMOverview.vue`
- Modify: `OneOPS-UI/scripts/ipam-journey-smoke.cjs`
- Modify: `OneOPS-UI/scripts/ipam-operation-smoke.cjs`

- [ ] **Step 1: Close the remaining backend lifecycle and guardrail gaps**

Use the existing tests in `ip_address_request_test.go` and `ipam_statistics_test.go` as the baseline, then add or finish coverage for:
- disabled-pool allocation rejection;
- reserved-IP and preferred-IP rejection paths;
- release to `releasing` transition;
- reclaim back to `available`;
- statistics that continue treating `releasing` as blocked capacity.

- [ ] **Step 2: Make the user-facing flows reflect the stabilized lifecycle**

Update only the journey pages required for launch closure:
- `IPAllocationFlow.vue`
- `IPReclaimFlow.vue`
- `IPFactAuditFlow.vue`
- `IPAMOverview.vue`

The frontend should visibly prove:
- request status and assigned address visibility;
- release/reclaim consequences and refresh behavior;
- unresolved audit risk and lifecycle counts after mutation.

- [ ] **Step 3: Verify targeted backend lifecycle tests**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps && go test ./app/ipam/service/impl -run 'Test(EnsureAddressPoolAllocatableRejectsDisabledPool|EnsureAddressPoolAllocatableAllowsEnabledPool|ValidateReclaimable|ApplyReclaimToAvailable|IPAMStatisticsUtilizationTreatsReleasingAsBlocked)' -count=1
```

Expected:
- allocation/reclaim/statistics lifecycle tests PASS;
- no regression in disabled-pool and reclaim semantics.

- [ ] **Step 4: Verify the browser and operation smoke flows**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOPS-UI && npm run smoke:ipam-journey && npm run smoke:ipam-operation
```

Expected:
- journey smoke still enters overview, allocation, reclaim, and fact/audit flows;
- operation smoke proves submit -> complete -> release -> reclaim -> finding -> resolve without manual repair between steps.

### Task 3: Launch Evidence And Gate Review

**Files:**
- Modify if needed: `OneOPS-UI/scripts/ipam-journey-smoke.cjs`
- Modify if needed: `OneOPS-UI/scripts/ipam-operation-smoke.cjs`
- Create: `docs/evidence/ipam/launch-closure/2026-06-22-readiness-summary.md`

- [ ] **Step 1: Run the full closure verification set**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps && go test ./app/ipam/... -count=1
```

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOPS-UI && npm run typecheck && npm run smoke:ipam-journey && npm run smoke:ipam-operation
```

Expected:
- backend IPAM package tests PASS;
- frontend typecheck PASS;
- both smoke commands PASS in the same round.

- [ ] **Step 2: Refresh the launch evidence set**

Update `docs/evidence/ipam/frontend-journeys/` and `docs/evidence/ipam/operation-smoke/` with the latest successful run artifacts.

At minimum, evidence should show:
- allocation request completion;
- release and reclaim completion;
- finding generation and resolve completion;
- overview/audit visibility after the mutations.

- [ ] **Step 3: Write the launch gate summary**

Create `docs/evidence/ipam/launch-closure/2026-06-22-readiness-summary.md` with:
- exact commands run;
- pass/fail status;
- links or relative paths to refreshed evidence artifacts;
- any remaining blockers that still prevent marking IPAM `launch-ready`.

- [ ] **Step 4: Mark the phase complete only if all launch gates are satisfied**

Do not treat this phase as closed unless all of these are true:
- projection/finding behavior is explainable from canonical fact provenance;
- allocation, reclaim, and audit flows are frontend-operable end to end;
- backend tests and frontend smoke pass in one fresh round;
- evidence is written in a form suitable for a launch review.
