# OneOPS NetPath Demo Closure Design

Date: 2026-06-22

## Purpose

Define the smallest remaining scope needed to move NetPath from productization-in-progress to `demo-ready`.

## Scope

In scope:

- result and evidence closure
- minimal policy closure
- at least one downstream probe/ticket consumer chain
- demo gate semantics and blockers

Out of scope:

- full production rollout hardening
- broad policy-family expansion beyond minimal closure
- full shared-contract hardening

## Closure Target

`demo-ready` means:

- snapshot -> analyze -> result -> evidence chain is complete;
- at least one downstream consumer chain is demonstrable;
- policy semantics are no longer silently over-optimistic.

## Remaining Gaps

- result/evidence UX closure
- minimal policy closure
- probe/ticket demonstrable end-to-end chain

## Recommended Work Buckets

1. Result and evidence closure
2. Minimal policy closure
3. Probe/ticket demo chain
4. Demo evidence and gate review
