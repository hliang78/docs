---
documentStatus: blocked-human-confirmation
topic: generic-ai-autodev-platform
template: 07-后端开发设计模板
createdAt: 2026-05-17
sourceType: planning-mining
---

# 【后端开发设计】通用AI自动化平台_规划与控制模块_V1.0

## 1. 文档信息

| 项目 | 内容 |
|------|------|
| 系统名称 | 通用 AI 自动化平台 |
| 模块名称 | 规划与控制模块 |
| 版本号 | V1.0 |
| 创建日期 | 2026-05-17 |
| 关联文档 | 【需求概要】通用AI自动化平台_V1.0.md<br>【接口文档】通用AI自动化平台_规划管理模块_V1.0.md |

## 2. 当前真实规划事实

- `dagengine` 被限定为执行引擎内核。
- 新平台至少需要 `planning`、`control`、`infrastructure governance`、`execution`、`evidence` 五平面。
- 首期后端不直接实现全量 OpenClaw 运行控制，而是先支撑 `program/doc/batch` 闭环。
- 首期技术路线已经收敛到：`dagengine + 自研 planner/control API + MySQL + 文件系统`。
- 新增冻结约束：运行环境治理对象化、业务层与基础设施层分离、预留超级 repair agent。
- `WorkspaceProfile / ToolchainProfile / CredentialBinding` 独立对象化、`PlatformIncident` 入 repair 平面、首期前端展示 profile / incident 摘要均已确认。
- 后端运行时方向已收敛到：`Go + Gin + 单进程模块化单体`。
- 自动驾驶引擎命名已完成三层冻结：
  - 规划与 contract 文档使用 authoritative names
  - `engine/` 内部实现使用 code names
  - UI 与评审解释使用 human-facing aliases

## 3. 候选分层设计

### 3.1 Planning 层

职责：

- Program
- PlanningDocument
- Workstream
- StoryBatch
- ReadinessDecision

### 3.2 Control 层

职责：

- RuntimeTaskPolicy
- RuntimeStory
- ExecutionPack
- WorkerProfile
- ApprovalProfile
- TurnHandoff
- BlockerRecord

### 3.3 Infrastructure Governance 层

职责：

- WorkspaceProfile
- ToolchainProfile
- CredentialBinding
- RuntimeEnvProfile
- PreflightProbe
- PlatformIncident
- RepairRun

### 3.4 Execution 层

复用 `dagengine`：

- ProcessDefinition
- NodeDefinition
- Task
- Ticket
- Execution

### 3.5 Evidence 层

职责：

- readiness summary
- batch summary
- planning evidence
- runtime evidence index

### 3.6 Engine 决策层

authoritative objects：

- `AutonomousDrivingInput`
- `WorldStateSnapshot`
- `IntentRequest`
- `RuntimeCapabilitySnapshot`
- `GuardDecision`
- `ActionPlan`
- `BackfeedPlan`
- `DecisionEnvelope`

engine code names：

- `DriveInput`
- `RoadView`
- `DriveGoal`
- `CarSetup`
- `GoCheck`
- `NextMove`
- `ReturnPlan`
- `DriveDecision`

## 4. 候选工程结构

首期推荐采用 [directory-structure-decision.md](/Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/generic-ai-autodev-platform/directory-structure-decision.md) 中定义的单根目录 monorepo，不先拆成多服务。

```text
generic-ai-autodev/
├── frontend-admin/
├── backend/
│   ├── cmd/
│   │   ├── server/
│   │   ├── migrate/
│   │   ├── seed/
│   │   └── readiness-recalc/
│   ├── src/
│   │   ├── engine/
│   │   │   ├── drive/
│   │   │   ├── road/
│   │   │   ├── goal/
│   │   │   ├── safety/
│   │   │   ├── move/
│   │   │   ├── run/
│   │   │   ├── back/
│   │   │   └── view/
│   ├── tests/
│   └── scripts/
├── schemas/
├── artifacts/
├── runtime-cache/
├── scripts/
└── docs/
```

说明：

- `frontend-admin/` 倾向采用显式 `React + TypeScript + Vite + TanStack Router + TanStack Query + shadcn/ui` 工作台栈
- `backend/` 是首期唯一后端程序入口
- `backend/` 采用 `Go + Gin`
- `cmd/server` 是首期唯一常驻 API 进程
- `backend/` 内部再按 `planning / batch-review / ops-governance / repair / readiness / adapters` 逻辑分层
- `backend/src/engine/` 是自动驾驶决策内核，内部优先采用 `DriveInput / RoadView / DriveGoal / GoCheck / NextMove / DriveDecision` 这套短名
- `schemas/` 承载共享 contract
- `artifacts/` 负责 evidence / export 承载
- `runtime-cache/` 负责程序级临时缓存和 trace
- `scripts/` 承接程序级验证脚本

### 4.1 engine 命名桥接规则

- `engine/` 内部可以使用 code names：
  - `DriveInput`
  - `RoadView`
  - `DriveGoal`
  - `GoCheck`
  - `NextMove`
  - `DriveDecision`
- 一旦跨出 `engine/` 边界，对外 contract 继续使用 authoritative names：
  - `AutonomousDrivingInput`
  - `WorldStateSnapshot`
  - `IntentRequest`
  - `GuardDecision`
  - `ActionPlan`
  - `DecisionEnvelope`

推荐桥接函数：

```go
func RoadViewFromWorldState(snapshot WorldStateSnapshot) RoadView
func DriveGoalFromIntent(req IntentRequest) DriveGoal
func GoSignalFromReadiness(d ReadinessDecision) GoSignal
func DriveDecisionFromEnvelope(e DecisionEnvelope) DriveDecision
```

## 5. 首期实现边界

- 先实现 planning 资源与读取接口
- 先实现 batch readiness 资源
- 先预留 profile / incident 的只读摘要接口
- 先按单后端应用承载 planning/control/ops governance 读取面
- 先按单常驻 API 进程承载前端全部读取面
- 先不实现全量 resident/pool/runtime 控制 UI
- 先不实现 AI 优化与轻量编辑
- 先不引入大型 AI workflow 编排框架
- 先不把 `BullMQ` 当成首批前置依赖

## 6. 与 dagengine 的关系

- `dagengine` 提供执行引擎内核
- 新平台新增 planning/control 语义层
- 基础设施治理层在 `dagengine` 之上，不写回 `dagengine` 充当业务真相层
- reviewed batch 后续通过 compile 转为 `dagengine` 可执行对象
- 首期优先采用库级适配，而不是先拆远程 `dagengine` 服务桥接

## 7. AI 推导建议

- compile 层建议单独模块化，不直接塞进 planning API 层。[待人工确认: 后端负责人]
- planning 与 runtime 的存储建议逻辑分离。[待人工确认: 架构负责人]
- 显式 React 工作台前端应消费自研薄 API，而不是直接耦合到底层 `dagengine` 接口，方向已确认。
- `SuperRepairCoordinator` 只消费 `PlatformIncident / PreflightProbe / RepairPlaybook` 这类基础设施对象，不直接改业务对象，方向已确认。
- 自动驾驶短名只应进入 `engine/` 内部实现，不能反向污染 API contract、schema 文档与数据库命名。

## 8. 规划缺口

- `MySQL` 边界已确认采用“同实例独立数据库”，数据库命名已确认采用 `oneops_ai_autodev`。
- 前端技术方向已确认采用显式 React 工作台栈，只借鉴 `React-Admin` 资源模式。
- `backend/` 的具体 import 细节与迁移入口封装方式仍待确认。

## 9. 代码事实来源清单

- `docs/prd-autodev/generic-ai-autodev-platform/dagengine-kernel-mapping.md`
- `docs/prd-autodev/generic-ai-autodev-platform/openclaw-control-plane-mapping.md`
- `docs/prd-autodev/generic-ai-autodev-platform/prd-planning-plane-mapping.md`
- `docs/prd-autodev/generic-ai-autodev-platform/technical-selection.md`
- `docs/prd-autodev/generic-ai-autodev-platform/runtime-governance-and-super-repair.md`
- `docs/prd-autodev/generic-ai-autodev-platform/directory-structure-decision.md`
- `docs/prd-autodev/generic-ai-autodev-platform/backend-framework-process-decision.md`
- `docs/prd-autodev/generic-ai-autodev-platform/migration-tool-decision.md`
- `docs/prd-autodev/generic-ai-autodev-platform/dagengine-integration-decision.md`
- `docs/prd-autodev/generic-ai-autodev-platform/validation-baseline-decision.md`
- `docs/prd-autodev/generic-ai-autodev-platform/autonomous-driving-engine-naming-freeze.md`
