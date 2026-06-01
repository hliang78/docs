# 【接口调用文档】OneOPS_DeviceV2纳管观测_v0.1

## 1. 文档信息

| 项目 | 内容 |
| --- | --- |
| 系统名称 | OneOPS |
| 模块名称 | Device V2 纳管观测 |
| 版本号 | v0.1 |
| 接口基准地址 | 待实现 |
| 关联接口文档 | 【接口文档】OneOPS_DeviceV2纳管观测_v0.1.md |

## 2. 调用前准备

| 项目 | 内容 |
| --- | --- |
| 环境地址 | `http://127.0.0.1:3001/#/device/device-v2-management-redesign` |
| 登录账号 | `admin` |
| 前置数据 | 已入库单台设备 |
| 注意事项 | 凭据不得写入请求示例之外的文档或配置 |

## 3. 通用响应结构

复用现有 OneOPS 响应结构。业务调用方必须根据实际接口实现确认字段，不得自行推断。

## 4. 状态码说明

| 状态码 | 说明 | 处理建议 |
| --- | --- | --- |
| 200 | 成功 | 读取 data |
| 400 | 参数错误 | 检查单设备标识、monitor mode、actionIds |
| 500 | 执行失败 | 查看 action error 和后端日志 |

## 5. 接口调用说明

### 5.1 获取纳管摘要

**接口描述**：读取单台设备 action 摘要。

**接口地址**：`GET 待实现`

**请求参数**：

| 参数 | 示例 | 说明 |
| --- | --- | --- |
| deviceV2Id | 待实现 | 单设备标识 |

**响应关注点**：

- `actions`
- `retryableActions`
- `status`
- `error`

### 5.2 生成继续纳管计划

**接口描述**：生成单设备监控/日志纳管计划。

**接口地址**：`POST 待实现`

**请求体示例**：

```json
{
  "deviceV2Id": "待实现",
  "serverMonitorMode": "agent"
}
```

### 5.3 执行继续纳管

**接口描述**：执行指定 ensure action。

**接口地址**：`POST 待实现`

**请求体示例**：

```json
{
  "deviceV2Id": "待实现",
  "actionIds": ["monitor.ensure", "log.syslog.ensure"],
  "serverMonitorMode": "agent"
}
```

**调用约束**：

- 不允许批量执行。
- 不允许业务接口调用 `docs/openclaw-autodev/tools/d2on/`。
- 服务器远程操作必须经 controller API。

## 6. 接口汇总表

| 序号 | 功能 | 请求方式 | 接口地址 | 是否需要登录 | 说明 |
| --- | --- | --- | --- | --- | --- |
| 1 | 获取纳管摘要 | GET | 待实现 | 是 | 单设备 |
| 2 | 生成纳管计划 | POST | 待实现 | 是 | 单设备 |
| 3 | 执行继续纳管 | POST | 待实现 | 是 | 单设备 |

## 7. 常见问题

| 问题 | 原因 | 处理 |
| --- | --- | --- |
| 返回参数错误 | 缺少单设备标识或服务器监控模式 | 补齐明确参数 |
| 返回执行失败 | 远程配置、controller API、模板缺失 | 查看 action error |
| 网络设备无法配置 | 缺少 H3C/syslog 模板、controller remote access 契约缺失或登录失败 | 先使用 `docs/openclaw-autodev/tools/d2on/d2on-discovery.py` 开发测试工具通过 controller remote API 采集只读证据；业务接口不得调用该工具 |

## 8. 当前交付边界

- 截至本轮，文档与代码层仅能确认单设备继续纳管的接口与证据契约，尚未形成可复用的真实 controller-backed 单台执行结果。
- readiness/review 不应把本轮结果表述为成功执行；应保留为“本地契约已验证、真实执行证据仍缺失”的边界状态。
- 如果后续拿到真实远程执行 trace，再补充到调用文档的示例与证据说明中。

## 8. 开发测试发现工具

`docs/openclaw-autodev/tools/d2on/d2on-discovery.py` 是 D2ON-000 的开发/测试入口，仅用于真实设备探索和后续验证准备。它支持：

- `db-candidates`：使用运行时提供的只读 MySQL 环境变量查询 `platform_devices_v2` 候选设备。
- `inspect-server-via-controller`：优先通过 controller `/api/v1/remote/run` 执行只读 Linux 系统日志文件探测，检查 `/var/log/syslog`、`/var/log/auth.log`、`/var/log/messages`、`/var/log/secure`。
- `inspect-network-via-controller`：优先通过 controller `/api/v1/remote/run` 执行只读网络设备命令族探测，记录 syslog/SNMP trap 模板候选但不应用配置。
- `inspect-server`：通过 SSH 执行只读 Linux 系统日志文件探测，检查 `/var/log/syslog`、`/var/log/auth.log`、`/var/log/messages`、`/var/log/secure`。
- `inspect-network`：通过 SSH 执行只读网络设备命令族探测，作为 controller 不可用时的开发回退路径；如果多个命令族同时命中，按模板歧义失败处理，不猜测厂商。

工具证据写入 `docs/openclaw-autodev/evidence/d2on/discovery/`，摘要写入 `docs/openclaw-autodev/evidence/d2on/D2ON-000.md`。凭据、token、密码不得写入代码、文档、配置或证据；候选设备查询证据只记录稳定标识，不落库原始 attributes/metadata JSON，避免携带 SNMP community、token 或凭据。controller 请求体和远程命令 stdout/stderr 摘要写入 evidence 前会对常见 password/token/secret/SNMP community/security-name 和 SSH 诊断用户名模式做 best-effort 脱敏；探索命令仍应保持只读和最小范围，避免无必要输出完整敏感配置。
