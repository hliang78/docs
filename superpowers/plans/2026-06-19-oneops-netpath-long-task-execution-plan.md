# OneOPS NetPath Long Task Execution Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development for implementation phases and superpowers:verification-before-completion before claiming a phase is complete. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver OneOPS NetPath through planned phases instead of scattered one-off tasks.

**Architecture:** OneOPS owns collection, storage, snapshot quality, APIs, UI, probes, and ticket workflow. `oneops-netpath` owns deterministic forwarding simulation behind a OneOPS-owned engine port. Every phase must leave a testable artifact and a concise status block.

**Tech Stack:** Go, OneOPS DC2 collection, OneOPS netpath modules, optional `oneops-netpath` SDK adapter, future frontend path view, future probe orchestration.

---

## Governing Foundation

This execution plan is constrained by:

- `docs/superpowers/specs/2026-06-19-oneops-fact-application-foundation-design.md`
- `docs/superpowers/plans/2026-06-19-oneops-netpath-master-roadmap.md`
- `docs/superpowers/acceptance/2026-06-19-oneops-netpath-user-journeys-checklist.md`

NetPath must follow the shared OneOPS fact application direction:

```text
Collection layer
  -> Canonical fact layer
  -> Snapshot/projection layer
  -> Application layer
```

Implications:

- Route, interface, topology, IP, and future firewall inputs should be canonical DC2 facts or explicitly versioned snapshots.
- NetPath should consume canonical facts through a snapshot provider, not invent a parallel route/topology fact model.
- Application-specific run and trace state is allowed, but every result must retain source fact, freshness, quality, and snapshot references.
- Temporary import endpoints are fallback tools only; using one instead of DC2 canonical facts requires user agreement.

## Operating Contract

Default execution rule:

- Continue the active phase without asking when the next step is already covered by this plan.
- Report each meaningful round using the agreed status block.
- Use subagents for implementation reviews when code changes are non-trivial.
- Use TDD for new behavior and bug fixes.
- Commit small, phase-scoped changes.
- Do not use `pro-autodev-loop`.

Status block:

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

## Consent Gates

Stop and ask the user before continuing if any item below occurs:

- A phase requires adding a new external dependency to `OneOPS/go.mod` or changing the default build dependency strategy.
- A phase requires enabling the build-tagged `oneops-netpath` SDK adapter in default production wiring.
- A phase needs destructive or broad data changes, such as migrations that alter existing records, backfills over production-like data, or cleanup scripts.
- A phase needs credentials, live device access, SNMP/SSH/WinRM access, or probe execution against real infrastructure.
- A phase requires choosing vendor CLI scope beyond the MVP route-table parser set.
- A phase proposes a temporary route/config import endpoint instead of DC2 canonical facts.
- A phase proposes a generic snapshot publication table instead of typed application snapshots.
- A phase requires deciding tenant scoping semantics for DC2 latest facts beyond the current test fixtures.
- A phase changes the acceptance target, for example allowing policy gaps to be treated as permit decisions.
- A test failure appears outside the active phase and fixing it would require touching unrelated modules.
- Implementation uncovers a design conflict between OneOPS data model and `oneops-netpath` engine contracts.

Everything else can proceed by default.

## Current Baseline

Completed:

- Phase 0: research and architecture foundation.
- Phase 1: engine and port foundation.
- Phase 2: engine-ready internal SnapshotProvider skeleton.

Current commits of interest:

- `oneops-netpath`: public SDK surface under `pkg/netpath`.
- `OneOPS`: `app/netpath/engine` port.
- `OneOPS`: `app/netpath/adapter/oneopsnetpath` build-tagged adapter scaffold.
- `OneOPS`: `app/netpath/snapshot/provider` analysis model, fact helpers, assembler, and validator.

Known gap now blocking realistic end-to-end analysis:

- DC2 has `server_route`, but no generic network-device `route_table` processor or built-in route collection dataset.
- Canonical latest fact reads are currently scoped by explicit `device_codes`; NetPath SDK runs additionally verify those devices through OneOPS `device_to_tenant` mappings before reading facts.
- NetPath runtime wiring is source-level ready, but generated `cmd/wire_gen.go` has not been refreshed because the file already contains unrelated local edits.
- NetPath analysis snapshots are currently typed application snapshots, not generic obsflow snapshots.

## Phase Sequence

### Phase 3: Route Table Collection And Normalization

Purpose:

- Make DC2 produce normalized `route_table` facts for network devices.

Plan file:

- `docs/superpowers/plans/2026-06-19-oneops-netpath-route-table-phase3.md`

Exit criteria:

- `route_table` facts can be produced through `ProcessFacts`.
- Route facts include `vrf`, `destination`, `next_hop_ip`, `out_interface`, `protocol`, `metric`, `preference`, `null_route`, and `raw`.
- SnapshotProvider assembler consumes route facts generated through the same field shape.
- Route facts include DC2 provenance and can answer which collection/processing source produced them.
- Provider and DC2 tests pass without `oneops-netpath` dependency leakage.

Default continue:

- Implement processor, tests, registry entry, and one minimal built-in dataset contract.

Consent required:

- Adding vendor-specific parsers beyond the first MVP contract set.
- Any migration or backfill for existing DC2 facts.

### Phase 4: First End-To-End Path Analysis Run

Purpose:

- Create a persisted analysis run from a validated snapshot and a business flow.

Expected plan file:

- `docs/superpowers/plans/2026-06-19-oneops-netpath-first-e2e-run-phase4.md`

Exit criteria:

- API/service path builds or selects a validated snapshot.
- Engine run persists flow, snapshot ID, trace, hops, steps, diagnostics, disposition, status, and error message.
- Failed engine runs are stored with readable errors.

Current Phase 4A progress:

- `config.Config` now exposes `netpath.engine_mode`.
- `app/netpath/runtime` can select `pending`, `disabled`, or `sdk`.
- Default builds reject `sdk` with a clear `oneops_netpath_sdk` build-tag error.
- Tagged builds construct a provider-backed SDK engine from DC2 latest facts through `AnalysisSnapshot`.
- SDK-backed runs require explicit `device_codes`; the provider reads DC2 latest facts per scoped device instead of using global latest queries.
- SDK-backed runs require a tenant/device scope authorizer and reject blocked snapshots before invoking the engine.
- Phase 4B added a OneOPS `DeviceTenantScopeAuthorizer` backed by `IDeviceTenantMapping.FindByRelationKeyAndMasterKeys`; all requested `device_codes` must belong to `tenant_code`.
- Snapshot preview now also requires explicit `device_codes` and uses the same tenant/device authorizer before reading DC2 latest facts.
- Service/runtime construction now fails fast when a latest-fact-backed path lacks a tenant/device authorizer, and tests cover zero DC2 fact reads after authorization denial.
- Analysis run retrieval now requires matching `tenant_code`.
- `app/netpath/service/impl.NetPathServiceSet`, `app/netpath/api.NetPathSet`, and `app/netpath/router.NetPath` are source-level ready for Wire integration.
- `initialize.Router` has a guarded NetPath route call, so stale `cmd/wire_gen.go` does not expose a broken route.

Deferred integration item:

- Regenerate `cmd/wire_gen.go` only in a clean integration window, or after explicitly reconciling the unrelated existing generated-file edits.
- DC2 latest facts remain target-scoped at the storage/API layer; NetPath enforces tenant scope in the runtime/service boundary through explicit device authorization.
- Decide whether/when to add `github.com/netxops/oneops-netpath` to default `go.mod`; current SDK-tagged verification intentionally uses a temporary local modfile/replace to avoid changing the default dependency strategy without consent.

Default continue:

- Wire only through existing OneOPS engine port and service boundaries.

Consent required:

- Enabling SDK adapter in default build.
- Changing persistence schema with migrations.

### Phase 5: Evidence Drilldown

Purpose:

- Let operators inspect route, topology, and policy evidence related to a path.

Exit criteria:

- Device-on-path evidence endpoint returns matched route entries and source refs.
- Unsupported ACL, NAT, PBR, or security policy phases appear as diagnostics, not silent allows.
- Evidence can be linked back to trace steps.

Consent required:

- Expanding scope from route/topology evidence into real firewall policy evaluation.

### Phase 6: Interactive Path Visualization

Purpose:

- Render complete path results with topology, arrows, highlights, device drilldown, and blockers.

Exit criteria:

- Path page shows source, destination, devices, links, direction, terminal state, and diagnostics.
- User can zoom, pan, select device/link, and open evidence.

Consent required:

- Introducing a new frontend graph library if the current frontend stack lacks one.

### Phase 7: Probe Orchestrator

Purpose:

- Generate and run linked ping/traceroute probe plans after path analysis.

Exit criteria:

- Probe plan includes source-to-destination ping, source-to-source-gateway ping, source-to-destination-gateway ping, destination-to-destination-gateway ping, and source-to-destination traceroute.
- Probe results are stored separately from simulated trace disposition.

Consent required:

- Running probes against real infrastructure.
- Choosing probe executors or credentials.

### Phase 8: Ticket And Workflow Closure

Purpose:

- Turn path analysis, evidence, and probe results into operational closure.

Exit criteria:

- Ticket payload includes run ID, snapshot ID, flow, disposition, path summary, blocker, evidence, and probe results.
- Re-analysis can be linked to the original ticket.

Consent required:

- Integrating with external ticket systems or sending data outside the local OneOPS instance.

### Phase 9: Policy, NAT, PBR, And Firewall Evaluators

Purpose:

- Move from evidence-only firewall visibility to deterministic policy evaluation.

Exit criteria:

- ACL/security policy/NAT/PBR phases produce explicit allow, deny, transformed, unsupported, or insufficient-data outcomes.
- No path is marked allowed when required policy data is missing.

Consent required:

- Selecting initial firewall vendor/model scope.
- Changing engine semantics in `oneops-netpath`.

## Progress Ledger

- [x] Phase 0 complete.
- [x] Phase 1 complete.
- [x] Phase 2 complete.
- [ ] Phase 3 active next.
- [ ] Phase 4 active: Phase 4A/4B runtime wiring and tenant-scoped device authorization complete; persistence pending.
- [ ] Phase 5 pending.
- [ ] Phase 6 pending.
- [ ] Phase 7 pending.
- [ ] Phase 8 pending.
- [ ] Phase 9 pending.

## Verification Rule

Before closing any phase, run:

```bash
git status --short
```

Run phase-specific tests. For netpath backend phases, include at least:

```bash
go test -count=1 ./app/netpath/snapshot/provider
go test -count=1 ./app/netpath/snapshot ./app/netpath/dto ./app/netpath/engine ./app/netpath/service ./app/netpath/service/impl ./app/netpath/api ./app/netpath/adapter/oneopsnetpath ./app/netpath/snapshot/provider
```

Confirm dependency boundary:

```bash
git diff -- go.mod go.sum
rg -n "github.com/netxops/oneops-netpath" app/netpath/snapshot/provider app/netpath/snapshot go.mod
```
