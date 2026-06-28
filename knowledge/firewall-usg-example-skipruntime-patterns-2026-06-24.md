# OneOPS Firewall USG Example SkipRuntime Root Cause Notes 2026-06-24

## 背景

2026-06-24 在目录 `ctrlhub/controller/pkg/nodemap/example/usg_example` 执行 `go run main.go` 时，最初有两类失败：

- `CTY-YZ-JS-YZ-MTDD-01D04F403-A13-06U19-DP-FW1000-NFW | 新建测试 | 5`
- `CZ-LY-FW-1.BD.F5000 | 策略复用 | 6`

最终修复后，完整回归结果为：

- `总用例: 77`
- `通过: 77`
- `失败: 0`
- `基准比对结果: 一致`

这次排查暴露出的共同模式不是匹配算法本身错误，而是 lowerer 把“本应忽略的语法”当成了不支持语法，导致规则被静默标记为 `SkipRuntime`，后续运行时根本没有机会参与匹配或复用。

## 错误类型 1: `description` 元数据被当成不支持语法

### 现象

- 表面现象像是“应该命中已有策略，结果却走到了生成策略分支”。
- 更隐蔽的版本是“配置能编译，但运行时少了一条关键规则”。
- 问题出现在 USG v2 lowerer 的 policy 和 NAT 规则处理路径里。

### 根因

`description` 只是规则元数据，不应该影响运行时可执行性。但在 `v2/usgrt` lowerer 中，这类子句没有被明确识别为可忽略内容，于是被当成 unsupported syntax 处理，进而让规则失去运行时资格。

核心修复点：

- `ctrlhub/controller/pkg/nodemap/node/device/firewall/v2/usgrt/lower.go`
- 相关位置在 `lowerPolicyClause` 的 policy 规则分支和 NAT 规则分支

修复后的处理方式是：

- 显式接受 `description`
- 仅把它当作 metadata
- 不再因为它设置 unsupported diagnostics 或触发 `SkipRuntime`

### 识别信号

如果后续再遇到类似问题，可以优先看这些信号：

- 失败场景不是 parser panic，而是“少匹配一条规则”或“误走新建策略”
- compile/report 中出现与 `description` 相关的 unsupported 线索
- 同一配置里主体地址、服务、zone 都正常，但某条 rule 在 runtime 阶段被跳过

### 已落地的回归保护

- `ctrlhub/controller/pkg/nodemap/node/device/firewall/v2/usgrt/unsupported_test.go`
- `ctrlhub/controller/pkg/nodemap/node/device/firewall/usg/real_config_smoke_test.go`

这两处测试分别覆盖：

- `description` 不应让 policy rule 失去运行时资格
- `description` 不应让 NAT rule 失去运行时资格
- 真实配置场景下可以继续编译并参与运行时匹配

## 错误类型 2: SecPath `security-policy` 下的 `#` 分隔行被当成不支持语法

### 现象

- 典型表现是“策略复用应该成功，但系统认为需要新生成策略”。
- 这次最典型的真实案例是 `CZ-LY-FW-1.BD.F5000` 的 `策略复用 | 6`。
- 进一步定位时可以看到目标策略如 `LY_policy_1553` 实际上已经存在，但它在运行时不可用。

### 根因

部分真实配置在 `security-policy` rule 块里会带 `#` 分隔行。这类行本质上是结构分隔或注释噪音，不应影响语义。但 `v2/secpathrt` lowerer 在遍历 rule children 时把 `#` 当成了 unsupported child，导致整条 rule 被静默排除出 runtime。

核心修复点：

- `ctrlhub/controller/pkg/nodemap/node/device/firewall/v2/secpathrt/lower.go`
- 关键函数：`lowerSecurityPolicyRuleFromChildren`

修复后的处理方式是：

- 将 `#` 与 `description`、`counting` 一样视为可忽略内容
- 不再让这类分隔行污染 rule 可执行性

### 识别信号

- 精确匹配和子集场景正常，但复用场景异常
- 配置里明明存在可复用 rule，runtime 却像看不见它
- 真实配置文件里出现大量 `#` 分隔行
- 某条 rule 的 `SkipRuntime` 为 `true`

### 真实样本

这次用于锁定问题的真实配置样本：

- `ctrlhub/controller/pkg/nodemap/example/usg_example/2026-01-19-08.36.34-132.239.180.12-CZ-LY-FW-1.BD.F5000.txt`

### 已落地的回归保护

- `ctrlhub/controller/pkg/nodemap/node/device/firewall/v2/secpathrt/unsupported_test.go`
- `ctrlhub/controller/pkg/nodemap/node/device/firewall/secpath/real_config_smoke_test.go`

其中真实配置 smoke test 明确验证：

- 复用目标策略仍然可见
- 目的地址组扩展后仍能走复用路径
- `#` 分隔行不会再让 rule 被静默跳过

## 这两类错误的共同模式

这两类问题虽然出现在不同 lowerer，但本质是同一个家族问题：

1. 真实设备配置里存在“非语义核心”的辅助子句。
2. lowerer 没有把它们列入允许忽略的白名单。
3. 编译阶段没有 hard fail。
4. 运行时却把整条 rule 排除掉。
5. 最终在上层表现成“匹配不到”“复用失败”“误生成新策略”。

这类问题最危险的地方在于：

- 它不像语法错误那样立即爆炸
- 它会伪装成策略匹配逻辑问题
- 如果没有真实配置 smoke test，很容易把排查方向带偏

## 调试建议

后续如果再遇到 USG example 或真实防火墙配置类似异常，建议按这个顺序排查：

1. 先确认失败类型是“规则不存在”还是“规则存在但 runtime 看不见”。
2. 检查相关 rule 是否被打上 `SkipRuntime`。
3. 搜索 rule children 里是否有 `description`、`#`、`counting` 或其他元数据行。
4. 对照对应 lowerer 是否显式允许这些子句。
5. 在修改匹配算法前，优先补一个真实配置 smoke test 固化现象。

## 本次相关修复与验证

涉及文件：

- `ctrlhub/controller/pkg/nodemap/node/device/firewall/v2/usgrt/lower.go`
- `ctrlhub/controller/pkg/nodemap/node/device/firewall/v2/usgrt/unsupported_test.go`
- `ctrlhub/controller/pkg/nodemap/node/device/firewall/usg/real_config_smoke_test.go`
- `ctrlhub/controller/pkg/nodemap/node/device/firewall/v2/secpathrt/lower.go`
- `ctrlhub/controller/pkg/nodemap/node/device/firewall/v2/secpathrt/unsupported_test.go`
- `ctrlhub/controller/pkg/nodemap/node/device/firewall/secpath/real_config_smoke_test.go`
- `ctrlhub/controller/pkg/nodemap/example/usg_example/main.go`
- `ctrlhub/controller/pkg/nodemap/example/usg_example/main_test.go`

验证命令：

```bash
go test ./controller/pkg/nodemap/example/usg_example -run TestShouldMatchOrGenerateForScenario -count=1
go test ./controller/pkg/nodemap/node/device/firewall/v2/secpathrt -run TestCompileWithReport_AllowsSecurityPolicyCommentSeparator -count=1
go test ./controller/pkg/nodemap/node/device/firewall/secpath -run TestSecPathRealConfigFlyConfigExtendsReusedDestinationGroup -count=1
cd ctrlhub/controller/pkg/nodemap/example/usg_example && go run main.go
```

## 后续深入研究建议

1. 给 `usgrt` 和 `secpathrt` 建立统一的“可忽略语法”策略，避免每个 lowerer 各自漏掉一类元数据。
2. 给 `SkipRuntime` 增加更明显的日志或报告字段，降低“静默跳过”排查成本。
3. 扩大真实配置 smoke corpus，重点覆盖 `description`、`#`、`counting`、厂商分隔符、注释变体。
4. 梳理“unsupported syntax”与“ignorable syntax”的边界，避免 metadata 噪音继续误伤 runtime。
