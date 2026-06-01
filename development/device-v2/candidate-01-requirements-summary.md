# 【需求概要】OneOPS_DeviceV2_V1.0

## 1. 文档信息

| 项目 | 内容 |
|------|------|
| 系统名称 | OneOPS |
| 版本号 | V1.0 |
| 创建日期 | 2026-05-15 |
| 文档状态 | `blocked-human-confirmation` |
| 需求来源 | 当前源码反向提取：`OneOPS/app/device/v2/**`、`OneOPS/app/device/v2/ingest/**`、`OneOPS-UI/src/views/device/**`、`OneOPS-UI/src/api/device/**` |
| 编写人 | Codex AI 候选稿，待人工修改定稿 |

## 2. 业务背景与目标

### 2.1 业务背景

Device V2 是 OneOPS 中面向设备入库、设备清册管理、设备采集/store pipeline、V1/V2 同步和设备动态属性管理的一组功能。当前代码已经存在后端 Device V2 模型、导入批次、ingest task、store run、observation、schema、change history 等能力，也存在前端设备管理页、导入批次页、ingest pipeline 页和 schema 设计页。

本文档不是新需求定义，而是基于当前真实代码反向生成的候选需求概要，用于帮助人工快速确认真实业务范围、补充缺口并形成正式标准文档。

### 2.2 业务目标

| 目标编号 | 业务目标 | 价值说明 | 衡量方式 |
|----------|----------|----------|----------|
| G-001 | 建立 Device V2 设备主记录管理能力 | 支撑设备清册查询、详情、创建、更新、删除和动态属性维护 | `[待确认]` 以人工确认后的清册字段、权限和操作范围为准 |
| G-002 | 支持 Device V2 入库任务 | 支撑手工 JSON、Excel 上传、导入批次、校验、应用和结果追踪 | `[待确认]` 以入库成功率、错误可解释性、可追溯性为准 |
| G-003 | 支持 store pipeline 与采集 evidence | 支撑设备纳管准备、store/start、task summary、runs、observations、latest DC2 查询 | `[待确认]` 以人工确认的 store 成功判定和采集证据为准 |
| G-004 | 支持 V1/V2 同步与兼容 | 降低旧设备台账和 Device V2 并存期间的数据割裂 | `[待确认]` 以同步策略、覆盖策略、冲突策略为准 |
| G-005 | 支持动态 schema 和变更历史 | 支撑动态字段扩展、schema 预检查、字段变更追踪 | `[待确认]` 以 schema 发布门禁和变更审计规则为准 |

## 3. 用户角色

| 角色 | 描述 | 主要职责 | 使用终端 |
|------|------|----------|----------|
| 设备管理员 | 维护设备清册和设备属性的人员 | 查询、创建、编辑、删除或同步 Device V2 设备 | Web |
| 入库操作员 | 执行设备批量入库或 Excel 上传的人员 | 准备入库数据、提交任务、查看校验和执行结果 | Web |
| 采集/纳管操作员 | 启动 store pipeline 或查看采集结果的人员 | 发起 store/start、查看 task、runs、observations、latest DC2 | Web |
| 架构/后端负责人 | 维护 Device V2 数据模型、接口、同步和 store 逻辑 | 确认数据模型、接口契约、状态机和兼容策略 | 代码/接口 |
| 测试负责人 | 验证入库、管理和采集链路 | 设计 read-only 验证、fixture、危险操作审批 | Web/API/自动化 |
| 安全负责人 | 确认凭据、删除、purge、同步、采集等风险边界 | 确认权限、审计、脱敏、危险操作策略 | 文档/配置 |

## 4. 功能需求

### 4.1 Device V2 设备管理

- 功能点1：查询 Device V2 设备列表，支持分页、关键字、编码、名称、IP、标签、属性、纳管状态和位置过滤。
- 功能点2：查看 Device V2 设备详情，包含基础字段、动态属性、元数据、标签、分组标签和关联信息。
- 功能点3：创建、更新 Device V2 设备主记录。
- 功能点4：删除 Device V2 设备，删除策略、关系清理和生产环境权限待确认。
- 功能点5：查看 change history、network overview、interfaces、status 等辅助信息。

### 4.2 Device V2 入库

- 功能点1：通过 `device/v2/ingest` 提交入库任务或上传 Excel。
- 功能点2：通过 `device/v2/import/batches` 创建、上传、校验、应用、重试、更新和清理导入批次。
- 功能点3：查询入库任务、导入批次、导入记录、锚点冲突和模板。
- 功能点4：保留入库任务结果和错误信息，支持人工修正和重试。

### 4.3 Device V2 store 与采集证据

- 功能点1：查询设备 store readiness。
- 功能点2：启动或重试 store pipeline。
- 功能点3：查询 task 详情、summary、collection plans、runs、observations。
- 功能点4：查询设备最近一次 store collection DC2 结果。

### 4.4 Device V2 schema 与同步

- 功能点1：查询当前 schema。
- 功能点2：保存 schema 和执行 schema precheck。
- 功能点3：从 V1 同步到 V2，或从 V2 同步到 V1。
- 功能点4：执行 base reference check。

## 5. 非功能需求概要

### 5.1 性能需求

| 指标 | 要求 | 备注 |
|------|------|------|
| 列表查询响应时间 | `[待确认]` | 当前代码支持分页；P95 指标未确认 |
| 批量入库数据量 | `[待确认]` | Excel 行数、批次记录上限、分页上限需人工确认 |
| store task 查询分页 | 默认/上限由后端代码控制 | runs/observations 查询存在分页和 page_size 限制 |

### 5.2 可用性需求

系统应能在入库失败、校验失败、store 部分失败、采集缺失时返回可定位的错误或 evidence。具体错误分级、页面提示和重试入口需要人工确认。

### 5.3 安全性需求

认证、权限、tenant/device 边界、凭据引用展示、删除、purge、sync、store/start 等危险操作必须由人工确认。候选文档不得直接授权自动化执行这些操作。

### 5.4 可扩展性需求

Device V2 通过 `labels`、`attributes`、`metadata`、`group_tags` 和 schema 支持动态扩展。扩展字段的命名、类型、必填、兼容和迁移规则待人工确认。

## 6. 关键业务规则

| 规则编号 | 业务规则 | 触发场景 | 处理要求 |
|----------|----------|----------|----------|
| R-001 | Device V2 设备以 `code` 作为业务唯一编码 | 创建、查询、更新、删除、store、sync | `code` 必须可追溯，自动编码策略待确认 |
| R-002 | JSON 扩展字段需要序列化到持久化字段 | 创建、更新、查询 DeviceV2 | `labels_json`、`attributes_json`、`metadata_json`、`group_tags_json` 与内存字段互转 |
| R-003 | 入库任务和导入批次必须留下结果和错误信息 | ingest/import 执行 | 保留 status、message、error、row_no、device_code 等追踪字段 |
| R-004 | store/start、retry、sync、delete、purge 属于危险或写入操作 | 自动化测试、人工操作 | 默认不得由自动化直接执行，除非 story scope 明确批准 |
| R-005 | read-only 查询接口可作为自动化候选验证 | 列表、详情、task 查询、observations 查询 | 仍需确认 fixture、权限和环境 |

## 7. 系统边界与约束

### 7.1 系统边界

| 范围 | 内容 |
|------|------|
| 包含范围 | Device V2 设备管理、入库、导入批次、store pipeline、schema、sync、change history、network overview |
| 不包含范围 | 真实设备生产采集授权、凭据管理正式规则、删除策略定稿、上线验收标准 |
| 外部依赖 | Device V1、Entity V2、设备采集/observations、前端路由和 request 封装、权限系统 `[待确认]` |

### 7.2 约束条件

| 约束类型 | 约束内容 | 影响 |
|----------|----------|------|
| 技术约束 | 后端为 Go/Gin/GORM，前端为 Vue/TypeScript | 07 后端开发设计模板中的 Java/Spring 结构不直接适用，需要按当前技术栈反向填写 |
| 业务约束 | 删除、purge、sync、store/start、Excel 上传有副作用 | 自动化和测试需要审批边界 |
| 数据约束 | 动态字段较多，业务语义不都能从代码确认 | 候选文档必须保留 `[待确认]` |

## 8. 用户故事

### 8.1 设备管理员用户故事

#### 8.1.1 查询并维护设备清册

- Web：设备管理员进入 Device V2 设备管理页面。
- Web：用户按关键字、IP、标签或位置过滤设备列表。
- Web：用户打开设备详情，查看属性、状态、采集证据和变更历史。
- Web：用户按权限创建、编辑或删除设备，危险操作需确认。

#### 8.1.2 发起设备 store pipeline

- Web：用户选择一个或多个设备。
- Web：用户打开 store/start 弹窗并提交任务。
- Web：系统返回 task_id，用户查看 summary、runs、observations 和 latest DC2。

### 8.2 入库操作员用户故事

#### 8.2.1 上传 Excel 入库

- Web：入库操作员进入 Device V2 ingest pipeline 页面。
- Web：用户下载模板、上传 Excel 或整理草稿行。
- Web：系统生成 ingest task，展示校验问题、执行结果和设备导入结果。

#### 8.2.2 导入批次追踪

- Web：用户进入 import batches 页面。
- Web：用户查看历史批次、最近任务、导入记录和锚点冲突。
- Web：用户按人工确认后的规则执行 retry/apply/purge。

## 9. 关键业务名词

| 名词 | 解释 | 备注 |
|------|------|------|
| Device V2 | OneOPS 当前设备 V2 主记录与管理模型 | 真实模型为 `DeviceV2`，表名 `platform_devices_v2` |
| Ingest Task | 新入库框架任务 | 真实模型为 `DeviceV2IngestTask` |
| Import Batch | 多次导入批次 | 真实模型为 `DeviceV2ImportBatch` |
| Store Run | store pipeline 中单设备执行结果 | 真实模型为 `DeviceV2StoreRun` |
| Observation | store/采集中记录的字段观测事实 | 真实模型为 `DeviceV2Observation` |
| Latest DC2 | 最近一次 DC2 采集结果视图 | 当前是接口视图，不是独立模型 |

## 10. 待确认事项

| 序号 | 待确认内容 | 影响范围 | 负责人 | 状态 |
|------|------------|----------|--------|------|
| 1 | Device V2 本期正式业务范围是否包含 import batch 与 ingest task 两套入库链路 | 入库 | 产品负责人 | 待确认 |
| 2 | 删除、purge、sync、store/start 是否允许在生产环境由 UI 发起 | 管理/安全 | 安全负责人 | 待确认 |
| 3 | Device V2 状态、纳管状态、生命周期状态的正式枚举和含义 | 管理/store | 产品/后端负责人 | 待确认 |
| 4 | 凭据引用字段是否允许展示、提交、导出 | 入库/安全 | 安全负责人 | 待确认 |
| 5 | 哪些 read-only 接口可进入自动化回归 | 测试 | 测试负责人 | 待确认 |

## 11. 附录

- 参考文档：`docs/development-doc-templates/01-需求概要模板.md`
- 参考源码：`OneOPS/app/device/v2/**`
- 参考前端：`OneOPS-UI/src/views/device/**`、`OneOPS-UI/src/api/device/**`


### 11.1 代码事实来源清单

> 本节为 DEV-DOCS-003A 追加的代码事实来源清单。本文档状态仍为 `blocked-human-confirmation`，不可直接作为开发、测试、上线、story 发布、API 契约或验收依据。

| 分类 | 源码路径 / 材料 | 对应事实 | 待人工确认 |
|------|----------------|----------|------------|
| 标准文档结构 | `docs/development-doc-templates/01-需求概要模板.md` | 本文保留 01 模板的文档信息、业务背景与目标、用户角色、功能需求、非功能需求、业务规则、边界、用户故事、名词、待确认事项和附录结构。 | `[待人工确认: 项目负责人]` 是否进入人工 review。 |
| route/router | `OneOPS/app/device/v2/router/device_v2.go`、`OneOPS/app/device/v2/ingest/router/device_v2_ingest.go` | 当前真实 API 入口覆盖 Device V2 管理、schema、sync、store task、import batch、ingest task、change history、network overview 等。 | `[待人工确认: 后端负责人]` 哪些入口属于正式长期能力。 |
| handler/controller | `OneOPS/app/device/v2/api/device_v2.go`、`device_v2_store_minimal_api.go`、`device_v2_change_history.go`、`device_v2_sync_to_v1.go` | Handler 负责请求绑定、参数校验、service 调用和响应包装；写入/危险动作包括 create/update/delete、sync、store start/retry、import apply/purge。 | `[待人工确认: 安全/权限负责人]` 写入动作权限、审批和审计规则。 |
| DTO/model/service | `OneOPS/app/device/v2/dto/*.go`、`model/*.go`、`service/*.go`、`service/impl/*.go` | 当前真实模型包含 `DeviceV2`、import batch/record、ingest task、store run、observation；`DeviceV2` 使用 code 唯一和 JSON 动态字段。 | `[待人工确认: 后端负责人]` 字段语义、状态枚举和数据契约。 |
| DAO/GORM 调用 | `OneOPS/app/device/v2/service/impl/device_v2.go`、`device_v2_minimal_import_lifecycle.go`、`device_v2_minimal_import_record_flow.go`、`device_v2_minimal_store.go` | 通过 GORM 查询/更新 entity source、import batch/record、pipeline task、store run 和 observations。 | `[待人工确认: 后端负责人]` 事务、幂等、并发与清理策略。 |
| 前端 wrapper/page | `OneOPS-UI/src/api/device/device-v2.ts`、`device-v2-import.ts`、`device-v2-ingest.ts`、`src/router/utils.ts`、`src/views/device/DeviceV2Management.vue`、`DeviceV2IngestPipelineRedesign.vue` | 前端存在设备管理、管理重构、schema、import batches、ingest pipeline 路由和对应请求封装。 | `[待人工确认: 前端负责人]` 正式菜单、页面命名和交互流程。 |
| evidence | `docs/prd-autodev/d2-launch-acceptance/evidence-index.md`、`launch-readiness-report.md` | 2 个 approved clones 的 import/apply、handoff、store、observations、latest DC2 有证据；完整 5-device、UI edit、cleanup、非 admin 权限仍 blocked/not run。 | `[待人工确认: 测试负责人]` 哪些 evidence 可作为后续测试输入。 |

- 当前真实代码事实：见上表与 `docs/openclaw-autodev/evidence/dev-docs/DEV-DOCS-003A-device-v2-01-02-code-facts.md`。
- 候选文档内容：本文按 01 模板填充业务背景、目标、角色、功能、规则、边界和用户故事。
- AI 推导建议：P0/P1 和用户角色仅为候选提炼，需人工确认。
- 规划缺口：正式业务范围、权限、验收标准、性能目标、删除/purge/sync/store 策略均待人工确认。
