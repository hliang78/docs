# EVE-NG Linux RHEL Server 首轮初始化与边界记录

更新时间：2026-06-28  
适用环境：`192.168.100.20` 上的 EVE-NG Community `6.2.0-4`

## 1. 目的

这份文档不把 `linux-rhel-8.4` 直接写成“已实证标准模板”。

当前更重要的是把这张镜像在 EVE 里的真实初始化尝试、已验证事实和当前未收敛边界记录清楚，避免团队把它误当成已经和 Ubuntu 一样可以稳定复用的服务器模板。

## 2. 当前结论

截至 2026-06-28，`linux-rhel-8.4` 在当前 EVE 环境中：

1. 已确认镜像真实存在，系统为 `Red Hat Enterprise Linux 8.4 (Ootpa)`。
2. 已确认默认网卡名为 `ens3`，默认网络配置文件为 `/etc/sysconfig/network-scripts/ifcfg-ens3`。
3. 已确认基础镜像可以被离线标准化为：
   - `root/admin@123`
   - `admin/admin@123`
   - `admin` 加入 `wheel`
4. 已确认基础镜像可以被离线写入静态管理配置：
   - `172.32.2.19/24`
   - 网关 `172.32.2.254`
5. 但当前还没有形成“可复验的管理面闭环”：
   - 宿主机无法 `ping 172.32.2.19`
   - `ARP` 一直是 `incomplete`
   - `22/tcp` 无法建立
   - `telnet` 控制台也没有形成稳定可交互登录入口
   - 独立 `qemu` 运行态探针里，宿主机转发端口虽然能 `connect`，但 `SSH banner exchange` 仍然超时

因此它当前应标记为：

1. `镜像可识别`
2. `离线账号标准化可执行`
3. `离线静态网络配置可写入`
4. `运行态管理面未实证打通`
5. `当前不能作为 Linux Server 标准模板`

## 3. 本次实际验证结果

### 3.1 镜像与系统类型

离线检查已确认：

1. 镜像目录存在：`/opt/unetlab/addons/qemu/linux-rhel-8.4`
2. 主磁盘文件存在：`virtioa.qcow2`
3. 系统识别为：

```text
Red Hat Enterprise Linux 8.4 (Ootpa)
```

4. 分区形态为：
   - `/dev/sda1` -> `/boot`
   - `/dev/rhel/root` -> `/`
   - `/dev/rhel/swap` -> `swap`

### 3.2 默认网络模型

离线读取已确认：

1. 默认网卡配置文件是：
   - `/etc/sysconfig/network-scripts/ifcfg-ens3`
2. 默认配置为：

```text
BOOTPROTO=dhcp
DEVICE=ens3
ONBOOT=yes
```

3. 默认 SSH 服务配置中：
   - `PermitRootLogin yes`
   - `PasswordAuthentication yes`

这说明它理论上具备“走密码 SSH”的基础条件，但默认仍是 DHCP 管理模型，不适合当前无 DHCP 的管理桥。

### 3.3 已完成的离线标准化

本次已对基础镜像执行：

1. `virt-customize` 统一账号：
   - `root/admin@123`
   - `admin/admin@123`
   - `admin -> wheel`
2. 离线写入主机名：
   - `RHEL1`
3. 离线改写 `ifcfg-ens3` 为静态管理地址：

```text
IPADDR=172.32.2.19
PREFIX=24
GATEWAY=172.32.2.254
DNS1=172.32.2.254
DNS2=8.8.8.8
BOOTPROTO=none
ONBOOT=yes
```

4. 已确认文件写回后仍保留正确 `SELinux` 标签：
   - `ifcfg-ens3 -> net_conf_t`
   - `/etc/hostname -> hostname_etc_t`

### 3.4 已尝试的可管理化增强

为了让 EVE 串口更接近“服务器模板”而不是“桌面安装形态”，本次还额外尝试了：

1. 把默认 target 改为 `multi-user.target`
2. 增加：
   - `serial-getty@ttyS0.service`
3. 直接改写当前内核 BLS 启动项，加入：

```text
console=tty0 console=ttyS0,115200n8
```

### 3.5 运行态 overlay probe 结果

为了把“镜像本身问题”和“EVE 封装问题”拆开，本次还做了一轮独立运行态探针：

1. 基于基础镜像创建临时 overlay：
   - `/tmp/rhel-runtime-probe.qcow2`
2. 直接在 EVE 宿主机用 `qemu-system-x86_64` 启动这张 overlay：
   - 不经过 `.unl` 拓扑
   - 使用 `hostfwd tcp::4226-:22`
   - 单独记录串口启动日志
3. 当前 probe 启动前，overlay 内部状态已确认：
   - `ifcfg-ens3` 仍是静态管理配置
   - `/etc/NetworkManager/conf.d/10-force-ifcfg-rh.conf` 存在
   - `/etc/NetworkManager/system-connections` 为空
   - `/var/lib/NetworkManager` 里只剩：
     - `NetworkManager-intern.conf`
     - `NetworkManager.state`
4. 但这轮 probe 的运行态结果仍然没有收敛：
   - `192.168.100.20:4226` 可以建立 TCP 连接
   - 但 `ssh -p 4226 root@192.168.100.20` 持续停在：

```text
Connection timed out during banner exchange
```

5. 同时，本轮 probe 的当前启动日志只推进到：

```text
Starting firewalld - dynamic firewall daemon...
```

6. 截至 probe 进程自然结束，当前启动日志里仍没有形成这轮新启动对应的：
   - `Started Network Manager.`
   - `Started OpenSSH server daemon.`
   - `Reached target Multi-User System.`

这说明问题已经不是“离线 ifcfg 文件有没有写进去”这么简单，而是运行态启动链本身就在当前镜像上不稳定。

### 3.6 历史镜像特征补充

离线回读镜像内既有日志和残留状态，还能看到两个重要特征：

1. 这张镜像存在明显的桌面/图形安装痕迹：
   - `gdm`
   - `gnome-shell`
   - `vino-server`
   - `xrdp`
   - `libvirt`
2. 历史 `NetworkManager` 日志里曾经明确出现过：
   - `ens3` 被自动激活
   - 通过 `DHCP` 绑定到 `192.168.1.54`

这说明它不是一张干净的“最小化服务器模板”，而更像一张被长期使用过、带桌面和历史网络状态的实验镜像。

### 3.7 第二轮专项验证结果

在上面的基础上，本次又继续做了两组更有针对性的运行态验证，目的都是把根因进一步收敛，而不是继续停留在“可能是启动太慢”这一层。

#### 3.7.1 服务裁剪 probe

本次重新制作了一张临时 overlay，并在不改基础镜像的前提下，主动裁剪了明显不属于“实验服务器模板”的服务链：

1. `gdm`
2. `xrdp`
3. `libvirtd`
4. `ModemManager`
5. `avahi`
6. `cups`
7. `firewalld`
8. `NetworkManager-wait-online`

同时把这些服务对应的：

1. `dbus` alias
2. `socket` 激活入口
3. `target.wants` 软链接

也一并屏蔽或删除。

这轮验证说明：

1. 串口启动日志里的杂项服务明显减少了。
2. 当前串口链条已经能更清楚地看到：
   - `Starting Network Manager...`
   - `Reached target sshd-keygen.target`
3. 但即便这样，宿主机转发端口上的 `SSH banner` 仍然没有出现：

```text
Connection timed out during banner exchange
```

也就是说，简单把桌面/宿主相关服务裁掉，并不能直接让管理面闭环恢复。

#### 3.7.2 绑定旧 UUID 的静态 ifcfg probe

由于历史日志反复显示，运行态总是在自动激活同一个旧连接：

```text
auto-activating connection 'ens3' (444b9393-1769-4fe7-90d3-e5b0f8bbec94)
```

本次又做了一轮更精准的测试：

1. 继续使用临时 overlay
2. 保留静态管理配置：
   - `172.32.2.19/24`
   - `172.32.2.254`
3. 但把 `ifcfg-ens3` 显式绑定到这个旧 UUID：

```text
UUID=444b9393-1769-4fe7-90d3-e5b0f8bbec94
```

4. 同时继续保留：
   - `BOOTPROTO=none`
   - `ONBOOT=yes`
   - `NM_CONTROLLED=yes`

验证结果仍然没有改变：

1. overlay 里的 `ifcfg-ens3` 确实保持静态配置
2. `/etc/NetworkManager/system-connections` 仍然为空
3. `/var/lib/NetworkManager` 里仍只剩：
   - `NetworkManager-intern.conf`
   - `NetworkManager.state`
4. 但历史与反复出现的运行态日志仍显示：

```text
policy: auto-activating connection 'ens3' (444b9393-1769-4fe7-90d3-e5b0f8bbec94)
dhcp4 (ens3): activation: beginning transaction
dhcp4 (ens3): state changed unknown -> bound, address=192.168.1.54
```

5. 宿主机转发端口上的 `SSH banner` 依然超时。

这说明当前问题已经可以更具体地描述为：

1. 离线静态 `ifcfg-ens3` 已经真实存在于磁盘中
2. 但运行态 `NetworkManager` 仍在按旧的 `ens3` 连接模型走 `DHCP`
3. 这条旧连接逻辑并没有因为：
   - 删除 lease
   - 删除时间戳
   - 强制 `ifcfg-rh`
   - 绑定旧 UUID
   而自动切换到我们希望的静态管理模型

### 3.8 第三轮启动稳定性验证

为了确认这条线到底是“网络模型错误”还是“镜像启动稳定性本身就不足”，本次又继续做了两组验证：

#### 3.8.1 开机即时运行态探针

本次尝试把 `nmcli/ip route/ifcfg` 探针直接挂到：

1. `multi-user.target`
2. `NetworkManager.service.wants`

并要求它同时：

1. 写入 guest 内部文件
2. 回显到 `ttyS0`

这样理论上只要 `NetworkManager` 真正进入 active，串口里就应该出现：

```text
=== NMCLI CON ===
=== NMCLI DEVICE ===
```

但实际结果是：

1. 探针输出文件始终为空
2. 串口里也没有出现探针标记
3. 宿主机转发端口仍然只表现为：

```text
Connection timed out during banner exchange
```

这说明在当前镜像里，问题已经不只是“旧连接对象没有清理干净”，而是连稳定的运行态探针入口都难以形成。

#### 3.8.2 强裁剪后的当前启动链

本次把前面已确认会制造噪声或拖慢启动的服务继续做了更彻底的裁剪，包括：

1. `gdm`
2. `xrdp`
3. `libvirtd`
4. `ModemManager`
5. `avahi`
6. `cups`
7. `firewalld`
8. `NetworkManager-wait-online`
9. `accounts-daemon`
10. `rtkit`
11. `udisks2`
12. `polkit`
13. `systemd-machined`
14. `sssd`
15. `chronyd`
16. `tuned`
17. `ksmtuned`

同时把对应的：

1. `dbus` alias
2. `socket` 激活入口
3. `target.wants` 软链接

也尽量一起去掉。

裁剪后的串口链条确实更干净了，当前已能明确看到它最终推进到：

```text
Starting Network Manager...
```

但截至这轮观测窗口结束，仍然没有形成：

1. 可见的 `nmcli` 探针输出
2. 可建立的 `SSH banner`
3. 可复验的稳定管理面

这说明当前镜像的真实边界可以进一步升级为：

1. 即使已经做了较强的服务裁剪，启动路径仍然不稳定
2. 即使已经把探针挂到 `NetworkManager` 启动点，运行态仍然没有形成稳定观测入口
3. 这张镜像当前不适合作为第一阶段主线服务器模板继续投入

## 4. 当前失败表现

在完成上面的离线标准化后，本次仍然稳定复现了下面几类失败：

### 4.1 宿主机管理面失败

从 EVE 宿主机复测：

1. `ping 172.32.2.19` 失败
2. 返回：

```text
Destination Host Unreachable
```

3. `arp -n` 中该地址始终为：

```text
(incomplete)
```

4. `22/tcp` 建连失败：

```text
No route to host
```

### 4.2 独立直启仍未形成 SSH 可管理闭环

即使脱离 `.unl`，直接在宿主机上启动临时 overlay：

1. `hostfwd` 端口会打开
2. 但 `SSH` 仍然无法拿到 banner
3. 当前 probe 的启动日志停在 `firewalld` 启动阶段附近

也就是说，这条线当前并不是“只有 EVE 网桥层有问题”，而是镜像自己的运行态启动链也没有收敛。

### 4.3 控制台未形成稳定登录入口

尽管本次已经尝试补上：

1. `multi-user.target`
2. `serial-getty@ttyS0`
3. `console=ttyS0`

但当前 `telnet://192.168.100.20:32777` 仍未形成稳定可交互登录提示。

也就是说，当前不能把这张镜像视为“已经具备和 Ubuntu 一样的 EVE 串口初始化路径”。

## 5. 已缩小的根因范围

这轮排查虽然没有把管理面打通，但已经排除了几条错误方向：

1. 不是镜像不存在。
2. 不是账号标准化没写进去。
3. 不是静态配置文件根本没写进去。
4. 不是 `SELinux` 标签被 guestfish 直接写坏。
5. 不是单纯少建了 `serial-getty@ttyS0`。
6. 不是单纯“EVE 图形封装把镜像搞坏了”，因为脱离 `.unl` 的独立 overlay probe 也没有拿到稳定 `SSH` banner。

当前更像下面这类边界之一：

1. 镜像当前运行态启动链在当前环境里推进很慢，甚至会停在 `firewalld` 附近，导致 `NetworkManager` / `sshd` 没有形成稳定闭环。
2. 这张 RHEL 镜像仍保留较重的桌面/图形与多服务安装特征，不像干净的服务器模板。
3. 即使静态 `ifcfg-ens3` 已写回，而且显式绑定了旧 UUID，也还不能让运行态放弃旧的 `DHCP ens3` 连接路径。
4. 当前更像是 `NetworkManager` 历史连接状态与这张旧镜像的整体运行态模型耦合过深。
5. 即使已经做了较强的服务裁剪，镜像启动稳定性仍然不足，难以形成稳定的运行态观测入口。
6. 还需要额外的系统级裁剪、运行态清理或直接重制镜像，而不是继续只靠离线文件标准化。

## 6. 对第一阶段测试推进的影响

这条边界不会阻断服务器类测试整体推进，但会影响 RHEL 这条子线的节奏：

1. 当前 Linux Server 主线仍应以 Ubuntu 模板承接：
   - SSH
   - 脚本
   - 监控
2. `linux-rhel-8.4` 当前更适合作为“服务器镜像适配专项”，而不是稳定模板。
3. 第一阶段服务器覆盖面建议优先继续推进：
   - `linux-debian-10.3.0`
   - `linux-Kylin-Server-V11-2503`

## 7. 后续建议

后续如果继续攻关 `linux-rhel-8.4`，建议按下面顺序推进：

1. 不建议继续在这张既有镜像上做“只改 ifcfg 文件”的离线盲改。
2. 更合适的方向是直接准备一张新的、最小化的 RHEL / Rocky / Alma 服务器镜像，再按当前统一标准重做。
3. 如果还要继续攻关这张现有镜像，优先级应改为：
   - 在运行态里直接清理 `NetworkManager` 的旧连接对象
   - 先把 `NetworkManager` 启动后的即时探针真正跑起来
   - 重新验证 `ens3` 是否还能被自动拉成 `DHCP 192.168.1.54`
   - 再验证静态管理配置是否真正生效
4. 如果后续仍不能打通，应把它明确记录为：
   - `当前 EVE 环境下未收敛的 RHEL 服务器模板边界`
