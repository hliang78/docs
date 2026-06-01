---
topic: generic-ai-autodev-platform
kind: full-stack
title: 新目录承接结构决策稿
createdAt: 2026-05-17T17:35:00+0800
program: true
status: draft
---

# Directory Structure Decision

## Purpose

- 这份文档专门回答一个实现前必须冻结的问题：
  - 这个新程序根目录到底怎么承接自动驾驶系统
  - 首期是否拆成多服务、多仓、多进程
  - 前后端、引擎适配、对象存储、evidence、runtime cache 应该如何落位

## Current Decision

- 程序根目录固定为：
  - `/Users/huangliang/project/OneOPS-ALL/generic-ai-autodev`
- 首期采用：
  - `单目录 monorepo`
  - `一个前端应用`
  - `一个后端应用`
  - `后端内部逻辑分层`
- 首期明确不采用：
  - 多 repo
  - 多独立 API 服务先行拆分
  - 一开始就上复杂微服务结构

一句话结论：

- 首期应被理解为“一个新程序根目录”，不是“一组松散小项目集合”。

## Why This Structure

## 1. 符合 MVP 目标

- 当前目标是先跑通：
  - `Program -> Docs -> StoryBatch`
  - planning/control/readiness
  - profile / incident 只读摘要
- 这还不需要为了“未来可能拆分”先引入多服务复杂度。

## 2. 避免目录层面过度工程化

- 如果首期就拆成：
  - `planner-api`
  - `control-api`
  - `ops-governance-api`
  - `repair-orchestrator`
  多个独立应用
- 会立刻引入：
  - 多启动入口
  - 多配置
  - 多日志
  - 多验证脚本
  - 多部署语义
- 这和当前“先规划闭环、后稳定开工”的节奏不匹配。

## 3. 保留未来拆分空间

- 虽然物理上先是一个后端应用，
- 但逻辑上仍然分成：
  - planning
  - control
  - ops governance
  - repair
  - engine adapter
  - storage / evidence
- 这样后续如果某一层真的需要独立服务化，再拆也不晚。

## Recommended Root Layout

```text
generic-ai-autodev/
├── README.md
├── docs/
│   ├── 000-resource-mining/
│   ├── 100-planning/
│   ├── 200-development/
│   └── 300-evidence/
├── frontend-admin/
├── backend/
│   ├── src/
│   │   ├── app/
│   │   ├── modules/
│   │   │   ├── planning/
│   │   │   ├── batch-review/
│   │   │   ├── ops-governance/
│   │   │   ├── repair/
│   │   │   └── readiness/
│   │   ├── adapters/
│   │   │   ├── dagengine/
│   │   │   ├── mysql/
│   │   │   ├── filesystem/
│   │   │   └── secrets/
│   │   ├── domain/
│   │   └── shared/
│   ├── tests/
│   └── scripts/
├── schemas/
├── artifacts/
│   ├── evidence/
│   └── exports/
├── runtime-cache/
└── scripts/
```

## Directory Roles

### `docs/`

- 存自动驾驶系统自己的沉淀文档
- 不直接等于主仓 `docs/` 的替代物
- 建议语义：
  - `000-resource-mining/`：原始资产与导入材料
  - `100-planning/`：program、alignment、architecture 冻结稿
  - `200-development/`：代码阶段后的设计与实现文档
  - `300-evidence/`：本程序自身的验证与验收证据

### `frontend-admin/`

- 承接显式 React 工作台应用
- 借鉴 `React-Admin` 的资源/列表/详情模式，但不直接采用其脚手架
- 只负责前端工作台，不混入后端运行脚本

### `backend/`

- 首期唯一后端程序入口
- 物理上一个应用，逻辑上多模块
- 这是首期最关键的收束点

### `schemas/`

- 放对象 schema、DTO、共享 contract
- 用于前后端共享类型和结构化约束

### `artifacts/`

- 放自动驾驶系统运行后产生的 export/evidence
- 只存导出与证据，不存 authoritative truth

### `runtime-cache/`

- 放 prompt cache、probe cache、临时快照、调试 trace
- 可以丢失，不能参与真相判定

### `scripts/`

- 放新程序根目录下的本地开发/验证脚本
- 只服务新程序根目录，不和主仓全局脚本混用

## Backend Structure Recommendation

## Physical Shape

- 一个应用：
  - `backend/`
- 不在首期拆成多个独立部署单元。

## Logical Shape

### `modules/planning`

- `Program`
- `PlanningDocument`
- `Workstream`
- `StoryBatch`
- `PlanningReview`

### `modules/batch-review`

- batch 审核
- publish readiness
- story release gate

### `modules/ops-governance`

- `WorkerProfile`
- `WorkspaceProfile`
- `ToolchainProfile`
- `CredentialBinding`
- `RuntimeEnvProfile`
- `PreflightProbe`
- `PlatformIncident`

### `modules/repair`

- `RepairRun`
- `SuperRepairCoordinator`
- `RepairPlaybook`

### `modules/readiness`

- summary panel
- blocker aggregation
- next action projection

### `adapters/dagengine`

- 对接 `dagengine`
- 只做执行内核适配

### `adapters/mysql`

- authoritative object store

### `adapters/filesystem`

- evidence / export / artifact indexing

### `adapters/secrets`

- `CredentialBinding` 到真实 secret source 的解析层

## Why Not Split APIs First

- 首期前端只需要读：
  - program
  - documents
  - batches
  - readiness
  - profile summary
  - incident summary
- 这些都可以先由一个后端应用暴露。
- 逻辑分层已经足够保护边界，不需要先物理拆分。

## Frontend Structure Recommendation

```text
frontend-admin/
├── src/
│   ├── app/
│   ├── pages/
│   │   ├── programs/
│   │   └── workbench/
│   ├── features/
│   │   ├── docs-read/
│   │   ├── batch-review/
│   │   ├── readiness-summary/
│   │   └── ops-summary/
│   ├── components/
│   ├── data-provider/
│   ├── statecharts/
│   └── shared/
├── public/
└── scripts/
```

要求：

- `ops-summary` 在首期只是右栏摘要能力，不是独立页面系统。
- `AI assist` 与 `light edit` 不进入首批目录主线。

## Relation To Main Repo Docs

- 主仓 `docs/prd-autodev/generic-ai-autodev-platform/` 仍然是当前规划主战场。
- `generic-ai-autodev/docs/` 是新程序自己的内部 docs 根目录。
- 在代码前阶段，不需要急着把现有规划文档整体迁过去。
- 推荐等代码阶段启动后，再做一次“规划文档 -> 程序内 docs”的受控映射。

## Recommended Validation Baseline

在目录冻结阶段，先冻结“验证承载位置”，不冻结最终命令细节：

- 前端验证脚本放：
  - `generic-ai-autodev/frontend-admin/scripts/`
- 后端验证脚本放：
  - `generic-ai-autodev/backend/scripts/`
- 程序级聚合验证脚本放：
  - `generic-ai-autodev/scripts/`

这样后续补具体命令时，不会再因为目录语义摇摆。

## Current Recommendation

1. 接受现有新程序根目录作为唯一程序根目录。
2. 接受首期采用“一个前端应用 + 一个后端应用 + 后端内部逻辑分层”。
3. 接受 `artifacts/` 和 `runtime-cache/` 作为程序内明确目录，而不是继续散落在各处。
4. 接受首期不物理拆 `planner-api/control-api/ops-governance-api` 多服务。
5. 接受代码启动后，再把当前规划文档逐步映射进 `generic-ai-autodev/docs/`。
