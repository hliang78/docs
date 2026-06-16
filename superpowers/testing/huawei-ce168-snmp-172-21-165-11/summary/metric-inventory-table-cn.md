# 华为 CE16808 SNMP 指标探索总表

目标设备：`172.21.165.11`  
设备识别：`HUAWEI CE16808`  
系统版本：`VRP V200R024C00SPC500`  
原始输出目录：`docs/superpowers/testing/huawei-ce168-snmp-172-21-165-11/raw/`

| 指标域 | 页面用途 | 建议指标 / metric_key | OID / 来源 | 探索结果 | 优先级 | 采集建议 |
|---|---|---|---|---|---|---|
| 设备基础信息 | 设备名称、型号、版本、位置、在线状态、运行时长 | `sys_descr`, `sys_object_id`, `sys_uptime`, `sys_name`, `sys_location` | `SNMPv2-MIB::sysDescr/sysObjectID/sysUpTime/sysName/sysLocation`，`.1.3.6.1.2.1.1.*` | 已支持；识别为 `HUAWEI CE16808`，版本 `V200R024C00SPC500`，位置 `Beijing China` | P0 | 可直接进入 `system_basic` 或设备元数据采集 |
| 实体库存 | 机框、板卡、端口、电源、风扇等硬件映射 | `entity_descr`, `entity_class`, `entity_name`, `entity_serial`, `entity_model` | `ENTITY-MIB::entPhysicalTable`，`.1.3.6.1.2.1.47.1.1.1.1` | 已支持；387 个实体，包含机框、LPU、MPU、SFU、端口、电源等 | P0 | 作为硬件健康、温度、风扇、电源的索引主表 |
| 接口基础 | 接口列表、端口状态、速率、别名 | `if_name`, `if_alias`, `if_admin_status`, `if_oper_status`, `if_speed_bps` | `IF-MIB::ifTable` + `ifXTable`，`.1.3.6.1.2.1.2.2.1`，`.1.3.6.1.2.1.31.1.1.1` | 已支持；192 个接口，`ifName/ifAlias/ifHighSpeed` 完整 | P0 | Huawei CE 策略应优先使用 `ifXTable` |
| 接口流量 | 入/出方向吞吐、利用率趋势 | `if_in_rate`, `if_out_rate`, `if_in_utilization`, `if_out_utilization` | 首选 `ifHCInOctets` `.1.3.6.1.2.1.31.1.1.1.6`，`ifHCOutOctets` `.1.3.6.1.2.1.31.1.1.1.10`，`ifHighSpeed` `.1.3.6.1.2.1.31.1.1.1.15` | 已支持；192 个接口全部有 HC 计数器和高速速率 | P0 | 替换当前 bootstrap 中的 32-bit `ifInOctets/ifOutOctets` |
| 接口错误与丢弃 | In/Out Errors、Discards、接口质量趋势 | `if_in_error_rate`, `if_out_error_rate`, `if_in_discard_rate`, `if_out_discard_rate` | `ifInErrors` `.1.3.6.1.2.1.2.2.1.14`，`ifOutErrors` `.1.3.6.1.2.1.2.2.1.20`，`ifInDiscards` `.1.3.6.1.2.1.2.2.1.13`，`ifOutDiscards` `.1.3.6.1.2.1.2.2.1.19` | 已支持；192 个接口完整返回 | P0 | 纳入 `interface_quality`，按 rate 计算 |
| CRC/FCS 错误 | 页面中的 CRC Errors | `if_crc_error_rate` | `EtherLike-MIB::dot3StatsFCSErrors`，`.1.3.6.1.2.1.10.7.2.1.3` | 已支持；156 个物理以太接口有数据 | P0 | 只对物理以太接口展示，逻辑口不应强制要求 |
| 包类型统计 | PPS、单播/组播/广播占比 | `if_in_unicast_pps`, `if_in_multicast_pps`, `if_in_broadcast_pps`, `if_out_unicast_pps`, `if_out_multicast_pps`, `if_out_broadcast_pps` | `ifHCInUcastPkts/MulticastPkts/BroadcastPkts`，`ifHCOutUcastPkts/MulticastPkts/BroadcastPkts`，`.1.3.6.1.2.1.31.1.1.1.7-13` | 已支持；192 个接口完整返回 | P0 | 用于 Traffic Mix、PPS、广播/组播占比面板 |
| 模块 CPU/内存 | CPU Usage、Memory Usage、模块性能 | `cpu_usage_direct`, `memory_usage_direct`, `memory_size_mb`, `cpu_usage_max` | Huawei Entity State，`.1.3.6.1.4.1.2011.5.25.31.1.1.1.1.5/.7/.19/.29` | 已支持；有效值集中在 LPU、MPU、SFU 等模块 | P0 | 按模块采集，设备总览可取 max/avg |
| 温度传感器 | Temperature、硬件温度列表 | `sensor_temperature_celsius` | Huawei Entity State，`.1.3.6.1.4.1.2011.5.25.31.1.1.1.1.11` | 已支持；LPU/MPU/SFU/电源模块均有温度 | P1 | 建议归入 `thermal_sensors`，按实体名展示 |
| 模块电压 | 硬件健康、电压异常辅助判断 | `entity_voltage` | Huawei Entity State，`.1.3.6.1.4.1.2011.5.25.31.1.1.1.1.13` | 已支持；存在非零电压值 | P1 | 需要确认单位换算后再做阈值 |
| 风扇状态 | Fan Status、风扇转速、风扇异常 | `fan_speed`, `fan_present`, `fan_state` | Huawei Fan Table，`.1.3.6.1.4.1.2011.5.25.31.1.1.10.1.5/.6/.7` | 已支持；3 个风扇，状态均为 present/state=1，speed=43 | P1 | 单独建 `fan_status` 表格面板 |
| 电源状态 | Power Supply、冗余电源、电源功率 | `power_present`, `power_state`, `power_current`, `power_voltage`, `power_watts` | Huawei Power Table，`.1.3.6.1.4.1.2011.5.25.31.1.1.18.1.5/.6/.7/.8/.10` | 已支持；4 个电源，均 present/state=1，并有电流、电压、功率 | P1 | 单独建 `power_supply` 表格面板 |
| 光模块功率 | Transceivers、Rx/Tx 光功率 | `optical_rx_power_raw`, `optical_tx_power_raw` | Huawei Entity State 中预期 `.1.3.6.1.4.1.2011.5.25.31.1.1.1.1.22` 等 | 当前未确认；本次 entity state walk 未返回光功率列 | P2 | 需要单独探索光模块 MIB 或加载 Huawei MIB 后再确认 |
| VLAN | VLAN 数量、VLAN 列表 | `vlan_count`, `vlan_id` | `Q-BRIDGE-MIB`，`.1.3.6.1.2.1.17.7` | 已支持；观察到 8 个 VLAN：`1/10/66/2153/2176/2178/2203/2251` | P2 | 可作为资源统计，不建议 P0 高频采集 |
| MAC 表 | MAC Entries、二层转发表 | `mac_entries`, `mac_address`, `mac_port`, `mac_status` | `BRIDGE-MIB::dot1dTpFdbTable`，`.1.3.6.1.2.1.17.4.3` | 已支持；观察到 164 条 FDB 地址/端口/状态记录 | P2 | 核心交换机上表可能变大，建议低频或按需采集 |
| STP | STP Root、STP State | `stp_state`, `stp_root`, `stp_port_state` | `BRIDGE-MIB`，`.1.3.6.1.2.1.17.2` | 已支持；STP 分支有数据 | P2 | 适合资源/状态面板，需再做字段级建模 |
| ARP | ARP Entries | `arp_entries`, `arp_ip`, `arp_mac`, `arp_if_index` | `IP-MIB::ipNetToMediaTable`，`.1.3.6.1.2.1.4.22` | 已支持；776 行原始 ARP 表数据 | P2 | 可统计数量或低频采集明细 |
| IPv4 路由 | IPv4 Routes | `ipv4_route_count`, `ipv4_route_dest`, `ipv4_route_next_hop` | `IP-FORWARD-MIB`，`.1.3.6.1.2.1.4.24` | 已支持；路由数量 scalar 为 25，转发表 710 行原始数据 | P2 | 可做路由数量和路由表快照，不建议高频 |
| LLDP 邻居 | 邻居拓扑、端口对端 | `lldp_neighbor`, `lldp_remote_system`, `lldp_remote_port` | 标准 LLDP-MIB，`.1.0.8802.1.1.2` | 当前不支持；SNMP 返回 `No Such Object` | P2 | 需要 CLI、Huawei 私有 MIB 或调整 SNMP view |
| OSPF 邻居 | OSPF Neighbors | `ospf_neighbor_state`, `ospf_neighbor_count` | 标准 OSPF-MIB，`.1.3.6.1.2.1.14` | 当前不支持；SNMP 返回 `No Such Object` | P2 | 需要 Huawei 私有 MIB、CLI 或调整 SNMP view |
| BGP 邻居 | BGP Neighbors | `bgp_peer_state`, `bgp_peer_count` | 标准 BGP4-MIB，`.1.3.6.1.2.1.15` | 当前不支持；SNMP 返回 `No Such Object` | P2 | 需要 Huawei 私有 MIB、CLI 或调整 SNMP view |
| Packet Buffer / QoS | Packet Buffer Usage、QoS 资源 | `packet_buffer_usage`, `if_buffer_usage`, `qos_resource_overrun` | Huawei XQoS，`.1.3.6.1.4.1.2011.5.25.32` | 部分支持；XQoS 返回 30228 行，但本机未加载 Huawei MIB，具体对象名和单位未确认 | P2 | 暂不进入 P0；先安装/加载 Huawei MIB 做对象翻译 |

