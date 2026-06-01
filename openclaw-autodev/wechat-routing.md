# OpenClaw Weixin Agent-Loop Routing

更新时间：2026-05-15

本文件只描述 OpenClaw 自带的 `openclaw-weixin` channel。`openclaw-weixin`
账号应绑定到 `main` agent。`main` 只作为微信入口路由器，不作为 PF3、D2 或
CT 的持续开发执行者。

微信可以继续用自然语言聊天，但会触发持续开发、测试、停止、清理的消息必须使用
明确前缀。没有前缀的消息一律视为普通对话，不得启动、停止、修复或继续任何
agent loop。

## Blocked 快捷回复

收到 `运行阻塞` 消息后，优先直接回复下面任一行：

```text
<任务> 现场
<任务> 继续 <已处理原因>
<任务> 修阻塞 [一句说明，可省略]
<任务> 放开限制
<任务> 停止
```

说明：

- `继续`：当前阻塞已处理，直接继续调度当前 story。
- `修阻塞`：创建独立 repair agent 处理卡点，不复用业务 worker。
- `放开限制`：按任务预设的默认开发范围自动批准，比手写 `同意 <范围>` 更省事。
- 只有需要精细审批时，才使用 `同意 <具体范围>` 或 `同意 --profile ...`。

## Deterministic First

微信入站消息先经过：

```bash
/Users/huangliang/project/OneOPS-ALL/scripts/openclaw-weixin-router.sh
```

固定命令由脚本直接执行并回复，不进入大模型：

```text
openclaw-weixin inbound
  -> openclaw-weixin-router.sh
      -> matched: run the mapped local control script, send stdout to Weixin, stop
      -> not matched: exit 2, continue to main agent/model
```

脚本先匹配固定控制前缀，再动态读取当前
`docs/openclaw-autodev/loops/*.conf` 和 `docs/openclaw-autodev/stories/*.json`
中的 task-id。未带合法前缀、普通自然语言、或脚本无法确定语义的消息，才交给
`main` agent 模型判断。这样控制面不会再依赖模型是否加载了路由文档，也不会因为
main 会话长上下文而阻塞 `PF3 状态` / `PF3 现场` 这类查询。

长任务命令必须避免阻塞微信入站线程：`PF3 修复`、`POOL 启动`、`LOOP 启动` 由
脚本后台提交并立即返回日志路径。查询类命令同步执行，但回复需要保持短文本；超长
输出截断，完整内容进入 `state/` 或 `logs/`。

## Prefix Contract

前缀必须出现在消息第一行开头，大小写不敏感，前缀后接空格和指令：

```text
<PREFIX> <COMMAND> [自然语言补充说明]
```

合法前缀：

| Prefix | Scope | Meaning |
| --- | --- | --- |
| `PF3` | `platform3` | Platform3 自动开发、状态、修复、审批 |
| `D2` | `d2` group | D2 前后端一起控制 |
| `D2FE` | `d2-fe` | Device V2 前端 |
| `D2BE` | `d2-be` | Device V2 后端 |
| `CT` | `ct` | 持续测试/验证 |
| `POC` | `poc-ct` | OneOps PoC 关注方向探索驱动测试 |
| `POOL` | task pool | 动态任务池启动、同步、状态、停止 |
| `LOOP` | `all` | 全部 agent loop 的清理、状态、停止 |
| `REPAIR` | independent repair agent | 独立临时修复 agent，专门处理 BLOCKED/运行/契约/环境问题 |
| `TASK` / `任务` | dynamic task address | 用 `TASK <task-id> <COMMAND>` 访问任意当前 OpenClaw task |
| `<task-id>` | dynamic task prefix | 直接用当前 task-id 或其无符号形式作为前缀，例如 `d2-fe 状态`、`D2FE 状态` |

新增探索类 loop 前缀可以通过
`docs/openclaw-autodev/weixin-prefixes.json` 扩展；固定 router 会先查该文件，
再映射到 `loops/<task-id>.conf`。当前 `POC`、`POCCT`、`POC-CT` 都映射到
`poc-ct`。

动态 task prefix 来自当前存在的 `loops/<task-id>.conf` 或
`stories/<task-id>.json`。router 同时支持：

```text
<task-id> 状态
<task-id-without-symbols> 状态
TASK <task-id> 状态
任务 <task-id> 状态
```

例如当前存在 `d2-fe` 时，`d2-fe 状态`、`D2FE 状态`、`TASK d2-fe 状态`
都会路由到 `scripts/openclaw-agent-loop.sh status d2-fe`。已归档且不在当前
`loops/` 或 `stories/` 中的任务不会作为动态当前任务出现。

## Command Mapping

```text
命令              -> 返回已测试常用只读微信命令
帮助              -> 返回已测试常用只读微信命令
TASK <任务> 命令   -> 返回该任务已测试常用只读命令
TASK <任务> 状态   -> scripts/openclaw-agent-loop.sh status <任务>
TASK <任务> 进度   -> scripts/openclaw-task-progress.mjs <任务>
TASK <任务> 现场   -> scripts/openclaw-agent-loop.sh detail <任务>

PF3 命令          -> 返回 PF3 已测试常用只读命令
PF3 启动          -> scripts/openclaw-agent-loop.sh enable platform3
PF3 状态          -> scripts/openclaw-agent-loop.sh status platform3
PF3 可信状态      -> scripts/openclaw-agent-loop.sh truth-status platform3
PF3 进度          -> scripts/openclaw-task-progress.mjs platform3
PF3 修复          -> scripts/openclaw-agent-loop.sh start platform3
PF3 现场          -> scripts/openclaw-agent-loop.sh detail platform3
PF3 交接          -> scripts/openclaw-agent-loop.sh handoff platform3
PF3 阻塞分类      -> scripts/openclaw-agent-loop.sh blocker platform3
PF3 状态收敛      -> scripts/openclaw-agent-loop.sh reconcile platform3
PF3 Daemon报告    -> scripts/openclaw-agent-loop.sh daemon-report platform3
PF3 诊断          -> scripts/openclaw-agent-loop.sh provider-check platform3
PF3 重试 <原因>   -> scripts/openclaw-agent-loop.sh retry platform3 <原因>
PF3 同意 <范围>   -> scripts/openclaw-agent-loop.sh approve platform3 <范围>
PF3 拒绝 <原因>   -> 保持 APPROVAL，不恢复调度；回复已记录/可重新审批
PF3 停止          -> scripts/openclaw-agent-loop.sh disable platform3
PF3 归档 [说明]   -> scripts/openclaw-archive-task.sh platform3 [说明]

D2 命令           -> 返回 D2 已测试常用只读命令
D2 启动           -> scripts/openclaw-agent-loop.sh enable d2
D2 状态           -> scripts/openclaw-agent-loop.sh status d2
D2 可信状态       -> scripts/openclaw-agent-loop.sh truth-status d2
D2 进度           -> scripts/openclaw-task-progress.mjs d2
D2 修复           -> scripts/openclaw-agent-loop.sh start d2
D2 现场           -> scripts/openclaw-agent-loop.sh detail d2
D2 交接           -> scripts/openclaw-agent-loop.sh handoff d2
D2 阻塞分类       -> scripts/openclaw-agent-loop.sh blocker d2
D2 状态收敛       -> scripts/openclaw-agent-loop.sh reconcile d2
D2 Daemon报告     -> scripts/openclaw-agent-loop.sh daemon-report d2
D2 重试 <原因>    -> scripts/openclaw-agent-loop.sh retry d2 <原因>
D2 同意 <范围>    -> scripts/openclaw-agent-loop.sh approve d2 <范围>
D2 停止           -> scripts/openclaw-agent-loop.sh disable d2
D2 归档           -> 拒绝执行；D2 是 group target，请使用 D2FE 归档 或 D2BE 归档

D2FE 命令         -> 返回 D2FE 已测试常用只读命令
D2FE 启动         -> scripts/openclaw-agent-loop.sh enable d2-fe
D2FE 状态         -> scripts/openclaw-agent-loop.sh status d2-fe
D2FE 可信状态     -> scripts/openclaw-agent-loop.sh truth-status d2-fe
D2FE 进度         -> scripts/openclaw-task-progress.mjs d2-fe
D2FE 修阻塞 [说明] -> scripts/openclaw-repair-agent.sh start d2-fe [说明]
D2FE 修复         -> scripts/openclaw-agent-loop.sh start d2-fe
D2FE 现场         -> scripts/openclaw-agent-loop.sh detail d2-fe
D2FE 交接         -> scripts/openclaw-agent-loop.sh handoff d2-fe
D2FE 阻塞分类     -> scripts/openclaw-agent-loop.sh blocker d2-fe
D2FE 状态收敛     -> scripts/openclaw-agent-loop.sh reconcile d2-fe
D2FE Daemon报告   -> scripts/openclaw-agent-loop.sh daemon-report d2-fe
D2FE 重试 <原因>  -> scripts/openclaw-agent-loop.sh retry d2-fe <原因>
D2FE 同意 <范围>  -> scripts/openclaw-agent-loop.sh approve d2-fe <范围>
D2FE 停止         -> scripts/openclaw-agent-loop.sh disable d2-fe
D2FE 归档 [说明] -> scripts/openclaw-archive-task.sh d2-fe [说明]

D2BE 命令         -> 返回 D2BE 已测试常用只读命令
D2BE 启动         -> scripts/openclaw-agent-loop.sh enable d2-be
D2BE 状态         -> scripts/openclaw-agent-loop.sh status d2-be
D2BE 可信状态     -> scripts/openclaw-agent-loop.sh truth-status d2-be
D2BE 进度         -> scripts/openclaw-task-progress.mjs d2-be
D2BE 修阻塞 [说明] -> scripts/openclaw-repair-agent.sh start d2-be [说明]
D2BE 修复         -> scripts/openclaw-agent-loop.sh start d2-be
D2BE 现场         -> scripts/openclaw-agent-loop.sh detail d2-be
D2BE 交接         -> scripts/openclaw-agent-loop.sh handoff d2-be
D2BE 阻塞分类     -> scripts/openclaw-agent-loop.sh blocker d2-be
D2BE 状态收敛     -> scripts/openclaw-agent-loop.sh reconcile d2-be
D2BE Daemon报告   -> scripts/openclaw-agent-loop.sh daemon-report d2-be
D2BE 重试 <原因>  -> scripts/openclaw-agent-loop.sh retry d2-be <原因>
D2BE 同意 <范围>  -> scripts/openclaw-agent-loop.sh approve d2-be <范围>
D2BE 停止         -> scripts/openclaw-agent-loop.sh disable d2-be
D2BE 归档 [说明] -> scripts/openclaw-archive-task.sh d2-be [说明]

CT 命令           -> 返回 CT 已测试常用只读命令
CT 启动           -> scripts/openclaw-agent-loop.sh enable ct
CT 状态           -> scripts/openclaw-agent-loop.sh status ct
CT 可信状态       -> scripts/openclaw-agent-loop.sh truth-status ct
CT 进度           -> scripts/openclaw-task-progress.mjs ct
CT 修复           -> scripts/openclaw-agent-loop.sh start ct
CT 现场           -> scripts/openclaw-agent-loop.sh detail ct
CT 交接           -> scripts/openclaw-agent-loop.sh handoff ct
CT 阻塞分类       -> scripts/openclaw-agent-loop.sh blocker ct
CT 状态收敛       -> scripts/openclaw-agent-loop.sh reconcile ct
CT Daemon报告     -> scripts/openclaw-agent-loop.sh daemon-report ct
CT 重试 <原因>    -> scripts/openclaw-agent-loop.sh retry ct <原因>
CT 同意 <范围>    -> scripts/openclaw-agent-loop.sh approve ct <范围>
CT 停止           -> scripts/openclaw-agent-loop.sh disable ct
CT 归档 [说明]    -> scripts/openclaw-archive-task.sh ct [说明]

POC 命令          -> 返回 POC 已测试常用只读命令
POC 启动          -> scripts/openclaw-agent-loop.sh enable poc-ct
POC 状态          -> scripts/openclaw-agent-loop.sh status poc-ct
POC 可信状态      -> scripts/openclaw-agent-loop.sh truth-status poc-ct
POC 进度          -> scripts/openclaw-task-progress.mjs poc-ct
POC 修复          -> scripts/openclaw-agent-loop.sh start poc-ct
POC 现场          -> scripts/openclaw-agent-loop.sh detail poc-ct
POC 交接          -> scripts/openclaw-agent-loop.sh handoff poc-ct
POC 阻塞分类      -> scripts/openclaw-agent-loop.sh blocker poc-ct
POC 状态收敛      -> scripts/openclaw-agent-loop.sh reconcile poc-ct
POC Daemon报告    -> scripts/openclaw-agent-loop.sh daemon-report poc-ct
POC 诊断          -> scripts/openclaw-agent-loop.sh provider-check poc-ct
POC 重试 <原因>   -> scripts/openclaw-agent-loop.sh retry poc-ct <原因>
POC 同意 <范围>   -> scripts/openclaw-agent-loop.sh approve poc-ct <范围>
POC 停止          -> scripts/openclaw-agent-loop.sh disable poc-ct
POC 归档 [说明]   -> scripts/openclaw-archive-task.sh poc-ct [说明]

POOL 命令         -> 返回 POOL 已测试常用只读命令
POOL 启动         -> scripts/openclaw-agent-loop.sh pool start
POOL 状态         -> scripts/openclaw-agent-loop.sh pool status
POOL 进度         -> scripts/openclaw-task-progress.mjs all
POOL 同步         -> scripts/openclaw-agent-loop.sh pool sync
POOL 监控         -> scripts/openclaw-agent-loop.sh monitor status
POOL Daemon报告   -> scripts/openclaw-agent-loop.sh daemon-report all
POOL 阻塞策略     -> scripts/openclaw-agent-loop.sh blocker-policy
POOL 监控刷新     -> scripts/openclaw-agent-loop.sh monitor once
POOL 现场 <任务>  -> scripts/openclaw-agent-loop.sh monitor detail <任务>
POOL 停止         -> scripts/openclaw-agent-loop.sh pool stop
POOL 常驻安装     -> scripts/openclaw-agent-loop.sh resident install
POOL 常驻状态     -> scripts/openclaw-agent-loop.sh resident status
POOL 常驻停止     -> scripts/openclaw-agent-loop.sh resident stop
POOL 常驻卸载     -> scripts/openclaw-agent-loop.sh resident uninstall
POOL 归档 <任务> [说明] -> scripts/openclaw-archive-task.sh <任务> [说明]

LOOP 命令         -> 返回 LOOP 已测试常用只读命令
LOOP 状态         -> scripts/openclaw-agent-loop.sh status all
LOOP 可信状态     -> scripts/openclaw-agent-loop.sh truth-status all
LOOP 进度         -> scripts/openclaw-task-progress.mjs all
LOOP 监控         -> scripts/openclaw-agent-loop.sh monitor status
LOOP Daemon报告   -> scripts/openclaw-agent-loop.sh daemon-report all
LOOP 阻塞策略     -> scripts/openclaw-agent-loop.sh blocker-policy
LOOP 停止         -> scripts/openclaw-agent-loop.sh stop all
LOOP 清理         -> scripts/openclaw-agent-loop.sh cleanup all
LOOP 启动         -> scripts/openclaw-agent-loop.sh daemon all
LOOP 归档 <任务> [说明] -> scripts/openclaw-archive-task.sh <任务> [说明]

REPAIR 命令       -> 返回独立修复命令帮助
REPAIR 启动 D2FE [说明] -> scripts/openclaw-repair-agent.sh start d2-fe [说明]
REPAIR 启动 D2BE [说明] -> scripts/openclaw-repair-agent.sh start d2-be [说明]
REPAIR 启动 PF3 [说明]  -> scripts/openclaw-repair-agent.sh start platform3 [说明]
REPAIR 启动 CT [说明]   -> scripts/openclaw-repair-agent.sh start ct [说明]
REPAIR 启动 POC [说明]  -> scripts/openclaw-repair-agent.sh start poc-ct [说明]
<任务> 修阻塞 [说明] -> scripts/openclaw-repair-agent.sh start <task> [说明]
REPAIR 状态 [id]  -> scripts/openclaw-repair-agent.sh status [id|latest]
REPAIR 现场 [id]  -> scripts/openclaw-repair-agent.sh detail [id|latest]
REPAIR 列表       -> scripts/openclaw-repair-agent.sh list
REPAIR 停止 [id]  -> scripts/openclaw-repair-agent.sh stop [id|latest]
REPAIR 关闭 [id]  -> scripts/openclaw-repair-agent.sh close [id|latest]
```

## Natural Language Rules

- `帮我看看 D2 怎么样`：普通对话，只能回答或建议，不得执行命令。
- `命令` / `帮助` / `PF3 命令`：命令，返回已测试常用只读命令清单；不展示未验证或会改变调度状态的命令。
- `TASK d2-fe 状态` / `d2-fe 状态`：命令，动态路由到当前 task `d2-fe`。
- `TASK dev-docs 状态`：只有当前存在 `loops/dev-docs.conf` 或
  `stories/dev-docs.json` 时才是命令；如果 `dev-docs` 已归档，会回复
  `TaskNotFound`，不得由模型猜测或恢复任务。
- `D2 状态`：命令，必须执行对应 status。
- `PF3 进度` / `D2FE 任务进度`：命令，返回 story 总数、已完成、剩余、完成率、当前 story、最近完成项、下一项、loop 运行状态、provider 状态和最后报告摘要。
- `D2FE 启动 重点处理导入页类型错误`：命令，启用 `d2-fe` 调度；补充说明只作为上下文。
- `D2FE 停止`：命令，禁用 `d2-fe` 调度并停止已运行 daemon。
- `D2FE 归档 本轮完成`：命令，先禁用 `d2-fe` 调度，再把
  `loops/d2-fe.conf`、`stories/d2-fe.json`、`evidence/d2-fe/`、
  `state/d2-fe/` 中存在的产物移动到
  `docs/openclaw-autodev/archive/d2-fe-<timestamp>/`，并写入 `MANIFEST.md`。
  归档不是删除；需要恢复时由人工根据 manifest 手动移回。`D2 归档` 会被拒绝，
  因为 `D2` 是 group target，容易误收整个 D2 队列。
- `POC 启动`：命令，启用 `poc-ct` 探索驱动测试 loop；它执行
  `oneops-poc-concern-autotest` 的 flow mapping、薄弱环节分级和后续探针设计，
  不复用 `CT` 的持续健康检查 shell loop。
- `POC 修复`：命令，单次运行 `poc-ct` 当前可选 story；适合人工确认后立即推进一轮。
- `POOL 启动`：命令，启动动态任务池 supervisor；新增或移除 `loops/*.conf` 后由任务池自动同步。
- `LOOP 归档 dev-docs 本轮已完成` / `POOL 归档 dev-docs 本轮已完成`：命令，归档指定 task-id；适合归档动态新增的
  loop 或没有固定微信前缀的任务。
- `POOL 监控`：命令，查看任务池持续监控报告；`POOL 监控刷新` 会立即扫描一次。
- `PF3 现场` / `POOL 现场 PF3`：命令，返回手机可读的短现场；完整事件明细写入
  `docs/openclaw-autodev/state/<task>/work-detail.txt`，避免微信长消息刷屏。
- `REPAIR 启动 D2FE`：命令，创建独立临时 repair agent，自动读取目标 loop 的
  status/blocker/recovery-decision/daemon/detail/handoff/story 上下文，并生成默认
  修复说明；专门修复 BLOCKED/运行/契约/环境问题；不复用 `d2-fe` agent，不进入业务
  story 队列，也不会自动启用或重试原 loop。修复证据写入
  `docs/openclaw-autodev/state/repair/<repair-id>/`。可追加简短说明来覆盖默认重点，
  例如 `REPAIR 启动 D2FE 只检查 daemon 重启问题`。
- `REPAIR 关闭 <repair-id>`：命令，停止并删除临时 repair agent；保留 repair
  状态、prompt、run log 和 summary，便于复盘。
- 监控里只有 `Working activity=agent-child children=...openclaw...openclaw-agent`
  才代表任务有真实执行证据；`WorkingNoOutput` 表示 agent 子进程存在但当前
  turn 输出仍为空，`DaemonIdle`、`WaitingForSchedule`、`StaleLock`
  或 `NoRecentActivity` 都不能视为健康开发。
- `PF3 现场` 会读取 `docs/openclaw-autodev/state/<task>/progress.json`。该文件由
  controller 脚本写入，用于确定性识别 `Starting`、`Working`、`PromptStuck`、
  `ToolStuck`、`SessionEnded` 等状态；不要让大模型判断运行控制面是否卡死。
- `progress.json` 同时记录 `contextTokens` / `contextWindowTokens` /
  `promptTokens` / `totalTokens`。`contextWindowTokens` 是模型/harness 窗口容量，
  不是单轮真实消耗；判断告警只看活跃上下文。main 微信入口不承担固定命令上下文，
  固定命令必须脚本短路；worker 每个 bounded turn 使用新 session，通过
  state/evidence 文件交接，避免长会话堆积。
- worker 默认采用激进轮换：每个 block 只跑一个短 turn，结束后 controller 写入
  `docs/openclaw-autodev/state/<task>/handoff.md`；下一轮新 worker 必须先读 handoff，
  再读项目文档和 evidence。长期记忆由
  `scripts/openclaw-autodev-memory.sh` 的本地 SQLite/FTS 索引提供，必要时 worker
  用 `search <task> <ticket-or-topic>` 查询，不能靠 main 或旧 worker 长上下文续命。
- 如果看到 `AdoptedWorking activity=adopted-session adopted=<session>`，
  表示本地 daemon 已接管 OpenClaw 中仍在运行的旧 session；此时用
  `traceAge` / `traceEvent` 判断真实进展，`localRawSize=0b` 只是旧 CLI
  stdout 文件，不代表没有真实运行。
- `POOL 常驻安装`：命令，安装 OpenClaw resident task；OpenClaw gateway 可用时自动持续同步任务池。
- `继续修复 PF3`：普通对话，不得执行；应提示使用 `PF3 修复`。
- `同意` / `继续` / `停止`：普通对话，除非上一条明确是同一个前缀任务的审批问题。
- 审批回复必须带前缀和明确范围，例如
  `PF3 同意 只允许 single target canary 的设计和只读验证，不允许 commit mode`。
  Router 必须把范围原文写入 `approve` 命令，下一轮 worker 会在 prompt 中看到
  `Operator approval context`。
- 可使用审批模板生成明确范围，例如
  `D2BE 同意 @safe-difference DVCE5B9B461254F platform_code null -> PLT20231020012 已人工接受`。
  模板只生成审批文本，不绕过删除、写库、生产配置、auth/tenant/credential、依赖、
  commit/push 或外部集成红线。可用 `LOOP 审批模板` 查看本地模板。
- 可使用通用授权 profile 简化长审批文本，例如
  `D2ON 授权 discovery-readonly`、`D2ON 授权 remote-readonly 192.168.100.7`。
  Profile 定义位于 `docs/openclaw-autodev/approval-profiles.json`，授权账本位于
  `docs/openclaw-autodev/state/approvals/<task>.json`。可用 `<任务> 授权列表`
  查看可用 profile，`<任务> 授权状态` 查看当前账本，`<任务> 授权撤销 <profile>`
  撤销授权。Profile 只授权能力范围，不携带密钥；凭据、token、cookie、SNMP
  community、私钥和密码仍必须通过本机运行时渠道提供，不得写入仓库文件或 evidence。
- `BLOCKED` / `APPROVAL` 告警里的 `NextApproval:` 是已经渲染好的建议审批回复，
  以任务前缀和 `同意` 开头；只能在确认现场证据后整行复制发送，不得当作无条件同意。
  如果 Ticket 无法精确匹配 story 队列，告警必须显示占位符，例如
  `[story-title-not-found-in-queue]`，不得回退到旧 current-story。
- `PF3 拒绝 <原因>` 不恢复调度，只回复已保持审批等待；如要停止调度使用
  `PF3 停止`。

## Router Rules

- 所有 sustained development 命令必须调用 `scripts/openclaw-agent-loop.sh`。
- 所有 `归档` 命令必须调用 `scripts/openclaw-archive-task.sh`；该脚本只做可恢复归档，
  不直接删除任务产物。
- Router 必须动态识别当前 OpenClaw task：`loops/*.conf` 和 `stories/*.json`
  中存在的 task-id 可以直接作为微信前缀，也可以通过 `TASK <task-id>` 访问。
- 动态路由只表示“当前任务存在”，不表示任务已启用；是否调度仍以
  `openclaw-agent-loop.sh status <task>` 和 loop config 的 `ENABLED` 为准。
- `main` 作为微信入口路由器，只解析首行前缀、执行对应 loop 命令、返回短状态。
- `main` 不得在自己的 direct chat context 中实现 PF3、D2 或 CT 的业务开发。
- `platform3`、`d2-fe`、`d2-be` 是 loop worker agent，由
  `scripts/openclaw-agent-loop.sh start|daemon` 按需创建；它们不直接绑定微信。
- `repair-*` 是一次性独立修复 agent，由
  `scripts/openclaw-repair-agent.sh start <task>` 创建；它只处理 loop 阻塞问题，
  不作为持续开发 worker，不绑定微信，完成后可用 `REPAIR 关闭 <id>` 删除 agent。
- 任务池以 `docs/openclaw-autodev/loops/*.conf` 为准：文件新增即入池，但只有
  enabled 的任务可被调度；文件移除后 `POOL` supervisor 必须停止对应 loop 并删除
  不再使用的 worker agent。
- `启动/停止` 对业务任务表示 `enable/disable` 调度开关；`修复` 才是单次
  `start` 执行。
- 常驻模式由 `resident install` 安装 launchd service；它不使用 cron，只在
  OpenClaw gateway 可用时同步任务池；明确 `POOL 常驻停止/卸载` 前保持存在。
- 不带合法前缀的消息不得启动、继续、停止、修复、清理任何 loop。
- 前缀不合法或指令不明确时，只回复可用前缀和示例，不执行命令。
- 微信汇报必须短，细节写入 evidence 或 loop state。
- worker 返回 `LoopControl: APPROVAL` 或 `LoopControl: BLOCKED` 时，loop
  controller 必须复用最近的 `main` direct 微信 session，通过
  `openclaw agent --deliver` 主动发送一条审批/阻塞通知。不要用外部
  `openclaw message send --channel openclaw-weixin`，该路径缺少微信
  `contextToken` 时可能返回 message id 但不会实际送达。通知只发一次；后续由
  带前缀的微信回复恢复或停止调度。
- `APPROVAL` 通知必须给“同意 <具体范围> / 拒绝 / 停止”示例；`BLOCKED` 通知
  必须给“现场 / 阻塞分类 / 状态收敛 / 重试或 REPAIR / 停止”示例。不要在技术阻塞时
  把主要动作写成“同意”，否则会诱导用户用审批命令处理 harness 卡死、
  PromptStuck、ToolStuck 等技术问题。
- `状态`、`现场`、`阻塞分类` 会自动执行状态收敛；显式 `状态收敛` 用于修复
  loop state、`last-control`、`current-story.json` 和 story lane 的分裂。
- `可信状态` 审计 runtime、story queue、business next 三层状态；当 story 队列
  完成但最新 `Next` 仍要求继续业务链时，必须输出 `Accuracy=Conflict` 和最小
  `RequiredAction`，不得直接宣称业务完成。
- `阻塞分类` 必须区分自动化框架、环境、业务授权、业务优化和未知。业务优化允许先
  调整 story 的 `scope`、`acceptance`、`validation`、`allowedPaths`、`lanes` 或
  `dependsOn`，再进入最小业务修复；业务授权只能等待明确审批或最小范围停止。
- `Daemon报告` 返回 daemon supervisor 独立报告；`阻塞策略` 返回 BLOCK ticket
  pattern 策略表。两者是只读命令。
- `REPAIR` 生命周期必须写 append-only events：submitted、started、finished、
  blocked、restart-prevented、stopped、stop-noop、closed。
