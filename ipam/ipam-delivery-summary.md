# IPAM 地址管理能力交付说明

## 1. 交付目标

本轮交付围绕企业全网 IP 地址管理能力展开，覆盖地址规划、地址统计、自动采集与稽核、地址申请与回收流程等核心功能。

本期重点是地址管理能力本身，不包含现网拓扑图、端到端拓扑图等拓扑可视化能力。拓扑相关能力建议在后续拓扑功能扩展阶段单独设计和实现。

## 2. 本期已覆盖能力

### 2.1 地址规划

已实现地址池和保留地址段能力，用于承载企业地址空间规划。

地址池能力包括：

- 创建地址池
- 查询地址池详情
- 分页查询地址池
- 更新地址池
- 删除地址池
- 按租户、区域、安全区域、平台 VRF、网段、IP 版本等维度参与统计过滤

保留地址段能力包括：

- 创建保留地址段
- 查询保留地址段详情
- 分页查询保留地址段
- 更新保留地址段
- 删除保留地址段
- 分配时识别保留地址段，并按申请单的特殊分配标记控制是否允许穿透

### 2.2 IP 地址流程管理

已实现 IP 申请、审批分配、释放、回收的 MVP 流程。

流程能力包括：

- 创建 IP 地址申请单
- 支持分配申请和保留申请
- 审批后自动分配地址
- 支持首选 IP
- 支持批量数量上限保护
- 支持释放地址
- 支持回收地址
- 回收时保护仍有现网发现记录的地址，除非显式 force

关键约束：

- 自动分配本期只支持 IPv4 地址池
- IPv6 地址池会返回明确的不支持错误，不进行大范围遍历
- 地址生命周期使用 `LifecycleStatus` 表达，不复用在线状态字段
- 现有平台 VRF 概念保持不变，地址分配时从地址池的平台 VRF 映射到地址记录

### 2.3 自动采集事实

已实现现网地址事实的上报和查询能力，用于承接自动采集结果。

采集事实能力包括：

- 单条事实 upsert
- 批量事实 upsert
- 分页查询事实
- 支持采集来源、设备、接口、MAC、平台 VRF、安全区域、首次发现、最近发现等字段
- 批量写入有上限保护
- 必要上下文通过确定性编码保存在事实记录中，不允许静默丢失

### 2.4 地址稽核发现

已实现基于采集事实生成稽核发现的 MVP 能力。

稽核发现类型包括：

- 未规划地址
- 规划地址疑似过期
- 归属不一致
- MAC 不一致
- 重复观测
- 规划匹配歧义

稽核处理能力包括：

- 根据事实生成稽核发现
- 避免重复创建未关闭的同类发现
- 分页查询稽核发现
- 关闭/解决稽核发现

重要口径：

- 当同一个地址在多个地址空间中可能匹配多条规划记录时，不会任意取第一条规划地址
- 规划匹配歧义会单独生成发现
- 即使规划匹配歧义，仍会继续生成与规划无关的事实类发现，例如重复观测
- 空观测状态不会被当作活跃状态，避免产生噪声
- 空 MAC 不会触发 MAC 冲突

### 2.5 地址统计

已实现 IPAM 统计服务，用于支持地址管理总览和后续页面展示。

统计能力包括：

- 总览统计
- 地址池统计
- 生命周期统计
- 稽核统计

统计口径包括：

- 地址池总数
- 已规划地址数
- 已分配、已保留、可用、释放中、已回收、冲突、未知等生命周期数量
- 现网事实数量
- 未解决稽核发现数量
- 申请单状态数量
- 地址池利用率
- 稽核发现类型、严重级别、处理状态分布

质量修复：

- 事实统计在带租户、网段、地址池、平台 VRF 等过滤时，不只按 IP 字符串匹配，而是结合地址上下文进行匹配，避免重叠地址场景串数。

### 2.6 前端 API 契约

已补齐前端 API wrapper 和 TypeScript 类型契约，为后续页面开发提供调用基础。

覆盖模块包括：

- 地址池
- 保留地址段
- 地址申请流程
- 现网采集事实
- 稽核发现
- IPAM 统计

本期仅补 API/types，不包含完整页面、菜单、路由和交互实现。

## 3. 后端接口清单

### 3.1 地址池

- `POST /ipam/address-pools`
- `POST /ipam/address-pools/list`
- `GET /ipam/address-pools/:code`
- `PUT /ipam/address-pools`
- `DELETE /ipam/address-pools/:code`

### 3.2 保留地址段

- `POST /ipam/reserved-ranges`
- `POST /ipam/reserved-ranges/list`
- `GET /ipam/reserved-ranges/:code`
- `PUT /ipam/reserved-ranges`
- `DELETE /ipam/reserved-ranges/:code`

### 3.3 地址申请流程

- `POST /ipam/address-requests`
- `POST /ipam/address-requests/list`
- `POST /ipam/address-requests/:code/approve-allocate`
- `POST /ipam/address-requests/release/:ip_code`
- `POST /ipam/address-requests/reclaim/:ip_code?force=true`

### 3.4 现网事实

- `POST /ipam/address-facts/upsert`
- `POST /ipam/address-facts/batch-upsert`
- `POST /ipam/address-facts/list`

### 3.5 稽核发现

- `POST /ipam/audit-findings/generate-from-fact/:fact_code`
- `POST /ipam/audit-findings/list`
- `POST /ipam/audit-findings/:code/resolve`

### 3.6 统计

- `POST /ipam/statistics/overview`
- `POST /ipam/statistics/pools`
- `POST /ipam/statistics/lifecycle`
- `POST /ipam/statistics/audit`

## 4. 建议操作体验

### 4.1 地址规划流程

1. 维护基础网段和平台 VRF 等基础上下文。
2. 创建地址池，定义租户、区域、安全区域、平台 VRF、起止地址、用途和容量阈值。
3. 创建保留地址段，标记网关、广播、基础设施、特殊用途等不可普通分配的地址范围。
4. 通过地址池统计查看规划覆盖和利用情况。

### 4.2 地址申请流程

1. 用户提交地址申请，填写地址池、数量、用途、归属对象、首选 IP 等信息。
2. 平台校验地址池、数量、保留段、已用地址、重复地址等约束。
3. 审批通过后自动分配或保留地址。
4. 地址进入对应生命周期，例如已分配或已保留。
5. 后续可进入释放或回收流程。

### 4.3 自动采集与稽核流程

1. 采集任务或外部系统上报地址事实。
2. 平台按自然键进行事实 upsert。
3. 用户或系统触发基于事实的稽核发现生成。
4. 平台生成未规划、重复观测、归属不一致、MAC 不一致、规划疑似过期等发现。
5. 运维人员处理发现，并标记解决。

### 4.4 统计查看流程

1. 用户进入 IPAM 总览查看地址池数量、规划地址数量、生命周期分布、事实数量和未解决稽核数量。
2. 用户按租户、区域、安全区域、平台 VRF、网段、地址池、IP 版本等过滤。
3. 用户进入地址池统计查看具体地址池利用率。
4. 用户进入稽核统计查看发现类型、严重级别和处理状态分布。

## 5. 验证结果

后端验证：

- `go test ./app/ipam/... ./initialize ./boot/provider -run '^$' -count=1` 通过
- `go test ./app/ipam/service/impl -run 'Test(IPAMStatistics|IPAddressFact|IPAddressAuditFinding|IPAddressRequest|ReservedRange|AddressPool|IPAMAddressMath)' -count=1` 通过
- `go test ./app/ipam/service/impl -run 'TestIPAMStatistics|TestMatchesIPAMStatisticsFactScopeUsesVRFAndFactMeta' -count=1` 通过

前端验证：

- `npm run typecheck` 通过

## 6. 本期不包含范围

以下能力明确后置：

- IP 现网拓扑图
- IP 端到端拓扑图
- 拓扑路径推导
- 设备本地 VRF 的完整建模和纳管
- IPv6 自动地址分配
- 完整前端页面、菜单、路由和交互
- 自动化周期采集任务编排
- 大规模统计的数据库级聚合优化

## 7. 后续建议

建议下一阶段按以下顺序推进：

1. 前端页面开发：IPAM 总览、地址池规划、地址申请、采集事实、稽核发现。
2. 端到端联调：用模拟地址池、模拟事实、模拟申请单跑通完整操作链路。
3. 补充数据库迁移/部署说明：确保新增模型字段和 DAO 在部署环境一致。
4. 完善采集接入：明确事实来源、采集周期、数据去重策略。
5. 拓扑阶段单独启动：在已有地址事实和设备接口数据基础上扩展现网拓扑和端到端拓扑能力。
