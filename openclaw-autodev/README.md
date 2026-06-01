# OpenClaw Agent Loop

This is the single sustained-development mechanism for PF3, D2 frontend, D2
backend, and continuous testing.

Do not use OpenClaw cron for continuous development. Cron is only for unrelated
periodic jobs such as reminders or scheduled reports.

## Only Entry Point

```bash
/Users/huangliang/project/OneOPS-ALL/scripts/openclaw-agent-loop.sh <command> <task-or-group>
```

## Directory Layout

All automation-owned files live under:

```text
docs/openclaw-autodev/
```

```text
README.md                  agent-loop operating guide
wechat-routing.md          OpenClaw Weixin prefix routing
runtime-template.md        runtime guardrail template
project-template.conf.example task-pool project file template
shared-d2.md               D2 FE/BE shared coordination
loops/*.conf               task configs
stories/*.json             Ralph-style small story queues
memory/autodev-memory.sqlite lightweight local memory index
state/                     loop state, locks, maintenance archives
logs/                      automation logs
evidence/                  automation-level evidence
issues/                    automation-created issue notes
```

Commands:

```text
start   run one bounded agent-loop block now
daemon  run repeated blocks in the background, default 24 hours
pool    run the dynamic task-pool supervisor
resident install a launchd resident that keeps the task pool alive with OpenClaw
enable  enable scheduling for one task or group
disable disable scheduling and stop one task or group
status  show loop state and last report
stop    request stop for a task or group
cleanup clean stale loop state, sessions, tasks, and known retired agents
list    list configured loop tasks
```

Independent repair agents are intentionally outside the sustained-development
loop. Use them when a business loop is BLOCKED by tool/runtime/contract/test-data
problems and you want a separate temporary agent to diagnose or patch the
blocker without continuing the original story:

```bash
/Users/huangliang/project/OneOPS-ALL/scripts/openclaw-repair-agent.sh start d2-fe
/Users/huangliang/project/OneOPS-ALL/scripts/openclaw-repair-agent.sh status
/Users/huangliang/project/OneOPS-ALL/scripts/openclaw-repair-agent.sh detail
/Users/huangliang/project/OneOPS-ALL/scripts/openclaw-repair-agent.sh close
```

Weixin equivalents use the `REPAIR` prefix, for example
`REPAIR 启动 D2FE`, `REPAIR 状态`, `REPAIR 现场`, and `REPAIR 关闭`.
The start note is optional; without it the repair agent captures the current
BLOCKED scene and generates a default repair brief. Repair state and evidence are kept under
`docs/openclaw-autodev/state/repair/<repair-id>/`.

Tasks:

```text
platform3
d2-fe
d2-be
ct
```

Groups:

```text
d2   d2-fe + d2-be, shared via docs/openclaw-autodev/shared-d2.md
all  every docs/openclaw-autodev/loops/*.conf task
pool dynamic task-pool supervisor
```

## Task Pool

The task pool is file-driven. Every sustained-development project is one file:

```text
docs/openclaw-autodev/loops/<task-id>.conf
```

The filename and `TASK_ID` must match. To add a project, copy
`docs/openclaw-autodev/project-template.conf.example` to
`docs/openclaw-autodev/loops/<task-id>.conf`, fill in workspace, docs, allowed
writes, and validation command. New project files default to disabled:

```bash
ENABLED="0"
```

The task exists in the pool but is not scheduled until it is enabled:

```bash
/Users/huangliang/project/OneOPS-ALL/scripts/openclaw-agent-loop.sh enable <task-id>
```

Then start or rely on the resident pool:

```bash
/Users/huangliang/project/OneOPS-ALL/scripts/openclaw-agent-loop.sh pool start
```

The pool supervisor scans `loops/*.conf` every `POOL_SCAN_SECONDS` seconds
(default `30`). It only schedules enabled project files. If a project is
disabled, the pool stops its daemon and skips scheduling. If a project file is
removed, the pool writes a stop request for that task, kills its daemon if it is
still running, marks its state as `Removed`, and deletes the worker agent when
no remaining task uses it.

Validation-only loops may set:

```bash
SHELL_TURN_COMMAND="scripts/continuous-validation.sh"
```

When present, the loop runs that command directly and writes a standard
`LoopControl` footer. This is intended for CT-style health checks that should
not depend on model availability or occupy the shared model slot.

Useful per-task overrides:

```bash
AGENT_MODEL="openai-codex/gpt-5.5"
AGENT_PROFILE="workbench-alt"
PROVIDER_PROBE_MODEL="openai-codex/gpt-5.5"
HARNESS_PROFILE="strict-worker"
HARNESS_CONTRACT_DOC="/Users/huangliang/project/OneOPS-ALL/docs/openclaw-autodev/strict-worker-profile.md"
PATCH_MAX_FILES="3"
CONTROLLER_VERIFY_ON_DONE="1"
CONTROLLER_VERIFY_COMMAND="<same as validation command or stricter>"
POST_BLOCK_COMMAND="node /Users/huangliang/project/OneOPS-ALL/scripts/prd-program-cycle.mjs <topic> <task-group>"
RUNTIME_ENV_FILE="/absolute/path/to/runtime.env"
RUNTIME_ENV_FILES=$'/absolute/path/one.env\n/absolute/path/two.env'
```

Notes:

- `AGENT_MODEL` controls which model is used when the loop creates or recreates
  its worker agent.
- `AGENT_PROFILE` is optional. When set, worker-agent creation and worker turns
  use `openclaw --profile <name>` so one loop can run on a different OpenClaw
  account/profile than the default router/runtime.
- `PROVIDER_PROBE_MODEL` may differ from the worker model when you want a
  cheaper or faster health probe.
- `HARNESS_PROFILE` injects extra execution constraints into the worker prompt.
  Use `strict-worker` for small-step, weak-worker, or cost-optimized execution
  where context, patch scope, and verifier discipline need to be stricter than
  the default prompt. `qwen-worker` remains as a compatibility alias for older
  loops and docs. When `strict-worker` is active, the controller also compiles
  the selected story
  into `docs/openclaw-autodev/state/<task-id>/current-execution-pack.json` and
  injects a compact execution-pack summary into the worker prompt.
- `HARNESS_CONTRACT_DOC` is optional. When present, a compact leading excerpt of
  that file is injected into the worker prompt after read budget and precheck
  output.
- `PATCH_MAX_FILES` limits how many files the harness should touch before it
  must stop and ask for a broader scope.
- `CONTROLLER_VERIFY_ON_DONE` makes the shell controller rerun verification
  after a worker reports `DONE`. This is recommended for local models.
- `CONTROLLER_VERIFY_COMMAND` defaults to `VALIDATION_COMMAND` and is the exact
  command the controller runs for post-turn verification.
- `POST_BLOCK_COMMAND` is optional. The controller runs it after a block
  finishes and after the latest state/handoff/report have been written. Use it
  for bounded orchestration follow-ups such as PRD cycle syncing.
- `RUNTIME_ENV_FILE` / `RUNTIME_ENV_FILES` are optional runtime-only secret
  sources. They are sourced immediately before precheck, worker turns, and shell
  turns. Missing files block the task early instead of failing later as an
  ambiguous remote-runtime error.
- When `AGENT_PROFILE` is set and `RUNTIME_ENV_FILE` is empty, the controller
  also auto-discovers `~/.openclaw-<AGENT_PROFILE>/runtime.env`.
- Model selection happens before runtime env files are sourced. Export
  `OPENCLAW_AGENT_MODEL` / `PROVIDER_PROBE_MODEL` in the invoking shell if you
  want to switch a loop onto a different cloud model without editing the loop
  config.

## Worker Lifecycle

The default policy is aggressive worker rotation:

```text
resident/pool -> daemon -> one short worker turn -> handoff -> next worker turn
```

Each configured loop defaults to `MAX_TURNS=1`, `MAX_MINUTES=25`, and
`TIMEOUT_SECONDS=1500`. A worker should finish one bounded unit of work, write a
compact final footer, and exit. The daemon then sleeps briefly and schedules the
next fresh OpenClaw session if the task remains enabled and control is
`CONTINUE`.

The controller writes a deterministic handoff file after every turn:

```text
docs/openclaw-autodev/state/<task-id>/handoff.md
```

## State Manager

The shell loop is intentionally becoming a thin execution wrapper. State
modeling, process inspection, lock cleanup, model-slot inspection, and monitor
reports are handled by:

```bash
/Users/huangliang/project/OneOPS-ALL/scripts/openclaw-state-manager.mjs
```

Useful commands:

```bash
scripts/openclaw-state-manager.mjs monitor all
scripts/openclaw-state-manager.mjs status d2
scripts/openclaw-state-manager.mjs detail d2-fe
scripts/openclaw-state-manager.mjs cleanup all
scripts/openclaw-state-manager.mjs model-slot
OPENCLAW_STATE_WATCH_INTERVAL_MS=5000 scripts/openclaw-state-manager.mjs watch all
```

The resident loop calls the state manager on every scan, so status is refreshed
frequently without asking a model. This improves visibility into daemon
processes, trace activity, locks, stale pids, and model-slot ownership while
reducing shell state logic.

The next worker receives this handoff in its prompt before project docs and must
treat it as the current source of truth. This prevents one long worker context
from accumulating too much history while still preserving ticket, tests, next
step, and blocker details.

The injected prompt is intentionally compact. The controller includes only the
first `HANDOFF_PROMPT_LINES` lines of handoff (default `24`) and the first
`APPROVAL_PROMPT_LINES` lines of approval (default `8`). Each run stores the
exact prompt sent to OpenClaw:

```text
docs/openclaw-autodev/state/<task-id>/<run-id>-turn-<n>.prompt.txt
docs/openclaw-autodev/state/<task-id>/current-prompt.txt
```

Inspect prompt size before a run:

```bash
/Users/huangliang/project/OneOPS-ALL/scripts/openclaw-agent-loop.sh prompt platform3
```

## Story Queue

The loop uses a Ralph-style story queue to keep each worker turn small and
fresh. Story files live under:

```text
docs/openclaw-autodev/stories/<task-or-group>.json
```

Each worker receives at most one current story. If no selectable story exists,
the worker must return `DONE` instead of searching broad docs for new work.
The controller updates the story from the worker's final footer through the
story orchestrator:

```text
LoopControl: CONTINUE -> story status in_progress
LoopControl: DONE     -> story status done
LoopControl: BLOCKED  -> story status blocked
LoopControl: APPROVAL -> story status approval
```

Story orchestration is guarded by:

```bash
/Users/huangliang/project/OneOPS-ALL/scripts/openclaw-story-orchestrator.mjs validate <task-or-group>
/Users/huangliang/project/OneOPS-ALL/scripts/openclaw-story-orchestrator.mjs plan <task-or-group>
/Users/huangliang/project/OneOPS-ALL/scripts/openclaw-story-orchestrator.mjs select <task-id>
```

The orchestrator treats `open`, `in_progress`, and `needs_next_turn` as
selectable. `blocked`, `approval`, `done`, `cancelled`, and `disabled` are not
auto-selected. Operator `approve` and `retry` release the current task lane back
to `open` before the pool schedules another bounded turn.

Multi-lane stories use `laneStatus` for per-task state. A story becomes `done`
only after every lane is done; any lane in `approval` or `blocked` holds the
aggregate story at that status. This keeps FE/BE handoffs explicit instead of
letting one lane silently close or reopen the whole story.

For shared groups such as D2, FE and BE can read the same story file while
selecting different `lanes`:

```json
{
  "id": "D2FE-DVR-007-BROWSER-EVIDENCE",
  "status": "open",
  "lanes": ["d2-fe"]
}
```

Inspect current stories:

```bash
/Users/huangliang/project/OneOPS-ALL/scripts/openclaw-agent-loop.sh stories platform3
/Users/huangliang/project/OneOPS-ALL/scripts/openclaw-agent-loop.sh stories d2
/Users/huangliang/project/OneOPS-ALL/scripts/openclaw-agent-loop.sh stories ct
```

Repeating stories, such as CT validation, can set `"repeat": true`; when the
worker returns `DONE`, the controller records completion and reopens the story.

The formal queue shape is documented in:

```text
docs/openclaw-autodev/story-schema.json
```

PRD program queues can be audited and linked with:

```bash
/Users/huangliang/project/OneOPS-ALL/scripts/prd-openclaw-sync.mjs d2-launch-acceptance d2
/Users/huangliang/project/OneOPS-ALL/scripts/prd-openclaw-sync.mjs d2-launch-acceptance d2 --publish-reviewed
```

The sync report is written to the PRD evidence folder, for example
`docs/prd-autodev/d2-launch-acceptance/evidence/automation-sync.md`. Reviewed
packages count toward PRD automation closure; draft packages are reported but
not published.

For multi-round program control, pair the sync with:

```bash
/Users/huangliang/project/OneOPS-ALL/scripts/prd-program-cycle.mjs <topic> <task-group> --publish-reviewed
```

That controller does not replace lane execution. It watches the reviewed batch
state, writes a planning brief after the current reviewed batch finishes, and
can trigger a planner lane or planner command exactly once for that completed
batch. The planner is responsible for deciding whether to draft the next batch,
promote a reviewed batch, close the PRD with final readiness, or stop the
program. It should not spin environment repair into repeated PRD micro-batches;
the only narrow exception is a final-stage tiny validation task that is clearly
the fastest way to decide `close` / `continue` / `stop`.

For longer memory, the controller maintains a lightweight local index:

```bash
/Users/huangliang/project/OneOPS-ALL/scripts/openclaw-autodev-memory.sh index all
/Users/huangliang/project/OneOPS-ALL/scripts/openclaw-autodev-memory.sh search platform3 "P3-064 validation"
/Users/huangliang/project/OneOPS-ALL/scripts/openclaw-autodev-memory.sh status
```

The index currently uses SQLite FTS5 over handoffs, last reports, work details,
and evidence files. It is deterministic, local, and cheap enough to refresh
after every turn. If true embedding retrieval is needed later, vector columns or
a small sqlite-vec/lancedb sidecar can be added under the same `memory/`
directory without changing the loop command model.

Task-pool commands:

```bash
/Users/huangliang/project/OneOPS-ALL/scripts/openclaw-agent-loop.sh pool start
/Users/huangliang/project/OneOPS-ALL/scripts/openclaw-agent-loop.sh pool status
/Users/huangliang/project/OneOPS-ALL/scripts/openclaw-agent-loop.sh pool sync
/Users/huangliang/project/OneOPS-ALL/scripts/openclaw-agent-loop.sh pool stop
/Users/huangliang/project/OneOPS-ALL/scripts/openclaw-agent-loop.sh enable <task-id>
/Users/huangliang/project/OneOPS-ALL/scripts/openclaw-agent-loop.sh disable <task-id>
```

`daemon pool`, `status pool`, and `stop pool` are aliases for the same pool
supervisor operations.

## Resident Pool

Install the OpenClaw resident task once:

```bash
/Users/huangliang/project/OneOPS-ALL/scripts/openclaw-agent-loop.sh resident install
```

This installs a long-running launchd task named `ai.openclaw.autodev.pool`.
It is not cron. It waits for `openclaw gateway health` to become available,
then continuously syncs the task pool. As long as OpenClaw is running and the
resident task has not been explicitly stopped or uninstalled, it keeps watching
`docs/openclaw-autodev/loops/*.conf`.

Resident commands:

```bash
/Users/huangliang/project/OneOPS-ALL/scripts/openclaw-agent-loop.sh resident install
/Users/huangliang/project/OneOPS-ALL/scripts/openclaw-agent-loop.sh resident status
/Users/huangliang/project/OneOPS-ALL/scripts/openclaw-agent-loop.sh resident stop
/Users/huangliang/project/OneOPS-ALL/scripts/openclaw-agent-loop.sh resident start
/Users/huangliang/project/OneOPS-ALL/scripts/openclaw-agent-loop.sh resident uninstall
```

Lifecycle:

```text
OpenClaw gateway stopped  -> resident waits
OpenClaw gateway starts   -> resident syncs task pool
loops/<task>.conf added   -> resident starts that loop
loops/<task>.conf removed -> resident stops that loop and deletes unused worker agent
resident stop/uninstall   -> resident and task pool stop
```

The resident plist source lives under `docs/openclaw-autodev/state/resident/`.
A LaunchAgent symlink is installed at
`~/Library/LaunchAgents/ai.openclaw.autodev.pool.plist` so macOS can keep it
alive.

## Examples

Run one block:

```bash
/Users/huangliang/project/OneOPS-ALL/scripts/openclaw-agent-loop.sh start platform3
/Users/huangliang/project/OneOPS-ALL/scripts/openclaw-agent-loop.sh start d2
/Users/huangliang/project/OneOPS-ALL/scripts/openclaw-agent-loop.sh start ct
```

Run 24-hour continuous development:

```bash
DURATION_HOURS=24 /Users/huangliang/project/OneOPS-ALL/scripts/openclaw-agent-loop.sh pool start
DURATION_HOURS=24 /Users/huangliang/project/OneOPS-ALL/scripts/openclaw-agent-loop.sh daemon platform3
DURATION_HOURS=24 /Users/huangliang/project/OneOPS-ALL/scripts/openclaw-agent-loop.sh daemon d2
DURATION_HOURS=24 CONTINUE_AFTER_DONE=1 /Users/huangliang/project/OneOPS-ALL/scripts/openclaw-agent-loop.sh daemon ct
```

`start` and `daemon` automatically run cleanup first, then recreate the loop
agents required by the requested task or group. Target-scoped cleanup is narrow:
it cleans local task state and duplicate daemons, but skips global OpenClaw
session purge and loop-agent deletion. Cleanup keeps the Weixin router on
`main` bound to `openclaw-weixin`. To run global cleanup manually:

```bash
/Users/huangliang/project/OneOPS-ALL/scripts/openclaw-agent-loop.sh cleanup all
```

Global cleanup preserves only `main` by default. It deletes configured loop
agents such as `platform3`, `d2-fe`, and `d2-be`, clears stale
sessions/tasks/state, ensures `openclaw-weixin` still routes to `main`, and
archives maintenance output under `docs/openclaw-autodev/state/maintenance`.
Use this only before a fresh 24-hour run or an explicit supervisor reset.

To clean one task without global OpenClaw session purge or loop-agent deletion:

```bash
/Users/huangliang/project/OneOPS-ALL/scripts/openclaw-agent-loop.sh cleanup d2-fe
```

To force global behavior for a target, opt in explicitly:

```bash
FULL_OPENCLAW_CLEANUP=1 /Users/huangliang/project/OneOPS-ALL/scripts/openclaw-agent-loop.sh cleanup d2-fe
```

If you only want to clear sessions/tasks while keeping loop agents visible in
OpenClaw:

```bash
KEEP_LOOP_AGENTS=1 /Users/huangliang/project/OneOPS-ALL/scripts/openclaw-agent-loop.sh cleanup all
```

Known retired agents can be overridden with:

```bash
RETIRED_AGENT_IDS="old-agent-a old-agent-b" /Users/huangliang/project/OneOPS-ALL/scripts/openclaw-agent-loop.sh cleanup all
```

Observe and stop:

```bash
/Users/huangliang/project/OneOPS-ALL/scripts/openclaw-agent-loop.sh status all
/Users/huangliang/project/OneOPS-ALL/scripts/openclaw-agent-loop.sh stop all
```

Tune a block:

```bash
MAX_TURNS=1 MAX_MINUTES=25 /Users/huangliang/project/OneOPS-ALL/scripts/openclaw-agent-loop.sh start platform3
```

## WeChat Routing

OpenClaw's `openclaw-weixin` channel routes to `main`, which acts as the
Weixin router. Natural language chat is allowed, but agent-loop commands must
start with a routing prefix on the first line. Business loop agents such as
`platform3`, `d2-fe`, and `d2-be` are created by the script when a loop starts;
they do not receive Weixin messages directly.

The Weixin inbound path is deterministic first:

```text
openclaw-weixin inbound
  -> scripts/openclaw-weixin-router.sh
      -> fixed command matched: run the mapped local control script and reply
      -> no fixed command: exit 2 and fall back to main agent/model
```

The router script is intentionally small and conservative. It only executes
known control commands. It recognizes the fixed prefixes plus dynamic current
OpenClaw tasks from `docs/openclaw-autodev/loops/*.conf` and
`docs/openclaw-autodev/stories/*.json`. Ordinary natural-language messages, or
anything without a fixed prefix, dynamic task-id prefix, or `TASK <task-id>` on
the first line, fall through to the model. This keeps control commands fast and
predictable while preserving normal chat for ambiguous requests.

Long-running fixed commands such as `PF3 修复`, `POOL 启动`, and `LOOP 启动`
are submitted in the background and return a log path immediately. Read-only
queries such as `PF3 状态` and `PF3 现场` run synchronously and keep the Weixin
reply capped, with full details left under `docs/openclaw-autodev/state/` or
`docs/openclaw-autodev/logs/`.

Map prefixed Weixin commands directly to the single entry point:

```text
TASK <任务> 状态 -> scripts/openclaw-agent-loop.sh status <任务>
TASK <任务> 进度 -> scripts/openclaw-task-progress.mjs <任务>
TASK <任务> 现场 -> scripts/openclaw-agent-loop.sh detail <任务>
<task-id> 状态   -> scripts/openclaw-agent-loop.sh status <task-id>

PF3 启动      -> scripts/openclaw-agent-loop.sh enable platform3
PF3 停止      -> scripts/openclaw-agent-loop.sh disable platform3
PF3 状态      -> scripts/openclaw-agent-loop.sh status platform3
PF3 可信状态  -> scripts/openclaw-agent-loop.sh truth-status platform3
PF3 现场      -> scripts/openclaw-agent-loop.sh detail platform3
PF3 阻塞分类  -> scripts/openclaw-agent-loop.sh blocker platform3
PF3 状态收敛  -> scripts/openclaw-agent-loop.sh reconcile platform3
PF3 Daemon报告 -> scripts/openclaw-agent-loop.sh daemon-report platform3
PF3 诊断      -> scripts/openclaw-agent-loop.sh provider-check platform3
PF3 重试 <原因> -> scripts/openclaw-agent-loop.sh retry platform3 <原因>
PF3 同意 <范围> -> scripts/openclaw-agent-loop.sh approve platform3 <范围>
PF3 归档 [说明] -> scripts/openclaw-archive-task.sh platform3 [说明]

D2 启动       -> scripts/openclaw-agent-loop.sh enable d2
D2 停止       -> scripts/openclaw-agent-loop.sh disable d2
D2 状态       -> scripts/openclaw-agent-loop.sh status d2
D2 可信状态   -> scripts/openclaw-agent-loop.sh truth-status d2
D2 阻塞分类   -> scripts/openclaw-agent-loop.sh blocker d2
D2 状态收敛   -> scripts/openclaw-agent-loop.sh reconcile d2
D2 Daemon报告 -> scripts/openclaw-agent-loop.sh daemon-report d2
D2 同意 <范围> -> scripts/openclaw-agent-loop.sh approve d2 <范围>
D2 归档       -> 拒绝执行；D2 是 group target，请使用 D2FE 归档 或 D2BE 归档

D2FE 启动     -> scripts/openclaw-agent-loop.sh enable d2-fe
D2FE 停止     -> scripts/openclaw-agent-loop.sh disable d2-fe
D2FE 可信状态 -> scripts/openclaw-agent-loop.sh truth-status d2-fe
D2FE 阻塞分类 -> scripts/openclaw-agent-loop.sh blocker d2-fe
D2FE 状态收敛 -> scripts/openclaw-agent-loop.sh reconcile d2-fe
D2FE Daemon报告 -> scripts/openclaw-agent-loop.sh daemon-report d2-fe
D2FE 同意 <范围> -> scripts/openclaw-agent-loop.sh approve d2-fe <范围>
D2FE 归档 [说明] -> scripts/openclaw-archive-task.sh d2-fe [说明]
D2BE 启动     -> scripts/openclaw-agent-loop.sh enable d2-be
D2BE 停止     -> scripts/openclaw-agent-loop.sh disable d2-be
D2BE 可信状态 -> scripts/openclaw-agent-loop.sh truth-status d2-be
D2BE 阻塞分类 -> scripts/openclaw-agent-loop.sh blocker d2-be
D2BE 状态收敛 -> scripts/openclaw-agent-loop.sh reconcile d2-be
D2BE Daemon报告 -> scripts/openclaw-agent-loop.sh daemon-report d2-be
D2BE 同意 <范围> -> scripts/openclaw-agent-loop.sh approve d2-be <范围>
D2BE 归档 [说明] -> scripts/openclaw-archive-task.sh d2-be [说明]

CT 启动       -> scripts/openclaw-agent-loop.sh enable ct
CT 停止       -> scripts/openclaw-agent-loop.sh disable ct
CT 状态       -> scripts/openclaw-agent-loop.sh status ct
CT 可信状态   -> scripts/openclaw-agent-loop.sh truth-status ct
CT 阻塞分类   -> scripts/openclaw-agent-loop.sh blocker ct
CT 状态收敛   -> scripts/openclaw-agent-loop.sh reconcile ct
CT Daemon报告 -> scripts/openclaw-agent-loop.sh daemon-report ct
CT 重试 <原因> -> scripts/openclaw-agent-loop.sh retry ct <原因>
CT 同意 <范围> -> scripts/openclaw-agent-loop.sh approve ct <范围>
CT 归档 [说明] -> scripts/openclaw-archive-task.sh ct [说明]

POOL 启动     -> scripts/openclaw-agent-loop.sh pool start
POOL 状态     -> scripts/openclaw-agent-loop.sh pool status
POOL 同步     -> scripts/openclaw-agent-loop.sh pool sync
POOL 监控     -> scripts/openclaw-agent-loop.sh monitor status
POOL Daemon报告 -> scripts/openclaw-agent-loop.sh daemon-report all
POOL 阻塞策略 -> scripts/openclaw-agent-loop.sh blocker-policy
POOL 监控刷新 -> scripts/openclaw-agent-loop.sh monitor once
POOL 现场 PF3 -> scripts/openclaw-agent-loop.sh monitor detail platform3
POOL 停止     -> scripts/openclaw-agent-loop.sh pool stop
POOL 常驻安装 -> scripts/openclaw-agent-loop.sh resident install
POOL 常驻状态 -> scripts/openclaw-agent-loop.sh resident status
POOL 常驻停止 -> scripts/openclaw-agent-loop.sh resident stop
POOL 常驻卸载 -> scripts/openclaw-agent-loop.sh resident uninstall
POOL 归档 <任务> [说明] -> scripts/openclaw-archive-task.sh <任务> [说明]

LOOP 状态     -> scripts/openclaw-agent-loop.sh status all
LOOP 可信状态 -> scripts/openclaw-agent-loop.sh truth-status all
LOOP 阻塞分类 -> scripts/openclaw-agent-loop.sh blocker all
LOOP 状态收敛 -> scripts/openclaw-agent-loop.sh reconcile all
LOOP Daemon报告 -> scripts/openclaw-agent-loop.sh daemon-report all
LOOP 阻塞策略 -> scripts/openclaw-agent-loop.sh blocker-policy
LOOP 清理     -> scripts/openclaw-agent-loop.sh cleanup all
LOOP 归档 <任务> [说明] -> scripts/openclaw-archive-task.sh <任务> [说明]
```

Messages without `PF3`, `D2`, `D2FE`, `D2BE`, `CT`, `POOL`, or `LOOP` at the
start are ordinary conversation and must not trigger a loop.

`归档` 是可恢复的整理动作，不是删除。它会在存在 loop 配置时先禁用具体任务，
再把已有的 loop/story/evidence/state 产物移动到
`docs/openclaw-autodev/archive/<task>-<timestamp>/`，并生成 `MANIFEST.md`。
`D2` 这类 group target 会被拒绝，避免误归档共享 story 队列。

When a loop returns `LoopControl: APPROVAL` or `LoopControl: BLOCKED`, the
controller sends one proactive notification by reusing the latest direct `main`
Weixin session with `openclaw agent --deliver`. Do not use external
`openclaw message send --channel openclaw-weixin` for this; without the inbound
Weixin context token it may report a message id while not delivering. Approval
must be explicit and scoped, for example:

```text
PF3 同意 只允许 single target canary 的设计和只读验证，不允许 commit mode
```

The approval text is written into the task state and injected into the next
worker turn as `Operator approval context`. `启动` only enables scheduling; it
does not override an approval gate.

Reusable approval templates are available for common safe-release cases:

```bash
scripts/openclaw-agent-loop.sh approval-templates
scripts/openclaw-agent-loop.sh approval-template d2-be safe-difference "<现场依据>"
scripts/openclaw-agent-loop.sh approve d2-be --template safe-difference "<现场依据>"
scripts/openclaw-agent-loop.sh approve d2-be @safe-difference "<现场依据>"
```

Templates only generate scoped approval text. They do not bypass red lines:
data writes, deletes, production config, auth/tenant/credential behavior,
dependencies, commits, pushes, and external integrations still need explicit
human scope that names the exact allowed boundary.

Reusable approval profiles provide a shorter capability-based approval path for
Weixin and long-running automation. Profiles are defined in
`docs/openclaw-autodev/approval-profiles.json`; grants are recorded in
`docs/openclaw-autodev/state/approvals/<task>.json`.

```bash
scripts/openclaw-agent-loop.sh approval-profiles
scripts/openclaw-agent-loop.sh approval-profile d2on discovery-readonly
scripts/openclaw-agent-loop.sh approve d2on --profile discovery-readonly
scripts/openclaw-agent-loop.sh approvals d2on
scripts/openclaw-agent-loop.sh revoke-approval d2on discovery-readonly
```

Weixin equivalents:

```text
D2ON 授权列表
D2ON 授权 discovery-readonly
D2ON 授权 remote-readonly 192.168.100.7
D2ON 授权状态
D2ON 授权撤销 discovery-readonly
```

Profiles expand into explicit approval text and write the approval ledger. They
still do not carry secrets: credentials, tokens, cookies, SNMP communities,
private keys, and passwords must come from runtime-only local channels and must
not be persisted in code, docs, config, logs, or evidence.

BLOCKED/APPROVAL Weixin notifications may include a `NextApproval:` line when
the blocker is classified as a business authorization/manual-review boundary.
That line is a fully rendered approval reply beginning with the task prefix
and `同意`; copy it only after confirming the evidence matches your decision.
If the current ticket cannot be resolved exactly to a story in the queue, the
rendered reply must use explicit placeholders such as
`[story-title-not-found-in-queue]` instead of falling back to a stale current
story.

For technical blockers such as `status=timeout`, `stopReason=rpc`, or
`LoopControl footer missing`, use `PF3 重试 <原因>` instead of `PF3 同意 ...`.
`重试` clears the technical `BLOCKED` state, keeps the existing approval scope,
and asks the resident pool to schedule the next bounded turn.

Before retrying, use `PF3 阻塞分类` to identify the correct owner and route. If
the loop state, `last-control`, `current-story.json`, and story lane disagree,
run `PF3 状态收敛`; normal `状态` / `现场` / `阻塞分类` paths also perform this
reconciliation automatically. Business blockers are split into authorization
boundaries, which require explicit approval, and optimization blockers, where
the story itself may be adjusted before a focused business repair continues.

Use `D2 可信状态` or `LOOP 可信状态` when progress and business meaning may differ.
This separates `RuntimeState`, `QueueState`, and `BusinessState`, and marks
`Accuracy=Conflict` when a complete story queue still has a latest report that
asks to continue the business chain. `D2 进度` also displays this accuracy line.

Daemon supervision is also centralized. Each task may have only one
`run-daemon <task>` process. Cleanup adopts a single live daemon, kills
duplicates, and preserves repeat daemons such as CT even when the last block
reported `DONE`. This prevents resident from multiplying daemons after a repeat
health check completes. Use `LOOP Daemon报告` for the independent supervisor
report and `LOOP 阻塞策略` for the executable BLOCK ticket pattern table.

Repair agents now emit lifecycle events for `submitted`, `started`, `finished`,
`blocked`, `restart-prevented`, `stopped`, `stop-noop`, and `closed`. Their
captured context includes status, blocker classification, daemon report, detail,
handoff, and stories.

The resident pool refreshes the monitor on every scan. The monitor writes a
stable summary to `docs/openclaw-autodev/state/monitor/report.txt` and structured
state to `docs/openclaw-autodev/state/monitor/state.json`. Use `POOL 监控` from
Weixin for the latest report, and `POOL 监控刷新` when you want an immediate
scan outside the normal resident interval.

For a compact work-in-progress explanation, use `PF3 现场` or `POOL 现场 PF3`.
The Weixin reply stays short: state, current session, approval scope, last tool
event, last report line, and a detail-file path. The full event trail is written
to `docs/openclaw-autodev/state/<task>/work-detail.txt`.

The controller writes machine-readable progress for each active turn:

```text
docs/openclaw-autodev/state/<task>/progress.json
```

This file is generated by `scripts/openclaw-agent-loop.sh`, not by the model.
It records the current session, raw file size, last trajectory event, event age,
last tool event, child-process liveness, token usage, and a deterministic
classification:

```text
Starting       trace not ready yet
Working        child process or tool/model progress observed
PromptStuck    prompt.submitted without later progress past PROMPT_STUCK_MINUTES
ToolStuck      tool.call without tool.result past TOOL_STUCK_MINUTES
SessionEnded   OpenClaw session ended; controller must find LoopControl footer
```

Future recovery policy must use this file and process checks as the control
source of truth. The model should only perform business development work and
return the required `LoopControl` footer.

## Context Size Discipline

Keep control and development context separate:

```text
main Weixin context
  deterministic commands are handled by scripts/openclaw-weixin-router.sh
  only ambiguous natural language falls back to the main model

worker agent context
  each bounded turn uses a fresh OpenClaw session
  handoff happens through docs/openclaw-autodev/state, evidence, and source files
```

The worker prompt explicitly forbids broad log/tree reads and asks the agent to
use bounded commands (`rg`, `git diff --stat`, targeted `sed -n`) instead of
loading large files. `progress.json` records active `contextTokens`,
`contextWindowTokens`, `promptTokens`, `totalTokens`, and `contextWarning`.
`contextWindowTokens` is the model/harness window capacity, not a per-turn usage
number. The default active-context warning threshold is:

```bash
CONTEXT_WARN_TOKENS=80000
```

If `PF3 现场` shows a context warning, the controller should rotate to a fresh
turn/session and rely on compact state/evidence rather than continuing a large
conversation history.

Monitor health is evidence based:

```text
Working            real OpenClaw child process is active, for example openclaw/openclaw-agent
WorkingNoOutput    OpenClaw child exists, but the current turn output is still empty too long
AdoptedWorking     daemon is waiting on an already-active OpenClaw session after restart
Starting           block just started; waiting briefly for child process or report evidence
DaemonIdle         daemon is alive, but no block is currently running
WaitingForSchedule enabled task has no daemon yet; resident should schedule it
StaleLock          a lock exists but its owner is gone; resident cleanup can remove it
NoRecentActivity   lock exists, but no agent child or fresh report was observed
Blocked            loop returned or recorded a hard blocker
ApprovalRequired   loop is waiting for an explicit operator decision
Disabled           task scheduling is disabled
```

`DaemonRunning` alone is not treated as proof of work. For real work, look for
`Working` plus `activity=agent-child` and `children=...openclaw...openclaw-agent`
in the monitor report. If it says `WorkingNoOutput`, the process exists but the
current turn file is still empty, for example `rawSize=0b`; treat that as a
monitor warning rather than a healthy development turn.

When a daemon restarts while OpenClaw is still processing a prior turn, the loop
adopts that existing session instead of starting another one. In that case
`rawSize=0b` may refer to an abandoned CLI stdout file; use
`AdoptedWorking`, `activity=adopted-session`, `adopted=<session>`, `traceAge`,
and `traceEvent` as the real progress signal. A healthy adopted run has a fresh
`traceAge` and a moving `traceEvent` such as `tool.result`; any `localRaw=...`
field is only the abandoned local CLI stdout file.

## D2 Shared Loop

`D2` is a group loop for one product task with two independent agents:

```text
D2 group loop
  d2-fe agent -> OneOPS-UI frontend
  d2-be agent -> OneOPS backend
```

They share information through:

```text
docs/openclaw-autodev/shared-d2.md
OneOPS-UI/docs/device-v2-ui-autodev/COORDINATION.md
```

This keeps FE/BE coordination explicit while preserving write isolation.

## Task Configs

Each loop is configured by one file under:

```text
docs/openclaw-autodev/loops/<task>.conf
```

The config declares the OpenClaw agent, workspace, runtime docs, allowed writes,
validation command, and task-specific rules. Adding a new sustained-development
stream only means adding a config file under `loops/`; `all` and `pool` discover
it automatically.

## Loop Contract

Every direct agent turn must end with:

```text
LoopControl: CONTINUE|DONE|BLOCKED|APPROVAL
Task:
Status:
Ticket:
Changed:
Tests:
Next:
```

The script, not the model and not cron, decides whether to continue, stop, ask
for approval, or report a blocker.

## Reference Files

Read these when you need compact contract references instead of broad prose:

- `docs/openclaw-autodev/references/task-config.md`: loop config fields and
  adaptation intent by field.
- `docs/openclaw-autodev/references/runtime-rules.md`: compact runtime guardrail
  summary.
- `docs/openclaw-autodev/worker-adaptation-principles.md`: macro adaptation
  model for weak workers across task types.
- `docs/openclaw-autodev/worker-profile-mapping.md`: which current loops map
  cleanly to one worker profile and which should be split.
- `docs/openclaw-autodev/worker-capability-schema.json`: worker capability
  profile structure.
- `docs/openclaw-autodev/story-execution-pack-schema.json`: compiled execution
  pack structure for one story/worker handoff.
- `docs/openclaw-autodev/handoff-schema.json`: structured cross-turn handoff
  contract.
- `docs/openclaw-autodev/evidence-schema.json`: structured evidence claim
  contract.
- `docs/openclaw-autodev/profiles/*.json`: reusable worker profile instances.
- `docs/openclaw-autodev/execution-packs/examples/*.json`: example compiled
  execution packs for current loop styles.

## Execution Pack Compiler

Use the compiler when you want the controller-facing version of "loop + story +
profile match" instead of checking the docs by hand:

```bash
node scripts/openclaw-execution-pack.mjs build ct --story CT-CONTINUOUS-VALIDATION
node scripts/openclaw-execution-pack.mjs validate-profile dev-docs --story DEV-DOCS-002A
node scripts/openclaw-execution-pack.mjs validate-profile qwen-realcode-smoke --story QWEN-REALCODE-001
node scripts/openclaw-execution-pack.mjs validate-profile d2on --story D2ON-000
```

What this enforces:

- select one current story from `loops/*.conf` + `stories/*.json`;
- classify the story into one primary task kind;
- choose or validate the worker profile instance for that task kind;
- compile a concrete execution pack with truth source, actions, validation, and
  recovery policy;
- warn when an orchestration lane such as `d2on` is being narrowed to one
  temporary worker pack instead of being consumed as one broad weak worker.
