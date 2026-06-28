# OneOps Task Domain Contract Registry Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Promote `task_domain` from loose template/runtime metadata into a platform-owned contract registry so `流程 + agent 策略 + 任务域` can safely drive multi-domain execution without hidden assumptions.

**Architecture:** Add one shared task-domain registry package with static platform-owned definitions. Resolve template-local domain aliases into registry refs during load/normalize, propagate `task_domain_ref` through orchestration and `agentruntime`, and enforce domain-level validation both at task submission time and at role-result completion time.

**Tech Stack:** Go, existing OneOps orchestration template loader, orchestration runtime registry, `agentruntime` durable task runtime, GORM models, existing loader/runtime tests, static registry-style platform config.

---

## File Structure

### Existing files to modify

- `OneOps/app/orchestration/template/define.go`
  - add domain reference fields instead of relying on string-only domain names
- `OneOps/app/orchestration/template/loader.go`
  - resolve template aliases against the shared task-domain registry
- `OneOps/app/orchestration/template/normalize.go`
  - carry `task_domain_ref` into normalized runtime policy
- `OneOps/app/orchestration/template/loader_test.go`
  - cover valid and invalid domain alias / role-pack combinations
- `OneOps/app/orchestration/runtime/step_contract.go`
  - include `TaskDomainRef` in `StepAgentPolicy`
- `OneOps/app/orchestration/runtime/agent_step.go`
  - propagate `TaskDomainRef` into agent task requests
- `OneOps/app/orchestration/compiler/dagengine_compiler.go`
  - include `task_domain_ref` in node config
- `OneOps/app/orchestration/service/impl/dagengine_adapter.go`
  - merge and decode `TaskDomainRef`
- `OneOps/app/orchestration/dto/agent_task.go`
  - add `task_domain_ref` to submit and response DTOs
- `OneOps/app/orchestration/orchestration_model/agent_task.go`
  - persist `task_domain_ref`
- `OneOps/app/orchestration/service/impl/agent_task_gateway.go`
  - persist and submit domain ref metadata
- `OneOps/app/orchestration/service/impl/capability_gateway.go`
  - expose domain-ref observability state
- `OneOps/app/agentruntime/service/roles.go`
  - extend `RoleRequest` domain fields and use domain/role-pack compatibility checks
- `OneOps/app/agentruntime/service/runtime.go`
  - validate submitted tasks against domain contracts
- `OneOps/app/agentruntime/service/runtime_test.go`
  - cover unknown-domain and incompatible role-pack submit cases
- `OneOps/app/agentruntime/agentruntime_model/task.go`
  - persist `task_domain_ref`
- `OneOps/app/agentruntime/service/task_repository.go`
  - write `task_domain_ref` into stored tasks
- `OneOps/app/agentruntime/service/task_runtime.go`
  - validate role result against domain result contract before persisting callback-pending/completed output
- `OneOps/app/agentruntime/service/task_runtime_test.go`
  - cover domain result mismatch and missing payload keys
- `OneOps/app/orchestration/template/testdata/diagnosis_rca/domains.yaml`
- `OneOps/app/orchestration/template/testdata/multi_agent_ticket_closure/domains.yaml`
- `OneOps/app/orchestration/template/testdata/operation_assist/domains.yaml`
  - move template domains to registry-ref style aliases

### New files to create

- `OneOps/app/orchestration/taskdomain/registry.go`
  - shared task-domain definition model, default registry, and validation helpers
- `OneOps/app/orchestration/taskdomain/registry_test.go`
  - registry resolution and compatibility tests

## Task 1: Create The Shared Task Domain Registry

**Files:**
- Create: `OneOps/app/orchestration/taskdomain/registry.go`
- Create: `OneOps/app/orchestration/taskdomain/registry_test.go`
- Test: `OneOps/app/orchestration/taskdomain/registry_test.go`

- [ ] **Step 1: Write the failing registry tests**

```go
package taskdomain

import "testing"

func TestRegistryResolveKnownDomain(t *testing.T) {
	registry := NewDefaultRegistry()

	domain, ok := registry.Resolve("incident.analysis.v1")
	if !ok {
		t.Fatal("Resolve ok = false, want true")
	}
	if domain.Name != "incident_analysis" {
		t.Fatalf("domain name = %q, want %q", domain.Name, "incident_analysis")
	}
	if domain.ResultType != "analysis" {
		t.Fatalf("result type = %q, want %q", domain.ResultType, "analysis")
	}
}

func TestValidateRolePackBindingRejectsPackOutsideDomain(t *testing.T) {
	registry := NewDefaultRegistry()
	domain, ok := registry.Resolve("ticket.closure.v1")
	if !ok {
		t.Fatal("Resolve ok = false, want true")
	}

	err := ValidateRolePackBinding(domain, "analysis.rca.v1")
	if err == nil {
		t.Fatal("ValidateRolePackBinding error = nil, want incompatible role pack error")
	}
}
```

- [ ] **Step 2: Run the registry tests to verify they fail**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
go test ./app/orchestration/taskdomain -run 'TestRegistryResolveKnownDomain|TestValidateRolePackBindingRejectsPackOutsideDomain' -count=1
```

Expected:

```text
FAIL ... undefined: NewDefaultRegistry
```

- [ ] **Step 3: Write the minimal shared registry**

```go
package taskdomain

import (
	"fmt"
	"strings"
)

type Definition struct {
	Ref                       string
	Name                      string
	Description               string
	RequiredContextKeys       []string
	ResultType                string
	RequiredResultPayloadKeys []string
	AllowedRolePacks          []string
	DefaultTimeoutSeconds     int
	DefaultCallbackMaxRetry   int
	ApprovalRequired          bool
	AllowedTerminalStates     []string
}

type Registry map[string]Definition

func NewDefaultRegistry() Registry {
	return Registry{
		"incident.analysis.v1": {
			Ref:                       "incident.analysis.v1",
			Name:                      "incident_analysis",
			ResultType:                "analysis",
			RequiredContextKeys:       []string{"alert_code"},
			RequiredResultPayloadKeys: []string{"summary"},
			AllowedRolePacks:          []string{"analysis.rca.v1"},
			DefaultTimeoutSeconds:     900,
			DefaultCallbackMaxRetry:   3,
			AllowedTerminalStates:     []string{"completed", "failed", "escalated"},
		},
		"ticket.closure.v1": {
			Ref:                   "ticket.closure.v1",
			Name:                  "ticket_closure",
			AllowedRolePacks:      []string{"closure.analysis.v1", "closure.dispatch.v1", "closure.tracking.v1", "closure.knowledge.v1"},
			DefaultTimeoutSeconds: 600,
			AllowedTerminalStates: []string{"completed", "failed", "rejected", "timed_out", "escalated", "action_required"},
		},
	}
}

func (r Registry) Resolve(ref string) (Definition, bool) {
	ref = strings.TrimSpace(ref)
	if ref == "" {
		return Definition{}, false
	}
	domain, ok := r[ref]
	return domain, ok
}

func ValidateRolePackBinding(domain Definition, rolePackRef string) error {
	rolePackRef = strings.TrimSpace(rolePackRef)
	if rolePackRef == "" {
		return nil
	}
	for _, candidate := range domain.AllowedRolePacks {
		if strings.TrimSpace(candidate) == rolePackRef {
			return nil
		}
	}
	return fmt.Errorf("task domain %q does not allow role pack %q", domain.Ref, rolePackRef)
}
```

- [ ] **Step 4: Run the registry tests to verify they pass**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
go test ./app/orchestration/taskdomain -run 'TestRegistryResolveKnownDomain|TestValidateRolePackBindingRejectsPackOutsideDomain' -count=1
```

Expected:

```text
ok  	github.com/netxops/OneOps/app/orchestration/taskdomain
```

- [ ] **Step 5: Commit**

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
git add app/orchestration/taskdomain/registry.go app/orchestration/taskdomain/registry_test.go
git commit -m "feat: add shared task domain registry"
```

## Task 2: Upgrade Template Loading To Resolve Registry-Backed Domains

**Files:**
- Modify: `OneOps/app/orchestration/template/define.go`
- Modify: `OneOps/app/orchestration/template/loader.go`
- Modify: `OneOps/app/orchestration/template/normalize.go`
- Modify: `OneOps/app/orchestration/runtime/step_contract.go`
- Modify: `OneOps/app/orchestration/template/loader_test.go`
- Modify: `OneOps/app/orchestration/template/testdata/diagnosis_rca/domains.yaml`
- Modify: `OneOps/app/orchestration/template/testdata/multi_agent_ticket_closure/domains.yaml`
- Modify: `OneOps/app/orchestration/template/testdata/operation_assist/domains.yaml`
- Test: `OneOps/app/orchestration/template/loader_test.go`

- [ ] **Step 1: Write the failing template-loader tests**

```go
func TestLoadBundleResolvesTaskDomainRegistryRef(t *testing.T) {
	root := t.TempDir()
	writeFile(t, root, "manifest.yaml", validManifestYAML())
	writeFile(t, root, "workflow.yaml", strings.TrimSpace(`
steps:
  - key: analysis_submit
    kind: agent_step
    policy:
      action: analyze_alert
      agent:
        task_domain_ref: rca
        strategy_ref: analysis.deep_dive
    transitions:
      on_success: completed
      on_failure: failed
`))
	writeFile(t, root, "agents.yaml", validDiagnosisAgentsYAML())
	writeFile(t, root, "domains.yaml", strings.TrimSpace(`
domains:
  rca:
    ref: incident.analysis.v1
`))
	writeFile(t, root, "strategies.yaml", validStrategiesYAML())

	bundle, err := LoadBundle(root)
	if err != nil {
		t.Fatalf("LoadBundle error: %v", err)
	}

	agent := bundle.Workflow.Steps[0].Policy.Agent
	if agent.TaskDomainRef != "incident.analysis.v1" {
		t.Fatalf("task domain ref = %q, want %q", agent.TaskDomainRef, "incident.analysis.v1")
	}
	if agent.TaskDomain != "incident_analysis" {
		t.Fatalf("task domain = %q, want %q", agent.TaskDomain, "incident_analysis")
	}
}

func TestLoadBundleRejectsRolePackOutsideResolvedDomain(t *testing.T) {
	root := t.TempDir()
	writeFile(t, root, "manifest.yaml", validManifestYAML())
	writeFile(t, root, "workflow.yaml", strings.TrimSpace(`
steps:
  - key: analysis_submit
    kind: agent_step
    policy:
      action: analyze_alert
      agent:
        task_domain_ref: closure
        role_pack_ref: analysis.rca.v1
    transitions:
      on_success: completed
      on_failure: failed
`))
	writeFile(t, root, "agents.yaml", validDiagnosisAgentsYAML())
	writeFile(t, root, "domains.yaml", strings.TrimSpace(`
domains:
  closure:
    ref: ticket.closure.v1
`))

	_, err := LoadBundle(root)
	if err == nil {
		t.Fatal("LoadBundle error = nil, want domain/role-pack mismatch error")
	}
}
```

- [ ] **Step 2: Run the template-loader tests to verify they fail**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
go test ./app/orchestration/template -run 'TestLoadBundleResolvesTaskDomainRegistryRef|TestLoadBundleRejectsRolePackOutsideResolvedDomain' -count=1
```

Expected:

```text
FAIL ... TaskDomainRef undefined
```

- [ ] **Step 3: Implement registry-backed template resolution**

```go
type WorkflowAgentPolicy struct {
	Catalog          string                 `yaml:"catalog"`
	TaskDomain       string                 `yaml:"task_domain"`
	TaskDomainRef    string                 `yaml:"task_domain_ref"`
	RolePackRef      string                 `yaml:"role_pack_ref"`
	RoleRef          string                 `yaml:"role_ref"`
	StrategyRef      string                 `yaml:"strategy_ref"`
	StrategyInput    map[string]interface{} `yaml:"strategy_input"`
	AllowedTools     []string               `yaml:"allowed_tools"`
	TimeoutSeconds   int                    `yaml:"timeout_seconds,omitempty"`
	CallbackMaxRetry int                    `yaml:"callback_max_retry,omitempty"`
	ApprovalRequired *bool                  `yaml:"approval_required,omitempty"`
}

type TaskDomainDefinition struct {
	Ref string `yaml:"ref"`
}
```

```go
func resolveDomainReference(ref string, domains DomainsFile, registry taskdomain.Registry) (taskdomain.Definition, error) {
	alias := strings.TrimSpace(ref)
	if alias == "" {
		return taskdomain.Definition{}, fmt.Errorf("task domain ref is required")
	}

	local, ok := domains.Domains[alias]
	if !ok {
		return taskdomain.Definition{}, fmt.Errorf("references missing task domain %q", alias)
	}
	resolved, ok := registry.Resolve(local.Ref)
	if !ok {
		return taskdomain.Definition{}, fmt.Errorf("task domain registry ref %q is not registered", local.Ref)
	}
	return resolved, nil
}
```

```go
type StepAgentPolicy struct {
	Catalog          string
	TaskDomain       string
	TaskDomainRef    string
	RolePackRef      string
	RoleRef          string
	StrategyRef      string
	StrategyInput    map[string]interface{}
	AllowedTools     []string
	TimeoutSeconds   int
	CallbackMaxRetry int
	ApprovalRequired bool
}
```

- [ ] **Step 4: Run the template-loader tests to verify they pass**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
go test ./app/orchestration/template -run 'TestLoadBundleResolvesTaskDomainRegistryRef|TestLoadBundleRejectsRolePackOutsideResolvedDomain' -count=1
```

Expected:

```text
ok  	github.com/netxops/OneOps/app/orchestration/template
```

- [ ] **Step 5: Commit**

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
git add app/orchestration/template/define.go app/orchestration/template/loader.go app/orchestration/template/normalize.go app/orchestration/runtime/step_contract.go app/orchestration/template/loader_test.go app/orchestration/template/testdata/diagnosis_rca/domains.yaml app/orchestration/template/testdata/multi_agent_ticket_closure/domains.yaml app/orchestration/template/testdata/operation_assist/domains.yaml
git commit -m "feat: resolve templates against task domain registry"
```

## Task 3: Propagate Task Domain Ref Through Orchestration Submission

**Files:**
- Modify: `OneOps/app/orchestration/runtime/agent_step.go`
- Modify: `OneOps/app/orchestration/compiler/dagengine_compiler.go`
- Modify: `OneOps/app/orchestration/service/impl/dagengine_adapter.go`
- Modify: `OneOps/app/orchestration/dto/agent_task.go`
- Modify: `OneOps/app/orchestration/orchestration_model/agent_task.go`
- Modify: `OneOps/app/orchestration/service/impl/agent_task_gateway.go`
- Modify: `OneOps/app/orchestration/service/impl/capability_gateway.go`
- Modify: `OneOps/app/orchestration/runtime/agent_step_test.go`
- Modify: `OneOps/app/orchestration/service/impl/agent_task_gateway_test.go`
- Test: `OneOps/app/orchestration/runtime/agent_step_test.go`
- Test: `OneOps/app/orchestration/service/impl/agent_task_gateway_test.go`

- [ ] **Step 1: Write the failing propagation tests**

```go
func TestAgentStepRuntime_PassesTaskDomainRefToExecutor(t *testing.T) {
	executor := &stubAgentStepExecutor{}
	runtime := NewAgentStepRuntime(executor)

	_, err := runtime.Run(context.Background(), NodeExecutionInput{
		NodeID: "analysis_submit",
		Step: NormalizedStep{
			Key:  "analysis_submit",
			Kind: "agent_step",
			Policy: StepPolicy{
				Action: "analyze_alert",
				Agent: StepAgentPolicy{
					TaskDomain:    "incident_analysis",
					TaskDomainRef: "incident.analysis.v1",
				},
			},
		},
	})
	if err != nil {
		t.Fatalf("Run error: %v", err)
	}
	if executor.taskDomainRef != "incident.analysis.v1" {
		t.Fatalf("task domain ref = %q, want %q", executor.taskDomainRef, "incident.analysis.v1")
	}
}
```

```go
func TestAgentTaskGatewaySubmitsTaskDomainRef(t *testing.T) {
	patch, err := gateway.ExecuteAgentStep(context.Background(), orchestrationRuntime.AgentStepRequest{
		NodeID:           "analysis_submit",
		Action:           "analyze_alert",
		TaskDomain:       "incident_analysis",
		TaskDomainRef:    "incident.analysis.v1",
		RolePackRef:      "analysis.rca.v1",
		ResumeTokenContextKey: "analysis_resume_token",
		Context: map[string]interface{}{
			"execution_id": "exec-1",
			"alert_code":   "ALERT-1",
		},
	})
	if err != nil {
		t.Fatalf("ExecuteAgentStep error: %v", err)
	}
	if client.lastReq.TaskDomainRef != "incident.analysis.v1" {
		t.Fatalf("submit task domain ref = %q, want %q", client.lastReq.TaskDomainRef, "incident.analysis.v1")
	}
	if got := patch["agent_task_domain_ref"]; got != "incident.analysis.v1" {
		t.Fatalf("patch agent_task_domain_ref = %#v, want %q", got, "incident.analysis.v1")
	}
}
```

- [ ] **Step 2: Run the propagation tests to verify they fail**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
go test ./app/orchestration/runtime ./app/orchestration/service/impl -run 'TestAgentStepRuntime_PassesTaskDomainRefToExecutor|TestAgentTaskGatewaySubmitsTaskDomainRef' -count=1
```

Expected:

```text
FAIL ... TaskDomainRef undefined
```

- [ ] **Step 3: Implement `task_domain_ref` propagation**

```go
type AgentStepRequest struct {
	NodeID                string
	Action                string
	AgentCatalogName      string
	TaskDomain            string
	TaskDomainRef         string
	RolePackRef           string
	RoleRef               string
	StrategyRef           string
	StrategyInput         map[string]interface{}
	AllowedTools          []string
	TimeoutSeconds        int
	CallbackMaxRetry      int
	ApprovalRequired      bool
	ResumeTokenContextKey string
	Context               map[string]interface{}
}
```

```go
type AgentRuntimeSubmitReq struct {
	TaskID                string                 `json:"task_id"`
	ExecutionID           string                 `json:"execution_id"`
	NodeID                string                 `json:"node_id"`
	TaskType              string                 `json:"task_type"`
	AgentCatalogName      string                 `json:"agent_catalog_name,omitempty"`
	TaskDomain            string                 `json:"task_domain,omitempty"`
	TaskDomainRef         string                 `json:"task_domain_ref,omitempty"`
	RolePackRef           string                 `json:"role_pack_ref,omitempty"`
	RoleRef               string                 `json:"role_ref,omitempty"`
	StrategyRef           string                 `json:"strategy_ref,omitempty"`
	StrategyInput         map[string]interface{} `json:"strategy_input,omitempty"`
	AllowedTools          []string               `json:"allowed_tools,omitempty"`
	TimeoutSeconds        int                    `json:"timeout_seconds,omitempty"`
	CallbackMaxRetry      int                    `json:"callback_max_retry,omitempty"`
	ApprovalRequired      bool                   `json:"approval_required,omitempty"`
	ResumeToken           string                 `json:"resume_token"`
	ResumeTokenContextKey string                 `json:"resume_token_context_key,omitempty"`
	InputContext          map[string]interface{} `json:"input_context,omitempty"`
}
```

```go
type AgentTask struct {
	ID                string `gorm:"column:id;primaryKey;type:varchar(36)"`
	ExecutionID       string `gorm:"column:execution_id;type:varchar(36);index;not null"`
	NodeID            string `gorm:"column:node_id;type:varchar(128);index;not null"`
	TaskType          string `gorm:"column:task_type;type:varchar(64);not null"`
	TaskDomain        string `gorm:"column:task_domain;type:varchar(128)"`
	TaskDomainRef     string `gorm:"column:task_domain_ref;type:varchar(128)"`
	RolePackRef       string `gorm:"column:role_pack_ref;type:varchar(128)"`
	// ...
}
```

- [ ] **Step 4: Run the propagation tests to verify they pass**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
go test ./app/orchestration/runtime ./app/orchestration/service/impl -run 'TestAgentStepRuntime_PassesTaskDomainRefToExecutor|TestAgentTaskGatewaySubmitsTaskDomainRef' -count=1
```

Expected:

```text
ok  	github.com/netxops/OneOps/app/orchestration/runtime
ok  	github.com/netxops/OneOps/app/orchestration/service/impl
```

- [ ] **Step 5: Commit**

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
git add app/orchestration/runtime/agent_step.go app/orchestration/compiler/dagengine_compiler.go app/orchestration/service/impl/dagengine_adapter.go app/orchestration/dto/agent_task.go app/orchestration/orchestration_model/agent_task.go app/orchestration/service/impl/agent_task_gateway.go app/orchestration/service/impl/capability_gateway.go app/orchestration/runtime/agent_step_test.go app/orchestration/service/impl/agent_task_gateway_test.go
git commit -m "feat: propagate task domain refs through orchestration"
```

## Task 4: Enforce Task Domain Contracts In AgentRuntime Submit And Result Validation

**Files:**
- Modify: `OneOps/app/agentruntime/service/roles.go`
- Modify: `OneOps/app/agentruntime/service/runtime.go`
- Modify: `OneOps/app/agentruntime/agentruntime_model/task.go`
- Modify: `OneOps/app/agentruntime/service/task_repository.go`
- Modify: `OneOps/app/agentruntime/service/task_runtime.go`
- Modify: `OneOps/app/agentruntime/service/runtime_test.go`
- Modify: `OneOps/app/agentruntime/service/task_runtime_test.go`
- Test: `OneOps/app/agentruntime/service/runtime_test.go`
- Test: `OneOps/app/agentruntime/service/task_runtime_test.go`

- [ ] **Step 1: Write the failing agentruntime tests**

```go
func TestRuntimeSubmitRejectsUnknownTaskDomainRef(t *testing.T) {
	db := newTaskRepositoryAutoMigrateDB(t)
	repo := NewTaskRepository(db)
	runtime := NewRuntime(zap.NewNop(), &fakeCallbackClient{}, NewDefaultRoles(nil), repo, nil)

	err := runtime.Submit(context.Background(), agentruntimeDTO.AgentRuntimeSubmitReq{
		TaskID:        "task-domain-missing-1",
		ExecutionID:   "exec-domain-missing-1",
		NodeID:        "analysis_submit",
		TaskType:      "analyze_alert",
		TaskDomain:    "incident_analysis",
		TaskDomainRef: "missing.domain.v1",
		RolePackRef:   "analysis.rca.v1",
		ResumeToken:   "resume-domain-missing-1",
		InputContext: map[string]interface{}{
			"alert_code": "ALERT-1",
		},
	})
	if err == nil {
		t.Fatal("Submit error = nil, want unknown task domain ref error")
	}
}

func TestTaskRuntimeRejectsResultTypeMismatchForDomain(t *testing.T) {
	repo := newFakeTaskRuntimeRepo()
	runtime := NewTaskRuntime(zap.NewNop(), repo, &fakeCallbackClient{}, RoleRegistry{
		RolePackKey("analysis.rca.v1"): fakeRoleHandler{
			result: RoleResult{
				Status:     "completed",
				ResultType: "dispatch_plan",
				ResultPayload: map[string]interface{}{
					"summary": "wrong type",
				},
			},
		},
	}, "worker-1")

	err := runtime.runTask(context.Background(), agentruntimeModel.Task{
		ID:            "task-run-1",
		TaskType:      "analyze_alert",
		TaskDomain:    "incident_analysis",
		TaskDomainRef: "incident.analysis.v1",
		RolePackRef:   "analysis.rca.v1",
		InputPayloadJSON: `{"alert_code":"ALERT-1"}`,
	})
	if err == nil {
		t.Fatal("runTask error = nil, want result type mismatch error")
	}
}
```

- [ ] **Step 2: Run the agentruntime tests to verify they fail**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
go test ./app/agentruntime/service -run 'TestRuntimeSubmitRejectsUnknownTaskDomainRef|TestTaskRuntimeRejectsResultTypeMismatchForDomain' -count=1
```

Expected:

```text
FAIL ... TaskDomainRef undefined
```

- [ ] **Step 3: Implement submit-time and result-time domain validation**

```go
type RoleRequest struct {
	TaskID           string
	ExecutionID      string
	NodeID           string
	TaskType         string
	AgentCatalogName string
	TaskDomain       string
	TaskDomainRef    string
	RolePackRef      string
	RoleRef          string
	StrategyRef      string
	StrategyInput    map[string]interface{}
	AllowedTools     []string
	Context          map[string]interface{}
}
```

```go
type Runtime struct {
	logger         *zap.Logger
	callbackClient CallbackClient
	roles          RoleRegistry
	rolePacks      RolePackRegistry
	domains        taskdomain.Registry
	repo           TaskEnqueuer
	workers        *TaskWorkers
}
```

```go
func ValidateTaskDomainRequest(req RoleRequest, registry taskdomain.Registry) (taskdomain.Definition, error) {
	definition, ok := registry.Resolve(req.TaskDomainRef)
	if !ok {
		return taskdomain.Definition{}, fmt.Errorf("task domain %q is not registered", req.TaskDomainRef)
	}
	if strings.TrimSpace(req.TaskDomain) != "" && strings.TrimSpace(req.TaskDomain) != definition.Name {
		return taskdomain.Definition{}, fmt.Errorf("task domain ref %q requires task_domain=%q", req.TaskDomainRef, definition.Name)
	}
	for _, key := range definition.RequiredContextKeys {
		if stringValue(req.Context[key]) == "" {
			return taskdomain.Definition{}, fmt.Errorf("task domain %q missing required inputs: %s", req.TaskDomainRef, key)
		}
	}
	if err := taskdomain.ValidateRolePackBinding(definition, req.RolePackRef); err != nil {
		return taskdomain.Definition{}, err
	}
	return definition, nil
}
```

```go
func ValidateDomainResult(domain taskdomain.Definition, result RoleResult) error {
	if strings.TrimSpace(domain.ResultType) != "" && strings.TrimSpace(result.ResultType) != strings.TrimSpace(domain.ResultType) {
		return fmt.Errorf("task domain %q requires result_type=%q", domain.Ref, domain.ResultType)
	}
	for _, key := range domain.RequiredResultPayloadKeys {
		if stringValue(result.ResultPayload[key]) == "" {
			return fmt.Errorf("task domain %q missing required result payload key %q", domain.Ref, key)
		}
	}
	if len(domain.AllowedTerminalStates) > 0 && !stringInNormalizedList(result.Status, domain.AllowedTerminalStates) {
		return fmt.Errorf("task domain %q does not allow terminal status=%q", domain.Ref, result.Status)
	}
	return nil
}
```

- [ ] **Step 4: Run the agentruntime tests to verify they pass**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
go test ./app/agentruntime/service -run 'TestRuntimeSubmitRejectsUnknownTaskDomainRef|TestTaskRuntimeRejectsResultTypeMismatchForDomain' -count=1
```

Expected:

```text
ok  	github.com/netxops/OneOps/app/agentruntime/service
```

- [ ] **Step 5: Run the focused regression suite**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
go test ./app/orchestration/taskdomain ./app/orchestration/template ./app/orchestration/runtime ./app/orchestration/service/impl ./app/agentruntime/service -count=1
```

Expected:

```text
ok  	github.com/netxops/OneOps/app/orchestration/taskdomain
ok  	github.com/netxops/OneOps/app/orchestration/template
ok  	github.com/netxops/OneOps/app/orchestration/runtime
ok  	github.com/netxops/OneOps/app/orchestration/service/impl
ok  	github.com/netxops/OneOps/app/agentruntime/service
```

- [ ] **Step 6: Commit**

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
git add app/agentruntime/service/roles.go app/agentruntime/service/runtime.go app/agentruntime/agentruntime_model/task.go app/agentruntime/service/task_repository.go app/agentruntime/service/task_runtime.go app/agentruntime/service/runtime_test.go app/agentruntime/service/task_runtime_test.go
git commit -m "feat: enforce task domain contracts in agentruntime"
```

## Self-Review

- [ ] The plan covers the full intended slice:
  - shared registry
  - template resolution
  - orchestration propagation
  - agentruntime submit/result validation
- [ ] No task depends on undefined types without defining them in the same or earlier task.
- [ ] The implementation stays lightweight:
  - static registry
  - reference-based templates
  - no schema engine
  - no autonomy redesign

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-06-28-oneops-task-domain-contract-registry-implementation-plan.md`.

Two execution options:

1. Subagent-Driven (recommended) - I dispatch a fresh subagent per task, review between tasks, fast iteration
2. Inline Execution - Execute tasks in this session using executing-plans, batch execution with checkpoints
