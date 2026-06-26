# OneOps Agent Orchestration Framework MVP Design

## 1. Goal

Build a lightweight agent orchestration framework that can be reused across multiple OneOps scenarios by importing templates, instead of hard-coding one workflow per use case.

The first version must stay intentionally small:

- lightweight
- MVP-first
- easy to integrate with existing OneOps modules
- safe by default in production

The framework should support at least two scenario families through template import:

1. alert-to-ticket closed-loop handling
2. deep fault diagnosis with multi-agent collaboration

This is not a full low-code platform in phase 1. It is a thin orchestration kernel plus a thin OneOps integration layer.

## 2. Design Principles

### 2.1 MVP first

Phase 1 should only build the minimum kernel needed to run two template types. Anything that looks like a general-purpose platform feature should be delayed unless it is required by those two templates.

### 2.2 Hybrid deployment model

The orchestration kernel should be an independent service. OneOps should remain the entry point, operations console, and capability provider.

This keeps the boundary clean without losing deep integration.

### 2.3 Template-driven behavior

Scenario differences should come from imported templates, not from per-scenario code branches in the kernel.

### 2.4 Outer control, inner autonomy

The outer layer must remain deterministic and auditable through a state machine. Only selected inner nodes should run multi-agent diagnosis loops.

### 2.5 Safe production posture

Automation level must be environment-aware. Production defaults should be conservative; lower environments can be more autonomous.

## 3. Target Architecture

The recommended architecture is:

- `OneOps` acts as experience layer, integration layer, and capability provider
- `flow` evolves into the standalone orchestration kernel
- templates define scenario behavior

### 3.1 Layering

#### L1. OneOps Experience Layer

This is the user-facing side:

- alert entry points
- ticket center
- task center entry points
- knowledge and SOP views
- execution status views
- template import and enable/disable entry points

#### L2. OneOps Integration Layer

This is a thin adapter layer inside OneOps:

- converts alerts or manual actions into execution requests
- assembles execution context from OneOps data
- forwards start/approve/retry/query requests to the orchestration kernel
- maps permissions and environment policies
- writes execution results back to OneOps

This layer should be implemented as a new thin OneOps module, for example `OneOps/app/orchestration`.

#### L3. Agent Orchestration Kernel

This is the independent runtime core, preferably evolved from the existing `flow` repo:

- template loading and validation
- outer workflow state machine
- inner agent node runner
- execution context storage
- tool gateway
- audit and policy guard

#### L4. Capability Plane

The kernel should not directly depend on many business modules. Instead, it should call capabilities through a narrow gateway:

- task execution
- monitoring and metric query
- log query
- device and topology query
- ticket create/update
- knowledge retrieval and draft write-back
- notification

#### L5. Governance Layer

Cross-cutting control should remain explicit:

- RBAC
- approval gates
- credential boundary
- audit trail
- environment-based automation level
- timeout and retry control

### 3.2 Responsibility split

Templates define what to do:

- stages
- agent roles
- tool references
- SOP references
- approval checkpoints
- close conditions
- knowledge write-back actions

The kernel defines how execution remains safe and stable:

- state transitions
- retries
- timeout handling
- context persistence
- policy enforcement
- audit

## 4. Template Model

Phase 1 should avoid a heavy DSL. The template bundle should stay small and mostly declarative.

### 4.1 Bundle structure

Each template bundle should contain at most:

1. `manifest.yaml`
2. `workflow.yaml`
3. `agents.yaml`
4. optional `runbooks/` or `knowledge/`

### 4.2 `manifest.yaml`

This file contains:

- template name
- template version
- scenario type
- risk level
- supported environments
- status: enabled or disabled

### 4.3 `workflow.yaml`

This file defines the outer state machine:

- stages
- transition conditions
- close conditions
- approval checkpoints
- timeout policy
- retry policy
- escalation behavior

### 4.4 `agents.yaml`

This file defines the inner agent collaboration model:

- agent names
- roles
- allowed tools
- shared context segments
- entry node
- call relationships
- max rounds
- timeout

### 4.5 `runbooks/` or `knowledge/`

Phase 1 should only support referenced SOP content or bundled knowledge snippets. It should not try to build a full knowledge graph or advanced memory system.

### 4.6 Explicit non-goals for phase 1

Phase 1 should not support:

- template-defined custom executors
- template-defined arbitrary code
- plugin sandbox bundles
- complex expression language
- visual template builder

## 5. Runtime Design

Phase 1 runtime should contain only six core pieces.

### 5.1 Template Loader

Responsibilities:

- load bundle files
- validate schema
- check version compatibility
- reject incomplete templates early

### 5.2 Execution Engine

Responsibilities:

- execute the outer workflow state machine
- track current step
- handle timeout
- handle retry
- determine completion, escalation, or failure

This is the main deterministic control plane.

### 5.3 Agent Node Runner

Responsibilities:

- run selected inner multi-agent steps
- load the `agents.yaml` definition
- enforce maximum rounds and timeout
- return structured diagnosis output back to the execution engine

This should only be entered from explicitly declared `agent_step` nodes.

### 5.4 Context Store

Responsibilities:

- store per-execution context
- persist alert, ticket, device, evidence, diagnosis, approvals, and tool outputs
- provide resumable snapshots

Phase 1 should prefer a simple persistent model over advanced memory abstractions.

### 5.5 Tool Gateway

Responsibilities:

- provide a narrow, stable interface from kernel to OneOps capabilities
- hide internal module complexity
- centralize execution logging and authorization checks

### 5.6 Audit and Policy Guard

Responsibilities:

- enforce environment rules
- enforce approval requirements
- enforce tool allowlists
- record who did what and why

## 6. Minimal Execution Model

Phase 1 should only support two node types:

### 6.1 `flow_step`

Used for deterministic workflow actions, such as:

- create ticket
- wait for approval
- update status
- write back summary
- transition to closed state

### 6.2 `agent_step`

Used for uncertain reasoning loops, such as:

- diagnose probable root cause
- gather more evidence
- generate recommended actions
- generate closure summary draft

This keeps the design simple:

- state machine controls the loop
- agent nodes handle uncertainty

## 7. MVP Scenario Templates

Phase 1 should ship only two official templates.

### 7.1 Alert-To-Ticket Loop

Goal:

Turn alert events into a traceable, auditable closed-loop ticket process.

Suggested minimal flow:

1. receive alert
2. deduplicate or merge
3. create ticket
4. generate dispatch suggestion
5. track execution
6. close or resolve
7. draft knowledge summary

Minimal `agent_step` usage:

- dispatch suggestion
- closure summary drafting

### 7.2 Deep Fault Diagnosis

Goal:

Run controlled multi-agent diagnosis with human confirmation before high-risk action.

Suggested minimal flow:

1. receive event or manual trigger
2. collect initial context
3. run diagnosis agent step
4. rank root-cause candidates
5. generate recommendations
6. wait for human confirmation or execution handoff
7. draft knowledge summary

Minimal inner agent roles:

- `Coordinator`
- `EvidenceCollector`
- `Analyst`

Phase 1 should stop at diagnosis and recommendation. Full autonomous remediation is not required.

## 8. Phase 1 Scope

### 8.1 Core domain objects

Only four runtime objects are required:

#### `TemplateDefinition`

- template metadata
- current enabled status
- supported environments
- scenario type
- version

#### `TemplateExecution`

- execution id
- template id and version
- trigger source
- environment
- current status
- current node
- final result

#### `ExecutionContext`

- alert snapshot
- ticket snapshot
- device and topology references
- evidence records
- diagnosis output
- approval records

#### `ExecutionEvent`

- ordered audit events
- state transitions
- tool calls
- approval actions
- escalation records
- failure records

### 8.2 Minimal API surface

Phase 1 should support only:

- `POST /templates/import`
- `GET /templates`
- `GET /templates/:id`
- `POST /executions/start`
- `GET /executions/:id`
- `POST /executions/:id/approve`
- `POST /executions/:id/retry`
- `GET /executions/:id/events`

Phase 1 does not need full online template editing.

### 8.3 Minimal OneOps integration points

Only five integrations are required:

1. alert trigger entry
2. ticket create/update
3. task center execution
4. observability lookup
5. knowledge draft write-back

### 8.4 Minimal UI surface

Only three pages are needed:

1. template list
2. execution detail
3. operations and audit view

Phase 1 should not build a drag-and-drop workflow designer.

## 9. Error Handling and Safety Boundaries

### 9.1 Allowed terminal statuses

Phase 1 should keep terminal states small and explicit:

- `completed`
- `waiting_approval`
- `escalated`
- `failed`

### 9.2 Agent step safety

Each `agent_step` must define:

- `max_rounds`
- `timeout_seconds`
- `allowed_tools`

If limits are exceeded, the execution should move to `escalated` or `failed`, not continue indefinitely.

### 9.3 Tool risk rules

Tool invocations should be separated into:

- read-only tools
- low-risk write tools
- high-risk write tools

Production defaults:

- read-only tools allowed
- low-risk writes allowed only if environment policy permits
- high-risk writes require approval

### 9.4 Context minimization

The context store should hold only execution-relevant data. The kernel should not gain broad implicit access to unrelated sensitive data.

### 9.5 Retry model

Phase 1 should implement only simple retry behavior:

- retry once
- fixed small retry count
- explicit manual retry

It should not implement a complex compensation framework.

## 10. Testing Strategy

Phase 1 testing should stay practical and high-signal.

### 10.1 Template schema tests

Validate required fields, node references, tool allowlists, and basic version rules.

### 10.2 Golden template tests

Run stable sample inputs against the two official templates and verify:

- state transitions
- expected tool calls
- expected diagnosis output shape

### 10.3 Tool gateway mock tests

Ensure template execution can be tested without live dependencies.

### 10.4 One end-to-end smoke path

At least one alert-to-ticket execution path should be runnable end to end in a test or dev environment.

## 11. Technology and Repository Placement

### 11.1 Orchestration kernel

The orchestration kernel should be built from the existing `flow` repository instead of being embedded directly inside OneOps.

Reasoning:

- a service boundary already exists
- it matches the chosen hybrid architecture
- it avoids making OneOps heavier in phase 1

### 11.2 OneOps integration module

Add a thin module such as `OneOps/app/orchestration` to handle:

- template import and enable/disable
- execution start and query
- approval callback
- integration-layer context assembly
- operations-facing views

### 11.3 Task execution reuse

Reuse `OneOps/app/platform/dto/ExecutionEnvelopeV2` as the phase 1 task execution contract instead of creating a second execution DSL.

### 11.4 LLM reuse

Reuse the existing `OneOps/app/llm` provider layer. The kernel should not introduce a second model provider abstraction in phase 1.

### 11.5 Ticket integration reuse

Phase 1 should integrate first with the existing alert ticket model instead of trying to unify every ticketing model inside OneOps.

### 11.6 Initial capability adapters

Only five capability adapters should be built first:

- `AlertAdapter`
- `TicketAdapter`
- `TaskCenterAdapter`
- `ObservabilityAdapter`
- `KnowledgeAdapter`

## 12. Out of Scope

The following are explicitly out of scope for phase 1:

- graphical workflow designer
- marketplace for templates
- plugin sandbox execution
- large-scale long-term memory systems
- universal cross-platform integration framework
- automatic dispatch of people, vehicles, and materials
- fully autonomous production remediation

## 13. Recommended Next Step

After design approval, implementation planning should focus on one narrow slice:

1. evolve `flow` into a minimal orchestration runtime
2. create `OneOps/app/orchestration`
3. wire the `Alert-To-Ticket Loop` template first
4. prove the model with one diagnosis-oriented template second

This sequence keeps the first delivery small while still validating the full framework shape.
