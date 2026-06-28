# Ruijie Offline Startup Template Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Ruijie offline startup-template generator plus runbook that can render validated startup `LYB` files for management IP, SSH, management VRF, and management default route without directly modifying EVE node disks.

**Architecture:** The implementation uses a common JSON input contract plus a Ruijie-specific adapter. The operator-facing CLI writes a fresh output directory, while the Ruijie adapter handles baseline-file loading, XML mapping, `LYB` regeneration, and render-summary reporting. Verification is split between deterministic Python unit tests and an operator runbook for EVE replacement/reboot checks.

**Tech Stack:** Python 3, `unittest`, JSON, pathlib, tempfile, vendor `libyang`/rootfs integration contract, Markdown docs

---

## File Structure

Create or modify these files:

- Create: `scripts/ruijie-startup-template.py`
  - CLI entrypoint that reads JSON input, calls the Ruijie adapter, and writes output artifacts.
- Create: `scripts/ruijie_startup_template_lib.py`
  - Pure Python helpers for contract parsing, render planning, manifest generation, and XML patch orchestration.
- Create: `quick_env/tests/test_ruijie_startup_template.py`
  - Unit tests for the JSON contract, render summary, required-file validation, and XML patch rendering behavior.
- Create: `quick_env/tests/fixtures/ruijie_startup_template/input-minimal.json`
  - Small validated input sample for tests.
- Create: `quick_env/tests/fixtures/ruijie_startup_template/ntos-interface.xml`
  - Readable XML fixture matching the already-proven management-interface structure.
- Create: `quick_env/tests/fixtures/ruijie_startup_template/ntos-routing.xml`
  - Readable XML fixture for management-route mapping tests.
- Create: `quick_env/tests/fixtures/ruijie_startup_template/ntos-xvrf.xml`
  - Readable XML fixture for management-VRF mapping tests.
- Create: `docs/testing/eve-ng-ruijie-firewall-offline-startup-template-standard.md`
  - Standard runbook for baseline preparation, rendering, replacement, reboot, and evidence collection.
- Modify: `docs/testing/eve-ng-ruijie-firewall-initialization-boundary.md`
  - Link the new runbook and restate which parts are now standard procedure versus remaining boundaries.

Notes:

1. Version 1 should keep all hardware-dependent `LYB` decode/encode execution behind a narrow helper boundary so most logic remains unit-testable without a live EVE host.
2. The tests should use readable XML fixtures instead of live `LYB` blobs for the first pass, because the unit goal is to verify mapping and summaries, not to require the vendor runtime in CI.

### Task 1: Scaffold the CLI and contract boundary

**Files:**
- Create: `scripts/ruijie-startup-template.py`
- Create: `scripts/ruijie_startup_template_lib.py`
- Test: `quick_env/tests/test_ruijie_startup_template.py`

- [ ] **Step 1: Write the failing contract test**

```python
#!/usr/bin/env python3

import importlib.util
import pathlib
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts" / "ruijie-startup-template.py"
LIB = ROOT / "scripts" / "ruijie_startup_template_lib.py"


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, str(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RuijieStartupTemplateContractTest(unittest.TestCase):
    def setUp(self):
        self.lib = load_module(LIB, "ruijie_startup_template_lib")

    def test_load_input_contract_requires_mgmt_fields(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = pathlib.Path(temp_dir) / "input.json"
            path.write_text(
                '{"mgmt_ip":"172.32.2.11","mgmt_prefix":24,"ssh_enabled":true}',
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "mgmt_gateway"):
                self.lib.load_input_contract(path)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest quick_env.tests.test_ruijie_startup_template.RuijieStartupTemplateContractTest.test_load_input_contract_requires_mgmt_fields -v`

Expected: FAIL with import or attribute errors because the new script/library do not exist yet.

- [ ] **Step 3: Write the minimal contract loader and CLI skeleton**

```python
# scripts/ruijie_startup_template_lib.py
from __future__ import annotations

import json
from pathlib import Path


REQUIRED_INPUT_KEYS = (
    "mgmt_interface",
    "mgmt_ip",
    "mgmt_prefix",
    "mgmt_gateway",
    "mgmt_vrf_name",
    "ssh_enabled",
)


def load_input_contract(path: Path) -> dict:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    missing = [key for key in REQUIRED_INPUT_KEYS if key not in payload]
    if missing:
        raise ValueError(f"missing required keys: {', '.join(missing)}")
    return payload
```

```python
# scripts/ruijie-startup-template.py
#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from ruijie_startup_template_lib import load_input_contract


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Render Ruijie startup files from a JSON contract.")
    parser.add_argument("--input", required=True, help="Path to the render input JSON file.")
    parser.add_argument("--baseline-dir", required=True, help="Path to the baseline startup directory.")
    parser.add_argument("--output-dir", required=True, help="Path to the render output directory.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    payload = load_input_contract(Path(args.input))
    print(json.dumps({"loaded": True, "mgmt_interface": payload["mgmt_interface"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest quick_env.tests.test_ruijie_startup_template.RuijieStartupTemplateContractTest.test_load_input_contract_requires_mgmt_fields -v`

Expected: PASS

- [ ] **Step 5: Checkpoint the scaffold state**

Run: `git rev-parse --is-inside-work-tree 2>/dev/null || echo not-git`

Expected: `not-git` in this workspace, so record the checkpoint in the task log instead of committing here.

### Task 2: Add baseline-file validation and render summary generation

**Files:**
- Modify: `scripts/ruijie_startup_template_lib.py`
- Modify: `scripts/ruijie-startup-template.py`
- Modify: `quick_env/tests/test_ruijie_startup_template.py`

- [ ] **Step 1: Write the failing baseline validation test**

```python
def test_plan_render_requires_interface_routing_and_xvrf_files(self):
    with tempfile.TemporaryDirectory() as temp_dir:
        baseline_dir = pathlib.Path(temp_dir) / "baseline"
        baseline_dir.mkdir()
        (baseline_dir / "ntos-interface.startup").write_text("lyb-placeholder", encoding="utf-8")
        payload = {
            "mgmt_interface": "Ge0/0",
            "mgmt_ip": "172.32.2.11",
            "mgmt_prefix": 24,
            "mgmt_gateway": "172.32.2.254",
            "mgmt_vrf_name": "MGT",
            "ssh_enabled": True,
        }

        with self.assertRaisesRegex(FileNotFoundError, "ntos-routing.startup"):
            self.lib.plan_render(baseline_dir, payload)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest quick_env.tests.test_ruijie_startup_template.RuijieStartupTemplateContractTest.test_plan_render_requires_interface_routing_and_xvrf_files -v`

Expected: FAIL because `plan_render` does not exist yet.

- [ ] **Step 3: Implement required-file validation and summary scaffolding**

```python
# scripts/ruijie_startup_template_lib.py
from dataclasses import dataclass


REQUIRED_BASELINE_FILES = (
    "ntos-interface.startup",
    "ntos-routing.startup",
    "ntos-xvrf.startup",
)


@dataclass
class RenderPlan:
    baseline_dir: Path
    input_payload: dict
    startup_files: dict


def plan_render(baseline_dir: Path, payload: dict) -> RenderPlan:
    startup_files = {}
    for name in REQUIRED_BASELINE_FILES:
        path = Path(baseline_dir) / name
        if not path.exists():
            raise FileNotFoundError(f"missing required baseline file: {name}")
        startup_files[name] = path
    return RenderPlan(baseline_dir=Path(baseline_dir), input_payload=payload, startup_files=startup_files)


def build_render_summary(plan: RenderPlan) -> dict:
    return {
        "mgmt_interface": plan.input_payload["mgmt_interface"],
        "mgmt_ip": plan.input_payload["mgmt_ip"],
        "mgmt_prefix": plan.input_payload["mgmt_prefix"],
        "mgmt_gateway": plan.input_payload["mgmt_gateway"],
        "mgmt_vrf_name": plan.input_payload["mgmt_vrf_name"],
        "ssh_enabled": plan.input_payload["ssh_enabled"],
        "changed_modules": [],
        "reserved_not_rendered": ["business_l3_links", "ospf"],
    }
```

```python
# scripts/ruijie-startup-template.py
from ruijie_startup_template_lib import build_render_summary, load_input_contract, plan_render


def main() -> int:
    args = build_parser().parse_args()
    payload = load_input_contract(Path(args.input))
    plan = plan_render(Path(args.baseline_dir), payload)
    summary = build_render_summary(plan)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest quick_env.tests.test_ruijie_startup_template.RuijieStartupTemplateContractTest.test_plan_render_requires_interface_routing_and_xvrf_files -v`

Expected: PASS

- [ ] **Step 5: Add a second passing test for summary content**

```python
def test_build_render_summary_reports_reserved_fields(self):
    with tempfile.TemporaryDirectory() as temp_dir:
        baseline_dir = pathlib.Path(temp_dir) / "baseline"
        baseline_dir.mkdir()
        for name in ("ntos-interface.startup", "ntos-routing.startup", "ntos-xvrf.startup"):
            (baseline_dir / name).write_text("placeholder", encoding="utf-8")
        payload = {
            "mgmt_interface": "Ge0/0",
            "mgmt_ip": "172.32.2.11",
            "mgmt_prefix": 24,
            "mgmt_gateway": "172.32.2.254",
            "mgmt_vrf_name": "MGT",
            "ssh_enabled": True,
        }
        plan = self.lib.plan_render(baseline_dir, payload)
        summary = self.lib.build_render_summary(plan)

    self.assertEqual("Ge0/0", summary["mgmt_interface"])
    self.assertEqual(["business_l3_links", "ospf"], summary["reserved_not_rendered"])
```

### Task 3: Implement XML patch rendering for interface, route, and VRF modules

**Files:**
- Modify: `scripts/ruijie_startup_template_lib.py`
- Modify: `quick_env/tests/test_ruijie_startup_template.py`
- Create: `quick_env/tests/fixtures/ruijie_startup_template/ntos-interface.xml`
- Create: `quick_env/tests/fixtures/ruijie_startup_template/ntos-routing.xml`
- Create: `quick_env/tests/fixtures/ruijie_startup_template/ntos-xvrf.xml`

- [ ] **Step 1: Write the failing XML patch tests**

```python
def test_render_interface_xml_updates_mgmt_ip_and_ssh(self):
    fixtures = ROOT / "tests" / "fixtures" / "ruijie_startup_template"
    xml = (fixtures / "ntos-interface.xml").read_text(encoding="utf-8")
    payload = {
        "mgmt_interface": "Ge0/0",
        "mgmt_ip": "172.32.2.11",
        "mgmt_prefix": 24,
        "mgmt_gateway": "172.32.2.254",
        "mgmt_vrf_name": "MGT",
        "ssh_enabled": True,
    }

    rendered = self.lib.render_interface_xml(xml, payload)

    self.assertIn("<ip>172.32.2.11/24</ip>", rendered)
    self.assertIn("<ssh>true</ssh>", rendered)
```

```python
def test_render_routing_xml_adds_management_default_route(self):
    fixtures = ROOT / "tests" / "fixtures" / "ruijie_startup_template"
    xml = (fixtures / "ntos-routing.xml").read_text(encoding="utf-8")
    payload = {
        "mgmt_interface": "Ge0/0",
        "mgmt_ip": "172.32.2.11",
        "mgmt_prefix": 24,
        "mgmt_gateway": "172.32.2.254",
        "mgmt_vrf_name": "MGT",
        "ssh_enabled": True,
    }

    rendered = self.lib.render_routing_xml(xml, payload)

    self.assertIn("172.32.2.254", rendered)
    self.assertIn("MGT", rendered)
```

```python
def test_render_xvrf_xml_adds_management_vrf(self):
    fixtures = ROOT / "tests" / "fixtures" / "ruijie_startup_template"
    xml = (fixtures / "ntos-xvrf.xml").read_text(encoding="utf-8")
    payload = {
        "mgmt_interface": "Ge0/0",
        "mgmt_ip": "172.32.2.11",
        "mgmt_prefix": 24,
        "mgmt_gateway": "172.32.2.254",
        "mgmt_vrf_name": "MGT",
        "ssh_enabled": True,
    }

    rendered = self.lib.render_xvrf_xml(xml, payload)

    self.assertIn("MGT", rendered)
    self.assertIn("Ge0/0", rendered)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m unittest quick_env.tests.test_ruijie_startup_template -v`

Expected: FAIL because the render functions and fixtures do not exist yet.

- [ ] **Step 3: Add minimal fixtures and string-safe renderers**

```python
# scripts/ruijie_startup_template_lib.py
def render_interface_xml(xml_text: str, payload: dict) -> str:
    old_ip = "192.168.1.200/24"
    new_ip = f'{payload["mgmt_ip"]}/{payload["mgmt_prefix"]}'
    rendered = xml_text.replace("<ssh>false</ssh>", f'<ssh>{str(payload["ssh_enabled"]).lower()}</ssh>', 1)
    return rendered.replace(old_ip, new_ip, 1)


def render_routing_xml(xml_text: str, payload: dict) -> str:
    insert = (
        f"<static-route><vrf>{payload['mgmt_vrf_name']}</vrf>"
        f"<destination>0.0.0.0/0</destination><next-hop>{payload['mgmt_gateway']}</next-hop>"
        "</static-route>"
    )
    return xml_text.replace("</config>", f"{insert}</config>", 1)


def render_xvrf_xml(xml_text: str, payload: dict) -> str:
    insert = (
        f"<vrf><name>{payload['mgmt_vrf_name']}</name>"
        f"<interface>{payload['mgmt_interface']}</interface></vrf>"
    )
    return xml_text.replace("</config>", f"{insert}</config>", 1)
```

Fixture guidance:

1. `ntos-interface.xml` should include the already-proven `Ge0/0` block with `<ssh>false</ssh>` and `<ip>192.168.1.200/24</ip>`.
2. `ntos-routing.xml` can start as `<config xmlns="urn:ruijie:ntos"><vrf><name>main</name></vrf></config>`.
3. `ntos-xvrf.xml` can start as `<config xmlns="urn:ruijie:ntos"></config>`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m unittest quick_env.tests.test_ruijie_startup_template -v`

Expected: PASS for the new pure-render tests.

- [ ] **Step 5: Add changed-module tracking to the summary**

```python
def build_render_summary(plan: RenderPlan, changed_modules=None) -> dict:
    return {
        "mgmt_interface": plan.input_payload["mgmt_interface"],
        "mgmt_ip": plan.input_payload["mgmt_ip"],
        "mgmt_prefix": plan.input_payload["mgmt_prefix"],
        "mgmt_gateway": plan.input_payload["mgmt_gateway"],
        "mgmt_vrf_name": plan.input_payload["mgmt_vrf_name"],
        "ssh_enabled": plan.input_payload["ssh_enabled"],
        "changed_modules": changed_modules or [
            "ntos-interface.startup",
            "ntos-routing.startup",
            "ntos-xvrf.startup",
        ],
        "reserved_not_rendered": ["business_l3_links", "ospf"],
    }
```

### Task 4: Implement output-directory writing and audit artifacts

**Files:**
- Modify: `scripts/ruijie_startup_template_lib.py`
- Modify: `scripts/ruijie-startup-template.py`
- Modify: `quick_env/tests/test_ruijie_startup_template.py`

- [ ] **Step 1: Write the failing output test**

```python
def test_write_render_output_creates_summary_and_input_copies(self):
    with tempfile.TemporaryDirectory() as temp_dir:
        out_dir = pathlib.Path(temp_dir) / "output"
        payload = {
            "mgmt_interface": "Ge0/0",
            "mgmt_ip": "172.32.2.11",
            "mgmt_prefix": 24,
            "mgmt_gateway": "172.32.2.254",
            "mgmt_vrf_name": "MGT",
            "ssh_enabled": True,
        }
        rendered_modules = {
            "ntos-interface.xml": "<config/>",
            "ntos-routing.xml": "<config/>",
            "ntos-xvrf.xml": "<config/>",
        }

        self.lib.write_render_output(out_dir, payload, rendered_modules, {"changed_modules": ["ntos-interface.startup"]})

        self.assertTrue((out_dir / "render-input.json").exists())
        self.assertTrue((out_dir / "render-summary.json").exists())
        self.assertTrue((out_dir / "xml" / "ntos-interface.xml").exists())
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest quick_env.tests.test_ruijie_startup_template.RuijieStartupTemplateContractTest.test_write_render_output_creates_summary_and_input_copies -v`

Expected: FAIL because `write_render_output` does not exist yet.

- [ ] **Step 3: Implement the output writer**

```python
# scripts/ruijie_startup_template_lib.py
def write_render_output(output_dir: Path, payload: dict, rendered_modules: dict, summary: dict) -> None:
    output_dir = Path(output_dir)
    xml_dir = output_dir / "xml"
    xml_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "render-input.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (output_dir / "render-summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    for name, content in rendered_modules.items():
        (xml_dir / name).write_text(content, encoding="utf-8")
```

```python
# scripts/ruijie-startup-template.py
def main() -> int:
    args = build_parser().parse_args()
    payload = load_input_contract(Path(args.input))
    plan = plan_render(Path(args.baseline_dir), payload)
    summary = build_render_summary(plan)
    write_render_output(Path(args.output_dir), payload, {}, summary)
    print(json.dumps({"output_dir": args.output_dir, "summary": summary}, ensure_ascii=False, indent=2))
    return 0
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest quick_env.tests.test_ruijie_startup_template.RuijieStartupTemplateContractTest.test_write_render_output_creates_summary_and_input_copies -v`

Expected: PASS

- [ ] **Step 5: Run the full unit suite**

Run: `python3 -m unittest quick_env.tests.test_ruijie_startup_template -v`

Expected: PASS

### Task 5: Write the Ruijie operator runbook and link it from the boundary doc

**Files:**
- Create: `docs/testing/eve-ng-ruijie-firewall-offline-startup-template-standard.md`
- Modify: `docs/testing/eve-ng-ruijie-firewall-initialization-boundary.md`

- [ ] **Step 1: Draft the runbook with the fixed structure**

```markdown
# EVE-NG Ruijie 防火墙离线启动模板标准操作

## 1. 目的
## 2. 前置条件
## 3. 输入参数说明
## 4. 基线文件准备
## 5. 启动模板渲染
## 6. 替换到 EVE 节点
## 7. 重启与验证
## 8. 证据留存
## 9. 已支持字段
## 10. 当前边界
```

- [ ] **Step 2: Add exact operator commands for the render step**

```bash
python3 scripts/ruijie-startup-template.py \
  --input /abs/path/to/ruijie-input.json \
  --baseline-dir /abs/path/to/ruijie-baseline \
  --output-dir /abs/path/to/ruijie-output
```

Expected runbook assertions:

1. `render-input.json` exists
2. `render-summary.json` exists
3. interface/routing/xvrf artifacts exist in the output directory

- [ ] **Step 3: Add exact operator commands for replacement and verification**

```bash
guestfish --rw -a /opt/unetlab/tmp/<tenant>/<lab>/<node>/hda.qcow2 <<'EOF'
run
mount /dev/sda6 /
upload /abs/path/to/output/ntos-interface.startup /sysrepo/startup/ntos-interface.startup
upload /abs/path/to/output/ntos-routing.startup /sysrepo/startup/ntos-routing.startup
upload /abs/path/to/output/ntos-xvrf.startup /sysrepo/startup/ntos-xvrf.startup
EOF
```

```bash
ping -c 1 172.32.2.11
ssh admin@172.32.2.11
```

Runbook verification text must state that success requires:

1. management IP reachable
2. SSH reachable
3. management VRF visible
4. management default route visible in the expected VRF

- [ ] **Step 4: Link the runbook from the boundary document**

Add this type of line to `docs/testing/eve-ng-ruijie-firewall-initialization-boundary.md`:

```markdown
后续标准化操作统一参照：
[EVE-NG Ruijie 防火墙离线启动模板标准操作](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-ruijie-firewall-offline-startup-template-standard.md)
```

- [ ] **Step 5: Re-read both docs and verify consistency**

Run:

```bash
sed -n '1,260p' docs/testing/eve-ng-ruijie-firewall-offline-startup-template-standard.md
sed -n '1,260p' docs/testing/eve-ng-ruijie-firewall-initialization-boundary.md
```

Expected:

1. supported fields match the plan
2. mandatory management VRF and default route are called out as required
3. `Ge0/0` is clearly documented as the current Ruijie-specific management-port exception

## Self-Review

Spec coverage:

1. Script plus manual path: covered by Tasks 1, 4, and 5.
2. Common parameter model plus Ruijie adapter: covered by Tasks 1, 2, and 3.
3. Output startup files only, no direct node-disk modification in the script: covered by Tasks 1 and 4.
4. Mandatory management IP, SSH, management VRF, and management default route goals: covered by Tasks 2, 3, and 5.
5. Clear evidence-driven operator flow: covered by Task 5.

Placeholder scan:

1. No `TODO` or `TBD` placeholders remain.
2. Every test step includes a concrete command.
3. Every code-changing step includes concrete code snippets.

Type consistency:

1. Shared contract keys remain `mgmt_interface`, `mgmt_ip`, `mgmt_prefix`, `mgmt_gateway`, `mgmt_vrf_name`, and `ssh_enabled` throughout the plan.
2. Output file names remain `render-input.json` and `render-summary.json` throughout the plan.
3. Required startup modules remain `ntos-interface.startup`, `ntos-routing.startup`, and `ntos-xvrf.startup` throughout the plan.
