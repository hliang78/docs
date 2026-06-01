---
topic: generic-ai-autodev-platform
kind: evidence
title: 现有项目规划对历史问题的逐条解决能力分析
createdAt: 2026-05-18T00:20:00+0800
program: true
---

# Problem Resolution Analysis Against Current Project

## Purpose

- 这份文档不是继续提问题，而是回答一个更严格的问题：
  - 自动驾驶系统现在这套规划，是否真的能解决上一轮提取出的历史问题。
- 分析对象：
  - [problem-extraction-from-019e1946-to-now.md](/Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/generic-ai-autodev-platform/evidence/problem-extraction-from-019e1946-to-now.md)
- 判断标准：
  - 不是“提到了这个问题”就算解决。
  - 只有当当前项目里已经出现了足够具体的对象、边界、状态、路由或存储决策，才算具备真实解法。

## Status Legend

- `covered`
  - 当前规划已经给出足够明确的对象或机制，按这套设计落地，原则上能真实解决该问题。
- `partial`
  - 当前方向是对的，但还缺关键 schema、路由细则、对象粒度、验证规则或产品承接方式，暂时不能算“确定能解决”。
- `not-yet-covered`
  - 当前规划还没有真正覆盖这个问题，或被明确后移，不能声称已解决。

## High-Level Verdict

- 总体判断：
  - 这次新项目方向是对的，而且明显比旧体系更接近“能真正解决问题”的状态。
  - 但还不能说“所有问题都已被现有规划彻底解决”。
- 当前粗分：
  - `covered`: 37 项
  - `partial`: 2 项
  - `not-yet-covered`: 0 项
- 最关键结论：
  - 三平面分离、truth plane、对象存储边界、runtime profile、preflight、repair plane 这些核心方向已经足够强，是这次规划最有价值的部分。
  - 之前缺的 provider/runtime、verifier/evidence、readiness、mobile/message projection 这四组 formal contract 已经补齐。
  - 在原问题集之外，又新增冻结了两条顶层规则：
    - `PRD planning plane <-> AutoDev execution plane` 双向自动循环
    - harness 独立治理层
  - 现在还没完全落稳的，主要只剩：
    - mixed-lane 多 worker 编排细则
    - identifier / lookup / ticket 命中规则

## Core Evidence Base

- [alignment.md](/Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/generic-ai-autodev-platform/alignment.md)
- [program-plan.md](/Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/generic-ai-autodev-platform/program-plan.md)
- [object-state-freeze-checklist.md](/Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/generic-ai-autodev-platform/object-state-freeze-checklist.md)
- [role-object-state-map.md](/Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/generic-ai-autodev-platform/role-object-state-map.md)
- [object-storage-file-boundary.md](/Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/generic-ai-autodev-platform/object-storage-file-boundary.md)
- [runtime-governance-and-super-repair.md](/Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/generic-ai-autodev-platform/runtime-governance-and-super-repair.md)
- [openclaw-control-plane-mapping.md](/Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/generic-ai-autodev-platform/openclaw-control-plane-mapping.md)
- [prd-planning-plane-mapping.md](/Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/generic-ai-autodev-platform/prd-planning-plane-mapping.md)
- [validation-baseline-decision.md](/Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/generic-ai-autodev-platform/validation-baseline-decision.md)
- [frontend-workbench-decision.md](/Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/generic-ai-autodev-platform/frontend-workbench-decision.md)
- [frontend-state-query-decision.md](/Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/generic-ai-autodev-platform/frontend-state-query-decision.md)
- [frontend-final-alignment-checklist.md](/Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/generic-ai-autodev-platform/frontend-final-alignment-checklist.md)
- [prd-autodev-bidirectional-loop-freeze.md](/Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/generic-ai-autodev-platform/prd-autodev-bidirectional-loop-freeze.md)
- [harness-governance-freeze.md](/Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/generic-ai-autodev-platform/harness-governance-freeze.md)
- [business-orchestration-state-impact-analysis.md](/Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/generic-ai-autodev-platform/evidence/business-orchestration-state-impact-analysis.md)

## A. 入口与控制面问题

### P-01 自然语言入口不能等价替代命令入口

- Status: `covered`
- 当前项目如何解决：
  - 把旧 `loops/*.conf` 明确降级为迁移来源，正式主模型升级为 `RuntimeTaskPolicy`、`RuntimeStory`、`ExecutionPack`。
  - 控制面对象已经被正式提出，不再让聊天入口直接充当唯一控制语义。
- 依据：
  - `alignment.md`
  - `openclaw-control-plane-mapping.md`
- 结论：
  - 只要按当前控制平面对象落地，这个问题能真实解决。

### P-02 控制面需要手机友好的短格式回报，而不是长文报告

- Status: `covered`
- 当前项目如何解决：
  - [human-ops-message-projection.md](/Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/generic-ai-autodev-platform/human-ops-message-projection.md) 已正式冻结：
    - `MessageProjection`
    - `MobileSummary`
    - `ApprovalMessageTemplate`
    - `RepairMessageTemplate`
    - `StatusMessageTemplate`
  - 同时明确：
    - Web workbench 仍是 primary UI
    - 手机/消息控制面只能作为 structured export
    - 一条消息只做一个目的，且正文不承载 secrets
- 结论：
  - 这条问题现在已经有正式机制解法。

### P-03 人工审批不是附属动作，而是系统一级对象

- Status: `covered`
- 当前项目如何解决：
  - `ApprovalProfile` 已明确进入控制平面。
  - `approval.required` 路由被单独冻结，不再与 repair/planner 混流。
- 依据：
  - `object-state-freeze-checklist.md`
  - `role-object-state-map.md`
  - `openclaw-control-plane-mapping.md`
- 结论：
  - 这一条已经具备真实解法。

## B. Provider / Profile / Runtime 配置问题

### P-04 provider 名称、模型 profile、harness 入口最初不稳定

- Status: `covered`
- 当前项目如何解决：
  - [provider-runtime-policy-freeze.md](/Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/generic-ai-autodev-platform/provider-runtime-policy-freeze.md) 已正式冻结：
    - `ProviderProfile`
    - `ProviderEndpoint`
    - `HarnessBinding`
  - provider 身份、endpoint 路由、worker adapter 绑定不再依赖隐式默认值。
- 结论：
  - 这条问题现在已经具备真实解法。

### P-05 模型额度、订阅限制、超时会直接击穿整条自动链

- Status: `covered`
- 当前项目如何解决：
  - [provider-runtime-policy-freeze.md](/Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/generic-ai-autodev-platform/provider-runtime-policy-freeze.md) 已正式冻结：
    - `QuotaPolicy`
    - `TimeoutPolicy`
    - `LivenessPolicy`
  - 同时给出 exhausted、silent hang、timeout、endpoint unhealthy 的结构化治理路线。
- 结论：
  - 这条问题现在已经被正式覆盖。

### P-06 不同角色共享同一模型心智会导致全链不稳定

- Status: `covered`
- 当前项目如何解决：
  - `WorkerProfile`、`RuntimeTaskPolicy`、lane 分离已经明确。
  - 角色和可用能力不再默认共享。
- 依据：
  - `alignment.md`
  - `object-state-freeze-checklist.md`
  - `runtime-governance-and-super-repair.md`
- 结论：
  - 只要实现时不偷懒退回单模型共享，这一条能真实解决。

### P-07 外部能力没有先产品化，运行时才暴露缺口

- Status: `covered`
- 当前项目如何解决：
  - `WorkspaceProfile`、`ToolchainProfile`、`CredentialBinding`、`RuntimeEnvProfile`、`PreflightProbe` 已成正式对象。
  - 执行前必须 probe，不再默认“机器上能用就算能力存在”。
- 依据：
  - `alignment.md`
  - `runtime-governance-and-super-repair.md`
- 结论：
  - 这是当前规划里解决得最实的一类问题。

### P-08 权限与系统级前提缺失时，系统缺少统一 preflight 语义

- Status: `covered`
- 当前项目如何解决：
  - `PreflightProbe` 被正式定义为 turn 前 gate。
  - probe 失败默认禁止正式执行。
- 依据：
  - `alignment.md`
  - `runtime-governance-and-super-repair.md`
- 结论：
  - 已具备真实解法。

## C. 会话、进程、生命周期问题

### P-09 进程存在不等于任务真的在正确执行

- Status: `covered`
- 当前项目如何解决：
  - 通过 `TurnTruth`、`TaskTruth`、`StoryTruth` 把“进程活着”与“业务执行真实状态”分开。
  - 前端和控制器不再直接读零散进程文件。
- 依据：
  - `role-object-state-map.md`
  - `object-storage-file-boundary.md`
- 结论：
  - 当前 truth plane 设计足以解决这个问题。

### P-10 stale lock / stale gateway process / stale pointer 是高频系统病灶

- Status: `covered`
- 当前项目如何解决：
  - `PlatformIncident`、`RepairRun`、`SuperRepairCoordinator` 明确接手机制性残留。
  - `current-story/current-prompt/current-execution-pack` 被降级为 cache，禁止当真相。
- 依据：
  - `runtime-governance-and-super-repair.md`
  - `object-storage-file-boundary.md`
- 结论：
  - 旧残留问题已经被正面建模，而不是再隐藏。

### P-11 daemon 双实例、半启动、孤儿会话都曾真实发生

- Status: `covered`
- 当前项目如何解决：
  - `TurnTruth.status` 明确包含 `orphaned`、`reconciled`。
  - `SuperRepairCoordinator` 负责 residue cleanup 和 probe rerun。
- 依据：
  - `object-state-freeze-checklist.md`
  - `runtime-governance-and-super-repair.md`
- 结论：
  - 生命周期问题在当前规划里已经进入正式治理范围。

### P-12 `prompt.submitted` 后长时间没有有效进展，是弱 worker 的典型失效形态

- Status: `covered`
- 当前项目如何解决：
  - [provider-runtime-policy-freeze.md](/Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/generic-ai-autodev-platform/provider-runtime-policy-freeze.md) 已补上：
    - `firstProgressTimeoutMs`
    - `silentHangTimeoutMs`
    - `heartbeatIntervalMs`
    - `progressSignalRule`
    - `orphanDetectionRule`
  - 这使 hang、静默、会话假存活不再只是经验判断。
- 结论：
  - 这条问题现在已具备 formal liveness contract。

### P-13 0B 状态文件说明“状态存在”与“状态可用”是两回事

- Status: `covered`
- 当前项目如何解决：
  - 核心状态真相被移到 MySQL authoritative store。
  - 文件状态只能是 cache / trace / export，不能参与业务决策。
- 依据：
  - `object-storage-file-boundary.md`
- 结论：
  - 这是新项目最明确解决的一类问题。

## D. 状态真相与对象归并问题

### P-14 状态真相分裂是旧体系最核心的问题之一

- Status: `covered`
- 当前项目如何解决：
  - 明确提出 `StoryTruth`、`BatchTruth`、`TurnTruth`、`TaskTruth`、`RepairTruth`。
  - 明确提出 `StoryTruthReducer`、`BatchTruthReducer` 等归并关系。
- 依据：
  - `role-object-state-map.md`
  - `object-state-freeze-checklist.md`
- 结论：
  - 当前项目对这条问题的解法是成立的。

### P-15 monitor / status / detail 曾经不是同一真源

- Status: `covered`
- 当前项目如何解决：
  - 前端被禁止直接读零散文件。
  - 所有展示都应读统一 truth 与 evidence read model。
- 依据：
  - `role-object-state-map.md`
  - `object-storage-file-boundary.md`
  - `frontend-state-query-decision.md`
- 结论：
  - 这条问题在当前项目里已被正面解决。

### P-16 旧 blocked / 旧 report / 旧 handoff 会覆盖新结论

- Status: `covered`
- 当前项目如何解决：
  - authoritative store + truth reducer + file 降级为 projection/cache。
  - 明确禁止从 `last-report`、handoff、`current-story` 反推最终真相。
- 依据：
  - `object-storage-file-boundary.md`
  - `role-object-state-map.md`
- 结论：
  - 当前规划足以扭转这类覆盖问题。

### P-17 合成 ticket 会污染真实业务 ticket

- Status: `covered`
- 当前项目如何解决：
  - 平台事故、blocker、repair 被拆成 `PlatformIncident`、`BlockerRecord`、`RepairRun`。
  - 框架机制票据不再需要伪装成业务 story truth。
- 依据：
  - `openclaw-control-plane-mapping.md`
  - `runtime-governance-and-super-repair.md`
- 结论：
  - 这条问题已经有结构化解法。

### P-18 `reviewed` / `draft` / `open` / `done` / `blocked` / `approval` 语义曾长期混线

- Status: `covered`
- 当前项目如何解决：
  - 规划状态、执行状态、repair 状态被分层冻结，不再用一套字段混跑。
- 依据：
  - `object-state-freeze-checklist.md`
- 结论：
  - 当前规划可以真实解决这一条。

## E. Story 编排、批次治理、lane boundary 问题

### P-19 当前 story 注入会被旧 handoff 牵着走

- Status: `covered`
- 当前项目如何解决：
  - `ExecutionPack` 成为正式编译产物。
  - `current-story/current-prompt/current-execution-pack` 被降级为 cache。
- 依据：
  - `openclaw-control-plane-mapping.md`
  - `object-storage-file-boundary.md`
- 结论：
  - 当前规划已正面解决这一条。

### P-20 “没有可选 story”经常不是没活干，而是前一票语义没有被正确路由

- Status: `covered`
- 当前项目如何解决：
  - blocker taxonomy 和 route map 已冻结。
  - `planning.gap`、`approval.required`、`environment.*` 不再共享一条 blocked 路径。
- 依据：
  - `role-object-state-map.md`
  - `runtime-governance-and-super-repair.md`
- 结论：
  - 当前设计能真实减少这类“假无票”现象。

### P-21 PRD、执行、repair 三条链路的边界是后来才被迫修清的

- Status: `covered`
- 当前项目如何解决：
  - 规划平面、控制平面、执行/repair 平面被明确分开。
  - `dagengine` 也被限定为执行内核，而不是整个平台。
- 依据：
  - `alignment.md`
  - `prd-planning-plane-mapping.md`
  - `openclaw-control-plane-mapping.md`
  - `dagengine-integration-decision.md`
- 结论：
  - 这是当前项目最根本的修正之一。

### P-22 PRD 过早拆成小 story 会丢掉 batch 规划价值

- Status: `covered`
- 当前项目如何解决：
  - `Program -> Workstream -> StoryBatch -> RuntimeStory` 被明确成主关系。
  - 首期规划反复强调 reviewed planning slice、batch-first，而不是粗暴出微 story。
- 依据：
  - `program-plan.md`
  - `prd-planning-plane-mapping.md`
  - `role-object-state-map.md`
- 结论：
  - 当前项目对这条问题的解法是成立的。

### P-23 混合 lane 被错误当成单能力 worker 任务下发

- Status: `partial`
- 当前项目已有进展：
  - `ExecutionPack`、`WorkerProfile`、`RuntimeTaskPolicy` 已经提出。
  - 明确反对裸 story 下发。
- 仍缺什么：
  - 多 worker join / handoff / mixed execution pack 的具体编排策略还没冻成 schema。
  - 目前更像“原则正确”，但还未到“编排细则充分”的程度。
- 结论：
  - 有解题方向，但暂时只能算部分解决。

### P-24 ticket 匹配与 story 命中曾经不精确

- Status: `partial`
- 当前项目已有进展：
  - 已把对象层提升为主真相层，理论上可以避免靠模糊文本命中。
- 仍缺什么：
  - 当前文档没有正式冻结 `identifier strategy`、`lookup rule`、`human-facing ticket reference format`。
- 结论：
  - 这个问题的根因已经被看见，但还没彻底被机制化。

## F. 验证、evidence、假完成问题

### P-25 “页面能打开/类型能过”曾多次被误当成真实完成

- Status: `covered`
- 当前项目如何解决：
  - [evidence-verifier-contract.md](/Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/generic-ai-autodev-platform/evidence-verifier-contract.md) 已正式区分：
    - `smoke`
    - `contract`
    - `business-proof`
    - `readiness-gate`
  - 因而“能打开/能编译”只能证明 smoke 或 contract，不能单独推进 `done`。
- 结论：
  - 这条问题现在已经有明确机制约束。

### P-26 `DONE` 不能只靠模型 footer 决定

- Status: `covered`
- 当前项目如何解决：
  - `verify` 与 truth reducer 被正式上提。
  - `Worker` 被禁止直接判最终完成态。
- 依据：
  - `role-object-state-map.md`
  - `object-state-freeze-checklist.md`
  - `openclaw-control-plane-mapping.md`
- 结论：
  - 这条问题已经被当前项目正面解决。

### P-27 blocker-only evidence 不是 closure

- Status: `covered`
- 当前项目如何解决：
  - `blocked`、`approval`、`done` 语义被拆开。
  - `BlockerRecord` 与 `EvidenceSet` 并存，不再把“有 blocker 文档”误当“闭环完成”。
- 依据：
  - `object-state-freeze-checklist.md`
  - `role-object-state-map.md`
- 结论：
  - 当前规划足以解决这类误 closure。

### P-28 浏览器可达性验证与真实执行验证不是一回事

- Status: `covered`
- 当前项目如何解决：
  - 已将 `readiness`、`evidence`、`validation`、`business execution` 分层。
  - 前端也明确只做 `只读 + 审阅 + 状态推进` 起步，不把可达性混同为执行成功。
- 依据：
  - `validation-baseline-decision.md`
  - `frontend-final-alignment-checklist.md`
- 结论：
  - 当前项目在概念上已经把这条分清。

### P-29 从截断 summary 反推成功与否是不可靠的

- Status: `covered`
- 当前项目如何解决：
  - 彻底禁止“export 反向写 truth”。
  - summary/export 只能是 projection，不是 authoritative store。
- 依据：
  - `object-storage-file-boundary.md`
- 结论：
  - 当前项目对这条问题的解法非常明确。

### P-30 没有 durable evidence 文件时，历史成功声明不可被完全信任

- Status: `covered`
- 当前项目如何解决：
  - [evidence-verifier-contract.md](/Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/generic-ai-autodev-platform/evidence-verifier-contract.md) 已正式冻结：
    - `EvidenceSet`
    - `EvidenceArtifact`
    - `VerifierResult`
    - `ProofCompleteness`
    - durable proof minimum rule
  - 没有 durable artifact 时，不能进入正式 closure。
- 结论：
  - 这条问题现在已经被明确解决。

## G. Browser / 真实环境 / 凭据边界问题

### P-31 浏览器验证多次被 worker context 或 policy 阻断

- Status: `covered`
- 当前项目如何解决：
  - `RuntimeEnvProfile` + `PreflightProbe` + `ApprovalProfile` 明确回答“当前 worker 是否具备浏览器能力”。
- 依据：
  - `runtime-governance-and-super-repair.md`
  - `alignment.md`
- 结论：
  - 当前规划已具备真实解法。

### P-32 gateway token / auth token 失效会把真实验证直接打断

- Status: `covered`
- 当前项目如何解决：
  - `CredentialBinding`、`PreflightProbe`、`PlatformIncident`、`RepairRun` 已形成闭环。
- 依据：
  - `runtime-governance-and-super-repair.md`
  - `object-state-freeze-checklist.md`
- 结论：
  - 这类问题在当前项目里已经被机制化承接。

### P-33 真实远程访问需求很早就存在，但工具与边界不是一开始就准备好的

- Status: `covered`
- 当前项目如何解决：
  - `ToolchainProfile`、`CredentialBinding`、`RuntimeEnvProfile`、`ApprovalProfile` 已经分层。
  - 不再依赖“机器碰巧能远程连”。
- 依据：
  - `runtime-governance-and-super-repair.md`
  - `openclaw-control-plane-mapping.md`
- 结论：
  - 当前规划能真实解决这条问题。

### P-34 敏感信息与 evidence 的边界需要系统强约束

- Status: `covered`
- 当前项目如何解决：
  - `CredentialBinding` 明确只存引用、范围、可见角色、到期信息。
  - evidence 与对象层被明确分离。
- 依据：
  - `runtime-governance-and-super-repair.md`
  - `object-storage-file-boundary.md`
- 结论：
  - 这条问题当前项目已经有明确解法。

## H. 文件分布式真相问题

### P-35 文件既当真相、又当缓存、又当交接、又当导出物

- Status: `covered`
- 当前项目如何解决：
  - `对象在库里，文件在盘上，决策走对象，文件只做证据和导出。`
- 依据：
  - `object-storage-file-boundary.md`
- 结论：
  - 这是当前项目最明确、最强的一条纠偏。

### P-36 从导出物反向重建真相是旧体系的系统债

- Status: `covered`
- 当前项目如何解决：
  - export 投影被明确禁止反向写回 truth。
  - 读模型统一走 API，不走文件拼装。
- 依据：
  - `object-storage-file-boundary.md`
  - `frontend-state-query-decision.md`
- 结论：
  - 当前规划对这条问题的解法成立。

### P-37 文件残留会穿透轮次边界，污染新一轮调度

- Status: `covered`
- 当前项目如何解决：
  - 旧 `current-*` 文件只允许作为 cache。
  - 业务调度改从数据库对象与 truth 读取。
- 依据：
  - `object-storage-file-boundary.md`
- 结论：
  - 这一条已经被正面解决。

## I. 前端与工作台层面的隐含问题

### P-38 现在前端虽然大方向已收口，但它承接的是旧体系里最难的对象

- Status: `covered`
- 当前项目如何解决：
  - 前端已明确不直接读取零散状态文件。
  - [readiness-decision-freeze.md](/Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/generic-ai-autodev-platform/readiness-decision-freeze.md) 已把 `ReadinessDecision` 与 `ReadinessSummaryProjection` 提升为正式对象。
  - [evidence-verifier-contract.md](/Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/generic-ai-autodev-platform/evidence-verifier-contract.md) 与 [provider-runtime-policy-freeze.md](/Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/generic-ai-autodev-platform/provider-runtime-policy-freeze.md) 也补齐了前端依赖的主对象边界。
- 结论：
  - 从规划层看，前端承接这些难对象现在已经有了足够正式的后端 contract。

### P-39 `ready-for-openclaw` 本质上不是一个 badge，而是多对象归并结果

- Status: `covered`
- 当前项目如何解决：
  - [readiness-decision-freeze.md](/Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/generic-ai-autodev-platform/readiness-decision-freeze.md) 已正式冻结：
    - `ReadinessDecision`
    - `ReadinessSummaryProjection`
    - 输入对象
    - 归并规则
    - program/batch promotion rules
  - readiness 已从 UI 提示语升级成正式决策对象。
- 结论：
  - 这条问题现在已经有充分的规划级解法。

## Final Judgment By Category

### 已经具备真实解法的问题

- P-01
- P-02
- P-03
- P-04
- P-05
- P-06
- P-07
- P-08
- P-09
- P-10
- P-11
- P-12
- P-13
- P-14
- P-15
- P-16
- P-17
- P-18
- P-19
- P-20
- P-21
- P-22
- P-25
- P-26
- P-27
- P-28
- P-29
- P-30
- P-31
- P-32
- P-33
- P-34
- P-35
- P-36
- P-37
- P-38
- P-39

### 方向对但还没完全冻完的问题

- P-23
- P-24

### 当前范围还没真正解决的问题

- 无

## What Must Happen Before We Can Claim “This Project Truly Solves Them”

### 1. 必须把 mixed-lane 编排细则补成正式 schema

- 至少补：
  - multi-worker join/handoff 规则
  - mixed execution pack 编排字段
  - lane 间交接与回收语义

### 2. 必须把 identifier / lookup rule 正式冻结

- 至少补：
  - human-facing ticket reference format
  - object lookup rule
  - story / batch / task / export 的统一引用策略

## Final Conclusion

- 这次自动驾驶系统这套规划不是只会重复旧体系，它已经抓住了旧体系最痛的几个根因：
  - 多真相源
  - 文件分布式真相
  - 规划/控制/修复混流
  - runtime 环境未对象化
  - worker 自报完成等于完成
- 所以方向上它是“能解决”的。
- 但如果严格按“确实能解决才行”来要求，现在还不能对全部问题给出 `yes`。
- 更准确的说法是：
  - 这套项目规划已经足以真实解决大部分结构性老问题；
  - 之前最大的 4 个缺口已经补成冻结文档；
  - 剩余没有完全闭合的，主要只剩 mixed-lane 编排细则与 identifier/lookup 规则。
- 因此下一步最对的动作，不是立刻开工实现，而是决定是否继续把这 2 个剩余 partial 也补成冻结文档，或者把它们明确下沉到代码阶段设计。
