# docs/prompts 资产分析

本文档分析 `docs/prompts` 中的历史提示词资产，并说明哪些内容已经被沉淀到正式开发文档中，哪些内容需要后续适配。

## 总体判断

`docs/prompts` 不是简单的废弃材料。它反映了项目周期内对“需求 -> 原型 -> 设计 -> 开发 -> 测试”的完整思考，尤其适合作为正式文档体系的原始素材。

但这些文件不应继续作为唯一开发规范，原因是：

- 它们主要是 prompt，不是团队维护型文档。
- 部分内容绑定 Java/Spring Boot 2.6.9/Nebula。
- 当前 OneOPS 是多子项目仓库，包含 Go、Vue、Agent、Telegraf 等不同技术栈。
- 多份 prompt 中的目录、响应结构、状态码、输出位置存在口径不统一。
- 它们没有和当前 OpenClaw/autodev/evidence 体系完全衔接。

## 文件清单与价值归类

| 文件 | 阶段 | 可沉淀价值 | 适配状态 |
|---|---|---|---|
| `需求阶段-软件系统需求概要设计文档输出提示词.md` | 需求 | 需求概要章节、用户角色、功能/非功能、用户故事 | 已沉淀到 `development-process.md` |
| `需求阶段-功能描述清单生成提示词.md` | 需求 | 功能清单拆分 | 待后续补模板 |
| `需求阶段-实体原型清单生成提示词.md` | 需求/数据 | 实体识别、原型字段来源 | 待后续补模板 |
| `需求阶段-软件系统需求原型拆分工作提示词.md` | 原型 | 子系统、模块、页面清单、导航关系 | 已沉淀到 `development-process.md` |
| `需求阶段-软件系统需求原型页面生成工作提示词.md` | 原型 | 页面生成与交互描述 | 待与前端设计规范融合 |
| `开发准备阶段-基于nebula的spring-boot.2.6.9的工程创建提示词.md` | 脚手架 | Java/Nebula 技术栈与工程结构 | 已沉淀为 Java 参考，不作为全局强约束 |
| `开发准备阶段-标准业务模块脚手架创建所使用的提示词.md` | 脚手架 | sdk/local/local.starter 三段式模块 | 已沉淀到 `backend-development-standard.md` |
| `开发准备阶段-标准工具模块脚手架创建所使用的提示词.md` | 脚手架 | 工具模块结构 | 待补充工具模块规范 |
| `开发阶段-数据库设计与实现-业务模块数据库设计文档生成提示词.md` | 数据库 | 表结构、ER、索引、数据字典、扩展性 | 已沉淀到 `development-process.md` |
| `开发阶段-生成HTTP RESTFul接口清单和接口说明文档提示词.md` | API | Controller/API 文档结构、响应示例 | 已沉淀到 `api-documentation-standard.md` |
| `开发阶段-调用接口实现-Controller层对应接口和swagger生成的提示词.md` | API/实现 | Controller 生成规则、Swagger | 已沉淀为 Java 参考 |
| `开发阶段-逻辑代码实现-服务层及数据层代码生成提示词.md` | 实现 | Service/Repository/Mapper/Po 规则、Validate、NebulaToolkitService | 已沉淀到 `backend-development-standard.md` |
| `开发阶段-Service层代码审核、注释完善工作提示词.md` | 审核 | 命名、事务、异常、并发、缓存审核 | 已沉淀到 `development-process.md` 和后端规范 |
| `测试阶段-调用接口文档和测试用例文档生成.md` | 测试 | 测试用例、接口调用文档、性能测试 | 已沉淀到 `testing-standard.md` |
| `测试阶段-pytest测试脚本生成.md` | 测试自动化 | pytest 结构、ResponseValidator、业务成功判断 | 已沉淀到 `testing-standard.md` |

## 已形成的正式文档

| 正式文档 | 来源 |
|---|---|
| `README.md` | prompts 总体生命周期与当前文档缺口 |
| `development-process.md` | 需求、原型、数据库、API、测试、审核 prompts |
| `documentation-standard.md` | prompts 输出目录与文档命名规则的统一化 |
| `backend-development-standard.md` | Java/Nebula 脚手架、Service/Repository、代码审核 prompts |
| `api-documentation-standard.md` | API/Controller/接口文档 prompts |
| `testing-standard.md` | 测试用例、pytest、探索驱动测试 evidence |
| `templates.md` | 需求、概要设计、数据库、API、测试、探索 evidence 的可复制模板 |

## 关键沉淀结论

1. 项目需要的是“文档闭环”，不是更多一次性 prompt。
2. 需求文档要能推导原型、实体、API、测试。
3. API 文档必须表达业务成功判断，不能只写 HTTP 200。
4. 测试必须留下 evidence，并记录环境、fixture、输入、输出和 next decision。
5. Java/Nebula 规范有价值，但只能作为对应模块参考。
6. 复杂项目应采用探索驱动测试，先找 flow line 与 weak points，再执行 probe。
7. H0/H1 风险必须优先处理，否则 gate 结果不可信。
8. AI 只能从 prompts 中提炼候选规范和占位，不能把历史 prompt 内容反推成已确认需求或设计。

## 仍需补齐的文档

下一批建议补齐：

- `docs/development/frontend-development-standard.md`
- `docs/development/database-design-standard.md`
- `docs/development/code-review-standard.md`
- 将 `templates.md` 中的模板按需拆分为独立 `docs/development/templates/*.md`

## 对后续 autodev 的建议

后续自动化不应直接读取某个 prompt 就开始开发，而应采用：

```text
prompt assets
  -> formal development docs
  -> blocked-human-confirmation
  -> human completion and confirmation
  -> PRD/program plan
  -> reviewed story batch
  -> OpenClaw execution
  -> evidence
  -> formal docs update
```

如果某个 prompt 中的规则与正式文档冲突，以正式文档为准；如果正式文档缺失，则将 prompt 内容提炼为文档后再用于执行。
