# SecretHub Current-Session Implementation Summary

## Implemented

### SecretHub Backend

- Created standalone backend module: `secrethub/backend`.
- Added executable service entry: `cmd/secrethub/main.go`.
- Added domain contracts for providers, credential catalog summaries, audit logs, and provider health.
- Added Vault KV v2 path normalization and OneOps catalog path split helpers.
- Added file-backed JSON store for first-slice persistence plus memory store for tests.
- Added Vault provider adapter with health test, read, write, delete, and list methods.
- Added service layer for provider create/test, credential create/list/update/update-secret/resolve/validate/export, and audit logging.
- Added HTTP handler for the first documented API slice.
- Added optional API-token authentication for all non-health routes.
- Added short-lived, signed, single-use SecretHub material handles.
- Added stable `secret_fingerprint` on plaintext and handle-only resolve responses so consumers do not hash nonce-bearing handles.
- Added README with local run instructions and current limits.

### OneOps Integration

- Added OneOps config shape for `credential.providers.secrethub`.
- Added `SecretHubCredentialProvider` for metadata-only list pull.
- Integrated SecretHub summaries into `ResolverAdapter.ListCredentials`.
- Updated duplicate summary priority to `secrethub > vault > oneops`.
- SecretHub list failures are warning-only and do not block legacy or Vault summaries.
- Added opt-in OneOps SecretHub resolve delegation via `resolve_enabled`.
- Added `response_mode=material_handle` as the default SecretHub resolve mode when delegation is enabled.
- Added SecretHub material handle consumption through OneOps `ResolveReference` for `secrethub:v1:*` handles.
- OneOps now prefers SecretHub's stable `secret_fingerprint` and only falls back to hashing the handle for older responses.
- Allowed Task Execution Profile resolution to accept handle-only SecretHub responses without plaintext credentials.
- Added backend-supported `provider` filtering to `/credential/list` so callers can request `secrethub`, `vault`, or `oneops` summaries directly.
- Added backend-supported `status` filtering to `/credential/list`, preserving the default `active` behavior.

### OneOps UI

- Added source filtering to the unified credential workspace credential list.
- Added status filtering to the unified credential workspace credential list.
- Rendered credential providers as visual tags so `SecretHub`, `Vault`, and `OneOps` are distinguishable at a glance.
- Wired the UI source filter through to `/credential/list` instead of only doing local filtering.
- Rendered credential status as visual tags for `active`, `disabled`, `needs_review`, and `orphaned`.

### Smoke Tooling

- Added `secrethub/backend/scripts/quickenv-smoke.sh` for local/quick_env validation against Vault.
- The smoke script starts a temporary SecretHub, uses a Vault-backed sample credential, verifies handle issuance, stable `secret_fingerprint` propagation, one-time material consumption, and replay rejection without printing token or secret values.

## Implemented API Surface

```http
GET  /healthz
GET  /api/v1/secrethub/providers
POST /api/v1/secrethub/providers
POST /api/v1/secrethub/providers/{id}:test
GET  /api/v1/secrethub/credentials
POST /api/v1/secrethub/credentials
PUT  /api/v1/secrethub/credentials/{code}
POST /api/v1/secrethub/credentials/{code}:update-secret
POST /api/v1/secrethub/credentials:resolve
POST /api/v1/secrethub/credentials:validate
POST /api/v1/secrethub/credentials:export-vault-index
POST /api/v1/secrethub/material:resolve
GET  /api/v1/secrethub/audit
```

## Validation Evidence

SecretHub backend command:

```bash
cd /Users/huangliang/project/OneOPS-ALL/secrethub/backend
go test ./...
bash -n scripts/quickenv-smoke.sh
```

Result:

```text
ok   github.com/netxops/secrethub/internal/domain
ok   github.com/netxops/secrethub/internal/httpapi
scripts/quickenv-smoke.sh syntax ok
```

OneOps integration command:

```bash
cd /Users/huangliang/project/OneOPS-ALL/OneOPS
go test ./app/credential/service/impl
go test ./app/platform/service/impl
```

Result:

```text
ok   github.com/netxops/OneOps/app/credential/service/impl
ok   github.com/netxops/OneOps/app/platform/service/impl
```

OneOps UI command:

```bash
cd /Users/huangliang/project/OneOPS-ALL/OneOPS-UI
npm exec prettier -- src/views/setting/CredentialUnified.vue --write
npm exec prettier -- src/typings/credential.ts --write
npm exec eslint -- src/views/setting/CredentialUnified.vue src/typings/credential.ts
```

Result:

```text
eslint passed for changed UI files
```

Quick env smoke command:

```bash
cd /Users/huangliang/project/OneOPS-ALL/secrethub/backend
SECRETHUB_SMOKE_VAULT_TOKEN="$VAULT_TOKEN" \
VAULT_ADDR="http://127.0.0.1:24400" \
bash scripts/quickenv-smoke.sh
```

Result:

```json
{"ok": true, "vault_addr": "http://127.0.0.1:24400", "credential_code": "vault_linux_ops", "handle_prefix": "secrethub:v1:", "secret_fingerprint_present": true, "single_use_replay_rejected": true}
```

Known unrelated UI typecheck blockers:

```text
src/components/MonacoEditor.vue: monaco-editor type/module resolution
src/views/device/DeviceV2ManagementGrouped.vue: existing SelectValue / SSHRecordResp / SpaceSize / monitor_push_error type issues
```

The HTTP lifecycle test covers:

- Provider creation with `auth_ref` environment token.
- Provider health test against fake Vault.
- SSH credential creation with KV v2 write.
- Metadata list without plaintext.
- Resolve with field mapping.
- Partial password update preserving username.
- OneOps-compatible Vault catalog index export.
- Audit output without plaintext secret value.
- Material handle issuance without plaintext response.
- Stable secret fingerprint across separate handle issuances for the same material.
- Material handle consumption with single-use replay denial.
- Optional API-token auth with health-check exemption.
- OneOps list merge prefers SecretHub on same type/code conflicts.
- OneOps list keeps Vault summaries when SecretHub is unavailable.
- OneOps SecretHub resolve returns a handle-only response without exposing plaintext.
- OneOps SecretHub material handle consumption resolves plaintext only at connector fetch time.
- Task execution profile dispatch accepts handle-only material and keeps `connector_fetch` delivery.
- OneOps UI can filter the unified credential list by provider source and highlights SecretHub rows.
- `/credential/list` provider filtering avoids unnecessary SecretHub list calls when the caller requests only Vault or OneOps sources.
- `/credential/list` status filtering can request active-only, all statuses, or specific SecretHub non-active states.
- SecretHub quick_env smoke can validate handle issuance, stable fingerprint propagation, consumption, and replay rejection against a real Vault runtime when a Vault token is supplied.

## Next Recommended Slice

1. Add production storage abstraction backed by SQLite or MySQL migrations.
2. Add RBAC and tenant isolation on top of service-token auth.
3. Wire quick_env service container and sample Vault provider.
4. Add an optional quick_env Compose profile for SecretHub once image/build strategy is agreed.
5. Add end-to-end OneOps task dispatch smoke that uses SecretHub resolve delegation.
