# OneOps Orchestration Runtime Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the next lightweight orchestration MVP layer in OneOps by introducing a shared node runtime foundation, persistent suspend-and-resume support, controlled external call nodes, and migration of existing node execution onto the new runtime path.

**Architecture:** Keep `OneOps/app/orchestration` as the business-facing owner of templates, persistence, APIs, and governance while keeping `dagenginev2` as the execution kernel. Insert a runtime registry and runtime contracts between `DagengineAdapter` and business capability execution so that new node types can be added without bloating the main execution path.

**Tech Stack:** Go, Gin, GORM, SQLite tests, MySQL-compatible GORM models, `github.com/netxops/dagenginev2/engine`, `github.com/netxops/dagenginev2/interfaces`, YAML-backed orchestration templates, existing OneOps provider/router wiring.

---

## File Structure

### `OneOps` repo

- Create: `OneOps/app/orchestration/runtime/types.go`
  Purpose: shared runtime input/output contracts, suspend instruction, and execution result helpers
- Create: `OneOps/app/orchestration/runtime/errors.go`
  Purpose: structured runtime error model and helpers
- Create: `OneOps/app/orchestration/runtime/events.go`
  Purpose: standard runtime event and concise log model
- Create: `OneOps/app/orchestration/runtime/registry.go`
  Purpose: node-runtime registry and dispatch lookup
- Create: `OneOps/app/orchestration/runtime/middleware.go`
  Purpose: shared execution wrapper for logs, event emission, and error normalization
- Create: `OneOps/app/orchestration/runtime/registry_test.go`
  Purpose: verify runtime registration, lookup, and duplicate protection
- Create: `OneOps/app/orchestration/runtime/middleware_test.go`
  Purpose: verify middleware log/event/error behavior
- Create: `OneOps/app/orchestration/runtime/flow_step.go`
  Purpose: runtime implementation for `flow_step`
- Create: `OneOps/app/orchestration/runtime/agent_step.go`
  Purpose: runtime implementation for `agent_step`
- Create: `OneOps/app/orchestration/runtime/callback_wait_step.go`
  Purpose: runtime implementation for `callback_wait_step`
- Create: `OneOps/app/orchestration/runtime/approval_wait_step.go`
  Purpose: runtime implementation for `approval_wait_step`
- Create: `OneOps/app/orchestration/runtime/external_call_step.go`
  Purpose: runtime implementation for `external_call_step`
- Create: `OneOps/app/orchestration/runtime/runtime_test_helpers.go`
  Purpose: small fake implementations shared by runtime tests
- Create: `OneOps/app/orchestration/orchestration_model/suspend_record.go`
  Purpose: persistent wait record model
- Create: `OneOps/app/orchestration/dto/resume.go`
  Purpose: callback/approval resume DTOs
- Create: `OneOps/app/orchestration/service/i_resume.go`
  Purpose: resume service interface
- Create: `OneOps/app/orchestration/service/impl/resume.go`
  Purpose: suspend resolution, callback resume, approval approve/reject logic
- Create: `OneOps/app/orchestration/service/impl/resume_test.go`
  Purpose: suspend persistence and resume-flow tests
- Create: `OneOps/app/orchestration/api/resume.go`
  Purpose: callback/approval resume endpoints
- Create: `OneOps/app/orchestration/router/resume.go`
  Purpose: route registration for resume endpoints
- Create: `OneOps/app/orchestration/orchestration_model/external_target.go`
  Purpose: persistent platform-managed external target model
- Create: `OneOps/app/orchestration/target_registry/registry.go`
  Purpose: pre-registered target resolution and request defaults
- Create: `OneOps/app/orchestration/target_registry/registry_test.go`
  Purpose: target resolution tests
- Create: `OneOps/app/orchestration/service/impl/external_target.go`
  Purpose: service to load and resolve platform-owned target definitions
- Modify: `OneOps/app/orchestration/template/define.go`
  Purpose: support `external_call_step`, `callback_wait_step`, and `approval_wait_step` fields
- Modify: `OneOps/app/orchestration/template/loader.go`
  Purpose: validate new node types and required fields
- Modify: `OneOps/app/orchestration/template/loader_test.go`
  Purpose: add validation tests for new step types
- Modify: `OneOps/app/orchestration/compiler/dagengine_compiler.go`
  Purpose: preserve new node types and runtime configuration in compiled DAG nodes
- Modify: `OneOps/app/orchestration/compiler/dagengine_compiler_test.go`
  Purpose: verify compilation of new step configuration
- Modify: `OneOps/app/orchestration/service/impl/dagengine_adapter.go`
  Purpose: replace gateway-only execution with runtime registry dispatch and wait handling
- Modify: `OneOps/app/orchestration/service/impl/execution.go`
  Purpose: persist concise logs, standardized events, and waiting statuses
- Modify: `OneOps/app/orchestration/service/impl/execution_test.go`
  Purpose: cover runtime events, waiting states, and resume interactions
- Modify: `OneOps/app/orchestration/service/impl/capability_gateway.go`
  Purpose: narrow into business capability provider instead of generic node switch
- Modify: `OneOps/app/orchestration/service/impl/capability_gateway_test.go`
  Purpose: test capability behavior used by flow and agent runtimes
- Modify: `OneOps/app/orchestration/dto/execution.go`
  Purpose: expose waiting status and resume-related fields
- Modify: `OneOps/app/orchestration/orchestration_model/template_execution.go`
  Purpose: support waiting status and optional summary fields if needed
- Modify: `OneOps/app/orchestration/orchestration_model/execution_event.go`
  Purpose: persist standardized runtime events
- Create: `OneOps/app/orchestration/orchestration_model/execution_log.go`
  Purpose: concise node log persistence
- Modify: `OneOps/app/orchestration/service/i_execution.go`
  Purpose: allow execution lookup to expose waiting-aware status
- Modify: `OneOps/boot/provider/api.go`
  Purpose: wire resume APIs
- Modify: `OneOps/boot/provider/service_groups.go`
  Purpose: wire runtime registry, resume service, and external target services
- Modify: `OneOps/initialize/routers.go`
  Purpose: register resume routes

### `docs` repo

- Modify: `docs/runbooks/alert-to-ticket-dagengine-mvp.md`
  Purpose: document waiting, resume, and external call runtime behavior

## Task 1: Build the Shared Runtime Foundation

**Files:**
- Create: `OneOps/app/orchestration/runtime/types.go`
- Create: `OneOps/app/orchestration/runtime/errors.go`
- Create: `OneOps/app/orchestration/runtime/events.go`
- Create: `OneOps/app/orchestration/runtime/registry.go`
- Create: `OneOps/app/orchestration/runtime/middleware.go`
- Create: `OneOps/app/orchestration/runtime/registry_test.go`
- Create: `OneOps/app/orchestration/runtime/middleware_test.go`
- Create: `OneOps/app/orchestration/runtime/runtime_test_helpers.go`

- [ ] **Step 1: Write the failing runtime registry test**

```go
func TestRegistry_RegisterAndResolveRuntime(t *testing.T) {
	registry := NewRegistry()
	runtime := &fakeRuntime{}

	if err := registry.Register("flow_step", runtime); err != nil {
		t.Fatalf("Register returned error: %v", err)
	}

	got, err := registry.Resolve("flow_step")
	if err != nil {
		t.Fatalf("Resolve returned error: %v", err)
	}
	if got != runtime {
		t.Fatal("resolved runtime does not match registered runtime")
	}
}

func TestRegistry_RejectsDuplicateRuntime(t *testing.T) {
	registry := NewRegistry()
	runtimeA := &fakeRuntime{}
	runtimeB := &fakeRuntime{}

	if err := registry.Register("flow_step", runtimeA); err != nil {
		t.Fatalf("initial Register returned error: %v", err)
	}
	if err := registry.Register("flow_step", runtimeB); err == nil {
		t.Fatal("expected duplicate runtime registration error")
	}
}
```

- [ ] **Step 2: Run the runtime tests to verify they fail**

Run: `cd OneOps && go test ./app/orchestration/runtime -run TestRegistry -v`
Expected: FAIL because the runtime package and registry do not exist yet.

- [ ] **Step 3: Implement the shared runtime contracts and registry**

```go
type NodeRuntime interface {
	Run(context.Context, NodeExecutionInput) (NodeExecutionResult, error)
}

type NodeExecutionInput struct {
	ExecutionID string
	NodeID      string
	NodeType    string
	Attempt     int
	TraceID     string
	Deadline    time.Time
	Context     map[string]interface{}
	NodeConfig  map[string]interface{}
}

type NodeExecutionResult struct {
	Status             string
	ContextPatch       map[string]interface{}
	Logs               []ExecutionLogEntry
	Events             []ExecutionEvent
	Error              *RuntimeError
	SuspendInstruction *SuspendInstruction
}

type Registry struct {
	mu       sync.RWMutex
	runtimes map[string]NodeRuntime
}

type fakeRuntime struct {
	result NodeExecutionResult
	err    error
}

func (f *fakeRuntime) Run(_ context.Context, _ NodeExecutionInput) (NodeExecutionResult, error) {
	return f.result, f.err
}

type stubTargetResolver struct {
	target *ResolvedExternalTarget
	err    error
}

func (s *stubTargetResolver) Resolve(context.Context, string) (*ResolvedExternalTarget, error) {
	return s.target, s.err
}
```

```go
func (r *Registry) Register(nodeType string, runtime NodeRuntime) error {
	nodeType = strings.TrimSpace(nodeType)
	if nodeType == "" {
		return fmt.Errorf("node type is required")
	}
	if runtime == nil {
		return fmt.Errorf("runtime is required")
	}

	r.mu.Lock()
	defer r.mu.Unlock()
	if _, exists := r.runtimes[nodeType]; exists {
		return fmt.Errorf("runtime %q already registered", nodeType)
	}
	r.runtimes[nodeType] = runtime
	return nil
}
```

- [ ] **Step 4: Write the failing middleware test**

```go
func TestMiddleware_WrapsRuntimeWithLogsEventsAndNormalizedError(t *testing.T) {
	mw := NewMiddleware()
	input := NodeExecutionInput{
		ExecutionID: "exec-1",
		NodeID:      "node-1",
		NodeType:    "flow_step",
	}

	result, err := mw.Run(context.Background(), input, func(context.Context, NodeExecutionInput) (NodeExecutionResult, error) {
		return NodeExecutionResult{}, fmt.Errorf("boom")
	})

	if err == nil {
		t.Fatal("expected middleware to return normalized error")
	}
	if result.Error == nil || result.Error.Category != "runtime_error" {
		t.Fatalf("unexpected runtime error: %#v", result.Error)
	}
	if len(result.Events) < 2 {
		t.Fatalf("unexpected event count: %d", len(result.Events))
	}
}
```

- [ ] **Step 5: Run the middleware test to verify it fails**

Run: `cd OneOps && go test ./app/orchestration/runtime -run TestMiddleware -v`
Expected: FAIL because middleware does not exist yet.

- [ ] **Step 6: Implement runtime middleware, structured errors, and standard events**

```go
type RuntimeError struct {
	Category    string                 `json:"category"`
	Code        string                 `json:"code"`
	Message     string                 `json:"message"`
	Retryable   bool                   `json:"retryable"`
	Details     map[string]interface{} `json:"details,omitempty"`
	ExternalRef string                 `json:"external_ref,omitempty"`
}

type ExecutionEvent struct {
	EventType  string                 `json:"event_type"`
	Payload    map[string]interface{} `json:"payload,omitempty"`
	OccurredAt time.Time              `json:"occurred_at"`
}

type Middleware struct{}

func NewRuntimeError(category, code, message string, retryable bool, details map[string]interface{}) *RuntimeError {
	return &RuntimeError{
		Category:  strings.TrimSpace(category),
		Code:      strings.TrimSpace(code),
		Message:   strings.TrimSpace(message),
		Retryable: retryable,
		Details:   details,
	}
}

func NormalizeRuntimeError(err error) *RuntimeError {
	if err == nil {
		return nil
	}
	return NewRuntimeError("runtime_error", "runtime_execution_failed", err.Error(), false, nil)
}

func NormalizeRuntimeExecutionError(nodeType string, err error) *RuntimeError {
	if err == nil {
		return nil
	}
	return NewRuntimeError("runtime_error", strings.TrimSpace(nodeType)+"_execution_failed", err.Error(), false, nil)
}
```

```go
func (m *Middleware) Run(
	ctx context.Context,
	input NodeExecutionInput,
	run func(context.Context, NodeExecutionInput) (NodeExecutionResult, error),
) (NodeExecutionResult, error) {
	result := NodeExecutionResult{
		Events: []ExecutionEvent{NewExecutionEvent("node_started", map[string]interface{}{
			"execution_id": input.ExecutionID,
			"node_id":      input.NodeID,
			"node_type":    input.NodeType,
		})},
	}

	inner, err := run(ctx, input)
	result = MergeNodeExecutionResult(result, inner)
	if err != nil && result.Error == nil {
		result.Error = NormalizeRuntimeError(err)
	}

	if result.Error != nil {
		result.Events = append(result.Events, NewExecutionEvent("node_failed", map[string]interface{}{
			"execution_id": input.ExecutionID,
			"node_id":      input.NodeID,
			"category":     result.Error.Category,
			"code":         result.Error.Code,
		}))
		return result, fmt.Errorf(result.Error.Message)
	}

	eventType := "node_completed"
	if result.SuspendInstruction != nil {
		eventType = "node_waiting"
	}
	result.Events = append(result.Events, NewExecutionEvent(eventType, map[string]interface{}{
		"execution_id": input.ExecutionID,
		"node_id":      input.NodeID,
	}))
	return result, nil
}
```

- [ ] **Step 7: Run the runtime package tests to verify they pass**

Run: `cd OneOps && go test ./app/orchestration/runtime -v`
Expected: PASS with registry and middleware tests green.

- [ ] **Step 8: Commit the runtime-foundation slice**

```bash
git -C OneOps add app/orchestration/runtime
git -C OneOps commit -m "feat: add orchestration runtime foundation"
```

## Task 2: Add Persistent Suspend-and-Resume Support

**Files:**
- Create: `OneOps/app/orchestration/orchestration_model/suspend_record.go`
- Create: `OneOps/app/orchestration/orchestration_model/execution_log.go`
- Create: `OneOps/app/orchestration/dto/resume.go`
- Create: `OneOps/app/orchestration/service/i_resume.go`
- Create: `OneOps/app/orchestration/service/impl/resume.go`
- Create: `OneOps/app/orchestration/service/impl/resume_test.go`
- Create: `OneOps/app/orchestration/api/resume.go`
- Create: `OneOps/app/orchestration/router/resume.go`
- Modify: `OneOps/app/orchestration/dto/execution.go`
- Modify: `OneOps/app/orchestration/orchestration_model/execution_event.go`
- Modify: `OneOps/app/orchestration/orchestration_model/template_execution.go`
- Modify: `OneOps/app/orchestration/service/i_execution.go`
- Modify: `OneOps/boot/provider/api.go`
- Modify: `OneOps/boot/provider/service_groups.go`
- Modify: `OneOps/initialize/routers.go`

- [ ] **Step 1: Write the failing suspend-and-resume test**

```go
func TestResumeService_ResolveCallbackResume(t *testing.T) {
	db := newResumeTestDB(t)
	service := NewResumeSrv(db, zap.NewNop())

	record := &orchestrationModel.SuspendRecord{
		ID:          "suspend-1",
		ExecutionID: "exec-1",
		NodeID:      "wait_callback",
		WaitType:    "callback",
		ResumeToken: "token-1",
		Status:      "active",
	}
	if err := db.Create(record).Error; err != nil {
		t.Fatalf("create suspend record failed: %v", err)
	}

	resp, err := service.ResumeCallback(context.Background(), dto.CallbackResumeReq{
		ResumeToken: "token-1",
		Payload:     map[string]interface{}{"result": "ok"},
	})
	if err != nil {
		t.Fatalf("ResumeCallback returned error: %v", err)
	}
	if resp.Status != "resolved" {
		t.Fatalf("unexpected resume status: %s", resp.Status)
	}
}
```

- [ ] **Step 2: Run the resume test to verify it fails**

Run: `cd OneOps && go test ./app/orchestration/service/impl -run TestResumeService_ResolveCallbackResume -v`
Expected: FAIL because the suspend model and resume service do not exist yet.

- [ ] **Step 3: Implement suspend and concise log persistence models**

```go
type SuspendRecord struct {
	ID              string `gorm:"primaryKey;type:varchar(36)"`
	ExecutionID     string `gorm:"type:varchar(36);index;not null"`
	NodeID          string `gorm:"type:varchar(128);index;not null"`
	WaitType        string `gorm:"type:varchar(32);index;not null"`
	ResumeToken     string `gorm:"type:varchar(128);uniqueIndex;not null"`
	Status          string `gorm:"type:varchar(32);index;not null"`
	WaitPayloadJSON string `gorm:"type:json;not null"`
	ExpiresAt       *time.Time
	ResolvedAt      *time.Time
	CreatedAt       time.Time
	UpdatedAt       time.Time
}
```

```go
type ExecutionLog struct {
	ID          string `gorm:"primaryKey;type:varchar(36)"`
	ExecutionID string `gorm:"type:varchar(36);index;not null"`
	NodeID      string `gorm:"type:varchar(128);index;not null"`
	Level       string `gorm:"type:varchar(16);not null"`
	Message     string `gorm:"type:varchar(255);not null"`
	Code        string `gorm:"type:varchar(64);index;not null"`
	DetailsJSON string `gorm:"type:json;not null"`
	CreatedAt   time.Time
}
```

- [ ] **Step 4: Implement resume DTOs and service interface**

```go
type CallbackResumeReq struct {
	ResumeToken string                 `json:"resume_token"`
	Payload     map[string]interface{} `json:"payload"`
}

type ApprovalDecisionReq struct {
	ResumeToken string `json:"resume_token"`
	Decision    string `json:"decision"`
	Operator    string `json:"operator"`
	Comment     string `json:"comment"`
}

type ResumeResp struct {
	ExecutionID string `json:"execution_id"`
	NodeID      string `json:"node_id"`
	Status      string `json:"status"`
}
```

```go
type IResume interface {
	ResumeCallback(context.Context, dto.CallbackResumeReq) (*dto.ResumeResp, error)
	Approve(context.Context, dto.ApprovalDecisionReq) (*dto.ResumeResp, error)
	Reject(context.Context, dto.ApprovalDecisionReq) (*dto.ResumeResp, error)
}
```

- [ ] **Step 5: Implement resume service and standardized suspend resolution**

```go
func (s *ResumeSrv) ResumeCallback(ctx context.Context, req dto.CallbackResumeReq) (*dto.ResumeResp, error) {
	record, err := s.findActiveSuspendByToken(ctx, req.ResumeToken, "callback")
	if err != nil {
		return nil, err
	}
	now := time.Now()
	record.Status = "resolved"
	record.ResolvedAt = &now
	if err := s.DB.WithContext(ctx).Save(record).Error; err != nil {
		return nil, err
	}
	return &dto.ResumeResp{
		ExecutionID: record.ExecutionID,
		NodeID:      record.NodeID,
		Status:      record.Status,
	}, nil
}
```

```go
func (s *ResumeSrv) findActiveSuspendByToken(ctx context.Context, token, waitType string) (*orchestrationModel.SuspendRecord, error) {
	var record orchestrationModel.SuspendRecord
	if err := s.DB.WithContext(ctx).
		Where("resume_token = ? AND wait_type = ? AND status = ?", strings.TrimSpace(token), waitType, "active").
		First(&record).Error; err != nil {
		return nil, err
	}
	return &record, nil
}
```

- [ ] **Step 6: Implement resume APIs and route wiring**

```go
func (a *ResumeAPI) ResumeCallback(ctx *gin.Context) {
	var req dto.CallbackResumeReq
	if ok := bind.JSON(&req, ctx); !ok {
		return
	}
	resp, err := a.ResumeSrv.ResumeCallback(ctx, req)
	if err != nil {
		response.FailWithMsg(err.Error(), ctx)
		return
	}
	response.OkWithData(resp, ctx)
}
```

```go
func Resume(r *gin.RouterGroup, api *api.ResumeAPI) {
	g := r.Group("orchestration/resume")
	g.POST("callback", api.ResumeCallback)
	g.POST("approve", api.Approve)
	g.POST("reject", api.Reject)
}
```

- [ ] **Step 7: Run the focused resume tests to verify they pass**

Run: `cd OneOps && go test ./app/orchestration/service/impl -run TestResumeService_ResolveCallbackResume -v`
Expected: PASS with active suspend resolution green.

- [ ] **Step 8: Run the orchestration package tests to verify suspend wiring stays green**

Run: `cd OneOps && go test ./app/orchestration/... -v`
Expected: PASS with new resume package, models, and route-facing code compiling cleanly.

- [ ] **Step 9: Commit the suspend-and-resume slice**

```bash
git -C OneOps add app/orchestration boot/provider/api.go boot/provider/service_groups.go initialize/routers.go
git -C OneOps commit -m "feat: add orchestration suspend and resume support"
```

## Task 3: Add Controlled External Call Runtime and Target Registry

**Files:**
- Create: `OneOps/app/orchestration/orchestration_model/external_target.go`
- Create: `OneOps/app/orchestration/target_registry/registry.go`
- Create: `OneOps/app/orchestration/target_registry/registry_test.go`
- Create: `OneOps/app/orchestration/service/impl/external_target.go`
- Create: `OneOps/app/orchestration/runtime/external_call_step.go`
- Modify: `OneOps/app/orchestration/template/define.go`
- Modify: `OneOps/app/orchestration/template/loader.go`
- Modify: `OneOps/app/orchestration/template/loader_test.go`
- Modify: `OneOps/app/orchestration/compiler/dagengine_compiler.go`
- Modify: `OneOps/app/orchestration/compiler/dagengine_compiler_test.go`

- [ ] **Step 1: Write the failing external target registry test**

```go
func TestRegistry_ResolveTargetByRef(t *testing.T) {
	db, err := gorm.Open(sqlite.Open("file::memory:?cache=shared"), &gorm.Config{})
	if err != nil {
		t.Fatalf("open sqlite failed: %v", err)
	}
	if err := db.AutoMigrate(&orchestrationModel.ExternalTarget{}); err != nil {
		t.Fatalf("auto migrate failed: %v", err)
	}
	if err := db.Create(&orchestrationModel.ExternalTarget{
		ID:        "target-1",
		Ref:       "ticketing_system_prod",
		Method:    "POST",
		BaseURL:   "https://ticket.example.com",
		Enabled:   true,
		TimeoutSeconds: 30,
	}).Error; err != nil {
		t.Fatalf("create external target failed: %v", err)
	}

	registry := target_registry.NewRegistry(db)
	target, err := registry.Resolve(context.Background(), "ticketing_system_prod")
	if err != nil {
		t.Fatalf("Resolve returned error: %v", err)
	}
	if target.BaseURL != "https://ticket.example.com" {
		t.Fatalf("unexpected base url: %s", target.BaseURL)
	}
}
```

- [ ] **Step 2: Run the target registry test to verify it fails**

Run: `cd OneOps && go test ./app/orchestration/target_registry -run TestRegistry_ResolveTargetByRef -v`
Expected: FAIL because the target registry and model do not exist yet.

- [ ] **Step 3: Implement the external target model and registry**

```go
type ExternalTarget struct {
	ID             string `gorm:"primaryKey;type:varchar(36)"`
	Ref            string `gorm:"type:varchar(128);uniqueIndex;not null"`
	Method         string `gorm:"type:varchar(16);not null"`
	BaseURL        string `gorm:"type:varchar(255);not null"`
	DefaultPath    string `gorm:"type:varchar(255);not null"`
	DefaultHeaders string `gorm:"type:json;not null"`
	TimeoutSeconds int    `gorm:"not null"`
	Enabled        bool   `gorm:"not null"`
	CreatedAt      time.Time
	UpdatedAt      time.Time
}
```

```go
func (r *Registry) Resolve(ctx context.Context, ref string) (*orchestrationModel.ExternalTarget, error) {
	var target orchestrationModel.ExternalTarget
	if err := r.DB.WithContext(ctx).
		Where("ref = ? AND enabled = ?", strings.TrimSpace(ref), true).
		First(&target).Error; err != nil {
		return nil, err
	}
	return &target, nil
}
```

- [ ] **Step 4: Write the failing external call runtime test**

```go
func TestExternalCallRuntime_RunReturnsContextPatch(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		_, _ = w.Write([]byte(`{"ticket_code":"TICKET-1"}`))
	}))
	defer server.Close()

	runtime := NewExternalCallRuntime(&stubTargetResolver{
		target: &ResolvedExternalTarget{
			Method:         "POST",
			BaseURL:        server.URL,
			DefaultPath:    "/create",
			TimeoutSeconds: 5,
		},
	})

	result, err := runtime.Run(context.Background(), NodeExecutionInput{
		ExecutionID: "exec-1",
		NodeID:      "external",
		NodeType:    "external_call_step",
		NodeConfig: map[string]interface{}{
			"target_ref": "ticketing_system_prod",
		},
	})
	if err != nil {
		t.Fatalf("Run returned error: %v", err)
	}
	if result.ContextPatch["ticket_code"] != "TICKET-1" {
		t.Fatalf("unexpected context patch: %#v", result.ContextPatch)
	}
}
```

- [ ] **Step 5: Run the external runtime test to verify it fails**

Run: `cd OneOps && go test ./app/orchestration/runtime -run TestExternalCallRuntime_RunReturnsContextPatch -v`
Expected: FAIL because `external_call_step` runtime does not exist yet.

- [ ] **Step 6: Extend template and compiler support for new wait and external node fields**

```go
type WorkflowStep struct {
	Key                string   `yaml:"key"`
	Type               string   `yaml:"type"`
	Action             string   `yaml:"action"`
	Next               string   `yaml:"next"`
	OnFailure          string   `yaml:"on_failure"`
	AgentCatalogName   string   `yaml:"agent_catalog_name,omitempty"`
	AllowedTools       []string `yaml:"allowed_tools,omitempty"`
	TargetRef          string   `yaml:"target_ref,omitempty"`
	RequestTemplateRef string   `yaml:"request_template_ref,omitempty"`
	CallbackRef        string   `yaml:"callback_ref,omitempty"`
	ResumePolicy       string   `yaml:"resume_policy,omitempty"`
	ApprovalPolicyRef  string   `yaml:"approval_policy_ref,omitempty"`
	TimeoutSeconds     int      `yaml:"timeout_seconds,omitempty"`
	OnTimeout          string   `yaml:"on_timeout,omitempty"`
}
```

```go
func buildNodeConfig(step template.WorkflowStep) map[string]interface{} {
	config := map[string]interface{}{
		"action": strings.TrimSpace(step.Action),
	}
	if v := strings.TrimSpace(step.TargetRef); v != "" {
		config["target_ref"] = v
	}
	if v := strings.TrimSpace(step.CallbackRef); v != "" {
		config["callback_ref"] = v
	}
	if v := strings.TrimSpace(step.ApprovalPolicyRef); v != "" {
		config["approval_policy_ref"] = v
	}
	if step.TimeoutSeconds > 0 {
		config["timeout_seconds"] = step.TimeoutSeconds
	}
	return config
}
```

- [ ] **Step 7: Implement the external call runtime**

```go
func (r *ExternalCallRuntime) Run(ctx context.Context, input NodeExecutionInput) (NodeExecutionResult, error) {
	targetRef := stringValue(input.NodeConfig, "target_ref")
	if targetRef == "" {
		return NodeExecutionResult{}, NewRuntimeError("validation_error", "missing_target_ref", "target_ref is required", false, nil)
	}

	target, err := r.TargetResolver.Resolve(ctx, targetRef)
	if err != nil {
		return NodeExecutionResult{}, NewRuntimeError("external_call_error", "target_resolve_failed", err.Error(), false, nil)
	}

	request, err := http.NewRequestWithContext(ctx, target.Method, target.BaseURL+target.DefaultPath, nil)
	if err != nil {
		return NodeExecutionResult{}, NewRuntimeError("external_call_error", "request_build_failed", err.Error(), false, nil)
	}

	response, err := r.Client.Do(request)
	if err != nil {
		return NodeExecutionResult{}, NewRuntimeError("external_call_error", "request_failed", err.Error(), true, nil)
	}
	defer response.Body.Close()
```

```go
	var payload map[string]interface{}
	if err := json.NewDecoder(response.Body).Decode(&payload); err != nil {
		return NodeExecutionResult{}, NewRuntimeError("external_call_error", "response_decode_failed", err.Error(), false, nil)
	}
	if response.StatusCode < 200 || response.StatusCode >= 300 {
		return NodeExecutionResult{}, NewRuntimeError("external_call_error", "unexpected_status_code", fmt.Sprintf("status=%d", response.StatusCode), true, map[string]interface{}{"payload": payload})
	}

	return NodeExecutionResult{
		Status:       "completed",
		ContextPatch: payload,
		Logs: []ExecutionLogEntry{NewExecutionLogEntry("info", "external call completed", "external_call_completed", map[string]interface{}{
			"target_ref": targetRef,
			"status":     response.StatusCode,
		})},
	}, nil
}
```

- [ ] **Step 8: Run the focused orchestration tests to verify they pass**

Run: `cd OneOps && go test ./app/orchestration/runtime ./app/orchestration/target_registry ./app/orchestration/template ./app/orchestration/compiler -v`
Expected: PASS with external target resolution, runtime execution, template validation, and compiler metadata tests green.

- [ ] **Step 9: Commit the external-call slice**

```bash
git -C OneOps add app/orchestration
git -C OneOps commit -m "feat: add orchestration external call runtime"
```

## Task 4: Migrate Existing Execution Path to the Runtime Registry

**Files:**
- Create: `OneOps/app/orchestration/runtime/flow_step.go`
- Create: `OneOps/app/orchestration/runtime/agent_step.go`
- Create: `OneOps/app/orchestration/runtime/callback_wait_step.go`
- Create: `OneOps/app/orchestration/runtime/approval_wait_step.go`
- Modify: `OneOps/app/orchestration/service/impl/dagengine_adapter.go`
- Modify: `OneOps/app/orchestration/service/impl/execution.go`
- Modify: `OneOps/app/orchestration/service/impl/execution_test.go`
- Modify: `OneOps/app/orchestration/service/impl/capability_gateway.go`
- Modify: `OneOps/app/orchestration/service/impl/capability_gateway_test.go`
- Modify: `docs/runbooks/alert-to-ticket-dagengine-mvp.md`

- [ ] **Step 1: Write the failing waiting-runtime test**

```go
func TestCallbackWaitRuntime_RunReturnsSuspendInstruction(t *testing.T) {
	runtime := NewCallbackWaitRuntime()

	result, err := runtime.Run(context.Background(), NodeExecutionInput{
		ExecutionID: "exec-1",
		NodeID:      "wait_callback",
		NodeType:    "callback_wait_step",
		NodeConfig: map[string]interface{}{
			"callback_ref":    "ticket_callback",
			"timeout_seconds": 300,
		},
	})
	if err != nil {
		t.Fatalf("Run returned error: %v", err)
	}
	if result.SuspendInstruction == nil {
		t.Fatal("expected suspend instruction")
	}
	if result.SuspendInstruction.WaitType != "callback" {
		t.Fatalf("unexpected wait type: %s", result.SuspendInstruction.WaitType)
	}
}
```

- [ ] **Step 2: Run the waiting-runtime test to verify it fails**

Run: `cd OneOps && go test ./app/orchestration/runtime -run TestCallbackWaitRuntime_RunReturnsSuspendInstruction -v`
Expected: FAIL because wait runtimes do not exist yet.

- [ ] **Step 3: Implement flow, agent, callback-wait, and approval-wait runtimes**

```go
func (r *FlowStepRuntime) Run(ctx context.Context, input NodeExecutionInput) (NodeExecutionResult, error) {
	state, err := r.Gateway.ExecuteFlowAction(ctx, input)
	if err != nil {
		return NodeExecutionResult{}, NormalizeRuntimeExecutionError("flow_step", err)
	}
	return NodeExecutionResult{
		Status:       "completed",
		ContextPatch: state,
	}, nil
}

func (r *AgentStepRuntime) Run(ctx context.Context, input NodeExecutionInput) (NodeExecutionResult, error) {
	state, err := r.Gateway.ExecuteAgentAction(ctx, input)
	if err != nil {
		return NodeExecutionResult{}, NormalizeRuntimeExecutionError("agent_step", err)
	}
	return NodeExecutionResult{
		Status:       "completed",
		ContextPatch: state,
	}, nil
}
```

```go
func (r *CallbackWaitRuntime) Run(_ context.Context, input NodeExecutionInput) (NodeExecutionResult, error) {
	return NodeExecutionResult{
		Status: "waiting",
		SuspendInstruction: &SuspendInstruction{
			WaitType:       "callback",
			TimeoutSeconds: intValue(input.NodeConfig, "timeout_seconds"),
			Payload: map[string]interface{}{
				"callback_ref": stringValue(input.NodeConfig, "callback_ref"),
			},
		},
	}, nil
}
```

- [ ] **Step 4: Refactor the dagengine adapter to dispatch through runtime registry**

```go
type DagengineAdapter struct {
	Registry   *runtime.Registry
	Middleware *runtime.Middleware
	Logger     *zap.Logger
}
```

```go
	runner, err := a.Registry.Resolve(process.GetNodeType(nodeID))
	if err != nil {
		result.Status = "failed"
		result.Events = append(result.Events, newExecutionEvent("execution_failed", map[string]interface{}{
			"execution_id": executionID,
			"node_id":      nodeID,
			"error":        err.Error(),
		}))
		return result, err
	}

	nodeInput := runtime.NodeExecutionInput{
		ExecutionID: executionID,
		NodeID:      nodeID,
		NodeType:    process.GetNodeType(nodeID),
		Attempt:     1,
		Context:     result.Context,
		NodeConfig:  process.GetNodeConfig(nodeID),
	}
	nodeResult, execErr := a.Middleware.Run(ctx, nodeInput, runner.Run)
```

- [ ] **Step 5: Persist concise logs and waiting statuses inside execution service**

```go
	record := &orchestrationModel.TemplateExecution{
		ID:                   result.ExecutionID,
		TemplateDefinitionID: templateDef.ID,
		TemplateCode:         templateDef.Code,
		Environment:          req.Environment,
		TriggerSource:        req.TriggerSource,
		Status:               normalizeExecutionStatus(result.Status),
		ResultJSON:           string(resultJSON),
	}
```

```go
	for _, entry := range result.Logs {
		detailsJSON, err := json.Marshal(entry.Details)
		if err != nil {
			tx.Rollback()
			return nil, fmt.Errorf("marshal execution log details: %w", err)
		}
		logRecord := &orchestrationModel.ExecutionLog{
			ID:          uuid.NewString(),
			ExecutionID: record.ID,
			NodeID:      entry.NodeID,
			Level:       entry.Level,
			Message:     entry.Message,
			Code:        entry.Code,
			DetailsJSON: string(detailsJSON),
		}
		if err := tx.Create(logRecord).Error; err != nil {
			tx.Rollback()
			return nil, err
		}
	}
```

- [ ] **Step 6: Add integration tests for waiting status and runtime dispatch**

```go
func TestExecutionService_StartExecutionPersistsWaitingCallbackStatus(t *testing.T) {
	registry := runtime.NewRegistry()
	if err := registry.Register("callback_wait_step", NewCallbackWaitRuntime()); err != nil {
		t.Fatalf("Register returned error: %v", err)
	}
	adapter := NewDagengineAdapter(
		registry,
		runtime.NewMiddleware(),
		zap.NewNop(),
	)
	service := NewExecutionSrv(db, zap.NewNop(), templateSrv, adapter)

	resp, err := service.StartExecution(context.Background(), dto.StartExecutionReq{
		TemplateCode:  "callback-template",
		Environment:   "prod",
		TriggerSource: "manual",
	})
	if err != nil {
		t.Fatalf("StartExecution returned error: %v", err)
	}
	if resp.Status != "waiting_callback" {
		t.Fatalf("unexpected status: %s", resp.Status)
	}
}
```

- [ ] **Step 7: Run the orchestration execution tests to verify the new runtime path passes**

Run: `cd OneOps && go test ./app/orchestration/service/impl -v`
Expected: PASS with completed and waiting execution scenarios green.

- [ ] **Step 8: Run the full orchestration plus alert-engine verification suite**

Run: `cd OneOps && go test ./app/orchestration/... ./app/alert_engine/... ./boot/provider ./initialize -count=1`
Expected: PASS with runtime-registry migration, waiting support, and route wiring compiling cleanly.

- [ ] **Step 9: Update the operator runbook**

```md
## Waiting States

- `waiting_callback`: execution paused until a resume callback hits the OneOps resume API
- `waiting_approval`: execution paused until an operator approves or rejects through the OneOps resume API

## External Call Runtime

- external calls only resolve platform-managed `target_ref`
- request and response data are summarized into execution logs and events
```

- [ ] **Step 10: Commit the runtime-migration slice**

```bash
git -C OneOps add app/orchestration boot/provider/api.go boot/provider/service_groups.go initialize/routers.go
git -C OneOps commit -m "feat: route orchestration execution through runtime registry"

git -C docs add runbooks/alert-to-ticket-dagengine-mvp.md
git -C docs commit -m "docs: add orchestration runtime foundation notes"
```

## Spec Coverage Check

- shared runtime foundation: covered by Task 1
- persistent waiting and resumable execution: covered by Task 2 and Task 4
- controlled external call runtime: covered by Task 3
- runtime registry migration for existing nodes: covered by Task 4
- concise logs, events, and structured errors: covered by Task 1 and Task 4
- OneOps-owned target registration and resume APIs: covered by Task 2 and Task 3

## Placeholder Scan

No `TODO`, `TBD`, or deferred placeholders are left in task steps. Every task contains concrete files, code snippets, commands, and expected outputs.

## Type Consistency Check

- shared runtime execution uses `NodeExecutionInput`, `NodeExecutionResult`, `RuntimeError`, `ExecutionEvent`, and `SuspendInstruction`
- callback and approval resumes use `SuspendRecord`, `CallbackResumeReq`, `ApprovalDecisionReq`, and `ResumeResp`
- runtime dispatch always resolves through `Registry.Resolve(nodeType)` and executes via `Middleware.Run(..., runner.Run)`
- external target resolution always goes through `target_registry.Registry.Resolve`
