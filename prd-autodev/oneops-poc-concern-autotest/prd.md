---
topic: oneops-poc-concern-autotest
kind: full-stack
title: OneOps PoC 关注方向自动测试闭环
createdAt: 2026-05-14T10:47:34+0800
program: true
status: convergence-draft
---

# OneOps PoC 关注方向自动测试闭环 PRD

## 0. 当前状态

这是完整 PRD 规划的收敛草案，不是最终稿，也不是只针对“设备/监控/日志/拓扑”的局部 PRD。

当前工作方式：

- 先完成全局规划框架：目标、范围、分域、阶段、证据、自动化边界。
- 再按 workstream 多轮深入探索：每轮先梳理流程动线，再围绕最终目标和中途关键环境设计探针，补齐成功标准、证据链、风险和故事边界。
- 最后在用户确认后，只发布第一批小规模 OpenClaw 自动化故事；后续批次根据证据和反馈滚动推进。

## 1. 背景与目标

源 PoC 文档只用于提取 OneOps 平台关注方向，不用于执行上海移动研究院 PoC，也不用于形成客户验收结论。

本 PRD 的目标是把 PoC 暴露出的关注面，规划成 OneOps 长期可运行的“上线质量门禁 + 自动测试 + 证据回写”体系。它服务于上线前判断、演示/交付前自检、长期回归巡检，但第一优先级是上线质量门禁。

## 2. 产品原则

- 关注方向来自 PoC，但验收口径服务 OneOps 自身质量，而不是复刻 22 个 PoC 用例。
- 门禁必须可复核：不能只有 UI smoke 或脚本成功码，要能看到 API、数据、日志、截图、Prometheus/Loki 查询等组合证据。
- 自动化必须可持续：长期 fixture、稳定命名、批次化故事、证据回写和失败原因分类都要进入 PRD。
- 大任务必须分域推进：全局 PRD 先完整，局部工作流逐步深入，不一次性发布所有自动化任务。
- 探索必须沿流程动线推进：先梳理入口、关键步骤、数据落点、下游消费和最终目标，再测试最终目标和中途薄弱环节。
- 薄弱环节必须按危害程度分类：H0/H1 优先挖掘和修复，H2/H3 记录但不能抢占主路径。
- 测试环境允许必要的 apply、触发、写入和查询，但 PRD 仍要区分只读、写测试数据、触发任务、外部推送等风险等级。

### 2.1 探索驱动测试协议

本 PRD 的执行协议见 `exploration-driven-test-method.md`。后续 workstream、test matrix 和 OpenClaw story 都必须遵循该协议。

每个目标方向必须产出：

- 流程动线：入口动作、中间步骤、关键状态、数据落点、下游展示或消费。
- 最终目标：这条动线最终要证明什么业务结果。
- 中途关键环境：DB、API、服务、Agent、设备、凭据、策略、脚本、Prometheus/Loki、外部系统等。
- 薄弱环节假设：哪些点最可能导致门禁误判、主路径失败、证据缺失、安全风险或恢复失败。
- 危害等级：按 H0 Critical、H1 High、H2 Medium、H3 Low 分类。
- 探针层级：static、read-only、dry-run、controlled-action、end-goal-proof。
- 下一步决策：继续测试、补 fixture、拆修复 story、请求审批或延后。

探索 story 不能只写“验证某能力”。它必须只回答一个核心问题，并明确停止条件和 evidence contract。

## 3. 范围

### 3.1 In Scope

- 从 PoC 提取 OneOps 平台关注方向。
- 形成完整 full-stack PRD、测试矩阵、workstream 拆分和批次计划。
- 设计长期 fixture 和证据标准。
- 利用 `prd-autodev-loop` 进行多轮探索、确认和 PRD 收敛。
- 用户确认后，再利用 `openclaw-autodev` 发布小批次自动测试/修复故事。

### 3.2 Out Of Scope

- 执行客户 PoC。
- 把自动测试结果包装成客户验收结论。
- 未确认前启动 OpenClaw loop、写入 story queue 或发布批量任务。
- 未确认前进行真实生产环境推送、通知发送、防火墙变更、部署或迁移。

## 4. 全局能力域

| Workstream | 关注域 | 规划目标 |
|---|---|---|
| WS-01 | 设备、监控、日志、拓扑 | 建立对象、采集、可观测数据和拓扑关系的质量门禁基础 |
| WS-02 | Agent / Controller 分布式部署 | 验证分区部署、健康、版本、生命周期和任务分发是否可追踪 |
| WS-03 | 告警管理闭环 | 验证触发、通知、升级、抑制、维护窗口和恢复闭环 |
| WS-04 | 凭据与审计 | 验证凭据引用、远程任务安全边界、操作日志检索和导出 |
| WS-05 | 自动化工作台与脚本辅助 | 验证模板、变量集、定时、AI 脚本辅助和沙箱试跑 |
| WS-06 | 防火墙工单与策略对账 | 验证工单导入、预检查、配置生成、推送反馈和策略查询对账 |
| WS-07 | 跨域证据与回归体系 | 统一矩阵、批次、证据、状态和下一批决策 |

## 5. 阶段规划

### Phase 0: PRD 探索与对齐

目标：形成完整规划，而不是只完成一个局部。

产物：

- `poc-concern-extraction.md`
- `program-plan.md`
- `test-matrix.md`
- `exploration-driven-test-method.md`
- `workstreams/*.md`
- `prd.md`
- `story-packages/batch-001.json` 草案

退出条件：

- 用户确认全局 workstream 切分合理。
- 用户确认第一阶段优先级和门禁定义。
- 用户确认探索驱动测试协议，包括流程动线、关键环境、薄弱环节和危害等级。
- 用户确认第一批 OpenClaw 故事范围。

### Phase 1: 上线质量门禁基础

优先领域：WS-01。

原因：设备对象、采集数据、日志、监控和拓扑是后续告警、自动化、防火墙、安全审计的事实基础。

已确认的 WS-01 子门禁：

- 设备：基于采集证据与平台字段形成最大可验证字段集，验证采集、解析、入库正确，避免对不同设备一刀切。
- 监控：任务下发、任务治理、Prometheus 可查、标签附着正确。
- 日志：log-forward 可 apply，syslog/tail 可真实触发，Loki 可查。
- 拓扑：Device V2 + 采集链路生成 obsflow L2 snapshot，传统 `/topology` 完成 UI/下钻验证。

### Phase 2: 分布式执行与事件闭环

优先领域：WS-02、WS-03。

目标：

- Agent / Controller 状态可信，且测试链路上的生命周期动作可执行、可恢复、可回溯。
- 告警从真实设备异常进入触发、通知策略、超时升级、恢复闭环。
- 告警抑制、维护窗口、主次告警关联保留在规划内，但首批作为 P1。
- 不以页面可达替代业务证据。

### Phase 3: 安全、审计与自动化执行

优先领域：WS-04、WS-05。

目标：

- 凭据录入、引用、轮换、禁用和远程任务使用链路可验证，不暴露明文。
- 操作日志可按人、时间、对象检索和导出。
- 巡检模板、变量集、定时任务、脚本试跑和 AI 脚本辅助可形成真实执行证据。

### Phase 4: 防火墙工单与策略对账

优先领域：WS-06。

目标：

- 工单输入、对象解析、策略预检查、推荐配置生成、策略查询和策略对账形成闭环。
- 推送反馈和真实防火墙测试保留在规划内，但 P0 延后。

### Phase 5: 持续回归体系

优先领域：WS-07。

目标：

- 每批 OpenClaw 任务完成后自动留下证据摘要。
- `test-matrix.md` 状态可被回写。
- DONE / BLOCKED / APPROVAL 能直接支撑下一批规划。
- 证据摘要面向日报阅读，使用固定中文格式。
- 输出管理层 readiness 总览和机器可读 JSON，支持后续自动判断能否上线。

## 6. WS-01 已深入确认内容

### 6.1 长期 fixture

- 长期测试数据命名采用 `ONEOPS_GATE_*`。
- 设备字段基线先以 `docs/openclaw-autodev/D2_INGEST_BASE_FIELD_TABLE.md` 为基础，但成功判断以“采集到的证据 + 平台字段”形成的最大可验证字段集为准。不同设备可采集字段可能不同，不按固定字段全集一刀切。
- fixture 来源是测试 MySQL 数据库 `192.168.0.199:3306/zb_firewall_199`，user `root`，`autoMigrate=true`。数据库密码不写入 PRD 或 story，后续自动化通过环境变量或本机密钥注入。
- `ONEOPS_GATE_*` fixture 必须在发布 OpenClaw 自动化任务前准备好。

### 6.2 设备子门禁

成功标准：

- 每台 `ONEOPS_GATE_*` 设备都生成自己的最大可验证字段集，来源包括平台字段、采集证据、DC2 facts 和设备类型能力。
- 对每台设备，该最大可验证字段集内的字段必须完成采集、解析、入库并可被 Device V2 API / DC2 facts 证明正确。
- 不同设备之间允许字段集合不同。
- 不适用于某类设备、未被设备能力支持、未采集到证据或环境缺失的字段要记录 reason，不能被当作失败，也不能静默消失。

证据：

- Device V2 API。
- DC2 collect/standardize/process run。
- facts/latest facts/fact issues。
- Device V2 UI 截图。

### 6.3 监控子门禁

成功标准：

- 监控任务可下发。
- 任务治理状态可见。
- Prometheus 可查到监控数据。
- 指标标签符合当前“监控策略 / 通用标签附着”的 `attach_tags` 定义。
- P0 metric 仅覆盖当前网络设备：`ping`、`snmp`、`snmp_interface`。
- NVR 指标当前没有测试设备，暂不纳入。
- 服务器 SNMP 需要准备服务器配置，延后纳入。
- P0 治理范围是下发、状态、重试/同步、Prometheus 可查、标签正确。
- drift/diff/repair 需要准备数据，延后纳入。

证据：

- Monitoring task API。
- Teleabs strategy 或 strategy-set 参数。
- PromQL 查询结果。
- label assertion 结果。
- UI 截图。

### 6.4 日志子门禁

成功标准：

- log-forward 可以 apply。
- syslog 路径：编写 SSH/netlink 工具，登录已配置 syslog 转发的目标网络设备并进入 config 模式；Cisco 执行 `wr` 保存配置，H3C 和 Huawei 执行 `save`，以触发确定性 syslog；Loki 收到正确日志。
- tail 路径：在目标服务器 `/var/log/messages`、`/var/log/syslog` 生成确定性日志，tail 采集后 Loki 收到正确日志。

证据：

- plan create/bind/dry-run/preflight/apply。
- syslog 触发记录。
- tail 日志生成记录。
- Loki 查询结果。
- UI 截图。

### 6.5 拓扑子门禁

成功标准：

- 至少 2 个 `ONEOPS_GATE_*` 网络设备 fixture。
- 至少 1 条 L2 edge。
- obsflow L2 topology snapshot 作为主证据。
- 传统 `/topology` 作为 UI/展示/下钻验证。
- 接口下钻首批可因 fixture interface 未准备标记为 `BLOCKED`，但必须纳入最终 WS-01 Done。

证据：

- DC2 interface/neighbor facts。
- obsflow L2 workflow/snapshot。
- `/topology` API。
- 拓扑 UI 和下钻截图。

## 7. WS-02 已深入确认内容

### 7.1 范围与测试对象

- 当前已有可用测试 Agent / Controller。
- P0 先验证单 Controller/Agent 链路。
- 多 Controller、多 Agent、多区域/多安全域关系延后。

### 7.2 生命周期门禁

WS-02 不是只读状态门禁。上线门禁要覆盖以下真实动作：

- 注册。
- 心跳。
- 状态查询。
- 任务下发。
- 重启。
- 停止。
- 卸载。
- 部署和升级链路。

升级/安装要求：

- 使用真实的最新安装包。
- 允许同版本反复安装，以验证安装/升级链路。
- 卸载成功后，自动化必须重新安装 Agent，恢复测试链路。

### 7.3 成功标准

- 中心侧 Agent / Controller 列表、详情、心跳、版本、状态一致。
- 生命周期动作在测试 Agent / Controller 上真实执行，且结果可回溯。
- 任务下发成功必须看到 Agent 侧执行日志或回执。
- 停止、卸载等破坏性动作必须有恢复策略，避免影响后续门禁。
- 卸载后的恢复动作也是门禁的一部分：重新安装后 Agent 必须重新注册、恢复心跳，并能再次接收任务。

### 7.4 证据

- 中心 API 记录：Agent / Controller 列表、详情、状态、版本、心跳、任务状态。
- Agent 侧组合证据：本地日志、Agent API、任务回执表或可等价证明执行结果的记录。
- 生命周期动作执行记录。
- UI 截图：Agent/Controller 列表、详情、任务分发或执行状态。

## 8. WS-03 已深入确认内容

### 8.1 触发源

- P0 使用真实关闭某些测试设备来触发告警。
- 触发动作必须包含恢复策略，避免设备长期离线影响后续门禁。

### 8.2 P0 门禁范围

P0 覆盖：

- 告警触发。
- 告警生成。
- 列表/详情呈现。
- 告警通知策略命中。
- send log 通知证据。
- 告警长时间未修复，超过时间阈值后升级通告到上一级人员。

### 8.3 P1 范围

以下能力保留在 WS-03，但不作为首批 P0：

- 告警抑制。
- 维护窗口。
- 主次告警关联。

### 8.4 通知边界

- P0 不真实发送短信、邮件、企业微信或 Webhook。
- P0 使用 send log 证明通知策略命中和通知内容正确。

### 8.5 证据

- 设备关闭/恢复动作记录。
- 告警 API：列表、详情、状态、级别、对象、摘要、时间。
- 通知策略匹配记录。
- send log 记录。
- 超时升级阈值和升级通告记录。
- UI 截图：告警列表、详情、通知或升级记录。

## 9. WS-04 已深入确认内容

### 9.1 P0 门禁范围

P0 覆盖：

- 凭据录入。
- 凭据引用。
- 远程任务选择凭据。
- 远程任务真实执行到测试设备/服务器。
- 执行时不暴露明文。
- 凭据轮换。
- 凭据禁用。

### 9.2 写入边界

- 测试环境允许自动化真实写入或更新测试 Vault/凭据。
- 写入对象必须是测试凭据，不能复用生产凭据。
- 后续 story 必须声明测试凭据命名规则、作用范围和清理/恢复策略。

### 9.3 审计范围

P0 审计对象：

- 登录。
- 设备操作。
- Agent 生命周期。
- 告警处理。
- 凭据使用。
- 远程任务执行。

### 9.4 证据

- 凭据 API JSON：创建、引用、轮换、禁用状态。
- 远程任务 API JSON：任务参数、凭据引用、执行结果。
- 明文泄露断言：API 响应、UI、任务日志、审计日志、Agent 日志中不得出现测试凭据明文。
- 审计 API JSON：责任主体、时间、业务对象、动作、结果。
- UI 截图：凭据页面、远程任务页面、审计页面。
- 不要求 CSV/XLSX 导出作为 P0 证据。

## 10. WS-05 已深入确认内容

### 10.1 P0 门禁范围

P0 覆盖：

- 模板。
- 变量集。
- 定时任务。
- 任务中心执行。
- 脚本试跑。
- AI 脚本辅助。

### 10.2 执行边界

- 自动化任务要真实执行到测试设备/服务器。
- 脚本试跑允许只读巡检命令。
- 脚本类型有多种，P0 需要覆盖代表性脚本类型，具体类型清单后续按产品能力确认。

### 10.3 AI 脚本辅助

- AI 脚本辅助进入 P0。
- P0 使用真实 LLM，不使用 mock/disabled-mode 作为通过证据。
- 后续 story 必须声明真实 LLM 的 provider、模型、凭据来源、调用成本边界和失败降级策略。

### 10.4 定时任务

- P0 允许创建计划。
- 后续通过运行记录验证计划触发和执行结果。
- story 需要声明最短周期、轮询窗口和超时策略。

### 10.5 证据

- 模板和变量集 API JSON。
- 任务中心执行记录。
- 测试设备/服务器上的真实执行日志。
- 脚本试跑输入、输出和状态。
- 真实 LLM 请求/响应摘要或可审计记录，避免记录敏感凭据。
- 定时任务计划和运行记录。
- UI 截图：模板、变量集、任务中心、脚本试跑、AI 脚本辅助、定时任务。

## 11. WS-06 已深入确认内容

### 11.1 P0 门禁范围

P0 覆盖：

- 工单导入。
- 对象解析。
- 策略预检查。
- 推荐配置生成。
- 策略查询。
- 策略对账。

### 11.2 延后范围

- 推送反馈需要测试，但延后。
- 真实防火墙测试延后。

### 11.3 输入 fixture

工单输入 fixture 需要覆盖：

- Excel/CSV。
- 页面表单。
- API JSON。

### 11.4 配置生成证据

- 防火墙推荐配置生成的核心证据是 CLI 配置文本。
- 后续 story 需要定义 CLI 配置文本的校验方式：关键命令断言、diff、语法校验或人工可读快照。

### 11.5 证据

- 工单导入 API/UI 证据。
- 对象解析结果。
- 预检查报告。
- CLI 配置文本。
- 策略查询 API JSON。
- 策略对账结果。
- UI 截图：工单、对象解析、预检查、配置生成、策略查询/对账。

## 12. WS-07 已深入确认内容

### 12.1 证据存放位置

- 证据文件统一放在 PRD program 下的 `evidence/`。
- 不默认同步到 `docs/openclaw-autodev/evidence`，除非后续 OpenClaw 执行机制需要引用。

### 12.2 证据摘要

- 每批证据摘要使用固定中文格式，方便日报阅读。
- 每批结束后生成 `evidence/batch-###-summary.md`。
- 每批结束后生成机器可读状态 `evidence/batch-###-status.json`。

### 12.3 Readiness 总览

- 需要生成一页管理层 readiness 总览。
- 建议路径：`evidence/readiness-summary.md`。
- 总览内容至少包括总通过率、P0 阻塞项、环境缺口、需要人工审批项和下一批建议。

### 12.4 矩阵回写

- 每个 batch 结束后要求自动回写 `test-matrix.md` 状态。
- 状态词汇：`PASS`、`FAIL`、`BLOCKED`、`APPROVAL`、`SKIPPED`。

### 12.5 机器可读门禁结果

- 最终门禁结果需要机器可读 JSON。
- 建议路径：`evidence/final-gate-result.json`。
- 该 JSON 用于后续自动判断能否上线。

## 13. 全局证据规范

每个门禁项至少要声明：

- 目标能力域。
- 测试数据/fixture。
- API 或脚本入口。
- 预期结果。
- 证据文件路径。
- 失败分类：产品缺陷、环境缺口、测试脚本缺口、数据准备缺口、需要人工审批。

证据类型包括：

- CLI/script output。
- API request/response。
- DB 或业务记录 ID。
- Prometheus/Loki 查询结果。
- Browser screenshot/console/network 状态。
- Go/npm/backend test output。
- 手工触发记录。
- 固定中文批次摘要。
- 机器可读状态 JSON。

## 14. 批次规划草案

| Batch | 目标 | Lane | 状态 |
|---|---|---|---|
| batch-001 | WS-01 flow mapping：设备/监控/日志/拓扑四条流程动线、最终目标、关键环境、H0/H1 薄弱环节假设 | ct | draft |
| batch-002 | WS-01 read-only baseline：`ONEOPS_GATE_*` fixture inventory、字段 universe、当前证据现状 | ct | draft |
| batch-003 | WS-01 dry-run/preflight：Device V2/DC2、monitoring、log-forward、topology 的可运行探针和阻塞分类 | ct | draft |
| batch-004 | WS-01 controlled action：可恢复采集、监控、日志、拓扑最小动作探针 | ct, d2-fe, d2-be | planning |
| batch-005 | WS-01 end-goal proof：四条动线组合证据、薄弱环节清单和门禁结论 | ct, d2-fe, d2-be | planning |
| batch-006 | WS-02/WS-03 flow mapping：Agent/Controller 生命周期和告警触发通知升级动线 | ct | planning |
| batch-007 | WS-02/WS-03 baseline/dry-run：安装包、恢复、关闭设备、send log、升级 fixture 等关键环境 | ct, d2-fe, d2-be | planning |
| batch-008 | WS-04/WS-05 安全与自动化执行 flow mapping：凭据、远程任务、脚本、定时、真实 LLM | ct, d2-fe, d2-be | planning |
| batch-009 | WS-06 防火墙工单与策略对账 flow mapping/read-only baseline | ct, d2-fe, d2-be | planning |
| batch-010 | WS-07 证据体系：固定中文摘要、矩阵回写、危害等级排序、readiness 总览和机器可读门禁 JSON | ct | planning |

## 15. 收敛后的未决项分层

### 15.1 执行前必须确认

这些问题会直接影响首批 OpenClaw story 是否能安全运行。

| Area | Must Confirm Before Execution |
|---|---|
| WS-01 | 从测试数据库查询并列出实际 `ONEOPS_GATE_*` 设备、服务器、tenant、IP、厂商和型号。 |
| WS-01 | 明确浏览器证据使用既有开发服务，还是由自动化本地启动前后端服务。 |
| WS-02 | 定位真实最新 Agent 安装包的获取方式、包名/version 识别方式和校验方式。 |
| WS-02 | 定义卸载后重装的超时时间、重试次数和失败恢复策略。 |
| WS-05 | 确认真实 LLM 的 provider、模型、凭据来源、调用成本和失败降级策略。 |
| WS-07 | 定义 `final-gate-result.json` schema 和 readiness 阈值，避免后续“能否上线”判定口径摇摆。 |

### 15.2 Story 内可探索

这些问题可以作为首批或后续 story 的交付内容，不阻塞 PRD 继续收敛。每个探索项必须声明所属流程动线、关键环境、薄弱环节假设、危害等级、探针层级和停止条件。

| Area | Exploratory Story Output | Default Harm Focus |
|---|---|---|
| WS-01 | D2 base field table 到真实 fixture 字段的 expectation manifest。 | H1: 字段门禁误判或主路径证据缺失 |
| WS-01 | Cisco `wr`、H3C/Huawei `save` 触发后的 syslog 文本模式。 | H1: 日志触发成功但 Loki 证据不可复核 |
| WS-01 | tail 测试日志文本模式，以及 `/var/log/messages`、`/var/log/syslog` 写入权限或 helper 方案。 | H1: tail 源无法稳定产生可查日志 |
| WS-03 | 真实关闭设备触发告警的设备范围、执行方式和恢复策略。 | H0: 设备无法恢复或误影响非测试对象 |
| WS-03 | P0 告警策略、通知策略、升级阈值、上一级人员 fixture 是否已在测试 DB 预置。 | H1: 告警策略缺失导致闭环无法判定 |
| WS-03 | send log 查询入口、字段断言和证据文件格式。 | H1: 通知是否命中无法复核 |
| WS-04 | 测试 Vault/凭据命名规则、作用范围、轮换值来源和清理/恢复策略。 | H0: 凭据泄露、污染或无法清理 |
| WS-04 | 真实远程任务安全命令集合。 | H0: 误执行变更类命令或命中非测试目标 |
| WS-04 | “不暴露明文”的断言面：API 响应、UI、任务日志、审计日志、Agent 日志。 | H0: 明文凭据泄露 |
| WS-05 | P0 覆盖哪些脚本类型，以及每类脚本的只读命令白名单。 | H0: 脚本试跑误触变更动作 |
| WS-05 | 测试设备/服务器的任务执行目标和可执行命令集合。 | H1: 任务执行证据不可复现 |
| WS-05 | 定时任务计划的最短周期、轮询窗口和超时策略。 | H2: 调度结果不稳定或假失败 |
| WS-06 | 策略查询 P0 覆盖哪些查询类型。 | H1: 策略对账结论不足以支撑门禁 |
| WS-06 | 标准防火墙策略 fixture 和导入表/CSV/API JSON 示例。 | H1: 工单导入/解析证据不稳定 |
| WS-06 | CLI 配置文本的校验方式。 | H1: 推荐配置生成错误但无法判定 |
| WS-07 | 固定中文摘要模板字段。 | H2: 证据可读性和决策字段不足 |

### 15.3 P1 或后续延后

这些范围已经进入全局规划，但不作为第一阶段 P0。

| Area | Deferred Scope |
|---|---|
| WS-01 | NVR 指标、服务器 SNMP、监控 drift/diff/repair。 |
| WS-01 | 拓扑接口下钻可在 fixture interface 准备前临时 `BLOCKED`，但最终 WS-01 Done 必须补齐。 |
| WS-02 | 多 Controller、多 Agent、多区域/多安全域关系。 |
| WS-03 | 告警抑制、维护窗口、主次告警关联。 |
| WS-06 | 推送反馈、真实防火墙测试。 |

## 16. OpenClaw 交付边界

在用户确认最终 PRD 和第一批 story 前：

- 不发布 OpenClaw story。
- 不启动 loop。
- 不修改 loop config。
- 不触发真实外部推送。

确认后按小批次推进，每批通常 3 到 8 个故事，并在批次结束后回写证据和下一批建议。
