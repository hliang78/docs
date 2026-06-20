# Global Enterprise IPAM MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a planning-first IPAM MVP that lets a global enterprise start from address planning, initialize existing data, manage address pools, request/reclaim IPs, and audit planned versus observed addresses.

**Architecture:** Deliver the rollout in thin vertical slices. First make existing address data visible in the IPAM model by backfilling default pools and lifecycle fields. Then add planning entities and UI pages on top of that stable data foundation, followed by workflow pages, observed fact ingestion, audit automation, and release gates.

**Tech Stack:** Go backend, MySQL, Gin API, existing OneOPS DAL/models, Vue/Ant Design frontend, bash/Go smoke scripts, evidence artifacts under `OneOPS/docs/evidence`.

---

## Frontend Closed-Loop Gap Register

The delivery target is an operator-visible IPAM workflow, not just backend APIs or smoke coverage. The current gaps are:

- Planning gap: the overview can display schemes and nodes, but operators still need frontend create flows for schemes and nodes, then later edit/archive/publish flows.
- Pool gap: address pool APIs exist, but operators still need list, create, edit, delete, and reserved range operations from the frontend.
- Request gap: allocation/release/reclaim APIs exist, but operators still need a request workbench to create, approve, reject, release, and reclaim from the frontend.
- Fact gap: observed facts can be upserted by API/smoke, but operators still need a fact list and detail view to understand source, device, interface, MAC, confidence, and timestamps.
- Audit gap: audit findings can be generated and resolved by API/smoke, but operators still need a finding queue with filter, detail, resolve, and evidence context.
- Navigation gap: the temporary `/ipam/address` entry is useful for testing, but the final IPAM entry should expose Planning, Pools, Requests, Facts, Audit, and Statistics as first-class work areas.
- Release gap: backend smoke covers many flows, but frontend smoke must cover the visible workflow before launch.

## Frontend Closed-Loop Milestones

## Acceptance User Journeys

后续验收以用户旅程为主，不以单个接口或单个按钮为主。

### Journey 1: 建立企业地址规划

Actor: IP 地址规划负责人。

Goal: 从一个企业级根地址空间开始，逐级拆分到区域、站点、业务或安全区域。

Happy path:
- 用户进入 `IPAM总览`。
- 用户创建地址规划方案，填写方案名称、根地址空间、归属信息和状态。
- 用户在方案下创建规划节点，填写 CIDR、区域、站点、业务、安全区域、用途和状态。
- 系统拒绝不在父级范围内或与同级重叠的 CIDR。
- 用户回到总览后看到方案数、规划节点数和节点列表刷新。

Acceptance signals:
- 前端可以完成创建，不需要 API 工具。
- 后端 CIDR 校验错误能在前端被用户看见。
- 刷新页面后规划数据仍存在。

### Journey 2: 将规划转为可分配地址池

Actor: IP 地址管理员。

Goal: 在规划后的网段内建立可管理、可统计、可保留的地址池。

Happy path:
- 用户在 `地址池操作台` 查看现有地址池。
- 用户创建地址池，填写网段编码、CIDR、起止 IP、租户、平台 VRF、安全区域、站点、用途和容量阈值。
- 用户为地址池创建保留地址段，例如网关、VIP、网络设备或不可自动分配范围。
- 系统刷新地址池列表、保留段列表和容量统计。

Acceptance signals:
- 前端可以创建地址池和保留段。
- 前端可以删除测试地址池和测试保留段。
- 地址池利用率表与操作台数据能同步刷新。

### Journey 3: 申请并分配 IP 地址

Actor: 应用负责人、网络管理员或运维人员。

Goal: 从地址池发起 IP 申请，并由平台完成分配。

Happy path:
- 用户在 `IP申请与回收` 操作台创建分配申请。
- 用户选择地址池，填写申请人、归属对象、数量、期望 IP、用途和业务系统。
- 用户提交后看到申请记录。
- 用户审批分配申请。
- 系统生成已分配地址并刷新统计。

Acceptance signals:
- 前端可以创建申请并审批分配。
- 已完成申请能看到分配出的 IP 编码或地址。
- 地址生命周期和利用率随分配刷新。

### Journey 4: 释放与回收 IP 地址

Actor: IP 地址管理员。

Goal: 将已分配地址从使用状态退回可用池。

Happy path:
- 用户在申请记录中找到已分配地址。
- 用户执行释放操作。
- 用户执行回收操作。
- 系统刷新申请状态、地址生命周期和地址池容量。

Acceptance signals:
- 前端可以对已分配地址触发释放和回收。
- 回收后的统计和列表能刷新。
- 失败原因能直接显示给用户。

Current delivery:
- Done: added a dedicated `IP回收流程` mode under the temporary `/ipam/address` entry.
- Done: operators can inspect allocation/request-derived reclaim candidates, see pool, preferred IP, allocated address, owner, and business system context.
- Done: release and reclaim buttons are wired to existing backend APIs and guarded when the allocated IP code is missing.
- Verified: `npm run typecheck` passed and `npm run smoke:ipam-journey` passed with `IP回收流程` evidence.
- Gap: the current frontend `IPAddressResp` and backend address list response do not expose a complete address lifecycle view for reclaim candidates. Some existing completed requests also return empty `allocated_addresses`, so mutation smoke must wait for backend response fields or a dedicated reclaim candidate API.

### Journey 5: 采集现网事实并稽核

Actor: 网络运维或稽核人员。

Goal: 将现网发现的 IP 使用事实与规划/地址池/申请记录比对，处理风险。

Happy path:
- 用户查看现网事实列表，识别来源设备、接口、MAC、VRF、置信度和时间。
- 用户生成或查看稽核发现。
- 用户处理未规划、重复观测、归属不一致、MAC 不一致等发现。
- 用户将发现标记为已解决。

Acceptance signals:
- 前端可以查看事实和稽核发现。
- 前端可以解决发现。
- 未解决稽核数量随处理刷新。

### Journey 6: 运营总览与上线验收

Actor: 平台负责人或验收人员。

Goal: 从一个入口判断 IPAM 是否具备上线所需的规划、池化、申请、回收、事实和稽核闭环。

Happy path:
- 用户进入 `IPAM总览`。
- 用户看到地址池数、规划地址数、利用率、待处理申请、现网事实、未解决稽核。
- 用户能从总览进入规划、地址池、申请、事实、稽核操作区。
- 验收人员执行前端 smoke，留下证据。

Acceptance signals:
- 所有核心旅程可通过前端完成。
- browser smoke 和 backend smoke 都通过。
- 证据目录中有可追溯的验收结果。

### Milestone A: Planning frontend closure

Goal: an operator can create a planning scheme, create planning nodes under a scheme or parent node, see overlap errors from the backend, and immediately see refreshed planning data.

Acceptance:
- `/#/ipam/address` -> `IPAM总览` shows planning scheme and node counts.
- User can click `新建方案`, fill name/root CIDR/owner/status, submit, and see the new scheme.
- User can click `新增节点`, choose scheme and optional parent, fill CIDR/scope/purpose/status, submit, and see the new node.
- Backend validation errors, including CIDR overlap, are shown as Ant Design error messages.
- `npm run typecheck` passes.

### Milestone B: Pool frontend closure

Goal: an operator can manage address pools and reserved ranges without using API tools.

Acceptance:
- User can list and filter pools.
- User can create/edit/delete a pool.
- User can create/update/delete reserved ranges from pool context.
- Pool capacity refreshes after mutation.

Progress:
- Done: added an address pool workbench to `/#/ipam/address` -> `IPAM总览`.
- Done: operators can see address pool rows and reserved range rows from the frontend.
- Done: operators can open `新建地址池` and `新建保留段` drawers.
- Done: create/delete functions are wired to existing backend APIs and refresh IPAM data after mutation.
- Remaining: add edit flows, safer delete constraints for default/backfilled pools, and browser smoke for pool/reserved range mutation.

### Milestone C: Request frontend closure

Goal: an operator can allocate, release, and reclaim addresses from the frontend.

Acceptance:
- User can create allocation requests.
- User can approve allocation requests.
- User can release and reclaim assigned IPs.
- Request status and allocated addresses are visible.

Progress:
- Done: added an `IP申请与回收` workbench to `/#/ipam/address` -> `IPAM总览`.
- Done: request records are loaded from the backend and displayed with type, status, pool, preferred IP, quantity, purpose, and business system.
- Done: operators can open `新建分配申请`; the drawer defaults from the selected pool and auto-fills tenant, platform VRF, site, and security zone when available.
- Done: create request, approve allocation, release, and reclaim actions are wired to existing backend APIs and refresh IPAM statistics after mutation.
- Verified: `npm run typecheck` passed, and browser inspection confirmed the workbench plus request drawer are visible.
- Superseded: inline request operation in `IPAM总览` was removed because the overview should not host every IPAM operation.
- Done: added a dedicated `IP分配流程` mode under the temporary `/ipam/address` entry with a three-step minimal flow: select pool, fill request, submit/approve.
- Done: `IPAM总览` now keeps statistics and a lightweight handoff hint instead of the request workbench.
- Verified: `npm run typecheck` passed, the new flow loads address pools and recent requests, and the overview shows the handoff hint.
- Remaining: run a mutation browser smoke that creates a safe test request, approves it, then releases/reclaims the allocated address with cleanup evidence.

### Milestone D: Facts and audit frontend closure

Goal: an operator can inspect observed facts, generate or review audit findings, and resolve findings.

Acceptance:
- User can list observed facts with source/device/interface/MAC context.
- User can generate a finding from a selected fact where applicable.
- User can list and resolve findings.
- Statistics reflect resolved/unresolved counts.

Progress:
- Done: added a dedicated `现网事实与稽核` mode under the temporary `/ipam/address` entry.
- Done: operators can view observed facts with source, status, device, interface, MAC, VRF, pool, security zone, confidence, and last seen time.
- Done: operators can manually upsert a smoke-safe observed fact from the frontend.
- Done: operators can generate audit findings from a selected fact.
- Done: operators can view audit findings with type, severity, status, address, pool, suggested action, and last detected time.
- Done: operators can mark unresolved findings as resolved when present.
- Verified: SFC parse passed, `npm run typecheck` passed, and browser inspection confirmed the facts and findings data render in `现网事实与稽核`.
- Remaining: run a mutation browser smoke that upserts a new fact, generates a finding, resolves it, and confirms the overview statistics refresh.

### Milestone E: Frontend smoke and release gate

Goal: the visible IPAM workflow becomes release-verifiable.

Acceptance:
- Browser smoke covers entering IPAM总览, creating a scheme, creating a node, creating pool/request/fact/finding flows when safe.
- Evidence artifacts are written under `OneOPS/docs/evidence/ipam`.
- Known cleanup behavior is documented.

Progress:
- Done: added `npm run smoke:ipam-journey` in `OneOPS-UI` for read-only frontend journey validation.
- Done: smoke covers `地址列表`, `IPAM总览`, `IP分配流程`, `IP回收流程`, and `现网事实与稽核` entry visibility.
- Done: smoke records screenshots and summary under `docs/evidence/ipam/frontend-journeys`.
- Verified: `npm run smoke:ipam-journey` passed and produced evidence `20260618-182741-SUMMARY.md`.
- Remaining: add a gated mutation smoke for safe test allocation, fact upsert, finding generation, finding resolve, and cleanup notes.

### Task 1: Existing Data Backfill Foundation

**Files:**
- Create: `/Users/huangliang/project/OneOPS-ALL/OneOPS/scripts/ipam_backfill_existing_data.go`
- Use: `/Users/huangliang/project/OneOPS-ALL/OneOPS/scripts/ipam_smoke.sh`

- [ ] **Step 1: Add a dry-run capable backfill tool**

Create `scripts/ipam_backfill_existing_data.go` that connects through env-provided MySQL settings, reads IPv4 rows from `prefix`, creates one default pool per prefix when missing, and updates legacy `ip_address` rows with `pool_code`, `lifecycle_status`, and `source`.

- [ ] **Step 2: Run dry-run**

Run:

```bash
MYSQL_HOST=192.168.0.164 MYSQL_PORT=3606 MYSQL_DB=UniOPS MYSQL_USER=UniOPS MYSQL_PASSWORD='<password>' go run scripts/ipam_backfill_existing_data.go
```

Expected: the tool prints planned pool creations and IP updates, but does not write.

- [ ] **Step 3: Apply backfill**

Run:

```bash
IPAM_BACKFILL_APPLY=1 MYSQL_HOST=192.168.0.164 MYSQL_PORT=3606 MYSQL_DB=UniOPS MYSQL_USER=UniOPS MYSQL_PASSWORD='<password>' go run scripts/ipam_backfill_existing_data.go
```

Expected: default pools are created and old IP rows get pool/lifecycle/source fields.

- [ ] **Step 4: Verify with smoke**

Run:

```bash
IPAM_SMOKE_TOKEN='<token>' ./scripts/ipam_smoke.sh
```

Expected: smoke passes, `total_pool_count` is greater than zero, and lifecycle no longer shows all addresses as `unknown`.

### Task 2: Planning Scheme Domain

**Files:**
- Create backend model/API/service/router files for address planning schemes and planning nodes.
- Create frontend API/types for planning schemes and planning nodes.

- [ ] **Step 1: Add planning scheme model**

Create a scheme entity with code, name, enterprise CIDR, status, description, and owner fields.

- [ ] **Step 2: Add planning node model**

Create a hierarchical node entity with parent code, scheme code, CIDR, region, site, business unit, environment, security zone, purpose, and status.

- [ ] **Step 3: Add overlap validation**

Validate that child CIDRs stay inside the parent CIDR and sibling CIDRs do not overlap.

- [ ] **Step 4: Add scheme/node CRUD APIs**

Expose create, update, detail, list, publish, and archive endpoints.

- [ ] **Step 5: Add backend tests**

Cover parent containment, sibling overlap rejection, and publish preconditions.

### Task 3: Planning-First Frontend Entry

**Files:**
- Modify `/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/views/ipam/IPAgg.vue`
- Create planning scheme and planning tree Vue components.

- [ ] **Step 1: Replace temporary total-overview entry with planning-first entry**

Add tabs or cards for global planning, pools, requests, facts, audit, and statistics.

- [ ] **Step 2: Add planning tree**

Show enterprise CIDR -> region -> site -> pool hierarchy with capacity indicators.

- [ ] **Step 3: Add node creation drawer**

Allow users to split a parent CIDR into child planning nodes with validation feedback.

### Task 4: Address Pool Productization

**Files:**
- Add frontend address pool list/detail/create/edit pages.
- Reuse existing backend address pool APIs.

- [ ] **Step 1: Add pool list and filters**

Filter by tenant, region, site, security zone, platform VRF, purpose, status, and capacity threshold.

- [ ] **Step 2: Add create/edit flow**

Validate pool range, CIDR containment, and required fields.

- [ ] **Step 3: Add reserved range management inside pool detail**

Let users create and edit reserved ranges from the pool context.

### Task 5: IP Request and Reclaim Productization

**Files:**
- Add frontend request list/detail/create/approve/release/reclaim pages.
- Reuse existing backend request APIs and add missing reject/cancel APIs.

- [ ] **Step 1: Add request list**

Show request type, requester, pool, status, quantity, allocated addresses, and timestamps.

- [ ] **Step 2: Add request create wizard**

Guide users through region/site/security zone/purpose/quantity and recommend a pool.

- [ ] **Step 3: Add approve/reject/cancel operations**

Approve allocates IPs. Reject and cancel preserve audit history.

- [ ] **Step 4: Add release/reclaim operations**

Release marks an IP as releasing. Reclaim returns it to available after checks.

### Task 6: Observed Facts and Audit Automation

**Files:**
- Add scheduled audit job.
- Connect collection outputs to `ipam_address_fact`.
- Add frontend fact and finding pages.

- [ ] **Step 1: Add fact ingestion adapter**

Map device/interface/MAC/VRF/security-zone observations into IPAM facts.

- [ ] **Step 2: Add scheduled audit generation**

Generate findings for unplanned, duplicate, stale, owner mismatch, and MAC mismatch cases.

- [ ] **Step 3: Add audit handling UI**

Allow users to filter, acknowledge, resolve, and inspect findings.

### Task 7: Release Gates and Governance

**Files:**
- Extend `/Users/huangliang/project/OneOPS-ALL/OneOPS/scripts/ipam_smoke.sh`
- Add frontend smoke scripts under `/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/scripts`
- Add release evidence docs under `/Users/huangliang/project/OneOPS-ALL/OneOPS/docs/evidence/ipam`

- [ ] **Step 1: Add backfill smoke**

Assert pool count and lifecycle distribution after backfill.

- [ ] **Step 2: Add mutation smoke to release checklist**

Run mutation smoke in test environments only.

- [ ] **Step 3: Add frontend smoke**

Check planning entry, pool list, request list, statistics, facts, and audit pages.

- [ ] **Step 4: Add operating guide**

Document initialization, smoke usage, rollback, and known cleanup behavior.
