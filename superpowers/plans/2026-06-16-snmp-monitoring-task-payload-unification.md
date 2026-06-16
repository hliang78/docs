# SNMP Monitoring Task Payload Unification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make SNMP selector strategy sets resolve exactly one effective strategy branch for one apply execution, then feed that branch into existing downstream rendering and task generation.

**Architecture:** Reuse the existing `StrategySetMatcher` as the branch selector, resolve one `selected_strategy_id` inside `StrategyApplyV2Srv`, and keep `GenerateFromStrategySet(...)` plus downstream `CollectionTarget -> CollectionTask -> Dispatch` unchanged for phase 1. Reject mixed-branch SNMP executions instead of silently co-composing sibling payloads.

**Tech Stack:** Go, Gin service layer, GORM-backed DTO/services, existing SNMP strategy matcher, Telegraf config generator tests.

---

### Task 1: Add branch-resolution tests at the StrategyApply plan layer

**Files:**
- Modify: `/OneOPS/OneOps/app/platform/service/impl/strategy_apply_v2_test.go`
- Verify: `/OneOPS/OneOps/app/platform/service/impl/strategy_set_matcher.go`

- [ ] **Step 1: Write the failing test for auto-selecting one SNMP branch**

Add a test near the existing selector-set tests that builds:

- a selector strategy set with `st-root`, `st-huawei`, `st-h3c`
- SNMP template `tpl-snmp`
- one Huawei device spec with metadata:
  - `catalog_name=Switch`
  - `manufacturer_name=Huawei`
  - `platform_name=VRP`

Expected assertions:

```go
assert.Equal(t, "st-huawei", execCtx.Plan.Params[strategySetSelectedStrategyIDParam])
assert.Equal(t, "st-huawei", execCtx.Plan.SelectedStrategyID)
```

- [ ] **Step 2: Run the focused test and verify it fails**

Run:

```bash
go test ./app/platform/service/impl -run TestStrategyApplyV2Srv_PrepareApplyExecution_AutoSelectsSnmpSelectorBranch -count=1
```

Expected: FAIL because `SelectedStrategyID` is empty or no automatic branch selection occurs.

- [ ] **Step 3: Write the failing test for mixed-branch rejection**

Add a second test that uses one selector strategy set and two devices:

- Huawei VRP device
- H3C Comware device

Expected:

```go
_, err := s.prepareApplyExecution(context.Background(), input)
require.Error(t, err)
assert.Contains(t, err.Error(), "multiple matched SNMP strategy branches")
```

- [ ] **Step 4: Run the mixed-branch test and verify it fails**

Run:

```bash
go test ./app/platform/service/impl -run TestStrategyApplyV2Srv_PrepareApplyExecution_RejectsMixedSnmpSelectorBranches -count=1
```

Expected: FAIL because current code still allows the apply path without enforcing one branch.

### Task 2: Teach StrategyApply plan building to resolve one SNMP selector branch

**Files:**
- Modify: `/OneOPS/OneOps/app/platform/service/impl/strategy_apply_plan_v2.go`
- Modify: `/OneOPS/OneOps/app/platform/service/impl/strategy_apply_context_v2.go`
- Verify: `/OneOPS/OneOps/app/platform/service/impl/strategy_set_matcher.go`

- [ ] **Step 1: Add `SelectedStrategyID` to `StrategyApplyPlan`**

Extend the plan model so the selected branch identity is explicit instead of being hidden only inside params:

```go
type StrategyApplyPlan struct {
    // existing fields...
    SelectedStrategyID string
}
```

- [ ] **Step 2: Add a helper in `strategy_apply_plan_v2.go` to resolve one SNMP selector branch**

Implement a helper with behavior:

- return early if `StrategySetID` is empty;
- load the strategy set;
- only activate when:
  - strategy-set mode is `strategy_selector`
  - targets are device-only
  - at least one template/plugin in the set is SNMP-oriented
- if `input.StrategyID` is already provided, keep it as the selected branch;
- otherwise run `NewStrategySetMatcher(...).ResolveDevices(...)`;
- require all matched groups to collapse to one `StrategyID`;
- on multiple groups, return a clear error;
- on zero groups, return a clear error.

- [ ] **Step 3: Wire the helper into `buildStrategyApplyPlan(...)`**

Update flow so branch selection happens before:

- `validateStrategySetGlobalParams(...)`
- `resolvePairsWithCapability(...)`
- `strategyApplyV2BuildPairPlans(...)`

Then:

- set `input.StrategyID` to the resolved branch if it was empty;
- write `params[strategySetSelectedStrategyIDParam] = selectedStrategyID`;
- persist `SelectedStrategyID` into the returned `StrategyApplyPlan`.

- [ ] **Step 4: Run the new selector tests**

Run:

```bash
go test ./app/platform/service/impl -run 'TestStrategyApplyV2Srv_PrepareApplyExecution_(AutoSelectsSnmpSelectorBranch|RejectsMixedSnmpSelectorBranches|PlansSelectedStrategySetRenderFilter)' -count=1
```

Expected: PASS.

### Task 3: Ensure downstream SNMP render path consumes the resolved branch consistently

**Files:**
- Modify: `/OneOPS/OneOps/app/platform/service/impl/strategy_apply_plan_v2.go`
- Modify: `/OneOPS/OneOps/app/platform/service/impl/strategy_apply_pair_resolution_v2.go`
- Verify: `/OneOPS/OneOps/app/platform/service/impl/telegraf_config_generator_impl.go`

- [ ] **Step 1: Keep pair filtering aligned with selected branch**

Ensure `resolvePairsWithCapability(...)` sees the selected strategy id for selector sets so template filtering stays branch-consistent.

Minimal expected behavior:

- when selected branch is Huawei, pair resolution uses Huawei template family;
- when selected branch is H3C, pair resolution uses H3C template family;
- no sibling branch should survive pair filtering for that execution.

- [ ] **Step 2: Preserve existing strategy-set render mode**

Do not replace:

```go
GenerateFromStrategySet(...)
```

Instead, verify that it still receives:

```go
params[strategySetSelectedStrategyIDParam]
```

and therefore renders only the selected branch.

- [ ] **Step 3: Add/adjust regression coverage if needed**

If existing tests do not prove this end-to-end, add one focused assertion in `strategy_apply_v2_test.go` that confirms:

- selector-set render mode remains enabled
- selected branch id is injected
- global params do not absorb child-only overrides

- [ ] **Step 4: Run focused tests**

Run:

```bash
go test ./app/platform/service/impl -run 'TestStrategyApplyV2Srv_(PrepareApplyExecution_StrategySelectorDoesNotPromoteSelectedStrategyParamsToGlobalOverrides|ApplyStrategySetChildStrategy_InheritsFinalTaskConfig)' -count=1
```

Expected: PASS.

### Task 4: Update the SNMP design docs and verify the first-phase behavior

**Files:**
- Modify: `/OneOPS/docs/superpowers/specs/2026-06-14-snmp-network-strategy-generic-dashboard-panel-design.md`
- Verify: `/OneOPS/docs/superpowers/plans/2026-06-16-snmp-monitoring-task-payload-unification.md`

- [ ] **Step 1: Ensure the spec describes the first-phase constraint**

Document that SNMP selector strategy-set executions now:

- select one leaf branch
- reject mixed-branch multi-device executions
- pass one branch identity into downstream rendering

- [ ] **Step 2: Run the full focused verification set**

Run:

```bash
go test ./app/platform/service/impl -run 'TestStrategyApplyV2Srv_(PrepareApplyExecution_AutoSelectsSnmpSelectorBranch|PrepareApplyExecution_RejectsMixedSnmpSelectorBranches|PrepareApplyExecution_PlansSelectedStrategySetRenderFilter|PrepareApplyExecution_StrategySelectorDoesNotPromoteSelectedStrategyParamsToGlobalOverrides|ApplyStrategySetChildStrategy_InheritsFinalTaskConfig)' -count=1
```

Expected: PASS.

- [ ] **Step 3: Run a broader safety check on selector matching**

Run:

```bash
go test ./app/platform/service/impl -run 'TestStrategySetMatcherResolveDevices' -count=1
```

Expected: PASS.
