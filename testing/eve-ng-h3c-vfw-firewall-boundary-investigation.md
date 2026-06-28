# EVE-NG H3C VFW 防火墙边界排查记录

更新时间：2026-06-28  
适用环境：`192.168.100.20` 上的 EVE-NG Community `6.2.0-4`

## 1. 目的

这份文档不把 `h3cvfw1k-7.1.064` 直接写成“已实证标准模板”。

当前更重要的是把已经确认的事实、已排除的错误方向、以及还没有打通的边界写清楚，避免后续团队把它误当成已经稳定可复用的防火墙基线。

## 2. 当前结论

截至 2026-06-28，`h3cvfw1k-7.1.064` 在当前 EVE 环境中：

1. 已经确认可以正常启动。
2. 已经确认可以展开到 `ethernet=20`。
3. 已经确认接口可以配置 IP、ARP 可学习、SSH 服务可监听。
4. 已经进一步确认：设备自身控制面默认不会自动放通，必须显式命中 `Management <-> Local` 的域间放行策略。
5. 在补上最小 `zone-pair + packet-filter ACL` 放行后，`ICMP`、`TCP/22`、设备侧到网关的 `ping` 都已经实证打通。

更具体地说：

1. 防火墙接口能够响应 ARP。
2. 防火墙本地 `22/tcp` 处于 `LISTEN`。
3. 宿主机发往防火墙的 ICMP Echo Request 能到达设备所在链路。
4. 在未补放行策略前，设备不返回 ICMP Echo Reply，也没有形成可复验的 SSH 建连结果。
5. 在未补放行策略前，设备主动向管理网关发 `ping` 时，链路抓包看不到有效 ICMP 发出。
6. 在补上放行策略后，宿主机 `ping 172.32.2.17` 成功、`TCP/22` 探测成功、设备侧 `ping 172.32.2.254` 成功。

因此，这个镜像当前应标记为：

1. `镜像可启动`
2. `接口可挂线`
3. `管理面需要显式域间放行`
4. `控制面基础连通已实证打通`
5. `仍需继续沉淀标准初始化模板`

## 3. 本次排查对象

### 3.1 设备与镜像

1. EVE 模板：`h3cvfw1k`
2. 镜像：`h3cvfw1k-7.1.064`
3. 节点形态一：`H3C-FW1`
   - `ethernet=20`
   - `qemu_nic=e1000`
4. 节点形态二：`H3C-FW2`
   - `ethernet=20`
   - `qemu_nic=virtio-net-pci`

### 3.2 管理网络

1. 管理网关设备：Cisco IOL `GW-SW`
2. 管理网关地址：`172.32.2.254/24`
3. H3C-FW1 管理地址：`172.32.2.16/24`
4. H3C-FW2 管理地址：`172.32.2.17/24`

## 4. 已验证事实

### 4.1 接口与挂线

1. EVE API 已回读到 `20` 个接口。
2. 设备 CLI 已显示 `GE1/0` 到 `GE20/0`。
3. 管理网络曾分别挂到最后一个口与第一个口进行验证。
4. 网关交换机侧对应端口已确认在 `Vlan1` 中。

### 4.2 设备本地配置

本次已完成过以下配置验证：

1. 本地账号 `admin/admin@123`
2. `ssh server enable`
3. `line vty` 使用本地认证
4. `ssh user admin service-type stelnet authentication-type password`
5. `display ssh server status` 显示 `Stelnet server: Enable`
6. `display tcp` 显示 `0.0.0.0:22 LISTEN`

### 4.3 抓包与宿主机证据

宿主机侧抓包已经明确证明：

1. 防火墙会回复 ARP。
2. 宿主机发往防火墙 `22/tcp` 的 SYN 已真正到达链路。
3. 防火墙没有回 `SYN-ACK`，也没有回 RST。
4. 宿主机发往防火墙的 ICMP Echo Request 已真正到达链路。
5. 防火墙没有回 ICMP Echo Reply。
6. 防火墙本地发起 `ping` 时，没有观察到与期望相符的 ICMP 发包结果。

### 4.4 2026-06-28 复验新增证据

这轮复验把“设备有没有真正起机、管理口有没有真正挂上、控制面到底卡在哪一层”补得更完整了。

已新增确认：

1. H3C-FW2 控制台端口 `192.168.100.20:32775` 可直连，并已进入 `<H3C-FW2>` 提示符。
2. EVE 宿主机侧管理 TAP `vunl0_7_0` 在设备完整起机后进入 `LOWER_UP`。
3. `vnet0_7` 上已明确存在 `vunl0_1_33` 与 `vunl0_7_0`，说明管理 bridge 挂线真实存在。
4. H3C-FW2 当前实际有管理地址的接口是 `GE1/0`，不是 `GE20/0`。
5. `display ip routing-table` 已看到默认路由 `0.0.0.0/0 -> 172.32.2.254` 经 `GE1/0`。
6. `display arp` 已动态学习到 `172.32.2.254` 的 MAC，说明二层邻接已建立。
7. 从设备侧执行 `ping 172.32.2.254` 时，宿主机对 `vnet0_7` 抓包结果为 `0 packets captured`，说明设备没有把 ICMP Echo Request 真正发到链路上。
8. 从宿主机侧执行 `ping 172.32.2.17` 时，`vnet0_7` 抓包已看到 `172.32.2.1 -> 172.32.2.17` 的 ICMP Echo Request 到达，但设备没有回应 Echo Reply。
9. 已把 `Management` 安全域成员从错误的 `GE20/0` 修正为 `GE1/0`，问题依旧存在。
10. 已尝试在接口视图下追加 `manage ping` / `manage ssh` 类命令，但当前镜像直接返回 `Unrecognized command`。

### 4.5 2026-06-28 二次复验新增证据

这轮又补了四条更关键的事实，进一步缩小了根因范围：

1. `display security-zone` 已明确看到 `GigabitEthernet1/0` 就在 `Management` 安全域内。
2. `display license` 已明确看到：
   - `STANDARD` 试用许可存在
   - `Current State: In use`
   这说明当前不是“完全无许可”状态。
3. 再次按 H3C 官方常规防火墙资料尝试：
   - `manage ping inbound`
   - `manage ping outbound`
   - `manage ssh inbound`
   当前镜像依然全部返回 `Unrecognized command`。
4. 这说明 `vFW1000` 当前镜像的管理面命令模型并不能直接套用常见 H3C 防火墙手册。
5. 对 `GE1/0` 清空接口计数器后，再从设备侧执行 `ping 172.32.2.254`：
   - CLI 统计为 `5 packet(s) transmitted`
   - 但接口 `Output (total)` 只增加到 `1 packets, 60 bytes`
6. 这说明设备并没有把 `5` 个期望的 ICMP Echo Request 正常发到链路上。
7. 从宿主机侧再次探测 `TCP/22` 时，结果仍为 `TCP22_FAIL`。
8. 结合前后证据，当前问题已经进一步收敛到：
   - 不是安全域遗漏
   - 不是无许可
   - 也不是少打一条常见 `manage` 命令
   - 更像镜像在当前 EVE 虚拟化形态下没有形成正常的三层控制面收发闭环

这说明问题不在以下层面：

1. 不是 EVE 完全没连上。
2. 不是交换机侧端口没进 `Vlan1`。
3. 不是防火墙完全没学到 ARP。
4. 不是 SSH 服务根本没有监听。
5. 也不能再把“宿主机侧 TAP 初始 `NO-CARRIER`”当作根因，因为设备完整起机后该接口已变成 `LOWER_UP`。

### 4.6 2026-06-28 三次复验新增证据

这轮重点不再重复验证链路，而是专门核对“管理放行命令到底应该落在哪个配置入口”。

已新增确认：

1. 当前运行配置中，`Management` 安全域只看到：
   - `security-zone name Management`
   - `import interface GigabitEthernet1/0`
   没有看到显式的 `zone-pair` 或接口级 `manage ...` 配置。
2. 当前运行配置中与 SSH 直接相关的配置主要是：
   - `line vty 0 63`
   - `protocol inbound ssh`
   - `ssh server enable`
   - `ssh user admin service-type stelnet authentication-type password`
   - `local-user admin class manage`
3. 这里的 `protocol inbound ssh` 实际位于 `line vty 0 63` 视图，不是 `security-zone name Management` 视图。
4. 在当前 `vFW1000` 镜像的 `security-zone name Management` 视图下，命令帮助中并没有出现常见防火墙资料里的 `protocol inbound` / `protocol outbound`。
5. 在当前 `GigabitEthernet1/0` 三层接口视图下，命令帮助中同样没有出现常见资料里的 `manage { ping | ssh | http | https } { inbound | outbound }`。
6. 这说明：
   - “接口管理协议需要单独放行”这个方向本身是成立的
   - 但当前镜像暴露出来的实际 CLI 入口，与常见 H3C 防火墙通用资料并不一致
7. 因此，当前还不能简单把问题归因到“少打一条 `manage ping/manage ssh` 命令”，更准确的说法是：
   当前 `vFW1000` 镜像的管理面放行模型还没有被正确识别。

### 4.7 2026-06-28 四次复验新增证据

这轮不再停留在分析，而是直接按 `vFW` 的安全域模型做了最小放行验证。

已新增确认：

1. 通过控制台成功创建了 `ACL 2000`：
   - `acl basic 2000`
   - `rule 0 permit source any`
2. 通过控制台成功创建并回读到两条安全域对：
   - `zone-pair security source Management destination Local`
   - `zone-pair security source Local destination Management`
3. 两条 `zone-pair` 都成功绑定了 `packet-filter 2000`。
4. 配置完成后，宿主机对 `172.32.2.17` 的 `ping` 已成功，`3/3` 回包。
5. 配置完成后，宿主机对 `172.32.2.17:22` 的 `TCP` 探测已成功。
6. 配置完成后，设备侧执行 `ping 172.32.2.254` 已成功，`5/5` 回包。
7. 这说明此前卡住的核心原因并不是：
   - EVE 没连上
   - 镜像完全不兼容
   - SSH 服务没监听
8. 而是 `vFW` 对“目的地址或源地址为本机”的报文默认不自动放通，必须显式命中 `Management <-> Local` 的域间放行策略。
9. 这也说明当前最小可用管理面模型已经被实证找到：
   - 管理接口加入 `Management` 安全域
   - 创建 `Management -> Local` 与 `Local -> Management` 的 `zone-pair`
   - 通过 `packet-filter` 绑定允许管理流量的 ACL
10. 额外观察到的剩余现象是：
   - 首次 SSH 交互已进入密码变更流程
   - 这证明 SSH 认证链路已真正到达设备侧
   - 但也意味着后续标准模板还需要明确首次 SSH 密码策略与初始化流程

### 4.8 2026-06-28 五次复验新增证据

这轮重点验证“保存后是否还成立”，避免把一次性运行态结果误当成模板能力。

已新增确认：

1. 控制台执行 `save force` 已成功。
2. 节点已完成一次人工触发重启。
3. 重启完成后，宿主机 `ping 172.32.2.17` 仍成功。
4. 重启完成后，宿主机 `TCP/22` 探测仍成功。
5. 重启完成后，设备内 `display zone-pair security` 仍可看到：
   - `Local -> Management`
   - `Management -> Local`
6. 重启完成后，设备侧 `ping 172.32.2.254` 仍成功。
7. 这说明当前最小管理面模型不是一次性运行态偶然结果，而是已经具备基本持久化能力。

### 4.9 2026-06-28 六次复验新增证据

这轮重点验证“首次 SSH 强制改密”到底能不能被彻底消掉。

已新增确认：

1. 当前镜像的 `password-control` 命令树中，不支持：
   - `password-control change-password first-login`
   - `undo password-control change-password first-login enable`
2. 当前镜像支持：
   - `password-control update-interval 0`
   - `undo password-control update-interval`
3. 首次 SSH 交互已经实证可完成密码变更，改密到 `Admin@1234` 后，可正常登录并执行命令。
4. 在把 `update-interval` 调整为 `0` 后，再尝试把密码回设为 `admin@123`，配置写入成功。
5. 但下一次 SSH 使用 `admin@123` 登录时，仍然再次进入：
   - `First login or password reset`
6. 这说明：
   - 触发“首次改密”的根因并不只是最小改密间隔
   - `admin@123` 在这台设备上可以作为首登触发口令
   - 但不能作为稳定复用的 SSH 实验口令
7. 当前已经实证稳定可用的 SSH 口令例外值为：
   - 用户名：`admin`
   - 密码：`Admin@1234`

## 5. 已尝试但未打通的方向

### 5.1 不同网卡模型

均未解决：

1. `e1000`
2. `virtio-net-pci`

### 5.2 不同管理口位置

均未解决：

1. 最后一个口 `GE20/0`
2. 第一个口 `GE1/0`

### 5.3 不同路由实例方式

均未解决：

1. 接口绑定自建 `ip vpn-instance MGT`
2. 接口放到全局路由表

### 5.4 安全域相关尝试

已验证但未解决：

1. 将接口导入 `Management` 安全域
2. 显式创建 `Management -> Local`
3. 显式创建 `Local -> Management`
4. 在上述 `zone-pair` 上应用放宽 ACL
5. 把误绑的 `GE20/0` 修正为真实管理口 `GE1/0`

### 5.5 管理面协议放行命令

已验证但未解决：

1. 在 `GigabitEthernet1/0` 视图下尝试追加 `manage ping` / `manage ssh` 类命令
2. 当前镜像直接返回 `Unrecognized command`
3. 说明该镜像的管理面协议放行机制与已查到的 H3C 常规资料并不一致，至少不能直接按常见命令套路推进
4. 即使接口已经在 `Management` 安全域中，问题依旧存在

## 6. 当前最可靠的边界表述

目前最稳妥的结论不是“这台防火墙不支持”，而是：

1. 在当前 `192.168.100.20` 的 EVE 环境里，`h3cvfw1k-7.1.064` 还没有找到一条可重复、可文档化、可复验的管理面初始化路径。
2. 当前已确认此前问题的根因就在“设备自身控制面/管理面协议放行机制”，而不是二层挂线、ARP、路由或 SSH 监听缺失。
3. 当前还可进一步明确：
   - 不是 `Management` 安全域遗漏
   - 不是完全无许可
   - 也不是简单把常见 H3C 通用命令照抄进去就能解决
4. 当前更准确的结论应为：
   - 接口管理协议需要单独放行，这个方向是对的
   - `vFW1000` 当前可工作的最小模型不是 `manage ...`，而是 `Management <-> Local` 的 `zone-pair + packet-filter ACL`
   - 这条最小放行路径已经实证打通
5. 当前剩余边界已经收敛为：
   - `admin@123` 不能作为稳定复用 SSH 口令
   - 如果坚持统一实验口令，这台设备仍然存在例外
   - 还没有形成一份最终版、可批量复验的标准初始化模板
6. 这说明它已经不应再被定义为“纯镜像不通”，而应被定义为“已找到管理面放行模型，但模板化尚未完成”。

## 7. 对 OneOPS 测试推进的影响

这条边界不会阻断第一阶段整体测试推进，但会影响 H3C 防火墙这条子线的节奏：

1. 可以继续使用 Huawei USG 先承接防火墙配置采集、策略解析、策略查询、策略生成等流程测试。
2. 现在也可以把 H3C VFW 继续推进到“标准初始化模板补齐”这一步，而不必停留在纯边界排查阶段。
3. 在模板化完成前，H3C VFW 仍不建议直接混入主线稳定模板统计。

## 8. 后续建议

后续如果继续攻关 `h3cvfw1k-7.1.064`，建议按下面顺序推进：

1. 把这次已验证的最小管理面模型沉淀成标准配置片段：
   - `acl basic 2000`
   - `rule 0 permit source any`
   - `zone-pair security source Management destination Local`
   - `packet-filter 2000`
   - `zone-pair security source Local destination Management`
   - `packet-filter 2000`
2. 把当前稳定可用的 SSH 例外口令 `Admin@1234` 明确写入设备手册，并标记为与统一实验口令不一致的厂商边界。
3. 如果后续还要继续追求统一口令，再单独研究是否存在厂商隐藏开关或其它不触发首登改密的密码写入方式。
4. 基于当前已打通的管理面，继续验证配置采集、策略查询和其他防火墙能力链。
5. 在模板化完成前，继续保留：
   - 宿主机到设备的 `ICMP`
   - 宿主机到设备的 `TCP/22`
   - 设备到网关的 `ping`
   作为每轮复验的最小回归检查项。
