# Netlink Netmiko Platform Adapter Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Backfill netlink platform profiles from Netmiko behavior for read-only backup and show-command workflows.

**Architecture:** Keep Go netlink as the execution engine. Add offline tests for platform mode/profile data, then update netlink and OneOPS template YAML to make Huawei, H3C, Maipu, and FiberHome platform behavior explicit. Fix the task-center Ansible backup script recursion and broaden its platform aliases.

**Tech Stack:** Go tests, YAML mode/profile configuration, Ansible YAML, Netmiko platform behavior as reference.

---

### Task 1: Offline Platform Profile Tests

**Files:**
- Create: `netlink/config/platform_profile_offline_test.go`

- [ ] **Step 1: Write failing offline tests**

Add tests that load `netlink/configs/mode_configs/*.yaml` and `ctrlhub/controller/deploy/templates/*/*/mode_config/base_mode_config.yaml`, assert key platform files parse, and verify Maipu/FiberHome are not identical to Comware.

- [ ] **Step 2: Run failing tests**

Run: `cd netlink && go test ./config -run 'TestModeConfigPlatformProfiles|TestOneOPSTemplateModeConfigs' -count=1`

- [ ] **Step 3: Backfill profile YAML**

Update netlink and OneOPS template mode configs for Huawei VRP/USG, H3C Comware/SecPath, Maipu MyPower, and FiberHome Fengine.

- [ ] **Step 4: Run tests**

Run the same Go test command and expect pass.

### Task 2: Task-Center Backup Script

**Files:**
- Modify: `quick_env/init-configs/gitea/source-repo/ansible/network-config-backup/site.yml`
- Modify if mirrored locally: cloned/generated source repo files only if present and in scope.

- [ ] **Step 1: Write failing static test**

Add an offline test or script check that fails when `huawei_backup_command` and `h3c_backup_command` self-reference, and verifies new platform aliases.

- [ ] **Step 2: Fix recursion and platform aliases**

Rename resolved variables and add aliases for `huawei_vrp`, `huawei_usg`, `h3c_comware`, `h3c_secpath`, `maipu_mypower`, and `fiberhome_fengine`.

- [ ] **Step 3: Run offline validation**

Run YAML parsing/static checks. No SSH/Telnet.

### Task 3: Manual Confirmation Runbook

**Files:**
- Create: `docs/runbooks/netlink-maipu-fiberhome-manual-confirmation.md`

- [ ] **Step 1: Create runbook**

Document one-time manual confirmation for Maipu first, FiberHome second. Include commands to run manually and results to record.

- [ ] **Step 2: Review**

Ensure the runbook does not instruct automated loops or repeated login.

### Task 4: Verification

**Files:**
- All touched files.

- [ ] **Step 1: Run Go offline tests**

Run: `cd netlink && go test ./config ./mode ./pipeline -count=1`

- [ ] **Step 2: Run YAML static checks**

Run a Python YAML parser over touched YAML files.

- [ ] **Step 3: Summarize**

Report changed files, tests, and manual confirmation boundaries.
