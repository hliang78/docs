# D2 Redesign 真正上线 AI 自动开发指导书

更新时间：2026-05-13

本文是给 AI 自动开发使用的执行文档。目标是把 D2 设备导入、采集、入库、清册管理真正上线，同时不失去人工对代码、字段和行为的掌控力。

## 0. 结论

本轮真正上线改造的正式入口只有两个 redesign 页面：

| 用户给定路径 | 本机对应路径 | 页面定位 |
| --- | --- | --- |
| `/home/jacky/project/OneOPS-ALL/OneOps-UI/src/views/device/DeviceV2IngestPipelineRedesign.vue` | `/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/views/device/DeviceV2IngestPipelineRedesign.vue` | 设备导入、清单准备、基础入库提交、结果交接 |
| `/home/jacky/project/OneOPS-ALL/OneOps-UI/src/views/device/DeviceV2ManagementRedesign.vue` | `/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/views/device/DeviceV2ManagementRedesign.vue` | 清册管理、继续入库、采集证据、后续采集、设备维护 |

允许新增或修改支撑模块：

- `/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/views/device/device-v2-import/**`
- `/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/views/device/device-v2-redesign/**`
- `/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/api/device/device-v2.ts`
- `/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/api/device/device-v2-ingest.ts`
- `/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/api/device/device-v2-import.ts`
- `/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/typings/device/device_v2_import.ts`

允许参考和迁移能力，但不要把旧页面作为最终入口：

- `/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/views/device/DeviceV2Management.vue`
- `/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/views/device/DeviceV2ImportBatches.vue`
- `/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device/v2/**`

## 1. 上游文档优先级

AI 开发时必须按以下顺序读取和服从：

1. 字段主表：`/Users/huangliang/project/OneOPS-ALL/docs/openclaw-autodev/D2_INGEST_BASE_FIELD_TABLE.md`
2. 本指导书：`/Users/huangliang/project/OneOPS-ALL/docs/openclaw-autodev/D2_REDESIGN_AI_AUTODEV_GUIDE.md`
3. 上线重构规划：`/Users/huangliang/project/OneOPS-ALL/docs/openclaw-autodev/D2_FE_INGEST_MANAGEMENT_REDESIGN_PLAN.md`
4. P0 实施任务单：`/Users/huangliang/project/OneOPS-ALL/docs/openclaw-autodev/D2_FE_P0_IMPLEMENTATION_TASKS.md`
5. 缺口分析：`/Users/huangliang/project/OneOPS-ALL/docs/openclaw-autodev/D2_FE_REDESIGN_GAP_ANALYSIS.md`
6. 后端字段审计：`/Users/huangliang/project/OneOPS-ALL/docs/openclaw-autodev/D2_BACKEND_DEVICE_V2_INGEST_FIELD_AUDIT.md`

原则：

- 字段以字段主表为准。
- 页面以两个 redesign 文件为准。
- 能力以真实 API 和现有旧页面已验证逻辑为准。
- 任何文档和代码冲突时，先回到代码确认真实行为，再更新文档或写明缺口。

## 2. 真正上线范围

上线版必须覆盖完整生命周期：

```text
导入清单
  -> 本地解析/手工维护
  -> 后端 ingest 或 import batch 校验
  -> apply / submit 写入 Device V2
  -> 管理页聚焦本批设备
  -> 继续入库 store/start
  -> 采集/探测/事实 observations
  -> collection plans 后续采集建议
  -> 清册维护、筛选、详情、编辑
  -> 同步 V1/V2、变更历史、状态追溯
```

两个页面职责：

| 页面 | 必须上线的能力 |
| --- | --- |
| `DeviceV2IngestPipelineRedesign.vue` | 上传模板、解析清单、手工新增/批量编辑、字段校验、导入提交、任务结果、失败修复、交接到管理页 |
| `DeviceV2ManagementRedesign.vue` | 列表查询、详情、编辑、删除、批量选择、继续入库、store task 结果、runs、observations、collection plans、同步、变更历史入口 |

不能再把“采集、继续入库、监控接入”整体标成待契约。后端已有契约的能力必须被接入；后端确实没有契约的能力才允许禁用，并写明具体缺口。

## 3. 已有真实后端契约

### 3.1 Ingest API

文件：

- `/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device/v2/ingest/router/device_v2_ingest.go`
- `/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/api/device/device-v2-ingest.ts`

接口：

| 方法 | 路径 | 用途 |
| --- | --- | --- |
| GET | `/device/v2/ingest/capabilities` | 入库能力 |
| GET | `/device/v2/ingest/template/excel` | Excel 模板 |
| GET | `/device/v2/ingest/tasks` | 最近入库任务 |
| POST | `/device/v2/ingest/tasks` | JSON submit |
| POST | `/device/v2/ingest/tasks/upload` | Excel upload |
| GET | `/device/v2/ingest/tasks/:taskId` | 任务详情 |

上线要求：

- redesign 入库页可以继续使用该链路作为“快速导入/单批提交”。
- 必须补齐 `access_points/credential_refs/catalog/system/hardware` 的前端承接。
- 任务结果必须展示 `matched_by/manage_status/error/message`，后端未返回的字段不能伪造。

### 3.2 Import Batch API

文件：

- `/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device/v2/router/device_v2.go`
- `/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device/v2/api/device_v2_import_minimal_api.go`
- `/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/api/device/device-v2-import.ts`
- `/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/views/device/DeviceV2ImportBatches.vue`

接口：

| 方法 | 路径 | 用途 |
| --- | --- | --- |
| POST | `/device/v2/import/batches` | 创建批次 |
| POST | `/device/v2/import/batches/:batchId/upload` | 上传批次 |
| POST | `/device/v2/import/batches/:batchId/validate` | 校验 |
| POST | `/device/v2/import/batches/:batchId/apply` | 应用入库 |
| POST | `/device/v2/import/batches/:batchId/retry` | 重试 |
| POST | `/device/v2/import/batches/:batchId/records/update` | 批量修正记录 |
| GET | `/device/v2/import/batches` | 批次列表 |
| GET | `/device/v2/import/batches/:batchId/summary` | 批次摘要 |
| GET | `/device/v2/import/batches/:batchId/records` | 批次记录 |
| GET | `/device/v2/import/anchor-conflicts` | 锚点冲突 |
| GET | `/device/v2/import/anchor-basis` | 锚点依据 |
| GET | `/device/v2/import/templates/:importPass` | 分阶段模板 |

上线要求：

- redesign 入库页不能只保留 ingest 快速入口，还要能承接 import batch 的分阶段导入能力。
- `pass_1_base/pass_2_access/pass_3_credential/pass_4_relation` 至少要在 UI 里有明确入口或阶段说明。
- `pass_2_access` 和 `pass_3_credential` 是 `access_points` 和凭据绑定上线的关键，不可省略。

### 3.3 Device V2 Management API

文件：

- `/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device/v2/router/device_v2.go`
- `/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/api/device/device-v2.ts`

接口：

| 方法 | 路径 | 用途 |
| --- | --- | --- |
| GET | `/device/v2/list` | 列表查询 |
| POST | `/device/v2` | 创建 |
| GET | `/device/v2/:code` | 详情 |
| PUT | `/device/v2/:code` | 更新 |
| DELETE | `/device/v2/:code` | 删除 |
| GET | `/device/v2/:code/status` | 状态 |
| GET | `/device/v2/:code/store-readiness` | 入库就绪 |
| GET | `/device/v2/:code/network-overview` | 网络概览 |
| GET | `/device/v2/:code/interfaces` | 接口 |
| GET | `/device/v2/:code/change-history` | 变更历史 |
| POST | `/device/v2/:code/change-history/:id/status` | 变更状态更新 |

上线要求：

- redesign 管理页必须支持真实列表、详情、编辑、删除。
- 详情中必须按字段主表展示身份、平台/catalog、接入点、状态层、系统画像、硬件画像、来源。
- 编辑不能只依赖 `attributes_json`，至少要给核心字段结构化入口。

### 3.4 Store / Collection API

文件：

- `/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device/v2/api/device_v2_store_minimal_api.go`
- `/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/api/device/device-v2.ts`
- `/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/views/device/DeviceV2Management.vue`

接口：

| 方法 | 路径 | 用途 |
| --- | --- | --- |
| POST | `/device/v2/store/start` | 开始继续入库 |
| POST | `/device/v2/store/retry` | 重试流水线 |
| GET | `/device/v2/tasks/:taskId` | pipeline task |
| GET | `/device/v2/tasks/:taskId/summary` | task summary |
| GET | `/device/v2/tasks/:taskId/runs` | 单设备 runs |
| GET | `/device/v2/tasks/:taskId/observations` | 采集/入库事实 |
| GET | `/device/v2/tasks/:taskId/collection-plans` | 后续采集计划 |
| GET | `/device/v2/:code/last-store-collection-dc2` | 最近 DC2 采集 |

上线要求：

- redesign 管理页必须收编旧 `DeviceV2Management.vue` 中的继续入库、结果抽屉、自动刷新、runs、observations、collection plans、DC2 证据展示能力。
- “采集”在 D2 上线版里不是装饰按钮，必须展示真实 task/runs/observations。
- `collection-plans` 是后续采集入口的依据，不能用静态文案替代。

## 4. 字段硬规则

AI 自动开发必须遵守：

| 规则 | 说明 |
| --- | --- |
| `access_points` 是一等数据 | controller detect 或 store/collection 成功的访问点必须能展示 |
| `credential_refs` 只存引用 | 不展示、不保存密码、community、token 明文 |
| `catalog` 独立 | `device_kind/vendor/model/device_type` 不能冒充 catalog |
| `manage_status` 分层 | entity、ingest result、store readiness、attributes 不能混为一个标签 |
| fallback 要标明 | 旧 `IP + credential` 可兼容，但不能显示成 detect success |
| 后端未返回不能伪造 | task result 没有 access point 就显示未返回，不从草稿冒充 |
| 高级 JSON 不是唯一入口 | 核心字段必须有结构化维护方式 |

核心字段分组必须贯穿两个页面：

1. 身份：`code/biz_code/name/biz_name/sn/asset_number/hostname`
2. 平台/catalog：`platform/platform_code/platform_name/catalog/catalog_code/catalog_name`
3. 接入点：`access_points[]`
4. 凭据引用：`credential_ref_*`、`credential_refs`
5. 状态层：`status/manageable/manage_status/manageable_status/core_store_status`
6. 位置：`tenant/region/site/rack/location_node_code`
7. 系统画像：`system_version/patch_version/firmware_version/kernel_version/os_name/os_version/architecture`
8. 硬件画像：`cpu_arch/cpu_model/cpu_cores/cpu_sockets/memory_total/memory_total_bytes/memory_slots/hardware`
9. 来源：`source/batch_id/task_id/run_id/matched_by/row_no`

## 5. 页面改造策略

### 5.1 入库页

目标文件：

`/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/views/device/DeviceV2IngestPipelineRedesign.vue`

必须实现的上线能力：

| 能力 | 要求 |
| --- | --- |
| 模板下载 | 支持 ingest 模板，后续补 import pass 模板入口 |
| 文件上传 | 至少 XLSX；如 UI 写 CSV，必须确认后端路径支持，不能假写 |
| 草稿解析 | 支持字段主表里的核心字段 |
| 手工新增/批量编辑 | 支持身份、平台、catalog、接入点、凭据、位置 |
| 本地校验 | identity、platform、catalog、access point、JSON |
| 任务提交 | 支持 `submitDeviceV2IngestTaskReq`；如走 import batch，要清晰分流 |
| 任务结果 | 展示 stages、validation issues、execution results、matched_by、manage_status |
| 交接管理页 | 用 codes/task_id 聚焦，不把状态映射写死 |

可以收编：

- `DeviceV2ImportBatches.vue` 的批次创建、上传、validate、apply、records、summary 逻辑。
- `device-v2-import/**` 的草稿表格、字段配置、批量编辑组件。

### 5.2 管理页

目标文件：

`/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/views/device/DeviceV2ManagementRedesign.vue`

必须实现的上线能力：

| 能力 | 要求 |
| --- | --- |
| 列表 | 服务端分页、keyword/codes/ip/manage_status/management_path 等已确认筛选 |
| 详情 | 按字段主表分组展示 |
| 编辑 | 结构化维护核心字段，JSON 放高级区 |
| 删除 | 保留真实 delete 操作和确认 |
| 继续入库 | 接入 `startDeviceV2StorePipelineReq` |
| 任务结果 | 接入 task、summary、runs、observations、collection-plans |
| 采集证据 | 显示 DC2 或 store observation 的真实事实 |
| 后续采集 | 根据 collection plans 展示可执行/不可执行项 |
| 同步 | 收编 sync-from-v1 / sync-to-v1 已有能力 |
| 变更历史 | 至少保留入口和只读展示 |

必须从旧页迁移或复用：

- `openStoreStartModal`
- `openBatchStoreStartModal`
- `buildStoreStartRequestPayload`
- `submitStoreStart`
- `loadStoreStartTaskDetails`
- `refreshStoreStartTask`
- store result drawer 的 summary/runs/observations/collection plans 展示逻辑
- `resolveStoreStartStoredCredentialRef`
- `goToStoreStartDC2RunDetail`
- sync-from-v1 / sync-to-v1 操作

迁移时要重构为更清晰的 composable 或组件，不要把旧页几千行原样复制进 redesign 页面。

## 6. 推荐工程结构

优先拆成小模块，避免两个 Vue 文件继续膨胀：

```text
src/views/device/device-v2-redesign/
  field-model.ts              # 共享字段读取、access point、状态层、catalog helper
  lifecycle.ts                # 导入->入库->采集->管理 生命周期判断
  store-task.ts               # store/start、task detail、runs、observations、plans 组合逻辑
  import-flow.ts              # ingest/import batch 分流和交接逻辑
  management-mappers.ts       # DeviceV2Item -> table/detail view model
  validation.ts               # 草稿和编辑校验
  components/
    AccessPointTable.vue
    CredentialRefsView.vue
    DeviceFieldSections.vue
    StoreTaskResultDrawer.vue
    CollectionPlanTable.vue
    DeviceEditDrawer.vue
```

如果暂时不建组件，也至少把纯函数 helper 放到 `.ts` 文件，避免把所有业务逻辑堆在 `.vue`。

## 7. AI 自动开发分阶段任务

每个阶段必须小步提交、可 typecheck、可人工 review。

### 阶段 A：字段模型地基

目标：

- 新增 `field-model.ts`
- API 类型补 `AccessPoint/CredentialRefs/SystemProfile/HardwareProfile/CollectionPlan`
- 两个 redesign 页面先接 helper，但不大改 UI

验收：

- `npm run typecheck:d2` 通过
- 管理页读取 access point、credential refs、catalog、状态层不报错

### 阶段 B：入库页上线化

目标：

- 草稿字段补 `access_points/credential_refs/catalog/system/hardware`
- `isDraftManageable` 改为 access point 优先
- result 表补 `matched_by/manage_status/error_code`
- 交接管理页用 codes/task_id 聚焦

验收：

- 有旧 IP + 凭据时显示 fallback
- 有 access point success 时显示接入点成功
- catalog 缺失不会被 device_kind/model 顶替

### 阶段 C：管理页清册上线化

目标：

- 主表列改成身份、平台/catalog、接入点、状态层、系统/硬件摘要、来源
- 详情按字段主表分组
- 编辑 drawer 支持核心字段结构化维护

验收：

- `access_points` 数组能完整展示
- `credential_refs` 能解释 endpoint 凭据来源
- 多层 `manage_status` 不合并为一个成功/失败

### 阶段 D：继续入库和采集证据

目标：

- 迁移 store/start modal 或 drawer
- 接入 task summary、runs、observations、collection-plans
- 展示 DC2 采集证据和后续采集计划

验收：

- 从管理页能对单台/多台设备发起 store/start
- 能看到 task/runs/observations/collection plans
- 没有 observations 时不能宣称“已采集成功”

### 阶段 E：导入批次能力融合

目标：

- 把 import batch 的 validate/apply/records/summary 能力融合到入库页，或提供清晰入口
- 支持 pass_1_base/pass_2_access/pass_3_credential/pass_4_relation 的阶段展示

验收：

- 能创建批次、上传、校验、apply
- access 和 credential pass 的结果能进入管理页 access points/credential refs 展示

### 阶段 F：上线收口

目标：

- 完成错误态、空态、loading、权限、确认弹窗
- 清理“待契约”按钮，只保留真实缺口
- 补手工验收脚本和截图说明

验收：

- `npm run typecheck:d2` 通过
- 页面能完整跑一条“导入 -> 入库 -> 继续入库 -> 查看采集证据 -> 管理维护”流程

## 8. 每轮 AI 开发任务模板

给 AI 下发任务时，建议使用这个模板：

```text
任务：D2 Redesign 阶段 <A/B/C/D/E/F> - <具体目标>

目标页面：
- DeviceV2IngestPipelineRedesign.vue
- DeviceV2ManagementRedesign.vue

必须读取：
- docs/openclaw-autodev/D2_INGEST_BASE_FIELD_TABLE.md
- docs/openclaw-autodev/D2_REDESIGN_AI_AUTODEV_GUIDE.md
- 相关 API 文件和旧页面实现

允许修改：
- <列出本轮文件>

禁止：
- 不要改无关页面
- 不要删除旧 IP/credential 兼容字段
- 不要伪造 detect success
- 不要把 device_kind/model 当 catalog
- 不要把所有状态合成一个 manage_status
- 不要保存凭据明文

验收：
- npm run typecheck:d2
- <本轮具体 UI/数据验收>

输出：
- 变更文件列表
- 字段流说明
- 已运行测试
- 未解决缺口
```

## 9. Review 检查清单

每轮 review 必须问：

| 问题 | 通过标准 |
| --- | --- |
| 是否仍然只围绕两个 redesign 页面？ | 没有把旧页面变成正式入口 |
| 是否复用了真实 API？ | 没有 mock 数据冒充上线 |
| 字段是否按主表分组？ | 一等字段都有稳定位置 |
| access point 是否成为核心？ | 不是只显示裸 IP |
| 凭据是否安全？ | 只显示 ref，不显示明文 |
| 状态是否分层？ | entity/ingest/store 不混用 |
| 旧能力是否被收编？ | store/import/DC2 等真实能力未丢失 |
| 后端缺口是否明确？ | 禁用项写明缺哪个接口或字段 |
| 是否 typecheck？ | `npm run typecheck:d2` 通过或说明原因 |

## 10. 最终上线验收场景

至少要手工验收这些场景：

1. 上传一份基础设备清单，解析成功，能看到身份、平台、catalog、接入点、凭据。
2. 有问题的行能定位到字段，修复后可提交。
3. 提交入库后能看到 task stages 和每台设备 result。
4. 点击交接后，管理页聚焦本批设备。
5. 管理页详情能看到 access points、credential refs、状态层、系统/硬件画像。
6. 单台设备执行继续入库，能看到 task summary、runs、observations。
7. 批量设备执行继续入库，有确认弹窗和结果抽屉。
8. collection plans 显示后续可采集项和不可采集原因。
9. 没有采集证据时，页面不显示“采集成功”。
10. 编辑设备核心字段后，列表和详情能刷新显示。
11. sync-from-v1 / sync-to-v1 不破坏 V2 字段主表口径。
12. 删除设备有确认，有错误提示。

## 11. 测试命令

前端最低命令：

```bash
cd /Users/huangliang/project/OneOPS-ALL/OneOPS-UI
npm run typecheck:d2
```

如改动影响更多公共类型，再运行：

```bash
cd /Users/huangliang/project/OneOPS-ALL/OneOPS-UI
npm run typecheck
```

后端如改 Device V2 API 或 DTO，至少运行：

```bash
cd /Users/huangliang/project/OneOPS-ALL/OneOPS
go test ./app/device/v2/...
go test ./app/device/v2/ingest/...
```

## 12. 最重要的边界

这次不是做一个新的演示页。  
这次是把两个 redesign 页面变成 D2 的真实生产入口。

因此 AI 自动开发必须做到：

- 保留真实后端能力。
- 收编旧页面成熟能力。
- 按字段主表重新组织。
- 不伪造采集和入库证据。
- 每个按钮都能说明调用哪个 API、输入哪些字段、写回哪里。

完成后的状态应该是：用户可以从 redesign 入库页开始，完成导入、采集、入库、管理全流程；开发者也能沿着字段主表理解每一个字段从哪里来、到哪里去、为什么这样展示。
