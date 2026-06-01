# Bidi 能力契约 IDL 与代码生成

## 能力 IDL

- **`agent_capabilities.yaml`**：Agent 能力契约单点定义（方法名、请求/响应字段），与 OneOPS `app/platform/bidi/spec`、Controller 白名单、Agent 表驱动一致。
- 命名约定：平台边界统一 **snake_case**（dir_path, file_path, session_id 等）。

## 代码生成

从 YAML 生成 Controller 白名单等：

```bash
# 在仓库根目录执行（或先 cd OneOPS）
cd OneOPS && go run ./tools/bidi_codegen \
  -yaml ../docs/bidi/agent_capabilities.yaml \
  -out ../ctrlhub/controller/cmd/bidi_controller/agent_whitelist_generated.go
```

- **生成产物**：`ctrlhub/controller/cmd/bidi_controller/agent_whitelist_generated.go`（`AgentQueryMethodWhitelistList`）。
- **何时运行**：修改 `agent_capabilities.yaml` 增删能力后执行一次；可集成到 make/CI。

## 新增能力流程（Phase 4）

1. 在 **`agent_capabilities.yaml`** 中增加一项（method、request、response）。
2. 运行上述 **codegen**，重新生成 Controller 白名单。
3. 在 **OneOPS spec**（`OneOPS/app/platform/bidi/spec/capabilities.go`）中增加方法常量与 Req/Resp（或后续由 codegen 生成）。
4. 在 **Agent** 侧实现接口并在表驱动中加一行；在 **OneOPS** 侧增加能力方法并调 `CallAgent(..., spec.MethodXxx, params)`。
5. Controller 无需手改业务代码（白名单由生成覆盖）。

## 新能力真正跑通：端到端清单

需要从「IDL → 白名单 → OneOPS → API/路由 → Agent 实现」完整做一遍时，请按：

- **[NEW_CAPABILITY_RUNBOOK.md](./NEW_CAPABILITY_RUNBOOK.md)**  
  按步骤操作（含 YAML、codegen、spec、OneOpsBidiService、IAgent/AgentAPI/路由、Agent wrap + 表驱动、验证方式），以 GetHostname 为例贯穿全链路。
