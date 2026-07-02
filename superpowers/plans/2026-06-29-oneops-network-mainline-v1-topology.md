# OneOps Network Mainline V1 Topology Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 EVE-NG 主机上生成一份新的 `oneops-network-mainline-v1.unl`，把 `GW + ACC1 + ACC2 + R1-R4 + S1 + S2 + OBS` 的第一版主线拓扑骨架真正落地。

**Architecture:** 直接在 EVE 主机写入一份新的 `.unl` 实验文件，用独立 `network` 节点承接每条点对点或接入关系，再通过节点接口 `network_id` 固定端口真值。创建完成后不立即灌初始化配置，而是先回读 XML 内容确认节点、网络和链路都和冻结表一致。

**Tech Stack:** EVE-NG `.unl` XML、SSH、宿主机文件回读

---

### Task 1: Write the new lab file

**Files:**
- Create: `/opt/unetlab/labs/oneops-network-mainline-v1.unl` on `192.168.100.20`
- Reference: `/Users/huangliang/project/OneOPS-ALL/docs/testing/phase1-network-mainline-addressing-and-port-map.md`

- [ ] **Step 1: Build a fresh lab XML skeleton**

Create a new lab named `oneops-network-mainline-v1` with:

```xml
<lab name="oneops-network-mainline-v1" version="1" scripttimeout="300" lock="0" author="Codex">
  <description>OneOps network mainline v1 topology skeleton</description>
  <topology>
    <nodes></nodes>
    <networks></networks>
  </topology>
</lab>
```

- [ ] **Step 2: Add all nodes with the approved image mapping**

Write node entries for:

```text
GW, ACC1, ACC2
R1, R2, R3, R4
S1, S2, OBS
```

Use these image families:

```text
GW/ACC1/ACC2 -> iol
R1-R4 -> huaweiar1k-5.170-V300R022C00SPC100-Auto-update-esn
S1/S2/OBS -> linux-ubuntu-server-20.04
```

- [ ] **Step 3: Add one network object per frozen link**

Create network entries for:

```text
pnet0 uplink
9 management/access links
6 route-mesh links
```

Expected total:

```text
1 pnet + 21 bridge networks = 22 networks
```

- [ ] **Step 4: Bind each node interface to the intended network_id**

Apply the exact frozen pairings from the design doc and address/port map.

- [ ] **Step 5: Fix permissions**

Run:

```bash
sshpass -p eve ssh -o StrictHostKeyChecking=no root@192.168.100.20 \
  'chown www-data:www-data /opt/unetlab/labs/oneops-network-mainline-v1.unl && /opt/unetlab/wrappers/unl_wrapper -a fixpermissions'
```

Expected: command exits `0`

### Task 2: Verify node and link truth

**Files:**
- Read: `/opt/unetlab/labs/oneops-network-mainline-v1.unl` on `192.168.100.20`

- [ ] **Step 1: Read back the lab file**

Run:

```bash
sshpass -p eve ssh -o StrictHostKeyChecking=no root@192.168.100.20 \
  'sed -n "1,260p" /opt/unetlab/labs/oneops-network-mainline-v1.unl'
```

Expected: XML contains all 10 nodes and all expected networks

- [ ] **Step 2: Count nodes and networks**

Run:

```bash
sshpass -p eve ssh -o StrictHostKeyChecking=no root@192.168.100.20 \
  "python3 - <<'PY'
import xml.etree.ElementTree as ET
root = ET.parse('/opt/unetlab/labs/oneops-network-mainline-v1.unl').getroot()
nodes = root.findall('./topology/nodes/node')
networks = root.findall('./topology/networks/network')
print('nodes', len(nodes))
print('networks', len(networks))
PY"
```

Expected:

```text
nodes 10
networks 22
```

- [ ] **Step 3: Verify key interface bindings**

Run a targeted readback for:

```text
GW IF1-IF10
ACC1 IF1-IF4
ACC2 IF1-IF4
R1-R4 IF1-IF4 + IF-last
S1 IF1/IF2
S2 IF1/IF2
OBS IF1
```

Expected: each pairing matches the frozen link map

### Task 3: Summarize the created topology

**Files:**
- Modify: none required

- [ ] **Step 1: Report the created lab name and device map**

Include:

```text
lab file path
node count
network count
which image each role used
```

- [ ] **Step 2: Report immediate next constraints**

Include:

```text
topology only, no init yet
next step is device init + management validation
```
