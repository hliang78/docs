---
topic: generic-ai-autodev-platform
kind: full-stack
title: 自动驾驶系统
createdAt: 2026-05-17T10:40:32+0800
status: draft
---

# dagengine 内核能力与缺口映射

## 1. 目的

明确 `dagengine` 作为“执行引擎内核”时，哪些能力可以直接复用，哪些能力仍明显缺失，以及自动驾驶系统首期必须新增哪些 planning/control 对象。

## 2. 当前真实代码事实

### 2.1 API 分层骨架已具备

`dagengine/v2/api/server.go` 已按领域注册以下路由组：

- engine
- process definitions
- ticket
- task
- escalation
- template

这说明 `dagengine` 已有面向平台 API 的模块化入口，而不是只有单体引擎接口。

### 2.2 ProcessDefinition 已具备可视化流程与节点定义容器

`dagengine/v2/persistence/interfaces.go` 已定义：

- `ProcessDefinition`
- `NodeDefinition`
- `DependencyDefinition`
- `ProcessLayout`

其中已经包含：

- 流程基础元数据
- 节点列表
- 边依赖
- 节点画布坐标

这对未来承接 `StoryBatch -> execution process` 很有价值。

### 2.3 Task/Ticket 已具备人工节点与流程推进模型

`dagengine/v2/task/model.go` 已定义：

- `Task`
- `ListFilter`

字段已覆盖：

- `ExecutionID`
- `NodeID`
- `ProcessID`
- `Assignee`
- `Status`
- `TimeoutAt`
- `Result`

`dagengine/v2/ticket/model.go` 已定义：

- `Ticket`
- `draft/submitted/in_progress/completed/cancelled`
- `PausedAt`
- `PauseReason`
- `Metadata`

这说明 `dagengine` 已经具备：

- 人工待办
- 执行暂停/恢复
- 案例容器级状态管理

### 2.4 Task API 已支持人工节点恢复执行

`dagengine/v2/api/task_handlers.go` 已支持：

- `GET /api/v1/my-tasks`
- `GET /api/v1/tasks/:id`
- `POST /api/v1/executions/:eid/nodes/:nid/complete`

其中 `completeNode` 会：

- 完成待办
- 调用 `ContinueExecution`
- 在新节点挂起时继续创建下一个待办

这意味着它天然适合承接未来的：

- approval node
- manual review node
- human-in-the-loop gate

### 2.5 Ticket API 已具备更宽泛的流程控制壳

`dagengine/v2/api/ticket_handlers.go` 已支持：

- create/list/get/update ticket
- submit/cancel/pause/resume
- result/progress

这说明 `dagengine` 不仅能跑“流程”，还能包装成更长生命周期的“案例/工单”。

### 2.6 平台 MVP 骨架已存在，但更像骨架而不是成品

`dagengine/it_ops/platform/services/platform_service.go` 已定义：

- `PlatformService`
- `WorkflowManager`
- `WorkflowDefinition`
- `PlatformNodeRegistry`
- `PlatformExecutionScheduler`

同时提供：

- workflow 定义
- plugin/script/api/builtin node 类型
- scheduler/config 骨架

但这部分更像 MVP 平台壳，还不是能直接承接新控制面的完整实现。

## 3. 可直接复用的内核能力

### 3.1 执行流程容器

建议直接复用：

- `ProcessDefinition`
- `NodeDefinition`
- `DependencyDefinition`
- `ProcessLayout`

用途：

- 承接未来 runtime 编译后的执行过程定义
- 表达 StoryBatch 映射后的可执行流程

### 3.2 执行状态与持久化接口

建议直接复用：

- `PersistenceInterface`
- `Save/Get/List/Delete ProcessDefinition`
- `ExecutionDocument` 相关存储能力

用途：

- 作为自动驾驶系统 runtime 存储抽象底座

### 3.3 人工节点与待办模型

建议直接复用：

- `Task`
- task API
- `ContinueExecution` 路径

用途：

- 承接 future approval/review/manual gate

### 3.4 案例容器与暂停恢复机制

建议直接复用：

- `Ticket`
- ticket API
- pause/resume/progress/result

用途：

- 承接 program execution case 或长流程任务容器

### 3.5 API 模块化注册方式

建议直接复用思路：

- `server.go` 领域式注册

用途：

- 后续可扩展为 `planning/control/runtime/evidence` 分域 API

## 4. 不应直接复用或当前明显不足的部分

### 4.1 planning/control 语义缺失

`dagengine` 当前没有直接表达这些对象：

- Program
- Workstream
- StoryBatch
- RuntimeStory
- ExecutionPack
- WorkerProfile
- ApprovalProfile
- Handoff
- RepairRun
- ReadinessDecision

这意味着它不能直接替代：

- `prd-autodev` 的规划平面
- `openclaw-autodev` 的控制平面

### 4.2 file persistence 尚未完整

从 `dagengine/v2/persistence/interfaces.go` 及相关实现可以看到：

- 内存持久化相对完整
- 文件持久化有多处“待完成”实现

因此首期不能把未完备的 file persistence 当作生产级基座。

### 4.3 platform service 更像 MVP 骨架

`it_ops/platform/services/platform_service.go` 已有很好骨架，但当前问题是：

- 更偏 workflow 平台，不是 AI 自动化控制平台
- 未直接建模 planning/control/evidence
- 对 OpenClaw 风格的 story/repair/approval/reconcile 语义无直接支持

### 4.4 不能直接拿 Ticket/Task 当 Story/Batch

虽然概念接近，但不能硬映射：

- `Story` != `Task`
- `Batch` != `ProcessDefinition`
- `LoopConfig` != `PlatformConfig`

中间必须补一层新对象：

- planning 对象
- control 对象
- runtime 编译对象

## 5. 自动驾驶系统建议对象分层

### 5.1 Planning Plane 新对象

- `Program`
- `Workstream`
- `PlanningDocument`
- `StoryBatch`
- `ReadinessGate`

### 5.2 Control Plane 新对象

- `RuntimeTask`
- `Lane`
- `RuntimeStory`
- `ExecutionPack`
- `WorkerProfile`
- `ApprovalProfile`
- `Handoff`
- `RepairPolicy`

### 5.3 Execution Plane 复用对象

- `ProcessDefinition`
- `NodeDefinition`
- `DependencyDefinition`
- `Task`
- `Ticket`
- `Execution`

## 6. 候选映射关系

| 自动驾驶系统概念 | dagengine 候选承接 | 说明 |
|---|---|---|
| reviewed StoryBatch | `ProcessDefinition` metadata + extra planning store | 不能裸用，需要 planning 层补语义 |
| approval step | `Task` + suspended execution | 适合 |
| long-running automation case | `Ticket` + execution | 适合 |
| runtime execution graph | `ProcessDefinition` | 适合 |
| planner/control API | `v2/api/server.go` 分域模式 | 适合复用模式 |
| evidence store | [待补充] | 现有内核未直接覆盖 |

## 7. 首期后端结论

首期后端应采用：

1. `dagengine` 作为执行引擎内核。
2. 自动驾驶系统单独新增 `planning` 与 `control` 领域模型。
3. 通过编译层把 reviewed batch/story 转换成 `dagengine` 可执行对象。
4. 不直接把 `it_ops/platform` 当成完整平台交付物。

## 8. AI 推导建议

- 首期后端 API 应先围绕 `program/doc/batch/readiness`，而不是一开始全量暴露 OpenClaw runtime 控制。[待人工确认: 后端负责人]
- 后续可把 `Task/Ticket` 用于 human review、approval、manual release 等节点，而不是直接替代 planning 对象。[待人工确认: 架构负责人]

## 9. 规划缺口

- `ExecutionPack` 的正式 schema 还未定义。
- planning store 与 runtime store 如何分层还未定。
- `readiness -> runtime compile` 的转换规则还未正式文档化。

## 10. 代码事实来源清单

### 已读取关键文件

- `dagengine/v2/api/server.go`
- `dagengine/v2/api/process_definitions.go`
- `dagengine/v2/api/task_handlers.go`
- `dagengine/v2/api/ticket_handlers.go`
- `dagengine/v2/persistence/interfaces.go`
- `dagengine/v2/task/model.go`
- `dagengine/v2/ticket/model.go`
- `dagengine/it_ops/platform/services/platform_service.go`

### 文件对应事实类型

- API 分域结构
- process/task/ticket/persistence 领域对象
- platform service MVP 骨架

### 仍未读取或无法确认的范围

- `dagengine` 真实生产使用路径
- 更完整的 plugin/runtime 实现深度
- 自动驾驶系统是否沿用其现有 service manager 装配方式

### 因无法确认而保留的内容

- planning store 的最终实现方式
- runtime compile 的最终对象结构
