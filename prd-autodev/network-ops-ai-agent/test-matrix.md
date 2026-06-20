---
topic: network-ops-ai-agent
kind: full-stack
title: 网络运维智能体融入 OneOPS
createdAt: 2026-06-18T11:00:42+0800
program: true
---

# Test Matrix

| Area | Surface/API | Scenario | Role/Data | Expected | Evidence | Lane | Priority | Status |
|---|---|---|---|---|---|---|---|---|
| AI 入口 | 告警详情页 | 用户点击 AI 分析当前告警 | 运维用户、单条 active alert | 生成结构化诊断报告，不执行修复 | 页面截图、API 响应、报告 JSON | d2-fe,d2-be | P0 | draft |
| RCA 适配 | `rca3` analyze facade | 告警、拓扑、日志证据装配为 RCA 请求 | topology snapshot、alert、log evidence | 输出候选根因及 reasons/evidence | 单元测试、fixture、样例报告 | d2-be | P0 | draft |
| 知识库 | 文档上传与召回 | 上传厂商手册或 SOP 后问答引用片段 | PDF/Markdown/Word 样例 | 回答包含来源、版本、片段引用 | 召回日志、引用清单 | d2-be | P0 | draft |
| 可观测 | Loki/Prometheus adapter | 按告警时间窗拉取日志/指标摘要 | device_code、interface、time window | 转换为 `Evidence`，标记 source/confidence | adapter 测试、样例 Evidence JSON | d2-be | P1 | draft |
| 安全 | 权限与审计 | 不同租户/角色访问知识和诊断 | 两租户文档、设备、告警 | 不越权召回或展示 | 权限测试、审计记录 | ct,d2-be | P0 | draft |
| 质量 | 幻觉与缺证据控制 | 缺少拓扑或日志证据时请求分析 | incomplete evidence | 报告明确缺口，不编造根因 | 评测样例、人工检查表 | ct | P0 | draft |
