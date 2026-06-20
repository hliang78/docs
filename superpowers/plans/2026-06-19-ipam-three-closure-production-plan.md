# IPAM Three-Closure Production Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan as one continuous long task. Do not split into small unrelated tasks. Acceptance is based on user journeys.

**Goal:** Turn IPAM from a visible MVP into a practical production tool by completing three frontend-operable and backend-meaningful closures: resource closure, allocation closure, and audit closure.

**Architecture:** Planning nodes remain planning baseline, Prefix remains subnet master data, address pool/reservation/request/IP/fact/finding remain operational objects. The frontend must guide users through real actions, not explain concepts without enabling work. Backend rules must enforce what the frontend promises.

**Tech Stack:** OneOPS Go backend, MySQL, Vue 3, TypeScript, Ant Design Vue, existing OneOPS API/request patterns, `smoke:ipam-journey`, `smoke:ipam-operation`.

---

## Core Diagnosis

The current IPAM is close to a usable pilot, but not yet a truly practical production tool. Its risk is not missing pages. Its risk is that some frontend interactions still explain concepts instead of completing work.

A practical IPAM must let users answer and act on these questions:

- Which planned address segment can become assignable inventory?
- Which Prefix is the authoritative subnet master data?
- Which address pool can safely allocate?
- Which IP is assigned, reserved, releasing, available, or risky?
- Which observed fact created a real audit finding?
- Which finding has been resolved, and what changed after resolution?

If an interface element does not help answer or act on one of these questions, it should be removed, moved to secondary help, or rewritten as a concrete next action.

## Frontend Copy Policy

Remove or avoid these in primary flows:

- Concept-only explanations that do not lead to an action.
- MVP/demo/temporary wording.
- Future-tense promises such as "后续开放" or "未来接入".
- Generic empty states like "暂无数据".
- Alerts that restate the section title.
- Flow labels that imply approval processes where OneOPS does not implement them.

Keep or add these:

- Action consequences: what happens if the user submits.
- Blocking reasons: why a button is disabled or a request failed.
- Source boundaries: planned data, Prefix master data, observed facts, audit findings.
- Next actions: create Prefix, create pool, submit request, generate finding, resolve finding.
- Stable status semantics: available, reserved, assigned, releasing, unresolved, resolved.

## Closure 1: Resource Closure

### User journey

A planner starts from planned address space, converts a usable segment into Prefix master data or binds an existing Prefix, creates an address pool, and reserves protected ranges.

### Practical acceptance

- Planning node list has a concrete action: `关联 Prefix` or `从此节点建池`.
- If no Prefix exists, the frontend gives one next action, not a concept explanation.
- Address pool creation cannot submit planning node code as `prefix_code`.
- Prefix selector shows name/code/tenant/VRF/CIDR in an operator-readable way.
- Address pool creation explains only operational consequences: assignable range, fixed allocation policy, disabled/enabled state.
- Reserved range creation enforces pool boundary and overlap rules through backend validation.

### Implementation tasks

- [ ] Replace passive planning-to-Prefix copy with concrete row actions.
- [ ] Add or expose `关联 Prefix` action for planning node rows.
- [ ] Add guarded `生成 Prefix` action only if existing Prefix create API has enough fields.
- [ ] Keep `从此节点建池` but make Prefix binding the first required step in the drawer.
- [ ] Remove explanatory alerts that repeat conceptual model after actions are clear.
- [ ] Extend operation smoke to verify planning node to pool drawer requires Prefix.

## Closure 2: Allocation Closure

### User journey

A requester selects an enabled pool, submits an allocation request, an operator executes allocation, and the allocated IP becomes visible and traceable.

### Practical acceptance

- Disabled pools are not selectable by default and backend rejects them.
- Missing required fields show page-level feedback.
- Exhausted pool, reserved preferred IP, invalid preferred IP, and disabled pool errors are understandable.
- Completed request shows allocated IP without requiring users to inspect raw API data.
- Address list or request table gives a clear path to inspect the allocated IP.
- Release/reclaim starts from a real assigned IP and returns it to available inventory.

### Implementation tasks

- [x] Hide disabled pools from default allocation candidates.
- [x] Keep allocation validation and backend errors visible in page.
- [ ] Add result affordance: after allocation, show allocated IP as a clickable/searchable value.
- [ ] Add operation smoke for submit request failure and fact failure.
- [ ] Add operation smoke with timestamped data for allocation success when fixture data is available.
- [ ] Add route or filter handoff from allocation result to address list.

## Closure 3: Audit Closure

### User journey

Observed fact enters the system, generates or updates a real audit finding, operator resolves it, and the resolved state changes what appears as unresolved risk.

### Practical acceptance

- Manual fact upsert has a production reason: operations supplement and verification.
- Automatic collection is the primary source, but frontend should not pretend to run collection.
- Fact fields have operational meaning: IP, source, observed status, VRF, pool, device/interface, MAC, confidence.
- Generating findings returns one of three meaningful results:
  - new finding created,
  - existing unresolved finding updated,
  - no risk found.
- Resolving a finding removes it from unresolved risk counts.
- Repeated observations update unresolved findings and do not create noise.
- Resolved findings do not suppress future real risks.

### Implementation tasks

- [x] Explain automatic collection as primary source and manual upsert as supplement.
- [x] Keep repeated observations deduplicated for unresolved findings.
- [x] Keep resolved findings outside duplicate suppression.
- [x] Make generate-finding response visible with created/updated/no-risk semantics where backend response allows it.
- [ ] Add operation smoke for fact validation feedback.
- [ ] Add operation smoke with timestamped fact to generate and resolve a finding.
- [ ] Ensure overview unresolved audit count matches resolved status semantics.

## Visual and UX Direction

- Keep OneOPS control-room style: compact, calm, explicit.
- Reduce alerts. Use them only for consequences, blockers, or operation results.
- Keep tables dense but pair every empty table with a next action.
- Prefer row actions over separate explanatory sections.
- Keep mutation actions close to the data row they affect.
- Keep names prominent, codes visible, and status labels textual.

## Acceptance Commands

Frontend baseline:

```bash
cd /Users/huangliang/project/OneOPS-ALL/OneOPS-UI
npm run typecheck
npm run smoke:ipam-journey
npm run smoke:ipam-operation
```

Backend targeted checks:

```bash
cd /Users/huangliang/project/OneOPS-ALL/OneOps
go test ./app/ipam/service/impl -run 'TestEnsureAddressPoolAllocatable|TestReservedRange|TestValidateReclaimable|TestIPAMStatisticsUtilization|TestIsDuplicateOpenFinding'
```

## Stop Conditions

Stop and ask before changing any of these product decisions:

- Making planning node a subnet master record instead of Prefix.
- Replacing platform VRF semantics.
- Changing security zone from manual input to a source-backed selector.
- Introducing a formal approval workflow.
- Writing destructive smoke data cleanup.

## 2026-06-19 08:37 Closure checkpoint

Completed in current long-task pass:

- Resource closure is now smoke-covered from the frontend: when no enabled address pool exists, operation smoke creates an enabled pool from existing Prefix master data through the IPAM overview drawer.
- Allocation closure is now smoke-covered from the frontend: operation smoke submits an allocation request and executes allocation from the IP allocation flow.
- Audit closure is now smoke-covered from the frontend: operation smoke creates a manual fact, manually generates/updates a finding, and confirms the finding resolved.
- UX hardening added for immediate visibility: newly submitted allocation requests, allocated results, manual facts, generated findings, and resolved findings stay visible without relying on table reload ordering.
- Address pool creation now auto-fills IPv4 usable start/end addresses after Prefix selection when the fields are empty.

Latest evidence:

- `npm run typecheck`: PASS after Vue component changes.
- `npm run smoke:ipam-journey`: PASS.
- `npm run smoke:ipam-operation`: PASS with resource, allocation, and audit closures.

## 2026-06-19 08:50 Reclaim closure checkpoint

Completed in this pass:

- Reclaim flow now has page-level operation feedback for release and reclaim, not only toast notifications.
- Operation smoke now continues from the allocation request created in the same run, releases the allocated IP, confirms reclaim, and verifies visible page feedback.
- Reclaim smoke is scoped to the current run's `SMOKE-<timestamp>` owner code to avoid acting on unrelated historical data.

Latest evidence:

- `npm run typecheck`: PASS.
- `npm run smoke:ipam-operation`: PASS with resource, allocation, reclaim, and audit closures.
- `npm run smoke:ipam-journey`: PASS.

## 2026-06-20 Canonical fact projection checkpoint

Completed in this pass:

- Checked `lifecycle_status` test baseline drift for IPAM: current IPAM handwritten `ip_address` test schemas and model/generated query already use `lifecycle_status`, and `go test ./app/ipam/...` passes.
- Added a service-layer projection entry from DC2 canonical facts into IPAM address facts: `IPAddressFactSrv.ProjectCanonicalFacts`.
- Projection currently supports address-bearing canonical facts:
  - `interface_ip` -> `ipam_address_fact`
  - `arp_entry` -> `ipam_address_fact`
- `mac_table_entry` without IP is intentionally skipped for direct address fact creation. It remains useful later as enrichment/correlation evidence, not as a standalone IP fact.
- Canonical provenance is preserved through compact `RawData` / `RawRef` metadata keys for fact type, identity key, target id, contract key, dataset key, and processor key.
- Projection reuses existing IPAM `BatchUpsert`, so it keeps current validation, normalization, deduplication, confidence, first/last seen, and page/audit semantics.

Latest evidence:

- RED first: projection tests failed because conversion function and canonical metadata fields were missing.
- GREEN: `go test ./app/ipam/service/impl -run 'TestProjectCanonical|TestBuildIPAddressFactRawRef|TestNormalizeIPAddressFactReq'`: PASS.
- Regression: `go test ./app/ipam/service/impl -run 'TestEnsureAddressPoolAllocatable|TestReservedRange|TestValidateReclaimable|TestIPAMStatisticsUtilization|TestIsDuplicateOpenFinding|TestIPAddressFact|TestProjectCanonical'`: PASS.
- Package baseline: `go test ./app/ipam/...`: PASS.

Known non-IPAM baseline noise:

- `go test ./app/...` currently surfaces unrelated vet failures in `app/pipeline/activity` (`fmt.Sprintf` / `fmt.Errorf` formatting issues). This is separate from IPAM lifecycle schema and projection work.

## 2026-06-20 Canonical latest projection checkpoint

Completed in this pass:

- Added a manual projection API: `POST /ipam/address-facts/project-canonical-latest`.
- The API reads DC2 latest canonical facts and projects them into `ipam_address_fact` through the IPAM projection service.
- Default projection scope is intentionally narrow and address-bearing only:
  - `interface_ip`
  - `arp_entry`
- A caller may specify `fact_type` explicitly, but unsupported/non-address facts are still skipped by the IPAM projection layer.
- Projection defaults to valid DC2 facts only. `include_invalid=true` can be used for diagnostics, but this is not the normal production path.
- Added frontend operation entry on the IPAM fact/audit page: `同步采集事实`.
- Manual sync keeps current product decision intact: facts are synchronized on demand; audit findings are still generated manually from fact rows.

Latest evidence:

- API RED first: default projection fact-type tests failed before helper existed.
- Backend GREEN: `go test ./app/ipam/api -run 'TestCanonicalLatestProjectionFactTypes'`: PASS.
- Backend package and initialize: `go test ./app/ipam/... ./initialize`: PASS.
- Frontend typecheck: `npm run typecheck`: PASS.
- Journey smoke: first run hit Chrome debug-port startup flake; rerun with `IPAM_CHROME_PORT=9254` PASS.
- Operation smoke: first run hit Chrome debug-port startup flake; rerun with `IPAM_OPERATION_CHROME_PORT=9255` PASS.

Known follow-up:

- Stabilize smoke scripts by choosing a free Chrome debugging port dynamically instead of relying on fixed `9234` / `9235` defaults.
