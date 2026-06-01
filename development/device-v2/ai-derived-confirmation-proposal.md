# Device V2 当前代码事实与规划推导

| 项目 | 内容 |
| --- | --- |
| 文档状态 | `code-fact-and-planning-draft` |
| 适用范围 | Device V2 入库、Device V2 设备管理 |
| 使用限制 | 先记录当前真实代码，再给出 AI 规划建议；不得把 AI 建议当成已实现事实 |

> 本文目标是帮助人工和 AI 一起反向生产标准化工程文档。优先整理当前代码里的真实建模、真实逻辑、真实 API，再基于这些事实提出代码规划建议。

## 1. 当前真实代码范围

| 层次 | 真实代码位置 | 说明 |
| --- | --- | --- |
| 后端 Device V2 主模块 | `OneOPS/app/device/v2/**` | Device V2 主记录、导入批次、导入行、store task、observation、schema、change history、sync 等 |
| 后端 Device V2 ingest 模块 | `OneOPS/app/device/v2/ingest/**` | 另一套较新的 ingest task 框架，支持 JSON/Excel 任务提交、模板下载、任务查询 |
| 前端 API | `OneOPS-UI/src/api/device/device-v2.ts`、`device-v2-import.ts`、`device-v2-ingest.ts` | 前端实际调用的 Device V2、import batches、ingest task API |
| 前端页面 | `OneOPS-UI/src/views/device/DeviceV2Management*.vue`、`DeviceV2ImportBatches.vue`、`DeviceV2IngestPipelineRedesign.vue`、`device-v2-import/**` | 设备管理、导入批次、ingest 工作台相关页面 |

## 2. 当前真实后端建模

这一节是当前代码事实，不是 AI 推导。

| 真实模型 | 代码位置 | 数据表 | 真实含义 | 关键字段 |
| --- | --- | --- | --- | --- |
| `DeviceV2` | `OneOPS/app/device/v2/model/device_v2.go` | `platform_devices_v2` | Device V2 设备主记录，兼容现有数据表；使用动态 JSON 字段承载 labels、attributes、metadata、group tags | `id`、`code`、`type`、`name`、`platform_code`、`status`、`labels_json`、`attributes_json`、`metadata_json`、`group_tags_json` |
| `DeviceV2ImportBatch` | `OneOPS/app/device/v2/model/device_v2_import_batch.go` | `device_v2_import_batch` | 多次导入批次记录 | `batch_id`、`template_code`、`import_pass`、`namespace`、`mode`、`status`、`source_file`、`sheet`、`total`、`success`、`failed`、`skipped`、`validate_failed`、`apply_failed`、`message`、`created_by`、`options_json` |
| `DeviceV2ImportRecord` | `OneOPS/app/device/v2/model/device_v2_import_record.go` | `device_v2_import_record` | 导入批次中的行级记录 | `batch_id`、`row_no`、`namespace`、`entity_code`、`resolved_entity_id`、`match_mode`、`code_source`、`locator_trace`、`validate_status`、`apply_status`、`error_code`、`error_message`、`raw_payload_json`、`normalized_patch_json`、`applied_at` |
| `DeviceV2StoreRun` | `OneOPS/app/device/v2/model/device_v2_store_run.go` | `device_v2_store_run` | 一次 store pipeline task 中单台设备的执行结果 | `run_id`、`task_id`、`device_code`、`status`、`current_step`、`core_store_status`、`manageable_status`、`summary_json`、`finished_at` |
| `DeviceV2Observation` | `OneOPS/app/device/v2/model/device_v2_observation.go` | `device_v2_observation` | P0 阶段最小 observation 事实 | `observation_id`、`task_id`、`run_id`、`device_code`、`capability`、`field_key`、`status`、`value_json`、`raw_json`、`source`、`plane`、`collector_key`、`collected_at` |
| `DeviceV2IngestTask` | `OneOPS/app/device/v2/ingest/model/device_v2_ingest_task.go` | `device_v2_ingest_task` | 新 ingest task 框架的任务记录 | `task_id`、`status`、`framework_version`、`source`、`requested_by`、`execution_enabled`、`device_count`、`devices_json`、`result_json`、`stages_json` |

### 2.1 重要事实

- 当前真实设备主表不是简单固定字段模型，而是 `platform_devices_v2` + JSON 动态字段模型。
- `DeviceV2` 的 `lifecycle_stage`、`stage_status`、`manage_status`、`manageable` 不是表字段，代码从 `attributes` 中反解。
- 当前确实存在导入批次和导入行模型，分别是 `DeviceV2ImportBatch` 和 `DeviceV2ImportRecord`。
- 当前确实存在 store run 和 observation 模型，分别是 `DeviceV2StoreRun` 和 `DeviceV2Observation`。
- 当前不存在名为 `LatestDC2` 的独立模型；“最新 DC2”是通过最近的 `DeviceV2StoreRun.summary.device_collection2` 推导出来的接口视图。

## 3. 当前真实状态机

### 3.1 导入批次状态

来自 `OneOPS/app/device/v2/service/impl/device_v2_minimal_import.go`。

| 对象 | 状态 | 当前含义 |
| --- | --- | --- |
| 导入批次 | `created` | 批次已创建，或上传后处于待校验状态 |
| 导入批次 | `validated` | 行级校验完成 |
| 导入批次 | `applying` | 正在执行 apply |
| 导入批次 | `partial` | 部分成功、部分失败或跳过 |
| 导入批次 | `success` | 批次处理成功 |
| 导入批次 | `failed` | 批次处理失败 |

### 3.2 导入行状态

| 对象 | 状态字段 | 状态 | 当前含义 |
| --- | --- | --- | --- |
| 导入行 | `validate_status` | `pending` | 待校验 |
| 导入行 | `validate_status` | `ok` | 校验通过 |
| 导入行 | `validate_status` | `error` | 校验失败 |
| 导入行 | `apply_status` | `pending` | 待应用 |
| 导入行 | `apply_status` | `success` | 应用成功 |
| 导入行 | `apply_status` | `failed` | 应用失败 |
| 导入行 | `apply_status` | `skipped` | 应用跳过 |

### 3.3 store run 与 observation 状态

| 对象 | 状态字段 | 状态 |
| --- | --- | --- |
| store run | `status` | `pending`、`running`、`partial`、`success`、`failed`、`blocked` |
| store run | `core_store_status` | `pending`、`success`、`failed`、`blocked` |
| store run | `manageable_status` | `unknown`、`pending`、`ready`、`unready` |
| observation | `status` | `success`、`partial`、`failed`、`skipped` |

## 4. 当前真实导入逻辑

### 4.1 旧导入批次链路

真实入口：`OneOPS/app/device/v2/api/device_v2.go` + `OneOPS/app/device/v2/service/impl/device_v2_minimal_import.go`。

| 步骤 | 真实逻辑 |
| --- | --- |
| 创建批次 | `CreateImportBatch` 调用 `CreateBatch`，生成 `device-v2-import-<uuid>` 格式的 `batch_id`，写入 `device_v2_import_batch` |
| 上传记录 | `UploadImportBatch` 支持 JSON rows，也支持 multipart Excel；上传后删除旧 records，重建 `device_v2_import_record` |
| 校验批次 | `ValidateImportBatch` 调用 `ValidateBatch`，逐行更新 `validate_status`、`error_code`、`error_message` |
| 应用批次 | `ApplyImportBatch` 调用 `ApplyBatch`，把批次置为 `applying`，再逐行执行 apply |
| 重试批次 | `RetryImportBatch` 会把 scoped records 的 apply 状态重置，然后可选 revalidate，再按 `only_validated=true` apply |
| 更新行记录 | `UpdateImportBatchRecords` 修改 raw payload，并重置 validate/apply 状态 |
| 查询批次 | `ListImportBatches`、`GetImportBatchSummary`、`ListImportBatchRecords` 查询批次和行 |
| 清理批次 | `PurgeImportBatches` 用于清理历史导入批次视图 |

真实 import pass：

| import pass | 当前含义 |
| --- | --- |
| `pass_1_base` | 最小资产/基础设备信息 |
| `pass_2_access` | 接入端点信息 |
| `pass_3_credential` | 凭据绑定 |
| `pass_4_relation` | 设备关系 |

### 4.2 新 ingest task 链路

真实入口：`OneOPS/app/device/v2/ingest/api/device_v2_ingest.go` + `OneOPS/app/device/v2/ingest/service/impl/device_v2_ingest.go`。

| 步骤 | 真实逻辑 |
| --- | --- |
| 查询能力 | `Capabilities` 返回框架版本、是否启用执行、支持 source、支持 task status、默认 stages |
| 提交 JSON 任务 | `SubmitTask` 接收 `DeviceV2IngestSubmitReq`，走 source adapter、builder、validator、executor |
| 上传 Excel 任务 | `UploadTask` 接收表单字段 `excel`，解析后提交 ingest task |
| 下载模板 | `DownloadExcelTemplate` 返回 Excel 模板 |
| 查询任务 | `GetTask` 按 `task_id` 查询 `device_v2_ingest_task` |
| 最近任务 | `ListTasks` 查询最近 ingest task，limit 最大 20 |

真实 source：

| source | 当前含义 |
| --- | --- |
| `manual_api` | 手工 API JSON |
| `excel_upload` | Excel 上传 |
| `reference_payload` | 引用 payload |
| `future_pipeline` | 未来 pipeline payload |

真实 ingest task status：

| status | 当前含义 |
| --- | --- |
| `prepared` | 已准备 |
| `completed` | 已完成 |
| `failed` | 失败 |

## 5. 当前真实设备管理逻辑

真实入口：`OneOPS/app/device/v2/router/device_v2.go`、`OneOPS/app/device/v2/api/device_v2.go`、`OneOPS/app/device/v2/api/device_v2_store_minimal_api.go`。

| 能力 | 当前真实逻辑 |
| --- | --- |
| 列表 | `GET device/v2/list`，支持分页、codes、keyword、name、ip、label、attribute、manage_status、management_path、location、region、site、rack 等过滤 |
| 详情 | `GET device/v2/:code`，按 code 查询 Device V2 |
| 创建 | `POST device/v2?base_ref_mode=warn`，写入 Device V2，并记录 change history |
| 更新 | `PUT device/v2/:code?base_ref_mode=warn`，更新 name、platform_code、status、labels、attributes、metadata、group_tags |
| 删除 | `DELETE device/v2/:code`，如果注入了 RelationCleaner，会先清理关系，再删除设备 |
| 状态 | `GET device/v2/:code/status`，优先从 entity_v2 读取 lifecycle/stage/manage 状态 |
| store readiness | `GET device/v2/:code/store-readiness`，当前主要检查是否存在接入地址；缺失则 `blocked/missing_access_address` |
| store/start | `POST device/v2/store/start`，通过 entity_v2 pipeline 启动 `device_v2` 流水线 |
| store/retry | `POST device/v2/store/retry`，按 task/stage/codes 重试 entity_v2 pipeline |
| task summary | `GET device/v2/tasks/:taskId/summary`，汇总 pipeline task、store runs、observation 数量 |
| runs | `GET device/v2/tasks/:taskId/runs`，查询 `device_v2_store_run` |
| observations | `GET device/v2/tasks/:taskId/observations`，查询 `device_v2_observation` |
| collection plans | `GET device/v2/tasks/:taskId/collection-plans`，基于 runs 构造每台设备的下一步采集计划列表 |
| latest DC2 | `GET device/v2/:code/last-store-collection-dc2`，从最近 store run 的 summary 中寻找 `device_collection2.run_id` |
| change history | `GET device/v2/:code/change-history`、`POST device/v2/:code/change-history/:id/status` |
| V1 同步 | `POST device/v2/sync-from-v1`、`POST device/v2/sync-to-v1` |

## 6. 当前真实 API 清单

路径以下均为后端 router 中的相对路径；前端通常通过 `/api/v1` 前缀访问。

### 6.1 Device V2 管理 API

| 方法 | 路径 | 当前用途 |
| --- | --- | --- |
| `GET` | `device/v2/list` | 设备列表 |
| `POST` | `device/v2` | 创建设备 |
| `GET` | `device/v2/:code` | 查询设备详情 |
| `PUT` | `device/v2/:code` | 更新设备 |
| `DELETE` | `device/v2/:code` | 删除设备 |
| `GET` | `device/v2/:code/status` | 查询三阶段状态 |
| `GET` | `device/v2/:code/interfaces` | 查询设备接口镜像 |
| `GET` | `device/v2/:code/network-overview` | 查询网络概览 |
| `GET` | `device/v2/:code/store-readiness` | 查询 store readiness |
| `GET` | `device/v2/:code/last-store-collection-dc2` | 查询最近一次 DC2 采集结果引用 |

### 6.2 store/task API

| 方法 | 路径 | 当前用途 |
| --- | --- | --- |
| `POST` | `device/v2/store/start` | 启动 store pipeline |
| `POST` | `device/v2/store/retry` | 重试 store pipeline |
| `GET` | `device/v2/tasks/:taskId` | 查询 pipeline task |
| `GET` | `device/v2/tasks/:taskId/summary` | 查询 task summary |
| `GET` | `device/v2/tasks/:taskId/collection-plans` | 查询采集计划列表 |
| `GET` | `device/v2/tasks/:taskId/runs` | 查询 store runs |
| `GET` | `device/v2/tasks/:taskId/observations` | 查询 observations |

### 6.3 import batches API

| 方法 | 路径 | 当前用途 |
| --- | --- | --- |
| `POST` | `device/v2/import/batches` | 创建导入批次 |
| `POST` | `device/v2/import/batches/:batchId/upload` | 上传 JSON rows 或 Excel 文件 |
| `POST` | `device/v2/import/batches/:batchId/validate` | 校验批次 |
| `POST` | `device/v2/import/batches/:batchId/apply` | 应用批次 |
| `POST` | `device/v2/import/batches/:batchId/retry` | 重试批次 |
| `POST` | `device/v2/import/batches/:batchId/records/update` | 更新批次行 raw payload |
| `GET` | `device/v2/import/batches` | 查询导入批次列表 |
| `POST` | `device/v2/import/batches:purge` | 清理导入批次 |
| `GET` | `device/v2/import/batches/:batchId/summary` | 查询批次汇总 |
| `GET` | `device/v2/import/batches/:batchId/records` | 查询批次行 |
| `GET` | `device/v2/import/anchor-conflicts` | 查询锚点冲突 |
| `GET` | `device/v2/import/anchor-basis` | 查询当前锚点依据 |
| `GET` | `device/v2/import/templates/:importPass` | 查询导入模板 |

### 6.4 ingest task API

| 方法 | 路径 | 当前用途 |
| --- | --- | --- |
| `GET` | `device/v2/ingest/capabilities` | 查询 ingest 能力 |
| `GET` | `device/v2/ingest/template/excel` | 下载 ingest Excel 模板 |
| `GET` | `device/v2/ingest/tasks` | 查询最近 ingest tasks |
| `POST` | `device/v2/ingest/tasks` | 提交 JSON ingest task |
| `POST` | `device/v2/ingest/tasks/upload` | 上传 Excel ingest task |
| `GET` | `device/v2/ingest/tasks/:taskId` | 查询 ingest task |

## 7. 真实代码与原规划的差异

| 原先容易误解的说法 | 当前真实情况 | 对标准文档的影响 |
| --- | --- | --- |
| `Device` 是固定字段设备模型 | 当前真实主模型是 `DeviceV2`，字段中只有少量固定列，大量业务信息在 JSON attributes/labels/metadata 中 | 标准文档必须明确“固定字段”和“动态属性”的边界 |
| `ImportBatch/ImportRow` 只是 AI 推导 | 当前真实存在 `DeviceV2ImportBatch` 和 `DeviceV2ImportRecord` | 可以作为正式文档的代码事实基础 |
| `LatestDC2` 是模型 | 当前没有独立 `LatestDC2` 模型，只有 `last-store-collection-dc2` 接口视图 | 文档中应写“最新 DC2 查询视图”，不要写成数据表 |
| `StoreTask` 是独立模型 | 当前 store task 主要来自 entity_v2 pipeline task；Device V2 本地有 `DeviceV2StoreRun` 记录单设备 run | 文档应区分 pipeline task 与 store run |
| `warning` 行状态存在 | 当前导入行状态是 `validate_status=ok/error/pending`，没有真实 `warning` 状态 | 如果需要 warning，属于后续增强，不是当前事实 |
| readiness 检查 credential/protocol/port | 当前 `store-readiness` 主要检查接入地址是否存在 | 更完整 readiness 是规划缺口，不是现状 |

## 8. 基于真实代码的规划建议

### 8.1 入库方向

| 规划项 | 当前基础 | 建议 |
| --- | --- | --- |
| 行级校验语义 | 已有 `validate_status=pending/ok/error` | 若业务需要 warning/blocked/manual_review，应扩展真实状态机，而不是只写文档 |
| apply 范围 | 已支持 record_ids、row_nos、entity_codes、only_validated | 标准文档应明确默认 apply 是否只允许 `validate_status=ok` |
| import pass | 已有 `pass_1_base`、`pass_2_access`、`pass_3_credential`、`pass_4_relation` | 标准文档应分别描述四类导入，不要笼统写“Excel 入库” |
| 凭证引用 | 导入字段和 ingest 字段都支持 credential ref | 需要确认哪些字段只允许 ref，哪些页面可展示 ref/status |
| 批次清理 | 已有 `PurgeImportBatches` | 需要确认它是测试/回归工具，还是产品功能 |

### 8.2 设备管理方向

| 规划项 | 当前基础 | 建议 |
| --- | --- | --- |
| 清册列表 | 已有丰富过滤条件 | 标准文档应从真实 query 参数反推清册筛选能力 |
| 详情 | 已有按 code 查询 | 如果页面需要聚合接入、来源、采集状态，需要确认由前端拼装还是后端聚合 |
| store readiness | 已有最小检查：接入地址 | 需要增强为 credential、protocol、port、controller detect 等更完整规则 |
| store/start | 已接入 entity_v2 pipeline | 标准文档应明确 task、run、observation 三层关系 |
| latest DC2 | 已有接口视图 | 标准文档应定义 freshness 和成功标准 |
| 删除 | 已有 DELETE，会清关系后删设备 | 必须补“真实设备保护”和“克隆测试记录清理”边界 |

## 9. 建议下一批标准文档反推任务

| Story | 目标 | 输入代码 | 输出 |
| --- | --- | --- | --- |
| D2-DOC-REAL-MODEL-001 | 整理真实数据模型 | `model/*.go`、前端 typings | 真实模型章节 |
| D2-DOC-REAL-API-002 | 整理真实 API | `router/*.go`、`api/*.go`、前端 API TS | API 契约草案 |
| D2-DOC-REAL-FLOW-003 | 整理真实业务流程 | import service、ingest service、store API | 入库/管理真实流程图 |
| D2-DOC-GAP-004 | 对比真实代码与目标规划 | 本文第 7/8 节 | 差距清单与后续 story |

## 10. 需要人工确认的代码问题

这些问题直接影响代码和标准文档，不是文档流转问题。

1. Device V2 标准模型是否以 `platform_devices_v2` 固定列 + JSON attributes/labels/metadata 为核心表达？
2. `DeviceV2ImportBatch` / `DeviceV2ImportRecord` 是否作为正式入库批次模型，而不是临时实现？
3. `device_v2_ingest_task` 与 `device_v2_import_batch` 是并行两套入口，还是后续需要合并成一个主入口？
4. `pass_1_base` 到 `pass_4_relation` 是否是正式入库阶段划分？
5. 导入行是否需要新增 `warning` / `blocked` / `manual_review` 等状态？
6. `store-readiness` 是否需要从“检查接入地址”升级为“检查接入地址 + credential ref + protocol/port + controller detect”？
7. `last-store-collection-dc2` 的 freshness 和成功标准是什么？
8. `DELETE device/v2/:code` 是否允许用于正式产品删除？还是只能用于测试克隆清理？
9. 非 admin 权限是否需要在后端 API 层做硬校验，而不仅是前端按钮控制？
10. 当前 `PurgeImportBatches` 是否应保留为运维/测试能力，还是作为产品归档/清理功能暴露？

