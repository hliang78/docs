# Config Baseline Governance Closed Loop Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a rule-based, versioned baseline policy layer for configuration management and surface latest compliance results in the existing queue.

**Architecture:** Keep immutable config versions as collected facts. Add baseline policy, policy version, and evaluation records under the platform configuration management boundary. Evaluation matches an active policy to a config version, reads normalized content, applies simple text/regex rules, persists findings, and exposes the latest result through Device V2 config management APIs.

**Tech Stack:** Go, GORM, MySQL migrations, Gin APIs, Vue 3, TypeScript, Ant Design Vue.

---

### Task 1: Backend Models and Evaluation Service

**Files:**
- Create: `OneOps/app/platform/platform_model/config_baseline.go`
- Create: `OneOps/app/platform/service/impl/config_baseline_service.go`
- Test: `OneOps/app/platform/service/impl/config_baseline_service_test.go`
- Modify: `OneOps/app/platform/service/i_config_management.go`
- Modify: `OneOps/app/platform/service/impl/config_management_service_set.go`

- [ ] **Step 1: Write failing tests for policy creation, activation, and rule evaluation**

Cover creating a policy, creating a policy version with rules, activating it, evaluating a matching config version as compliant, and evaluating another version as drifted.

- [ ] **Step 2: Run service tests and verify they fail because the service does not exist**

Run: `go test ./app/platform/service/impl -run ConfigBaseline -count=1`

- [ ] **Step 3: Implement baseline models and service**

Add policy, policy version, and evaluation structs. Implement rule matching, active policy lookup, and persisted evaluation summary.

- [ ] **Step 4: Run service tests and verify they pass**

Run: `go test ./app/platform/service/impl -run ConfigBaseline -count=1`

### Task 2: Queue Integration

**Files:**
- Modify: `OneOps/app/platform/service/impl/config_version_service.go`
- Test: `OneOps/app/platform/service/impl/config_version_service_test.go`

- [ ] **Step 1: Write failing test showing latest baseline evaluation overrides row baseline status**

Create a config version row and a latest evaluation row with `drifted`. Assert `ListCenterAssets` returns `baseline_status=drifted`.

- [ ] **Step 2: Run targeted test and verify it fails**

Run: `go test ./app/platform/service/impl -run ListCenterAssetsUsesLatestBaselineEvaluation -count=1`

- [ ] **Step 3: Load latest evaluations and apply them to asset rows**

Keep existing selected-version baseline status as fallback when no evaluation exists.

- [ ] **Step 4: Run targeted and config management tests**

Run: `go test ./app/platform/service/impl -run 'ConfigVersionService|ConfigBaseline' -count=1`

### Task 3: Device V2 API

**Files:**
- Modify: `OneOps/app/device/v2/api/device_v2.go`
- Modify: `OneOps/app/device/v2/api/device_v2_config_management.go`
- Modify: `OneOps/app/device/v2/router/device_v2.go`
- Test: `OneOps/app/device/v2/api/device_v2_test.go`

- [ ] **Step 1: Write failing API tests for listing policies, creating policy, adding version, activating, and running evaluation**

Use the existing fake service style in `device_v2_test.go`.

- [ ] **Step 2: Run Device V2 API tests and verify they fail**

Run: `go test ./app/device/v2/api -run 'BaselinePolicy|BaselineEvaluation' -count=1`

- [ ] **Step 3: Add service dependency, handlers, and routes**

Handlers should return `503` when the baseline service is unavailable and use existing response helpers.

- [ ] **Step 4: Run Device V2 API tests**

Run: `go test ./app/device/v2/api -run 'ConfigManagement|Baseline' -count=1`

### Task 4: Database Migration

**Files:**
- Create: `OneOps/migrations/add_config_baseline_governance_tables_20260608.sql`

- [ ] **Step 1: Add migration with three tables and indexes**

Use table names from the model layer and index policy/version/evaluation lookup fields.

- [ ] **Step 2: Verify SQL has no placeholder text**

Run: `rg -n 'TODO|TBD|placeholder' migrations/add_config_baseline_governance_tables_20260608.sql`

### Task 5: Frontend API and UI

**Files:**
- Modify: `OneOps-UI/src/api/device/device-v2.ts`
- Modify: `OneOps-UI/src/views/device/DeviceConfigManagement.vue`
- Create: `OneOps-UI/scripts/device-config-management-baseline-governance-smoke.ts`

- [ ] **Step 1: Add TypeScript API types and request helpers**

Expose policy list/create/version/activate/evaluation endpoints.

- [ ] **Step 2: Add baseline management view**

Add a compact `基线管理` mode, policy table, create drawer, rule list editor, and manual evaluation button.

- [ ] **Step 3: Update queue labels**

Use `未配置基线策略`, `符合基线`, `已漂移`, and `评估失败`.

- [ ] **Step 4: Add smoke test**

Assert baseline label mapping and basic policy request payload shaping.

- [ ] **Step 5: Run frontend checks**

Run: `pnpm exec vue-tsc --noEmit`
Run: `pnpm tsx scripts/device-config-management-baseline-governance-smoke.ts`

### Task 6: Verification and Commits

**Files:**
- All modified files.

- [ ] **Step 1: Run backend targeted tests**

Run: `go test ./app/platform/service/impl ./app/device/v2/api -run 'ConfigBaseline|ConfigManagement|Baseline' -count=1`

- [ ] **Step 2: Run frontend targeted checks**

Run: `pnpm exec vue-tsc --noEmit`
Run: `pnpm tsx scripts/device-config-management-baseline-governance-smoke.ts`

- [ ] **Step 3: Commit docs, backend, and frontend**

Commit each repository with focused messages.
