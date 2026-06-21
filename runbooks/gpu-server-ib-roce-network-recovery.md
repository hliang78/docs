# GPU 服务器 IB / ROCE 网络恢复 Runbook

Date: 2026-06-21

## 目的

这份 runbook 用于处理 GPU 服务器的 IB、ROCE 和存储网络相关故障，尤其是以下高频问题：

- NCCL 或多机训练异常
- IB 网卡 down
- 网卡名与 `mlx5_*` 对应关系错误
- 存储网络异常导致共享目录不可用
- RDMA MTU、PFC、DSCP 或持久化配置错误

## 适用范围

优先适用于：

- `A800`
- `A800二期扩容`
- 涉及 IB 组网的 H100 或其他训练节点

可部分参考于 ROCE 场景：

- `4090`
- 部分 A10 或其他以以太网 RDMA 组网的服务器

## 进入条件

出现以下任一症状时进入本 runbook：

- OneOPS、业务或监控提示训练通信异常
- `ibdev2netdev` 对应关系不符合预期
- `ibstat` 显示非 `Active`
- 存储目录如 `/nvfile-data` 无法挂载或掉线
- 服务器重启后网卡名变化

## 排障原则

### 先分清是“名字错”还是“链路坏”

IB/ROCE 问题最容易混淆成一类，但处理路径不同：

- 名字错：逻辑对应关系异常，通常需要修复命名或配置
- 链路坏：模块、线缆、交换机端口、驱动、固件或卡本身异常

### 先收敛症状，再动驱动

先确认到底是：

- 业务超时
- 卡 down
- 目录挂载失败
- 命名错误
- 拥塞或带宽异常

不要一上来就重装 OFED 或重启整机。

## 标准流程

### 1. OneOPS 和业务侧确认

先确认：

- 哪个训练任务、哪个节点组出现问题
- 是单节点还是多节点
- 是否刚发生过重启、换卡、系统变更、驱动升级

从 OneOPS 收集：

- 告警
- 日志
- 最近任务记录
- 最近变更或操作审计

### 2. 基础检查命令

先跑这组命令：

```bash
ip addr
ibdev2netdev
ibstat
mount | grep nvfile-data
ethtool <bond-or-eth>
```

如果是 ROCE 场景，再看：

```bash
ip link
ibv_devinfo
```

### 3. 问题分型

#### A. 网卡名或 `mlx5_*` 对应关系错误

常见表现：

- 存储网卡没有落在预期的 `mlx5_2`
- 重启后 `ib2` 或等效存储网卡映射变化

处理顺序：

1. 先找出真正承载存储地址的网卡
2. 对照 `ibdev2netdev` 看对应的是哪个 `mlx5_*`
3. 如果已有标准检查脚本，优先执行
4. 脚本无效时再人工改名

常用检查：

```bash
ip addr | grep 172.16.
ibdev2netdev
```

人工改名前注意：

- 必须先明确当前映射
- 优先在维护窗口进行
- 改完要立刻复查并考虑持久化

#### B. IB 网卡 down

常见表现：

- `ibstat` 不是 `Active`
- 存储目录掉线
- 业务报多机通信错误

处理顺序：

1. 用 `ibstat` 确认端口状态
2. 检查模块、线缆、交换机端口
3. 必要时重置网卡或重启相关服务
4. 仍未恢复时考虑换线、换模块、换卡

常用检查：

```bash
ibstat
systemctl status nvfile-helperd
systemctl status nvfile-client
```

如果存储侧依赖 helper/client 服务，可尝试：

```bash
systemctl restart nvfile-helperd
systemctl restart nvfile-client
```

#### C. 共享目录挂载失败

常见表现：

- `/nvfile-data` 不可用
- 业务启动后直接报存储路径问题

处理顺序：

1. 确认存储网卡是否 `Active`
2. 确认 helper/client 服务状态
3. 确认 mount 状态
4. 再判断是否为上游网络问题

#### D. 拥塞或性能异常

常见表现：

- 训练耗时异常增加
- 链路不完全断，但性能明显恶化

处理思路：

1. 先确认是不是业务参数问题
2. 再确认网络是否触发拥塞、PFC 或 DSCP 配置异常
3. 需要时联动交换机 / UFM / IB 工程师

这里通常不是一线值班单独能闭环的问题，重点是把证据收齐：

- 时间段
- 受影响节点
- 训练任务
- 业务现象
- 网卡状态
- 交换机或 UFM 侧日志

## OFED / IB 驱动恢复

只有在确认问题与驱动、模块或配置有关时，才进入这一步。

先确认：

- 内核版本与 `kernel-devel` 是否匹配
- `openibd` 是否能正常启动
- 最近是否升级过系统、驱动或固件

恢复步骤建议：

1. 确认内核、头文件、依赖一致
2. 重新安装或修复 OFED
3. 重启相关服务
4. 必要时重启服务器
5. 重新验证 `ibstat` 和业务连通性

### 恢复后至少验证

```bash
ibstat
ibdev2netdev
ping <gateway-or-peer>
mount | grep nvfile-data
```

如果需要做更深验证，可补：

- `ibping`
- 业务侧 NCCL 测试
- OneOPS 任务中心下发标准验证脚本

## ROCE 专项

如果是 ROCE 网卡命名、QoS 或 MTU 问题，重点看：

- 按 MAC 固化命名
- `cma_roce_tos`
- PFC 和 DSCP
- 网卡 MTU
- 开机自启动服务

这类问题通常表现为：

- 重启后名字丢失
- 配置临时生效但重启失效
- 训练性能异常

建议处理顺序：

1. 先确认命名是否稳定
2. 再确认 QoS 与 MTU
3. 最后确认持久化服务是否生效

## 持久化要求

任何临时修复完成后，都要检查是否已持久化：

- 名称映射规则
- 网络脚本
- systemd service
- 开机加载配置

否则非常容易在重启后复发。

## 升级条件

出现以下情况时升级给网络 / IB 专家或厂商：

- 多节点同时异常
- 线缆或模块替换后仍无恢复
- `ibstat` 长时间无法回到 `Active`
- 明显是交换机/UFM/拥塞控制侧问题
- 重装驱动后仍不恢复

## 关联文档

- [gpu-server-fault-response.md](/Users/huangliang/project/OneOPS-ALL/docs/runbooks/gpu-server-fault-response.md)
- [gpu-server-bmc-and-vendor-evidence-collection.md](/Users/huangliang/project/OneOPS-ALL/docs/runbooks/gpu-server-bmc-and-vendor-evidence-collection.md)
- [gpu-server-os-reinstall-and-baseline.md](/Users/huangliang/project/OneOPS-ALL/docs/runbooks/gpu-server-os-reinstall-and-baseline.md)
