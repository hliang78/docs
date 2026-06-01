---
topic: generic-ai-autodev-platform
kind: full-stack
title: 自动驾驶系统
createdAt: 2026-05-17T10:40:32+0800
program: true
---

# Frontend Pages And Controls

## Purpose

定义首期 MVP 中“PRD/StoryBatch 文档与批次管理”前端产品形态，确保首页能形成从 `Topic/Program` 到 `PRD/Workstream/TestMatrix` 到 `StoryBatch/RuntimeStory` 的最小闭环。

## Findings

- 首期前端不是通用控制台全量展开，而是先聚焦 `PRD/StoryBatch 文档与批次管理`。
- 首页必须同时承接三条主流程：
  - `Topic/Program` 列表与详情
  - `PRD/Workstream/TestMatrix` 浏览与状态管理
  - `StoryBatch/RuntimeStory` 审核、状态推进、发布准备
- 首期不追求重编辑器，而以 `只读 + 审阅 + 状态推进` 为主。
- 需要保留 `多轮对话驱动 AI 优化` 与 `简单手动编辑` 的轻量入口。
- `模型/profile 配置管理` 不是首批前端主线。

## Requirements

- 首页需要展示 `program` 列表、状态、当前阶段、最近 batch 概览。
- `program` 详情需要能够跳转或展开 `context-brief`、`program-plan`、`workstreams`、`test-matrix`、`review`、`final-readiness`。
- 文档视图需要支持阅读、状态识别、待确认项提示、与 AI 对话优化入口。
- `batch` 视图需要展示 batch 状态、story 列表、lane、依赖关系、review 状态、发布准备状态。
- 页面需要明确区分：
  - 规划阶段文档
  - reviewed / draft 状态
  - 可发布 / 不可发布 batch
- 轻量编辑仅限少量字段或文本块，不承担完整文档编辑器职责。

## Acceptance

- 可以从首页进入某个 `program` 并看到其文档与 batch 的闭环导航。
- 可以清楚判断某个 `program` 当前处于需求澄清、research、alignment、PRD、batch ready 中的哪一阶段。
- 可以在不进入代码执行视角的前提下，完成对文档与 batch 的审阅和状态推进准备。
- 可以触发或记录一次面向 AI 的多轮优化入口。
- 页面范围不混入首批非主线能力，如模型/profile 配置全量管理。

## Validation

- 产出前端信息架构图或页面层级说明。
- 产出页面对象清单与关键状态清单。
- 产出最小闭环用户流说明。
- 与 `program-plan.md` 和 `test-matrix.md` 对齐，不出现超出首期边界的页面目标。
- 产出 `docs/development/generic-ai-autodev-platform/candidate-04-prototype-list.md`。

## Candidate Stories

- 产出前端首页与 program 详情页信息架构草案。
- 产出文档浏览/审阅/状态推进页的关键状态定义。
- 产出 StoryBatch/RuntimeStory 审核与发布准备页的交互草案。
