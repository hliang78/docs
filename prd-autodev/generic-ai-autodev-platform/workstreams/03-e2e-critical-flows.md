---
topic: generic-ai-autodev-platform
kind: full-stack
title: 自动驾驶系统
createdAt: 2026-05-17T10:40:32+0800
program: true
---

# End-to-End Critical Flows

## Purpose

定义首期规划闭环中的关键 E2E 流程，确保最终验收口径能够落到“规划闭环 + 第一批可执行 StoryBatch 达到 `ready-for-openclaw`”。

## Findings

- 首期 E2E 重点不是代码执行成功，而是规划信息链路完整且可转入自动开发。
- 关键流程必须覆盖 `Program -> Docs -> StoryBatch -> Readiness Review`。
- 现阶段最关键的不是“按钮是否可点”，而是每一步是否有稳定对象、状态和 gate。
- `ready-for-openclaw` 不能只靠人为印象，需要有显式判定条件。

## Requirements

- 定义至少一条从 `Program` 到 `reviewed StoryBatch` 的完整闭环流程。
- 定义 `draft`、`reviewed`、`ready-for-openclaw` 的核心状态。
- 定义后续 OpenClaw 启动前所需的最小证据与文档集合。
- 定义 `planner/frontend/backend/ct` 在首批闭环中的使用位置。

## Acceptance

- 可以说明首期 MVP 如何从需求澄清走到第一批可执行 StoryBatch 达到 `ready-for-openclaw`。
- 可以判断任一 batch 当前是否满足进入 OpenClaw 的条件。
- 可以解释为什么当前轮次应停在代码前，而不是继续直接启动开发。

## Validation

- 对齐 `program-plan.md` 的 batch 策略与 `alignment.md` 的首期验收口径。
- 对齐 `template-rollout-mapping.md` 与 `evidence/final-readiness.md`，不出现“batch 看似 ready 但标准文档仍缺关键输入”的情况。

## Candidate Stories

- 产出规划闭环 E2E 流程图或文字流程稿。
- 产出 batch readiness 判定条件。

## E2E Flow Draft

1. `intake/questioning`
   - 产出 `questions.md`、`context-brief.md`
   - 目标：冻结 MVP、首批边界、挖矿顺序
2. `research/alignment`
   - 产出 `program-plan.md`、三类 mapping 文档、`workstreams/*.md`
   - 目标：把矿脉信息转成前端、后端、控制、规划抽象
3. `standardization`
   - 产出 `candidate-01` 到 `candidate-07`
   - 目标：把已提取事实装入标准模板
4. `batch-drafting`
   - 产出 `story-packages/batch-001.json`
   - 目标：把后续 OpenClaw 或人工执行切片写成有 lane、有 gate 的结构化 batch
5. `readiness-review`
   - 产出 `review.md`、`evidence/final-readiness.md`
   - 目标：判断是否可进入代码阶段

## Batch Readiness Rule Draft

### Program Ready

- `context-brief/program-plan/alignment/review` 已存在
- `01-07` 候选文档已形成首轮版本
- planning/control/runtime 的核心对象已抽出

### Batch Draft Ready

- batch 已有明确 `title/status/releaseGate`
- 每个 story 已有 `id/title/lanes/scope/nonGoals/acceptance/validation`
- story 范围与首期 MVP 一致，没有偷偷混入模型/profile 管理或运行台全量能力

### OpenClaw Publish Ready

- batch 状态从 `draft` 切到 `reviewed`
- 目标 task contract 已存在，且默认 disabled
- 每个 story 的 `allowedPaths`、`validation`、`dependsOn`、`stopConditions` 可安全执行
- 人工已确认代码目录、技术栈、前端讨论结论、以及首批实现切片

## Candidate Lane Usage

| Lane | 当前职责 | 是否进入首批代码批次 |
|---|---|---|
| `planner` | 规划文档收口、batch drafting、readiness 审阅 | 是，但以文档/规划 story 为主 |
| `frontend` | Program 工作台、文档阅读、Batch 审核 UI | 待下轮确认后进入 |
| `backend` | planning 资源、batch readiness、dagengine compile 边界 | 待下轮确认后进入 |
| `ct` | 规划闭环 smoke 与后续回归约束 | 待首批代码切片形成后进入 |
