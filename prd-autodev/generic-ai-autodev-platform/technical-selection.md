---
topic: generic-ai-autodev-platform
kind: full-stack
title: 自动驾驶系统
createdAt: 2026-05-17T10:40:32+0800
status: draft
---

# 技术选型结论

## 1. 目的

把当前已确认的“MVP 轻量技术路线”固化成正式结论，避免后续前端讨论、后端切片、OpenClaw task contract 设计时再次回到“大型 AI 编排平台是否引入”的岔路。

## 2. 结论

当前选型采用：`后续最容易演进版`。

### 2.1 选型结果

| 层 | 选型 | 用途 |
|---|---|---|
| Frontend | `React + TypeScript + Vite + TanStack Router + TanStack Query + shadcn/ui` | 承接 `Program -> Docs -> StoryBatch` 管理工作台，并借鉴 `React-Admin` 的工作台模式 |
| State Model | `XState` | 管理 `draft/reviewed/ready/blocked` 等状态机 |
| Execution Kernel | `dagengine` | 承接 process/task/ticket/execution 内核 |
| Backend Runtime | `Go + Gin` | 承接统一后端 API 与 `dagengine` 适配 |
| Platform Service | 自研薄层 `planner/control API` | 承接 planning/control/ops governance 语义 |
| Metadata Store | `MySQL` | 存 program、document、batch、review、policy 等结构化元数据 |
| Evidence Store | 文件系统 | 存 markdown、json、evidence、screenshots、batch summary |
| Async Task | 首期不引入；必要时再补 `BullMQ` | 后续承接 compile、assist、readiness recalc 等轻异步任务 |

## 3. 为什么选这套

### 3.1 对当前目标最匹配

- 当前重点是规划闭环和工作台，不是做一个通用 AI workflow 平台。
- 这套组合足以支撑：
  - Program 工作台
  - 文档审阅
  - Batch readiness
  - 后续 reviewed batch -> runtime compile

### 3.2 不会把平台带偏

- 不引入 `LangGraph`、`CrewAI`、`Flowise`、`Activepieces` 作为核心。
- 保留平台主导权在本项目自己的 planning/control/runtime 模型中。
- 避免先被第三方 agent/workflow 抽象锁死，再反向适配业务。
- 后端直接采用 `Go + Gin`，避免再造一层跨语言中间 API 去适配 `dagengine`。

### 3.3 后续演进空间更大

- 显式 `React` 工作台栈更适合 AI 自动开发、文件级维护与后续定制。
- 借鉴 `React-Admin` 的资源列表/详情/过滤心智，但不被其壳和约定绑死。
- `MySQL + 文件系统` 更贴近当前环境约束，也适合后续平台化演进。
- `dagengine` 继续扮演执行内核，不浪费已有资产。
- `BullMQ` 延后引入，避免 MVP 早期过度工程化。

## 4. 不采用的方向

| 方向 | 当前不采用原因 |
|---|---|
| `PocketBase` 作为核心后端 | 适合极轻 MVP，但不适合承接后续三平面长期演进核心 |
| `LangGraph` 作为平台核心 | 更偏 AI agent/workflow 基础设施，超出当前 MVP 重心 |
| `Activepieces` / `Flowise` / `CrewAI` | 会把平台拉向通用编排产品，而不是当前的 planning/control 平台 |
| `React-Admin` 直接作为前端脚手架 | 工作台模式可借鉴，但对 AI 自动开发和显式组件控制不够友好 |

## 5. 推荐分层

### 5.1 Planning Plane

- `Program`
- `PlanningDocument`
- `Workstream`
- `StoryBatch`
- `ReadinessDecision`

### 5.2 Control Plane

- `RuntimeTaskPolicy`
- `RuntimeStory`
- `ExecutionPack`
- `WorkerProfile`
- `ApprovalProfile`
- `TurnHandoff`
- `BlockerRecord`

### 5.3 Execution Plane

- `dagengine` 的 `ProcessDefinition`
- `Task`
- `Ticket`
- `Execution`

### 5.4 Evidence Plane

- markdown
- json
- screenshots
- batch summary
- final readiness

## 6. MVP 实施边界

### 6.1 首批做

- Program 列表
- Program 工作台
- 文档阅读与状态识别
- Batch 审核与 readiness 判定
- planning/control API 的最小读取接口

### 6.2 首批不做

- OpenClaw 运行控制台
- 模型/profile 全量管理
- 大规模 AI 工作流编排
- 重型异步编排与多代理框架

## 7. 对后续代码阶段的影响

- 前端优先按“借鉴 `React-Admin` 工作台模式的显式 React 栈”讨论页面形态。
- 后端优先按 `dagengine + 薄 planner/control API` 讨论目录与接口切片。
- 后端优先按 [backend-framework-process-decision.md](/Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/generic-ai-autodev-platform/backend-framework-process-decision.md) 的 `Go + Gin + 单进程模块化单体` 承接。
- 存储优先按 `MySQL + 文件系统` 讨论实体与 evidence 映射。
- `BullMQ` 不是首批前置条件，只有在 assist/compile/readiness 异步压力出现时再补。
- 新目录优先按 [directory-structure-decision.md](/Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/generic-ai-autodev-platform/directory-structure-decision.md) 的“单根目录 monorepo + 一个前端 + 一个后端 + 逻辑分层”承接。

## 8. 当前仍待确认

- 前端技术方向已确认采用显式 `React` 栈，并只借鉴 `React-Admin` 的资源/列表/详情模式。
- `MySQL` 边界已确认采用“同实例独立数据库”，数据库命名已确认采用 `oneops_ai_autodev`。
- 新程序根目录的最终验证命令。
- 首批不纳入 `AI 优化/轻量编辑` 已确认，后续 batch 再补。
- `backend/` 的具体 import 细节与验证脚本落地顺序仍待确认。

## 8.1 已确认的新目录承接方式

- 新程序根目录固定为 `/Users/huangliang/project/OneOPS-ALL/generic-ai-autodev`
- 首期采用单目录 monorepo
- 首期采用一个前端应用 + 一个后端应用
- 后端采用逻辑分层，不先物理拆成多服务
- 后端首期采用 `Go + Gin + 单进程模块化单体`
- `dagengine` 首期采用库级接入，不复用其现成 server
- 数据库命名采用 `oneops_ai_autodev`
- validation contract 采用项目级 wrapper scripts

## 9. 当前结论

- 技术路线已经不再开放式发散。
- 当前最优动作是围绕这套选型做前端专题讨论和首批代码切片，而不是继续扩大选型面。
