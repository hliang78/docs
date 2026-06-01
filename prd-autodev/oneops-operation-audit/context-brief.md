---
topic: oneops-operation-audit
kind: backend
title: OneOPS 操作审计轻量化设计
createdAt: 2026-05-21T11:55:18+0800
---

# Context Brief

## Goal

为 OneOPS 设计并落地第一阶段统一操作审计能力。

成功标准：
- 可以从一个统一接口查询多种已有审计/留痕来源。
- 可以更直接回答“谁改了什么”。
- 不引入复杂的新子系统。
- 在当前会话内完成第一阶段后端最小实现。

## Boundaries

- 不做大而全的独立审计平台。
- 不要求第一阶段完全统一所有历史数据结构。
- 不优先做大规模前端改造。
- 不引入消息队列、异步审计中心、复杂事件总线等重型设施。

## Focus

- 全部高价值操作域先覆盖一点：
  - 老设备变更历史
  - Device V2 变更
  - 终端会话/登录
  - Monitoring 凭证审计
  - 任务审计摘要
  - 账号/权限类系统日志
- 统一查询层
- 轻量统一模型
- 少量必要补写点
- 当前资产台账变更以 Device V2 为主，因为 Device V2 入库后还会同步到 V1；老 `device_history` 暂不作为第一阶段重点来源。

## Background

OneOPS 当前已经存在多套分散留痕能力，但没有统一操作审计中心：
- `device_history` 记录老设备台账变更；
- `device_v2_change_event` / `device_v2_change_field` 记录 Device V2 字段级变更；
- `terminal_records` 记录终端会话；
- `platform_monitoring_v2_credential_audit` 记录凭证解析/校验/使用；
- `platform_task_log` 中存在材料解析与审批相关审计摘要；
- `log_record` 已覆盖部分账号、组织、站点等后台管理 API；
- `aiops_incident_analysis_record` 记录 AI 分析留痕。

当前最大问题不是“没有留痕”，而是“无法统一查询、统一理解、统一追责”。

## Primary Users / Systems

- 平台管理员
- 运维/网络/设备管理人员
- 审计/追责场景下的排查人员
- 依赖现有留痕表的后端模块

## Known Constraints

- 当前系统已存在多个不同风格的审计/日志表，不能一次性重构。
- 现有部分 API 已直接写 `log_record`，部分模块完全不写。
- 老设备历史与 Device V2 变更模型差异较大。
- 终端、监控、任务审计都各自有独立语义。
- 资产变更侧当前更应关注 Device V2 入口及其向 V1 的同步链路，而不是优先治理旧 `device_history`。

## Concerns

- 方案过重，超出当前会话可交付范围。
- 统一层设计不当，导致后续接入反而更复杂。
- 一次性试图做“统一写入 + 统一存储 + 统一页面”，风险过高。
- 轻量方案如果只查不补写，会继续留下部分追责盲区。

## Evidence Needed

- 明确的第一阶段设计文档
- 第一阶段统一审计接口
- 可展示的来源覆盖清单
- 最基本的查询验证结果

## Open Questions

- 第一阶段是否采用“纯聚合查询”，还是“聚合查询 + 新增轻量统一事件表”的混合策略。
- 对 `log_record` 的复用应是直接聚合，还是同时做标准化映射抽象。
