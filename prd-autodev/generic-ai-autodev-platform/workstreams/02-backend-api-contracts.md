---
topic: generic-ai-autodev-platform
kind: full-stack
title: 自动驾驶系统
createdAt: 2026-05-17T10:40:32+0800
program: true
---

# Backend API Contracts

## Purpose

明确 `dagengine` 作为执行引擎内核时，首期平台后端应复用哪些现成能力、缺哪些 control/planning 契约，以及后续 API 契约需要怎样围绕前端最小闭环展开。

## Findings

- `dagengine/v2/api/server.go` 已具备按 engine/process/ticket/task/escalation/template 分域注册 API 的结构。
- `dagengine/v2/persistence/interfaces.go` 已定义 `ProcessDefinition`、`NodeDefinition`、`DependencyDefinition`、`ProcessLayout`，可以承接 runtime graph。
- `dagengine/v2/task/model.go` 与 `dagengine/v2/api/task_handlers.go` 已具备人工待办、超时、完成后继续执行的路径。
- `dagengine/v2/ticket/model.go` 与 `dagengine/v2/api/ticket_handlers.go` 已具备案例容器、暂停恢复、进度查询能力。
- `dagengine/it_ops/platform/services/platform_service.go` 已有 workflow/node/scheduler 平台骨架，但更像 MVP workflow 平台，不是 AI 自动化控制平台成品。
- `dagengine` 当前缺少直接表达 `Program/Workstream/StoryBatch/ExecutionPack/WorkerProfile/Handoff/ReadinessDecision` 的 planning/control 语义。
- `dagengine` 当前也缺少直接表达 `DriverLearningSignal / DriverLearningRecord / TakeoverRequest / TakeoverDecision` 的学习/接管语义。
- 首期后端并不需要先把所有 OpenClaw runtime 能力 UI 化，而是先围绕 `program/doc/batch` 管理闭环定义 API。
- 详细映射见 `dagengine-kernel-mapping.md`。

## Requirements

- 明确 `dagengine` 可直接复用的 process/task/ticket/persistence/api 骨架。
- 明确自动驾驶系统必须新增的 planning/control 领域对象与接口层。
- 明确前端首页最小闭环对应的后端资源对象和查询/状态推进接口范围。
- 明确 reviewed batch 如何在后续阶段编译到 `dagengine` runtime graph。
- 明确 AI 司机学习通道与外部接管通道在首批 API 中的最小承接方式。
- 明确组件结束信号在首批 API 中的最小承接方式。

## Acceptance

- 形成一版 `dagengine` 可复用能力清单与缺口清单。
- 形成一版首期后端 API 契约边界，不把控制台扩展成全量运行台。
- 为后续 `06-接口文档模板` 提供候选接口面。
- 形成 `dagengine-kernel-mapping.md` 这样的代码级事实沉淀。
- 形成首批学习/接管对象的最小资源面，不让它们继续停留在概念文档。
- 形成首批结束信号对象的最小资源面，避免 done/close 信号继续混线。

## Validation

- 代码路径级引用 `dagengine` 现有 API / persistence / task / ticket 能力。
- 缺口说明能够映射到 planning/control 新对象，而不是泛化描述。
- 不把 `Task/Ticket/ProcessDefinition` 直接误写成 `Story/Batch/Program` 的等价物。

## Candidate Stories

- 盘点 `dagengine` 可复用内核接口与扩展点。
- 定义首期 `program/doc/batch` 后端资源边界。
- 定义 reviewed batch -> runtime compile 的候选映射规则。
- 定义学习信号与接管请求的首批 schema / API / projection 承接方式。
- 定义组件结束信号与结束信号评估的首批 schema / API / projection 承接方式。

## First Slice Recommendation

首批后端不需要一次性把“AI 司机学习系统”做成复杂自治模块，但至少要把它纳入正式资源面。

### Schema Slice

- 首批必须补：
  - `DriverLearningSignal`
  - `DriverLearningRecord`
  - `TakeoverRequest`
  - `TakeoverDecision`
  - `ComponentEndSignal`
  - `EndSignalEvaluation`
- 这 6 个对象优先进入：
  - control plane schema
  - projection read model
  - message projection source

### API Slice

- 首批推荐只开放最小接口：
  - `GET /api/v1/programs/{programId}/decision-rail`
  - `GET /api/v1/programs/{programId}/driver-learning`
  - `GET /api/v1/programs/{programId}/takeover`
  - `GET /api/v1/programs/{programId}/end-signals`
  - `POST /api/v1/programs/{programId}/takeover-requests`
  - `POST /api/v1/takeover-requests/{takeoverRequestId}/apply`
- 设计原则：
  - 学习通道首批以只读聚合为主
  - 接管通道首批必须允许正式写入请求
  - 不要求首批开放复杂历史管理、批量编辑或策略训练面板

### Read Model Slice

- 首批后端至少应返回：
  - `DecisionRailView`
  - `DriverLearningSummaryView`
  - `TakeoverSummaryView`
  - `EndSignalSummaryView`
- 其中 `DecisionRailView` 至少补入：
  - `currentIntentSummary`
  - `latestLearningSummary`
  - `activeTakeoverSummary`
  - `availableTakeoverActions`
  - `latestEndSignalSummary`
  - `riskConfidenceSummary`
  - `topReasons`

### Compilation Boundary

- `DriverLearningRecord`
  - 进入下一轮 `AutonomousDrivingInput` 的补充输入
- `TakeoverDecision`
  - 进入下一次 `IntentRequest / OrchestrationTransition / DecisionEnvelope` 的约束输入
- 也就是说：
  - 学习对象更偏向“下一轮判断输入”
  - 接管对象更偏向“当前推进约束输入”
