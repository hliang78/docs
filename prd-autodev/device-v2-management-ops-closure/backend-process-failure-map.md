---
topic: device-v2-management-ops-closure
kind: full-stack
title: Device V2 采集与监控后端全过程失败地图
createdAt: 2026-05-21T14:20:00+0800
---

# Device V2 采集与监控后端全过程失败地图

## 1. 目的

这份文档专门回答你刚刚强调的关键点：

- 要覆盖前端可能需要承接的错误，不能只看前端已有摘要
- 必须深入到后端，沿着采集、继续纳管、监控推送的全过程，把真实失败点逐段拆出来

本文不直接给页面方案，而是先补一张“后端失败地图”，用于约束后续前后端协同表达。

## 2. 覆盖范围

本次重点覆盖三条真实主线：

1. `store/start -> pipeline -> task summary -> process_result`
2. `sync-to-v1 -> monitor push -> process_result`
3. `onboarding ensure -> monitoring dispatch -> log/snmp onboarding -> onboarding actions`

其中：

- 采集主线决定“设备能否被正式链路采到”
- `sync-to-v1` 和 `monitor push` 决定“监控推送链路是否能走通”
- `ensureOnboarding` 决定“继续纳管时前端还能看到哪些结构化失败动作”

## 3. 当前真实代码事实

### 3.1 采集入口并不只是一句 `store/start`

采集从 [StartStorePipeline](/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device/v2/api/device_v2.go:607) 进入。

在真正进入 pipeline 之前，后端先做两件事：

- [applyDeviceCollection2ProductionDefaults](/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device/v2/api/device_v2.go:280) 注入生产默认项
- [normalizeDeviceCollectionOptions](/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device/v2/api/device_v2.go:340) 做参数下线校验、SNMP/MIB 约束校验

这意味着采集链路的第一层失败，其实可能发生在“还没启动 pipeline”之前，例如：

- 使用了已下线选项
- 开启了 SNMP 但没有 `mib_tree_file`
- 运行时配置强制注入了 DC2 选项，但前端并不知道

这些失败今天会直接 `response.FailWithMsg(...)` 返回给前端，而不会进入后续 `task summary`。

### 3.2 正式链路的 DC2 目标和凭据引用来自设备属性拼装

DC2 目标是在 [deviceV2ToDC2Target](/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device_collection2/service/impl/device_collection2_run.go:1249) 里从设备 `attributes / metadata / labels` 拼出来的。

这里明确会读取：

- `in_band_ip / management_ip`
- `credential_ref_in_band`
- `credential_refs.in_band`
- `credential_refs.ssh`
- `snmp_credential_ref`
- `winrm_credential_ref`

这说明：

- 正式链路是否用到正确凭据引用，本身就是后端运行态问题，不只是前端文案问题
- 即使前端能展示设备当前保存的 `credential_ref_in_band`，也不等于已经证明“本次正式链路解析并使用成功”

### 3.3 `task summary` 是采集结果的二次整理层

[GetTaskSummary](/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device/v2/api/device_v2.go:683) 并不直接返回原始 pipeline 细节，而是：

1. 加载 task
2. 读取全部 store runs
3. 统计 observations
4. 调用 [buildMinimalStoreTaskSummary](/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device/v2/api/device_v2_store_minimal_api.go:539)
5. 为每台设备回写 `process_result`

这一步很重要，因为“前端今天看到的很多结果”其实已经是摘要层，不是原始执行层。

### 3.4 采集失败有两个最关键的压平点

第一个压平点在 [classifyCollectDecision](/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device/v2/api/device_v2_store_minimal_api.go:810)。

这里会把很多不同失败翻译成统一用户文案，例如：

- `D2_STORE_CONTROLLER_DETECT_FAILED` -> “设备探测失败，请检查连通性和账号后重试”
- `D2_STORE_RUNTIME_FAILED / D2_STORE_DC2_REQUIRED_FAILED` -> “采集执行失败，请联系运维处理”

第二个压平点在 [buildMinimalCollectionExecutionLayer](/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device/v2/api/device_v2_store_minimal_api.go:1012)。

这里认定“DC2 是否执行过”的条件非常窄：

- `status=success|partial`
- 或 `run_id` 非空
- 或 `facts / observation_count` 大于 0

否则就统一展示为：

- `headline = 本次未发起 DC2 采集`
- `message = 当前没有发现本次 DC2 采集执行记录`

这正是“发起过但失败了”和“根本没发起”会被压成同一表象的关键代码落点。

### 3.5 `last-store-collection-dc2` 更像采集入口，不是失败解释层

[GetLastStoreCollectionDC2](/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device/v2/api/device_v2_store_minimal_api.go:407) 只会选取 `device_collection2.run_id` 非空的最近一次 run。

它当前返回的核心字段只有：

- `task_id`
- `store_run_id`
- `dc2_run_id`
- `target_id`
- `contract_key`

这意味着：

- 它适合支持“查看最近一次采集详细数据”
- 不适合单独承担“为什么失败”的首层解释
- 某些失败 run 因为没有 `run_id`，甚至不会被它选中

### 3.6 `sync-to-v1` 和 `monitor push` 已经是独立失败面

[SyncToV1](/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device/v2/api/device_v2_sync_to_v1.go:182) 的真实流程是：

1. 遍历设备执行 [syncOneDeviceV2ToV1](/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device/v2/api/device_v2_sync_to_v1.go:600)
2. 为每台设备回写 `sync_to_v1_status / message`
3. 对成功拿到 `device_v1_code` 的设备，调用 [NotifyMonitorProbeByDeviceCodes](/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device/service/impl/device_store_service.go:363)
4. 再回写 `monitor_push_status / error`
5. 构建 [buildSyncToV1ProcessResult](/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device/v2/api/device_v2_sync_to_v1.go:273) 并回写 `process_result`

也就是说，这里天然至少有两层失败：

- `sync_to_v1` 本身失败
- `sync_to_v1` 成功后，`monitor push` 再失败

### 3.7 `syncOneDeviceV2ToV1` 自身还包含多段子失败

[syncOneDeviceV2ToV1](/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device/v2/api/device_v2_sync_to_v1.go:600) 内部会依次处理：

- 读取 `device_v2`
- 判断是否已有 `device_v1_code`
- 创建或回填 `device_v1`
- 绑定凭据
- 同步接口

所以它的失败并不是单点：

- 设备不存在
- 构建 `device_v1` 请求失败
- 创建 `device_v1` 失败
- 回填 `device_v1_code` 失败
- 凭据绑定失败
- 接口同步失败

这些失败会被 [classifySyncToV1Failure](/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device/v2/api/device_v2_sync_to_v1.go:464) 粗分成：

- 资料缺失
- 接口同步失败
- 凭据绑定失败
- 未知失败

### 3.8 `ensureOnboarding` 不是简单重放 toast，而是另一条完整后端流程

[EnsureOnboarding](/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device/v2/api/device_v2_onboarding_api.go:2181) 会进入 [ensureOnboardingForCode](/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device/v2/api/device_v2_onboarding_api.go:2198)。

真实步骤是：

1. [readLatestOnboardingRun](/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device/v2/api/device_v2_onboarding_api.go:209) 读取最近 store run
2. [composeOnboardingActions](/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device/v2/api/device_v2_onboarding_api.go:442) 合成已有动作
3. [ensureMonitoringDispatchOnboarding](/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device/v2/api/device_v2_onboarding_api.go:1942) 执行 `sync-to-v1 + monitor push`
4. [loadOnboardingConfig](/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device/v2/api/device_v2_onboarding_api.go:714) 解析日志纳管配置
5. [resolveManagedAreaListener](/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device/v2/api/device_v2_onboarding_api.go:1831) 解析 area listener
6. [ensureLogOnboarding](/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device/v2/api/device_v2_onboarding_api.go:2046) 承接 syslog/log forward
7. [ensureSNMPTrapTargetOnboarding](/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device/v2/api/device_v2_onboarding_api.go:2125) 承接 SNMP trap target
8. `persistOnboardingActions`

它返回给前端的不是单一报错，而是一组 `actions / blocked_actions / failed_actions / unknown_actions`。

### 3.9 controller-backed 证据已经相对丰富

[buildControllerBackedMonitoringAction](/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device/v2/api/device_v2_onboarding_api.go:403) 已经会把这些证据挂到 action evidence 上：

- `task_id`
- `store_run_id`
- `controller_stage`
- `store_run_status`
- `core_store_status`
- `manageable_status`
- `device_collection2`
- `decision`
- `store_summary`

这说明继续纳管场景并不是“后端没证据”，而是“前端当前没有把这组 evidence 前置成稳定结果区”。

## 4. 采集主线失败地图

| 阶段 | 代码入口 | 典型失败点 | 当前对前端的暴露方式 | 风险 |
| --- | --- | --- | --- | --- |
| 请求入参 | [normalizeDeviceCollectionOptions](/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device/v2/api/device_v2.go:340) | 已下线选项、SNMP 缺 MIB | 直接 HTTP fail | 不会进入 task summary，前端若只看 summary 会漏掉 |
| 启动 pipeline | [StartStorePipeline](/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device/v2/api/device_v2.go:607) | `EntityV2Srv` 未配置、启动失败 | 直接 HTTP fail | 前端不能假设一定有 task |
| 设备目标构造 | [deviceV2ToDC2Target](/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device_collection2/service/impl/device_collection2_run.go:1249) | 地址、凭据引用、SNMP/WinRM 参数不完整 | 多数体现在后续 run summary / controller 失败 | 前端若不展示接入摘要，会误导查错方向 |
| run 查询 | [GetTaskSummary](/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device/v2/api/device_v2.go:683) | run/observation 读取失败 | 直接 HTTP fail | 页面若只 toast，会丢失任务上下文 |
| 前置资料 | `buildCollectPrepareStep` | 缺少必填字段、身份不足 | `process_result.steps` 已结构化 | 这是当前最稳的一类错误 |
| controller 探测 | [classifyCollectDecision](/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device/v2/api/device_v2_store_minimal_api.go:810) | `D2_STORE_CONTROLLER_DETECT_FAILED` | 被翻译成“检查连通性和账号” | 容易误导为 SSH/网络问题 |
| DC2 执行 | [buildMinimalCollectionExecutionLayer](/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device/v2/api/device_v2_store_minimal_api.go:1012) | `status=failed` 但无 `run_id/facts` | 被压成“未发起 DC2” | 发起失败和未发起被混淆 |
| 结果写入 | `buildCollectPersistStep` | `D2_STORE_PERSISTENCE_FAILED` | `process_result` 有失败步 | 前端不应再让用户查设备侧 |
| 最近一次 DC2 入口 | [GetLastStoreCollectionDC2](/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device/v2/api/device_v2_store_minimal_api.go:407) | 失败 run 无 `run_id`，查不到 | 前端显示“没有最近一次 DC2” | 这不等于本次没有走到 DC2 相关阶段 |

## 5. 继续纳管 / 监控推送失败地图

| 阶段 | 代码入口 | 典型失败点 | 当前对前端的暴露方式 | 风险 |
| --- | --- | --- | --- | --- |
| 最近 run 读取 | [readLatestOnboardingRun](/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device/v2/api/device_v2_onboarding_api.go:209) | 无 DB、无最近 run | 直接 HTTP fail | 继续纳管连基础上下文都没有 |
| 结构化动作合成 | [composeOnboardingActions](/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device/v2/api/device_v2_onboarding_api.go:442) | persisted actions 解析/校验失败 | 直接 HTTP fail | 前端不能只依赖 toast |
| readiness 短路 | [ensureMonitoringDispatchOnboarding](/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device/v2/api/device_v2_onboarding_api.go:1942) | store readiness 还没成功 | action evidence 里标成 `v1_sync_status=skipped` / `monitor_push_status=skipped` | 若前端不展示 evidence，会看不出是“根本没进入推送” |
| sync-to-v1 | [syncOneDeviceV2ToV1](/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device/v2/api/device_v2_sync_to_v1.go:600) | 创建设备失败、回填失败、凭据绑定失败、接口同步失败 | action evidence / process_result | 若只看 monitor failed，会掩盖上游失败 |
| 缺少 `device_v1_code` | `ensureMonitoringDispatchOnboarding` | `sync-to-v1` 未返回 V1 code | action failed，`monitor_push_status=skipped` | 这是明确的上游阻断，不应显示成“监控推送失败” |
| monitor push 服务调用 | [NotifyMonitorProbeByDeviceCodes](/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device/service/impl/device_store_service.go:363) | store service 未配置、controller push 失败 | `monitor_push_status=failed` + `monitor_push_error` | 需要和 sync-to-v1 失败分层展示 |
| 日志纳管配置加载 | [loadOnboardingConfig](/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device/v2/api/device_v2_onboarding_api.go:714) | area 缺失、collector 缺失、collector 不在线 | blocked action | 当前可结构化，但前端没稳定展示 |
| area listener 解析 | [resolveManagedAreaListener](/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device/v2/api/device_v2_onboarding_api.go:1831) | plan 缺失、agent 缺失、不在线、能力不匹配 | blocked action | 这是平台配置面失败，不应引导用户查设备 SSH |
| syslog 设备侧纳管 | [ensureLogOnboarding](/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device/v2/api/device_v2_onboarding_api.go:2046) | listener 不完整、系统日志路径未知 | action failed / unknown | 前端需要把它和监控推送区分开 |
| SNMP trap 设备侧纳管 | [ensureSNMPTrapTargetOnboarding](/Users/huangliang/project/OneOPS-ALL/OneOPS/app/device/v2/api/device_v2_onboarding_api.go:2125) | trap listener 缺失、设备侧交付未完成 | action failed / blocked | 当前 evidence 很适合做结果卡 |
| onboarding actions 回写 | `persistOnboardingActions` | DB 保存失败 | 直接 HTTP fail | 前端会拿不到结构化动作，只剩接口错误 |

## 6. 当前错误信息落在哪里

现在的后端错误并不是只存在一个地方，而是分散在 5 种落点：

### 6.1 直接 HTTP 失败

特点：

- 接口当场失败
- 前端只能拿到错误字符串

典型环节：

- `store/start` 参数错误
- `task summary` 读取失败
- `ensureOnboarding` 读取最新 run 失败
- `persistOnboardingActions` 保存失败

### 6.2 `task summary.layers`

特点：

- 面向摘要展示
- 容易被压平

典型字段：

- `layers.core_store`
- `layers.collection_execution`
- `layers.collection_gap`

### 6.3 `process_result.steps`

特点：

- 比 `layers` 更结构化
- 已经有 `process / step / status / error_code / nextAction / details`

典型来源：

- `buildMinimalStoreRunProcessResult`
- `buildSyncToV1ProcessResult`

### 6.4 `onboarding actions.evidence`

特点：

- 对继续纳管最丰富
- 已经能表达 controller-backed、sync-to-v1、monitor push、log/snmp 侧失败

典型字段：

- `controller_stage`
- `store_run_status`
- `device_collection2`
- `v1_sync_status`
- `monitor_push_status`
- `listener_service_type`
- `reason`

### 6.5 设备 attrs/meta 回写结果

特点：

- 更像设备最近状态快照
- 适合右侧详情简明复核

典型字段：

- `sync_to_v1_status`
- `sync_to_v1_message`
- `monitor_push_status`
- `monitor_push_error`
- `process_result`

## 7. 当前前后端协同缺口

### 7.1 有结构化失败，但前端默认没有把它前置

最典型的是：

- `onboarding action evidence`
- `process_result.steps`

它们已经足够支撑“阶段 + 优先核对项 + 证据锚点”的展示，但当前 UI 仍主要依赖摘要和 toast。

### 7.2 有失败，但摘要层会把它压扁

最典型的是：

- `controller_detect_failed`
- `device_collection2.status=failed` 但没有 `run_id`

这意味着如果前端只信任 `layers.collection_execution.headline`，就会天然误导。

### 7.3 有静态凭据引用，但不等于有运行态使用证据

前端当前能展示设备保存的：

- `credential_ref_in_band`
- `credential_refs.*`

但如果后端不稳定返回“本次正式链路实际使用的接入摘要”，前端就只能展示“当前保存值”，不能冒充“本次运行态值”。

## 8. AI 推导建议

### 8.1 第一批前端不要只接一个来源

采集失败至少要综合：

- `task summary.process_result.steps`
- `task summary.layers`
- `selected store run.summary.device_collection2`
- `last-store-collection-dc2`

继续纳管失败至少要综合：

- `onboarding failed_actions / blocked_actions`
- `onboarding evidence`
- 设备 attrs/meta 上回写的 `sync_to_v1_status / monitor_push_status / process_result`

### 8.2 后端最好补一个“分层错误协同”最小契约

若要降低前端规则复杂度，后端最值得补的不是一堆新接口，而是稳定这几类字段：

- `stage`
- `reason_code`
- `next_check_items`
- `evidence`
- `correlation_ids`

尤其是采集链路，至少要避免把“DC2 失败”继续稳定压成“未发起 DC2”。

### 8.3 针对凭据引用问题，后端最值得补的是运行态接入摘要

结合当前运行态事实，采集场景里最有价值的证据不是泛化文案，而是：

- 本次正式链路目标地址
- 本次正式链路接入方式
- 本次正式链路凭据引用名
- controller / DC2 的失败 reason

如果这组字段稳定，前端就能把“优先核对 credential_ref”承接得非常准确；否则前端只能保守展示，不应假装已经定位根因。
