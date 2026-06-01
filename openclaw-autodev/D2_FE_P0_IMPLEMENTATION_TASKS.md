# D2 前端 P0 实施任务单

更新时间：2026-05-13

上游依据：

- 字段主表：`/Users/huangliang/project/OneOPS-ALL/docs/openclaw-autodev/D2_INGEST_BASE_FIELD_TABLE.md`
- 缺口分析：`/Users/huangliang/project/OneOPS-ALL/docs/openclaw-autodev/D2_FE_REDESIGN_GAP_ANALYSIS.md`
- 重构规划：`/Users/huangliang/project/OneOPS-ALL/docs/openclaw-autodev/D2_FE_INGEST_MANAGEMENT_REDESIGN_PLAN.md`

定位：本文是 P0 研发任务单。目标不是一次性重写页面，而是先把 D2 前端的核心字段口径扶正，让入库页和管理页都以一等数据为骨架。

## 0. P0 目标

P0 只解决五件事：

1. 建立共享字段模型，避免两个页面继续各读各的 `attributes/metadata`。
2. `access_points` 成为入库页和管理页的一等字段。
3. `credential_refs` 能解释凭据来源，且只显示引用。
4. `manage_status` 拆成多层状态，不再混成一个“可运维”标签。
5. `platform/catalog/device_kind/model` 分层展示，不再互相冒充。

P0 不解决：

- 完整采集流程。
- 自动监控接入。
- 后端 facets 统计。
- 复杂变更审批。
- 所有字段的高级编辑体验。

## 1. 当前代码事实

### 1.1 入库页

涉及文件：

- `/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/views/device/DeviceV2IngestPipelineRedesign.vue`
- `/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/views/device/device-v2-import/field-config.ts`
- `/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/views/device/device-v2-import/device-mapping.ts`
- `/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/views/device/device-v2-import/draft-issues.ts`
- `/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/views/device/device-v2-import/draft-view-ops.ts`
- `/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/views/device/device-v2-import/draft-parser.ts`
- `/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/views/device/device-v2-import/useDeviceV2IngestDraft.ts`

现状：

| 点 | 当前代码 | 风险 |
| --- | --- | --- |
| 草稿字段 | `field-config.ts` 只有 `platform`、IP、顶层凭据、位置、vendor/model | 没有 `access_points/credential_refs/catalog_*` |
| payload 构造 | `rowValuesToIngestDevice()` 只写有限 attributes | 会丢 `metadata/labels/group_tags/access_points` |
| 可纳管判断 | `isDraftManageable()` 只看 `in_band_ip/out_band_ip + credential` | 不符合接入点优先口径 |
| 草稿表格 | `deviceRows` 只显示编码、名称、管理地址、纳管状态 | 没有平台/catalog、接入点证据 |
| 执行结果 | `executionColumns` 只显示 code/action/status/manageable/message | 没有 `matched_by/manage_status/access point/credential_ref` |

### 1.2 管理页

涉及文件：

- `/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/views/device/DeviceV2ManagementRedesign.vue`
- `/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/api/device/device-v2.ts`

现状：

| 点 | 当前代码 | 风险 |
| --- | --- | --- |
| 行模型 | `DeviceRow` 只有 `primaryIp/access/credential/type/platform/manageStatus` | 无法表达 access point 和状态层 |
| 状态判断 | `resolveManageStatus()` 把 `manageable/manage_status/stage_status` 合并 | 多语义混用 |
| 行映射 | `mapDeviceRow()` 读取 `in_band_ip/out_band_ip/ip/management_ip` | 成功探测接入点不可见 |
| 凭据展示 | 只读 `credential_ref_in_band/out_band/snmp` | 无法解释 endpoint 凭据继承 |
| 类型展示 | `record.type || attrs.device_type/category` | catalog 与 device_kind/type 混用 |
| 编辑 modal | 只维护 `platform_code/status/labels_json/attributes_json` | 人无法稳定维护核心字段 |

## 2. P0 任务 1：共享字段模型

### 2.1 新增文件

建议新增：

`/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/views/device/device-v2-redesign/field-model.ts`

### 2.2 类型定义

必须包含：

```ts
export interface DeviceV2AccessPoint {
  endpoint_id?: string;
  plane?: 'in_band' | 'out_band' | string;
  ip?: string;
  ip_code?: string;
  login_method?: string;
  login_port?: number;
  transport?: string;
  credential_ref?: string;
  priority?: number;
  detected?: boolean;
  detect_status?: 'success' | 'failed' | 'partial' | 'unknown' | string;
  detect_source?: string;
  last_detected_at?: string;
  evidence?: Record<string, unknown> | string;
  source_kind?: 'stored' | 'fallback' | 'manual' | 'detected';
}

export interface DeviceV2CredentialRefs {
  default?: string;
  in_band?: string;
  out_band?: string;
  snmp?: string;
  winrm?: string;
  [key: string]: string | undefined;
}

export interface DeviceV2ManageStatusLayers {
  entity_manage_status?: string;
  attribute_manage_status?: string;
  ingest_manage_status?: string;
  manageable?: boolean;
  stage_status?: string;
  manageable_status?: string;
  core_store_status?: string;
}

export interface DeviceV2PlatformCatalogView {
  platform_code?: string;
  platform_name?: string;
  platform_input?: string;
  catalog_code?: string;
  catalog_name?: string;
  catalog_input?: string;
  device_kind?: string;
  device_type?: string;
  vendor?: string;
  model?: string;
}
```

### 2.3 helper 定义

必须实现：

| helper | 输入 | 输出 | 关键规则 |
| --- | --- | --- | --- |
| `toRecord(value)` | unknown | object map | 非对象返回空对象 |
| `readText(map, ...keys)` | object | string | trim 后返回第一个非空 |
| `readCredentialRefs(recordOrAttrs)` | DeviceV2Item 或 attrs | CredentialRefs | 顶层旧凭据折叠到 map |
| `readAccessPoints(recordOrAttrs)` | DeviceV2Item 或 attrs | AccessPoint[] | 优先 `attrs.access_points`，再 fallback IP + credential |
| `pickPrimaryAccessPoint(points)` | points | point/null | 成功 detected 优先，其次 priority，其次 in_band |
| `readPlatformCatalog(record)` | DeviceV2Item | PlatformCatalogView | catalog 独立于 device_kind/model |
| `readManageStatusLayers(record)` | DeviceV2Item | ManageStatusLayers | 不做最终文案，只拆层 |
| `summarizeManageReadiness(layers, points)` | layers + points | UI summary | 成功接入点 + credential_ref 优先 |

### 2.4 fallback 规则

当没有 `attributes.access_points` 时，允许生成展示用 fallback：

| 来源字段 | fallback access point |
| --- | --- |
| `in_band_ip + credential_ref_in_band` | `plane=in_band`、`login_method=ssh`、`source_kind=fallback` |
| `in_band_ip + snmp_credential_ref` | `plane=in_band`、`login_method=snmp`、`source_kind=fallback` |
| `in_band_ip + winrm_credential_ref` | `plane=in_band`、`login_method=winrm`、`source_kind=fallback` |
| `out_band_ip + credential_ref_out_band` | `plane=out_band`、`login_method=ssh`、`source_kind=fallback` |

限制：

- fallback 不能设置 `detected=true`。
- fallback 只用于展示和兼容判断。
- 如果后端已经有 `access_points`，不要重复生成相同 endpoint。

## 3. P0 任务 2：API 类型补齐

### 3.1 修改文件

- `/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/api/device/device-v2.ts`
- `/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/api/device/device-v2-ingest.ts`

### 3.2 要补的类型

在 API 类型层补最小结构，不要求后端 envelope 改：

| 类型 | 用途 |
| --- | --- |
| `DeviceV2AccessPoint` | 管理页、入库页、采集动作复用 |
| `DeviceV2CredentialRefs` | 凭据引用集合 |
| `DeviceV2SystemProfile` | 系统版本和架构字段 |
| `DeviceV2HardwareProfile` | CPU、内存字段 |
| `DeviceV2IngestAttributes` | 入库 attributes 受控结构 |
| `DeviceV2IngestMetadata` | 入库 metadata 受控结构 |

边界：

- `DeviceV2Item.attributes` 仍可保留 `Record<string, unknown>`，但 helper 要用类型读取。
- 不要把所有字段强塞到顶层 API item。

## 4. P0 任务 3：入库草稿支持 access point

### 4.1 修改 `field-config.ts`

新增字段组：

| 字段 | label | 备注 |
| --- | --- | --- |
| `catalog` | 类型/catalog | 明确不是 `device_kind` |
| `catalog_code` | 类型编码 | 有 code 时优先 |
| `catalog_name` | 类型名称 | 展示/输入 |
| `access_plane` | 接入面 | `in_band/out_band` |
| `access_ip` | 接入地址 | 用于结构化 endpoint |
| `access_method` | 登录方式 | `ssh/telnet/http/https/winrm/snmp` |
| `access_port` | 登录端口 | number |
| `access_credential_ref` | 接入点凭据引用 | 写入 endpoint |
| `access_detect_status` | 探测状态 | 只展示或导入证据 |

header alias：

| Excel 表头 | 归一字段 |
| --- | --- |
| `catalog_code` | `catalog_code` |
| `catalog_name` | `catalog_name` |
| `catalog` | `catalog` |
| `access_points` | `access_points_json` |
| `endpoint_ip` | `access_ip` |
| `login_method` | `access_method` |
| `login_port` | `access_port` |
| `credential_ref` | `access_credential_ref` |
| `detect_status` | `access_detect_status` |

### 4.2 修改 `device-mapping.ts`

`rowValuesToIngestDevice()` 必须：

1. 保留 `catalog/catalog_code/catalog_name` 到 `attributes` 或 `metadata`，按后端当前口径优先写 `attributes`。
2. 根据 `access_*` 字段构造 `attributes.access_points[]`。
3. 根据顶层凭据构造 `attributes.credential_refs`。
4. 继续保留旧字段 `in_band_ip/out_band_ip/credential_ref_*`，作为兼容字段。
5. 不丢 `labels/group_tags/metadata`，如果 P0 不做 UI 编辑，也至少保留从 `DeviceV2IngestDevice` 回灌时的原值。

建议构造：

```json
{
  "attributes": {
    "catalog_code": "server",
    "catalog_name": "服务器",
    "credential_refs": {
      "in_band": "cred-ssh-core",
      "snmp": "cred-snmp-core"
    },
    "access_points": [
      {
        "plane": "in_band",
        "ip": "10.0.0.1",
        "login_method": "ssh",
        "login_port": 22,
        "credential_ref": "cred-ssh-core",
        "source_kind": "manual"
      }
    ]
  }
}
```

### 4.3 修改 `draft-issues.ts`

`isDraftManageable(row)` 改为：

1. 先读草稿中的 `access_points` 或 `access_*`。
2. 如果存在 `detected=true` 或 `detect_status=success` 且有 `credential_ref`，返回 true。
3. 如果没有成功接入点，再 fallback 到旧 `IP + credential`。
4. 返回值最好从 boolean 升级为摘要对象：

```ts
interface DraftManageabilitySummary {
  manageable: boolean;
  source: 'access_point' | 'fallback_ip_credential' | 'missing';
  reason: string;
}
```

兼容期可以保留 `isDraftManageable()`，内部调用 `summarizeDraftManageability()`。

### 4.4 修改入库页表格

`DeviceV2IngestPipelineRedesign.vue` 的 `deviceColumns/deviceRows` 调整：

| 旧列 | 新列 |
| --- | --- |
| 设备编码 | 设备 |
| 名称 | 平台/catalog |
| 管理地址 | 访问接入点 |
| 基础入库 | 入库判断 |
| 纳管状态 | 纳管依据 |
| 下一步 | 下一步 |

`readinessMetrics` 调整：

| 指标 | 口径 |
| --- | --- |
| 当前清单 | 草稿行数 |
| 身份完整 | 通过身份校验行数 |
| 接入点成功 | `access_points.detect_status=success` 行数 |
| catalog 完整 | 有 `catalog_code/catalog/catalog_name` 行数 |
| 待修复 | issue 行数 |

## 5. P0 任务 4：任务结果补字段

### 5.1 修改 API 类型

`DeviceV2IngestExecutionDeviceResult` 增加可选字段：

```ts
access_point?: DeviceV2AccessPoint;
access_points?: DeviceV2AccessPoint[];
credential_ref?: string;
error_code?: string;
```

### 5.2 修改 `executionColumns`

新增列：

| 列 | 字段 |
| --- | --- |
| 命中 | `matched_by` |
| 纳管状态 | `manage_status` |
| 接入点 | `access_point` 或 `access_points[0]` |
| 凭据 | `credential_ref` |
| 错误 | `error_code/message` |

边界：

- 如果后端当前没有返回接入点字段，显示“后端未返回”，不要从草稿偷偷冒充执行结果。
- `manageable` 继续显示，但旁边必须有 `manage_status`。

## 6. P0 任务 5：管理页 access point 和状态层

### 6.1 修改 `DeviceRow`

新增或替换字段：

| 新字段 | 来源 |
| --- | --- |
| `identityText` | identity helper |
| `platformCatalogText` | platform catalog helper |
| `primaryAccessPoint` | `pickPrimaryAccessPoint(readAccessPoints(record))` |
| `accessPointCount` | access points length |
| `accessEvidence` | detected/fallback/unknown |
| `credentialSummary` | credential refs + primary endpoint |
| `manageLayers` | status layer helper |
| `manageReadiness` | readiness summary |

保留旧字段 `primaryIp/access/credential` 也可以，但应由新 helper 派生。

### 6.2 修改 `resolveManageStatus()`

旧逻辑：

```ts
record.manageable || record.manage_status === 'success' || record.stage_status === 'success'
```

新逻辑：

1. `record.manageable === true` 可作为强信号。
2. `record.manage_status` 只代表 entity 顶层状态。
3. `attributes.manage_status` 单独展示，不参与直接覆盖。
4. 有成功接入点 + credential_ref 时，可显示“接入已验证”。
5. 有 IP + credential fallback 时，只显示“待验证”，不显示“已验证”。

建议 UI summary：

| 状态 | 条件 |
| --- | --- |
| `operable` | entity success 或 manageable true，且有接入/凭据依据 |
| `accessVerified` | access point detect success + credential_ref |
| `registeredOnly` | 有身份和平台，但无接入点 |
| `toComplete` | 缺身份、平台或凭据 |
| `unknown` | 后端状态无法解释 |

如果 SavedViewKey 暂不扩展，也至少在详情里显示上述解释，不要只给一个标签。

### 6.3 修改 `mapDeviceRow()`

必须改的读取：

| 当前 | 新口径 |
| --- | --- |
| `primaryIp = readString(attrs, 'in_band_ip',...)` | `primaryAccessPoint.ip`，fallback 才读旧 IP |
| `credential = readString(attrs, credential...)` | endpoint `credential_ref` + `credential_refs` |
| `type = record.type || attrs.device_type/category` | `catalog_code/name` 优先，`device_kind/model` 副显示 |
| `access = attrs.access/login_method/protocol` | `plane/method/port/detect_status/source_kind` |

### 6.4 修改详情栏

详情栏 P0 最少增加三个块：

| 块 | 内容 |
| --- | --- |
| 平台与类型 | platform、catalog、device_kind/vendor/model 分开 |
| 访问接入点 | endpoint、plane、ip、method、port、credential_ref、detect_status |
| 状态层 | entity manage_status、attribute manage_status、manageable、stage_status |

原“采集与监控”块可以保留，但其中的“凭证映射”要换成 credential refs + endpoint 引用。

## 7. P0 任务 6：编辑入口最低改造

P0 不要求完整字段表单，但要避免继续只有 JSON：

| 字段 | 控件 | 保存位置 |
| --- | --- | --- |
| `platform_code` | input/select | 顶层 |
| `catalog_code/catalog_name` | input/select | attributes/metadata |
| `in_band_ip/out_band_ip` | input | attributes |
| `credential_ref_in_band/credential_ref_out_band/snmp_credential_ref/winrm_credential_ref` | input | attributes + credential_refs |
| `access_points` | 简单表格或 JSON with schema hint | attributes.access_points |

最低要求：

- 编辑 modal 中增加“访问接入点 JSON”独立 textarea。
- 保存前校验它必须是数组。
- 如果用户填写 `detected=true`，但没有 `detect_source/last_detected_at/evidence`，提示“手工编辑不能伪造探测成功”，保存时改为 `detect_status=unknown` 或阻止保存。

## 8. 验收用例

### 8.1 入库页

| 用例 | 输入 | 期望 |
| --- | --- | --- |
| 旧字段可纳管 | `in_band_ip + credential_ref_in_band` | 显示 fallback 可纳管，不能显示 detect success |
| 成功接入点 | `access_points[0].detect_status=success + credential_ref` | 显示接入点成功，可纳管依据为 access point |
| 无凭据接入点 | 有 IP/method/port，无 credential_ref | 可入库，仅登记或待补充 |
| catalog 独立 | 有 `device_kind=model`，无 catalog | catalog 显示缺失，不能用 model 代替 |
| 平台 alias | Excel `platform_code` | 仍进入 platform 输入，提示后端解析主数据 |
| 执行结果无接入点 | 后端 result 不返 access point | 结果列显示“后端未返回”，不能用草稿伪造 |

### 8.2 管理页

| 用例 | 设备 attributes | 期望 |
| --- | --- | --- |
| 有存储接入点 | `access_points` 数组 | 主表显示首选 endpoint，详情显示所有 endpoint |
| 只有旧 IP 凭据 | `in_band_ip + credential_ref_in_band` | 显示 fallback 待验证 |
| 有 credential_refs | `credential_refs.in_band/default` | 详情显示凭据引用集合 |
| catalog 缺失 | 有 `device_kind/vendor/model`，无 catalog | catalog 显示待补充，补充分类正常显示 |
| 多层状态冲突 | `record.manage_status=pending`、`attrs.manage_status=manageable` | 详情分层展示，不合并成一个成功 |
| 无 IP 无凭据 | 只有身份字段 | 管理状态显示仅登记/待补充 |

## 9. 开发顺序

推荐顺序：

1. 新增 `field-model.ts` 和类型。
2. 给 `field-model.ts` 写最小单元测试或独立样例。
3. 入库页先接 helper，只改展示和判断，不大改布局。
4. 管理页接 helper，先改 `mapDeviceRow()` 和详情栏。
5. 再补编辑 modal 的 access point 最低入口。
6. 最后补任务结果列。

不要一上来大面积重写页面模板。P0 的成功标准是字段口径准确，不是视觉完成度。

## 10. AI 自动开发约束

给 AI 继续开发时，必须带上这些硬约束：

1. 不允许删除旧 IP/credential 字段，兼容期仍要保留。
2. 不允许把 fallback 接入点标记为 detect success。
3. 不允许把 `device_kind/model/vendor` 当成 catalog。
4. 不允许把 `manage_status` 一个字段解释成全部状态。
5. 不允许在前端保存凭据明文。
6. 不允许只改 UI 文案，不改字段读取和 payload 构造。
7. 不允许把后端未返回的执行结果用草稿数据冒充。

这份任务单完成后，再进入 P1：系统版本、架构、CPU、内存、labels、group_tags、metadata 的结构化维护。
