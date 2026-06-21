# OneOPS DC2 Policy Golden Runtime Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prove first-phase NetPath policy and route facts can run through the real DC2 standardize/process pipeline from realistic device command output.

**Architecture:** Add golden fixture tests around existing configured contracts instead of adding a side-channel parser harness. Each fixture feeds `stdout` into `DeviceCollection2Srv.Standardize`, then feeds standardized rows into `ProcessFacts`, and asserts canonical facts and fields. Real-device smoke runs can later reuse the same dataset list and expected fact families.

**Tech Stack:** Go tests, DC2 configured YAML contracts, raw_text standardizer, canonical fact registry.

---

## Task 1: Golden Runtime Tests For Policy CLI Facts

**Files:**
- Create: `OneOPS/app/device_collection2/service/impl/device_collection2_policy_golden_test.go`

- [ ] **Step 1: Write failing golden tests**

Add table-driven tests for H3C SecPath and Huawei USG configured contracts. For each `cli_*` policy dataset, call `Standardize` with realistic `stdout`, then call `ProcessFacts`, and assert the expected fact type and a few normalized fields.

- [ ] **Step 2: Run the targeted tests**

Run:

```bash
cd OneOPS
go test ./app/device_collection2/service/impl -run 'TestPolicyGolden'
```

Expected: fail first if any parser/contract path still only emits raw row-level facts.

- [ ] **Step 3: Fix parser or contract gaps**

Keep fixes scoped to `app/device_collection2/fact/route_policy_processor.go` or configured contract YAML only. Preserve raw fallback for unknown output.

- [ ] **Step 4: Run regression**

Run:

```bash
cd OneOPS
go test ./app/device_collection2/fact ./app/device_collection2/service/impl -run 'TestPolicyGolden|TestPolicyFactProcessor|TestPolicyRawDataset|TestConfiguredPolicyContracts'
go test ./app/device_collection2/...
```

Expected: all pass.

## Task 2: Real Device Smoke Hook

**Files:**
- Create or update a script only if the repo does not already have a suitable DC2 single-device smoke entrypoint.

- [ ] **Step 1: Locate existing real-device test entrypoint**

Find current scripts/env vars for controller-backed DC2 collection.

- [ ] **Step 2: Document the exact dataset list**

Use the configured firewall datasets:

```text
cli_security_zone_binding
cli_acl_rule
cli_firewall_policy
cli_nat_rule
cli_pbr_rule
snmp_ipRouteTable
```

- [ ] **Step 3: Run against an available test device**

Use platform-owned device credentials/configuration only. Do not print secrets. Capture dataset status, fact counts, and first normalized fact sample per fact type.
