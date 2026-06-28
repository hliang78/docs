# EVE-NG Huawei AR 路由器标准操作手册

更新时间：2026-06-27  
适用环境：`192.168.100.20` 上的 EVE-NG Community `6.2.0-4`

## 1. 目的

这份手册记录 Huawei AR 路由器在当前 EVE 环境中的实际初始化方式。

目标不是给出“理论上像是华为的命令”，而是把下面这些点真正落成一条可复用的标准路径：

1. 节点如何创建
2. 管理口到底映射到哪个真实接口
3. 首登创建账号有哪些额外行为
4. `MGT` 管理平面如何配置
5. SSH 为什么会“命令都配了但还是连不上”

## 2. 设备身份

1. 设备家族：Huawei AR Router
2. 设备角色：业务网络设备
3. 厂商：Huawei
4. 当前模板状态：`已实证`

## 3. 适用镜像与节点规格

本次实测使用：

1. EVE 模板：`huaweiar1k`
2. 镜像名称：`huaweiar1k-5.170-V300R022C00SPC100-Auto-update-esn`
3. CPU：`1`
4. 内存：`2048`
5. 控制台：`telnet`
6. `ethernet` 参数：`20`

## 4. 接口展开与命名表

### 4.1 EVE API 侧可挂线接口

在当前环境里，EVE API 回读出的可挂线接口为：

1. `G0/0/0`
2. `G0/0/1`
3. `G0/0/2`
4. `G0/0/3`
5. `G0/0/4`
6. `G0/0/5`
7. `G0/0/6`
8. `G0/0/7`
9. `G0/0/8`
10. `G0/0/9`
11. `G0/0/10`
12. `G0/0/11`
13. `G0/0/12`
14. `G0/0/13`
15. `G0/0/14`
16. `G0/0/15`
17. `G0/0/16`
18. `G0/0/17`
19. `G0/0/18`
20. `G0/0/19`

### 4.2 设备 CLI 侧实际接口显示

设备启动后，`display ip interface brief` 实际显示为：

1. `GigabitEthernet0/0/0` 到 `GigabitEthernet0/0/20`
2. `NULL0`

这意味着当前镜像存在一个重要边界：

1. EVE API 只暴露了 `20` 个可挂线口
2. 华为 CLI 却多显示了一个 `GigabitEthernet0/0/20`
3. 当前实测可确认接到 EVE 管理桥的是 `GigabitEthernet0/0/19`
4. `GigabitEthernet0/0/20` 当前不要作为标准管理口使用

### 4.3 当前标准管理口

当前统一固定为：

1. 管理口：`GigabitEthernet0/0/19`
2. 管理地址：`172.32.2.10/24`
3. 管理网关：`172.32.2.254`
4. 管理实例：`MGT`

## 5. 首登初始化过程

这台镜像的首登流程不能按“登录后直接开始配置”的思路处理，必须按下面顺序执行。

### 5.1 首次 Console 登录创建账号

首次进入串口后会出现：

```text
Login authentication
Warning: An initial username and password are required for the first login via the console.
New Username:
```

此时输入：

1. 用户名：`admin`
2. 密码：`admin@123`
3. 确认密码：`admin@123`

完成后设备会主动退出控制台：

```text
The account create success.
Info:Configuration console exit, please retry to log on
```

这一步是正常行为，不是失败。

### 5.2 第二次登录

必须重新登录一次：

```text
Username: admin
Password: admin@123
```

### 5.3 关闭 Auto-Config

第二次登录后设备会提示：

```text
Do you want to stop Auto-Config? [y/n]:
```

必须输入：

```text
y
```

否则 DHCP、路由、DNS、VTY 等配置可能被后续自动配置覆盖。

## 6. 标准初始化配置

下面是本次实际打通的最小标准配置。

```text
system-view
sysname AR1

ip vpn-instance MGT
 ipv4-family
 quit

aaa
 local-user admin privilege level 15
 local-user admin service-type terminal ssh
 quit

user-interface vty 0 4
 authentication-mode aaa
 protocol inbound ssh
 quit

ssh user admin authentication-type password
stelnet server enable
rsa local-key-pair create
 2048
ssh server permit interface GigabitEthernet 0/0/19

interface GigabitEthernet0/0/19
 ip binding vpn-instance MGT
 ip address 172.32.2.10 255.255.255.0
 quit

ip route-static vpn-instance MGT 0.0.0.0 0.0.0.0 172.32.2.254
save
```

## 7. 已实证结果

### 7.1 管理平面

实测通过：

1. `GigabitEthernet0/0/19` 绑定到 `MGT`
2. 管理地址 `172.32.2.10/24` 生效
3. `MGT` 默认路由已安装
4. `ping -vpn-instance MGT 172.32.2.254` 连续 `5/5` 成功

### 7.2 SSH

实测通过：

1. `display ssh server status` 显示 `Stelnet server : Enable`
2. `display ssh user-information` 中存在 `admin / password`
3. `display tcp status` 显示 `0.0.0.0:22` 处于 `Listening`
4. 从 EVE 宿主机临时接入同一管理桥后，`nc -vz 172.32.2.10 22` 成功
5. 从 EVE 宿主机实际 `ssh admin@172.32.2.10` 登录成功

### 7.3 关键验证命令

```text
display ip interface brief
display current-configuration | include sysname|ip vpn-instance MGT|GigabitEthernet0/0/19|ip route-static vpn-instance MGT|local-user admin|ssh user admin|stelnet server enable|ssh server permit interface|user-interface vty
display ssh server status
display ssh user-information
display tcp status | include 0.0.0.0:22
ping -vpn-instance MGT 172.32.2.254
```

## 8. 已知边界

这台镜像当前必须明确记录下面几个边界：

1. 首次创建本地账号后，串口会主动退出，必须重新登录一次。
2. 第二次登录后，必须先停止 `Auto-Config`，否则后续配置可能丢失。
3. `screen-length 0 temporary` 在 Console 场景下不可用，不要把它当成必备步骤。
4. EVE API 与设备 CLI 的接口数量不完全一致：
   - API 可挂线接口到 `G0/0/19`
   - CLI 多出一个 `GigabitEthernet0/0/20`
5. 仅执行 `stelnet server enable` 还不够，必须再执行：

```text
ssh server permit interface GigabitEthernet 0/0/19
```

否则 SSH 端口虽然显示已监听，但同网段 TCP 建连仍会卡住。

## 9. 当前标准结论

在当前 `192.168.100.20` 环境里，Huawei AR 路由器已经具备进入 OneOPS 第一阶段真实设备测试的初始化前提：

1. 管理口已确认
2. 管理实例已确认
3. SSH 初始化已确认
4. 账号标准已确认
5. 已知边界已明确

后续如果要把它接入 OneOPS 的采集、监控、接口/路由/邻居验证，可以直接以这份手册作为路由器类设备的标准起点。
