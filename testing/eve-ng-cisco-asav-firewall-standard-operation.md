# EVE-NG Cisco ASAv 防火墙标准操作手册

更新时间：2026-06-28  
适用环境：`192.168.100.20` 上的 EVE-NG Community `6.2.0-4`

## 1. 目的

这份手册记录 Cisco ASAv 在当前 EVE 环境里已经真实打通的初始化路径。

它的重点不是证明“镜像能启动”，而是把下面几件事固定成可复用操作：

1. `Mgmt0/0` 管理口如何真正打通
2. 为什么必须走一次恢复启动
3. 本地管理员和 `enable` 怎样进入稳定状态
4. SSH 怎样真实登录
5. 正常启动后如何完成持久化复验

## 2. 设备身份

1. 设备家族：Cisco ASAv Firewall
2. 设备角色：业务网络设备 / 防火墙
3. 厂商：Cisco
4. 当前模板状态：`已实证`

## 3. 适用镜像与节点规格

本次实测使用：

1. EVE 模板：`asav`
2. 镜像名称：`asav-9.22.1.1-PLR-Licensed`
3. CPU：`1`
4. 内存：`2048`
5. 控制台：`telnet`
6. `ethernet` 参数：`8`

## 4. 接口展开与命名表

### 4.1 EVE API 侧接口

当前 API 回读接口为：

1. `Mgmt0/0`
2. `Gi0/0`
3. `Gi0/1`
4. `Gi0/2`
5. `Gi0/3`
6. `Gi0/4`
7. `Gi0/5`
8. `Gi0/6`

### 4.2 当前标准管理口

在当前环境里，标准管理口固定为：

1. 管理口：`Management0/0`
2. 管理地址：`172.32.2.18/24`
3. 管理网关：`172.32.2.254`
4. 管理面：`management`

### 4.3 与统一“最后一个口做管理口”规则的关系

这台设备必须作为明确例外记录：

1. 它自带专用管理口 `Mgmt0/0`
2. 当前第一阶段标准应优先使用专用管理口
3. 不继续把“最后一个业务口做管理口”的统一规则套到 ASAv 上

## 5. 首启与恢复启动路径

### 5.1 首次启动行为

首次启动后会出现一次自动重启：

1. `ASAv clone detected, reboot required`

因此新建节点后，不能把第一次启动过程误判成异常。

### 5.2 为什么必须走恢复启动

当前环境下，正常启动后的控制台只会自动进入：

1. `User enable_1 logged in to ciscoasa`
2. `priv 1`

这不足以形成可重复的初始化闭环。

当前已经实证可用的正确路径是：

1. 先正常首启一次，生成节点 overlay
2. 停机
3. 修改 overlay 里的 `/grub.conf`
4. 把第一启动项切到 `with no configuration load`
5. 再启动节点，从恢复模式完成初始化

### 5.3 当前恢复启动的关键点

本次已经确认：

1. 需要修改的是节点 overlay 里的 `/grub.conf`
2. 不是只改基础镜像目录
3. 初始化完成后，要把 `/grub.conf` 再改回正常启动项

## 6. 标准初始化步骤

### 6.1 Console 阶段临时口令

由于 `admin@123` 会被 ASA 密码策略拒绝，当前标准流程必须先使用合规临时口令。

本次实测可用示例：

1. 临时 Console 口令：`Adm1n@132`

### 6.2 Console 阶段最小标准配置

下面这组命令已经在恢复启动状态下实测通过：

```text
terminal pager 0

conf t
hostname ASA1

interface management0/0
 management-only
 nameif management
 security-level 100
 ip address 172.32.2.18 255.255.255.0
 no shutdown

route management 0.0.0.0 0.0.0.0 172.32.2.254 1

username admin password Adm1n@132 privilege 15
aaa authentication ssh console LOCAL
ssh 0.0.0.0 0.0.0.0 management
enable password Adm1n@132

end
write memory
```

### 6.3 首次 SSH 改密

Console 里重置本地用户后，首次 SSH 登录会出现：

```text
Your password was reset by the administrator.
Please change your password before proceeding.
```

当前标准做法是：

1. 用临时口令 `Adm1n@132` 发起首次 SSH 登录
2. 按提示把用户口令改成最终稳定口令
3. 本次实测最终稳定口令示例：`Adm1n@134`
4. 登录后再把 `enable password` 同步到同一个最终稳定口令
5. 再次 `write memory`

可执行示例：

```text
conf t
enable password Adm1n@134
end
write memory
```

### 6.4 切回正常启动并复验

初始化完成后，应执行：

1. 停机
2. 把 overlay `/grub.conf` 恢复为正常第一启动项
3. 正常启动节点
4. 做宿主机 `ping`、SSH、`enable`、接口状态复验

## 7. 已实证结果

### 7.1 管理平面

实测通过：

1. `Management0/0` 地址 `172.32.2.18/24` 生效
2. `show running-config route` 可见：
   - `route management 0.0.0.0 0.0.0.0 172.32.2.254 1`
3. 从宿主机 `ping 172.32.2.18` 成功
4. 设备侧 `ping management 172.32.2.254` 成功

### 7.2 SSH

实测通过：

1. 宿主机以 `admin` 成功 SSH 登录
2. SSH 登录后可以 `enable`
3. `show curpriv` 已回读：
   - `Username : enable_15`
   - `Current privilege level : 15`
4. `show interface ip brief` 已回读：
   - `Management0/0 172.32.2.18 up/up`

### 7.3 重启后复验

当前已经完成正常启动后的复验：

1. 节点切回正常 GRUB 后可正常启动
2. SSH 可再次登录
3. `enable` 可再次进入 `priv 15`
4. `Management0/0` 地址、管理路由和本地用户配置均仍存在

## 8. 关键验证命令

设备内：

```text
show curpriv
show interface ip brief
show running-config interface management0/0
show running-config route
show running-config username
show running-config aaa
show running-config ssh
```

宿主机侧：

```text
ping -c 2 172.32.2.18
ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o HostKeyAlgorithms=+ssh-rsa -o PubkeyAuthentication=no admin@172.32.2.18
```

## 9. 已知边界

这台设备当前必须明确记录下面几个边界：

1. 首次启动会自动 clone reboot 一次。
2. 当前标准初始化依赖一次 `GRUB -> with no configuration load` 恢复启动。
3. EVE 删除节点后，`tmp` 覆盖目录不一定自动清理；如果要重做首次启动验证，必须手工确认已清空。
4. `admin@123` 会因为连续字符策略被拒绝，不能作为当前标准实验口令。
5. `password-policy` 当前可见命令里，没有直接放开“连续 ASCII 序列”限制的选项。
6. Console 重置本地用户密码后，首次 SSH 登录必须再改密一次。
7. SSH 客户端需要兼容 `ssh-rsa` host key。
8. 当前许可状态仍是 `Unlicensed`，后续做更深性能和高级特性验证时要单列风险。

## 10. 当前标准结论

在当前 `192.168.100.20` 环境里，Cisco ASAv 已经具备进入 OneOPS 第一阶段真实设备测试的初始化前提，但必须带着明确前置使用：

1. 当前标准管理口是专用 `Mgmt0/0`
2. 当前标准路径依赖一次恢复启动，而不是普通首启直接配
3. SSH 和 `enable` 已完成真实登录验证，且正常重启后仍可复用
4. 统一实验口令 `admin/admin@123` 在这台设备上不成立，必须单列密码策略例外
5. 这台设备现在已经可以进入后续的 Cisco 防火墙配置采集、策略查询、ACL/NAT 样本和自动化脚本测试
