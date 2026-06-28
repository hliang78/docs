# AgentRuntime M1 Closure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close the current long task into a real M1 production-style orchestration mainline: OneOps compiles and runs a template, `agentruntime` executes durable agent tasks, waits survive restart, and the full path is reproducible through scripts, evidence, and runbooks.

**Architecture:** Treat the current durable `agentruntime` implementation as the baseline and stop expanding sideways. This phase is not about inventing new agent platform layers. It is about hard-closing the mainline with one real execution path, one real restart/recovery path, and one stable operational entrypoint. Anything that does not directly strengthen that closure is explicitly deferred.

**Tech Stack:** Go, GORM/MySQL, Gin, Nacos-backed config bootstrap, OneOps orchestration runtime, `agentruntime`, real API acceptance scripts, shell helper scripts, evidence markdown/json.

---

## Closure Definition

This long task is considered **closed** only if all of the following are true:

1. A real orchestration template can trigger a real multi-agent execution path end-to-end.
2. `agentruntime` runs as a durable task runtime backed by MySQL rather than in-memory blocking behavior.
3. `waiting_approval` and `waiting_callback` executions survive service restart and can be resumed to completion through real APIs.
4. The local operator path is reproducible through a small set of stable commands, with evidence files and runbook instructions that match the current system.

If all four are true, M1 is closed even if broader platform ambitions are still deferred.

## Scope Lock

### In Scope For This Closure

- Durable task submission and worker execution in `agentruntime`
- Callback retry and startup recovery behavior
- Approval wait and callback wait persistence plus resume APIs
- Real `acceptance` and `acceptance-restart` entrypoints
- Task-domain and role-pack references flowing through the current template/runtime path
- Runbook, evidence, and verification commands for the above

### Explicitly Out Of Scope For This Closure

- Fully generic agent society or autonomous task decomposition
- Rich capability marketplace or policy governance UI
- General visual orchestration/designer platform
- Multi-tenant production hardening beyond the current local-first production-style path
- Broad template family rollout across many task domains

These are M2+ topics. They must not block M1 closure.

## Reality Check

The current codebase already satisfies most of M1 in substance:

- [x] Durable runtime files exist and are wired:
  - `OneOps/app/agentruntime/agentruntime_model/task.go`
  - `OneOps/app/agentruntime/service/task_repository.go`
  - `OneOps/app/agentruntime/service/task_worker.go`
  - `OneOps/app/agentruntime/service/task_runtime.go`
  - `OneOps/app/agentruntime/service/runtime_config.go`
  - `OneOps/cmd/agentruntime/main.go`
- [x] Orchestration `task_domain_ref` and `role_pack_ref` flow through compiler/runtime contracts:
  - `OneOps/app/orchestration/compiler/dagengine_compiler.go`
  - `OneOps/app/orchestration/runtime/step_contract.go`
  - `OneOps/app/orchestration/runtime/agent_step.go`
- [x] Wait-state persistence and resume APIs are real, not simulated in-memory
- [x] Restart-survivable acceptance has already succeeded with real evidence:
  - `docs/openclaw-autodev/evidence/orchestration/restart-resume-real-api/20260628-100046-restart-resume-real-api-acceptance.md`
- [x] Mainline runbook has been updated to the real `8380` API path and `acceptance-restart` command

The remaining work is therefore **closure hardening and formal sign-off**, not a fresh architecture build.

## Latest Verification Snapshot

Latest successful verification bundle:

- Focused Go regression:
  - `cd /home/jacky/project/OneOPS-ALL/OneOps && go test ./app/agentruntime/... ./app/orchestration/runtime ./app/orchestration/service/impl -count=1`
- Real multi-agent acceptance evidence:
  - `docs/openclaw-autodev/evidence/orchestration/multi-agent-ticket-closure-real-api/20260628-101016-multi-agent-ticket-closure-real-api-acceptance.json`
  - `docs/openclaw-autodev/evidence/orchestration/multi-agent-ticket-closure-real-api/20260628-101016-multi-agent-ticket-closure-real-api-acceptance.md`
- Real restart-resume acceptance evidence:
  - `docs/openclaw-autodev/evidence/orchestration/restart-resume-real-api/20260628-100921-restart-resume-real-api-acceptance.json`
  - `docs/openclaw-autodev/evidence/orchestration/restart-resume-real-api/20260628-100921-restart-resume-real-api-acceptance.md`

Note:

- An earlier `acceptance` attempt failed only because it was incorrectly run in parallel with `acceptance-restart`, and the restart flow intentionally bounced the shared local services mid-poll.
- The clean sequential rerun succeeded, so this is not treated as a product gap.

Related structural review:

- `docs/superpowers/2026-06-28-oneops-agentruntime-mainline-readiness-review.md`
- This review is the current source of truth for readiness blockers on the existing mainline.

## Files That Matter For M1 Closure

### Runtime Mainline

- `OneOps/app/agentruntime/service/runtime.go`
  - durable submit path and request validation
- `OneOps/app/agentruntime/service/task_repository.go`
  - durable task lifecycle persistence
- `OneOps/app/agentruntime/service/task_worker.go`
  - execution worker, callback worker, recovery loop
- `OneOps/app/agentruntime/service/task_runtime.go`
  - execution-to-callback state machine
- `OneOps/app/agentruntime/service/runtime_config.go`
  - Nacos-loaded runtime configuration contract
- `OneOps/cmd/agentruntime/main.go`
  - runtime bootstrap, migration, worker startup

### Orchestration Mainline

- `OneOps/app/orchestration/compiler/dagengine_compiler.go`
  - compile current template contract into dagengine payload
- `OneOps/app/orchestration/service/impl/agent_runtime_client.go`
  - real submit path into `agentruntime`
- `OneOps/app/orchestration/runtime/agent_step.go`
  - current node-to-agent-task translation
- `OneOps/app/orchestration/runtime/approval_wait_step.go`
  - durable approval wait semantics
- `OneOps/app/orchestration/runtime/callback_wait_step.go`
  - durable callback wait semantics

### Operator / Acceptance Surface

- `OneOps/scripts/start_multi_agent_closure_stack.sh`
  - stable operator entrypoint
- `OneOPS-UI/scripts/multi-agent-ticket-closure-real-api-acceptance.ts`
  - real end-to-end multi-agent acceptance
- `OneOPS-UI/scripts/restart-resume-real-api-acceptance.ts`
  - restart + resume acceptance
- `docs/runbooks/alert-to-ticket-dagengine-mvp.md`
  - operator instructions and evidence path

## Remaining Gap Analysis

There are only three remaining categories that can still block closure:

### Gap 1: Repeatability Gap

Question: can a second operator rerun the same commands and get the same behavior without tribal knowledge?

Blocking symptom:
- Commands drift from reality
- Ports or config sources are ambiguous
- Evidence paths are not obvious

Closure answer:
- lock the official commands to `start`, `acceptance`, `acceptance-restart`, `status`, `stop`
- lock OneOps API to `8380` and UI to `3001` for the local runbook path
- keep Nacos as the runtime-settings source of truth

### Gap 2: Mainline Verification Gap

Question: do we have one compact verification bundle that proves the current mainline still works?

Blocking symptom:
- individual features pass, but no compact “M1 pass/fail” view exists

Closure answer:
- run one focused verification batch:
  - `go test ./app/agentruntime/... ./app/orchestration/runtime ./app/orchestration/service/impl -count=1`
  - `./scripts/start_multi_agent_closure_stack.sh acceptance`
  - `./scripts/start_multi_agent_closure_stack.sh acceptance-restart`

### Gap 3: Scope Discipline Gap

Question: are we still trying to close M1 while quietly building M2?

Blocking symptom:
- work keeps being redirected into agent packs, visual editors, or generalized frameworkization

Closure answer:
- treat those items as backlog only
- do not reopen architecture unless a defect blocks the three mainline verification commands above

## Task 1: Freeze The M1 Closure Boundary

**Files:**
- Modify: `docs/superpowers/plans/2026-06-27-agentruntime-first-production-implementation-plan.md`

- [x] **Step 1: Replace the broad buildout plan with a closure plan**

This document now serves as the closure contract rather than a historical construction log.

- [x] **Step 2: Define M1 strictly by executable mainline behavior**

The closure definition in this file now requires:

- one real multi-agent execution path
- one real restart/recovery path
- one stable operator entrypoint
- one matching runbook/evidence bundle

- [x] **Step 3: Mark non-blocking ambitions as out of scope**

Deferred items are now explicitly listed so they do not block sign-off.

## Task 2: Run The Final Mainline Verification Bundle

**Files:**
- Evidence: `docs/openclaw-autodev/evidence/orchestration/**`
- Runbook: `docs/runbooks/alert-to-ticket-dagengine-mvp.md`

- [x] **Step 1: Run focused Go regression**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
go test ./app/agentruntime/... ./app/orchestration/runtime ./app/orchestration/service/impl -count=1
```

Latest result:

```text
?   	github.com/netxops/OneOps/app/agentruntime/agentruntime_model	[no test files]
ok  	github.com/netxops/OneOps/app/agentruntime/api	0.114s
?   	github.com/netxops/OneOps/app/agentruntime/dto	[no test files]
ok  	github.com/netxops/OneOps/app/agentruntime/service
ok  	github.com/netxops/OneOps/app/orchestration/runtime
ok  	github.com/netxops/OneOps/app/orchestration/service/impl
```

- [x] **Step 2: Run the real multi-agent acceptance path**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
./scripts/start_multi_agent_closure_stack.sh acceptance
```

Latest result:

```text
Observatory URL: http://127.0.0.1:3001/#/platform/execution-observatory
Execution ID: be74794c-d577-4ea6-b336-e1d53b34fa5f
Evidence JSON: /home/jacky/project/OneOPS-ALL/docs/openclaw-autodev/evidence/orchestration/multi-agent-ticket-closure-real-api/20260628-101016-multi-agent-ticket-closure-real-api-acceptance.json
Evidence Markdown: /home/jacky/project/OneOPS-ALL/docs/openclaw-autodev/evidence/orchestration/multi-agent-ticket-closure-real-api/20260628-101016-multi-agent-ticket-closure-real-api-acceptance.md
```

- [x] **Step 3: Run the real restart-resume acceptance path**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
./scripts/start_multi_agent_closure_stack.sh acceptance-restart
```

Latest result:

```text
Approval Execution ID: fe7ef02c-2e45-4675-96b6-9c7ae2e39f79
Callback Execution ID: 7c757a7f-f403-4e63-b871-149f04bc56a8
Evidence JSON: /home/jacky/project/OneOPS-ALL/docs/openclaw-autodev/evidence/orchestration/restart-resume-real-api/20260628-100921-restart-resume-real-api-acceptance.json
Evidence Markdown: /home/jacky/project/OneOPS-ALL/docs/openclaw-autodev/evidence/orchestration/restart-resume-real-api/20260628-100921-restart-resume-real-api-acceptance.md
```

- [x] **Step 4: Confirm acceptance-restart proves restart-survivable waits**

Confirmed by latest evidence content:

- before restart: `waiting_approval` and `waiting_callback`
- after restart: still `waiting_approval` and `waiting_callback`
- final status: both `completed`

- [x] **Step 5: If any command fails, fix only closure-blocking defects**

Allowed fixes:

- helper script drift
- acceptance script drift
- runtime config/bootstrap mismatch
- resume/recovery regression

Not allowed:

- new platform concepts
- generic framework expansion
- unrelated refactors

Applied in this verification round:

- treated the earlier parallel-run failure as an execution-method issue rather than a product defect
- reran `acceptance-restart` and `acceptance` sequentially to obtain clean closure evidence

## Task 3: Produce The M1 Sign-Off Record

**Files:**
- Modify: `docs/runbooks/alert-to-ticket-dagengine-mvp.md`
- Modify: `docs/superpowers/plans/2026-06-27-agentruntime-first-production-implementation-plan.md`

- [x] **Step 1: Record the final evidence paths in the working summary**

Capture:

- latest `acceptance` evidence markdown/json
- latest `acceptance-restart` evidence markdown/json
- final test command and result

- [x] **Step 2: Verify the runbook still matches reality**

Runbook must match:

- API base `http://127.0.0.1:8380/api/v1`
- UI observatory `http://127.0.0.1:3001/#/platform/execution-observatory`
- `./scripts/start_multi_agent_closure_stack.sh acceptance`
- `./scripts/start_multi_agent_closure_stack.sh acceptance-restart`

- [x] **Step 3: Mark M1 closed only if all closure-definition items are true**

Pass checklist:

- durable agentruntime mainline is real
- wait/resume persistence is real
- restart recovery is real
- operator path is reproducible

Current result:

- all closure-definition items are true
- no remaining blocker is required for M1 sign-off
- M1 can now be treated as closed

## Decision Rule

This plan should **not** drift into additional implementation unless one of these is still false:

1. `acceptance` fails
2. `acceptance-restart` fails
3. focused Go regression fails
4. runbook does not match the real commands

If all four pass, the correct next action is:

- declare **M1 closure complete**
- open a new M2 plan for:
  - capability/role-pack registry hardening
  - multi-template task-domain expansion
  - visualization and debugging upgrades
  - broader production hardening

## Current Read On Closure Feasibility

Based on the current code and already-produced evidence, this long task **can reach closure**. The main risk is no longer architecture risk; it is verification discipline. The code already contains the durable runtime, restart recovery path, resume APIs, and acceptance entrypoints. The only way this long task fails to close is if we keep expanding the target instead of finishing the verification-and-sign-off loop.

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-06-27-agentruntime-first-production-implementation-plan.md`. Two execution options:

1. Subagent-Driven (recommended) - I dispatch a fresh subagent per task, review between tasks, fast iteration
2. Inline Execution - Execute tasks in this session using executing-plans, batch execution with checkpoints
