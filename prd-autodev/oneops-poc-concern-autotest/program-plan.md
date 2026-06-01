---
topic: oneops-poc-concern-autotest
kind: full-stack
title: OneOps PoC 关注方向自动测试闭环
createdAt: 2026-05-14T10:47:34+0800
program: true
---

# Program Plan

## Objective

把 PoC 文档映射出的 OneOps 关注方向，转化为一套探索驱动、可分批执行、可回写证据、可驱动后续修复的自动测试项目。

本项目按“完整 PRD 规划 + 多轮 workstream 深入”的方式推进。WS-01 的设备/监控/日志/拓扑是第一阶段深入对象，但不是 PRD 的全部范围。

测试策略从“功能清单验证”调整为“流程动线探索”。每个方向先梳理端到端流程动线，再围绕最终目标和中途关键环境设计探针，同时挖掘薄弱环节并按危害程度排序。

## Definition Of Done

- PRD 明确每个关注方向的成功标准、非目标、证据要求和自动化边界。
- `test-matrix.md` 覆盖 PoC 提取出的主要能力域，并映射到 OneOps 页面/API/脚本/模块。
- `exploration-driven-test-method.md` 明确流程动线、关键环境、薄弱环节、危害等级、探针层级和证据决策规则。
- 每个 workstream 至少有初版目标、验收形态、证据形态、开放问题和批次位置。
- 每个 workstream 至少有一条流程动线，且每条动线声明最终目标、中途关键环境、H0/H1 薄弱环节假设和下一批探针。
- 首批 OpenClaw 故事只覆盖一个可审查的小批次，且在用户确认后发布。
- 每批自动化执行后产生证据摘要，并更新矩阵状态和下一批建议。

## Scope

### In Scope

- 从 PoC 文档提取关注方向。
- 研究 OneOps 当前代码、页面、API、脚本和测试资产。
- 梳理目标方向的流程动线、最终目标、关键环境和薄弱环节假设。
- 输出 full-stack PRD、分域 workstream、测试矩阵和首批故事包草案。
- 后续通过 `ct`、`d2-fe`、`d2-be` 等 OpenClaw lane 分批驱动自动测试和必要修复。

### Out Of Scope

- 执行上海移动研究院 PoC。
- 使用真实客户设备或把测试结果包装成客户 PoC 验收结论。
- 一次性发布所有自动化故事。
- 未经确认修改生产配置、认证/租户逻辑、迁移、依赖、部署或外部集成。

## Exploration-Driven Test Model

本项目的测试批次按探索深度组织，而不是按功能宽度一次性铺开。详细方法见 `exploration-driven-test-method.md`。

每个目标方向必须先回答：

- 流程动线是什么：入口、关键步骤、数据落点、下游消费、最终目标。
- 最终目标如何证明：哪些 API、DB、日志、Prometheus/Loki、脚本输出、浏览器截图构成组合证据。
- 中途关键环境是什么：DB、服务、Agent、设备、凭据、策略、脚本、查询系统、外部系统。
- 哪些位置最脆弱：环境缺口、字段合同、状态流转、恢复能力、审计、明文泄露、误连外部系统。
- 危害等级是什么：H0/H1 优先挖掘和修复，H2/H3 记录但不能抢占主路径。

Story 不能只写“验证某能力”。每个探索 story 必须写清一个问题、一个 probe level、一个停止条件和一个下一步决策。

## Workstreams

| ID | Workstream | Lane | Status | Notes |
|---|---|---|---|---|
| WS-01 | 设备纳管、监控日志与拓扑 | ct, d2-fe, d2-be | draft | 先验证已有 D2/监控/日志/拓扑脚本和合同，再决定修复故事 |
| WS-02 | Agent Controller 与分布式部署 | ct | draft | P0 验证单 Controller/Agent 链路的真实生命周期动作和 Agent 侧回执 |
| WS-03 | 告警管理闭环 | ct, d2-fe, d2-be | draft | P0 覆盖真实关闭设备触发、通知策略、send log、超时升级；抑制/维护/主次关联为 P1 |
| WS-04 | 操作安全域与审计 | ct, d2-fe, d2-be | draft | P0 允许真实写入测试凭据、真实远程执行，验证轮换/禁用、不暴露明文和审计 |
| WS-05 | 自动化工作台与脚本辅助 | ct, d2-fe, d2-be | draft | P0 覆盖模板、变量集、定时、任务执行、脚本试跑、真实 LLM AI 辅助 |
| WS-06 | 防火墙工单与策略对账 | ct, d2-fe, d2-be | draft | P0 覆盖工单导入、对象解析、预检查、CLI 推荐配置、策略查询/对账；推送反馈和真实防火墙延后 |
| WS-07 | 跨域证据与回归体系 | ct | draft | 固定中文证据摘要、矩阵回写、管理层 readiness 总览、机器可读门禁 JSON |

## Dependency Map

- WS-01 是多数后续域的对象基础：设备对象、采集结果和拓扑关系需要先有可复核基线。
- WS-02 是分布式执行前提：Agent/Controller 健康决定采集、日志、远程任务等验证是否可信。
- WS-03 依赖真实设备异常或可控事件证据，P0 采用真实关闭测试设备触发，不能只验证告警页面渲染。
- WS-04 与 WS-05 共用凭证引用和远程执行证据边界。
- WS-06 依赖安全区域规划、策略对象、采集解析和工单链路。
- WS-07 横向服务所有 workstream，定义每批证据是否足够进入下一批。

## Risk Register

| Severity | Risk | Decision Needed |
|---|---|---|
| P0 | 自动化误触非测试环境外部系统、凭据或防火墙推送 | PRD 中按只读、写测试数据、触发任务、外部推送分级；测试环境内允许必要 apply/触发 |
| P0 | 将 PoC 验收误解为当前任务目标 | PRD 明确“只提取关注方向，不做客户 PoC” |
| P0 | 没有先梳理流程动线就启动真实动作测试 | 先产出 flow line 和关键环境清单，再进入 read-only/dry-run/controlled-action 探针 |
| P0 | 高危薄弱环节被低危 polish 或宽泛 smoke 淹没 | 每个发现必须标注 H0/H1/H2/H3；H0/H1 优先拆修复或审批 story |
| P1 | 覆盖面过大导致故事不可审查 | 每批 3-8 个小故事，优先证据基线 |
| P1 | 现有脚本存在环境耦合，导致自动测试假失败 | 先做可运行性盘点，区分产品缺陷与环境缺口 |
| P1 | UI smoke 替代真实业务证据 | 每个矩阵项要求 API/数据/日志/页面/导出等至少一种可复核证据 |
| P2 | FE/BE 修复 lane 边界与 CT 验证混在一起 | CT 先产出问题和证据，修复批次再分配给 d2-fe/d2-be |

## Batch Plan

| Batch | Goal | Target Lanes | Status | Gate |
|---|---|---|---|---|
| batch-001 | WS-01 flow mapping：设备/监控/日志/拓扑四条流程动线、最终目标、关键环境、H0/H1 薄弱环节假设 | ct | draft | 只做静态梳理和只读证据规划，不执行真实 apply/采集/关闭设备 |
| batch-002 | WS-01 read-only baseline：`ONEOPS_GATE_*` fixture inventory、字段 universe、当前可验证证据现状 | ct | draft | DB 密码外部注入；输出脱敏 inventory；不写产品库、不触发采集 |
| batch-003 | WS-01 dry-run/preflight：Device V2/DC2、monitoring、log-forward、topology 的可运行探针和阻塞分类 | ct | draft | 每个阻塞点标注 H0/H1/H2/H3 和下一步决策 |
| batch-004 | WS-01 controlled action：可恢复采集、监控、日志、拓扑最小动作探针 | ct, d2-fe, d2-be | draft | 进入真实动作前必须有恢复策略和审批边界 |
| batch-005 | WS-01 end-goal proof：四条动线组合证据与门禁结论 | ct, d2-fe, d2-be | draft | 最终目标和中途薄弱环节都要有证据，不只看主路径 PASS |
| batch-006 | WS-02/WS-03 flow mapping 与 H0/H1 风险：Agent/Controller 生命周期、告警触发通知升级动线 | ct | draft | 先梳理安装包、恢复、关闭设备、send log、升级 fixture 等高危点 |
| batch-007 | WS-02/WS-03 read-only/dry-run baseline | ct, d2-fe, d2-be | draft | 先证明环境、策略、设备和审计入口可观测，再执行生命周期或关闭设备 |
| batch-008 | WS-04/WS-05 安全与自动化执行 flow mapping：凭据、远程任务、脚本、定时、真实 LLM | ct, d2-fe, d2-be | draft | H0 优先：明文泄露、误执行变更命令、凭据清理失败、LLM 成本和凭据边界 |
| batch-009 | WS-06 防火墙工单与策略对账 flow mapping/read-only baseline | ct, d2-fe, d2-be | draft | 推送反馈和真实防火墙测试仍延后；先验证导入、解析、预检查、CLI 文本证据 |
| batch-010 | WS-07 证据体系：固定中文摘要、矩阵回写、危害等级排序、readiness 总览和机器可读门禁 JSON | ct | draft | evidence 必须能表达 flow、weak point、harm class、decision |

## Approval Boundaries

- 发布 OpenClaw 故事前需要用户确认 PRD 方向和首批范围。
- 写入 OpenClaw story queue、修改 loop config、启用 loop 或启动 pool 前需要确认。
- 任何真实外部系统调用、凭据读取/写入、防火墙推送、通知发送、迁移、部署、提交/推送都需要明确批准。
