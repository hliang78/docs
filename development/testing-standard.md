# OneOPS 测试与 evidence 规范

本文档定义 OneOPS 的测试文档、自动化测试、探索驱动测试和 evidence 记录标准。

## 测试目标

测试不是只证明接口可调用，而是要证明目标业务结果可被可靠达成，并且失败时能定位原因。

对于复杂项目，应同时覆盖：

- 最终目标是否达成。
- 中途关键环境是否可信。
- 高危 weak points 是否被发现和处理。
- 自动化结果是否可复现。

## 使用门禁

测试文档、测试用例、探索 probe 设计只有在状态为 `reviewed` 或 `active` 时，才能作为执行类测试、验收测试或 autodev story 发布依据。

如果测试文档状态为 `blocked-human-confirmation`：

- 不得直接执行会写入、触发任务、调用外部系统或触碰真实设备的测试。
- 不得把其中的性能指标、fixture、通过标准当成已确认事实。
- AI/autodev worker 只能输出待确认清单、补充建议、read-only 调查计划。

如果测试文档状态为 `draft`：

- 可以用于评审和补充。
- 只能执行明确安全的 read-only 验证，且必须标记为非验收证据。

## 测试分类

| 类型 | 目的 | 典型证据 |
|---|---|---|
| 功能测试 | 验证业务功能 | 测试用例、接口响应、UI 截图 |
| 接口测试 | 验证 API 契约 | 请求/响应、业务状态字段 |
| 集成测试 | 验证模块协作 | DB/API/任务/外部依赖 evidence |
| 性能测试 | 验证吞吐和响应 | TPS、响应时间、错误率 |
| 回归测试 | 防止已有能力退化 | 自动化报告、diff |
| 探索驱动测试 | 发现薄弱环节并分类风险 | flow line、probe、weak point、H0/H1/H2/H3 |
| 安全边界测试 | 防止越权、secret 泄露、误触设备 | sanitization、approval、target proof |

## 测试用例文档

推荐位置：

```text
docs/testing/cases/
```

推荐命名：

```text
【测试用例】<系统>_<模块>_V<版本号>.md
```

标准内容：

- 文档信息。
- 测试概述。
- 测试环境。
- 测试工具。
- 功能性测试用例。
- 接口测试用例。
- 性能测试用例。
- 安全与权限测试。
- 探索测试计划。
- 测试数据与 fixture。
- 执行记录与报告链接。

## 功能测试用例形状

| 字段 | 说明 |
|---|---|
| 用例编号 | 稳定 ID，例如 `TC_W_001` |
| 用例名称 | 简短说明 |
| 前置条件 | 账号、fixture、数据状态 |
| 测试步骤 | 可复现步骤 |
| 输入数据 | 请求或操作输入 |
| 预期结果 | 业务结果，不只 HTTP 状态 |
| 实际结果 | 执行后填写 |
| 测试状态 | `PASS/FAIL/BLOCKED/SKIPPED` |
| evidence | 证据路径 |

## 接口测试原则

接口测试必须验证：

- HTTP status。
- 业务成功字段，例如 `success`、`code`、`responseCode`。
- `data` 中关键字段。
- 错误消息。
- 权限和 tenant/device 边界。
- 空结果和异常路径。

特别规则：

```text
HTTP 200 不等于业务成功。
```

如果响应体中 `success=false`，即使 HTTP status 是 200，也应视为业务失败。

## pytest 脚本要求

历史 prompts 中的 pytest 结构可以保留为参考：

- `tests/test_<module>.py`
- `tests/conftest.py`
- `reports/test_report_<module>_<time>.html`

推荐结构：

```text
tests/
  conftest.py
  test_<module>.py
reports/
  test_report_<module>_<timestamp>.html
```

测试脚本应包含：

- 环境配置。
- 认证配置。
- ResponseValidator。
- fixture/test data。
- 正常路径。
- 参数边界。
- 权限边界。
- 数据不存在。
- 重复提交。
- 业务失败判断。

ResponseValidator 应兼容项目历史响应结构：

```python
def is_success(resp_json):
    if "success" in resp_json:
        return resp_json.get("success") is True
    if "code" in resp_json:
        return resp_json.get("code") in (0, 200)
    if "responseCode" in resp_json:
        return resp_json.get("responseCode") in (0, 200)
    return False
```

## 探索驱动测试

复杂项目应使用探索驱动测试，而不是一次性列粗粒度用例。

标准顺序：

1. 梳理目标方向的 `flow line`。
2. 定义每条 flow line 的 `final goal`。
3. 找出中途 `critical environments`。
4. 提出 `weak-point hypotheses`。
5. 按 `H0/H1/H2/H3` 进行 harm classification。
6. 设计 `probe`。
7. 执行并记录 evidence。
8. 根据结果决定 `continue/open-repair/补fixture/request-approval/defer/stop`。

## Probe 分类

| Probe level | 说明 | 默认是否可自动执行 |
|---|---|---|
| `static` | 只读文档/代码分析 | 是 |
| `read-only-db` | 只读 DB 查询 | 需要确认 test-only 与 secret handling |
| `read-only-api` | 只读 API | 是，但必须确认无副作用 |
| `read-only-observability` | Prometheus/Loki 等只读查询 | 是，但必须约束 fixture |
| `read-only-script-inspection` | 检查脚本是否有副作用 | 是 |
| `dry-run` | 可能生成临时记录或模拟执行 | 需要 story 明确允许 |
| `controlled-action` | 真实写入/任务触发/同步/采集 | 需要 reviewed story，必要时 approval |
| `external-device-action` | 真实设备命令或外部系统动作 | 必须 explicit approval |

## Harm classification

| 等级 | 含义 | 处理原则 |
|---|---|---|
| `H0` | unsafe / invalidates gate | 最高优先级；未处理前不应继续低风险 proof |
| `H1` | gate-untrustworthy / blocks proof | 阻塞 gate 可信度；优先修复或补证据 |
| `H2` | coverage gap | 记录盲区，可排入后续补强 |
| `H3` | efficiency / maintainability | 优化类问题 |

## Evidence 记录

每次自动化或人工测试都应记录：

- `run_id`
- `story_id`
- `flow_line`
- `probe_id`
- `environment`
- `fixtures`
- `command_or_request`
- `status`
- `weak_points`
- `harm_class`
- `evidence_paths`
- `sanitization`
- `next_decision`
- `daily_cn_summary`

自动化 evidence 状态词：

- `PASS`
- `FAIL`
- `BLOCKED`
- `APPROVAL`
- `SKIPPED`

## Secret 与安全

测试 evidence 禁止写入：

- password
- token
- private key
- SNMP community
- bearer token
- DSN 中的凭证
- credential value

允许写入：

- credential ref。
- redacted id/hash。
- presence boolean。
- endpoint alias。
- fixture code。
- tenant code。

## 完成定义

一个测试任务完成时，应能回答：

- 测试了什么目标。
- 使用了什么环境和 fixture。
- 执行了什么命令或请求。
- 结果是 `PASS/FAIL/BLOCKED/APPROVAL/SKIPPED` 中哪一个。
- 是否发现 H0/H1 风险。
- 下一步是继续、修复、补 fixture、审批、延后还是停止。
