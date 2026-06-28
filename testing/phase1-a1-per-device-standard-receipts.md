# A1 逐设备标准回执

更新时间：2026-06-28  
适用环境：`192.168.100.20` 上的 EVE-NG Community `6.2.0-4`

## 1. 目的

这份文档把 `A1` 从“总表回执”继续展开成“逐设备标准回执”。

它服务于三个目标：

1. 给每类设备提供统一格式的接入基线记录
2. 让网络设备、服务器设备、防火墙设备都能按同一骨架继续补证
3. 让后续 `B1/C1/C2/D1/E1` 场景直接复用这些标准回执，不再重复整理登录和管理面前提

上层依据：

1. [A1 单设备接入基线回执（第一版）](/Users/huangliang/project/OneOPS-ALL/docs/testing/phase1-a1-single-device-baseline-receipt-v1.md)
2. [第一阶段设备登录凭据基线](/Users/huangliang/project/OneOPS-ALL/docs/testing/phase1-device-login-baseline.md)
3. [第一批联合场景可执行测试清单](/Users/huangliang/project/OneOPS-ALL/docs/testing/phase1-first-batch-executable-checklist.md)
4. [A1 最小监控任务补证标准](/Users/huangliang/project/OneOPS-ALL/docs/testing/phase1-a1-minimal-monitoring-task-evidence.md)

## 2. 统一回执字段

后续每类设备都按下面 5 个字段维护：

1. 标准管理模型
2. 标准登录基线
3. `A1` 当前证据状态
4. 当前支持边界
5. 下一步补证重点

## 3. 网络设备

### 3.1 Cisco Gateway Switch

1. 标准管理模型：
   `Vlan1@MGT VRF`，管理地址 `172.32.2.254/24`，外联口通过 `pnet0`
2. 标准登录基线：
   `SSH`，`admin/admin@123`
3. `A1` 当前证据状态：
   已有既有直接实证；当前作为稳定底座，无本轮在线复验
4. 当前支持边界：
   设备侧 SSH 与管理配置已可复用，但客户端需兼容老 IOS SSH 算法
5. 下一步补证重点：
   在 `B1/B2` 里补“网关 + 双路由器”同窗口复验证据

参考：

1. [EVE-NG Cisco 网关交换机标准操作手册](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-cisco-gateway-standard-operation.md)

### 3.2 Huawei AR

1. 标准管理模型：
   最后一个管理口接入 Cisco 网关，管理地址 `172.32.2.10/24`，管理平面在 `MGT`
2. 标准登录基线：
   `SSH`，`admin/admin@123`；首次 Console 创建账号后必须重新登录一次
3. `A1` 当前证据状态：
   已有既有直接实证；当前未在本轮在线实测集
4. 当前支持边界：
   仅配置 `stelnet server enable` 不够，必须显式补 `ssh server permit interface`
5. 下一步补证重点：
   在 `B1` 里补 `OSPF` 邻居、路由、拓扑三段联调证据

参考：

1. [EVE-NG Huawei AR 路由器标准操作手册](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-huawei-ar-router-standard-operation.md)

### 3.3 H3C VSR

1. 标准管理模型：
   `GE20/0` 接入 Cisco 网关，管理地址 `172.32.2.15/24`，管理平面在 `MGT`
2. 标准登录基线：
   `SSH`，`admin/admin@123`；依赖密码策略放宽，客户端需兼容 `ssh-rsa`
3. `A1` 当前证据状态：
   已有既有直接实证；当前未在本轮在线实测集
4. 当前支持边界：
   `admin/admin@123` 不是天然默认值，而是初始化收敛结果
5. 下一步补证重点：
   在 `B1` 里补与 Huawei AR 的互联、邻居、路由、拓扑统一回执

参考：

1. [EVE-NG H3C VSR 路由器标准操作手册](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-h3c-vsr-router-standard-operation.md)

## 4. 防火墙设备

### 4.1 Huawei USG

1. 标准管理模型：
   `GigabitEthernet0/0/0` 绑定 `MGT`，管理地址 `172.32.2.13/24`
2. 标准登录基线：
   默认 `admin/Admin@123`，首次 Console 强制改密后收敛到 `admin/admin@123`
3. `A1` 当前证据状态：
   已有既有直接实证；管理、SSH、策略与 NAT 最小链已打通
4. 当前支持边界：
   `HTTP` 管理面可访问，但 `HTTPS 443` 当前仍未形成稳定外部访问
5. 下一步补证重点：
   在 `C1` 里补策略生成、策略查询、`DNAT/SNAT` 与客户流量回执

参考：

1. [EVE-NG Huawei USG 防火墙标准操作手册](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-huawei-usg-firewall-standard-operation.md)
2. [EVE-NG Huawei USG 策略与 NAT 实机验证记录](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-huawei-usg-policy-nat-live-validation.md)

### 4.2 H3C VFW

1. 标准管理模型：
   `GE1/0` 接入管理桥，管理地址 `172.32.2.17/24`，通过 `Management <-> Local` 放行管理流量
2. 标准登录基线：
   `SSH`，稳定口令例外值为 `admin/Admin@1234`
3. `A1` 当前证据状态：
   本轮在线实测已通过“管理地址可达 + SSH 可登录 + 身份可回读”
4. 当前支持边界：
   `admin@123` 只能作为首登触发口令，不能作为稳定复用 SSH 口令
5. 下一步补证重点：
   补最小监控任务证据，并决定是否把它继续保留在边界专项，还是纳入主线统计

参考：

1. [EVE-NG H3C VFW 防火墙标准操作手册（草案）](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-h3c-vfw-firewall-standard-operation.md)
2. [EVE-NG H3C VFW 防火墙边界排查记录](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-h3c-vfw-firewall-boundary-investigation.md)

### 4.3 Ruijie Firewall

1. 标准管理模型：
   `Ge0/0 + main`，管理地址 `172.32.2.11/24`，当前不纳入 `VRF` 支持范围
2. 标准登录基线：
   标准模板仍记为 `admin/admin@123`；当前在线节点实测为 `admin/qwerASDF!@34`
3. `A1` 当前证据状态：
   本轮在线实测已证明管理面可达、`SSH` 可登录，但模板已漂移
4. 当前支持边界：
   设备可登录不等于模板已收敛；当前应把它视为“接入已通但模板漂移”
5. 下一步补证重点：
   二选一收敛：
   把在线节点拉回 `admin/admin@123`；或把 `qwerASDF!@34` 正式收敛成新的设备标准凭据

参考：

1. [EVE-NG Ruijie 防火墙离线启动模板标准操作](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-ruijie-firewall-offline-startup-template-standard.md)
2. [EVE-NG Ruijie 防火墙首轮初始化与边界记录](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-ruijie-firewall-initialization-boundary.md)

### 4.4 Cisco ASAv

1. 标准管理模型：
   `Management0/0`，管理地址 `172.32.2.18/24`，管理路由指向 `172.32.2.254`
2. 标准登录基线：
   先用临时口令 `Adm1n@132`，首次 SSH 强制改密后收敛到 `admin/Adm1n@134`
3. `A1` 当前证据状态：
   已有既有直接实证；SSH、`enable`、持久化复验已完成
4. 当前支持边界：
   `admin@123` 不符合当前密码策略；`enable password` 需要和最终口令同步
5. 下一步补证重点：
   在 `C3` 里补对象、策略、持久化与恢复启动后的统一回执

参考：

1. [EVE-NG Cisco ASAv 防火墙标准操作手册](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-cisco-asav-firewall-standard-operation.md)

## 5. 服务器设备

### 5.1 Ubuntu Server

1. 标准管理模型：
   单管理口，静态地址接入管理网络
2. 标准登录基线：
   `SSH`，`admin/admin@123`；`root/admin@123` 作为回退入口
3. `A1` 当前证据状态：
   已有既有直接实证；SSH、`sudo`、重启复验已完成
4. 当前支持边界：
   当前只实证了单管理口规格
5. 下一步补证重点：
   在 `D1/E1` 里补监控任务、自动化脚本、跨防火墙行为证据

参考：

1. [EVE-NG Linux Server 标准操作手册](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-linux-server-standard-operation.md)

### 5.2 Debian Server

1. 标准管理模型：
   单管理口，静态地址接入管理网络
2. 标准登录基线：
   `SSH`，`admin/admin@123`；`root/admin@123` 作为回退入口
3. `A1` 当前证据状态：
   已有既有直接实证；SSH、`sudo`、新节点复验已完成
4. 当前支持边界：
   `buster archive` 仍是环境准备边界，后续自动化脚本要避免旧源假设
5. 下一步补证重点：
   在 `D1/E1` 里补批量任务、监控与脚本执行回执

参考：

1. [EVE-NG Debian Server 标准操作手册](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-linux-debian-server-standard-operation.md)

### 5.3 Kylin Server

1. 标准管理模型：
   单管理口，静态地址接入管理网络
2. 标准登录基线：
   `SSH`，`admin/admin@123`；`root/admin@123` 作为回退入口
3. `A1` 当前证据状态：
   已有既有直接实证；SSH、`sudo`、重启复验已完成
4. 当前支持边界：
   串口控制台当前不稳定，应把 SSH 视为主入口
5. 下一步补证重点：
   在 `D1/E1` 里补 SSH 任务、监控和脚本链路回执

参考：

1. [EVE-NG Kylin Server 标准操作手册](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-linux-kylin-server-standard-operation.md)

## 6. A1 当前总体判断

从“逐设备标准回执”的角度看，`A1` 当前状态应判断为：

1. 标准管理模型已经基本收口
2. 标准登录基线已经基本收口
3. 逐设备接入证据已经具备第一版可复用框架
4. 但最小监控任务证据仍普遍缺失
5. Ruijie 当前仍存在模板漂移

因此：

1. `A1` 已进入可持续补证阶段
2. 后续每次补证，应优先回写这份逐设备标准回执
