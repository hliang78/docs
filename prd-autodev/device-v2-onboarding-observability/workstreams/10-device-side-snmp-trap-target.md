# Workstream 10 - Device-Side SNMP Trap Target

## Goal

Add device-side SNMP trap target delivery to Device V2 onboarding, using the already completed area `snmp_trap_listener` publish path as the collector-side endpoint.

## Current Code Facts

- Area listener page and collector-side `snmp_trap_listener` publish are already closed in `D2ON-034` / `D2ON-035`.
- Device-side syslog delivery is implemented for:
  - server rsyslog forwarding
  - H3C/Comware network syslog target configuration
- `EnsureOnboarding` chooses log listener service types for syslog:
  - `server_syslog_listener`
  - `network_syslog_listener`
- `EnsureOnboarding` now also evaluates a separate `snmp_trap_target` action for supported network devices by resolving the managed `snmp_trap_listener`.
- The `snmp_trap_target` action evidence is persisted separately from syslog `log_forward` evidence.
- Before continuing this workstream, `D2ON-045` ran a full all-device collection validation gate. The usable next probes should be chosen from the 11 `success/ready` devices, while the 6 `blocked/unready` devices remain exact per-device blockers.

## Requirements

- Resolve the managed `snmp_trap_listener` endpoint for the device's function area.
- Start with one concrete network profile: H3C/Comware.
- Use controller `/api/v1/remote/run` for device-side commands, matching the existing network syslog delivery pattern.
- Configure, save, and verify trap target readback.
- Unsupported vendors must fail closed with an exact blocker and no success paraphrase.
- Evidence must include listener plan identity, endpoint, vendor/profile, controller status, remote exit code, and verify-match result.

## Non-Goals

- No device-side trap target delivery for every vendor in the first story.
- No collector-side listener reimplementation.
- No Prometheus/Loki/trap arrival assertion as the success gate.
- No credential material in persisted evidence.

## Acceptance Shape

- H3C/Comware command template is unit-tested. Closed by `D2ON-046`.
- Onboarding evidence records `snmp_trap_target` action truth separately from syslog action truth. Closed by `D2ON-047`.
- A live probe configures the trap target and verifies readback on a ready H3C/Comware device. Closed by `D2ON-048`.

## 2026-05-18 D2ON-046 Command Layer

- Added the first H3C/Comware SNMP trap target command/profile layer beside the existing network syslog profile helpers.
- Template identity: `h3c_comware_snmp_trap_target`.
- Commands include `system-view`, `snmp-agent`, `snmp-agent trap enable`, target-host configuration, `save force`, and readback via `display current-configuration | include snmp-agent target-host`.
- Default listener handling is explicit: `snmp_trap_listener` maps to `teleabs_template:snmp_trap` and UDP/162.
- Unsupported network platforms return `unsupported network snmp trap target template`.
- Controller execution was intentionally deferred to `D2ON-047` and is now closed there.

## 2026-05-18 D2ON-047 Controller Execution

- Connected managed `snmp_trap_listener` resolution into onboarding ensure.
- Added controller `/api/v1/remote/run` execution for the H3C/Comware trap target profile.
- Persisted `snmp_trap_target` evidence separately from `log_forward`, including listener identity, endpoint, controller status, remote exit code, template ID, verify command, and verify match.
- Trap security name is resolved from Device V2 SNMP credential references and redacted from persisted evidence.

## 2026-05-18 D2ON-048 Live Probe

- Ready H3C/Comware device: `DVCD25E1C13D3C3`, IP `172.32.2.14`.
- Managed trap listener: `4a7eb57e-5268-11f1-91aa-a61f7c1de05a`, endpoint `192.168.100.6:162`.
- Final `snmp_trap_target` result: `status=success`, `controller_remote_success=true`, `remote_exit_code=0`, `snmp_trap_target_status=configured`, `snmp_trap_verify_match=true`.
- Workstream status: completed for the first H3C/Comware device-side SNMP trap target scope.
