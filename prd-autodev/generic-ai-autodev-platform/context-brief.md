---
topic: generic-ai-autodev-platform
kind: full-stack
title: 自动驾驶系统
createdAt: 2026-05-17T10:40:32+0800
program: true
---

# Program Context Brief

## Goal

基于 `dagengine`，在新目录中重构一套自动驾驶系统。该系统需要同时承接：

- `prd-autodev` 的规划与标准化文档能力
- `openclaw-autodev` 的执行控制与自动开发能力
- 前端可视化管理能力，包括 OpenClaw 任务、模型、profile 配置等

## Scope

当前已明确进入范围的方向：

- 自动驾驶系统不是旧目录的小修小补，而是新的重实现目录
- `dagengine` 被明确定位为执行引擎内核，至少需要复用其流程/任务/执行相关能力
- 需要前端界面
- 前端首期优先 `PRD/StoryBatch 文档与批次管理`
- 前端首期首页要形成最小闭环：
  - `Topic/Program` 列表与详情
  - `PRD/Workstream/TestMatrix` 浏览与状态管理
  - `StoryBatch/RuntimeStory` 审核、状态推进、发布准备
- 首期交互以 `只读 + 审阅 + 状态推进` 为主
- 同时允许 `多轮对话驱动 AI 优化` 与 `简单手动编辑` 作为轻量入口
- 需要把需求、开发、测试阶段产物绑定到 `docs/development-doc-templates/01-10`
- 文档模板不是一次性全产出，而是随着阶段逐步形成
- 首期标准文档优先 `01-07`
- 需要由 `prd-autodev-loop` 与 `openclaw-autodev` 驱动后续自动开发
- 当前阶段先做规划与标准化，不启动正式 OpenClaw 开发

当前尚未确认的范围：

- 前端控制台首期菜单与页面边界
- `dagengine` 复用深度
- `01-07` 内部的优先产出顺序
- 首批候选 lane 的精确定义
- 后续 `模型/profile 配置管理` 纳入时机

## Boundaries

- 当前阶段仅做需求澄清、上下文收敛、文档标准路线确认
- 当前阶段不直接进入正式 story 发布
- 当前阶段不直接启动 OpenClaw 开发任务
- 当前阶段不把历史文档内容视为既定新架构
- 所有后续阶段都应产出文件化标准文档，而不是仅依赖对话

## Priority Focus

1. 明确首期 MVP 规划边界
2. 通过多轮、多角度挖矿提取足够信息
3. 先完成前端产品形态的首轮挖矿
4. 再明确 `dagengine`、`openclaw-autodev`、`prd-autodev` 三者的重构关系
5. 明确标准化文档范围与阶段化产出方式
6. 在 reviewed PRD/batch 之前，不提前启动自动开发

## Background

已有资产表明：

- `docs/prd-autodev` 已形成 `Program/PRD/StoryBatch` 的前置规划模式
- `docs/openclaw-autodev` 已形成 loop/story/evidence/repair 的执行控制模式
- `dagengine` 已具备 process/task/ticket/persistence/api/plugin 等基础能力，但尚未直接承载完整 AI control plane

因此，这次工作更接近“资产开采 + 系统重构”，而不是单项目功能开发。

## Concerns

- 若首期范围过大，会导致 PRD、StoryBatch、OpenClaw task 都过粗
- 若不明确前端管理台的优先级，容易一开始同时铺太多面
- 若不明确文档模板覆盖策略，需求/设计/测试标准化链路会失衡
- 若不明确 `dagengine` 是内核还是平台骨架，后续后端设计会反复重构
- 若没有足够多轮的挖矿，后续批次会建立在不充分信息上
- 若前端首批闭环定义不清，后续批次会同时混入编辑器、运行台、配置台三种不同产品目标

## Open Questions

- 前端首期菜单与导航边界
- `dagengine` 的复用边界
- 标准化模板 `01-07` 的首批优先顺序
- 多角度挖矿的优先顺序
- 候选 lane 的精确定义
