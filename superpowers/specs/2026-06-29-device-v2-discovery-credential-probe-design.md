# Device V2 Discovery Credential Probe Design

Date: 2026-06-29

## Summary

This design extends the existing Device V2 network discovery flow with a second-stage credential probe workflow.

The new flow keeps network scanning and credential validation separate:

1. `controller + nmap` performs network discovery and writes discovery candidates.
2. Users select candidate devices and provide a temporary credential pool for the current probe run.
3. OneOps resolves the selected credential refs, dispatches a controller-side probe RPC, and stores per-device per-protocol probe results.
4. Devices remain ingestible even if no credentials succeed.
5. Successful SSH and SNMP credentials are attached to the ingested device only after final confirmation rules are satisfied.

This design specifically avoids forcing users to manually enter or bind credentials during initial ingest when discovery can validate them first.

## Decisions Already Fixed

- `function_area` must be manually selected by the user when starting discovery.
- Discovery scope supports `single_ip`, `ip_range`, and `cidr`.
- Stage 1 discovery uses `controller + nmap`.
- Credential probing is a separate stage after network discovery, not part of the initial scan RPC.
- Users provide a temporary credential pool for each credential probe run.
- Devices are always allowed to ingest even if SSH and SNMP probes both fail.
- If SSH probe succeeds, the device should eventually bind an SSH credential.
- If SNMP probe succeeds, the device should eventually bind an SNMP credential.
- If multiple credentials succeed for the same protocol on the same device, all successes must be retained and the user must manually choose the final binding.
- SNMP reachability is not determined by `nmap` alone; final SNMP success is based on a real SNMP request.

## Goals

- Reduce manual credential entry during Device V2 ingest.
- Reuse the controller's network position for real SSH and SNMP validation.
- Preserve all successful credential candidates for later manual confirmation.
- Feed confirmed credential bindings directly into downstream collection and monitoring workflows.
- Keep plaintext credential material out of persistent discovery records.

## Non-Goals

- Auto-selecting a winner when multiple SSH or SNMP credentials succeed.
- Blocking ingest when no credential succeeds.
- Replacing the existing full collection pipeline with probe logic.
- Building a long-lived credential inventory per `function_area` in this phase.
- Solving generic out-of-band protocols such as IPMI or Redfish in the first release.

## User Workflow

### Phase 1: Network Discovery

1. User creates a discovery plan with `function_area`, scope, and port profile.
2. User runs discovery.
3. Controller executes `nmap` and returns candidate devices.
4. OneOps stores discovery candidates and shows them in the Device V2 discovery UI.

### Phase 2: Credential Probe

1. User selects one or more discovery candidates.
2. User clicks `凭证探测`.
3. User chooses a temporary probe credential pool for:
   - SSH credentials
   - SNMP credentials
4. User optionally keeps the default rule to only probe services that look reachable from stage 1 scan results.
5. OneOps resolves selected credential refs and dispatches the probe request to the controller for the candidate devices' `function_area`.
6. Controller tests SSH and SNMP using real protocol handshakes and returns per-credential results.
7. OneOps stores the detailed results and updates candidate-level summaries.

### Phase 3: Ingest

1. User ingests a candidate device.
2. If one SSH credential succeeded, OneOps can prefill the SSH binding.
3. If one SNMP credential succeeded, OneOps can prefill the SNMP binding.
4. If multiple credentials succeeded for a protocol, the user must choose the final binding before or during ingest confirmation.
5. The resulting Device V2 entity is created even if no credentials are chosen.

## Architecture

### Responsibility Split

#### OneOps

- Owns plans, runs, candidates, probe runs, probe results, and final binding decisions.
- Resolves selected credential refs before dispatching probe RPCs.
- Persists only credential refs and probe outcomes, not plaintext secrets.
- Applies final selected credential refs into Device V2 ingest payloads.

#### Controller

- Executes network discovery inside the selected `function_area`.
- Executes SSH and SNMP probe attempts from the network location where the controller is deployed.
- Returns structured probe results with protocol-specific status and lightweight diagnostics.

#### Frontend

- Keeps current discovery plan and run experience.
- Adds candidate selection, credential probe initiation, probe result display, and final binding confirmation.

## Data Model

### Existing Table

`device_v2_discovery_candidate` remains the durable record for stage 1 network discovery.

### New Table: `device_v2_discovery_probe_run`

Represents one batch credential probe request submitted by the user.

Suggested fields:

- `id`
- `code`
- `discovery_run_code`
- `function_area`
- `status`
- `selected_candidate_codes` JSON
- `selected_protocols` JSON
- `selected_credential_refs` JSON
- `options` JSON
- `started_at`
- `completed_at`
- `error_message`
- `created_at`
- `updated_at`

Status values:

- `pending`
- `running`
- `completed`
- `failed`

### New Table: `device_v2_discovery_probe_result`

Stores one probe attempt result for one device, one protocol, and one credential ref.

Suggested fields:

- `id`
- `code`
- `probe_run_code`
- `candidate_code`
- `protocol`
- `credential_ref`
- `probe_status`
- `detail`
- `latency_ms`
- `summary` JSON
- `observed_at`
- `created_at`
- `updated_at`

Probe status values:

- `success`
- `auth_failed`
- `timeout`
- `unreachable`
- `unsupported`
- `skipped`
- `error`

### Candidate-Level Summary Fields

Extend `device_v2_discovery_candidate` with summary fields for direct UI rendering:

- `ssh_probe_status`
- `snmp_probe_status`
- `ssh_success_count`
- `snmp_success_count`
- `selected_ssh_credential_ref`
- `selected_snmp_credential_ref`
- `probe_summary` JSON

These fields are summaries only. Detailed attempts remain in `device_v2_discovery_probe_result`.

## Candidate State Model

Candidate main state is not blocked by protocol success.

Suggested candidate states:

- `pending`
- `probing`
- `probe_partial`
- `probe_ready`
- `ingested`
- `ignored`

Protocol summaries are stored independently:

- `untested`
- `success`
- `failed`
- `ambiguous`

Interpretation:

- `probe_ready`: no unresolved multi-success conflict remains
- `probe_partial`: at least one protocol has multiple successful credentials awaiting manual choice

## Probe Rules

### SSH

- Only probe by default when the stage 1 candidate indicates SSH is likely reachable:
  - TCP port `22` is open, or
  - service fingerprint indicates SSH
- Final success is based on a real SSH authentication attempt.
- Controller should use a native Go SSH client path rather than shelling out to `sshpass`.

### SNMP

- `nmap` UDP `161` is only a weak hint.
- If UDP `161` is `open` or `open|filtered`, the candidate is eligible for SNMP probe.
- Final success is based on a real SNMP request, not on `nmap` alone.
- Probe should use `sysDescr.0` and may fall back to `sysObjectID.0`.

### Credential Selection

- Users supply a temporary set of credential refs per probe run.
- OneOps resolves them just in time for this run.
- Controller receives only the minimum protocol material required to probe.
- Persistent records keep only the original `credential_ref`.

## Controller RPC Design

### Existing RPC

- `DeviceDiscovery.Scan`

### New RPC

- `DeviceDiscovery.ProbeCredentials`

Suggested request shape:

```json
{
  "probe_run_code": "DPR-001",
  "function_area": "fa-prod-a",
  "candidates": [
    {
      "candidate_code": "DC-001",
      "ip": "10.10.10.1",
      "open_ports": [22, 161],
      "service_fingerprints": ["ssh", "snmp"]
    }
  ],
  "protocols": ["ssh", "snmp"],
  "ssh_credentials": [
    {
      "credential_ref": "cred-ssh-01",
      "username": "ops",
      "password": "runtime_resolved_secret"
    }
  ],
  "snmp_credentials": [
    {
      "credential_ref": "cred-snmp-01",
      "version": "2c",
      "community": "runtime_resolved_secret"
    }
  ],
  "options": {
    "ssh_timeout_sec": 5,
    "snmp_timeout_sec": 3,
    "snmp_retry": 1,
    "only_probe_discovered_ports": true
  }
}
```

Suggested response shape:

```json
{
  "controller_id": "ctrl-001",
  "status": "completed",
  "results": [
    {
      "candidate_code": "DC-001",
      "protocol": "ssh",
      "credential_ref": "cred-ssh-01",
      "probe_status": "success",
      "latency_ms": 182,
      "summary": {
        "banner": "SSH-2.0-OpenSSH_8.4"
      }
    }
  ]
}
```

The request examples above show transient runtime payload fields only. They must not be persisted into discovery tables or logs in plaintext form.

## Controller Protocol Implementation

### SSH Probe

Use `golang.org/x/crypto/ssh`:

- connect TCP
- complete SSH handshake
- authenticate using password or private key
- optionally establish a session

Success means the credential is valid and the session was established. No vendor-specific command parsing is required for phase 1.

### SNMP Probe

Use a native SNMP library such as `gosnmp`:

- v2c with community
- v3 with auth/priv settings in later phase
- perform `GET sysDescr.0`
- optionally retry with `GET sysObjectID.0`

Success means the target responded with valid SNMP data.

## Backend API Design

Suggested endpoints:

- `POST /api/v1/device/v2/discovery/probe-runs`
  - create and start a credential probe run
- `GET /api/v1/device/v2/discovery/probe-runs/:code`
  - query probe run status
- `GET /api/v1/device/v2/discovery/candidates/:code/probe-results`
  - list detailed probe attempts for one candidate
- `POST /api/v1/device/v2/discovery/candidates/:code/credential-selection`
  - save final chosen SSH and SNMP credential refs

Existing ingest approval endpoints should be extended to consume the selected binding state.

## Frontend Design

### Candidate List

Add:

- row selection
- `凭证探测` batch action
- `SSH` probe summary column
- `SNMP` probe summary column
- selected credential display columns

### Probe Modal

The modal should allow the user to:

- choose one or more candidate devices
- provide temporary SSH credential refs
- provide temporary SNMP credential refs
- choose whether to only probe ports indicated by discovery

### Candidate Detail

Each candidate should show:

- all successful SSH credential refs
- all successful SNMP credential refs
- failed attempt summaries
- final selected binding state

### Ingest Confirmation

During ingest:

- if no protocol succeeded, allow ingest with warning
- if exactly one protocol credential succeeded, prefill the binding
- if multiple credentials succeeded for a protocol, require user choice before final confirmation if they want that protocol bound

## Ingest Mapping

When a final credential is selected:

- SSH should populate `credential_ref_in_band`
- SNMP should populate `snmp_credential_ref`

If the repo continues to standardize on structured bindings, ingest may also mirror the choice into:

- `credential_refs["in_band:ssh"]`
- `credential_refs["in_band:snmp"]`

The first release should still ensure compatibility with current downstream collectors that expect legacy top-level fields.

## Security

- OneOps resolves credential refs only for the lifetime of the probe dispatch.
- Plaintext credential material must not be written into discovery candidate, probe run, or probe result tables.
- Controller must not persist plaintext credential material beyond the in-memory probe execution path.
- Logs must redact secret payloads and only reference `credential_ref`.

## Error Handling

- Probe run failure should not alter existing discovery candidates beyond marking the probe run failed.
- Per-attempt failures should still be stored as results.
- A controller-wide RPC failure marks the probe run `failed`.
- Partial per-device failures still allow the probe run to complete with mixed results.

## Rollout Plan

### Phase 1

- add controller RPC for SSH and SNMP probe
- add backend tables and APIs
- add candidate-level summaries
- add frontend batch probe and manual selection flow
- extend ingest to consume selected bindings

### Phase 2

- add SNMP v3 support
- add SSH private key support
- improve diagnostics and failure reason display
- support batch confirmation UX improvements

### Phase 3

- add operational analytics such as credential success rates
- add reuse helpers for frequent probe choices
- add downstream warnings when a device ingests without required credentials

## Testing

### Backend

- probe run lifecycle tests
- candidate summary aggregation tests
- final binding selection tests
- ingest mapping tests

### Controller

- SSH success, auth failure, timeout, unreachable
- SNMP success, bad community, timeout
- skipped probes when service is not indicated by discovery metadata

### Frontend

- batch probe initiation smoke test
- multi-success selection modal behavior
- ingest confirmation with selected bindings

## Risks

- Controller-side protocol libraries may expose environment-specific timing issues.
- UDP `161` heuristics can still produce many attempts against silent drops.
- Allowing ingest without credentials may create devices that cannot immediately collect.
- The temporary credential pool UX must remain simple enough to be usable at scale.

## Open Implementation Notes

- Reuse the current discovery `function_area` routing path and OneOps-to-controller caller abstraction.
- Prefer adding a dedicated probe RPC instead of overloading collection endpoints intended for vendor-aware command execution.
- Keep the first release scoped to in-band SSH and in-band SNMP.
