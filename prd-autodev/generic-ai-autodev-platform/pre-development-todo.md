---
topic: generic-ai-autodev-platform
kind: full-stack
title: 自动驾驶系统
createdAt: 2026-05-17T10:40:32+0800
program: true
status: draft
---

# 进入开发前 TODO 清单

## 使用原则

- 这份清单是“进入开发前”的 gate，不是开发过程 backlog。
- 未完成的项，默认不能进入正式 OpenClaw 开发任务。
- 每一项都需要文件化产物，不能只靠对话确认。

## TODO 总表

| ID | TODO | 目标 | 主要产物 | 当前状态 |
|---|---|---|---|---|
| TODO-01 | 前端产品形态深挖 | 明确首期 MVP 的页面、导航、对象、状态、用户流 | `workstreams/01-frontend-pages.md`、`docs/development/generic-ai-autodev-platform/candidate-04-prototype-list.md` | completed |
| TODO-02 | `dagengine` 内核能力与缺口映射 | 明确可复用内核、不能直接复用部分、需要补的新对象 | `workstreams/02-backend-api-contracts.md`、`dagengine-kernel-mapping.md` | completed |
| TODO-03 | `openclaw-autodev` 控制平面抽象深挖 | 提取 loop/story/execution pack/repair/approval 等核心模型 | `openclaw-control-plane-mapping.md`、相关 workstream 更新 | completed |
| TODO-04 | `prd-autodev` 规划平面抽象深挖 | 提取 `Topic/Program/Workstream/StoryBatch/ReadinessDecision` 等核心模型 | `prd-planning-plane-mapping.md`、相关 workstream 更新 | completed |
| TODO-05 | 标准模板 `01-07` 阶段化映射 | 明确首批标准文档的产出顺序、输入来源、修订策略 | `template-rollout-mapping.md`、`docs/development/generic-ai-autodev-platform/*.md` | completed |
| TODO-06 | 候选 lane 与 batch readiness 规则 | 明确 `planner/frontend/backend/ct` 等候选 lane 与进入 OpenClaw 的 gate | `alignment.md`、`test-matrix.md`、`workstreams/03-e2e-critical-flows.md` | completed |
| TODO-07 | 第一版 reviewed planning slice | 形成可审阅的 planning slice，支撑第一批 OpenClaw batch | `alignment.md`、`review.md`、`story-packages/batch-001.json`、`evidence/final-readiness.md`、`object-state-freeze-checklist.md`、`runtime-governance-and-super-repair.md`、`migration-tool-decision.md`、`dagengine-integration-decision.md`、`validation-baseline-decision.md` | completed |
| TODO-08 | 关键人工补充要求收集与回写 | 在任何 AI 开工前，补充并冻结用户后续提出的重要要求 | 新一轮对齐文档、相关 candidate 文档回写 | completed |
| TODO-09 | 核心 contract 缺口补完 | 把 provider/runtime、evidence/verifier、readiness、message projection 四类缺口补成正式冻结文档 | `provider-runtime-policy-freeze.md`、`evidence-verifier-contract.md`、`readiness-decision-freeze.md`、`human-ops-message-projection.md` | completed |
| TODO-10 | 顶层循环目标与 harness 规则补完 | 把 `PRD <-> AutoDev` 双向自动循环、PRD 验收终止权、harness 独立治理层补成正式冻结文档 | `prd-autodev-bidirectional-loop-freeze.md`、`harness-governance-freeze.md` | completed |
| TODO-11 | 业务编排状态一等公民与护栏规则补完 | 把业务编排状态正式提升为一等公民，并补入自动辅助驾驶式护栏与 interlock 规则 | `business-orchestration-state-first-class-freeze.md` | completed |
| TODO-12 | 自动驾驶引擎整合分析 | 把现有分散概念收束成统一引擎视角，避免后续落回 handler/controller if-else | `autonomous-driving-engine-analysis.md` | completed |
| TODO-13 | 自动驾驶引擎工程冻结 | 把自动驾驶引擎收敛为可进入实现的工程 contract，冻结最小输入输出 schema、模块边界、规则类型和动作集 | `autonomous-driving-engine-freeze.md`、`alignment.md`、`evidence/final-readiness.md` | completed |
| TODO-14 | 自动驾驶引擎概念映射 | 把正式对象映射成自动驾驶与日常协作里的直觉概念，降低开发与评审心智负担 | `autonomous-driving-engine-concept-mapping.md` | completed |
| TODO-15 | 自动驾驶引擎代码命名规范 | 把自动驾驶类比正式落到变量、方法、结构体、目录与桥接函数命名层 | `autonomous-driving-engine-code-naming.md` | completed |
| TODO-16 | 自动驾驶引擎命名一致性冻结 | 把 planning authoritative names、engine code names、human aliases 三层命名规则正式冻结，防止文档和实现命名漂移 | `autonomous-driving-engine-naming-freeze.md`、`alignment.md`、`program-plan.md`、`object-state-freeze-checklist.md` | completed |
| TODO-17 | AI 司机学习与外部接管冻结 | 把“自动辅助驾驶系统 + AI 司机”中的学习通道与外部接管通道正式对象化，避免后续退回自由文本干预 | `ai-driver-learning-and-takeover-freeze.md`、`object-state-freeze-checklist.md`、`human-ops-message-projection.md` | completed |
| TODO-18 | 组件结束信号冻结 | 把多组件协作里的结束信号、采纳规则与投影方式正式对象化，避免局部 done 被误放大成全局 close | `component-end-signal-freeze.md`、`object-state-freeze-checklist.md`、`evidence-verifier-contract.md`、`prd-autodev-bidirectional-loop-freeze.md` | completed |

## Gate 定义

### Gate A - 目标冻结

- 首期是 `MVP`
- `dagengine` 是执行引擎内核
- 前端首期优先 `PRD/StoryBatch 文档与批次管理`
- 验收口径为 `规划闭环 + 首批可执行 StoryBatch 进入 ready-for-openclaw 状态`

状态：`completed`

### Gate B - 资产挖矿充分

- `openclaw-autodev`、`prd-autodev`、`dagengine` 至少完成多轮、多角度挖矿
- 关键对象、契约、状态机、边界接口被提取出来

状态：`completed`

### Gate C - 前端 MVP 定义清楚

- 首页最小闭环明确
- 页面层级、对象清单、状态清单明确
- `模型/profile 配置管理` 不混入首批主线

状态：`completed`

### Gate D - 标准文档路线明确

- `01-07` 首批先行
- 每类文档的输入来源明确
- 文档允许后续修订，但首批必须能支撑 planning slice

状态：`completed`

### Gate E - OpenClaw 启动条件明确

- reviewed planning slice 就绪
- batch ready 规则明确
- 候选 lane 清楚
- 需要的 task contract 已定义

状态：`completed`

### Gate F - 关键人工要求已补充

- 用户明确表示：在完成现有开工前任务后，还有一轮重要要求需要补充
- 在这轮要求被正式记录并回写前，任何前端/后端 implementation batch 都不能 promote 或发布

状态：`completed`

## 当前执行顺序

1. 围绕 `autonomous-driving-engine-freeze.md` 定义首批 schema / reducer / planner API / projection read model 切片
2. 把 `DriverLearningSignal / DriverLearningRecord / TakeoverRequest / TakeoverDecision` 并入首批 schema / reducer / projection 切片
3. 把 `ComponentEndSignal / EndSignalEvaluation / EndSignalProjection` 并入首批 schema / reducer / projection 切片
4. 结合前端工作台、右栏摘要与消息控制面，确认 `DecisionEnvelope`、takeover 提示与 end-signal 摘要的首批承接方式
5. 按 `autonomous-driving-engine-naming-freeze.md` 保持 planning authoritative names 与 engine code names 一致
6. 再决定是否创建首批 OpenClaw task contract

## 本轮正在执行

当前执行：`继续把自动驾驶引擎从决策抽象推进成真实运行内核`

完成标准：

- 基于引擎冻结稿把实现切片压缩到最小闭环
- 明确 `DecisionEnvelope` 与 `ReadinessSummaryProjection` 的前后端承接边界
- 明确结束信号、学习信号、接管信号进入右栏与消息面的首批 read model 边界
- 明确风险/置信度在右栏中的最小融合表达
- 明确复杂故障诊断进入 `diagnostics` 子内核，而不是继续散落在 controller / handler 分支里
- 明确 program 级 runtime kernel 的 inbox、working memory、agenda、command journal 与 checkpoint
- 明确所有正式概念的驱动归属，避免出现未被 runtime/command/backfeed 承接的空挂对象
- 为首批代码与 OpenClaw task contract 提供稳定输入
