# EVE-NG H3C VFW 防火墙标准操作手册（草案）

更新时间：2026-06-28  
适用环境：`192.168.100.20` 上的 EVE-NG Community `6.2.0-4`

## 1. 目的

这份手册记录 H3C VFW 防火墙在当前 EVE 环境中已经实证打通的最小管理面模型。

它当前还不是最终版标准模板，但已经回答了最关键的问题：

1. 镜像是否真的能起
2. 管理接口是否真的能用
3. 为什么之前 `ping/ssh` 都不通
4. 需要补哪些最小配置才能让管理面闭环

## 2. 设备身份

1. 设备家族：H3C VFW Firewall
2. 设备角色：业务网络设备 / 防火墙
3. 厂商：H3C
4. 当前模板状态：`草案，基础管理已实证打通`

## 3. 适用镜像与节点规格

本次实测使用：

1. EVE 模板：`h3cvfw1k`
2. 镜像名称：`h3cvfw1k-7.1.064`
3. CPU：`1`
4. 内存：`2048`
5. 控制台：`telnet`
6. `ethernet` 参数：`20`
7. `qemu_nic`：`virtio-net-pci`

补充说明：

1. 本次也尝试过 `e1000`
2. 管理面真正打通的是 `virtio-net-pci + GE1/0` 这条路径

## 4. 接口展开与命名表

### 4.1 EVE API 侧可挂线接口

当前 `20` 口规格下，EVE API 可回读 `20` 个接口。

### 4.2 设备 CLI 侧实际接口

设备内实际接口为：

1. `GE1/0`
2. `GE2/0`
3. `...`
4. `GE20/0`

### 4.3 当前标准管理口

当前草案固定为：

1. 管理口：`GigabitEthernet1/0`
2. 管理地址：`172.32.2.17/24`
3. 管理网关：`172.32.2.254`
4. 管理安全域：`Management`

补充说明：

1. 这台设备当前不走“最后一个口作为管理口”的统一规则
2. 当前已实证可用的是第一个口 `GE1/0`

## 5. 关键模型结论

这台 H3C VFW 当前最重要的结论不是某条命令，而是它的管理面模型：

1. `ssh server enable` 不是充分条件
2. 接口有 IP、ARP 可学、默认路由存在，也不是充分条件
3. 对于“目的地址或源地址为本机”的流量，`vFW` 默认不会自动放通
4. 管理面必须显式命中 `Management <-> Local` 的域间放行策略

当前实证可用的最小模型是：

1. 管理接口加入 `Management` 安全域
2. 创建 `Management -> Local` 的 `zone-pair`
3. 创建 `Local -> Management` 的 `zone-pair`
4. 通过 `packet-filter` 绑定允许管理流量的 ACL

## 6. 标准初始化配置

下面是当前环境中已经实际打通的最小标准配置。

```text
screen-length disable
system-view
sysname H3C-FW2

interface GigabitEthernet1/0
 port link-mode route
 ip address 172.32.2.17 255.255.255.0
 quit

security-zone name Management
 import interface GigabitEthernet1/0
 quit

ip route-static 0.0.0.0 0 172.32.2.254

line vty 0 63
 authentication-mode scheme
 protocol inbound ssh
 quit

ssh server enable
ssh user admin service-type stelnet authentication-type password

local-user admin class manage
 service-type ssh terminal
 authorization-attribute user-role network-admin
 password simple admin@123
 quit

password-control enable
password-control length 9
undo password-control history
password-control update-interval 0

acl basic 2000
 rule 0 permit source any
 quit

zone-pair security source Management destination Local
 packet-filter 2000
 quit

zone-pair security source Local destination Management
 packet-filter 2000
 quit

save force
```

补充说明：

1. 上面这组配置可以把管理面打通
2. 但如果把本地用户直接固化为 `admin/admin@123`，首次 SSH 真实交互仍会进入强制改密流程
3. 当前已经实证可稳定复用的 SSH 口令，是在首次 SSH 改密后收敛到：
   - 用户名：`admin`
   - 密码：`Admin@1234`

## 7. 已实证结果

### 7.1 节点与接口

实测通过：

1. 镜像可正常启动
2. `ethernet=20` 可展开
3. CLI 中可见 `GE1/0` 到 `GE20/0`
4. 管理口 `GE1/0` 可稳定接入管理桥

### 7.2 管理平面

实测通过：

1. 管理地址 `172.32.2.17/24` 生效
2. 默认路由 `0.0.0.0/0 -> 172.32.2.254` 生效
3. `GE1/0` 已加入 `Management` 安全域
4. `Management -> Local` 与 `Local -> Management` 的 `zone-pair` 已创建
5. 两条 `zone-pair` 都已绑定 `packet-filter 2000`

### 7.3 连通性

实测通过：

1. 宿主机 `ping 172.32.2.17` 成功
2. 宿主机 `TCP/22` 探测成功
3. 设备侧 `ping 172.32.2.254` 成功

这说明：

1. 控制面基础连通已经打通
2. 之前卡住的根因就是本机管理流量未显式放行

### 7.4 持久化与重启复验

实测通过：

1. `save force` 已成功
2. 节点重启后，宿主机 `ping 172.32.2.17` 仍成功
3. 节点重启后，宿主机 `TCP/22` 探测仍成功
4. 节点重启后，`display zone-pair security` 仍可看到：
   - `Local -> Management`
   - `Management -> Local`
5. 节点重启后，设备侧 `ping 172.32.2.254` 仍成功

### 7.5 SSH 账号收敛结果

实测通过：

1. 首次 SSH 使用 `admin@123` 会进入强制改密流程
2. 完成首次改密后，把密码设置为 `Admin@1234`，可稳定 SSH 登录
3. 登录后再次进入系统不会重复触发首次改密

实测失败：

1. 即使把 `password-control update-interval` 调整为 `0`
2. 即使在完成首次改密后再把密码改回 `admin@123`
3. 下一次 SSH 仍然会再次进入 `First login or password reset`

这说明：

1. `admin@123` 在这台设备上可以作为“首登触发口令”
2. 但不能作为“稳定复用 SSH 口令”
3. 当前稳定可复用的实验口令例外值应为 `Admin@1234`

## 8. 关键验证命令

设备内：

```text
display ip interface brief
display ip routing-table
display security-zone name Management
display zone-pair security
display ssh server status
display tcp
```

宿主机侧：

```bash
ping -c 2 172.32.2.17
nc -vz -w 2 172.32.2.17 22
ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
  -o KexAlgorithms=diffie-hellman-group14-sha1,diffie-hellman-group-exchange-sha1 \
  -o Ciphers=aes128-cbc,aes256-cbc,3des-cbc \
  -o HostKeyAlgorithms=+ssh-rsa -o PubkeyAcceptedAlgorithms=+ssh-rsa \
  admin@172.32.2.17
```

## 9. 已知边界

这台设备当前必须明确记录下面几个边界：

1. 当前管理口不是最后一个口，而是 `GE1/0`
2. 当前 CLI 不支持通用资料里的：
   - `manage ping inbound`
   - `manage ssh inbound`
3. 当前可工作的最小模型是 `zone-pair + packet-filter ACL`，不是接口级 `manage ...`
4. `admin@123` 不能作为稳定复用 SSH 口令
5. 如果再次把密码回设为 `admin@123`，下一次 SSH 仍会再次进入强制改密
6. 当前稳定可复用的 SSH 口令例外值是 `Admin@1234`
7. 当前已经完成一次“保存后重启复验”
8. 当前还没有收敛成最终标准模板，只能算“草案已可用”

## 10. 当前标准结论

在当前 `192.168.100.20` 环境里，`h3cvfw1k-7.1.064` 已经不应再被视为“纯镜像不通”：

1. 基础管理面模型已经找到
2. `ICMP`、`TCP/22`、设备侧回 `ping` 已实证打通
3. 保存后重启复验已通过
4. 当前最值得继续推进的不是重新猜根因，而是：
   - 决定是否接受 `Admin@1234` 作为这台设备的实验口令例外
   - 把这份草案提升成正式标准模板
