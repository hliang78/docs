# 自动化脚本执行高风险命令门禁 P0 设计

> 日期：2026-06-17
> 范围：OneOps 平台内 `Script Studio / Task Center` 自动化任务主链路
> 子仓库：`OneOPS-ALL` 当前工作区
> 状态：设计待用户评审

---

## 1. 目标与边界

本设计只解决一个 P0 问题：

> **在 OneOps 平台内的自动化脚本执行主链路上，前置拦截已知高风险命令，避免危险脚本进入试跑或任务执行流程。**

已与用户对齐的边界如下：

- 仅覆盖 `Script Studio / Task Center` 主链路。
- 不覆盖 `remote/run`、`config_execute`、controller session、agent 旁路执行入口。
- P0 采用 **黑名单优先**。
- 命中规则后 **直接阻断**，不进入审批分流。
- 规则先以内置默认集落地，但必须支持 **通过配置扩展**，不能把规则写死在分散代码里。

P0 北极星：

> **任何命中已知高风险命令规则的脚本，在 Script Studio 试跑前或模板进入可执行状态前即被阻断。**

---

## 2. 现状与问题

当前 OneOps 已经具备一批“执行前校验”，但它们主要集中在以下方向：

- 参数、JSON、凭据引用、敏感字段检查。
- 模板激活态、校验态、指纹新鲜度检查。
- `TaskExecutionProfile` 对审批、提权、凭据材料可得性的判断。
- controller / agent 末端对 `require_approval / deny` 的执行期拦截。

当前缺口是：

1. **没有预置的高风险命令黑白名单。**
2. **没有统一的“脚本内容策略门禁”。**
3. **平台主链路不会因为脚本中出现危险命令而前置失败。**
4. **高风险命令治理在现有设计里被留给上层 agent 或人工控制，不是平台内建能力。**

这意味着，只要脚本在参数、凭据、模板状态上合法，它仍可能带着 `rm -rf`、`shutdown`、`userdel`、`mkfs` 之类的高风险命令进入试跑或后续执行链路。

---

## 3. 设计原则

P0 设计遵循四条原则：

1. **统一门禁，不做入口散弹式校验。**
   - 避免把同一套规则分散到 `Script Studio`、`Task Center`、模板发布等多个函数中。

2. **前置阻断，不依赖末端执行失败。**
   - 用户应在试跑或模板校验阶段就收到明确错误，而不是等 controller / agent 才失败。

3. **默认内置，配置可扩展。**
   - P0 不做数据库规则管理界面，但规则结构必须支持后续接配置中心或数据库。

4. **只做高信号规则，不做复杂语义推理。**
   - P0 优先覆盖明显高危命令，不在第一阶段引入完整的只读白名单或脚本语义分析引擎。

---

## 4. 总体方案

推荐方案：**统一 `ScriptExecutionPolicyGate`。**

平台侧新增一个统一组件：

```text
ScriptExecutionPolicyGate
  ├─ RuleProvider
  ├─ ContentExtractor
  ├─ Matcher
  └─ DecisionBuilder
```

职责：

- 输入：脚本内容、脚本类型、入口上下文。
- 输出：`allow / deny`，以及命中规则详情。

P0 不把这套能力挂到 `TaskExecutionProfile` 上，原因是：

- `TaskExecutionProfile` 当前聚焦凭据、审批、提权、材料解析。
- 命令内容治理属于另一条业务维度。
- 若复用 `ExecutionProfile` 承载 P0 直接阻断，错误路径会更绕，试跑报错也不够直观。

因此 P0 选择：**在平台侧新增独立门禁组件，前置拦截。**

---

## 5. 调用点设计

P0 只挂两个调用点，并明确主次关系。

### 5.1 Script Studio 试跑前校验

在 `Script Studio` 测试执行链路中，调用 `ScriptExecutionPolicyGate` 检查当前 draft 内容。

推荐挂点：

- `app/platform/service/impl/script_studio.go`
- 在构建测试执行 envelope 之前完成校验。

行为：

- 命中高风险规则：直接返回业务错误，不创建测试任务。
- 未命中：继续走现有的 inventory、credential、parameter、auth policy 校验链路。

这样用户在试跑入口就能获得清晰反馈，避免“任务已创建但执行失败”的体验。

### 5.2 Task Template 校验 / 发布前校验

在模板校验链路中引入同一套策略门禁。

推荐挂点：

- `app/platform/service/impl/task_template_v2.go`
- 与现有模板 validation status / fingerprint 治理合并处理。

行为：

- 模板内容命中高风险规则：模板校验失败，不能进入可执行态。
- 模板内容未命中：保留现有校验逻辑与校验记录更新方式。

这一步是 `Task Center` 侧的主防线。因为当前任务创建链路已经要求模板处于有效校验态，所以只要模板侧被拦住，Task Center 基于该模板的正常执行就会被一并拦住。

P0 对 `Task Center` 的覆盖范围限定为：

- **基于任务模板的主执行路径**

P0 不承诺覆盖：

- 纯临时 inline script / 原始 envelope 直提交流程
- 不依赖模板校验态的旁路任务创建方式

### 5.3 本期不新增的调用点

P0 明确不接入以下入口：

- `POST /api/v1/remote/run`
- `POST /api/v1/config_execute`
- controller session 执行
- agent 直接执行
- 纯临时 inline script / 原始 envelope 直提交流程
- 其他非模板主线的旁路命令入口

原因不是它们不重要，而是本期用户已明确要求只覆盖平台任务主链路。后续阶段可在相同规则模型上继续扩面。

---

## 6. 规则模型

P0 规则采用统一结构，支持内置默认规则与配置扩展。

建议结构：

```json
{
  "rule_id": "shell.rm_rf_root",
  "enabled": true,
  "severity": "critical",
  "match_type": "regex",
  "pattern": "(?i)\\brm\\s+-rf\\s+/(\\s|$)",
  "applies_to": ["shell", "bash", "sh"],
  "description": "禁止删除根目录或全局递归删除命令",
  "remediation_hint": "请改用受控路径和显式文件清单，不允许全局递归删除"
}
```

字段说明：

- `rule_id`：稳定规则标识，用于日志、审计、配置覆盖。
- `enabled`：是否启用。
- `severity`：P0 仅用于审计与展示，统一按阻断处理。
- `match_type`：`keyword` 或 `regex`。
- `pattern`：匹配表达式。
- `applies_to`：适用脚本类型。
- `description`：面向操作者的规则说明。
- `remediation_hint`：命中后的修复建议。

P0 规则集来源：

1. **内置默认规则**
   - 随代码发布，保证开箱即用。

2. **配置扩展规则**
   - 通过平台配置增加、关闭或覆盖规则。
   - 不要求 P0 提供管理 UI。

### 6.1 配置策略

P0 建议支持如下配置语义：

- `enabled=false` 可关闭整套门禁。
- 可通过 `rule_id` 覆盖内置规则的 `enabled/pattern/severity/description/remediation_hint`。
- 可追加自定义规则。

合并顺序：

```text
内置默认规则
  -> 按 rule_id 应用配置覆盖
  -> 追加配置中的新增规则
  -> 生成最终生效规则集
```

这样可以满足“P0 先内置，但通过配置扩展”的要求，不会把后续演进锁死。

---

## 7. 内容提取与匹配策略

P0 不做完整脚本解释器，但也不应只做“全文裸正则”这种误伤过高的方案。

### 7.1 Shell / Bash / Sh

处理方式：

- 按行扫描。
- 去掉空白行。
- 忽略以 `#` 开头的纯注释行。
- 对剩余行做规则匹配。

P0 不处理复杂 shell AST，也不尝试识别运行时拼接后的动态命令。

### 7.2 Python

P0 只做轻量扫描，重点识别显式命令执行片段，例如：

- `os.system(...)`
- `subprocess.run(...)`
- `subprocess.Popen(...)`

匹配目标是这些调用中的高风险命令文本。如果命令在运行时被复杂拼接，P0 可能无法完全覆盖，这属于已知限制。

### 7.3 Ansible

P0 只检查会直接下发命令文本的模块参数，不做所有变更模块的语义治理。

优先覆盖：

- `shell`
- `command`
- `raw`
- `script`

推荐做法：

- 尝试按 YAML 结构解析 playbook。
- 遍历 `tasks / pre_tasks / post_tasks / handlers`。
- 只提取上述模块的命令字符串做匹配。

明确不做：

- 不把 `service`、`copy`、`user`、`lineinfile` 这类模块视为 P0 高风险命令扫描对象。
- 不尝试判断“业务上是否属于变更操作”。

这样可以让 P0 聚焦在“危险命令文本”，而不把问题扩展成“完整变更治理系统”。

---

## 8. P0 默认高风险规则范围

P0 只覆盖高信号、低争议的命令类型。

建议默认规则分组：

### 8.1 破坏性文件系统命令

- `rm -rf /`
- `rm -rf /*`
- `mkfs`
- `fdisk`
- `parted`
- `dd` 写入块设备，例如 `of=/dev/sdX`

### 8.2 主机可用性命令

- `shutdown`
- `reboot`
- `halt`
- `poweroff`
- `init 0`
- `init 6`

### 8.3 账号与口令命令

- `userdel`
- `passwd`
- `chpasswd`

### 8.4 安全边界破坏命令

- `iptables -F`
- `iptables --flush`
- `systemctl stop firewalld`
- `service iptables stop`

P0 不建议一开始放太多“边界模糊”的规则，例如：

- `curl | sh`
- `chmod 777`
- `sed` / `echo >>`

这些命令虽然有风险，但误伤率更高，更适合放到 P1 做分级或审批化治理。

---

## 9. 决策与错误返回

P0 只支持两个结果：

- `allow`
- `deny`

命中任一启用规则即 `deny`。

建议统一错误语义：

- 错误码：`TASK_COMMAND_POLICY_DENIED`
- 用户可读消息：`脚本命中高风险命令策略，已阻止执行`

建议附带字段：

- `rule_id`
- `description`
- `matched_fragment`
- `remediation_hint`

`matched_fragment` 要做以下限制：

- 仅返回截断后的最小命中片段。
- 避免回显整段脚本。
- 如片段中可能携带密钥、口令或 token，需沿用现有敏感词脱敏策略处理。

---

## 10. 审计与可观测性

P0 虽然不做审批，但必须留痕。

至少记录两类信息：

### 10.1 业务日志

记录：

- operator / triggered_by
- source：`script_studio` 或 `task_template_validation`
- template_id / draft_id
- app_type
- rule_id
- severity
- decision=`deny`

### 10.2 模板治理结果

如果命中规则发生在模板校验链路：

- 让模板 validation status 进入失败态。
- 在校验结果中带出命中规则摘要。

这样 `Task Center` 不需要自己重新理解“高风险命令语义”，只需要继续依赖现有模板治理状态即可。

---

## 11. 组件与文件落点

建议新增或调整以下代码边界：

### 11.1 新增组件

- `app/platform/service/script_execution_policy.go`
  - 定义 `ScriptExecutionPolicyGate` 接口与 DTO。

- `app/platform/service/impl/script_execution_policy_gate.go`
  - 统一门禁实现。

- `app/platform/service/impl/script_execution_policy_rules.go`
  - 内置默认规则。

- `app/platform/service/impl/script_execution_policy_provider.go`
  - 规则加载与配置合并。

### 11.2 接入点修改

- `app/platform/service/impl/script_studio.go`
  - 试跑前调用 gate。

- `app/platform/service/impl/task_template_v2.go`
  - 模板校验链路调用 gate。

P0 不建议把规则匹配逻辑直接塞进现有大文件中的某个函数体里，否则会迅速演化成多处重复判断。

---

## 12. 测试策略

P0 至少补齐以下测试：

### 12.1 Gate 单测

- shell 命中规则返回 `deny`
- shell 注释行不误报
- ansible `shell/command/raw` 命中规则返回 `deny`
- ansible 普通读命令不误报
- 配置覆盖能关闭内置规则
- 配置能追加自定义规则

### 12.2 Script Studio 集成测试

- draft 内容带危险命令时，试跑请求直接失败
- 返回错误码、规则说明与修复提示

### 12.3 Task Template 集成测试

- 模板内容带危险命令时，模板校验失败
- 模板未通过校验时，后续 `Task Center` 正常执行链路不可用

### 12.4 回归测试

- 现有 credential / inventory / parameter / auth policy 校验链路无回归
- 未命中规则的普通模板仍可试跑与执行

---

## 13. 上线与回滚

P0 应采用保守上线方式。

### 13.1 上线步骤

1. 代码发布内置默认规则。
2. 默认仅在 `Script Studio / Task Template validation` 生效。
3. 观察命中日志与误报情况。
4. 如规则需要微调，通过配置覆盖修正。

### 13.2 回滚策略

提供总开关：

- `script_execution_policy.enabled=false`

回滚后行为：

- 平台恢复到当前无命令门禁状态。
- 不需要回退代码即可快速解除拦截。

---

## 14. 非目标与已知限制

P0 明确不做以下内容：

- 不覆盖 controller `remote/run` / `config_execute` 等旁路执行入口。
- 不覆盖纯临时 inline script / 原始 envelope 直提交流程。
- 不做审批流、双人复核、例外放行。
- 不做只读命令白名单。
- 不做数据库规则管理与前端规则维护界面。
- 不做完整 Python / shell AST 语义分析。
- 不做 ansible 所有变更模块的风险识别。

已知限制：

- 运行时拼接出的动态命令，P0 可能无法全部识别。
- `service/user/copy` 等非命令文本型变更行为，P0 不覆盖。
- 旁路执行入口依然可能绕过本期门禁，这是已接受范围。

---

## 15. 验收标准

本设计完成后，P0 验收以以下结果为准：

1. `Script Studio` 中包含明显高风险命令的脚本无法试跑。
2. 含明显高风险命令的任务模板无法通过校验并进入可执行态。
3. `Task Center` 基于该模板的主链路执行因此被前置拦住。
4. 规则集默认随代码生效，且可通过配置关闭、覆盖或追加。
5. 未命中规则的既有正常脚本不产生明显回归。

---

## 16. 后续演进方向

P1 建议在同一模型上继续扩展：

- 把 `remote/run`、`config_execute` 纳入同一门禁体系。
- 新增中风险命令分级，支持 `deny / require_approval`。
- 针对巡检类模板引入只读白名单。
- 扩展 ansible 模块级风险识别。
- 把规则源从配置扩展到数据库与管理界面。

P0 的价值不在于一次性做完全部治理，而在于先把最危险、最缺失、最容易出事故的一类问题前置收住，并且用正确的组件边界为后续治理留口子。
