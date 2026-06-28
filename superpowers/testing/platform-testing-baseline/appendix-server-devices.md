## Domain Scope

服务器设备在第一阶段重点覆盖以下链路：

1. 设备纳管
2. SSH 采集和身份识别
3. 监控推送和运行态指标
4. 自动化脚本执行
5. 与网络边界设备联动时的连通和访问路径验证

## Critical Journeys

- device ingest -> SSH collect -> monitor push
- device ingest -> IPMI / OOB collect -> monitor template selection
- server workload traffic -> boundary device -> external path verification
- automation script execute -> result parse -> rerun stability

## Device / Protocol / Capability Matrix

第一轮至少覆盖：

1. SSH
2. 基础主机指标监控
3. 只读脚本执行
4. 服务器到边界设备的访问路径

## Failure Modes And Boundaries

重点记录以下边界：

1. SSH 可登录但身份不稳定
2. 监控任务已建但指标未落地
3. 脚本可执行但结果解析不稳定
4. OOB / IPMI 无法在当前环境真实表达

## P0 / P1 / P2 Scenario List

P0：

1. 服务器 SSH 可达且身份稳定
2. 基础资源指标可被监控
3. 服务器经边界设备访问外联目标
4. 一条只读自动化脚本可重复执行

P1：

1. 多块网卡
2. 多类监控模板
3. 与网络拓扑结果交叉验证

P2：

1. 多台服务器批量纳管
2. 批量脚本执行
3. 高并发监控任务

## Fixture And Sample Requirements

至少准备：

1. SSH 凭据
2. 监控模板或指标期望清单
3. 只读脚本样例
4. 连通性和资源基线样例

## Local Integration And Real-World Validation

服务器类设备建议沿用同一条最小场景，但把内网测试节点逐步替换成轻量 Linux 或目标服务器镜像：

1. [共享入口](/Users/huangliang/project/OneOPS-ALL/docs/testing/README.md)
2. [EVE-NG 管理网关拓扑标准](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-mgt-gateway-topology-standard.md)
3. [EVE-NG `bridge` 到 `pnet0` 最小拓扑模板](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-bridge-pnet0-boundary-template.md)
4. [EVE-NG 第一条真实场景运行手册：`bridge + boundary + pnet0`](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-first-scenario-bridge-boundary-pnet0-runbook.md)

IPMI / OOB 一类能力如果 EVE 无法真实表达，应明确转入物理或专门实验环境验证，不要在当前文档里假装已覆盖。

## Gate Eligibility

一台服务器设备只有在下面几点同时满足时，才应进入“阶段性支持”：

1. SSH 采集稳定
2. 监控任务成功下发且能观测到数据
3. 自动化脚本至少完成一次可重复只读验证
4. 对无法在 EVE 中表达的 OOB 能力已单独标出边界
