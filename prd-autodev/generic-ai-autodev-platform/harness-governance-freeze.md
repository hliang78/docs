---
topic: generic-ai-autodev-platform
kind: full-stack
title: Harness 治理冻结
createdAt: 2026-05-18T02:08:00+0800
program: true
status: draft
---

# Harness Governance Freeze

## Purpose

- 这份文档补一个之前被低估的关键层：
  - `harness` 不是 provider 后面的一个 adapter 字段。
  - `harness` 实际决定 worker 如何拿上下文、如何调用工具、如何维护 session、如何上报 progress、如何产出 evidence。
- 如果 harness 不被单独治理，自动驾驶系统就会把最关键的执行差异继续藏在脚本和经验里。

## Why Harness Must Be Elevated

- 同一个 provider、同一个模型，在不同 harness 下可能呈现完全不同的执行行为：
  - tool calling 方式不同
  - patch/write 行为不同
  - browser/tool 可用性不同
  - progress signal 不同
  - session lifecycle 不同
  - evidence capture 能力不同
- 所以：
  - `ProviderProfile` 解决“调用谁”
  - `HarnessProfile` 解决“怎么执行”
- 这两者不能继续混在一起。

## Formal Objects

### `HarnessProfile`

- 作用：
  - 表示一种正式可治理的执行 harness 身份。
- 至少包含：
  - `harnessProfileId`
  - `harnessType`
  - `adapterFamily`
  - `supportedTaskKinds`
  - `supportedToolCapabilities`
  - `supportedOutputModes`
  - `status`
- 负责回答：
  - 当前 worker 究竟跑在哪种 harness 上。
  - 该 harness 本身具备哪些执行语义。

### `HarnessSessionPolicy`

- 作用：
  - 冻结 harness 的 session 创建、复用、回收、超时与 orphan 规则。
- 至少包含：
  - `harnessSessionPolicyId`
  - `harnessProfileId`
  - `sessionCreateRule`
  - `sessionReuseRule`
  - `sessionExpiryRule`
  - `orphanRecoveryRule`
  - `sessionCleanupRule`

### `HarnessContextPolicy`

- 作用：
  - 冻结 harness 的上下文打包与注入规则。
- 至少包含：
  - `harnessContextPolicyId`
  - `harnessProfileId`
  - `contextPackRule`
  - `windowBudgetRule`
  - `contextTruncationRule`
  - `fileAttachRule`
  - `toolSchemaInjectRule`

### `HarnessOutputContract`

- 作用：
  - 冻结 harness 可接受和可产出的输出形态。
- 至少包含：
  - `harnessOutputContractId`
  - `harnessProfileId`
  - `patchMode`
  - `reportMode`
  - `progressSignalMode`
  - `evidenceCaptureMode`
  - `failureSignalMode`

## Relationship To Existing Objects

- `HarnessBinding`
  - 不再自己承载全部 harness 语义，而是负责把：
    - `ProviderProfile`
    - `WorkerProfile`
    - `RuntimeTaskPolicy`
    - `HarnessProfile`
    - `HarnessSessionPolicy`
    - `HarnessContextPolicy`
    - `HarnessOutputContract`
    绑定成一个可执行组合。
- `ExecutionPack`
  - 必须显式引用 resolved harness snapshot，而不是只写 provider/model。
- `TurnHandoff`
  - 必须带上 harness 级 progress / failure / evidence 投影。
- `EvidenceSet`
  - 需要知道证据来自哪个 harness 模式。
- `RepairRun`
  - 需要知道修的是 provider 问题、harness 问题，还是两者交叉问题。

## Harness Rules

### Provider Is Not Harness

1. 不能用 provider 名字代替 harness 身份。
2. 不能用模型 profile 代替 harness 能力。
3. 不能假设同一 provider 下所有 lane 的 harness 行为一致。

### Harness Must Affect Scheduling

- controller 选 worker 时，必须同时匹配：
  - `RuntimeTaskPolicy`
  - `WorkerProfile`
  - `ProviderProfile`
  - `HarnessProfile`
- 只匹配模型，不匹配 harness，不能正式发车。

### Harness Must Affect Verification

- verifier 必须知道当前 harness 的输出契约：
  - patch 是直接写文件还是生成 diff
  - progress 是 heartbeat、structured event 还是 session token stream
  - evidence 是截图、日志、structured result 还是组合模式
- 否则 verifier 会错把 harness 差异当业务成功/失败。

### Harness Must Affect Repair

- harness 类问题要能单独建模，例如：
  - session stuck
  - tool bridge broken
  - patch apply mode mismatch
  - browser hook unavailable
  - progress signal lost
- 这些不能全部误归到 provider 或 environment。

## Operational Consequence

- 自动驾驶系统至少要把 harness 看成一个与 provider 并列的治理平面，而不是 provider 的附注。
- 首期即使不做完整 harness 管理台，也必须先让 schema、binding、read model 存在。
- 前端右栏摘要后续也必须能回答：
  - 当前 story 跑在哪个 harness
  - 它支持什么
  - 它当前为什么不健康

## What This Freeze Solves

- 把之前被低估的 harness 风险正式提升到对象层。
- 避免后续再把执行差异错误归因给模型、provider 或 worker 本身。
