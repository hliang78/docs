---
topic: d2v2
kind: full-stack
title: Device V2 运维入口迁移
createdAt: 2026-05-15T19:08:51+0800
program: true
---

# Program Question Round 001

## Purpose

Enrich the rough program input before planning, workstreams, or story batches.

## Questions

1. What is the top-level outcome or release/readiness decision this program should support?
2. Which modules, pages, APIs, roles, environments, or data sets are definitely in scope?
3. Which areas are explicitly out of scope for now?
4. What are the highest-risk flows or failures you are worried about?
5. What evidence should each batch produce before the next batch starts?
6. Which lanes should participate first: frontend, backend, CT, or full-stack?
7. What approval boundaries must automation respect?

## Answers

- Top-level outcome: Device V2 清册单台设备具备可用的运维入口：监控、WebShell、操作审计；Loki 日志只预留入口和契约说明，后续确认类型后再开发。
- In scope: `/#/device/device-v2-management-redesign`，旧设备详情页 `/#/device/inventory` 的监控、终端、安全审计能力，Device V2 到 Device V1 同步桥接，前端与后端实现和验证。
- Out of scope: GPU 信息、旧带外日志迁移、Loki 查询实现、生产配置/迁移/依赖升级、改变旧设备 V1 行为。
- Highest risks: V2 code 和 V1 code 混用导致旧能力查不到数据；同步缺字段时静默成功；前端用兜底字段误导用户；旧页面行为被重构破坏。
- Evidence: 每个故事必须写 `docs/openclaw-autodev/evidence/d2v2/<story-id>/summary.md`，包含修改范围、验证命令、失败问题或真实页面/接口证据。
- Lanes: 新建单任务 `d2v2` 承载 FE+BE，故事用依赖链顺序执行，避免前端先猜后端契约。
- Approval boundaries: 用户已授权修改旧前后端设备相关代码且无需另行授权，但不得改变旧行为；仍禁止删除文件、依赖升级、生产配置、迁移、提交/推送。

## Context Brief

### Goal

让 Device V2 清册围绕单台设备具备旧设备页同等运维入口，同时代码结构保持“V2 只做桥接，功能调用旧实现”的边界。

### Scope

- 后端：确认或补齐 Device V2 到 Device V1 的桥接状态/同步契约，确保缺字段直接暴露错误。
- 前端：在 Device V2 清册行级“更多”和详情侧栏中增加监控、WebShell、操作审计、日志入口。
- 验证：以真实 V1 code 驱动旧监控/终端/审计能力，不使用 mock、兜底、静默空数据。

### Boundaries

- 不迁移 GPU。
- 不迁移旧“带外日志”。
- Loki 日志仅预留入口和阻塞说明，不实现查询。
- 不改变 `Inventory.vue` 既有用户路径行为。

### Priority Focus

先建 V1 code gate，再接旧监控/WebShell/操作审计，最后验证与证据。

### Concerns

- V2 设备未同步到 V1 时，旧能力不可用，必须明确提示同步失败原因。
- 旧页面代码可能需要抽取复用，抽取必须保持旧页面视觉和行为不变。
- 后端如果缺必要字段，必须返回明确错误，不能前端智能推断。

### Open Questions

- Loki 日志类型、label、时间范围、查询权限和展示方式待后续沟通。
