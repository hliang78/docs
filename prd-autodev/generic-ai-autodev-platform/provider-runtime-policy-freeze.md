---
topic: generic-ai-autodev-platform
kind: full-stack
title: Provider 与 Runtime Policy 冻结
createdAt: 2026-05-18T01:30:00+0800
program: true
status: draft
---

# Provider Runtime Policy Freeze

## Purpose

- 这份文档补的是运行治理里最容易被“先实现再补救”的缺口：
  - provider 身份不稳定
  - endpoint 与 harness 绑定不透明
  - quota / timeout / liveness 只存在于脚本习惯里
- 目标不是实现 SDK 细节，而是在代码前冻结一组必须落库、必须被 controller 明确读取的治理对象。

## Why This Must Be Formal

- 旧体系里，`provider name`、`model path`、`gateway endpoint`、`harness adapter` 经常散落在环境变量、脚本默认值、worker 心智和临时说明里。
- 结果不是“偶尔配错”，而是整条自动链在不同 worker、不同机器、不同时间点呈现出不同执行语义。
- 只冻结 `RuntimeEnvProfile` 还不够，因为它回答的是“可用什么能力”，不是“provider 侧应该如何被稳定解析、限流、超时和保活”。

## Formal Objects

### `ProviderProfile`

- 作用：
  - 表示一个可被平台识别和治理的 provider 身份。
- 至少包含：
  - `providerProfileId`
  - `providerType`
  - `providerName`
  - `defaultModelRef`
  - `supportedCapabilities`
  - `status`
  - `defaultEndpointId`
  - `defaultHarnessBindingId`
- 负责回答：
  - 这个 lane / worker 实际是在使用哪一类 provider。
  - 这个 provider 默认能力边界是什么。

### `ProviderEndpoint`

- 作用：
  - 表示 provider 的一个可路由 endpoint，而不是把 endpoint 写死在 env var 或脚本里。
- 至少包含：
  - `providerEndpointId`
  - `providerProfileId`
  - `endpointType`
  - `baseUrlRef`
  - `region`
  - `gatewayBindingRef`
  - `healthStatus`
  - `authBindingRef`
- 负责回答：
  - controller 实际连的是哪个入口。
  - 某 endpoint 不健康时应切到哪里。

### `HarnessBinding`

- 作用：
  - 明确 provider/model/worker 与执行 harness 的绑定关系。
  - 但它不是 harness 全部语义本体，harness 本身仍需独立治理对象。
- 至少包含：
  - `harnessBindingId`
  - `providerProfileId`
  - `workerProfileId`
  - `runtimeTaskPolicyId`
  - `harnessProfileId`
  - `harnessSessionPolicyId`
  - `harnessContextPolicyId`
  - `harnessOutputContractId`
  - `adapterType`
  - `modelSelectorRule`
  - `responseMode`
  - `toolCallingMode`
  - `status`
- 负责回答：
  - 同一个 provider 在不同 worker 上用哪个 adapter。
  - model path、tool calling、response format 如何稳定落到执行器。

### `QuotaPolicy`

- 作用：
  - 把额度和并发限制从“运行中临时碰撞”升级成正式对象。
- 至少包含：
  - `quotaPolicyId`
  - `providerProfileId`
  - `requestRateLimit`
  - `tokenBudgetWindow`
  - `concurrencyLimit`
  - `degradeStrategy`
  - `exhaustedRoute`
- 负责回答：
  - 额度耗尽时是等待、降级、切换 endpoint，还是进入 repair。

### `TimeoutPolicy`

- 作用：
  - 冻结 provider call、turn、verification、repair retry 的时间预算。
- 至少包含：
  - `timeoutPolicyId`
  - `providerProfileId`
  - `requestTimeoutMs`
  - `firstProgressTimeoutMs`
  - `silentHangTimeoutMs`
  - `retryBackoffRule`
  - `hardStopRule`
- 负责回答：
  - 多久没有首个有效进展算异常。
  - 超时后 controller 是重试、换路由还是转 incident。

### `LivenessPolicy`

- 作用：
  - 冻结“活着”与“还在有效推进”之间的判断规则。
- 至少包含：
  - `livenessPolicyId`
  - `providerProfileId`
  - `heartbeatIntervalMs`
  - `progressSignalRule`
  - `sessionFreshnessRule`
  - `orphanDetectionRule`
  - `livenessFailureRoute`
- 负责回答：
  - `prompt.submitted` 后多久没进展算 hang。
  - session 存在但无有效输出时怎样创建 incident。

## Binding Rules

1. `RuntimeEnvProfile` 负责能力画像，不直接替代 provider policy。
2. `RuntimeEnvProfile` 必须引用：
   - `ProviderProfile`
   - `ProviderEndpoint`
   - `QuotaPolicy`
   - `TimeoutPolicy`
   - `LivenessPolicy`
3. `CredentialBinding` 只负责凭据引用，不负责 provider 路由策略。
4. `WorkerProfile` 与 `RuntimeTaskPolicy` 通过 `HarnessBinding` 解析到具体 adapter 语义。
5. `HarnessBinding` 必须引用独立的 harness 治理对象，而不是自己承载所有执行语义。
6. `ExecutionPack` 只能引用这些 policy id 与 resolved snapshot，不允许内嵌临时自然语言说明。

## Operational Rules

### Provider Resolution

- controller 选择 worker 时，必须先完成：
  - `RuntimeTaskPolicy -> HarnessBinding`
  - `RuntimeEnvProfile -> ProviderProfile`
  - `ProviderProfile -> ProviderEndpoint`
- 没有 resolved binding 的 story，不允许进入正式执行。

### Quota And Capacity

- provider quota 不足不能被视为普通业务 blocker。
- 当 `QuotaPolicy` 触发耗尽条件时，默认路线是：
  - 先走 degrade / wait / fallback
  - 无法恢复时创建 `PlatformIncident`
  - 必要时进入 `RepairRun`

### Timeout And Silent Hang

- `request timeout`、`first progress timeout`、`silent hang timeout` 必须分开定义。
- 任何超时都必须产生结构化结果：
  - `verifier failure`
  - `blocker`
  - `incident`
  - `repair recommendation`
- 不允许只在日志里出现 “seems stuck”。

### Liveness And Session Health

- `session exists` 不等于 `execution healthy`。
- `LivenessPolicy` 至少要支持：
  - 首进展 SLA
  - 连续静默判断
  - orphan session 判断
  - stale endpoint 判断
- liveness 失败默认进入 `PlatformIncident`，而不是让 planner 或 human 猜。

## Relationship To Existing Objects

- [harness-governance-freeze.md](/Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/generic-ai-autodev-platform/harness-governance-freeze.md)
  - 定义 harness 本身的独立治理层。

- `RuntimeEnvProfile`
  - 表示可用环境能力，并引用 provider 运行策略。
- `CredentialBinding`
  - 表示访问凭据，不替代 provider 身份和 endpoint 路由。
- `PreflightProbe`
  - 必须检查 provider endpoint、auth、quota 可用性、最小 liveness 前提。
- `PlatformIncident`
  - 承接 provider exhausted、timeout hang、endpoint unhealthy、orphan session 等机制故障。
- `RepairRun`
  - 执行 refresh auth、switch endpoint、rebind harness、clear stale session、rerun probe 等治理动作。

## What This Freeze Solves

- P-04 provider 名称、模型 profile、harness 入口不稳定
- P-05 模型额度、订阅限制、超时直接击穿自动链
- P-12 `prompt.submitted` 后长期无有效进展却没有明确 liveness 规则

## Implementation Consequence

- 代码阶段必须把上述对象视为 schema/API 对象，而不是“文档建议”。
- 如果首期实现暂时不做完整 provider 控制台，后端仍必须先把这些对象和 read model 建好。
- 前端首期至少要能读到 provider/harness/quota/liveness 的紧凑摘要，而不是从 report 文本猜当前 runtime 风险。
