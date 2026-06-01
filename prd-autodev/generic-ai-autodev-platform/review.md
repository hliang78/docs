---
topic: generic-ai-autodev-platform
kind: full-stack
title: 自动驾驶系统
createdAt: 2026-05-17T10:40:32+0800
program: true
---

# Logic Review

## P0 Blockers

- 当前仍不能进入正式代码阶段或发布 OpenClaw batch，因为首批实现切片还未完成最后一次人工对齐。
- `batch-001` 虽已可结构化表达，但目标 task contract、schema/API 承接方式、以及是否把剩余 partial contract 继续前置冻结，仍未最终确认。

## P1 Risks

- 前端首批闭环已经收束到工作台形态，但 `多路由` 还是 `单工作台多标签` 仍会影响首批页面实现边界。
- 如果不把环境对象化，后续 worker 仍会重复遭遇“目录、账号、工具、env vars、helper tools” 隐式漂移问题。
- 如果不把业务 blocker 与基础设施 blocker 分开，`Planner / Repair / Human` 仍会继续抢 blocked 路由控制权。
- 首期前端虽然已确认需要展示 `profile / incident` 只读摘要并通过右栏同步 readiness，但这些摘要依赖的后端 read model 仍未正式实现。
- 新程序根目录的技术栈、目录组织与验证基线已形成决策稿，但它们还没有真正落成 task contract、allowed writes 与可执行 validation wrapper，因此当前 batch 仍不适合直接发布到 OpenClaw。
- provider/runtime policy、verifier/evidence contract、`ReadinessDecision`、`MessageProjection` 这几类缺口已补成冻结文档，但还没有真正落成 schema、API、reducer 与 read model，因此当前仍不能把它们当成可执行 contract。
- `PRD <-> AutoDev` 双向自动循环和 harness 独立治理这两条核心规则现在已被提升，但同样还没真正落成循环 backfeed schema、acceptance API 与 harness read model。
- “业务编排状态是一等公民，但必须有自动辅助驾驶式护栏” 这条规则现在也已冻结，但还没有真正落成 orchestration guard / interlock 的 schema 与拦截逻辑。
- 自动驾驶引擎命名虽然已经收敛出短词方案，但如果不把 planning authoritative names 与 engine code names 明确分层，后续文档、API、实现仍会再次漂移。

## P2 Suggestions

- 下一轮先做一次“代码启动前对齐”，重点讨论三件事：前端工作台形态、首批代码切片、运行时承接目录与验证基线。
- 前端专题讨论建议围绕：
  - Program 首页与工作台的布局模式
  - 文档阅读面板与 Batch 审核面板是并列还是主从
  - readiness 视图如何可视化阻断项
- 在未冻结技术栈、前端摘要承载方式与验证基线前，不要急着把 batch promote 成 `reviewed`，否则 validation、allowedPaths 与 ops contract 都会失真。
- 在进入代码前，还要坚持命名一致性冻结：规划文档继续用 authoritative names，代码内再落自动驾驶短名。

## Decision

- stop-before-code: 当前 planning slice 已足够支撑下一轮人工对齐，但还不应直接进入实现。
- next-discussion-focus: 先做前端专题与代码切片确认，再决定是否创建 `frontend/backend/ct` 的 OpenClaw task contract。
