---
topic: generic-ai-autodev-platform
kind: full-stack
title: 自动驾驶系统
createdAt: 2026-05-17T10:40:32+0800
program: true
---

# Program Plan

## Objective

以 `dagengine` 作为执行引擎内核，在新目录中重构一个首期可跑通的自动驾驶系统 MVP。首期重点不是把所有历史能力一次迁移完，而是先通过多轮、多角度挖矿，提取 `prd-autodev` 与 `openclaw-autodev` 的关键信息、契约和对象模型，完成标准化规划，并为后续由 `prd-autodev-loop` 产出 PRD/batch、由 `openclaw-autodev` 启动自动开发建立稳定输入。最终目标不是一次性下发开发，而是让 `PRD planning plane <-> AutoDev execution plane` 形成直接双向自动循环，并由 PRD 验收终止循环。

## Definition Of Done

- 首期目标、范围、边界、优先级、验收方式在标准化规划文档中明确。
- `dagengine` 被明确限定为执行引擎内核，而不是直接照搬成整个平台。
- 首期技术路线固定为 `React + TypeScript + Vite + TanStack Router + TanStack Query + shadcn/ui + XState + dagengine + planner/control API + MySQL + 文件系统`。
- `prd-autodev` 与 `openclaw-autodev` 的核心资产完成至少一轮以上多角度挖矿，形成可复用抽象。
- 前端首期优先方向明确为 `PRD/StoryBatch 文档与批次管理`。
- 标准文档链路明确采用 `docs/development-doc-templates/01-10`，但按阶段逐步产出，不要求一次性完成全部模板。
- 在未完成规划与标准化之前，不启动正式 OpenClaw 开发任务。
- 第一版 reviewed program/PRD/batch 可以作为后续 OpenClaw 自动开发的安全输入。
- 第一批可执行 StoryBatch 达到 `ready-for-openclaw`，且其输入来自已 reviewed 的规划产物。
- execution verifier/evidence 能稳定回流到 PRD/planning plane，驱动下一轮 batch、PRD 修订或 acceptance close。
- 循环最终只能由 PRD/planning plane 给出 acceptance close，而不是由单次 execution 自行结束。
- 规划文档、schema 与 API contract 中的核心对象命名保持 authoritative 一致，不因代码层自动驾驶短名而漂移。
- 规划目录的统一写法以 [documentation-naming-conventions.md](/Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/generic-ai-autodev-platform/documentation-naming-conventions.md) 为准。

## Scope

### In Scope

- 基于 `dagengine` 的自动驾驶系统方案定义
- `prd-autodev` / `openclaw-autodev` 的多轮、多角度深入挖矿
- 规划、开发、测试文档标准化路线设计
- 前端首期 `PRD/StoryBatch 文档与批次管理` 目标定义
- 后续 OpenClaw 自动开发的 program/PRD/batch 输入设计
- PRD 与 AutoDev 双向自动循环设计
- 新目录与新架构的边界设计
- 新程序根目录承接结构冻结
- harness 治理边界与执行语义冻结

### Out Of Scope

- 当前轮次不直接启动前后端实际开发
- 当前轮次不直接发布 OpenClaw RuntimeStory
- 当前轮次不把 OpenClaw 管理台、模型/profile 配置管理一次性全部实现
- 当前轮次不把 `docs/development-doc-templates/01-10` 全部一次性写完
- 当前轮次不把历史实现直接整体复制到新目录

## Planning Strategy

### Core Principle

规划阶段的核心不是尽快开工，而是通过多轮、多角度深入挖矿，先把信息提取充分，再形成架构、文档、批次与自动化边界。

### Mining Rules

1. 先挖资产，再做抽象，再做设计，再做 batch。
2. 每一轮挖矿必须留下文件化产物，不能只停留在会话判断。
3. 挖矿角度至少覆盖：
   - 领域对象
   - 文件契约
   - 状态机
   - 运行控制
   - 前端管理需求
   - 后端内核映射
   - 标准文档映射
4. 在挖矿信息不足时，优先继续 research，而不是抢先进入 story 发布。
5. 第一批 OpenClaw 任务只能消费 reviewed 的规划产物，不能反过来替代规划。
6. execution 结果必须自动结构化回流 planning plane，不能停留在执行侧报告。
7. PRD 是循环的最终 acceptance authority。
8. 自动驾驶引擎相关对象命名必须区分 planning authoritative names 与 engine code names，禁止在规划文档中混用。

## Standard Document Rollout

### Phase-First Rule

标准文档采用阶段式覆盖，不做“一次性补齐 01-10”。

### First Priority

首期优先覆盖 `01-07`：

- `01-需求概要模板.md`
- `02-功能清单模板.md`
- `03-实体属性清单模板.md`
- `04-原型清单模板.md`
- `05-数据库设计模板.md`
- `06-接口文档模板.md`
- `07-后端开发设计模板.md`

### Later Expansion

进入测试和自动化验证阶段后，再逐步补齐：

- `08-测试用例模板.md`
- `09-接口调用文档模板.md`
- `10-自动化测试脚本说明模板.md`

### Revision Policy

首批标准文档允许先形成可审阅版本，后续随着挖矿深入和 batch 执行证据持续修订。

## Technology Direction

### Chosen MVP Stack

- Frontend: `React + TypeScript + Vite + TanStack Router + TanStack Query + shadcn/ui`
- State Model: `XState`
- Execution Kernel: `dagengine`
- Platform Service: 自研薄层 `planner/control API`
- Metadata Store: `MySQL`
- Evidence Store: 文件系统
- Async Task: 首期不引入，必要时再补 `BullMQ`

补充确认：

- 前端只借鉴 `React-Admin` 的工作台模式，不直接采用其脚手架壳
- 数据库命名采用 `oneops_ai_autodev`
- validation contract 采用项目级 wrapper scripts

### Directory Direction

- 新程序根目录固定为 `/Users/huangliang/project/OneOPS-ALL/generic-ai-autodev`
- 首期采用：
  - 一个前端应用 `frontend-admin/`
  - 一个后端应用 `backend/`
  - 程序内 `artifacts/`、`runtime-cache/`、`schemas/`、`scripts/`
- 首期不拆成多个独立后端服务

### Backend Runtime Direction

- `backend/` 首期采用 `Go + Gin`
- 进程模型采用 `单进程模块化单体`
- `SuperRepairCoordinator` 首期作为模块存在，不独立常驻
- `dagengine` 首期优先通过库级适配接入

### Why This Direction

- 保持系统核心抽象在本项目内部，而不是交给大型 AI workflow 平台。
- 让前端工作台和后端执行内核都能逐步演进。
- 对当前 `Program -> Docs -> StoryBatch` MVP 闭环最贴合。

## Workstreams

| ID | Workstream | Lane | Status | Notes |
|---|---|---|---|---|
| 01 | 资产挖矿与对象抽取 | planning | in_progress | 多轮、多角度提取 `prd-autodev` / `openclaw-autodev` / `dagengine` 核心抽象 |
| 02 | 标准化文档路线设计 | planning | in_progress | `01-07` 模板映射已建立，后续待与代码切片联动 |
| 03 | 前端 MVP 规划 | frontend-planning | in_progress | 首期优先 `PRD/StoryBatch 文档与批次管理` 页面与交互，技术方向采用显式 React 工作台栈，并借鉴 `React-Admin` 模式 |
| 04 | 后端内核映射规划 | backend-planning | in_progress | 明确 `dagengine` 内核映射与 control/planning 缺口，元数据层采用 `MySQL + 文件系统` |
| 04A | 新目录承接结构规划 | backend-planning | in_progress | 冻结新程序根目录、前后端承载方式与程序内目录语义 |
| 04B | 后端运行时承接规划 | backend-planning | in_progress | 冻结 `backend/` 的语言、框架、进程模型与 `dagengine` 接入方式 |
| 05 | 自动开发启动策略 | planning | draft | reviewed PRD/batch -> OpenClaw task 的启动边界 |
| 06 | 候选 Lane 规划 | planning | in_progress | 预定义 `planner/frontend/backend/ct` 等候选执行 lane |
| 07 | Regression Suite | ct | in_progress | 已形成首轮 planning shell smoke 与 contract regression 草案 |

## Dependency Map

- `资产挖矿与对象抽取` -> `标准化文档路线设计`
- `资产挖矿与对象抽取` -> `前端 MVP 规划`
- `资产挖矿与对象抽取` -> `后端内核映射规划`
- `标准化文档路线设计` + `前端 MVP 规划` + `后端内核映射规划` + `候选 Lane 规划` -> program alignment
- program alignment -> first reviewed PRD / batch
- first reviewed PRD / batch -> OpenClaw task creation and execution
- OpenClaw execution -> verifier/evidence/backfeed -> PRD acceptance / next batch / close decision

## Risk Register

| Severity | Risk | Decision Needed |
|---|---|---|
| P0 | 规划阶段过早进入开发，导致 story 与架构粗糙失真 | 先完成多轮挖矿与标准化，再启动 OpenClaw |
| P0 | 把 `dagengine` 误当成完整平台而非执行内核 | 固定其当前定位为执行引擎内核 |
| P1 | 首期前端范围过大，影响 MVP 跑通 | 先聚焦 `PRD/StoryBatch 文档与批次管理` |
| P1 | `01-10` 模板被误解为首轮一次性全部交付 | 明确按阶段逐步产出 |
| P1 | 旧资产直接复制导致新系统失去通用化抽象 | 坚持“挖矿 -> 抽象 -> 重构”路线 |
| P1 | 首批 lanes 未提前定义，后续 story/batch 难以落 lane | 在规划阶段先给出候选 lane 框架 |
| P1 | 把平台误理解为单向 PRD -> execution，而不是双向自动循环 | 明确 PRD backfeed 与 acceptance close 规则 |
| P1 | harness 仍被当成 provider 附属字段，导致执行语义失真 | 把 harness 升级为独立治理层 |

## Batch Plan

| Batch | Goal | Target Lanes | Status | Gate |
|---|---|---|---|---|
| batch-000A | Phase 0 资源盘点与坑位规划 | planning | completed | 已完成首轮矿脉盘点 |
| batch-000B | 第二轮需求澄清与规划策略确认 | planning | in_progress | 当前轮次 |
| batch-000C | 多角度 research 与标准文档映射 | planning | draft | 以前端产品形态为第一优先挖矿输入 |
| batch-001 | First reviewed planning slice | planning | draft | 用户确认首期 MVP 规划方向 |

## Pre-Code Deliverables

进入代码阶段前，首批应至少形成这些 blocked-human-confirmation 候选文档：

- `candidate-01-requirements-summary.md`
- `candidate-02-function-list.md`
- `candidate-03-entity-attribute-list.md`
- `candidate-04-prototype-list.md`
- `candidate-05-database-design.md`
- `candidate-06-api-documentation.md`
- `candidate-07-backend-development-design.md`

这些文档允许继续修订，但应足以支撑“代码阶段前的最后一次对齐”。

## Approval Boundaries

- Writes outside allowed paths.
- Dependency changes.
- Backend contract or persistence changes without explicit approval.
- Production config, migrations, credentials, auth, tenant logic, deploy, commit, push, merge, PR.
- 在规划未 reviewed 前，不启动正式 OpenClaw 开发任务。
