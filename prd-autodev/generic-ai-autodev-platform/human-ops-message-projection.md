---
topic: generic-ai-autodev-platform
kind: full-stack
title: Human Ops Message Projection 冻结
createdAt: 2026-05-18T01:36:00+0800
program: true
status: draft
---

# Human Ops Message Projection

## Purpose

- Web workbench 仍然是自动驾驶系统的一线主界面。
- 但只靠 Web workbench，不足以覆盖：
  - 手机端快速知情
  - 审批型确认
  - repair 现场同步
  - 弱网或离桌状态下的轻控制
- 所以消息控制面不应继续靠“临场写一段话”，而要变成正式 projection contract。

## Positioning

- 这份文档不是把聊天软件升级成主真相源。
- 恰恰相反，它是为了把聊天输出降级成：
  - `formal control-plane export`
  - `mobile-friendly summary`
  - `human action prompt`
- 真相仍在对象层，消息只是投影。

## Formal Objects

### `MessageProjection`

- 作用：
  - 表示一次面向人类消息通道的结构化导出对象。
- 至少包含：
  - `messageProjectionId`
  - `targetChannelType`
  - `ownerObjectType`
  - `ownerObjectId`
  - `messageType`
  - `templateId`
  - `payload`
  - `redactionLevel`
  - `generatedAt`
  - `expiresAt`

### `MobileSummary`

- 作用：
  - 提供适合手机屏阅读的短格式摘要。
- 至少包含：
  - `title`
  - `status`
  - `oneLineReason`
  - `topBlockers`
  - `requiredAction`
  - `safeLinkRef`
  - `updatedAt`

### `ApprovalMessageTemplate`

- 作用：
  - 承载审批型消息模板。
- 必须包含：
  - 审批对象
  - 审批原因
  - 风险提示
  - 可执行动作
  - 超时说明

### `RepairMessageTemplate`

- 作用：
  - 承载 repair/incident 现场消息模板。
- 必须包含：
  - 事故摘要
  - 当前影响
  - 已尝试修复
  - 下一步建议

### `TakeoverMessageTemplate`

- 作用：
  - 承载外部接管型消息模板。
- 必须包含：
  - 当前对象
  - 当前 AI 司机意图
  - 接管原因
  - 可执行接管动作
  - 超时与恢复说明

### `StatusMessageTemplate`

- 作用：
  - 承载批次、story、program 的状态型摘要模板。
- 必须包含：
  - 当前状态
  - 简短原因
  - 是否需要 human action
  - 对应详情入口

## Message Design Rules

1. 一条消息只做一个目的：
   - 状态同步
   - 审批请求
   - repair 现场
   - readiness 结论
   - takeover 提示
2. 不用 markdown tables。
3. 默认适配手机屏阅读，优先短句、短段、短列表。
4. 消息正文不放 secrets、不放完整 token、不放敏感路径细节。
5. 详情通过安全链接或引用对象 id 进入 Web workbench。
6. 消息来源必须是 structured objects，不能从 chat history 和临时 prose 反推。

## Source Objects

消息投影允许读取的来源：

- `ReadinessDecision`
- `ReadinessSummaryProjection`
- `BlockerRecord`
- `PlatformIncident`
- `RepairRun`
- `VerifierResult`
- `EvidenceSet`
- `DriverLearningSignal`
- `DriverLearningRecord`
- `PlanningReview`
- `TakeoverRequest`
- `TakeoverDecision`
- `ComponentEndSignal`
- `EndSignalEvaluation`
- `EndSignalProjection`
- `BatchTruth`
- `StoryTruth`

禁止直接作为消息真相源的内容：

- worker 自由文本 footer
- 旧 report 截断 summary
- 零散状态文件
- 人工口头复述

## Template Semantics

### Approval Flow

- 审批消息必须明确：
  - 现在卡住什么
  - 需要 human 选什么
  - 不响应会怎样
- 不能把审批消息写成冗长日报。

### Takeover Flow

- 接管消息必须明确：
  - 当前谁在推进
  - 为什么需要接管
  - 可以暂停、覆写、改路由还是恢复
  - 不接管会有什么风险

### Repair Flow

- repair 消息必须明确：
  - 当前是环境/权限/provider/process 哪类故障
  - 自动修复到哪一步
  - 是否已升级为 human intervention

### Status Flow

- 状态消息必须明确：
  - 当前对象
  - 当前状态
  - 一句话原因
  - 是否需要点击回 workbench

### End Signal Flow

- 如果消息里提到了“结束”，必须明确：
  - 到底是哪个组件结束了自己的工作
  - 这个结束只被接受到哪一层
  - 还有哪一层没有正式闭环
- 禁止把局部结束信号写成：
  - “任务已全部完成”
  - “流程已关闭”
  - “可以直接收尾”
- 除非已经收到正式 acceptance，否则消息面只能说：
  - 结束了什么
  - 尚未结束什么
  - 下一步建议路由是什么

## Relationship To Web Workbench

- Web workbench 是 primary UI。
- message projection 是 secondary control export。
- 任何消息里的状态、blocker、readiness、end signal，都必须能回链到 workbench 中的同一对象摘要。
- 这保证：
  - 手机端适合知情与轻操作
  - 真正复杂的上下文仍在工作台完成

## Security And Redaction

- `MessageProjection.redactionLevel` 必须控制：
  - 哪些字段可发到外部消息通道
  - 哪些字段只允许 workbench 内看
- 默认策略：
  - 发状态，不发 secrets
  - 发摘要，不发原始日志
  - 发对象引用，不发敏感 payload

## What This Freeze Solves

- P-02 控制面需要手机友好的短格式回报，而不是长文报告

## Implementation Consequence

- 即使首期不做完整消息分发后台，也必须先冻结：
  - message projection schema
  - mobile summary schema
  - approval/repair/status/takeover 模板对象
  - end signal message wording rule
- 这样未来继续承接微信/手机控制面时，系统不会重新退回“靠聊天现编”的旧模式。
