# D2 入库基础字段表

更新时间：2026-05-13

定位：这是 D2 Device V2 入库字段的主表。后续需求、开发、联调、验收、AI 自动开发，都优先以本文为字段入口。其他 D2 文档只作为辅助说明、代码审计或上线背景材料。

## 0. 分级原则

一等数据：决定结果。  
用于判断设备是谁、属于哪个平台/类型、能不能连接、能不能纳管、入库是否成功。

二等数据：解释结果。  
用于说明位置、分类、分组、批次、校验、追踪、下一步动作。

三等数据：展示过程。  
用于展示时间、操作者、统计、提示、上下文，不反向决定核心业务。

## 1. 一等数据

### 1.1 设备身份

| 字段 | 中文名 | 来源 | 处理规则 | 去处 | 边界 |
| --- | --- | --- | --- | --- | --- |
| `code` | 设备编码 | JSON submit、批次 raw、已有 DeviceV2 | trim；优先匹配 entity/projection/code registry；创建时可作为指定 code | DeviceV2 主编码、详情、更新、删除、store run | 没有 code 时新 ingest 生成 `DVC...`，batch 可生成 `DV2...` |
| `biz_code` | 业务编码 | Excel/JSON；batch 可由 `system_id` fallback | trim；参与身份定位 | `attributes.biz_code`、匹配、校验 | 当前 payload 内不能重复 |
| `name` | 设备名称 | batch raw、已有 entity/projection | trim；可由 `biz_name/hostname/code/biz_code` fallback | DeviceV2 entity name、`attributes.name` | 空时最终可 fallback 到 code |
| `biz_name` | 业务名称 | 新 ingest Excel/JSON | trim；canonical builder 优先作为 Name | DeviceV2 name 候选 | Excel `name` alias 会进入 `biz_name` |
| `sn` | 序列号 | Excel/JSON attributes、batch raw | trim；作为 locator | `attributes.sn`、store observation | 可用于匹配已有设备 |
| `asset_number` | 资产编号 | Excel/JSON attributes、batch raw | trim；作为 locator | `attributes.asset_number`、store observation | 可用于匹配已有设备 |
| `hostname` | 主机名 | Excel/JSON attributes、batch raw | trim；作为 locator | `attributes.hostname`、store observation | 可用于匹配已有设备 |

身份定位顺序：

1. `code`
2. code registry
3. `biz_code`
4. `sn`
5. `asset_number`
6. `in_band_ip`
7. `out_band_ip`
8. `hostname`

### 1.2 平台与类型主字段

| 字段 | 中文名 | 来源 | 处理规则 | 去处 | 边界 |
| --- | --- | --- | --- | --- | --- |
| `platform` | 平台 | 新 ingest Excel 主列、JSON | 按 platform 主数据 code/name 匹配 | `attributes.platform`、`metadata.platform_name` | Excel 里的 `platform_code` header 会 alias 到 `platform` |
| `platform_code` | 平台编码 | JSON、batch raw、platform 主数据解析结果 | 优先于 `platform`；最终以主数据 `Platform.Code` 为准 | DeviceV2 platformCode、`attributes.platform_code`、`metadata.platform_code` | platform 表存在且匹配不到会失败 |
| `platform_name` | 平台名称 | platform 主数据 | 解析成功后写入 metadata | `metadata.platform_name` | 不是输入主字段 |
| `catalog` | 类型/类别名称 | 显式 `attributes.catalog` 或 `metadata` | 按 catalog 主数据 code/name 匹配 | `attributes.catalog`、`metadata.catalog_name` | 新 ingest Excel 没有该列 |
| `catalog_code` | 类型/类别编码 | 显式 `attributes.catalog_code` 或 `metadata` | 匹配 catalog 主数据 | `attributes.catalog_code`、`metadata.catalog_code` | 不由 `device_kind` 自动生成 |
| `catalog_name` | 类型/类别名称 | 显式 `attributes.catalog_name` 或 `metadata` | 匹配 catalog 主数据 | `metadata.catalog_name` | 不由 `model/device_type` 自动生成 |

必须记住：

- 平台 `platform/platform_code` 是当前入库主数据字段。
- 类型 catalog 只有显式提供 `catalog/catalog_code/catalog_name` 才会解析。
- `device_kind`、`device_type`、`device_model`、`model` 不是 catalog 的同义词。

### 1.3 状态与纳管

| 字段 | 中文名 | 来源 | 处理规则 | 去处 | 边界 |
| --- | --- | --- | --- | --- | --- |
| `status` | 设备基础状态 | Excel/JSON/batch | 新 ingest 允许空、`active`、`inactive`、`planned`、`retired`；batch 空默认 `active` | `attributes.status`、DeviceV2 status | 非法值校验失败 |
| `manageable` | 是否可纳管 | 后端根据 IP + 凭据派生 | 布尔值 | ingest result、DeviceV2 attributes、store summary | 前端不能自行推断替代 |
| `manage_status` | 纳管状态 | 后端派生 | ingest result 是 `manageable/registered_only/failed/unknown`；entity 顶层是 `success/pending` | 页面展示、筛选、结果判断 | 同名字段多语义，必须看所在对象 |
| `manageable_status` | 纳管就绪状态 | store run | `ready/unready/pending/unknown` | store run、collection plan | 不等于 `manage_status` |
| `core_store_status` | 核心入库状态 | store run | `pending/success/failed/blocked` | store run、collection plan | 决定下一步 `noop/retry_store` |

### 1.4 接入与凭据

| 字段 | 中文名 | 来源 | 处理规则 | 去处 | 边界 |
| --- | --- | --- | --- | --- | --- |
| `in_band_ip` | 带内 IP | Excel/JSON/batch | 非空必须是合法 IP | `attributes.in_band_ip`、access_points、observation | 可作为身份 locator |
| `out_band_ip` | 带外 IP | Excel/JSON/batch | 非空必须是合法 IP | `attributes.out_band_ip`、access_points、observation | 可作为身份 locator |
| `credential_ref_in_band` | 带内凭据引用 | 新 ingest Excel/JSON/attrs | 折叠到 `credential_refs.in_band/default` | `attributes`、纳管判断 | batch 旧字段 `in_band_credential_ref` 会 alias 到它 |
| `credential_ref_out_band` | 带外凭据引用 | 新 ingest Excel/JSON/attrs | 折叠到 `credential_refs.out_band` | `attributes`、纳管判断 | batch 旧字段 `out_band_credential_ref` 会 alias 到它 |
| `snmp_credential_ref` | SNMP 凭据引用 | JSON/batch；新 ingest Excel 模板无列但代码支持 | 折叠到 `credential_refs.snmp` | `attributes`、纳管判断 | 属于带内可纳管凭据 |
| `winrm_credential_ref` | WinRM 凭据引用 | 新 ingest Excel/JSON/batch | 持久化，参与纳管判断 | `attributes.winrm_credential_ref` | 当前不会折叠成 `credential_refs.winrm` |
| `credential_refs` | 凭据引用集合 | 写库归一化 | 由顶层凭据折叠，也可显式提供 | access_points 默认凭据 | 自动生成 key 有限制 |
| `access_points` | 接入点 | 显式 attrs 或由 IP 生成 | 补 `plane/ip/login_method/login_port/transport/priority/endpoint_id` | 采集/连接基础 | 没有 IP 不生成 |

接入点必须提升为一等数据。  
原因：真正能证明设备“可访问、可采集、可纳管”的，不是单独的 IP，也不是单独的凭据，而是 controller detect 成功后的连接事实。这个连接事实应该沉淀为 `access_points`。

### 1.5 访问接入点结构

`access_points[]` 是访问接入点数组。一个接入点代表一种可尝试或已验证的访问路径。

| 字段 | 中文名 | 来源 | 处理规则 | 去处 | 边界 |
| --- | --- | --- | --- | --- | --- |
| `endpoint_id` | 接入点 ID | 写库归一化生成，或外部显式提供 | 通常由 plane/ip/login_method 等生成稳定 ID | `access_points[].endpoint_id` | 用于凭据绑定、采集结果回写 |
| `plane` | 接入面 | in_band/out_band 或采集结果 | 归一化小写 | `access_points[].plane` | 常见值：`in_band/out_band` |
| `ip` | 访问地址 | `in_band_ip/out_band_ip` 或 detect 结果 | trim；应是可访问地址 | `access_points[].ip` | 未来也可支持 hostname/address，但需契约确认 |
| `ip_code` | IP 编码 | `in_band_ip_code/out_band_ip_code` 或 IPAM | trim | `access_points[].ip_code` | 可空 |
| `login_method` | 登录方式 | 输入、默认值、detect 结果 | 空默认 ssh；支持 ssh/telnet/http/https/winrm 等 | `access_points[].login_method` | 决定默认端口和 transport |
| `login_port` | 登录端口 | 输入或默认值 | ssh 22、telnet 23、http 80、https 443、winrm 5985 | `access_points[].login_port` | detect 成功端口应覆盖默认端口 |
| `transport` | 传输协议 | 输入或 login_method 推断 | 空时自动推断 | `access_points[].transport` | 连接/采集协议 |
| `credential_ref` | 凭据引用 | 顶层凭据、credential_refs、detect 成功凭据 | applyCredentialDefaultsToEndpoints 会补默认凭据 | `access_points[].credential_ref` | 不存明文，只存引用 |
| `priority` | 优先级 | 输入或默认 | 按 plane 默认；也可由 detect 成功结果调整 | `access_points[].priority` | 用于选择首选接入点 |
| `detected` | 是否探测成功 | controller detect | detect 成功写 true | `access_points[].detected` | 当前主代码未固定写入，建议后续契约补充 |
| `detect_status` | 探测状态 | controller detect | 建议 `success/failed/partial/unknown` | `access_points[].detect_status` | 当前主代码未固定写入 |
| `detect_source` | 探测来源 | controller detect | 如 controller 名称、任务 ID、采集来源 | `access_points[].detect_source` | 当前主代码未固定写入 |
| `last_detected_at` | 最近探测时间 | controller detect | ISO 时间 | `access_points[].last_detected_at` | 当前主代码未固定写入 |
| `evidence` | 探测证据 | controller detect | 可放握手方式、banner、命令结果摘要 | `access_points[].evidence` | 不能存敏感明文 |

接入点来源优先级：

1. controller detect 成功结果
2. 显式 `attributes.access_points`
3. `in_band_ip/out_band_ip` + 凭据字段自动生成
4. 旧批次 access/credential pass 补充

接入点写入原则：

- detect 成功的点应进入 `access_points`，并带上凭据引用。
- 同一个 plane/ip/login_method/port 不应重复生成多个接入点。
- 凭据只保存 `credential_ref`，不能保存用户名、密码、community 明文。
- `access_points` 里的成功接入点，比单独的 `in_band_ip/out_band_ip` 更能代表真实可访问性。
- 以后“可采集/可纳管”的判断，应优先看成功接入点，再看传统 IP + credential fallback。

建议接入点标准形态：

```json
{
  "endpoint_id": "in_band:ssh:10.0.0.1:22",
  "plane": "in_band",
  "ip": "10.0.0.1",
  "login_method": "ssh",
  "login_port": 22,
  "transport": "ssh",
  "credential_ref": "cred-ssh-core",
  "priority": 10,
  "detected": true,
  "detect_status": "success",
  "detect_source": "controller_detect",
  "last_detected_at": "2026-05-13T10:00:00+08:00"
}
```

纳管判断：

- 带内可纳管：`in_band_ip` + `credential_ref_in_band` 或 `snmp_credential_ref` 或 `winrm_credential_ref`
- 带外可纳管：`out_band_ip` + `credential_ref_out_band`
- 否则：`registered_only`

新口径：

- 旧判断：IP + credential。
- 新目标：成功 `access_points` + credential_ref。
- 兼容期：后端仍保留 IP + credential fallback，但字段表和后续开发要把 controller detect 成功点沉淀到 `access_points`。

### 1.6 入库结果主字段

| 字段 | 中文名 | 来源 | 处理规则 | 去处 | 边界 |
| --- | --- | --- | --- | --- | --- |
| `task_id` | 入库任务 ID | 后端生成 | 新 ingest 为 `ingest-task-...`；store 为 `device-v2-store-...` | 任务详情、最近任务、追溯 | 不由前端生成 |
| `source` | 入库来源 | 请求 | 必须是 `manual_api/excel_upload/reference_payload/future_pipeline` | task.source | 非法失败 |
| `task.status` | 任务状态 | 后端派生 | `prepared/completed/failed` | task 展示 | execution failed 才 failed |
| `stages` | 入库阶段 | 默认阶段 + 执行结果 | `request_received/canonical_device_payload/validator_slot/execution_adapter` | task 展示 | execution stage 会改成 completed/failed/blocked |
| `result.execution.device_results` | 单设备执行结果 | executor | 每台设备 created/updated/failed/blocked | 页面结果、清册交接 | task result 不能直接冒充清册 list |
| `device_count` | 设备数量 | canonical devices/codes | count | task/store summary | 统计字段，但影响任务主结果 |

## 2. 二等数据

### 2.1 位置数据

| 字段 | 中文名 | 来源 | 处理规则 | 去处 | 边界 |
| --- | --- | --- | --- | --- | --- |
| `region_name` | 区域名称 | 新 ingest Excel | 按 region code/name 匹配 | `attributes.region_name`、`metadata.region_name` | 匹配不到会失败 |
| `region_code` | 区域编码 | batch/attrs/alias | alias 可进入 region_name 后匹配 | `attributes.region_code`、observation | 与 site 层级相关 |
| `site_name` | 站点/机房名称 | 新 ingest Excel | 按 site code/name 匹配 | `attributes.site_name`、`metadata.site_name` | 与 region 不一致会失败 |
| `site_code` | 站点/机房编码 | batch/attrs/alias | alias 可进入 site_name 后匹配 | `attributes.site_code`、observation | 与 rack 层级相关 |
| `rack_name` | 机柜名称 | 新 ingest Excel | 按 rack code/name 匹配 | `attributes.rack_name`、`metadata.rack_name` | 与 site 不一致会失败 |
| `rack_code` | 机柜编码 | batch/attrs/alias | alias 可进入 rack_name 后匹配 | `attributes.rack_code`、observation | 层级校验 |
| `rack_position` | 机位/机架号 | Excel/JSON/batch | 写 `rack_position`，并同步 `frame` | attributes、observation | 不参与主身份 |
| `location_node_code` | 位置节点编码 | attrs/store summary | 读取展示 | store summary/list filter | 新 ingest 不生成 |

### 2.2 类型、硬件、补充分类

| 字段 | 中文名 | 来源 | 处理规则 | 去处 | 边界 |
| --- | --- | --- | --- | --- | --- |
| `device_kind` | 设备类别文本 | 新 ingest Excel、batch raw | 新 ingest 进入 attrs；batch minimal 当前未进入 attrs | attributes | 不等于 catalog |
| `device_type` | 设备类型 | 旧 batch base | 进入 attrs.device_type | observation hardware | 不等于 catalog |
| `device_model` | 设备型号 | 旧 batch base | 进入 attrs.device_model | observation hardware | 不等于新 ingest `model` |
| `device_model_code` | 设备型号编码 | V1 同步、显式 attrs | V1 同步写入 attrs.device_model_code；base reference 可校验 | attributes、network overview | 新 ingest Excel 当前不提供 |
| `device_model_name` | 设备型号名称 | V1 同步 metadata、DeviceModel 主数据 | V1 同步写入 metadata.device_model_name | metadata、展示 | 不是入库主匹配字段 |
| `vendor` | 厂商 | 新 ingest Excel | 进入 attrs.vendor | attributes | 当前不查主数据 |
| `model` | 型号文本 | 新 ingest Excel | 进入 attrs.model | attributes | 当前不查 device_model 主数据 |
| `manufacturer_code` | 厂商编码 | V1 同步 metadata、DeviceModel.Manufacturer | 写入 metadata.manufacturer_code | metadata、展示 | 新 ingest 主链路当前不生成 |
| `manufacturer_name` | 厂商名称 | V1 同步 metadata、DeviceModel.Manufacturer | 写入 metadata.manufacturer_name | metadata、展示 | 与新 ingest `vendor` 不是同一字段 |

### 2.3 系统版本与硬件画像

| 字段 | 中文名 | 来源 | 处理规则 | 去处 | 边界 |
| --- | --- | --- | --- | --- | --- |
| `system_version` | 系统版本 | V1 同步 metadata；未来采集/解析结果可补充 | trim 后写 metadata.system_version | metadata、详情展示、系统画像 | 新 ingest Excel 当前不提供 |
| `patch_version` | 补丁版本 | V1 同步 metadata；未来采集/解析结果可补充 | trim 后写 metadata.patch_version | metadata、详情展示、系统画像 | 新 ingest Excel 当前不提供 |
| `firmware_version` | 固件版本 | V1 同步 metadata；未来采集/解析结果可补充 | trim 后写 metadata.firmware_version | metadata、详情展示、系统画像 | 新 ingest Excel 当前不提供 |
| `kernel_version` | 内核版本 | 预留采集/解析字段 | 建议进入 attributes 或 metadata，待后端契约确认 | 系统画像 | 当前 D2 入库代码未发现固定写入 |
| `os_name` | 操作系统名称 | 预留采集/解析字段 | 建议进入 attributes 或 metadata，待后端契约确认 | 系统画像 | 当前 D2 入库代码未发现固定写入 |
| `os_version` | 操作系统版本 | 预留采集/解析字段 | 建议进入 attributes 或 metadata，待后端契约确认 | 系统画像 | 当前 D2 入库代码未发现固定写入 |
| `architecture` | 系统架构 | 预留采集/解析字段 | 建议统一使用 `architecture`，例如 `x86_64/aarch64` | 系统/硬件画像 | 当前 D2 入库代码未发现固定写入 |
| `cpu_arch` | CPU 架构 | 预留采集/解析字段 | 如需和系统架构区分，进入 attributes.cpu_arch | 硬件画像 | 当前 D2 入库代码未发现固定写入 |
| `cpu_model` | CPU 型号 | 预留采集/解析字段 | 进入 attributes.cpu_model 或硬件明细 | 硬件画像 | 当前 D2 入库代码未发现固定写入 |
| `cpu_cores` | CPU 核数 | 预留采集/解析字段 | 建议 number；进入 attributes.cpu_cores | 容量画像 | 当前 D2 入库代码未发现固定写入 |
| `cpu_sockets` | CPU 颗数 | 预留采集/解析字段 | 建议 number；进入 attributes.cpu_sockets | 容量画像 | 当前 D2 入库代码未发现固定写入 |
| `memory_total` | 内存总量 | 预留采集/解析字段 | 建议统一单位，优先 bytes 或 MiB，必须在契约中固定 | 容量画像 | 当前 D2 入库代码未发现固定写入 |
| `memory_total_bytes` | 内存总字节数 | 预留采集/解析字段 | 如采用 bytes，建议使用该字段名 | 容量画像 | 当前 D2 入库代码未发现固定写入 |
| `memory_slots` | 内存槽位数 | 预留采集/解析字段 | 建议 number；进入 attributes.memory_slots | 硬件画像 | 当前 D2 入库代码未发现固定写入 |
| `hardware` | 硬件明细容器 | 预留采集/解析字段 | 可放 CPU/内存/磁盘/板卡明细，需另定 schema | attributes 或 metadata | 容器字段，具体 key 再分级 |

说明：

- `system_version/patch_version/firmware_version` 是当前代码里能确认的版本字段，来自 V1 同步 metadata。
- CPU、内存、架构类字段当前更像采集/解析后的硬件画像，不是现有新 ingest Excel 主字段。
- 这些字段建议归为二等数据：它们解释设备能力和画像，但不直接决定入库身份；如果后续采集流程用它们决定调度或准入，再提升为一等。

### 2.4 组织、标签、分组

| 字段 | 中文名 | 来源 | 处理规则 | 去处 | 边界 |
| --- | --- | --- | --- | --- | --- |
| `tenant_name` | 租户名称 | 新 ingest Excel | 进入 attrs.tenant_name | attributes | 当前不解析 tenant_code |
| `tenant_code` | 租户编码 | alias/attrs | Excel alias 到 tenant_name；显式 attrs 可被 base validation 校验 | attributes | 新 ingest 不由 tenant_name 推导 |
| `namespace` | 命名空间 | batch req/raw | 空默认 `infra/device` | normalized_patch | 新 ingest 主链路无核心作用 |
| `function_area` | 功能区 | attrs/metadata/labels 或默认 | 未显式设置时写 `DefaultArea` | attributes | 影响 Agent/采集功能域 |
| `labels` | 标签 | JSON/batch raw | trim string map | DeviceV2 labels | 可筛选/展示 |
| `group_tags` | 分组标签 | JSON/batch raw | trim、去空、去重 | entity extra、projection | 分组展示 |

### 2.5 批次、校验、追踪

| 字段 | 中文名 | 来源 | 处理规则 | 去处 | 边界 |
| --- | --- | --- | --- | --- | --- |
| `batch_id` | 批次 ID | batch req/generated | import batch 主键 | batch/record | 旧 batch 链路 |
| `row_no` | 行号 | Excel/batch rows | 下标 + 1 或上传行号 | 错误定位 | 非业务主键 |
| `validate_status` | 校验状态 | batch validate | `pending/ok/error` | import record | error 阻止正常 apply |
| `apply_status` | 应用状态 | batch apply | `pending/success/failed/skipped` | import record | relation pass 当前 skipped |
| `error_code` | 错误码 | batch validate/apply | `IMPORT_VALIDATE_ERROR/IMPORT_APPLY_ERROR` | import record | 追踪用 |
| `error_message` | 错误信息 | validate/apply/executor | trim | 页面/审计 | 不作为主判断字段 |
| `matched_by` | 命中字段 | ingest executor | code/biz_code/sn/asset_number/in_band_ip/out_band_ip/hostname | execution result | 判断匹配原因 |
| `locator_trace` | 定位追踪 | import record 模型 | 当前 minimal 核心流程未见主要写入 | 预留/审计 | 不可依赖 |
| `conflict_candidates` | 冲突候选 | import record 模型 | validation 默认清空 | 审计 | 当前不是主链路核心 |

### 2.6 store 与采集建议

| 字段 | 中文名 | 来源 | 处理规则 | 去处 | 边界 |
| --- | --- | --- | --- | --- | --- |
| `run_id` | 单设备 run ID | store | taskID + code stable sha1 | store run | store 链路 |
| `current_step` | 当前步骤 | store | `load_device/minimal_upsert` 等 | store run | 展示/诊断 |
| `collection_plan_source` | 采集计划来源 | minimal plan | 固定 `minimal_status` | collection plan list | 不是完整 DC2 计划 |
| `next_collection_plan` | 下一步计划 | run 状态派生 | 成功 `noop`，失败 `retry_store` | collection plan list | 当前只是 minimal 建议 |
| `collection_plan_snapshot` | 采集计划快照 | store summary | 当前为空数组 | store summary | 不能当真实采集计划 |
| `manageable_pending_reasons` | 未就绪原因 | collection plan | 非 ready 时 `manageability_not_ready` | plan list | 粒度较粗 |

## 3. 三等数据

### 3.1 展示和上下文

| 字段 | 中文名 | 来源 | 处理规则 | 去处 | 边界 |
| --- | --- | --- | --- | --- | --- |
| `remark` | 备注 | 新 ingest Excel | 进入 attrs.remark | 展示/追溯 | 不决定主流程 |
| `description` | 描述 | batch base/relation | raw | 展示/追溯 | 不决定主流程 |
| `message` | 消息 | 后端执行/错误 | trim | task/run/result 展示 | 可解释，不替代状态字段 |
| `requested_by` | 请求人 | submit/form | trim | source_summary/task | 可空 |
| `created_by` | 创建人 | batch req | trim | batch | 可空 |
| `warnings` | 警告 | source snapshot | 当前多为空数组 | result/source_summary | 不作为失败依据 |

### 3.2 时间字段

| 字段 | 中文名 | 来源 | 去处 |
| --- | --- | --- | --- |
| `created_at` | 创建时间 | GORM hook/DB | task/batch/run/record 展示 |
| `updated_at` | 更新时间 | GORM hook/DB | task/batch/run/record 展示 |
| `applied_at` | 应用时间 | batch apply success | import record |
| `finished_at` | 完成时间 | store run | store run |

### 3.3 统计字段

| 字段 | 中文名 | 来源 | 边界 |
| --- | --- | --- | --- |
| `accepted_count` | 接受数量 | len(devices) 或 validation | 统计 |
| `rejected_count` | 拒绝数量 | validation | 统计 |
| `input_row_count` | 输入行数 | len(rows) | 统计 |
| `raw_device_count` | 原始设备数 | len(req.Devices) | 统计 |
| `accepted_row_count` | 接受行数 | len(rows) | 统计 |
| `created` | 新增数 | executor/store | 统计，也可辅助判断结果 |
| `updated` | 更新数 | executor/store | 统计，也可辅助判断结果 |
| `failed` | 失败数 | executor/store/import | 统计，也可辅助判断结果 |
| `skipped` | 跳过数 | executor/import | 统计 |
| `success` | 成功数 | import batch | 统计 |
| `total` | 总数 | batch/list | 统计 |

### 3.4 配置和容器

| 字段 | 中文名 | 来源 | 处理规则 | 边界 |
| --- | --- | --- | --- | --- |
| `options` | 选项 | batch/store req | clone/map JSON | 只作为执行上下文 |
| `pipeline_template` | 流水线模板 | store req | 空默认 `device_v2_minimal_store` | 不决定设备身份 |
| `framework_version` | 框架版本 | 常量 | `v0-minimal` | 展示/兼容 |
| `adapter` | 适配器 | source | manual_json/excel_devices_sheet 等 | 追溯 |
| `source_type` | 来源类型 | source | 同 req.Source | 追溯 |
| `metadata` | 元数据容器 | JSON/batch/解析补充 | merge | 容器本身三等；里面的 `platform_code/catalog_code/region_code` 等按具体字段等级处理 |
| `attributes` | 属性容器 | JSON/Excel/batch | merge/normalize | 容器本身不是等级，里面字段按具体语义分级 |

## 4. 使用规则

1. 字段主表以本文为准。
2. 一等数据必须有后端真实来源，不能由前端 mock、fallback、静默默认。
3. 二等数据可以辅助筛选、解释、追踪，但不能覆盖一等数据。
4. 三等数据只能展示过程，不能反向决定设备身份、平台、类型、纳管状态。
5. 容器字段如 `attributes/metadata` 不直接决定等级，必须看里面具体 key。
6. 同名字段必须看对象层级：`manage_status` 在 ingest result、entity、attrs 里含义不同。
7. 平台和类型不能混：`platform/platform_code` 是平台；`catalog/catalog_code` 是类型；`device_kind/model/device_model/device_type` 当前只是描述或旧链路字段。
8. 系统版本、架构、CPU、内存字段先按二等数据管理；当前主线代码只确认 `system_version/patch_version/firmware_version`，其他字段需要后续采集/解析契约确认后再固化。
9. controller detect 成功的访问点必须沉淀为一等数据 `access_points`，包括地址、协议、端口、凭据引用和探测状态；单独 IP 或单独凭据都不能完整代表访问接入点。
