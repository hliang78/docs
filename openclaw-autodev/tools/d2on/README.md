# D2ON Helper Tools

This directory contains Device V2 onboarding helper tools used by the `d2on`
OpenClaw task.

These tools are for development testing and exploration only. They are not a
business feature path. Business code must not call these tools for remote
server operations; business remote-server operations must go through
controller-provided APIs.

When this task runs under OpenClaw loop automation, runtime-only database/API
tokens and remote test credentials may be injected through loop config
`RUNTIME_ENV_FILE` / `RUNTIME_ENV_FILES`. These files must live outside the
repository or under operator-controlled secret storage and must never be
committed.

For variable names only, start from
`docs/openclaw-autodev/tools/d2on/runtime.env.example` and copy it to an
external secret location before use.

If you want to run the `d2on` worker on a cloud model instead of local Ollama,
export `OPENCLAW_AGENT_MODEL` and optionally `PROVIDER_PROBE_MODEL` in the
invoking shell before starting the loop. Example:

```bash
export OPENCLAW_AGENT_MODEL="aigocode/gpt-5.4-mini"
export PROVIDER_PROBE_MODEL="aigocode/gpt-5.4-mini"
```

The custom provider itself should be configured in local OpenClaw config, not
inside this repository. `AIGOCODE_API_KEY` may be exported in the invoking
shell or injected through `RUNTIME_ENV_FILE` / `RUNTIME_ENV_FILES`. Runtime env
files are still the right place for provider credentials, DB/API tokens, and
remote test credentials, but they are sourced too late to change the loop's
selected worker model.

For the default `d2on` agent profile (`aigocode-direct`), the loop will also
auto-discover a runtime env file at:

```text
/Users/huangliang/.openclaw-aigocode-direct/runtime.env
```

unless `D2ON_RUNTIME_ENV_FILE` or `D2ON_RUNTIME_ENV_FILES` overrides it.
Use the bundled template only as a variable-name reference:

```bash
cp /Users/huangliang/project/OneOPS-ALL/docs/openclaw-autodev/tools/d2on/runtime.env.example \
  /Users/huangliang/.openclaw-aigocode-direct/runtime.env
chmod 600 /Users/huangliang/.openclaw-aigocode-direct/runtime.env
```

Check readiness without printing secrets:

```bash
/Users/huangliang/project/OneOPS-ALL/scripts/openclaw-d2on-runtime-env-doctor.sh
```

## Entrypoint

```bash
cd /Users/huangliang/project/OneOPS-ALL

# Show usage.
docs/openclaw-autodev/tools/d2on/d2on-discovery.py --help

# Preferred path: controller-backed read-only Linux discovery.
D2ON_CONTROLLER_URL=http://127.0.0.1:18080 \
D2ON_X_AUTH_TOKEN='<runtime token if controller requires it>' \
D2ON_SERVER_SSH_USER=root \
D2ON_SERVER_SSH_PASSWORD='<runtime secret>' \
  docs/openclaw-autodev/tools/d2on/d2on-discovery.py inspect-server-via-controller \
  --host 192.168.100.7

# Preferred path: controller-backed read-only network-device discovery.
D2ON_CONTROLLER_URL=http://127.0.0.1:18080 \
D2ON_X_AUTH_TOKEN='<runtime token if controller requires it>' \
D2ON_NETWORK_SSH_USER=admin \
D2ON_NETWORK_SSH_PASSWORD='<runtime secret>' \
  docs/openclaw-autodev/tools/d2on/d2on-discovery.py inspect-network-via-controller \
  --host 172.32.2.14 --vendor h3c --platform comware

# Query real Device V2 candidates from MySQL. Credentials are runtime-only.
D2ON_MYSQL_HOST=127.0.0.1 \
D2ON_MYSQL_PORT=3306 \
D2ON_MYSQL_DATABASE=oneops \
D2ON_MYSQL_USER=readonly_user \
D2ON_MYSQL_PASSWORD='<runtime secret>' \
  docs/openclaw-autodev/tools/d2on/d2on-discovery.py db-candidates \
  --target 192.168.100.7 --target 172.32.2.14

# Read-only Linux system-log discovery over SSH.
docs/openclaw-autodev/tools/d2on/d2on-discovery.py inspect-server \
  --host 192.168.100.7 --user '<runtime ssh user>'

# Read-only network-device command-family discovery over direct SSH fallback.
docs/openclaw-autodev/tools/d2on/d2on-discovery.py inspect-network \
  --host 172.32.2.14 --user '<runtime ssh user>'
```

The tool writes detailed JSON evidence under
`docs/openclaw-autodev/evidence/d2on/discovery/` and appends compact durable
run summaries to `docs/openclaw-autodev/evidence/d2on/D2ON-000.md`.

## What the tool does

Allowed tool purposes:

- Query real server and network-device candidates from `platform_devices_v2` in
  the local/test database, or fail with an explicit connection/query error.
  Candidate evidence records only stable identifiers; raw inventory JSON blobs
  are not persisted because they may contain credentials, tokens, or SNMP
  communities.
- Use authorized read-only test database/API access when needed.
- Prefer controller `/api/v1/remote/run` for read-only server and network
  verification so OpenClaw workers validate against the same remote-access
  contract that business code will use.
- Keep direct SSH helper paths only as development fallback when controller API
  is unavailable or a lower-level login problem must be isolated.
- Record command, target, exit status, stdout/stderr summary, and timestamp for
  every remote command. Output summaries are redacted for common password,
  token, secret, SNMP community, security-name, and SSH diagnostic username
  patterns before evidence is written.
- Record Linux system-log file existence for:
  - `/var/log/syslog`
  - `/var/log/auth.log`
  - `/var/log/messages`
  - `/var/log/secure`
- Discover server log-forwarding command clues without changing files.
- Discover network-device syslog and SNMP trap command families without
  applying configuration. If more than one command family appears valid, the
  tool treats the result as ambiguous and exits non-zero instead of guessing a
  template.

Authorized test targets are listed in
`docs/openclaw-autodev/tools/d2on/test-targets.md`.

## Runtime secret handling

- Test database credentials and API tokens must be provided at runtime and must
  not be persisted in code, generated docs, config, or evidence. The MySQL
  password is passed to the local `mysql` client through the process environment
  instead of command-line arguments.
- Browser/UI login for D2 smoke scripts should come from `D2_UI_LOGIN_USERNAME`
  / `D2_UI_LOGIN_PASSWORD` in the runtime env file. Current scripts still allow
  `admin/admin@123` as a fallback, but runtime injection is preferred so the
  login source is explicit and rotatable.
- Controller URL, controller token, and remote login credentials must come from
  runtime-only env files such as `D2ON_RUNTIME_ENV_FILE` /
  `D2ON_RUNTIME_ENV_FILES`. Do not write them into this directory.
- Direct SSH fallback credentials must come from the operator's SSH agent/config
  or runtime prompt/wrapper. Do not write them into this directory.
- Evidence redacts the MySQL password and records only whether a runtime user
  was provided for SSH or controller-backed remote access.
- Remote stdout/stderr summaries are best-effort redacted for common secret and
  SSH diagnostic username patterns before persistence. Discovery operators should still avoid commands
  that intentionally dump credential-heavy full configuration unless the story
  explicitly requires them.

## Failure behavior

Discovery tools must fail loudly on database, credential, login, command, or
template errors. Non-zero exits are intentional evidence for unknown
credentials, unsupported devices, failed login, or ambiguous command templates.

## Boundaries

- Discovery tools must not apply configuration changes.
- Business code must not import, shell out to, or depend on these tools.
- Business remote-server operations must go through controller-provided APIs.
- Configuration-changing remote commands belong only to explicit ensure/apply
  stories such as `D2ON-004`.
- Tools must not infer missing vendors, credentials, commands, listener
  addresses, or log paths.
