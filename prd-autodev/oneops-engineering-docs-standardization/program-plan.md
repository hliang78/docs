# OneOPS 工程文档标准化 Program Plan

## Program Goal

建立独立的工程文档标准化 PRD/program，使 `dev-docs` loop 与 `docs/development/**` 文档体系有清晰、独立、可追踪的需求来源和自动化边界。

## Workstreams

| Workstream | 目标 | 输出 |
|---|---|---|
| WS-DOC-01 文档体系骨架 | 建立正式开发文档入口与核心规范 | `docs/development/README.md`, `documentation-standard.md` |
| WS-DOC-02 人工确认门禁 | 确保 AI 初稿不可直接使用 | `blocked-human-confirmation`, templates, usage gates |
| WS-DOC-03 自动化边界 | 让 `dev-docs` 独立于 `poc-ct` | `dev-docs.conf`, `dev-docs.json`, evidence |
| WS-DOC-04 模板结构治理 | 将 `docs/development-doc-templates` 作为候选标准文档主结构 | `docs/development-doc-templates/01-07` |
| WS-DOC-05 中文工程文档 | 确保正式工程文档产物中文优先 | 语言规范、中文模板、自动化约束 |
| WS-DOC-06 标准结构反推文档 | 从 `docs/development-doc-templates/01-07` 选择标准文档结构，再用真实代码事实填充候选文档 | 标准目录/章节结构、真实模型/API/状态/流程填充、候选文档、人工确认清单 |
| WS-DOC-07 多方向 story 生成 | 让未来每个业务方向都能按统一方向包生成小粒度自动化 story | 方向包约束、story 拆分规则、batch 模板、validation 模式 |

## Sequencing

1. 建立独立 PRD 目录。
2. 将 `dev-docs` loop 的 CHARTER/COORDINATION/CONTEXT 指向本目录。
3. 保留 `docs/development/**` 作为工程文档正式输出。
4. 运行自动化检查人工确认门禁。
5. 检查工程文档产物是否中文优先。
6. 针对既有功能按“选择 `docs/development-doc-templates/01-07` 标准结构 -> 深度阅读源码提取真实事实 -> 标准结构填充候选文档 -> 差距分析 -> story 切片 -> 人工确认”逐步生成文档。
7. 对每个新方向先补充方向包，再按 `story-generation-guide.md` 生成 draft story package。
8. 后续由人工补充各类 `[待人工确认]` 占位，再考虑升级文档状态。

## Reverse Documentation Rule

`dev-docs` 生成既有功能文档时，必须从 `docs/development-doc-templates/01-07` 选择标准文档结构：

- 标准文档目录。
- 文档类型和命名。
- 章节顺序。
- 必填表格。
- 人工确认占位。
- 适用于当前模块的候选文档清单。

结构确定后，再读取当前代码并输出可填充事实：

- 真实模型/表/字段。
- 真实 API route/method/handler。
- 真实 DTO/request/response。
- 真实状态值和状态流转。
- 真实前端 API wrapper 与页面入口。
- 真实服务调用链和测试/evidence。
- 关键 service implementation、错误分支、状态变化、事务/幂等/重试、查询/更新语义。

随后把这些事实填入标准结构，形成候选文档。无法从代码确认的内容保留 `[待人工确认:<role>]`，未来规划必须明确标注为 `AI 推导建议` 或 `规划缺口`，不得混入真实事实段落。

## Code Reading Depth Rule

事实提取阶段必须体现足够的代码理解深度。自动化 worker 可以用 `rg` 定位入口，但必须继续阅读上下文和调用链。

每个方向至少覆盖：

- 后端 route/router。
- API handler/controller。
- request/response DTO。
- model/entity 和 TableName/字段标签。
- service interface。
- service implementation。
- repository/DAO/GORM 查询与更新。
- 前端 API wrapper。
- 前端页面或组件入口。
- 已有测试、脚本或 evidence。
- 相关工程文档和 PRD 上下文。

每批候选文档必须产出或更新 `代码事实来源清单`，说明已读关键文件、对应事实、未确认范围和人工待确认项。没有来源清单的候选文档不得进入人工定稿流程。

## Direction Package Contract

未来每个方向进入 `dev-docs` 前，必须先有一个最小方向包。方向包不是正式需求，不确认业务结论，只用于限制自动化读取、输出和 story 切片。

方向包字段：

| 字段 | 必填 | 用途 |
|---|---|---|
| `directionSlug` | 是 | 生成输出目录、文件名、story id 前缀 |
| `directionName` | 是 | 生成人可读标题 |
| `businessScope` | 是 | 限制要反向整理的既有业务能力 |
| `sourceScopes` | 是 | 限制源码、前端、脚本、已有文档、evidence 读取范围 |
| `outputDir` | 是 | 限制写入目录 |
| `templateRange` | 是 | 默认 `01-07` |
| `excludedTemplates` | 是 | 默认 `08-11` |
| `targetTaskId` | 是 | 默认 `dev-docs` |
| `humanConfirmationRoles` | 是 | 生成待确认占位 |

## Story Generation Pattern

每个方向默认生成 4 个 story，按 `dependency-chain` 排序：

| Story | 模板范围 | 主要输出 | 粒度边界 |
|---|---|---|---|
| A | 01-02 | 需求概要、功能清单 | 只整理业务目标、角色、功能项、非目标和待确认 |
| B | 03-04 | 实体属性、原型清单 | 只整理模型/DTO/字段、页面/组件/入口 |
| C | 05-06 | 数据库设计、接口文档 | 只整理真实表、字段、索引、API、DTO、前端 wrapper |
| D | 07 | 后端开发设计、方向 README | 只整理真实后端分层、调用链、实现缺口 |

如果某个方向规模过大，应继续拆分为子方向，例如 `device-v2-ingest` 与 `device-v2-management`，不要把多个不相邻业务能力塞进一个 story。

每个 story 的 scope 都必须包含“阅读足够源码并记录代码事实来源清单”的要求。只生成文档、不记录事实来源的 story 不可发布。

## Reusable Batch Requirements

story package 必须包含：

- `program`
- `batch`
- `title`
- `status=draft`
- `executionMode=dependency-chain`
- `targetTaskIds=["dev-docs"]`
- `direction`
- `templateRange`
- `excludedTemplates`
- `releaseGate`
- `storySizingRule`
- `pipeline`
- `stories`

每个 story 必须包含：

- `id`
- `status=draft`
- `dependsOn`，首个 story 可为空
- `lanes=["dev-docs"]`
- `title`
- `scope`
- `nonGoals`
- `allowedPaths`
- `acceptance`
- `validation`

具体样例见 `story-generation-guide.md`。

## Boundary

本 program 不服务 `poc-ct`。`poc-ct` 继续由：

```text
docs/prd-autodev/oneops-poc-concern-autotest
```

驱动。

本 program 服务：

```text
docs/openclaw-autodev/loops/dev-docs.conf
docs/development/**
```

## Current Automation Status

- `DEV-DOCS-001` 已完成，验证了人工确认门禁。
- `batch-002-device-v2-engineering-docs` 已被当前规则取代，不再作为后续发布入口。
- `batch-003-device-v2-code-fact-standard-docs` 已作为 draft 样板，按 `01-07` 模板、方向包、深度源码事实提取和候选文档拆成小 story，并明确排除 `08-11`。
- 后续 story 必须先在 `story-packages/` 中 draft，人工确认后才能发布。
