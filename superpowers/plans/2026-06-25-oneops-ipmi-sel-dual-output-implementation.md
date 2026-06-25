# OneOps IPMI SEL Dual Output Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend `oneops_ipmi` so one input task can emit IPMI metrics to Prometheus-style outputs and incremental SEL event logs to Loki with durable local cursors and strict whitelist-based stream separation.

**Architecture:** The implementation adds explicit dual-stream template metadata in `teleabs`, a new `sel_logs` collector plus durable cursor store in the `ctrlhub` Telegraf input, and explicit `namepass` routing plus productized seed updates in `OneOps`. The rollout is deliberately phased so existing `oneops_ipmi` metric-only behavior remains unchanged unless `sel_logs` is enabled.

**Tech Stack:** Go, Telegraf input/output plugins, Teleabs JSON templates, OneOps platform services, SQL seed migrations, Loki, Prometheus remote write

---

## Repo Map

This feature spans four Git repos inside the workspace:

- `teleabs/`
  - template model and `oneops-ipmi-basic` template metadata
- `ctrlhub/`
  - `inputs.oneops_ipmi` implementation and unit tests
- `OneOps/`
  - template-provider behavior, output routing tests, productized SQL seeds, and platform-side tests
- `quick_env/`
  - runtime bootstrap SQL and seed-guard coverage for strict dual-output routing

## Planned File Structure

### Teleabs

- Modify: `/home/jacky/project/OneOPS-ALL/teleabs/models.go`
  - add explicit `Produces []string` support to `AbstractionTemplate`
- Modify: `/home/jacky/project/OneOPS-ALL/teleabs/teleabs-templates/categories/infrastructure/server/oob/oneops_ipmi_basic.json`
  - declare dual produces and render new `sel_logs` parameters
- Modify: `/home/jacky/project/OneOPS-ALL/teleabs/stable_template_render_test.go`
  - assert the rendered template carries new parameters and still hides credential fields

### Ctrlhub Agent

- Modify: `/home/jacky/project/OneOPS-ALL/ctrlhub/controller/agent/pkg/telegraf/plugins/inputs/oneops_ipmi/oneops_ipmi.go`
  - register config fields, dispatch `sel_logs`, wire cursor store and whitelist-safe log measurement emission
- Modify: `/home/jacky/project/OneOPS-ALL/ctrlhub/controller/agent/pkg/telegraf/plugins/inputs/oneops_ipmi/sample.conf`
  - document `sel_logs` and state-dir config
- Modify: `/home/jacky/project/OneOPS-ALL/ctrlhub/controller/agent/pkg/telegraf/plugins/inputs/oneops_ipmi/oneops_ipmi_test.go`
  - extend collector normalization and config validation coverage
- Create: `/home/jacky/project/OneOPS-ALL/ctrlhub/controller/agent/pkg/telegraf/plugins/inputs/oneops_ipmi/sel_cursor_store.go`
  - isolate durable cursor persistence and state-key logic
- Create: `/home/jacky/project/OneOPS-ALL/ctrlhub/controller/agent/pkg/telegraf/plugins/inputs/oneops_ipmi/sel_cursor_store_test.go`
  - test bootstrap, restart resume, and reset handling
- Create: `/home/jacky/project/OneOPS-ALL/ctrlhub/controller/agent/pkg/telegraf/plugins/inputs/oneops_ipmi/sel_log_collector.go`
  - isolate SEL incremental delta logic and event-to-metric conversion
- Create: `/home/jacky/project/OneOPS-ALL/ctrlhub/controller/agent/pkg/telegraf/plugins/inputs/oneops_ipmi/sel_log_collector_test.go`
  - test delta selection, duplicate avoidance, and measurement shape

### OneOps Platform

- Modify: `/home/jacky/project/OneOPS-ALL/OneOps/app/platform/service/impl/teleabs_template_provider.go`
  - prefer explicit template `Produces` over plugin-type inference
- Modify: `/home/jacky/project/OneOPS-ALL/OneOps/app/platform/service/impl/teleabs_template_produces.go`
  - keep inference for templates without explicit `Produces`, but stop relying on inference for `oneops_ipmi`
- Modify: `/home/jacky/project/OneOPS-ALL/OneOps/app/platform/service/impl/teleabs_template_provider_exec_test.go`
  - assert `oneops-ipmi-basic` advertises `["metrics","logs"]`
- Modify: `/home/jacky/project/OneOPS-ALL/OneOps/app/platform/service/impl/monitoring_task_v3_service_test.go`
  - assert input-produce inference for `oneops-ipmi-basic` includes both streams
- Modify: `/home/jacky/project/OneOPS-ALL/OneOps/app/platform/service/impl/telegraf_output_provider_test.go`
  - assert Loki default remains legacy for unrelated outputs but explicit `namepass` for IPMI dual-output configs is preserved
- Modify: `/home/jacky/project/OneOPS-ALL/OneOps/app/platform/service/impl/telegraf_config_generator_impl_test.go`
  - assert generated TOML for explicit Prometheus/Loki outputs preserves strict whitelist routing
- Modify: `/home/jacky/project/OneOPS-ALL/OneOps/migrations/seed_server_oob_ipmi_strategy_set.sql`
  - productize `sel_logs`, local cursor dir, and dual output IDs for server OOB IPMI strategy
- Modify: `/home/jacky/project/OneOPS-ALL/OneOps/app/platform/service/impl/server_oob_ipmi_seed_test.go`
  - assert the migration seed includes dual outputs and `sel_logs`

### Quick Env
- Modify: `/home/jacky/project/OneOPS-ALL/quick_env/docker-entrypoint-initdb.d/zzzzzzzzz-current-mysql-seed-bootstrap.sql`
  - add explicit `namepass` config for `http_push_prometheus` and `loki_forwarder`
- Modify: `/home/jacky/project/OneOPS-ALL/quick_env/docker-entrypoint-initdb.d/zz-platform-bootstrap.sql`
  - keep quick env base output seeds aligned with strict whitelist routing
- Modify: `/home/jacky/project/OneOPS-ALL/quick_env/tests/test_seed_template_guard.py`
  - assert quick env seeds carry the IPMI dual-output routing config

## Task 1: Add Explicit Dual-Stream Template Metadata In Teleabs

**Files:**
- Modify: `/home/jacky/project/OneOPS-ALL/teleabs/models.go`
- Modify: `/home/jacky/project/OneOPS-ALL/teleabs/teleabs-templates/categories/infrastructure/server/oob/oneops_ipmi_basic.json`
- Modify: `/home/jacky/project/OneOPS-ALL/teleabs/stable_template_render_test.go`

- [ ] **Step 1: Write the failing Teleabs render test**

```go
{
	name:       "oneops_ipmi",
	templateID: "oneops-ipmi-basic",
	pluginType: "oneops_ipmi",
	layer:      BasicAbstraction,
	target: MonitoringTarget{
		DeviceID:   "server-oob-1",
		DeviceName: "server-oob-1",
		Address:    "10.20.30.60",
		Port:       623,
		Credentials: map[string]interface{}{
			"username": "root",
			"password": "secret",
		},
	},
	config: map[string]interface{}{
		"collectors":                []interface{}{"ipmi", "dcmi", "bmc", "chassis", "sel_logs"},
		"sel_log_state_dir":         "/var/lib/oneops-telegraf/ipmi-sel",
		"sel_log_bootstrap":         "latest",
		"sel_log_max_entries_per_scrape": 100,
	},
	mustContain: []string{
		"[[inputs.oneops_ipmi]]",
		`collectors = ["ipmi", "dcmi", "bmc", "chassis", "sel_logs"]`,
		`sel_log_state_dir = "/var/lib/oneops-telegraf/ipmi-sel"`,
		`sel_log_bootstrap = "latest"`,
		`sel_log_max_entries_per_scrape = 100`,
	},
}
```

- [ ] **Step 2: Run the Teleabs render test and verify it fails**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/teleabs
go test ./... -run 'TestStableTemplateRender/oneops_ipmi' -v
```

Expected: FAIL because the template JSON does not yet define the new parameters or TOML render lines.

- [ ] **Step 3: Add explicit template metadata and render support**

Update the template model and the `oneops-ipmi-basic` JSON so the template can declare dual stream output intent and render SEL-log config:

```go
type AbstractionTemplate struct {
	ID              string              `json:"id"`
	Name            string              `json:"name"`
	Description     string              `json:"description"`
	PluginType      string              `json:"plugin_type"`
	Layer           AbstractionLayer    `json:"layer"`
	ComplexityLevel ComplexityLevel     `json:"complexity_level"`
	Parameters      []TemplateParameter `json:"parameters"`
	Template        string              `json:"template"`
	ValidationRules []ValidationRule    `json:"validation_rules_legacy,omitempty"`
	TemplateLevelRules []TemplateLevelRule `json:"validation_rules,omitempty"`
	Version         string              `json:"version"`
	IsActive        bool                `json:"is_active"`
	CreatedAt       time.Time           `json:"created_at"`
	UpdatedAt       time.Time           `json:"updated_at"`
	CollectionScope string              `json:"collection_scope,omitempty"`
	TargetKind      string              `json:"target_kind,omitempty"`
	Produces        []string            `json:"produces,omitempty"`
	ProducesMetrics []ProducedMetric    `json:"produces_metrics,omitempty"`
}
```

```json
"produces": ["metrics", "logs"],
"parameters": [
  {
    "name": "sel_log_state_dir",
    "type": "string",
    "required": false,
    "source": "technical",
    "description": "Local directory for durable SEL cursor files"
  },
  {
    "name": "sel_log_bootstrap",
    "type": "string",
    "required": false,
    "default_value": "latest",
    "source": "technical",
    "description": "Initial SEL bootstrap mode"
  },
  {
    "name": "sel_log_max_entries_per_scrape",
    "type": "number",
    "required": false,
    "default_value": 100,
    "source": "technical",
    "description": "Max new SEL events to emit per scrape"
  }
],
"template": "[[inputs.oneops_ipmi]]\n  servers = {{.servers | toTomlArray}}\n  {{if .collectors}}\n  collectors = {{.collectors | toTomlArray}}\n  {{end}}\n  privilege = \"{{.privilege | default \"OPERATOR\"}}\"\n  timeout = \"{{.timeout | default \"20s\"}}\"\n  {{if .exclude_sensor_ids}}\n  exclude_sensor_ids = {{.exclude_sensor_ids | toTomlArray}}\n  {{end}}\n  {{if .sel_log_state_dir}}\n  sel_log_state_dir = \"{{.sel_log_state_dir}}\"\n  {{end}}\n  {{if .sel_log_bootstrap}}\n  sel_log_bootstrap = \"{{.sel_log_bootstrap | default \"latest\"}}\"\n  {{end}}\n  {{if .sel_log_max_entries_per_scrape}}\n  sel_log_max_entries_per_scrape = {{.sel_log_max_entries_per_scrape}}\n  {{end}}\n  interval = \"{{.interval | default \"60s\"}}\""
```

- [ ] **Step 4: Run the Teleabs render test and verify it passes**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/teleabs
go test ./... -run 'TestStableTemplateRender/oneops_ipmi' -v
```

Expected: PASS with rendered TOML including `sel_logs` parameters and still hiding credential fields.

- [ ] **Step 5: Commit the Teleabs metadata change**

```bash
cd /home/jacky/project/OneOPS-ALL/teleabs
git add models.go \
  teleabs-templates/categories/infrastructure/server/oob/oneops_ipmi_basic.json \
  stable_template_render_test.go
git commit -m "feat: declare oneops ipmi dual-stream template metadata"
```

## Task 2: Add Durable SEL Cursor Storage In The Ctrlhub IPMI Input

**Files:**
- Create: `/home/jacky/project/OneOPS-ALL/ctrlhub/controller/agent/pkg/telegraf/plugins/inputs/oneops_ipmi/sel_cursor_store.go`
- Create: `/home/jacky/project/OneOPS-ALL/ctrlhub/controller/agent/pkg/telegraf/plugins/inputs/oneops_ipmi/sel_cursor_store_test.go`
- Modify: `/home/jacky/project/OneOPS-ALL/ctrlhub/controller/agent/pkg/telegraf/plugins/inputs/oneops_ipmi/oneops_ipmi_test.go`

- [ ] **Step 1: Write the failing cursor-store tests**

```go
func TestSELCursorStoreBootstrapEmptyState(t *testing.T) {
	dir := t.TempDir()
	store := newSELCursorStore(dir)

	cursor, ok, err := store.Load("10.20.30.60", "sel_logs")
	if err != nil {
		t.Fatalf("Load() error = %v", err)
	}
	if ok {
		t.Fatalf("expected missing cursor, got %+v", cursor)
	}
}

func TestSELCursorStoreRoundTrip(t *testing.T) {
	dir := t.TempDir()
	store := newSELCursorStore(dir)

	want := SELCursorState{
		Server:        "10.20.30.60",
		Collector:     "sel_logs",
		LastRecordID:  42,
		LastTimestamp: 1719302400,
		BMCIdentity:   "10.20.30.60|27400|fw-1",
	}
	if err := store.Save(want); err != nil {
		t.Fatalf("Save() error = %v", err)
	}

	got, ok, err := store.Load("10.20.30.60", "sel_logs")
	if err != nil || !ok {
		t.Fatalf("Load() = (%+v, %v, %v), want ok", got, ok, err)
	}
	if got.LastRecordID != want.LastRecordID {
		t.Fatalf("LastRecordID = %d, want %d", got.LastRecordID, want.LastRecordID)
	}
}

func TestSELCursorStoreDetectsResetByLowerRecordID(t *testing.T) {
	prev := SELCursorState{LastRecordID: 100, BMCIdentity: "10.20.30.60|27400|fw-1"}
	if !selCursorNeedsReset(prev, 20, "10.20.30.60|27400|fw-1") {
		t.Fatalf("expected lower record id to trigger reset")
	}
}
```

- [ ] **Step 2: Run the cursor-store tests and verify they fail**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/ctrlhub
go test ./controller/agent/pkg/telegraf/plugins/inputs/oneops_ipmi -run 'TestSELCursorStore|TestNormalizeCollectorName' -v
```

Expected: FAIL because the cursor store types and helpers do not exist yet.

- [ ] **Step 3: Implement the minimal cursor store**

Create a focused JSON-backed cursor store:

```go
type SELCursorState struct {
	Server        string `json:"server"`
	Collector     string `json:"collector"`
	LastRecordID  uint16 `json:"last_record_id"`
	LastTimestamp int64  `json:"last_timestamp"`
	LastSeenAt    int64  `json:"last_seen_at"`
	BMCIdentity   string `json:"bmc_identity"`
}

type selCursorStore struct {
	dir string
}

func newSELCursorStore(dir string) *selCursorStore {
	return &selCursorStore{dir: dir}
}

func (s *selCursorStore) Load(server, collector string) (SELCursorState, bool, error) {
	path := s.pathFor(server, collector)
	data, err := os.ReadFile(path)
	if errors.Is(err, os.ErrNotExist) {
		return SELCursorState{}, false, nil
	}
	if err != nil {
		return SELCursorState{}, false, err
	}
	var state SELCursorState
	if err := json.Unmarshal(data, &state); err != nil {
		return SELCursorState{}, false, err
	}
	return state, true, nil
}

func (s *selCursorStore) Save(state SELCursorState) error {
	if err := os.MkdirAll(s.dir, 0o755); err != nil {
		return err
	}
	tmp := s.pathFor(state.Server, state.Collector) + ".tmp"
	data, err := json.MarshalIndent(state, "", "  ")
	if err != nil {
		return err
	}
	if err := os.WriteFile(tmp, data, 0o644); err != nil {
		return err
	}
	return os.Rename(tmp, s.pathFor(state.Server, state.Collector))
}
```

- [ ] **Step 4: Run the cursor-store tests and verify they pass**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/ctrlhub
go test ./controller/agent/pkg/telegraf/plugins/inputs/oneops_ipmi -run 'TestSELCursorStore|TestNormalizeCollectorName' -v
```

Expected: PASS with JSON persistence and reset helper behavior covered.

- [ ] **Step 5: Commit the cursor-store change**

```bash
cd /home/jacky/project/OneOPS-ALL/ctrlhub
git add controller/agent/pkg/telegraf/plugins/inputs/oneops_ipmi/sel_cursor_store.go \
  controller/agent/pkg/telegraf/plugins/inputs/oneops_ipmi/sel_cursor_store_test.go \
  controller/agent/pkg/telegraf/plugins/inputs/oneops_ipmi/oneops_ipmi_test.go
git commit -m "feat: add durable sel cursor store for oneops ipmi"
```

## Task 3: Implement Incremental `sel_logs` Collection And Log Measurement Emission

**Files:**
- Create: `/home/jacky/project/OneOPS-ALL/ctrlhub/controller/agent/pkg/telegraf/plugins/inputs/oneops_ipmi/sel_log_collector.go`
- Create: `/home/jacky/project/OneOPS-ALL/ctrlhub/controller/agent/pkg/telegraf/plugins/inputs/oneops_ipmi/sel_log_collector_test.go`
- Modify: `/home/jacky/project/OneOPS-ALL/ctrlhub/controller/agent/pkg/telegraf/plugins/inputs/oneops_ipmi/oneops_ipmi.go`
- Modify: `/home/jacky/project/OneOPS-ALL/ctrlhub/controller/agent/pkg/telegraf/plugins/inputs/oneops_ipmi/sample.conf`
- Modify: `/home/jacky/project/OneOPS-ALL/ctrlhub/controller/agent/pkg/telegraf/plugins/inputs/oneops_ipmi/oneops_ipmi_test.go`

- [ ] **Step 1: Write the failing `sel_logs` tests**

```go
func TestNormalizeCollectorNameSupportsSELLogs(t *testing.T) {
	got, err := normalizeCollectorName("sel_logs")
	if err != nil {
		t.Fatalf("normalizeCollectorName() error = %v", err)
	}
	if got != "sel_logs" {
		t.Fatalf("normalizeCollectorName() = %q, want %q", got, "sel_logs")
	}
}

func TestSELLogDeltaSkipsHistoricalBootstrap(t *testing.T) {
	entries := []selStandardEntry{
		{RecordID: 10, TimestampUnix: 1000, Message: "old"},
		{RecordID: 11, TimestampUnix: 1001, Message: "latest"},
	}
	state, emitted := bootstrapSELLogCursor("10.20.30.60", entries, "10.20.30.60|27400|fw-1")
	if len(emitted) != 0 {
		t.Fatalf("expected no bootstrap replay, got %+v", emitted)
	}
	if state.LastRecordID != 11 {
		t.Fatalf("LastRecordID = %d, want 11", state.LastRecordID)
	}
}

func TestSELLogDeltaEmitsOnlyNewRecords(t *testing.T) {
	prev := SELCursorState{Server: "10.20.30.60", Collector: "sel_logs", LastRecordID: 11, BMCIdentity: "10.20.30.60|27400|fw-1"}
	entries := []selStandardEntry{
		{RecordID: 11, TimestampUnix: 1001, Message: "old"},
		{RecordID: 12, TimestampUnix: 1002, Message: "new-a"},
		{RecordID: 13, TimestampUnix: 1003, Message: "new-b"},
	}
	next, emitted, reset := computeSELLogDelta(prev, entries, "10.20.30.60|27400|fw-1", 100)
	if reset {
		t.Fatalf("unexpected reset")
	}
	if len(emitted) != 2 {
		t.Fatalf("len(emitted) = %d, want 2", len(emitted))
	}
	if next.LastRecordID != 13 {
		t.Fatalf("LastRecordID = %d, want 13", next.LastRecordID)
	}
}
```

- [ ] **Step 2: Run the `sel_logs` tests and verify they fail**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/ctrlhub
go test ./controller/agent/pkg/telegraf/plugins/inputs/oneops_ipmi -run 'TestSELLog|TestNormalizeCollectorNameSupportsSELLogs' -v
```

Expected: FAIL because `sel_logs` helpers and collector code do not exist yet.

- [ ] **Step 3: Implement `sel_logs` config and collector integration**

Add focused config to `OneOpsIPMIExporter` and dispatch it from `runCollector`:

```go
type OneOpsIPMIExporter struct {
	Servers                     []string         `toml:"servers"`
	Collectors                  []string         `toml:"collectors"`
	ExcludeSensorIDs            []int64          `toml:"exclude_sensor_ids"`
	Privilege                   string           `toml:"privilege"`
	Timeout                     config.Duration  `toml:"timeout"`
	SELEvents                   []SELMetricMatch `toml:"sel_event"`
	SELLogStateDir              string           `toml:"sel_log_state_dir"`
	SELLogBootstrap             string           `toml:"sel_log_bootstrap"`
	SELLogMaxEntriesPerScrape   int              `toml:"sel_log_max_entries_per_scrape"`
	SELLogIncludeRaw            bool             `toml:"sel_log_include_raw"`
	SELLogMinSeverity           string           `toml:"sel_log_min_severity"`
	SELLogMeasurement           string           `toml:"sel_log_measurement"`
	Log                         telegraf.Logger  `toml:"-"`
}
```

```go
case "sel_logs":
	return p.collectSELLogs(acc, server, baseTags)
```

Create a dedicated SEL log measurement:

```go
func (p *OneOpsIPMIExporter) emitSELLogEntry(acc telegraf.Accumulator, entry selStandardEntry, baseTags map[string]string, now time.Time) {
	measurement := p.SELLogMeasurement
	if strings.TrimSpace(measurement) == "" {
		measurement = "ipmi_sel_event_log"
	}
	tags := mergeTags(baseTags, map[string]string{
		"record_id":      strconv.FormatUint(uint64(entry.RecordID), 10),
		"severity":       entry.Severity,
		"sensor_type":    entry.SensorType,
		"sensor_number":  entry.SensorNumber,
		"generator_id":   entry.GeneratorID,
		"event_direction": entry.EventDirection,
		"event_type":     entry.EventType,
	})
	fields := map[string]interface{}{
		"message":         entry.Message,
		"event_timestamp": entry.TimestampUnix,
	}
	if p.SELLogIncludeRaw && entry.RawHex != "" {
		fields["raw_hex"] = entry.RawHex
	}
	acc.AddFields(measurement, fields, tags, time.Unix(entry.TimestampUnix, 0))
}
```

- [ ] **Step 4: Run the focused `sel_logs` tests and verify they pass**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/ctrlhub
go test ./controller/agent/pkg/telegraf/plugins/inputs/oneops_ipmi -run 'TestSELLog|TestNormalizeCollectorNameSupportsSELLogs' -v
```

Expected: PASS with bootstrap, incremental delta, and measurement shape covered.

- [ ] **Step 5: Update sample config and commit**

Add the new collector and config comments:

```toml
# ipmi, dcmi, bmc, bmc_watchdog, chassis, sel, sel_events, sel_logs, sm_lan_mode
collectors = ["ipmi", "dcmi", "bmc", "chassis"]

# sel_log_state_dir = "/var/lib/oneops-telegraf/ipmi-sel"
# sel_log_bootstrap = "latest"
# sel_log_max_entries_per_scrape = 100
# sel_log_include_raw = false
# sel_log_measurement = "ipmi_sel_event_log"
```

Commit:

```bash
cd /home/jacky/project/OneOPS-ALL/ctrlhub
git add controller/agent/pkg/telegraf/plugins/inputs/oneops_ipmi/oneops_ipmi.go \
  controller/agent/pkg/telegraf/plugins/inputs/oneops_ipmi/sel_log_collector.go \
  controller/agent/pkg/telegraf/plugins/inputs/oneops_ipmi/sel_log_collector_test.go \
  controller/agent/pkg/telegraf/plugins/inputs/oneops_ipmi/sample.conf \
  controller/agent/pkg/telegraf/plugins/inputs/oneops_ipmi/oneops_ipmi_test.go
git commit -m "feat: add incremental sel log collector to oneops ipmi"
```

## Task 4: Make OneOps Respect Explicit Dual-Stream Template Produces

**Files:**
- Modify: `/home/jacky/project/OneOPS-ALL/OneOps/app/platform/service/impl/teleabs_template_provider.go`
- Modify: `/home/jacky/project/OneOPS-ALL/OneOps/app/platform/service/impl/teleabs_template_produces.go`
- Modify: `/home/jacky/project/OneOPS-ALL/OneOps/app/platform/service/impl/teleabs_template_provider_exec_test.go`
- Modify: `/home/jacky/project/OneOPS-ALL/OneOps/app/platform/service/impl/monitoring_task_v3_service_test.go`

- [ ] **Step 1: Write the failing OneOps provider tests**

```go
func TestTeleabsTemplateProvider_OneOpsIPMIBasicDeclaresDualProduces(t *testing.T) {
	provider := NewTeleabsTemplateProvider(zap.NewNop(), &config.Config{
		Teleabs: config.Teleabs{TemplateDir: mustWorkspaceTeleabsTemplateDir(t)},
	})

	tpl, err := provider.GetTemplateByID(context.Background(), "oneops-ipmi-basic")
	if err != nil {
		t.Fatalf("GetTemplateByID failed: %v", err)
	}
	if !monitoringTaskV3StringSliceEqual(tpl.Produces, []string{"metrics", "logs"}) {
		t.Fatalf("expected produces=[metrics logs], got %+v", tpl.Produces)
	}
}
```

```go
func TestMonitoringTaskV3Service_BuildDispatchPlan_InferInputProducesFromOneOpsIPMIDualTemplate(t *testing.T) {
	svc := NewMonitoringTaskV3ServiceWithDeps(MonitoringTaskV3Deps{
		Logger: zap.NewNop(),
		TeleabsTemplateProvider: &fakeTemplateProvider{templates: map[string]*dto.TeleabsTemplateDetail{
			"oneops-ipmi-basic": {
				ID:         "oneops-ipmi-basic",
				PluginType: "oneops_ipmi",
				Produces:   []string{"metrics", "logs"},
			},
		}},
	})

	plan, err := svc.BuildDispatchPlan(context.Background(), &ApplyCommandV3{
		TemplateID: "oneops-ipmi-basic",
	}, []TargetV3{{EntityType: "device", EntityID: "dev-1", Address: "10.0.0.1"}})
	if err != nil {
		t.Fatalf("build dispatch plan returned error: %v", err)
	}
	if !monitoringTaskV3StringSliceEqual(plan.ApplyInput.InputProduces, []string{"metrics", "logs"}) {
		t.Fatalf("expected input_produces=[metrics logs], got %+v", plan.ApplyInput.InputProduces)
	}
}
```

- [ ] **Step 2: Run the OneOps provider tests and verify they fail**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
go test ./app/platform/service/impl -run 'TestTeleabsTemplateProvider_OneOpsIPMIBasic|TestMonitoringTaskV3Service_BuildDispatchPlan_InferInputProducesFromOneOpsIPMIDualTemplate' -v
```

Expected: FAIL because the provider currently infers `oneops_ipmi` as metrics-only.

- [ ] **Step 3: Implement explicit `Produces` precedence**

Prefer template-level `Produces` before plugin-type inference:

```go
func explicitOrInferredProduces(t *teleabs.AbstractionTemplate, metrics []dto.ProducedMetricDTO) []string {
	if t != nil {
		if values := normalizeTeleabsProduces(t.Produces); len(values) > 0 {
			return values
		}
	}
	if t == nil {
		return nil
	}
	return inferTeleabsProducesFromPluginAndMetrics(t.PluginType, metrics)
}
```

Then replace the `Produces:` assignments in `GetTemplateByID`, `GetTemplateByIDForDisplay`, and `ListTemplates` to call `explicitOrInferredProduces(...)`.

- [ ] **Step 4: Run the OneOps provider tests and verify they pass**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
go test ./app/platform/service/impl -run 'TestTeleabsTemplateProvider_OneOpsIPMIBasic|TestMonitoringTaskV3Service_BuildDispatchPlan_InferInputProducesFromOneOpsIPMIDualTemplate' -v
```

Expected: PASS with `oneops-ipmi-basic` producing both `metrics` and `logs`.

- [ ] **Step 5: Commit the OneOps provider change**

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
git add app/platform/service/impl/teleabs_template_provider.go \
  app/platform/service/impl/teleabs_template_produces.go \
  app/platform/service/impl/teleabs_template_provider_exec_test.go \
  app/platform/service/impl/monitoring_task_v3_service_test.go
git commit -m "feat: honor explicit dual-stream produces for oneops ipmi"
```

## Task 5: Lock Down Output Routing So Metrics Never Reach Loki And Logs Never Reach Prometheus

**Files:**
- Modify: `/home/jacky/project/OneOPS-ALL/OneOps/app/platform/service/impl/telegraf_output_provider_test.go`
- Modify: `/home/jacky/project/OneOPS-ALL/OneOps/app/platform/service/impl/telegraf_config_generator_impl_test.go`
- Modify: `/home/jacky/project/OneOPS-ALL/OneOps/migrations/seed_server_oob_ipmi_strategy_set.sql`
- Modify: `/home/jacky/project/OneOPS-ALL/OneOps/app/platform/service/impl/server_oob_ipmi_seed_test.go`
- Modify: `/home/jacky/project/OneOPS-ALL/quick_env/docker-entrypoint-initdb.d/zz-platform-bootstrap.sql`
- Modify: `/home/jacky/project/OneOPS-ALL/quick_env/docker-entrypoint-initdb.d/zzzzzzzzz-current-mysql-seed-bootstrap.sql`
- Modify: `/home/jacky/project/OneOPS-ALL/quick_env/tests/test_seed_template_guard.py`

- [ ] **Step 1: Write the failing output-routing tests**

```go
t.Run("oneops ipmi loki output keeps explicit sel log whitelist", func(t *testing.T) {
	lokiCfgJSON, _ := json.Marshal(map[string]interface{}{
		"domain":   "http://127.0.0.1:8081",
		"endpoint": "/api/v1/loki/push",
		"timeout":  "5s",
		"namepass": []string{"ipmi_sel_event_log"},
	})
	store.data["ipmi-loki"] = &platform_model.TelegrafOutput{
		Name:            "ipmi-loki",
		FunctionArea:    "monitoring",
		Enabled:         true,
		PluginType:      "loki",
		Layer:           "enterprise",
		SuitableForJSON: mustJSONBytes(t, []string{"logs"}),
		ConfigJSON:      lokiCfgJSON,
	}
	store.data["ipmi-loki"].Common.ID = "ipmi-loki"

	defs, err := provider.GetOutputsForFunctionArea(context.Background(), "monitoring", "", []string{"logs"}, []string{"ipmi-loki"})
	require.NoError(t, err)
	require.Len(t, defs, 1)
	assert.Equal(t, []interface{}{"ipmi_sel_event_log"}, defs[0].Config["namepass"])
})
```

```go
assert.Contains(t, result["loki-out-ipmi"], `namepass = ["ipmi_sel_event_log"]`)
assert.Contains(t, result["http-out-ipmi"], `namepass = ["ipmi","ipmi_scrape_duration","ipmi_temperature","ipmi_fan_speed","ipmi_voltage","ipmi_current","ipmi_power","ipmi_sensor","ipmi_dcmi_power_consumption","ipmi_bmc","ipmi_sel_logs","ipmi_sel_events_count_by","ipmi_sel_events_latest","ipmi_chassis_power"]`)
assert.NotContains(t, result["http-out-ipmi"], `ipmi_sel_event_log`)
```

- [ ] **Step 2: Run the output-routing tests and verify they fail**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
go test ./app/platform/service/impl -run 'TestTelegrafOutputProvider_GetOutputsForFunctionArea|TestTelegrafConfigGenerator_OutputOnlyPerType' -v
```

Expected: FAIL because the IPMI-specific explicit whitelist config is not yet present in the seeded configs and tests.

- [ ] **Step 3: Add explicit whitelist routing to seeds**

Update the strategy seed and quick env outputs so IPMI dual-output tasks route safely:

```sql
JSON_ARRAY('8ec4cae8-0fb0-11f1-b426-0050569b3ce3', '4b7a5857-0fb7-11f1-b426-0050569b3ce3')
```

```sql
'{"domain": "http://${CONTROLLER_SERVER_HOST}:${CONTROLLER_HTTP_PORT}", "timeout": "5s", "endpoint": "/api/v1/loki/push", "gzip_request": false, "metric_name_label": "__name", "sanitize_label_names": false, "namepass": ["ipmi_sel_event_log"]}'
```

```sql
'{"url": "http://${CONTROLLER_SERVER_HOST}:${CONTROLLER_HTTP_PORT}/api/v1/prometheus/push", "method": "POST", "headers": {"Content-Type": "application/x-protobuf", "Content-Encoding": "snappy", "X-Prometheus-Remote-Write-Version": "0.1.0"}, "timeout": "5s", "interval": "1s", "additional_config": "data_format = \"prometheusremotewrite\"", "insecure_skip_verify": true, "namepass": ["ipmi","ipmi_scrape_duration","ipmi_temperature","ipmi_fan_speed","ipmi_voltage","ipmi_current","ipmi_power","ipmi_sensor","ipmi_dcmi_power_consumption","ipmi_bmc","ipmi_sel_logs","ipmi_sel_events_count_by","ipmi_sel_events_latest","ipmi_chassis_power"]}'
```

- [ ] **Step 4: Run the output-routing and seed tests and verify they pass**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
go test ./app/platform/service/impl -run 'TestTelegrafOutputProvider_GetOutputsForFunctionArea|TestTelegrafConfigGenerator_OutputOnlyPerType|TestServerOOBIPMISeed' -v

cd /home/jacky/project/OneOPS-ALL/quick_env
python3 tests/test_seed_template_guard.py
```

Expected:

- Go tests PASS with explicit whitelist preservation
- Python seed guard PASS with the new `namepass` snippets present

- [ ] **Step 5: Commit the routing and seed changes**

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
git add app/platform/service/impl/telegraf_output_provider_test.go \
  app/platform/service/impl/telegraf_config_generator_impl_test.go \
  app/platform/service/impl/server_oob_ipmi_seed_test.go \
  migrations/seed_server_oob_ipmi_strategy_set.sql
git commit -m "feat: route oneops ipmi metrics and sel logs to separate outputs"

cd /home/jacky/project/OneOPS-ALL/quick_env
git add docker-entrypoint-initdb.d/zz-platform-bootstrap.sql \
  docker-entrypoint-initdb.d/zzzzzzzzz-current-mysql-seed-bootstrap.sql \
  tests/test_seed_template_guard.py
git commit -m "test: align quick env output seeds with ipmi dual routing"
```

## Task 6: Run Focused End-To-End Verification Across All Three Repos

**Files:**
- Test only

- [ ] **Step 1: Run Teleabs verification**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/teleabs
go test ./... -run 'TestStableTemplateRender/oneops_ipmi' -v
```

Expected: PASS

- [ ] **Step 2: Run Ctrlhub IPMI verification**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/ctrlhub
go test ./controller/agent/pkg/telegraf/plugins/inputs/oneops_ipmi -v
```

Expected: PASS with `sel_logs`, cursor-store, and existing parser tests all green

- [ ] **Step 3: Run OneOps platform verification**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps
go test ./app/platform/service/impl -run 'TestTeleabsTemplateProvider_OneOpsIPMIBasic|TestMonitoringTaskV3Service_BuildDispatchPlan|TestTelegrafOutputProvider_GetOutputsForFunctionArea|TestTelegrafConfigGenerator_OutputOnlyPerType|TestServerOOBIPMISeed' -v
```

Expected: PASS

- [ ] **Step 4: Run quick env seed verification**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/quick_env
python3 tests/test_seed_template_guard.py
```

Expected: PASS

- [ ] **Step 5: Final implementation handoff commit**

If any test-only tweaks were needed during verification, commit them in the repo they belong to using a focused message such as:

```bash
git commit -m "test: finalize oneops ipmi dual-output verification coverage"
```

## Self-Review

### Spec Coverage

- Single `oneops_ipmi` task with dual outputs: covered by Tasks 1, 4, and 5
- Incremental SEL-only logs to Loki: covered by Tasks 2 and 3
- Restart-safe local cursor persistence: covered by Tasks 2 and 3
- Logs never reach Prometheus and metrics never reach Loki: covered by Task 5
- Existing metric-only behavior remains intact: covered by Tasks 3 and 6
- Productized server OOB IPMI seed path: covered by Task 5

### Placeholder Scan

- No `TODO`, `TBD`, or “similar to above” references remain
- Every code-changing task includes exact file paths and concrete commands
- Every test step names the exact command to run and the expected outcome

### Type Consistency

- `Produces []string` is introduced in `teleabs/models.go` and consumed consistently through the OneOps provider
- `SELCursorState`, `selCursorStore`, and `sel_logs` are named consistently across Task 2 and Task 3
- `ipmi_sel_event_log` is the single log measurement name referenced by template, collector, and output routing tasks
