# OneOPS 开发文档总览

本文档集用于把项目周期内散落在 `docs/prompts`、PRD、自动化任务、测试证据和代码实现中的经验，沉淀为长期可维护的正式开发文档。

`docs/prompts` 可以继续保留为历史提示词资产，但正式开发活动应优先引用本目录下的规范和模板。

## 文档目标

- 为需求、设计、开发、接口、测试、代码审核提供统一文档入口。
- 让新成员可以从文档理解模块边界、接口契约、数据模型、测试策略和自动化运行方式。
- 让 AI/autodev worker 读取稳定文档，而不是依赖一次性 prompt 或对话上下文。
- 约束 AI/autodev worker 只能整理、提炼、标注假设和占位，不得代替人类确认需求、设计、业务规则和验收口径。
- 约束正式工程文档产物以中文为主，英文只保留必要技术概念、代码标识和机器可读字段。
- 让长期演进可追踪：每次需求变更、接口变更、测试补充都能回写到对应文档。

## 文档分层

| 层级 | 目录/文件 | 主要读者 | 作用 |
|---|---|---|---|
| 开发过程 | `development-process.md` | 产品、研发、测试、AI worker | 说明从需求到测试闭环的标准流转 |
| 文档规范 | `documentation-standard.md` | 文档维护者、AI worker | 说明文档类型、命名、模板和更新规则 |
| 后端规范 | `backend-development-standard.md` | 后端研发、代码生成 worker | 说明模块结构、Service/Repository/API/校验规范 |
| API 规范 | `api-documentation-standard.md` | 前后端、测试 | 说明接口文档与接口实现的契约 |
| 测试规范 | `testing-standard.md` | 测试、研发、自动化 worker | 说明测试用例、pytest、探索测试和证据格式 |
| 文档模板 | `templates.md` | 所有人 | 提供需求、设计、数据库、API、测试、evidence 模板 |
| Prompt 资产分析 | `prompt-assets-analysis.md` | 项目维护者 | 说明 `docs/prompts` 中哪些内容已沉淀、哪些需适配 |

## 推荐阅读顺序

1. `development-process.md`
2. `documentation-standard.md`
3. 按角色阅读：
   - 后端研发：`backend-development-standard.md`
   - 前后端联调：`api-documentation-standard.md`
   - 测试/自动化：`testing-standard.md`
4. 需要追溯历史提示词来源时，阅读 `prompt-assets-analysis.md`

## 正式文档与 prompts 的关系

`docs/prompts` 中的文件反映了项目早期对文档、代码生成、测试生成的探索，价值很高，但它们有几个问题：

- 部分内容绑定 Java/Spring Boot/Nebula，不一定适用于当前所有 OneOPS 子项目。
- 部分内容是“让 AI 一次性生成”的提示词，不是团队可持续维护的规范。
- 部分文档模板之间存在重复或口径差异，例如接口响应结构、测试状态码、输出目录。
- 缺少和当前 autodev/探索驱动测试体系的衔接。

因此，本目录采用“提炼原则、保留关键概念、适配当前项目”的方式，把 prompts 转化为正式开发文档。

## 维护规则

- 新增模块时，至少补齐需求/设计/API/测试中的必要文档。
- 修改接口、数据结构、测试策略时，必须同步更新相关文档。
- 自动化 worker 产出的 evidence 如果形成稳定结论，应回写到正式文档。
- 不确定内容使用 `[待人工确认: <角色>]`、`[待补充]` 或 `[候选方案]` 标记，不要伪装成已确认事实。
- 任何应由产品、架构、业务负责人、运维负责人或测试负责人确认的内容，AI 只能放置 `[待人工确认]`、`[待补充]`、`[候选方案]` 占位，并说明需要谁确认。
- 由 AI 生成且仍缺少人工补充/确认的标准工程文档，状态必须是 `blocked-human-confirmation`，不可直接用于开发、测试、story 发布或验收。
- 过时内容应标记 `[已废弃]`，并给出替代文档链接；不要直接静默删除。
