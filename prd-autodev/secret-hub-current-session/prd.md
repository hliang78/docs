# SecretHub Backend First Slice PRD

## Summary

Create a standalone SecretHub backend foundation that manages Vault providers, credential catalog metadata, Vault secret writes/reads, OneOps-compatible metadata listing, resolve, validation, audit, and Vault catalog index export.

## Requirements

1. The backend exposes `GET /healthz`.
2. The backend exposes provider APIs for list, create, and connectivity test.
3. The backend exposes credential APIs for list, create, metadata update, partial secret update, resolve, and validate.
4. The backend exports a Vault catalog index compatible with current OneOps catalog sync.
5. Secret material is written to and read from Vault, not stored in SecretHub's local metadata store.
6. Provider tokens are resolved from environment references and are never returned by GET APIs.
7. Audit events record create/update/test/resolve/export operations without secret values.
8. Lists and audit APIs never expose plaintext fields such as password, token, private key, community, or auth pass.

## API Slice

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

## Acceptance

- A test can create a Vault provider backed by an environment token reference.
- A test can create an SSH credential and verify the Vault API receives a KV v2 write.
- A test can list credentials and verify no plaintext is included.
- A test can resolve a credential and verify field mapping is applied.
- A test can partially update only `password` without clearing existing `username`.
- A test can export OneOps Vault catalog index with `path` split from SecretHub `secret_path`.

## Validation

```bash
cd /Users/huangliang/project/OneOPS-ALL/secrethub/backend
go test ./...
go test ./... -run TestHTTP
gofmt -w .
```

## Follow-Up Slices

- Add production DB migration support.
- Add service auth/RBAC and tenant isolation.
- Add short-lived SecretHub material handles.
- Wire quick_env service container and sample provider.
- Add OneOps list provider/client integration.
- Add SecretHub UI pages after backend contracts stabilize.

## Current Session Evidence

- Backend module created at `secrethub/backend`.
- Implemented standard-library HTTP API and file-backed store.
- Implemented Vault KV v2 read/write/delete/list adapter.
- Implemented optional API-token auth and signed single-use material handles.
- Implemented OneOps SecretHub list provider behind `credential.providers.secrethub`.
- Added tests for KV v2 path normalization, HTTP credential lifecycle, API-token auth, and material-handle flow with a fake Vault.
- Added OneOps list tests for SecretHub override and SecretHub outage fallback.
- Validation command: `cd secrethub/backend && go test ./...`.
