# OneOPS IPAM Fact Projection Phase 2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Project canonical facts into IPAM observed facts and audit flows without replacing IPAM planning, allocation, request, reclaim, or lifecycle workflow state.

**Architecture:** Add an IPAM-local projection path that reads valid latest canonical facts and materializes application-facing `ipam_address_fact` plus audit evidence. Preserve canonical provenance in structured projection metadata instead of continuing to rely on the current lossy `RawRef` packing, while keeping `ip_address`, `address_pool`, and request/reclaim tables authoritative for planning and workflow decisions.

**Tech Stack:** Go, GORM, MySQL, Vue 3, Ant Design Vue, existing `OneOPS/app/device_collection2`, `OneOPS/app/ipam`, and `OneOPS-UI` modules.

---

## Scope Guardrails

- Phase 2 only projects canonical facts into IPAM observed facts and audit evidence.
- Do not replace or reinterpret `ip_address`, `address_pool`, `ip_address_request`, reclaim flow, or planning nodes as canonical facts.
- Do not make the frontend read Device Collection 2 facts directly.
- Keep existing manual fact upsert and audit workflows working while projected facts are introduced.

## Current Code Facts Driving This Phase

- `OneOPS/app/ipam/service/impl/ip_address_fact.go` currently rebuilds `RawRef` on every upsert and stores only `prefix_code`, `pool_code`, `tenant_code`, `observed_status`, and `raw_data` inside a 255-character packed blob.
- `OneOPS/app/ipam/service/impl/ip_address_audit_finding.go` parses that `RawRef` blob to decide planned matching, stale-planned detection, and duplicate active observation logic.
- `OneOPS-UI/src/views/ipam/IPFactAuditFlow.vue` displays `online` / `offline` / `unknown`, while backend audit helpers currently treat active as `active|reachable|up|on` and inactive as `inactive|down|off|unreachable`.
- Device Collection 2 latest facts already exist in `device_collection2_fact_latest`; `interface_ip` is available now, `arp_entry` exists in processor code, and the current MAC processor emits `mac_table_entry` even though higher-level docs often call the source `mac_table`.
- Current IPAM `RawRef` behavior is lossy and overwrite-prone. Phase 2 needs structured source context or other safe projection metadata so reruns do not silently discard evidence.

## Code Areas Likely To Change

- Modify: `OneOPS/app/ipam/ipam_model/ip_address_fact.go`
- Modify: `OneOPS/app/ipam/ipam_model/ip_address_audit_finding.go`
- Modify: `OneOPS/app/ipam/dto/ip_address_fact.go`
- Modify: `OneOPS/app/ipam/dto/ip_address_audit_finding.go`
- Modify: `OneOPS/app/ipam/service/i_ip_address_fact.go`
- Modify: `OneOPS/app/ipam/service/i_ip_address_audit_finding.go`
- Modify: `OneOPS/app/ipam/service/impl/ip_address_fact.go`
- Create or modify: `OneOPS/app/ipam/service/impl/ip_address_fact_projection.go`
- Create or modify: `OneOPS/app/ipam/service/impl/ip_address_fact_status.go`
- Modify: `OneOPS/app/ipam/service/impl/ip_address_audit_finding.go`
- Modify: `OneOPS/app/ipam/service/impl/ipam_statistics.go`
- Modify: `OneOPS/app/ipam/service/impl/ip_address_fact_test.go`
- Modify: `OneOPS/app/ipam/service/impl/ip_address_audit_finding_test.go`
- Modify: `OneOPS/app/ipam/service/impl/ipam_statistics_test.go`
- Optional modify: `OneOPS/app/ipam/api/ip_address_fact.go`
- Optional modify: `OneOPS/app/ipam/router/ip_address_fact.go`
- Optional modify: `OneOPS/app/device_collection2/api/device_collection2.go`
- Optional modify: `OneOPS/app/device_collection2/service/impl/device_collection2.go`
- Modify: `OneOPS-UI/src/views/ipam/IPFactAuditFlow.vue`
- Modify: `OneOPS-UI/src/api/ipam/ip_address_fact.ts`
- Modify: `OneOPS-UI/src/api/ipam/ip_address_audit_finding.ts`
- Modify: `OneOPS-UI/src/typings/ipam/ip_address_fact.ts`
- Modify: `OneOPS-UI/src/typings/ipam/ip_address_audit_finding.ts`
- Regression-check only: `OneOPS/app/ipam/service/impl/ip_address_request.go`, `OneOPS/app/ipam/service/impl/address_planning.go`, `OneOPS-UI/src/views/ipam/IPAMOverview.vue`

### Task 1: Projection Contract And Metadata Shape

**Files:**
- Modify: `OneOPS/app/ipam/ipam_model/ip_address_fact.go`
- Modify: `OneOPS/app/ipam/dto/ip_address_fact.go`
- Modify: `OneOPS/app/ipam/service/impl/ip_address_fact.go`
- Create or modify: `OneOPS/app/ipam/service/impl/ip_address_fact_projection.go`

- [ ] Freeze the projection input contract around valid latest canonical facts: `interface_ip` as the required anchor, `mac_table_entry` as optional enrichment, and `arp_entry` as the next supported enrichment source.
- [ ] Decide and document the naming rule for MAC evidence so implementation does not drift between design language (`mac_table`) and current code fact type (`mac_table_entry`).
- [ ] Define IPAM projection identity explicitly. Recommended baseline: canonical IP plus VRF scope plus observed owner/interface scope, with reruns from the same canonical fact updating the same `ipam_address_fact` row.
- [ ] Replace `RawRef` as the primary provenance carrier with structured projection metadata. Preserve at minimum `fact_id`, `run_id`, `target_id`, `fact_type`, `identity_key`, `observed_at`, `valid`, `confidence`, `contract_key`, `dataset_key`, `processor_key`, `processor_version`, and `source_fields`.
- [ ] If a full schema change is too invasive for the first slice, add safe projection metadata beside `RawRef` and keep `RawRef` only as a compatibility field. Do not keep the overwrite-only packed query-string model as the long-term source context.
- [ ] Define coexistence rules for manual vs projected fact rows so manual补录 stays available without letting projected reruns wipe out operator-entered evidence.

### Task 2: Backend Projector Entry Point

**Files:**
- Modify: `OneOPS/app/ipam/service/i_ip_address_fact.go`
- Modify: `OneOPS/app/ipam/service/impl/ip_address_fact.go`
- Create or modify: `OneOPS/app/ipam/service/impl/ip_address_fact_projection.go`
- Optional modify: `OneOPS/app/ipam/api/ip_address_fact.go`
- Optional modify: `OneOPS/app/ipam/router/ip_address_fact.go`
- Optional modify: `OneOPS/app/device_collection2/api/device_collection2.go`
- Optional modify: `OneOPS/app/device_collection2/service/impl/device_collection2.go`

- [ ] Add an IPAM-local projection service or projection entry point. Prefer a dedicated projector over teaching manual `Upsert` to impersonate canonical fact ingestion.
- [ ] Use existing latest canonical fact storage as the source of truth. Start with valid `interface_ip` latest facts and only add new Device Collection 2 query surfaces if the current access path is too coarse for batch projection.
- [ ] Map canonical fields into IPAM observed facts conservatively: `ip` and `vrf` into address/VRF scope, interface identity into observed interface fields, device identity into observed device fields, and MAC or ARP evidence into MAC fields plus confidence adjustments.
- [ ] Preserve `FirstSeenAt` as the earliest observed time across reruns and only move `LastSeenAt` forward.
- [ ] Keep projection writes limited to observed-fact and audit-evidence surfaces. Do not let the projector overwrite planned lifecycle, request status, reclaim state, or address ownership decisions in `ip_address`.

### Task 3: Status Vocabulary Normalization

**Files:**
- Create or modify: `OneOPS/app/ipam/service/impl/ip_address_fact_status.go`
- Modify: `OneOPS/app/ipam/service/impl/ip_address_fact.go`
- Modify: `OneOPS/app/ipam/service/impl/ip_address_audit_finding.go`
- Modify: `OneOPS/app/ipam/dto/ip_address_fact.go`
- Modify: `OneOPS-UI/src/views/ipam/IPFactAuditFlow.vue`
- Modify: `OneOPS-UI/src/typings/ipam/ip_address_fact.ts`

- [ ] Introduce one shared normalization path used by projector, fact response builders, and audit finding generation.
- [ ] Normalize source values such as `up/down`, `reachable/unreachable`, and `on/off` into one persisted observed-fact vocabulary. Recommended persisted values: `active`, `inactive`, `unknown`.
- [ ] Keep the UI display vocabulary as `online`, `offline`, `unknown` if desired, but make it a pure presentation mapping over the persisted observed-fact status.
- [ ] Remove the current split where the frontend writes `online/offline` while backend duplicate and stale detection relies on `active/inactive` aliases.
- [ ] Keep planned IPAM address state separate from observed fact state. Audit logic may compare them, but projection must not overwrite planned `IPAddress.Status` or lifecycle fields.

### Task 4: Audit Generation And Evidence Drilldown

**Files:**
- Modify: `OneOPS/app/ipam/ipam_model/ip_address_audit_finding.go`
- Modify: `OneOPS/app/ipam/dto/ip_address_audit_finding.go`
- Modify: `OneOPS/app/ipam/service/i_ip_address_audit_finding.go`
- Modify: `OneOPS/app/ipam/service/impl/ip_address_audit_finding.go`
- Modify: `OneOPS/app/ipam/service/impl/ipam_statistics.go`

- [ ] Update audit candidate generation to read structured projection metadata first, with legacy `RawRef` parsing only as a fallback path during transition.
- [ ] Extend finding DTOs so a finding can expose why it exists: projected fact source, observation time, canonical dataset/processor, and key joined evidence such as device/interface/prefix/VRF.
- [ ] Ensure unplanned, ambiguous planned match, stale planned, owner mismatch, MAC mismatch, and duplicate observation findings still work when the observed fact came from canonical projection instead of manual input.
- [ ] Use projection metadata to improve planned matching before falling back to raw IP-only matching, especially when prefix or VRF evidence is available.
- [ ] Keep overview and statistics aggregation behavior stable after new evidence fields are introduced.

### Task 5: Idempotency And Regression Tests

**Files:**
- Modify: `OneOPS/app/ipam/service/impl/ip_address_fact_test.go`
- Modify: `OneOPS/app/ipam/service/impl/ip_address_audit_finding_test.go`
- Modify: `OneOPS/app/ipam/service/impl/ipam_statistics_test.go`

- [ ] Add projector tests that run the same canonical fact bundle twice and assert no duplicate `ipam_address_fact` rows are created.
- [ ] Assert `FirstSeenAt` never moves forward, `LastSeenAt` only moves forward, and structured source metadata is not narrowed or silently dropped on rerun.
- [ ] Add tests for later canonical updates that change device, interface, or MAC evidence and verify projection merges safely instead of clobbering stable provenance.
- [ ] Add audit tests proving status aliases behave identically across `online`, `active`, `reachable`, `up` and across `offline`, `inactive`, `down`, `unreachable`.
- [ ] Add audit tests proving duplicate observation logic uses normalized active/inactive state plus structured evidence, not only brittle string parsing.
- [ ] Add statistics tests to confirm observed fact counts and unresolved finding counts still aggregate correctly after metadata changes.

### Task 6: Frontend Evidence Visibility

**Files:**
- Modify: `OneOPS-UI/src/views/ipam/IPFactAuditFlow.vue`
- Modify: `OneOPS-UI/src/api/ipam/ip_address_fact.ts`
- Modify: `OneOPS-UI/src/api/ipam/ip_address_audit_finding.ts`
- Modify: `OneOPS-UI/src/typings/ipam/ip_address_fact.ts`
- Modify: `OneOPS-UI/src/typings/ipam/ip_address_audit_finding.ts`
- Regression-check only: `OneOPS-UI/src/views/ipam/IPAMOverview.vue`

- [ ] Expand fact and finding typings so projected evidence can be rendered without exposing opaque blobs.
- [ ] In `IPFactAuditFlow.vue`, surface evidence per fact row: source type, canonical fact type, dataset or processor, observed time, and joined device/interface/prefix/VRF details.
- [ ] Visually distinguish projected facts from manual facts so operators can tell whether a row came from canonical projection or human补录.
- [ ] Keep the displayed status label consistent with the shared normalized vocabulary and avoid letting UI-only terminology leak back into backend persistence.
- [ ] Add a compact evidence section or drawer for audit findings so operators can compare planned state, observed fact state, and canonical source context on one screen.
- [ ] Keep `IPAMOverview.vue` focused on counts and summaries; do not turn the overview into a raw metadata browser.

## Verification

Backend verification after implementation:

```bash
cd /Users/huangliang/project/OneOPS-ALL/OneOPS
go test ./app/ipam/service/impl ./app/device_collection2/service/impl
```

Expected: IPAM implementation tests pass, and no new Device Collection 2 failures are introduced by fact access changes.

Frontend verification after implementation:

```bash
cd /Users/huangliang/project/OneOPS-ALL/OneOPS-UI
npm run typecheck
npm run build
```

Expected: no TypeScript or build regressions after evidence and status DTO changes.

Optional workflow smoke:

```bash
cd /Users/huangliang/project/OneOPS-ALL/OneOPS-UI
npm run smoke:ipam-journey
```

Expected: IPAM fact and audit flow still renders, observed facts load, and evidence UI remains reachable.

## Phase Exit Criteria

- Valid latest canonical `interface_ip` facts can be projected into `ipam_address_fact` without manual re-entry.
- Projection preserves structured source context; the current lossy and overwritten `RawRef` field is no longer the only provenance carrier.
- Status vocabulary is normalized end-to-end from canonical source through backend audit logic to frontend display.
- Re-running the same projection is idempotent.
- Audit findings remain explainable through visible evidence and remain tied to IPAM planning state instead of replacing it.
- IPAM planning, request, allocation, reclaim, and lifecycle workflows remain authoritative and behaviorally unchanged.
