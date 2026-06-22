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
| `IPAM` | Launch closure | `planned` | `launch-ready` | Waiting for focused closure spec and plan |
| `NetPath` | Demo closure | `planned` | `demo-ready` | Waiting for focused closure spec and plan |
| `NetPath` | Production closure | `planned` | `production-ready` | Opens only after demo closure is integrated |
| `dc2` | Shared contract hardening | `planned` | minimal hardened contract | Opens only after IPAM and NetPath prove stable consumer needs |

## Operating Rule

When a phase changes status, update this board in the same round as the phase-local spec/plan or implementation checkpoint.
