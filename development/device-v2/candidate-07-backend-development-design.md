# 【后端开发设计】OneOPS_DeviceV2_V1.0

## 1. 文档信息

| 项目 | 内容 |
|------|------|
| 系统名称 | OneOPS |
| 模块名称 | Device V2 入库与设备管理 |
| 版本号 | V1.0 |
| 创建日期 | 2026-05-15 |
| 文档状态 | `blocked-human-confirmation` |
| 技术栈 | Go / Gin / GORM / Wire / MySQL `[当前源码事实]` |
| 关联文档 | 【需求概要】OneOPS_DeviceV2_V1.0.md<br>【数据库设计】OneOPS_DeviceV2_V1.0.md<br>【接口文档】OneOPS_DeviceV2_V1.0.md<br>`docs/openclaw-autodev/evidence/dev-docs/DEV-DOCS-003D-device-v2-07-code-facts.md` |

> 标准文档结构：本文使用 `docs/development-doc-templates/07-后端开发设计模板.md` 的章节顺序：文档信息、工程结构、分层职责、Controller 设计、Service 设计、数据访问设计、对象转换、事务/缓存/异常、文件输出清单、代码规范。模板原始示例偏 Java/Spring Boot；候选文档内容按当前 OneOPS Device V2 的 Go/Gin/GORM 真实代码填充，不生成 Java Controller/Service/Mapper 规划。
>
> 当前真实代码事实只表示已读取源码中的现状；AI 推导建议与规划缺口均不可直接作为产品需求、架构决策、API 契约、数据库字段、权限模型、fixture、性能目标、采集协议、删除策略或验收标准。

## 2. 工程结构

### 2.1 标准业务模块结构

候选文档内容：当前真实 Device V2 后端结构如下。

```text
OneOPS/app/device/v2/
├── api/
│   ├── device_v2.go
│   ├── device_v2_import_minimal_api.go
│   ├── device_v2_store_minimal_api.go
│   ├── device_v2_change_history.go
│   └── ...
├── dto/
│   ├── device_v2.go
│   ├── device_v2_import.go
│   ├── device_v2_schema.go
│   └── ...
├── model/
│   ├── device_v2.go
│   ├── device_v2_import_batch.go
│   ├── device_v2_import_record.go
│   ├── device_v2_store_run.go
│   ├── device_v2_observation.go
│   └── ...
├── router/
│   └── device_v2.go
└── service/
    ├── i_device_v2.go
    ├── i_device_v2_import.go
    ├── i_device_v2_schema.go
    └── impl/
        ├── device_v2.go
        ├── device_v2_minimal_read.go
        ├── device_v2_minimal_write.go
        ├── device_v2_minimal_import*.go
        ├── device_v2_minimal_store.go
        ├── device_v2_projection.go
        └── ...
```

入库新框架结构：

```text
OneOPS/app/device/v2/ingest/
├── api/device_v2_ingest.go
├── dto/device_v2_ingest.go
├── dto/device_v2_ingest_excel.go
├── model/device_v2_ingest_task.go
├── router/device_v2_ingest.go
└── service/
    ├── i_device_v2_ingest.go
    └── impl/
        ├── device_v2_ingest.go
        ├── device_v2_ingest_excel.go
        ├── device_v2_ingest_executor.go
        └── device_v2_ingest_pipeline.go
```

当前真实代码事实：`router/device_v2.go` 注册 `device/v2` 路由；`ingest/router/device_v2_ingest.go` 注册 `device/v2/ingest` 路由；服务实现主要集中在 `service/impl`，没有独立 Java/Spring 风格 controller/repository/mapper 包。

### 2.2 标准工具模块结构

当前 Device V2 不属于独立工具模块，暂无单独工具模块结构。可复用公共能力包括：

- `OneOPS/pkg/response`：统一响应封装，API handler 使用 `response.OkWithData` / `response.FailWithMsg`。
- `OneOPS/pkg/bind`：请求绑定。
- `OneOPS/app/common/excel`：Excel 导入服务。
- `OneOPS/dal/mysql`：GORM/gen 查询入口。
- `OneOPS/boot/provider/service_groups.go`：Wire provider 注册。

规划缺口：公共工具边界、是否抽 Repository 层、是否统一错误码/审计中间件仍为 `[待人工确认: 后端负责人]`。

## 3. 分层职责

| 层级 | 目录 | 职责 | 命名规范 |
|------|------|------|----------|
| Router | `router/`、`ingest/router/` | 注册 Gin 路由和 handler 映射 | `device_v2.go`、`device_v2_ingest.go` |
| API/Handler | `api/`、`ingest/api/` | HTTP 参数绑定、边界检查、响应封装、调用 Service | `DeviceV2API`、`DeviceV2IngestAPI` |
| DTO | `dto/`、`ingest/dto/` | 请求、响应、查询参数结构和 binding tags | `DeviceV2*Req/Resp` |
| Model | `model/`、`ingest/model/` | GORM 持久化模型、TableName、JSON 序列化钩子、状态常量 | `DeviceV2*` |
| Service 接口 | `service/`、`ingest/service/` | 定义业务能力边界 | `IDeviceV2*` |
| Service 实现 | `service/impl/`、`ingest/service/impl/` | 业务编排、校验、导入、store、projection、schema、GORM 访问 | `DeviceV2*` 或按能力拆分 |
| DI Provider | `boot/provider/`、各 `*Set` | Wire 注入服务集合 | `DeviceV2APISet`、`DeviceV2IngestSet` |

AI 推导建议：后续若补新能力，应优先保持 handler 薄、service 编排、model 只做持久化与序列化；但是否作为正式架构规范需 `[待人工确认: 架构/后端负责人]`。

## 4. Controller 设计

| Service 接口 | Controller | 根路径 | 说明 |
|--------------|------------|--------|------|
| `service.IDeviceV2` | `DeviceV2API` | `/device/v2` | 设备管理、列表、详情、创建、更新、删除、sync、schema |
| `service.IDeviceV2Import` | `DeviceV2API` | `/device/v2/import` | import batch 创建、上传、校验、应用、重试、记录查询 |
| `service.IDeviceV2Schema` | `DeviceV2API` | `/device/v2/schema` | schema current/precheck/save |
| `service.IDeviceInterfaceV2` | `DeviceV2API` | `/device/v2/{code}/interfaces` | 设备接口镜像查询 |
| `ingest/service.IDeviceV2Ingest` | `DeviceV2IngestAPI` | `/device/v2/ingest` | ingest capabilities、模板、任务提交/上传/查询 |
| Entity V2 pipeline service `[外部依赖]` | `DeviceV2API` | `/device/v2/store`、`/device/v2/tasks` | store pipeline 启动、重试、task 查询 |

### 4.1 方法映射规则

| 方法类型 | 命名特征 | HTTP 方法 | 示例 |
|----------|----------|-----------|------|
| 查询 | list/get/current/summary/runs/observations/capabilities | GET | `GET /device/v2/list`、`GET /device/v2/tasks/:taskId/summary` |
| 创建/提交 | create/submit/upload/start | POST | `POST /device/v2`、`POST /device/v2/ingest/tasks`、`POST /device/v2/store/start` |
| 更新/执行 | update/save/precheck/retry/sync | POST/PUT | `PUT /device/v2/:code`、`POST /device/v2/schema/precheck`、`POST /device/v2/store/retry` |
| 删除/清理 | delete/purge | DELETE/POST | `DELETE /device/v2/:code`、`POST /device/v2/import/batches:purge` |

当前真实代码事实：`router/device_v2.go` 中 `GET :code` 等动态路由位于 import、store、status、network 等固定路由之后；`ingest/router/device_v2_ingest.go` 使用 `/device/v2/ingest/tasks/upload` 上传 Excel。

### 4.2 响应封装

- API handler 使用 `response.OkWithData(data, ctx)` 返回成功数据。
- 失败使用 `response.FailWithMsg(msg, ctx)`。
- 当前响应 envelope 为 `{request_id, code, msg, data}`。
- 前端 `request<T>` 多数接口读取解包后的 `data`；`requestEnvelope<T>` 用于读取完整 envelope。

规划缺口：HTTP status 与业务 `code=-1` 的长期契约、统一错误码、权限失败返回格式仍为 `[待人工确认: 后端/安全负责人]`。

## 5. Service 设计

### 5.1 Service 接口清单

| 接口 | 方法 | 入参 | 返回值 | 说明 |
|------|------|------|--------|------|
| `IDeviceV2` | `GetSourceByCode` | `context.Context`、`code string` | `*entityv2model.EntityInstance`、`error` | 按 code 读取 Entity V2 主源 |
| `IDeviceV2` | `GetByCode` | `context.Context`、`code string` | `*model.DeviceV2`、`error` | 读取并投影为 DeviceV2 |
| `IDeviceV2` | `List` | `context.Context`、`codes []string`、`limit int` | `[]*model.DeviceV2`、`error` | code 列表查询，默认 limit 500 |
| `IDeviceV2` | `ListPage` | `context.Context`、`offset/limit`、`codes`、`*dto.DeviceV2Filter` | `[]*model.DeviceV2`、`total`、`error` | 分页与 label/attribute/location/manage 过滤 |
| `IDeviceV2` | `Create` | `context.Context`、`id/code/name/platformCode/status/labels/attributes/metadata/groupTags` | `*model.DeviceV2`、`error` | 事务写 EntityInstance、记录 change event、同步 projection |
| `IDeviceV2` | `Update` | `context.Context`、`code` 与更新字段 | `*model.DeviceV2`、`error` | 事务更新 EntityInstance、记录 change event、同步 projection |
| `IDeviceV2` | `DeleteByCode` | `context.Context`、`code string` | `error` | 删除 EntityInstance、projection、dead letter、可选 code registry，记录 delete event |
| `IDeviceV2Import` | `CreateBatch/UploadBatch/ValidateBatch/ApplyBatch/RetryBatch/UpdateBatchRecords` | import DTO | `*DeviceV2ImportBatch`、`error` | import batch 生命周期与记录更新 |
| `IDeviceV2Import` | `GetBatchByID/GetBatchSummary/ListBatches/ListBatchRecords/ListAnchorConflictRecords/GetAnchorBasis/PurgeBatches` | import query DTO | batch/record/list/map、`error` | 批次查询、记录查询、anchor basis、purge |
| `IDeviceV2Ingest` | `SubmitTask/SubmitExcelTask/DownloadExcelTemplate/ListTasks/GetTask` | ingest DTO、Excel file 或 task ID | ingest task / template bytes、`error` | 新入库框架任务、Excel 模板、任务查询 |

### 5.2 基础方法要求

候选文档内容：

- 查询类接口必须支持明确过滤条件和分页上限；当前 `ListPage` 默认 `limit=20`，`List` 默认 `limit=500`，ingest `ListTasks` 默认 `5`、最大 `20`。
- 写入类接口必须返回可追踪结果，至少包括 `code`、`batch_id`、`task_id`、`run_id` 或错误信息。
- store/import/ingest/sync 等异步或任务类能力必须保留 task/result/error evidence。
- 删除、purge、sync、store/start、ingest submit/upload 属于有副作用能力，权限、审计、二次确认和可回滚策略均需人工确认。

当前真实代码事实：`Create/Update/DeleteByCode` 使用 GORM transaction；`Start` store 任务会创建 `EntityPipelineTask`、`DeviceV2StoreRun`、`DeviceV2Observation`；ingest submit 当前同步执行 parse/build/validate/execute 后创建 `DeviceV2IngestTask`。

### 5.3 边界校验规则

| 数据类型 | 校验要求 | 示例 |
|----------|----------|------|
| 设备编码 | 非空、trim、去重 | `normalizeCodes`、`minimalNormalizeCodes` |
| JSON filter key | 只允许字母、数字、下划线 | `safeDeviceV2ListJSONFilterKey`、`safeJSONKey` |
| `label_value` | 必须同时有 `label_key` | `validateDeviceV2ListJSONFilter` |
| `attribute_value` | 必须同时有 `attribute_key` | `validateDeviceV2ListJSONFilter` |
| ingest identity | 至少有 `biz_code/sn/asset_number/in_band_ip/out_band_ip/hostname` 之一，内部链路也可附带 `code` | `defaultIngestValidator` |
| ingest status | 仅允许空、`active`、`inactive`、`planned`、`retired` | `allowedIngestStatuses` |
| IP 字段 | `in_band_ip`、`out_band_ip` 需可被 `net.ParseIP` 解析 | `defaultIngestValidator` |
| store run sort_by | 仅允许空、`created_at`、`priority` | `normalizeDeviceV2StoreRunSortBy` |
| observation sort_by | 仅允许空、`collected_at`、`priority` | `normalizeDeviceV2ObservationSortBy` |
| ingest task ID | 非空 | `DeviceV2IngestAPI.GetTask` |
| Excel 上传 | 表单字段必须是 `excel` | `DeviceV2IngestAPI.UploadTask` |

规划缺口：上述状态与校验仅为当前源码事实，是否成为长期业务规则需 `[待人工确认: 产品/后端负责人]`。

## 6. 数据访问设计

### 6.1 Mapper 方法清单

当前 Go/GORM 实现没有 Java MyBatis Mapper。候选映射如下：

| Mapper | 方法 | SQL 类型 | 说明 |
|--------|------|----------|------|
| GORM Model: `EntityInstance` | `Where(...).First/Create/Save/Delete/Find/Count` | SELECT/INSERT/UPDATE/DELETE | Device V2 读写主源，条件含 `entity_type=device_v2`、`entity_id` 与 JSON_EXTRACT |
| GORM Model: `DeviceV2` | `Create/Save/Delete/Find` | INSERT/UPDATE/SELECT/DELETE | `platform_devices_v2` projection/兼容表，主契约待确认 |
| GORM Model: `DeviceV2ImportBatch` | `Create/Update/Find/List` | INSERT/UPDATE/SELECT | 导入批次 |
| GORM Model: `DeviceV2ImportRecord` | `Create/Update/Find/List` | INSERT/UPDATE/SELECT | 导入记录、validate/apply 状态 |
| GORM Model: `DeviceV2IngestTask` | `Create/First/Find` | INSERT/SELECT | ingest 任务，`ListTasks` 限制最大 20 |
| GORM Model: `EntityPipelineTask` | `Create/First` | INSERT/SELECT | store pipeline task |
| GORM Model: `DeviceV2StoreRun` | `Create/Find` | INSERT/SELECT | store run |
| GORM Model: `DeviceV2Observation` | `Create/Find` | INSERT/SELECT | store observation |
| GORM Model: `DeviceV2ProjectionDeadLetter`、`DeviceV2CodeRegistry` | `Delete/Find/Save` | SELECT/UPDATE/DELETE | projection 同步失败记录和 code registry |

### 6.2 Repository 方法清单

当前代码主要通过 service impl + GORM DB/query 访问数据，未见独立 Repository 层。候选记录如下：

| Repository | 方法 | 调用 Mapper | 说明 |
|------------|------|-------------|------|
| `DeviceV2Srv` 实现 | `GetByCode/List/ListPage/Create/Update/DeleteByCode` | GORM `EntityInstance` + `DeviceV2` projection | 设备读写、投影和 change event |
| `DeviceV2MinimalImportSrv` 实现 | `CreateBatch/UploadBatch/ValidateBatch/ApplyBatch/RetryBatch/UpdateBatchRecords/List...` | GORM import batch/record | 导入批次和记录生命周期 |
| `DeviceV2IngestSrv` 实现 | `SubmitTask/SubmitExcelTask/ListTasks/GetTask` | GORM ingest task + executor | ingest task 与同步执行结果 |
| `DeviceV2MinimalStoreSrv` 实现 | `Start/Retry/loadTask/persistTaskBundle` | GORM EntityPipelineTask/store run/observation | store task、run、observation evidence |

AI 推导建议：如需长期维护，可评估把 EntityInstance 查询、import record flow、store bundle 持久化拆出 repository，但当前候选文档不得要求重构。

## 7. 对象转换

- Model 与 DTO 之间当前由 service/API 手工组装或通过 helper 处理。
- JSON 字段通过 GORM hooks 或 helper 在 `map/slice` 与 `*_json` 字符串之间转换。
- ingest payload 到 DeviceV2 的转换由 ingest pipeline、canonical builder、validator、executor 和 minimal shared helpers 处理。

| 转换方向 | 源对象 | 目标对象 | 白名单属性 | 说明 |
|----------|--------|----------|------------|------|
| API request -> DTO | JSON/query/form | `DeviceV2*Req` | DTO tags、query key、form field | Gin binding / helper parse |
| DTO -> Entity source | `DeviceV2CreateReq/UpdateReq` | `EntityInstance` | code/name/platform/status/labels/attributes/metadata/group_tags | `buildEntitySourceForWrite`，写前 base reference mode 支持 warn/strict |
| Entity source -> API response | `EntityInstance` | `DeviceV2` | entity_id/name/status/labels/attributes/metadata/group_tags | `entityToDeviceV2Projection` |
| Projection sync | `EntityInstance` | `platform_devices_v2` | projection fields | `syncDeviceV2ProjectionWithDeadLetter`，失败时返回 projection 但保留 dead letter |
| Import raw row -> record | `rows[] map[string]interface{}` | `DeviceV2ImportRecord` | raw_payload、normalized_patch、entity_code | upload 阶段生成 pending validate/apply |
| Import record -> ingest device | `NormalizedPatch` | `DeviceV2IngestDevice` | identity、平台、凭证、属性 | `minimalIngestDeviceFromNormalizedPatch` |
| Ingest submit -> task | `DeviceV2IngestSubmitReq` | `DeviceV2IngestTask` | source/requested_by/devices | parse/build/validate/execute 后保存 task |
| Ingest device -> DeviceV2 | `DeviceV2IngestDevice` | `EntityInstance`/`DeviceV2` | code/name/platform/status/credential/location/attrs | upsert executor 根据 code/registry/locator resolve existing device |
| Store run -> task evidence | `DeviceV2StoreRun` | task runs response | run/status/summary | store API 查询使用 runs 表 |
| Observation -> task evidence | `DeviceV2Observation` | observations response | capability/field/status/value/raw | store API 查询使用 observations 表 |

规划缺口：哪些字段可覆盖、哪些字段只能由权威来源写入、credential ref 与明文凭证处理边界仍需 `[待人工确认: 安全/后端负责人]`。

## 8. 事务、缓存与异常

| 场景 | 处理方式 | 备注 |
|------|----------|------|
| 创建 DeviceV2 | GORM transaction：查重 EntityInstance、创建 entity、记录 change event；commit 后同步 projection | `base_ref_mode` 支持 warn/strict；projection 同步失败会返回 entity projection 并记录 dead letter |
| 更新 DeviceV2 | GORM transaction：读取 entity、构建 next entity、`Save`、记录 change event；commit 后同步 projection | 具体字段 merge/覆盖规则待人工确认 |
| 删除 DeviceV2 | GORM transaction：删除 EntityInstance、`platform_devices_v2`、projection dead letter、可选 code registry，记录 delete event | clone cleanup 与原始记录删除边界需人工确认 |
| import batch upload/validate/apply/retry | service 编排记录 batch/record 状态；validate 检查重复 code/biz_code；apply 调用 minimal executor | 批量事务边界、部分成功策略、错误码需人工确认 |
| ingest task submit/upload | parse/build/validate/execute 后创建 task；Excel 上传使用 `SubmitExcelTask` | 当前为同步执行语义，是否长期保留需人工确认 |
| store/start/retry | `Start` 创建 EntityPipelineTask、runs、observations；失败数决定 task `success/partial/failed` | `async` 选项与真实异步/幂等/并发语义待确认 |
| 查询缓存 | 未在本轮源码确认 Device V2 专用缓存 | `[待确认]` |
| 业务异常 | handler 调用 `response.FailWithMsg`；service 返回 `error` | HTTP 状态、业务 code、错误码映射待确认 |

## 9. 文件输出清单

| 输出内容 | 文件命名 | 输出位置 |
|----------|----------|----------|
| Router | `device_v2.go` | `OneOPS/app/device/v2/router/` |
| API Handler | `device_v2*.go` | `OneOPS/app/device/v2/api/` |
| DTO | `device_v2*.go` | `OneOPS/app/device/v2/dto/` |
| Model | `device_v2*.go` | `OneOPS/app/device/v2/model/` |
| Service 接口 | `i_device_v2*.go` | `OneOPS/app/device/v2/service/` |
| Service 实现 | `device_v2*.go` | `OneOPS/app/device/v2/service/impl/` |
| Ingest Router/API/DTO/Model/Service | `device_v2_ingest*.go` | `OneOPS/app/device/v2/ingest/` |
| 前端 request wrapper `[当前真实代码事实]` | `device-v2.ts`、`device-v2-import.ts`、`device-v2-ingest.ts` | `OneOPS-UI/src/api/device/` |
| 前端页面/组件 `[当前真实代码事实]` | `DeviceV2Management.vue`、`DeviceV2ImportBatches.vue` | `OneOPS-UI/src/views/device/` |

## 10. 代码规范

- 使用当前项目 Go 代码风格，保持 `gofmt`。
- API handler 只做参数绑定、权限/边界检查候选、响应封装和服务调用，不承载复杂业务逻辑。
- Service impl 负责业务编排、状态转换、数据持久化和外部依赖调用。
- Model 层负责 GORM tags、TableName、JSON 字段序列化/反序列化。
- 新增写入或危险操作必须补充权限、审计、测试和人工确认边界。
- 新增接口需同步更新候选接口文档、前端 wrapper 和 read-only/write/task-trigger 副作用分类。

AI 推导建议：后续维护 07 文档时，应同步更新 05 数据库设计、06 接口文档和本文件的 source facts；但本候选稿仍保持 `blocked-human-confirmation`，不可直接用于开发或验收。
