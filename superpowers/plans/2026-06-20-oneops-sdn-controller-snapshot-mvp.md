# OneOPS SDN Controller Snapshot MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the OneOPS backend and simple UI loop for configuring ACI/Huawei SDN controllers, testing connectivity through `ctrlhub/controller`, syncing a read-only snapshot, and viewing normalized SDN resources.

**Architecture:** OneOPS UI calls OneOPS backend SDN APIs. OneOPS backend stores SDN controller configs and snapshots, resolves credentials by reference, and calls `ctrlhub/controller` `POST /api/v1/sdn/snapshot`. Vendor-specific ACI/Huawei adaptation remains only in `ctrlhub/controller`.

**Tech Stack:** Go, gorilla/mux, MongoDB Go driver, Vue 3, TypeScript, Ant Design Vue, existing OneOPS `request` helper.

---

## File Structure

Backend repo: `/Users/huangliang/project/OneOPS-ALL/agent`

- Create `pkg/controller/sdn/model.go`
  - SDN config, snapshot, resource, summary, request/response models.
- Create `pkg/controller/sdn/client.go`
  - Minimal HTTP client for `ctrlhub/controller` snapshot API.
- Create `pkg/controller/sdn/store.go`
  - Mongo-backed store with in-memory fallback for nil Mongo in unit tests.
- Create `pkg/controller/sdn/service.go`
  - Validation, credential resolving, ctrlhub calls, summary calculation, test/sync orchestration.
- Create `pkg/controller/sdn/service_test.go`
  - TDD tests for validation, summary, sync success/failure, password sanitization.
- Create `pkg/controller/api/sdn.go`
  - HTTP handlers for SDN controller CRUD, test, sync, latest snapshot, history.
- Create `pkg/controller/api/sdn_test.go`
  - Handler tests using fake service/fake ctrlhub.
- Modify `cmd/controller/main.go`
  - Register `/api/v1/sdn/...` routes.

Frontend repo: `/Users/huangliang/project/OneOPS-ALL/OneOPS-UI`

- Create `src/typings/platform/sdn-controller.ts`
  - TypeScript types for controller config, summary, snapshots, resources.
- Create `src/api/platform/sdn-controller.ts`
  - API client functions.
- Create `src/views/platform/SdnControllerManagement.vue`
  - Operational UI page.
- Modify `src/router/utils.ts`
  - Add hidden route `platform/sdn-controllers`.

Docs repo: `/Users/huangliang/project/OneOPS-ALL/docs`

- Existing spec: `superpowers/specs/2026-06-20-oneops-sdn-controller-snapshot-mvp-design.md`
- This plan: `superpowers/plans/2026-06-20-oneops-sdn-controller-snapshot-mvp.md`

---

## Task 1: Backend SDN Domain Models

**Files:**
- Create: `/Users/huangliang/project/OneOPS-ALL/agent/pkg/controller/sdn/model.go`
- Test: `/Users/huangliang/project/OneOPS-ALL/agent/pkg/controller/sdn/service_test.go`

- [ ] **Step 1: Write failing model validation and summary tests**

Create `pkg/controller/sdn/service_test.go` with:

```go
package sdn

import (
	"strings"
	"testing"
)

func TestValidateControllerConfigRequiresCoreFields(t *testing.T) {
	cfg := ControllerConfig{
		Name:          "ACI Prod",
		Provider:      ProviderACI,
		CtrlhubBaseURL: "http://ctrlhub.local:8081",
		SDNScheme:     "https",
		SDNHost:       "apic.local",
		CredentialRef: "secret-aci-prod",
	}

	if err := ValidateControllerConfig(cfg); err != nil {
		t.Fatalf("ValidateControllerConfig() error = %v", err)
	}

	cfg.SDNHost = ""
	err := ValidateControllerConfig(cfg)
	if err == nil || !strings.Contains(err.Error(), "sdn_host is required") {
		t.Fatalf("ValidateControllerConfig() error = %v, want sdn_host required", err)
	}
}

func TestBuildSummaryCountsAllNormalizedResourceGroups(t *testing.T) {
	snapshot := Snapshot{
		Tenants:   []Resource{{Name: "TenantA"}},
		VRFs:      []Resource{{Name: "VRF-A"}},
		Networks:  []Resource{{Name: "BD-A"}, {Name: "BD-B"}},
		Subnets:   []Resource{{Name: "10.0.0.0/24"}},
		Segments:  []Resource{{Name: "Web"}},
		Endpoints: []Resource{{Name: "endpoint-1"}, {Name: "endpoint-2"}},
		Switches:  []Resource{{Name: "leaf-101"}},
		Ports:     []Resource{{Name: "eth1/1"}},
		Contracts: []Resource{{Name: "AllowHTTP"}},
		Filters:   []Resource{{Name: "HTTP"}, {Name: "entry-80"}},
	}

	summary := BuildSummary(snapshot)

	if summary.Tenants != 1 || summary.VRFs != 1 || summary.Networks != 2 ||
		summary.Subnets != 1 || summary.Segments != 1 || summary.Endpoints != 2 ||
		summary.Switches != 1 || summary.Ports != 1 || summary.Contracts != 1 ||
		summary.Filters != 2 || summary.Total != 13 {
		t.Fatalf("BuildSummary() = %+v", summary)
	}
}
```

- [ ] **Step 2: Run tests and verify they fail**

Run:

```bash
cd /Users/huangliang/project/OneOPS-ALL/agent
go test ./pkg/controller/sdn -run 'TestValidateControllerConfigRequiresCoreFields|TestBuildSummaryCountsAllNormalizedResourceGroups' -count=1
```

Expected: FAIL because `pkg/controller/sdn` and model functions do not exist.

- [ ] **Step 3: Add minimal models and helpers**

Create `pkg/controller/sdn/model.go`:

```go
package sdn

import (
	"fmt"
	"net/url"
	"strings"
	"time"
)

type Provider string

const (
	ProviderACI    Provider = "aci"
	ProviderHuawei Provider = "huawei"
)

type SyncStatus string

const (
	SyncStatusNeverSynced SyncStatus = "never_synced"
	SyncStatusSuccess     SyncStatus = "success"
	SyncStatusFailed      SyncStatus = "failed"
)

type ControllerConfig struct {
	ID                 string          `json:"id" bson:"id"`
	Name               string          `json:"name" bson:"name"`
	Provider           Provider        `json:"provider" bson:"provider"`
	Enabled            bool            `json:"enabled" bson:"enabled"`
	CtrlhubBaseURL      string          `json:"ctrlhub_base_url" bson:"ctrlhub_base_url"`
	SDNScheme           string          `json:"sdn_scheme" bson:"sdn_scheme"`
	SDNHost             string          `json:"sdn_host" bson:"sdn_host"`
	SDNPort             int             `json:"sdn_port,omitempty" bson:"sdn_port,omitempty"`
	CredentialRef       string          `json:"credential_ref" bson:"credential_ref"`
	InsecureSkipVerify  bool            `json:"insecure_skip_verify" bson:"insecure_skip_verify"`
	TimeoutSeconds      int             `json:"timeout_seconds,omitempty" bson:"timeout_seconds,omitempty"`
	Area                string          `json:"area,omitempty" bson:"area,omitempty"`
	Site                string          `json:"site,omitempty" bson:"site,omitempty"`
	Tenant              string          `json:"tenant,omitempty" bson:"tenant,omitempty"`
	Description         string          `json:"description,omitempty" bson:"description,omitempty"`
	LastSyncStatus      SyncStatus      `json:"last_sync_status" bson:"last_sync_status"`
	LastSyncAt          *time.Time      `json:"last_sync_at,omitempty" bson:"last_sync_at,omitempty"`
	LastSuccessAt       *time.Time      `json:"last_success_at,omitempty" bson:"last_success_at,omitempty"`
	LastError           string          `json:"last_error,omitempty" bson:"last_error,omitempty"`
	LastSummary         ResourceSummary `json:"last_summary" bson:"last_summary"`
	CreatedAt           time.Time       `json:"created_at" bson:"created_at"`
	UpdatedAt           time.Time       `json:"updated_at" bson:"updated_at"`
}

type ControllerConfigRequest struct {
	Name              string   `json:"name"`
	Provider          Provider `json:"provider"`
	Enabled           bool     `json:"enabled"`
	CtrlhubBaseURL     string   `json:"ctrlhub_base_url"`
	SDNScheme          string   `json:"sdn_scheme"`
	SDNHost            string   `json:"sdn_host"`
	SDNPort            int      `json:"sdn_port,omitempty"`
	CredentialRef      string   `json:"credential_ref"`
	InsecureSkipVerify bool     `json:"insecure_skip_verify"`
	TimeoutSeconds     int      `json:"timeout_seconds,omitempty"`
	Area               string   `json:"area,omitempty"`
	Site               string   `json:"site,omitempty"`
	Tenant             string   `json:"tenant,omitempty"`
	Description        string   `json:"description,omitempty"`
}

type Resource struct {
	ID           string         `json:"id" bson:"id"`
	Name         string         `json:"name" bson:"name"`
	Provider     Provider       `json:"provider" bson:"provider"`
	ProviderType string         `json:"provider_type" bson:"provider_type"`
	DN           string         `json:"dn" bson:"dn"`
	Tenant       string         `json:"tenant" bson:"tenant"`
	Attributes   map[string]any `json:"attributes" bson:"attributes"`
	Raw          any            `json:"raw,omitempty" bson:"raw,omitempty"`
}

type Snapshot struct {
	Provider     Provider         `json:"provider" bson:"provider"`
	CollectedAt  time.Time        `json:"collected_at" bson:"collected_at"`
	Tenants      []Resource       `json:"tenants" bson:"tenants"`
	VRFs         []Resource       `json:"vrfs" bson:"vrfs"`
	Networks     []Resource       `json:"networks" bson:"networks"`
	Subnets      []Resource       `json:"subnets" bson:"subnets"`
	Applications []Resource       `json:"applications" bson:"applications"`
	Segments     []Resource       `json:"segments" bson:"segments"`
	Endpoints    []Resource       `json:"endpoints" bson:"endpoints"`
	Switches     []Resource       `json:"switches" bson:"switches"`
	Ports        []Resource       `json:"ports" bson:"ports"`
	Contracts    []Resource       `json:"contracts" bson:"contracts"`
	Filters      []Resource       `json:"filters" bson:"filters"`
	Metadata     SnapshotMetadata `json:"metadata" bson:"metadata"`
}

type SnapshotMetadata struct {
	Source          string `json:"source" bson:"source"`
	ProviderVersion string `json:"provider_version" bson:"provider_version"`
}

type SnapshotResponse struct {
	Provider    Provider         `json:"provider"`
	CollectedAt time.Time        `json:"collected_at"`
	DurationMS  int64            `json:"duration_ms"`
	Snapshot    Snapshot         `json:"snapshot"`
	Metadata    SnapshotMetadata `json:"metadata"`
}

type SnapshotRecord struct {
	ID              string          `json:"id" bson:"id"`
	ControllerID    string          `json:"controller_id" bson:"controller_id"`
	Provider        Provider        `json:"provider" bson:"provider"`
	CollectedAt     time.Time       `json:"collected_at" bson:"collected_at"`
	SyncedAt        time.Time       `json:"synced_at" bson:"synced_at"`
	DurationMS      int64           `json:"duration_ms" bson:"duration_ms"`
	Status          SyncStatus      `json:"status" bson:"status"`
	ErrorSummary    string          `json:"error_summary,omitempty" bson:"error_summary,omitempty"`
	ResourceSummary ResourceSummary `json:"resource_summary" bson:"resource_summary"`
	Snapshot        *Snapshot       `json:"snapshot,omitempty" bson:"snapshot,omitempty"`
	Metadata        SnapshotMetadata `json:"metadata" bson:"metadata"`
}

type ResourceSummary struct {
	Tenants   int `json:"tenants" bson:"tenants"`
	VRFs      int `json:"vrfs" bson:"vrfs"`
	Networks  int `json:"networks" bson:"networks"`
	Subnets   int `json:"subnets" bson:"subnets"`
	Segments  int `json:"segments" bson:"segments"`
	Endpoints int `json:"endpoints" bson:"endpoints"`
	Switches  int `json:"switches" bson:"switches"`
	Ports     int `json:"ports" bson:"ports"`
	Contracts int `json:"contracts" bson:"contracts"`
	Filters   int `json:"filters" bson:"filters"`
	Total     int `json:"total" bson:"total"`
}

func NormalizeProvider(raw string) (Provider, error) {
	switch Provider(strings.ToLower(strings.TrimSpace(raw))) {
	case ProviderACI:
		return ProviderACI, nil
	case ProviderHuawei:
		return ProviderHuawei, nil
	default:
		return "", fmt.Errorf("unsupported provider %q", raw)
	}
}

func ValidateControllerConfig(cfg ControllerConfig) error {
	if strings.TrimSpace(cfg.Name) == "" {
		return fmt.Errorf("name is required")
	}
	if _, err := NormalizeProvider(string(cfg.Provider)); err != nil {
		return err
	}
	if strings.TrimSpace(cfg.CtrlhubBaseURL) == "" {
		return fmt.Errorf("ctrlhub_base_url is required")
	}
	if _, err := url.ParseRequestURI(strings.TrimSpace(cfg.CtrlhubBaseURL)); err != nil {
		return fmt.Errorf("ctrlhub_base_url is invalid: %w", err)
	}
	scheme := strings.ToLower(strings.TrimSpace(cfg.SDNScheme))
	if scheme == "" {
		scheme = "https"
	}
	if scheme != "http" && scheme != "https" {
		return fmt.Errorf("sdn_scheme must be http or https")
	}
	if strings.TrimSpace(cfg.SDNHost) == "" {
		return fmt.Errorf("sdn_host is required")
	}
	if strings.TrimSpace(cfg.CredentialRef) == "" {
		return fmt.Errorf("credential_ref is required")
	}
	return nil
}

func BuildSummary(snapshot Snapshot) ResourceSummary {
	summary := ResourceSummary{
		Tenants:   len(snapshot.Tenants),
		VRFs:      len(snapshot.VRFs),
		Networks:  len(snapshot.Networks),
		Subnets:   len(snapshot.Subnets),
		Segments:  len(snapshot.Segments),
		Endpoints: len(snapshot.Endpoints),
		Switches:  len(snapshot.Switches),
		Ports:     len(snapshot.Ports),
		Contracts: len(snapshot.Contracts),
		Filters:   len(snapshot.Filters),
	}
	summary.Total = summary.Tenants + summary.VRFs + summary.Networks + summary.Subnets +
		summary.Segments + summary.Endpoints + summary.Switches + summary.Ports +
		summary.Contracts + summary.Filters
	return summary
}
```

- [ ] **Step 4: Run tests and verify they pass**

Run:

```bash
cd /Users/huangliang/project/OneOPS-ALL/agent
go test ./pkg/controller/sdn -run 'TestValidateControllerConfigRequiresCoreFields|TestBuildSummaryCountsAllNormalizedResourceGroups' -count=1
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
cd /Users/huangliang/project/OneOPS-ALL/agent
git add pkg/controller/sdn/model.go pkg/controller/sdn/service_test.go
git commit -m "feat: add sdn controller domain models"
```

---

## Task 2: Backend Ctrlhub Snapshot Client

**Files:**
- Create: `/Users/huangliang/project/OneOPS-ALL/agent/pkg/controller/sdn/client.go`
- Test: `/Users/huangliang/project/OneOPS-ALL/agent/pkg/controller/sdn/client_test.go`

- [ ] **Step 1: Write failing client tests**

Create `pkg/controller/sdn/client_test.go`:

```go
package sdn

import (
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
)

func TestCtrlhubClientCollectSnapshotPostsExpectedPayload(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost || r.URL.Path != "/api/v1/sdn/snapshot" {
			t.Fatalf("unexpected request %s %s", r.Method, r.URL.Path)
		}
		var payload map[string]any
		if err := json.NewDecoder(r.Body).Decode(&payload); err != nil {
			t.Fatalf("decode payload: %v", err)
		}
		if payload["provider"] != "aci" {
			t.Fatalf("provider = %#v", payload["provider"])
		}
		endpoint := payload["endpoint"].(map[string]any)
		if endpoint["password"] != "unit-test-password" {
			t.Fatalf("password not sent to ctrlhub endpoint payload")
		}
		writeCtrlhubTestJSON(t, w, map[string]any{
			"success": true,
			"message": "ok",
			"data": map[string]any{
				"provider": "aci",
				"duration_ms": 7,
				"collected_at": "2026-06-20T00:00:00Z",
				"metadata": map[string]any{"source": "controller"},
				"snapshot": map[string]any{
					"provider": "aci",
					"collected_at": "2026-06-20T00:00:00Z",
					"tenants": []map[string]any{{"name": "TenantA"}},
					"vrfs": []map[string]any{},
					"networks": []map[string]any{},
					"subnets": []map[string]any{},
					"applications": []map[string]any{},
					"segments": []map[string]any{},
					"endpoints": []map[string]any{},
					"switches": []map[string]any{},
					"ports": []map[string]any{},
					"contracts": []map[string]any{},
					"filters": []map[string]any{},
					"metadata": map[string]any{"source": "controller"},
				},
			},
		})
	}))
	defer server.Close()

	client := NewCtrlhubClient(server.URL, server.Client())
	resp, err := client.CollectSnapshot(context.Background(), SnapshotRequest{
		Provider: ProviderACI,
		Endpoint: SnapshotEndpoint{
			Scheme: "https", Host: "apic.local", Username: "aci-user", Password: "unit-test-password",
		},
	})
	if err != nil {
		t.Fatalf("CollectSnapshot() error = %v", err)
	}
	if resp.Provider != ProviderACI || len(resp.Snapshot.Tenants) != 1 {
		t.Fatalf("CollectSnapshot() = %+v", resp)
	}
}

func TestCtrlhubClientSanitizesPasswordOnError(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		http.Error(w, "provider said unit-test-password failed", http.StatusBadGateway)
	}))
	defer server.Close()

	client := NewCtrlhubClient(server.URL, server.Client())
	_, err := client.CollectSnapshot(context.Background(), SnapshotRequest{
		Provider: ProviderACI,
		Endpoint: SnapshotEndpoint{Host: "apic.local", Username: "aci-user", Password: "unit-test-password"},
	})
	if err == nil {
		t.Fatal("CollectSnapshot() expected error")
	}
	if strings.Contains(err.Error(), "unit-test-password") {
		t.Fatalf("error leaked password: %v", err)
	}
}

func writeCtrlhubTestJSON(t *testing.T, w http.ResponseWriter, payload any) {
	t.Helper()
	w.Header().Set("Content-Type", "application/json")
	if err := json.NewEncoder(w).Encode(payload); err != nil {
		t.Fatalf("encode response: %v", err)
	}
}
```

- [ ] **Step 2: Run tests and verify they fail**

Run:

```bash
cd /Users/huangliang/project/OneOPS-ALL/agent
go test ./pkg/controller/sdn -run 'TestCtrlhubClient' -count=1
```

Expected: FAIL because `NewCtrlhubClient`, `SnapshotRequest`, and `SnapshotEndpoint` do not exist.

- [ ] **Step 3: Add ctrlhub client implementation**

Add these types to `model.go`:

```go
type SnapshotEndpoint struct {
	Scheme             string `json:"scheme,omitempty"`
	Host               string `json:"host"`
	Port               int    `json:"port,omitempty"`
	Username           string `json:"username,omitempty"`
	Password           string `json:"password,omitempty"`
	UseHTTPS           bool   `json:"use_https"`
	InsecureSkipVerify bool   `json:"insecure_skip_verify,omitempty"`
	TimeoutSeconds     int    `json:"timeout_seconds,omitempty"`
}

type SnapshotRequest struct {
	Provider   Provider         `json:"provider"`
	Endpoint   SnapshotEndpoint `json:"endpoint"`
	IncludeRaw bool             `json:"include_raw,omitempty"`
	Metadata   SnapshotMetadata `json:"metadata"`
}
```

Create `pkg/controller/sdn/client.go`:

```go
package sdn

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"strings"
	"time"
)

type CtrlhubClient struct {
	baseURL    string
	httpClient *http.Client
}

type ctrlhubEnvelope struct {
	Success bool              `json:"success"`
	Message string            `json:"message"`
	Data    *SnapshotResponse `json:"data"`
	Error   string            `json:"error"`
}

func NewCtrlhubClient(baseURL string, httpClient *http.Client) *CtrlhubClient {
	if httpClient == nil {
		httpClient = &http.Client{Timeout: 30 * time.Second}
	}
	return &CtrlhubClient{baseURL: strings.TrimRight(baseURL, "/"), httpClient: httpClient}
}

func (c *CtrlhubClient) CollectSnapshot(ctx context.Context, req SnapshotRequest) (*SnapshotResponse, error) {
	body, err := json.Marshal(req)
	if err != nil {
		return nil, sanitizeErr(err, req.Endpoint.Password)
	}
	httpReq, err := http.NewRequestWithContext(ctx, http.MethodPost, c.baseURL+"/api/v1/sdn/snapshot", bytes.NewReader(body))
	if err != nil {
		return nil, sanitizeErr(err, req.Endpoint.Password)
	}
	httpReq.Header.Set("Content-Type", "application/json")
	httpReq.Header.Set("Accept", "application/json")

	resp, err := c.httpClient.Do(httpReq)
	if err != nil {
		return nil, sanitizeErr(err, req.Endpoint.Password)
	}
	defer resp.Body.Close()

	payload, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, sanitizeErr(err, req.Endpoint.Password)
	}
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return nil, sanitizeErr(fmt.Errorf("ctrlhub snapshot failed with status %d: %s", resp.StatusCode, string(payload)), req.Endpoint.Password)
	}

	var envelope ctrlhubEnvelope
	if err := json.Unmarshal(payload, &envelope); err != nil {
		return nil, sanitizeErr(fmt.Errorf("decode ctrlhub snapshot response: %w", err), req.Endpoint.Password)
	}
	if !envelope.Success {
		msg := envelope.Error
		if msg == "" {
			msg = envelope.Message
		}
		return nil, sanitizeErr(fmt.Errorf("ctrlhub snapshot failed: %s", msg), req.Endpoint.Password)
	}
	if envelope.Data == nil {
		return nil, fmt.Errorf("ctrlhub snapshot response missing data")
	}
	return envelope.Data, nil
}

func sanitizeErr(err error, secrets ...string) error {
	if err == nil {
		return nil
	}
	msg := err.Error()
	for _, secret := range secrets {
		if secret != "" {
			msg = strings.ReplaceAll(msg, secret, "***")
		}
	}
	return fmt.Errorf("%s", msg)
}
```

- [ ] **Step 4: Run tests and verify they pass**

Run:

```bash
cd /Users/huangliang/project/OneOPS-ALL/agent
go test ./pkg/controller/sdn -run 'TestCtrlhubClient' -count=1
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
cd /Users/huangliang/project/OneOPS-ALL/agent
git add pkg/controller/sdn/model.go pkg/controller/sdn/client.go pkg/controller/sdn/client_test.go
git commit -m "feat: add sdn ctrlhub snapshot client"
```

---

## Task 3: Backend Store And Service

**Files:**
- Create: `/Users/huangliang/project/OneOPS-ALL/agent/pkg/controller/sdn/store.go`
- Create: `/Users/huangliang/project/OneOPS-ALL/agent/pkg/controller/sdn/service.go`
- Modify: `/Users/huangliang/project/OneOPS-ALL/agent/pkg/controller/sdn/service_test.go`

- [ ] **Step 1: Write failing service orchestration tests**

Append to `pkg/controller/sdn/service_test.go`:

```go
package sdn

import (
	"context"
	"strings"
	"testing"
	"time"
)

type fakeCredentialResolver struct {
	credential Credential
	err        error
}

func (r fakeCredentialResolver) ResolveCredential(ctx context.Context, ref string) (Credential, error) {
	if r.err != nil {
		return Credential{}, r.err
	}
	return r.credential, nil
}

type fakeSnapshotCollector struct {
	response *SnapshotResponse
	err      error
	request  SnapshotRequest
}

func (c *fakeSnapshotCollector) CollectSnapshot(ctx context.Context, req SnapshotRequest) (*SnapshotResponse, error) {
	c.request = req
	if c.err != nil {
		return nil, c.err
	}
	return c.response, nil
}

func TestServiceSyncStoresSnapshotAndUpdatesControllerStatus(t *testing.T) {
	store := NewMemoryStore()
	cfg := ControllerConfig{
		ID: "sdn-1", Name: "ACI", Provider: ProviderACI, Enabled: true,
		CtrlhubBaseURL: "http://ctrlhub.local:8081", SDNScheme: "https", SDNHost: "apic.local",
		CredentialRef: "secret-aci", LastSyncStatus: SyncStatusNeverSynced,
	}
	if err := store.CreateController(context.Background(), cfg); err != nil {
		t.Fatalf("CreateController() error = %v", err)
	}

	collector := &fakeSnapshotCollector{response: &SnapshotResponse{
		Provider: ProviderACI,
		CollectedAt: time.Date(2026, 6, 20, 0, 0, 0, 0, time.UTC),
		DurationMS: 9,
		Snapshot: Snapshot{Provider: ProviderACI, Tenants: []Resource{{Name: "TenantA"}}},
	}}
	svc := NewService(store, fakeCredentialResolver{credential: Credential{Username: "u", Password: "p"}}, collector)

	result, err := svc.SyncController(context.Background(), "sdn-1")
	if err != nil {
		t.Fatalf("SyncController() error = %v", err)
	}
	if !result.Success || result.Summary.Tenants != 1 || result.Summary.Total != 1 {
		t.Fatalf("SyncController() = %+v", result)
	}
	if collector.request.Endpoint.Password != "p" || collector.request.Endpoint.Username != "u" {
		t.Fatalf("collector request endpoint = %+v", collector.request.Endpoint)
	}

	updated, err := store.GetController(context.Background(), "sdn-1")
	if err != nil {
		t.Fatalf("GetController() error = %v", err)
	}
	if updated.LastSyncStatus != SyncStatusSuccess || updated.LastSuccessAt == nil {
		t.Fatalf("updated controller = %+v", updated)
	}
	latest, err := store.GetLatestSnapshot(context.Background(), "sdn-1")
	if err != nil {
		t.Fatalf("GetLatestSnapshot() error = %v", err)
	}
	if latest.ResourceSummary.Tenants != 1 || latest.Snapshot == nil {
		t.Fatalf("latest snapshot = %+v", latest)
	}
}

func TestServiceSyncFailureSanitizesPassword(t *testing.T) {
	store := NewMemoryStore()
	cfg := ControllerConfig{
		ID: "sdn-1", Name: "ACI", Provider: ProviderACI, Enabled: true,
		CtrlhubBaseURL: "http://ctrlhub.local:8081", SDNScheme: "https", SDNHost: "apic.local",
		CredentialRef: "secret-aci", LastSyncStatus: SyncStatusNeverSynced,
	}
	if err := store.CreateController(context.Background(), cfg); err != nil {
		t.Fatalf("CreateController() error = %v", err)
	}

	svc := NewService(
		store,
		fakeCredentialResolver{credential: Credential{Username: "u", Password: "unit-test-password"}},
		&fakeSnapshotCollector{err: assertErr("provider failed unit-test-password")},
	)

	result, err := svc.SyncController(context.Background(), "sdn-1")
	if err == nil {
		t.Fatal("SyncController() expected error")
	}
	if result.Success {
		t.Fatalf("SyncController() result = %+v", result)
	}
	updated, _ := store.GetController(context.Background(), "sdn-1")
	if strings.Contains(updated.LastError, "unit-test-password") {
		t.Fatalf("last error leaked password: %q", updated.LastError)
	}
}

type assertErr string

func (e assertErr) Error() string { return string(e) }
```

- [ ] **Step 2: Run tests and verify they fail**

Run:

```bash
cd /Users/huangliang/project/OneOPS-ALL/agent
go test ./pkg/controller/sdn -run 'TestServiceSync' -count=1
```

Expected: FAIL because store/service interfaces do not exist.

- [ ] **Step 3: Add store and service implementation**

Create `pkg/controller/sdn/store.go`:

```go
package sdn

import (
	"context"
	"fmt"
	"sync"
	"time"

	"go.mongodb.org/mongo-driver/bson"
	"go.mongodb.org/mongo-driver/mongo"
	"go.mongodb.org/mongo-driver/mongo/options"
)

const (
	databaseName              = "controller"
	controllerCollectionName  = "sdn_controllers"
	snapshotCollectionName    = "sdn_snapshots"
)

type Store interface {
	CreateController(ctx context.Context, cfg ControllerConfig) error
	UpdateController(ctx context.Context, cfg ControllerConfig) error
	GetController(ctx context.Context, id string) (ControllerConfig, error)
	ListControllers(ctx context.Context) ([]ControllerConfig, error)
	DeleteController(ctx context.Context, id string) error
	SaveSnapshot(ctx context.Context, record SnapshotRecord) error
	GetLatestSnapshot(ctx context.Context, controllerID string) (SnapshotRecord, error)
	ListSnapshots(ctx context.Context, controllerID string, limit int64) ([]SnapshotRecord, error)
}

type MongoStore struct {
	client *mongo.Client
}

func NewMongoStore(client *mongo.Client) *MongoStore {
	return &MongoStore{client: client}
}

func (s *MongoStore) controllers() *mongo.Collection {
	return s.client.Database(databaseName).Collection(controllerCollectionName)
}

func (s *MongoStore) snapshots() *mongo.Collection {
	return s.client.Database(databaseName).Collection(snapshotCollectionName)
}

func (s *MongoStore) CreateController(ctx context.Context, cfg ControllerConfig) error {
	_, err := s.controllers().InsertOne(ctx, cfg)
	return err
}

func (s *MongoStore) UpdateController(ctx context.Context, cfg ControllerConfig) error {
	cfg.UpdatedAt = time.Now().UTC()
	result, err := s.controllers().UpdateOne(ctx, bson.M{"id": cfg.ID}, bson.M{"$set": cfg})
	if err != nil {
		return err
	}
	if result.MatchedCount == 0 {
		return fmt.Errorf("sdn controller %q not found", cfg.ID)
	}
	return nil
}

func (s *MongoStore) GetController(ctx context.Context, id string) (ControllerConfig, error) {
	var cfg ControllerConfig
	err := s.controllers().FindOne(ctx, bson.M{"id": id}).Decode(&cfg)
	return cfg, err
}

func (s *MongoStore) ListControllers(ctx context.Context) ([]ControllerConfig, error) {
	cursor, err := s.controllers().Find(ctx, bson.M{}, options.Find().SetSort(bson.M{"updated_at": -1}))
	if err != nil {
		return nil, err
	}
	defer cursor.Close(ctx)
	var result []ControllerConfig
	if err := cursor.All(ctx, &result); err != nil {
		return nil, err
	}
	return result, nil
}

func (s *MongoStore) DeleteController(ctx context.Context, id string) error {
	result, err := s.controllers().DeleteOne(ctx, bson.M{"id": id})
	if err != nil {
		return err
	}
	if result.DeletedCount == 0 {
		return fmt.Errorf("sdn controller %q not found", id)
	}
	return nil
}

func (s *MongoStore) SaveSnapshot(ctx context.Context, record SnapshotRecord) error {
	_, err := s.snapshots().InsertOne(ctx, record)
	return err
}

func (s *MongoStore) GetLatestSnapshot(ctx context.Context, controllerID string) (SnapshotRecord, error) {
	var record SnapshotRecord
	err := s.snapshots().FindOne(ctx, bson.M{"controller_id": controllerID, "status": SyncStatusSuccess}, options.FindOne().SetSort(bson.M{"synced_at": -1})).Decode(&record)
	return record, err
}

func (s *MongoStore) ListSnapshots(ctx context.Context, controllerID string, limit int64) ([]SnapshotRecord, error) {
	if limit <= 0 {
		limit = 20
	}
	cursor, err := s.snapshots().Find(ctx, bson.M{"controller_id": controllerID}, options.Find().SetSort(bson.M{"synced_at": -1}).SetLimit(limit))
	if err != nil {
		return nil, err
	}
	defer cursor.Close(ctx)
	var result []SnapshotRecord
	if err := cursor.All(ctx, &result); err != nil {
		return nil, err
	}
	return result, nil
}

type MemoryStore struct {
	mu          sync.RWMutex
	controllers map[string]ControllerConfig
	snapshots   []SnapshotRecord
}

func NewMemoryStore() *MemoryStore {
	return &MemoryStore{controllers: map[string]ControllerConfig{}, snapshots: []SnapshotRecord{}}
}

func (s *MemoryStore) CreateController(ctx context.Context, cfg ControllerConfig) error {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.controllers[cfg.ID] = cfg
	return nil
}

func (s *MemoryStore) UpdateController(ctx context.Context, cfg ControllerConfig) error {
	s.mu.Lock()
	defer s.mu.Unlock()
	if _, ok := s.controllers[cfg.ID]; !ok {
		return fmt.Errorf("sdn controller %q not found", cfg.ID)
	}
	s.controllers[cfg.ID] = cfg
	return nil
}

func (s *MemoryStore) GetController(ctx context.Context, id string) (ControllerConfig, error) {
	s.mu.RLock()
	defer s.mu.RUnlock()
	cfg, ok := s.controllers[id]
	if !ok {
		return ControllerConfig{}, fmt.Errorf("sdn controller %q not found", id)
	}
	return cfg, nil
}

func (s *MemoryStore) ListControllers(ctx context.Context) ([]ControllerConfig, error) {
	s.mu.RLock()
	defer s.mu.RUnlock()
	result := make([]ControllerConfig, 0, len(s.controllers))
	for _, cfg := range s.controllers {
		result = append(result, cfg)
	}
	return result, nil
}

func (s *MemoryStore) DeleteController(ctx context.Context, id string) error {
	s.mu.Lock()
	defer s.mu.Unlock()
	delete(s.controllers, id)
	return nil
}

func (s *MemoryStore) SaveSnapshot(ctx context.Context, record SnapshotRecord) error {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.snapshots = append(s.snapshots, record)
	return nil
}

func (s *MemoryStore) GetLatestSnapshot(ctx context.Context, controllerID string) (SnapshotRecord, error) {
	s.mu.RLock()
	defer s.mu.RUnlock()
	for i := len(s.snapshots) - 1; i >= 0; i-- {
		if s.snapshots[i].ControllerID == controllerID && s.snapshots[i].Status == SyncStatusSuccess {
			return s.snapshots[i], nil
		}
	}
	return SnapshotRecord{}, fmt.Errorf("latest snapshot for controller %q not found", controllerID)
}

func (s *MemoryStore) ListSnapshots(ctx context.Context, controllerID string, limit int64) ([]SnapshotRecord, error) {
	s.mu.RLock()
	defer s.mu.RUnlock()
	result := []SnapshotRecord{}
	for i := len(s.snapshots) - 1; i >= 0; i-- {
		if s.snapshots[i].ControllerID == controllerID {
			result = append(result, s.snapshots[i])
			if limit > 0 && int64(len(result)) >= limit {
				break
			}
		}
	}
	return result, nil
}
```

Create `pkg/controller/sdn/service.go`:

```go
package sdn

import (
	"context"
	"fmt"
	"strings"
	"time"

	"github.com/gofrs/uuid"
)

type Credential struct {
	Username string
	Password string
	Token    string
}

type CredentialResolver interface {
	ResolveCredential(ctx context.Context, ref string) (Credential, error)
}

type SnapshotCollector interface {
	CollectSnapshot(ctx context.Context, req SnapshotRequest) (*SnapshotResponse, error)
}

type Service struct {
	store      Store
	resolver   CredentialResolver
	collector  SnapshotCollector
}

type SyncResult struct {
	Success      bool            `json:"success"`
	ControllerID string          `json:"controller_id"`
	Provider     Provider        `json:"provider"`
	Status       SyncStatus      `json:"status"`
	Summary      ResourceSummary `json:"summary"`
	Error        string          `json:"error,omitempty"`
	DurationMS   int64           `json:"duration_ms,omitempty"`
	SyncedAt     time.Time       `json:"synced_at"`
}

func NewService(store Store, resolver CredentialResolver, collector SnapshotCollector) *Service {
	return &Service{store: store, resolver: resolver, collector: collector}
}

func (s *Service) CreateController(ctx context.Context, req ControllerConfigRequest) (ControllerConfig, error) {
	now := time.Now().UTC()
	id, err := uuid.NewV4()
	if err != nil {
		return ControllerConfig{}, err
	}
	cfg := requestToConfig(req)
	cfg.ID = id.String()
	cfg.LastSyncStatus = SyncStatusNeverSynced
	cfg.CreatedAt = now
	cfg.UpdatedAt = now
	if err := ValidateControllerConfig(cfg); err != nil {
		return ControllerConfig{}, err
	}
	if err := s.store.CreateController(ctx, cfg); err != nil {
		return ControllerConfig{}, err
	}
	return cfg, nil
}

func (s *Service) UpdateController(ctx context.Context, id string, req ControllerConfigRequest) (ControllerConfig, error) {
	existing, err := s.store.GetController(ctx, id)
	if err != nil {
		return ControllerConfig{}, err
	}
	updated := requestToConfig(req)
	updated.ID = id
	updated.CreatedAt = existing.CreatedAt
	updated.UpdatedAt = time.Now().UTC()
	updated.LastSyncStatus = existing.LastSyncStatus
	updated.LastSyncAt = existing.LastSyncAt
	updated.LastSuccessAt = existing.LastSuccessAt
	updated.LastError = existing.LastError
	updated.LastSummary = existing.LastSummary
	if err := ValidateControllerConfig(updated); err != nil {
		return ControllerConfig{}, err
	}
	if err := s.store.UpdateController(ctx, updated); err != nil {
		return ControllerConfig{}, err
	}
	return updated, nil
}

func (s *Service) ListControllers(ctx context.Context) ([]ControllerConfig, error) {
	return s.store.ListControllers(ctx)
}

func (s *Service) GetController(ctx context.Context, id string) (ControllerConfig, error) {
	return s.store.GetController(ctx, id)
}

func (s *Service) DeleteController(ctx context.Context, id string) error {
	return s.store.DeleteController(ctx, id)
}

func (s *Service) TestController(ctx context.Context, id string) (SyncResult, error) {
	cfg, err := s.store.GetController(ctx, id)
	if err != nil {
		return SyncResult{}, err
	}
	resp, cred, err := s.collect(ctx, cfg)
	if err != nil {
		return SyncResult{Success: false, ControllerID: id, Provider: cfg.Provider, Status: SyncStatusFailed, Error: sanitizeText(err.Error(), cred.Password), SyncedAt: time.Now().UTC()}, err
	}
	return SyncResult{Success: true, ControllerID: id, Provider: cfg.Provider, Status: SyncStatusSuccess, Summary: BuildSummary(resp.Snapshot), DurationMS: resp.DurationMS, SyncedAt: time.Now().UTC()}, nil
}

func (s *Service) SyncController(ctx context.Context, id string) (SyncResult, error) {
	cfg, err := s.store.GetController(ctx, id)
	if err != nil {
		return SyncResult{}, err
	}
	resp, cred, err := s.collect(ctx, cfg)
	now := time.Now().UTC()
	if err != nil {
		safeErr := sanitizeText(err.Error(), cred.Password)
		cfg.LastSyncStatus = SyncStatusFailed
		cfg.LastSyncAt = &now
		cfg.LastError = safeErr
		_ = s.store.UpdateController(ctx, cfg)
		record := SnapshotRecord{ID: newID(), ControllerID: id, Provider: cfg.Provider, SyncedAt: now, Status: SyncStatusFailed, ErrorSummary: safeErr}
		_ = s.store.SaveSnapshot(ctx, record)
		return SyncResult{Success: false, ControllerID: id, Provider: cfg.Provider, Status: SyncStatusFailed, Error: safeErr, SyncedAt: now}, err
	}
	summary := BuildSummary(resp.Snapshot)
	record := SnapshotRecord{
		ID: newID(), ControllerID: id, Provider: cfg.Provider, CollectedAt: resp.CollectedAt,
		SyncedAt: now, DurationMS: resp.DurationMS, Status: SyncStatusSuccess,
		ResourceSummary: summary, Snapshot: &resp.Snapshot, Metadata: resp.Metadata,
	}
	if err := s.store.SaveSnapshot(ctx, record); err != nil {
		return SyncResult{}, err
	}
	cfg.LastSyncStatus = SyncStatusSuccess
	cfg.LastSyncAt = &now
	cfg.LastSuccessAt = &now
	cfg.LastError = ""
	cfg.LastSummary = summary
	if err := s.store.UpdateController(ctx, cfg); err != nil {
		return SyncResult{}, err
	}
	return SyncResult{Success: true, ControllerID: id, Provider: cfg.Provider, Status: SyncStatusSuccess, Summary: summary, DurationMS: resp.DurationMS, SyncedAt: now}, nil
}

func (s *Service) LatestSnapshot(ctx context.Context, id string) (SnapshotRecord, error) {
	return s.store.GetLatestSnapshot(ctx, id)
}

func (s *Service) SnapshotHistory(ctx context.Context, id string, limit int64) ([]SnapshotRecord, error) {
	return s.store.ListSnapshots(ctx, id, limit)
}

func (s *Service) collect(ctx context.Context, cfg ControllerConfig) (*SnapshotResponse, Credential, error) {
	cred, err := s.resolver.ResolveCredential(ctx, cfg.CredentialRef)
	if err != nil {
		return nil, cred, err
	}
	resp, err := s.collector.CollectSnapshot(ctx, SnapshotRequest{
		Provider: cfg.Provider,
		Endpoint: SnapshotEndpoint{
			Scheme: cfg.SDNScheme, Host: cfg.SDNHost, Port: cfg.SDNPort,
			Username: cred.Username, Password: credentialPassword(cred),
			UseHTTPS: strings.EqualFold(cfg.SDNScheme, "https"),
			InsecureSkipVerify: cfg.InsecureSkipVerify,
			TimeoutSeconds: cfg.TimeoutSeconds,
		},
		IncludeRaw: false,
		Metadata: SnapshotMetadata{Source: "oneops"},
	})
	return resp, cred, err
}

func requestToConfig(req ControllerConfigRequest) ControllerConfig {
	return ControllerConfig{
		Name: strings.TrimSpace(req.Name), Provider: req.Provider, Enabled: req.Enabled,
		CtrlhubBaseURL: strings.TrimSpace(req.CtrlhubBaseURL),
		SDNScheme: strings.TrimSpace(req.SDNScheme), SDNHost: strings.TrimSpace(req.SDNHost),
		SDNPort: req.SDNPort, CredentialRef: strings.TrimSpace(req.CredentialRef),
		InsecureSkipVerify: req.InsecureSkipVerify, TimeoutSeconds: req.TimeoutSeconds,
		Area: strings.TrimSpace(req.Area), Site: strings.TrimSpace(req.Site),
		Tenant: strings.TrimSpace(req.Tenant), Description: strings.TrimSpace(req.Description),
	}
}

func credentialPassword(cred Credential) string {
	if cred.Password != "" {
		return cred.Password
	}
	return cred.Token
}

func sanitizeText(text string, secrets ...string) string {
	for _, secret := range secrets {
		if secret != "" {
			text = strings.ReplaceAll(text, secret, "***")
		}
	}
	return text
}

func newID() string {
	id, err := uuid.NewV4()
	if err != nil {
		return fmt.Sprintf("sdn-%d", time.Now().UnixNano())
	}
	return id.String()
}
```

- [ ] **Step 4: Run service tests**

Run:

```bash
cd /Users/huangliang/project/OneOPS-ALL/agent
gofmt -w pkg/controller/sdn/*.go
go test ./pkg/controller/sdn -count=1
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
cd /Users/huangliang/project/OneOPS-ALL/agent
git add pkg/controller/sdn
git commit -m "feat: add sdn controller snapshot service"
```

---

## Task 4: Backend HTTP API Handlers

**Files:**
- Create: `/Users/huangliang/project/OneOPS-ALL/agent/pkg/controller/api/sdn.go`
- Create: `/Users/huangliang/project/OneOPS-ALL/agent/pkg/controller/api/sdn_test.go`

- [ ] **Step 1: Write failing handler tests**

Create `pkg/controller/api/sdn_test.go`:

```go
package api

import (
	"bytes"
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/gorilla/mux"
	ctrlsdn "github.com/netxops/agent/pkg/controller/sdn"
	"go.uber.org/zap"
)

func TestSDNCreateControllerRejectsMissingHost(t *testing.T) {
	api := NewSDNAPI(ctrlsdn.NewService(ctrlsdn.NewMemoryStore(), fakeAPIResolver{}, fakeAPICollector{}), zap.NewNop())
	body := []byte(`{"name":"ACI","provider":"aci","ctrlhub_base_url":"http://ctrlhub","credential_ref":"secret"}`)
	req := httptest.NewRequest(http.MethodPost, "/api/v1/sdn/controllers", bytes.NewReader(body))
	rec := httptest.NewRecorder()

	api.CreateController(rec, req)

	if rec.Code != http.StatusBadRequest {
		t.Fatalf("status=%d body=%s", rec.Code, rec.Body.String())
	}
}

func TestSDNCreateAndSyncController(t *testing.T) {
	store := ctrlsdn.NewMemoryStore()
	api := NewSDNAPI(ctrlsdn.NewService(store, fakeAPIResolver{credential: ctrlsdn.Credential{Username: "u", Password: "p"}}, fakeAPICollector{
		response: &ctrlsdn.SnapshotResponse{
			Provider: ctrlsdn.ProviderACI,
			Snapshot: ctrlsdn.Snapshot{Provider: ctrlsdn.ProviderACI, Tenants: []ctrlsdn.Resource{{Name: "TenantA"}}},
		},
	}), zap.NewNop())

	createBody := []byte(`{"name":"ACI","provider":"aci","enabled":true,"ctrlhub_base_url":"http://ctrlhub","sdn_scheme":"https","sdn_host":"apic.local","credential_ref":"secret"}`)
	createReq := httptest.NewRequest(http.MethodPost, "/api/v1/sdn/controllers", bytes.NewReader(createBody))
	createRec := httptest.NewRecorder()
	api.CreateController(createRec, createReq)
	if createRec.Code != http.StatusOK {
		t.Fatalf("create status=%d body=%s", createRec.Code, createRec.Body.String())
	}

	var createResp struct {
		Data ctrlsdn.ControllerConfig `json:"data"`
	}
	if err := json.Unmarshal(createRec.Body.Bytes(), &createResp); err != nil {
		t.Fatalf("decode create response: %v", err)
	}

	syncReq := httptest.NewRequest(http.MethodPost, "/api/v1/sdn/controllers/"+createResp.Data.ID+"/sync", nil)
	syncReq = muxSetVar(syncReq, "id", createResp.Data.ID)
	syncRec := httptest.NewRecorder()
	api.SyncController(syncRec, syncReq)
	if syncRec.Code != http.StatusOK {
		t.Fatalf("sync status=%d body=%s", syncRec.Code, syncRec.Body.String())
	}

	var syncResp struct {
		Data ctrlsdn.SyncResult `json:"data"`
	}
	if err := json.Unmarshal(syncRec.Body.Bytes(), &syncResp); err != nil {
		t.Fatalf("decode sync response: %v", err)
	}
	if syncResp.Data.Summary.Tenants != 1 {
		t.Fatalf("sync response = %+v", syncResp)
	}
}

type fakeAPIResolver struct {
	credential ctrlsdn.Credential
}

func (r fakeAPIResolver) ResolveCredential(ctx context.Context, ref string) (ctrlsdn.Credential, error) {
	return r.credential, nil
}

type fakeAPICollector struct {
	response *ctrlsdn.SnapshotResponse
}

func (c fakeAPICollector) CollectSnapshot(ctx context.Context, req ctrlsdn.SnapshotRequest) (*ctrlsdn.SnapshotResponse, error) {
	return c.response, nil
}

func muxSetVar(req *http.Request, key, value string) *http.Request {
	return mux.SetURLVars(req, map[string]string{key: value})
}
```

- [ ] **Step 2: Run tests and verify they fail**

Run:

```bash
cd /Users/huangliang/project/OneOPS-ALL/agent
go test ./pkg/controller/api -run 'TestSDN' -count=1
```

Expected: FAIL because `NewSDNAPI` and handlers do not exist.

- [ ] **Step 3: Implement API handlers**

Create `pkg/controller/api/sdn.go`:

```go
package api

import (
	"encoding/json"
	"net/http"
	"strconv"

	"github.com/gorilla/mux"
	ctrlsdn "github.com/netxops/agent/pkg/controller/sdn"
	"go.uber.org/zap"
)

type SDNAPI struct {
	service *ctrlsdn.Service
	logger  *zap.Logger
}

type sdnEnvelope struct {
	Success bool        `json:"success"`
	Message string      `json:"message"`
	Data    interface{} `json:"data,omitempty"`
	Error   string      `json:"error,omitempty"`
}

func NewSDNAPI(service *ctrlsdn.Service, logger *zap.Logger) *SDNAPI {
	if logger == nil {
		logger = zap.NewNop()
	}
	return &SDNAPI{service: service, logger: logger}
}

func (api *SDNAPI) ListControllers(w http.ResponseWriter, r *http.Request) {
	items, err := api.service.ListControllers(r.Context())
	api.write(w, err, items, "sdn controllers listed")
}

func (api *SDNAPI) CreateController(w http.ResponseWriter, r *http.Request) {
	var req ctrlsdn.ControllerConfigRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		api.writeError(w, http.StatusBadRequest, "invalid request body", err)
		return
	}
	item, err := api.service.CreateController(r.Context(), req)
	api.write(w, err, item, "sdn controller created")
}

func (api *SDNAPI) GetController(w http.ResponseWriter, r *http.Request) {
	item, err := api.service.GetController(r.Context(), mux.Vars(r)["id"])
	api.write(w, err, item, "sdn controller loaded")
}

func (api *SDNAPI) UpdateController(w http.ResponseWriter, r *http.Request) {
	var req ctrlsdn.ControllerConfigRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		api.writeError(w, http.StatusBadRequest, "invalid request body", err)
		return
	}
	item, err := api.service.UpdateController(r.Context(), mux.Vars(r)["id"], req)
	api.write(w, err, item, "sdn controller updated")
}

func (api *SDNAPI) DeleteController(w http.ResponseWriter, r *http.Request) {
	err := api.service.DeleteController(r.Context(), mux.Vars(r)["id"])
	api.write(w, err, map[string]string{"id": mux.Vars(r)["id"]}, "sdn controller deleted")
}

func (api *SDNAPI) TestController(w http.ResponseWriter, r *http.Request) {
	result, err := api.service.TestController(r.Context(), mux.Vars(r)["id"])
	api.write(w, err, result, "sdn controller tested")
}

func (api *SDNAPI) SyncController(w http.ResponseWriter, r *http.Request) {
	result, err := api.service.SyncController(r.Context(), mux.Vars(r)["id"])
	api.write(w, err, result, "sdn snapshot synced")
}

func (api *SDNAPI) LatestSnapshot(w http.ResponseWriter, r *http.Request) {
	record, err := api.service.LatestSnapshot(r.Context(), mux.Vars(r)["id"])
	api.write(w, err, record, "sdn latest snapshot loaded")
}

func (api *SDNAPI) SnapshotHistory(w http.ResponseWriter, r *http.Request) {
	limit, _ := strconv.ParseInt(r.URL.Query().Get("limit"), 10, 64)
	records, err := api.service.SnapshotHistory(r.Context(), mux.Vars(r)["id"], limit)
	api.write(w, err, records, "sdn snapshot history loaded")
}

func (api *SDNAPI) write(w http.ResponseWriter, err error, data interface{}, message string) {
	if err != nil {
		api.writeError(w, http.StatusBadRequest, "sdn request failed", err)
		return
	}
	w.Header().Set("Content-Type", "application/json")
	_ = json.NewEncoder(w).Encode(sdnEnvelope{Success: true, Message: message, Data: data})
}

func (api *SDNAPI) writeError(w http.ResponseWriter, status int, message string, err error) {
	api.logger.Warn("sdn api request failed", zap.String("message", message), zap.Error(err))
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(sdnEnvelope{Success: false, Message: message, Error: err.Error()})
}

```

- [ ] **Step 4: Run handler tests**

Run:

```bash
cd /Users/huangliang/project/OneOPS-ALL/agent
gofmt -w pkg/controller/api/sdn.go pkg/controller/api/sdn_test.go
go test ./pkg/controller/api -run 'TestSDN' -count=1
```

Expected: PASS for API tests.

- [ ] **Step 5: Commit**

Commit only API files:

```bash
cd /Users/huangliang/project/OneOPS-ALL/agent
git add pkg/controller/api/sdn.go pkg/controller/api/sdn_test.go
git commit -m "feat: add sdn controller api handlers"
```

---

## Task 5: Backend Credential Resolver And Production Wiring

**Files:**
- Modify: `/Users/huangliang/project/OneOPS-ALL/agent/pkg/controller/sdn/service.go`
- Create: `/Users/huangliang/project/OneOPS-ALL/agent/pkg/controller/sdn/credential.go`
- Modify: `/Users/huangliang/project/OneOPS-ALL/agent/cmd/controller/main.go`
- Test: `/Users/huangliang/project/OneOPS-ALL/agent/pkg/controller/sdn/service_test.go`

- [ ] **Step 1: Write failing resolver tests**

Append to `pkg/controller/sdn/service_test.go`:

```go
func TestCredentialFromSecretDocumentUsesPasswordOrToken(t *testing.T) {
	passwordDoc := map[string]any{"code": "secret-1", "username": "user", "plain_text": "pass"}
	cred := credentialFromSecretDocument(passwordDoc)
	if cred.Username != "user" || cred.Password != "pass" {
		t.Fatalf("credentialFromSecretDocument(password) = %+v", cred)
	}

	tokenDoc := map[string]any{"code": "secret-2", "username": "token-user", "token": "api-token"}
	cred = credentialFromSecretDocument(tokenDoc)
	if cred.Username != "token-user" || cred.Token != "api-token" {
		t.Fatalf("credentialFromSecretDocument(token) = %+v", cred)
	}
}
```

- [ ] **Step 2: Run test and verify it fails**

Run:

```bash
cd /Users/huangliang/project/OneOPS-ALL/agent
go test ./pkg/controller/sdn -run TestCredentialFromSecretDocumentUsesPasswordOrToken -count=1
```

Expected: FAIL because helper does not exist.

- [ ] **Step 3: Implement credential resolver**

Create `pkg/controller/sdn/credential.go`:

```go
package sdn

import (
	"context"
	"fmt"

	"go.mongodb.org/mongo-driver/bson"
	"go.mongodb.org/mongo-driver/mongo"
)

type SecretCredentialResolver struct {
	client *mongo.Client
}

func NewSecretCredentialResolver(client *mongo.Client) *SecretCredentialResolver {
	return &SecretCredentialResolver{client: client}
}

func (r *SecretCredentialResolver) ResolveCredential(ctx context.Context, ref string) (Credential, error) {
	if r.client == nil {
		return Credential{}, fmt.Errorf("mongo client is required to resolve credential %q", ref)
	}
	var doc map[string]any
	err := r.client.Database("controller").Collection("secrets").FindOne(ctx, bson.M{"code": ref}).Decode(&doc)
	if err != nil {
		err = r.client.Database("controller").Collection("setting_secrets").FindOne(ctx, bson.M{"code": ref}).Decode(&doc)
	}
	if err != nil {
		return Credential{}, fmt.Errorf("credential %q not found: %w", ref, err)
	}
	cred := credentialFromSecretDocument(doc)
	if cred.Username == "" && cred.Password == "" && cred.Token == "" {
		return Credential{}, fmt.Errorf("credential %q has no usable username/password/token", ref)
	}
	return cred, nil
}

func credentialFromSecretDocument(doc map[string]any) Credential {
	return Credential{
		Username: stringField(doc, "username"),
		Password: firstStringField(doc, "plain_text", "plainText", "password"),
		Token:    firstStringField(doc, "token", "api_token", "apiToken"),
	}
}

func firstStringField(doc map[string]any, keys ...string) string {
	for _, key := range keys {
		if value := stringField(doc, key); value != "" {
			return value
		}
	}
	return ""
}

func stringField(doc map[string]any, key string) string {
	value, ok := doc[key]
	if !ok || value == nil {
		return ""
	}
	typed, ok := value.(string)
	if !ok {
		return fmt.Sprintf("%v", value)
	}
	return typed
}
```

- [ ] **Step 4: Make service create per-controller ctrlhub clients**

Modify `Service.collect` in `service.go`:

```go
collector := s.collector
if collector == nil {
	collector = NewCtrlhubClient(cfg.CtrlhubBaseURL, nil)
}
resp, err := collector.CollectSnapshot(ctx, SnapshotRequest{
	Provider: cfg.Provider,
	Endpoint: SnapshotEndpoint{
		Scheme: cfg.SDNScheme, Host: cfg.SDNHost, Port: cfg.SDNPort,
		Username: cred.Username, Password: credentialPassword(cred),
		UseHTTPS: strings.EqualFold(cfg.SDNScheme, "https"),
		InsecureSkipVerify: cfg.InsecureSkipVerify,
		TimeoutSeconds: cfg.TimeoutSeconds,
	},
	IncludeRaw: false,
	Metadata: SnapshotMetadata{Source: "oneops"},
})
```

- [ ] **Step 5: Finish route wiring**

Modify `cmd/controller/main.go` so the controller process builds the production SDN API:

```go
sdnAPI := api.NewSDNAPI(
	ctrlsdn.NewService(
		ctrlsdn.NewMongoStore(ctl.GetMongoClient()),
		ctrlsdn.NewSecretCredentialResolver(ctl.GetMongoClient()),
		nil,
	),
	logger.L(),
)
```

Add import:

```go
ctrlsdn "github.com/netxops/agent/pkg/controller/sdn"
```

Register routes after other platform routes:

```go
r.HandleFunc("/api/v1/sdn/controllers", sdnAPI.ListControllers).Methods("GET")
r.HandleFunc("/api/v1/sdn/controllers", sdnAPI.CreateController).Methods("POST")
r.HandleFunc("/api/v1/sdn/controllers/{id}", sdnAPI.GetController).Methods("GET")
r.HandleFunc("/api/v1/sdn/controllers/{id}", sdnAPI.UpdateController).Methods("PUT")
r.HandleFunc("/api/v1/sdn/controllers/{id}", sdnAPI.DeleteController).Methods("DELETE")
r.HandleFunc("/api/v1/sdn/controllers/{id}/test", sdnAPI.TestController).Methods("POST")
r.HandleFunc("/api/v1/sdn/controllers/{id}/sync", sdnAPI.SyncController).Methods("POST")
r.HandleFunc("/api/v1/sdn/controllers/{id}/snapshots/latest", sdnAPI.LatestSnapshot).Methods("GET")
r.HandleFunc("/api/v1/sdn/controllers/{id}/snapshots", sdnAPI.SnapshotHistory).Methods("GET")
```

- [ ] **Step 6: Run backend tests and compile checks**

Run:

```bash
cd /Users/huangliang/project/OneOPS-ALL/agent
gofmt -w pkg/controller/sdn/*.go pkg/controller/api/sdn.go cmd/controller/main.go
go test ./pkg/controller/sdn -count=1
go test ./pkg/controller/api -run 'TestSDN' -count=1
go test ./cmd/controller -run TestDoesNotExist -count=1
```

Expected: all PASS. If `go test ./cmd/controller` exposes existing unrelated failures, capture the exact output and keep the SDN package/API tests as required evidence.

- [ ] **Step 7: Commit**

```bash
cd /Users/huangliang/project/OneOPS-ALL/agent
git add pkg/controller/sdn pkg/controller/api/sdn.go cmd/controller/main.go
git commit -m "feat: wire sdn snapshot backend"
```

---

## Task 6: Frontend Types And API Client

**Files:**
- Create: `/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/typings/platform/sdn-controller.ts`
- Create: `/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/api/platform/sdn-controller.ts`
- Optional test/smoke: `/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/scripts/sdn-controller-api-smoke.ts`

- [ ] **Step 1: Write failing API smoke**

Create `scripts/sdn-controller-api-smoke.ts`:

```ts
import { readFileSync } from 'node:fs';

const apiSource = readFileSync('src/api/platform/sdn-controller.ts', 'utf8');
const typeSource = readFileSync('src/typings/platform/sdn-controller.ts', 'utf8');

const requiredApiNames = [
  'sdnControllerListReq',
  'sdnControllerCreateReq',
  'sdnControllerUpdateReq',
  'sdnControllerDeleteReq',
  'sdnControllerTestReq',
  'sdnControllerSyncReq',
  'sdnControllerLatestSnapshotReq',
  'sdnControllerHistoryReq',
];

for (const name of requiredApiNames) {
  if (!apiSource.includes(`export const ${name}`)) {
    throw new Error(`missing API export ${name}`);
  }
}

for (const name of ['SDNControllerConfig', 'SDNSnapshotRecord', 'SDNResourceSummary', 'SDNSnapshot']) {
  if (!typeSource.includes(`interface ${name}`)) {
    throw new Error(`missing type ${name}`);
  }
}

console.log('sdn controller api smoke ok');
```

Run:

```bash
cd /Users/huangliang/project/OneOPS-ALL/OneOPS-UI
npx esbuild scripts/sdn-controller-api-smoke.ts --bundle --platform=node --format=esm --outfile=.tmp/sdn-controller-api-smoke.mjs >/dev/null && node .tmp/sdn-controller-api-smoke.mjs
```

Expected: FAIL because files do not exist.

- [ ] **Step 2: Add TypeScript types**

Create `src/typings/platform/sdn-controller.ts`:

```ts
export type SDNProvider = 'aci' | 'huawei';
export type SDNSyncStatus = 'never_synced' | 'success' | 'failed';

export interface SDNResourceSummary {
  tenants: number;
  vrfs: number;
  networks: number;
  subnets: number;
  segments: number;
  endpoints: number;
  switches: number;
  ports: number;
  contracts: number;
  filters: number;
  total: number;
}

export interface SDNControllerConfig {
  id: string;
  name: string;
  provider: SDNProvider;
  enabled: boolean;
  ctrlhub_base_url: string;
  sdn_scheme: 'http' | 'https';
  sdn_host: string;
  sdn_port?: number;
  credential_ref: string;
  insecure_skip_verify: boolean;
  timeout_seconds?: number;
  area?: string;
  site?: string;
  tenant?: string;
  description?: string;
  last_sync_status: SDNSyncStatus;
  last_sync_at?: string;
  last_success_at?: string;
  last_error?: string;
  last_summary: SDNResourceSummary;
  created_at: string;
  updated_at: string;
}

export type SDNControllerReq = Omit<
  SDNControllerConfig,
  'id' | 'last_sync_status' | 'last_sync_at' | 'last_success_at' | 'last_error' | 'last_summary' | 'created_at' | 'updated_at'
>;

export interface SDNResource {
  id: string;
  name: string;
  provider: SDNProvider;
  provider_type: string;
  dn: string;
  tenant: string;
  attributes: Record<string, unknown>;
  raw?: unknown;
}

export interface SDNSnapshotMetadata {
  source: string;
  provider_version: string;
}

export interface SDNSnapshot {
  provider: SDNProvider;
  collected_at: string;
  tenants: SDNResource[];
  vrfs: SDNResource[];
  networks: SDNResource[];
  subnets: SDNResource[];
  applications: SDNResource[];
  segments: SDNResource[];
  endpoints: SDNResource[];
  switches: SDNResource[];
  ports: SDNResource[];
  contracts: SDNResource[];
  filters: SDNResource[];
  metadata: SDNSnapshotMetadata;
}

export interface SDNSnapshotRecord {
  id: string;
  controller_id: string;
  provider: SDNProvider;
  collected_at: string;
  synced_at: string;
  duration_ms: number;
  status: SDNSyncStatus;
  error_summary?: string;
  resource_summary: SDNResourceSummary;
  snapshot?: SDNSnapshot;
  metadata: SDNSnapshotMetadata;
}

export interface SDNSyncResult {
  success: boolean;
  controller_id: string;
  provider: SDNProvider;
  status: SDNSyncStatus;
  summary: SDNResourceSummary;
  error?: string;
  duration_ms?: number;
  synced_at: string;
}
```

- [ ] **Step 3: Add API client**

Create `src/api/platform/sdn-controller.ts`:

```ts
import request, { HTTP_DELETE, HTTP_GET, HTTP_POST, HTTP_PUT } from '@/utils/request';
import type {
  SDNControllerConfig,
  SDNControllerReq,
  SDNSnapshotRecord,
  SDNSyncResult,
} from '@/typings/platform/sdn-controller';

export const sdnControllerListReq = async () => {
  return request<SDNControllerConfig[]>({
    url: '/sdn/controllers',
    method: HTTP_GET,
    silentSuccess: true,
  });
};

export const sdnControllerCreateReq = async (data: SDNControllerReq) => {
  return request<SDNControllerConfig>({
    url: '/sdn/controllers',
    method: HTTP_POST,
    data,
  });
};

export const sdnControllerUpdateReq = async (id: string, data: SDNControllerReq) => {
  return request<SDNControllerConfig>({
    url: `/sdn/controllers/${id}`,
    method: HTTP_PUT,
    data,
  });
};

export const sdnControllerDeleteReq = async (id: string) => {
  return request<{ id: string }>({
    url: `/sdn/controllers/${id}`,
    method: HTTP_DELETE,
  });
};

export const sdnControllerTestReq = async (id: string) => {
  return request<SDNSyncResult>({
    url: `/sdn/controllers/${id}/test`,
    method: HTTP_POST,
  });
};

export const sdnControllerSyncReq = async (id: string) => {
  return request<SDNSyncResult>({
    url: `/sdn/controllers/${id}/sync`,
    method: HTTP_POST,
  });
};

export const sdnControllerLatestSnapshotReq = async (id: string) => {
  return request<SDNSnapshotRecord>({
    url: `/sdn/controllers/${id}/snapshots/latest`,
    method: HTTP_GET,
    silentSuccess: true,
  });
};

export const sdnControllerHistoryReq = async (id: string, limit = 20) => {
  return request<SDNSnapshotRecord[]>({
    url: `/sdn/controllers/${id}/snapshots?limit=${limit}`,
    method: HTTP_GET,
    silentSuccess: true,
  });
};
```

- [ ] **Step 4: Run smoke**

Run:

```bash
cd /Users/huangliang/project/OneOPS-ALL/OneOPS-UI
npx esbuild scripts/sdn-controller-api-smoke.ts --bundle --platform=node --format=esm --outfile=.tmp/sdn-controller-api-smoke.mjs >/dev/null && node .tmp/sdn-controller-api-smoke.mjs
```

Expected: PASS and prints `sdn controller api smoke ok`.

- [ ] **Step 5: Commit**

```bash
cd /Users/huangliang/project/OneOPS-ALL/OneOPS-UI
git add src/typings/platform/sdn-controller.ts src/api/platform/sdn-controller.ts scripts/sdn-controller-api-smoke.ts
git commit -m "feat: add sdn controller ui api client"
```

---

## Task 7: Frontend SDN Controller Management Page

**Files:**
- Create: `/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/views/platform/SdnControllerManagement.vue`
- Modify: `/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/router/utils.ts`
- Create: `/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/scripts/sdn-controller-page-smoke.ts`

- [ ] **Step 1: Write failing page smoke**

Create `scripts/sdn-controller-page-smoke.ts`:

```ts
import { readFileSync } from 'node:fs';

const page = readFileSync('src/views/platform/SdnControllerManagement.vue', 'utf8');
const router = readFileSync('src/router/utils.ts', 'utf8');

for (const text of ['SDN 控制器', '测试连接', '同步', '最近快照', 'Tenants', 'Endpoints']) {
  if (!page.includes(text)) {
    throw new Error(`page missing ${text}`);
  }
}

for (const text of ['SdnControllerManagement', 'platform/sdn-controllers']) {
  if (!router.includes(text)) {
    throw new Error(`router missing ${text}`);
  }
}

console.log('sdn controller page smoke ok');
```

Run:

```bash
cd /Users/huangliang/project/OneOPS-ALL/OneOPS-UI
npx esbuild scripts/sdn-controller-page-smoke.ts --bundle --platform=node --format=esm --outfile=.tmp/sdn-controller-page-smoke.mjs >/dev/null && node .tmp/sdn-controller-page-smoke.mjs
```

Expected: FAIL because page and route do not exist.

- [ ] **Step 2: Add route**

Modify `src/router/utils.ts` inside `dynamicRoute` near other platform routes:

```ts
const sdnControllerManagementRoute: RouteRecordRaw = {
  path: 'platform/sdn-controllers',
  name: 'SdnControllerManagement',
  component: () => import('@/views/platform/SdnControllerManagement.vue'),
  meta: {
    title: 'SDN 控制器',
    requiresAuth: true,
    hideInMenu: true,
  },
};
```

Push it near other `children.push(...)` platform routes:

```ts
if (!children.some(route => route.path === sdnControllerManagementRoute.path)) {
  children.push(sdnControllerManagementRoute);
}
```

- [ ] **Step 3: Add page implementation**

Create `src/views/platform/SdnControllerManagement.vue` with this first version:

```vue
<template>
  <div class="page-container">
    <a-page-header title="SDN 控制器" sub-title="管理 ACI/Huawei 控制器接入、只读快照同步和资源查看">
      <template #extra>
        <a-space>
          <a-button :loading="loading" @click="loadControllers">刷新</a-button>
          <a-button type="primary" @click="openCreate">新增控制器</a-button>
        </a-space>
      </template>
    </a-page-header>

    <a-card style="margin-top: 16px">
      <a-form layout="inline">
        <a-form-item label="Provider">
          <a-select v-model:value="filters.provider" allow-clear style="width: 140px">
            <a-select-option value="aci">ACI</a-select-option>
            <a-select-option value="huawei">Huawei</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="状态">
          <a-select v-model:value="filters.status" allow-clear style="width: 150px">
            <a-select-option value="never_synced">未同步</a-select-option>
            <a-select-option value="success">成功</a-select-option>
            <a-select-option value="failed">失败</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="关键词">
          <a-input v-model:value="filters.keyword" allow-clear placeholder="名称 / Host / Site" style="width: 240px" />
        </a-form-item>
      </a-form>
    </a-card>

    <a-card style="margin-top: 16px">
      <a-table :columns="columns" :data-source="filteredControllers" :loading="loading" row-key="id">
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'provider'">
            <a-tag :color="record.provider === 'aci' ? 'blue' : 'green'">{{ providerLabel(record.provider) }}</a-tag>
          </template>
          <template v-else-if="column.key === 'status'">
            <a-tag :color="statusColor(record.last_sync_status)">{{ statusLabel(record.last_sync_status) }}</a-tag>
            <div v-if="record.last_error" class="muted">{{ record.last_error }}</div>
          </template>
          <template v-else-if="column.key === 'summary'">
            <span>{{ record.last_summary?.total || 0 }} 项</span>
          </template>
          <template v-else-if="column.key === 'action'">
            <a-space>
              <a @click="handleTest(record)">测试连接</a>
              <a @click="handleSync(record)">同步</a>
              <a @click="openSnapshot(record)">最近快照</a>
              <a @click="openEdit(record)">编辑</a>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-card>

    <a-modal v-model:open="formModal.open" :title="formModal.mode === 'create' ? '新增控制器' : '编辑控制器'" :width="780" @ok="saveController">
      <a-form :model="form" :label-col="{ span: 6 }" :wrapper-col="{ span: 18 }">
        <a-form-item label="名称" required><a-input v-model:value="form.name" /></a-form-item>
        <a-form-item label="Provider" required>
          <a-select v-model:value="form.provider">
            <a-select-option value="aci">ACI</a-select-option>
            <a-select-option value="huawei">Huawei</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="Ctrlhub URL" required><a-input v-model:value="form.ctrlhub_base_url" /></a-form-item>
        <a-form-item label="协议"><a-select v-model:value="form.sdn_scheme"><a-select-option value="https">HTTPS</a-select-option><a-select-option value="http">HTTP</a-select-option></a-select></a-form-item>
        <a-form-item label="SDN Host" required><a-input v-model:value="form.sdn_host" /></a-form-item>
        <a-form-item label="端口"><a-input-number v-model:value="form.sdn_port" :min="1" :max="65535" style="width: 100%" /></a-form-item>
        <a-form-item label="凭证引用" required><a-input v-model:value="form.credential_ref" placeholder="Secret code / Vault catalog code" /></a-form-item>
        <a-form-item label="跳过证书校验"><a-switch v-model:checked="form.insecure_skip_verify" /></a-form-item>
        <a-form-item label="超时秒数"><a-input-number v-model:value="form.timeout_seconds" :min="1" :max="600" style="width: 100%" /></a-form-item>
        <a-form-item label="Area"><a-input v-model:value="form.area" /></a-form-item>
        <a-form-item label="Site"><a-input v-model:value="form.site" /></a-form-item>
        <a-form-item label="Tenant"><a-input v-model:value="form.tenant" /></a-form-item>
        <a-form-item label="启用"><a-switch v-model:checked="form.enabled" /></a-form-item>
        <a-form-item label="描述"><a-textarea v-model:value="form.description" :rows="3" /></a-form-item>
      </a-form>
    </a-modal>

    <a-drawer v-model:open="snapshotDrawer.open" title="最近快照" width="980">
      <a-spin :spinning="snapshotDrawer.loading">
        <a-empty v-if="!snapshotDrawer.record?.snapshot" description="暂无最近快照" />
        <template v-else>
          <a-descriptions size="small" bordered :column="3">
            <a-descriptions-item label="Provider">{{ snapshotDrawer.record.provider }}</a-descriptions-item>
            <a-descriptions-item label="同步时间">{{ snapshotDrawer.record.synced_at }}</a-descriptions-item>
            <a-descriptions-item label="资源总数">{{ snapshotDrawer.record.resource_summary.total }}</a-descriptions-item>
          </a-descriptions>
          <a-tabs style="margin-top: 16px">
            <a-tab-pane v-for="group in resourceGroups" :key="group.key" :tab="group.label">
              <a-table :columns="resourceColumns" :data-source="snapshotResources(group.key)" row-key="dn" size="small" :pagination="{ pageSize: 10 }" />
            </a-tab-pane>
          </a-tabs>
        </template>
      </a-spin>
    </a-drawer>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue';
import { message } from 'ant-design-vue';
import {
  sdnControllerCreateReq,
  sdnControllerLatestSnapshotReq,
  sdnControllerListReq,
  sdnControllerSyncReq,
  sdnControllerTestReq,
  sdnControllerUpdateReq,
} from '@/api/platform/sdn-controller';
import type { SDNControllerConfig, SDNControllerReq, SDNProvider, SDNResource, SDNSnapshotRecord, SDNSyncStatus } from '@/typings/platform/sdn-controller';

const loading = ref(false);
const controllers = ref<SDNControllerConfig[]>([]);
const filters = reactive<{ provider?: SDNProvider; status?: SDNSyncStatus; keyword: string }>({ keyword: '' });

const emptySummary = { tenants: 0, vrfs: 0, networks: 0, subnets: 0, segments: 0, endpoints: 0, switches: 0, ports: 0, contracts: 0, filters: 0, total: 0 };
const formModal = reactive<{ open: boolean; mode: 'create' | 'edit'; editingId?: string }>({ open: false, mode: 'create' });
const form = reactive<SDNControllerReq>({
  name: '',
  provider: 'aci',
  enabled: true,
  ctrlhub_base_url: '',
  sdn_scheme: 'https',
  sdn_host: '',
  credential_ref: '',
  insecure_skip_verify: false,
  timeout_seconds: 30,
});
const snapshotDrawer = reactive<{ open: boolean; loading: boolean; record?: SDNSnapshotRecord }>({ open: false, loading: false });

const columns = [
  { title: '名称', dataIndex: 'name', key: 'name' },
  { title: 'Provider', dataIndex: 'provider', key: 'provider' },
  { title: 'Host', dataIndex: 'sdn_host', key: 'sdn_host' },
  { title: 'Site', dataIndex: 'site', key: 'site' },
  { title: '状态', key: 'status' },
  { title: '资源', key: 'summary' },
  { title: '操作', key: 'action', width: 260 },
];
const resourceColumns = [
  { title: '名称', dataIndex: 'name', key: 'name' },
  { title: 'ID', dataIndex: 'id', key: 'id' },
  { title: 'Tenant', dataIndex: 'tenant', key: 'tenant' },
  { title: '类型', dataIndex: 'provider_type', key: 'provider_type' },
  { title: 'DN', dataIndex: 'dn', key: 'dn' },
];
const resourceGroups = [
  { key: 'tenants', label: 'Tenants' },
  { key: 'vrfs', label: 'VRFs' },
  { key: 'networks', label: 'Networks' },
  { key: 'subnets', label: 'Subnets' },
  { key: 'segments', label: 'Segments' },
  { key: 'endpoints', label: 'Endpoints' },
  { key: 'switches', label: 'Switches' },
  { key: 'ports', label: 'Ports' },
  { key: 'contracts', label: 'Contracts' },
  { key: 'filters', label: 'Filters' },
] as const;

const filteredControllers = computed(() => {
  const keyword = filters.keyword.trim().toLowerCase();
  return controllers.value.filter(item => {
    if (filters.provider && item.provider !== filters.provider) return false;
    if (filters.status && item.last_sync_status !== filters.status) return false;
    if (!keyword) return true;
    return [item.name, item.sdn_host, item.site, item.area].some(value => String(value || '').toLowerCase().includes(keyword));
  });
});

const loadControllers = async () => {
  loading.value = true;
  try {
    controllers.value = (await sdnControllerListReq()) || [];
  } finally {
    loading.value = false;
  }
};

const openCreate = () => {
  Object.assign(form, { name: '', provider: 'aci', enabled: true, ctrlhub_base_url: '', sdn_scheme: 'https', sdn_host: '', sdn_port: undefined, credential_ref: '', insecure_skip_verify: false, timeout_seconds: 30, area: '', site: '', tenant: '', description: '' });
  formModal.mode = 'create';
  formModal.editingId = undefined;
  formModal.open = true;
};

const openEdit = (record: SDNControllerConfig) => {
  Object.assign(form, record);
  formModal.mode = 'edit';
  formModal.editingId = record.id;
  formModal.open = true;
};

const saveController = async () => {
  if (formModal.mode === 'edit' && formModal.editingId) {
    await sdnControllerUpdateReq(formModal.editingId, { ...form });
  } else {
    await sdnControllerCreateReq({ ...form });
  }
  formModal.open = false;
  await loadControllers();
};

const handleTest = async (record: SDNControllerConfig) => {
  const result = await sdnControllerTestReq(record.id);
  if (result?.success) message.success(`测试连接成功，发现 ${result.summary.total} 项资源`);
};

const handleSync = async (record: SDNControllerConfig) => {
  const result = await sdnControllerSyncReq(record.id);
  if (result?.success) message.success(`同步完成，发现 ${result.summary.total} 项资源`);
  await loadControllers();
};

const openSnapshot = async (record: SDNControllerConfig) => {
  snapshotDrawer.open = true;
  snapshotDrawer.loading = true;
  snapshotDrawer.record = undefined;
  try {
    snapshotDrawer.record = await sdnControllerLatestSnapshotReq(record.id);
  } finally {
    snapshotDrawer.loading = false;
  }
};

const snapshotResources = (key: string): SDNResource[] => {
  const snapshot = snapshotDrawer.record?.snapshot as any;
  return snapshot?.[key] || [];
};

const providerLabel = (provider: SDNProvider) => (provider === 'aci' ? 'ACI' : 'Huawei');
const statusLabel = (status: SDNSyncStatus) => ({ never_synced: '未同步', success: '成功', failed: '失败' }[status] || status);
const statusColor = (status: SDNSyncStatus) => ({ never_synced: 'default', success: 'green', failed: 'red' }[status] || 'default');

onMounted(loadControllers);
</script>

<style scoped>
.muted {
  color: #8c8c8c;
  font-size: 12px;
  margin-top: 4px;
}
</style>
```

- [ ] **Step 4: Run smoke and typecheck**

Run:

```bash
cd /Users/huangliang/project/OneOPS-ALL/OneOPS-UI
npx esbuild scripts/sdn-controller-page-smoke.ts --bundle --platform=node --format=esm --outfile=.tmp/sdn-controller-page-smoke.mjs >/dev/null && node .tmp/sdn-controller-page-smoke.mjs
npm run typecheck
```

Expected: smoke PASS. Typecheck PASS, or if existing unrelated type errors appear, capture exact output and run a focused `npx vue-tsc --noEmit --skipLibCheck` after fixing SDN page errors.

- [ ] **Step 5: Commit**

```bash
cd /Users/huangliang/project/OneOPS-ALL/OneOPS-UI
git add src/views/platform/SdnControllerManagement.vue src/router/utils.ts scripts/sdn-controller-page-smoke.ts
git commit -m "feat: add sdn controller management page"
```

---

## Task 8: Integration Verification And Secret Scan

**Files:**
- No required source changes.
- Optional evidence: `/Users/huangliang/project/OneOPS-ALL/docs/superpowers/evidence/2026-06-20-oneops-sdn-snapshot-mvp-verification.md`

- [ ] **Step 1: Run backend verification**

Run:

```bash
cd /Users/huangliang/project/OneOPS-ALL/agent
go test ./pkg/controller/sdn -count=1
go test ./pkg/controller/api -run 'TestSDN' -count=1
go test ./cmd/controller -run TestDoesNotExist -count=1
```

Expected: SDN package and SDN API tests PASS. `cmd/controller` compile check PASS or documented existing unrelated failure.

- [ ] **Step 2: Run frontend verification**

Run:

```bash
cd /Users/huangliang/project/OneOPS-ALL/OneOPS-UI
npx esbuild scripts/sdn-controller-api-smoke.ts --bundle --platform=node --format=esm --outfile=.tmp/sdn-controller-api-smoke.mjs >/dev/null && node .tmp/sdn-controller-api-smoke.mjs
npx esbuild scripts/sdn-controller-page-smoke.ts --bundle --platform=node --format=esm --outfile=.tmp/sdn-controller-page-smoke.mjs >/dev/null && node .tmp/sdn-controller-page-smoke.mjs
npm run typecheck
```

Expected: both smokes PASS. Typecheck PASS or documented unrelated failure.

- [ ] **Step 3: Run secret scan**

Run:

```bash
cd /Users/huangliang/project/OneOPS-ALL
git -C agent diff HEAD -- . ':!go.sum' | rg -n '198\.19\.254\.60|pesg-|APIC-cookie=[A-Za-z0-9]|X-ACCESS-TOKEN: [A-Za-z0-9]|plain_text.*password|password.*plain_text'
git -C OneOPS-UI diff HEAD -- . ':!package-lock.json' | rg -n '198\.19\.254\.60|pesg-|APIC-cookie=[A-Za-z0-9]|X-ACCESS-TOKEN: [A-Za-z0-9]'
```

Expected: no matches. `rg` exits 1 when no matches are found.

- [ ] **Step 4: Verify no OneOPS vendor adaptation was added**

Run:

```bash
cd /Users/huangliang/project/OneOPS-ALL
git -C agent diff HEAD -- pkg/controller pkg/controller/api cmd/controller | rg -n 'aaaLogin|APIC-cookie|X-ACCESS-TOKEN|/controller/dc/v3|/api/node/class'
```

Expected: no matches. OneOPS should only call `/api/v1/sdn/snapshot` on ctrlhub.

- [ ] **Step 5: Write verification evidence if failures are partly unrelated**

If any broad command fails due existing unrelated issues, create:

`/Users/huangliang/project/OneOPS-ALL/docs/superpowers/evidence/2026-06-20-oneops-sdn-snapshot-mvp-verification.md`

With:

```markdown
# OneOPS SDN Snapshot MVP Verification

## Passing Checks

- `go test ./pkg/controller/sdn -count=1`
- `go test ./pkg/controller/api -run 'TestSDN' -count=1`
- `sdn-controller-api-smoke`
- `sdn-controller-page-smoke`

## Broad Check Caveats

Record exact unrelated failures here, including package, test name, and first error line.

## Secret Scan

Record no-match result for real ACI IP/password/token patterns.
```

- [ ] **Step 6: Final commits**

Commit evidence only if created:

```bash
cd /Users/huangliang/project/OneOPS-ALL/docs
git add superpowers/evidence/2026-06-20-oneops-sdn-snapshot-mvp-verification.md
git commit -m "docs: record oneops sdn snapshot verification"
```

---

## Implementation Notes

- The `agent` repo currently has unrelated uncommitted changes. Implementers must not revert them.
- The `OneOPS-UI` repo currently has unrelated uncommitted changes. Implementers must not revert them.
- Use a fresh git worktree or carefully scoped commits before executing tasks.
- Do not add ACI/Huawei/H3C direct API calls to OneOPS backend or UI.
- Do not commit real ACI host, username, or password.
- Keep `include_raw=false` in OneOPS first phase.

## Self-Review Checklist

- Spec coverage: controller config, test, sync, latest snapshot, UI list, UI drawer, credential reference, security boundaries, and no vendor adaptation are all mapped to tasks.
- Placeholder scan: no placeholder red flags remain.
- Type consistency: provider names are `aci` and `huawei`; status values are `never_synced`, `success`, `failed`; API paths are `/api/v1/sdn/controllers...` on backend and `/sdn/controllers...` in frontend request helper because request base URL is `/api/v1`.
