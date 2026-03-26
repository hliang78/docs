# OneOps 日志规范提案（讨论稿）

本文档对 OneOps 相关项目的日志现状做了梳理，并给出统一的日志规范建议，便于后续落地与迁移。**请先阅读并反馈意见，再进入实施阶段。**

## 统一日志项目：onelog

已新增**独立日志库** `onelog`（`/onelog`），作为平台内**唯一**日志实现，供 OneOps、netlink、ctrlhub 等所有项目依赖，便于基于日志做故障判断与可观测。

- **仓库内路径**：`OneOPS-ALL/onelog/`
- **模块名**：`github.com/netxops/onelog`
- **能力**：统一配置（LogConfig）、Init/Global、WithModule、SmartSampler、LogLevelController（动态级别）
- **使用说明**：见 [onelog/README.md](../onelog/README.md)

各项目在 `go.mod` 中增加 `replace github.com/netxops/onelog => ../onelog`（或实际相对路径）后，统一通过 `onelog.Init` 初始化、`onelog.Global()` 或注入的 Logger 打日志。

---

## 一、现状分析

### 1.1 涉及的代码范围

| 区域 | 日志方式 | 说明 |
|------|----------|------|
| **OneOps 主应用** | `app.Logger`（zap）、`initialize.InitZapEnhanced` | 已接入增强日志（采样、动态级别、JSON/Console） |
| **netlink** | `zap.L()`、`log.Printf`/`log.Println`、`fmt.Println`/`fmt.Printf`、`PipelineLogger`/`ContextLogger` | 多种方式混用 |
| **ctrlhub** | 自建 zap 增强、`pkg/logger`、agent 独立 logger | 与 OneOps 类似但独立实现 |
| **独立小工具/CLI** | `log.Fatal`、`fmt.Printf`、部分 zap | 如 validate_template、sync_etcd、onvif_tool、capture 等 |

### 1.2 已具备的能力（OneOps 主应用）

- 统一使用 **zap**，通过依赖注入 `app.Logger`
- **增强配置**：`pkg/logger` 支持 JSON/Console、文件轮转、采样、动态级别、模块级别
- **文档**：`OneOps/pkg/logger/README.md`、`OneOps/docs/LOGGING_INTEGRATION_SUMMARY.md`

### 1.3 存在的问题

1. **入口不统一**
   - 主流程用 `app.Logger`，netlink 部分用 `zap.L()`、标准库 `log`、`fmt`，导致无法统一配置与采样。
   - `main.go` 中同一语义既打 `app.Logger` 又打 `fmt.Println`，重复且不利于采集。

2. **无统一日志格式约定**
   - 消息文案风格不一（中英混用、有的带 emoji、有的不带）。
   - 结构化字段命名不统一（如 `listen_addr` vs `port` vs `addr`）。
   - 缺少公认的“事件类型”或“模块”字段，不利于检索与告警。

3. **级别使用不统一**
   - 哪些算 INFO / WARN / ERROR 没有成文规则，DEBUG 使用场景也未统一。

4. **底层/子模块未统一**
   - netlink 中 `log.Printf`、`fmt` 直接输出，不经过 zap，无法享受级别、采样、轮转和统一格式。

5. **敏感信息与体积**
   - 未明确禁止在日志中输出密码、token、完整配置等；部分调试日志可能带大量 payload，影响体积与合规。

---

## 二、规范目标

- **可观测**：通过固定字段（如 level、ts、module、event、msg）便于检索与告警。
- **可配置**：级别、输出、采样、轮转统一由配置控制，不散落各处。
- **可维护**：新代码有明确规则可循，旧代码有迁移指引。
- **性能与成本**：通过采样与级别控制控制日志量与 I/O。

---

## 三、建议的日志标准

### 3.1 日志级别定义

| 级别 | 用途 | 示例 |
|------|------|------|
| **DEBUG** | 仅开发/排查时需要，生产默认不输出 | 解析细节、循环内每条记录、中间变量 |
| **INFO** | 关键业务/生命周期事件，生产默认输出 | 服务启动/停止、配置加载完成、任务开始/结束、重要状态变更 |
| **WARN** | 可恢复的异常或预期内的异常分支 | 重试成功、缺省值、过期接口调用、限流命中 |
| **ERROR** | 需要关注的失败，可能影响功能 | 请求失败、外部调用失败、持久化失败、业务校验失败 |
| **Fatal/DPanic** | 仅用于进程启动失败等不可恢复场景，尽量少用 | 配置缺失、必要依赖连不上导致退出 |

**原则**：  
- 不滥用 INFO，避免“正常心跳/轮询”刷屏。  
- 错误原因与上下文用 ERROR 一次说清，避免只打 WARN 导致漏告警。

### 3.2 统一结构化字段（JSON 输出时）

建议每条日志都尽量包含：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `ts` | string (ISO8601) | 是 | 由 logger 自动注入 |
| `level` | string | 是 | debug/info/warn/error |
| `msg` | string | 是 | 简短、稳定、可读的一句话描述 |
| `caller` | string | 可选 | 由 zap 配置决定 |
| `module` | string | 建议 | 模块/领域，如 `platform.deployment`、`netlink.pipeline`、`auth` |
| `event` | string | 建议 | 事件类型，如 `service_start`、`task_failed`、`config_loaded` |

**扩展字段**（按需）：  
- 请求/任务：`request_id`、`task_id`、`device_id`、`platform_id` 等。  
- 耗时：`duration_ms` 或 `duration`（与现有 zap Duration 一致）。  
- 错误：`error`（建议用 zap.Error(err)）。  

**命名**：统一 **snake_case**，与现有 `zap.String("listen_addr", ...)` 一致。

### 3.3 消息文案（msg）约定

- **语言**：建议统一中文或统一英文；若保留中文，至少保证 `event`/关键字段英文便于脚本/告警。
- **风格**：陈述句、过去式或完成态，如“启动完成”“任务执行失败”。
- **避免**：在 msg 中堆大量动态信息，应放到结构化字段。
- **避免**：在 msg 中写敏感信息（密码、token、完整密钥）。

示例：

```text
msg: "OneOps Bidi 服务启动成功"   event: "service_start"   listen_addr: ":8080"
msg: "部署任务执行失败"           event: "deployment_failed"   task_id: "xxx"   error: "..."
```

### 3.4 模块（module）划分建议

便于按模块过滤和做模块级日志级别控制（与现有 `module_levels` 一致）：

- `bootstrap`：启动、配置加载、信号处理  
- `platform.deployment`：部署相关  
- `platform.agent`：Agent 相关  
- `platform.collection`：采集任务  
- `netlink.pipeline`：管道执行（若纳入统一 logger）  
- `auth` / `security`：登录、权限、证书  
- `api`：HTTP/gRPC 请求（若在中间件打日志）  
- `storage` / `db`：存储、DB、缓存  

具体模块列表可在落地时按目录/包再细化并写入规范。

### 3.5 采样与性能

- **高频日志**（如同一 key 下重复的 DEBUG/INFO）：必须经采样器或限速，避免刷屏。  
- 使用现有 `GlobalSampler` 或模块内等价逻辑，键名稳定（如 `skip_numeric_field`），便于聚合。  
- ERROR 不采样，保证每条都落盘。

### 3.6 禁止与不推荐

- **禁止**：在日志中输出密码、API Key、Token、证书内容、完整配置（含密钥）。  
- **不推荐**：同一语义同时打 Logger 和 `fmt.Println`/`log.Print`，只保留 Logger。  
- **不推荐**：在非 CLI 业务代码中直接使用 `log`、`fmt` 做业务日志，应统一走 zap（或项目约定的 Logger 抽象）。

---

## 四、技术实现建议（供讨论）

### 4.1 统一入口

- **OneOps 主应用**：继续以 `app.Logger` 为唯一业务日志出口；启动/信号等也仅用 `app.Logger`，去掉重复的 `fmt.Println`。  
- **netlink**：若作为库被 OneOps 调用，建议通过接口注入 Logger，而不是内部使用 `zap.L()` 或 `log`；独立运行的 netlink 二进制可自建 zap 并复用同一套格式与配置约定。  
- **ctrlhub**：视是否与 OneOps 合并部署，决定是复用 OneOps 的 logger 配置还是对齐字段与级别定义。

### 4.2 注入与模块名

- 在创建 Logger 时或中间件里为每个包/模块绑定 `module`（如 `logger.With(zap.String("module", "platform.deployment"))`），避免每行手写。  
- 现有 `pkg/logger` 的 `module_levels` 可与该 `module` 字段对应，实现按模块调级别。

### 4.3 配置与兼容

- 保持现有 `LogConfig`（级别、格式、轮转、采样、`module_levels`）作为统一配置源。  
- 生产默认：`level: info`，`format: json`，采样开启；开发/调试可通过环境变量或 API 临时调高级别。

### 4.4 迁移顺序建议

1. **文档与规范**：确定本文档终稿（级别、字段、模块、禁止项）。  
2. **主应用**：去掉 main 中与 Logger 重复的 fmt/log，补充 `module`/`event` 等关键字段。  
3. **高频与敏感**：检查并加上采样、脱敏。  
4. **netlink/ctrlhub**：按“统一入口”逐步改为注入 Logger 或对齐格式与级别。

---

## 五、需要您确认的点

1. **范围**：规范是否先只约束 **OneOps 主应用**，还是希望一并覆盖 **netlink**、**ctrlhub**？  
2. **msg 语言**：统一中文、统一英文，还是“msg 中文 + event/字段英文”？  
3. **module 粒度**：是否采用“大模块（如 platform）+ 子域（如 deployment）”的两级命名（如 `platform.deployment`）？  
4. **敏感信息**：除“禁止密码/token”外，是否需要明确“可打/不可打”的配置项或环境变量列表？  
5. **迁移优先级**：是否同意先做 main 去重 + 关键路径补全字段，再逐步推广到 netlink/其他子项目？  

确认或修改以上几点后，可以据此定稿《OneOps 日志规范》并进入实施（含具体修改清单和示例补丁）。若你希望，我也可以根据你的选择直接生成一版精简的“终版规范”和 checklist，便于贴在仓库或 Wiki。
