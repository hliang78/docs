# Current Netlink Completion And Ansible Task Assetization MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** First finish and release the current netlink-native task-center changes, then start the Ansible task assetization MVP from `/OneOPS/docs/superpowers/ANSIBLE_TASK_ASSETIZATION_MVP_DESIGN_20260606.md`.

**Architecture:** Treat the current netlink work as a release hardening lane: idempotent template import, platform noop update semantics, task overview metadata preservation, and agent-native network configuration backup routing. Huawei VRP/USG, H3C Comware/SecPath, Maipu MyPower, and Cisco IOS/NX-OS/ASA backup tasks should run through the agent `network_config_backup` runner; unsupported device families remain on the Ansible backup path. After that, implement the assetization MVP in platform-owned layers: task template contract metadata, Ansible target precheck, device fanout reuse, artifact projection, and device config backup indexes.

**Tech Stack:** Go, GORM, Gin, Python unittest, Bash import scripts, quick_env seed repository, OneOps platform task center, existing runtime artifact APIs, existing `ResolveAnsibleDeviceProfile`.

---

## File Structure

### Current completion lane

- Modify: `/OneOPS/quick_env/init-configs/gitea/source-repo/templates/import-variable-sets.sh`
  - Responsibility: import variable sets idempotently, avoid duplicate creation when old platform returns "not found" for an unchanged update.
- Modify: `/OneOPS/quick_env/init-configs/gitea/source-repo/templates/import-to-oneops.sh`
  - Responsibility: import task templates idempotently with first-match duplicate handling and readable-record fallback.
- Create: `/OneOPS/quick_env/tests/test_template_import_scripts.py`
  - Responsibility: regression tests for stale update IDs, duplicate list rows, and readable noop-update fallback.
- Modify: `/OneOPS/OneOps/app/platform/service/impl/task_template_v2.go`
  - Responsibility: treat `RowsAffected=0` update as success when the scoped template row exists.
- Modify: `/OneOPS/OneOps/app/platform/service/impl/variable_set_v2.go`
  - Responsibility: treat `RowsAffected=0` update as success when the scoped variable set row exists.
- Modify: `/OneOPS/OneOps/app/platform/service/impl/task_catalog_v2_test.go`
  - Responsibility: regression tests for noop update semantics.
- Modify: `/OneOPS/OneOps/app/platform/service/impl/oneops_bidi_service.go`
  - Responsibility: preserve `template_id` when a pending task overview is promoted to a real controller row.
- Modify: `/OneOPS/OneOps/app/platform/service/impl/oneops_bidi_task_overview_test.go`
  - Responsibility: regression test for `template_id` preservation.
- Modify: `/OneOPS/netlink/backup/backup.go`
  - Responsibility: support Cisco IOS/NX-OS/ASA aliases, default commands, and mode config files for native backup.
- Modify: `/OneOPS/netlink/backup/backup_test.go`
  - Responsibility: regression tests for Cisco native backup aliases and default commands.
- Modify: `/OneOPS/netlink/cmd/netlink-backup/main_test.go`
  - Responsibility: CLI-level alias/default-command coverage for Cisco modes.
- Modify: `/OneOPS/OneOps/app/platform/pkg/deviceexecprofile/ansible.go`
  - Responsibility: resolve Huawei USG, H3C SecPath, Maipu MyPower, and Cisco ASA vendor families.
- Modify: `/OneOPS/OneOps/app/platform/pkg/deviceexecprofile/ansible_test.go`
  - Responsibility: regression coverage for the newly resolved vendor families.
- Modify: `/OneOPS/OneOps/app/platform/service/impl/task_device_fanout.go`
  - Responsibility: route supported network configuration backup child tasks to `network_config_backup` agent runner while leaving unsupported families on Ansible.
- Modify: `/OneOPS/OneOps/app/platform/service/impl/task_device_fanout_test.go`
  - Responsibility: regression coverage for native child envelope conversion and Ansible fallback.
- Modify: `/OneOPS/OneOps/app/platform/service/impl/scheduled_task_v2.go`
  - Responsibility: allow `device_codes` on `network_config_backup` scheduled tasks.
- Modify: `/OneOPS/quick_env/init-configs/gitea/source-repo/templates/task-template-catalog.json`
  - Responsibility: seed network backup templates with agent execution defaults and Cisco support text.
- Modify: `/OneOPS/quick_env/init-configs/gitea/source-repo/ansible/network-config-backup-netlink/site.yml`
  - Responsibility: keep the legacy netlink CLI wrapper aligned with native Cisco mode support.
- Modify: `/OneOPS/quick_env/tests/test_network_playbooks.py`
  - Responsibility: catalog/playbook regression tests for Cisco and agent defaults.

### Assetization MVP lane

- Modify: `/OneOPS/OneOps/app/platform/platform_model/platform_task_template.go`
  - Responsibility: add task asset contract metadata fields.
- Modify: `/OneOPS/OneOps/app/platform/dto/task_template.go`
  - Responsibility: expose contract metadata on create, update, and response DTOs.
- Modify: `/OneOPS/OneOps/app/platform/service/impl/task_template_v2.go`
  - Responsibility: persist and return contract metadata.
- Modify: `/OneOPS/OneOps/app/platform/service/impl/task_v2_test_helpers_test.go`
  - Responsibility: add test-table columns for contract metadata.
- Modify: `/OneOPS/quick_env/init-configs/gitea/source-repo/templates/task-template-catalog.json`
  - Responsibility: seed `task-center-ansible-network-config-backup` as an asset with contract metadata.
- Create: `/OneOPS/quick_env/init-configs/gitea/source-repo/ansible/network-config-backup/oneops.contract.json`
  - Responsibility: define the runtime contract for the network config backup asset.
- Modify: `/OneOPS/quick_env/init-configs/gitea/source-repo/templates/import-to-oneops.sh`
  - Responsibility: import `contract_json`, `asset_category`, `risk_level`, and `lifecycle_status`.
- Create: `/OneOPS/OneOps/app/platform/dto/task_asset_precheck.go`
  - Responsibility: request and response DTOs for Ansible task asset precheck.
- Create: `/OneOPS/OneOps/app/platform/service/i_task_asset_precheck.go`
  - Responsibility: interface boundary for the precheck service.
- Create: `/OneOPS/OneOps/app/platform/service/impl/task_asset_precheck.go`
  - Responsibility: load template contract, resolve devices, and produce ready/blocked rows.
- Create: `/OneOPS/OneOps/app/platform/service/impl/task_asset_precheck_test.go`
  - Responsibility: precheck behavior tests for ready, missing device, missing address, missing credential, and unsupported vendor family.
- Modify: `/OneOPS/OneOps/app/platform/api/task_template.go`
  - Responsibility: expose `POST /task-assets/:template_id/ansible/precheck`.
- Modify: `/OneOPS/OneOps/app/platform/router/platform_bidi.go`
  - Responsibility: register the precheck route in bidi platform routing.
- Modify: `/OneOPS/OneOps/app/platform/router/platform.go`
  - Responsibility: register the precheck route in legacy platform routing if the legacy route set is still active.
- Create: `/OneOPS/OneOps/app/platform/platform_model/device_config_backup.go`
  - Responsibility: store device config backup projection records.
- Create: `/OneOPS/OneOps/app/platform/service/impl/device_config_backup_projection.go`
  - Responsibility: parse runtime artifacts and summary JSON into backup records.
- Create: `/OneOPS/OneOps/app/platform/service/impl/device_config_backup_projection_test.go`
  - Responsibility: verify cfg artifacts are sensitive and summary JSON creates device-level records.
- Modify: `/OneOPS/OneOps/app/platform/api/task_api.go`
  - Responsibility: add parent task target summary once child task artifacts can be projected.
- Modify: `/OneOPS/OneOps/app/platform/api/task_api_test.go`
  - Responsibility: target summary API tests.
- Create: `/OneOPS/OneOps/app/platform/api/device_config_backup.go`
  - Responsibility: expose device config backup history API.
- Create: `/OneOPS/OneOps/app/platform/api/device_config_backup_test.go`
  - Responsibility: verify device backup history response.

---

## Task 0: Finish Current Netlink Changes

**Files:**
- Modify: `/OneOPS/quick_env/init-configs/gitea/source-repo/templates/import-variable-sets.sh`
- Modify: `/OneOPS/quick_env/init-configs/gitea/source-repo/templates/import-to-oneops.sh`
- Create: `/OneOPS/quick_env/tests/test_template_import_scripts.py`
- Modify: `/OneOPS/OneOps/app/platform/service/impl/task_template_v2.go`
- Modify: `/OneOPS/OneOps/app/platform/service/impl/variable_set_v2.go`
- Modify: `/OneOPS/OneOps/app/platform/service/impl/task_catalog_v2_test.go`
- Modify: `/OneOPS/OneOps/app/platform/service/impl/oneops_bidi_service.go`
- Modify: `/OneOPS/OneOps/app/platform/service/impl/oneops_bidi_task_overview_test.go`
- Modify: `/OneOPS/netlink/backup/backup.go`
- Modify: `/OneOPS/netlink/backup/backup_test.go`
- Modify: `/OneOPS/netlink/cmd/netlink-backup/main_test.go`
- Modify: `/OneOPS/OneOps/app/platform/pkg/deviceexecprofile/ansible.go`
- Modify: `/OneOPS/OneOps/app/platform/pkg/deviceexecprofile/ansible_test.go`
- Modify: `/OneOPS/OneOps/app/platform/service/impl/task_device_fanout.go`
- Modify: `/OneOPS/OneOps/app/platform/service/impl/task_device_fanout_test.go`
- Modify: `/OneOPS/OneOps/app/platform/service/impl/scheduled_task_v2.go`
- Modify: `/OneOPS/quick_env/init-configs/gitea/source-repo/templates/task-template-catalog.json`
- Modify: `/OneOPS/quick_env/init-configs/gitea/source-repo/ansible/network-config-backup-netlink/site.yml`
- Modify: `/OneOPS/quick_env/tests/test_network_playbooks.py`

- [ ] **Step 1: Confirm only intended files are staged**

Run:

```bash
git -C /OneOPS/quick_env status --short
git -C /OneOPS/OneOps status --short
```

Expected:

```text
quick_env shows only the two import scripts and tests/test_template_import_scripts.py for this lane.
OneOps may show unrelated user changes, but this lane only stages task_template_v2.go, variable_set_v2.go, task_catalog_v2_test.go, oneops_bidi_service.go, and oneops_bidi_task_overview_test.go.
```

- [ ] **Step 2: Run current lane verification**

Run:

```bash
python3 -m unittest quick_env.tests.test_network_playbooks quick_env.tests.test_template_import_scripts
bash -n quick_env/init-configs/gitea/source-repo/templates/import-variable-sets.sh
bash -n quick_env/init-configs/gitea/source-repo/templates/import-to-oneops.sh
go test ./backup ./cmd/netlink-backup -count=1
go test ./app/platform/pkg/deviceexecprofile -count=1
go test ./app/platform/service/impl -run 'Test(BuildChildExecutionEnvelopeForDevice|ResolveTaskDeviceExecutionTarget|BuildTaskDeviceInventoryContent|TaskCreationServiceV2|HandleReportTaskOverview|HandleTaskTopicEvent|TaskQueryServiceV2|TaskTemplateServiceV2|VariableSetServiceV2)' -count=1
git -C quick_env diff --check
git -C OneOps diff --check
```

Run netlink Go tests from `/OneOPS/netlink`; run OneOps Go tests from `/OneOPS/OneOps`. Run the Python and Bash commands from `/OneOPS`.

Expected:

```text
Python unittest: OK
Bash syntax checks: exit 0
Go test: ok github.com/netxops/OneOps/app/platform/service/impl
diff --check: no output
```

- [ ] **Step 3: Re-run real template imports against local platform**

Run:

```bash
tmp=$(mktemp)
bash /OneOPS/quick_env/init-configs/gitea/source-repo/templates/import-variable-sets.sh >"$tmp" 2>&1
python3 - "$tmp" <<'PY'
import sys
text = open(sys.argv[1], encoding="utf-8", errors="replace").read()
assert "variable set import completed" in text
assert "creating variable set:" not in text
assert "update target missing, creating variable set instead:" not in text
print("variable import idempotent")
PY
rm -f "$tmp"

tmp=$(mktemp)
bash /OneOPS/quick_env/init-configs/gitea/source-repo/templates/import-to-oneops.sh >"$tmp" 2>&1
python3 - "$tmp" <<'PY'
import sys
text = open(sys.argv[1], encoding="utf-8", errors="replace").read()
assert "task template import completed" in text
assert "creating template:" not in text
assert "update target missing, creating template instead:" not in text
print("template import idempotent")
PY
rm -f "$tmp"
```

Expected:

```text
variable import idempotent
template import idempotent
```

- [ ] **Step 4: Commit quick_env current lane**

Run:

```bash
git -C /OneOPS/quick_env add \
  init-configs/gitea/source-repo/templates/import-variable-sets.sh \
  init-configs/gitea/source-repo/templates/import-to-oneops.sh \
  tests/test_template_import_scripts.py
git -C /OneOPS/quick_env commit -m "fix: make task template imports idempotent"
```

Expected:

```text
[main <sha>] fix: make task template imports idempotent
```

- [ ] **Step 5: Commit OneOps current lane without unrelated user changes**

Run:

```bash
git -C /OneOPS/OneOps add \
  app/platform/service/impl/task_template_v2.go \
  app/platform/service/impl/variable_set_v2.go \
  app/platform/service/impl/task_catalog_v2_test.go \
  app/platform/service/impl/oneops_bidi_service.go \
  app/platform/service/impl/oneops_bidi_task_overview_test.go
git -C /OneOPS/OneOps diff --cached --name-only
git -C /OneOPS/OneOps commit -m "fix: keep task template updates idempotent"
```

Expected cached names:

```text
app/platform/service/impl/oneops_bidi_service.go
app/platform/service/impl/oneops_bidi_task_overview_test.go
app/platform/service/impl/task_catalog_v2_test.go
app/platform/service/impl/task_template_v2.go
app/platform/service/impl/variable_set_v2.go
```

- [ ] **Step 6: Push current lane commits**

Run:

```bash
git -C /OneOPS/quick_env push
git -C /OneOPS/OneOps push
```

Expected:

```text
Both repositories push the new commit to their configured upstream.
```

- [ ] **Step 7: Redeploy platform service before relying on noop update fix**

Run from `/OneOPS/quick_env`:

```bash
compose_cmd="$(bash -lc 'source /OneOPS/quick_env/lib/runtime_helpers.sh && detect_docker_compose')"
$compose_cmd ps
```

Then restart the platform container/service used by this environment. If quick_env is the active runtime, run:

```bash
cd /OneOPS/quick_env
$compose_cmd up -d --build oneops
```

Expected:

```text
The OneOps platform container is recreated or restarted and becomes healthy.
```

- [ ] **Step 8: Validate native Maipu backup once after redeploy**

Run the existing task trigger path for the native template:

```bash
python3 - <<'PY'
print("Use the existing OneOps task creation API with template task-center-native-network-config-backup-netlink, target 172.21.253.9, and an authorized X-Auth-Token header.")
print("Do not print credential material in terminal output.")
PY
```

Expected:

```text
Task app_type=network_config_backup
run_on_agent=true
No Ansible playbook path in diagnostic output
Runtime artifacts include one cfg and one json summary
```

---

## Task 1: Persist Task Asset Contract Metadata

**Files:**
- Modify: `/OneOPS/OneOps/app/platform/platform_model/platform_task_template.go`
- Modify: `/OneOPS/OneOps/app/platform/dto/task_template.go`
- Modify: `/OneOPS/OneOps/app/platform/service/impl/task_template_v2.go`
- Modify: `/OneOPS/OneOps/app/platform/service/impl/task_catalog_v2_test.go`
- Modify: `/OneOPS/OneOps/app/platform/service/impl/task_v2_test_helpers_test.go`

- [ ] **Step 1: Write failing DTO/service round-trip test**

Add this test to `/OneOPS/OneOps/app/platform/service/impl/task_catalog_v2_test.go`:

```go
func TestTaskTemplateServiceV2_CreateAndGet_RoundTripsAssetContract(t *testing.T) {
	db := newTaskV2TestDB(t)
	svc := NewTaskTemplateServiceV2(zap.NewNop(), types.DBTypeMySQL(db))

	created, err := svc.CreateTaskTemplate(context.Background(), &dto.TaskTemplateCreateReq{
		Name:            "network-config-backup-asset",
		AppType:         "ansible",
		PlaybookPath:    "ansible/network-config-backup/site.yml",
		ContractJSON:    `{"apiVersion":"oneops.runtime/v1","kind":"ansible_task_contract","name":"network-config-backup"}`,
		AssetCategory:   "network_config_backup",
		RiskLevel:       "low",
		LifecycleStatus: "active",
	})
	if err != nil {
		t.Fatalf("CreateTaskTemplate failed: %v", err)
	}

	got, err := svc.GetTaskTemplate(context.Background(), created.ID)
	if err != nil {
		t.Fatalf("GetTaskTemplate failed: %v", err)
	}
	if got == nil || got.ContractJSON == "" || got.AssetCategory != "network_config_backup" || got.RiskLevel != "low" || got.LifecycleStatus != "active" {
		t.Fatalf("expected asset contract metadata to round-trip, got %+v", got)
	}
}
```

- [ ] **Step 2: Run test and verify it fails**

Run from `/OneOPS/OneOps`:

```bash
go test ./app/platform/service/impl -run TestTaskTemplateServiceV2_CreateAndGet_RoundTripsAssetContract -count=1
```

Expected:

```text
FAIL because TaskTemplateCreateReq, TaskTemplateResp, or PlatformTaskTemplate does not expose the new fields.
```

- [ ] **Step 3: Add model fields**

Add to `PlatformTaskTemplate` in `/OneOPS/OneOps/app/platform/platform_model/platform_task_template.go`:

```go
ContractJSON    string `gorm:"type:text;comment:任务资产运行契约 JSON"`
AssetCategory   string `gorm:"type:varchar(64);index;comment:任务资产分类"`
RiskLevel       string `gorm:"type:varchar(32);comment:风险等级"`
LifecycleStatus string `gorm:"type:varchar(32);comment:生命周期状态"`
```

- [ ] **Step 4: Add DTO fields**

Add these fields to `TaskTemplateCreateReq`, `TaskTemplateUpdateReq`, and `TaskTemplateResp` in `/OneOPS/OneOps/app/platform/dto/task_template.go`:

```go
ContractJSON    string `json:"contract_json,omitempty"`
AssetCategory   string `json:"asset_category,omitempty"`
RiskLevel       string `json:"risk_level,omitempty"`
LifecycleStatus string `json:"lifecycle_status,omitempty"`
```

- [ ] **Step 5: Persist fields in service**

In `/OneOPS/OneOps/app/platform/service/impl/task_template_v2.go`, add the four fields to create, update, and response mapping:

```go
ContractJSON:    req.ContractJSON,
AssetCategory:   req.AssetCategory,
RiskLevel:       req.RiskLevel,
LifecycleStatus: req.LifecycleStatus,
```

and in update map:

```go
"contract_json":     req.ContractJSON,
"asset_category":    req.AssetCategory,
"risk_level":        req.RiskLevel,
"lifecycle_status":  req.LifecycleStatus,
```

- [ ] **Step 6: Extend SQLite test schema**

Add these columns to the `platform_task_template` table in `/OneOPS/OneOps/app/platform/service/impl/task_v2_test_helpers_test.go`:

```sql
contract_json TEXT,
asset_category TEXT,
risk_level TEXT,
lifecycle_status TEXT
```

- [ ] **Step 7: Run tests**

Run:

```bash
gofmt -w app/platform/platform_model/platform_task_template.go app/platform/dto/task_template.go app/platform/service/impl/task_template_v2.go app/platform/service/impl/task_catalog_v2_test.go app/platform/service/impl/task_v2_test_helpers_test.go
go test ./app/platform/service/impl -run 'TestTaskTemplateServiceV2' -count=1
```

Expected:

```text
ok github.com/netxops/OneOps/app/platform/service/impl
```

---

## Task 2: Seed Network Config Backup Contract

**Files:**
- Create: `/OneOPS/quick_env/init-configs/gitea/source-repo/ansible/network-config-backup/oneops.contract.json`
- Modify: `/OneOPS/quick_env/init-configs/gitea/source-repo/templates/task-template-catalog.json`
- Modify: `/OneOPS/quick_env/init-configs/gitea/source-repo/templates/import-to-oneops.sh`
- Modify: `/OneOPS/quick_env/tests/test_template_import_scripts.py`

- [ ] **Step 1: Write failing import script test for contract metadata**

Extend the fake handler in `/OneOPS/quick_env/tests/test_template_import_scripts.py` to capture POST/PUT payloads:

```python
ImportScriptHandler.payloads = []
```

In `do_POST` and `do_PUT`, after reading the request body:

```python
body = self.rfile.read(int(self.headers.get("Content-Length", "0")))
try:
    self.__class__.payloads.append(json.loads(body.decode("utf-8")))
except Exception:
    self.__class__.payloads.append({})
```

Add test:

```python
def test_task_template_import_sends_asset_contract_fields(self):
    ImportScriptHandler.mode = "templates"
    result, _calls = self.run_script(
        "import-to-oneops.sh",
        {
            "templates": [
                {
                    "name": "native-template",
                    "description": "native template",
                    "app_type": "ansible",
                    "contract_json": "{\"kind\":\"ansible_task_contract\"}",
                    "asset_category": "network_config_backup",
                    "risk_level": "low",
                    "lifecycle_status": "active",
                }
            ]
        },
    )
    self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
    self.assertTrue(ImportScriptHandler.payloads)
    payload = ImportScriptHandler.payloads[-1]
    self.assertEqual(payload["contract_json"], "{\"kind\":\"ansible_task_contract\"}")
    self.assertEqual(payload["asset_category"], "network_config_backup")
    self.assertEqual(payload["risk_level"], "low")
    self.assertEqual(payload["lifecycle_status"], "active")
```

- [ ] **Step 2: Run test and verify it fails**

Run:

```bash
python3 -m unittest quick_env.tests.test_template_import_scripts.TemplateImportScriptTest.test_task_template_import_sends_asset_contract_fields
```

Expected:

```text
FAIL because import-to-oneops.sh drops the new fields.
```

- [ ] **Step 3: Update import script allowed keys**

Add these keys to the Python key list in `/OneOPS/quick_env/init-configs/gitea/source-repo/templates/import-to-oneops.sh`:

```python
"contract_json",
"asset_category",
"risk_level",
"lifecycle_status",
```

- [ ] **Step 4: Create contract file**

Create `/OneOPS/quick_env/init-configs/gitea/source-repo/ansible/network-config-backup/oneops.contract.json`:

```json
{
  "apiVersion": "oneops.runtime/v1",
  "kind": "ansible_task_contract",
  "name": "network-config-backup",
  "script": {
    "type": "ansible",
    "entrypoint": "ansible/network-config-backup/site.yml"
  },
  "target": {
    "device_types": ["switch", "router", "firewall", "load_balancer"],
    "vendor_families": ["cisco_ios", "cisco_nxos", "huawei_ce", "h3c_cli", "f5_bigip", "maipu_mypower"],
    "access_planes": ["in_band", "out_band"],
    "requires_address": true
  },
  "inventory": {
    "required_host_vars": ["ansible_host", "vendor_family"],
    "optional_host_vars": ["ansible_connection", "ansible_network_os", "ansible_ssh_common_args", "ansible_command_timeout"],
    "forbidden_host_vars": ["ansible_user", "ansible_password", "ansible_ssh_pass", "ansible_become_password", "ansible_ssh_private_key_file", "token", "private_key"]
  },
  "credential": {
    "required": true,
    "source": "credential_ref",
    "forbid_inline_secret": true
  },
  "runtime": {
    "read_only": true,
    "idempotent": true,
    "safe_for_schedule": true,
    "supports_check_mode": false
  },
  "outputs": {
    "artifacts": [
      {"path": "network-backups/*.cfg", "kind": "text", "sensitive": true},
      {"path": "network-config-backup-*.json", "kind": "json", "sensitive": false}
    ],
    "manifest": "ONEOPS_ARTIFACT_MANIFEST"
  },
  "risk": {
    "level": "low",
    "approval_required": false
  }
}
```

- [ ] **Step 5: Embed contract metadata into catalog**

In `/OneOPS/quick_env/init-configs/gitea/source-repo/templates/task-template-catalog.json`, update `task-center-ansible-network-config-backup`:

```json
"contract_json": "{\"apiVersion\":\"oneops.runtime/v1\",\"kind\":\"ansible_task_contract\",\"name\":\"network-config-backup\"}",
"asset_category": "network_config_backup",
"risk_level": "low",
"lifecycle_status": "active"
```

Keep this as compact JSON for the seed catalog. The full file remains the source contract in the script repository.

- [ ] **Step 6: Run quick_env tests**

Run:

```bash
python3 -m unittest quick_env.tests.test_network_playbooks quick_env.tests.test_template_import_scripts
bash -n quick_env/init-configs/gitea/source-repo/templates/import-to-oneops.sh
```

Expected:

```text
unittest OK
bash syntax check exit 0
```

---

## Task 3: Add Ansible Task Asset Precheck Service

**Files:**
- Create: `/OneOPS/OneOps/app/platform/dto/task_asset_precheck.go`
- Create: `/OneOPS/OneOps/app/platform/service/i_task_asset_precheck.go`
- Create: `/OneOPS/OneOps/app/platform/service/impl/task_asset_precheck.go`
- Create: `/OneOPS/OneOps/app/platform/service/impl/task_asset_precheck_test.go`
- Modify: `/OneOPS/OneOps/app/platform/service/impl/task_device_fanout.go`

- [ ] **Step 1: Create DTOs**

Create `/OneOPS/OneOps/app/platform/dto/task_asset_precheck.go`:

```go
package dto

type TaskAssetPrecheckReq struct {
	DeviceCodes   []string `json:"device_codes"`
	AccessPlane   string   `json:"access_plane"`
	CredentialRef string   `json:"credential_ref,omitempty"`
}

type TaskAssetPrecheckResp struct {
	Total   int                         `json:"total"`
	Ready   int                         `json:"ready"`
	Blocked int                         `json:"blocked"`
	Warning int                         `json:"warning"`
	Items   []TaskAssetPrecheckItemResp `json:"items"`
}

type TaskAssetPrecheckItemResp struct {
	DeviceCode        string `json:"device_code"`
	Status            string `json:"status"`
	AccessPlane       string `json:"access_plane,omitempty"`
	TargetAddress     string `json:"target_address,omitempty"`
	VendorFamily      string `json:"vendor_family,omitempty"`
	AnsibleConnection string `json:"ansible_connection,omitempty"`
	AnsibleNetworkOS  string `json:"ansible_network_os,omitempty"`
	CredentialRef      string `json:"credential_ref,omitempty"`
	CredentialSource   string `json:"credential_source,omitempty"`
	Reason            string `json:"reason,omitempty"`
}
```

- [ ] **Step 2: Create service interface**

Create `/OneOPS/OneOps/app/platform/service/i_task_asset_precheck.go`:

```go
package service

import (
	"context"

	"github.com/netxops/OneOps/app/platform/dto"
)

type ITaskAssetPrecheckService interface {
	PrecheckAnsibleTaskAsset(ctx context.Context, templateID string, req *dto.TaskAssetPrecheckReq) (*dto.TaskAssetPrecheckResp, error)
}
```

- [ ] **Step 3: Write failing ready and blocked tests**

Create `/OneOPS/OneOps/app/platform/service/impl/task_asset_precheck_test.go` with tests:

```go
type fakeTaskAssetPrecheckDeviceV2 struct {
	devices []*devv2model.DeviceV2
}

func (f *fakeTaskAssetPrecheckDeviceV2) List(ctx context.Context, codes []string, limit int) ([]*devv2model.DeviceV2, error) {
	_ = ctx
	_ = limit
	allowed := map[string]bool{}
	for _, code := range codes {
		allowed[strings.TrimSpace(code)] = true
	}
	out := make([]*devv2model.DeviceV2, 0, len(f.devices))
	for _, device := range f.devices {
		if device != nil && allowed[strings.TrimSpace(device.Code)] {
			out = append(out, device)
		}
	}
	return out, nil
}

func (f *fakeTaskAssetPrecheckDeviceV2) GetSourceByCode(context.Context, string) (*entityv2model.EntityInstance, error) {
	return nil, fmt.Errorf("not used")
}
func (f *fakeTaskAssetPrecheckDeviceV2) GetByCode(context.Context, string) (*devv2model.DeviceV2, error) {
	return nil, fmt.Errorf("not used")
}
func (f *fakeTaskAssetPrecheckDeviceV2) ListPage(context.Context, int, int, []string, *devv2dto.DeviceV2Filter) ([]*devv2model.DeviceV2, int64, error) {
	return nil, 0, fmt.Errorf("not used")
}
func (f *fakeTaskAssetPrecheckDeviceV2) UpsertSeed(context.Context, string, string, map[string]string, map[string]interface{}, map[string]interface{}, []string) (*devv2model.DeviceV2, error) {
	return nil, fmt.Errorf("not used")
}
func (f *fakeTaskAssetPrecheckDeviceV2) Create(context.Context, string, string, string, string, string, map[string]string, map[string]interface{}, map[string]interface{}, []string) (*devv2model.DeviceV2, error) {
	return nil, fmt.Errorf("not used")
}
func (f *fakeTaskAssetPrecheckDeviceV2) Update(context.Context, string, string, string, string, map[string]string, map[string]interface{}, map[string]interface{}, []string) (*devv2model.DeviceV2, error) {
	return nil, fmt.Errorf("not used")
}
func (f *fakeTaskAssetPrecheckDeviceV2) BatchLabels(context.Context, devv2dto.DeviceV2BatchLabelsReq) (devv2dto.DeviceV2BatchLabelsResp, error) {
	return devv2dto.DeviceV2BatchLabelsResp{}, fmt.Errorf("not used")
}
func (f *fakeTaskAssetPrecheckDeviceV2) DeleteByCode(context.Context, string) error {
	return fmt.Errorf("not used")
}

func TestTaskAssetPrecheck_ReadyDeviceIncludesInventoryProfile(t *testing.T) {
	db := newTaskV2TestDB(t)
	template := &platformModel.PlatformTaskTemplate{
		Name:         "network-config-backup",
		AppType:      "ansible",
		ContractJSON: `{"target":{"vendor_families":["h3c_cli"],"access_planes":["in_band"]}}`,
	}
	if err := db.Table(template.TableName()).Create(template).Error; err != nil {
		t.Fatalf("create template failed: %v", err)
	}
	svc := &TaskAssetPrecheckService{
		Logger: zap.NewNop(),
		DB:     types.DBTypeMySQL(db),
		DeviceV2Srv: &fakeTaskAssetPrecheckDeviceV2{devices: []*devv2model.DeviceV2{{
			Code: "SW001",
			Attributes: map[string]interface{}{
				"in_band_ip":   "10.0.0.1",
				"manufacturer": "H3C",
				"platform":     "Comware",
				"credential_refs": map[string]interface{}{
					"default": "vault_h3c_sw001",
				},
			},
		}}},
	}

	resp, err := svc.PrecheckAnsibleTaskAsset(context.Background(), template.ID, &dto.TaskAssetPrecheckReq{
		DeviceCodes: []string{"SW001"},
		AccessPlane: "in_band",
	})
	if err != nil {
		t.Fatalf("PrecheckAnsibleTaskAsset failed: %v", err)
	}
	if resp.Ready != 1 || resp.Blocked != 0 || len(resp.Items) != 1 {
		t.Fatalf("unexpected precheck counts: %+v", resp)
	}
	item := resp.Items[0]
	if item.Status != "ready" || item.VendorFamily != "h3c_cli" || item.AnsibleConnection != "ssh" || item.CredentialSource != "device_binding" {
		t.Fatalf("unexpected ready item: %+v", item)
	}
}

func TestTaskAssetPrecheck_BlocksMissingCredential(t *testing.T) {
	db := newTaskV2TestDB(t)
	template := &platformModel.PlatformTaskTemplate{
		Name:         "network-config-backup",
		AppType:      "ansible",
		ContractJSON: `{"target":{"vendor_families":["h3c_cli"],"access_planes":["in_band"]}}`,
	}
	if err := db.Table(template.TableName()).Create(template).Error; err != nil {
		t.Fatalf("create template failed: %v", err)
	}
	svc := &TaskAssetPrecheckService{
		Logger: zap.NewNop(),
		DB:     types.DBTypeMySQL(db),
		DeviceV2Srv: &fakeTaskAssetPrecheckDeviceV2{devices: []*devv2model.DeviceV2{{
			Code: "SW002",
			Attributes: map[string]interface{}{
				"in_band_ip":   "10.0.0.2",
				"manufacturer": "H3C",
				"platform":     "Comware",
			},
		}}},
	}

	resp, err := svc.PrecheckAnsibleTaskAsset(context.Background(), template.ID, &dto.TaskAssetPrecheckReq{
		DeviceCodes: []string{"SW002"},
		AccessPlane: "in_band",
	})
	if err != nil {
		t.Fatalf("PrecheckAnsibleTaskAsset failed: %v", err)
	}
	if resp.Ready != 0 || resp.Blocked != 1 || len(resp.Items) != 1 {
		t.Fatalf("unexpected precheck counts: %+v", resp)
	}
	if resp.Items[0].Status != "blocked" || !strings.Contains(resp.Items[0].Reason, "凭证") {
		t.Fatalf("expected missing credential block, got %+v", resp.Items[0])
	}
}
```

Required imports for this test file:

```go
import (
	"context"
	"fmt"
	"strings"
	"testing"

	devv2dto "github.com/netxops/OneOps/app/device/v2/dto"
	devv2model "github.com/netxops/OneOps/app/device/v2/model"
	entityv2model "github.com/netxops/OneOps/app/entity/v2/model"
	"github.com/netxops/OneOps/app/platform/dto"
	platformModel "github.com/netxops/OneOps/app/platform/platform_model"
	"github.com/netxops/OneOps/pkg/types"
	"go.uber.org/zap"
)
```

- [ ] **Step 4: Run tests and verify they fail**

Run:

```bash
go test ./app/platform/service/impl -run TestTaskAssetPrecheck -count=1
```

Expected:

```text
FAIL because the service does not exist yet.
```

- [ ] **Step 5: Implement precheck service**

Create `/OneOPS/OneOps/app/platform/service/impl/task_asset_precheck.go`:

```go
package impl

import (
	"context"
	"encoding/json"
	"fmt"
	"strings"

	devv2svc "github.com/netxops/OneOps/app/device/v2/service"
	"github.com/netxops/OneOps/app/platform/dto"
	deviceexecprofile "github.com/netxops/OneOps/app/platform/pkg/deviceexecprofile"
	platformTenant "github.com/netxops/OneOps/app/platform/pkg/tenant"
	platformModel "github.com/netxops/OneOps/app/platform/platform_model"
	"github.com/netxops/OneOps/pkg/types"
	"go.uber.org/zap"
	"gorm.io/gorm"
)

type TaskAssetPrecheckService struct {
	Logger      *zap.Logger
	DB          types.DBTypeMySQL
	DeviceV2Srv devv2svc.IDeviceV2
}

type ansibleTaskContract struct {
	Target struct {
		VendorFamilies []string `json:"vendor_families"`
		AccessPlanes   []string `json:"access_planes"`
	} `json:"target"`
}

func (s *TaskAssetPrecheckService) db(ctx context.Context) *gorm.DB {
	return (*gorm.DB)(s.DB).WithContext(ctx)
}

func (s *TaskAssetPrecheckService) PrecheckAnsibleTaskAsset(ctx context.Context, templateID string, req *dto.TaskAssetPrecheckReq) (*dto.TaskAssetPrecheckResp, error) {
	if s == nil || s.DeviceV2Srv == nil {
		return nil, fmt.Errorf("task asset precheck service unavailable")
	}
	if req == nil {
		return nil, fmt.Errorf("请求不能为空")
	}
	templateID = strings.TrimSpace(templateID)
	if templateID == "" {
		return nil, fmt.Errorf("template_id 不能为空")
	}
	var template platformModel.PlatformTaskTemplate
	if err := platformTenant.ScopeDB(ctx, s.db(ctx).Table((&platformModel.PlatformTaskTemplate{}).TableName())).
		Where("id = ?", templateID).First(&template).Error; err != nil {
		return nil, err
	}
	contract := parseAnsibleTaskContract(template.ContractJSON)
	accessPlane := effectiveTaskAccessPlane(req.AccessPlane)
	devices, err := s.DeviceV2Srv.List(ctx, normalizeTaskTargetDeviceCodes(req.DeviceCodes), len(req.DeviceCodes))
	if err != nil {
		return nil, err
	}
	byCode := map[string]interface{}{}
	for _, device := range devices {
		if device != nil {
			byCode[strings.TrimSpace(device.Code)] = device
		}
	}
	resp := &dto.TaskAssetPrecheckResp{Total: len(normalizeTaskTargetDeviceCodes(req.DeviceCodes))}
	for _, code := range normalizeTaskTargetDeviceCodes(req.DeviceCodes) {
		item := precheckOneDevice(code, byCode[code], accessPlane, strings.TrimSpace(req.CredentialRef), contract)
		switch item.Status {
		case "ready":
			resp.Ready++
		case "warning":
			resp.Warning++
		default:
			resp.Blocked++
		}
		resp.Items = append(resp.Items, item)
	}
	return resp, nil
}
```

Complete the implementation by reusing `resolveTaskDeviceExecutionTarget` and `deviceexecprofile.ResolveAnsibleDeviceProfile`. The precheck must never include username, password, private key, token, or resolved credential material in the response.

- [ ] **Step 6: Run tests**

Run:

```bash
gofmt -w app/platform/dto/task_asset_precheck.go app/platform/service/i_task_asset_precheck.go app/platform/service/impl/task_asset_precheck.go app/platform/service/impl/task_asset_precheck_test.go
go test ./app/platform/service/impl -run 'TestTaskAssetPrecheck|TestBuildTaskDeviceInventoryContent' -count=1
```

Expected:

```text
ok github.com/netxops/OneOps/app/platform/service/impl
```

---

## Task 4: Expose Precheck API

**Files:**
- Modify: `/OneOPS/OneOps/app/platform/api/task_template.go`
- Modify: `/OneOPS/OneOps/app/platform/router/platform_bidi.go`
- Modify: `/OneOPS/OneOps/app/platform/router/platform.go`
- Create: `/OneOPS/OneOps/app/platform/api/task_asset_precheck_test.go`

- [ ] **Step 1: Write failing API test**

Create a Gin test that registers:

```go
router.POST("/task-assets/:template_id/ansible/precheck", api.PrecheckAnsibleTaskAsset)
```

Post:

```json
{"device_codes":["SW001"],"access_plane":"in_band"}
```

Assert response code `0`, `total=1`, and `items[0].status="ready"` from a fake precheck service.

- [ ] **Step 2: Add API dependency and handler**

Add field to `TaskTemplateAPI`:

```go
TaskAssetPrecheckSrv platformService.ITaskAssetPrecheckService
```

Add handler:

```go
func (a *TaskTemplateAPI) PrecheckAnsibleTaskAsset(ctx *gin.Context) {
	templateID := strings.TrimSpace(ctx.Param("template_id"))
	var req dto.TaskAssetPrecheckReq
	if ok := bind.JSON(&req, ctx); !ok {
		return
	}
	if a.TaskAssetPrecheckSrv == nil {
		response.FailWithMsg("任务资产预检服务未就绪", ctx)
		return
	}
	resp, err := a.TaskAssetPrecheckSrv.PrecheckAnsibleTaskAsset(ctx.Request.Context(), templateID, &req)
	if err != nil {
		response.FailWithMsg(err.Error(), ctx)
		return
	}
	response.OkWithData(resp, ctx)
}
```

- [ ] **Step 3: Register route**

Add to both platform route sets before generic template routes:

```go
taskAssets := g.Group("task-assets")
taskAssets.POST(":template_id/ansible/precheck", taskTemplateAPI.PrecheckAnsibleTaskAsset)
```

- [ ] **Step 4: Run tests**

Run:

```bash
gofmt -w app/platform/api/task_template.go app/platform/router/platform_bidi.go app/platform/router/platform.go app/platform/api/task_asset_precheck_test.go
go test ./app/platform/api -run TestTaskAssetPrecheckAPI -count=1
go test ./app/platform/router -run Test -count=1
```

Expected:

```text
API test passes.
Router tests pass or no matching tests are run.
```

---

## Task 5: Project Runtime Artifacts Into Device Config Backup Records

**Files:**
- Create: `/OneOPS/OneOps/app/platform/platform_model/device_config_backup.go`
- Create: `/OneOPS/OneOps/app/platform/service/impl/device_config_backup_projection.go`
- Create: `/OneOPS/OneOps/app/platform/service/impl/device_config_backup_projection_test.go`

- [ ] **Step 1: Create model**

Create `/OneOPS/OneOps/app/platform/platform_model/device_config_backup.go`:

```go
package platform_model

import (
	"time"

	commonModel "github.com/netxops/OneOps/app/common/model"
)

type DeviceConfigBackup struct {
	commonModel.Common
	TenantScoped
	DeviceCode         string     `gorm:"type:varchar(128);index:idx_device_config_backup_device_time,priority:1"`
	TaskID             string     `gorm:"type:varchar(64);index"`
	ParentTaskID       string     `gorm:"type:varchar(64);index"`
	ControllerID       string     `gorm:"type:varchar(128)"`
	VendorFamily       string     `gorm:"type:varchar(64)"`
	AccessPlane        string     `gorm:"type:varchar(32)"`
	BackupStatus       string     `gorm:"type:varchar(32)"`
	BackupTime         *time.Time `gorm:"index:idx_device_config_backup_device_time,priority:2"`
	ArtifactName       string     `gorm:"type:varchar(256)"`
	ArtifactStorageKey string     `gorm:"type:varchar(512)"`
	ArtifactSize       int64
	ArtifactSHA256     string `gorm:"type:varchar(128)"`
	ConfigHash         string `gorm:"type:varchar(128)"`
	SummaryJSON        string `gorm:"type:text"`
	ErrorMessage       string `gorm:"type:text"`
}

func (*DeviceConfigBackup) TableName() string {
	return "platform_device_config_backup"
}
```

- [ ] **Step 2: Write failing projection test**

Create a test that feeds one child task runtime output with:

```json
{
  "result": {"status": "success"},
  "artifacts": [
    {"name":"network-config-backup-SW001.cfg","path":"network-backups/SW001-manual.cfg","kind":"text","sensitive":true,"size":128,"sha256":"cfgsha","storage_key":"application/task-artifacts/project/controller/task/SW001.cfg"},
    {"name":"network-config-backup-SW001.json","path":"network-config-backup-SW001.json","kind":"json","sensitive":false,"size":64,"sha256":"jsonsha","content_base64":"eyJkZXZpY2VfY29kZSI6IlNXMDAxIiwiY29uZmlnX2hhc2giOiJoYXNoMSJ9"}
  ]
}
```

Assert one `DeviceConfigBackup` row with `DeviceCode=SW001`, `BackupStatus=success`, `ArtifactSHA256=cfgsha`, `ConfigHash=hash1`.

- [ ] **Step 3: Implement projection**

Implement a service function:

```go
func ProjectDeviceConfigBackupFromTaskRuntime(ctx context.Context, db *gorm.DB, task platformModel.Task, runtimeOutput string) error
```

Rules:

- Only project tasks with `AppType=ansible` and `TargetDeviceCode` not empty.
- Prefer the sensitive `.cfg` artifact as `ArtifactName`, `ArtifactStorageKey`, `ArtifactSize`, and `ArtifactSHA256`.
- Parse summary JSON artifact from `content_base64` when present.
- Store raw summary JSON in `SummaryJSON`.
- Use task `ParentTaskID`, `TaskID`, `ControllerID`, `AccessPlane`, and `TargetDeviceCode`.

- [ ] **Step 4: Run tests**

Run:

```bash
gofmt -w app/platform/platform_model/device_config_backup.go app/platform/service/impl/device_config_backup_projection.go app/platform/service/impl/device_config_backup_projection_test.go
go test ./app/platform/service/impl -run TestDeviceConfigBackupProjection -count=1
```

Expected:

```text
ok github.com/netxops/OneOps/app/platform/service/impl
```

---

## Task 6: Add Parent Target Summary API

**Files:**
- Modify: `/OneOPS/OneOps/app/platform/api/task_api.go`
- Modify: `/OneOPS/OneOps/app/platform/router/platform_bidi.go`
- Modify: `/OneOPS/OneOps/app/platform/router/platform.go`
- Modify: `/OneOPS/OneOps/app/platform/api/task_api_test.go`

- [ ] **Step 1: Write failing API test**

Add test for:

```http
GET /tasks/:taskID/target-summary
```

Create parent task, two child tasks, task logs, and one `platform_device_config_backup` row. Assert response:

```json
{
  "total": 2,
  "success": 1,
  "failed": 1,
  "archived": 1,
  "items": [
    {"device_code":"SW001","status":"success","artifact_name":"network-config-backup-SW001.cfg"},
    {"device_code":"SW002","status":"failed","error_message":"missing credential_ref"}
  ]
}
```

- [ ] **Step 2: Implement query**

Add handler to `TaskAPI`:

```go
func (a *TaskAPI) GetTaskTargetSummary(ctx *gin.Context)
```

Query child rows by `parent_task_id = :taskID`, join or look up `platform_device_config_backup` by child task id, and derive counts from child status plus backup rows.

- [ ] **Step 3: Register route**

Add before `tasks.GET(":taskID", taskAPI.GetTask)`:

```go
tasks.GET(":taskID/target-summary", taskAPI.GetTaskTargetSummary)
```

- [ ] **Step 4: Run API tests**

Run:

```bash
gofmt -w app/platform/api/task_api.go app/platform/router/platform_bidi.go app/platform/router/platform.go app/platform/api/task_api_test.go
go test ./app/platform/api -run 'TestTaskAPI_.*TargetSummary' -count=1
```

Expected:

```text
ok github.com/netxops/OneOps/app/platform/api
```

---

## Task 7: Add Device Config Backup History API

**Files:**
- Create: `/OneOPS/OneOps/app/platform/api/device_config_backup.go`
- Create: `/OneOPS/OneOps/app/platform/api/device_config_backup_test.go`
- Modify: `/OneOPS/OneOps/app/platform/router/platform_bidi.go`
- Modify: `/OneOPS/OneOps/app/platform/router/platform.go`

- [ ] **Step 1: Write failing API test**

Register:

```go
router.GET("/device/v2/:device_code/config-backups", api.ListDeviceConfigBackups)
```

Seed two backup rows for one device and one row for another device. Assert only the requested device rows are returned in descending backup time order.

- [ ] **Step 2: Implement handler**

Handler behavior:

- Read `device_code` from path.
- Query `platform_device_config_backup` under current tenant scope.
- Return `backup_status`, `backup_time`, `task_id`, `artifact_name`, `artifact_sha256`, `artifact_size`, `config_hash`, and download metadata.
- Do not return cfg content.

- [ ] **Step 3: Register route**

Add under the platform device area or device v2 route set used by the application:

```go
devices.GET(":code/config-backups", deviceConfigBackupAPI.ListDeviceConfigBackups)
```

If the existing device v2 router owns the canonical route, register the API there instead and keep the response DTO identical.

- [ ] **Step 4: Run tests**

Run:

```bash
gofmt -w app/platform/api/device_config_backup.go app/platform/api/device_config_backup_test.go app/platform/router/platform_bidi.go app/platform/router/platform.go
go test ./app/platform/api -run TestDeviceConfigBackupAPI -count=1
```

Expected:

```text
ok github.com/netxops/OneOps/app/platform/api
```

---

## Task 8: MVP End-To-End Validation

**Files:**
- Read: `/OneOPS/docs/superpowers/ANSIBLE_TASK_ASSETIZATION_MVP_DESIGN_20260606.md`
- Read: `/OneOPS/task-diagnostic-*.txt`

- [ ] **Step 1: Run focused test suite**

Run:

```bash
python3 -m unittest quick_env.tests.test_network_playbooks quick_env.tests.test_template_import_scripts
go test ./app/platform/service/impl -run 'Test(TaskTemplateServiceV2|TaskAssetPrecheck|DeviceConfigBackupProjection|TaskCreationServiceV2|BuildTaskDeviceInventoryContent)' -count=1
go test ./app/platform/api -run 'Test(TaskAssetPrecheckAPI|TestTaskAPI_.*TargetSummary|TestDeviceConfigBackupAPI|TestTaskAPI_.*RuntimeArtifact)' -count=1
git -C quick_env diff --check
git -C OneOps diff --check
```

Expected:

```text
All commands exit 0.
```

- [ ] **Step 2: Import updated templates**

Run:

```bash
bash /OneOPS/quick_env/init-configs/gitea/source-repo/templates/import-variable-sets.sh
bash /OneOPS/quick_env/init-configs/gitea/source-repo/templates/import-to-oneops.sh
```

Expected:

```text
No new duplicate template or variable-set creation.
task-center-ansible-network-config-backup has asset_category=network_config_backup.
```

- [ ] **Step 3: Run precheck with two devices**

Call:

```http
POST /api/v1/platform/task-assets/task-center-ansible-network-config-backup/ansible/precheck
```

Body:

```json
{"device_codes":["SW001","SW002"],"access_plane":"in_band"}
```

Expected:

```text
Response has total=2, at least one ready item, and blocked item includes a clear reason.
Ready item includes vendor_family, ansible_connection, target_address, credential_source.
Response does not include username, password, token, private key, or resolved credential material.
```

- [ ] **Step 4: Run network config backup task**

Use the existing task creation API with the Ansible network config backup template and ready device codes.

Expected:

```text
Parent task is created.
Child tasks are created per device.
Ready child inventory contains ansible_host, vendor_family, ansible_connection, and ansible_network_os when profile provides it.
Inventory contains no inline secrets.
Successful device creates cfg and json runtime artifacts.
Target summary shows device-level success/failure.
Device config backup history shows latest backup status and time.
```

- [ ] **Step 5: Commit MVP changes**

Run:

```bash
git -C /OneOPS/quick_env add \
  init-configs/gitea/source-repo/ansible/network-config-backup/oneops.contract.json \
  init-configs/gitea/source-repo/templates/task-template-catalog.json \
  init-configs/gitea/source-repo/templates/import-to-oneops.sh \
  tests/test_template_import_scripts.py
git -C /OneOPS/quick_env commit -m "feat: seed ansible network backup asset contract"

git -C /OneOPS/OneOps add \
  app/platform/platform_model/platform_task_template.go \
  app/platform/platform_model/device_config_backup.go \
  app/platform/dto/task_template.go \
  app/platform/dto/task_asset_precheck.go \
  app/platform/service/i_task_asset_precheck.go \
  app/platform/service/impl/task_template_v2.go \
  app/platform/service/impl/task_catalog_v2_test.go \
  app/platform/service/impl/task_v2_test_helpers_test.go \
  app/platform/service/impl/task_asset_precheck.go \
  app/platform/service/impl/task_asset_precheck_test.go \
  app/platform/service/impl/device_config_backup_projection.go \
  app/platform/service/impl/device_config_backup_projection_test.go \
  app/platform/api/task_template.go \
  app/platform/api/task_asset_precheck_test.go \
  app/platform/api/task_api.go \
  app/platform/api/task_api_test.go \
  app/platform/api/device_config_backup.go \
  app/platform/api/device_config_backup_test.go \
  app/platform/router/platform_bidi.go \
  app/platform/router/platform.go
git -C /OneOPS/OneOps commit -m "feat: add ansible task asset precheck and backup projection"
```

Expected:

```text
Two focused commits are created. Unrelated dirty files remain unstaged.
```

---

## Self-Review

**Spec coverage:**

- Contract metadata: Task 1 and Task 2.
- Device precheck ready/blocked: Task 3 and Task 4.
- Inventory profile reuse and no inline secrets: Task 3 and existing `task_device_fanout.go` tests.
- Artifact archive visibility: Task 5 and existing runtime artifact API.
- Device-level parent summary: Task 6.
- Device config backup history: Task 7.
- End-to-end acceptance: Task 8.

**Known sequencing rule:**

- Do not start Task 1 until Task 0 is committed, pushed, and the native Maipu backup path has been validated once after platform redeploy.

**Dirty worktree rule:**

- OneOps already contains unrelated user changes. Stage only the exact files listed in each task.
