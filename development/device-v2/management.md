# Device V2 设备管理工程文档初稿

| 项目 | 内容 |
| --- | --- |
| 文档状态 | `blocked-human-confirmation` |
| 人工确认人 | `[待人工确认: 项目负责人]` |
| 人工确认日期 | `[待人工确认: 项目负责人]` |
| 适用范围 | 设备 V2 清册管理、详情、编辑、删除或保留、store/start、task evidence 的文档整理 |

> 本文仅用于汇总 Device V2 设备管理方向的已记录证据、缺口和人工确认项。当前状态为 `blocked-human-confirmation`，**不可直接**作为开发、测试、上线、story 发布或验收依据。

## 1. 文档边界

本文只整理来源材料，不确认以下内容：

- 不确认清册字段、详情页字段、编辑表单、删除策略、保留策略或正式交互。
- 不确认 API path、DTO、数据库字段、fixture、权限模型、性能目标或采集协议。
- 不把 D2 launch evidence 中的阶段性结果提升为长期工程规范。
- 不把 `D2LA_*` 克隆样本的局部证据反推为完整上线验收通过。
- 不执行或指导任何生产操作、真实删除、批量采集、凭证暴露或外部集成变更。

## 2. 来源材料索引

| 来源 | 可提炼内容 | 使用限制 |
| --- | --- | --- |
| `docs/prd-autodev/oneops-engineering-docs-standardization/idea.md` | AI/autodev 只能整理、提炼、占位、标风险 | 不可反推需求、设计、业务规则、架构、API、数据模型或验收标准 |
| `docs/development/prompt-assets-analysis.md` | prompt assets 到正式工程文档的治理链路 | prompt 内容不能直接变成开发依据 |
| `docs/prd-autodev/d2-launch-acceptance/evidence-index.md` | Management list、field reconciliation、store readiness/start、task summary、runs、observations、latest DC2 的 evidence 摘要 | 只记录 evidence 状态，不自动确认 launch PASS |
| `docs/prd-autodev/d2-launch-acceptance/launch-readiness-report.md` | 设备 V2 清册管理页级 `BLOCKED` 结论与人工决策点 | 不可替代正式产品或验收确认 |
| `docs/openclaw-autodev/shared-d2.md` | D2 FE/BE 协作记录、阶段性 evidence 路径和真实操作 harness 线索 | 只作为 evidence 路径索引，不复制凭证、不执行生产动作 |

## 3. 设备管理流程草图（不可直接执行）

以下流程只是从 evidence 和协作记录中整理出的候选叙述，当前**不可直接**用于开发、联调、测试或验收。每一步的输入、输出、字段、权限、错误状态、采集行为和删除边界都需要人工确认。

| 阶段 | 候选说明 | 当前状态 |
| --- | --- | --- |
| 清册定位 | `[候选方案: AI 提炼]` evidence 中记录过通过管理清册或 list 查询定位 approved `D2LA_*` clones，并用于入库 handoff 后的可见性检查。 | `[待人工确认: 产品负责人]` 清册入口、筛选条件、搜索字段、分页排序和空态口径未确认。 |
| 详情查看 | `[候选方案: AI 提炼]` 清册结果可作为详情核对入口，已记录过 endpoint/protocol/port 与 credential-ref preservation 的对账事实。 | `[待人工确认: 技术负责人]` 详情字段分组、脱敏规则、源记录映射和可见权限未确认。 |
| 编辑/修改 | `[候选方案: AI 提炼]` 既有 launch evidence 明确 UI edit/update 对 cloned `D2LA_*` device 为 `NOT RUN`。 | `[待人工确认: 产品负责人]` 编辑是否 launch 必须项、允许编辑字段、低风险字段选择和保存失败语义未确认。 |
| 删除或保留 | `[候选方案: AI 提炼]` evidence 要求 clone cleanup/delete 仍是 operational/destructive boundary；import batch/task/row records 应保留为证据。 | `[待人工确认: 产品负责人]` exact-code 删除时机、保留策略、禁止删除原始记录边界和审计要求未确认。 |
| store readiness | `[候选方案: AI 提炼]` approved 2-row scope 曾记录 store readiness 恢复/可用线索，并进入后续 store start。 | `[待人工确认: 技术负责人]` readiness 条件、凭证引用、access point、协议 detect 和阻断语义未确认。 |
| store/start | `[候选方案: AI 提炼]` approved 2 clones 曾记录 store/start task evidence；优先从设备管理 UI 触发，UI blocked 时记录 API fallback 原因。 | `[待人工确认: 技术负责人]` 触发入口、幂等、重试、并发、权限和错误分类未确认。 |
| task evidence | `[候选方案: AI 提炼]` approved 2 clones 曾记录 task summary、runs、observations、latest DC2；完整 5-device parallel collection 未完成。 | `[待人工确认: 测试负责人]` task evidence 的必需字段、成功/失败判定、freshness 和验收表达未确认。 |

## 4. 已记录的设备管理证据事实

以下内容仅表示“已有 evidence 记录过”，不得直接扩展为正式规则：

- `[候选方案: AI 提炼]` Management list/handoff：approved imported clones 曾在管理清册路径中被定位或核对；该事实只证明局部 handoff 证据存在。
- `[候选方案: AI 提炼]` Field reconciliation：approved 2-row path 曾核对 endpoint/protocol/port 和 credential refs；3 个 skipped candidates 仍是独立 blocker，不是已验收差异。
- `[候选方案: AI 提炼]` Store readiness/start：approved 2 clones 曾有 readiness、store task 和 task summary 证据。
- `[候选方案: AI 提炼]` Runs/observations/latest DC2：approved 2 clones 曾有真实 observations 与 latest DC2 evidence；不可反推为 5-device parallel collection PASS。
- `[候选方案: AI 提炼]` Edit/update：Batch 001-004 没有 cloned `D2LA_*` UI edit/update evidence，状态应保持 `NOT RUN` 或 `BLOCKED`，除非人工另行接受风险。
- `[候选方案: AI 提炼]` Delete cleanup：clone delete cleanup 和 final cleanup report 没有完成；删除相关内容不得自动转成可执行策略。
- `[候选方案: AI 提炼]` Launch readiness 对设备 V2 清册管理的页级结论仍是 `BLOCKED`，原因包括 UI edit 缺失、clone delete cleanup 缺失、5-device parallel collection 不完整和权限姿态未确认。

## 5. 清册与详情候选信息架构（待确认）

| 区域 | 候选用途 | 人工确认项 |
| --- | --- | --- |
| 清册列表 | `[候选方案: AI 提炼]` 展示设备身份、平台/catalog、位置、接入、状态、来源、更新时间和操作入口。 | `[待人工确认: 产品负责人]` 字段清单、排序筛选、默认视图、空态和批量操作未确认。 |
| 详情抽屉/详情页 | `[候选方案: AI 提炼]` 汇总基础信息、接入信息、凭证引用状态、入库来源、采集状态和任务证据入口。 | `[待人工确认: 技术负责人]` 字段来源、脱敏显示、敏感信息隐藏和差异提示未确认。 |
| 编辑表单 | `[候选方案: AI 提炼]` 可先从低风险字段候选，如名称、标签、metadata、状态等讨论。 | `[待人工确认: 产品负责人]` 允许编辑字段、校验规则、保存语义、审批/审计需求未确认。 |
| 操作区 | `[候选方案: AI 提炼]` 可能包含查看、编辑、store/start、retry、删除或保留等入口。 | `[待人工确认: 安全/权限负责人]` 角色权限、危险操作二次确认和拒绝路径未确认。 |
| task evidence | `[候选方案: AI 提炼]` 汇总 task summary、runs、observations、collection plans、latest DC2 等证据入口。 | `[待人工确认: 测试负责人]` 哪些证据是 launch 必须项、哪些是 post-launch watch 未确认。 |

## 6. 风险与缺口

| 风险/缺口 | 当前记录 | 处理要求 |
| --- | --- | --- |
| 完整 5-device parallel collection 未完成 | 2/5 approved clones 有真实 observations/latest DC2；3/5 因 enrichment/import readiness 未尝试。 | `[待人工确认: 产品负责人]` 补齐、替换或显式接受 reduced-scope 风险。 |
| UI edit/update 未运行 | evidence-index 记录 Edit 为 `NOT RUN`。 | `[待人工确认: 产品负责人]` 决定是否必须补 evidence，或记录 accepted risk。 |
| clone delete cleanup 未运行 | Delete cleanup 和 cleanup report 为 `NOT RUN`；import batch evidence 需要保留。 | `[待人工确认: 技术负责人]` 删除时机、保留策略、禁止删除原始记录边界和审计要求。 |
| 非 admin 权限姿态未确认 | readiness report 将 permissions / non-admin launch role 记录为 P1 `BLOCKED`。 | `[待人工确认: 安全/权限负责人]` 角色、菜单、按钮、API 拒绝路径和 evidence 要求。 |
| store/retry 与采集协议未确认 | 已有 store/start/task evidence 只覆盖局部 approved clones。 | `[待人工确认: 技术负责人]` readiness、controller detect、retry、失败分类和协议边界。 |
| 任务证据成功口径未确认 | observations/latest DC2 只证明局部 evidence 存在。 | `[待人工确认: 测试负责人]` task summary、runs、observations、latest DC2 的正式验收表达。 |

## 7. 删除或保留边界（不可直接执行）

- `[候选方案: AI 提炼]` 只讨论 cloned `D2LA_*` 记录的 exact-code cleanup；原始真实 Device V2 记录不得删除。
- `[候选方案: AI 提炼]` import batch/task/row records 应作为证据保留；不得把 evidence retention 反推为正式保留周期。
- `[待人工确认: 产品负责人]` 是否需要在 launch 前补 clone cleanup/delete evidence，或接受 cleanup 缺失风险。
- `[待人工确认: 技术负责人]` 删除操作的幂等、部分失败、软删/硬删、审计日志、批量操作和回滚语义。
- `[待人工确认: 安全/权限负责人]` 删除按钮、二次确认、危险操作授权和误删保护。

## 8. 不得从 evidence 反推的内容

- 不得把 2 个 approved imported `D2LA_*` clones 的清册和采集证据反推为完整 5 设备上线通过。
- 不得把 management list/handoff evidence 反推为正式清册字段、筛选、排序、分页或详情契约。
- 不得把 field reconciliation evidence 反推为 API/DTO/数据库字段契约。
- 不得把 store/start evidence 反推为正式采集协议、重试策略、并发策略、权限模型或成功标准。
- 不得把 observations/latest DC2 evidence 反推为完整采集质量、SLO、freshness 或监控接入标准。
- 不得把 cleanup intent 反推为正式删除策略、保留周期、审计规则或生产操作手册。

## 9. 待人工确认清单

### 9.1 产品负责人

- `[待人工确认: 产品负责人]` 设备 V2 清册管理的正式业务范围、上线范围和用户角色范围。
- `[待人工确认: 产品负责人]` 清册字段、详情字段、筛选项、批量操作和空态/错误态的产品口径。
- `[待人工确认: 产品负责人]` UI edit/update 是否属于 launch 必须项，以及缺失 evidence 的处理方式。
- `[待人工确认: 产品负责人]` cloned `D2LA_*` 删除、保留或 accepted risk 的最终决策。
- `[待人工确认: 产品负责人]` 5-device parallel collection 是否必须补齐，或是否接受 2/5 reduced evidence 风险。

### 9.2 技术负责人

- `[待人工确认: 技术负责人]` 清册 list、detail、edit、delete、store/start、task evidence 的正式工程边界和责任分层。
- `[待人工确认: 技术负责人]` 哪些 launch evidence 可转入工程约束，哪些只能保留为阶段性证据。
- `[待人工确认: 技术负责人]` credential reference、access point、protocol/port、metadata/labels 的契约表达；本文不确认字段名、存储结构或协议细节。
- `[待人工确认: 技术负责人]` store readiness、controller detect、retry、run classification、latest DC2 freshness 的技术口径。
- `[待人工确认: 技术负责人]` clone cleanup/delete 的幂等、失败补偿、审计和保留策略。

### 9.3 安全/权限负责人

- `[待人工确认: 安全/权限负责人]` 非 admin 角色、菜单可见性、按钮启用、API 权限和拒绝路径。
- `[待人工确认: 安全/权限负责人]` 详情页敏感信息脱敏、credential reference 展示边界和禁止 plaintext secret 的规则。
- `[待人工确认: 安全/权限负责人]` 编辑、删除、store/start、retry 等危险或高影响操作的授权和审计。

### 9.4 测试负责人

- `[待人工确认: 测试负责人]` 清册 list/detail/edit/delete-or-retain/store-start/task-evidence 的正式测试用例和验收口径。
- `[待人工确认: 测试负责人]` full 5-device scope、reduced 2/5 scope、blocked candidates 的测试状态表达。
- `[待人工确认: 测试负责人]` task summary、runs、observations、latest DC2 的必需 evidence、失败分类和 freshness 判断。
- `[待人工确认: 测试负责人]` cleanup report 缺失时设备管理方向能否进入后续阶段，以及需要补哪些 evidence。

## 10. 后续文档化建议

- `[待人工确认: 项目负责人]` 是否允许继续拆分 `management-source-materials.md`、`management-human-gates.md`、`management-evidence-map.md`。
- `[待补充]` 若允许拆分，所有子文档仍必须默认 `blocked-human-confirmation`。
- `[待补充]` 若后续人工确认部分内容，应逐项记录确认人、日期、范围和仍未确认的保留项。

## 11. 代码事实来源清单

> 本节补充 DEV-DOCS-002C 的源码阅读记录，只记录“当前真实代码事实”和“未确认范围”。这些事实仍不得自动提升为产品需求、API 契约、数据库设计或验收标准。

### 11.1 已读取关键文件与事实

| 已读取关键文件 | 事实类型 | 当前真实代码事实 | 未确认范围 |
| --- | --- | --- | --- |
| `docs/development-doc-templates/01-需求概要模板.md`、`02-功能清单模板.md` | 标准文档结构 | 本轮候选文档只能沿用 01-02 及后续 03-07 模板结构；不得生成 08-11。 | `[待人工确认: 项目负责人]` 管理方向是否继续拆分子文档。 |
| `OneOPS/app/device/v2/router/device_v2.go` | route/router | 真实路由组为 `device/v2`；管理相关入口包括 `GET list`、`GET :code`、`POST ""`、`PUT :code`、`DELETE :code`、`GET :code/status`、`GET :code/store-readiness`、`POST store/start`、`POST store/retry`、`GET tasks/:taskId/*`、`GET :code/last-store-collection-dc2`。 | `[待人工确认: 技术负责人]` 哪些 route 属于正式管理页面范围，哪些仅为内部或阶段性 evidence 入口。 |
| `OneOPS/app/device/v2/api/device_v2.go` | handler/controller | `List` 绑定 query、默认 `page=1/page_size=20`，校验 `label_value` 需要 `label_key`、`attribute_value` 需要 `attribute_key`；`Create/Update` 使用 `base_ref_mode` 并调用 service；`Delete` 可先调用 `RelationCleaner.DeleteAllRelations` 再 `DeleteByCode`；store/start 与 retry 通过 `EntityV2Srv` pipeline。 | `[待人工确认: 安全/权限负责人]` 删除、store/start、retry、sync 等写操作权限与审计策略。 |
| `OneOPS/app/device/v2/dto/device_v2.go` | request/response DTO | `DeviceV2ListReq` 支持 `codes/keyword/name/ip/label_key/label_value/attribute_key/attribute_value/manage_status/management_path/location_node_code/location_path_prefix/region_code/site_code/rack_code`；`DeviceV2CreateReq` 需要 `code`；`DeviceV2StoreStartReq` 需要 `codes`。 | `[待人工确认: 产品负责人]` 查询字段和筛选项是否即为正式清册交互。 |
| `OneOPS/app/device/v2/model/device_v2.go` | model/entity | `DeviceV2` 表名函数返回 `platform_devices_v2`；核心字段含 `id/code/type/name/platform_code/status/created_at/updated_at`，`labels/attributes/metadata/group_tags` 通过 JSON 字段序列化，`lifecycle_stage/stage_status/manage_status/manageable` 为非持久化投影或反序列化派生。 | `[待人工确认: 后端负责人]` 字段语义、枚举和数据迁移策略。 |
| `OneOPS/app/device/v2/service/i_device_v2.go` | service interface | 当前接口边界含 `GetSourceByCode/GetByCode/List/ListPage/Create/Update/DeleteByCode`。 | `[待人工确认: 后端负责人]` service 边界是否需要按管理、入库、store 拆分。 |
| `OneOPS/app/device/v2/service/impl/device_v2_minimal_read.go` | DAO/GORM 查询 | 读模型当前主要从 `entity_v2` 的 `EntityInstance` 查询 `entity_type = device_v2`；列表支持 JSON path 过滤；keyword 会匹配 `entity_id/name` 及 attributes/metadata/labels 中若干路径。 | `[待人工确认: 后端负责人]` read model 与 `platform_devices_v2` 的权威关系。 |
| `OneOPS/app/device/v2/service/impl/device_v2_minimal_write.go` | DAO/GORM 更新/删除 | `Create/Update/DeleteByCode` 存在对 `EntityInstance` 和 `DeviceV2` projection/legacy 表的写入或删除路径；删除还清理 change events/fields 等关联记录。 | `[待人工确认: 安全/权限负责人]` 删除策略、软删/硬删、回滚和审计要求。 |
| `OneOPS-UI/src/api/device/device-v2.ts` | frontend request wrapper | 前端 BASE 为 `/device/v2`；存在 list/get/create/update/delete、store start/retry、task summary/runs/observations/collection-plans、last-store-collection-dc2、change history 等 wrapper，并对部分响应做结构断言。 | `[待人工确认: 前端负责人]` wrapper 是否全部暴露在正式页面。 |
| `OneOPS-UI/src/views/device/device-v2-redesign/useDeviceV2RedesignList.ts` | 页面/组件逻辑 | 管理清册 composable 调用 `listDeviceV2Req`，传入 `page/page_size/codes/keyword/manage_status/management_path`，并可按 `code` 调用 `getDeviceV2Req` 加载详情。 | `[待人工确认: 产品负责人]` 当前 redesign 视图是否为正式原型。 |
| `OneOPS-UI/src/views/device/device-v2-redesign/field-model.ts` | 页面字段模型 | 前端字段组包括 identity、catalog、access_points、credential_refs、status_layers、location、system_profile、hardware_profile、source；credential ref 字段标记 `secret: true`，但正式脱敏规则未确认。 | `[待人工确认: 安全/权限负责人]` credential reference 的展示、导出和脱敏策略。 |
| `OneOPS-UI/src/views/device/device-v2-redesign/useDeviceV2RedesignStore.ts` | 页面/采集逻辑 | 前端 store composable 调用 store start、task、summary、runs；start 时传 `options.async=true` 和 `requested_by=ui:device-v2-redesign`，并在获得 task 后加载详情。 | `[待人工确认: 测试负责人]` store task 成功/失败、freshness 和 evidence 必需字段。 |
| `docs/prd-autodev/d2-launch-acceptance/evidence-index.md`、`launch-readiness-report.md` | tests/evidence 摘要 | 2 个 approved `D2LA_*` clones 有管理交接、field reconciliation、store start、observations、latest DC2 evidence；UI edit、clone delete cleanup 和完整 5-device parallel 仍未完成或 blocked。 | `[待人工确认: 产品负责人]` 是否补齐 evidence 或接受 reduced-scope 风险。 |

### 11.2 当前真实代码事实

- 设备管理的当前真实入口覆盖 list/detail/create/update/delete、status、store readiness、store start/retry、task summary/runs/observations/collection plans、latest DC2、change history 和 network overview；但本文不确认这些入口全部属于正式上线范围。
- 清册查询的当前真实过滤参数已在 DTO 和前端 wrapper 中出现；但查询字段、排序、默认视图和空态仍需人工确认。
- `DeviceV2` 既有 `platform_devices_v2` GORM model，也有从 `entity_v2` `EntityInstance` 投影读取的实现；本文不确认最终权威数据源和迁移策略。
- 前端 redesign 字段模型已显式把 credential refs 归为 secret 字段；本文不确认脱敏、权限和导出规则。
- store/start 与 retry 是写入/副作用操作；本文只记录代码事实，不授权自动化或生产执行。

### 11.3 规划缺口与 AI 推导建议

| 类型 | 内容 |
| --- | --- |
| 规划缺口 | `[待人工确认: 产品负责人]` 管理页面正式功能范围、UI edit 是否 launch 必需、clone cleanup 风险处理、5-device evidence 决策。 |
| 规划缺口 | `[待人工确认: 后端负责人]` `entity_v2` read model 与 `platform_devices_v2` GORM model 的长期权威关系、同步边界和迁移策略。 |
| 规划缺口 | `[待人工确认: 安全/权限负责人]` 删除、store/retry、sync、credential refs、非 admin 角色的权限与审计。 |
| AI 推导建议 | `[候选方案: AI 提炼]` 后续如获人工批准，可把管理方向拆为 `management-source-materials.md`、`management-human-gates.md`、`management-evidence-map.md`，仍保持 `blocked-human-confirmation`。 |
