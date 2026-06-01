---
topic: generic-ai-autodev-platform
kind: full-stack
title: 自动驾驶系统
createdAt: 2026-05-17T10:40:32+0800
program: true
---

# Permissions And Error States

## Purpose

定义首期 MVP 在“只读 + 审阅 + 状态推进”模式下的权限边界、禁止动作和关键错误状态，避免在代码阶段误把规划工作台做成运行控制台或全量编辑器。

## Findings

- 当前首期角色更偏 `planner/architect/frontend-owner/backend-owner/ct-owner`，不是运行态值班控制台用户。
- 用户已明确：首期前端主线是 `PRD/StoryBatch 文档与批次管理`，而不是 OpenClaw 运行控制或模型/profile 配置。
- `openclaw` 现有控制体系已明确审批边界、allowed writes、repair/approval 生命周期，说明“能做什么”必须结构化，而不是隐藏在文案里。
- 规划阶段的最大风险不是普通接口报错，而是错误地允许：
  - 提前发布 batch
  - 提前启动 OpenClaw
  - 把 draft 当 reviewed
  - 把轻量编辑扩展成广义文档重写
- 首期文档内容主要来自文件资产，天然会面临缺文件、状态不一致、引用失效、readiness 证据缺失等错误态。

## Requirements

- 明确首期最小角色与动作边界。
- 明确 `read`、`review`、`state progression`、`light edit`、`publish`、`start runtime` 之间的权限等级。
- 明确页面级错误状态，至少覆盖：
  - program 不存在
  - 文档缺失
  - 文档状态不一致
  - batch story 依赖不完整
  - readiness 未满足
  - AI 优化或轻量编辑超边界
- 明确哪些错误属于：
  - 可直接提示并继续
  - 需要人工确认
  - 必须阻断进入代码或 OpenClaw

## Acceptance

- 可以说清首期哪些操作必须只读，哪些操作可以推进状态，哪些操作必须拦截。
- 可以为 `candidate-06-api-documentation.md` 提供权限与错误码输入。
- 可以为前端专题讨论提供页面级空态、错态、禁用态清单。

## Validation

- 与 `alignment.md` 中“先只读 + 审阅 + 状态推进”的决策一致。
- 与 `openclaw-control-plane-mapping.md` 的 approval/repair 语义不冲突。
- 与 `candidate-04-prototype-list.md` 的页面形态一致，不把首期页面误扩成运行控制台。

## Candidate Stories

- 明确首期权限矩阵与禁用动作。
- 列出页面级核心错误状态与对应用户提示策略。
- 输出后续 API 需要承载的错误码与 readiness 拦截规则。

## Candidate Permission Matrix

| 动作 | 首期是否允许 | 说明 |
|---|---|---|
| 浏览 program 列表/详情 | 允许 | 核心只读能力 |
| 浏览规划文档 | 允许 | 核心只读能力 |
| 浏览 StoryBatch/RuntimeStory/readiness | 允许 | 核心只读能力 |
| 标记审阅状态/推进 planning 状态 | 允许 | 需保留审计信息 |
| AI 多轮优化建议 | 后续补入 | 不进入本轮首批代码切片 |
| 轻量编辑低风险字段 | 后续补入 | 需先冻结字段范围 |
| 发布到 OpenClaw | 禁止 | 本轮停在代码前 |
| 启动/停止 loop、repair、pool | 禁止 | 不属于首期主线 |
| 模型/profile 全量管理 | 禁止 | 后续 batch 再补 |

## Candidate Error States

| 错误状态 | 触发场景 | 前端处理 | 是否阻断 |
|---|---|---|---|
| `program-not-found` | Topic/Program 不存在或路径失效 | 展示空态并返回首页 | 否 |
| `document-missing` | 某文档不存在 | 标记缺失并提示补齐 | 否 |
| `document-status-conflict` | 文档 metadata 与实际内容状态冲突 | 标红并要求人工复核 | 是 |
| `batch-invalid-story` | story 缺少 lane/validation/allowedPaths 等关键字段 | readiness 面板阻断 reviewed | 是 |
| `batch-dependency-conflict` | dependsOn 指向不存在或循环依赖 | 阻断 reviewed | 是 |
| `readiness-not-met` | `01-07` 或 mapping 仍缺关键输入 | 阻断进入代码或发布 | 是 |
| `action-out-of-scope` | 用户尝试进入运行控制/高风险动作 | 明确提示“当前阶段不支持” | 否 |
| `edit-boundary-exceeded` | 轻量编辑触达非白名单字段 | 拒绝保存并提示人工讨论 | 是 |

## API-Level Suggestions

- `403`
  - 用于超出首期边界的动作，例如试图直接发布 batch 或进入运行控制。
- `409`
  - 建议用于 readiness/status 冲突，例如 draft batch 被要求 promote。
- `422`
  - 建议用于 story schema 不完整、依赖冲突、文档缺关键元数据等可校验问题。
