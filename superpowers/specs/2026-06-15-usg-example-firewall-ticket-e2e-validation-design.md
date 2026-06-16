# USG Example Firewall Ticket E2E Validation Design

**Date:** 2026-06-15

**Goal**

Build a repeatable end-to-end validation flow that converts `ctrlhub/controller/pkg/nodemap/example/usg_example/test_policy.yaml` test cases into real firewall ticket work orders, uploads them through the existing firewall ticket flow, and verifies whether the resulting match/reuse/new-policy behavior is consistent with the current `usg example` oracle.

**Why This Exists**

The existing `usg example` workflow already proves controller-side behavior with local fixtures and HTML reports, but it does not validate the real `/ticket/firewall` upload path, blueprint-tag selection, work-order item creation, or UI-visible execution results. We need one flow that connects those layers and explicitly covers:

- cases that should hit existing policies
- cases that should partially reuse existing policies
- cases that should generate new policy configuration
- cases that should surface route or planning errors

## Scope

This design covers:

- reading `test_policy.yaml`
- reading `test_policy_report.html` as the oracle
- resolving blueprint tags from node names
- generating uploadable firewall ticket workbooks
- creating firewall tickets through the real UI/API path
- collecting resulting work-order details
- reconciling actual results against oracle expectations
- producing a machine-readable and human-readable validation report

This design does not cover:

- changing firewall ticket backend matching logic
- changing `usg example` generation logic
- redesigning the firewall ticket upload format
- full support for complex inbound workbook rows that require server or load-balancer fields not present in `test_policy.yaml`

## Source Inputs

The validation flow consumes these inputs:

1. `test_policy.yaml`
   - Source of node names, groups, test-case order, scenario names, and traffic intent fields.
   - Core fields used for conversion are `src`, `dst`, `service.protocol`, `service.port`, and optional descriptive metadata.

2. `test_policy_report.html`
   - Oracle for expected behavior.
   - The report already contains the effective controller-side outcome for each case, including whether existing policy matched and whether configuration was generated.

3. `Blueprint` tag options from `/api/v1/symbol/tag/optsByBusinessType/Blueprint`
   - Runtime source of `blueprint_tag_code`.
   - Tag `label` is matched against the node name from `test_policy.yaml`.

## Oracle Model

We will not infer expectations from the scenario name alone. The scenario name is useful for reporting, but the authoritative expected outcome comes from the HTML report.

Each `usg example` case is normalized into one of four expected classes:

- `matched_only`
  - Existing policy matched.
  - No new generated configuration is expected.

- `generated_only`
  - No existing policy matched.
  - New generated configuration is expected.

- `mixed`
  - Existing policy matched in part and new generated configuration is also expected.

- `error`
  - The case is expected to end in route, planning, or other execution-preventing failure.

The normalization source is the report row for the same:

- node name
- group name
- scenario name
- case index within the group

Primary signals from the HTML report:

- `MatchedCount`
- `GeneratedCount`
- `MatchedDetails`
- `GeneratedDetails`

## Workbook Conversion Model

### Direction Choice

The first implementation will generate only `OUT` workbook rows, using the existing `情景2` workbook shape.

Reason:

- The firewall ticket backend accepts `IN` rows, but inbound rows have extra semantic requirements such as `Area`, `real_ip`, `real_port`, or load-balancer fields.
- `test_policy.yaml` reliably provides traffic intent but not the additional inbound-only server modeling fields.
- For the first end-to-end validation, we want to measure policy hit/reuse/new-generation behavior, not fail due to unrelated workbook completeness gaps.

This means the generated workbook structure will follow the existing production sample format:

- sheet name: `工单`
- section title: `情景2：出向策略工单 - <node>`
- columns:
  - `访问源(必填)`
  - `访问目标地址(必填)`
  - `访问目标端口`
  - `协议(必填)`
  - `SNAT`
  - `备注`

### Row Mapping

Each `test_policy.yaml` test case becomes exactly one workbook row.

Mapping:

- `src` -> `访问源`
- `dst` -> `访问目标地址`
- `service.port` -> `访问目标端口`
- `service.protocol` -> `协议`
- empty string -> `SNAT`
- synthesized trace string -> `备注`

The trace string in `备注` is required for reconciliation and will contain:

`USG_E2E|<node>|<group>|#<case_index>|<scenario_name>`

This string must be stable and unique within one validation run so that each uploaded work-order item can be mapped back to the original case.

### Workbook Grouping

One workbook is generated per node.

Reasons:

- keeps blueprint-tag resolution simple
- keeps execution blast radius limited
- makes failures easier to isolate
- avoids mixing unrelated node contexts inside one work order

## Blueprint Tag Resolution

Blueprint tag resolution is strict exact-match on node name.

Rule:

- fetch all `Blueprint` options
- compare `option.label` against the node name from `test_policy.yaml`
- if exactly one match is found, use that `option.value` as `blueprint_tag_code`

Failure handling:

- zero matches -> mark node as `missing_blueprint_tag`, skip upload for that node
- more than one match -> mark node as `ambiguous_blueprint_tag`, skip upload for that node

This flow intentionally avoids fuzzy matching and prefix matching. The cost of missing one node is lower than the cost of uploading a work order to the wrong blueprint.

## Upload And Execution Flow

For each node with a resolved blueprint tag:

1. generate workbook
2. upload workbook through the real firewall ticket upload path
3. create one firewall ticket using the resolved `blueprint_tag_code`
4. record returned work-order code
5. poll or re-query the work order until a stable state is observed
6. fetch work-order details, item details, and route decisions when needed

Work orders are processed sequentially, not in parallel.

Reason:

- limits load on the environment
- makes network and execution logs easy to attribute
- reduces the chance that concurrent runs hide causality

## Actual Result Classification

Each uploaded work-order item is classified using backend-visible outputs, not just top-level work-order status.

Primary evidence:

- item `item_status`
- item configs:
  - `matched_cli`
  - `generated_cli`
- route-decision records when the item status indicates planning or routing failure

Actual classification rules:

- `matched_only`
  - `matched_cli` present
  - `generated_cli` absent

- `generated_only`
  - `generated_cli` present
  - `matched_cli` absent

- `mixed`
  - both `matched_cli` and `generated_cli` present

- `error`
  - item status indicates route, conflict, simulation, deny, loop, missing next hop, unsupported multi-route, or other planning failure

If none of the above rules can classify an item deterministically, the item is marked `unclassified_actual` and reported explicitly.

## Reconciliation Rules

Each actual item is joined back to the source case using the structured `备注` marker.

For each source case, the report will show:

- node
- group
- case index
- scenario name
- oracle class
- actual class
- consistency result

Consistency is `true` only when:

- blueprint tag resolved correctly
- workbook row was uploaded
- a corresponding work-order item was found
- the actual class equals the oracle class

Otherwise the case is reported as one of:

- `oracle_mismatch`
- `upload_failed`
- `missing_blueprint_tag`
- `ambiguous_blueprint_tag`
- `item_not_found`
- `unclassified_actual`

## Output Artifacts

The validation run should produce both raw and summarized artifacts.

Raw artifacts:

- generated workbook per node
- manifest file listing node, blueprint tag code, workbook path, row count, and expected classes
- upload/create results including work-order codes
- fetched work-order detail snapshots as needed

Summary artifacts:

- machine-readable reconciliation report, preferably JSON
- human-readable summary report, preferably Markdown

The summary report should include:

- total nodes discovered
- nodes with resolved blueprint tags
- skipped nodes and reasons
- total work orders created
- total work-order items reconciled
- consistent count
- inconsistent count
- unresolved count
- grouped results by scenario name
- grouped results by actual class

## Risk Controls

### Environment Safety

- Process nodes sequentially.
- Do not batch many nodes into one work order.
- Keep generated workbooks in a dedicated output directory.
- Record all created work-order codes so cleanup is possible.

### Data Safety

- Do not mutate source `usg example` files.
- Do not change existing ticket behavior in the first implementation.
- Do not use fuzzy blueprint matching.

### Diagnostic Quality

- Always preserve the `备注` trace marker.
- Always keep per-node manifest rows.
- Always store enough evidence to explain mismatches without rerunning immediately.

## Testing Strategy

Validation happens at three levels:

1. conversion-level verification
   - confirm `test_policy.yaml` cases are transformed into expected workbook rows
   - confirm oracle extraction from HTML report is stable
   - confirm blueprint-tag exact matching behaves correctly

2. upload-flow verification
   - confirm generated workbook can be uploaded and ticket created
   - confirm returned work-order code is recorded

3. reconciliation verification
   - confirm created work-order items can be joined back to source cases
   - confirm actual class computation matches backend-visible item evidence

The first execution should prioritize nodes that already have exact blueprint-tag matches in the runtime environment. Full coverage is desirable, but a stable first pass is more important than forcing every edge node through the path immediately.

## Open Decision Recorded

The user explicitly requested that:

- existing-policy-hit scenarios must be included in testing
- blueprint tags must be selected by node name
- validation should be end-to-end through the real `/ticket/firewall` flow, not just offline artifact generation

This design follows those decisions directly.
