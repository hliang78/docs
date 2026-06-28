## Domain Scope

网络设备在第一阶段重点覆盖以下链路：

1. 设备纳管
2. SNMP / SSH 采集
3. 接口、邻居、路由、VLAN 等关键事实采集
4. 监控推送与数据入库
5. 拓扑生成和自动化脚本

## Critical Journeys

- device ingest -> SNMP collect -> monitor push -> runtime health
- device ingest -> SSH collect -> identity correction -> monitor push
- route / neighbor collect -> topology generation -> topology verification
- automation script execute -> command result parse -> boundary record

## Device / Protocol / Capability Matrix

第一轮至少覆盖：

1. SNMP
2. SSH / CLI
3. 接口与地址
4. 邻居与路由
5. 基础监控指标
6. 只读自动化命令执行

## Failure Modes And Boundaries

重点记录以下边界：

1. SNMP 可通但 SSH 不通
2. SSH 可采但身份纠偏不稳定
3. 接口数据存在但拓扑关系不完整
4. 监控任务下发成功但运行态指标为空

## P0 / P1 / P2 Scenario List

P0：

1. `pc-a / pc-b` 内网互通
2. `boundary inside` 接口状态和地址采集
3. `boundary outside` 接 `pnet0` 后的外联邻居或默认路由
4. SNMP 指标和控制台接口状态互证

P1：

1. LLDP 或路由邻居拓扑
2. 接口 flap / 计数器变化监控
3. 拓扑生成结果校验

P2：

1. 多接口多 VLAN
2. 多邻居多路由表
3. 大量监控项并发下发

## Fixture And Sample Requirements

至少准备：

1. SNMP 凭据
2. SSH 凭据
3. 设备控制台回显样例
4. 接口、邻居、路由的预期对照表

## Local Integration And Real-World Validation

网络设备建议从“边界设备接 `bridge` 和 `pnet0`”这条场景开始：

1. [共享入口](/Users/huangliang/project/OneOPS-ALL/docs/testing/README.md)
2. [EVE-NG 管理网关拓扑标准](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-mgt-gateway-topology-standard.md)
3. [EVE-NG `bridge` 到 `pnet0` 最小拓扑模板](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-bridge-pnet0-boundary-template.md)
4. [EVE-NG 第一条真实场景运行手册：`bridge + boundary + pnet0`](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-first-scenario-bridge-boundary-pnet0-runbook.md)

如果设备支持 SSH 和 SNMP 双通道，优先同时验证，不要只打一条通道。

## Gate Eligibility

一台网络设备只有在下面几点同时满足时，才应进入“阶段性支持”：

1. 至少一种主采集通道稳定
2. 接口和基础事实采集可信
3. 监控任务成功下发且有有效数据
4. 拓扑关系能和实验设计相互印证
5. 自动化脚本至少完成一次只读验证
