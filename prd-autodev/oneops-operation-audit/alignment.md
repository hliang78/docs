---
topic: oneops-operation-audit
kind: backend
title: OneOPS 操作审计轻量化设计
createdAt: 2026-05-21T11:55:18+0800
---

# Alignment

## Proposed Direction

- 第一阶段采用“混合方案 C”的轻量落地版本：
  - 不新建复杂子系统；
  - 不要求统一所有写入；
  - 先实现一个统一审计查询层；
  - 同时复用并标准化映射现有多源留痕。
- 把 `log_record` 视为“已有后台管理审计入口”，而不是废弃对象。
- 把 `device_v2_change_event` 视为“最成熟的结构化审计来源”。
- 把 `terminal_records`、`platform_monitoring_v2_credential_audit`、`platform_task_log` 视为高价值补充来源。
- 第一阶段后端交付物建议为：
  - 一个轻量统一审计 DTO 模型；
  - 一个统一查询 service；
  - 一个统一查询 API；
  - 至少覆盖 5 类来源的聚合查询结果。
 - 资产变更主线优先采用 Device V2 作为统一审计核心来源；`device_history` 留到后续兼容阶段。

## Options

- 方案 A：新建独立审计平台
  - 优点：概念统一
  - 缺点：太重，不符合当前边界
- 方案 B：只扩 `log_record`
  - 优点：最省事
  - 缺点：难以自然承载 Device V2、终端、凭证、任务等异构来源
- 方案 C：新增轻量统一查询层，复用现有来源
  - 优点：投入小、覆盖广、可逐步演进
  - 缺点：第一阶段仍是“读聚合优先”，统一写入要放后续

推荐采用方案 C。

## User Decisions

- 第一阶段全部高价值操作域都先覆盖一点。
- 重点目标：
  - 能追责谁改了什么
  - 能统一查询
- 约束：
  - 不要新建复杂子系统
  - 新增实现要简洁
- 实现策略：
  - 采用混合方案 C
- 当前会话目标：
  - 设计 + 后端最小实现 + 一个基础查询接口
- 资产变更优先级调整：
  - 优先审计 Device V2 及其相关链路
  - `device_history` 暂缓
