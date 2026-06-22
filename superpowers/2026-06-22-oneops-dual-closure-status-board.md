# OneOPS Dual-Closure Status Board

Date: 2026-06-22

## Purpose

This board tracks the closure status of:

- `IPAM launch closure`
- `NetPath demo closure`
- `NetPath production closure`
- `Shared contract hardening`

Status vocabulary:

- `planned`
- `source-level complete`
- `verified`
- `integrated`
- `ready`

NetPath ready states:

- `demo-ready`
- `production-ready`

IPAM ready state:

- `launch-ready`

## Current Board

| Line | Phase | Status | Target Ready State | Notes |
| --- | --- | --- | --- | --- |
| `IPAM` | Launch closure | `planned` | `launch-ready` | Focused design and implementation plan now exist; execution not started |
| `NetPath` | Demo closure | `planned` | `demo-ready` | Focused design and implementation plan now exist; execution not started |
| `NetPath` | Production closure | `planned` | `production-ready` | Deferred until demo closure reaches the open criteria |
| `dc2` | Shared contract hardening | `planned` | minimal hardened contract | Deferred until IPAM and NetPath expose stable shared-fact needs |

## Operating Rule

When a phase changes status, update this board in the same round as the phase-local spec/plan or implementation checkpoint.

## Related Docs

- `specs/2026-06-22-oneops-netpath-ipam-dual-closure-master-design.md`
- `plans/2026-06-22-oneops-netpath-ipam-dual-closure-master.md`
- `specs/2026-06-22-oneops-ipam-launch-closure-design.md`
- `plans/2026-06-22-oneops-ipam-launch-closure.md`
- `specs/2026-06-22-oneops-netpath-demo-closure-design.md`
- `plans/2026-06-22-oneops-netpath-demo-closure.md`
- `2026-06-22-oneops-dual-closure-phase-open-criteria.md`
