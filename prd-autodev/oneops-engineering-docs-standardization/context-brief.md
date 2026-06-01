# OneOPS 工程文档标准化 Context Brief

## 背景

`docs/development-doc-templates` 已经沉淀出标准工程文档模板，当前工程文档候选稿应直接以这些模板为主结构。

当前问题是：项目缺少基于真实代码反向生成、可由人工确认定稿的正式开发文档体系，不利于长期发展。

## 目标

建立一个独立于 `poc-ct` 的工程文档标准化 PRD，用于指导：

- `docs/development/**` 开发文档体系建设。
- `dev-docs` OpenClaw loop 的任务边界。
- 从 `docs/development-doc-templates/01-07` 选择标准化文档结构，再从当前真实代码提取真实建模、真实 API、真实逻辑、真实状态机、真实前端调用，并按标准结构填充为候选文档。
- 聚焦代码规划、业务规划、实施切片、测试切片和风险缺口；文档状态和流转只作为必要门禁，不作为主要内容。
- 面向更多方向复用时，每个方向先形成方向包，再按固定 story 生成模式拆成小粒度 `dev-docs` draft story。
- 后续文档治理、模板维护、evidence 回写。

## 非目标

- 不承载 PoC concern exploratory testing。
- 不修改 `oneops-poc-concern-autotest` 的 PRD 目标。
- 不反推产品需求、架构决策、数据库模型、API 契约、权限模型、测试通过标准。
- 不替代产品、架构、后端、前端、测试、运维/安全负责人的确认工作。
- 不直接驱动产品代码实现。

## 已确认原则

- AI 可以读取标准模板、整理标准文档结构、分析源码事实、发现缺口、生成候选文档内容。
- AI 生成既有功能文档时，必须先确定标准文档目录与章节结构，再盘点真实代码事实，然后把事实填充进候选文档。
- 代码事实盘点必须有足够源码阅读深度，不能只读少量 router/model 或只摘 `rg` 搜索结果。
- 候选文档或 evidence 必须留下 `代码事实来源清单`，记录已读文件、对应事实、未确认范围和待人工确认项。
- AI 必须明确区分 `当前真实代码事实`、`候选文档内容`、`AI 推导建议`、`规划缺口`。
- AI 不能把候选内容写成正式结论。
- 有人工确认占位的工程文档不可直接使用。
- 标准工程文档默认状态应为 `blocked-human-confirmation`。
- 只有 `reviewed` 或 `active` 文档可以作为开发、测试、story 发布或验收依据。
- 正式工程文档产物应以中文为主；仅保留必要英文关键概念、代码标识、字段名、enum、状态值和文件路径。
- 新方向的候选文档默认只生成 `docs/development-doc-templates/01-07`；`08-11` 只有在用户明确要求时才纳入。
- 新方向自动化 story 必须由方向包驱动，包含方向名、代码范围、输出目录、模板范围、排除模板和人工确认角色。

## 当前实现位置

- 正式开发文档：`docs/development/**`
- 自动化 loop：`docs/openclaw-autodev/loops/dev-docs.conf`
- story queue：`docs/openclaw-autodev/stories/dev-docs.json`
- evidence：`docs/openclaw-autodev/evidence/dev-docs/**`
- story 生成指南：`docs/prd-autodev/oneops-engineering-docs-standardization/story-generation-guide.md`

## 与 poc-ct 的边界

`oneops-poc-concern-autotest` 只服务 OneOPS PoC concern exploration/testing，尤其是 `poc-ct` loop 的探索驱动测试。

工程文档标准化独立服务 `dev-docs` loop，PRD 目录为：

```text
docs/prd-autodev/oneops-engineering-docs-standardization
```
