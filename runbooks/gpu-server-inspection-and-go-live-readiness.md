# GPU 服务器标准巡检与上线检查 Runbook

Date: 2026-06-21

## 目的

这份 runbook 用于判断一台 GPU/NPU 服务器是否达到“可交付、可接管、可上线、可投入训练或业务”的状态。它把原始 SOP 中的检查项、压测项和验收逻辑整理成 OneOPS 风格的巡检与上线门禁。

## 适用场景

适用于以下场景：

- 新机器首次上线前验收
- 扩容节点交付前检查
- 重装后的恢复验收
- 换卡、换件、驱动修复后的重新放行
- 日常巡检中对重点节点做深度确认

适用机型：

- `4090`
- `A800`
- `A800二期扩容`
- `A10`
- `H100`
- `910B`

## 判定原则

上线检查不是只看一条命令或一项监控是否正常，而是同时回答 3 个问题：

1. 静态配置是否正确
2. 运行态是否稳定
3. 业务验证是否通过

最终结论只允许落在三档：

- `可上线`
- `限制上线`
- `不可上线`

## 使用顺序

### 1. 先用 OneOPS 收上下文

先在 OneOPS 确认：

- 设备编码、机型、项目、机柜位置
- 当前是否有未收口告警
- 最近是否有变更、重装、换件、驱动修复
- 是否已有历史故障或重复异常

### 2. 再做本 runbook 的分段检查

按顺序执行：

1. 静态检查
2. 运行态检查
3. 压测与功能验证
4. 上线验收与证据归档

## 一、静态检查

### 1. 基础身份与硬件信息

确认：

- 设备编码、主机名、机型一致
- 关键部件在位
- 磁盘布局、RAID、网卡数量符合预期

至少检查：

```bash
hostname
lsblk
lspci
```

### 2. 管理网与 bond

确认：

- 管理网地址正确
- bond 配置正确
- 默认网关可达

至少检查：

```bash
ip addr
cat /proc/net/bonding/<bond-name>
ping <gateway>
```

如果这里不通过，不进入后续压测。

### 3. GPU/NPU 基础状态

确认：

- 设备数量符合预期
- `Persistence Mode` 已按要求启用
- 关键服务正常

至少检查：

```bash
nvidia-smi
nvidia-smi -L
nvidia-smi --query-gpu=persistence_mode --format=csv
systemctl status nvidia-fabricmanager
```

说明：

- 对英伟达系设备，`nvidia-fabricmanager` 是 A800/H100 等机型的重要前置项
- 对 910B 或其他专用平台，用对应工具替代，但验收逻辑相同：设备要在位、状态要稳定

### 4. IB / ROCE / 存储网络前置检查

确认：

- 存储网卡名字和对应关系正确
- 端口状态正常
- 存储挂载路径可用

至少检查：

```bash
ibdev2netdev
ibstat
mount | grep nvfile-data
```

如果是 ROCE 场景，再补：

```bash
ibv_devinfo
ip link
```

如果这里失败，转到专题文档：

- [gpu-server-ib-roce-network-recovery.md](/Users/huangliang/project/OneOPS-ALL/docs/runbooks/gpu-server-ib-roce-network-recovery.md)

### 5. 驱动依赖与 GPU 优化项

确认：

- 驱动与内核匹配
- `nvidia_peermem` 正常
- OFED / RDMA 依赖完整

至少检查：

```bash
lsmod | grep nvidia_peermem
modinfo nvidia_peermem
uname -r
```

对 A800 / H100，若 `nvidia_peermem` 缺失或异常，直接判为 `限制上线` 或 `不可上线`，不要贸然放行。

## 二、运行态检查

### 1. 平台状态

从 OneOPS 确认：

- 设备在线
- 监控接入正常
- 最近无新的硬件或系统级告警
- 日志中心没有持续报错

### 2. 本机运行态

确认：

- GPU/NPU 可稳定识别
- 系统盘和关键挂载正常
- 关键服务运行正常

至少检查：

```bash
df -h
systemctl status nvidia-fabricmanager
systemctl status zabbix-agent2
```

如果是存储型训练节点，还应检查共享目录是否正常访问。

### 3. 特殊机型提示

#### A800 / H100

重点关注：

- IB 对应关系
- `nvidia-fabricmanager`
- `nvidia_peermem`
- 存储网络和训练网络是否都健康

#### A10 / 4090

重点关注：

- bond 网络
- GPU 数量与在位
- CUDA 可用性

#### 910B

重点关注：

- NPU 在位
- 平台工具链是否正常
- 不要用英伟达命令作为唯一验收标准

## 三、压测与功能验证

### 1. NCCL / 多机通信验证

适用场景：

- 多机多卡训练节点
- A800 / H100 / 有通信依赖的 GPU 集群

验收目标：

- 多机通信链路通
- 没有明显 NCCL 报错
- 性能没有异常抖动

如果本阶段失败，不判定为 `可上线`。

### 2. GPU 压测

建议目标：

- GPU 使用率能稳定拉起
- 长时间运行无掉卡、无异常报错

可选方式：

- `gpu_burn`
- 模型压测

注意：

- 压测前必须确保驱动和 CUDA 匹配
- 压测期间需要观察 GPU 利用率、温度和错误

### 3. CPU / 内存测试

适用场景：

- 重装后
- 更换内存 / CPU 后
- 机器有历史不稳定记录时

目标：

- 短时压力下无明显异常
- 不出现新的系统告警或错误

### 4. DCGM 检测

适用场景：

- 怀疑 GPU 健康度问题
- 交付前需要补一轮较强诊断

原则：

- 作为增强验证，不是所有机器每天都跑
- 结果异常时，降级为 `限制上线` 或转故障响应

## 四、上线结论

### 可上线

满足以下条件：

- 静态配置正确
- 运行态稳定
- 无未收口严重告警
- 关键验证通过
- 业务侧或交付侧确认可接管

### 限制上线

适用于：

- 机器基本可用，但仍有待观察项
- 某些增强测试未做或结果边界不清
- 存在已知限制，但不阻断当前计划用途

必须记录限制项和复查时间。

### 不可上线

适用于：

- 关键配置错误
- GPU/NPU、网络或存储状态异常
- 压测或通信验证失败
- 存在持续告警或不稳定现象

这时转到：

- [gpu-server-fault-response.md](/Users/huangliang/project/OneOPS-ALL/docs/runbooks/gpu-server-fault-response.md)

## 五、证据归档

每次巡检或上线检查至少保留：

- OneOPS 告警与日志截图
- 本机关键命令输出
- 压测或验证结果
- 最终结论
- 是否已通知业务或交付方

建议在 OneOPS 或配套记录中统一保存：

- 设备编码
- 检查时间
- 检查人
- 结论等级
- 风险备注
- 复查计划

## 六、与其他 Runbook 的边界

这份文档回答的是“能不能上线”。

如果你要处理的是“为什么坏了、怎么恢复”，转到：

- [gpu-server-fault-response.md](/Users/huangliang/project/OneOPS-ALL/docs/runbooks/gpu-server-fault-response.md)

如果你要处理的是“IB/ROCE 怎么修”，转到：

- [gpu-server-ib-roce-network-recovery.md](/Users/huangliang/project/OneOPS-ALL/docs/runbooks/gpu-server-ib-roce-network-recovery.md)

如果你要处理的是“带外怎么取证和报厂商”，转到：

- [gpu-server-bmc-and-vendor-evidence-collection.md](/Users/huangliang/project/OneOPS-ALL/docs/runbooks/gpu-server-bmc-and-vendor-evidence-collection.md)

如果你要处理的是“系统怎么重装和恢复基线”，转到：

- [gpu-server-os-reinstall-and-baseline.md](/Users/huangliang/project/OneOPS-ALL/docs/runbooks/gpu-server-os-reinstall-and-baseline.md)
