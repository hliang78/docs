# Device V2 工程文档入口

| 项目 | 内容 |
| --- | --- |
| 文档状态 | `blocked-human-confirmation` |
| 人工确认人 | `[待人工确认: 项目负责人]` |
| 人工确认日期 | `[待人工确认: 项目负责人]` |
| 未解决占位数 | 见“待人工确认清单” |
| 适用范围 | Device V2 入库、Device V2 设备管理两个工程文档方向 |

> 本目录是 Device V2 工程文档的中文结构索引。当前目标不是输出松散事实清单，而是先确定标准文档结构，再把源码中提取到的真实结构体、字段、接口、流程和测试证据填充为候选文档；在状态仍为 `blocked-human-confirmation` 时，**不可直接**作为开发、测试、story 发布或验收依据。

## 0. 人工确认占位

- 状态确认：`blocked-human-confirmation`，不得自动提升为 `reviewed` 或 `active`。
- 业务负责人：`[待人工确认: 产品负责人]`
- 技术负责人：`[待人工确认: 技术负责人]`
- 测试/验收负责人：`[待人工确认: 测试负责人]`
- 文档维护负责人：`[待人工确认: 项目负责人]`

## 1. 文档边界

本入口只建立 Device V2 工程文档结构，不确认任何未定内容：

- 不确认产品需求、业务规则、页面交互、权限模型或验收口径。
- 不确认 API path、DTO、数据库字段、fixture、性能目标、采集协议或删除策略。
- 不把 D2 launch evidence 中的阶段性结果提升为长期工程规范。
- 不修改产品代码、既有 D2 PRD、生产配置、凭证、migration 或外部集成。

## 2. 标准候选文档生成路径

后续自动化应按以下顺序逐步生成文档：

1. 使用 `docs/development-doc-templates/01-需求概要模板.md` 到 `07-后端开发设计模板.md` 作为本轮标准结构来源。
2. 从当前源码提取真实结构体、字段、表、API、DTO、状态、前端调用、服务流程和测试证据。
3. 按 01-07 模板结构填充候选文档，供人工确认、修改后定稿。
4. 本轮不生成 `08-测试用例模板.md` 到 `11-Service代码审查报告模板.md` 对应文档。

所有候选文档必须区分 `标准文档结构`、`当前真实代码事实`、`候选文档内容`、`AI 推导建议`、`规划缺口`。

## 2.1 本轮候选标准文档

| 模板编号 | 候选文档 | 当前状态 | 说明 |
| --- | --- | --- | --- |
| 01 | [`candidate-01-requirements-summary.md`](./candidate-01-requirements-summary.md) | `blocked-human-confirmation` | 需求概要候选稿，基于真实代码反推业务背景、目标、角色、功能和边界。 |
| 02 | [`candidate-02-function-list.md`](./candidate-02-function-list.md) | `blocked-human-confirmation` | 功能清单候选稿，基于真实接口、页面和服务能力拆分功能项。 |
| 03 | [`candidate-03-entity-attribute-list.md`](./candidate-03-entity-attribute-list.md) | `blocked-human-confirmation` | 实体属性清单候选稿，基于真实 Go model/DTO 提取实体和字段。 |
| 04 | [`candidate-04-prototype-list.md`](./candidate-04-prototype-list.md) | `blocked-human-confirmation` | 原型清单候选稿，基于真实前端路由、页面和组件提取页面结构。 |
| 05 | [`candidate-05-database-design.md`](./candidate-05-database-design.md) | `blocked-human-confirmation` | 数据库设计候选稿，基于真实 GORM model 和 TableName 提取表结构。 |
| 06 | [`candidate-06-api-documentation.md`](./candidate-06-api-documentation.md) | `blocked-human-confirmation` | 接口文档候选稿，基于真实 router/handler/DTO/前端 wrapper 提取 API。 |
| 07 | [`candidate-07-backend-development-design.md`](./candidate-07-backend-development-design.md) | `blocked-human-confirmation` | 后端开发设计候选稿，按模板结构映射当前 Go/Gin/GORM 分层。 |

## 3. 方向一：Device V2 入库

建议后续拆分为以下文档；每份文档生成时仍必须保持 `blocked-human-confirmation`，直到人工逐项确认：

| 候选文档 | 当前状态 | 说明 |
| --- | --- | --- |
| [`ingest.md`](./ingest.md) | `blocked-human-confirmation` | 入库方向工程文档初稿，汇总来源材料、已记录 evidence 事实、不可反推项和人工确认清单；不可直接作为开发或验收依据。 |
| [`mainline-store-pipeline-refactor.md`](./mainline-store-pipeline-refactor.md) | `active-design-draft` | Device V2 主线采集入库改造设计，定义 prepare/store/manage、sync-to-v1、monitor push 的端到端主线语义。 |
| [`zb-store-v2-integration.md`](./zb-store-v2-integration.md) | `active-design-draft` | ZB 入库接入 Device V2 主线设计，记录已确认决策、字段校验、凭据策略、异步编排和回调语义。 |
| [`candidate-06-api-documentation.md`](./candidate-06-api-documentation.md) | `blocked-human-confirmation` | 按标准 API 文档结构填充 Device V2 真实接口、DTO、前端 wrapper 和待确认项；不可直接作为联调、测试或验收依据。 |
| [`ai-derived-confirmation-proposal.md`](./ai-derived-confirmation-proposal.md) | `code-fact-and-planning-draft` | 上一轮源码事实与规划推导材料，只能作为后续 `source-fact-inventory.md` 的输入之一，不是最终标准文档结构。 |
| `ingest-source-materials.md` | `[候选方案: AI 提炼]` | 后续可拆分：汇总 DB-derived sample、Excel/import、batch、handoff、field reconciliation 等来源材料，不沉淀为业务规则。 |
| `ingest-human-gates.md` | `[待人工确认: 产品负责人]` | 后续可拆分：入库前置数据、跳过/失败处理、批次保留、错误提示、导入范围等确认项。 |
| `ingest-evidence-map.md` | `[候选方案: AI 提炼]` | 后续可拆分：映射 launch evidence 中已证明、未运行、blocked、accepted risk 的条目。 |

当前可安全记录的事实仅限文档状态与证据索引：2 个 approved imported `D2LA_*` clones 有入库/应用/管理交接/字段核对证据；完整 5 设备样本仍存在 3 个候选缺少权威 enrichment 的 blocker。该事实不可直接扩展成上线验收标准。

## 4. 方向二：Device V2 设备管理

建议后续拆分为以下文档；每份文档生成时仍必须保持 `blocked-human-confirmation`，直到人工逐项确认：

| 候选文档 | 当前状态 | 说明 |
| --- | --- | --- |
| [`management.md`](./management.md) | `blocked-human-confirmation` | 设备管理方向工程文档初稿，汇总清册、详情、编辑、删除或保留、采集证据和人工确认清单；不可直接作为开发或验收依据。 |
| [`candidate-06-api-documentation.md`](./candidate-06-api-documentation.md) | `blocked-human-confirmation` | 按标准 API 文档结构填充 Device V2 真实接口、DTO、前端 wrapper 和待确认项；不可直接作为联调、测试或验收依据。 |
| `management-source-materials.md` | `[候选方案: AI 提炼]` | 后续可拆分：汇总 management list/handoff、field reconciliation、store readiness/start、task summary、runs、observations、latest DC2 等来源材料。 |
| `management-human-gates.md` | `[待人工确认: 产品负责人]` | 管理列表、编辑、删除、清理、权限、采集/重试、监控等需要人工确认的门禁。 |
| `management-evidence-map.md` | `[候选方案: AI 提炼]` | 映射设备管理方向已证明切片与未运行/blocked 项。 |

当前可安全记录的事实仅限文档状态与证据索引：2 个 approved clones 有管理交接、store start、observations、latest DC2 等证据；UI edit/update、clone delete cleanup、5-device parallel collection 和非 admin 权限姿态仍未完成或 blocked。该事实不可直接扩展成权限、删除、采集或验收规则。

## 5. 来源材料

本目录后续文档只能从以下材料中提炼“已记录证据、缺口和人工确认项”，不得反推未确认规范：

- `docs/prd-autodev/oneops-engineering-docs-standardization/prd.md`：工程文档标准化、中文优先、`blocked-human-confirmation` 门禁。
- `docs/prd-autodev/oneops-engineering-docs-standardization/idea.md`：AI/autodev 只能整理、提炼、占位、标风险，不能反推需求或设计。
- `docs/development/prompt-assets-analysis.md`：历史 prompts 只能作为素材，缺失正式文档时需先提炼为待确认文档。
- `docs/development-doc-templates/**`：标准化开发文档模板，是候选文档结构的主要依据。
- `docs/development/templates.md`、`api-documentation-standard.md`、`backend-development-standard.md`、`testing-standard.md`：补充规范和约束，不替代 `docs/development-doc-templates/**` 的模板结构。
- `docs/prd-autodev/d2-launch-acceptance/evidence-index.md`：Device V2 launch evidence 的已证明项、blocked 项、NOT RUN 项和 accepted risk。
- `docs/prd-autodev/d2-launch-acceptance/launch-readiness-report.md`：Device V2 入库工作台与设备 V2 清册管理的 launch readiness 结论。
- `docs/openclaw-autodev/shared-d2.md`：D2 FE/BE 协作记录和阶段性 evidence 路径。

## 6. 待人工确认清单

### 6.1 通用门禁

- `[待人工确认: 项目负责人]` 是否允许本目录继续拆分候选文档。
- `[待人工确认: 产品负责人]` Device V2 入库与设备管理的业务范围、角色范围、上线范围。
- `[待人工确认: 技术负责人]` 哪些 evidence 可沉淀为工程约束，哪些只能保留为阶段性 launch 证据。
- `[待人工确认: 测试负责人]` 哪些 launch evidence 可作为后续测试输入，哪些必须重新设计测试用例。

### 6.2 Device V2 入库

- `[待人工确认: 产品负责人]` 完整样本范围：继续补齐 5 设备、替换候选设备，或接受 2/5 风险。
- `[待人工确认: 产品负责人]` 3 个 blocked candidates 的 platform/catalog/rack enrichment 来源与处理方式。
- `[待人工确认: 技术负责人]` 入库批次保留、错误状态、跳过记录、源记录安全的正式规则。
- `[待人工确认: 测试负责人]` 入库 upload/validate/apply/handoff/field reconciliation 的验收口径。

### 6.3 Device V2 设备管理

- `[待人工确认: 产品负责人]` UI edit/update 是否属于 launch 必须项，以及未运行证据如何处理。
- `[待人工确认: 产品负责人]` clone delete cleanup 的触发时机、保留策略与禁止删除边界。
- `[待人工确认: 技术负责人]` store start/retry、task summary、runs、observations、latest DC2 的正式工程口径。
- `[待人工确认: 安全/权限负责人]` 非 admin 角色、权限模型、可见操作和拒绝路径。
- `[待人工确认: 测试负责人]` 5-device parallel collection 与 reduced-scope accepted risk 的验收表达。

## 7. 后续维护规则

- 新增或拆分的 Device V2 文档默认状态必须是 `blocked-human-confirmation`。
- 文档中所有未确认信息必须保留为 `[待人工确认:<role>]`、`[待补充]` 或 `[候选方案: AI 提炼]`。
- 任何文档不得因为已有 evidence 而自动确认 API、DTO、数据库字段、权限、fixture、采集协议、删除策略或验收标准。
- 状态提升到 `reviewed`/`active` 只能由人工确认后执行，并需要同步记录确认人、日期和范围。
