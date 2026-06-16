# 2026-06-14 SNMP Strategy Dashboard Node Definitions

These node definitions are generated from the live strategy dashboard derivation table.

- Source derivation: `/OneOPS/docs/superpowers/specs/2026-06-14-snmp-strategy-dashboard-derivation-table.json`
- Node definition count: `23`

## 1. Generation Rule

- one strategy row -> one strategy dashboard node definition
- `recipe_key` only governs reusable layout/panel-family logic
- `panel_families` and `metric_group_keys` define current node-local display responsibility
- `ce168_reusable_concepts`, `ce168_regenerate_panels`, and `ce168_forbidden_carryovers` govern how CE168 may or may not influence regeneration

## 2. Per-Strategy Node Definitions

### SNMP服务器监控策略 (副本)

- Strategy ID: `0ee83a51-bda6-4d64-8b3a-370a7a7c465d`
- Suite root: `OneOPS SNMP Server Ops`
- Node key: `0ee83a51_bda6_4d64_8b3a_370a7a7c465d`
- Node role: `server-basic`
- Recipe key: `snmp.server.basic`
- Panel families: `device_metrics.default`
- Metric groups: `device_metrics`
- Display scope summary: 当前对基础 device metrics summary 负责，不应借用 switch/chassis 样式。
- Optional overlays: `system_basic.cpu_memory.trend, device_metrics.processes.summary`
- CE168 reusable concepts: `summary + detail 的抽象层次`
- CE168 regenerate panels: `device summary panels -> 由当前 effective metric keys 直接重生`
- CE168 forbidden carryovers: `100GE5/0, 100GE6/0, 40GE7/0, 10GE8/0, Top 4 by Rx Power, Last 4 by Rx Power, Temperature Sensors, Fans, Power Supplies`

### H3C通用SNMP网络监控策略

- Strategy ID: `10000000-0000-4000-8000-000000000001`
- Suite root: `OneOPS SNMP Network Ops`
- Node key: `10000000_0000_4000_8000_000000000001`
- Node role: `switch-common`
- Recipe key: `snmp.switch.topology-common`
- Panel families: `l2_neighbors.summary, l2_mac_table.summary, l2_mac_table.count, l3_arp_table.summary, l3_arp_table.count, l2_vlan_table.summary, l2_vlan_table.count, l2_stp_state.summary, l2_stp_state.port_count, l2_stp_state.forwarding_count, l2_stp_state.blocking_count, device_metrics.default`
- Metric groups: `l2_neighbors, l2_mac_table, l3_arp_table, l2_vlan_table, l2_stp_state, device_metrics`
- Display scope summary: 当前只对 L2/L3 topology summary 与 device_metrics.default 负责；不包含 CE168 中 CPU、接口排行、温度、风扇、电源、光模块等硬编码样本语义。
- Optional overlays: `system_basic.cpu_memory.trend, interface_basic.utilization_topn, interface_basic.pps, device_metrics.temperature.sensors, device_metrics.fan_status.components, device_metrics.power_status.components, device_metrics.transceiver.rx_top4`
- CE168 reusable concepts: `邻居 / MAC / ARP / VLAN / STP 作为 topology summary family 的组织方式; root summary 与 strategy summary 分层展示`
- CE168 regenerate panels: `Interface Utilization Top 10 -> 仅当策略长出 interface traffic/status 指标后重生; Traffic Throughput -> 仅当策略长出 interface octets/throughput 指标后重生; Packets Per Second -> 仅当策略长出 interface packet counters 后重生; CPU / Memory Trend -> 仅当策略长出 system cpu/memory 指标后重生`
- CE168 forbidden carryovers: `100GE5/0, 100GE6/0, 40GE7/0, 10GE8/0, Top 4 by Rx Power, Last 4 by Rx Power, Temperature Sensors, Fans, Power Supplies, Huawei VRP Control Plane CPU, Huawei VRP Control Plane Memory`

### H3C网络设备监控 (副本)

- Strategy ID: `10000000-0000-4000-8000-000000000002`
- Suite root: `OneOPS SNMP Network Ops`
- Node key: `10000000_0000_4000_8000_000000000002`
- Node role: `switch-common`
- Recipe key: `snmp.switch.topology-common`
- Panel families: `l2_neighbors.summary, l2_mac_table.summary, l2_mac_table.count, l3_arp_table.summary, l3_arp_table.count, l2_vlan_table.summary, l2_vlan_table.count, l2_stp_state.summary, l2_stp_state.port_count, l2_stp_state.forwarding_count, l2_stp_state.blocking_count, device_metrics.default`
- Metric groups: `l2_neighbors, l2_mac_table, l3_arp_table, l2_vlan_table, l2_stp_state, device_metrics`
- Display scope summary: 当前只对 L2/L3 topology summary 与 device_metrics.default 负责；不包含 CE168 中 CPU、接口排行、温度、风扇、电源、光模块等硬编码样本语义。
- Optional overlays: `system_basic.cpu_memory.trend, interface_basic.utilization_topn, interface_basic.pps, device_metrics.temperature.sensors, device_metrics.fan_status.components, device_metrics.power_status.components, device_metrics.transceiver.rx_top4`
- CE168 reusable concepts: `邻居 / MAC / ARP / VLAN / STP 作为 topology summary family 的组织方式; root summary 与 strategy summary 分层展示`
- CE168 regenerate panels: `Interface Utilization Top 10 -> 仅当策略长出 interface traffic/status 指标后重生; Traffic Throughput -> 仅当策略长出 interface octets/throughput 指标后重生; Packets Per Second -> 仅当策略长出 interface packet counters 后重生; CPU / Memory Trend -> 仅当策略长出 system cpu/memory 指标后重生`
- CE168 forbidden carryovers: `100GE5/0, 100GE6/0, 40GE7/0, 10GE8/0, Top 4 by Rx Power, Last 4 by Rx Power, Temperature Sensors, Fans, Power Supplies, Huawei VRP Control Plane CPU, Huawei VRP Control Plane Memory`

### SNMP服务器监控策略

- Strategy ID: `1a20d032-83f4-4c21-9bd5-ab6c14d6bcc2`
- Suite root: `OneOPS SNMP Server Ops`
- Node key: `1a20d032_83f4_4c21_9bd5_ab6c14d6bcc2`
- Node role: `server-basic`
- Recipe key: `snmp.server.basic`
- Panel families: `(none)`
- Metric groups: `(none)`
- Display scope summary: 当前有效契约为空；不能直接生成具体 strategy dashboard 内容。
- Optional overlays: `system_basic.cpu_memory.trend, device_metrics.processes.summary`
- CE168 reusable concepts: `summary + detail 的抽象层次`
- CE168 regenerate panels: `device summary panels -> 由当前 effective metric keys 直接重生`
- CE168 forbidden carryovers: `100GE5/0, 100GE6/0, 40GE7/0, 10GE8/0, Top 4 by Rx Power, Last 4 by Rx Power, Temperature Sensors, Fans, Power Supplies`

### Huawei通用SNMP网络监控策略

- Strategy ID: `20000000-0000-4000-8000-000000000001`
- Suite root: `OneOPS SNMP Network Ops`
- Node key: `20000000_0000_4000_8000_000000000001`
- Node role: `switch-common`
- Recipe key: `snmp.switch.topology-common`
- Panel families: `l2_neighbors.summary, l2_mac_table.summary, l2_mac_table.count, l3_arp_table.summary, l3_arp_table.count, l2_vlan_table.summary, l2_vlan_table.count, l2_stp_state.summary, l2_stp_state.port_count, l2_stp_state.forwarding_count, l2_stp_state.blocking_count, device_metrics.default`
- Metric groups: `l2_neighbors, l2_mac_table, l3_arp_table, l2_vlan_table, l2_stp_state, device_metrics`
- Display scope summary: 当前只对 L2/L3 topology summary 与 device_metrics.default 负责；不包含 CE168 中 CPU、接口排行、温度、风扇、电源、光模块等硬编码样本语义。
- Optional overlays: `system_basic.cpu_memory.trend, interface_basic.utilization_topn, interface_basic.pps, device_metrics.temperature.sensors, device_metrics.fan_status.components, device_metrics.power_status.components, device_metrics.transceiver.rx_top4`
- CE168 reusable concepts: `邻居 / MAC / ARP / VLAN / STP 作为 topology summary family 的组织方式; root summary 与 strategy summary 分层展示`
- CE168 regenerate panels: `Interface Utilization Top 10 -> 仅当策略长出 interface traffic/status 指标后重生; Traffic Throughput -> 仅当策略长出 interface octets/throughput 指标后重生; Packets Per Second -> 仅当策略长出 interface packet counters 后重生; CPU / Memory Trend -> 仅当策略长出 system cpu/memory 指标后重生`
- CE168 forbidden carryovers: `100GE5/0, 100GE6/0, 40GE7/0, 10GE8/0, Top 4 by Rx Power, Last 4 by Rx Power, Temperature Sensors, Fans, Power Supplies, Huawei VRP Control Plane CPU, Huawei VRP Control Plane Memory`

### 华为网络设备监控 (副本)

- Strategy ID: `20000000-0000-4000-8000-000000000002`
- Suite root: `OneOPS SNMP Network Ops`
- Node key: `20000000_0000_4000_8000_000000000002`
- Node role: `switch-common`
- Recipe key: `snmp.switch.topology-common`
- Panel families: `l2_neighbors.summary, l2_mac_table.summary, l2_mac_table.count, l3_arp_table.summary, l3_arp_table.count, l2_vlan_table.summary, l2_vlan_table.count, l2_stp_state.summary, l2_stp_state.port_count, l2_stp_state.forwarding_count, l2_stp_state.blocking_count, device_metrics.default`
- Metric groups: `l2_neighbors, l2_mac_table, l3_arp_table, l2_vlan_table, l2_stp_state, device_metrics`
- Display scope summary: 当前只对 L2/L3 topology summary 与 device_metrics.default 负责；不包含 CE168 中 CPU、接口排行、温度、风扇、电源、光模块等硬编码样本语义。
- Optional overlays: `system_basic.cpu_memory.trend, interface_basic.utilization_topn, interface_basic.pps, device_metrics.temperature.sensors, device_metrics.fan_status.components, device_metrics.power_status.components, device_metrics.transceiver.rx_top4`
- CE168 reusable concepts: `邻居 / MAC / ARP / VLAN / STP 作为 topology summary family 的组织方式; root summary 与 strategy summary 分层展示`
- CE168 regenerate panels: `Interface Utilization Top 10 -> 仅当策略长出 interface traffic/status 指标后重生; Traffic Throughput -> 仅当策略长出 interface octets/throughput 指标后重生; Packets Per Second -> 仅当策略长出 interface packet counters 后重生; CPU / Memory Trend -> 仅当策略长出 system cpu/memory 指标后重生`
- CE168 forbidden carryovers: `100GE5/0, 100GE6/0, 40GE7/0, 10GE8/0, Top 4 by Rx Power, Last 4 by Rx Power, Temperature Sensors, Fans, Power Supplies, Huawei VRP Control Plane CPU, Huawei VRP Control Plane Memory`

### 华为网络设备监控 (副本)

- Strategy ID: `20000000-0000-4000-8000-000000000003`
- Suite root: `OneOPS SNMP Network Ops`
- Node key: `20000000_0000_4000_8000_000000000003`
- Node role: `switch-common`
- Recipe key: `snmp.switch.topology-common`
- Panel families: `l2_neighbors.summary, l2_mac_table.summary, l2_mac_table.count, l3_arp_table.summary, l3_arp_table.count, l2_vlan_table.summary, l2_vlan_table.count, l2_stp_state.summary, l2_stp_state.port_count, l2_stp_state.forwarding_count, l2_stp_state.blocking_count, device_metrics.default`
- Metric groups: `l2_neighbors, l2_mac_table, l3_arp_table, l2_vlan_table, l2_stp_state, device_metrics`
- Display scope summary: 当前只对 L2/L3 topology summary 与 device_metrics.default 负责；不包含 CE168 中 CPU、接口排行、温度、风扇、电源、光模块等硬编码样本语义。
- Optional overlays: `system_basic.cpu_memory.trend, interface_basic.utilization_topn, interface_basic.pps, device_metrics.temperature.sensors, device_metrics.fan_status.components, device_metrics.power_status.components, device_metrics.transceiver.rx_top4`
- CE168 reusable concepts: `邻居 / MAC / ARP / VLAN / STP 作为 topology summary family 的组织方式; root summary 与 strategy summary 分层展示`
- CE168 regenerate panels: `Interface Utilization Top 10 -> 仅当策略长出 interface traffic/status 指标后重生; Traffic Throughput -> 仅当策略长出 interface octets/throughput 指标后重生; Packets Per Second -> 仅当策略长出 interface packet counters 后重生; CPU / Memory Trend -> 仅当策略长出 system cpu/memory 指标后重生`
- CE168 forbidden carryovers: `100GE5/0, 100GE6/0, 40GE7/0, 10GE8/0, Top 4 by Rx Power, Last 4 by Rx Power, Temperature Sensors, Fans, Power Supplies, Huawei VRP Control Plane CPU, Huawei VRP Control Plane Memory`

### 华为网络设备监控 (副本)

- Strategy ID: `20000000-0000-4000-8000-000000000004`
- Suite root: `OneOPS SNMP Network Ops`
- Node key: `20000000_0000_4000_8000_000000000004`
- Node role: `switch-common`
- Recipe key: `snmp.switch.topology-common`
- Panel families: `l2_neighbors.summary, l2_mac_table.summary, l2_mac_table.count, l3_arp_table.summary, l3_arp_table.count, l2_vlan_table.summary, l2_vlan_table.count, l2_stp_state.summary, l2_stp_state.port_count, l2_stp_state.forwarding_count, l2_stp_state.blocking_count, device_metrics.default`
- Metric groups: `l2_neighbors, l2_mac_table, l3_arp_table, l2_vlan_table, l2_stp_state, device_metrics`
- Display scope summary: 当前只对 L2/L3 topology summary 与 device_metrics.default 负责；不包含 CE168 中 CPU、接口排行、温度、风扇、电源、光模块等硬编码样本语义。
- Optional overlays: `system_basic.cpu_memory.trend, interface_basic.utilization_topn, interface_basic.pps, device_metrics.temperature.sensors, device_metrics.fan_status.components, device_metrics.power_status.components, device_metrics.transceiver.rx_top4`
- CE168 reusable concepts: `邻居 / MAC / ARP / VLAN / STP 作为 topology summary family 的组织方式; root summary 与 strategy summary 分层展示`
- CE168 regenerate panels: `Interface Utilization Top 10 -> 仅当策略长出 interface traffic/status 指标后重生; Traffic Throughput -> 仅当策略长出 interface octets/throughput 指标后重生; Packets Per Second -> 仅当策略长出 interface packet counters 后重生; CPU / Memory Trend -> 仅当策略长出 system cpu/memory 指标后重生`
- CE168 forbidden carryovers: `100GE5/0, 100GE6/0, 40GE7/0, 10GE8/0, Top 4 by Rx Power, Last 4 by Rx Power, Temperature Sensors, Fans, Power Supplies, Huawei VRP Control Plane CPU, Huawei VRP Control Plane Memory`

### 华为网络设备监控 (副本)

- Strategy ID: `20000000-0000-4000-8000-000000000005`
- Suite root: `OneOPS SNMP Network Ops`
- Node key: `20000000_0000_4000_8000_000000000005`
- Node role: `switch-common`
- Recipe key: `snmp.switch.topology-common`
- Panel families: `l2_neighbors.summary, l2_mac_table.summary, l2_mac_table.count, l3_arp_table.summary, l3_arp_table.count, l2_vlan_table.summary, l2_vlan_table.count, l2_stp_state.summary, l2_stp_state.port_count, l2_stp_state.forwarding_count, l2_stp_state.blocking_count, device_metrics.default`
- Metric groups: `l2_neighbors, l2_mac_table, l3_arp_table, l2_vlan_table, l2_stp_state, device_metrics`
- Display scope summary: 当前只对 L2/L3 topology summary 与 device_metrics.default 负责；不包含 CE168 中 CPU、接口排行、温度、风扇、电源、光模块等硬编码样本语义。
- Optional overlays: `system_basic.cpu_memory.trend, interface_basic.utilization_topn, interface_basic.pps, device_metrics.temperature.sensors, device_metrics.fan_status.components, device_metrics.power_status.components, device_metrics.transceiver.rx_top4`
- CE168 reusable concepts: `邻居 / MAC / ARP / VLAN / STP 作为 topology summary family 的组织方式; root summary 与 strategy summary 分层展示`
- CE168 regenerate panels: `Interface Utilization Top 10 -> 仅当策略长出 interface traffic/status 指标后重生; Traffic Throughput -> 仅当策略长出 interface octets/throughput 指标后重生; Packets Per Second -> 仅当策略长出 interface packet counters 后重生; CPU / Memory Trend -> 仅当策略长出 system cpu/memory 指标后重生`
- CE168 forbidden carryovers: `100GE5/0, 100GE6/0, 40GE7/0, 10GE8/0, Top 4 by Rx Power, Last 4 by Rx Power, Temperature Sensors, Fans, Power Supplies, Huawei VRP Control Plane CPU, Huawei VRP Control Plane Memory`

### Huawei VRP 路由能力监控策略

- Strategy ID: `20000000-0000-4000-8000-000000000099`
- Suite root: `OneOPS SNMP Network Ops`
- Node key: `20000000_0000_4000_8000_000000000099`
- Node role: `routing-overlay`
- Recipe key: `snmp.switch.routing-overlay`
- Panel families: `l3_route_table.ipv4_count, l3_route_table.ipv6_count, routing_bgp.neighbor_total, routing_bgp.established_total, routing_ospf.neighbor_total, routing_ospf.full_total`
- Metric groups: `routing_summary`
- Display scope summary: 当前只对 route/BGP/OSPF summary 负责，必须作为独立 routing overlay node 存在。
- Optional overlays: `routing_bgp.neighbor_total, routing_bgp.established_total, routing_ospf.neighbor_total, routing_ospf.full_total, l3_route_table.ipv4_count, l3_route_table.ipv6_count`
- CE168 reusable concepts: `overlay 独立存在而不是塞进 root 大盘`
- CE168 regenerate panels: `routing summary cards -> 由当前 routing effective panel keys 直接重生`
- CE168 forbidden carryovers: `100GE5/0, 100GE6/0, 40GE7/0, 10GE8/0, Top 4 by Rx Power, Last 4 by Rx Power, Temperature Sensors, Fans, Power Supplies`

### SNMP网络监控策略 (副本)

- Strategy ID: `23618ca7-5af3-4727-b649-aed7ecfa18f5`
- Suite root: `OneOPS SNMP Network Ops`
- Node key: `23618ca7_5af3_4727_b649_aed7ecfa18f5`
- Node role: `firewall-common`
- Recipe key: `snmp.firewall.current-common`
- Panel families: `l2_neighbors.summary, l2_mac_table.summary, l2_mac_table.count, l3_arp_table.summary, l3_arp_table.count, l2_vlan_table.summary, l2_vlan_table.count, l2_stp_state.summary, l2_stp_state.port_count, l2_stp_state.forwarding_count, l2_stp_state.blocking_count, device_metrics.default`
- Metric groups: `l2_neighbors, l2_mac_table, l3_arp_table, l2_vlan_table, l2_stp_state, device_metrics`
- Display scope summary: 当前仍只对 topology summary 与 device_metrics.default 负责；防火墙语义节点已独立，但 sessions / throughput / security panels 需等待策略契约显式长出。
- Optional overlays: `system_basic.cpu_memory.trend, interface_basic.summary, security.sessions.summary, security.throughput.summary`
- CE168 reusable concepts: `summary-first 的信息层次`
- CE168 regenerate panels: `security / sessions / throughput panels -> 仅当防火墙策略 effective metrics 显式提供时重生`
- CE168 forbidden carryovers: `100GE5/0, 100GE6/0, 40GE7/0, 10GE8/0, Top 4 by Rx Power, Last 4 by Rx Power, Temperature Sensors, Fans, Power Supplies`

### Cisco generic SNMP network monitoring strategy

- Strategy ID: `30000000-0000-4000-8000-000000000001`
- Suite root: `OneOPS SNMP Network Ops`
- Node key: `30000000_0000_4000_8000_000000000001`
- Node role: `switch-common`
- Recipe key: `snmp.switch.topology-common`
- Panel families: `l2_neighbors.summary, l2_mac_table.summary, l2_mac_table.count, l3_arp_table.summary, l3_arp_table.count, l2_vlan_table.summary, l2_vlan_table.count, l2_stp_state.summary, l2_stp_state.port_count, l2_stp_state.forwarding_count, l2_stp_state.blocking_count, device_metrics.default`
- Metric groups: `l2_neighbors, l2_mac_table, l3_arp_table, l2_vlan_table, l2_stp_state, device_metrics`
- Display scope summary: 当前只对 L2/L3 topology summary 与 device_metrics.default 负责；不包含 CE168 中 CPU、接口排行、温度、风扇、电源、光模块等硬编码样本语义。
- Optional overlays: `system_basic.cpu_memory.trend, interface_basic.utilization_topn, interface_basic.pps, device_metrics.temperature.sensors, device_metrics.fan_status.components, device_metrics.power_status.components, device_metrics.transceiver.rx_top4`
- CE168 reusable concepts: `邻居 / MAC / ARP / VLAN / STP 作为 topology summary family 的组织方式; root summary 与 strategy summary 分层展示`
- CE168 regenerate panels: `Interface Utilization Top 10 -> 仅当策略长出 interface traffic/status 指标后重生; Traffic Throughput -> 仅当策略长出 interface octets/throughput 指标后重生; Packets Per Second -> 仅当策略长出 interface packet counters 后重生; CPU / Memory Trend -> 仅当策略长出 system cpu/memory 指标后重生`
- CE168 forbidden carryovers: `100GE5/0, 100GE6/0, 40GE7/0, 10GE8/0, Top 4 by Rx Power, Last 4 by Rx Power, Temperature Sensors, Fans, Power Supplies, Huawei VRP Control Plane CPU, Huawei VRP Control Plane Memory`

### 思科网络设备监控 (副本)

- Strategy ID: `30000000-0000-4000-8000-000000000002`
- Suite root: `OneOPS SNMP Network Ops`
- Node key: `30000000_0000_4000_8000_000000000002`
- Node role: `switch-common`
- Recipe key: `snmp.switch.topology-common`
- Panel families: `l2_neighbors.summary, l2_mac_table.summary, l2_mac_table.count, l3_arp_table.summary, l3_arp_table.count, l2_vlan_table.summary, l2_vlan_table.count, l2_stp_state.summary, l2_stp_state.port_count, l2_stp_state.forwarding_count, l2_stp_state.blocking_count, device_metrics.default`
- Metric groups: `l2_neighbors, l2_mac_table, l3_arp_table, l2_vlan_table, l2_stp_state, device_metrics`
- Display scope summary: 当前只对 L2/L3 topology summary 与 device_metrics.default 负责；不包含 CE168 中 CPU、接口排行、温度、风扇、电源、光模块等硬编码样本语义。
- Optional overlays: `system_basic.cpu_memory.trend, interface_basic.utilization_topn, interface_basic.pps, device_metrics.temperature.sensors, device_metrics.fan_status.components, device_metrics.power_status.components, device_metrics.transceiver.rx_top4`
- CE168 reusable concepts: `邻居 / MAC / ARP / VLAN / STP 作为 topology summary family 的组织方式; root summary 与 strategy summary 分层展示`
- CE168 regenerate panels: `Interface Utilization Top 10 -> 仅当策略长出 interface traffic/status 指标后重生; Traffic Throughput -> 仅当策略长出 interface octets/throughput 指标后重生; Packets Per Second -> 仅当策略长出 interface packet counters 后重生; CPU / Memory Trend -> 仅当策略长出 system cpu/memory 指标后重生`
- CE168 forbidden carryovers: `100GE5/0, 100GE6/0, 40GE7/0, 10GE8/0, Top 4 by Rx Power, Last 4 by Rx Power, Temperature Sensors, Fans, Power Supplies, Huawei VRP Control Plane CPU, Huawei VRP Control Plane Memory`

### 思科网络设备监控 (副本)

- Strategy ID: `30000000-0000-4000-8000-000000000003`
- Suite root: `OneOPS SNMP Network Ops`
- Node key: `30000000_0000_4000_8000_000000000003`
- Node role: `switch-common`
- Recipe key: `snmp.switch.topology-common`
- Panel families: `l2_neighbors.summary, l2_mac_table.summary, l2_mac_table.count, l3_arp_table.summary, l3_arp_table.count, l2_vlan_table.summary, l2_vlan_table.count, l2_stp_state.summary, l2_stp_state.port_count, l2_stp_state.forwarding_count, l2_stp_state.blocking_count, device_metrics.default`
- Metric groups: `l2_neighbors, l2_mac_table, l3_arp_table, l2_vlan_table, l2_stp_state, device_metrics`
- Display scope summary: 当前只对 L2/L3 topology summary 与 device_metrics.default 负责；不包含 CE168 中 CPU、接口排行、温度、风扇、电源、光模块等硬编码样本语义。
- Optional overlays: `system_basic.cpu_memory.trend, interface_basic.utilization_topn, interface_basic.pps, device_metrics.temperature.sensors, device_metrics.fan_status.components, device_metrics.power_status.components, device_metrics.transceiver.rx_top4`
- CE168 reusable concepts: `邻居 / MAC / ARP / VLAN / STP 作为 topology summary family 的组织方式; root summary 与 strategy summary 分层展示`
- CE168 regenerate panels: `Interface Utilization Top 10 -> 仅当策略长出 interface traffic/status 指标后重生; Traffic Throughput -> 仅当策略长出 interface octets/throughput 指标后重生; Packets Per Second -> 仅当策略长出 interface packet counters 后重生; CPU / Memory Trend -> 仅当策略长出 system cpu/memory 指标后重生`
- CE168 forbidden carryovers: `100GE5/0, 100GE6/0, 40GE7/0, 10GE8/0, Top 4 by Rx Power, Last 4 by Rx Power, Temperature Sensors, Fans, Power Supplies, Huawei VRP Control Plane CPU, Huawei VRP Control Plane Memory`

### 锐捷网络设备监控 (副本)

- Strategy ID: `40000000-0000-4000-8000-000000000001`
- Suite root: `OneOPS SNMP Network Ops`
- Node key: `40000000_0000_4000_8000_000000000001`
- Node role: `switch-common`
- Recipe key: `snmp.switch.topology-common`
- Panel families: `l2_neighbors.summary, l2_mac_table.summary, l2_mac_table.count, l3_arp_table.summary, l3_arp_table.count, l2_vlan_table.summary, l2_vlan_table.count, l2_stp_state.summary, l2_stp_state.port_count, l2_stp_state.forwarding_count, l2_stp_state.blocking_count, device_metrics.default`
- Metric groups: `l2_neighbors, l2_mac_table, l3_arp_table, l2_vlan_table, l2_stp_state, device_metrics`
- Display scope summary: 当前只对 L2/L3 topology summary 与 device_metrics.default 负责；不包含 CE168 中 CPU、接口排行、温度、风扇、电源、光模块等硬编码样本语义。
- Optional overlays: `system_basic.cpu_memory.trend, interface_basic.utilization_topn, interface_basic.pps, device_metrics.temperature.sensors, device_metrics.fan_status.components, device_metrics.power_status.components, device_metrics.transceiver.rx_top4`
- CE168 reusable concepts: `邻居 / MAC / ARP / VLAN / STP 作为 topology summary family 的组织方式; root summary 与 strategy summary 分层展示`
- CE168 regenerate panels: `Interface Utilization Top 10 -> 仅当策略长出 interface traffic/status 指标后重生; Traffic Throughput -> 仅当策略长出 interface octets/throughput 指标后重生; Packets Per Second -> 仅当策略长出 interface packet counters 后重生; CPU / Memory Trend -> 仅当策略长出 system cpu/memory 指标后重生`
- CE168 forbidden carryovers: `100GE5/0, 100GE6/0, 40GE7/0, 10GE8/0, Top 4 by Rx Power, Last 4 by Rx Power, Temperature Sensors, Fans, Power Supplies, Huawei VRP Control Plane CPU, Huawei VRP Control Plane Memory`

### 锐捷网络设备监控 (副本)

- Strategy ID: `40000000-0000-4000-8000-000000000002`
- Suite root: `OneOPS SNMP Network Ops`
- Node key: `40000000_0000_4000_8000_000000000002`
- Node role: `switch-common`
- Recipe key: `snmp.switch.topology-common`
- Panel families: `l2_neighbors.summary, l2_mac_table.summary, l2_mac_table.count, l3_arp_table.summary, l3_arp_table.count, l2_vlan_table.summary, l2_vlan_table.count, l2_stp_state.summary, l2_stp_state.port_count, l2_stp_state.forwarding_count, l2_stp_state.blocking_count, device_metrics.default`
- Metric groups: `l2_neighbors, l2_mac_table, l3_arp_table, l2_vlan_table, l2_stp_state, device_metrics`
- Display scope summary: 当前只对 L2/L3 topology summary 与 device_metrics.default 负责；不包含 CE168 中 CPU、接口排行、温度、风扇、电源、光模块等硬编码样本语义。
- Optional overlays: `system_basic.cpu_memory.trend, interface_basic.utilization_topn, interface_basic.pps, device_metrics.temperature.sensors, device_metrics.fan_status.components, device_metrics.power_status.components, device_metrics.transceiver.rx_top4`
- CE168 reusable concepts: `邻居 / MAC / ARP / VLAN / STP 作为 topology summary family 的组织方式; root summary 与 strategy summary 分层展示`
- CE168 regenerate panels: `Interface Utilization Top 10 -> 仅当策略长出 interface traffic/status 指标后重生; Traffic Throughput -> 仅当策略长出 interface octets/throughput 指标后重生; Packets Per Second -> 仅当策略长出 interface packet counters 后重生; CPU / Memory Trend -> 仅当策略长出 system cpu/memory 指标后重生`
- CE168 forbidden carryovers: `100GE5/0, 100GE6/0, 40GE7/0, 10GE8/0, Top 4 by Rx Power, Last 4 by Rx Power, Temperature Sensors, Fans, Power Supplies, Huawei VRP Control Plane CPU, Huawei VRP Control Plane Memory`

### H3C SecPath 防火墙 SNMP监控策略

- Strategy ID: `4c902a48-5f12-11f1-a9bb-0242ac14000c`
- Suite root: `OneOPS SNMP Network Ops`
- Node key: `4c902a48_5f12_11f1_a9bb_0242ac14000c`
- Node role: `firewall-common`
- Recipe key: `snmp.firewall.current-common`
- Panel families: `l2_neighbors.summary, l2_mac_table.summary, l2_mac_table.count, l3_arp_table.summary, l3_arp_table.count, l2_vlan_table.summary, l2_vlan_table.count, l2_stp_state.summary, l2_stp_state.port_count, l2_stp_state.forwarding_count, l2_stp_state.blocking_count, device_metrics.default`
- Metric groups: `l2_neighbors, l2_mac_table, l3_arp_table, l2_vlan_table, l2_stp_state, device_metrics`
- Display scope summary: 当前仍只对 topology summary 与 device_metrics.default 负责；防火墙语义节点已独立，但 sessions / throughput / security panels 需等待策略契约显式长出。
- Optional overlays: `system_basic.cpu_memory.trend, interface_basic.summary, security.sessions.summary, security.throughput.summary`
- CE168 reusable concepts: `summary-first 的信息层次`
- CE168 regenerate panels: `security / sessions / throughput panels -> 仅当防火墙策略 effective metrics 显式提供时重生`
- CE168 forbidden carryovers: `100GE5/0, 100GE6/0, 40GE7/0, 10GE8/0, Top 4 by Rx Power, Last 4 by Rx Power, Temperature Sensors, Fans, Power Supplies`

### 迈普通用SNMP网络监控策略

- Strategy ID: `50000000-0000-4000-8000-000000000001`
- Suite root: `OneOPS SNMP Network Ops`
- Node key: `50000000_0000_4000_8000_000000000001`
- Node role: `switch-common`
- Recipe key: `snmp.switch.topology-common`
- Panel families: `l2_neighbors.summary, l2_mac_table.summary, l2_mac_table.count, l3_arp_table.summary, l3_arp_table.count, l2_vlan_table.summary, l2_vlan_table.count, l2_stp_state.summary, l2_stp_state.port_count, l2_stp_state.forwarding_count, l2_stp_state.blocking_count, device_metrics.default`
- Metric groups: `l2_neighbors, l2_mac_table, l3_arp_table, l2_vlan_table, l2_stp_state, device_metrics`
- Display scope summary: 当前只对 L2/L3 topology summary 与 device_metrics.default 负责；不包含 CE168 中 CPU、接口排行、温度、风扇、电源、光模块等硬编码样本语义。
- Optional overlays: `system_basic.cpu_memory.trend, interface_basic.utilization_topn, interface_basic.pps, device_metrics.temperature.sensors, device_metrics.fan_status.components, device_metrics.power_status.components, device_metrics.transceiver.rx_top4`
- CE168 reusable concepts: `邻居 / MAC / ARP / VLAN / STP 作为 topology summary family 的组织方式; root summary 与 strategy summary 分层展示`
- CE168 regenerate panels: `Interface Utilization Top 10 -> 仅当策略长出 interface traffic/status 指标后重生; Traffic Throughput -> 仅当策略长出 interface octets/throughput 指标后重生; Packets Per Second -> 仅当策略长出 interface packet counters 后重生; CPU / Memory Trend -> 仅当策略长出 system cpu/memory 指标后重生`
- CE168 forbidden carryovers: `100GE5/0, 100GE6/0, 40GE7/0, 10GE8/0, Top 4 by Rx Power, Last 4 by Rx Power, Temperature Sensors, Fans, Power Supplies, Huawei VRP Control Plane CPU, Huawei VRP Control Plane Memory`

### 烽火通用SNMP网络监控策略

- Strategy ID: `50000000-0000-4000-8000-000000000002`
- Suite root: `OneOPS SNMP Network Ops`
- Node key: `50000000_0000_4000_8000_000000000002`
- Node role: `switch-common`
- Recipe key: `snmp.switch.topology-common`
- Panel families: `l2_neighbors.summary, l2_mac_table.summary, l2_mac_table.count, l3_arp_table.summary, l3_arp_table.count, l2_vlan_table.summary, l2_vlan_table.count, l2_stp_state.summary, l2_stp_state.port_count, l2_stp_state.forwarding_count, l2_stp_state.blocking_count, device_metrics.default`
- Metric groups: `l2_neighbors, l2_mac_table, l3_arp_table, l2_vlan_table, l2_stp_state, device_metrics`
- Display scope summary: 当前只对 L2/L3 topology summary 与 device_metrics.default 负责；不包含 CE168 中 CPU、接口排行、温度、风扇、电源、光模块等硬编码样本语义。
- Optional overlays: `system_basic.cpu_memory.trend, interface_basic.utilization_topn, interface_basic.pps, device_metrics.temperature.sensors, device_metrics.fan_status.components, device_metrics.power_status.components, device_metrics.transceiver.rx_top4`
- CE168 reusable concepts: `邻居 / MAC / ARP / VLAN / STP 作为 topology summary family 的组织方式; root summary 与 strategy summary 分层展示`
- CE168 regenerate panels: `Interface Utilization Top 10 -> 仅当策略长出 interface traffic/status 指标后重生; Traffic Throughput -> 仅当策略长出 interface octets/throughput 指标后重生; Packets Per Second -> 仅当策略长出 interface packet counters 后重生; CPU / Memory Trend -> 仅当策略长出 system cpu/memory 指标后重生`
- CE168 forbidden carryovers: `100GE5/0, 100GE6/0, 40GE7/0, 10GE8/0, Top 4 by Rx Power, Last 4 by Rx Power, Temperature Sensors, Fans, Power Supplies, Huawei VRP Control Plane CPU, Huawei VRP Control Plane Memory`

### SNMP网络监控策略

- Strategy ID: `baf7bb34-86b7-45f8-8e28-2afce170966a`
- Suite root: `OneOPS SNMP Network Ops`
- Node key: `baf7bb34_86b7_45f8_8e28_2afce170966a`
- Node role: `switch-common`
- Recipe key: `snmp.switch.topology-common`
- Panel families: `l2_neighbors.summary, l2_mac_table.summary, l2_mac_table.count, l3_arp_table.summary, l3_arp_table.count, l2_vlan_table.summary, l2_vlan_table.count, l2_stp_state.summary, l2_stp_state.port_count, l2_stp_state.forwarding_count, l2_stp_state.blocking_count, device_metrics.default`
- Metric groups: `l2_neighbors, l2_mac_table, l3_arp_table, l2_vlan_table, l2_stp_state, device_metrics`
- Display scope summary: 当前只对 L2/L3 topology summary 与 device_metrics.default 负责；不包含 CE168 中 CPU、接口排行、温度、风扇、电源、光模块等硬编码样本语义。
- Optional overlays: `system_basic.cpu_memory.trend, interface_basic.utilization_topn, interface_basic.pps, device_metrics.temperature.sensors, device_metrics.fan_status.components, device_metrics.power_status.components, device_metrics.transceiver.rx_top4`
- CE168 reusable concepts: `邻居 / MAC / ARP / VLAN / STP 作为 topology summary family 的组织方式; root summary 与 strategy summary 分层展示`
- CE168 regenerate panels: `Interface Utilization Top 10 -> 仅当策略长出 interface traffic/status 指标后重生; Traffic Throughput -> 仅当策略长出 interface octets/throughput 指标后重生; Packets Per Second -> 仅当策略长出 interface packet counters 后重生; CPU / Memory Trend -> 仅当策略长出 system cpu/memory 指标后重生`
- CE168 forbidden carryovers: `100GE5/0, 100GE6/0, 40GE7/0, 10GE8/0, Top 4 by Rx Power, Last 4 by Rx Power, Temperature Sensors, Fans, Power Supplies, Huawei VRP Control Plane CPU, Huawei VRP Control Plane Memory`

### 服务器带外SNMP通用监控策略

- Strategy ID: `server_oob_snmp_common_strategy`
- Suite root: `OneOPS SNMP Server Ops`
- Node key: `server_oob_snmp_common_strategy`
- Node role: `server-oob`
- Recipe key: `snmp.server.oob-common`
- Panel families: `device_metrics.default`
- Metric groups: `device_metrics`
- Display scope summary: 当前对 OOB 设备基础指标负责；可继续向硬件 inventory / health overlay 演进。
- Optional overlays: `hardware.inventory.summary, oob.health.summary`
- CE168 reusable concepts: `summary + detail 的抽象层次`
- CE168 regenerate panels: `device summary panels -> 由当前 effective metric keys 直接重生`
- CE168 forbidden carryovers: `100GE5/0, 100GE6/0, 40GE7/0, 10GE8/0, Top 4 by Rx Power, Last 4 by Rx Power, Temperature Sensors, Fans, Power Supplies`

### 服务器带外SNMP监控策略

- Strategy ID: `server_oob_snmp_strategy`
- Suite root: `OneOPS SNMP Server Ops`
- Node key: `server_oob_snmp_strategy`
- Node role: `server-oob`
- Recipe key: `snmp.server.oob-common`
- Panel families: `device_metrics.default`
- Metric groups: `device_metrics`
- Display scope summary: 当前对 OOB 设备基础指标负责；可继续向硬件 inventory / health overlay 演进。
- Optional overlays: `hardware.inventory.summary, oob.health.summary`
- CE168 reusable concepts: `summary + detail 的抽象层次`
- CE168 regenerate panels: `device summary panels -> 由当前 effective metric keys 直接重生`
- CE168 forbidden carryovers: `100GE5/0, 100GE6/0, 40GE7/0, 10GE8/0, Top 4 by Rx Power, Last 4 by Rx Power, Temperature Sensors, Fans, Power Supplies`

### 曙光服务器带外SNMP硬件监控策略

- Strategy ID: `server_oob_snmp_sugon_strategy`
- Suite root: `OneOPS SNMP Server Ops`
- Node key: `server_oob_snmp_sugon_strategy`
- Node role: `server-oob`
- Recipe key: `snmp.server.oob-common`
- Panel families: `device_metrics.default`
- Metric groups: `device_metrics`
- Display scope summary: 当前对 OOB 设备基础指标负责；可继续向硬件 inventory / health overlay 演进。
- Optional overlays: `hardware.inventory.summary, oob.health.summary`
- CE168 reusable concepts: `summary + detail 的抽象层次`
- CE168 regenerate panels: `device summary panels -> 由当前 effective metric keys 直接重生`
- CE168 forbidden carryovers: `100GE5/0, 100GE6/0, 40GE7/0, 10GE8/0, Top 4 by Rx Power, Last 4 by Rx Power, Temperature Sensors, Fans, Power Supplies`
