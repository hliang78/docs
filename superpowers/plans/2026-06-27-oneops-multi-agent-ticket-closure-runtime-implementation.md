# OneOps Multi-Agent Ticket Closure Runtime Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first real OneOps multi-agent ticket-closure loop with asynchronous agent task submission, persistent callback/resume flow, human approval, execution tracking, knowledge drafting, and observability.

**Architecture:** OneOps remains the execution, approval, persistence, and observability owner. A separate `agentruntime` binary inside the same Go module receives submitted agent tasks, runs fixed role handlers, and calls back into OneOps using persisted resume tokens. The workflow remains dagengine-backed and uses `agent_step -> callback_wait_step -> approval_wait_step` rather than inventing a second orchestration kernel.

**Tech Stack:** Go, GORM, Gin, dagengine v2, existing OneOps orchestration runtime, Vue 3, Ant Design Vue, esbuild-based smoke and acceptance scripts.

---

## File Structure

### OneOps backend

- Create: `OneOps/app/orchestration/orchestration_model/agent_task.go`
  - Persist OneOps-owned agent task submission and latest callback result state.
- Create: `OneOps/app/orchestration/dto/agent_task.go`
  - Define backend response DTOs and internal submit payload shapes for agent-task observability.
- Create: `OneOps/app/orchestration/service/impl/agent_runtime_client.go`
  - Submit asynchronous tasks from OneOps to the separate agent runtime service.
- Create: `OneOps/app/orchestration/service/impl/agent_task_gateway.go`
  - Implement `runtime.AgentStepExecutor` with persistent task creation and callback token propagation.
- Modify: `OneOps/app/orchestration/runtime/callback_wait_step.go`
  - Reuse a pre-generated resume token from context instead of always generating a new UUID.
- Modify: `OneOps/app/orchestration/runtime/agent_step.go`
  - Keep `agent_step` asynchronous by returning a context patch with agent task metadata.
- Modify: `OneOps/app/orchestration/compiler/dagengine_compiler.go`
  - Emit agent node config and callback token propagation config into compiled nodes.
- Modify: `OneOps/app/orchestration/template/define.go`
  - Add explicit workflow fields for agent callback token propagation.
- Modify: `OneOps/app/orchestration/service/impl/dagengine_adapter.go`
  - Register `AgentTaskGateway` instead of using the generic capability gateway for agent submission.
- Modify: `OneOps/app/orchestration/service/i_execution.go`
  - Add an execution-agent-task listing method for observability.
- Modify: `OneOps/app/orchestration/service/impl/execution.go`
  - Query agent tasks alongside execution state and expose per-execution task history.
- Modify: `OneOps/app/orchestration/api/execution.go`
  - Add `GET /orchestration/executions/:executionId/agent-tasks`.
- Modify: `OneOps/app/orchestration/router/execution.go`
  - Register the agent-task endpoint.
- Modify: `OneOps/cmd/wire.go`
  - Wire `AgentTaskGateway` and `AgentRuntimeClient` into `DagengineAdapter`; regenerate `cmd/wire_gen.go`.

### Agent runtime service

- Create: `OneOps/cmd/agentruntime/main.go`
  - Start the separate agent runtime HTTP service.
- Create: `OneOps/app/agentruntime/dto/task.go`
  - Define submit-task and callback payload contracts.
- Create: `OneOps/app/agentruntime/service/runtime.go`
  - Route submitted tasks to fixed role handlers asynchronously.
- Create: `OneOps/app/agentruntime/service/callback_client.go`
  - Post structured results back to OneOps resume APIs.
- Create: `OneOps/app/agentruntime/service/roles.go`
  - Register role handlers.
- Create: `OneOps/app/agentruntime/service/role_analysis.go`
- Create: `OneOps/app/agentruntime/service/role_dispatch.go`
- Create: `OneOps/app/agentruntime/service/role_tracking.go`
- Create: `OneOps/app/agentruntime/service/role_knowledge.go`
  - Implement fixed-role agent logic with an injectable LLM/tool abstraction.
- Create: `OneOps/app/agentruntime/api/task.go`
  - Expose the submit-task endpoint used by OneOps.

### Frontend observability

- Modify: `OneOPS-UI/src/typings/orchestration/execution.ts`
  - Add execution-agent-task response types.
- Modify: `OneOPS-UI/src/api/orchestration/execution.ts`
  - Add `listExecutionAgentTasksReq`.
- Modify: `OneOPS-UI/src/views/platform/ExecutionObservatory.vue`
  - Show agent task history, role, status, and latest result summary in the drawer.
- Modify: `OneOPS-UI/scripts/execution-observatory-smoke.ts`
  - Assert that the new API and drawer panel are present.

### Real acceptance and docs

- Create: `OneOPS-UI/scripts/multi-agent-ticket-closure-real-api-acceptance.ts`
  - Seed a real multi-agent workflow, drive approval, and verify tracking/knowledge outputs.
- Modify: `OneOPS-UI/package.json`
  - Add the new acceptance command.
- Modify: `docs/runbooks/alert-to-ticket-dagengine-mvp.md`
  - Add real multi-agent runtime startup and validation steps.

---

### Task 1: Compile-Time Agent Contract And Callback Token Propagation

**Files:**
- Modify: `OneOps/app/orchestration/template/define.go`
- Modify: `OneOps/app/orchestration/compiler/dagengine_compiler.go`
- Modify: `OneOps/app/orchestration/compiler/dagengine_compiler_test.go`
- Modify: `OneOps/app/orchestration/runtime/callback_wait_step.go`
- Modify: `OneOps/app/orchestration/runtime/callback_wait_step_test.go`

- [ ] **Step 1: Write the failing tests**

Add compiler and runtime coverage for the async agent contract:

```go
func TestCompileBundleIncludesAgentResumeTokenContextKey(t *testing.T) {
	process, err := CompileBundle("multi-agent-template", &template.Bundle{
		Workflow: template.Workflow{
			Steps: []template.WorkflowStep{
				{
					Key:                  "analysis_submit",
					Type:                 "agent_step",
					Action:               "analyze_alert",
					AgentCatalogName:     "closure_agents",
					AllowedTools:         []string{"ticketing_api", "wecom"},
					Next:                 "analysis_wait",
					OnFailure:            "failed",
					ResumeTokenContextKey: "analysis_resume_token",
				},
				{
					Key:                  "analysis_wait",
					Type:                 "callback_wait_step",
					Action:               "wait_for_analysis",
					CallbackRef:          "agent_runtime_callback",
					ResumePolicy:         "merge_context",
					ResumeTokenContextKey: "analysis_resume_token",
					Next:                 "completed",
				},
			},
		},
	})
	if err != nil {
		t.Fatalf("CompileBundle error: %v", err)
	}
	if got := process.NodeConfigs["analysis_submit"]["resume_token_context_key"]; got != "analysis_resume_token" {
		t.Fatalf("resume token context key = %#v, want %q", got, "analysis_resume_token")
	}
	if got := process.NodeConfigs["analysis_wait"]["resume_token_context_key"]; got != "analysis_resume_token" {
		t.Fatalf("wait node token context key = %#v, want %q", got, "analysis_resume_token")
	}
}

func TestCallbackWaitStepUsesProvidedResumeToken(t *testing.T) {
	runtime := NewCallbackWaitStepRuntime()
	result, err := runtime.Run(context.Background(), NodeExecutionInput{
		ExecutionID: "exec-1",
		NodeID:      "analysis_wait",
		NodeType:    "callback_wait_step",
		Context: map[string]interface{}{
			"analysis_resume_token": "resume-analysis-1",
		},
		NodeConfig: map[string]interface{}{
			"action":                   "wait_for_analysis",
			"callback_ref":             "agent_runtime_callback",
			"resume_policy":            "merge_context",
			"resume_token_context_key": "analysis_resume_token",
		},
	})
	if err != nil {
		t.Fatalf("Run error: %v", err)
	}
	if got := result.SuspendInstruction.ResumeToken; got != "resume-analysis-1" {
		t.Fatalf("resume token = %q, want %q", got, "resume-analysis-1")
	}
}
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
go test ./app/orchestration/compiler ./app/orchestration/runtime -run 'TestCompileBundleIncludesAgentResumeTokenContextKey|TestCallbackWaitStepUsesProvidedResumeToken' -count=1
```

Expected:

- compiler test fails because `ResumeTokenContextKey` does not exist on `WorkflowStep`
- callback wait test fails because `callback_wait_step` always generates a new UUID

- [ ] **Step 3: Write minimal implementation**

Add the field to workflow definitions and compile it into node configs:

```go
type WorkflowStep struct {
	Key                   string   `yaml:"key"`
	Type                  string   `yaml:"type"`
	Action                string   `yaml:"action"`
	Next                  string   `yaml:"next"`
	OnFailure             string   `yaml:"on_failure"`
	AgentCatalogName      string   `yaml:"agent_catalog_name,omitempty"`
	AllowedTools          []string `yaml:"allowed_tools,omitempty"`
	TargetRef             string   `yaml:"target_ref,omitempty"`
	RequestTemplateRef    string   `yaml:"request_template_ref,omitempty"`
	CallbackRef           string   `yaml:"callback_ref,omitempty"`
	ResumePolicy          string   `yaml:"resume_policy,omitempty"`
	ResumeTokenContextKey string   `yaml:"resume_token_context_key,omitempty"`
	ApprovalPolicyRef     string   `yaml:"approval_policy_ref,omitempty"`
	TimeoutSeconds        int      `yaml:"timeout_seconds,omitempty"`
	OnTimeout             string   `yaml:"on_timeout,omitempty"`
}
```

```go
if value := strings.TrimSpace(step.ResumeTokenContextKey); value != "" {
	config["resume_token_context_key"] = value
}
```

Then reuse an existing token in the callback wait runtime:

```go
resumeToken := ""
if key, ok := readStringConfig(input.NodeConfig, "resume_token_context_key"); ok {
	if raw, exists := input.Context[key]; exists {
		if token, ok := raw.(string); ok && strings.TrimSpace(token) != "" {
			resumeToken = strings.TrimSpace(token)
		}
	}
}
if resumeToken == "" {
	resumeToken = uuid.NewString()
}

return NodeExecutionResult{
	Status: "waiting_callback",
	SuspendInstruction: &SuspendInstruction{
		WaitType:    "callback",
		ResumeToken: resumeToken,
		Details:     details,
	},
}, nil
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
go test ./app/orchestration/compiler ./app/orchestration/runtime -run 'TestCompileBundleIncludesAgentResumeTokenContextKey|TestCallbackWaitStepUsesProvidedResumeToken' -count=1
```

Expected:

- both tests pass

- [ ] **Step 5: Commit**

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
git add app/orchestration/template/define.go \
  app/orchestration/compiler/dagengine_compiler.go \
  app/orchestration/compiler/dagengine_compiler_test.go \
  app/orchestration/runtime/callback_wait_step.go \
  app/orchestration/runtime/callback_wait_step_test.go
git commit -m "feat: add agent callback token propagation"
```

### Task 2: Persist Agent Tasks And Submit Them From `agent_step`

**Files:**
- Create: `OneOps/app/orchestration/orchestration_model/agent_task.go`
- Create: `OneOps/app/orchestration/dto/agent_task.go`
- Create: `OneOps/app/orchestration/service/impl/agent_runtime_client.go`
- Create: `OneOps/app/orchestration/service/impl/agent_task_gateway.go`
- Modify: `OneOps/app/orchestration/runtime/agent_step.go`
- Modify: `OneOps/app/orchestration/service/impl/dagengine_adapter.go`
- Modify: `OneOps/cmd/wire.go`
- Test: `OneOps/app/orchestration/service/impl/agent_task_gateway_test.go`

- [ ] **Step 1: Write the failing tests**

Create a new service test that proves `agent_step` now persists and submits asynchronous work:

```go
func TestAgentTaskGatewaySubmitsTaskAndReturnsContextPatch(t *testing.T) {
	db := newOrchestrationTestDB(t)
	client := &fakeAgentRuntimeClient{}
	gateway := NewAgentTaskGateway(db, zap.NewNop(), client)

	patch, err := gateway.ExecuteAgentStep(context.Background(), runtime.AgentStepRequest{
		NodeID:           "analysis_submit",
		Action:           "analyze_alert",
		AgentCatalogName: "closure_agents",
		AllowedTools:     []string{"ticketing_api", "wecom"},
		Context: map[string]interface{}{
			"execution_id": "exec-agent-1",
			"ticket_id":    "ticket-1",
			"alert_code":   "ALERT-1",
		},
	})
	if err != nil {
		t.Fatalf("ExecuteAgentStep error: %v", err)
	}

	if patch["analysis_resume_token"] == "" {
		t.Fatal("analysis_resume_token = empty, want generated token")
	}
	if patch["agent_task_id"] == "" {
		t.Fatal("agent_task_id = empty, want persisted id")
	}

	var row orchestrationModel.AgentTask
	if err := db.First(&row, "id = ?", patch["agent_task_id"]).Error; err != nil {
		t.Fatalf("query agent task failed: %v", err)
	}
	if row.Status != "submitted" {
		t.Fatalf("status = %q, want %q", row.Status, "submitted")
	}
	if client.lastReq.ResumeToken == "" {
		t.Fatal("submit request resume token = empty, want propagated token")
	}
}
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
go test ./app/orchestration/service/impl -run 'TestAgentTaskGatewaySubmitsTaskAndReturnsContextPatch' -count=1
```

Expected:

- build fails because `AgentTask`, `AgentTaskGateway`, and `AgentRuntimeClient` do not exist

- [ ] **Step 3: Write minimal implementation**

Create the OneOps-owned persistence model:

```go
type AgentTask struct {
	ID                 string    `gorm:"column:id;primaryKey"`
	ExecutionID        string    `gorm:"column:execution_id;size:64;index"`
	NodeID             string    `gorm:"column:node_id;size:128;index"`
	TaskType           string    `gorm:"column:task_type;size:64"`
	AgentCatalogName   string    `gorm:"column:agent_catalog_name;size:128"`
	Status             string    `gorm:"column:status;size:32;index"`
	ResumeToken        string    `gorm:"column:resume_token;size:128;uniqueIndex"`
	AllowedToolsJSON   string    `gorm:"column:allowed_tools_json;type:text"`
	InputPayloadJSON   string    `gorm:"column:input_payload_json;type:text"`
	ResultPayloadJSON  string    `gorm:"column:result_payload_json;type:text"`
	LastError          string    `gorm:"column:last_error;size:255"`
	LastCallbackAt     *time.Time `gorm:"column:last_callback_at"`
	CreatedAt          time.Time `gorm:"column:created_at"`
	UpdatedAt          time.Time `gorm:"column:updated_at"`
}

func (*AgentTask) TableName() string { return "orchestration_agent_tasks" }
```

Create the submit client contract and gateway:

```go
type AgentRuntimeSubmitReq struct {
	TaskID           string                 `json:"task_id"`
	ExecutionID      string                 `json:"execution_id"`
	NodeID           string                 `json:"node_id"`
	TaskType         string                 `json:"task_type"`
	AgentCatalogName string                 `json:"agent_catalog_name"`
	AllowedTools     []string               `json:"allowed_tools"`
	ResumeToken      string                 `json:"resume_token"`
	InputContext     map[string]interface{} `json:"input_context"`
}

type AgentRuntimeClient interface {
	SubmitTask(context.Context, AgentRuntimeSubmitReq) error
}
```

```go
func (g *AgentTaskGateway) ExecuteAgentStep(ctx context.Context, req runtime.AgentStepRequest) (map[string]interface{}, error) {
	resumeToken := uuid.NewString()
	taskID := uuid.NewString()

	row := &orchestrationModel.AgentTask{
		ID:               taskID,
		ExecutionID:      stringValue(req.Context["execution_id"]),
		NodeID:           req.NodeID,
		TaskType:         req.Action,
		AgentCatalogName: req.AgentCatalogName,
		Status:           "submitted",
		ResumeToken:      resumeToken,
		AllowedToolsJSON: mustJSON(req.AllowedTools),
		InputPayloadJSON: mustJSON(req.Context),
	}
	if err := g.DB.WithContext(ctx).Create(row).Error; err != nil {
		return nil, err
	}

	submitReq := dto.AgentRuntimeSubmitReq{
		TaskID:           taskID,
		ExecutionID:      row.ExecutionID,
		NodeID:           req.NodeID,
		TaskType:         req.Action,
		AgentCatalogName: req.AgentCatalogName,
		AllowedTools:     append([]string(nil), req.AllowedTools...),
		ResumeToken:      resumeToken,
		InputContext:     cloneMap(req.Context),
	}
	if err := g.Client.SubmitTask(ctx, submitReq); err != nil {
		_ = g.DB.WithContext(ctx).Model(row).Updates(map[string]interface{}{
			"status":     "failed",
			"last_error": truncateForExecutionLog(err.Error(), 255),
		}).Error
		return nil, err
	}

	return map[string]interface{}{
		"agent_task_id":         taskID,
		"agent_task_status":     "submitted",
		"agent_task_type":       req.Action,
		"analysis_resume_token": resumeToken,
	}, nil
}
```

Update `DagengineAdapter` registration:

```go
adapter.Registry.Register("flow_step", orchestrationRuntime.NewFlowStepRuntime(a.Gateway))
adapter.Registry.Register("agent_step", orchestrationRuntime.NewAgentStepRuntime(a.AgentTaskGateway))
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
go test ./app/orchestration/service/impl -run 'TestAgentTaskGatewaySubmitsTaskAndReturnsContextPatch' -count=1
go generate ./cmd
```

Expected:

- gateway test passes
- `go generate ./cmd` completes and refreshes `cmd/wire_gen.go`

- [ ] **Step 5: Commit**

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
git add app/orchestration/orchestration_model/agent_task.go \
  app/orchestration/dto/agent_task.go \
  app/orchestration/service/impl/agent_runtime_client.go \
  app/orchestration/service/impl/agent_task_gateway.go \
  app/orchestration/service/impl/agent_task_gateway_test.go \
  app/orchestration/runtime/agent_step.go \
  app/orchestration/service/impl/dagengine_adapter.go \
  cmd/wire.go cmd/wire_gen.go
git commit -m "feat: persist and submit orchestration agent tasks"
```

### Task 3: Build The Separate `agentruntime` Service And Role Handlers

**Files:**
- Create: `OneOps/cmd/agentruntime/main.go`
- Create: `OneOps/app/agentruntime/dto/task.go`
- Create: `OneOps/app/agentruntime/api/task.go`
- Create: `OneOps/app/agentruntime/service/runtime.go`
- Create: `OneOps/app/agentruntime/service/callback_client.go`
- Create: `OneOps/app/agentruntime/service/roles.go`
- Create: `OneOps/app/agentruntime/service/role_analysis.go`
- Create: `OneOps/app/agentruntime/service/role_dispatch.go`
- Create: `OneOps/app/agentruntime/service/role_tracking.go`
- Create: `OneOps/app/agentruntime/service/role_knowledge.go`
- Test: `OneOps/app/agentruntime/service/runtime_test.go`
- Test: `OneOps/app/agentruntime/api/task_test.go`

- [ ] **Step 1: Write the failing tests**

Create a runtime test proving the service runs asynchronously and calls back with structured results:

```go
func TestRuntimeDispatchesAnalysisTaskAndPostsCallback(t *testing.T) {
	callbacks := &fakeCallbackClient{}
	runtime := NewRuntime(zap.NewNop(), callbacks, fakeRoleRegistry{
		"analyze_alert": fakeRoleHandler{
			result: RoleResult{
				Status:     "succeeded",
				ResultType: "analysis",
				ResultPayload: map[string]interface{}{
					"summary": "probable interface flap",
					"impact":  "single-site",
				},
			},
		},
	})

	err := runtime.Submit(context.Background(), dto.AgentRuntimeSubmitReq{
		TaskID:      "task-1",
		ExecutionID: "exec-1",
		NodeID:      "analysis_submit",
		TaskType:    "analyze_alert",
		ResumeToken: "resume-1",
		InputContext: map[string]interface{}{
			"alert_code": "ALERT-1",
		},
	})
	if err != nil {
		t.Fatalf("Submit error: %v", err)
	}

	requireEventually(t, time.Second, func() bool {
		return callbacks.called
	})
	if callbacks.lastReq.ResumeToken != "resume-1" {
		t.Fatalf("resume token = %q, want %q", callbacks.lastReq.ResumeToken, "resume-1")
	}
	if callbacks.lastReq.Payload["agent_result_type"] != "analysis" {
		t.Fatalf("agent_result_type = %#v, want %q", callbacks.lastReq.Payload["agent_result_type"], "analysis")
	}
}
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
go test ./app/agentruntime/... -count=1
```

Expected:

- build fails because the `app/agentruntime` package tree does not exist

- [ ] **Step 3: Write minimal implementation**

Define the submit and callback contracts:

```go
type AgentRuntimeSubmitReq struct {
	TaskID           string                 `json:"task_id"`
	ExecutionID      string                 `json:"execution_id"`
	NodeID           string                 `json:"node_id"`
	TaskType         string                 `json:"task_type"`
	AgentCatalogName string                 `json:"agent_catalog_name"`
	AllowedTools     []string               `json:"allowed_tools"`
	ResumeToken      string                 `json:"resume_token"`
	InputContext     map[string]interface{} `json:"input_context"`
}

type CallbackResumeReq struct {
	ResumeToken string                 `json:"resume_token"`
	Payload     map[string]interface{} `json:"payload"`
}
```

Implement fixed-role runtime dispatch:

```go
func (r *Runtime) Submit(ctx context.Context, req dto.AgentRuntimeSubmitReq) error {
	handler, ok := r.roles[req.TaskType]
	if !ok {
		return fmt.Errorf("unsupported task type %q", req.TaskType)
	}

	go func() {
		result := handler.Run(context.Background(), RoleRequest{
			TaskID:       req.TaskID,
			ExecutionID:  req.ExecutionID,
			TaskType:     req.TaskType,
			AllowedTools: append([]string(nil), req.AllowedTools...),
			Context:      cloneMap(req.InputContext),
		})
		payload := map[string]interface{}{
			"agent_task_id":      req.TaskID,
			"agent_task_status":  result.Status,
			"agent_result_type":  result.ResultType,
			"agent_result":       result.ResultPayload,
			"operator_required":  result.OperatorActionRequired,
			"agent_next_hint":    result.NextHint,
		}
		_ = r.callbackClient.Resume(context.Background(), dto.CallbackResumeReq{
			ResumeToken: req.ResumeToken,
			Payload:     payload,
		})
	}()

	return nil
}
```

Implement the role registry:

```go
func NewDefaultRoles(llm LLMClient) map[string]RoleHandler {
	return map[string]RoleHandler{
		"analyze_alert":       NewAnalysisRole(llm),
		"recommend_dispatch":  NewDispatchRole(llm),
		"track_execution":     NewTrackingRole(llm),
		"draft_knowledge":     NewKnowledgeRole(llm),
	}
}
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
go test ./app/agentruntime/... -count=1
go test ./cmd/agentruntime/... -count=1
```

Expected:

- agentruntime service and API tests pass

- [ ] **Step 5: Commit**

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
git add cmd/agentruntime/main.go \
  app/agentruntime/dto/task.go \
  app/agentruntime/api/task.go \
  app/agentruntime/api/task_test.go \
  app/agentruntime/service/runtime.go \
  app/agentruntime/service/runtime_test.go \
  app/agentruntime/service/callback_client.go \
  app/agentruntime/service/roles.go \
  app/agentruntime/service/role_analysis.go \
  app/agentruntime/service/role_dispatch.go \
  app/agentruntime/service/role_tracking.go \
  app/agentruntime/service/role_knowledge.go
git commit -m "feat: add separate multi-agent runtime service"
```

### Task 4: Wire The Analysis And Dispatch Loop Through Approval

**Files:**
- Create: `OneOps/app/orchestration/template/testdata/multi_agent_ticket_closure/manifest.yaml`
- Create: `OneOps/app/orchestration/template/testdata/multi_agent_ticket_closure/workflow.yaml`
- Create: `OneOps/app/orchestration/template/testdata/multi_agent_ticket_closure/agents.yaml`
- Modify: `OneOps/app/orchestration/service/impl/execution_test.go`
- Modify: `OneOps/app/orchestration/service/impl/resume_test.go`

- [ ] **Step 1: Write the failing tests**

Add a backend loop test that proves the workflow reaches approval only after analysis and dispatch callbacks arrive:

```go
func TestMultiAgentClosureAnalysisDispatchApprovalLoop(t *testing.T) {
	db := newOrchestrationTestDB(t)
	logger := zap.NewNop()
	templateRoot := filepath.Join("..", "..", "template", "testdata", "multi_agent_ticket_closure")
	templateSrv := newTemplateSrvWithImportedBundle(t, db, logger, "multi-agent-closure", templateRoot)
	runtimeServer := newFakeAgentRuntimeServer(t,
		fakeAgentTaskResult("analyze_alert", map[string]interface{}{"summary": "uplink flap"}),
		fakeAgentTaskResult("recommend_dispatch", map[string]interface{}{"assignee": "noc-l2"}),
	)

	execSrv := NewExecutionSrv(db, logger, templateSrv, newTestAdapterWithRuntimeURL(t, runtimeServer.URL))
	startResp, err := execSrv.StartExecution(context.Background(), dto.StartExecutionReq{
		TemplateCode: "multi-agent-closure",
		Environment:  "prod",
		Context: map[string]interface{}{
			"alert_code":  "ALERT-MA-1",
			"ticket_code": "TICKET-MA-1",
		},
	})
	if err != nil {
		t.Fatalf("StartExecution error: %v", err)
	}
	if startResp.Status != "waiting_approval" {
		t.Fatalf("status = %q, want %q", startResp.Status, "waiting_approval")
	}
	if startResp.WaitType != "approval" {
		t.Fatalf("wait type = %q, want %q", startResp.WaitType, "approval")
	}
}
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
go test ./app/orchestration/service/impl -run 'TestMultiAgentClosureAnalysisDispatchApprovalLoop' -count=1
```

Expected:

- fails because the multi-agent template bundle does not exist
- or fails because submitted agent callbacks do not advance execution into `waiting_approval`

- [ ] **Step 3: Write minimal implementation**

Create the first production-shaped bundle:

```yaml
steps:
  - key: create_primary_ticket
    type: flow_step
    action: create_primary_ticket
    next: analysis_submit
    on_failure: failed
  - key: analysis_submit
    type: agent_step
    action: analyze_alert
    agent_catalog_name: closure_agents
    allowed_tools:
      - topology_api
      - ticketing_api
    resume_token_context_key: analysis_resume_token
    next: analysis_wait
    on_failure: failed
  - key: analysis_wait
    type: callback_wait_step
    action: wait_for_analysis
    callback_ref: agent_runtime_callback
    resume_policy: merge_context
    resume_token_context_key: analysis_resume_token
    next: dispatch_submit
    on_failure: failed
  - key: dispatch_submit
    type: agent_step
    action: recommend_dispatch
    agent_catalog_name: closure_agents
    allowed_tools:
      - schedule_api
      - wecom
    resume_token_context_key: dispatch_resume_token
    next: dispatch_wait
    on_failure: failed
  - key: dispatch_wait
    type: callback_wait_step
    action: wait_for_dispatch
    callback_ref: agent_runtime_callback
    resume_policy: merge_context
    resume_token_context_key: dispatch_resume_token
    next: wait_execution_approval
    on_failure: failed
  - key: wait_execution_approval
    type: approval_wait_step
    action: wait_for_execution_approval
    approval_policy_ref: ops_manager
    timeout_seconds: 1800
    next: sync_external_dispatch
    on_failure: manual_review
```

Make sure the fake runtime callback payload matches what `ResumeCallback` merges:

```go
payload := map[string]interface{}{
	"agent_task_id":     taskID,
	"agent_task_status": "succeeded",
	"agent_result_type": "analysis",
	"agent_result": map[string]interface{}{
		"summary": "uplink flap",
	},
}
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
go test ./app/orchestration/service/impl -run 'TestMultiAgentClosureAnalysisDispatchApprovalLoop' -count=1
```

Expected:

- loop test passes
- execution reaches `waiting_approval`

- [ ] **Step 5: Commit**

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
git add app/orchestration/template/testdata/multi_agent_ticket_closure/manifest.yaml \
  app/orchestration/template/testdata/multi_agent_ticket_closure/workflow.yaml \
  app/orchestration/template/testdata/multi_agent_ticket_closure/agents.yaml \
  app/orchestration/service/impl/execution_test.go \
  app/orchestration/service/impl/resume_test.go
git commit -m "feat: wire analysis and dispatch agent loop"
```

### Task 5: Add Tracking, Knowledge, And Agent-Task Observability

**Files:**
- Modify: `OneOps/app/orchestration/dto/agent_task.go`
- Modify: `OneOps/app/orchestration/service/i_execution.go`
- Modify: `OneOps/app/orchestration/service/impl/execution.go`
- Modify: `OneOps/app/orchestration/api/execution.go`
- Modify: `OneOps/app/orchestration/router/execution.go`
- Modify: `OneOPS-UI/src/typings/orchestration/execution.ts`
- Modify: `OneOPS-UI/src/api/orchestration/execution.ts`
- Modify: `OneOPS-UI/src/views/platform/ExecutionObservatory.vue`
- Modify: `OneOPS-UI/scripts/execution-observatory-smoke.ts`

- [ ] **Step 1: Write the failing tests**

Add a backend test for listing execution agent tasks:

```go
func TestExecutionService_ListExecutionAgentTasks(t *testing.T) {
	db := newOrchestrationTestDB(t)
	seedAgentTask(t, db, orchestrationModel.AgentTask{
		ID:               "task-analysis-1",
		ExecutionID:      "exec-1",
		NodeID:           "analysis_submit",
		TaskType:         "analyze_alert",
		AgentCatalogName: "closure_agents",
		Status:           "succeeded",
		ResultPayloadJSON: `{"summary":"uplink flap"}`,
	})

	svc := NewExecutionSrv(db, zap.NewNop(), nil, nil)
	items, err := svc.ListExecutionAgentTasks(context.Background(), "exec-1")
	if err != nil {
		t.Fatalf("ListExecutionAgentTasks error: %v", err)
	}
	if len(items) != 1 {
		t.Fatalf("item count = %d, want %d", len(items), 1)
	}
	if items[0].TaskType != "analyze_alert" {
		t.Fatalf("task type = %q, want %q", items[0].TaskType, "analyze_alert")
	}
}
```

Extend the UI smoke to assert the drawer includes an agent-task section:

```ts
assert.match(viewSource, /Agent Tasks/, 'view should include agent task panel');
assert.match(apiSource, /export const listExecutionAgentTasksReq = async/, 'should export listExecutionAgentTasksReq');
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
go test ./app/orchestration/service/impl -run 'TestExecutionService_ListExecutionAgentTasks' -count=1

cd /home/jacky/project/OneOPS-ALL/OneOPS-UI
npm run smoke:execution-observatory
```

Expected:

- backend test fails because `ListExecutionAgentTasks` does not exist
- UI smoke fails because no agent-task API/panel exists

- [ ] **Step 3: Write minimal implementation**

Add a response DTO and execution service method:

```go
type ExecutionAgentTaskResp struct {
	ID               string `json:"id"`
	NodeID           string `json:"node_id"`
	TaskType         string `json:"task_type"`
	AgentCatalogName string `json:"agent_catalog_name"`
	Status           string `json:"status"`
	ResultPayloadJSON string `json:"result_payload_json,omitempty"`
	LastError        string `json:"last_error,omitempty"`
	UpdatedAt        time.Time `json:"updated_at"`
}
```

```go
func (s *ExecutionSrv) ListExecutionAgentTasks(ctx context.Context, executionID string) ([]dto.ExecutionAgentTaskResp, error) {
	var rows []orchestrationModel.AgentTask
	if err := s.DB.WithContext(ctx).
		Order("updated_at asc").
		Find(&rows, "execution_id = ?", strings.TrimSpace(executionID)).Error; err != nil {
		return nil, err
	}
	out := make([]dto.ExecutionAgentTaskResp, 0, len(rows))
	for _, row := range rows {
		out = append(out, dto.ExecutionAgentTaskResp{
			ID:                row.ID,
			NodeID:            row.NodeID,
			TaskType:          row.TaskType,
			AgentCatalogName:  row.AgentCatalogName,
			Status:            row.Status,
			ResultPayloadJSON: row.ResultPayloadJSON,
			LastError:         row.LastError,
			UpdatedAt:         row.UpdatedAt,
		})
	}
	return out, nil
}
```

Show the task list in the observatory drawer:

```ts
const agentTasks = ref<ExecutionAgentTaskResp[]>([]);

export const listExecutionAgentTasksReq = async (executionID: string) => {
  return request<ExecutionAgentTaskResp[]>({
    url: `/orchestration/executions/${encodeURIComponent(executionID)}/agent-tasks`,
    method: HTTP_GET,
  });
};
```

```vue
<div class="drawer-section-title">Agent Tasks</div>
<a-empty v-if="agentTasks.length === 0" description="暂无 Agent 任务" />
<a-timeline v-else>
  <a-timeline-item v-for="task in agentTasks" :key="task.id">
    <strong>{{ task.task_type }}</strong>
    <div>{{ task.status }} / {{ task.agent_catalog_name }}</div>
    <pre class="timeline-item__payload">{{ formatPayload(task.result_payload_json) }}</pre>
  </a-timeline-item>
</a-timeline>
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
go test ./app/orchestration/service/impl -run 'TestExecutionService_ListExecutionAgentTasks' -count=1

cd /home/jacky/project/OneOPS-ALL/OneOPS-UI
npm run smoke:execution-observatory
```

Expected:

- backend agent-task test passes
- observatory smoke passes

- [ ] **Step 5: Commit**

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
git add app/orchestration/dto/agent_task.go \
  app/orchestration/service/i_execution.go \
  app/orchestration/service/impl/execution.go \
  app/orchestration/api/execution.go \
  app/orchestration/router/execution.go
git commit -m "feat: expose execution agent task observability"

cd /home/jacky/project/OneOPS-ALL/OneOPS-UI
git add src/typings/orchestration/execution.ts \
  src/api/orchestration/execution.ts \
  src/views/platform/ExecutionObservatory.vue \
  scripts/execution-observatory-smoke.ts
git commit -m "feat: show agent task history in observatory"
```

### Task 6: Real Multi-Agent Acceptance And Runbook Closure

**Files:**
- Create: `OneOPS-UI/scripts/multi-agent-ticket-closure-real-api-acceptance.ts`
- Modify: `OneOPS-UI/package.json`
- Modify: `docs/runbooks/alert-to-ticket-dagengine-mvp.md`

- [ ] **Step 1: Write the failing acceptance script contract**

Create a script skeleton that expects a full multi-agent closure loop:

```ts
assert.equal(approvalExecution.status, 'waiting_approval', 'execution should pause for approval after dispatch');
assert.ok(approvalExecution.resume_token, 'approval execution should expose resume token');
assert.ok(agentTasks.some(task => task.task_type === 'analyze_alert'), 'should record analysis task');
assert.ok(agentTasks.some(task => task.task_type === 'recommend_dispatch'), 'should record dispatch task');
assert.ok(agentTasks.some(task => task.task_type === 'track_execution'), 'should record tracking task');
assert.ok(agentTasks.some(task => task.task_type === 'draft_knowledge'), 'should record knowledge task');
```

- [ ] **Step 2: Run script to verify it fails**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOPS-UI
npx esbuild scripts/multi-agent-ticket-closure-real-api-acceptance.ts --bundle --platform=node --format=esm --outfile=.tmp/multi-agent-ticket-closure-real-api-acceptance.mjs
node .tmp/multi-agent-ticket-closure-real-api-acceptance.mjs
```

Expected:

- file missing or acceptance fails because the multi-agent workflow and agent-task endpoint are not complete yet

- [ ] **Step 3: Write the acceptance implementation**

Implement the flow:

```ts
const started = await postJson<ExecutionResp>(token, '/orchestration/executions', {
  template_code: templateCode,
  environment,
  trigger_source: 'multi_agent_ticket_closure_acceptance',
  context: {
    alert_code: alertCode,
    ticket_code: ticketCode,
  },
}, 'start multi-agent execution');

const waitingApproval = await waitForExecutionStatus(token, started.id, 'waiting_approval');
await postJson<ResumeResp>(token, '/orchestration/resume/approve', {
  resume_token: waitingApproval.resume_token,
  decision: 'approve',
  operator: 'ops_oncall',
  comment: 'accept dispatch plan',
}, 'approve multi-agent execution');

const completed = await waitForExecutionStatus(token, started.id, 'completed');
const agentTasks = await getJson<ExecutionAgentTaskResp[]>(
  token,
  `/orchestration/executions/${encodeURIComponent(started.id)}/agent-tasks`,
  'list agent tasks',
);
```

Update `package.json`:

```json
"acceptance:multi-agent-ticket-closure-real-api": "npx esbuild scripts/multi-agent-ticket-closure-real-api-acceptance.ts --bundle --platform=node --format=esm --outfile=.tmp/multi-agent-ticket-closure-real-api-acceptance.mjs >/dev/null && node .tmp/multi-agent-ticket-closure-real-api-acceptance.mjs"
```

Update the runbook with:

```md
1. Start `OneOps` on `:8380`.
2. Start `agentruntime` on `:8391`.
3. Run `npm run acceptance:multi-agent-ticket-closure-real-api`.
4. Open `/#/platform/execution-observatory` and inspect Agent Tasks plus approval timeline.
```

- [ ] **Step 4: Run end-to-end verification**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
go test ./app/orchestration/... ./app/agentruntime/... -count=1

cd /home/jacky/project/OneOPS-ALL/OneOPS-UI
npm run smoke:execution-observatory
npm run acceptance:multi-agent-ticket-closure-real-api
npx eslint src/views/platform/ExecutionObservatory.vue src/api/orchestration/execution.ts src/typings/orchestration/execution.ts scripts/multi-agent-ticket-closure-real-api-acceptance.ts --ext .vue,.ts
```

Expected:

- orchestration backend tests pass
- agentruntime tests pass
- observatory smoke passes
- real acceptance prints an observatory URL, execution ID, and evidence file path

- [ ] **Step 5: Commit**

```bash
cd /home/jacky/project/OneOPS-ALL/OneOPS-UI
git add scripts/multi-agent-ticket-closure-real-api-acceptance.ts package.json
git commit -m "test: add multi-agent closure real API acceptance"

cd /home/jacky/project/OneOPS-ALL
git add docs/runbooks/alert-to-ticket-dagengine-mvp.md
git commit -m "docs: document multi-agent closure runbook"
```

## Self-Review

### Spec coverage

- agent task submission and persistence: covered by Task 2
- separate agent runtime service: covered by Task 3
- analysis + dispatch + approval loop: covered by Task 4
- tracking + knowledge + closure observability: covered by Tasks 5 and 6
- OneOps-owned wait/resume semantics: covered by Tasks 1, 2, and 4

### Placeholder scan

- no `TODO`, `TBD`, or “similar to Task N” placeholders remain
- every code-changing step includes concrete file paths, code blocks, and verification commands

### Type consistency

- `ResumeTokenContextKey` is used consistently across template, compiler, runtime, and workflow YAML
- `AgentTask`, `AgentRuntimeSubmitReq`, `ExecutionAgentTaskResp`, and `listExecutionAgentTasksReq` names are reused consistently across backend and UI

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-06-27-oneops-multi-agent-ticket-closure-runtime-implementation.md`. Two execution options:

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?
