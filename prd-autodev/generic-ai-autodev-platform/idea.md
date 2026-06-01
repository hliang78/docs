---
topic: generic-ai-autodev-platform
kind: full-stack
title: 自动驾驶系统
createdAt: 2026-05-17T10:40:32+0800
program: true
---

# Idea

## Original Input

基于 dagengine 作为基础，挖掘 openclaw-autodev 与 prd-autodev 资产，在新目录中重构通用 AI 自动化体系；需要前端界面管理 OpenClaw、模型与 profile 配置；需求、开发、测试阶段都要基于 docs/development-doc-templates 生成标准化文档；前后端代码希望先由 prd-autodev-loop 与 openclaw-autodev 驱动自动开发。

## Known Constraints

- 当前阶段先停在规划与标准化，不进入正式代码开发。
- 自动驾驶系统需要在新目录中重实现，不能直接把历史资产整体复制过去。
- 首期 MVP 先聚焦 `PRD/StoryBatch 文档与批次管理`，不把模型/profile 配置管理作为首批主线。
- `dagengine` 当前定位为执行引擎内核，不直接视为完整平台成品。
- 后续所有需求、开发、测试产物都需要与 `docs/development-doc-templates` 对齐。
