---
topic: generic-ai-autodev-platform
kind: evidence
title: 从 019e1946 起的会话演进挖矿
createdAt: 2026-05-17T13:10:00+0800
program: true
---

# Session Mining From 019e1946 To Now

## Scope

- 起点会话：`019e1946-2012-7e41-9f3d-42bfbc37cbb0`
- 时间范围：`2026-05-12` 到 `2026-05-17`
- 目标：重建 `OpenClaw`、`PRD-autodev`、`长时测试`、`repair`、`qwen worker`、`d2on` 的真实演进链，提炼对自动驾驶系统有指导意义的结构性问题。
- 说明：
  - `cc-connect` 当前已废弃，但其相关会话中包含“微信指挥 AI、人工审批、长时任务回报”的需求萌芽，仍有分析价值。
  - 本文重点不是保留旧集成方式，而是提炼它后来如何演进成 `openclaw-weixin`、`router`、`repair`、`approval`、`PRD loop` 这些控制面能力。

## Main Phases

## Phase 0

- 时间：`2026-05-12 07:01` 起
- 代表会话：`019e1946...`
- 主题：微信 -> OpenClaw -> Codex 通路验证

### What Happened

- 最开始关注点是“能不能从微信发消息控制 Codex 完成小任务”。
- 很快暴露出不是业务问题，而是 runtime/provider 问题：
  - `openai:default` 与 `openai-codex:*` profile 不匹配
  - OpenClaw 调到 Codex harness 时 provider 名不对
  - 修完 provider 之后又撞到 subscription usage limit

### Why It Matters Later

- 这是后续“主循环模型、worker 模型、repair 模型需要拆 profile”的最早信号。
- 也是后续“任务控制入口”和“代码执行入口”必须分离的最早信号。
- 说明控制面从一开始就不是单纯的聊天入口，而是一个需要鉴权、路由、限额感知、运行时探针的系统。

## Phase 1

- 时间：`2026-05-12`
- 代表会话：`019e1b13...`
- 主题：微信控制长时自动开发，不再依赖 cc-connect

### What Happened

- 用户开始明确要求通过微信启动长期自动开发，而不是临时聊天。
- 很快发现自然语言消息并不会自动等价于“启动 cron / agent loop”。
- 补出了两类关键约束：
  - 微信命令需要拦截和映射，而不是让自然语言自己碰运气
  - 长时任务的微信汇报必须极短、结构化、适合手机阅读

### Structural Insight

- 这一步把“人工 in the loop”从附属需求变成了控制面一等功能。
- 自动驾驶系统前端和消息入口都要支持：
  - 启动/停止/修复/审批
  - 状态和进度摘要
  - 短格式回报

## Phase 2

- 时间：`2026-05-12` 到 `2026-05-13`
- 代表会话：
  - `019e1c85...`
  - `019e1e66...`
  - `019e1e86...`
  - `019e200f...`
  - `019e20af...`
- 主题：自动开发从“接线”升级到“真实上线”

### What Happened

- 最初 D2 前后端自动开发还偏“页面能打开、接口能接上”。
- 用户随后迅速收紧要求：
  - 必须真实上线
  - 必须通过 `chrome-devtools` 验证
  - 所有字段都要真实有效
  - 不允许降级、兜底、假成功
- 这催生了两类新东西：
  - 更细的 AI 自动开发指导文档
  - 第一批“不要只看页面 smoke，要看真实业务链路”的要求

### Structural Insight

- 这是后续“evidence 不是第一公民就一定会假完成”的起点。
- 说明自动化平台如果没有把“真实验收方式”纳入 task contract，story 很容易漂到“看起来完成”。

## Phase 3

- 时间：`2026-05-13`
- 代表会话：
  - `019e218f...`
  - `019e23f8...`
  - `019e2429...`
- 主题：从临时 story 转向 PRD/技能化/批次化

### What Happened

- 开始把 `openclaw-autodev` 做成可复用技能。
- 开始把 `prd-autodev-loop` 做成正式技能，而不只是临时讨论。
- 会话里第一次清晰提出这些要求：
  - 粗略输入必须先互动问答
  - 复杂任务要支持 Program Plan / Workstreams / Test Matrix / Story Batches
  - PRD 到自动化发布要有确定性脚本，不要手工拼 story

### Structural Insight

- 这是后续“PRD 不该直接生粗 story”的真正起点。
- 自动驾驶系统必须把这些对象做成显式实体：
  - Program
  - Question Round
  - Context Brief
  - Alignment
  - Story Batch
  - Publish Record

## Phase 4

- 时间：`2026-05-13` 到 `2026-05-15`
- 代表会话：
  - `019e21cc...`
  - `019e22c0...`
  - `019e2932...`
- 主题：长时测试与深测开始压出框架问题

### What Happened

- 从“周期 smoke”升级到“长期深度探索测试”。
- 很快发现不是测试脚本不够，而是框架自身存在问题：
  - queue 选择正确，但 worker 被旧 handoff 牵引
  - `prompt.submitted` 后无任何 tool/event
  - state 文件 0B
  - story 注入和 handoff 注入混线

### Structural Insight

- 这一步暴露出一个非常关键的问题：
  - 平台最初缺少“当前 story 注入优先于历史 handoff”的硬约束
- 后面大量 `qwen`、`dev-docs`、`d2on` 的问题，本质都和这里同源：
  - 真正执行的不是当前队列想执行的 story

## Phase 5

- 时间：`2026-05-14`
- 代表会话：
  - `019e2648...`
  - `019e2667...`
  - `019e2773...`
- 主题：story 编排一致性、状态真源、审批语义修复

### What Happened

- 用户开始直接指出“story 编排一致性比较差”。
- 框架开始围绕以下问题修补：
  - monitor/status/detail 读的不是同一套真源
  - reviewed/open/draft/status 字段容易混淆
  - operator approval 会被旧 session 的 blocked 结果覆盖
  - `Ticket` 无法精确命中 story，误挂前缀相似项

### Structural Insight

- 这是“唯一真源”思想真正开始落地的地方。
- 说明自动驾驶系统绝不能把：
  - queue status
  - story truth
  - monitor summary
  - human approval
  - report ticket matching
  做成几套松散逻辑。

## Phase 6

- 时间：`2026-05-15`
- 代表会话：
  - `019e2bb2...`
  - `019e2c7e...`
- 主题：runtime blocker、remote access、模型 profile 分离

### What Happened

- `D2ON` 开始进入真实环境：
  - 真设备
  - 真 MySQL
  - 真远程 discovery
- 这时问题快速从代码逻辑转向运行时：
  - evidence 里敏感信息泄露风险
  - repair/retry 路由差异
  - 某任务的模型额度 429，影响整个自动链
- 同时出现新需求：
  - 代码开发 agent 需要稳定 remote access 工具，不要每次临时开放
  - 主循环和 worker 要用不同模型

### Structural Insight

- 这是 profile/config 管理面必须产品化的直接证据。
- 前端 MVP 做 profile 管理不是锦上添花，而是吸取真实运行教训后的刚需。

## Phase 7

- 时间：`2026-05-16` 到 `2026-05-17`
- 代表会话：
  - `019e2fae...`
  - `019e300e...`
  - `019e30a1...`
  - `019e30ef...`
  - `019e319b...`
  - `019e31ba...`
  - `019e3346...`
  - `019e337e...`
- 主题：qwen 弱 worker 工程化、d2on/d2on-prd 闭环、repair 路由、规划重构

### What Happened

- `qwen` 调优把很多“执行层不稳定”问题彻底放大：
  - prompt stuck
  - 旧进程残留
  - daemon 双实例
  - stale pointer
  - state truth 冲突
- 然后逐步补出：
  - worker profile
  - execution pack
  - runtime rules
  - repair agent
  - blocker route
  - `d2on -> d2on-prd` 循环

### Structural Insight

- 这一阶段证明了：如果没有前面几阶段的修补，后面的“通用平台重构”几乎不可能正确开始。
- 也说明你现在要求“先挖矿、先提取、先规划，再开发”是完全正确的逆向纠偏。

## Cross-Cutting Lessons

## Lesson 1

- 很多技术 bug，其实起点是“产品对象没有定义清楚”。
- 最典型的对象缺失：
  - profile
  - execution pack
  - repair ticket
  - approval record
  - question round
  - context brief

## Lesson 2

- 没有 story/batch 粒度治理，就不会有稳定自动化。
- 最初的问题不是 AI 不聪明，而是给 AI 的单位工作不稳定。

## Lesson 3

- 没有验证 contract，就不会有真正的 `DONE`。
- 从 D2 到 D2ON，再到 dev-docs，假完成问题都反复出现。

## Lesson 4

- 没有 lane boundary，就会让 PRD、repair、执行互相污染。
- 后面很多 blocker 路由修补，本质是在还旧债。

## Lesson 5

- 长时自动化的核心不是生成代码，而是状态管理、恢复、证据和人机协作。

## Direct Guidance For Current Platform

- 自动驾驶系统不能从“AI 聊天入口”开始设计，要从“对象和 contract”开始设计。
- 首期前端必须优先承载：
  - Program / PRD / batch
  - profile / runtime env
  - execution pack preview
  - blocker / repair / approval
  - evidence / readiness 审阅
- `dagengine` 更适合承载执行状态机和调度内核，不适合替代这些上层规划与控制对象。
- `openclaw-autodev` 和 `prd-autodev` 应被当作矿产资源：
  - 提取约束
  - 提取失败模式
  - 提取对象模型
  - 不能把现有实现原样搬过去

## Recommended Next Use Of This Mining

1. 把本文和 [weekly-session-mining-2026-05-17.md](/Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/generic-ai-autodev-platform/evidence/weekly-session-mining-2026-05-17.md) 合起来，作为自动驾驶系统的“反补丁化设计输入”。
2. 基于这些历史问题，先冻结自动驾驶系统的对象模型和状态模型。
3. 在代码启动前，先补一份“角色与对象关系图”，明确 planner / controller / worker / repair / human 各自读写什么。
