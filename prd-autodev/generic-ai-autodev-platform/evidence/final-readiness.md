---
topic: generic-ai-autodev-platform
kind: full-stack
title: 自动驾驶系统
createdAt: 2026-05-17T10:40:32+0800
program: true
---

# Final Readiness

## Status

- alignment-ready: 已完成多轮挖矿、三平面抽象、`01-07` 候选标准文档和第一版 batch 草案。
- core-contract-gaps-closed: provider/runtime policy、evidence/verifier、readiness、message projection 四个核心缺口已补成冻结文档。
- loop-goal-frozen: `PRD planning plane <-> AutoDev execution plane` 双向自动循环目标已正式冻结，且终止权明确归属 PRD acceptance。
- harness-governance-frozen: harness 已从 provider 附属字段提升为独立治理层。
- orchestration-state-first-class-frozen: 业务编排状态已被提升为一等公民，并补入自动辅助驾驶式护栏规则。
- autonomous-driving-engine-analyzed: 已形成“把零散逻辑整合成统一自动驾驶引擎”的分析稿。
- autonomous-driving-engine-frozen: 已把自动驾驶引擎正式冻结到工程 contract，明确最小输入输出 schema、模块边界、首期规则类型与动作集。
- ai-driver-channels-frozen: 已把 AI 司机学习通道与外部接管通道补成正式冻结文档。
- component-end-signal-frozen: 已把多组件协作里的结束信号机制正式冻结。
- code-not-approved: 当前适合停在代码前，因为首批实现切片、前端形态细节、运行时 contract 仍需最后一次人工对齐。
- openclaw-not-started: 尚未创建或启用本 topic 的 OpenClaw task，也未发布 stories。

## Summary

- 首期 MVP 边界已经稳定：前端先做 `Program -> Docs -> StoryBatch` 工作台闭环，`dagengine` 作为执行引擎内核，`OpenClaw` 与 `PRD` 分别抽成控制平面与规划平面。
- 首期技术路线已经固定为 `React + TypeScript + Vite + TanStack Router + TanStack Query + shadcn/ui + XState + dagengine + planner/control API + MySQL + 文件系统`，不引入大型 AI workflow 编排作为核心。
- `docs/development/generic-ai-autodev-platform/` 下 `candidate-01` 到 `candidate-07` 已形成首轮 `blocked-human-confirmation` 文档，可以支撑下一轮产品、前端、后端讨论。
- [technical-selection.md](/Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/generic-ai-autodev-platform/technical-selection.md) 已形成可审阅技术选型结论。
- [frontend-workbench-decision.md](/Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/generic-ai-autodev-platform/frontend-workbench-decision.md) 已形成前端工作台推荐决策稿。
- [frontend-page-structure.md](/Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/generic-ai-autodev-platform/frontend-page-structure.md) 已形成页面结构与组件分解稿。
- [frontend-state-query-decision.md](/Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/generic-ai-autodev-platform/frontend-state-query-decision.md) 已形成前端状态与查询架构决策稿。
- [frontend-final-alignment-checklist.md](/Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/generic-ai-autodev-platform/frontend-final-alignment-checklist.md) 已形成前端最终对齐清单。
- [directory-structure-decision.md](/Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/generic-ai-autodev-platform/directory-structure-decision.md) 已形成新目录承接结构决策稿。
- [backend-framework-process-decision.md](/Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/generic-ai-autodev-platform/backend-framework-process-decision.md) 已形成后端框架与进程模型决策稿。
- [migration-tool-decision.md](/Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/generic-ai-autodev-platform/migration-tool-decision.md) 已形成迁移工具决策稿。
- [dagengine-integration-decision.md](/Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/generic-ai-autodev-platform/dagengine-integration-decision.md) 已形成 `dagengine` 接入组织决策稿。
- [validation-baseline-decision.md](/Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/generic-ai-autodev-platform/validation-baseline-decision.md) 已形成首期验证基线决策稿。
- [provider-runtime-policy-freeze.md](/Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/generic-ai-autodev-platform/provider-runtime-policy-freeze.md) 已补齐 provider/harness/quota/timeout/liveness 正式冻结。
- [evidence-verifier-contract.md](/Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/generic-ai-autodev-platform/evidence-verifier-contract.md) 已补齐 verifier、evidence、proof completeness 的正式 contract。
- [readiness-decision-freeze.md](/Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/generic-ai-autodev-platform/readiness-decision-freeze.md) 已把 readiness 从 UI 概念提升为正式对象与 projection。
- [human-ops-message-projection.md](/Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/generic-ai-autodev-platform/human-ops-message-projection.md) 已补齐手机/消息控制面的结构化导出 contract。
- [prd-autodev-bidirectional-loop-freeze.md](/Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/generic-ai-autodev-platform/prd-autodev-bidirectional-loop-freeze.md) 已把 `PRD <-> AutoDev` 双向自动循环与 PRD 验收终止权冻结成正式规则。
- [harness-governance-freeze.md](/Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/generic-ai-autodev-platform/harness-governance-freeze.md) 已把 harness 从 provider 附注升级成独立治理层。
- [business-orchestration-state-first-class-freeze.md](/Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/generic-ai-autodev-platform/business-orchestration-state-first-class-freeze.md) 已把“业务编排状态一等公民 + 自动辅助驾驶式护栏”冻结成正式规则。
- [autonomous-driving-engine-analysis.md](/Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/generic-ai-autodev-platform/autonomous-driving-engine-analysis.md) 已把“不要靠 if/else，而要抽成统一自动驾驶引擎”的整体整合思路分析出来。
- [autonomous-driving-engine-freeze.md](/Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/generic-ai-autodev-platform/autonomous-driving-engine-freeze.md) 已把引擎从“总抽象”推进成工程冻结稿，明确 `AutonomousDrivingInput`、`DecisionEnvelope`、模块边界、规则族与首期动作集。
- [autonomous-driving-engine-concept-mapping.md](/Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/generic-ai-autodev-platform/autonomous-driving-engine-concept-mapping.md) 已把正式对象映射成自动驾驶与日常协作里的直觉概念，用于降低开发与评审心智负担。
- [autonomous-driving-engine-code-naming.md](/Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/generic-ai-autodev-platform/autonomous-driving-engine-code-naming.md) 已把自动驾驶类比进一步落到变量、方法、结构体、目录与桥接函数命名层。
- [autonomous-driving-engine-naming-freeze.md](/Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/generic-ai-autodev-platform/autonomous-driving-engine-naming-freeze.md) 已把 authoritative planning names、engine code names、human-facing aliases 三层命名规则冻结，确保后续规划文档保持一致。
- [ai-driver-learning-and-takeover-freeze.md](/Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/generic-ai-autodev-platform/ai-driver-learning-and-takeover-freeze.md) 已把 AI 司机学习通道与外部接管通道正式对象化，补齐“自动辅助驾驶系统 + AI 司机”的剩余顶层控制能力。
- [component-end-signal-freeze.md](/Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/generic-ai-autodev-platform/component-end-signal-freeze.md) 已把 worker、verifier、repair、readiness、takeover、acceptance 的结束信号正式分层，避免局部结束被误当全局 closure。
- [component-end-signal-api-slice.md](/Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/generic-ai-autodev-platform/component-end-signal-api-slice.md) 已把结束信号的首批写入接口、评估接口与 read model 承接方式压成实现切片草案。
- [decision-rail-fusion-contract.md](/Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/generic-ai-autodev-platform/decision-rail-fusion-contract.md) 已把右侧决策栏正式收敛成“自动辅助驾驶系统 + AI 司机”的融合读模型，补齐学习、接管、结束信号与风险/置信度的统一承接语义。
- [fault-diagnosis-engine-freeze.md](/Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/generic-ai-autodev-platform/fault-diagnosis-engine-freeze.md) 已把复杂故障判断收口成领域专用诊断引擎机制，明确事实归并、故障假设、冲突消解与恢复路由，不再依赖散装 `if / else`。
- [engine-runtime-kernel-freeze.md](/Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/generic-ai-autodev-platform/engine-runtime-kernel-freeze.md) 已把引擎收口成真实运行内核，明确 inbox、working memory、agenda、command journal、feedback loop 与 checkpoint，而不是一次性字段拼装。
- [engine-drive-coverage-matrix.md](/Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/generic-ai-autodev-platform/engine-drive-coverage-matrix.md) 已逐个概念校验其驱动归属，明确哪些是 upstream 输入、哪些必须进入 runtime、哪些必须通过 command/receipt/backfeed 被真实驱动。
- [business-orchestration-state-impact-analysis.md](/Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/generic-ai-autodev-platform/evidence/business-orchestration-state-impact-analysis.md) 已补出“业务编排内部状态本身会直接影响自动化执行”的会话证据分析。
- [batch-002-frontend-mvp-draft.json](/Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/generic-ai-autodev-platform/story-packages/batch-002-frontend-mvp-draft.json) 已形成前端 implementation batch 草案，但明确不可开工。
- `template-rollout-mapping.md` 已把 `01-07` 模板与当前挖矿资产建立映射，说明标准化路线已具备执行基础。
- `story-packages/batch-001.json` 已从空壳补成首版结构化草案，但仍保持 `draft`，避免在前端工作台细节与 task contract 未确认前误发布。
- 前端 implementation batch 目前只允许以 draft 形式存在，等待前端专题和代码前最终对齐完成后再重新评估。
- 当前最正确的停点不是“继续实现”，而是“用现有规划产物做一次高质量对齐”，尤其是前端工作台形态与首批代码切片。
- 现在顶层抽象也进一步收紧了：不是“纯自动驾驶”，而是“自动辅助驾驶系统 + AI 司机”，并且 AI 司机已经明确必须具备学习通道与外部接管通道。
- 现在还进一步明确：多组件系统里的“结束”不能再靠模糊词表达，而必须通过正式结束信号和采纳机制分层处理。
- 现在右侧决策栏也进一步冻结成正式融合层，不能再退回单一 readiness badge 或宽泛 ops 摘要。
- 现在复杂故障判断机制也进一步冻结成正式诊断层，后续代码阶段不能把 incident/proof/takeover/blocker 判断退回到 handler 分支里。
- 现在引擎本体也进一步冻结成常驻运行时，而不是 request-time 计算函数；后续代码阶段必须把 inbox、agenda、command receipt、checkpoint 一起落下。
- 现在所有正式概念也已补做驱动覆盖校验，后续代码阶段不能再保留“名字在文档里存在，但没有进入 runtime/command/backfeed”的空挂对象。
- 前端专题已进一步收敛：首期把 `profile / incident` 只读摘要挂在右侧决策栏，独立 `Ops Mode` 后移到后续批次再议。
- 新目录承接方式也已明显收敛：现有新程序根目录作为唯一程序根目录，首期采用一个前端应用 + 一个后端应用 + 后端内部逻辑分层。
- 后端运行时也已明显收敛：`backend/` 首期采用 `Go + Gin + 单进程模块化单体`，并优先以库级方式接入 `dagengine`。

## Residual Risks

- 前端工作台采用多路由还是单工作台多标签，仍会影响首页、文档阅读、Batch 审核三者的交互密度。
- 首批代码切片已确认只做 `只读 + 审阅 + 状态推进`，`AI 优化/轻量编辑` 后移到后续 batch。
- 新程序根目录的目录承接方式、后端框架与进程模型、MySQL 边界都已基本冻结；迁移工具、`dagengine` 接入组织、验证基线也已获得人工确认，但仍处于“决策已定、实现未开工”的状态，当前仍不适合生成真实 `allowedPaths` 与最终 validation 命令。
- 数据库命名已确认采用 `oneops_ai_autodev`，前端技术方向已确认采用显式 React 工作台栈，并只借鉴 `React-Admin` 模式。
- 前端工作台的页面结构、组件边界、状态归属已大体冻结，剩余主要是交互样式级细节，而不是信息架构级摇摆。
- 前端专题现在已经可以从“页面长什么样”切换到“读模型、交互确认样式、首屏预取策略”这种更接近可执行 slice 的讨论层级。
- 文档正文返回形态已确认采用 `markdown + structured metadata`，review transition 已收敛到 `modal confirm`。
- `readiness-check` 前端反馈、Batch 审核面板固定摘要、mode 切换记忆、导航树展开策略也已确认，前端剩余未决项已经压缩到文案级别。
- 如果现在直接创建 OpenClaw task，容易把尚未冻结的前端/后端方案固化成 runtime contract，后续返工成本高。
- 核心缺口已从“缺 formal freeze 文档”收敛为“还没落成 schema/API/task contract/read model”，所以当前仍不适合把 implementation batch 视为可开工输入。
- 新增两条顶层规则已经补齐，但也进一步说明：代码阶段不能只落 provider/runtime/readiness，还必须同步落循环 backfeed/acceptance 与 harness schema。
- 现在又进一步明确：代码阶段还必须同步落 business orchestration state、guard、interlock 的 schema/reducer/API，否则业务系统仍可能在高自治状态下做出危险推进。
- 现在连高层决策内核本身也已完成冻结，这意味着剩余 gap 已不再是“怎么抽象”，而是“如何把 `DecisionEnvelope`、engine reducer、planner API、projection read model 这条主路径实现出来”。
- 现在连 AI 司机学习通道与外部接管通道也已冻结，这意味着代码阶段还必须把学习信号、接管请求和接管裁定纳入正式 schema 与前端/消息入口。

## Required Human Confirmation Before Code

1. 前端工作台形态
   - 是否接受“顶层双路由 + 工作台内切换”的推荐
   - `ready-for-openclaw` 的反馈是否以右侧决策栏为主
2. 首批代码切片
   - 是否仅实现 `只读 + 审阅 + 状态推进`
   - 右栏 `profile / incident` 摘要按紧凑卡片默认值承载是否接受
3. 新目录承接方式
   - 前端显式 React 工作台栈的目录切分是否接受
   - 首批验证基线
4. 后端工程细节
   - `cmd/migrate` 采用 library 还是极薄 shell wrapper
   - `dagengine` adapter 首批覆盖范围
   - `AutonomousDrivingInput / DecisionEnvelope` 首批 schema 承接位置是否接受
5. OpenClaw task contract 策略
   - 是否按 `frontend/backend/ct` 拆 task
   - task id、默认 disabled、allowed writes 初稿
