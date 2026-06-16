# Huawei CE168 SNMP Exploration Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to run this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Explore SNMP support on Huawei CE168 target `172.21.165.11` and turn the observed OIDs into a practical metric inventory for OneOPS SNMP strategy/dashboard work.

**Architecture:** Run read-only SNMP probes from broad, cheap checks to focused MIB walks. Store raw walk output and summarized CSV/Markdown notes under `docs/superpowers/testing/huawei-ce168-snmp-172-21-165-11/`, then map supported OIDs to metric groups such as `system_basic`, `interface_basic`, `hardware_health`, `optical_transceiver`, `l2_l3_resources`, and `config_compliance_inputs`.

**Tech Stack:** Net-SNMP CLI (`snmpget`, `snmpwalk`, `snmpbulkwalk`, `snmptranslate`), shell, Markdown/CSV outputs, existing OneOPS SNMP metric contract terminology.

---

## Safety Rules

- Use SNMP read-only operations only: `snmpget`, `snmpwalk`, `snmpbulkwalk`.
- Do not run `snmpset`.
- Do not commit or write the SNMP community string to this file or result files.
- Keep command timeout small at first, then expand only after basic reachability is confirmed.
- Prefer numeric OIDs in raw commands so exploration still works when local MIB files are incomplete.

## Target

- Device: Huawei CE168 family switch
- Management IP: `172.21.165.11`
- SNMP version: start with v2c
- Community: provide at runtime via `SNMP_COMMUNITY`

## Output Structure

- Raw output directory: `docs/superpowers/testing/huawei-ce168-snmp-172-21-165-11/raw/`
- Summary directory: `docs/superpowers/testing/huawei-ce168-snmp-172-21-165-11/summary/`
- Final metric inventory: `docs/superpowers/testing/huawei-ce168-snmp-172-21-165-11/summary/metric-inventory.md`

## Runtime Setup

- [ ] **Step 1: Create output directories**

Run:

```bash
mkdir -p docs/superpowers/testing/huawei-ce168-snmp-172-21-165-11/raw
mkdir -p docs/superpowers/testing/huawei-ce168-snmp-172-21-165-11/summary
```

Expected: both directories exist.

- [ ] **Step 2: Export runtime variables without persisting secrets**

Run in the active shell:

```bash
export SNMP_TARGET='172.21.165.11'
export SNMP_COMMUNITY='<set-from-user-provided-secret>'
export SNMP_OPTS="-v2c -c ${SNMP_COMMUNITY} -On -t 3 -r 1"
export SNMP_OUT='docs/superpowers/testing/huawei-ce168-snmp-172-21-165-11'
```

Expected: `echo "$SNMP_TARGET"` prints `172.21.165.11`. Do not print `SNMP_COMMUNITY`.

## Task 1: Tooling And Reachability

**Purpose:** Confirm local tooling and cheap SNMP reachability before any table walks.

- [ ] **Step 1: Check Net-SNMP tools**

Run:

```bash
command -v snmpget
command -v snmpwalk
command -v snmpbulkwalk
command -v snmptranslate
```

Expected: paths are printed for available tools. If `snmpbulkwalk` is missing, use `snmpwalk` for all table walks.

- [ ] **Step 2: Read basic system scalars**

Run:

```bash
snmpget $SNMP_OPTS "$SNMP_TARGET" \
  .1.3.6.1.2.1.1.1.0 \
  .1.3.6.1.2.1.1.2.0 \
  .1.3.6.1.2.1.1.3.0 \
  .1.3.6.1.2.1.1.5.0 \
  .1.3.6.1.2.1.1.6.0 \
  > "$SNMP_OUT/raw/01-system-scalars.txt"
```

Expected: output contains `sysDescr`, `sysObjectID`, `sysUpTime`, `sysName`, and `sysLocation` numeric OIDs.

- [ ] **Step 3: Record first conclusion**

Append to `summary/metric-inventory.md`:

```markdown
# Huawei CE168 SNMP Metric Inventory

## Target

- IP: 172.21.165.11
- SNMP: v2c read-only exploration

## Basic System

Observed system scalar support:

| Concept | OID | Supported | Notes |
|---|---|---:|---|
| sysDescr | .1.3.6.1.2.1.1.1.0 | yes/no | |
| sysObjectID | .1.3.6.1.2.1.1.2.0 | yes/no | |
| sysUpTime | .1.3.6.1.2.1.1.3.0 | yes/no | |
| sysName | .1.3.6.1.2.1.1.5.0 | yes/no | |
| sysLocation | .1.3.6.1.2.1.1.6.0 | yes/no | |
```

Expected: summary file exists and records basic SNMP availability.

## Task 2: Entity Inventory

**Purpose:** Build the index map needed to join Huawei private hardware state, fan, power, optical, and temperature values back to physical modules.

- [ ] **Step 1: Walk ENTITY-MIB physical inventory**

Run:

```bash
snmpbulkwalk $SNMP_OPTS "$SNMP_TARGET" .1.3.6.1.2.1.47.1.1.1.1 \
  > "$SNMP_OUT/raw/02-entity-physical-table.txt"
```

Expected: output contains entries for `entPhysicalDescr`, `entPhysicalClass`, `entPhysicalName`, and ideally serial/model fields.

- [ ] **Step 2: Record entity concepts**

Add a section to `summary/metric-inventory.md`:

```markdown
## Entity Inventory

Metric group candidate: `entity_inventory`

| Concept | Metric key | OID family | Supported | Notes |
|---|---|---|---:|---|
| Entity description | entity_descr | .1.3.6.1.2.1.47.1.1.1.1.2 | yes/no | |
| Entity class | entity_class | .1.3.6.1.2.1.47.1.1.1.1.5 | yes/no | |
| Entity name | entity_name | .1.3.6.1.2.1.47.1.1.1.1.7 | yes/no | |
| Entity serial number | entity_serial | .1.3.6.1.2.1.47.1.1.1.1.11 | yes/no | |
| Entity model | entity_model | .1.3.6.1.2.1.47.1.1.1.1.13 | yes/no | |
```

Expected: entity index is available for later joins.

## Task 3: Interface Tables

**Purpose:** Verify CE high-speed interface metrics and decide whether Huawei bootstrap must switch from `ifInOctets/ifOutOctets` to `ifHCInOctets/ifHCOutOctets`.

- [ ] **Step 1: Walk IF-MIB base table**

Run:

```bash
snmpbulkwalk $SNMP_OPTS "$SNMP_TARGET" .1.3.6.1.2.1.2.2.1 \
  > "$SNMP_OUT/raw/03-if-table.txt"
```

Expected: output contains `ifDescr`, `ifType`, `ifSpeed`, `ifAdminStatus`, `ifOperStatus`, `ifInOctets`, `ifOutOctets`, errors, and discards.

- [ ] **Step 2: Walk IF-MIB high-capacity table**

Run:

```bash
snmpbulkwalk $SNMP_OPTS "$SNMP_TARGET" .1.3.6.1.2.1.31.1.1.1 \
  > "$SNMP_OUT/raw/04-ifx-table.txt"
```

Expected: output contains `ifName`, `ifHCInOctets`, `ifHCOutOctets`, `ifHighSpeed`, and ideally high-capacity packet counters.

- [ ] **Step 3: Record interface concepts**

Add a section to `summary/metric-inventory.md`:

```markdown
## Interface Basic And Traffic

Metric group candidate: `interface_basic`

| Concept | Metric key | Preferred OID | Fallback OID | Supported | Notes |
|---|---|---|---|---:|---|
| Interface name | if_name | .1.3.6.1.2.1.31.1.1.1.1 | .1.3.6.1.2.1.2.2.1.2 | yes/no | |
| Interface alias | if_alias | .1.3.6.1.2.1.31.1.1.1.18 | | yes/no | |
| Admin status | if_admin_status | .1.3.6.1.2.1.2.2.1.7 | | yes/no | |
| Oper status | if_oper_status | .1.3.6.1.2.1.2.2.1.8 | | yes/no | |
| In traffic | if_in_rate | .1.3.6.1.2.1.31.1.1.1.6 | .1.3.6.1.2.1.2.2.1.10 | yes/no | prefer HC |
| Out traffic | if_out_rate | .1.3.6.1.2.1.31.1.1.1.10 | .1.3.6.1.2.1.2.2.1.16 | yes/no | prefer HC |
| Interface speed | if_speed_bps | .1.3.6.1.2.1.31.1.1.1.15 | .1.3.6.1.2.1.2.2.1.5 | yes/no | `ifHighSpeed` is Mbps |
```

Expected: interface metric support is clear enough to update the Huawei strategy later.

## Task 4: Interface Quality And Packet Mix

**Purpose:** Cover dashboard rows for errors, CRC/FCS, discards, packets-per-second, and traffic mix.

- [ ] **Step 1: Walk EtherLike-MIB statistics**

Run:

```bash
snmpbulkwalk $SNMP_OPTS "$SNMP_TARGET" .1.3.6.1.2.1.10.7.2.1 \
  > "$SNMP_OUT/raw/05-etherlike-dot3-stats.txt"
```

Expected: if supported, output includes FCS/CRC and collision-style Ethernet counters.

- [ ] **Step 2: Record interface quality concepts**

Add a section to `summary/metric-inventory.md`:

```markdown
## Interface Quality And Packet Mix

Metric group candidate: `interface_quality`

| Concept | Metric key | OID | Supported | Notes |
|---|---|---|---:|---|
| In errors | if_in_error_rate | .1.3.6.1.2.1.2.2.1.14 | yes/no | |
| Out errors | if_out_error_rate | .1.3.6.1.2.1.2.2.1.20 | yes/no | |
| In discards | if_in_discard_rate | .1.3.6.1.2.1.2.2.1.13 | yes/no | |
| Out discards | if_out_discard_rate | .1.3.6.1.2.1.2.2.1.19 | yes/no | |
| FCS/CRC errors | if_crc_error_rate | .1.3.6.1.2.1.10.7.2.1.3 | yes/no | |
| In unicast packets | if_in_unicast_pps | .1.3.6.1.2.1.31.1.1.1.7 | yes/no | |
| In multicast packets | if_in_multicast_pps | .1.3.6.1.2.1.31.1.1.1.8 | yes/no | |
| In broadcast packets | if_in_broadcast_pps | .1.3.6.1.2.1.31.1.1.1.9 | yes/no | |
| Out unicast packets | if_out_unicast_pps | .1.3.6.1.2.1.31.1.1.1.11 | yes/no | |
| Out multicast packets | if_out_multicast_pps | .1.3.6.1.2.1.31.1.1.1.12 | yes/no | |
| Out broadcast packets | if_out_broadcast_pps | .1.3.6.1.2.1.31.1.1.1.13 | yes/no | |
```

Expected: interface quality and traffic mix candidates are documented.

## Task 5: Huawei Entity Health

**Purpose:** Verify Huawei private MIB support for CPU, memory, temperature, voltage, board power, module states, fan states, and PSU states.

- [ ] **Step 1: Walk Huawei entity state table**

Run:

```bash
snmpbulkwalk $SNMP_OPTS "$SNMP_TARGET" .1.3.6.1.4.1.2011.5.25.31.1.1.1.1 \
  > "$SNMP_OUT/raw/06-huawei-entity-state-table.txt"
```

Expected: output includes at least some of CPU, memory, status, temperature, voltage, optical power, or board power columns.

- [ ] **Step 2: Walk Huawei fan table**

Run:

```bash
snmpbulkwalk $SNMP_OPTS "$SNMP_TARGET" .1.3.6.1.4.1.2011.5.25.31.1.1.10.1 \
  > "$SNMP_OUT/raw/07-huawei-fan-table.txt"
```

Expected: output includes fan slot, speed, presence, state, and description fields if supported.

- [ ] **Step 3: Walk Huawei power table**

Run:

```bash
snmpbulkwalk $SNMP_OPTS "$SNMP_TARGET" .1.3.6.1.4.1.2011.5.25.31.1.1.18.1 \
  > "$SNMP_OUT/raw/08-huawei-power-table.txt"
```

Expected: output includes power slot, present, state, current, voltage, description, and power fields if supported.

- [ ] **Step 4: Record hardware health concepts**

Add a section to `summary/metric-inventory.md`:

```markdown
## Hardware Health

Metric group candidates: `hardware_health`, `thermal_sensors`, `fan_status`, `power_supply`, `optical_transceiver`

| Concept | Metric key | OID | Supported | Notes |
|---|---|---|---:|---|
| Entity operational status | entity_oper_status | .1.3.6.1.4.1.2011.5.25.31.1.1.1.1.2 | yes/no | |
| Entity alarm light/state | entity_alarm_state | .1.3.6.1.4.1.2011.5.25.31.1.1.1.1.4 | yes/no | |
| Entity CPU usage | cpu_usage_direct | .1.3.6.1.4.1.2011.5.25.31.1.1.1.1.5 | yes/no | maps to `system_basic` |
| Entity memory usage | memory_usage_direct | .1.3.6.1.4.1.2011.5.25.31.1.1.1.1.7 | yes/no | maps to `system_basic` |
| Entity temperature | sensor_temperature_celsius | .1.3.6.1.4.1.2011.5.25.31.1.1.1.1.11 | yes/no | |
| Entity voltage | entity_voltage | .1.3.6.1.4.1.2011.5.25.31.1.1.1.1.13 | yes/no | |
| Optical power Rx | optical_rx_power_raw | .1.3.6.1.4.1.2011.5.25.31.1.1.1.1.22 | yes/no | unit conversion must be verified |
| Board power | board_power_watts | .1.3.6.1.4.1.2011.5.25.31.1.1.1.1.24 | yes/no | |
| Fan speed | fan_speed | .1.3.6.1.4.1.2011.5.25.31.1.1.10.1.5 | yes/no | |
| Fan present | fan_present | .1.3.6.1.4.1.2011.5.25.31.1.1.10.1.6 | yes/no | |
| Fan state | fan_state | .1.3.6.1.4.1.2011.5.25.31.1.1.10.1.7 | yes/no | |
| PSU present | power_present | .1.3.6.1.4.1.2011.5.25.31.1.1.18.1.5 | yes/no | |
| PSU state | power_state | .1.3.6.1.4.1.2011.5.25.31.1.1.18.1.6 | yes/no | |
| PSU current | power_current | .1.3.6.1.4.1.2011.5.25.31.1.1.18.1.7 | yes/no | |
| PSU voltage | power_voltage | .1.3.6.1.4.1.2011.5.25.31.1.1.18.1.8 | yes/no | |
| PSU power | power_watts | .1.3.6.1.4.1.2011.5.25.31.1.1.18.1.10 | yes/no | |
```

Expected: hardware health candidates are separated from generic CPU/memory and can become dedicated metric groups.

## Task 6: L2/L3 Resource Tables

**Purpose:** Explore whether SNMP can populate the dashboard's Routing & Layer 2 block.

- [ ] **Step 1: Walk LLDP local and remote tables**

Run:

```bash
snmpbulkwalk $SNMP_OPTS "$SNMP_TARGET" .1.0.8802.1.1.2.1.3 \
  > "$SNMP_OUT/raw/09-lldp-local.txt"
snmpbulkwalk $SNMP_OPTS "$SNMP_TARGET" .1.0.8802.1.1.2.1.4 \
  > "$SNMP_OUT/raw/10-lldp-remote.txt"
```

Expected: output contains LLDP local port IDs and remote neighbor values if LLDP SNMP is exposed.

- [ ] **Step 2: Walk bridge and VLAN tables**

Run:

```bash
snmpbulkwalk $SNMP_OPTS "$SNMP_TARGET" .1.3.6.1.2.1.17 \
  > "$SNMP_OUT/raw/11-bridge-mib.txt"
snmpbulkwalk $SNMP_OPTS "$SNMP_TARGET" .1.3.6.1.2.1.17.7 \
  > "$SNMP_OUT/raw/12-q-bridge-mib.txt"
```

Expected: output may include MAC forwarding, VLAN, and STP-related data. Large output is normal on core switches.

- [ ] **Step 3: Walk IP route and neighbor families**

Run:

```bash
snmpbulkwalk $SNMP_OPTS "$SNMP_TARGET" .1.3.6.1.2.1.4.22 \
  > "$SNMP_OUT/raw/13-ip-net-to-media.txt"
snmpbulkwalk $SNMP_OPTS "$SNMP_TARGET" .1.3.6.1.2.1.4.24 \
  > "$SNMP_OUT/raw/14-ip-forwarding-table.txt"
```

Expected: output may include ARP/neighbor and route entries if exposed through standard IP-MIB.

- [ ] **Step 4: Walk OSPF and BGP standard families**

Run:

```bash
snmpbulkwalk $SNMP_OPTS "$SNMP_TARGET" .1.3.6.1.2.1.14 \
  > "$SNMP_OUT/raw/15-ospf-mib.txt"
snmpbulkwalk $SNMP_OPTS "$SNMP_TARGET" .1.3.6.1.2.1.15 \
  > "$SNMP_OUT/raw/16-bgp4-mib.txt"
```

Expected: output contains OSPF/BGP data only if those MIB views are enabled and protocols are active.

- [ ] **Step 5: Record L2/L3 resource concepts**

Add a section to `summary/metric-inventory.md`:

```markdown
## L2/L3 Resources

Metric group candidate: `l2_l3_resources`

| Concept | Metric key | OID family | Supported | Notes |
|---|---|---|---:|---|
| LLDP neighbor count/detail | lldp_neighbor | .1.0.8802.1.1.2.1.4 | yes/no | |
| MAC address entries | mac_entries | .1.3.6.1.2.1.17 / .1.3.6.1.2.1.17.7 | yes/no | |
| VLAN inventory | vlan_count | .1.3.6.1.2.1.17.7 | yes/no | |
| STP state | stp_state | .1.3.6.1.2.1.17.2 | yes/no | |
| ARP entries | arp_entries | .1.3.6.1.2.1.4.22 | yes/no | |
| IPv4 route count | ipv4_route_count | .1.3.6.1.2.1.4.24 | yes/no | |
| OSPF neighbor state | ospf_neighbor_state | .1.3.6.1.2.1.14 | yes/no | |
| BGP peer state | bgp_peer_state | .1.3.6.1.2.1.15 | yes/no | |
```

Expected: resource block support is documented even when some MIBs are unavailable.

## Task 7: Packet Buffer And QoS

**Purpose:** Explore whether the dashboard's packet buffer panel can be SNMP-driven on this CE168.

- [ ] **Step 1: Walk Huawei memory MIB**

Run:

```bash
snmpbulkwalk $SNMP_OPTS "$SNMP_TARGET" .1.3.6.1.4.1.2011.6.2 \
  > "$SNMP_OUT/raw/17-huawei-memory-mib.txt"
```

Expected: output may include memory or buffer utilization objects depending on CE software support.

- [ ] **Step 2: Walk Huawei XQoS MIB branch**

Run:

```bash
snmpbulkwalk $SNMP_OPTS "$SNMP_TARGET" .1.3.6.1.4.1.2011.5.25.32 \
  > "$SNMP_OUT/raw/18-huawei-xqos-mib.txt"
```

Expected: output may include interface buffer usage or QoS resource objects. If empty, packet buffer may require CLI or trap/event integration instead of polling.

- [ ] **Step 3: Record packet buffer decision**

Add a section to `summary/metric-inventory.md`:

```markdown
## Packet Buffer And QoS

Metric group candidate: `packet_buffer`

| Concept | Metric key | OID family | Supported | Notes |
|---|---|---|---:|---|
| Packet buffer usage | packet_buffer_usage | Huawei memory/XQoS branches | yes/no | |
| Interface buffer usage | if_buffer_usage | Huawei XQoS branch | yes/no | |
| QoS resource overrun | qos_resource_overrun | Huawei XQoS traps/counters | yes/no | |
```

Expected: packet buffer is classified as SNMP-supported, trap/event-supported, or unsupported for this device.

## Task 8: Contract Mapping Recommendation

**Purpose:** Turn raw observations into actionable OneOPS metric groups.

- [ ] **Step 1: Draft group mapping**

Add a final section to `summary/metric-inventory.md`:

```markdown
## Recommended OneOPS Metric Groups

| Group key | Entity | Data shape | Priority | Source |
|---|---|---|---:|---|
| system_basic | device | timeseries | P0 | SNMP scalar/Huawei entity state |
| interface_basic | interface | table_timeseries | P0 | IF-MIB + IF-MIB::ifXTable |
| interface_quality | interface | table_timeseries | P0 | IF-MIB + EtherLike-MIB |
| hardware_health | module | table_timeseries | P1 | ENTITY-MIB + HUAWEI-ENTITY-EXTENT-MIB |
| fan_status | module | table | P1 | HUAWEI-ENTITY-EXTENT-MIB fan table |
| power_supply | module | table | P1 | HUAWEI-ENTITY-EXTENT-MIB power table |
| optical_transceiver | interface | table_timeseries | P1 | HUAWEI-ENTITY-EXTENT-MIB optical fields |
| l2_l3_resources | device | table | P2 | LLDP/BRIDGE/Q-BRIDGE/IP/OSPF/BGP MIBs |
| packet_buffer | interface | timeseries | P2 | Huawei memory/XQoS if supported |
```

Expected: the summary is ready to drive updates to the Huawei SNMP strategy bootstrap and metric contract resolver.

- [ ] **Step 2: Identify bootstrap changes**

Record these decisions in the summary:

```markdown
## Bootstrap Change Candidates

- Replace 32-bit interface octet counters with `ifHCInOctets` and `ifHCOutOctets` when `ifXTable` is supported.
- Add `ifHighSpeed` for high-speed utilization calculation.
- Keep `ifSpeed` as fallback only.
- Add `ifName` and `ifAlias` to improve panel labels.
- Add Huawei entity table CPU/memory/temperature fields after verifying which entity rows represent the chassis/control boards.
- Add fan and power tables as separate metric groups, not as generic system metrics.
- Treat L2/L3 resource counts as P2 because large tables may be expensive on core switches.
```

Expected: follow-up implementation can modify `quick_env/docker-entrypoint-initdb.d/zzzzzzzzzz-huawei-snmp-network-strategy-bootstrap.sql` with observed, device-backed evidence.

