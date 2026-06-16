# SNMP Resolved Payload Identity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Persist the selected SNMP selector branch as an explicit resolved payload identity inside the apply plan and collection-target creation path.

**Architecture:** Extend `StrategyApplyPlan` with a small SNMP-only resolved payload object, build it from the selected leaf strategy plus parent chain, and propagate its identity into target-create labels so downstream collection-task generation sees one stable source of truth.

**Tech Stack:** Go, existing `StrategySetMatcher`, StrategyApply V2 orchestration, CollectionTarget DTO labels.

---

### Task 1: Add failing tests for resolved SNMP payload identity

**Files:**
- Modify: `/OneOPS/OneOps/app/platform/service/impl/strategy_apply_v2_test.go`

- [ ] **Step 1: Add a failing plan test for resolved payload identity**

Assert that a selector SNMP set with one Huawei device produces:

- `Plan.SelectedStrategyID == "st-huawei"`
- `Plan.ResolvedSnmpPayload.StrategySetID == "set-1"`
- `Plan.ResolvedSnmpPayload.SelectedStrategyID == "st-huawei"`
- `Plan.ResolvedSnmpPayload.StrategyChainIDs == []string{"st-root","st-huawei"}`

- [ ] **Step 2: Run the focused test and verify it fails**

Run:

```bash
go test ./app/platform/service/impl -run TestStrategyApplyV2Srv_PrepareApplyExecution_ResolvesSnmpPayloadIdentity -count=1
```

Expected: FAIL because the plan does not yet expose a resolved SNMP payload object.

- [ ] **Step 3: Add a failing target-create test for payload labels**

Assert that when `CreateTargets=true`, the target-create plan includes SNMP labels:

- `strategy_set_id=set-1`
- `selected_strategy_id=st-huawei`
- `strategy_chain=st-root,st-huawei`
- `payload_mode=snmp_selector_branch`

- [ ] **Step 4: Run the focused test and verify it fails**

Run:

```bash
go test ./app/platform/service/impl -run TestStrategyApplyV2Srv_PrepareApplyExecution_PopulatesSnmpTargetCreateLabels -count=1
```

Expected: FAIL because target-create plan labels are not yet populated from resolved SNMP payload identity.

### Task 2: Build explicit resolved SNMP payload identity in StrategyApplyPlan

**Files:**
- Modify: `/OneOPS/OneOps/app/platform/service/impl/strategy_apply_context_v2.go`
- Modify: `/OneOPS/OneOps/app/platform/service/impl/strategy_apply_plan_v2.go`

- [ ] **Step 1: Extend StrategyApplyPlan and task plan structures**

Add:

- `ResolvedSnmpPayload *ResolvedSnmpCollectionPayload` to `StrategyApplyPlan`
- `Labels map[string]string` to `StrategyApplyTaskPlan`
- `ResolvedSnmpCollectionPayload` struct with:
  - `StrategySetID`
  - `SelectedStrategyID`
  - `StrategyChainIDs`
  - `TemplateID`
  - `CollectionScope`
  - `TargetKind`

- [ ] **Step 2: Add a helper to resolve the selected strategy chain**

Implement a helper in `strategy_apply_plan_v2.go` that:

- loads the selected strategy and parents through `TeleabsStrategySrv.Get(...)`
- returns root-to-leaf `StrategyChainIDs`
- returns the first non-empty template in the chain

- [ ] **Step 3: Build the resolved SNMP payload after branch selection**

Inside `buildStrategyApplyPlan(...)`, when the apply is selector-mode SNMP:

- build `ResolvedSnmpCollectionPayload`
- attach it to `StrategyApplyPlan`
- keep `SelectedStrategyID` and `params[strategySetSelectedStrategyIDParam]` aligned with it

- [ ] **Step 4: Run focused tests**

Run:

```bash
go test ./app/platform/service/impl -run 'TestStrategyApplyV2Srv_PrepareApplyExecution_(AutoSelectsSnmpSelectorBranch|RejectsMixedSnmpSelectorBranches|ResolvesSnmpPayloadIdentity)' -count=1
```

Expected: PASS.

### Task 3: Propagate resolved SNMP payload identity into collection-target creation

**Files:**
- Modify: `/OneOPS/OneOps/app/platform/service/impl/strategy_apply_plan_v2.go`
- Modify: `/OneOPS/OneOps/app/platform/service/impl/strategy_apply_target_create_helpers_v2.go`
- Modify: `/OneOPS/OneOps/app/platform/service/impl/strategy_apply_post_apply_targets_v2.go`

- [ ] **Step 1: Populate SNMP payload labels in target-create plan**

When `ResolvedSnmpPayload` exists, set `TargetCreatePlan.Labels`:

```go
map[string]string{
    "strategy_set_id":      payload.StrategySetID,
    "selected_strategy_id": payload.SelectedStrategyID,
    "strategy_chain":       strings.Join(payload.StrategyChainIDs, ","),
    "payload_mode":         "snmp_selector_branch",
}
```

- [ ] **Step 2: Merge plan labels into collection-target request labels**

Update `strategyApplyV2BuildCollectionTargetReqsFromMapping(...)` so every created target carries:

- existing labels (`collection_scope`, `target_kind`, `function_area`, `required_capability`)
- plus the `TargetCreatePlan.Labels`

- [ ] **Step 3: Run focused tests**

Run:

```bash
go test ./app/platform/service/impl -run 'TestStrategyApplyV2Srv_PrepareApplyExecution_(PopulatesSnmpTargetCreateLabels|PlansSelectedStrategySetRenderFilter|StrategySelectorDoesNotPromoteSelectedStrategyParamsToGlobalOverrides)' -count=1
```

Expected: PASS.

### Task 4: Update the SNMP design doc and run the full focused verification set

**Files:**
- Modify: `/OneOPS/docs/superpowers/specs/2026-06-14-snmp-network-strategy-generic-dashboard-panel-design.md`

- [ ] **Step 1: Document that resolved SNMP payload identity is now persisted**

Add the phase-1 rule that SNMP selector applies now persist:

- selected strategy id
- strategy chain ids
- strategy-set identity
- target-create labels carrying that identity

- [ ] **Step 2: Run the full focused verification set**

Run:

```bash
go test ./app/platform/service/impl -run 'TestStrategyApplyV2Srv_(PrepareApplyExecution_AutoSelectsSnmpSelectorBranch|PrepareApplyExecution_RejectsMixedSnmpSelectorBranches|PrepareApplyExecution_ResolvesSnmpPayloadIdentity|PrepareApplyExecution_PopulatesSnmpTargetCreateLabels|PrepareApplyExecution_PlansSelectedStrategySetRenderFilter|PrepareApplyExecution_StrategySelectorDoesNotPromoteSelectedStrategyParamsToGlobalOverrides|ApplyStrategySetChildStrategy_InheritsFinalTaskConfig)' -count=1
```

Expected: PASS.
