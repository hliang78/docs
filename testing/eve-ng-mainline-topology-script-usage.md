# EVE Mainline Topology Script Usage

## Goal

Use a local CLI to safely rebuild or delete the current OneOps EVE mainline topology without relying on a model-driven agent.

## Commands

```bash
python3 scripts/eve_mainline_topology.py plan
python3 scripts/eve_mainline_topology.py preflight
python3 scripts/eve_mainline_topology.py apply
python3 scripts/eve_mainline_topology.py apply --confirm-destructive oneops-network-mainline-v1
python3 scripts/eve_mainline_bootstrap.py
python3 scripts/eve_mainline_topology.py destroy
```

## Environment variables

```bash
export EVE_HOST=192.168.100.20
export EVE_USER=admin
export EVE_PASS=eve
```

## Current behavior

1. `plan` reads the frozen YAML and prints the intended lab, node, and link counts.
2. `preflight` performs a read-only safety check and tells us whether an `apply` would be destructive.
3. `apply` only proceeds when `preflight` finds no non-destructive blockers, then safely deletes the same-name lab, recreates the frozen topology, and starts all nodes.
4. `eve_mainline_bootstrap.py` reuses the already-created lab and pushes the frozen device baseline:
   - `GW` gets `192.168.100.150/24` on `pnet0` and `172.32.2.254/24` on `Vlan1`
   - `ACC1/ACC2` get management IPs and isolate server business ports into local access VLANs
   - `R1-R4` get management IPs, six mesh /24 links, and `OSPF 3/3 Full`
   - `S1/S2/OBS` get static netplan addressing
5. `destroy` stops nodes, detaches interfaces, deletes networks, deletes nodes, and finally deletes the lab.

## Link semantics

在当前 EVE 版本里，“真正的点对点 link 画法”不是单独的 link 写对象，而是：

1. 底层仍然落成 `network type=bridge`
2. 该 network 只挂 2 个端点
3. 且 `visibility=0`

满足这三个条件后，`/api/labs/<lab>/topology` 会把它折叠成真正的 `node -> node` 连线，而不是 `node -> network`。

因此脚本现在区分两层语义：

1. Every non-`pnet0` network must map to exactly one expected point-to-point link
2. No extra node endpoint may be attached to the same network
3. Every P2P `bridge` must end in hidden mode `visibility=0`
4. `preflight` reports `exclusive_link_semantics: true` only when 1-2 成立
5. `preflight` reports `hidden_p2p_visual_mode: true` only when 3 成立

This means the script now distinguishes between:

1. a dedicated point-to-point hidden bridge-backed link
2. an incorrect visible bridge node on the canvas
3. an incorrect shared bridge drift

## Destructive apply gate

If `preflight` sees that the target lab already exists, CLI `apply` now blocks by default.

To continue intentionally, the operator must provide an exact destructive confirmation:

```bash
python3 scripts/eve_mainline_topology.py apply \
  --spec scripts/eve_mainline_topology.yaml \
  --confirm-destructive oneops-network-mainline-v1
```

This means:

1. No existing `oneops-` lab is deleted by accident
2. The lab name must be typed explicitly
3. `preflight` becomes the standard first step before any mainline rebuild

## Console conflict gate

`preflight` now also inspects other running labs returned by `GET /api/folders/` and compares their active console ports with the target mainline port range.

If another running lab is still occupying ports such as `32769-32777`, the script returns:

1. `checks.console_ports_exclusive: false`
2. `blockers: ["target-lab-exists", "conflicting-running-labs"]` or at least `["conflicting-running-labs"]`
3. detailed `current.console_port_conflicts`
4. `warnings` entries such as `console-port-conflict:32769:<lab>:<node>`

This protects us from a dangerous false-positive state where:

1. the current `.unl` structure looks correct
2. but Web console sessions are still landing on nodes from an older lab
3. because the older lab was never fully stopped and cleaned

## Important boundary

EVE API assigns runtime node IDs automatically during `POST /nodes`. The YAML `id` field in this script is treated as a logical device ID for OneOps planning, not as a guaranteed EVE runtime node ID.

In the current `192.168.100.20` environment, API-created networks should use `visibility: 1`. Using `visibility: 0` during `POST /networks` can make immediate network read-back fail even when the API returns `201 success`.

Running `preflight` against the current mainline lab on `2026-06-30` returned `blocked` because:

1. `oneops-network-mainline-v1` already exists
2. `oneops-gateway-switch-20260627-082039.unl` is still running
3. that older lab is occupying the same console ports `32769-32777`

In that state, the current mainline still reports:

1. `node_names_match_spec: true`
2. `network_names_match_spec: true`
3. `hidden_p2p_visual_mode: true`
4. `exclusive_link_semantics: true`

But `console_ports_exclusive` is `false`, so `apply` must not continue until the old lab is cleaned.

## Current non-goals

1. No automatic OneOps-side采集、监控、拓扑验收
2. No Linux `snmpd` offline package installation in the bootstrap step
3. No OBS `controller + agent` deployment
4. No automatic host-side orphan `tap/tmp` cleanup
