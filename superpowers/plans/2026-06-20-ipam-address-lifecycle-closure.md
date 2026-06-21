# IPAM Address Lifecycle Closure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a production-oriented IPAM lifecycle flow centered on address assets, covering pool allocation, release, reclaim, fact gating, and journey-based acceptance.

**Architecture:** Keep planning, request, address asset, and fact projection separated. Treat `IPAddressRequest` as a process record, treat `IPAddress` as the lifecycle主体, and let `ipam_address_fact` provide reclaim-time evidence. Frontend journey pages consume explicit lifecycle and fact fields instead of inferring from request status.

**Tech Stack:** Go, GORM, Vue 3, TypeScript, Ant Design Vue

---

### Task Package A: 地址生命周期独立化与地址中心化闭环

**Files:**
- Modify: `OneOPS/app/ipam/dto/ip_address.go`
- Modify: `OneOPS-UI/src/typings/ipam/ip_address.ts`
- Modify: `OneOPS-UI/src/views/ipam/IPAllocationFlow.vue`
- Modify: `OneOPS-UI/src/views/ipam/IPReclaimFlow.vue`
- Modify: `OneOPS-UI/src/views/ipam/IPAgg.vue`

- [ ] Expose `lifecycle_status`, `last_seen_at`, ownership, and request linkage through address DTOs.
- [ ] Update allocation flow to hand off a concrete target address instead of an implicit first allocated address.
- [ ] Update reclaim flow to operate on the selected address in the current request.
- [ ] Show address lifecycle separately from request status in the allocation and reclaim workbenches.

### Task Package B: 回收前事实闸门与强制回收语义

**Files:**
- Modify: `OneOPS/app/ipam/service/impl/ip_address_request.go`
- Modify: `OneOPS/app/ipam/service/impl/ip_address_request_test.go`
- Modify: `OneOPS-UI/src/views/ipam/IPReclaimFlow.vue`
- Modify: `OneOPS-UI/src/api/ipam/ip_address_request.ts`

- [ ] Align frontend reclaim flow with backend `LastSeenAt` force-gate semantics.
- [ ] Show reclaim blockers clearly in the reclaim workbench.
- [ ] Require an explicit user action before sending `force=true`.
- [ ] Preserve release -> releasing -> reclaim confirmation semantics in the UI.

### Task Package C: 地址列表升级为生命周期核对台

**Files:**
- Modify: `OneOPS/app/ipam/dto/ipam_agg.go`
- Modify: `OneOPS/app/ipam/service/impl/ipam_agg.go`
- Modify: `OneOPS-UI/src/typings/ipam/ipam_agg.ts`
- Modify: `OneOPS-UI/src/views/ipam/IPAgg.vue`

- [ ] Surface address lifecycle status in the aggregate list payload.
- [ ] Show lifecycle as a first-class column in the address list.
- [ ] Add list-driven actions for release/reclaim investigation and lifecycle verification.
- [ ] Keep handoff positioning and target highlighting intact.

### Task Package D: 稽核处理台与回收阻断联动

**Files:**
- Modify: `OneOPS-UI/src/views/ipam/IPFactAuditFlow.vue`
- Modify: `OneOPS-UI/src/views/ipam/IPReclaimFlow.vue`
- Modify: `OneOPS-UI/src/views/ipam/IPAgg.vue`

- [ ] Let audit findings communicate reclaim risk in a user-understandable way.
- [ ] Add direct navigation between finding handling and reclaim verification.
- [ ] Distinguish `仍在使用` from `可回收` in the UI language and actions.

### Task Package E: 用户旅程验收与上线收口

**Files:**
- Modify: `OneOPS-UI/src/views/ipam/IPAMOverview.vue`
- Modify: `OneOPS-UI/src/views/ipam/IPAllocationFlow.vue`
- Modify: `OneOPS-UI/src/views/ipam/IPReclaimFlow.vue`
- Modify: `OneOPS-UI/src/views/ipam/IPFactAuditFlow.vue`
- Modify: `OneOPS-UI/src/views/ipam/IPAgg.vue`

- [ ] Walk the three core journeys end-to-end from the frontend.
- [ ] Remove remaining low-value explanatory copy and keep action-oriented guidance only.
- [ ] Normalize lifecycle wording across overview, allocation, reclaim, list, and audit pages.
- [ ] Close remaining visual and interaction inconsistencies that break the production journey.
