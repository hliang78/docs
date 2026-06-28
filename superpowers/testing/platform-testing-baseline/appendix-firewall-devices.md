## Domain Scope

防火墙设备在第一阶段重点覆盖以下链路：

1. 设备纳管和配置采集
2. 安全域、接口、对象、策略、NAT 解析
3. 策略生成和策略查询
4. 监控推送与运行态验证
5. 自动化脚本的只读验证和可回滚小变更验证

## Critical Journeys

- page import -> online collection -> fact parse -> detail/read-model verification
- config/object workflow -> precheck execute -> collection result render
- internal flow -> policy query -> expected hit explanation
- internal flow -> policy generate -> rendered workorder / command preview
- inside -> outside flow -> NAT / ACL / route boundary verification

## Device / Protocol / Capability Matrix

第一轮至少覆盖：

1. SSH / CLI 配置采集
2. 配置文本解析
3. 安全域 / 地址对象 / 服务对象 / 策略 / NAT
4. 监控基础能力
5. 只读自动化命令执行

## Failure Modes And Boundaries

重点记录以下边界：

1. 可采集但解析不完整
2. 可解析但策略查询和真实命中不一致
3. 可生成策略但工单或命令不可执行
4. 可建监控任务但设备侧没有有效指标

## P0 / P1 / P2 Scenario List

P0：

1. `pc-a -> pc-b`
2. `pc-a -> 外部目标`
3. 一条明确应拒绝的流

P1：

1. 多安全域
2. NAT 与非 NAT 混合流
3. 策略查询与生成交叉验证

P2：

1. 大对象集
2. 大策略集
3. 多次重复采集后的稳定性验证

## Fixture And Sample Requirements

至少准备：

1. 一份控制台真实配置
2. 一份采集后的原始配置快照
3. 三类流量样例：允许、拒绝、出网
4. 解析结果与真实配置的对照证据

## Local Integration And Real-World Validation

防火墙类设备建议统一从这条真实场景起步：

1. [共享入口](/Users/huangliang/project/OneOPS-ALL/docs/testing/README.md)
2. [EVE-NG 管理网关拓扑标准](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-mgt-gateway-topology-standard.md)
3. [EVE-NG `bridge` 到 `pnet0` 最小拓扑模板](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-bridge-pnet0-boundary-template.md)
4. [EVE-NG 第一条真实场景运行手册：`bridge + boundary + pnet0`](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-first-scenario-bridge-boundary-pnet0-runbook.md)

每次执行都应把“控制台真实配置”和“平台解析结果”并排比对，避免只验证平台侧输出。

当前已确认的一条厂商边界需要全员共享：

1. `Ruijiefirewall-V1.03` 当前标准管理模型固定为 `Ge0/0 + main`。
2. 这条镜像不纳入 OneOPS 当前阶段的 `VRF` 支持范围。
3. 围绕锐捷防火墙的采集、解析、策略、监控与自动化测试，都应先基于这条管理模型推进，不要把“独立管理 `VRF`”当作前置条件。
4. 该设备当前已确认存在本机 Web 内部 API，但还不应视为已确认的官方公开 OpenAPI；对接策略仍应以 `SSH/CLI` 主通道为准。
5. 截至 `2026-06-28`，Ruijie 防火墙标准化模板已完成收口，后续对它的推进应视为增强适配，而不是基础模板补课。

当前还需要同步另一条 Huawei USG 厂商事实：

1. `Huawei USG` 的地址对象、服务对象与 `permit/deny security-policy` 已经在真实设备上落证，不能再把它停留在“只有初始化，没有配置面验证”的阶段。
2. `Huawei USG DNAT` 也已落证，但当前真实设备不接受“`destination-zone + action destination-nat ...`”这类平台既有假设。
3. `Huawei USG SNAT` 也已落证，而且当前至少确认了两条真实可用路径：`easy-ip` 与 `address-group`。
4. 因此围绕 `Huawei USG` 的 OneOPS 适配，应把 `nat-policy` 真实设备语法收敛列为专项。
5. 平台生成与设备落配置一致性，应作为 `Huawei USG` 的主验证项之一。
6. 策略查询结果与真实配置块对照，应继续作为 `Huawei USG` 的主验证项之一。
7. 当前定向单测虽为绿色，但日志已经暴露 `nat-policy` 规则名称模板存在 `NAT_POLICY` 变量求值异常，这类“未红但不稳”的点也应纳入第一阶段薄弱环节跟踪。

## Gate Eligibility

一台防火墙设备只有在下面几点同时满足时，才应进入“阶段性支持”：

1. 配置可稳定采集
2. 关键对象和策略可解释
3. 至少一条允许流和一条拒绝流得到实证
4. 失败项有清晰边界，不是模糊异常
