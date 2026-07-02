# Device V2 Access Resolver Phase 1 Design

## Goal

Land the first credential-governance subproject by unifying the read path for
device access and credential bindings.

Phase 1 is intentionally limited to read-time normalization. It does not yet
change credential CRUD or binding write entry points.

## Scope

Implement a reusable `AccessResolver` for `device_v2` and migrate these read
consumers to use it:

- `device_collection2` target building
- `monitor push` credential-binding checks
- `task fanout` / `task asset precheck`

Out of scope for Phase 1:

- `ingest`, `discovery`, `zb store`, `zb override` write-path refactors
- `terminal`, `guacd`, `webshell`
- `zb call` ephemeral credential separation
- credential materialization unification

## Problem

Current consumers independently re-interpret:

- `attributes.access_points`
- `attributes/metadata.credential_refs`
- legacy fields such as `credential_ref_in_band`, `credential_ref_out_band`,
  `snmp_credential_ref`

This creates drift between collection, monitoring, and task execution.

## Design

Add a cross-package resolver in `app/device/v2/service` so consumers do not
depend on an `impl` package and can share one normalization rule set.

### Public model

`ResolvedAccessPoint`

- `ID`
- `Plane`
- `Protocol`
- `Address`
- `Port`
- `CredentialRef`
- `Source`
- `LegacyBacked`

### Public functions

- `ResolveAccessPoints(device *model.DeviceV2) []ResolvedAccessPoint`
- `ResolvePreferredAccessPoint(device *model.DeviceV2, plane string, protocols ...string) (*ResolvedAccessPoint, bool)`
- `ResolveCredentialBindings(device *model.DeviceV2) map[string]string`

### Resolution rules

1. Prefer explicit `access_points`.
2. If an explicit access point omits `credential_ref`, infer it from
   `credential_refs` and legacy fields using the access point's
   `plane + protocol`.
3. If no explicit access point exists for a needed protocol, synthesize a
   legacy-backed access point from top-level fields.
4. Structured access points win over legacy projections for the same
   `plane + protocol`.

### Binding projection

Resolver also projects normalized bindings for read consumers:

- `default`
- `in_band`, `in_band:ssh`, `in_band:telnet`, `in_band:winrm`
- `snmp`, `in_band:snmp`
- `out_band`, `out_band:ssh`, `out_band:telnet`
- `out_band:snmp`, `snmp_outband`
- `out_band:ipmi`, `ipmi_outband`
- `out_band:redfish`, `redfish_outband`

## Consumer migration

### device_collection2

Use `ResolvePreferredAccessPoint` for:

- in-band CLI
- in-band SNMP

Keep existing SNMP inline parameter parsing unchanged in Phase 1.

### monitor push

Replace ad-hoc merging of `credential_refs + legacy fields + access_points`
with `ResolveCredentialBindings`.

### task fanout / task asset precheck

Replace direct legacy/ref probing with `ResolvePreferredAccessPoint` and fall
back to task-level `credential_ref` only when device binding is absent.

## Acceptance

- No new read logic directly interprets `credential_ref_in_band`,
  `credential_ref_out_band`, or `snmp_credential_ref`.
- `device_collection2`, `monitor push`, and `task fanout` read through the
  resolver.
- Legacy data still works through compatibility projection.
- Structured `access_points` take precedence over legacy fallback.
