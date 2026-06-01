---
topic: generic-ai-autodev-platform
kind: full-stack
title: 业务编排状态一等公民与安全护栏冻结
createdAt: 2026-05-18T03:05:00+0800
program: true
status: draft
---

# Business Orchestration State First-Class Freeze

## Purpose

- 这份文档冻结两个必须同时成立的原则：
  - 业务编排状态必须是一等公民。
  - 业务编排状态不能被无护栏地直接驱动执行。
- 更直白地说：
  - 业务系统像一个 AI 司机，具备高度自主决策能力。
  - 平台还必须像自动辅助驾驶系统一样，在关键时刻做约束、纠偏、拦截，避免严重事故。

## Why This Must Be Formal

- 从历史会话看，很多事故不是 runtime 先坏，而是业务编排状态先给出了危险信号：
  - 还没 reviewed 就被当成可发布
  - blocked 被错路由回 PRD 或被误当 done
  - 单个 story done 被误当 program close
  - 旧 handoff/旧 report 压过当前业务状态
- 这些都说明：
  - 业务编排状态不是 UI badge。
  - 它既是自动化的控制输入，也是最需要安全护栏的上层决策面。

## Core Analogy

### Business System As Driver

- 业务编排层负责：
  - 决定目标
  - 决定当前要推进哪个 batch/story
  - 决定何时 reviewed、何时 ready、何时 accept、何时 close
- 这层必须保留较高自治性，否则平台只会变成人工按钮集。
- 但这里的“司机”更准确地说是 AI 司机，不是固定的人类点击者。
- 所以系统不能只考虑“司机能不能开”，还必须考虑：
  - AI 司机如何学习上一轮结果
  - 外部如何在必要时接管 AI 司机

### Safety Guard As ADAS

- 平台控制层必须额外提供护栏：
  - 对危险状态迁移做拦截
  - 对不完整输入做降级或阻断
  - 对高风险关闭/发布做二次确认
  - 对“看起来可以继续，其实证据不足”的场景做强约束
- 也就是说：
  - 平台不是替业务系统做决策
  - 但平台必须防止业务系统做出高代价错误决策

## Two Extra Channels

### Learning Channel

- AI 司机必须持续吸收：
  - verifier 结果
  - evidence 完备度
  - backfeed 结论
  - acceptance 结论
  - incident 历史
- 否则业务编排状态就只是在重复表达意图，而不是基于反馈逐轮进化。

### External Takeover Channel

- 当 AI 司机给出高风险推进、错误路由或持续误判时，
- 系统必须允许 external human / controller 接管：
  - 暂停当前 transition
  - 覆写 business intent
  - 强制转 repair / approval / review
  - 直接阻断继续执行

## Formal Objects

### `BusinessOrchestrationState`

- 作用：
  - 表示当前 program/batch/story 在业务编排层的正式状态，不是单个字段，而是可查询、可归并、可做护栏判断的对象。
- 至少包含：
  - `businessOrchestrationStateId`
  - `ownerObjectType`
  - `ownerObjectId`
  - `businessPhase`
  - `businessIntent`
  - `allowedNextActions`
  - `currentRiskLevel`
  - `linkedPlanningReviewId`
  - `linkedReadinessDecisionId`
  - `linkedAcceptanceDecisionId`
  - `updatedAt`

### `OrchestrationTransition`

- 作用：
  - 表示业务层请求发生的一次关键状态推进。
- 至少包含：
  - `orchestrationTransitionId`
  - `ownerObjectType`
  - `ownerObjectId`
  - `fromState`
  - `toState`
  - `requestedAction`
  - `requestedBy`
  - `requestedAt`
  - `reason`

### `OrchestrationSafetyGuard`

- 作用：
  - 表示类似自动辅助驾驶的约束层，对关键状态推进做 allow/warn/block/escalate 判断。
- 至少包含：
  - `orchestrationSafetyGuardId`
  - `guardType`
  - `ownerObjectType`
  - `ownerObjectId`
  - `evaluatedTransitionId`
  - `decision`
  - `riskReasons`
  - `requiredInterlocks`
  - `evaluatedAt`

### `SafetyInterlock`

- 作用：
  - 表示某次危险推进前必须满足的强约束。
- 至少包含：
  - `safetyInterlockId`
  - `interlockType`
  - `ownerObjectType`
  - `ownerObjectId`
  - `status`
  - `satisfiedBy`
  - `checkedAt`
- 常见类型：
  - `review-required`
  - `readiness-required`
  - `evidence-required`
  - `approval-required`
  - `no-open-incident-required`
  - `no-route-conflict-required`

## What Counts As Dangerous Decisions

以下都属于“业务系统有可能自己做出，但平台必须拦住”的危险决定：

1. `draft -> reviewed`，但缺关键字段、依赖、lane、validation。
2. `reviewed -> publish`，但 readiness 仍未满足。
3. `blocked -> continue`，但 blocker 实际应走 repair/approval。
4. `worker says done -> close batch`，但 verifier/evidence 不足。
5. `single story done -> accept-and-close`，但 program 级 acceptance 未满足。
6. `old handoff / old report -> override current orchestration state`。

## Guard Rules

### Rule 1

- 业务编排状态可以提出推进意图，但不能绕过护栏直接推进执行。

### Rule 2

- 任何关键推进都必须经过 `OrchestrationTransition` + `OrchestrationSafetyGuard`。

### Rule 3

- `allow` 以外至少要支持：
  - `warn`
  - `block`
  - `escalate`

### Rule 4

- `warn` 不能自动等同于继续执行；是否放行必须有明确定义。

### Rule 5

- `block` 必须给出结构化原因，不能只返一句 prose。

### Rule 6

- `escalate` 默认进入 human / approval / PRD acceptance，而不是 silent fail。

### Rule 7

- 关键状态推进必须保留外部接管入口，不能只允许 AI 司机单向推进。

## Relationship To Existing Objects

- `PlanningReview`
  - 决定业务编排是否具备 reviewed 前提。
- `ReadinessDecision`
  - 决定是否具备进入 OpenClaw 的执行前提。
- `PRDAcceptanceDecision`
  - 决定是否具备终止循环的最终前提。
- `BlockerRecord`
  - 决定某些推进是否应被改路由。
- `VerifierResult / EvidenceSet / ProofCompleteness`
  - 决定 “done / accept / close” 是否真的成立。
- `BusinessOrchestrationState`
  - 把这些业务信号提升为统一控制输入。
- `OrchestrationSafetyGuard`
  - 对这些信号做自动辅助驾驶式拦截与纠偏。

## State Semantics

### `BusinessOrchestrationState.businessPhase`

- `planning`
- `batch-review`
- `ready-check`
- `execution`
- `backfeed-review`
- `acceptance`
- `closed`
- `stopped`

### `OrchestrationSafetyGuard.decision`

- `allow`
- `warn`
- `block`
- `escalate`

## Frontend And Human Ops Consequence

- 前端右栏、result banner、review modal、batch 审核摘要，不应只展示“当前状态”。
- 还必须能展示：
  - 当前业务推进意图
  - 当前护栏判断
  - 当前缺的 interlock
  - 当前为什么被 block / warn / escalate
- 这样人看到的就不是一个孤立 badge，而是“司机 + 辅助驾驶”共同给出的当前控制结论。

## What This Freeze Changes

- 自动驾驶系统不再把业务编排状态理解成：
  - metadata
  - 文档标签
  - 展示用字段
- 更准确的理解应是：
  - 业务编排状态是自动化控制输入的一等公民；
  - 但它必须被 `OrchestrationSafetyGuard` 约束，避免严重事故。

## Implementation Consequence

- 代码阶段至少要补：
  - `BusinessOrchestrationState` schema
  - `OrchestrationTransition` schema
  - `OrchestrationSafetyGuard` schema
  - `SafetyInterlock` schema
  - 对应 reducer / API / read model
- 如果这层不落地，平台很容易再次出现：
  - “业务状态看起来合理，但自动化被错误放行”
  - “业务状态看起来能继续，但其实应该被护栏拦下”
