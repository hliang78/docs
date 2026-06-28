# EVE-NG Rocky Linux Server 准备方案

更新时间：2026-06-28  
适用环境：`192.168.100.20` 上的 EVE-NG Community `6.2.0-4`

## 1. 目的

这份文档用于替代当前不稳定的 `linux-rhel-8.4` 旧镜像路线。

目标不是继续在旧 RHEL 8.4 镜像上做无限排障，而是尽快准备一条新的、最小化的、RHEL 兼容服务器镜像路径，用来承接：

1. 服务器 SSH 采集
2. 监控任务
3. 自动化脚本
4. 与网络设备、防火墙设备联动的真实场景测试

## 2. 当前结论

截至 2026-06-28，当前更适合选择：

1. `Rocky Linux 9 GenericCloud x86_64 qcow2`

作为新的 RHEL 兼容服务器基线，而不是继续把 `linux-rhel-8.4` 当作主线模板推进。

选择 Rocky 9 的原因很直接：

1. 它是 RHEL 兼容发行版，适合承接原先对 RHEL 系服务器测试能力的目标。
2. 官方直接提供 `qcow2` cloud 镜像，不需要先走完整 ISO 安装。
3. 对 EVE 来说，导入路径更短：
   - 下载
   - 落到 `addons/qemu`
   - 离线标准化
   - 新建节点验证
4. 当前 EVE 本地没有现成的 Rocky / Alma / RHEL 系安装资源，重新走旧镜像排障收益太低。

## 3. 当前已确认事实

### 3.1 本地资源现状

在当前 EVE 宿主机上，已经确认：

1. 没有现成的 Rocky / Alma / CentOS / 新版 RHEL 系 `qcow2` 或 ISO 资源。
2. 当前与 RHEL 系最接近的现有服务器镜像，只有：
   - `linux-rhel-8.4`
3. 因此如果要继续推进 RHEL 兼容服务器测试，必须引入新的基础镜像。

### 3.2 官方 Rocky 资源可达

已经从 EVE 宿主机直接验证，下面两个官方资源都可访问：

1. 镜像文件：
   [Rocky-9-GenericCloud.latest.x86_64.qcow2](https://dl.rockylinux.org/pub/rocky/9/images/x86_64/Rocky-9-GenericCloud.latest.x86_64.qcow2)
2. 校验文件：
   [Rocky-9-GenericCloud.latest.x86_64.qcow2.CHECKSUM](https://dl.rockylinux.org/pub/rocky/9/images/x86_64/Rocky-9-GenericCloud.latest.x86_64.qcow2.CHECKSUM)

本次实测结果：

1. HTTP 状态：`200`
2. 镜像 `Content-Length`：`645988352`

这说明官方 Rocky 9 GenericCloud 路线在当前环境里是可落地的。

### 3.3 当前落地状态

本次已经开始在 EVE 宿主机上执行下载：

1. 目标目录：
   - `/opt/unetlab/addons/qemu/linux-rocky-9-genericcloud`
2. 目标文件：
   - `Rocky-9-GenericCloud.latest.x86_64.qcow2`
   - `Rocky-9-GenericCloud.latest.x86_64.qcow2.CHECKSUM`

当前这一步的意义是：

1. 把“新镜像替代旧 RHEL”的方向从讨论变成实操。
2. 后续只要下载完成，就可以直接进入离线标准化和 EVE 新节点验证。

## 4. 推荐导入标准

建议按下面的 EVE 目录标准准备 Rocky 镜像：

1. 目录名：
   - `linux-rocky-9-genericcloud`
2. EVE 主磁盘文件名：
   - `virtioa.qcow2`

推荐步骤：

1. 下载官方 `qcow2`
2. 完成 `sha256` 校验
3. 重命名为：
   - `virtioa.qcow2`
4. 放入：
   - `/opt/unetlab/addons/qemu/linux-rocky-9-genericcloud/`
5. 执行：
   - `/opt/unetlab/wrappers/unl_wrapper -a fixpermissions`

## 5. Rocky 基线标准化目标

如果下载与导入成功，后续标准化目标与现有 Ubuntu / Debian / Kylin 线保持一致：

1. 统一账号：
   - `root/admin@123`
   - `admin/admin@123`
2. `admin` 具备 `sudo` / 管理能力
3. 静态管理地址写入：
   - `172.32.2.x/24`
4. 默认网关：
   - `172.32.2.254`
5. 真实 `SSH` 登录成功
6. 初始化后重启复验成功
7. 基础镜像固化后，新节点原生启动复验成功

## 6. 首轮验证清单

Rocky 镜像进入 EVE 后，首轮只做最小闭环，不做功能扩展：

1. 节点能正常创建和启动
2. 串口是否形成稳定可交互入口
3. `SSH` 是否能建立
4. `ip -br a` 是否按静态地址收敛
5. `ip route` 是否正确指向 `172.32.2.254`
6. `sudo` 是否可用
7. 重启后配置是否保留

只有这 7 项跑通，才把它升级为“服务器标准模板候选”。

## 7. 与旧 RHEL 8.4 的关系

当前建议非常明确：

1. `linux-rhel-8.4` 保留为：
   - `RHEL 镜像适配专项`
2. `Rocky 9 GenericCloud` 作为：
   - `新的 RHEL 兼容服务器主线候选`

这样处理的好处是：

1. 不阻塞第一阶段服务器测试主线
2. 不把团队精力继续消耗在旧镜像的历史状态上
3. 后续如果 Rocky 跑通，OneOPS 在客户视角仍然具备 RHEL 系服务器覆盖能力

## 8. 下一步

当前建议执行顺序如下：

1. 等 Rocky 9 `qcow2` 下载完成并完成校验
2. 在 EVE 中按 `virtioa.qcow2` 标准落位
3. 对 Rocky 9 做第一轮离线标准化
4. 新建节点并完成最小管理面验证
5. 如果通过，再补成独立标准操作手册
