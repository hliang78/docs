# obsflow collection / attention / dataset / fact_type 对照（2026-05-26）

## 先说结论

`obsflow` 本身不是直接按 OID 或 CLI 命令决定“采哪些指标”，而是按下面 4 层逐步收敛：

1. 处理任务先决定需要哪些 `collection`
2. `attentions` 决定每个 `collection` 允许走哪些采集方式
3. `dc2_only` 下，`collection` 会被映射成一组 `dataset_keys`
4. DC2 执行后产出 `fact_type`，obsflow 再按 `collection -> fact_type` 去消费

## 一、任务 -> collection

常见 obsflow 处理任务与输入 collection：

| 处理任务 | collection |
| --- | --- |
| `neighbor_links` / `L2nodeMapServer` | `NeighborLldp`、`NeighborCdp` |
| `device_ports` / `DevicePorts` | `IfTable`、`SnmpIfEntry`，可附带 `SnmpIpAddrEntry`、`SnmpIfHighSpeed` |
| `arp_mac` / `ArpTableServer2` | `SwitchArpTable`、`MACTABLE` |

代码参考：

- [task_contract.go](../OneOps/app/obsflow/api/task_contract.go)
- [neighbor_links/task.go](../OneOps/app/obsflow/tasks/neighbor_links/task.go)
- [device_ports/task.go](../OneOps/app/obsflow/tasks/device_ports/task.go)
- [arp_mac/task.go](../OneOps/app/obsflow/tasks/arp_mac/task.go)

## 二、collection -> attention 采集方式

`attentions` 负责声明某类设备在某个 collection 下允许的采集组合。

obsflow 当前闭环校验关注的 collection 与采集方式：

| collection | 合法 collectMethod / stage method |
| --- | --- |
| `IfTable` / `SnmpIfEntry` | `SNMP` / `snmpIftable` |
| `SnmpIpAddrEntry` | `SNMP` / `snmpIpAddrEntry` |
| `SnmpIfHighSpeed` | `SNMP` / `snmpIfHighSpeed` |
| `NeighborCdp` | `SNMP` / `snmpCDP` |
| `NeighborLldp` | `SSH` / `sshLldp`，或 `TELNET` / `telnetLldp` |
| `SwitchArpTable` | `SNMP` / `snmpArp` |
| `MACTABLE` | `SNMP` / `snmpMacTable`，或 `SSH` / `sshMacTable`，或 `TELNET` / `telnetMacTable` |

代码参考：

- [config_collection_contract_store.go](../OneOps/app/obsflow/adapters/config_collection_contract_store.go)

## 三、dc2_only 下 collection -> dataset_keys

静态映射：

| collection | 默认 dataset_keys |
| --- | --- |
| `IfTable` | `snmp_if_table` |
| `SnmpIfEntry` | `snmp_if_table` |
| `SnmpIfHighSpeed` | `snmp_if_highspeed` |
| `SnmpIpAddrEntry` | `snmp_ip_addr_entry` |
| `SwitchArpTable` | `snmp_arp` |
| `NeighborLldp` | `snmp_if_table`、`snmp_lldpRemEntry`、`cli_lldp_neighbors` |
| `NeighborCdp` | `snmp_if_table`、`snmp_cdp_neighbors`、`cli_cdp_neighbors` |

特殊项：

| collection | dataset_keys 规则 |
| --- | --- |
| `MACTABLE` | 不是固定值，按目标设备 `attentions` 中的 `collectMethod / stage method` 动态推导 |

`MACTABLE` 动态映射规则：

| collectMethod / stage method | dataset_key |
| --- | --- |
| `SNMP` / `snmpMacTable` | `snmp_dot1dTpFdbTable` |
| `SSH` / `sshMacTable` | `cli_mac_table` |
| `TELNET` / `telnetMacTable` | `cli_mac_table` |

代码参考：

- [runtime_ports.go](../OneOps/app/obsflow/bridge/runtime_ports.go)

## 四、DC2 facts -> obsflow collection 读取

obsflow 在 `dc2_only` 下不是直接读 dataset，而是读 DC2 产出的 `fact_type`。

当前映射如下：

| collection | fact_type 过滤 |
| --- | --- |
| `NeighborCdp` | `topology_neighbor` 且 `protocol=cdp` |
| `NeighborLldp` | `topology_neighbor` 且 `protocol=lldp` |
| `IfTable` | `interface` |
| `SnmpIfEntry` | `interface` |
| `SnmpIfHighSpeed` | `interface` |
| `SnmpIpAddrEntry` | `interface_ip` |
| `SwitchArpTable` | `arp_entry` |
| `MACTABLE` | `mac_table_entry` |

代码参考：

- [dc2_fact_bundle_store.go](../OneOps/app/obsflow/adapters/dc2_fact_bundle_store.go)

## 五、如何理解“obsflow 决定采哪些指标”

更准确的说法应该是：

- obsflow 决定“需要哪些 collection”
- attentions 决定“这些 collection 允许走哪些采集方式”
- `dc2_only` 桥接决定“这些 collection 落成哪些 dataset_keys”
- DC2 再决定“这些 dataset 最终产出哪些 fact_type”

所以：

- 如果你要改“这个任务要不要采 LLDP / ARP / MAC / ifTable”，主要看 obsflow 的任务合同和 workflow collection 规则
- 如果你要改“LLDP 走 SNMP 还是 SSH/TELNET”，主要看 `attentions`
- 如果你要改“collection 对应哪组 DC2 dataset”，主要看 obsflow bridge 的 `dc2_only` 映射
- 如果你要改“某类设备命中哪套 DC2 画像”，主要看 `device_collection2.collection_profiles`
- 如果你要改“采集执行对象怎么跑、多久跑、跑哪些 dataset”，主要看 `device_collection2_policy`
