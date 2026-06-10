# Firewall Policy Generation Profile - 2026-06-09

## Node

- Node: `FW-172.22.166.14-H3C-M9016-CMNET`
- Hostname: `SH-HAP-ZQIDC-CMNET-FW-H3C-M9016-2`
- Platform: `SecPath`
- Source payload: `/tmp/fw-mgmt-policy-test-payload.json`

## Generated Files

- `FW-172.22.166.14-H3C-M9016-CMNET.policy_generation_profile.yaml`
  - Paste this directly into the frontend policy generation profile editor.
- `FW-172.22.166.14-H3C-M9016-CMNET.policy_generation_profile.with-signals.yaml`
  - Same profile plus reverse-inference evidence.

## Batch Platform Setup

On 2026-06-09, the current active `firewall_node` records in the demo platform were updated in place.

- Active firewall nodes updated: `18`
- Soft-deleted historical firewall nodes skipped: `2`
- Metadata target: `firewall_node.meta_data`
- Preserved existing metadata keys such as `physical_firewall`, `firewall_vsys`, `split_file`, and `source`.
- Added/overwrote only the nested `policy_generation_profile` and batch trace fields.

Batch artifacts:

- `firewall_node_meta_data_backup_2026-06-09.jsonl`
  - Original metadata backup before this batch update.
- `firewall_policy_generation_profile_batch_2026-06-09.csv`
  - Per-node policy template, address strategy, service strategy, and compile status.
- `FWN*.policy_generation_profile.yaml`
  - Per-node generated `policy_generation_profile` files.

Batch verification:

- All `18` active nodes have valid JSON metadata after the update.
- All `18` active nodes now contain `policy_generation_profile`.
- All `18` saved profiles compiled successfully through Controller `/api/v1/firewall/policy_generation_profile/compile`.

## Reverse Inference

Controller `policy_generation_profile/expression_habit` inferred:

- Address strategy: `inline_address`, confidence `high`
- Service strategy: `inline_service`, confidence `medium`
- Signal: based on the latest usable parsed policy from the node.

## Verification

Compile API succeeded:

- `policy_name_template`: `SH-policy{SEQ:id:4:1:1:MAIN}`
- compiled address strategy: `inline_address`
- compiled service strategy: `inline_service`

Real management-habit policy test with the compiled profile:

- Summary: 24 scenarios, 7 passed
- `Trust -> Untrust`: 2 / 4 passed
- `Trust -> Management`: 3 / 4 passed
- `Untrust -> Trust`: 2 / 4 passed
- Management-related directions still need route/config cleanup before they can fully pass.

Example generated CLI:

```text
security-policy ip
 rule 3 name SH-policy0003
  source-zone Trust
  destination-zone Untrust
  source-ip-host 10.1.1.1
  destination-ip-host 172.22.254.73
  service-port tcp destination eq 2455
  action pass
```
