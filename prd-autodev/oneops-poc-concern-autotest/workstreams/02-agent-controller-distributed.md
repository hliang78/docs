# WS-02 Agent Controller 与分布式部署

## Focus

覆盖 PoC TC-07、TC-08，以及集中 OneOps + 区域 Controller + 区域 Agent 的分布式执行关注点。

## Repository Anchors

- Frontend: `OneOPS-UI/src/views/platform/AgentManagement.vue`, `AgentDeployment.vue`, `AgentDetail.vue`, `ControllerManagement.vue`.
- Backend: `OneOPS/app/agent`, Platform2 controller/agent scripts.
- Scripts/tests: `platform2_agent_*`, `platform2_controller_*`, `platform2_multi_agent_test`.

## Draft Acceptance Shape

- Agent/Controller 列表、详情、心跳、版本、状态之间一致。
- 部署、升级、停止、卸载等生命周期动作在测试 Agent / Controller 上可真实执行并可回溯。
- 任务分发路径必须有 Agent 侧执行日志或回执，不能只依赖中心 API 记录。

## Confirmed Planning Decisions

- WS-02 上线门禁覆盖生命周期动作：部署、升级、停止、卸载。
- 当前已有可用测试 Agent / Controller，不需要先做 fake fixture。
- P0 允许真实执行：注册、心跳、状态查询、任务下发、重启、停止、卸载。
- P0 范围先验证单 Controller/Agent 链路。
- 多 Controller、多 Agent、多区域/多安全域关系延后到 P1+。
- 任务分发成功必须看到 Agent 侧执行日志或回执。
- 升级动作使用真实的最新安装包；允许同版本反复安装来验证升级/安装链路。
- 卸载成功后，自动化必须重新安装 Agent，恢复测试链路。
- Agent 侧执行日志/回执采用组合证据。

## Remaining Open Questions

- 需要定位最新真实安装包的获取方式、包名/version 识别方式和校验方式。
- 需要定义卸载后重装的超时时间、重试次数和失败恢复策略。
