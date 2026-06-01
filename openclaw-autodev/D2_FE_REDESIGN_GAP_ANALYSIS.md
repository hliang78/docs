# D2 前端入库页与管理页重构缺口分析

更新时间：2026-05-13

基准文档：`/Users/huangliang/project/OneOPS-ALL/docs/openclaw-autodev/D2_INGEST_BASE_FIELD_TABLE.md`

分析对象：

- 入库页：`/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/views/device/DeviceV2IngestPipelineRedesign.vue`
- 管理页：`/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/views/device/DeviceV2ManagementRedesign.vue`
- 入库草稿模块：`/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/views/device/device-v2-import/**`
- API 类型：`/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/api/device/device-v2.ts`
- API 类型：`/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/api/device/device-v2-ingest.ts`

## 0. 总结

当前两个 redesign 页面已经接上真实后端，但字段体系还没有真正按 `D2_INGEST_BASE_FIELD_TABLE.md` 重构。

最大缺口不是“页面不能用”，而是：

1. 一等数据没有完全结构化承接，尤其是 `access_points`。
2. 平台和类型字段还混在展示层，`catalog` 基本没有进入 UI 口径。
3. 系统版本、架构、CPU、内存等硬件画像字段没有页面入口。
4. 入库页仍按旧口径判断可纳管：`IP + credential`，没有承接 controller detect 成功后的访问接入点。
5. 管理页把多层 `manage_status` 混成一个“可运维/待补充”展示状态，有语义风险。

一句话：现在 UI 是“能跑通的真实 API 页面”，但还不是“以字段主表为核心的 D2 入库和清册工作台”。

## 1. 入库页现状

### 1.1 已覆盖字段

入库页和草稿模块已覆盖：

| 字段组 | 当前覆盖 |
| --- | --- |
| 身份 | `code`、`biz_code`、`biz_name`、`sn`、`asset_number`、`hostname` |
| 平台 | `platform` |
| 基础状态 | `status` |
| 接入 | `in_band_ip`、`out_band_ip` |
| 凭据 | `credential_ref_in_band`、`credential_ref_out_band`、`snmp_credential_ref`、`winrm_credential_ref`、`winrm_port` |
| 位置 | `tenant_name`、`region_name`、`site_name`、`rack_name`、`rack_position` |
| 补充分类 | `device_kind`、`vendor`、`model` |
| 备注 | `remark` |
| 任务结果 | `task_id`、`status`、`stages`、`result.execution.device_results` |

### 1.2 入库页一等数据缺口

| 缺口 | 当前状态 | 风险 | 建议 |
| --- | --- | --- | --- |
| `access_points` 没有进入草稿字段 | `field-config.ts` 没有 `access_points`，`device-mapping.ts` 不生成 access_points | controller detect 成功的访问点无法沉淀，页面仍只知道 IP/凭据 | 增加 access point 结构化编辑/展示，至少支持从 detect 结果回填 |
| 可纳管判断仍是 `IP + credential` | `isDraftManageable()` 只看 `in_band_ip/out_band_ip` 和凭据字段 | 与新主表口径不一致，无法表达多个接入点、探测状态、优先级 | 改为优先看成功 `access_points[].detected + credential_ref`，再 fallback 到旧口径 |
| `credential_refs` 不可见 | 只显示顶层凭据字段 | 无法看见归一化后的凭据集合，也无法解释 endpoint credential_ref 来源 | 在任务详情/草稿详情中展示凭据引用集合，不展示明文 |
| `catalog/catalog_code/catalog_name` 未覆盖 | 新 ingest 草稿字段没有 catalog | 平台和类型无法同时准确表达；`device_kind/model` 容易被误当 catalog | 增加 catalog 字段组，明确和 `device_kind/model` 区分 |
| `platform_code` 在 Excel 中 alias 到 `platform`，页面未提示 | 草稿字段只有 `platform`，API 类型有 `platform_code` | 用户可能以为 platform_code 会原样写入 | UI 文案说明：Excel `platform_code` 会作为 `platform` 输入，并由后端解析主数据 |

### 1.3 入库页二等数据缺口

| 缺口 | 当前状态 | 风险 | 建议 |
| --- | --- | --- | --- |
| 系统版本字段缺失 | 无 `system_version/patch_version/firmware_version` | 无法承接 V1 同步或采集解析后的系统版本画像 | 增加“系统版本”字段组，先作为可选 attrs/metadata 字段 |
| 架构、CPU、内存字段缺失 | 无 `architecture/cpu_*/memory_*` | 后续 controller detect/采集结果无展示和回填位置 | 增加“硬件画像”字段组，标注为采集/解析字段 |
| `device_model_code/device_model_name/manufacturer_*` 未覆盖 | 只有新 ingest `vendor/model` | 与旧 V1/主数据字段断层 | 增加主数据型号字段和展示说明 |
| `tenant_code` 未覆盖 | 只有 `tenant_name` | 无法表达明确租户编码 | 增加 tenant_code 或明确 tenant_name 暂不解析 |
| `location_node_code` 未覆盖 | 只有 region/site/rack name | 无法承接位置节点编码 | 作为高级字段展示 |

### 1.4 入库页三等数据缺口

| 缺口 | 当前状态 | 风险 | 建议 |
| --- | --- | --- | --- |
| `metadata` 不可编辑/不可视 | `rowValuesToIngestDevice` 不保留 metadata | 来源、批次、采集上下文无法结构化带入 | 增加高级 JSON 区或受控字段 |
| `labels/group_tags` 不可编辑 | API 支持，但草稿 UI 未覆盖 | 分组和标签不能在入库前准备 | 增加标签/分组字段 |
| task result 只展示部分字段 | execution table 只显示 code/action/status/manageable/message | `matched_by/manage_status` 信息不足 | 增加 matched_by、manage_status、access point/credential 解释 |

## 2. 管理页现状

### 2.1 已覆盖字段

管理页已覆盖：

| 字段组 | 当前覆盖 |
| --- | --- |
| 身份 | `code`、`name`、关键词搜索 |
| 平台 | `platform_code` |
| 状态 | `status`、`manage_status`、`manageable`、`stage_status` |
| 接入 | 从 attributes 读取 `in_band_ip/out_band_ip/ip/management_ip/snmp_address` |
| 凭据 | 从 attributes 读取 `credential_ref_in_band/credential_ref_out_band/snmp_credential_ref` |
| 位置 | 从 attributes/labels 读取 site/rack/area |
| 来源 | 从 metadata/attributes 读取 source、batch_id |
| 编辑 | 支持 code/name/platform_code/status/labels_json/attributes_json |

### 2.2 管理页一等数据缺口

| 缺口 | 当前状态 | 风险 | 建议 |
| --- | --- | --- | --- |
| `access_points` 未结构化展示 | `mapDeviceRow()` 只取 primaryIp 和 login_method/protocol | 成功 detect 接入点不可见，多个接入点不可见 | 增加“访问接入点”详情区，展示 endpoint、plane、ip、method、port、credential_ref、detect_status |
| `credential_refs` 未展示 | 只读顶层 credential_ref | 凭据折叠结果不可见，endpoint 继承关系不可解释 | 展示 credential_refs map，并关联 access_points |
| `catalog` 未展示 | 只读 `record.type || attrs.device_type/category` | 类型/catalog 与 device_type 混用 | 增加 catalog/catalog_code/catalog_name 展示，并把 device_type/model 放到硬件画像 |
| `manage_status` 语义混用 | `resolveManageStatus()` 把 `record.manage_status === success`、`stage_status === success` 都当 operable | entity 顶层、attrs、ingest result、store readiness 可能混淆 | 明确区分 entity manage_status、attrs manage_status、manageable_status |
| 入库交接用 `manage_status=success/pending` | 入库页 handoff 把 task 可纳管转成清册 `success/pending` | task result 的 `manageable/registered_only` 与清册 entity `success/pending` 映射隐式 | 写明映射，或用 codes 聚焦后由后端真实 list 返回状态 |

### 2.3 管理页二等数据缺口

| 缺口 | 当前状态 | 风险 | 建议 |
| --- | --- | --- | --- |
| 系统版本/固件/补丁缺失 | 详情不展示 `system_version/patch_version/firmware_version` | 无法支撑系统画像 | 在详情侧栏增加“系统画像”区 |
| 架构/CPU/内存缺失 | 详情不展示 `architecture/cpu_*/memory_*` | controller detect/采集结果无法消费 | 在系统画像区预留 |
| 型号/厂商主数据缺失 | 只显示 `type/platform` | `device_model_code/name/manufacturer_*` 不可见 | 增加硬件摘要字段 |
| 位置字段不完整 | 只显示 site/rack/area | region_code/name、location_node_code 不清楚 | 增加位置详情展开 |
| `next_collection_plan` 未承接 | 批量采集按钮禁用，未展示 plan | 用户不知道为何待采集、下一步是什么 | 展示 minimal collection plan 或明确“待契约” |

### 2.4 管理页三等数据缺口

| 缺口 | 当前状态 | 风险 | 建议 |
| --- | --- | --- | --- |
| attributes JSON 是唯一高级编辑入口 | modal 只给 JSON textarea | 容易破坏结构，难以记忆核心字段 | 按字段主表拆结构化表单，JSON 放高级区 |
| metadata 不可编辑 | create/update payload 不传 metadata | 无法维护来源/系统画像上下文 | 增加 metadata JSON 或受控字段 |
| group_tags 不可编辑 | API 支持但表单不传 | 分组不能维护 | 增加 group_tags 控件 |

## 3. API 类型缺口

### 3.1 DeviceV2Item 类型

当前 `DeviceV2Item` 只有泛型 `attributes?: Record<string, unknown>` 和 `metadata?: Record<string, unknown>`。

缺口：

- 没有 `AccessPoint` 类型。
- 没有 `CredentialRefs` 类型。
- 没有 `DeviceSystemProfile` 类型。
- 没有 `DeviceHardwareProfile` 类型。
- 没有明确 `catalog_code/catalog_name/catalog` 字段读取辅助。

建议：

- 增加前端类型别名，不一定要求后端 envelope 立刻变更。
- 页面读取 attributes/metadata 时使用 typed helper，而不是到处 `readString(attrs, ...)`。

### 3.2 DeviceV2IngestDevice 类型

当前 `DeviceV2IngestDevice` 支持 `attributes/metadata/labels/group_tags`，但没有显式 access point 类型。

建议：

- 增加：
  - `AccessPoint`
  - `CredentialRefs`
  - `DeviceV2IngestAttributes`
  - `DeviceV2IngestMetadata`
- `attributes.access_points` 和 `attributes.credential_refs` 结构化。

## 4. 重构建议

### 4.1 入库页重构顺序

1. 字段模型先升级：
   - 补 `access_points`
   - 补 `catalog_*`
   - 补系统版本/硬件画像字段
   - 补 labels/group_tags/metadata
2. 草稿解析升级：
   - Excel 表头支持 access point 相关字段。
   - 支持 controller detect 结果导入或回填。
3. 可纳管判断升级：
   - 优先成功 access point。
   - fallback 到旧 IP + credential。
4. task 结果展示升级：
   - 展示 matched_by、manage_status、access point 证据。

### 4.2 管理页重构顺序

1. 详情侧栏先升级：
   - 访问接入点
   - 平台与类型
   - 系统画像
   - 硬件画像
2. 表格列再升级：
   - 主接入点替代 primaryIp。
   - catalog/type 分开。
   - manage_status 分层展示。
3. 编辑表单升级：
   - 从 JSON textarea 改为字段主表驱动的结构化表单。
   - JSON 保留为高级编辑。
4. 筛选升级：
   - 已确认字段先做。
   - 未确认 facets 继续禁用。

## 5. 优先级

P0：

- `access_points` 一等数据结构化。
- `manage_status` 多层语义拆开。
- 入库页和管理页都能展示 controller detect 成功接入点。

P1：

- catalog 与 device_kind/device_model/model 拆开。
- 系统版本、架构、CPU、内存进入系统/硬件画像区。
- labels/group_tags/metadata 进入受控维护。

P2：

- collection plan 展示。
- 更细的采集/监控动作。
- 保存视图和统计 facets。

## 6. 当前判断

基于字段主表看，D2 前端现在最大缺口是：页面还没有围绕“一等数据”重构信息架构。

尤其是：

- `access_points` 应成为入库和管理的核心。
- `catalog` 应从 `device_kind/model/type` 中独立出来。
- 系统/硬件画像应作为二等数据完整展示。
- 旧的 `IP + credential` 只能作为兼容判断，不应继续作为最终模型。
