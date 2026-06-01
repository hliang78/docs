---
topic: generic-ai-autodev-platform
kind: full-stack
title: 自动驾驶系统
createdAt: 2026-05-17T10:40:32+0800
program: true
---

# Program PRD

## Objective

在新目录中基于 `dagengine` 重构一套首期可跑通的自动驾驶系统 MVP，并先让规划者通过前端工作台完成 `Program -> Docs -> StoryBatch` 的最小闭环。

## MVP Scope

- 前端首期只聚焦 `PRD/StoryBatch 文档与批次管理`
- 交互先做 `只读 + 审阅 + 状态推进`
- `dagengine` 作为执行引擎内核
- `openclaw-autodev` 作为控制平面矿脉来源
- `prd-autodev` 作为规划平面矿脉来源
- 标准文档首批优先 `01-07`

## Non-Goals

- 当前轮次不进入正式代码开发
- 当前轮次不发布 OpenClaw RuntimeStory
- 当前轮次不做模型/profile 配置主线
- 当前轮次不做 OpenClaw 运行态全量控制台

## Primary User Flow

1. 规划者进入 Program 首页，看到 Topic/Program 列表与当前阶段。
2. 进入 Program 工作台，浏览 `context-brief/program-plan/workstreams/test-matrix/review/final-readiness`。
3. 打开 Batch 审核面板，判断某个 batch 是否已经满足 reviewed 或 ready-for-openclaw 的前提。
4. 在完成人工对齐后，再决定是否启动代码批次与 OpenClaw task contract。

## Current Planning Outputs

- 需求与边界：`context-brief.md`、`alignment.md`、`program-plan.md`
- 前后端/流程切片：`workstreams/*.md`、`test-matrix.md`
- 关键抽象：`dagengine-kernel-mapping.md`、`openclaw-control-plane-mapping.md`、`prd-planning-plane-mapping.md`
- 标准文档：`docs/development/generic-ai-autodev-platform/candidate-01` 到 `candidate-07`
- 代码前 gate：`pre-development-todo.md`、`review.md`、`evidence/final-readiness.md`

## Current Status

当前 PRD 已足够支撑“代码前最后一次对齐”，但还不应直接转入实现。下一步先做前端讨论和代码切片确认，再决定是否把 `batch-001` promote 为 reviewed。
