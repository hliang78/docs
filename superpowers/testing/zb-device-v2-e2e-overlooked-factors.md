# ZB / Device V2 E2E 易忽略因素清单

配套文档：
- AI 交接：[zb-device-v2-e2e-ai-handoff.md](/home/jacky/project/OneOPS-ALL/docs/superpowers/testing/zb-device-v2-e2e-ai-handoff.md)
- 测试总纲：[zb-device-v2-e2e-master-outline.md](/home/jacky/project/OneOPS-ALL/docs/superpowers/testing/zb-device-v2-e2e-master-outline.md)

适用范围：
- `ZB` 外部入口
- 页面导入 `CreateBatch -> Upload -> Validate -> Apply`
- 页面 `store/start`
- `entity_instance / platform_devices_v2 / device_v1`
- agent 真实任务与 runtime
- `device_v2` 前端详情页、列表页、工作台、监控中心

这份文档不替代测试总纲。
它专门记录那些“很容易让测试结论失真”的因素，避免出现：
- 实际已经失败，但我们误判为成功
- 数据已经不一致，但页面看起来正常
- 运行态已经异常，但只看到了配置下发成功
- 真实问题被投影层、缓存层、聚合层掩盖

## 使用原则

每次新增真实联调用例时，不只要看“有没有数据”，还要先过这 4 个问题：

1. 当前看到的是源数据，还是投影数据，还是读时聚合结果？
2. 当前看到的是“配置成功”，还是“运行成功”？
3. 当前结果来自最新一轮 task，还是上一轮残留状态？
4. 同一台设备在 `detail / list / task summary / agent runtime` 四处是否一致？

只要这 4 个问题里有一个没答清楚，当前结论就不能当最终结论。

## 一、最容易忽略的核心因素

### 1. `harnessed integration` 很容易被误当成全真联调

风险：
- 用 stub 的 `detect/facts/manage/monitor` 验证通过，并不代表真实链路通过。
- 它更适合作为快速回归，而不是最终验收。

真实教训：
- 前期大量 `ZB-* / UIS-* / CMP-*` 用例都通过，但后续真实联调还是挖出了多条生产级问题。

强制动作：
- 每轮结论都要明确标记是 `passed` 还是 `passed-real`
- 真实链路必须留下 `request_id / task_id / 设备编码 / 时间 / 证据`

### 2. `task success` 不等于“内容正确”

风险：
- task 成功只说明流程没报错，不说明写进 DB、V1、agent 的内容就是对的。

真实教训：
- `REAL-017 / REAL-018 / REAL-019 / REAL-020` 里就出现过“状态成功，但字段映射漏同步”的问题，例如 `device_v1.login_method` 为空。

强制动作：
- 成功链路至少同时核对：
  - `entity_instance`
  - `platform_devices_v2`
  - `device_v1`
  - agent 任务内容
  - 页面读模型

### 3. `monitor_push_status=success` 不等于 agent 运行健康

风险：
- 它只代表监控任务下发成功，不代表 agent 上的任务正在健康运行。

真实教训：
- `REAL-027` 里两台设备页面都还是成功，但 agent 真实 runtime 已经分别出现 `no route to host` 和 `connection refused`。

强制动作：
- 不只查 `monitor_push_status`
- 还必须查：
  - `/api/v2/platform/monitoring/tasks?view_mode=runtime`
  - 必要时查单条 `/runtime`
  - `inputs[].last_error / last_gather_at / runtime_status`

### 4. 投影层数据和真实源数据之间的差异，极容易误导判断

这是当前最需要单独强调的一类。

风险：
- `entity_instance` 是真实源数据
- `platform_devices_v2` 是投影
- `device_v2 detail/list` 又是基于不同读路径拼出来的只读结果
- `runtime_health` 还是读时聚合，不是持久字段

也就是说，同一台设备可能同时存在：
- 源数据已经更新
- 投影没同步
- `list` 已经对了
- `detail` 还错着
- 页面显示的是读时聚合后的第三种状态

真实教训：
- `REAL-026`：`created_at / updated_at` 在页面 detail/list 里被错误投影成零值，但源表有正确时间
- `REAL-036`：blocked 后 `detail/list` 残留旧成功态，是因为 blocked 写回只清了 `attributes`，没清 `metadata`
- `REAL-037 / REAL-038`：恢复 payload 会把旧成功态重新写回源数据，再被读模型重新放大
- 同一时刻还出现过：
  - `list` 干净
  - `detail` 仍然读出旧 `process_result`
  这种现象

强制动作：
- 任何可疑状态都至少并排核对这 5 层：
  - `entity_instance.attributes`
  - `entity_instance.metadata`
  - `platform_devices_v2.attributes`
  - `platform_devices_v2.metadata`
  - `GET /api/v1/device/v2/{code}` 与 `/list`

最低检查项：
- `stage_status`
- `manage_status`
- `sync_to_v1_status`
- `monitor_push_status`
- `process_result`
- `workflow_trace`
- `created_at / updated_at`

如果 `source / projection / detail / list` 四层有任意一层不一致，必须单独记为 finding。

### 5. `detail` 和 `list` 不是天然一致的

风险：
- 两个接口可能走不同读路径
- 一个直接从 `entity_instance` 拼
- 一个从投影表查
- 一个再叠加 `runtime_health`

真实教训：
- 我们已经真实遇到过：
  - `list` 是干净的
  - `detail` 还挂着旧 `process_result`

强制动作：
- 每个关键 case 至少同时查一次：
  - `GET /api/v1/device/v2/{code}`
  - `GET /api/v1/device/v2/list?keyword={code}`

### 6. `runtime_health` 是读时聚合，不是持久状态

风险：
- 它不是写回 `device_v2` 的固定字段
- 读取当下会根据 `device_v1_code -> task_subject -> monitoring runtime projection` 重新计算

影响：
- 你看到的 `runtime_health` 可能变
- 但源表数据完全没变

强制动作：
- 遇到 `runtime_health` 异常时，同时记录：
  - `device_v1_code`
  - 关联的 `projection_id`
  - `view_mode=runtime` 的原始证据

### 7. “恢复数据”本身也会制造脏状态

风险：
- 很多人会默认恢复 payload 是“干净的”
- 但真实备份里可能带着旧 `process_result / sync_to_v1_status / monitor_push_status / workflow_trace`
- 一旦直接 `PUT` 回去，就会把旧成功态重新污染回来

真实教训：
- `REAL-037` 就是这条

强制动作：
- 任何恢复 payload 在执行前都要检查并净化：
  - `process_result`
  - `workflow_trace`
  - `sync_to_v1_status`
  - `sync_to_v1_message`
  - `monitor_push_status`
  - `monitor_push_error`
  - `runtime_health`

### 8. 活跃页面组件不一定是你刚改的那个组件

风险：
- 路由可能已经切到 `Rebuilt` 版
- 但代码还在旧组件上改

真实教训：
- `REAL-032 / REAL-033`：真实活跃路由挂的是 `DeviceV2AdaptWorkbenchRebuilt.vue`，不是旧版工作台组件

强制动作：
- 浏览器级真验收前，先确认：
  - 实际路由
  - 实际挂载组件
  - 实际网络请求

### 9. agent runtime 会自然漂移成 `stale`

风险：
- 即使没改设备数据，运行态也会因为时间窗口自然从 `running/failed` 漂到 `stale`
- 很容易被误判成“这轮操作导致的变化”

真实教训：
- 最新回查里 `ping-basic_192_168_100_15_161` 就已经真实变成了 `stale`

强制动作：
- 记录证据时必须带时间
- 比较前后状态时，同时记录 `last_updated / last_gather_at`

### 10. 同一批 runtime 证据会随着网络恢复，从 `unknown` 演化成 `failed/running`

风险：
- 第一轮看到 `runtime_status=unknown`，不代表问题已经消失
- 它也可能只是 agent 还没把最新 input 运行结果暴露出来
- 网络恢复、任务重新执行、snapshot 再同步后，同一条任务可能马上从 `unknown` 变成明确的 `running` 或 `failed`

真实教训：
- `DVCBAEFDC43A8F3` 在网络恢复后重新触发真实 `store/start`，`runtime_health` 不再停留在模糊态，而是继续收敛成：
  - `ping-basic_192_168_100_15_161 = running`
  - `snmp-passthrough_192_168_100_15_161 = failed`
  - 错误为 `connection refused`

强制动作：
- 不要只截一轮 runtime 结果就下结论
- 至少并排记录：
  - `device_v2.runtime_health`
  - `view_mode=runtime`
  - 单条 `/runtime`
  - 当前网络/时间窗口
- 一旦网络条件发生变化，要重新回放真实链路，再看 runtime 是否从 `unknown` 收敛成明确状态

补充提醒：
- 像 `REAL-070` 这种“重放后先 `unknown`、再回到 `running/stale`”的场景里，即使状态重新出现了，也不能默认它代表新版本已经采到新数据。
- 必须同时核对 `version`、`last_updated / last_gather_at` 与本轮 `store/start` 时间；如果 runtime 回来的时间戳早于本轮重放完成时间，那更像是旧 input 运行态重新被读到，而不是新一轮采集已经真正发生。
- 这类场景还要并排看 `platform_metric_asset_instance`；如果 runtime 已恢复成 `running/stale`，但 metric asset 仍全部停在 `planned`，就更不能把它误判成“本轮采集已稳定恢复”。
- `REAL-071` 之后要把这两层现象拆开看：如果 `unknown` 窗口结束后出现的是“晚于本轮重放完成时间”的新 `last_updated`，那说明 agent 旧状态回写问题已经被压住；这时若 `platform_metric_asset_instance` 仍继续停在 `planned`，优先怀疑的是“snapshot / observed metric 同步没触发”，而不是 agent 又读回了旧样本。
- `REAL-072` 之后这个判断口径还要再更新一层：如果 `store/start` 完成后 `platform_monitoring_v2_agent_task_snapshot.synced_at` 已经推进到本轮完成时间附近，且 `platform_metric_asset_instance` 已从 `planned` 收敛成 `observed/stale`，就说明自动 snapshot 同步已经生效；这时单条 `/runtime` 仍然 `unknown`，优先追的是 agent input 首轮采集时序，而不是平台又漏调了 `sync-agent-snapshot`。
- `REAL-073` 之后还要再拆一层：如果 burst apply 期间发生了多次 `ReplaceAllInputs()`，要警惕“旧 generation 的 gather 还在继续白跑，最终代 gather 被排到很后面”。修复后，像 `ping` 这类更早轮到的 input，应该能在本轮 fresh 时间戳出现后更快脱离 `unknown`；若仍长时间不动，再去怀疑它自己的采集位置或耗时。
- `REAL-074` 之后解读 `last_updated / last_gather_at` 也要注意区分“input 自己真正完成的时间”和“整轮循环起点时间”。如果 later input 明显比 earlier input 晚很多才从 `unknown` 变成 `running`，但两者却共享同一个更早时间戳，那更像是时间戳口径 bug；修复后，这两条时间应该能自然拉开。
- `REAL-075` 之后还要补一层判断：如果 agent 日志能证明 `snmp` 比 `ping` 更早收到 apply，但它仍明显更晚才从 `unknown` 变成 `running`，就不要再默认是“后续无关 replace 把它 priority 覆盖掉了”。priority carry-over 修完后，这类窗口更可能是 `snmp` 自己这一轮 gather 的真实耗时。
- `REAL-076` 之后这个判断口径还要再细一层：如果 debug 日志显示 `snmp` 自己真正的 gather duration 只有几秒，但它距离 apply 很久之后才开始，那优先怀疑的是“旧 priority backlog 抢在当前 replay 前面”，而不是 SNMP 插件本身慢。修掉这层后，`snmp` 的完成时间应该会收敛到接近 `ping + snmp` 自身耗时的量级，而不是继续卡在几十秒甚至一分钟以上。
- `REAL-077` 之后还要再补一层：如果 agent 已经切到 Telegraf 式 per-input runner，并且像 `DVCE1EE3F7D394C` 这类 replay 在恢复了几十条旧任务的情况下也能在首轮查询就直接返回 `running`，那就不要再默认把后续任何慢窗口都归因到“全局串行 sweep”或“priority backlog”。这时若某条任务仍明显慢很多，优先看的是该 input 自己的真实 gather 时长、同设备限流、或监控模板内容体量。
- `REAL-078` 之后还要补一个解读口径：如果 replay 后 `ping/snmp` 已经在新版本上返回 `running`，但 `t+30s` 左右再次查询时 `last_updated` 没有继续推进，不要马上判成“采集停了”。先对照当前 `telegraf_inputs.interval`；像本轮 `interval=60s` 的配置下，`21:08:44` 已完成 fresh gather，而 `21:09:30` 仍保持同一 `last_updated` 是预期表现，关键是版本是否已切到本轮、以及 agent 日志里是否已有 fresh apply 和 metric dump。

### 11. 阻断后“没刷新 agent 任务”也是正式验收项

风险：
- 很多测试只看“成功时任务有没有发”
- 忽略了“失败时任务不应该被刷新”

真实教训：
- `REAL-015 / REAL-016 / REAL-036` 都验证了阻断后 agent 任务时间不应前移

强制动作：
- 阻断类 case 必查：
  - `projection_id`
  - `last_updated`
  - `last_gather_at`
  - 是否出现误刷新

## 二、针对投影差异的专项检查法

以后凡是怀疑“页面和真实数据不一致”，统一按这个顺序排：

1. 查 `entity_instance`
   目标：确认源数据是否已经正确

2. 查 `platform_devices_v2`
   目标：确认投影是否同步

3. 查 `GET /api/v1/device/v2/{code}`
   目标：确认 detail 读模型是否正确

4. 查 `GET /api/v1/device/v2/list`
   目标：确认 list 读模型是否正确

5. 查 `task summary / runs / observations`
   目标：确认当前状态是否来自本轮 task，而不是历史残留

建议统一记录这张对照表：

| 层 | 关键字段 | 结果 |
| --- | --- | --- |
| entity source | `stage_status/manage_status/process_result/sync_to_v1_status/monitor_push_status` | |
| projection table | 同上 | |
| detail API | 同上 | |
| list API | 同上 | |
| task summary | `overall_status/process_result/headline` | |

只要不是全等，就不能直接下“系统正确”的结论。

## 三、后续新增真实用例时的强制检查清单

每条新增 `REAL-*` 用例，建议至少补齐下面这些检查：

- 这条结果来自真实链路还是 stub/harness
- `request_id / task_id / device_code`
- `entity_instance` 和 `platform_devices_v2` 是否一致
- `detail` 和 `list` 是否一致
- `monitor_push_status` 和 agent runtime 是否一致
- `runtime_health` 是否只是读时聚合结果
- 同一类列表接口到底返回 `data.list` 还是 `data.items`
- 是否存在旧 task 的 `process_result` 残留
- 是否存在恢复 payload 回灌旧成功态
- 阻断时 agent 任务是否被误刷新
- 成功时 agent 任务内容是否真的正确

## 四、建议的落地规则

建议以后在真实联调记录里新增 3 个固定标签：

- `source-vs-projection`
  只要源数据和投影有差异，就打这个标签

- `config-vs-runtime`
  只要监控配置和 agent 运行态有差异，就打这个标签

- `history-leak`
  只要当前结果混入上一轮 task / 上一轮恢复数据，就打这个标签

这样后面按标签回看，会比单纯翻 `REAL-*` 编号快很多。

## 五、当前已经被真实踩中的高风险项

截至 2026-06-01，已经被真实联调明确踩中的高风险项包括：

- blocked 后旧成功态残留在 `detail/list`
- 恢复 payload 把旧成功态重新写回
- `list` 和 `detail` 走出不同结果
- 查询接口返回体结构不同，排查时误读 `data.list` / `data.items`
- `created_at/updated_at` 投影为零值
- `monitor_push_status=success` 但 agent runtime 已失败
- 活跃前端路由和被修改组件不一致
- `runtime_health` 未注入主程序装配
- ZB 复用已有设备时覆盖现有凭据引用
- `sync_to_v1` 成功但字段内容漏同步
- `block_on_partial` 这类参数名容易被误解成“任意 partial 都阻断”，但真实可扩展语义必须结合 `required_dataset_keys / required_failed_dataset_keys` 一起判断
- `required_dataset_keys` 不能只放全局默认；一旦设备 profile 增多，必须下沉到 `collection_profiles`，否则不同设备类型会共用错误的“关键 dataset”口径
- profile 命中信息和 required dataset 可能只透在 `device_runs[].device_collection2.*` 这一层，不一定出现在顶层 `device_run` 字段；查结果时要看对位置
- `required dataset` 的真实阻断不能只看 DC2 原始 run：即使 `device_collection2_run_device.dataset_results_json` 已经明确出现 `status=partial`，如果最终 `device_v2` summary / store_run projection 没有把 `partial_dataset_keys`、`required_failed_dataset_keys` 一路带到 store gate，任务仍可能被误放行为 `D2_STORE_SUCCESS`
- Nacos 直连调试时要分清实例和参数口径：当前 `:8280` 服务实际读取的是 `127.0.0.1:9048` 的 `ONEOPS_PROD/cipher-aes-start-config`，并且单配置 GET/POST 使用 `tenant=ONEOPS_PROD`；若误把更新打到 `8848` 或继续使用 `namespaceId`，很容易出现“发布成功但运行实例没有生效”的假象
- 为验证 `required partial` 这类严格场景而临时加严 `collection_profiles.required_dataset_keys` 后，必须在结论收口前恢复基线配置并重启运行中的 `:8280`；否则后续正常样本会继续按“临时加严 profile”运行，造成回归结论失真
- `external_request_log.status=Success` 只代表 ZB 同步入口已经受理，不代表整条异步入库成功；真正的最终结果要看 `callback_detail.summary_v2`、内部 `task_id` 以及实体最终态，尤其在 `required partial` 这类场景里，同步阶段仍可能返回“成功保存基础信息阶段”，但 callback 会在数秒后回落成 `ZB_STORE_ALL_FAILED`
- `monitor_push_status=success`、任务 `found=true`、甚至 projection `version` 已经刷新，也不等价于 agent runtime 已经形成可读健康态；像 `REAL-058` 这类场景里，单条 `/runtime` 仍可能统一返回 `status=unknown / 未发现该任务对应的 input 运行状态`，所以“配置已下发成功”和“运行态已稳定可观测”必须拆开验证
- `runtime unknown` 不一定代表名称匹配实现错误；像 `REAL-059` 里真实返回的 input 名称就是 `task_id + "_" + hash`，现有前缀匹配可以命中，所以要先排除“任务刚刷新完成、input 状态尚未形成”的时序窗口，再去怀疑匹配逻辑
- `runtime_health` 聚合不能把 `stale` 当成健康态；像 `REAL-060` 这种场景里，单条 `/runtime` 已经明确是 `stale`，如果 `device_v2 detail/list` 还显示 `healthy`，那是聚合口径 bug，不是前端展示问题
- 任务配置里的 `interval=60s` 不代表 `/runtime.last_updated` 一定会按分钟级平滑前进；像 `REAL-062` 里同一台设备的 `ping` 与 `snmp` 都表现出更慢、更跳变的刷新窗口，因此 `stale` 阈值要结合真实刷新节奏解读，不能机械地把“超过 5 分钟没动”直接当成任务已死
- 监控任务“存在且能运行”不等于“内容正确”；像 `REAL-063` 里 `DVCE1EE3F7D394C` 的 H3C 专用 `snmp-passthrough` 策略虽然能下发，但其中 `cpu_usage/memory_usage` OID 在目标设备上真实返回 `No Such Instance`，所以内容级验收必须把“任务模板是否命中了设备支持的 OID”单独作为检查项
- `device_collection2` 同一轮 facts 里可能同时出现“高质量 identity.model”和“低质量 physical_entity.model”；如果合并逻辑依赖 `ListFacts` 的默认顺序、又采用“先到先占坑”，就会把 `Fixed SubCard on Board` 这类模块名错误写成主设备型号。像 `REAL-064` 这种场景里，必须明确让 `device_identity.model` 优先于普通 physical module 名
- 修正入库画像不等于监控策略会自动细化；像 `REAL-065` 里即使主记录已经真实变成 `VSR1000`，当前 `strategy_selector` 里如果没有 `VSR1000` 专用子策略，`snmp-passthrough` 仍会继续命中 H3C 通用副本。因此“主数据模型正确”和“监控策略选择正确”要分两层验收
- 任务级 runtime `running/healthy` 不等于指标级覆盖也健康；像 `REAL-066` / `REAL-067` 里同一条 `snmp-passthrough` 任务已经真实 `running` 且最近一次 `input` 采集成功，但 `platform_metric_asset_instance` 仍可能出现 `observed=20 / stale=4`。如果只看 `/runtime`，设备会被误判成健康；必须再把 `metric_asset_instance` 的 `stale` 一起纳入内容级验收
- `sync-agent-snapshot` 既会刷新 runtime snapshot，也会触发 observed/stale metric asset 同步；像 `REAL-067` 这种场景里，如果不先执行一次真实 `POST /api/v2/platform/monitoring/tasks:sync-agent-snapshot`，库里的 `platform_metric_asset_instance` 可能还停在旧状态，导致“runtime 已更新、指标覆盖仍旧值”的排查结论失真
- `runtime_health` 聚合存在优先级，不是简单把所有异常拼在一起：当前口径是 `task failed > task stale > metric stale > healthy`。因此当同一设备既有真实 `runtime stale`、又有 `metric_asset_instance.stale` 时，页面消息会优先显示“运行状态超过 5 分钟未更新”，而不是“声明指标未观测到”；排查时要按这个优先级理解最终展示结果
- `last_metrics_count` 不能靠 `len(metricsCh)` 的前后差推断；像 `REAL-068` 里一旦 `processMetrics` 并发消费同一个 channel，单个 input 的采集量就可能被算成负数。凡是看到 `last_metrics_count < 0`，优先怀疑 agent 侧计数实现，而不是先怀疑目标设备或 plugin
- `ReplaceAllInputs()` 会先清空 agent 侧 `inputStatus`，但不会同步清空 `observedMetrics` 或平台库里的 `metric_asset_instance`。因此像 `REAL-069` 这种“重放刚完成，`/runtime` 还是 unknown，但 detail/list 已经能看到 stale metric 覆盖”的现象，并不一定表示 runtime 查询坏了，可能只是新一轮采集还没形成
- agent 当前 `gatherMetrics()` 是串行遍历所有 input 的。现场如果同时挂了很多 SNMP 任务、且单个 SNMP 任务本身又可能耗时 5~40 秒，那么“配置里写着 `interval=60s`”并不代表每一条任务都能在 60 秒内得到新的 `inputStatus`。像 `REAL-069` 里，`ping` 很快恢复 `running`，但同一设备的 `snmp` 在一个 nominal interval 后仍可能保持 `unknown`

这些项都不应该再被当成“边角问题”。
后续新增 case 时，默认都要先排除它们。
