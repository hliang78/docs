# ZB Collect Strategy Credential Override Design

## Background

`CollectStrateyIssuance` currently focuses on pushing collection strategies to OneOps targets, but it does not close the loop between strategy-carried credentials and the device inventory credential bindings. In practice, ZB may send strategy parameters that already contain usable access material such as:

- in-band CLI username/password
- in-band SNMP v1/v2c community
- in-band SNMP v3 USM fields
- out-of-band SNMP v1/v2c/v3 fields
- out-of-band IPMI username/password
- out-of-band Redfish username/password

The desired behavior for this design is explicit: after a strategy push succeeds, OneOps must forcibly update the corresponding credential bindings on both `device v2` and `device v1`. Existing bindings are not protected from replacement.

## Goals

- Make strategy-carried credentials first-class inputs to device credential binding.
- Apply credential overrides only after strategy push succeeds.
- Update `device v2` credential references and `device v1` role bindings consistently.
- Support in-band CLI, in-band SNMP, out-of-band SNMP, out-of-band IPMI, and out-of-band Redfish.
- Avoid storing plaintext credentials on `device v2`; only store references there.
- Keep logs and audit records free of plaintext secrets.

## Non-Goals

- Support out-of-band SSH. Current business scope does not define OOB SSH.
- Introduce a cross-service distributed transaction across strategy apply and inventory updates.
- Replace internal structured SNMP v3 storage with a compressed string format.
- Generalize this behavior to every strategy entry point outside the ZB external request flow.

## Current Constraints

- The override entry point lives in `ZbCallSrv` during `CollectStrateyIssuance`.
- `device v1` already has role-based replacement APIs for secret and community bindings.
- `device v2` stores credential bindings primarily as `credential_ref_*`, `snmp_credential_ref`, and `credential_refs.*`.
- SNMP v3 is already modeled internally as structured fields such as `sec_name`, `sec_level`, `auth_protocol`, `auth_password`, `priv_protocol`, `priv_password`, and `context_name`.
- Existing strategy payloads carry parameters, not canonical OneOps `credential_ref` values.

## Recommended Approach

Use a post-success override pipeline inside the ZB strategy issuance flow:

1. Build and execute the quick-apply request as today.
2. If strategy execution fails, do not touch inventory credential bindings.
3. If strategy execution succeeds, parse strategy parameters into a normalized credential override intent per device.
4. Materialize those intents into OneOps credential objects or reusable bindings.
5. Update `device v2` credential references.
6. Update `device v1` role bindings where the legacy model has a matching role.
7. Emit structured audit logs for every attempted override.

This keeps inventory state aligned with the actual pushed strategy and avoids the failure mode where inventory is overwritten even though strategy application never took effect.

## Alternatives Considered

### 1. Override before strategy execution

Pros:

- minimal code movement near the existing placeholder

Cons:

- wrong semantics when strategy push fails
- inventory can diverge from deployed monitoring state

Rejected because failure handling becomes misleading and dangerous.

### 2. Override after strategy execution

Pros:

- correct operational ordering
- easy to explain to operators
- keeps the existing apply path intact

Cons:

- needs a small helper pipeline after `Execute`

Recommended because it best matches the business requirement.

### 3. Persist a deferred override task and reconcile asynchronously

Pros:

- clean separation between strategy execution and inventory mutation

Cons:

- more moving parts
- slower feedback
- more state to reconcile

Rejected for now because the behavior is still ZB-specific and does not justify a new orchestration layer yet.

## Scope of Credential Overrides

The override pipeline supports exactly these credential families:

- in-band CLI: SSH or Telnet style username/password, with optional `auth_pass` and `auth_cmd`
- in-band SNMP v1/v2c
- in-band SNMP v3 USM
- out-of-band SNMP v1/v2c
- out-of-band SNMP v3 USM
- out-of-band IPMI
- out-of-band Redfish

Explicitly excluded:

- out-of-band SSH
- strategies that carry no recognizable credential fields

## Intent Extraction Rules

The implementation should not depend on a single hard-coded `StrategyID`. It should infer credential intent from parameter shape first, then optionally use template or strategy metadata as a tiebreaker.

### In-band CLI

Recognize when parameters include:

- `username` and `password`

Optional enrichers:

- `auth_pass`
- `auth_cmd`
- `login_method`
- `port`

Default plane:

- in-band

### SNMP v1/v2c

Recognize when parameters include:

- `community` or `snmp_community`

Optional:

- `version`
- `context_name`

Default plane:

- in-band unless explicit out-of-band markers exist

### SNMP v3

Recognize when parameters include:

- `sec_name` or `security_name` or `snmp_username`
- `sec_level` or `security_level`

And then validate by security level:

- `noAuthNoPriv`: requires `sec_name` + `sec_level`
- `authNoPriv`: additionally requires `auth_protocol` + `auth_password`
- `authPriv`: additionally requires `priv_protocol` + `priv_password`

Optional:

- `context_name`

### Out-of-band IPMI

Recognize when parameters include:

- `ipmi_username`
- `ipmi_password`

### Out-of-band Redfish

Recognize when parameters include:

- `redfish_username`
- `redfish_password`

### Plane Resolution

Plane selection order:

1. explicit plane fields such as `snmp_plane` or `plane`
2. `out_band_*` / `in_band_*` prefixes
3. template or strategy metadata that clearly indicates out-of-band collection
4. default fallbacks:
   - CLI -> in-band
   - generic SNMP -> in-band

## Materialization Rules

The override pipeline must convert plaintext strategy parameters into OneOps-managed credential objects before binding them to inventory.

### Naming and Reuse

Credential names must not leak plaintext values. Use stable, device-scoped names built from:

- device code
- plane
- credential kind
- normalized material fingerprint

Suggested patterns:

- secret: `zb-auto-<deviceCode>-<plane>-<kind>-<fingerprint>`
- SNMP community: `zb-auto-<deviceCode>-<plane>-snmpc-<fingerprint>`
- SNMP v3 USM: `zb-auto-<deviceCode>-<plane>-snmpv3-<fingerprint>`

`fingerprint` is a short prefix of `sha256` over normalized non-empty credential fields with deterministic ordering.

Reuse policy:

- same device + same plane + same kind + same fingerprint -> reuse existing credential object
- same device + same plane + same kind + different fingerprint -> create a new object and override bindings
- do not auto-share generated credentials across devices

### Storage Forms

- SNMP v1/v2c -> `Community`
- SNMP v3 USM -> unified credential object using the existing structured field map model
- CLI / IPMI / Redfish -> `Secret`

## Binding Rules

### Device V2

`device v2` should only store references, not plaintext.

Bindings:

- in-band CLI:
  - `credential_ref_in_band`
  - `credential_refs.in_band`
  - `credential_refs.in_band:ssh` or `credential_refs.in_band:telnet`
- in-band SNMP:
  - `snmp_credential_ref`
  - `credential_refs.snmp`
  - `credential_refs.in_band:snmp`
- out-of-band SNMP:
  - `credential_refs.out_band:snmp`
- out-of-band IPMI:
  - `credential_refs.out_band:ipmi`
- out-of-band Redfish:
  - `credential_refs.out_band:redfish`

When updating `device v2`, merge with existing non-credential attributes and only replace the relevant credential reference fields.

### Device V1

Use the existing role-binding APIs where the legacy model has a compatible concept.

Bindings:

- in-band CLI -> in-band secret role
- in-band SNMP -> in-band SNMP role
- out-of-band SNMP -> out-of-band SNMP role

Legacy limitations:

- if `device v1` has no first-class IPMI or Redfish role, do not invent a fake legacy binding
- in that case, `device v2` becomes the source of truth for out-of-band IPMI and Redfish

## Execution Flow

The override path runs inside the existing ZB async goroutine but after quick apply succeeds.

1. Build `QuickApplyStrategyRequest`
2. Execute `MetricStrategyQuickApplyService.Execute`
3. On success, resolve the target devices that should be updated
4. For each device:
   - extract credential intent from strategy parameters
   - materialize managed credential objects
   - bind `device v2`
   - bind `device v1`
   - log one structured audit record
5. Continue processing other devices even if one device override fails

## Error Handling

Error policy is intentionally asymmetric:

- strategy push failure -> no credential overrides
- strategy push success + override failure -> keep strategy success, report override failure separately
- `device v2` success + `device v1` failure -> no rollback of `device v2`
- one device override failure in a batch -> do not block other devices

This is not a transactional workflow across systems. The system should prefer accurate partial-result reporting over fake all-or-nothing behavior.

## Audit and Logging

Every override attempt must log:

- `device_code`
- `strategy_id`
- `template_id`
- `credential_kind`
- `plane`
- `result`
- `credential_fingerprint`

Never log plaintext values for:

- `community`
- `password`
- `auth_password`
- `priv_password`
- `ipmi_password`
- `redfish_password`

## SNMP V3 Compressed String Compatibility

If an upstream caller needs a single-field transport format for SNMP v3, support it only as an input compatibility layer, for example `snmp_v3_blob`.

Recommended format:

- `snmpv3:1:<base64url(json)>`

Rules:

- decode immediately at the API edge
- convert to structured SNMP v3 fields
- do not store the blob as the long-term internal representation

This preserves compatibility without weakening the current structured credential model.

## Code Boundaries

Primary implementation file:

- `OneOps/app/external_request/service/zb/impl/zb_call_service.go`

Suggested helper responsibilities:

- `extractZBStrategyCredentialIntent`
- `materializeZBStrategyCredentials`
- `bindZBStrategyCredentialsToDeviceV2`
- `bindZBStrategyCredentialsToDeviceV1`

Implementation should stay ZB-scoped rather than immediately generalizing into a global strategy apply framework.

## Testing Strategy

Minimum coverage matrix:

- in-band SNMP v2c override success
- in-band SNMP v3 override success
- out-of-band SNMP v2c override success
- out-of-band SNMP v3 override success
- in-band CLI override success
- out-of-band IPMI override success
- out-of-band Redfish override success
- strategy apply failure prevents overrides
- repeated identical parameters reuse existing credential objects
- different devices with identical parameters remain device-scoped
- partial override failure records errors without converting strategy success into failure

Preferred test locations:

- `OneOps/app/external_request/service/zb/impl/zb_call_service_test.go`
- `OneOps/app/external_request/service/zb/impl/zb_device_v2_store_test.go`
- optional new focused test file if existing harnesses are too noisy

## Open Decisions Resolved In This Design

- override policy: unconditional replacement
- execution timing: after successful strategy apply
- out-of-band SSH: excluded
- out-of-band scope: SNMP, IPMI, Redfish included
- SNMP v3 compressed string: input compatibility only, not internal storage

## Acceptance Criteria

- A successful ZB strategy push that carries recognized credentials updates the corresponding `device v2` credential references.
- The same successful push updates compatible `device v1` role bindings where a legacy role exists.
- Failed strategy pushes do not mutate inventory credentials.
- Override attempts are auditable without leaking plaintext secrets.
- Repeated pushes with the same device-scoped credential material reuse existing generated credential objects instead of creating duplicates endlessly.
