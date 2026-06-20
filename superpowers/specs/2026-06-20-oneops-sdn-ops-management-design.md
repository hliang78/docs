# OneOPS SDN 运维管理设计

## 背景

OneOPS 已经完成 SDN 控制器配置、连接测试、手工同步、快照摘要展示的最小闭环。ACI 测试环境已经通过 `OneOPS UI -> OneOPS 后端 -> CtrlHub -> APIC` 同步成功，说明基础链路可用。

新的产品目标是建设 SDN 运维管理能力：

- 主流品牌 SDN 控制器集群维护。
- SDN 资源管理。
- SDN 配置下发。
- SDN 网络告警。

本设计保持既定边界：OneOPS 不直接适配厂商控制器 API，ACI、华为、H3C 等控制器差异由 CtrlHub 适配。OneOPS 负责运维对象、资源视图、流程编排、权限、审计、告警展示和配置意图。

## 目标

建设一个可分阶段交付的 SDN 运维管理模块。第一阶段先交付只读运维闭环，把已经同步成功的控制器快照转化为可查询、可审计、可对账、可被后续 L2 Service 和网络编排消费的数据资产。

## 非目标

第一阶段不做以下事项：

- 不在 OneOPS 中增加 ACI、华为、H3C 的厂商 API 客户端。
- 不直接向生产 SDN 控制器下发配置。
- 不把厂商 raw payload 作为 OneOPS 业务逻辑依赖。
- 不一次性实现完整告警闭环、自动修复、回滚编排。
- 不改变现有设备采集、IPAM、NetPath、L2 Service 的主流程。

## 职责边界

### OneOPS

OneOPS 负责面向运维人员的管理能力：

- SDN 控制器资产管理：控制器配置、凭证引用、启停、区域、站点、租户标签、同步状态。
- SDN 资源视图：租户、VRF、网络、子网、Segment、Endpoint、交换机、端口、合约、过滤器。
- 快照管理：最新快照、历史快照、资源摘要、同步错误、快照差异。
- 运维流程：资源查询、对账、变更计划、变更审批、执行记录、审计。
- 告警消费：展示 CtrlHub 或监控系统归一化后的 SDN 告警。
- 业务集成：后续给 L2 Service、NetPath、IPAM、拓扑视图提供 SDN 资源上下文。

### CtrlHub

CtrlHub 负责和控制器交互：

- 厂商适配：ACI、华为，后续 H3C。
- 控制器登录、Token、TLS、分页、限速和错误处理。
- 资源采集并映射到 OneOPS 统一 SDN 快照模型。
- 控制器集群健康诊断。
- 告警采集并映射到统一告警模型。
- 配置下发执行和结果回传。

## 分阶段方案

### 阶段 1：只读运维闭环

阶段 1 扩展现有 SDN 控制器页面和后端 API，让同步结果可以真正用于日常运维。

功能范围：

- 控制器列表继续保留连接测试、同步、最近快照入口。
- 最近快照从摘要升级为资源浏览。
- 支持资源类型页签：Tenants、VRFs、Networks、Subnets、Segments、Endpoints、Switches、Ports、Contracts、Filters。
- 每类资源展示统一字段：名称、ID、租户、厂商类型、DN、控制器、采集时间。
- 支持按名称、租户、DN、IP、MAC、交换机、端口等关键字段搜索。
- 增加同步历史列表：成功、失败、耗时、错误摘要、资源总量。
- 增加快照差异：最新快照与上一成功快照比较，展示新增、删除、变化数量和明细。
- 保存 OneOPS 标准资源投影，后续业务模块不用解析整份 snapshot JSON。

验收标准：

- ACI 同步成功后，可以在 OneOPS 中查看 10 类资源明细。
- 资源总数与现有摘要一致。
- 最近两次成功同步后，可以看到资源差异。
- 同步失败时，页面能看到 CtrlHub 返回的清晰错误摘要。
- OneOPS 代码中没有新增 ACI/华为厂商 API 适配逻辑。

### 阶段 2：控制器集群维护

阶段 2 增加控制器健康与集群状态。

功能范围：

- CtrlHub 新增 SDN 诊断接口，分步检测 TCP、TLS、登录、基础查询、集群状态。
- OneOPS 展示控制器健康状态、版本、节点数量、节点角色、节点在线状态。
- 支持健康检查历史，展示最近失败步骤。
- 支持证书校验状态、证书有效期提示。

验收标准：

- ACI 控制器可以展示 APIC 集群节点和健康结果。
- 华为控制器可以通过同一 OneOPS 页面展示健康摘要。
- 诊断失败能定位到 TCP、TLS、认证、查询、权限中的一个阶段。

### 阶段 3：SDN 网络告警

阶段 3 增加 SDN 告警管理。

功能范围：

- CtrlHub 采集 ACI Faults 和华为控制器告警。
- OneOPS 保存统一 SDN 告警模型。
- 告警字段包含控制器、厂商、资源类型、资源 ID、租户、级别、状态、首次发现时间、最近发现时间、恢复时间、原始告警码。
- 告警可以从控制器、资源详情页互相跳转。
- 支持手工刷新和后续定时刷新。

验收标准：

- 可以看到 ACI 当前 fault 列表并关联到资源。
- 告警恢复后状态能更新。
- 告警详情不暴露凭证和敏感 raw 信息。

### 阶段 4：SDN 配置下发

阶段 4 开始支持变更执行，但必须先做计划和审计。

功能范围：

- OneOPS 产生厂商无关的配置意图。
- 第一批意图建议只覆盖低风险对象：网络、子网、VRF 绑定、合约引用。
- CtrlHub 将配置意图翻译为 ACI 或华为 API 调用。
- OneOPS 保存变更计划、Dry-run 结果、审批状态、执行状态、失败原因。
- 支持执行后重新同步快照，自动对账实际结果。

验收标准：

- 所有下发动作必须先生成变更计划。
- 未审批计划不能执行。
- 执行后必须有审计记录和同步对账结果。
- OneOPS 仍不包含厂商 API 调用。

## 第一阶段数据模型

第一阶段在已有 `platform_sdn_controller` 和 `platform_sdn_controller_snapshot` 之外增加标准资源投影表，避免 UI 和业务模块反复解析 snapshot JSON。

### SDN 资源投影

建议模型名：`platform_sdn_resource`

字段：

- `id`：OneOPS 内部 ID。
- `tenant_code`：OneOPS 租户隔离字段。
- `controller_id`：SDN 控制器 ID。
- `snapshot_id`：来源快照 ID。
- `provider`：`aci`、`huawei`。
- `resource_type`：`tenant`、`vrf`、`network`、`subnet`、`segment`、`endpoint`、`switch`、`port`、`contract`、`filter`。
- `resource_id`：厂商归一化 ID。
- `name`：资源名称。
- `tenant_name`：SDN 租户名称。
- `vrf_name`：VRF 名称。
- `network_name`：网络或 BD 名称。
- `dn`：厂商 DN 或路径。
- `ip`：Endpoint 或 subnet 相关 IP。
- `mac`：Endpoint MAC。
- `switch_name`：交换机名称。
- `port_name`：端口名称。
- `provider_type`：厂商对象类型。
- `attributes_json`：归一化扩展属性 JSON。
- `collected_at`：采集时间。
- `created_at`、`updated_at`。

索引：

- `tenant_code, controller_id, resource_type`
- `tenant_code, controller_id, snapshot_id`
- `tenant_code, resource_type, name`
- `tenant_code, ip`
- `tenant_code, mac`
- `tenant_code, dn`

### SDN 快照差异

建议模型名：`platform_sdn_snapshot_diff`

字段：

- `id`
- `tenant_code`
- `controller_id`
- `from_snapshot_id`
- `to_snapshot_id`
- `resource_type`
- `change_type`：`added`、`removed`、`changed`
- `resource_key`：稳定比较键，优先使用 DN，其次使用资源类型加资源 ID。
- `before_json`
- `after_json`
- `summary_json`
- `created_at`

## 第一阶段 API

复用已有控制器 API，并增加资源与差异查询接口。

### 资源查询

`GET /api/v1/sdn/controllers/{id}/resources`

查询参数：

- `resource_type`
- `keyword`
- `tenant_name`
- `vrf_name`
- `network_name`
- `page`
- `page_size`

返回：

- 分页资源列表。
- 当前控制器、快照 ID、采集时间。
- 当前过滤条件下的资源数量。

### 资源详情

`GET /api/v1/sdn/controllers/{id}/resources/{resource_id}`

返回：

- 标准字段。
- 扩展属性。
- 来源快照。
- 关联资源线索，例如 endpoint 关联 network、port、switch。

### 快照历史

已有 `GET /api/v1/sdn/controllers/{id}/snapshots` 继续保留，补充差异摘要字段：

- `added_count`
- `removed_count`
- `changed_count`

### 快照差异

`GET /api/v1/sdn/controllers/{id}/snapshots/{snapshot_id}/diffs`

查询参数：

- `resource_type`
- `change_type`
- `keyword`
- `page`
- `page_size`

返回：

- 分页差异列表。
- 按资源类型聚合的差异摘要。

## 第一阶段 UI

页面位置继续属于设备管理：`OneOPS-UI/src/views/device/SdnControllerManagement.vue`。

页面结构：

- 控制器列表：保留当前列表、筛选、测试连接、同步、最近快照。
- 最近操作结果：保留同步成功/失败摘要。
- 资源浏览抽屉或详情页：
  - 顶部展示控制器、Provider、快照 ID、采集时间、总资源数。
  - 使用页签切换资源类型。
  - 每个页签都有搜索框和分页表格。
  - Endpoint 页签重点展示 IP、MAC、Tenant、Network、Switch、Port。
  - Network/Subnet 页签重点展示 Tenant、VRF、CIDR、DN。
  - Contract/Filter 页签重点展示 Tenant、名称、厂商类型、DN。
- 快照历史抽屉：
  - 展示同步时间、状态、耗时、资源总量、错误摘要。
  - 成功快照提供“查看差异”入口。
- 差异视图：
  - 按 added、removed、changed 过滤。
  - 按资源类型过滤。
  - changed 展示 before/after 的关键字段差异。

## 第一阶段实现路径

1. 后端先增加资源投影和差异计算的单元测试。
2. 后端在同步成功后，把 normalized snapshot 展开写入资源投影表。
3. 后端在有上一成功快照时计算并保存 diff。
4. 后端增加资源查询、资源详情、差异查询 API。
5. 前端扩展最近快照入口，展示资源页签和历史差异。
6. 用 ACI 已同步成功的数据做人工验收。
7. 保持 CtrlHub 接口不变，除非发现现有 normalized snapshot 字段不足。

## 错误处理

- OneOPS 同步失败时保留当前行为：记录失败快照摘要和控制器 `last_error`。
- 资源投影失败时，同步应标记为失败，错误摘要说明“快照采集成功但资源投影失败”。
- 差异计算失败时，同步可以成功，但记录差异状态为失败，页面提示无法生成差异。
- 所有错误不包含密码、Token、Cookie。

## 权限与审计

第一阶段最少需要以下权限语义：

- 查看 SDN 控制器。
- 管理 SDN 控制器。
- 执行连接测试。
- 执行资源同步。
- 查看 SDN 资源。
- 查看 SDN 快照历史。

如果当前权限系统不便新增细粒度权限，第一阶段可以复用设备管理权限，但 API 层必须保留后续拆分点。

审计建议：

- 控制器新增、编辑、删除。
- 连接测试。
- 手工同步。
- 查看 raw snapshot 的行为。第一阶段默认不开放 raw snapshot。

## 与后续模块的关系

### L2 Service

第一阶段只提供只读关联基础：

- L2 Service 后续可选择 SDN 控制器、租户、VRF、网络。
- 创建或变更 L2 Service 前，可先查询 SDN 资源是否存在。
- 不在第一阶段自动创建或修改 SDN 网络。

### NetPath

SDN endpoint、switch、port、network 可作为 NetPath 的补充事实来源。第一阶段只保证资源投影可查询，不直接改 NetPath 推理。

### IPAM

SDN subnet 可用于 IPAM 对账。第一阶段只保存 subnet 资源，后续再实现 IPAM 与 SDN subnet 的一致性检查。

## 验证计划

后端：

- 单元测试资源投影展开。
- 单元测试资源查询过滤。
- 单元测试 snapshot diff：新增、删除、变化、无变化。
- 单元测试同步成功后写入资源投影。
- 单元测试同步失败不污染上一成功资源。

前端：

- 资源抽屉空态。
- ACI 成功同步后资源页签展示。
- Endpoint 搜索。
- 快照历史展示。
- 差异视图展示。

集成：

- 使用当前 ACI 测试控制器同步一次。
- 再同步一次，确认无变化时 diff 为空。
- 人工在 APIC 上制造一个低风险新增对象或使用测试数据注入，确认 diff 显示 added。

## 通过标准

第一阶段完成后，运维人员可以在 OneOPS 中完成以下动作：

- 查看 SDN 控制器同步是否正常。
- 查看 ACI 控制器中的主要 SDN 资源明细。
- 按租户、网络、Endpoint 关键词定位资源。
- 查看同步历史和失败原因。
- 判断两次同步之间有哪些资源变化。

这时 OneOPS 具备“SDN 资源管理”的只读基础，可以继续推进控制器集群维护、告警和配置下发。
