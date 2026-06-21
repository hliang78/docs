# OneOPS NetPath Fast Closure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close the shortest remaining gaps from NetPath MVP to an actionable OneOPS loop by wiring NetPath ticket-draft into real OneOPS `platform/tasks`, then adding front-end task creation, rerun/compare support, and honest probe visibility.

**Architecture:** Keep the current NetPath MVP chain intact and avoid inventing a second ticket system. Reuse the existing `platform/tasks` mainline as the real closure carrier, add a NetPath facade API that maps analysis-run and ticket-draft context into a platform task creation envelope, and let the UI create and follow the real task from inside NetPath.

**Tech Stack:** Go, GORM, Gin, Vue 3, Ant Design Vue, existing OneOPS NetPath DTO/service/router patterns.

---

## Current Gap Summary

- Closed already:
  - persisted analysis run
  - probe plan build/get/dispatch
  - workflow handoff view
  - monitor_probe draft view
  - probe execution readback
  - ticket draft preview
  - interactive topology/evidence MVP page
- Blocking closure gaps:
  - no real create-task action from path result
  - no frontend action to create and revisit that real task
  - no rerun/compare path for before/after validation
  - traceroute is still visibly unsupported in current probe dispatch mapping
- Important non-blocker:
  - deeper platform3/l3nodemap integration can follow after `platform/tasks` closure proves the workflow

## File Structure

- Backend DTO/API/service:
  - Modify: `OneOPS/app/netpath/dto/netpath.go`
  - Modify: `OneOPS/app/netpath/service/i_netpath.go`
  - Modify: `OneOPS/app/netpath/service/impl/netpath.go`
  - Modify: `OneOPS/app/netpath/service/impl/module.go`
  - Modify: `OneOPS/app/netpath/api/netpath.go`
  - Modify: `OneOPS/app/netpath/router/netpath.go`
- Backend tests:
  - Modify: `OneOPS/app/netpath/service/impl/netpath_test.go`
  - Modify: `OneOPS/app/netpath/service/impl/module_test.go`
  - Modify: `OneOPS/app/netpath/api/netpath_test.go`
  - Modify: `OneOPS/app/netpath/router/netpath_test.go`
- Frontend integration:
  - Modify: `OneOPS-UI/src/typings/netpath/netpath.ts`
  - Modify: `OneOPS-UI/src/api/netpath/netpath.ts`
  - Modify: `OneOPS-UI/src/views/topology/NetPathMvp.vue`
  - Modify: `OneOPS-UI/src/router/utils.ts`
  - Modify: `OneOPS-UI/scripts/netpath-mvp-smoke.ts`
- Compare support:
  - Reuse the same files above; do not create a second compare-specific subsystem unless needed

### Task 1: Add NetPath -> Platform Task Facade

**Files:**
- Modify: `OneOPS/app/netpath/dto/netpath.go`
- Modify: `OneOPS/app/netpath/service/i_netpath.go`
- Modify: `OneOPS/app/netpath/service/impl/netpath.go`
- Modify: `OneOPS/app/netpath/service/impl/module.go`
- Modify: `OneOPS/app/netpath/api/netpath.go`
- Modify: `OneOPS/app/netpath/router/netpath.go`
- Test: `OneOPS/app/netpath/service/impl/netpath_test.go`
- Test: `OneOPS/app/netpath/service/impl/module_test.go`
- Test: `OneOPS/app/netpath/api/netpath_test.go`
- Test: `OneOPS/app/netpath/router/netpath_test.go`

- [ ] **Step 1: Write failing tests for NetPath task creation facade**

Add tests that prove:
- create from `analysis_run_code`
- payload maps `snapshot_id`, flow summary, disposition, blockers, and probe summary into task context
- request validates required execution envelope bindings
- service delegates to existing platform task creation service
- response returns `task_id` and helpful follow-up links

- [ ] **Step 2: Run targeted backend tests to verify failure**

Run:

```bash
cd /Users/huangliang/project/OneOPS-ALL/OneOPS && go test ./app/netpath/service/impl ./app/netpath/api ./app/netpath/router
```

Expected:
- FAIL with missing DTO/method/route assertions for task-create facade

- [ ] **Step 3: Add DTOs and service methods**

Add:
- task-create request with minimal execution bindings
- task-create response with `task_id`, `task_url`, `diagnostic_logs_url`, and draft summary echo
- helper DTOs for execution binding sections if needed

Add service methods:
- `CreateAnalyzeRunTask`

- [ ] **Step 4: Inject platform task creation dependency**

Wire existing `platform` task creation service into NetPath service/module using the least invasive option pattern.

- [ ] **Step 5: Implement task-create mapping**

Implementation should derive from:
- current analyze run
- current ticket draft
- current probe execution

and merge user-supplied minimal execution fields for `platform/tasks`.

The service should fail closed when:
- analyze run does not exist
- tenant scope does not match
- task creation dependency is unavailable
- required platform execution fields are missing

- [ ] **Step 6: Add API and router endpoint**

Minimum endpoint:

```text
POST /api/netpath/analysis-runs/:code/task-create
```

- [ ] **Step 7: Re-run targeted backend tests**

Run:

```bash
cd /Users/huangliang/project/OneOPS-ALL/OneOPS && go test ./app/netpath/service/impl ./app/netpath/api ./app/netpath/router
```

Expected:
- PASS for task-create facade coverage

### Task 2: Front-End Create/View Task Workflow

**Files:**
- Modify: `OneOPS-UI/src/typings/netpath/netpath.ts`
- Modify: `OneOPS-UI/src/api/netpath/netpath.ts`
- Modify: `OneOPS-UI/src/views/topology/NetPathMvp.vue`
- Modify: `OneOPS-UI/src/router/utils.ts`
- Test: `OneOPS-UI/scripts/netpath-mvp-smoke.ts`

- [ ] **Step 1: Write smoke assertions for task-create UI/API surface**

Add smoke checks that require:
- task-create typings
- task-create API requests
- create-diagnostic-task action in `NetPathMvp`
- created task summary card or panel

- [ ] **Step 2: Run smoke script to verify failure**

Run:

```bash
cd /Users/huangliang/project/OneOPS-ALL/OneOPS-UI && npm run smoke:netpath-mvp
```

Expected:
- FAIL with missing task-create surface

- [ ] **Step 3: Add typings and API functions**

Add:
- `NetPathAnalyzeTaskCreateReq`
- `NetPathAnalyzeTaskCreateResp`
- task-create request helper

- [ ] **Step 4: Extend `NetPathMvp.vue`**

Add:
- create diagnostic task CTA in Ticket Draft card
- loading/error state
- created task summary panel
- links to task center / diagnostic logs / analysis run / evidence / probe execution

Also keep the UI honest:
- if task creation has not happened yet, show draft-only state
- if creation succeeded, show `task_id` and follow-up links

- [ ] **Step 5: Align route visibility with real menu entry**

Update the local fallback route so it does not accidentally hide NetPath when menu data is absent during development or smoke flows.

- [ ] **Step 6: Re-run frontend smoke**

Run:

```bash
cd /Users/huangliang/project/OneOPS-ALL/OneOPS-UI && npm run smoke:netpath-mvp
```

Expected:
- PASS

### Task 3: Add Rerun And Compare Backbone

**Files:**
- Modify: `OneOPS/app/netpath/dto/netpath.go`
- Modify: `OneOPS/app/netpath/service/i_netpath.go`
- Modify: `OneOPS/app/netpath/service/impl/netpath.go`
- Modify: `OneOPS/app/netpath/api/netpath.go`
- Modify: `OneOPS/app/netpath/router/netpath.go`
- Modify: `OneOPS/app/netpath/service/impl/netpath_test.go`
- Modify: `OneOPS/app/netpath/api/netpath_test.go`
- Modify: `OneOPS/app/netpath/router/netpath_test.go`
- Modify: `OneOPS-UI/src/typings/netpath/netpath.ts`
- Modify: `OneOPS-UI/src/api/netpath/netpath.ts`
- Modify: `OneOPS-UI/src/views/topology/NetPathMvp.vue`

- [ ] **Step 1: Write failing tests for rerun/compare**

Cover:
- create rerun from existing run against new snapshot
- compare baseline and followup dispositions
- compare hop device sequence
- created task workflow can reference baseline/followup runs in request or summary when available

- [ ] **Step 2: Run targeted tests to verify failure**

Run:

```bash
cd /Users/huangliang/project/OneOPS-ALL/OneOPS && go test ./app/netpath/service/impl ./app/netpath/api ./app/netpath/router
```

Expected:
- FAIL with missing rerun/compare behavior

- [ ] **Step 3: Implement backend rerun and compare endpoints**

Minimum endpoints:

```text
POST /api/netpath/analysis-runs/:code:rerun
GET  /api/netpath/analysis-runs/:code/compare?target_run_code=...
```

- [ ] **Step 4: Add compare panel in `NetPathMvp.vue`**

Show:
- disposition changed or unchanged
- added hops
- removed hops
- changed blocker summary when available

- [ ] **Step 5: Re-run backend and frontend checks**

Run:

```bash
cd /Users/huangliang/project/OneOPS-ALL/OneOPS && go test ./app/netpath/service/impl ./app/netpath/api ./app/netpath/router
cd /Users/huangliang/project/OneOPS-ALL/OneOPS-UI && npm run smoke:netpath-mvp
```

Expected:
- PASS

### Task 4: Probe Enrichment And Traceroute Honesty

**Files:**
- Modify: `OneOPS/app/netpath/service/impl/netpath.go`
- Modify: `OneOPS/app/netpath/service/impl/monitor_probe_dispatcher.go`
- Modify: `OneOPS/app/netpath/service/impl/netpath_test.go`
- Modify: `OneOPS/app/netpath/service/impl/monitor_probe_dispatcher_test.go`
- Modify: `OneOPS-UI/src/views/topology/NetPathMvp.vue`

- [ ] **Step 1: Write failing tests for probe execution visibility**

Cover:
- traceroute item remains explicit when unsupported
- ping results expose timestamps and display-safe fields
- execution summary distinguishes simulated trace vs live probe result

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
cd /Users/huangliang/project/OneOPS-ALL/OneOPS && go test ./app/netpath/service/impl
```

Expected:
- FAIL on missing enriched fields/diagnostics

- [ ] **Step 3: Implement enriched execution mapping**

Do:
- keep unsupported traceroute visible, never silently drop it
- expose latest observed timestamp and executor metadata uniformly
- preserve clear `unsupported` or `blocked` reason for traceroute

- [ ] **Step 4: Re-run probe-related tests**

Run:

```bash
cd /Users/huangliang/project/OneOPS-ALL/OneOPS && go test ./app/netpath/service/impl
```

Expected:
- PASS

## Execution Order

1. Task 1 and Task 2 first for fastest visible closure using real `platform/tasks`
2. Task 3 next for before/after validation
3. Task 4 after that unless an existing traceroute execution path is discovered mid-flight

## Review Checklist

- Closure record is persisted and queryable
- UI can create closure record from current run
- Closure record links back to analysis/probe evidence
- Rerun/compare is visible in UI and backed by API
- Unsupported traceroute is explicit, not hidden
- No new path is marked healthy purely because live probe data is absent
