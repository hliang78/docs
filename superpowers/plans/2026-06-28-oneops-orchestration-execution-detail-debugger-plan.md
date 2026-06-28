# OneOps Orchestration Execution Detail Debugger Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a dedicated execution detail debugger page with a real execution graph, dual ops/debug views, and real waiting-execution resume actions.

**Architecture:** Keep `ExecutionObservatory` as the overview entry point and add a dedicated `Execution Detail` page backed by a lightweight backend graph projection API. Reuse the existing orchestration execution detail, events, agent-task, and resume APIs; add only one new graph endpoint plus focused frontend components for runtime graph rendering and node inspection.

**Tech Stack:** Go, Gin, GORM, Google Wire, Vue 3, TypeScript, Ant Design Vue, existing `request` utility, existing orchestration acceptance-script pattern, existing hidden route registration in `OneOPS-UI/src/router/utils.ts`.

---

## File Structure

### Backend (`OneOps`)

- Create: `OneOps/app/orchestration/dto/execution_graph.go`
  Purpose: define graph-specific DTOs without bloating `dto/execution.go`.
- Create: `OneOps/app/orchestration/service/i_execution_graph.go`
  Purpose: define the graph projection service contract.
- Create: `OneOps/app/orchestration/service/impl/execution_graph.go`
  Purpose: project template structure plus runtime state into a read-only execution graph response.
- Create: `OneOps/app/orchestration/service/impl/execution_graph_test.go`
  Purpose: regression tests for graph projection semantics.
- Modify: `OneOps/app/orchestration/api/execution.go`
  Purpose: expose `GET /orchestration/executions/:executionId/graph`.
- Modify: `OneOps/app/orchestration/router/execution.go`
  Purpose: register the graph route next to existing execution detail routes.
- Modify: `OneOps/boot/provider/service_groups.go`
  Purpose: wire the new graph projection service set into orchestration providers.
- Modify: `OneOps/cmd/wire_gen.go`
  Purpose: refresh generated wire injector output after adding the new service dependency.

### Frontend (`OneOPS-UI`)

- Modify: `OneOPS-UI/src/typings/orchestration/execution.ts`
  Purpose: add graph DTOs and node-inspector-facing types.
- Modify: `OneOPS-UI/src/api/orchestration/execution.ts`
  Purpose: add the execution graph API wrapper.
- Create: `OneOPS-UI/src/views/platform/ExecutionDetailDebugger.vue`
  Purpose: dedicated single-execution page with header, graph area, and dual detail views.
- Create: `OneOPS-UI/src/components/orchestration/ExecutionRuntimeGraph.vue`
  Purpose: render a read-only execution graph using the projected graph response.
- Create: `OneOPS-UI/src/components/orchestration/ExecutionOpsPanel.vue`
  Purpose: display current wait/action-required state and perform approve/reject/resume actions.
- Create: `OneOPS-UI/src/components/orchestration/ExecutionDebugPanel.vue`
  Purpose: display agent-task and execution-event timelines.
- Create: `OneOPS-UI/src/components/orchestration/ExecutionNodeInspector.vue`
  Purpose: show focused node details for the selected graph node.
- Modify: `OneOPS-UI/src/views/platform/ExecutionObservatory.vue`
  Purpose: replace drawer-first navigation with navigation to the dedicated detail page while keeping lightweight drawer support optional.
- Modify: `OneOPS-UI/src/router/utils.ts`
  Purpose: register the hidden execution detail route.
- Modify: `OneOPS-UI/package.json`
  Purpose: add smoke and real-API acceptance commands for the debugger page.
- Create: `OneOPS-UI/scripts/execution-detail-debugger-smoke.ts`
  Purpose: verify route registration, page import, and graph API wrapper wiring.
- Create: `OneOPS-UI/scripts/execution-detail-debugger-real-api-acceptance.ts`
  Purpose: seed a real execution, fetch the new graph endpoint, and print the detail debugger URL plus evidence.

### Documentation

- Modify: `docs/runbooks/alert-to-ticket-dagengine-mvp.md`
  Purpose: document the new execution detail debugger route and verification flow.

## Task 1: Add The Backend Graph Projection Contract

**Files:**
- Create: `OneOps/app/orchestration/dto/execution_graph.go`
- Create: `OneOps/app/orchestration/service/i_execution_graph.go`
- Create: `OneOps/app/orchestration/service/impl/execution_graph.go`
- Create: `OneOps/app/orchestration/service/impl/execution_graph_test.go`

- [ ] **Step 1: Write the failing graph projection tests**

```go
func TestExecutionGraphService_GetExecutionGraphProjectsCurrentWaitState(t *testing.T) {
	db, err := gorm.Open(sqlite.Open("file::memory:?cache=shared"), &gorm.Config{})
	if err != nil {
		t.Fatalf("open sqlite failed: %v", err)
	}
	if err := db.AutoMigrate(
		&orchestrationModel.TemplateDefinition{},
		&orchestrationModel.TemplateExecution{},
		&orchestrationModel.ExecutionEvent{},
		&orchestrationModel.AgentTask{},
		&orchestrationModel.SuspendRecord{},
	); err != nil {
		t.Fatalf("auto migrate failed: %v", err)
	}

	logger := zap.NewNop()
	templateSrv := NewTemplateSrv(db, logger)
	if _, err := templateSrv.ImportTemplate(context.Background(), dto.ImportTemplateReq{
		Code:        "multi-agent-closure",
		SourcePath:  filepath.Join("app", "orchestration", "template", "testdata", "multi_agent_ticket_closure"),
		Environment: "prod",
	}); err != nil {
		t.Fatalf("ImportTemplate returned error: %v", err)
	}

	execution := orchestrationModel.TemplateExecution{
		ID:            "exec-graph-1",
		TemplateCode:  "multi-agent-closure",
		Environment:   "prod",
		Status:        "waiting_approval",
		WaitingNodeID: "wait_approval",
		WaitType:      "approval",
		ResumeToken:   "resume-graph-1",
		ResultJSON:    `{"alert_code":"ALERT-GRAPH-1","ticket_code":"TICKET-GRAPH-1"}`,
	}
	if err := db.Create(&execution).Error; err != nil {
		t.Fatalf("create execution failed: %v", err)
	}
	if err := db.Create(&orchestrationModel.AgentTask{
		ID:               "task-graph-1",
		ExecutionID:      execution.ID,
		NodeID:           "recommend_dispatch",
		TaskType:         "recommend_dispatch",
		Status:           "completed",
		ResumeToken:      "agent-resume-1",
		AllowedToolsJSON: `["ticketing_api"]`,
		InputPayloadJSON: `{"alert_code":"ALERT-GRAPH-1"}`,
		ResultPayloadJSON: `{"dispatch_team":"noc"}`,
	}).Error; err != nil {
		t.Fatalf("create agent task failed: %v", err)
	}
	if err := db.Create(&orchestrationModel.ExecutionEvent{
		ID:          "evt-graph-1",
		ExecutionID: execution.ID,
		NodeID:      "wait_approval",
		NodeType:    "approval_wait_step",
		EventType:   "node_waiting",
		PayloadJSON: `{"wait_type":"approval"}`,
	}).Error; err != nil {
		t.Fatalf("create execution event failed: %v", err)
	}

	svc := NewExecutionGraphSrv(db, logger, templateSrv)
	resp, err := svc.GetExecutionGraph(context.Background(), execution.ID)
	if err != nil {
		t.Fatalf("GetExecutionGraph returned error: %v", err)
	}
	if resp.Execution.Status != "waiting_approval" {
		t.Fatalf("execution status = %q, want %q", resp.Execution.Status, "waiting_approval")
	}
	if resp.Execution.CurrentNodeID != "wait_approval" {
		t.Fatalf("current node = %q, want %q", resp.Execution.CurrentNodeID, "wait_approval")
	}
	waitNode := findGraphNodeByID(t, resp.Nodes, "wait_approval")
	if !waitNode.IsCurrent || !waitNode.IsWaiting {
		t.Fatalf("wait node flags = %+v, want current waiting node", waitNode)
	}
	dispatchNode := findGraphNodeByID(t, resp.Nodes, "recommend_dispatch")
	if dispatchNode.AgentTask == nil || dispatchNode.AgentTask.Status != "completed" {
		t.Fatalf("dispatch node agent task = %+v, want completed task", dispatchNode.AgentTask)
	}
	if dispatchNode.Route.Next != "wait_approval" {
		t.Fatalf("dispatch next route = %q, want %q", dispatchNode.Route.Next, "wait_approval")
	}
}

func findGraphNodeByID(t *testing.T, nodes []dto.ExecutionGraphNode, nodeID string) dto.ExecutionGraphNode {
	t.Helper()
	for _, node := range nodes {
		if node.NodeID == nodeID {
			return node
		}
	}
	t.Fatalf("graph node %q not found", nodeID)
	return dto.ExecutionGraphNode{}
}
```

- [ ] **Step 2: Run the new backend tests to verify they fail**

Run: `cd /home/jacky/project/OneOPS-ALL/OneOps && go test ./app/orchestration/service/impl -run 'TestExecutionGraphService_GetExecutionGraphProjectsCurrentWaitState' -count=1`

Expected: FAIL with `undefined: NewExecutionGraphSrv`, missing DTO types, or missing helper types.

- [ ] **Step 3: Add the graph DTOs and service interface**

```go
package dto

type ExecutionGraphResp struct {
	Execution ExecutionGraphExecution `json:"execution"`
	Nodes     []ExecutionGraphNode    `json:"nodes"`
	Edges     []ExecutionGraphEdge    `json:"edges"`
}

type ExecutionGraphExecution struct {
	ExecutionID   string `json:"execution_id"`
	TemplateCode  string `json:"template_code"`
	Environment   string `json:"environment"`
	Status        string `json:"status"`
	CurrentNodeID string `json:"current_node_id,omitempty"`
	WaitingNodeID string `json:"waiting_node_id,omitempty"`
	WaitType      string `json:"wait_type,omitempty"`
	ResumeToken   string `json:"resume_token,omitempty"`
	ActionRequired bool  `json:"action_required"`
}

type ExecutionGraphNode struct {
	NodeID              string                         `json:"node_id"`
	NodeName            string                         `json:"node_name"`
	NodeType            string                         `json:"node_type"`
	RuntimeStatus       string                         `json:"runtime_status"`
	ExecutionStatusHint string                         `json:"execution_status_hint,omitempty"`
	IsCurrent           bool                           `json:"is_current"`
	IsWaiting           bool                           `json:"is_waiting"`
	IsActionRequired    bool                           `json:"is_action_required"`
	WaitType            string                         `json:"wait_type,omitempty"`
	AgentTask           *ExecutionGraphAgentTask       `json:"agent_task,omitempty"`
	Route               ExecutionGraphRoute            `json:"route"`
	Summary             string                         `json:"summary,omitempty"`
	LastError           string                         `json:"last_error,omitempty"`
	UpdatedAt           string                         `json:"updated_at,omitempty"`
}

type ExecutionGraphAgentTask struct {
	TaskID   string `json:"task_id"`
	TaskType string `json:"task_type"`
	Status   string `json:"status"`
}

type ExecutionGraphRoute struct {
	Next      string `json:"next,omitempty"`
	OnFailure string `json:"on_failure,omitempty"`
	OnTimeout string `json:"on_timeout,omitempty"`
}

type ExecutionGraphEdge struct {
	Source   string `json:"source"`
	Target   string `json:"target"`
	Kind     string `json:"kind"`
	IsActive bool   `json:"is_active"`
	IsTaken  bool   `json:"is_taken"`
}
```

```go
package service

import (
	"context"

	"github.com/netxops/OneOps/app/orchestration/dto"
)

type IExecutionGraph interface {
	GetExecutionGraph(ctx context.Context, executionID string) (*dto.ExecutionGraphResp, error)
}
```

- [ ] **Step 4: Implement the minimal projection service**

```go
package impl

type ExecutionGraphSrv struct {
	DB          *gorm.DB
	Logger      *zap.Logger
	TemplateSrv orchestrationService.ITemplate
}

var ExecutionGraphSet = wire.NewSet(
	NewExecutionGraphSrv,
	wire.Bind(new(orchestrationService.IExecutionGraph), new(*ExecutionGraphSrv)),
)

func NewExecutionGraphSrv(db *gorm.DB, logger *zap.Logger, templateSrv orchestrationService.ITemplate) *ExecutionGraphSrv {
	if logger == nil {
		logger = zap.NewNop()
	}
	return &ExecutionGraphSrv{DB: db, Logger: logger, TemplateSrv: templateSrv}
}

func (s *ExecutionGraphSrv) GetExecutionGraph(ctx context.Context, executionID string) (*dto.ExecutionGraphResp, error) {
	var execution orchestrationModel.TemplateExecution
	if err := s.DB.WithContext(ctx).First(&execution, "id = ?", strings.TrimSpace(executionID)).Error; err != nil {
		return nil, err
	}

	_, bundle, err := s.TemplateSrv.GetLoadedTemplate(ctx, execution.TemplateCode, execution.Environment)
	if err != nil {
		return nil, err
	}
	process, err := compiler.CompileBundle(execution.TemplateCode, bundle)
	if err != nil {
		return nil, err
	}

	agentTaskByNode, err := s.loadAgentTaskMap(ctx, execution.ID)
	if err != nil {
		return nil, err
	}
	actionRequiredNodeIDs, err := s.loadActionRequiredNodeIDs(ctx, execution.ID)
	if err != nil {
		return nil, err
	}

	resp := &dto.ExecutionGraphResp{
		Execution: dto.ExecutionGraphExecution{
			ExecutionID:    execution.ID,
			TemplateCode:   execution.TemplateCode,
			Environment:    execution.Environment,
			Status:         execution.Status,
			CurrentNodeID:  execution.WaitingNodeID,
			WaitingNodeID:  execution.WaitingNodeID,
			WaitType:       execution.WaitType,
			ResumeToken:    execution.ResumeToken,
			ActionRequired: len(actionRequiredNodeIDs) > 0,
		},
		Nodes: s.buildExecutionGraphNodes(process, execution, agentTaskByNode, actionRequiredNodeIDs),
		Edges: s.buildExecutionGraphEdges(process, execution.WaitingNodeID),
	}
	return resp, nil
}

func (s *ExecutionGraphSrv) loadAgentTaskMap(ctx context.Context, executionID string) (map[string]orchestrationModel.AgentTask, error) {
	var rows []orchestrationModel.AgentTask
	if err := s.DB.WithContext(ctx).
		Order("updated_at asc").
		Find(&rows, "execution_id = ?", executionID).Error; err != nil {
		return nil, err
	}
	out := make(map[string]orchestrationModel.AgentTask, len(rows))
	for _, row := range rows {
		out[row.NodeID] = row
	}
	return out, nil
}

func (s *ExecutionGraphSrv) loadActionRequiredNodeIDs(ctx context.Context, executionID string) (map[string]struct{}, error) {
	var rows []orchestrationModel.ExecutionEvent
	if err := s.DB.WithContext(ctx).
		Where("execution_id = ? AND event_type = ?", executionID, "execution_action_required").
		Find(&rows).Error; err != nil {
		return nil, err
	}
	out := make(map[string]struct{}, len(rows))
	for _, row := range rows {
		if strings.TrimSpace(row.NodeID) != "" {
			out[row.NodeID] = struct{}{}
		}
	}
	return out, nil
}

func (s *ExecutionGraphSrv) buildExecutionGraphEdges(process *define.DAGProcess, waitingNodeID string) []dto.ExecutionGraphEdge {
	edges := make([]dto.ExecutionGraphEdge, 0, len(process.Nodes)*2)
	for _, node := range process.Nodes {
		if next := strings.TrimSpace(node.Next); next != "" {
			edges = append(edges, dto.ExecutionGraphEdge{
				Source:   node.Key,
				Target:   next,
				Kind:     "next",
				IsActive: waitingNodeID == next,
				IsTaken:  waitingNodeID == next,
			})
		}
	}
	return edges
}

func (s *ExecutionGraphSrv) buildExecutionGraphNodes(
	process *define.DAGProcess,
	execution orchestrationModel.TemplateExecution,
	agentTaskByNode map[string]orchestrationModel.AgentTask,
	actionRequiredNodeIDs map[string]struct{},
) []dto.ExecutionGraphNode {
	nodes := make([]dto.ExecutionGraphNode, 0, len(process.Nodes))
	for _, node := range process.Nodes {
		graphNode := dto.ExecutionGraphNode{
			NodeID:        node.Key,
			NodeName:      node.Key,
			NodeType:      node.Type,
			RuntimeStatus: "pending",
			IsCurrent:     execution.WaitingNodeID == node.Key,
			IsWaiting:     execution.WaitingNodeID == node.Key,
			WaitType:      "",
			Route: dto.ExecutionGraphRoute{
				Next:      strings.TrimSpace(node.Next),
				OnFailure: strings.TrimSpace(stringValue(node.Config["on_failure"])),
				OnTimeout: strings.TrimSpace(stringValue(node.Config["on_timeout"])),
			},
		}
		if graphNode.IsCurrent {
			graphNode.RuntimeStatus = "waiting"
			graphNode.ExecutionStatusHint = execution.Status
			graphNode.WaitType = execution.WaitType
		}
		if task, ok := agentTaskByNode[node.Key]; ok {
			graphNode.AgentTask = &dto.ExecutionGraphAgentTask{
				TaskID:   task.ID,
				TaskType: task.TaskType,
				Status:   task.Status,
			}
			graphNode.RuntimeStatus = normalizeGraphRuntimeStatus(task.Status, graphNode.RuntimeStatus)
			graphNode.LastError = task.LastError
			graphNode.UpdatedAt = formatExecutionTimestamp(task.UpdatedAt)
		}
		if _, ok := actionRequiredNodeIDs[node.Key]; ok {
			graphNode.IsActionRequired = true
		}
		nodes = append(nodes, graphNode)
	}
	return nodes
}

func normalizeGraphRuntimeStatus(taskStatus, fallback string) string {
	switch strings.TrimSpace(taskStatus) {
	case "completed":
		return "completed"
	case "failed", "dead":
		return "failed"
	case "running", "claimed", "callback_pending", "callback_retry":
		return "running"
	case "submitted":
		return "pending"
	default:
		return fallback
	}
}
```

- [ ] **Step 5: Run the backend projection tests to verify they pass**

Run: `cd /home/jacky/project/OneOPS-ALL/OneOps && go test ./app/orchestration/service/impl -run 'TestExecutionGraphService_GetExecutionGraphProjectsCurrentWaitState' -count=1`

Expected: PASS

- [ ] **Step 6: Commit the backend projection contract**

```bash
cd /home/jacky/project/OneOPS-ALL
git add OneOps/app/orchestration/dto/execution_graph.go \
  OneOps/app/orchestration/service/i_execution_graph.go \
  OneOps/app/orchestration/service/impl/execution_graph.go \
  OneOps/app/orchestration/service/impl/execution_graph_test.go
git commit -m "feat: add orchestration execution graph projection service"
```

## Task 2: Expose The Graph API And Wire It Into The Server

**Files:**
- Modify: `OneOps/app/orchestration/api/execution.go`
- Modify: `OneOps/app/orchestration/router/execution.go`
- Modify: `OneOps/boot/provider/service_groups.go`
- Modify: `OneOps/cmd/wire_gen.go`

- [ ] **Step 1: Write the failing API route test**

```go
func TestExecutionAPI_GetExecutionGraph(t *testing.T) {
	gin.SetMode(gin.TestMode)

	type stubExecutionGraphSrv struct{}
	func (stubExecutionGraphSrv) GetExecutionGraph(ctx context.Context, executionID string) (*dto.ExecutionGraphResp, error) {
		return &dto.ExecutionGraphResp{
			Execution: dto.ExecutionGraphExecution{
				ExecutionID: executionID,
				Status:      "waiting_approval",
			},
			Nodes: []dto.ExecutionGraphNode{
				{NodeID: "wait_approval", NodeType: "approval_wait_step", RuntimeStatus: "waiting", IsCurrent: true},
			},
			Edges: []dto.ExecutionGraphEdge{
				{Source: "recommend_dispatch", Target: "wait_approval", Kind: "next", IsActive: true, IsTaken: true},
			},
		}, nil
	}

	engine := gin.New()
	api := &ExecutionAPI{
		Logger:            zap.NewNop(),
		ExecutionGraphSrv: stubExecutionGraphSrv{},
	}
	engine.GET("/api/v1/orchestration/executions/:executionId/graph", api.GetExecutionGraph)

	req := httptest.NewRequest(http.MethodGet, "/api/v1/orchestration/executions/exec-api-1/graph", nil)
	recorder := httptest.NewRecorder()
	engine.ServeHTTP(recorder, req)

	if recorder.Code != http.StatusOK {
		t.Fatalf("status code = %d, want %d, body=%s", recorder.Code, http.StatusOK, recorder.Body.String())
	}
	if !strings.Contains(recorder.Body.String(), `"execution_id":"exec-api-1"`) {
		t.Fatalf("body = %s, want execution graph payload", recorder.Body.String())
	}
}
```

- [ ] **Step 2: Run the API route test to verify it fails**

Run: `cd /home/jacky/project/OneOPS-ALL/OneOps && go test ./app/orchestration/api -run 'TestExecutionAPI_GetExecutionGraph' -count=1`

Expected: FAIL with missing `ExecutionGraphSrv` field or missing `GetExecutionGraph` handler.

- [ ] **Step 3: Extend the API and route registration**

```go
type ExecutionAPI struct {
	Logger            *zap.Logger
	ExecutionSrv      orchestrationService.IExecution
	ExecutionGraphSrv orchestrationService.IExecutionGraph
}

func (a *ExecutionAPI) GetExecutionGraph(ctx *gin.Context) {
	resp, err := a.ExecutionGraphSrv.GetExecutionGraph(ctx, ctx.Param("executionId"))
	if err != nil {
		response.FailWithMsg(err.Error(), ctx)
		a.Logger.Error("orchestration execution graph failed", zap.Error(err))
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
	g.GET(":executionId/graph", api.GetExecutionGraph)
	g.GET(":executionId/events", api.ListExecutionEvents)
	g.GET(":executionId/agent-tasks", api.ListExecutionAgentTasks)
}
```

- [ ] **Step 4: Register the service set and regenerate wire**

```go
// OneOps/boot/provider/service_groups.go
orchestrationSrv.TemplateSet,
orchestrationSrv.CapabilityGatewaySet,
orchestrationSrv.DagengineAdapterSet,
orchestrationSrv.ExecutionSet,
orchestrationSrv.ExecutionGraphSet,
orchestrationSrv.ResumeSet,
```

Run: `cd /home/jacky/project/OneOPS-ALL/OneOps && go generate ./cmd`

Expected: `cmd/wire_gen.go` updates cleanly with no `undefined` provider errors.

- [ ] **Step 5: Run backend API and implementation tests**

Run: `cd /home/jacky/project/OneOPS-ALL/OneOps && go test ./app/orchestration/api ./app/orchestration/service/impl -count=1`

Expected: PASS

- [ ] **Step 6: Commit the graph endpoint wiring**

```bash
cd /home/jacky/project/OneOPS-ALL
git add OneOps/app/orchestration/api/execution.go \
  OneOps/app/orchestration/router/execution.go \
  OneOps/boot/provider/service_groups.go \
  OneOps/cmd/wire_gen.go
git commit -m "feat: expose orchestration execution graph api"
```

## Task 3: Build The Detail Page Skeleton And Navigation Flow

**Files:**
- Modify: `OneOPS-UI/src/typings/orchestration/execution.ts`
- Modify: `OneOPS-UI/src/api/orchestration/execution.ts`
- Create: `OneOPS-UI/src/views/platform/ExecutionDetailDebugger.vue`
- Modify: `OneOPS-UI/src/views/platform/ExecutionObservatory.vue`
- Modify: `OneOPS-UI/src/router/utils.ts`
- Create: `OneOPS-UI/scripts/execution-detail-debugger-smoke.ts`
- Modify: `OneOPS-UI/package.json`

- [ ] **Step 1: Write the failing UI smoke script**

```ts
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';

const root = process.cwd();
const routerSource = fs.readFileSync(path.join(root, 'src/router/utils.ts'), 'utf8');
const apiSource = fs.readFileSync(path.join(root, 'src/api/orchestration/execution.ts'), 'utf8');

assert.match(routerSource, /path:\s*'platform\/execution-observatory\/:executionId'/, 'detail route should be registered');
assert.match(routerSource, /name:\s*'ExecutionDetailDebugger'/, 'detail route name should be registered');
assert.match(apiSource, /export const getExecutionGraphReq = async/, 'graph api wrapper should be exported');
console.log('execution-detail-debugger smoke checks passed');
```

- [ ] **Step 2: Run the smoke script to verify it fails**

Run: `cd /home/jacky/project/OneOPS-ALL/OneOPS-UI && npm run smoke:execution-detail-debugger`

Expected: FAIL because the command or route wrapper does not exist yet.

- [ ] **Step 3: Add graph typings and API wrapper**

```ts
export interface ExecutionGraphResp {
  execution: ExecutionGraphExecution;
  nodes: ExecutionGraphNode[];
  edges: ExecutionGraphEdge[];
}

export interface ExecutionGraphExecution {
  execution_id: string;
  template_code: string;
  environment: string;
  status: string;
  current_node_id?: string;
  waiting_node_id?: string;
  wait_type?: string;
  resume_token?: string;
  action_required: boolean;
}

export interface ExecutionGraphNode {
  node_id: string;
  node_name: string;
  node_type: string;
  runtime_status: string;
  execution_status_hint?: string;
  is_current: boolean;
  is_waiting: boolean;
  is_action_required: boolean;
  wait_type?: string;
  summary?: string;
  last_error?: string;
  updated_at?: string;
  route: {
    next?: string;
    on_failure?: string;
    on_timeout?: string;
  };
  agent_task?: {
    task_id: string;
    task_type: string;
    status: string;
  };
}

export interface ExecutionGraphEdge {
  source: string;
  target: string;
  kind: 'next' | 'on_failure' | 'on_timeout';
  is_active: boolean;
  is_taken: boolean;
}
```

```ts
export const getExecutionGraphReq = async (executionID: string) => {
  return request<ExecutionGraphResp>({
    url: `/orchestration/executions/${encodeURIComponent(executionID)}/graph`,
    method: HTTP_GET,
  });
};
```

- [ ] **Step 4: Create the detail page shell and route**

```vue
<template>
  <div class="page-container execution-detail-debugger">
    <a-page-header :title="`Execution ${executionID}`" sub-title="单条执行运行态调试台" @back="goBack">
      <template #extra>
        <a-space>
          <a-button :loading="loading.detail || loading.graph || loading.events || loading.agentTasks" @click="reloadAll">
            刷新
          </a-button>
        </a-space>
      </template>
    </a-page-header>

    <a-alert
      class="mb-3"
      type="info"
      show-icon
      message="当前展示真实 orchestration execution 的运行态"
      description="此页面面向运维和值守调试，不是模板设计器。"
    />

    <a-row :gutter="16">
      <a-col :xs="24" :xl="16">
        <a-card title="Runtime Graph">
          <div class="graph-placeholder">Graph component will mount here</div>
        </a-card>
      </a-col>
      <a-col :xs="24" :xl="8">
        <a-card title="Execution State">
          <a-descriptions :column="1" bordered size="small">
            <a-descriptions-item label="Status">{{ execution?.status || '-' }}</a-descriptions-item>
            <a-descriptions-item label="Waiting Node">{{ execution?.waiting_node_id || '-' }}</a-descriptions-item>
            <a-descriptions-item label="Wait Type">{{ execution?.wait_type || '-' }}</a-descriptions-item>
          </a-descriptions>
        </a-card>
      </a-col>
    </a-row>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { getExecutionGraphReq, getExecutionReq, listExecutionAgentTasksReq, listExecutionEventsReq } from '@/api/orchestration/execution';
import type { ExecutionAgentTaskResp, ExecutionEventResp, ExecutionGraphResp, ExecutionResp } from '@/typings/orchestration/execution';

const route = useRoute();
const router = useRouter();
const executionID = computed(() => String(route.params.executionId || '').trim());
const execution = ref<ExecutionResp | null>(null);
const graph = ref<ExecutionGraphResp>({
  execution: {
    execution_id: '',
    template_code: '',
    environment: '',
    status: '',
    action_required: false,
  },
  nodes: [],
  edges: [],
});
const events = ref<ExecutionEventResp[]>([]);
const agentTasks = ref<ExecutionAgentTaskResp[]>([]);
const loading = reactive({
  detail: false,
  graph: false,
  events: false,
  agentTasks: false,
});

function goBack() {
  void router.push({ name: 'ExecutionObservatory' });
}

async function reloadAll() {
  if (!executionID.value) return;
  loading.detail = true;
  loading.graph = true;
  loading.events = true;
  loading.agentTasks = true;
  try {
    const [detailResp, graphResp, eventResp, agentTaskResp] = await Promise.all([
      getExecutionReq(executionID.value),
      getExecutionGraphReq(executionID.value),
      listExecutionEventsReq(executionID.value),
      listExecutionAgentTasksReq(executionID.value),
    ]);
    execution.value = detailResp;
    graph.value = graphResp;
    events.value = eventResp || [];
    agentTasks.value = agentTaskResp || [];
  } finally {
    loading.detail = false;
    loading.graph = false;
    loading.events = false;
    loading.agentTasks = false;
  }
}

onMounted(async () => {
  await reloadAll();
});
</script>
```

```ts
const executionDetailDebuggerRoute: RouteRecordRaw = {
  path: 'platform/execution-observatory/:executionId',
  name: 'ExecutionDetailDebugger',
  component: () => import('@/views/platform/ExecutionDetailDebugger.vue'),
  meta: {
    title: '编排执行详情调试台',
    requiresAuth: true,
    hideInMenu: true,
  },
};
```

- [ ] **Step 5: Change observatory row navigation to the detail page**

```ts
import { useRouter } from 'vue-router';

const router = useRouter();

async function openExecution(executionID: string) {
  await router.push({
    name: 'ExecutionDetailDebugger',
    params: { executionId: executionID },
  });
}
```

- [ ] **Step 6: Add the smoke command and run it**

```json
"smoke:execution-detail-debugger": "npx esbuild scripts/execution-detail-debugger-smoke.ts --bundle --platform=node --format=esm --outfile=.tmp/execution-detail-debugger-smoke.mjs >/dev/null && node .tmp/execution-detail-debugger-smoke.mjs"
```

Run: `cd /home/jacky/project/OneOPS-ALL/OneOPS-UI && npm run smoke:execution-detail-debugger`

Expected: PASS with `execution-detail-debugger smoke checks passed`.

- [ ] **Step 7: Commit the detail page skeleton**

```bash
cd /home/jacky/project/OneOPS-ALL
git add OneOPS-UI/src/typings/orchestration/execution.ts \
  OneOPS-UI/src/api/orchestration/execution.ts \
  OneOPS-UI/src/views/platform/ExecutionDetailDebugger.vue \
  OneOPS-UI/src/views/platform/ExecutionObservatory.vue \
  OneOPS-UI/src/router/utils.ts \
  OneOPS-UI/scripts/execution-detail-debugger-smoke.ts \
  OneOPS-UI/package.json
git commit -m "feat: add execution detail debugger page shell"
```

## Task 4: Render The Runtime Graph And Node Inspector

**Files:**
- Create: `OneOPS-UI/src/components/orchestration/ExecutionRuntimeGraph.vue`
- Create: `OneOPS-UI/src/components/orchestration/ExecutionNodeInspector.vue`
- Modify: `OneOPS-UI/src/views/platform/ExecutionDetailDebugger.vue`

- [ ] **Step 1: Write the failing graph component test via smoke assertions**

```ts
const pageSource = fs.readFileSync(path.join(root, 'src/views/platform/ExecutionDetailDebugger.vue'), 'utf8');
assert.match(pageSource, /ExecutionRuntimeGraph/, 'detail page should render the runtime graph component');
assert.match(pageSource, /ExecutionNodeInspector/, 'detail page should render the node inspector component');
```

- [ ] **Step 2: Run the smoke script to verify it fails**

Run: `cd /home/jacky/project/OneOPS-ALL/OneOPS-UI && npm run smoke:execution-detail-debugger`

Expected: FAIL because the new components are not mounted yet.

- [ ] **Step 3: Implement the read-only graph component**

```vue
<template>
  <div class="execution-runtime-graph">
    <div v-if="!graph.nodes.length" class="execution-runtime-graph__empty">暂无运行图数据</div>
    <div v-else class="execution-runtime-graph__grid">
      <button
        v-for="node in graph.nodes"
        :key="node.node_id"
        type="button"
        class="execution-runtime-node"
        :class="[
          `execution-runtime-node--${node.runtime_status || 'pending'}`,
          { 'is-current': node.is_current, 'is-waiting': node.is_waiting, 'is-action-required': node.is_action_required },
        ]"
        @click="$emit('select-node', node)"
      >
        <div class="execution-runtime-node__title">{{ node.node_id }}</div>
        <div class="execution-runtime-node__meta">{{ node.node_type }}</div>
        <div class="execution-runtime-node__status">{{ node.execution_status_hint || node.runtime_status }}</div>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { ExecutionGraphResp, ExecutionGraphNode } from '@/typings/orchestration/execution';

defineProps<{
  graph: ExecutionGraphResp;
}>();

defineEmits<{
  (e: 'select-node', node: ExecutionGraphNode): void;
}>();
</script>
```

- [ ] **Step 4: Implement the node inspector component**

```vue
<template>
  <a-card size="small" title="Node Inspector">
    <a-empty v-if="!node" description="点击运行图节点查看详情" />
    <a-descriptions v-else :column="1" bordered size="small">
      <a-descriptions-item label="Node ID">{{ node.node_id }}</a-descriptions-item>
      <a-descriptions-item label="Node Type">{{ node.node_type }}</a-descriptions-item>
      <a-descriptions-item label="Runtime Status">{{ node.runtime_status }}</a-descriptions-item>
      <a-descriptions-item label="Wait Type">{{ node.wait_type || '-' }}</a-descriptions-item>
      <a-descriptions-item label="Next">{{ node.route?.next || '-' }}</a-descriptions-item>
      <a-descriptions-item label="On Failure">{{ node.route?.on_failure || '-' }}</a-descriptions-item>
      <a-descriptions-item label="On Timeout">{{ node.route?.on_timeout || '-' }}</a-descriptions-item>
      <a-descriptions-item label="Summary">{{ node.summary || '-' }}</a-descriptions-item>
      <a-descriptions-item label="Last Error">{{ node.last_error || '-' }}</a-descriptions-item>
    </a-descriptions>
  </a-card>
</template>
```

- [ ] **Step 5: Mount graph and inspector in the detail page**

```vue
<ExecutionRuntimeGraph
  :graph="graph"
  @select-node="selectedNode = $event"
/>

<ExecutionNodeInspector :node="selectedNode" />
```

```ts
const graph = ref<ExecutionGraphResp>({
  execution: {
    execution_id: '',
    template_code: '',
    environment: '',
    status: '',
    action_required: false,
  },
  nodes: [],
  edges: [],
});
const selectedNode = ref<ExecutionGraphNode | null>(null);

async function loadGraph(executionID: string) {
  loading.graph = true;
  try {
    graph.value = await getExecutionGraphReq(executionID);
    selectedNode.value = graph.value.nodes.find(node => node.is_current) || graph.value.nodes[0] || null;
  } finally {
    loading.graph = false;
  }
}
```

- [ ] **Step 6: Run the smoke script and focused lint**

Run: `cd /home/jacky/project/OneOPS-ALL/OneOPS-UI && npm run smoke:execution-detail-debugger && npx eslint src/views/platform/ExecutionDetailDebugger.vue src/components/orchestration/ExecutionRuntimeGraph.vue src/components/orchestration/ExecutionNodeInspector.vue --ext .vue,.ts`

Expected: smoke PASS and eslint PASS.

- [ ] **Step 7: Commit the graph rendering layer**

```bash
cd /home/jacky/project/OneOPS-ALL
git add OneOPS-UI/src/components/orchestration/ExecutionRuntimeGraph.vue \
  OneOPS-UI/src/components/orchestration/ExecutionNodeInspector.vue \
  OneOPS-UI/src/views/platform/ExecutionDetailDebugger.vue
git commit -m "feat: render execution runtime graph and node inspector"
```

## Task 5: Add Ops And Debug Panels Plus Real-API Acceptance

**Files:**
- Create: `OneOPS-UI/src/components/orchestration/ExecutionOpsPanel.vue`
- Create: `OneOPS-UI/src/components/orchestration/ExecutionDebugPanel.vue`
- Modify: `OneOPS-UI/src/views/platform/ExecutionDetailDebugger.vue`
- Create: `OneOPS-UI/scripts/execution-detail-debugger-real-api-acceptance.ts`
- Modify: `OneOPS-UI/package.json`
- Modify: `docs/runbooks/alert-to-ticket-dagengine-mvp.md`

- [ ] **Step 1: Write the failing acceptance script**

```ts
const graph = await getJson<ExecutionGraphResp>(
  token,
  `/orchestration/executions/${encodeURIComponent(started.id)}/graph`,
  `get execution graph ${started.id}`,
);
assert.ok(graph.nodes.length > 0, 'graph should include nodes');
assert.ok(graph.edges.length > 0, 'graph should include edges');
assert.ok(graph.execution.status, 'graph execution status should be present');
assert.ok(
  graph.nodes.some(node => node.is_current || node.is_waiting),
  'graph should mark a current or waiting node',
);
```

- [ ] **Step 2: Run the acceptance script to verify it fails**

Run: `cd /home/jacky/project/OneOPS-ALL/OneOPS-UI && npm run acceptance:execution-detail-debugger-real-api`

Expected: FAIL because the command or graph API route does not exist yet.

- [ ] **Step 3: Implement the ops panel with real resume actions**

```vue
<template>
  <a-card size="small" title="Ops View">
    <a-alert
      :type="execution?.status === 'escalated' ? 'error' : execution?.wait_type ? 'warning' : 'info'"
      show-icon
      :message="headline"
      :description="description"
      class="mb-3"
    />

    <a-form v-if="showActions" layout="vertical">
      <template v-if="execution?.wait_type === 'approval'">
        <a-form-item label="处理人">
          <a-input v-model:value="operator" allow-clear placeholder="例如：ops_oncall" />
        </a-form-item>
        <a-form-item label="备注">
          <a-textarea v-model:value="comment" :rows="3" />
        </a-form-item>
        <a-space>
          <a-button type="primary" :loading="submitting" @click="$emit('approve', { operator, comment })">Approve</a-button>
          <a-button danger :loading="submitting" @click="$emit('reject', { operator, comment })">Reject</a-button>
        </a-space>
      </template>
      <template v-else-if="execution?.wait_type === 'callback'">
        <a-form-item label="Callback Payload JSON">
          <a-textarea v-model:value="callbackPayload" :rows="8" />
        </a-form-item>
        <a-button type="primary" :loading="submitting" @click="$emit('resume-callback', callbackPayload)">
          Resume Callback
        </a-button>
      </template>
    </a-form>
  </a-card>
</template>
```

- [ ] **Step 4: Implement the debug panel**

```vue
<template>
  <a-card size="small" title="Debug View">
    <a-tabs>
      <a-tab-pane key="agent" tab="Agent Tasks">
        <a-timeline>
          <a-timeline-item v-for="task in agentTasks" :key="task.id">
            <strong>{{ task.task_type }}</strong>
            <div>{{ task.status }} · {{ task.node_id }}</div>
            <pre v-if="task.last_error">{{ task.last_error }}</pre>
            <pre v-if="task.result_payload_json">{{ formatPayload(task.result_payload_json) }}</pre>
          </a-timeline-item>
        </a-timeline>
      </a-tab-pane>
      <a-tab-pane key="events" tab="Events">
        <a-timeline>
          <a-timeline-item v-for="event in events" :key="event.id">
            <strong>{{ event.event_type }}</strong>
            <div>{{ event.node_id || '-' }} · {{ event.occurred_at }}</div>
            <pre>{{ formatPayload(event.payload_json) }}</pre>
          </a-timeline-item>
        </a-timeline>
      </a-tab-pane>
    </a-tabs>
  </a-card>
</template>

<script setup lang="ts">
import type { ExecutionAgentTaskResp, ExecutionEventResp } from '@/typings/orchestration/execution';

defineProps<{
  agentTasks: ExecutionAgentTaskResp[];
  events: ExecutionEventResp[];
}>();

function formatPayload(payloadJSON?: string) {
  if (!payloadJSON) return '{}';
  try {
    return JSON.stringify(JSON.parse(payloadJSON), null, 2);
  } catch {
    return payloadJSON;
  }
}
</script>
```

- [ ] **Step 5: Mount the panels and hook real actions**

```ts
async function handleApprove(payload: { operator?: string; comment?: string }) {
  if (!execution.value?.resume_token) {
    message.error('当前 execution 没有 resume token');
    return;
  }
  await approveExecutionReq({
    resume_token: execution.value.resume_token,
    decision: 'approve',
    operator: payload.operator || undefined,
    comment: payload.comment || undefined,
  });
  await reloadAll();
}

async function handleReject(payload: { operator?: string; comment?: string }) {
  if (!execution.value?.resume_token) {
    message.error('当前 execution 没有 resume token');
    return;
  }
  await rejectExecutionReq({
    resume_token: execution.value.resume_token,
    decision: 'reject',
    operator: payload.operator || undefined,
    comment: payload.comment || undefined,
  });
  await reloadAll();
}

async function handleResumeCallback(callbackPayloadJSON: string) {
  const parsed = JSON.parse(callbackPayloadJSON || '{}');
  await resumeExecutionCallbackReq({
    resume_token: execution.value?.resume_token || '',
    payload: parsed,
  });
  await reloadAll();
}
```

- [ ] **Step 6: Add the real-API acceptance command and script**

```json
"acceptance:execution-detail-debugger-real-api": "npx esbuild scripts/execution-detail-debugger-real-api-acceptance.ts --bundle --platform=node --format=esm --outfile=.tmp/execution-detail-debugger-real-api-acceptance.mjs >/dev/null && node .tmp/execution-detail-debugger-real-api-acceptance.mjs"
```

The acceptance script should:

- resolve token using the same login fallback pattern as `execution-observatory-real-api-acceptance.ts`
- import or refresh the template
- create a real execution
- poll until the execution is settled or waiting
- call `GET /orchestration/executions/:id/graph`
- assert graph nodes, edges, and current or waiting node flags
- print `/#/platform/execution-observatory/<executionId>`
- write evidence under `docs/openclaw-autodev/evidence/orchestration/execution-detail-debugger-real-api`

- [ ] **Step 7: Update the runbook and run full verification**

Update `docs/runbooks/alert-to-ticket-dagengine-mvp.md` with:

- the new detail page route
- how to navigate from observatory list into execution detail debugger
- how to run the new acceptance command

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
go test ./app/orchestration/api ./app/orchestration/service/impl ./cmd -count=1

cd /home/jacky/project/OneOPS-ALL/OneOPS-UI
npm run smoke:execution-detail-debugger
npm run acceptance:execution-detail-debugger-real-api
```

Expected:

- Go tests PASS
- smoke PASS
- acceptance PASS and prints a real execution detail debugger URL

- [ ] **Step 8: Commit the debugger panels and validation flow**

```bash
cd /home/jacky/project/OneOPS-ALL
git add OneOPS-UI/src/components/orchestration/ExecutionOpsPanel.vue \
  OneOPS-UI/src/components/orchestration/ExecutionDebugPanel.vue \
  OneOPS-UI/src/views/platform/ExecutionDetailDebugger.vue \
  OneOPS-UI/scripts/execution-detail-debugger-real-api-acceptance.ts \
  OneOPS-UI/package.json \
  docs/runbooks/alert-to-ticket-dagengine-mvp.md
git commit -m "feat: add orchestration execution detail debugger"
```

## Self-Review

Spec coverage check:

- dedicated execution detail page: covered by Tasks 3-5
- graph projection API: covered by Tasks 1-2
- dual ops/debug view: covered by Task 5
- real approve/reject/callback actions: covered by Task 5
- reuse of existing observatory entry: covered by Task 3

Placeholder scan:

- no `TODO`, `TBD`, or deferred-code placeholders are intentionally left in the plan steps
- every test, route, component, and command referenced above has an explicit file target

Type consistency check:

- graph API name is consistently `GetExecutionGraph` / `getExecutionGraphReq`
- dedicated page route is consistently `ExecutionDetailDebugger`
- DTO names consistently use `ExecutionGraph*`

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-06-28-oneops-orchestration-execution-detail-debugger-plan.md`. Two execution options:

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?
