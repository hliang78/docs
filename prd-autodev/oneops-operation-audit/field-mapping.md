---
topic: oneops-operation-audit
kind: backend
title: OneOPS 统一操作审计字段映射
createdAt: 2026-05-21T16:10:00+0800
---

# 字段映射

这份文档只回答一个问题：

旧 `日志管理` 兼容页和新 `操作审计` 正式页之间，字段是怎么对应的，哪些能力保留，哪些能力只是统一审计补充。

## 核心差异

- 旧页核心来源只有 `log_record`
- 新页核心是多来源聚合
- 旧页偏“后台操作日志”
- 新页偏“统一审计视图”

## 旧页到新页的字段对应

| 旧日志页字段 | 旧来源 | 新统一审计字段 | 说明 |
| --- | --- | --- | --- |
| `module` | `log_record.module` | `module` | 新页会做模块域归一化，例如 `system` / `device_v2` / `terminal` |
| `resource` | `log_record.resource` | `action` + `summary` | 新页把动作和摘要拆开，不再只保留原始资源名 |
| `requester` | `log_record.requester` | `operator` | 统一为操作人 |
| `created_time` | `log_record.created_time` | `occurred_at` | 统一成事件发生时间 |
| `process_time` | `log_record.process_time` | `detail.process_time` | 保留在详情里，不放列表主字段 |
| `status` | `log_record.status` | `status` | 新页会统一显示状态标签 |
| `fail_reason` | `log_record.fail_reason` | `detail.fail_reason` | 失败原因放详情主卡片中 |
| `request_info` | `log_record.request_info` | `detail.request_info` | 作为原始详情预览保留 |
| `response_info` | `log_record.response_info` | `detail.response_info` | 作为原始详情预览保留 |
| `org_code` | `log_record.org_code` | `detail.org_code` | 仅详情展示 |

## 新页新增但旧页没有的统一字段

- `source_type`
- `source_label`
- `resource_type`
- `resource_id`
- `risk_level`
- `raw_ref`

这些字段是统一审计的关键，因为它们帮助回答：

- 这条记录来自哪张来源表
- 这是哪类资源
- 具体资源标识是什么
- 是否高风险
- 原始证据在哪里

## 各来源映射规则

### 1. `log_record`

- `source_type` = `log_record`
- `module` = `system`
- `action` = `resource`
- `operator` = `requester`
- `summary` = `module / resource`
- `status` = `status`
- `detail.*` 保留旧详情

### 2. `device_v2_change_event`

- `source_type` = `device_v2_change_event`
- `module` = `device_v2`
- `action` = `action`
- `operator` = `operator`
- `resource_type` = `entity_type`
- `resource_id` = `device_code` 优先，其次 `entity_id`
- `summary` = `summary/title`
- `risk_level` = `risk_level`
- `source_label` = 来源中文标签

### 3. `terminal_records`

- `source_type` = `terminal_records`
- `module` = `terminal`
- `action` = `login`
- `operator` = `operator`
- `resource_type` = `session`
- `resource_id` = `instance_code/host`
- `summary` = `协议 + 用户名 + 主机`
- `status` = `active/completed`

### 4. `platform_monitoring_v2_credential_audit`

- `source_type` = `platform_monitoring_v2_credential_audit`
- `module` = `monitoring`
- `action` = `resolve/validate/use`
- `operator` = `operator`
- `resource_type` = `resource_type`
- `resource_id` = `credential_ref/plan_id/request_id`
- `summary` = `action + credential_ref`
- `status` = `result`

### 5. `platform_task_log(task_material_resolve)`

- `source_type` = `platform_task_log`
- `module` = `task`
- `action` = `task_material_resolve`
- `operator` = 空
- `resource_type` = `task`
- `resource_id` = `task_id`
- `summary` = 审批单/审计单/凭证/决策的摘要
- `status` = `decision` 优先，其次 `level`

## 第一阶段保留旧页的能力

- 原始 `request_info / response_info` 查看方式
- 仅看旧系统日志时的简单认知成本
- 已有菜单入口和习惯

## 第一阶段新页新增的能力

- 跨来源统一查
- 统一时间线
- 统一来源标识
- 统一资源类型 / 资源标识
- Device V2 风险等级展示
- 终端 / 凭证 / 任务审计和旧系统日志混合查看

## 第一阶段仍不替代的能力

- 旧页的“只看 log_record”心智非常直接，仍适合老排障路径
- 各来源的领域专用页面仍是最终细节页
- 这版不是审计治理闭环，不承担审批/确认/告警编排
