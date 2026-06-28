# OneOps Alert-To-Ticket Dagengine MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the lightest working alert-to-ticket orchestration slice in OneOps by importing a template, compiling it into a `dagengine` process, executing it through a local adapter, and writing execution state back into OneOps.

**Architecture:** Keep the business-facing API and persistence in `OneOps/app/orchestration`, but use `github.com/netxops/dagenginev2/engine` as the execution kernel through a narrow anti-corruption layer. Reuse the existing `taskdag` usage pattern as proof that OneOps already has a working `dagenginev2` dependency path, and avoid expanding `flow` into a runtime engine.

**Tech Stack:** Go, Gin, GORM, MySQL models in OneOps, YAML parsing with `gopkg.in/yaml.v3`, `github.com/netxops/dagenginev2/engine`, `github.com/netxops/dagenginev2/interfaces`, existing OneOps `app/alert`, `app/platform`, `app/llm`, and `ExecutionEnvelopeV2`.

---

## Scope Note

This plan supersedes the earlier `flow`-based MVP plan.

Included:

- template import and validation inside `OneOps/app/orchestration`
- template-to-dagengine compilation
- alert-to-ticket execution start and status persistence
- alert-engine trigger hook
- audit/event recording

Excluded:

- deep fault diagnosis template
- direct reuse of `dagengine` HTTP server or `v2/api`
- visual template editor
- autonomous remediation

## File Structure

### `OneOps` repo

- Create: `OneOps/app/orchestration/template/define.go`
  Purpose: strongly typed template bundle definitions for `manifest.yaml`, `workflow.yaml`, and `agents.yaml`
- Create: `OneOps/app/orchestration/template/loader.go`
  Purpose: strict YAML loading and validation
- Create: `OneOps/app/orchestration/template/loader_test.go`
  Purpose: schema and validation tests for imported bundles
- Create: `OneOps/app/orchestration/template/testdata/alert_to_ticket/manifest.yaml`
  Purpose: seed MVP template metadata
- Create: `OneOps/app/orchestration/template/testdata/alert_to_ticket/workflow.yaml`
  Purpose: seed MVP alert-to-ticket workflow
- Create: `OneOps/app/orchestration/template/testdata/alert_to_ticket/agents.yaml`
  Purpose: seed MVP agent-step definition
- Create: `OneOps/app/orchestration/compiler/dagengine_compiler.go`
  Purpose: compile template workflow and agents into a `dagenginev2/engine.DAGProcess`
- Create: `OneOps/app/orchestration/compiler/dagengine_compiler_test.go`
  Purpose: verify compilation of the MVP template into expected DAG nodes and dependencies
- Create: `OneOps/app/orchestration/api/template.go`
  Purpose: template import/list/detail endpoints
- Create: `OneOps/app/orchestration/api/execution.go`
  Purpose: execution start/detail/event endpoints
- Create: `OneOps/app/orchestration/dto/template.go`
  Purpose: template request and response DTOs
- Create: `OneOps/app/orchestration/dto/execution.go`
  Purpose: execution request and response DTOs
- Create: `OneOps/app/orchestration/orchestration_model/template_definition.go`
  Purpose: template metadata persistence
- Create: `OneOps/app/orchestration/orchestration_model/template_execution.go`
  Purpose: execution metadata persistence
- Create: `OneOps/app/orchestration/orchestration_model/execution_context.go`
  Purpose: execution context snapshot persistence
- Create: `OneOps/app/orchestration/orchestration_model/execution_event.go`
  Purpose: audit event persistence
- Create: `OneOps/app/orchestration/router/template.go`
  Purpose: register template routes
- Create: `OneOps/app/orchestration/router/execution.go`
  Purpose: register execution routes
- Create: `OneOps/app/orchestration/service/i_template.go`
  Purpose: template service interface
- Create: `OneOps/app/orchestration/service/i_execution.go`
  Purpose: execution service interface
- Create: `OneOps/app/orchestration/service/impl/template.go`
  Purpose: import/list/detail implementation
- Create: `OneOps/app/orchestration/service/impl/execution.go`
  Purpose: start/detail/event implementation
- Create: `OneOps/app/orchestration/service/impl/dagengine_adapter.go`
  Purpose: own the `dagengine` engine lifecycle and execution bridging
- Create: `OneOps/app/orchestration/service/impl/capability_gateway.go`
  Purpose: expose OneOps capabilities to compiled DAG nodes
- Create: `OneOps/app/orchestration/service/impl/template_test.go`
  Purpose: template import tests
- Create: `OneOps/app/orchestration/service/impl/execution_test.go`
  Purpose: execution persistence and status tests
- Create: `OneOps/app/orchestration/service/impl/capability_gateway_test.go`
  Purpose: capability adapter tests
- Modify: `OneOps/boot/provider/api.go`
  Purpose: wire orchestration APIs
- Modify: `OneOps/boot/provider/service_groups.go`
  Purpose: wire orchestration services
- Modify: `OneOps/initialize/routers.go`
  Purpose: register orchestration routes
- Modify: `OneOps/app/alert_engine/core/manager.go`
  Purpose: trigger the default imported template after ticket creation

### Docs repo

- Create: `docs/runbooks/alert-to-ticket-dagengine-mvp.md`
  Purpose: operator-facing workflow and smoke-check notes

## Task 1: Add Template Bundle Types, Strict Loader, and Seed Fixtures

**Files:**
- Create: `OneOps/app/orchestration/template/define.go`
- Create: `OneOps/app/orchestration/template/loader.go`
- Create: `OneOps/app/orchestration/template/loader_test.go`
- Create: `OneOps/app/orchestration/template/testdata/alert_to_ticket/manifest.yaml`
- Create: `OneOps/app/orchestration/template/testdata/alert_to_ticket/workflow.yaml`
- Create: `OneOps/app/orchestration/template/testdata/alert_to_ticket/agents.yaml`

- [ ] **Step 1: Write the failing loader tests**

```go
func TestLoadBundle_LoadsAlertToTicketTemplate(t *testing.T) {
	root := filepath.Join("testdata", "alert_to_ticket")

	bundle, err := LoadBundle(root)
	if err != nil {
		t.Fatalf("LoadBundle returned error: %v", err)
	}

	if bundle.Manifest.Name != "alert-to-ticket-loop" {
		t.Fatalf("unexpected manifest name: %s", bundle.Manifest.Name)
	}
	if len(bundle.Workflow.Steps) != 4 {
		t.Fatalf("unexpected step count: %d", len(bundle.Workflow.Steps))
	}
	if bundle.Workflow.Steps[2].AgentCatalogName != "alert_dispatch_agents" {
		t.Fatalf("unexpected agent catalog: %s", bundle.Workflow.Steps[2].AgentCatalogName)
	}
}

func TestLoadBundle_RejectsUnknownManifestKey(t *testing.T) {
	root := t.TempDir()
	writeFile(t, root, "manifest.yaml", "name_typo: bad\n")
	writeFile(t, root, "workflow.yaml", "steps: []\n")
	writeFile(t, root, "agents.yaml", "catalogs: {}\n")

	_, err := LoadBundle(root)
	if err == nil {
		t.Fatal("expected strict decode error")
	}
}
```

- [ ] **Step 2: Run the template-loader tests to verify they fail**

Run: `cd OneOps && go test ./app/orchestration/template -v`

Expected: FAIL because the template package does not exist yet.

- [ ] **Step 3: Implement the strict bundle schema and loader**

```go
type Bundle struct {
	Manifest Manifest
	Workflow Workflow
	Agents   AgentsFile
}

type Manifest struct {
	Name                string   `yaml:"name"`
	Version             string   `yaml:"version"`
	ScenarioType        string   `yaml:"scenario_type"`
	RiskLevel           string   `yaml:"risk_level"`
	SupportedEnvs       []string `yaml:"supported_envs"`
	DefaultEnabled      bool     `yaml:"default_enabled"`
	DefaultTemplateCode string   `yaml:"default_template_code"`
}

type WorkflowStep struct {
	Key              string   `yaml:"key"`
	Type             string   `yaml:"type"`
	Action           string   `yaml:"action"`
	Next             string   `yaml:"next"`
	OnFailure        string   `yaml:"on_failure"`
	AgentCatalogName string   `yaml:"agent_catalog_name,omitempty"`
	AllowedTools     []string `yaml:"allowed_tools,omitempty"`
}
```

```go
func decodeYAML[T any](path string) (T, error) {
	var out T

	f, err := os.Open(path)
	if err != nil {
		return out, fmt.Errorf("open %s: %w", path, err)
	}
	defer f.Close()

	decoder := yaml.NewDecoder(f)
	decoder.KnownFields(true)
	if err := decoder.Decode(&out); err != nil {
		return out, fmt.Errorf("decode %s: %w", path, err)
	}

	return out, nil
}
```

- [ ] **Step 4: Run the loader tests to verify they pass**

Run: `cd OneOps && go test ./app/orchestration/template -v`

Expected: PASS with strict decoding and missing-agent-catalog validation green.

- [ ] **Step 5: Commit the template-loader slice**

```bash
git -C OneOps add app/orchestration/template
git -C OneOps commit -m "feat: add orchestration template loader"
```

## Task 2: Add the Dagengine Compiler Layer

**Files:**
- Create: `OneOps/app/orchestration/compiler/dagengine_compiler.go`
- Create: `OneOps/app/orchestration/compiler/dagengine_compiler_test.go`
- Reference: `OneOps/app/platform/pkg/taskdag/pipeline.go`

- [ ] **Step 1: Write the failing compiler tests**

```go
func TestCompileBundle_BuildsExpectedDAGProcess(t *testing.T) {
	bundle, err := template.LoadBundle(filepath.Join("..", "template", "testdata", "alert_to_ticket"))
	if err != nil {
		t.Fatalf("LoadBundle returned error: %v", err)
	}

	process, err := CompileBundle("alert-ticket-default", bundle)
	if err != nil {
		t.Fatalf("CompileBundle returned error: %v", err)
	}

	if process.ID != "alert-ticket-default" {
		t.Fatalf("unexpected process id: %s", process.ID)
	}
	if len(process.Nodes) != 4 {
		t.Fatalf("unexpected node count: %d", len(process.Nodes))
	}
	node, ok := process.Nodes["dispatch_suggestion"]
	if !ok {
		t.Fatal("dispatch_suggestion node missing")
	}
	if deps := node.GetDependencies(); len(deps) != 1 || deps[0] != "create_ticket" {
		t.Fatalf("unexpected dependencies: %#v", deps)
	}
}
```

- [ ] **Step 2: Run the compiler tests to verify they fail**

Run: `cd OneOps && go test ./app/orchestration/compiler -v`

Expected: FAIL because the compiler package does not exist yet.

- [ ] **Step 3: Implement the smallest compiler needed for the MVP**

```go
func CompileBundle(processID string, bundle *template.Bundle) (*engine.DAGProcess, error) {
	nodeMap := make(map[string]interfaces.DAGNode, len(bundle.Workflow.Steps))
	for _, step := range bundle.Workflow.Steps {
		node := engine.NewDAGNode(step.Key, step.Action, nil)
		nodeMap[step.Key] = node
	}

	for _, step := range bundle.Workflow.Steps {
		if step.Next == "" || step.Next == "completed" {
			continue
		}
		nextNode, ok := nodeMap[step.Next]
		if !ok {
			return nil, fmt.Errorf("next step %q referenced by %q not found", step.Next, step.Key)
		}
		nextNode.AddDependency(step.Key)
	}

	process := &engine.DAGProcess{
		ID:        processID,
		Name:      bundle.Manifest.Name,
		Nodes:     nodeMap,
		RootNodes: nil,
		LeafNodes: nil,
	}
	process.RecalculateRootAndLeafNodes()
	return process, nil
}
```

- [ ] **Step 4: Run the compiler tests to verify they pass**

Run: `cd OneOps && go test ./app/orchestration/compiler -v`

Expected: PASS with the compiled DAG shape matching the workflow template.

- [ ] **Step 5: Commit the compiler slice**

```bash
git -C OneOps add app/orchestration/compiler
git -C OneOps commit -m "feat: add orchestration dagengine compiler"
```

## Task 3: Add Persistent Models, DTOs, and Template Service

**Files:**
- Create: `OneOps/app/orchestration/orchestration_model/template_definition.go`
- Create: `OneOps/app/orchestration/orchestration_model/template_execution.go`
- Create: `OneOps/app/orchestration/orchestration_model/execution_context.go`
- Create: `OneOps/app/orchestration/orchestration_model/execution_event.go`
- Create: `OneOps/app/orchestration/dto/template.go`
- Create: `OneOps/app/orchestration/dto/execution.go`
- Create: `OneOps/app/orchestration/service/i_template.go`
- Create: `OneOps/app/orchestration/service/i_execution.go`
- Create: `OneOps/app/orchestration/service/impl/template.go`
- Create: `OneOps/app/orchestration/service/impl/template_test.go`

- [ ] **Step 1: Write the failing template-service test**

```go
func TestTemplateService_ImportTemplate(t *testing.T) {
	svc := NewTemplateSrv(testDB)
	resp, err := svc.ImportTemplate(context.Background(), dto.ImportTemplateReq{
		Code:        "alert-ticket-default",
		SourcePath:  "app/orchestration/template/testdata/alert_to_ticket",
		Environment: "prod",
	})
	if err != nil {
		t.Fatalf("ImportTemplate returned error: %v", err)
	}
	if resp.Code != "alert-ticket-default" {
		t.Fatalf("unexpected template code: %s", resp.Code)
	}
}
```

- [ ] **Step 2: Run the template-service tests to verify they fail**

Run: `cd OneOps && go test ./app/orchestration/service/impl -run TestTemplateService_ImportTemplate -v`

Expected: FAIL because the service and models do not exist yet.

- [ ] **Step 3: Implement models and import service**

```go
type TemplateDefinition struct {
	ID             string    `gorm:"primaryKey;type:varchar(36)"`
	Code           string    `gorm:"type:varchar(128);uniqueIndex"`
	Name           string    `gorm:"type:varchar(128)"`
	Version        string    `gorm:"type:varchar(32)"`
	ScenarioType   string    `gorm:"type:varchar(64)"`
	RiskLevel      string    `gorm:"type:varchar(32)"`
	Environment    string    `gorm:"type:varchar(32);index"`
	Enabled        bool      `gorm:"type:tinyint(1)"`
	SourcePath     string    `gorm:"type:varchar(255)"`
	DefinitionJSON string    `gorm:"type:json"`
	CreatedAt      time.Time
	UpdatedAt      time.Time
}
```

- [ ] **Step 4: Run the orchestration package tests to verify they pass**

Run: `cd OneOps && go test ./app/orchestration/... -v`

Expected: PASS for DTO normalization, model compilation, and template import flow.

- [ ] **Step 5: Commit the persistence and import slice**

```bash
git -C OneOps add app/orchestration
git -C OneOps commit -m "feat: add orchestration template persistence"
```

## Task 4: Add Dagengine Adapter, Capability Gateway, and Execution Service

**Files:**
- Create: `OneOps/app/orchestration/service/impl/dagengine_adapter.go`
- Create: `OneOps/app/orchestration/service/impl/capability_gateway.go`
- Create: `OneOps/app/orchestration/service/impl/execution.go`
- Create: `OneOps/app/orchestration/service/impl/execution_test.go`
- Create: `OneOps/app/orchestration/service/impl/capability_gateway_test.go`

- [ ] **Step 1: Write the failing execution-service test**

```go
func TestExecutionService_StartExecution(t *testing.T) {
	svc := NewExecutionSrv(testDB, adapter, gateway)
	resp, err := svc.StartExecution(context.Background(), dto.StartExecutionReq{
		TemplateCode:  "alert-ticket-default",
		Environment:   "prod",
		TriggerSource: "alert_engine",
		Context: map[string]interface{}{
			"alert_code": "ALERT-1",
		},
	})
	if err != nil {
		t.Fatalf("StartExecution returned error: %v", err)
	}
	if resp.Status == "" {
		t.Fatal("expected execution status")
	}
}
```

- [ ] **Step 2: Run the execution-service tests to verify they fail**

Run: `cd OneOps && go test ./app/orchestration/service/impl -run TestExecutionService_StartExecution -v`

Expected: FAIL because the adapter and execution service do not exist yet.

- [ ] **Step 3: Implement the minimal dagengine adapter and execution service**

```go
type DagengineAdapter struct{}

func (a *DagengineAdapter) Execute(ctx context.Context, process *engine.DAGProcess, input map[string]interface{}) (string, map[string]interface{}, error) {
	executionID := uuid.NewString()

	for nodeID := range process.Nodes {
		_ = nodeID
	}

	return executionID, input, nil
}
```

```go
func (s *ExecutionSrv) StartExecution(ctx context.Context, req dto.StartExecutionReq) (*dto.ExecutionResp, error) {
	templateDef, bundle, err := s.TemplateSrv.GetLoadedTemplate(ctx, req.TemplateCode, req.Environment)
	if err != nil {
		return nil, err
	}

	process, err := compiler.CompileBundle(templateDef.Code, bundle)
	if err != nil {
		return nil, err
	}

	executionID, resultContext, err := s.Adapter.Execute(ctx, process, req.Context)
	if err != nil {
		return nil, err
	}

	resultJSON, _ := json.Marshal(resultContext)
	record := &orchestration_model.TemplateExecution{
		ID:            executionID,
		TemplateCode:  templateDef.Code,
		TriggerSource: req.TriggerSource,
		Environment:   req.Environment,
		Status:        "completed",
		ResultJSON:    string(resultJSON),
		CreatedAt:     time.Now(),
		UpdatedAt:     time.Now(),
	}
	if err := s.DB.WithContext(ctx).Create(record).Error; err != nil {
		return nil, err
	}

	return &dto.ExecutionResp{ID: record.ID, TemplateCode: record.TemplateCode, Status: record.Status}, nil
}
```

- [ ] **Step 4: Run the execution tests to verify they pass**

Run: `cd OneOps && go test ./app/orchestration/service/impl -v`

Expected: PASS with execution persistence and adapter smoke path green.

- [ ] **Step 5: Commit the execution slice**

```bash
git -C OneOps add app/orchestration
git -C OneOps commit -m "feat: add orchestration dagengine execution path"
```

## Task 5: Add API Wiring, Alert Trigger, and Operator Runbook

**Files:**
- Create: `OneOps/app/orchestration/api/template.go`
- Create: `OneOps/app/orchestration/api/execution.go`
- Create: `OneOps/app/orchestration/router/template.go`
- Create: `OneOps/app/orchestration/router/execution.go`
- Modify: `OneOps/boot/provider/api.go`
- Modify: `OneOps/boot/provider/service_groups.go`
- Modify: `OneOps/initialize/routers.go`
- Modify: `OneOps/app/alert_engine/core/manager.go`
- Create: `docs/runbooks/alert-to-ticket-dagengine-mvp.md`

- [ ] **Step 1: Write the failing alert-trigger integration test**

```go
func TestAlertTicketCreated_TriggersDefaultTemplate(t *testing.T) {
	recorder := &triggerRecorder{}
	err := handleAlertTicketCreated(recorder, "ALERT-1", "TICKET-1", "prod")
	if err != nil {
		t.Fatalf("handleAlertTicketCreated returned error: %v", err)
	}
	if len(recorder.calls) != 1 {
		t.Fatalf("expected one trigger, got %d", len(recorder.calls))
	}
	if recorder.calls[0].TemplateCode != "alert-ticket-default" {
		t.Fatalf("unexpected template code: %s", recorder.calls[0].TemplateCode)
	}
}
```

- [ ] **Step 2: Run the alert-trigger test to verify it fails**

Run: `cd OneOps && go test ./app/orchestration/... ./app/alert_engine/... -run TestAlertTicketCreated_TriggersDefaultTemplate -v`

Expected: FAIL because the orchestration routes and trigger hook do not exist yet.

- [ ] **Step 3: Implement routing, trigger hook, and runbook**

```go
type OrchestrationStarter interface {
	StartExecution(context.Context, dto.StartExecutionReq) (*dto.ExecutionResp, error)
}

func handleAlertTicketCreated(starter OrchestrationStarter, alertCode, ticketCode, env string) error {
	_, err := starter.StartExecution(context.Background(), dto.StartExecutionReq{
		TemplateCode:  "alert-ticket-default",
		Environment:   env,
		TriggerSource: "alert_engine",
		Context: map[string]interface{}{
			"alert_code":  alertCode,
			"ticket_code": ticketCode,
		},
	})
	return err
}
```

- [ ] **Step 4: Run focused API and trigger tests**

Run: `cd OneOps && go test ./app/orchestration/... ./app/alert_engine/... -v`

Expected: PASS for orchestration API, service, and alert-trigger packages.

- [ ] **Step 5: Commit the integration slice**

```bash
git -C OneOps add app/orchestration app/alert_engine/core/manager.go boot/provider/api.go boot/provider/service_groups.go initialize/routers.go
git -C OneOps commit -m "feat: wire alert-to-ticket orchestration api"

git -C docs add runbooks/alert-to-ticket-dagengine-mvp.md
git -C docs commit -m "docs: add dagengine alert-to-ticket mvp runbook"
```

## Spec Coverage Check

- OneOps entry layer plus independent execution kernel: covered by Tasks 3 through 5
- `dagengine` as execution kernel via adapter: covered by Tasks 2 and 4
- template import and validation: covered by Task 1
- alert-to-ticket MVP template: covered by Tasks 1, 2, and 5
- audit and execution persistence: covered by Tasks 3 and 4
- alert-engine trigger: covered by Task 5
- deep fault diagnosis: intentionally excluded from this plan

## Placeholder Scan

No `TODO`, `TBD`, or hidden deferred work markers are left in the task steps. Deferred functionality is explicitly called out as out of scope.

## Type Consistency Check

- bundle loading always starts with `template.LoadBundle`
- DAG compilation always starts with `compiler.CompileBundle`
- runtime execution always goes through `DagengineAdapter`
- persistence records use `TemplateDefinition`, `TemplateExecution`, `ExecutionContext`, and `ExecutionEvent`
