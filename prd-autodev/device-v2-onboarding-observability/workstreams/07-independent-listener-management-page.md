---
topic: device-v2-onboarding-observability
kind: full-stack
title: Workstream 07 - Independent Listener Management Page
status: reviewed
---

# Workstream 07: Independent Listener Management Page

## Goal

新增一个平台侧独立页面，用于管理区域 agent 上的 `syslog / snmp trap` 监听服务。该页面不依赖 Device V2 单台 `继续纳管` 流程即可独立执行日常运维操作。

## Scope

- 页面允许用户选择 FunctionArea 与 agent。
- 页面允许用户管理以下首期服务类型：
  - `服务器 syslog 监听`
  - `网络设备 syslog 监听`
  - `snmp trap 监听`
- 页面支持 `dry-run / preflight / apply / remove` 类操作。
- 页面在实现上包装复用现有 `remote_syslog` / `log_forward_plan` 模型与发布过程。

## Non-Goals

- 不在本 workstream 内引入新的底层发布链路。
- 不在本 workstream 内把 `服务器 syslog 监听` 与 `网络设备 syslog 监听` 拆成两套后端投递模型。
- 不在本 workstream 内实现设备侧完整 SNMP trap target 远程下发。

## Current Real Code Facts

- 现有 [LogForwardPlanManagement.vue](/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/views/platform/LogForwardPlanManagement.vue) 已能管理 `local_file / remote_syslog`。
- 现有后端 `PrepareRemote / BuildRemote` 已能围绕 `collector_agent_code` 生成 collector 侧 syslog listener 发布上下文。
- 现有 controller plugin mapping 已包含 `inputs.snmp_trap`。
- 当前 [AreaListenerServiceManagement.vue](/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/views/platform/AreaListenerServiceManagement.vue) 已经有顶部三枚“新建”按钮和三张概览卡片的 `新增` 入口，这些入口都会打开带 preset 的创建弹窗。
- 当前页面的保存链路本质上仍是创建/更新 `plan_type=remote_syslog` 的 `log_forward_plan` 包装；产品上还不能据此直接视为“区域 listener 功能已完成”。
- 当前页面已经暴露 release modal 和 `dry-run / preflight / apply / remove / pause / resume` 按钮，但 `snmp_trap_listener` 依旧明确返回 adapter gap，`server/network syslog` 也还缺少 owner 认可的“真实下发已完成”证据。

## Current Product Gaps

- 从 owner 的实际使用视角看，页面右上角的三枚“新建”按钮和卡片里的 `新增` 不应只停留在“能打开弹窗”；它们需要通向完整可用的创建、保存、列表刷新、编辑、发布操作闭环。
- `server_syslog_listener` / `network_syslog_listener` 需要拿到真实 collector-side 下发与状态回写，而不是只停在包装后的 plan 保存或弱语义占位。
- `snmp_trap_listener` 不能长期停在“诚实暴露 adapter gap”这一半成品状态；如果页面把它作为一级入口展示，就需要补齐 collector-side trap listener 发布适配，至少把区域 listener 管理做完整。
- 在这些功能闭环和真实下发没有完成前，不应把下一轮优先级继续放在 managed-listener runtime/blocker 修复上。

## Proposed Direction

- 新页面以“区域日志接入服务管理”而不是“日志转发计划”命名。
- 页面层将 `syslog` 显式拆成 `服务器` 与 `网络设备` 两种表单语义。
- 后端首期不新建独立投递模型，而是在页面保存/发布阶段映射到现有 `log_forward_plan` 能力。
- `snmp trap` 本轮明确只作为 listener 管理入口收纳，必要的模板缺口继续诚实暴露。

## Acceptance

- 独立页面入口与 Device V2 onboarding 页面语义分离。
- 用户能明确选择 agent 和 listener service type。
- `服务器 syslog 监听` 与 `网络设备 syslog 监听` 在页面上有不同默认值/说明。
- 发布链路复用现有 `remote_syslog` / `log_forward_plan`，而不是重造一套实现。
- `snmp trap` 首期只落在 listener 管理范围内。

## Story Handoff

- `D2ON-029A`: 收口 area listener service contract。
- `D2ON-029B`: 落独立 listener management page。
- `D2ON-029C`: 把单设备 onboarding syslog listener 读取接到新 contract。
- `D2ON-030`: 等上述链条完成后再恢复 exact rerun。
- 新 owner 方向：先补 listener 页功能闭环与真实下发，再决定是否重新打开 onboarding managed-listener runtime/blocker 修复轮次。
