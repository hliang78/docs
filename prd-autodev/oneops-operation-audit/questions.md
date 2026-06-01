---
topic: oneops-operation-audit
kind: backend
title: OneOPS 操作审计轻量化设计
createdAt: 2026-05-21T11:55:18+0800
---

# Question Round 001

## Purpose

Enrich the rough input before PRD or automation.

## Questions

1. What exact page, module, API, or workflow should this focus on first?
2. What outcome would make you say this is successful?
3. What must not change?
4. What are you most worried might go wrong?
5. Which users, roles, data, or environment should be treated as primary?
6. What evidence would convince you the work is really done?

## Answers

- Q1. What exact page, module, API, or workflow should this focus on first?
  A1. 全部都先覆盖一点，不想只做单点模块。
- Q2. What outcome would make you say this is successful?
  A2. 能追责“谁改了什么”，并且能统一查询。
- Q3. What must not change?
  A3. 不要新建复杂子系统；如果新增实现，需要尽量简洁。
- Q4. What are you most worried might go wrong?
  A4. 设计成一个庞大的模块，最后难以落地、难以维护。
- Q5. Which users, roles, data, or environment should be treated as primary?
  A5. 当前以后台管理/运维操作为主，重点覆盖已有高价值留痕：设备、Device V2、终端、监控凭证、任务审计、账号权限。
- Q6. What evidence would convince you the work is really done?
  A6. 先完成轻量统一设计，并在当前会话落地第一阶段后端最小实现，至少提供一个统一查询接口。

## Context Brief

### Goal

在不引入复杂子系统的前提下，为 OneOPS 设计并落地第一阶段统一操作审计能力，支持从多个现有留痕来源统一查询，并提升“谁改了什么”的追责能力。

### Boundaries

- 不做大型独立审计平台。
- 不要求一次性替换所有现有日志/历史表。
- 第一阶段以后端最小实现为主，不强求完整前端页面。
- 优先复用现有表和现有留痕能力。

### Focus

- 统一查询现有多源审计/历史记录。
- 为当前缺少统一视图但业务价值高的操作提供统一审计入口。
- 为后续逐步扩展统一审计事件模型保留空间。
- Device V2 作为当前主要资产变更入口优先处理；`device_history` 可以后置考虑。

### Concerns

- 设计过重。
- 覆盖太散导致第一阶段无法交付。
- 统一模型与现有多种留痕格式不兼容。

### Open Questions

- 第一阶段统一查询是否需要直接聚合 `log_record`。
- 第一阶段是否只做查询聚合，还是顺手补一小部分统一写入。
