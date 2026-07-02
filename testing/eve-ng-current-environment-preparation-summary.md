# EVE-NG 当前测试环境准备总览

更新时间：2026-06-29  
适用环境：`192.168.100.20` 上的 EVE-NG Community `6.2.0-4`

## 1. 目的

这份文档用于回答一个最现实的问题：

围绕 OneOPS 第一阶段真实设备测试，当前这套 EVE 环境到底已经准备到什么程度。

它不是方案文档，而是环境盘点文档。重点不在“理论上可以做什么”，而在“当前已经实证可复用什么、哪些设备线可以直接进入测试、哪些边界已经明确不应混入主线”。

## 2. 当前环境已经形成的共同底座

### 2.1 统一的拓扑模型

当前已经明确采用统一的共同模型：

1. 固定一台 Cisco 网关交换机作为基础设施设备
2. 网关设备只负责外联和带外管理，不参与业务测试
3. 其余节点统一视为业务网络设备
4. 业务设备根据每轮测试目标变化，灵活连线和组合

对应标准文档：

1. [EVE-NG 管理网关拓扑标准](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-mgt-gateway-topology-standard.md)
2. [EVE-NG Cisco 网关交换机标准操作手册](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-cisco-gateway-standard-operation.md)
3. [第一阶段网络设备主线 EVE 底座实测回执（第一版）](/Users/huangliang/project/OneOPS-ALL/docs/testing/phase1-network-mainline-eve-baseline-live-validation-v1.md)

### 2.2 统一的管理网络模型

当前已经收敛出的共同规则如下：

1. 网关交换机第一个上联口连接 `pnet0`
2. 网关交换机在 `MGT VRF` 中使用 `192.168.100.150/24` 对外联通
3. 网关交换机 `interface vlan1` 在 `MGT VRF` 中使用 `172.32.2.254/24`
4. 所有业务网络设备的带外管理地址从 `172.32.2.0/24` 分配
5. 业务三层互联地址从 `172.32.64.0/24` 起分配
6. 默认把非管理接口纳入动态路由域，当前共同约定以 `OSPF` 为主

这意味着后续无论测试防火墙、路由器还是服务器，都已经有一个统一的管理与地址平面，不需要每次重搭基础环境。

补充状态：

1. `2026-06-29` 已完成 `oneops-network-mainline-v1.unl` 的第一轮真实落地
2. `GW/ACC1/ACC2/R1/R2/R3/R4/S1/S2/OBS` 已完成一轮真实初始化与联通性复验
3. `R1/R2/R3/R4` 的 OSPF Full Mesh 已达到 `3/3 Full`
4. `S1/S2` 已完成跨业务网互通

### 2.3 统一的初始化模板方法

当前已经形成统一的设备初始化模板标准：

1. 每类设备先形成“首登与基础配置标准”
2. 再固化为可重复的初始化模板
3. 再在新节点上复验模板是否可直接复用
4. 最后把该设备纳入第一阶段真实场景测试矩阵

对应标准文档：

1. [EVE-NG 设备初始化模板标准](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-device-initialization-template-standard.md)

本轮新增的现实结论：

1. Ubuntu 20.04 这版服务器镜像，`netplan` 默认路由应固定写成 `to: 0.0.0.0/0`
2. Linux 控制台初始化自动化应固定先做一次显式 `sudo` 授权握手
3. 华为 AR 的 Mesh 口应固定补 `ospf network-type p2p`，避免 `2-Way/ExStart` 停留
4. `OBS` 不按普通业务服务器规格处理，固定按 `8 vCPU / 16G RAM` 运行

## 3. 已经可以直接进入第一阶段测试的设备线

下面这些设备线，当前已经不只是“镜像存在”，而是已经完成了至少一轮可复用的初始化和管理面实证。

### 3.1 网络设备

1. Cisco 网关交换机
   已作为共同基础设施设备实证可用。
2. Huawei AR 路由器
   已实证 `MGT` 实例、管理 IP、`stelnet` 和标准初始化路径。
3. H3C VSR 路由器
   已实证 `GE20/0` 管理口、`MGT` 实例和 SSH 登录；登录凭据以设备标准手册为准，不再要求与其他设备完全统一。

对应文档：

1. [EVE-NG Cisco 网关交换机标准操作手册](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-cisco-gateway-standard-operation.md)
2. [EVE-NG Huawei AR 路由器标准操作手册](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-huawei-ar-router-standard-operation.md)
3. [EVE-NG H3C VSR 路由器标准操作手册](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-h3c-vsr-router-standard-operation.md)

### 3.2 防火墙设备

1. Huawei USG 防火墙
   已实证管理口、`MGT` 实例、SSH、策略与 NAT 最小落证。
2. Ruijie 防火墙
   已实证首口管理模型、离线启动模板改写、SSH 和 Web 采集入口。
3. Cisco ASAv 防火墙
   已实证恢复启动、管理口、SSH、持久化复验。

补充口径：

1. 第一阶段现在允许不同设备保留各自标准登录账号或口令
2. 测试关注点是“凭据是否已文档化、可复现、可回执”，不是“是否全设备完全统一”

对应文档：

1. [EVE-NG Huawei USG 防火墙标准操作手册](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-huawei-usg-firewall-standard-operation.md)
2. [EVE-NG Huawei USG 策略与 NAT 实机验证记录](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-huawei-usg-policy-nat-live-validation.md)
3. [EVE-NG Huawei USG 防火墙标准模板](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-huawei-usg-firewall-standard-template.md)
4. [EVE-NG Ruijie 防火墙离线启动模板标准操作](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-ruijie-firewall-offline-startup-template-standard.md)
5. [EVE-NG Ruijie 防火墙首轮初始化与边界记录](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-ruijie-firewall-initialization-boundary.md)
6. [EVE-NG Cisco ASAv 防火墙标准操作手册](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-cisco-asav-firewall-standard-operation.md)

### 3.3 服务器设备

1. Ubuntu Server
   已实证统一账号、静态管理地址、SSH、`sudo`、`SNMP v2c` 与重启复验。
2. Debian Server
   已实证统一账号、静态管理地址、SSH、`sudo` 与新节点复验。
3. Kylin Server
   已实证统一账号、静态管理地址、SSH、`sudo` 与新节点复验。

补充口径：

1. 主线里的 `S1/S2` 可按普通业务服务器轻量规格处理
2. `OBS` 固定为观测面例外项，资源规格固定为 `8 vCPU / 16G RAM`
3. 后续 `controller + agent`、集中任务入口和监控联动都默认落在这台高规格 `OBS` 上

对应文档：

1. [EVE-NG Linux Server 标准操作手册](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-linux-server-standard-operation.md)
2. [EVE-NG Debian Server 标准操作手册](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-linux-debian-server-standard-operation.md)
3. [EVE-NG Kylin Server 标准操作手册](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-linux-kylin-server-standard-operation.md)

## 4. 当前已经明确的边界设备线

边界被明确下来，本身就是环境准备的重要成果。这样后续主线测试不会再被不稳定设备反复拖住。

### 4.1 H3C VFW 防火墙

当前只能视为边界专项，不应纳入第一阶段主线标准模板。

已确认：

1. 节点可启动
2. 接口可展开
3. 接口可配地址
4. 本地 `22/tcp` 已监听

但当前未收敛：

1. 外部到设备自身的 `ICMP`
2. 外部到设备自身的 `SSH`
3. 稳定的三层控制面出入方向闭环

对应文档：

1. [EVE-NG H3C VFW 防火墙边界排查记录](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-h3c-vfw-firewall-boundary-investigation.md)

### 4.2 RHEL 8.4 服务器

当前不应作为主线服务器标准镜像。

已确认：

1. 离线账号标准化可行
2. 离线静态地址写入可行
3. 运行态管理面始终未收敛

核心边界：

1. `ARP` 未稳定收敛
2. `ICMP` 未打通
3. `SSH` 未打通
4. 串口控制台未形成稳定入口

对应文档：

1. [EVE-NG Linux RHEL Server 首轮初始化与边界记录](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-linux-rhel-server-boundary-investigation.md)

### 4.3 Ruijie 防火墙的模型例外

Ruijie 防火墙不是不可用，而是必须明确例外模型：

1. 第一阶段不把 `VRF` 纳入其可交付支持范围
2. 标准管理模型固定为 `Ge0/0 + main`
3. 不再要求它服从“最后一个口作为管理口”的共同规则
4. 登录口令应按设备当前标准模板单独记录，不再以“必须回到统一口令”作为通过前提

这条例外已经明确写入设备标准，后续测试应按该标准推进，不要回到旧假设上反复试错。

## 5. 服务器基线替代路线

当前已经明确：

1. 旧 `RHEL 8.4` 路线不适合作为主线基线
2. 新主线应转向 `Rocky 9 GenericCloud`
3. 这条路线的准备方案已经落文档

对应文档：

1. [EVE-NG Rocky Linux Server 准备方案](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-linux-rocky-server-preparation-plan.md)

补充状态：

1. 官方 Rocky 9 下载地址已确认可达
2. 当前镜像下载已按要求暂停
3. 不影响现有环境汇总与第一阶段测试设计继续推进

## 6. 当前环境准备的阶段判断

如果以“是否已经具备围绕真实设备设计针对性测试”的标准来看，当前环境准备可以判断为：

1. 基础拓扑底座已就绪
2. 统一管理平面已就绪
3. 多条设备标准线已就绪
4. 关键边界线已明确
5. 可以正式进入第一阶段场景化测试设计

但同时也要保持清醒：

1. 这还不是“全部设备都已经稳定”
2. 这也不是“所有镜像都已完成标准化”
3. 当前更准确的状态是：
   已经具备围绕真实设备做系统性第一阶段测试的基础条件

补充说明：

1. 对网络设备主线来说，EVE 底座已经不是“待设计”，而是“已真实跑通”
2. 当前真正尚未开始的是 OneOps 侧的正式 `采集 / 监控 / 拓扑` 三段回执

## 7. 建议的下一步

当前最应该推进的不是继续泛化找更多镜像，而是把已经准备好的设备线接入统一测试矩阵。

下一步建议顺序：

1. 先从当前已就绪设备里挑出第一批联合场景
2. 先把 `OBS` 上的 `controller + agent` 补齐；执行前固定确认 `OBS = 8 vCPU / 16G RAM`
3. 再按采集、监控、解析、策略、拓扑、自动化脚本拆出验证链
4. 针对每类设备补“高风险薄弱点”专项场景
5. 每轮测试都回写证据、失败事实和支持边界

对应入口文档：

1. [第一阶段真实设备测试矩阵](/Users/huangliang/project/OneOPS-ALL/docs/testing/phase1-real-device-test-matrix.md)
2. [第一阶段网络设备主线 EVE 底座实测回执（第一版）](/Users/huangliang/project/OneOPS-ALL/docs/testing/phase1-network-mainline-eve-baseline-live-validation-v1.md)
3. [OBS `controller + agent` 部署前置检查清单](/Users/huangliang/project/OneOPS-ALL/docs/testing/phase1-obs-controller-agent-precheck-checklist.md)
