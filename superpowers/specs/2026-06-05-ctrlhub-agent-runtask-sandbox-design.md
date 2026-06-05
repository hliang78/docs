# Ctrlhub Agent RunTask Sandbox Design

## Goal

Make `ctrlhub` agent `RunTask` execution resilient by running each remote task in its own systemd-managed cgroup, so a failed or runaway task is bounded by task-level resource limits and can be stopped without destabilizing the agent process.

This design covers `RunTask` execution for shell, Ansible, Terraform, OpenTofu, and Terragrunt. It does not containerize Telegraf input plugins in this phase.

## Current State

The agent exposes `RunTask` as a Bidi RPC capability in `ctrlhub/controller/agent/cmd/agent/capabilities.go`. The execution path enters `AgentService.handleRunTask` in `ctrlhub/controller/agent/cmd/agent/agent_service.go`, prepares a task workspace under `workspace/tasks/<task_id>`, and dispatches by `app_type`.

The final command execution currently uses `exec.CommandContext` directly from the agent process. This gives cancellation through Go context, but it does not provide task-level CPU, memory, process-count, runtime, or filesystem isolation. The agent service unit has baseline hardening, but child tasks still share the same service cgroup and effective runtime environment.

## Desired Behavior

Each `RunTask` command must execute under a distinct systemd transient service named from the task id, for example `oneops-task-<sanitized-task-id>.service`. A scope backend can be added later, but the MVP uses transient services because `RuntimeMaxSec`, output capture, and `systemctl stop` semantics are clearer.

The task sandbox must enforce default limits:

- `MemoryMax`: `1G`
- `CPUQuota`: `100%`
- `TasksMax`: `256`
- `RuntimeMaxSec`: `1800`
- `KillMode`: `control-group`
- `WorkingDirectory`: the prepared task run directory

The limits must be configurable from agent YAML under a `task_sandbox` section. Defaults must preserve a useful local development experience while being safe enough for production rollout.

`StopTask` must stop the systemd transient service for the requested task. It must also cancel the Go context to preserve current behavior for non-systemd and in-process cleanup paths.

If systemd sandboxing is enabled but `systemd-run` is unavailable, `RunTask` must fail with a structured, actionable error. A compatibility fallback to the legacy direct executor may exist behind an explicit config flag, but it must be disabled by default in production-oriented configs.

## Architecture

Introduce a focused execution abstraction in the agent package:

```go
type TaskSandboxRunner interface {
	Run(ctx context.Context, req SandboxRunRequest) (SandboxRunResult, error)
	Stop(ctx context.Context, taskID string) error
}
```

`SandboxRunRequest` contains task identity, working directory, executable path, arguments, environment, resource limits, and log callbacks. `SandboxRunResult` contains command output summary, exit status, sandbox name, and duration.

The first implementation is `SystemdTaskSandboxRunner`. It wraps commands with `systemd-run` and waits for completion while streaming stdout and stderr back through the existing task log reporting functions.

The existing shell, Ansible, Terraform, OpenTofu, and Terragrunt functions continue to build their command, args, working directory, and environment. They then call a single helper that delegates to `TaskSandboxRunner` instead of calling `exec.CommandContext` directly.

## Data Flow

1. Controller calls `RunTask`.
2. Agent resolves material and validates `TaskExecutionProfile`.
3. Agent prepares `workspace/tasks/<task_id>`.
4. The app-specific runner builds the command:
   - shell: script path or `sh -c <arguments>`
   - Ansible: `ansible-playbook ...`
   - Terraform family: `<terraform|tofu|terragrunt> init`, then `apply`
5. Agent creates a sandbox request with task id, cwd, env, command, args, and limits.
6. `SystemdTaskSandboxRunner` launches `systemd-run` with transient properties and a wrapped command.
7. Output is streamed to existing task log reporting.
8. Exit status maps to existing `success`, `failed`, or `cancelled` response values.
9. Successful tasks remove the prepared workspace. Failed and cancelled tasks keep the workspace for diagnostics, matching current behavior.

## Configuration

Add a config section to `ctrlhub/controller/agent/pkg/config`:

```yaml
task_sandbox:
  enabled: true
  backend: systemd
  allow_legacy_fallback: false
  memory_max: 1G
  cpu_quota: 100%
  tasks_max: 256
  runtime_max_sec: 1800
  unit_prefix: oneops-task
```

`enabled=false` keeps the current direct executor for local compatibility. Production examples should enable sandboxing and disable legacy fallback.

## Systemd Execution Model

The runner uses a transient service with `systemd-run --wait --collect --pipe`. The generated command must include:

```text
systemd-run
  --unit=<unit-name>
  --wait
  --collect
  --pipe
  --property=MemoryMax=<memory_max>
  --property=CPUQuota=<cpu_quota>
  --property=TasksMax=<tasks_max>
  --property=RuntimeMaxSec=<runtime_max_sec>
  --property=KillMode=control-group
  --property=WorkingDirectory=<work_dir>
  --setenv=KEY=VALUE ...
  <command> <args...>
```

The implementation must sanitize unit names so task ids cannot inject flags or invalid unit characters.

## Stop Semantics

`AgentService` currently tracks `runningTaskCancels`. Add a matching task sandbox registry:

- `taskID -> sandboxName`
- `taskID -> cancelFunc`

`StopTask` behavior:

1. Look up the running task.
2. Cancel the Go context.
3. Call `TaskSandboxRunner.Stop(ctx, taskID)` to stop the registered service name.
4. Return `200 stopping` if either cancellation or sandbox stop was initiated.
5. Return `404 task not running` if the task is unknown.

For systemd, stop uses `systemctl stop <unit-name>`.

## Security Boundaries

This phase provides process and resource isolation through systemd cgroups. It is not a full container sandbox and does not provide a separate filesystem namespace beyond current service hardening.

The design still depends on:

- running the agent as a dedicated low-privilege user;
- keeping `NoNewPrivileges`, `ProtectSystem`, `ProtectHome`, and `ReadWritePaths` in the agent service;
- restricting Controller-side authorization for `RunTask` and file RPCs.

Follow-up hardening can add path whitelisting for file RPC and optional container or namespace backends.

## Error Handling

Failure cases must produce clear messages:

- `TASK_SANDBOX_UNAVAILABLE`: sandbox is enabled but `systemd-run` is missing or systemd is not available.
- `TASK_SANDBOX_START_FAILED`: systemd accepted neither unit nor command.
- `TASK_SANDBOX_LIMIT_HIT`: systemd reports timeout or resource-limit termination.
- `TASK_CANCELLED`: caller stopped the task or parent context was cancelled.
- `TASK_COMMAND_FAILED`: command exited non-zero.

Existing task output and lifecycle log reporting must continue to work.

## Testing

Unit tests:

- config defaults and YAML parsing for `task_sandbox`;
- systemd unit-name sanitization;
- systemd-run argument construction for limits, cwd, env, command, and args;
- shell, Ansible, and Terraform command paths delegate to `TaskSandboxRunner`;
- `StopTask` cancels context and calls sandbox stop;
- unavailable systemd returns `TASK_SANDBOX_UNAVAILABLE` without falling back unless explicitly enabled.

Integration smoke, gated by an env var:

- run a short command through real `systemd-run`;
- run a command that exceeds `RuntimeMaxSec`;
- stop a long-running command and verify the service is gone.

## Rollout Plan

1. Add the abstraction and tests while preserving the direct executor as an explicit backend.
2. Add the systemd runner and keep it disabled by default in local configs.
3. Enable systemd sandboxing in production deployment templates.
4. Add a smoke script for real hosts with systemd.
5. After verification, consider making sandboxing the default for generated agent configs.

## Out Of Scope

- Container, chroot, seccomp, or namespace isolation.
- Telegraf plugin process isolation.
- Controller-side policy redesign.
- File RPC path whitelisting, except where needed to avoid regressions in task workspace handling.
