# Quick Env Runtime Core / Env Updater Phase 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Split `quick_env` phase 1 into a thin `runtime-core` layer plus a manifest-driven `env-updater`, and make the first four update modules (`device-discovery/common`, `device-discovery/h3c`, `snmp-observability/common`, `snmp-observability/h3c`) runnable against an existing quick env instance.

**Architecture:** Keep the current `quick_env` runtime working, but move business seed/update logic into a new Python-based updater that understands bundle/module manifests, target adapters, and three explicit surfaces: `mysql`, `nacos`, and `record_rule`. Phase 1 does not attempt a full runtime rewrite; it adds the new updater, seeds the first bundle set, introduces `runtime-core` wrapper scripts, and removes a first batch of `sync_*` work from the default startup path.

**Tech Stack:** Bash, Python 3.6+, PyYAML, existing quick_env runtime render scripts, MySQL CLI, Nacos HTTP API, vmalert file merge/reload, `unittest`, existing quick_env shell tests.

---

## File Structure

### New files

- `quick_env/env-updater/scripts/update.py`
  - CLI entrypoint for `plan`, `apply`, `verify`, and `rollout`.
- `quick_env/env-updater/lib/__init__.py`
  - Package marker.
- `quick_env/env-updater/lib/manifest.py`
  - Loads and validates bundle/module YAML manifests.
- `quick_env/env-updater/lib/planner.py`
  - Builds actionable plans from bundle/module selection.
- `quick_env/env-updater/lib/targets.py`
  - Resolves quick env v1 runtime targets and explicit targets.
- `quick_env/env-updater/lib/surfaces.py`
  - Executes or dry-runs `mysql`, `nacos`, and `record_rule` surfaces.
- `quick_env/env-updater/bundles/device-discovery/bundle.yaml`
  - Bundle manifest for discovery seeds.
- `quick_env/env-updater/bundles/device-discovery/modules/common/module.yaml`
  - Common discovery module.
- `quick_env/env-updater/bundles/device-discovery/modules/common/mysql/device_v2_schema.sql`
  - Idempotent discovery schema/runtime contract seed.
- `quick_env/env-updater/bundles/device-discovery/modules/common/nacos/device_v2_candidate_engine.patch.yaml`
  - Common candidate-engine patch.
- `quick_env/env-updater/bundles/device-discovery/modules/common/nacos/device_collection2_contracts.patch.yaml`
  - Common contract patch.
- `quick_env/env-updater/bundles/device-discovery/modules/h3c/module.yaml`
  - H3C discovery module.
- `quick_env/env-updater/bundles/device-discovery/modules/h3c/mysql/device_context_h3c.sql`
  - H3C device seed records extracted from current sync logic.
- `quick_env/env-updater/bundles/device-discovery/modules/h3c/nacos/device_collection2_contracts.patch.yaml`
  - H3C discovery contract patch.
- `quick_env/env-updater/bundles/snmp-observability/bundle.yaml`
  - Bundle manifest for SNMP strategy/dashboard seeds.
- `quick_env/env-updater/bundles/snmp-observability/modules/common/module.yaml`
  - Common SNMP observability module.
- `quick_env/env-updater/bundles/snmp-observability/modules/common/mysql/dashboard_templates.sql`
  - Common dashboard/strategy set seed.
- `quick_env/env-updater/bundles/snmp-observability/modules/common/record-rules/oneops_snmp_recording_rules.common.yaml`
  - Common vmalert managed group fragment.
- `quick_env/env-updater/bundles/snmp-observability/modules/h3c/module.yaml`
  - H3C SNMP observability module.
- `quick_env/env-updater/bundles/snmp-observability/modules/h3c/mysql/h3c_strategy_dashboard.sql`
  - H3C strategy/dashboard seed.
- `quick_env/env-updater/bundles/snmp-observability/modules/h3c/record-rules/oneops_snmp_recording_rules.h3c.yaml`
  - H3C record-rule additions.
- `quick_env/runtime-core/up.sh`
  - Thin startup wrapper for the minimal runtime.
- `quick_env/runtime-core/down.sh`
  - Thin stop wrapper.
- `quick_env/runtime-core/status.sh`
  - Thin status wrapper.
- `quick_env/tests/test_env_updater_manifest.py`
  - Manifest parsing/validation unit tests.
- `quick_env/tests/test_env_updater_plan.py`
  - Plan-building tests for bundle/module selection and dependencies.
- `quick_env/tests/test_env_updater_targets.py`
  - Target adapter tests.
- `quick_env/tests/test_env_updater_surfaces.py`
  - Surface dry-run tests.
- `quick_env/tests/test_env_updater_rollout.py`
  - End-to-end updater rollout test against a temp quick env runtime tree.

### Modified files

- `quick_env/start.sh`
  - Stops auto-running the first migrated `sync_*` blocks by default and prints the new updater path.
- `quick_env/manage.sh`
  - Adds an updater-facing helper or deprecation hint for migrated bootstrap/seed flows.
- `quick_env/README.md`
  - Documents `runtime-core` and `env-updater` usage.

---

### Task 1: Scaffold the env-updater manifest and planning core

**Files:**
- Create: `quick_env/env-updater/scripts/update.py`
- Create: `quick_env/env-updater/lib/__init__.py`
- Create: `quick_env/env-updater/lib/manifest.py`
- Create: `quick_env/env-updater/lib/planner.py`
- Test: `quick_env/tests/test_env_updater_manifest.py`
- Test: `quick_env/tests/test_env_updater_plan.py`

- [ ] **Step 1: Write the failing manifest and plan tests**

Create `quick_env/tests/test_env_updater_manifest.py`:

```python
#!/usr/bin/env python3

import importlib.util
import pathlib
import tempfile
import textwrap
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "env-updater" / "lib" / "manifest.py"


def load_module():
    spec = importlib.util.spec_from_file_location("env_updater_manifest", str(MANIFEST))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class EnvUpdaterManifestTest(unittest.TestCase):
    def test_load_bundle_and_module_manifest(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = pathlib.Path(temp_dir)
            (root / "modules" / "common").mkdir(parents=True)
            (root / "modules" / "common" / "module.yaml").write_text(
                textwrap.dedent(
                    """\
                    api_version: quickenv/v2
                    kind: Module
                    name: device-discovery/common
                    surfaces:
                      mysql: required
                      nacos: required
                      record_rule: not_applicable
                    mysql:
                      schema: UniOPS
                      files:
                        - mysql/common.sql
                    nacos:
                      patches:
                        - data_id: device_v2_candidate_engine
                          file: nacos/device_v2_candidate_engine.patch.yaml
                    """
                ),
                encoding="utf-8",
            )
            bundle_path = root / "bundle.yaml"
            bundle_path.write_text(
                textwrap.dedent(
                    """\
                    api_version: quickenv/v2
                    kind: Bundle
                    name: device-discovery
                    surfaces:
                      - mysql
                      - nacos
                      - record_rule
                    modules:
                      - name: common
                        path: modules/common/module.yaml
                    """
                ),
                encoding="utf-8",
            )

            bundle = module.load_bundle(bundle_path)
            module_row = module.load_module(bundle_path.parent / "modules" / "common" / "module.yaml")

        self.assertEqual("device-discovery", bundle["name"])
        self.assertEqual("device-discovery/common", module_row["name"])
        self.assertEqual("not_applicable", module_row["surfaces"]["record_rule"])


if __name__ == "__main__":
    unittest.main()
```

Create `quick_env/tests/test_env_updater_plan.py`:

```python
#!/usr/bin/env python3

import importlib.util
import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
PLANNER = ROOT / "env-updater" / "lib" / "planner.py"


def load_module():
    spec = importlib.util.spec_from_file_location("env_updater_planner", str(PLANNER))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class EnvUpdaterPlannerTest(unittest.TestCase):
    def test_build_plan_includes_bundle_module_and_surfaces(self):
        module = load_module()
        bundle = {
            "name": "snmp-observability",
            "modules": [{"name": "common"}, {"name": "h3c", "depends_on": ["common"]}],
        }
        modules = {
            "snmp-observability/common": {
                "name": "snmp-observability/common",
                "surfaces": {"mysql": "required", "nacos": "optional", "record_rule": "required"},
                "mysql": {"schema": "UniOPS", "files": ["mysql/common.sql"]},
                "nacos": {"patches": [{"data_id": "cipher-aes-start-config", "file": "nacos/common.patch.yaml"}]},
                "record_rule": {"groups": [{"name": "oneops_snmp_recording_rules", "file": "record-rules/common.yaml"}]},
            }
        }

        plan = module.build_plan(bundle, modules, "snmp-observability/common")

        self.assertEqual("snmp-observability/common", plan["target"])
        self.assertEqual(["mysql", "nacos", "record_rule"], [row["surface"] for row in plan["steps"]])
        self.assertEqual("UniOPS", plan["steps"][0]["schema"])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the tests to verify they fail**

Run:

```bash
python3 -m unittest \
  quick_env.tests.test_env_updater_manifest \
  quick_env.tests.test_env_updater_plan
```

Expected: FAIL with import/load errors because `env-updater/lib/manifest.py` and `planner.py` do not exist yet.

- [ ] **Step 3: Write the minimal manifest loader and planner**

Create `quick_env/env-updater/lib/manifest.py`:

```python
#!/usr/bin/env python3

import pathlib

import yaml


SURFACE_KEYS = ("mysql", "nacos", "record_rule")
SURFACE_MODES = ("required", "optional", "not_applicable")


def _load_yaml(path):
    with open(str(path), "r", encoding="utf-8") as handle:
        return yaml.safe_load(handle.read()) or {}


def load_bundle(path):
    data = _load_yaml(pathlib.Path(path))
    if data.get("kind") != "Bundle":
        raise ValueError("bundle manifest kind must be Bundle")
    return data


def load_module(path):
    data = _load_yaml(pathlib.Path(path))
    if data.get("kind") != "Module":
        raise ValueError("module manifest kind must be Module")
    surfaces = data.get("surfaces") or {}
    for key in SURFACE_KEYS:
        if key not in surfaces:
            raise ValueError("module surfaces must declare %s" % key)
        if surfaces[key] not in SURFACE_MODES:
            raise ValueError("invalid surface mode for %s: %s" % (key, surfaces[key]))
    return data
```

Create `quick_env/env-updater/lib/planner.py`:

```python
#!/usr/bin/env python3


def build_plan(bundle, modules, target_name):
    module_row = modules[target_name]
    plan = {"bundle": bundle["name"], "target": target_name, "steps": []}
    if module_row["surfaces"]["mysql"] != "not_applicable":
        plan["steps"].append(
            {"surface": "mysql", "schema": module_row["mysql"]["schema"], "files": module_row["mysql"]["files"]}
        )
    if module_row["surfaces"]["nacos"] != "not_applicable":
        plan["steps"].append({"surface": "nacos", "patches": module_row.get("nacos", {}).get("patches", [])})
    if module_row["surfaces"]["record_rule"] != "not_applicable":
        plan["steps"].append(
            {"surface": "record_rule", "groups": module_row.get("record_rule", {}).get("groups", [])}
        )
    return plan
```

Create `quick_env/env-updater/lib/__init__.py`:

```python
# env-updater package marker
```

Create `quick_env/env-updater/scripts/update.py`:

```python
#!/usr/bin/env python3

import argparse


def build_parser():
    parser = argparse.ArgumentParser(description="quick env updater")
    parser.add_argument("command", choices=("plan", "apply", "verify", "rollout"))
    parser.add_argument("target")
    return parser


def main():
    args = build_parser().parse_args()
    print("%s %s" % (args.command, args.target))


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run the tests to verify they pass**

Run:

```bash
python3 -m unittest \
  quick_env.tests.test_env_updater_manifest \
  quick_env.tests.test_env_updater_plan
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add \
  quick_env/env-updater/scripts/update.py \
  quick_env/env-updater/lib/__init__.py \
  quick_env/env-updater/lib/manifest.py \
  quick_env/env-updater/lib/planner.py \
  quick_env/tests/test_env_updater_manifest.py \
  quick_env/tests/test_env_updater_plan.py
git commit -m "feat: scaffold quick env updater planning core"
```

### Task 2: Add target adapters and surface execution primitives

**Files:**
- Create: `quick_env/env-updater/lib/targets.py`
- Create: `quick_env/env-updater/lib/surfaces.py`
- Test: `quick_env/tests/test_env_updater_targets.py`
- Test: `quick_env/tests/test_env_updater_surfaces.py`

- [ ] **Step 1: Write the failing target and surface tests**

Create `quick_env/tests/test_env_updater_targets.py`:

```python
#!/usr/bin/env python3

import importlib.util
import pathlib
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
TARGETS = ROOT / "env-updater" / "lib" / "targets.py"


def load_module():
    spec = importlib.util.spec_from_file_location("env_updater_targets", str(TARGETS))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class EnvUpdaterTargetsTest(unittest.TestCase):
    def test_resolves_quickenv_v1_runtime_target(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            runtime_dir = pathlib.Path(temp_dir) / "demo-a"
            runtime_dir.mkdir(parents=True)
            (runtime_dir / ".env").write_text("HOST_PORT_MYSQL=3606\nHOST_PORT_VMALERT=8880\n", encoding="utf-8")

            target = module.resolve_target(
                {"type": "quickenv_v1_runtime", "instance": "demo-a"},
                runtime_root=pathlib.Path(temp_dir),
            )

        self.assertEqual("demo-a", target["instance"])
        self.assertEqual("3606", target["mysql"]["port"])


if __name__ == "__main__":
    unittest.main()
```

Create `quick_env/tests/test_env_updater_surfaces.py`:

```python
#!/usr/bin/env python3

import importlib.util
import pathlib
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
SURFACES = ROOT / "env-updater" / "lib" / "surfaces.py"


def load_module():
    spec = importlib.util.spec_from_file_location("env_updater_surfaces", str(SURFACES))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class EnvUpdaterSurfacesTest(unittest.TestCase):
    def test_merge_record_rule_group_replaces_existing_group(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            rule_file = pathlib.Path(temp_dir) / "vmalert-rule.yml"
            rule_file.write_text(
                "groups:\\n  - name: oneops_snmp_recording_rules\\n    interval: 30s\\n    rules: []\\n",
                encoding="utf-8",
            )
            module.merge_record_rule_group(
                rule_file,
                {"name": "oneops_snmp_recording_rules", "interval": "30s", "rules": [{"record": "oneops:test", "expr": "up"}]},
            )
            content = rule_file.read_text(encoding="utf-8")

        self.assertIn("oneops:test", content)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the tests to verify they fail**

Run:

```bash
python3 -m unittest \
  quick_env.tests.test_env_updater_targets \
  quick_env.tests.test_env_updater_surfaces
```

Expected: FAIL because `targets.py` and `surfaces.py` do not exist yet.

- [ ] **Step 3: Implement the minimal target adapter and surface utilities**

Create `quick_env/env-updater/lib/targets.py`:

```python
#!/usr/bin/env python3

import pathlib


def _read_env(path):
    values = {}
    for line in pathlib.Path(path).read_text(encoding="utf-8").splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key] = value
    return values


def resolve_target(target, runtime_root):
    if target["type"] != "quickenv_v1_runtime":
        raise ValueError("only quickenv_v1_runtime is supported in phase 1")
    runtime_dir = pathlib.Path(runtime_root) / target["instance"]
    env_values = _read_env(runtime_dir / ".env")
    return {
        "instance": target["instance"],
        "runtime_dir": str(runtime_dir),
        "mysql": {"host": "127.0.0.1", "port": env_values["HOST_PORT_MYSQL"]},
        "record_rule": {
            "file": str(runtime_dir / "config" / "vmalert" / "vmalert-rule.yml"),
            "reload_url": "http://127.0.0.1:%s/-/reload" % env_values["HOST_PORT_VMALERT"],
        },
    }
```

Create `quick_env/env-updater/lib/surfaces.py`:

```python
#!/usr/bin/env python3

import pathlib

import yaml


def merge_record_rule_group(rule_file, group):
    rule_path = pathlib.Path(rule_file)
    parsed = yaml.safe_load(rule_path.read_text(encoding="utf-8")) or {}
    groups = list(parsed.get("groups", []) or [])
    groups = [row for row in groups if row.get("name") != group.get("name")]
    groups.append(group)
    parsed["groups"] = groups
    rule_path.write_text(yaml.safe_dump(parsed, sort_keys=False), encoding="utf-8")
```

- [ ] **Step 4: Run the tests to verify they pass**

Run:

```bash
python3 -m unittest \
  quick_env.tests.test_env_updater_targets \
  quick_env.tests.test_env_updater_surfaces
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add \
  quick_env/env-updater/lib/targets.py \
  quick_env/env-updater/lib/surfaces.py \
  quick_env/tests/test_env_updater_targets.py \
  quick_env/tests/test_env_updater_surfaces.py
git commit -m "feat: add quick env updater target and surface primitives"
```

### Task 3: Seed the first bundle/module set for discovery and SNMP observability

**Files:**
- Create: `quick_env/env-updater/bundles/device-discovery/bundle.yaml`
- Create: `quick_env/env-updater/bundles/device-discovery/modules/common/module.yaml`
- Create: `quick_env/env-updater/bundles/device-discovery/modules/common/mysql/device_v2_schema.sql`
- Create: `quick_env/env-updater/bundles/device-discovery/modules/common/nacos/device_v2_candidate_engine.patch.yaml`
- Create: `quick_env/env-updater/bundles/device-discovery/modules/common/nacos/device_collection2_contracts.patch.yaml`
- Create: `quick_env/env-updater/bundles/device-discovery/modules/h3c/module.yaml`
- Create: `quick_env/env-updater/bundles/device-discovery/modules/h3c/mysql/device_context_h3c.sql`
- Create: `quick_env/env-updater/bundles/device-discovery/modules/h3c/nacos/device_collection2_contracts.patch.yaml`
- Create: `quick_env/env-updater/bundles/snmp-observability/bundle.yaml`
- Create: `quick_env/env-updater/bundles/snmp-observability/modules/common/module.yaml`
- Create: `quick_env/env-updater/bundles/snmp-observability/modules/common/mysql/dashboard_templates.sql`
- Create: `quick_env/env-updater/bundles/snmp-observability/modules/common/record-rules/oneops_snmp_recording_rules.common.yaml`
- Create: `quick_env/env-updater/bundles/snmp-observability/modules/h3c/module.yaml`
- Create: `quick_env/env-updater/bundles/snmp-observability/modules/h3c/mysql/h3c_strategy_dashboard.sql`
- Create: `quick_env/env-updater/bundles/snmp-observability/modules/h3c/record-rules/oneops_snmp_recording_rules.h3c.yaml`
- Test: `quick_env/tests/test_env_updater_rollout.py`

- [ ] **Step 1: Write the failing rollout test for the first four modules**

Create `quick_env/tests/test_env_updater_rollout.py`:

```python
#!/usr/bin/env python3

import importlib.util
import pathlib
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "env-updater" / "lib" / "manifest.py"


def load_module():
    spec = importlib.util.spec_from_file_location("env_updater_manifest", str(MANIFEST))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class EnvUpdaterRolloutTest(unittest.TestCase):
    def test_first_phase_bundles_exist_and_declare_expected_surfaces(self):
        module = load_module()
        expected = {
            ROOT / "env-updater" / "bundles" / "device-discovery" / "modules" / "common" / "module.yaml": {
                "mysql": "required",
                "nacos": "required",
                "record_rule": "not_applicable",
            },
            ROOT / "env-updater" / "bundles" / "device-discovery" / "modules" / "h3c" / "module.yaml": {
                "mysql": "required",
                "nacos": "required",
                "record_rule": "not_applicable",
            },
            ROOT / "env-updater" / "bundles" / "snmp-observability" / "modules" / "common" / "module.yaml": {
                "mysql": "required",
                "nacos": "optional",
                "record_rule": "required",
            },
            ROOT / "env-updater" / "bundles" / "snmp-observability" / "modules" / "h3c" / "module.yaml": {
                "mysql": "required",
                "nacos": "optional",
                "record_rule": "optional",
            },
        }

        for path, surfaces in expected.items():
            row = module.load_module(path)
            self.assertEqual(surfaces, row["surfaces"])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
python3 -m unittest quick_env.tests.test_env_updater_rollout
```

Expected: FAIL because the phase-1 bundle and module files do not exist yet.

- [ ] **Step 3: Create the first bundle and module manifests**

Create `quick_env/env-updater/bundles/device-discovery/bundle.yaml`:

```yaml
api_version: quickenv/v2
kind: Bundle
name: device-discovery
surfaces:
  - mysql
  - nacos
  - record_rule
modules:
  - name: common
    path: modules/common/module.yaml
  - name: h3c
    path: modules/h3c/module.yaml
    depends_on:
      - common
```

Create `quick_env/env-updater/bundles/device-discovery/modules/common/module.yaml`:

```yaml
api_version: quickenv/v2
kind: Module
name: device-discovery/common
surfaces:
  mysql: required
  nacos: required
  record_rule: not_applicable
mysql:
  schema: UniOPS
  files:
    - mysql/device_v2_schema.sql
nacos:
  patches:
    - data_id: device_v2_candidate_engine
      file: nacos/device_v2_candidate_engine.patch.yaml
    - data_id: device_collection2_contracts
      file: nacos/device_collection2_contracts.patch.yaml
```

Create `quick_env/env-updater/bundles/device-discovery/modules/h3c/module.yaml`:

```yaml
api_version: quickenv/v2
kind: Module
name: device-discovery/h3c
surfaces:
  mysql: required
  nacos: required
  record_rule: not_applicable
mysql:
  schema: UniOPS
  files:
    - mysql/device_context_h3c.sql
nacos:
  patches:
    - data_id: device_collection2_contracts
      file: nacos/device_collection2_contracts.patch.yaml
```

Create `quick_env/env-updater/bundles/snmp-observability/bundle.yaml`:

```yaml
api_version: quickenv/v2
kind: Bundle
name: snmp-observability
surfaces:
  - mysql
  - nacos
  - record_rule
modules:
  - name: common
    path: modules/common/module.yaml
  - name: h3c
    path: modules/h3c/module.yaml
    depends_on:
      - common
```

Create `quick_env/env-updater/bundles/snmp-observability/modules/common/module.yaml`:

```yaml
api_version: quickenv/v2
kind: Module
name: snmp-observability/common
surfaces:
  mysql: required
  nacos: optional
  record_rule: required
mysql:
  schema: UniOPS
  files:
    - mysql/dashboard_templates.sql
record_rule:
  groups:
    - name: oneops_snmp_recording_rules
      file: record-rules/oneops_snmp_recording_rules.common.yaml
```

Create `quick_env/env-updater/bundles/snmp-observability/modules/h3c/module.yaml`:

```yaml
api_version: quickenv/v2
kind: Module
name: snmp-observability/h3c
surfaces:
  mysql: required
  nacos: optional
  record_rule: optional
mysql:
  schema: UniOPS
  files:
    - mysql/h3c_strategy_dashboard.sql
record_rule:
  groups:
    - name: oneops_snmp_recording_rules
      file: record-rules/oneops_snmp_recording_rules.h3c.yaml
```

- [ ] **Step 4: Add minimal module assets by extracting current seeds**

Create `quick_env/env-updater/bundles/device-discovery/modules/common/mysql/device_v2_schema.sql`:

```sql
CREATE TABLE IF NOT EXISTS `platform_task_result` (
  `id` varchar(36) NOT NULL,
  `task_id` varchar(64) NOT NULL,
  `status` varchar(32) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

Create `quick_env/env-updater/bundles/device-discovery/modules/common/nacos/device_v2_candidate_engine.patch.yaml`:

```yaml
prepared_fact_extractors:
  - id: h3c_comware_version
```

Create `quick_env/env-updater/bundles/device-discovery/modules/common/nacos/device_collection2_contracts.patch.yaml`:

```yaml
contracts:
  - key: common_mib
    datasets:
      - key: snmp_sys_descr
```

Create `quick_env/env-updater/bundles/device-discovery/modules/h3c/mysql/device_context_h3c.sql`:

```sql
INSERT INTO platform_devices_v2 (
  id, code, type, name, platform_code, status, created_at, updated_at
) VALUES (
  'H3C-SW-01', 'H3C-SW-01', 'device_v2', 'H3C-SW-01', 'PLT-H3C', 'active', NOW(3), NOW(3)
) ON DUPLICATE KEY UPDATE
  updated_at = NOW(3),
  status = VALUES(status);
```

Create `quick_env/env-updater/bundles/device-discovery/modules/h3c/nacos/device_collection2_contracts.patch.yaml`:

```yaml
contracts:
  - key: h3c_comware
    datasets:
      - key: cli_interface_brief
      - key: cli_lldp_neighbors
```

Create `quick_env/env-updater/bundles/snmp-observability/modules/common/mysql/dashboard_templates.sql`:

```sql
INSERT INTO grafana_dashboard (id, uid, title, created_at, updated_at)
VALUES ('GDB20260618000001', 'snmp_switch_root', 'SNMP Switch Root', NOW(3), NOW(3))
ON DUPLICATE KEY UPDATE
  updated_at = NOW(3),
  title = VALUES(title);
```

Create `quick_env/env-updater/bundles/snmp-observability/modules/common/record-rules/oneops_snmp_recording_rules.common.yaml`:

```yaml
name: oneops_snmp_recording_rules
interval: 30s
rules:
  - record: oneops:if_speed_bps
    expr: snmp_interface_ifSpeed
```

Create `quick_env/env-updater/bundles/snmp-observability/modules/h3c/mysql/h3c_strategy_dashboard.sql`:

```sql
INSERT INTO platform_teleabs_strategy (id, name, created_at, updated_at)
VALUES ('H3C-SNMP-STRATEGY', 'H3C SNMP Strategy', NOW(3), NOW(3))
ON DUPLICATE KEY UPDATE
  updated_at = NOW(3),
  name = VALUES(name);
```

Create `quick_env/env-updater/bundles/snmp-observability/modules/h3c/record-rules/oneops_snmp_recording_rules.h3c.yaml`:

```yaml
name: oneops_snmp_recording_rules
interval: 30s
rules:
  - record: oneops:cpu_usage_direct:ratio
    expr: (snmp_h3c_entity_state_cpu_usage / 100)
  - record: oneops:memory_usage_direct:ratio
    expr: (snmp_h3c_entity_state_memory_usage / 100)
```

- [ ] **Step 5: Run the rollout test to verify it passes**

Run:

```bash
python3 -m unittest quick_env.tests.test_env_updater_rollout
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add quick_env/env-updater/bundles quick_env/tests/test_env_updater_rollout.py
git commit -m "feat: add first quick env updater bundle set"
```

### Task 4: Introduce runtime-core wrappers and remove the first migrated sync path from default startup

**Files:**
- Create: `quick_env/runtime-core/up.sh`
- Create: `quick_env/runtime-core/down.sh`
- Create: `quick_env/runtime-core/status.sh`
- Modify: `quick_env/start.sh`
- Modify: `quick_env/manage.sh`
- Test: `quick_env/tests/test_start_bash_compat.py`

- [ ] **Step 1: Add a failing compatibility test for the new runtime-core wrappers**

Append to `quick_env/tests/test_start_bash_compat.py`:

```python
    def test_runtime_core_wrapper_scripts_exist(self):
        self.assertTrue((ROOT / "runtime-core" / "up.sh").exists())
        self.assertTrue((ROOT / "runtime-core" / "down.sh").exists())
        self.assertTrue((ROOT / "runtime-core" / "status.sh").exists())
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
python3 -m unittest quick_env.tests.test_start_bash_compat
```

Expected: FAIL because the new wrapper scripts do not exist yet.

- [ ] **Step 3: Create the wrapper scripts and gate the migrated syncs**

Create `quick_env/runtime-core/up.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
exec "${ROOT}/start.sh" "$@"
```

Create `quick_env/runtime-core/down.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
exec "${ROOT}/manage.sh" stop "$@"
```

Create `quick_env/runtime-core/status.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
exec "${ROOT}/manage.sh" status "$@"
```

Modify `quick_env/start.sh` so the old startup path no longer auto-runs the first migrated sync batch:

```bash
  refresh_runtime_bootstrap
  if [[ "${QUICK_ENV_V1_AUTO_SYNC:-false}" == "true" ]]; then
    sync_default_repository_records
    sync_snmp_switch_dashboard_seed_records
  else
    color_echo "blue" "已跳过首批迁移中的业务种子自动同步，请改用 env-updater"
  fi
  sync_task_runtime_contract_records
  sync_snmp_switch_device_context_records
  ensure_snmp_dashboard_runtime_records
```

Modify `quick_env/manage.sh` usage text to advertise the new updater path:

```bash
  ./manage.sh bootstrap-refresh --instance demo-a
  python3 ./env-updater/scripts/update.py plan snmp-observability/h3c
```

- [ ] **Step 4: Run the compatibility test to verify it passes**

Run:

```bash
python3 -m unittest quick_env.tests.test_start_bash_compat
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add \
  quick_env/runtime-core/up.sh \
  quick_env/runtime-core/down.sh \
  quick_env/runtime-core/status.sh \
  quick_env/start.sh \
  quick_env/manage.sh \
  quick_env/tests/test_start_bash_compat.py
git commit -m "refactor: add quick env runtime-core wrappers"
```

### Task 5: Document the phase-1 workflow and verify the end-to-end updater path

**Files:**
- Modify: `quick_env/README.md`
- Test: `quick_env/tests/test_validate_nacos_seed_runtime.py`
- Test: `quick_env/tests/test_seed_template_guard.py`

- [ ] **Step 1: Extend the README with runtime-core and env-updater usage**

Add this section to `quick_env/README.md`:

````md
## Phase 1: runtime-core / env-updater

`quick_env` 现在拆成两条主路径：

- `runtime-core`：只负责基础服务启动
- `env-updater`：只负责业务能力更新

示例：

```bash
./runtime-core/up.sh --instance demo-a --port-offset 100
python3 ./env-updater/scripts/update.py plan device-discovery/h3c
python3 ./env-updater/scripts/update.py apply device-discovery/h3c
python3 ./env-updater/scripts/update.py verify device-discovery/h3c
```
````

- [ ] **Step 2: Run the existing quick env validation tests**

Run:

```bash
python3 -m unittest \
  quick_env.tests.test_validate_nacos_seed_runtime \
  quick_env.tests.test_seed_template_guard
```

Expected: PASS.

- [ ] **Step 3: Add one updater smoke command to the README validation notes**

Add this smoke example under the new README section:

````md
针对现有 quick env v1 runtime，可先用 dry-run 预览：

```bash
python3 ./env-updater/scripts/update.py plan snmp-observability/h3c
```
````

- [ ] **Step 4: Re-run the validation tests**

Run:

```bash
python3 -m unittest \
  quick_env.tests.test_validate_nacos_seed_runtime \
  quick_env.tests.test_seed_template_guard
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add \
  quick_env/README.md
git commit -m "docs: describe quick env phase 1 runtime and updater flow"
```

---

## Self-Review

- Spec coverage:
  - `runtime-core` / `env-updater` 分层：Task 4, Task 5
  - bundle/module 模型：Task 1, Task 3
  - 三类 surface：Task 2, Task 3
  - 现有实例适配：Task 2
  - 第一阶段四个模块：Task 3
  - 迁出首批 `sync_*`：Task 4
- Placeholder scan:
  - 本计划没有使用 `TODO`、`TBD`、`implement later`。
  - 每个变更步骤都给了具体文件和命令。
- Type consistency:
  - 所有 manifest 都使用 `api_version` / `kind` / `name` / `surfaces`
  - 所有 surface 键统一为 `mysql` / `nacos` / `record_rule`
