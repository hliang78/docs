# OneOps Alert-To-Ticket Orchestration MVP Implementation Plan

> **Superseded:** This plan has been replaced by `2026-06-26-oneops-alert-to-ticket-dagengine-mvp-plan.md` after confirming `dagengine` is the better phase 1 execution kernel.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the lightest working slice of the approved orchestration framework by running one reusable `Alert-To-Ticket Loop` template end to end through OneOps.

**Architecture:** Keep the kernel logic in the `flow` repo as a new `app/orchestration` package instead of rewriting the legacy AST/conversion code. Expose that kernel through a thin `OneOps/app/orchestration` module that imports templates, starts executions, calls existing OneOps capabilities, and returns execution status. Delay the deep-fault-diagnosis template and any separate deployment split until this slice is stable.

**Tech Stack:** Go, Gin, GORM, MySQL models in OneOps, YAML parsing with `gopkg.in/yaml.v3`, existing OneOps `app/flow`, `app/alert`, `app/platform`, `app/llm`, and `ExecutionEnvelopeV2`.

---

## Scope Note

This plan intentionally implements only the first MVP slice from the approved spec:

- included: template import, template execution, alert trigger, ticket update, audit trail, one official `Alert-To-Ticket Loop` template
- excluded: deep diagnosis template, visual template editor, separate orchestrator deployment, advanced memory, high-risk autonomous remediation

## File Structure

### `flow` repo

- Create: `flow/app/orchestration/define/template.go`
  Purpose: strongly typed bundle definitions for `manifest.yaml`, `workflow.yaml`, and `agents.yaml`
- Create: `flow/app/orchestration/loader/loader.go`
  Purpose: load and validate bundle files from disk
- Create: `flow/app/orchestration/loader/loader_test.go`
  Purpose: schema and validation tests for bundle loading
- Create: `flow/app/orchestration/engine/engine.go`
  Purpose: run `flow_step` and `agent_step` nodes with deterministic state transitions
- Create: `flow/app/orchestration/engine/engine_test.go`
  Purpose: unit tests for state transitions, retries, and terminal states
- Create: `flow/app/orchestration/gateway/types.go`
  Purpose: narrow capability interfaces that the kernel calls
- Create: `flow/app/orchestration/agent/runner.go`
  Purpose: minimal agent-step contract with bounded rounds and timeout
- Create: `flow/app/orchestration/testdata/alert_to_ticket/manifest.yaml`
  Purpose: seed MVP template metadata
- Create: `flow/app/orchestration/testdata/alert_to_ticket/workflow.yaml`
  Purpose: seed MVP outer workflow definition
- Create: `flow/app/orchestration/testdata/alert_to_ticket/agents.yaml`
  Purpose: seed MVP agent-step definition

### `OneOps` repo

- Create: `OneOps/app/orchestration/api/template.go`
  Purpose: template import/list/detail endpoints
- Create: `OneOps/app/orchestration/api/execution.go`
  Purpose: start/detail/event endpoints for the MVP slice
- Create: `OneOps/app/orchestration/dto/template.go`
  Purpose: request and response DTOs for templates
- Create: `OneOps/app/orchestration/dto/execution.go`
  Purpose: request and response DTOs for executions
- Create: `OneOps/app/orchestration/orchestration_model/template_definition.go`
  Purpose: persistent template metadata
- Create: `OneOps/app/orchestration/orchestration_model/template_execution.go`
  Purpose: persistent execution metadata
- Create: `OneOps/app/orchestration/orchestration_model/execution_context.go`
  Purpose: execution context snapshot storage
- Create: `OneOps/app/orchestration/orchestration_model/execution_event.go`
  Purpose: audit event storage
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
  Purpose: start/query/event implementation for the MVP slice
- Create: `OneOps/app/orchestration/service/impl/kernel_adapter.go`
  Purpose: bridge OneOps execution requests to the `flow` orchestration engine
- Create: `OneOps/app/orchestration/service/impl/capability_gateway.go`
  Purpose: implement kernel capability interfaces with OneOps services
- Create: `OneOps/app/orchestration/service/impl/template_test.go`
  Purpose: template import tests
- Create: `OneOps/app/orchestration/service/impl/execution_test.go`
  Purpose: execution and audit tests
- Create: `OneOps/app/orchestration/service/impl/capability_gateway_test.go`
  Purpose: adapter tests against alert/ticket/task abstractions
- Modify: `OneOps/boot/provider/api.go`
  Purpose: wire new orchestration APIs
- Modify: `OneOps/boot/provider/service_groups.go`
  Purpose: wire new orchestration services
- Modify: `OneOps/initialize/routers.go`
  Purpose: register orchestration routes
- Modify: `OneOps/app/alert_engine/core/manager.go`
  Purpose: add lightweight trigger hook that can start the default template after ticket creation

### Docs and fixtures

- Create: `docs/runbooks/alert-to-ticket-mvp-template.md`
  Purpose: operator-facing explanation of the template flow

## Task 1: Add Kernel Bundle Types and Loader

**Files:**
- Create: `flow/app/orchestration/define/template.go`
- Create: `flow/app/orchestration/loader/loader.go`
- Create: `flow/app/orchestration/loader/loader_test.go`
- Create: `flow/app/orchestration/testdata/alert_to_ticket/manifest.yaml`
- Create: `flow/app/orchestration/testdata/alert_to_ticket/workflow.yaml`
- Create: `flow/app/orchestration/testdata/alert_to_ticket/agents.yaml`
- Modify: `flow/go.mod`

- [ ] **Step 1: Write the failing loader tests**

```go
package loader_test

import (
	"path/filepath"
	"testing"

	"flow/app/orchestration/loader"
)

func TestLoadBundle_SucceedsForAlertToTicketTemplate(t *testing.T) {
	root := filepath.Join("..", "testdata", "alert_to_ticket")

	bundle, err := loader.LoadBundle(root)
	if err != nil {
		t.Fatalf("LoadBundle returned error: %v", err)
	}

	if bundle.Manifest.Name != "alert-to-ticket-loop" {
		t.Fatalf("unexpected manifest name: %s", bundle.Manifest.Name)
	}
	if len(bundle.Workflow.Steps) == 0 {
		t.Fatal("expected workflow steps")
	}
	if len(bundle.Agents.Agents) == 0 {
		t.Fatal("expected agent definitions")
	}
}

func TestLoadBundle_FailsWhenWorkflowReferencesMissingAgent(t *testing.T) {
	root := filepath.Join("testdata", "broken_missing_agent")

	_, err := loader.LoadBundle(root)
	if err == nil {
		t.Fatal("expected validation error")
	}
}
```

- [ ] **Step 2: Run the flow loader tests to verify they fail**

Run: `cd flow && go test ./app/orchestration/loader -v`

Expected: FAIL with package or symbol errors because the orchestration loader package does not exist yet.

- [ ] **Step 3: Implement bundle structs, loader, and seed YAML**

```go
package define

type Bundle struct {
	Manifest Manifest
	Workflow Workflow
	Agents   AgentCatalog
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

type Workflow struct {
	Steps []WorkflowStep `yaml:"steps"`
}

type WorkflowStep struct {
	Key              string   `yaml:"key"`
	Type             string   `yaml:"type"`
	Action           string   `yaml:"action"`
	Next             string   `yaml:"next"`
	OnFailure        string   `yaml:"on_failure"`
	AgentCatalogName string   `yaml:"agent_catalog_name"`
	AllowedTools     []string `yaml:"allowed_tools"`
}

type AgentCatalog struct {
	Agents []AgentDefinition `yaml:"agents"`
}

type AgentDefinition struct {
	Name    string   `yaml:"name"`
	Role    string   `yaml:"role"`
	Tools   []string `yaml:"tools"`
	Timeout int      `yaml:"timeout_seconds"`
}
```

```go
package loader

import (
	"fmt"
	"os"
	"path/filepath"

	"flow/app/orchestration/define"
	"gopkg.in/yaml.v3"
)

func LoadBundle(root string) (*define.Bundle, error) {
	bundle := &define.Bundle{}
	if err := loadYAML(filepath.Join(root, "manifest.yaml"), &bundle.Manifest); err != nil {
		return nil, err
	}
	if err := loadYAML(filepath.Join(root, "workflow.yaml"), &bundle.Workflow); err != nil {
		return nil, err
	}
	if err := loadYAML(filepath.Join(root, "agents.yaml"), &bundle.Agents); err != nil {
		return nil, err
	}
	if err := validateBundle(bundle); err != nil {
		return nil, err
	}
	return bundle, nil
}

func loadYAML(path string, out interface{}) error {
	data, err := os.ReadFile(path)
	if err != nil {
		return fmt.Errorf("read %s: %w", path, err)
	}
	if err := yaml.Unmarshal(data, out); err != nil {
		return fmt.Errorf("decode %s: %w", path, err)
	}
	return nil
}
```

```yaml
name: alert-to-ticket-loop
version: 0.1.0
scenario_type: alert_to_ticket
risk_level: low
supported_envs:
  - dev
  - test
  - prod
default_enabled: true
default_template_code: alert-ticket-default
```

```yaml
steps:
  - key: deduplicate_alert
    type: flow_step
    action: deduplicate_alert
    next: create_ticket
    on_failure: failed
  - key: create_ticket
    type: flow_step
    action: create_ticket
    next: dispatch_suggestion
    on_failure: failed
  - key: dispatch_suggestion
    type: agent_step
    action: generate_dispatch_suggestion
    agent_catalog_name: alert_dispatch_agents
    next: close_ticket
    on_failure: escalated
  - key: close_ticket
    type: flow_step
    action: close_ticket
    next: completed
    on_failure: failed
```

- [ ] **Step 4: Run the loader tests to verify they pass**

Run: `cd flow && go test ./app/orchestration/loader -v`

Expected: PASS with both bundle-loading tests green.

- [ ] **Step 5: Commit the loader slice**

```bash
git -C flow add go.mod app/orchestration
git -C flow commit -m "feat: add orchestration bundle loader"
```

## Task 2: Add Minimal Kernel Execution Engine

**Files:**
- Create: `flow/app/orchestration/engine/engine.go`
- Create: `flow/app/orchestration/engine/engine_test.go`
- Create: `flow/app/orchestration/gateway/types.go`
- Create: `flow/app/orchestration/agent/runner.go`

- [ ] **Step 1: Write failing execution-engine tests**

```go
package engine_test

import (
	"context"
	"testing"

	"flow/app/orchestration/define"
	"flow/app/orchestration/engine"
)

func TestRun_CompletesAlertToTicketWorkflow(t *testing.T) {
	bundle := &define.Bundle{
		Workflow: define.Workflow{
			Steps: []define.WorkflowStep{
				{Key: "create_ticket", Type: "flow_step", Action: "create_ticket", Next: "dispatch"},
				{Key: "dispatch", Type: "agent_step", Action: "generate_dispatch_suggestion", AgentCatalogName: "alert_dispatch_agents", Next: "completed"},
			},
		},
	}

	runner := engine.New(engine.Dependencies{
		FlowExecutor:  engine.StaticFlowExecutor(nil),
		AgentExecutor: engine.StaticAgentExecutor(map[string]interface{}{"owner": "noc-a"}),
	})

	result, err := runner.Run(context.Background(), bundle, map[string]interface{}{"alert_code": "A-1"})
	if err != nil {
		t.Fatalf("Run returned error: %v", err)
	}
	if result.Status != "completed" {
		t.Fatalf("unexpected status: %s", result.Status)
	}
	if result.Context["owner"] != "noc-a" {
		t.Fatalf("expected owner to be set, got %#v", result.Context["owner"])
	}
}

func TestRun_EscalatesOnAgentFailure(t *testing.T) {
	bundle := &define.Bundle{
		Workflow: define.Workflow{
			Steps: []define.WorkflowStep{
				{Key: "dispatch", Type: "agent_step", Action: "generate_dispatch_suggestion", AgentCatalogName: "alert_dispatch_agents", OnFailure: "escalated"},
			},
		},
	}

	runner := engine.New(engine.Dependencies{
		AgentExecutor: engine.FailingAgentExecutor("timeout"),
	})

	result, err := runner.Run(context.Background(), bundle, map[string]interface{}{})
	if err != nil {
		t.Fatalf("Run returned error: %v", err)
	}
	if result.Status != "escalated" {
		t.Fatalf("expected escalated status, got %s", result.Status)
	}
}
```

- [ ] **Step 2: Run the engine tests to verify they fail**

Run: `cd flow && go test ./app/orchestration/engine -v`

Expected: FAIL because the engine package and executor shims do not exist yet.

- [ ] **Step 3: Implement the smallest useful engine**

```go
package engine

import (
	"context"
	"fmt"

	"flow/app/orchestration/define"
)

type FlowExecutor interface {
	Execute(context.Context, string, map[string]interface{}) (map[string]interface{}, error)
}

type AgentExecutor interface {
	Execute(context.Context, string, map[string]interface{}) (map[string]interface{}, error)
}

type Dependencies struct {
	FlowExecutor  FlowExecutor
	AgentExecutor AgentExecutor
}

type Result struct {
	Status  string
	Context map[string]interface{}
	Events  []string
}

type Engine struct {
	deps Dependencies
}

func New(deps Dependencies) *Engine {
	return &Engine{deps: deps}
}

func (e *Engine) Run(ctx context.Context, bundle *define.Bundle, seed map[string]interface{}) (*Result, error) {
	state := cloneContext(seed)
	result := &Result{Status: "running", Context: state}
	steps := make(map[string]define.WorkflowStep, len(bundle.Workflow.Steps))
	for _, step := range bundle.Workflow.Steps {
		steps[step.Key] = step
	}
	current := bundle.Workflow.Steps[0].Key
	for current != "" && current != "completed" {
		step := steps[current]
		var (
			output map[string]interface{}
			err    error
		)
		switch step.Type {
		case "flow_step":
			output, err = e.deps.FlowExecutor.Execute(ctx, step.Action, state)
		case "agent_step":
			output, err = e.deps.AgentExecutor.Execute(ctx, step.Action, state)
		default:
			return nil, fmt.Errorf("unsupported step type: %s", step.Type)
		}
		if err != nil {
			result.Status = fallbackStatus(step.OnFailure)
			return result, nil
		}
		mergeContext(state, output)
		current = step.Next
	}
	result.Status = "completed"
	return result, nil
}
```

- [ ] **Step 4: Run the engine tests to verify they pass**

Run: `cd flow && go test ./app/orchestration/engine -v`

Expected: PASS with completion and escalation cases green.

- [ ] **Step 5: Commit the execution engine slice**

```bash
git -C flow add app/orchestration/engine app/orchestration/gateway app/orchestration/agent
git -C flow commit -m "feat: add orchestration execution engine"
```

## Task 3: Add OneOps Persistent Models and Service Interfaces

**Files:**
- Create: `OneOps/app/orchestration/orchestration_model/template_definition.go`
- Create: `OneOps/app/orchestration/orchestration_model/template_execution.go`
- Create: `OneOps/app/orchestration/orchestration_model/execution_context.go`
- Create: `OneOps/app/orchestration/orchestration_model/execution_event.go`
- Create: `OneOps/app/orchestration/service/i_template.go`
- Create: `OneOps/app/orchestration/service/i_execution.go`
- Create: `OneOps/app/orchestration/dto/template.go`
- Create: `OneOps/app/orchestration/dto/execution.go`
- Create: `OneOps/app/orchestration/service/impl/template_test.go`

- [ ] **Step 1: Write failing model and DTO tests**

```go
package impl_test

import (
	"testing"

	orchestrationDTO "github.com/netxops/OneOps/app/orchestration/dto"
)

func TestImportTemplateReq_Normalize(t *testing.T) {
	req := orchestrationDTO.ImportTemplateReq{
		Code:        " alert-ticket-default ",
		SourcePath:  " flow/app/orchestration/testdata/alert_to_ticket ",
		Environment: " prod ",
	}

	req.Normalize()

	if req.Code != "alert-ticket-default" {
		t.Fatalf("unexpected code: %q", req.Code)
	}
	if req.Environment != "prod" {
		t.Fatalf("unexpected env: %q", req.Environment)
	}
}
```

- [ ] **Step 2: Run the OneOps orchestration DTO test to verify it fails**

Run: `cd OneOps && go test ./app/orchestration/... -run TestImportTemplateReq_Normalize -v`

Expected: FAIL because the orchestration package tree does not exist yet.

- [ ] **Step 3: Implement the minimal persistent types and interfaces**

```go
package orchestration_model

import "time"

type TemplateDefinition struct {
	ID                string    `gorm:"primaryKey;type:varchar(36)"`
	Code              string    `gorm:"type:varchar(128);uniqueIndex"`
	Name              string    `gorm:"type:varchar(128)"`
	Version           string    `gorm:"type:varchar(32)"`
	ScenarioType      string    `gorm:"type:varchar(64)"`
	RiskLevel         string    `gorm:"type:varchar(32)"`
	Environment       string    `gorm:"type:varchar(32);index"`
	Enabled           bool      `gorm:"type:tinyint(1)"`
	BundlePath        string    `gorm:"type:varchar(255)"`
	DefinitionJSON    string    `gorm:"type:json"`
	CreatedAt         time.Time
	UpdatedAt         time.Time
}

type TemplateExecution struct {
	ID             string    `gorm:"primaryKey;type:varchar(36)"`
	TemplateCode   string    `gorm:"type:varchar(128);index"`
	TriggerSource  string    `gorm:"type:varchar(64)"`
	Environment    string    `gorm:"type:varchar(32)"`
	Status         string    `gorm:"type:varchar(32);index"`
	CurrentStepKey string    `gorm:"type:varchar(128)"`
	ResultJSON     string    `gorm:"type:json"`
	CreatedAt      time.Time
	UpdatedAt      time.Time
}
```

```go
package dto

import "strings"

type ImportTemplateReq struct {
	Code        string `json:"code"`
	SourcePath  string `json:"source_path"`
	Environment string `json:"environment"`
}

func (r *ImportTemplateReq) Normalize() {
	r.Code = strings.TrimSpace(r.Code)
	r.SourcePath = strings.TrimSpace(r.SourcePath)
	r.Environment = strings.TrimSpace(r.Environment)
}
```

- [ ] **Step 4: Run the OneOps orchestration package tests to verify they pass**

Run: `cd OneOps && go test ./app/orchestration/... -v`

Expected: PASS for DTO normalization and package compilation.

- [ ] **Step 5: Commit the model/interface slice**

```bash
git -C OneOps add app/orchestration
git -C OneOps commit -m "feat: add orchestration models and interfaces"
```

## Task 4: Implement Template Import and Kernel Adapter

**Files:**
- Create: `OneOps/app/orchestration/service/impl/template.go`
- Create: `OneOps/app/orchestration/service/impl/kernel_adapter.go`
- Create: `OneOps/app/orchestration/api/template.go`
- Create: `OneOps/app/orchestration/router/template.go`
- Modify: `OneOps/boot/provider/api.go`
- Modify: `OneOps/boot/provider/service_groups.go`
- Modify: `OneOps/initialize/routers.go`
- Test: `OneOps/app/orchestration/service/impl/template_test.go`

- [ ] **Step 1: Write the failing template import test**

```go
package impl_test

import (
	"context"
	"testing"

	orchestrationDTO "github.com/netxops/OneOps/app/orchestration/dto"
	"github.com/netxops/OneOps/app/orchestration/service/impl"
)

func TestTemplateService_ImportTemplate(t *testing.T) {
	svc := impl.NewTemplateSrv(nil)
	req := orchestrationDTO.ImportTemplateReq{
		Code:        "alert-ticket-default",
		SourcePath:  "../flow/app/orchestration/testdata/alert_to_ticket",
		Environment: "prod",
	}

	_, err := svc.ImportTemplate(context.Background(), req)
	if err != nil {
		t.Fatalf("ImportTemplate returned error: %v", err)
	}
}
```

- [ ] **Step 2: Run the template import test to verify it fails**

Run: `cd OneOps && go test ./app/orchestration/service/impl -run TestTemplateService_ImportTemplate -v`

Expected: FAIL because `NewTemplateSrv` and kernel-loading support do not exist yet.

- [ ] **Step 3: Implement the import path through a kernel adapter**

```go
package impl

import (
	"context"
	"encoding/json"
	"time"

	"github.com/google/uuid"
	orchestrationDTO "github.com/netxops/OneOps/app/orchestration/dto"
	orchestrationModel "github.com/netxops/OneOps/app/orchestration/orchestration_model"
	"gorm.io/gorm"

	kernelLoader "flow/app/orchestration/loader"
)

type TemplateSrv struct {
	DB *gorm.DB
}

func NewTemplateSrv(db *gorm.DB) *TemplateSrv {
	return &TemplateSrv{DB: db}
}

func (s *TemplateSrv) ImportTemplate(ctx context.Context, req orchestrationDTO.ImportTemplateReq) (*orchestrationDTO.TemplateResp, error) {
	req.Normalize()
	bundle, err := kernelLoader.LoadBundle(req.SourcePath)
	if err != nil {
		return nil, err
	}

	definitionJSON, err := json.Marshal(bundle)
	if err != nil {
		return nil, err
	}

	record := &orchestrationModel.TemplateDefinition{
		ID:             uuid.NewString(),
		Code:           req.Code,
		Name:           bundle.Manifest.Name,
		Version:        bundle.Manifest.Version,
		ScenarioType:   bundle.Manifest.ScenarioType,
		RiskLevel:      bundle.Manifest.RiskLevel,
		Environment:    req.Environment,
		Enabled:        true,
		BundlePath:     req.SourcePath,
		DefinitionJSON: string(definitionJSON),
		CreatedAt:      time.Now(),
		UpdatedAt:      time.Now(),
	}
	if err := s.DB.WithContext(ctx).Save(record).Error; err != nil {
		return nil, err
	}

	return &orchestrationDTO.TemplateResp{
		Code:        record.Code,
		Name:        record.Name,
		Version:     record.Version,
		Environment: record.Environment,
		Enabled:     record.Enabled,
	}, nil
}
```

- [ ] **Step 4: Run template-service tests and OneOps package tests**

Run: `cd OneOps && go test ./app/orchestration/... -v`

Expected: PASS with template import path compiling and import test green.

- [ ] **Step 5: Commit the import/API wiring slice**

```bash
git -C OneOps add app/orchestration boot/provider/api.go boot/provider/service_groups.go initialize/routers.go
git -C OneOps commit -m "feat: add orchestration template import api"
```

## Task 5: Implement Execution Start, Audit Trail, and Capability Gateway

**Files:**
- Create: `OneOps/app/orchestration/service/impl/execution.go`
- Create: `OneOps/app/orchestration/service/impl/capability_gateway.go`
- Create: `OneOps/app/orchestration/api/execution.go`
- Create: `OneOps/app/orchestration/router/execution.go`
- Create: `OneOps/app/orchestration/service/impl/execution_test.go`
- Create: `OneOps/app/orchestration/service/impl/capability_gateway_test.go`

- [ ] **Step 1: Write the failing execution-service test**

```go
package impl_test

import (
	"context"
	"testing"

	orchestrationDTO "github.com/netxops/OneOps/app/orchestration/dto"
	"github.com/netxops/OneOps/app/orchestration/service/impl"
)

func TestExecutionService_StartExecution(t *testing.T) {
	svc := impl.NewExecutionSrv(nil, nil, nil)
	req := orchestrationDTO.StartExecutionReq{
		TemplateCode: "alert-ticket-default",
		Environment:  "prod",
		TriggerSource: "alert_engine",
		Context: map[string]interface{}{
			"alert_code": "ALERT-1",
		},
	}

	resp, err := svc.StartExecution(context.Background(), req)
	if err != nil {
		t.Fatalf("StartExecution returned error: %v", err)
	}
	if resp.Status != "completed" {
		t.Fatalf("unexpected status: %s", resp.Status)
	}
}
```

- [ ] **Step 2: Run the execution-service test to verify it fails**

Run: `cd OneOps && go test ./app/orchestration/service/impl -run TestExecutionService_StartExecution -v`

Expected: FAIL because execution service and gateway wiring do not exist yet.

- [ ] **Step 3: Implement execution service, gateway, and audit writes**

```go
package impl

import (
	"context"
	"encoding/json"
	"time"

	"github.com/google/uuid"
	orchestrationDTO "github.com/netxops/OneOps/app/orchestration/dto"
	orchestrationModel "github.com/netxops/OneOps/app/orchestration/orchestration_model"
	kernelDefine "flow/app/orchestration/define"
	kernelEngine "flow/app/orchestration/engine"
	"gorm.io/gorm"
)

type ExecutionSrv struct {
	DB      *gorm.DB
	Kernel  *KernelAdapter
	Gateway *CapabilityGateway
}

func NewExecutionSrv(db *gorm.DB, kernel *KernelAdapter, gateway *CapabilityGateway) *ExecutionSrv {
	return &ExecutionSrv{DB: db, Kernel: kernel, Gateway: gateway}
}

func (s *ExecutionSrv) StartExecution(ctx context.Context, req orchestrationDTO.StartExecutionReq) (*orchestrationDTO.ExecutionResp, error) {
	template, bundle, err := s.Kernel.LoadTemplate(ctx, req.TemplateCode, req.Environment)
	if err != nil {
		return nil, err
	}

	engine := kernelEngine.New(kernelEngine.Dependencies{
		FlowExecutor:  s.Gateway,
		AgentExecutor: s.Gateway,
	})

	result, err := engine.Run(ctx, &kernelDefine.Bundle{
		Manifest: bundle.Manifest,
		Workflow: bundle.Workflow,
		Agents:   bundle.Agents,
	}, req.Context)
	if err != nil {
		return nil, err
	}

	resultJSON, _ := json.Marshal(result.Context)
	execution := &orchestrationModel.TemplateExecution{
		ID:             uuid.NewString(),
		TemplateCode:   template.Code,
		TriggerSource:  req.TriggerSource,
		Environment:    req.Environment,
		Status:         result.Status,
		CurrentStepKey: "",
		ResultJSON:     string(resultJSON),
		CreatedAt:      time.Now(),
		UpdatedAt:      time.Now(),
	}
	if err := s.DB.WithContext(ctx).Create(execution).Error; err != nil {
		return nil, err
	}

	return &orchestrationDTO.ExecutionResp{
		ID:           execution.ID,
		TemplateCode: execution.TemplateCode,
		Status:       execution.Status,
	}, nil
}
```

- [ ] **Step 4: Run execution and gateway tests to verify they pass**

Run: `cd OneOps && go test ./app/orchestration/... -v`

Expected: PASS with execution start, audit persistence, and gateway fakes green.

- [ ] **Step 5: Commit the execution slice**

```bash
git -C OneOps add app/orchestration
git -C OneOps commit -m "feat: add orchestration execution service"
```

## Task 6: Wire Alert Trigger and Default Template Behavior

**Files:**
- Modify: `OneOps/app/alert_engine/core/manager.go`
- Create: `docs/runbooks/alert-to-ticket-mvp-template.md`
- Test: `OneOps/app/orchestration/service/impl/execution_test.go`

- [ ] **Step 1: Write the failing alert-trigger integration test**

```go
package impl_test

import (
	"context"
	"testing"

	orchestrationDTO "github.com/netxops/OneOps/app/orchestration/dto"
)

type triggerRecorder struct {
	calls []orchestrationDTO.StartExecutionReq
}

func (r *triggerRecorder) StartExecution(_ context.Context, req orchestrationDTO.StartExecutionReq) (*orchestrationDTO.ExecutionResp, error) {
	r.calls = append(r.calls, req)
	return &orchestrationDTO.ExecutionResp{ID: "exec-1", Status: "completed"}, nil
}

func TestAlertCallback_TriggersDefaultTemplate(t *testing.T) {
	recorder := &triggerRecorder{}
	err := handleAlertTicketCreated(recorder, "ALERT-1", "TICKET-1", "prod")
	if err != nil {
		t.Fatalf("handleAlertTicketCreated returned error: %v", err)
	}
	if len(recorder.calls) != 1 {
		t.Fatalf("expected one execution trigger, got %d", len(recorder.calls))
	}
	if recorder.calls[0].TemplateCode != "alert-ticket-default" {
		t.Fatalf("unexpected template code: %s", recorder.calls[0].TemplateCode)
	}
}
```

- [ ] **Step 2: Run the alert-trigger integration test to verify it fails**

Run: `cd OneOps && go test ./app/orchestration/... -run TestAlertCallback_TriggersDefaultTemplate -v`

Expected: FAIL because the callback helper and alert-engine hook do not exist yet.

- [ ] **Step 3: Add the minimal alert-engine hook and operator runbook**

```go
package core

import (
	"context"

	orchestrationDTO "github.com/netxops/OneOps/app/orchestration/dto"
)

type OrchestrationStarter interface {
	StartExecution(context.Context, orchestrationDTO.StartExecutionReq) (*orchestrationDTO.ExecutionResp, error)
}

func handleAlertTicketCreated(starter OrchestrationStarter, alertCode, ticketCode, env string) error {
	_, err := starter.StartExecution(context.Background(), orchestrationDTO.StartExecutionReq{
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

```markdown
# Alert-To-Ticket MVP Template

1. Alert engine creates or updates the source alert ticket.
2. OneOps orchestration starts template `alert-ticket-default`.
3. The kernel runs `deduplicate_alert`, `create_ticket`, `dispatch_suggestion`, and `close_ticket`.
4. Every transition is written to execution events for audit and troubleshooting.
5. If the agent step times out or fails, the execution enters `escalated`.
```

- [ ] **Step 4: Run the focused tests and one broad smoke test**

Run: `cd OneOps && go test ./app/orchestration/... ./app/alert_engine/... -v`

Expected: PASS with the alert trigger helper and orchestration integration tests green.

Run: `cd flow && go test ./app/orchestration/... -v`

Expected: PASS with the kernel bundle and engine tests still green.

- [ ] **Step 5: Commit the end-to-end MVP slice**

```bash
git -C OneOps add app/alert_engine/core/manager.go app/orchestration
git -C OneOps commit -m "feat: trigger alert-to-ticket orchestration mvp"

git -C docs add runbooks/alert-to-ticket-mvp-template.md
git -C docs commit -m "docs: add alert-to-ticket mvp runbook"
```

## Task 7: Add Regression Checks and Manual Verification Notes

**Files:**
- Modify: `docs/runbooks/alert-to-ticket-mvp-template.md`
- Test: `OneOps/app/orchestration/service/impl/execution_test.go`

- [ ] **Step 1: Add a failing regression test for escalated terminal state**

```go
func TestNormalizeTerminalStatus_PreservesEscalated(t *testing.T) {
	if got := impl.NormalizeTerminalStatus("escalated"); got != "escalated" {
		t.Fatalf("expected escalated, got %s", got)
	}
	if got := impl.NormalizeTerminalStatus(""); got != "failed" {
		t.Fatalf("expected failed fallback, got %s", got)
	}
}
```

- [ ] **Step 2: Run the regression test to verify it fails**

Run: `cd OneOps && go test ./app/orchestration/service/impl -run TestExecutionService_PersistsEscalatedStatus -v`

Expected: FAIL until the service persists non-success terminal states correctly.

- [ ] **Step 3: Persist terminal status through a small helper and document the manual smoke path**

```go
func NormalizeTerminalStatus(status string) string {
	if status == "" {
		return "failed"
	}
	return status
}

execution.Status = NormalizeTerminalStatus(result.Status)
if err := s.DB.WithContext(ctx).Save(execution).Error; err != nil {
	return nil, err
}
```

```markdown
## Manual smoke check

1. Import the seed template through `POST /api/orchestration/templates/import`.
2. Create a synthetic alert that produces an alert ticket.
3. Confirm the execution record reaches `completed` or `escalated`.
4. Open the execution detail page and verify the stored context contains `alert_code` and `ticket_code`.
5. Review execution events to confirm the `dispatch_suggestion` step is present.
```

- [ ] **Step 4: Run the full orchestration test suites**

Run: `cd flow && go test ./app/orchestration/... ./...`

Expected: PASS for the new orchestration packages; if unrelated legacy tests fail, capture that separately and rerun the focused package set.

Run: `cd OneOps && go test ./app/orchestration/... ./app/alert_engine/...`

Expected: PASS for the orchestration and alert-trigger packages.

- [ ] **Step 5: Commit the regression hardening slice**

```bash
git -C OneOps add app/orchestration
git -C OneOps commit -m "test: harden alert-to-ticket orchestration mvp"

git -C docs add runbooks/alert-to-ticket-mvp-template.md
git -C docs commit -m "docs: extend alert-to-ticket mvp smoke checks"
```

## Spec Coverage Check

- approved lightweight MVP shape: covered by Tasks 1 through 7
- template bundle with `manifest/workflow/agents`: covered by Task 1
- outer state machine plus inner agent step: covered by Task 2
- persistent template/execution/context/event records: covered by Tasks 3 and 5
- narrowed MVP surface of import/start/query/event: covered by Tasks 3 through 7
- OneOps integration layer and alert trigger: covered by Tasks 4 through 6
- audit and escalated safety path: covered by Tasks 5 and 7
- official `Alert-To-Ticket Loop` template: covered by Tasks 1 and 6
- deep fault diagnosis template: intentionally excluded from this plan and should get its own follow-up plan

## Placeholder Scan

No `TODO`, `TBD`, or "implement later" markers are left in the task steps. The only deferred work is explicitly called out as separate follow-up scope, not hidden inside this plan.

## Type Consistency Check

- template records use `TemplateDefinition`
- execution records use `TemplateExecution`
- bundle loading is always through `loader.LoadBundle`
- kernel execution always starts through `engine.New(...).Run(...)`
- execution requests always use `StartExecutionReq`
