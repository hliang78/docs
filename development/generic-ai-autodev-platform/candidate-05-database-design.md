---
documentStatus: blocked-human-confirmation
topic: generic-ai-autodev-platform
template: 05-数据库设计模板
createdAt: 2026-05-17
sourceType: planning-mining
---

# 【数据库设计】通用AI自动化平台_规划与控制域_V1.0

## 1. 文档信息

| 项目 | 内容 |
|------|------|
| 系统名称 | 通用 AI 自动化平台 |
| 模块名称 | 规划与控制域 |
| 版本号 | V1.0 |
| 创建日期 | 2026-05-17 |
| 关联文档 | 【需求概要】通用AI自动化平台_V1.0.md |

## 2. 当前真实规划事实

- 当前还处于代码前规划阶段。
- 已冻结高层存储方向：`MySQL + 文件系统`。
- 已明确需要一组 planning/control/runtime 对象。
- `MySQL` 用于结构化元数据与真相层对象，文件系统用于 markdown、json、evidence 等文档型资产。
- `dagengine` 不承担业务对象真相存储，只承接执行引擎内核。

## 3. 候选表设计方向

| 表名 | 用途 | 状态 |
|------|------|------|
| programs | 存储 program 根对象 | 候选 |
| planning_documents | 存储文档元数据与状态 | 候选 |
| workstreams | 存储 workstream 元数据 | 候选 |
| story_batches | 存储 batch 元数据与执行模式 | 候选 |
| runtime_stories | 存储控制面 story | 候选 |
| runtime_task_policies | 存储 lane/task policy | 候选 |
| worker_profiles | 存储 worker 能力画像 | 候选 |
| workspace_profiles | 存储目录与路径权限画像 | 候选 |
| toolchain_profiles | 存储语言/工具链与 helper tool 画像 | 候选 |
| credential_bindings | 存储外部账号/凭据引用 | 候选 |
| runtime_env_profiles | 存储环境组合画像 | 候选 |
| preflight_probes | 存储 turn 前环境探针结果 | 候选 |
| execution_packs | 存储编译后的 execution pack 快照 | 候选 |
| blocker_records | 存储 blocker 分类与处理记录 | 候选 |
| platform_incidents | 存储平台机制性 incident | 候选 |
| repair_runs | 存储 repair 生命周期 | 候选 |
| story_truths / turn_truths / task_truths / repair_truths | 存储真相层对象 | 候选 |

## 4. 候选存储分层

| 存储层 | 承载对象 | 说明 |
|------|------|------|
| `MySQL` | `programs`、`planning_documents`、`story_batches`、`runtime_task_policies`、`worker/runtime/probe/incident/truth` 相关对象 | 存结构化查询与状态管理对象 |
| 文件系统 | markdown、batch json、evidence、screenshots | 保留现有文档与证据资产形态 |
| `dagengine` runtime persistence | process/task/ticket/execution | 只承接执行内核数据，不作为规划与控制真相层 |

## 5. AI 推导建议

- planning 数据与 runtime 执行数据应逻辑分层，不建议混成一套大表。[待人工确认: 架构负责人]
- `dagengine` 原有 persistence 更适合承接 execution/process 数据，不直接承接 planning 文档元数据。[待人工确认: 后端负责人]
- `WorkspaceProfile / ToolchainProfile / CredentialBinding` 独立入表方向已确认。
- `PlatformIncident` 作为 repair 平面一等对象入表方向已确认。
- `CredentialBinding` 建议只保存 secret reference 与 scope，不保存明文 credential。[待人工确认: 架构负责人]

## 6. 规划缺口

- `MySQL` 边界已确认采用“同实例独立数据库”。
- 数据库命名已确认采用 `oneops_ai_autodev`。
- 是否将 planning 文档正文也结构化持久化，尚未决定。
- truth 表是否采用统一 event log + projection，还是多张直接状态表，仍待确认。

## 7. 代码事实来源清单

- `docs/prd-autodev/generic-ai-autodev-platform/dagengine-kernel-mapping.md`
- `docs/prd-autodev/generic-ai-autodev-platform/prd-planning-plane-mapping.md`
- `docs/prd-autodev/generic-ai-autodev-platform/openclaw-control-plane-mapping.md`
- `docs/prd-autodev/generic-ai-autodev-platform/technical-selection.md`
- `docs/prd-autodev/generic-ai-autodev-platform/object-storage-file-boundary.md`
- `docs/prd-autodev/generic-ai-autodev-platform/runtime-governance-and-super-repair.md`
