---
topic: generic-ai-autodev-platform
kind: full-stack
title: 自动驾驶系统
createdAt: 2026-05-17T10:40:32+0800
status: draft
---

# openclaw 控制平面抽象映射

## 1. 目的

把 `docs/openclaw-autodev` 从“现有 Bash + 文档体系”提炼成可迁移到自动驾驶系统中的控制平面对象、契约和状态机。

## 2. 当前真实代码/文档事实

### 2.1 story 不是备注，而是最小执行单元

`docs/openclaw-autodev/story-schema.json` 已明确：

- `story` 是 queue 中最小执行单元
- 必含：
  - `id`
  - `title`
  - `status`
  - `priority`
  - `lanes`
  - `scope`
  - `acceptance`
  - `validation`

状态包含：

- `open`
- `in_progress`
- `needs_next_turn`
- `blocked`
- `approval`
- `done`
- `cancelled`
- `disabled`

这说明控制面不是直接调度“任务文件”，而是先调度 story。

### 2.2 execution pack 是 story 的编译结果

`docs/openclaw-autodev/story-execution-pack-schema.json` 已明确 execution pack 至少包含：

- `taskId`
- `workerProfileId`
- `taskKind`
- `environmentKind`
- `projectRoot`
- `sourceOfTruth`
- `currentStory`
- `contextPack`
- `actionPolicy`
- `runtimePolicy`
- `verificationPolicy`
- `outputContract`
- `evidenceContract`
- `recoveryPolicy`

这说明 OpenClaw 的真正关键动作不是“把 story 直接喂给 worker”，而是先做 story compile。

### 2.3 worker profile 是独立对象，不应硬编码在 story

`docs/openclaw-autodev/worker-capability-schema.json` 已定义：

- 支持的 task kind
- 支持的 environment kind
- context tolerance
- action capabilities
- write capabilities
- verification model
- scheduling defaults

这说明 worker profile 是控制面上的一等资源。

### 2.4 approval profile 是动作权限边界

`docs/openclaw-autodev/approval-profiles.json` 已定义多类审批能力包：

- `readonly-db-api`
- `frontend-test`
- `backend-restart`
- `remote-readonly`
- `network-apply-syslog`
- `server-apply-via-controller`

每个 profile 都明确：

- allowed
- denied
- evidenceRequired

这说明“能不能做”不应该藏在 story prose 里，而应挂到结构化 approval profile。

### 2.5 handoff 是跨 turn 的标准状态交接

`docs/openclaw-autodev/handoff-schema.json` 已定义：

- `control`
- `ticket`
- `changed`
- `tests`
- `next`
- `blockerClass`
- `activeStory`
- `sourceOfTruth`
- `verifyEvidence`

这说明 handoff 不是随意报告，而是控制面投影的一部分。

### 2.6 reliability model 已经把控制面边界讲清楚

`docs/openclaw-autodev/reliability-model.md` 和 `worker-adaptation-principles.md` 已明确：

- authoritative truth 以 ended trajectory + valid `LoopControl` 为准
- verify 必须压过 worker 自报完成
- retry 前必须先做 blocker classification
- repair 是独立生命周期，不应和 business story 混在一起
- worker 必须运行在 compiled execution pack 中

## 3. 可提炼的控制平面一等对象

### 3.1 RuntimeTask

来源：

- `loops/*.conf`

职责：

- 定义 lane/task 身份
- 绑定 story queue
- 绑定 validation / runtime env / allowed writes

### 3.2 RuntimeStory

来源：

- `stories/*.json`
- `story-schema.json`

职责：

- 作为 worker 可消费的最小 bounded 单元
- 管理 `status / acceptance / validation / lanes / dependsOn`

### 3.3 ExecutionPack

来源：

- `story-execution-pack-schema.json`

职责：

- story 编译后的真实 worker 输入
- 注入 source of truth、context、action policy、verify policy、recovery policy

### 3.4 WorkerProfile

来源：

- `worker-capability-schema.json`

职责：

- 描述 worker 能做什么、不能做什么
- 作为 story/task 与 worker 之间的匹配约束

### 3.4A HarnessProfile

来源：

- 新增 `harness-governance-freeze.md`

职责：

- 描述当前 worker 真实运行在哪种 harness 上
- 描述 context packing、tool calling、session lifecycle、output/evidence 语义

### 3.5 ApprovalProfile

来源：

- `approval-profiles.json`

职责：

- 定义可允许的高风险动作边界
- 指定 evidence 要求

### 3.6 TurnHandoff

来源：

- `handoff-schema.json`

职责：

- 保存跨 turn 的 authoritative projection
- 为下一 turn 提供结构化继续上下文

### 3.7 RecoveryPolicy / BlockerPolicy

来源：

- `reliability-model.md`
- `worker-adaptation-principles.md`

职责：

- 明确 blocker class
- 决定 retry / repair / approval / stop 路由

### 3.8 CycleBackfeed Export

职责：

- 把 execution truth、verifier、evidence、blocker、incident 汇总成 planning plane 可消费的结构化回流输入
- 不允许只把 report prose 丢回 PRD

## 4. 自动驾驶系统中的建议分层

### 4.1 不要继续把 loops.conf 当主模型

建议：

- `loops/*.conf` 在自动驾驶系统中只作为迁移来源
- 正式主模型应升级为结构化 `RuntimeTaskPolicy`

### 4.2 不要把 story json 当唯一对象仓库

建议分为：

- `PlanningStoryBatch`
- `RuntimeStory`
- `ExecutionPack`

并额外补齐：

- `HarnessProfile`
- `HarnessSessionPolicy`
- `HarnessContextPolicy`
- `HarnessOutputContract`

这样可避免一个 JSON 同时承担规划、调度、执行三种语义。

### 4.3 repair 与 approval 要独立成控制对象

不要只把它们作为 `story.status` 文本。

建议新增：

- `ApprovalRequest`
- `RepairRun`
- `BlockerRecord`

## 5. 控制面状态机建议

### 5.1 RuntimeStory 状态

保留现有主状态：

- `open`
- `in_progress`
- `needs_next_turn`
- `blocked`
- `approval`
- `done`
- `cancelled`
- `disabled`

### 5.2 ExecutionTurn 结果

保留 handoff/control 结果：

- `CONTINUE`
- `DONE`
- `BLOCKED`
- `APPROVAL`

### 5.3 Recovery 路由

按 blocker class 派发：

- `automation.model_runtime`
- `automation.controller_or_story`
- `automation.health_check`
- `environment.runtime`
- `business.authorization`
- `business.optimization`
- `unknown.blocked`

## 6. 候选 lane 建议

基于当前平台首期规划，建议预定义这些 lane：

- `planner`
  - 负责 PRD / batch / readiness / 文档演进
- `frontend`
  - 负责前端页面、交互、UI 文档实现
- `backend`
  - 负责 planning/control API 与 runtime compile 后端实现
- `ct`
  - 负责验证、回归、evidence 汇总

后续可再扩：

- `browser-verification`
- `docs-standardization`
- `repair`

## 7. Batch Readiness 建议规则

某一批 story 要进入 OpenClaw 前，至少满足：

1. 上游 program/planning 文档已 reviewed。
2. story 均已 lane-scoped。
3. story 的 allowed paths、acceptance、validation 清晰。
4. 若需要 worker profile / approval profile，已结构化指明。
5. 若顺序执行，`dependsOn` 或 `executionMode` 已定义。
6. batch 内不存在“规划仍未确认”的主歧义。

## 8. 首期结论

自动驾驶系统控制面应抽象出：

- `RuntimeTaskPolicy`
- `RuntimeStory`
- `ExecutionPack`
- `WorkerProfile`
- `HarnessProfile`
- `ApprovalProfile`
- `TurnHandoff`
- `BlockerRecord`
- `RepairRun`

而不是继续直接依赖：

- `loops/*.conf`
- `stories/*.json`
- 分散 prose docs

## 9. AI 推导建议

- 首期控制面 API 可以优先只暴露 `story review / batch readiness / lane assignment / publish preparation`，不需要一开始全量替代 OpenClaw runtime CLI。[待人工确认: 架构负责人]
- `planner` lane 适合先于 `frontend/backend/ct` 成为第一批自动开发 lane。[待人工确认: 产品负责人]

## 10. 规划缺口

- `RuntimeTaskPolicy` 的正式 schema 还未落地。
- `ExecutionPack` 与 `dagengine ProcessDefinition` 的编译边界还未完全定稿。
- harness 目前虽然已进入 `HarnessBinding` 语义，但仍需补足独立 schema 与 read model。
- approval/repair 是否进入首批 UI 仍待下一轮前端讨论。

## 11. 代码事实来源清单

### 已读取关键文件

- `docs/openclaw-autodev/story-schema.json`
- `docs/openclaw-autodev/story-execution-pack-schema.json`
- `docs/openclaw-autodev/handoff-schema.json`
- `docs/openclaw-autodev/worker-capability-schema.json`
- `docs/openclaw-autodev/approval-profiles.json`
- `docs/openclaw-autodev/worker-adaptation-principles.md`
- `docs/openclaw-autodev/reliability-model.md`
- `docs/openclaw-autodev/references/task-config.md`
- `docs/openclaw-autodev/references/runtime-rules.md`

### 文件对应事实类型

- story schema
- execution pack schema
- worker/approval profile schema
- reliability/recovery rules

### 仍未读取或无法确认的范围

- 脚本实现中的所有状态收敛细节
- UI 若承接 approval/repair 时的交互要求

### 因无法确认而保留的内容

- 最终控制面 API 资源命名
- approval/repair 是否属于首批 UI 能力
