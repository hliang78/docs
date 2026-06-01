# PoC Concern Extraction

Source document: `/Users/huangliang/Library/Containers/com.tencent.xinWeChat/Data/Documents/xwechat_files/wxid_7323973239612_4510/temp/drag/上海移动研究院自动化运维平台POC测试方案_V1.1(1).docx`

## Extraction Rule

Only extract concern directions that reflect OneOps platform priorities. Do not treat the source as a PoC execution checklist.

## Source Concerns

- Daily operations should be easier for on-call staff.
- Platform behavior should match existing security and change-management constraints.
- Critical operations should be traceable, reviewable, and auditable.
- Monitoring/logging should reduce cross-system switching.
- Alerts should reduce noise and support assignment, suppression, maintenance windows, and recovery closure.
- Credentials should be reference-driven and not scattered across scripts, sheets, or chat records.
- Automation should make routine inspection, scheduling, scripting, and safe trial runs repeatable.
- Firewall policy changes should reduce inconsistency between request, approval, generation, execution, query, and reconciliation.
- Distributed Controller/Agent deployment should support separated security zones.
- Evidence should be good enough for review and archive, not only for one-time demo.

## Extracted Capability Domains

| Domain | Source TC Range | OneOps Concern |
|---|---|---|
| Device onboarding | TC-01 | Object foundation, field integrity, uniqueness, site/room binding |
| Monitoring/logging | TC-02 to TC-05 | Collection, metric/log data availability, centralized query and dashboards |
| Topology | TC-06 | Node/link visibility, drill-down, snapshot and collected relation persistence |
| Agent/Controller | TC-07 to TC-08 | Distributed deployment, health, version, lifecycle operations |
| Alerting | TC-09 to TC-13 | Trigger, notification, escalation, suppression, maintenance, recovery |
| Credential/audit | TC-14 to TC-15 | Vault-style credential reference, operation log search/export |
| Automation/script | TC-16 to TC-20 | Template execution, variable sets, schedules, AI script draft, sandbox trial |
| Firewall workflow | TC-21 to TC-22 | Ticket import, policy generation, push feedback, query and reconciliation |
| Evidence loop | Cross-cutting | Batch evidence, matrix status, release/readiness decisions |

## PRD Implication

The final PRD should not mirror the 22 PoC cases one-to-one. It should define a long-running OneOps automatic validation program, with a first batch that safely establishes evidence coverage and later batches that target gaps by lane.
