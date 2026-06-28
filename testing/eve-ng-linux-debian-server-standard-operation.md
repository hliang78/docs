# EVE-NG Debian Server 标准操作手册

更新时间：2026-06-28  
适用环境：`192.168.100.20` 上的 EVE-NG Community `6.2.0-4`

## 1. 目的

这份手册记录 `linux-debian-10.3.0` 在当前 EVE 环境中的实际标准化路径。

目标不是只证明这台 Debian 能启动，而是把下面几件事收敛成可复验模板：

1. 统一账号 `admin/admin@123`
2. 固定带外管理地址
3. SSH 登录可用
4. `sudo` 提权可用
5. 重启后仍然保持成立

## 2. 设备身份

1. 设备家族：Debian Server
2. 设备角色：业务网络设备 / 服务器
3. 厂商：Debian
4. 当前模板状态：`已实证`

## 3. 适用镜像与节点规格

本次实测使用：

1. EVE 模板：`linux`
2. 镜像名称：`linux-debian-10.3.0`
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

1. `eth0`

### 4.3 当前标准管理口

当前统一固定为：

1. 管理口：`eth0`
2. 管理地址：`172.32.2.20/24`
3. 管理网关：`172.32.2.254`
4. 主机名：`DEB1`

## 5. 默认状态与标准化要点

### 5.1 默认镜像的实际状态

本次离线检查确认：

1. 系统为 `Debian GNU/Linux 10 (buster)`
2. 默认主机名为 `kvm`
3. 默认网络配置为：

```text
allow-hotplug eth0
iface eth0 inet dhcp
```

4. 默认存在 `root`，但不适合作为当前统一实验模板直接使用
5. 默认未安装 `sudo`
6. 默认 `apt source` 仍指向已过期的 `buster` 在线源
7. 默认 `/etc/resolv.conf` 残留了无效 `nameserver 192.168.1.1`

### 5.2 已完成的离线标准化

本次对基础镜像已完成：

1. `root` 口令统一为 `admin@123`
2. 新增 `admin`
3. `admin` 口令统一为 `admin@123`
4. `admin` 加入 `sudo` 组
5. 主机名改为 `DEB1`
6. `/etc/network/interfaces` 改为静态管理地址：

```text
auto lo
iface lo inet loopback

auto eth0
iface eth0 inet static
    address 172.32.2.20/24
    gateway 172.32.2.254
    dns-nameservers 172.32.2.254 8.8.8.8
```

### 5.3 本次固化项

这张 Debian 10 模板在 `2026-06-28` 已把下面三处一并固化进基础镜像：

1. `/etc/resolv.conf` 改成真实可用 DNS
2. `/etc/apt/sources.list` 切到 `archive.debian.org`
3. `/etc/hosts` 把 `127.0.1.1` 从 `kvm` 改成 `DEB1`

## 6. 标准初始化步骤

下面这组内容已经固化进基础镜像；这里保留为“标准镜像应具备的落盘内容”：

```text
cat >/etc/resolv.conf <<'EOF'
nameserver 172.32.2.254
nameserver 8.8.8.8
EOF

cat >/etc/apt/sources.list <<'EOF'
deb http://archive.debian.org/debian buster main
deb http://archive.debian.org/debian-security buster/updates main
EOF

cat >/etc/apt/apt.conf.d/99archive-no-check-valid-until <<'EOF'
Acquire::Check-Valid-Until "false";
EOF

wget -O /root/sudo_1.8.27-1+deb10u3_amd64.deb \
  http://archive.debian.org/debian/pool/main/s/sudo/sudo_1.8.27-1+deb10u3_amd64.deb
dpkg -i /root/sudo_1.8.27-1+deb10u3_amd64.deb

cat >/etc/hosts <<'EOF'
127.0.0.1 localhost
127.0.1.1 DEB1

# The following lines are desirable for IPv6 capable hosts
::1 localhost ip6-localhost ip6-loopback
ff02::1 ip6-allnodes
ff02::2 ip6-allrouters
EOF
```

## 7. 已实证结果

### 7.1 登录与权限

实测通过：

1. `root/admin@123` SSH 登录成功
2. `admin/admin@123` SSH 登录成功
3. `id` 回读为 `admin` 已加入 `sudo`
4. `printf 'admin@123\n' | sudo -S whoami` 返回 `root`

### 7.2 管理平面

实测通过：

1. `eth0` 已固定为 `172.32.2.20/24`
2. 默认路由已指向 `172.32.2.254`
3. 宿主机 `ping 172.32.2.20` 成功
4. 设备内 `ping 172.32.2.254` 成功
5. 设备内 `ping 8.8.8.8` 成功

关键回读结果：

```text
hostname
ip -br a
ip route
cat /etc/resolv.conf
```

### 7.3 `sudo`

实测通过：

1. `sudo` 包已成功安装
2. `/etc/hosts` 修正后，`sudo` 不再报主机名解析告警
3. `admin` 账号可正常提权

### 7.4 重启复验

这台 Debian Server 已完成“初始化后重启仍然成立”的验证：

1. 重启后宿主机 `ping 172.32.2.20` 成功恢复
2. 重启后 `root` SSH 再次登录成功
3. 重启后 `admin` SSH 再次登录成功
4. 重启后回读仍保持：
   - `hostname = DEB1`
   - `eth0 = 172.32.2.20/24`
   - `default via 172.32.2.254`
   - `sudo` 提权成功

### 7.5 新节点复验

在把上述内容固化回基础镜像之后，本次又新建了一台全新 Debian 临时节点，仅执行：

1. 新建节点
2. 挂到管理交换机
3. 开机

没有再做任何运行态修补。

实测结果：

1. 宿主机 `ping 172.32.2.20` 成功
2. `root/admin@123` SSH 直接成功
3. `admin/admin@123` SSH 直接成功
4. `su - admin -c "printf 'admin@123\n' | sudo -S whoami"` 返回 `root`

这说明当前 Debian 标准已经从“可手工修通”提升到“基础镜像可直接复用”。

## 8. 关键验证命令

设备内：

```text
hostname
ip -br a
ip route
cat /etc/resolv.conf
su - admin -c "printf 'admin@123\n' | sudo -S whoami"
```

宿主机侧：

```text
ping -c 2 172.32.2.20
ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null root@172.32.2.20
ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null admin@172.32.2.20
```

## 9. 已知边界

这张镜像当前必须明确记录下面几个边界：

1. 默认镜像不是统一账号模型，必须先做离线标准化。
2. 默认网络是 DHCP，不适合当前无 DHCP 的管理桥。
3. `dns-nameservers` 写进 `/etc/network/interfaces` 后，并不会自动修复运行态 `/etc/resolv.conf`。
4. Debian 10 `buster` 已 EOL，`apt` 不能再直接依赖原在线源，必须切到归档源。
5. 默认未安装 `sudo`，不能假设 `admin` 进了 `sudo` 组就已经可提权。
6. 当前只实证了 `1` 口规格，还没有展开多网卡业务口验证。

## 10. 当前标准结论

在当前 `192.168.100.20` 环境里，`linux-debian-10.3.0` 已具备进入 OneOPS 第一阶段真实设备测试的初始化前提，但要带着明确边界使用：

1. 它已经能纳入统一账号 `admin/admin@123`
2. 它已经能固定带外管理地址并稳定重启
3. 它已经完成基础镜像固化，并经新节点原生启动复验
4. 它已经能承接 SSH、脚本、监控类服务器测试
5. 当前标准仍然是“单管理口 Debian 服务器模板”，不是“多业务口服务器模板”
