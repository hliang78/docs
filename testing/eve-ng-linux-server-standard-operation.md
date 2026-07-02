# EVE-NG Linux Server 标准操作手册

更新时间：2026-06-29  
适用环境：`192.168.100.20` 上的 EVE-NG Community `6.2.0-4`

## 1. 目的

这份手册记录 Linux Server 在当前 EVE 环境中的实际初始化方式。

当前目标不是只做到“能开机”，而是把下面几件事真正落成一条标准路径：

1. 模板默认账号和网络行为到底是什么
2. 如何把它变成统一的 `admin/admin@123`
3. 带外管理地址和业务地址如何固定下来
4. `SSH`、`sudo` 和 `SNMP` 是否真正可用
5. 当前阶段哪些地方还不能直接当成标准

## 2. 设备身份

1. 设备家族：Linux Server
2. 设备角色：业务服务器 / 观测服务器
3. 厂商：Ubuntu
4. 当前模板状态：`已实证`

## 3. 适用镜像与节点规格

本次实测使用：

1. EVE 模板：`linux`
2. 镜像名称：`linux-ubuntu-server-20.04`
3. 控制台：`telnet`
4. `qemu_nic`：`virtio-net-pci`

当前已实测的两种规格：

1. 业务服务器 `S1/S2`：`CPU = 1`，内存 = `2048`，`ethernet = 2`
2. 观测服务器 `OBS`：`CPU = 8`，内存 = `16G`，`ethernet = 1`

补充说明：

1. 当前主线已经验证了“双口业务服务器 + 单口观测服务器”的组合
2. “扩成 `20` 个接口”还没有进入当前 Linux Server 标准
3. 如果后续要把 Linux 也纳入统一多口业务拓扑，需要单独做一轮接口扩展验证

## 4. 接口展开与命名表

### 4.1 EVE API 侧可挂线接口

业务服务器 `S1/S2` 当前 API 回读接口为：

1. `e0`
2. `e1`

观测服务器 `OBS` 当前 API 回读接口为：

1. `e0`

### 4.2 设备 CLI 侧实际接口

业务服务器 `S1/S2` 内实际网卡名为：

1. `eth0`
2. `eth1`

观测服务器 `OBS` 内实际网卡名为：

1. `eth0`

### 4.3 当前标准接口角色

业务服务器 `S1/S2` 当前统一固定为：

1. `eth0 = 业务口`
2. `eth1 = 管理口`
3. 管理网关 = `172.32.2.254`

观测服务器 `OBS` 当前统一固定为：

1. `eth0 = 管理口`
2. 管理网关 = `172.32.2.254`
3. 节点规格固定为 `8 vCPU / 16G RAM`

## 5. 模板默认状态与前置处理

### 5.1 默认镜像的实际状态

本次实测确认这张镜像默认并不是“可直接拿来用”的状态：

1. 系统内只有 `root`
2. `root` 默认口令未知
3. 默认接口是 `dhcp4: yes`
4. 当它接到当前无 DHCP 的管理链路时，首次开机会卡在：

```text
Wait for Network to be Configured
```

直到大约 `2` 分钟后才继续进入登录提示。

### 5.2 标准化离线处理

为了把它纳入统一实验口令，本次对基础镜像做了离线处理：

```bash
virt-customize -a /opt/unetlab/addons/qemu/linux-ubuntu-server-20.04/virtioa.qcow2 \
  --root-password password:admin@123 \
  --run-command 'id -u admin >/dev/null 2>&1 || useradd -m -s /bin/bash admin' \
  --password admin:password:admin@123 \
  --run-command 'usermod -aG sudo admin'
```

处理结果：

1. `root` 口令改为 `admin@123`
2. 新增 `admin`
3. `admin` 口令改为 `admin@123`
4. `admin` 已加入 `sudo`

### 5.3 一个关键边界

这条 Linux 模板必须明确记录一个 EVE 行为边界：

1. 节点创建后，EVE 会为该节点生成自己的 `qcow2` 叠加盘
2. 后续再去修改基础镜像，不会自动影响已经存在的节点
3. 如果基础镜像标准化发生在节点创建之后，必须删除该节点并重建

否则会出现：

1. 基础镜像已经有 `admin`
2. 但已创建节点仍然吃旧的叠加盘
3. 实际登录行为与预期不一致

## 6. 标准初始化配置

### 6.1 业务服务器 `S1` 双口初始化

```text
sudo hostnamectl set-hostname S1

sudo tee /etc/netplan/01-netcfg.yaml >/dev/null <<'EOF'
network:
  version: 2
  renderer: networkd
  ethernets:
    eth0:
      dhcp4: false
      addresses:
        - 172.32.101.61/24
      routes:
        - to: 0.0.0.0/0
          via: 172.32.101.254
    eth1:
      dhcp4: false
      addresses:
        - 172.32.2.61/24
      routes:
        - to: 192.168.100.0/24
          via: 172.32.2.254
      nameservers:
        addresses:
          - 172.32.2.254
          - 8.8.8.8
EOF

sudo netplan apply
```

### 6.2 业务服务器 `S2` 双口初始化

```text
sudo hostnamectl set-hostname S2

sudo tee /etc/netplan/01-netcfg.yaml >/dev/null <<'EOF'
network:
  version: 2
  renderer: networkd
  ethernets:
    eth0:
      dhcp4: false
      addresses:
        - 172.32.102.62/24
      routes:
        - to: 0.0.0.0/0
          via: 172.32.102.254
    eth1:
      dhcp4: false
      addresses:
        - 172.32.2.62/24
      routes:
        - to: 192.168.100.0/24
          via: 172.32.2.254
      nameservers:
        addresses:
          - 172.32.2.254
          - 8.8.8.8
EOF

sudo netplan apply
```

### 6.3 观测服务器 `OBS` 单口初始化

```text
sudo hostnamectl set-hostname OBS

sudo tee /etc/netplan/01-netcfg.yaml >/dev/null <<'EOF'
network:
  version: 2
  renderer: networkd
  ethernets:
    eth0:
      dhcp4: false
      addresses:
        - 172.32.2.71/24
      routes:
        - to: 0.0.0.0/0
          via: 172.32.2.254
      nameservers:
        addresses:
          - 172.32.2.254
          - 8.8.8.8
EOF

sudo netplan apply
```

### 6.4 SNMP 标准化

当前这批 Ubuntu 20.04 服务器在主线环境里没有直接可用的公网 DNS 和在线软件源。
因此 `snmpd` 的标准化必须明确依赖“内网离线分发包”这条路径。

本轮实测的可复用步骤如下：

```text
mkdir -p /tmp/snmp-ubuntu20
cd /tmp/snmp-ubuntu20

curl -O http://172.32.2.1:18080/mysql-common_5.8+1.0.5ubuntu2_all.deb
curl -O http://172.32.2.1:18080/libmysqlclient21_8.0.42-0ubuntu0.20.04.1_amd64.deb
curl -O http://172.32.2.1:18080/libsensors-config_3.6.0-2ubuntu1.1_all.deb
curl -O http://172.32.2.1:18080/libsensors5_3.6.0-2ubuntu1.1_amd64.deb
curl -O http://172.32.2.1:18080/libsnmp-base_5.8+dfsg-2ubuntu2.9_all.deb
curl -O http://172.32.2.1:18080/libsnmp35_5.8+dfsg-2ubuntu2.9_amd64.deb
curl -O http://172.32.2.1:18080/snmp_5.8+dfsg-2ubuntu2.9_amd64.deb
curl -O http://172.32.2.1:18080/snmpd_5.8+dfsg-2ubuntu2.9_amd64.deb

echo 'admin@123' | sudo -S dpkg -i /tmp/snmp-ubuntu20/*.deb

cat <<'EOF' | sudo tee /etc/snmp/snmpd.conf >/dev/null
agentaddress udp:161
rocommunity admin@123 127.0.0.1
rocommunity admin@123 172.32.2.0/24
rocommunity admin@123 192.168.100.0/24
syslocation OneOps-EVE
syscontact OneOps
master agentx
EOF

echo 'admin@123' | sudo -S systemctl enable snmpd
echo 'admin@123' | sudo -S systemctl restart snmpd
```

关键说明：

1. `SNMP` 当前统一使用 `v2c`
2. 当前统一 `community = admin@123`
3. `enable` 不足以吸收刚写入的新配置，必须再执行一次 `restart`
4. 如果只做安装不重启，`snmpd` 会继续停留在默认的 `localhost` 监听行为

如果 Console 下 `sudo` 交互不方便，也可以用 `su -` 切到 `root` 完成同样的配置。  
当前 `root` 口令同样为：

```text
admin@123
```

## 7. 已实证结果

### 7.1 登录与权限

实测通过：

1. Console 使用 `admin/admin@123` 登录成功
2. `su -` 使用 `root/admin@123` 成功
3. `admin` 已在 `sudo` 组中
4. `printf 'admin@123\n' | sudo -S whoami` 返回 `root`

### 7.2 管理平面

实测通过：

1. `S1` 管理口 `eth1` 已固定为 `172.32.2.61/24`
2. `S2` 管理口 `eth1` 已固定为 `172.32.2.62/24`
3. `OBS` 管理口 `eth0` 已固定为 `172.32.2.71/24`
4. 三台服务器的管理默认网关均已指向 `172.32.2.254`
5. `ping -c 2 172.32.2.254` 成功

关键回读结果：

```text
ip -br a
ip route
networkctl status eth0 --no-pager
networkctl status eth1 --no-pager
hostname
```

### 7.3 SSH

实测通过：

1. `OpenSSH server` 正常启动
2. 从 EVE 宿主机 `172.32.2.1` 可实际 `ssh admin@172.32.2.61`
3. 从 EVE 宿主机 `172.32.2.1` 可实际 `ssh admin@172.32.2.62`
4. 从 EVE 宿主机 `172.32.2.1` 可实际 `ssh admin@172.32.2.71`

### 7.4 SNMP

实测通过：

1. `S1` 已可从 EVE 宿主机侧 `snmpwalk -v2c -c admin@123 172.32.2.61`
2. `S2` 已可从 EVE 宿主机侧 `snmpwalk -v2c -c admin@123 172.32.2.62`
3. `OBS` 已可从 EVE 宿主机侧 `snmpwalk -v2c -c admin@123 172.32.2.71`
4. 三台服务器都已返回系统 OID `1.3.6.1.2.1.1.1.0`

关键回读结果：

```text
systemctl is-active snmpd
ss -lun | grep :161
snmpwalk -v2c -c admin@123 172.32.2.61 1.3.6.1.2.1.1.1.0
snmpwalk -v2c -c admin@123 172.32.2.62 1.3.6.1.2.1.1.1.0
snmpwalk -v2c -c admin@123 172.32.2.71 1.3.6.1.2.1.1.1.0
```

### 7.5 重启复验

这批 Linux Server 已完成“初始化后重启仍然成立”的验证：

1. 重启后 `Wait for Network to be Configured` 不再卡到 `2` 分钟
2. Console 登录提示正常出现
3. 重启后 `SSH` 再次登录成功
4. 重启后 `SNMP` 仍可由管理面远端回收

### 7.6 OBS 规格约束

当前主线对 `OBS` 有一条明确固定约束：

1. `OBS` 不是普通轻量业务服务器
2. `OBS` 当前固定按 `8 vCPU / 16G RAM` 起机
3. 后续承载 `controller + agent`、集中执行链和监控联动时，都应沿用这条规格

## 8. 关键验证命令

设备内：

```text
id admin
getent group sudo
ip -br a
ip route
networkctl status eth0 --no-pager
networkctl status eth1 --no-pager
hostname
ping -c 2 172.32.2.254
systemctl is-active snmpd
```

宿主机侧：

```text
ping -c 2 172.32.2.61
ping -c 2 172.32.2.62
ping -c 2 172.32.2.71
ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null admin@172.32.2.61
ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null admin@172.32.2.62
ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null admin@172.32.2.71
snmpwalk -v2c -c admin@123 172.32.2.61 1.3.6.1.2.1.1.1.0
snmpwalk -v2c -c admin@123 172.32.2.62 1.3.6.1.2.1.1.1.0
snmpwalk -v2c -c admin@123 172.32.2.71 1.3.6.1.2.1.1.1.0
printf 'admin@123\n' | sudo -S whoami
```

## 9. 已知边界

这张镜像当前必须明确记录下面几个边界：

1. 默认镜像不是统一账号模型，必须先做离线标准化
2. 默认网络是 `dhcp4: yes`，接到无 DHCP 的管理链路后，首次开机会卡很久
3. 只有把 `netplan` 改成静态地址后，后续重启才进入稳定状态
4. 修改基础镜像不会自动修复已经创建的旧节点；模板改完后必须删节点重建
5. 服务器当前没有直接可用的公网 DNS 和在线软件源；`snmpd` 安装依赖离线包分发或预制镜像
6. `S1/S2` 当前实证的是 `2` 口业务服务器模型，`OBS` 当前实证的是 `1` 口观测服务器模型
7. `OBS` 当前还是资源例外项，固定按 `8 vCPU / 16G RAM` 运行，不应按业务服务器的轻量规格替代
8. 当前还不能把这份手册直接当成“20 口 Linux 服务器标准”
9. 当前通过了管理面、`SSH` 和 `SNMP` 标准化，但还没有展开：
   - 监控 Agent 批量下发
   - 大量脚本任务并发执行
   - 更复杂的多业务口服务器模型

## 10. 当前标准结论

在当前 `192.168.100.20` 环境里，`linux-ubuntu-server-20.04` 已经具备进入 OneOps 第一阶段真实设备测试的初始化前提，但要带着明确边界使用：

1. 它已经能纳入统一账号 `admin/admin@123`
2. 它已经能固定带外管理地址并稳定重启
3. 它已经能同时提供 `SSH + SNMP v2c` 入口，作为 OneOps 服务器类入库与监控验证起点
4. `S1/S2` 已进入“双口业务服务器模板”状态，`OBS` 当前仍是“单管理口观测服务器模板”
5. `OBS` 当前固定规格是 `8 vCPU / 16G RAM`
6. 当前标准还不是“20 口 Linux 服务器模板”
