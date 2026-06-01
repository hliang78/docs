---
topic: generic-ai-autodev-platform
kind: full-stack
title: 组件结束信号 API 切片
createdAt: 2026-05-18T05:10:00+0800
program: true
status: draft
---

# Component End Signal API Slice

## Purpose

- 这份文档不再讨论“为什么要有结束信号”，
- 而是直接回答首批代码阶段怎么承接：
  - 结束信号如何写入
  - 结束信号如何被评估
  - 前端和消息面如何读取结束信号摘要

## First Slice Scope

- 首批只覆盖：
  - `ComponentEndSignal`
  - `EndSignalEvaluation`
  - `EndSignalProjection`
- 首批不覆盖：
  - 复杂历史筛选台
  - 跨 program 全局结束信号搜索
  - 结束信号规则可视化编排器

## Minimal Write Path

### 1. Emit End Signal

- 触发方：
  - worker
  - verifier
  - repair
  - readiness reducer
  - takeover flow
  - acceptance flow
- 最小写入语义：
  - 某个组件完成当前动作时，先写 `ComponentEndSignal`
  - 不能直接写高层 closure

推荐接口：

```text
POST /api/v1/end-signals
```

推荐请求体：

```json
{
  "ownerObjectType": "runtime-story",
  "ownerObjectId": "story-001",
  "sourceComponentType": "worker",
  "sourceComponentId": "worker-backend-01",
  "signalType": "worker-finished",
  "signalStatus": "finished",
  "signalScope": "runtime-story-only",
  "evidenceRefs": ["evidence-set-001", "verifier-result-001"],
  "nextSuggestedRoute": "wait-verifier"
}
```

### 2. Evaluate End Signal

- 触发方：
  - controller
  - engine reducer
  - acceptance/readiness evaluator
- 最小语义：
  - 系统决定这个结束信号是否能被接受
  - 以及最多能被升级到哪一层

推荐接口：

```text
POST /api/v1/end-signals/{componentEndSignalId}/evaluate
```

推荐请求体：

```json
{
  "decision": "accepted",
  "acceptedAs": "verifier-awaiting-proof",
  "effectiveRoute": "readiness-reducer"
}
```

## Minimal Read Path

### 1. Program-Level End Signal Summary

推荐接口：

```text
GET /api/v1/programs/{programId}/end-signals
```

推荐返回：

```json
{
  "ownerObjectType": "program",
  "ownerObjectId": "program-001",
  "latestSignal": {
    "signalType": "verifier-finished",
    "signalStatus": "finished",
    "signalScope": "runtime-story-only",
    "summary": "Verifier finished, but closure not yet accepted."
  },
  "latestEvaluation": {
    "decision": "accepted",
    "acceptedAs": "verification-complete",
    "effectiveRoute": "proof-completeness-check"
  },
  "pendingSignals": 2,
  "updatedAt": "2026-05-18T05:10:00+08:00"
}
```

### 2. Decision Rail Aggregation

- 右栏主接口不应自己拼结束信号，
- 应由页面级 read model 一起返回。

推荐补入：

```json
{
  "currentIntentSummary": "...",
  "latestLearningSummary": "...",
  "activeTakeoverSummary": "...",
  "latestEndSignalSummary": {
    "signalType": "repair-finished",
    "acceptedAs": "repair-complete-rerun-required",
    "nextSuggestedRoute": "rerun-verifier"
  }
}
```

## View Model Recommendation

### `EndSignalSummaryView`

推荐字段：

- `ownerObjectType`
- `ownerObjectId`
- `latestSignalType`
- `latestSignalStatus`
- `latestSignalScope`
- `latestSignalSummary`
- `latestAcceptedAs`
- `nextSuggestedRoute`
- `pendingSignalCount`
- `updatedAt`

### `EndSignalTimelineItemView`

推荐字段：

- `componentEndSignalId`
- `sourceComponentType`
- `signalType`
- `signalStatus`
- `signalScope`
- `evaluationDecision`
- `acceptedAs`
- `emittedAt`

## Frontend Contract

- 首批前端不需要做“结束信号管理台”。
- 但至少要能：
  - 在右栏看到最新结束信号摘要
  - 在 batch/program 详情里看到它没有被错误放大成全局 close
  - 在消息面看到“结束了什么，但还没闭环什么”

## Mutation Rule

- 前端不得直接提交：
  - `story-done`
  - `batch-completed`
  - `program-closed`
- 前端如果需要参与结束动作，
- 只能触发：
  - 接管
  - 审批
  - acceptance
- 由后端生成相应 `ComponentEndSignal`

## First Slice Success Criteria

1. worker/verifier/repair/readiness/takeover/acceptance 都能发结构化结束信号。
2. 所有结束信号都必须经过 `EndSignalEvaluation`。
3. `DecisionRailView` 能展示最新结束信号摘要。
4. 局部结束信号不会再被前端或消息面误渲染成全局 closure。
