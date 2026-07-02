# 第一阶段网络设备主线执行 Runbook

更新时间：2026-06-29  
适用环境：`192.168.100.20` 上的 EVE-NG Community `6.2.0-4`

## 1. 目的

这份 Runbook 只回答一件事：第一阶段网络设备主线场景如何按统一顺序执行、放行和收尾。

本文件只服务于这条冻结主线：

1. OneOps 视角
2. EVE 底座
3. 文档先行
4. 严格按 `采集 -> 监控 -> 拓扑` 放行

## 2. 上层依据

执行前必须先锁定以下基线，不允许现场改口径：

1. [第一阶段网络设备主线标准场景](/Users/huangliang/project/OneOPS-ALL/docs/testing/phase1-network-mainline-standard-scenario.md)
2. [第一阶段网络设备主线地址与端口分配](/Users/huangliang/project/OneOPS-ALL/docs/testing/phase1-network-mainline-addressing-and-port-map.md)
3. [EVE-NG 拓扑生命周期操作验证记录](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-topology-lifecycle-validation.md)
4. [EVE-NG `bridge` 到 `pnet0` 最小拓扑模板](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-bridge-pnet0-boundary-template.md)
5. [EVE-NG 管理网关拓扑标准](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-mgt-gateway-topology-standard.md)
6. [EVE-NG Cisco 网关交换机标准操作手册](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-cisco-gateway-standard-operation.md)
7. [EVE-NG Huawei AR 路由器标准操作手册](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-huawei-ar-router-standard-operation.md)
8. [EVE-NG H3C VSR 路由器标准操作手册](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-h3c-vsr-router-standard-operation.md)
9. [EVE-NG Linux Server 标准操作手册](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-linux-server-standard-operation.md)
10. [A1 最小监控任务补证标准](/Users/huangliang/project/OneOPS-ALL/docs/testing/phase1-a1-minimal-monitoring-task-evidence.md)
11. [第一阶段网络设备主线 EVE 底座实测回执（第一版）](/Users/huangliang/project/OneOPS-ALL/docs/testing/phase1-network-mainline-eve-baseline-live-validation-v1.md)
12. [OBS `controller + agent` 部署前置检查清单](/Users/huangliang/project/OneOPS-ALL/docs/testing/phase1-obs-controller-agent-precheck-checklist.md)

## 3. 场景冻结范围

本 Runbook 固定执行 `4+2+1` 第一波主线：

1. 业务路由设备：`R1`、`R2`、`R3`、`R4`
2. 业务服务器：`S1`、`S2`
3. 观测服务器：`OBS`
4. 管理网关交换机：`GW`
5. 接入交换机：`ACC1`、`ACC2`

执行边界固定如下：

1. `OBS` 部署 `controller + agent`，只走管理平面
2. `OBS` 固定按 `8 vCPU / 16G RAM` 起机
3. `GW` 负责 `pnet0` 外联和管理平面，不参加业务验证
4. `ACC1`、`ACC2` 只承接接入关系，不承接服务器业务网关
5. `R1` 固定承接 `172.32.101.254`
6. `R3` 固定承接 `172.32.102.254`
7. `R2`、`R4` 在 V1 不承接服务器业务网关，也不在对应服务器业务网段配置 IP

## 4. 总执行顺序

执行顺序固定为：

1. 建拓扑
2. 设备初始化复核
3. 管理平面连通性验证
4. 业务平面地址与 OSPF 配置
5. 采集基线
6. 监控基线
7. 拓扑基线
8. 关闭设备并清理拓扑

任何一步未过，都不能跳步继续。

## 5. 阶段门禁

主线门禁固定如下：

1. `采集不过，不进入监控`
2. `监控不过，不进入拓扑`
3. 每个阶段都必须产出回执
4. 回执不完整，视同该阶段未通过

推荐回执命名：

1. `建拓扑回执`
2. `初始化复核回执`
3. `管理连通性回执`
4. `业务地址与 OSPF 回执`
5. `采集基线回执`
6. `监控基线回执`
7. `拓扑基线回执`
8. `收尾清理回执`

固定回写目标：

1. `采集基线` 回写到 `/Users/huangliang/project/OneOPS-ALL/docs/testing/phase1-network-mainline-collection-receipt-v1.md`
2. `监控基线` 回写到 `/Users/huangliang/project/OneOPS-ALL/docs/testing/phase1-network-mainline-monitoring-receipt-v1.md`
3. `拓扑基线` 回写到 `/Users/huangliang/project/OneOPS-ALL/docs/testing/phase1-network-mainline-topology-receipt-v1.md`
4. 在 Task 3/4 的固定模板完成前，证据也必须按以上 3 个目标文件名收集，不允许现场新建临时命名文件

前置实测口径：

1. 在正式进入 `6.5 采集基线` 之前，应先参考 [第一阶段网络设备主线 EVE 底座实测回执（第一版）](/Users/huangliang/project/OneOPS-ALL/docs/testing/phase1-network-mainline-eve-baseline-live-validation-v1.md)
2. 若底座回执未满足“拓扑已成、初始化已成、管理面已通、业务地址与 OSPF 已通”四条，不进入 OneOps 正式回执阶段

## 6. 执行步骤

### 6.1 建拓扑

目标：

1. 在 EVE 上创建本次主线实验室
2. 按冻结位序完成节点、网络和接口连线
3. 把管理平面、接入平面、路由平面一次性摆正

执行要求：

1. 拓扑生命周期动作参照 [EVE-NG 拓扑生命周期操作验证记录](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-topology-lifecycle-validation.md)
2. `GW` 到 `pnet0` 的外联边界参照 [EVE-NG `bridge` 到 `pnet0` 最小拓扑模板](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-bridge-pnet0-boundary-template.md)
3. 管理底座参照 [EVE-NG 管理网关拓扑标准](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-mgt-gateway-topology-standard.md)
4. 设备、地址、接口位序严格服从 [第一阶段网络设备主线地址与端口分配](/Users/huangliang/project/OneOPS-ALL/docs/testing/phase1-network-mainline-addressing-and-port-map.md)
5. `OBS` 建点时必须显式核对资源规格为 `8 vCPU / 16G RAM`

核对点：

1. `GW` 已上联 `pnet0`
2. `GW` 已下联所有节点管理口
3. `ACC1` 只接 `S1`、`R1`、`R2`
4. `ACC2` 只接 `S2`、`R3`、`R4`
5. `R1/R2/R3/R4` 六条 `L3MESH` 链路齐全
6. `OBS` 只接管理口
7. `OBS` 节点规格已按 `8 vCPU / 16G RAM` 创建

放行条件：

1. EVE 回读的节点、网络、接口关系与冻结表一致
2. 没有临时换口
3. 没有把业务平面直接并到 `pnet0`

回执要求：

1. 记录 Lab 名称
2. 记录节点 ID
3. 记录双端链路核对结果
4. 记录 `OBS` 资源规格
5. 标注是否存在模板接口数量不足或接口名漂移

### 6.2 设备初始化复核

目标：

1. 确认每台设备已经按各自标准手册完成最小初始化
2. 确认管理口、登录口令、SSH 入口和基础命名已固定

执行要求：

1. 华为路由器参照 [EVE-NG Huawei AR 路由器标准操作手册](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-huawei-ar-router-standard-operation.md)
2. H3C 路由器参照 [EVE-NG H3C VSR 路由器标准操作手册](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-h3c-vsr-router-standard-operation.md)
3. Linux 服务器参照 [EVE-NG Linux Server 标准操作手册](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-linux-server-standard-operation.md)
4. `GW` 和交换机侧初始化参照 [EVE-NG Cisco 网关交换机标准操作手册](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-cisco-gateway-standard-operation.md)
5. `GW`、`ACC1`、`ACC2` 也必须完成各自标准初始化并可登录
6. `OBS` 进入 `controller + agent` 部署前，必须先过 [OBS `controller + agent` 部署前置检查清单](/Users/huangliang/project/OneOPS-ALL/docs/testing/phase1-obs-controller-agent-precheck-checklist.md)

核对点：

1. 业务网络设备管理口确实落在冻结位序的最后一个接口规则上
2. `GW` 明确不适用“最后一个接口”规则，按冻结管理网关基线执行
3. 管理地址与设备 ID 对齐，`GW` 例外为 `172.32.2.254/24`
4. `OBS` 已装好 `controller + agent`
5. `OBS` 不额外拉观测网
6. 各设备 SSH 或控制台入口可复现
7. `OBS` 资源规格仍为 `8 vCPU / 16G RAM`

放行条件：

1. 所有节点都能稳定登录
2. 所有管理地址都已固定
3. 没有设备把管理面误放到业务口
4. `OBS` 规格未被降配

回执要求：

1. 记录每台设备主机名
2. 记录管理接口名
3. 记录管理地址和默认网关
4. 记录登录入口是否通过
5. 记录 `OBS` 节点规格核对结果

### 6.3 管理平面连通性验证

目标：

1. 先证明带外管理面完整可用
2. 为 OneOps 采集、监控和 `OBS` 执行链打底

执行要求：

1. 除 `GW` 外，其余受管节点管理默认网关统一指向 `172.32.2.254`
2. `GW` 自身固定承接 `172.32.2.254/24`，不适用“管理默认网关统一指向 `172.32.2.254`”这条
3. `OBS` 到全部节点只走管理平面
4. 先验证管理口可达，再做平台动作

核对点：

1. `OBS -> GW/ACC1/ACC2/R1/R2/R3/R4/S1/S2` 管理地址可达
2. 关键设备 SSH 可达
3. 管理平面不依赖业务口和 OSPF

放行条件：

1. 全部管理地址连通
2. `OBS` 可作为后续统一执行入口

回执要求：

1. 记录管理地址探测结果
2. 记录 SSH 连通结果
3. 记录异常设备和处理结论

### 6.4 业务平面地址与 OSPF 配置

目标：

1. 完成服务器业务网段和路由 Full Mesh 地址落地
2. 完成 `R1/R2/R3/R4` 的 OSPF 收敛

执行要求：

1. 地址分配严格服从 [第一阶段网络设备主线地址与端口分配](/Users/huangliang/project/OneOPS-ALL/docs/testing/phase1-network-mainline-addressing-and-port-map.md)
2. `R1` 配置 `172.32.101.254`
3. `R3` 配置 `172.32.102.254`
4. `R2`、`R4` 不配置服务器业务网关 IP
5. `R1/R2/R3/R4` 六条 Mesh 链路全部进入 OSPF
6. 管理平面不得加入业务 OSPF

核对点：

1. `S1` 默认网关是 `172.32.101.254`
2. `S2` 默认网关是 `172.32.102.254`
3. 六条 `172.32.64.0/24` 到 `172.32.69.0/24` 链路地址全部生效
4. 四台路由器 OSPF 邻居全部建立

放行条件：

1. 服务器到各自网关可达
2. 四台路由器邻居和路由稳定

回执要求：

1. 记录服务器业务地址和网关
2. 记录六条 Mesh 链路地址
3. 记录 OSPF 邻居结果
4. 记录是否出现管理口误入 OSPF

### 6.5 采集基线

目标：

1. 在 OneOps 完成主线采集首轮基线
2. 回收身份、接口、邻居、路由等事实

执行要求：

1. 本主线最小采集对象范围固定包含 `R1`、`R2`、`R3`、`R4`、`ACC1`、`ACC2`、`S1`、`S2`
2. `R1`、`R2`、`R3`、`R4` 负责主干身份、接口、邻居、路由事实
3. `ACC1`、`ACC2`、`S1`、`S2` 至少要补齐足以核对冻结接入关系的接入侧事实
4. 采集结果必须能回对地址表、接口表、OSPF 事实和接入关系真值
5. `OBS` 只作为执行入口，不改变业务平面

核对点：

1. 设备身份信息正确
2. 接口数量和接口角色正确
3. OSPF 邻居可见
4. 路由学习结果可见
5. `ACC1/ACC2/S1/S2` 接入事实可见，且足以回对冻结接线关系

放行条件：

1. 形成可核对的采集回执
2. `采集不过，不进入监控`
3. 采集回执必须写回 `/Users/huangliang/project/OneOPS-ALL/docs/testing/phase1-network-mainline-collection-receipt-v1.md`

回执要求：

1. 记录采集时间
2. 记录固定对象清单：`R1`、`R2`、`R3`、`R4`、`ACC1`、`ACC2`、`S1`、`S2`
3. 记录身份、接口、邻居、路由、接入事实 5 类结果
4. 记录与冻结真值不一致的点

### 6.6 监控基线

目标：

1. 在采集通过后建立最小监控基线
2. 证明任务创建、任务下发、Agent 执行、结果回收链条可用

执行要求：

1. 只在采集回执通过后进入
2. 监控判断口径统一参照 [A1 最小监控任务补证标准](/Users/huangliang/project/OneOPS-ALL/docs/testing/phase1-a1-minimal-monitoring-task-evidence.md)
3. 监控对象最小范围固定覆盖 `R1`、`R2`、`R3`、`R4`
4. 监控入口依赖 `OBS` 上的 `controller + agent`

核对点：

1. 平台计划层成功
2. 平台任务层可见
3. Agent 运行层可见
4. 目标结果层至少出现一条可解释结果

放行条件：

1. 只做到“平台计划层 + 平台任务层”，不算监控通过
2. 做到“平台计划层 + 平台任务层 + Agent 运行层”，仍不算监控通过
3. 只有 4 层证据齐全，且至少有一条可解释目标结果，才算监控基线通过
4. `监控不过，不进入拓扑`
5. 监控回执必须写回 `/Users/huangliang/project/OneOPS-ALL/docs/testing/phase1-network-mainline-monitoring-receipt-v1.md`

回执要求：

1. 记录任务编号
2. 记录平台计划层结果
3. 记录平台任务层结果
4. 记录 Agent 运行层结果
5. 记录至少一条可解释目标结果
6. 若失败，明确失败落在哪一层

### 6.7 拓扑基线

目标：

1. 在监控通过后完成主线拓扑基线
2. 证明平台输出能回对真实连接和真实三层关系

执行要求：

1. 只在监控回执通过后进入
2. 平台拓扑必须同时回对路由 Full Mesh 和服务器接入关系
3. 管理平面不得被误判成业务拓扑主链
4. `ACC1`、`ACC2`、`S1`、`S2` 的接入侧事实未达到可核对冻结关系的程度时，不允许进入本阶段

核对点：

1. `R1/R2/R3/R4` 六条三层关系可见
2. `S1 -> ACC1 -> R1/R2` 接入事实可核对
3. `S2 -> ACC2 -> R3/R4` 接入事实可核对
4. `R1` 是 `172.32.101.0/24` 网关
5. `R3` 是 `172.32.102.0/24` 网关
6. `R2`、`R4` 没有被误识别为服务器网关

放行条件：

1. 平台拓扑与冻结真值一致
2. 结论可回写主线回执
3. 拓扑回执必须写回 `/Users/huangliang/project/OneOPS-ALL/docs/testing/phase1-network-mainline-topology-receipt-v1.md`

回执要求：

1. 记录拓扑截图或拓扑结果编号
2. 记录与冻结链路表的逐项比对结果
3. 记录误识别、漏识别和混入管理面的情况

### 6.8 关闭设备并清理拓扑

目标：

1. 让本次主线执行可彻底结束
2. 避免残留节点、残留网络、残留 tap 口污染下一轮

执行要求：

1. 所有设备必须先关机
2. 关机后再断开接口、删除网络、删除节点、删除整个拓扑
3. 收尾动作参照 [EVE-NG 拓扑生命周期操作验证记录](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-topology-lifecycle-validation.md)
4. 宿主机侧回查 `brctl show`、`bridge link`、`ip tuntap list`
5. 不能只凭节点 `status` 字段判断已经停机，必须补第二证据
6. 删除节点或删除拓扑后，必须额外检查 `tmp` 覆盖目录是否残留

核对点：

1. 所有设备都已停止，且不是只凭 `status` 单点判断
2. Lab 内节点、网络、接口关系都已删除
3. 没有遗留孤儿 tap 口
4. 没有遗留临时拓扑文件
5. 没有遗留 `tmp` 覆盖目录残留

放行条件：

1. 所有设备已关闭
2. 拓扑已删除
3. 宿主机桥接状态已回到干净状态
4. `tmp` 覆盖目录已确认清理干净

回执要求：

1. 记录停机结果
2. 记录拓扑删除结果
3. 记录宿主机残留检查结果
4. 记录 `status` 之外的停机佐证
5. 记录 `tmp` 覆盖目录检查结果

## 7. 异常处理原则

执行中遇到异常，统一按下面规则处理：

1. 管理平面未通，回退到“设备初始化复核”
2. 业务地址或 OSPF 未通，停在“业务平面地址与 OSPF 配置”
3. 采集未过，停在“采集基线”
4. 监控未过，停在“监控基线”
5. 不允许跳过回执直接进入下一阶段

## 8. 本次 Run 结束标准

一次完整执行只有同时满足下面条件才算结束：

1. 八个阶段全部执行完
2. 八份回执都已产出
3. 采集、监控、拓扑三段门禁都已满足
4. 所有设备已关闭
5. 拓扑已删除

如果未满足上述条件，本次 Run 只能算中断，不能算完成。
