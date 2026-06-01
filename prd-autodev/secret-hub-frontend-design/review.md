---
topic: secret-hub-frontend-design
kind: frontend
title: SecretHub 前端规划设计
createdAt: 2026-05-28T17:03:32+0800
---

# Logic Review

## P0 Blockers

- Production UI implementation should start with SecretHub native login/session. A standalone browser app must not store a long-lived SecretHub service token in localStorage, source code, or static config.

## P1 Risks

- If the frontend exposes resolve as a normal action, SecretHub may become a plaintext viewer and violate the least-plaintext direction.
- If Audit Trail ships before backend pagination/filtering, it must be labeled as a recent-events view only.
- Local development may still need CORS or Vite proxy setup, but production should stay same-origin so session cookies are predictable.
- quick_env is owned by the OneOPS platform quick-deploy workflow and should not be presented as a SecretHub validation path.
- SecretHub validation should use its own backend/frontend dev servers, standalone compose, or the local artifact compose smoke.

## P2 Suggestions

- Prefer `secrethub/frontend` as a standalone Vite app with its own router, API client, auth gate and Swiss design tokens.
- Keep provider update/delete, credential delete, sync preview/apply, referrers and full audit search out of MVP until backend APIs exist.
- Treat OneOPS as an external API consumer only; do not couple SecretHub Console to OneOPS UI, route guards, stores or API envelope.
- If OneOPS later integrates with SecretHub, treat quick_env as the OneOPS-side deployment environment only, not as SecretHub's default runtime.
