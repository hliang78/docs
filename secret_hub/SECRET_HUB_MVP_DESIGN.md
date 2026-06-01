# OneOPS SecretHub MVP Design

## Background

OneOps already has a unified credential concept and Vault catalog integration. The current model works, but it still asks OneOps to understand Vault-specific details such as KV v2 paths, catalog indexes, field mappings, provider tokens, and sync behavior.

SecretHub is a small standalone secret management platform that centralizes those responsibilities. OneOps consumes a stable credential API and keeps focusing on device onboarding, collection, task execution, and change workflows.

## Product Positioning

SecretHub is not a replacement for Vault. It is an operational layer above Vault and other third-party secret stores.

Responsibilities:

- Manage connections to Vault and future secret providers.
- Maintain a normalized credential catalog.
- Simplify secret creation, update, import, sync, and audit.
- Provide OneOps with stable credential list and resolve APIs.

Non-responsibilities for MVP:

- Full enterprise IAM.
- Complex approval workflow.
- Secret rotation engine.
- Full multi-provider parity.
- Replacing OneOps business workflows.

## MVP Goals

The MVP should make this workflow simple:

1. Add a Vault provider.
2. Test provider connectivity and permissions.
3. Create or import a credential without manually editing Vault catalog JSON.
4. See the credential in OneOps onboarding and binding flows.
5. Update a credential secret from SecretHub.
6. Keep an audit trail of create, update, sync, and resolve events.

## Core Concepts

### Provider

A provider is a third-party secret store connection.

MVP provider:

- Vault KV v2

Future providers:

- AWS Secrets Manager
- Alibaba Cloud KMS / Secrets Manager
- Kubernetes Secret
- Azure Key Vault
- Generic HTTP secret broker

### Credential Catalog

The catalog describes what a secret means to OneOps.

Required catalog metadata:

- `code`
- `name`
- `type`
- `usage`
- `provider_id`
- `secret_path`
- `field_mapping`

The secret material remains in the provider.

### Credential Reference

OneOps stores and passes `credential_ref`, usually the catalog `code`.

OneOps should not need to know the provider path, provider token, or field mapping details.

### Tenant Boundary

The current implementation treats tenant as a first-class runtime scope.

- Providers, credential catalog rows, audit logs and material-handle consumption records carry `tenant_id`.
- Provider IDs and credential codes are unique within a tenant, not globally.
- Native console sessions are scoped by `SECRETHUB_TENANT_ID`.
- Trusted backend-to-backend API tokens can target tenants with `tenant=token` entries in `SECRETHUB_API_TOKENS`.
- RBAC remains outside the current slice; tenant isolation is enforced at the API/store boundary first.

## Architecture

```text
Vault / future providers
        |
        | provider adapters
        v
OneOPS SecretHub
        |
        | standard credential APIs
        v
OneOps
  - device onboarding
  - credential binding
  - collection
  - task execution
  - change execution
```

SecretHub owns catalog operations. Providers own secret material.

OneOps consumes:

- Credential list
- Credential metadata
- Credential resolve
- Credential reference validation

## Recommended Repository Layout

```text
OneOPS-ALL/
  secrethub/
    backend/
      cmd/
      internal/
        provider/
        catalog/
        secret/
        sync/
        audit/
        oneops/
      migrations/
    frontend/
      src/
        api/
        views/
        components/
    docs/
  docs/
    SECRET_HUB_MVP_DESIGN.md
    SECRET_HUB_AI_HANDOFF.md
```

The MVP should remain a standalone service and frontend. quick_env belongs to
the OneOPS quick-deploy workflow; its only direct relationship to SecretHub is
that it can start a Vault instance which SecretHub may use as an external Vault
provider.

## Backend Modules

### Provider Module

Purpose:

- Store provider connection metadata.
- Validate provider connectivity.
- Check read/write/list/delete capabilities.

Provider interface:

```go
type SecretProvider interface {
    TestConnection(ctx context.Context) (*ProviderHealth, error)
    ReadSecret(ctx context.Context, path string) (map[string]string, error)
    WriteSecret(ctx context.Context, path string, data map[string]string) error
    DeleteSecret(ctx context.Context, path string) error
    ListSecrets(ctx context.Context, prefix string) ([]ProviderSecretRef, error)
}
```

Vault MVP behavior:

- Store KV v2 API paths internally.
- Accept operator-friendly paths in the UI.
- Normalize `kv/foo/bar` to `kv/data/foo/bar` for API calls when needed.

### Catalog Module

Purpose:

- Store normalized catalog metadata.
- Generate credential codes.
- Apply default field mappings.
- Expose list/query APIs for OneOps and SecretHub UI.

Credential types for MVP:

- `ssh_account`
- `snmp_community`
- `http_basic`
- `username_password`
- `token`

Common usages:

- `inband`
- `outband`
- `snmp_inband`
- `snmp_outband`
- `change_execution`
- `telegraf:snmp`
- `telegraf:mysql`
- `telegraf:redis`
- `api`

### Secret Module

Purpose:

- Create secret material in provider.
- Update selected secret fields.
- Preserve fields not included in partial updates.
- Never store plaintext secret values in SecretHub DB.

Update rule:

- Empty secret payload means metadata-only update.
- Non-empty secret payload means read existing provider secret, merge fields, write back.

### Sync Module

Purpose:

- Import existing Vault secrets into SecretHub catalog.
- Support dry-run and apply.
- Detect conflicts before writing.

MVP sync modes:

- Import by explicit path prefix.
- Import by existing Vault catalog index.
- Export/update Vault catalog index for compatibility with current OneOps behavior.

### Audit Module

Purpose:

- Record who changed what and when.
- Record provider connection tests.
- Record sync results.
- Record OneOps resolve calls without storing plaintext.

Audit event examples:

- `provider.created`
- `provider.tested`
- `credential.created`
- `credential.secret_updated`
- `credential.metadata_updated`
- `credential.deleted`
- `sync.dry_run`
- `sync.applied`
- `credential.resolved`

### OneOps Adapter Module

Purpose:

- Provide compatibility APIs for OneOps.
- Optionally push catalog updates into OneOps during transition.

The adapter should support two integration modes:

- Pull mode: OneOps queries SecretHub list/resolve APIs.
- Sync mode: SecretHub pushes or exports catalog data to OneOps existing `credential_vault_catalog`.

MVP recommendation:

- Start with pull APIs plus optional export of Vault catalog index.

## Data Model

### `secret_provider`

```sql
id                  varchar(64) primary key
name                varchar(128) not null
type                varchar(64) not null
endpoint            varchar(512) not null
namespace           varchar(128)
auth_ref            varchar(256)
default_mount       varchar(128)
status              varchar(32)
last_checked_at     datetime
last_error          text
created_at          datetime
updated_at          datetime
deleted_at          datetime
```

Notes:

- `auth_ref` points to an encrypted config item or bootstrap secret.
- Do not store provider token as plaintext.

### `secret_catalog`

```sql
id                  varchar(64) primary key
code                varchar(128) unique not null
name                varchar(255) not null
type                varchar(64) not null
usage               varchar(128)
provider_id         varchar(64) not null
secret_path         varchar(512) not null
field_mapping_json  text
description         text
status              varchar(32)
tags_json           text
created_at          datetime
updated_at          datetime
deleted_at          datetime
```

### `secret_audit_log`

```sql
id                  varchar(64) primary key
event_type          varchar(64) not null
actor               varchar(128)
provider_id         varchar(64)
credential_code     varchar(128)
subject_type        varchar(64)
subject_id          varchar(128)
request_id          varchar(128)
result              varchar(32)
message             text
metadata_json       text
created_at          datetime
```

## API Design

### Provider APIs

```http
GET    /api/v1/secrethub/providers
POST   /api/v1/secrethub/providers
PUT    /api/v1/secrethub/providers/{id}
DELETE /api/v1/secrethub/providers/{id}
POST   /api/v1/secrethub/providers/{id}:test
POST   /api/v1/secrethub/providers/{id}:sync-preview
POST   /api/v1/secrethub/providers/{id}:sync-apply
```

### Credential APIs

```http
GET    /api/v1/secrethub/credentials
POST   /api/v1/secrethub/credentials
GET    /api/v1/secrethub/credentials/{code}
PUT    /api/v1/secrethub/credentials/{code}
DELETE /api/v1/secrethub/credentials/{code}
POST   /api/v1/secrethub/credentials/{code}:update-secret
POST   /api/v1/secrethub/credentials:resolve
POST   /api/v1/secrethub/credentials:validate
GET    /api/v1/secrethub/credentials/{code}/referrers
```

### OneOps Compatibility APIs

```http
POST /api/v1/oneops/credential/list
POST /api/v1/oneops/credential/resolve
POST /api/v1/oneops/credential/catalog:export-vault-index
```

The compatibility API can return the same shape as OneOps currently expects:

```json
{
  "items": [
    {
      "code": "vault_linux_ops2",
      "name": "Linux Ops 2",
      "type": "ssh_account",
      "masked": true,
      "provider": "secrethub",
      "usage": "inband"
    }
  ],
  "total": 1
}
```

## Vault MVP Details

### Creating A Credential

Operator input:

```text
Provider: Vault Prod
Name: Linux Ops 2
Type: SSH Account
Usage: inband
Username: ops
Password: ******
```

SecretHub generates:

```text
code: vault_ssh_inband_linux_ops_2
secret_path: kv/data/oneops/credentials/vault_ssh_inband_linux_ops_2
field_mapping:
  username: username
  password: password
```

SecretHub writes:

```json
{
  "username": "ops",
  "password": "******"
}
```

### Importing Existing Vault Secrets

MVP import flow:

1. Select provider.
2. Enter path prefix.
3. Click dry-run.
4. SecretHub lists candidate paths.
5. SecretHub infers type by keys.
6. Operator fixes name/type/usage for uncertain rows.
7. Apply creates catalog entries.

Inference examples:

- Has `community`: `snmp_community`
- Has `username` and `password`: `ssh_account` or `username_password`
- Has `token`: `token`

When inference is ambiguous, mark the row as `needs_review`.

### Vault Catalog Index Compatibility

SecretHub may write a simplified index for current OneOps compatibility:

```json
{
  "defaults": {
    "path": "kv/data/oneops/credentials",
    "type": "ssh_account",
    "usage": "inband"
  },
  "items": [
    {
      "code": "vault_linux_ops2",
      "name": "Linux Ops 2"
    }
  ]
}
```

SecretHub should also support the existing expanded format:

```json
{
  "items": [
    {
      "code": "vault_linux_ops2",
      "name": "Linux Ops 2",
      "type": "ssh_account",
      "usage": "inband",
      "path": "kv/data/oneops/credentials",
      "field_mapping": {
        "username": "username",
        "password": "password"
      }
    }
  ]
}
```

## OneOps Integration Plan

Detailed OneOps-side implementation notes are maintained in [SecretHub OneOps Integration](SECRET_HUB_ONEOPS_INTEGRATION.md).

### Phase 1: Keep Current OneOps Working

SecretHub writes or exports Vault catalog index.

OneOps continues to use:

```http
POST /credential/vault/catalog:sync
```

This minimizes OneOps changes.

### Phase 2: OneOps Pulls From SecretHub

OneOps credential list provider can call:

```http
GET /api/v1/secrethub/credentials
```

Device onboarding can keep using the same `credential_ref`.

### Phase 3: OneOps Resolve Delegates To SecretHub

OneOps task execution calls SecretHub resolve API instead of reading Vault directly.

```http
POST /api/v1/secrethub/credentials:resolve
```

Request:

```json
{
  "credential_ref": "vault_linux_ops2",
  "usage": "inband",
  "subject_type": "device",
  "subject_id": "device-001"
}
```

Response:

```json
{
  "credential_code": "vault_linux_ops2",
  "provider": "vault-prod",
  "material_handle": "secrethub:v1:...",
  "credentials": {
    "username": "ops",
    "password": "******"
  }
}
```

MVP can return material directly to trusted OneOps backend. Longer term should prefer short-lived material handles.

## Frontend UX

The UI should feel like a professional enterprise operations console.

Do:

- Dense but readable tables.
- Clear filter bars.
- Small metrics at top.
- Explicit statuses.
- Plain forms.
- No marketing hero.
- No decorative gradients or large illustration panels.

Do not:

- Expose plaintext in lists.
- Ask operators to edit raw catalog JSON for common workflows.
- Hide provider health and permission errors.

### Navigation

Primary pages:

- `Secret Sources`
- `Credentials`
- `Sync Jobs`
- `Audit`

### Secret Sources Page

Purpose:

- Manage Vault and future secret providers.

Top actions:

- Add provider
- Test all

Table columns:

- Name
- Type
- Endpoint
- Namespace
- Default mount
- Status
- Last checked
- Last error
- Actions

Actions:

- Test
- Edit
- Sync preview
- Disable

### Credentials Page

Purpose:

- Main workbench for secret catalog.

Top metrics:

- Total credentials
- Active providers
- Unhealthy providers
- Recently updated

Filter bar:

- Keyword
- Provider
- Type
- Usage
- Status

Table columns:

- Code
- Name
- Type
- Usage
- Provider
- Secret path
- Status
- Updated at
- Referrers
- Actions

Actions:

- Create credential
- Edit metadata
- Update secret
- View referrers
- Disable/delete

### Credential Form

Fields:

- Provider
- Name
- Code, auto-generated by default
- Type
- Usage
- Secret path, auto-generated by default
- Field mapping, hidden behind advanced mode
- Secret fields based on type
- Description

Type-specific secret inputs:

SSH account:

- Username
- Password
- Private key
- Passphrase
- Enable username
- Enable password
- SSH port
- Telnet port

SNMP community:

- Community
- Port

HTTP basic:

- Username
- Password
- Token

Token:

- Token

### Sync Jobs Page

Purpose:

- Simplify importing existing provider secrets.

Flow:

1. Select provider.
2. Enter path prefix.
3. Dry-run.
4. Review candidate rows.
5. Fix ambiguous rows.
6. Apply.

Table columns:

- Provider path
- Suggested code
- Name
- Inferred type
- Usage
- Status
- Message

### Audit Page

Purpose:

- Trace credential changes and usage.

Filters:

- Time range
- Event type
- Actor
- Provider
- Credential code
- Result

Table columns:

- Time
- Event
- Actor
- Credential
- Provider
- Subject
- Result
- Message

## Security Requirements

MVP security baseline:

- Never store plaintext secret material in SecretHub DB.
- Never display plaintext in tables.
- Mask sensitive fields by default.
- Record audit logs for writes and resolves.
- Provider tokens should be stored as encrypted secrets or injected from environment.
- Keep provider write capability separate from read capability where possible.
- Avoid logging secret values.

Sensitive keys:

- `password`
- `passwd`
- `secret`
- `token`
- `private_key`
- `passphrase`
- `community`
- `auth_pass`

## Acceptance Criteria

MVP is acceptable when:

1. A user can add a Vault provider and test connectivity.
2. A user can create an SSH credential without writing catalog JSON.
3. The secret is written to Vault.
4. The catalog record is visible in SecretHub.
5. OneOps can list or sync the new credential.
6. Device onboarding can reference that credential.
7. A user can update only the password field without clearing username or other fields.
8. Audit logs show create/update/sync/resolve events.
9. Existing Vault secrets can be imported through dry-run and apply.
10. Lists never expose plaintext.

## Open Questions

- Should SecretHub be deployed as an independent service or inside OneOps backend initially?
- Should OneOps call SecretHub live, or should SecretHub push catalog rows into OneOps DB during the transition?
- Where should provider tokens be stored in production?
- Which auth system should SecretHub use for MVP?
- Should resolve return plaintext to OneOps backend or only short-lived material handles?
