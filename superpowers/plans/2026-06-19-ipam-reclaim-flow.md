# IPAM Reclaim Flow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a dedicated Journey 4 frontend flow so operators can find allocated IP addresses and release/reclaim them without using API tools.

**Architecture:** Keep `IP分配流程` focused on allocation. Add `IPReclaimFlow.vue` as a separate temporary mode under `/ipam/address`. The flow lists IP addresses with lifecycle context, filters for assigned/releasing candidates in the UI, and uses the existing address request release/reclaim APIs by IP code. Default smoke stays read-only; mutation is a later gated step.

**Tech Stack:** Vue 3 setup script, Ant Design Vue, existing `ipAddressPageReq`, `ipAddressRequestReleaseReq`, and `ipAddressRequestReclaimReq` APIs.

---

## Files

- Create: `/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/views/ipam/IPReclaimFlow.vue`
- Modify: `/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/views/ipam/IPAgg.vue`
- Modify: `/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/scripts/ipam-journey-smoke.cjs`
- Modify: `/Users/huangliang/project/OneOPS-ALL/docs/superpowers/plans/2026-06-19-global-enterprise-ipam-mvp.md`

## User Journey Acceptance

Journey 4 is accepted when a user can:
- Open `IP回收流程` from `/ipam/address`.
- See allocated/releasing/reclaimed IP address rows with address, lifecycle, pool, tenant, VRF, owner, and source.
- Trigger release for assigned IPs.
- Trigger reclaim for assigned or releasing IPs.
- Refresh and see lifecycle/statistics update.
- Run frontend smoke that verifies the flow is visible and read-only safe.

## Task 1: Add reclaim flow component

- [ ] Create `IPReclaimFlow.vue`.
- [ ] Load IP addresses from `ipAddressPageReq`.
- [ ] Display lifecycle labels and candidate actions.
- [ ] Call release/reclaim APIs with IP code.
- [ ] Refresh the list after mutation.

## Task 2: Add temporary entry mode

- [ ] Add `IP回收流程` button to `IPAgg.vue`.
- [ ] Render `IPReclaimFlow` when selected.
- [ ] Keep existing modes unchanged.

## Task 3: Extend frontend smoke

- [ ] Update `ipam-journey-smoke.cjs` to verify `IP回收流程` visibility.
- [ ] Keep smoke read-only by default.

## Task 4: Verify

- [ ] SFC parse for new component.
- [ ] Run `npm run typecheck`.
- [ ] Run `npm run smoke:ipam-journey`.
