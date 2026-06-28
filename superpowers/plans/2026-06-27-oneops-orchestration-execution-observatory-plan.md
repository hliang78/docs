# OneOps Orchestration Execution Observatory Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a real test/pre-production observability page for orchestration executions, backed by real OneOps execution data and safe navigation-first operator flows.

**Architecture:** Extend the existing `OneOps/app/orchestration` backend with execution summary and list APIs, then add a hidden `OneOPS-UI` platform page that polls those APIs and renders a two-tab `Execution Observatory` experience. Keep the page read-oriented in phase 1: execution overview, detail drawer, event timeline, and `Action Required` navigation without direct in-page execution mutation.

**Tech Stack:** Go, Gin, GORM, Vue 3, TypeScript, Ant Design Vue, existing `request` utility, existing `ProTable` patterns, existing hidden-route registration in `src/router/utils.ts`.

---

## File Structure

### Backend (`OneOps`)

- Modify: `OneOps/app/orchestration/dto/execution.go`
  Purpose: add DTOs for execution list rows, summary response, and list query contracts.
- Modify: `OneOps/app/orchestration/service/i_execution.go`
  Purpose: extend execution service with list and summary methods.
- Modify: `OneOps/app/orchestration/service/impl/execution.go`
  Purpose: implement summary aggregation and filtered execution listing with context-derived fields.
- Modify: `OneOps/app/orchestration/api/execution.go`
  Purpose: expose summary and execution list HTTP handlers.
- Modify: `OneOps/app/orchestration/router/execution.go`
  Purpose: register summary and list routes before parameterized `:executionId` routes.
- Modify: `OneOps/app/orchestration/service/impl/execution_test.go`
  Purpose: add backend contract tests for summary and execution list behavior.

### Frontend (`OneOPS-UI`)

- Create: `OneOPS-UI/src/typings/orchestration/execution.ts`
  Purpose: define observatory-facing TypeScript contracts for summary, list rows, details, events, and action-required items.
- Create: `OneOPS-UI/src/api/orchestration/execution.ts`
  Purpose: wrap orchestration observatory APIs using the existing `request` utility.
- Create: `OneOPS-UI/src/views/platform/ExecutionObservatory.vue`
  Purpose: render the hidden real-environment observability page with tabs, cards, list, drawer, and polling.
- Modify: `OneOPS-UI/src/router/utils.ts`
  Purpose: register a hidden platform route for the observatory page.
- Modify: `OneOPS-UI/package.json`
  Purpose: add a dedicated smoke command for the observatory page.
- Create: `OneOPS-UI/scripts/execution-observatory-smoke.ts`
  Purpose: smoke-check route registration and API wrapper availability without needing a browser E2E harness.

### Documentation

- Modify: `docs/runbooks/alert-to-ticket-dagengine-mvp.md`
  Purpose: record the hidden route and operator validation path for the observatory page.

## Task 1: Add Backend Summary And Execution List APIs

**Files:**
- Modify: `OneOps/app/orchestration/dto/execution.go`
- Modify: `OneOps/app/orchestration/service/i_execution.go`
- Modify: `OneOps/app/orchestration/service/impl/execution.go`
- Modify: `OneOps/app/orchestration/api/execution.go`
- Modify: `OneOps/app/orchestration/router/execution.go`
- Modify: `OneOps/app/orchestration/service/impl/execution_test.go`

- [ ] **Step 1: Write the failing backend tests**

```go
func TestExecutionService_ListExecutionsIncludesContextFields(t *testing.T) {
	db := newExecutionTestDB(t)
	now := time.Now().UTC().Truncate(time.Second)

	records := []orchestrationModel.TemplateExecution{
		{
			ID:           "exec-running-1",
			TemplateCode: "alert-ticket-default",
			Environment:  "prod",
			Status:       "running",
			ResultJSON:   `{"alert_code":"ALERT-1","ticket_code":"TICKET-1","last_node":"dispatch_ticket"}`,
			CreatedAt:    now.Add(-10 * time.Minute),
			UpdatedAt:    now.Add(-1 * time.Minute),
		},
		{
			ID:            "exec-waiting-1",
			TemplateCode:  "alert-ticket-default",
			Environment:   "prod",
			Status:        "waiting_callback",
			WaitingNodeID: "wait_callback",
			WaitType:      "callback",
			ResultJSON:    `{"alert_code":"ALERT-2","ticket_code":"TICKET-2","last_node":"wait_callback"}`,
			CreatedAt:     now.Add(-20 * time.Minute),
			UpdatedAt:     now.Add(-2 * time.Minute),
		},
	}
	for _, record := range records {
		if err := db.Create(&record).Error; err != nil {
			t.Fatalf("create execution failed: %v", err)
		}
	}

	svc := NewExecutionSrv(db, zap.NewNop(), nil, nil)
	items, err := svc.ListExecutions(context.Background(), dto.ExecutionListReq{
		Status:   "waiting_callback",
		Page:     1,
		PageSize: 20,
	})
	if err != nil {
		t.Fatalf("ListExecutions returned error: %v", err)
	}
	if len(items.Items) != 1 {
		t.Fatalf("item count = %d, want %d", len(items.Items), 1)
	}
	if items.Items[0].TicketCode != "TICKET-2" {
		t.Fatalf("ticket code = %q, want %q", items.Items[0].TicketCode, "TICKET-2")
	}
	if items.Items[0].LastNode != "wait_callback" {
		t.Fatalf("last node = %q, want %q", items.Items[0].LastNode, "wait_callback")
	}
}

func TestExecutionService_GetExecutionSummaryAggregatesStatuses(t *testing.T) {
	db := newExecutionTestDB(t)
	statuses := []string{"running", "waiting_callback", "escalated", "completed", "failed"}
	for i, status := range statuses {
		record := orchestrationModel.TemplateExecution{
			ID:           fmt.Sprintf("exec-summary-%d", i),
			TemplateCode: "alert-ticket-default",
			Environment:  "prod",
			Status:       status,
			ResultJSON:   `{}`,
			CreatedAt:    time.Now().Add(time.Duration(-i) * time.Minute),
			UpdatedAt:    time.Now().Add(time.Duration(-i) * time.Minute),
		}
		if err := db.Create(&record).Error; err != nil {
			t.Fatalf("create execution failed: %v", err)
		}
	}

	svc := NewExecutionSrv(db, zap.NewNop(), nil, nil)
	summary, err := svc.GetExecutionSummary(context.Background())
	if err != nil {
		t.Fatalf("GetExecutionSummary returned error: %v", err)
	}
	if summary.RunningCount != 1 || summary.WaitingCount != 1 || summary.EscalatedCount != 1 {
		t.Fatalf("unexpected summary: %+v", summary)
	}
	if summary.CompletedCount != 1 || summary.FailedCount != 1 {
		t.Fatalf("unexpected summary: %+v", summary)
	}
}
```

- [ ] **Step 2: Run the backend tests to verify they fail**

Run: `cd /home/jacky/project/OneOPS-ALL/OneOps && go test ./app/orchestration/service/impl -run 'TestExecutionService_(ListExecutionsIncludesContextFields|GetExecutionSummaryAggregatesStatuses)' -count=1`

Expected: FAIL with missing `ListExecutions`, `GetExecutionSummary`, or missing DTO/type errors.

- [ ] **Step 3: Add the backend DTO and service contracts**

```go
type ExecutionListReq struct {
	Status       string `form:"status"`
	TemplateCode string `form:"template_code"`
	Keyword      string `form:"keyword"`
	TimeFrom     string `form:"time_from"`
	TimeTo       string `form:"time_to"`
	Page         int    `form:"page"`
	PageSize     int    `form:"page_size"`
}

type ExecutionListItemResp struct {
	ExecutionID   string `json:"execution_id"`
	Status        string `json:"status"`
	TemplateCode  string `json:"template_code"`
	WaitingNodeID string `json:"waiting_node_id,omitempty"`
	WaitType      string `json:"wait_type,omitempty"`
	AlertCode     string `json:"alert_code,omitempty"`
	TicketCode    string `json:"ticket_code,omitempty"`
	LastNode      string `json:"last_node,omitempty"`
	CreatedAt     string `json:"created_at"`
	UpdatedAt     string `json:"updated_at"`
}

type ExecutionListResp struct {
	Items    []ExecutionListItemResp `json:"items"`
	Total    int64                   `json:"total"`
	Page     int                     `json:"page"`
	PageSize int                     `json:"page_size"`
}

type ExecutionSummaryResp struct {
	RunningCount   int64  `json:"running_count"`
	WaitingCount   int64  `json:"waiting_count"`
	EscalatedCount int64  `json:"escalated_count"`
	CompletedCount int64  `json:"completed_count"`
	FailedCount    int64  `json:"failed_count"`
	UpdatedAt      string `json:"updated_at"`
}
```

```go
type IExecution interface {
	StartExecution(ctx context.Context, req dto.StartExecutionReq) (*dto.ExecutionResp, error)
	GetExecution(ctx context.Context, executionID string) (*dto.ExecutionResp, error)
	ListExecutionEvents(ctx context.Context, executionID string) ([]dto.ExecutionEventResp, error)
	ListActionRequiredEvents(ctx context.Context, limit int) ([]dto.ExecutionActionRequiredResp, error)
	ListExecutions(ctx context.Context, req dto.ExecutionListReq) (*dto.ExecutionListResp, error)
	GetExecutionSummary(ctx context.Context) (*dto.ExecutionSummaryResp, error)
}
```

- [ ] **Step 4: Implement the backend list and summary logic**

```go
func (s *ExecutionSrv) ListExecutions(ctx context.Context, req dto.ExecutionListReq) (*dto.ExecutionListResp, error) {
	if s.DB == nil {
		return nil, fmt.Errorf("orchestration execution service requires db")
	}

	page := req.Page
	if page <= 0 {
		page = 1
	}
	pageSize := normalizeListLimit(req.PageSize, 20, 100)

	query := s.DB.WithContext(ctx).Model(&orchestrationModel.TemplateExecution{})
	if value := strings.TrimSpace(req.Status); value != "" {
		query = query.Where("status = ?", value)
	}
	if value := strings.TrimSpace(req.TemplateCode); value != "" {
		query = query.Where("template_code = ?", value)
	}
	if value := strings.TrimSpace(req.Keyword); value != "" {
		like := "%" + value + "%"
		query = query.Where("id LIKE ? OR result_json LIKE ?", like, like)
	}
	if ts, ok := parseRFC3339Time(req.TimeFrom); ok {
		query = query.Where("updated_at >= ?", ts)
	}
	if ts, ok := parseRFC3339Time(req.TimeTo); ok {
		query = query.Where("updated_at <= ?", ts)
	}

	var total int64
	if err := query.Count(&total).Error; err != nil {
		return nil, err
	}

	var rows []orchestrationModel.TemplateExecution
	if err := query.Order("updated_at desc").Offset((page-1)*pageSize).Limit(pageSize).Find(&rows).Error; err != nil {
		return nil, err
	}

	items := make([]dto.ExecutionListItemResp, 0, len(rows))
	for _, row := range rows {
		contextData, _ := decodeExecutionContextJSON(row.ResultJSON)
		items = append(items, dto.ExecutionListItemResp{
			ExecutionID:   row.ID,
			Status:        row.Status,
			TemplateCode:  row.TemplateCode,
			WaitingNodeID: row.WaitingNodeID,
			WaitType:      row.WaitType,
			AlertCode:     eventPayloadString(contextData, "alert_code"),
			TicketCode:    eventPayloadString(contextData, "ticket_code"),
			LastNode:      eventPayloadString(contextData, "last_node"),
			CreatedAt:     formatRFC3339(row.CreatedAt),
			UpdatedAt:     formatRFC3339(row.UpdatedAt),
		})
	}

	return &dto.ExecutionListResp{Items: items, Total: total, Page: page, PageSize: pageSize}, nil
}

func (s *ExecutionSrv) GetExecutionSummary(ctx context.Context) (*dto.ExecutionSummaryResp, error) {
	if s.DB == nil {
		return nil, fmt.Errorf("orchestration execution service requires db")
	}

	type statusCount struct {
		Status string
		Count  int64
	}
	var rows []statusCount
	if err := s.DB.WithContext(ctx).
		Model(&orchestrationModel.TemplateExecution{}).
		Select("status, COUNT(*) AS count").
		Group("status").
		Scan(&rows).Error; err != nil {
		return nil, err
	}

	summary := &dto.ExecutionSummaryResp{UpdatedAt: formatRFC3339(time.Now())}
	for _, row := range rows {
		switch strings.TrimSpace(row.Status) {
		case "running":
			summary.RunningCount += row.Count
		case "waiting_callback", "waiting_approval", "waiting":
			summary.WaitingCount += row.Count
		case "escalated":
			summary.EscalatedCount += row.Count
		case "completed":
			summary.CompletedCount += row.Count
		case "failed":
			summary.FailedCount += row.Count
		}
	}
	return summary, nil
}
```

- [ ] **Step 5: Expose HTTP handlers and routes**

```go
func (a *ExecutionAPI) ListExecutions(ctx *gin.Context) {
	var req dto.ExecutionListReq
	req.Status = ctx.Query("status")
	req.TemplateCode = ctx.Query("template_code")
	req.Keyword = ctx.Query("keyword")
	req.TimeFrom = ctx.Query("time_from")
	req.TimeTo = ctx.Query("time_to")
	req.Page, _ = strconv.Atoi(ctx.DefaultQuery("page", "1"))
	req.PageSize, _ = strconv.Atoi(ctx.DefaultQuery("page_size", "20"))

	resp, err := a.ExecutionSrv.ListExecutions(ctx, req)
	if err != nil {
		response.FailWithMsg(err.Error(), ctx)
		return
	}
	response.OkWithData(resp, ctx)
}

func (a *ExecutionAPI) GetExecutionSummary(ctx *gin.Context) {
	resp, err := a.ExecutionSrv.GetExecutionSummary(ctx)
	if err != nil {
		response.FailWithMsg(err.Error(), ctx)
		return
	}
	response.OkWithData(resp, ctx)
}
```

```go
func Execution(r *gin.RouterGroup, api *api.ExecutionAPI) {
	g := r.Group("orchestration/executions")
	g.POST("", api.StartExecution)
	g.GET("summary", api.GetExecutionSummary)
	g.GET("action-required", api.ListActionRequiredEvents)
	g.GET("", api.ListExecutions)
	g.GET(":executionId", api.GetExecution)
	g.GET(":executionId/events", api.ListExecutionEvents)
}
```

- [ ] **Step 6: Run the backend tests to verify they pass**

Run: `cd /home/jacky/project/OneOPS-ALL/OneOps && go test ./app/orchestration/service/impl -run 'TestExecutionService_(ListExecutionsIncludesContextFields|GetExecutionSummaryAggregatesStatuses|ListExecutionEvents|ListActionRequiredEvents)' -count=1`

Expected: PASS

- [ ] **Step 7: Commit the backend API slice**

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
git add app/orchestration/dto/execution.go \
  app/orchestration/service/i_execution.go \
  app/orchestration/service/impl/execution.go \
  app/orchestration/api/execution.go \
  app/orchestration/router/execution.go \
  app/orchestration/service/impl/execution_test.go
git commit -m "feat: add orchestration execution observatory APIs"
```

## Task 2: Add Frontend Observatory Types And API Wrappers

**Files:**
- Create: `OneOPS-UI/src/typings/orchestration/execution.ts`
- Create: `OneOPS-UI/src/api/orchestration/execution.ts`

- [ ] **Step 1: Write the failing frontend smoke script**

```ts
import { executionListReq, executionSummaryReq, executionEventsReq, executionActionRequiredReq } from '../src/api/orchestration/execution';

function assertFn(name: string, value: unknown) {
  if (typeof value !== 'function') {
    throw new Error(`${name} should be a function`);
  }
}

assertFn('executionListReq', executionListReq);
assertFn('executionSummaryReq', executionSummaryReq);
assertFn('executionEventsReq', executionEventsReq);
assertFn('executionActionRequiredReq', executionActionRequiredReq);

console.log('execution observatory api smoke ok');
```

- [ ] **Step 2: Run the smoke script to verify it fails**

Run: `cd /home/jacky/project/OneOPS-ALL/OneOPS-UI && npx esbuild scripts/execution-observatory-smoke.ts --bundle --platform=node --format=esm --outfile=.tmp/execution-observatory-smoke.mjs >/dev/null && node .tmp/execution-observatory-smoke.mjs`

Expected: FAIL because `src/api/orchestration/execution.ts` does not exist yet.

- [ ] **Step 3: Add TypeScript contracts**

```ts
export interface ExecutionSummaryResp {
  running_count: number;
  waiting_count: number;
  escalated_count: number;
  completed_count: number;
  failed_count: number;
  updated_at: string;
}

export interface ExecutionListItemResp {
  execution_id: string;
  status: string;
  template_code: string;
  waiting_node_id?: string;
  wait_type?: string;
  alert_code?: string;
  ticket_code?: string;
  last_node?: string;
  created_at: string;
  updated_at: string;
}

export interface ExecutionListResp {
  items: ExecutionListItemResp[];
  total: number;
  page: number;
  page_size: number;
}

export interface ExecutionQueryReq {
  status?: string;
  template_code?: string;
  keyword?: string;
  time_from?: string;
  time_to?: string;
  page?: number;
  page_size?: number;
}
```

- [ ] **Step 4: Add API wrapper functions**

```ts
import request, { HTTP_GET } from '@/utils/request';
import type {
  ExecutionActionRequiredResp,
  ExecutionEventResp,
  ExecutionListResp,
  ExecutionQueryReq,
  ExecutionResp,
  ExecutionSummaryResp,
} from '@/typings/orchestration/execution';

export const executionSummaryReq = async () =>
  request<ExecutionSummaryResp>({
    url: '/orchestration/executions/summary',
    method: HTTP_GET,
  });

export const executionListReq = async (params: ExecutionQueryReq) =>
  request<ExecutionListResp>({
    url: '/orchestration/executions',
    method: HTTP_GET,
    params,
  });

export const executionDetailReq = async (executionId: string) =>
  request<ExecutionResp>({
    url: `/orchestration/executions/${executionId}`,
    method: HTTP_GET,
  });

export const executionEventsReq = async (executionId: string) =>
  request<ExecutionEventResp[]>({
    url: `/orchestration/executions/${executionId}/events`,
    method: HTTP_GET,
  });

export const executionActionRequiredReq = async (limit = 50) =>
  request<ExecutionActionRequiredResp[]>({
    url: '/orchestration/executions/action-required',
    method: HTTP_GET,
    params: { limit },
  });
```

- [ ] **Step 5: Run the smoke script to verify it passes**

Run: `cd /home/jacky/project/OneOPS-ALL/OneOPS-UI && npx esbuild scripts/execution-observatory-smoke.ts --bundle --platform=node --format=esm --outfile=.tmp/execution-observatory-smoke.mjs >/dev/null && node .tmp/execution-observatory-smoke.mjs`

Expected: PASS with `execution observatory api smoke ok`

- [ ] **Step 6: Commit the frontend API slice**

```bash
cd /home/jacky/project/OneOPS-ALL/OneOPS-UI
git add src/typings/orchestration/execution.ts src/api/orchestration/execution.ts scripts/execution-observatory-smoke.ts
git commit -m "feat: add execution observatory frontend api contracts"
```

## Task 3: Build The Hidden `ExecutionObservatory` Page

**Files:**
- Create: `OneOPS-UI/src/views/platform/ExecutionObservatory.vue`
- Modify: `OneOPS-UI/src/router/utils.ts`
- Modify: `OneOPS-UI/package.json`
- Create: `OneOPS-UI/scripts/execution-observatory-smoke.ts`

- [ ] **Step 1: Write the failing route smoke check**

```ts
import { buildAsyncRoutes } from '../src/router/utils';

const routes = buildAsyncRoutes([
  {
    path: '/platform/execution-observatory',
    name: 'ExecutionObservatory',
    component: '@/views/platform/ExecutionObservatory.vue',
    meta: { title: '执行观测台', requiresAuth: true, hideInMenu: true },
  },
]);

const route = routes.find(item => item.name === 'ExecutionObservatory');
if (!route) {
  throw new Error('ExecutionObservatory route missing');
}
if (route.meta?.hideInMenu !== true) {
  throw new Error('ExecutionObservatory route should be hidden');
}

console.log('execution observatory route smoke ok');
```

- [ ] **Step 2: Run the smoke check to verify it fails**

Run: `cd /home/jacky/project/OneOPS-ALL/OneOPS-UI && npx esbuild scripts/execution-observatory-smoke.ts --bundle --platform=node --format=esm --outfile=.tmp/execution-observatory-smoke.mjs >/dev/null && node .tmp/execution-observatory-smoke.mjs`

Expected: FAIL because the route or page does not exist yet.

- [ ] **Step 3: Implement the hidden route registration**

```ts
const executionObservatoryRoute: RouteRecordRaw = {
  path: 'platform/execution-observatory',
  name: 'ExecutionObservatory',
  component: () => import('@/views/platform/ExecutionObservatory.vue'),
  meta: {
    title: '执行观测台',
    requiresAuth: true,
    hideInMenu: true,
  },
};
```

```ts
return [
  ...asyncRoutes,
  executionObservatoryRoute,
  metricMetadataManagementRoute,
  dataQualityManagementRoute,
];
```

- [ ] **Step 4: Implement the page shell with tabs, cards, list, and drawer**

```vue
<template>
  <div class="page-container execution-observatory">
    <a-alert
      type="warning"
      show-icon
      message="测试/预发真实执行环境"
      description="本页展示真实 orchestration execution，不提供首页内直接 approve/reject/resume。"
      class="hero-alert"
    />

    <a-tabs v-model:active-key="activeTab" type="card">
      <a-tab-pane key="executions" tab="Executions">
        <div class="summary-grid">
          <a-card v-for="card in summaryCards" :key="card.key" size="small" class="summary-card" @click="applyStatusFilter(card.status)">
            <div class="summary-card__label">{{ card.label }}</div>
            <div class="summary-card__value">{{ card.value }}</div>
          </a-card>
        </div>

        <a-form layout="inline" :model="filters" class="toolbar">
          <a-select v-model:value="filters.status" placeholder="状态" allow-clear style="width: 180px" />
          <a-input v-model:value="filters.template_code" placeholder="模板编码" allow-clear style="width: 200px" />
          <a-input v-model:value="filters.keyword" placeholder="关键字" allow-clear style="width: 220px" />
          <a-space>
            <a-button type="primary" @click="loadExecutions">查询</a-button>
            <a-button @click="resetFilters">重置</a-button>
          </a-space>
        </a-form>

        <pro-table
          row-key="execution_id"
          :columns="executionColumns"
          :data-source="executionRows"
          :is-loading="loading.executions"
          :pagination="pagination"
          :refersh="loadExecutions"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.dataIndex === 'execution_id'">
              <a @click="openExecutionDrawer(record)">{{ record.execution_id }}</a>
            </template>
            <template v-if="column.dataIndex === 'status'">
              <a-tag :color="statusTagColor(record.status)">{{ record.status }}</a-tag>
            </template>
          </template>
        </pro-table>
      </a-tab-pane>

      <a-tab-pane key="actionRequired" tab="Action Required">
        <pro-table
          row-key="event_id"
          :columns="actionRequiredColumns"
          :data-source="actionRequiredRows"
          :is-loading="loading.actionRequired"
          :pagination="false"
        />
      </a-tab-pane>
    </a-tabs>

    <a-drawer v-model:open="drawer.visible" width="720" title="Execution Detail">
      <a-descriptions v-if="drawer.detail" bordered :column="1" size="small">
        <a-descriptions-item label="Execution ID">{{ drawer.detail.id }}</a-descriptions-item>
        <a-descriptions-item label="状态">{{ drawer.detail.status }}</a-descriptions-item>
        <a-descriptions-item label="模板">{{ drawer.detail.template_code }}</a-descriptions-item>
        <a-descriptions-item label="等待类型">{{ drawer.detail.wait_type || '-' }}</a-descriptions-item>
        <a-descriptions-item label="最近更新时间">{{ drawer.detail.updated_at }}</a-descriptions-item>
      </a-descriptions>
    </a-drawer>
  </div>
</template>
```

- [ ] **Step 5: Wire data loading, polling, and drawer fetches**

```ts
const activeTab = ref('executions');
const filters = reactive({ status: '', template_code: '', keyword: '', page: 1, page_size: 20 });
const loading = reactive({ summary: false, executions: false, actionRequired: false, detail: false });
const executionRows = ref<ExecutionListItemResp[]>([]);
const actionRequiredRows = ref<ExecutionActionRequiredResp[]>([]);
const summary = ref<ExecutionSummaryResp | null>(null);
const drawer = reactive({
  visible: false,
  executionId: '',
  detail: null as ExecutionResp | null,
  events: [] as ExecutionEventResp[],
});

let pollTimer: ReturnType<typeof setInterval> | null = null;

async function loadSummary() {
  loading.summary = true;
  try {
    summary.value = await executionSummaryReq();
  } finally {
    loading.summary = false;
  }
}

async function loadExecutions() {
  loading.executions = true;
  try {
    const resp = await executionListReq(filters);
    executionRows.value = resp.items ?? [];
    pagination.total = resp.total ?? 0;
  } finally {
    loading.executions = false;
  }
}

async function openExecutionDrawer(row: ExecutionListItemResp) {
  drawer.visible = true;
  drawer.executionId = row.execution_id;
  loading.detail = true;
  try {
    const [detail, events] = await Promise.all([
      executionDetailReq(row.execution_id),
      executionEventsReq(row.execution_id),
    ]);
    drawer.detail = detail;
    drawer.events = events ?? [];
  } finally {
    loading.detail = false;
  }
}

function startPolling() {
  stopPolling();
  pollTimer = setInterval(() => {
    if (activeTab.value === 'executions') {
      void Promise.all([loadSummary(), loadExecutions()]);
    } else {
      void loadActionRequired();
    }
  }, 15000);
}
```

- [ ] **Step 6: Add the package script and run smoke + typecheck**

```json
"smoke:execution-observatory": "npx esbuild scripts/execution-observatory-smoke.ts --bundle --platform=node --format=esm --outfile=.tmp/execution-observatory-smoke.mjs >/dev/null && node .tmp/execution-observatory-smoke.mjs"
```

Run: `cd /home/jacky/project/OneOPS-ALL/OneOPS-UI && npm run smoke:execution-observatory && npm run typecheck`

Expected: PASS

- [ ] **Step 7: Commit the frontend page slice**

```bash
cd /home/jacky/project/OneOPS-ALL/OneOPS-UI
git add src/views/platform/ExecutionObservatory.vue src/router/utils.ts package.json scripts/execution-observatory-smoke.ts
git commit -m "feat: add execution observatory page"
```

## Task 4: Finalize Action-Required Navigation And Runbook

**Files:**
- Modify: `OneOPS-UI/src/views/platform/ExecutionObservatory.vue`
- Modify: `docs/runbooks/alert-to-ticket-dagengine-mvp.md`

- [ ] **Step 1: Write the failing smoke assertion for action-required navigation**

```ts
import fs from 'node:fs';

const source = fs.readFileSync('src/views/platform/ExecutionObservatory.vue', 'utf8');
if (!source.includes("tab=\"Action Required\"")) {
  throw new Error('Action Required tab missing');
}
if (!source.includes('openTicketDetail')) {
  throw new Error('ticket navigation helper missing');
}

console.log('execution observatory action-required smoke ok');
```

- [ ] **Step 2: Run the smoke assertion to verify it fails**

Run: `cd /home/jacky/project/OneOPS-ALL/OneOPS-UI && npm run smoke:execution-observatory`

Expected: FAIL until the tab and navigation helpers exist.

- [ ] **Step 3: Add action-required row actions and safe navigation helpers**

```ts
const actionRequiredColumns = [
  { title: 'Ticket', dataIndex: 'ticket_code', key: 'ticket_code' },
  { title: 'Execution', dataIndex: 'execution_id', key: 'execution_id' },
  { title: 'Action', dataIndex: 'action_key', key: 'action_key' },
  { title: 'Reason', dataIndex: 'reason', key: 'reason' },
  { title: 'Occurred At', dataIndex: 'occurred_at', key: 'occurred_at' },
  { title: '操作', key: 'action' },
];

function openTicketDetail(ticketCode?: string) {
  if (!ticketCode) return;
  router.push({ path: `/ticket/alert-ticket`, query: { code: ticketCode } });
}

function openExecutionFromAction(item: ExecutionActionRequiredResp) {
  activeTab.value = 'executions';
  filters.keyword = item.execution_id;
  void loadExecutions();
}
```

```vue
<template #bodyCell="{ column, record }">
  <template v-if="column.key === 'action'">
    <a-space>
      <a @click="openExecutionFromAction(record)">查看执行</a>
      <a @click="openTicketDetail(record.ticket_code)">查看工单</a>
    </a-space>
  </template>
</template>
```

- [ ] **Step 4: Update the runbook with the hidden route and validation path**

```md
- Hidden real-environment UI route: `/platform/execution-observatory`
- `Executions` tab verifies real runtime activity through summary cards, execution rows, and event drawers.
- `Action Required` tab verifies escalated/manual-action executions can be located and traced without direct in-page mutation.
```

- [ ] **Step 5: Run final frontend and backend verification**

Run: `cd /home/jacky/project/OneOPS-ALL/OneOps && go test ./app/orchestration/... ./app/alert/... ./app/alert_engine/... ./boot/provider ./initialize -count=1`

Expected: PASS

Run: `cd /home/jacky/project/OneOPS-ALL/OneOPS-UI && npm run smoke:execution-observatory && npm run typecheck`

Expected: PASS

- [ ] **Step 6: Commit the navigation and docs slice**

```bash
cd /home/jacky/project/OneOPS-ALL/OneOPS-UI
git add src/views/platform/ExecutionObservatory.vue
git commit -m "feat: add execution observatory action routing"

cd /home/jacky/project/OneOPS-ALL
git add docs/runbooks/alert-to-ticket-dagengine-mvp.md docs/superpowers/plans/2026-06-27-oneops-orchestration-execution-observatory-plan.md
git commit -m "docs: add execution observatory rollout notes"
```
