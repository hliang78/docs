# Task Config Reference

This is the compact reference for `docs/openclaw-autodev/loops/*.conf`.

Use it when creating or reviewing a loop config. Treat the actual loop file and
controller behavior as authoritative.

## Identity And Routing

- `TASK_ID`: unique task/lane id; must match the filename.
- `AGENT_ID`: worker agent id, usually equal to `TASK_ID`.
- `ENABLED`: whether the pool may schedule the task.
- `PROJECT_ROOT`: root directory the worker should treat as its execution
  workspace.

## Contract Docs

- `CHARTER_DOC`: long-lived task charter or program brief.
- `RUNTIME_DOC`: runtime contract document.
- `CHECKLIST_DOC`: closure state machine when the task uses checklist-driven
  progression.
- `BACKLOG_DOC`: backlog source when backlog continuation is required.
- `COORDINATION_DOC`: task-local coordination surface.
- `SHARED_DOCS`: shared coordination docs used across lanes.
- `CONTEXT_DOCS`: compact context pack preferred over broad charter/backlog
  reading.

## Story And Evidence

- `STORY_FILE`: story queue for bounded execution units.
- `EVIDENCE_DIR`: durable evidence root for this task.

## Validation And Precheck

- `WORKER_VALIDATION_COMMAND`: optional worker-facing validation text or light
  checks when the loop needs controller-side final verification to stay
  authoritative.
- `VALIDATION_COMMAND`: worker-visible acceptance commands.
- `PRECHECK_COMMAND`: environment truth gate before the worker starts.
- `CONTROLLER_VERIFY_ON_DONE`: whether controller reruns verification after a
  worker reports `DONE`.
- `CONTROLLER_VERIFY_COMMAND`: exact controller-side verify command.
- `POST_BLOCK_COMMAND`: optional controller-side follow-up command run after a
  block finishes and state/handoff are written.
- `SHELL_TURN_COMMAND`: use a shell turn instead of a model worker for
  validation-only lanes such as CT.

## Scope And Writes

- `ALLOWED_WRITES`: filesystem write whitelist.
- `PATCH_MAX_FILES`: maximum patch breadth for weak/local workers.
- `EXTRA_RULES`: task-specific boundaries that cannot yet be expressed as
  structure.
- `READ_BUDGET_RULES`: read-order and context-budget rules.

## Worker Selection

- `AGENT_MODEL`: model/provider path.
- `AGENT_PROFILE`: alternate OpenClaw runtime profile.
- `PROVIDER_PROBE_MODEL`: health probe model path.
- `HARNESS_PROFILE`: behavior harness name such as `strict-worker`.
- `HARNESS_CONTRACT_DOC`: compact profile contract note injected into prompt.
- `THINKING`: model reasoning mode when supported.

## Runtime Environment

- `RUNTIME_ENV_FILE` / `RUNTIME_ENV_FILES`: runtime-only secret sources.
- If `RUNTIME_ENV_FILE` is unset and `AGENT_PROFILE` is set, the controller
  also tries `~/.openclaw-<AGENT_PROFILE>/runtime.env`.
- `MAX_TURNS`: bounded turns per loop block.
- `MAX_MINUTES`: bounded wall-clock budget.
- `TIMEOUT_SECONDS`: hard command/worker timeout.
- `DAEMON_SLEEP_SECONDS`: delay between daemon blocks.
- `CONTINUE_AFTER_DONE`: whether the daemon should keep scanning after a story
  finishes.

## Adaptation Guidance

For weak workers, a good config should make these items explicit:

- copied workspace or product workspace truth source;
- precheck and runtime ownership;
- allowed action surface, not just allowed writes;
- targeted validation for the selected story;
- bounded patch width;
- recovery expectations after verify failure.

See also:

- `docs/openclaw-autodev/worker-adaptation-principles.md`
- `docs/openclaw-autodev/worker-capability-schema.json`
- `docs/openclaw-autodev/story-execution-pack-schema.json`
