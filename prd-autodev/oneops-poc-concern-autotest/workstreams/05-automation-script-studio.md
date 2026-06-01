# WS-05 自动化工作台与脚本辅助

## Focus

覆盖 PoC TC-16 到 TC-20：模板、变量集、定时任务、AI 脚本辅助、凭证驱动远程任务、沙箱试跑。

## Repository Anchors

- Frontend: `OneOPS-UI/src/views/platform/Task*`, `ScriptTemplateStudio.vue`, `TemplateDebug*`, `ScheduledTaskManagement.vue`, `VariableSetManagement.vue`, `AIOpsWorkbench.vue`.
- Backend: task center, template debug, credential, aiops and job modules.
- Scripts/tests: `task-center-*`, `template_debug_*`, `template-debug-v3-*`.

## Draft Acceptance Shape

- 模板和变量集能驱动任务创建和真实执行。
- 定时任务证据可关联策略与运行记录。
- AI 脚本辅助进入 P0，使用真实 LLM。
- 脚本试跑必须证明日志来自测试环境中的真实测试设备/服务器。
- 脚本执行边界是只读巡检命令，但需要覆盖多种脚本类型。

## Confirmed Planning Decisions

- P0 覆盖模板、变量集、定时任务、任务中心执行、脚本试跑、AI 脚本辅助。
- AI 脚本辅助使用真实 LLM，不使用 mock/disabled-mode 作为 P0 通过证据。
- 自动化任务真实执行到测试设备/服务器。
- 脚本试跑允许只读巡检命令。
- 脚本类型有多种，P0 需要至少覆盖代表性脚本类型，具体类型清单后续按代码/产品能力确认。
- 定时任务允许创建计划，后续通过运行记录验证触发与执行结果。

## Remaining Open Questions

- 需要确认 P0 覆盖哪些脚本类型，以及每类脚本的只读命令白名单。
- 需要确认真实 LLM 的 provider、模型、凭据来源、调用成本和失败降级策略。
- 需要确认测试设备/服务器的任务执行目标和可执行命令集合。
- 需要定义定时任务计划的最短周期、轮询窗口和超时策略。
