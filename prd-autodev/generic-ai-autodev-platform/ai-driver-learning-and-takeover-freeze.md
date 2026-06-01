---
topic: generic-ai-autodev-platform
kind: full-stack
title: AI 司机学习与外部接管冻结
createdAt: 2026-05-18T04:25:00+0800
program: true
status: draft
---

# AI Driver Learning And External Takeover Freeze

## Purpose

- 这份文档冻结“自动辅助驾驶系统 + AI 司机”模型里另外两个必须正式成立的通道：
  - AI 司机学习通道
  - 外部接管通道
- 如果这两条通道不被对象化，系统很容易退回：
  - AI 司机每轮像失忆一样重复犯错
  - 接管只能靠人工聊天喊停
  - 高风险推进没有正式覆写入口

## Core Rule

1. AI 司机可以提出推进意图，但不能拥有不可撤销的单向控制权。
2. AI 司机的学习输入必须来自结构化反馈，而不是散落聊天 prose。
3. 外部接管必须是正式控制动作，而不是临场口头干预。
4. 学习和接管都只能影响后续判断、后续路由和后续执行，不能偷偷改写历史 truth。

## Formal Objects

### `DriverLearningSignal`

- 作用：
  - 表示一次可被 AI 司机吸收的结构化学习信号。
- 至少包含：
  - `driverLearningSignalId`
  - `ownerObjectType`
  - `ownerObjectId`
  - `sourceObjectType`
  - `sourceObjectId`
  - `signalType`
  - `signalSeverity`
  - `signalSummary`
  - `extractedAt`
- 常见类型：
  - `verifier-failed`
  - `evidence-insufficient`
  - `acceptance-rejected`
  - `incident-repeated`
  - `route-misclassified`
  - `readiness-misjudged`

### `DriverLearningRecord`

- 作用：
  - 表示一轮或一段周期内，AI 司机已经吸收的学习结论。
- 至少包含：
  - `driverLearningRecordId`
  - `ownerObjectType`
  - `ownerObjectId`
  - `programCycleId`
  - `inputSignalIds`
  - `recommendedIntentAdjustment`
  - `recommendedGuardAdjustment`
  - `recommendedPolicyAdjustment`
  - `confidence`
  - `recordedAt`

### `TakeoverRequest`

- 作用：
  - 表示来自 human 或外部控制面的正式接管请求。
- 至少包含：
  - `takeoverRequestId`
  - `ownerObjectType`
  - `ownerObjectId`
  - `requestedBy`
  - `requestedAction`
  - `takeoverReason`
  - `targetRoute`
  - `priority`
  - `requestedAt`
- 常见动作：
  - `pause`
  - `override-intent`
  - `reroute-to-review`
  - `reroute-to-repair`
  - `force-approval`
  - `resume`

### `TakeoverDecision`

- 作用：
  - 表示一次外部接管请求的正式处理结果。
- 至少包含：
  - `takeoverDecisionId`
  - `linkedTakeoverRequestId`
  - `decision`
  - `effectiveAction`
  - `effectiveUntil`
  - `decidedBy`
  - `decidedAt`
- 结论至少支持：
  - `accepted`
  - `rejected`
  - `expired`
  - `applied`

## Learning Channel Rule

### Allowed Inputs

- AI 司机学习通道允许吸收：
  - `VerifierResult`
  - `EvidenceSet`
  - `ProofCompleteness`
  - `CycleBackfeed`
  - `PRDAcceptanceDecision`
  - `PlatformIncident`
  - `ReadinessDecision`
  - `BlockerRecord`

### Allowed Outputs

- 学习通道可以影响：
  - 下一轮 `IntentRequest`
  - `RuntimeTaskPolicy`
  - `ApprovalProfile`
  - `OrchestrationSafetyGuard`
  - `ActionPlan` 的偏好选择
- 学习通道不能直接改写：
  - `StoryTruth`
  - `BatchTruth`
  - `TurnTruth`
  - 已完成的 `VerifierResult`

### Required Semantics

1. 学习结论必须有来源信号。
2. 学习结论必须能回链到具体 cycle、story、incident 或 verifier。
3. 学习结论必须作为下一轮引擎输入的一部分，而不是只放在总结段落里。
4. 同一类重复事故应能够积累成更强的 guard/policy 调整建议。

## External Takeover Rule

### When Takeover Must Be Possible

以下场景必须保留正式接管入口：

1. AI 司机持续误判 blocker 路由。
2. AI 司机试图推进高风险状态转换。
3. readiness、approval、acceptance 结论与业务预期明显冲突。
4. incident/repair 已经说明系统当前不适合继续自动推进。
5. 人类需要临时暂停、切换路线或收回执行权。

### What Takeover Can Change

- 外部接管可以正式改变：
  - 当前推进是否暂停
  - 当前业务意图是否覆写
  - 当前路由是否转入 review / repair / approval
  - 当前执行是否恢复
- 外部接管不能直接伪造：
  - 完成态
  - verifier 通过结果
  - 证据完备度

### Required Entry Points

- 外部接管入口至少应来自：
  - Web workbench
  - 消息控制面
  - approval 流程
  - 更高优先级 controller / agent

## Relationship To Existing Objects

- `DriverLearningSignal`
  - 来自 `VerifierResult / EvidenceSet / CycleBackfeed / PlatformIncident / ReadinessDecision / BlockerRecord`
- `DriverLearningRecord`
  - 归并多个学习信号，作为下一轮 `AutonomousDrivingInput` 的补充输入
- `TakeoverRequest`
  - 指向 `Program / StoryBatch / RuntimeStory / BusinessOrchestrationState`
- `TakeoverDecision`
  - 影响下一次 `OrchestrationTransition / IntentRequest / DecisionEnvelope`

## Frontend And Message Consequence

- 右栏、review modal、mobile summary 不应只显示“当前状态”。
- 还至少要能表达：
  - 当前 AI 司机意图
  - 最近学习结论
  - 是否存在活动中的接管请求
  - 当前可用的接管动作
- 消息面不应只做只读播报，还应能承接结构化接管提示。

## What This Freeze Changes

- 从现在起，系统不再把 AI 司机理解成：
  - 只会提出当前意图
  - 不吸收历史反馈
  - 不可被外部正式接管
- 更准确的要求应是：
  - AI 司机必须通过结构化学习信号持续修正判断
  - 外部控制面必须保留正式的暂停、覆写、改路由和接管入口

## Implementation Consequence

- 代码阶段至少要补：
  - `DriverLearningSignal` schema
  - `DriverLearningRecord` schema
  - `TakeoverRequest` schema
  - `TakeoverDecision` schema
  - 对应 reducer / API / read model / message projection
- 如果这层不落地，系统很容易再次出现：
  - “AI 司机已经多次犯错，但系统没有正式学习闭环”
  - “明明应该人工接管，却只能靠自由文本喊停”
