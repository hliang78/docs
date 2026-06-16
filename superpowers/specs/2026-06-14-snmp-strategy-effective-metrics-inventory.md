# 2026-06-14 SNMP Strategy Effective Metrics Inventory

This document is generated from the current OneOPS runtime API, not from guessed seeds.

- Source API: `http://127.0.0.1:8080/api/v1`
- Generated at: `2026-06-14 18:11:16 CST`
- SNMP strategy count: `23`
- Effective metric signature count: `6`

## 1. Key Findings

- Signature `11530cbbb679`: `17` strategies, role `network-topology-common`, groups `l2_neighbors, l2_mac_table, l3_arp_table, l2_vlan_table, l2_stp_state, device_metrics`, panels `l2_neighbors.summary, l2_mac_table.summary, l2_mac_table.count, l3_arp_table.summary, l3_arp_table.count, l2_vlan_table.summary, l2_vlan_table.count, l2_stp_state.summary, l2_stp_state.port_count, l2_stp_state.forwarding_count, l2_stp_state.blocking_count, device_metrics.default`
- Signature `0bd7d00bb3aa`: `2` strategies, role `server-oob-overlay`, groups `device_metrics`, panels `device_metrics.default`
- Signature `4f53cda18c2b`: `1` strategies, role `empty-shell`, groups `(none)`, panels `(none)`
- Signature `5c14ce2706c2`: `1` strategies, role `server-oob-overlay`, groups `device_metrics`, panels `device_metrics.default`
- Signature `5cc29af1ae28`: `1` strategies, role `generic-device-metrics`, groups `device_metrics`, panels `device_metrics.default`
- Signature `d9a25c291e40`: `1` strategies, role `routing-overlay`, groups `routing_summary`, panels `l3_route_table.ipv4_count, l3_route_table.ipv6_count, routing_bgp.neighbor_total, routing_bgp.established_total, routing_ospf.neighbor_total, routing_ospf.full_total`

## 2. Immediate Regeneration Implication

The current runtime reality is that most network SNMP strategies collapse into one identical effective metric signature. That means current dashboard differentiation cannot be justified by inventing vendor-specific CE168-style panels if those panels are absent from the effective contract.

The largest cluster currently resolves to role `network-topology-common` with panel families `l2_neighbors.summary, l2_mac_table.summary, l2_mac_table.count, l3_arp_table.summary, l3_arp_table.count, l2_vlan_table.summary, l2_vlan_table.count, l2_stp_state.summary, l2_stp_state.port_count, l2_stp_state.forwarding_count, l2_stp_state.blocking_count, device_metrics.default`.

## 3. Signature Clusters

### Signature `11530cbbb679`

- Role: `network-topology-common`
- Group keys: `l2_neighbors, l2_mac_table, l3_arp_table, l2_vlan_table, l2_stp_state, device_metrics`
- Panel keys: `l2_neighbors.summary, l2_mac_table.summary, l2_mac_table.count, l3_arp_table.summary, l3_arp_table.count, l2_vlan_table.summary, l2_vlan_table.count, l2_stp_state.summary, l2_stp_state.port_count, l2_stp_state.forwarding_count, l2_stp_state.blocking_count, device_metrics.default`
- Metric keys: `local_port, neighbor_port, neighbor_name, neighbor_chassis_id, neighbor_management_ip, mac_address, bridge_port, mac_status, ip_address, if_index, arp_type, vlan_id, vlan_name, vlan_status, vlan_type, stp_port, stp_state, stp_enable, stp_path_cost, stp_designated_bridge, uptime, source`
- Capability keys: `l2_neighbor_local_port, l2_neighbor_remote_port, l2_neighbor_identity, l2_neighbor_chassis, l2_neighbor_management_ip, l2_mac_identity, l2_mac_bridge_port, l2_mac_status, l3_arp_identity, l3_arp_mac, l3_arp_if_index, l3_arp_type, l2_vlan_identity, l2_vlan_name, l2_vlan_status, l2_vlan_type, l2_stp_identity, l2_stp_state, l2_stp_enable, l2_stp_path_cost, l2_stp_designated_bridge`

Strategies:
- `H3C通用SNMP网络监控策略 (H3C / Comware)`
- `H3C网络设备监控 (副本) (H3C / Comware / MSR36-40)`
- `Huawei通用SNMP网络监控策略 (Huawei / VRP)`
- `华为网络设备监控 (副本) (Huawei / VRP / S6735-S24X6C, S6735-S48X6C)`
- `华为网络设备监控 (副本) (Huawei / VRP / S5735-L48T4S-A1)`
- `华为网络设备监控 (副本) (Huawei / VRP / NE40E-X8A)`
- `华为网络设备监控 (副本) (Huawei / VRP / S5736-S24T4XC, S5736-S48S4XC, S5735-L48T4S-A1, S6730-H48X6C, S5735)`
- `SNMP网络监控策略 (副本) (Huawei / USG)`
- `Cisco generic SNMP network monitoring strategy (Cisco / IOS)`
- `思科网络设备监控 (副本) (Cisco / Nexus)`
- `思科网络设备监控 (副本) (Cisco / Nexus / N7K-C7010)`
- `锐捷网络设备监控 (副本) (Ruijie / Ruijie)`
- `锐捷网络设备监控 (副本) (Ruijie / Ruijie / RG-RSR20-XA-24)`
- `H3C SecPath 防火墙 SNMP监控策略 (H3C / SecPath)`
- `迈普通用SNMP网络监控策略 (Maipu / MyPower)`
- `烽火通用SNMP网络监控策略 (FiberHome / Fengine)`
- `SNMP网络监控策略`

CE168 handling:
- Borrow: 借鉴 CE168 的信息组织思路：邻居、MAC、ARP、VLAN、STP 作为 topology summary family。
- Regenerate: 按当前 effective panel_keys 重新生成 `l2_neighbors.* / l2_mac_table.* / l3_arp_table.* / l2_vlan_table.* / l2_stp_state.*`，不能直接照抄 CE168 标题和坐标。
- Forbidden: 禁止直接复用 `100GE5/0`、`100GE6/0`、`40GE7/0`、`10GE8/0`、`Huawei VRP Control Plane CPU`、`Temperature Sensors`、`Top 4 by Rx Power` 这类硬编码 sample 内容。

### Signature `0bd7d00bb3aa`

- Role: `server-oob-overlay`
- Group keys: `device_metrics`
- Panel keys: `device_metrics.default`
- Metric keys: `oob_sysDescr, oob_sysObjectID, oob_sysUpTime, sysName`
- Capability keys: `(none)`

Strategies:
- `服务器带外SNMP通用监控策略`
- `服务器带外SNMP监控策略`

CE168 handling:
- Borrow: 不从 CE168 借鉴结构，最多借鉴“显式 summary + detail”这种抽象层次。
- Regenerate: 按当前 `device_metrics.default` 的有效字段重生 summary panel。
- Forbidden: 禁止直接复用任何 CE168 switch/chassis/interface 语义面板。

### Signature `4f53cda18c2b`

- Role: `empty-shell`
- Group keys: `(none)`
- Panel keys: `(none)`
- Metric keys: `(none)`
- Capability keys: `(none)`

Strategies:
- `SNMP服务器监控策略`

CE168 handling:
- Borrow: 不借鉴 CE168。
- Regenerate: 当前策略本身没有有效指标，不能直接生成具体 strategy dashboard 内容。
- Forbidden: 禁止为了填满页面去复制 CE168 sample 面板。

### Signature `5c14ce2706c2`

- Role: `server-oob-overlay`
- Group keys: `device_metrics`
- Panel keys: `device_metrics.default`
- Metric keys: `oob_sysDescr, oob_sysObjectID, oob_sysUpTime, sysName, sugonServerModel, oob_sugonSensorCount`
- Capability keys: `(none)`

Strategies:
- `曙光服务器带外SNMP硬件监控策略 (Sugon)`

CE168 handling:
- Borrow: 不从 CE168 借鉴结构，最多借鉴“显式 summary + detail”这种抽象层次。
- Regenerate: 按当前 `device_metrics.default` 的有效字段重生 summary panel。
- Forbidden: 禁止直接复用任何 CE168 switch/chassis/interface 语义面板。

### Signature `5cc29af1ae28`

- Role: `generic-device-metrics`
- Group keys: `device_metrics`
- Panel keys: `device_metrics.default`
- Metric keys: `source, memAvail, memBuffer, memCached, processes, uptime`
- Capability keys: `(none)`

Strategies:
- `SNMP服务器监控策略 (副本)`

CE168 handling:
- Borrow: 不从 CE168 借鉴结构，最多借鉴“显式 summary + detail”这种抽象层次。
- Regenerate: 按当前 `device_metrics.default` 的有效字段重生 summary panel。
- Forbidden: 禁止直接复用任何 CE168 switch/chassis/interface 语义面板。

### Signature `d9a25c291e40`

- Role: `routing-overlay`
- Group keys: `routing_summary`
- Panel keys: `l3_route_table.ipv4_count, l3_route_table.ipv6_count, routing_bgp.neighbor_total, routing_bgp.established_total, routing_ospf.neighbor_total, routing_ospf.full_total`
- Metric keys: `ipv4_route_count, ipv6_route_count, bgp_neighbor_total, bgp_established_total, ospf_neighbor_total, ospf_full_total`
- Capability keys: `ipv4_route_count, ipv6_route_count, bgp_neighbor_total, bgp_established_total, ospf_neighbor_total, ospf_full_total`

Strategies:
- `Huawei VRP 路由能力监控策略 (Huawei / VRP)`

CE168 handling:
- Borrow: 只借鉴 CE168 对“独立 overlay”处理的思路，不借鉴具体 switch 大盘结构。
- Regenerate: 按 `l3_route_table.* / routing_bgp.* / routing_ospf.*` 当前 effective panel_keys 重生 routing node。
- Forbidden: 禁止把 CE168 的接口排行、板卡、温度、光模块面板混入 routing overlay。

## 4. Per-Strategy Inventory

### SNMP服务器监控策略 (副本)

- Strategy ID: `0ee83a51-bda6-4d64-8b3a-370a7a7c465d`
- Parent: `SNMP服务器监控策略` (`1a20d032-83f4-4c21-9bd5-ab6c14d6bcc2`)
- Scope: `- / - / -`
- Contract source: `legacy_import`
- Effective signature: `5cc29af1ae28`
- Dashboard role: `generic-device-metrics`
- Effective groups: `device_metrics`
- Effective panel keys: `device_metrics.default`
- Effective metric keys: `source, memAvail, memBuffer, memCached, processes, uptime`
- Effective capability keys: `(none)`
- Effective concept keys: `(none)`
- CE168 borrow: 不从 CE168 借鉴结构，最多借鉴“显式 summary + detail”这种抽象层次。
- CE168 regenerate: 按当前 `device_metrics.default` 的有效字段重生 summary panel。
- CE168 forbidden: 禁止直接复用任何 CE168 switch/chassis/interface 语义面板。

### H3C通用SNMP网络监控策略

- Strategy ID: `10000000-0000-4000-8000-000000000001`
- Parent: `SNMP网络监控策略` (`baf7bb34-86b7-45f8-8e28-2afce170966a`)
- Scope: `H3C / Comware / -`
- Contract source: `legacy_import`
- Effective signature: `11530cbbb679`
- Dashboard role: `network-topology-common`
- Effective groups: `l2_neighbors, l2_mac_table, l3_arp_table, l2_vlan_table, l2_stp_state, device_metrics`
- Effective panel keys: `l2_neighbors.summary, l2_mac_table.summary, l2_mac_table.count, l3_arp_table.summary, l3_arp_table.count, l2_vlan_table.summary, l2_vlan_table.count, l2_stp_state.summary, l2_stp_state.port_count, l2_stp_state.forwarding_count, l2_stp_state.blocking_count, device_metrics.default`
- Effective metric keys: `local_port, neighbor_port, neighbor_name, neighbor_chassis_id, neighbor_management_ip, mac_address, bridge_port, mac_status, ip_address, if_index, arp_type, vlan_id, vlan_name, vlan_status, vlan_type, stp_port, stp_state, stp_enable, stp_path_cost, stp_designated_bridge, uptime, source`
- Effective capability keys: `l2_neighbor_local_port, l2_neighbor_remote_port, l2_neighbor_identity, l2_neighbor_chassis, l2_neighbor_management_ip, l2_mac_identity, l2_mac_bridge_port, l2_mac_status, l3_arp_identity, l3_arp_mac, l3_arp_if_index, l3_arp_type, l2_vlan_identity, l2_vlan_name, l2_vlan_status, l2_vlan_type, l2_stp_identity, l2_stp_state, l2_stp_enable, l2_stp_path_cost, l2_stp_designated_bridge`
- Effective concept keys: `local_port, neighbor_port, neighbor_name, neighbor_chassis_id, neighbor_management_ip, mac_address, bridge_port, mac_status, ip_address, if_index, arp_type, vlan_id, vlan_name, vlan_status, vlan_type, stp_port, stp_state, stp_enable, stp_path_cost, stp_designated_bridge`
- CE168 borrow: 借鉴 CE168 的信息组织思路：邻居、MAC、ARP、VLAN、STP 作为 topology summary family。
- CE168 regenerate: 按当前 effective panel_keys 重新生成 `l2_neighbors.* / l2_mac_table.* / l3_arp_table.* / l2_vlan_table.* / l2_stp_state.*`，不能直接照抄 CE168 标题和坐标。
- CE168 forbidden: 禁止直接复用 `100GE5/0`、`100GE6/0`、`40GE7/0`、`10GE8/0`、`Huawei VRP Control Plane CPU`、`Temperature Sensors`、`Top 4 by Rx Power` 这类硬编码 sample 内容。

### H3C网络设备监控 (副本)

- Strategy ID: `10000000-0000-4000-8000-000000000002`
- Parent: `H3C通用SNMP网络监控策略` (`10000000-0000-4000-8000-000000000001`)
- Scope: `H3C / Comware / MSR36-40`
- Contract source: `legacy_import`
- Effective signature: `11530cbbb679`
- Dashboard role: `network-topology-common`
- Effective groups: `l2_neighbors, l2_mac_table, l3_arp_table, l2_vlan_table, l2_stp_state, device_metrics`
- Effective panel keys: `l2_neighbors.summary, l2_mac_table.summary, l2_mac_table.count, l3_arp_table.summary, l3_arp_table.count, l2_vlan_table.summary, l2_vlan_table.count, l2_stp_state.summary, l2_stp_state.port_count, l2_stp_state.forwarding_count, l2_stp_state.blocking_count, device_metrics.default`
- Effective metric keys: `local_port, neighbor_port, neighbor_name, neighbor_chassis_id, neighbor_management_ip, mac_address, bridge_port, mac_status, ip_address, if_index, arp_type, vlan_id, vlan_name, vlan_status, vlan_type, stp_port, stp_state, stp_enable, stp_path_cost, stp_designated_bridge, uptime, source`
- Effective capability keys: `l2_neighbor_local_port, l2_neighbor_remote_port, l2_neighbor_identity, l2_neighbor_chassis, l2_neighbor_management_ip, l2_mac_identity, l2_mac_bridge_port, l2_mac_status, l3_arp_identity, l3_arp_mac, l3_arp_if_index, l3_arp_type, l2_vlan_identity, l2_vlan_name, l2_vlan_status, l2_vlan_type, l2_stp_identity, l2_stp_state, l2_stp_enable, l2_stp_path_cost, l2_stp_designated_bridge`
- Effective concept keys: `local_port, neighbor_port, neighbor_name, neighbor_chassis_id, neighbor_management_ip, mac_address, bridge_port, mac_status, ip_address, if_index, arp_type, vlan_id, vlan_name, vlan_status, vlan_type, stp_port, stp_state, stp_enable, stp_path_cost, stp_designated_bridge`
- CE168 borrow: 借鉴 CE168 的信息组织思路：邻居、MAC、ARP、VLAN、STP 作为 topology summary family。
- CE168 regenerate: 按当前 effective panel_keys 重新生成 `l2_neighbors.* / l2_mac_table.* / l3_arp_table.* / l2_vlan_table.* / l2_stp_state.*`，不能直接照抄 CE168 标题和坐标。
- CE168 forbidden: 禁止直接复用 `100GE5/0`、`100GE6/0`、`40GE7/0`、`10GE8/0`、`Huawei VRP Control Plane CPU`、`Temperature Sensors`、`Top 4 by Rx Power` 这类硬编码 sample 内容。

### SNMP服务器监控策略

- Strategy ID: `1a20d032-83f4-4c21-9bd5-ab6c14d6bcc2`
- Parent: `(none)` (`-`)
- Scope: `- / - / -`
- Contract source: `backend_resolver`
- Effective signature: `4f53cda18c2b`
- Dashboard role: `empty-shell`
- Effective groups: `(none)`
- Effective panel keys: `(none)`
- Effective metric keys: `(none)`
- Effective capability keys: `(none)`
- Effective concept keys: `(none)`
- CE168 borrow: 不借鉴 CE168。
- CE168 regenerate: 当前策略本身没有有效指标，不能直接生成具体 strategy dashboard 内容。
- CE168 forbidden: 禁止为了填满页面去复制 CE168 sample 面板。

### Huawei通用SNMP网络监控策略

- Strategy ID: `20000000-0000-4000-8000-000000000001`
- Parent: `SNMP网络监控策略` (`baf7bb34-86b7-45f8-8e28-2afce170966a`)
- Scope: `Huawei / VRP / -`
- Contract source: `legacy_import`
- Effective signature: `11530cbbb679`
- Dashboard role: `network-topology-common`
- Effective groups: `l2_neighbors, l2_mac_table, l3_arp_table, l2_vlan_table, l2_stp_state, device_metrics`
- Effective panel keys: `l2_neighbors.summary, l2_mac_table.summary, l2_mac_table.count, l3_arp_table.summary, l3_arp_table.count, l2_vlan_table.summary, l2_vlan_table.count, l2_stp_state.summary, l2_stp_state.port_count, l2_stp_state.forwarding_count, l2_stp_state.blocking_count, device_metrics.default`
- Effective metric keys: `local_port, neighbor_port, neighbor_name, neighbor_chassis_id, neighbor_management_ip, mac_address, bridge_port, mac_status, ip_address, if_index, arp_type, vlan_id, vlan_name, vlan_status, vlan_type, stp_port, stp_state, stp_enable, stp_path_cost, stp_designated_bridge, uptime, source`
- Effective capability keys: `l2_neighbor_local_port, l2_neighbor_remote_port, l2_neighbor_identity, l2_neighbor_chassis, l2_neighbor_management_ip, l2_mac_identity, l2_mac_bridge_port, l2_mac_status, l3_arp_identity, l3_arp_mac, l3_arp_if_index, l3_arp_type, l2_vlan_identity, l2_vlan_name, l2_vlan_status, l2_vlan_type, l2_stp_identity, l2_stp_state, l2_stp_enable, l2_stp_path_cost, l2_stp_designated_bridge`
- Effective concept keys: `local_port, neighbor_port, neighbor_name, neighbor_chassis_id, neighbor_management_ip, mac_address, bridge_port, mac_status, ip_address, if_index, arp_type, vlan_id, vlan_name, vlan_status, vlan_type, stp_port, stp_state, stp_enable, stp_path_cost, stp_designated_bridge`
- CE168 borrow: 借鉴 CE168 的信息组织思路：邻居、MAC、ARP、VLAN、STP 作为 topology summary family。
- CE168 regenerate: 按当前 effective panel_keys 重新生成 `l2_neighbors.* / l2_mac_table.* / l3_arp_table.* / l2_vlan_table.* / l2_stp_state.*`，不能直接照抄 CE168 标题和坐标。
- CE168 forbidden: 禁止直接复用 `100GE5/0`、`100GE6/0`、`40GE7/0`、`10GE8/0`、`Huawei VRP Control Plane CPU`、`Temperature Sensors`、`Top 4 by Rx Power` 这类硬编码 sample 内容。

### 华为网络设备监控 (副本)

- Strategy ID: `20000000-0000-4000-8000-000000000002`
- Parent: `Huawei通用SNMP网络监控策略` (`20000000-0000-4000-8000-000000000001`)
- Scope: `Huawei / VRP / S6735-S24X6C, S6735-S48X6C`
- Contract source: `legacy_import`
- Effective signature: `11530cbbb679`
- Dashboard role: `network-topology-common`
- Effective groups: `l2_neighbors, l2_mac_table, l3_arp_table, l2_vlan_table, l2_stp_state, device_metrics`
- Effective panel keys: `l2_neighbors.summary, l2_mac_table.summary, l2_mac_table.count, l3_arp_table.summary, l3_arp_table.count, l2_vlan_table.summary, l2_vlan_table.count, l2_stp_state.summary, l2_stp_state.port_count, l2_stp_state.forwarding_count, l2_stp_state.blocking_count, device_metrics.default`
- Effective metric keys: `local_port, neighbor_port, neighbor_name, neighbor_chassis_id, neighbor_management_ip, mac_address, bridge_port, mac_status, ip_address, if_index, arp_type, vlan_id, vlan_name, vlan_status, vlan_type, stp_port, stp_state, stp_enable, stp_path_cost, stp_designated_bridge, uptime, source`
- Effective capability keys: `l2_neighbor_local_port, l2_neighbor_remote_port, l2_neighbor_identity, l2_neighbor_chassis, l2_neighbor_management_ip, l2_mac_identity, l2_mac_bridge_port, l2_mac_status, l3_arp_identity, l3_arp_mac, l3_arp_if_index, l3_arp_type, l2_vlan_identity, l2_vlan_name, l2_vlan_status, l2_vlan_type, l2_stp_identity, l2_stp_state, l2_stp_enable, l2_stp_path_cost, l2_stp_designated_bridge`
- Effective concept keys: `local_port, neighbor_port, neighbor_name, neighbor_chassis_id, neighbor_management_ip, mac_address, bridge_port, mac_status, ip_address, if_index, arp_type, vlan_id, vlan_name, vlan_status, vlan_type, stp_port, stp_state, stp_enable, stp_path_cost, stp_designated_bridge`
- CE168 borrow: 借鉴 CE168 的信息组织思路：邻居、MAC、ARP、VLAN、STP 作为 topology summary family。
- CE168 regenerate: 按当前 effective panel_keys 重新生成 `l2_neighbors.* / l2_mac_table.* / l3_arp_table.* / l2_vlan_table.* / l2_stp_state.*`，不能直接照抄 CE168 标题和坐标。
- CE168 forbidden: 禁止直接复用 `100GE5/0`、`100GE6/0`、`40GE7/0`、`10GE8/0`、`Huawei VRP Control Plane CPU`、`Temperature Sensors`、`Top 4 by Rx Power` 这类硬编码 sample 内容。

### 华为网络设备监控 (副本)

- Strategy ID: `20000000-0000-4000-8000-000000000003`
- Parent: `Huawei通用SNMP网络监控策略` (`20000000-0000-4000-8000-000000000001`)
- Scope: `Huawei / VRP / S5735-L48T4S-A1`
- Contract source: `legacy_import`
- Effective signature: `11530cbbb679`
- Dashboard role: `network-topology-common`
- Effective groups: `l2_neighbors, l2_mac_table, l3_arp_table, l2_vlan_table, l2_stp_state, device_metrics`
- Effective panel keys: `l2_neighbors.summary, l2_mac_table.summary, l2_mac_table.count, l3_arp_table.summary, l3_arp_table.count, l2_vlan_table.summary, l2_vlan_table.count, l2_stp_state.summary, l2_stp_state.port_count, l2_stp_state.forwarding_count, l2_stp_state.blocking_count, device_metrics.default`
- Effective metric keys: `local_port, neighbor_port, neighbor_name, neighbor_chassis_id, neighbor_management_ip, mac_address, bridge_port, mac_status, ip_address, if_index, arp_type, vlan_id, vlan_name, vlan_status, vlan_type, stp_port, stp_state, stp_enable, stp_path_cost, stp_designated_bridge, uptime, source`
- Effective capability keys: `l2_neighbor_local_port, l2_neighbor_remote_port, l2_neighbor_identity, l2_neighbor_chassis, l2_neighbor_management_ip, l2_mac_identity, l2_mac_bridge_port, l2_mac_status, l3_arp_identity, l3_arp_mac, l3_arp_if_index, l3_arp_type, l2_vlan_identity, l2_vlan_name, l2_vlan_status, l2_vlan_type, l2_stp_identity, l2_stp_state, l2_stp_enable, l2_stp_path_cost, l2_stp_designated_bridge`
- Effective concept keys: `local_port, neighbor_port, neighbor_name, neighbor_chassis_id, neighbor_management_ip, mac_address, bridge_port, mac_status, ip_address, if_index, arp_type, vlan_id, vlan_name, vlan_status, vlan_type, stp_port, stp_state, stp_enable, stp_path_cost, stp_designated_bridge`
- CE168 borrow: 借鉴 CE168 的信息组织思路：邻居、MAC、ARP、VLAN、STP 作为 topology summary family。
- CE168 regenerate: 按当前 effective panel_keys 重新生成 `l2_neighbors.* / l2_mac_table.* / l3_arp_table.* / l2_vlan_table.* / l2_stp_state.*`，不能直接照抄 CE168 标题和坐标。
- CE168 forbidden: 禁止直接复用 `100GE5/0`、`100GE6/0`、`40GE7/0`、`10GE8/0`、`Huawei VRP Control Plane CPU`、`Temperature Sensors`、`Top 4 by Rx Power` 这类硬编码 sample 内容。

### 华为网络设备监控 (副本)

- Strategy ID: `20000000-0000-4000-8000-000000000004`
- Parent: `Huawei通用SNMP网络监控策略` (`20000000-0000-4000-8000-000000000001`)
- Scope: `Huawei / VRP / NE40E-X8A`
- Contract source: `legacy_import`
- Effective signature: `11530cbbb679`
- Dashboard role: `network-topology-common`
- Effective groups: `l2_neighbors, l2_mac_table, l3_arp_table, l2_vlan_table, l2_stp_state, device_metrics`
- Effective panel keys: `l2_neighbors.summary, l2_mac_table.summary, l2_mac_table.count, l3_arp_table.summary, l3_arp_table.count, l2_vlan_table.summary, l2_vlan_table.count, l2_stp_state.summary, l2_stp_state.port_count, l2_stp_state.forwarding_count, l2_stp_state.blocking_count, device_metrics.default`
- Effective metric keys: `local_port, neighbor_port, neighbor_name, neighbor_chassis_id, neighbor_management_ip, mac_address, bridge_port, mac_status, ip_address, if_index, arp_type, vlan_id, vlan_name, vlan_status, vlan_type, stp_port, stp_state, stp_enable, stp_path_cost, stp_designated_bridge, uptime, source`
- Effective capability keys: `l2_neighbor_local_port, l2_neighbor_remote_port, l2_neighbor_identity, l2_neighbor_chassis, l2_neighbor_management_ip, l2_mac_identity, l2_mac_bridge_port, l2_mac_status, l3_arp_identity, l3_arp_mac, l3_arp_if_index, l3_arp_type, l2_vlan_identity, l2_vlan_name, l2_vlan_status, l2_vlan_type, l2_stp_identity, l2_stp_state, l2_stp_enable, l2_stp_path_cost, l2_stp_designated_bridge`
- Effective concept keys: `local_port, neighbor_port, neighbor_name, neighbor_chassis_id, neighbor_management_ip, mac_address, bridge_port, mac_status, ip_address, if_index, arp_type, vlan_id, vlan_name, vlan_status, vlan_type, stp_port, stp_state, stp_enable, stp_path_cost, stp_designated_bridge`
- CE168 borrow: 借鉴 CE168 的信息组织思路：邻居、MAC、ARP、VLAN、STP 作为 topology summary family。
- CE168 regenerate: 按当前 effective panel_keys 重新生成 `l2_neighbors.* / l2_mac_table.* / l3_arp_table.* / l2_vlan_table.* / l2_stp_state.*`，不能直接照抄 CE168 标题和坐标。
- CE168 forbidden: 禁止直接复用 `100GE5/0`、`100GE6/0`、`40GE7/0`、`10GE8/0`、`Huawei VRP Control Plane CPU`、`Temperature Sensors`、`Top 4 by Rx Power` 这类硬编码 sample 内容。

### 华为网络设备监控 (副本)

- Strategy ID: `20000000-0000-4000-8000-000000000005`
- Parent: `Huawei通用SNMP网络监控策略` (`20000000-0000-4000-8000-000000000001`)
- Scope: `Huawei / VRP / S5736-S24T4XC, S5736-S48S4XC, S5735-L48T4S-A1, S6730-H48X6C, S5735`
- Contract source: `legacy_import`
- Effective signature: `11530cbbb679`
- Dashboard role: `network-topology-common`
- Effective groups: `l2_neighbors, l2_mac_table, l3_arp_table, l2_vlan_table, l2_stp_state, device_metrics`
- Effective panel keys: `l2_neighbors.summary, l2_mac_table.summary, l2_mac_table.count, l3_arp_table.summary, l3_arp_table.count, l2_vlan_table.summary, l2_vlan_table.count, l2_stp_state.summary, l2_stp_state.port_count, l2_stp_state.forwarding_count, l2_stp_state.blocking_count, device_metrics.default`
- Effective metric keys: `local_port, neighbor_port, neighbor_name, neighbor_chassis_id, neighbor_management_ip, mac_address, bridge_port, mac_status, ip_address, if_index, arp_type, vlan_id, vlan_name, vlan_status, vlan_type, stp_port, stp_state, stp_enable, stp_path_cost, stp_designated_bridge, uptime, source`
- Effective capability keys: `l2_neighbor_local_port, l2_neighbor_remote_port, l2_neighbor_identity, l2_neighbor_chassis, l2_neighbor_management_ip, l2_mac_identity, l2_mac_bridge_port, l2_mac_status, l3_arp_identity, l3_arp_mac, l3_arp_if_index, l3_arp_type, l2_vlan_identity, l2_vlan_name, l2_vlan_status, l2_vlan_type, l2_stp_identity, l2_stp_state, l2_stp_enable, l2_stp_path_cost, l2_stp_designated_bridge`
- Effective concept keys: `local_port, neighbor_port, neighbor_name, neighbor_chassis_id, neighbor_management_ip, mac_address, bridge_port, mac_status, ip_address, if_index, arp_type, vlan_id, vlan_name, vlan_status, vlan_type, stp_port, stp_state, stp_enable, stp_path_cost, stp_designated_bridge`
- CE168 borrow: 借鉴 CE168 的信息组织思路：邻居、MAC、ARP、VLAN、STP 作为 topology summary family。
- CE168 regenerate: 按当前 effective panel_keys 重新生成 `l2_neighbors.* / l2_mac_table.* / l3_arp_table.* / l2_vlan_table.* / l2_stp_state.*`，不能直接照抄 CE168 标题和坐标。
- CE168 forbidden: 禁止直接复用 `100GE5/0`、`100GE6/0`、`40GE7/0`、`10GE8/0`、`Huawei VRP Control Plane CPU`、`Temperature Sensors`、`Top 4 by Rx Power` 这类硬编码 sample 内容。

### Huawei VRP 路由能力监控策略

- Strategy ID: `20000000-0000-4000-8000-000000000099`
- Parent: `(none)` (`-`)
- Scope: `Huawei / VRP / -`
- Contract source: `legacy_import`
- Effective signature: `d9a25c291e40`
- Dashboard role: `routing-overlay`
- Effective groups: `routing_summary`
- Effective panel keys: `l3_route_table.ipv4_count, l3_route_table.ipv6_count, routing_bgp.neighbor_total, routing_bgp.established_total, routing_ospf.neighbor_total, routing_ospf.full_total`
- Effective metric keys: `ipv4_route_count, ipv6_route_count, bgp_neighbor_total, bgp_established_total, ospf_neighbor_total, ospf_full_total`
- Effective capability keys: `ipv4_route_count, ipv6_route_count, bgp_neighbor_total, bgp_established_total, ospf_neighbor_total, ospf_full_total`
- Effective concept keys: `ipv4_route_count, ipv6_route_count, bgp_neighbor_total, bgp_established_total, ospf_neighbor_total, ospf_full_total`
- CE168 borrow: 只借鉴 CE168 对“独立 overlay”处理的思路，不借鉴具体 switch 大盘结构。
- CE168 regenerate: 按 `l3_route_table.* / routing_bgp.* / routing_ospf.*` 当前 effective panel_keys 重生 routing node。
- CE168 forbidden: 禁止把 CE168 的接口排行、板卡、温度、光模块面板混入 routing overlay。

### SNMP网络监控策略 (副本)

- Strategy ID: `23618ca7-5af3-4727-b649-aed7ecfa18f5`
- Parent: `SNMP网络监控策略` (`baf7bb34-86b7-45f8-8e28-2afce170966a`)
- Scope: `Huawei / USG / -`
- Contract source: `backend_resolver`
- Effective signature: `11530cbbb679`
- Dashboard role: `network-topology-common`
- Effective groups: `l2_neighbors, l2_mac_table, l3_arp_table, l2_vlan_table, l2_stp_state, device_metrics`
- Effective panel keys: `l2_neighbors.summary, l2_mac_table.summary, l2_mac_table.count, l3_arp_table.summary, l3_arp_table.count, l2_vlan_table.summary, l2_vlan_table.count, l2_stp_state.summary, l2_stp_state.port_count, l2_stp_state.forwarding_count, l2_stp_state.blocking_count, device_metrics.default`
- Effective metric keys: `local_port, neighbor_port, neighbor_name, neighbor_chassis_id, neighbor_management_ip, mac_address, bridge_port, mac_status, ip_address, if_index, arp_type, vlan_id, vlan_name, vlan_status, vlan_type, stp_port, stp_state, stp_enable, stp_path_cost, stp_designated_bridge, uptime, source`
- Effective capability keys: `l2_neighbor_local_port, l2_neighbor_remote_port, l2_neighbor_identity, l2_neighbor_chassis, l2_neighbor_management_ip, l2_mac_identity, l2_mac_bridge_port, l2_mac_status, l3_arp_identity, l3_arp_mac, l3_arp_if_index, l3_arp_type, l2_vlan_identity, l2_vlan_name, l2_vlan_status, l2_vlan_type, l2_stp_identity, l2_stp_state, l2_stp_enable, l2_stp_path_cost, l2_stp_designated_bridge`
- Effective concept keys: `local_port, neighbor_port, neighbor_name, neighbor_chassis_id, neighbor_management_ip, mac_address, bridge_port, mac_status, ip_address, if_index, arp_type, vlan_id, vlan_name, vlan_status, vlan_type, stp_port, stp_state, stp_enable, stp_path_cost, stp_designated_bridge`
- CE168 borrow: 借鉴 CE168 的信息组织思路：邻居、MAC、ARP、VLAN、STP 作为 topology summary family。
- CE168 regenerate: 按当前 effective panel_keys 重新生成 `l2_neighbors.* / l2_mac_table.* / l3_arp_table.* / l2_vlan_table.* / l2_stp_state.*`，不能直接照抄 CE168 标题和坐标。
- CE168 forbidden: 禁止直接复用 `100GE5/0`、`100GE6/0`、`40GE7/0`、`10GE8/0`、`Huawei VRP Control Plane CPU`、`Temperature Sensors`、`Top 4 by Rx Power` 这类硬编码 sample 内容。

### Cisco generic SNMP network monitoring strategy

- Strategy ID: `30000000-0000-4000-8000-000000000001`
- Parent: `SNMP网络监控策略` (`baf7bb34-86b7-45f8-8e28-2afce170966a`)
- Scope: `Cisco / IOS / -`
- Contract source: `legacy_import`
- Effective signature: `11530cbbb679`
- Dashboard role: `network-topology-common`
- Effective groups: `l2_neighbors, l2_mac_table, l3_arp_table, l2_vlan_table, l2_stp_state, device_metrics`
- Effective panel keys: `l2_neighbors.summary, l2_mac_table.summary, l2_mac_table.count, l3_arp_table.summary, l3_arp_table.count, l2_vlan_table.summary, l2_vlan_table.count, l2_stp_state.summary, l2_stp_state.port_count, l2_stp_state.forwarding_count, l2_stp_state.blocking_count, device_metrics.default`
- Effective metric keys: `local_port, neighbor_port, neighbor_name, neighbor_chassis_id, neighbor_management_ip, mac_address, bridge_port, mac_status, ip_address, if_index, arp_type, vlan_id, vlan_name, vlan_status, vlan_type, stp_port, stp_state, stp_enable, stp_path_cost, stp_designated_bridge, uptime, source`
- Effective capability keys: `l2_neighbor_local_port, l2_neighbor_remote_port, l2_neighbor_identity, l2_neighbor_chassis, l2_neighbor_management_ip, l2_mac_identity, l2_mac_bridge_port, l2_mac_status, l3_arp_identity, l3_arp_mac, l3_arp_if_index, l3_arp_type, l2_vlan_identity, l2_vlan_name, l2_vlan_status, l2_vlan_type, l2_stp_identity, l2_stp_state, l2_stp_enable, l2_stp_path_cost, l2_stp_designated_bridge`
- Effective concept keys: `local_port, neighbor_port, neighbor_name, neighbor_chassis_id, neighbor_management_ip, mac_address, bridge_port, mac_status, ip_address, if_index, arp_type, vlan_id, vlan_name, vlan_status, vlan_type, stp_port, stp_state, stp_enable, stp_path_cost, stp_designated_bridge`
- CE168 borrow: 借鉴 CE168 的信息组织思路：邻居、MAC、ARP、VLAN、STP 作为 topology summary family。
- CE168 regenerate: 按当前 effective panel_keys 重新生成 `l2_neighbors.* / l2_mac_table.* / l3_arp_table.* / l2_vlan_table.* / l2_stp_state.*`，不能直接照抄 CE168 标题和坐标。
- CE168 forbidden: 禁止直接复用 `100GE5/0`、`100GE6/0`、`40GE7/0`、`10GE8/0`、`Huawei VRP Control Plane CPU`、`Temperature Sensors`、`Top 4 by Rx Power` 这类硬编码 sample 内容。

### 思科网络设备监控 (副本)

- Strategy ID: `30000000-0000-4000-8000-000000000002`
- Parent: `SNMP网络监控策略` (`baf7bb34-86b7-45f8-8e28-2afce170966a`)
- Scope: `Cisco / Nexus / -`
- Contract source: `legacy_import`
- Effective signature: `11530cbbb679`
- Dashboard role: `network-topology-common`
- Effective groups: `l2_neighbors, l2_mac_table, l3_arp_table, l2_vlan_table, l2_stp_state, device_metrics`
- Effective panel keys: `l2_neighbors.summary, l2_mac_table.summary, l2_mac_table.count, l3_arp_table.summary, l3_arp_table.count, l2_vlan_table.summary, l2_vlan_table.count, l2_stp_state.summary, l2_stp_state.port_count, l2_stp_state.forwarding_count, l2_stp_state.blocking_count, device_metrics.default`
- Effective metric keys: `local_port, neighbor_port, neighbor_name, neighbor_chassis_id, neighbor_management_ip, mac_address, bridge_port, mac_status, ip_address, if_index, arp_type, vlan_id, vlan_name, vlan_status, vlan_type, stp_port, stp_state, stp_enable, stp_path_cost, stp_designated_bridge, uptime, source`
- Effective capability keys: `l2_neighbor_local_port, l2_neighbor_remote_port, l2_neighbor_identity, l2_neighbor_chassis, l2_neighbor_management_ip, l2_mac_identity, l2_mac_bridge_port, l2_mac_status, l3_arp_identity, l3_arp_mac, l3_arp_if_index, l3_arp_type, l2_vlan_identity, l2_vlan_name, l2_vlan_status, l2_vlan_type, l2_stp_identity, l2_stp_state, l2_stp_enable, l2_stp_path_cost, l2_stp_designated_bridge`
- Effective concept keys: `local_port, neighbor_port, neighbor_name, neighbor_chassis_id, neighbor_management_ip, mac_address, bridge_port, mac_status, ip_address, if_index, arp_type, vlan_id, vlan_name, vlan_status, vlan_type, stp_port, stp_state, stp_enable, stp_path_cost, stp_designated_bridge`
- CE168 borrow: 借鉴 CE168 的信息组织思路：邻居、MAC、ARP、VLAN、STP 作为 topology summary family。
- CE168 regenerate: 按当前 effective panel_keys 重新生成 `l2_neighbors.* / l2_mac_table.* / l3_arp_table.* / l2_vlan_table.* / l2_stp_state.*`，不能直接照抄 CE168 标题和坐标。
- CE168 forbidden: 禁止直接复用 `100GE5/0`、`100GE6/0`、`40GE7/0`、`10GE8/0`、`Huawei VRP Control Plane CPU`、`Temperature Sensors`、`Top 4 by Rx Power` 这类硬编码 sample 内容。

### 思科网络设备监控 (副本)

- Strategy ID: `30000000-0000-4000-8000-000000000003`
- Parent: `SNMP网络监控策略` (`baf7bb34-86b7-45f8-8e28-2afce170966a`)
- Scope: `Cisco / Nexus / N7K-C7010`
- Contract source: `legacy_import`
- Effective signature: `11530cbbb679`
- Dashboard role: `network-topology-common`
- Effective groups: `l2_neighbors, l2_mac_table, l3_arp_table, l2_vlan_table, l2_stp_state, device_metrics`
- Effective panel keys: `l2_neighbors.summary, l2_mac_table.summary, l2_mac_table.count, l3_arp_table.summary, l3_arp_table.count, l2_vlan_table.summary, l2_vlan_table.count, l2_stp_state.summary, l2_stp_state.port_count, l2_stp_state.forwarding_count, l2_stp_state.blocking_count, device_metrics.default`
- Effective metric keys: `local_port, neighbor_port, neighbor_name, neighbor_chassis_id, neighbor_management_ip, mac_address, bridge_port, mac_status, ip_address, if_index, arp_type, vlan_id, vlan_name, vlan_status, vlan_type, stp_port, stp_state, stp_enable, stp_path_cost, stp_designated_bridge, uptime, source`
- Effective capability keys: `l2_neighbor_local_port, l2_neighbor_remote_port, l2_neighbor_identity, l2_neighbor_chassis, l2_neighbor_management_ip, l2_mac_identity, l2_mac_bridge_port, l2_mac_status, l3_arp_identity, l3_arp_mac, l3_arp_if_index, l3_arp_type, l2_vlan_identity, l2_vlan_name, l2_vlan_status, l2_vlan_type, l2_stp_identity, l2_stp_state, l2_stp_enable, l2_stp_path_cost, l2_stp_designated_bridge`
- Effective concept keys: `local_port, neighbor_port, neighbor_name, neighbor_chassis_id, neighbor_management_ip, mac_address, bridge_port, mac_status, ip_address, if_index, arp_type, vlan_id, vlan_name, vlan_status, vlan_type, stp_port, stp_state, stp_enable, stp_path_cost, stp_designated_bridge`
- CE168 borrow: 借鉴 CE168 的信息组织思路：邻居、MAC、ARP、VLAN、STP 作为 topology summary family。
- CE168 regenerate: 按当前 effective panel_keys 重新生成 `l2_neighbors.* / l2_mac_table.* / l3_arp_table.* / l2_vlan_table.* / l2_stp_state.*`，不能直接照抄 CE168 标题和坐标。
- CE168 forbidden: 禁止直接复用 `100GE5/0`、`100GE6/0`、`40GE7/0`、`10GE8/0`、`Huawei VRP Control Plane CPU`、`Temperature Sensors`、`Top 4 by Rx Power` 这类硬编码 sample 内容。

### 锐捷网络设备监控 (副本)

- Strategy ID: `40000000-0000-4000-8000-000000000001`
- Parent: `SNMP网络监控策略` (`baf7bb34-86b7-45f8-8e28-2afce170966a`)
- Scope: `Ruijie / Ruijie / -`
- Contract source: `legacy_import`
- Effective signature: `11530cbbb679`
- Dashboard role: `network-topology-common`
- Effective groups: `l2_neighbors, l2_mac_table, l3_arp_table, l2_vlan_table, l2_stp_state, device_metrics`
- Effective panel keys: `l2_neighbors.summary, l2_mac_table.summary, l2_mac_table.count, l3_arp_table.summary, l3_arp_table.count, l2_vlan_table.summary, l2_vlan_table.count, l2_stp_state.summary, l2_stp_state.port_count, l2_stp_state.forwarding_count, l2_stp_state.blocking_count, device_metrics.default`
- Effective metric keys: `local_port, neighbor_port, neighbor_name, neighbor_chassis_id, neighbor_management_ip, mac_address, bridge_port, mac_status, ip_address, if_index, arp_type, vlan_id, vlan_name, vlan_status, vlan_type, stp_port, stp_state, stp_enable, stp_path_cost, stp_designated_bridge, uptime, source`
- Effective capability keys: `l2_neighbor_local_port, l2_neighbor_remote_port, l2_neighbor_identity, l2_neighbor_chassis, l2_neighbor_management_ip, l2_mac_identity, l2_mac_bridge_port, l2_mac_status, l3_arp_identity, l3_arp_mac, l3_arp_if_index, l3_arp_type, l2_vlan_identity, l2_vlan_name, l2_vlan_status, l2_vlan_type, l2_stp_identity, l2_stp_state, l2_stp_enable, l2_stp_path_cost, l2_stp_designated_bridge`
- Effective concept keys: `local_port, neighbor_port, neighbor_name, neighbor_chassis_id, neighbor_management_ip, mac_address, bridge_port, mac_status, ip_address, if_index, arp_type, vlan_id, vlan_name, vlan_status, vlan_type, stp_port, stp_state, stp_enable, stp_path_cost, stp_designated_bridge`
- CE168 borrow: 借鉴 CE168 的信息组织思路：邻居、MAC、ARP、VLAN、STP 作为 topology summary family。
- CE168 regenerate: 按当前 effective panel_keys 重新生成 `l2_neighbors.* / l2_mac_table.* / l3_arp_table.* / l2_vlan_table.* / l2_stp_state.*`，不能直接照抄 CE168 标题和坐标。
- CE168 forbidden: 禁止直接复用 `100GE5/0`、`100GE6/0`、`40GE7/0`、`10GE8/0`、`Huawei VRP Control Plane CPU`、`Temperature Sensors`、`Top 4 by Rx Power` 这类硬编码 sample 内容。

### 锐捷网络设备监控 (副本)

- Strategy ID: `40000000-0000-4000-8000-000000000002`
- Parent: `SNMP网络监控策略` (`baf7bb34-86b7-45f8-8e28-2afce170966a`)
- Scope: `Ruijie / Ruijie / RG-RSR20-XA-24`
- Contract source: `legacy_import`
- Effective signature: `11530cbbb679`
- Dashboard role: `network-topology-common`
- Effective groups: `l2_neighbors, l2_mac_table, l3_arp_table, l2_vlan_table, l2_stp_state, device_metrics`
- Effective panel keys: `l2_neighbors.summary, l2_mac_table.summary, l2_mac_table.count, l3_arp_table.summary, l3_arp_table.count, l2_vlan_table.summary, l2_vlan_table.count, l2_stp_state.summary, l2_stp_state.port_count, l2_stp_state.forwarding_count, l2_stp_state.blocking_count, device_metrics.default`
- Effective metric keys: `local_port, neighbor_port, neighbor_name, neighbor_chassis_id, neighbor_management_ip, mac_address, bridge_port, mac_status, ip_address, if_index, arp_type, vlan_id, vlan_name, vlan_status, vlan_type, stp_port, stp_state, stp_enable, stp_path_cost, stp_designated_bridge, uptime, source`
- Effective capability keys: `l2_neighbor_local_port, l2_neighbor_remote_port, l2_neighbor_identity, l2_neighbor_chassis, l2_neighbor_management_ip, l2_mac_identity, l2_mac_bridge_port, l2_mac_status, l3_arp_identity, l3_arp_mac, l3_arp_if_index, l3_arp_type, l2_vlan_identity, l2_vlan_name, l2_vlan_status, l2_vlan_type, l2_stp_identity, l2_stp_state, l2_stp_enable, l2_stp_path_cost, l2_stp_designated_bridge`
- Effective concept keys: `local_port, neighbor_port, neighbor_name, neighbor_chassis_id, neighbor_management_ip, mac_address, bridge_port, mac_status, ip_address, if_index, arp_type, vlan_id, vlan_name, vlan_status, vlan_type, stp_port, stp_state, stp_enable, stp_path_cost, stp_designated_bridge`
- CE168 borrow: 借鉴 CE168 的信息组织思路：邻居、MAC、ARP、VLAN、STP 作为 topology summary family。
- CE168 regenerate: 按当前 effective panel_keys 重新生成 `l2_neighbors.* / l2_mac_table.* / l3_arp_table.* / l2_vlan_table.* / l2_stp_state.*`，不能直接照抄 CE168 标题和坐标。
- CE168 forbidden: 禁止直接复用 `100GE5/0`、`100GE6/0`、`40GE7/0`、`10GE8/0`、`Huawei VRP Control Plane CPU`、`Temperature Sensors`、`Top 4 by Rx Power` 这类硬编码 sample 内容。

### H3C SecPath 防火墙 SNMP监控策略

- Strategy ID: `4c902a48-5f12-11f1-a9bb-0242ac14000c`
- Parent: `SNMP网络监控策略` (`baf7bb34-86b7-45f8-8e28-2afce170966a`)
- Scope: `H3C / SecPath / -`
- Contract source: `legacy_import`
- Effective signature: `11530cbbb679`
- Dashboard role: `network-topology-common`
- Effective groups: `l2_neighbors, l2_mac_table, l3_arp_table, l2_vlan_table, l2_stp_state, device_metrics`
- Effective panel keys: `l2_neighbors.summary, l2_mac_table.summary, l2_mac_table.count, l3_arp_table.summary, l3_arp_table.count, l2_vlan_table.summary, l2_vlan_table.count, l2_stp_state.summary, l2_stp_state.port_count, l2_stp_state.forwarding_count, l2_stp_state.blocking_count, device_metrics.default`
- Effective metric keys: `local_port, neighbor_port, neighbor_name, neighbor_chassis_id, neighbor_management_ip, mac_address, bridge_port, mac_status, ip_address, if_index, arp_type, vlan_id, vlan_name, vlan_status, vlan_type, stp_port, stp_state, stp_enable, stp_path_cost, stp_designated_bridge, uptime, source`
- Effective capability keys: `l2_neighbor_local_port, l2_neighbor_remote_port, l2_neighbor_identity, l2_neighbor_chassis, l2_neighbor_management_ip, l2_mac_identity, l2_mac_bridge_port, l2_mac_status, l3_arp_identity, l3_arp_mac, l3_arp_if_index, l3_arp_type, l2_vlan_identity, l2_vlan_name, l2_vlan_status, l2_vlan_type, l2_stp_identity, l2_stp_state, l2_stp_enable, l2_stp_path_cost, l2_stp_designated_bridge`
- Effective concept keys: `local_port, neighbor_port, neighbor_name, neighbor_chassis_id, neighbor_management_ip, mac_address, bridge_port, mac_status, ip_address, if_index, arp_type, vlan_id, vlan_name, vlan_status, vlan_type, stp_port, stp_state, stp_enable, stp_path_cost, stp_designated_bridge`
- CE168 borrow: 借鉴 CE168 的信息组织思路：邻居、MAC、ARP、VLAN、STP 作为 topology summary family。
- CE168 regenerate: 按当前 effective panel_keys 重新生成 `l2_neighbors.* / l2_mac_table.* / l3_arp_table.* / l2_vlan_table.* / l2_stp_state.*`，不能直接照抄 CE168 标题和坐标。
- CE168 forbidden: 禁止直接复用 `100GE5/0`、`100GE6/0`、`40GE7/0`、`10GE8/0`、`Huawei VRP Control Plane CPU`、`Temperature Sensors`、`Top 4 by Rx Power` 这类硬编码 sample 内容。

### 迈普通用SNMP网络监控策略

- Strategy ID: `50000000-0000-4000-8000-000000000001`
- Parent: `SNMP网络监控策略` (`baf7bb34-86b7-45f8-8e28-2afce170966a`)
- Scope: `Maipu / MyPower / -`
- Contract source: `legacy_import`
- Effective signature: `11530cbbb679`
- Dashboard role: `network-topology-common`
- Effective groups: `l2_neighbors, l2_mac_table, l3_arp_table, l2_vlan_table, l2_stp_state, device_metrics`
- Effective panel keys: `l2_neighbors.summary, l2_mac_table.summary, l2_mac_table.count, l3_arp_table.summary, l3_arp_table.count, l2_vlan_table.summary, l2_vlan_table.count, l2_stp_state.summary, l2_stp_state.port_count, l2_stp_state.forwarding_count, l2_stp_state.blocking_count, device_metrics.default`
- Effective metric keys: `local_port, neighbor_port, neighbor_name, neighbor_chassis_id, neighbor_management_ip, mac_address, bridge_port, mac_status, ip_address, if_index, arp_type, vlan_id, vlan_name, vlan_status, vlan_type, stp_port, stp_state, stp_enable, stp_path_cost, stp_designated_bridge, uptime, source`
- Effective capability keys: `l2_neighbor_local_port, l2_neighbor_remote_port, l2_neighbor_identity, l2_neighbor_chassis, l2_neighbor_management_ip, l2_mac_identity, l2_mac_bridge_port, l2_mac_status, l3_arp_identity, l3_arp_mac, l3_arp_if_index, l3_arp_type, l2_vlan_identity, l2_vlan_name, l2_vlan_status, l2_vlan_type, l2_stp_identity, l2_stp_state, l2_stp_enable, l2_stp_path_cost, l2_stp_designated_bridge`
- Effective concept keys: `local_port, neighbor_port, neighbor_name, neighbor_chassis_id, neighbor_management_ip, mac_address, bridge_port, mac_status, ip_address, if_index, arp_type, vlan_id, vlan_name, vlan_status, vlan_type, stp_port, stp_state, stp_enable, stp_path_cost, stp_designated_bridge`
- CE168 borrow: 借鉴 CE168 的信息组织思路：邻居、MAC、ARP、VLAN、STP 作为 topology summary family。
- CE168 regenerate: 按当前 effective panel_keys 重新生成 `l2_neighbors.* / l2_mac_table.* / l3_arp_table.* / l2_vlan_table.* / l2_stp_state.*`，不能直接照抄 CE168 标题和坐标。
- CE168 forbidden: 禁止直接复用 `100GE5/0`、`100GE6/0`、`40GE7/0`、`10GE8/0`、`Huawei VRP Control Plane CPU`、`Temperature Sensors`、`Top 4 by Rx Power` 这类硬编码 sample 内容。

### 烽火通用SNMP网络监控策略

- Strategy ID: `50000000-0000-4000-8000-000000000002`
- Parent: `SNMP网络监控策略` (`baf7bb34-86b7-45f8-8e28-2afce170966a`)
- Scope: `FiberHome / Fengine / -`
- Contract source: `legacy_import`
- Effective signature: `11530cbbb679`
- Dashboard role: `network-topology-common`
- Effective groups: `l2_neighbors, l2_mac_table, l3_arp_table, l2_vlan_table, l2_stp_state, device_metrics`
- Effective panel keys: `l2_neighbors.summary, l2_mac_table.summary, l2_mac_table.count, l3_arp_table.summary, l3_arp_table.count, l2_vlan_table.summary, l2_vlan_table.count, l2_stp_state.summary, l2_stp_state.port_count, l2_stp_state.forwarding_count, l2_stp_state.blocking_count, device_metrics.default`
- Effective metric keys: `local_port, neighbor_port, neighbor_name, neighbor_chassis_id, neighbor_management_ip, mac_address, bridge_port, mac_status, ip_address, if_index, arp_type, vlan_id, vlan_name, vlan_status, vlan_type, stp_port, stp_state, stp_enable, stp_path_cost, stp_designated_bridge, uptime, source`
- Effective capability keys: `l2_neighbor_local_port, l2_neighbor_remote_port, l2_neighbor_identity, l2_neighbor_chassis, l2_neighbor_management_ip, l2_mac_identity, l2_mac_bridge_port, l2_mac_status, l3_arp_identity, l3_arp_mac, l3_arp_if_index, l3_arp_type, l2_vlan_identity, l2_vlan_name, l2_vlan_status, l2_vlan_type, l2_stp_identity, l2_stp_state, l2_stp_enable, l2_stp_path_cost, l2_stp_designated_bridge`
- Effective concept keys: `local_port, neighbor_port, neighbor_name, neighbor_chassis_id, neighbor_management_ip, mac_address, bridge_port, mac_status, ip_address, if_index, arp_type, vlan_id, vlan_name, vlan_status, vlan_type, stp_port, stp_state, stp_enable, stp_path_cost, stp_designated_bridge`
- CE168 borrow: 借鉴 CE168 的信息组织思路：邻居、MAC、ARP、VLAN、STP 作为 topology summary family。
- CE168 regenerate: 按当前 effective panel_keys 重新生成 `l2_neighbors.* / l2_mac_table.* / l3_arp_table.* / l2_vlan_table.* / l2_stp_state.*`，不能直接照抄 CE168 标题和坐标。
- CE168 forbidden: 禁止直接复用 `100GE5/0`、`100GE6/0`、`40GE7/0`、`10GE8/0`、`Huawei VRP Control Plane CPU`、`Temperature Sensors`、`Top 4 by Rx Power` 这类硬编码 sample 内容。

### SNMP网络监控策略

- Strategy ID: `baf7bb34-86b7-45f8-8e28-2afce170966a`
- Parent: `(none)` (`-`)
- Scope: `- / - / -`
- Contract source: `explicit_contract`
- Effective signature: `11530cbbb679`
- Dashboard role: `network-topology-common`
- Effective groups: `l2_neighbors, l2_mac_table, l3_arp_table, l2_vlan_table, l2_stp_state, device_metrics`
- Effective panel keys: `l2_neighbors.summary, l2_mac_table.summary, l2_mac_table.count, l3_arp_table.summary, l3_arp_table.count, l2_vlan_table.summary, l2_vlan_table.count, l2_stp_state.summary, l2_stp_state.port_count, l2_stp_state.forwarding_count, l2_stp_state.blocking_count, device_metrics.default`
- Effective metric keys: `local_port, neighbor_port, neighbor_name, neighbor_chassis_id, neighbor_management_ip, mac_address, bridge_port, mac_status, ip_address, if_index, arp_type, vlan_id, vlan_name, vlan_status, vlan_type, stp_port, stp_state, stp_enable, stp_path_cost, stp_designated_bridge, uptime, source`
- Effective capability keys: `l2_neighbor_local_port, l2_neighbor_remote_port, l2_neighbor_identity, l2_neighbor_chassis, l2_neighbor_management_ip, l2_mac_identity, l2_mac_bridge_port, l2_mac_status, l3_arp_identity, l3_arp_mac, l3_arp_if_index, l3_arp_type, l2_vlan_identity, l2_vlan_name, l2_vlan_status, l2_vlan_type, l2_stp_identity, l2_stp_state, l2_stp_enable, l2_stp_path_cost, l2_stp_designated_bridge`
- Effective concept keys: `local_port, neighbor_port, neighbor_name, neighbor_chassis_id, neighbor_management_ip, mac_address, bridge_port, mac_status, ip_address, if_index, arp_type, vlan_id, vlan_name, vlan_status, vlan_type, stp_port, stp_state, stp_enable, stp_path_cost, stp_designated_bridge`
- CE168 borrow: 借鉴 CE168 的信息组织思路：邻居、MAC、ARP、VLAN、STP 作为 topology summary family。
- CE168 regenerate: 按当前 effective panel_keys 重新生成 `l2_neighbors.* / l2_mac_table.* / l3_arp_table.* / l2_vlan_table.* / l2_stp_state.*`，不能直接照抄 CE168 标题和坐标。
- CE168 forbidden: 禁止直接复用 `100GE5/0`、`100GE6/0`、`40GE7/0`、`10GE8/0`、`Huawei VRP Control Plane CPU`、`Temperature Sensors`、`Top 4 by Rx Power` 这类硬编码 sample 内容。

### 服务器带外SNMP通用监控策略

- Strategy ID: `server_oob_snmp_common_strategy`
- Parent: `服务器带外SNMP监控策略` (`server_oob_snmp_strategy`)
- Scope: `- / - / -`
- Contract source: `legacy_import`
- Effective signature: `0bd7d00bb3aa`
- Dashboard role: `server-oob-overlay`
- Effective groups: `device_metrics`
- Effective panel keys: `device_metrics.default`
- Effective metric keys: `oob_sysDescr, oob_sysObjectID, oob_sysUpTime, sysName`
- Effective capability keys: `(none)`
- Effective concept keys: `(none)`
- CE168 borrow: 不从 CE168 借鉴结构，最多借鉴“显式 summary + detail”这种抽象层次。
- CE168 regenerate: 按当前 `device_metrics.default` 的有效字段重生 summary panel。
- CE168 forbidden: 禁止直接复用任何 CE168 switch/chassis/interface 语义面板。

### 服务器带外SNMP监控策略

- Strategy ID: `server_oob_snmp_strategy`
- Parent: `(none)` (`-`)
- Scope: `- / - / -`
- Contract source: `legacy_import`
- Effective signature: `0bd7d00bb3aa`
- Dashboard role: `server-oob-overlay`
- Effective groups: `device_metrics`
- Effective panel keys: `device_metrics.default`
- Effective metric keys: `oob_sysDescr, oob_sysObjectID, oob_sysUpTime, sysName`
- Effective capability keys: `(none)`
- Effective concept keys: `(none)`
- CE168 borrow: 不从 CE168 借鉴结构，最多借鉴“显式 summary + detail”这种抽象层次。
- CE168 regenerate: 按当前 `device_metrics.default` 的有效字段重生 summary panel。
- CE168 forbidden: 禁止直接复用任何 CE168 switch/chassis/interface 语义面板。

### 曙光服务器带外SNMP硬件监控策略

- Strategy ID: `server_oob_snmp_sugon_strategy`
- Parent: `服务器带外SNMP监控策略` (`server_oob_snmp_strategy`)
- Scope: `Sugon / - / -`
- Contract source: `legacy_import`
- Effective signature: `5c14ce2706c2`
- Dashboard role: `server-oob-overlay`
- Effective groups: `device_metrics`
- Effective panel keys: `device_metrics.default`
- Effective metric keys: `oob_sysDescr, oob_sysObjectID, oob_sysUpTime, sysName, sugonServerModel, oob_sugonSensorCount`
- Effective capability keys: `(none)`
- Effective concept keys: `(none)`
- CE168 borrow: 不从 CE168 借鉴结构，最多借鉴“显式 summary + detail”这种抽象层次。
- CE168 regenerate: 按当前 `device_metrics.default` 的有效字段重生 summary panel。
- CE168 forbidden: 禁止直接复用任何 CE168 switch/chassis/interface 语义面板。

## 5. Hard Rule For The Next Dashboard Batch

Dashboard regeneration must use the inventory above as its semantic source of truth.

That means:

- do not copy CE168 panel titles, port names, or coordinates directly;
- do not create vendor-specific CPU/interface/optics panels unless the effective contract justifies them;
- do let different strategies share the same dashboard signature when their effective metrics are identical;
- do keep the suite-root + strategy-dashboard-tree model, and let strategy node differences come from effective metrics first.

