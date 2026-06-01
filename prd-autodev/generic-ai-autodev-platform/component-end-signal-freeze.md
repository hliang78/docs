---
topic: generic-ai-autodev-platform
kind: full-stack
title: 组件结束信号冻结
createdAt: 2026-05-18T04:55:00+0800
program: true
status: draft
---

# Component End Signal Freeze

## Purpose

- 这份文档冻结一个容易被低估、但对多环节系统极其关键的机制：
  - 每个组件工作的结束信号。
- 在自动辅助驾驶系统 + AI 司机模型里，真正危险的不是“组件没结束”，
- 而是：
  - 组件已经结束，但结束语义不清
  - 局部结束信号被误放大成全局完成
  - 旧 handoff、旧 report、旧 done 文案继续污染新一轮判断

## Core Rule

1. 每个组件都必须发出结构化结束信号，不能只留 prose。
2. 局部结束信号只代表本组件结束，不自动代表上层闭环结束。
3. 结束信号必须携带证据来源、影响范围和下一步建议。
4. 只有更高 authority 的结束决策，才能放大或覆盖下层结束信号。

## Why This Must Be Formal

- `worker says done` 不是 story close。
- `verifier passed` 不是 program acceptance。
- `repair done` 不是 execution automatically resume。
- `takeover applied` 不是问题已经闭环。
- `readiness ready-for-openclaw` 不是整个 program 终止。
- 所以系统必须显式区分：
  - 谁结束了
  - 结束了什么
  - 这个结束信号的 authority 到哪一层为止

## Formal Objects

### `ComponentEndSignal`

- 作用：
  - 表示某个组件完成当前工作后的结构化结束信号。
- 至少包含：
  - `componentEndSignalId`
  - `ownerObjectType`
  - `ownerObjectId`
  - `sourceComponentType`
  - `sourceComponentId`
  - `signalType`
  - `signalStatus`
  - `signalScope`
  - `evidenceRefs`
  - `nextSuggestedRoute`
  - `authorityLevel`
  - `emittedAt`

### `EndSignalEvaluation`

- 作用：
  - 表示系统对某个结束信号的正式采纳或拒绝结果。
- 至少包含：
  - `endSignalEvaluationId`
  - `linkedComponentEndSignalId`
  - `decision`
  - `acceptedAs`
  - `rejectedReason`
  - `effectiveRoute`
  - `evaluatedAt`

### `EndSignalProjection`

- 作用：
  - 表示给前端右栏、消息面、审阅面板看的结束信号摘要。
- 至少包含：
  - `ownerObjectType`
  - `ownerObjectId`
  - `latestSignalType`
  - `latestSignalStatus`
  - `latestSignalScope`
  - `latestSignalSummary`
  - `nextSuggestedRoute`
  - `updatedAt`

## Signal Type Set

建议首批至少冻结：

- `worker-finished`
- `worker-blocked`
- `repair-finished`
- `repair-blocked`
- `verifier-finished`
- `readiness-issued`
- `takeover-applied`
- `acceptance-issued`
- `controller-stopped`

## Authority Hierarchy

结束信号必须分层，不允许同权混跑。

1. `worker-finished`
   - 只能说明 worker 当前执行结束
2. `verifier-finished`
   - 只能说明验证动作结束并给出 verdict
3. `repair-finished`
   - 只能说明 repair 流程当前阶段结束
4. `readiness-issued`
   - 只能说明 readiness gate 已正式计算
5. `takeover-applied`
   - 可以改变当前推进路由和控制权
6. `acceptance-issued`
   - 只有这一层有资格终止整个 program loop

一句话：

- 下层可以结束自己的工作，
- 上层才有资格结束更大的闭环。

## Component Semantics

### Worker End Signal

- 最低语义：
  - 当前 execution pack 已完成一次执行
  - 已提交 patch/report/evidence candidate/self-assessment
- 不得自动表示：
  - `RuntimeStory = done`
  - `StoryBatch = completed`
  - `Program = closed`

### Verifier End Signal

- 最低语义：
  - 当前验证动作执行结束
  - 已产出 `VerifierResult`
- 不得自动表示：
  - proof completeness 已足够
  - acceptance 已满足

### Repair End Signal

- 最低语义：
  - 当前 repair 运行已结束或暂停
  - 已给出是否可 rerun 的建议
- 不得自动表示：
  - story 已恢复为 done
  - 原 blocker 已自动关闭

### Readiness End Signal

- 最低语义：
  - `ReadinessDecision` 已正式签发
- 不得自动表示：
  - execution 已开始
  - program 已完成

### Takeover End Signal

- 最低语义：
  - 接管请求已经被应用、拒绝或过期
- 允许影响：
  - 当前 intent
  - 当前 route
  - 当前是否暂停
- 不得自动表示：
  - 当前对象已 closure

### Acceptance End Signal

- 最低语义：
  - `PRDAcceptanceDecision` 已正式给出
- 这是唯一可以结束整个 program loop 的结束信号。

## Evaluation Rule

1. 所有结束信号都必须先进入 `EndSignalEvaluation`。
2. `worker-finished` 若无 verifier/evidence，不得被接受为 `story-done`。
3. `verifier-finished` 若 proof insufficient，不得被接受为 `closure-ready`。
4. `repair-finished` 若 blocker rerun 未完成，不得被接受为 `resume-execution`。
5. `acceptance-issued = accept-and-close` 才能被接受为 `program-closed`。

## Relationship To Existing Objects

- `ComponentEndSignal`
  - 来自 `Worker / Verifier / Repair / Readiness / Takeover / Acceptance`
- `EndSignalEvaluation`
  - 影响 `DecisionEnvelope / ReadinessDecision / BusinessOrchestrationState`
- `EndSignalProjection`
  - 进入 `DecisionRailView / MessageProjection / Batch summary`

## Frontend Consequence

- 右栏和消息面不应只显示：
  - done
  - blocked
  - ready
- 还必须能表达：
  - 最近是谁结束了什么
  - 这个结束信号只到哪一层
  - 当前系统是否已正式采纳
  - 下一步应去 review / rerun / repair / accept

## What This Freeze Changes

- 从现在起，系统不再把“结束”理解成一个模糊词。
- 更准确的要求应是：
  - 每个组件结束时发 `ComponentEndSignal`
  - 系统再通过 `EndSignalEvaluation` 决定是否放大为更高层结束态
  - 最终只有 `acceptance-issued` 能终止 program loop

## Implementation Consequence

- 首批实现至少要补：
  - `ComponentEndSignal` schema
  - `EndSignalEvaluation` schema
  - `EndSignalProjection` read model
- 如果这层不落地，系统很容易再次出现：
  - “局部执行结束被误当全局完成”
  - “旧结束文案继续压过新一轮真实状态”
