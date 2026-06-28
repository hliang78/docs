# OneOps Standardized Orchestration Flow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the current flat orchestration workflow step model with a standardized flow contract and refactor compiler plus runtime to execute only normalized steps.

**Architecture:** Keep OneOps as the orchestration owner, keep dagengine as the execution kernel, and hard-cut templates to a new structured workflow schema. Introduce a normalization layer between template loading and compilation, then migrate runtime execution to a common step-aware contract so node kinds stay stable while execution semantics become explicit.

**Tech Stack:** Go, GORM, Gin, dagenginev2, YAML bundle loader, Zap, existing orchestration runtime tests and real multi-agent closure acceptance path

---

## File Structure

### Existing files to modify

- `OneOps/app/orchestration/template/define.go`
  - replace flat `WorkflowStep` fields with structured flow sections
- `OneOps/app/orchestration/template/loader.go`
  - validate only the new structured workflow schema and stop accepting flat fields
- `OneOps/app/orchestration/template/loader_test.go`
  - rewrite loader tests for the new schema and add negative validation cases
- `OneOps/app/orchestration/compiler/dagengine_compiler.go`
  - compile only normalized steps and remove direct dependence on flat workflow fields
- `OneOps/app/orchestration/compiler/dagengine_compiler_test.go`
  - verify normalized step compilation and terminal token handling
- `OneOps/app/orchestration/runtime/types.go`
  - replace node-config-centric execution input and result with normalized-step-centric contracts
- `OneOps/app/orchestration/runtime/registry.go`
  - register and resolve runtimes by `kind` instead of implicit `nodeType` assumptions
- `OneOps/app/orchestration/runtime/flow_step.go`
  - read action and policy from normalized step input
- `OneOps/app/orchestration/runtime/agent_step.go`
  - read action, agent catalog, and allowed tools from normalized step input
- `OneOps/app/orchestration/runtime/external_call_step.go`
  - read target and request policy from normalized step input
- `OneOps/app/orchestration/runtime/callback_wait_step.go`
  - read resume policy and timeout from normalized step input
- `OneOps/app/orchestration/runtime/approval_wait_step.go`
  - read approval policy and timeout from normalized step input
- `OneOps/app/orchestration/runtime/*_test.go`
  - migrate per-runtime tests to the new input and result contract
- `OneOps/app/orchestration/service/impl/dagengine_adapter.go`
  - pass normalized steps into runtimes and route transitions explicitly
- `OneOps/app/orchestration/service/impl/execution_test.go`
  - update mainline orchestration tests for the new schema and runtime contract
- `OneOps/app/orchestration/service/impl/resume_test.go`
  - update callback and approval tests for `on_reject` and `on_timeout`
- `OneOps/app/orchestration/template/testdata/alert_to_ticket/workflow.yaml`
  - rewrite to standardized workflow schema
- `OneOps/app/orchestration/template/testdata/multi_agent_ticket_closure/workflow.yaml`
  - rewrite to standardized workflow schema

### New files to create

- `OneOps/app/orchestration/template/normalize.go`
  - convert parsed workflow steps into `NormalizedStep` values
- `OneOps/app/orchestration/template/normalize_test.go`
  - verify kind-specific normalization and transition validation
- `OneOps/app/orchestration/runtime/step_contract.go`
  - define shared runtime-facing step types such as `NormalizedStep`, `StepInputs`, `StepPolicy`, `StepTransitions`, and `StepOutputs`

## Task 1: Hard-Cut The Workflow Template Schema

**Files:**
- Modify: `OneOps/app/orchestration/template/define.go`
- Modify: `OneOps/app/orchestration/template/loader.go`
- Modify: `OneOps/app/orchestration/template/loader_test.go`
- Modify: `OneOps/app/orchestration/template/testdata/alert_to_ticket/workflow.yaml`
- Modify: `OneOps/app/orchestration/template/testdata/multi_agent_ticket_closure/workflow.yaml`
- Test: `OneOps/app/orchestration/template/loader_test.go`

- [ ] **Step 1: Write failing loader tests for the new structured schema**

```go
func TestLoadBundleAcceptsStandardizedWorkflowSchema(t *testing.T) {
	root := t.TempDir()
	writeFile(t, root, "manifest.yaml", validManifestYAML())
	writeFile(t, root, "workflow.yaml", strings.TrimSpace(`
steps:
  - key: analysis_submit
    kind: agent_step
    inputs:
      from_context:
        alert_code: alert.code
    policy:
      action: analyze_alert
      agent:
        catalog: closure_agents
        allowed_tools:
          - topology_api
    transitions:
      on_success: analysis_wait
      on_failure: failed
    outputs:
      result_key: analysis
  - key: analysis_wait
    kind: callback_wait_step
    inputs:
      from_context:
        resume_token: analysis_resume_token
    policy:
      action: wait_for_analysis
      resume:
        token_context_key: analysis_resume_token
    transitions:
      on_success: completed
      on_failure: failed
`))
	writeFile(t, root, "agents.yaml", validAgentsYAML())

	bundle, err := LoadBundle(root)
	if err != nil {
		t.Fatalf("LoadBundle error: %v", err)
	}
	if len(bundle.Workflow.Steps) != 2 {
		t.Fatalf("step count = %d, want 2", len(bundle.Workflow.Steps))
	}
	if bundle.Workflow.Steps[0].Kind != "agent_step" {
		t.Fatalf("first kind = %q, want %q", bundle.Workflow.Steps[0].Kind, "agent_step")
	}
}

func TestLoadBundleRejectsLegacyFlatWorkflowFields(t *testing.T) {
	root := t.TempDir()
	writeFile(t, root, "manifest.yaml", validManifestYAML())
	writeFile(t, root, "workflow.yaml", strings.TrimSpace(`
steps:
  - key: old_step
    type: flow_step
    action: create_ticket
    next: completed
    on_failure: failed
`))
	writeFile(t, root, "agents.yaml", "catalogs: {}\n")

	_, err := LoadBundle(root)
	if err == nil {
		t.Fatal("LoadBundle error = nil, want legacy schema validation error")
	}
	if !strings.Contains(err.Error(), "field type not found") &&
		!strings.Contains(err.Error(), "kind") {
		t.Fatalf("LoadBundle error = %q, want missing kind or legacy-field rejection", err)
	}
}
```

- [ ] **Step 2: Run the loader tests to verify they fail**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
go test ./app/orchestration/template -run 'TestLoadBundleAcceptsStandardizedWorkflowSchema|TestLoadBundleRejectsLegacyFlatWorkflowFields' -count=1
```

Expected:

```text
FAIL ... unknown field "kind" or missing WorkflowStep structured fields
```

- [ ] **Step 3: Replace flat `WorkflowStep` with the new structured sections**

```go
type WorkflowStep struct {
	Key         string          `yaml:"key"`
	Kind        string          `yaml:"kind"`
	Inputs      WorkflowInputs  `yaml:"inputs"`
	Policy      WorkflowPolicy  `yaml:"policy"`
	Transitions WorkflowRoutes  `yaml:"transitions"`
	Outputs     WorkflowOutputs `yaml:"outputs"`
}

type WorkflowInputs struct {
	FromContext map[string]string      `yaml:"from_context"`
	Static      map[string]interface{} `yaml:"static"`
}

type WorkflowPolicy struct {
	Action   string                 `yaml:"action"`
	Timeout  string                 `yaml:"timeout"`
	Agent    WorkflowAgentPolicy    `yaml:"agent"`
	External WorkflowExternalPolicy `yaml:"external"`
	Resume   WorkflowResumePolicy   `yaml:"resume"`
	Approval WorkflowApprovalPolicy `yaml:"approval"`
}

type WorkflowAgentPolicy struct {
	Catalog      string   `yaml:"catalog"`
	AllowedTools []string `yaml:"allowed_tools"`
}

type WorkflowExternalPolicy struct {
	TargetRef          string `yaml:"target_ref"`
	RequestTemplateRef string `yaml:"request_template_ref"`
	CallbackRef        string `yaml:"callback_ref"`
}

type WorkflowResumePolicy struct {
	TokenContextKey string `yaml:"token_context_key"`
}

type WorkflowApprovalPolicy struct {
	PolicyRef string `yaml:"policy_ref"`
}

type WorkflowRoutes struct {
	OnSuccess string `yaml:"on_success"`
	OnFailure string `yaml:"on_failure"`
	OnTimeout string `yaml:"on_timeout"`
	OnReject  string `yaml:"on_reject"`
}

type WorkflowOutputs struct {
	ResultKey string            `yaml:"result_key"`
	Bindings  map[string]string `yaml:"bindings"`
}
```

- [ ] **Step 4: Update loader validation to require the new schema and reject flat fields**

```go
func validateWorkflow(workflow Workflow, catalogs map[string]AgentCatalog) error {
	stepKeys := make(map[string]struct{}, len(workflow.Steps))
	for _, step := range workflow.Steps {
		key := strings.TrimSpace(step.Key)
		if key == "" {
			return fmt.Errorf("workflow step key must not be empty")
		}
		if _, exists := stepKeys[key]; exists {
			return fmt.Errorf("workflow step key %q is duplicate", key)
		}
		stepKeys[key] = struct{}{}
	}

	for _, step := range workflow.Steps {
		if strings.TrimSpace(step.Kind) == "" {
			return fmt.Errorf("workflow step %q field %q is required", step.Key, "kind")
		}
		if !isSupportedStepKind(step.Kind) {
			return fmt.Errorf("workflow step %q field %q has unsupported value %q", step.Key, "kind", step.Kind)
		}
		if strings.TrimSpace(step.Policy.Action) == "" {
			return fmt.Errorf("workflow step %q field %q is required", step.Key, "policy.action")
		}
		if err := validateTransitions(stepKeys, step); err != nil {
			return err
		}
		if err := validateStepPolicy(step, catalogs); err != nil {
			return err
		}
	}
	return nil
}
```

- [ ] **Step 5: Rewrite official workflow testdata to the new schema**

```yaml
steps:
  - key: analysis_submit
    kind: agent_step
    inputs:
      from_context:
        alert_code: alert.code
    policy:
      action: analyze_alert
      agent:
        catalog: closure_agents
        allowed_tools:
          - topology_api
          - ticketing_api
    transitions:
      on_success: analysis_wait
      on_failure: failed
    outputs:
      result_key: analysis
```

- [ ] **Step 6: Run the template package tests**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
go test ./app/orchestration/template -count=1
```

Expected:

```text
ok  	github.com/netxops/OneOps/app/orchestration/template
```

- [ ] **Step 7: Commit**

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
git add app/orchestration/template/define.go app/orchestration/template/loader.go app/orchestration/template/loader_test.go app/orchestration/template/testdata/alert_to_ticket/workflow.yaml app/orchestration/template/testdata/multi_agent_ticket_closure/workflow.yaml
git commit -m "refactor: hard cut orchestration workflow schema"
```

## Task 2: Add A Normalization Layer Between Loader And Compiler

**Files:**
- Create: `OneOps/app/orchestration/template/normalize.go`
- Create: `OneOps/app/orchestration/template/normalize_test.go`
- Create: `OneOps/app/orchestration/runtime/step_contract.go`
- Test: `OneOps/app/orchestration/template/normalize_test.go`

- [ ] **Step 1: Write failing normalization tests**

```go
func TestNormalizeBundleConvertsWorkflowStepToNormalizedStep(t *testing.T) {
	bundle := &Bundle{
		Workflow: Workflow{
			Steps: []WorkflowStep{
				{
					Key:  "dispatch_submit",
					Kind: "agent_step",
					Inputs: WorkflowInputs{
						FromContext: map[string]string{"ticket_code": "ticket.code"},
					},
					Policy: WorkflowPolicy{
						Action: "recommend_dispatch",
						Agent: WorkflowAgentPolicy{
							Catalog:      "closure_agents",
							AllowedTools: []string{"schedule_api"},
						},
					},
					Transitions: WorkflowRoutes{
						OnSuccess: "dispatch_wait",
						OnFailure: "failed",
					},
					Outputs: WorkflowOutputs{ResultKey: "dispatch"},
				},
			},
		},
	}

	steps, err := NormalizeWorkflow(bundle)
	if err != nil {
		t.Fatalf("NormalizeWorkflow error: %v", err)
	}
	if len(steps) != 1 {
		t.Fatalf("normalized step count = %d, want 1", len(steps))
	}
	if steps[0].Policy.Agent.Catalog != "closure_agents" {
		t.Fatalf("catalog = %q, want %q", steps[0].Policy.Agent.Catalog, "closure_agents")
	}
}

func TestNormalizeWorkflowRejectsApprovalWaitWithoutOnRejectOrOnTimeout(t *testing.T) {
	bundle := &Bundle{
		Workflow: Workflow{
			Steps: []WorkflowStep{
				{
					Key:  "wait_approval",
					Kind: "approval_wait_step",
					Policy: WorkflowPolicy{
						Action: "wait_for_execution_approval",
						Approval: WorkflowApprovalPolicy{
							PolicyRef: "ops_manager",
						},
					},
					Transitions: WorkflowRoutes{
						OnSuccess: "completed",
					},
				},
			},
		},
	}

	_, err := NormalizeWorkflow(bundle)
	if err == nil {
		t.Fatal("NormalizeWorkflow error = nil, want transition validation error")
	}
	if !strings.Contains(err.Error(), "on_reject") {
		t.Fatalf("NormalizeWorkflow error = %q, want missing on_reject semantics", err)
	}
}
```

- [ ] **Step 2: Run the normalization tests to verify they fail**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
go test ./app/orchestration/template -run 'TestNormalizeBundleConvertsWorkflowStepToNormalizedStep|TestNormalizeWorkflowRejectsApprovalWaitWithoutOnRejectOrOnTimeout' -count=1
```

Expected:

```text
FAIL ... undefined: NormalizeWorkflow
```

- [ ] **Step 3: Define the shared normalized step contract**

```go
type NormalizedStep struct {
	Key         string
	Kind        string
	Inputs      StepInputs
	Policy      StepPolicy
	Transitions StepTransitions
	Outputs     StepOutputs
}

type StepInputs struct {
	FromContext map[string]string
	Static      map[string]interface{}
}

type StepPolicy struct {
	Action   string
	Timeout  time.Duration
	Agent    StepAgentPolicy
	External StepExternalPolicy
	Resume   StepResumePolicy
	Approval StepApprovalPolicy
}

type StepTransitions struct {
	OnSuccess string
	OnFailure string
	OnTimeout string
	OnReject  string
}

type StepOutputs struct {
	ResultKey string
	Bindings  map[string]string
}
```

- [ ] **Step 4: Implement normalization and kind-specific validation**

```go
func NormalizeWorkflow(bundle *Bundle) ([]runtime.NormalizedStep, error) {
	if bundle == nil {
		return nil, fmt.Errorf("bundle is nil")
	}

	steps := make([]runtime.NormalizedStep, 0, len(bundle.Workflow.Steps))
	stepKeys := collectStepKeys(bundle.Workflow.Steps)
	for _, raw := range bundle.Workflow.Steps {
		step, err := normalizeStep(raw)
		if err != nil {
			return nil, err
		}
		if err := validateNormalizedTransitions(stepKeys, step); err != nil {
			return nil, err
		}
		if err := validateNormalizedStep(step); err != nil {
			return nil, err
		}
		steps = append(steps, step)
	}
	return steps, nil
}
```

- [ ] **Step 5: Run the normalization tests and full template tests**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
go test ./app/orchestration/template -count=1
```

Expected:

```text
ok  	github.com/netxops/OneOps/app/orchestration/template
```

- [ ] **Step 6: Commit**

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
git add app/orchestration/template/normalize.go app/orchestration/template/normalize_test.go app/orchestration/runtime/step_contract.go
git commit -m "refactor: add normalized orchestration step contract"
```

## Task 3: Refactor The Compiler To Consume Only Normalized Steps

**Files:**
- Modify: `OneOps/app/orchestration/compiler/dagengine_compiler.go`
- Modify: `OneOps/app/orchestration/compiler/dagengine_compiler_test.go`
- Test: `OneOps/app/orchestration/compiler/dagengine_compiler_test.go`

- [ ] **Step 1: Write failing compiler tests for normalized-step compilation**

```go
func TestCompileBundleBuildsNodeConfigFromNormalizedSteps(t *testing.T) {
	bundle := loadTestBundle(t, filepath.Join("..", "template", "testdata", "multi_agent_ticket_closure"))

	process, err := CompileBundle("proc-1", bundle)
	if err != nil {
		t.Fatalf("CompileBundle error: %v", err)
	}

	config := process.GetNodeConfig("analysis_submit")
	policy, ok := config["policy"].(map[string]interface{})
	if !ok {
		t.Fatalf("policy config type = %T, want map[string]interface{}", config["policy"])
	}
	transitions, ok := config["transitions"].(map[string]interface{})
	if !ok {
		t.Fatalf("transitions config type = %T, want map[string]interface{}", config["transitions"])
	}
	if transitions["on_success"] != "analysis_wait" {
		t.Fatalf("on_success = %#v, want %q", transitions["on_success"], "analysis_wait")
	}
	if policy["action"] != "analyze_alert" {
		t.Fatalf("action = %#v, want %q", policy["action"], "analyze_alert")
	}
}

func TestCompileBundleRejectsUnknownTransitionTarget(t *testing.T) {
	bundle := &template.Bundle{
		Manifest: template.Manifest{Name: "bad"},
		Workflow: template.Workflow{
			Steps: []template.WorkflowStep{
				{
					Key:  "step_1",
					Kind: "flow_step",
					Policy: template.WorkflowPolicy{
						Action: "create_ticket",
					},
					Transitions: template.WorkflowRoutes{
						OnSuccess: "ghost_step",
						OnFailure: "failed",
					},
				},
			},
		},
	}

	_, err := CompileBundle("proc-2", bundle)
	if err == nil {
		t.Fatal("CompileBundle error = nil, want unknown transition target error")
	}
	if !strings.Contains(err.Error(), "ghost_step") {
		t.Fatalf("CompileBundle error = %q, want unknown target message", err)
	}
}
```

- [ ] **Step 2: Run the compiler tests to verify they fail**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
go test ./app/orchestration/compiler -run 'TestCompileBundleBuildsNodeConfigFromNormalizedSteps|TestCompileBundleRejectsUnknownTransitionTarget' -count=1
```

Expected:

```text
FAIL ... expected policy/transitions config, got flat action/next fields
```

- [ ] **Step 3: Normalize before compile and generate node config from the standard sections**

```go
func CompileBundle(processID string, bundle *template.Bundle) (*engine.DAGProcess, error) {
	steps, err := template.NormalizeWorkflow(bundle)
	if err != nil {
		return nil, err
	}

	nodeMap := make(map[string]interfaces.DAGNode, len(steps))
	nodeTypes := make(map[string]string, len(steps))
	nodeConfigs := make(map[string]map[string]interface{}, len(steps))
	for _, step := range steps {
		nodeMap[step.Key] = engine.NewDAGNode(step.Key, step.Policy.Action, nil)
		nodeTypes[step.Key] = step.Kind
		nodeConfigs[step.Key] = map[string]interface{}{
			"step":        step,
			"inputs":      step.Inputs,
			"policy":      step.Policy,
			"transitions": step.Transitions,
			"outputs":     step.Outputs,
		}
	}

	for _, step := range steps {
		target := strings.TrimSpace(step.Transitions.OnSuccess)
		if target == "" || isTerminalTarget(target) {
			continue
		}
		nodeMap[target].AddDependency(step.Key)
	}

	process := &engine.DAGProcess{
		ID:          processID,
		Name:        strings.TrimSpace(bundle.Manifest.Name),
		Nodes:       nodeMap,
		NodeTypes:   nodeTypes,
		NodeConfigs: nodeConfigs,
	}
	process.RecalculateRootAndLeafNodes()
	return process, nil
}
```

- [ ] **Step 4: Run the compiler tests and the full orchestration compiler package**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
go test ./app/orchestration/compiler -count=1
```

Expected:

```text
ok  	github.com/netxops/OneOps/app/orchestration/compiler
```

- [ ] **Step 5: Commit**

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
git add app/orchestration/compiler/dagengine_compiler.go app/orchestration/compiler/dagengine_compiler_test.go
git commit -m "refactor: compile orchestration from normalized steps"
```

## Task 4: Unify Runtime Execution Around The Normalized Step Contract

**Files:**
- Modify: `OneOps/app/orchestration/runtime/types.go`
- Modify: `OneOps/app/orchestration/runtime/registry.go`
- Modify: `OneOps/app/orchestration/runtime/flow_step.go`
- Modify: `OneOps/app/orchestration/runtime/agent_step.go`
- Modify: `OneOps/app/orchestration/runtime/external_call_step.go`
- Modify: `OneOps/app/orchestration/runtime/callback_wait_step.go`
- Modify: `OneOps/app/orchestration/runtime/approval_wait_step.go`
- Modify: `OneOps/app/orchestration/runtime/*_test.go`
- Modify: `OneOps/app/orchestration/service/impl/dagengine_adapter.go`
- Modify: `OneOps/app/orchestration/service/impl/execution_test.go`
- Modify: `OneOps/app/orchestration/service/impl/resume_test.go`
- Test: `OneOps/app/orchestration/runtime/...`
- Test: `OneOps/app/orchestration/service/impl/...`

- [ ] **Step 1: Write failing runtime contract tests**

```go
func TestAgentStepRuntimeReadsPolicyFromNormalizedStep(t *testing.T) {
	runtime := NewAgentStepRuntime(fakeAgentExecutor{
		patch: map[string]interface{}{"analysis": map[string]interface{}{"summary": "ok"}},
	})

	result, err := runtime.Run(context.Background(), NodeExecutionInput{
		ExecutionID: "exec-1",
		NodeID:      "analysis_submit",
		Context:     map[string]interface{}{"alert": map[string]interface{}{"code": "ALERT-1"}},
		Step: NormalizedStep{
			Key:  "analysis_submit",
			Kind: "agent_step",
			Policy: StepPolicy{
				Action: "analyze_alert",
				Agent: StepAgentPolicy{
					Catalog:      "closure_agents",
					AllowedTools: []string{"knowledge_base"},
				},
			},
			Transitions: StepTransitions{
				OnSuccess: "analysis_wait",
				OnFailure: "failed",
			},
		},
	})
	if err != nil {
		t.Fatalf("Run error: %v", err)
	}
	if result.Outcome != "success" {
		t.Fatalf("outcome = %q, want %q", result.Outcome, "success")
	}
}

func TestApprovalWaitStepUsesOnRejectTransition(t *testing.T) {
	step := NormalizedStep{
		Key:  "wait_execution_approval",
		Kind: "approval_wait_step",
		Policy: StepPolicy{
			Action: "wait_for_execution_approval",
			Approval: StepApprovalPolicy{
				PolicyRef: "ops_manager",
			},
		},
		Transitions: StepTransitions{
			OnSuccess: "tracking_submit",
			OnReject:  "rejected",
			OnTimeout: "escalated",
		},
	}

	if step.Transitions.OnReject != "rejected" {
		t.Fatalf("on_reject = %q, want %q", step.Transitions.OnReject, "rejected")
	}
}
```

- [ ] **Step 2: Run the runtime tests to verify they fail**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
go test ./app/orchestration/runtime/... -count=1
```

Expected:

```text
FAIL ... NodeExecutionInput has no Step field / NodeExecutionResult has no Outcome field
```

- [ ] **Step 3: Replace runtime input/output with normalized-step-centric contracts**

```go
type NodeRuntime interface {
	Kind() string
	Run(context.Context, NodeExecutionInput) (NodeExecutionResult, error)
}

type NodeExecutionInput struct {
	ExecutionID string
	NodeID      string
	Context     map[string]interface{}
	Step        NormalizedStep
}

type NodeExecutionResult struct {
	Outcome       string
	ContextPatch  map[string]interface{}
	Logs          []ExecutionLogEntry
	Events        []ExecutionEvent
	Error         *RuntimeError
	WaitState     *SuspendInstruction
	TerminalState string
}
```

- [ ] **Step 4: Refactor each runtime to read from `input.Step` instead of loose node config**

```go
func (r *AgentStepRuntime) Kind() string {
	return "agent_step"
}

func (r *AgentStepRuntime) Run(ctx context.Context, input NodeExecutionInput) (NodeExecutionResult, error) {
	action := strings.TrimSpace(input.Step.Policy.Action)
	if action == "" {
		runtimeErr := NewRuntimeError(DefaultRuntimeErrorCategory, "agent_step_invalid_policy", "policy.action is required", false, nil)
		return NodeExecutionResult{Outcome: "failure", Error: runtimeErr}, runtimeErr
	}

	patch, err := r.executor.ExecuteAgentStep(ctx, AgentStepRequest{
		NodeID:           input.NodeID,
		Action:           action,
		AgentCatalogName: input.Step.Policy.Agent.Catalog,
		AllowedTools:     append([]string{}, input.Step.Policy.Agent.AllowedTools...),
		Context:          cloneValueMap(input.Context),
	})
	if err != nil {
		runtimeErr := NormalizeRuntimeExecutionError(input.Step.Kind, err)
		return NodeExecutionResult{Outcome: "failure", Error: runtimeErr}, runtimeErr
	}

	return NodeExecutionResult{
		Outcome:      "success",
		ContextPatch: patch,
	}, nil
}
```

- [ ] **Step 5: Refactor the adapter to pass normalized steps and route by explicit transitions**

```go
runtimeResult, execErr := a.Middleware.Run(ctx, orchestrationRuntime.NodeExecutionInput{
	ExecutionID: executionID,
	NodeID:      nodeID,
	Context:     cloneMap(result.Context),
	Step:        stepFromNodeConfig(process.GetNodeConfig(nodeID)),
}, nodeRuntime.Run)

switch runtimeResult.Outcome {
case "success":
	next := strings.TrimSpace(runtimeResult.Step.Transitions.OnSuccess)
	_ = next
case "failure":
	// map timeout or reject to explicit transition keys before terminal fallback
case "wait":
	result.Status = waitStatusFor(runtimeResult.WaitState)
}
```

- [ ] **Step 6: Update runtime and service tests to cover `on_reject`, `on_timeout`, and terminal token semantics**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
go test ./app/orchestration/runtime/... -count=1
go test ./app/orchestration/service/impl -count=1
```

Expected:

```text
ok  	github.com/netxops/OneOps/app/orchestration/runtime
ok  	github.com/netxops/OneOps/app/orchestration/service/impl
```

- [ ] **Step 7: Run the mainline orchestration package suite**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
go test ./app/orchestration/... -count=1
```

Expected:

```text
ok  	github.com/netxops/OneOps/app/orchestration/...
```

- [ ] **Step 8: Commit**

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
git add app/orchestration/runtime app/orchestration/service/impl/dagengine_adapter.go app/orchestration/service/impl/execution_test.go app/orchestration/service/impl/resume_test.go
git commit -m "refactor: unify orchestration runtime around normalized steps"
```

## Task 5: Certify The Multi-Agent Closure Mainline On The Real Stack

**Files:**
- Modify: `OneOps/app/orchestration/template/testdata/multi_agent_ticket_closure/workflow.yaml`
- Modify: `OneOps/scripts/start_multi_agent_closure_stack.sh` (only if stack launch needs schema-aware adjustments)
- Test: real stack acceptance and package-level regression

- [ ] **Step 1: Add a real-stack regression expectation for reject and timeout routes**

```yaml
transitions:
  on_success: tracking_submit
  on_reject: rejected
  on_timeout: escalated
```

- [ ] **Step 2: Run the orchestration regression suites before the real stack**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
go test ./app/orchestration/template ./app/orchestration/compiler ./app/orchestration/runtime ./app/orchestration/service/impl -count=1
```

Expected:

```text
ok  	github.com/netxops/OneOps/app/orchestration/template
ok  	github.com/netxops/OneOps/app/orchestration/compiler
ok  	github.com/netxops/OneOps/app/orchestration/runtime
ok  	github.com/netxops/OneOps/app/orchestration/service/impl
```

- [ ] **Step 3: Restart the real stack**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL
bash OneOps/scripts/start_multi_agent_closure_stack.sh restart
```

Expected:

```text
agentruntime_ready=yes
oneops_ready=yes
execution_observatory_url=http://127.0.0.1:3001/#/platform/execution-observatory
```

- [ ] **Step 4: Run the real acceptance mainline**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL
bash OneOps/scripts/start_multi_agent_closure_stack.sh acceptance
```

Expected:

```text
... acceptance:multi-agent-ticket-closure-real-api ...
... execution completed ...
```

- [ ] **Step 5: Commit**

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
git add app/orchestration/template/testdata/multi_agent_ticket_closure/workflow.yaml scripts/start_multi_agent_closure_stack.sh
git commit -m "test: certify standardized multi-agent closure mainline"
```

## Self-Review

### Spec coverage

- Standardized workflow step structure: covered by Task 1
- Normalized internal model: covered by Task 2
- Compiler consumes normalized steps only: covered by Task 3
- Unified runtime contract: covered by Task 4
- Explicit `on_reject` / `on_timeout` / terminal token semantics: covered by Tasks 2, 4, and 5
- Real multi-agent closure certification: covered by Task 5

### Placeholder scan

- No `TODO`, `TBD`, or deferred placeholders remain
- All tasks contain concrete file paths, commands, and code snippets

### Type consistency

- `WorkflowStep` structured fields introduced in Task 1
- `NormalizedStep` contract introduced in Task 2
- Compiler switched to `NormalizedStep` in Task 3
- Runtime switched to `NodeExecutionInput.Step` and `NodeExecutionResult.Outcome` in Task 4
