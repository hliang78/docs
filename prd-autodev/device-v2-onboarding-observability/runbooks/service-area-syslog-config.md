# Service Area Syslog Configuration Runbook

Purpose: record how a service area configures a managed syslog listener so future automation can turn the current manual flow into a repeatable script.

## Boundary

This runbook covers the service-area side:

- Select a service area / function area.
- Select an online collector agent in that area.
- Create or update an area listener contract.
- Publish/apply the listener to the collector agent.
- Verify that the collector agent is listening on UDP syslog.

This runbook does not cover device-side delivery, except for recording the handoff values that device onboarding consumes later:

- `listener_service_type`
- `listener_plan_id`
- `collector_agent_code`
- `agent_ip`
- `agent_port`

## Live Values From D2ON-039

- Function area: `DefaultArea`
- Listener service type: `server_syslog_listener`
- Listener plan id: `fd5ee4f4-51fd-11f1-8781-a61f7c1de05a`
- Listener plan name: `DefaultArea-agent-DVC8D386DCF00A0-39f957d8-server-syslog-listener`
- Collector agent code: `agent-DVC8D386DCF00A0-39f957d8`
- Collector agent IP: `192.168.100.6`
- Listener endpoint: `udp://0.0.0.0:514`
- Device-side delivery target value: `192.168.100.6:514`
- Publish model: `log_forward_plan`
- Collector template id: `syslog-hybrid`

## Manual UI Flow

1. Open `#/platform/area-listener-services`.
2. Click one of:
   - `新建服务器 Syslog` for `server_syslog_listener`.
   - `新建网络 Syslog` for `network_syslog_listener`.
3. Select the function area.
4. Select an online collector agent in that function area.
5. Keep the listener endpoint as UDP `0.0.0.0:514` unless the area requires a different port.
6. Save the listener plan.
7. Open the release modal for the saved row.
8. Run `dry-run`, then `preflight`, then `apply`.
9. Treat the service-area listener as ready only when apply evidence says:
   - `listener_publish.publish_model=log_forward_plan`
   - `listener_publish.listener_service_type` matches the requested service type
   - `listener_publish.listener_protocol=syslog`
   - `last_apply_status=converged`

## API Shape For Future Automation

The current implementation intentionally reuses `remote_syslog / log_forward_plan` instead of adding a second listener model. Future scripts should call the same platform APIs that the page calls, with an explicit listener contract in `target_scope`.

Required logical fields:

```json
{
  "function_area": "DefaultArea",
  "plan_type": "remote_syslog",
  "listener_service_type": "server_syslog_listener",
  "collector_agent_code": "agent-DVC8D386DCF00A0-39f957d8",
  "target_scope": {
    "listener_service_type": "server_syslog_listener",
    "listener_service": {
      "service_type": "server_syslog_listener",
      "protocol": "syslog",
      "listen_address": "udp://0.0.0.0:514"
    },
    "adapter_extension": {
      "publish_model": "log_forward_plan",
      "listener_service_type": "server_syslog_listener",
      "listener_protocol": "syslog",
      "collector_agent_code": "agent-DVC8D386DCF00A0-39f957d8",
      "listener_template_id": "syslog-hybrid"
    }
  }
}
```

Automation should persist the created plan id and then call the release operations in order:

```text
create/update log_forward_plan
dry-run log_forward_plan
preflight log_forward_plan
apply log_forward_plan
read back log_forward_plan
```

The script must fail closed if `listener_service_type` is absent. Legacy `remote_syslog` rows without `listener_service_type` are not a managed area listener contract and must not be consumed by Device V2 onboarding.

## Collector-Side Publish Semantics

For syslog listeners:

- `server_syslog_listener` and `network_syslog_listener` both publish collector-side syslog listener config through `syslog-hybrid`.
- The distinction is product semantics and downstream onboarding selection, not a separate collector template.
- The area listener publish evidence is attached as `listener_publish` in dry-run/preflight/apply responses.

Minimum apply evidence for success:

```json
{
  "listener_publish": {
    "publish_model": "log_forward_plan",
    "listener_service_type": "server_syslog_listener",
    "listener_protocol": "syslog",
    "listener_template_id": "syslog-hybrid",
    "collector_agent_code": "agent-DVC8D386DCF00A0-39f957d8"
  },
  "last_apply_status": "converged"
}
```

## Runtime Verification

After apply, verify on the collector host:

```bash
ss -lunp | grep ':514'
```

Expected shape:

```text
udp ... 0.0.0.0:514 ... agent
```

The D2ON live environment has previously verified that the collector agent restored both `syslog-hybrid` and `snmp-trap-hybrid` inputs after deployment.

## Device Onboarding Handoff

Once the service-area listener is converged, Device V2 onboarding consumes the managed listener contract by matching:

```text
function_area + plan_type=remote_syslog + listener_service_type
```

For a server device, onboarding then performs device-side syslog delivery:

- Resolve `credential_ref_in_band`.
- SSH to the server.
- Write `/etc/rsyslog.d/90-oneops-device-v2-forward.conf`.
- Configure:

```text
*.* @<collector-agent-ip>:<listener-port>
```

- Restart rsyslog.
- Verify the file contains the listener endpoint.

Current server-side script prototype:

```bash
#!/usr/bin/env bash
set -eu

listener_host="${ONEOPS_SYSLOG_LISTENER_HOST:?ONEOPS_SYSLOG_LISTENER_HOST is required}"
listener_port="${ONEOPS_SYSLOG_LISTENER_PORT:-514}"
oneops_sudo_password="${ONEOPS_SUDO_PASSWORD:-}"
conf_path="${ONEOPS_RSYSLOG_CONF_PATH:-/etc/rsyslog.d/90-oneops-device-v2-forward.conf}"

if ! command -v rsyslogd >/dev/null 2>&1; then
  echo oneops_rsyslog_missing
  exit 42
fi

run_privileged() {
  if [ "$(id -u)" = "0" ]; then
    "$@"
    return
  fi
  if [ -n "$oneops_sudo_password" ]; then
    printf '%s\n' "$oneops_sudo_password" | sudo -S -p '' "$@"
    return
  fi
  sudo -n "$@"
}

tmp_file="$(mktemp)"
printf '%s\n' \
  '# Managed by OneOPS Device V2 onboarding' \
  '*.* @'"${listener_host}"':'"${listener_port}" > "$tmp_file"

run_privileged mkdir -p /etc/rsyslog.d
changed=0
if [ ! -f "$conf_path" ] || ! cmp -s "$tmp_file" "$conf_path"; then
  run_privileged cp "$tmp_file" "$conf_path"
  changed=1
fi
rm -f "$tmp_file"

if command -v systemctl >/dev/null 2>&1; then
  run_privileged systemctl restart rsyslog
else
  run_privileged service rsyslog restart
fi

run_privileged grep -F '@'"${listener_host}"':'"${listener_port}" "$conf_path" >/dev/null
unset oneops_sudo_password
echo "oneops_syslog_forwarding_configured changed=${changed}"
```

Runtime variables:

```text
ONEOPS_SYSLOG_LISTENER_HOST=<collector-agent-ip>
ONEOPS_SYSLOG_LISTENER_PORT=<listener-port, default 514>
ONEOPS_SUDO_PASSWORD=<optional, from resolved SSH credential password>
ONEOPS_RSYSLOG_CONF_PATH=/etc/rsyslog.d/90-oneops-device-v2-forward.conf
```

The current Go implementation renders the same logic inline for controller `/api/v1/remote/run`. Future automation can either keep rendering the script body or upload this script as a managed artifact and pass the variables at execution time.

For a network device, onboarding performs device-side syslog delivery through controller `target.type=network_device`. The D2ON-040 live probe verified the H3C/Comware path:

```json
{
  "target": {
    "type": "network_device",
    "host": "<device-in-band-ip>",
    "port": 22,
    "protocol": "ssh"
  },
  "profile": {
    "vendor": "h3c",
    "platform": "comware"
  },
  "commands": [
    "system-view",
    "info-center enable",
    "info-center loghost <collector-agent-ip> port <listener-port>",
    "quit",
    "save force",
    "display current-configuration | include info-center"
  ]
}
```

The live validated values were:

```text
device_code=DVCD25E1C13D3C3
device_host=172.32.2.14
listener_service_type=network_syslog_listener
listener_plan_id=04f03968-5283-11f1-9041-a61f7c1de05a
collector_agent_code=agent-DVC8D386DCF00A0-39f957d8
collector_agent_ip=192.168.100.6
listener_port=514
network_vendor=h3c
network_platform=comware
```

Verification reads back:

```text
display current-configuration | include info-center
```

H3C/Comware may omit the default syslog port `514` in `display current-configuration`, so automation should treat `info-center loghost <collector-agent-ip>` as success when the listener port is `514`; for non-default ports, the port must also be present in the readback.

The service-area script should not do this device-side step. It should only output the handoff tuple needed by device onboarding:

```json
{
  "listener_plan_id": "fd5ee4f4-51fd-11f1-8781-a61f7c1de05a",
  "listener_service_type": "server_syslog_listener",
  "collector_agent_code": "agent-DVC8D386DCF00A0-39f957d8",
  "agent_ip": "192.168.100.6",
  "agent_port": 514
}
```

## Automation Notes

- Inputs should be `function_area`, `listener_service_type`, optional `collector_agent_code`, and optional `port`.
- If `collector_agent_code` is omitted, choose an online area agent with `teleabs_template:syslog`.
- Refuse to continue if the selected agent is offline or has no syslog capability.
- Prefer idempotent update when a converged listener already exists for the same `function_area + listener_service_type`.
- Do not store credentials or raw controller response bodies in evidence.
- Store only parsed evidence: status, plan id, agent code, listener protocol, template id, remote exit code if applicable, and stdout/stderr summaries.
