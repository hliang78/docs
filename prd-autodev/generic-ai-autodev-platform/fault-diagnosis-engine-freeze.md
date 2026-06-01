---
topic: generic-ai-autodev-platform
kind: full-stack
title: 故障诊断引擎冻结
createdAt: 2026-05-18T07:05:00+0800
program: true
status: draft
---

# Fault Diagnosis Engine Freeze

## Purpose

- 这份文档专门回答一个更尖锐的问题：
  - 自动驾驶系统能不能做出真正的复杂故障诊断引擎
  - 而不是继续靠一串字段 `if / else` 去猜当前该 `block`、`repair`、`takeover` 还是 `continue`
- 结论是：
  - 可以
  - 但前提是把“故障判断”从 controller/handler 里拔出来，收口成独立引擎层

## Final Judgment

- 复杂故障判断不应该建模成：
  - `if verifier failed and incident exists then block`
  - `if proof missing and worker done then rerun`
  - `if provider timeout repeated then repair`
- 这类写法最大的问题不是丑，而是：
  - 规则复制
  - 入口分散
  - 条件优先级失控
  - 新故障一进来就要到处改分支
- 更合理的机制应该是：
  - 先归并事实
  - 再生成故障假设
  - 再做冲突消解
  - 最后输出恢复路由

一句话：

- 自动驾驶系统需要的不是“大 if/else”，而是一台领域专用的故障诊断引擎。

## Design Positioning

- 这不是通用规则平台。
- 这也不是把 LLM 变成拍脑袋判官。
- 它是自动驾驶引擎里的一个专门子内核：
  - `worldstate` 负责看清现实
  - `fault-diagnosis` 负责解释为什么不能安全推进
  - `guards/planner` 负责把诊断结论转成动作与路由

## The Four-Layer Mechanism

复杂故障判断建议固定为 4 层：

1. `fact reduction`
2. `hypothesis generation`
3. `conflict adjudication`
4. `recovery routing`

### 1. Fact Reduction

- 目标：
  - 把分散事件归并成统一可判断事实
- 输入来源：
  - `StoryTruth`
  - `TurnTruth`
  - `VerifierResult`
  - `EvidenceSet`
  - `ProofCompleteness`
  - `BlockerRecord`
  - `PlatformIncident`
  - `PreflightProbe`
  - `ComponentEndSignal`
  - `TakeoverRequest`
  - `DriverLearningRecord`
- 输出：
  - `DiagnosticFact[]`

### 2. Hypothesis Generation

- 目标：
  - 让引擎先形成“当前最可能是哪类故障”的候选假设
- 不是直接判最后动作。
- 输出：
  - `FaultHypothesis[]`

### 3. Conflict Adjudication

- 目标：
  - 解决多个故障假设同时成立时，谁优先、谁压制谁、谁需要合并
- 输出：
  - `FaultDecision`

### 4. Recovery Routing

- 目标：
  - 根据正式诊断结论，给出下一步恢复路由
- 输出：
  - `RecoveryRoutePlan`

## Formal Contracts

### `DiagnosticFact`

- 作用：
  - 表示一条已经过 reducer 归并的诊断事实。
- 至少包含：
  - `diagnosticFactId`
  - `ownerObjectType`
  - `ownerObjectId`
  - `factType`
  - `factKey`
  - `factValue`
  - `confidence`
  - `derivedFromObjectRefs`
  - `observedAt`

### `SymptomFrame`

- 作用：
  - 把同一轮诊断里彼此相关的症状聚成一个帧。
- 至少包含：
  - `symptomFrameId`
  - `ownerObjectType`
  - `ownerObjectId`
  - `factRefs`
  - `symptomTags`
  - `assembledAt`

### `FaultHypothesis`

- 作用：
  - 表示一条候选故障解释。
- 至少包含：
  - `faultHypothesisId`
  - `faultClass`
  - `faultCode`
  - `severity`
  - `confidence`
  - `supportingFactRefs`
  - `missingEvidenceClasses`
  - `routeHint`
  - `generatedByRuleId`
  - `generatedAt`

### `FaultDecision`

- 作用：
  - 表示冲突消解后的正式故障判断。
- 至少包含：
  - `faultDecisionId`
  - `winningHypothesisIds`
  - `suppressedHypothesisIds`
  - `decisionClass`
  - `decisionSeverity`
  - `decisionMode`
  - `dominantReason`
  - `reasonChain`
  - `decidedAt`

### `RecoveryRoutePlan`

- 作用：
  - 表示当前故障被系统正式接纳后，该走哪条恢复路由。
- 至少包含：
  - `recoveryRoutePlanId`
  - `faultDecisionId`
  - `routeType`
  - `routeActions`
  - `requiredApprovals`
  - `requiredInterlocks`
  - `backfeedRequirements`
  - `plannedAt`

## Rule Shape

真正避免 `if / else` 的关键，不是“没有条件”，而是让条件进入正式规则对象。

### `DiagnosticRule`

- 每条规则至少包含：
  - `ruleId`
  - `ruleFamily`
  - `matchAllFacts`
  - `matchAnyFacts`
  - `forbidFacts`
  - `requiredEvidenceClasses`
  - `emitFaultClass`
  - `emitSeverity`
  - `emitRouteHint`
  - `priority`
  - `suppressesRuleIds`
  - `cooldownPolicy`

### Four Rule Families

#### `symptom-reduction`

- 先把原始对象压成稳定症状。

#### `fault-hypothesis`

- 从症状组合生成候选故障假设。

#### `adjudication`

- 定义故障之间谁压谁。

#### `recovery-routing`

- 把诊断结果转成恢复路线。

## Adjudication Mechanism

复杂故障不是“谁先 match 就听谁的”。

必须显式定义冲突消解：

### 1. Dominance Order

- 建议优先级固定为：
  - `critical platform incident`
  - `safety interlock violation`
  - `takeover-required`
  - `repair-required`
  - `proof / verifier conflict`
  - `business blocker`
  - `informational warnings`

### 2. Evidence Gate

- 没有足够证据的假设不能升级成正式 `block`。
- 它最多只能：
  - `warn`
  - `request-more-proof`

### 3. Suppression

- 某些高阶故障应压制低阶表象。

### 4. Merge

- 某些假设不是互斥，而是组合。

## Route Planning Mechanism

- 故障诊断引擎只负责“判断出了什么问题”。
- 真正的下一步路由仍然必须正式化。

推荐固定映射：

| 诊断结论 | 推荐恢复路由 |
|---|---|
| `business-proof-gap` | `rerun-verifier` / `rebuild-evidence` |
| `runtime-capability-mismatch` | `route-to-repair` |
| `provider-liveness-failure` | `route-to-repair` / `pause-and-takeover` |
| `stale-truth-conflict` | `refresh-truth` / `recompute-worldstate` |
| `unsafe-close-attempt` | `request-human-confirmation` |
| `takeover-required` | `pause-and-takeover` |

## Example

- worker 自报完成
- verifier 未通过
- `ProofCompleteness = insufficient`
- 有一个高优先级 `TakeoverRequest`
- 最近还有未关闭 `PlatformIncident`

### Step 1. Facts

- `story-worker-self-reported-done`
- `verifier-status = failed`
- `proof-status = insufficient`
- `takeover-pressure = high`
- `incident-severity = major`

### Step 2. Hypotheses

- `unsafe-close-attempt`
- `business-proof-gap`
- `takeover-required`
- `repair-required`

### Step 3. Adjudication

- `takeover-required` 与 `repair-required` 共同压制 `auto-continue`
- `unsafe-close-attempt` 压制“局部完成可升级”

### Step 4. Recovery Route

- `routeType = pause-and-takeover`
- `routeActions`：
  - 暂停自动推进
  - 拒绝 closure 升级
  - 保留 verifier 失败证据
  - 通知外部接管面

## Relationship To Existing Engine Contracts

- `WorldStateSnapshot`
  - 仍然是诊断事实的上游来源
- `GuardDecision`
  - 不应直接自己猜复杂故障
  - 它应读取 `FaultDecision`
- `ActionPlan`
  - 不应直接承载故障判断
  - 它应读取 `RecoveryRoutePlan`
- `DecisionEnvelope`
  - 应补入：
    - `faultDecision`
    - `recoveryRoutePlan`
    - `diagnosticReasonChain`

## Backend Shape Recommendation

建议在现有 `backend/src/engine/` 下补一层：

```text
backend/src/engine/
├── diagnostics/
│   ├── contracts/
│   ├── reducers/
│   ├── rules/
│   ├── adjudicator/
│   ├── router/
│   └── projection/
```

## What Must Stay Hardcoded

- reducer pipeline 顺序
- adjudication pipeline 框架
- reason chain 生成格式
- adapter interfaces

## What Must Become Declarative

- `DiagnosticRule`
- dominance order
- suppression matrix
- recovery route mapping
- evidence gate policy
- cooldown / retry / repeated-fault policy

## First Implementation Slice

1. 先把 `DiagnosticFact` reducer 做出来
2. 再做 `FaultHypothesis` 规则注册表
3. 再做 `FaultDecision` adjudicator
4. 再做 `RecoveryRoutePlan` router
5. 最后把结果并入 `DecisionEnvelope` 与 `DecisionRailView`

## Freeze Conclusion

- 从现在起，复杂故障判断不应再散落在 controller、handler、readiness reducer 和前端 summary 里。
- 更准确的实现要求应是：
  - 用 reducer 生成诊断事实
  - 用规则生成故障假设
  - 用 adjudicator 做冲突消解
  - 用 router 生成恢复路线
- 这样自动驾驶系统才是真的“有引擎”，而不是“有很多条件分支”。
