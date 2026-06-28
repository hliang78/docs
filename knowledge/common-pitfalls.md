# OneOPS 常见陷阱和解决方案

本文档记录 OneOPS 开发和测试中的常见问题模式，帮助快速定位和解决问题。

## 1. Bidi 通信相关

### 1.1 Controller 显示 offline 但实际在线

**症状：**
- `/api/v2/platform2/agent/controllers` 返回 controller 状态为 offline
- 但 controller 进程正常运行，日志显示连接成功

**根因：**
- `StoreBackedControllerInventoryService` 只读取数据库，未 overlay live session
- 或者 controller session 未写入 inventory 表

**解决方案：**
- 检查 `OneOPS/app/platform2/agent/controller/inventory.go` 的 overlay 逻辑
- 确认 controller 启动时调用了 `RegisterController`
- 参考：ISSUE-20260506-001

### 1.2 Bidi ack 收到但业务状态未更新

**症状：**
- Controller 返回 ack
- 但 attempt/ledger 状态仍为 pending 或 timeout_unknown

**根因：**
- Ack 只代表消息送达，不代表业务成功
- 缺少业务回调处理逻辑

**解决方案：**
- 不要把 ack 当作业务成功标志
- 必须等待明确的业务回调（如 ReportTaskOverview）
- 参考：Platform2 验收门禁第5条

## 2. 数据库相关

### 2.1 AutoMigrate 启动卡死

**症状：**
- OneOPS 启动时长时间无响应
- 日志停在 "Running AutoMigrate..."

**根因：**
- `mysql.autoMigrate: true` 会对所有表执行 AutoMigrate
- 大型项目表很多，AutoMigrate 耗时长

**解决方案：**
- 本地开发设置 `mysql.autoMigrate: false`
- 使用定向迁移脚本：`scripts/migrate_platform2_monitoring_metric_schema.go`
- 参考：gap matrix 第1节"本地 backend 联调基线"

### 2.2 Schema 漂移导致字段缺失

**症状：**
- API 返回 500
- 日志显示 "column not found: target_expression"

**根因：**
- 历史 schema 与当前 model 不一致
- 某些表缺少新增的字段

**解决方案：**
- 运行对应的迁移脚本
- 检查 `scripts/migrate_*.go` 是否有对应脚本
- 如果没有，手动执行 ALTER TABLE 或创建迁移脚本

## 3. 前端相关

### 3.1 调用旧 API 导致验收失败

**症状：**
- 功能正常工作
- 但 code review 时被拒绝

**根因：**
- 前端调用了 `/api/v1/*` 或 `@/api/platform/*` 旧 API
- 违反 platform2 硬约束

**解决方案：**
- 检查 import 语句，确保只使用 `@/api/platform2/*`
- 如果缺 platform2 API，显示阻塞页，不要调用旧 API
- 参考：Platform2 验收门禁第2、3条

### 3.2 Route deep-link 不工作

**症状：**
- 直接访问 URL 时页面显示空白或默认状态
- 从菜单点击进入正常

**根因：**
- 组件未实现 route-query 预填逻辑
- 或者 autoload 逻辑缺失

**解决方案：**
- 在 `mounted()` 或 `onMounted()` 中读取 `route.query`
- 根据 query 参数预填表单或触发数据加载
- 参考：`Platform2MonitoringWorkbench.vue` 的实现

## 4. Credential 相关

### 4.1 Credential 解析失败

**症状：**
- API 返回 "credential not found: demo-ssh-001"
- 或者 "credential resolver failed"

**根因：**
- 使用了不存在的 demo credential_ref
- 或者 credential_ref 格式不符合 platform2 规范

**解决方案：**
- 使用真实存在的 credential（如 SCT20251220000043）
- 或者先创建测试 credential
- 前端改用 credential picker，不要硬编码
- 参考：P0-1 阻塞项

## 5. 监控相关

### 5.1 Compile 成功但 apply 失败

**症状：**
- `/api/v2/platform2/monitoring/plans:compile` 返回 200
- `/api/v2/platform2/monitoring/plans:apply` 返回 500

**根因：**
- Compile 时未传 target_snapshot_json，使用了 stub resolver
- Apply 时使用真实 resolver，target 不存在

**解决方案：**
- 确保 target（agent/device/application）真实存在
- 或者使用 template-based auto compile，自动生成 material
- 参考：gap matrix 第1节"监控 bidi"

### 5.2 Snapshot 未触发同步

**症状：**
- Apply 成功
- 但 `platform2_metric_instance` 表无数据

**根因：**
- Apply 成功后未触发 snapshot sync
- 或者 snapshot sync 逻辑有 bug

**解决方案：**
- 检查 `monitoring/service/impl/apply.go` 的 snapshot 触发逻辑
- 确认 `ReportTaskOverview` 回调后调用了 `snapshot.Sync()`
- 参考：P0-3 阻塞项

### 5.3 仪表盘种子都在，但设备监控中心仍然不出盘

**症状：**
- `platform_teleabs_strategy_set_dashboard_binding` 已有绑定
- Grafana dashboard 种子也已存在
- 但 `/api/v1/platform/metrics/strategy/device-dashboards?target_part=...` 返回空

**根因：**
- 静态 `strategy_set -> dashboard` 绑定不等于设备已经关联到策略集
- 当前后端仍需要 `platform_monitoring_task_subject.subject_id -> strategy_set_id` 这层设备关联证据

**解决方案：**
- 先查目标设备是否已有 `platform_monitoring_task_subject` 记录
- 再查 binding 表是否覆盖对应 `strategy_set_id`
- 不要再优先怀疑旧的 runtime dashboard materialization 缺失
- 参考：`docs/knowledge/oneops-mvp-strategy-dashboard-seed-only-lessons-2026-06-17.md`

## 6. 性能相关

### 6.1 Agent 列表查询慢

**症状：**
- `/api/v2/platform2/agent/inventory` 响应时间 > 5s
- 数据量大时更明显

**根因：**
- 未建立索引
- 或者查询逻辑有 N+1 问题

**解决方案：**
- 在 `tenant_code`, `agent_code`, `status` 字段建立索引
- 使用 JOIN 代替循环查询
- 添加分页和过滤条件

### 6.2 前端首屏加载慢

**症状：**
- 首次打开页面需要 10s+
- Network 显示 bundle.js 很大

**根因：**
- 未做代码分割
- 或者引入了大型依赖（如 echarts 全量引入）

**解决方案：**
- 使用动态 import 做路由级代码分割
- 按需引入依赖（如 echarts 只引入需要的图表）
- 使用 vite-plugin-visualizer 分析 bundle

## 7. 测试相关

### 7.1 单元测试通过但集成测试失败

**症状：**
- 单元测试全部通过
- 但真实环境运行失败

**根因：**
- 单元测试使用了 mock，未覆盖真实场景
- 或者环境配置不一致

**解决方案：**
- 补充集成测试，使用真实依赖
- 确保测试环境与生产环境配置一致
- 使用 docker-compose 统一测试环境

### 7.2 USG `description` 元数据导致规则被静默跳过

**症状：**
- 配置可以编译
- 但运行时策略匹配或 NAT 复用像“少了一条规则”

**根因：**
- `description` 这类 metadata 子句被 lowerer 误判为 unsupported syntax
- 规则随后被标记为 `SkipRuntime`

**解决方案：**
- 检查 `v2/usgrt` lowerer 是否显式忽略 `description`
- 优先补真实配置 smoke test，不要先怀疑匹配算法
- 参考：`docs/knowledge/firewall-usg-example-skipruntime-patterns-2026-06-24.md`

### 7.3 SecPath `#` 分隔行导致复用规则不可见

**症状：**
- 精确匹配正常
- 但策略复用场景异常，系统误以为需要新建策略

**根因：**
- `security-policy` rule 下的 `#` 分隔行被当成 unsupported child
- 目标 rule 被静默排除出 runtime

**解决方案：**
- 检查 `v2/secpathrt` lowerer 是否把 `#` 视为可忽略内容
- 先看 rule 是否 `SkipRuntime=true`
- 参考：`docs/knowledge/firewall-usg-example-skipruntime-patterns-2026-06-24.md`

## 8. 运维环境相关

### 8.1 调整 inotify 后 Docker/Grafana 外部访问无响应

**症状：**
- 本机访问 `127.0.0.1:3000` 或宿主机 IP 的 `3000` 正常
- 外部访问 `http://<host-ip>:3000` 无响应
- `tcpdump` 只看到外部 SYN 进来，没有正常 SYN-ACK 回包

**根因：**
- `fs.inotify.max_user_watches` 本身不是原因
- 执行 `sysctl --system` 时重新加载了既有 `net.ipv4.ip_forward=0`
- Docker 发布端口的外部流量需要 IPv4 转发到容器网络，`ip_forward=0` 会导致转发失败

**解决方案：**
- 临时恢复：`sudo sysctl -w net.ipv4.ip_forward=1`
- 永久修复：确保 `/etc/sysctl.conf` 和 `/etc/sysctl.d/*.conf` 中不会再把 `net.ipv4.ip_forward` 覆盖为 `0`
- 参考：`docs/knowledge/docker-grafana-inotify-sysctl-ip-forward-2026-06-10.md`

## 使用方法

当遇到问题时：
1. 先在本文档搜索关键词
2. 如果找到类似问题，按照解决方案尝试
3. 如果未找到，创建新的 ISSUE 文件
4. 修复后，如果是通用问题，补充到本文档

## 维护规则

- 每10个类似问题，提取一个通用模式
- 每月回顾，删除过时的条目
- 保持简洁，每个问题 < 200 字
