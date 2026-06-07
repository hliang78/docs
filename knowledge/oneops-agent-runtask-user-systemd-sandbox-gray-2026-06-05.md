# OneOps Agent RunTask User Systemd Sandbox Gray Notes

## Context

2026-06-05 对 ctrlhub agent RunTask sandbox 做了方案 1 灰度：非 root agent 自动使用 `systemd-run --user`，避免用户级 systemd 服务内调用系统级 `systemd-run` 时触发 polkit 报错。

目标机器：

- `10.0.110.252`, `agent-DVCCF3C11FF7D2B-f8cab20c`
- `10.0.110.253`, `agent-DVCC488229BB59E-bff1abbc`

两台 agent 均运行在 `sy_cmsr` 的 user systemd 下：

```text
/home/sy_cmsr/.config/systemd/user/agent.service
/home/sy_cmsr/.config/agent/agent.yaml
/home/sy_cmsr/app/agent/agent
```

## Code Behavior

`SystemdTaskSandboxRunner` 根据 EUID 选择 systemd scope：

- `euid == 0`: system scope，执行 `systemd-run ...`
- `euid != 0`: user scope，执行 `systemd-run --user ...`

同样地，`StopTask` 在 user mode 下调用：

```bash
systemctl --user stop oneops-task-<task-id>.service
```

## Deployment-Agent Verification

正式 deployment-agent 链路已验证，不只是手工覆盖二进制：

```bash
/tmp/deployment-agent-user-sandbox \
  -deployment-id=gray-user-sandbox-252-1780637476 \
  -app-id=agent \
  -agent-code=agent-DVCCF3C11FF7D2B-f8cab20c \
  -controller-url=http://10.0.110.251:18080 \
  -operation=deploy \
  -package-url=http://10.0.110.251:18080/agent.zip
```

`10.0.110.253` 使用同样命令，deployment id 为 `gray-user-sandbox-253-1780637476`，agent code 为 `agent-DVCC488229BB59E-bff1abbc`。

两台部署日志均完成到：

```text
setup_service
start_service
State transition ... to completed
deployment-agent completed successfully
```

并且 `start_service` 日志中明确为：

```text
Starting service {"service": "agent", "user_unit": true}
```

## Rendered Config

deployment-agent 自动渲染出的 `~/.config/agent/agent.yaml` 包含生产 sandbox 默认值：

```yaml
task_sandbox:
  enabled: true
  backend: "systemd"
  allow_legacy_fallback: false
  memory_max: "1G"
  cpu_quota: "100%"
  tasks_max: 256
  runtime_max_sec: 1800
  unit_prefix: "oneops-task"
```

这说明正式部署链路会固化 sandbox 默认值；前一次手工补 YAML 只是因为当时绕过了 deployment-agent，直接替换了远端二进制。

## RunTask Evidence After Deployment

deployment-agent 正式部署后再次下发 shell RunTask：

- `10.0.110.252`: `ecf97a75-c4de-4c5c-a1a6-436a1ed90b24`
- `10.0.110.253`: `3677eb79-b890-445a-91a6-46bba8851256`

平台任务日志断言结果：

```text
marker=true
sandbox=true
unit=true
uid1000=true
polkit_error=false
```

关键输出包含：

```text
Running as unit: oneops-task-<task-id>.service
[agent] 进程执行完成: command=sh sandbox=oneops-task-<task-id>.service
1000
```

未出现：

```text
Interactive authentication required
```

## Root/System Scope Evidence

同日进一步用 `sudo -n` 在两台机器上执行 root deployment-agent，验证 root agent 仍走 system scope。

临时 root agent code：

- `10.0.110.252`: `agent-root-sandbox-252`
- `10.0.110.253`: `agent-root-sandbox-253`

root deployment-agent 日志显示：

```text
Starting service {"service": "agent", "user_unit": false}
deployment-agent completed successfully
```

root agent 配置路径和工作目录：

```text
/etc/agent/agent.yaml
/opt/agent
/var/log/agent/agent.log
```

root agent 启动日志显示 `agent_code=agent-root-sandbox-*`，并成功 `RegisterAgent`。

root RunTask 验证任务：

- `10.0.110.252`: `04051e88-f215-4f0a-b5e9-0d208f5a65c1`
- `10.0.110.253`: `87a6a9af-06a9-4f55-b569-5ff6df746013`

平台任务日志断言结果：

```text
marker=true
sandbox=true
unit=true
uid0=true
polkit_error=false
```

关键点：

- `id -u` 输出为 `0`，证明任务由 root agent 执行。
- 日志包含 `Running as unit: oneops-task-<task-id>.service`。
- 未出现 `Interactive authentication required`。
- 结合 root deployment `user_unit=false` 与代码中的 `euid == 0` 分支，确认 root agent 使用 system scope，不带 `--user`。

测试结束后，已用 root deployment-agent `uninstall` 清理临时 system agent：

```text
root-sandbox-cleanup-252-1780638533
root-sandbox-cleanup-253-1780638533
```

清理后确认：

```text
system=inactive
user=active
stderr-empty
```

## Notes

- 当前验证包为 `agent-v0.0.1-119-g38e48d5-dirty.zip`，因为本地代码尚未提交。
- `make package-agent` 产物使用 `-s -w`，远端 agent 二进制大小约 `99930296` 字节；手工构建包曾约 `140024771` 字节，大小差异来自构建参数。
- 这两台 openEuler/systemd 243/cgroup v1 机器上，`RuntimeMaxSec` 和 `TasksMax` 有效；`MemoryMax` 可见 RSS 限制，但 memsw 行为受 cgroup v1/swap 限制影响。

## Next Release Steps

1. 提交 agent sandbox user-mode 代码和测试。
2. 用非 dirty commit 重新打包。
3. 再跑一次 deployment-agent deploy 和 RunTask 断言。
4. 将 user/system scope 灰度证据纳入发布说明。
