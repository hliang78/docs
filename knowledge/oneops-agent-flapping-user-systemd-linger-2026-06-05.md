# OneOps Agent 轮流上下线排查经验：用户级 systemd 与 linger

日期：2026-06-05

## 背景

平台 Agent 列表中，以下两个远端 agent 长时间表现为不稳定，页面上看到它们轮流 online/offline：

- `agent-DVCCF3C11FF7D2B-f8cab20c`，`10.0.110.252`，`zq01-oneops-poc-02.novalocal`
- `agent-DVCC488229BB59E-bff1abbc`，`10.0.110.253`，`zq01-oneops-poc-03.novalocal`

本次重点分析 `10.0.110.252`。最终确认：这不是前端展示问题，也不是 Controller 拒绝连接，而是 agent 被部署成 `sy_cmsr` 的用户级 systemd 服务；该用户 `Linger=no`，SSH session 退出后 user manager 被 systemd-logind 停止，随之停止 `agent.service`，agent 收到 SIGTERM 并正常退出。

## 关键结论

`10.0.110.252` 的 agent 进程由用户级 systemd 管理：

```text
systemd,1
  -> systemd --user
      -> /home/sy_cmsr/app/agent/agent --config=/home/sy_cmsr/.config/agent/agent.yaml
```

服务文件：

```text
/home/sy_cmsr/.config/systemd/user/agent.service
```

用户状态：

```text
State=active
Sessions=3408
Linger=no
```

因此，当 `sy_cmsr` 没有登录 session 时，用户级 systemd 会退出，`agent.service` 也会被正常停止。日志中 agent 的 `signal=terminated` 正是这个停止动作触发的 SIGTERM。

## 平台侧现象与代码机制

平台 UI 展示来自 `platform_agent` 状态。Controller 每 30 秒向 OneOps 上报心跳，心跳中包含当前活跃 agent 列表。OneOps 平台收到心跳后，会把心跳列表中缺失的在线 agent 标记为离线，原因是 `not_in_heartbeat`。

关键代码位置：

- Controller 心跳上报 agent 列表：`/OneOPS/ctrlhub/controller/cmd/controller/main.go`
- OneOps 同步 Controller 心跳：`/OneOPS/OneOps/app/platform/service/impl/oneops_bidi_service.go`
- 心跳缺失置离线逻辑：`syncAgentsFromHeartbeat`

排查时日志中可以看到 Controller 心跳的 `agent_count` 变化：

```text
09:57:06 agent_count=3
09:59:06 agent_count=1
10:00:36 agent_count=2
10:03:36 agent_count=1
10:04:36 agent_count=2
```

当 `10.0.110.252` 的 agent service 随 user manager 停止后，Controller 心跳列表中缺少该 agent，平台就把它标记为离线。

## 排查过程

### 1. 先确认不是前端问题

查询平台数据库：

```bash
docker exec demo-core-mysql mysql -uroot -pUniOPS@Passw0rd UniOPS -e "
SELECT agent_code, controller_id, area, status, target_ip, address,
       last_heartbeat, offline_at, offline_reason, updated_at
FROM platform_agent
ORDER BY updated_at DESC;

SELECT controller_id, status, address, last_heartbeat, updated_at
FROM platform_controller
ORDER BY updated_at DESC;
"
```

典型结果：

```text
agent-DVCCF3C11FF7D2B-f8cab20c  offline  10.0.110.252  not_in_heartbeat
agent-DVCC488229BB59E-bff1abbc  offline  10.0.110.253  not_in_heartbeat
agent-001                       online   10.0.110.251
```

`offline_reason=not_in_heartbeat` 表明离线来自 Controller 心跳列表缺失，而不是 UI 自己判断。

### 2. 查看 Controller 心跳波动

```bash
tail -n 220 /OneOPS/OneOps/logs/oneops.log | \
  rg '处理Controller心跳|agent_count|ReportAgentMetadataBatch|collection_task_status_sync'
```

重点观察：

```text
处理Controller心跳 {"agent_count":1,"agent_list_size":1}
处理Controller心跳 {"agent_count":2,"agent_list_size":2}
处理Controller心跳 {"agent_count":3,"agent_list_size":3}
```

如果 `agent_count` 在 1/2/3 之间变化，说明 Controller 当前看到的 agent 连接集合不稳定。

### 3. 查看 Controller 7073 连接

在 Controller 所在节点执行：

```bash
ss -antp | rg ':7073\b|7073\b'
```

稳定状态应看到远端 agent 到 Controller 的连接，例如：

```text
[::ffff:10.0.110.251]:7073  [::ffff:10.0.110.252]:53952
```

若只看到本机 `agent-001`，说明远端 agent 当前未稳定连接到 Controller。

### 4. 分析 10.0.110.252 的 agent 日志

日志文件：

```text
/OneOPS/agent.log
/home/sy_cmsr/.local/log/agent/agent.log
```

提取生命周期事件：

```bash
rg -n '"msg":"(启动 Agent \(bidi\)|Agent启动成功|注册成功|收到信号，正在关闭|开始停止Agent|断开连接|Agent已停止|Agent关闭完成|连接成功建立|开始连接到目标|连接失败|重连失败)' \
  /OneOPS/agent.log
```

典型时间线：

```text
08:36:20 START
08:36:20 REGISTER_OK
08:36:35 TERMINATED
08:36:35 DISCONNECT

08:37:56 START
08:37:56 REGISTER_OK
08:38:53 TERMINATED
08:38:53 DISCONNECT

09:37:21 START
09:37:21 REGISTER_OK
09:42:43 TERMINATED
09:42:43 DISCONNECT
```

日志中没有 `connection refused`、`timeout`、`panic`、`OOM` 等异常，反复出现的是：

```text
"收到信号，正在关闭","signal":"terminated"
```

这说明 agent 是被外部 SIGTERM 正常停止，不是自己崩溃。

### 5. 排除系统级 service、root crontab、OOM

在 `10.0.110.252` 上执行：

```bash
systemctl status oneops-agent
journalctl -u oneops-agent --since "2026-06-05 08:30:00"
crontab -l
sudo crontab -l
dmesg -T | grep -i 'killed\|oom'
```

结果：

```text
Unit oneops-agent.service could not be found.
No entries.
no crontab for root
无 OOM/killed 记录
```

这说明 agent 不是系统级 `oneops-agent.service` 管理，也不是 root cron 或 OOM 导致。

### 6. 找 agent 父进程

```bash
ps -ef | grep agent
ps -fp <agent_ppid>
pstree -asp <agent_pid>
tr '\0' ' ' < /proc/<agent_ppid>/cmdline; echo
readlink -f /proc/<agent_ppid>/cwd
ls -l /proc/<agent_ppid>/fd/0 /proc/<agent_ppid>/fd/1 /proc/<agent_ppid>/fd/2
```

典型输出：

```text
sy_cmsr  2789187 2789180  /home/sy_cmsr/app/agent/agent --config=/home/sy_cmsr/.config/agent/agent.yaml

UID        PID      PPID CMD
sy_cmsr    2789180    1  /usr/lib/systemd/systemd --user

systemd,1
  -> systemd,2789180 --user
      -> agent,2789187 --config=/home/sy_cmsr/.config/agent/agent.yaml
```

这一步确认 agent 由 `sy_cmsr` 的用户级 systemd 管理。

### 7. 查找用户级 service

```bash
find /home/sy_cmsr -maxdepth 4 -type f | \
  xargs grep -n "app/agent\|agent.yaml\|oneops-agent" 2>/dev/null
```

关键结果：

```text
/home/sy_cmsr/.config/systemd/user/agent.service:12:WorkingDirectory=/home/sy_cmsr/app/agent
/home/sy_cmsr/.config/systemd/user/agent.service:18:ExecStart=/home/sy_cmsr/app/agent/agent --config=/home/sy_cmsr/.config/agent/agent.yaml
```

查看服务文件：

```bash
systemctl --user cat agent
```

关键配置：

```ini
[Service]
Type=notify
TimeoutStartSec=90
Restart=on-failure
RestartSec=5
ExecStart=/home/sy_cmsr/app/agent/agent --config=/home/sy_cmsr/.config/agent/agent.yaml

[Install]
WantedBy=default.target
```

### 8. 查看用户级 systemd 状态

```bash
systemctl --user status agent -l --no-pager
systemctl --user show agent \
  -p ActiveState -p SubState -p Result -p NRestarts \
  -p ExecMainPID -p ExecMainCode -p ExecMainStatus \
  -p Type -p Restart -p TimeoutStartUSec -p InvocationID
```

典型输出：

```text
ActiveState=active
SubState=running
Result=success
NRestarts=0
ExecMainStatus=0
Type=notify
Restart=on-failure
```

`NRestarts=0` 和 `Result=success` 说明 systemd 没有把它当失败重启处理。agent 是被正常 stop，因此 `Restart=on-failure` 不会生效。

### 9. 查系统日志确认 session 退出触发 stop

`journalctl --user -u agent` 可能没有记录，因为 user journal 未持久化或输出被重定向。直接看系统日志：

```bash
sudo journalctl --since "2026-06-05 08:30:00" -o short-iso | \
  grep -Ei 'agent.service|user@|sy_cmsr|session|systemd'
```

关键链路：

```text
08:36:18 sshd: Accepted password for sy_cmsr
08:36:18 Started User Manager for UID 1000
08:36:20 Starting UniOps Agent (bidi)
08:36:20 Started UniOps Agent (bidi)
08:36:25 pam_unix(sshd:session): session closed for user sy_cmsr
08:36:25 Session 3390 logged out
08:36:35 Stopping User Manager for UID 1000
08:36:35 Stopping UniOps Agent (bidi)
08:36:35 agent.service: Succeeded
08:36:35 Stopped UniOps Agent (bidi)
08:36:35 Stopped User Manager for UID 1000
```

后续 `08:37`、`09:37`、`09:43`、`09:49` 都是同样模式：SSH 登录时 user manager 启动，agent 跟着启动；SSH 退出后 user manager 被停止，agent 跟着停止。

最后确认 linger 状态：

```bash
loginctl show-user sy_cmsr -p Linger -p State -p Sessions
```

结果：

```text
State=active
Sessions=3408
Linger=no
```

这就是根因。

## 根因

`10.0.110.252` 的 agent 被部署为用户级 systemd 服务：

```text
/home/sy_cmsr/.config/systemd/user/agent.service
```

该服务挂在 `default.target` 下，依赖 `sy_cmsr` 的 user manager 生命周期。当前 `sy_cmsr` 用户 `Linger=no`，所以没有登录 session 时，`user@1000.service` 会被 systemd-logind 停止。

停止 user manager 时，systemd 正常停止 `agent.service`：

```text
Stopping UniOps Agent (bidi)
agent.service: Succeeded
Stopped UniOps Agent (bidi)
```

agent 收到 SIGTERM 后优雅退出，Controller 不再收到它的心跳，OneOps 平台在下一轮 Controller 心跳同步中把它标记为 `not_in_heartbeat` 离线。

## 解决方法

### 推荐方案：启用 linger

在目标节点上执行：

```bash
sudo loginctl enable-linger sy_cmsr

sudo -iu sy_cmsr systemctl --user daemon-reload
sudo -iu sy_cmsr systemctl --user enable --now agent

loginctl show-user sy_cmsr -p Linger -p State -p Sessions
```

期望结果：

```text
Linger=yes
```

然后退出 SSH，再验证 agent 仍然存活：

```bash
ps -ef | grep '/home/sy_cmsr/app/agent/agent'
ss -antp | grep 7073
```

在 Controller 节点确认连接仍存在：

```bash
ss -antp | rg '10\.0\.110\.252|:7073\b|7073\b'
```

在平台数据库确认状态稳定：

```bash
docker exec demo-core-mysql mysql -uroot -pUniOPS@Passw0rd UniOPS -e "
SELECT agent_code, status, target_ip, last_heartbeat, offline_at, offline_reason, updated_at
FROM platform_agent
WHERE target_ip IN ('10.0.110.252','10.0.110.253');
"
```

### 长期更稳方案：改为系统级 service

如果 agent 需要长期作为机器守护进程运行，建议部署为系统级 service，例如：

```text
/etc/systemd/system/oneops-agent.service
```

并使用 `User=sy_cmsr` 运行 agent。这样 agent 生命周期由系统级 systemd 管理，不依赖登录 session，也不需要依赖 user lingering。

示意：

```ini
[Unit]
Description=UniOps Agent (bidi)
After=network-online.target
Wants=network-online.target

[Service]
Type=notify
User=sy_cmsr
Group=sy_cmsr
WorkingDirectory=/home/sy_cmsr/app/agent
Environment="APP_LOG_DIR=/home/sy_cmsr/.local/log/agent"
Environment="LOG_DIR=/home/sy_cmsr/.local/log/agent"
Environment="AGENT_CODE=agent-DVCCF3C11FF7D2B-f8cab20c"
Environment="LOG_LEVEL=info"
ExecStart=/home/sy_cmsr/app/agent/agent --config=/home/sy_cmsr/.config/agent/agent.yaml
Restart=always
RestartSec=5
KillMode=mixed
KillSignal=SIGTERM
TimeoutStopSec=30

[Install]
WantedBy=multi-user.target
```

启用：

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now oneops-agent
sudo systemctl status oneops-agent -l --no-pager
```

## 建议同时检查 10.0.110.253

`10.0.110.253` 的表现与 `10.0.110.252` 类似，建议执行同样检查：

```bash
ps -ef | grep agent
pstree -asp <agent_pid>
systemctl --user cat agent
loginctl show-user sy_cmsr -p Linger -p State -p Sessions
sudo journalctl --since "2026-06-05 08:30:00" -o short-iso | \
  grep -Ei 'agent.service|user@|sy_cmsr|session|systemd'
```

如果也看到 `Linger=no` 和 `Stopping User Manager -> Stopping UniOps Agent`，同样执行：

```bash
sudo loginctl enable-linger sy_cmsr
sudo -iu sy_cmsr systemctl --user enable --now agent
```

## 经验沉淀

- agent 上下线问题先看平台数据库的 `offline_reason`，`not_in_heartbeat` 表示 Controller 心跳列表缺失。
- UI 在线状态不是根因来源，优先沿 `UI -> platform_agent -> Controller heartbeat -> Controller agent connections -> agent process` 链路排查。
- 看到 agent 日志里的 `signal=terminated` 时，不要先按崩溃处理，应先查 systemd、父进程和 session 生命周期。
- 用户级 systemd 服务默认跟随用户 session 生命周期；如果要无人值守运行，必须启用 `loginctl enable-linger <user>`，或改成系统级 service。
- `Restart=on-failure` 不能处理正常 stop。user manager 退出时，`agent.service` 是 `Result=success`，不会触发 failure restart。
- `journalctl --user -u agent` 没日志不代表 user systemd 没管理服务。若输出被重定向或 user journal 未持久化，应查系统日志中的 `user@UID.service`、`session` 和 `systemd-logind`。
- 多节点 agent 问题要分别查每台机器的部署方式。相同症状可能来自相同的 user lingering 配置缺失。
