# OneOps Agentic Orchestration Platform Master Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a production-oriented OneOps agentic orchestration platform where the runtime is stable, the agent contract is controlled, and different business tasks are delivered mainly by switching `流程 + agent 策略 + 任务域` templates instead of rewriting core code.

**Architecture:** Keep OneOps as the experience layer, persistence owner, and integration owner. Keep dagengine as the execution kernel. Keep `agentruntime` as the async agent execution service. Add a stable orchestration runtime layer, a stable agent contract layer, and a template domain layer so one platform can support closure, diagnosis, and operation-assist workflows.

**Tech Stack:** Go, GORM/MySQL, Gin, dagengine, OneOps orchestration runtime registry, Nacos-backed platform config, Vue 3 / Ant Design Vue UI surfaces, existing execution observatory and detail debugger, production-style callback/approval flows.

---

## Planning Rule

This is the control plan for the whole platform, not a one-off feature plan.

- M1 closes the first production-meaningful mainline.
- M2 proves template-driven multi-domain reuse.
- M3 adds bounded autonomy only after M1 and M2 are operationally credible.
- New child plans are allowed, but only under one of these milestones.
- Any work that does not strengthen `real input`, `real output`, `human takeover`, or `operability` should be deprioritized.

## Current Baseline

The following foundation already exists and should be treated as in-progress platform assets, not throwaway demo work:

- `OneOps/app/orchestration/runtime/*.go`
  - runtime registry, flow step, agent step, callback wait, approval wait, external call, middleware
- `OneOps/app/orchestration/template/*.go`
  - template loader plus workflow/agents/manifest testdata
- `OneOps/app/orchestration/service/impl/*.go`
  - execution service, resume service, agent runtime client, agent task gateway, capability gateway, execution graph APIs
- `OneOps/app/agentruntime/service/*.go`
  - durable task repository, worker loops, callback retry, startup recovery, role registry, tool policy enforcement
- `OneOps/cmd/agentruntime/*.go`
  - production-shaped runtime bootstrap and Nacos-compatible config loading
- `OneOPS-UI/src/views/platform/*.vue`
  - execution observatory, execution detail debugger, agent detail, manual launch entry
- `docs/runbooks/alert-to-ticket-dagengine-mvp.md`
  - real local acceptance path for the first closure mainline

The immediate job is not to restart architecture work. The immediate job is to close the first platform mainline, then generalize it cleanly.

## Current Status Snapshot

The platform is no longer at the "can this even run" stage.

### Already materially established

- orchestration runtime foundation exists
- durable `agentruntime` exists
- callback and approval waiting are persistent concepts
- `role_ref`, `role_pack_ref`, and `strategy_ref` already participate in execution
- strategy-level runtime policy inheritance now covers:
  - `timeout_seconds`
  - `callback_max_retry`
  - `approval_required`

### Current weakest layer

The current weakest layer is `任务域`.

The code already carries `task_domain`, but it is still mostly:

- a template field
- a runtime label
- a routing hint

It is not yet a platform-owned contract object with strong validation and governed input/output semantics.

### Current active focus

The next mainline focus should therefore be:

- complete M1 closure hardening where needed
- then immediately raise `task_domain` into a governed contract layer for M2 reuse

This means the next child plan should focus on `Task Domain Contract Registry`, not on adding more isolated step features.

---

## Milestone M1: Platformized Closure Mainline

**Outcome:** One real multi-agent closure path can run repeatedly with durable waits, real callbacks, real operator takeover, and usable observability.

### Scope

- `alert -> ticket -> multi-agent coordination -> approval / callback -> closure trace`
- durable `agentruntime` workers and recovery
- callback wait and approval wait as persistent resumable states
- operator-facing takeover actions
- one real template that can be pilot-tested

### Files

#### Primary backend files

- `OneOps/app/orchestration/compiler/dagengine_compiler.go`
- `OneOps/app/orchestration/runtime/*.go`
- `OneOps/app/orchestration/service/impl/execution.go`
- `OneOps/app/orchestration/service/impl/resume.go`
- `OneOps/app/orchestration/service/impl/agent_task_gateway.go`
- `OneOps/app/orchestration/service/impl/execution_graph.go`
- `OneOps/app/orchestration/dto/*.go`
- `OneOps/app/orchestration/orchestration_model/*.go`
- `OneOps/app/agentruntime/service/*.go`
- `OneOps/cmd/agentruntime/*.go`

#### Primary UI files

- `OneOPS-UI/src/views/platform/ExecutionObservatory.vue`
- `OneOPS-UI/src/views/platform/ExecutionDetailDebugger.vue`
- `OneOPS-UI/src/views/platform/AgentDetail.vue`
- `OneOPS-UI/src/api/aiops.ts`
- `OneOPS-UI/src/typings/aiops.ts`

#### Primary template and ops files

- `OneOps/app/orchestration/template/testdata/multi_agent_ticket_closure/*.yaml`
- `docs/runbooks/alert-to-ticket-dagengine-mvp.md`
- `OneOps/scripts/start_multi_agent_closure_stack.sh`

### Task 1: Freeze The M1 Contract Surface

- [ ] Confirm the single supported M1 template contract:
  - alert input payload
  - ticket creation/update payload
  - agent task request/response payload
  - approval action payload
  - callback resume payload
- [ ] Remove or explicitly mark any temporary behavior that bypasses the intended async path.
- [ ] Ensure terminal semantics are explicit for:
  - `succeeded`
  - `failed`
  - `rejected`
  - `timed_out`
  - `escalated`
  - `action_required`
- [ ] Add or update tests in:
  - `OneOps/app/orchestration/runtime/*_test.go`
  - `OneOps/app/orchestration/service/impl/execution_test.go`
  - `OneOps/app/orchestration/service/impl/resume_test.go`

### Task 2: Close The Persistent Wait/Resume Loop

- [ ] Verify callback wait never relies on in-memory blocking or ad hoc polling.
- [ ] Verify approval wait is persisted, explicitly visible, and resumable after restart.
- [ ] Ensure `reject -> on_failure` and `timeout -> on_timeout` routing is deterministic and auditable.
- [ ] Refine terminal token semantics so operator actions such as escalation are first-class, not generic failures.
- [ ] Add restart and replay tests covering:
  - runtime restart while callback is pending
  - runtime restart while approval is pending
  - delayed callback after worker recovery
  - duplicate callback idempotency

### Task 3: Make Operator Takeover Production-Usable

- [ ] Ensure the execution detail page can clearly answer:
  - what is waiting
  - what failed
  - why it failed
  - what needs human action
  - how to resume or reject
- [ ] Ensure action-required records are persisted in OneOps-owned models and query APIs.
- [ ] Support minimum operator actions in real APIs:
  - approve
  - reject
  - resume callback
  - mark escalated follow-up
- [ ] Add API and UI tests for action-required visibility and action execution.

### Task 4: Convert The First Mainline Into A Pilot Asset

- [ ] Replace any remaining test-only closure assumptions with production-shaped configuration references.
- [ ] Make the real acceptance path use:
  - real OneOps APIs
  - real `agentruntime`
  - real DB persistence
  - real UI navigation
- [ ] Update `docs/runbooks/alert-to-ticket-dagengine-mvp.md` into an M1 pilot runbook with:
  - startup path
  - launch path
  - approval/callback path
  - failure drill
  - recovery drill
- [ ] Produce one repeatable acceptance command set:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
go test ./app/agentruntime/... ./cmd/agentruntime ./app/orchestration/runtime ./app/orchestration/service/impl -count=1
```

Expected:

```text
ok  	github.com/netxops/OneOps/app/agentruntime/...
ok  	github.com/netxops/OneOps/cmd/agentruntime
ok  	github.com/netxops/OneOps/app/orchestration/runtime
ok  	github.com/netxops/OneOps/app/orchestration/service/impl
```

- [ ] Produce one repeatable real-run acceptance path:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
./scripts/start_multi_agent_closure_stack.sh
```

Expected:

```text
stack started
agentruntime ready
oneops ready
manual launch URL printed
execution detail URL printed
```

### M1 Exit Criteria

- [ ] One real closure execution can be launched from the UI and traced end to end.
- [ ] Callback and approval waits survive process restarts.
- [ ] Failures become visible operator actions, not black holes.
- [ ] At least one real pilot workflow can be demonstrated to stakeholders.

---

## Milestone M2: Template-Driven Multi-Domain Platform

**Outcome:** The platform proves it is reusable. Changing template, agent strategy, and task domain changes the behavior more than changing core code.

### Scope

- keep the same runtime kernel
- keep the same agent contract layer
- add at least two more task domains beyond closure
- make agent catalog and tool policy materially change runtime behavior

### Files

- `OneOps/app/orchestration/template/define.go`
- `OneOps/app/orchestration/template/loader.go`
- `OneOps/app/orchestration/template/loader_test.go`
- `OneOps/app/orchestration/compiler/dagengine_compiler.go`
- `OneOps/app/orchestration/runtime/registry.go`
- `OneOps/app/orchestration/runtime/types.go`
- `OneOps/app/orchestration/dto/agent_task.go`
- `OneOps/app/agentruntime/service/roles.go`
- `OneOps/app/agentruntime/service/role_*.go`
- `OneOps/app/orchestration/template/testdata/*`
- `docs/runbooks/*`

### Task 5: Formalize The Template Domain Model

- [ ] Split template concerns into explicit layers:
  - process definition
  - agent strategy definition
  - task-domain definition
- [ ] Promote `task_domain` from string-like metadata into a registry-backed contract definition with:
  - required context keys
  - expected result type
  - required result payload keys
  - allowed role packs
  - default runtime policy
  - allowed terminal semantics
- [ ] Add typed template fields for:
  - domain name
  - strategy/profile
  - agent catalog bindings
  - tool policy references
  - approval policy references
  - external target references
- [ ] Prefer references to platform-owned configuration instead of large inline blobs.
- [ ] Add loader validation so invalid template combinations fail before execution.
- [ ] Add at least one new template fixture each for:
  - diagnosis / RCA
  - operation / inspection / change-assist

### Task 6: Strengthen The Agent Contract Layer

- [ ] Formalize the stable contract for each agent task:
  - role identity
  - allowed tools
  - required input fields
  - result type
  - next-hint semantics
  - escalation semantics
- [ ] Ensure `RoleRegistry` behaves like a registry-driven runtime, not a growing switch statement.
- [ ] Introduce versioned result typing where needed so different domains can reuse the same runtime safely.
- [ ] Add contract tests per role to verify:
  - required tools are present
  - payload enrichment is present
  - unsupported tools are blocked
  - malformed results fail fast

### Task 7: Prove Multi-Domain Reuse With Real Templates

- [ ] Add one diagnosis template with a real execution story:
  - alert ingestion
  - evidence collection
  - diagnosis summary
  - human review or follow-up
- [ ] Add one operation-assist template with a real execution story:
  - checklist or SOP steps
  - approval checkpoint
  - execution tracking
  - operator closure
- [ ] Ensure these domains reuse:
  - the same wait/resume system
  - the same agent task system
  - the same observability pages
  - the same action-required handling
- [ ] Document per-domain acceptance criteria and runbooks.

### M2 Exit Criteria

- [ ] At least three domains run on the same platform:
  - closure
  - diagnosis / RCA
  - operation-assist
- [ ] Adding a new domain is primarily template/config work.
- [ ] Runtime rewrites are not required for normal domain onboarding.
- [ ] Agent strategy changes can be expressed without changing core wait/resume code.

---

## Milestone M3: Controlled Autonomy

**Outcome:** The platform supports useful autonomy while keeping execution bounded, explainable, interruptible, and recoverable.

### Scope

- bounded task decomposition
- structured multi-agent handoff objects
- policy and budget controls
- mandatory return-to-human path for risk conditions

### Files

- `OneOps/app/agentruntime/service/runtime.go`
- `OneOps/app/agentruntime/service/task_runtime.go`
- `OneOps/app/agentruntime/service/roles.go`
- `OneOps/app/agentruntime/service/role_*.go`
- `OneOps/app/orchestration/runtime/agent_step.go`
- `OneOps/app/orchestration/dto/agent_task.go`
- `OneOps/app/orchestration/orchestration_model/agent_task.go`
- `OneOPS-UI/src/views/platform/AgentDetail.vue`
- `OneOPS-UI/src/views/platform/ExecutionDetailDebugger.vue`

### Task 8: Add Bounded Decomposition Instead Of Freeform Agent Society

- [ ] Define where decomposition is allowed:
  - only inside approved template boundaries
  - only for specific role types
  - only within configured budget and tool limits
- [ ] Represent subtask creation as structured records, not hidden chain-of-thought.
- [ ] Persist agent-to-agent handoff artifacts so operators can audit:
  - why a subtask was created
  - what inputs were passed
  - what tools were allowed
  - how the subtask ended
- [ ] Ensure autonomy failure always routes back to operator-visible states.

### Task 9: Add Explanation And Control Surfaces

- [ ] Extend UI and APIs to show:
  - agent plan summary
  - subtask list
  - used tools
  - budget consumption
  - escalation reason
- [ ] Add operator controls for:
  - cancel
  - force human takeover
  - retry with narrowed policy
  - continue after review
- [ ] Keep explanations structured and operational, not vague reasoning text dumps.

### M3 Exit Criteria

- [ ] Agents can decompose work in bounded scenarios.
- [ ] Autonomy is observable, budgeted, and interruptible.
- [ ] High-risk decisions still require human gatekeeping.
- [ ] The platform remains operationally understandable after autonomy is introduced.

---

## Cross-Cutting Workstreams

### Task 10: Production Config And Deployment Simplification

- [ ] Keep startup simple by preferring platform config and Nacos bootstrap over one-off environment toggles.
- [ ] Ensure `agentruntime` and OneOps use the same operational source of truth where possible.
- [ ] Keep environment variables as override-only or emergency controls.
- [ ] Add deployment notes for:
  - local acceptance
  - pre-production
  - production bootstrap

### Task 11: Observability And Validation

- [ ] Keep visual surfaces lightweight but useful now; do not turn visual orchestration editing into the main priority yet.
- [ ] Prioritize:
  - execution observatory
  - execution detail debugger
  - agent task detail
  - action-required visibility
- [ ] Add evidence-oriented validation artifacts:
  - test commands
  - real execution screenshots or URLs
  - failure drill results
  - recovery drill results

### Task 12: Toy-Prevention Gate

- [ ] Before starting any major new feature, ask:
  - does it use real input
  - does it produce real output
  - is there human takeover
  - is it operable
- [ ] If the answer is no to any item, reduce scope or defer the work.

---

## Recommended Execution Order

- [ ] Finish M1 close-out first.
- [ ] Create one short child plan for remaining M1 gaps if needed.
- [ ] After M1 acceptance is repeatable, start M2 domain expansion.
- [ ] Start M3 only after M2 proves real reuse.

---

## Definition Of Done For The Platform Phase

This master plan is successful when all of the following are true:

- [ ] OneOps can run a real multi-agent closure workflow end to end.
- [ ] The same platform can run at least two additional task domains by switching templates and strategy.
- [ ] `agentruntime` is not a toy executor; it is a durable controlled execution service.
- [ ] Operators can observe, intervene, resume, reject, escalate, and audit all meaningful waits and failures.
- [ ] Increased agent autonomy does not reduce control or operability.
