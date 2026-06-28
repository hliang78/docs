# OneOps AgentRuntime Mainline Readiness Review

## Purpose

This review does **not** evaluate future platform ambitions.
It evaluates only the current mainline:

- OneOps orchestration runtime
- durable `agentruntime`
- wait / resume / restart behavior
- local operator and acceptance path

The question is:

> Is the current mainline only a runnable demo, or is it a production-meaningful runtime path?

## Executive Summary

The answer is mixed:

- The orchestration runtime path is real.
- Durable task persistence is real.
- Wait, resume, and restart recovery are real.
- The helper and acceptance entrypoints are real enough to verify closure.

But the agent-execution layer is not yet fully real:

- current default agent roles are stub handlers
- service-to-service auth still has a debug fallback path
- some task-level strategy fields are propagated but not truly enforced

So the most accurate current statement is:

> This is a **real orchestration runtime closure**, but **not yet a fully real multi-agent business execution closure**.

## What Is Already Real

### Real runtime behavior

- orchestration compiles templates into executable runtime steps
- agent tasks are durably submitted into MySQL-backed `agentruntime_tasks`
- execution worker and callback worker run asynchronously
- `waiting_approval` and `waiting_callback` are persisted rather than held in memory
- restart recovery works and has real acceptance evidence

### Real operator verification path

- `./scripts/start_multi_agent_closure_stack.sh acceptance`
- `./scripts/start_multi_agent_closure_stack.sh acceptance-restart`
- real evidence JSON and markdown are written under `docs/openclaw-autodev/evidence/orchestration/**`

## Readiness Classification

### P0: Must Fix Before Claiming “Real Multi-Agent Execution”

#### P0-1 Default role handlers are still stub logic

Impact:

- current “multi-agent” execution is structurally real, but business behavior is still placeholder behavior
- flow can finish successfully without any true external capability execution

Evidence:

- [role_analysis.go](/home/jacky/project/OneOPS-ALL/OneOps/app/agentruntime/service/role_analysis.go:25)
- [role_dispatch.go](/home/jacky/project/OneOPS-ALL/OneOps/app/agentruntime/service/role_dispatch.go:40)
- [role_tracking.go](/home/jacky/project/OneOPS-ALL/OneOps/app/agentruntime/service/role_tracking.go:19)
- [role_knowledge.go](/home/jacky/project/OneOPS-ALL/OneOps/app/agentruntime/service/role_knowledge.go:20)
- [main.go](/home/jacky/project/OneOPS-ALL/OneOps/cmd/agentruntime/main.go:72)

Problem detail:

- handlers validate required tool names only as strings
- handlers do not call real ticketing, scheduling, topology, knowledge, or LLM backends
- returned payloads are deterministic placeholders

Exit criterion:

- at least one primary role in the current `multi-agent-closure` template must execute through a real adapter rather than a stub result builder

#### P0-2 Callback auth still falls back to debug token

Impact:

- production runtime auth is not cleanly separated from debug auth
- config mistakes can be hidden by fallback behavior

Evidence:

- [runtime_config.go](/home/jacky/project/OneOPS-ALL/OneOps/app/agentruntime/service/runtime_config.go:35)
- [config.go](/home/jacky/project/OneOPS-ALL/OneOps/config/config.go:52)

Problem detail:

- `CallbackAuthToken` silently falls back to `DebugToken`
- this makes service-to-service auth less strict than it appears

Exit criterion:

- callback auth must require an explicit runtime token in runtime config
- missing callback token must fail startup or fail callback use clearly

### P1: Strongly Recommended Before Claiming “Production-Meaningful Mainline”

#### P1-1 Task-level strategy contract is only partially enforced

Impact:

- templates can express more than runtime currently honors
- authors may assume task-level controls are live when they are not

Evidence:

- [task.go](/home/jacky/project/OneOPS-ALL/OneOps/app/agentruntime/agentruntime_model/task.go:30)
- [runtime.go](/home/jacky/project/OneOPS-ALL/OneOps/app/agentruntime/service/runtime.go:107)
- [task_runtime.go](/home/jacky/project/OneOPS-ALL/OneOps/app/agentruntime/service/task_runtime.go:186)

Problem detail:

- `timeout_seconds`, `approval_required`, and related policy fields are propagated and persisted
- runtime behavior clearly uses task-level callback retry
- runtime does not clearly enforce task-level timeout
- runtime does not clearly enforce task-level approval semantics inside `agentruntime`

Exit criterion:

- either enforce these fields in runtime behavior
- or remove/de-scope them from the current mainline contract so templates cannot pretend they are active

#### P1-2 Registry sources are duplicated in code

Impact:

- role packs, roles, and task domains can drift
- template portability and governance become fragile as scope expands

Evidence:

- [roles.go](/home/jacky/project/OneOPS-ALL/OneOps/app/agentruntime/service/roles.go:77)
- [roles.go](/home/jacky/project/OneOPS-ALL/OneOps/app/agentruntime/service/roles.go:233)
- [runtime.go](/home/jacky/project/OneOPS-ALL/OneOps/app/agentruntime/service/runtime.go:38)
- [task_runtime.go](/home/jacky/project/OneOPS-ALL/OneOps/app/agentruntime/service/task_runtime.go:54)
- [task_domain_contract.go](/home/jacky/project/OneOPS-ALL/OneOps/app/agentruntime/service/task_domain_contract.go:11)
- [loader.go](/home/jacky/project/OneOPS-ALL/OneOps/app/orchestration/template/loader.go:241)

Problem detail:

- several layers instantiate their own default registries
- there is no single injected source of truth for runtime capability contracts

Exit criterion:

- mainline should read role packs and task-domain contracts from one owned registry source per process

#### P1-3 Worker readiness is too optimistic

Impact:

- runtime can report ready while worker passes are repeatedly failing
- operator and scheduler trust can be misplaced

Evidence:

- [task_worker.go](/home/jacky/project/OneOPS-ALL/OneOps/app/agentruntime/service/task_worker.go:59)
- [task_worker.go](/home/jacky/project/OneOPS-ALL/OneOps/app/agentruntime/service/task_worker.go:89)
- [task_worker.go](/home/jacky/project/OneOPS-ALL/OneOps/app/agentruntime/service/task_worker.go:140)

Problem detail:

- `ready=true` is set after worker loops start
- later pass failures only log warnings
- readiness does not degrade on sustained runtime failure

Exit criterion:

- readiness should reflect operational ability, not only loop startup

### P2: Cleanup Items That Still Signal “Demo Surface”

#### P2-1 Acceptance and helper defaults still carry local-demo assumptions

Impact:

- operator surface still leaks local bootstrap expectations
- “real path” and “demo path” are not visually separated enough

Evidence:

- [start_multi_agent_closure_stack.sh](/home/jacky/project/OneOPS-ALL/OneOps/scripts/start_multi_agent_closure_stack.sh:21)
- [start_multi_agent_closure_stack.sh](/home/jacky/project/OneOPS-ALL/OneOps/scripts/start_multi_agent_closure_stack.sh:22)
- [multi-agent-ticket-closure-real-api-acceptance.ts](/home/jacky/project/OneOPS-ALL/OneOPS-UI/scripts/multi-agent-ticket-closure-real-api-acceptance.ts:46)
- [multi-agent-ticket-closure-real-api-acceptance.ts](/home/jacky/project/OneOPS-ALL/OneOPS-UI/scripts/multi-agent-ticket-closure-real-api-acceptance.ts:49)
- [restart-resume-real-api-acceptance.ts](/home/jacky/project/OneOPS-ALL/OneOPS-UI/scripts/restart-resume-real-api-acceptance.ts:37)
- [restart-resume-real-api-acceptance.ts](/home/jacky/project/OneOPS-ALL/OneOPS-UI/scripts/restart-resume-real-api-acceptance.ts:40)

Problem detail:

- default `admin/admin@123`
- acceptance scripts still contain legacy API-base fallback assumptions

Exit criterion:

- local verification helpers should be explicit about “dev-only defaults”
- production-meaningful paths should require deliberate runtime configuration

## Consistency Review

### Good consistency

- wait-state persistence is consistent with restart-resume acceptance
- orchestration-to-agentruntime task metadata propagation is consistent for:
  - `task_domain_ref`
  - `role_pack_ref`
  - `callback_max_retry`
- Nacos bootstrap is the intended main config source for the helper-driven runtime path

### Current inconsistencies

- “agent strategy richness” in template contracts is ahead of actual runtime enforcement
- “real multi-agent” wording is ahead of actual role implementation reality
- “runtime auth” is less strict than production wording suggests because of debug-token fallback

## Redundancy / Fallback / Demo Review

### Acceptable fallback

- helper launch mode choosing `systemd` or `nohup`
- acceptance login using explicit token when available, login only as a convenience path

### Risky fallback

- callback auth token falling back to debug token
- runtime semantics implied by stored fields but not truly enforced

### Demo residue still visible

- stub role handlers
- local default credentials in helper / acceptance scripts
- legacy local API-base fallbacks in acceptance scripts

## Final Judgment

### If the claim is:

> “We have a real orchestration runtime with durable agent task execution, wait persistence, and restart recovery.”

Judgment:

- **Yes**

### If the claim is:

> “We have a real multi-agent business execution platform where agents are already doing real work.”

Judgment:

- **No, not yet**

## Minimal Mainline Hardening Order

1. Remove callback auth fallback to debug token.
2. Replace at least one primary default role with a real adapter-backed implementation.
3. Decide whether task-level timeout / approval are real runtime contracts or not.
4. Collapse runtime capability registries toward a single source of truth.
5. Make readiness reflect sustained worker health.
6. Clean up demo defaults from helper and acceptance surfaces.

## Recommended Use Of This Review

Use this document as the single readiness checklist for the current mainline.

Do **not** mix it with:

- future capability marketplace work
- visual orchestration/editor ambitions
- generalized agent-society architecture

Those belong to later plans.
