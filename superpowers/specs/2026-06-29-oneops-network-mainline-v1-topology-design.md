# OneOps Network Mainline V1 Topology Design

## Goal

在 `192.168.100.20` 的 EVE-NG 上生成一份新的主线拓扑骨架，作为 OneOps 第一阶段网络设备主线 `4+2+1` 的统一实验底座。

这次设计只解决两件事：

1. 把端口分配原则落实成一份新的、可回读的 EVE 拓扑
2. 把“管理平面 / 接入平面 / 路由平面”三层骨架固定下来，供后续初始化和 OneOps 测试复用

## Scope

本次范围包含：

1. 新建独立 Lab 文件
2. 放入 `GW`、`ACC1`、`ACC2`、`R1-R4`、`S1`、`S2`、`OBS`
3. 按冻结端口表完成所有链路连线
4. 回读节点、网络、接口绑定，确认拓扑骨架落地

本次范围不包含：

1. 设备初始化配置下发
2. 业务地址、OSPF、SSH、VRF 等配置验证
3. OneOps 采集、监控、拓扑任务执行

## Device Mapping

第一版设备映射固定如下：

1. `GW` 使用 `iol` 交换机镜像
2. `ACC1` 使用 `iol` 交换机镜像
3. `ACC2` 使用 `iol` 交换机镜像
4. `R1-R4` 使用 `huaweiar1k-5.170-V300R022C00SPC100-Auto-update-esn`
5. `S1` 使用 `linux-ubuntu-server-20.04`
6. `S2` 使用 `linux-ubuntu-server-20.04`
7. `OBS` 使用 `linux-ubuntu-server-20.04`

这样做的理由是：

1. 这些镜像都已在当前 EVE 主机上存在
2. `GW` 与接入交换机先用同一类二层镜像，便于把拓扑真值和接口位序先固定
3. `R1-R4` 先统一用同一华为路由器样本，便于后续把初始化模板批量复用到 `B1/N1`

## Topology Rules

拓扑固定遵循下面四条规则：

1. `GW` 承担管理网关与 `pnet0` 外联
2. `ACC1/ACC2` 同时承担来自 `GW` 的管理上联和业务接入
3. `R1-R4` 两两全互联，形成路由平面 Full Mesh
4. `S1/S2` 采用双口，`OBS` 采用单管理口

## Frozen Link Map

冻结链路关系如下：

1. `GW IF1 -> pnet0`
2. `GW IF2 -> ACC1 IF1`
3. `GW IF3 -> ACC2 IF1`
4. `GW IF4 -> R1 IF-last`
5. `GW IF5 -> R2 IF-last`
6. `GW IF6 -> R3 IF-last`
7. `GW IF7 -> R4 IF-last`
8. `GW IF8 -> S1 IF2`
9. `GW IF9 -> S2 IF2`
10. `GW IF10 -> OBS IF1`
11. `ACC1 IF2 -> S1 IF1`
12. `ACC1 IF3 -> R1 IF1`
13. `ACC1 IF4 -> R2 IF1`
14. `ACC2 IF2 -> S2 IF1`
15. `ACC2 IF3 -> R3 IF1`
16. `ACC2 IF4 -> R4 IF1`
17. `R1 IF2 -> R2 IF2`
18. `R1 IF3 -> R3 IF2`
19. `R1 IF4 -> R4 IF2`
20. `R2 IF3 -> R3 IF3`
21. `R2 IF4 -> R4 IF3`
22. `R3 IF4 -> R4 IF4`

## Verification Standard

这次拓扑创建完成后，至少要满足下面三条：

1. Lab 文件能被 EVE 正常读取
2. 节点和网络数量与设计一致
3. 每条冻结链路都能通过节点接口的 `network_id` 回读到

## Immediate Next Step

拓扑骨架验证通过后，下一步应直接进入：

1. `GW/ACC/R/S/OBS` 初始化模版套用
2. 管理地址与 SSH 复验
3. `B1` 或 `N1` 的第一轮真实执行
