---
topic: generic-ai-autodev-platform
kind: full-stack
title: 自动驾驶引擎代码命名规范
createdAt: 2026-05-17T16:40:00+0800
program: true
status: draft
---

# Autonomous Driving Engine Code Naming

## Purpose

- 这份文档回答一个更落地的问题：
  - 如果我们决定用“自动驾驶”作为总抽象，那么变量、方法、结构体到底怎么命名？
- 目标不是做文案包装，而是降低写代码和读代码时的心智负担。

## Final Rule

- 可以用自动驾驶概念命名。
- 但要分层使用，而不是全仓库无差别比喻化。
- 命名优先级应是：
  - `一眼看懂`
  - `短词`
  - `生活直觉`
  - 最后才是术语感

推荐原则：

1. `engine/` 核心决策层，优先使用自动驾驶命名。
2. `adapter/infra/storage/api` 边界层，保留技术与业务锚点。
3. 跨层桥接对象，采用“双名制”：
   - 自动驾驶名负责降低心智
   - 业务/技术名负责保持精确
4. 如果一个词需要停下来想 2 秒，就说明它还不够好。

一句话版本：

- 内核像车脑，可以用驾驶命名。
- 边界像接线口，必须保留真实世界标签。

## Simple Word First

- 这套命名应优先使用最短、最常见、最不需要解释的词。
- 推荐优先词族：
  - `road`
  - `drive`
  - `goal`
  - `go`
  - `safe`
  - `lock`
  - `move`
  - `run`
  - `back`
  - `view`

- 不再把下面这些词作为主推荐：
  - `maneuver`
  - `verdict`
  - `clearance`
  - `latch`
  - `cockpit`

原因：

- 它们方向没错。
- 但还不够“扫一眼就懂”。

## Naming Scope

### Should Use Auto-Driving Names

- `backend/src/engine/**`
- engine contracts
- engine reducers
- engine planners
- engine guards
- engine projections
- engine unit tests

### Should Keep Technical Or Domain Names

- `provider`
- `harness`
- `mysql`
- `migration`
- `openclaw`
- `prd`
- external API resources
- persistence table names

原因：

- 这些层面对接的是真实系统，不只是内核类比。
- 如果把 provider、DB 表、OpenClaw task 都强行改成车类比，反而更难排查问题。

## The Naming Strategy

### Strategy A - Core Structs Use Auto-Driving Names

在 `engine/contracts/` 里，推荐优先命名为：

| 当前正式名 | 推荐代码名 | 理解方式 |
|---|---|---|
| `AutonomousDrivingInput` | `DriveInput` | 本轮驾驶输入 |
| `WorldStateSnapshot` | `RoadView` | 当前看到的路况 |
| `IntentRequest` | `DriveGoal` | 这一轮想往哪推进 |
| `RuntimeCapabilitySnapshot` | `CarSetup` | 当前车和执行机构的配置 |
| `GuardDecision` | `GoCheck` | 检查现在能不能走 |
| `ActionPlan` | `NextMove` | 下一步准备怎么动 |
| `BackfeedPlan` | `ReturnPlan` | 执行后如何回流 |
| `DecisionEnvelope` | `DriveDecision` | 本轮决策说明 |

### Strategy B - Business Objects Keep Domain Meaning But Can Have Driving Aliases

对已经冻结、且会跨 planning/control/execution 平面传播的对象，不建议直接重命名主对象。

推荐方式：

| 正式对象 | 推荐在 engine 内的别名 | 原因 |
|---|---|---|
| `BusinessOrchestrationState` | `DriverState` | 内核里更直觉，但外层仍保留正式名 |
| `OrchestrationTransition` | `StateMove` | 表达状态要往哪走 |
| `OrchestrationSafetyGuard` | `SafetyRail` | 一看就知道是安全护栏 |
| `SafetyInterlock` | `SafetyLock` | 锁没开就不能继续 |
| `ReadinessDecision` | `GoSignal` | 现在是不是能发车 |
| `ExecutionPack` | `RunPack` | 发给执行层的运行包 |
| `CycleBackfeed` | `TripReport` | 跑完这一段后的回报 |
| `PRDAcceptanceDecision` | `FinishCall` | 最终要不要收尾 |

### Strategy C - Methods Use Driving Verbs

方法名优先用“感知 -> 判断 -> 规划 -> 执行 -> 回流”这套驾驶动作词。

| 职责 | 推荐方法名 |
|---|---|
| 聚合事实 | `SeeRoad()` |
| 读取意图 | `ReadGoal()` |
| 评估护栏 | `CheckSafety()` |
| 判断是否可继续 | `CanGo()` |
| 生成动作计划 | `PlanNextMove()` |
| 编译执行输入 | `BuildRunPack()` |
| 下发执行 | `RunMove()` |
| 回收结果 | `CollectTripReport()` |
| 回流下一轮 | `SendBackReport()` |
| 输出统一结论 | `BuildDriveDecision()` |

## Recommended Naming Matrix

### Struct Names

```go
type DriveInput struct {
    EvaluationID      string
    TriggerEvent      string
    RoadView          RoadView
    DriveGoal         DriveGoal
    CarSetup          CarSetup
    ActiveLocks       []SafetyLock
    TripContext       TripContext
}

type RoadView struct {
    ViewID              string
    StoryTruthIDs       []string
    BatchTruthID        string
    OpenBlockerIDs      []string
    OpenIncidentIDs     []string
    ProofCompleteness   string
    LatestGarageCheckID string
}

type DriveGoal struct {
    GoalID           string
    DriverStateID    string
    StateMoveID      string
    Phase            string
    Goal             string
    RequestedAction  string
}

type GoCheck struct {
    CheckID           string
    Decision          string
    RiskLevel         string
    TriggeredRailIDs  []string
    RequiredLockIDs   []string
    BlockingCodes     []string
}

type NextMove struct {
    MoveID                string
    MoveType              string
    TargetLane            string
    TargetHarnessProfileID string
    NeedsHumanApproval    bool
}

type DriveDecision struct {
    DecisionID      string
    RoadView        RoadView
    DriveGoal       DriveGoal
    GoCheck         GoCheck
    NextMove        NextMove
    ReasonChain     []ReasonStep
}
```

### Variable Names

推荐：

```go
road := SeeRoad(in)
goal := ReadGoal(in)
car := LoadCarSetup(in)
check := CheckSafety(road, goal, car)
move := PlanNextMove(check, car)
decision := BuildDriveDecision(road, goal, check, move)
```

避免：

```go
data := ...
state := ...
result := ...
handlerResult := ...
nextThing := ...
```

原因：

- 自动驾驶命名真正的价值，不只是“更形象”。
- 更重要的是每个变量一眼就能看出它在决策流水线里的位置。

## Package Naming

推荐：

```text
backend/src/engine/
├── drive/
├── road/
├── goal/
├── safety/
├── move/
├── run/
├── back/
└── view/
```

推荐语义：

| 目录 | 职责 |
|---|---|
| `drive/` | 本轮决策总装配 |
| `road/` | 归并 world/truth 成路况图 |
| `goal/` | 读取当前驾驶目标 |
| `safety/` | 做安全检查与裁定 |
| `move/` | 生成下一步动作 |
| `run/` | 把动作发给执行层 |
| `back/` | 吸收执行回报 |
| `view/` | 形成统一对外展示结果 |

如果希望与现有 freeze 文档更平滑兼容，也可以采用“双名目录”：

```text
backend/src/engine/
├── worldstate-road/
├── intent-goal/
├── guards-safety/
├── planner-move/
├── actuator-run/
├── backfeed-back/
└── projection-view/
```

这更适合过渡期。

## Bridge Naming Rule

跨 engine 与外部正式对象交互时，推荐显式写桥接方法名：

```go
func RoadViewFromWorldState(snapshot WorldStateSnapshot) RoadView
func DriveGoalFromOrchestration(state BusinessOrchestrationState, t OrchestrationTransition) DriveGoal
func GoSignalFromReadiness(d ReadinessDecision) GoSignal
func TripReportFromCycleBackfeed(b CycleBackfeed) TripReport
func DriveDecisionFromEnvelope(e DecisionEnvelope) DriveDecision
```

这样做好处是：

- 内核里可以享受低心智命名。
- 边界上仍然知道真实对接的是哪个正式对象。

## Method Naming Pattern

推荐统一成流水线式动词：

1. `Sense*`
2. `Read*`
3. `Check*`
4. `Plan*`
5. `Build*`
6. `Run*`
7. `Collect*`
8. `SendBack*`
9. `Build*`

例如：

```go
func SeeRoad(in DriveInput) RoadView
func ReadGoal(in DriveInput) DriveGoal
func CheckSafety(road RoadView, goal DriveGoal, car CarSetup) GoCheck
func PlanNextMove(check GoCheck, car CarSetup) NextMove
func BuildRunPack(move NextMove) RunPack
func RunMove(pack RunPack) RunResult
func CollectTripReport(result RunResult) TripReport
func BuildDriveDecision(
    road RoadView,
    goal DriveGoal,
    check GoCheck,
    move NextMove,
) DriveDecision
```

## Naming Guardrails

### Guardrail 1

- 不要为了类比，把具体业务信息抹掉。

坏例子：

- `CarState`
- `DriveData`
- `RoadThing`

好例子：

- `RoadView`
- `DriverState`
- `GoSignal`

### Guardrail 2

- 不要让一个名字同时承担业务与基础设施两种含义。

坏例子：

- 把 `ProviderProfile` 直接改成 `EngineProfile`

原因：

- 会和真正的 decision engine 冲突。

### Guardrail 3

- 不要把数据库、OpenClaw、PRD 外部协议也强行改成驾驶类比。

坏例子：

- 把 `ReadinessDecision` 表直接命名成 `garage_clearance`
- 把 OpenClaw `RuntimeStory` API 改成 `maneuver_card`

更稳的做法：

- 内核 struct 可以叫 `GoSignal`
- persistence / API 仍保留正式对象名

## Best Practical Compromise

- 如果今天立刻开始写代码，最稳的方案不是“全项目自动驾驶重命名”。
- 最稳的方案是：

1. 外部正式对象名保持冻结文档里的 authoritative 命名。
2. `engine/` 内部决策 struct / variable / method 改用自动驾驶命名。
3. 用桥接函数把两套名字接起来。

这样会同时得到两种好处：

- 开发体验更直觉
- 架构边界仍然精确

## Recommended First Batch

首批最值得先采用自动驾驶命名的代码对象：

- `DriveInput`
- `RoadView`
- `DriveGoal`
- `CarSetup`
- `GoCheck`
- `NextMove`
- `RunPack`
- `TripReport`
- `DriveDecision`

首批最值得先采用自动驾驶动词的方法：

- `SeeRoad`
- `ReadGoal`
- `CheckSafety`
- `PlanNextMove`
- `BuildRunPack`
- `RunMove`
- `CollectTripReport`
- `BuildDriveDecision`

## Immediate Value

- 这样命名之后，开发者读 engine 代码时，脑中会自然出现一条很顺的链：
  - 先看路
  - 再看司机想干嘛
  - 再看护栏允不允许
  - 再规划动作
  - 再发给执行机构
  - 再把结果带回来

- 这比直接面对：
  - `context`
  - `state`
  - `decision`
  - `result`
  - `payload`
  - `nextState`

- 要更容易形成稳定心智模型。
