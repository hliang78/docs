# SNMP Recording Rule Versioned Readiness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Tighten recording-rule readiness from “this target has at least one successful publish record” to “the current target’s current recording-rule content still matches the most recent successful publish version”.

**Architecture:** Keep the existing by-target readiness endpoint and extend it with current materialized YAML SHA plus one `version_matched` signal. Compute the current YAML SHA from the existing by-target materialization path, compare it against the last successful publish record’s `yaml_sha256`, and let the frontend use `ready && version_matched` as the formal save gate. Do not add new publish actions, tree-path behavior, or generic history browsing.

**Tech Stack:** Go resolver/API/router tests, existing recording-rule materialization logic, Vue 3 state helpers, TypeScript smoke tests.

---

### Task 1: Lock version-consistency behavior with tests

**Files:**
- Modify: `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver_test.go`
- Modify: `/OneOPS/OneOps/app/platform/api/teleabs_metric_contract_http_test.go`
- Modify: `/OneOPS/OneOps-UI/scripts/snmp-strategy-set-formal-closure-state-smoke.ts`
- Modify: `/OneOPS/OneOps-UI/scripts/snmp-strategy-set-grafana-dashboard-save-action-smoke.ts`

- [ ] Add a resolver test proving readiness returns `version_matched=true` when the current materialized YAML SHA equals the last successful publish SHA.
- [ ] Add a resolver test proving readiness returns `ready=true` but `version_matched=false` when publish history exists but the current YAML has changed.
- [ ] Extend API tests to assert the new readiness fields are exposed.
- [ ] Extend frontend smoke to require backend `version_matched` before formal save is treated as fully ready.

### Task 2: Implement backend version-aware readiness

**Files:**
- Modify: `/OneOPS/OneOps/app/platform/dto/snmp_metric_contract.go`
- Modify: `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver.go`

- [ ] Add `current_yaml_sha256` and `version_matched` to the readiness DTO.
- [ ] Reuse `ResolveStrategySetTargetRecordingRuleMaterializationDryRun` to compute the current by-target YAML SHA.
- [ ] Keep `ready` backward-compatible as “successful publish exists”.
- [ ] Compute `version_matched` only when both current YAML SHA and last successful YAML SHA are present.

### Task 3: Implement frontend version-aware consumption

**Files:**
- Modify: `/OneOPS/OneOps-UI/src/typings/platform/snmp-metric-contract.ts`
- Modify: `/OneOPS/OneOps-UI/src/views/platform/StrategyTemplate/snmpStrategySetFormalClosureState.ts`
- Modify: `/OneOPS/OneOps-UI/src/views/platform/StrategyTemplate/StrategySetDetailDrawer.vue`

- [ ] Extend the frontend readiness type with `current_yaml_sha256` and `version_matched`.
- [ ] Change formal closure state to treat backend readiness as sufficient only when `ready && version_matched`.
- [ ] If backend says `ready=true` but `version_matched=false`, keep the stage at `待发布 Recording Rule` and make the next action explicitly say the rules need republish.
- [ ] Change the flat save guard to skip the warning only when backend readiness is both ready and version-matched.

### Task 4: Update handoff and verify

**Files:**
- Modify: `/OneOPS/docs/superpowers/handovers/2026-06-10-snmp-metric-groups-dashboard-family-handoff.md`

- [ ] Record that formal readiness is now version-aware rather than only “曾经成功发布过”.
- [ ] Run:
  - `cd /OneOPS/OneOps && go test ./app/platform/service/impl -run 'TestMetricCapabilityContractResolver.*RecordingRuleReadiness.*' -count=1`
  - `cd /OneOPS/OneOps && go test ./app/platform/api -run 'TestTeleabsAPI_.*RecordingRuleReadiness.*' -count=1`
  - `cd /OneOPS/OneOps && go test ./app/platform/router -run TestTeleabsRoutes_ConsistentBetweenPlatformAndBidi -count=1`
  - `cd /OneOPS/OneOps-UI && npm run smoke:snmp-strategy-set-formal-closure-state`
  - `cd /OneOPS/OneOps-UI && npm run smoke:snmp-strategy-set-grafana-dashboard-save-action`
  - `cd /OneOPS/OneOps-UI && npm run smoke:snmp-strategy-set-dashboard-tree-drawer`
  - `cd /OneOPS/OneOps-UI && npm run typecheck`
  - `git -C /OneOPS/OneOps diff --check`
  - `git -C /OneOPS/OneOps-UI diff --check`
  - `git -C /OneOPS/docs diff --check`
