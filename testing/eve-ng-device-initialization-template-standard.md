# EVE-NG 设备初始化模板标准

更新时间：2026-06-28  
适用范围：OneOPS 第一阶段真实设备测试

## 1. 目的

这份文档用于统一不同设备在进入测试前的初始化模板结构。

目标不是马上把所有设备都配成一样，而是让每一类设备都按同一张标准表来准备：

1. 登录方式
2. 接口命名
3. 带外管理配置
4. 基础远程登录配置
5. 业务接口初始化策略
6. 动态路由初始化策略
7. 验证命令
8. 边界说明

这样后续每初始化一台新设备，新增的是“设备内容”，不是“模板格式”。

## 2. 模板使用规则

后续每一个设备初始化模板，建议都按下面固定章节编写：

1. 设备身份
2. 适用镜像
3. 接口展开与命名表
4. 带外管理初始化
5. 登录初始化
6. 业务接口初始化
7. 路由初始化
8. 验证命令
9. 已实证结果
10. 已知边界

## 3. 通用初始化要求

### 3.1 标准化登录凭据

实验环境不再强制要求所有设备共用同一套账号口令。

当前统一要求改为：

1. 每类设备都必须有一组明确的“标准登录凭据”
2. 这组凭据可以因厂商、设备家族、密码策略不同而不同
3. 只要该凭据已经实证可用、可复现、已写入标准手册，就应视为合格

补充规则：

1. 如果某设备可以稳定收敛到 `admin/admin@123`，可以继续沿用
2. 如果厂商默认密码策略明确拒绝 `admin@123`，不能为了“统一”而假设设备已经支持
3. 这类设备必须在各自标准手册里记录：
   - 当前可接受的标准账号与口令
   - 是否需要首次 SSH 改密
   - 是否需要额外密码策略放宽步骤
   - 是否存在设备级例外口令

### 3.2 带外管理平面

所有业务网络设备都应遵循：

1. 最后一个接口作为带外管理口
2. 带外管理口加入本机 `MGT VRF` 或等价管理平面
3. 带外管理地址从 `172.32.2.0/24` 分配
4. 默认网关指向 `172.32.2.254`
5. 带外口接入 Cisco 网关交换机 `vlan 1`
6. 如果某个镜像在 EVE API 与设备 CLI 之间出现接口编号不一致，标准管理口应以“EVE API 可真实挂线且已实测打通”的最后一个接口为准，并在设备手册里单独记录这个边界

### 3.3 业务接口平面

除带外管理口外，其余业务接口遵循：

1. 初始全部 `no shutdown`
2. 二层口按测试需要加入 VLAN
3. 三层口按测试需要配置 `172.32.64.0/24` 起始地址
4. 除管理平面外，其余三层业务口加入 `OSPF`

### 3.4 验证最小集

每一类设备初始化完成后，至少验证：

1. 控制台可进入
2. 管理地址生效
3. SSH 或等价远程登录可用
4. 管理路由存在
5. 接口命名和模板一致

## 4. 标准模板

后续每台设备都按下面结构记录。

### 4.1 设备身份

1. 设备家族：
2. 设备角色：
3. 厂商：
4. 当前模板状态：
   - `已实证`
   - `文档草案`
   - `待实机验证`

### 4.2 适用镜像

1. EVE 模板：
2. 镜像名称：
3. 建议节点规格：
4. 接口数量：

### 4.3 接口展开与命名表

1. 第 1 到第 20 个接口命名
2. 最后一个接口对应的真实管理口名称
3. 建议业务三层口
4. 建议业务二层口

### 4.4 带外管理初始化

1. `MGT VRF` 或等价管理平面定义
2. 管理接口地址
3. 管理默认网关
4. 管理接口启用命令

### 4.5 登录初始化

1. 本地用户
2. 密码
3. SSH / Telnet / HTTPS / Console 初始策略
4. 密钥或域名要求

### 4.6 业务接口初始化

1. 业务口默认状态
2. 二层 access / trunk 策略
3. 三层口地址规划规则

### 4.7 路由初始化

1. 静态默认路由
2. `OSPF` 初始策略
3. 管理平面与业务平面隔离要求

### 4.8 验证命令

至少包含：

1. 接口查看命令
2. 路由查看命令
3. 管理平面查看命令
4. SSH 状态查看命令

### 4.9 已实证结果

记录：

1. 哪些项已经在 EVE 中实际打通
2. 哪些项只是命令面可写、但未完成外部连通验证

### 4.10 已知边界

记录：

1. 命令差异
2. SSH 算法兼容性
3. 接口命名差异
4. 与共同规则不一致的地方
5. 登录账号或口令的设备级例外

## 5. 第一批设备模板清单

建议先覆盖下面几类：

1. Cisco Gateway Switch
   状态：`已实证`
   参考文档：
   [EVE-NG Cisco 网关交换机标准操作手册](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-cisco-gateway-standard-operation.md)
2. Huawei AR Router
   状态：`已实证`
   参考文档：
   [EVE-NG Huawei AR 路由器标准操作手册](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-huawei-ar-router-standard-operation.md)
3. H3C VSR Router
   状态：`已实证`
   参考文档：
   [EVE-NG H3C VSR 路由器标准操作手册](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-h3c-vsr-router-standard-operation.md)
4. Huawei USG Firewall
   状态：`已实证`
   参考文档：
   [EVE-NG Huawei USG 防火墙标准操作手册](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-huawei-usg-firewall-standard-operation.md)
   补充验证：
   [EVE-NG Huawei USG 策略与 NAT 实机验证记录](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-huawei-usg-policy-nat-live-validation.md)
   标准模板：
   [EVE-NG Huawei USG 防火墙标准模板](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-huawei-usg-firewall-standard-template.md)
5. H3C VFW Firewall
   状态：`草案已可用，模板收敛中`
   参考文档：
   [EVE-NG H3C VFW 防火墙标准操作手册（草案）](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-h3c-vfw-firewall-standard-operation.md)
   补充排查：
   [EVE-NG H3C VFW 防火墙边界排查记录](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-h3c-vfw-firewall-boundary-investigation.md)
6. Cisco ASAv Firewall
   状态：`已实证`
   参考文档：
   [EVE-NG Cisco ASAv 防火墙标准操作手册](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-cisco-asav-firewall-standard-operation.md)
   补充边界：
   [EVE-NG Cisco ASAv 防火墙首轮初始化与边界记录](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-cisco-asav-firewall-initialization-boundary.md)
7. Linux Server
   状态：`已实证`
   参考文档：
   [EVE-NG Linux Server 标准操作手册](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-linux-server-standard-operation.md)
8. Debian Server
   状态：`已实证`
   参考文档：
   [EVE-NG Debian Server 标准操作手册](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-linux-debian-server-standard-operation.md)
9. Kylin Server
   状态：`已实证`
   参考文档：
   [EVE-NG Kylin Server 标准操作手册](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-linux-kylin-server-standard-operation.md)
10. Ruijie Firewall
   状态：`已实证`
   参考文档：
   [EVE-NG Ruijie 防火墙离线启动模板标准操作](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-ruijie-firewall-offline-startup-template-standard.md)
   补充边界：
   [EVE-NG Ruijie 防火墙首轮初始化与边界记录](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-ruijie-firewall-initialization-boundary.md)

## 6. 第一批设备初始化模板矩阵

| 设备家族 | 当前候选镜像 | 主要测试价值 | 当前初始化状态 |
| --- | --- | --- | --- |
| Cisco Gateway Switch | `i86bi_LinuxL2-AdvEnterpriseK9-M_152_May_2018.bin` | 管理底座、带外网关、SSH 基线 | 已实证 |
| Huawei AR Router | `huaweiar1k-5.170-V300R022C00SPC100-Auto-update-esn` | 路由、接口、邻居、采集、监控 | 已实证 |
| H3C VSR Router | `h3cvsr1k-7.1.064` | 国产路由接口与采集 | 已实证，`20` 口与 `MGT` 管理口已打通 |
| Huawei USG Firewall | `huaweiusg6kv-V500R005C10SPC300` | 配置采集、策略、对象、NAT | 已实证，当前仅 `6` 口规格稳定；`SSH` 与管理配置可重启复用；对象与 `permit/deny security-policy` 已完成实机落证；`DNAT` 已落证但当前真实设备不接受带 `destination-zone` 的既有假设；`SNAT easy-ip` 与 `SNAT_POOL` 也已完成实机落证；`HTTP` 可访问，`HTTPS 443` 仍待专项排查 |
| H3C VFW Firewall | `h3cvfw1k-7.1.064` | 防火墙配置采集与策略 | 草案已可用；`GE1/0` 管理口、`Management <-> Local` 放行、`ICMP`、`TCP/22`、设备侧回 `ping`、保存后重启复验均已打通；当前主要边界是 `admin@123` 不能作为稳定复用 SSH 口令，稳定例外口令为 `Admin@1234` |
| Cisco ASAv Firewall | `asav-9.22.1.1-PLR-Licensed` | Cisco 防火墙配置采集、策略、NAT | 已实证，`Mgmt0/0` 管理口、SSH、`enable`、正常启动后的持久化已打通；当前标准依赖恢复启动与 ASA 密码策略例外 |
| Ruijie Firewall | `Ruijiefirewall-V1.03` | 国产防火墙管理模型与策略类测试 | 已实证并完成标准化模板收口：默认首口管理模型、离线启动模板改写、`172.32.2.11/24`、默认路由、`SSH` 均已固化；当前标准固定为 `Ge0/0 + main`，不纳入 `VRF` 支持范围 |
| Ubuntu Server | `linux-ubuntu-server-20.04` | SSH、脚本、监控 | 已实证，当前仅单管理口规格稳定 |
| Debian Server | `linux-debian-10.3.0` | SSH、脚本、监控 | 已实证，`172.32.2.20/24`、`SSH`、`sudo`、重启复验、基础镜像固化后的新节点复验均已打通；当前需明确 `buster archive` 边界 |
| Kylin Server | `linux-Kylin-Server-V11-2503` | SSH、脚本、监控 | 已实证，`172.32.2.21/24`、`SSH`、`sudo`、重启复验、基础镜像固化后的新节点复验均已打通；当前串口控制台仍是专项边界 |
| Linux RHEL Server | `linux-rhel-8.4` | RHEL 服务器 SSH、脚本、监控 | 已完成首轮离线标准化与运行态排查；EVE 管理面与独立 overlay probe 的 `SSH` 都未收敛，当前启动链停在 `firewalld` 阶段附近，暂不纳入稳定模板 |

## 7. 推荐推进顺序

建议按下面顺序继续补齐实际初始化模板：

1. 继续补强 Huawei USG 防火墙真实场景
2. 继续扩展 Linux / 路由器侧场景
3. H3C VFW Firewall 单列专项攻关
4. 其它待引入设备按同一模板继续扩展

原因：

1. 路由器、网关、服务器三条主线已经都有了第一轮可复用模板
2. Huawei USG 已经可以承接主线防火墙流程测试，并具备 `permit / deny / DNAT / SNAT` 四类基础配置样本
3. Ruijie Firewall 已经完成模板收口，后续只需要按既定 `main` 管理模型做增强适配
4. H3C VFW 已经从纯边界排查推进到“模板草案可用”，下一步优先决定是否接受 `Admin@1234` 作为设备例外口令

## 8. 下一步操作建议

从现在开始，后续每完成一类设备初始化，都新增一份独立设备手册，并回写这份总模板标准：

1. 状态改为 `已实证`
2. 增加文档链接
3. 增加已知边界
4. 如果出现“EVE API 可挂线接口”和“设备 CLI 实际接口名”不一致，必须把接口映射结果回写到总模板标准里

这样这份文件会逐步变成“设备初始化标准总表”，而不是一次性草稿。
