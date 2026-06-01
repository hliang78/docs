---
topic: generic-ai-autodev-platform
kind: full-stack
title: 引擎驱动覆盖矩阵
createdAt: 2026-05-18T08:05:00+0800
program: true
status: draft
---

# Engine Drive Coverage Matrix

## Purpose

- 这份文档专门回答：
  - 当前所有正式概念，是否都能被引擎真实驱动
  - 哪些概念应由引擎直接拥有
  - 哪些概念应被引擎消费、裁定、派发、回流
  - 哪些概念明确不该被 runtime 直接拥有

## Core Rule

- “引擎能驱动所有概念”不等于“引擎直接拥有所有概念”。
- 更准确的分层应是：
  - `upstream source`
  - `engine-owned runtime state`
  - `engine-derived decision`
  - `engine-dispatched command target`
  - `engine-emitted feedback/projection`

如果一个概念既不是输入、也不是内态、也不是决策、也不是命令目标、也不是回流投影，
那它就是未被真实驱动的空挂对象。

## Drive Classes

| 驱动分类 | 含义 |
|---|---|
| `upstream-only` | 由 human/planner/external world 产生，引擎只消费，不直接拥有 |
| `runtime-owned` | 由 `ProgramCycleRuntime` 持续维护，是引擎真实运转的一部分 |
| `decision-derived` | 由引擎根据 working memory 和规则管线推导得出 |
| `command-target` | 由引擎发命令驱动其变化或生成 |
| `feedback-derived` | 由执行/验证/事故/接管回流后形成 |
| `projection-only` | 只用于前端/消息/审计，不反向拥有业务真相 |

## Planning Plane Coverage

| 概念 | 驱动分类 | 引擎如何驱动 | 说明 |
|---|---|---|---|
| `Program` | `upstream-only` | 作为 program actor 的宿主 id 被 runtime 绑定 | 引擎不创建 program，但每个 program 必须拥有一个 `ProgramCycleRuntime` |
| `QuestionRound` | `upstream-only` | 仅作为规划输入被消费 | 由 planner/human 主导，不由 runtime 自动生成 |
| `ContextBrief` | `upstream-only` | 进入 intent/world 上下文 | 不是 runtime 内态 |
| `Workstream` | `upstream-only` | 作为 batch/story 编排边界被消费 | 引擎不直接调度 workstream 本体 |
| `TestMatrix` | `upstream-only` | 影响 verifier/expected outputs | 不由 runtime 直接拥有 |
| `StoryBatch` | `upstream-only` + `command-target` | 被 runtime 读取，并通过动作推进其后续执行 | 引擎不生成 batch 正文，但会驱动 batch 进入执行相关阶段 |
| `PlanningReview` | `upstream-only` | 作为 readiness / intent 输入 | 不是引擎常驻内态 |
| `ProgramCycle` | `runtime-owned` | 由 `ProgramCycleRuntime` 持续推进轮次与阶段 | 是 program actor 的主节拍对象 |
| `CycleBackfeed` | `feedback-derived` | 由 command receipt / verifier / evidence 回流后生成 | 反向驱动下一轮 agenda |
| `PRDAcceptanceDecision` | `upstream-only` + `feedback-derived` | 由 backfeed 唤醒并作为 close/continue 终止权输入 | acceptance 不应被局部执行自动冒充 |
| `BusinessOrchestrationState` | `runtime-owned` | 由 runtime 持续维护当前推进意图与阶段 | 是 AI 司机意图层常驻状态 |
| `OrchestrationTransition` | `decision-derived` | 由 event + learning/takeover/backfeed 推导下一跳意图 | 不是自由文本 |
| `OrchestrationSafetyGuard` | `decision-derived` | 被 diagnostics/guards 持续读取与更新 | 是引擎规则的一部分 |
| `SafetyInterlock` | `decision-derived` | 由 guard 管线触发、校验、阻断 | 必须进入 runtime wakeup/agenda 体系 |

## Control Plane Coverage

| 概念 | 驱动分类 | 引擎如何驱动 | 说明 |
|---|---|---|---|
| `RuntimeTaskPolicy` | `upstream-only` + `decision-derived` | 被 capability matching 消费，并可被 learning 影响偏好 | 不是 handler 临时字段 |
| `RuntimeStory` | `command-target` | 由 agenda 选择、命令派发、回执更新 | runtime 不应直接跳过 story 生命周期 |
| `ExecutionPack` | `command-target` | 由 planner/command pipeline 编译与派发 | 是命令目标，不是静态文档 |
| `WorkerProfile` | `upstream-only` | 进入 capability snapshot 与 target selection | 不由 runtime 动态生成 |
| `ProviderProfile` | `upstream-only` | 进入 capability snapshot | 参与路由，不参与真相归并 |
| `ProviderEndpoint` | `upstream-only` | 被 command routing 选择 | 由 runtime 消费 |
| `HarnessBinding` | `upstream-only` | 进入 adapter target 选择 | 由 runtime 消费 |
| `HarnessProfile` | `upstream-only` | 进入 command target 选择与 output contract 校验 | 不由 runtime 拥有 |
| `HarnessSessionPolicy` | `upstream-only` | 影响 command/receipt 生命周期 | 是运行时策略输入 |
| `HarnessContextPolicy` | `upstream-only` | 影响 command payload 注入 | 是运行时策略输入 |
| `HarnessOutputContract` | `upstream-only` | 影响 receipt / verifier ingest 解析 | 是回流解析输入 |
| `QuotaPolicy` | `upstream-only` | 影响 capability/fault 判断 | 不满足时唤醒 diagnostics |
| `TimeoutPolicy` | `upstream-only` | 产生 timer wakeup event | 必须进入 runtime timer 通道 |
| `LivenessPolicy` | `upstream-only` | 产生 liveness/incident event | 必须进入 diagnostics |
| `WorkspaceProfile` | `upstream-only` | 约束 command target 范围 | 由 runtime 消费 |
| `ToolchainProfile` | `upstream-only` | 影响 capability matching | 由 runtime 消费 |
| `CredentialBinding` | `upstream-only` | 影响 command payload / endpoint access | 由 runtime 消费 |
| `RuntimeEnvProfile` | `upstream-only` | 进入 capability snapshot | 是执行环境输入 |
| `PreflightProbe` | `feedback-derived` | 由 runtime 触发 probe，回执进入 diagnostics | 会改变 wakeup/agenda |
| `ApprovalProfile` | `upstream-only` + `decision-derived` | 由 guards 和 takeover/approval route 消费 | 不应只停留在 UI 文案 |
| `DriverLearningSignal` | `feedback-derived` | 由 verifier/evidence/backfeed/incident 等事件产生 | 必须通过 event ingest 进入 runtime |
| `DriverLearningRecord` | `runtime-owned` | 由 runtime 周期归并学习信号 | 是 AI 司机记忆的一部分 |
| `ComponentEndSignal` | `feedback-derived` | 由 worker/verifier/repair/readiness/takeover/acceptance 回流产生 | 必须进入 inbox |
| `EndSignalEvaluation` | `decision-derived` | 由 runtime adjudication 采纳/拒绝 | 不应被前端自己放大 |
| `TurnHandoff` | `feedback-derived` | 作为执行结果事件被 ingest | 不是最终真相 |
| `EvidenceSet` | `feedback-derived` | 由 command receipt / verifier 结果回流形成 | 进入 worldstate/diagnostics |
| `VerifierResult` | `feedback-derived` | 由执行回执或 verifier 通道回流形成 | 强驱动 diagnostics |
| `ProofCompleteness` | `decision-derived` | 由 verifier/evidence reducer 归并形成 | 是故障与 readiness 的核心动力 |
| `BlockerRecord` | `feedback-derived` | 由 runtime story / repair / verifier 事件生成 | 进入 fault 假设 |
| `PlatformIncident` | `feedback-derived` | 由 blocker/probe/liveness/timeout 回流形成 | 直接唤醒 repair/takeover 路由 |
| `RepairRun` | `command-target` + `feedback-derived` | 由 runtime 发 repair 命令并接收回执 | 是恢复路线的一部分 |
| `TakeoverRequest` | `upstream-only` + `feedback-derived` | 由 human/message/external controller 进入 inbox | 不是 runtime 自创对象 |
| `TakeoverDecision` | `decision-derived` | 由 runtime 对接管请求裁定形成 | 回写 orchestration 与 rail |
| `ReadinessDecision` | `decision-derived` | 由 worldstate/diagnostics/end-signal/backfeed 归并形成 | 不应由页面 badge 伪造 |
| `EndSignalProjection` | `projection-only` | 由 end-signal evaluation 投影形成 | 不反向拥有真相 |
| `MessageProjection` | `projection-only` | 由 decision/backfeed/readiness/takeover 投影形成 | 只作为外部控制面导出 |

## Truth Plane Coverage

| 概念 | 驱动分类 | 引擎如何驱动 | 说明 |
|---|---|---|---|
| `StoryTruth` | `feedback-derived` | 由 worker/verifier/blocker/receipt 通过 reducer 更新 | 真相必须被回流驱动 |
| `BatchTruth` | `feedback-derived` | 由 story truth / review / release gate reducer 更新 | 不是前端拼出来的摘要 |
| `TurnTruth` | `feedback-derived` | 由 command intent/receipt/handoff/retry 更新 | 是 runtime 层最近执行真实态 |
| `TaskTruth` | `feedback-derived` | 由 runtime task/adapter 回执归并 | 保持执行细粒度真相 |
| `RepairTruth` | `feedback-derived` | 由 repair run 回执归并 | 是 repair plane 真相 |

## Engine Layer Coverage

| 概念 | 驱动分类 | 引擎如何驱动 | 说明 |
|---|---|---|---|
| `AutonomousDrivingInput` | `runtime-owned` | 由 working memory + top agenda 装配 | 不是 request-time 拼装体 |
| `WorldStateSnapshot` | `decision-derived` | 由 truth/evidence/incident/probe reducers 生成 | 是 runtime 当前现实 |
| `IntentRequest` | `decision-derived` | 由 orchestration + learning + takeover + backfeed 推导 | 是 AI 司机这轮意图 |
| `RuntimeCapabilitySnapshot` | `decision-derived` | 由 policy/profile/env/provider/harness 聚合形成 | 是 planner 选择动作的能力图 |
| `FaultDecision` | `decision-derived` | 由 diagnostics 规则、冲突消解、dominance order 生成 | 不是 guard 自己猜 |
| `GuardDecision` | `decision-derived` | 读取 `FaultDecision`、interlock、approval profile 形成裁定 | 是推进裁决层 |
| `ActionPlan` | `decision-derived` | 由 planner 基于 guard + capability + lease 选择 | 是下一步驱动动作 |
| `BackfeedPlan` | `decision-derived` | 由 planner/action 完成后决定回刷项 | 驱动循环闭环 |
| `DecisionEnvelope` | `decision-derived` | 汇总当前 runtime 的正式裁定输出 | 是统一决策卡，不是日志 |

## Runtime Kernel Coverage

| 概念 | 驱动分类 | 引擎如何驱动 | 说明 |
|---|---|---|---|
| `ProgramCycleRuntime` | `runtime-owned` | program actor 常驻运行 | 是引擎真实本体 |
| `EngineEvent` | `runtime-owned` | 所有 wakeup source 统一标准化进入 inbox | 没有它就没有真实驱动力 |
| `WorkingMemoryFrame` | `runtime-owned` | 每轮 ingest/decision 后刷新 | 不是数据库全量镜像 |
| `AgendaItem` | `runtime-owned` | 由 event ingest 生成、依赖和优先级驱动消费 | 是内部待办机制 |
| `CommandIntent` | `runtime-owned` | 由 action plan 发射 | 所有外部作用必须先变成命令 |
| `CommandReceipt` | `feedback-derived` | 由 adapter/executor 回执形成 | 回流到 inbox 继续驱动 |
| `EngineCheckpoint` | `runtime-owned` | 每轮循环后持久化 | 保证重启恢复和不中断驱动 |

## Non-Negotiable Conclusion

下面这些概念如果没有进入 runtime loop，就说明引擎还不是真驱动：

1. `BusinessOrchestrationState`
2. `DriverLearningRecord`
3. `TakeoverDecision`
4. `ComponentEndSignal / EndSignalEvaluation`
5. `ProofCompleteness`
6. `BlockerRecord / PlatformIncident`
7. `ActionPlan / BackfeedPlan`
8. `CommandIntent / CommandReceipt`
9. `CycleBackfeed`
10. `DecisionEnvelope`

## Real Drive Test

判断某个概念有没有被真实驱动，只问 5 个问题：

1. 它进入 runtime 的方式是 `EngineEvent`、`WorkingMemoryFrame`、还是只停在文档里？
2. 它会不会改变 agenda、fault decision、guard decision 或 action plan？
3. 它的变化有没有 command、receipt、backfeed 或 projection 跟随？
4. 引擎重启后，它的当前有效状态能不能从 checkpoint + object truth 恢复？
5. 如果把所有 handler 里的 `if / else` 删掉，这个概念还能不能继续参与推进？

只要有一项答不出来，它就还是空挂概念，不算被引擎真正驱动。

## Immediate Consequence

- 从现在起，代码阶段不能只实现对象 schema。
- 必须同步实现这些最小 runtime 驱动环：
  - `EngineEvent -> WorkingMemoryFrame`
  - `WorkingMemoryFrame -> AgendaItem`
  - `AgendaItem -> FaultDecision / GuardDecision / ActionPlan`
  - `ActionPlan -> CommandIntent`
  - `CommandIntent -> CommandReceipt`
  - `CommandReceipt -> CycleBackfeed / DecisionEnvelope / MessageProjection`
