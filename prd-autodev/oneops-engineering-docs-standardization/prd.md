# OneOPS 工程文档标准化 PRD

## 1. 文档信息

| 项目 | 内容 |
|---|---|
| PRD 名称 | OneOPS 工程文档标准化 |
| 目录 | `docs/prd-autodev/oneops-engineering-docs-standardization` |
| 服务 loop | `dev-docs` |
| 状态 | `blocked-human-confirmation` |
| 人工确认人 | `[待人工确认: 项目负责人]` |
| 人工确认日期 | `[待人工确认: 项目负责人]` |
| 关联输入 | `docs/development-doc-templates/**`, `docs/development/**`, 源码目录 |

## 2. 问题陈述

OneOPS 当前已有 `docs/development-doc-templates/**` 标准模板，但仍缺少基于真实代码反向生成、可持续维护的正式开发文档候选稿体系。

同时，工程文档标准化不应与 `poc-ct` 的 PoC 探索测试 PRD 混用。一个 PRD 不应同时承担 PoC 测试与工程文档治理两个目标。

## 3. 目标

- 为工程文档标准化建立独立 PRD/program 目录。
- 建立 `docs/development/**` 文档体系，包括开发流程、文档规范、后端规范、API 规范、测试规范和模板化候选文档。
- 通过 AI 与人工配合，从 `docs/development-doc-templates/01-07` 选择标准化文档结构，再从当前真实代码提取事实，按模板结构补充为候选工程文档，最后由人工确认和修改。
- 工程文档候选内容应聚焦代码规划、业务规划和落地路径，包括真实结构体/模型、真实表、真实字段、真实接口、真实 DTO、真实状态、真实服务流程、真实页面调用、测试切片、风险缺口和实施顺序；不得把大量篇幅浪费在文档流转、版本、合并等议题上。
- 建立人工确认门禁：AI 生成或自动化生成的标准工程文档，未经人工补充/确认不得直接用于开发、测试、story 发布或验收。
- 将 `dev-docs` loop 绑定到本 PRD，而不是绑定到 `poc-ct` 或其 PRD。
- 让后续自动化只能做文档治理、缺口识别、evidence 汇总，不反推需求或设计。
- 约束工程文档正式产物以中文为主，必要英文术语和机器可读字段保留英文。
- 建立面向多业务方向的标准化 story 生成机制：每个方向先声明代码范围、模板范围、输出目录和人工确认门禁，再生成小粒度、可调度、可追溯的 `dev-docs` draft story。
- 提高代码事实提取阶段的源码阅读深度：不能只读少量 router/model 片段，必须围绕方向包系统阅读入口、DTO、model、service 实现、前端调用、页面、状态/错误处理、测试/evidence 和相关文档，形成可追溯的事实依据。

## 4. 非目标

- 不修改产品代码。
- 不确认任何产品需求、架构决策、API 契约、数据库字段、权限模型、fixture、性能目标或验收标准。
- 不发布未经人工确认的执行类 story。
- 不复用 `oneops-poc-concern-autotest` 承载工程文档治理。
- 不把某个方向的代码事实、字段语义、业务规划直接推广为其他方向的标准结论。

## 5. 需求

### 5.1 独立 PRD 目录

工程文档标准化必须使用独立目录：

```text
docs/prd-autodev/oneops-engineering-docs-standardization
```

该目录至少包含：

- `idea.md`
- `context-brief.md`
- `prd.md`
- `program-plan.md`
- `test-matrix.md`
- `story-packages/`
- `evidence/`

### 5.2 文档状态门禁

标准工程文档必须支持以下状态：

- `blocked-human-confirmation`
- `draft`
- `reviewed`
- `active`
- `deprecated`

规则：

- AI 初稿默认是 `blocked-human-confirmation`。
- 存在 `[待人工确认]`、影响关键结论的 `[待补充]` 或未采纳 `[候选方案]` 时，不得进入 `reviewed/active`。
- `blocked-human-confirmation` 文档不能作为开发、测试、story 发布、验收依据。

### 5.3 人工确认占位

文档模板必须包含：

- 状态。
- 人工确认人。
- 人工确认日期。
- 未解决占位数。
- `## 0. 人工确认占位`。

### 5.4 自动化边界

`dev-docs` loop 只能写：

- `docs/development/**`
- `docs/openclaw-autodev/evidence/dev-docs/**`

它不能：

- 修改产品代码。
- 修改 `oneops-poc-concern-autotest` PRD。
- 推断并确认需求/设计/API/数据/权限/测试标准。
- 将文档提升为 `reviewed/active`。

### 5.6 标准结构优先的反向文档生成

当 `dev-docs` 为既有功能生成工程文档时，必须按以下顺序输出：

1. 标准文档结构：从 `docs/development-doc-templates/01-07` 选择目标文档类型、章节顺序、表格结构和人工确认占位。
2. 当前真实代码范围：后端模块、前端模块、脚本、测试和相关 evidence。
3. 当前真实建模：真实 struct/class/type、真实数据库表、真实 JSON 字段、真实 enum/status。
4. 当前真实 API：真实 route、method、handler、前端 request wrapper、关键请求/响应 DTO。
5. 当前真实业务逻辑：服务调用链、状态流转、校验逻辑、持久化行为、外部依赖。
6. 当前真实测试与 evidence：已有测试、脚本、自动化 evidence、缺失验证。
7. 候选文档内容：把真实结构体、字段、接口、流程、状态、测试证据填充到标准化章节中。
8. 基于事实的 AI 推导建议：只允许放在候选文档的建议或缺口章节中，并明确标注为 `AI 推导建议` 或 `规划缺口`。
9. 人工确认占位：所有无法从代码确认的业务含义、字段语义、权限边界、验收口径必须保留 `[待人工确认:<role>]`。

禁止：

- 跳过标准文档结构，直接输出松散事实清单。
- 只用 `rg` 搜到的少量代码片段就生成候选文档。
- 只读取 router/model 而不阅读 service 实现、DTO、前端调用和关键页面。
- 把候选模型写成当前真实模型。
- 把候选 API 写成已实现 API。
- 把候选状态机写成现有 enum。
- 用大段文字讨论文档流转、文档版本、文档合并来替代代码事实整理。

### 5.7.1 代码事实提取深度

代码事实提取阶段必须以“理解当前实现”为目标，而不是只为填表找字段。

每个方向至少应阅读并记录以下范围：

| 范围 | 需要提取的事实 |
|---|---|
| 路由/入口 | route、method、handler、middleware、权限/认证入口 |
| API handler/controller | 请求绑定、响应结构、错误处理、调用的 service 方法 |
| DTO/request/response | 字段、JSON key、校验标签、默认值、分页/过滤/排序参数 |
| model/entity | struct/class、表名、字段、索引标签、关联关系、状态字段 |
| service interface | 对外能力边界、方法命名、入参/出参、调用约束 |
| service implementation | 真实业务流程、状态变化、事务、幂等、重试、外部依赖、错误分支 |
| repository/DAO/GORM 调用 | 查询条件、更新字段、软删/硬删、预加载、聚合逻辑 |
| 前端 API wrapper | method/path、请求参数、响应映射、调用命名 |
| 前端页面/组件 | 页面入口、操作按钮、表单字段、列表字段、弹窗、状态展示 |
| 测试/脚本/evidence | 已验证行为、未覆盖行为、历史结论、可复用样本 |
| 相关文档 | 已有约束、人工确认项、历史规划和当前差异 |

输出候选文档前，必须在候选文档或 evidence 中留下 `代码事实来源清单`，至少包含：

- 已读取的关键文件路径。
- 每类事实对应的源码位置。
- 没读到或无法确认的范围。
- 因源码不足而保留的 `[待人工确认]`。

允许使用 `rg` 定位入口，但不能把 `rg` 输出本身当作完整事实。需要读取入口附近的上下文和调用链，必要时继续追到 service、model、DTO、前端调用和页面。

### 5.7 标准文档逐步生成规则

标准文档应分阶段逐步生成：

- 第一阶段：从 `docs/development-doc-templates/01-07` 选择标准文档目录、文档类型与章节结构。
- 第二阶段：真实代码事实盘点。
- 第三阶段：把真实结构体、字段、接口、状态、流程、测试证据填充到标准结构中，形成候选文档。
- 第四阶段：代码事实与目标业务规划差距分析。
- 第五阶段：面向实现的 story 切片和测试切片。
- 第六阶段：人工确认后再沉淀为正式标准文档。

每一阶段都必须能独立校验，且不得依赖对话记忆。

### 5.8 文档语言规范

工程文档产物必须以中文为主。

允许保留英文的内容：

- 代码标识、文件名、目录名、命令、类名、函数名、字段名。
- API method/path、JSON key、enum、状态值。
- 已成为团队共识的关键概念，例如 `PRD`、`OpenClaw`、`autodev`、`story`、`loop`、`evidence`、`fixture`、`probe`、`read-only`、`blocked-human-confirmation`、`reviewed`、`active`。

不允许：

- 正式工程文档主体以英文段落输出。
- 为了照搬旧材料而输出英文模板主体。
- 将面向人工维护的说明、规则、验收、风险、流程写成英文。

### 5.9 多方向候选文档生成

后续每个业务方向都必须以“方向包”的方式进入自动化，不得直接要求 `dev-docs` 泛化生成所有文档。

方向包至少包含：

| 字段 | 说明 |
|---|---|
| `directionSlug` | 输出目录和 story id 使用的短标识，例如 `device-v2`、`device-v2-ingest` |
| `directionName` | 中文方向名称，例如 `Device V2 入库`、`Device V2 设备管理` |
| `businessScope` | 本方向的业务边界，只描述要反向整理的既有能力 |
| `sourceScopes` | 后端、前端、脚本、已有文档、evidence 的读取范围 |
| `outputDir` | 候选文档输出目录，通常为 `docs/development/<directionSlug>/` |
| `templateRange` | 本轮模板范围，默认 `01-07`，除非用户明确扩展 |
| `excludedTemplates` | 不纳入本轮的模板，例如 `08-11` |
| `targetTaskId` | 默认 `dev-docs` |
| `humanConfirmationRoles` | 产品、后端、前端、测试、安全等待确认角色 |

方向包规则：

- 一个方向包只服务一个业务方向或一个紧密相邻的子方向。
- 同一批 story 不得同时覆盖多个无依赖方向；多方向应拆成多个 batch。
- 每个方向必须先生成 `candidate-01` 到 `candidate-07` 的候选文档，除非用户明确缩小模板范围。
- 生成文件必须保留模板标题、章节结构和 `blocked-human-confirmation` 状态。
- 每个真实字段、接口、表、页面、服务流程应能追溯到代码路径；不能追溯时只能放入 `AI 推导建议` 或 `规划缺口`。

### 5.10 自动化 story 生成规则

工程文档标准化的 story package 应由方向包生成，默认使用 `dependency-chain`：

1. `01-需求概要` + `02-功能清单`。
2. `03-实体属性清单` + `04-原型清单`。
3. `05-数据库设计` + `06-接口文档`。
4. `07-后端开发设计` + 方向 README 更新。

story 生成约束：

- package 默认 `status=draft`，人工确认后才能改为 `reviewed` 并发布。
- story 默认 `status=draft`，发布前再改为 `open`。
- 单个 story 只覆盖一个模板或一组相邻模板。
- `allowedPaths` 只能包含 `docs/development/<directionSlug>/**` 与 `docs/openclaw-autodev/evidence/dev-docs/**`。
- `validation` 必须包含目标文件存在性、关键标题/状态/待确认占位检查，以及 `git diff --check`。
- story 不得要求修改产品代码、migration、生产配置、凭证或其他 PRD。
- story 标题应体现方向和模板范围，不使用 `整体`、`完整`、`全部`、`端到端` 等粗粒度词。

参考生成规则见：

```text
docs/prd-autodev/oneops-engineering-docs-standardization/story-generation-guide.md
```

## 6. 验收标准

- `dev-docs.conf` 的 PRD/coordination 上下文指向本目录。
- `docs/prd-autodev/oneops-poc-concern-autotest` 不再承担工程文档标准化职责。
- `docs/development/documentation-standard.md` 明确 `blocked-human-confirmation` 门禁。
- `docs/development/templates.md` 默认生成不可直接使用的 `blocked-human-confirmation` 文档。
- `dev-docs` evidence 记录人工确认门禁检查结果。
- `docs/development/documentation-standard.md` 明确工程文档产物中文优先。
- `docs/development/templates.md` 的模板主体为中文，英文仅用于必要关键概念和机器可读字段。
- Device V2 等既有功能的工程文档先给出标准化文档结构，再按该结构填充真实代码事实，形成候选文档。
- 候选文档必须明确区分 `当前真实代码事实`、`候选文档内容`、`AI 推导建议`、`规划缺口`。
- 文档中涉及模型、API、状态机、前端调用时，必须能追溯到真实代码路径或明确标注为未实现规划。
- 新方向进入自动化前，必须先形成方向包，并按 `story-generation-guide.md` 拆成小粒度 `dev-docs` story package。
- story package 必须保留 `templateRange`、`excludedTemplates`、`pipeline`、`releaseGate`、`storySizingRule` 等字段，便于人工审核和自动化发布前检查。
- 每份候选文档或对应 evidence 必须包含 `代码事实来源清单`，能证明 AI 已阅读足够代码，而不是只做关键词摘录。

## 7. 风险

| 风险 | 等级 | 处理 |
|---|---|---|
| AI 把未确认推导写成正式需求 | H0 | 必须以人工确认占位阻断 |
| 工程文档 PRD 与 PoC 测试 PRD 混用 | H1 | 独立目录与独立 loop |
| 未确认文档被自动化直接使用 | H1 | 文档状态门禁与 loop EXTRA_RULES |
| 模板里人工占位太多导致难推进 | H2 | 后续由人工分批补充确认 |
