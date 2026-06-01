---
topic: generic-ai-autodev-platform
kind: full-stack
title: 自动驾驶系统
createdAt: 2026-05-17T10:40:32+0800
program: true
---

# Regression Suite

## Purpose

定义首期 MVP 在进入代码阶段后必须具备的最小回归闭环，确保“Program -> Docs -> StoryBatch”工作台不会因为局部开发而失去规划一致性。

## Findings

- 当前首期验收不是运行时自动化结果，而是规划闭环与 batch readiness。
- 因此前期回归重点不是复杂业务数据，而是：
  - 文档与状态是否一致
  - 页面导航是否闭环
  - readiness 判定是否稳定
  - 前后端资源是否对齐
- `01-07` 标准文档本身就是回归输入；后续代码实现不能把标准文档与页面/API 做成两套口径。
- `ct` lane 不应一上来承担全量端到端业务测试，而应先承接 planning shell smoke 和 contract regression。

## Requirements

- 定义首期代码批次后的最小 smoke 套件。
- 定义文档、API、前端三层的一致性回归点。
- 定义 `draft/reviewed/readiness` 状态迁移的回归断言。
- 为未来 `08-10` 模板补齐提供输入位。

## Acceptance

- 可以列出首批代码开发后最少必须跑的检查项。
- 可以说明哪些回归属于前端、后端、CT 共担，哪些仍留待后续 batch。
- 可以作为首批代码故事中的 `validation` 候选来源。

## Validation

- 与 `test-matrix.md` 中的 P0 场景对齐。
- 与 `candidate-06-api-documentation.md` 和 `candidate-07-backend-development-design.md` 的边界一致。
- 不把真实 OpenClaw runtime、大模型配置或 repair 流程误纳入首轮回归主线。

## Candidate Stories

- 定义 planning shell smoke 套件。
- 定义 batch readiness contract regression。
- 定义标准文档与页面/API 一致性检查。

## Regression Layers

### Layer 1 - Planning Data Smoke

- program 列表可加载
- program 详情可返回文档与 batch 概览
- 缺文档时返回明确状态，不是静默空白

### Layer 2 - Document And Batch Contract

- 文档状态值只能来自约定枚举
- batch story 必须满足最小字段要求
- dependsOn、lane、releaseGate、stopConditions 校验稳定

### Layer 3 - Frontend Flow Smoke

- 首页可进入 Program 工作台
- Program 工作台可切换文档视图与 Batch 审核视图
- readiness 面板能正确显示 `draft/reviewed/blocking-items`

### Layer 4 - Readiness Decision Regression

- `draft` 不能直接视为 `ready-for-openclaw`
- 缺少 `allowedPaths/validation/dependsOn` 的 story 不能被 promote
- 缺少关键候选文档时 batch 不可 promoted

## Candidate Validation Set

| 层级 | 候选验证 |
|---|---|
| 文档 | `rg -n "TBD|待确认" docs/prd-autodev/generic-ai-autodev-platform docs/development/generic-ai-autodev-platform` 用于识别残留占位符，但需要允许白名单待确认项存在 |
| JSON | `jq empty docs/prd-autodev/generic-ai-autodev-platform/story-packages/batch-001.json` |
| 契约 | 校验 batch story 字段、状态枚举、dependsOn 完整性 |
| 前端 | Program 首页 -> 工作台 -> 文档视图 -> Batch 审核视图 smoke |
| 后端 | Program/doc/batch 读取接口的 contract smoke |

## Deferred Until Later Batch

- AI 多轮优化对话回归
- 轻量编辑与保存冲突回归
- OpenClaw loop/pool/repair 可视化回归
- 模型/profile 配置管理回归
