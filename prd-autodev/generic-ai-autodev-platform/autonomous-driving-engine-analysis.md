---
topic: generic-ai-autodev-platform
kind: full-stack
title: 自动驾驶引擎整合分析
createdAt: 2026-05-18T03:25:00+0800
program: true
status: draft
---

# Autonomous Driving Engine Analysis

## Purpose

- 这份文档回答一个关键架构问题：
  - 现在已经抽出了很多对象、状态、护栏、readiness、loop、harness、repair、approval。
  - 但如果把它们直接写成一堆 `if / else`，平台仍会退化成补丁系统。
- 所以这里要回答的是：
  - 如何把这些复杂、分散的概念，投射成一台统一的“自动驾驶引擎”。

## Core Judgment

- 你的方向是对的。
- 自动驾驶系统不能继续把这些概念实现成：
  - controller 里的大 if/else
  - handler 里的散装条件判断
  - 不同模块各自维护一小套推进逻辑
- 更好的抽象应该是：
  - 把平台看成“自动辅助驾驶系统 + AI 司机”
  - `Autonomous Driving Engine` 是辅助驾驶大脑，不直接等于司机自身
  - 业务系统当前推进意图由 AI 司机表达
  - 也不直接等于执行内核
  - 它负责把零散逻辑统一翻译成：
    - 状态归并规则
    - 风险判断规则
    - 可执行动作规则
    - 护栏与 interlock 规则
    - 循环推进规则

## What The Engine Is And Is Not

## It Is

- 一个统一决策内核。
- 一个把 object truth、business intent、safety guard、runtime capability、execution feedback 串起来的规则引擎。
- 一个把“当前世界是什么”转成“下一步该做什么”的系统。

## It Is Not

- 不是另一个 giant controller service。
- 不是把所有逻辑都交给 LLM 临场发挥。
- 不是把 `dagengine` 原样升级成总控平台。
- 不是一个用 workflow 图硬拼所有边角规则的可视化玩具。

## The Right Projection

如果用自动驾驶类比，自动驾驶系统里的角色关系应该是：

- `BusinessOrchestrationState`
  - 相当于 AI 司机的当前驾驶意图与业务阶段
- `Truth objects`
  - 相当于车辆对现实世界的感知结果
- `OrchestrationSafetyGuard / SafetyInterlock`
  - 相当于自动辅助驾驶的风险约束层
- `RuntimeTaskPolicy / WorkerProfile / HarnessProfile`
  - 相当于车辆当前可用的动力、传感器、执行机构边界
- `ExecutionPack`
  - 相当于真正下发给执行机构的控制指令包
- `dagengine`
  - 相当于底层执行内核，不负责高层业务判断

## Two Missing Channels Must Become Formal

- 如果司机本身也是 AI，那么这套系统还不能只解决“怎么判断下一步”。
- 它还必须同时解决两件事：
  1. AI 司机如何持续学习
  2. 谁能在必要时从外部接管

### 1. Learning Channel

- AI 司机不能只看当前按钮和状态。
- 它必须持续吸收：
  - `VerifierResult`
  - `EvidenceSet`
  - `CycleBackfeed`
  - `PRDAcceptanceDecision`
  - `PlatformIncident`
- 这些输入不是日志附件，而是司机更新下一轮策略、风险偏好和推进判断的学习材料。

### 2. External Takeover Channel

- 自动辅助驾驶系统不能假设 AI 司机永远判断正确。
- 系统必须允许外部控制面在关键时刻：
  - 暂停推进
  - 覆写当前意图
  - 改路由到 repair / review / approval
  - 直接接管当前推进权
- 这个外部接管通道可以来自：
  - Web workbench
  - 消息控制面
  - human approval
  - 更高优先级的外部 agent/controller

## The Engine Should Be Built Around 5 Questions

这台引擎每次循环都只回答 5 个问题：

1. 当前真实世界状态是什么？
2. 当前业务系统想做什么？
3. 这件事现在能不能安全地做？
4. 如果能做，应该由谁、在哪个 harness、以什么 contract 去做？
5. 做完之后，结果如何回流并决定下一轮？

## Recommended Engine Model

## 1. World Model Layer

这层负责统一“现实世界状态”。

输入对象：

- `StoryTruth`
- `BatchTruth`
- `TurnTruth`
- `RepairTruth`
- `PlatformIncident`
- `VerifierResult`
- `EvidenceSet`
- `ProofCompleteness`
- `PreflightProbe`

输出：

- `WorldStateSnapshot`

作用：

- 让引擎先看到一个统一现实，而不是去读多个对象自己猜。

## 2. Business Intent Layer

这层负责表达“业务系统想做什么”。

输入对象：

- `BusinessOrchestrationState`
- `PlanningReview`
- `ReadinessDecision`
- `PRDAcceptanceDecision`
- `OrchestrationTransition`

输出：

- `IntentRequest`

作用：

- 把“想 reviewed / 想 publish / 想 continue / 想 accept-and-close”结构化。
- 不让业务意图藏在 prose 或按钮文案里。

## 3. Safety And Interlock Layer

这层是自动辅助驾驶核心。

输入：

- `WorldStateSnapshot`
- `IntentRequest`
- `OrchestrationSafetyGuard`
- `SafetyInterlock`
- `ApprovalProfile`
- `BlockerRecord`

输出：

- `GuardDecision`

结论至少包括：

- `allow`
- `warn`
- `block`
- `escalate`

作用：

- 不是替代业务意图，而是裁定这次推进是否安全。

## 4. Action Planning Layer

这层负责把“允许推进”转成“可执行动作”。

输入：

- `GuardDecision`
- `RuntimeTaskPolicy`
- `WorkerProfile`
- `ProviderProfile`
- `HarnessProfile`
- `RuntimeEnvProfile`
- `ReadinessDecision`

输出：

- `ActionPlan`

常见动作：

- `compile-execution-pack`
- `request-approval`
- `route-to-repair`
- `recalc-readiness`
- `emit-message-projection`
- `draft-next-batch`
- `close-program`

## 5. Execution And Backfeed Layer

这层负责真正落地并回流。

输入：

- `ActionPlan`

输出：

- `ExecutionPack`
- `RepairRun`
- `MessageProjection`
- `CycleBackfeed`
- `NextBusinessStateUpdate`

作用：

- 让“执行”和“下一轮决策”重新回到统一循环，而不是散在报告里。

## Why This Beats If/Else

如果继续 `if / else`，会出现 4 个老问题：

1. 同一条规则会复制到多个入口。
2. 业务状态、runtime 状态、readiness 状态会在不同模块被各自解释。
3. 新增一个状态时，没人知道要改哪几个分支。
4. 风险判断没有统一 reason chain，最后只能靠日志猜。

而自动驾驶引擎模型的好处是：

1. 状态先被归并成统一 world model。
2. 业务意图先被抽成显式 transition。
3. 护栏统一裁定风险。
4. 动作计划统一生成执行步骤。
5. 执行结果统一回流下一轮。

## How To Avoid Turning The Engine Into Another If/Else Blob

关键不是“写一个 Engine 类”，而是把逻辑拆成 4 类声明式规则：

## A. State Reduction Rules

- 定义：
  - 多个事件如何归并成当前 truth/world state
- 例子：
  - 旧 handoff 不能压过当前 selected story
  - 单次 worker footer 不能压过 verifier truth

## B. Guard Rules

- 定义：
  - 哪些 business transition 必须被 block/warn/escalate
- 例子：
  - `reviewed -> publish` 但 readiness 不足时必须 block
  - `single story done -> accept-and-close` 时必须 escalate

## C. Capability Matching Rules

- 定义：
  - 当前动作由哪个 worker/provider/harness/env 组合执行
- 例子：
  - 混合 lane 不能下给单能力 worker
  - browser proof 必须匹配可浏览器 harness

## D. Loop Progression Rules

- 定义：
  - 执行结果如何回流到 PRD 和下一轮
- 例子：
  - business proof 不足时是 `revise-prd` 还是 `draft-next-batch`
  - acceptance 满足时才允许 `accept-and-close`

## Recommended Internal Engine Contract

建议统一用一个 `DecisionEnvelope` 作为引擎输出，而不是让每个模块各返一套结果：

```text
DecisionEnvelope
├── worldStateSnapshot
├── intentRequest
├── guardDecision
├── requiredInterlocks
├── chosenActionPlan
├── reasonChain
├── emittedCommands
└── backfeedPlan
```

这样前端、消息面、日志、审计都能看到同一套判断链。

## Recommended Runtime Loop

```text
event ingested
-> reducers update truth
-> build world state snapshot
-> derive business intent
-> run safety guards
-> if blocked/escalated: emit decision + projection
-> if allowed: build action plan
-> execute through adapters
-> capture verifier/evidence/incident
-> emit cycle backfeed
-> derive next orchestration state
```

## Where Dagengine Fits

- `dagengine` 很适合放在 execution/runner 层。
- 它不应该负责：
  - 业务编排状态解释
  - readiness 决策
  - acceptance close
  - orchestration safety guard
- 更准确地说：
  - `dagengine` 是 actuator kernel
  - `Autonomous Driving Engine` 才是 high-level decision kernel

## Recommended Implementation Shape In Backend

建议在 `backend/` 里不要把这些逻辑散在 modules 里，而是额外抽一层：

```text
backend/src/engine/
├── worldstate/
├── intent/
├── guards/
├── planner/
├── actuator/
├── backfeed/
└── projection/
```

职责建议：

- `worldstate/`
  - truth -> world snapshot
- `intent/`
  - orchestration state -> transition intent
- `guards/`
  - interlock / risk evaluation
- `planner/`
  - guard result -> action plan
- `actuator/`
  - call dagengine / repair / messaging / readiness recalc
- `backfeed/`
  - execution result -> cycle backfeed / next state
- `projection/`
  - decision envelope -> frontend/message projection

## What Should Be Declarative vs Hardcoded

## Hardcoded In Code

- 引擎主循环框架
- reducer 执行顺序
- guard evaluator pipeline
- action planner pipeline
- adapter interfaces

## Declarative As Data / Policy

- 状态枚举与迁移表
- guard rules
- interlock definitions
- capability matching matrix
- loop progression matrix
- publish/readiness/acceptance gates

这意味着：

- 不是完全不用代码
- 而是代码负责“怎么跑规则”
- 数据/策略负责“规则是什么”

## The Most Important Design Constraint

- 引擎必须输出可解释的 reason chain。
- 否则它会变成另一个黑箱自动机。

每次关键判断至少都要能回答：

1. 当前看到了哪些事实？
2. 当前识别到了什么业务意图？
3. 哪条护栏被触发了？
4. 为什么 allow / warn / block / escalate？
5. 因此最终生成了什么动作计划？

## Final Judgment

- 你的“自动驾驶引擎”思路不是包装说法，而是很适合当前平台的总抽象。
- 它正好能把现在已经冻结的这些对象收束起来：
  - `BusinessOrchestrationState`
  - `ReadinessDecision`
  - `PRDAcceptanceDecision`
  - `OrchestrationSafetyGuard`
  - `SafetyInterlock`
  - `ExecutionPack`
  - `HarnessProfile`
  - `CycleBackfeed`
- 如果按这个方向推进，平台的核心就不再是“散装 controller 逻辑”，而会变成：
  - 一台统一的高层决策引擎
  - 一组声明式规则
  - 一套可解释的动作规划与回流机制

## Immediate Next Step

- 最值得下一步补的，不是再加更多概念。
- 而是补一份更工程化的冻结稿：
  - `autonomous-driving-engine-freeze.md`
- 它应该进一步回答：
  - 引擎最小输入输出 schema
  - reducer/guard/planner/backfeed 的模块边界
  - 哪些规则首期声明式化
  - 哪些动作首期必须支持
