# EVE-NG H3C VSR 路由器标准操作手册

更新时间：2026-06-27  
适用环境：`192.168.100.20` 上的 EVE-NG Community `6.2.0-4`

## 1. 目的

这份手册记录 H3C VSR 路由器在当前 EVE 环境中的实际初始化方式。

这台设备的价值在于验证它能不能真正进入你的统一业务设备模型：

1. 是否支持 `20` 口规格
2. 最后一个口能不能作为标准管理口
3. `MGT` 管理实例是否可用
4. 统一账号 `admin/admin@123` 能不能真正落地
5. SSH 是否只是“服务打开”，还是能被实际客户端登录

## 2. 设备身份

1. 设备家族：H3C VSR Router
2. 设备角色：业务网络设备 / 路由器
3. 厂商：H3C
4. 当前模板状态：`已实证`

## 3. 适用镜像与节点规格

本次实测使用：

1. EVE 模板：`h3cvsr1k`
2. 镜像名称：`h3cvsr1k-7.1.064`
3. CPU：`1`
4. 内存：`2048`
5. 控制台：`telnet`
6. `ethernet` 参数：`20`
7. `qemu_nic`：`virtio-net-pci`

## 4. 接口展开与命名表

### 4.1 EVE API 侧可挂线接口

本次 `20` 口规格下，API 回读接口为：

1. `Gi1/0`
2. `Gi2/0`
3. `Gi3/0`
4. `Gi4/0`
5. `Gi5/0`
6. `Gi6/0`
7. `Gi7/0`
8. `Gi8/0`
9. `Gi9/0`
10. `Gi10/0`
11. `Gi11/0`
12. `Gi12/0`
13. `Gi13/0`
14. `Gi14/0`
15. `Gi15/0`
16. `Gi16/0`
17. `Gi17/0`
18. `Gi18/0`
19. `Gi19/0`
20. `Gi20/0`

### 4.2 设备 CLI 侧实际接口

设备内 `display ip interface brief` 回读为：

1. `GE1/0` 到 `GE20/0`

补充说明：

1. API 名称是 `Gi`
2. CLI 名称是 `GE` 或 `GigabitEthernet`
3. 当前最后一个接口在两侧都能稳定对应到 `20/0`

### 4.3 当前标准管理口

当前统一固定为：

1. 管理口：`GigabitEthernet20/0`
2. 管理地址：`172.32.2.15/24`
3. 管理网关：`172.32.2.254`
4. 管理实例：`MGT`

## 5. 首登行为

### 5.1 默认 Console 行为

首次进入串口时会看到：

```text
Line aux0 is available.
Press ENTER to get started.
```

按回车后直接进入：

```text
<H3C>
```

这台镜像当前没有像华为 AR 那样的“首登必须先创建账号”流程。

### 5.2 初始 SSH 状态

初始状态下执行：

```text
display ssh server status
```

返回：

```text
SSH is not configured.
```

因此 SSH 必须显式初始化，不能假定镜像默认可用。

## 6. 标准初始化配置

下面是当前环境中已经实际打通的最小标准配置。

```text
screen-length disable
system-view
sysname H3C-R1

ip vpn-instance MGT

interface GigabitEthernet20/0
 ip binding vpn-instance MGT
 ip address 172.32.2.15 255.255.255.0
 quit

ip route-static vpn-instance MGT 0.0.0.0 0 172.32.2.254

password-control enable
password-control length 9
undo password-control history enable
undo password-control complexity user-name check
undo password-control change-password first-login enable

local-user admin class manage
 password simple admin@123
 service-type ssh terminal
 authorization-attribute user-role network-admin
 quit

ssh server enable
public-key local create rsa
 2048

line vty 0 63
 authentication-mode scheme
 protocol inbound ssh
 quit

save force
```

## 7. 已实证结果

### 7.1 20 口与管理口模型

实测通过：

1. `ethernet=20` 规格可正常启动
2. CLI 中 `GE1/0` 到 `GE20/0` 全部出现
3. 最后一个口 `GE20/0` 可稳定接入管理桥

### 7.2 管理平面

实测通过：

1. `GigabitEthernet20/0` 已绑定到 `MGT`
2. 管理地址 `172.32.2.15/24` 生效
3. `display ip routing-table vpn-instance MGT` 中可见：
   - 直连网段 `172.32.2.0/24`
   - 默认路由 `0.0.0.0/0 -> 172.32.2.254`
4. 从 EVE 宿主机接入同一管理桥后，`ping -c 2 172.32.2.15` 成功

### 7.3 SSH

实测通过：

1. `display ssh server status` 显示：

```text
Stelnet server: Enable
SSH version : 2.0
```

2. 从 EVE 宿主机实际 `ssh admin@172.32.2.15` 登录成功
3. 登录后可正常回读：

```text
display ip interface brief
display ip routing-table vpn-instance MGT
```

### 7.4 统一账号

这台设备最终已经实现统一实验账号：

1. 用户名：`admin`
2. 密码：`admin@123`

但它不是“默认天然接受”这套口令，而是依赖第 6 节里的密码策略放宽配置。

## 8. 关键验证命令

设备内：

```text
display version | include uptime|Software|Version
display ip interface brief
display current-configuration interface GigabitEthernet20/0
display ip routing-table vpn-instance MGT
display ssh server status
display current-configuration | include password-control
```

宿主机侧：

```text
ping -c 2 172.32.2.15
ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o HostKeyAlgorithms=+ssh-rsa -o PubkeyAcceptedAlgorithms=+ssh-rsa admin@172.32.2.15
```

## 9. 已知边界

这台设备当前必须明确记录下面几个边界：

1. `ip vpn-instance MGT` 在这台 Comware 设备上不进入华为 AR 那种 `ipv4-family` 子视图，不要套用华为命令结构。
2. 默认密码控制会拦住 `admin/admin@123`：
   - 长度至少 `10`
   - 口令不能包含用户名
   - 首次 SSH 登录强制改密
3. 如果要保留统一实验口令，必须显式执行：
   - `password-control length 9`
   - `undo password-control complexity user-name check`
   - `undo password-control change-password first-login enable`
4. 当前 SSH 只提供 `ssh-rsa` host key，现代客户端默认会报：

```text
no matching host key type found. Their offer: ssh-rsa
```

5. 因此客户端侧需要兼容参数：

```text
ssh -o HostKeyAlgorithms=+ssh-rsa -o PubkeyAcceptedAlgorithms=+ssh-rsa admin@172.32.2.15
```

## 10. 当前标准结论

在当前 `192.168.100.20` 环境里，`h3cvsr1k-7.1.064` 已经具备进入 OneOPS 第一阶段真实设备测试的初始化前提：

1. `20` 口规格已实证可用
2. 最后一个口做管理口的共同规则在这台设备上成立
3. `MGT` 管理实例和默认路由已实证可用
4. SSH 已完成真实登录验证
5. 统一账号 `admin/admin@123` 可以实现，但必须附带明确的密码策略放宽步骤
