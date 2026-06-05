# Nvidia SMI Longest Path Test Design

## Objective

验证 `nvidia_smi` 监控能力的最长链路：

1. Teleabs 提供 `nvidia_smi` 模板。
2. OneOps 通过 `github.com/netxops/teleabs v0.0.26` 读取该模板。
3. 平台从策略/模板入口生成监控任务并下发到 agent。
4. Agent 上能查询到任务数据，且任务 TOML 内容正确。
5. Agent 实际执行该监控 input 后返回失败状态。

本轮不验证 Prometheus、VictoriaMetrics 或下游指标落库。

## Failure Model

使用确定性失败，而不是依赖测试机器是否安装 GPU 或 `nvidia-smi`：

- 模板使用 Telegraf `[[inputs.nvidia_smi]]`。
- 测试参数将 `bin_path` 设置为 `/tmp/oneops-nvidia-smi-missing`。
- Agent 应成功接收并保存任务。
- Agent 执行 input 时应报错，运行态应显示 `failed`，错误信息应包含调用该路径失败或找不到可执行文件的语义。

这样可以区分两类结果：

- 下发/解析失败：链路没有走到 agent 执行阶段，不符合本测试目标。
- 运行采集失败：链路走通，agent 执行插件后产生预期失败，符合本测试目标。

## Teleabs Changes

新增嵌入模板：

- `teleabs-templates/categories/infrastructure/system/nvidia_smi/nvidia_smi_basic.json`

模板要点：

- `id`: `nvidia-smi-basic`
- `plugin_type`: `nvidia_smi`
- `layer`: `basic`
- `collection_scope`: `local`
- `target_kind`: `system`
- 参数：`bin_path`、`timeout`、`interval`
- TOML 输出：

```toml
[[inputs.nvidia_smi]]
  bin_path = "{{.bin_path | default \"/usr/bin/nvidia-smi\"}}"
  timeout = "{{.timeout | default \"5s\"}}"
  interval = "{{.interval | default \"60s\"}}"
```

同时补充模板渲染测试，确认 `bin_path` 会进入最终 TOML。

Teleabs 变更提交到远端并打 tag：

- tag: `v0.0.26`
- OneOps `go.mod` 引用：`github.com/netxops/teleabs v0.0.26`

## Ctrlhub Agent Changes

Agent 需要能解析和运行 `[[inputs.nvidia_smi]]`：

- 在 `controller/agent/cmd/agent/main.go` 增加 Telegraf input 空白导入：
  - `github.com/influxdata/telegraf/plugins/inputs/nvidia_smi`
- 在 `SupportedTelegrafPluginsForTeleabs` 增加 `nvidia_smi`，用于能力上报和平台匹配。

补充 agent 侧解析测试：

- 使用 `TelegrafTaskManager.ApplyTask` 应用含 `[[inputs.nvidia_smi]]` 的 TOML。
- 断言任务保存成功，`PluginsInput` 包含 `nvidia_smi`。
- 不要求本地有真实 GPU。

## OneOps Changes

OneOps 只做版本引用和必要测试：

- `go.mod` / `go.sum` 从当前 teleabs 版本推进到 `v0.0.26`。
- 保留当前工作树中已有的其它 `go.mod/go.sum` 修改语义，仅更新 teleabs 版本。
- 补充模板 provider 测试，确认 OneOps 能通过 `TeleabsTemplateProvider` 读取 `nvidia-smi-basic`，且模板为 `local/system`。

## Longest Path Verification

真实链路验证步骤：

1. 启动或确认 OneOps、Controller、Agent 已在线。
2. 通过平台监控任务应用入口下发 `template_id=nvidia-smi-basic` 的任务。
3. 参数中设置：
   - `bin_path=/tmp/oneops-nvidia-smi-missing`
   - `timeout=1s`
   - `interval=10s`
4. 从 apply 响应记录 `agent_code` 与 `task_id`。
5. 查询 agent 任务详情，确认：
   - `found=true`
   - `plugins_input` 包含 `nvidia_smi`
   - `config` 包含 `[[inputs.nvidia_smi]]`
   - `config` 包含 `/tmp/oneops-nvidia-smi-missing`
6. 查询 runtime，确认：
   - status 为 `failed`
   - inputs 中对应 input 的 `ok=false`
   - `last_error` 非空，且指向 `nvidia_smi` 调用失败

## Acceptance Criteria

- Teleabs `go test ./...` 通过。
- Ctrlhub agent 相关测试通过。
- OneOps 相关 provider / apply 侧测试通过。
- `v0.0.26` tag 已推送到 `github.com/netxops/teleabs`。
- OneOps `go.mod` 引用 `github.com/netxops/teleabs v0.0.26`。
- 真实最长链路验证能证明任务已到 agent，且 agent 执行 `nvidia_smi` 产生预期失败。

## Out of Scope

- 不验证 Prometheus 或 VictoriaMetrics 数据。
- 不要求测试机有 NVIDIA GPU。
- 不新增 GPU 自动发现、资产建模或告警规则。
- 不修改 UI，除非现有 UI/API 无法选择该模板。
