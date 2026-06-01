---
topic: generic-ai-autodev-platform
kind: full-stack
title: 自动驾驶系统命名统一约定
createdAt: 2026-05-17T18:10:00+0800
program: true
status: draft
---

# 自动驾驶系统命名统一约定

## Purpose

- 这份文档用于统一当前规划目录里的对象名、状态名、产品名与口语说明。
- 目标不是再发明新词，而是让规划文档、冻结稿、评审稿和后续实现输入使用同一套写法。

## Canonical Names

- 产品中文名统一为：`自动驾驶系统`
- 产品英文说明名统一为：`Autonomous Driving System`
- topic slug 保持现有 metadata 值
- 新程序根目录保持现有真实路径命名
- 顶层循环目标统一为：`PRD planning plane <-> AutoDev execution plane`

补充边界：

- `自动驾驶系统` 是项目正式名称。
- 在概念解释层，更准确的心智模型是：`自动辅助驾驶系统 + AI 司机`。
- `自动驾驶引擎 / Autonomous Driving Engine` 是系统内部的决策内核名称，不与项目名混用。
- 现有 topic slug 与程序根目录路径仅在 metadata 与真实路径中保留。

## Planning Object Names

- 规划文档里的 authoritative object names 统一使用：
  - `Topic`
  - `Program`
  - `PRD`
  - `Workstream`
  - `TestMatrix`
  - `StoryBatch`
  - `RuntimeStory`
  - `ReadinessDecision`

- 这些对象名用于：
  - 规划文档
  - freeze 文档
  - schema 设计
  - API contract
  - 对象关系说明

## Status Names

- readiness 状态统一写为：`ready-for-openclaw`
- 如果需要给人解释，可在正文说明它表示“已经满足进入 OpenClaw 的发布前提”。
- 不再在同一批规划文档里混用：
  - `ready for OpenClaw`
  - `OpenClaw batch ready`
  - `publish-ready for OpenClaw`

## UI Phrase Rules

- 前端首期主线统一写为：`PRD/StoryBatch 文档与批次管理`
- 首页最小闭环统一写为：
  - `Topic/Program` 列表与详情
  - `PRD/Workstream/TestMatrix` 浏览与状态管理
  - `StoryBatch/RuntimeStory` 审核、状态推进、发布准备
- 首期闭环链路统一写为：`Program -> Docs -> StoryBatch`

## Legacy Source Names

- 历史资产和模块名继续保留它们的真实名字：
  - `prd-autodev`
  - `prd-autodev-loop`
  - `openclaw-autodev`
  - `dagengine`
- 它们是来源系统名，不强行改成自动驾驶系统对象名。

## Naming Boundary

- `DriveInput`、`DriveDecision`、`GoSignal` 等自动驾驶短名，只应出现在：
  - 自动驾驶命名说明文档
  - `backend/src/engine/**` 代码语境说明
- 规划文档中的正式对象仍应写回：
  - `AutonomousDrivingInput`
  - `DecisionEnvelope`
  - `ReadinessDecision`

## Review Checklist

1. 是否优先使用 authoritative object names，而不是口语替代词。
2. readiness 是否统一写成 `ready-for-openclaw`。
3. 是否把历史模块名与自动驾驶系统对象名区分清楚。
4. 是否避免在同一段里混用规划名、代码名和 UI 解释名。
