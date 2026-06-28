# OneOPS 真实设备测试文档索引

## 1. 目的

这组文档用于把 OneOPS 第一阶段“围绕真实设备做针对性测试”的方法沉淀成统一入口。

它不是几份零散的冒烟脚本，而是后续各领域共同复用的测试底座：

1. 先明确测试目标和验证边界
2. 再用可重复拓扑承载真实设备场景
3. 再把采集、监控、解析、策略、拓扑、脚本等能力链挂到同一场景上
4. 最后用证据和边界来判断是否真的“支持某类设备”

## 2. 文档地图

建议阅读顺序如下：

1. [Testing Objective Basis](/Users/huangliang/project/OneOPS-ALL/docs/superpowers/testing/platform-testing-baseline/testing-objective-basis.md)
   记录用户原话和我们达成的一致理解，是第一阶段测试的最高依据。
2. [EVE-NG 当前测试环境准备总览](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-current-environment-preparation-summary.md)
   汇总当前 `192.168.100.20` 这台 EVE 上已经完成的拓扑底座、已就绪设备线、边界设备线和服务器替代路线，是当前环境盘点的统一入口。
3. [第一阶段真实设备测试矩阵](/Users/huangliang/project/OneOPS-ALL/docs/testing/phase1-real-device-test-matrix.md)
   把第一阶段的测试对象、能力链、场景重点、薄弱点和优先级整理成统一矩阵，后续新增设备家族时直接按这份矩阵扩展。
4. [第一批联合场景可执行测试清单](/Users/huangliang/project/OneOPS-ALL/docs/testing/phase1-first-batch-executable-checklist.md)
   把第一阶段矩阵进一步落成可以直接执行的联合场景清单，明确每条场景的设备组合、验证目标、关键证据、薄弱点和退出标准。
5. [A1 单设备接入基线回执（第一版）](/Users/huangliang/project/OneOPS-ALL/docs/testing/phase1-a1-single-device-baseline-receipt-v1.md)
   记录 `A1` 当前第一版回执，把本轮在线实测设备与既有直接实证设备分开整理，并明确当前未完成项、漂移项和下一步补齐动作。
6. [A1 逐设备标准回执](/Users/huangliang/project/OneOPS-ALL/docs/testing/phase1-a1-per-device-standard-receipts.md)
   把 `A1` 继续展开到逐设备粒度，统一记录标准管理模型、标准登录基线、当前证据状态、支持边界和下一步补证重点。
7. [A1 最小监控任务补证标准](/Users/huangliang/project/OneOPS-ALL/docs/testing/phase1-a1-minimal-monitoring-task-evidence.md)
   把 `A1` 中“最小监控任务”怎么选、怎么验、至少要保留哪几层证据固定下来，避免把“任务创建成功”误记成“监控已通过”。
8. [A1 H3C VFW 最小监控任务回执（待实测）](/Users/huangliang/project/OneOPS-ALL/docs/testing/phase1-a1-h3c-vfw-minimal-monitoring-receipt-v1.md)
   把当前最顺的第一条执行对象 `H3C VFW` 先起好监控回执框架，后续真机补证时可直接回填四层证据。
9. [第一阶段设备登录凭据基线](/Users/huangliang/project/OneOPS-ALL/docs/testing/phase1-device-login-baseline.md)
   把主线设备的登录入口、标准账号口令、首登改密规则和 SSH 兼容性例外集中收敛，后续场景回执应优先引用这份基线。
10. [EVE-NG 拓扑生命周期操作验证记录](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-topology-lifecycle-validation.md)
   说明 EVE API 在当前环境中哪些动作已经实测通过，哪些地方有坑。
11. [EVE-NG `bridge` 到 `pnet0` 最小拓扑模板](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-bridge-pnet0-boundary-template.md)
   说明为什么推荐“内部 `bridge` + 边界设备 + 外联 `pnet0`”这个共同模型。
12. [EVE-NG 第一条真实场景运行手册：`bridge + boundary + pnet0`](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-first-scenario-bridge-boundary-pnet0-runbook.md)
   给出可以直接照着搭建和验证的第一条场景。
13. [EVE-NG 管理网关拓扑标准](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-mgt-gateway-topology-standard.md)
   记录网关设备、业务网络设备、带外管理、三层地址和清理规则。
14. [EVE-NG Cisco 网关交换机标准操作手册](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-cisco-gateway-standard-operation.md)
   记录 Cisco 网关交换机的创建规格、基础配置、SSH 配置和验证步骤。
15. [EVE-NG Huawei AR 路由器标准操作手册](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-huawei-ar-router-standard-operation.md)
   记录 Huawei AR 路由器的首登、管理口映射、`MGT` 实例、SSH 配置和已知边界。
16. [EVE-NG H3C VSR 路由器标准操作手册](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-h3c-vsr-router-standard-operation.md)
   记录 H3C VSR 路由器的 `20` 口规格、`GE20/0` 管理口、统一口令所需密码策略和 SSH 兼容参数。
17. [EVE-NG Huawei USG 防火墙标准操作手册](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-huawei-usg-firewall-standard-operation.md)
   记录 Huawei USG 防火墙的默认账号、强制改密、`MGT` 管理口、SSH 持久化复验、`HTTP/HTTPS` 管理面现状，以及 `20` 口扩展边界。
18. [EVE-NG Huawei USG 策略与 NAT 实机验证记录](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-huawei-usg-policy-nat-live-validation.md)
   记录 Huawei USG 在真实设备上对业务接口、安全域、地址对象、服务对象、`permit/deny security-policy`、`DNAT`、`SNAT easy-ip`、`SNAT_POOL` 的最小落证结果，并明确当前 `DNAT` 与平台既有 `destination-zone` 假设之间的冲突边界，以及 `nat-policy` 命名模板的已发现薄弱点。
19. [EVE-NG Huawei USG 防火墙标准模板](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-huawei-usg-firewall-standard-template.md)
   把 Huawei USG 当前已经实证的管理面、对象、`permit/deny policy`、`DNAT`、`SNAT` 收敛成可直接复用的标准模板，并明确哪些字段已经可以参数化，哪些仍属于平台或厂商边界。
20. [EVE-NG H3C VFW 防火墙标准操作手册（草案）](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-h3c-vfw-firewall-standard-operation.md)
   记录 H3C VFW 当前已经打通的最小管理面模型，包括 `Management <-> Local` 放行、`ACL + zone-pair` 配置、管理地址和复验方法。
21. [EVE-NG H3C VFW 防火墙边界排查记录](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-h3c-vfw-firewall-boundary-investigation.md)
   记录 H3C VFW 从“控制面未通”到“最小管理面模型已找到”的完整排查过程，以及当前剩余的模板化边界。
22. [EVE-NG Ruijie 防火墙离线启动模板标准操作](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-ruijie-firewall-offline-startup-template-standard.md)
   记录锐捷防火墙当前可复用的离线启动模板路径，并明确当前共享标准为 `Ge0/0 + main`，不把 `VRF` 作为可交付支持能力。
23. [EVE-NG Ruijie 防火墙首轮初始化与边界记录](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-ruijie-firewall-initialization-boundary.md)
   记录锐捷防火墙的默认登录、首口管理模型、官方备份包回灌链路、离线改写 `LYB` 启动模板的实证结果，以及“不纳入 `VRF` 支持范围”的边界结论。
24. [EVE-NG Ruijie 防火墙 Web API 能力与边界](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-ruijie-firewall-web-api-capability-boundary.md)
   记录锐捷防火墙本机 Web 管理面的后端结构、`/api/v1` 接口主干、登录与 session 模型，以及“内部 Web API 不等于官方公开 OpenAPI”的判断依据。
25. [EVE-NG Ruijie 防火墙 OneOPS 适配候选矩阵](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-ruijie-firewall-oneops-adaptation-candidate-matrix.md)
   把锐捷防火墙当前已发现的本机 Web API 按 OneOPS 的采集、监控、策略、拓扑、诊断和自动化能力链重新整理成优先级清单。
26. [EVE-NG Ruijie 防火墙 P0 结构化采集合同](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-ruijie-firewall-p0-collection-contract.md)
   把 `interface` 与 `network_router` 两组只读接口整理成字段级采集合同，明确请求参数、核心返回字段、OneOPS 映射与 live 验证点。
27. [EVE-NG Ruijie 防火墙 P0 接口实测回执](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-ruijie-firewall-p0-live-validation.md)
   记录 `2026-06-28` 对 Ruijie Web 登录链路、接口面、路由面做的第一轮真实调用结果，明确哪些接口已打通、哪些返回空但正常、哪些当前存在实现问题。
28. [EVE-NG Linux Server 标准操作手册](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-linux-server-standard-operation.md)
   记录 Ubuntu Server 模板的离线账号标准化、静态管理地址、SSH、`sudo` 和重启复验结果。
29. [EVE-NG Debian Server 标准操作手册](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-linux-debian-server-standard-operation.md)
   记录 Debian 10 模板的离线账号标准化、静态管理地址、DNS / `apt archive` 收敛、`sudo` 安装与重启复验结果。
30. [EVE-NG Kylin Server 标准操作手册](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-linux-kylin-server-standard-operation.md)
   记录 Kylin V11 模板的离线账号标准化、静态管理地址、SSH、`sudo`、重启复验，以及当前串口控制台边界。
31. [EVE-NG Linux RHEL Server 首轮初始化与边界记录](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-linux-rhel-server-boundary-investigation.md)
   记录 RHEL 8.4 镜像在当前 EVE 上已确认的账号/网络离线标准化能力，以及当前 `ARP/ICMP/SSH/Console` 未收敛、独立 overlay probe 也停在 `firewalld` 启动阶段附近的运行态边界。
32. [EVE-NG Rocky Linux Server 准备方案](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-linux-rocky-server-preparation-plan.md)
   记录为什么要用 Rocky 9 GenericCloud 替代当前旧 RHEL 8.4 路线，以及官方镜像下载、EVE 导入、标准化和首轮验证的共同入口。
33. [EVE-NG 设备初始化模板标准](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-device-initialization-template-standard.md)
   统一不同设备的初始化模板结构、通用要求和第一批设备矩阵。
34. [EVE-NG 第一批设备候选清单](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-phase1-available-device-candidates.md)
   记录当前 `192.168.100.20` 上真实存在、可直接用于第一阶段测试的设备镜像。
35. [EVE-NG Cisco ASAv 防火墙标准操作手册](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-cisco-asav-firewall-standard-operation.md)
   记录 Cisco ASAv 当前已经实证可复用的恢复启动、`Mgmt0/0` 管理配置、SSH、`enable` 与重启复验路径。
36. [EVE-NG Cisco ASAv 防火墙首轮初始化与边界记录](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-cisco-asav-firewall-initialization-boundary.md)
   记录 Cisco ASAv 为什么会卡在 `enable_1/priv 1`、为什么必须走恢复启动，以及密码策略、首次 SSH 改密、`tmp` 覆盖目录复用等关键边界。

## 3. 统一方法

无论后续扩展到网络设备、服务器设备还是防火墙设备，都先复用同一条骨架：

1. 用 EVE 建一条最小可重复拓扑
2. 在拓扑里放入目标真实设备或最接近的设备镜像
3. 先验证数据面和边界设备本身
4. 再把 OneOPS 的能力链逐段挂进去
5. 最后记录“已验证能力”和“明确不支持边界”

## 4. 三类领域如何接这套底座

1. 防火墙设备
   优先验证配置采集、对象解析、策略生成、策略查询、NAT/ACL 命中和边界流量。
2. 网络设备
   优先验证接口/邻居/路由采集、SNMP/SSH 双通道、监控推送、拓扑生成和自动化脚本。
3. 服务器设备
   优先验证 SSH 采集、监控任务、脚本执行、资产识别，以及与网络边界的联动行为。

## 5. 每条场景都必须产出的证据

每次执行真实设备场景，至少保留以下证据：

1. 拓扑定义
2. 节点和网络的 EVE API 回读结果
3. 控制台配置和连通性结果
4. OneOPS 侧采集、监控或任务执行结果
5. 失败场景的实际报错和边界说明
6. 宿主机侧 `brctl show`、`bridge link`、`ip tuntap list` 排障证据

## 6. 后续扩展建议

后面新增任何设备家族时，建议都新增一份独立场景文档，并沿用下面这套结构：

1. 目标设备和目标能力链
2. 最小拓扑
3. 地址和接口规划
4. 分层验证步骤
5. 弱点分析点
6. 通过标准
7. 不支持边界
8. 清理步骤
