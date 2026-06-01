---
topic: generic-ai-autodev-platform
kind: full-stack
title: 对象存储与文件边界设计稿
createdAt: 2026-05-17T14:05:00+0800
program: true
status: draft
---

# Object Storage And File Boundary

## Purpose

- 这份文档回答一个底层问题：
  - 自动驾驶系统的核心对象到底放哪里
  - 哪些文件只是导出物
  - 哪些状态绝不能再从文件反推
- 目标是根治旧体系的“文件分布式真相”问题，而不是继续在其上补丁。

## Design Decision

- 核心业务对象真相层：`MySQL`
- 大体积证据与导出物层：`filesystem`
- 运行时临时缓存层：`filesystem temporary cache`
- 前端与控制器读取入口：`self-built planner/control API`
- `dagengine` 定位：执行引擎内核，不承担核心业务对象真相存储

一句话原则：

- `对象在库里，文件在盘上，决策走对象，文件只做证据和导出。`

## Why This Must Change

旧体系的根本问题不是“文件太多”，而是文件同时承担了 4 种互相冲突的角色：

1. 真相存储
2. 协作接口
3. 中间缓存
4. 导出证据

结果就是：

- 旧 `current-story` 污染新一轮 story 选择
- 旧 `handoff` 牵引 worker 继续执行过期上下文
- `last-report`、`state.json`、`progress.json`、`story.json` 互相覆盖
- 人工、脚本、worker 都围绕文件做决定

所以自动驾驶系统必须先把“对象真相”和“文件导出”硬拆开。

## Storage Layers

## Layer 1 - Authoritative Object Store

- 介质：`MySQL`
- 角色：唯一真相层
- 特征：
  - 有主键
  - 有版本号/更新时间
  - 有明确状态字段
  - 支持结构化查询
  - 支持事务

以下对象必须放在这一层：

- `Program`
- `QuestionRound`
- `ContextBrief`
- `Workstream`
- `TestMatrix`
- `StoryBatch`
- `PlanningReview`
- `RuntimeTaskPolicy`
- `RuntimeStory`
- `ExecutionPack`
- `WorkerProfile`
- `WorkspaceProfile`
- `ToolchainProfile`
- `CredentialBinding`
- `RuntimeEnvProfile`
- `PreflightProbe`
- `ApprovalProfile`
- `BlockerRecord`
- `PlatformIncident`
- `RepairRun`
- `StoryTruth`
- `BatchTruth`
- `TurnTruth`
- `TaskTruth`
- `RepairTruth`

## Layer 2 - Evidence And Artifact Store

- 介质：`filesystem`
- 角色：
  - 证据
  - 导出
  - 审计留痕
  - 可读文档

以下内容应放在这一层：

- markdown 证据文档
- 截图
- 浏览器录屏
- 原始日志摘要
- diff 导出
- 验证命令输出快照
- PRD/标准文档导出稿
- batch 导出 JSON

要求：

- 文件必须带来源对象 id
- 文件必须带生成时间
- 文件必须能从对象层重新索引出来
- 文件删除或丢失，不应改变对象 truth

## Layer 3 - Runtime Cache

- 介质：`filesystem` 或进程内缓存
- 角色：
  - 临时优化
  - 中间加速
  - debug

以下内容可以放在这一层：

- prompt render cache
- code context cache
- provider 原始响应缓存
- session trace
- 临时编译产物

要求：

- 缓存失效后，系统应仍可从真相层恢复
- 缓存绝不能参与最终业务决策

## Layer 4 - Export Projection

- 介质：`filesystem`
- 角色：
  - 人读友好导出
  - 兼容旧流程
  - 对外共享

典型导出物：

- `story-packages/*.json`
- `candidate-01~07.md`
- readiness 报告
- 批次摘要
- 证据索引页

要求：

- export 由对象层生成
- export 不允许反向写回 truth

## Object Classes

## A. 必须是数据库对象

这些对象不能再只是文件：

- `Program`
- `StoryBatch`
- `RuntimeStory`
- `ExecutionPack`
- `BlockerRecord`
- `PlatformIncident`
- `RepairRun`
- `WorkerProfile`
- `WorkspaceProfile`
- `ToolchainProfile`
- `CredentialBinding`
- `RuntimeEnvProfile`
- `Truth` 系列对象

原因：

- 它们会被多角色读写
- 它们需要状态转换
- 它们需要版本治理
- 它们不能容忍“旧文件被继续读”

## B. 可以是文件导出物

- `questions.md`
- `context-brief.md`
- `prd.md`
- `review.md`
- `evidence/*.md`
- `StoryBatch export json`

前提：

- 它们背后仍然有对应的对象来源
- 前端和脚本不直接拿这些文件当真相

## C. 只能是缓存或 trace

- `current-story`
- `current-prompt`
- `current-execution-pack`
- `raw provider response`
- `session transcript trace`
- `local debug snapshot`

要求：

- 这些名字即使保留，也只能是 cache
- 任何业务判断都不能直接依赖它们

## What Must Never Be Repeated

以下旧模式必须彻底禁止：

1. 从 `current-story.json` 推断“当前应该执行哪个 story”
2. 从 `last-report.txt` 推断最终状态
3. 从 handoff 文件推断“本轮真正任务是什么”
4. 从多个文件拼出 monitor/status/detail
5. 人工直接改状态文件来修复任务
6. worker 只写文件，不写结构化对象结果

## Read Model

前端和控制器必须统一通过 API 读对象，而不是读文件。

## Planner API Read Model

- 读：
  - `Program`
  - `QuestionRound`
  - `ContextBrief`
  - `Workstream`
  - `TestMatrix`
  - `StoryBatch`
  - `PlanningReview`
  - 执行结果摘要
  - `EvidenceSet` 索引

## Control API Read Model

- 读：
  - `RuntimeTaskPolicy`
- `RuntimeStory`
- `WorkerProfile`
- `RuntimeEnvProfile`
- `WorkspaceProfile`
- `ToolchainProfile`
- `CredentialBinding`
- `PreflightProbe`
- `ApprovalProfile`
- `BlockerRecord`
- `PlatformIncident`
- `RepairRun`
- `Truth` 对象

## Frontend Read Model

- `Docs Mode`
  - 读 planning 对象
- `Batch Mode`
  - 读 batch 与 story truth
- `Ops Mode`
  - 读 blocker、repair、truth、evidence index

前端不应直接读：

- `docs/**/*.md` 作为唯一状态来源
- `state/*.json`
- `progress/*.json`
- `current-story/current-prompt/current-execution-pack`

## Write Model

## Planning Writes

- 由 `Planner API` 写入 MySQL 对象
- 文件导出由后台统一生成

## Execution Writes

- `Controller` 写：
  - `RuntimeStory`
  - `ExecutionPack`
  - `BlockerRecord`
  - `Truth` 事件
- `Worker` 回传：
  - report
  - evidence metadata
  - blocker facts
- `Reducer` 写：
  - `StoryTruth`
  - `TurnTruth`
  - `TaskTruth`

## Repair Writes

- `Repair` 写：
  - `RepairRun`
  - repair evidence metadata
  - repair result event

## File Writes

- 只允许由统一 export/evidence service 落盘
- 不允许由多个脚本各自自由落“真相文件”

## Recommended MySQL Tables

这不是最终表设计，只是冻结方向。

### Planning Tables

- `programs`
- `question_rounds`
- `context_briefs`
- `workstreams`
- `test_matrices`
- `story_batches`
- `planning_reviews`

### Control Tables

- `runtime_task_policies`
- `runtime_stories`
- `execution_packs`
- `worker_profiles`
- `workspace_profiles`
- `toolchain_profiles`
- `credential_bindings`
- `runtime_env_profiles`
- `preflight_probes`
- `approval_profiles`
- `turn_handoffs`
- `blocker_records`
- `platform_incidents`
- `repair_runs`

### Truth Tables

- `story_truths`
- `batch_truths`
- `turn_truths`
- `task_truths`
- `repair_truths`

### Artifact Index Tables

- `evidence_sets`
- `artifact_exports`

## Filesystem Directory Role

建议把文件系统语义强制收紧成下面几类：

### `/artifacts/evidence/...`

- 只存证据正文与二进制证据

### `/artifacts/exports/...`

- 只存 markdown/json/html 导出物

### `/runtime-cache/...`

- 只存 cache、trace、临时产物

### `/legacy-import/...`

- 只存从旧 `openclaw-autodev / prd-autodev` 导入的历史材料

## Migration Rule

对旧体系的迁移，不应是“继续读旧文件”，而应是：

1. 先把旧文件分类：
   - planning 文档
   - story/batch 导出
   - evidence
   - runtime cache
   - dirty truth-like files
2. 再把应进对象层的内容导入 MySQL
3. 保留原文件为 legacy evidence，不再继续作为真相

## Frontend Impact

这个边界会直接影响前端设计：

- 前端列表页应查询对象表，而不是扫描目录
- 前端状态标签应来自 truth API，而不是文件投影
- 前端详情页可展示证据文件，但证据文件只是附件，不是状态来源

## Immediate Decisions To Confirm

1. 首期是否接受“核心对象全部进 MySQL，文件只做 evidence/export/cache”的边界。
2. 首期是否允许继续保留旧 `story-packages/*.json` 作为 export，而不是 authoritative store。
3. 是否接受前端完全不直接依赖现有分散状态文件。
4. `dagengine` 是否只承载执行内核与状态流转，不承载业务对象存储。
5. secrets 是否接受只以 `CredentialBinding` 引用方式进入对象层，而不是直接写进 story 或 markdown 文档。

## Recommended Next Step

1. 以上 4 个点做人工确认。
2. 确认后，再讨论前端信息架构和 API 分层。
3. 在进入代码阶段前，把“对象表设计草案”补出来。
