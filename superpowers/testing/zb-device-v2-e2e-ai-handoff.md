# ZB / Device V2 E2E AI 交接文档

适用目标：
- 后续 AI 继续接手 `ZB` 外部入库与页面 `device_v2` 入库的真实联调测试
- 继续沿当前有效方法做“真链路 + 真数据 + 真 agent/runtime + 真 DB 内容”验证

关联文档：
- 测试总纲：[zb-device-v2-e2e-master-outline.md](/home/jacky/project/OneOPS-ALL/docs/superpowers/testing/zb-device-v2-e2e-master-outline.md)
- 易忽略因素：[zb-device-v2-e2e-overlooked-factors.md](/home/jacky/project/OneOPS-ALL/docs/superpowers/testing/zb-device-v2-e2e-overlooked-factors.md)
- 设计文档：[2026-05-31-zb-device-v2-e2e-design.md](/home/jacky/project/OneOPS-ALL/docs/superpowers/specs/2026-05-31-zb-device-v2-e2e-design.md)

## 1. 先读这 6 条

1. 当前这套测试方法有效的核心，不是“跑用例”，而是坚持只认真实链路证据。
2. 每条结论都必须明确区分：`passed`、`passed-real`、`finding-real`、`passed-code`。
3. 不能只看状态位，必须验证内容正确：
   - `entity_instance`
   - `platform_devices_v2`
   - 必要时 `device_v1`
   - agent 任务内容
   - 单条 `/runtime`
   - 页面 `detail / list / workbench / monitoring-center`
4. `monitor_push_status=success` 只代表下发成功，不代表 agent 运行健康。
5. `runtime_health` 是读时聚合，不是持久字段。
6. 只要改了 `Nacos`，就必须同步 `quick_env` 模板，不允许两边口径漂移。

## 2. 当前环境基线

截至 `2026-06-01`，当前真实联调环境以这组参数为准：

- OneOps API：`http://127.0.0.1:8280`
- 活跃 Nacos：`127.0.0.1:9048`
- Nacos tenant：`ONEOPS_PROD`
- Nacos group：`DEFAULT_GROUP`
- 前端：`http://127.0.0.1:3012`
- 登录账号：`admin / admin@123`

不要默认 `8080` 或其他旧地址仍然有效。每次接手时，先重新确认当前活跃进程和端口。

## 3. 本轮之后固定遵守的测试规则

### 3.1 只认真实链路

优先级：
- `REAL-*` > harnessed integration

允许保留 harnessed 测试做快速回归，但它们不能替代真实验收。

### 3.2 每条真实 case 必留 6 类证据

至少记录：
- `request_id` 或 `task_id`
- 设备编码
- 时间
- DB 结果
- agent/runtime 结果
- 外部呈现结果

### 3.3 任何成功链路都不是只看“有无数据”

至少核对：
- 业务状态是否成功
- 主记录字段是否正确
- 投影字段是否正确
- agent 任务是否真的刷新
- runtime 内容是否合理

### 3.4 任何阻断链路都要看“是否没有误刷新”

至少核对：
- `sync_to_v1_status`
- `monitor_push_status`
- `process_result`
- agent 任务 `last_updated / last_gather_at`

## 4. Nacos 与 quick_env 同步规则

这是强制规则。

只要变更了下列 OneOps 配置之一：
- [nacos-device_collection2.merge.yaml](/home/jacky/project/OneOPS-ALL/OneOps/config/nacos-device_collection2.merge.yaml)
- [example_config.yaml](/home/jacky/project/OneOPS-ALL/OneOps/example_config.yaml)

就必须同步检查并更新：
- [cipher-aes-start-config.yaml](/home/jacky/project/OneOPS-ALL/quick_env/init-configs/nacos/cipher-aes-start-config.yaml)

最常见的同步项：
- `collection_profiles`
- `dataset_keys`
- `required_dataset_keys`
- `block_on_failure`
- `block_on_partial`
- 与 `device_collection2` 相关的采集口径注释

### 4.1 为什么必须同步

因为真实联调一直在同时使用两套入口：
- 当前本地/真实 OneOps 实例
- `quick_env` 初始化模板

如果只改 `OneOps/config`，不改 `quick_env`，后续 AI 很容易在：
- 新起实例
- `bootstrap-refresh`
- 复现场景

时得到另一套配置，导致测试结论失真。

### 4.2 quick_env 生效动作

改完模板后，不会自动覆盖已导入的 Nacos 旧值。

至少做其中一种：

```bash
cd /home/jacky/project/OneOPS-ALL/quick_env
./manage.sh bootstrap-refresh --instance <实例名>
```

或删除初始化标记后重新走初始化：

- `quick_env/.runtime/<instance-slug>/.nacos_initialized`

### 4.3 当前已对齐的口径

当前这轮已经对齐过：
- `OneOps/config/nacos-device_collection2.merge.yaml`
- `OneOps/example_config.yaml`
- `quick_env/init-configs/nacos/cipher-aes-start-config.yaml`

重点是：
- 各 profile 的 `required_dataset_keys`
- `block_on_partial` 新语义

## 5. 当前有效的测试方法

### 5.1 推荐顺序

1. 先选真实设备样本
2. 先确认当前 Nacos 基线
3. 再触发入口
4. 再并排查 DB / runtime / 页面
5. 最后回填总纲和易忽略因素

### 5.2 真入口优先级

建议优先这 4 类：
- 页面 `store/start`
- 页面导入 `CreateBatch -> Upload -> Validate -> Apply -> store/start`
- `ZB` 单设备真实请求
- `ZB` 混合批次真实请求

### 5.3 查证顺序

推荐固定按这条顺序排：

1. 入口返回
2. `entity_pipeline_task`
3. `device_v2_store_run`
4. `entity_instance`
5. `platform_devices_v2`
6. 必要时 `device_v1`
7. `platform_monitoring_task_subject`
8. `view_mode=runtime`
9. 单条 `/runtime`
10. 页面 `detail / list / workbench / monitoring-center`

## 6. 当前高价值真实样本

### 6.1 服务器样本

- `DVCBAEFDC43A8F3`
- `device_v1_code=DEV20260531000005`
- 典型作用：
  - 页面导入/页面 `store/start`
  - 脏凭据阻断与恢复
  - `runtime_health` 与前端三页一致性

说明：
- 服务器在入库采集阶段不通过 SNMP 做 DC2 采集，这条当前按设计接受。
- 但如果配置了 `snmp` 监控任务，agent 仍可能真实报 `connection refused`，这属于监控运行结果，不属于采集链路 bug。

### 6.2 复用设备样本

- `DVC19218A412EA1`
- `device_v1_code=DEV20260531000004`
- 典型作用：
  - `ZB` 复用已有设备
  - 凭据覆盖问题
  - `sync_to_v1`
  - callback 一致性

### 6.3 网络设备样本

- `DVCE1EE3F7D394C`
- `device_v1_code=DEV20260531000009`
- `H3C / Comware / VSR1000`
- `in_band_ip=172.32.2.15`
- 典型作用：
  - `required_dataset_keys`
  - `block_on_partial`
  - 通用 `snmp-passthrough`
  - runtime stale / unknown / metric coverage

## 7. 当前关键口径

### 7.1 `block_on_partial`

当前不是“任意 partial 一律阻断”。

当前真实口径是：
- `partial + required dataset 缺失`：阻断
- `partial + only optional dataset 缺失`：可放行

因此继续测时，必须同时看：
- `required_dataset_keys`
- `required_failed_dataset_keys`

### 7.2 服务器采集阶段不走 SNMP

这条当前按预期接受。

不要再把“服务器入库采集不走 SNMP”当缺陷方向继续追。

### 7.3 `runtime_health`

当前已经包含：
- 任务级 `running/failed/stale/unknown`
- 指标级 `platform_metric_asset_instance.status=stale`

也就是说：
- 任务健康但声明指标 stale，设备级也会降为 `degraded`
- 但任务级 `failed/stale` 仍比指标级 stale 优先

## 8. 当前已证明有效的命令模板

### 8.1 登录

```bash
curl -s http://127.0.0.1:8280/api/v1/access/login \
  -H 'Content-Type: application/json' \
  -d '{"account":"admin","password":"admin@123"}'
```

### 8.2 页面入口真实回放

```bash
curl -s -X POST 'http://127.0.0.1:8280/api/v1/device/v2/store/start' \
  -H "X-Auth-Token: $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"codes":["DVCE1EE3F7D394C"],"options":{"async":false}}'
```

### 8.3 任务 runtime

```bash
curl -s -H "X-Auth-Token: $TOKEN" \
  "http://127.0.0.1:8280/api/v2/platform/monitoring/tasks/agent-001:collect_agent-001_ping-basic_172_32_2_15_161/runtime"
```

### 8.4 runtime 列表

```bash
curl -s -H "X-Auth-Token: $TOKEN" \
  "http://127.0.0.1:8280/api/v2/platform/monitoring/tasks?view_mode=runtime&agent_code=agent-001&page=1&page_size=50"
```

### 8.5 同步 agent snapshot

```bash
curl -s -X POST \
  -H "X-Auth-Token: $TOKEN" \
  "http://127.0.0.1:8280/api/v2/platform/monitoring/tasks:sync-agent-snapshot"
```

### 8.6 quick_env 刷新 Nacos

```bash
cd /home/jacky/project/OneOPS-ALL/quick_env
./manage.sh bootstrap-refresh --instance <实例名>
```

## 9. 当前未收口但很值得继续的方向

### 9.1 网络设备 SNMP runtime 的时序窗口

现状：
- `DVCE1EE3F7D394C`
- `snmp-passthrough` 在重放后仍可能出现一段 `runtime unknown`
- 当前更像：
  - `ReplaceAllInputs()` 清空 `inputStatus`
  - agent 串行 `gatherMetrics()`
  - 并非任务未下发
- 最新真实回放 `task_id=entv2_1780298951581795673` 还补充证明：
  - `t0=2026-06-01 15:29:46 +08:00` 时两条 `/runtime` 都会退成 `unknown`
  - 到 `t+70=15:31:20` 又会同时回到 `running`
  - 但 `last_updated` 停在更早的 `2026-06-01T15:27:20+08:00`
  - 到 `t+140=15:32:30` 又一起漂成 `stale`
  - 同时 `platform_metric_asset_instance` 仍停在 `ping=planned(9)`、`snmp=planned(21)`
- 这意味着当前窗口不一定是在“等新版本第一次采集”，也可能是在窗口结束后重新读到旧 input 的运行态时间戳
- 最新进展：给 agent 的 `TelegrafInputCollector` 加了 input status 代际保护并重启现场进程后，`REAL-070` 那种“`unknown` 之后又挂回早于本轮重放时间的旧样本”已不再复现
  - 新回放 `task_id=entv2_1780300434210851389`
  - `t0=15:54:21` 与 `t+70=15:55:53` 两条 `/runtime` 都持续是 `unknown`
  - 到 `t+140=15:57:03` 时，`snmp` 才首次回到 `running`
  - 且 `last_updated=2026-06-01T15:54:38+08:00` 已晚于本轮 `store/start` 完成时间 `15:54:06`
- 这说明“旧 input 状态回写当前代”这一层已经被压住；当前更值得继续追的剩余问题，变成了：
  - 为什么 `ping` 仍可长期保持 `unknown`
  - 为什么单条 `/runtime` 仍会在一段时间里保持 `unknown`

- 最新进展：`monitor push` 后未自动触发 `snapshot / observed metric` 同步这一层已经补上
  - 代码侧在 `OneOps/app/device/service/impl` 给 store 入口加了 best-effort `TaskProjectionServiceV2.SyncAgentSnapshot(...)`
  - 红灯测试：`TestTryNotifyMonitorProbeByStrategySelectorSets_SyncsAgentSnapshotAfterSuccessfulApply`
  - 回归：`go test ./app/device/service/impl -count=1`、`go test ./cmd -run TestDoesNotExist -count=1`
  - 真实回放 `task_id=entv2_1780301405928656020`
  - 本轮 `store/start` 在 `2026-06-01 16:10:19 +08:00` 完成时，两条单条 `/runtime` 仍都返回 `status=unknown / version=1780301418`
  - 但数据库已经自动写出新的 `platform_monitoring_v2_agent_task_snapshot.snapshot_version=1780301419031913491`，`synced_at=2026-06-01 16:10:19.032`
  - 同时 `platform_metric_asset_instance` 已不再停在 `planned`，而是 `ping=observed(9)`、`snmp=observed(19)+stale(2)`
  - `GET /api/v1/device/v2/DVCE1EE3F7D394C` 也立刻收敛成 `runtime_health=degraded`，message 为“0 个监控任务正在运行，但 1 个任务下有 2 个声明指标未观测到”
- 这说明现在要把两层问题彻底拆开看：
  - `snapshot / metric asset` 自动同步已经恢复
  - 剩余 open gap 是 agent input runtime 状态本身为什么还会短时间保持 `unknown`

- 最新进展：`ReplaceAllInputs()` burst apply 时“旧代 gather 白跑到底，把最终代挤到后面”这一层也已经补上
  - 代码侧给 agent 的 `gatherMetrics()` 抽了有序快照执行器，并在进入下一条 input 前检查 generation；若中途发生 replace，就提前终止旧代循环，让挂起的最新一代 gather 尽快启动
  - 红灯测试：`TestReplaceAllInputs_StopsStaleGatherCycleSoLatestInputsCanRunPromptly`
  - 回归：`go test ./pkg/ops/metrics -count=1`
  - 真实回放 `task_id=entv2_1780303994867650312`
  - 本轮 `store/start` 在 `2026-06-01 16:53:26 +08:00` 完成后：
    - `t+20=16:53:46` 时，`ping` 已提前收敛为 `running`
    - `last_updated=2026-06-01T16:53:35+08:00`，已晚于本轮完成时间
    - `snmp` 仍保持 `unknown`
    - 到 `t+100=16:55:07` 时，`snmp` 才回到 `running`
    - `GET /api/v1/device/v2/DVCE1EE3F7D394C` 也同步回到 `runtime_health=healthy`
  - 这说明现在的剩余窗口主要只和“这个 input 实际何时轮到自己开始/完成采集”有关，而不是旧代 gather 还在白跑几分钟

- 最新进展：later input 的 `last_updated / last_gather_at` 时间戳也已经改成按各自完成时刻回写
  - 红灯测试：`TestGatherMetricsSnapshot_RecordsPerInputTimestampInsteadOfWholeCycleStart`
  - 回归：`go test ./pkg/ops/metrics -count=1`
  - 真实回放 `task_id=entv2_1780304230109079297`
  - 本轮里：
    - `ping` 在 `t+20=16:57:41` 返回 `running / last_updated=2026-06-01T16:57:30+08:00`
    - `snmp` 到 `t+80=16:58:42` 才返回 `running / last_updated=2026-06-01T16:58:40+08:00`
    - 设备级 detail 也同步显示 `runtime_health.last_updated=2026-06-01T16:58:40+08:00`
  - 这说明 later input 不会再沿用整轮循环起点时间，后续判断“到底是哪条 input 何时真正收敛”会更可靠

- 最新进展：较早更新的 input priority 现在会跨后续无关 replace 继续保留，不再只看“最后一轮变化的是谁”
  - 红灯测试：`TestReplaceAllInputs_KeepsEarlierUpdatedInputPrioritizedAcrossLaterUnrelatedReplace`
  - collector 现在会维护“当前 generation 里尚未完成首轮采集的 pending priority inputs”，后续 processor/output/别的 input replace 会把这批名字一起带到最新 generation
  - 回归：`go test ./pkg/ops/metrics -count=1`
  - 真实回放 `task_id=entv2_1780305330979015003`
  - 本轮 agent 日志已明确看到下发顺序是 `snmp -> processor -> output -> ping`
  - 运行态观测里：
    - `t0=17:15:53` 时，`ping` 已返回 `running / last_updated=2026-06-01T17:15:51+08:00`
    - 同时 `snmp` 仍是 `unknown`
    - `t+20=17:16:13`、`t+40=17:16:33`、`t+60=17:16:53` 时，`snmp` 仍持续 `unknown`
    - 到 `t+80=17:17:13` 时，`snmp` 才返回 `running / last_updated=2026-06-01T17:16:59+08:00`
    - 设备级 `GET /api/v1/device/v2/DVCE1EE3F7D394C` 也在同一时刻从 `runtime_health=unknown` 回到 `healthy`
  - 这条结果很关键：既然本轮 `snmp` 比 `ping` 更早收到 apply，但最终仍要到 `t+80` 才收敛，就说明“较早更新 input 被后续 replace 挤掉优先级”这一层虽然真实存在、也已经被代码修住，但现在现场剩余窗口更像是 `snmp` 自身 gather 完成得晚

- 最新进展：打开 agent `debug` 时长日志后，已经确认 `snmp` 本身并不慢，真正拖窗口的是“旧 priority backlog 抢在当前 replay 前面”
  - 为了不碰正常配置，额外加了一份临时调试配置 [agent.debug.yaml](/home/jacky/project/OneOPS-ALL/ctrlhub/controller/agent/configs/agent.debug.yaml)
  - 调试日志里第一次量到的现场事实是：
    - `task_id=entv2_1780305742791739710`
    - `collect_agent-001_snmp-passthrough_172_32_2_15_161` 在 `17:22:35.366` 收到 apply
    - 但真正的 `Gathered metrics from input` 到 `17:23:49.994` 才出现，`duration=3.853281921s`
    - 也就是说它不是自己跑了 70 多秒，而是晚了 70 多秒才轮到自己开始
  - 随后又从同一份 debug 日志确认，排在它前面的主要是一长串旧的 `ping-basic_*` gather；这批 backlog 来自 agent 重启后恢复的持久化任务，而我们当时的 pending priority 实现会把“当前 replay 的新变更”和“旧 backlog”一起按名字重排
  - 针对这层又补了红灯测试：`TestReplaceAllInputs_PrioritizesCurrentBurstAheadOfOlderPendingBacklog`
  - collector 现在除了 pending set 之外，还会维护 pending priority 的执行顺序：当前 burst 里的新变更放前面，旧 backlog 放后面
  - 回归：`go test ./pkg/ops/metrics -count=1`
  - 带着修复和 debug 配置再次重启现场 agent，并在“恢复 41 条持久化任务后、老 backlog 仍在扫”的最差场景下重放：
    - `task_id=entv2_1780306024767573333`
    - `snmp` 在 `17:27:17.262` 收到 apply
    - `ping` 在 `17:27:19.868` 完成首轮 gather，`duration=2.051671712s`
    - `snmp` 在 `17:27:23.830` 完成首轮 gather，`duration=3.962464057s`
    - 对应 runtime 已在 `last_updated=17:27:19` 与 `17:27:23` 收敛为 `running`
  - 这轮说明真正卡住我们的不是 `snmp` 插件耗时，而是 priority 排队策略；压掉这层后，`snmp` 首轮窗口已经从之前约 `80s` 收敛到接近 `ping + snmp` 自身耗时的 `6~7s`

继续追时要同时看：
- 单条 `/runtime`
- `platform_metric_asset_instance`
- agent 日志
- 是否刚重放、刚重启、刚 snapshot
- `last_updated / last_gather_at` 是否早于本轮 `store/start` 完成时间

当前更准确的结论：
- `monitor push -> snapshot / metric asset` 自动同步已经恢复
- 旧代 input status 回写当前代，已经修掉
- burst replace 把最终代 gather 挤到很后面，这一层也已经修掉
- later input 复用整轮起点时间戳，这一层也已经修掉
- 较早更新 input 会被后续无关 replace 挤掉 priority，这一层也已经修掉
- 旧 priority backlog 会抢在当前 replay 前面，这一层也已经修掉
- 仍然可能存在的短暂 `unknown`，现在更像是 `ping/snmp` 自身真实 gather 耗时之和，而不再像前面几层 priority/并发/时间戳 bug
- 下一步如果还要继续压时间，重点已经不是“会不会排不到前面”，而是看值不值得把 `ping` 和 `snmp` 两条真正并行化，或者让同设备的 `snmp` 比 `ping` 先跑

### 9.1.1 Telegraf 式容量重构计划

为了让后续 AI 能直接继续，不再只停留在 finding/修 bug 层面，本轮已经把面向“大量 SNMP 任务”的正式重构方案落到了：

- [2026-06-01-agent-telegraf-style-input-scheduler.md](/home/jacky/project/OneOPS-ALL/docs/superpowers/plans/2026-06-01-agent-telegraf-style-input-scheduler.md)
- 辅助说明：[zb-agent-telegraf-scale-refactor-notes.md](/home/jacky/project/OneOPS-ALL/docs/superpowers/testing/zb-agent-telegraf-scale-refactor-notes.md)

这份计划的边界很重要：

- 目标是先把当前 agent 从“全局串行 sweep”改成“每个 input 独立 runner + overrun skip + bounded SNMP concurrency”
- 先不做“把多个 OneOps SNMP 任务合并成一个多-agent SNMP input”的语义级 batching；那会是下一份独立计划

下一位 AI 如果继续开发，建议默认按计划里的 Task 1 -> Task 6 顺序走，而不是重新在旧的 global priority queue 上继续打补丁

### 9.2 通用 SNMP 策略对 `VSR1000` 的内容覆盖

当前结论：
- 不需要专门给 `VSR1000` 加专用策略
- 用通用 SNMP 监控即可

后续要看的不是“有没有专用策略”，而是：
- 通用 `snmp-passthrough` 对它的指标覆盖够不够
- 哪些 `stale` 是可接受未覆盖项
- 哪些会导致真实监控价值不足

### 9.3 页面读模型恢复链路

虽然已经修过多轮：
- blocked 后清理旧成功态
- restore payload 不再回灌旧管理态

但后续每次加新读模型字段时，仍要优先做一次：
- blocked -> recover -> detail/list/workbench/monitoring-center

四层一致性回归。

## 10. 每次接手后的第一轮动作

后续 AI 建议固定这么做：

1. 打开总纲和易忽略因素文档
2. 确认当前活跃 OneOps / Nacos / 前端端口
3. 确认最近是否改过 `Nacos`，若改过，核对 `quick_env` 是否已同步
4. 选择 1 条当前 open finding
5. 用真实入口重放
6. 留下 `request_id/task_id + DB + runtime + 页面` 证据
7. 更新：
   - 总纲
   - 易忽略因素
   - 必要时本交接文档

## 11. 什么时候必须回写这份交接文档

只要出现以下任一情况，就要更新这份文档：

- 活跃端口、Nacos 租户、登录方式变化
- 新增了新的“高价值样本设备”
- `block_on_partial`、`required_dataset_keys` 等口径变化
- 新发现一种足以误导后续 AI 的易忽略因素
- `Nacos -> quick_env` 的同步规则有新边界

## 12. 当前结论

到本轮为止，后续 AI 最重要的工作方式不是“继续堆 case”，而是保持这 4 条纪律：

- 真实链路优先
- 内容正确性优先
- 投影与聚合差异优先排查
- `Nacos` 与 `quick_env` 永远同步
