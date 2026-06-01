---
topic: device-v2-onboarding-observability
kind: full-stack
title: Device V2 纳管观测闭环
status: draft
---

# Research

## Browser Evidence

- Page: `http://127.0.0.1:3001/#/device/device-v2-management-redesign`
- Login worked with provided admin account after database restart.
- Network calls observed:
  - `GET /api/v1/device/v2/list?page=1&page_size=20`
  - `GET /api/v1/device/v2/ingest/tasks?limit=5`
  - `GET /api/v1/device/v2/DVC8B7374049C21/last-store-collection-dc2`
  - `GET /api/v1/device-collection2/runs/{run_id}/devices`
  - `GET /api/v1/device-collection2/facts?...`

Sample `last-store-collection-dc2` response:

```json
{
  "found": true,
  "device_code": "DVC8B7374049C21",
  "target_id": "DVC8B7374049C21",
  "contract_key": "server_linux",
  "task_id": "entv2_1778840314183543000",
  "store_run_id": "dvsr_5875cfa67fad8f9c12f539e1605d380bad330249",
  "dc2_run_id": "dc2s_5875cfa67fad8f9c12f539e1605d380bad330249"
}
```

## Current Real Code Facts

- Device V2 management page already has store start and DC2 evidence navigation.
- Store runtime persists per-device run summaries and marks `NextManageIDs`, but it stops at ready-for-manage instead of executing the rest of onboarding.
- Device V2 SyncToV1 already creates/backfills Device V1 and then calls monitor probe notification.
- Monitoring platform has task apply, reconcile, operation, metric observation, and topology APIs.
- Telegraf plugin mapping includes log collection, SNMP trap, and Loki output primitives.

## Added Scenario Research: Independent Syslog/SNMP Trap Management

### Current Real Code Facts

- Frontend already has a dedicated platform page [OneOPS-UI/src/views/platform/LogForwardPlanManagement.vue](/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/views/platform/LogForwardPlanManagement.vue) for `local_file` and `remote_syslog` plans.
- `remote_syslog` already requires `collector_agent_code`, supports source selection, syslog standard options, and apply/preflight/dry-run operations.
- Backend `PrepareRemote` in [OneOPS/app/platform/api/log_forward_prepare_adapter.go](/Users/huangliang/project/OneOPS-ALL/OneOPS/app/platform/api/log_forward_prepare_adapter.go) validates the selected collector agent, checks `teleabs_template:syslog` capability, resolves source targets, and builds collector-side syslog listener context.
- Backend `BuildRemote` in [OneOPS/app/platform/api/log_forward_compile_request_builder.go](/Users/huangliang/project/OneOPS-ALL/OneOPS/app/platform/api/log_forward_compile_request_builder.go) compiles only the collector target and emits the syslog listener template with `address/protocol/additional_config`.
- Existing platform strategy/task forms already expose `snmp_trap` as a first-class task type, and controller plugin mapping already maps it to `inputs.snmp_trap`.

### Gap Against The New Requirement

- Current `remote_syslog` page is still modeled as a "日志转发计划" page, not a dedicated "区域基础服务 / syslog / snmp trap 管理" page.
- Current page semantics are centered on log forwarding plans, not on daily management of area-level listener services.
- Current code does not expose an explicit distinction between `服务器 syslog 监听` and `网络设备 syslog 监听` as separate management concepts, even though the new requirement needs that distinction at the page level.
- Current onboarding PRD mentions FunctionArea-level `syslog` / `snmp_trap` services, but there is no standalone management entry that lets an operator choose an agent and independently publish these listener configurations outside the onboarding flow.

### AI Derived Suggestion

- Reuse the existing apply/preflight/dry-run chain from `app/platform` log forwarding instead of inventing a new delivery path.
- Introduce a dedicated management page whose domain language is `区域日志接入服务` rather than `日志转发计划`.
- Treat listener management as a separate product surface from Device V2 onboarding: onboarding can call it, but operators must also be able to manage it directly.
- Model at least three independent service profiles in the page and PRD:
  - `server_syslog_listener`
  - `network_syslog_listener`
  - `snmp_trap_listener`
- Keep the downstream delivery chain reusable, but let the page make the server/network distinction explicit in form fields, defaults, and validation.

## Planning Gaps

- No single onboarding state model connects store success, V1 bridge, monitor task delivery, log/trap setup, and Prom/Loki verification.
- No evidence object currently says “Prometheus metric seen” or “Loki log/trap seen” for a Device V2 store run.
- Frontend “日志” action is not tied to the onboarding plan.
- Network device remote syslog/trap configuration requires a safety model before execution.

## AI Derived Suggestion

Use Device V2 store task/run as the root correlation id. Every later stage should write evidence under the same `task_id` and `run_id`, with child stage ids for monitor and log onboarding. This gives the frontend one place to render status and lets OpenClaw/CT verify the whole path without chasing unrelated logs.
