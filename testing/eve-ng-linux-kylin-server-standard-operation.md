# EVE-NG Kylin Server 标准操作手册

更新时间：2026-06-28  
适用环境：`192.168.100.20` 上的 EVE-NG Community `6.2.0-4`

## 1. 目的

这份手册记录 `linux-Kylin-Server-V11-2503` 在当前 EVE 环境中的实际标准化路径。

目标是把下面几件事收敛成可复用模板：

1. 统一账号 `admin/admin@123`
2. 固定带外管理地址
3. SSH 登录可用
4. `sudo` 提权可用
5. 重启后仍然保持成立
6. 明确串口控制台当前边界

## 2. 设备身份

1. 设备家族：Kylin Server
2. 设备角色：业务网络设备 / 服务器
3. 厂商：Kylin
4. 当前模板状态：`已实证`

## 3. 适用镜像与节点规格

本次实测使用：

1. EVE 模板：`linux`
2. 镜像名称：`linux-Kylin-Server-V11-2503`
3. CPU：`1`
4. 内存：`2048`
5. 控制台：`telnet`
6. `ethernet` 参数：`1`
7. `qemu_nic`：`virtio-net-pci`

补充说明：

1. 当前阶段只验证了 `1` 口规格。
2. 当前不把它定义成“20 口服务器模板”。

## 4. 接口展开与命名表

### 4.1 EVE API 侧可挂线接口

当前 API 回读接口为：

1. `e0`

### 4.2 设备 CLI 侧实际接口

设备内实际网卡名为：

1. `ens3`

### 4.3 当前标准管理口

当前统一固定为：

1. 管理口：`ens3`
2. 管理地址：`172.32.2.21/24`
3. 管理网关：`172.32.2.254`
4. 主机名：`KYL1`

## 5. 默认状态与标准化要点

### 5.1 默认镜像的实际状态

本次离线检查确认：

1. 系统为 `Kylin Linux Advanced Server V11 (Swan25)`
2. 默认网络配置文件为 `/etc/sysconfig/network-scripts/ifcfg-ens3`
3. 默认网络模型为：

```text
BOOTPROTO=dhcp
DEVICE=ens3
ONBOOT=yes
```

4. 默认 `root` 为锁定状态
5. 默认镜像已安装 `sudo`
6. `sshd_config` 当前已明确允许：
   - `PermitRootLogin yes`
   - `PasswordAuthentication yes`

这说明它比当前 RHEL 8.4 模板更接近可直接标准化的状态。

### 5.2 已完成的离线标准化

本次对基础镜像已完成：

1. `root` 口令统一为 `admin@123`
2. 新增 `admin`
3. `admin` 口令统一为 `admin@123`
4. `admin` 加入 `wheel`
5. 主机名改为 `KYL1`
6. `/etc/hosts` 写入：

```text
127.0.0.1 localhost
127.0.1.1 KYL1
```

7. `/etc/sysconfig/network-scripts/ifcfg-ens3` 改为静态管理地址：

```text
TYPE=Ethernet
PROXY_METHOD=none
BROWSER_ONLY=no
BOOTPROTO=none
DEFROUTE=yes
IPV4_FAILURE_FATAL=no
IPV6INIT=yes
IPV6_AUTOCONF=yes
IPV6_DEFROUTE=yes
IPV6_FAILURE_FATAL=no
IPV6_ADDR_GEN_MODE=eui64
NAME=ens3
DEVICE=ens3
ONBOOT=yes
IPADDR=172.32.2.21
PREFIX=24
GATEWAY=172.32.2.254
DNS1=172.32.2.254
DNS2=8.8.8.8
```

## 6. 标准初始化步骤

下面这组内容已经固化进基础镜像；这里保留为“标准镜像应具备的落盘内容”：

```text
virt-customize -a /opt/unetlab/addons/qemu/linux-Kylin-Server-V11-2503/virtioa.qcow2 \
  --root-password password:admin@123 \
  --run-command 'id -u admin >/dev/null 2>&1 || useradd -m -s /bin/bash admin' \
  --password admin:password:admin@123 \
  --run-command 'usermod -aG wheel admin'

guestfish --rw -a /opt/unetlab/addons/qemu/linux-Kylin-Server-V11-2503/virtioa.qcow2 -i <<'EOF'
write /etc/hostname "KYL1\n"
write /etc/hosts "127.0.0.1 localhost\n127.0.1.1 KYL1\n\n::1 localhost ip6-localhost ip6-loopback\nff02::1 ip6-allnodes\nff02::2 ip6-allrouters\n"
write /etc/sysconfig/network-scripts/ifcfg-ens3 "TYPE=Ethernet\nPROXY_METHOD=none\nBROWSER_ONLY=no\nBOOTPROTO=none\nDEFROUTE=yes\nIPV4_FAILURE_FATAL=no\nIPV6INIT=yes\nIPV6_AUTOCONF=yes\nIPV6_DEFROUTE=yes\nIPV6_FAILURE_FATAL=no\nIPV6_ADDR_GEN_MODE=eui64\nNAME=ens3\nDEVICE=ens3\nONBOOT=yes\nIPADDR=172.32.2.21\nPREFIX=24\nGATEWAY=172.32.2.254\nDNS1=172.32.2.254\nDNS2=8.8.8.8\n"
EOF
```

## 7. 已实证结果

### 7.1 登录与权限

实测通过：

1. `root/admin@123` SSH 登录成功
2. `admin/admin@123` SSH 登录成功
3. `id` 回读为 `admin` 已加入 `wheel`
4. `printf 'admin@123\n' | sudo -S whoami` 返回 `root`

### 7.2 管理平面

实测通过：

1. `ens3` 已固定为 `172.32.2.21/24`
2. 默认路由已指向 `172.32.2.254`
3. 宿主机 `ping 172.32.2.21` 成功
4. 设备内 `ping 172.32.2.254` 成功

关键回读结果：

```text
hostname
ip -br a
ip route
```

### 7.3 新节点原生复验

在把上述内容固化回基础镜像之后，本次又新建了一台全新 Kylin 临时节点，仅执行：

1. 新建节点
2. 挂到管理交换机
3. 开机

没有再做任何运行态修补。

实测结果：

1. 宿主机 `ping 172.32.2.21` 成功
2. `root/admin@123` SSH 直接成功
3. `admin/admin@123` SSH 直接成功
4. `sudo` 提权直接成功

### 7.4 重启复验

这台 Kylin Server 已完成“初始化后重启仍然成立”的验证：

1. 重启后 `172.32.2.21` 可以恢复
2. 重启后 `root` SSH 再次登录成功
3. 重启后 `sudo` 提权再次成功

补充边界：

1. 首次开机与重启后的网络恢复都比 Debian 慢
2. 本次重启后大约等待 `20` 秒，再次 `ping` 才恢复稳定

### 7.5 控制台现状

本次对 `telnet://127.0.0.1:32777` 做了实际探测。

已确认的事实：

1. 串口连接可以建立
2. 可以收到窗口标题 `KYL1`

当前边界：

1. 当前 `telnet` 串口连接会被远端主动关闭
2. 还没有形成稳定可交互的登录提示
3. 当前更适合把它视为“SSH 管理已实证，串口控制台待专项补强”的服务器模板

## 8. 关键验证命令

设备内：

```text
hostname
ip -br a
ip route
ping -c 2 172.32.2.254
su - admin -c "printf 'admin@123\n' | sudo -S whoami"
```

宿主机侧：

```text
ping -c 2 172.32.2.21
ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null root@172.32.2.21
ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null admin@172.32.2.21
```

## 9. 已知边界

这张镜像当前必须明确记录下面几个边界：

1. 默认镜像仍是 `DHCP + root locked`，不能直接拿来做统一实验模板。
2. `virt-customize` 当前会给 Kylin 11 生成 `md5` 口令哈希告警，虽然本次实机可用，但后续最好单独确认更合适的 `password-crypto`。
3. 当前 `telnet` 串口还没有形成稳定可交互入口。
4. 首次开机和重启后的网络恢复时间都偏慢。
5. 当前只实证了 `1` 口规格，还没有展开多网卡业务口验证。

## 10. 当前标准结论

在当前 `192.168.100.20` 环境里，`linux-Kylin-Server-V11-2503` 已具备进入 OneOPS 第一阶段真实设备测试的初始化前提，但要带着明确边界使用：

1. 它已经能纳入统一账号 `admin/admin@123`
2. 它已经能固定带外管理地址并在重启后恢复
3. 它已经完成基础镜像固化，并经新节点原生启动复验
4. 它已经能承接 SSH、脚本、监控类服务器测试
5. 当前标准仍然是“单管理口 Kylin 服务器模板”
6. 串口控制台还不应计入已完成能力
