# SecretHub Current-Session Development Idea

## Original Request

`[$prd-autodev-loop] 请帮我推进secret hub的开发，不要通过自动化框架来实现。就在当前会话中进行。`

## Classification

Full-stack program, current-session implementation. This session starts with the backend because the existing SecretHub documents and OneOps integration notes identify backend contracts as the lowest-risk first dependency.

## Explicit Constraints

- Do not use OpenClaw or any automation framework.
- Work directly in the current Codex session.
- Keep progress file-based so follow-up work can resume from repository artifacts.

## Starting Slice

Implement the first standalone backend slice under `secrethub/backend`:

- Go service scaffold.
- Vault-only provider adapter.
- Provider CRUD/test endpoint.
- Credential create/list/update-secret/resolve/validate.
- Vault catalog index export for OneOps Phase 1 compatibility.
- Audit log without plaintext secret values.

