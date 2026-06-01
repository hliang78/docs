# Live Agent Deployment Evidence - 2026-05-18

## Verdict

- `agent-deployment-result`: **successful on real device**.
- `deployment_id`: `deploy-0fc9c7b1`
- `device_code`: `DVC8D386DCF00A0`
- `function_area`: `DefaultArea`
- `agent_package_version`: `v0.0.1-debug-demo`
- `deployment_created_at`: `2026-05-18T13:46:38+08:00`
- `deployment_completed_at`: `2026-05-18T13:47:42+08:00`
- `overview_result`: `completed`, `1/1` succeeded.

## Platform Evidence

- Created through `POST /api/v1/platform/deployments/agent`.
- Deployment device logs showed the full chain: download `deployment-agent`, resolve agent package URL, download zip, unzip, stop old service, write systemd unit, start new service, and finish with `deployment-agent completed successfully`.
- `GET /api/v1/platform/agents/agent-DVC8D386DCF00A0-39f957d8` returned `online`, `deviceID=DVC8D386DCF00A0`, `deployedAt=2026-05-18T13:47:37+08:00`.
- Agent capabilities included `teleabs_template:syslog` and `teleabs_template:snmp_trap`.

## Remote Evidence

- On `192.168.100.6`, `agent.service` restarted successfully at `2026-05-18T13:47:37+08:00`.
- Main process PID after restart: `940016`.
- `ss -lunp` showed UDP `*:514` and `*:162` both listened by `agent`.
- `/var/log/agent/agent.log` showed the old process received `terminated` at `13:47:33`, the new process started at `13:47:37`, and restored 5 persisted tasks including `syslog-hybrid` and `snmp-trap-hybrid` inputs.

## Residual Platform Projection Bug

- `GET /api/v1/platform/devices/DVC8D386DCF00A0` still returned `hasAgent=false` and `agentCode=null` after the real deployment succeeded.
- This is a device-detail projection / relation read bug, not evidence against deployment success.
- Current-session code diagnosis: Bidi Device V2 detail conversion returned `DeviceV2ToDetailInfo` without enriching from `platform_agent`; legacy detail lookup also had a code-vs-ID mismatch risk because deployment writes `platform_agent.device_id` as the device business code while one detail path queried by row UUID ID.
- Current-session fix: Bidi Device V2 detail/list projection and legacy detail projection now read the preferred `platform_agent` record by device business code first, while still accepting the row ID as a compatibility key.

## Follow-Up

- After OneOPS is rebuilt/restarted with the current-session patch, re-check `GET /api/v1/platform/devices/DVC8D386DCF00A0`; expected projection is `hasAgent=true` and `agentCode=agent-DVC8D386DCF00A0-39f957d8`.
- Re-running onboarding/ensure should be treated as the next product-flow validation, separate from the already successful agent deployment result.
