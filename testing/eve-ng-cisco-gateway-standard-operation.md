# EVE-NG Cisco 网关交换机标准操作手册

更新时间：2026-06-27  
适用环境：`192.168.100.20` 上的 EVE-NG Community `6.2.0-4`

## 1. 目的

这份手册用于把 OneOPS 第一阶段测试里的“网关设备基础环境准备”固化成可重复标准操作。

它回答的是下面这件事：

如何在 EVE 中稳定创建一台 Cisco 网关交换机，并把它初始化成后续所有业务网络设备都可以复用的管理底座。

## 2. 当前已验证可用的网关镜像

本次实际验证通过的网关镜像是：

1. `i86bi_LinuxL2-AdvEnterpriseK9-M_152_May_2018.bin`

本次已实证确认：

1. 镜像可以正常启动
2. 镜像支持 `ip vrf`
3. 镜像支持 `interface vlan1`
4. 镜像支持 SSH 登录
5. 镜像可按 `20` 个以太网接口规格创建

## 3. 创建规格

### 3.1 节点规格

创建网关交换机时使用以下节点规格：

1. 模板：`iol`
2. 镜像：`i86bi_LinuxL2-AdvEnterpriseK9-M_152_May_2018.bin`
3. `ethernet=5`
4. `serial=0`
5. `ram=1024`
6. `nvram=1024`

### 3.2 接口展开规则

当前 EVE 的 `iol` 模板中：

1. `1` 个 `ethernet` 模块等于 `4` 个接口
2. `ethernet=5` 就等于 `20` 个接口

本次实际回读到的接口列表为：

1. `e0/0 e0/1 e0/2 e0/3`
2. `e1/0 e1/1 e1/2 e1/3`
3. `e2/0 e2/1 e2/2 e2/3`
4. `e3/0 e3/1 e3/2 e3/3`
5. `e4/0 e4/1 e4/2 e4/3`

## 4. 接口角色标准

网关交换机固定按下面方式使用接口：

1. `e0/0`
   连接 `pnet0`
   作为外联管理上联口
2. 其余接口
   全部作为 `vlan 1` access 口
   供业务网络设备的带外管理接口接入

## 5. 标准基础配置

### 5.1 管理平面目标

网关设备初始化后，需要满足以下目标：

1. 具备独立的 `MGT VRF`
2. 上联口在 `MGT VRF`
3. `Vlan1` 在 `MGT VRF`
4. `Vlan1` 作为所有业务设备带外管理网关
5. 设备可以通过 SSH 登录

### 5.2 标准配置内容

本次验证通过的基础配置如下：

```ios
hostname GW-SW

ip vrf MGT
 rd 1:1

ip domain-name oneops.lab
username admin privilege 15 secret admin@123

crypto key generate rsa modulus 2048
ip ssh version 2

interface Ethernet0/0
 no switchport
 ip vrf forwarding MGT
 ip address 192.168.100.150 255.255.255.0
 no shutdown

interface Vlan1
 ip vrf forwarding MGT
 ip address 172.32.2.254 255.255.255.0
 no shutdown

interface range Ethernet0/1 - 3
 switchport mode access
 switchport access vlan 1
 no shutdown

interface range Ethernet1/0 - 3
 switchport mode access
 switchport access vlan 1
 no shutdown

interface range Ethernet2/0 - 3
 switchport mode access
 switchport access vlan 1
 no shutdown

interface range Ethernet3/0 - 3
 switchport mode access
 switchport access vlan 1
 no shutdown

interface range Ethernet4/0 - 3
 switchport mode access
 switchport access vlan 1
 no shutdown

ip route vrf MGT 0.0.0.0 0.0.0.0 192.168.100.254

line vty 0 4
 exec-timeout 30 0
 login local
 transport input ssh

service password-encryption
```

### 5.3 标准账号

实验环境统一使用：

1. 用户名：`admin`
2. 密码：`admin@123`

## 6. 标准操作顺序

建议每次都按下面顺序执行：

1. 新建独立 Lab
2. 新建 `pnet0` 网络
3. 创建 Cisco IOL 网关交换机
4. 把 `e0/0` 接到 `pnet0`
5. 启动设备
6. 通过控制台打入标准基础配置
7. 保存配置
8. 做登录和接口验证

## 7. 标准验证命令

初始化完成后，至少执行下面几组验证。

### 7.1 VRF 验证

```ios
show vrf
```

通过标准：

1. 存在 `MGT`
2. `Et0/0` 在 `MGT`
3. `Vl1` 在 `MGT`

### 7.2 接口验证

```ios
show ip interface brief
```

通过标准：

1. `Ethernet0/0` 地址为 `192.168.100.150`
2. `Vlan1` 地址为 `172.32.2.254`
3. 管理平面相关接口状态符合预期

### 7.3 SSH 验证

```ios
show ip ssh
```

通过标准：

1. `SSH Enabled - version 2.0`

### 7.4 路由验证

```ios
show running-config | include ip route vrf MGT
```

通过标准：

1. 存在到 `192.168.100.254` 的默认路由

## 8. 本次实际验证结果

本次已经完成以下实证：

1. 控制台成功进入特权模式
2. `MGT VRF` 创建成功
3. `Ethernet0/0` 成功配置到 `MGT VRF`
4. `Ethernet0/0` 成功配置 `192.168.100.150/24`
5. `Vlan1` 成功配置到 `MGT VRF`
6. `Vlan1` 成功配置 `172.32.2.254/24`
7. `SSH` 成功启用
8. `admin/admin@123` 成功登录

## 9. SSH 兼容性边界

这台老 IOS 镜像虽然已经可以正常启用 SSH，但仍有一个现实边界：

1. 设备支持的密钥交换算法比较旧
2. 现代 SSH 客户端直接登录时，可能报密钥交换不兼容

本次实际成功登录时，使用了兼容参数：

```bash
ssh \
  -o KexAlgorithms=+diffie-hellman-group14-sha1 \
  -o HostKeyAlgorithms=+ssh-rsa \
  -o PubkeyAcceptedAlgorithms=+ssh-rsa \
  admin@192.168.100.150
```

因此要明确区分：

1. 设备侧 SSH 服务和账号密码是正常的
2. 客户端若失败，可能是本地 SSH 默认算法过新

## 10. 对后续业务设备的要求

在这台网关交换机准备完成后，后续所有业务网络设备都应遵循：

1. 最后一个接口作为带外管理口
2. 该接口接入网关交换机的 `vlan 1`
3. 管理地址从 `172.32.2.0/24` 中分配
4. 默认网关指向 `172.32.2.254`

## 11. 清理要求

如果本次拓扑只是临时验证，则结束后固定执行：

1. 关闭网关交换机
2. 删除拓扑
3. 检查宿主机 `brctl show`
4. 检查宿主机 `bridge link`
5. 检查宿主机 `ip tuntap list`
6. 清除残留 `vunl...` 动态网卡

## 12. 推荐复用方式

后续每次需要新的实验拓扑时，都建议先复用这份手册把网关交换机打好，再开始挂业务设备。

这样可以把：

1. 外联管理平面
2. 带外管理平面
3. SSH 登录基线
4. 清理方法

全部固定下来，让后续测试只聚焦在业务网络设备本身。
