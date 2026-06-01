---
topic: generic-ai-autodev-platform
kind: full-stack
title: ReadinessDecision 冻结
createdAt: 2026-05-18T01:34:00+0800
program: true
status: draft
---

# Readiness Decision Freeze

## Purpose

- `ready-for-openclaw` 不是一个页面 badge，也不是一次按钮点击后的瞬时文案。
- 它本质上是多对象、多状态、多验证结果归并出来的正式决策。
- 这份文档的目标，是把 readiness 从“前端和评审人共同脑补的概念”提升成控制面与规划面共享的正式对象。

## Why This Must Be Formal

- 旧体系里，是否 ready 往往混杂在 review 文本、batch 状态、blocker 备注、worker 汇报和人工感觉里。
- 如果不把 readiness 冻成正式对象：
  - 前端会自己拼状态
  - human 会从 summary 猜结论
  - controller 无法稳定判断是否允许发布或开工

## Formal Objects

### `ReadinessDecision`

- 作用：
  - 表示某个 program 或 batch 当前是否具备进入下一阶段的正式结论。
- 至少包含：
  - `readinessDecisionId`
  - `ownerObjectType`
  - `ownerObjectId`
  - `status`
  - `decisionReason`
  - `blockingReasons`
  - `missingFields`
  - `releaseGateSummary`
  - `linkedSourceSnapshot`
  - `decidedAt`
  - `decidedBy`

### `ReadinessSummaryProjection`

- 作用：
  - 表示给前端、消息投影、人类审阅使用的只读摘要。
- 至少包含：
  - `ownerObjectType`
  - `ownerObjectId`
  - `status`
  - `bannerVariant`
  - `blockerSummary`
  - `missingFieldSummary`
  - `releaseGateSummary`
  - `verifierSummary`
  - `incidentSummary`
  - `updatedAt`
- 规则：
  - 它是 projection，不是新真相源。
  - 前端必须读取它，而不是自己从多个对象拼 readiness badge。

## Input Sources

`ReadinessDecision` 的输入必须是结构化对象，而不是自由文本：

- `PlanningReview`
- `BatchTruth`
- `StoryTruth`
- `BlockerRecord`
- `VerifierResult`
- `EvidenceSet`
- `PlatformIncident`
- `PreflightProbe`
- `TakeoverDecision`

必要时还可带：

- `ProofCompleteness`
- `ApprovalProfile`
- `RuntimeTaskPolicy`
- `DriverLearningRecord`

## Status Set

建议冻结以下状态：

- `not-ready`
- `ready-for-openclaw`
- `blocked-human-confirmation`
- `execution-waiting`
- `stopped`
- `closed`

## Decision Semantics

### `not-ready`

- 说明：
  - 仍缺关键 review、关键字段、关键 proof，或者存在未清 blocker。

### `ready-for-openclaw`

- 说明：
  - planning 已 reviewed，batch truth 完整，关键 verifier/proof 满足，且无未解决 release gate 风险。

### `blocked-human-confirmation`

- 说明：
  - 结构上大体成立，但仍需要 human 对范围、风险、取舍或审批做明确确认。

### `execution-waiting`

- 说明：
  - readiness 已满足，但尚未发布或尚在等待 runtime slot / task contract / operator action。

### `stopped`

- 说明：
  - 不是暂时没 ready，而是该 program/batch 被明确停止推进。

### `closed`

- 说明：
  - 该对象已经完成其生命周期，不再参与后续 readiness 归并。

## Promotion Rules

### Program-Level Readiness

一个 `Program` 进入 `ready-for-openclaw`，至少要求：

1. `PlanningReview.status = reviewed`
2. 存在至少一个结构完整、lane-scoped 的 `StoryBatch`
3. `BatchTruth` 没有关键 unresolved blocker
4. 关键 `VerifierResult` 与 `EvidenceSet` 足够支撑 readiness
5. 没有处于 `open/investigating/escalated` 的关键 `PlatformIncident`
6. `PreflightProbe` 不存在会直接阻止首批执行的关键失败

### Batch-Level Readiness

一个 `StoryBatch` 进入 `ready-for-openclaw`，至少要求：

1. batch 范围、lane、依赖和 release gate 已冻结
2. `missingFields` 为空或仅剩非 gate 级信息
3. `blockers` 为空，或仅剩不阻断发布的低级提示
4. verifier/proof 对当前阶段足够
5. task contract 与环境承接规则可被编译成执行输入

## Aggregation Rules

1. readiness 归并必须先读 truth，再读 verifier/evidence，再读 incident/probe。
2. 任一关键 gate 失败时，不允许被 UI summary 覆盖成绿色通过。
3. `PlatformIncident` 与 `PreflightProbe` 不是附属运维信息，它们可以直接拉低 readiness。
4. 活动中的 `TakeoverDecision` 也可以直接阻止或降级 readiness。
5. blocker、missing fields、release gate 必须同时存在于 decision 和 projection 中，不能只留一种展示。
6. 同一 owner object 的最新 `ReadinessDecision` 才有资格驱动前端与消息投影。

## Frontend Contract

- 前端的 result banner、右栏同步摘要、batch 审核固定摘要，必须读取 `ReadinessSummaryProjection`。
- 前端不允许：
  - 从多个 query 自己拼 `ready/not-ready`
  - 把 `PlanningReview.status = reviewed` 自动等同于 ready
  - 把单次 passed toast 当作正式 readiness truth
- 前端可以做的是：
  - 展示 projection
  - 触发新的 readiness check
  - 显示同步更新后的结果条与右栏摘要
- 如果存在活动接管，也必须在 readiness 摘要中明确提示，而不是前端静默忽略。

## Relationship To Existing Frontend Decisions

- `passed 5 秒自动消失，blocked/error 不自动消失` 仍成立，但它描述的是交互层行为，不是 decision 本体。
- `结果条 + 右栏同步` 现在有了正式对象承接：`ReadinessSummaryProjection`。
- batch 审核面板固定显示 `blockers / missing fields / release gate`，现在被正式提升为 decision 的必带摘要。

## What This Freeze Solves

- P-38 前端承接的是最难对象，但缺正式后端主对象
- P-39 `ready-for-openclaw` 不是 badge，而是多对象归并结果

## Implementation Consequence

- 后端必须提供：
  - `ReadinessDecision` schema
  - readiness reducer
  - projection read model
- 首期前端不需要实现全部管理能力，但必须以 projection 为唯一展示输入。
