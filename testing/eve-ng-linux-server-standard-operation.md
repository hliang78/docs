# EVE-NG Linux Server 标准操作手册

更新时间：2026-06-27  
适用环境：`192.168.100.20` 上的 EVE-NG Community `6.2.0-4`

## 1. 目的

这份手册记录 Linux Server 在当前 EVE 环境中的实际初始化方式。

这台设备的目标不是只做到“能开机”，而是把下面几件事落成一条标准路径：

1. 模板默认账号和网络行为到底是什么
2. 如何把它变成统一的 `admin/admin@123`
3. 带外管理地址如何固定下来
4. SSH 和 `sudo` 是否真正可用
5. 当前阶段哪些地方还不能直接当成标准

## 2. 设备身份

1. 设备家族：Linux Server
2. 设备角色：业务网络设备 / 服务器
3. 厂商：Ubuntu
4. 当前模板状态：`已实证`

## 3. 适用镜像与节点规格

本次实测使用：

1. EVE 模板：`linux`
2. 镜像名称：`linux-ubuntu-server-20.04`
3. CPU：`1`
4. 内存：`2048`
5. 控制台：`telnet`
6. `ethernet` 参数：`1`
7. `qemu_nic`：`virtio-net-pci`

补充说明：

1. 当前阶段只验证了 `1` 口规格。
2. “扩成 `20` 个接口”还没有进入当前 Linux Server 标准。
3. 如果后续要把 Linux 也纳入统一多口业务拓扑，需要单独做一轮接口扩展验证。

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
2. 管理地址：`172.32.2.14/24`
3. 管理网关：`172.32.2.254`
4. 主机名：`SRV1`

## 5. 模板默认状态与前置处理

### 5.1 默认镜像的实际状态

本次实测确认这张镜像默认并不是“可直接拿来用”的状态：

1. 系统内只有 `root`
2. `root` 默认口令未知
3. `eth0` 默认是 `dhcp4: yes`
4. 当它接到当前无 DHCP 的管理桥时，首次开机会卡在：

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

在当前环境里，进入 Console 并用 `admin/admin@123` 登录后，执行下面这组最小配置即可完成标准化：

```text
sudo hostnamectl set-hostname SRV1

sudo tee /etc/netplan/01-netcfg.yaml >/dev/null <<'EOF'
network:
  version: 2
  renderer: networkd
  ethernets:
    eth0:
      dhcp4: false
      addresses:
        - 172.32.2.14/24
      gateway4: 172.32.2.254
      nameservers:
        addresses:
          - 172.32.2.254
          - 8.8.8.8
EOF

sudo netplan apply
```

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

1. `eth0` 已固定为 `172.32.2.14/24`
2. 默认路由已指向 `172.32.2.254`
3. `ping -c 2 172.32.2.254` 成功

关键回读结果：

```text
ip -br a
ip route
networkctl status eth0 --no-pager
hostname
```

### 7.3 SSH

实测通过：

1. `OpenBSD Secure Shell server` 正常启动
2. 从 EVE 宿主机 `172.32.2.1` 可实际 `ssh admin@172.32.2.14`
3. SSH 登录后可回读：

```text
hostname
```

结果为：

```text
SRV1
```

### 7.4 重启复验

这台 Linux Server 已完成“初始化后重启仍然成立”的验证：

1. 重启后 `Wait for Network to be Configured` 不再卡到 `2` 分钟
2. 本次重启日志显示：

```text
Finished Wait for Network to be Configured
```

3. 重启后 Console 登录提示正常出现
4. 重启后 SSH 再次登录成功

## 8. 关键验证命令

设备内：

```text
id admin
getent group sudo
ip -br a
ip route
networkctl status eth0 --no-pager
hostname
ping -c 2 172.32.2.254
```

宿主机侧：

```text
ping -c 2 172.32.2.14
ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null admin@172.32.2.14
printf 'admin@123\n' | sudo -S whoami
```

## 9. 已知边界

这台镜像当前必须明确记录下面几个边界：

1. 默认镜像不是统一账号模型，必须先做离线标准化。
2. 默认网络是 `dhcp4: yes`，接到无 DHCP 的管理桥后，首次开机会卡很久。
3. 只有把 `netplan` 改成静态地址后，后续重启才进入稳定状态。
4. 修改基础镜像不会自动修复已经创建的旧节点；模板改完后必须删节点重建。
5. 当前只实证了 `1` 口规格，不能把这份手册直接当成“20 口 Linux 服务器标准”。
6. 当前通过了管理面和 SSH 标准化，但还没有展开：
   - 多网卡业务口验证
   - 监控 Agent 批量下发
   - 大量脚本任务并发执行

## 10. 当前标准结论

在当前 `192.168.100.20` 环境里，`linux-ubuntu-server-20.04` 已经具备进入 OneOPS 第一阶段真实设备测试的初始化前提，但要带着明确边界使用：

1. 它已经能纳入统一账号 `admin/admin@123`
2. 它已经能固定带外管理地址并稳定重启
3. 它已经能作为服务器类设备的 SSH、脚本、监控验证起点
4. 当前标准仍然是“单管理口服务器模板”，不是“多业务口服务器模板”
