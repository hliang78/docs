---
topic: generic-ai-autodev-platform
kind: full-stack
title: 自动驾驶引擎概念映射
createdAt: 2026-05-17T16:20:00+0800
program: true
status: draft
---

# Autonomous Driving Engine Concept Mapping

## Purpose

- 这份文档不是新增架构。
- 它的作用是把已经冻结的正式对象，映射成更容易被开发、产品、前端、评审共同理解的直觉概念。
- 目标只有一个：
  - 降低开发心智负担。

## Use Rule

- 讨论 schema、API、read model、状态流转时，仍使用正式对象名。
- 讨论产品逻辑、协作流程、onboarding、UI 文案、review 解释时，优先使用这里的直觉映射。
- 最理想的效果是：
  - 代码里保留严格命名
  - 脑中使用简单类比

## One-Sentence Mental Model

- 这个平台就像一台“带自动辅助驾驶的项目推进车”，而且默认司机本身也是 AI。
- `PRD/planning` 负责决定目的地。
- AI 司机负责表达当前想怎么推进。
- `Autonomous Driving Engine` 负责判断当前该不该继续、怎么继续。
- `dagengine` 和各类 worker/harness 负责真正踩油门、转向、执行动作。
- `Readiness / guard / interlock` 负责防止车还没准备好就硬上路。
- `CycleBackfeed / acceptance` 负责看这一段路到底有没有真的走对。

## Core Mapping Table

| 正式概念 | 自动驾驶类比 | 日常协作类比 | 一句话理解 |
|---|---|---|---|
| `Program` | 一趟完整行程 | 一个完整项目 | 这是我们到底要去哪、为什么去 |
| `Workstream` | 路线分段 | 项目子线 | 大行程中的一段独立路段 |
| `StoryBatch` | 当前这一段行驶计划 | 本轮任务包 | 这一轮准备连续完成的一组小任务 |
| `RuntimeStory` | 一个具体驾驶动作 | 一张执行工单 | 本轮真正拿去执行的最小单元 |
| `StoryTruth / BatchTruth / TurnTruth` | 真实路况与车况 | 当前实际进展 | 不看汇报口径，只看真实发生了什么 |
| `WorldStateSnapshot` | 仪表盘 + 路况总览 | 当前局面快照 | 把分散事实归并成一眼能判断的现状 |
| `BusinessOrchestrationState` | AI 司机当前意图 | 项目推进 AI 当前推进意图 | 现在想继续、暂停、发车还是收尾 |
| `OrchestrationTransition` | AI 司机请求变道/加速/靠边 | 请求切状态 | 想从一个阶段切到另一个阶段 |
| `IntentRequest` | 导航指令 + AI 司机意图 | 本次推进请求 | 这一次到底想推动什么动作 |
| `OrchestrationSafetyGuard` | ADAS 风险判断 | 审核与风控判断 | 这件事现在做会不会出事 |
| `SafetyInterlock` | 系安全带/踩刹车/确认盲区 | 强制前置条件 | 有些条件没满足，就绝不能继续 |
| `ApprovalProfile` | 需要驾驶员确认才能执行的高风险动作 | 审批权限包 | 哪些动作必须有人点头 |
| `ReadinessDecision` | 是否达到可上路状态 | 是否可以正式开工 | 现在是不是已经准备好进入下一阶段 |
| `RuntimeTaskPolicy` | 当前驾驶模式 | 任务执行规则 | 这一类任务默认怎么跑、能跑到哪 |
| `WorkerProfile` | 执行机构能力画像 | 执行人能力画像 | 这个执行者擅长做什么、不擅长什么 |
| `HarnessProfile` | 车辆/执行机构类型 | 工作台/执行环境类型 | 这次动作是在什么执行形态里完成的 |
| `ProviderProfile` | 动力来源 | 模型/服务供应商 | 由谁提供底层能力 |
| `RuntimeEnvProfile` | 当前车辆配置与油量电量 | 当前环境配置 | 当前机器、工具、凭据、网络是否够用 |
| `PreflightProbe` | 发车前检查 | 开工前自检 | 上路前先看车门、刹车、油量是不是正常 |
| `GuardDecision` | 车机对当前动作的裁定 | 风险结论 | 允许、警告、阻断、升级哪一种 |
| `ActionPlan` | 下一步驾驶动作组合 | 下一步执行计划 | 既然判断完了，那具体接下来干什么 |
| `ExecutionPack` | 下发给执行机构的控制指令包 | 发给执行人的任务说明包 | 真正可执行、可验证、可约束的执行输入 |
| `dagengine` | 底盘与执行内核 | 执行引擎 | 负责把动作真的跑起来，不负责决定业务方向 |
| `EvidenceSet` | 行车记录与传感器证据 | 执行证据包 | 不是说做完了，而是拿出证明 |
| `VerifierResult` | 自动检测结果 | 质检结果 | 是否真的达标，要由验证结果说话 |
| `ProofCompleteness` | 证据是否足够判责 | 证据完备度 | 不是有一点证据就算数 |
| `BlockerRecord` | 路障记录 | 阻塞单 | 到底是什么东西拦住了推进 |
| `PlatformIncident` | 车辆系统故障 | 平台级事故 | 不是业务没想清楚，而是系统本身坏了 |
| `RepairRun` | 进维修站 | 运维修复 | 基础设施或机制性问题的修复过程 |
| `CycleBackfeed` | 行驶结果回传导航系统 | 执行结果回传规划层 | 跑完这一段后，把真实结果带回上层重新判断 |
| `PRDAcceptanceDecision` | 到站确认 | 业务验收结论 | 是继续下一段，还是本趟行程已经完成 |
| `DecisionEnvelope` | 本次驾驶决策说明书 | 本次决策单 | 把“看到什么、为什么这么判断、接下来做什么”一次讲清楚 |
| `MessageProjection` | 车机对外播报 | 面向人类的简报 | 给手机、消息、右栏看的结构化摘要 |

## Five Questions In Plain Language

| 引擎问题 | 自动驾驶表达 | 日常表达 |
|---|---|---|
| 当前真实世界状态是什么？ | 车现在在哪，前方路况如何 | 现在项目实际进展到哪，卡在哪 |
| 当前业务系统想做什么？ | AI 司机现在想变道、超车还是靠边 | 我们现在想 review、publish、repair 还是 close |
| 这件事现在能不能安全地做？ | 现在变道会不会撞车 | 现在推进会不会把错误状态放过去 |
| 如果能做，应该由谁、在哪个 harness、以什么 contract 去做？ | 用哪套驾驶模式和执行机构完成 | 该交给谁、在哪种执行环境里做、按什么规则做 |
| 做完之后，结果如何回流并决定下一轮？ | 跑完这一段后导航是否要改路 | 做完后是继续下一批、补证据、转 repair，还是收尾 |

## Quick Role Mapping

| 角色 | 自动驾驶类比 | 日常协作类比 |
|---|---|---|
| `Planner` | 导航系统 | 方案与拆解的人 |
| `BusinessOrchestrationState` | AI 司机脑中的当前驾驶意图 | 项目负责人当前推进意图 |
| `Autonomous Driving Engine` | 车上的自动辅助驾驶大脑 | 统一决策内核 |
| `Controller` | 发车调度系统 | 执行调度员 |
| `Worker` | 实际执行机构 | 具体干活的人或 agent |
| `Repair / SuperRepair` | 维修系统 | 运维/环境修复角色 |
| `Human` | 外部接管方 | 最终拍板的人 |

## AI Driver Model

- 更准确的理解不是“系统自己全自动开”，而是：
  - 系统里有一个 AI 司机负责提出推进意图
  - 自动辅助驾驶系统负责约束、纠偏、解释和规划
- 所以 `BusinessOrchestrationState / IntentRequest` 更像司机意图层，
- `Autonomous Driving Engine / Guard / Interlock` 更像辅助驾驶层。

## Two Essential Channels

### 1. Learning Channel

- AI 司机必须有学习通道。
- 它要持续吃进去的不是闲聊，而是：
  - `VerifierResult`
  - `EvidenceSet`
  - `CycleBackfeed`
  - `PRDAcceptanceDecision`
  - `PlatformIncident`
- 这样司机才会越开越稳，而不是每一轮都像失忆重来。

### 2. External Takeover Channel

- AI 司机也不能拥有绝对控制权。
- 系统必须保留外部接管通道，让 human 或外部控制器能够：
  - 暂停
  - 覆写意图
  - 改路由
  - 接管当前推进
- Web workbench、消息控制面、审批入口都应被设计成这个通道的一部分。

## Easy Explanation Of The 5 Layers

### 1. `World Model`

- 自动驾驶里：
  - 先看清路。
- 日常里：
  - 先搞清楚真实情况。
- 平台里：
  - 先归并 truth、evidence、incident、probe。

### 2. `Business Intent`

- 自动驾驶里：
  - 车主想去哪、当前想怎么开。
- 日常里：
  - 这轮到底想推进什么结果。
- 平台里：
  - 把 reviewed、publish、continue、close 这些意图显式化。

### 3. `Safety / Interlock`

- 自动驾驶里：
  - 不是你想变道就能变，先看盲区、车速、车距。
- 日常里：
  - 不是你想发版就能发，先看审批、证据、风险。
- 平台里：
  - 用 guard 和 interlock 做 allow / warn / block / escalate。

### 4. `Action Planning`

- 自动驾驶里：
  - 确认能动以后，决定踩油门、减速还是转向。
- 日常里：
  - 决定是发执行包、转 repair、还是让人补确认。
- 平台里：
  - 生成 `ActionPlan`。

### 5. `Execution / Backfeed`

- 自动驾驶里：
  - 车真的开出去，然后把行驶结果反馈回来。
- 日常里：
  - 任务真的做了，再回来判断下一轮。
- 平台里：
  - 通过 `ExecutionPack` 执行，并通过 `CycleBackfeed` 回流。

## The Three Most Important Cognitive Cuts

### 1. 不要把 `dagengine` 当司机

- 更准确的理解：
  - `dagengine` 是底盘和执行机构。
- 它能把动作跑起来。
- 但它不负责决定现在该不该发车、该不该变道、该不该结束行程。

### 2. 不要把 `ReadinessDecision` 当绿灯 badge

- 更准确的理解：
  - 它是发车许可。
- 不是前端自己拼出来的一抹绿色。
- 它是正式判断：现在到底能不能上路。

### 3. 不要把 `DecisionEnvelope` 当日志

- 更准确的理解：
  - 它是“本次决策说明书”。
- 不是给机器偷偷留一条 trace。
- 它应该让前端、人类、审计、消息面看到同一套原因链。

## Naming Guidance

- 对开发者最友好的方式不是把正式名词改掉。
- 而是给正式名词配固定别名。
- 如果要进一步把这套类比落到变量、方法、结构体命名，见 [autonomous-driving-engine-code-naming.md](/Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/generic-ai-autodev-platform/autonomous-driving-engine-code-naming.md)。

建议在讨论时固定这样说：

| 正式名 | 建议口头别名 |
|---|---|
| `WorldStateSnapshot` | 路况图 |
| `BusinessOrchestrationState` | 驾驶状态 |
| `ReadinessDecision` | 发车信号 |
| `OrchestrationSafetyGuard` | 安全护栏 |
| `SafetyInterlock` | 安全锁 |
| `RuntimeCapabilitySnapshot` | 车辆配置 |
| `ActionPlan` | 下一步 |
| `ExecutionPack` | 运行包 |
| `CycleBackfeed` | 跑后回报 |
| `DecisionEnvelope` | 决策卡 |

## Recommended Team Usage

- 后端设计评审：
  - 用正式 schema 名称
  - 同时口头配上这份文档的别名
- 前端设计评审：
  - 优先用“发车信号”“决策卡”“安全护栏”这类说法
- 新成员 onboarding：
  - 先看这份映射，再看 freeze 文档
- PR/代码 review：
  - 如果出现“把护栏写进 handler if/else”这类退化，直接用这份映射指出它为什么违背总抽象

## Immediate Value

- 有了这份映射，团队更容易形成共同直觉：
  - `Program` 不是文件夹，是一趟完整行程
- `ReadinessDecision` 不是 badge，是发车信号
- `DecisionEnvelope` 不是日志，是决策卡
  - `dagengine` 不是总控大脑，只是执行底盘
  - `CycleBackfeed` 不是报告附件，而是回流导航系统的真实结果
