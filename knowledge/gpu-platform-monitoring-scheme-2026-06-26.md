# 平台 GPU 监控方案与现状实现分析

## 背景

本文档用于沉淀 OneOPS/ctrlhub 体系下 GPU 监控的现状、边界和推荐落地方案，避免后续把 GPU 运维问题简单等同为“服务器硬件监控问题”。

核心结论：

- GPU 监控主线应由 `nvidia_smi` 指标和 GPU 相关日志承担。
- IPMI 只作为辅助监控面，用于判断服务器硬件环境是否健康、是否发生重要硬件故障。
- 平台应把 GPU 本体、服务器硬件环境、故障日志三条信号汇聚成统一故障时间线。

## 一、ctrlhub agent 当前实现现状

### 1. GPU 指标采集

`ctrlhub agent` 已内置 `nvidia_smi` Telegraf 输入插件。

相关入口：

- `ctrlhub/controller/agent/cmd/agent/main.go`
- `telegraf/plugins/inputs/nvidia_smi/nvidia_smi.go`
- `telegraf/plugins/inputs/nvidia_smi/schema_v12/parser.go`

实现方式：

- 本机执行 `nvidia-smi -q -x`
- 根据 XML schema 版本解析输出
- 产出 `nvidia_smi` 与 `nvidia_smi_mig` measurement

当前已采集的关键字段包括：

- `utilization_gpu`
- `utilization_memory`
- `temperature_gpu`
- `memory_used`
- `memory_total`
- `memory_free`
- `power_draw`
- `fan_speed`
- `clocks_current_graphics`
- `clocks_current_sm`
- `clocks_current_memory`
- `pcie_link_gen_current`
- `pcie_link_width_current`
- MIG 显存相关字段

平台侧已有模板和策略种子：

- 模板：`teleabs/teleabs-templates/categories/infrastructure/system/nvidia_smi/nvidia_smi_basic.json`
- 套件种子：`quick_env/docker-entrypoint-initdb.d/zzzzzzzzz-current-mysql-seed-bootstrap.sql`

### 2. IPMI 指标与日志采集

`ctrlhub agent` 已内置 OneOPS 自定义 `oneops_ipmi` 插件。

相关入口：

- `ctrlhub/controller/agent/pkg/telegraf/plugins/inputs/oneops_ipmi/oneops_ipmi.go`
- `ctrlhub/controller/agent/pkg/telegraf/plugins/inputs/oneops_ipmi/sel_log_collector.go`

支持的 collector 包括：

- `ipmi`
- `dcmi`
- `bmc`
- `bmc_watchdog`
- `chassis`
- `sel`
- `sel_events`
- `sel_logs`
- `sm_lan_mode`

产出能力分两类：

- 指标：温度、风扇、电流、电压、功耗、BMC 信息、机箱供电状态、SEL 计数等
- 日志：`ipmi_sel_event_log`

其中 `sel_logs` 已实现以下能力：

- 本地游标持久化
- 首次 `latest` 引导
- 增量采集
- BMC 身份变更检测
- 单次最大发送条数限制
- 严重级别过滤

这意味着 IPMI 在平台里已经不只是“能采到”，而是具备了相对成熟的事件日志闭环能力。

### 3. 输出与标签附着

当前路由模式已经成型：

- IPMI 数值指标进入 Prometheus remote write
- `ipmi_sel_event_log` 单独进入 Loki

相关位置：

- `quick_env/docker-entrypoint-initdb.d/zz-platform-bootstrap.sql`
- `ctrlhub/controller/pkg/controller/loki_forwarder.go`

标签附着方面，`nvidia_smi`、`ipmi`、`oneops_ipmi` 已通过 attach processor 附着设备标签，例如：

- `tenant`
- `ip`
- `device_name`
- `hostname`
- `catalog`
- `site`
- `region`
- `rack`

相关位置：

- `quick_env/bin/oneops-telegraf/telegraf.conf`

## 二、当前实现的边界

### 1. `nvidia_smi` 能回答什么

它适合回答：

- GPU 是否存在
- GPU 利用率是否异常
- 显存是否压满
- 温度、功耗、风扇、时钟是否异常
- PCIe 链路是否降速
- MIG 显存视角是否异常

### 2. `nvidia_smi` 不能单独回答什么

它不能完整回答：

- 是否发生 `Xid`
- 是否出现驱动崩溃或 `GPU has fallen off the bus`
- `fabric manager` 是否异常
- 某 GPU 是否“在位但不可用”
- 故障是否由操作系统、驱动、内核模块、CUDA 运行时引起

### 3. IPMI 能回答什么

IPMI 适合回答：

- 风扇、电源、散热、机箱供电是否异常
- BMC 是否异常
- 是否有重要硬件告警进入 SEL
- 服务器硬件环境是否处于不健康状态

### 4. IPMI 不能代替 GPU 监控

IPMI 无法作为 GPU 主监控面，因为它通常不能直接给出：

- GPU 掉卡
- GPU 驱动异常
- ECC/Xid 故障本体
- 训练任务视角的性能退化

因此 IPMI 的正确定位是：

**辅助证明服务器硬件环境是否异常，而不是替代 GPU 本体监控。**

## 三、当前已暴露出的风险

### 1. `nvidia_smi` 存在字符串字段 remote write 丢弃问题

当前 `nvidia_smi` 解析会产出一批字符串字段，例如：

- `driver_version`
- `cuda_version`
- `display_mode`
- `display_active`
- `current_ecc`
- `vbios_version`
- `remapped_rows_pending`
- `remapped_rows_failure`

但 Prometheus remote write 只接受数值样本，因此实际运行日志里已经出现 dropped series。

相关证据：

- `tmp/telegraf.log`

这说明当前 GPU 面板和告警应优先依赖数值字段，不应依赖这些字符串字段的 remote write 结果。

### 2. GPU 故障日志面仍然缺失

相比 IPMI 已有 `ipmi_sel_event_log`，GPU 侧仍缺少统一日志面，至少还没有形成平台级的以下事件沉淀：

- `NVRM: Xid`
- `GPU has fallen off the bus`
- `RmInitAdapter failed`
- ECC 相关内核日志
- `nvidia-fabricmanager` 故障日志

这会导致 GPU 异常只能看到指标变化，但缺少日志级故障证据链。

## 四、平台 GPU 监控设计原则

### 1. 主监控面必须是 GPU 本体

平台在 GPU 场景下，最先要回答的是：

- 卡是否齐
- 卡是否忙
- 卡是否热
- 卡是否掉
- 卡是否存在驱动级故障

所以主监控面必须围绕 GPU 本体设计。

### 2. IPMI 只做辅助硬件环境判断

IPMI 的职责应明确收敛为：

- 判断服务器风扇、电源、散热、主板、供电是否健康
- 判断是否有重要硬件告警
- 为 GPU 故障提供硬件侧旁证

### 3. 指标、日志、运维动作要能串成一条时间线

真正可用的平台方案不应只给出一个图表，而应能串起：

1. GPU 指标异常
2. GPU 或系统日志异常
3. IPMI/SEL 硬件旁证
4. 平台告警
5. 任务中心采集与处置动作

## 五、推荐的监控方案

### 第一层：GPU 主监控面

基于现有 `nvidia_smi` 插件，作为每台 GPU 主机的标准基础监控。

建议采集频率：

- 生产默认：`60s`
- 高价值训练集群：`30s`

核心指标：

- 存活与数量
  - `nvidia_smi_utilization_gpu`
  - 按 `instance + index + uuid` 统计卡数
- 负载与容量
  - `nvidia_smi_utilization_gpu`
  - `nvidia_smi_utilization_memory`
  - `nvidia_smi_memory_used`
  - `nvidia_smi_memory_total`
- 健康与热状态
  - `nvidia_smi_temperature_gpu`
  - `nvidia_smi_power_draw`
  - `nvidia_smi_fan_speed`
- 性能退化信号
  - `nvidia_smi_clocks_current_graphics`
  - `nvidia_smi_clocks_current_sm`
  - `nvidia_smi_pcie_link_gen_current`
  - `nvidia_smi_pcie_link_width_current`
- MIG 场景
  - `nvidia_smi_mig` 相关显存字段

### 第二层：GPU 故障日志面

建议新增 GPU 专项日志采集，进入 Loki。

建议来源：

- `journald`
- `/var/log/messages`
- `/var/log/syslog`
- `nvidia-fabricmanager`
- `nvidia-persistenced`

建议匹配关键词：

- `NVRM: Xid`
- `GPU has fallen off the bus`
- `RmInitAdapter failed`
- `ECC`
- `fabric manager`
- `NVLink`
- `SXid`

日志面目标：

- 提供 GPU 故障证据
- 作为告警注释或事件时间线来源
- 为 runbook 和 RCA 提供可检索上下文

### 第三层：IPMI 辅助硬件环境监控

GPU 主机统一绑定 `server_oob_ipmi` 或等价策略，collector 至少启用：

- `ipmi`
- `dcmi`
- `bmc`
- `chassis`
- `sel_logs`

重点关注：

- `ipmi_temperature`
- `ipmi_fan_speed`
- `ipmi_power`
- `ipmi_dcmi_power_consumption`
- `ipmi_chassis_power`
- `ipmi_bmc`
- `ipmi_sel_event_log`

定位目标：

- 判断是否存在散热故障
- 判断是否存在供电异常
- 判断是否出现机箱级或主板级故障
- 为 GPU 故障提供硬件环境旁证

## 六、告警分层建议

### P1：强故障

- 采集不到任一 GPU 指标，且主机本应是 GPU 主机
- GPU 卡数低于期望值
- GPU 日志中出现 `Xid`、`fallen off the bus`、严重 ECC
- `ipmi_chassis_power_state == 0`
- `ipmi_sel_event_log` 出现 critical 级硬件告警

### P2：高风险异常

- `nvidia_smi_temperature_gpu` 持续高温
- `nvidia_smi_memory_used / nvidia_smi_memory_total > 95%` 持续异常
- `nvidia_smi_pcie_link_gen_current` 长时间低于基线
- `ipmi_fan_speed_state >= warning`
- `ipmi_power_state >= warning`

### P3：趋势与容量类

- 长时低利用率空置 GPU
- 长时显存高占用
- 功耗异常抖动
- 风扇长期高转速但未到告警阈值

## 七、建议的大盘结构

建议拆成三个视图，而不是混成一张“硬件大盘”：

### 1. GPU 运行态大盘

- 每机 GPU 数量
- 每卡利用率
- 每卡显存占用
- 每卡温度
- 每卡功耗
- PCIe 链路状态

### 2. GPU 故障诊断大盘

- 最近 `Xid/ECC/fabric manager` 事件
- GPU 指标异常时间点
- 与任务执行、告警时间对齐

### 3. 服务器硬件环境大盘

- 风扇状态
- 功耗
- 机箱供电
- BMC 信息
- SEL 事件流

## 八、推荐落地顺序

### Phase 1：启用现有能力

- 启用 `nvidia-smi-basic`
- 绑定 GPU 监控套件
- 为 GPU 主机补齐带外 IPMI 监控
- 只用数值型 GPU 指标做面板和告警

### Phase 2：补 GPU 日志面

- 为 GPU 主机新增日志采集源
- 把 `Xid/ECC/驱动异常` 送入 Loki
- 建立 GPU 告警与日志联动

### Phase 3：修正 `nvidia_smi` 字段建模

- 将字符串状态改造成 tag 或枚举数值
- 避免 remote write 持续丢弃
- 清理无效 series

### Phase 4：增强 GPU 专项能力

- 视需要补充 DCGM 或更细粒度 GPU exporter
- 增加每进程、NVLink、throttle reason、ECC 细项
- 支撑训练集群更精细的容量和故障分析

## 九、结论

平台 GPU 监控不应被理解为“给 GPU 服务器加一个 IPMI 监控”。

正确的方案是：

- 用 `nvidia_smi` 监控 GPU 本体
- 用 GPU 日志监控驱动和故障事件
- 用 IPMI 监控服务器硬件环境

其中 IPMI 的职责非常明确：

**只为 GPU 运维提供辅助，表明服务器硬件环境是否受监控、是否发生了重要硬件故障。**

如果后续继续演进，平台应优先补齐 GPU 日志面和 `nvidia_smi` 字段建模问题，而不是继续扩大 IPMI 在 GPU 运维中的职责范围。
