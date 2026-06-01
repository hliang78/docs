# WS-03 告警管理闭环

## Focus

覆盖 PoC TC-09 到 TC-13：触发、呈现、通知、分责升级、抑制、维护窗口、恢复闭环。

## Repository Anchors

- Frontend: `OneOPS-UI/src/views/alert`.
- Backend: `OneOPS/app/alert`, `OneOPS/app/alert_engine`.
- Scripts/tests: alert RCA smoke, alert backend tests if present.

## Draft Acceptance Shape

- 真实关闭测试设备后能触发告警。
- 告警能生成、列表/详情呈现，并能保留对象、级别、摘要、时间和当前状态。
- 告警通知策略能被命中，P0 使用 send log 作为通知证据，不真实发送外部通知。
- 告警长时间未修复并超过阈值后，能升级通告到上一级人员。
- 告警抑制、维护窗口、主次告警关联先作为 P1，仍保留在 WS-03 规划内。

## Confirmed Planning Decisions

- P0 触发源是真实关闭某些测试设备，而不是只注入模拟事件。
- P0 覆盖告警生成、列表/详情呈现、通知策略命中、send log 通知证据、超时升级通告。
- 责任分级定义为：告警长时间未修复，超过时间阈值后升级通告到上一级人员。
- P0 通知证据使用 send log，不真实发送短信、邮件、企业微信或 Webhook。
- 告警抑制、维护窗口、主次告警关联先按 P1 处理。

## Remaining Open Questions

- 需要确认用于触发告警的测试设备范围，以及“关闭设备”的执行方式和恢复策略。
- 需要确认 P0 告警策略、通知策略、升级阈值、上一级人员 fixture 是否由测试 DB 预置。
- 需要定义 send log 的查询入口和字段断言。
