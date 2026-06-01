---
topic: oneops-poc-concern-autotest
kind: full-stack
title: OneOps PoC 关注方向自动测试闭环
createdAt: 2026-05-14T10:47:34+0800
program: true
---

# Test Matrix

本矩阵是能力域索引，不是直接可发布的 story 清单。执行时必须先使用 `exploration-driven-test-method.md` 把每个能力域拆成流程动线、最终目标、关键环境、薄弱环节假设和危害等级。

## Exploration Lens

| Area | Flow Line | Final Goal | Critical Environments | Priority Weak Points | Harm Focus |
|---|---|---|---|---|---|
| 设备子门禁 | fixture inventory -> Device V2 record -> DC2 target resolution -> collect/facts -> store readiness -> field manifest -> UI/API evidence | 每台 `ONEOPS_GATE_*` 设备按自身最大可验证字段集证明采集、解析、入库正确 | 测试 DB、Device V2 API、DC2 resolver、facts/fact issues、D2 base field table、浏览器证据 | fixture 缺字段、target resolution 错误、字段一刀切、fact issue 被忽略、store readiness 与实际不一致 | H1，若误连非测试对象则 H0 |
| 监控子门禁 | fixture device -> monitoring strategy/template -> task delivery/governance -> Prometheus sample -> label assertion -> UI/API evidence | 网络设备 `ping`/`snmp`/`snmp_interface` 任务可治理，Prometheus 有样本且标签正确 | Teleabs strategy、monitoring task API、Agent/collector、Prometheus、`attach_tags`、浏览器页面 | 任务未下发、重试/同步状态不可见、PromQL 无样本、标签与 fixture 不匹配、策略来源漂移 | H1 |
| 日志子门禁 | fixture source -> log-forward plan -> dry-run/preflight/apply -> syslog/tail trigger -> Loki query -> label/content assertion | log-forward apply 后真实触发日志，Loki 可查到内容和标签都正确的记录 | Log-forward API、Grok/Tail source、网络设备 save 命令、服务器日志路径、Loki、SSH/netlink 工具 | apply 成功但无日志、触发文本不确定、tail 权限不足、Loki label 缺失、误触非测试设备 | H1，误触非测试设备为 H0 |
| 拓扑子门禁 | fixture devices/interfaces -> DC2 topology facts -> obsflow L2 snapshot -> topology API -> frontend graph -> drill-down evidence | 至少 2 节点/1 边可生成、展示并下钻到设备/接口证据 | DC2 topology facts、obsflow、topology API、前端拓扑页面、fixture interface/neighbor 数据 | 无稳定 L2 edge、snapshot 与 API 不一致、前端图展示但无法下钻、接口 fixture 缺失 | H1 |
| Agent 部署运维 | install/register -> heartbeat/status -> task dispatch -> lifecycle action -> uninstall/reinstall recovery -> audit evidence | 单 Agent/Controller 链路生命周期动作真实可执行、可恢复、可回溯 | Agent 包、Controller API、Agent 主机、任务回执、Agent 日志、审计入口 | 最新包不可定位、卸载后无法恢复、心跳状态漂移、任务回执缺失、生命周期审计缺失 | H0/H1 |
| 告警触发通知 | controlled device abnormal -> alert creation -> list/detail -> notification policy -> send log -> escalation/recovery | 真实设备异常能触发告警、命中通知策略、超过阈值升级并可恢复 | 测试设备、alert engine、策略 fixture、send log、恢复动作、告警页面/API | 关闭设备不可恢复、策略 fixture 缺失、send log 不可查、升级阈值不可控、恢复闭环缺证据 | H0/H1 |
| 凭据引用远程任务 | test credential create -> credential reference -> remote task -> rotate/disable -> audit/no-plaintext checks | 测试凭据可被任务引用，轮换/禁用有效，任何证据面不暴露明文 | Vault/credential API、测试设备/服务器、任务中心、审计日志、Agent 日志、UI/API 响应 | 明文泄露、凭据污染、禁用后仍可用、清理失败、任务误用生产目标 | H0 |
| 自动化模板巡检 | template/variable set -> task render -> task dispatch -> readonly execution -> logs/evidence -> schedule polling | 模板、变量、定时和脚本试跑能真实执行只读巡检并产生日志证据 | Template API、task center、scheduler、测试设备/服务器、只读命令白名单、LLM provider | 脚本误触变更命令、目标不受控、调度假成功、LLM 凭据/成本边界不清、执行日志不可复核 | H0/H1 |
| 防火墙工单 | Excel/CSV/form/API input -> object parse -> precheck -> CLI recommendation -> policy query/reconciliation | 工单可导入、对象解析正确、预检查有结果、生成可校验 CLI 配置文本 | fixture 文件、policy objects、precheck API、CLI generator、query/reconciliation API、UI | 对象解析错误、预检查漏报、CLI 文本无法校验、真实推送边界不清、策略对账类型不足 | H1，真实推送误触为 H0 |
| 证据体系 | story evidence -> batch summary/status JSON -> matrix update -> readiness summary -> final gate JSON | 每批证据能支撑下一批决策和最终上线门禁判断 | PRD evidence 目录、status vocabulary、matrix update、readiness threshold、automation sync | 只记录日志不产决策、危害等级缺失、matrix 不回写、机器状态不可判定、readiness 口径摇摆 | H1/H2 |

## Capability Matrix

| Area | Surface/API | Scenario | Role/Data | Expected | Evidence | Lane | Priority | Status |
|---|---|---|---|---|---|---|---|---|
| 设备子门禁 | `OneOPS-UI/src/views/device`, `OneOPS/app/device/v2`, `OneOPS/app/device_collection2` | 基于每台 `ONEOPS_GATE_*` 设备的采集证据和平台字段，形成最大可验证字段集，并验证采集、解析、入库正确 | 测试 DB 中预置的 `ONEOPS_GATE_*` 长期设备、DC2 采集策略、D2 base field table、实际采集证据 | 每台设备的最大可验证字段集正确入库；不同设备允许字段差异；不适用/无证据/环境缺失字段有 reason；无阻断 fact issues | API 响应 + DB fixture inventory + DC2 run/facts + per-device verifiable field manifest + 后端测试 + 浏览器截图 | ct, d2-fe, d2-be | P0 | draft |
| 监控子门禁 | Platform monitoring pages/API, Teleabs strategy, Prometheus | 网络设备 `ping`/`snmp`/`snmp_interface` 监控任务下发、治理并产生带正确标签的 Prometheus 数据 | `ONEOPS_GATE_*` 网络设备、监控任务、Prometheus、通用标签附着 `attach_tags` | 下发、状态、重试/同步正确；Prometheus 返回样本；标签匹配实时策略 `attach_tags` 和 fixture 元数据 | 任务 API + Teleabs strategy params + PromQL 结果 + 脚本摘要 + 浏览器截图 | ct | P0 | draft |
| 日志子门禁 | 日志转发计划、日志源、Loki/log API | log-forward apply 后分别通过网络设备 save/syslog 和服务器 tail 触发日志并在 Loki 查询到 | `ONEOPS_GATE_*` 网络设备、`ONEOPS_GATE_*` tail 服务器、`/var/log/messages`、`/var/log/syslog`、Loki | apply 成功；Cisco `wr` 或 H3C/Huawei `save` 触发 syslog；tail 路径写入测试日志；Loki 返回包含预期内容和标签的日志 | `log_forward_*` 脚本 + SSH/netlink 触发记录 + 服务器日志生成记录 + Loki query + 浏览器截图 | ct | P0 | draft |
| 集中看板 | `dashboard/Monitor`, Grafana/monitor APIs | 监控看板按设备/对象过滤查看指标 | 已有指标 fixture | 看板或 API 返回指标详情，不出现空白误判 | 浏览器截图 + API 响应 | ct, d2-fe | P1 | draft |
| 拓扑子门禁 | `src/api/topology`, `OneOPS/app/topology`, `OneOPS/app/obsflow`, DC2 topology facts | Device V2 + 采集链路生成 obsflow L2 snapshot，再由前端展示和下钻 | 2+ `ONEOPS_GATE_*` 网络设备、1+ L2 edge、接口/邻居采集 | L2 snapshot 为主证据；传统/改造 topology 前端可展示 2 节点/1 边并下钻设备/接口；下钻可延后但必须补齐 | L2 workflow/snapshot + `/topology` API + UI截图 + Go test + drill-down evidence | ct, d2-fe, d2-be | P0 | draft |
| Agent 部署运维 | Platform Agent/Controller pages, `OneOPS/app/agent`, Platform2 scripts | 单 Controller/Agent 链路上验证注册、心跳、状态、任务下发、重启、停止、卸载、部署/升级/重装恢复 | 可用测试 Agent / Controller、真实最新安装包 | 中心侧列表/详情/心跳/版本/状态一致；生命周期动作可回溯；卸载后可用真实包重新安装恢复；任务分发有 Agent 侧组合证据 | Platform2 smoke + API response + Agent 侧日志/API/任务回执 + UI截图 | ct | P0 | draft |
| 告警触发通知 | `src/views/alert`, `OneOPS/app/alert`, `alert_engine` | 真实关闭测试设备触发告警，列表/详情呈现，通知策略命中并记录 send log | 测试设备、fixture 告警策略、通知策略、send log | 告警包含对象、级别、概要、时间、状态；通知策略命中；send log 可复核通知内容 | 设备关闭/恢复记录 + alert API + send log + UI截图 | ct, d2-fe, d2-be | P0 | draft |
| 分责升级 | alert strategy/group/receiver APIs | 告警长时间未修复，超过时间阈值后升级通告到上一级人员 | fixture escalation policy、上一级人员 fixture、send log | 状态流转、升级阈值、上级接收方、升级通告内容符合策略 | API/state transition evidence + send log + UI截图 | ct, d2-be | P0 | draft |
| 告警抑制/维护/恢复 | inhibit/maintain/alarm APIs | 主次告警抑制、维护窗口免通知、恢复闭环 | fixture alarms/windows | 列表可读，通知受控，恢复后闭环 | API 响应 + send log + UI截图 | ct, d2-fe, d2-be | P1 | draft |
| 凭据引用远程任务 | Credential/Vault APIs, task/terminal pages | 真实写入测试凭据，完成录入/引用/轮换/禁用，并用凭据真实执行远程任务 | 测试 Vault/凭据、测试设备/服务器、远程任务 | 任务选择凭据引用；执行成功；API/UI/日志/审计不暴露明文；轮换/禁用后行为正确 | Credential API JSON + task evidence + 明文泄露断言 + UI截图 | ct, d2-fe, d2-be | P0 | draft |
| 操作日志审计 | `sys/log_record`, terminal/ssh records, task logs | 检索登录、设备操作、Agent 生命周期、告警处理、凭据使用、远程任务执行审计记录 | fixture operation logs / real gate actions | 审计记录包含责任主体、时间、业务对象、动作、结果；API JSON + UI 截图足够 | API JSON + UI截图 | ct, d2-be | P0 | draft |
| 自动化模板巡检 | Task template/variable set/task center | 模板和变量集生成巡检任务，并真实执行到测试设备/服务器 | template fixture、variable set、测试设备/服务器 | 任务生成、参数渲染、任务中心执行成功；输出覆盖只读巡检项 | task-center API + task logs + 设备/服务器执行日志 + UI截图 | ct, d2-fe, d2-be | P0 | draft |
| 定时任务 | scheduled task APIs/pages | 创建测试计划，后续轮询运行记录验证触发与执行结果 | short window schedule fixture | 触发时间与策略一致；运行记录可关联模板/变量/目标/执行结果 | API polling + run record + UI截图 | ct | P0 | draft |
| AI 脚本辅助 | AIOps/script studio, LLM provider | 使用真实 LLM 由业务描述生成脚本草稿，并进入审核/试跑路径 | real LLM provider、测试提示词、脚本草稿 | 草稿结构可读；可被审核与试跑引用；保留 LLM 调用摘要或审计记录 | LLM call summary + UI/API evidence + script draft | ct, d2-fe | P0 | draft |
| 沙箱脚本试跑 | script/task center/credential APIs | 多脚本类型草稿在测试设备/服务器执行只读巡检命令并产生日志 | 测试设备/服务器、只读命令白名单、多脚本类型 fixture | 试跑日志真实可查；只执行只读巡检命令；不误触变更类操作 | task logs + 设备/服务器执行日志 + credential reference evidence + UI截图 | ct, d2-be | P0 | draft |
| 防火墙工单 | firewall ticket/precheck/policy generation APIs | Excel/CSV、页面表单、API JSON 工单导入后完成对象解析、策略预检查、推荐配置生成 | fixture Excel/CSV/API JSON/policy objects | 工单可导入；对象解析正确；预检查有结果；生成 CLI 配置文本；推送反馈和真实防火墙测试延后 | firewall API/UI + precheck report + CLI config text + UI截图 | ct, d2-fe, d2-be | P0 | draft |
| 策略查询对账 | policy query/validation APIs | 策略查询和策略对账 | fixture policy set | 返回策略命中和对账摘要；具体查询类型待确认 | API JSON + UI截图 | ct, d2-fe, d2-be | P0 | draft |
| 证据体系 | PRD program `evidence/`, matrix updates, readiness report | 每批故事结束后生成固定中文摘要、机器可读状态、回写矩阵，并形成 readiness 总览 | batch evidence | `PASS/FAIL/BLOCKED/APPROVAL/SKIPPED` 清晰；日报可读；机器可判定上线状态 | `evidence/batch-###-summary.md` + `evidence/batch-###-status.json` + `evidence/readiness-summary.md` + `evidence/final-gate-result.json` + `test-matrix.md` 回写 | ct | P0 | draft |
