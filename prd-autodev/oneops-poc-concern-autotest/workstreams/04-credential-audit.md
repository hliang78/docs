# WS-04 操作安全域与审计

## Focus

覆盖 PoC TC-14、TC-15：凭据引用驱动远程任务、操作日志检索与导出审计抽样。

## Repository Anchors

- Frontend: credential unified pages, task/terminal related pages.
- Backend: `OneOPS/app/credential`, `OneOPS/app/device_terminal`, sys log record APIs, task logs.
- Scripts/tests: Vault catalog smoke, credential backend tests, task credential scripts.

## Draft Acceptance Shape

- 远程任务引用凭据，不在 OneOps 保存或显示明文密码。
- 操作日志能按责任主体、时间、业务对象检索。
- 导出材料或 API 响应可作为审计抽样证据。
- 测试环境允许真实写入/更新测试凭据，并用该凭据真实执行远程任务。
- 凭据轮换、禁用后，远程任务行为和审计记录可验证。

## Confirmed Planning Decisions

- P0 覆盖凭据录入/引用、远程任务选择凭据、执行时不暴露明文、凭据可轮换/禁用。
- 允许自动化真实写入或更新测试 Vault/凭据。
- 远程任务必须真实执行到测试设备/服务器。
- 审计 P0 覆盖登录、设备操作、Agent 生命周期、告警处理、凭据使用、远程任务执行。
- 审计证据 API JSON + UI 截图足够，不要求导出文件。

## Remaining Open Questions

- 需要确认测试 Vault/凭据的命名规则、作用范围、轮换值来源和清理/恢复策略。
- 需要确认真实远程任务的安全命令集合，例如只读命令、探测命令或固定脚本。
- 需要定义“不暴露明文”的断言面：API 响应、UI、任务日志、审计日志、Agent 日志。
