# GPU 运维 SOP 源资料映射

## 背景

本文档用于说明 `tmp/运维团队SOP文档-202510.docx` 已被如何吸收进 OneOPS 文档体系。目标不是逐页转写，而是把原始手册拆成更适合长期维护、检索和执行的知识文档。

## 原始文档结构

原 SOP 共覆盖 12 个主题区：

1. 认识服务器
2. 服务器检查项
3. 服务器故障信息收集
4. 故障处理参考
5. 配置操作
6. 测试方法总结
7. 系统重装
8. 常用操作
9. 历史故障复盘
10. 129 项目故障解决
11. 天翼云防火墙放行配置
12. 安全 4A 授权延期

## OneOPS 转换原则

### 保留

- 可复用的故障分类与处理经验
- 值班现场需要的排障顺序
- 机型差异与关键检查点
- 常见系统命令与验证点

### 改写

- 以截图为主的说明改成文字动作
- 以 Zabbix/飞书/厂商门户为主的流程改成 OneOPS 主流程
- 以手工抄表为主的闭环改成“事件记录 -> 知识沉淀”

### 不直接迁移

- 纯硬件面板识图
- 大量带图片的拆机操作细节
- 明文口令、代理参数、飞书链接、外部账号信息
- 项目专属且难以通用化的个别操作

## 章节映射

### 一、认识服务器

处理方式：

- 不单独落成 OneOPS 文档主线
- 只在 runbook 中保留“识别机型/厂商/机柜/设备编码”的必要要求

原因：

- 原章主要依赖面板图和槽位图，图像依赖强
- 适合作为硬件培训资料，不适合作为值班 SOP 主体

### 二、服务器检查项

吸收方式：

- 合并到 [gpu-server-fault-response.md](/Users/huangliang/project/OneOPS-ALL/docs/runbooks/gpu-server-fault-response.md)
- 并拆出巡检与验收专题 [gpu-server-inspection-and-go-live-readiness.md](/Users/huangliang/project/OneOPS-ALL/docs/runbooks/gpu-server-inspection-and-go-live-readiness.md)

保留重点：

- IB 网卡名称核对
- GPU 持久化模式检查
- `nvidia_peermem` / OFED 依赖检查
- `nvidia-fabricmanager` 状态检查

### 三、服务器故障信息收集

吸收方式：

- 作为 runbook 的“证据采集”章节主来源
- 并拆出专题文档 [gpu-server-bmc-and-vendor-evidence-collection.md](/Users/huangliang/project/OneOPS-ALL/docs/runbooks/gpu-server-bmc-and-vendor-evidence-collection.md)

保留重点：

- 从监控 / 告警入口确认症状
- 带外收集 SN、风扇、电源、GPU、RAID、日志
- 系统侧收集 GPU、网卡、硬盘、日志证据

改写重点：

- 优先用 OneOPS 的告警、日志、设备详情、任务中心、统一凭证
- Zabbix、带外系统、厂商日志导出改成兜底路径

### 四、故障处理参考

吸收方式：

- 作为 runbook 的“分类处置”章节主来源
- 作为 incident knowledge 的经验支撑

保留重点：

- GPU 掉卡 / ECC / GPU 更换
- IB 网卡 down / 网卡名异常 / 存储网挂载失败
- 风扇、电源、内存、CPU、硬盘、RAID、系统引导问题
- GPU 驱动 / Docker / NFS / BIOS 类问题

### 五、配置操作

吸收方式：

- 不做全量迁移
- 仅保留与故障处置直接相关的少量配置动作
- 与网络恢复强相关的内容拆到 [gpu-server-ib-roce-network-recovery.md](/Users/huangliang/project/OneOPS-ALL/docs/runbooks/gpu-server-ib-roce-network-recovery.md)

原因：

- 该章更像运维命令仓库，不是值班现场的首要路径
- 许多内容适合后续拆成专题 runbook

### 六、测试方法总结

吸收方式：

- runbook 中保留“修复后验证”最小闭环
- 并拆出上线门禁专题 [gpu-server-inspection-and-go-live-readiness.md](/Users/huangliang/project/OneOPS-ALL/docs/runbooks/gpu-server-inspection-and-go-live-readiness.md)

保留重点：

- NCCL 测试
- GPU 压测
- CPU / 内存 / DCGM 检查

### 七、系统重装

吸收方式：

- 已拆成专题文档 [gpu-server-os-reinstall-and-baseline.md](/Users/huangliang/project/OneOPS-ALL/docs/runbooks/gpu-server-os-reinstall-and-baseline.md)

处理原则：

- 将重装视为升级处置，不放进一线值班的默认操作
- 在专题文档中只保留阶段化恢复框架，不直接保留原始凭据或下载地址

### 八、常用操作

吸收方式：

- 只保留与故障响应直接相关的少量动作
- RDMA、ROCE、MTU 和持久化相关内容拆到 [gpu-server-ib-roce-network-recovery.md](/Users/huangliang/project/OneOPS-ALL/docs/runbooks/gpu-server-ib-roce-network-recovery.md)

保留重点：

- 带外账户 / 网络修复
- 交换机配置备份
- RDMA/ROCE 调优与重命名

### 九、历史故障复盘

吸收方式：

- 转化成知识库思路，而不是照抄原始案例
- 与事件记录表联动，沉淀故障模式文档

### 十到十二、项目专属与外围主题

处理方式：

- 本次不并入通用 GPU 故障 runbook
- 视需要后续拆专题文档

## 当前落地产物

本次转换当前输出六份文档：

- [gpu-ops-sop-source-map-2026-06-21.md](/Users/huangliang/project/OneOPS-ALL/docs/knowledge/gpu-ops-sop-source-map-2026-06-21.md)
- [gpu-server-fault-patterns-from-incident-log-2026-06-21.md](/Users/huangliang/project/OneOPS-ALL/docs/knowledge/gpu-server-fault-patterns-from-incident-log-2026-06-21.md)
- [gpu-server-fault-response.md](/Users/huangliang/project/OneOPS-ALL/docs/runbooks/gpu-server-fault-response.md)
- [gpu-server-bmc-and-vendor-evidence-collection.md](/Users/huangliang/project/OneOPS-ALL/docs/runbooks/gpu-server-bmc-and-vendor-evidence-collection.md)
- [gpu-server-ib-roce-network-recovery.md](/Users/huangliang/project/OneOPS-ALL/docs/runbooks/gpu-server-ib-roce-network-recovery.md)
- [gpu-server-os-reinstall-and-baseline.md](/Users/huangliang/project/OneOPS-ALL/docs/runbooks/gpu-server-os-reinstall-and-baseline.md)
- [gpu-server-inspection-and-go-live-readiness.md](/Users/huangliang/project/OneOPS-ALL/docs/runbooks/gpu-server-inspection-and-go-live-readiness.md)

## 后续建议

下一阶段如果要继续做知识库产品化，建议再拆 4 类专题：

- GPU 驱动 / 平台专用运行时专题
- 项目专属扩展专题，例如 129 项目、云防火墙、4A 授权
- 结构化知识标签与导入索引
