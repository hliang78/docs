# EVE-NG `bridge` 到 `pnet0` 最小拓扑模板

更新时间：2026-06-27  
适用环境：`192.168.100.20` 上的 EVE-NG Community `6.2.0-4`

## 1. 这份模板解决什么问题

当我们说“希望 `bridge` 到 `pnet0`”时，真正想要的通常不是把两者强行并成一个宿主机桥，而是：

1. 实验室内部有一个可控的二层测试网
2. 这个内部网可以通过一个边界设备接入外部网络
3. 后续采集、监控、策略、自动化脚本都能在这个边界上做验证

所以推荐模型不是：

1. 直接把 `vnet0_x` 和 `pnet0` 在宿主机上硬桥接

而是：

1. 内部设备接 `bridge`
2. 边界设备一侧接 `bridge`
3. 边界设备另一侧接 `pnet0`

## 2. 推荐最小结构

```text
[Test PC A] --\
               \
                [bridge: Net_inside] -- [Boundary Device] -- [pnet0]
               /
[Test PC B] --/
```

角色说明：

1. `Test PC A / B`
   用来做最小连通、ARP、路由、NAT、ACL、策略命中验证
2. `bridge: Net_inside`
   只承担实验室内部二层互联
3. `Boundary Device`
   推荐用防火墙、路由器或三层交换机
4. `pnet0`
   宿主机外联网络入口，对应物理或上层管理网络

## 3. 为什么不要直接把 `bridge` 当成 `pnet0`

`bridge` 和 `pnet0` 在 EVE 里承担的职责不同：

1. `bridge`
   - 实验室内部虚拟二层网
   - 宿主机上通常表现为 `vnet0_x`
2. `pnet0`
   - EVE 对外云口
   - 宿主机上已经桥到 `eth0`

如果直接在宿主机层面把 `vnet0_x` 和 `pnet0` 混在一起，会带来几个问题：

1. 实验室流量和外部网络流量边界不清
2. 排障时很难区分是设备问题还是宿主机桥问题
3. 更容易误把残留 tap 口、残留 Lab、控制台冲突当成网络故障

因此，OneOPS 后续的真实设备测试，应把“边界控制”放在实验拓扑里的设备上，而不是放在宿主机桥接技巧上。

## 4. 最小拓扑建议

### 4.1 节点构成

推荐最小四元组：

1. `pc-a`
   - 模板：`vpcs` 或轻量 Linux
   - 作用：内网源端
2. `pc-b`
   - 模板：`vpcs` 或轻量 Linux
   - 作用：内网对端
3. `boundary`
   - 模板：优先用后续要测的真实厂商设备
   - 可选：`asav`、`huaweiusg6kv`、`h3cvfw1k`、`Ruijiefirewall`、`huaweiar1k`、`h3cvsr1k`
4. `pnet0 cloud`
   - 类型：`pnet0`
   - 作用：外联目标

### 4.2 网络构成

推荐只保留两张网：

1. `Net_inside`
   - 类型：`bridge`
   - 供 `pc-a`、`pc-b`、`boundary-inside` 共用
2. `Net_outside`
   - 类型：`pnet0`
   - 只给 `boundary-outside` 使用

## 5. 连线方式

推荐的接口关系：

```text
pc-a eth0           -> Net_inside
pc-b eth0           -> Net_inside
boundary ge0/0/0    -> Net_inside
boundary ge0/0/1    -> Net_outside (pnet0)
```

如果边界设备是防火墙或路由器，建议明确标识：

1. `inside`
2. `outside`

不要让同一个设备的两个口都接 `bridge`，否则它就只是内部网里的另一个成员，不是真正的边界。

## 6. 创建顺序

推荐固定顺序：

1. 新建 Lab
2. 新建高 ID 测试节点
3. 新建 `bridge` 网络 `Net_inside`
4. 新建 `pnet0` 网络 `Net_outside`
5. 先挂内部接口
6. 再挂边界设备外联接口
7. 回读每个节点接口
8. 启动节点
9. 控制台配置地址
10. 做分层验证

### 6.1 `bridge` 建议参数

```json
POST /api/labs/<lab>/networks
{
  "name": "Net_inside",
  "left": 420,
  "top": 260,
  "type": "bridge",
  "visibility": 1,
  "icon": "lan.png"
}
```

### 6.2 `pnet0` 建议参数

```json
POST /api/labs/<lab>/networks
{
  "name": "Net_outside",
  "left": 760,
  "top": 260,
  "type": "pnet0",
  "visibility": 1,
  "icon": "cloud.png"
}
```

## 7. 分层验证方法

### 7.1 第一层：内部二层是否正常

目标：

1. 先证明 `bridge` 内部通

做法：

1. `pc-a` 和 `pc-b` 配同网段地址
2. 两端双向 `ping`

示例：

1. `pc-a`: `10.10.20.20/24`
2. `pc-b`: `10.10.20.21/24`

通过标准：

1. 双向 `ping` 成功
2. 说明 `Net_inside` 没问题

### 7.2 第二层：边界设备 inside 口是否接入成功

目标：

1. 证明 `boundary-inside` 已经加入内部网

做法：

1. 给边界设备 inside 口配置 `10.10.20.1/24`
2. `pc-a` 和 `pc-b` `ping 10.10.20.1`

通过标准：

1. 两台测试节点都能到 `10.10.20.1`

### 7.3 第三层：边界设备 outside 口是否接入 `pnet0`

目标：

1. 证明边界设备已经接到外部网络

做法：

1. 给 outside 口配置外联地址
2. 在边界设备上看 ARP、路由、下一跳
3. 如果允许，也可以测试访问 `pnet0` 同网段可达目标

通过标准：

1. outside 口已 up
2. 外联方向有 ARP/邻居
3. 边界设备具备出接口可用性

### 7.4 第四层：内网经边界到外网

目标：

1. 证明“bridge 通过边界接入 `pnet0`”真的成立

做法：

1. `pc-a` 和 `pc-b` 默认网关指向 `10.10.20.1`
2. 在边界设备上完成静态路由或 NAT
3. 从 `pc-a` 发起到外部目标的连通测试

通过标准：

1. 内网主机能经边界访问外联目标

## 8. 这个模板后续怎么复用

### 8.1 采集测试

把 `boundary` 换成真实厂商设备：

1. 防火墙：测配置采集、对象解析、策略提取
2. 路由器：测接口、路由、NAT、邻居采集
3. 交换机：测 VLAN、接口、MAC、STP 采集

### 8.2 监控测试

复用同一拓扑：

1. `boundary` 作为被监控主设备
2. `pc-a / pc-b` 负责制造流量
3. `pnet0` 侧验证外联指标或边界行为

### 8.3 策略测试

对防火墙类设备：

1. `pc-a -> pc-b`
   用来验证内网策略
2. `pc-a -> pnet0`
   用来验证出网策略

## 9. 当前环境的特殊约束

这台 `192.168.100.20` 需要额外注意：

1. 如果未来再次出现常驻实验室，低 ID 节点控制台端口仍可能与其它实验室冲突
2. 删除 Lab 后，宿主机可能残留孤儿 tap 口
3. 排障时要同时看：
   - EVE API
   - 宿主机 `brctl show`
   - `bridge link`
   - `ip tuntap list`

因此，本模板在当前环境里执行时，建议固定增加两个前置动作：

1. 如果不是全新空白环境，创建节点后优先使用高 ID 节点做数据面验证
2. 测试结束后，验证宿主机 bridge 下没有残留 `vunl...` 口

## 10. 推荐的第一批模板变体

建议先沉淀成这三套：

1. `bridge + asav + pnet0`
   适合：防火墙策略、NAT、对象和配置解析
2. `bridge + huaweiar1k + pnet0`
   适合：路由、接口、采集、监控
3. `bridge + h3cvsr1k + pnet0`
   适合：国产路由设备采集、监控和自动化脚本

如果只是做最小网络联通验证，则先用：

1. `2 x vpcs`
2. `1 x boundary`
3. `1 x bridge`
4. `1 x pnet0`

这套最小模板跑通后，再替换边界设备即可。
