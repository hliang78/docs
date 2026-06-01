---
topic: generic-ai-autodev-platform
kind: full-stack
title: 引擎运行内核冻结
createdAt: 2026-05-18T07:35:00+0800
program: true
status: draft
---

# Engine Runtime Kernel Freeze

## Purpose

- 这份文档专门回答一个比“规则怎么写”更底层的问题：
  - 自动驾驶系统的引擎到底怎么真实运转
  - 怎样避免引擎退化成“请求来了，把一堆字段拼起来算一次”
- 这份文档不再讨论名词抽象。
- 它直接冻结运行内核。

## Final Judgment

- 如果引擎只有：
  - `AutonomousDrivingInput`
  - `GuardDecision`
  - `ActionPlan`
  - `DecisionEnvelope`
- 但没有：
  - 持续运行的事件循环
  - 工作内存
  - agenda 调度
  - 命令发射与回执
  - 回流与恢复
- 那它就仍然是空壳。

所以从现在起，自动驾驶系统的真实驱动力必须定义成：

- `event-driven runtime kernel`
- `program-scoped actor loop`
- `persistent working memory`
- `command journal + feedback loop`

一句话：

- 引擎不是一次性计算器，而是一个持续运转的程序级驾驶员内核。

## Runtime Unit

建议每个 `Program` 都有一个独立运行单元：

### `ProgramCycleRuntime`

- 作用：
  - 表示一个 `Program` 的常驻运行时内核实例。
- 它不是 HTTP handler。
- 它也不是某次 API 请求的局部对象。
- 它是一个持续存在、可恢复、可暂停、可接管的 program actor。

## The Real Driving Force

引擎的真实驱动力不是“谁来点按钮”，而是 7 类 wakeup source：

1. `intent event`
2. `execution feedback event`
3. `verifier/evidence event`
4. `incident/probe event`
5. `takeover/approval event`
6. `timer/retry timeout event`
7. `backfeed/acceptance event`

规则：

- 没有事件，不做无意义推进。
- 有事件时，不允许跳过工作内存和 agenda 直接临时判断。

## Runtime Core Components

### 1. `EngineInbox`

- 作用：
  - 接收 program 级所有事件。
- 来源包括：
  - 前端推进请求
  - AI 司机意图变化
  - `dagengine` 执行回执
  - `VerifierResult`
  - `EvidenceSet`
  - `PlatformIncident`
  - `TakeoverRequest`
  - `ComponentEndSignal`
  - timer timeout

### 2. `WorkingMemory`

- 作用：
  - 保存当前 program 的“可决策现实”。
- 它不是数据库全量镜像。
- 它是从对象层抽取出的当前驾驶态内存。

### 3. `AgendaQueue`

- 作用：
  - 保存当前还需要引擎处理的待决项目。
- 示例：
  - `re-evaluate-readiness`
  - `adjudicate-fault`
  - `plan-next-move`
  - `await-human-confirmation`
  - `refresh-decision-rail`

### 4. `RulePipeline`

- 作用：
  - 驱动 `worldstate -> diagnostics -> guards -> planner` 的顺序执行。
- 这里不是任意 callback 链。
- 必须是固定顺序、可追踪的流水线。

### 5. `CommandJournal`

- 作用：
  - 保存已经发出的命令意图和当前状态。
- 没有 journal，就没有真正的执行闭环。

### 6. `LeaseManager`

- 作用：
  - 防止同一 program 同时发出互相冲突的动作。
- 例如：
  - 一个 story 正在 verifier
  - 另一个入口又想 close program
- 必须通过 lease / lock / ownership 明确谁持有当前推进权。

### 7. `FeedbackIngestor`

- 作用：
  - 吸收执行回执与外部世界变化，并重新唤醒引擎。

### 8. `CheckpointStore`

- 作用：
  - 持久化运行时 checkpoint。
- 引擎重启后必须能恢复：
  - inbox offset
  - working memory snapshot
  - pending agenda
  - command journal
  - active leases

## Formal Runtime Contracts

### `EngineEvent`

- 作用：
  - 表示引擎邮箱里的标准事件。
- 至少包含：
  - `engineEventId`
  - `programId`
  - `ownerObjectType`
  - `ownerObjectId`
  - `eventType`
  - `eventSource`
  - `eventPayloadRef`
  - `causedByCommandId`
  - `occurredAt`
  - `dedupeKey`

### `WorkingMemoryFrame`

- 作用：
  - 表示某次循环后 program 的当前工作内存快照。
- 至少包含：
  - `workingMemoryFrameId`
  - `programId`
  - `worldStateSnapshotId`
  - `intentRequestId`
  - `faultDecisionId`
  - `guardDecisionId`
  - `latestLearningRecordId`
  - `latestTakeoverDecisionId`
  - `latestEndSignalEvaluationId`
  - `activeLeaseIds`
  - `frameVersion`
  - `capturedAt`

### `AgendaItem`

- 作用：
  - 表示一项待执行的引擎内部工作。
- 至少包含：
  - `agendaItemId`
  - `programId`
  - `agendaType`
  - `priority`
  - `blocking`
  - `dependsOnAgendaItemIds`
  - `inputRefs`
  - `status`
  - `scheduledAt`

### `CommandIntent`

- 作用：
  - 表示引擎决定发出的一个正式动作意图。
- 至少包含：
  - `commandIntentId`
  - `programId`
  - `actionPlanId`
  - `commandType`
  - `targetAdapter`
  - `payloadRef`
  - `idempotencyKey`
  - `status`
  - `issuedAt`

### `CommandReceipt`

- 作用：
  - 表示执行侧对命令的正式回执。
- 至少包含：
  - `commandReceiptId`
  - `commandIntentId`
  - `receiptType`
  - `resultStatus`
  - `resultRefs`
  - `errorCode`
  - `receivedAt`

### `EngineCheckpoint`

- 作用：
  - 表示可恢复的运行时快照。
- 至少包含：
  - `engineCheckpointId`
  - `programId`
  - `lastConsumedEventId`
  - `workingMemoryFrameId`
  - `pendingAgendaItemIds`
  - `activeCommandIntentIds`
  - `activeLeaseIds`
  - `checkpointAt`

## Runtime Loop

建议固定为下面这条 loop：

```text
event arrives
-> normalize into EngineEvent
-> append to EngineInbox
-> consume event into WorkingMemory
-> enqueue AgendaItem(s)
-> run RulePipeline on top agenda
-> emit FaultDecision / GuardDecision / ActionPlan
-> create CommandIntent(s)
-> acquire lease(s)
-> dispatch to adapter(s)
-> receive CommandReceipt / VerifierResult / Incident / Takeover event
-> ingest feedback
-> refresh WorkingMemoryFrame
-> persist EngineCheckpoint
-> decide next wakeup or sleep
```

## Actor Rule

### Single Decision Writer

- 同一个 `Program` 在同一时刻只能有一个 decision writer。
- 也就是说：
  - 这个 program 的最终裁定只能由一个 `ProgramCycleRuntime` 顺序写出
- 这样才能避免：
  - 两个 handler 同时推进
  - 一个入口在 repair，另一个入口在 accept-and-close

### Async Execution, Serialized Decisions

- 决策可以串行。
- 执行可以异步。
- 这正是“有真实驱动力”而不混乱的关键。

## Wakeup And Sleep Rule

引擎不是一直空转。

它应在两种状态之间切换：

### `awake`

- inbox 有新事件
- timer 到期
- command receipt 返回
- takeover / approval 到达

### `sleeping`

- 没有未消费事件
- 没有待执行 agenda
- 没有超时中的 command
- 没有需要立即重算的 interlock

这意味着：

- 引擎不是定时拼装摘要
- 而是在真正需要时被唤醒

## Command Discipline

### 1. All External Effects Go Through Commands

- 不允许 engine module 直接改外部世界。
- 所有外部动作都必须先变成 `CommandIntent`：
  - 调 `dagengine`
  - 发 takeover 消息
  - 触发 repair
  - 重算 readiness
  - 生成 projection

### 2. Commands Must Be Idempotent

- 否则恢复后会重放出事故。

### 3. No Fire-And-Forget

- 所有命令都要等：
  - receipt
  - timeout
  - explicit retry policy

## Recovery And Restart Rule

真正的引擎必须允许中断后恢复。

所以：

- 重启后先加载 `EngineCheckpoint`
- 恢复 `WorkingMemoryFrame`
- 重新挂起未完成 `CommandIntent`
- 对超时命令重新生成 wakeup event
- 再继续 loop

没有这一步，就不是真引擎，只是在线计算服务。

## Why This Is Not Field Stitching

字段拼装式系统的特征是：

- 请求来了才读字段
- 算一次结果就结束
- 不记住上一轮中间态
- 没有命令账本
- 没有回执闭环
- 重启后靠猜

运行内核式系统的特征是：

- 事件先进入 inbox
- 当前现实先进入 working memory
- 待办先进入 agenda
- 动作先进入 command journal
- 回执再进入 feedback loop
- checkpoint 保证可恢复

## Relationship To Dagengine

- `dagengine/v2/engine` 已经证明事件驱动调度、事件驱动器、重试执行器、持久化恢复这些机制可以作为底盘参考。
- 但自动驾驶系统的高层 runtime kernel 不直接等于 `dagengine`。
- 更准确的关系是：
  - `dagengine`
    - 负责执行图和节点调度
  - `ProgramCycleRuntime`
    - 负责业务级唤醒、诊断、裁定、命令、回流

## Backend Shape Recommendation

建议在 `backend/src/engine/` 下明确增加：

```text
backend/src/engine/
├── runtime/
│   ├── inbox/
│   ├── memory/
│   ├── agenda/
│   ├── leases/
│   ├── journal/
│   ├── checkpoint/
│   └── kernel/
```

职责建议：

- `inbox/`
  - ingest / dedupe / ordering
- `memory/`
  - working memory frame build / update
- `agenda/`
  - internal task scheduling
- `leases/`
  - ownership and conflict control
- `journal/`
  - command intent / receipt log
- `checkpoint/`
  - persistence and recovery
- `kernel/`
  - main actor loop

## First Implementation Slice

如果要让引擎真正“活起来”，第一批最值得落的不是更多 read model，而是：

1. `EngineEvent` inbox
2. `WorkingMemoryFrame`
3. `AgendaItem`
4. `CommandIntent` + `CommandReceipt`
5. `EngineCheckpoint`
6. `ProgramCycleRuntime` main loop

## Freeze Conclusion

- 从现在起，自动驾驶系统的引擎不应再被理解成一个“计算 `DecisionEnvelope` 的函数”。
- 更准确的理解应是：
  - 每个 program 都有一个持续存在的 actor runtime
  - 它靠事件被唤醒
  - 靠 working memory 持有当前现实
  - 靠 agenda 推进内部工作
  - 靠 command journal 驱动外部动作
  - 靠 feedback loop 吸收执行结果
  - 靠 checkpoint 保证中断恢复
- 这样它才有真实驱动力，真实运转，而不是字段拼装壳。
