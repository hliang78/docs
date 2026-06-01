# SecretHub Current-Session Context Brief

## Goal

Move SecretHub from design-only documentation into a runnable backend foundation that can support the documented Phase 1 compatibility path.

## Current Code Facts

- `docs/secret_hub` contains design, OneOps integration, and AI handoff documents.
- `secrethub/` did not exist before this session.
- Existing OneOps already has credential list, Vault catalog CRUD/sync, migration audit, and material handle support.
- Existing OneOps Vault catalog physical path rule is `path + "/" + code`, unless the path already ends with the code.
- Existing OneOps list DTO exposes credential summary metadata only: `code`, `name`, `type`, `masked`, `provider`, `usage`.

## Assumptions For This Session

- Build a standalone SecretHub service rather than embedding inside `OneOPS`.
- Use Go to stay close to OneOps backend conventions.
- Avoid external Go dependencies in the first slice so the backend compiles independently and quickly.
- Use a file-backed JSON store for the first runnable version; production DB migrations can come after contracts stabilize.
- Provider token is referenced by `auth_ref`, not persisted as plaintext.
- Resolve may return plaintext material to trusted callers for MVP, but audit logs and list APIs must never store or return plaintext.

## Non-Goals

- No SecretHub frontend in this first slice.
- No OneOps code changes in this first slice.
- No OpenClaw story publication or task creation.
- No secret rotation, approval workflow, enterprise IAM, or multi-provider parity.

## Key Risks

- File-backed storage is intentionally transitional and not production storage.
- Auth/RBAC and tenant isolation still require a follow-up security design.
- Resolve currently exposes plaintext to trusted backend callers until short-lived material handles are implemented.
- Phase 1 catalog ownership must be operationally clear: SecretHub owns catalog entries it exports.

