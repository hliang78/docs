# CC Connect Codex Weixin Sessions

这套最小集成把 `cc-connect` 的微信远程聊天和本地 `codex` 线程做了一层显式会话映射，目标是让远程开发具备可管理的生命周期，而不是只靠“当前聊天上下文还在不在”。

## 能力

- 远程会话开启：为当前微信聊天创建一个逻辑开发会话。
- 持续开发中的检查点：随时记录当前进展，避免上下文丢失后只能凭记忆恢复。
- 会话关闭：显式结束当前逻辑会话并保存最后摘要。
- 会话恢复：在新的 Codex 线程里读取旧会话摘要，继续同一个远程开发任务。

## 脚本

使用：

```bash
/Users/huangliang/project/OneOPS-ALL/scripts/cc-codex-session.sh
/Users/huangliang/project/OneOPS-ALL/scripts/cc-codex-weixin-router.sh
/Users/huangliang/project/OneOPS-ALL/scripts/cc-codex-alias-entry.sh
/Users/huangliang/project/OneOPS-ALL/scripts/install-cc-connect-session-router.sh
```

常用命令：

```bash
scripts/cc-codex-session.sh 新建 修复 Device V2 登录问题
scripts/cc-codex-session.sh 状态
scripts/cc-codex-session.sh 记录 已定位到 controller 返回字段缺失，下一步补接口契约
scripts/cc-codex-session.sh 关闭 已完成接口修复与 typecheck，待浏览器复验
scripts/cc-codex-session.sh 恢复 最近 再补一轮浏览器验证并整理最终结论
scripts/cc-codex-session.sh 列表 5
```

## 远程微信命令约定

推荐把下面这些命令发给远程 Codex 会话：

```text
会话 新建 <任务>
会话 状态
会话 记录 <阶段摘要>
会话 关闭 [最终摘要]
会话 恢复 最近 [补充要求]
会话 恢复 <session-id> [补充要求]
会话 列表 [数量]
```

含义：

- `会话 新建`：绑定当前微信聊天到一个逻辑开发会话。
- `会话 记录`：刷新检查点，供后续恢复使用。
- `会话 关闭`：结束逻辑会话，但不删除历史。
- `会话 恢复`：在新的 Codex 线程中载入旧会话摘要，继续同一开发主线。

## 路由器

`cc-codex-weixin-router.sh` 模仿 `openclaw-weixin-router.sh` 的风格：

```bash
printf '%s\n' '会话 状态' | scripts/cc-codex-weixin-router.sh
```

退出码约定：

- `0`：命令已确定性处理，stdout 可直接回微信。
- `2`：不是 `会话` 控制命令，应回退给模型继续自然语言对话。
- `64`：路由器调用方式错误。

这使远程微信会话可以先走“命令优先、模型兜底”的入口，而不是把所有输入都交给模型判断。

## cc-connect 前置接线

`cc-connect` 自身支持：

- `[[commands]]`：把聊天命令直接映射到本地 shell
- `[[aliases]]`：把首词匹配的自然语言重写成目标命令

因此这套集成可以做到真正的“前置命令改写”：

```text
会话 新建 修复登录问题
  -> alias: 会话 => /ccsession
  -> exec: scripts/cc-codex-alias-entry.sh 新建 修复登录问题
  -> router: scripts/cc-codex-weixin-router.sh --message "会话 新建 修复登录问题"
  -> session manager: scripts/cc-codex-session.sh 新建 修复登录问题
```

安装：

```bash
scripts/install-cc-connect-session-router.sh
```

查看状态：

```bash
scripts/cc-connect-session-router-status.sh
```

安装脚本会：

- 备份当前 `~/.cc-connect/config.toml`
- 追加一个托管的 `ccsession` exec command
- 追加 `会话` / `SESSION` / `session` 三个别名
- 运行 `cc-connect config format`

## 状态文件

状态保存在：

```text
docs/cc-connect/state/sessions/*.json
```

每个会话记录以下核心字段：

- `id`：逻辑会话 ID
- `session_key`：`cc-connect` 当前远程聊天键
- `codex_thread_id`：首次绑定的 Codex 线程
- `active_codex_thread_id`：当前继续工作的 Codex 线程
- `task`：主任务
- `status`：`open` / `resumed` / `closed`
- `last_summary`：最后一次检查点摘要
- `notes[]`：阶段性记录

## 推荐工作流

1. 用户在微信里说：`会话 新建 修复某问题`
2. Codex 开始工作，阶段结束时执行：`会话 记录 ...`
3. 本轮完成后执行：`会话 关闭 ...`
4. 下次在新聊天里说：`会话 恢复 最近 ...`

这样即使远程聊天断开，逻辑开发会话也能被新的 Codex 线程接住。

## 自测

可以运行：

```bash
scripts/cc-codex-router-smoke.sh
```

它会验证：

- `会话 命令`
- `会话 新建`
- `会话 状态`
- `会话 记录`
- `会话 关闭`
- `会话 恢复 最近`
- 普通自然语言是否正确回退到模型
