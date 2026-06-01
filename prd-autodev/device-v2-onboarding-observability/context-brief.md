---
topic: device-v2-onboarding-observability
kind: full-stack
title: Device V2 极简纳管设计
createdAt: 2026-05-15T20:57:53+0800
status: draft
---

# Context Brief

## 用户原始问题

采集验证其实是采集入库。入库后需要进入监控纳管和日志纳管。网络设备监控以下发监控任务成功为准；网络设备日志通过远程登录设备配置 syslog 或 SNMP trap target 到区域 agent。服务器监控支持 agent 或 SNMP；服务器日志支持 agent 日志转发或 SSH 配置日志转发。远程访问不稳定、延迟大、设备命令差异大，因此希望方案极简，不使用一堆状态控制。

## 分类

full-stack program：前端单台继续纳管入口、后端 action evidence、监控任务复用、区域基础服务配置、远程 ensure 模板、系统日志策略。

## 已确认目标

- “继续纳管”首期只对单台设备执行。
- 历史首期纳管成功以配置成功为主，不强制 Prometheus/Loki 数据到达；2026-05-18 新 scope 升级后，闭环必须继续验证 Prometheus/Loki 数据可查询。
- 不做复杂状态机，使用 ensure action result 记录证据。
- 网络设备日志首期优先 syslog；SNMP trap 保留一级定义和模板缺口。
- 网络设备远程配置成功后自动保存。
- 服务器监控方式由用户选择 agent / SNMP。
- 服务器日志有 agent 时优先 agent；无 agent 时生成 SSH 配置计划。
- FunctionArea 区域基础服务先放配置文件。
- 新 scope：指标必须在 Prometheus 查询出来；服务器本地日志、服务器 syslog 日志、网络设备 syslog 日志、网络设备 SNMP trap 日志必须在 Loki 查询出来。
- 新 scope live 端点：Prometheus `http://192.168.0.164:9090`，Loki `http://192.168.0.164:3100`。

## 新增场景已确认

- 需要一个独立的 `syslog / snmp trap` 管理页面，主语义是管理区域 agent 上的监听服务，而不是以设备侧 target 下发为主入口。
- 页面允许选择 agent，并对监听服务做 dry-run / preflight / apply 类操作。
- `syslog` 需要在页面层面明确区分两类表单语义：
  - `服务器 syslog 监听`
  - `网络设备 syslog 监听`
- 两类 syslog 首期差异主要体现在表单和默认值，不要求在这一轮引入不同的后端配置模型。
- 新页面可以包装复用现有 `remote_syslog` / `log_forward_plan` 模型与发布链路，不要求重造下发过程。
- 历史 listener 管理轮只做 listener 管理；后续 batch-012 已完成首个 H3C/Comware trap target 配置/回读，新 scope 继续验证 trap 日志是否进入 Loki。

## 边界

- 不发布 OpenClaw stories，除非用户确认 batch。
- 首期不做批量并发远程配置。
- 首期不新增 onboarding DAG 或独立状态表。
- 历史首期不实现完整 SNMP trap 下发；后续 batch-012 已完成首个 H3C/Comware trap target 配置/回读，新 scope 继续验证 trap 日志是否进入 Loki。

## 核心设计假设

- `device_v2_store_run.summary_json` 可作为极简 onboarding evidence 根对象。
- 监控任务 agent 权威来源沿用 FunctionArea + 能力开关现有机制。
- syslog listener 可复用现有下发流程。
- 设备差异进入模板，不进入流程。
- 再次点击“继续纳管”只重试 `failed` / `unknown` action。

## 仍需后续确认

- 区域基础服务配置文件最终路径和 schema。
- 网络设备各厂商 syslog inspect/apply/save/verify 命令模板。
- 服务器 SNMP 开启模板。
- 服务器 SSH 日志转发模板。
- SNMP trap teleabs 模板。
