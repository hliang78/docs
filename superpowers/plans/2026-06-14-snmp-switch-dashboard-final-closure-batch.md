# SNMP Switch Dashboard Final Closure Batch

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close the current switch-dashboard backend boundary so public resolver methods are reduced to orchestration while generation, shared assembly, and persistence each live behind their own internal boundary.

**Architecture:** Keep the existing switch dashboard behavior and response contracts unchanged, but finish the internal split into three layers: generator, shared service, and persistence service. The active save/materialize/tree paths must all consume these boundaries instead of re-stitching logic inside `MetricCapabilityContractResolver`.

**Tech Stack:** Go backend in `/OneOPS/OneOps`, focused resolver/service tests, existing Teleabs/Grafana persistence tables, docs in `/OneOPS/docs/superpowers`.

---

## Batch Scope

This batch closes the current backend restructuring line in one pass:

- keep public API shape unchanged;
- keep current switch/routing-capable baseline behavior unchanged;
- add a dedicated internal persistence service;
- move active flat save and tree save execution to that persistence boundary;
- document the completed split.

Out of scope for this batch:

- runtime panel-state logic;
- UI changes;
- baseline-selection redesign;
- new dashboard families;
- routing data gating.

## Closure Target

After this batch, the active internal split is:

- `resolver`
  - public API-facing orchestration only
- `generator`
  - baseline resolution
  - template resolution
  - dashboard generation
  - binding-owner enrichment
- `service`
  - shared dry-run assembly
  - shared tree dry-run assembly
  - shared tree-generation assembly
- `persistence service`
  - flat save persistence
  - tree save persistence
  - save-batch persistence entry

That is the intended closure point for the current switch-dashboard backend line.
