# SecretHub AI Handoff

This handoff is written for the next AI or engineer who will implement the OneOPS SecretHub MVP.

## Current Goal

Build a standalone secret management platform that simplifies Vault and future third-party secret store operations for OneOps.

The MVP should:

- Manage Vault providers.
- Create, import, update, and list credentials.
- Hide Vault catalog index complexity from operators.
- Provide OneOps-compatible credential list and resolve APIs.
- Preserve audit trails.

Read first:

- [SecretHub MVP Design](SECRET_HUB_MVP_DESIGN.md)
- [SecretHub OneOps Integration](SECRET_HUB_ONEOPS_INTEGRATION.md)

## Existing OneOps Context

Relevant existing code:

- OneOps credential API: `/home/ubuntu/project/OneOPS/app/credential/api/credential.go`
- OneOps credential router: `/home/ubuntu/project/OneOPS/app/credential/router/credential.go`
- OneOps Vault provider: `/home/ubuntu/project/OneOPS/app/credential/service/impl/vault_provider.go`
- OneOps credential DTOs: `/home/ubuntu/project/OneOPS/app/credential/dto/request_response.go`
- OneOps unified credential page: `/home/ubuntu/project/OneOPS-UI/src/views/setting/CredentialUnified.vue`
- Quick env Vault init: `/home/ubuntu/project/quick_env/init-configs/vault/init-vault.sh`
- Quick env OneOps config: `/home/ubuntu/project/quick_env/init-configs/nacos/cipher-aes-start-config.yaml`

Important existing behavior:

- OneOps can list and manage Vault catalog entries.
- OneOps can sync a Vault catalog index through `POST /credential/vault/catalog:sync`.
- OneOps expects catalog metadata such as `code`, `name`, `type`, `usage`, `path`, and `field_mapping`.
- Actual secret material lives in Vault.
- The final Vault secret path is usually `catalog.path + "/" + catalog.code`.

## Recommended First Implementation Strategy

Do not begin with every provider. Start with Vault only and define provider interfaces clearly.

Recommended sequence:

1. Create `OneOPS-ALL/secrethub/backend`.
2. Add basic config loading.
3. Add DB migrations for provider, catalog, audit.
4. Implement Vault provider adapter.
5. Implement provider CRUD and test API.
6. Implement credential CRUD.
7. Implement partial secret update.
8. Implement Vault catalog index export for OneOps Phase 1 compatibility.
9. Implement OneOps-compatible list API.
10. Implement OneOps-compatible resolve API.
11. Implement frontend pages.
12. If testing against quick_env, only use the Vault that quick_env starts as an
    external Vault provider; do not add SecretHub services or seed flows to
    quick_env.

## MVP Backend Tasks

### Task 1: Scaffold Backend

Suggested language:

- Go, if staying consistent with OneOps backend.

Suggested structure:

```text
OneOPS-ALL/secrethub/backend/
  cmd/secrethub/main.go
  internal/config/
  internal/http/
  internal/provider/
  internal/provider/vault/
  internal/catalog/
  internal/secret/
  internal/sync/
  internal/audit/
  internal/oneops/
  migrations/
```

Minimum server routes:

```http
GET /healthz
GET /api/v1/secrethub/providers
POST /api/v1/secrethub/providers
POST /api/v1/secrethub/providers/{id}:test
GET /api/v1/secrethub/credentials
POST /api/v1/secrethub/credentials
PUT /api/v1/secrethub/credentials/{code}
POST /api/v1/secrethub/credentials/{code}:update-secret
POST /api/v1/secrethub/credentials:resolve
GET /api/v1/secrethub/audit
```

### Task 2: Provider Model

Provider statuses:

- `active`
- `disabled`
- `unhealthy`
- `unknown`

Provider fields:

- `id`
- `name`
- `type`
- `endpoint`
- `namespace`
- `default_mount`
- `auth_ref`
- `status`
- `last_checked_at`
- `last_error`

For MVP, it is acceptable to store provider token in local development config. Production must use encrypted storage or environment injection.

### Task 3: Vault Adapter

Implement:

```go
ReadSecret(ctx, path)
WriteSecret(ctx, path, data)
DeleteSecret(ctx, path)
ListSecrets(ctx, prefix)
TestConnection(ctx)
```

Vault KV v2 read response:

```json
{
  "data": {
    "data": {
      "username": "ops",
      "password": "secret"
    },
    "metadata": {}
  }
}
```

Return only the inner `data.data`.

Path handling:

- UI can accept friendly path like `kv/oneops/credentials/foo`.
- Adapter should normalize to API path `kv/data/oneops/credentials/foo`.
- Do not double-insert `/data/`.

### Task 4: Catalog Model

Catalog statuses:

- `active`
- `disabled`
- `needs_review`
- `orphaned`

Catalog fields:

- `code`
- `name`
- `type`
- `usage`
- `provider_id`
- `secret_path`
- `field_mapping`
- `description`
- `status`
- `tags`

Default field mappings:

```json
{
  "ssh_account": {
    "username": "username",
    "password": "password",
    "private_key": "private_key",
    "passphrase": "passphrase",
    "auth_username": "auth_username",
    "auth_pass": "auth_pass",
    "ssh_port": "ssh_port",
    "telnet_port": "telnet_port"
  },
  "snmp_community": {
    "community": "community"
  },
  "http_basic": {
    "username": "username",
    "password": "password",
    "token": "token"
  },
  "token": {
    "token": "token"
  }
}
```

### Task 5: Create Credential

Input example:

```json
{
  "provider_id": "vault-prod",
  "name": "Linux Ops",
  "type": "ssh_account",
  "usage": "inband",
  "secret_data": {
    "username": "ops",
    "password": "secret"
  }
}
```

Backend behavior:

- Generate `code` if absent.
- Generate `secret_path` if absent.
- Apply default field mapping if absent.
- Write `secret_data` to provider.
- Save catalog.
- Write audit event.

### Task 6: Partial Secret Update

Input:

```json
{
  "secret_data": {
    "password": "new-secret"
  }
}
```

Backend behavior:

- Read existing provider secret.
- Merge input keys into existing data.
- Write merged payload back.
- Save audit event.

Do not clear fields omitted from the request.

### Task 7: Resolve Credential

Input:

```json
{
  "credential_ref": "vault_linux_ops",
  "usage": "inband",
  "subject_type": "device",
  "subject_id": "device-001"
}
```

Behavior:

- Find active catalog by code.
- Check usage compatibility.
- Read provider secret.
- Apply field mapping.
- Return mapped fields to trusted OneOps backend.
- Write audit event without plaintext.

Output:

```json
{
  "credential_code": "vault_linux_ops",
  "provider": "vault-prod",
  "credentials": {
    "username": "ops",
    "password": "secret"
  }
}
```

Later phase:

- Return short-lived material handles instead of plaintext.

### Task 8: Import Existing Vault Secrets

Dry-run input:

```json
{
  "provider_id": "vault-prod",
  "path_prefix": "kv/oneops/credentials",
  "default_type": "ssh_account",
  "default_usage": "inband"
}
```

Dry-run output:

```json
{
  "items": [
    {
      "provider_path": "kv/data/oneops/credentials/linux_ops",
      "suggested_code": "vault_linux_ops",
      "suggested_name": "linux_ops",
      "inferred_type": "ssh_account",
      "usage": "inband",
      "status": "ready"
    }
  ]
}
```

Apply should create catalog rows only. It should not rewrite existing secrets unless explicitly requested.

## MVP Frontend Tasks

Suggested structure:

```text
OneOPS-ALL/secrethub/frontend/src/
  api/
    providers.ts
    credentials.ts
    audit.ts
  views/
    SecretSources.vue
    SecretCatalog.vue
    SyncJobs.vue
    AuditLog.vue
  components/
    ProviderForm.vue
    CredentialForm.vue
    SecretFieldEditor.vue
```

### Page: Secret Sources

Build:

- Provider table.
- Add/edit provider modal.
- Test connection button.
- Status badge.
- Last error display.

No hero, no marketing copy. Use compact enterprise console layout.

### Page: Credentials

Build:

- Metrics row.
- Filter bar.
- Credential table.
- Create credential modal.
- Edit metadata modal.
- Update secret modal.
- View referrers drawer.

Important:

- Tables must never show plaintext secret values.
- Secret inputs should use password controls for sensitive keys.
- Advanced field mapping editor can be collapsed by default.

### Page: Sync Jobs

Build:

- Provider selector.
- Path prefix input.
- Dry-run button.
- Result table.
- Apply button.
- Row status labels.

### Page: Audit

Build:

- Filter bar.
- Audit table.
- Metadata drawer.

## OneOps Integration Tasks

### Option A: Minimal Compatibility

SecretHub exports Vault catalog index.

OneOps continues to call:

```http
POST /api/v1/credential/vault/catalog:sync
```

This is the lowest-risk first integration.

### Option B: Direct Pull

Add a OneOps list provider that calls:

```http
GET /api/v1/secrethub/credentials
```

Use SecretHub response to populate OneOps credential lists and device onboarding selectors.

### Option C: Resolve Delegation

OneOps calls SecretHub resolve:

```http
POST /api/v1/secrethub/credentials:resolve
```

This removes Vault token usage from OneOps.

Recommended path:

1. Implement Option A first.
2. Add Option B after SecretHub is stable.
3. Add Option C after audit and auth are reliable.

## UI Design Rules

Follow these rules:

- Enterprise application style.
- Compact, quiet, operational.
- Tables and forms are primary.
- Avoid landing-page style sections.
- Avoid large decorative cards.
- Avoid gradients and illustrations.
- Use clear status labels.
- Keep copy short.
- Avoid showing instructional text in the main workflow unless it prevents operator error.

Suggested page shell:

```text
Top toolbar:
  Title | provider health summary | primary action

Filter row:
  keyword | provider | type | usage | status

Main table:
  dense but readable columns

Drawer/modal:
  edit forms and details
```

## Security Checklist

Before calling MVP complete:

- No plaintext secrets in DB.
- No plaintext secrets in logs.
- No plaintext secrets in list APIs.
- Secret update audit records do not include values.
- Provider token is masked in GET responses.
- Resolve API writes audit logs.
- Delete operations require confirmation in UI.
- Import apply shows dry-run result first.

## Suggested Acceptance Tests

Backend:

- Create Vault provider and test connection.
- Create SSH credential and verify Vault write path.
- List credentials and verify no plaintext.
- Partial update password and verify username remains.
- Resolve credential and verify field mapping.
- Dry-run import from Vault prefix.
- Apply import and verify catalog rows.
- Audit logs exist for create/update/resolve.

Frontend:

- Provider page can add and test provider.
- Credential page can create SSH credential.
- Credential page can update only password.
- Sync page can dry-run and apply.
- Audit page displays events.
- No table displays secret values.

OneOps integration:

- Export or sync catalog to OneOps.
- OneOps credential list includes SecretHub-managed credential.
- Device onboarding can select credential.
- OneOps resolve path can obtain credential material through configured integration mode.

## Known Risks

- Vault KV v2 path confusion can cause failed reads. Normalize paths centrally.
- If SecretHub and OneOps both edit the same catalog, ownership conflicts can happen. Prefer SecretHub as catalog owner.
- Direct plaintext resolve increases risk. Move to short-lived material handles after MVP.
- Provider token storage must be hardened before production.
- Import inference will be imperfect. Keep a `needs_review` state.

## Development Guardrails

- Keep MVP small.
- Do not implement rotation, approval, or many providers in the first pass.
- Do not expose raw Vault catalog JSON as the primary workflow.
- Keep provider adapter interfaces stable.
- Add tests around path normalization and partial secret updates.
- Treat OneOps integration as a consumer contract, not a UI dependency.
