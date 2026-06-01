---
topic: generic-ai-autodev-platform
kind: full-stack
title: 运行环境治理与超级修复代理设计稿
createdAt: 2026-05-17T15:55:00+0800
program: true
status: draft
---

# Runtime Governance And Super Repair

## Purpose

- 这份文档专门处理当前新增的 3 个高优先级问题：
  - worker 执行环境信息如何治理
  - 业务层与基础设施层如何分开又协同
  - 如何定义一个能修复平台机制缺陷导致中断的超级修复代理
- 它不是实现方案，而是进入代码前必须冻结的架构约束补丁。

## Why This Must Be Elevated

结合本周会话挖矿，最难修的故障大多不是“代码逻辑写错”，而是以下 3 类问题长期没有被对象化：

1. 环境信息散落在目录、脚本、shell 环境、账号配置、临时说明里。
2. 业务规划问题和基础设施故障问题在 blocked 场景里混流。
3. 运行被平台机制问题打断后，缺少一个稳定的上层恢复者，只能人工补丁。

如果这 3 类问题不在规划阶段先冻结，自动驾驶系统会再次走向“对象没定义，靠 repair 补丁”的老路。

## A. Runtime Environment Governance

## A.1 设计原则

- worker 不直接继承“当前机器碰巧可用的环境”。
- 环境必须是结构化对象，不是自然语言备注。
- 环境必须先 probe，再允许 story 真正开始执行。
- secrets、账号、目录、工具、语言环境变量必须分层存储。
- 不同 lane / role 可以绑定不同环境画像，不共享隐式默认值。

## A.2 必须提升为一等对象的环境信息

### `WorkspaceProfile`

- 负责描述：
  - repoRoot
  - workingDirectory
  - allowedPaths
  - tempDirectories
  - artifactDirectories
  - legacyImportDirectories
- 解决的问题：
  - worker 到底在哪个目录执行
  - 哪些目录允许写
  - 哪些目录只读

### `ToolchainProfile`

- 负责描述：
  - node/python/java/go/browser 等语言与工具版本
  - 必须存在的 CLI
  - 自定义 helper tools
  - 构建/测试命令基线
- 解决的问题：
  - 为什么同一个 story 在不同 worker 上表现不同
  - 为什么“能跑”与“可验证”经常不一致

### `CredentialBinding`

- 负责描述：
  - provider account 引用
  - gateway/token 引用
  - mysql 连接引用
  - remote access / browser / third-party service 凭据引用
- 规则：
  - 只存引用、范围、可见角色、到期信息
  - 不把敏感明文直接散落到 story、report、evidence

### `RuntimeEnvProfile`

- 负责组合：
  - `WorkspaceProfile`
  - `ToolchainProfile`
  - `CredentialBinding`
  - env var policy
  - network / browser / db / remote access capability
- 它回答的是：
  - “某一类 worker 在某一条 lane 上，被允许使用什么环境能力”

### `PreflightProbe`

- 负责在 turn 前检查：
  - workspace 可达
  - toolchain 是否满足
  - env vars 是否齐全
  - token/account 是否可用
  - db / browser / remote access 是否联通
  - residue 是否清理完成
- 没有通过 `PreflightProbe`，默认不应启动 worker 正式执行。

## A.3 运行环境治理规则

1. `ExecutionPack` 只能引用 profile，不直接内嵌大段环境说明。
2. worker 真实执行前，必须把 profile 解析成一次性 `resolved runtime view`。
3. `resolved runtime view` 属于运行时快照，可审计，但不应回写覆盖 profile。
4. helper tools 也必须纳入 `ToolchainProfile`，不能继续依赖“某台机器上碰巧有一个脚本”。
5. 每次 repair 后要重新跑 probe，不能只凭“修过了”继续执行。

## B. Business Layer And Infrastructure Layer Separation

## B.1 必须分开的原因

- 业务层关心的是：
  - program 是否对齐
  - batch 是否 reviewed
  - story scope 是否合理
  - acceptance / validation / evidence 是否充分
- 基础设施层关心的是：
  - provider 是否可用
  - 环境变量是否齐全
  - 目录与工具链是否就绪
  - 浏览器 / db / remote access 是否联通
  - 进程/会话/残留是否健康

旧体系的典型问题就是把这两层都压成一个 `blocked`，结果谁都来接，谁都接不稳。

## B.2 分层建议

### Business Plane

- 核心对象：
  - `Program`
  - `QuestionRound`
  - `ContextBrief`
  - `Workstream`
  - `StoryBatch`
  - `PlanningReview`
  - `RuntimeStory`
- 主要问题类型：
  - scope 缺失
  - acceptance 不完整
  - planning gap
  - approval required

### Infrastructure Governance Plane

- 核心对象：
  - `WorkspaceProfile`
  - `ToolchainProfile`
  - `CredentialBinding`
  - `RuntimeEnvProfile`
  - `PreflightProbe`
  - `PlatformIncident`
  - `RepairRun`
- 主要问题类型：
  - environment workspace / tooling / auth / dependency
  - provider session / capacity
  - residue / process health
  - platform defect / missing helper tool

### Bridge Layer

- 核心对象：
  - `RuntimeTaskPolicy`
  - `WorkerProfile`
  - `ExecutionPack`
- 作用：
  - 把业务 story 编译成带能力约束的执行输入
  - 根据 lane 选择合适 worker 和 runtime env
  - 决定“这个业务目标是否能在当前基础设施上安全执行”

## B.3 路由原则

1. `planning.gap` 进入 `Planner`
2. `approval.required` 进入 `Approval/Human`
3. `environment.*`、`provider.*`、`process.*` 进入 `Repair / SuperRepair`
4. `verification.failed` 默认先保持在业务视角，由 `Controller + Human` 判断是代码问题还是环境伪故障

## C. Super Repair Agent

## C.1 定位

- 这里的“超级 agent”不是一个自由发挥的全能 AI。
- 它应被定义为：`SuperRepairCoordinator`
- 本质是平台机制修复与恢复编排器，而不是业务开发代理。

## C.2 负责什么

- 主动发现并处理平台机制故障：
  - stale current pointers
  - orphan sessions
  - provider stuck / auth expired
  - residue not cleaned
  - missing helper tool
  - runtime env drift
  - probe failed after retry
- 统一发起：
  - residue cleanup
  - probe rerun
  - repair playbook selection
  - retry recommendation
  - human escalation

## C.3 明确不负责什么

- 不负责任何业务规划拆解
- 不直接改 PRD / batch / acceptance
- 不直接把 story 改成 `done`
- 不跳过 reducer 直接写 UI 状态
- 不替代 human 做高风险授权

## C.4 需要的配套对象

### `PlatformIncident`

- 表示平台机制层事故，而不是业务 story blocker 备注
- 至少包含：
  - incidentType
  - detectedBy
  - affectedLane
  - affectedTaskId
  - severity
  - status
  - linkedBlockerId
  - linkedRepairRunId

### `RepairPlaybook`

- 表示结构化修复策略，不是散落在脚本里的隐性知识
- 例如：
  - cleanup residue
  - refresh auth
  - rebind runtime env
  - reinstall helper tool
  - restart engine adapter

### `ProbeSnapshot`

- 表示 probe 某一次执行的结果明细
- 用来回答“修完之后到底恢复了没有”

## C.5 Super Repair 工作流

```text
probe failed / runtime interrupted
-> create PlatformIncident
-> classify blocker
-> choose RepairPlaybook
-> run RepairRun
-> rerun PreflightProbe
-> if healthy: release retry recommendation
-> if still broken: escalate to human
```

## D. 对 MVP 的直接影响

## D.1 首期前端不一定要做全量运维面板

但首期模型里必须先有这些对象，否则后续前端无法稳定扩展：

- `WorkerProfile`
- `WorkspaceProfile`
- `ToolchainProfile`
- `CredentialBinding`
- `RuntimeEnvProfile`
- `PreflightProbe`
- `PlatformIncident`
- `RepairRun`

## D.2 首期 API 至少要预留这些读取面

- profile list / detail
- program decision rail summary
- probe summary
- incident summary
- repair run summary

## D.3 首期不应做的事情

- 不把超级修复代理做成任意 prompt 聊天入口
- 不把 secrets 管理混成 markdown 文档编辑
- 不允许 worker 自己发现环境缺东西后随意扩 scope 安装和修改

## E. 进入代码前需要拍板的新增问题

1. `WorkspaceProfile / ToolchainProfile / CredentialBinding` 已确认采用独立对象建模，不再塞进单一大 `RuntimeEnvProfile`。
2. `PlatformIncident` 已确认接受为 repair 平面一等对象。
3. `SuperRepairCoordinator` 已确认只处理平台机制问题，不处理业务 scope 问题。
4. 首期前端已确认需要展示 profile / incident 的只读摘要。
5. helper tools 是否接受纳入 `ToolchainProfile` 管理，而不是继续靠 README 和 shell 备注。

## Current Recommendation

- 接受环境治理对象化。
- 接受业务层与基础设施层显式分离。
- 接受“超级 agent”被收束为 `SuperRepairCoordinator`，只负责平台机制恢复。
- 在代码前，把这些对象和边界补进候选实体、数据库、API、后端设计文档。

## Confirmed In This Round

- `WorkspaceProfile / ToolchainProfile / CredentialBinding` 独立建模已获确认。
- `PlatformIncident` 作为 repair 平面一等对象已获确认。
- `SuperRepairCoordinator` 只处理平台机制恢复已获确认。
- 首期前端展示 `profile / incident` 只读摘要已获确认。
