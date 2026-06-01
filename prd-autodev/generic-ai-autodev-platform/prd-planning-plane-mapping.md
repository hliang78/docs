---
topic: generic-ai-autodev-platform
kind: full-stack
title: 自动驾驶系统
createdAt: 2026-05-17T10:40:32+0800
status: draft
---

# prd 规划平面抽象映射

## 1. 目的

把 `docs/prd-autodev` 从“PRD 文件夹集合”提炼成自动驾驶系统中的规划平面对象、阶段 gate 和批次演进模型。

## 2. 当前真实文档事实

### 2.1 topic 是规划入口

`docs/prd-autodev/README.md` 已明确：

- 每个 PRD topic 只服务一个 product/program concern
- topic 是进入 OpenClaw 前的产品侧 staging area

这说明 topic 不是普通文档目录，而是规划域的根对象。

### 2.2 program 模式已经存在

从现有 `device-v2-onboarding-observability` 等目录可以看到，program 级资产至少包含：

- `idea.md`
- `questions.md`
- `context-brief.md`
- `alignment.md`
- `program-plan.md`
- `prd.md`
- `test-matrix.md`
- `story-packages/*.json`
- `evidence/*`
- `cycle-control.json`

这说明 `prd-autodev` 已经具备一条完整的 planning loop。

### 2.3 PRD 与执行有清晰边界

`docs/prd-autodev/README.md` 明确：

- PRD 拥有 program/batch/readiness 目标
- execution 拥有 repair/approval/runtime/tooling 问题
- 不应因为一次环境或运行时 blocker 就切新的 PRD 微批次

这说明规划平面与控制平面已经有明确边界约束。

### 2.4 batch 是 planning plane 下发给 execution 的结构化切片

现有文档和 story package 骨架表明 batch 至少承担：

- scope slicing
- lane binding
- dependency mode
- release gate
- reviewed/draft status

因此 `batch` 是 planning plane 中的一等对象，而不是 story 文件附属物。

### 2.5 cycle controller 说明 program 是多轮演进体

`cycle-control.json` + `prd-program-cycle.mjs` 这一组机制说明：

- reviewed batch 执行完成后，可回到 planning
- planning 要根据 evidence 决定：
  - draft next batch
  - promote next batch
  - close program
  - stop program

这意味着 program 是一个可多轮循环的状态机。

## 3. 可提炼的规划平面一等对象

### 3.1 Program

职责：

- 承载一个明确产品/平台 concern
- 拥有全局 objective、DoD、scope、risk、batch evolution

当前来源：

- topic 目录
- `program-plan.md`

### 3.2 PlanningDocument

职责：

- 承载某一类规划产物

当前来源：

- `idea.md`
- `questions.md`
- `context-brief.md`
- `alignment.md`
- `prd.md`
- `test-matrix.md`
- `review.md`

### 3.3 Workstream

职责：

- 把大 program 切成可持续推进的分析/设计/实现子域

当前来源：

- `workstreams/*.md`

### 3.4 StoryBatch

职责：

- 作为 planning -> execution 的结构化下发单元

当前来源：

- `story-packages/*.json`

### 3.5 ReadinessDecision

职责：

- 决定 program 是否继续、关闭、停下、还是进入下一批

当前来源：

- `review.md`
- `final-readiness.md`
- `automation-sync.md`

### 3.6 CycleController

职责：

- 连接 reviewed batch、execution evidence、next planning action

当前来源：

- `cycle-control.json`
- `prd-program-cycle.mjs`

### 3.7 PRDAcceptanceDecision

职责：

- 基于 execution backfeed、verifier、evidence 决定：
  - 继续循环
  - 修订 PRD
  - 起草下一批
  - promote 下一批
  - accept and close

### 3.8 CycleBackfeed

职责：

- 作为 execution plane 回流 planning plane 的正式结构化输入
- 禁止让 PRD 直接从 worker prose 或零散报告猜 execution 结果

## 4. 规划平面状态建议

### 4.1 Program 阶段

建议至少保留：

- `intake`
- `questioning`
- `research`
- `alignment`
- `planning-ready`
- `batch-drafting`
- `batch-reviewed`
- `execution-waiting`
- `evidence-review`
- `closed`
- `stopped`

### 4.2 Batch 状态

保留现有主状态：

- `draft`
- `reviewed`
- `running`
- `completed`
- `completed-with-gaps`
- `completed-blocked`
- `blocked`

### 4.3 Readiness 决策

建议标准决策值：

- `continue`
- `close`
- `stop`
- `needs-research`
- `needs-alignment`

### 4.4 循环终止语义

- `RuntimeStory.done` 不等于 program close
- `StoryBatch.completed` 不等于 program close
- 只有 `PRDAcceptanceDecision = accept-and-close` 才能正式终止循环

## 5. 自动驾驶系统规划平面建议对象

- `Program`
- `PlanningDocument`
- `Workstream`
- `StoryBatch`
- `BatchReview`
- `ReadinessDecision`
- `CyclePolicy`
- `PlanningEvidence`
- `PRDAcceptanceDecision`
- `CycleBackfeed`

## 6. 与控制平面的边界

规划平面负责：

- 目标
- 范围
- 切片
- 验收
- readiness
- 最终 acceptance 与循环终止

控制平面负责：

- story compile
- worker selection
- runtime verification
- repair / approval / retry
- 把 execution 结果结构化回流 planning plane

执行平面负责：

- process/task/ticket/execution

## 7. 首期结论

自动驾驶系统不能把 PRD 仅当成 markdown 集合。

首期就应把这些对象显式化：

- `Program`
- `Workstream`
- `StoryBatch`
- `ReadinessDecision`
- `CyclePolicy`

这样前端首页的 `Program -> Docs -> StoryBatch` 最小闭环才有稳定数据模型。

## 8. AI 推导建议

- 首期前端可以把 `program` 当成一级资源，把各类 planning 文档作为其挂载对象，而不是为每份文档做平铺导航。[待人工确认: 产品负责人]
- `review.md` 与 `final-readiness.md` 后续应提升成结构化 readiness view，而不仅是长文本。[待人工确认: 架构负责人]

## 9. 规划缺口

- planning 文档的结构化元数据模型还未正式定义。
- batch review 的统一状态迁移规则还未落成 schema。
- program 与 candidate 标准文档之间的引用关系还未显式建模。

## 10. 代码事实来源清单

### 已读取关键文件

- `docs/prd-autodev/README.md`
- `docs/prd-autodev/device-v2-onboarding-observability/program-plan.md`
- `docs/prd-autodev/device-v2-onboarding-observability/prd.md`
- `docs/prd-autodev/device-v2-onboarding-observability/test-matrix.md`
- `docs/prd-autodev/device-v2-onboarding-observability/cycle-control.json`
- `docs/prd-autodev/oneops-engineering-docs-standardization/story-generation-guide.md`

### 文件对应事实类型

- planning flow
- program asset layout
- batch and cycle behavior
- standard document generation path

### 仍未读取或无法确认的范围

- 所有 topic 的长期演化差异
- 后续 planning metadata 是否已经在脚本层固化

### 因无法确认而保留的内容

- planning objects 的最终 API 表达方式
