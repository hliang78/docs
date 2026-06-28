# EVE-NG 第一批设备候选清单

更新时间：2026-06-28  
适用环境：`192.168.100.20` 上的 EVE-NG Community `6.2.0-4`

## 1. 目的

这份清单只回答一个问题：

当前这台 EVE 上，哪些镜像已经真实存在，可以直接进入 OneOPS 第一阶段测试。

这份文档的价值在于避免“方案写得很好，但 EVE 上没有对应镜像”。

## 2. 盘点方式

本次通过 EVE API 的模板列表接口对当前环境做了实际盘点，重点查看了防火墙、路由器和服务器类模板下的可用镜像。

结论以“当前环境实测能列出镜像名称”为准，而不是以模板理论支持列表为准。

## 3. 当前已发现的可用镜像

### 3.1 防火墙类

已发现：

1. `asav-9.22.1.1-PLR-Licensed`
2. `huaweiusg6kv-2018`
3. `huaweiusg6kv-5.1.7-2018`
4. `huaweiusg6kv-V500R005C10SPC300`
5. `h3cvfw1k-7.1.064`
6. `Ruijiefirewall-V1.03`

当前未在这台环境中看到可直接列出的镜像：

1. `fortinet`
2. `paloalto`
3. `vsrx`
4. `vsrxng`

这不代表平台永远不支持，只代表当前 EVE 环境里还不能直接用它们起第一批测试。

### 3.2 网络设备类

已发现：

1. `i86bi_LinuxL2-AdvEnterpriseK9-M_152_May_2018.bin`
2. `i86bi_linux_l2-adventerprisek9-ms.SSA.high_iron_20190423.bin`
3. `x86_64_crb_linux_l2-adventerprisek9-ms.bin`
4. `i86bi_LinuxL3-AdvEnterpriseK9-M2_157_3_May_2018.bin`
5. `x86_64_crb_linux-adventerprisek9-ms.bin`
6. `huaweiar1k-5.170`
7. `huaweiar1k-5.170-V300R019C00SPC300-Auto-update-esn`
8. `huaweiar1k-5.170-V300R021C00SPC100T-Auto-update-esn`
9. `huaweiar1k-5.170-V300R022C00SPC100-Auto-update-esn`
10. `h3cvsr1k-7.1.064`

当前未在这台环境中看到可直接列出的镜像：

1. `csr1000v`
2. `vios`
3. `viosl2`
4. `veos`
5. `vyos`
6. `mikrotik`
7. `hpvsr`

补充说明：

1. 当前环境里已经存在可用的 Cisco IOL 二层和三层镜像。
2. 这意味着“思科网关交换机”这条基础设计，在当前 EVE 上具备落地前提。
3. 本次临时探测中，EVE `iol` 模板已实测支持 `ethernet=5`，而模板定义里“1 模块 = 4 个接口”，因此当前环境下把网关设备起成 `20` 个以太网接口是可行的。
4. 本次探测中宿主机真实进程参数也已看到 `-e 5`，说明并不是纸面配置，而是实际按 `20` 口规格启动。
5. 其中 `i86bi_LinuxL2-AdvEnterpriseK9-M_152_May_2018.bin` 已经完成 CLI 级确认，可作为当前标准网关镜像。
6. 对它的具体创建与配置步骤，统一参照：
   [EVE-NG Cisco 网关交换机标准操作手册](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-cisco-gateway-standard-operation.md)
7. 如果后续改用其它 Cisco IOL 镜像，仍然需要单独确认：
   - `MGT VRF` 命令是否可用
   - `interface vlan1` 是否支持所需配置
   - 第一个上联口和其余管理口的命名是否符合预期
8. `huaweiar1k-5.170-V300R022C00SPC100-Auto-update-esn` 已完成 CLI 级初始化验证，可直接作为当前华为路由器标准镜像。
9. 它当前已经实测打通：
   - 首登本地账号创建
   - `MGT` 管理实例
   - 管理口 `172.32.2.10/24`
   - `stelnet` 登录
10. 它当前需要明确记录的边界是：
   - 首登建账号后串口会主动退出，必须再次登录
   - 必须显式停止 `Auto-Config`
   - EVE API 可挂线接口到 `G0/0/19`，但 CLI 多显示一个 `GigabitEthernet0/0/20`
   - 必须额外执行 `ssh server permit interface GigabitEthernet0/0/19`，否则 SSH 端口虽然已监听，但同网段建连会卡住
11. 对它的具体创建与初始化步骤，统一参照：
   [EVE-NG Huawei AR 路由器标准操作手册](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-huawei-ar-router-standard-operation.md)
12. `h3cvsr1k-7.1.064` 已完成第一轮 CLI 与管理面初始化验证，可作为当前 H3C 路由器标准镜像。
13. 它当前已经实测打通：
   - `ethernet=20` 规格
   - 最后一个口 `GE20/0` 作为管理口
   - `MGT` 管理实例
   - 管理地址 `172.32.2.15/24`
   - 实际 SSH 登录
14. 它当前必须明确记录的边界是：
   - 为了保留统一实验口令 `admin/admin@123`，必须放宽默认密码控制
   - SSH 客户端需要兼容 `ssh-rsa` host key
   - `ip vpn-instance` 语法与华为 AR 不同，不能套用 `ipv4-family` 子视图
15. 对它的具体创建与初始化步骤，统一参照：
   [EVE-NG H3C VSR 路由器标准操作手册](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-h3c-vsr-router-standard-operation.md)
16. `huaweiusg6kv-V500R005C10SPC300` 已完成第一轮 CLI 与管理面初始化验证，可作为当前华为防火墙标准镜像。
17. 它当前已经实测打通：
   - 默认 `admin / Admin@123` 首登改密
   - 专用 `MGMT` 口初始化
   - `MGT` 管理实例
   - `22/tcp` 与实际 SSH 登录
18. 它当前必须明确记录的边界是：
   - 当前 EVE 上只有 `ethernet=6` 规格稳定
   - 强扩到 `ethernet=20` 后，管理数据面不稳定，不能直接作为标准
   - SSH 认证依赖 `aaa -> manager-user admin`，不是 `local-user`
   - SSH 客户端需要兼容 `diffie-hellman-group14-sha1`
19. 对它的具体创建与初始化步骤，统一参照：
   [EVE-NG Huawei USG 防火墙标准操作手册](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-huawei-usg-firewall-standard-operation.md)
20. `h3cvfw1k-7.1.064` 已完成管理面最小模型验证，当前可作为 H3C 防火墙模板草案继续推进。
21. 它当前已经实测打通：
   - 节点可正常启动
   - `ethernet=20` 可展开
   - 接口可配 IP，ARP 可应答
   - `22/tcp` 本地已监听
   - 管理口 `GE1/0`
   - `Management` 安全域成员导入
   - `Management -> Local` 与 `Local -> Management` 的 `zone-pair`
   - 通过 `packet-filter ACL` 显式放行管理流量
   - 宿主机 `ping 172.32.2.17`
   - 宿主机 `TCP/22` 探测
   - 设备侧 `ping 172.32.2.254`
22. 它当前必须明确记录的边界是：
   - 当前可工作的最小模型不是通用资料里的 `manage ping/manage ssh`，而是 `zone-pair + packet-filter ACL`
   - 当前管理口不是最后一个口，而是第一个口 `GE1/0`
   - `admin@123` 会触发首次 SSH 强制改密，不能作为稳定复用口令
   - 当前已实证稳定 SSH 例外口令为 `Admin@1234`
   - 当前已经完成 `save force + 重启复验`
23. 当前更适合把它视为“基础管理已打通、模板草案收敛中、存在实验口令例外”的 H3C 防火墙候选镜像。
24. 对它的当前初始化草案，统一参照：
   [EVE-NG H3C VFW 防火墙标准操作手册（草案）](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-h3c-vfw-firewall-standard-operation.md)
25. 对它的完整排查与剩余边界，统一参照：
   [EVE-NG H3C VFW 防火墙边界排查记录](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-h3c-vfw-firewall-boundary-investigation.md)
25. `Ruijiefirewall-V1.03` 已完成第一轮初始化入口验证，并已实证官方回灌链路和离线启动模板改写路径，可作为当前锐捷防火墙候选镜像继续推进。
26. 它当前已经实测打通：
   - 默认控制台登录 `admin / firewall`
   - 首登改密到 `admin@123`
   - 默认首口 `Ge0/0` 管理地址 `192.168.1.200/24`
   - 默认 `ping` 与 `HTTPS` 管理面
   - 把管理连线切到第一个口后，宿主机实际 `ping` 通默认管理地址
   - `cmd backup-config -> cmd import-config` 官方回灌链路
   - 离线改写 `ntos-interface.startup` 后，设备直接以 `172.32.2.11/24` 启动
   - `admin / admin@123` 的实际 SSH 登录
27. 它当前必须明确记录的边界是：
   - `ethernet=20` 形态下，只有前 8 个口进入标准防火墙接口命名
   - 后续扩展口仍表现为 Linux 风格接口名
   - “最后一个口作为管理口”的统一规则当前不适用
   - 第一阶段标准管理口应固定为 `Ge0/0`，不继续把最后一个口纳入正式模板目标
   - Web 登录验证码不适合作为自动化初始化主路径
   - 官方备份包中的真实配置载荷是加密文件，不能直接按备份包方式离线改写
   - 当前虽然已能离线改写 `LYB` 启动文件，但参数化模板与 `main` 管理模型的默认路由仍待补强
   - `VRF` 只存在部分配置能力，不纳入当前可交付支持范围
28. 当前更适合把它视为“已探明默认管理模型、已实证官方回灌链路与离线启动模板改写、按 `Ge0/0 + main` 推进的模板草案”。
29. 对它的具体证据与边界，统一参照：
   [EVE-NG Ruijie 防火墙首轮初始化与边界记录](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-ruijie-firewall-initialization-boundary.md)
30. `asav-9.22.1.1-PLR-Licensed` 已完成第一轮 CLI 与管理面初始化验证，可作为当前 Cisco 防火墙标准镜像进入第一阶段测试。
31. 它当前已经实测打通：
   - EVE API 新建节点、网络、挂线与启动
   - `Mgmt0/0 + Gi0/0 .. Gi0/6` 的接口模型回读
   - 首次启动自动 clone reboot
   - `GRUB -> with no configuration load` 恢复启动
   - 管理口 `172.32.2.18/24`
   - 管理默认路由 `172.32.2.254`
   - 本地管理员与 SSH 实际登录
   - 正常启动后的重启持久化复验
32. 它当前必须明确记录的边界是：
   - 当前标准初始化依赖一次恢复启动，不是普通首启直接配
   - 当前控制台正常启动后自动登录用户是 `enable_1`，权限只有 `priv 1`
   - 删除节点后，EVE `tmp` 覆盖目录不一定自动清理
   - 统一实验口令 `admin/admin@123` 会被 ASA 连续字符策略拒绝
   - Console 重置本地用户密码后，首次 SSH 登录必须再改密一次
   - SSH 客户端需要兼容 `ssh-rsa` host key
33. 对它的具体创建与初始化步骤，统一参照：
   [EVE-NG Cisco ASAv 防火墙标准操作手册](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-cisco-asav-firewall-standard-operation.md)
34. 对它的现场证据与边界，统一参照：
   [EVE-NG Cisco ASAv 防火墙首轮初始化与边界记录](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-cisco-asav-firewall-initialization-boundary.md)

### 3.3 服务器 / Linux 类

已发现：

1. `linux-Kylin-Server-V11-2503`
2. `linux-debian-10.3.0`
3. `linux-rhel-8.4`
4. `linux-ubuntu-server-18.04.4`
5. `linux-ubuntu-server-20.04`

当前未在这台环境中看到可直接列出的镜像：

1. `win`

补充说明：

1. `linux-ubuntu-server-20.04` 已完成第一轮标准初始化验证，可作为当前服务器类标准镜像。
2. 它当前已经实测打通：
   - 离线统一账号 `admin/admin@123`
   - `root/admin@123` 回退登录
   - 静态管理地址 `172.32.2.14/24`
   - 实际 SSH 登录
   - `sudo` 权限
   - 初始化后重启复验
3. 它当前必须明确记录的边界是：
   - 默认镜像只有未知 `root` 口令和 DHCP 管理口
   - 如果基础镜像标准化发生在节点创建之后，必须删节点重建
   - 当前只实证了 `ethernet=1`，还不是多口服务器模板
4. 对它的具体创建与初始化步骤，统一参照：
   [EVE-NG Linux Server 标准操作手册](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-linux-server-standard-operation.md)
5. `linux-debian-10.3.0` 已完成第一轮标准初始化验证，可作为当前 Debian 服务器标准镜像。
6. 它当前已经实测打通：
   - 离线统一账号 `admin/admin@123`
   - `root/admin@123` 回退登录
   - 静态管理地址 `172.32.2.20/24`
   - 实际 `SSH` 登录
   - `sudo` 安装与提权
   - 初始化后重启复验
   - 基础镜像固化后的新节点原生启动复验
7. 它当前必须明确记录的边界是：
   - 默认镜像仍是 `DHCP + kvm hostname + stale resolv.conf`
   - `dns-nameservers` 不会自动修复运行态 `/etc/resolv.conf`
   - Debian 10 `buster` 已 `EOL`，必须切到 `archive.debian.org`
   - 当前只实证了 `ethernet=1`，还不是多口服务器模板
8. 对它的具体创建与初始化步骤，统一参照：
   [EVE-NG Debian Server 标准操作手册](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-linux-debian-server-standard-operation.md)
9. `linux-Kylin-Server-V11-2503` 已完成第一轮标准初始化验证，可作为当前 Kylin 服务器标准镜像。
10. 它当前已经实测打通：
   - 离线统一账号 `admin/admin@123`
   - `root/admin@123` 回退登录
   - 静态管理地址 `172.32.2.21/24`
   - 实际 `SSH` 登录
   - `sudo` 提权
   - 初始化后重启复验
   - 基础镜像固化后的新节点原生启动复验
11. 它当前必须明确记录的边界是：
   - 默认镜像仍是 `DHCP + root locked`
   - 当前 `telnet` 串口还没有形成稳定可交互入口
   - 首次开机和重启后的网络恢复时间都偏慢
   - 当前只实证了 `ethernet=1`，还不是多口服务器模板
12. 对它的具体创建与初始化步骤，统一参照：
   [EVE-NG Kylin Server 标准操作手册](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-linux-kylin-server-standard-operation.md)
13. `linux-rhel-8.4` 已完成第一轮离线标准化与运行态排查，但当前不能作为已实证的 RHEL 服务器标准镜像。
14. 它当前已经确认的事实是：
   - 系统为 `Red Hat Enterprise Linux 8.4`
   - 默认网卡名是 `ens3`
   - 默认网络模型是 `DHCP`
   - 可离线统一为 `root/admin@123` 与 `admin/admin@123`
   - 可离线写入静态管理地址 `172.32.2.19/24`
15. 它当前必须明确记录的边界是：
   - 宿主机对 `172.32.2.19` 的 `ARP` 一直是 `incomplete`
   - `ICMP` 与 `22/tcp` 都未打通
   - 当前 `telnet` 控制台没有形成稳定可交互登录提示
   - 即使已补充 `multi-user.target`、`serial-getty@ttyS0` 与 `console=ttyS0`，问题依旧未收敛
   - 独立 `qemu` overlay probe 里，`hostfwd` 端口虽可连接，但 `SSH banner exchange` 仍超时
   - 裁剪桌面/宿主服务后，启动链虽然更干净，但 `SSH banner exchange` 依旧超时
   - 当前更强的运行态证据表明：`NetworkManager` 仍会自动激活旧的 `ens3` 连接 UUID，并把它拉成 `DHCP 192.168.1.54`
   - 即使把探针挂到 `NetworkManager` 启动点并做更强裁剪，当前也还没有形成稳定的 `nmcli` 运行态观测入口
16. 当前更适合把它视为“RHEL 服务器镜像适配专项”，而不是主线稳定模板。
17. 对它的具体证据与边界，统一参照：
   [EVE-NG Linux RHEL Server 首轮初始化与边界记录](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-linux-rhel-server-boundary-investigation.md)
18. 当前已经确认，本地 EVE 没有现成的 Rocky / Alma / 新版 RHEL 系服务器资源，因此新的 RHEL 兼容服务器主线需要单独引入。
19. 当前推荐优先引入：
   - `linux-rocky-9-genericcloud`
20. 选择原因：
   - 官方直接提供 `qcow2`
   - 与 EVE 导入链路最短
   - 更适合作为新的 RHEL 兼容服务器标准模板候选
21. 当前这条替代路线的共同入口，统一参照：
   [EVE-NG Rocky Linux Server 准备方案](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-linux-rocky-server-preparation-plan.md)

## 4. 第一批推荐组合

如果目标是尽快围绕真实设备跑出第一阶段结果，建议优先从下面三条开始。

### 4.1 防火墙优先组合

推荐顺序：

1. `bridge + huaweiusg6kv + pnet0`
2. `bridge + h3cvfw1k + pnet0`
3. `bridge + asav + pnet0`

原因：

1. 更贴近你当前关心的配置解析、策略生成、策略查询
2. 更容易在最小拓扑里观察 inside / outside / NAT / ACL 行为

### 4.2 路由器优先组合

推荐顺序：

1. `Cisco IOL Gateway + huaweiar1k`
2. `Cisco IOL Gateway + h3cvsr1k`

原因：

1. 适合尽快打接口、路由、邻居、采集、监控和自动化脚本
2. 适合先建立网络设备支持边界

### 4.3 服务器优先组合

推荐顺序：

1. `linux-ubuntu-server-20.04 + boundary + pnet0`
2. `linux-debian-10.3.0 + boundary + pnet0`
3. `linux-Kylin-Server-V11-2503 + boundary + pnet0`
4. `linux-rocky-9-genericcloud + boundary + pnet0`
5. `linux-rhel-8.4 + boundary + pnet0`

原因：

1. 适合尽快打 SSH 采集、监控任务和脚本执行
2. Debian 10 现在可以作为 Ubuntu 之外的第二条服务器实证线
3. Kylin 已经能承接国产服务器线的第一轮实证
4. Rocky 9 更适合作为新的 RHEL 兼容服务器主线候选
5. 旧 `linux-rhel-8.4` 只保留为专项边界排查对象

## 5. 第一批落地建议

如果按“先把共同骨架跑通，再逐步加设备家族”来推进，建议顺序如下：

1. `1 x Cisco IOL Gateway + 1 x huaweiar1k`
   用来先打通带外管理底座、接口、路由和监控基线
2. `1 x Cisco IOL Gateway + 1 x huaweiusg6kv`
   用来先打通防火墙配置解析、策略查询和策略生成基线
3. `1 x Cisco IOL Gateway + 1 x linux-ubuntu-server-20.04 + 1 x huaweiusg6kv`
   用来把服务器 SSH、脚本和监控接到同一套场景上

## 6. 使用方式

后续每新增一条设备变体场景，建议都同时记录下面三件事：

1. 用了哪一个镜像
2. 想验证哪条能力链
3. 当前验证通过点和明确失败边界

这样同一个 EVE 环境就会逐步形成一份“真实可执行设备覆盖地图”，而不是只停留在抽象支持列表。
