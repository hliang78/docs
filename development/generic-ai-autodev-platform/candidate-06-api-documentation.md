---
documentStatus: blocked-human-confirmation
topic: generic-ai-autodev-platform
template: 06-接口文档模板
createdAt: 2026-05-17
sourceType: planning-mining
---

# 【接口文档】通用AI自动化平台_规划管理模块_V1.0

## 1. 文档信息

| 项目 | 内容 |
|------|------|
| 系统名称 | 通用 AI 自动化平台 |
| 模块名称 | 规划管理模块 |
| 版本号 | V1.0 |
| 创建日期 | 2026-05-17 |
| 接口基准地址 | [待确认: 后端负责人] |
| 通用响应格式 | [待确认: 后端负责人] |
| 关联文档 | 【需求概要】通用AI自动化平台_V1.0.md<br>【数据库设计】通用AI自动化平台_规划与控制域_V1.0.md |

## 2. 通用说明

当前候选接口默认由自研 `planner/control API` 提供，不直接暴露 `dagengine` 原始接口给前端工作台。
首批代码切片只覆盖 `只读 + 审阅 + 状态推进`，不包含 AI 优化和轻量编辑写入能力。

新增命名冻结约束：

- 本文档属于 API contract 文档，所有对象字段与资源语义继续使用 authoritative planning names。
- 不允许在 API contract 中直接把正式对象名替换成 engine 内部 code names。
- 例如：
  - 文档中继续写 `AutonomousDrivingInput`
  - 继续写 `DecisionEnvelope`
  - 继续写 `ReadinessDecision`
  - 不改写成 `DriveInput / DriveDecision / GoSignal`

### 2.1 通用请求头

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| Content-Type | string | 是 | application/json |
| Authorization | string | [待确认: 后端负责人] | Bearer {token} |

### 2.2 通用响应结构

```json
{
  "success": true,
  "data": {},
  "message": "ok"
}
```

### 2.3 状态码说明

| 状态码 | 说明 |
|--------|------|
| 200 | 成功 |
| 400 | 参数错误 |
| 401 | 未授权 |
| 403 | 无权限 |
| 404 | 资源不存在 |
| 409 | 状态冲突 |
| 422 | 契约校验失败 |
| 500 | 服务器内部错误 |

## 3. 接口列表

### 3.1 Program 列表查询

**接口描述**：获取 program 列表与阶段概览。

**请求信息**

| 项目 | 内容 |
|------|------|
| 接口URL | GET /api/v1/programs |
| 请求方式 | GET |
| Content-Type | application/json |
| 权限要求 | [待确认: 产品负责人] |

**业务规则与校验**

| 规则 | 处理方式 |
|------|----------|
| 只返回规划域 program | [待确认: 后端负责人] |

### 3.2 Program 详情查询

**接口描述**：获取单个 program 详情与文档、batch 概览。

**请求信息**

| 项目 | 内容 |
|------|------|
| 接口URL | GET /api/v1/programs/{programId} |
| 请求方式 | GET |
| Content-Type | application/json |
| 权限要求 | [待确认: 产品负责人] |

### 3.3 Program 文档列表/读取

**接口描述**：读取 `context-brief/program-plan/workstreams/test-matrix/review/final-readiness` 等文档。

**请求信息**

| 项目 | 内容 |
|------|------|
| 接口URL | GET /api/v1/programs/{programId}/documents |
| 请求方式 | GET |
| Content-Type | application/json |
| 权限要求 | [待确认: 产品负责人] |

### 3.4 Batch 列表与详情

**接口描述**：读取 batch 列表、stories、状态、readiness。

**请求信息**

| 项目 | 内容 |
|------|------|
| 接口URL | GET /api/v1/programs/{programId}/batches |
| 请求方式 | GET |
| Content-Type | application/json |
| 权限要求 | [待确认: 产品负责人] |

### 3.5 PlanningReview 状态推进

**接口描述**：推进 review 状态，如 `draft -> reviewed` 或 `reviewed -> blocked-human-confirmation`。

**请求信息**

| 项目 | 内容 |
|------|------|
| 接口URL | POST /api/v1/programs/{programId}/reviews/{reviewId}/transition |
| 请求方式 | POST |
| Content-Type | application/json |
| 权限要求 | [待确认: 产品负责人] |

### 3.6 Batch readiness 校验

**接口描述**：对某个 batch 进行结构化 readiness 预检查，返回阻断项，不触发发布。

**请求信息**

| 项目 | 内容 |
|------|------|
| 接口URL | POST /api/v1/programs/{programId}/batches/{batchId}/readiness-check |
| 请求方式 | POST |
| Content-Type | application/json |
| 权限要求 | [待确认: 产品负责人] |

### 3.7 WorkerProfile 列表与详情

**接口描述**：读取 worker 能力画像与 lane 绑定关系。

**请求信息**

| 项目 | 内容 |
|------|------|
| 接口URL | GET /api/v1/profiles/workers |
| 请求方式 | GET |
| Content-Type | application/json |
| 权限要求 | [待确认: 产品负责人] |

### 3.8 RuntimeEnvProfile 列表与详情

**接口描述**：读取 workspace、toolchain、credential、runtime env 等环境画像摘要。

**请求信息**

| 项目 | 内容 |
|------|------|
| 接口URL | GET /api/v1/profiles/runtime-envs |
| 请求方式 | GET |
| Content-Type | application/json |
| 权限要求 | [待确认: 产品负责人] |

### 3.9 Ops Summary / Incident Summary

**接口描述**：读取某个 program 或 lane 的 probe、incident、repair 摘要。

**请求信息**

| 项目 | 内容 |
|------|------|
| 接口URL | GET /api/v1/programs/{programId}/ops-summary |
| 请求方式 | GET |
| Content-Type | application/json |
| 权限要求 | [待确认: 产品负责人] |

### 3.10 DecisionEnvelope 读取

**接口描述**：读取某个 program、batch 或 runtime object 的最新统一决策输出，供右栏、结果条、审核摘要使用。

**请求信息**

| 项目 | 内容 |
|------|------|
| 接口URL | GET /api/v1/decision-envelopes/{ownerType}/{ownerId} |
| 请求方式 | GET |
| Content-Type | application/json |
| 权限要求 | [待确认: 产品负责人] |

**命名规则**

| 规则 | 处理方式 |
|------|----------|
| 返回对象 contract 使用 `DecisionEnvelope` authoritative 字段语义 | 已冻结 |
| engine 内部可映射到 `DriveDecision`，但 API 对外不暴露该 code name | 已冻结 |

### 3.11 ReadinessDecision 读取

**接口描述**：读取某个 program 或 batch 的最新 readiness 正式结论及 projection。

**请求信息**

| 项目 | 内容 |
|------|------|
| 接口URL | GET /api/v1/readiness-decisions/{ownerType}/{ownerId} |
| 请求方式 | GET |
| Content-Type | application/json |
| 权限要求 | [待确认: 产品负责人] |

**命名规则**

| 规则 | 处理方式 |
|------|----------|
| API contract 对外仍使用 `ReadinessDecision` authoritative 名称 | 已冻结 |
| 前端文案可解释为“发车信号”，但不替换 API 字段名 | 已冻结 |

## 4. 接口汇总表

| 序号 | 功能 | 请求方式 | URL | 说明 |
|------|------|----------|-----|------|
| 1 | Program 列表 | GET | /api/v1/programs | 首页数据源 |
| 2 | Program 详情 | GET | /api/v1/programs/{programId} | 工作台数据源 |
| 3 | 文档读取 | GET | /api/v1/programs/{programId}/documents | 文档视图数据源 |
| 4 | Batch 列表/详情 | GET | /api/v1/programs/{programId}/batches | Batch 审核视图数据源 |
| 5 | Review 状态推进 | POST | /api/v1/programs/{programId}/reviews/{reviewId}/transition | 审阅状态推进 |
| 6 | Batch readiness 校验 | POST | /api/v1/programs/{programId}/batches/{batchId}/readiness-check | readiness 预检查 |
| 7 | WorkerProfile 列表 | GET | /api/v1/profiles/workers | worker 画像摘要 |
| 8 | RuntimeEnvProfile 列表 | GET | /api/v1/profiles/runtime-envs | 环境画像摘要 |
| 9 | Ops Summary | GET | /api/v1/programs/{programId}/ops-summary | probe/incident/repair 摘要 |
| 10 | DecisionEnvelope 读取 | GET | /api/v1/decision-envelopes/{ownerType}/{ownerId} | 统一决策输出 |
| 11 | ReadinessDecision 读取 | GET | /api/v1/readiness-decisions/{ownerType}/{ownerId} | readiness 正式结论 |

## 5. 当前真实规划事实

- 这些接口目前是候选接口面，不代表已存在代码。
- 其设计目标是支撑首期 `program -> docs -> batch` 最小闭环。
- 接口提供者当前倾向于自研薄层 `planner/control API`，而不是引入大型 AI workflow 编排框架。
- profile / incident / repair 摘要已经成为首期必须预留的读取面。
- `WorkspaceProfile / ToolchainProfile / CredentialBinding` 独立对象化已确认，因此 profile 读取接口按分层对象设计。
- `PlatformIncident` 作为 repair 平面一等对象已确认，因此 ops 摘要必须包含 incident 投影。
- 首期这些接口由同一个 `Go + Gin` 后端进程统一暴露。
- 前端已确认采用显式 `React` 工作台栈，因此接口更适合返回页面级 read model，而不是让前端在深层组件中拼多源数据。

## 6. AI 推导建议

- `documents` 资源可返回文档状态、待确认计数、最后更新时间等元数据。[待人工确认: 前端负责人]
- `ops-summary` 聚合 `PreflightProbe`、`PlatformIncident`、`RepairRun` 的只读投影方向已确认，避免前端拼多源数据。
- `program detail`、`documents`、`batches` 最好直接返回 workbench 可消费的 read model，方向已确认。
- `batches` 资源应直接返回 blockers summary、missing fields summary、release gate summary，方便 Batch 审核面板固定摘要条消费。
- `readiness-check` 调用后，前端建议同时刷新右栏决策 read model，并返回可用于结果条的简短摘要。
- API contract 层应坚持 authoritative object names；自动驾驶短名只保留在 engine 内部实现与桥接函数层。

## 7. 规划缺口

- 鉴权模型未确认。
- 文档内容返回已确认采用 `markdown + structured metadata` 混合形态。
- review 状态推进是否与审批动作复用一套 transition API，仍待确认。

## 8. 代码事实来源清单

- `docs/prd-autodev/generic-ai-autodev-platform/workstreams/01-frontend-pages.md`
- `docs/prd-autodev/generic-ai-autodev-platform/dagengine-kernel-mapping.md`
- `docs/prd-autodev/generic-ai-autodev-platform/openclaw-control-plane-mapping.md`
- `docs/prd-autodev/generic-ai-autodev-platform/prd-planning-plane-mapping.md`
- `docs/prd-autodev/generic-ai-autodev-platform/technical-selection.md`
- `docs/prd-autodev/generic-ai-autodev-platform/runtime-governance-and-super-repair.md`
- `docs/prd-autodev/generic-ai-autodev-platform/backend-framework-process-decision.md`
- `docs/prd-autodev/generic-ai-autodev-platform/autonomous-driving-engine-naming-freeze.md`
