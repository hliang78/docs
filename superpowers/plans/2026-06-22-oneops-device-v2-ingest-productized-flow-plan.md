# OneOPS Device V2 导入设备清单产品化流程 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 `导入设备清单` 重构为严格四步流程，并把“提交成功”语义与 Device V2 管理页可见性绑定起来。

**Architecture:** 先收紧后端与前端共享的“真实成功”判定，再把导入页拆成 `准备清单 -> 系统检查 -> 确认提交 -> 成功交接` 四个明确阶段。成功交接使用独立页面语境承接，并通过真实成功 `device_code` + `task_id` 兜底交接到 Device V2 管理页。

**Tech Stack:** Vue 3 + TypeScript + Ant Design Vue + Vite smoke scripts, Go + Gin + GORM, existing Device V2 ingest/list APIs.

---

## File Structure

### Frontend files

- Modify: `OneOPS-UI/src/views/device/DeviceV2IngestPipelineRedesign.vue`
  - 收紧当前导入页为 Step 1/2/3 的流程页
  - 去掉大块说明卡片
  - 只保留紧凑的步骤、按钮、状态、表格、行内反馈
- Create: `OneOPS-UI/src/views/device/DeviceV2IngestSuccessHandoff.vue`
  - 承接 Step 4 成功交接页
  - 只展示真实成功结果和后续动作
- Modify: `OneOPS-UI/src/router/utils.ts`
  - 增加成功交接页路由
- Create: `OneOPS-UI/src/views/device/device-v2-ingest-flow-outcome.ts`
  - 统一计算 `失败 / 部分成功 / 成功`、成功设备集合、交接参数
- Create: `OneOPS-UI/src/views/device/device-v2-ingest-flow-state.ts`
  - 统一从 task 结果推导当前流程阶段和按钮可用性
- Modify: `OneOPS-UI/src/views/device/DeviceV2ManagementGrouped.vue`
  - 支持 ingest handoff 兜底策略
  - 当 `codes` 不足时使用 `task_id` 恢复本次成功设备集合
- Modify: `OneOPS-UI/src/api/device/device-v2-ingest.ts`
  - 增补前端 ingest task 类型，显式包含 handoff 需要的 result 字段
- Modify: `OneOPS-UI/src/api/device/device-v2.ts`
  - 如有必要，扩展 Device V2 list 查询参数或新增按 ingest 交接锚点查询 helper
- Create: `OneOPS-UI/scripts/d2-ingest-productized-flow-smoke.ts`
  - 覆盖真实成功判定、部分成功、失败、交接参数

### Backend files

- Modify: `OneOps/app/device/v2/ingest/service/impl/device_v2_ingest_pipeline.go`
  - 在 task result 中持久化明确的 handoff summary
- Modify: `OneOps/app/device/v2/ingest/service/impl/device_v2_ingest_executor.go`
  - 统一成功设备、失败设备、可采集设备统计口径
- Modify: `OneOps/app/device/v2/ingest/service/impl/device_v2_ingest.go`
  - 保持 `SubmitTask` 仅返回真实执行后的 task，但配套新的 handoff result 契约
- Modify: `OneOps/app/device/v2/service/impl/device_v2_minimal_read.go`
  - 支持按 ingest handoff 锚点恢复成功设备集合（如果选择由 list 层兜底）
- Modify: `OneOps/app/device/v2/api/device_v2.go`
  - 接入新的 list 查询参数或 handoff helper API
- Test: `OneOps/app/device/v2/ingest/api/device_v2_ingest_test.go`
- Test: `OneOps/app/device/v2/ingest/service/impl/device_v2_ingest_executor_test.go`
- Test: `OneOps/app/device/v2/api/device_v2_test.go`

## Task 1: Lock The Shared Success Contract

**Files:**
- Modify: `OneOps/app/device/v2/ingest/service/impl/device_v2_ingest_pipeline.go`
- Modify: `OneOps/app/device/v2/ingest/service/impl/device_v2_ingest_executor.go`
- Test: `OneOps/app/device/v2/ingest/service/impl/device_v2_ingest_executor_test.go`
- Test: `OneOps/app/device/v2/ingest/api/device_v2_ingest_test.go`

- [ ] **Step 1: Write the failing Go test for handoff summary**

```go
func TestBuildPreparedTaskIncludesHandoffSummary(t *testing.T) {
	execution := &ingestExecutionReport{
		Enabled:      true,
		Created:      2,
		Updated:      1,
		Failed:       0,
		Manageable:   2,
		Unmanageable: 1,
		DeviceResults: []ingestExecutionDeviceResult{
			{DeviceCode: "DVC-A", Action: "created", Status: "completed", Manageable: true, ManageStatus: "manageable"},
			{DeviceCode: "DVC-B", Action: "updated", Status: "completed", Manageable: true, ManageStatus: "manageable"},
			{DeviceCode: "DVC-C", Action: "created", Status: "completed", Manageable: false, ManageStatus: "registered_only"},
		},
	}

	task := buildPreparedTask(&dto.DeviceV2IngestSubmitReq{Source: "manual_api"}, nil, nil, []model.DeviceV2IngestDevice{{}, {}, {}}, nil, execution)

	postCheck := task.Result["post_check"].(map[string]interface{})
	handoff := postCheck["handoff"].(map[string]interface{})

	assert.Equal(t, "success", handoff["status"])
	assert.Equal(t, []string{"DVC-A", "DVC-B", "DVC-C"}, handoff["success_device_codes"])
	assert.Equal(t, float64(2), handoff["manageable_count"])
	assert.Equal(t, float64(1), handoff["registry_only_count"])
}
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
go test ./OneOps/app/device/v2/ingest/service/impl -run TestBuildPreparedTaskIncludesHandoffSummary -v
```

Expected:

- FAIL because `post_check.handoff` does not exist yet

- [ ] **Step 3: Add the minimal handoff summary builder**

```go
func buildHandoffSummary(execution *ingestExecutionReport) map[string]interface{} {
	if execution == nil {
		return map[string]interface{}{
			"status":               "failed",
			"success_device_codes": []string{},
			"manageable_count":     0,
			"registry_only_count":  0,
		}
	}

	successCodes := make([]string, 0, execution.Created+execution.Updated)
	for _, item := range execution.DeviceResults {
		action := strings.ToLower(strings.TrimSpace(item.Action))
		if action == "created" || action == "updated" {
			successCodes = append(successCodes, strings.TrimSpace(item.DeviceCode))
		}
	}

	status := "failed"
	switch {
	case len(successCodes) > 0 && execution.Failed == 0:
		status = "success"
	case len(successCodes) > 0:
		status = "partial_success"
	}

	return map[string]interface{}{
		"status":               status,
		"success_device_codes": normalizeStringSlice(successCodes),
		"manageable_count":     execution.Manageable,
		"registry_only_count":  execution.Unmanageable,
	}
}
```

- [ ] **Step 4: Wire the new handoff summary into `post_check`**

```go
func buildPostCheckResult(validation *ingestValidationReport, execution *ingestExecutionReport, deviceCount int) map[string]interface{} {
	// existing fields...
	result := map[string]interface{}{
		"validation_passed": validationPassed,
		"accepted_count":    acceptedCount,
		"rejected_count":    rejectedCount,
		"device_count":      deviceCount,
		"next_action":       "当前已完成最小入库执行；后续可继续接设备检测与属性补齐能力",
	}
	result["handoff"] = buildHandoffSummary(execution)
	// existing execution summary...
	return result
}
```

- [ ] **Step 5: Add the partial-success API test**

```go
func TestSubmitTaskReturnsPartialSuccessHandoff(t *testing.T) {
	// existing test setup...
	resp := performSubmitTask(t, router, payload)

	postCheck := resp.Result["post_check"].(map[string]interface{})
	handoff := postCheck["handoff"].(map[string]interface{})

	assert.Equal(t, "partial_success", handoff["status"])
	assert.NotEmpty(t, handoff["success_device_codes"])
}
```

- [ ] **Step 6: Run backend tests**

Run:

```bash
go test ./OneOps/app/device/v2/ingest/service/impl ./OneOps/app/device/v2/ingest/api -run 'Test(BuildPreparedTaskIncludesHandoffSummary|SubmitTaskReturnsPartialSuccessHandoff)' -v
```

Expected:

- PASS for both tests

- [ ] **Step 7: Commit**

```bash
git add \
  OneOps/app/device/v2/ingest/service/impl/device_v2_ingest_pipeline.go \
  OneOps/app/device/v2/ingest/service/impl/device_v2_ingest_executor.go \
  OneOps/app/device/v2/ingest/service/impl/device_v2_ingest_executor_test.go \
  OneOps/app/device/v2/ingest/api/device_v2_ingest_test.go
git commit -m "feat: add ingest handoff success summary"
```

## Task 2: Add Frontend Outcome Helpers And Smoke Coverage

**Files:**
- Create: `OneOPS-UI/src/views/device/device-v2-ingest-flow-outcome.ts`
- Create: `OneOPS-UI/src/views/device/device-v2-ingest-flow-state.ts`
- Create: `OneOPS-UI/scripts/d2-ingest-productized-flow-smoke.ts`

- [ ] **Step 1: Write the failing smoke test for outcome resolution**

```ts
import assert from 'node:assert/strict';
import { resolveIngestFlowOutcome } from '../src/views/device/device-v2-ingest-flow-outcome';

const success = resolveIngestFlowOutcome({
  task_id: 'ingest-task-1',
  result: {
    post_check: {
      handoff: {
        status: 'success',
        success_device_codes: ['DVC-A', 'DVC-B'],
        manageable_count: 1,
        registry_only_count: 1,
      },
    },
    execution: { created: 1, updated: 1, failed: 0 },
  },
} as any);

assert.equal(success.status, 'success');
assert.deepEqual(success.codes, ['DVC-A', 'DVC-B']);
assert.equal(success.canNavigateToManagement, true);
```

- [ ] **Step 2: Run the smoke test to verify it fails**

Run:

```bash
npx esbuild scripts/d2-ingest-productized-flow-smoke.ts --bundle --platform=node --format=esm --outfile=.tmp/d2-ingest-productized-flow-smoke.mjs >/dev/null && node .tmp/d2-ingest-productized-flow-smoke.mjs
```

Expected:

- FAIL because `resolveIngestFlowOutcome` does not exist yet

- [ ] **Step 3: Add the minimal outcome helper**

```ts
export type IngestFlowOutcomeStatus = 'failed' | 'partial_success' | 'success';

export function resolveIngestFlowOutcome(task: {
  task_id?: string;
  result?: Record<string, unknown>;
}): {
  status: IngestFlowOutcomeStatus;
  codes: string[];
  taskID: string;
  manageableCount: number;
  registryOnlyCount: number;
  canNavigateToManagement: boolean;
} {
  const taskID = String(task?.task_id || '').trim();
  const result = (task?.result || {}) as Record<string, any>;
  const handoff = ((result.post_check || {}) as Record<string, any>).handoff || {};
  const codes = Array.isArray(handoff.success_device_codes)
    ? handoff.success_device_codes.map((item: unknown) => String(item || '').trim()).filter(Boolean)
    : [];
  const status = (String(handoff.status || '').trim() || 'failed') as IngestFlowOutcomeStatus;
  return {
    status,
    codes,
    taskID,
    manageableCount: Number(handoff.manageable_count || 0),
    registryOnlyCount: Number(handoff.registry_only_count || 0),
    canNavigateToManagement: codes.length > 0 && !!taskID,
  };
}
```

- [ ] **Step 4: Add a flow-state helper for the four steps**

```ts
export function resolveIngestFlowStep(input: {
  hasDraftRows: boolean;
  issueCount: number;
  outcomeStatus: 'failed' | 'partial_success' | 'success' | '';
}): 1 | 2 | 3 | 4 {
  if (input.outcomeStatus === 'partial_success' || input.outcomeStatus === 'success') return 4;
  if (input.hasDraftRows && input.issueCount === 0) return 3;
  if (input.hasDraftRows) return 2;
  return 1;
}
```

- [ ] **Step 5: Expand smoke coverage for failed and partial-success cases**

```ts
const failed = resolveIngestFlowOutcome({
  task_id: 'ingest-task-2',
  result: { post_check: { handoff: { status: 'failed', success_device_codes: [] } } },
} as any);
assert.equal(failed.status, 'failed');
assert.equal(failed.canNavigateToManagement, false);

const partial = resolveIngestFlowOutcome({
  task_id: 'ingest-task-3',
  result: { post_check: { handoff: { status: 'partial_success', success_device_codes: ['DVC-X'] } } },
} as any);
assert.equal(partial.status, 'partial_success');
assert.deepEqual(partial.codes, ['DVC-X']);
```

- [ ] **Step 6: Run smoke and lint**

Run:

```bash
npx esbuild scripts/d2-ingest-productized-flow-smoke.ts --bundle --platform=node --format=esm --outfile=.tmp/d2-ingest-productized-flow-smoke.mjs >/dev/null && node .tmp/d2-ingest-productized-flow-smoke.mjs
npx eslint src/views/device/device-v2-ingest-flow-outcome.ts src/views/device/device-v2-ingest-flow-state.ts scripts/d2-ingest-productized-flow-smoke.ts --ext .ts
```

Expected:

- smoke prints a success line
- eslint reports 0 errors

- [ ] **Step 7: Commit**

```bash
git add \
  OneOPS-UI/src/views/device/device-v2-ingest-flow-outcome.ts \
  OneOPS-UI/src/views/device/device-v2-ingest-flow-state.ts \
  OneOPS-UI/scripts/d2-ingest-productized-flow-smoke.ts
git commit -m "test: add ingest flow outcome helpers"
```

## Task 3: Refactor The Ingest Page Into Steps 1-3

**Files:**
- Modify: `OneOPS-UI/src/views/device/DeviceV2IngestPipelineRedesign.vue`
- Test: `OneOPS-UI/scripts/d2-ingest-buttons-smoke.cjs`
- Test: `OneOPS-UI/scripts/d2-company-excel-import-smoke.ts`
- Test: `OneOPS-UI/scripts/d2-ingest-productized-flow-smoke.ts`

- [ ] **Step 1: Write the failing smoke assertions for the compact step flow**

```ts
import assert from 'node:assert/strict';
import fs from 'node:fs';

const source = fs.readFileSync('src/views/device/DeviceV2IngestPipelineRedesign.vue', 'utf8');

assert.match(source, /上传清单/);
assert.doesNotMatch(source, /上传并提交设备清单/);
assert.doesNotMatch(source, /可直接上传旧设备清单/);
assert.doesNotMatch(source, /凭据怎么准备/);
assert.match(source, /Step 1|准备清单/);
assert.match(source, /Step 2|系统检查/);
assert.match(source, /Step 3|确认提交/);
```

- [ ] **Step 2: Run the smoke tests to verify they fail**

Run:

```bash
npx esbuild scripts/d2-company-excel-import-smoke.ts --bundle --platform=node --format=esm --outfile=.tmp/d2-company-excel-import-smoke.mjs >/dev/null && node .tmp/d2-company-excel-import-smoke.mjs
node scripts/d2-ingest-buttons-smoke.cjs
```

Expected:

- FAIL because the page still renders the old upload-and-submit copy and info cards

- [ ] **Step 3: Refactor the CTA and strip the large helper cards**

```vue
<div class="operation-command__actions">
  <a-button
    v-if="currentStep === 1"
    type="primary"
    :loading="parsingFile"
    :disabled="capabilityBlocked"
    @click="triggerFileSelect"
  >
    <template #icon><UploadOutlined /></template>
    上传清单
  </a-button>
  <a-button v-else-if="currentStep === 2" type="primary" @click="focusFirstBlockingRow">
    仅看问题设备
  </a-button>
  <a-popconfirm
    v-else-if="currentStep === 3"
    title="确认提交可提交设备？"
    ok-text="提交"
    cancel-text="取消"
    @confirm="submitDraft"
  >
    <a-button type="primary" :loading="submitting">确认提交</a-button>
  </a-popconfirm>
</div>
```

- [ ] **Step 4: Replace duplicated overview cards with a compact metric strip**

```vue
<section class="overview-band">
  <div class="metric-cell">
    <span>清单设备</span>
    <strong>{{ draftRows.length }}</strong>
  </div>
  <div class="metric-cell">
    <span>需修改</span>
    <strong>{{ submitSummary.issueCount }}</strong>
  </div>
  <div class="metric-cell">
    <span>可提交</span>
    <strong>{{ submitReadyCount }}</strong>
  </div>
</section>
```

- [ ] **Step 5: Push Step 4 content out of the page**

```ts
const outcome = computed(() => resolveIngestFlowOutcome(latestTask.value || {} as any));
const currentStep = computed(() =>
  resolveIngestFlowStep({
    hasDraftRows: draftRows.value.length > 0,
    issueCount: submitSummary.value.issueCount,
    outcomeStatus: outcome.value.status,
  }),
);

watch(
  () => outcome.value.status,
  status => {
    if (status === 'success' || status === 'partial_success') {
      router.push({
        name: 'DeviceV2IngestSuccessHandoff',
        query: {
          task_id: outcome.value.taskID,
          codes: outcome.value.codes.join(','),
        },
      });
    }
  },
);
```

- [ ] **Step 6: Re-run smoke, typecheck, and lint**

Run:

```bash
node scripts/d2-ingest-buttons-smoke.cjs
npx esbuild scripts/d2-company-excel-import-smoke.ts --bundle --platform=node --format=esm --outfile=.tmp/d2-company-excel-import-smoke.mjs >/dev/null && node .tmp/d2-company-excel-import-smoke.mjs
npm run typecheck:d2
npx eslint src/views/device/DeviceV2IngestPipelineRedesign.vue --ext .vue
```

Expected:

- button/copy smoke passes
- `typecheck:d2` passes
- eslint reports 0 errors

- [ ] **Step 7: Commit**

```bash
git add \
  OneOPS-UI/src/views/device/DeviceV2IngestPipelineRedesign.vue \
  OneOPS-UI/scripts/d2-ingest-buttons-smoke.cjs \
  OneOPS-UI/scripts/d2-company-excel-import-smoke.ts \
  OneOPS-UI/scripts/d2-ingest-productized-flow-smoke.ts
git commit -m "feat: refactor ingest page into compact step flow"
```

## Task 4: Add The Success Handoff Page

**Files:**
- Create: `OneOPS-UI/src/views/device/DeviceV2IngestSuccessHandoff.vue`
- Modify: `OneOPS-UI/src/router/utils.ts`
- Test: `OneOPS-UI/scripts/d2-la-import-apply-handoff.cjs`
- Test: `OneOPS-UI/scripts/d2-redesign-browser-smoke.cjs`

- [ ] **Step 1: Write the failing route smoke**

```ts
import assert from 'node:assert/strict';
import fs from 'node:fs';

const routerSource = fs.readFileSync('src/router/utils.ts', 'utf8');
assert.match(routerSource, /DeviceV2IngestSuccessHandoff/);
assert.match(routerSource, /title: '导入成功交接'/);
```

- [ ] **Step 2: Run the smoke to verify it fails**

Run:

```bash
npx esbuild scripts/d2-la-import-apply-handoff.cjs --bundle --platform=node --format=cjs --outfile=.tmp/d2-la-import-apply-handoff.cjs >/dev/null && node .tmp/d2-la-import-apply-handoff.cjs
```

Expected:

- FAIL because the success handoff route does not exist yet

- [ ] **Step 3: Add the route**

```ts
const deviceV2IngestSuccessHandoffRoute: RouteRecordRaw = {
  path: 'device/device-v2-ingest-success-handoff',
  name: 'DeviceV2IngestSuccessHandoff',
  component: () => import('@/views/device/DeviceV2IngestSuccessHandoff.vue'),
  meta: {
    title: '导入成功交接',
    requiresAuth: true,
    hideInMenu: true,
  },
};
```

- [ ] **Step 4: Add the minimal success handoff page**

```vue
<template>
  <div class="ingest-success-page">
    <div class="success-hero">
      <div class="success-hero__eyebrow">STEP 4 / 4</div>
      <h1>{{ heading }}</h1>
      <div class="success-stats">
        <div><span>成功入库</span><strong>{{ codes.length }}</strong></div>
        <div><span>可采集</span><strong>{{ manageableCount }}</strong></div>
        <div><span>待补充</span><strong>{{ registryOnlyCount }}</strong></div>
      </div>
      <div class="success-actions">
        <a-button type="primary" @click="openManagement">进入设备管理页查看这批设备</a-button>
        <a-button @click="backToDraft">回去修复剩余问题设备</a-button>
        <a-button @click="startNewDraft">开始新清单</a-button>
      </div>
    </div>
  </div>
</template>
```

- [ ] **Step 5: Wire the page to query params**

```ts
const codes = computed(() => parseCodes(route.query.codes));
const taskID = computed(() => String(route.query.task_id || '').trim());

function openManagement() {
  router.push({
    name: 'DeviceV2Management',
    query: {
      codes: codes.value.join(','),
      task_id: taskID.value,
    },
  });
}
```

- [ ] **Step 6: Run route and browser smoke**

Run:

```bash
node scripts/d2-redesign-browser-smoke.cjs
node scripts/d2-la-import-apply-handoff.cjs
```

Expected:

- the redesign browser smoke still loads
- the handoff smoke sees the new handoff route and management jump

- [ ] **Step 7: Commit**

```bash
git add \
  OneOPS-UI/src/router/utils.ts \
  OneOPS-UI/src/views/device/DeviceV2IngestSuccessHandoff.vue \
  OneOPS-UI/scripts/d2-la-import-apply-handoff.cjs \
  OneOPS-UI/scripts/d2-redesign-browser-smoke.cjs
git commit -m "feat: add ingest success handoff page"
```

## Task 5: Make Management Handoff Reliable

**Files:**
- Modify: `OneOPS-UI/src/views/device/DeviceV2ManagementGrouped.vue`
- Modify: `OneOPS-UI/src/api/device/device-v2.ts`
- Modify: `OneOps/app/device/v2/api/device_v2.go`
- Modify: `OneOps/app/device/v2/service/impl/device_v2_minimal_read.go`
- Test: `OneOPS-UI/scripts/d2-la-import-apply-handoff.cjs`
- Test: `OneOps/app/device/v2/api/device_v2_test.go`

- [ ] **Step 1: Write the failing backend test for task-id fallback**

```go
func TestListDeviceV2ByIngestTaskID(t *testing.T) {
	// seed device_v2 entities and ingest task result with handoff.success_device_codes
	req := httptest.NewRequest(http.MethodGet, "/api/v1/device/v2/list?task_id=ingest-task-1", nil)
	// perform request...
	assert.Equal(t, 2, len(resp.Data.List))
	assert.Equal(t, "DVC-A", resp.Data.List[0].Code)
}
```

- [ ] **Step 2: Run the backend test to verify it fails**

Run:

```bash
go test ./OneOps/app/device/v2/api -run TestListDeviceV2ByIngestTaskID -v
```

Expected:

- FAIL because list API does not use `task_id` as a handoff fallback yet

- [ ] **Step 3: Add a list-layer helper that resolves success codes from ingest task**

```go
func (a *DeviceV2API) resolveIngestTaskCodes(ctx context.Context, taskID string) ([]string, error) {
	taskID = strings.TrimSpace(taskID)
	if taskID == "" {
		return nil, nil
	}
	var task ingestmodel.DeviceV2IngestTask
	if err := a.db(ctx).Where("task_id = ?", taskID).First(&task).Error; err != nil {
		return nil, err
	}
	postCheck := entitycore.ParseAnyMap(task.ResultJSON)["post_check"].(map[string]interface{})
	handoff := postCheck["handoff"].(map[string]interface{})
	return interfaceSliceToStrings(handoff["success_device_codes"]), nil
}
```

- [ ] **Step 4: Apply the fallback when the request has `task_id`**

```go
var codes []string
if req.Codes != "" {
	// existing parsing...
}
if len(codes) == 0 && strings.TrimSpace(req.TaskID) != "" {
	resolvedCodes, err := a.resolveIngestTaskCodes(ctx.Request.Context(), req.TaskID)
	if err != nil {
		failWithDeviceV2OutputError(ctx, standardizeDeviceV2ReadError(err.Error(), "list_devices", "设备列表暂时无法读取，请稍后重试。"))
		return
	}
	codes = append(codes, resolvedCodes...)
}
```

- [ ] **Step 5: Consume the fallback in the management page**

```ts
const hasHandoffFallback = computed(() => !prefillCodes.value.length && !!handoffTaskId.value);

function buildDeviceListParams(): DeviceV2ListReq {
  return {
    page: pagination.current,
    page_size: pagination.pageSize,
    codes: effectiveCodeScope.value.length ? effectiveCodeScope.value.join(',') : undefined,
    task_id: hasHandoffFallback.value ? handoffTaskId.value : undefined,
    ...routeListParams,
    filters: usesRouteNativeParams ? undefined : buildStructuredFilterClauses(),
  };
}
```

- [ ] **Step 6: Re-run frontend and backend handoff tests**

Run:

```bash
go test ./OneOps/app/device/v2/api -run TestListDeviceV2ByIngestTaskID -v
node scripts/d2-la-import-apply-handoff.cjs
```

Expected:

- backend list test passes
- handoff smoke sees the management page load the expected batch

- [ ] **Step 7: Commit**

```bash
git add \
  OneOPS-UI/src/views/device/DeviceV2ManagementGrouped.vue \
  OneOPS-UI/src/api/device/device-v2.ts \
  OneOps/app/device/v2/api/device_v2.go \
  OneOps/app/device/v2/service/impl/device_v2_minimal_read.go \
  OneOps/app/device/v2/api/device_v2_test.go
git commit -m "feat: add reliable ingest handoff to device management"
```

## Task 6: Final Verification And Docs Sync

**Files:**
- Modify: `docs/superpowers/specs/2026-06-22-oneops-device-v2-ingest-productized-flow-design.md` (only if implementation drift is found)

- [ ] **Step 1: Run the frontend verification batch**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOPS-UI
npm run typecheck:d2
node scripts/d2-ingest-buttons-smoke.cjs
node scripts/d2-redesign-browser-smoke.cjs
node scripts/d2-la-import-apply-handoff.cjs
npx esbuild scripts/d2-ingest-productized-flow-smoke.ts --bundle --platform=node --format=esm --outfile=.tmp/d2-ingest-productized-flow-smoke.mjs >/dev/null && node .tmp/d2-ingest-productized-flow-smoke.mjs
```

Expected:

- all smoke scripts pass
- `typecheck:d2` passes

- [ ] **Step 2: Run the backend verification batch**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL
go test ./OneOps/app/device/v2/ingest/service/impl ./OneOps/app/device/v2/ingest/api ./OneOps/app/device/v2/api -run 'Test(BuildPreparedTaskIncludesHandoffSummary|SubmitTaskReturnsPartialSuccessHandoff|ListDeviceV2ByIngestTaskID)' -v
```

Expected:

- all targeted backend tests pass

- [ ] **Step 3: Compare implementation against the spec**

```md
- Step 1 only exposes a single default CTA: 上传清单
- Step 2 prioritizes blocking issues over descriptive guidance
- Step 3 only confirms submit-ready devices
- Step 4 uses a dedicated success handoff page
- Large explanatory cards are gone from the default flow
- Success navigation only uses real success codes and task fallback
```

- [ ] **Step 4: Update the spec if drift is discovered**

```md
If the implementation naming differs (for example, "成功交接" vs "导入成功交接"),
edit the spec so it matches the shipped behavior exactly.
```

- [ ] **Step 5: Commit**

```bash
git add \
  docs/superpowers/specs/2026-06-22-oneops-device-v2-ingest-productized-flow-design.md
git commit -m "docs: sync ingest productized flow spec with implementation"
```

## Self-Review

### Spec coverage

- 四步流程：Task 3 + Task 4
- 真实成功语义：Task 1 + Task 2
- 管理页稳定可见：Task 5
- 去掉解释型大卡片：Task 3
- 成功交接页：Task 4

没有遗漏的 spec 段落。

### Placeholder scan

- 没有 `TODO` / `TBD`
- 每个代码步骤都有明确文件和示例代码
- 每个验证步骤都有精确命令

### Type consistency

- 前端统一使用 `resolveIngestFlowOutcome`
- 前端统一使用 `task_id` + `codes` 做交接
- 后端统一使用 `post_check.handoff.success_device_codes` 作为成功集合

没有名称冲突。
