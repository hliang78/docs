---
topic: generic-ai-autodev-platform
kind: full-stack
title: 决策栏融合读模型冻结
createdAt: 2026-05-18T06:20:00+0800
program: true
status: draft
---

# Decision Rail Fusion Contract

## Purpose

- 这份文档冻结工作台右侧 `DecisionRailView` 的融合语义。
- 它直接回答 3 个问题：
  - 自动辅助驾驶系统和 AI 司机的哪些信号会汇总到同一条决策栏里
  - “概率融合”在这里更准确地应表达成哪些风险/置信度维度
  - 组件结束信号如何影响决策栏，而不是被误写成全局 closure

## Positioning

- `DecisionRailView` 不是日志摘要。
- `DecisionRailView` 也不是前端临时拼出来的展示盒子。
- 它是自动驾驶系统在 workbench 和消息控制面上的统一驾驶舱读模型。

一句话：

- AI 司机负责提出意图，自动辅助驾驶系统负责融合判断，而 `DecisionRailView` 负责把这一刻的综合判断投影成人和前端都能稳定消费的结构化摘要。

## Fusion Inputs

`DecisionRailView` 至少允许融合这些正式来源：

- `ReadinessSummaryProjection`
- `BusinessOrchestrationState`
- `IntentRequest`
- `DriverLearningRecord`
- `TakeoverRequest`
- `TakeoverDecision`
- `ComponentEndSignal`
- `EndSignalEvaluation`
- `VerifierResult`
- `ProofCompleteness`
- `BlockerRecord`
- `PlatformIncident`

规则：

- 融合输入必须来自正式对象。
- 不能从聊天 prose、worker 尾注、临时 markdown 总结里反推。

## Four Confidence Axes

这里不建议粗暴做一个“万能总分”。

更准确的首批表达是 4 条置信度轴：

### 1. `intentConfidence`

- 含义：
  - AI 司机当前推进意图是否稳定、明确、没有自相矛盾。
- 主要来源：
  - `BusinessOrchestrationState`
  - `IntentRequest`
  - `DriverLearningRecord`

### 2. `safetyConfidence`

- 含义：
  - 当前推进是否通过护栏、联锁、readiness、风险判断。
- 主要来源：
  - `ReadinessSummaryProjection`
  - `GuardDecision`
  - `SafetyInterlock`
  - `PlatformIncident`

### 3. `executionConfidence`

- 含义：
  - 如果现在继续推进，执行侧成功落地的把握有多高。
- 主要来源：
  - `WorkerProfile`
  - `HarnessProfile`
  - `RuntimeEnvProfile`
  - `VerifierResult`
  - `PlatformIncident`

### 4. `closureConfidence`

- 含义：
  - 当前局部工作是否真正达到“可被正式接受的结束”。
- 主要来源：
  - `ComponentEndSignal`
  - `EndSignalEvaluation`
  - `ProofCompleteness`
  - `VerifierResult`
  - `PRDAcceptanceDecision`

## Pressure Axis

除了置信度，还必须单独表达接管压力：

### `takeoverPressure`

- 取值建议：
  - `none`
  - `low`
  - `medium`
  - `high`
  - `critical`
- 作用：
  - 表示外部接管通道当前对系统的施压程度。
- 它不是概率，而是优先级与干预强度信号。

## Fusion Rules

### 1. 决策栏先看硬约束，再看综合置信度

- 任何 `block` 级联锁或 readiness 拒绝，都不能被平均分冲淡。
- 也就是说：
  - 即便 `intentConfidence` 很高
  - 只要 `safetyConfidence` 被硬阻断
  - `railStatus` 也不能显示为 `ready`

### 2. 局部结束只能提升局部 closure 判断

- 某个 worker、verifier、repair、takeover 组件结束自己的工作，
- 只能影响 `closureConfidence` 或 `latestEndSignalSummary`。
- 不能自动把 `program` 或整轮循环提升成完成态。

### 3. 只有正式 acceptance 才能关闭整轮

- `acceptance-issued` 之前，
- `closureConfidence` 再高，也只能表达“很接近可收尾”。
- 不能表达“已经整体完成”。

### 4. 接管压力可以压低综合可继续推进结论

- 如果存在：
  - 活动中的接管请求
  - 待执行覆写
  - 高优先级外部控制器接管
- 那么即使其余置信度不低，
- `railStatus` 也至少应进入 `attention`。

### 5. 学习结论必须反哺意图置信度

- 如果最近 `DriverLearningRecord` 明确指出：
  - AI 司机持续误判 blocker
  - 路由选择反复错误
  - 证据完备度判断不稳定
- 那么 `intentConfidence` 不应继续维持高位。

## Rail Status Recommendation

建议 `DecisionRailView.railStatus` 首批固定为：

- `loading`
- `ready`
- `attention`
- `blocked`

解释规则：

- `ready`
  - 可继续推进，且没有高优先级接管/结束争议
- `attention`
  - 还能继续看，但存在接管、学习偏差、局部结束争议或中等级风险
- `blocked`
  - 存在硬阻断、readiness 不通过、关键证据缺失或平台事故

## View Contract

### `DecisionRailView`

推荐字段：

- `programId`
- `railStatus`
- `recommendedAction`
- `oneLineReason`
- `intentConfidence`
- `safetyConfidence`
- `executionConfidence`
- `closureConfidence`
- `takeoverPressure`
- `readinessSummary`
- `currentIntentSummary`
- `latestLearningSummary`
- `activeTakeoverSummary`
- `latestEndSignalSummary`
- `topReasons`
- `updatedAt`

### `RiskConfidenceSummaryView`

推荐字段：

- `intentConfidence`
- `safetyConfidence`
- `executionConfidence`
- `closureConfidence`
- `takeoverPressure`
- `dominantRisk`
- `dominantReason`

### `LatestEndSignalSummaryView`

推荐字段：

- `signalType`
- `signalStatus`
- `signalScope`
- `acceptedAs`
- `nextSuggestedRoute`
- `notYetClosedScope`

## UI Projection Rule

- 右栏不建议只显示一个“总分”。
- 更稳的表达方式是：
  - 一个主状态标签
  - 一条 `recommendedAction`
  - 一组精简 `topReasons`
  - 一块四轴风险/置信度摘要
  - 一块最新结束信号摘要

这样用户能同时看清：

- AI 司机想干什么
- 自动辅助驾驶系统为什么允许/警告/阻断
- 哪一步已经结束
- 哪一步还没有正式闭环

## Message Projection Rule

- 手机或消息控制面不需要展示完整四轴明细，
- 但必须继承相同的融合结论。

最小导出建议：

- `railStatus`
- `recommendedAction`
- `oneLineReason`
- `takeoverPressure`
- `latestEndSignalSummary`
- `topReasons` 的前 1 到 2 条

## API Consequence

- `GET /api/v1/programs/{programId}/decision-rail`
  - 返回 `DecisionRailView`
- `GET /api/v1/programs/{programId}/end-signals`
  - 返回 `EndSignalSummaryView` 与 timeline 明细
- `GET /api/v1/programs/{programId}/driver-learning`
  - 返回 `DriverLearningSummaryView`
- `GET /api/v1/programs/{programId}/takeover`
  - 返回 `TakeoverSummaryView`

## Example

```json
{
  "programId": "program-001",
  "railStatus": "attention",
  "recommendedAction": "wait-takeover-decision",
  "oneLineReason": "Latest verifier signal was accepted locally, but takeover is pending and proof is still incomplete.",
  "intentConfidence": 0.72,
  "safetyConfidence": 0.64,
  "executionConfidence": 0.78,
  "closureConfidence": 0.41,
  "takeoverPressure": "high",
  "readinessSummary": "Core prerequisites passed, but closure is not yet accepted.",
  "currentIntentSummary": "AI driver wants to continue batch validation.",
  "latestLearningSummary": "Recent learning suggests the driver should not auto-upgrade verifier completion to closure.",
  "activeTakeoverSummary": "External controller requested review before continue.",
  "latestEndSignalSummary": {
    "signalType": "verifier-finished",
    "signalStatus": "finished",
    "signalScope": "runtime-story-only",
    "acceptedAs": "verification-complete",
    "nextSuggestedRoute": "proof-completeness-check",
    "notYetClosedScope": "program"
  },
  "topReasons": [
    "Takeover request is still active.",
    "Proof completeness has not yet passed."
  ],
  "updatedAt": "2026-05-18T06:20:00+08:00"
}
```

## Freeze Conclusion

- 从现在起，右栏决策栏不再只是 readiness 或 ops 摘要。
- 它必须成为“自动辅助驾驶系统 + AI 司机”的正式融合读模型：
  - 把意图、学习、接管、结束信号和风险/置信度压到同一层
  - 但又不允许任何局部结束越权冒充全局完成
