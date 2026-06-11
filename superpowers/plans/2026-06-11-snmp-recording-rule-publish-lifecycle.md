# SNMP Recording Rule Publish Lifecycle Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publish by-target SNMP recording rule YAML into the configured runtime rule file, reload the rule engine, and persist an auditable publish record.

**Architecture:** Reuse the existing by-target materialization dry-run resolver as the only rule generator. Add a strict file publisher that merges a configured managed group into the existing vmalert rule file, atomically writes the file, calls the configured reload endpoint, and persists publish status. Keep publishing explicit and synchronous; do not add automatic republish or Grafana generation.

**Tech Stack:** Go service/API/router/model in `/OneOPS/OneOps`, `gopkg.in/yaml.v3`, standard `net/http`, GORM auto-migrated platform model, TypeScript API/types smoke in `/OneOPS/OneOps-UI`, quick env vmalert file acceptance.

---

## Scope Lock

This plan only implements:

```text
strategy_set_id + target_part
  -> ResolveStrategySetTargetRecordingRuleMaterializationDryRun
  -> merge managed group into configured rule file
  -> local parse-back validation
  -> atomic file write
  -> configured reload request
  -> publish record
```

Strict non-goals:

- no Grafana dashboard JSON;
- no Grafana page consumption;
- no automatic publish on strategy changes;
- no inventory-wide multi-context aggregation;
- no rollback implementation after reload failure;
- no Kubernetes, object-storage, or Prometheus Operator backend;
- no new vendor/private metric standardization.

The publish request body remains:

```json
{ "target_part": "DEVICE-CODE-OR-ID" }
```

---

## File Structure

Backend config:

- Modify `/OneOPS/OneOps/config/config.go`
- Create `/OneOPS/OneOps/config/snmp_recording_rule_publisher.go`

Backend model and DTO:

- Create `/OneOPS/OneOps/app/platform/platform_model/snmp_recording_rule_publish_record.go`
- Modify `/OneOPS/OneOps/initialize/mysql.go`
- Modify `/OneOPS/OneOps/app/platform/dto/snmp_metric_contract.go`

Backend service:

- Modify `/OneOPS/OneOps/app/platform/service/i_metric_capability_contract_resolver.go`
- Modify `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver.go`
- Modify `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver_test.go`

Backend API/router:

- Modify `/OneOPS/OneOps/app/platform/api/teleabs.go`
- Modify `/OneOPS/OneOps/app/platform/api/teleabs_metric_contract_http_test.go`
- Modify `/OneOPS/OneOps/app/platform/router/platform.go`
- Modify `/OneOPS/OneOps/app/platform/router/platform_bidi.go`
- Modify `/OneOPS/OneOps/app/platform/router/teleabs_routes_consistency_test.go`

Frontend:

- Modify `/OneOPS/OneOps-UI/src/typings/platform/snmp-metric-contract.ts`
- Modify `/OneOPS/OneOps-UI/src/api/platform/teleabs.ts`
- Create `/OneOPS/OneOps-UI/scripts/snmp-strategy-set-recording-rule-publish-smoke.ts`
- Create `/OneOPS/OneOps-UI/scripts/snmp-strategy-set-recording-rule-publish-real-api-acceptance.cjs`
- Modify `/OneOPS/OneOps-UI/package.json`

Docs/quick env:

- Modify `/OneOPS/docs/superpowers/handovers/2026-06-10-snmp-metric-groups-dashboard-family-handoff.md`

---

### Task 1: Publisher Config Contract

**Files:**

- Create: `/OneOPS/OneOps/config/snmp_recording_rule_publisher.go`
- Modify: `/OneOPS/OneOps/config/config.go`

- [ ] **Step 1: Add config struct**

Create `config/snmp_recording_rule_publisher.go`:

```go
package config

type SnmpRecordingRulePublisher struct {
	Enabled               bool   `yaml:"enabled"`
	Backend               string `yaml:"backend"`
	RuleFilePath          string `yaml:"rule_file_path"`
	ManagedGroupName      string `yaml:"managed_group_name"`
	ReloadURL             string `yaml:"reload_url"`
	ReloadMethod          string `yaml:"reload_method"`
	RequestTimeoutSeconds int    `yaml:"request_timeout_seconds"`
}
```

- [ ] **Step 2: Wire config into root config**

In `/OneOPS/OneOps/config/config.go`, add this field to `type Config struct`:

```go
SnmpRecordingRulePublisher SnmpRecordingRulePublisher `yaml:"snmp_recording_rule_publisher"`
```

- [ ] **Step 3: Run compile check**

```bash
cd /OneOPS/OneOps
go test ./config -run '^$' -count=1
```

Expected: PASS.

---

### Task 2: Publish Record Model And DTOs

**Files:**

- Create: `/OneOPS/OneOps/app/platform/platform_model/snmp_recording_rule_publish_record.go`
- Modify: `/OneOPS/OneOps/initialize/mysql.go`
- Modify: `/OneOPS/OneOps/app/platform/dto/snmp_metric_contract.go`

- [ ] **Step 1: Add publish record model**

Create `app/platform/platform_model/snmp_recording_rule_publish_record.go`:

```go
package platform_model

import (
	"time"

	"gorm.io/datatypes"
)

type SnmpRecordingRulePublishRecord struct {
	ID               string         `gorm:"type:varchar(64);primaryKey;comment:发布记录 ID"`
	StrategySetID    string         `gorm:"type:varchar(64);index;not null;comment:策略集 ID"`
	TargetPart       string         `gorm:"type:varchar(128);index;not null;comment:目标标识"`
	TargetDeviceID   string         `gorm:"type:varchar(64);index;comment:设备 ID"`
	TargetDeviceCode string         `gorm:"type:varchar(128);index;comment:设备编码"`
	TargetContext    datatypes.JSON `gorm:"type:json;comment:规范化目标上下文"`
	Backend          string         `gorm:"type:varchar(32);not null;comment:发布后端"`
	RuleFilePath     string         `gorm:"type:varchar(512);not null;comment:规则文件路径"`
	ManagedGroupName string         `gorm:"type:varchar(128);not null;comment:受管规则组名称"`
	RuleCount        int            `gorm:"not null;default:0;comment:规则数量"`
	YAMLSHA256       string         `gorm:"type:varchar(64);index;comment:YAML SHA256"`
	Status           string         `gorm:"type:varchar(32);index;not null;comment:状态"`
	ErrorMessage     string         `gorm:"type:text;comment:错误信息"`
	StartedAt        *time.Time     `gorm:"comment:开始时间"`
	MaterializedAt   *time.Time     `gorm:"comment:生成时间"`
	MergedAt         *time.Time     `gorm:"comment:合并时间"`
	ValidatedAt      *time.Time     `gorm:"comment:校验时间"`
	WrittenAt        *time.Time     `gorm:"comment:写入时间"`
	ReloadedAt       *time.Time     `gorm:"comment:重载时间"`
	CreatedAt        time.Time      `gorm:"autoCreateTime"`
	UpdatedAt        time.Time      `gorm:"autoUpdateTime"`
}

func (SnmpRecordingRulePublishRecord) TableName() string {
	return "platform_snmp_recording_rule_publish_records"
}
```

- [ ] **Step 2: Register model in AutoMigrate**

In `/OneOPS/OneOps/initialize/mysql.go`, add this model near the other `platform_model` entries:

```go
platform_model.SnmpRecordingRulePublishRecord{},
```

- [ ] **Step 3: Add DTOs**

In `/OneOPS/OneOps/app/platform/dto/snmp_metric_contract.go`, add after the materialization response:

```go
type SnmpStrategySetTargetRecordingRulePublishRequest struct {
	TargetPart string `json:"target_part"`
}

type SnmpRecordingRulePublishStep struct {
	Name      string `json:"name"`
	Status    string `json:"status"`
	Message   string `json:"message,omitempty"`
	Timestamp string `json:"timestamp,omitempty"`
}

type SnmpRecordingRulePublishSummary struct {
	PublishID        string                         `json:"publish_id"`
	Backend          string                         `json:"backend"`
	RuleFilePath     string                         `json:"rule_file_path"`
	ManagedGroupName string                         `json:"managed_group_name"`
	RuleCount        int                            `json:"rule_count"`
	Status           string                         `json:"status"`
	Steps            []SnmpRecordingRulePublishStep `json:"steps"`
	ErrorMessage     string                         `json:"error_message,omitempty"`
}

type SnmpStrategySetTargetRecordingRulePublishResponse struct {
	StrategySetID string                         `json:"strategy_set_id"`
	Target        SnmpMetricResolvedTargetContext `json:"target"`
	Source        string                         `json:"source"`
	RuleGroup     SnmpRecordingRulePreviewGroup  `json:"rule_group"`
	Rules         []SnmpRecordingRulePreviewRule `json:"rules"`
	Summary       SnmpRecordingRulePreviewSummary `json:"summary"`
	YAMLSHA256    string                         `json:"yaml_sha256"`
	Publish       SnmpRecordingRulePublishSummary `json:"publish"`
}
```

- [ ] **Step 4: Run compile check**

```bash
cd /OneOPS/OneOps
go test ./app/platform/dto ./app/platform/platform_model -run '^$' -count=1
```

Expected: PASS.

---

### Task 3: Pure YAML Managed Group Merge

**Files:**

- Modify: `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver.go`
- Modify: `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver_test.go`

- [ ] **Step 1: Write failing merge test**

Add `TestMetricCapabilityContractResolverMergesManagedRecordingRuleGroup`.

Test input:

```go
existing := `groups:
  - name: counts
    interval: 5m
    rules:
      - record: ifin_rate:5m
        expr: rate(snmp_interface_ifInOctets[5m])
  - name: oneops_snmp_recording_rules
    interval: 30s
    rules:
      - record: old_record
        expr: old_metric
`
group := dto.SnmpRecordingRulePreviewGroup{
	Name:     "oneops_snmp_recording_rules_preview",
	Interval: "30s",
	Rules: []dto.SnmpRecordingRulePreviewRule{
		{Record: "oneops:if_in_rate:bps", Expr: "rate(snmp_interface_ifInOctets[5m]) * 8"},
		{Record: "oneops:cpu_usage_direct:ratio", Expr: "snmp_cpu_usage / 100"},
	},
}
```

Assert:

- merged YAML still contains `name: counts`;
- merged YAML contains `name: oneops_snmp_recording_rules`;
- merged YAML does not contain `old_record`;
- merged YAML contains both new records;
- summary rule count is `2`;
- duplicate same record with different expr returns error containing `duplicate managed record`.

- [ ] **Step 2: Run failing test**

```bash
cd /OneOPS/OneOps
go test ./app/platform/service/impl -run TestMetricCapabilityContractResolverMergesManagedRecordingRuleGroup -count=1
```

Expected: FAIL because merge helper does not exist.

- [ ] **Step 3: Implement merge helper**

Add:

```go
func mergeManagedRecordingRuleGroup(existing []byte, group dto.SnmpRecordingRulePreviewGroup, managedGroupName string) ([]byte, int, error)
```

Implementation requirements:

- parse `existing` into `dto.SnmpPrometheusRuleFile`;
- if `existing` is empty, treat it as `groups: []`;
- reject empty `managedGroupName`;
- remove groups with matching managed group name;
- deduplicate `record + expr`;
- reject same record with different expr;
- append managed group at the end;
- marshal with `yaml.v3`;
- parse back and verify exactly one managed group exists;
- return merged bytes and managed rule count.

- [ ] **Step 4: Run merge test**

```bash
cd /OneOPS/OneOps
go test ./app/platform/service/impl -run TestMetricCapabilityContractResolverMergesManagedRecordingRuleGroup -count=1
```

Expected: PASS.

---

### Task 4: File Publisher With Reload Client

**Files:**

- Modify: `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver.go`
- Modify: `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver_test.go`

- [ ] **Step 1: Write failing file publisher test**

Add `TestMetricCapabilityContractResolverPublishesManagedRuleFileAndReloads`.

Test setup:

```go
dir := t.TempDir()
ruleFile := filepath.Join(dir, "vmalert-rule.yml")
err := os.WriteFile(ruleFile, []byte("groups:\n  - name: counts\n    rules:\n      - record: existing\n        expr: vector(1)\n"), 0644)
if err != nil { t.Fatal(err) }
reloadCalled := false
server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
	reloadCalled = true
	if r.Method != http.MethodGet {
		t.Fatalf("unexpected reload method: %s", r.Method)
	}
	w.WriteHeader(http.StatusOK)
}))
defer server.Close()
```

Assert:

- publish returns status `reloaded`;
- file contains `counts`;
- file contains managed group;
- file contains `oneops:if_in_rate:bps`;
- reload server was called;
- a reload HTTP 500 returns status `failed_reload`.

- [ ] **Step 2: Run failing test**

```bash
cd /OneOPS/OneOps
go test ./app/platform/service/impl -run TestMetricCapabilityContractResolverPublishesManagedRuleFileAndReloads -count=1
```

Expected: FAIL because publisher helper does not exist.

- [ ] **Step 3: Implement publisher helper**

Add a small internal config struct:

```go
type snmpRecordingRulePublishConfig struct {
	Enabled               bool
	Backend               string
	RuleFilePath          string
	ManagedGroupName      string
	ReloadURL             string
	ReloadMethod          string
	RequestTimeoutSeconds int
}
```

Add:

```go
func publishManagedRecordingRuleFile(ctx context.Context, cfg snmpRecordingRulePublishConfig, group dto.SnmpRecordingRulePreviewGroup) (yamlSHA string, summary dto.SnmpRecordingRulePublishSummary, err error)
```

Implementation requirements:

- require `cfg.Enabled == true`;
- require `cfg.Backend == "vmalert_file"`;
- require non-empty file path, managed group, reload URL, reload method;
- read existing file;
- call `mergeManagedRecordingRuleGroup`;
- write to temp file in same directory;
- `os.Rename(temp, cfg.RuleFilePath)`;
- call reload URL with configured method and timeout;
- status is `reloaded` on 2xx reload;
- status is `failed_reload` on non-2xx or request error;
- do not rollback in this stage.

- [ ] **Step 4: Run publisher test**

```bash
cd /OneOPS/OneOps
go test ./app/platform/service/impl -run TestMetricCapabilityContractResolverPublishesManagedRuleFileAndReloads -count=1
```

Expected: PASS.

---

### Task 5: Publish Resolver And Record Persistence

**Files:**

- Modify: `/OneOPS/OneOps/app/platform/service/i_metric_capability_contract_resolver.go`
- Modify: `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver.go`
- Modify: `/OneOPS/OneOps/app/platform/service/impl/metric_capability_contract_resolver_test.go`

- [ ] **Step 1: Add interface method**

```go
ResolveStrategySetTargetRecordingRulePublish(ctx context.Context, strategySetID string, request dto.SnmpStrategySetTargetRecordingRulePublishRequest) (*dto.SnmpStrategySetTargetRecordingRulePublishResponse, error)
```

- [ ] **Step 2: Write failing resolver test**

Add `TestMetricCapabilityContractResolverPublishesStrategySetRecordingRulesByTarget`.

Use the existing H3C by-target fixture and `recordingRulePreviewPassthroughConfigForTest()`.

Assert:

- response target context is H3C/Comware;
- publish status is `reloaded`;
- `yaml_sha256` is non-empty;
- managed file contains 12 records;
- database has one row in `platform_snmp_recording_rule_publish_records`;
- row status is `reloaded`;
- empty target returns `target_part is required`;
- disabled publisher config returns `recording rule publisher is disabled`.

- [ ] **Step 3: Implement resolver method**

Implementation flow:

```text
ResolveStrategySetTargetRecordingRuleMaterializationDryRun
  -> publishManagedRecordingRuleFile
  -> insert SnmpRecordingRulePublishRecord
  -> return publish response
```

Use existing `ProxySrv.GetDB(ctx)` pattern from target context resolver to persist the record.

- [ ] **Step 4: Run resolver test**

```bash
cd /OneOPS/OneOps
go test ./app/platform/service/impl -run 'TestMetricCapabilityContractResolverPublishesStrategySetRecordingRulesByTarget|TestMetricCapabilityContractResolverPublishesManagedRuleFileAndReloads|TestMetricCapabilityContractResolverMergesManagedRecordingRuleGroup' -count=1
```

Expected: PASS.

---

### Task 6: HTTP Route

**Files:**

- Modify: `/OneOPS/OneOps/app/platform/api/teleabs.go`
- Modify: `/OneOPS/OneOps/app/platform/api/teleabs_metric_contract_http_test.go`
- Modify: `/OneOPS/OneOps/app/platform/router/platform.go`
- Modify: `/OneOPS/OneOps/app/platform/router/platform_bidi.go`
- Modify: `/OneOPS/OneOps/app/platform/router/teleabs_routes_consistency_test.go`

- [ ] **Step 1: Write failing HTTP tests**

Add `TestTeleabsAPI_PublishStrategySetRecordingRulesByTarget_HTTP`.

Path:

```text
POST /platform/metrics/teleabs/strategy-sets/set-1/metric-contract/recording-rules/publish/by-target
```

Body:

```json
{ "target_part": "SW-1" }
```

Assert:

- resolver receives `set-1`;
- resolver receives `SW-1`;
- response contains `publish.status = reloaded`;
- response contains non-empty `yaml_sha256`;
- empty target forwards strict error.

- [ ] **Step 2: Implement handler**

Add to `/OneOPS/OneOps/app/platform/api/teleabs.go`:

```go
func (a *TeleabsAPI) PublishTeleabsStrategySetRecordingRulesByTarget(ctx *gin.Context)
```

Use the same structure as `MaterializeTeleabsStrategySetRecordingRulesByTarget`, but call:

```go
a.MetricContractResolver.ResolveStrategySetTargetRecordingRulePublish(...)
```

- [ ] **Step 3: Register route**

Add to both routers:

```text
POST strategy-sets/:id/metric-contract/recording-rules/publish/by-target
```

- [ ] **Step 4: Run API/router tests**

```bash
cd /OneOPS/OneOps
go test ./app/platform/api -run TestTeleabsAPI_PublishStrategySetRecordingRulesByTarget -count=1
go test ./app/platform/router -run TestTeleabsRoutes_ConsistentBetweenPlatformAndBidi -count=1
```

Expected: PASS.

---

### Task 7: Frontend Types And Smoke

**Files:**

- Modify: `/OneOPS/OneOps-UI/src/typings/platform/snmp-metric-contract.ts`
- Modify: `/OneOPS/OneOps-UI/src/api/platform/teleabs.ts`
- Create: `/OneOPS/OneOps-UI/scripts/snmp-strategy-set-recording-rule-publish-smoke.ts`
- Modify: `/OneOPS/OneOps-UI/package.json`

- [ ] **Step 1: Add frontend types**

Add interfaces matching backend DTOs:

```ts
export interface SnmpStrategySetTargetRecordingRulePublishRequest {
  target_part: string;
}

export interface SnmpRecordingRulePublishStep {
  name: string;
  status: string;
  message?: string;
  timestamp?: string;
}

export interface SnmpRecordingRulePublishSummary {
  publish_id: string;
  backend: string;
  rule_file_path: string;
  managed_group_name: string;
  rule_count: number;
  status: string;
  steps: SnmpRecordingRulePublishStep[];
  error_message?: string;
}

export interface SnmpStrategySetTargetRecordingRulePublishResponse {
  strategy_set_id: string;
  target: SnmpMetricResolvedTargetContext;
  source: 'backend_resolver' | string;
  rule_group: SnmpRecordingRulePreviewGroup;
  rules: SnmpRecordingRulePreviewRule[];
  summary: SnmpRecordingRulePreviewSummary;
  yaml_sha256: string;
  publish: SnmpRecordingRulePublishSummary;
}
```

- [ ] **Step 2: Add API wrapper**

In `/OneOPS/OneOps-UI/src/api/platform/teleabs.ts`, add:

```ts
export const publishTeleabsStrategySetRecordingRulesByTarget = async (
  id: string,
  body: SnmpStrategySetTargetRecordingRulePublishRequest,
) => {
  const resp = await requestEnvelope<SnmpStrategySetTargetRecordingRulePublishResponse>({
    url: `${BASE}/strategy-sets/${encodeURIComponent(id)}/metric-contract/recording-rules/publish/by-target`,
    method: HTTP_POST,
    data: body,
    silentError: true,
  });
  if (!resp || resp.code !== 0) {
    throw new Error(resp?.msg || 'Recording rule 发布失败');
  }
  return resp.data;
};
```

- [ ] **Step 3: Add smoke script**

Create `/OneOPS/OneOps-UI/scripts/snmp-strategy-set-recording-rule-publish-smoke.ts` with assertions:

```ts
import assert from 'node:assert/strict';
import type { publishTeleabsStrategySetRecordingRulesByTarget } from '../src/api/platform/teleabs';
import type {
  SnmpStrategySetTargetRecordingRulePublishRequest,
  SnmpStrategySetTargetRecordingRulePublishResponse,
} from '../src/typings/platform/snmp-metric-contract';

type PublishFn = typeof publishTeleabsStrategySetRecordingRulesByTarget;

const body: SnmpStrategySetTargetRecordingRulePublishRequest = { target_part: 'DVCF5A07C0AFFC9' };
assert.deepEqual(Object.keys(body), ['target_part']);
const fnShape: PublishFn | null = null;
assert.equal(fnShape, null);

const response: SnmpStrategySetTargetRecordingRulePublishResponse = {
  strategy_set_id: 'set-1',
  source: 'backend_resolver',
  target: {
    target_part: 'DVCF5A07C0AFFC9',
    device_id: 'dev-1',
    device_code: 'DVCF5A07C0AFFC9',
    metadata_source: 'platform_devices_v2',
    context: { catalog_name: 'network', manufacturer_name: 'H3C', platform_name: 'Comware' },
  },
  rule_group: { name: 'oneops_snmp_recording_rules_preview', interval: '30s', rules: [] },
  rules: [],
  summary: { total: 0, generated: 0, deduplicated: 0, skipped_not_base: 0, skipped_not_recordable: 0, skipped_config_driven: 0 },
  yaml_sha256: 'abc123',
  publish: {
    publish_id: 'pub-1',
    backend: 'vmalert_file',
    rule_file_path: '/tmp/vmalert-rule.yml',
    managed_group_name: 'oneops_snmp_recording_rules',
    rule_count: 12,
    status: 'reloaded',
    steps: [{ name: 'reload', status: 'success' }],
  },
};

assert.equal(response.publish.status, 'reloaded');
assert.equal(response.publish.rule_count, 12);
assert.ok(response.yaml_sha256);
console.log('snmp strategy-set recording rule publish smoke passed');
```

- [ ] **Step 4: Add package script and run**

Add:

```json
"smoke:snmp-strategy-set-recording-rule-publish": "npx esbuild scripts/snmp-strategy-set-recording-rule-publish-smoke.ts --bundle --platform=node --format=cjs --loader:.vue=text --outfile=.tmp/snmp-strategy-set-recording-rule-publish-smoke.cjs >/dev/null && node .tmp/snmp-strategy-set-recording-rule-publish-smoke.cjs"
```

Run:

```bash
cd /OneOPS/OneOps-UI
npm run smoke:snmp-strategy-set-recording-rule-publish
```

Expected: PASS.

---

### Task 8: Real API Acceptance Script

**Files:**

- Create: `/OneOPS/OneOps-UI/scripts/snmp-strategy-set-recording-rule-publish-real-api-acceptance.cjs`
- Modify: `/OneOPS/OneOps-UI/package.json`

- [ ] **Step 1: Add real API acceptance script**

The script must:

- require `ONEOPS_API_TOKEN`;
- use `ONEOPS_API_BASE_URL` default `http://127.0.0.1:18082/api/v1`;
- use `ONEOPS_STRATEGY_SET_ID` default `4284353d-1233-4022-ad18-871b3d8444c7`;
- publish these targets in order:

```text
DVCF5A07C0AFFC9
DVC2C4468B0B813
DVCF21C6B43350C
```

For each response assert:

- `publish.status = reloaded`;
- `publish.backend = vmalert_file`;
- `publish.managed_group_name = oneops_snmp_recording_rules`;
- `publish.rule_count = 12`;
- `yaml_sha256` is non-empty;
- request body keys equal `["target_part"]`.

- [ ] **Step 2: Add package script**

```json
"smoke:snmp-strategy-set-recording-rule-publish-real-api": "node scripts/snmp-strategy-set-recording-rule-publish-real-api-acceptance.cjs"
```

- [ ] **Step 3: Run with current backend and vmalert**

```bash
cd /OneOPS/OneOps-UI
ONEOPS_API_BASE_URL=http://127.0.0.1:18082/api/v1 \
ONEOPS_API_TOKEN="$(cat /tmp/oneops-ui-real-page-token-18082.txt)" \
npm run smoke:snmp-strategy-set-recording-rule-publish-real-api
```

Expected: PASS.

---

### Task 9: Handoff And Verification

**Files:**

- Modify: `/OneOPS/docs/superpowers/handovers/2026-06-10-snmp-metric-groups-dashboard-family-handoff.md`

- [ ] **Step 1: Update handoff**

Add:

- publish endpoint path;
- request/response shape;
- publisher config shape;
- lifecycle statuses;
- quick env acceptance results;
- explicit deferred items.

- [ ] **Step 2: Run focused verification**

```bash
cd /OneOPS/OneOps
go test ./app/platform/service/impl -run 'TestMetricCapabilityContractResolver.*RecordingRule|TestMetricCapabilityContractResolver.*Publish' -count=1
go test ./app/platform/api -run 'TestTeleabsAPI_.*RecordingRulesByTarget|TestTeleabsAPI_PublishStrategySetRecordingRulesByTarget' -count=1
go test ./app/platform/router -run TestTeleabsRoutes_ConsistentBetweenPlatformAndBidi -count=1

cd /OneOPS/OneOps-UI
npm run smoke:snmp-strategy-set-recording-rule-materialization-dry-run
npm run smoke:snmp-strategy-set-recording-rule-publish

cd /OneOPS/quick_env
bash tests/test_sync_snmp_network_strategy_seed.sh
bash tests/test_snmp_network_strategy_seed.sh

git -C /OneOPS/OneOps diff --check
git -C /OneOPS/OneOps-UI diff --check
git -C /OneOPS/quick_env diff --check
git -C /OneOPS/docs diff --check
```

Expected: PASS / no output.

---

## Execution Notes

- Do not start Grafana work in this plan.
- Do not add automatic publish triggers.
- Do not add rollback behavior in this plan.
- Do not infer target metadata in the frontend.
- If a real backend process is started for acceptance, stop it before final response and remove `cpu.prof` and `mem.prof`.
