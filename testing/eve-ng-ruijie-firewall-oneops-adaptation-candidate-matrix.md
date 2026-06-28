# EVE-NG Ruijie 防火墙 OneOPS 适配候选矩阵

## 1. 目的

这份文档把当前 `Ruijiefirewall-V1.03` 已发现的本机 Web API，按 OneOPS 的能力链重新整理成可推进的适配清单。

它解决的不是“这台设备有没有接口”这个问题，而是：

1. 哪些接口更适合先做只读采集。
2. 哪些接口适合支撑监控、策略、拓扑、诊断。
3. 哪些接口虽然存在，但当前不应优先纳入交付。
4. 如何把 Web API 适配与 `SSH/CLI` 主通道配合起来，而不是互相替代。

## 2. 共享前提

基于当前实证，下面几点默认成立：

1. 锐捷防火墙当前管理模型固定为 `Ge0/0 + main`。
2. 不纳入 OneOPS 当前阶段的 `VRF` 支持范围。
3. 本机存在大量 `/api/v1/...` 接口。
4. 这些接口更像“Web 管理后台内部接口”，不是已确认的官方公开 OpenAPI。
5. 登录模型为 `captcha + public_key + /api/v1/login/ + sessionid`。
6. 因此，Web API 当前只适合作为增强适配路径，不应取代 `SSH/CLI` 主通道。

## 3. OneOPS 能力链映射

### 3.1 认证与会话引导

这组接口决定 OneOPS 是否能稳定拿到后续 Web API 的只读访问能力。

| 能力链 | 候选接口 | 用途 | 当前建议 |
| --- | --- | --- | --- |
| 登录前置 | `/api/v1/captcha/` | 获取验证码 | 仅在必须走 Web 会话时使用 |
| 登录前置 | `/api/v1/public_key/` | 获取登录加密公钥 | 需要专项适配 |
| 登录 | `/api/v1/login/` | 建立 session | 作为实验性增强能力 |
| 登出 | `/api/v1/logout/` | 释放 session | 建议配套实现 |

判断：

1. 这组接口是所有 Web API 适配的门槛。
2. 但它的稳定性与复杂度都高于 `SSH/CLI`。
3. 因此不建议把它作为第一条正式交付主通道。

## 4. 按测试目标拆分的候选接口组

### 4.1 配置采集与资产建模

这是最适合优先做的方向，因为它天然偏只读。

#### 4.1.1 接口与链路资产

候选模块：`interface`

代表接口：

1. `/api/v1/interface/get_all_interface/`
2. `/api/v1/interface/get_physical_interface/`
3. `/api/v1/interface/get_sub_interface/`
4. `/api/v1/interface/get_bridge_fdb/`
5. `/api/v1/interface/get_deploy_mode/`
6. `/api/v1/interface/port_panel/`
7. `/api/v1/interface/get_mesh_info/`

适配价值：

1. 构建设备接口清单。
2. 获取物理口、子接口、桥接口、聚合口信息。
3. 为拓扑生成和链路校验提供结构化输入。

当前优先级：`P0`

原因：

1. 与 OneOPS 的“设备采集、拓扑生成”高度贴合。
2. 大量接口具备明显的只读命名特征。
3. 副作用风险相对可控。
4. 截至 `2026-06-28`，这组接口里已经实测打通：
   - `get_all_interface`
   - `get_physical_interface`
   - `get_sub_interface`
   - `port_panel`
   - `get_bridge_fdb`
5. 当前仍不应把 `get_deploy_mode` 当作这组能力的阻塞点。

#### 4.1.2 路由与网络配置

候选模块：`network_router`

代表接口：

1. `/api/v1/route/static/`
2. `/api/v1/route/table/`
3. `/api/v1/routePolicy/list/`
4. `/api/v1/routePolicy/info/`
5. `/api/v1/routePolicy/app/`

适配价值：

1. 提取静态路由、策略路由、路由表。
2. 为拓扑推理和路径分析补充三层事实。
3. 为“策略查询是否命中正确路径”提供网络侧依据。

当前优先级：`P0`

#### 4.1.3 地址、区域、应用、服务对象

候选模块：

1. `addresses`
2. `areas`
3. `application`
4. `service`
5. `url_classification`
6. `url_filter`

代表接口：

1. `/api/v1/ip/address/`
2. `/api/v1/ip/group/`
3. `/api/v1/areas/`
4. `/api/v1/application/`
5. `/api/v1/service/getData/`
6. `/api/v1/object/url_classification/get_url_classification_list/`
7. `/api/v1/object/url_filter/get_url_filter_list/`

适配价值：

1. 为策略解析建立对象层事实。
2. 为配置查询、策略命中解释、对象依赖分析打底。

当前优先级：`P0`

### 4.2 策略解析与策略查询

这是 Ruijie 防火墙对 OneOPS 最有业务价值的一组能力。

候选模块：

1. `policy`
2. `nat`
3. `security_rules`
4. `ssl_proxy`
5. `safety_protection`

代表接口：

1. `/api/v1/policy/get_policy/`
2. `/api/v1/policy/get_policy_group/`
3. `/api/v1/policy/get_permit_all/`
4. `/api/v1/policy/get_policy_cycle/`
5. `/api/v1/policy/get_optimize_list/`
6. `/api/v1/nat/get_convert/`
7. `/api/v1/nat/get_pool/`
8. `/api/v1/security_rule/get/`
9. `/api/v1/ssl/ssl_policy/get_ssl_policy/`
10. `/api/v1/dos/policy/`

适配价值：

1. 安全策略采集与结构化解析。
2. NAT 规则与地址池解析。
3. 策略命中解释、策略查询、策略优化建议。
4. 为后续“策略生成”建立现状事实层。

当前优先级：`P0`

当前建议：

1. 先做只读获取与字段梳理。
2. 再与 CLI 导出配置做逐项对照。
3. 只有字段语义稳定后，才推进策略查询与命中推理。

### 4.3 监控与运行态数据

这是第二阶段最适合补强的方向，尤其贴近你的“监控推送”和“大量监控目标”目标。

候选模块：

1. `device_monitoring`
2. `flow_monitor`
3. `safe_cockpit`
4. `log_monitoring`
5. `reputation_center`

代表接口：

1. `/api/v1/device/hour/list`
2. `/api/v1/device/day/list`
3. `/api/v1/device/week/list`
4. `/api/v1/flow_monitor/interface_status/`
5. `/api/v1/flow_monitor/interface_history/`
6. `/api/v1/flow_monitor/session_monitor/getSessionStatistics/`
7. `/api/v1/flow_monitor/session_monitor/getSessionInfo/`
8. `/api/v1/top/attacktype/`
9. `/api/v1/log/get_securitylog`
10. `/api/v1/log/get_session_log/`

适配价值：

1. 补足设备运行态、接口流量、会话趋势、日志事件。
2. 为监控任务、告警推送、趋势分析提供结构化数据源。
3. 可以与 OneOPS 现有监控主通道形成交叉校验。

当前优先级：`P1`

原因：

1. 业务价值高。
2. 但很多结果来自设备内部数据库或统计任务，语义和刷新周期需要额外校验。

### 4.4 故障诊断与抓包辅助

这组能力很适合做实验室验证和客户现场辅助，但不建议直接作为第一阶段主交付能力。

候选模块：`fault_diagnosis`

代表接口：

1. `/api/v1/fault_diagnosis/pinguid/`
2. `/api/v1/fault_diagnosis/tracertuid/`
3. `/api/v1/fault_diagnosis/baggrabbinglist/`
4. `/api/v1/fault_diagnosis/baggrabbinguid/`
5. `/api/v1/fault_diagnosis/diagnostic_center/getTask/`
6. `/api/v1/fault_diagnosis/diagnostic_center/getTaskResult/`

适配价值：

1. 为实验室自动化验证补充设备侧自检证据。
2. 为策略命中、连通性、抓包结果建立设备内观察点。

当前优先级：`P1`

### 4.5 变更与自动化下发

这组接口大量涉及写操作，不适合第一阶段直接纳入正式交付。

高风险模块：

1. `interface` 中的 `edit_`、`switch_`、`bridge/config/`
2. `network_router` 中的编辑与删除接口
3. `policy` 中的 `add_`、`del_`、`move_`
4. `nat` 中的 `edit_`、`del_`
5. `system_maintenance` 中的 `import/`、`reboot/`、`restore/`、`upgradeBackend/`

当前优先级：`P2`

当前建议：

1. 第一阶段只记录这些接口存在。
2. 第二阶段先做最小副作用实验。
3. 写接口必须绑定回滚验证与快照留证。

## 5. 按 OneOPS 场景的落地建议

### 5.1 设备采集

优先接入：

1. `interface`
2. `network_router`
3. `addresses`
4. `areas`
5. `application`
6. `service`
7. `policy`
8. `nat`

目标：

1. 形成一份比纯 CLI 更结构化的设备事实模型。
2. 与 CLI 原始配置做双源对照。

### 5.2 监控推送

优先接入：

1. `device_monitoring`
2. `flow_monitor`
3. `log_monitoring`

目标：

1. 验证设备内统计值是否能稳定抽取。
2. 确认周期、粒度、字段是否满足 OneOPS 监控模型。

### 5.3 防火墙配置解析与策略查询

优先接入：

1. `policy`
2. `nat`
3. `addresses`
4. `areas`
5. `application`
6. `service`
7. `security_rules`

目标：

1. 用接口直接拿结构化配置。
2. 与 CLI 文本解析结果交叉验证。
3. 降低仅靠文本解析带来的歧义。

### 5.4 拓扑生成

优先接入：

1. `interface`
2. `network_router`
3. `link_detection`
4. `isp_library`
5. `device_monitoring`

目标：

1. 构建设备内接口视图。
2. 结合 EVE 实验链路和 OneOPS 邻接推理，验证拓扑事实。

### 5.5 自动化脚本

当前策略：

1. 第一阶段以只读脚本为主。
2. 第二阶段再挑选低风险写接口。
3. 所有写接口都必须先在 EVE 中完成副作用边界验证。

## 6. 建议的推进顺序

### 6.1 第一批

1. 登录会话打通
2. `interface` 只读采集
   - 先固定：
     - `get_all_interface`
     - `get_physical_interface`
     - `get_sub_interface`
     - `port_panel`
     - `get_bridge_fdb`
   - 暂不依赖：
     - `get_deploy_mode`
3. `network_router` 只读采集
4. `addresses/areas/application/service` 只读采集
5. `policy/nat` 只读采集

目标：

建立“结构化配置采集”最小闭环。

### 6.2 第二批

1. `device_monitoring`
2. `flow_monitor`
3. `log_monitoring`
4. `fault_diagnosis`

目标：

建立“运行态与监控”闭环。

### 6.3 第三批

1. `quickly_start/openapi/*`
2. 低风险写接口
3. 受控变更与回滚实验

目标：

评估自动化下发与增强控制能力。

## 7. 需要特别提醒的边界

1. 这些接口当前仍属于“内部 Web API”。
2. 路径命名可读，不代表字段语义稳定。
3. 很多接口虽然名字像只读，但实际是否有副作用仍要 live 验证。
4. 验证码、公钥、session 机制意味着它不是天然适合批量无头接入的设备 API。
5. 因此当前不建议把 Web API 适配当作 Ruijie 防火墙的唯一能力线。

## 8. 当前共享口径

针对 OneOPS 的下一步推进，建议统一使用下面这句话：

`Ruijie 防火墙当前最有价值的增强适配方向，是把本机内部 Web API 用于结构化只读采集、监控补数、策略与拓扑事实校验，而不是直接把它当成稳定公开 API 来承担所有自动化控制。`
