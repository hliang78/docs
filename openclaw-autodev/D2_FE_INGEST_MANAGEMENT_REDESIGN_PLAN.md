# D2 入库页与管理页重构规划

更新时间：2026-05-13

基准文档：

- 主字段表：`/Users/huangliang/project/OneOPS-ALL/docs/openclaw-autodev/D2_INGEST_BASE_FIELD_TABLE.md`
- 缺口分析：`/Users/huangliang/project/OneOPS-ALL/docs/openclaw-autodev/D2_FE_REDESIGN_GAP_ANALYSIS.md`

定位：本文不是新的字段源。字段以主字段表为准，本文只规划前端如何把字段主表落到入库页和管理页，让 AI 自动开发可以执行，同时让人能理解、核对、记忆和控制。

## 0. 设计方向

Context：D2 是高密度运维工作台，用户要在入库、补齐、采集、纳管之间判断每个字段是否可信、从哪里来、写到哪里去。

Anchor：Swiss。使用中性浅底、单一蓝色强调、左对齐文字、1px 规则线和编号轨道，适合把复杂字段拆成可核验的清册界面。

Differentiator：所有页面围绕一条“字段证据轨道”展开，每台设备都能看到身份、访问接入点、系统硬件画像三段事实，不再把 IP、凭据、类型、状态散落到各处。

System：继续使用 Ant Design Vue，保持 OneOPS 现有产品 UI；页面主色不新增花哨主题，强调色只用于当前步骤、主按钮、选中状态和关键证据。

Implementation：先补共享字段模型和读取 helper，再改入库草稿和管理详情，最后改表格列、筛选和批量动作。

## 1. 总体判断

当前 redesign 页的问题不是“不能用”，而是“没有围绕字段主表组织”。页面已经接了真实 API，但一等字段没有成为界面骨架。

必须重新确立两个页面的职责：

| 页面 | 核心职责 | 不该承担 |
| --- | --- | --- |
| 入库页 | 把 Excel/JSON/手工输入整理成 canonical device payload，展示校验、匹配、写库结果 | 不负责长期清册维护，不把采集动作做成主流程 |
| 管理页 | 查看、补齐、验证、维护已入库设备，承接采集和纳管证据 | 不重新解释入库任务，不隐藏字段来源 |

核心重构原则：

1. 一等数据决定页面骨架。
2. 二等数据解释结果，放到详情和分组表单。
3. 三等数据放高级区，不抢主流程。
4. 任何 AI 自动开发都必须能回答字段的来源、处理、去处、边界。
5. 页面不做“聪明推断”，只展示后端结果和明确的兼容 fallback。

## 2. 共享字段模型

前端需要先建立共享类型和 helper，否则两个页面会继续各读各的 `attributes/metadata`。

建议新增或集中到 `OneOPS-UI/src/views/device/device-v2-redesign/field-model.ts`：

| 模型 | 包含字段 | 用途 |
| --- | --- | --- |
| `DeviceIdentityView` | `code/biz_code/name/biz_name/sn/asset_number/hostname` | 身份摘要、重复判断、搜索展示 |
| `PlatformCatalogView` | `platform/platform_code/platform_name/catalog/catalog_code/catalog_name/device_kind/device_type/model/vendor` | 明确平台、catalog、补充分类三者关系 |
| `AccessPointView` | `endpoint_id/plane/ip/ip_code/login_method/login_port/transport/credential_ref/priority/detected/detect_status/detect_source/last_detected_at/evidence` | 入库和管理的接入点主结构 |
| `CredentialRefsView` | `in_band/out_band/snmp/default/winrm` 等引用 | 解释 endpoint 凭据来源，只显示 ref |
| `ManageStatusLayersView` | `entity_manage_status/ingest_manage_status/manageable/manageable_status/core_store_status` | 拆开多层状态语义 |
| `SystemProfileView` | `system_version/patch_version/firmware_version/kernel_version/os_name/os_version/architecture` | 系统画像 |
| `HardwareProfileView` | `cpu_arch/cpu_model/cpu_cores/cpu_sockets/memory_total/memory_total_bytes/memory_slots/hardware` | CPU、内存、硬件画像 |
| `FieldSourceView` | `source/batch_id/row_no/task_id/matched_by/locator_trace` | 解释字段来源和命中路径 |

必须提供的 helper：

| helper | 作用 |
| --- | --- |
| `readDeviceIdentity(record)` | 从顶层、attributes、metadata 统一读身份字段 |
| `readPlatformCatalog(record)` | 平台、catalog、补充分类分层读取 |
| `readCredentialRefs(record)` | 读取并归一化顶层凭据和 `credential_refs` |
| `readAccessPoints(record)` | 优先读取 `attributes.access_points`，必要时由旧 IP + credential fallback 生成只读接入点 |
| `readManageStatusLayers(record, taskResult?)` | 拆分 entity、ingest、store readiness 状态 |
| `readSystemProfile(record)` | 系统版本和 OS/架构字段 |
| `readHardwareProfile(record)` | CPU、内存、硬件明细字段 |
| `buildIngestDeviceFromDraft(row)` | 草稿行到后端 submit payload，不能丢 `access_points/metadata/labels/group_tags` |

边界：

- helper 可以做展示 fallback，但不能把 fallback 冒充成后端已写入事实。
- 凭据只能显示 `credential_ref`，不能接收或展示密码、community 明文。
- `device_kind/model/vendor` 只能显示为补充分类，不能替代 `catalog`。

## 3. 入库页规划

### 3.1 页面目标

入库页要回答四个问题：

1. 这台设备是谁。
2. 属于哪个平台和 catalog。
3. 有哪些访问接入点，哪些已经被探测成功。
4. 提交后写入、更新、失败、仅登记的原因是什么。

### 3.2 信息架构

建议结构：

| 区域 | 内容 | 字段层级 |
| --- | --- | --- |
| 顶部窄头部 | 页面名、批次号、上传、下载模板、提交 | 三等动作信息 |
| 批次侧栏 | 最近批次、能力状态、入库边界 | 三等上下文 |
| 字段准备总览 | 设备数、身份完整、接入点成功、catalog 完整、待修复 | 一等汇总 |
| 草稿表格 | 设备、平台/catalog、主接入点、纳管判断、问题数、来源行 | 一等主视图 |
| 行详情抽屉 | 分组维护所有字段 | 一等、二等、三等 |
| 任务结果 | 阶段、执行结果、matched_by、manage_status、接入点证据 | 一等结果 |

不要继续把页面核心放在“可纳管数量”一个指标上。可纳管必须被解释为：成功接入点 + 凭据引用，兼容期才回退到 IP + credential。

### 3.3 草稿表格列

| 列 | 显示 | 来源 |
| --- | --- | --- |
| 设备 | `biz_name/name/code/biz_code`，副行显示 `sn/asset_number/hostname` | 一等身份 |
| 平台/catalog | 主行 `platform_code/name`，副行 `catalog_code/name`，补充行 `device_kind/vendor/model` | 一等 + 二等 |
| 访问接入点 | 首选成功 endpoint，显示 `plane ip method:port` | `access_points` 或 fallback |
| 凭据 | `credential_ref` 摘要，隐藏明文 | `credential_refs`、endpoint |
| 入库判断 | `可写入/待修复/仅登记/冲突` | 校验和身份定位 |
| 纳管判断 | `可纳管/仅登记/未知`，并显示依据 | `access_points` 优先 |
| 来源 | Excel 行号、批次、任务 | 三等追踪 |

### 3.4 行详情抽屉

用抽屉而不是大 modal。抽屉左侧保留设备摘要，右侧使用 tabs：

| Tab | 字段 | 交互 |
| --- | --- | --- |
| 身份 | `code/biz_code/biz_name/name/sn/asset_number/hostname` | 必填/定位字段高亮，显示命中顺序 |
| 平台与类型 | `platform/platform_code/platform_name/catalog/catalog_code/catalog_name/device_kind/vendor/model/device_model_*` | platform/catalog 用 select 或可搜索输入；补充分类为文本 |
| 访问接入点 | `access_points[]` 全字段 | 表格编辑；支持从 `in_band/out_band` 自动生成；detect 成功行只读标记证据 |
| 凭据引用 | `credential_ref_*`、`credential_refs` | 只填 ref；显示 endpoint 继承关系 |
| 位置 | `tenant_*、region_*、site_*、rack_*、rack_position、location_node_code` | 分层展示，层级不一致时错误显式 |
| 系统/硬件画像 | 系统版本、OS、架构、CPU、内存 | 可选字段，标注“采集/解析补充” |
| 标签与高级 | `labels/group_tags/metadata/attributes_json` | JSON 作为高级入口，提交前做解析校验 |

### 3.5 入库校验口径

提交前校验分三层：

| 层级 | 必须满足 | 不满足时 |
| --- | --- | --- |
| P0 身份 | 至少命中一个 locator：`code/biz_code/sn/asset_number/in_band_ip/out_band_ip/hostname` | 阻止提交 |
| P0 平台 | `platform` 或 `platform_code` 可解析 | 阻止提交或明确后端会失败 |
| P0 接入点 | 有 IP 时生成 access point；有 detect 成功结果时保留证据 | 不阻止基础入库，但标记仅登记 |
| P1 catalog | 有 catalog 输入时必须独立解析 | 不用 `device_kind/model` 代替 |
| P1 系统硬件 | 字段类型正确，CPU/内存数字单位清晰 | 可提交，但给 warning |
| P2 高级 JSON | JSON 合法，不覆盖一等字段冲突 | 不合法阻止提交 |

### 3.6 任务结果展示

设备处理结果表必须补这些列：

| 列 | 原因 |
| --- | --- |
| `matched_by` | 告诉用户为什么命中已有设备 |
| `manage_status` | 展示 ingest 结果语义，不混成 entity 状态 |
| `access_point` | 显示用于判断的接入点或 fallback 来源 |
| `credential_ref` | 解释凭据引用，不能展示明文 |
| `message/error_code` | 失败时给可复制原因 |

## 4. 管理页规划

### 4.1 页面目标

管理页要回答五个问题：

1. 清册里有哪些设备。
2. 每台设备的核心字段是否完整。
3. 当前可访问路径是什么，证据来自哪里。
4. 系统、架构、CPU、内存画像是否已有。
5. 下一步是补字段、重试入库、采集验证，还是进入监控。

### 4.2 信息架构

建议结构：

| 区域 | 内容 | 字段层级 |
| --- | --- | --- |
| 顶部窄头部 | 刷新、新建、更多动作 | 三等 |
| 工作域切换 | 清册、接入、采集、监控、变更、来源 | 业务导航 |
| 左侧视图 | 全部、可纳管、仅登记、待补齐、采集待处理 | 一等状态分组 |
| 过滤区 | 关键词、code、platform、catalog、manage status、site/rack | 一等 + 二等 |
| 主表 | 设备身份、平台/catalog、主接入点、状态分层、画像摘要、来源 | 一等主视图 |
| 详情栏/抽屉 | 完整字段分组、接入点、画像、来源、操作 | 一等 + 二等 |

当前右侧 detail rail 可以保留，但需要按字段主表重排，不再只放“资产摘要、来源与变更、采集与监控”三块。

### 4.3 主表列

| 列 | 显示 | 关键边界 |
| --- | --- | --- |
| 设备 | `name/code`，副行 `biz_code/sn/hostname` | 身份字段不缺位 |
| 平台/catalog | platform 和 catalog 分两行 | catalog 缺失不能用 device_kind 顶替 |
| 接入点 | 首选成功接入点；无成功时显示 fallback 或缺失 | 明确 `detected/fallback/unknown` |
| 纳管状态 | entity、ingest、store readiness 分层摘要 | 不把 `success/pending/manageable` 混为一个含义 |
| 系统画像 | OS/版本/架构摘要 | 缺失显示待采集，不显示假值 |
| 硬件画像 | CPU/内存摘要 | 单位固定，未知保持未知 |
| 位置 | region/site/rack/rack_position | 层级异常可标记 |
| 来源 | source/batch/task/matched_by | 便于追溯 |

### 4.4 详情结构

详情使用固定分组，顺序与字段主表一致：

| 分组 | 内容 | 操作 |
| --- | --- | --- |
| 01 身份 | code、biz_code、name、sn、asset、hostname | 维护资料 |
| 02 平台与类型 | platform、catalog、device_kind、vendor、model、device_model | 选择主数据 |
| 03 访问接入点 | access_points 表格、credential_refs、detect evidence | 绑定凭据、重试探测 |
| 04 状态层 | status、manageable、manage_status、manageable_status、core_store_status | 查看解释，不直接手填派生状态 |
| 05 位置 | tenant、region、site、rack、location_node_code | 维护位置 |
| 06 系统画像 | system/patch/firmware/kernel/os/architecture | 由采集或手工补齐 |
| 07 硬件画像 | CPU、内存、hardware 明细 | 由采集或手工补齐 |
| 08 来源与高级 | labels、group_tags、metadata、attributes JSON | 高级编辑，需差异预览 |

### 4.5 编辑方式

编辑不能再只靠 `attributes_json`：

| 编辑层 | 控件 | 保存方式 |
| --- | --- | --- |
| 常用字段 | 普通表单、select、tag input | 写顶层和受控 attributes |
| access_points | 表格行编辑 | 写 `attributes.access_points` |
| credential_refs | key/value ref 编辑 | 写 `attributes.credential_refs` |
| system/hardware | 分组表单 | 写 metadata 或 attributes，按后端契约固定 |
| labels/group_tags | tag 控件 | 写顶层 `labels/group_tags` |
| 高级 JSON | 折叠区 textarea | 保存前做 JSON parse、差异预览、敏感字段阻断 |

关键限制：

- 不能允许用户直接修改派生状态来伪造可纳管。
- `access_points.detected=true` 必须来自 detect 或后端证据，手工新增只能是 `unknown/manual`。
- 旧字段 `in_band_ip/out_band_ip` 可以继续维护，但要同步或提示生成接入点。

## 5. 视觉与交互规划

### 5.1 视觉语言

| 项 | 方案 |
| --- | --- |
| 页面底色 | 中性浅底，避免深色监控风 |
| 结构 | 1px 规则线、表格、抽屉、分组标题 |
| 强调 | 单一蓝色只用于当前状态、主操作、选中行、成功证据 |
| 字体 | 继续系统 sans，数字用 tabular 视觉 |
| 卡片 | 只用于重复项或清晰分组，不做层层嵌套 |
| 动效 | 150-220ms，用于展开、保存、状态切换 |

### 5.2 记忆方式

页面要帮助用户记住字段，而不是要求用户背字段：

| 记忆锚点 | 内容 |
| --- | --- |
| 01 身份 | 设备是谁 |
| 02 平台/catalog | 设备归属和类型 |
| 03 接入点 | 怎么访问，凭据引用是什么 |
| 04 状态层 | 入库、纳管、store readiness 分开 |
| 05 位置 | 在哪里 |
| 06 系统画像 | 跑什么系统 |
| 07 硬件画像 | CPU/内存/架构是什么 |
| 08 来源 | 从哪来、谁写的、为何命中 |

这套编号要贯穿入库草稿、管理详情和后续开发文档。

## 6. 研发拆分

### P0：把一等字段落地

| 任务 | 文件 |
| --- | --- |
| 增加共享 field model 和 helper | `OneOPS-UI/src/views/device/device-v2-redesign/field-model.ts` |
| 前端 API 类型补 `AccessPoint/CredentialRefs/SystemProfile/HardwareProfile` | `OneOPS-UI/src/api/device/device-v2.ts`、`device-v2-ingest.ts` |
| 入库草稿支持 `access_points/credential_refs/catalog_*` | `device-v2-import/field-config.ts`、`device-mapping.ts` |
| 入库可纳管判断改为 access point 优先 | `useDeviceV2IngestDraft.ts` |
| 管理页详情展示 access points 和状态层 | `DeviceV2ManagementRedesign.vue` |

验收：

- 有 controller detect 成功接入点时，入库页和管理页都能看到 endpoint、凭据 ref、探测状态。
- 没有 detect 结果但有旧 IP + credential 时，页面显示 fallback，不显示为已探测成功。
- platform 和 catalog 分开展示，device_kind/model 不再冒充 catalog。

### P1：补齐二等字段

| 任务 | 文件 |
| --- | --- |
| 系统版本、架构、CPU、内存进入详情 | 管理页详情和 field helper |
| 入库页增加系统/硬件画像可选字段 | 入库草稿模块 |
| labels/group_tags/metadata 结构化维护 | 入库页、管理页编辑抽屉 |
| task result 补 matched_by、manage_status、access point 依据 | 入库页任务结果表 |

验收：

- `system_version/patch_version/firmware_version/architecture/cpu_*/memory_*` 有固定展示位置。
- 字段缺失时显示“待采集/待补充”，不生成假值。
- 高级 JSON 不再是唯一编辑入口。

### P2：动作与自动开发闭环

| 任务 | 说明 |
| --- | --- |
| collection plan 展示 | 展示 `next_collection_plan/manageable_pending_reasons` |
| 采集验证入口 | 从成功接入点选择目标，不从裸 IP 盲跑 |
| 监控接入入口 | 只允许在接入点和凭据证据完整时开放 |
| 字段差异预览 | 保存前展示顶层、attributes、metadata、labels 的变化 |

验收：

- 每个动作都能解释输入字段和写回字段。
- AI 生成代码前能定位字段所属层级和页面落点。

## 7. 当前最大缺口

最大的缺口仍然是 `access_points` 没有成为前端主模型。

它带来的连锁问题：

1. 入库页仍像旧模型一样围绕 IP 和凭据判断。
2. 管理页不能解释 controller detect 成功的访问事实。
3. 采集、纳管、监控动作没有稳定目标。
4. 用户无法记住“凭据到底绑定在哪里”。

因此下一轮开发不要先美化表格，也不要先加更多统计。先做：

1. 共享字段模型。
2. 入库草稿 access point。
3. 管理详情 access point。
4. 状态层拆分。
5. catalog 和硬件画像补位。

这五件事完成后，D2 前端才会从“可运行页面”进入“可控上线页面”。
