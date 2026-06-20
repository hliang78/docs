# OneOPS NetPath Master Roadmap

> **For agentic workers:** This is the long-running master roadmap. Do not treat it as a single implementation task. Each phase must produce its own focused design or implementation plan before code changes. Use superpowers:subagent-driven-development for implementation phases and keep status reports aligned to the phase names below.

**Goal:** Deliver OneOPS NetPath as an end-to-end network path analysis capability covering collection, snapshot modeling, forwarding simulation, visualization, probing, and operational closure.

**Architecture:** OneOPS owns collection, storage, snapshot generation, UI, probes, and workflow. `oneops-netpath` owns deterministic path analysis over an engine-ready snapshot. Integration is through a OneOPS-owned engine port and optional SDK adapter, keeping the platform decoupled from any single engine implementation.

**Tech Stack:** Go, OneOPS modules, DC2 latest facts, OneOPS topology/firewall/device services, oneops-netpath SDK, build tags, future frontend topology visualization, future probe orchestration.

---

## Operating Rule

All future long-task rounds should report progress using this structure:

```text
【本轮状态】
当前阶段：
- Phase N: <name>

基于的数据模型：
- ...

完成的工作：
- ...

验证：
- ...

下一步：
- ...
```

Do not start unrelated feature work while a phase is active. If new information changes the plan, update this roadmap first or add a phase-specific design note.

## Current Baseline

Completed work:

- `oneops-netpath` has a public SDK surface under `pkg/netpath`.
- OneOPS has an engine port under `app/netpath/engine`.
- OneOPS `NetPathService` maps DTOs to the engine port and persists mapped results.
- OneOPS has a build-tagged SDK adapter scaffold under `app/netpath/adapter/oneopsnetpath`.
- OneOPS has a DC2 preview snapshot builder under `app/netpath/snapshot`.
- OneOPS has a configurable NetPath runtime under `app/netpath/runtime` with `pending`, `disabled`, and build-tagged `sdk` modes.
- User journeys and acceptance checklist are documented.
- SnapshotProvider design is documented.

Important design documents:

- `docs/superpowers/specs/2026-06-18-oneops-netpath-platform-design.md`
- `docs/superpowers/specs/2026-06-19-oneops-fact-application-foundation-design.md`
- `docs/superpowers/specs/2026-06-19-oneops-netpath-user-journeys-acceptance-design.md`
- `docs/superpowers/acceptance/2026-06-19-oneops-netpath-user-journeys-checklist.md`
- `docs/superpowers/specs/2026-06-19-oneops-netpath-snapshot-provider-design.md`
- `docs/superpowers/specs/2026-06-19-oneops-netpath-sdk-adapter-design.md`

Known constraints:

- Current `oneops-netpath` engine evaluates route and topology only.
- ACL, NAT, PBR, and security policy are first-phase NetPath facts, but may remain evidence, diagnostics, and confidence gates until engine evaluators exist.
- Current OneOPS preview builder lacks route tables and must not be used as an engine-ready snapshot.
- DC2 has a generic network-device `route_table` fact processor in the Phase 4 worktree; NetPath now also has a provider-backed latest-fact seam, a build-tagged SDK runtime path, explicit `device_codes` scope propagation, tenant-scoped run retrieval at the service/API boundary, a OneOPS `device_to_tenant` authorization adapter, and source-level OneOPS DI/router registration. Production runs still need durable persistence beyond the in-memory run store and `cmd/wire_gen.go` regeneration in a clean integration window.
- Tenant scoping for DC2 latest facts needs explicit design and validation.
- Default OneOPS builds must not require `oneops-netpath` until dependency strategy is settled.
- NetPath must consume shared canonical facts or typed snapshots/projections; it must not create a parallel fact model for route, interface, topology, IP, or firewall evidence.

First-phase policy fact design:

- `docs/superpowers/specs/2026-06-20-oneops-netpath-policy-fact-foundation-design.md`

## Phase 0: Research And Architecture Foundation

Status: complete.

Purpose:

- Establish direction by comparing Batfish/IP Fabric/SuzieQ style capabilities.
- Decide whether OneOPS should integrate external engines, reimplement MVP concepts, or do both.

Completed outputs:

- external capability analysis;
- Batfish packet journey analysis;
- OneOPS platform boundary;
- oneops-netpath standalone MVP direction;
- SDK adapter strategy;
- user journey acceptance baseline.

Exit criteria:

- User agrees OneOPS should own collection, storage, UI, probes, and workflow while engine capability remains pluggable.

## Phase 1: Engine And Port Foundation

Status: complete.

Purpose:

- Make path analysis callable through a stable OneOPS-owned interface.

Completed outputs:

- `oneops-netpath/pkg/netpath` public SDK.
- OneOPS `app/netpath/engine.AnalysisEngine`.
- Service-to-engine mapping.
- Build-tagged SDK adapter scaffold.

Acceptance:

- OneOPS default tests pass without `oneops-netpath` dependency.
- Tagged SDK adapter tests pass with local workspace.
- No `go.mod`, `go.sum`, or committed `go.work` dependency leak.

## Phase 2: Engine-Ready SnapshotProvider

Status: complete.

Purpose:

- Convert OneOPS collected data into an engine-ready analysis snapshot that can be safely supplied to the SDK adapter.

Primary data model:

- DC2 latest facts:
  - `device_identity`
  - `interface`
  - `interface_ip`
  - `topology_neighbor`
  - proposed `route_table`
  - existing partial `server_route`
- Firewall config snapshot:
  - interfaces
  - routes
  - zones
- Internal OneOPS `AnalysisSnapshot`.
- Future tagged mapper to `netpath.Snapshot`.

Subphases:

1. Phase 2A: internal analysis snapshot model
   - Define OneOPS-owned structs for devices, interfaces, links, route tables, route evidence, policy evidence, and diagnostics.
   - No `oneops-netpath` import.

2. Phase 2B: reader ports
   - Define interfaces for DC2 latest facts, device inventory, topology links, and firewall facts.
   - Depend on service boundaries, not GORM tables or service impl packages.
   - First production-facing DC2 latest-fact seam requires `tenant_code` and explicit `device_codes`, then reads per target/fact type without `target_id=""`.

3. Phase 2C: assembler
   - Assemble devices, interfaces, links, route tables, and diagnostics from injected facts.
   - Support current `interface`, `interface_ip`, `topology_neighbor`, `server_route`.
   - Support proposed `route_table` facts in tests so the contract is ready.

4. Phase 2D: quality gate
   - Classify snapshots as `ready`, `degraded`, or `blocked`.
   - Block snapshots that would make the engine error because of missing ingress, missing devices, invalid route prefixes, or unenforced tenant scope.

5. Phase 2E: provider and mapper
   - Implement provider retrieval path.
   - Add tagged mapper to `netpath.Snapshot`.
   - Keep default builds independent from `oneops-netpath`.

Exit criteria:

- Unit tests cover ready, degraded, and blocked snapshots.
- A synthetic route/topology fixture can produce an engine-ready snapshot.
- Preview builder remains separate from analysis assembler.
- Missing route tables are diagnostics or blocked state, not fake routes.
- Provider-side latest-fact reads fail closed without tenant and explicit device scope.

Completed outputs:

- OneOPS internal `AnalysisSnapshot` model under `app/netpath/snapshot/provider`.
- DC2 fact helpers and stable interface join-key contract.
- In-memory assembler for device identity, interfaces, interface IPs, topology links, route tables, server routes, diagnostics, and source run IDs.
- Snapshot validator with `ready`, `degraded`, and `blocked` quality gate.
- Build-tagged provider snapshot adapter that invokes the tenant-safe latest-fact provider contract and maps `AnalysisSnapshot` to `oneops-netpath/pkg/netpath.Snapshot` while failing closed on blocked snapshot quality.
- Boundary verification passed for provider and existing netpath packages.

## Phase 3: Route Table Collection And Normalization

Status: broadened into Phase 3A and 3B; route table implementation is in isolated worktree and policy fact design is documented.

Purpose:

- Fill the largest real data gap: generic network-device route tables.
- Freeze the first-phase policy fact families needed to avoid false confident allow decisions.
- Keep route data in the shared canonical fact layer so IPAM, topology, NetPath, RCA, and future agents can converge on one fact model.

Primary data model:

- DC2 `route_table` fact.
- NetPath first-phase policy facts:
  - `security_zone_binding`
  - `acl_rule`
  - `firewall_policy`
  - `nat_rule`
  - `pbr_rule`
  - `address_object`
  - `service_object`
  - `policy_parser_diagnostic`

Required fact fields:

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

Subphases:

1. Phase 3A: Define route table canonical fact schema.
2. Phase 3A: Add processor tests for normalized route rows.
3. Phase 3A: Add one or more collection dataset contracts for route output.
4. Phase 3A: Backfill assembler support from Phase 2C.
5. Phase 3A: Add fixture-driven path analysis tests using route facts.
6. Phase 3B: Freeze ACL, NAT, PBR, firewall policy, object, zone-binding, and parser-diagnostic facts.
7. Phase 3B: Add snapshot quality gates so missing policy facts block or degrade confidence instead of silently allowing traffic.
8. Phase 3B: Extend firewall config snapshot output beyond policy/NAT counts into normalized rows or explicit unsupported diagnostics.

Current implementation notes:

- Phase 4 adds `processor.route_table.v1`, H3C Comware/SecPath `cli_route_table`, invalid-row fact issues, latest/history tests, and DC2-shaped NetPath provider fixtures.
- Direct/connected route identities use `nh:direct` even when the source row carries a next-hop value.
- Null route fixtures preserve H3C-style standardized next-hop evidence such as `0.0.0.0` while using identity fragment `nh:null`.
- Production readiness still depends on resolving tenant-authorized device scope and wiring the SnapshotProvider/SDK adapter into durable NetPath runs; `AnalyzeRunCreateReq.device_codes` is now the intended explicit scope carrier into `engine.AnalyzeRequest`.

Exit criteria:

- OneOPS can collect or ingest route facts for at least one network-device style fixture.
- SnapshotProvider can generate route tables without hand-written test-only data.
- Engine can return `delivered_to_subnet`, `no_route`, `null_routed`, and `neighbor_unreachable` from collected-style route facts.
- Route fact provenance can answer which DC2 run, dataset, processor, and source fields produced a route.
- Latest-fact provider seam reads route facts per scoped target, not through global latest queries.
- Firewall, ACL, NAT, and PBR gaps are represented as facts, diagnostics, or blocked quality, never silently ignored.

## Phase 4: First End-To-End Path Analysis Run

Status: active. Phase 4A/4B runtime wiring and tenant-scoped device authorization are source-level complete; durable persistence remains pending.

Purpose:

- Make OneOPS create a path analysis run backed by a real analysis snapshot.
- Preserve canonical fact and snapshot/projection references so the path result can be explained and audited.

Subphases:

1. Wire SnapshotProvider into an explicitly enabled analysis engine path using `engine.AnalyzeRequest.DeviceCodes` as the explicit scoped device set.
   - Status: Phase 4A complete for source-level wiring.
   - Implemented `config.netpath.engine_mode`.
   - Implemented `runtime.Configure` for `pending`, `disabled`, and build-tagged `sdk` modes.
   - Implemented provider-backed SDK snapshot provider under the `oneops_netpath_sdk` build tag.
   - Implemented `AnalyzeRunCreateReq.device_codes` and engine request scope propagation.
   - Preview builder and SDK provider now read DC2 latest facts per scoped device code instead of through global latest queries.
   - SDK provider fails closed when device scope or tenant/device scope authorizer is missing.
   - Added `DeviceTenantScopeAuthorizer` backed by OneOPS `IDeviceTenantMapping.FindByRelationKeyAndMasterKeys`, so every requested device must be mapped to the run tenant.
   - Snapshot preview uses the same authorizer before reading DC2 facts, so preview and analysis share the same tenant/device scope boundary.
   - Service/runtime construction now fails fast when a latest-fact-backed path lacks a tenant/device authorizer, and tests prove denied scopes perform zero DC2 fact reads.
   - SDK provider rejects `blocked` analysis snapshots before calling the engine.
   - SDK latest fact limit is aligned to DC2's non-clamped maximum of 1000.
   - `GET /netpath/analysis-runs/:code` now requires matching `tenant_code`.
   - Added `NetPathServiceSet`, `NetPathSet`, and `initialize.Router` source registration.
   - Deferred `cmd/wire_gen.go` regeneration because the generated file already has unrelated working-tree edits.
   - Deferred default `go.mod` dependency on `oneops-netpath`; clean SDK-tagged CI requires a dependency strategy decision because current verification uses a local temporary modfile/replace.
2. Persist snapshot source references with the run.
3. Persist trace, hops, steps, diagnostics, and disposition.
4. Add API tests for create/get analysis run.
5. Add a fixture or smoke path from DC2 facts to analysis result.

Exit criteria:

- User can submit a concrete flow and receive a persisted path result.
- The result includes snapshot ID, flow, disposition, trace, hops, route lookup steps, and diagnostics.
- Engine errors become failed runs with readable error messages.

## Phase 5: Evidence Drilldown

Status: pending.

Purpose:

- Let operators inspect route and policy evidence relevant to the current path.

Primary data model:

- trace steps;
- route hit evidence;
- policy evidence stubs;
- firewall policy overview;
- raw config references.

Subphases:

1. Define path evidence DTOs.
2. Add route evidence endpoint.
3. Add device-on-path evidence endpoint.
4. Attach raw references and source fact IDs where available.
5. Add diagnostics for missing evidence.

Exit criteria:

- Clicking a path device can return relevant route entries and diagnostics.
- Policy/NAT/PBR evidence is shown as available or unsupported, not falsely evaluated.

## Phase 6: Interactive Path Visualization

Status: pending.

Purpose:

- Render the path as an operator-friendly interactive view.

Subphases:

1. Define graph DTO for analysis result.
2. Map trace hops and links to topology nodes and edges.
3. Encode device type, direction arrows, path highlight, terminal state, and uncertainty markers.
4. Add device and edge drilldown interactions.
5. Add frontend tests or browser verification for core path states.

Exit criteria:

- Source, destination, path direction, devices, links, and blocker state are visually clear.
- Users can zoom, select nodes, inspect details, and distinguish simulated path from surrounding topology.

## Phase 7: Probe Orchestrator

Status: pending.

Purpose:

- Add active connectivity testing after path analysis.

Probe types:

- source to destination ping;
- source to source gateway ping;
- source to destination gateway ping;
- destination to destination gateway ping;
- source to destination traceroute.

Subphases:

1. Define probe plan and result persistence.
2. Infer or request source and destination gateway.
3. Select executor.
4. Execute ping and traceroute through existing task/controller path.
5. Link results to analysis run and graph view.

Exit criteria:

- Path analysis can trigger a linked probe plan.
- Probe results are stored and visible separately from simulated disposition.
- Traceroute output can be compared with simulated hops when correlation data exists.

## Phase 8: Ticket And Change Closure

Status: pending.

Purpose:

- Convert diagnosis into actionable operational work.

Subphases:

1. Define diagnostic summary payload.
2. Create internal work item or ticket record from path result.
3. Attach snapshot, flow, disposition, blocker, evidence, and probe results.
4. Support rerun after new collection.
5. Support before/after comparison.

Exit criteria:

- A path result can create a work item with enough context for network or firewall teams.
- Before and after runs can be linked to prove remediation.

## Phase 9: Policy, NAT, PBR Evaluators

Status: evaluator phase after first-phase policy facts exist.

Purpose:

- Move from evidence-only policy facts to real traffic decision evaluation.

Subphases:

1. Add engine evaluator extension points.
2. Implement ingress ACL evaluator.
3. Implement security policy evaluator.
4. Implement NAT transformation evaluator.
5. Implement PBR route override evaluator.
6. Add vendor-specific evaluator refinements incrementally.

Exit criteria:

- Engine can produce `denied_in`, `denied_out`, policy permit/deny steps, and NAT transformation steps from normalized facts.
- Unsupported vendor features remain explicit diagnostics.

## Phase Dependencies

```text
Phase 0 -> Phase 1 -> Phase 2 -> Phase 3 -> Phase 4
                                  Phase 4 -> Phase 5 -> Phase 6
                                  Phase 4 -> Phase 7
                                  Phase 5 + Phase 7 -> Phase 8
                                  Phase 2 + Phase 4 -> Phase 9
```

## Near-Term Execution Plan

The next long-task block should execute Phase 2 only:

1. Write a detailed implementation plan for Phase 2A-2D.
2. Implement internal analysis snapshot model and reader ports.
3. Implement assembler with synthetic facts.
4. Implement quality gate.
5. Keep SDK mapper/provider wiring as a separate final Phase 2E slice.

Do not start route collection contracts, UI, probes, or tickets until Phase 2 has a tested internal assembler and quality gate.

## Status Report Template

Each future round should include:

```text
【本轮状态】
当前阶段：
- Phase <N>: <name>

基于的数据模型：
- ...

完成的工作：
- ...

验证：
- ...

计划推进：
- 本轮完成了 roadmap 中的 <item>
- 下一轮进入 <item>
```

## Acceptance Anchor

The long task is not accepted merely because code exists. It is accepted when the user journey checklist can be checked end to end:

- collection source visible;
- snapshot quality visible;
- flow submitted;
- explainable trace generated;
- path rendered;
- evidence drilldown available;
- probes linked;
- ticket or diagnostic closure available.
