# PRD Program Plan

## Objective

用最少新增机制，让 Device V2 设备能够从采集入库进入“监控纳管 / 日志纳管”的可重试闭环。历史首期不做大编排，不新增复杂状态表，并以配置成功为成功标准；2026-05-18 scope 升级后，新的闭环必须继续验证 Prometheus/Loki 数据面可查询。

## Definition Of Done

- 高质量完成优先于形式完成：只有当真实任务目标、验收证据、以及 truthful monitor/log 结果都达到要求时，PRD 才把该轮 `d2on` 视为真正完成；仅仅 story `DONE` 不足以通过。
- 前端提供单台 `继续纳管` 入口，并区分监控纳管、日志纳管。
- 后端能为单台设备生成 onboarding action list。
- 后端能执行 `failed` / `unknown` / new ensure action，并跳过已成功 action。
- action evidence 写入 `device_v2_store_run.summary_json.onboarding`。
- 网络设备 syslog target 远程配置成功后自动保存。
- 服务器监控支持用户选择 agent / SNMP。
- FunctionArea 基础服务和系统日志策略首期由配置文件承载。
- 平台侧存在独立的区域 `syslog / snmp trap` 管理页，可选择 agent 并管理 listener 服务。
- scope 升级：指标能从 Prometheus 查询出来。
- scope 升级：服务器本地日志、服务器 syslog 日志、网络设备 syslog 日志、网络设备 SNMP trap 日志能从 Loki 查询出来。

## Scope

### In Scope

- Device V2 管理页单台 `继续纳管` 设计。
- `summary_json.onboarding.actions` evidence contract。
- 监控纳管复用现有监控任务下发机制。
- 网络设备 syslog listener 检查与 syslog target ensure 设计。
- 服务器 agent/SNMP 监控选择设计。
- 服务器系统日志 `first_existing` 策略设计。
- 配置文件 schema 草案。
- 独立的区域 `syslog / snmp trap` listener 管理页设计与实现拆分。
- 基于现有 `remote_syslog` / `log_forward_plan` 发布链路的包装复用方案。
- 新 scope：显式 `codes[]` 的批量 onboarding plan/ensure。
- 新 scope 前置门禁：所有当前 Device V2 设备先执行一次显式 code 清单的 `device_collection2` 采集验证入库，逐设备记录 success/blocked，已知不通设备不作为全局失败。
- 新 scope：device-side SNMP trap target 下发、保存、回读验证，首期以 H3C/Comware 为目标模板。
- 新 scope：observed-data validation。Prometheus live endpoint `http://192.168.0.164:9090`；Loki live endpoint `http://192.168.0.164:3100`。
- 新 scope：把 `metric_observed`、`server_local_log_observed`、`server_syslog_observed`、`network_syslog_observed`、`snmp_trap_observed` 写入 onboarding evidence，区分 success/pending/blocked/failed。

### Out Of Scope

- 批量并发远程配置。
- 告警触发、告警入库和 RCA 验证。
- 所有日志源一次性全量覆盖；新 scope 先以 bounded probes 证明每类数据面查询链路。
- 新增独立 onboarding DAG。
- 完整审批流。
- 为 server/network syslog 建两套不同后端投递模型。

## Current Fact Summary

- 前端已有“采集验证”“真实采集”“日志”等入口，但语义未收敛为纳管。
- `DeviceV2StoreRun` 已有 `summary_json`，可以作为极简 evidence 容器。
- `SyncToV1` 已有 Device V2 -> Device V1 桥接和监控推送代码路径。
- 监控任务 agent 权威来源已有 FunctionArea + 能力开关机制。
- syslog listener 已有下发流程，SNMP trap 需要 teleabs 模板。
- attach 标签随监控任务下发，首期不重做标签体系。
- `OneOPS-UI/src/views/platform/LogForwardPlanManagement.vue` 与 `OneOPS/app/platform/api/log_forward_*` 已经具备 `remote_syslog` 的 dry-run / preflight / apply 能力，可作为新页面的发布复用基础。
- `oneops_test_tool` 已提供 Prometheus/Loki 查询 API，后续数据面验证统一通过 `GET|POST /api/v1/observability/*` 记录 evidence。

## Current Assessment

- `d2on` 第一轮已产出 discovery 工具、action/evidence 类型和局部 UI/API 壳，但没有真正完成新的单设备 onboarding 闭环。
- 当前前端 `继续纳管` 仍绑定旧的 `store` 流水线，而不是新的 `/device/v2/:code/onboarding/*` 路由。
- 当前后端 onboarding API 仍存在“假闭环”风险：`EnsureOnboarding` 直接使用空的默认配置、写入硬编码成功 evidence，并创建合成 run，而不是在真实最新 run 上合并结果。
- 第二轮已完成“去除假闭环并切到新 onboarding API”，但它同时暴露出一个明确剩余 gap：`DeviceV2ManagementRedesign` 仍缺真实 browser/devtools 验证或明确 blocker 归档。
- `batch-003` 的浏览器验证已经完成，read-only redesign evidence 已闭环；新的核心 gap 不再是 Chrome 条件，而是 `EnsureOnboarding` 真实执行路径仍然过于乐观。
- 当前后端 `EnsureOnboarding` 仍默认合成 syslog success action，并未把 monitor/log 两类 ensure 的真实非成功状态诚实写回 evidence；前端 execute 路径也仍偏向成功 toast 语义。这个 gap 已足够构成下一轮持续开发，而不是继续停在 closure 等待。
- 复盘结论：像 `D2ON-009` 这种“单次浏览器点验或 blocker 记录”不应继续复制成新的 PRD 微批次；但当 live UI 验证完成后，如果代码事实暴露新的产品 contract gap，应立即切换到下一轮 reviewed batch 继续开发。
- 最新 cycle brief 与 final-readiness/review 仍表明：浏览器/devtools gap 已经关闭，当前剩余工作属于 execution-side honest execute-path follow-up，而不是新的浏览器/环境修复轮次。业务 owner 已明确要求 `d2on` 与 `d2on-prd` 互相驱动、持续运行，因此这一轮直接把 execute-path follow-up 提升为新的 reviewed execution batch，而不是继续停在“等待更多证据”的静态口径。
- 2026-05-17T15:40+08:00: no new PRD batch was created in that re-check, and the planner stayed resident while the remaining gap was still execution-side evidence.
- 2026-05-17T15:47+08:00: batch-007 remained the active continuation round in that re-check because the remaining gap was still execution-side truthful single-device monitor/log evidence.
- 2026-05-17T15:52+08:00: another planner re-check still stayed resident because the remaining gap was execution-side truthful single-device monitor/log evidence, not a fresh PRD boundary.
- 2026-05-17T16:xx+08:00: owner-directed correction: passive waiting is no longer acceptable when `d2on` has no open execution stories. Draft and publish `batch-007` so `d2on-prd` actively drives `d2on` back into a real single-device execute path instead of looping on the same wait conclusion.
- 2026-05-17T16:14+08:00: `batch-007` did resume execution, but `D2ON-020/021/022` were still formally closed on doc-only outputs instead of real controller-backed code/evidence progress. The next batch must therefore encode machine-checkable evidence markers and forbid doc-only `DONE`.
- 2026-05-17T16:17+08:00: the latest cycle brief still shows the program in `automation-linked-awaiting-final-readiness`, and the current planner decision is to keep the resident loop open rather than draft another PRD boundary.
- 2026-05-17T18:10+08:00: `D2ON-024` and `D2ON-025` turned the closure question into an exact live product verdict: `POST /onboarding/ensure` returned `onboarding config source is required` with `data=null`, while the same single-device flow still exposed the controller-backed tuple `controller_stage=rules`, `store_run_status=blocked`, `core_store_status=blocked`, `manageable_status=unready`.
- 2026-05-17T18:12+08:00: that evidence justifies one true next PRD batch rather than another tiny validation gate. `batch-008` closes as a high-quality-complete truth gate with an exact blocker, and reviewed `batch-009` becomes the active resident repair round.
- 2026-05-17T19:19+08:00: `D2ON-027` repaired the top-level `ensure` envelope drift and preserved the exact blocked actions inside a normal onboarding payload, but the same rerun still returned `log_forward` → `onboarding config source is required`.
- 2026-05-17T19:37+08:00: because the owner wants the resident topic to continue and the remaining gap is still a true product-path repair, reviewed `batch-010` becomes the next bounded PRD batch instead of another passive keep-open note or a tiny closure-stage validation.
- 2026-05-17T20:32+08:00: owner-directed scope correction after `D2ON-029`: the old `config_source_required` blocker is gone, but the live path is now honestly blocked on missing runtime syslog listener contract. Insert a narrow syslog listener contract/page/wiring chain before resuming `D2ON-030`; do not open `batch-011`.
- 2026-05-17T22:xx+08:00: owner redirected the next round again after reviewing the independent listener page visually: do not prioritize worker/blocker repair yet. Treat the current area-listener page as functionally incomplete until all highlighted create-entry flows are truly usable and the page can perform real collector-side config publish/apply instead of wrapper-only behavior or adapter-gap honesty. Only after that functional completion should the program return to the managed-listener runtime/blocker thread.
- 2026-05-18: `D2ON-032` through `D2ON-035` closed the independent area listener page round: quick-create/CRUD works, server/network syslog listener publish has real collector-side evidence, SNMP trap listener publish has real collector-side evidence, and a browser/devtools pass captured live listener rows.
- 2026-05-18: `D2ON-039` and `D2ON-040` closed the device-side syslog delivery gap for both server and H3C/Comware network probes through controller remote runs; the old runtime syslog placeholder blocker is no longer the current truth.
- 2026-05-18: `D2ON-041` closed the redesigned Device V2 server monitor-mode selection path. The page now requires Agent/SNMP choice for server onboarding and sends `device_type` plus `monitor_mode` to backend `plan` and `ensure`.
- Current closure state: the bounded single-device onboarding observability scope is closed-success.
- 2026-05-18 new scope opened by owner request: extend beyond the closed single-device scope into (1) explicit batch onboarding and (2) device-side SNMP trap target delivery. This is not a reopening of batch-011; it started as `batch-012` and is now closed by `D2ON-048`.
- 2026-05-18 owner added a hard prerequisite before trap target delivery: run collection validation/store for all current devices first, because some devices are known to be unreachable. Live task `entv2_1779094092855556000` finished `partial`: 17 total, 11 success/ready, 6 blocked/unready, 0 failed. This gates the next SNMP trap target stories.
- 2026-05-18: `D2ON-043` through `D2ON-048` closed `batch-012`. The backend and frontend now support explicit-code batch plan/ensure, the all-device collection gate is durably recorded, and the H3C/Comware `snmp_trap_target` action resolves the managed `snmp_trap_listener`, executes through controller `/api/v1/remote/run`, saves config, verifies readback, and persists separate trap evidence from syslog evidence.
- Current new-scope closure state: `batch-012` is closed-success for the bounded batch onboarding and first device-side SNMP trap target scope. No broad fleet run, all-vendor SNMP trap support, or trap-packet arrival assertion is claimed.
- 2026-05-18: owner upgraded scope again. The next closure target is no longer only configuration/readback; metrics must be queryable in Prometheus, and server local logs, server syslog logs, network syslog logs, and network SNMP trap logs must be queryable in Loki.
- 2026-05-18: `D2ON-049` prepared reusable Prometheus/Loki query APIs in `oneops_test_tool` and verified `Prometheus up` returns `hit_count=1`; Loki range query reaches the endpoint but current `{__name=~"tail|syslog|snmp_trap"}` returns `hit_count=0`, which is an exact no-samples fact for the next batch rather than a transport failure.

## Workstreams

| ID | Workstream | Lane | Status | Notes |
|---|---|---|---|---|
| 01 | Frontend Continue Onboarding | d2-fe | completed | 单台按钮、模式选择、两类纳管摘要、action evidence |
| 02 | Onboarding Evidence Contract | d2-be | completed | `summary_json.onboarding.actions` 读写、摘要推导 |
| 03 | Monitoring Ensure | d2-be/platform3 | completed | 服务器 agent/SNMP 选择已在 redesign page 与 backend plan contract 验证 |
| 04 | Log Ensure And Config | d2-be/platform3 | completed | 区域 listener + server/network syslog device-side delivery 已有 live evidence |
| 05 | Remote Template Minimal Set | platform3 | completed | H3C/Comware syslog inspect/apply/save/verify 已验证；SNMP trap listener publish 已闭；H3C/Comware device-side trap target profile 已补齐 |
| 06 | Regression Evidence | ct | draft | 单台 UI/API、失败重试、配置文件校验 |
| 07 | Independent Listener Management Page | d2-fe/d2-be | completed | 独立 syslog/snmp trap 管理页；包装复用 remote_syslog/log_forward_plan |
| 08 | Listener Functional Completion And Real Publish | d2on | completed | 区域 listener 页完整功能与真实 collector-side 下发已闭环 |
| 09 | Batch Onboarding | d2on | completed | 显式 codes[] 批量 plan/ensure、顺序执行、逐设备 evidence、前端批量结果；全设备采集验证门禁和 bounded live probe 已完成 |
| 10 | Device-Side SNMP Trap Target | d2on/platform3 | completed | 已基于 managed `snmp_trap_listener` 完成 H3C/Comware trap target 下发、保存、回读验证；syslog 与 trap evidence 分开记录 |
| 11 | Observed Data Validation | d2on/platform3 | in-progress | Prometheus 指标查询、Loki 服务器本地日志/服务器 syslog/网络 syslog/SNMP trap 查询；从 `D2ON-049` 工具能力开始 |

## Minimal Flow

```text
Device V2 row
  -> 继续纳管
  -> choose server monitoring mode if needed
  -> build action list
  -> skip success actions
  -> execute new/failed/unknown ensure actions
  -> save summary_json.onboarding
  -> render monitoring/log summaries
```

## Risk Register

| Severity | Risk | Decision |
|---|---|---|
| P0 | 远程设备配置半成功或保存失败 | action result 允许 `unknown`；再次点击只重试 failed/unknown |
| P0 | 厂商命令差异导致误配置 | 差异进入模板，流程只执行 ensure contract |
| P1 | 区域 syslog/snmp_trap 服务定义不稳定 | 首期配置文件，后续再升级为一级模型 |
| P1 | 服务器日志文件跨系统差异 | `first_existing` 策略，不存在不报错 |
| P1 | SNMP trap 还没有模板 | 首期只记录缺口，不阻塞 syslog |
| P0 | 批量 onboarding 远程配置扩大 blast radius | 首期只接受显式 codes[]，默认顺序执行，并保留逐设备结果 |
| P0 | 设备事实过期或部分设备不通导致 trap 下发误判 | trap target 下发前先跑全设备采集验证入库；不通设备记录为逐设备 blocked/manual_pending |
| P0 | SNMP trap target 命令差异导致误配置 | 首期只实现 H3C/Comware，未知厂商 exact blocker |
| P0 | 配置成功但 Prometheus/Loki 无样本 | 新 scope 必须把 no_samples/pending、query_failed、label_mismatch、collector_unready 分开记录，不把配置成功等同于数据面成功 |

## Batch Plan

| Batch | Goal | Target Lanes | Status | Gate |
|---|---|---|---|---|
| batch-001 | 固化极简纳管 contract 和配置 schema | d2-fe,d2-be,platform3 | completed-with-gaps | 已执行，但存在假闭环和证据缺口 |
| batch-002 | 去除假闭环并切到新 onboarding API | d2on | completed | 已执行完成，并补齐了第二轮主要代码/evidence 缺口 |
| batch-003 | 浏览器/devtools 验证 redesign page，并决定 readiness 是否关闭或继续 | d2on | completed-blocked | 已产出 durable blocker；该类单次 closing check 只有在最后收尾且效率明确更优时才值得单独成批，否则默认留在执行侧 repair/approval gate |
| batch-004 | 单设备 onboarding execute 路径诚实化 | d2on | reviewed | 浏览器验证后确认存在真实 execute contract gap，进入持续开发 |
| batch-005 | 用有界单设备 execute probe 推进真实 monitor/log evidence | d2on | reviewed | owner-directed continuation from batch-004 evidence |
| batch-006 | 恢复真实单设备 execute 主线并去掉被动等待漂移 | d2on | reviewed | batch-005 已完成但未落到真实 execute evidence；必须继续驱动 execution lane |
| batch-007 | 用更明确的返工故事继续推进 execute-path 主线 | d2on | completed-with-drift | 已重新驱动 execution lane，但 worker 仍把 doc-only 结果误判为完成 |
| batch-008 | 用故事级验证和机器可核对证据重新拉回真实代码/真实执行主线 | d2on | completed-with-exact-blocker | 已拿到 live `ensure` blocker 与 controller-backed tuple；该 closure-stage truth gate 已高质量完成 |
| batch-009 | 修复精确 `config source` blocker 并沿同一路径复跑 | d2on | completed-with-rerun-truth | 已修复 `ensure` 顶层漂移并保留 exact controller tuple，但同一路径仍保留 `log_forward` config-source blocker |
| batch-010 | 在恢复同一路径 rerun 前补齐 syslog listener contract/page/wiring 链 | d2on | completed-with-exact-blocker | 已完成 `D2ON-029A/B/C` 与 `D2ON-030/031`，并把 live 路径收敛成“旧 placeholder 合同仍在返回”的精确 blocker |
| batch-011 | 先补齐 area listener 页功能闭环与真实 collector-side 下发，再决定是否回到 managed-listener runtime/blocker 线程 | d2on | completed | 已完成 `D2ON-032/033/034/035`，后续又以 `D2ON-039/040/041` 关闭 server/network device-side delivery 与 server monitor-mode UI 缺口 |
| batch-012 | 打开新 scope：批量 onboarding、全设备采集验证门禁、device-side SNMP trap target 下发 | d2on | completed | `D2ON-043/044/045/046/047/048` 已完成；bounded live probe 使用 ready H3C/Comware 设备验证 batch ensure 与 `snmp_trap_target` controller execution 成功 |
| batch-013 | 升级新 scope：Prometheus 指标可查询，Loki 日志/trap 可查询 | d2on | reviewed | `D2ON-049` 已完成查询工具；下一步用工具分别验证指标、服务器本地日志、服务器 syslog、网络 syslog、SNMP trap |
