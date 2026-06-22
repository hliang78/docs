# OneOPS Dual-Closure Deferred Phase-Open Criteria

Date: 2026-06-22

## Purpose

Define when it is valid to open:

- `NetPath production closure`
- `shared contract hardening`

## NetPath Production Closure Opens When

- NetPath demo closure is at least `integrated`
- a probe/ticket demo chain is visible end to end
- unresolved work is mostly runtime/ops hardening, not missing core UX chain

## Shared Contract Hardening Opens When

- IPAM launch closure is at least `verified`
- NetPath demo closure is at least `verified`
- both lines can point to a concrete minimal shared fact set that must become stable

## Explicit Rule

Do not open either deferred phase because the topic feels important in abstract. Open only when the earlier application closure phases have exposed stable, concrete needs.
