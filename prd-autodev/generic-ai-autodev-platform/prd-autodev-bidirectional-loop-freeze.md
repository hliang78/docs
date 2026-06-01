---
topic: generic-ai-autodev-platform
kind: full-stack
title: PRD 与 AutoDev 双向自动循环冻结
createdAt: 2026-05-18T02:05:00+0800
program: true
status: draft
---

# PRD AutoDev Bidirectional Loop Freeze

## Purpose

- 这份文档冻结一个此前没有被明确钉死的核心目标：
  - 自动驾驶系统不是“PRD 先产出一次，AutoDev 执行一次，然后人工再决定怎么办”。
  - 核心目标必须是：`PRD planning plane <-> autodev execution plane` 直接双向自动循环。
- 同时明确最终终止权：
  - 最终不是由 worker、repair、controller 或单个 batch 自己宣布循环结束。
  - 最终必须由 `PRD` 基于结构化 evidence 做验收，并终止循环。

## Core Principle

1. `PRD` 不是静态文档集合，而是持续接收执行反馈、修订批次、判断继续还是终止的 planning authority。
2. `AutoDev` 不是一次性消费 PRD 的下游执行器，而是持续向 PRD 回传真实结果、blocker、evidence、verifier 的 execution authority。
3. 自动驾驶系统的目标不是“reviewed PRD -> 一次执行”，而是“reviewed PRD -> 自动执行 -> evidence backfeed -> PRD 决策 -> 下一轮自动执行”。
4. 终止循环只能由 PRD/planning plane 产生正式 acceptance decision。
5. 任何局部组件结束信号都不能直接终止整个循环。

## Formal Objects

### `ProgramCycle`

- 作用：
  - 表示一个 program 当前所处的自动循环阶段。
- 至少包含：
  - `programCycleId`
  - `programId`
  - `currentRound`
  - `entryBatchId`
  - `status`
  - `activeReadinessDecisionId`
  - `activeAcceptanceDecisionId`
  - `updatedAt`

### `CycleBackfeed`

- 作用：
  - 表示 execution plane 回流到 planning plane 的结构化反馈包。
- 至少包含：
  - `cycleBackfeedId`
  - `programId`
  - `storyBatchId`
  - `sourceBatchTruthId`
  - `sourceStoryTruthIds`
  - `sourceVerifierResultIds`
  - `sourceEvidenceSetIds`
  - `sourceBlockerRecordIds`
  - `sourceIncidentIds`
  - `backfeedType`
  - `createdAt`

### `PRDAcceptanceDecision`

- 作用：
  - 表示 PRD/planning plane 对当前循环轮次给出的正式验收结论。
- 至少包含：
  - `prdAcceptanceDecisionId`
  - `programId`
  - `storyBatchId`
  - `status`
  - `decisionReason`
  - `acceptedScope`
  - `remainingGaps`
  - `nextAction`
  - `decidedAt`

## Loop Semantics

### Forward Loop

```text
PRD / planning review
-> StoryBatch reviewed
-> ReadinessDecision says ready-for-openclaw
-> RuntimeStory / ExecutionPack compile
-> AutoDev executes
-> verifier / evidence / blocker / incident produced
```

### Backward Loop

```text
execution truth + verifier + evidence + blockers
-> CycleBackfeed
-> PRD reads structured backfeed
-> PRDAcceptanceDecision
-> choose:
   - draft next batch
   - promote next batch
   - revise PRD / acceptance / scope
   - close program
   - stop program
```

## Acceptance And Termination Rule

### What Can End A Story

- `RuntimeStory` 可以进入 `done`。
- `RepairRun` 可以进入 `done`。
- `StoryBatch` 可以进入 `completed` 或 `reviewed next step ready`。

### What Cannot End The Whole Loop

- worker footer
- 单次 verifier 通过
- 单次 batch 完成
- 单次 repair 完成
- 前端上一个绿色 badge
- 任意局部 `ComponentEndSignal`

### What Can End The Loop

- 只有 `PRDAcceptanceDecision` 明确判定：
  - 当前 program 的 acceptance 已满足
  - 没有必须继续推进的 remaining gaps
  - 当前可以 `close program`

## Status Set

### `ProgramCycle.status`

- `planning`
- `execution-ready`
- `executing`
- `backfeed-review`
- `next-batch-drafting`
- `accepted`
- `stopped`

### `PRDAcceptanceDecision.status`

- `continue`
- `revise-prd`
- `draft-next-batch`
- `promote-next-batch`
- `accept-and-close`
- `stop`

## Routing Rules

1. execution plane 的所有结果不能直接改写 PRD 结论，必须通过 `CycleBackfeed` 回流。
2. `environment.* / provider.* / process.*` blocker 默认仍走 repair，不自动回流 PRD 改 scope。
3. 只有 planning-relevant 信号才有资格改变 PRD：
   - acceptance 缺失
   - scope 不准
   - batch 切片不合理
   - business proof 不成立
4. PRD 接受 backfeed 后，必须产出新的结构化决策，而不是留在 prose 里。

## Relationship To Existing Objects

- `PlanningReview`
  - 负责 reviewed planning slice 的进入条件。
- `ReadinessDecision`
  - 负责回答某个 batch 是否 ready-for-openclaw。
- `BatchTruth / StoryTruth`
  - 负责 execution 真实结果。
- `EvidenceSet / VerifierResult / ProofCompleteness`
  - 负责 PRD 做 acceptance 时的证据基础。
- `ProgramCycle`
  - 负责把规划和执行串成真正的多轮循环。
- `PRDAcceptanceDecision`
  - 负责最终关闭循环。

## What This Freeze Changes

- 自动驾驶系统的终极目标不再只是“生成 reviewed PRD/batch 再开工”。
- 更准确的目标应是：
  - 让 PRD 与 AutoDev 形成直接双向自动循环；
  - 并由 PRD 依据结构化证据来验收和终止循环。

## Implementation Consequence

- 代码阶段必须给 planning plane 留出 backfeed 和 acceptance 的正式 schema/API。
- `cycle-control.json` 只能作为迁移参考，不能继续承担主循环真相。
- 前端工作台后续必须支持：
  - 看当前循环轮次
  - 看 execution backfeed
  - 看 PRD acceptance decision
  - 看为何继续 / 为何关闭
  - 看最近局部结束信号为何没有被放大成全局结束
