# Firewall Imported Config Platform Test Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 `ctrlhub/controller/pkg/nodemap/tests/firewall/testdata/imported-configs` 中的真实防火墙配置导入 OneOPS 平台，验证防火墙模块的配置上传、Controller 快照解析、MinIO 回读、基线确认和 readiness 链路。

**Architecture:** 先用 Controller 离线语料测试证明解析器能处理样本，再通过 OneOPS 防火墙节点接口逐份上传配置。每次上传必须先通过 `/api/v1/firewall/config_snapshot` 预检，预检通过后才写 MinIO 和 `firewall_node.config_fact_snapshot`，再用平台接口回读和检查 readiness。

**Tech Stack:** Go, OneOPS firewall module, Controller NodeMap/firewall snapshot API, MinIO file storage, MySQL quick_env runtime.

---

## 1. Scope

In scope:

- 上传并验证 6 份 imported firewall config 文件。
- 覆盖 HuaWei/USG、SecPath、Dptech 三类平台值。
- 验证平台上传闭环：节点准备、文件上传、快照生成、MinIO 回读、基线变更确认、readiness、未匹配接口/区域、管理习惯反推入口。
- 区分解析器问题、平台链路问题和当前功能缺口。

Out of scope:

- 在线 SSH 采集真实设备。
- 自动下发策略。
- 完整历史快照版本表。当前代码主要使用 `firewall_node.config_fact_snapshot`。

## 2. Test Data Inventory

| File | Planned Platform | Offline Baseline |
| --- | --- | --- |
| `172.21.166.19-SH-HAP-ZJIDC-CORE-FW-HW-E8000E-X8-120260527_162627.log` | `USG` first, fallback `HuaWei` for direct Controller smoke | parsed as HuaWei: ports 71, policies 35, NAT 96, IPv4 routes 113, IPv6 routes 6 |
| `172.21.166.35-SH-HAP-ZJIDC-BORDER-FW-H3C-M9008-1&220260527_162629.log` | `SecPath` | ports 155, policies 15, NAT 2, IPv4 routes 21, IPv6 routes 0 |
| `172.22.166.14-SH-HAP-ZQIDC-CMNET-FW-H3C-M9016-220260527_162631.log` | `SecPath` | ports 88, policies 14, NAT 0, IPv4 routes 2, IPv6 routes 2 |
| `172.31.131.106-北斗短报文专用边界防火墙-0120260527_162634.log` | `Dptech` | ports 44, policies 1, NAT 0, IPv4 routes 1, IPv6 routes 0 |
| `172.31.188.11120260527_162634.log` | `USG` first, fallback `HuaWei` for direct Controller smoke | parsed as HuaWei: ports 53, policies 11, NAT 0, IPv4 routes 6, IPv6 routes 3 |
| `172.31.131.5-20260527_162629.log` | `USG` first, fallback `HuaWei` | not covered by current `TestImportedFirewallConfigsBuildOfflineNodeMap`; treat as discovery sample |

Note: OneOPS UI supported platform values include `USG`, `SecPath`, `Dptech`, `Sangfor`, `ASA`, `Fortinet`, `SRX`. Controller NodeMap also accepts `HuaWei` directly. For platform upload testing, prefer UI-supported `USG`; if direct Controller smoke is needed, use `HuaWei` to match the current offline corpus.

## 3. Environment Readiness

- [ ] Start quick_env with OneOPS core, Controller, MySQL and MinIO.

```bash
cd /OneOPS/quick_env
./start.sh --instance firewall-import-test --use-instance-oneops-core --enable-nginx --controller-function-area DefaultArea
./validate.sh --instance firewall-import-test
```

- [ ] Start Controller from the generated runtime if it is not already running.

```bash
cd /OneOPS/quick_env/.runtime/firewall-import-test
./controller/run.sh
```

- [ ] Confirm platform URLs and tokens.

```bash
export ONEOPS_BASE_URL="http://<oneops-host>:<oneops-port>"
export CONTROLLER_BASE_URL="http://<controller-host>:<controller-port>"
export TOKEN="<login-token-if-required>"
```

- [ ] Confirm direct Controller snapshot API is reachable.

```bash
curl -sS "$CONTROLLER_BASE_URL/api/v1/firewall/config_snapshot" \
  -H 'Content-Type: application/json' \
  -d '{"platform":"SecPath","config_text":"sysname smoke-test"}'
```

Expected: request reaches Controller. The tiny config may fail parsing, but the response must be a structured JSON error from Controller, not connection refused or proxy 404.

## 4. Offline Parser Baseline

- [ ] Run the existing imported config corpus test before platform upload.

```bash
cd /OneOPS/ctrlhub/controller
go test ./pkg/nodemap/tests/firewall -run TestImportedFirewallConfigsBuildOfflineNodeMap -count=1 -v
```

Expected: PASS for the 5 covered samples with the counts listed in section 2.

- [ ] Add a separate discovery result for `172.31.131.5-20260527_162629.log`.

Expected: either it parses with `HuaWei`/`USG` and gets added to the corpus, or it is recorded as unsupported syntax before platform upload. Do not mix this discovery failure with platform upload defects.

## 5. Platform Upload Cases

For each sample:

- [ ] Prepare or select one firewall node.

Required fields:

- `name`: include sample short name, for example `FW-IMPORT-H3C-M9008-BORDER`.
- `platform`: `USG`, `SecPath`, or `Dptech`.
- `ip`: use the IP embedded in the filename.
- `status`: `active`.

Use the UI route `/firewall` or the API route `/firewall/planning/firewall-node`. Capture the returned node `id`. If the create API rejects both empty and non-empty `code`, use an existing node or seed one directly; keep that as a node-create defect, not an upload defect.

- [ ] Upload the config file.

```bash
curl -sS -X POST "$ONEOPS_BASE_URL/firewall/planning/firewall-node/$NODE_ID/update-config-file" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@$CONFIG_FILE" \
  -F "config_text_format=raw"
```

Expected:

- HTTP success response with message `配置更新成功`.
- Response has non-empty `config_file_object_name`.
- Response has non-empty `config_fact_snapshot` or `config_fact_snapshot_data`.
- Snapshot `config_health.ok=true`.
- Snapshot `hostname` matches parsed sysname when present.
- Snapshot `facts.interfaces` and `facts.routes` are non-empty for the 5 covered samples.

- [ ] Verify MinIO回读.

```bash
curl -sS "$ONEOPS_BASE_URL/firewall/planning/firewall-node/$NODE_ID/config-content" \
  -H "Authorization: Bearer $TOKEN"
```

Expected:

- `content` length matches the uploaded file closely.
- `format=raw`.
- `object_name` matches the upload response.

- [ ] Verify generated snapshot.

```bash
curl -sS "$ONEOPS_BASE_URL/firewall/planning/firewall-node/$NODE_ID/config-snapshot" \
  -H "Authorization: Bearer $TOKEN"
```

Expected:

- `version=1`.
- `platform` equals the node platform.
- `fingerprint` starts with `sha256:`.
- `facts.interfaces.length > 0`.
- `facts.routes.length > 0` when the offline baseline has routes.
- Current known gap: `diagnostics.policy_count` and `diagnostics.nat_count` are not reliable platform assertions yet because Controller snapshot currently fills them as `0`.

- [ ] Verify readiness.

```bash
curl -sS "$ONEOPS_BASE_URL/firewall/planning/firewall-node/$NODE_ID/readiness" \
  -H "Authorization: Bearer $TOKEN"
```

Expected:

- `checks` contains `config`.
- Config check is ready and mentions parsed interfaces.
- Zone mapping may be not-ready until zones are created; that is acceptable for initial upload testing.

- [ ] Verify unmatched zone/interface helper.

```bash
curl -sS "$ONEOPS_BASE_URL/firewall/planning/firewall-node/$NODE_ID/unmatched" \
  -H "Authorization: Bearer $TOKEN"
```

Expected: returns structured `unmatched_interfaces` and `unmatched_zones`; no 500.

## 6. Baseline Change Cases

- [ ] Upload the same file again.

Expected: success without `confirm_baseline_change=true`, same or equivalent snapshot fingerprint.

- [ ] Upload a deliberately changed version of one sample without confirmation.

Change one low-risk line locally, such as an interface description or one static route in a temporary copy.

Expected:

- Upload is rejected before MinIO side effects.
- Error payload uses source fact/precheck style.
- Error code should correspond to `nodemap_firewall_node_config_baseline_changed`.

- [ ] Upload the changed version with confirmation.

```bash
curl -sS -X POST "$ONEOPS_BASE_URL/firewall/planning/firewall-node/$NODE_ID/update-config-file" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@$CHANGED_CONFIG_FILE" \
  -F "config_text_format=raw" \
  -F "confirm_baseline_change=true"
```

Expected:

- Upload succeeds.
- `config_fact_snapshot.fingerprint` changes.
- Old MinIO object is deleted or no longer referenced by the node.

## 7. Negative Cases

- [ ] Upload a sample with the wrong platform, for example H3C config as `Dptech`.

Expected: Controller snapshot precheck fails with a structured error; no MinIO object is written.

- [ ] Upload an empty file.

Expected: failure with config empty / snapshot precheck error; no MinIO object is written.

- [ ] Upload to a locked node.

Steps:

1. Complete enough readiness prerequisites to lock, or use an already locked node.
2. Call upload.

Expected: rejected with locked-node source fact error. Then verify `POST /firewall/planning/firewall-node/:id/unlock` with a reason allows upload again.

## 8. Functional Module Smoke After Upload

Run these only after at least one SecPath, one USG/HuaWei, and one Dptech sample upload succeeds.

- [ ] Management habit suggestion:

```bash
curl -sS "$ONEOPS_BASE_URL/firewall/planning/firewall-node/$NODE_ID/management-habit-suggestion" \
  -H "Authorization: Bearer $TOKEN"
```

Expected: structured suggestion or structured precheck telling exactly which source fact is missing.

- [ ] Latest policy overview:

```bash
curl -sS "$ONEOPS_BASE_URL/firewall/planning/firewall-node/$NODE_ID/management-habit-policy-overview" \
  -H "Authorization: Bearer $TOKEN"
```

Expected: no 500. For policy-rich samples, response should expose latest policy/context data if supported by the current implementation.

- [ ] Policy profile compile/preview smoke:

```bash
curl -sS -X POST "$ONEOPS_BASE_URL/firewall/planning/firewall-node/$NODE_ID/policy-generation-profile-compile" \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"policy_generation_profile":{}}'
```

Expected: either successful compile preview or structured validation error; no panic/500.

## 9. Pass Criteria

P0 pass:

- All 5 existing offline corpus samples still pass.
- At least one `USG`, one `SecPath`, and one `Dptech` upload succeed end to end.
- Uploaded config can be read back from MinIO.
- `config-snapshot` returns stable fingerprint, hostname, interfaces and routes.
- Baseline changed upload is blocked unless `confirm_baseline_change=true`.
- Readiness config check passes for uploaded nodes.

P1 pass:

- The sixth sample `172.31.131.5-20260527_162629.log` is either added to offline corpus and platform upload, or documented as unsupported with exact parser error.
- Management habit and policy overview endpoints return useful data for policy-rich samples.
- UI flow under `/firewall` matches API behavior and surfaces source fact errors clearly.

Known gaps to track separately:

- Platform snapshot diagnostics currently do not assert parsed `policy_count` or `nat_count`.
- Snapshot history APIs from the MVP plan are not present in current router; current acceptance should use `firewall_node.config_fact_snapshot`.

