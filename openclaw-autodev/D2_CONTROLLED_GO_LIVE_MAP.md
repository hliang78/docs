# D2 前后端上线干货版

更新时间：2026-05-13

文档角色：辅助文档。字段主表请以 `/Users/huangliang/project/OneOPS-ALL/docs/openclaw-autodev/D2_INGEST_BASE_FIELD_TABLE.md` 为准；本文用于理解功能、上线边界和开发控制思路。

目标：把 D2 到底做什么、有哪些字段、字段从哪里来又到哪里去、哪些能上线哪些不能上线讲清楚。后续 AI 自动开发必须按这份文档审需求、审代码、审证据。

## 1. 功能

### 1.1 D2 是什么

D2 是 Device V2 的生产化入口，目前由两类页面和一组后端 API 组成：

- 入库工作台：把 Excel 或手工设备清单变成后端 Device V2 ingest task。
- 清册管理页：展示和管理已经进入 Device V2 的设备清册。
- 后端契约：提供 Device V2 list/detail/create/update/delete 和 ingest capability/template/submit/upload/list/detail。

一句话：D2 负责把设备从“待导入清单”推进到“Device V2 清册”，并让页面能看到真实入库结果、真实纳管状态、真实后端错误。

### 1.2 入库工作台

前端页面：

- 路由：`/device/device-v2-ingest-pipeline-redesign`
- 文件：`/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/views/device/DeviceV2IngestPipelineRedesign.vue`

后端 API：

- `GET /api/v1/device/v2/ingest/capabilities`
- `GET /api/v1/device/v2/ingest/template/excel`
- `POST /api/v1/device/v2/ingest/tasks`
- `POST /api/v1/device/v2/ingest/tasks/upload`
- `GET /api/v1/device/v2/ingest/tasks`
- `GET /api/v1/device/v2/ingest/tasks/:taskId`

它应该做：

- 查看后端是否具备 D2 入库能力。
- 下载 `.xlsx` 模板。
- 上传 `.xlsx` 清单，multipart 字段名必须是 `excel`。
- 创建入库任务。
- 展示最近任务。
- 展示任务阶段。
- 展示每台设备的执行结果。
- 把可纳管设备交给清册管理页继续查看。

它不应该做：

- 不支持 CSV 生产上传。
- 不创建本地假 task。
- 不用前端静态数据冒充任务结果。
- 不在后端失败时显示成功。
- 不把坏 JSON、坏响应、空响应当成正常空数据。

### 1.3 清册管理页

前端页面：

- 路由：`/device/device-v2-management-redesign`
- 文件：`/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/views/device/DeviceV2ManagementRedesign.vue`

后端 API：

- `GET /api/v1/device/v2/list`
- `GET /api/v1/device/v2/:code`
- `POST /api/v1/device/v2`
- `PUT /api/v1/device/v2/:code`
- `DELETE /api/v1/device/v2/:code`

它应该做：

- 分页展示 Device V2 清册。
- 支持真实后端筛选。
- 支持查看详情。
- 支持已确认的创建、编辑、删除。
- 显示最近入库任务。
- 从入库任务跳转时按 `keyword`、`codes`、`manage_status` 聚焦设备。

它不应该做：

- 不用当前页数据冒充全局统计。
- 不开放未确认的筛选 facets。
- 不开放未确认的批量动作。
- 不自己推断后端没有返回的状态。

### 1.4 当前真实状态

已经具备上线候选基础：

- 后端 D2BE-006 已确认字段契约。
- 前端 DVR-007 已按真实本地后端做过浏览器验证。
- 前端上传已收敛为 `.xlsx` only。
- 前端未确认动作已隐藏或禁用。
- `npm run typecheck:d2` 曾通过。
- `go test ./app/device/v2/...` 曾通过。

还没到正式生产入口：

- 正式菜单入口替换还需要人批准。
- 权限、租户、认证、生产配置、部署、回滚策略还需要人批准。
- 部分文档仍有旧 blocker 文案，需要同步。
- 源/区域/采集/保存视图等 facets 没有完整生产后端契约。

## 2. 字段

### 2.1 设备身份字段

这些字段回答：这台设备是谁？

| 字段 | 类型 | 含义 | 当前口径 |
| --- | --- | --- | --- |
| `code` | string | 设备唯一编码 | 核心主键，列表 row key，详情和更新删除都按它定位 |
| `name` | string | 设备名称 | 展示名；后端 detail/list 必须能返回 |
| `platform_code` | string | 平台、厂商、模型或设备归属编码 | 来自实体字段、projection 或 `attributes.platform_code` |
| `status` | string | 设备基础状态 | ingest 接受 `active`、`inactive`、`planned`、`retired` 或空值 |

记忆：身份四件套是 `code / name / platform_code / status`。

### 2.2 设备纳管字段

这些字段回答：这台设备能不能被管起来？

| 字段 | 类型 | 含义 | 当前口径 |
| --- | --- | --- | --- |
| `manage_status` | string | 设备纳管或管理阶段状态 | 后端值优先，FE 只展示和过滤，不凭空改写 |
| `manageable` | boolean | 是否具备纳管条件 | 后端派生布尔值，FE 可用于“可纳管/未就绪”显示 |
| `lifecycle_stage` | string | 生命周期阶段 | 后端实体阶段字段 |
| `stage_status` | string | 阶段状态 | 后端实体阶段状态字段 |

`manage_status` 可能出现的值族：

- 实体纳管状态：`pending`、`success`
- store readiness 状态：`unknown`、`pending`、`ready`、`unready`
- ingest 属性标签：`manageable`、`registered_only`、`failed`

重要规则：

- `manageable` 是“是否可纳管”的直接布尔判断。
- `manage_status` 是“纳管状态/阶段”的文本状态。
- FE 可以把二者组合成人类可读文案，但不能用别的字段重新发明状态。

### 2.3 设备扩展字段

这些字段回答：设备还有哪些业务信息？

| 字段 | 类型 | 含义 | 当前口径 |
| --- | --- | --- | --- |
| `labels` | object string map | 标签 | 用于轻量分类和标签筛选 |
| `attributes` | object | 属性 | 放 IP、凭据引用、管理路径、SN、地址等结构化扩展信息 |
| `metadata` | object | 元数据 | 放来源、批次、导入上下文等系统信息 |
| `group_tags` | string[] | 分组标签 | 设备分组、业务分组、展示标签 |

重要规则：

- 这四个字段来自后端 JSON projection。
- 后端已经要求坏 JSON 显式报错。
- FE 不允许把坏 JSON 静默变成 `{}` 或 `[]`。

### 2.4 清册列表查询字段

Endpoint：`GET /api/v1/device/v2/list`

确认可用：

| 字段 | 来源 | 用途 |
| --- | --- | --- |
| `page` | FE 分页控件 | 当前页 |
| `page_size` | FE 分页控件 | 每页数量 |
| `codes` | 入库任务交接、批量聚焦 | 按设备编码列表查询，逗号分隔 |
| `keyword` | 搜索框、路由 query | 按 code/name/IP/profile 等常用字段模糊查询 |
| `name` | 高级筛选 | 按设备名模糊查询 |
| `ip` | 高级筛选 | 按 in-band/out-band/management/address 模糊查询 |
| `label_key` | 高级筛选 | 标签 key |
| `label_value` | 高级筛选 | 标签 value，不能脱离 `label_key` 单独使用 |
| `attribute_key` | 高级筛选 | 属性 key |
| `attribute_value` | 高级筛选 | 属性 value，不能脱离 `attribute_key` 单独使用 |
| `manage_status` | 状态筛选、入库交接 | 精确匹配后端纳管状态 |
| `management_path` | 管理域筛选 | 按 management/org path 前缀匹配 |

后端有但前端产品映射未完全确认：

- `location_node_code`
- `location_path_prefix`
- `region_code`
- `site_code`
- `rack_code`

当前不能生产开放的筛选：

- source filter：来源筛选没有确认后端契约。
- collection filter：采集筛选没有确认后端契约。
- saved-view count facets：保存视图的非 total 计数没有确认后端聚合契约。
- area/source/collection 这类 UI 概念不能用当前页数据伪造全局结果。

### 2.5 清册响应字段

Endpoint：`GET /api/v1/device/v2/list`

响应 envelope：

| 字段 | 类型 | 含义 |
| --- | --- | --- |
| `list` | `DeviceV2Item[]` | 当前页设备 |
| `total` | number | 后端真实总数 |
| `page` | number | 后端确认页码 |
| `page_size` | number | 后端确认每页数量 |

`list[]` 设备字段：

| 字段 | 含义 |
| --- | --- |
| `id` | 前端类型里存在，但核心业务定位仍看 `code` |
| `code` | 设备唯一编码 |
| `name` | 设备名称 |
| `platform_code` | 平台编码 |
| `status` | 基础状态 |
| `lifecycle_stage` | 生命周期阶段 |
| `stage_status` | 阶段状态 |
| `manage_status` | 纳管状态 |
| `manageable` | 是否可纳管 |
| `labels` | 标签 |
| `attributes` | 属性 |
| `metadata` | 元数据 |
| `group_tags` | 分组标签 |
| `created_at` | 创建时间 |
| `updated_at` | 更新时间 |

### 2.6 清册写入字段

Create：`POST /api/v1/device/v2`

| 字段 | 必填 | 含义 |
| --- | --- | --- |
| `code` | 是 | 设备唯一编码 |
| `name` | 否 | 设备名称 |
| `platform_code` | 否 | 平台编码 |
| `status` | 否 | 基础状态 |
| `labels` | 否 | 标签 |
| `attributes` | 否 | 属性 |
| `metadata` | 否 | 元数据 |
| `group_tags` | 否 | 分组标签 |

Update：`PUT /api/v1/device/v2/:code`

- 路径里的 `:code` 决定更新哪台设备。
- body 字段同 create，但 `code` 不在 body 里改。
- 空字段按后端更新语义处理，不能由 FE 猜测“清空”或“不更新”。

Delete：`DELETE /api/v1/device/v2/:code`

- 路径里的 `:code` 决定删除哪台设备。
- 前端必须二次确认。

### 2.7 入库 capability 字段

Endpoint：`GET /api/v1/device/v2/ingest/capabilities`

| 字段 | 含义 |
| --- | --- |
| `framework_version` | 当前入库框架版本，目前后端口径为 `v0-minimal` |
| `execution_enabled` | 是否启用真实 DB-backed 执行器 |
| `supported_sources` | 支持的 source 枚举 |
| `task_statuses` | 支持的任务状态 |
| `default_stages` | 默认阶段列表 |

### 2.8 入库提交字段

JSON submit：`POST /api/v1/device/v2/ingest/tasks`

| 字段 | 必填 | 含义 |
| --- | --- | --- |
| `source` | 是 | 来源，必须是后端支持值 |
| `requested_by` | 否 | 请求人 |
| `devices` | 是 | 待入库设备列表，不能为空 |

`source` 确认值：

- `manual_api`
- `excel_upload`
- `reference_payload`
- `future_pipeline`

Excel upload：`POST /api/v1/device/v2/ingest/tasks/upload`

| 字段 | 含义 |
| --- | --- |
| multipart `excel` | 上传文件字段名，必须叫 `excel` |
| 文件格式 | `.xlsx` |
| 模板文件 | `device_v2_ingest_template.xlsx` |
| sheet | `devices` |

### 2.9 入库设备字段

`devices[]` 单台设备字段：

| 字段 | 含义 |
| --- | --- |
| `code` | 设备编码 |
| `biz_code` | 业务编码，可用于识别 |
| `biz_name` | 业务名称 |
| `platform` | 平台文本 |
| `platform_code` | 平台编码 |
| `status` | 基础状态 |
| `credential_ref_in_band` | 带内凭据引用 |
| `credential_ref_out_band` | 带外凭据引用 |
| `snmp_credential_ref` | SNMP 凭据引用 |
| `winrm_credential_ref` | WinRM 凭据引用 |
| `winrm_port` | WinRM 端口 |
| `rack_position` | 机柜位置 |
| `labels` | 标签 |
| `attributes` | 属性 |
| `metadata` | 元数据 |
| `group_tags` | 分组标签 |

纳管判断重点：

- 管理地址类字段通常在 `attributes` 中。
- 凭据引用类字段影响是否可纳管。
- 后端最终给出 `manageable` 和 `manage_status`。

### 2.10 入库任务字段

`DeviceV2IngestTask`：

| 字段 | 含义 |
| --- | --- |
| `task_id` | 任务 ID，形如 `ingest-task-<uuid>` |
| `status` | 任务状态 |
| `current_stage` | 当前阶段 |
| `framework_version` | 入库框架版本 |
| `source` | 任务来源 |
| `requested_by` | 请求人 |
| `execution_enabled` | 是否启用真实执行器 |
| `device_count` | 设备数量 |
| `message` | 任务消息 |
| `devices` | 规范化后的设备列表 |
| `result` | 任务结果 |
| `stages` | 阶段列表 |
| `created_at` | 创建时间 |
| `updated_at` | 更新时间 |

任务状态：

- `prepared`
- `completed`
- `failed`

默认阶段：

- `request_received`
- `canonical_device_payload`
- `validator_slot`
- `execution_adapter`

阶段状态：

- `completed`
- `placeholder`
- `blocked`
- `failed`

### 2.11 入库结果字段

`result.validation.issues[]`：

| 字段 | 含义 |
| --- | --- |
| `row_no` | Excel 或输入行号 |
| `device_code` | 设备编码 |
| `field` | 出错字段 |
| `message` | 错误信息 |

`result.execution.device_results[]`：

| 字段 | 含义 |
| --- | --- |
| `device_code` | 设备编码 |
| `action` | 执行动作 |
| `status` | 执行状态 |
| `matched_by` | 命中的识别字段 |
| `message` | 结果消息 |
| `manageable` | 是否可纳管 |
| `manage_status` | 纳管结果状态 |

`action` 值：

- `created`
- `updated`
- `failed`
- `skipped`
- `blocked`

`status` 值：

- `completed`
- `failed`
- `skipped`
- `blocked`

`matched_by` 可能值：

- `code`
- `biz_code`
- `sn`
- `asset_number`
- `in_band_ip`
- `out_band_ip`
- `hostname`

`manage_status` 结果口径：

- 正常成功：`manageable` 或 `registered_only`
- 单设备失败：`failed`
- disabled executor / 防御路径：`unknown` 或空

## 3. 字段来源和去处

### 3.1 清册查询流

```text
用户在清册页输入筛选
  -> FE buildListParams()
  -> GET /api/v1/device/v2/list
  -> BE DeviceV2ListReq
  -> BE DeviceV2Filter
  -> DB / entity projection / JSON projection
  -> BE DeviceV2Item DTO
  -> FE DeviceV2Item
  -> 表格、详情、统计、跳转聚焦
```

字段流向：

| 字段 | 来源 | 去处 |
| --- | --- | --- |
| `page/page_size` | 前端分页控件 | 后端分页查询，再回显到分页器 |
| `keyword` | 搜索框或 route query | 后端模糊查询 code/name/IP/profile |
| `codes` | 入库结果交接、批量选择 | 后端按 code 聚焦设备 |
| `manage_status` | 状态筛选或入库交接 | 后端精确过滤，前端展示状态标签 |
| `total` | 后端 list 响应 | 只能用于真实总数，不能由 FE 当前页计算替代 |
| `list` | 后端 list 响应 | 表格、详情入口、选择态 |

### 3.2 清册设备字段流

```text
DB entity / projection
  -> 后端解码 labels/attributes/metadata/extra
  -> 后端合成 DeviceV2Item
  -> 前端 assertDeviceV2ListResp()
  -> DeviceV2ManagementRedesign.vue 渲染
```

字段流向：

| 字段 | 来源 | 去处 |
| --- | --- | --- |
| `code` | `entity_instance.entity_id` / projection code | row key、详情 API、更新 API、删除 API、入库交接 |
| `name` | entity name 或 `attributes.name` projection | 表格标题、详情标题、搜索命中 |
| `platform_code` | entity/projection 或 `attributes.platform_code` | 平台列、详情基础信息 |
| `status` | source device status | 状态列、详情基础信息 |
| `lifecycle_stage` | entity stage 字段 | 生命周期展示 |
| `stage_status` | entity stage status 字段 | 阶段状态展示 |
| `manage_status` | entity `manage_status` 优先，否则 attributes/readiness | 筛选、状态标签、入库交接判断 |
| `manageable` | 后端从 explicit attribute 或 manage status/readiness 派生 | 可纳管标签、可纳管设备聚焦 |
| `labels` | JSON projection | 标签展示和标签筛选 |
| `attributes` | JSON projection | IP、管理路径、凭据引用、纳管辅助信息 |
| `metadata` | JSON projection | 批次、来源、导入上下文 |
| `group_tags` | extra/projection | 分组标签展示和编辑 |

### 3.3 入库上传流

```text
.xlsx 文件
  -> FE hidden file input accept=".xlsx"
  -> FormData.append("excel", file)
  -> POST /api/v1/device/v2/ingest/tasks/upload
  -> BE xlsx.OpenReaderAt
  -> devices sheet
  -> normalized DeviceV2IngestDevice[]
  -> validation
  -> execution_adapter
  -> DB-backed upsert 或 blocked executor
  -> persisted ingest task
  -> FE 展示 task/stages/result
```

字段流向：

| 字段 | 来源 | 去处 |
| --- | --- | --- |
| Excel `devices` sheet | 用户上传模板 | 后端解析成 `devices[]` |
| `code/biz_code/sn/ip/hostname` | Excel 行或 JSON payload | 设备识别、匹配、生成 `matched_by` |
| `credential_ref_*` | Excel 行或 payload | 后端判断纳管条件 |
| `attributes` | Excel 行或 payload | 写入 Device V2 projection，并参与管理路径/IP 等展示 |
| `metadata` | Excel 行、source、批次上下文 | 后续追溯来源和批次 |
| `group_tags` | Excel 行或 payload | 写入分组标签 |

### 3.4 入库任务流

```text
FE submit/upload
  -> BE 创建 task_id
  -> BE 生成 stages
  -> BE validation
  -> BE execution
  -> BE persist task devices/result/stages
  -> FE list/detail recent tasks
  -> FE 可跳转清册页聚焦设备
```

字段流向：

| 字段 | 来源 | 去处 |
| --- | --- | --- |
| `task_id` | 后端生成 | 最近任务列表、详情刷新、批次追溯、管理页最近入库 |
| `status` | 后端 deriveTaskStatus | 任务状态标签、轮询/刷新判断 |
| `current_stage` | 后端阶段推进 | 页面当前阶段展示 |
| `framework_version` | capability/task 后端返回 | 页面展示，判断当前框架能力 |
| `execution_enabled` | 后端 runtime 能力 | 页面提示真实执行或能力未就绪 |
| `device_count` | 后端任务设备数量 | 页面统计 |
| `stages` | 后端默认阶段和执行结果 | 阶段进度条/阶段列表 |
| `result.validation.issues` | 后端校验 | 错误列表，不允许继续伪成功 |
| `result.execution.device_results` | 后端执行器 | 每台设备结果、可纳管统计、跳转清册聚焦 |

### 3.5 入库到清册交接流

```text
result.execution.device_results[]
  -> 提取 device_code
  -> 按 manageable/manage_status 分组
  -> 清册页 route query: keyword/codes/manage_status
  -> GET /api/v1/device/v2/list
  -> 展示真实清册设备
```

交接规则：

- 只用后端返回的 `device_code` 定位设备。
- 可纳管设备优先看 `manageable === true`。
- `manage_status` 只作为后端状态，不由 FE 改写。
- 跳转到清册页后必须重新查真实 list，不能直接把 task result 当清册数据。

### 3.6 写入和回流

```text
清册 create/update/delete
  -> Device V2 后端 API
  -> DB entity/projection/change event
  -> 重新 GET list/detail
  -> FE 展示后端确认后的结果
```

规则：

- create/update/delete 成功后要重新读后端。
- 不用本地 optimistic 数据当最终状态。
- delete 必须二次确认。
- 失败必须展示错误。

## 4. 限制和边界

### 4.1 已确认可以做

前端可以做：

- 使用真实 D2 list API 展示清册。
- 使用 `keyword`、`codes`、`manage_status` 等已确认筛选。
- 展示真实 `total/list/page/page_size`。
- 上传 `.xlsx` 文件到 ingest upload API。
- 下载 `.xlsx` 模板。
- 展示真实 ingest task、stages、result。
- 对 create/update/delete 做基础 UI，但必须严格按后端响应处理。
- 隐藏或禁用未确认动作。

后端可以做：

- list/detail/create/update/delete。
- ingest capability/template/submit/upload/list/detail。
- JSON decode 显式失败。
- 无效 filter 显式失败。
- 空 devices、非法 source、坏 Excel 显式失败。
- 返回真实 task/result/stage。

AI 可以做：

- 在允许目录内改代码。
- 补字段契约。
- 补前后端类型。
- 补页面真实 API 对接。
- 补测试。
- 补 evidence。
- 修复 typecheck/test 暴露的问题。

### 4.2 当前不能直接做

前端不能直接上线开放：

- CSV 生产上传。
- source filter。
- collection filter。
- saved-view 非 total 计数。
- area/source/collection 等没有后端聚合契约的 facets。
- 批量绑定标签。
- 接入监控。
- 绑定凭证。
- 查看变更。
- V1 同步。
- 批量采集验证。
- 批量补充资料。
- 同步采集目标。

这些动作不是永远不能做，而是必须先明确：

- 对应 API 是哪个。
- payload 是什么。
- 成功响应是什么。
- 失败响应是什么。
- 是否异步。
- 是否可重试。
- 权限如何控制。
- 审计如何记录。

### 4.3 数据边界

禁止：

- 用 mock 数据进入上线候选。
- 用 fallback 静默吞掉后端错误。
- 用当前页数据伪造全局统计。
- 用空对象替代坏 JSON。
- 用本地 task 替代后端 task。
- 用 task result 直接冒充清册 list。
- 用 FE 自己推断替代后端 `manageable/manage_status`。

必须：

- 后端错误要暴露给 FE。
- FE 错误要显示给用户。
- 所有上线字段都要有来源。
- 所有页面动作都要有后端契约。
- 所有 AI 产物都要有 evidence。

### 4.4 上线边界

AI 自动开发不等于 AI 自动上线。

AI 可以推进到：

- 代码完成。
- 类型检查通过。
- 单元测试通过。
- 浏览器 smoke 通过。
- evidence 记录完整。
- 文档契约更新。
- 上线候选 ready。

人必须批准：

- 正式菜单入口替换。
- 生产配置变更。
- 认证、权限、租户策略。
- DB migration。
- commit。
- push。
- merge。
- deploy。
- rollback 执行。
- 真实生产数据修复。

### 4.5 前后端职责边界

d2-fe：

- 归属 `/Users/huangliang/project/OneOPS-ALL/OneOPS-UI`
- 主要文件：
  - `src/views/device/DeviceV2IngestPipelineRedesign.vue`
  - `src/views/device/DeviceV2ManagementRedesign.vue`
  - `src/views/device/device-v2-import/**`
  - `src/api/device/device-v2.ts`
  - `src/api/device/device-v2-ingest.ts`

d2-be：

- 归属 `/Users/huangliang/project/OneOPS-ALL/OneOPS`
- 主要文件：
  - `app/device/v2/**`
  - `app/device/v2/ingest/**`
  - `docs/device-v2-ui-autodev/D2BE-006_FIELD_CONTRACT.md`

协同：

- 共享文档：`/Users/huangliang/project/OneOPS-ALL/docs/openclaw-autodev/shared-d2.md`
- FE evidence：`/Users/huangliang/project/OneOPS-ALL/docs/openclaw-autodev/evidence/d2-fe/**`
- BE evidence：`/Users/huangliang/project/OneOPS-ALL/docs/openclaw-autodev/evidence/d2-be/**`

规则：

- FE 不私自改 BE。
- BE 不私自改 FE。
- 跨端问题先写协调文档。
- 字段变更必须同步类型、页面、后端契约、evidence。

### 4.6 验收边界

最小验收：

- FE：`npm run typecheck:d2`
- BE：`go test ./app/device/v2/...`
- Browser：打开两个 redesign 路由，确认真实 API 200、页面无 console error、关键交互能跑通。

上线候选验收：

- 清册页真实 `GET /api/v1/device/v2/list`。
- 入库页真实 `GET /api/v1/device/v2/ingest/capabilities`。
- 最近任务真实 `GET /api/v1/device/v2/ingest/tasks?limit=5`。
- task detail 真实 `GET /api/v1/device/v2/ingest/tasks/:taskId`。
- 上传控件只接受 `.xlsx`。
- 未确认动作隐藏或禁用。
- 错误能显示，不能伪成功。
- evidence 写入 D2 对应目录。

### 4.7 最好记的版本

功能：

- 入库页把 Excel/手工清单变成 task。
- 清册页把 Device V2 设备查出来、管起来。

字段：

- 设备看 `code/name/platform_code/status`。
- 纳管看 `manageable/manage_status/lifecycle_stage/stage_status`。
- 扩展看 `labels/attributes/metadata/group_tags`。
- 入库看 `task_id/status/stages/result/device_results`。

流向：

- Excel -> ingest task -> execution result -> Device V2 清册。
- 筛选条件 -> list API -> 后端 DB/projection -> FE 表格。
- task result 只能用于交接，最终展示必须回查 list。

边界：

- `.xlsx` only。
- 真实 API only。
- 后端状态 only。
- 未确认动作 disabled/hidden。
- AI 可开发到候选，人批准后才上线。
