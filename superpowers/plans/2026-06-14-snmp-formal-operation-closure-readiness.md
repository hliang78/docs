# SNMP Formal Operation Closure Readiness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the formal by-target operation loop visible inside the strategy-set drawer so users can see, for the current target and current session, whether they have completed panel preview, recording-rule publish, and formal dashboard save.

**Architecture:** Keep the scope entirely in `OneOps-UI`. Reuse the existing by-target preview, recording-rule, and flat dashboard save states, derive one small session-scoped readiness state from them, and render it in the drawer as a compact formal-closure panel with an explicit next-step hint. Do not add backend APIs, persisted history lookups, or new publish/save mutations.

**Tech Stack:** Vue 3 composition API, existing strategy-set state helpers, TypeScript smoke tests, Ant Design Vue.

---

### Task 1: Lock the target behavior with smoke tests

**Files:**
- Create: `/OneOPS/OneOps-UI/scripts/snmp-strategy-set-formal-closure-state-smoke.ts`
- Modify: `/OneOPS/OneOps-UI/scripts/snmp-strategy-set-dashboard-tree-drawer-smoke.ts`
- Modify: `/OneOPS/OneOps-UI/package.json`

- [ ] Add a dedicated smoke for the new session-scoped formal-closure state helper.
- [ ] Assert status progression at minimum for: no target, preview loaded, publish success for current target, and formal save completed.
- [ ] Extend the drawer smoke to assert the new panel copy and helper wiring are present.
- [ ] Add one npm smoke script entry for the new helper.

### Task 2: Implement the derived formal-closure readiness state

**Files:**
- Create: `/OneOPS/OneOps-UI/src/views/platform/StrategyTemplate/snmpStrategySetFormalClosureState.ts`
- Modify: `/OneOPS/OneOps-UI/src/views/platform/StrategyTemplate/StrategySetDetailDrawer.vue`

- [ ] Create one focused state helper that accepts the current target input, panel preview state, recording-rule state, and flat dashboard save state.
- [ ] Derive compact summary items from existing in-session data only.
- [ ] Derive one explicit current stage label and one explicit next-action hint.
- [ ] Keep target matching strict: only treat publish/save as valid for the currently entered target when `target.target_part` matches exactly after trim.

### Task 3: Render the formal-closure panel in the drawer

**Files:**
- Modify: `/OneOPS/OneOps-UI/src/views/platform/StrategyTemplate/StrategySetDetailDrawer.vue`

- [ ] Render a compact panel near the formal action buttons.
- [ ] Make the copy explicit that this is the formal by-target loop for the current session.
- [ ] Show the current stage, next action, and summary items without adding new actions or changing backend behavior.
- [ ] Keep tree pilot UI untouched except for layout coexistence.

### Task 4: Update handoff and verify

**Files:**
- Modify: `/OneOPS/docs/superpowers/handovers/2026-06-10-snmp-metric-groups-dashboard-family-handoff.md`

- [ ] Record that the drawer now exposes the formal current-session closure state and next-step hint.
- [ ] Run:
  - `cd /OneOPS/OneOps-UI && npm run smoke:snmp-strategy-set-formal-closure-state`
  - `cd /OneOPS/OneOps-UI && npm run smoke:snmp-strategy-set-dashboard-tree-drawer`
  - `cd /OneOPS/OneOps-UI && npm run smoke:snmp-strategy-set-grafana-dashboard-save-action`
  - `cd /OneOPS/OneOps-UI && npm run smoke:snmp-strategy-set-recording-rule-state`
  - `cd /OneOPS/OneOps-UI && npm run typecheck`
  - `git -C /OneOPS/OneOps-UI diff --check`
  - `git -C /OneOPS/docs diff --check`
