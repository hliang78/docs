# 【数据库设计】OneOPS_DeviceV2_V1.0

## 1. 文档信息

| 项目 | 内容 |
|------|------|
| 系统名称 | OneOPS |
| 模块名称 | Device V2 入库与设备管理 |
| 版本号 | V1.0 |
| 创建日期 | 2026-05-15 |
| 文档状态 | `blocked-human-confirmation` |
| 数据库类型 | MySQL/GORM `[待确认: 后端负责人]` |
| 关联文档 | 【需求概要】OneOPS_DeviceV2_V1.0.md<br>【实体属性清单】OneOPS_DeviceV2_V1.0.md |
| 代码事实来源清单 | `docs/openclaw-autodev/evidence/dev-docs/DEV-DOCS-003C-device-v2-05-06-code-facts.md` |

> 候选稿边界：本文档按 `docs/development-doc-templates/05-数据库设计模板.md` 的标准文档结构整理；当前真实代码事实、AI 推导建议、规划缺口和未确认范围见代码事实来源清单。本文档为 `blocked-human-confirmation`，不可直接作为开发、迁移、数据库设计定稿或验收依据。

## 2. 设计原则

- 范式：本文档只记录当前代码中的真实表结构候选，不反向确认新的范式设计。
- 主键：当前模型包含 string 主键和 uint64 自增主键两类。
- 命名：当前真实表名使用小写字母加下划线。
- 时间字段：当前 Go/GORM 模型使用 `created_at`、`updated_at`，部分表使用 `finished_at`、`applied_at`、`collected_at`。
- 状态字段：多个表都有 `status` 或状态类字段，但含义不同，必须逐表定义。
- 软删除：当前本轮读取的核心模型未确认统一软删除字段；删除策略待确认。

## 3. 业务实体关系概览

### 3.1 核心实体识别

| 实体 | 表名 | 说明 |
|------|------|------|
| DeviceV2 | `platform_devices_v2` | Device V2 设备主记录，表名兼容现有数据 |
| DeviceV2ImportBatch | `device_v2_import_batch` | 多次导入批次 |
| DeviceV2ImportRecord | `device_v2_import_record` | 导入批次行记录 |
| DeviceV2IngestTask | `device_v2_ingest_task` | 新入库框架任务 |
| DeviceV2StoreRun | `device_v2_store_run` | store pipeline 单设备 run |
| DeviceV2Observation | `device_v2_observation` | store/采集 observation |

### 3.2 ER 关系说明

| 源实体 | 关系 | 目标实体 | 说明 |
|--------|------|----------|------|
| DeviceV2ImportBatch | 1:N | DeviceV2ImportRecord | 通过 `batch_id` 逻辑关联 |
| DeviceV2IngestTask | 1:N | DeviceV2IngestDevice | `devices_json` 中保存任务设备载荷 |
| DeviceV2IngestTask | 1:N | TaskStage | `stages_json` 中保存任务阶段 |
| DeviceV2StoreRun | N:1 | DeviceV2 | 通过 `device_code` 逻辑关联 |
| DeviceV2Observation | N:1 | DeviceV2StoreRun | 通过 `run_id` 逻辑关联 |
| DeviceV2Observation | N:1 | DeviceV2 | 通过 `device_code` 逻辑关联 |

## 4. 数据表清单

### 4.1 表结构总览

| 序号 | 表名 | 中文名称 | 说明 |
|------|------|----------|------|
| 1 | `platform_devices_v2` | Device V2 设备主表 | 设备主记录和动态字段 JSON |
| 2 | `device_v2_import_batch` | 导入批次表 | import batch 状态、统计、来源 |
| 3 | `device_v2_import_record` | 导入记录表 | import batch 行级记录 |
| 4 | `device_v2_ingest_task` | ingest 任务表 | 新入库任务和任务载荷 |
| 5 | `device_v2_store_run` | store run 表 | store pipeline 单设备执行结果 |
| 6 | `device_v2_observation` | observation 表 | store/采集字段级观测事实 |

### 4.2 详细表结构

#### 4.2.1 platform_devices_v2（Device V2 设备主表）

**表说明**：保存 Device V2 设备主记录，包含业务唯一 code、平台、状态、动态字段 JSON 和审计时间。

| 字段名 | 数据类型 | 长度 | 允许空 | 默认值 | 约束 | 注释 |
|--------|----------|------|--------|--------|------|------|
| id | varchar | 128 | 否 | - | PRIMARY KEY | 主键，可与 Code 一致 |
| code | varchar | 64 | 否 | - | UNIQUE INDEX | 设备编码业务唯一 |
| type | varchar | 32 | 是 | device_v2 | - | 实体类型 |
| name | varchar | 255 | 是 | - | - | 名称 |
| platform_code | varchar | 64 | 是 | - | INDEX | 平台编码 |
| status | varchar | 32 | 是 | - | - | 状态 |
| labels_json | longtext | - | 是 | {} | - | 标签 JSON |
| attributes_json | longtext | - | 是 | {} | - | 属性 JSON |
| metadata_json | longtext | - | 是 | {} | - | 元数据 JSON |
| group_tags_json | longtext | - | 是 | [] | - | 分组标签 JSON |
| created_at | datetime | - | 否 | 当前时间 | - | 创建时间 |
| updated_at | datetime | - | 否 | 当前时间 | - | 更新时间 |

**索引设计**：

| 索引名 | 索引类型 | 字段 | 说明 |
|--------|----------|------|------|
| uniqueIndex | 唯一索引 | code | 设备业务编码唯一 |
| index | 普通索引 | platform_code | 平台过滤 |

**关联关系**：

| 关联表 | 关联字段 | 关系类型 | 说明 |
|--------|----------|----------|------|
| device_v2_store_run | device_code | 一对多 | 逻辑关联设备 store runs |
| device_v2_observation | device_code | 一对多 | 逻辑关联 observation |

#### 4.2.2 device_v2_import_batch（导入批次表）

**表说明**：保存 import batch 的批次状态、统计、来源和选项。

| 字段名 | 数据类型 | 长度 | 允许空 | 默认值 | 约束 | 注释 |
|--------|----------|------|--------|--------|------|------|
| id | bigint unsigned | - | 否 | auto | PRIMARY KEY | 自增主键 |
| batch_id | varchar | 64 | 否 | - | UNIQUE INDEX | 批次业务 ID |
| template_code | varchar | 128 | 是 | - | INDEX | 模板编码 |
| import_pass | varchar | 64 | 否 | - | INDEX | 导入 pass |
| namespace | varchar | 128 | 是 | infra/device | INDEX | 命名空间 |
| mode | varchar | 32 | 否 | apply | - | 模式 |
| status | varchar | 32 | 否 | created | INDEX | 批次状态 |
| source_file | varchar | 255 | 是 | - | - | 来源文件 |
| sheet | varchar | 128 | 是 | - | - | Sheet |
| total/success/failed/skipped | int | - | 否 | 0 | - | 数量统计 |
| validate_failed/apply_failed/project_failed | int | - | 否 | 0 | - | 失败统计 |
| auto_code_count/auto_generated_ratio | int | - | 否 | 0 | - | 自动编码统计 |
| ambiguous_count/not_found_count | int | - | 否 | 0 | - | 锚点解析统计 |
| dominant_code_source | varchar | 64 | 是 | "" | - | 主导编码来源 |
| dominant_code_ratio | int | - | 否 | 0 | - | 主导编码比例 |
| message | varchar | 1024 | 是 | "" | - | 消息 |
| created_by | varchar | 128 | 是 | - | - | 创建人 |
| options_json | longtext | - | 是 | {} | - | 选项 JSON |
| code_source_stats_json | longtext | - | 是 | {} | - | 编码来源统计 JSON |
| created_at/updated_at | datetime | - | 否 | 当前时间 | - | 时间字段 |

**索引设计**：

| 索引名 | 索引类型 | 字段 | 说明 |
|--------|----------|------|------|
| uniqueIndex | 唯一索引 | batch_id | 批次 ID 唯一 |
| index | 普通索引 | template_code/import_pass/namespace/status | 查询过滤 |

**关联关系**：

| 关联表 | 关联字段 | 关系类型 | 说明 |
|--------|----------|----------|------|
| device_v2_import_record | batch_id | 一对多 | 一个批次包含多条记录 |

#### 4.2.3 device_v2_import_record（导入记录表）

**表说明**：保存 import batch 中每一行的原始载荷、标准化 patch、校验/应用状态和错误信息。

| 字段名 | 数据类型 | 长度 | 允许空 | 默认值 | 约束 | 注释 |
|--------|----------|------|--------|--------|------|------|
| id | bigint unsigned | - | 否 | auto | PRIMARY KEY | 自增主键 |
| batch_id | varchar | 64 | 否 | - | INDEX | 批次 ID |
| row_no | int | - | 否 | 0 | INDEX | 行号 |
| namespace | varchar | 128 | 是 | infra/device | INDEX | 命名空间 |
| entity_code | varchar | 128 | 是 | - | INDEX | 实体编码 |
| resolved_entity_id | varchar | 128 | 是 | - | INDEX | 解析实体 ID |
| match_mode | varchar | 32 | 是 | - | INDEX | 匹配模式 |
| code_source | varchar | 64 | 是 | - | INDEX | 编码来源 |
| locator_trace | varchar | 1024 | 是 | - | - | 定位追踪 |
| validate_status | varchar | 32 | 否 | pending | INDEX | 校验状态 |
| apply_status | varchar | 32 | 否 | pending | INDEX | 应用状态 |
| error_code | varchar | 64 | 是 | - | - | 错误码 |
| error_message | text | - | 是 | - | - | 错误信息 |
| conflict_candidates_json | longtext | - | 是 | [] | - | 冲突候选 |
| raw_payload_json | longtext | - | 是 | {} | - | 原始载荷 |
| normalized_patch_json | longtext | - | 是 | {} | - | 标准化 patch |
| applied_at | datetime | - | 是 | - | - | 应用时间 |
| created_at/updated_at | datetime | - | 否 | 当前时间 | - | 时间字段 |

**索引设计**：

| 索引名 | 索引类型 | 字段 | 说明 |
|--------|----------|------|------|
| index | 普通索引 | batch_id,row_no,namespace,entity_code,resolved_entity_id,match_mode,code_source,validate_status,apply_status | 查询、筛选和追踪 |

**关联关系**：

| 关联表 | 关联字段 | 关系类型 | 说明 |
|--------|----------|----------|------|
| device_v2_import_batch | batch_id | 多对一 | 逻辑关联所属批次 |

#### 4.2.4 device_v2_ingest_task（ingest 任务表）

**表说明**：保存 Device V2 新入库框架任务和任务载荷。

| 字段名 | 数据类型 | 长度 | 允许空 | 默认值 | 约束 | 注释 |
|--------|----------|------|--------|--------|------|------|
| task_id | varchar | 64 | 否 | - | PRIMARY KEY | 任务 ID |
| status | varchar | 32 | 否 | - | INDEX | 任务状态 |
| framework_version | varchar | 32 | 否 | - | - | 框架版本 |
| source | varchar | 64 | 否 | - | INDEX | 来源 |
| requested_by | varchar | 128 | 是 | - | - | 请求人 |
| execution_enabled | bool | - | 否 | false | - | 是否启用执行 |
| device_count | int | - | 否 | 0 | - | 设备数量 |
| message | varchar | 1024 | 是 | - | - | 消息 |
| devices_json | longtext | - | 是 | [] | - | 设备载荷 JSON |
| result_json | longtext | - | 是 | {} | - | 结果 JSON |
| stages_json | longtext | - | 是 | [] | - | 阶段 JSON |
| created_at/updated_at | datetime | - | 否 | 当前时间 | - | 时间字段 |

**索引设计**：

| 索引名 | 索引类型 | 字段 | 说明 |
|--------|----------|------|------|
| primaryKey | 主键 | task_id | 任务 ID 唯一 |
| index | 普通索引 | status,source | 状态和来源过滤 |

**关联关系**：

| 关联表 | 关联字段 | 关系类型 | 说明 |
|--------|----------|----------|------|
| 无独立子表 | devices_json/stages_json | 嵌套关系 | 设备载荷和阶段以 JSON 保存 |

#### 4.2.5 device_v2_store_run（store run 表）

**表说明**：保存 store pipeline 中单台设备的执行结果。

| 字段名 | 数据类型 | 长度 | 允许空 | 默认值 | 约束 | 注释 |
|--------|----------|------|--------|--------|------|------|
| run_id | varchar | 64 | 否 | - | PRIMARY KEY | run ID |
| task_id | varchar | 64 | 否 | - | INDEX | task ID |
| device_code | varchar | 128 | 否 | - | INDEX | 设备编码 |
| status | varchar | 32 | 否 | pending | INDEX | run 状态 |
| current_step | varchar | 64 | 是 | "" | - | 当前步骤 |
| core_store_status | varchar | 32 | 否 | pending | INDEX | core store 状态 |
| manageable_status | varchar | 32 | 否 | unknown | INDEX | 可纳管状态 |
| summary_json | longtext | - | 是 | {} | - | 摘要 JSON |
| created_at/updated_at | datetime | - | 否 | 当前时间 | - | 时间字段 |
| finished_at | datetime | - | 是 | - | - | 完成时间 |

**索引设计**：

| 索引名 | 索引类型 | 字段 | 说明 |
|--------|----------|------|------|
| primaryKey | 主键 | run_id | run 唯一 |
| index | 普通索引 | task_id,device_code,status,core_store_status,manageable_status | 查询过滤 |

**关联关系**：

| 关联表 | 关联字段 | 关系类型 | 说明 |
|--------|----------|----------|------|
| platform_devices_v2 | device_code/code | 多对一 | 逻辑关联设备 |
| device_v2_observation | run_id | 一对多 | 逻辑关联 observations |

#### 4.2.6 device_v2_observation（observation 表）

**表说明**：保存 store/采集过程中产生的字段级观测事实。

| 字段名 | 数据类型 | 长度 | 允许空 | 默认值 | 约束 | 注释 |
|--------|----------|------|--------|--------|------|------|
| observation_id | varchar | 64 | 否 | - | PRIMARY KEY | observation ID |
| task_id | varchar | 64 | 否 | - | INDEX | task ID |
| run_id | varchar | 64 | 否 | - | INDEX | run ID |
| device_code | varchar | 128 | 否 | - | INDEX | 设备编码 |
| capability | varchar | 64 | 否 | - | INDEX | capability |
| field_key | varchar | 128 | 否 | - | INDEX | 字段 key |
| status | varchar | 32 | 否 | success | INDEX | observation 状态 |
| value_json | longtext | - | 是 | {} | - | 值 JSON |
| raw_json | longtext | - | 是 | {} | - | 原始 JSON |
| source | varchar | 64 | 是 | "" | - | 来源 |
| plane | varchar | 32 | 是 | "" | - | 接入面 |
| collector_key | varchar | 64 | 是 | "" | - | 采集器 |
| error_message | text | - | 是 | - | - | 错误信息 |
| collected_at/created_at/updated_at | datetime | - | 否 | 当前时间 | - | 时间字段 |

**索引设计**：

| 索引名 | 索引类型 | 字段 | 说明 |
|--------|----------|------|------|
| primaryKey | 主键 | observation_id | observation 唯一 |
| index | 普通索引 | task_id,run_id,device_code,capability,field_key,status | 查询过滤 |

**关联关系**：

| 关联表 | 关联字段 | 关系类型 | 说明 |
|--------|----------|----------|------|
| device_v2_store_run | run_id | 多对一 | 逻辑关联 run |
| platform_devices_v2 | device_code/code | 多对一 | 逻辑关联设备 |

## 5. 数据字典

| 枚举名称 | 取值 | 含义 | 所属表/字段 |
|----------|------|------|-------------|
| StoreRunStatus | pending/running/partial/success/failed/blocked | store run 状态 | device_v2_store_run.status |
| CoreStoreStatus | pending/success/failed/blocked | core store 状态 | device_v2_store_run.core_store_status |
| ManageableStatus | unknown/pending/ready/unready | 可纳管状态 | device_v2_store_run.manageable_status |
| ObservationStatus | success/partial/failed/skipped | observation 状态 | device_v2_observation.status |
| IngestTaskStatus | prepared/completed/failed | ingest task 状态 | device_v2_ingest_task.status |
| IngestSource | manual_api/excel_upload/reference_payload/future_pipeline | ingest 来源 | device_v2_ingest_task.source |
| DeviceV2Status | `[待确认]` | 设备状态 | platform_devices_v2.status |
| ImportBatchStatus | `[待确认]` | 导入批次状态 | device_v2_import_batch.status |
| ImportRecordStatus | pending 等 `[待确认]` | 校验/应用状态 | device_v2_import_record.validate_status/apply_status |

## 6. 关键业务规则的数据支撑

| 业务规则 | 数据库实现方式 |
|----------|----------------|
| 设备编码唯一 | `platform_devices_v2.code` 唯一索引 |
| 导入批次可追踪 | `device_v2_import_batch.batch_id` 唯一索引，批次统计字段记录结果 |
| 导入行级错误可追踪 | `device_v2_import_record` 保存 `row_no`、`error_code`、`error_message`、`raw_payload_json`、`normalized_patch_json` |
| ingest task 可复盘 | `device_v2_ingest_task` 保存 `devices_json`、`result_json`、`stages_json` |
| store run 可定位失败 | `device_v2_store_run` 保存 `status/core_store_status/manageable_status/summary_json` |
| observation 可查询字段级证据 | `device_v2_observation` 保存 `capability/field_key/status/value_json/raw_json` |

## 7. 数据量预估与扩展性说明

### 7.1 数据量预估

| 表名 | 预估日增 | 预估总量 | 增长趋势 |
|------|----------|----------|----------|
| platform_devices_v2 | `[待确认]` | `[待确认]` | 随设备资产规模增长 |
| device_v2_import_batch | `[待确认]` | `[待确认]` | 随导入频率增长 |
| device_v2_import_record | `[待确认]` | `[待确认]` | 与导入文件行数相关 |
| device_v2_ingest_task | `[待确认]` | `[待确认]` | 与入库任务数量相关 |
| device_v2_store_run | `[待确认]` | `[待确认]` | 与 store task 和设备数量相关 |
| device_v2_observation | `[待确认]` | `[待确认]` | 可能增长较快，需归档策略 |

### 7.2 扩展性设计

- 分表策略：`[待确认]`，尤其是 observation 和 import record。
- 历史数据归档策略：`[待确认]`。
- 预留字段：大量 JSON 字段已存在，但 JSON 字段治理规则和索引策略待确认。

## 8. 待确认事项

| 序号 | 待确认内容 | 影响表/字段 | 状态 |
|------|------------|-------------|------|
| 1 | 是否为核心表补充外键或保持逻辑关联 | 多表关系 | 待确认 |
| 2 | observation/import record 的归档和清理策略 | device_v2_observation、device_v2_import_record | 待确认 |
| 3 | `status` 类字段正式枚举和迁移兼容 | 多表 status 字段 | 待确认 |
| 4 | JSON 字段是否需要虚拟列或索引 | labels/attributes/metadata/value/raw | 待确认 |
| 5 | 删除策略是否需要软删除字段 | platform_devices_v2 等 | 待确认 |
| 6 | `platform_devices_v2` 与 `entity_v2` 源表/投影关系如何定稿 | DeviceV2 主源、projection、同步/删除策略 | 待人工确认 |
| 7 | change history、schema、interface、projection、dead letter、import apply log 等已发现模型是否纳入完整数据库设计 | Device V2 完整表清单 | 待人工确认 |

