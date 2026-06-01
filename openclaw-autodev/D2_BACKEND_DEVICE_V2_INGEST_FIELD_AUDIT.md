# D2 后端 Device V2 入库字段审计

更新时间：2026-05-13

文档角色：辅助文档。字段主表请以 `/Users/huangliang/project/OneOPS-ALL/docs/openclaw-autodev/D2_INGEST_BASE_FIELD_TABLE.md` 为准；本文用于追溯后端代码、字段来源和审计细节。

目标：按后端真实代码提取 Device V2 入库过程中的所有字段、字段来源、字段处理、字段去处和关键边界。本文不以 UI 或旧总结为准，只以后端代码为准。

## 0. 总体结论

D2 后端入库不是一个单点接口，而是三条相关链路：

1. `ingest` 主链路：`/api/v1/device/v2/ingest/**`，当前 redesign 入库工作台主要使用它。
2. `import/batches` 批次链路：`/api/v1/device/v2/import/**`，偏批次导入、校验、应用、重试、清理。
3. `store/collection` 链路：围绕 store run、采集计划、可纳管状态、采集缺口诊断。

本轮先审计第 1 条 `ingest` 主链路，并标出它如何进入 Device V2 写库逻辑。后续继续展开第 2、3 条。

主链路真实过程：

```text
HTTP API
  -> SubmitTask / SubmitExcelTask
  -> sourceAdapter.Parse
  -> defaultCanonicalBuilder.Build
  -> defaultIngestValidator.Validate
  -> deviceV2UpsertExecutor.Execute
  -> DeviceV2Srv.Create / Update
  -> entity_instance + device_v2 projection + code registry
  -> device_v2_ingest_task 持久化 task/devices/result/stages
```

关键修正：

- Excel 模板真实字段不止 `code/name/platform/status`，还包含 `biz_code`、`biz_name`、IP、凭据、租户、区域、机房、机柜、主机名、资产编号、平台、状态、设备类型、厂商、型号、SN、备注。
- Excel 中 `platform_code` 是 header alias，会映射到 `platform`；模板主列叫 `platform`。
- 类别/catalog 不是顶层 ingest struct 字段，而是进入 `attributes` 后被 `resolveImportedCatalogRef` 解析。
- 设备类型相关字段当前分裂为 `device_kind`、`device_type`、`device_model`、`model`，其中新 ingest Excel 模板放的是 `device_kind/vendor/model`，旧 import/batches 里有 `device_kind/device_model/device_type`。
- `management_path/org_path` 在 ingest Excel alias 中存在兼容，但注释明确：入库阶段不再使用。

## 1. 总体文件

### 1.1 ingest 主链路文件

| 文件 | 作用 |
| --- | --- |
| `/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device/v2/ingest/router/device_v2_ingest.go` | 注册 ingest 路由 |
| `/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device/v2/ingest/api/device_v2_ingest.go` | HTTP API：capabilities、submit、upload、template、task list/detail |
| `/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device/v2/ingest/dto/device_v2_ingest.go` | submit/capability DTO |
| `/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device/v2/ingest/dto/device_v2_ingest_excel.go` | Excel 模板字段、别名、sheet |
| `/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device/v2/ingest/model/device_v2_ingest_task.go` | ingest task 表模型、task/device/stage 枚举 |
| `/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device/v2/ingest/service/impl/device_v2_ingest.go` | SubmitTask 主流程 |
| `/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device/v2/ingest/service/impl/device_v2_ingest_excel.go` | Excel 解析和 Excel row -> ingest device |
| `/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device/v2/ingest/service/impl/device_v2_ingest_pipeline.go` | source parse、canonical build、validate、task result/stages |
| `/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device/v2/ingest/service/impl/device_v2_ingest_executor.go` | 查重匹配、platform/catalog/location 解析、upsert 执行 |

### 1.2 写库与纳管相关文件

| 文件 | 作用 |
| --- | --- |
| `/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device/v2/service/impl/device_v2_minimal_write.go` | DeviceV2Srv Create/Update |
| `/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device/v2/service/impl/device_v2_minimal_attributes.go` | attributes 归一化、access_points、credential_refs、manageable |
| `/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device/v2/service/impl/device_v2_minimal_base_validation.go` | base 主数据引用校验 |
| `/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device/v2/model/device_v2.go` | DeviceV2 projection 模型 |
| `/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device/v2/model/device_v2_code_registry.go` | code registry |

### 1.3 import/batches 与采集相关文件，下一轮展开

| 文件 | 作用 |
| --- | --- |
| `/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device/v2/dto/device_v2_import.go` | 批次导入 DTO 和多 pass Excel 行结构 |
| `/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device/v2/model/device_v2_import_batch.go` | 导入批次模型 |
| `/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device/v2/model/device_v2_import_record.go` | 导入记录模型 |
| `/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device/v2/service/impl/device_v2_minimal_import*.go` | 批次导入、校验、应用、重试 |
| `/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device/v2/api/device_v2_store_minimal_api.go` | store task/run/collection 相关 API |
| `/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device/v2/model/device_v2_store_run.go` | store run 模型和 manageable_status |

## 2. API 层字段

### 2.1 Capabilities

Endpoint：`GET /api/v1/device/v2/ingest/capabilities`

响应字段：

| 字段 | 类型 | 来源代码 | 真实值/处理 | 去处 |
| --- | --- | --- | --- | --- |
| `framework_version` | string | `model.FrameworkVersionV0Minimal` | 固定 `v0-minimal` | FE 展示当前框架版本 |
| `execution_enabled` | bool | API 层硬编码 | 当前返回 `true` | FE 判断是否可真实执行 |
| `supported_sources` | []string | `model.SupportedSources` | `manual_api/excel_upload/reference_payload/future_pipeline` | FE 或调用方选择 submit source |
| `task_statuses` | []string | `model.SupportedTaskStatuses` | `prepared/completed/failed` | FE 状态展示 |
| `default_stages` | []string | `model.DefaultTaskStages` | `request_received/canonical_device_payload/validator_slot/execution_adapter` | FE 阶段展示 |

边界：

- `execution_enabled` 在 capability API 中固定返回 true；实际 task 中的 `execution_enabled` 还要看 executor 是否真实启用。

### 2.2 SubmitTask

Endpoint：`POST /api/v1/device/v2/ingest/tasks`

请求字段：

| 字段 | 类型 | 来源 | 处理 | 边界 |
| --- | --- | --- | --- | --- |
| `source` | string | JSON body | trim 后必须在 supported sources 内 | 非法返回 `source 非法` |
| `requested_by` | string | JSON body | trim；进入 source snapshot 和 task | 可空 |
| `devices` | []DeviceV2IngestDevice | JSON body | parse -> normalize -> build -> validate -> execute | 空返回 `devices 不能为空` |

### 2.3 UploadTask

Endpoint：`POST /api/v1/device/v2/ingest/tasks/upload`

请求字段：

| 字段 | 类型 | 来源 | 处理 | 边界 |
| --- | --- | --- | --- | --- |
| multipart `excel` | file | form-data | `ctx.FormFile("excel")` 后用 `xlsx.OpenReaderAt` 解析 | 字段缺失返回 `导入文件不能为空（表单字段: excel）` |
| `requested_by` | string | form field | trim 后透传到 SubmitExcelTask | 可空 |
| `filename` | string | uploaded file header | 传入 SubmitExcelTask，但当前没有写入 task 字段 | 仅上下文信息 |
| `size` | int64 | uploaded file header | 必须 > 0 | 空文件返回 `导入文件不能为空` |

边界：

- 代码没有通过扩展名判断 `.xlsx`，而是直接用 xlsx parser；非 xlsx 会解析失败。
- 生产 UI 目前应限制 `.xlsx`，但后端真实边界是“能被 xlsx parser 打开”。

### 2.4 Template

Endpoint：`GET /api/v1/device/v2/ingest/template/excel`

响应：

| 字段/信息 | 真实值 |
| --- | --- |
| filename | `device_v2_ingest_template.xlsx` |
| sheet | `devices` |
| content-type | `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` |

## 3. Excel 字段

### 3.1 模板真实 headers

这些字段来自 `DeviceV2IngestExcelHeaders`：

| Excel 字段 | 进入哪里 | 处理 |
| --- | --- | --- |
| `biz_code` | top-level `BizCode` | trim |
| `biz_name` | top-level `Name` | trim |
| `in_band_ip` | `attributes.in_band_ip` | trim，后续校验 IP |
| `credential_ref_in_band` | top-level `CredentialRefInBand` | trim，后续也写入 attributes |
| `winrm_credential_ref` | top-level `WinRMCredentialRef` | trim，后续也写入 attributes |
| `winrm_port` | top-level `WinRMPort` | `strconv.Atoi`，失败为 0 |
| `out_band_ip` | `attributes.out_band_ip` | trim，后续校验 IP |
| `credential_ref_out_band` | top-level `CredentialRefOutBand` | trim，后续也写入 attributes |
| `tenant_name` | `attributes.tenant_name` | trim；当前 ingest 主链路未解析成 `tenant_code` |
| `region_name` | `attributes.region_name` | 后续匹配 region 主数据 |
| `site_name` | `attributes.site_name` | 后续匹配 site 主数据 |
| `rack_name` | `attributes.rack_name` | 后续匹配 rack 主数据 |
| `rack_position` | top-level `RackPosition` | trim，后续写 `rack_position` 和 `frame` |
| `hostname` | `attributes.hostname` | 可作为定位字段 |
| `asset_number` | `attributes.asset_number` | 可作为定位字段 |
| `platform` | top-level `Platform` | 可按 platform code 或 name 匹配主数据 |
| `status` | top-level `Status` | 后续 lower；只允许空/active/inactive/planned/retired |
| `device_kind` | `attributes.device_kind` | 当前未转 catalog，仅作为属性保留 |
| `vendor` | `attributes.vendor` | 当前仅作为属性保留 |
| `model` | `attributes.model` | 当前仅作为属性保留；不是 `device_model_code` |
| `sn` | `attributes.sn` | 可作为定位字段 |
| `remark` | `attributes.remark` | 当前仅作为属性保留 |

### 3.2 Excel header aliases

这些别名先归一化 header，再进入对应字段：

| 输入 header | 归一到 | 关键影响 |
| --- | --- | --- |
| `platform_code` | `platform` | Excel 里的 `platform_code` 会被当作 `platform`，再按平台 code/name 解析 |
| `tenant_code` | `tenant_name` | 进入 `attributes.tenant_name`，主 ingest 链路当前不解析 tenant_code |
| `region_code` | `region_name` | 进入 `attributes.region_name`，仍可按 code/name 匹配 region |
| `site_code` | `site_name` | 进入 `attributes.site_name`，仍可按 code/name 匹配 site |
| `rack_code` | `rack_name` | 进入 `attributes.rack_name`，仍可按 code/name 匹配 rack |
| `org_path` | `management_path` | 兼容旧输入，但入库阶段不再使用 |
| `name` | `biz_name` | 设备名进入 top-level `Name` |

重要边界：

- `platform_code` 在 Excel 主链路不是最终字段名，只是 `platform` 的别名。
- `management_path` 属于 top-level headers 的兼容项，但注释明确“入库阶段不再使用”。

### 3.3 Excel 必须至少有一个定位列头

解析 Excel 时只检查 header 是否存在至少一个，不是检查每行值：

- `biz_code`
- `sn`
- `asset_number`
- `in_band_ip`
- `out_band_ip`
- `hostname`

如果这些 header 一个都没有：报错 `Excel 至少需要一个定位列头: biz_code/sn/asset_number/in_band_ip/out_band_ip/hostname`。

后续每行真实身份值由 validator 再检查。

## 4. DeviceV2IngestDevice 字段

这是 JSON submit 和 Excel 解析后进入 pipeline 的核心结构。

| 字段 | JSON 名 | 来源 | 处理 | 去处 |
| --- | --- | --- | --- | --- |
| `Code` | `code` | JSON 可传；Excel 当前模板无 `code` 主列但代码读取 row.Values["code"] | trim | 优先用于匹配 existing device；创建时作为指定 code |
| `BizCode` | `biz_code` | JSON/Excel | trim | 身份定位、attributes.biz_code、accepted/rejected code |
| `Name` | `biz_name` | JSON `biz_name` 或 Excel `biz_name/name` | trim；fallback 到 existing name/resolved code | DeviceV2 entity name、attributes.name |
| `Platform` | `platform` | JSON/Excel；Excel `platform_code` alias 也进这里 | trim | platform 主数据按 code/name 解析 |
| `PlatformCode` | `platform_code` | JSON submit 可直接传；Excel 主链路通常为空 | trim | 优先用于 platform 主数据解析和最终 platform_code |
| `Status` | `status` | JSON/Excel | lower；只允许空/active/inactive/planned/retired | attributes.status、DeviceV2 status |
| `CredentialRefInBand` | `credential_ref_in_band` | JSON/Excel | trim | attributes、credential_refs、纳管判断 |
| `CredentialRefOutBand` | `credential_ref_out_band` | JSON/Excel | trim | attributes、credential_refs、纳管判断 |
| `SNMPCredentialRef` | `snmp_credential_ref` | JSON 可传；Excel 模板没有该列但代码支持 | trim | attributes、credential_refs、纳管判断 |
| `WinRMCredentialRef` | `winrm_credential_ref` | JSON/Excel | trim | attributes、纳管判断；不会生成 winrm credential alias |
| `WinRMPort` | `winrm_port` | JSON/Excel | int；Excel parse 失败为 0 | attributes.winrm_port |
| `RackPosition` | `rack_position` | JSON/Excel | trim | attributes.rack_position，同时写 frame |
| `Labels` | `labels` | JSON | trim key/value；Excel 不生成 | DeviceV2 labels |
| `Attributes` | `attributes` | JSON；Excel 非 top-level headers 全进入 attributes | merge/normalize | DeviceV2 attributes |
| `Metadata` | `metadata` | JSON | merge；platform/catalog/location 解析会补充 | DeviceV2 metadata |
| `GroupTags` | `group_tags` | JSON | trim、去重、去空 | entity extra.group_tags / projection group_tags |

## 5. 解析与规范化

### 5.1 sourceAdapter.Parse

输入：`DeviceV2IngestSubmitReq`

输出：

- `ingestSourceSnapshot`
- `[]ingestInputRow`

`ingestSourceSnapshot` 字段：

| 字段 | 来源/处理 |
| --- | --- |
| `source_type` | trim(req.Source) |
| `adapter` | 由 source 决定：`manual_json/excel_devices_sheet/reference_payload/future_pipeline_payload` |
| `requested_by` | trim(req.RequestedBy) |
| `raw_device_count` | len(req.Devices) |
| `accepted_row_count` | len(rows) |
| `warnings` | 当前为空数组 |

`ingestInputRow` 字段：

| 字段 | 来源/处理 |
| --- | --- |
| `row_no` | req.Devices 下标 + 1 |
| `raw_values` | `deviceToMap(device)` |
| `normalized_values` | 字符串 trim；map clone；string slice trim/去重 |
| `warnings` | 当前为空数组 |

### 5.2 canonical builder

`defaultCanonicalBuilder.Build` 从 `normalized_values` 重建 `DeviceV2IngestDevice`：

- `Name` 取 `biz_name`，否则 `name`。
- `Status` 转小写。
- `Labels` 只接受 map string 或 map interface 中的 string 值。
- `Attributes` 只接受 `map[string]interface{}`。
- `GroupTags` 支持 `[]string` 或 `[]interface{}` 中的 string。

边界：

- 非 string 的 label value 会被丢弃。
- 非 map 的 attributes/metadata 会变空 map。
- 非法 int 字段会变 0。

## 6. 校验

`defaultIngestValidator.Validate` 对 canonical devices 做校验。

### 6.1 身份字段

每台设备至少要有以下之一：

- `code`
- `biz_code`
- `attributes.sn`
- `attributes.asset_number`
- `attributes.in_band_ip`
- `attributes.out_band_ip`
- `attributes.hostname`

否则 issue：

- `field=identity`
- message：`至少提供 biz_code/sn/asset_number/in_band_ip/out_band_ip/hostname 之一（内部链路也可附带 code）`

### 6.2 status

允许值：

- 空
- `active`
- `inactive`
- `planned`
- `retired`

非法时 issue：

- `field=status`
- message：`status 非法: <value>`

### 6.3 IP

校验字段：

- `attributes.in_band_ip`
- `attributes.out_band_ip`

处理：

- 非空才校验。
- 用 `net.ParseIP`。
- 非法时报 `<field> 不是合法 IP: <value>`。

### 6.4 重复

校验重复字段：

- `code`
- `biz_code`

边界：

- 只在当前 devices payload 内查重复。
- 不在 validator 阶段查数据库重复。

## 7. 匹配与写库

### 7.1 existing device 匹配顺序

`resolveExistingDevice` 顺序：

1. 如果有 `device.Code`，先查 entity_instance：`entity_type=device_v2 AND entity_id=code`。
2. 再查 projection：`device_v2.code=code`。
3. 再查 code registry：`code_norm=lower(trim(code)) AND status=active`。
4. 再按 locator 顺序查 JSON 字段：
   - `biz_code`
   - `sn`
   - `asset_number`
   - `in_band_ip`
   - `out_band_ip`
   - `hostname`

locator 查询位置：

- entity `attributes` JSON
- projection `attributes_json`

边界：

- locator 命中多个 entity：报错，不能确定更新目标。
- locator 命中多个 projection：报错。
- registry 命中多个 entity_id：报错。

### 7.2 创建 code 规则

如果找不到 existing device：

- 如果输入有 `device.Code`，先检查是否已占用。
- 如果未占用，用输入 code 创建。
- 如果输入没有 code，生成 `DVC` + 12 位 UUID 大写片段。
- 最多尝试 12 次。

占用检查：

- entity_instance
- device_v2 projection
- device_v2_code_registry active code_norm

### 7.3 平台 platform 解析

输入候选：

1. `device.PlatformCode`
2. `device.Platform`
3. 已选择的 `platformCode`

解析表：

- base `platform` 表，即 `basemodel.Platform`

匹配方式：

- 先 `code = ?`
- 再 `LOWER(name) = LOWER(?)`

成功后：

- `platformCode = platform.Code`
- `attributes.platform_code = platform.Code`
- `metadata.platform_code = platform.Code`
- `attributes.platform = platform.Name`
- `metadata.platform_name = platform.Name`

失败边界：

- 如果 platform 表存在，且输入平台值非空但找不到：报错 `导入的 platform/platform_code 未匹配平台主数据: <value>`。
- 如果 platform 表不存在：不解析，不报错。

### 7.4 类别 catalog 解析

catalog 不在 `DeviceV2IngestDevice` 顶层字段里，它从 `attributes/metadata` 读取。

候选值：

- `attributes.catalog_code`
- `attributes.catalog_name`
- `attributes.catalog`
- `metadata.catalog_code`
- `metadata.catalog_name`

解析表：

- base `catalog` 表，即 `basemodel.Catalog`

匹配方式：

- `LOWER(code) = LOWER(?)`
- `LOWER(name) = LOWER(?)`

成功后：

- `attributes.catalog_code = catalog.Code`
- `attributes.catalog = catalog.Name`
- `metadata.catalog_code = catalog.Code`
- `metadata.catalog_name = catalog.Name`

失败边界：

- 如果输入了 catalog 相关值但 catalog 表不存在：报错 `导入包含 catalog/catalog_code/catalog_name，但 catalog 主数据表不存在`。
- 如果表存在但找不到：报错 `导入的 catalog/catalog_code/catalog_name 未匹配类别主数据: <value>`。

当前重要缺口：

- 新 ingest Excel 模板没有 `catalog_code/catalog_name/catalog` 列。
- Excel 的 `device_kind` 不会自动映射为 catalog。
- 旧 import/batches 有 `device_kind/device_type/device_model`，下一轮要继续追是否映射 catalog/device_model。

### 7.5 位置 region/site/rack 解析

候选字段：

- region：`attributes.region_code`、`attributes.region_name`、`metadata.region_code`、`metadata.region_name`
- site：`attributes.site_code`、`attributes.site_name`、`metadata.site_code`、`metadata.site_name`
- rack：`attributes.rack_code`、`attributes.rack_name`、`metadata.rack_code`、`metadata.rack_name`

匹配表：

- `region`
- `site`
- `rack`

匹配方式：

- code 忽略大小写
- name 忽略大小写

层级边界：

- site 与 region 不一致时报错。
- rack 与 site 不一致时报错。

成功后：

- 补齐 `attributes.*_code`
- 补齐 `attributes.*_name`
- 补齐 `metadata.*_code`
- 补齐 `metadata.*_name`

### 7.6 attributes 合并

`mergeIngestAttributes` 处理：

| 字段 | 处理 |
| --- | --- |
| existing/base attrs | 先 clone |
| device.Attributes | 覆盖/补充 |
| `code` | 如果 resolvedCode 非空，写入 attrs.code |
| `biz_code` | 非空写入 attrs.biz_code |
| `name` | device.Name / attrs.name / code |
| `platform_code` | device.PlatformCode / device.Platform / attrs.platform_code |
| `platform` | device.Platform 非空写入 |
| `status` | device.Status / attrs.status |
| `credential_ref_in_band` | device 或既有 attrs |
| `credential_ref_out_band` | device 或既有 attrs |
| `snmp_credential_ref` | device 或既有 attrs |
| `winrm_credential_ref` | device 或既有 attrs |
| `winrm_port` | device 或既有 attrs，必须 > 0 |
| `rack_position` | 写 `rack_position`，并同步 `frame` |

### 7.7 function_area 默认值

如果 attrs、metadata、labels 中都没有：

- `function_area`
- `functionArea`

则写入：

- `attributes.function_area = "DefaultArea"`

## 8. 纳管和采集相关字段

### 8.1 最小纳管判断

ingest executor 里的 `deriveManageabilityStatus`：

可纳管条件：

- 有 `attributes.in_band_ip` 且有以下任一：
  - `credential_ref_in_band`
  - `snmp_credential_ref`
  - `winrm_credential_ref`
- 或有 `attributes.out_band_ip` 且有：
  - `credential_ref_out_band`

返回：

- true, `manageable`
- false, `registered_only`

### 8.2 DeviceV2 写库后的纳管状态

`DeviceV2Srv.buildEntitySourceForWrite` 还会再次归一化：

- `attributes.manageable = bool`
- `attributes.manage_status = "manageable"` 或 `"registered_only"`
- entity `LifecycleStage = "manage"`
- entity `StageStatus = "success"`
- entity `ManageStatus = "success"` 或 `"pending"`

关键差异：

- ingest result 里的 `manage_status` 是 `manageable/registered_only/failed/unknown`。
- entity 顶层 `manage_status` 是 `success/pending`。
- 这两个不是同一个语义层，前端不能混为一个字段解释。

### 8.3 credential_refs 折叠

写库归一化会从顶层凭据字段折叠出 `attributes.credential_refs`：

| 输入字段 | 生成 refs |
| --- | --- |
| `credential_ref_in_band` | `in_band:<login_method>`、`in_band`、`default` |
| `credential_ref_out_band` | `out_band:<login_method>`、`out_band` |
| `snmp_credential_ref` | `snmp` |

默认 login_method：

- 空时按 `ssh`

注意：

- `winrm_credential_ref` 参与纳管判断并持久化，但当前折叠逻辑不会生成 `credential_refs.winrm` alias。

### 8.4 access_points 生成

如果没有显式 `attributes.access_points`，会从 IP 生成：

| 来源字段 | 生成 |
| --- | --- |
| `in_band_ip` | access point plane=`in_band` |
| `out_band_ip` | access point plane=`out_band` |
| `in_band_ip_code` | endpoint `ip_code` |
| `out_band_ip_code` | endpoint `ip_code` |

默认：

- login_method 空 -> `ssh`
- ssh port -> 22
- telnet -> 23
- http -> 80
- https -> 443
- winrm -> 5985

## 9. Task 持久化字段

表：`device_v2_ingest_task`

### 9.1 顶层字段

| 字段 | 来源 | 处理 |
| --- | --- | --- |
| `task_id` | `newTaskID()` | `ingest-task-` + uuid 去横线 |
| `status` | `deriveTaskStatus(execution)` | failed>0 -> failed；enabled 且非 blocked -> completed；否则 prepared |
| `framework_version` | 常量 | `v0-minimal` |
| `source` | req.Source | trim |
| `requested_by` | req.RequestedBy | trim |
| `execution_enabled` | execution.Enabled | executor 是否启用 |
| `device_count` | len(devices) | canonical device 数 |
| `message` | execution.Message | 空则 `device payload prepared` |
| `devices_json` | task.Devices | JSON 序列化 |
| `result_json` | task.Result | JSON 序列化 |
| `stages_json` | task.Stages | JSON 序列化 |
| `created_at` | GORM hook | create time |
| `updated_at` | GORM hook | update time |

JSON decode 边界：

- `devices_json` 坏 JSON：显式报 `device_v2 ingest devices JSON decode failed`
- `result_json` 坏 JSON：显式报 `device_v2 ingest result JSON decode failed`
- `stages_json` 坏 JSON：显式报 `device_v2 ingest stages JSON decode failed`

### 9.2 result 字段

`task.Result` 顶层：

| 字段 | 来源 |
| --- | --- |
| `accepted_count` | len(devices) |
| `device_codes` | devices 中非空 Code |
| `device_keys` | first identity key |
| `input_row_count` | len(rows) |
| `source_summary` | source adapter snapshot |
| `validation` | validator report |
| `execution` | executor report |
| `post_check` | validation + execution 汇总 |

### 9.3 execution.device_results 字段

| 字段 | 来源/处理 |
| --- | --- |
| `device_code` | finalCode；失败前默认 identityKey/code |
| `action` | `created/updated/failed/skipped/blocked` |
| `status` | 成功 `completed`；失败 `failed`；禁用 `blocked` |
| `matched_by` | `code/biz_code/sn/asset_number/in_band_ip/out_band_ip/hostname` |
| `message` | upsert 消息或错误 |
| `manageable` | deriveManageabilityStatus |
| `manage_status` | `manageable/registered_only/failed/unknown` |

## 10. 本轮发现的关键边界和缺口

1. `platform` 已有真实主数据解析：按 platform code/name 匹配，不匹配会失败。
2. `catalog` 已有真实解析逻辑，但新 ingest Excel 模板没有 catalog 字段，`device_kind` 也不会自动变 catalog。
3. `device_kind/vendor/model/remark` 在新 ingest Excel 主链路中只是 attributes，不参与平台/catalog/device_model 主数据校验。
4. `tenant_name` 会进入 attributes，但新 ingest 主链路当前没有把 tenant_name 解析为 tenant_code。
5. `region/site/rack` 会解析主数据，并校验层级一致。
6. `management_path/org_path` 虽有兼容 alias，但入库阶段不再使用，不能作为当前 D2 ingest 的核心流转字段。
7. `manage_status` 至少有两层含义：ingest result 的 `manageable/registered_only`，entity 顶层的 `success/pending`。
8. `winrm_credential_ref` 可使设备可纳管，但不会折叠到 `credential_refs.winrm`。
9. Excel parser 不看扩展名，只看 xlsx parser 能否打开；UI 的 `.xlsx only` 是前端生产约束。
10. 新 ingest 主链路和旧 import/batches 链路字段不完全一致，不能混写总结。

## 11. 下一轮必须继续提取

下一轮重点：

- `import/batches` 四个 pass 的全部字段：base/access/credential/relation。
- `device_kind/device_type/device_model/model/catalog` 在旧批次链路里的真实处理。
- `store run` 和 `collection plan` 字段：`manageable_status`、`core_store_status`、`collection_plan_source`、`next_collection_plan`。
- 批次校验状态、应用状态、错误码、自动 code、冲突候选、locator trace。
- 采集、解析、纳管之间的字段边界。

## 12. import/batches 批次导入链路

这条链路不是 redesign ingest upload 的同一套 Excel 模板。它通过 batch/record 模型承载多 pass 导入。

真实 pass：

| pass | 常量 | 作用 |
| --- | --- | --- |
| base | `pass_1_base` | 设备基础资产 |
| access | `pass_2_access` | 接入面、IP、登录方式、端口、凭据引用 |
| credential | `pass_3_credential` | 凭据绑定 |
| relation | `pass_4_relation` | 设备关系，当前 minimal implementation 会 skip |

### 12.1 CreateBatch 字段

`DeviceV2ImportCreateBatchReq`：

| 字段 | 来源 | 处理/去处 |
| --- | --- | --- |
| `batch_id` | 请求可传 | 可空；为空时由 build batch 逻辑生成 |
| `template_code` | 请求 | 写入 batch.template_code |
| `import_pass` | 请求必填 | 必须是四个 pass 之一 |
| `namespace` | 请求 | 空默认 `infra/device` |
| `mode` | 请求 | 空默认 `apply`；也支持 `dry_run` |
| `source_file` | 请求 | 写入 batch.source_file |
| `sheet` | 请求 | 写入 batch.sheet |
| `created_by` | 请求 | 写入 batch.created_by |
| `options` | 请求 map | JSON 存入 options_json |

### 12.2 UploadBatch 字段

`DeviceV2ImportUploadReq`：

| 字段 | 来源 | 处理/去处 |
| --- | --- | --- |
| `source_file` | 请求 | 更新 batch.source_file |
| `sheet` | 请求 | 更新 batch.sheet |
| `rows` | 请求必填 | 转为 import records；空报错 |

`DeviceV2ImportRecord`：

| 字段 | 来源/处理 |
| --- | --- |
| `id` | DB 自增 |
| `batch_id` | batch.BatchID |
| `row_no` | 上传行序号 |
| `namespace` | batch namespace |
| `entity_code` | validation 阶段生成 |
| `resolved_entity_id` | apply 成功后写入 |
| `match_mode` | 当前模型字段存在，本轮 minimal 代码未看到核心写入 |
| `code_source` | 当前模型字段存在，用于查询/统计 |
| `locator_trace` | 当前模型字段存在，用于定位追踪 |
| `validate_status` | `pending/ok/error` |
| `apply_status` | `pending/success/failed/skipped` |
| `error_code` | `IMPORT_VALIDATE_ERROR/IMPORT_APPLY_ERROR` 或空 |
| `error_message` | 校验/应用错误 |
| `conflict_candidates` | JSON 数组；validation 默认清空 |
| `raw_payload` | 上传原始行 |
| `normalized_patch` | validation 生成的标准补丁 |
| `applied_at` | apply 成功时间 |

### 12.3 pass_1_base Excel 字段

`DeviceV2ImportBaseExcelRow`：

| 字段 | 中文列 | 进入 raw_payload key | 后续处理 |
| --- | --- | --- | --- |
| `SystemID` | 系统ID | `system_id` | 如果 `biz_code` 空，可作为 bizCode |
| `Code` | 设备编码 | `code` | 优先实体编码 |
| `Name` | 设备名称 | `name` | 设备名候选 |
| `Tenant` | 租户 | `tenant` | 进入 raw；minimalNormalize 当前未读入 attrs |
| `Namespace` | 命名空间 | `namespace` | 进入 raw |
| `DeviceKind` | 设备类别 | `device_kind` | 进入 raw；minimalNormalize 当前未读入 attrs |
| `SN` | 序列号 | `sn` | 进入 attrs.sn，定位字段 |
| `InBandIP` | 带内IP | `in_band_ip` | attrs.in_band_ip，校验 IP |
| `OutBandIP` | 带外IP | `out_band_ip` | attrs.out_band_ip，校验 IP |
| `LoginMethod` | 默认登录方式 | `login_method` | 进入 raw；minimalNormalize 当前未读入 attrs |
| `LoginPort` | 默认登录端口 | `login_port` | 进入 raw；minimalNormalize 当前未读入 attrs |
| `InBandLoginMethod` | 带内登录方式 | `in_band_login_method` | 进入 raw |
| `InBandLoginPort` | 带内登录端口 | `in_band_login_port` | 进入 raw |
| `OutBandLoginMethod` | 带外登录方式 | `out_band_login_method` | 进入 raw |
| `OutBandLoginPort` | 带外登录端口 | `out_band_login_port` | 进入 raw |
| `InBandCredentialRef` | 带内凭据引用 | `in_band_credential_ref` | alias 到 attrs.credential_ref_in_band |
| `OutBandCredentialRef` | 带外凭据引用 | `out_band_credential_ref` | alias 到 attrs.credential_ref_out_band |
| `SNMPCredentialRef` | SNMP凭据引用 | `snmp_credential_ref` | attrs.snmp_credential_ref |
| `APICredentialRef` | API凭据引用 | `api_credential_ref` | 进入 raw；minimalNormalize 当前未读入 attrs |
| `AssetNumber` | 资产编号 | `asset_number` | attrs.asset_number，定位字段 |
| `Hostname` | 主机名 | `hostname` | attrs.hostname，定位字段 |
| `DeviceModel` | 设备型号 | `device_model` | attrs.device_model |
| `DeviceType` | 设备类型 | `device_type` | attrs.device_type |
| `Region` | 区域 | `region` | attrs.region |
| `Site` | 机房 | `site` | attrs.site |
| `Rack` | 机柜 | `rack` | attrs.rack |
| `RackPosition` | 机架号 | `rack_position` | attrs.rack_position |
| `FunctionArea` | 功能区 | `function_area` | 进入 raw；minimalNormalize 当前未读入 attrs |
| `Description` | 描述 | `description` | 进入 raw；minimalNormalize 当前未读入 attrs |

关键差异：

- 旧 base pass 有 `device_model/device_type`。
- 新 ingest Excel 是 `device_kind/vendor/model`。
- 旧 base pass 也没有直接叫 `catalog` 的字段。

### 12.4 pass_2_access 字段

`DeviceV2ImportAccessExcelRow`：

| 字段 | 中文列 | key | 含义 |
| --- | --- | --- | --- |
| `SystemID` | 系统ID | `system_id` | 设备业务 ID |
| `Code` | 设备编码 | `code` | 设备编码 |
| `Plane` | 接入面 | `plane` | in_band/out_band 等 |
| `IP` | IP地址 | `ip` | 接入点 IP |
| `LoginMethod` | 登录方式 | `login_method` | ssh/telnet/http/https/winrm 等 |
| `LoginPort` | 登录端口 | `login_port` | 端口 |
| `Transport` | 传输协议 | `transport` | 采集/连接协议 |
| `CredentialRef` | 凭据引用 | `credential_ref` | 该接入点凭据 |
| `Priority` | 优先级 | `priority` | 接入点优先级 |
| `InBandIP` | 带内IP | `in_band_ip` | 兼容宽表 |
| `InBandLoginMethod` | 带内登录方式 | `in_band_login_method` | 兼容宽表 |
| `InBandLoginPort` | 带内登录端口 | `in_band_login_port` | 兼容宽表 |
| `InBandCredential` | 带内凭据引用 | `in_band_credential_ref` | 兼容宽表 |
| `OutBandIP` | 带外IP | `out_band_ip` | 兼容宽表 |
| `OutBandLoginMethod` | 带外登录方式 | `out_band_login_method` | 兼容宽表 |
| `OutBandLoginPort` | 带外登录端口 | `out_band_login_port` | 兼容宽表 |
| `OutBandCredential` | 带外凭据引用 | `out_band_credential_ref` | 兼容宽表 |

### 12.5 pass_3_credential 字段

`DeviceV2ImportCredentialExcelRow`：

| 字段 | 中文列 | key | 含义 |
| --- | --- | --- | --- |
| `SystemID` | 系统ID | `system_id` | 设备业务 ID |
| `Code` | 设备编码 | `code` | 设备编码 |
| `EndpointID` | 端点ID | `endpoint_id` | 接入点 ID |
| `Plane` | 接入面 | `plane` | 接入面 |
| `IP` | IP地址 | `ip` | IP |
| `LoginMethod` | 登录方式 | `login_method` | 登录方式 |
| `LoginPort` | 登录端口 | `login_port` | 登录端口 |
| `CredentialRef` | 凭据引用 | `credential_ref` | 凭据引用 |
| `CredentialType` | 凭据类型 | `credential_type` | 凭据类型 |
| `AuthScope` | 授权范围 | `auth_scope` | 授权范围 |
| `InBandCredentialRef` | 带内凭据引用 | `in_band_credential_ref` | 兼容宽表 |
| `OutBandCredentialRef` | 带外凭据引用 | `out_band_credential_ref` | 兼容宽表 |
| `SNMPCredentialRef` | SNMP凭据引用 | `snmp_credential_ref` | 兼容宽表 |
| `APICredentialRef` | API凭据引用 | `api_credential_ref` | 兼容宽表 |

### 12.6 pass_4_relation 字段

`DeviceV2ImportRelationExcelRow`：

| 字段 | 中文列 | key | 当前处理 |
| --- | --- | --- | --- |
| `SystemID` | 系统ID | `system_id` | raw |
| `Code` | 设备编码 | `code` | raw |
| `RelationType` | 关系类型 | `relation_type` | raw |
| `TargetCode` | 目标设备编码 | `target_code` | raw |
| `Direction` | 方向 | `direction` | raw |
| `Weight` | 权重 | `weight` | raw |
| `Enabled` | 启用 | `enabled` | raw |
| `Description` | 描述 | `description` | raw |

边界：

- 当前 minimal implementation 对 relation pass 执行 `skipped`，message 为 `minimal implementation skips relation pass`。

### 12.7 批次 normalization

`minimalNormalizeImportRecord` 真实读取进入 attrs 的字段：

- `sn`
- `asset_number`
- `hostname`
- `in_band_ip`
- `out_band_ip`
- `device_model`
- `device_type`
- `region_code`
- `region`
- `site_code`
- `site`
- `rack_code`
- `rack`
- `rack_position`
- `credential_ref_in_band`
- `credential_ref_out_band`
- `snmp_credential_ref`
- `winrm_credential_ref`
- `winrm_port`
- `platform_code`
- `platform`

额外 alias：

- `in_band_credential_ref` -> `credential_ref_in_band`
- `out_band_credential_ref` -> `credential_ref_out_band`
- `system_id` -> `biz_code` fallback

标准 normalized_patch：

| 字段 | 来源/处理 |
| --- | --- |
| `code` | raw.code；空则后续按 batch/row 生成 |
| `biz_code` | raw.biz_code，否则 raw.system_id |
| `name` | raw.name/raw.biz_name/raw.hostname/code/biz_code |
| `platform_code` | raw.platform_code，否则 raw.platform |
| `status` | raw.status；空默认 `active` |
| `credential_ref_in_band` | attrs.credential_ref_in_band |
| `credential_ref_out_band` | attrs.credential_ref_out_band |
| `snmp_credential_ref` | raw.snmp_credential_ref |
| `rack_position` | attrs.rack_position |
| `group_tags` | raw.group_tags |
| `labels` | raw.labels |
| `metadata` | raw.metadata |
| `attributes` | attrs |
| `namespace` | batch namespace，空默认 `infra/device` |

校验：

- 至少有 `code/biz_code/sn/asset_number/in_band_ip/out_band_ip/hostname` 之一。
- `in_band_ip/out_band_ip` 必须是合法 IP。
- 当前 batch 内 `code`、`biz_code` 不能重复。

自动 code：

- 有 code 用 code。
- 无 code 有 biz_code 用 biz_code。
- 否则 `DV2` + batchID 后 12 位 + 3 位 rowNo。

## 13. store pipeline 和采集计划字段

### 13.1 Start 请求

`DeviceV2StoreStartReq` 位于 `dto/device_v2.go`，真实启动 store pipeline。

核心字段：

| 字段 | 含义 | 处理 |
| --- | --- | --- |
| `codes` | 设备编码列表 | 必须非空 |
| `pipeline_template` | pipeline 模板 | 空默认 `device_v2_minimal_store` |
| `options` | pipeline 选项 | clone 后进入 task.Options；API 层会注入默认 async 和采集配置 |

### 13.2 EntityPipelineTask 字段

store start 创建 `EntityPipelineTask`：

| 字段 | 真实值/来源 |
| --- | --- |
| `task_id` | `device-v2-store-` + uuid |
| `entity_type` | `device_v2` |
| `entity_ids` | codes |
| `pipeline_template` | 请求值或 `device_v2_minimal_store` |
| `current_stage` | 初始 `store`，完成后 `manage` |
| `overall_status` | `running/success/partial/failed` |
| `options` | 请求 options |
| `result.summary.device_total` | codes 数量 |
| `result.summary.created` | executor created 数 |
| `result.summary.updated` | executor updated 数 |
| `result.summary.failed` | 失败数 |
| `result.summary.manageable` | manageable run 数 |
| `result.summary.unmanageable` | unmanageable run 数 |
| `result.summary.observation_count` | observation 数 |
| `result.summary.execution_framework` | `device_v2_minimal_store` |
| `stages` | `pre_register/store/manage` |

### 13.3 DeviceV2StoreRun 字段

表：`device_v2_store_run`

| 字段 | 来源/处理 |
| --- | --- |
| `run_id` | stable sha1：taskID + code |
| `task_id` | store task id |
| `device_code` | code 或 result.DeviceCode |
| `status` | `pending/running/partial/success/failed/blocked` |
| `current_step` | `load_device/minimal_upsert` |
| `core_store_status` | `pending/success/failed/blocked` |
| `manageable_status` | `unknown/pending/ready/unready` |
| `summary` | run summary JSON |
| `created_at` | create time |
| `updated_at` | update time |
| `finished_at` | run 完成时间 |

`manageable_status` 归一化：

- 如果 result.ManageStatus 已是 `ready/unready/pending`，直接使用。
- 否则 `result.Manageable == true` -> `ready`。
- 否则 -> `unready`。

### 13.4 Store run summary 字段

`minimalBuildRunSummary`：

| 字段 | 来源 |
| --- | --- |
| `device_code` | execution result |
| `name` | DeviceV2.Name，否则 device_code |
| `action` | execution result action |
| `message` | execution result message |
| `manageable` | execution result manageable |
| `manage_status` | execution result manage_status |
| `platform_code` | device.Attributes.platform_code |
| `in_band_ip` | device.Attributes.in_band_ip |
| `out_band_ip` | device.Attributes.out_band_ip |
| `hostname` | device.Attributes.hostname |
| `sn` | device.Attributes.sn |
| `asset_number` | device.Attributes.asset_number |
| `location_node_code` | device.Attributes.location_node_code |
| `region_code` | device.Attributes.region_code |
| `site_code` | device.Attributes.site_code |
| `rack_code` | device.Attributes.rack_code |
| `labels` | DeviceV2.Labels |
| `group_tags` | DeviceV2.GroupTags |
| `collection_plan_snapshot` | 当前 minimal 中为空数组 |

### 13.5 Observations 字段

store 会生成 observation：

| capability | field_key |
| --- | --- |
| `identity` | `code` |
| `identity` | `hostname` |
| `identity` | `sn` |
| `identity` | `asset_number` |
| `access` | `in_band_ip` |
| `access` | `out_band_ip` |
| `access` | `credential_ref_in_band` |
| `access` | `credential_ref_out_band` |
| `location` | `region_code` |
| `location` | `site_code` |
| `location` | `rack_code` |
| `location` | `rack_position` |
| `hardware` | `platform_code` |
| `hardware` | `device_model` |
| `hardware` | `device_type` |

每条 observation：

- `observation_id`：sha1 stable id
- `task_id`
- `run_id`
- `device_code`
- `capability`
- `field_key`
- `status=success`
- `value={"value": <field value>}`
- `raw={"value": <field value>}`
- `source=device_v2_minimal_store`

### 13.6 Collection plan list 字段

`DeviceV2TaskCollectionPlanListReq` 查询字段：

- `page`
- `page_size`
- `device_code`
- `run_id`
- `status`
- `core_store_status`
- `manageable_status`
- `action`
- `availability_status`
- `plan_source`

`DeviceV2TaskCollectionPlanListItem`：

| 字段 | 来源/处理 |
| --- | --- |
| `task_id` | task id |
| `run_id` | store run |
| `device_code` | store run |
| `status` | run.status |
| `core_store_status` | run.core_store_status |
| `manageable_status` | run.manageable_status |
| `current_step` | run.current_step |
| `collection_plan_source` | 固定 `minimal_status` |
| `manageable_ready_planes` | 当前 minimal plan 未填 |
| `manageable_pending_reasons` | 如果 manageable_status != ready，则 `manageability_not_ready` |
| `next_collection_plan` | 见下表 |

`next_collection_plan`：

| 字段 | 真实值/处理 |
| --- | --- |
| `plan_key` | `minimal:<action>` |
| `action` | run 成功且 core_store 成功 -> `noop`；否则 `retry_store` |
| `collection_key` | run.current_step，否则 `store` |
| `stage_key` | `store` |
| `availability_status` | `noop` -> `done`；`retry_store` -> `available` |
| `availability_reasons` | 成功 `run_success`；失败 `last_run_<status>` |
| `reasons` | 同 availability_reasons |

边界：

- 当前 minimal collection plan 不是实际 SNMP/DC2 采集计划，只是基于 store run 状态生成的下一步建议。
- `collection_plan_snapshot` 当前为空，真实采集计划需要看更完整的 DC2/device_collection2 侧车配置与报告。

## 14. 采集配置边界

`normalizeDeviceCollectionOptions` 会处理 store pipeline options。

默认：

- `async=true`

DeviceCollection2 相关 options：

| 字段 | 来源/处理 |
| --- | --- |
| `device_collection2.enabled` | config 启用且请求未写时注入 |
| `device_collection2.collection_mode` | config mode 注入，允许 `dc2_primary/dc2_only` |
| `device_collection2.store_pipeline_probe_enabled` | config 或 mode 需要 probe 时注入 |
| `device_collection2.contract_key` | config 注入；有 collection_profiles 时不注入 |
| `device_collection2.dataset_keys` | config 注入；有 collection_profiles 时不注入 |
| `device_collection2.block_on_failure` | config 或 `dc2_primary/dc2_only` 注入 |
| `device_collection2.block_on_partial` | config 注入 |
| `enable_snmp` | `dc2_only` 时强制 false |

已下线 options，出现即报错：

- `device_v2_prepare_controller`
- `device_v2_prepare_local_snmp_enabled`
- `device_v2_prepare_local_collect_enabled`
- `observation_mib_tree_file`

## 15. 第二轮修正后的关键点

1. “平台”在新 ingest 主链路会查 platform 主数据；在旧 batch normalized_patch 中是 `platform_code = raw.platform_code || raw.platform`，随后通过 ingest executor 继续解析。
2. “类型/catalog”目前不是一个统一字段：
   - 新 ingest Excel：`device_kind/vendor/model` 只是 attributes。
   - 旧 base pass：`device_kind` 进入 raw 但 minimal normalize 未读入 attrs；`device_model/device_type` 会进入 attrs。
   - catalog 只有当 attributes/metadata 中显式有 `catalog_code/catalog_name/catalog` 时才解析。
3. “采集”在 minimal store 中分两层：
   - observations：把已有字段整理成 identity/access/location/hardware 观测。
   - collection plan：当前只是根据 store run 成败给 `noop/retry_store`，不是完整真实采集动作。
4. `manageable_status` 是 store run 的 readiness 状态：`unknown/pending/ready/unready`，不同于 entity `manage_status=success/pending`，也不同于 ingest result `manage_status=manageable/registered_only`。

## 16. 字段索引总表

这一节用于快速查字段，不代替上面的详细链路。

### 16.1 身份字段

| 字段 | 所属链路 | 来源 | 处理 | 去处/边界 |
| --- | --- | --- | --- | --- |
| `code` | ingest/batch/store | JSON submit、batch raw、已有 DeviceV2 | trim；优先匹配 entity/projection/registry；可作为 create code | 核心实体编码；没有 code 时 ingest 生成 `DVC...`，batch 可生成 `DV2...` |
| `biz_code` | ingest/batch | Excel/JSON/system_id fallback | trim；batch 中 system_id 可 fallback | 定位字段；写入 attrs.biz_code |
| `system_id` | batch | pass Excel | batch 中可 fallback 为 biz_code | 新 ingest 主链路无此字段 |
| `biz_name` | ingest | Excel/JSON/name alias | trim | top-level Name 候选 |
| `name` | batch/alias | Excel alias 或 batch raw | ingest Excel `name -> biz_name`；batch name 是设备名称 | DeviceV2 entity name / attrs.name |
| `hostname` | ingest/batch/store | attributes/raw | trim；校验 identity | 定位字段；observation identity |
| `sn` | ingest/batch/store | attributes/raw | trim | 定位字段；observation identity |
| `asset_number` | ingest/batch/store | attributes/raw | trim | 定位字段；observation identity |

### 16.2 平台、类型、catalog 字段

| 字段 | 所属链路 | 来源 | 处理 | 去处/边界 |
| --- | --- | --- | --- | --- |
| `platform` | ingest | Excel 主列、JSON | 先按 platform.code 匹配，再按 platform.name 匹配 | 成功后写 attrs.platform=平台名、metadata.platform_name |
| `platform_code` | ingest JSON/batch | JSON 可传；Excel 中是 platform alias；batch raw 可传 | 优先于 platform；最终会被 platform 主数据 code 覆盖 | attrs.platform_code、metadata.platform_code、DeviceV2 platformCode |
| `platform_name` | ingest metadata | platform 主数据解析后生成 | metadata 补充 | 展示/追溯 |
| `device_kind` | 新 ingest Excel/batch raw | Excel 字段 | 新 ingest 仅进入 attrs；batch minimal normalize 当前未读入 attrs | 不等于 catalog |
| `vendor` | 新 ingest Excel | Excel 字段 | 进入 attrs.vendor | 当前不参与主数据解析 |
| `model` | 新 ingest Excel | Excel 字段 | 进入 attrs.model | 不等于 `device_model` 或 `device_model_code` |
| `device_model` | batch/store observation | batch base | 进入 attrs.device_model | observation hardware；不自动解析 `device_model_code` |
| `device_type` | batch/store observation | batch base | 进入 attrs.device_type | observation hardware |
| `catalog` | ingest executor | attrs/metadata 显式输入 | 按 catalog code/name 解析 | 新 ingest Excel 不提供该列 |
| `catalog_code` | ingest executor/base validation | attrs/metadata 显式输入 | 匹配 catalog 主数据 code/name 后写 code | 主数据表存在且找不到会报错 |
| `catalog_name` | ingest executor | attrs/metadata 显式输入 | 匹配后写 metadata.catalog_name | 不由 device_kind 自动生成 |

### 16.3 状态字段

| 字段 | 所属链路 | 值域 | 来源/处理 | 边界 |
| --- | --- | --- | --- | --- |
| `status` | ingest device | 空/active/inactive/planned/retired | submit/Excel；canonical lower；validator 校验 | batch 空默认 active |
| `task.status` | ingest task | prepared/completed/failed | deriveTaskStatus | execution failed > 0 才 failed |
| `entity.manage_status` | DeviceV2 entity | success/pending | buildEntitySourceForWrite | true->success，false->pending |
| `attrs.manage_status` | DeviceV2 attrs | manageable/registered_only | deriveDeviceV2Manageability | 写库归一化生成 |
| `execution.device_results[].manage_status` | ingest result | manageable/registered_only/failed/unknown | executor result | 与 entity.manage_status 不同 |
| `manageable` | ingest/entity/result | bool | 由 IP + credential 判断 | 不应由 FE 另行推断 |
| `manageable_status` | store run | unknown/pending/ready/unready | store run normalize | readiness 层，不等于 manage_status |
| `core_store_status` | store run | pending/success/failed/blocked | store 执行结果 | collection plan 判断依据 |
| `apply_status` | import record | pending/success/failed/skipped | batch apply | relation pass 当前 skipped |
| `validate_status` | import record | pending/ok/error | batch validate | 校验失败写 IMPORT_VALIDATE_ERROR |

### 16.4 地址、位置、路径字段

| 字段 | 所属链路 | 来源 | 处理 | 去处/边界 |
| --- | --- | --- | --- | --- |
| `in_band_ip` | ingest/batch/store | Excel/JSON/raw attrs | validator 校验 IP | access point、manageable、observation |
| `out_band_ip` | ingest/batch/store | Excel/JSON/raw attrs | validator 校验 IP | access point、manageable、observation |
| `in_band_ip_code` | write normalization | attrs | 可进入 access_points.ip_code | 新 ingest Excel 无模板列 |
| `out_band_ip_code` | write normalization | attrs | 可进入 access_points.ip_code | 新 ingest Excel 无模板列 |
| `region_name` | ingest Excel | Excel | 按 region code/name 匹配 | 成功补 region_code/name |
| `region_code` | batch/alias | Excel alias 或 attrs | alias 到 region_name 后仍可匹配 code | store observation |
| `site_name` | ingest Excel | Excel | 按 site code/name 匹配，并校验 region 层级 | 成功补 site_code/name |
| `site_code` | batch/alias | Excel alias 或 attrs | alias 到 site_name 后仍可匹配 code | store observation |
| `rack_name` | ingest Excel | Excel | 按 rack code/name 匹配，并校验 site 层级 | 成功补 rack_code/name |
| `rack_code` | batch/alias | Excel alias 或 attrs | alias 到 rack_name 后仍可匹配 code | store observation |
| `rack_position` | ingest/batch | Excel/JSON | 写 attrs.rack_position，同时写 frame | observation location |
| `management_path` | ingest alias/list filter | org_path alias 或 attrs | ingest 阶段不再使用 | 不能当 D2 ingest 主字段 |
| `org_path` | ingest alias | Excel 旧 header | alias 到 management_path | 入库阶段不使用 |
| `location_node_code` | store summary/list filter | attrs | store summary 展示 | 新 ingest 不生成 |

### 16.5 凭据、接入、采集字段

| 字段 | 所属链路 | 来源 | 处理 | 去处/边界 |
| --- | --- | --- | --- | --- |
| `credential_ref_in_band` | ingest/write | Excel/JSON/attrs | 折叠为 credential_refs in_band/default | in_band 纳管判断 |
| `in_band_credential_ref` | batch alias | batch raw | alias 到 credential_ref_in_band | 旧宽表兼容 |
| `credential_ref_out_band` | ingest/write | Excel/JSON/attrs | 折叠为 credential_refs out_band | out_band 纳管判断 |
| `out_band_credential_ref` | batch alias | batch raw | alias 到 credential_ref_out_band | 旧宽表兼容 |
| `snmp_credential_ref` | ingest/write | JSON 支持；batch 支持；新 ingest Excel 模板无列 | 折叠为 credential_refs.snmp | in_band 纳管判断 |
| `winrm_credential_ref` | ingest/write | Excel/JSON/batch | 持久化；参与纳管判断 | 不折叠出 credential_refs.winrm |
| `winrm_port` | ingest/write | Excel/JSON/batch | int；失败为 0 | attrs.winrm_port |
| `credential_refs` | write attrs | 顶层凭据折叠或已有 attrs | 补 in_band/out_band/default/snmp | access_points credential 默认值 |
| `access_points` | write attrs | 显式 attrs 或从 IP 生成 | 补 plane/ip/login_method/login_port/transport/priority/endpoint_id | 采集/连接基础 |
| `endpoint_id` | access point/pass_3 | 自动生成或 Excel | access point 标识 | pass_3 credential 可指定 |
| `plane` | access/credential pass | Excel | 接入面 | in_band/out_band 等 |
| `login_method` | access/write | Excel/attrs | 空默认 ssh | 决定默认端口和 transport |
| `login_port` | access/write | Excel/attrs | <=0 时按 method 默认 | ssh 22/telnet 23/http 80/https 443/winrm 5985 |
| `transport` | access/write | Excel/attrs | 空时由 login_method 推断 | 采集连接协议 |
| `priority` | access/write | Excel/attrs | 空时按 plane 默认 | access point 排序 |
| `collection_plan_snapshot` | store summary | 当前 minimal | 空数组 | 不是完整采集计划 |
| `next_collection_plan` | collection plan API | run 状态派生 | success->noop，否则 retry_store | minimal_status，不是完整 DC2 计划 |

### 16.6 元数据、标签、分组字段

| 字段 | 所属链路 | 来源 | 处理 | 去处/边界 |
| --- | --- | --- | --- | --- |
| `labels` | ingest/batch/write | JSON/batch raw | trim string map | DeviceV2 labels |
| `attributes` | ingest/batch/write | JSON/Excel non-top-level/raw normalize | merge 后写 entity/projection | 主要业务扩展容器 |
| `metadata` | ingest/batch/write | JSON/batch raw | merge；platform/catalog/location 会补充 | 追溯和补充信息 |
| `group_tags` | ingest/batch/write | JSON/batch raw | trim、去空、去重 | entity extra.group_tags/projection group_tags |
| `tenant_name` | 新 ingest Excel | Excel | 进入 attrs.tenant_name | 当前不解析 tenant_code |
| `tenant_code` | alias/base validation | Excel alias 到 tenant_name；attrs 可显式提供 | base validation 可校验 attrs.tenant_code | 新 ingest 主链路不会从 tenant_name 解析 |
| `namespace` | batch | req/batch/raw | 空默认 infra/device | normalized_patch.namespace |
| `function_area` | write attrs | attrs/metadata/labels 或默认 | 空时写 DefaultArea | 影响 Agent/采集功能域 |
| `functionArea` | write attrs | 兼容字段 | 只用于判断是否显式设置 | 不作为默认写入名 |

### 16.7 任务、批次、run 字段

| 字段 | 所属链路 | 来源 | 处理 |
| --- | --- | --- | --- |
| `task_id` | ingest/store | uuid | ingest: `ingest-task-...`；store: `device-v2-store-...` |
| `run_id` | store | stable sha1 | taskID + device code |
| `batch_id` | import | req/generated | import batch 主键 |
| `row_no` | import/ingest rows | 行号 | Excel/batch 校验定位 |
| `source` | ingest task | req.Source | supported sources |
| `source_type` | source_summary | req.Source | source snapshot |
| `adapter` | source_summary | source -> adapter | manual_json/excel_devices_sheet/reference_payload/future_pipeline_payload |
| `requested_by` | ingest | req/form | task/source summary |
| `raw_device_count` | ingest source | len(req.Devices) | source_summary |
| `accepted_row_count` | ingest source | len(rows) | source_summary |
| `input_row_count` | ingest result | len(rows) | result |
| `accepted_count` | ingest result | len(devices) | result/post_check |
| `rejected_count` | post_check | validation rejected | result/post_check |
| `device_count` | ingest/store | len devices/codes | task/run summary |
| `created` | execution/store | executor count | task result/store summary |
| `updated` | execution/store | executor count | task result/store summary |
| `failed` | execution/store/import | executor/apply count | task result/store summary/batch |
| `skipped` | execution/import | executor/apply count | task result/batch |
| `message` | all | execution/error | 展示和审计 |
| `error_code` | import record | validation/apply | IMPORT_VALIDATE_ERROR/IMPORT_APPLY_ERROR |
| `error_message` | import record | validation/apply | 错误详情 |
| `conflict_candidates` | import record | model field | validation 默认清空 |
| `locator_trace` | import record | model field | 当前 minimal 核心流程未见主要写入 |

## 17. 总结

后端真实情况可以压缩成三句话：

1. 新 D2 ingest 主链路的核心是 `DeviceV2IngestDevice -> validate -> upsert -> ingest_task`，平台会解析，catalog 只有显式字段才解析，Excel 的 `device_kind/vendor/model` 只是属性。
2. 旧 import/batches 链路是另一套字段体系，base/access/credential/relation 四个 pass 中 `device_model/device_type` 存在，但 `device_kind` 目前在 minimal normalize 中没有真正进入 attrs。
3. 采集相关当前分为 store observations 和 minimal collection plan；`next_collection_plan` 只是根据 store run 状态产生的 `noop/retry_store` 建议，不等于完整 DC2 采集计划。
