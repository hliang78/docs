# OneOps EVE Mainline Topology Script Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a local Python CLI that can safely destroy and rebuild the current `oneops-network-mainline-v1` EVE topology through the EVE API, then start nodes and print stable summaries.

**Architecture:** Keep the script small and explicit: a YAML topology contract, a focused library for spec parsing plus EVE API operations, and a thin CLI entrypoint for `plan`, `apply`, and `destroy`. Use read-back validation after every EVE write so the tool stops early on inconsistent state instead of masking partial failures.

**Tech Stack:** Python 3, stdlib `argparse`/`dataclasses`/`json`/`pathlib`/`typing`, `requests`, `PyYAML`, `unittest`, EVE-NG HTTP API

---

## File structure

- Create: `scripts/eve_mainline_topology.py`
- Create: `scripts/eve_mainline_topology_lib.py`
- Create: `scripts/eve_mainline_topology.yaml`
- Create: `tests/test_eve_mainline_topology.py`
- Create: `docs/testing/eve-ng-mainline-topology-script-usage.md`

Responsibilities:

- `scripts/eve_mainline_topology.py`
  CLI wrapper only. Parse command-line options, load environment defaults, call library entrypoints, print final JSON.
- `scripts/eve_mainline_topology_lib.py`
  YAML contract loading, safety guard, plan rendering, EVE API client, `apply`/`destroy` orchestration, and read-back validation helpers.
- `scripts/eve_mainline_topology.yaml`
  Frozen current mainline truth: lab metadata, node definitions, link definitions, and startup order.
- `tests/test_eve_mainline_topology.py`
  Contract tests and flow tests using fake in-memory EVE client behavior so implementation can be verified without the live EVE host.
- `docs/testing/eve-ng-mainline-topology-script-usage.md`
  Minimal usage doc for teammates to run the tool without reading code.

### Task 1: Freeze the YAML contract and spec loader

**Files:**
- Create: `scripts/eve_mainline_topology.yaml`
- Create: `scripts/eve_mainline_topology_lib.py`
- Create: `tests/test_eve_mainline_topology.py`

- [ ] **Step 1: Write the failing contract tests**

```python
import tempfile
import textwrap
import unittest
from pathlib import Path

from scripts.eve_mainline_topology_lib import (
    TopologySpecError,
    load_topology_spec,
    require_safe_lab_name,
)


class TopologySpecContractTest(unittest.TestCase):
    def test_load_topology_spec_reads_frozen_mainline_contract(self) -> None:
        spec = load_topology_spec(Path("scripts/eve_mainline_topology.yaml"))
        self.assertEqual(spec.lab.name, "oneops-network-mainline-v1")
        self.assertEqual(spec.lab.path, "/opt/unetlab/labs/oneops-network-mainline-v1.unl")
        self.assertEqual(spec.node_map["GW"].id, 101)
        self.assertEqual(spec.node_map["OBS"].cpu, 8)
        self.assertEqual(spec.node_map["OBS"].ram, 16384)
        self.assertEqual(len(spec.links), 22)
        self.assertEqual(spec.links[0].id, "L01")

    def test_load_topology_spec_rejects_duplicate_node_names(self) -> None:
        payload = textwrap.dedent(
            """
            lab:
              name: oneops-demo
              path: /opt/unetlab/labs/oneops-demo.unl
              description: duplicate name case
            nodes:
              - {name: GW, id: 101, template: iol, type: iol, ethernet: 5, cpu: 1, ram: 1024, left: 10, top: 10}
              - {name: GW, id: 102, template: iol, type: iol, ethernet: 1, cpu: 1, ram: 1024, left: 20, top: 20}
            links: []
            """
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "duplicate.yaml"
            path.write_text(payload, encoding="utf-8")
            with self.assertRaises(TopologySpecError):
                load_topology_spec(path)

    def test_require_safe_lab_name_blocks_non_oneops_names_without_force(self) -> None:
        with self.assertRaises(TopologySpecError):
            require_safe_lab_name("prod-lab", force=False)
        require_safe_lab_name("oneops-safe-lab", force=False)
        require_safe_lab_name("prod-lab", force=True)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python3 -m unittest discover -s tests -p 'test_eve_mainline_topology.py' -v
```

Expected:

```text
ImportError: cannot import name 'TopologySpecError'
```

- [ ] **Step 3: Write the frozen YAML contract**

```yaml
lab:
  path: /opt/unetlab/labs/oneops-network-mainline-v1.unl
  name: oneops-network-mainline-v1
  description: OneOps phase1 mainline topology

nodes:
  - name: GW
    id: 101
    template: iol
    type: iol
    ethernet: 5
    cpu: 1
    ram: 1024
    left: 120
    top: 80
  - name: ACC1
    id: 102
    template: iol
    type: iol
    ethernet: 1
    cpu: 1
    ram: 1024
    left: 120
    top: 220
  - name: ACC2
    id: 103
    template: iol
    type: iol
    ethernet: 1
    cpu: 1
    ram: 1024
    left: 120
    top: 360
  - name: R1
    id: 104
    template: huaweiar1k
    type: qemu
    image: huaweiar1k-5.170-V300R022C00SPC100-Auto-update-esn
    ethernet: 5
    cpu: 1
    ram: 2048
    left: 360
    top: 200
  - name: R2
    id: 105
    template: huaweiar1k
    type: qemu
    image: huaweiar1k-5.170-V300R022C00SPC100-Auto-update-esn
    ethernet: 5
    cpu: 1
    ram: 2048
    left: 360
    top: 320
  - name: R3
    id: 106
    template: huaweiar1k
    type: qemu
    image: huaweiar1k-5.170-V300R022C00SPC100-Auto-update-esn
    ethernet: 5
    cpu: 1
    ram: 2048
    left: 540
    top: 200
  - name: R4
    id: 107
    template: huaweiar1k
    type: qemu
    image: huaweiar1k-5.170-V300R022C00SPC100-Auto-update-esn
    ethernet: 5
    cpu: 1
    ram: 2048
    left: 540
    top: 320
  - name: S1
    id: 108
    template: linux
    type: qemu
    image: linux-ubuntu-server-20.04
    ethernet: 2
    cpu: 1
    ram: 2048
    left: 300
    top: 500
  - name: S2
    id: 109
    template: linux
    type: qemu
    image: linux-ubuntu-server-20.04
    ethernet: 2
    cpu: 1
    ram: 2048
    left: 600
    top: 500
  - name: OBS
    id: 110
    template: linux
    type: qemu
    image: linux-ubuntu-server-20.04
    ethernet: 1
    cpu: 8
    ram: 16384
    left: 780
    top: 80

links:
  - id: L01
    type: pnet0
    name: GW-pnet0
    endpoints:
      - node: GW
        interface: 0
      - pnet: 0
  - id: L02
    type: bridge
    name: GW-ACC1-MGT
    endpoints:
      - node: GW
        interface: 1
      - node: ACC1
        interface: 0
  - id: L03
    type: bridge
    name: GW-ACC2-MGT
    endpoints:
      - node: GW
        interface: 2
      - node: ACC2
        interface: 0
  - id: L04
    type: bridge
    name: GW-R1-MGT
    endpoints:
      - node: GW
        interface: 3
      - node: R1
        interface: 4
  - id: L05
    type: bridge
    name: GW-R2-MGT
    endpoints:
      - node: GW
        interface: 4
      - node: R2
        interface: 4
  - id: L06
    type: bridge
    name: GW-R3-MGT
    endpoints:
      - node: GW
        interface: 5
      - node: R3
        interface: 4
  - id: L07
    type: bridge
    name: GW-R4-MGT
    endpoints:
      - node: GW
        interface: 6
      - node: R4
        interface: 4
  - id: L08
    type: bridge
    name: GW-S1-MGT
    endpoints:
      - node: GW
        interface: 7
      - node: S1
        interface: 1
  - id: L09
    type: bridge
    name: GW-S2-MGT
    endpoints:
      - node: GW
        interface: 8
      - node: S2
        interface: 1
  - id: L10
    type: bridge
    name: GW-OBS-MGT
    endpoints:
      - node: GW
        interface: 9
      - node: OBS
        interface: 0
  - id: L11
    type: bridge
    name: ACC1-S1-ACC
    endpoints:
      - node: ACC1
        interface: 1
      - node: S1
        interface: 0
  - id: L12
    type: bridge
    name: ACC1-R1-ACC
    endpoints:
      - node: ACC1
        interface: 2
      - node: R1
        interface: 0
  - id: L13
    type: bridge
    name: ACC1-R2-ACC
    endpoints:
      - node: ACC1
        interface: 3
      - node: R2
        interface: 0
  - id: L14
    type: bridge
    name: ACC2-S2-ACC
    endpoints:
      - node: ACC2
        interface: 1
      - node: S2
        interface: 0
  - id: L15
    type: bridge
    name: ACC2-R3-ACC
    endpoints:
      - node: ACC2
        interface: 2
      - node: R3
        interface: 0
  - id: L16
    type: bridge
    name: ACC2-R4-ACC
    endpoints:
      - node: ACC2
        interface: 3
      - node: R4
        interface: 0
  - id: L17
    type: bridge
    name: R1-R2-MESH
    endpoints:
      - node: R1
        interface: 1
      - node: R2
        interface: 1
  - id: L18
    type: bridge
    name: R1-R3-MESH
    endpoints:
      - node: R1
        interface: 2
      - node: R3
        interface: 1
  - id: L19
    type: bridge
    name: R1-R4-MESH
    endpoints:
      - node: R1
        interface: 3
      - node: R4
        interface: 1
  - id: L20
    type: bridge
    name: R2-R3-MESH
    endpoints:
      - node: R2
        interface: 2
      - node: R3
        interface: 2
  - id: L21
    type: bridge
    name: R2-R4-MESH
    endpoints:
      - node: R2
        interface: 3
      - node: R4
        interface: 2
  - id: L22
    type: bridge
    name: R3-R4-MESH
    endpoints:
      - node: R3
        interface: 3
      - node: R4
        interface: 3
```

- [ ] **Step 4: Write the minimal spec loader implementation**

```python
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import yaml


class TopologySpecError(ValueError):
    pass


@dataclass(frozen=True)
class LabSpec:
    path: str
    name: str
    description: str


@dataclass(frozen=True)
class NodeSpec:
    name: str
    id: int
    template: str
    type: str
    ethernet: int
    cpu: int
    ram: int
    left: int
    top: int
    image: Optional[str] = None


@dataclass(frozen=True)
class LinkEndpointSpec:
    node: Optional[str] = None
    interface: Optional[int] = None
    pnet: Optional[int] = None


@dataclass(frozen=True)
class LinkSpec:
    id: str
    type: str
    name: str
    endpoints: list[LinkEndpointSpec]


@dataclass(frozen=True)
class TopologySpec:
    lab: LabSpec
    nodes: list[NodeSpec]
    links: list[LinkSpec]
    node_map: dict[str, NodeSpec]


def require_safe_lab_name(name: str, force: bool = False) -> None:
    if force:
        return
    if not name.startswith("oneops-"):
        raise TopologySpecError(f"unsafe lab name: {name}")


def load_topology_spec(path: Path) -> TopologySpec:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TopologySpecError("top-level YAML must be a mapping")

    lab_raw = payload.get("lab") or {}
    nodes_raw = payload.get("nodes") or []
    links_raw = payload.get("links") or []

    lab = LabSpec(
        path=str(lab_raw["path"]),
        name=str(lab_raw["name"]),
        description=str(lab_raw["description"]),
    )

    nodes: list[NodeSpec] = []
    seen_names: set[str] = set()
    seen_ids: set[int] = set()
    for raw in nodes_raw:
        node = NodeSpec(
            name=str(raw["name"]),
            id=int(raw["id"]),
            template=str(raw["template"]),
            type=str(raw["type"]),
            ethernet=int(raw["ethernet"]),
            cpu=int(raw["cpu"]),
            ram=int(raw["ram"]),
            left=int(raw["left"]),
            top=int(raw["top"]),
            image=raw.get("image"),
        )
        if node.name in seen_names:
            raise TopologySpecError(f"duplicate node name: {node.name}")
        if node.id in seen_ids:
            raise TopologySpecError(f"duplicate node id: {node.id}")
        seen_names.add(node.name)
        seen_ids.add(node.id)
        nodes.append(node)

    node_map = {node.name: node for node in nodes}
    links: list[LinkSpec] = []
    for raw in links_raw:
        endpoints = [LinkEndpointSpec(**endpoint) for endpoint in raw["endpoints"]]
        if len(endpoints) != 2:
            raise TopologySpecError(f"link {raw['id']} must have exactly two endpoints")
        links.append(
            LinkSpec(
                id=str(raw["id"]),
                type=str(raw["type"]),
                name=str(raw["name"]),
                endpoints=endpoints,
            )
        )

    return TopologySpec(lab=lab, nodes=nodes, links=links, node_map=node_map)
```

- [ ] **Step 5: Run tests to verify they pass**

Run:

```bash
python3 -m unittest discover -s tests -p 'test_eve_mainline_topology.py' -v
```

Expected:

```text
OK
```

- [ ] **Step 6: Commit**

```bash
git add scripts/eve_mainline_topology.yaml scripts/eve_mainline_topology_lib.py tests/test_eve_mainline_topology.py
git commit -m "feat: add EVE mainline topology spec contract"
```

### Task 2: Implement `plan` output and CLI entrypoint

**Files:**
- Create: `scripts/eve_mainline_topology.py`
- Modify: `scripts/eve_mainline_topology_lib.py`
- Modify: `tests/test_eve_mainline_topology.py`

- [ ] **Step 1: Write the failing CLI and summary tests**

```python
import io
import json
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from scripts.eve_mainline_topology import main
from scripts.eve_mainline_topology_lib import load_topology_spec, render_plan_summary


class TopologyPlanOutputTest(unittest.TestCase):
    def test_render_plan_summary_includes_counts_and_lab_name(self) -> None:
        spec = load_topology_spec(Path("scripts/eve_mainline_topology.yaml"))
        summary = render_plan_summary(spec)
        self.assertEqual(summary["lab"]["name"], "oneops-network-mainline-v1")
        self.assertEqual(summary["counts"]["nodes"], 10)
        self.assertEqual(summary["counts"]["links"], 22)
        self.assertEqual(summary["counts"]["networks"], 22)

    def test_cli_plan_prints_json_summary(self) -> None:
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            exit_code = main(["plan", "--spec", "scripts/eve_mainline_topology.yaml"])
        self.assertEqual(exit_code, 0)
        payload = json.loads(buffer.getvalue().splitlines()[-1])
        self.assertEqual(payload["status"], "planned")
        self.assertEqual(payload["lab"], "oneops-network-mainline-v1")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python3 -m unittest discover -s tests -p 'test_eve_mainline_topology.py' -v
```

Expected:

```text
ImportError: cannot import name 'main'
```

- [ ] **Step 3: Implement the plan summary helper**

```python
def render_plan_summary(spec: TopologySpec) -> dict:
    return {
        "status": "planned",
        "lab": {
            "name": spec.lab.name,
            "path": spec.lab.path,
            "description": spec.lab.description,
        },
        "counts": {
            "nodes": len(spec.nodes),
            "links": len(spec.links),
            "networks": len(spec.links),
        },
        "nodes": [
            {
                "name": node.name,
                "id": node.id,
                "template": node.template,
                "ethernet": node.ethernet,
                "cpu": node.cpu,
                "ram": node.ram,
            }
            for node in spec.nodes
        ],
        "links": [
            {
                "id": link.id,
                "type": link.type,
                "name": link.name,
                "endpoints": [
                    {
                        "node": endpoint.node,
                        "interface": endpoint.interface,
                        "pnet": endpoint.pnet,
                    }
                    for endpoint in link.endpoints
                ],
            }
            for link in spec.links
        ],
    }
```

- [ ] **Step 4: Implement the CLI entrypoint**

```python
#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from eve_mainline_topology_lib import load_topology_spec, render_plan_summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage the OneOps EVE mainline topology.")
    parser.add_argument("command", choices=["plan", "apply", "destroy"])
    parser.add_argument("--spec", default="scripts/eve_mainline_topology.yaml")
    parser.add_argument("--force", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    spec = load_topology_spec(Path(args.spec))

    if args.command == "plan":
        payload = render_plan_summary(spec)
        print(f"LAB planned: {spec.lab.name}")
        print(f"NODES planned: {len(spec.nodes)}")
        print(f"LINKS planned: {len(spec.links)}")
        print(json.dumps(payload, ensure_ascii=False))
        return 0

    raise NotImplementedError(f"command not implemented yet: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 5: Run tests to verify they pass**

Run:

```bash
python3 -m unittest discover -s tests -p 'test_eve_mainline_topology.py' -v
```

Expected:

```text
OK
```

- [ ] **Step 6: Commit**

```bash
git add scripts/eve_mainline_topology.py scripts/eve_mainline_topology_lib.py tests/test_eve_mainline_topology.py
git commit -m "feat: add EVE mainline topology plan command"
```

### Task 3: Implement `apply` with EVE API client and read-back validation

**Files:**
- Modify: `scripts/eve_mainline_topology.py`
- Modify: `scripts/eve_mainline_topology_lib.py`
- Modify: `tests/test_eve_mainline_topology.py`

- [ ] **Step 1: Write the failing `apply` flow tests**

```python
import unittest

from scripts.eve_mainline_topology_lib import (
    FakeEveClient,
    apply_topology,
    load_topology_spec,
)


class TopologyApplyFlowTest(unittest.TestCase):
    def test_apply_rebuilds_lab_and_starts_all_nodes(self) -> None:
        spec = load_topology_spec(Path("scripts/eve_mainline_topology.yaml"))
        client = FakeEveClient(existing_lab=True)
        result = apply_topology(client, spec, force=False)
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["lab"], "oneops-network-mainline-v1")
        self.assertIn("GW", result["nodes"])
        self.assertEqual(result["nodes"]["GW"]["id"], 101)
        self.assertEqual(client.events[0], "destroy:oneops-network-mainline-v1")
        self.assertIn("start:GW:101", client.events)
        self.assertIn("start:OBS:110", client.events)

    def test_apply_stops_when_created_network_cannot_be_read_back(self) -> None:
        spec = load_topology_spec(Path("scripts/eve_mainline_topology.yaml"))
        client = FakeEveClient(missing_network_after_create="L02")
        with self.assertRaises(RuntimeError):
            apply_topology(client, spec, force=False)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python3 -m unittest discover -s tests -p 'test_eve_mainline_topology.py' -v
```

Expected:

```text
ImportError: cannot import name 'apply_topology'
```

- [ ] **Step 3: Implement the EVE client contract and a fake test client**

```python
class EveClient:
    def lab_exists(self, lab_name: str) -> bool:
        raise NotImplementedError

    def create_lab(self, lab: LabSpec) -> None:
        raise NotImplementedError

    def get_lab(self, lab_name: str) -> dict:
        raise NotImplementedError

    def create_node(self, lab_name: str, node: NodeSpec) -> dict:
        raise NotImplementedError

    def list_nodes(self, lab_name: str) -> list[dict]:
        raise NotImplementedError

    def create_network(self, lab_name: str, link: LinkSpec) -> int:
        raise NotImplementedError

    def list_networks(self, lab_name: str) -> list[dict]:
        raise NotImplementedError

    def attach_interface(self, lab_name: str, node_id: int, interface_index: int, network_id: int) -> None:
        raise NotImplementedError

    def get_node_interfaces(self, lab_name: str, node_id: int) -> list[dict]:
        raise NotImplementedError

    def start_node(self, lab_name: str, node_id: int) -> dict:
        raise NotImplementedError


class FakeEveClient(EveClient):
    def __init__(self, existing_lab: bool = False, missing_network_after_create: str | None = None) -> None:
        self.existing_lab = existing_lab
        self.missing_network_after_create = missing_network_after_create
        self.events: list[str] = []
        self.networks: dict[str, int] = {}
        self.nodes: dict[str, dict] = {}
        self.interfaces: dict[int, dict[int, int]] = {}

    def lab_exists(self, lab_name: str) -> bool:
        return self.existing_lab

    def create_lab(self, lab: LabSpec) -> None:
        self.events.append(f"create-lab:{lab.name}")

    def get_lab(self, lab_name: str) -> dict:
        return {"name": lab_name}

    def create_node(self, lab_name: str, node: NodeSpec) -> dict:
        self.nodes[node.name] = {"id": node.id, "console": 32768 + node.id}
        self.interfaces[node.id] = {}
        self.events.append(f"create-node:{node.name}:{node.id}")
        return self.nodes[node.name]

    def list_nodes(self, lab_name: str) -> list[dict]:
        return [{"name": name, **data} for name, data in self.nodes.items()]

    def create_network(self, lab_name: str, link: LinkSpec) -> int:
        network_id = len(self.networks) + 1
        if link.id != self.missing_network_after_create:
            self.networks[link.id] = network_id
        self.events.append(f"create-network:{link.id}:{network_id}")
        return network_id

    def list_networks(self, lab_name: str) -> list[dict]:
        return [{"name": link_id, "id": network_id} for link_id, network_id in self.networks.items()]

    def attach_interface(self, lab_name: str, node_id: int, interface_index: int, network_id: int) -> None:
        self.interfaces[node_id][interface_index] = network_id
        self.events.append(f"attach:{node_id}:{interface_index}:{network_id}")

    def get_node_interfaces(self, lab_name: str, node_id: int) -> list[dict]:
        return [
            {"id": index, "network_id": network_id}
            for index, network_id in sorted(self.interfaces[node_id].items())
        ]

    def start_node(self, lab_name: str, node_id: int) -> dict:
        self.events.append(f"start:{self._node_name_by_id(node_id)}:{node_id}")
        return {"console": 32768 + node_id}

    def _node_name_by_id(self, node_id: int) -> str:
        for name, data in self.nodes.items():
            if data["id"] == node_id:
                return name
        raise KeyError(node_id)
```

- [ ] **Step 4: Implement `apply_topology` with read-back validation**

```python
def apply_topology(client: EveClient, spec: TopologySpec, force: bool) -> dict:
    require_safe_lab_name(spec.lab.name, force=force)

    if client.lab_exists(spec.lab.name):
        destroy_topology(client, spec, force=force)

    client.create_lab(spec.lab)
    client.get_lab(spec.lab.name)

    created_nodes: dict[str, dict] = {}
    for node in spec.nodes:
        created_nodes[node.name] = client.create_node(spec.lab.name, node)

    node_readback = {item["name"]: item["id"] for item in client.list_nodes(spec.lab.name)}
    expected_node_ids = {node.name: node.id for node in spec.nodes}
    if node_readback != expected_node_ids:
        raise RuntimeError(f"node read-back mismatch: expected={expected_node_ids} got={node_readback}")

    network_ids: dict[str, int] = {}
    for link in spec.links:
        network_id = client.create_network(spec.lab.name, link)
        network_ids[link.id] = network_id
        visible_networks = {item["name"] for item in client.list_networks(spec.lab.name)}
        if link.id not in visible_networks:
            raise RuntimeError(f"network not visible after create: {link.id}")

    for link in spec.links:
        network_id = network_ids[link.id]
        for endpoint in link.endpoints:
            if endpoint.node is None:
                continue
            node_id = spec.node_map[endpoint.node].id
            client.attach_interface(spec.lab.name, node_id, int(endpoint.interface), network_id)
        for endpoint in link.endpoints:
            if endpoint.node is None:
                continue
            node_id = spec.node_map[endpoint.node].id
            interfaces = {item["id"]: item["network_id"] for item in client.get_node_interfaces(spec.lab.name, node_id)}
            if interfaces.get(int(endpoint.interface)) != network_id:
                raise RuntimeError(
                    f"interface read-back mismatch for {link.id}: "
                    f"{endpoint.node}:{endpoint.interface} expected={network_id} got={interfaces.get(int(endpoint.interface))}"
                )

    result_nodes: dict[str, dict] = {}
    for node in spec.nodes:
        start_result = client.start_node(spec.lab.name, node.id)
        result_nodes[node.name] = {"id": node.id, "console": start_result["console"]}

    return {
        "status": "ok",
        "lab": spec.lab.name,
        "nodes": result_nodes,
        "networks": {link_id: {"id": network_id} for link_id, network_id in network_ids.items()},
        "warnings": [],
    }
```

- [ ] **Step 5: Wire the CLI `apply` command**

```python
import os

from eve_mainline_topology_lib import (
    RequestsEveClient,
    apply_topology,
    load_topology_spec,
    render_plan_summary,
)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    spec = load_topology_spec(Path(args.spec))

    if args.command == "plan":
        payload = render_plan_summary(spec)
        print(f"LAB planned: {spec.lab.name}")
        print(f"NODES planned: {len(spec.nodes)}")
        print(f"LINKS planned: {len(spec.links)}")
        print(json.dumps(payload, ensure_ascii=False))
        return 0

    client = RequestsEveClient(
        host=os.getenv("EVE_HOST", "192.168.100.20"),
        username=os.getenv("EVE_USER", "admin"),
        password=os.getenv("EVE_PASS", "eve"),
    )

    if args.command == "apply":
        payload = apply_topology(client, spec, force=args.force)
        print(f"LAB created: {spec.lab.name}")
        print(json.dumps(payload, ensure_ascii=False))
        return 0

    raise NotImplementedError(f"command not implemented yet: {args.command}")
```

- [ ] **Step 6: Run tests to verify they pass**

Run:

```bash
python3 -m unittest discover -s tests -p 'test_eve_mainline_topology.py' -v
```

Expected:

```text
OK
```

- [ ] **Step 7: Commit**

```bash
git add scripts/eve_mainline_topology.py scripts/eve_mainline_topology_lib.py tests/test_eve_mainline_topology.py
git commit -m "feat: add EVE mainline topology apply workflow"
```

### Task 4: Implement `destroy`, harden output, and write usage docs

**Files:**
- Modify: `scripts/eve_mainline_topology.py`
- Modify: `scripts/eve_mainline_topology_lib.py`
- Modify: `tests/test_eve_mainline_topology.py`
- Create: `docs/testing/eve-ng-mainline-topology-script-usage.md`

- [ ] **Step 1: Write the failing destroy-flow and warning tests**

```python
import unittest
from pathlib import Path

from scripts.eve_mainline_topology_lib import FakeEveClient, destroy_topology, load_topology_spec


class TopologyDestroyFlowTest(unittest.TestCase):
    def test_destroy_runs_safe_delete_order(self) -> None:
        spec = load_topology_spec(Path("scripts/eve_mainline_topology.yaml"))
        client = FakeEveClient(existing_lab=True)
        result = destroy_topology(client, spec, force=False)
        self.assertEqual(result["status"], "destroyed")
        self.assertEqual(result["lab"], "oneops-network-mainline-v1")
        self.assertIn("stop:101", client.events)
        self.assertIn("delete-lab:oneops-network-mainline-v1", client.events)

    def test_destroy_reports_residual_warning_when_cleanup_not_complete(self) -> None:
        spec = load_topology_spec(Path("scripts/eve_mainline_topology.yaml"))
        client = FakeEveClient(existing_lab=True, fail_delete_node_id=110)
        result = destroy_topology(client, spec, force=False)
        self.assertEqual(result["status"], "partial")
        self.assertIn("node-delete-failed:110", result["warnings"])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python3 -m unittest discover -s tests -p 'test_eve_mainline_topology.py' -v
```

Expected:

```text
ImportError: cannot import name 'destroy_topology'
```

- [ ] **Step 3: Implement `destroy_topology` and residual warnings**

```python
def destroy_topology(client: EveClient, spec: TopologySpec, force: bool) -> dict:
    require_safe_lab_name(spec.lab.name, force=force)
    warnings: list[str] = []
    client.events.append(f"destroy:{spec.lab.name}")

    if not client.lab_exists(spec.lab.name):
        return {"status": "absent", "lab": spec.lab.name, "warnings": warnings}

    for node in spec.nodes:
        try:
            client.stop_node(spec.lab.name, node.id)
        except Exception:
            warnings.append(f"stop-failed:{node.id}")

    for link in spec.links:
        for endpoint in link.endpoints:
            if endpoint.node is None:
                continue
            try:
                client.attach_interface(spec.lab.name, spec.node_map[endpoint.node].id, int(endpoint.interface), 0)
            except Exception:
                warnings.append(f"detach-failed:{endpoint.node}:{endpoint.interface}")

    for link in reversed(spec.links):
        try:
            client.delete_network(spec.lab.name, link.id)
        except Exception:
            warnings.append(f"network-delete-failed:{link.id}")

    for node in reversed(spec.nodes):
        try:
            client.delete_node(spec.lab.name, node.id)
        except Exception:
            warnings.append(f"node-delete-failed:{node.id}")

    try:
        client.delete_lab(spec.lab.name)
    except Exception:
        warnings.append(f"lab-delete-failed:{spec.lab.name}")

    return {
        "status": "destroyed" if not warnings else "partial",
        "lab": spec.lab.name,
        "warnings": warnings,
    }
```

- [ ] **Step 4: Finish the CLI destroy path and stable JSON output**

```python
    if args.command == "apply":
        payload = apply_topology(client, spec, force=args.force)
        print(f"LAB created: {spec.lab.name}")
        for node_name, node_payload in payload["nodes"].items():
            print(f"NODE started: {node_name} -> console {node_payload['console']}")
        print(json.dumps(payload, ensure_ascii=False))
        return 0

    if args.command == "destroy":
        payload = destroy_topology(client, spec, force=args.force)
        print(f"LAB destroyed: {spec.lab.name}")
        print(json.dumps(payload, ensure_ascii=False))
        return 0

    raise NotImplementedError(f"command not implemented yet: {args.command}")
```

- [ ] **Step 5: Write the teammate usage doc**

```markdown
# EVE Mainline Topology Script Usage

## Goal

Use a local CLI to safely rebuild or delete the current OneOps EVE mainline topology without using a model-driven agent.

## Commands

```bash
python3 scripts/eve_mainline_topology.py plan
python3 scripts/eve_mainline_topology.py apply
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
2. `apply` safely deletes the same-name lab if it already exists, then recreates the current frozen topology and starts nodes.
3. `destroy` performs safe deletion in this order: stop nodes, detach interfaces, delete networks, delete nodes, delete lab.

## Current non-goals

1. No device initialization
2. No SSH validation
3. No SNMP validation
4. No OBS `controller + agent` deployment
5. No automatic host-side orphan `tap/tmp` cleanup
```

- [ ] **Step 6: Run tests to verify they pass**

Run:

```bash
python3 -m unittest discover -s tests -p 'test_eve_mainline_topology.py' -v
```

Expected:

```text
OK
```

- [ ] **Step 7: Commit**

```bash
git add scripts/eve_mainline_topology.py scripts/eve_mainline_topology_lib.py tests/test_eve_mainline_topology.py docs/testing/eve-ng-mainline-topology-script-usage.md
git commit -m "feat: add EVE mainline topology destroy workflow"
```

## Self-review

Spec coverage check:

1. Local CLI plus YAML contract: covered by Task 1 and Task 2
2. `plan / apply / destroy`: covered by Task 2, Task 3, and Task 4
3. Safe same-name deletion before rebuild: covered by Task 3 and Task 4
4. Read-back validation after writes: covered by Task 3
5. Human summary plus JSON output: covered by Task 2, Task 3, and Task 4
6. Current non-goals remain excluded: reflected in Task 4 usage doc and no task introduces device init or OBS deployment

Placeholder scan:

1. No `TODO`, `TBD`, or “similar to above” placeholders remain
2. Each code step contains concrete file content or function content
3. Every test step has an exact command and expected outcome

Type consistency check:

1. `TopologySpecError`, `load_topology_spec`, `require_safe_lab_name`, `render_plan_summary`, `apply_topology`, and `destroy_topology` are referenced consistently across tasks
2. YAML uses `ram` in MiB and the OBS fixed value stays `16384`
3. The command names remain exactly `plan`, `apply`, and `destroy`
