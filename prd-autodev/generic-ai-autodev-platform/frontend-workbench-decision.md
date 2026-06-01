---
topic: generic-ai-autodev-platform
kind: full-stack
title: 自动驾驶系统
createdAt: 2026-05-17T10:40:32+0800
status: draft
---

# 前端工作台决策稿

## 1. 目的

在进入代码阶段前，把前端工作台最容易摇摆的几个结构问题先收束：路由模式、布局模式、首批交互边界、以及“借鉴 `React-Admin` 模式但不直接采用其脚手架”的前端承接方式。

## 2. 设计上下文

沿用 OneOPS 当前 product UI 方向：

- 面向高频运维/规划用户
- 追求紧凑、可检视、可复制、可核查
- 不做营销式 dashboard
- 不隐藏不确定性
- 以浅色、克制、信息密度高的工作台形态为主

这意味着新工作台更像“规划控制室”，而不是“AI 可视化大屏”。

## 3. 推荐结论

### 3.1 路由模式

推荐：`双层路由 + 单工作台内切换`

#### 顶层路由

- `/programs`
  - Program 首页，承接 Topic/Program 列表
- `/programs/:programId`
  - Program 工作台，承接文档、batch、readiness

#### 工作台内切换

不要把每个文档、每个 batch 都做成完全独立页面。

推荐在 `/programs/:programId` 下，通过 query/state 切换工作台主视图：

- `mode=docs`
- `mode=batch`
- `doc=context-brief|program-plan|workstream|test-matrix|review|final-readiness`
- `batch=batch-001`

#### 为什么这样选

- 比“全多路由”更适合工作台心智，不会让用户在同一个 program 内频繁跳页。
- 比“全单页无路由状态”更适合保留可分享链接、刷新恢复、历史回退。
- 更贴合“借鉴 `React-Admin` 资源心智”的工作台模式：列表页一个 route，详情页一个 route，详情页内部做自定义布局。

### 3.2 布局模式

推荐：`首页双栏，工作台三栏`

#### Program 首页

- 左侧：筛选、阶段筛选、状态筛选
- 中部主区：program 列表
- 右侧弱栏：最近 batch、待确认数量、最近更新时间

首页重点是“找 program”和“判断当前值得点哪个”，不是直接进入深度编辑。

#### Program 工作台

- 左栏：program 导航树
  - program 基本信息
  - 文档目录
  - batch 列表
- 中栏：主工作区
  - 文档阅读视图 或 batch 审核视图
- 右栏：决策/状态栏
  - 当前阶段
  - reviewed/draft 状态
  - readiness blockers
  - profile / incident 只读摘要
  - 待人工确认项
  - 下一步建议动作

#### 为什么这样选

- 三栏能同时保留“上下文、内容、决策”，很适合规划型工作台。
- 比单栏 tab 更少来回切换。
- 比把所有内容都塞成卡片式 dashboard 更符合 OneOPS 现有“控制室”语言。
- 左侧目录树切换比 tabs 更适合当前文档数量、batch 数量和后续扩展的对象层级。

### 3.3 文档阅读与 Batch 审核关系

推荐：`同一工作台中的两个主模式，不做两个平级页面系统`

#### Docs Mode

中心是文档正文与状态信息：

- 文档标题
- 文档状态
- 最近更新
- 待确认项
- 相关 batch 引用

#### Batch Mode

中心是 StoryBatch/RuntimeStory 审核：

- batch 状态
- execution mode
- stories 列表
- lane
- dependsOn
- stopConditions
- publish blockers

#### 互相跳转

- 文档里可以跳到相关 batch
- batch 里可以回跳支撑它的文档

这两个模式应互相引用，但不要拆成两个认知割裂的产品。

### 3.3A `profile / incident` 摘要承载位置

推荐：`首期挂在右侧决策栏，不独立成 Ops Mode`

- 当前 MVP 的主任务仍然是跑通 `Program -> Docs -> StoryBatch` 的规划闭环。
- `profile / incident` 在首期更像“能否继续推进”的辅助决策信息，而不是独立操作工作流。
- 如果现在就拆出独立 `Ops Mode`，会引入第三条主导航心智，打断首期工作台收敛。
- 右栏本来就承载 `blockers / next action / readiness`，把 `profile / incident` 摘要放进去，语义最一致。
- 后续只有当 profile 编辑、probe 历史、incident 时间线、repair run 跟踪等运维流程成熟后，再考虑升级成独立 `Ops Mode`。

### 3.4 首批交互边界

推荐：`batch-001 只做 只读 + 审阅 + 状态推进`

首批纳入：

- 浏览 program
- 浏览文档
- 浏览 StoryBatch/RuntimeStory
- 显示 readiness blockers
- 标记 reviewed/draft 类状态推进

首批不纳入：

- AI 多轮优化
- 轻量编辑
- OpenClaw 发布
- 运行态控制

#### 为什么这样选

- 当前最重要的是把“工作台闭环”和“状态闭环”跑通。
- 如果首批同时引入 AI 优化与轻量编辑，会明显拉大前后端边界、权限边界和存储边界。
- 这两个能力更适合进入 `batch-002`。

### 3.5 前端框架使用方式

推荐：`借鉴工作台模式，不直接采用 React-Admin 壳`

#### 直接借鉴的部分

- list
- resource routing
- filters
- detail shell
- data provider 心智

#### 建议采用的显式技术栈

- `React`
- `TypeScript`
- `Vite`
- `TanStack Router`
- `TanStack Query`
- `XState`
- `shadcn/ui`

#### 自定义实现的部分

- Program 工作台三栏布局
- 文档阅读面板
- Batch 审核面板
- readiness 右侧决策栏

#### 为什么这样选

- 继承 `React-Admin` 的工作台心智，但避免被其默认 CRUD 语义绑死
- 对 AI 自动开发更友好：目录显式、组件边界清楚、状态与数据流更直观
- 更适合当前“规划控制室”而不是“后台表单系统”的定位

## 4. 页面结构建议

### 4.1 Program 首页

目标：

- 快速找到目标 program
- 一眼判断当前阶段和阻断程度

主要区块：

- 顶部：标题、搜索、阶段筛选
- 主表：program name / current phase / docs status / batch status / readiness summary / updatedAt
- 右侧摘要：需要优先处理的 program、最近变更、待确认数

### 4.2 Program 工作台

目标：

- 在一个稳定上下文里完成文档审阅与 batch 判断

主要区块：

- 顶部：program 标题、阶段标签、返回列表
- 左栏：文档树 + batch 清单
- 中栏：docs mode 或 batch mode
- 右栏：决策栏

### 4.3 Readiness 决策栏

这块建议做成首批差异化组件，而不是普通统计卡片。

应展示：

- current phase
- ready / not ready
- next required action
- top blockers
- blockers count
- missing docs
- invalid story fields
- worker / runtime env 摘要
- preflight / incident 摘要

#### 摘要密度默认值

首期按“紧凑摘要卡片”处理，不做长列表、时间线、原始日志展开。

`ProfileSummaryCard` 建议只显示：

- 当前 `WorkerProfile`
- 当前 `RuntimeEnvProfile`
- 当前 `WorkspaceProfile`
- 当前 `ToolchainProfile`
- profile readiness 标签

`IncidentSummaryCard` 建议只显示：

- 最近一次 `PreflightProbe` 状态
- open incident 数量
- 最近 incident 的 severity / status
- 最近 `RepairRun` 状态
- 当前 next action

`Batch Mode` 首期还建议固定显示一个紧凑批次摘要条，只放：

- blockers 总数
- missing fields 总数
- release gate 摘要

这样用户在进入 batch 时，不需要先读完整个 story 表，先能判断该批次是否接近 `ready-for-openclaw`。

`readiness-check` 的前端反馈建议采用：

- 主内容区顶部短暂结果条
- 右侧决策栏同步刷新

这样既有动作反馈，也不会把最新真相留在临时提示里。

首期明确不显示：

- secret 明文
- 长 probe 历史
- incident 时间线
- repair 详细日志
- 任意可执行控制按钮

它应该回答一个核心问题：

“这个 program / batch 现在离进入下一步还差什么？”

首期它还要顺带回答：

“当前环境画像和 incident 摘要有没有阻止我们继续推进？”

## 5. 不推荐的方案

### 5.1 全多路由

不推荐把：

- 每个文档
- 每个 batch
- 每个 readiness 视图

都做成独立 route。

问题：

- 工作流被切碎
- 状态上下文丢失
- 页面之间跳转太重

### 5.2 全单页大 dashboard

不推荐把所有内容都塞成一个滚动大页。

问题：

- 文档阅读和 batch 审核会互相抢注意力
- readiness 结论不够明确
- 很容易变成泛化的“AI 工作台拼盘”

### 5.3 首批就做 AI 优化与轻量编辑

不推荐。

问题：

- 权限模型会复杂很多
- 需要额外定义保存策略、版本策略、冲突策略
- 会拖慢最小闭环落地

## 6. 推荐的首批页面范围

### 必做

- Program 首页
- Program 工作台
- Docs Mode
- Batch Mode
- Readiness 决策栏
- `profile / incident` 只读摘要卡片

### 延后

- AI 优化抽屉
- 轻量编辑抽屉
- 模型/profile 配置页
- OpenClaw 控制台
- 独立 `Ops Mode`

## 7.1 本轮确认补充

- 首期前端必须展示 `profile / incident` 的只读摘要。
- 该摘要当前优先建议挂在 `Program 工作台` 的右侧决策栏。
- 独立 `Ops Mode` 后移。
- 工作台内部采用左侧目录树切换。
- 右栏摘要采用“紧凑摘要卡片”默认值。

## 7. 对代码切片的影响

如果采用本决策稿，首批代码切片可以非常清楚：

1. `frontend-shell`
   - 首页与工作台骨架
2. `docs-read`
   - 文档树、文档阅读、状态显示
3. `batch-review`
   - StoryBatch/RuntimeStory/readiness 展示
4. `state-summary`
   - 右栏决策组件

这比把 AI 对话、轻量编辑、发布动作混在第一批更稳。

## 8. 建议拍板项

我建议你直接按下面 6 条拍板：

1. 顶层采用 `Program 首页` + `Program 工作台` 两级路由。
2. 工作台内部采用 `query 驱动 + 左侧目录树切换`。
3. 工作台采用 `左导航 + 中内容 + 右决策栏` 三栏结构。
4. 首期把 `profile / incident` 只读摘要挂在右侧决策栏，不独立成 `Ops Mode`。
5. 右栏摘要采用“紧凑摘要卡片”，不做时间线和日志展开。
6. `AI 优化` 与 `轻量编辑` 延后到 `batch-002`。

## 8.1 进一步建议默认值

已确认继续采用下面 4 条：

1. `docs` / `batch` mode 切换时，保留同一 program 内上一次选中的对象。
2. 左侧导航树采用“按当前 mode 默认展开 + 记忆用户上次展开状态”。
3. `readiness-check` 采用“结果条 + 右栏同步”，其中 `passed` 自动消失，`blocked/error` 不自动消失。
4. review modal 只展示“当前状态 -> 目标状态 + 关键摘要 + 可选备注”，不复制整页详情。

## 9. 当前结论

如果没有新的业务约束，前端专题我建议就按这个方向收口。这样下一轮就可以直接讨论页面结构细节，而不用再在“多路由还是单页、是否独立 Ops Mode、先不先做 AI 优化”这些大方向上反复摇摆。
