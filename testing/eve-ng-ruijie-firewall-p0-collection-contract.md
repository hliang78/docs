# EVE-NG Ruijie 防火墙 P0 结构化采集合同

## 1. 目标

这份文档把当前 `Ruijiefirewall-V1.03` 最值得优先接入的 `P0` 只读接口，整理成 OneOPS 可直接消费的结构化采集合同。

范围只覆盖两条主线：

1. `interface`
2. `network_router`

目标不是一次性打完所有字段，而是先建立：

1. 可重复调用的登录与查询顺序
2. 稳定的字段抽取口径
3. 与 OneOPS 采集模型的第一轮映射
4. 每条接口的 live 验证重点

## 2. 共享前提

1. 当前接口都运行在设备本机 Web 后端上。
2. 设备登录是 `captcha + public_key + /api/v1/login/ + sessionid` 模型。
3. 这组接口当前属于内部 Web API，不应视为正式公开 OpenAPI。
4. OneOPS 第一阶段仍以 `SSH/CLI` 为主通道。
5. 这份合同的定位是：
   - `结构化补强`
   - `事实校验`
   - `为后续策略、拓扑、监控做底座`

对应 live 实测回执：

[EVE-NG Ruijie 防火墙 P0 接口实测回执](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-ruijie-firewall-p0-live-validation.md)

截至 `2026-06-28`，当前这份合同里的 live 状态应统一按下面口径理解：

1. 已打通：
   - `public_key`
   - `captcha`
   - `login`
   - `get_all_interface`
   - `get_physical_interface`
   - `search_iface`
   - `port_panel`
   - `get_bridge_fdb`
   - `route/static`
   - `route/table`
   - `routePolicy/list`
2. 返回空但链路正常：
   - `get_sub_interface`
3. 当前不应直接纳入稳定采集：
   - `get_deploy_mode`
4. 当前不应假设可用：
   - `20099` 免验证码登录分支

## 3. 统一调用口径

### 3.1 URL 前缀

后端真实路由在 Django 中挂载为：

`/api/v1/...`

前端 bundle 里经常只出现：

`/v1/...`

这说明前端大概率在请求层额外挂了 `/api` 前缀。

因此 OneOPS 侧建议统一按下面方式理解：

1. 文档主口径：`/api/v1/...`
2. 如果抓浏览器请求时只看到 `/v1/...`，应按“前端 baseURL 已拼接 `/api`”处理

### 3.2 认证口径

当前建议先固定为：

1. `/api/v1/public_key/`
2. `/api/v1/captcha/`
3. `/api/v1/login/`
4. 后续查询请求带 session cookie

### 3.3 验证原则

每条接口都要经过三层校验：

1. `字段能取到`
2. `字段语义与页面/CLI 一致`
3. `重复调用结果稳定`

## 4. P0-1 接口资产采集合同

### 4.1 `/api/v1/interface/get_all_interface/`

用途：

1. 获取设备全部接口名称集合
2. 识别普通接口、聚合口、桥接口
3. 为后续逐口查询提供全集

请求方式：

`GET`

关键请求参数：

1. `page_type`
   - 代码中存在 `addAgMember` 特殊分支

核心返回特征：

1. 普通口返回：
   - `name`
2. 聚合口额外可能返回：
   - `type=ag`
   - `slaves`
3. 桥接口额外可能返回：
   - `type=bridge`

OneOPS 映射建议：

1. `name` -> `interface.name`
2. `type` -> `interface.kind`
3. `slaves` -> `interface.members`

当前价值：

1. 这是所有接口采集的全集入口
2. 适合做第一条 live 接口验证

### 4.2 `/api/v1/interface/get_physical_interface/`

用途：

1. 获取物理接口完整配置与运行态
2. 是当前最核心的接口资产入口

请求方式：

`GET`

已知代码行为：

1. 会组合配置面、状态面、区域面等多路数据
2. 返回值明显比页面展示更完整

文档级核心字段：

1. 基础标识
   - `name`
   - `alias`
   - `slot`
   - `port`
   - `panel_row`
   - `panel_col`
2. L2/L3 属性
   - `link_model`
   - `connect_type`
   - `connect_type2`
   - `bridge`
   - `area`
3. 地址与路由
   - `ip`
   - `IPv6_prefix`
   - `v6_next_ip`
   - `link_local`
4. 接口介质与状态
   - `status`
   - `link_state`
   - `speed`
   - `ether_type`
   - `medium_type`
5. 管理与角色属性
   - `is_mgmt`
   - `interface_type`
   - `is_set`
6. 访问与带宽
   - `allows`
   - `bandwidth`
7. 高级属性
   - `advanced.mtu`
   - `advanced.mac`
8. IPv4 连接方式结构
   - `connect_type_data.connect_type`
   - `connect_type_data.DHCP`
   - `connect_type_data.PPPOE`
   - `connect_type_data.STATIC`
9. IPv6 结构
   - `ipv6_switch`
   - `IPv6_address_advance`
10. 附加结构
   - `isp`
   - `neighbor`

OneOPS 映射建议：

1. `name` -> 设备接口主键
2. `alias` -> 接口描述
3. `status/link_state/speed/ether_type/medium_type` -> 接口运行态与介质属性
4. `ip/IPv6_prefix/link_local` -> 接口地址事实
5. `connect_type/connect_type_data` -> 地址获取方式
6. `area/interface_type/is_mgmt` -> 管理面与安全域语义
7. `bridge` -> 二层桥接关系
8. `panel_row/panel_col/slot/port` -> 面板可视化与拓扑展示

当前建议：

1. 第一轮只抽稳定只读字段
2. 暂不把 `neighbor`、`isp` 当成强依赖字段
3. 对 `connect_type_data` 要与 CLI 逐项比对

### 4.3 `/api/v1/interface/get_sub_interface/`

用途：

1. 获取子接口与 VLAN 子接口视图
2. 补足仅靠物理口接口无法表达的三层边界

请求方式：

`GET`

关键请求参数：

1. `page_size`
2. `current_page`
3. `name` 可选

文档级核心字段：

1. `name`
2. `alias`
3. `vlan_id`
4. `physical`
5. `connect_type`
6. `tunnel_id`
7. `area`
8. `isp`
9. `neighbor`
10. `bridge`
11. `IPv6_prefix`
12. `v6_next_ip`
13. `ipv6_switch`
14. `connect_type_data`

OneOPS 映射建议：

1. `name` -> 子接口名
2. `physical` -> 父接口引用
3. `vlan_id` -> VLAN tag
4. `area` -> 安全域归属
5. `connect_type_data` -> 子接口三层地址模型

### 4.4 `/api/v1/interface/get_deploy_mode/`

用途：

1. 获取设备部署模式
2. 对透明/路由模式判断非常关键

请求方式：

`GET`

关键请求参数：

1. `mode`
   - 实际校验后会被固定成 `working-mode`

核心返回字段：

1. `mode`
   - `route`
   - `bridge`
   - `none`

OneOPS 映射建议：

1. `mode` -> 设备部署模式
2. 直接影响后续：
   - 策略解释口径
   - 拓扑关系推理
   - bridge 相关接口是否作为主入口

截至 `2026-06-28` 的 live 结论：

1. 当前这条接口在设备侧仍不稳定。
2. 不带参数返回字段必填错误。
3. 带 `mode=working-mode` 后返回设备侧异常：
   - `list indices must be integers or slices, not str`
4. 当前阶段不建议把它作为 OneOPS 的稳定采集入口。
5. 建议替代口径：
   - 以 `get_physical_interface` 中的 `link_model`
   - 加上 `bridge` 字段
   - 先推断当前设备是否处于路由基线或桥接基线
6. 当前基线设备实测为：
   - 全口 `link_model=ROUTE`
   - 无桥绑定

### 4.5 `/api/v1/interface/port_panel/`

用途：

1. 获取设备前面板接口排布
2. 更适合拓扑展示和设备面板视图

请求方式：

`GET`

核心返回结构：

1. 顶层以产品型号为 key
2. `ports` 为二维数组
3. 每个元素至少有：
   - `ifname`

当前定位：

1. 不作为核心采集字段
2. 作为 UI/拓扑增强字段

优先级：`P0-增强`

### 4.6 `/api/v1/interface/get_bridge_fdb/`

用途：

1. 获取桥接口 FDB 表
2. 对透明模式和二层学习关系非常关键

请求方式：

`GET`

参数注意：

1. 实际 serializer 使用 `iface_name`
2. 历史文档示例里曾写成 `name`
3. `param` 会被强制校验为 `fdb`

这条歧义已经完成 live 校验，当前应统一按 `iface_name` 调用。

返回形态：

1. 当前返回的是 `buffer/details` 风格文本
2. 不是天然结构化 JSON

当前定位：

1. 适合做透明模式补强
2. 但需要二次解析

优先级：`P1`

截至 `2026-06-28` 的 live 结论：

1. 使用 `iface_name=br0&param=fdb` 已真实返回 `20000`。
2. 当前基线只返回：
   - `details="br0-vr0:"`
3. 这说明接口已经可用，只是当前基线下尚无更多 FDB 表项。

## 5. P0-2 路由资产采集合同

### 5.1 `/api/v1/route/static/`

用途：

1. 获取静态路由列表
2. 支持按目的网段、下一跳、匹配条件过滤

请求方式：

`GET`

关键请求参数：

1. `ipType`
   - `IPv4`
   - `IPv6`
2. `destination`
3. `nexthop`
4. `match`

核心返回字段：

1. 顶层：
   - `total`
   - `ipv4-static-route` 或 `ipv6-static-route`
2. 路由项：
   - `destination`
   - `next-hop`
3. 下一跳项：
   - `next-hop`
   - `distance`
   - `enable`

OneOPS 映射建议：

1. `destination` -> 静态路由前缀
2. `next-hop[].next-hop` -> 下一跳与出接口绑定事实
3. `distance` -> 管理距离
4. `enable` -> 启用状态

### 5.2 `/api/v1/route/table/`

用途：

1. 获取运行态路由表
2. 是拓扑与路径推理的关键事实源

请求方式：

`GET`

关键请求参数：

1. `ipType`
   - `IPv4`
   - `IPv6`

核心返回字段：

1. 顶层：
   - `total`
   - `ipv4-routes` 或 `ipv6-routes`
2. 路由项：
   - `prefix`
   - `protocol`
   - `selected`
   - `distance`
   - `metric`
   - `installed`
   - `nexthops`
3. 下一跳项：
   - `ip`
   - `interfaceName`
   - `active`
   - `directlyConnected`

OneOPS 映射建议：

1. `prefix` -> 运行态路由前缀
2. `protocol` -> 路由来源
3. `nexthops[].interfaceName` -> 出接口
4. `selected/installed/active` -> 当前生效状态

当前价值：

1. 比静态路由接口更贴近真实转发面
2. 适合与 `show ip route` 或等价 CLI 输出做对照

### 5.3 `/api/v1/routePolicy/list/`

用途：

1. 获取策略路由列表
2. 为路径命中和策略查询提供路由侧规则

请求方式：

`GET`

关键请求参数：

1. `current_page`
2. `page_size`
3. `filter`

核心返回字段：

1. 顶层：
   - `policy-total`
   - `policy`
2. 规则项：
   - `name`
   - `description`
   - `pbr-id`
   - `position-id`
   - `enabled`
   - `group-name`
   - `source-zone`
   - `source-network`
   - `dest-network`
   - `service`
   - `app`
   - `time-range`
   - `out-if`
   - `next-hop-list`
   - `action`
   - `track`
   - `track-status`
   - `match-count`
   - `config-source`
   - `create-time`
   - `invalid`
   - `invalid-type`
   - `_next`
   - `_prev`

OneOPS 映射建议：

1. `source-zone/source-network/dest-network/service/app` -> 匹配条件
2. `out-if/next-hop-list` -> 转发动作
3. `enabled/track-status/invalid` -> 有效性状态
4. `position-id` -> 顺序

### 5.4 `/api/v1/routePolicy/info/`

用途：

1. 获取单条策略路由详情
2. 适合作为列表采集后的详情补全接口

请求方式：

`GET`

关键请求参数：

1. `id`

核心返回字段：

与 `routePolicy/list` 中单条规则字段基本一致，但更适合作为详情真值接口。

当前建议：

1. 先用 `list` 拉全量
2. 再抽样或按需调用 `info`
3. 避免一开始就对每条规则都打详情请求

## 6. 推荐采集顺序

### 6.1 最小闭环

1. 登录
2. `get_all_interface`
3. `get_physical_interface`
4. `get_sub_interface`
5. `get_bridge_fdb`
6. `route/static`
7. `route/table`
8. `routePolicy/list`

### 6.2 原因

1. 先拿接口全集
2. 再拿物理口与子接口事实
3. 再补桥口 FDB 与三层路径
4. 部署模式先由 `link_model + bridge` 推断

## 7. 第一轮 live 验证点

### 7.1 interface 线

1. `get_all_interface` 是否稳定返回聚合口和桥口
2. `get_physical_interface` 中 `is_mgmt/interface_type/area` 是否与当前现场一致
3. `get_sub_interface` 是否能正确反映 VLAN 子接口
4. `get_bridge_fdb` 在无二层学习项时是否仍稳定返回空表头
5. `get_deploy_mode` 的设备侧异常是否能通过后端补丁或替代 RPC 解决

### 7.2 network_router 线

1. `route/static` 与 CLI 静态路由是否逐项一致
2. `route/table` 是否能反映 connected/static 的当前生效态
3. `routePolicy/list` 的对象字段是单对象还是对象数组
4. `track-status`、`invalid`、`match-count` 的语义是否稳定

## 8. 当前不建议过早依赖的部分

1. `neighbor`
2. `isp`
3. `bridge FDB` 的文本返回结构
4. 任何写接口

原因：

1. 这些字段要么语义不够稳定
2. 要么需要额外解析
3. 要么副作用风险过高

## 9. 对 OneOPS 的直接建议

1. 先把这组接口当成“结构化只读补充源”
2. 不要一开始就替代 CLI
3. 最佳策略是：
   - `CLI` 提供原始配置真值
   - `Web API` 提供结构化字段真值
   - 两者交叉比对后再进入平台模型

## 10. 共享口径

`Ruijie 防火墙 P0 采集应先围绕 interface 与 network_router 这两组只读接口展开，用它们补足结构化资产、接口、路由和策略路由事实，再与 CLI 结果做双源校验，逐步形成稳定的 OneOPS 设备采集合同。`
