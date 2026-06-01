---
topic: generic-ai-autodev-platform
kind: full-stack
title: Evidence 与 Verifier Contract 冻结
createdAt: 2026-05-18T01:32:00+0800
program: true
status: draft
---

# Evidence Verifier Contract

## Purpose

- 这份文档要解决的不是“怎么多收集一些日志”，而是两个更关键的问题：
  - 什么才算完成所需的有效证明
  - 什么验证结果有资格推动 truth 进入 `done`
- 旧体系里最大的假完成来源，不是没人验证，而是 verifier、evidence、closure 之间没有正式 contract。

## Why This Must Be Frozen

- `页面能打开`、`类型能过`、`worker footer 说 done`、`有 blocker 文档`，都曾被误用成 closure 依据。
- 如果 `EvidenceSet`、`VerifierResult`、`ProofCompleteness` 不冻结，新的对象层依然会被“看起来像完成”的文本污染。
- 自动驾驶系统必须明确：
  - `DONE requires verifier + sufficient proof`
  - 不是 `DONE requires worker says done`

## Formal Objects

### `EvidenceSet`

- 作用：
  - 表示某个 `RuntimeStory`、`TurnTruth`、`ReadinessDecision` 的证据集合。
- 至少包含：
  - `evidenceSetId`
  - `ownerObjectType`
  - `ownerObjectId`
  - `evidenceArtifacts`
  - `proofCompletenessId`
  - `generatedAt`
  - `generatedBy`
  - `status`
- 规则：
  - `EvidenceSet` 是对象，不是一个目录名。
  - 证据文件丢失不应直接改写 story truth，但应降低 proof completeness。

### `EvidenceArtifact`

- 作用：
  - 表示一个可索引、可审计的证据条目。
- 至少包含：
  - `evidenceArtifactId`
  - `evidenceSetId`
  - `artifactType`
  - `storageUri`
  - `sourceObjectType`
  - `sourceObjectId`
  - `capturedAt`
  - `capturedBy`
  - `durabilityLevel`
  - `secretRiskLevel`
- 常见类型：
  - screenshot
  - browser video
  - command output snapshot
  - diff export
  - api response snapshot
  - structured verification report

### `VerifierResult`

- 作用：
  - 表示一次结构化验证的结果，而不是报告正文。
- 至少包含：
  - `verifierResultId`
  - `runtimeStoryId`
  - `verifierType`
  - `status`
  - `verdict`
  - `checkedAssertions`
  - `failedAssertions`
  - `linkedEvidenceSetId`
  - `executedAt`
  - `executedBy`
- 常见类型：
  - `smoke`
  - `contract`
  - `business-proof`
  - `readiness-gate`

### `ProofCompleteness`

- 作用：
  - 回答“现有证据是否足够支撑当前结论”。
- 至少包含：
  - `proofCompletenessId`
  - `ownerObjectType`
  - `ownerObjectId`
  - `requiredProofClasses`
  - `presentProofClasses`
  - `missingProofClasses`
  - `verdict`
  - `assessedAt`
- 典型 verdict：
  - `sufficient`
  - `insufficient`
  - `blocker-only`
  - `stale`

## Verification Classes

### `smoke`

- 证明：
  - 基础可达性或最小流程是否启动。
- 不能单独证明：
  - 业务目标已完成。

### `contract`

- 证明：
  - API、schema、状态约束、对象边界是否符合契约。
- 作用：
  - 防止“勉强能跑，但已经偏离对象 contract”。

### `business-proof`

- 证明：
  - 业务目标或用户路径真的成立。
- 例如：
  - PRD/workbench 中对象状态推进正确
  - readiness gate 归并结果与 blocker 摘要一致

### `readiness-gate`

- 证明：
  - 某个 batch 或 program 是否达到了进入下一阶段的 gate。
- 不是执行成功证明，而是推进决策证明。

## Durable Proof Minimum Rule

1. 任何 `done` 结论都必须绑定至少一个 `VerifierResult`。
2. 任何 `done` 结论都必须绑定一个 `EvidenceSet`。
3. 任何 `done` 结论都必须通过 `ProofCompleteness.verdict = sufficient`。
4. 至少一个证据条目必须是 durable artifact：
   - 可重新索引
   - 有对象来源 id
   - 有生成时间
   - 不依赖临时 stdout 滚动窗口
5. 只有短 summary、worker footer、口头说明，没有 durable artifact 时，不能进入正式 closure。

## Closure Rules

### DONE Rule

- `RuntimeStory.status = done` 的最低前提：
  - 至少一个通过的 `VerifierResult`
  - 至少一个关联的 `EvidenceSet`
  - `ProofCompleteness = sufficient`
  - 无未解释的关键失败断言

### Blocker Rule

- blocker 证据只证明：
  - 为什么当前没法继续
  - 卡在哪里
- blocker 证据不能证明：
  - 当前已经完成
  - 问题已经闭环
- 也就是说：
  - `blocker-only evidence is not closure`

### Worker Footer Rule

- worker 可以提交：
  - patch
  - report
  - evidence candidate
  - self-assessment
- worker 不能直接提交：
  - 最终 `done`
  - 最终 `readiness passed`
  - 最终 `proof sufficient`
  - 最终 `program close`

## End Signal Relationship

- worker、verifier、repair 结束时，都应先生成 `ComponentEndSignal`。
- `ComponentEndSignal` 只能说明“当前组件动作结束了”，
- 不能绕过 `EndSignalEvaluation` 直接放大成 story close、batch close 或 program close。

## Readiness Relationship

- `ReadinessDecision` 只能读取结构化 `VerifierResult`、`EvidenceSet`、`ProofCompleteness`。
- readiness 结果条不能只显示“passed”，必须知道：
  - 是哪类 verifier 通过
  - 哪些 proof class 已满足
  - 哪些还缺失
- 同时，关键 verifier/evidence 结论也应能沉淀成 `DriverLearningSignal`，供 AI 司机下一轮修正判断。

## Storage Rules

1. `EvidenceSet`、`EvidenceArtifact`、`VerifierResult`、`ProofCompleteness` 都必须是对象层可查询实体。
2. markdown 报告、截图、视频、日志文件是 artifact，不是 verifier result 本体。
3. export summary 不允许反向替代 proof completeness。
4. secret-bearing artifact 必须通过 `secretRiskLevel` 标记，消息投影与前端摘要默认只展示脱敏信息。

## What This Freeze Solves

- P-25 “页面能打开/类型能过”被误当真实完成
- P-26 `DONE` 不能只靠模型 footer 决定
- P-27 blocker-only evidence 不是 closure
- P-30 没有 durable evidence 时，历史成功声明不可完全信任

## Implementation Consequence

- 首期实现至少要提供：
  - verifier result schema
  - evidence index schema
  - proof completeness reducer
- 首期还应明确：
  - 哪些 verifier/evidence 失败会生成 `DriverLearningSignal`
  - 哪些 proof 缺口会触发接管建议，而不是只写进 summary
  - 哪些 verifier/evidence 结论会生成 `ComponentEndSignal`
  - 哪些局部结束信号会被拒绝升级成 closure
- 即使前端首期只做 `只读 + 审阅 + 状态推进`，也必须读结构化 verifier/evidence 摘要，而不是 report 全文。
