# Alert-To-Ticket Dagengine MVP Runbook

## Purpose

This MVP closes a minimal loop:

- alert engine creates an alert ticket
- orchestration triggers the default template `alert-ticket-default`
- template execution is compiled to a dagengine process
- execution status, context snapshot, and audit events are stored in OneOps

## Required Steps

1. Import the seed template with `POST /orchestration/templates`.
2. Confirm the template can be fetched with `GET /orchestration/templates/:code?environment=prod`.
3. Trigger an alert that creates a ticket.
4. Verify a corresponding orchestration execution exists with `GET /orchestration/executions/:executionId`.

## UI Verification

Use the hidden UI route `/#/platform/execution-observatory` in `OneOPS-UI` to validate the runtime with real data.

- `Executions` tab shows the live execution list from `GET /orchestration/executions` and the status cards from `GET /orchestration/executions/summary`.
- `Action Required` tab shows live action-required records from `GET /orchestration/executions/action-required`.
- Operators can directly `认领` and `Resolve` an action-required record from the observatory page, which calls the real claim/resolve APIs.
- Clicking an execution ID now opens the dedicated detail debugger route `/#/platform/execution-observatory/:executionId`.
- Opening a row drawer reads `GET /orchestration/executions/:executionId` and `GET /orchestration/executions/:executionId/events` so callback waits, approval waits, rejects, timeouts, and escalations can be inspected directly.
- Waiting executions now expose a lightweight action panel in the drawer that calls the real `/orchestration/resume/approve`, `/orchestration/resume/reject`, and `/orchestration/resume/callback` APIs.
- The execution detail debugger also reads `GET /orchestration/executions/:executionId/graph` to render the runtime graph, plus the real agent task and event timelines. It now shows `action_required_detail` as the live operator-follow-up state.

### Observatory Manual Launch

After the local stack is running, operators can start one real multi-agent closure execution directly from the page:

1. Open `http://127.0.0.1:3001/#/platform/execution-observatory`
2. Click `发起真实多Agent闭环`
3. Wait for the redirect into the execution detail debugger
4. Inspect runtime graph, agent tasks, and wait/resume actions on the returned execution

This page action uses the fixed MVP template `multi-agent-closure` in `prod` and is intended for real runtime verification rather than generic orchestration launch management.

### Real API Acceptance

If backend and UI are already running locally, you can create a real execution and then inspect it in the observatory page:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOPS-UI
ONEOPS_API_BASE_URL=http://127.0.0.1:8380/api/v1 \
ONEOPS_API_TOKEN=<your-token> \
npm run acceptance:execution-observatory-real-api
```

The script will:

- generate and import a temporary approval-escalation template bundle
- start a real orchestration execution with a unique `alert_code` and `ticket_code`
- wait for `waiting_approval`, then call the real `/orchestration/resume/reject` API
- verify the execution becomes `escalated` and creates an action-required record
- call the real claim and resolve APIs
- verify the execution appears in list and summary APIs and the action-required record reaches `resolved`
- print the observatory URL and write evidence files under `docs/openclaw-autodev/evidence/orchestration/execution-observatory-real-api`

### Execution Detail Debugger Acceptance

If backend and UI are already running locally, you can create a real execution and validate the dedicated execution detail debugger page:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOPS-UI
ONEOPS_API_BASE_URL=http://127.0.0.1:8380/api/v1 \
ONEOPS_API_TOKEN=<your-token> \
npm run acceptance:execution-detail-debugger-real-api
```

The script will:

- import or refresh the `multi-agent-closure` template from the local `multi_agent_ticket_closure` bundle
- start a real orchestration execution with a unique `alert_code` and `ticket_code`
- poll execution detail and events until settled
- call `GET /orchestration/executions/:executionId/graph`
- verify the graph includes nodes, edges, and a marked current or waiting node
- print the execution detail debugger URL and write evidence files under `docs/openclaw-autodev/evidence/orchestration/execution-detail-debugger-real-api`

### Live Wait Seed

If you want to open the page and manually click real `Approve / Reject / Resume Callback` actions, seed two waiting executions first:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOPS-UI
ONEOPS_API_BASE_URL=http://127.0.0.1:8380/api/v1 \
ONEOPS_API_TOKEN=<your-token> \
npm run seed:execution-observatory-live-actions
```

The seed script will:

- create one real `waiting_approval` execution
- create one real `waiting_callback` execution
- print a shared search keyword plus both execution IDs
- write evidence files under `docs/openclaw-autodev/evidence/orchestration/execution-observatory-live-actions`

### Multi-Agent Ticket Closure Acceptance

If `OneOps` and `agentruntime` are already running locally, you can execute the full multi-agent closure loop against the real APIs:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOPS-UI
ONEOPS_API_BASE_URL=http://127.0.0.1:8380/api/v1 \
ONEOPS_API_TOKEN=<your-token> \
npm run acceptance:multi-agent-ticket-closure-real-api
```

Recommended local verification flow:

1. Start both local processes through the helper script:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
./scripts/start_multi_agent_closure_stack.sh start
```

2. Run `npm run acceptance:multi-agent-ticket-closure-real-api`.
3. Open `/#/platform/execution-observatory` and inspect Agent Tasks plus the approval timeline for the returned execution ID.

If you want a single local entrypoint that both starts the stack and runs one real multi-agent closure execution, use:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
./scripts/start_multi_agent_closure_stack.sh acceptance
```

That command will:

- build and start `agentruntime` plus `OneOps`
- run the real UI acceptance script with the default local login `admin/admin@123`
- print the observatory URL, execution detail URL, execution ID, and evidence file paths

If you want to validate that wait-state executions survive process restart and can still be resumed correctly, use:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
./scripts/start_multi_agent_closure_stack.sh acceptance-restart
```

That command will:

- start or reuse the local `agentruntime` and `OneOps` stack
- create one real `waiting_approval` execution and one real `waiting_callback` execution
- restart both services through the same helper entrypoint
- verify both executions remain in their waiting state after restart
- call the real resume APIs and verify both executions reach `completed`
- write evidence files under `docs/openclaw-autodev/evidence/orchestration/restart-resume-real-api`

The helper script now derives runtime settings from the Nacos bootstrap file and only exports them to child processes:

- `ONEOPS_LISTEN_PORT`
- `AGENTRUNTIME_PORT`
- `ONEOPS_API_BASE_URL`

In the standard local path you should not need to hand-set those values. The helper reads them from `nacos_config.yaml` through `scripts/print_multi_agent_runtime_settings.go`, then uses the resolved values to start services and run acceptance scripts.

It also writes pid/log files under `/tmp/oneops-multi-agent-closure` by default and supports:

```bash
./scripts/start_multi_agent_closure_stack.sh status
./scripts/start_multi_agent_closure_stack.sh restart
./scripts/start_multi_agent_closure_stack.sh stop
```

When `systemd-run --user` is available, the helper now prefers transient user services for `agentruntime` and `OneOps`. That gives a more production-like detached lifecycle than plain shell backgrounding and makes `status` more reliable.

By default the script waits for `agentruntime :18080` and `OneOps :8380` to start listening before it returns. You can override the wait budget with `ONEOPS_MULTI_AGENT_READY_TIMEOUT_SEC`.

Notes:

- `agentruntime` listens on `:18080` by default unless `ONEOPS_AGENT_RUNTIME_LISTEN_ADDR` overrides it.
- In the current local setup, OneOps API is expected on `http://127.0.0.1:8380` and the UI dev server on `http://127.0.0.1:3001`.
- The local helper builds `agentruntime` from `OneOps/cmd` and `OneOps` from the repo root into `/tmp/oneops-multi-agent-closure/bin`, then launches those built binaries.
- That launch directory choice is what keeps the default local helper on file bootstrap: `OneOps/cmd` does not contain `nacos_config.yaml`, so the helper-exported `ONEOPS_AGENT_RUNTIME_CONFIG_FILE` continues to drive local startup and defaults to `local_config_test.yaml` in the repo root.
- If `systemd-run --user` is available, logs still land in `/tmp/oneops-multi-agent-closure/*.log`, while process lifecycle is owned by transient user units:

```bash
systemctl --user status oneops-multi-agent-agentruntime
systemctl --user status oneops-multi-agent-oneops
```

- If you need to inspect the transient service manager view directly, use:

```bash
journalctl --user -u oneops-multi-agent-agentruntime -n 50 --no-pager
journalctl --user -u oneops-multi-agent-oneops -n 50 --no-pager
```

- If an operator wants the production-style Nacos bootstrap path, do not use this local helper launch path. Start `agentruntime` from a directory where `nacos_config.yaml` is intentionally present, following the production bootstrap convention instead.
- Once `nacos_config.yaml` is detected by `agentruntime`, bootstrap failures are fail-fast and do not fall back to `local_config_test.yaml`.
- Callback auth and submit routing are expected to come from the same Nacos-backed runtime config path rather than ad hoc shell exports.
- The acceptance script falls back to `/api/v1/access/login` only when `ONEOPS_API_TOKEN` is not provided. If local login is unhealthy, pass `ONEOPS_API_TOKEN` explicitly. In the current local config, `ONEOPS_API_TOKEN=abc123` is the most reliable choice.

The acceptance script will:

- import or refresh the `multi-agent-closure` template from the local `multi_agent_ticket_closure` bundle
- start a real execution with unique `alert_code` and `ticket_code`
- wait until the flow reaches `waiting_approval`
- approve the execution through the real `/orchestration/resume/approve` API
- wait until tracking and knowledge agent steps finish and execution reaches `completed`
- verify `analyze_alert`, `recommend_dispatch`, `track_execution`, and `draft_knowledge` agent tasks all exist
- write evidence files under `docs/openclaw-autodev/evidence/orchestration/multi-agent-ticket-closure-real-api`

## Expected Stored Records

- `orchestration_template_definitions`
- `orchestration_template_executions`
- `orchestration_execution_contexts`
- `orchestration_execution_logs`
- `orchestration_execution_events`
- `orchestration_suspend_records` when a wait node is reached

## MVP Notes

- The execution adapter is intentionally lightweight and runs the compiled DAG locally in topological order.
- `alert_engine` currently triggers the default environment `prod` unless later wiring adds environment derivation.
- The external call runtime is platform-managed and uses pre-registered external targets rather than inline endpoint definitions in template execution.
- Flow and agent runtimes persist concise node logs plus standardized execution and node events.
- Callback wait nodes now stop execution with status `waiting_callback`; approval wait nodes stop execution with status `waiting_approval`.
- Waiting executions store `waiting_node_id`, `wait_type`, and `resume_token` on the execution row for follow-up handling.
- Waiting executions also create an active suspend record so `/orchestration/resume/*` APIs can resolve the callback or approval without in-memory state.
- In the current MVP, callback resume and approval `approve` continue execution using the wait node's `next` target.
- Approval `reject` now routes through the wait node's `on_failure` target. If that target is terminal, execution closes there; if it is another step, execution continues from that step.
- Wait timeout handling now routes through the wait node's `on_timeout` target with the same terminal-or-step behavior.
- If a wait-node terminal target resolves to `escalated`, runtime also emits a structured `execution_action_required` event and stores `terminal_outcome` in execution context for downstream operations handling.
- Operators and downstream services can now read runtime events from `GET /orchestration/executions/:executionId/events` and query action-required records from `GET /orchestration/executions/action-required`.
- Action-required records are now the live operator state layer. The timeline event remains audit data; claim and resolve lifecycle live on the persisted record.
- Alert ticket consumers can read action-required items already narrowed to a ticket via `GET /alert/ticket/:code/orchestration-actions`.
- If resume unblocks the wait record but the continuation path cannot be started, the execution is also closed as `failed` instead of staying in `waiting_*`.
- The gateway records node progress into execution context; it does not yet call external remediation systems.
