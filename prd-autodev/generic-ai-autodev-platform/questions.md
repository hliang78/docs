---
topic: generic-ai-autodev-platform
kind: full-stack
title: 自动驾驶系统
createdAt: 2026-05-17T10:40:32+0800
program: true
---

# Program Question Round 001

## Purpose

在进入 research、alignment、PRD、StoryBatch 之前，先把自动驾驶系统的目标边界、首期范围、交付标准和自动化策略确认清楚。

## Questions

1. 这次要做的是“自动驾驶系统”的首期 MVP，还是直接按长期平台形态规划并分批落地？
2. 前端管理界面的首期核心能力，你更看重哪一组：
   - OpenClaw 任务/loop/pool 管理
   - 模型与 profile 配置管理
   - PRD/AutoDev 文档与 StoryBatch 管理
   - 以上三组都要，但需要明确首期优先级
3. `dagengine` 在新体系中的定位，你期望是：
   - 只作为执行引擎内核
   - 作为后端平台基础骨架
   - 作为后端基础骨架，同时逐步吸收 control plane 能力
4. 对 `prd-autodev` 与 `openclaw-autodev` 的“挖矿重构”，你更倾向：
   - 先做抽象建模与标准化文档，再逐步迁移能力
   - 先把最关键链路跑通，再补标准化
   - 两条并行，但要明确哪条是主线
5. 需求、开发、测试三阶段标准化文档，你希望首期至少覆盖哪些模板：
   - 01-07 为必须，08-10 随批次补齐
   - 01-10 全部纳入首期
   - 01-07 + 08 测试用例模板 先落地
6. 自动开发执行策略上，你是希望：
   - 先由 `prd-autodev-loop` 产出 program/PRD/batch，再由 `openclaw-autodev` 执行
   - 同时创建前端/后端两个 OpenClaw 任务并行开发
   - 先只做规划和标准化，不立刻启动自动开发
7. 你对首期验收最关键的“看得见结果”是什么：
   - 一个可用的 Web 控制台
   - 一套可运行的自动化控制后端
   - 一套完整标准文档链路
   - 上述三者的最小闭环

## Current Understanding

- 目标不是继续修补现有 `docs/openclaw-autodev` / `docs/prd-autodev`，而是基于 `dagengine` 在新目录中重构一套更通用的 AI 自动化平台。
- 自动驾驶系统至少包含前端界面，并能管理 OpenClaw 任务、模型、profile 配置。
- 自动驾驶系统要把 `prd-autodev` 与 `openclaw-autodev` 视为“矿产资源”，先挖矿，再抽象，再重构。
- 需求、开发、测试阶段都不能只停留在自由格式文档，必须对齐 `docs/development-doc-templates` 形成标准化产物。
- 开发执行链路希望遵循：`prd-autodev-loop` 负责 program/PRD/story package，`openclaw-autodev` 负责创建和执行自动化任务。

## Answers

- Q1: 首期先跑通 MVP。
- Q2: 前端首期优先 `PRD/StoryBatch 文档与批次管理`。
- Q3: `dagengine` 定位为执行引擎内核。
- Q4: `prd-autodev` / `openclaw-autodev` 需要通过多轮、多角度深入挖矿后再重构，当前阶段以规划与信息提取为主。
- Q5: 标准文档覆盖 `01-10`，但随着需求、开发、测试阶段逐步产出，不一次性全部生成。
- Q6: 先只做规划与标准化；先产出 reviewed PRD/batch，再启动 OpenClaw。
- Q7: 当前更关注“规划阶段把信息挖透并标准化”，可视化与开发属于后续阶段成果。

## Program Question Round 002

### Purpose

在已确认 MVP 方向之后，继续对首期产品边界、前端首屏职责、规划阶段文档链路和挖矿角度做更细粒度确认，为 research 与 alignment 提供更稳的落点。

### Questions

1. 前端首期 `PRD/StoryBatch 文档与批次管理`，你更希望首屏先承接哪条主流程：
   - `Topic/Program` 列表与详情
   - `PRD/Workstream/TestMatrix` 文档浏览与状态管理
   - `StoryBatch/RuntimeStory` 审核、状态推进、发布准备
   - 上述三条组成一个最小闭环
2. 对“PRD/StoryBatch 文档与批次管理”，首期是否需要可编辑能力，还是先以浏览、审阅、状态推进为主？
3. 规划阶段的标准文档首期输出，你更希望优先落哪几类正式文档：
   - 01 需求概要
   - 02 功能清单
   - 04 原型清单
   - 06 接口文档
   - 08 测试用例
   - 10 自动化测试脚本说明
4. 你希望“多轮、多角度挖矿”的角度里，哪几个必须最先展开：
   - 前端产品形态与信息架构
   - `dagengine` 内核能力与缺口
   - `openclaw-autodev` 控制平面抽象
   - `prd-autodev` 规划平面抽象
   - 标准文档模板映射关系
5. 首期 MVP 的验收你更偏向哪种口径：
   - 规划闭环跑通即可
   - 规划闭环 + 前端原型/页面方案明确
   - 规划闭环 + 第一批可执行 StoryBatch 达到 `ready-for-openclaw`
6. 首期是否需要把“模型/profile 配置管理”纳入规划文档主线，即便不作为最先开发页面？
7. 首期是否需要在规划阶段就为未来 OpenClaw task 预定义候选 lane，例如 `planner`、`frontend`、`backend`、`ct`？

### Answers

- Q1: 前端首期首页需要由 `Topic/Program` 列表与详情、`PRD/Workstream/TestMatrix` 浏览与状态管理、`StoryBatch/RuntimeStory` 审核与发布准备组成最小闭环。
- Q2: 首期先以 `只读 + 审阅 + 状态推进` 为主，同时保留 `多轮对话驱动 AI 优化` 与 `简单手动编辑` 的轻量入口。
- Q3: 标准文档首期优先 `01-07`，如果不完善，允许后续持续修订。
- Q4: 挖矿优先顺序为：`前端产品形态` -> `dagengine 内核能力与缺口` -> `openclaw 控制平面抽象` -> `prd 规划平面抽象` -> `模板映射关系`。
- Q5: 首期 MVP 验收口径为 `规划闭环 + 首批可执行 StoryBatch 进入 ready-for-openclaw 状态`。
- Q6: `模型/profile 配置管理` 先不纳入首批主规划，后续 batch 再补。
- Q7: 候选 lane 需要在规划阶段预定义，但可在后续挖矿中细化。

## Context Brief

### Goal

明确“自动驾驶系统”的首期目标、范围、优先级和自动化推进方式，使后续 research、alignment、PRD、StoryBatch、OpenClaw task creation 有稳定输入。

### Scope

- `dagengine` 作为后续基础的定位确认
- 前端控制台目标确认
- `prd-autodev` / `openclaw-autodev` 的资产重构方式确认
- 标准化文档模板覆盖范围确认
- 自动开发推进顺序确认

### Boundaries

- 当前仍处于需求澄清阶段，不直接进入代码实现。
- 当前不直接发布 OpenClaw RuntimeStory。
- 当前不假设旧目录结构就是新系统结构。

### Priority Focus

- 先把目标形态和首期边界说明白
- 再决定 research 深度、架构方向和第一批 stories

### Concerns

- 目标过大，若不先切清首期范围，后续 story 会过宽。
- 若不明确 `dagengine` 的定位，容易在执行内核、控制平面、前端平台之间反复摇摆。
- 若不明确文档模板覆盖范围，需求/开发/测试三条线会难以同步标准化。

### Open Questions

- 前端首屏最小闭环
- 文档是否先读/审/推状态，还是直接支持编辑
- `01-10` 首批正式产物的优先顺序
- 多角度挖矿的优先顺序
- 首期 MVP 的具体验收口径
