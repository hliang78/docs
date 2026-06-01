# 新能力从定义到跑通 — 端到端清单

按下面顺序做一遍，新能力即可从「IDL → Controller 白名单 → OneOPS 调用 → Agent 实现」全链路跑通。以 **GetHostname**（无参，返回主机名）为例。

---

## 1. IDL：增加能力定义

**文件**：`docs/bidi/agent_capabilities.yaml`

在 `agent_capabilities` 下增加一项：

```yaml
  - method: GetHostname
    request: []
    response: [hostname]
```

---

## 2. 代码生成：刷新 Controller 白名单

在仓库根目录执行（或先 `cd OneOPS`）：

```bash
cd OneOPS && go run ./tools/bidi_codegen \
  -yaml ../docs/bidi/agent_capabilities.yaml \
  -out ../ctrlhub/controller/cmd/bidi_controller/agent_whitelist_generated.go
```

**结果**：`AgentQueryMethodWhitelistList` 中会多出 `"GetHostname"`，Controller 无需手改代码。

---

## 3. OneOPS spec：方法名常量

**文件**：`OneOPS/app/platform/bidi/spec/capabilities.go`

- 在 `const (` 中增加：`MethodGetHostname = "GetHostname"`
- 在 `AgentQueryMethodNames()` 的 return 切片中增加：`MethodGetHostname`

（若需要请求/响应类型，可在此文件增加 `GetHostnameReq` / `GetHostnameResp`，与 IDL 一致。）

---

## 4. OneOPS 平台层：能力方法

**文件**：`OneOPS/app/platform/service/impl/oneops_bidi_service.go`

增加经 Controller 转发到 Agent 的能力方法，例如：

```go
// GetHostname 经 Controller 转发到 Agent 获取主机名
func (s *OneOpsBidiService) GetHostname(agentCode string, ctx context.Context) (string, error) {
	raw, err := s.CallAgent(ctx, agentCode, spec.MethodGetHostname, nil)
	if err != nil {
		return "", err
	}
	if m, ok := raw.(map[string]interface{}); ok {
		if v, ok := m["hostname"].(string); ok {
			return v, nil
		}
	}
	return "", fmt.Errorf("返回格式错误")
}
```

（若已有 DTO，可返回 `*dto.XXX` 并在内部做 convert。）

---

## 5. OneOPS 服务接口与实现（供 API 调用）

**文件**：`OneOPS/app/platform/service/i_agent.go`  
在 `IAgent` 接口中增加：

```go
GetHostname(agentCode string, ctx context.Context) (string, error)
```

**文件**：`OneOPS/app/platform/service/impl/agent_bidi.go`  
- 若存在 `BidiAgentRPCForwarder`，在 forwarder 接口中增加 `GetHostname(...)`，并在实现里调 `s.forwarder.GetHostname(...)`。
- 在 `AgentBidiSrv` 上实现 `GetHostname`：有 forwarder 时调 forwarder，否则可调 `CallRPCToOneSession("GetHostname", nil)`（或你现有的 bidi 调用方式）。

**文件**：`OneOPS/app/platform/service/impl/oneops_bidi_service.go`  
- 已在第 4 步实现；若 forwarder 是 `OneOpsBidiService` 的封装，确保 `BidiAgentRPCForwarder` 实现里调 `OneOpsBidiService.GetHostname`。

（若你项目里 Agent 能力统一通过 forwarder 走 OneOpsBidiService，则只需在 `OneOpsBidiService` 实现 GetHostname，并在 `agent_bidi.go` 的 forwarder 实现中转发到它。）

---

## 6. OneOPS API 与路由（对前端暴露）

**文件**：`OneOPS/app/platform/api/agent.go`  
增加 HTTP 处理函数，例如：

```go
func (a *AgentAPI) GetHostname(ctx *gin.Context) {
	agentCode := ctx.Param("agentCode")
	if agentCode == "" {
		ctx.JSON(400, gin.H{"error": "missing agentCode"})
		return
	}
	hostname, err := a.AgentSrv.GetHostname(agentCode, ctx.Request.Context())
	if err != nil {
		ctx.JSON(500, gin.H{"error": err.Error()})
		return
	}
	ctx.JSON(200, gin.H{"hostname": hostname})
}
```

**文件**：`OneOPS/app/platform/router/platform_bidi.go`  
在 agents 组下增加路由，例如：

```go
agents.GET(":agentCode/hostname", agentAPI.GetHostname)
```

---

## 7. Agent 侧：实现 + 表驱动

**文件**：`ctrlhub/controller/agent/cmd/bidi_agent/capabilities.go`

- **实现**：若 GetHostname 属于「主机信息」，可放在现有 `getDeviceInfo()` 的扩展或单独函数；若你希望走能力接口，可定义小接口如 `HostInfoProvider`，实现里调 `os.Hostname()` 并返回 `map[string]interface{}{"hostname": hostname}`。
- **表驱动**：在 `agentCapabilities` 中增加一行，并实现对应的 wrap：

```go
// 在 agentCapabilities 表中增加
{"GetHostname", wrapGetHostname},

// 实现 wrap
func wrapGetHostname(as *AgentService) func(context.Context, interface{}) (interface{}, error) {
	return func(ctx context.Context, params interface{}) (interface{}, error) {
		hostname, _ := os.Hostname()
		return map[string]interface{}{"hostname": hostname}, nil
	}
}
```

（若走接口，可先定义 `HostInfoProvider` 接口与实现，再在 wrap 里调接口。）

---

## 8. 验证新能力已跑通

1. **启动**：OneOPS、Controller、Agent 均启动，Agent 已注册到 Controller。
2. **调 API**：  
   `GET /api/v1/platform/agents/{agentCode}/hostname`（或你实际挂载的 path）  
   应返回 `{"hostname":"..."}`。
3. **链路**：请求 → AgentAPI.GetHostname → IAgent.GetHostname → OneOpsBidiService.GetHostname → CallAgent(..., "GetHostname", nil) → Controller handleQueryAgent（白名单通过）→ Agent wrapGetHostname → 返回 hostname → 一路回写到 HTTP。

---

## 小结表

| 步骤 | 位置 | 动作 |
|------|------|------|
| 1 | docs/bidi/agent_capabilities.yaml | 增加 method + request/response |
| 2 | 命令行 | 运行 bidi_codegen，生成 Controller 白名单 |
| 3 | OneOPS/app/platform/bidi/spec/capabilities.go | 增加方法常量（及可选 Req/Resp） |
| 4 | OneOPS/.../oneops_bidi_service.go | 增加 GetHostname，内部 CallAgent(spec.MethodGetHostname, ...) |
| 5 | OneOPS/.../i_agent.go + agent_bidi.go | 接口与 forwarder 实现 GetHostname |
| 6 | OneOPS/.../api/agent.go + router | HTTP 处理函数 + 路由 |
| 7 | ctrlhub/.../bidi_agent/capabilities.go | wrap + agentCapabilities 表加一行 |

**Controller 无需改业务代码**；白名单由 codegen 从 IDL 生成。按上述顺序做齐，新能力即可真正运行起来。
