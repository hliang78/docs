# IPAM Production Launch Journey Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the current IPAM MVP into production-ready OneOPS IP address management, validated by complete frontend user journeys rather than isolated page checks.

**Architecture:** Keep planning scheme/node as planning baseline, keep Prefix as subnet master data, and make address pool, reservation, allocation request, release/reclaim, facts, and audit findings the operational objects. The frontend should guide users through separate but connected journeys: plan, prepare inventory, allocate, reclaim, audit, and govern. Backend services must enforce the same lifecycle and guardrails the UI explains.

**Tech Stack:** OneOPS Go backend, MySQL, Vue 3, TypeScript, Ant Design Vue, existing OneOPS routing/API/request patterns, Playwright/CDP-based `scripts/ipam-journey-smoke.cjs` acceptance.

---

## Product and UX Principles

This is a production operations surface, not a demo dashboard. The UI must feel calm, compact, inspectable, and safe during real change windows.

- Do not put every operation into one page.
- Keep the top IPAM entry as a control hub, then route users into purpose-built workflows.
- Prefer Ant Design Vue patterns already used by OneOPS.
- Show names first, keep codes visible and copyable where operationally useful.
- Every mutation must make the consequence clear before submission.
- Empty states must say what the user should do next.
- Error states must show actionable backend messages.
- Status color must always be paired with text.
- Avoid decorative metrics, vague success copy, and hidden fallback behavior.

## Production User Journeys Used for Acceptance

### Journey 1: Global address planning baseline

A network planner enters IPAM, creates or selects a global planning scheme, splits address space into region/site/business/environment planning nodes, and understands that these nodes are planning baseline rather than workflow objects.

Acceptance:

- User can find planning entry from IPAM hub.
- Planning scheme/node drawers do not expose draft/active/archive workflow states.
- Region, site, business, environment, and purpose are selectable when authoritative options exist.
- Security zone remains manually fillable until authoritative source is agreed.
- Planning node explains its relationship to Prefix.

### Journey 2: Prefix master data fusion

A planner converts useful planned ranges into Prefix master data or binds existing Prefix records, then creates an address pool only from Prefix.

Acceptance:

- Address pool creation cannot silently use planning node code as `prefix_code`.
- User can clearly choose an existing Prefix by name and code.
- If Prefix is missing, user receives a clear next action.
- Production path supports one of these explicit flows:
  - Bind existing Prefix to an address pool.
  - Create Prefix from planning node with explicit tenant, VRF, name, and CIDR confirmation.
- Prefix remains the subnet source of truth.

### Journey 3: Address pool and reservation preparation

An operator creates an address pool from Prefix, defines assignable range, reserves protected ranges, and sees guardrails before allocation.

Acceptance:

- Address pool status means only operational enabled/disabled.
- Disabled pools are not shown as allocatable and are rejected by backend allocation.
- Allocation policy is fixed to `first_available` for launch.
- Reserved ranges must be inside the pool.
- Reserved ranges cannot overlap existing reservations in the same pool.
- Reserved ranges block automatic allocation unless special allocation is explicitly enabled.
- UI explains special allocation before users can rely on it.

### Journey 4: IP allocation request closure

A requester selects an address pool, fills ownership and business intent, submits a request, and an operator completes allocation.

Acceptance:

- Request creation lands in user-facing `待处理` state.
- Operator action completes allocation and lands in `已完成` state.
- Draft and approved remain compatibility states, not primary states.
- Allocated address is visible in the request table and latest-result card.
- Missing pool, requester, or owner blocks submission with clear copy.
- Backend rejects allocation from disabled pool, exhausted pool, invalid preferred IP, and reserved IP without special allocation.

### Journey 5: IP release and reclaim closure

An operator finds assigned IPs, starts release, then confirms reclaim so the address returns to inventory.

Acceptance:

- UI labels release as `发起释放`.
- Release changes lifecycle to `releasing` and blocks reallocation.
- UI labels reclaim as `确认回收`.
- Confirmed reclaim returns address to `available` inventory.
- `reclaimed` is not presented as a stable current inventory state.
- Release/reclaim operations are auditable.

### Journey 6: Observed facts and audit closure

An operator or collector records observed IP facts, generates audit findings, and resolves risk.

Acceptance:

- Manual fact upsert remains available for testing and operations supplement.
- Automatic collection has a documented ingestion path into IP facts.
- Findings are generated as `未解决`.
- Resolving a finding marks it as `已解决`.
- Acknowledged/ignored remain backend-compatible but are not primary launch flow states.
- Duplicate observations do not create noisy duplicate findings.

### Journey 7: Statistics and governance visibility

An operator uses the IPAM hub to understand address inventory, utilization, pending requests, release/reclaim work, and unresolved audit risk.

Acceptance:

- Statistics match backend lifecycle semantics.
- `releasing` appears as blocked transition capacity, not available capacity.
- Filters by tenant, region/site, security zone, platform VRF, and pool behave consistently.
- Empty statistics explain whether there is no data, no matching filter result, or a backend load failure.

## UI Direction for Production

### Information architecture

Keep five top-level IPAM entry buttons for launch, but refine them into an intentional journey map:

1. `地址列表`: inventory lookup and current IP lifecycle.
2. `IPAM总览`: statistics, risk, and journey entry hub.
3. `地址规划与地址池`: planning baseline, Prefix binding, pool, reservation.
4. `IP分配流程`: request and allocation closure.
5. `IP回收流程`: release and reclaim closure.
6. `现网事实与稽核`: fact ingestion and finding closure.

If route budget is constrained, `地址规划与地址池` may remain inside current overview during the first production increment, but the UI should visually separate planning baseline from operating inventory.

### Visual design

Use the existing OneOPS product design language:

- Light tinted-neutral background for long-session readability.
- Compact but breathable card rhythm.
- Blue-violet accent only for current primary action and active navigation.
- Semantic colors for status only.
- No gradient text, decorative glass, or marketing-style hero metrics.
- Table density should remain operational, but section headers and alerts should reduce cognitive load.
- Drawers should use grouped sections, helper text, and explicit consequences.

### Interaction design

- Prefer progressive disclosure over giant forms.
- Keep destructive or lifecycle-changing actions behind popconfirm with consequence copy.
- After successful mutations, refresh only affected sections where possible.
- Show skeleton/loading on section, not full-page when only a table is loading.
- Show `复制编码` affordance for operational codes where practical.
- Use disabled controls with explanation when a feature is intentionally fixed for launch.

## Implementation Tracks

### Track A: Journey map and route cleanup

**Files:**

- Modify: `OneOPS-UI/src/views/ipam/IPAgg.vue`
- Modify: `OneOPS-UI/src/router` IPAM route registration if needed
- Modify: `OneOPS-UI/scripts/ipam-journey-smoke.cjs`

Steps:

- [x] Update IPAM hub copy so it presents journeys instead of temporary test buttons.
- [x] Keep existing routes stable for smoke and user testing.
- [x] Add route labels that match the production user journeys.
- [x] Smoke acceptance: user can enter every journey from the hub.

### Track B: Planning node to Prefix production path

**Files:**

- Modify: `OneOPS-UI/src/views/ipam/IPAMOverview.vue` or split to `OneOPS-UI/src/views/ipam/IPPlanningPoolFlow.vue`
- Modify: `OneOPS-UI/src/api/base/prefix.ts`
- Modify: `OneOPS-UI/src/typings/base/prefix.ts`
- Modify: backend Prefix service only if create/bind API is insufficient
- Modify: `OneOPS-UI/scripts/ipam-journey-smoke.cjs`

Steps:

- [x] Add visible `关联 Prefix` or `生成 Prefix` action on planning node rows.
- [ ] If binding existing Prefix, show Prefix selector with name, code, tenant, VRF, and CIDR.
- [ ] If generating Prefix, require tenant, platform VRF, Prefix name, and CIDR confirmation.
- [x] Prevent planning node code from being submitted as address pool `prefix_code`.
- [ ] Add empty state: `暂无 Prefix，请先关联或生成 Prefix`.
- [ ] Smoke acceptance: create/select planning node, see Prefix action, create address pool only after Prefix is available.

### Track C: Address pool production guardrails

**Files:**

- Modify: `OneOps/app/ipam/service/impl/address_pool.go`
- Modify: `OneOps/app/ipam/service/impl/reserved_range.go`
- Modify: `OneOps/app/ipam/service/impl/ip_address_request.go`
- Modify: `OneOPS-UI/src/views/ipam/IPAMOverview.vue`
- Modify: `OneOPS-UI/src/views/ipam/IPAllocationFlow.vue`
- Modify: backend unit tests under `OneOps/app/ipam/service/impl/*_test.go`
- Modify: `OneOPS-UI/scripts/ipam-journey-smoke.cjs`

Steps:

- [x] Backend rejects allocation from disabled pools.
- [x] Frontend hides disabled pools from default allocation selection or tags them as unavailable.
- [x] Backend validates reserved range is inside pool range.
- [x] Backend rejects overlapping reserved ranges in the same pool.
- [ ] Backend preserves existing reserved-range special allocation rule.
- [ ] Frontend copy explains disabled pools and reserved ranges.
- [ ] Smoke acceptance: reserved guardrail and disabled-pool copy visible; backend tests pass for invalid reservations.

### Track D: Allocation request production closure

**Files:**

- Modify: `OneOPS-UI/src/views/ipam/IPAllocationFlow.vue`
- Modify: `OneOps/app/ipam/service/impl/ip_address_request.go`
- Modify: `OneOps/app/ipam/dto/ip_address_request.go` if audit fields are missing
- Modify: `OneOPS-UI/scripts/ipam-journey-smoke.cjs`

Steps:

- [ ] Keep user-facing statuses as `待处理`, `已完成`, `已拒绝`, `已取消`.
- [ ] Ensure allocated addresses always load for completed requests.
- [x] Add clear error copy for exhausted pool, invalid preferred IP, reserved IP, and disabled pool.
- [ ] Add operator/audit metadata if backend currently lacks it.
- [x] Smoke acceptance: submit allocation request, execute allocation, see assigned address and completed status.

### Track E: Release and reclaim lifecycle correctness

**Files:**

- Modify: `OneOps/app/ipam/service/impl/ip_address_request.go`
- Modify: `OneOps/app/ipam/service/impl/ipam_statistics.go`
- Modify: `OneOPS-UI/src/views/ipam/IPReclaimFlow.vue`
- Modify: `OneOPS-UI/src/views/ipam/IPAMOverview.vue`
- Modify: backend lifecycle tests
- Modify: `OneOPS-UI/scripts/ipam-journey-smoke.cjs`

Steps:

- [x] Release sets lifecycle to `releasing`.
- [x] Allocation skips `releasing` addresses.
- [x] Reclaim sets lifecycle to `available` after confirmation.
- [x] Statistics treat `releasing` as blocked capacity.
- [x] UI does not present `reclaimed` as a stable current state.
- [ ] Smoke acceptance: release/reclaim semantics visible; backend tests prove lifecycle transition.

### Track F: Audit fact ingestion and finding closure

**Files:**

- Modify: `OneOPS-UI/src/views/ipam/IPFactAuditFlow.vue`
- Modify: `OneOps/app/ipam/service/impl/ip_address_fact.go`
- Modify: `OneOps/app/ipam/service/impl/ip_address_audit_finding.go`
- Modify: backend audit tests
- Modify: collector/import integration docs if present
- Modify: `OneOPS-UI/scripts/ipam-journey-smoke.cjs`

Steps:

- [x] Document or expose automatic fact ingestion path.
- [x] Keep manual upsert as operations supplement.
- [x] Ensure duplicate observations update existing open findings instead of creating noise.
- [x] Keep UI primary statuses as `未解决` and `已解决`.
- [ ] Smoke acceptance: upsert fact, generate finding, resolve finding.

### Track G: Production UI polish and accessibility

**Files:**

- Modify: all IPAM Vue pages touched above
- Create or modify shared IPAM UI helpers only if repeated patterns justify it
- Modify: `OneOPS-UI/scripts/ipam-journey-smoke.cjs`

Steps:

- [x] Replace temporary/test copy with production journey copy.
- [x] Add section-specific empty states with next action.
- [ ] Add section-specific loading states.
- [ ] Ensure all status colors have text labels.
- [ ] Ensure drawer primary actions are clear and consequence-aware.
- [ ] Ensure mobile/tablet layouts remain usable for core read paths.
- [ ] Smoke acceptance: all journey pages load with production labels and no temporary wording.

### Track H: End-to-end operation smoke

**Files:**

- Modify: `OneOPS-UI/scripts/ipam-journey-smoke.cjs`
- Create optional fixture helper under `OneOPS-UI/scripts/` if needed
- Use remote MySQL-backed environment already configured for test data

Steps:

- [x] Keep current visibility smoke as fast baseline.
- [ ] Add operation smoke for Prefix, pool, reservation, allocation, release, reclaim, fact, finding, resolve.
- [x] Add operation smoke foundation for safe validation-feedback paths without writing database records.
- [ ] Make operation smoke data idempotent by using timestamped names and querying before create where possible.
- [ ] Capture evidence screenshots for each journey.
- [ ] Final acceptance command: `npm run typecheck && npm run smoke:ipam-journey` plus operation smoke command if separated.

## Launch Readiness Checklist

- [ ] All P0 journeys pass smoke.
- [ ] Backend lifecycle and reservation unit tests pass.
- [ ] No visible planning workflow states on planning scheme/node.
- [ ] Prefix is the only address-pool subnet source of truth.
- [ ] Disabled pools cannot allocate.
- [ ] Reserved ranges cannot overlap and cannot escape pool bounds.
- [ ] Allocation request can complete and show allocated address.
- [ ] Release/reclaim lifecycle is correct.
- [ ] Audit finding closes from unresolved to resolved.
- [ ] UI copy no longer says temporary, demo, or future replacement for launch-critical flows.
- [ ] Error messages are understandable to operators.
- [ ] Evidence screenshots exist for each journey.

## Execution Policy

This plan should be executed as one long-running production launch task. Do not ask for confirmation between small implementation steps. Stop only for decisions with product consequences, such as changing the authoritative source of Prefix, changing security-zone source, or introducing formal approval workflow.
