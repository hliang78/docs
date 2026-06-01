# WS-06 防火墙工单与策略对账

## Focus

覆盖 PoC TC-21、TC-22：防火墙策略工单、配置解析/对比/生成、推送反馈、策略查询与对账。

## Repository Anchors

- Frontend: `OneOPS-UI/src/views/firewall`.
- Backend: `OneOPS/app/firewall`.
- Scripts/tests: firewall object/precheck/ticket/online collection smoke scripts.

## Draft Acceptance Shape

- Excel/CSV、页面表单、API JSON 都能进入工单链路。
- 工单导入后能完成对象解析、策略预检查、推荐配置生成。
- 推荐配置生成的核心证据是 CLI 配置文本。
- P0 覆盖策略查询和策略对账。
- 推送反馈需要测试，但延后。
- 真实防火墙测试延后。

## Confirmed Planning Decisions

- P0 覆盖工单导入、对象解析、策略预检查、推荐配置生成、策略查询、策略对账。
- 推送反馈延后，不纳入 P0。
- 真实防火墙测试延后，不纳入 P0。
- 工单输入 fixture 覆盖 Excel/CSV、页面表单、API JSON。
- 防火墙配置生成的核心证据是生成 CLI 配置文本。

## Remaining Open Questions

- 需要确认策略查询 P0 覆盖哪些查询类型，例如源/目的命中、端口/协议、重叠、覆盖、取反、冲突检测。
- 需要确认标准防火墙策略 fixture 和导入表/CSV/API JSON 示例。
- 需要定义 CLI 配置文本的校验方式：关键命令断言、diff、语法校验或人工可读快照。
