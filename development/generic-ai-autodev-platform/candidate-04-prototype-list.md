---
documentStatus: blocked-human-confirmation
topic: generic-ai-autodev-platform
module: frontend-mvp
template: 04-原型清单模板
createdAt: 2026-05-17
sourceType: planning-mining
---

# 【原型清单】通用AI自动化平台_规划管理子系统_PRD与Batch管理模块_V1.0

## 1. 文档信息

| 项目 | 内容 |
|------|------|
| 系统名称 | 通用 AI 自动化平台 |
| 子系统名称 | 规划管理子系统 |
| 功能模块名称 | PRD 与 Batch 管理模块 |
| 版本号 | V1.0 |
| 创建日期 | 2026-05-17 |
| 关联需求文档 | 【需求概要】通用AI自动化平台_V1.0.md |

## 2. 模块概述

### 2.1 业务目标

首期 MVP 先让规划者在 Web 界面中完成从 `program` 到 `文档审阅` 到 `batch readiness` 的最小闭环，为后续 OpenClaw 自动开发提供可审阅、可推进、可发布准备的前端入口。

### 2.2 功能范围

- 浏览 `topic/program` 列表与详情
- 浏览 `context-brief`、`program-plan`、`workstreams`、`test-matrix`、`review`、`final-readiness`
- 浏览并审阅 `batch/stories`
- 识别 `draft/reviewed/ready for OpenClaw` 状态
- 展示 `profile / incident` 只读摘要

不包含：

- 首期不做完整富文本编辑器
- 首期不做 `AI 多轮优化`
- 首期不做 `简单手动编辑`
- 首期不做模型/profile 配置管理主页面
- 首期不做 OpenClaw 运行态全量控制台

## 3. 页面统计

| 类型 | 数量 |
|------|------|
| 主页面 | 2 |
| 子页面 | 2 |
| 弹窗/抽屉 | 0 |
| 统计/分析页 | 0 |
| 合计 | 4 |

## 4. 页面清单

| 页面名称 | 页面类型 | 功能描述 | 核心功能要点 | 关联页面/组件 |
|----------|----------|----------|--------------|----------------|
| Program 首页 | 主页面 | 展示 program/topic 列表与阶段概览 | - 列表浏览<br>- 当前阶段识别<br>- 最近 batch 概览 | Program 工作台 |
| Program 工作台 | 主页面 | 进入某个 program 后查看文档、workstream、batch 全局状态 | - 文档导航<br>- 状态总览<br>- readiness 摘要<br>- profile / incident 摘要 | 文档阅读面板、Batch 审核面板 |
| 文档阅读面板 | 子页面 | 浏览 `context-brief/program-plan/workstreams/test-matrix/review` 等文档 | - 只读查看<br>- draft/reviewed 状态标识<br>- 待确认事项提醒 | Program 工作台 |
| Batch 审核面板 | 子页面 | 浏览 batch、stories、lane、依赖与发布准备状态 | - batch 状态识别<br>- stories 审阅<br>- readiness 判定 | Program 工作台 |

## 5. 页面层级结构

- Program 首页
  - Program 工作台
    - 文档阅读面板
    - Batch 审核面板

## 6. 公共组件

| 组件名称 | 适用范围 | 功能描述 |
|----------|----------|----------|
| Program 状态卡片 | Program 首页、Program 工作台 | 展示 program 当前阶段、batch 概览、readiness 摘要 |
| 文档状态标签 | 文档阅读面板、Batch 审核面板 | 显示 `draft`、`reviewed`、`ready` 等状态 |
| 待确认事项列表 | 文档阅读面板 | 汇总 `[待人工确认]`、`[待补充]` 等信息 |
| Story 依赖展示组件 | Batch 审核面板 | 展示 story、lane、dependsOn、publish readiness |
| Readiness 决策栏 | Program 工作台 | 展示 ready/not-ready、blockers、next action |
| Profile 摘要卡片 | Program 工作台 | 展示 worker/runtime env 只读摘要 |
| Incident 摘要卡片 | Program 工作台 | 展示 preflight/incident/repair 只读摘要 |
| Program 导航树 | Program 工作台 | 展示文档目录与 batch 目录 |

## 7. 页面导航关系

### 7.1 模块内部导航关系

| 源页面 | 触发动作 | 目标页面 | 备注 |
|--------|----------|----------|------|
| Program 首页 | 点击某个 program | Program 工作台 | 携带 topic/program 标识 |
| Program 工作台 | 点击某类文档 | 文档阅读面板 | 根据文档类型切换内容 |
| Program 工作台 | 点击某个 batch | Batch 审核面板 | 展示 stories、状态、依赖 |

### 7.2 模块间导航关系

| 源页面 | 触发动作 | 目标模块/页面 | 备注 |
|--------|----------|---------------|------|
| Batch 审核面板 | 点击 readiness 相关引用 | 文档阅读面板 | 回到相关 PRD/plan/test-matrix 文档 |
| Program 工作台 | 点击后续能力入口 | [待人工确认: 产品负责人] 模型/profile 配置页 | 不属于首批主线 |

## 8. 与其他模块的关联

| 关联模块 | 关联方式 | 说明 |
|----------|----------|------|
| 规划文档管理 | 数据共享 | 读取 `context-brief/program-plan/workstreams/test-matrix/review` |
| Batch 管理 | 数据共享 | 读取 `story-packages/*.json` 与 batch 状态 |
| OpenClaw 执行准备 | 状态推进 | 首期只做发布准备，不直接承接全量运行控制 |

## 9. 当前真实规划事实

- 已确认首期前端优先 `PRD/story 文档与批次管理`。
- 已确认首页必须形成 `program -> docs -> batch` 最小闭环。
- 已确认首期交互以 `只读 + 审阅 + 状态推进` 为主。
- 已确认首期需要展示 `profile / incident` 只读摘要。
- 已确认 `模型/profile 配置管理` 不属于首批主线。
- 已确认 `AI 多轮优化` 与 `简单手动编辑` 后移到后续 batch。

## 10. 候选原型内容

- Program 首页偏“规划总览”，不是运行监控首页。
- Program 工作台偏“文档与批次工作台”，而不是代码 IDE 或 OpenClaw 终端。
- 文档阅读与 Batch 审核分成两个主视图，降低页面认知负荷。
- 推荐采用 `Program 首页` + `Program 工作台` 两级路由，而不是每个文档/批次独立页面。
- 推荐在 Program 工作台中采用 `左导航 + 中内容 + 右决策栏` 三栏结构。
- 推荐工作台内部采用目录树切换，而不是顶部 tabs。
- 推荐首批只实现 `只读 + 审阅 + 状态推进`，把 `AI 优化` 与 `轻量编辑` 延后到后续 batch。
- 推荐首期把 `profile / incident` 摘要挂在右侧决策栏，不独立成 `Ops Mode`。
- 推荐 `profile / incident` 摘要采用紧凑卡片密度，只展示推进决策必需字段。
- 推荐首页采用 `Filter Panel + Program Table + Summary Rail`。
- 推荐工作台采用 `Nav Tree + Main Content + Decision Rail`。
- 推荐首批 Story 依赖先用表格/标签表达，不急于做图形化依赖视图。

## 11. AI 推导建议

- 首页采用 `Filter Panel + Program Table + Summary Rail`，工作台采用 `Nav Tree + Main Content + Decision Rail`，方向已确认。
- 工作台内部采用 query 驱动的 `docs mode / batch mode` + 目录树切换，方向已确认。
- `profile / incident` 摘要首期挂在右侧决策栏，而不是独立 `Ops Mode`，方向已确认。

## 12. 规划缺口

- 是否需要 batch 对比视图，当前未纳入首批。
- `ready for OpenClaw` 的前端交互反馈建议采用 `summary panel 为主 + readiness-check 临时结果条 + 右栏同步刷新`。
- `profile / incident` 摘要后续是否升级成独立 `Ops Mode`，当前未纳入首批。

## 13. 待确认事项

| 序号 | 待确认内容 | 影响页面 | 状态 |
|------|------------|----------|------|
| 1 | Program 工作台采用目录树切换 | Program 工作台、文档阅读面板、Batch 审核面板 | 已确认 |
| 2 | AI 优化延后到 `batch-002` | 文档阅读面板 | 已确认 |
| 3 | 轻量编辑延后到 `batch-002` | Program 工作台 | 已确认 |
| 4 | 首页是否展示后续能力入口占位，如模型/profile 配置 | Program 首页 | 已确认 |
| 5 | `ready for OpenClaw` 的反馈采用 badge、blocker list 还是 summary panel 为主 | Program 工作台、Batch 审核面板 | 已确认，summary panel 为主 |
| 6 | `profile / incident` 摘要是否永久保留在右栏，还是后续升级成独立 `Ops Mode` | Program 工作台 | 后续批次再议 |
| 7 | 右栏 `profile / incident` 摘要的具体字段和卡片密度 | Program 工作台 | 已按紧凑摘要默认值确认 |
| 8 | Batch 审核面板是否固定显示 blockers / missing fields / release gate 摘要 | Batch 审核面板 | 已确认 |
| 9 | readiness-check 结果采用结果条 + 右栏同步刷新 | Program 工作台、Batch 审核面板 | 已确认 |
| 10 | Docs/Batch mode 切换时保留上一次选中的 doc / batch | Program 工作台 | 已确认 |
| 11 | 左侧导航树采用按 mode 默认展开 + 记忆展开状态 | Program 工作台 | 已确认 |
| 12 | review modal 仅展示状态推进关键字段 | 文档阅读面板、Batch 审核面板 | 已确认 |

## 14. 代码事实来源清单

### 已读取关键文件

- `docs/prd-autodev/generic-ai-autodev-platform/program-plan.md`
- `docs/prd-autodev/generic-ai-autodev-platform/context-brief.md`
- `docs/prd-autodev/generic-ai-autodev-platform/alignment.md`
- `docs/prd-autodev/generic-ai-autodev-platform/workstreams/01-frontend-pages.md`
- `docs/prd-autodev/generic-ai-autodev-platform/test-matrix.md`
- `docs/development-doc-templates/04-原型清单模板.md`
- `docs/prd-autodev/generic-ai-autodev-platform/frontend-page-structure.md`

### 文件对应事实类型

- program 级目标、边界、批次策略
- front-end MVP 优先级与最小闭环
- 原型清单模板结构

### 仍未读取或无法确认的范围

- 实际前端代码仓中的现有页面壳与组件模式

### 因无法确认而保留的内容

- 所有交互布局细节
- review transition 的具体确认交互样式
- 轻量编辑字段边界
- AI 优化回写机制
