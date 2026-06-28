# EVE-NG Huawei USG 防火墙标准操作手册

更新时间：2026-06-28  
适用环境：`192.168.100.20` 上的 EVE-NG Community `6.2.0-4`

## 1. 目的

这份手册记录 Huawei USG 防火墙在当前 EVE 环境中的实际初始化方式。

这台设备的价值不只是“能不能登录”，而是要把下面这些关键点真实落证据：

1. 首登默认账号和强制改密行为
2. 专用管理口与业务口的真实接口命名
3. `MGT` 管理实例是否可用
4. `SSH/HTTPS` 管理服务如何真正放通
5. 在当前 EVE 上，`20` 口扩展是否会破坏管理数据面

## 2. 设备身份

1. 设备家族：Huawei USG Firewall
2. 设备角色：业务网络设备 / 防火墙
3. 厂商：Huawei
4. 当前模板状态：`已实证`

## 3. 适用镜像与节点规格

### 3.1 当前可用标准规格

本次最终实测打通的规格为：

1. EVE 模板：`huaweiusg6kv`
2. 镜像名称：`huaweiusg6kv-V500R005C10SPC300`
3. CPU：`2`
4. 内存：`4096`
5. 控制台：`telnet`
6. `ethernet` 参数：`6`
7. `qemu_nic`：`virtio-net-pci`

### 3.2 当前不可作为标准规格的组合

本次实测失败的组合为：

1. `ethernet=20 + qemu_nic=virtio-net-pci`
2. `ethernet=20 + qemu_nic=e1000`

失败表现不是“配置命令不可写”，而是更关键的管理数据面异常：

1. 接口在 CLI 中可见
2. 接口 `up/up`
3. 管理口配置可写
4. 但宿主机抓包持续只看到 ARP 请求，看不到 USG 对 ARP 的有效回复
5. 管理口 `ping`、`22/tcp`、`443/tcp` 无法真正建立

因此当前环境下，Huawei USG 不能按“统一扩成 20 口”的标准直接进入稳定测试。

## 4. 接口展开与命名表

### 4.1 当前 `6` 口规格的 EVE API 接口

当前 API 回读接口为：

1. `G0/0/0 / MGMT`
2. `G1/0/0`
3. `G1/0/1`
4. `G1/0/2`
5. `G1/0/3`
6. `G1/0/4`

### 4.2 当前标准管理口

在当前环境里，标准管理口固定为：

1. 管理口：`GigabitEthernet0/0/0`
2. 接口别名：`GE0/METH`
3. 管理地址：`172.32.2.13/24`
4. 管理网关：`172.32.2.254`
5. 管理实例：`MGT`

### 4.3 与统一“最后一个口做管理口”规则的关系

这台设备当前必须作为明确例外记录：

1. 它有专用管理口 `G0/0/0 / MGMT`
2. 在当前 `6` 口规格下，这个专用管理口已经实测可用
3. 在当前 `20` 口扩展尝试里，专用管理口与最后一个业务口都没有打通稳定管理数据面
4. 因此当前阶段应优先采用专用管理口，而不是强行套用“最后一个口做管理口”

## 5. 首登初始化过程

### 5.1 默认账号

这台镜像不是“首次创建本地账号”的模型，而是内置默认账号：

1. 用户名：`admin`
2. 初始密码：`Admin@123`

### 5.2 首次登录强制改密

首次通过 Console 登录后会出现：

```text
The password needs to be changed. Change now? [Y/N]:
```

应按下面顺序修改为实验统一口令：

1. 输入 `Y`
2. 旧密码：`Admin@123`
3. 新密码：`admin@123`
4. 确认密码：`admin@123`

修改成功后进入用户视图：

```text
<USG6000V2>
```

## 6. 标准初始化配置

下面是当前环境下已经实际打通的最小标准配置。

```text
screen-length 0 temporary

system-view
ip vpn-instance MGT
 ipv4-family
 quit
 quit

interface GigabitEthernet0/0/0
 ip binding vpn-instance MGT
 ip address 172.32.2.13 255.255.255.0
 service-manage enable
 service-manage https permit
 service-manage ping permit
 service-manage ssh permit
 quit

aaa
 manager-user admin
  service-type ssh terminal web
  state active
 quit
 quit

ssh user admin
ssh user admin authentication-type password
ssh user admin service-type stelnet
stelnet server enable

ip route-static vpn-instance MGT 0.0.0.0 0.0.0.0 172.32.2.254
sysname USG1
save
```

## 7. 已实证结果

### 7.1 管理平面

实测通过：

1. `GigabitEthernet0/0/0` 已绑定到 `MGT`
2. 管理地址 `172.32.2.13/24` 生效
3. `MGT` 默认路由已写入配置
4. 宿主机从同一管理桥访问时，ARP 已可正常学习

补充说明：

1. `ping -vpn-instance MGT 172.32.2.254` 在设备侧仍未稳定成功
2. 但宿主机对 `172.32.2.13` 的 `ICMP` 与 `22/tcp` 已实际打通
3. 这说明当前可用结论应以“外部管理面可访问”作为主证据，而不能单独依赖设备内发 `ping`

### 7.2 SSH

实测通过：

1. `display ssh server status` 显示 `STELNET IPv4 server : Enable`
2. `display ssh user-information` 中存在 `admin`
3. 宿主机 `nc -vz 172.32.2.13 22` 成功
4. 宿主机实际 `ssh admin@172.32.2.13` 登录成功
5. 通过 SSH 回读了：

```text
display current-configuration interface GigabitEthernet0/0/0
```

补充结果：

1. 节点重启后，宿主机再次探测 `22/tcp` 仍可建立连接。
2. 重启后通过 SSH 实际回读确认，下面这些配置仍然存在：
   - `ip binding vpn-instance MGT`
   - `ip address 172.32.2.13 255.255.255.0`
   - `service-manage ssh permit`
   - `manager-user admin`
   - `ssh user admin`
   - `stelnet server enable`
   - `ip route-static vpn-instance MGT 0.0.0.0 0.0.0.0 172.32.2.254`
3. 这说明当前这台 USG 的标准管理配置至少已经具备“重启后可复用”的持久化能力。

### 7.3 HTTPS

当前实测结果应分开看：

1. `service-manage https permit`
2. `display current-configuration | include web-manager` 已确认存在：
   - `web-manager enable`
   - `web-manager security enable`
   - `web-manager security version tlsv1.1 tlsv1.2`
3. 宿主机对 `80/tcp` 已实测连通，`curl -I http://172.32.2.13/` 返回 `404 Not Found`。
4. 宿主机对 `443/tcp` 仍实测超时，`curl -kI https://172.32.2.13/` 无法建立连接。

因此当前共享结论应固定为：

1. Web 管理配置在设备侧确实存在。
2. `HTTP` 管理面当前已可访问。
3. `HTTPS 443` 当前仍未形成可复验的外部访问结果。
4. 后续如果要走 Web 场景，应优先把“为什么 `web-manager enable + https permit` 仍未监听 `443`”单列成专项边界，而不要假设 HTTPS 已经打通。

### 7.4 重启后复验

本轮又对现成 `USG1` 节点做了一次“宿主机启动节点后重验”的复测，结论如下：

1. 节点可通过 `unl_wrapper -a start` 正常拉起。
2. 管理口 `vunl0_3_0` 重新挂回原管理桥。
3. 启动完成后，`22/tcp` 可恢复访问，SSH 可再次登录。
4. `GigabitEthernet0/0/0`、`MGT`、默认路由与 `manager-user admin` 配置都仍在。
5. `HTTP` 管理面恢复正常。
6. `HTTPS 443` 仍未恢复可访问。

## 8. 关键验证命令

```text
display ip interface brief
display current-configuration interface GigabitEthernet0/0/0
display ssh server status
display ssh user-information
display current-configuration | include sysname|ip vpn-instance MGT|manager-user admin|ssh user admin|stelnet server enable|service-manage ssh permit|ip route-static vpn-instance MGT|web-manager|service-manage http permit|service-manage https permit
```

宿主机侧关键验证：

```text
nc -vz 172.32.2.13 22
ssh -o KexAlgorithms=+diffie-hellman-group14-sha1 admin@172.32.2.13
curl -I http://172.32.2.13/
curl -kI https://172.32.2.13/
```

## 9. 已知边界

这台设备当前必须明确记录下面几个边界：

1. 默认首次登录账号不是 `admin/admin@123`，而是 `admin/Admin@123`，并且首登强制改密。
2. SSH 本地用户模型不是 AR 路由器那套 `local-user`，而是：

```text
aaa
 manager-user admin
```

3. 仅配置 `ssh user admin` 不足以完成 SSH 登录，必须同时让 `manager-user admin` 具备 `ssh terminal web` 等服务类型。
4. SSH 客户端需要兼容旧算法：

```text
ssh -o KexAlgorithms=+diffie-hellman-group14-sha1 admin@172.32.2.13
```

5. 当前环境下，`20` 口扩展不可直接作为标准：
   - `ethernet=20 + virtio-net-pci` 时，接口可见但管理面 ARP/SSH/HTTPS 不稳定
   - `ethernet=20 + e1000` 时启动阶段还出现 `No port available , system will restart.`
6. 当前已经实证可用的规格是：
   - `ethernet=6`
   - `qemu_nic=virtio-net-pci`
   - 专用管理口 `G0/0/0 / MGMT`
7. 当前不能把“配置里存在 `web-manager enable` 且接口放通了 `https`”直接等同于“`443/tcp` 已打通”。
8. 当前更准确的 Web 管理面口径是：
   - `HTTP 80` 已实测可访问
   - `HTTPS 443` 仍未形成稳定外部连通证据

## 10. 当前标准结论

在当前 `192.168.100.20` 环境里，Huawei USG 防火墙已经具备进入 OneOPS 第一阶段真实设备测试的初始化前提，但必须带着明确边界使用：

1. 当前可用标准是 `6` 口规格，不是 `20` 口规格
2. 当前标准管理口是专用 `MGMT` 口，不是最后一个业务口
3. SSH 与管理配置已经打通，且重启后仍可复用，可作为后续配置采集、策略解析、策略查询、对象/NAT 测试的起点
4. 当前 Web 管理面应按“`HTTP` 可用、`HTTPS 443` 待专项排查”处理
5. 如果后续一定要满足“20 口统一规格”，这台镜像在当前 EVE 上需要单独继续做兼容性攻关，不能直接视为已满足

如果后续要继续推进这台设备的防火墙主线能力，请直接接着阅读：

1. [EVE-NG Huawei USG 策略与 NAT 实机验证记录](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-huawei-usg-policy-nat-live-validation.md)
2. [EVE-NG Huawei USG 防火墙标准模板](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-huawei-usg-firewall-standard-template.md)
