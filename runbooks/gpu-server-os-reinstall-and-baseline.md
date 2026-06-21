# GPU 服务器系统重装与基线恢复 Runbook

Date: 2026-06-21

## 目的

这份 runbook 用于 GPU 服务器进入系统重装、重建或重大基线修复场景时，提供一套 OneOPS 化的恢复框架。它不替代机型厂商手册，而是帮助值班和交付同学把“重装”这件事拆成可执行的阶段与验收点。

## 什么时候进入本 runbook

只在以下情况进入：

- 服务器无法正常启动，且常规修复无效
- RAID / 系统盘 / 引导损坏
- 驱动、内核、网络基线已经不可修补
- 更换关键硬件后，需要重建系统环境
- 业务和运维已确认进入重装窗口

## 重要边界

### 这是升级处置，不是一线默认动作

系统重装会引入明显风险：

- 业务中断
- 配置丢失
- 网络和驱动不一致
- 重装后仍需重新验收

因此必须满足：

1. 业务确认停机窗口
2. 当前配置、日志、证据已备份
3. OneOPS 中已记录重装原因和责任人

### 不在文档中硬编码敏感凭据

原始 SOP 中出现的口令、代理、脚本地址、下载地址，不在本 runbook 中直接保留。实际执行时通过：

- OneOPS 统一凭证
- 配置管理
- 受控制品仓库
- 内部交付包

来获取。

## 重装前检查

### 1. 确认输入

重装前必须明确：

- 设备编码
- 机型
- 操作系统目标版本
- 是否需要 GPU 驱动、CUDA、OFED、Zabbix、EDR、基线 agent
- 是否有 bond / IB / ROCE / 存储网络要求
- 是否要恢复旧 IP、主机名、项目标签

### 2. 备份现状

至少备份：

- OneOPS 设备详情和归属信息
- 网络配置
- 当前磁盘分区和挂载信息
- 驱动版本
- 关键配置文件
- 相关日志与故障证据

### 3. 确认验收人

至少有两个验收视角：

- 技术验收：系统、驱动、网络、监控是否恢复
- 业务验收：训练或业务任务是否恢复

## 标准阶段

### 阶段 A：裸机与磁盘准备

目标：

- 确认硬件已稳定
- RAID / 磁盘布局正确
- 可以进入操作系统安装流程

至少检查：

- 磁盘和 RAID 状态
- 启动顺序
- 带外挂载介质是否正常
- 目标镜像是否正确

如果硬件层面仍不稳定，不要继续系统安装。

### 阶段 B：安装最小系统

建议原则：

- 优先最小化安装
- 避免同时引入过多不必要组件
- 先拿到一个稳定可登录、可联网、可管理的基础系统

安装完成后立即检查：

```bash
uname -r
lsblk
ip addr
hostname
df -h
```

### 阶段 C：基础网络恢复

这是最容易漏、也最影响后续的阶段。

至少确认：

- 主机名
- 管理网
- bond 配置
- 默认网关
- 关键 DNS / 路由

如果是 A800/H100 等 IB 组网机型，还要明确：

- 是否需要 OFED
- 是否需要单独 IB 地址
- 存储网络和业务网络的边界

网络恢复完成后至少做：

```bash
ping <gateway>
ip addr
cat /proc/net/bonding/<bond-name>
```

### 阶段 D：驱动和运行时恢复

按机型需要恢复：

- GPU 驱动
- CUDA
- `nvidia-fabricmanager`
- OFED / openibd
- 其他平台专用驱动或 SDK

原则：

1. 内核和驱动版本先对齐
2. 先驱动，再运行时
3. 每做完一层就验证，不要把所有东西堆到最后一次性排错

至少检查：

```bash
nvidia-smi
nvcc -V
systemctl status nvidia-fabricmanager
ibstat
```

### 阶段 E：运维与安全基线恢复

按环境要求恢复：

- OneOPS 所需 agent / 监控接入
- 操作系统基线
- EDR / 安全 agent
- 标准用户和 sudo 权限

这里不要手工散落配置，优先走：

- OneOPS 任务模板
- OneOPS 配置管理
- 受控初始化脚本

### 阶段 F：业务前验证

技术侧至少完成：

- 系统正常启动
- 网络正常
- GPU/NPU 识别正常
- 存储挂载正常
- 监控接入正常
- 关键服务正常

验证建议：

```bash
nvidia-smi
nvidia-smi --query-gpu=persistence_mode --format=csv
mount | grep nvfile-data
systemctl status nvidia-fabricmanager
systemctl status zabbix-agent2
```

### 阶段 G：业务验收

按环境选择：

- NCCL 测试
- GPU burn
- DCGM 检测
- 业务方真实任务试跑

没有业务验收时，不要写成“已完全恢复”。

## 按机型差异

### A800 / H100

重点：

- OFED
- `nvidia_peermem`
- `nvidia-fabricmanager`
- IB 存储网络

### A10 / 4090

重点：

- GPU 驱动与 CUDA
- bond 网络
- ROCE 或普通以太网络验证

### 910B 或其他专用平台

重点：

- 专用驱动 / SDK / 工具链
- NPU 在位与通信验证
- 不要混用英伟达验证套路

## 验收清单

重装完成后，建议逐项勾掉：

- 系统版本正确
- 启动正常
- 磁盘布局正确
- 主机名正确
- 管理网正常
- bond 或业务网正常
- 存储网正常
- GPU/NPU 正常识别
- 驱动与运行时正常
- 监控与 agent 正常
- 基线恢复完成
- 业务验证通过

## 什么时候停止并回退

出现以下情况时，不要硬推后续步骤：

- 硬件仍不稳定
- 驱动与内核持续不匹配
- 网络配置无法收敛
- 同机型已有标准镜像或标准化流程，但当前做法明显偏离

这时应暂停并回到：

- 厂商支持
- 平台标准镜像
- 交付负责人
- OneOPS 配置基线模板

## 关联文档

- [gpu-server-inspection-and-go-live-readiness.md](/Users/huangliang/project/OneOPS-ALL/docs/runbooks/gpu-server-inspection-and-go-live-readiness.md)
- [gpu-server-fault-response.md](/Users/huangliang/project/OneOPS-ALL/docs/runbooks/gpu-server-fault-response.md)
- [gpu-server-ib-roce-network-recovery.md](/Users/huangliang/project/OneOPS-ALL/docs/runbooks/gpu-server-ib-roce-network-recovery.md)
- [gpu-server-bmc-and-vendor-evidence-collection.md](/Users/huangliang/project/OneOPS-ALL/docs/runbooks/gpu-server-bmc-and-vendor-evidence-collection.md)
