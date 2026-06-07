# Netlink Maipu/FiberHome Manual Confirmation

Date: 2026-06-06

This runbook is for one-time human confirmation after the offline Netmiko-to-netlink profile backfill. Automated tests must stay offline and must not repeatedly log in to production devices.

## Scope

- Already accepted without extra confirmation:
  - Huawei VRP
  - Huawei USG
  - H3C Comware
  - H3C SecPath
- Needs manual confirmation:
  - Maipu MyPower first
  - FiberHome Fengine second

## Maipu MyPower

Netmiko source used: `/OneOPS/netmiko/netmiko/maipu/maipu.py`

Expected profile:

- auth command: `enable`
- prompt pattern: borrows Cisco IOS prompt handling for `hostname#`, `hostname>`, and config-mode prompts
- pager disable command: `more off`
- save command: `write`
- backup read command used by OneOPS: `show run`
- observed pager prompt before `more off`: `---MORE---`
- observed command errors:
  - `% Invalid input detected at '^' marker`
  - `% Unknown command`
  - `%Bad IP address or unknown hostname!`
  - `% Ambiguous command: s`
- logout command for manual sessions: `exit`
- observed `quit` behavior at `>` prompt: `quit` is rejected with `% Invalid input detected at '^' marker`; use `exit` when an interactive/manual session needs to log out.

Human check:

1. Log in to one Maipu device once.
2. Confirm `enable` reaches privileged mode.
3. Run `more off` and confirm it is accepted.
4. Run `show run` and confirm it returns configuration output without paging.
5. Run `exit` to close the manual session.
6. Do not run `write` unless the maintenance window explicitly allows a save operation.

## FiberHome Fengine

Netmiko does not provide a FiberHome/Fengine driver. Do not reuse `fiberstore_*` behavior as a substitute.

Expected provisional profile:

- auth command: `enable`
- pager disable command: `terminal length 0`
- save command: `write`
- backup read command used by OneOPS: `display current-configuration`

Human check:

1. Log in to one FiberHome device once.
2. Confirm `enable` reaches privileged mode.
3. Run `terminal length 0` and record whether it is accepted.
4. Run `display current-configuration` and record whether it returns configuration output.
5. If either command is rejected, record the accepted FiberHome equivalent and update:
   - `/OneOPS/netlink/configs/mode_configs/fiberhome_fengine_v1.yaml`
   - `/OneOPS/ctrlhub/controller/deploy/templates/fiberhome/fengine/mode_config/base_mode_config.yaml`
   - `/OneOPS/ctrlhub/controller/deploy/templates/mode_configs/fiberhome_fengine_v1.yaml`
   - `/OneOPS/quick_env/init-configs/gitea/source-repo/ansible/network-config-backup/site.yml`
