---
topic: device-v2-onboarding-observability
kind: full-stack
title: 远程访问纳管极简策略
status: draft
---

# Remote Access Minimal Strategy

## 已确认业务定义

纳管分为两类：

- 监控纳管
- 日志纳管

纳管成功以“配置成功”为主，不以 Prometheus/Loki 已收到数据为必须条件。

## 已确认首期决策

- `继续纳管` 首期只对单台设备执行；批量只生成计划或逐台展示结果。
- 网络设备远程配置 syslog/trap target 后自动保存配置。
- 网络设备日志纳管首期优先 syslog；SNMP trap 先做一级定义和 teleabs 模板缺口。
- 服务器监控方式由用户选择 agent / SNMP。
- 服务器日志纳管有 agent 时优先 agent；无 agent 时生成 SSH 配置计划。
- Linux 系统日志默认文件为 `/var/log/syslog`、`/var/log/auth.log`、`/var/log/messages`、`/var/log/secure`，策略模式为 `first_existing`。
- FunctionArea 区域基础服务首期先放配置文件。
- 再次点击 `继续纳管` 时只重试 `failed` / `unknown` 的 ensure。

## 设备类型与纳管方式

### 网络设备

监控纳管：

- 下发监控任务成功即视为监控纳管成功。
- agent 权威来源沿用现有 FunctionArea + 能力开关机制。

日志纳管：

- syslog 或 SNMP trap 二选一或两者都可。
- 远程登录网络设备，配置 syslog target 或 trap target 指向区域 agent IP。
- 目标 agent 必须开启对应监听器。
- syslog 当前已有监听任务下发流程。
- 首期优先 syslog。
- SNMP trap 需要由 teleabs 定义模板，再评估是否复用 syslog listener 流程。
- syslog / snmp_trap 适合升级为区域基础服务的一级定义。

### 服务器

监控纳管：

- 方式 A：先部署 agent，再下发监控任务。
- 方式 B：远程登录服务器开启 SNMP，通过 SNMP 监控。
- 首期由用户选择 agent / SNMP。

日志纳管：

- 方式 A：先部署 agent，再下发系统日志转发任务。
- 方式 B：远程 SSH 登录服务器，在目标服务器配置日志转发。
- 有 agent 时优先 agent；无 agent 时生成 SSH 配置计划。
- 首期只考虑系统日志。

## 最大问题

远程访问天然不稳定：

- 网络延迟大。
- 登录协议和凭据不统一。
- 设备型号、系统版本、命令差异大。
- 命令可能半成功。
- 设备可能需要保存配置。
- 重试可能造成重复配置。

所以不应该用很多状态去“模拟流程”，而应该把远程动作做成幂等的 `ensure`。

## 极简处理原则

### 1. 不控制状态，记录结果

不要设计复杂状态机，例如：

```text
pending -> connecting -> logged_in -> configuring -> saving -> verifying -> done
```

改成只记录一次动作结果：

```json
{
  "action": "ensure_syslog_target",
  "target": "DVC...",
  "desired": {"server": "10.0.0.10", "port": 514},
  "result": "success|failed|unknown",
  "changed": true,
  "message": "",
  "evidence": {}
}
```

页面状态由结果推导：

- 全部 required action 成功：已纳管
- 有失败：未完成
- 有 unknown：需要人工确认或重试

### 2. 所有远程动作都是 ensure，不是 set

远程命令不要表达为“执行这些命令”，而要表达为“确保目标配置存在”。

例子：

- `ensure_syslog_target(agent_ip, port)`
- `ensure_snmp_trap_target(agent_ip, port, version, community_or_user)`
- `ensure_server_snmp_enabled(...)`
- `ensure_server_log_forwarding(agent_or_loki_target, files)`

每个 ensure 内部允许有：

1. 查询当前配置
2. 判断是否已经满足
3. 缺失时应用最小变更
4. 查询确认

但对外只暴露一个结果。

### 3. 不做长事务

一次“继续纳管”点击可以发起一批 ensure，但不能假设所有远程设备会同步完成。

建议：

- UI 点击 `继续纳管`
- 后端生成 onboarding plan
- 后端按设备逐个执行短 timeout ensure
- 超时/失败写 evidence
- 用户可再次点击重试

不需要引入复杂队列时，首期可以同步执行少量设备；批量时再走现有 task/runtime。

### 4. 模板负责差异，不让流程负责差异

设备差异不要体现在状态机里，而体现在模板里。

一级对象：

```text
capability: syslog_listener | snmp_trap_listener | server_snmp | server_log_forward
template: vendor/platform/os specific
ensure: stable action contract
```

例如网络设备 syslog：

```json
{
  "capability": "network_syslog_target",
  "vendor": "huawei",
  "platform": "vrp",
  "ensure_action": "ensure_syslog_target",
  "commands": {
    "inspect": ["display current-configuration | include info-center loghost"],
    "apply": ["info-center loghost {{agent_ip}}"],
    "verify": ["display current-configuration | include {{agent_ip}}"]
  }
}
```

这样流程永远只知道执行 `ensure_syslog_target`，不关心 H3C/Huawei/Cisco 命令差异。

网络设备配置动作必须包含保存配置步骤。保存命令也由模板负责，不由流程硬编码。

### 5. 区域基础服务一级定义

syslog 和 snmp_trap 不建议作为普通设备任务散落管理，应该作为 FunctionArea 的基础服务能力。

首期先放配置文件，不新建表。

建议定义：

```json
{
  "function_area": "DefaultArea",
  "services": {
    "syslog": {
      "enabled": true,
      "agent_code": "agent-a",
      "listen_ip": "10.0.0.10",
      "listen_port": 514,
      "protocol": "udp"
    },
    "snmp_trap": {
      "enabled": true,
      "agent_code": "agent-a",
      "listen_ip": "10.0.0.10",
      "listen_port": 162,
      "protocol": "udp"
    }
  }
}
```

网络设备日志纳管只依赖这个定义，不临时猜 agent。

## 系统日志策略

系统日志不应硬编码在流程里，应有一个轻量策略。

首期策略可以非常小：

```json
{
  "strategy_id": "linux_system_default",
  "os_family": "linux",
  "files": ["/var/log/syslog", "/var/log/auth.log", "/var/log/messages", "/var/log/secure"],
  "mode": "first_existing",
  "output": "loki"
}
```

策略执行规则：

- `first_existing`: 只采目标机存在的文件。
- `required`: 必须存在，否则阻断。
- `optional`: 不存在只 warning。

Windows 或其他系统后续加策略，不改流程。

## 标签 attach 插件

标签来自 attach 插件，并随监控任务一起下发。

短期处理：

- 不重新设计标签系统。
- onboarding evidence 只记录“本次依赖 attach 插件标签”。
- 若后续要把标签升级为一级定义，可以和区域基础服务一起纳入 FunctionArea capability。

## 推荐的最小数据结构

仍然写入 `device_v2_store_run.summary_json`：

```json
{
  "onboarding": {
    "required": ["monitoring", "log"],
    "actions": [
      {
        "key": "monitoring.dispatch",
        "title": "下发监控任务",
        "required": true,
        "result": "success",
        "changed": true,
        "message": ""
      },
      {
        "key": "log.network.syslog_target",
        "title": "配置网络设备 syslog 目标",
        "required": true,
        "result": "failed",
        "changed": false,
        "message": "ssh timeout",
        "retryable": true
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

注意：这里不是一堆状态，而是 action result 列表。整体状态由 action result 计算。

## UI 表达

前端不要展示复杂阶段，只展示两栏：

- 监控纳管：成功 / 未完成 / 可重试
- 日志纳管：成功 / 未完成 / 可重试

点开详情再看 action evidence：

- 监控任务下发
- agent listener 检查
- 远程配置结果
- 日志策略应用结果

## 首期建议做什么

1. `继续纳管` 按钮。
2. 后端生成 minimal onboarding actions。
3. 先接入监控纳管已有机制。
4. syslog listener 复用已有流程，只记录区域基础服务缺口。
5. SNMP trap 只做一级定义和模板缺口，不强行实现。
6. 服务器系统日志先用轻量策略，默认 `first_existing`。
7. 远程配置执行只支持单台、短 timeout、可重试、结果写 evidence。

## 暂缓

- 多状态工作流。
- 长轮询验证 Prometheus/Loki。
- 批量大规模远程配置。
- 自动保存所有网络设备配置。
- 完整审批流。
- 多厂商全量命令模板。
