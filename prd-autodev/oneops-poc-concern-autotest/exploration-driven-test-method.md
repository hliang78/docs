---
topic: oneops-poc-concern-autotest
kind: full-stack
title: OneOps PoC 关注方向自动测试闭环
createdAt: 2026-05-15T00:00:00+0800
program: true
---

# Exploration-Driven Test Method

本项目采用探索驱动测试，不采用简单的功能清单式测试。

每个关注方向必须先梳理业务流程动线，再围绕动线的最终目标和中途关键环境做探索。测试不只证明最终目标是否可达，也要发现链路中的薄弱环节，并按危害程度决定优先级。

## Core Loop

每个 workstream 和 story 都按同一个循环推进：

1. Flow line: 梳理目标方向的端到端流程动线。
2. Final goal: 定义这条动线最终必须证明的业务结果。
3. Critical environments: 标出流程中依赖的关键环境、数据、服务、脚本、设备和外部系统。
4. Weak-point hypotheses: 对每个关键环境提出薄弱环节假设。
5. Probe design: 用最小、可复核、可回滚的探针验证假设。
6. Harm classification: 按危害程度给薄弱环节分级。
7. Evidence and decision: 产出证据，并决定继续测试、补 fixture、拆修复 story、请求审批或延后。

## Flow Line Artifact

每个领域至少维护一条流程动线。动线不是架构图，而是测试执行视角下的业务路径。

模板：

```text
Flow: <领域名>
Actor: <操作主体或自动化主体>
Start: <入口动作>
Steps:
  1. <页面/API/脚本/设备动作>
  2. <中间状态或数据落点>
  3. <下游消费或展示>
Final Goal:
  <最终必须证明的业务结果>
Critical Environments:
  - <DB/API/service/device/agent/log/query/credential>
Weak-Point Hypotheses:
  - <可能失败点> -> <影响>
Evidence:
  - <API JSON / DB snapshot / command output / log query / screenshot>
Exit Decision:
  PASS / FAIL / BLOCKED / APPROVAL / SKIPPED
```

## Weak-Point Harm Classification

薄弱环节按危害程度分类，不按发现顺序平均处理。

| Class | Meaning | Priority Rule | Examples |
|---|---|---|---|
| H0 Critical | 会导致错误上线判断、误触外部系统、泄露凭据、破坏恢复能力，或让核心门禁结论不可信 | 优先挖掘和修复，不能被低危问题阻塞注意力 | 明文凭据进入日志；测试误连生产设备；告警恢复失败但门禁仍 PASS |
| H1 High | 会破坏端到端主路径，或让关键证据缺失，导致上线质量门禁无法判定 | 当前批次优先处理，必要时拆修复 story | Device V2 入库字段缺失；Prometheus 无样本；Loki 查不到已触发日志 |
| H2 Medium | 局部能力异常，有替代证据或可降级，但会影响稳定性、可观测性或后续自动化 | 在高危项之后处理，记录复现条件 | 浏览器截图缺失但 API 证据完整；某厂商字段 unsupported 未分类 |
| H3 Low | 体验、文案、报表可读性或非阻断一致性问题 | 汇总到后续 polish 或证据改进批次 | 摘要措辞不统一；非关键列缺少排序 |

危害等级必须写入 evidence 和后续 story。没有危害等级的薄弱环节不能进入修复优先级排序。

## Probe Types

探针从低风险到高风险逐层推进。除非已有用户确认，否则不能跳过低风险探针直接执行真实变更。

| Probe Type | Purpose | Allowed Output |
|---|---|---|
| Static probe | 梳理代码、路由、脚本、配置、字段合同 | call map、API map、field map |
| Read-only data probe | 读取 DB/API/log/query 当前事实 | sanitized inventory、current state JSON |
| Dry-run probe | 验证计划、参数、预检查和可执行性 | dry-run result、preflight report |
| Controlled action probe | 在测试环境执行可恢复动作 | action log、before/after snapshot、recovery proof |
| End-goal proof | 验证最终目标是否真的达成 | combined evidence bundle |

每个 story 应尽量只推进一个 probe level。需要跨 level 时，必须明确前置条件和停止点。

## Story Shape

探索 story 必须比能力域更细，通常只回答一个问题。

必填字段：

- Flow line: 对应哪条流程动线。
- Question: 这一轮只回答一个什么未知问题。
- Hypothesis: 当前推测是什么。
- Probe level: static / read-only / dry-run / controlled-action / end-goal-proof。
- Critical environment: 本轮接触哪些环境。
- Weak-point hypotheses: 本轮要验证哪些薄弱环节。
- Harm class: H0/H1/H2/H3，未知时先按 H1 处理。
- Stop condition: 什么情况 PASS、BLOCKED、APPROVAL 或 FAIL。
- Evidence contract: 产出哪些文件，如何脱敏，如何回写矩阵。
- Next decision: 通过后进入哪一层探针；失败后拆什么修复或补环境 story。

## Batch Sequencing Rule

每个批次优先按探索深度组织，而不是按功能宽度组织。

推荐顺序：

1. Flow mapping batch: 只梳理流程动线、关键环境和薄弱环节假设。
2. Read-only baseline batch: 只读取当前事实，建立 fixture 和证据基线。
3. Dry-run batch: 验证计划、参数、预检查和脚本可运行性。
4. Controlled action batch: 执行可恢复动作，证明中间状态和恢复能力。
5. End-goal proof batch: 汇总端到端组合证据，判断门禁是否通过。
6. Remediation batch: 按 H0/H1/H2/H3 拆分修复故事，由对应 lane 执行。

如果一个批次同时包含 flow mapping、真实动作、最终目标证明和修复，它就太粗，必须拆分。

## Evidence Requirements

每个探索证据必须说明：

- 目标流程动线。
- 本轮最终目标或中间目标。
- 接触的关键环境。
- 发现的薄弱环节。
- 薄弱环节危害等级。
- 证据文件路径。
- 是否需要修复、补 fixture、人工审批或延后。

固定状态仍使用：

- `PASS`: 当前问题已被证据证明通过。
- `FAIL`: 产品或脚本存在可复现失败。
- `BLOCKED`: 环境、数据、权限、依赖不足。
- `APPROVAL`: 继续需要人工批准。
- `SKIPPED`: 明确延后，不参与当前门禁。

## Application To WS-01

WS-01 不能直接从“设备/监控/日志/拓扑门禁”启动大测试。它应先拆成四条流程动线：

1. Device flow: fixture inventory -> Device V2 record -> DC2 target resolution -> collect/facts -> store readiness -> field manifest -> UI/API evidence。
2. Monitoring flow: fixture device -> monitoring strategy/template -> task delivery/governance -> Prometheus sample -> label assertion -> UI/API evidence。
3. Logging flow: fixture source -> log-forward plan -> dry-run/preflight/apply -> deterministic syslog/tail trigger -> Loki query -> label/content assertion。
4. Topology flow: fixture devices/interfaces -> DC2 topology facts -> obsflow L2 snapshot -> topology API -> frontend graph -> drill-down evidence。

每条动线先找 H0/H1 薄弱环节，再决定是否进入真实动作探针。
