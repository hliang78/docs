---
topic: generic-ai-autodev-platform
kind: full-stack
title: 自动驾驶引擎工程冻结
createdAt: 2026-05-17T16:00:00+0800
program: true
status: draft
---

# Autonomous Driving Engine Freeze

## Purpose

- 这份文档把 [autonomous-driving-engine-analysis.md](/Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/generic-ai-autodev-platform/autonomous-driving-engine-analysis.md) 从“总抽象判断”推进成“可进入实现切片的工程冻结稿”。
- 面向更低心智负担的解释层，见 [autonomous-driving-engine-concept-mapping.md](/Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/generic-ai-autodev-platform/autonomous-driving-engine-concept-mapping.md)。
- 面向代码级命名，见 [autonomous-driving-engine-code-naming.md](/Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/generic-ai-autodev-platform/autonomous-driving-engine-code-naming.md)。
- 面向复杂故障诊断机制，见 [fault-diagnosis-engine-freeze.md](/Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/generic-ai-autodev-platform/fault-diagnosis-engine-freeze.md)。
- 面向真实运行内核，见 [engine-runtime-kernel-freeze.md](/Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/generic-ai-autodev-platform/engine-runtime-kernel-freeze.md)。
- 目标不是再加新概念，而是正式钉死：
  - 引擎最小输入输出 schema
  - reducer / guard / planner / actuator / backfeed 模块边界
  - 首期声明式规则类型
  - 首期必须支持的动作集

## Final Judgment

- 这台自动驾驶引擎可以驱动自动驾驶系统。
- 原因不是它“概念上好听”，而是这个项目现在已经具备了引擎所需的五层输入材料：
  - `truth/world facts`
  - `business intent`
  - `safety/interlock`
  - `runtime capability`
  - `execution/backfeed`
- 但它当前还只能算“可驱动的架构内核”，不能直接等同于“已可上线运行的代码系统”。
- 缺的已经不再是顶层抽象，而是把这些冻结对象正式收口成：
  - 一个统一引擎入口
  - 一个统一决策输出
  - 一套首期规则与动作 contract

## What The Engine Must Own

- 引擎必须拥有：
  - 统一读取当前结构化事实
  - 统一识别当前业务推进意图
  - 统一评估护栏、interlock 与风险
  - 统一选择下一步动作计划
  - 统一把执行结果回流成下一轮输入
- 引擎不负责：
  - 自己存储所有对象
  - 替代 `dagengine` 执行底层 DAG
  - 替代 PRD 产出规划文档正文
  - 替代前端拼 UI 展示逻辑
  - 让 LLM 临场自由决定全部推进规则

## Engine Runtime Boundary

- `dagengine`
  - 是 actuator kernel
  - 负责执行，不负责高层业务判断
- `Autonomous Driving Engine`
  - 是 high-level decision kernel
  - 负责把事实、意图、护栏、能力、回流转成动作计划
- `planner/control API`
  - 是引擎外壳与对象访问层
  - 负责装配输入快照、持久化输出结果、向前端暴露 projection
- `ProgramCycleRuntime`
  - 是引擎的常驻运行内核
  - 负责 inbox、working memory、agenda、command journal 与 feedback loop

## Minimum Engine Contracts

### `AutonomousDrivingInput`

- 作用：
  - 表示一次引擎评估所需的最小完整输入。
- 至少包含：
  - `evaluationId`
  - `ownerObjectType`
  - `ownerObjectId`
  - `triggerEvent`
  - `worldStateSnapshot`
  - `intentRequest`
  - `runtimeCapabilitySnapshot`
  - `activeInterlocks`
  - `cycleContext`
  - `evaluatedAt`

### `WorldStateSnapshot`

- 作用：
  - 把 truth、verifier、evidence、incident、probe 统一归并成当前世界状态。
- 至少包含：
  - `worldStateSnapshotId`
  - `ownerObjectType`
  - `ownerObjectId`
  - `storyTruthIds`
  - `batchTruthId`
  - `turnTruthId`
  - `repairTruthIds`
  - `verifierResultIds`
  - `evidenceSetIds`
  - `proofCompletenessStatus`
  - `openBlockerIds`
  - `openIncidentIds`
  - `latestPreflightProbeId`
  - `snapshotVersion`
  - `snapshotAt`

### `IntentRequest`

- 作用：
  - 表示业务系统当前请求引擎推进什么。
- 至少包含：
  - `intentRequestId`
  - `ownerObjectType`
  - `ownerObjectId`
  - `businessOrchestrationStateId`
  - `requestedTransitionId`
  - `businessPhase`
  - `businessIntent`
  - `requestedAction`
  - `requestedBy`
  - `requestedAt`

### `RuntimeCapabilitySnapshot`

- 作用：
  - 表示当前动作可使用的执行能力与约束组合。
- 至少包含：
  - `runtimeCapabilitySnapshotId`
  - `runtimeTaskPolicyId`
  - `candidateWorkerProfileIds`
  - `runtimeEnvProfileId`
  - `providerProfileIds`
  - `providerEndpointIds`
  - `harnessBindingIds`
  - `harnessProfileIds`
  - `approvalProfileIds`
  - `quotaStatus`
  - `livenessStatus`
  - `snapshotAt`

### `GuardDecision`

- 作用：
  - 表示护栏层对当前推进意图的正式裁定。
- 至少包含：
  - `guardDecisionId`
  - `ownerObjectType`
  - `ownerObjectId`
  - `decision`
  - `riskLevel`
  - `triggeredGuardRuleIds`
  - `requiredInterlockIds`
  - `blockingReasonCodes`
  - `decisionSummary`
  - `decidedAt`

### `ActionPlan`

- 作用：
  - 表示这次评估最终准备执行的动作计划。
- 至少包含：
  - `actionPlanId`
  - `ownerObjectType`
  - `ownerObjectId`
  - `actionType`
  - `actionPayload`
  - `requiresHumanApproval`
  - `targetLane`
  - `targetWorkerProfileId`
  - `targetHarnessProfileId`
  - `targetProviderProfileId`
  - `expectedOutputs`
  - `plannedAt`

### `BackfeedPlan`

- 作用：
  - 表示动作执行后必须回刷哪些 truth、projection、cycle 对象。
- 至少包含：
  - `backfeedPlanId`
  - `ownerObjectType`
  - `ownerObjectId`
  - `emitCycleBackfeed`
  - `recalcReadiness`
  - `refreshMessageProjection`
  - `refreshReadModelKeys`
  - `nextOrchestrationStateHint`

### `DecisionEnvelope`

- 作用：
  - 作为引擎统一输出，供前端、消息投影、审计日志、read model 共用。
- 至少包含：
  - `decisionEnvelopeId`
  - `evaluationId`
  - `worldStateSnapshot`
  - `intentRequest`
  - `faultDecision`
  - `guardDecision`
  - `requiredInterlocks`
  - `chosenActionPlan`
  - `reasonChain`
  - `diagnosticReasonChain`
  - `emittedCommands`
  - `recoveryRoutePlan`
  - `backfeedPlan`
  - `generatedAt`

## Minimal Reason Chain Rule

- 每个 `DecisionEnvelope.reasonChain` 至少回答：
  1. 当前读取了哪些事实对象
  2. 当前识别出的业务意图是什么
  3. 哪些 guard / interlock 被触发
  4. 为什么得到 `allow / warn / block / escalate`
  5. 最终为什么选择当前动作，而不是其他动作

## Engine Module Boundary

建议后端正式收口为：

```text
backend/src/engine/
├── contracts/
├── worldstate/
├── intent/
├── runtime/
├── diagnostics/
├── guards/
├── planner/
├── actuator/
├── backfeed/
└── projection/
```

### `contracts/`

- 定义：
  - `AutonomousDrivingInput`
  - `WorldStateSnapshot`
  - `RuntimeCapabilitySnapshot`
  - `GuardDecision`
  - `ActionPlan`
  - `BackfeedPlan`
  - `DecisionEnvelope`

### `worldstate/`

- 负责：
  - `StoryTruth / BatchTruth / TurnTruth / RepairTruth`
  - `VerifierResult / EvidenceSet / ProofCompleteness`
  - `BlockerRecord / PlatformIncident / PreflightProbe`
  - 归并成 `WorldStateSnapshot`

### `intent/`

- 负责：
  - `BusinessOrchestrationState`
  - `OrchestrationTransition`
  - `PlanningReview / ReadinessDecision / PRDAcceptanceDecision`
  - 归并成 `IntentRequest`

### `runtime/`

- 负责：
  - `EngineEvent`
  - `WorkingMemoryFrame`
  - `AgendaItem`
  - `CommandIntent / CommandReceipt`
  - `EngineCheckpoint`
  - `ProgramCycleRuntime` 主循环

### `diagnostics/`

- 负责：
  - `DiagnosticFact`
  - `FaultHypothesis`
  - `FaultDecision`
  - `RecoveryRoutePlan`
  - 复杂故障的规则生成、冲突消解与恢复路由

### `guards/`

- 负责：
  - `OrchestrationSafetyGuard`
  - `SafetyInterlock`
  - `ApprovalProfile`
  - 把推进意图裁定为 `allow / warn / block / escalate`

### `planner/`

- 负责：
  - 读取 `GuardDecision + RuntimeCapabilitySnapshot`
  - 选择 `ActionPlan`
  - 禁止业务模块直接绕过 planner 组装执行动作

### `actuator/`

- 负责：
  - 调 `dagengine` compiler / runner
  - 调 repair route
  - 调 readiness recompute
  - 调 message projection refresh
- 不负责：
  - 重新解释业务 intent
  - 自己放宽 safety guard

### `backfeed/`

- 负责：
  - 把执行结果转成：
    - `CycleBackfeed`
    - `NextBusinessStateUpdate`
    - truth refresh 请求

### `projection/`

- 负责：
  - 把 `DecisionEnvelope` 投影成：
    - frontend right-rail summary
    - review banner
    - `MessageProjection`
    - audit/debug trace

## Declarative Rule Families

- 首期只冻结 4 类声明式规则，不再继续扩散散装判断：
  - `state-reduction`
  - `guard`
  - `capability-matching`
  - `loop-progression`

### `state-reduction` Rules

- 用途：
  - 归并 truth，决定当前真实世界状态。
- 首期必须支持：
  - 最新有效 `VerifierResult` 压过 worker 自报完成
  - 最新有效 `StoryTruth` 压过旧 handoff / 旧 report
  - `PlatformIncident` 与 `PreflightProbe` 能直接降低世界状态可执行性
  - `ProofCompleteness` 不足时，世界状态不得宣称 ready

### `guard` Rules

- 用途：
  - 判断业务推进是否允许、安全、需要升级或阻断。
- 首期必须支持：
  - `draft -> reviewed` 缺关键字段时 `block`
  - `reviewed -> publish` readiness 不足时 `block`
  - `blocked -> continue` 但 blocker 属于 repair 类时 `route-to-repair`
  - `story done -> accept-and-close` 时默认 `escalate`
  - 存在关键 `PlatformIncident` 时禁止进入正式执行

### `capability-matching` Rules

- 用途：
  - 决定当前动作应该由谁、在哪种 harness、以什么 provider 组合执行。
- 首期必须支持：
  - story lane 必须匹配 `WorkerProfile`
  - browser / UI proof 必须匹配 browser-capable harness
  - 需要审批的动作必须命中对应 `ApprovalProfile`
  - `RuntimeTaskPolicy` 不允许的写路径不能进入 execution pack
  - quota / liveness 不满足时不得分配正式执行动作

### `loop-progression` Rules

- 用途：
  - 决定执行结果如何回流到 planning plane 和下一轮业务编排状态。
- 首期必须支持：
  - proof 不足时优先 `recalc-readiness` 或 `blocked-human-confirmation`
  - planning gap 明确时进入 `draft-next-batch`
  - infra blocker 明确时进入 `route-to-repair`
  - 只有 `PRDAcceptanceDecision = accept-and-close` 才允许 `close-program`
  - 单轮 execution 成功不能自动结束 program

## First-Phase Action Set

- 首期引擎必须至少支持以下动作：
  - `recalc-readiness`
  - `request-human-confirmation`
  - `request-approval`
  - `compile-execution-pack`
  - `dispatch-execution-pack`
  - `route-to-repair`
  - `emit-message-projection`
  - `emit-cycle-backfeed`
  - `draft-next-batch`
  - `update-orchestration-state`
  - `accept-and-close`
  - `stop-program`

## Command Routing Rule

- `ActionPlan` 只描述“做什么”，不直接内嵌底层实现细节。
- 首期动作路由固定为：
  - `compile-execution-pack` -> `backend/src/adapters/dagengine/compiler`
  - `dispatch-execution-pack` -> `backend/src/adapters/dagengine/runner`
  - `route-to-repair` -> repair / super-repair adapter
  - `emit-message-projection` -> message projection adapter
  - `emit-cycle-backfeed` -> planning plane backfeed adapter
  - `recalc-readiness` -> readiness reducer

## Minimum Runtime Loop

```text
trigger event
-> gather truth and policy inputs
-> update working memory and agenda
-> build AutonomousDrivingInput
-> diagnostics adjudication if needed
-> worldstate reducers build WorldStateSnapshot
-> intent derivation builds IntentRequest
-> guard evaluation builds GuardDecision
-> planner selects ActionPlan
-> actuator dispatches commands
-> command receipts return into inbox
-> backfeed emits CycleBackfeed and next orchestration hint
-> projection refreshes frontend/message summaries
```

## Frontend Consequence

- 前端首期不应该自己拼控制逻辑。
- 前端应主要读取：
  - `DecisionEnvelope` 投影摘要
  - `ReadinessSummaryProjection`
  - `BusinessOrchestrationState`
  - `OrchestrationSafetyGuard`
  - `SafetyInterlock`
- 这样右栏、review modal、result banner 看到的是同一条 reason chain，而不是多个 badge 的脑补组合。

## First Implementation Slice

- 代码阶段第一批最值得先落的，不是完整执行器，而是引擎壳层最小闭环：
  1. `runtime` inbox + checkpoint
  2. `WorkingMemoryFrame`
  3. `worldstate` reducer
  4. `diagnostics` adjudicator
  5. `guards` evaluator
  6. `planner` 的首批动作选择
  7. `DecisionEnvelope` read model
- 这样做的价值是：
  - 先把“怎么判断下一步”固定
  - 再让 `dagengine`、repair、message、frontend 都接到这根统一主轴上

## What This Freeze Changes

- 从现在起，自动驾驶系统不应再被实现成：
  - 多个 controller 各自推进状态
  - 多个 handler 各自判断 readiness
  - 前端自己脑补 why blocked / why allowed
  - `dagengine` 反向承担业务判断
- 更准确的实现要求应是：
  - 所有关键推进都经由统一引擎输入
  - 所有关键裁定都形成 `DecisionEnvelope`
  - 所有下一步执行都来自 `ActionPlan`
  - 所有循环回流都经由 `BackfeedPlan / CycleBackfeed`

## Immediate Next Step

- 进入代码前，最合理的下一步已经从“继续补抽象”切换成：
  - 基于这份冻结稿定义首批后端 schema / reducer / planner API slice
  - 同时把前端右栏与 batch 审核区明确绑定到 `DecisionEnvelope` 与 `ReadinessSummaryProjection`
