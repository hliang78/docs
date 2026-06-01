---
topic: oneops-poc-concern-autotest
kind: full-stack
title: OneOps PoC 关注方向自动测试闭环
createdAt: 2026-05-14T10:47:34+0800
program: true
---

# Program Question Round 001

## Purpose

在继续深挖代码、形成最终 PRD 和 OpenClaw 批次前，确认“从 PoC 提取关注方向”之后的自动测试目标、边界和证据口径。

## My Current Understanding

- 你关心的不是完成这份客户 PoC，而是用它暴露出来的关注面来反推 OneOps 应该长期自动验证什么。
- 这是一项 full-stack 复杂项目，应该先 PRD 探索，再分批进入 OpenClaw 自动化。
- 第一批更适合做 CT 主导的只读证据基线：现有脚本/页面/API/测试覆盖了什么，哪些领域缺口最大。

## Questions

1. 这套自动测试最终想支持什么决策：上线前质量门禁、演示/交付前自检、长期回归巡检，还是三者都要但分阶段？
2. 第一批你希望优先证明哪一类关注点：设备纳管/监控日志/拓扑，Agent/Controller，告警，凭据审计，自动化脚本，还是防火墙工单？
3. 自动测试的环境边界怎么定：只允许本地/开发环境 fixture，还是可以连接现有 OneOPS/OneOPS-UI 开发服务和测试数据库？
4. 对“通过”的证据你更看重哪种：命令行测试报告、浏览器录屏/截图、API 请求响应、数据库/日志记录、导出文件，还是组合证据？
5. 外部集成边界上，是否默认禁止真实通知、真实 Vault 写入、真实防火墙推送，只允许 mock/只读检查？
6. OpenClaw 首批故事是否按我的建议只发给 `ct` 做盘点和证据基线，等缺口明确后再拆给 `d2-fe`/`d2-be` 修复？

## Answers

- 2026-05-14 round 001:
  - 自动测试最终服务于“上线质量门禁”。
  - 第一批优先关注“设备 / 监控 / 日志 / 拓扑”。
  - 允许连接现有 OneOPS / OneOPS-UI 开发服务和测试数据库。
  - 通过证据采用组合证据：命令行、浏览器、API、数据库/日志、导出物按场景组合。
  - 这是测试环境，不设置默认禁止项；但仍需要在 PRD 中区分只读、写测试数据、触发任务、外部推送等风险等级。
  - 用户希望先继续探索并交互确认具体探索内容，再进入最终 PRD 和 OpenClaw story 发布。
- 2026-05-14 round 002:
  - 第一版拆成 4 个子门禁，不做单一总门禁。
  - 设备门禁关键：基于采集到的证据和平台字段，取最大可验证字段集作为采集、解析、入库成功的依据；不同设备采集到的字段可能存在差异，避免按固定字段全集一刀切。
  - 监控门禁关键：监控任务下发、监控任务治理、Prometheus 可查到监控数据、监控数据标签附着正确。
  - 拓扑门禁关键：改造为利用 Device V2 入库数据和采集方式生成拓扑，前端能展示并下钻。
  - 测试数据策略：长期数据。
  - 拓扑证据：以 obsflow L2 topology snapshot 作为主证据，传统 `/topology` 作为 UI/下钻验证。
  - 日志门禁：允许 log-forward apply；成功标准必须包含从设备触发日志，并能从 Loki 收到正确日志。
- 2026-05-14 round 003:
  - 长期 fixture 命名采用 `ONEOPS_GATE_*`。
  - 设备字段先以 `docs/openclaw-autodev/D2_INGEST_BASE_FIELD_TABLE.md` 为基础，但不要求所有设备满足同一字段全集；具体测试应结合设备实际采集证据和平台字段微调。
  - 监控标签附着标准来自当前“监控策略”的“通用标签附着”策略配置，重点读取其中 `attach_tags` 对不同 metric 的标签要求。
  - syslog 日志通过 SSH 登录已配置 syslog 转发的网络设备，修改/执行配置以触发日志，再验证 Loki 收到正确日志。
  - 服务器日志通过 tail 采集，在目标服务器手动生成日志，再验证 Loki 收到正确日志。
  - 拓扑最小成功阈值：至少 2 个长期网络设备 fixture、1 条边、接口下钻可用。下钻测试可因环境准备延后，但必须纳入门禁。

## Context Brief Update

Answers from this round should update `context-brief.md`, `program-plan.md`, `test-matrix.md`, and then drive `prd.md`.

## Discussion Cadence

- 2026-05-14 round 004:
  - 用户确认后续按 workstream 逐步讨论开放问题。
  - 每轮聚焦一个 workstream，先确认成功标准、测试数据、证据口径、自动化边界和批次位置。
  - 每轮讨论后更新 `prd.md`、对应 `workstreams/*.md`、`test-matrix.md` 和必要的 story package 草案。

## WS-01 Answers

- 2026-05-14 WS-01:
  - `ONEOPS_GATE_*` fixture 从测试数据库获取，并在给到自动化任务前准备好。数据库为 MySQL，host `192.168.0.199`，port `3306`，db `zb_firewall_199`，user `root`，`autoMigrate=true`。密码不写入 PRD 文件，自动化通过环境变量或本机密钥注入。
  - 监控 P0 metric 当前只覆盖网络设备的 `ping`、`snmp`、`snmp_interface`。
  - NVR 当前没有测试设备，暂不考虑。
  - 服务器可能支持 SNMP，但需要准备服务器配置，延后处理。
  - 监控治理 P0 范围为：下发、状态、重试/同步、Prometheus 可查、标签正确。
  - drift/diff/repair 延后，需要准备数据。
  - tail 文件路径为 `/var/log/messages`、`/var/log/syslog`。
  - syslog 触发需要编写工具：通过 SSH/netlink 库进入目标网络设备 config 模式；Cisco 设备执行 `wr` 保存配置；H3C 和 Huawei 执行 `save`。
  - 拓扑下钻允许首批因 fixture interface 未准备而 BLOCKED，但最终 WS-01 Done 必须补齐。

## WS-02 Answers

- 2026-05-14 WS-02:
  - WS-02 上线门禁要验证部署、升级、停止、卸载等生命周期动作，不只验证状态可信。
  - 当前已有可用的测试 Agent / Controller。
  - 允许自动化真实执行：注册、心跳、状态查询、任务下发、重启、停止、卸载。
  - P0 先验证单 Controller/Agent 链路，不先覆盖多区域/多安全域。
  - 任务分发证据必须看到 Agent 侧执行日志或回执，不能只停留在 API 记录。
  - 升级动作使用真实的最新安装包；允许同版本反复安装来验证升级/安装链路。
  - 卸载成功后，自动化必须重新安装 Agent，恢复测试链路。
  - Agent 侧执行日志/回执采用组合证据。

## WS-03 Answers

- 2026-05-14 WS-03:
  - 告警 P0 除触发、生成、呈现外，还要覆盖告警通知策略测试。
  - 责任分级本质是告警长时间未修复，超过时间阈值后升级通告到上一级人员；该升级通告进入门禁设计。
  - 告警抑制、维护窗口、主次告警关联先按 P1 处理。
  - 通知通道 P0 使用 send log 作为证据，不真实发送外部通知。
  - 告警触发源采用真实关闭某些设备来触发告警。

## WS-04 Answers

- 2026-05-14 WS-04:
  - 凭据 P0 覆盖凭据录入/引用、远程任务选择凭据、执行时不暴露明文、凭据可轮换/禁用。
  - 允许自动化真实写入或更新测试 Vault/凭据。
  - 远程任务要真实执行到测试设备/服务器，不只验证参数生成。
  - 审计 P0 覆盖登录、设备操作、Agent 生命周期、告警处理、凭据使用、远程任务执行。
  - 审计证据 API JSON + UI 截图足够，不要求导出文件。

## WS-05 Answers

- 2026-05-14 WS-05:
  - P0 覆盖模板、变量集、定时任务、任务中心执行、脚本试跑、AI 脚本辅助。
  - AI 脚本辅助进入 P0，并使用真实 LLM。
  - 自动化任务要真实执行到测试设备/服务器。
  - 脚本试跑允许只读巡检命令，但脚本类型有多种，门禁需要覆盖多脚本类型。
  - 定时任务允许创建计划，后续通过运行记录验证触发与执行结果。

## WS-06 Answers

- 2026-05-14 WS-06:
  - P0 覆盖工单导入、对象解析、策略预检查、推荐配置生成、策略查询、策略对账。
  - 推送反馈需要测试，但延后。
  - 真实防火墙测试延后。
  - 工单输入 fixture 需要覆盖 Excel/CSV、页面表单、API JSON。
  - 防火墙配置生成的核心证据是生成 CLI 配置文本。

## WS-07 Answers

- 2026-05-14 WS-07:
  - 证据摘要需要固定中文格式，方便日报阅读。
  - 需要生成一页管理层 readiness 总览。
  - 每个 batch 结束后要求自动回写 `test-matrix.md` 状态。
  - 证据文件统一放在 PRD program 下的 `evidence/`。
  - 最终门禁结果需要机器可读 JSON，方便后续自动判断能否上线。

## Batch-001 Confirmation

- 2026-05-14 batch-001:
  - 用户确认首批只做 WS-01 设备字段门禁基线准备，不同时推进监控/日志/拓扑执行。
  - 用户确认 batch-001 允许只读访问测试 DB；DB 密码通过环境变量或本机密钥注入，不写入文档。
  - 用户确认 batch-001 允许写入 PRD program 下的 `evidence/`，并回写 `test-matrix.md` 状态。
