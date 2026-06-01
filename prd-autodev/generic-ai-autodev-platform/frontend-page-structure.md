---
topic: generic-ai-autodev-platform
kind: full-stack
title: 自动驾驶系统
createdAt: 2026-05-17T10:40:32+0800
status: draft
---

# 前端页面结构与组件分解

## 1. 目的

把前端工作台决策继续推进到“可直接切前端代码 stories”的粒度：明确页面草图、区块职责、组件边界、数据依赖和首批切片。

## 2. 顶层路由结构

```text
/programs
/programs/:programId?mode=docs&doc=context-brief
/programs/:programId?mode=batch&batch=batch-001
```

说明：

- 只保留两级主路由。
- program 内部通过 query 驱动主模式切换。
- query 要支持刷新恢复和链接分享。
- 首期不单独开放 `mode=ops`。
- 同一 program 内切换 `docs` / `batch` 时，建议保留上一次选中的 `doc` / `batch`。

## 3. 页面草图

## 3.1 Program 首页草图

```text
+----------------------------------------------------------------------------------+
| 自动驾驶系统 / Programs                               搜索 | 阶段 | 状态 |
+----------------------------------------------------------------------------------+
| Filters                    | Program Table                                      |
| - phase                    | ------------------------------------------------- |
| - status                   | 名称 | 当前阶段 | 文档状态 | batch状态 | 更新时间 |
| - owner                    | ------------------------------------------------- |
|                            | 自动驾驶系统 ...                                 |
|                            | ...                                              |
|----------------------------+--------------------------------------------------|
| 右侧弱摘要栏                                                             |
| - 待优先处理 program                                                     |
| - 最近 batch 变更                                                        |
| - 待确认项数量                                                           |
+----------------------------------------------------------------------------------+
```

首页主要回答：

- 当前有哪些 program
- 哪个 program 正在卡住
- 哪个值得优先进入

## 3.2 Program 工作台草图

```text
+--------------------------------------------------------------------------------------------------+
| 返回 Programs | 自动驾驶系统 | alignment-ready | draft batch | blockers: 3      |
+--------------------------------------------------------------------------------------------------+
| 左导航树                       | 中央内容区                                    | 右侧决策栏       |
|--------------------------------+-----------------------------------------------+-------------------|
| Program 概览                   | Docs Mode 或 Batch Mode                       | 当前阶段          |
| 文档目录                        |                                               | ready / not ready |
| - context-brief               | [文档标题/批次标题]                           | blockers 列表      |
| - program-plan                | [状态标签] [更新时间]                         | missing docs      |
| - test-matrix                 | -------------------------------------------   | invalid fields    |
| - review                      | 主体内容 / story表 / 依赖关系 / 状态说明      | next action       |
| - final-readiness             |                                               | refs              |
| Batch 列表                    |                                               |                   |
| - batch-001                   |                                               |                   |
| - batch-002                   |                                               |                   |
|                                |                                               | profile summary   |
|                                |                                               | incident summary  |
+--------------------------------------------------------------------------------------------------+
```

工作台主要回答：

- 我现在看的是什么对象
- 它当前是什么状态
- 要进入下一步还差什么

## 4. 模式级结构

## 4.1 Docs Mode

### Header 区

- 文档标题
- doc type
- `draft/reviewed/blocked-human-confirmation`
- updatedAt
- related batch count

### Body 区

- markdown 正文
- 文档分节目录
- 待确认项高亮

### Footer / Side Actions

- related batches
- related workstreams
- future actions 占位

## 4.2 Batch Mode

### Header 区

- batch 标题
- batch status
- execution mode
- target lanes
- release gate
- compact batch summary strip

### Body 区

- story table
  - id
  - title
  - lane
  - status
  - dependsOn
  - validation
- stopConditions
- evidencePolicy 摘要

### `compact batch summary strip` 首期字段

- blockers count
- missing fields count
- release gate summary

### Footer / Side Actions

- related docs
- publish blockers
- future actions 占位

## 5. 首批组件分解

## 5.1 Shell 组件

| 组件 | 职责 | 首批必做 |
|---|---|---|
| `ProgramListPage` | Program 首页整体容器 | 是 |
| `ProgramWorkbenchPage` | Program 工作台整体容器 | 是 |
| `WorkbenchHeader` | 标题、阶段标签、返回入口 | 是 |
| `WorkbenchLayout` | 三栏骨架布局 | 是 |

## 5.2 首页组件

| 组件 | 职责 | 首批必做 |
|---|---|---|
| `ProgramFilterPanel` | phase/status/search 筛选 | 是 |
| `ProgramTable` | program 列表主体 | 是 |
| `ProgramSummaryRail` | 最近 batch / 待确认摘要 | 是 |
| `ProgramPhaseTag` | 当前阶段标签 | 是 |

## 5.3 工作台导航组件

| 组件 | 职责 | 首批必做 |
|---|---|---|
| `ProgramNavTree` | 左栏 program/doc/batch 导航树 | 是 |
| `DocumentNavGroup` | 文档目录分组 | 是 |
| `BatchNavGroup` | batch 列表分组 | 是 |

默认展开策略建议：

- `Program 概览` 默认展开
- 当前 mode 对应分组默认展开
- 非当前 mode 分组默认收起
- 同一 program 内记忆用户上一次展开状态

## 5.4 文档模式组件

| 组件 | 职责 | 首批必做 |
|---|---|---|
| `DocumentViewer` | 文档正文渲染 | 是 |
| `DocumentMetaBar` | 状态、更新时间、doc type、structured metadata 摘要 | 是 |
| `DocumentOutline` | 文档分节或锚点目录 | 否，可后补 |
| `PendingItemsPanel` | 待确认项提取展示 | 是 |
| `RelatedBatchLinks` | 相关 batch 跳转 | 是 |

## 5.5 Batch 模式组件

| 组件 | 职责 | 首批必做 |
|---|---|---|
| `BatchMetaBar` | batch 基础信息 | 是 |
| `BatchSummaryStrip` | blockers / missing fields / release gate 紧凑摘要 | 是 |
| `StoryTable` | stories 主表 | 是 |
| `StoryDependencyGraph` | dependsOn 可视化 | 否，首批先文字/标签 |
| `StopConditionList` | stop conditions 摘要 | 是 |
| `PublishBlockerPanel` | readiness 阻断项 | 是 |

## 5.6 决策栏组件

| 组件 | 职责 | 首批必做 |
|---|---|---|
| `ReadinessDecisionRail` | 右栏整体容器 | 是 |
| `PhaseSummaryCard` | 当前阶段与总体状态 | 是 |
| `ReadinessStatusBadge` | ready / not ready 标签 | 是 |
| `BlockerList` | 阻断项列表 | 是 |
| `ProfileSummaryCard` | worker/runtime env 只读摘要 | 是 |
| `IncidentSummaryCard` | preflight/incident/repair 只读摘要 | 是 |
| `NextActionPanel` | 下一步建议动作 | 是 |
| `ReferenceLinksPanel` | 相关文档/批次引用 | 是 |
| `ReadinessResultBanner` | readiness-check 的临时结果反馈条 | 是 |

`ReadinessResultBanner` 默认规则建议：

- `passed`：自动消失，停留 `5s`
- `blocked`：不自动消失
- `error`：不自动消失

### `ProfileSummaryCard` 首期字段

- worker profile name
- runtime env profile name
- workspace profile name
- toolchain profile name
- readiness tag

### `IncidentSummaryCard` 首期字段

- latest preflight status
- open incidents count
- latest incident severity
- latest incident status
- latest repair status
- next action

### 首期不显示

- long probe history
- incident timeline
- raw logs
- repair detail body
- any control buttons

## 6. 数据依赖草案

## 6.1 首页

- `GET /api/v1/programs`
  - program 列表
  - current phase
  - docs summary
  - batch summary
  - readiness summary

## 6.2 工作台

- `GET /api/v1/programs/{programId}`
  - program header
  - doc list
  - batch list
  - readiness summary
  - profile summary
  - incident summary

## 6.3 Docs Mode

- `GET /api/v1/programs/{programId}/documents`
  - doc meta
  - doc content
  - structured metadata
  - pending items
  - related batches

## 6.4 Batch Mode

- `GET /api/v1/programs/{programId}/batches`
  - batch meta
  - stories
  - stop conditions
  - release gate
  - blocker summary
  - missing fields summary

## 6.5 Frontend State Ownership

- URL/query state:
  - `mode`
  - `doc`
  - `batch`
  - 首页 filters
- query state:
  - program list
  - program detail
  - documents read model
  - batch read model
  - decision rail summary
  - driver learning summary
  - takeover summary
  - end signal summary
- XState state:
  - review transition
  - readiness-check
  - decision rail finite state
- local UI state:
  - nav expand/collapse
  - temporary highlights
  - local sort/open state

详细冻结见：

- [frontend-state-query-decision.md](/Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/generic-ai-autodev-platform/frontend-state-query-decision.md)

## 7. 首批不进入的组件

- `AiAssistDrawer`
- `LightEditDrawer`
- `PublishToOpenClawButton`
- `RuntimeControlPanel`
- `ModelProfileEntry`

这些都建议在 `batch-002` 或更后批次再进入。

## 8. 推荐前端代码切片

### Slice A - `frontend-shell`

- `ProgramListPage`
- `ProgramWorkbenchPage`
- `WorkbenchLayout`
- `WorkbenchHeader`

### Slice B - `docs-read`

- `ProgramNavTree`
- `DocumentViewer`
- `DocumentMetaBar`
- `PendingItemsPanel`

### Slice C - `batch-review`

- `BatchMetaBar`
- `BatchSummaryStrip`
- `StoryTable`
- `StopConditionList`
- `PublishBlockerPanel`

### Slice D - `state-summary`

- `ReadinessDecisionRail`
- `ReadinessResultBanner`
- `PhaseSummaryCard`
- `BlockerList`
- `ProfileSummaryCard`
- `IncidentSummaryCard`
- `NextActionPanel`

## 9. 当前建议拍板项

1. 首页采用 `Filter Panel + Program Table + Summary Rail`。
2. 工作台采用 `Nav Tree + Main Content + Decision Rail`。
3. 首批不做 drawer 式 AI/编辑能力。
4. `profile / incident` 只读摘要纳入首批右侧决策栏。
5. 依赖图首批先文本化，不急着做图形化。

## 9.1 首期不独立成 Ops Mode 的原因

- 摘要类信息更适合和 `readiness / blockers / next action` 放在同一个决策面板里。
- 如果单独开 `Ops Mode`，用户在文档判断、batch 判断、环境判断之间会来回切模式，增加认知切换。
- 首期还没有 profile 编辑、incident 时间线、repair 操作入口，独立模式的信息密度不够，容易形成“空模式”。

## 9.2 当前已确认

- 工作台内部采用左侧目录树切换。
- `profile / incident` 摘要挂在右侧决策栏。
- 摘要卡片采用紧凑信息密度，不做长列表和时间线。

## 9.3 后续升级条件

- 只有在需要 profile 编辑、incident 时间线、repair run 详情、probe 历史比较时，再考虑独立 `Ops Mode`。

## 10. 当前结论

如果你认可这份结构稿，前端层面已经足够支撑下一轮“代码前最终对齐”和后续前端 story 切分，不需要再停留在抽象页面讨论阶段。
