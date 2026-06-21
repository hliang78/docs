# GPU 服务器带外取证与厂商报障 Runbook

Date: 2026-06-21

## 目的

这份 runbook 用于 GPU/NPU 服务器发生硬件或疑似硬件故障时，指导值班同学通过带外管理系统和系统侧证据完成标准取证，并把材料整理成适合厂商或内部专家继续分析的包。

## 适用场景

适用于以下情况：

- GPU/NPU 掉卡、ECC、功耗异常、疑似硬件故障
- 风扇、电源、内存、CPU、硬盘、RAID、PCIe 部件异常
- 需要提交厂商 case
- 需要在换件、整机替换或升级前留存证据

## 原则

### OneOPS 先确认上下文，带外补硬件证据

先在 OneOPS 里确认：

- 设备编码、机型、项目、机柜位置
- 当前告警、日志、最近变更和相关任务
- 业务是否确认受影响

再进入带外系统补下面这类硬件证据：

- 服务器 SN
- GPU/NPU、风扇、电源、RAID、硬盘、内存、CPU 状态
- 带外事件日志
- 一键导出的黑盒日志

### 先证据，后换件

除非已经进入紧急恢复窗口，否则不要先拆机再补证据。换件前至少要留住：

1. 设备标识
2. 故障件定位
3. 带外状态截图
4. 系统侧辅助证据
5. 黑盒或日志包

## 取证清单

每次至少收集以下 8 类信息：

1. 设备基础信息
2. 故障时间线
3. OneOPS 告警和日志证据
4. 带外首页健康概览
5. 目标部件状态详情
6. 故障件 SN 或槽位证据
7. 带外日志导出
8. 系统侧补充命令输出

## 标准流程

### 1. 建立故障包

建议按这个目录收集：

```text
<date>-<device-code>-fault-evidence/
  01-oneops-alerts/
  02-bmc-overview/
  03-bmc-components/
  04-bmc-logs/
  05-system-commands/
  06-part-photos/
  07-vendor-summary.md
```

文件命名尽量包含：

- 日期时间
- 设备编码
- 证据类型

例如：

- `2026-06-21-0912-A800GPU05-bmc-gpu-status.png`
- `2026-06-21-0915-A800GPU05-nvidia-smi.txt`

### 2. OneOPS 侧先取证

先从 OneOPS 保存：

- 告警详情
- 设备监控异常曲线
- 日志中心相关日志
- 操作审计
- 最近执行过的任务记录

作用：

- 给厂商之外的内部排障同学一个统一上下文
- 避免只拿硬件截图，却不知道业务和平台现象

### 3. 带外首页与整机信息

无论什么品牌，先收这几类页面：

- 首页概览或系统概览
- 产品信息 / 系统信息
- SN、型号、固件版本
- 健康状态总览

如果厂商界面支持“一键收集”或“快捷访问日志”，优先先做一次完整导出。

### 4. 按故障域抓目标证据

#### GPU/NPU

至少保留：

- GPU/NPU 状态页
- 功耗、在位、健康状态
- GPU/NPU 对应 SN、BDF、槽位或物理位置

特别注意：

- 4090 类设备常常无法直接从带外或系统拿到 GPU SN，需要靠物理标签和槽位关系确认
- A800 / A10 / H100 往往可从带外或系统命令补足 SN
- 910B 要区分 NPU 与普通 GPU 语义

#### 风扇 / 电源 / 散热

至少保留：

- 风扇状态
- 转速异常或为 0 的页面
- 电源功率或状态页
- 温度异常页

#### 存储 / RAID / 硬盘

至少保留：

- RAID 卡状态
- 物理盘状态
- 逻辑盘状态

#### CPU / 内存 / PCIe / 网卡

至少保留：

- 部件状态页
- 错误标识或异常状态页

### 5. 导出带外日志

如果平台支持，优先导出：

- 黑盒日志
- 系统日志
- 串口日志
- IPMI 事件日志
- 审计日志

导出后记录：

- 日志类型
- 导出时间
- 对应故障设备

### 6. 系统侧补充命令

至少补这些命令输出：

```bash
nvidia-smi
nvidia-smi -L
nvidia-smi -q
lspci
dmidecode | head
lsblk
ip addr
dmesg | tail -n 200
journalctl -xe --no-pager | tail -n 200
```

如果是 IB 或存储问题，再补：

```bash
ibdev2netdev
ibstat
mount | grep nvfile-data
```

如果是 910B 或其他非英伟达平台，补对应厂商命令，但不要在文档里硬编码具体口令和下载地址。

## 厂商差异提示

### A800

常见带外取证重点：

- GPU 状态
- 风扇 / 电源 / 散热
- 一键黑盒日志
- GPU 或底板更换前后的 SN 拍照

### A10

注意差异：

- A10 低配机型部分 GPU SN 可能无法在带外拿到
- 需要结合系统命令或物理标签确认

### 4090

注意差异：

- GPU SN 通常依赖物理标签
- 带外更适合看功耗和槽位，而不是直接拿 SN

### 910B

注意差异：

- 重点对象是 NPU
- 冷重启无效时要尽早准备整机替换证据

## 换件拍照规范

涉及换 GPU、底板、风扇、电源等部件时，建议至少拍：

- 服务器 SN
- 故障件全貌
- 故障件标签 / SN
- 新旧件对照
- 故障槽位位置

如果是 GPU 更换，优先保证新旧件可区分，且放大后能识别标签。

## 厂商报障摘要模板

建议附一份简短摘要：

```md
# Vendor Summary

- Device: <device code>
- Model: <model>
- Impact: <business impact>
- First seen: <time>
- Current state: <still failing / recovered after reboot / intermittent>
- Suspected domain: <GPU / fan / PSU / RAID / NPU / IB>
- Actions already tried:
  - cold reboot
  - reseat / swap
  - driver check
- Attached evidence:
  - OneOPS alerts
  - BMC screenshots
  - BMC logs
  - system command outputs
  - part photos
```

## 什么时候停止自查并升级

出现以下情况时，建议停止继续本地试探，转厂商或更高等级支持：

- 同一部件重复故障
- 冷重启无效
- 带外已经明确显示硬件异常
- 需要拆机但部件定位仍不清
- 同批次多台机器出现类似症状

## 关联文档

- [gpu-server-fault-response.md](/Users/huangliang/project/OneOPS-ALL/docs/runbooks/gpu-server-fault-response.md)
- [gpu-server-ib-roce-network-recovery.md](/Users/huangliang/project/OneOPS-ALL/docs/runbooks/gpu-server-ib-roce-network-recovery.md)
- [gpu-server-os-reinstall-and-baseline.md](/Users/huangliang/project/OneOPS-ALL/docs/runbooks/gpu-server-os-reinstall-and-baseline.md)
