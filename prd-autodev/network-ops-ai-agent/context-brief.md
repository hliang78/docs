---
topic: network-ops-ai-agent
kind: full-stack
title: 网络运维智能体融入 OneOPS
createdAt: 2026-06-18T11:00:42+0800
program: true
---

# Program Context Brief

## Goal

在 OneOPS 中引入“网络运维智能体”能力：用户用自然语言描述日志告警、设备异常、配置变化或业务影响后，系统能结合 OneOPS 现有设备、拓扑、采集、日志、告警、RCA 和私有知识库，给出可追溯的根因候选、排查步骤和解决方案。

本阶段先完成调研、边界收敛和候选架构，不直接进入实现。

## Scope

- 自然语言一问一答入口：面向网络/安全运维场景。
- 私有知识文档接入：上传、解析、切片、抽取、检索、版本管理。
- RAG 与工具调用：把知识检索、OneOPS 数据查询、RCA 分析、日志检索、配置采集编排为可审计流程。
- RCA 增强：在现有平台无关 RCA 契约和 `rca2`/`rca3` 基础上，补充 LLM 解释、排障步骤生成和证据引用。
- 开源组件选型：重点评估 Dify/RAGFlow/LlamaIndex/Haystack、Milvus/Qdrant/OpenSearch、NetBox/Nautobot/Batfish/Nornir/Netmiko/Scrapli、Prometheus/Loki/OpenTelemetry 等。

## Boundaries

- 不把 LLM 当成根因裁决内核；根因候选仍应来自 OneOPS 的拓扑、告警、日志、采集事实和 RCA 规则/算法。
- 不让智能体直接执行高风险修复动作；MVP 只允许生成建议、只读诊断、受控采集，修复需人工确认。
- 不用第三方平台替换 OneOPS 的设备主数据、拓扑快照、RCA 合约和审计边界。
- 私有知识库必须有租户、来源、版本、权限和召回证据；不能把上传文档“揉进提示词”后失去来源。
- 开源组件以嵌入式/旁路服务/适配器方式引入，避免把 OneOPS 主链路锁死在某个外部产品模型里。

## Priority Focus

推荐优先做 “AI Copilot for RCA and Runbook”：

1. 告警/日志/设备异常问答。
2. 知识库引用式回答。
3. 调用 OneOPS 现有 RCA 和日志/拓扑查询能力。
4. 输出结构化诊断报告：现象、证据、根因候选、排查步骤、建议动作、置信与缺口。

## Background

OneOPS 已有几个关键底座：

- `rca2` 已定义标准化 NodeFact、模式、信号、Profile 和可解释候选输出。
- `rca3` 已定义分层拓扑、AlertBinding、Evidence、IncidentContext、LayerDecisionEngine、CrossLayerReducer 等接口。
- `docs/RCA_PLATFORM_AGNOSTIC_MINIMAL_CONTRACT.md` 明确 RCA 机制应与平台字段解耦，由 OneOPS 负责映射拓扑、告警、日志证据。
- `docs/ONEOPS_DATA_APPLICATION_FOUNDATION_CAPABILITY_MAP_2026-04-10.md` 已提出统一对象、统一时序、统一可信、统一消费底座，这是 AI 运维智能体的基础前提。
- OneOPS README 已包含 Prometheus、Grafana、Loki、rsyslog、Telegraf 网络设备日志推送链路。

## Concerns

- LLM 幻觉：排障建议必须引用证据，且区分“事实、推断、建议、缺口”。
- 知识污染：用户上传文档可能过期、冲突、低质量，需要质量状态和版本边界。
- 权限泄露：知识、设备、日志、告警、拓扑都必须按租户/角色隔离。
- 自动修复风险：自然语言到命令执行需要强审批、沙箱、回滚和审计。
- 组件复杂度：Dify/RAGFlow 这类平台能提速，但也可能引入重复用户体系、工作流模型和运维成本。

## Open Questions

1. MVP 首屏是“告警详情里的 AI 分析按钮”，还是独立“运维智能体”聊天页？
2. 私有知识文档的目标格式优先级是什么：PDF/Word/Markdown/Excel/设备厂商手册/历史工单？
3. 模型部署偏好：公有 API、私有大模型网关，还是本地离线模型？
4. 第一阶段是否允许智能体触发只读采集命令，如 show interface/show log/show ip route？
5. 是否需要对接现有工单/告警闭环，还是先只产出诊断报告？
