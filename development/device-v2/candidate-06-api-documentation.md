# 【接口文档】OneOPS_DeviceV2_V1.0

## 1. 文档信息

| 项目 | 内容 |
|------|------|
| 系统名称 | OneOPS |
| 模块名称 | Device V2 入库与设备管理 |
| 版本号 | V1.0 |
| 创建日期 | 2026-05-15 |
| 文档状态 | `blocked-human-confirmation` |
| 接口基准地址 | `/api/v1` `[待确认: 后端负责人]` |
| 通用响应格式 | `OneOPS/pkg/response.response`，成功 `code=0`，失败 `code=-1` |
| 关联文档 | `docs/development-doc-templates/06-接口文档模板.md`<br>`docs/development/device-v2/README.md`<br>`docs/development/device-v2/ai-derived-confirmation-proposal.md` |
| 代码事实来源清单 | `docs/openclaw-autodev/evidence/dev-docs/DEV-DOCS-003C-device-v2-05-06-code-facts.md` |

> 生成说明：本文档基于 `docs/development-doc-templates/06-接口文档模板.md` 的标准文档结构反向生成，接口、DTO、前端调用入口来自当前源码；当前真实代码事实、AI 推导建议、规划缺口和未确认范围见代码事实来源清单。本文档状态为 `blocked-human-confirmation` 候选稿，不可直接作为 API 契约、开发、联调或验收依据。

## 2. 通用说明

### 2.1 通用请求头

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| Content-Type | string | 是 | JSON 接口通常为 `application/json`；Excel 上传为 `multipart/form-data`。 |
| Authorization | string | 是（需登录接口除外） | 前端请求工具统一处理认证；`/device/v2/ingest/template/excel` 的前端下载 URL 会携带 `token` query。`[待确认: 安全负责人]` |
| X-Request-Id | string | 否 | 后端响应中包含 `request_id`；请求头是否强制传入待确认。 |
| X-Tenant-Code | string | 否 | 当前 DTO 中存在 tenant/tenant_code 相关字段，但 API 层租户头规则待确认。`[待确认: 安全负责人]` |

### 2.2 通用响应结构

当前真实响应封装来自 `OneOPS/pkg/response/response.go`：

```json
{
  "request_id": "",
  "code": 0,
  "msg": "",
  "data": {}
}
```

失败响应候选格式：

```json
{
  "request_id": "",
  "code": -1,
  "msg": "错误信息",
  "data": null
}
```

说明：

- HTTP status 当前通常为 `200`，业务成功需判断 `code == 0`。
- 前端 `request<T>` 多数场景返回已解包的 `data`。
- 前端 `requestEnvelope<T>` 用于需要读取 `code/msg/data` 的创建、更新等接口。

### 2.3 状态码说明

| 状态码 | 说明 |
|--------|------|
| HTTP 200 | 请求到达后端并返回业务响应；不等于业务成功。 |
| 业务 code 0 | 成功。 |
| 业务 code -1 | 失败，错误信息在 `msg`。 |
| HTTP 400/401/403/404/500 | 当前是否由全局中间件或网关返回，待确认。 |
| 601 | 模板中存在该状态码，但当前 Device V2 源码未在本轮确认使用。 |

## 3. 接口列表

### 3.1 查询 Device V2 设备列表

**接口描述**：查询 Device V2 设备清册，支持分页、编码、关键字、名称、IP、标签、属性、纳管状态、管理路径和位置过滤。

**请求信息**

| 项目 | 内容 |
|------|------|
| 接口URL | GET `/device/v2/list` |
| 请求方式 | GET |
| Content-Type | application/json |
| 权限要求 | `[待确认: 安全负责人]` |

**请求参数**

| 参数名 | 类型 | 位置 | 必填 | 说明 | 示例 |
|--------|------|------|------|------|------|
| page | Integer | query | 否 | 页码 | 1 |
| page_size | Integer | query | 否 | 每页数量 | 20 |
| codes | String | query | 否 | 逗号分隔的设备编码列表 | DVC001,DVC002 |
| keyword | String | query | 否 | 按 code/name/IP/profile 等常用字段模糊过滤 | core |
| name | String | query | 否 | 按设备名称模糊过滤 | core-sw |
| ip | String | query | 否 | 按 in_band_ip/out_band_ip/management_ip/address 模糊过滤 | 10.0.0.1 |
| label_key | String | query | 否 | 标签键；后端只允许字母、数字、下划线 | env |
| label_value | String | query | 否 | 标签值；前端要求同时传 `label_key` | prod |
| attribute_key | String | query | 否 | 属性键；后端只允许字母、数字、下划线 | vendor |
| attribute_value | String | query | 否 | 属性值；前端要求同时传 `attribute_key` | huawei |
| manage_status | String | query | 否 | 源码注释为 `success/pending` | success |
| management_path | String | query | 否 | 管理路径前缀，兼容 org_path | network/core |
| location_node_code | String | query | 否 | 位置节点编码 | rack-a |
| location_path_prefix | String | query | 否 | 位置路径前缀，支持 `/`、`,`、`>`、`|` 分割 | region/site/rack |
| region_code | String | query | 否 | 区域编码 | cn-east |
| site_code | String | query | 否 | 站点编码 | sh-01 |
| rack_code | String | query | 否 | 机柜编码 | rack-01 |

**请求示例**

```http
GET /api/v1/device/v2/list?page=1&page_size=20&keyword=core HTTP/1.1
Host: oneops.example
Authorization: Bearer {token}
Content-Type: application/json
```

**Body 示例**

```json
{}
```

**响应示例（成功）**

```json
{
  "request_id": "",
  "code": 0,
  "msg": "",
  "data": {
    "list": [
      {
        "id": "1",
        "code": "DVC001",
        "name": "core-sw-01",
        "platform_code": "network",
        "status": "active",
        "manage_status": "success",
        "manageable": true,
        "labels": {},
        "attributes": {},
        "metadata": {},
        "group_tags": []
      }
    ],
    "total": 1,
    "page": 1,
    "page_size": 20
  }
}
```

**响应示例（失败）**

```json
{
  "request_id": "",
  "code": -1,
  "msg": "label_value requires label_key",
  "data": null
}
```

**业务规则与校验**

| 规则 | 处理方式 |
|------|----------|
| `label_value` 需要同时传 `label_key` | 前端 wrapper 会抛错，后端也有校验。 |
| `attribute_value` 需要同时传 `attribute_key` | 前端 wrapper 会抛错，后端也有校验。 |
| `label_key`、`attribute_key` 仅支持字母、数字、下划线 | 后端返回失败响应。 |

### 3.2 查询 Device V2 设备详情

**接口描述**：按设备编码查询 Device V2 设备详情。

**请求信息**

| 项目 | 内容 |
|------|------|
| 接口URL | GET `/device/v2/{code}` |
| 请求方式 | GET |
| Content-Type | application/json |
| 权限要求 | `[待确认: 安全负责人]` |

**请求参数**

| 参数名 | 类型 | 位置 | 必填 | 说明 | 示例 |
|--------|------|------|------|------|------|
| code | String | path | 是 | 设备编码 | DVC001 |

**请求示例**

```http
GET /api/v1/device/v2/DVC001 HTTP/1.1
Host: oneops.example
Authorization: Bearer {token}
Content-Type: application/json
```

**Body 示例**

```json
{}
```

**响应示例（成功）**

```json
{
  "request_id": "",
  "code": 0,
  "msg": "",
  "data": {
    "id": "1",
    "code": "DVC001",
    "name": "core-sw-01",
    "platform_code": "network",
    "status": "active",
    "labels": {},
    "attributes": {},
    "metadata": {},
    "group_tags": []
  }
}
```

**响应示例（失败）**

```json
{
  "request_id": "",
  "code": -1,
  "msg": "device_v2 不存在",
  "data": null
}
```

**业务规则与校验**

| 规则 | 处理方式 |
|------|----------|
| `code` 为空 | 前端 wrapper 不应发起；后端行为待确认。 |
| 返回对象必须包含 `code` 和 `name` | 前端 `assertDeviceV2Item` 会校验。 |

### 3.3 创建 Device V2 设备

**接口描述**：创建 Device V2 设备主记录。

**请求信息**

| 项目 | 内容 |
|------|------|
| 接口URL | POST `/device/v2?base_ref_mode=warn` |
| 请求方式 | POST |
| Content-Type | application/json |
| 权限要求 | `[待确认: 安全负责人]` |

**请求参数**

| 参数名 | 类型 | 位置 | 必填 | 说明 | 示例 |
|--------|------|------|------|------|------|
| code | String | body | 是 | 设备编码 | DVC001 |
| name | String | body | 否 | 设备名称 | core-sw-01 |
| platform_code | String | body | 否 | 平台编码 | network |
| status | String | body | 否 | 状态，取值待确认 | active |
| labels | Object | body | 否 | 标签 | {"env":"prod"} |
| attributes | Object | body | 否 | 动态属性 | {"in_band_ip":"10.0.0.1"} |
| metadata | Object | body | 否 | 元数据 | {} |
| group_tags | Array[String] | body | 否 | 分组标签 | ["core"] |
| base_ref_mode | String | query | 否 | 前端当前固定传 `warn`，正式规则待确认 | warn |

**请求示例**

```http
POST /api/v1/device/v2?base_ref_mode=warn HTTP/1.1
Host: oneops.example
Authorization: Bearer {token}
Content-Type: application/json
```

**Body 示例**

```json
{
  "code": "DVC001",
  "name": "core-sw-01",
  "platform_code": "network",
  "status": "active",
  "labels": {},
  "attributes": {},
  "metadata": {},
  "group_tags": []
}
```

**响应示例（成功）**

```json
{
  "request_id": "",
  "code": 0,
  "msg": "",
  "data": {
    "code": "DVC001",
    "name": "core-sw-01"
  }
}
```

**响应示例（失败）**

```json
{
  "request_id": "",
  "code": -1,
  "msg": "code 为必填字段",
  "data": null
}
```

**业务规则与校验**

| 规则 | 处理方式 |
|------|----------|
| `code` 必填 | 后端 DTO `binding:"required"`。 |
| `base_ref_mode=warn` 是否为长期默认策略 | `[待确认: 后端负责人]`。 |
| `name/platform_code/status` 的业务必填性 | `[待确认: 产品负责人]`。 |

### 3.4 更新 Device V2 设备

**接口描述**：按设备编码更新 Device V2 设备主记录。

**请求信息**

| 项目 | 内容 |
|------|------|
| 接口URL | PUT `/device/v2/{code}?base_ref_mode=warn` |
| 请求方式 | PUT |
| Content-Type | application/json |
| 权限要求 | `[待确认: 安全负责人]` |

**请求参数**

| 参数名 | 类型 | 位置 | 必填 | 说明 | 示例 |
|--------|------|------|------|------|------|
| code | String | path | 是 | 设备编码 | DVC001 |
| name | String | body | 否 | 设备名称 | core-sw-01 |
| platform_code | String | body | 否 | 平台编码 | network |
| status | String | body | 否 | 状态，取值待确认 | active |
| labels | Object | body | 否 | 标签 | {} |
| attributes | Object | body | 否 | 动态属性 | {} |
| metadata | Object | body | 否 | 元数据 | {} |
| group_tags | Array[String] | body | 否 | 分组标签 | [] |

**请求示例**

```http
PUT /api/v1/device/v2/DVC001?base_ref_mode=warn HTTP/1.1
Host: oneops.example
Authorization: Bearer {token}
Content-Type: application/json
```

**Body 示例**

```json
{
  "name": "core-sw-01",
  "status": "active"
}
```

**响应示例（成功）**

```json
{
  "request_id": "",
  "code": 0,
  "msg": "",
  "data": {
    "code": "DVC001",
    "name": "core-sw-01"
  }
}
```

**响应示例（失败）**

```json
{
  "request_id": "",
  "code": -1,
  "msg": "更新 Device V2 设备失败",
  "data": null
}
```

**业务规则与校验**

| 规则 | 处理方式 |
|------|----------|
| 空字段不更新 | 后端 DTO 注释说明“按 code 更新，空字段不更新”。 |
| 哪些字段允许 UI/API 更新 | `[待确认: 安全负责人]`。 |

### 3.5 删除 Device V2 设备

**接口描述**：按设备编码删除 Device V2 设备。

**请求信息**

| 项目 | 内容 |
|------|------|
| 接口URL | DELETE `/device/v2/{code}` |
| 请求方式 | DELETE |
| Content-Type | application/json |
| 权限要求 | `[待确认: 安全负责人]` |

**请求参数**

| 参数名 | 类型 | 位置 | 必填 | 说明 | 示例 |
|--------|------|------|------|------|------|
| code | String | path | 是 | 设备编码 | DVC001 |

**请求示例**

```http
DELETE /api/v1/device/v2/DVC001 HTTP/1.1
Host: oneops.example
Authorization: Bearer {token}
Content-Type: application/json
```

**Body 示例**

```json
{}
```

**响应示例（成功）**

```json
{
  "request_id": "",
  "code": 0,
  "msg": "",
  "data": {
    "msg": "ok"
  }
}
```

**响应示例（失败）**

```json
{
  "request_id": "",
  "code": -1,
  "msg": "删除失败",
  "data": null
}
```

**业务规则与校验**

| 规则 | 处理方式 |
|------|----------|
| 后端存在可选 `RelationCleaner` | 删除时可能清理实体关系，正式行为待确认。 |
| 自动化默认不得删除真实设备 | 只允许在明确 story scope 中删除 clone fixture。`[待确认: 安全/测试负责人]` |
| 删除是硬删除、软删除还是关系清理后的实体删除 | `[待确认: 后端负责人]`。 |

### 3.6 启动 Device V2 store pipeline

**接口描述**：对一个或多个 Device V2 设备启动 store pipeline。

**请求信息**

| 项目 | 内容 |
|------|------|
| 接口URL | POST `/device/v2/store/start` |
| 请求方式 | POST |
| Content-Type | application/json |
| 权限要求 | `[待确认: 安全负责人]` |

**请求参数**

| 参数名 | 类型 | 位置 | 必填 | 说明 | 示例 |
|--------|------|------|------|------|------|
| codes | Array[String] | body | 是 | 设备编码列表 | ["DVC001"] |
| pipeline_template | String | body | 否 | pipeline 模板，空值时服务层使用默认值 | device_v2_minimal_store |
| options | Object | body | 否 | pipeline 选项；后端会补 `async=true` | {"async":true} |

**请求示例**

```http
POST /api/v1/device/v2/store/start HTTP/1.1
Host: oneops.example
Authorization: Bearer {token}
Content-Type: application/json
```

**Body 示例**

```json
{
  "codes": ["DVC001"],
  "pipeline_template": "device_v2_minimal_store",
  "options": {
    "async": true
  }
}
```

**响应示例（成功）**

```json
{
  "request_id": "",
  "code": 0,
  "msg": "",
  "data": {
    "task_id": "device-v2-store-xxxxxxxx",
    "current_stage": "store",
    "overall_status": "running",
    "stages": []
  }
}
```

**响应示例（失败）**

```json
{
  "request_id": "",
  "code": -1,
  "msg": "store service 未配置",
  "data": null
}
```

**业务规则与校验**

| 规则 | 处理方式 |
|------|----------|
| `codes` 必填 | 后端 DTO `binding:"required"`。 |
| 接口会触发任务 | 标记为 `task-trigger`，自动化不得默认执行。 |
| 幂等、重试、并发语义 | `[待确认: 后端负责人]`。 |

### 3.7 查询 Device V2 store task 结果

**接口描述**：查询 store task 详情、摘要、runs、observations、collection plans 和设备 latest DC2 结果。

**请求信息**

| 项目 | 内容 |
|------|------|
| 接口URL | 多个 GET 接口，见参数表 |
| 请求方式 | GET |
| Content-Type | application/json |
| 权限要求 | `[待确认: 安全负责人]` |

**请求参数**

| 参数名 | 类型 | 位置 | 必填 | 说明 | 示例 |
|--------|------|------|------|------|------|
| taskId | String | path | 是 | store task ID | device-v2-store-xxx |
| code | String | path | 是 | 仅 latest DC2 使用，设备编码 | DVC001 |
| page | Integer | query | 否 | runs/observations/plans 分页页码 | 1 |
| page_size | Integer | query | 否 | 每页数量 | 20 |
| device_code | String | query | 否 | 按设备编码过滤 | DVC001 |
| status | String | query | 否 | 按状态过滤 | failed |
| run_id | String | query | 否 | 按 run ID 过滤 | run-001 |
| sort_by | String | query | 否 | runs 支持 `created_at/priority`，observations 支持 `collected_at/priority` | priority |

**请求示例**

```http
GET /api/v1/device/v2/tasks/device-v2-store-xxx/runs?page=1&page_size=20 HTTP/1.1
Host: oneops.example
Authorization: Bearer {token}
Content-Type: application/json
```

**Body 示例**

```json
{}
```

**响应示例（成功）**

```json
{
  "request_id": "",
  "code": 0,
  "msg": "",
  "data": {
    "task_id": "device-v2-store-xxx",
    "list": [],
    "total": 0,
    "page": 1,
    "page_size": 20
  }
}
```

**响应示例（失败）**

```json
{
  "request_id": "",
  "code": -1,
  "msg": "task 不存在",
  "data": null
}
```

**业务规则与校验**

| 规则 | 处理方式 |
|------|----------|
| task 查询接口为只读 | 可作为自动化候选 read-only 接口。 |
| `sort_by` 非法 | 后端返回失败响应。 |
| `last-store-collection-dc2` 是否作为验收证据 | `[待确认: 产品/测试负责人]`。 |

### 3.8 Device V2 import batch

**接口描述**：管理多次导入批次，包括创建、上传、校验、应用、重试、记录更新、查询和清理。

**请求信息**

| 项目 | 内容 |
|------|------|
| 接口URL | `/device/v2/import/**` |
| 请求方式 | GET/POST |
| Content-Type | application/json 或 multipart/form-data |
| 权限要求 | `[待确认: 安全负责人]` |

**请求参数**

| 参数名 | 类型 | 位置 | 必填 | 说明 | 示例 |
|--------|------|------|------|------|------|
| batch_id | String | body/path/query | 视接口而定 | 批次 ID | device-v2-import-xxx |
| import_pass | String | body/path | 创建批次和模板接口必填 | 导入 pass | pass_1_base |
| namespace | String | body/query | 否 | 命名空间 | infra/device |
| rows | Array[Object] | body | 上传 JSON 时必填 | 导入行 | [] |
| only_pending | Boolean | body | 否 | 仅校验 pending 记录 | true |
| only_validated | Boolean | body | 否 | 仅应用已校验记录 | true |
| record_ids | Array[Number] | body | 否 | 指定记录 ID | [1] |
| row_nos | Array[Number] | body | 否 | 指定行号 | [1] |
| entity_codes | Array[String] | body | 否 | 指定实体编码 | ["DVC001"] |
| auto_start_pipeline | Boolean | body | 否 | 应用后自动启动 pipeline | false |
| dry_run | Boolean | body | 否 | purge 预览，不实际删除 | true |

**请求示例**

```http
POST /api/v1/device/v2/import/batches HTTP/1.1
Host: oneops.example
Authorization: Bearer {token}
Content-Type: application/json
```

**Body 示例**

```json
{
  "import_pass": "pass_1_base",
  "namespace": "infra/device",
  "mode": "dry_run",
  "source_file": "device-v2.xlsx",
  "created_by": "operator"
}
```

**响应示例（成功）**

```json
{
  "request_id": "",
  "code": 0,
  "msg": "",
  "data": {
    "batch_id": "device-v2-import-xxx"
  }
}
```

**响应示例（失败）**

```json
{
  "request_id": "",
  "code": -1,
  "msg": "import_pass 不能为空",
  "data": null
}
```

**业务规则与校验**

| 规则 | 处理方式 |
|------|----------|
| `apply`、`retry`、`purge` 属于写入或任务触发 | 自动化不得默认执行。 |
| `purge` 支持 `dry_run` | 是否允许真实清理待安全确认。 |
| import batch 与 ingest task 的长期边界 | `[待确认: 产品/后端负责人]`。 |

### 3.9 Device V2 ingest task

**接口描述**：新 Device V2 入库框架，支持能力查询、Excel 模板下载、任务提交、Excel 上传、任务查询。

**请求信息**

| 项目 | 内容 |
|------|------|
| 接口URL | `/device/v2/ingest/**` |
| 请求方式 | GET/POST |
| Content-Type | application/json 或 multipart/form-data |
| 权限要求 | `[待确认: 安全负责人]` |

**请求参数**

| 参数名 | 类型 | 位置 | 必填 | 说明 | 示例 |
|--------|------|------|------|------|------|
| source | String | body | 否 | 数据来源，业务必填性待确认 | manual |
| requested_by | String | body/form | 否 | 请求人 | operator |
| devices | Array[DeviceV2IngestDevice] | body | 是 `[待确认]` | 入库设备数组 | [] |
| excel | File | form | 是 | Excel 上传字段名 | device_v2.xlsx |
| taskId | String | path | 是 | 任务 ID | ingest-task-xxx |
| limit | Integer | query | 否 | 最近任务数量，默认 5 | 5 |

**请求示例**

```http
POST /api/v1/device/v2/ingest/tasks HTTP/1.1
Host: oneops.example
Authorization: Bearer {token}
Content-Type: application/json
```

**Body 示例**

```json
{
  "source": "manual",
  "requested_by": "operator",
  "devices": [
    {
      "code": "DVC001",
      "name": "core-sw-01",
      "platform_code": "network",
      "status": "active",
      "access_points": [
        {
          "plane": "in_band",
          "ip": "10.0.0.1",
          "login_method": "ssh",
          "login_port": 22,
          "credential_ref": "cred-linux-prod"
        }
      ]
    }
  ]
}
```

**响应示例（成功）**

```json
{
  "request_id": "",
  "code": 0,
  "msg": "",
  "data": {
    "task_id": "ingest-task-xxx",
    "status": "completed",
    "framework_version": "v0-minimal",
    "source": "manual",
    "execution_enabled": true,
    "device_count": 1,
    "devices": [],
    "result": {},
    "stages": []
  }
}
```

**响应示例（失败）**

```json
{
  "request_id": "",
  "code": -1,
  "msg": "device v2 ingest 服务未配置",
  "data": null
}
```

**业务规则与校验**

| 规则 | 处理方式 |
|------|----------|
| Excel 上传字段名必须是 `excel` | 后端 `ctx.FormFile("excel")`。 |
| 返回任务必须包含 `task_id`、`status`、`stages`、`devices` | 前端 `assertIngestTask` 校验。 |
| 凭据引用字段是否允许从前端提交 | `[待确认: 安全负责人]`。 |

## 4. 接口汇总表

| 序号 | 功能 | 请求方式 | URL | 说明 |
|------|------|----------|-----|------|
| 1 | 查询设备列表 | GET | `/device/v2/list` | 前端 `listDeviceV2Req`，后端 `DeviceV2API.List`。 |
| 2 | 查询设备详情 | GET | `/device/v2/{code}` | 前端 `getDeviceV2Req`，后端 `DeviceV2API.GetByCode`。 |
| 3 | 创建设备 | POST | `/device/v2` | 前端 `createDeviceV2Req`，后端 `DeviceV2API.Create`。 |
| 4 | 更新设备 | PUT | `/device/v2/{code}` | 前端 `updateDeviceV2Req`，后端 `DeviceV2API.Update`。 |
| 5 | 删除设备 | DELETE | `/device/v2/{code}` | 前端 `deleteDeviceV2Req`，后端 `DeviceV2API.Delete`。 |
| 6 | 查询接口镜像 | GET | `/device/v2/{code}/interfaces` | 后端 `DeviceV2API.ListInterfacesByDeviceCode`。 |
| 7 | 查询变更历史 | GET | `/device/v2/{code}/change-history` | 前端 `listDeviceV2ChangeHistoryReq`，后端 `DeviceV2API.ListChangeHistory`。 |
| 8 | 更新变更历史状态 | POST | `/device/v2/{code}/change-history/{id}/status` | 前端 `updateDeviceV2ChangeHistoryStatusReq`，后端 `DeviceV2API.UpdateChangeHistoryStatus`。 |
| 9 | 查询设备状态 | GET | `/device/v2/{code}/status` | 后端 `DeviceV2API.GetStatus`。 |
| 10 | 查询 store readiness | GET | `/device/v2/{code}/store-readiness` | 后端 `DeviceV2API.GetStoreReadiness`。 |
| 11 | 查询 latest DC2 | GET | `/device/v2/{code}/last-store-collection-dc2` | 前端 `getDeviceV2LastStoreCollectionDc2Req`，后端 `DeviceV2API.GetLastStoreCollectionDC2`。 |
| 12 | 查询网络概览 | GET | `/device/v2/{code}/network-overview` | 后端 `DeviceV2API.GetNetworkOverview`。 |
| 13 | 启动 store pipeline | POST | `/device/v2/store/start` | 前端 `startDeviceV2StorePipelineReq`，后端 `DeviceV2API.StartStorePipeline`。 |
| 14 | 重试 store pipeline | POST | `/device/v2/store/retry` | 前端 `retryDeviceV2StorePipelineReq`，后端 `DeviceV2API.RetryStorePipeline`。 |
| 15 | 查询 store task | GET | `/device/v2/tasks/{taskId}` | 前端 `getDeviceV2StoreTaskReq`，后端 `DeviceV2API.GetPipelineTask`。 |
| 16 | 查询 task summary | GET | `/device/v2/tasks/{taskId}/summary` | 前端 `getDeviceV2StoreTaskSummaryReq`，后端 `DeviceV2API.GetTaskSummary`。 |
| 17 | 查询 collection plans | GET | `/device/v2/tasks/{taskId}/collection-plans` | 前端 `listDeviceV2StoreCollectionPlansReq`，后端 `DeviceV2API.ListTaskCollectionPlans`。 |
| 18 | 查询 task runs | GET | `/device/v2/tasks/{taskId}/runs` | 前端 `listDeviceV2StoreRunsReq`，后端 `DeviceV2API.ListTaskRuns`。 |
| 19 | 查询 task observations | GET | `/device/v2/tasks/{taskId}/observations` | 前端 `listDeviceV2StoreObservationsReq`，后端 `DeviceV2API.ListTaskObservations`。 |
| 20 | 当前 schema | GET | `/device/v2/schema/current` | 前端 `getDeviceV2SchemaCurrentReq`，后端 `DeviceV2API.GetSchemaCurrent`。 |
| 21 | schema 预检查 | POST | `/device/v2/schema/precheck` | 前端 `precheckDeviceV2SchemaReq`，后端 `DeviceV2API.PrecheckSchema`。 |
| 22 | 保存 schema | POST | `/device/v2/schema` | 前端 `saveDeviceV2SchemaReq`，后端 `DeviceV2API.SaveSchema`。 |
| 23 | base reference check | POST | `/device/v2/base-reference-check` | 后端 `DeviceV2API.CheckBaseReferences`。 |
| 24 | 从 V1 同步到 V2 | POST | `/device/v2/sync-from-v1` | 前端 `syncDeviceV2FromV1Req`，后端 `DeviceV2API.SyncFromV1`。 |
| 25 | 从 V2 同步到 V1 | POST | `/device/v2/sync-to-v1` | 前端 `syncDeviceV2ToV1Req`，后端 `DeviceV2API.SyncToV1`。 |
| 26 | 创建 import batch | POST | `/device/v2/import/batches` | 后端 `DeviceV2API.CreateImportBatch`。 |
| 27 | 上传 import batch | POST | `/device/v2/import/batches/{batchId}/upload` | 后端 `DeviceV2API.UploadImportBatch`。 |
| 28 | 校验 import batch | POST | `/device/v2/import/batches/{batchId}/validate` | 后端 `DeviceV2API.ValidateImportBatch`。 |
| 29 | 应用 import batch | POST | `/device/v2/import/batches/{batchId}/apply` | 后端 `DeviceV2API.ApplyImportBatch`。 |
| 30 | 重试 import batch | POST | `/device/v2/import/batches/{batchId}/retry` | 后端 `DeviceV2API.RetryImportBatch`。 |
| 31 | 更新 import records | POST | `/device/v2/import/batches/{batchId}/records/update` | 后端 `DeviceV2API.UpdateImportBatchRecords`。 |
| 32 | 查询 import batches | GET | `/device/v2/import/batches` | 后端 `DeviceV2API.ListImportBatches`。 |
| 33 | 清理 import batches | POST | `/device/v2/import/batches:purge` | 后端 `DeviceV2API.PurgeImportBatches`。 |
| 34 | 查询 import summary | GET | `/device/v2/import/batches/{batchId}/summary` | 后端 `DeviceV2API.GetImportBatchSummary`。 |
| 35 | 查询 import records | GET | `/device/v2/import/batches/{batchId}/records` | 后端 `DeviceV2API.ListImportBatchRecords`。 |
| 36 | 查询 anchor conflicts | GET | `/device/v2/import/anchor-conflicts` | 后端 `DeviceV2API.ListImportAnchorConflicts`。 |
| 37 | 查询 anchor basis | GET | `/device/v2/import/anchor-basis` | 后端 `DeviceV2API.GetImportAnchorBasis`。 |
| 38 | 获取 import template | GET | `/device/v2/import/templates/{importPass}` | 后端 `DeviceV2API.GetImportTemplate`。 |
| 39 | ingest capabilities | GET | `/device/v2/ingest/capabilities` | 前端 `getDeviceV2IngestCapabilitiesReq`，后端 `DeviceV2IngestAPI.Capabilities`。 |
| 40 | 下载 ingest Excel 模板 | GET | `/device/v2/ingest/template/excel` | 前端 `buildDeviceV2IngestExcelTemplateURL`，后端 `DeviceV2IngestAPI.DownloadExcelTemplate`。 |
| 41 | 查询 ingest tasks | GET | `/device/v2/ingest/tasks` | 前端 `listDeviceV2IngestTasksReq`，后端 `DeviceV2IngestAPI.ListTasks`。 |
| 42 | 提交 ingest task | POST | `/device/v2/ingest/tasks` | 前端 `submitDeviceV2IngestTaskReq`，后端 `DeviceV2IngestAPI.SubmitTask`。 |
| 43 | 上传 ingest Excel | POST | `/device/v2/ingest/tasks/upload` | 前端 `uploadDeviceV2IngestExcelReq`，后端 `DeviceV2IngestAPI.UploadTask`。 |
| 44 | 查询 ingest task | GET | `/device/v2/ingest/tasks/{taskId}` | 前端 `getDeviceV2IngestTaskReq`，后端 `DeviceV2IngestAPI.GetTask`。 |

## 5. 待确认事项

| 序号 | 待确认内容 | 影响接口 | 状态 |
|------|------------|----------|------|
| 1 | API 基准地址是否统一为 `/api/v1` | 全部接口 | 待确认 |
| 2 | Device V2 认证方式、角色权限、tenant/device 边界 | 全部接口 | 待确认 |
| 3 | `base_ref_mode=warn` 是否为创建/更新的正式默认策略 | 创建、更新 | 待确认 |
| 4 | 删除设备是硬删除、软删除还是关系清理后的实体删除 | 删除设备 | 待确认 |
| 5 | 自动化是否允许执行删除、purge、sync、store/start、ingest submit/upload | 写入和任务触发接口 | 待确认 |
| 6 | `store-readiness` 的正式业务判定和前端 wrapper 是否需要补齐 | store readiness | 待确认 |
| 7 | `last-store-collection-dc2` 是否可以作为验收证据 | latest DC2、store task | 待确认 |
| 8 | import batch 与 ingest task 两套入库接口的长期边界 | import、ingest | 待确认 |
| 9 | `validate` 是否会持久化状态，副作用应标为 read-only 还是 write | import validate、schema precheck | 待确认 |
| 10 | 凭据引用字段是否允许从前端提交和展示 | ingest task、store/start、设备创建/更新 | 待确认 |
| 11 | 哪些源码接口属于长期对外契约，哪些只是 migration/debug/preview/临时辅助入口 | schema/sync/base-reference/import/store/change-history 等 | 待人工确认 |
