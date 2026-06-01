---
topic: generic-ai-autodev-platform
kind: full-stack
title: 角色对象状态关系图
createdAt: 2026-05-17T13:40:00+0800
program: true
status: draft
---

# Role Object State Map

## Purpose

- 这份文档是 [object-state-freeze-checklist.md](/Users/huangliang/project/OneOPS-ALL/docs/prd-autodev/generic-ai-autodev-platform/object-state-freeze-checklist.md) 的关系图版本。
- 目标不是补充新对象，而是把“谁负责什么、谁读写什么、状态怎样流动、前端该看什么”画清楚。
- 后续前端专题讨论、后端接口设计、`dagengine` 承接边界，都应以这份图为准。

## 1. 角色与平面

```mermaid
flowchart LR
    H["Human"]
    P["Planner"]
    C["Controller"]
    W["Worker"]
    R["Repair / SuperRepair"]
    UI["Frontend Workbench"]

    subgraph PP["Planning Plane"]
        PR["Program"]
        QR["QuestionRound"]
        CB["ContextBrief"]
        WS["Workstream"]
        TM["TestMatrix"]
        SB["StoryBatch"]
        RV["PlanningReview"]
    end

    subgraph CP["Control Plane"]
        TP["RuntimeTaskPolicy"]
        RS["RuntimeStory"]
        EP["ExecutionPack"]
        WP["WorkerProfile"]
        WSP["WorkspaceProfile"]
        TCP["ToolchainProfile"]
        CBP["CredentialBinding"]
        RP["RuntimeEnvProfile"]
        PF["PreflightProbe"]
        AP["ApprovalProfile"]
        TH["TurnHandoff"]
        BR["BlockerRecord"]
        PI["PlatformIncident"]
        RR["RepairRun"]
        EV["EvidenceSet"]
    end

    subgraph TR["Truth Plane"]
        ST["StoryTruth"]
        BT["BatchTruth"]
        TT["TurnTruth"]
        KT["TaskTruth"]
        RT["RepairTruth"]
    end

    H --> PR
    H --> RV
    H --> AP
    H --> BR

    P --> QR
    P --> CB
    P --> WS
    P --> TM
    P --> SB
    P --> RV

    RV --> SB
    SB --> RS

    C --> TP
    C --> RS
    C --> EP
    C --> TH
    C --> BR
    C --> EV

    WP --> EP
    WSP --> RP
    TCP --> RP
    CBP --> RP
    RP --> EP
    TP --> WP
    TP --> RP

    EP --> W
    W --> TH
    W --> EV
    W --> BR

    BR --> PI
    PI --> R
    R --> RR
    RR --> RT
    PF --> PI

    EV --> ST
    BR --> ST
    RS --> ST
    SB --> BT
    TH --> TT
    RS --> KT

    ST --> UI
    BT --> UI
    TT --> UI
    RT --> UI
    EV --> UI
```

## 2. 读写边界

### 角色读写矩阵

| 角色 | 可写对象 | 只读对象 | 禁止直接改写 |
|---|---|---|---|
| `Human` | `Program` 边界、`PlanningReview`、`ApprovalProfile`、审批记录 | 全部 truth、evidence、batch、blocker | `StoryTruth`、`TurnTruth`、运行时中间态 |
| `Planner` | `QuestionRound`、`ContextBrief`、`Workstream`、`TestMatrix`、`StoryBatch`、`PlanningReview` | 执行摘要、evidence、truth 投影 | `RuntimeStory`、`RepairRun` |
| `Controller` | `RuntimeStory`、`ExecutionPack`、`TurnHandoff`、`BlockerRecord`、`EvidenceSet` | reviewed `StoryBatch`、profile、truth | `Program`、`PlanningReview` |
| `Worker` | `TurnHandoff`、patch、执行 evidence、执行 blocker 报告 | `ExecutionPack`、必要代码上下文 | `StoryBatch`、`StoryTruth` |
| `Repair / SuperRepair` | `PlatformIncident`、`RepairRun`、repair evidence、repair blocker 更新 | `BlockerRecord`、runtime env profile、probe 结果 | `PlanningReview`、`StoryBatch` |
| `Frontend Workbench` | 简单状态推进动作、审批动作、发布动作 | truth、evidence、planning/control 对象 | 零散状态文件、脚本中间态 |

### 必须坚持的 4 个规则

1. `Planner` 不直接改执行态，只基于 reviewed 的结果和 evidence 继续规划。
2. `Worker` 不直接写 truth，只提交 report、evidence、blocker 事实。
3. `Frontend` 不直接消费 `state.json / progress.json / last-report.txt` 这类零散文件。
4. `Repair / SuperRepair` 只修基础设施与平台机制问题，不改业务 scope。

## 3. 状态流转

```mermaid
stateDiagram-v2
    [*] --> DraftProgram
    DraftProgram --> InResearch: question round started
    InResearch --> Aligned: context brief confirmed
    Aligned --> PlanningReviewed: batch reviewed
    PlanningReviewed --> BatchReady: publishable batches ready
    BatchReady --> ImplementationBlockedHuman: waiting final human requirement

    state "Batch Lifecycle" as BatchLifecycle {
        [*] --> DraftBatch
        DraftBatch --> ReviewedBatch: review passed
        ReviewedBatch --> PublishedBatch: publish accepted
        ReviewedBatch --> BlockedHumanBatch: human confirmation required
        PublishedBatch --> RetiredBatch: replaced or completed
    }

    state "Story Lifecycle" as StoryLifecycle {
        [*] --> OpenStory
        OpenStory --> SelectedStory: scheduler selected
        SelectedStory --> RunningStory: turn started
        RunningStory --> DoneStory: verifier passed
        RunningStory --> BlockedStory: blocker recorded
        RunningStory --> ApprovalStory: approval required
        ApprovalStory --> RunningStory: approval granted
        BlockedStory --> RunningStory: repair done or retry allowed
        BlockedStory --> AbandonedStory: scope dropped
    }

    state "Repair Lifecycle" as RepairLifecycle {
        [*] --> QueuedRepair
        QueuedRepair --> RunningRepair
        RunningRepair --> DoneRepair
        RunningRepair --> FailedRepair
        RunningRepair --> ExpiredRepair
    }
```

## 4. Blocker 路由图

```mermaid
flowchart TD
    B["BlockerRecord"]
    C1["business.scope"]
    C2["business.optimization"]
    C3["planning.gap"]
    C4["approval.required"]
    C5["environment.runtime / auth / tooling"]
    C6["environment.workspace / dependency / secret"]
    C7["provider.session / process.residue / infrastructure.*"]
    C8["verification.failed"]

    P["route-planner"]
    A["route-approval"]
    R["route-repair"]
    H["route-human-review"]

    B --> C1 --> H
    B --> C2 --> H
    B --> C3 --> P
    B --> C4 --> A
    B --> C5 --> R
    B --> C6 --> R
    B --> C7 --> R
    B --> C8 --> H
```

### 当前必须记住的边界

- `environment.*` 不自动回流 `Planner`
- `approval.required` 不自动触发 `Repair`
- `planning.gap` 才能进入下一轮 `Planner`

## 5. 真相源关系

```mermaid
flowchart LR
    CE["command issued"]
    WR["worker report"]
    VR["verifier result"]
    EW["evidence written"]
    AW["approval written"]
    RR["repair result"]
    PP["process probe"]
    SD["scheduler decision"]

    SR["StoryTruthReducer"]
    BR["BatchTruthReducer"]
    TR["TurnTruthReducer"]
    RRD["RepairTruthReducer"]

    SS["StoryTruth"]
    BS["BatchTruth"]
    TS["TurnTruth"]
    RS["RepairTruth"]

    CE --> TR
    WR --> TR
    PP --> TR

    WR --> SR
    VR --> SR
    EW --> SR
    AW --> SR
    RR --> SR
    SD --> SR

    SR --> SS
    SD --> BR
    SS --> BR
    BR --> BS

    RR --> RRD
    EW --> RRD
    RRD --> RS

    TR --> TS
```

### UI 只应该看什么

- `Program Workspace` 看：
  - `Program`
  - `Workstream`
  - `TestMatrix`
  - `StoryBatch`
  - `PlanningReview`
- `Batch Review Mode` 看：
  - `StoryBatch`
  - `BatchTruth`
  - `StoryTruth`
  - `release gate`
- `Execution / Repair Summary` 看：
  - `TaskTruth`
  - `TurnTruth`
  - `StoryTruth`
  - `RepairTruth`
  - `BlockerRecord`
  - `PlatformIncident`
  - `PreflightProbe`
  - `EvidenceSet`

## 6. 前端首期工作台映射

### 顶层导航建议

```mermaid
flowchart TD
    Root["/programs"]
    List["Program List"]
    Workspace["Program Workspace"]
    Docs["Docs Mode"]
    Batch["Batch Mode"]
    Ops["Ops Mode"]

    Root --> List
    List --> Workspace
    Workspace --> Docs
    Workspace --> Batch
    Workspace --> Ops
```

### 模式与对象对应

| 工作台模式 | 首期主要对象 | 核心动作 |
|---|---|---|
| `Docs Mode` | `Program`、`QuestionRound`、`ContextBrief`、`Workstream`、`TestMatrix` | 只读、审阅、简单手动修订、状态推进 |
| `Batch Mode` | `StoryBatch`、`PlanningReview`、`BatchTruth`、`StoryTruth` | review、blocked-human-confirmation、publish-ready 审核 |
| `Ops Mode` | `WorkerProfile`、`WorkspaceProfile`、`ToolchainProfile`、`CredentialBinding`、`RuntimeEnvProfile`、`PreflightProbe`、`PlatformIncident`、`BlockerRecord`、`RepairRun`、`EvidenceSet` | blocker 查看、repair 跟踪、approval 动作、readiness 审阅 |

### 当前已确认

1. `WorkspaceProfile / ToolchainProfile / CredentialBinding` 作为首期模型冻结对象保留。
2. `PlatformIncident` 作为 repair 平面一等对象保留。
3. 首期前端必须展示 `profile / incident` 只读摘要。

## 7. 进入代码前还需人工确认的点

1. 首期前端是否接受 `Program Workspace -> Docs / Batch / Ops` 三模式结构。
2. `profile / incident` 只读摘要是挂在右侧决策栏，还是以独立 `Ops Mode` 承载。
3. `TaskTruth / StoryTruth / TurnTruth / RepairTruth` 是否采用当前建议的四层拆分，不再合并成一层 task status。

## Recommended Next Step

1. 以上 4 个点做一次人工对齐。
2. 基于这份图，进入前端专题讨论。
3. 对齐后再冻结首页信息架构与 API 对象边界。
