---
topic: generic-ai-autodev-platform
kind: full-stack
title: 自动驾驶引擎命名一致性冻结
createdAt: 2026-05-17T17:10:00+0800
program: true
status: draft
---

# Autonomous Driving Engine Naming Freeze

## Purpose

- 这份文档冻结自动驾驶引擎相关对象在不同层的命名规则。
- 目标不是再发明新名字，而是保证：
  - 规划文档里的名字稳定
  - 代码里的名字直觉
  - UI 和评审里的说法统一

## Final Rule

- 从现在起，自动驾驶引擎相关命名采用三层制：
  1. `authoritative planning names`
  2. `engine code names`
  3. `human-facing aliases`

- 三层职责固定：
  - 规划文档、schema、API contract、对象冻结清单：
    - 只能使用 authoritative name
  - `backend/src/engine/**` 内部 struct / variable / method：
    - 优先使用 code name
  - 前端文案、评审解释、onboarding：
    - 优先使用 human-facing alias

## Layer Rule

### Layer 1 - Authoritative Planning Names

- 这是项目的正式对象名。
- 这些名字必须用于：
  - `alignment.md`
  - `program-plan.md`
  - `object-state-freeze-checklist.md`
  - `candidate-0x-*.md`
  - schema 文档
  - 数据库设计文档
  - API 文档
  - OpenClaw task contract 相关文档

- 这一层不追求最短，只追求：
  - 精确
  - 稳定
  - 可跨团队同步

### Layer 2 - Engine Code Names

- 这是 `engine/` 内部的推荐实现命名。
- 这些名字必须只在这些范围优先使用：
  - `backend/src/engine/**`
  - engine unit tests
  - engine internal adapters

- 这一层追求：
  - 一眼看懂
  - 短词
  - 驾驶直觉

### Layer 3 - Human-Facing Aliases

- 这是人读的解释层名字。
- 用于：
  - 右栏
  - 评审会
  - onboarding
  - 文档说明段落

- 这一层追求：
  - 容易讲
  - 容易记
  - 不要求和代码完全同名

## Authoritative To Code To Alias Matrix

| Authoritative Name | Engine Code Name | Human Alias |
|---|---|---|
| `AutonomousDrivingInput` | `DriveInput` | 驾驶输入 |
| `WorldStateSnapshot` | `RoadView` | 路况图 |
| `IntentRequest` | `DriveGoal` | 驾驶目标 |
| `RuntimeCapabilitySnapshot` | `CarSetup` | 车辆配置 |
| `GuardDecision` | `GoCheck` | 发车检查 |
| `ActionPlan` | `NextMove` | 下一步 |
| `BackfeedPlan` | `ReturnPlan` | 回流计划 |
| `DecisionEnvelope` | `DriveDecision` | 决策卡 |
| `BusinessOrchestrationState` | `DriverState` | 驾驶状态 |
| `OrchestrationTransition` | `StateMove` | 状态移动 |
| `OrchestrationSafetyGuard` | `SafetyRail` | 安全护栏 |
| `SafetyInterlock` | `SafetyLock` | 安全锁 |
| `ReadinessDecision` | `GoSignal` | 发车信号 |
| `ExecutionPack` | `RunPack` | 运行包 |
| `CycleBackfeed` | `TripReport` | 跑后回报 |
| `PRDAcceptanceDecision` | `FinishCall` | 收尾判断 |

## Canonical Rule

- 只要文档里出现以下场景，必须用 authoritative name：
  - 对象定义
  - 状态定义
  - schema 字段
  - API 字段
  - DB 设计
  - task contract
  - 对象关系图

- 不允许在这些地方直接写：
  - `DriveInput`
  - `RoadView`
  - `GoSignal`
  - `DriveDecision`

原因：

- 这些名字虽然更直觉，但它们是实现层名字，不是规划真名。

## Code Rule

- 只要代码位于 `backend/src/engine/**`，优先使用 code name。
- 如果代码跨出 engine 边界，则需要通过桥接函数显式转换。

例如：

```go
func RoadViewFromWorldState(snapshot WorldStateSnapshot) RoadView
func DriveGoalFromIntent(req IntentRequest) DriveGoal
func GoSignalFromReadiness(d ReadinessDecision) GoSignal
func DriveDecisionFromEnvelope(e DecisionEnvelope) DriveDecision
```

## Documentation Rule

- 规划文档里的第一次出现，推荐写法：
  - `AutonomousDrivingInput`（代码内推荐别名：`DriveInput`）
  - `DecisionEnvelope`（代码内推荐别名：`DriveDecision`）
  - `ReadinessDecision`（人类解释别名：发车信号）

- 这样做的好处是：
  - 正式名不会漂移
  - 代码名不会失联
  - 解释层也不会脱节

## Forbidden Drift

- 从现在起，禁止同一轮规划文档里出现下面这种漂移：
  - 一会写 `AutonomousDrivingInput`
  - 一会写 `DriveContext`
  - 一会又写 `DriveInput`

- 也禁止：
  - 把 `DecisionEnvelope` 在文档中改叫 `DriveDecision`
  - 把 `ReadinessDecision` 在 schema 里改叫 `GoSignal`
  - 把 `ExecutionPack` 在 API 文档里改叫 `RunPack`

## Review Checklist

- 以后 review 命名一致性时，至少检查 4 件事：
  1. 规划文档是否坚持 authoritative name
  2. engine 内部代码是否优先使用 code name
  3. 前端/评审文案是否优先使用 human alias
  4. 桥接层是否显式标出 authoritative -> code 的转换

## Immediate Consequence

- 从这份冻结稿开始：
  - 规划文档继续以 `AutonomousDrivingInput / DecisionEnvelope / ReadinessDecision` 为正式名
  - engine 代码可以放心使用 `DriveInput / DriveDecision / GoSignal`
  - 人类解释层统一收敛到“驾驶输入 / 决策卡 / 发车信号”
