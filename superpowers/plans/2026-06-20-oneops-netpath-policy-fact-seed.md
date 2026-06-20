# OneOPS NetPath Policy Fact Seed Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publish the first NetPath route/policy fact foundation into quick_env seed data without breaking existing DC2 collection profiles.

**Architecture:** Keep executable DC2 collection profiles conservative until policy processors exist. Add a first-class `netpath.fact_foundation` seed section to the Nacos template, validate it in quick_env seed tests, and document the active-vs-planned boundary. This lets quick_env carry the NetPath first-phase fact registry and quality-gate rules while implementation catches up.

**Tech Stack:** YAML Nacos seed files, Python unittest, quick_env validation helpers, superpowers docs.

---

## File Map

- Modify `quick_env/init-configs/nacos/cipher-aes-start-config.yaml`
  - Add `netpath.fact_foundation` with first-phase fact families, device-type requirements, and confidence gates.
  - Do not add ACL/NAT/PBR policy datasets to active `device_collection2.collection_profiles` until processors exist.
- Modify `quick_env/scripts/validate_nacos_seed_runtime.py`
  - Validate that the rendered `cipher-aes-start-config` carries the NetPath fact foundation registry.
- Modify `quick_env/tests/test_validate_nacos_seed_runtime.py`
  - Add failing tests for missing fact families and policy-gate mode.
- Modify `quick_env/README.md`
  - Document how quick_env seeds NetPath fact requirements and why some policy facts are initially confidence gates instead of active DC2 datasets.

## Task 1: Add Validation For NetPath Fact Foundation Seed

**Files:**

- Modify `quick_env/tests/test_validate_nacos_seed_runtime.py`
- Modify `quick_env/scripts/validate_nacos_seed_runtime.py`

- [x] **Step 1: Write failing validation tests**

Add a test that passes a minimal valid `netpath.fact_foundation` block and expects no errors, and another test that omits `nat_rule` and expects a precise error:

```python
    def test_accepts_netpath_fact_foundation_seed(self):
        module = load_module()

        configs = valid_seed_configs()
        configs["cipher-aes-start-config"] += """
netpath:
  fact_foundation:
    version: "2026-06-20.policy-fact-foundation-v1"
    required_fact_families:
      - device_identity
      - interface
      - interface_ip
      - topology_neighbor
      - route_table
      - security_zone_binding
      - acl_rule
      - firewall_policy
      - nat_rule
      - pbr_rule
      - address_object
      - service_object
      - policy_parser_diagnostic
    confidence_gate:
      missing_policy_facts: block
      missing_nat_facts_when_nat_may_apply: block
      missing_pbr_facts_when_pbr_may_apply: block
      unsupported_policy_parser: block
    device_type_requirements:
      firewall:
        required:
          - device_identity
          - interface
          - interface_ip
          - security_zone_binding
          - route_table
          - firewall_policy
          - nat_rule
          - address_object
          - service_object
          - policy_parser_diagnostic
      network:
        required:
          - device_identity
          - interface
          - interface_ip
          - topology_neighbor
          - route_table
      server:
        required:
          - device_identity
          - interface
          - interface_ip
          - server_route
"""

        errors = module.validate_nacos_seed_configs(configs, seed_env())

        self.assertEqual([], errors)

    def test_reports_missing_netpath_policy_fact_family(self):
        module = load_module()

        configs = valid_seed_configs()
        configs["cipher-aes-start-config"] += """
netpath:
  fact_foundation:
    version: "2026-06-20.policy-fact-foundation-v1"
    required_fact_families:
      - device_identity
      - interface
      - interface_ip
      - topology_neighbor
      - route_table
      - firewall_policy
      - pbr_rule
      - address_object
      - service_object
      - policy_parser_diagnostic
    confidence_gate:
      missing_policy_facts: block
      missing_nat_facts_when_nat_may_apply: block
      missing_pbr_facts_when_pbr_may_apply: block
      unsupported_policy_parser: block
"""

        errors = module.validate_nacos_seed_configs(configs, seed_env())

        self.assertIn("netpath.fact_foundation.required_fact_families must include nat_rule", errors)
```

- [x] **Step 2: Run the tests and confirm RED**

Run:

```bash
cd quick_env
python3 tests/test_validate_nacos_seed_runtime.py
```

Expected:

```text
FAIL because valid_seed_configs, seed_env, and netpath fact foundation validation do not exist yet
```

- [x] **Step 3: Add helper fixtures to the test file**

Add:

```python
def seed_env():
    return {
        "ONEOPS_CORE_SERVER_PORT": "28080",
        "ONEOPS_CORE_BIDI_PORT": "27070",
    }


def valid_seed_configs():
    return {
        "cipher-aes-start-config": """
server:
  port: 28080
bidi:
  listen_addr: ":27070"
device_collection2:
  contract_nacos:
    enabled: true
    data_id: device_collection2_contracts
    group: DEFAULT_GROUP
""",
        "device_collection2_contracts": """
contracts:
  - key: cisco_ios
    datasets:
      - key: cli_lldp_neighbors
""",
        "device_v2_candidate_engine": """
prepared_fact_extractors:
  - id: cisco_ios_version
""",
    }
```

- [x] **Step 4: Implement validator checks**

In `validate_nacos_seed_runtime.py`, add:

```python
REQUIRED_NETPATH_FACT_FAMILIES = [
    "device_identity",
    "interface",
    "interface_ip",
    "topology_neighbor",
    "route_table",
    "security_zone_binding",
    "acl_rule",
    "firewall_policy",
    "nat_rule",
    "pbr_rule",
    "address_object",
    "service_object",
    "policy_parser_diagnostic",
]

REQUIRED_NETPATH_CONFIDENCE_GATES = {
    "missing_policy_facts": "block",
    "missing_nat_facts_when_nat_may_apply": "block",
    "missing_pbr_facts_when_pbr_may_apply": "block",
    "unsupported_policy_parser": "block",
}
```

Then add a helper:

```python
def validate_netpath_fact_foundation(core, errors):
    netpath = core.get("netpath") if isinstance(core.get("netpath"), dict) else {}
    foundation = netpath.get("fact_foundation") if isinstance(netpath.get("fact_foundation"), dict) else {}
    if not foundation:
        errors.append("netpath.fact_foundation must be defined")
        return

    families = foundation.get("required_fact_families")
    if not isinstance(families, list):
        errors.append("netpath.fact_foundation.required_fact_families must be a list")
        families = []
    family_set = {str(item).strip() for item in families if str(item).strip()}
    for family in REQUIRED_NETPATH_FACT_FAMILIES:
        if family not in family_set:
            errors.append("netpath.fact_foundation.required_fact_families must include {}".format(family))

    gates = foundation.get("confidence_gate") if isinstance(foundation.get("confidence_gate"), dict) else {}
    for key, expected in REQUIRED_NETPATH_CONFIDENCE_GATES.items():
        if gates.get(key) != expected:
            errors.append("netpath.fact_foundation.confidence_gate.{} must be {}".format(key, expected))
```

Call it from `validate_nacos_seed_configs()` after DC2 contract validation:

```python
    validate_netpath_fact_foundation(core, errors)
```

- [x] **Step 5: Run tests and confirm GREEN**

Run:

```bash
cd quick_env
python3 tests/test_validate_nacos_seed_runtime.py
```

Expected:

```text
OK
```

## Task 2: Seed NetPath Fact Foundation In Nacos Template

**Files:**

- Modify `quick_env/init-configs/nacos/cipher-aes-start-config.yaml`

- [x] **Step 1: Add the seed block**

Append near the existing `netpath` or before `obsflow` if no NetPath block exists:

```yaml
netpath:
  fact_foundation:
    version: "2026-06-20.policy-fact-foundation-v1"
    required_fact_families:
      - device_identity
      - interface
      - interface_ip
      - topology_neighbor
      - route_table
      - security_zone_binding
      - acl_rule
      - firewall_policy
      - nat_rule
      - pbr_rule
      - address_object
      - service_object
      - policy_parser_diagnostic
    confidence_gate:
      missing_policy_facts: block
      missing_nat_facts_when_nat_may_apply: block
      missing_pbr_facts_when_pbr_may_apply: block
      unsupported_policy_parser: block
    device_type_requirements:
      firewall:
        required:
          - device_identity
          - interface
          - interface_ip
          - security_zone_binding
          - route_table
          - firewall_policy
          - nat_rule
          - address_object
          - service_object
          - policy_parser_diagnostic
        optional:
          - topology_neighbor
          - acl_rule
          - pbr_rule
      network:
        required:
          - device_identity
          - interface
          - interface_ip
          - topology_neighbor
          - route_table
        optional:
          - acl_rule
          - pbr_rule
          - mac_table_entry
          - arp_entry
      server:
        required:
          - device_identity
          - interface
          - interface_ip
          - server_route
        optional: []
    active_collection_boundary:
      policy_families_are_seeded_as_requirements: true
      add_policy_datasets_to_dc2_profiles_only_after_processors_exist: true
```

- [x] **Step 2: Validate YAML and seed rules**

Run:

```bash
cd quick_env
python3 - <<'PY'
from pathlib import Path
import yaml
path = Path("init-configs/nacos/cipher-aes-start-config.yaml")
yaml.safe_load(path.read_text(encoding="utf-8"))
print("YAML OK")
PY
python3 tests/test_validate_nacos_seed_runtime.py
```

Expected:

```text
YAML OK
OK
```

## Task 3: Document Quick Env Seed Boundary

**Files:**

- Modify `quick_env/README.md`

- [x] **Step 1: Add README section**

Add a short section near the DC2 seed documentation:

```markdown
### NetPath fact foundation seed

`quick_env/init-configs/nacos/cipher-aes-start-config.yaml` includes
`netpath.fact_foundation`. This seed publishes the first-phase NetPath fact
registry for route, firewall policy, ACL, NAT, PBR, zone binding, address
objects, service objects, and parser diagnostics.

The policy families are seeded as requirements and quality gates first. Do not
add ACL/NAT/PBR/firewall-policy dataset keys to active
`device_collection2.collection_profiles` until matching DC2 processors and
fact issue handling exist. Otherwise quick_env collection may turn healthy
devices into partial or blocked runs.
```

- [x] **Step 2: Run seed template guard**

Run:

```bash
cd quick_env
python3 tests/test_seed_template_guard.py
python3 tests/test_validate_nacos_seed_runtime.py
```

Expected:

```text
OK
OK
```


Execution note:

```text
python3 tests/test_seed_template_guard.py currently has unrelated SNMP seed guard failures in existing checks for dashboard/shared-target migrations and root L2 SQL text. The NetPath seed validation path passed via direct YAML assertions and tests/test_validate_nacos_seed_runtime.py.
```

## Self-Review

Spec coverage:

- NetPath policy fact families are represented in quick_env seed data.
- Quick env validation fails if required policy facts are missing.
- Policy facts are not added to active collection profiles before processors exist.
- README warns future workers not to poison active collection profiles prematurely.

Placeholder scan:

- No `TBD`, `TODO`, `implement later`, or `fill in details` entries are allowed.

Type consistency:

- `required_fact_families`, `confidence_gate`, `device_type_requirements`, and `active_collection_boundary` are YAML keys under `netpath.fact_foundation`.
