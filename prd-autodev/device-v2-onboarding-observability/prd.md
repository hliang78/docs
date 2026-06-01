---
topic: device-v2-onboarding-observability
kind: full-stack
title: Device V2 极简纳管设计
createdAt: 2026-05-15T20:57:53+0800
status: candidate
---

# PRD: Device V2 极简纳管设计

## Problem

Device V2 当前“采集验证”已经接近采集入库，但入库后进入监控纳管、日志纳管时仍缺少统一入口和稳定证据。最大风险不是状态不够多，而是远程访问不稳定、设备命令差异大、配置可能半成功。如果用复杂状态机控制，会把远程世界的不确定性带进平台状态。

## Product Direction

首期采用“手动继续纳管 + ensure action + evidence”的极简方案：

```text
单台设备继续纳管
  -> 生成 required actions
  -> 只执行未成功或需要执行的 ensure
  -> 每个 action 写结果证据
  -> 前端展示监控纳管 / 日志纳管两个结论
```

历史首期纳管成功以“配置成功”为准，不强制等待 Prometheus 或 Loki 收到数据。2026-05-18 scope 升级后，新的闭环必须继续向前验证平台侧数据面：监控指标要能在 Prometheus 查询出来；日志与 SNMP trap 要能在 Loki 查询出来。

## 2026-05-18 Scope Upgrade: Observed Data Closure

新范围把 `继续纳管` 从配置闭环升级为数据可观测闭环：

- 指标验证：对已纳管设备在 Prometheus 查询最近窗口内的核心指标。
- 服务器本地日志验证：对 agent/tail 采集的服务器本地日志在 Loki 查询最近窗口内的日志样本。
- 服务器 syslog 日志验证：对服务器 syslog listener 收到的日志在 Loki 查询最近窗口内的日志样本。
- 网络设备日志验证：对网络设备 syslog 日志在 Loki 查询最近窗口内的日志样本。
- 网络设备 SNMP trap 验证：对网络设备 SNMP trap 在 Loki 查询最近窗口内的 trap 日志样本。
- 成功证据必须记录查询端点、LogQL/PromQL 摘要、时间窗口、命中数量和样本摘要，不写入原始大段日志或凭证明文。

当前 live 查询端点：

- Prometheus: `http://192.168.0.164:9090`
- Loki: `http://192.168.0.164:3100`

初始只读探测：

- Prometheus `up` 查询已返回 `hit_count=1`。
- Prometheus metrics label values 包含 `ping_result_code` 与 `snmp_interface_ifOperStatus`。
- Loki `query_range` 可达；日志 instant query 不支持，验证必须使用 range query。
- 最近 30 分钟 `{__name=~"tail|syslog|snmp_trap"}` 暂未返回样本，因此后续实现需要区分 `pending/no_samples` 与查询端点不可达。

## Goals

- 在 Device V2 管理页提供单台设备 `继续纳管` 入口。
- 将纳管拆成监控纳管、日志纳管两个用户可理解的结果。
- 用 `device_v2_store_run.summary_json` 记录 `onboarding.actions`，避免新增复杂状态表。
- 把远程配置抽象成幂等 ensure：重复执行不会重复破坏配置。
- 支持网络设备 syslog 首期纳管，配置成功后自动保存。
- 支持服务器监控方式由用户选择 agent / SNMP。
- 支持服务器日志：有 agent 优先 agent，无 agent 生成 SSH 配置计划。
- 以配置文件承载 FunctionArea 区域基础服务定义和系统日志策略。
- 提供一个独立的区域 `syslog / snmp trap` 管理页面，用于选择 agent 并管理监听服务。
- 独立管理页中，`syslog` 必须明确区分 `服务器 syslog 监听` 与 `网络设备 syslog 监听` 两类表单语义。
- 独立管理页首期复用现有 `app/platform` 日志转发下发链路，不重造发布流程。
- scope 升级后，提供数据面验证 evidence：Prometheus 指标命中、Loki 服务器本地日志命中、Loki 服务器 syslog 命中、Loki 网络设备 syslog 命中、Loki 网络设备 SNMP trap 命中。

## Non-Goals

- 首期不做批量并发远程配置。
- 历史首期不要求 SNMP trap 全链路落地；scope 升级后，首个目标是 H3C/Comware 网络设备 trap target 到 Loki 可查。
- 首期不新增独立 onboarding DAG 或复杂状态流。
- 历史首期不以 Prometheus/Loki 数据到达作为纳管成功条件；scope 升级后的新成功条件要求 Prometheus/Loki 查询命中或记录精确 blocker。
- 首期不做完整审批流。
- 首期不为 `服务器 syslog 监听` 与 `网络设备 syslog 监听` 建两套不同后端配置模型。
- 历史首期不在独立管理页扩展到设备侧完整 SNMP trap target 远程下发；该设备侧 target 已在后续 batch-012 首个 H3C/Comware 范围内完成。

## Confirmed Decisions

- `继续纳管` 首期只对单台设备执行；批量只生成计划或逐台展示结果。
- 网络设备远程配置 syslog/trap target 后自动保存配置。
- 网络设备日志纳管首期优先 syslog。
- 服务器监控方式由用户选择 agent / SNMP。
- 服务器日志纳管有 agent 时优先 agent；无 agent 时生成 SSH 配置计划。
- Linux 系统日志默认文件为 `/var/log/syslog`、`/var/log/auth.log`、`/var/log/messages`、`/var/log/secure`。
- 系统日志策略模式为 `first_existing`。
- FunctionArea 区域基础服务首期先放配置文件。
- 再次点击 `继续纳管` 时，只重试 `failed` / `unknown` action。
- 新增独立管理页的主语义是“管理区域 agent 上的监听服务”，不是以设备侧 target 下发为主入口。
- `服务器 syslog 监听` 与 `网络设备 syslog 监听` 首期仅表单和默认值差异，不拆不同后端投递模型。
- 新页面可以包装复用现有 `remote_syslog` / `log_forward_plan` 模型与发布过程。
- `snmp trap` 本轮明确只做 listener 管理，不扩展到设备侧完整 trap target 远程下发。

## User Experience

### Device Row

设备行只需要两个纳管摘要：

- 监控纳管：成功 / 未完成 / 可重试 / 需要选择方式
- 日志纳管：成功 / 未完成 / 可重试 / 需要配置区域服务

### Continue Onboarding

单台设备动作：

```text
继续纳管
```

点击后：

- 若服务器监控方式未选择，先让用户选择 agent / SNMP。
- 若已有成功 action，不重复执行。
- 若存在 `failed` / `unknown` action，只重试这些 action。
- 执行结果写回当前 store run 的 `summary_json.onboarding`。

### Detail Drawer

详情不展示复杂状态机，只展示 action evidence：

- action title
- required
- result
- changed
- retryable
- message
- evidence

### Independent Listener Management Page

平台侧需要一个独立的区域监听服务管理页面，和 Device V2 单台 `继续纳管` 入口并列存在：

- 页面主语义：管理区域 agent 上的 `syslog / snmp trap` 监听服务。
- 用户先选择 FunctionArea 和目标 agent，再选择服务类型。
- 服务类型首期至少包含：
  - `服务器 syslog 监听`
  - `网络设备 syslog 监听`
  - `snmp trap 监听`
- `服务器 syslog 监听` 与 `网络设备 syslog 监听` 首期复用同一发布链路，但页面上的默认值、说明文案、Grok/标签建议、source 选择提示必须区分。
- 页面支持 `dry-run / preflight / apply / remove` 一类运维操作，不要求用户进入 Device V2 流程才能操作。

## Backend Contract

### Evidence Root

复用 `device_v2_store_run.summary_json`：

```json
{
  "onboarding": {
    "required": ["monitoring", "log"],
    "actions": [
      {
        "key": "monitoring.dispatch",
        "title": "下发监控任务",
        "category": "monitoring",
        "required": true,
        "result": "success",
        "changed": true,
        "retryable": false,
        "message": ""
      },
      {
        "key": "log.network.syslog_target",
        "title": "配置网络设备 syslog 目标",
        "category": "log",
        "required": true,
        "result": "failed",
        "changed": false,
        "retryable": true,
        "message": "ssh timeout"
      }
    ],
    "summary": {
      "monitoring": "success",
      "log": "failed",
      "overall": "partial"
    }
  }
}
```

### Result Values

每个 action 只使用少量结果值：

- `success`: 配置已确认成功。
- `failed`: 配置失败，可按 `retryable` 决定是否重试。
- `unknown`: 远程访问中断或结果无法判断，可重试或人工确认。
- `skipped`: 当前设备/选择不需要该动作。

整体摘要由 action result 推导，不手工维护复杂流转状态。

## Ensure Actions

### Monitoring

网络设备：

- `monitoring.dispatch`: 下发监控任务成功即监控纳管成功。

服务器：

- 用户选择 agent：确保 agent 存在或生成 agent 部署阻断，再下发监控任务。
- 用户选择 SNMP：远程登录服务器开启 SNMP，再下发 SNMP 监控任务。

### Log

网络设备：

- 首期优先 syslog。
- `log.area.syslog_listener`: 确认 FunctionArea 对应 agent 开启 syslog listener。
- `log.network.syslog_target`: 远程登录网络设备配置 syslog target 指向 agent IP，并自动保存配置。
- SNMP trap 首期仅记录一级定义和 teleabs 模板缺口。

服务器：

- 有 agent：下发系统日志转发任务。
- 无 agent：生成 SSH 配置计划，首期不默认自动执行。
- 系统日志策略使用 `first_existing`。

## Configuration Files

### Area Basic Services

首期用配置文件定义 FunctionArea 基础服务：

```json
{
  "function_areas": {
    "DefaultArea": {
      "syslog": {
        "enabled": true,
        "agent_code": "agent-a",
        "listen_ip": "10.0.0.10",
        "listen_port": 514,
        "protocol": "udp"
      },
      "snmp_trap": {
        "enabled": false,
        "agent_code": "",
        "listen_ip": "",
        "listen_port": 162,
        "protocol": "udp",
        "template_required": true
      }
    }
  }
}
```

独立管理页首期不要求改变上述基础服务 schema 的抽象方向，但允许在页面层引入更清晰的 service type 语义来包装当前模型。

### System Log Strategy

```json
{
  "strategies": [
    {
      "strategy_id": "linux_system_default",
      "os_family": "linux",
      "mode": "first_existing",
      "files": [
        "/var/log/syslog",
        "/var/log/auth.log",
        "/var/log/messages",
        "/var/log/secure"
      ]
    }
  ]
}
```

## API Design

Recommended minimal APIs:

```text
POST /api/v1/device/v2/:code/onboarding/plan
POST /api/v1/device/v2/:code/onboarding/ensure
GET  /api/v1/device/v2/:code/onboarding
```

`ensure` request should include:

```json
{
  "store_run_id": "dvsr_xxx",
  "monitoring_mode": "agent|snmp",
  "dry_run": false
}
```

`ensure` behavior:

- Single device only.
- Load latest or provided store run.
- Build required action list.
- Skip existing `success`.
- Execute only new, `failed`, or `unknown` action.
- Persist action results in `summary_json`.

## Acceptance

- PRD reflects confirmed manual single-device onboarding decisions.
- Evidence contract uses action results, not phase state machine.
- Network syslog remote config includes automatic save.
- Server monitoring mode is user-selected.
- Area basic services and system log strategy are configuration-file based.
- Independent listener management page is explicitly in scope and reuses the existing publish chain.
- Syslog listener management distinguishes server-vs-network semantics at the page/form layer.
- SNMP trap scope for this round stays at listener management only.
- OpenClaw story package remains draft until human review.

## Validation

- `jq empty docs/prd-autodev/device-v2-onboarding-observability/story-packages/batch-001.json`
- `rg -n "continue|ensure|first_existing|syslog|summary_json|failed|unknown" docs/prd-autodev/device-v2-onboarding-observability`

## OpenClaw Story Package

See `story-packages/batch-001.json`. It is intentionally `draft` and must not be published until reviewed.
