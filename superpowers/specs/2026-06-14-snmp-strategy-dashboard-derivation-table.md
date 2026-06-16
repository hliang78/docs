# 2026-06-14 SNMP Strategy Dashboard Derivation Table

This table is derived from the live effective-metrics inventory, not from CE168 layout copying.

- Source inventory: `/OneOPS/docs/superpowers/specs/2026-06-14-snmp-strategy-effective-metrics-inventory.md`
- Strategy row count: `23`
- Recipe count: `5`

## 1. Key Correction

Dashboard regeneration must separate three things:

- strategy node identity
- shared recipe reuse
- CE168 visual/reference borrowing

So:

- strategies with identical effective metrics may share one recipe;
- but they must still remain distinct strategy dashboard nodes;
- CE168 may only contribute reusable concepts and regenerate-only references, never direct hard-coded node content.

## 2. Recipe Clusters

### `snmp.switch.topology-common`

- Node role: `switch-common`
- Strategy count: `15`
- Shared signature(s): `11530cbbb679`
- Mandatory panel families: `l2_neighbors.summary, l2_mac_table.summary, l2_mac_table.count, l3_arp_table.summary, l3_arp_table.count, l2_vlan_table.summary, l2_vlan_table.count, l2_stp_state.summary, l2_stp_state.port_count, l2_stp_state.forwarding_count, l2_stp_state.blocking_count, device_metrics.default`
- Optional overlays: `system_basic.cpu_memory.trend, interface_basic.utilization_topn, interface_basic.pps, device_metrics.temperature.sensors, device_metrics.fan_status.components, device_metrics.power_status.components, device_metrics.transceiver.rx_top4`
- Metric scope: 当前只对 L2/L3 topology summary 与 device_metrics.default 负责；不包含 CE168 中 CPU、接口排行、温度、风扇、电源、光模块等硬编码样本语义。
Strategies:
- `H3C通用SNMP网络监控策略` -> node `10000000_0000_4000_8000_000000000001`
- `H3C网络设备监控 (副本)` -> node `10000000_0000_4000_8000_000000000002`
- `Huawei通用SNMP网络监控策略` -> node `20000000_0000_4000_8000_000000000001`
- `华为网络设备监控 (副本)` -> node `20000000_0000_4000_8000_000000000002`
- `华为网络设备监控 (副本)` -> node `20000000_0000_4000_8000_000000000003`
- `华为网络设备监控 (副本)` -> node `20000000_0000_4000_8000_000000000004`
- `华为网络设备监控 (副本)` -> node `20000000_0000_4000_8000_000000000005`
- `Cisco generic SNMP network monitoring strategy` -> node `30000000_0000_4000_8000_000000000001`
- `思科网络设备监控 (副本)` -> node `30000000_0000_4000_8000_000000000002`
- `思科网络设备监控 (副本)` -> node `30000000_0000_4000_8000_000000000003`
- `锐捷网络设备监控 (副本)` -> node `40000000_0000_4000_8000_000000000001`
- `锐捷网络设备监控 (副本)` -> node `40000000_0000_4000_8000_000000000002`
- `迈普通用SNMP网络监控策略` -> node `50000000_0000_4000_8000_000000000001`
- `烽火通用SNMP网络监控策略` -> node `50000000_0000_4000_8000_000000000002`
- `SNMP网络监控策略` -> node `baf7bb34_86b7_45f8_8e28_2afce170966a`

### `snmp.server.oob-common`

- Node role: `server-oob`
- Strategy count: `3`
- Shared signature(s): `0bd7d00bb3aa, 5c14ce2706c2`
- Mandatory panel families: `device_metrics.default`
- Optional overlays: `hardware.inventory.summary, oob.health.summary`
- Metric scope: 当前对 OOB 设备基础指标负责；可继续向硬件 inventory / health overlay 演进。
Strategies:
- `服务器带外SNMP通用监控策略` -> node `server_oob_snmp_common_strategy`
- `服务器带外SNMP监控策略` -> node `server_oob_snmp_strategy`
- `曙光服务器带外SNMP硬件监控策略` -> node `server_oob_snmp_sugon_strategy`

### `snmp.firewall.current-common`

- Node role: `firewall-common`
- Strategy count: `2`
- Shared signature(s): `11530cbbb679`
- Mandatory panel families: `l2_neighbors.summary, l2_mac_table.summary, l2_mac_table.count, l3_arp_table.summary, l3_arp_table.count, l2_vlan_table.summary, l2_vlan_table.count, l2_stp_state.summary, l2_stp_state.port_count, l2_stp_state.forwarding_count, l2_stp_state.blocking_count, device_metrics.default`
- Optional overlays: `system_basic.cpu_memory.trend, interface_basic.summary, security.sessions.summary, security.throughput.summary`
- Metric scope: 当前仍只对 topology summary 与 device_metrics.default 负责；防火墙语义节点已独立，但 sessions / throughput / security panels 需等待策略契约显式长出。
Strategies:
- `SNMP网络监控策略 (副本)` -> node `23618ca7_5af3_4727_b649_aed7ecfa18f5`
- `H3C SecPath 防火墙 SNMP监控策略` -> node `4c902a48_5f12_11f1_a9bb_0242ac14000c`

### `snmp.server.basic`

- Node role: `server-basic`
- Strategy count: `2`
- Shared signature(s): `4f53cda18c2b, 5cc29af1ae28`
- Mandatory panel families: `device_metrics.default`
- Optional overlays: `system_basic.cpu_memory.trend, device_metrics.processes.summary`
- Metric scope: 当前对基础 device metrics summary 负责，不应借用 switch/chassis 样式。
Strategies:
- `SNMP服务器监控策略 (副本)` -> node `0ee83a51_bda6_4d64_8b3a_370a7a7c465d`
- `SNMP服务器监控策略` -> node `1a20d032_83f4_4c21_9bd5_ab6c14d6bcc2`

### `snmp.switch.routing-overlay`

- Node role: `routing-overlay`
- Strategy count: `1`
- Shared signature(s): `d9a25c291e40`
- Mandatory panel families: `l3_route_table.ipv4_count, l3_route_table.ipv6_count, routing_bgp.neighbor_total, routing_bgp.established_total, routing_ospf.neighbor_total, routing_ospf.full_total`
- Optional overlays: `routing_bgp.neighbor_total, routing_bgp.established_total, routing_ospf.neighbor_total, routing_ospf.full_total, l3_route_table.ipv4_count, l3_route_table.ipv6_count`
- Metric scope: 当前只对 route/BGP/OSPF summary 负责，必须作为独立 routing overlay node 存在。
Strategies:
- `Huawei VRP 路由能力监控策略` -> node `20000000_0000_4000_8000_000000000099`

## 3. Per-Strategy Derivation Rows

### SNMP服务器监控策略 (副本)

- Strategy ID: `0ee83a51-bda6-4d64-8b3a-370a7a7c465d`
- Parent: `SNMP服务器监控策略` (`1a20d032-83f4-4c21-9bd5-ab6c14d6bcc2`)
- Suite root: `OneOPS SNMP Server Ops`
- Node key: `0ee83a51_bda6_4d64_8b3a_370a7a7c465d`
- Node role: `server-basic`
- Recipe key: `snmp.server.basic`
- Effective signature: `5cc29af1ae28`
- Effective groups: `device_metrics`
- Mandatory panel families: `device_metrics.default`
- Optional overlays: `system_basic.cpu_memory.trend, device_metrics.processes.summary`
- Metric scope summary: 当前对基础 device metrics summary 负责，不应借用 switch/chassis 样式。
- CE168 reusable concepts: `summary + detail 的抽象层次`
- CE168 regenerate-only panels: `device summary panels -> 由当前 effective metric keys 直接重生`
- CE168 forbidden carryovers: `100GE5/0, 100GE6/0, 40GE7/0, 10GE8/0, Top 4 by Rx Power, Last 4 by Rx Power, Temperature Sensors, Fans, Power Supplies`

### H3C通用SNMP网络监控策略

- Strategy ID: `10000000-0000-4000-8000-000000000001`
- Parent: `SNMP网络监控策略` (`baf7bb34-86b7-45f8-8e28-2afce170966a`)
- Suite root: `OneOPS SNMP Network Ops`
- Node key: `10000000_0000_4000_8000_000000000001`
- Node role: `switch-common`
- Recipe key: `snmp.switch.topology-common`
- Effective signature: `11530cbbb679`
- Effective groups: `l2_neighbors, l2_mac_table, l3_arp_table, l2_vlan_table, l2_stp_state, device_metrics`
- Mandatory panel families: `l2_neighbors.summary, l2_mac_table.summary, l2_mac_table.count, l3_arp_table.summary, l3_arp_table.count, l2_vlan_table.summary, l2_vlan_table.count, l2_stp_state.summary, l2_stp_state.port_count, l2_stp_state.forwarding_count, l2_stp_state.blocking_count, device_metrics.default`
- Optional overlays: `system_basic.cpu_memory.trend, interface_basic.utilization_topn, interface_basic.pps, device_metrics.temperature.sensors, device_metrics.fan_status.components, device_metrics.power_status.components, device_metrics.transceiver.rx_top4`
- Metric scope summary: 当前只对 L2/L3 topology summary 与 device_metrics.default 负责；不包含 CE168 中 CPU、接口排行、温度、风扇、电源、光模块等硬编码样本语义。
- CE168 reusable concepts: `邻居 / MAC / ARP / VLAN / STP 作为 topology summary family 的组织方式; root summary 与 strategy summary 分层展示`
- CE168 regenerate-only panels: `Interface Utilization Top 10 -> 仅当策略长出 interface traffic/status 指标后重生; Traffic Throughput -> 仅当策略长出 interface octets/throughput 指标后重生; Packets Per Second -> 仅当策略长出 interface packet counters 后重生; CPU / Memory Trend -> 仅当策略长出 system cpu/memory 指标后重生`
- CE168 forbidden carryovers: `100GE5/0, 100GE6/0, 40GE7/0, 10GE8/0, Top 4 by Rx Power, Last 4 by Rx Power, Temperature Sensors, Fans, Power Supplies, Huawei VRP Control Plane CPU, Huawei VRP Control Plane Memory`
- Notes:
  - 当前 runtime 实际上与多个 vendor/model 策略同构；节点仍需保留独立 strategy identity，但可以共享同一 recipe。

### H3C网络设备监控 (副本)

- Strategy ID: `10000000-0000-4000-8000-000000000002`
- Parent: `H3C通用SNMP网络监控策略` (`10000000-0000-4000-8000-000000000001`)
- Suite root: `OneOPS SNMP Network Ops`
- Node key: `10000000_0000_4000_8000_000000000002`
- Node role: `switch-common`
- Recipe key: `snmp.switch.topology-common`
- Effective signature: `11530cbbb679`
- Effective groups: `l2_neighbors, l2_mac_table, l3_arp_table, l2_vlan_table, l2_stp_state, device_metrics`
- Mandatory panel families: `l2_neighbors.summary, l2_mac_table.summary, l2_mac_table.count, l3_arp_table.summary, l3_arp_table.count, l2_vlan_table.summary, l2_vlan_table.count, l2_stp_state.summary, l2_stp_state.port_count, l2_stp_state.forwarding_count, l2_stp_state.blocking_count, device_metrics.default`
- Optional overlays: `system_basic.cpu_memory.trend, interface_basic.utilization_topn, interface_basic.pps, device_metrics.temperature.sensors, device_metrics.fan_status.components, device_metrics.power_status.components, device_metrics.transceiver.rx_top4`
- Metric scope summary: 当前只对 L2/L3 topology summary 与 device_metrics.default 负责；不包含 CE168 中 CPU、接口排行、温度、风扇、电源、光模块等硬编码样本语义。
- CE168 reusable concepts: `邻居 / MAC / ARP / VLAN / STP 作为 topology summary family 的组织方式; root summary 与 strategy summary 分层展示`
- CE168 regenerate-only panels: `Interface Utilization Top 10 -> 仅当策略长出 interface traffic/status 指标后重生; Traffic Throughput -> 仅当策略长出 interface octets/throughput 指标后重生; Packets Per Second -> 仅当策略长出 interface packet counters 后重生; CPU / Memory Trend -> 仅当策略长出 system cpu/memory 指标后重生`
- CE168 forbidden carryovers: `100GE5/0, 100GE6/0, 40GE7/0, 10GE8/0, Top 4 by Rx Power, Last 4 by Rx Power, Temperature Sensors, Fans, Power Supplies, Huawei VRP Control Plane CPU, Huawei VRP Control Plane Memory`
- Notes:
  - 当前 runtime 实际上与多个 vendor/model 策略同构；节点仍需保留独立 strategy identity，但可以共享同一 recipe。

### SNMP服务器监控策略

- Strategy ID: `1a20d032-83f4-4c21-9bd5-ab6c14d6bcc2`
- Parent: `(none)` (`-`)
- Suite root: `OneOPS SNMP Server Ops`
- Node key: `1a20d032_83f4_4c21_9bd5_ab6c14d6bcc2`
- Node role: `server-basic`
- Recipe key: `snmp.server.basic`
- Effective signature: `4f53cda18c2b`
- Effective groups: `(none)`
- Mandatory panel families: `(none)`
- Optional overlays: `system_basic.cpu_memory.trend, device_metrics.processes.summary`
- Metric scope summary: 当前有效契约为空；不能直接生成具体 strategy dashboard 内容。
- CE168 reusable concepts: `summary + detail 的抽象层次`
- CE168 regenerate-only panels: `device summary panels -> 由当前 effective metric keys 直接重生`
- CE168 forbidden carryovers: `100GE5/0, 100GE6/0, 40GE7/0, 10GE8/0, Top 4 by Rx Power, Last 4 by Rx Power, Temperature Sensors, Fans, Power Supplies`

### Huawei通用SNMP网络监控策略

- Strategy ID: `20000000-0000-4000-8000-000000000001`
- Parent: `SNMP网络监控策略` (`baf7bb34-86b7-45f8-8e28-2afce170966a`)
- Suite root: `OneOPS SNMP Network Ops`
- Node key: `20000000_0000_4000_8000_000000000001`
- Node role: `switch-common`
- Recipe key: `snmp.switch.topology-common`
- Effective signature: `11530cbbb679`
- Effective groups: `l2_neighbors, l2_mac_table, l3_arp_table, l2_vlan_table, l2_stp_state, device_metrics`
- Mandatory panel families: `l2_neighbors.summary, l2_mac_table.summary, l2_mac_table.count, l3_arp_table.summary, l3_arp_table.count, l2_vlan_table.summary, l2_vlan_table.count, l2_stp_state.summary, l2_stp_state.port_count, l2_stp_state.forwarding_count, l2_stp_state.blocking_count, device_metrics.default`
- Optional overlays: `system_basic.cpu_memory.trend, interface_basic.utilization_topn, interface_basic.pps, device_metrics.temperature.sensors, device_metrics.fan_status.components, device_metrics.power_status.components, device_metrics.transceiver.rx_top4`
- Metric scope summary: 当前只对 L2/L3 topology summary 与 device_metrics.default 负责；不包含 CE168 中 CPU、接口排行、温度、风扇、电源、光模块等硬编码样本语义。
- CE168 reusable concepts: `邻居 / MAC / ARP / VLAN / STP 作为 topology summary family 的组织方式; root summary 与 strategy summary 分层展示`
- CE168 regenerate-only panels: `Interface Utilization Top 10 -> 仅当策略长出 interface traffic/status 指标后重生; Traffic Throughput -> 仅当策略长出 interface octets/throughput 指标后重生; Packets Per Second -> 仅当策略长出 interface packet counters 后重生; CPU / Memory Trend -> 仅当策略长出 system cpu/memory 指标后重生`
- CE168 forbidden carryovers: `100GE5/0, 100GE6/0, 40GE7/0, 10GE8/0, Top 4 by Rx Power, Last 4 by Rx Power, Temperature Sensors, Fans, Power Supplies, Huawei VRP Control Plane CPU, Huawei VRP Control Plane Memory`
- Notes:
  - 当前 runtime 实际上与多个 vendor/model 策略同构；节点仍需保留独立 strategy identity，但可以共享同一 recipe。

### 华为网络设备监控 (副本)

- Strategy ID: `20000000-0000-4000-8000-000000000002`
- Parent: `Huawei通用SNMP网络监控策略` (`20000000-0000-4000-8000-000000000001`)
- Suite root: `OneOPS SNMP Network Ops`
- Node key: `20000000_0000_4000_8000_000000000002`
- Node role: `switch-common`
- Recipe key: `snmp.switch.topology-common`
- Effective signature: `11530cbbb679`
- Effective groups: `l2_neighbors, l2_mac_table, l3_arp_table, l2_vlan_table, l2_stp_state, device_metrics`
- Mandatory panel families: `l2_neighbors.summary, l2_mac_table.summary, l2_mac_table.count, l3_arp_table.summary, l3_arp_table.count, l2_vlan_table.summary, l2_vlan_table.count, l2_stp_state.summary, l2_stp_state.port_count, l2_stp_state.forwarding_count, l2_stp_state.blocking_count, device_metrics.default`
- Optional overlays: `system_basic.cpu_memory.trend, interface_basic.utilization_topn, interface_basic.pps, device_metrics.temperature.sensors, device_metrics.fan_status.components, device_metrics.power_status.components, device_metrics.transceiver.rx_top4`
- Metric scope summary: 当前只对 L2/L3 topology summary 与 device_metrics.default 负责；不包含 CE168 中 CPU、接口排行、温度、风扇、电源、光模块等硬编码样本语义。
- CE168 reusable concepts: `邻居 / MAC / ARP / VLAN / STP 作为 topology summary family 的组织方式; root summary 与 strategy summary 分层展示`
- CE168 regenerate-only panels: `Interface Utilization Top 10 -> 仅当策略长出 interface traffic/status 指标后重生; Traffic Throughput -> 仅当策略长出 interface octets/throughput 指标后重生; Packets Per Second -> 仅当策略长出 interface packet counters 后重生; CPU / Memory Trend -> 仅当策略长出 system cpu/memory 指标后重生`
- CE168 forbidden carryovers: `100GE5/0, 100GE6/0, 40GE7/0, 10GE8/0, Top 4 by Rx Power, Last 4 by Rx Power, Temperature Sensors, Fans, Power Supplies, Huawei VRP Control Plane CPU, Huawei VRP Control Plane Memory`
- Notes:
  - 当前 runtime 实际上与多个 vendor/model 策略同构；节点仍需保留独立 strategy identity，但可以共享同一 recipe。

### 华为网络设备监控 (副本)

- Strategy ID: `20000000-0000-4000-8000-000000000003`
- Parent: `Huawei通用SNMP网络监控策略` (`20000000-0000-4000-8000-000000000001`)
- Suite root: `OneOPS SNMP Network Ops`
- Node key: `20000000_0000_4000_8000_000000000003`
- Node role: `switch-common`
- Recipe key: `snmp.switch.topology-common`
- Effective signature: `11530cbbb679`
- Effective groups: `l2_neighbors, l2_mac_table, l3_arp_table, l2_vlan_table, l2_stp_state, device_metrics`
- Mandatory panel families: `l2_neighbors.summary, l2_mac_table.summary, l2_mac_table.count, l3_arp_table.summary, l3_arp_table.count, l2_vlan_table.summary, l2_vlan_table.count, l2_stp_state.summary, l2_stp_state.port_count, l2_stp_state.forwarding_count, l2_stp_state.blocking_count, device_metrics.default`
- Optional overlays: `system_basic.cpu_memory.trend, interface_basic.utilization_topn, interface_basic.pps, device_metrics.temperature.sensors, device_metrics.fan_status.components, device_metrics.power_status.components, device_metrics.transceiver.rx_top4`
- Metric scope summary: 当前只对 L2/L3 topology summary 与 device_metrics.default 负责；不包含 CE168 中 CPU、接口排行、温度、风扇、电源、光模块等硬编码样本语义。
- CE168 reusable concepts: `邻居 / MAC / ARP / VLAN / STP 作为 topology summary family 的组织方式; root summary 与 strategy summary 分层展示`
- CE168 regenerate-only panels: `Interface Utilization Top 10 -> 仅当策略长出 interface traffic/status 指标后重生; Traffic Throughput -> 仅当策略长出 interface octets/throughput 指标后重生; Packets Per Second -> 仅当策略长出 interface packet counters 后重生; CPU / Memory Trend -> 仅当策略长出 system cpu/memory 指标后重生`
- CE168 forbidden carryovers: `100GE5/0, 100GE6/0, 40GE7/0, 10GE8/0, Top 4 by Rx Power, Last 4 by Rx Power, Temperature Sensors, Fans, Power Supplies, Huawei VRP Control Plane CPU, Huawei VRP Control Plane Memory`
- Notes:
  - 当前 runtime 实际上与多个 vendor/model 策略同构；节点仍需保留独立 strategy identity，但可以共享同一 recipe。

### 华为网络设备监控 (副本)

- Strategy ID: `20000000-0000-4000-8000-000000000004`
- Parent: `Huawei通用SNMP网络监控策略` (`20000000-0000-4000-8000-000000000001`)
- Suite root: `OneOPS SNMP Network Ops`
- Node key: `20000000_0000_4000_8000_000000000004`
- Node role: `switch-common`
- Recipe key: `snmp.switch.topology-common`
- Effective signature: `11530cbbb679`
- Effective groups: `l2_neighbors, l2_mac_table, l3_arp_table, l2_vlan_table, l2_stp_state, device_metrics`
- Mandatory panel families: `l2_neighbors.summary, l2_mac_table.summary, l2_mac_table.count, l3_arp_table.summary, l3_arp_table.count, l2_vlan_table.summary, l2_vlan_table.count, l2_stp_state.summary, l2_stp_state.port_count, l2_stp_state.forwarding_count, l2_stp_state.blocking_count, device_metrics.default`
- Optional overlays: `system_basic.cpu_memory.trend, interface_basic.utilization_topn, interface_basic.pps, device_metrics.temperature.sensors, device_metrics.fan_status.components, device_metrics.power_status.components, device_metrics.transceiver.rx_top4`
- Metric scope summary: 当前只对 L2/L3 topology summary 与 device_metrics.default 负责；不包含 CE168 中 CPU、接口排行、温度、风扇、电源、光模块等硬编码样本语义。
- CE168 reusable concepts: `邻居 / MAC / ARP / VLAN / STP 作为 topology summary family 的组织方式; root summary 与 strategy summary 分层展示`
- CE168 regenerate-only panels: `Interface Utilization Top 10 -> 仅当策略长出 interface traffic/status 指标后重生; Traffic Throughput -> 仅当策略长出 interface octets/throughput 指标后重生; Packets Per Second -> 仅当策略长出 interface packet counters 后重生; CPU / Memory Trend -> 仅当策略长出 system cpu/memory 指标后重生`
- CE168 forbidden carryovers: `100GE5/0, 100GE6/0, 40GE7/0, 10GE8/0, Top 4 by Rx Power, Last 4 by Rx Power, Temperature Sensors, Fans, Power Supplies, Huawei VRP Control Plane CPU, Huawei VRP Control Plane Memory`
- Notes:
  - 当前 runtime 实际上与多个 vendor/model 策略同构；节点仍需保留独立 strategy identity，但可以共享同一 recipe。

### 华为网络设备监控 (副本)

- Strategy ID: `20000000-0000-4000-8000-000000000005`
- Parent: `Huawei通用SNMP网络监控策略` (`20000000-0000-4000-8000-000000000001`)
- Suite root: `OneOPS SNMP Network Ops`
- Node key: `20000000_0000_4000_8000_000000000005`
- Node role: `switch-common`
- Recipe key: `snmp.switch.topology-common`
- Effective signature: `11530cbbb679`
- Effective groups: `l2_neighbors, l2_mac_table, l3_arp_table, l2_vlan_table, l2_stp_state, device_metrics`
- Mandatory panel families: `l2_neighbors.summary, l2_mac_table.summary, l2_mac_table.count, l3_arp_table.summary, l3_arp_table.count, l2_vlan_table.summary, l2_vlan_table.count, l2_stp_state.summary, l2_stp_state.port_count, l2_stp_state.forwarding_count, l2_stp_state.blocking_count, device_metrics.default`
- Optional overlays: `system_basic.cpu_memory.trend, interface_basic.utilization_topn, interface_basic.pps, device_metrics.temperature.sensors, device_metrics.fan_status.components, device_metrics.power_status.components, device_metrics.transceiver.rx_top4`
- Metric scope summary: 当前只对 L2/L3 topology summary 与 device_metrics.default 负责；不包含 CE168 中 CPU、接口排行、温度、风扇、电源、光模块等硬编码样本语义。
- CE168 reusable concepts: `邻居 / MAC / ARP / VLAN / STP 作为 topology summary family 的组织方式; root summary 与 strategy summary 分层展示`
- CE168 regenerate-only panels: `Interface Utilization Top 10 -> 仅当策略长出 interface traffic/status 指标后重生; Traffic Throughput -> 仅当策略长出 interface octets/throughput 指标后重生; Packets Per Second -> 仅当策略长出 interface packet counters 后重生; CPU / Memory Trend -> 仅当策略长出 system cpu/memory 指标后重生`
- CE168 forbidden carryovers: `100GE5/0, 100GE6/0, 40GE7/0, 10GE8/0, Top 4 by Rx Power, Last 4 by Rx Power, Temperature Sensors, Fans, Power Supplies, Huawei VRP Control Plane CPU, Huawei VRP Control Plane Memory`
- Notes:
  - 当前 runtime 实际上与多个 vendor/model 策略同构；节点仍需保留独立 strategy identity，但可以共享同一 recipe。

### Huawei VRP 路由能力监控策略

- Strategy ID: `20000000-0000-4000-8000-000000000099`
- Parent: `(none)` (`-`)
- Suite root: `OneOPS SNMP Network Ops`
- Node key: `20000000_0000_4000_8000_000000000099`
- Node role: `routing-overlay`
- Recipe key: `snmp.switch.routing-overlay`
- Effective signature: `d9a25c291e40`
- Effective groups: `routing_summary`
- Mandatory panel families: `l3_route_table.ipv4_count, l3_route_table.ipv6_count, routing_bgp.neighbor_total, routing_bgp.established_total, routing_ospf.neighbor_total, routing_ospf.full_total`
- Optional overlays: `routing_bgp.neighbor_total, routing_bgp.established_total, routing_ospf.neighbor_total, routing_ospf.full_total, l3_route_table.ipv4_count, l3_route_table.ipv6_count`
- Metric scope summary: 当前只对 route/BGP/OSPF summary 负责，必须作为独立 routing overlay node 存在。
- CE168 reusable concepts: `overlay 独立存在而不是塞进 root 大盘`
- CE168 regenerate-only panels: `routing summary cards -> 由当前 routing effective panel keys 直接重生`
- CE168 forbidden carryovers: `100GE5/0, 100GE6/0, 40GE7/0, 10GE8/0, Top 4 by Rx Power, Last 4 by Rx Power, Temperature Sensors, Fans, Power Supplies`

### SNMP网络监控策略 (副本)

- Strategy ID: `23618ca7-5af3-4727-b649-aed7ecfa18f5`
- Parent: `SNMP网络监控策略` (`baf7bb34-86b7-45f8-8e28-2afce170966a`)
- Suite root: `OneOPS SNMP Network Ops`
- Node key: `23618ca7_5af3_4727_b649_aed7ecfa18f5`
- Node role: `firewall-common`
- Recipe key: `snmp.firewall.current-common`
- Effective signature: `11530cbbb679`
- Effective groups: `l2_neighbors, l2_mac_table, l3_arp_table, l2_vlan_table, l2_stp_state, device_metrics`
- Mandatory panel families: `l2_neighbors.summary, l2_mac_table.summary, l2_mac_table.count, l3_arp_table.summary, l3_arp_table.count, l2_vlan_table.summary, l2_vlan_table.count, l2_stp_state.summary, l2_stp_state.port_count, l2_stp_state.forwarding_count, l2_stp_state.blocking_count, device_metrics.default`
- Optional overlays: `system_basic.cpu_memory.trend, interface_basic.summary, security.sessions.summary, security.throughput.summary`
- Metric scope summary: 当前仍只对 topology summary 与 device_metrics.default 负责；防火墙语义节点已独立，但 sessions / throughput / security panels 需等待策略契约显式长出。
- CE168 reusable concepts: `summary-first 的信息层次`
- CE168 regenerate-only panels: `security / sessions / throughput panels -> 仅当防火墙策略 effective metrics 显式提供时重生`
- CE168 forbidden carryovers: `100GE5/0, 100GE6/0, 40GE7/0, 10GE8/0, Top 4 by Rx Power, Last 4 by Rx Power, Temperature Sensors, Fans, Power Supplies`
- Notes:
  - 当前 runtime 实际上与多个 vendor/model 策略同构；节点仍需保留独立 strategy identity，但可以共享同一 recipe。
  - 虽然当前 effective signature 与 switch-common 同构，但业务上必须保留独立 firewall strategy dashboard node。

### Cisco generic SNMP network monitoring strategy

- Strategy ID: `30000000-0000-4000-8000-000000000001`
- Parent: `SNMP网络监控策略` (`baf7bb34-86b7-45f8-8e28-2afce170966a`)
- Suite root: `OneOPS SNMP Network Ops`
- Node key: `30000000_0000_4000_8000_000000000001`
- Node role: `switch-common`
- Recipe key: `snmp.switch.topology-common`
- Effective signature: `11530cbbb679`
- Effective groups: `l2_neighbors, l2_mac_table, l3_arp_table, l2_vlan_table, l2_stp_state, device_metrics`
- Mandatory panel families: `l2_neighbors.summary, l2_mac_table.summary, l2_mac_table.count, l3_arp_table.summary, l3_arp_table.count, l2_vlan_table.summary, l2_vlan_table.count, l2_stp_state.summary, l2_stp_state.port_count, l2_stp_state.forwarding_count, l2_stp_state.blocking_count, device_metrics.default`
- Optional overlays: `system_basic.cpu_memory.trend, interface_basic.utilization_topn, interface_basic.pps, device_metrics.temperature.sensors, device_metrics.fan_status.components, device_metrics.power_status.components, device_metrics.transceiver.rx_top4`
- Metric scope summary: 当前只对 L2/L3 topology summary 与 device_metrics.default 负责；不包含 CE168 中 CPU、接口排行、温度、风扇、电源、光模块等硬编码样本语义。
- CE168 reusable concepts: `邻居 / MAC / ARP / VLAN / STP 作为 topology summary family 的组织方式; root summary 与 strategy summary 分层展示`
- CE168 regenerate-only panels: `Interface Utilization Top 10 -> 仅当策略长出 interface traffic/status 指标后重生; Traffic Throughput -> 仅当策略长出 interface octets/throughput 指标后重生; Packets Per Second -> 仅当策略长出 interface packet counters 后重生; CPU / Memory Trend -> 仅当策略长出 system cpu/memory 指标后重生`
- CE168 forbidden carryovers: `100GE5/0, 100GE6/0, 40GE7/0, 10GE8/0, Top 4 by Rx Power, Last 4 by Rx Power, Temperature Sensors, Fans, Power Supplies, Huawei VRP Control Plane CPU, Huawei VRP Control Plane Memory`
- Notes:
  - 当前 runtime 实际上与多个 vendor/model 策略同构；节点仍需保留独立 strategy identity，但可以共享同一 recipe。

### 思科网络设备监控 (副本)

- Strategy ID: `30000000-0000-4000-8000-000000000002`
- Parent: `SNMP网络监控策略` (`baf7bb34-86b7-45f8-8e28-2afce170966a`)
- Suite root: `OneOPS SNMP Network Ops`
- Node key: `30000000_0000_4000_8000_000000000002`
- Node role: `switch-common`
- Recipe key: `snmp.switch.topology-common`
- Effective signature: `11530cbbb679`
- Effective groups: `l2_neighbors, l2_mac_table, l3_arp_table, l2_vlan_table, l2_stp_state, device_metrics`
- Mandatory panel families: `l2_neighbors.summary, l2_mac_table.summary, l2_mac_table.count, l3_arp_table.summary, l3_arp_table.count, l2_vlan_table.summary, l2_vlan_table.count, l2_stp_state.summary, l2_stp_state.port_count, l2_stp_state.forwarding_count, l2_stp_state.blocking_count, device_metrics.default`
- Optional overlays: `system_basic.cpu_memory.trend, interface_basic.utilization_topn, interface_basic.pps, device_metrics.temperature.sensors, device_metrics.fan_status.components, device_metrics.power_status.components, device_metrics.transceiver.rx_top4`
- Metric scope summary: 当前只对 L2/L3 topology summary 与 device_metrics.default 负责；不包含 CE168 中 CPU、接口排行、温度、风扇、电源、光模块等硬编码样本语义。
- CE168 reusable concepts: `邻居 / MAC / ARP / VLAN / STP 作为 topology summary family 的组织方式; root summary 与 strategy summary 分层展示`
- CE168 regenerate-only panels: `Interface Utilization Top 10 -> 仅当策略长出 interface traffic/status 指标后重生; Traffic Throughput -> 仅当策略长出 interface octets/throughput 指标后重生; Packets Per Second -> 仅当策略长出 interface packet counters 后重生; CPU / Memory Trend -> 仅当策略长出 system cpu/memory 指标后重生`
- CE168 forbidden carryovers: `100GE5/0, 100GE6/0, 40GE7/0, 10GE8/0, Top 4 by Rx Power, Last 4 by Rx Power, Temperature Sensors, Fans, Power Supplies, Huawei VRP Control Plane CPU, Huawei VRP Control Plane Memory`
- Notes:
  - 当前 runtime 实际上与多个 vendor/model 策略同构；节点仍需保留独立 strategy identity，但可以共享同一 recipe。

### 思科网络设备监控 (副本)

- Strategy ID: `30000000-0000-4000-8000-000000000003`
- Parent: `SNMP网络监控策略` (`baf7bb34-86b7-45f8-8e28-2afce170966a`)
- Suite root: `OneOPS SNMP Network Ops`
- Node key: `30000000_0000_4000_8000_000000000003`
- Node role: `switch-common`
- Recipe key: `snmp.switch.topology-common`
- Effective signature: `11530cbbb679`
- Effective groups: `l2_neighbors, l2_mac_table, l3_arp_table, l2_vlan_table, l2_stp_state, device_metrics`
- Mandatory panel families: `l2_neighbors.summary, l2_mac_table.summary, l2_mac_table.count, l3_arp_table.summary, l3_arp_table.count, l2_vlan_table.summary, l2_vlan_table.count, l2_stp_state.summary, l2_stp_state.port_count, l2_stp_state.forwarding_count, l2_stp_state.blocking_count, device_metrics.default`
- Optional overlays: `system_basic.cpu_memory.trend, interface_basic.utilization_topn, interface_basic.pps, device_metrics.temperature.sensors, device_metrics.fan_status.components, device_metrics.power_status.components, device_metrics.transceiver.rx_top4`
- Metric scope summary: 当前只对 L2/L3 topology summary 与 device_metrics.default 负责；不包含 CE168 中 CPU、接口排行、温度、风扇、电源、光模块等硬编码样本语义。
- CE168 reusable concepts: `邻居 / MAC / ARP / VLAN / STP 作为 topology summary family 的组织方式; root summary 与 strategy summary 分层展示`
- CE168 regenerate-only panels: `Interface Utilization Top 10 -> 仅当策略长出 interface traffic/status 指标后重生; Traffic Throughput -> 仅当策略长出 interface octets/throughput 指标后重生; Packets Per Second -> 仅当策略长出 interface packet counters 后重生; CPU / Memory Trend -> 仅当策略长出 system cpu/memory 指标后重生`
- CE168 forbidden carryovers: `100GE5/0, 100GE6/0, 40GE7/0, 10GE8/0, Top 4 by Rx Power, Last 4 by Rx Power, Temperature Sensors, Fans, Power Supplies, Huawei VRP Control Plane CPU, Huawei VRP Control Plane Memory`
- Notes:
  - 当前 runtime 实际上与多个 vendor/model 策略同构；节点仍需保留独立 strategy identity，但可以共享同一 recipe。

### 锐捷网络设备监控 (副本)

- Strategy ID: `40000000-0000-4000-8000-000000000001`
- Parent: `SNMP网络监控策略` (`baf7bb34-86b7-45f8-8e28-2afce170966a`)
- Suite root: `OneOPS SNMP Network Ops`
- Node key: `40000000_0000_4000_8000_000000000001`
- Node role: `switch-common`
- Recipe key: `snmp.switch.topology-common`
- Effective signature: `11530cbbb679`
- Effective groups: `l2_neighbors, l2_mac_table, l3_arp_table, l2_vlan_table, l2_stp_state, device_metrics`
- Mandatory panel families: `l2_neighbors.summary, l2_mac_table.summary, l2_mac_table.count, l3_arp_table.summary, l3_arp_table.count, l2_vlan_table.summary, l2_vlan_table.count, l2_stp_state.summary, l2_stp_state.port_count, l2_stp_state.forwarding_count, l2_stp_state.blocking_count, device_metrics.default`
- Optional overlays: `system_basic.cpu_memory.trend, interface_basic.utilization_topn, interface_basic.pps, device_metrics.temperature.sensors, device_metrics.fan_status.components, device_metrics.power_status.components, device_metrics.transceiver.rx_top4`
- Metric scope summary: 当前只对 L2/L3 topology summary 与 device_metrics.default 负责；不包含 CE168 中 CPU、接口排行、温度、风扇、电源、光模块等硬编码样本语义。
- CE168 reusable concepts: `邻居 / MAC / ARP / VLAN / STP 作为 topology summary family 的组织方式; root summary 与 strategy summary 分层展示`
- CE168 regenerate-only panels: `Interface Utilization Top 10 -> 仅当策略长出 interface traffic/status 指标后重生; Traffic Throughput -> 仅当策略长出 interface octets/throughput 指标后重生; Packets Per Second -> 仅当策略长出 interface packet counters 后重生; CPU / Memory Trend -> 仅当策略长出 system cpu/memory 指标后重生`
- CE168 forbidden carryovers: `100GE5/0, 100GE6/0, 40GE7/0, 10GE8/0, Top 4 by Rx Power, Last 4 by Rx Power, Temperature Sensors, Fans, Power Supplies, Huawei VRP Control Plane CPU, Huawei VRP Control Plane Memory`
- Notes:
  - 当前 runtime 实际上与多个 vendor/model 策略同构；节点仍需保留独立 strategy identity，但可以共享同一 recipe。

### 锐捷网络设备监控 (副本)

- Strategy ID: `40000000-0000-4000-8000-000000000002`
- Parent: `SNMP网络监控策略` (`baf7bb34-86b7-45f8-8e28-2afce170966a`)
- Suite root: `OneOPS SNMP Network Ops`
- Node key: `40000000_0000_4000_8000_000000000002`
- Node role: `switch-common`
- Recipe key: `snmp.switch.topology-common`
- Effective signature: `11530cbbb679`
- Effective groups: `l2_neighbors, l2_mac_table, l3_arp_table, l2_vlan_table, l2_stp_state, device_metrics`
- Mandatory panel families: `l2_neighbors.summary, l2_mac_table.summary, l2_mac_table.count, l3_arp_table.summary, l3_arp_table.count, l2_vlan_table.summary, l2_vlan_table.count, l2_stp_state.summary, l2_stp_state.port_count, l2_stp_state.forwarding_count, l2_stp_state.blocking_count, device_metrics.default`
- Optional overlays: `system_basic.cpu_memory.trend, interface_basic.utilization_topn, interface_basic.pps, device_metrics.temperature.sensors, device_metrics.fan_status.components, device_metrics.power_status.components, device_metrics.transceiver.rx_top4`
- Metric scope summary: 当前只对 L2/L3 topology summary 与 device_metrics.default 负责；不包含 CE168 中 CPU、接口排行、温度、风扇、电源、光模块等硬编码样本语义。
- CE168 reusable concepts: `邻居 / MAC / ARP / VLAN / STP 作为 topology summary family 的组织方式; root summary 与 strategy summary 分层展示`
- CE168 regenerate-only panels: `Interface Utilization Top 10 -> 仅当策略长出 interface traffic/status 指标后重生; Traffic Throughput -> 仅当策略长出 interface octets/throughput 指标后重生; Packets Per Second -> 仅当策略长出 interface packet counters 后重生; CPU / Memory Trend -> 仅当策略长出 system cpu/memory 指标后重生`
- CE168 forbidden carryovers: `100GE5/0, 100GE6/0, 40GE7/0, 10GE8/0, Top 4 by Rx Power, Last 4 by Rx Power, Temperature Sensors, Fans, Power Supplies, Huawei VRP Control Plane CPU, Huawei VRP Control Plane Memory`
- Notes:
  - 当前 runtime 实际上与多个 vendor/model 策略同构；节点仍需保留独立 strategy identity，但可以共享同一 recipe。

### H3C SecPath 防火墙 SNMP监控策略

- Strategy ID: `4c902a48-5f12-11f1-a9bb-0242ac14000c`
- Parent: `SNMP网络监控策略` (`baf7bb34-86b7-45f8-8e28-2afce170966a`)
- Suite root: `OneOPS SNMP Network Ops`
- Node key: `4c902a48_5f12_11f1_a9bb_0242ac14000c`
- Node role: `firewall-common`
- Recipe key: `snmp.firewall.current-common`
- Effective signature: `11530cbbb679`
- Effective groups: `l2_neighbors, l2_mac_table, l3_arp_table, l2_vlan_table, l2_stp_state, device_metrics`
- Mandatory panel families: `l2_neighbors.summary, l2_mac_table.summary, l2_mac_table.count, l3_arp_table.summary, l3_arp_table.count, l2_vlan_table.summary, l2_vlan_table.count, l2_stp_state.summary, l2_stp_state.port_count, l2_stp_state.forwarding_count, l2_stp_state.blocking_count, device_metrics.default`
- Optional overlays: `system_basic.cpu_memory.trend, interface_basic.summary, security.sessions.summary, security.throughput.summary`
- Metric scope summary: 当前仍只对 topology summary 与 device_metrics.default 负责；防火墙语义节点已独立，但 sessions / throughput / security panels 需等待策略契约显式长出。
- CE168 reusable concepts: `summary-first 的信息层次`
- CE168 regenerate-only panels: `security / sessions / throughput panels -> 仅当防火墙策略 effective metrics 显式提供时重生`
- CE168 forbidden carryovers: `100GE5/0, 100GE6/0, 40GE7/0, 10GE8/0, Top 4 by Rx Power, Last 4 by Rx Power, Temperature Sensors, Fans, Power Supplies`
- Notes:
  - 当前 runtime 实际上与多个 vendor/model 策略同构；节点仍需保留独立 strategy identity，但可以共享同一 recipe。
  - 虽然当前 effective signature 与 switch-common 同构，但业务上必须保留独立 firewall strategy dashboard node。

### 迈普通用SNMP网络监控策略

- Strategy ID: `50000000-0000-4000-8000-000000000001`
- Parent: `SNMP网络监控策略` (`baf7bb34-86b7-45f8-8e28-2afce170966a`)
- Suite root: `OneOPS SNMP Network Ops`
- Node key: `50000000_0000_4000_8000_000000000001`
- Node role: `switch-common`
- Recipe key: `snmp.switch.topology-common`
- Effective signature: `11530cbbb679`
- Effective groups: `l2_neighbors, l2_mac_table, l3_arp_table, l2_vlan_table, l2_stp_state, device_metrics`
- Mandatory panel families: `l2_neighbors.summary, l2_mac_table.summary, l2_mac_table.count, l3_arp_table.summary, l3_arp_table.count, l2_vlan_table.summary, l2_vlan_table.count, l2_stp_state.summary, l2_stp_state.port_count, l2_stp_state.forwarding_count, l2_stp_state.blocking_count, device_metrics.default`
- Optional overlays: `system_basic.cpu_memory.trend, interface_basic.utilization_topn, interface_basic.pps, device_metrics.temperature.sensors, device_metrics.fan_status.components, device_metrics.power_status.components, device_metrics.transceiver.rx_top4`
- Metric scope summary: 当前只对 L2/L3 topology summary 与 device_metrics.default 负责；不包含 CE168 中 CPU、接口排行、温度、风扇、电源、光模块等硬编码样本语义。
- CE168 reusable concepts: `邻居 / MAC / ARP / VLAN / STP 作为 topology summary family 的组织方式; root summary 与 strategy summary 分层展示`
- CE168 regenerate-only panels: `Interface Utilization Top 10 -> 仅当策略长出 interface traffic/status 指标后重生; Traffic Throughput -> 仅当策略长出 interface octets/throughput 指标后重生; Packets Per Second -> 仅当策略长出 interface packet counters 后重生; CPU / Memory Trend -> 仅当策略长出 system cpu/memory 指标后重生`
- CE168 forbidden carryovers: `100GE5/0, 100GE6/0, 40GE7/0, 10GE8/0, Top 4 by Rx Power, Last 4 by Rx Power, Temperature Sensors, Fans, Power Supplies, Huawei VRP Control Plane CPU, Huawei VRP Control Plane Memory`
- Notes:
  - 当前 runtime 实际上与多个 vendor/model 策略同构；节点仍需保留独立 strategy identity，但可以共享同一 recipe。

### 烽火通用SNMP网络监控策略

- Strategy ID: `50000000-0000-4000-8000-000000000002`
- Parent: `SNMP网络监控策略` (`baf7bb34-86b7-45f8-8e28-2afce170966a`)
- Suite root: `OneOPS SNMP Network Ops`
- Node key: `50000000_0000_4000_8000_000000000002`
- Node role: `switch-common`
- Recipe key: `snmp.switch.topology-common`
- Effective signature: `11530cbbb679`
- Effective groups: `l2_neighbors, l2_mac_table, l3_arp_table, l2_vlan_table, l2_stp_state, device_metrics`
- Mandatory panel families: `l2_neighbors.summary, l2_mac_table.summary, l2_mac_table.count, l3_arp_table.summary, l3_arp_table.count, l2_vlan_table.summary, l2_vlan_table.count, l2_stp_state.summary, l2_stp_state.port_count, l2_stp_state.forwarding_count, l2_stp_state.blocking_count, device_metrics.default`
- Optional overlays: `system_basic.cpu_memory.trend, interface_basic.utilization_topn, interface_basic.pps, device_metrics.temperature.sensors, device_metrics.fan_status.components, device_metrics.power_status.components, device_metrics.transceiver.rx_top4`
- Metric scope summary: 当前只对 L2/L3 topology summary 与 device_metrics.default 负责；不包含 CE168 中 CPU、接口排行、温度、风扇、电源、光模块等硬编码样本语义。
- CE168 reusable concepts: `邻居 / MAC / ARP / VLAN / STP 作为 topology summary family 的组织方式; root summary 与 strategy summary 分层展示`
- CE168 regenerate-only panels: `Interface Utilization Top 10 -> 仅当策略长出 interface traffic/status 指标后重生; Traffic Throughput -> 仅当策略长出 interface octets/throughput 指标后重生; Packets Per Second -> 仅当策略长出 interface packet counters 后重生; CPU / Memory Trend -> 仅当策略长出 system cpu/memory 指标后重生`
- CE168 forbidden carryovers: `100GE5/0, 100GE6/0, 40GE7/0, 10GE8/0, Top 4 by Rx Power, Last 4 by Rx Power, Temperature Sensors, Fans, Power Supplies, Huawei VRP Control Plane CPU, Huawei VRP Control Plane Memory`
- Notes:
  - 当前 runtime 实际上与多个 vendor/model 策略同构；节点仍需保留独立 strategy identity，但可以共享同一 recipe。

### SNMP网络监控策略

- Strategy ID: `baf7bb34-86b7-45f8-8e28-2afce170966a`
- Parent: `(none)` (`-`)
- Suite root: `OneOPS SNMP Network Ops`
- Node key: `baf7bb34_86b7_45f8_8e28_2afce170966a`
- Node role: `switch-common`
- Recipe key: `snmp.switch.topology-common`
- Effective signature: `11530cbbb679`
- Effective groups: `l2_neighbors, l2_mac_table, l3_arp_table, l2_vlan_table, l2_stp_state, device_metrics`
- Mandatory panel families: `l2_neighbors.summary, l2_mac_table.summary, l2_mac_table.count, l3_arp_table.summary, l3_arp_table.count, l2_vlan_table.summary, l2_vlan_table.count, l2_stp_state.summary, l2_stp_state.port_count, l2_stp_state.forwarding_count, l2_stp_state.blocking_count, device_metrics.default`
- Optional overlays: `system_basic.cpu_memory.trend, interface_basic.utilization_topn, interface_basic.pps, device_metrics.temperature.sensors, device_metrics.fan_status.components, device_metrics.power_status.components, device_metrics.transceiver.rx_top4`
- Metric scope summary: 当前只对 L2/L3 topology summary 与 device_metrics.default 负责；不包含 CE168 中 CPU、接口排行、温度、风扇、电源、光模块等硬编码样本语义。
- CE168 reusable concepts: `邻居 / MAC / ARP / VLAN / STP 作为 topology summary family 的组织方式; root summary 与 strategy summary 分层展示`
- CE168 regenerate-only panels: `Interface Utilization Top 10 -> 仅当策略长出 interface traffic/status 指标后重生; Traffic Throughput -> 仅当策略长出 interface octets/throughput 指标后重生; Packets Per Second -> 仅当策略长出 interface packet counters 后重生; CPU / Memory Trend -> 仅当策略长出 system cpu/memory 指标后重生`
- CE168 forbidden carryovers: `100GE5/0, 100GE6/0, 40GE7/0, 10GE8/0, Top 4 by Rx Power, Last 4 by Rx Power, Temperature Sensors, Fans, Power Supplies, Huawei VRP Control Plane CPU, Huawei VRP Control Plane Memory`
- Notes:
  - 当前 runtime 实际上与多个 vendor/model 策略同构；节点仍需保留独立 strategy identity，但可以共享同一 recipe。

### 服务器带外SNMP通用监控策略

- Strategy ID: `server_oob_snmp_common_strategy`
- Parent: `服务器带外SNMP监控策略` (`server_oob_snmp_strategy`)
- Suite root: `OneOPS SNMP Server Ops`
- Node key: `server_oob_snmp_common_strategy`
- Node role: `server-oob`
- Recipe key: `snmp.server.oob-common`
- Effective signature: `0bd7d00bb3aa`
- Effective groups: `device_metrics`
- Mandatory panel families: `device_metrics.default`
- Optional overlays: `hardware.inventory.summary, oob.health.summary`
- Metric scope summary: 当前对 OOB 设备基础指标负责；可继续向硬件 inventory / health overlay 演进。
- CE168 reusable concepts: `summary + detail 的抽象层次`
- CE168 regenerate-only panels: `device summary panels -> 由当前 effective metric keys 直接重生`
- CE168 forbidden carryovers: `100GE5/0, 100GE6/0, 40GE7/0, 10GE8/0, Top 4 by Rx Power, Last 4 by Rx Power, Temperature Sensors, Fans, Power Supplies`

### 服务器带外SNMP监控策略

- Strategy ID: `server_oob_snmp_strategy`
- Parent: `(none)` (`-`)
- Suite root: `OneOPS SNMP Server Ops`
- Node key: `server_oob_snmp_strategy`
- Node role: `server-oob`
- Recipe key: `snmp.server.oob-common`
- Effective signature: `0bd7d00bb3aa`
- Effective groups: `device_metrics`
- Mandatory panel families: `device_metrics.default`
- Optional overlays: `hardware.inventory.summary, oob.health.summary`
- Metric scope summary: 当前对 OOB 设备基础指标负责；可继续向硬件 inventory / health overlay 演进。
- CE168 reusable concepts: `summary + detail 的抽象层次`
- CE168 regenerate-only panels: `device summary panels -> 由当前 effective metric keys 直接重生`
- CE168 forbidden carryovers: `100GE5/0, 100GE6/0, 40GE7/0, 10GE8/0, Top 4 by Rx Power, Last 4 by Rx Power, Temperature Sensors, Fans, Power Supplies`

### 曙光服务器带外SNMP硬件监控策略

- Strategy ID: `server_oob_snmp_sugon_strategy`
- Parent: `服务器带外SNMP监控策略` (`server_oob_snmp_strategy`)
- Suite root: `OneOPS SNMP Server Ops`
- Node key: `server_oob_snmp_sugon_strategy`
- Node role: `server-oob`
- Recipe key: `snmp.server.oob-common`
- Effective signature: `5c14ce2706c2`
- Effective groups: `device_metrics`
- Mandatory panel families: `device_metrics.default`
- Optional overlays: `hardware.inventory.summary, oob.health.summary`
- Metric scope summary: 当前对 OOB 设备基础指标负责；可继续向硬件 inventory / health overlay 演进。
- CE168 reusable concepts: `summary + detail 的抽象层次`
- CE168 regenerate-only panels: `device summary panels -> 由当前 effective metric keys 直接重生`
- CE168 forbidden carryovers: `100GE5/0, 100GE6/0, 40GE7/0, 10GE8/0, Top 4 by Rx Power, Last 4 by Rx Power, Temperature Sensors, Fans, Power Supplies`

## 4. Immediate Generation Rule

The next dashboard code batch should use the table above as follows:

- keep one suite root per suite family;
- materialize one strategy dashboard node per strategy row;
- reuse `recipe_key` only for layout/panel-family generation logic;
- never treat CE168 as the mother template;
- only add CPU/interface/hardware/optics panels when the effective contract truly grows those metrics.
