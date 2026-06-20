# IPAM 总览页设计规格

## 1. 背景

本轮 IPAM 后端已经完成地址规划、地址申请与回收、现网事实采集、稽核发现、统计接口以及前端 API 契约。下一步需要建设第一版前端入口页面，让用户可以从一个总览视角理解地址管理状态。

本页面定位为“地址管理驾驶舱”，重点展示地址规划、地址使用、流程状态、采集事实和稽核风险。

本期不包含现网拓扑图、端到端拓扑图、拓扑路径推导，也不引入设备本地 VRF 页面概念。

## 2. 目标

IPAM 总览页需要回答以下问题：

- 当前规划了多少地址池和地址资源。
- 地址处于哪些生命周期状态。
- 地址申请流程是否有积压。
- 现网采集事实是否已经进入系统。
- 稽核发现是否存在未处理风险。
- 哪些地址池利用率较高，需要重点关注。

## 3. 页面范围

### 3.1 本期包含

- 筛选区
- KPI 卡片区
- 生命周期分布
- 申请状态分布
- 稽核发现分布
- 地址池利用率列表
- 加载态、空态、错误提示

### 3.2 本期不包含

- 拓扑图
- 端到端路径图
- 地址池详情页
- 地址申请表单页
- 采集事实详情页
- 稽核发现处理弹窗
- 菜单权限配置的深度调整
- 设备本地 VRF 独立筛选或独立页面概念

## 4. 信息架构

页面采用“管理驾驶舱”结构。

### 4.1 顶部筛选区

筛选字段：

- 租户：`tenant_code`
- 区域：`region_code`
- 安全区域：`zone_code`
- 平台 VRF：`platform_vrf_code`
- 网段：`prefix_code`
- 地址池：`pool_code`
- IP 版本：`ip_version`
- 时间范围：`start_at` / `end_at`

筛选行为：

- 页面首次进入自动加载默认统计。
- 用户点击查询后刷新全部统计区块。
- 用户点击重置后清空筛选并重新加载。
- 时间范围主要用于申请、事实、稽核相关统计；规划类统计仍按当前数据口径展示。

### 4.2 KPI 卡片区

第一屏展示 6 个核心指标：

- 地址池总数：`total_pool_count`
- 已规划地址数：`planned_address_count`
- 地址利用率：`utilization_ratio`
- 未解决稽核发现：`unresolved_audit_finding_count`
- 现网事实数：`observed_fact_count`
- 待处理申请数：使用申请状态分布中 submitted/approved 等状态组合展示，第一版可先显示 submitted 数量

视觉要求：

- 利用率使用百分比和进度条展示。
- 未解决稽核发现使用风险色强调。
- 其他指标保持中性信息层级。

### 4.3 生命周期分布

展示地址生命周期数量：

- available
- reserved
- assigned
- releasing
- reclaimed
- conflict
- unknown

第一版可以使用横向条形进度或 Ant Design Vue 的统计卡片组合，不强制引入复杂图表。

### 4.4 申请状态分布

展示申请单状态数量：

- submitted
- approved
- rejected
- completed
- 其他状态按接口返回补充展示

第一版可展示为小型列表或标签统计。

### 4.5 稽核发现分布

展示三类统计：

- 按发现类型：`finding_type_counts`
- 按严重级别：`severity_counts`
- 按处理状态：`status_counts`

第一版重点显示：

- 未解决数量
- critical/warning/info 分布
- unplanned、duplicate_observation、owner_mismatch、mac_mismatch、stale_planned、ambiguous_planned_match 等类型分布

### 4.6 地址池利用率列表

表格字段建议：

- 地址池编码
- 地址池名称
- 网段编码
- 租户
- 区域
- 安全区域
- 平台 VRF
- IP 版本
- 已规划数量
- 已分配数量
- 已保留数量
- 可用数量
- 利用率

排序建议：

- 第一版前端按利用率降序展示。
- 如果后端后续提供排序参数，再改为后端排序。

风险展示：

- 利用率大于等于 80% 标记为 warning。
- 利用率大于等于 95% 标记为 critical。
- 阈值先在前端常量中定义，后续可与地址池容量阈值联动。

## 5. 数据接口

页面使用已存在的前端 API 契约：

- `ipamStatisticsOverviewReq`
- `ipamStatisticsPoolsReq`
- `ipamStatisticsLifecycleReq`
- `ipamStatisticsAuditReq`

对应后端接口：

- `POST /ipam/statistics/overview`
- `POST /ipam/statistics/pools`
- `POST /ipam/statistics/lifecycle`
- `POST /ipam/statistics/audit`

## 6. 数据流

1. 页面初始化筛选状态。
2. 调用四个统计接口。
3. 将总览指标渲染为 KPI 卡片。
4. 将生命周期、申请、稽核统计渲染为分布区块。
5. 将地址池统计渲染为表格。
6. 用户查询或重置时重新调用接口。

接口调用策略：

- 四个接口可以并行请求。
- 任一接口失败时，页面展示错误提示，但不阻塞其他已成功区块展示。
- 首版可使用统一 loading 状态，后续再拆成区块级 loading。

## 7. 错误和空态

错误处理：

- 接口失败时使用 Ant Design Vue message 展示错误。
- 统计卡片失败时显示 `--`。
- 表格失败时保留空列表。

空态处理：

- KPI 数字默认为 0。
- 分布列表为空时显示“暂无数据”。
- 地址池列表为空时显示表格空态。

## 8. 文件设计

建议新增页面文件：

- `src/views/ipam/IPAMOverview.vue`

页面内部可以先保持单文件实现，避免过早拆分。若后续页面复杂度增加，再拆分为：

- `components/OverviewMetricCard.vue`
- `components/StatisticsDistribution.vue`
- `components/PoolUtilizationTable.vue`

本期不强制拆分组件。

## 9. 路由和菜单

本期建议先创建页面文件。

是否接入菜单/路由取决于现有系统菜单配置方式：

- 如果当前菜单由后端或静态资源控制，本期不强行修改。
- 如果已有清晰前端路由入口，可补充到 IPAM 模块下。

为了降低范围风险，第一版实现可以先不改菜单，只确保页面文件和依赖编译通过。

## 10. 视觉方向

视觉方向采用现有后台系统风格，不做大规模视觉重构。

优化重点：

- 指标层级清晰。
- 风险指标突出。
- 筛选区不要占据过高首屏空间。
- 地址池列表适合快速定位高利用率资源。

## 11. 验收标准

功能验收：

- 页面可以加载总览统计。
- 页面可以展示生命周期分布。
- 页面可以展示申请状态分布。
- 页面可以展示稽核统计。
- 页面可以展示地址池统计列表。
- 筛选条件能传递到统计接口。
- 重置能恢复默认筛选。

技术验收：

- 前端 typecheck 通过。
- 不引入拓扑功能。
- 不新增设备本地 VRF 页面概念。
- 不破坏现有 IPAM 页面。
- 不修改无关 AIOps、Alert、Netpath 文件。

## 12. 后续扩展

后续可以继续扩展：

- 地址池详情页。
- 地址申请流程页面。
- 采集事实列表页面。
- 稽核发现处理页面。
- 统计图表增强。
- 与后续拓扑能力联动。
