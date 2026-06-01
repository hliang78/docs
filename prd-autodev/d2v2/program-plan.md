---
topic: d2v2
kind: full-stack
title: Device V2 运维入口迁移
createdAt: 2026-05-15T19:08:51+0800
program: true
---

# Program Plan

## Objective

交付 Device V2 清册的单设备运维入口迁移：以显式 V1 桥接为前置条件，复用旧设备监控、WebShell、操作审计能力，并为 Loki 日志保留明确待确认入口。

## Definition Of Done

- Device V2 行级“更多”和详情侧栏均能进入监控、WebShell、操作审计。
- 所有旧能力调用都使用确认后的 `device_v1_code`。
- 未同步或同步失败时，UI 直接暴露后端错误或缺字段列表，不继续打开旧能力。
- 旧 `/#/device/inventory` 行为保持不变。
- 日志入口不实现 Loki 查询，必须显示待确认原因。
- 前后端验证命令和浏览器/接口证据写入 OpenClaw evidence。

## Scope

### In Scope

- Device V2 到 V1 桥接状态/确保契约。
- Device V2 前端运维入口和弹窗/跳转。
- 旧监控、终端、操作审计复用。
- 代码级测试、类型检查、Go 测试、浏览器验证证据。

### Out Of Scope

- GPU 信息迁移。
- 旧带外日志迁移。
- Loki 日志查询实现。
- 依赖升级、数据库迁移、生产配置、认证/租户语义改动。

## Workstreams

| ID | Workstream | Lane | Status | Notes |
|---|---|---|---|---|
| 01 | Frontend Pages And Controls | d2v2 | reviewed | V2 页面入口、状态、旧实现复用 |
| 02 | Backend API Contracts | d2v2 | reviewed | V1 bridge 状态/同步契约 |
| 03 | End-to-End Critical Flows | d2v2 | reviewed | 真实设备路径验证 |
| 04 | Permissions And Error States | d2v2 | reviewed | 不兜底、不静默 |
| 05 | Regression Suite | d2v2 | reviewed | FE typecheck + BE go test + browser evidence |

## Dependency Map

- `D2V2-001` 后端桥接契约是所有旧能力入口前置。
- `D2V2-002` 前端 V1 code gate 依赖 `D2V2-001`。
- `D2V2-003` 监控/WebShell 入口依赖 `D2V2-002`。
- `D2V2-004` 操作审计依赖 `D2V2-002`。
- `D2V2-005` 日志占位依赖 `D2V2-002`。
- `D2V2-006` 验证证据依赖前面所有故事。

## Risk Register

| Severity | Risk | Decision Needed |
|---|---|---|
| P0 | V2 code 被误用于旧审计/终端接口 | 必须通过 V1 code gate |
| P0 | 同步失败后 UI 继续打开旧能力 | 禁止继续，直接暴露错误 |
| P1 | 抽取旧页面代码导致旧页面回归 | 允许改旧代码，但旧行为必须保持 |
| P1 | Loki 日志范围未确认 | 本批只做待确认入口 |

## Batch Plan

| Batch | Goal | Target Lanes | Status | Gate |
|---|---|---|---|---|
| batch-001 | V1 bridge and old-operation entries | d2v2 | reviewed | User requested immediate delegation |

## Approval Boundaries

- Writes outside allowed paths.
- Dependency changes.
- Device-related old frontend/backend code changes are approved by user for this program, provided old behavior remains unchanged.
- Backend contract changes are allowed only for Device V2 bridge/operation scope and must fail loudly on missing facts.
- Production config, migrations, credentials, auth, tenant logic, deploy, commit, push, merge, PR.
