# 【实体属性清单】OneOPS_DeviceV2_V1.0

## 1. 文档信息

| 项目 | 内容 |
|------|------|
| 系统名称 | OneOPS |
| 模块名称 | Device V2 入库与设备管理 |
| 版本号 | V1.0 |
| 创建日期 | 2026-05-15 |
| 文档状态 | `blocked-human-confirmation` |
| 关联需求文档 | 【需求概要】OneOPS_DeviceV2_V1.0.md |
| 编写说明 | 基于当前真实源码反向整理的候选实体属性清单；不可直接作为数据库设计、API 契约、迁移、开发或验收依据。 |

## 2. 实体概览

| 实体名称 | 中文名称 | 业务含义 | 主要来源 |
|----------|----------|----------|----------|
| DeviceV2 | 设备 V2 主记录 | Device V2 清册中的设备主实体，包含业务编码、名称、平台编码、状态和动态扩展字段。 | 当前真实代码事实：`OneOPS/app/device/v2/model/device_v2.go`、`OneOPS-UI/src/api/device/device-v2.ts` |
| DeviceV2IngestTask | Device V2 入库任务 | 通过手工 API、Excel 上传或候选来源提交的入库任务，记录来源、状态、设备清单、阶段和结果。 | 当前真实代码事实：`OneOPS/app/device/v2/ingest/model/device_v2_ingest_task.go`、`device-v2-ingest.ts` |
| DeviceV2ImportBatch | Device V2 导入批次 | 多次导入链路中的批次级记录，记录模板、pass、namespace、模式、统计、状态和选项。 | 当前真实代码事实：`OneOPS/app/device/v2/model/device_v2_import_batch.go`、`device_v2_import.ts` |
| DeviceV2ImportRecord | Device V2 导入行记录 | 导入批次中的行级记录，记录行号、匹配方式、校验/应用状态、错误和原始/标准化 payload。 | 当前真实代码事实：`OneOPS/app/device/v2/model/device_v2_import_record.go`、`device_v2_import.ts` |
| DeviceV2StoreRun | Device V2 Store Run | 一次 store pipeline task 中单台设备的执行结果和可纳管状态。 | 当前真实代码事实：`OneOPS/app/device/v2/model/device_v2_store_run.go`、`device-v2.ts` |
| DeviceV2Observation | Device V2 Observation | store/采集链路产出的字段级观测事实。 | 当前真实代码事实：`OneOPS/app/device/v2/model/device_v2_observation.go`、`device-v2.ts` |
| DeviceV2ChangeEvent | Device V2 变更事件 | 设备台账创建、更新、删除、同步、导入、采集写回等变更事件。 | 当前真实代码事实：`OneOPS/app/device/v2/model/device_v2_change_event.go`、`device_v2_change_history.go` |
| DeviceV2ChangeField | Device V2 变更字段 | 变更事件中的字段级 before/after 差异。 | 当前真实代码事实：`OneOPS/app/device/v2/model/device_v2_change_field.go` |
| DeviceV2Schema | Device V2 Schema | 动态属性、标签和关系类型配置，供列表/详情/表单渲染与校验候选使用。 | 当前真实代码事实：`OneOPS/app/device/v2/model/device_v2_schema.go`、`DeviceV2SchemaDesign.vue` |
| DeviceInterfaceV2 | 设备接口 V2 | 设备接口镜像模型，支撑接口/IP/MAC/邻居等网络视图。 | 当前真实代码事实：`OneOPS/app/device/v2/model/device_interface_v2.go` |

## 3. 实体属性清单

### 3.1 DeviceV2（设备 V2 主记录）

| 字段名 | 数据类型 | 约束信息 | 说明 |
|--------|----------|----------|------|
| id | String | 主键；`varchar(128)`；可与 Code 一致 | 主键 ID |
| code | String | `varchar(64)`；唯一索引；非空 | 设备业务唯一编码；正式编码规则 `[待人工确认: 产品负责人]` |
| type | String | `varchar(32)`；默认 `device_v2` | 实体类型，当前常量为 `device_v2` |
| name | String | `varchar(255)` | 设备名称 |
| platform_code | String | `varchar(64)`；索引 | 平台编码 |
| status | String | `varchar(32)` | 设备状态；正式枚举 `[待人工确认: 产品负责人]` |
| lifecycle_stage | String | 非持久化；由 attributes 提取 | 生命周期阶段；业务语义 `[待人工确认]` |
| stage_status | String | 非持久化；由 attributes 提取 | 阶段状态；业务语义 `[待人工确认]` |
| manage_status | String | 非持久化；由 attributes 提取 | 纳管状态；当前影响 manageable 计算 |
| manageable | Boolean | 非持久化；由 attributes 或 manage_status 推导 | 是否可纳管；正式判定规则 `[待人工确认: 后端负责人]` |
| labels | JSON Object | 非持久化；序列化至 `labels_json` | 动态标签 map |
| attributes | JSON Object | 非持久化；序列化至 `attributes_json` | 动态属性 map |
| metadata | JSON Object | 非持久化；序列化至 `metadata_json` | 动态元数据 map |
| group_tags | JSON Array | 非持久化；序列化至 `group_tags_json` | 分组标签 |
| labels_json | LongText | 持久化列 | labels 的 JSON 存储列 |
| attributes_json | LongText | 持久化列 | attributes 的 JSON 存储列 |
| metadata_json | LongText | 持久化列 | metadata 的 JSON 存储列 |
| group_tags_json | LongText | 持久化列 | group_tags 的 JSON 存储列 |
| created_at | Time | 自动填充 | 创建时间 |
| updated_at | Time | 自动更新 | 更新时间 |

### 3.2 DeviceV2IngestTask（Device V2 入库任务）

| 字段名 | 数据类型 | 约束信息 | 说明 |
|--------|----------|----------|------|
| task_id | String | 主键；`varchar(64)` | 入库任务 ID |
| status | String | `varchar(32)`；索引；非空 | 当前代码支持 `prepared`、`completed`、`failed` |
| framework_version | String | `varchar(32)`；非空 | 当前默认 `v0-minimal` |
| source | String | `varchar(64)`；索引；非空 | 当前支持 `manual_api`、`excel_upload`、`reference_payload`、`future_pipeline` |
| requested_by | String | `varchar(128)` | 请求人 |
| execution_enabled | Boolean | 默认 false；非空 | 是否启用执行适配；正式开关规则 `[待人工确认: 安全/权限负责人]` |
| device_count | Integer | 默认 0；非空 | 任务设备数量 |
| message | String | `varchar(1024)` | 任务消息 |
| devices | JSON Array | 非持久化；序列化至 `devices_json` | 入库设备清单；包含 code/biz_code/name/platform/status/credential refs/location/hardware/labels/attributes 等候选字段 |
| result | JSON Object | 非持久化；序列化至 `result_json` | 执行结果 |
| stages | JSON Array | 非持久化；序列化至 `stages_json` | 当前默认阶段：`request_received`、`canonical_device_payload`、`validator_slot`、`execution_adapter` |
| devices_json | LongText | 持久化列 | devices JSON 存储列 |
| result_json | LongText | 持久化列 | result JSON 存储列 |
| stages_json | LongText | 持久化列 | stages JSON 存储列 |
| created_at | Time | 自动填充 | 创建时间 |
| updated_at | Time | 自动更新 | 更新时间 |

### 3.3 DeviceV2ImportBatch（Device V2 导入批次）

| 字段名 | 数据类型 | 约束信息 | 说明 |
|--------|----------|----------|------|
| id | UInt64 | 主键；自增 | 批次记录主键 |
| batch_id | String | `varchar(64)`；唯一索引；非空 | 批次业务 ID |
| template_code | String | `varchar(128)`；索引 | 模板编码 |
| import_pass | String | `varchar(64)`；索引；非空 | 导入 pass |
| namespace | String | `varchar(128)`；索引；默认 `infra/device` | 命名空间 |
| mode | String | `varchar(32)`；非空；默认 `apply` | 导入模式；前端类型含 `dry_run` / `apply` |
| status | String | `varchar(32)`；索引；非空；默认 `created` | 批次状态；完整状态机 `[待人工确认: 后端负责人]` |
| source_file | String | `varchar(255)` | 源文件名 |
| sheet | String | `varchar(128)` | Excel sheet |
| total/success/failed/skipped | Integer | 默认 0；非空 | 行统计 |
| validate_failed/apply_failed/project_failed | Integer | 默认 0；非空 | 校验、应用、投影失败统计 |
| auto_code_count/auto_generated_ratio | Integer | 默认 0；非空 | 自动编码统计 |
| ambiguous_count/not_found_count | Integer | 默认 0；非空 | 锚点匹配异常统计 |
| dominant_code_source/dominant_code_ratio | String/Integer | 默认空/0 | 主要编码来源统计 |
| message | String | `varchar(1024)` | 批次消息 |
| created_by | String | `varchar(128)` | 创建人 |
| options | JSON Object | 非持久化；序列化至 `options_json` | 批次选项 |
| code_source_stats | JSON Object | 非持久化；序列化至 `code_source_stats_json` | 编码来源统计 |
| created_at/updated_at | Time | 自动填充/更新 | 审计时间 |

### 3.4 DeviceV2ImportRecord（Device V2 导入行记录）

| 字段名 | 数据类型 | 约束信息 | 说明 |
|--------|----------|----------|------|
| id | UInt64 | 主键；自增 | 行记录主键 |
| batch_id | String | `varchar(64)`；索引；非空 | 所属批次 ID |
| row_no | Integer | 索引；默认 0；非空 | Excel/输入行号 |
| namespace | String | `varchar(128)`；索引；默认 `infra/device` | 命名空间 |
| entity_code | String | `varchar(128)`；索引 | 解析后的实体编码 |
| resolved_entity_id | String | `varchar(128)`；索引 | 匹配到的实体 ID |
| match_mode | String | `varchar(32)`；索引 | 匹配方式 |
| code_source | String | `varchar(64)`；索引 | 编码来源 |
| locator_trace | String | `varchar(1024)` | 定位追踪 |
| validate_status | String | `varchar(32)`；索引；默认 `pending`；非空 | 校验状态 |
| apply_status | String | `varchar(32)`；索引；默认 `pending`；非空 | 应用状态 |
| error_code/error_message | String/Text | 可选 | 错误编码和错误消息 |
| conflict_candidates | JSON Array | 非持久化；序列化至 `conflict_candidates_json` | 冲突候选 |
| raw_payload | JSON Object | 非持久化；序列化至 `raw_payload_json` | 原始行数据 |
| normalized_patch | JSON Object | 非持久化；序列化至 `normalized_patch_json` | 标准化变更 |
| applied_at | Time | 可空 | 应用时间 |
| created_at/updated_at | Time | 自动填充/更新 | 审计时间 |

### 3.5 DeviceV2StoreRun（Device V2 Store Run）

| 字段名 | 数据类型 | 约束信息 | 说明 |
|--------|----------|----------|------|
| run_id | String | 主键；`varchar(64)` | 单设备 store run ID |
| task_id | String | `varchar(64)`；索引；非空 | pipeline task ID |
| device_code | String | `varchar(128)`；索引；非空 | 设备编码 |
| status | String | `varchar(32)`；索引；默认 `pending`；非空 | 当前代码支持 `pending/running/partial/success/failed/blocked` |
| current_step | String | `varchar(64)`；默认空 | 当前步骤 |
| core_store_status | String | `varchar(32)`；索引；默认 `pending`；非空 | 当前代码支持 `pending/success/failed/blocked` |
| manageable_status | String | `varchar(32)`；索引；默认 `unknown`；非空 | 当前代码支持 `unknown/pending/ready/unready` |
| summary | JSON Object | 非持久化；序列化至 `summary_json` | run 摘要 |
| created_at/updated_at | Time | 自动填充/更新 | 审计时间 |
| finished_at | Time | 可空 | 完成时间 |

### 3.6 DeviceV2Observation（Device V2 Observation）

| 字段名 | 数据类型 | 约束信息 | 说明 |
|--------|----------|----------|------|
| observation_id | String | 主键；`varchar(64)` | 观测记录 ID |
| task_id | String | `varchar(64)`；索引；非空 | pipeline task ID |
| run_id | String | `varchar(64)`；索引；非空 | store run ID |
| device_code | String | `varchar(128)`；索引；非空 | 设备编码 |
| capability | String | `varchar(64)`；索引；非空 | 能力分类 |
| field_key | String | `varchar(128)`；索引；非空 | 观测字段 key |
| status | String | `varchar(32)`；索引；默认 `success`；非空 | 当前代码支持 `success/partial/failed/skipped` |
| value | JSON Object | 非持久化；序列化至 `value_json` | 标准化值 |
| raw | JSON Object | 非持久化；序列化至 `raw_json` | 原始值 |
| source/plane/collector_key | String | 可选；有长度限制 | 采集来源、平面、采集器 key |
| error_message | Text | 可选 | 错误信息 |
| collected_at/created_at/updated_at | Time | 自动填充/更新 | 采集与审计时间 |

### 3.7 DeviceV2ChangeEvent（Device V2 变更事件）

| 字段名 | 数据类型 | 约束信息 | 说明 |
|--------|----------|----------|------|
| id | UInt64 | 主键；自增 | 事件 ID |
| device_code | String | `varchar(128)`；索引；非空 | 设备编码 |
| entity_type/entity_id | String | 索引；非空 | 关联实体类型和 ID |
| change_domain | String | `varchar(32)`；索引；默认 `ledger` | 变更域 |
| action | String | `varchar(32)`；索引；非空 | 当前代码支持 `create/update/delete` |
| source | String | `varchar(64)`；索引；非空 | 当前代码支持 `manual_api/v1_sync/batch_import/store_pipeline/device_collection_writeback/system_auto_repair` |
| operator | String | `varchar(128)`；索引 | 操作人 |
| title/summary | String/Text | 可选 | 事件标题和摘要 |
| risk_level | String | `varchar(32)`；索引；默认 `low` | 当前代码支持 `low/medium/high` |
| status | String | `varchar(32)`；索引；默认 `new` | 当前代码支持 `new/acknowledged/requires_action/ignored/resolved` |
| status_remark/status_updated_by/status_updated_at | Text/String/Time | 可选 | 状态处理信息 |
| field_count | Integer | 默认 0；非空 | 变更字段数量 |
| before_snapshot/after_snapshot | JSON Object | 非持久化；序列化至 JSON 列 | 变更前后快照 |
| created_at/updated_at | Time | 自动填充/更新 | 审计时间 |

### 3.8 DeviceV2ChangeField（Device V2 变更字段）

| 字段名 | 数据类型 | 约束信息 | 说明 |
|--------|----------|----------|------|
| id | UInt64 | 主键；自增 | 字段变更 ID |
| event_id | UInt64 | 索引；非空 | 所属变更事件 |
| device_code | String | `varchar(128)`；索引；非空 | 设备编码 |
| field_path | String | `varchar(255)`；索引；非空 | 字段路径 |
| field_label | String | `varchar(255)` | 字段标签 |
| field_domain | String | `varchar(64)`；索引 | 字段域 |
| change_kind | String | `varchar(32)`；索引；非空 | 当前代码支持 `added/updated/removed` |
| sort_order | Integer | 默认 0；非空 | 展示顺序 |
| before_value_json/after_value_json | LongText | 可选 | 字段变更前后值 |
| created_at | Time | 可选 | 创建时间 |

### 3.9 DeviceV2Schema（Device V2 Schema）

| 字段名 | 数据类型 | 约束信息 | 说明 |
|--------|----------|----------|------|
| id | Integer | 主键；自增 | schema ID |
| attributes_schema | LongText / JSON Array | 持久化列；解析为 `AttributeSpec[]` | 属性定义 |
| labels_schema | LongText / JSON Array | 持久化列；解析为 `AttributeSpec[]` | 标签定义 |
| relation_types | Text / JSON Array | 持久化列；解析为 `RelationTypeSpec[]` | 关系类型定义 |
| created_at/updated_at | Time | 自动填充/更新规则 `[待确认]` | 审计时间 |

### 3.10 DeviceInterfaceV2（设备接口 V2）

| 字段名 | 数据类型 | 约束信息 | 说明 |
|--------|----------|----------|------|
| id | String | 主键；`varchar(128)`；默认可与 interface_code 一致 | 接口主键 |
| interface_code | String | `varchar(64)`；唯一索引；非空 | 接口编码 |
| device_code | String | `varchar(64)`；索引；非空 | 所属设备编码 |
| source_device_id | String | `varchar(36)`；索引；可空 | 源设备 ID |
| name/status/phy_protocol/type | String | 可选 | 接口名称、状态、物理协议、接口类型 |
| snmp_if_index | Integer | 可选 | SNMP ifIndex |
| local_ip/local_macs/peer_macs/forward_macs | JSON Array | 非持久化；序列化至对应 JSON 列 | IP/MAC/邻居/转发 MAC |
| metadata | JSON Object | 非持久化；序列化至 `metadata_json` | 接口元数据 |
| created_at/updated_at | Time | 自动填充/更新 | 审计时间 |

## 4. 实体关系说明

| 源实体 | 关系 | 目标实体 | 关系说明 | 约束说明 |
|--------|------|----------|----------|----------|
| DeviceV2 | 一对多 | DeviceInterfaceV2 | 一个设备可关联多个接口镜像记录。 | 当前通过 `device_code` 逻辑关联；未见显式数据库外键。 |
| DeviceV2IngestTask | 一对多 | DeviceV2IngestDevice | 一个入库任务包含多个设备草稿/输入设备。 | 当前以 `devices_json` JSON 数组存储，不是独立表。 |
| DeviceV2ImportBatch | 一对多 | DeviceV2ImportRecord | 一个导入批次包含多条行记录。 | 当前通过 `batch_id` 逻辑关联；未见显式数据库外键。 |
| DeviceV2ImportRecord | 多对一/可选 | DeviceV2 | 行记录可解析/应用到 DeviceV2 设备。 | 当前通过 `entity_code`、`resolved_entity_id` 逻辑关联；匹配规则待人工确认。 |
| DeviceV2StoreRun | 多对一 | DeviceV2 | 每个 run 对应一台设备的一次 store 执行结果。 | 当前通过 `device_code` 逻辑关联。 |
| DeviceV2Observation | 多对一 | DeviceV2StoreRun | observation 属于某个 run 和 task。 | 当前通过 `run_id`、`task_id` 逻辑关联。 |
| DeviceV2ChangeEvent | 一对多 | DeviceV2ChangeField | 一个变更事件包含多个字段级变化。 | 当前通过 `event_id` 逻辑关联。 |
| DeviceV2Schema | 配置关系 | DeviceV2 | schema 影响 DeviceV2 动态属性、标签和关系类型的候选渲染/校验。 | 当前为单例/当前生效配置的代码注释；正式发布门禁待确认。 |

## 5. 设计建议

- 唯一性：当前真实代码中 `DeviceV2.code`、`DeviceV2ImportBatch.batch_id`、`DeviceInterfaceV2.interface_code` 是唯一索引候选；是否作为正式业务唯一性约束需 `[待人工确认: 后端负责人]`。
- 状态字段：当前真实状态值包括 ingest task `prepared/completed/failed`、store run `pending/running/partial/success/failed/blocked`、core store `pending/success/failed/blocked`、manageable `unknown/pending/ready/unready`、observation `success/partial/failed/skipped`、change event `new/acknowledged/requires_action/ignored/resolved`。这些只是当前真实代码事实，不代表正式状态机。
- 审计字段：多数实体包含 `created_at`、`updated_at`；部分包含 `created_by`、`operator`、`status_updated_by`、`applied_at`、`finished_at`、`collected_at`。审计必填、操作者来源和保留期 `[待人工确认: 安全/权限负责人]`。
- 扩展字段：DeviceV2、ImportBatch、ImportRecord、StoreRun、Observation、IngestTask 均存在 JSON 扩展或快照字段。正式 schema 类型、兼容策略和迁移策略 `[待人工确认: 后端负责人]`。
- 当前真实代码事实：本节字段来自 Go model、前端 wrapper 类型和已读 router/page 入口。
- 候选文档内容：本文将模型字段整理为实体属性表，便于人工 review。
- AI 推导建议：优先将 DeviceV2、IngestTask、ImportBatch/Record、StoreRun/Observation 作为核心实体 review；ChangeEvent/Schema/Interface 作为管理增强实体 review。
- 规划缺口：字段业务语义、必填规则、状态机、权限/审计、索引、外键、删除策略、数据保留期均未确认。

## 6. 待确认事项

| 序号 | 字段/关系 | 待确认内容 | 影响 |
|------|-----------|------------|------|
| 1 | DeviceV2.code | 编码生成、唯一性、可修改性、与 V1/导入编码的关系 | 影响 API 契约、导入去重、清册主键策略 |
| 2 | DeviceV2.status/manage_status/manageable | 正式状态枚举、状态流转和纳管判定 | 影响列表筛选、store readiness、验收口径 |
| 3 | JSON 扩展字段 | attributes/labels/metadata/group_tags 的 schema、类型、必填和兼容规则 | 影响前端表单、后端校验和迁移 |
| 4 | ImportBatch/ImportRecord 状态 | validate/apply/retry/purge 全状态机和错误编码 | 影响导入流程、重试、人工修正和测试 |
| 5 | StoreRun/Observation 状态 | store、core_store、manageable、observation 状态与失败分类 | 影响采集证据、运维告警和 launch readiness |
| 6 | 逻辑关联 | 是否补充外键、软删除、级联清理和历史保留 | 影响数据库设计、删除策略和审计 |
| 7 | 权限与审计字段 | 操作者来源、角色权限、敏感字段展示和留存策略 | 影响安全评审和上线门禁 |

## 7. 代码事实来源清单

详见 `docs/openclaw-autodev/evidence/dev-docs/DEV-DOCS-003B-device-v2-03-04-code-facts.md`。本文档状态保持 `blocked-human-confirmation`，不可直接作为开发、测试、上线、story 发布、数据库设计、API 契约或验收依据。
