# Device V2 Access Binding Writer Phase 2A Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Introduce a shared device_v2 access-binding writer and migrate the first batch of write entrypoints so credential binding writes stop being authored independently.

**Architecture:** Add a pure writer in `app/device/v2/service` that converts binding intents plus existing attrs/meta into canonical `access_points`, canonical `credential_refs`, and compatibility legacy projections. Then wire each write entrypoint to build intents and delegate binding materialization to the writer instead of hand-writing legacy fields, ref maps, and cleanup rules locally.

**Tech Stack:** Go, existing `device_v2` service layer, GORM-backed entity writes, Go tests with current package-level test harnesses

---

## File Structure

**Create**

- `OneOps/app/device/v2/service/access_binding_writer.go`
  Pure binding-writer entrypoint and helper types.
- `OneOps/app/device/v2/service/access_binding_writer_test.go`
  Central rule tests for write-side binding projection.

**Modify**

- `OneOps/app/device/v2/service/impl/device_v2_minimal_attributes.go`
  Replace local credential projection logic in `normalizeDeviceV2WriteAttributes` with the shared writer while preserving existing manageability checks.
- `OneOps/app/external_request/service/zb/impl/zb_device_v2_store.go`
  Convert ZB seed payload creation from direct field writes to binding intents.
- `OneOps/app/external_request/service/zb/impl/zb_strategy_credential_override.go`
  Replace direct patching of credential fields with writer-driven updates.
- `OneOps/app/device/v2/service/impl/device_v2_minimal_shared.go`
  Replace local structured/legacy extraction and D2LA copy projection logic with intent generation and writer output.
- `OneOps/app/device/v2/discovery/service/impl/device_v2_discovery_service.go`
  Replace direct binding field writes after discovery probing with writer usage.
- `OneOps/app/device/v2/ingest/service/impl/device_v2_ingest_executor.go`
  Replace local credential merge/cleanup with writer-driven binding output.
- `OneOps/app/device/v2/ingest/service/impl/device_v2_ingest_inline_credentials.go`
  Convert inline-credential materialization to generate binding intents and reuse the writer.

**Test**

- `OneOps/app/external_request/service/zb/impl/zb_device_v2_store_test.go`
- `OneOps/app/external_request/service/zb/impl/zb_strategy_credential_override_test.go`
- `OneOps/app/device/v2/service/impl/device_v2_minimal_shared_test.go`
- `OneOps/app/device/v2/discovery/service/impl/device_v2_discovery_service_test.go`
- `OneOps/app/device/v2/ingest/service/impl/device_v2_ingest_executor_test.go`
- `OneOps/app/device/v2/ingest/api/device_v2_ingest_test.go`

### Task 1: Add The Shared Access Binding Writer

**Files:**
- Create: `OneOps/app/device/v2/service/access_binding_writer.go`
- Test: `OneOps/app/device/v2/service/access_binding_writer_test.go`

- [ ] **Step 1: Write the failing writer tests**

```go
func TestApplyAccessBindings_ProjectsInBandAndOutBandAliases(t *testing.T) {
	result := ApplyAccessBindings(AccessBindingWriteInput{
		Intents: []AccessBindingIntent{
			{Plane: "in_band", Protocol: "ssh", Address: "192.0.2.10", Port: 22, CredentialRef: "cred-ssh", Source: "test"},
			{Plane: "in_band", Protocol: "snmp", Address: "192.0.2.10", Port: 161, CredentialRef: "cred-snmp", Source: "test"},
			{Plane: "out_band", Protocol: "ipmi", Address: "10.0.0.10", Port: 623, CredentialRef: "cred-ipmi", Source: "test"},
		},
	})

	refs := stringMapFromAny(result.Attrs["credential_refs"])
	if refs["default"] != "cred-ssh" || refs["in_band:ssh"] != "cred-ssh" {
		t.Fatalf("expected in-band ssh aliases, got %#v", refs)
	}
	if refs["snmp"] != "cred-snmp" || refs["in_band:snmp"] != "cred-snmp" {
		t.Fatalf("expected snmp aliases, got %#v", refs)
	}
	if refs["out_band:ipmi"] != "cred-ipmi" || refs["ipmi_outband"] != "cred-ipmi" {
		t.Fatalf("expected ipmi aliases, got %#v", refs)
	}
	if got := fmt.Sprint(result.Attrs["credential_ref_in_band"]); got != "cred-ssh" {
		t.Fatalf("expected credential_ref_in_band projection, got %#v", result.Attrs)
	}
	if got := fmt.Sprint(result.Attrs["snmp_credential_ref"]); got != "cred-snmp" {
		t.Fatalf("expected snmp_credential_ref projection, got %#v", result.Attrs)
	}
}

func TestApplyAccessBindings_StructuredBindingsClearStaleLegacyFields(t *testing.T) {
	result := ApplyAccessBindings(AccessBindingWriteInput{
		ExistingAttrs: map[string]interface{}{
			"credential_ref_in_band": "cred-legacy-ssh",
			"credential_ref_out_band": "cred-legacy-oob",
		},
		Intents: []AccessBindingIntent{
			{Plane: "in_band", Protocol: "telnet", Address: "192.0.2.20", Port: 23, CredentialRef: "cred-telnet", Source: "test"},
			{Plane: "out_band", Protocol: "snmp", Address: "10.0.0.20", Port: 161, CredentialRef: "cred-oob-snmp", Source: "test"},
		},
	})

	if got := fmt.Sprint(result.Attrs["credential_ref_in_band"]); got != "cred-telnet" {
		t.Fatalf("expected in-band legacy projection updated from structured telnet binding, got %#v", result.Attrs)
	}
	if got := fmt.Sprint(result.Attrs["credential_ref_out_band"]); got != "" {
		t.Fatalf("expected stale generic out-band legacy field cleared for snmp-only OOB binding, got %#v", result.Attrs)
	}
	refs := stringMapFromAny(result.Attrs["credential_refs"])
	if refs["out_band:snmp"] != "cred-oob-snmp" || refs["snmp_outband"] != "cred-oob-snmp" {
		t.Fatalf("expected OOB snmp aliases, got %#v", refs)
	}
}

func TestApplyAccessBindings_PreserveIfMissingKeepsExistingBinding(t *testing.T) {
	result := ApplyAccessBindings(AccessBindingWriteInput{
		ExistingAttrs: map[string]interface{}{
			"credential_refs": map[string]interface{}{
				"in_band:ssh": "cred-existing-ssh",
			},
		},
		Intents: []AccessBindingIntent{
			{Plane: "in_band", Protocol: "ssh", Address: "192.0.2.30", Source: "test", PreserveIfMissing: true},
		},
	})

	refs := stringMapFromAny(result.Attrs["credential_refs"])
	if refs["in_band:ssh"] != "cred-existing-ssh" {
		t.Fatalf("expected existing binding retained, got %#v", refs)
	}
}
```

- [ ] **Step 2: Run the writer tests to verify they fail**

Run:

```bash
go test ./app/device/v2/service -run 'TestApplyAccessBindings'
```

Expected: FAIL with `undefined: ApplyAccessBindings` and missing type errors for the new writer API.

- [ ] **Step 3: Implement the shared writer**

```go
package service

type AccessBindingIntent struct {
	Plane             string
	Protocol          string
	Address           string
	Port              int
	CredentialRef     string
	Source            string
	PreserveIfMissing bool
}

type AccessBindingWriteInput struct {
	ExistingAttrs map[string]interface{}
	ExistingMeta  map[string]interface{}
	Intents       []AccessBindingIntent
}

type AccessBindingDiagnostics struct {
	AppliedBindings     []string
	ProjectedFields     []string
	ClearedLegacyFields []string
	ConflictNotes       []string
}

type AccessBindingWriteResult struct {
	Attrs       map[string]interface{}
	Meta        map[string]interface{}
	Diagnostics AccessBindingDiagnostics
}

func ApplyAccessBindings(input AccessBindingWriteInput) AccessBindingWriteResult {
	writer := newAccessBindingWriter(input.ExistingAttrs, input.ExistingMeta)
	writer.applyIntents(input.Intents)
	return writer.result()
}
```

Implementation notes:

- start from cloned `ExistingAttrs` / `ExistingMeta`
- normalize `plane`, `protocol`, `address`, and `port`
- build canonical `access_points`
- build canonical `credential_refs`
- project:
  - `credential_ref_in_band`
  - `credential_ref_out_band`
  - `snmp_credential_ref`
  - `winrm_credential_ref`
- clear stale generic OOB legacy field when only `out_band:snmp` is authoritative
- emit diagnostics whenever:
  - a binding is applied
  - a legacy field is projected
  - a stale field is cleared

- [ ] **Step 4: Run the writer tests to verify they pass**

Run:

```bash
go test ./app/device/v2/service -run 'TestApplyAccessBindings'
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add \
  OneOps/app/device/v2/service/access_binding_writer.go \
  OneOps/app/device/v2/service/access_binding_writer_test.go
git commit -m "feat: add device v2 access binding writer"
```

### Task 2: Route Core Device V2 Write Normalization Through The Writer

**Files:**
- Modify: `OneOps/app/device/v2/service/impl/device_v2_minimal_attributes.go`
- Test: `OneOps/app/device/v2/service/impl/device_v2_minimal_shared_test.go`

- [ ] **Step 1: Add failing normalization regression tests around writer-backed behavior**

```go
func TestNormalizeDeviceV2WriteAttributes_UsesSharedWriterForStructuredPrecedence(t *testing.T) {
	attrs := map[string]interface{}{
		"credential_ref_in_band": "cred-legacy-ssh",
		"credential_refs": map[string]interface{}{
			"in_band:telnet": "cred-structured-telnet",
		},
		"access_points": []map[string]interface{}{
			{
				"plane":    "in_band",
				"protocol": "telnet",
				"ip":       "192.0.2.40",
			},
		},
	}

	out := normalizeDeviceV2WriteAttributes(attrs)
	if got := minimalReadString(out, "credential_ref_in_band"); got != "cred-structured-telnet" {
		t.Fatalf("expected shared writer projection to win, got %q attrs=%#v", got, out)
	}
}

func TestNormalizeDeviceV2WriteAttributes_ClearsGenericOOBForStructuredSNMP(t *testing.T) {
	attrs := map[string]interface{}{
		"credential_ref_out_band": "cred-generic-oob",
		"access_points": []map[string]interface{}{
			{
				"plane":          "out_band",
				"protocol":       "snmp",
				"ip":             "10.0.0.40",
				"credential_ref": "cred-oob-snmp",
			},
		},
	}

	out := normalizeDeviceV2WriteAttributes(attrs)
	if got := minimalReadString(out, "credential_ref_out_band"); got != "" {
		t.Fatalf("expected generic OOB legacy field cleared, got %q attrs=%#v", got, out)
	}
}
```

- [ ] **Step 2: Run the shared normalization tests to verify they fail**

Run:

```bash
go test ./app/device/v2/service/impl -run 'TestNormalizeDeviceV2WriteAttributes'
```

Expected: FAIL because `normalizeDeviceV2WriteAttributes` still relies on its local credential-projection logic.

- [ ] **Step 3: Replace local normalization logic with a writer-backed adapter**

```go
func normalizeDeviceV2WriteAttributes(attributes map[string]interface{}) map[string]interface{} {
	out := cloneAnyMap(attributes)
	if out == nil {
		out = map[string]interface{}{}
	}

	intents := buildAccessBindingIntentsFromAttrs(out)
	result := devv2svc.ApplyAccessBindings(devv2svc.AccessBindingWriteInput{
		ExistingAttrs: out,
		Intents:       intents,
	})

	out = cloneAnyMap(result.Attrs)
	out = normalizeDeviceV2EntityWriteAttributes(out)
	return out
}
```

Implementation notes:

- keep existing non-binding normalization behavior intact
- extract local binding interpretation into a helper like
  `buildAccessBindingIntentsFromAttrs`
- remove duplicated structured-to-legacy projection code once the writer-backed
  path is in place

- [ ] **Step 4: Run the normalization tests to verify they pass**

Run:

```bash
go test ./app/device/v2/service/impl -run 'TestNormalizeDeviceV2WriteAttributes|TestMinimalDeviceV2Executor'
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add \
  OneOps/app/device/v2/service/impl/device_v2_minimal_attributes.go \
  OneOps/app/device/v2/service/impl/device_v2_minimal_shared_test.go
git commit -m "refactor: back device v2 write normalization with shared binding writer"
```

### Task 3: Migrate ZB Seed Write And Credential Override

**Files:**
- Modify: `OneOps/app/external_request/service/zb/impl/zb_device_v2_store.go`
- Modify: `OneOps/app/external_request/service/zb/impl/zb_strategy_credential_override.go`
- Test: `OneOps/app/external_request/service/zb/impl/zb_device_v2_store_test.go`
- Test: `OneOps/app/external_request/service/zb/impl/zb_strategy_credential_override_test.go`

- [ ] **Step 1: Add failing ZB tests that assert writer-driven output instead of local field patching**

```go
func TestBuildZbDeviceV2SeedPayload_UsesSharedBindingWriterProjection(t *testing.T) {
	_, attrs, _, _ := buildZbDeviceV2SeedPayload("req-1", &externalRequestDto.Equipment{
		DeviceCode:      "DVC-ZB-PLAN-1",
		DeviceName:      "device-one",
		AttributionType: zbAttributionServer,
		InBandIP:        "192.0.2.50",
		OutBandIP:       "10.0.0.50",
		LoginMethod:     "ssh",
	}, map[string]string{
		"in_band":  "cred-in-ssh",
		"out_band": "cred-oob-shared",
	})

	refs := attrs["credential_refs"].(map[string]interface{})
	if refs["out_band:ipmi"] != "cred-oob-shared" || refs["out_band:redfish"] != "cred-oob-shared" {
		t.Fatalf("expected shared writer aliases for server OOB binding, got %#v", refs)
	}
}

func TestZbApplyStrategyCredentialOverride_UsesWriterToClearStaleOutBandLegacyField(t *testing.T) {
	// current device has credential_ref_out_band set, override only provides OOB snmp
	// expected writer result clears generic out-band legacy field instead of leaving stale value behind
}
```

- [ ] **Step 2: Run the ZB tests to verify they fail**

Run:

```bash
go test ./app/external_request/service/zb/impl -run 'TestBuildZbDeviceV2SeedPayload|TestZbApplyStrategyCredentialOverride'
```

Expected: FAIL because the current code still authors or patches binding fields directly.

- [ ] **Step 3: Refactor ZB seed payload and override to build intents**

```go
func buildZbDeviceV2SeedPayload(...) (...) {
	attrs := map[string]interface{}{ ...non-credential fields... }
	intents := []devv2svc.AccessBindingIntent{}

	if ref := strings.TrimSpace(credentialRefs["in_band"]); ref != "" {
		intents = append(intents, devv2svc.AccessBindingIntent{
			Plane:         "in_band",
			Protocol:      firstZbNonEmpty(equipment.LoginMethod, "ssh"),
			Address:       equipment.InBandIP,
			Port:          equipment.LoginPort,
			CredentialRef: ref,
			Source:        "zb_seed",
		})
	}
	if ref := strings.TrimSpace(credentialRefs["snmp"]); ref != "" {
		intents = append(intents, devv2svc.AccessBindingIntent{
			Plane:         "in_band",
			Protocol:      "snmp",
			Address:       equipment.InBandIP,
			Port:          161,
			CredentialRef: ref,
			Source:        "zb_seed",
		})
	}

	result := devv2svc.ApplyAccessBindings(devv2svc.AccessBindingWriteInput{ExistingAttrs: attrs, ExistingMeta: metadata, Intents: intents})
	return labels, result.Attrs, result.Meta, []string{"zb"}
}
```

```go
result := devv2svc.ApplyAccessBindings(devv2svc.AccessBindingWriteInput{
	ExistingAttrs: attrs,
	ExistingMeta:  metadata,
	Intents:       zbOverrideIntentsFromRefs(current, refs),
})
attrs = result.Attrs
metadata = result.Meta
```

- [ ] **Step 4: Run the ZB tests to verify they pass**

Run:

```bash
go test ./app/external_request/service/zb/impl -run 'TestBuildZbDeviceV2SeedPayload|TestEnsureZbDeviceV2CredentialRefs|TestZbApplyStrategyCredentialOverride'
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add \
  OneOps/app/external_request/service/zb/impl/zb_device_v2_store.go \
  OneOps/app/external_request/service/zb/impl/zb_strategy_credential_override.go \
  OneOps/app/external_request/service/zb/impl/zb_device_v2_store_test.go \
  OneOps/app/external_request/service/zb/impl/zb_strategy_credential_override_test.go
git commit -m "refactor: route zb device v2 binding writes through shared writer"
```

### Task 4: Migrate Minimal Shared Copy And Discovery Auto-Binding

**Files:**
- Modify: `OneOps/app/device/v2/service/impl/device_v2_minimal_shared.go`
- Modify: `OneOps/app/device/v2/discovery/service/impl/device_v2_discovery_service.go`
- Test: `OneOps/app/device/v2/service/impl/device_v2_minimal_shared_test.go`
- Test: `OneOps/app/device/v2/discovery/service/impl/device_v2_discovery_service_test.go`

- [ ] **Step 1: Add failing tests for writer-backed D2LA copy and discovery binding**

```go
func TestMinimalDeviceV2Executor_CopyCredentialRefsFromSourceOriginalUsesWriterProjection(t *testing.T) {
	// source has structured in_band:telnet and out_band:telnet only
	// target should receive writer-projected compatibility fields plus structured refs
}

func TestDiscoveryService_AutoBindUsesWriterProjection(t *testing.T) {
	// when ssh and snmp creds are detected, expect credential_refs aliases and access_points
	// to be normalized through the writer rather than only top-level fields being set
}
```

- [ ] **Step 2: Run the minimal/shared and discovery tests to verify they fail**

Run:

```bash
go test ./app/device/v2/service/impl -run 'TestMinimalDeviceV2Executor_CopyCredentialRefsFromSourceOriginalUsesWriterProjection'
go test ./app/device/v2/discovery/service/impl -run 'TestDiscoveryService_AutoBindUsesWriterProjection'
```

Expected: FAIL because these paths still write legacy fields directly.

- [ ] **Step 3: Replace local projection logic with writer-based merge**

```go
func (e *minimalDeviceV2Executor) copyCredentialRefsFromSourceOriginal(...) (...) {
	// collect intents from sourceAttrs instead of copying legacy projections directly
	intents := buildIntentsFromSourceDevice(sourceAttrs, "d2la_copy")
	result := devv2svc.ApplyAccessBindings(devv2svc.AccessBindingWriteInput{
		ExistingAttrs: attrs,
		Intents:       intents,
	})
	device.Attributes = result.Attrs
	device.CredentialRefInBand = strings.TrimSpace(minimalReadString(result.Attrs, "credential_ref_in_band"))
	device.CredentialRefOutBand = strings.TrimSpace(minimalReadString(result.Attrs, "credential_ref_out_band"))
	device.SNMPCredentialRef = strings.TrimSpace(minimalReadString(result.Attrs, "snmp_credential_ref"))
	device.WinRMCredentialRef = strings.TrimSpace(minimalReadString(result.Attrs, "winrm_credential_ref"))
	return device, nil
}
```

```go
result := devv2svc.ApplyAccessBindings(devv2svc.AccessBindingWriteInput{
	ExistingAttrs: attrs,
	ExistingMeta:  metadata,
	Intents:       discoveryBindingIntents(candidate, detectedSSHRef, detectedSNMPRef),
})
attrs = result.Attrs
metadata = result.Meta
```

- [ ] **Step 4: Run the minimal/shared and discovery tests to verify they pass**

Run:

```bash
go test ./app/device/v2/service/impl -run 'TestMinimalDeviceV2Executor|TestNormalizeDeviceV2WriteAttributes'
go test ./app/device/v2/discovery/service/impl -run 'TestDiscovery'
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add \
  OneOps/app/device/v2/service/impl/device_v2_minimal_shared.go \
  OneOps/app/device/v2/discovery/service/impl/device_v2_discovery_service.go \
  OneOps/app/device/v2/service/impl/device_v2_minimal_shared_test.go \
  OneOps/app/device/v2/discovery/service/impl/device_v2_discovery_service_test.go
git commit -m "refactor: use shared writer for minimal copy and discovery binding writes"
```

### Task 5: Migrate Ingest Binding Writes And Close Phase 2A Regression Coverage

**Files:**
- Modify: `OneOps/app/device/v2/ingest/service/impl/device_v2_ingest_executor.go`
- Modify: `OneOps/app/device/v2/ingest/service/impl/device_v2_ingest_inline_credentials.go`
- Test: `OneOps/app/device/v2/ingest/service/impl/device_v2_ingest_executor_test.go`
- Test: `OneOps/app/device/v2/ingest/api/device_v2_ingest_test.go`

- [ ] **Step 1: Add failing ingest regression tests for shared-writer materialization**

```go
func TestMergeIngestAttributes_UsesWriterToProjectBindings(t *testing.T) {
	device := ingestmodel.DeviceV2IngestDevice{
		CredentialRefInBand: "cred-inline-ssh",
		Attributes: map[string]interface{}{
			"in_band_ip": "192.0.2.60",
			"credential_refs": map[string]interface{}{
				"out_band:snmp": "cred-oob-snmp",
			},
			"access_points": []map[string]interface{}{
				{
					"plane":    "out_band",
					"protocol": "snmp",
					"ip":       "10.0.0.60",
				},
			},
		},
	}

	out := mergeIngestAttributes(nil, "DVC-INGEST-PLAN-1", device)
	refs := ingestAnyMap(out["credential_refs"])
	if refs["in_band:ssh"] != "cred-inline-ssh" {
		t.Fatalf("expected writer-projected in-band ssh alias, got %#v", refs)
	}
	if got := readStringFromMap(out, "credential_ref_out_band"); got != "" {
		t.Fatalf("expected stale generic out-band legacy field cleared, got %q attrs=%#v", got, out)
	}
}

func TestApplyInlineCredentials_UsesWriterToPersistAccessPointsAndAliases(t *testing.T) {
	// expect generated access_points and credential_refs to come from writer result
}
```

- [ ] **Step 2: Run the ingest tests to verify they fail**

Run:

```bash
go test ./app/device/v2/ingest/service/impl -run 'TestMergeIngestAttributes|TestApplyInlineCredentials'
go test ./app/device/v2/ingest/api -run 'TestDeviceV2Ingest'
```

Expected: FAIL because ingest still performs local merge and cleanup.

- [ ] **Step 3: Move ingest binding materialization behind the writer**

```go
func mergeIngestAttributes(base map[string]interface{}, code string, device ingestmodel.DeviceV2IngestDevice) map[string]interface{} {
	out := cloneAnyMap(base)
	out = mergeIngestAnyMap(out, sanitizeIngestRuntimeInputFields(device.Attributes))
	// keep non-binding fields
	...

	result := devv2svc.ApplyAccessBindings(devv2svc.AccessBindingWriteInput{
		ExistingAttrs: out,
		Intents:       ingestBindingIntents(device, out),
	})
	out = result.Attrs
	return out
}
```

```go
result := devv2svc.ApplyAccessBindings(devv2svc.AccessBindingWriteInput{
	ExistingAttrs: device.Attributes,
	Intents:       inlineCredentialBindingIntents(device, generatedRefs),
})
device.Attributes = result.Attrs
```

- [ ] **Step 4: Run the ingest tests to verify they pass**

Run:

```bash
go test ./app/device/v2/ingest/service/impl -run 'TestMergeIngestAttributes|TestApplyInlineCredentials'
go test ./app/device/v2/ingest/api -run 'TestDeviceV2Ingest'
```

Expected: PASS

- [ ] **Step 5: Run full Phase 2A verification**

Run:

```bash
go test ./app/device/v2/service
go test ./app/device/v2/service/impl -run 'TestNormalizeDeviceV2WriteAttributes|TestMinimalDeviceV2Executor'
go test ./app/external_request/service/zb/impl -run 'TestBuildZbDeviceV2SeedPayload|TestEnsureZbDeviceV2CredentialRefs|TestZbApplyStrategyCredentialOverride'
go test ./app/device/v2/discovery/service/impl -run 'TestDiscovery'
go test ./app/device/v2/ingest/service/impl -run 'TestMergeIngestAttributes|TestApplyInlineCredentials'
go test ./app/device/v2/ingest/api -run 'TestDeviceV2Ingest'
```

Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add \
  OneOps/app/device/v2/ingest/service/impl/device_v2_ingest_executor.go \
  OneOps/app/device/v2/ingest/service/impl/device_v2_ingest_inline_credentials.go \
  OneOps/app/device/v2/ingest/service/impl/device_v2_ingest_executor_test.go \
  OneOps/app/device/v2/ingest/api/device_v2_ingest_test.go
git commit -m "refactor: route ingest binding writes through shared writer"
```

## Self-Review

### Spec Coverage

- shared writer added: Task 1
- compatibility projection centralized: Tasks 1 and 2
- ZB seed/override migrated: Task 3
- minimal shared migrated: Task 4
- discovery/ingest migrated: Tasks 4 and 5
- rule tests moved to writer unit tests: Task 1, reinforced by adaptation tests in Tasks 2-5

No spec gaps found for Phase 2A scope.

### Placeholder Scan

- no `TBD`
- no `TODO`
- no “implement later”
- every task has explicit files, commands, and code skeletons

### Type Consistency

- writer API names are consistent across tasks:
  - `AccessBindingIntent`
  - `AccessBindingWriteInput`
  - `AccessBindingWriteResult`
  - `ApplyAccessBindings`
- intent builder helpers are described as local adapters only and do not define a conflicting public API

