# OneOps MVP 策略仪表盘极简种子方案经验

日期：2026-06-17

## 背景

本轮目标是验证一个更简洁的监控中心链路：

1. `quick_env` 直接预置策略集、策略、Grafana 仪表盘、`strategy_set -> dashboard` 绑定。
2. 不再依赖旧的 SNMP dashboard runtime materialization 分支能力。
3. 后端查询设备仪表盘时，只按设备关联到的策略集，再按静态绑定返回根仪表盘。

对应设计主线见：

```text
① 种子    quick_env 预置：策略集 + 策略 + 现成仪表盘 + strategy_set↔dashboard 绑定 + (record rule 手工/种子)
② 下发    选设备+策略集 → 生成 Telegraf → 推 agent → 写 StrategyApplyRecord(strategy_set_id ↔ 设备)
③ 展示    监控中心：选设备 → 查该设备的策略集 → 按绑定取盘 → Grafana 带 device 变量加载
```

## 关键结论

这条“极简种子”方案是可行的，但有一个不能省掉的前提：

- 可以去掉旧的“按 target_binding/runtime 再物化一套 dashboard 实例”的依赖。
- 不能去掉“设备最终要关联到策略集”这层事实来源。

换句话说：

- `策略集/策略/dashboard binding/record rule` 可以种子化。
- 设备是否能在监控中心查到仪表盘，仍然要依赖设备和策略集之间的运行时关联。

当前后端实现已经是这个模式：

- `ListDeviceBoundDashboardsByTargetPart` 会先找设备候选，再补查 `platform_monitoring_task_subject.strategy_set_id`。
- 找到策略集后，只按 `platform_teleabs_strategy_set_dashboard_binding` 返回根仪表盘。
- 返回结果中的 `match_reason` 为 `strategy_set_dashboard_binding`。

## 本次验证结果

### 1. clean smoke 环境可启动

对 clean 实例 `mvp-seed-integration-0617-fix` 执行完整启动后：

- `start.sh` 已打印“跳过旧版 target_binding 实例化，改走 strategy_set_dashboard_binding 静态绑定”。
- `validate.sh --instance mvp-seed-integration-0617-fix --timeout 5` 结果为 `PASS=64 FAIL=7`。

其中失败仍是历史噪音：

- 若干 `*:0` 外部端口检查
- `redis` 未鉴权导致 `NOAUTH`

这些不是本次种子简化方案引入的新问题。

### 2. 静态 binding 已落地，但设备默认还不会自动命中

clean 实例中已验证：

- `platform_teleabs_strategy_set_dashboard_binding` 中已有 `5` 条绑定
- `platform_monitoring_task_subject` 初始为 `0` 条

这说明：

- 仪表盘种子和静态绑定已经落库
- 但如果没有设备 -> 策略集关联，接口仍会返回空

### 3. 补最小 subject 关联后，接口返回正常

插入最小 smoke 数据后，接口已验证成功：

- `H3C-SW-01 -> 4284353d-1233-4022-ad18-871b3d8444c7 -> GDB20250418000001`
- `CISCO-SW-01 -> snmp_switch_routing_capable -> GDB20260617000001`

两次接口返回都命中：

```text
match_reason = strategy_set_dashboard_binding
```

## 容易误判的点

### 1. `strategy_set_dashboard_binding` 不等于“设备已经可见仪表盘”

很多时候看到 binding 表里有数据，就会以为前端一定能查到盘。

这不对。

设备要能命中仪表盘，至少还需要一层设备与策略集的关联证据。当前实现使用的是：

- `platform_monitoring_task_subject.subject_id`
- `platform_monitoring_task_subject.strategy_set_id`

如果这张表没有记录，监控中心查设备仪表盘仍可能是空结果。

### 2. record rule 不在 MySQL 业务表里

本次验证时容易误以为 record rule 应该存在于某张平台业务表，例如 `platform_teleabs_recording_rules`。

实际 quick env 里不是这样。

SNMP recording rule 当前落点是：

- `quick_env/config/vmalert/vmalert-rule.yml`
- Nacos 配置中的 `snmp_recording_rule_publisher`

因此判断“record rule 是否生效”时，先查 `vmalert-rule.yml` 和对应 runtime 挂载，不要先猜 MySQL 表缺失。

### 3. OneOPS API 认证头是 `X-Auth-Token`

本轮真实接口验证中，`Authorization: Bearer <token>` 返回“未登录或非法请求”。

正确方式是：

```bash
curl -sS -H "X-Auth-Token: <token>" \
  "http://127.0.0.1:8980/api/v1/platform/metrics/strategy/device-dashboards?target_part=H3C-SW-01"
```

## H3C CPU / Memory 对应关系

本次已确认 `quick_env` 中的 record rule 映射：

- `oneops:cpu_usage_direct:ratio`
  - `(snmp_cpu_usage / 100)`
  - `or (snmp_huawei_entity_state_hwEntityCpuUsage / 100)`
  - `or (snmp_h3c_entity_state_cpu_usage / 100)`
  - `or (snmp_maipu_system_cpu_usage / 100)`

- `oneops:memory_usage_direct:ratio`
  - `(snmp_memory_usage / 100)`
  - `or (snmp_huawei_entity_state_hwEntityMemUsage / 100)`
  - `or (snmp_h3c_entity_state_memory_usage / 100)`
  - `or (snmp_maipu_system_memory_usage / 100)`

因此 H3C 在 quick env 里走的是：

- `snmp_h3c_entity_state_cpu_usage`
- `snmp_h3c_entity_state_memory_usage`

## 对 quick_env / 后端分支的含义

这次结论可以直接指导分支收敛：

1. `quick_env` 新分支可以基于 `main` 保留“策略集 + 策略 + dashboard + binding + vmalert rule”这套种子化实现。
2. 旧 `snmp_metrics` 分支里那套依赖 `platform_teleabs_strategy_set_dashboard_target_binding` 的 legacy runtime materialization，不再是 MVP 主必需项。
3. 但新分支仍要保证设备最终能产生 `subject -> strategy_set` 关联，否则 UI 侧仍拿不到盘。

## 推荐排查顺序

以后如果遇到“种子都在，但监控中心不出盘”，按下面顺序判断：

1. 查 `platform_teleabs_strategy_set_dashboard_binding` 是否有目标策略集绑定。
2. 查 `platform_monitoring_task_subject` 是否存在目标设备的 `strategy_set_id`。
3. 直接调用 `/api/v1/platform/metrics/strategy/device-dashboards?target_part=...`，确认后端返回。
4. 如果接口空结果，再看设备元数据候选是否匹配 `subject_id`。
5. 如果是指标没数据，再去查 `quick_env/config/vmalert/vmalert-rule.yml` 和运行中的 `vmalert`。

## 相关文件

- `docs/superpowers/specs/2026-06-16-mvp-strategy-dashboard-simplification-design.md`
- `.codex-tmp/oneops-feature-device-v2-mvp-strategy-dashboard-simplification/app/platform/api/metric_strategy.go`
- `quick_env/config/vmalert/vmalert-rule.yml`
- `quick_env/init-configs/nacos/cipher-aes-start-config.yaml`
