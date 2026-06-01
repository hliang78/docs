---
topic: device-v2-onboarding-observability
kind: full-stack
title: Device V2 纳管观测闭环极简设计
status: draft
---

# Minimal Design

## 设计原则

目标不是新增一个“大纳管平台”，而是在现有 Device V2 store runtime 上补齐最小闭环。

原则：

- 不新增复杂编排引擎。
- 尽量不新增表，优先复用 `device_v2_store_run.summary_json`。
- 入库主链路保持短：采集、校验、持久化仍是 store runtime 的核心职责。
- 后续纳管动作必须幂等：重复执行不会重复创建设备、重复覆盖无关 agent 配置、重复远程改设备配置。
- 首期 `继续纳管` 只对单台设备执行，批量只生成计划或逐台展示结果。
- 网络设备远程配置属于首期过程，配置成功后自动保存。
- 网络设备日志纳管首期优先 syslog，SNMP trap 先做一级定义和 teleabs 模板缺口。

## 一句话方案

在 Device V2 store run 成功后，追加一个极简 `onboarding` 摘要对象，按需执行三个幂等动作：

```text
ensure_v1_bridge -> dispatch_monitoring -> prepare_log_onboarding -> verify_observed
```

其中 `prepare_log_onboarding` 对网络设备首期优先 syslog，并允许单台远程配置与自动保存；SNMP trap 先只生成一级定义和模板缺口。

## 现有对象复用

### 根对象

复用 `device_v2_store_run`：

- `run_id`: 单台设备入库 run。
- `task_id`: 批量 store task。
- `device_code`: Device V2 code。
- `summary_json`: 存放 onboarding evidence。

不新增 `onboarding_run` 表。只有当 summary 变得不可维护、查询压力明显增加时，再考虑拆表。

### Device V2 摘要

Device V2 attributes 只存少量摘要字段，避免污染动态属性：

- `onboarding_status`: `none|pending|managed|partial|blocked`
- `onboarding_run_id`
- `device_v1_code`
- `monitoring_status`
- `log_onboarding_status`
- `observed_status`

详细证据仍在 store run summary 里。

## Summary Contract

在 `DeviceV2StoreRun.Summary` 增加一个 `onboarding` 字段：

```json
{
  "onboarding": {
    "status": "pending|managed|partial|blocked",
    "updated_at": "2026-05-15T00:00:00+08:00",
    "steps": {
      "v1_bridge": {
        "status": "success|failed|skipped",
        "device_v1_code": "DEV_xxx",
        "message": ""
      },
      "monitoring": {
        "status": "success|failed|skipped",
        "task_ids": [],
        "message": ""
      },
      "log_plan": {
        "status": "ready|blocked|manual_required|skipped",
        "device_kind": "server|network|unknown",
        "plan": {},
        "message": ""
      },
      "verify": {
        "status": "success|partial|failed|waiting|skipped",
        "prometheus_seen": false,
        "loki_seen": false,
        "queries": [],
        "message": ""
      }
    }
  }
}
```

这个结构只表达最终证据，不试图记录完整工作流日志。需要完整日志时看已有任务日志、监控任务记录、controller/agent 返回。

## Step 1: Ensure V1 Bridge

复用现有 `syncOneDeviceV2ToV1` 逻辑，但从 API handler 中抽成 service/helper，供 store runtime 或后续 action 调用。

幂等键：

- Device V2 attributes 中已有 `device_v1_code` 时，确认 V1 存在并跳过创建。
- 没有 `device_v1_code` 时，按 SN/IP 查重，能匹配则回填。
- 找不到才创建 V1。

输出：

- `device_v1_code`
- `status`
- `message`

## Step 2: Dispatch Monitoring

复用现有：

```text
DeviceStoreSrv.NotifyMonitorProbeByDeviceCodes(ctx, []v1Code, credentialSourceByV1Code)
```

首期不强求拿到所有 task id；只记录调用结果和可用于后续 reconcile 的 device/v1 code。后续如果已有监控任务 projection 可查询，再补 `task_ids`。

幂等边界：

- 监控任务下发必须沿用现有监控治理的 stable task id。
- 重试只重新 reconcile/apply 当前设备相关任务，不新造平行任务。

## Step 3: Prepare Log Onboarding

这是最容易复杂化的地方，首期只做 planner，不做危险执行。

### Server

判断为服务器时：

1. 检查是否有 agent。
2. 有 agent：生成日志转发计划，目标是 `inputs.tail` 或已有 syslog/file log 方案，输出到 `outputs.loki`。
3. 无 agent：返回 `manual_required`，提示先部署 agent。

首期只写 plan：

```json
{
  "kind": "server",
  "requires_agent": true,
  "agent_code": "agent_xxx",
  "actions": ["apply_loki_log_task"]
}
```

### Network

判断为网络设备时：

1. 找到设备 FunctionArea 对应的区域 agent。
2. 检查该 agent 是否已有 syslog listener 和 snmp_trap listener。
3. 若 listener 不存在，生成 agent listener 下发计划。
4. 若 listener 存在，生成网络设备远程配置 dry-run plan。

首期不自动下发远程配置，只输出：

```json
{
  "kind": "network",
  "area": "DefaultArea",
  "agent_code": "agent_xxx",
  "listener": {
    "syslog": "udp://10.0.0.1:514",
    "snmp_trap": "udp://10.0.0.1:162"
  },
  "remote_config": {
    "mode": "dry_run",
    "approval_required": true
  }
}
```

## Step 4: Verify Observed

首期验证可以做成轻量查询，不要做复杂诊断。

Prometheus：

- 查询目标设备最近窗口是否有任意核心指标。
- 最小候选：`up`、ping、SNMP/interface、agent task observed metric。

Loki：

- 服务器：按 device/ip/agent/source 查询日志。
- 网络：按 device/ip/agent/source=syslog 或 source=snmp_trap 查询。

状态规则：

- Prometheus 与 Loki 都看到：`managed`
- Prometheus 看到、Loki 未看到：`partial`
- Loki 看到、Prometheus 未看到：`partial`
- 都未看到但刚下发：`pending`
- 前置条件缺失：`blocked`

## API 极简增量

首期只需要两个 API，甚至可以先只做一个：

### 推荐

```text
POST /api/v1/device/v2/store/runs/:run_id/onboarding:ensure
GET  /api/v1/device/v2/store/runs/:run_id/onboarding
```

`ensure` 做幂等推进：能做的做，不能做的写 evidence，不长时间等待 Prom/Loki。

### 更极简

只扩展现有 task summary/detail API，把 `summary.onboarding` 返回给前端。推进动作先放在 store runtime 尾部或重试按钮中。

## 前端极简改法

不要新建大页面。只改 Device V2 管理页：

- 主按钮文案从“采集验证”改为“采集入库”或“启动纳管”。
- 行状态点保持现有 UI，但 step 改为：
  - 入库
  - V1
  - 监控
  - 日志
  - 验证
- 详情抽屉里展示 `summary.onboarding.steps`。
- “日志”动作先改为“查看日志纳管计划”，不是直接跳日志页面。

## 为什么这比大编排稳定

- 少表：不引入新的生命周期存储。
- 少状态：只在 store run summary 里表达结果，不维护复杂任务 DAG。
- 易回滚：失败只影响当前 run 的 onboarding summary。
- 易渐进：先做 V1 + 监控，再做 log plan，再做 verify。
- 风险可控：网络设备远程配置默认 dry-run，不自动改现场。

## 分阶段落地

### Phase 1: 语义和 evidence

- 前端文案和状态改成纳管语义。
- `summary.onboarding` contract 落地。
- store 成功后写 `pending` onboarding 摘要。

### Phase 2: V1 + 监控

- 抽出 `EnsureV1Bridge` service/helper。
- store 成功后幂等执行 V1 bridge。
- V1 成功后调用现有监控推送。

### Phase 3: 日志计划

- 只生成 server/network log onboarding plan。
- 网络设备 remote config 只 dry-run。

### Phase 4: 观测验证

- 添加轻量 Prom/Loki 查询。
- 将结果写回 `summary.onboarding.steps.verify`。

## 暂不做

- 不做独立 onboarding DAG。
- 不做复杂审批系统。
- 不直接执行网络设备远程配置。
- 不新增大量监控/日志策略模板。
- 不要求一次性验证所有指标和所有日志源。
