---
topic: generic-ai-autodev-platform
kind: full-stack
title: 对象与状态冻结清单
createdAt: 2026-05-17T13:25:00+0800
program: true
status: draft
---

# Object And State Freeze Checklist

## Purpose

- 这份文档不是实现设计稿，而是“进入代码前必须冻结的对象模型与状态模型清单”。
- 目标是避免自动驾驶系统重复旧 `openclaw / prd-autodev` 的补丁式演进。
- 任何未冻结对象，默认不能进入正式前后端实现。

## Freeze Rule

- 先冻结对象，再冻结对象之间的读写关系。
- 先冻结状态，再冻结状态转换事件。
- 先冻结真相源，再冻结 UI 展示摘要。
- 先冻结 blocker route，再冻结 repair / approval / planner 行为。
- 先冻结统一对象存储与文件导出边界，禁止继续让核心真相散落在大量文件中。
- 先冻结 authoritative object names，再允许 engine 内部落 code aliases。

## Naming Rule

- 本文档中的对象名全部视为 authoritative names。
- 即使后续 `engine/` 内部代码采用自动驾驶短名，也不能反向污染这里的正式对象名。
- 具体命名映射见 [autonomous-driving-engine-naming-freeze.md](/Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/generic-ai-autodev-platform/autonomous-driving-engine-naming-freeze.md)。

## Part A - 角色冻结

以下角色必须先定义边界：

### `Human`

- 负责：
  - 目标确认
  - 范围裁剪
  - 审批
  - 环境类修复决策
  - 最终验收
- 不负责：
  - 直接维护 story truth
  - 手工改写运行时状态文件

### `Planner`

- 负责：
  - 粗略输入问答增强
  - program / workstream / batch 规划
  - reviewed planning slice 产出
- 不负责：
  - 直接执行 story
  - 处理 runtime blocker

### `Controller`

- 负责：
  - 选择 story
  - 生成 execution pack
  - 调度 worker
  - 汇总 verifier / evidence / blocker
- 不负责：
  - 替代 planner 做业务拆解
  - 假定 worker 自报完成就等于 `DONE`

### `Worker`

- 负责：
  - 执行被约束的 execution pack
  - 返回 patch / report / evidence
- 不负责：
  - 自行扩展范围
  - 修改 planner truth
  - 自己判定最终完成态

### `Repair / SuperRepair`

- 负责：
  - 处理 `runtime/tooling/env/auth/provider/process` 类 blocker
  - 处理平台机制性中断
  - 执行 residue cleanup、probe rerun、repair playbook
- 不负责：
  - 接管业务规划
  - 伪装为 planner 的下一轮任务生成
  - 直接判定业务 `DONE`

## Part B - 核心对象冻结

以下对象必须是一等对象，不能再藏在零散文档、状态文件或脚本参数里。

### Planning Plane

- `Program`
  - 顶层主题
  - 目标、边界、当前阶段、验收口径
- `QuestionRound`
  - 粗略输入后的追问轮次
- `ContextBrief`
  - 规划阶段浓缩上下文
- `Workstream`
  - 中层工作流分组
- `TestMatrix`
  - 关键验证场景矩阵
- `StoryBatch`
  - 一批待执行 stories 的规划包
- `PlanningReview`
  - reviewed / blocked-human-confirmation 等规划评审结果
- `ProgramCycle`
  - program 当前所处的自动循环轮次与阶段
- `CycleBackfeed`
  - execution 回流 planning 的结构化反馈包
- `PRDAcceptanceDecision`
  - PRD 对当前循环轮次的正式验收与终止决策
- `BusinessOrchestrationState`
  - 业务编排层的正式控制状态
- `OrchestrationTransition`
  - 关键业务状态推进请求
- `OrchestrationSafetyGuard`
  - 自动辅助驾驶式护栏判断
- `SafetyInterlock`
  - 关键推进前必须满足的强约束

### Control Plane

- `RuntimeTaskPolicy`
  - lane、默认模型、默认 runtime env、allowed writes、基础 stop conditions
- `RuntimeStory`
  - 执行侧 story 实体，不直接等同于 PRD 原文
- `ExecutionPack`
  - 当前 story 的编译产物
- `WorkerProfile`
  - worker 的能力画像
- `ProviderProfile`
  - provider 身份、默认模型、能力边界
- `ProviderEndpoint`
  - provider/gateway/region 级入口绑定
- `HarnessBinding`
  - provider、worker、runtime policy 与 adapter 的绑定关系
- `HarnessProfile`
  - harness 身份与执行语义画像
- `HarnessSessionPolicy`
  - harness session 生命周期规则
- `HarnessContextPolicy`
  - harness 上下文注入规则
- `HarnessOutputContract`
  - harness 输出、progress、evidence 契约
- `QuotaPolicy`
  - provider 额度、并发、降级策略
- `TimeoutPolicy`
  - request、first progress、silent hang 超时规则
- `LivenessPolicy`
  - heartbeat、silent hang、orphan session 判断规则
- `WorkspaceProfile`
  - 目录、写权限、artifact 目录、legacy import 目录
- `ToolchainProfile`
  - 语言/工具版本、必备 CLI、helper tools、验证命令基线
- `CredentialBinding`
  - provider、gateway、mysql、browser、remote access 等凭据引用
- `RuntimeEnvProfile`
  - provider、token、browser、remote access、db、gateway 等运行环境画像
- `PreflightProbe`
  - turn 前环境可用性与 residue 检查结果
- `ApprovalProfile`
  - 审批策略与审批范围
- `DriverLearningSignal`
  - AI 司机可吸收的结构化学习信号
- `DriverLearningRecord`
  - AI 司机按周期归并后的学习结论
- `ComponentEndSignal`
  - 某个组件结束当前工作的结构化结束信号
- `EndSignalEvaluation`
  - 系统对结束信号的正式采纳或拒绝结果
- `TurnHandoff`
  - 单轮执行交接物
- `EvidenceSet`
  - 该轮或该 story 的证据集合
- `VerifierResult`
  - 结构化验证结果，不等同于报告正文
- `ProofCompleteness`
  - 当前证据是否足够支撑结论
- `BlockerRecord`
  - 结构化阻塞记录
- `PlatformIncident`
  - 平台机制性中断对象
- `RepairRun`
  - repair 执行记录
- `TakeoverRequest`
  - 来自 human 或外部控制面的正式接管请求
- `TakeoverDecision`
  - 接管请求的正式处理结果
- `ReadinessDecision`
  - program/batch 当前 readiness 正式结论
- `EndSignalProjection`
  - 面向前端和消息面的结束信号摘要
- `MessageProjection`
  - 面向手机/消息通道的控制面导出对象

### Truth Plane

- `StoryTruth`
- `BatchTruth`
- `TurnTruth`
- `TaskTruth`
- `RepairTruth`

要求：

- 以上 truth 对象必须能回答“当前真实状态是什么”。
- 不能把 `UI summary`、`raw report`、`last text file` 直接当 truth。

### Engine Decision Layer

- `AutonomousDrivingInput`
  - 一次统一引擎评估的最小输入
- `WorldStateSnapshot`
  - truth / verifier / evidence / incident / probe 的统一世界快照
- `IntentRequest`
  - 当前业务系统请求的推进意图
- `RuntimeCapabilitySnapshot`
  - 当前动作可用的 worker / provider / harness / env 能力组合
- `GuardDecision`
  - 当前推进经过护栏后的正式裁定
- `ActionPlan`
  - 当前评估选择出的下一步动作计划
- `BackfeedPlan`
  - 当前动作完成后必须回刷的回流与 projection 计划
- `DecisionEnvelope`
  - 面向前端、消息面、审计、日志的统一决策输出

### Diagnostics Layer

- `DiagnosticFact`
  - 进入诊断引擎的归并事实
- `SymptomFrame`
  - 归并后的症状帧
- `FaultHypothesis`
  - 候选故障解释
- `FaultDecision`
  - 冲突消解后的正式故障裁定
- `RecoveryRoutePlan`
  - 故障裁定后的正式恢复路线

### Runtime Kernel Layer

- `ProgramCycleRuntime`
  - 每个 `Program` 的常驻引擎实例
- `EngineEvent`
  - 引擎 mailbox 的标准事件
- `WorkingMemoryFrame`
  - program 当前可决策现实的工作内存快照
- `AgendaItem`
  - runtime 内部待处理 agenda
- `CommandIntent`
  - 引擎发出的正式动作意图
- `CommandReceipt`
  - 执行侧返回的正式回执
- `EngineCheckpoint`
  - runtime 可恢复 checkpoint

### Storage Boundary

- 以下核心对象必须有统一对象读取入口，不允许继续只依赖分散文件：
  - `Program`
  - `StoryBatch`
  - `RuntimeStory`
  - `ExecutionPack`
  - `BlockerRecord`
  - `RepairRun`
  - `EvidenceTruth`
- 文件允许存在，但角色应降级为：
  - `artifact`
  - `export`
  - `cache`
  - `debug trace`
- 明确禁止继续保留的旧模式：
  - 从 `current-story.json` 反推当前真实 story
  - 从 `last-report.txt` 反推最终 truth
  - 从 handoff 文件反推当前批次执行目标
  - 从多个分散文件拼接 UI 当前状态

## Part C - 对象关系冻结

必须明确以下关系：

1. `Program -> Workstream -> StoryBatch -> RuntimeStory`
2. `Program -> ProgramCycle`
3. `ProgramCycle -> CycleBackfeed -> PRDAcceptanceDecision`
4. `Program / StoryBatch / RuntimeStory -> BusinessOrchestrationState`
5. `BusinessOrchestrationState -> OrchestrationTransition -> OrchestrationSafetyGuard`
6. `OrchestrationSafetyGuard -> SafetyInterlock`
7. `RuntimeStory -> ExecutionPack`
8. `RuntimeTaskPolicy -> WorkerProfile`
9. `RuntimeTaskPolicy -> RuntimeEnvProfile`
10. `RuntimeTaskPolicy / WorkerProfile -> HarnessBinding`
11. `HarnessBinding -> HarnessProfile / HarnessSessionPolicy / HarnessContextPolicy / HarnessOutputContract`
12. `RuntimeEnvProfile -> ProviderProfile`
13. `ProviderProfile -> ProviderEndpoint`
14. `RuntimeEnvProfile -> WorkspaceProfile`
15. `RuntimeEnvProfile -> ToolchainProfile`
16. `RuntimeEnvProfile -> CredentialBinding`
17. `VerifierResult / EvidenceSet / CycleBackfeed / PlatformIncident / ReadinessDecision / BlockerRecord -> DriverLearningSignal`
18. `DriverLearningSignal -> DriverLearningRecord`
19. `DriverLearningRecord -> IntentRequest / RuntimeTaskPolicy / ApprovalProfile / OrchestrationSafetyGuard`
20. `Human / MessageProjection / ApprovalFlow / ExternalController -> TakeoverRequest`
21. `TakeoverRequest -> TakeoverDecision`
22. `TakeoverDecision -> BusinessOrchestrationState / OrchestrationTransition / DecisionEnvelope`
23. `Worker / Verifier / Repair / Readiness / Takeover / Acceptance -> ComponentEndSignal`
24. `ComponentEndSignal -> EndSignalEvaluation`
25. `EndSignalEvaluation -> ReadinessDecision / DecisionEnvelope / BusinessOrchestrationState`
26. `EndSignalEvaluation -> EndSignalProjection`
17. `RuntimeEnvProfile -> QuotaPolicy / TimeoutPolicy / LivenessPolicy`
18. `RuntimeStory -> EvidenceSet`
19. `RuntimeStory -> VerifierResult`
20. `VerifierResult -> ProofCompleteness`
21. `RuntimeStory -> BlockerRecord`
22. `BlockerRecord -> PlatformIncident`
23. `PlatformIncident -> RepairRun`
24. `StoryBatch -> PlanningReview`
25. `PlanningReview + BatchTruth + StoryTruth + BlockerRecord + VerifierResult + EvidenceSet + PlatformIncident + PreflightProbe -> ReadinessDecision`
26. `ReadinessDecision -> MessageProjection`
27. `BusinessOrchestrationState + OrchestrationTransition + RuntimeTaskPolicy + WorkerProfile + RuntimeEnvProfile + ApprovalProfile + StoryTruth + BatchTruth + VerifierResult + EvidenceSet + PlatformIncident + PreflightProbe -> AutonomousDrivingInput`
28. `RuntimeTaskPolicy + WorkerProfile + RuntimeEnvProfile + ProviderProfile + ProviderEndpoint + HarnessBinding + HarnessProfile + ApprovalProfile + QuotaPolicy + LivenessPolicy -> RuntimeCapabilitySnapshot`
29. `AutonomousDrivingInput -> WorldStateSnapshot`
30. `WorldStateSnapshot + BusinessOrchestrationState + OrchestrationTransition -> IntentRequest`
31. `IntentRequest + OrchestrationSafetyGuard + SafetyInterlock + ApprovalProfile -> GuardDecision`
32. `GuardDecision + RuntimeCapabilitySnapshot -> ActionPlan`
33. `ActionPlan -> BackfeedPlan`
34. `AutonomousDrivingInput + WorldStateSnapshot + IntentRequest + GuardDecision + ActionPlan + BackfeedPlan -> DecisionEnvelope`
35. `Program -> ProgramCycleRuntime`
36. `Human / Frontend / dagengine / Verifier / Probe / Repair / Takeover / Acceptance / Timer -> EngineEvent`
37. `EngineEvent -> WorkingMemoryFrame`
38. `WorkingMemoryFrame -> DiagnosticFact / AutonomousDrivingInput`
39. `DiagnosticFact -> SymptomFrame -> FaultHypothesis -> FaultDecision`
40. `FaultDecision -> RecoveryRoutePlan / GuardDecision`
41. `EngineEvent + WorkingMemoryFrame + FaultDecision -> AgendaItem`
42. `ActionPlan -> CommandIntent`
43. `CommandIntent -> CommandReceipt`
44. `CommandReceipt -> TurnTruth / StoryTruth / EvidenceSet / VerifierResult / BlockerRecord / PlatformIncident / CycleBackfeed`
45. `WorkingMemoryFrame + AgendaItem + active command state -> EngineCheckpoint`

## Part C.1 - 引擎驱动判定规则

不是所有对象都应被 runtime 直接拥有。

必须明确 3 类对象：

1. `upstream-only`
   - 由 human、planner、external world 产生
   - 引擎只消费，不直接拥有
   - 如：`QuestionRound`、`ContextBrief`、`Workstream`、`TestMatrix`
2. `runtime-owned / decision-derived`
   - 必须进入 `ProgramCycleRuntime`
   - 如：`BusinessOrchestrationState`、`DriverLearningRecord`、`FaultDecision`、`GuardDecision`、`ActionPlan`
3. `feedback / projection`
   - 必须通过 command/receipt/backfeed 被真实驱动
   - 如：`VerifierResult`、`ProofCompleteness`、`CycleBackfeed`、`MessageProjection`

判定标准：

- 如果一个对象既不是 `upstream-only` 输入，
- 也不是 `runtime-owned / decision-derived`，
- 也不是 `feedback / projection`，
- 那它就是未被引擎真实驱动的空挂概念，不能进入代码。

完整覆盖矩阵见 [engine-drive-coverage-matrix.md](/Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/generic-ai-autodev-platform/engine-drive-coverage-matrix.md)。

必须明确以下只读关系：

1. `UI` 只能读 truth 对象与结构化证据，不直接读零散状态文件
2. `Planner` 只读执行结果摘要与 evidence，不直接改 worker 中间态
3. `Worker` 只读 execution pack、必要 code context、批准范围

## Part D - 状态模型冻结

## Planning 状态

### `Program.status`

- `draft`
- `in-research`
- `aligned`
- `planning-reviewed`
- `batch-ready`
- `implementation-blocked-human`

### `StoryBatch.status`

- `draft`
- `reviewed`
- `published`
- `blocked-human-confirmation`
- `retired`

### `PlanningReview.status`

- `pending`
- `reviewed`
- `blocked-human-confirmation`
- `rejected`

## Execution 状态

### `RuntimeStory.status`

- `open`
- `selected`
- `running`
- `blocked`
- `approval`
- `done`
- `abandoned`

### `TurnTruth.status`

- `queued`
- `running`
- `ended`
- `orphaned`
- `reconciled`

### `RepairRun.status`

- `queued`
- `running`
- `done`
- `failed`
- `expired`

### `PlatformIncident.status`

- `open`
- `investigating`
- `mitigated`
- `escalated`
- `closed`

### `ReadinessDecision.status`

- `not-ready`
- `ready-for-openclaw`
- `blocked-human-confirmation`
- `execution-waiting`
- `stopped`
- `closed`

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

## Blocker 状态

### `BlockerRecord.class`

- `business.scope`
- `business.optimization`
- `planning.gap`
- `approval.required`
- `environment.workspace`
- `environment.runtime`
- `environment.auth`
- `environment.tooling`
- `environment.dependency`
- `environment.secret`
- `infrastructure.capacity`
- `infrastructure.platform-defect`
- `provider.session`
- `process.residue`
- `verification.failed`

### `BlockerRecord.route`

- `route-planner`
- `route-repair`
- `route-approval`
- `route-human-review`

冻结规则：

- `environment.*` 默认不能自动回流 planner
- `approval.required` 默认不能自动触发 repair
- `planning.gap` 才允许进入 planner 下一轮

## Part E - 真相源冻结

每类真相必须有唯一 reducer。

### 必须先定义 reducer 的对象

- `StoryTruthReducer`
- `BatchTruthReducer`
- `TurnTruthReducer`
- `RepairTruthReducer`

### Reducer 输入必须分类

- `command issued`
- `worker report`
- `verifier result`
- `evidence written`
- `approval written`
- `repair result`
- `process probe`
- `scheduler decision`
- `incident opened`

### 必须冻结的存储规则

- `truth object` 只能通过统一 reducer 更新
- `export file` 不能反向写回 truth
- `cache file` 过期后必须可安全丢弃
- `debug trace` 只能用于诊断，不能参与业务决策

### Reducer 输出必须分类

- `truth status`
- `next required action`
- `current blocker`
- `evidence completeness`
- `ui summary projection`
- `readiness decision`
- `message projection`
- `cycle backfeed`
- `acceptance decision`

禁止继续保留的旧模式：

- 多个脚本各自推测 status
- `last-report.txt` 覆盖 truth
- status 页面和 detail 页面各自有一套推理逻辑
- 关键对象只以文件集合存在，没有统一对象读取入口
- 决策过程依赖大量约定路径，而不是依赖结构化对象读取

## Part F - 事件模型冻结

必须先定义这些标准事件：

- `program.aligned`
- `batch.reviewed`
- `batch.published`
- `story.selected`
- `turn.started`
- `worker.reported`
- `verifier.passed`
- `verifier.failed`
- `story.blocked`
- `story.approval-requested`
- `approval.granted`
- `repair.started`
- `repair.done`
- `probe.failed`
- `incident.opened`
- `incident.mitigated`
- `story.done`

要求：

- 所有状态转换都要通过标准事件落地。
- 不能再允许脚本直接“静默改状态”。

## Part G - 前端承载冻结

首期前端必须至少承载这些页面对象：

- `Program List`
- `Program Workspace`
- `PRD / Context / Questions Read Mode`
- `Story Batch Review Mode`
- `Worker Profile / Runtime Env Profile`
- `Workspace / Toolchain / Credential Profile Summary`
- `Blocker / Repair / Approval Summary`
- `Evidence / Readiness Review`
- `Program Cycle / PRD Acceptance Summary`

前端读取规则必须额外冻结：

- provider/runtime 摘要必须来自 `ProviderProfile / ProviderEndpoint / HarnessBinding / QuotaPolicy / TimeoutPolicy / LivenessPolicy` 的结构化只读模型
- harness 摘要必须来自 `HarnessProfile / HarnessSessionPolicy / HarnessContextPolicy / HarnessOutputContract`
- readiness 结果条与右栏同步摘要必须来自 `ReadinessSummaryProjection`
- 手机/消息通道如果继续存在，必须读取 `MessageProjection`，不能从聊天历史拼装

首期前端不应优先承载：

- 通用 AI 聊天工作台
- 自由 prompt 驱动开发入口
- 大规模可视化 DAG 编排器

## Part H - 开工前检查表

以下问题若还有任何一项答不出来，默认不能开工：

1. 当前最小闭环里有哪些一等对象？
2. 每个对象谁创建、谁修改、谁只读？
3. 哪些状态属于 planning，哪些属于 execution，哪些属于 repair？
4. 哪些 blocker 会回流 planner，哪些绝对不会？
5. UI 上每一个状态字段读的是哪个 truth reducer？
6. 当前 worker 能接什么任务，为什么？
7. 当前 execution pack 的固定字段有哪些？
8. `DONE` 到底由谁判定？
9. 哪类 verifier + evidence 才足以支撑 `DONE`？
10. 哪些文件只是导出物，哪些对象才是真相？
11. 一个 worker 的目录、工具、账号、env vars、helper tools、provider policy 到底由哪个对象负责？
12. `ready-for-openclaw` 由哪些对象归并决定？
13. 业务 blocker 和基础设施 blocker 分别走哪条 route？
14. 超级 repair agent 可以做什么、绝不能做什么？
15. execution 结果如何自动回流 PRD，且由谁给出最终 acceptance close？
16. harness 到底是谁、怎么执行、如何上报 progress/evidence？

## Recommended Immediate Follow-Up

1. 基于本清单补一份“角色-对象-状态关系图”
2. 基于本清单补一份“前端对象导航图”
3. 在代码阶段前，用这份清单逐项做人工对齐
