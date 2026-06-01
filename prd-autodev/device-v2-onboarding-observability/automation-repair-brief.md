---
topic: device-v2-onboarding-observability
kind: full-stack
title: Device V2 onboarding automation repair brief
status: active
updatedAt: 2026-05-17T00:00:00+0800
---

# Automation Repair Brief

## Goal

给 `gpt-5.4-mini` worker 一个足够窄、足够明确的修复上下文，避免把“已有文档/已有按钮/已有测试”误判成“新的 onboarding 闭环已经打通”。

## What Is Actually Broken

1. 前端 `继续纳管` 还在走旧的 store 流水线，不是新的 onboarding API。
2. onboarding drawer 读取的是 store task/run/observation，不是 `summary_json.onboarding.actions`。
3. `EnsureOnboarding` 直接使用空的 `DefaultOnboardingConfig()`；默认 `AreaSyslogServices` 为空，所以真实调用会先在配置校验处失败。
4. `EnsureOnboarding` 仍写入硬编码成功 evidence，这会制造“假成功”。
5. 当前实现会创建合成 run，而不是把 onboarding action 合并回真实最新 `DeviceV2StoreRun`。
6. 文档和 evidence 收尾未完成，不能支撑“第一轮已完成”的结论。

## Non-Negotiable Rules For The Next Worker Turn

- 不允许继续把旧 store 流水线包装成新的 onboarding 完成态。
- 不允许继续写硬编码 success / dispatch_result=success 作为占位。
- 不允许在没有真实配置来源、真实执行结果或明确 blocked evidence 的情况下宣称 done。
- 如果真实业务契约暂时无法安全接通，必须返回明确 blocked/failed evidence，而不是伪造 success。
- 每个 story 结束时要对照 acceptance 逐条自检；缺任一条就应该 `BLOCKED` 或 `CONTINUE`，不能 `DONE`。

## Concrete File Anchors

- Backend route shell: `OneOPS/app/device/v2/api/device_v2_onboarding_api.go`
- Backend action types/helpers: `OneOPS/app/device/v2/model/device_v2_onboarding_action.go`
- Backend config helpers: `OneOPS/app/device/v2/model/device_v2_onboarding_helpers.go`
- Frontend redesign page: `OneOPS-UI/src/views/device/DeviceV2ManagementRedesign.vue`
- PRD contract: `docs/prd-autodev/device-v2-onboarding-observability/prd.md`
- Dev API doc: `docs/development/device-v2-onboarding-observability/06-接口文档-OneOPS_DeviceV2纳管观测_v0.1.md`

## Definition Of Progress

- 用户点击 `继续纳管` 后，调用的是 onboarding API，不是 store start/retry。
- 前端看到的是 onboarding action evidence，不是 store observation 的替代视图。
- 后端要么真实读到 onboarding config 并执行受限 contract，要么明确报出 config/blocker；不能继续空配置 + 假成功。
- 当前批次的 evidence、review、readiness 文档必须改成具体结论，不再是 `TBD`。
