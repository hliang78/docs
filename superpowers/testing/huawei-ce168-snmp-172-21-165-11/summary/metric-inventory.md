# Huawei CE168 SNMP Metric Inventory

## Target

- IP: 172.21.165.11
- SNMP: v2c read-only exploration
- Device family observed from SNMP: HUAWEI CE16808
- Software observed from SNMP: VRP V200R024C00SPC500
- sysObjectID: .1.3.6.1.4.1.2011.2.239.59
- sysName: SH-HAP-ZJIDC-STO-CSW-HW-CE16808-1
- sysLocation: Beijing China
- sysUpTime at first probe: 365 days, 21:27:44.21

## Basic System

Observed system scalar support:

| Concept | OID | Supported | Notes |
|---|---|---:|---|
| sysDescr | .1.3.6.1.2.1.1.1.0 | yes | Identifies Huawei VRP and CE16808 model |
| sysObjectID | .1.3.6.1.2.1.1.2.0 | yes | Huawei enterprise object .1.3.6.1.4.1.2011.2.239.59 |
| sysUpTime | .1.3.6.1.2.1.1.3.0 | yes | Useful for device availability and reboot detection |
| sysName | .1.3.6.1.2.1.1.5.0 | yes | Stable device label |
| sysLocation | .1.3.6.1.2.1.1.6.0 | yes | Location metadata available |

## Entity Inventory

Metric group candidate: `entity_inventory`

Raw walk file: `raw/02-entity-physical-table.txt`

ENTITY-MIB physical table is supported. The walk returned 5805 lines and 387 indexed entities per core column. Sample names include `CE16808 frame`, `LPU slot 1`, `CEL48XSFD-G 1`, and interface entities such as `10GE1/0/0`.

Observed `entPhysicalClass` distribution:

| Class value | Count | Notes |
|---:|---:|---|
| 10 | 330 | Port-like physical entities |
| 9 | 17 | Module/container-like entities |
| 7 | 3 | Chassis/stack-level entities |
| 6 | 4 | Power-supply-like entities |
| 5 | 32 | Sensor/fan-like entities |
| 3 | 1 | Container/root-like entity |

| Concept | Metric key | OID family | Supported | Notes |
|---|---|---|---:|---|
| Entity description | entity_descr | .1.3.6.1.2.1.47.1.1.1.1.2 | yes | 387 indexed rows |
| Entity class | entity_class | .1.3.6.1.2.1.47.1.1.1.1.5 | yes | Needed for hardware grouping |
| Entity name | entity_name | .1.3.6.1.2.1.47.1.1.1.1.7 | yes | Includes chassis, slots, cards, and ports |
| Entity serial number | entity_serial | .1.3.6.1.2.1.47.1.1.1.1.11 | yes | 387 indexed rows; empty values need filtering |
| Entity model | entity_model | .1.3.6.1.2.1.47.1.1.1.1.13 | yes | 387 indexed rows; empty values need filtering |

## Interface Basic And Traffic

Metric group candidate: `interface_basic`

Raw walk files:

- `raw/03-if-table.txt`
- `raw/04-ifx-table.txt`

The target exposes 192 interfaces in both `ifTable` and `ifXTable`. High-capacity counters are present for all 192 interfaces, so CE168 strategy should prefer `ifHCInOctets`, `ifHCOutOctets`, and `ifHighSpeed`. Sample interface names include `Sip9/0/0`, `MEth0/0/0`, `Eth-Trunk1`, and `10GE8/0/0`.

| Concept | Metric key | Preferred OID | Fallback OID | Supported | Notes |
|---|---|---|---|---:|---|
| Interface description | if_descr | .1.3.6.1.2.1.2.2.1.2 | | yes | 192 rows |
| Interface name | if_name | .1.3.6.1.2.1.31.1.1.1.1 | .1.3.6.1.2.1.2.2.1.2 | yes | 192 rows |
| Interface alias | if_alias | .1.3.6.1.2.1.31.1.1.1.18 | | yes | 192 rows |
| Admin status | if_admin_status | .1.3.6.1.2.1.2.2.1.7 | | yes | 192 rows |
| Oper status | if_oper_status | .1.3.6.1.2.1.2.2.1.8 | | yes | 192 rows |
| In traffic | if_in_rate | .1.3.6.1.2.1.31.1.1.1.6 | .1.3.6.1.2.1.2.2.1.10 | yes | Prefer 64-bit HC counter |
| Out traffic | if_out_rate | .1.3.6.1.2.1.31.1.1.1.10 | .1.3.6.1.2.1.2.2.1.16 | yes | Prefer 64-bit HC counter |
| Interface speed | if_speed_bps | .1.3.6.1.2.1.31.1.1.1.15 | .1.3.6.1.2.1.2.2.1.5 | yes | `ifHighSpeed` is Mbps; values include 10000, 200000, 400000 |

## Interface Quality And Packet Mix

Metric group candidate: `interface_quality`

The target exposes error, discard, and high-capacity packet mix counters for all 192 interfaces.

| Concept | Metric key | OID | Supported | Notes |
|---|---|---|---:|---|
| In errors | if_in_error_rate | .1.3.6.1.2.1.2.2.1.14 | yes | 192 rows |
| Out errors | if_out_error_rate | .1.3.6.1.2.1.2.2.1.20 | yes | 192 rows |
| In discards | if_in_discard_rate | .1.3.6.1.2.1.2.2.1.13 | yes | 192 rows |
| Out discards | if_out_discard_rate | .1.3.6.1.2.1.2.2.1.19 | yes | 192 rows |
| FCS/CRC errors | if_crc_error_rate | .1.3.6.1.2.1.10.7.2.1.3 | yes | 156 physical Ethernet rows; raw file `raw/05-etherlike-dot3-stats.txt` |
| In unicast packets | if_in_unicast_pps | .1.3.6.1.2.1.31.1.1.1.7 | yes | 192 rows |
| In multicast packets | if_in_multicast_pps | .1.3.6.1.2.1.31.1.1.1.8 | yes | 192 rows |
| In broadcast packets | if_in_broadcast_pps | .1.3.6.1.2.1.31.1.1.1.9 | yes | 192 rows |
| Out unicast packets | if_out_unicast_pps | .1.3.6.1.2.1.31.1.1.1.11 | yes | 192 rows |
| Out multicast packets | if_out_multicast_pps | .1.3.6.1.2.1.31.1.1.1.12 | yes | 192 rows |
| Out broadcast packets | if_out_broadcast_pps | .1.3.6.1.2.1.31.1.1.1.13 | yes | 192 rows |

## Hardware Health

Metric group candidates: `hardware_health`, `thermal_sensors`, `fan_status`, `power_supply`.

Raw walk files:

- `raw/06-huawei-entity-state-table.txt`
- `raw/07-huawei-fan-table.txt`
- `raw/08-huawei-power-table.txt`

Huawei private entity state table is supported and returned 8514 lines. The table exposes 387 entity rows for CPU, memory, memory size, temperature, voltage, thresholds, and max CPU usage columns. Most port entities return zero for board-level values, so collection should filter or classify rows by `entPhysicalIndex` and entity name/class.

Observed non-zero module values:

| Entity | CPU % | Memory % | Temperature C | Notes |
|---|---:|---:|---:|---|
| CEL36CQFD-G 5 | 16 | 14 | 33 | LPU/module |
| CEL36CQFD-G 6 | 17 | 14 | 33 | LPU/module |
| CEL36LQFD-G 7 | 11 | 23 | 31 | LPU/module |
| CEL48XSFD-G 8 | 9 | 19 | 26 | LPU/module |
| CE-MPUD-HALF 9 | 3 | 9 | 28 | MPU/module |
| CE-MPUD-HALF 10 | 1 | 6 | 28 | MPU/module |
| CE-SFU08G-G SFU3 | 6 | 16 | 36 | SFU/module |
| CE-SFU08G-G SFU4 | 6 | 16 | 36 | SFU/module |
| CE-SFU08G-G SFU5 | 5 | 16 | 35 | SFU/module |
| CE-SFU08G-G SFU6 | 5 | 16 | 36 | SFU/module |
| CE-SFU08G-G SFU7 | 5 | 16 | 36 | SFU/module |
| CE-SFU08G-G SFU8 | 6 | 16 | 37 | SFU/module |
| POWER 1 | 0 | 0 | 30 | Power module temperature |
| POWER 2 | 0 | 0 | 30 | Power module temperature |
| POWER 3 | 0 | 0 | 29 | Power module temperature |
| POWER 4 | 0 | 0 | 29 | Power module temperature |

Observed fan modules:

| Fan | Speed | Present | State | Notes |
|---|---:|---:|---:|---|
| FAN1 | 43 | 1 | 1 | Present and normal by observed enum pattern |
| FAN2 | 43 | 1 | 1 | Present and normal by observed enum pattern |
| FAN3 | 43 | 1 | 1 | Present and normal by observed enum pattern |

Observed power modules:

| Power | Present | State | Current | Voltage | Power | Notes |
|---|---:|---:|---:|---:|---:|---|
| PWR1 | 1 | 1 | 10375 | 53509 | 549 | Present and normal by observed enum pattern |
| PWR2 | 1 | 1 | 9625 | 53464 | 510 | Present and normal by observed enum pattern |
| PWR3 | 1 | 1 | 12125 | 53464 | 642 | Present and normal by observed enum pattern |
| PWR4 | 1 | 1 | 10250 | 53529 | 543 | Present and normal by observed enum pattern |

| Concept | Metric key | OID | Supported | Notes |
|---|---|---|---:|---|
| Entity operational status | entity_oper_status | .1.3.6.1.4.1.2011.5.25.31.1.1.1.1.2 | yes | 387 rows |
| Entity CPU usage | cpu_usage_direct | .1.3.6.1.4.1.2011.5.25.31.1.1.1.1.5 | yes | Per module; aggregate max/avg for device overview |
| Entity memory usage | memory_usage_direct | .1.3.6.1.4.1.2011.5.25.31.1.1.1.1.7 | yes | Per module; aggregate max/avg for device overview |
| Entity memory size | memory_size_mb | .1.3.6.1.4.1.2011.5.25.31.1.1.1.1.19 | yes | Per module |
| Entity temperature | sensor_temperature_celsius | .1.3.6.1.4.1.2011.5.25.31.1.1.1.1.11 | yes | Per module |
| Entity voltage | entity_voltage | .1.3.6.1.4.1.2011.5.25.31.1.1.1.1.13 | yes | Raw units need conversion confirmation |
| Entity CPU max usage | cpu_usage_max | .1.3.6.1.4.1.2011.5.25.31.1.1.1.1.29 | yes | Per module |
| Optical power Rx | optical_rx_power_raw | .1.3.6.1.4.1.2011.5.25.31.1.1.1.1.22 | no | This column did not appear in this walk |
| Board power | board_power_watts | .1.3.6.1.4.1.2011.5.25.31.1.1.1.1.24 | no | This column did not appear in this walk |
| Fan speed | fan_speed | .1.3.6.1.4.1.2011.5.25.31.1.1.10.1.5 | yes | 3 rows |
| Fan present | fan_present | .1.3.6.1.4.1.2011.5.25.31.1.1.10.1.6 | yes | 3 rows |
| Fan state | fan_state | .1.3.6.1.4.1.2011.5.25.31.1.1.10.1.7 | yes | 3 rows |
| PSU present | power_present | .1.3.6.1.4.1.2011.5.25.31.1.1.18.1.5 | yes | 4 rows |
| PSU state | power_state | .1.3.6.1.4.1.2011.5.25.31.1.1.18.1.6 | yes | 4 rows |
| PSU current | power_current | .1.3.6.1.4.1.2011.5.25.31.1.1.18.1.7 | yes | 4 rows |
| PSU voltage | power_voltage | .1.3.6.1.4.1.2011.5.25.31.1.1.18.1.8 | yes | 4 rows |
| PSU power | power_watts | .1.3.6.1.4.1.2011.5.25.31.1.1.18.1.10 | yes | 4 rows |

## L2/L3 Resources

Metric group candidate: `l2_l3_resources`

Raw walk files:

- `raw/09-lldp-local.txt`
- `raw/10-lldp-remote.txt`
- `raw/11-bridge-mib.txt`
- `raw/12-q-bridge-mib.txt`
- `raw/13-ip-net-to-media.txt`
- `raw/14-ip-forwarding-table.txt`
- `raw/15-ospf-mib.txt`
- `raw/16-bgp4-mib.txt`

Standard LLDP-MIB, OSPF-MIB, and BGP4-MIB are not exposed by the current SNMP view. Bridge, Q-BRIDGE, ARP, and IPv4 forwarding tables are exposed.

Observed VLAN IDs from Q-BRIDGE: `1`, `10`, `66`, `2153`, `2176`, `2178`, `2203`, `2251`.

| Concept | Metric key | OID family | Supported | Notes |
|---|---|---|---:|---|
| LLDP neighbor count/detail | lldp_neighbor | .1.0.8802.1.1.2 | no | SNMP returns `No Such Object`; use CLI or adjust SNMP view |
| MAC address entries | mac_entries | .1.3.6.1.2.1.17.4.3 | yes | 164 FDB address/status rows observed |
| VLAN inventory | vlan_count | .1.3.6.1.2.1.17.7 | yes | 8 VLANs observed from Q-BRIDGE |
| STP state | stp_state | .1.3.6.1.2.1.17.2 | yes | Bridge STP branch returned data |
| ARP entries | arp_entries | .1.3.6.1.2.1.4.22 | yes | 776 raw rows across ARP columns |
| IPv4 route count | ipv4_route_count | .1.3.6.1.2.1.4.24.3.0 | yes | Scalar returned 25; forwarding table returned 710 raw rows |
| OSPF neighbor state | ospf_neighbor_state | .1.3.6.1.2.1.14 | no | Standard OSPF-MIB returns `No Such Object` |
| BGP peer state | bgp_peer_state | .1.3.6.1.2.1.15 | no | Standard BGP4-MIB returns `No Such Object` |

## Packet Buffer And QoS

Metric group candidate: `packet_buffer`

Raw walk files:

- `raw/17-huawei-memory-mib.txt`
- `raw/18-huawei-xqos-mib.txt`

Huawei memory branch `.1.3.6.1.4.1.2011.6.2` is not exposed by the current SNMP view. Huawei XQoS branch `.1.3.6.1.4.1.2011.5.25.32` is exposed and returned 30228 raw rows, but local Huawei MIB names are not installed, so the exact buffer/resource object names are not yet confirmed.

Observed XQoS shape:

| Numeric branch | Raw row count | Current interpretation |
|---|---:|---|
| .1.3.6.1.4.1.2011.5.25.32.4.1.4.3.3.1 | 29216 | Large QoS statistics table; needs Huawei MIB translation before strategy use |
| .1.3.6.1.4.1.2011.5.25.32.4.1.1.16.1.5 | 347 | QoS-related table column; object name unknown locally |
| .1.3.6.1.4.1.2011.5.25.32.4.1.1.16.1.6 | 347 | QoS-related table column; object name unknown locally |
| .1.3.6.1.4.1.2011.5.25.32.4.1.1.14.1.3 | 72 | QoS-related table column; object name unknown locally |
| .1.3.6.1.4.1.2011.5.25.32.4.1.1.14.1.4 | 72 | QoS-related table column; object name unknown locally |
| .1.3.6.1.4.1.2011.5.25.32.4.1.1.14.1.5 | 72 | QoS-related table column; object name unknown locally |

| Concept | Metric key | OID family | Supported | Notes |
|---|---|---|---:|---|
| Packet buffer usage | packet_buffer_usage | Huawei memory/XQoS branches | partial | XQoS exists, but object meaning needs MIB translation |
| Interface buffer usage | if_buffer_usage | Huawei XQoS branch | partial | Do not add to P0 strategy until object names and units are verified |
| QoS resource overrun | qos_resource_overrun | Huawei XQoS traps/counters | partial | Candidate for alert/event integration |

## Recommended OneOPS Metric Groups

| Group key | Entity | Data shape | Priority | Source | Recommendation |
|---|---|---|---:|---|---|
| system_basic | device/module | timeseries | P0 | Huawei entity state | Use per-module CPU/memory and aggregate max/avg for overview |
| interface_basic | interface | table_timeseries | P0 | IF-MIB + ifXTable | Use `ifHCInOctets`, `ifHCOutOctets`, `ifHighSpeed`, `ifName`, `ifAlias` |
| interface_quality | interface | table_timeseries | P0 | IF-MIB + EtherLike-MIB | Include errors, discards, FCS/CRC, and HC packet mix |
| hardware_health | module | table_timeseries | P1 | ENTITY-MIB + HUAWEI-ENTITY-EXTENT-MIB | Include module operational status, CPU, memory, temp, voltage |
| fan_status | module | table | P1 | Huawei fan table | 3 fan rows observed |
| power_supply | module | table | P1 | Huawei power table | 4 PSU rows observed |
| optical_transceiver | interface/module | table_timeseries | P2 | Huawei private or other optical MIB | Not confirmed by current entity state walk |
| l2_l3_resources | device | table | P2 | Bridge/Q-BRIDGE/IP-MIB | MAC/VLAN/ARP/routes supported; LLDP/OSPF/BGP not exposed through standard MIBs |
| packet_buffer | interface/device | timeseries | P2 | Huawei XQoS | Partial; needs Huawei MIB translation before use |

## Bootstrap Change Candidates

- Replace 32-bit `ifInOctets` and `ifOutOctets` with `ifHCInOctets` and `ifHCOutOctets` for this Huawei CE168 strategy.
- Add `ifHighSpeed` and calculate interface utilization from Mbps units.
- Add `ifName` and `ifAlias` to improve panel labels.
- Keep `ifSpeed`, `ifDescr`, `ifInOctets`, and `ifOutOctets` as fallback only.
- Add `ifHCInUcastPkts`, `ifHCInMulticastPkts`, `ifHCInBroadcastPkts`, `ifHCOutUcastPkts`, `ifHCOutMulticastPkts`, and `ifHCOutBroadcastPkts` for traffic mix.
- Add `dot3StatsFCSErrors` for CRC/FCS error panels on physical Ethernet interfaces.
- Add Huawei entity state table CPU, memory, memory size, temperature, voltage, and CPU max usage as module-scoped metrics.
- Add Huawei fan and power tables as separate groups.
- Treat MAC/VLAN/ARP/route counts as P2 because table sizes and dashboard intent need separate design.
- Do not add packet buffer/XQoS to the main strategy until Huawei MIB names and units are translated.
