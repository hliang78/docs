# Netlink Platform Adapter Backfill Design

Date: 2026-06-06

## Goal

Backfill OneOPS `netlink` platform adapter coverage by using Netmiko's platform behavior as a reference, while keeping OneOPS execution native to Go `netlink`.

The first delivery scope is read-only network device execution:

- configuration backup commands
- batch show/display commands
- offline validation of platform profile files

Configuration push, save, policy modification, and repeated automated device login are out of scope.

## Confirmed Platforms

The following platforms do not require new manual confirmation before the first backfill:

- Huawei VRP
- Huawei USG
- H3C Comware
- H3C SecPath

These can be treated as known platforms and aligned using existing OneOPS templates plus Netmiko reference behavior.

## Platforms Requiring Manual Confirmation

Manual confirmation is limited and ordered:

1. Maipu MyPower
2. FiberHome Fengine

Automated tests must not repeatedly log in to these devices. After static backfill, an operator will manually confirm each platform once using a short checklist.

## Reference Mapping

| OneOPS platform | Netmiko reference | Netlink target profile |
| --- | --- | --- |
| Huawei VRP | `huawei_vrp`, `huawei` | `huawei/vrp` |
| Huawei USG | Huawei VRP behavior reference | `huawei/usg` |
| H3C Comware | `h3c_comware`, `hp_comware` | `h3c/comware` |
| H3C SecPath | Comware behavior reference | `h3c/secpath` |
| Maipu MyPower | `maipu` | `maipu/mypower` |
| FiberHome Fengine | no direct Netmiko match | `fiberhome/fengine` |

FiberHome must not be mapped to Netmiko `fiberstore_*`; Fiberstore and FiberHome are different vendors.

## Design

### Platform Profile Backfill

Backfill and normalize the profile data in:

- `netlink/configs/mode_configs/*.yaml`
- `ctrlhub/controller/deploy/templates/*/*/mode_config/base_mode_config.yaml`
- `ctrlhub/controller/deploy/templates/*/*/collect/base/ssh_*.yaml`
- `ctrlhub/controller/deploy/templates/*/*/version_map.yaml`

Each platform profile should define:

- prompt regexes
- possible prompt regexes where needed
- pager prompt regexes
- pager response command
- init commands for read-only sessions
- configuration backup command
- common read-only show/display commands
- error prompt regexes

### Read-Only Execution Rules

The backfilled profiles must be safe for read-only workflows:

- Disable paging where supported.
- Avoid entering configuration mode unless the platform requires it for a confirmed read-only command path.
- Do not include save commands in read-only backup or show command workflows.
- Treat save/config commands as a future, separate scope.

Existing `mode_config` files may still contain `save_commands` for other workflows, but the read-only task profiles must not invoke them.

### Task-Center Alignment

The Ansible task-center scripts currently rely on a coarse `vendor_family` model. They should be aligned to OneOPS platform names:

- `network_vendor`
- `network_platform`
- `device_role`

The immediate failure in `network-config-backup/site.yml` also needs a separate fix for self-referential variables:

- `huawei_backup_command`
- `h3c_backup_command`

Those variables must be renamed to resolved variables or used inline with `default(...)`.

### Manual Confirmation

After static backfill, manual confirmation should run only for Maipu first, then FiberHome:

- login prompt recognized
- password prompt recognized
- paging disabled
- configuration backup command returns full output
- LLDP command behavior confirmed or marked unsupported
- MAC table command behavior confirmed or marked unsupported
- interface summary command behavior confirmed or marked unsupported
- error prompt behavior observed for one intentionally unsupported command

Manual confirmation output should be summarized and used to update the profile. The confirmation flow should avoid repeated loops.

## Offline Validation

Automated tests should be offline only:

- YAML parse tests for all touched profiles
- platform mapping tests
- regex fixture tests for prompt, pager, and error prompts
- command matrix presence tests
- task script variable recursion tests

No test should open SSH or Telnet sessions.

## Success Criteria

- Netlink has explicit profile coverage for Huawei VRP, Huawei USG, H3C Comware, H3C SecPath, Maipu MyPower, and FiberHome Fengine.
- Maipu and FiberHome are not blindly copied from H3C without platform-specific comments or pending-confirmation markers.
- Task-center backup scripts stop failing from recursive variables.
- Unsupported or unconfirmed platform behavior fails with a clear platform-specific message.
- All automated validation is offline and repeatable.

## Non-Goals

- No repeated automated login to production devices.
- No automatic configuration push.
- No automatic save operation.
- No Python Netmiko runtime dependency in the production path.
- No FiberHome to Fiberstore aliasing.
