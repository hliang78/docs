---
documentStatus: blocked-human-confirmation
topic: generic-ai-autodev-platform
template: 03-实体属性清单模板
createdAt: 2026-05-17
sourceType: planning-mining
---

# 【实体属性清单】通用AI自动化平台_规划与控制域_V1.0

## 1. 文档信息

| 项目 | 内容 |
|------|------|
| 系统名称 | 通用 AI 自动化平台 |
| 版本号 | V1.0 |
| 创建日期 | 2026-05-17 |
| 关联文档 | 【需求概要】通用AI自动化平台_V1.0.md |

## 2. 当前真实规划事实

当前规划阶段已明确或候选的核心实体：

- Program
- PlanningDocument
- Workstream
- StoryBatch
- RuntimeStory
- RuntimeTaskPolicy
- WorkerProfile
- WorkspaceProfile
- ToolchainProfile
- CredentialBinding
- RuntimeEnvProfile
- PreflightProbe
- PlatformIncident
- ExecutionPack
- ApprovalProfile
- TurnHandoff
- BlockerRecord
- RepairRun

新增命名冻结约束：

- 本文档中的实体名全部视为 planning authoritative names。
- 即使后续 `engine/` 内部代码采用自动驾驶短名，也不能在这里直接把正式实体改写成 code name。
- 具体映射见：
  - [autonomous-driving-engine-naming-freeze.md](/Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/generic-ai-autodev-platform/autonomous-driving-engine-naming-freeze.md)
  - [autonomous-driving-engine-code-naming.md](/Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/generic-ai-autodev-platform/autonomous-driving-engine-code-naming.md)

## 2.1 自动驾驶引擎命名映射

| 正式实体名 | engine 内推荐 code name | 人类解释别名 |
|------|------|------|
| `AutonomousDrivingInput` | `DriveInput` | 驾驶输入 |
| `WorldStateSnapshot` | `RoadView` | 路况图 |
| `IntentRequest` | `DriveGoal` | 驾驶目标 |
| `RuntimeCapabilitySnapshot` | `CarSetup` | 车辆配置 |
| `GuardDecision` | `GoCheck` | 发车检查 |
| `ActionPlan` | `NextMove` | 下一步 |
| `BackfeedPlan` | `ReturnPlan` | 回流计划 |
| `DecisionEnvelope` | `DriveDecision` | 决策卡 |
| `ReadinessDecision` | `GoSignal` | 发车信号 |
| `ExecutionPack` | `RunPack` | 运行包 |
| `CycleBackfeed` | `TripReport` | 跑后回报 |

## 3. 候选实体属性清单

| 实体 | 关键属性 | 说明 | 状态 |
|------|----------|------|------|
| Program | id, title, objective, scope, status, currentPhase | 规划根对象 | 候选 |
| PlanningDocument | id, programId, docType, status, path, updatedAt | 规划文档对象 | 候选 |
| Workstream | id, programId, title, purpose, status | 规划子域切片 | 候选 |
| StoryBatch | id, programId, batchNo, status, executionMode, targetLanes | 规划下发批次 | 候选 |
| RuntimeStory | id, batchId, lane, scope, acceptance, validation, status | 控制面最小执行 story | 候选 |
| RuntimeTaskPolicy | id, lane, allowedWrites, validationCommand, runtimePolicy | 控制面 task/lane policy | 候选 |
| WorkerProfile | id, supportedTaskKinds, supportedEnvironmentKinds, writeCapabilities | worker 能力画像 | 当前已有原型 |
| WorkspaceProfile | id, repoRoot, workingDirectory, allowedPaths, artifactDirectories, tempDirectories | 目录与写权限画像 | 新增冻结对象 |
| ToolchainProfile | id, languages, requiredCli, helperTools, baselineCommands | 工具链画像 | 新增冻结对象 |
| CredentialBinding | id, bindingType, referenceKey, visibleRoles, expiresAt | 凭据引用对象 | 新增冻结对象 |
| RuntimeEnvProfile | id, workspaceProfileId, toolchainProfileId, credentialBindingSet, envPolicy | 运行环境组合画像 | 新增冻结对象 |
| PreflightProbe | id, runtimeEnvProfileId, probeType, resultStatus, residueSummary, happenedAt | 执行前环境探针 | 新增冻结对象 |
| PlatformIncident | id, incidentType, severity, affectedTaskId, status, linkedBlockerId | 平台机制性事故对象 | 新增冻结对象 |
| ExecutionPack | id, taskId, workerProfileId, runtimeEnvProfileId, taskKind, contextPack, verificationPolicy | 编译后的执行输入 | 候选 |
| ApprovalProfile | id, risk, allowed, denied, evidenceRequired | 高风险动作审批包 | 当前已有原型 |
| TurnHandoff | taskId, control, ticket, changed, tests, next, blockerClass | 跨 turn 交接对象 | 当前已有原型 |
| BlockerRecord | id, taskId, blockerClass, reason, nextRoute | 阻塞分类对象 | 候选 |
| RepairRun | id, taskId, blockerId, status, evidencePath | repair 生命周期对象 | 候选 |

### 3.1 自动驾驶引擎决策层补充实体

| 实体 | 关键属性 | 说明 | 状态 |
|------|----------|------|------|
| AutonomousDrivingInput | evaluationId, ownerObjectType, ownerObjectId, triggerEvent, worldStateSnapshot, intentRequest, runtimeCapabilitySnapshot, activeInterlocks, cycleContext, evaluatedAt | 引擎评估最小输入 | 新增冻结对象 |
| WorldStateSnapshot | worldStateSnapshotId, ownerObjectType, ownerObjectId, storyTruthIds, batchTruthId, turnTruthId, repairTruthIds, verifierResultIds, evidenceSetIds, proofCompletenessStatus, openBlockerIds, openIncidentIds, latestPreflightProbeId, snapshotVersion, snapshotAt | 世界状态统一快照 | 新增冻结对象 |
| IntentRequest | intentRequestId, ownerObjectType, ownerObjectId, businessOrchestrationStateId, requestedTransitionId, businessPhase, businessIntent, requestedAction, requestedBy, requestedAt | 本轮推进意图 | 新增冻结对象 |
| RuntimeCapabilitySnapshot | runtimeCapabilitySnapshotId, runtimeTaskPolicyId, candidateWorkerProfileIds, runtimeEnvProfileId, providerProfileIds, providerEndpointIds, harnessBindingIds, harnessProfileIds, approvalProfileIds, quotaStatus, livenessStatus, snapshotAt | 执行能力组合快照 | 新增冻结对象 |
| GuardDecision | guardDecisionId, ownerObjectType, ownerObjectId, decision, riskLevel, triggeredGuardRuleIds, requiredInterlockIds, blockingReasonCodes, decisionSummary, decidedAt | 护栏裁定对象 | 新增冻结对象 |
| ActionPlan | actionPlanId, ownerObjectType, ownerObjectId, actionType, actionPayload, requiresHumanApproval, targetLane, targetWorkerProfileId, targetHarnessProfileId, targetProviderProfileId, expectedOutputs, plannedAt | 下一步动作计划 | 新增冻结对象 |
| BackfeedPlan | backfeedPlanId, ownerObjectType, ownerObjectId, emitCycleBackfeed, recalcReadiness, refreshMessageProjection, refreshReadModelKeys, nextOrchestrationStateHint | 回流计划对象 | 新增冻结对象 |
| DecisionEnvelope | decisionEnvelopeId, evaluationId, worldStateSnapshot, intentRequest, guardDecision, requiredInterlocks, chosenActionPlan, reasonChain, emittedCommands, backfeedPlan, generatedAt | 面向前端/消息/审计的统一决策输出 | 新增冻结对象 |

## 4. AI 推导建议

- `Program` 与 `PlanningDocument` 应分离，避免把所有状态堆进单一文档模型。[待人工确认: 架构负责人]
- `RuntimeStory` 与 `StoryBatch` 必须区分，不能一对一硬映射。[待人工确认: 后端负责人]
- `WorkspaceProfile / ToolchainProfile / CredentialBinding` 独立建模已确认，不继续塞进一张大 `RuntimeEnvProfile`。
- `PlatformIncident` 与 `BlockerRecord` 区分已确认，避免把机制性故障继续降格成文本备注。
- 自动驾驶引擎相关实体在规划文档中继续使用 authoritative name；`DriveInput / RoadView / GoSignal / DriveDecision` 仅作为 engine 内部 code name 使用。

## 5. 规划缺口

- 最终数据库/存储结构尚未冻结。
- `PlanningDocument` 的 docType 枚举尚未定稿。
- `CredentialBinding` 的 secret manager 绑定方式尚未定稿。

## 6. 代码事实来源清单

- `docs/prd-autodev/generic-ai-autodev-platform/prd-planning-plane-mapping.md`
- `docs/prd-autodev/generic-ai-autodev-platform/openclaw-control-plane-mapping.md`
- `docs/prd-autodev/generic-ai-autodev-platform/dagengine-kernel-mapping.md`
- `docs/prd-autodev/generic-ai-autodev-platform/runtime-governance-and-super-repair.md`
