# OneOPS NetPath Scheme A Master Execution Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver a usable OneOPS NetPath MVP in the UI first, then extend it into productized run history, graph DTOs, probe orchestration, and workflow closure without fragmenting the work into disconnected tasks.

**Architecture:** Run Scheme A as a continuous three-wave program. Wave A makes NetPath genuinely usable in `OneOPS-UI` by pairing runtime truthfulness with a first operator page. Wave B turns the MVP into a reusable product surface with run history and graph-friendly contracts. Wave C adds post-analysis closure through probes and workflow. The frontend reuses the existing topology canvas and dynamic route shell; the backend keeps OneOPS as the collection, storage, and orchestration owner while `oneops-netpath` remains the deterministic engine behind the port.

**Tech Stack:** Go, OneOPS `app/netpath`, OneOPS DC2 facts, Vue 3, TypeScript, Ant Design Vue, existing topology canvas, optional build-tagged `oneops-netpath` SDK runtime.

---

## Scope And Guardrails

This plan follows:

- `docs/superpowers/plans/2026-06-19-oneops-netpath-master-roadmap.md`
- `docs/superpowers/plans/2026-06-19-oneops-netpath-long-task-execution-plan.md`
- `docs/superpowers/plans/2026-06-20-oneops-netpath-frontend-mvp-phase6.md`
- `docs/superpowers/acceptance/2026-06-19-oneops-netpath-user-journeys-checklist.md`
- `docs/superpowers/specs/2026-06-19-oneops-fact-application-foundation-design.md`

Do not fragment the work into one-off tickets. Every task package below must leave a testable artifact and feed the next package.

Consent gates remain unchanged from the existing long-task plan:

- adding a new backend dependency or changing the default `oneops-netpath` dependency strategy;
- enabling SDK mode in default production builds;
- destructive schema/data changes;
- real infrastructure probes or credentialed execution;
- widening vendor scope;
- changing policy-gap semantics from explicit diagnostics to silent allow.

## Program Structure

### Wave A: Frontend-Usable MVP

Purpose:

- Make NetPath actually usable in the UI for one operator path: submit flow -> get explainable result -> drill into evidence -> see the path highlighted on existing topology.

Packages:

1. `A1` Runtime truth and request contract
2. `A2` Frontend contract and hidden-route shell
3. `A3` Analysis workbench page
4. `A4` Evidence drawer and topology projection

Wave A acceptance anchor:

- At least one tenant-scoped flow returns a real run result instead of placeholder output.
- UI can create a run, reopen the returned run, inspect hops, and open per-device evidence.
- Existing topology canvas can highlight the selected trace without a new graph library.

Current checkpoint:

- `A2` code landed, but review determined it already crossed into `A3` scope.
- Treat the existing `NetPathMvp.vue` page and `netpath-mvp-smoke.ts` as the starting baseline for `A3`, not as a cleanly completed `A2`.
- The next frontend gate is therefore not "finish a thinner shell", but "formalize the workbench with stable validation, request contracts, and result rendering".

### Wave B: Productization

Purpose:

- Turn the MVP into a reusable product surface instead of a one-shot demo page.

Packages:

5. `B1` Run history and lightweight list API
6. `B2` Graph-friendly backend DTO
7. `B3` Menu visibility, permissions, and release integration

Wave B acceptance anchor:

- User can revisit earlier runs from the UI.
- Frontend can render path overlays without reconstructing the whole graph from nested hops by hand.
- NetPath page can enter the normal menu and permission system.

### Wave C: Closure And Extended Analysis

Purpose:

- Add post-analysis execution and operational closure.

Packages:

8. `C1` Probe Orchestrator contract and first execution path
9. `C2` Ticket/workflow closure
10. `C3` Evaluator deepening for policy/NAT/PBR

Wave C acceptance anchor:

- NetPath result can trigger linked probes and carry those results into ticket/workflow evidence.
- Unsupported policy phases remain explicit until evaluators truly exist.

## Parallel Lanes

### Lane 1: Backend Runtime And Contracts

Owns:

- runtime truthfulness
- request validation
- list/history
- graph DTOs
- probe contracts
- permission-aligned route surface

Primary files:

- `OneOPS/app/netpath/runtime`
- `OneOPS/app/netpath/service`
- `OneOPS/app/netpath/api`
- `OneOPS/app/netpath/router`
- `OneOPS/app/netpath/dto`
- `OneOPS/app/netpath/netpath_model`

### Lane 2: Frontend MVP And Visualization

Owns:

- `netpath` typings
- `netpath` API client
- hidden-route shell
- NetPath analysis page
- evidence drawer
- topology highlight projection

Primary files:

- `OneOPS-UI/src/typings`
- `OneOPS-UI/src/api`
- `OneOPS-UI/src/views/topology`
- `OneOPS-UI/src/router/utils.ts`
- `OneOPS-UI/src/components/Topology`

### Lane 3: Integration And Release Surface

Owns:

- menu visibility
- permission/functionality mapping
- smoke/typecheck/browser verification
- final UX stitching between NetPath, topology, and later probes/workflow

Primary files:

- `OneOPS/static/mysql_init2.sql`
- `OneOPS/scripts/sql/output.sql`
- `OneOPS/app/sys`
- `OneOPS-UI/package.json`
- `OneOPS-UI/scripts`

## Dependency Graph

```text
A1 -> A2 -> A3
A3 -> A4
A1 -> B1
A1 -> B2
B1 + B2 -> B3
A4 + B2 -> C1
C1 -> C2
B2 + policy fact foundation -> C3
```

Parallelism rule:

- `A1` starts first and must produce a stable runtime/contract checkpoint.
- Once that checkpoint is clear, `A2` and the preparatory part of `B1` can proceed in parallel.
- `A3` depends on `A2`.
- `A4` depends on `A3` and can split internally into evidence helper work and topology helper work before final page integration.
- `B1` and `B2` can run in parallel after `A1`.
- `B3` waits for `B1/B2`.
- `C1` waits for `A4` and `B2`.

## Package Details

### Package A1: Runtime Truth And Request Contract

**Goal:** Ensure NetPath returns real SDK-backed results when configured for SDK mode, and fail early with operator-readable errors when the runtime contract is not satisfied.

**Files:**
- Modify: `OneOPS/app/netpath/service/impl/netpath.go`
- Modify: `OneOPS/app/netpath/service/impl/module.go`
- Modify: `OneOPS/app/netpath/runtime/runtime.go`
- Modify: `OneOPS/app/netpath/runtime/sdk_enabled.go`
- Modify: `OneOPS/app/netpath/dto/netpath.go`
- Test: `OneOPS/app/netpath/service/impl/netpath_test.go`
- Test: `OneOPS/app/netpath/runtime/runtime_sdk_test.go`

- [ ] **Step 1: Write failing service/runtime tests for SDK contract errors**
- [ ] **Step 2: Verify the tests fail for the expected reasons**
- [ ] **Step 3: Move `device_codes` and runtime-mode contract validation to the earliest safe backend boundary**
- [ ] **Step 4: Preserve distinct failure reasons for scope missing, snapshot blocked, SDK unavailable, and engine failure**
- [ ] **Step 5: Re-run focused netpath backend tests and full `./app/netpath/...`**

Acceptance:

- SDK mode no longer surprises the frontend with late hidden runtime errors.
- Successful runs carry real `traces/source_refs/diagnostics`.
- Failure states are stable enough for the UI to branch on them.

### Package A2: Frontend Contract And Hidden Route Shell

**Goal:** Land the frontend `netpath` domain shell without waiting for menu visibility.

**Files:**
- Create: `OneOPS-UI/src/typings/netpath/netpath.ts`
- Create: `OneOPS-UI/src/api/netpath/netpath.ts`
- Create: `OneOPS-UI/src/views/topology/NetPathMvp.vue`
- Create: `OneOPS-UI/scripts/netpath-mvp-smoke.ts`
- Modify: `OneOPS-UI/src/typings/index.ts`
- Modify: `OneOPS-UI/src/router/utils.ts`
- Modify: `OneOPS-UI/package.json`

- [ ] **Step 1: Write a failing smoke import for NetPath typings, API client, and page shell**
- [ ] **Step 2: Verify the smoke build fails before the new files exist**
- [ ] **Step 3: Add NetPath typings mirrored from the backend DTO**
- [ ] **Step 4: Add NetPath API wrappers using the shared `request.ts` client**
- [ ] **Step 5: Add a hidden route entry and minimal page shell**
- [ ] **Step 6: Re-run smoke and frontend `typecheck`**

Acceptance:

- NetPath domain exists in the frontend build.
- Hidden route can open without menu seeding.
- Smoke and `typecheck` pass.

### Package A3: Analysis Workbench Page

**Goal:** Build the first operator workbench: preview snapshot, create run, fetch run, and render summary/traces/hops.

Implementation note:

- The current page already contains an early workbench draft. `A3` should refine and stabilize that draft rather than reverting it back to a minimal `A2` shell.

**Files:**
- Modify: `OneOPS-UI/src/views/topology/NetPathMvp.vue`
- Optional helper split if needed: `OneOPS-UI/src/views/topology/useNetPathWorkbench.ts`
- Test: `OneOPS-UI/scripts/netpath-mvp-smoke.ts`

- [ ] **Step 1: Add a failing page smoke assertion for form and result sections**
- [ ] **Step 2: Verify the new assertion fails before the workbench exists**
- [ ] **Step 3: Implement the workbench form and submit flow**
- [ ] **Step 4: Render run code, status, disposition, diagnostics, trace list, and hop list**
- [ ] **Step 5: Re-run smoke and `typecheck`**

Acceptance:

- User can complete Journey 3 and most of Journey 4 from the acceptance checklist.
- Error display is unified through the shared request layer.

### Package A4: Evidence Drawer And Topology Projection

**Goal:** Complete the first full operator loop by attaching evidence drilldown and visual path emphasis.

Implementation note:

- Reuse the existing page-layer topology highlight chain instead of introducing a new canvas abstraction.
- The current minimal projection target is: `highlightNodeIds`, `highlightEdgeIds`, `orderedPathSegments`, and optional `selectedEdgeId`.
- Prefer mapping NetPath hop-to-hop links into existing rendered edge identifiers before changing the canvas component API.

**Files:**
- Modify: `OneOPS-UI/src/views/topology/NetPathMvp.vue`
- Create: `OneOPS-UI/src/views/topology/useNetPathEvidenceDrawer.ts`
- Create: `OneOPS-UI/src/views/topology/netpath-evidence-helpers.ts`
- Create: `OneOPS-UI/src/views/topology/netpath-graph.ts`
- Reuse: `OneOPS-UI/src/components/Topology/Topology.vue`
- Reuse: `OneOPS-UI/src/api/topology/topology.ts`

- [ ] **Step 1: Write failing smoke assertions for evidence-drawer and graph-helper markers**
- [ ] **Step 2: Verify they fail before the drawer/projection code exists**
- [ ] **Step 3: Implement evidence fetch, drawer state, and grouped rendering**
- [ ] **Step 4: Implement trace-to-highlight projection with at least node highlighting**
- [ ] **Step 5: Reuse the existing topology component instead of introducing a new graph library**
- [ ] **Step 6: Re-run smoke, `typecheck`, and a browser-level verification pass if the page is runnable**

Acceptance:

- User can complete Journeys 5 and 6 for the MVP scope.
- Selected trace is visually distinguishable.
- Device evidence opens and closes correctly without destabilizing the page.

### Package B1: Run History And Lightweight List API

**Goal:** Let the UI reopen runs without relying on a just-created run code.

**Files:**
- Modify: `OneOPS/app/netpath/service/i_netpath.go`
- Modify: `OneOPS/app/netpath/dto/netpath.go`
- Modify: `OneOPS/app/netpath/service/impl/netpath.go`
- Modify: `OneOPS/app/netpath/api/netpath.go`
- Modify: `OneOPS/app/netpath/router/netpath.go`
- Test: `OneOPS/app/netpath/api/netpath_test.go`
- Test: `OneOPS/app/netpath/service/impl/netpath_test.go`

- [ ] **Step 1: Write failing tests for tenant-scoped list/history retrieval**
- [ ] **Step 2: Verify the list API does not exist yet**
- [ ] **Step 3: Add a lightweight list DTO that does not embed full `result_json`**
- [ ] **Step 4: Implement service/API/router list support**
- [ ] **Step 5: Re-run backend tests**

Acceptance:

- Frontend can page through historical NetPath runs.
- List payload stays light and stable.

### Package B2: Graph-Friendly Backend DTO

**Goal:** Stop making the frontend reconstruct path graph semantics entirely from nested hops.

**Files:**
- Modify: `OneOPS/app/netpath/dto/netpath.go`
- Modify: `OneOPS/app/netpath/service/impl/evidence_summary.go`
- Modify: `OneOPS/app/netpath/service/impl/netpath.go`
- Modify: `OneOPS/app/netpath/api/netpath.go`
- Modify: `OneOPS/app/netpath/router/netpath.go`
- Test: `OneOPS/app/netpath/dto/netpath_test.go`
- Test: `OneOPS/app/netpath/service/impl/netpath_test.go`

- [ ] **Step 1: Write failing DTO/service tests for graph-oriented output**
- [ ] **Step 2: Verify the current response shape lacks stable node/edge/path semantics**
- [ ] **Step 3: Add a graph-focused DTO or endpoint, keeping current detail endpoints compatible**
- [ ] **Step 4: Populate nodes, edges, path ordering, and evidence anchors from current run data**
- [ ] **Step 5: Re-run DTO/service/API tests**

Acceptance:

- Frontend can consume graph output directly.
- Existing create/get/evidence compatibility is preserved.

### Package B3: Menu Visibility And Permissions

**Goal:** Graduate from hidden-route-only MVP to a normal menu-driven product entry.

**Files:**
- Modify: `OneOPS/static/mysql_init2.sql`
- Modify: `OneOPS/scripts/sql/output.sql`
- Modify: `OneOPS/app/sys/...` only if functionality registration needs backend support
- Modify: `OneOPS-UI/src/router/utils.ts` only if the visible route differs from the hidden shell

- [ ] **Step 1: Define final NetPath menu entry and functionality codes**
- [ ] **Step 2: Seed menu records pointing at the agreed page component**
- [ ] **Step 3: Align permission points for create/list/detail/evidence/probe actions**
- [ ] **Step 4: Verify dynamic menu loading can reach the page without hidden-route fallback**

Acceptance:

- NetPath enters the normal authenticated menu tree and permission system.

### Package C1: Probe Orchestrator Contract And First Execution Path

**Goal:** Define and then land the first post-analysis probe path without polluting engine semantics.

**Files:**
- Modify: `OneOPS/app/netpath/dto/netpath.go`
- Modify: `OneOPS/app/netpath/service/i_netpath.go`
- Modify: `OneOPS/app/netpath/api/netpath.go`
- Modify: `OneOPS/app/netpath/router/netpath.go`
- New supporting files as needed under `OneOPS/app/netpath` or another agreed orchestration boundary

- [ ] **Step 1: Write failing tests for run-linked probe plan creation and retrieval**
- [ ] **Step 2: Define DTO/state model for probe plan and probe results**
- [ ] **Step 3: Implement the first linked probe orchestration path**
- [ ] **Step 4: Preserve separation between simulated disposition and probe observations**
- [ ] **Step 5: Re-run focused backend tests**

Acceptance:

- Journey 9 can start in backend/API form.
- Probe results are linked, not conflated with trace disposition.

## Multi-Agent Execution Mapping

Use `subagent-driven-development` with one fresh implementer per package after the package becomes unblocked.

Recommended package ownership:

- Worker A: `A1 -> B1`
- Worker B: `A2 -> A3`
- Worker C: `A4 -> B2`
- Worker D: `B3 -> C1`

Rules:

- Do not run multiple workers on the same write set at once.
- `NetPathMvp.vue` is a convergence file; whichever package owns it at a given moment has exclusive write ownership until merged.
- Keep helper/module ownership disjoint when running `A4` and `B2` in parallel.

## Verification Matrix

### Backend

Run at minimum:

```bash
cd /Users/huangliang/project/OneOPS-ALL/OneOPS
go test -count=1 ./app/netpath/...
```

Use focused test runs for each package before the full suite when possible.

### Frontend

Run at minimum:

```bash
cd /Users/huangliang/project/OneOPS-ALL/OneOPS-UI
npm run typecheck
npm run smoke:netpath-mvp
```

If a runnable local page exists in the chosen execution slice, add browser verification against the hidden route.

## Stop Conditions

Stop the continuous rollout only when:

- a consent gate is reached;
- the runtime cannot produce real results because of external build/deploy state not controllable from the workspace;
- a shared convergence file has unresolved conflicting requirements;
- acceptance scope changes from “frontend usable MVP first” to a broader release target.

## Self-Review

- Scope check: this is a program plan, not a single package implementation plan. It intentionally groups work into continuous packages that can each become their own sub-plan during execution.
- Coverage check: it covers the user-approved Scheme A path from frontend usability to productization and closure.
- Placeholder scan: package names, file zones, dependencies, and acceptance anchors are explicit.

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-06-20-oneops-netpath-scheme-a-master-execution.md`.

Execution mode is already chosen by user intent:

- **Subagent-Driven (selected)** - continuous execution with fresh subagents per package, review between packages, minimal interruption.
