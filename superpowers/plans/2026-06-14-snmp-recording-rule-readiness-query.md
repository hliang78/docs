# SNMP Recording Rule Readiness Query Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add one minimal backend-readable readiness query for the formal by-target path so the frontend can determine whether the current target already has a successful recording-rule publish before formal dashboard save.

**Architecture:** Reuse the existing append-only `platform_snmp_recording_rule_publish_records` table. Add one strict read-only resolver/API route that returns the latest publish record for `strategy_set_id + target_part`, plus a small frontend consumer that prefers this backend readiness over current-session memory for the formal closure panel and flat dashboard save guard. Do not add new publish actions, orchestration, tree-path changes, or generic history browsing.

**Tech Stack:** Go resolver/API/router tests, existing GORM query proxy, Vue 3 state helpers, TypeScript smoke tests.

---

### Task 1: Lock backend readiness behavior with tests

**Files:**
- Modify: `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver_test.go`
- Modify: `/OneOPS/OneOps/app/platform/api/teleabs_metric_contract_http_test.go`
- Modify: `/OneOPS/OneOps/app/platform/router/platform.go`
- Modify: `/OneOPS/OneOps/app/platform/router/platform_bidi.go`

- [ ] Add a resolver test that saves multiple publish records and asserts the latest record for the same `strategy_set_id + target_part` is returned.
- [ ] Assert the returned readiness distinguishes successful publish vs failed/non-existent publish.
- [ ] Add API/route tests for the new strict by-target readiness endpoint.

### Task 2: Implement backend readiness query

**Files:**
- Modify: `/OneOPS/OneOps/app/platform/dto/snmp_metric_contract.go`
- Modify: `/OneOPS/OneOps/app/platform/service/i_metric_capability_contract_resolver.go`
- Modify: `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver.go`
- Modify: `/OneOPS/OneOps/app/platform/api/teleabs.go`
- Modify: `/OneOPS/OneOps/app/platform/router/platform.go`
- Modify: `/OneOPS/OneOps/app/platform/router/platform_bidi.go`

- [ ] Add a DTO for `strategy_set_id + target_part -> latest recording rule readiness`.
- [ ] Add one resolver method that queries `platform_snmp_recording_rule_publish_records` ordered by newest record first.
- [ ] Expose one read-only API route under the existing metric-contract by-target namespace.
- [ ] Keep success semantics narrow: only successful publish statuses count as ready.

### Task 3: Lock frontend backend-priority consumption with smoke tests

**Files:**
- Modify: `/OneOPS/OneOps-UI/scripts/snmp-strategy-set-formal-closure-state-smoke.ts`
- Modify: `/OneOPS/OneOps-UI/scripts/snmp-strategy-set-dashboard-tree-drawer-smoke.ts`
- Modify: `/OneOPS/OneOps-UI/scripts/snmp-strategy-set-grafana-dashboard-save-action-smoke.ts`

- [ ] Assert the formal-closure state can consume backend readiness and prefer it over empty session memory.
- [ ] Assert the drawer wiring mentions backend readiness consumption.
- [ ] Assert flat save guard can skip the warning when backend readiness says the current target is already published.

### Task 4: Implement frontend backend-priority consumption

**Files:**
- Modify: `/OneOPS/OneOps-UI/src/api/platform/teleabs.ts`
- Modify: `/OneOPS/OneOps-UI/src/typings/platform/snmp-metric-contract.ts`
- Modify: `/OneOPS/OneOps-UI/src/views/platform/StrategyTemplate/snmpStrategySetFormalClosureState.ts`
- Modify: `/OneOPS/OneOps-UI/src/views/platform/StrategyTemplate/StrategySetDetailDrawer.vue`

- [ ] Add typed API support for the readiness endpoint.
- [ ] Extend the formal-closure state to accept optional backend readiness.
- [ ] Load readiness for the current target inside the drawer and use it as the first truth for the formal closure panel.
- [ ] Update the flat save guard to prefer backend readiness before falling back to current-session publish state.

### Task 5: Update handoff and verify

**Files:**
- Modify: `/OneOPS/docs/superpowers/handovers/2026-06-10-snmp-metric-groups-dashboard-family-handoff.md`

- [ ] Record that formal readiness is now backend-readable by target rather than session-only.
- [ ] Run:
  - `cd /OneOPS/OneOps && go test ./app/platform/service/impl -run 'TestMetricCapabilityContractResolver.*RecordingRuleReadiness.*' -count=1`
  - `cd /OneOPS/OneOps && go test ./app/platform/api -run 'TestTeleabsAPI_.*RecordingRuleReadiness.*' -count=1`
  - `cd /OneOPS/OneOps && go test ./app/platform/router -run TestTeleabsRoutes_ConsistentBetweenPlatformAndBidi -count=1`
  - `cd /OneOPS/OneOps-UI && npm run smoke:snmp-strategy-set-formal-closure-state`
  - `cd /OneOPS/OneOps-UI && npm run smoke:snmp-strategy-set-dashboard-tree-drawer`
  - `cd /OneOPS/OneOps-UI && npm run smoke:snmp-strategy-set-grafana-dashboard-save-action`
  - `cd /OneOPS/OneOps-UI && npm run typecheck`
  - `git -C /OneOPS/OneOps diff --check`
  - `git -C /OneOPS/OneOps-UI diff --check`
  - `git -C /OneOPS/docs diff --check`
