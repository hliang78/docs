---
topic: generic-ai-autodev-platform
kind: full-stack
title: 自动驾驶系统
createdAt: 2026-05-17T10:40:32+0800
program: true
---

# Alignment

## Program Decisions

- 首期目标是自动驾驶系统 `MVP`，而不是一次性完成长期平台全貌。
- `dagengine` 当前被限定为 `执行引擎内核`。
- 当前阶段先做 `规划与标准化`，不提前启动 OpenClaw 开发任务。
- 系统重构路径采用：`多轮、多角度深入挖矿 -> 抽象建模 -> 标准化文档 -> reviewed PRD/batch -> OpenClaw 开发`。
- 自动驾驶系统的核心目标必须升级为：`PRD planning plane <-> AutoDev execution plane` 的直接双向自动循环。
- 最终循环终止权必须归属 `PRD/planning plane`，不能由 worker、repair 或单次 batch 自行宣布结束。
- 业务编排状态必须是一等公民，但不能无护栏直接驱动执行；系统必须提供类似自动辅助驾驶的 `OrchestrationSafetyGuard` 约束层。
- 更准确的总体抽象不是“纯无人驾驶”，而是“自动辅助驾驶系统 + AI 司机”：
  - `BusinessOrchestrationState / IntentRequest` 表达 AI 司机当前意图
  - `Autonomous Driving Engine` 负责辅助判断、纠偏和动作规划
- 自动驾驶系统的决策内核应进一步收束为统一的 `Autonomous Driving Engine`：把 business intent、truth、guard、capability、loop、backfeed 统一转译成动作规划，而不是散落在一堆 handler/controller if-else 中。
- 自动驾驶引擎现已进入工程冻结阶段：统一入口采用 `AutonomousDrivingInput`，统一决策输出采用 `DecisionEnvelope`，首期规则类型固定为 `state-reduction / guard / capability-matching / loop-progression`。
- 自动驾驶引擎命名已进入一致性冻结阶段：规划文档继续使用 `AutonomousDrivingInput / DecisionEnvelope / ReadinessDecision` 等 authoritative names，`engine/` 内部实现允许使用 `DriveInput / DriveDecision / GoSignal` 等 code names，并通过桥接函数显式转换。
- AI 司机不能只会“当前怎么开”，还必须具备两条正式通道：
  - 学习通道：把 `VerifierResult / EvidenceSet / CycleBackfeed / PRDAcceptanceDecision` 持续回流成下一轮策略修正
  - 外部接管通道：允许 human 或外部控制面在关键时刻暂停、覆写、改路由或接管推进
- 由于涉及组件很多，系统还必须具备正式的结束信号机制：
  - 每个组件都只能结束自己的工作
  - 不能把局部结束信号误放大成全局 closure
- 规划文档的统一写法以 [documentation-naming-conventions.md](/Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/generic-ai-autodev-platform/documentation-naming-conventions.md) 为准，避免对象名、状态名与口语说明混写。
- 代码阶段必须优先落引擎壳层最小闭环：`contracts -> worldstate -> guards -> planner -> projection`，而不是先把判断逻辑打散到 API handler。
- 前端首期优先面向 `PRD/StoryBatch 文档与批次管理`。
- 前端首页必须形成最小闭环：
  - `Topic/Program` 列表与详情
  - `PRD/Workstream/TestMatrix` 浏览与状态管理
  - `StoryBatch/RuntimeStory` 审核、状态推进、发布准备
- 首期交互以 `只读 + 审阅 + 状态推进` 为主。
- `AI 多轮优化` 与 `简单手动编辑` 明确延后到后续 batch，不进入第一批代码切片。
- 标准文档采用阶段式策略，首批优先 `01-07`，后续再补 `08-10`。
- 首期 MVP 验收口径为：`规划闭环 + 首批可执行 StoryBatch 进入 ready-for-openclaw 状态`。
- `模型/profile 配置管理` 不进入首批主线，后续 batch 再补。
- 运行环境治理必须前置对象化，至少冻结：
  - `WorkspaceProfile`
  - `ToolchainProfile`
  - `CredentialBinding`
  - `RuntimeEnvProfile`
  - `PreflightProbe`
- provider/runtime policy 也必须前置对象化，至少冻结：
  - `ProviderProfile`
  - `ProviderEndpoint`
  - `HarnessBinding`
  - `QuotaPolicy`
  - `TimeoutPolicy`
  - `LivenessPolicy`
- harness 必须单独前置对象化，不能只当 provider adapter 附注，至少冻结：
  - `HarnessProfile`
  - `HarnessSessionPolicy`
  - `HarnessContextPolicy`
  - `HarnessOutputContract`
- 自动驾驶系统必须把 `业务层问题` 与 `基础设施层问题` 分开建模，再通过 `ExecutionPack` 和 preflight 串起来。
- 系统必须预留一个 `SuperRepairCoordinator` 来处理机制性中断，但它不负责业务规划与业务开发决策。
- 挖矿优先顺序固定为：
  - 前端产品形态
  - `dagengine` 内核能力与缺口
  - `openclaw-autodev` 控制平面抽象
  - `prd-autodev` 规划平面抽象
  - 模板映射关系

## Batch Decisions

- `batch-000A` 已完成资源盘点与坑位规划。
- `batch-000B` 当前继续做需求澄清与规划策略确认。
- `batch-000C` 下一步进入多角度 research，其中以 `前端产品形态` 为第一优先挖矿主题。
- `batch-001` 的目标不是立刻开发，而是形成 reviewed 的 planning slice，并能安全产出第一批可执行 OpenClaw batch。
- 在代码前冻结阶段完成后，下一步不再补顶层概念，而是围绕自动驾驶引擎 contract 定义首批 schema/API/read model 切片。

## Control Plane Decisions

- 自动驾驶系统不继续把 `loops/*.conf` 当主模型，而是把它视为迁移来源。
- 自动驾驶系统控制面至少需要一等对象：
  - `RuntimeTaskPolicy`
  - `RuntimeStory`
- `ExecutionPack`
- `WorkerProfile`
- `WorkspaceProfile`
- `ToolchainProfile`
- `CredentialBinding`
- `RuntimeEnvProfile`
- `PreflightProbe`
- `ApprovalProfile`
- `DriverLearningSignal`
- `DriverLearningRecord`
- `ComponentEndSignal`
- `EndSignalEvaluation`
- `TurnHandoff`
- `BlockerRecord`
- `VerifierResult`
- `RepairRun`
- `PlatformIncident`
- `TakeoverRequest`
- `TakeoverDecision`
- `ReadinessDecision`
- `EndSignalProjection`
- `ProgramCycle`
- `CycleBackfeed`
- `PRDAcceptanceDecision`
- `BusinessOrchestrationState`
- `OrchestrationTransition`
- `OrchestrationSafetyGuard`
- `SafetyInterlock`
- 如果未来继续承接聊天/手机控制面，则 `MessageProjection` 也必须是一等导出对象
- 候选首批 lane 为：
  - `planner`
  - `frontend`
  - `backend`
  - `ct`
- batch readiness 进入 OpenClaw 前必须满足 reviewed planning、lane-scoped stories、清晰的 validation/allowed paths/依赖约束。
- 学习通道与外部接管通道的对象也必须在代码前进入正式 schema，而不能继续停留在解释层类比。
- 组件结束信号也必须在代码前进入正式 schema，否则 done/close/acceptance 仍会混线。

## Infrastructure Decisions

- `environment.* / provider.* / process.*` blocker 默认进入 `Repair / SuperRepair`，不回流 `Planner`。
- helper tools 需要纳入 `ToolchainProfile`，不再依赖“机器上碰巧装过”的隐式能力。
- `PreflightProbe` 失败时，默认禁止 worker 继续正式执行。
- `WorkspaceProfile / ToolchainProfile / CredentialBinding` 采用独立对象建模，不继续塞进单一大 `RuntimeEnvProfile`。
- `PlatformIncident` 正式接受为 repair 平面一等对象。
- 首期前端必须展示 `profile / incident` 的只读摘要，并以 `ReadinessSummaryProjection` 承接 readiness 结果条与右栏同步摘要。
- Web workbench 仍是主界面；若保留手机/消息控制面，则必须通过 `MessageProjection` 输出，不允许继续依赖自由文本报告。
- Web workbench、消息面、审批入口都必须能成为外部接管通道的一部分，而不只是只读播报面。
- harness 需要与 provider 并列治理：provider 回答“调用谁”，harness 回答“怎么执行”，两者都必须进入正式 schema 与 read model。
