# IPAM Facts and Audit Flow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a dedicated frontend flow for Journey 5 so operators can inspect observed IP facts and resolve audit findings without using API tools.

**Architecture:** Keep `IPAM总览` as a statistics surface. Add a focused `IPFactAuditFlow.vue` component under the temporary `/ipam/address` entry. The flow has two work areas: observed facts and audit findings. It reads existing backend data first, supports manual fact upsert for smoke-safe testing, and supports resolving findings when backend APIs expose that action.

**Tech Stack:** Vue 3 setup script, Ant Design Vue, existing OneOPS IPAM fact and audit APIs, current `/ipam/address` temporary mode switch.

---

## Files

- Create: `/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/views/ipam/IPFactAuditFlow.vue`
- Modify: `/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/views/ipam/IPAgg.vue`
- Modify: `/Users/huangliang/project/OneOPS-ALL/docs/superpowers/plans/2026-06-19-global-enterprise-ipam-mvp.md`

## User Journey Acceptance

Journey 5 is accepted when a user can:
- Open `现网事实与稽核` from `/ipam/address`.
- See observed facts with source, device, interface, MAC, VRF, confidence, and timestamps.
- Add or upsert a smoke-safe observed fact from the frontend.
- See audit findings with type, severity, status, observed IP, pool, and evidence context.
- Resolve an unresolved finding from the frontend when a finding exists.
- Return to `IPAM总览` and see unresolved audit statistics reflect backend state after refresh.

## Task 1: Add facts and audit flow component

- [ ] Create `IPFactAuditFlow.vue`.
- [ ] Load observed facts from the fact list API.
- [ ] Load audit findings from the audit list API.
- [ ] Add a compact observed fact form for manual upsert.
- [ ] Add a table for facts and a table for findings.
- [ ] Add resolve action for findings.

## Task 2: Add temporary entry mode

- [ ] Add `现网事实与稽核` button to `IPAgg.vue`.
- [ ] Render `IPFactAuditFlow` when selected.
- [ ] Keep `地址列表`, `IPAM总览`, and `IP分配流程` unchanged.

## Task 3: Verify

- [ ] Run `npm run typecheck` from `/Users/huangliang/project/OneOPS-ALL/OneOPS-UI`.
- [ ] Browser-open `/ipam/address`.
- [ ] Confirm `现网事实与稽核` opens.
- [ ] Confirm fact and finding tables render backend data or clear empty states.
- [ ] If safe, submit one smoke fact and confirm it appears after refresh.
