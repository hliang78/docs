# Device V2 Access Binding Writer Phase 2A Design

## Goal

Land the second credential-governance subproject by unifying the write path for
device_v2 access bindings and credential projections.

Phase 2A focuses on one thing: every device_v2 write entrypoint that mutates
credential bindings must stop writing legacy fields and `credential_refs`
independently, and instead go through one shared writer.

## Why This Exists

Phase 1 unified the read side through `AccessResolver`, but the write side is
still fragmented:

- `zb_device_v2_store` builds credential payloads directly
- `zb_strategy_credential_override` patches several credential fields directly
- `device_v2_minimal_shared` copies and re-projects bindings directly
- `discovery / ingest` still depend on scattered write behavior

This creates three recurring problems:

1. the same credential intent is materialized differently by different writers
2. legacy fields and structured bindings drift out of sync
3. adding a new access protocol requires editing many unrelated code paths

## Phase 2A Scope

### In Scope

- introduce a shared `AccessBindingWriter`
- move device_v2 credential-binding write rules into that writer
- migrate these write entrypoints to use it:
  - `zb_device_v2_store`
  - `zb_strategy_credential_override`
  - `device_v2_minimal_shared`
  - `discovery / ingest` paths that write credential bindings
- centralize compatibility projection for:
  - `credential_ref_in_band`
  - `credential_ref_out_band`
  - `snmp_credential_ref`
  - `winrm_credential_ref`
- centralize structured write projection for:
  - `access_points`
  - `credential_refs`

### Out of Scope

- vault secret/community lifecycle redesign
- consumer-side behavior redesign
- terminal / guacd / webshell / automation execution refactors
- external DTO protocol cleanup
- removing legacy fields from public payloads

## Canonical Model

Phase 2A defines two canonical write outputs:

1. `attributes.access_points`
   This is the canonical access-channel model. It describes:
   - plane
   - protocol
   - address
   - port
   - credential_ref

2. `attributes.credential_refs`
   This is the canonical binding index. It describes capability-based aliases
   such as:
   - `default`
   - `in_band`
   - `in_band:ssh`
   - `in_band:telnet`
   - `in_band:snmp`
   - `in_band:winrm`
   - `out_band`
   - `out_band:ssh`
   - `out_band:telnet`
   - `out_band:snmp`
   - `out_band:ipmi`
   - `out_band:redfish`
   - `snmp_outband`
   - `ipmi_outband`
   - `redfish_outband`

Legacy top-level fields remain as compatibility projections only. They are no
longer independent write targets.

## Single Writer Design

Add a shared writer in `app/device/v2/service` so every entrypoint can call the
same binding normalization logic without depending on an `impl` package.

### Public Types

`AccessBindingIntent`

- `Plane`
- `Protocol`
- `Address`
- `Port`
- `CredentialRef`
- `Source`
- `PreserveIfMissing`

`AccessBindingWriteInput`

- `ExistingAttrs`
- `ExistingMeta`
- `Intents`

`AccessBindingWriteResult`

- `Attrs`
- `Meta`
- `Diagnostics`

`AccessBindingDiagnostics`

- `AppliedBindings`
- `ProjectedFields`
- `ClearedLegacyFields`
- `ConflictNotes`

### Public Function

- `ApplyAccessBindings(input AccessBindingWriteInput) AccessBindingWriteResult`

## Writer Responsibilities

The writer is intentionally narrow. It must:

1. merge existing bindings and new intents
2. produce canonical `access_points`
3. produce canonical `credential_refs`
4. project compatibility legacy fields from the canonical result
5. clear stale legacy fields when canonical structured data already supersedes
   them
6. report decisions through diagnostics

The writer must not:

- query the database
- call vault / secret / community services
- create or update device_v2 records directly
- perform business precheck validation

That keeps the writer pure and reusable across every write entrypoint.

## Projection Rules

### Structured Wins

If an explicit or newly written structured binding exists, it wins over a
legacy top-level field for the same access capability.

### Compatibility Is Derived

Legacy fields are projected from canonical bindings, not authored directly:

- `credential_ref_in_band`
  derived from preferred in-band CLI binding
- `credential_ref_out_band`
  derived from preferred out-band CLI/BMC binding
- `snmp_credential_ref`
  derived from preferred in-band SNMP binding
- `winrm_credential_ref`
  derived from preferred in-band WinRM binding

### Stale Legacy Cleanup

If a structured binding already expresses the same intent more precisely, stale
legacy values must be removed or replaced through the projection step so that
future readers and writers see one consistent result.

### Preserve Mode

When an intent is marked `PreserveIfMissing`, existing canonical bindings may be
retained if the incoming intent does not provide a replacement.

## Entry Point Migration

### 1. `zb_device_v2_store`

Current problem:

- `buildZbDeviceV2SeedPayload` writes both legacy fields and `credential_refs`
  directly
- it also performs protocol-specific projection such as server out-band
  IPMI/Redfish aliasing

Phase 2A change:

- keep secret/community creation logic in place
- convert resolved credential refs into `AccessBindingIntent`
- call the writer to build final `attrs/meta`
- stop manually authoring credential legacy fields and `credential_refs`

### 2. `zb_strategy_credential_override`

Current problem:

- directly patches several legacy fields
- directly mutates `credential_refs`
- can partially overwrite the binding model without re-normalizing it

Phase 2A change:

- load the current device_v2 state
- convert override refs into intents
- call the writer against the current state
- write back the normalized result

### 3. `device_v2_minimal_shared`

Current problem:

- extracts credential refs from several representations
- performs scattered structured-to-legacy backfill
- D2LA copy behavior implicitly depends on local conversion rules

Phase 2A change:

- reuse the current source-device extraction only as intent collection
- merge explicit target input and copied source intents
- call the writer to build final attrs
- stop locally deciding how structured refs map back into legacy fields

### 4. `discovery / ingest`

Current problem:

- still depend on fragmented write semantics from earlier paths

Phase 2A change:

- adapt the credential-writing parts of discovery/ingest to build intents
- reuse the same writer before persisting device_v2 payloads

## Migration Strategy

Phase 2A should be landed incrementally:

1. add the writer and its unit tests
2. migrate `zb_device_v2_store`
3. migrate `zb_strategy_credential_override`
4. migrate `device_v2_minimal_shared`
5. migrate discovery/ingest write paths

This is not a big-bang rewrite. Compatibility projection remains during the
whole phase.

## Testing Strategy

### Writer Unit Tests

This is the main rule center. Cover:

- in-band ssh/telnet/snmp/winrm projection
- out-band ssh/telnet/snmp/ipmi/redfish projection
- structured-over-legacy precedence
- stale legacy cleanup
- preserve-if-missing behavior
- mixed conflict resolution

### Entry Point Adaptation Tests

Each migrated entrypoint should only verify:

- it builds the intended binding intents
- it persists the writer result correctly

Credential projection rule duplication should move out of entrypoint tests and
into writer tests.

### End-to-End Regression Tests

Keep focused E2E coverage for:

- `zb_device_v2_store`
- `zb_strategy_credential_override`
- D2LA / minimal copy
- monitor-push credential parity

## Risks And Controls

### Risk: Compatibility Drift

If the writer and old entrypoint logic coexist too long, results may diverge.

Control:

- migrate entrypoints sequentially
- stop local projection logic as each entrypoint switches

### Risk: Over-Broad Scope

Trying to redesign vault lifecycle or consumer behavior at the same time will
slow the治理 and blur acceptance.

Control:

- keep Phase 2A focused on binding writes only

### Risk: Hidden Rule Changes

Credential cleanup and structured precedence can be surprising during rollout.

Control:

- include diagnostics in writer output
- preserve targeted E2E tests

## Acceptance

Phase 2A is complete when all of the following are true:

- `zb_device_v2_store` no longer authors legacy credential fields or
  `credential_refs` directly
- `zb_strategy_credential_override` no longer patches credential fields
  directly
- `device_v2_minimal_shared` no longer locally interprets structured-to-legacy
  credential projection rules
- discovery/ingest binding writes go through the writer
- adding a new access protocol only requires writer and writer-test changes,
  not entrypoint-specific projection changes
- the main credential write-rule tests live in writer unit tests instead of
  being duplicated across multiple entrypoints

## Recommended Next Step

After this spec is approved, write an implementation plan for Phase 2A only.
Do not bundle later credential CRUD unification or consumer-side redesign into
the same plan.
