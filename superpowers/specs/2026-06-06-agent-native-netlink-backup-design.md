# Agent Native Netlink Backup Design

## Goal

Network device backup should be executed by OneOPS agent/controller native code, with netlink used as a Go library. Ansible remains available for generic automation, but it should not be the primary runtime dependency for network device command execution.

## Current State

The Maipu path works today through an Ansible playbook that shells out to `netlink-backup`. This proved the netlink device behavior and Maipu mode config, but it leaves three avoidable deployment requirements on every target agent:

- `ansible-playbook`
- `netlink-backup`
- `/etc/netlink/configs`

The most fragile part was not Maipu prompt handling. It was credential propagation through Ansible delegation. When a task uses `delegate_to: localhost`, Ansible variable context can resolve `ansible_user` to the local process user unless the controller explicitly injects the credential username.

## Target Architecture

For network configuration backup, the agent receives a native task type and calls a netlink backup service in-process.

```text
Controller RunTask
  -> agent RunTask handler
  -> native app_type=network_config_backup
  -> netlink backup package
  -> SSH/Telnet device login and command execution
  -> OneOPS artifact manifest and result
  -> controller artifact upload/reporting
```

The initial implementation keeps the existing Ansible playbook as a fallback and migration reference. It adds a new native path rather than removing the working path.

## Components

### netlink backup package

Create a reusable package under the netlink module. The existing `cmd/netlink-backup` logic moves into this package with a small public API:

- Request fields: host, port, username, password, private key, auth pass, mode, command, output path, config dir, timeouts, verbose.
- Result fields: output text, command, mode, config paths, duration, output size.
- The CLI becomes a thin wrapper around this package.

This lets the same code serve both manual CLI use and agent-native task execution.

### agent native runner

Add a new agent runner for:

```text
app_type: network_config_backup
```

The runner resolves credentials through the existing execution profile path, parses task parameters from `extra_vars_json` and `arguments`, calls the netlink backup package, writes artifacts into `ONEOPS_OUTPUT_DIR`, and returns a `runtime_output` compatible with the existing artifact upload flow.

### configuration

The first iteration continues to load netlink YAML configs from a local config directory. The default search order should be:

1. `netlink_config_dir` from task input
2. `NETLINK_CONFIG_DIR`
3. bundled or installed agent config dir
4. `/etc/netlink/configs`

Bundling configs inside the agent package is a packaging/deployment step after the native runner lands.

## Task Input Contract

Native backup task input is intentionally close to the current Ansible extra vars:

```json
{
  "app_type": "network_config_backup",
  "extra_vars_json": {
    "target_host": "172.21.253.9",
    "target_port": 22,
    "vendor_family": "maipu",
    "network_backup_command": "show run",
    "network_backup_tag": "netlink-maipu-test",
    "netlink_config_dir": "/etc/netlink/configs",
    "netlink_login_timeout": 30,
    "netlink_command_timeout": 180,
    "netlink_no_output_timeout": 15
  },
  "execution_profile": {
    "resolved_credential": {
      "username": "...",
      "password": "...",
      "auth_pass": "..."
    }
  }
}
```

The native runner must not require credential values in `extra_vars_json`.

## Artifact Contract

The runner writes the same artifact shape as the Ansible playbook:

- `network-config-backup-<safe-host>.cfg`
- `network-config-backup-<safe-host>.json`

The config artifact is marked sensitive. The summary JSON contains non-secret metadata:

- host
- mode
- command
- backup tag
- output size
- backup engine: `netlink-native`

## Error Handling

Errors should be returned with operator-friendly messages while avoiding secret leakage:

- missing host
- missing username
- missing password/private key
- unsupported vendor family
- missing netlink config file
- login failed
- privilege/init failed
- command timeout
- no-output timeout
- command execution failed
- artifact write failed

The first implementation can return string errors, but the netlink package API should leave room for typed errors later.

## Migration Strategy

1. Keep the current Ansible netlink playbook working.
2. Add native netlink backup task support to agent.
3. Convert Maipu task template to `app_type=network_config_backup`.
4. Run one Maipu acceptance task.
5. Move Huawei/H3C backup templates to the native runner.
6. Revisit FiberHome later.

## Non-goals

- Do not remove Ansible support.
- Do not implement FiberHome in this pass.
- Do not change prompt handling beyond the already validated Maipu netlink config.
- Do not require repeated real-device login in automated tests.

