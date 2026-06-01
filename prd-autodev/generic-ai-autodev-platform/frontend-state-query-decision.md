---
topic: generic-ai-autodev-platform
kind: full-stack
title: 前端状态与查询架构决策稿
createdAt: 2026-05-17T23:20:00+0800
program: true
status: draft
---

# Frontend State And Query Decision

## Purpose

- 这份文档专门冻结 `frontend-admin/` 在首期 MVP 的前端状态与查询架构：
  - URL 负责什么
  - TanStack Query 负责什么
  - XState 负责什么
  - 哪些状态不应该进入全局状态机

## Current Context

- 前端技术方向已确认采用：
  - `React + TypeScript + Vite + TanStack Router + TanStack Query + shadcn/ui + XState`
- 首期产品闭环已确认：
  - `Program -> Docs -> StoryBatch`
- 首期交互边界已确认：
  - `只读 + 审阅 + 状态推进`
- 首期不纳入：
  - `AI 多轮优化`
  - `轻量编辑`
  - `OpenClaw 发布`
  - `运行态控制`

## Core Principle

- URL 管导航真相
- Query 管服务端读取真相
- XState 管有限状态交互
- 局部组件状态只管短生命周期展示细节

一句话：

- 不把所有前端状态都塞进 XState，也不把服务端读取状态伪装成本地应用状态。

## Recommended Ownership Matrix

| 状态类型 | 推荐承载层 | 首期示例 |
|---|---|---|
| 路由/选择态 | `TanStack Router` search params | `mode=docs`、`doc=review`、`batch=batch-001` |
| 服务端读取态 | `TanStack Query` | program 列表、program 详情、docs、batches、decision rail、driver learning、takeover summary、end signal summary |
| 有限状态交互 | `XState` | review transition、readiness-check、右栏决策状态 |
| 短生命周期 UI 态 | local component state | 左栏折叠、行 hover、局部展开 |

## 1. URL State Recommendation

首期 URL 应承载：

- 当前 program
- 当前 mode
- 当前 document
- 当前 batch
- 首页筛选条件

推荐形态：

```text
/programs
/programs/:programId?mode=docs&doc=context-brief
/programs/:programId?mode=batch&batch=batch-001
```

### Why

- 支持刷新恢复
- 支持分享链接
- 支持浏览器历史回退
- 对 AI 自动开发更友好，页面状态来源一眼可读

### What Not To Put In URL

- 左栏是否展开
- 右栏某个小卡片是否折叠
- 临时 hover / focus
- 正在提交中的瞬时状态

## 2. Query State Recommendation

`TanStack Query` 负责所有首期服务端读取面：

- `programs list`
- `program detail`
- `documents read model`
- `batch read model`
- `decision rail summary`
- `driver learning summary`
- `takeover summary`
- `end signal summary`

推荐 query key 语义：

```text
["programs", filters]
["program", programId]
["program-documents", programId]
["program-batches", programId]
["program-decision-rail", programId]
["program-driver-learning", programId]
["program-takeover", programId]
["program-end-signals", programId]
```

### Workbench Loading Recommendation

建议首屏并行拉取：

- `["program", programId]`
- `["program-decision-rail", programId]`
- `["program-driver-learning", programId]`
- `["program-takeover", programId]`
- 当前 mode 对应的主内容 query

当前 mode 为 `docs` 时：

- 拉 `["program-documents", programId]`

当前 mode 为 `batch` 时：

- 拉 `["program-batches", programId]`

如果当前页面需要在 program/batch 头部直接显示结束信号摘要，则并行补拉：

- `["program-end-signals", programId]`

另一 mode 的内容不阻塞首屏。
页面稳定后，可低优先级预取另一 mode 的 meta 或摘要，但不预取完整正文。

### Read Model Recommendation

前端不直接消费原始后端响应拼 UI。

推荐在前端保留轻量 read model adapter，把接口响应映射成：

- `ProgramListItemView`
- `ProgramWorkbenchView`
- `DocumentView`
- `BatchReviewView`
- `DecisionRailView`
- `DriverLearningSummaryView`
- `TakeoverSummaryView`
- `EndSignalSummaryView`

这样做的好处：

- 降低组件直接耦合后端字段
- 方便后续文档正文、状态摘要、待确认项继续演进
- 更适合 AI 自动开发按组件与 view model 拆任务

## 3. XState Recommendation

XState 首期不做“全局真相存储器”，只做有限状态交互编排。

首期推荐机器：

### `workbench-mode-machine`

职责：

- 解释当前 workbench 是 `docs` 还是 `batch`
- 协调 query params 与主区渲染切换

### `review-transition-machine`

职责：

- 承接 review 状态推进动作
- 管理 `idle -> confirming -> submitting -> success/failure`

### `readiness-check-machine`

职责：

- 承接 batch readiness 预检查
- 管理 `idle -> checking -> passed/blocked/error`

### `decision-rail-machine`

职责：

- 决策栏的聚合显示态
- 承接融合后的风险与置信度可视状态
- 例如：
  - `loading`
  - `ready`
  - `blocked`
  - `attention`

### `takeover-action-machine`

职责：

- 承接右栏或消息面触发的接管动作
- 管理 `idle -> confirming -> submitting -> applied/failed`

### What XState Should Not Own

- 整个 program 列表数据
- 全量文档正文缓存
- batch story 原始列表
- profile / incident 原始读取结果

这些都应留给 `TanStack Query`。

## 4. Local UI State Recommendation

仅保留短命、纯展示类状态在组件内：

- nav group expand/collapse
- row hover / selected visuals
- temporary panel open/close
- local table sort indicator

原则：

- 不可分享、不可恢复、非业务真相的状态，不要上升成全局 contract

## 5. Component And Data Boundary

推荐页面职责：

### `ProgramListPage`

- 负责 filters -> query params -> list query
- 不直接关心 workbench 细节

### `ProgramWorkbenchPage`

- 负责读取 `programId`
- 负责解释 `mode/doc/batch`
- 负责装配左栏、中栏、右栏三块 read model

### `DocumentViewer`

- 只消费 `DocumentView`
- 不自己调用多个后端接口拼装

### `StoryTable`

- 只消费 `BatchReviewView`
- 不自己推导 release blockers

### `ReadinessDecisionRail`

- 只消费 `DecisionRailView`
- 不自己并发请求多份数据后做前端临时拼接

## 6. API Shaping Implication

为了支持这个前端架构，后端 API 应尽量返回：

- 页面级 read model
- 而不是要求前端手工拼多个分散 truth 文件

例如：

- `GET /api/v1/programs/{programId}` 应足够支撑 workbench header + nav + rail summary
- `GET /api/v1/programs/{programId}/decision-rail` 应返回：
  - readiness summary
  - current intent summary
  - latest learning summary
  - active takeover summary
  - available takeover actions
  - latest end signal summary
  - risk/confidence fusion summary
  - top reasons
- `GET /api/v1/programs/{programId}/documents` 应返回：
  - document meta
  - document content
  - structured metadata
  - pending items
  - related references
- `GET /api/v1/programs/{programId}/batches` 应返回：
  - batch meta
  - stories
  - blockers
  - release gate summary
- `GET /api/v1/programs/{programId}/driver-learning` 应返回：
  - recent learning signals
  - latest learning record
  - recommended adjustments summary
- `GET /api/v1/programs/{programId}/takeover` 应返回：
  - active takeover request
  - latest takeover decision
  - allowed takeover actions
- `GET /api/v1/programs/{programId}/end-signals` 应返回：
  - latest end signal
  - latest end signal evaluation
  - pending signal count
  - timeline items for detail header / panel

## 7. AI-Friendly Frontend Rules

为了让后续 AI 自动开发更稳定，前端应保持：

1. 页面容器与展示组件分离
2. query key 命名固定
3. 右栏 read model 不允许由前端临时拼接 learning/takeover/end-signal/risk 真相
4. 接管动作必须走正式 mutation，而不是局部 UI 假状态
5. view model 命名固定
6. 状态机只负责有限交互，不负责全量数据缓存
7. URL query 是 workbench 切换的权威来源

## 8. Current Recommendation

1. `TanStack Router` 管路由与 query state
2. `TanStack Query` 管服务端读取状态
3. `XState` 只管 review/readiness/decision 这类有限状态交互
4. 局部 UI 细节留在组件本地状态
5. 页面消费 read model，而不是在深层组件临时拼接口

## Remaining Decisions

1. `ProgramWorkbenchPage` 是否接受“首屏并行拉 program + decision rail + 当前 mode 内容”的推荐
2. review transition 的 modal 具体信息密度与按钮文案
3. readiness-check 结果展示采用右栏刷新、面板结果区，还是双重反馈
4. 结束信号摘要是只放右栏，还是同时在 batch/program 详情头部露出一行

## 9. Fusion Note

- `DecisionRailView` 不应退化成一个随手拼出来的 summary box。
- 它应是“自动辅助驾驶系统 + AI 司机”在前端上的统一驾驶舱摘要：
  - readiness 告诉我们能不能发车
  - current intent 告诉我们 AI 司机当前想怎么推进
  - learning 告诉我们司机最近学到了什么
  - takeover 告诉我们外部是否正在接管或准备接管
  - end signal 告诉我们局部工作结束到了哪一层，但还没有闭环到哪一层
  - risk/confidence 告诉我们此刻为什么该继续、该暂停、还是该升级处理
- 字段级融合 contract 见 [decision-rail-fusion-contract.md](/Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/generic-ai-autodev-platform/decision-rail-fusion-contract.md)。
