# IPAM Allocation Flow Page Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move IP allocation out of the overloaded IPAM overview into a dedicated minimal frontend flow that can be used for journey-based acceptance.

**Architecture:** Keep `IPAMOverview.vue` as a statistics and entry page. Add a focused `IPAllocationFlow.vue` component for selecting a pool, filling request basics, submitting a request, approving allocation, and showing recent requests. Use the current temporary `/ipam/address` entry to switch between address list, overview, and allocation flow without changing backend routes.

**Tech Stack:** Vue 3 setup script, Ant Design Vue, existing IPAM address pool and address request APIs, existing OneOPS UI route/menu behavior.

---

## Files

- Modify: `/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/views/ipam/IPAgg.vue`
- Modify: `/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/views/ipam/IPAMOverview.vue`
- Create: `/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/views/ipam/IPAllocationFlow.vue`

## Task 1: Add dedicated allocation flow component

- [ ] Create `IPAllocationFlow.vue` with a three-step visual flow: select pool, fill request, submit/approve.
- [ ] Load address pools from `addressPoolPageReq`.
- [ ] Load recent allocation requests from `ipAddressRequestPageReq`.
- [ ] Auto-fill tenant, platform VRF, security zone, and site from the selected pool.
- [ ] Submit allocation requests with `ipAddressRequestCreateReq`.
- [ ] Approve submitted requests with `ipAddressRequestApproveAndAllocateReq`.
- [ ] Refresh pools and request list after mutations.

## Task 2: Convert temporary entry into clear work modes

- [ ] Replace the single toggle in `IPAgg.vue` with three buttons: `地址列表`, `IPAM总览`, `IP分配流程`.
- [ ] Render `IPAllocationFlow` only when the user chooses `IP分配流程`.
- [ ] Keep existing address list behavior unchanged.

## Task 3: De-emphasize operations inside overview

- [ ] Keep overview statistics and planning/pool visibility.
- [ ] Remove the large inline request workbench from `IPAMOverview.vue`.
- [ ] Add a compact hint that IP allocation should be performed from `IP分配流程`.

## Task 4: Verify

- [ ] Run `npm run typecheck` from `/Users/huangliang/project/OneOPS-ALL/OneOPS-UI`.
- [ ] Open `/ipam/address` in the browser.
- [ ] Confirm `IP分配流程` opens a separate flow component.
- [ ] Confirm the flow can display address pools and recent requests.
