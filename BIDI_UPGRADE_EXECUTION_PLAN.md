# Bidi 重大升级 — 执行方案

本文档将《Bidi 重大升级设计方案》（`BIDI_MAJOR_UPGRADE_DESIGN.md`）中的**实施阶段建议**转化为可落地的**执行方案**：按阶段拆解任务、标注代码位置、依赖关系与验收标准，便于按步骤实施与排期。

---

## 一、总览与依赖关系

| 阶段 | 目标 | 依赖 | 建议顺序 |
|------|------|------|----------|
| **Phase 1** | Controller 通用 QueryAgent + 白名单；OneOPS 统一 CallAgent | 无 | 1 |
| **Phase 2** | 能力契约（spec 包）；OneOPS 能力方法 + 统一 convert | Phase 1 | 2 |
| **Phase 3** | Agent 能力接口化 + 表驱动绑定 | Phase 2 | 3 |
| **Phase 4** | 可选：IDL/代码生成；bidi 库增强 | Phase 3 | 4 |

**建议**：先完成 Phase 1～2，即可显著减少重复与心智负担；Phase 3～4 再推进「定义一处、生成三端」与类型安全。

---

## 二、Phase 1：Controller 通用 QueryAgent + OneOPS CallAgent

**产出**：新增能力时 Controller 零代码，OneOPS 只加一层封装。

### 2.1 任务清单

| 序号 | 任务 | 涉及模块/路径 | 验收标准 |
|------|------|----------------|----------|
| 1.1 | **Controller：实现通用 `QueryAgent` handler** | `ctrlhub/controller/cmd/bidi_controller/main.go` | 新增 `handleQueryAgent(ctx, params)`：从 params 取 `method`、`agent_code`；白名单校验；调用现有 `forwardToAgentByCode(agentCode, method, params)` 并返回结果 |
| 1.2 | **Controller：注册 `QueryAgent` 并接入白名单** | 同上 | `oneOpsCommunicator.RegisterRPCHandler("QueryAgent", cs.handleQueryAgent)`；白名单可从常量表或配置文件加载（如 `ListFiles`, `GetSystemMetrics`, `CreateDirectory`, ...） |
| 1.3 | **Controller：兼容现有「按能力名」RPC**（可选） | 同上 | 保留现有 `QueryAgentListFiles` 等注册；其 handler 内部改为：构造 `method`+params 后调用 `handleQueryAgent`，或统一路由到 `handleQueryAgent`，保证现有 OneOPS 调用不中断 |
| 1.4 | **OneOPS：实现统一 `CallAgent(agentCode, method, params)`** | `OneOPS/app/platform/service/impl/oneops_bidi_service.go` | `CallAgent(ctx, agentCode, method string, params map[string]interface{}) (interface{}, error)`：内部 `getControllerIDByAgentCode` → `CallController(controllerID, "QueryAgent", map["method"]=method, map["agent_code"]=agentCode 与 params 合并)` |
| 1.5 | **OneOPS：文件类能力改为走 CallAgent** | 同上 | `ListFiles`、`CreateDirectory`、`DeleteFile`、`DownloadFile`、`StartFileUpload`、`UploadFileChunk`、`GetUploadStatus` 内部改为先组 params，再 `CallAgent(agentCode, "ListFiles", params)` 等（RPC 方法名与 Controller 白名单一致）；对外 API 与 DTO 不变 |
| 1.6 | **OneOPS：GetAgentSystemMetrics 改为 CallAgent** | 同上 | `GetAgentSystemMetrics` 内部改为 `CallAgent(agentCode, "GetSystemMetrics", params)`，对应 Controller 侧由 `QueryAgent` 转发（或暂时保留 `QueryAgentSystemMetrics` 在兼容路由中） |

### 2.2 依赖与顺序

- 1.1、1.2 可先做；1.3 与 1.4 可并行（1.3 为兼容，可稍后）。
- 1.4 完成后再做 1.5、1.6（OneOPS 依赖 `CallAgent`）。

### 2.3 兼容与回退

- 保留现有 `QueryAgentListFiles` 等 RPC 名时，OneOPS 可先不改为 `QueryAgent`，仅把 Controller 内部实现收敛到 `handleQueryAgent`。
- 若需全面切到 `QueryAgent`：OneOPS 在 1.5/1.6 中改为 `CallController(..., "QueryAgent", ...)` 即可。

---

## 三、Phase 2：能力契约（spec）+ OneOPS 能力方法 + 统一 convert

**产出**：单点定义、三端一致命名与类型；新增能力时改 spec + 实现 + OneOPS 封装。

### 3.1 任务清单

| 序号 | 任务 | 涉及模块/路径 | 验收标准 |
|------|------|----------------|----------|
| 2.1 | **新建 spec 包（能力契约）** | 新建 `OneOPS/app/platform/bidi/spec/` 或仓库内 `bidi/platform/spec/` | 定义方法名常量（如 `MethodListFiles`, `MethodGetSystemMetrics`）；定义 Req/Resp 结构体（如 `ListFilesReq`, `ListFilesResp`, `FileInfo`）及 JSON 标签；维护「能力列表」供白名单与转换使用 |
| 2.2 | **Controller：白名单从 spec 或配置读取** | `ctrlhub/controller/cmd/bidi_controller/main.go` | `handleQueryAgent` 中的 method 白名单改为从 spec 的常量列表或生成的列表读取，新增能力时只改 spec 即可生效（若 Controller 与 OneOPS 同仓可引用 spec 包；否则通过配置/生成文件同步） |
| 2.3 | **OneOPS：能力方法内使用 spec 类型与 CallAgent** | `OneOPS/app/platform/service/impl/oneops_bidi_service.go` | `ListFiles` 等能力方法：入参/出参与 spec 中 Req/Resp 对齐；内部组 params 时使用 spec 字段名；调用 `CallAgent(agentCode, spec.MethodListFiles, params)`；convert 函数集中到 spec 包或同一层，如 `convertToFileListResp(raw)` 使用 spec 的 `ListFilesResp` 转 DTO |
| 2.4 | **OneOPS：统一 snake_case 约定** | spec + OneOPS convert 层 | 平台边界统一 snake_case（agent_code, dir_path）；在 Controller 的 `handleQueryAgent` 或 OneOPS 的 params 组装处做一次约定文档化并落地（若需兼容 Agent 端 camelCase，在 Controller 转发前做 map 键转换） |
| 2.5 | **文档：能力清单与 Req/Resp 对照表** | `docs/` 或 `OneOPS/docs/` | 列出当前所有 Agent 能力的方法名、请求字段、响应字段，与 spec 一致，便于后续生成与对接 |

### 3.2 依赖与顺序

- 2.1 先做；2.2、2.3 依赖 2.1；2.4、2.5 可与 2.2、2.3 并行或收尾时补充。

### 3.3 验收

- 新增一个「只读配置」类能力时：仅在 spec 中加方法名 + Req/Resp、Controller 白名单自动包含、OneOPS 加一层能力方法 + convert，**Controller 无需改代码**。

---

## 四、Phase 3：Agent 能力接口化 + 表驱动绑定

**产出**：Agent 只实现业务接口，RPC 绑定可表驱动或生成；业务逻辑可单测。

### 4.1 任务清单

| 序号 | 任务 | 涉及模块/路径 | 验收标准 |
|------|------|----------------|----------|
| 3.1 | **定义 Agent 侧能力接口（与 spec 对应）** | `ctrlhub/controller/agent/cmd/bidi_agent/` 或公共 spec 包 | 例如 `FileOperator`：`ListFiles(ctx, dirPath)`, `CreateDirectory(ctx, dirPath, mode)` 等；与 spec 中的方法名、参数一一对应 |
| 3.2 | **实现类注入 AgentService** | `ctrlhub/controller/agent/cmd/bidi_agent/agent_service.go` | 将现有 `handleListFiles` 等内部逻辑抽到 `FileOperator` 实现类（如 `fileService`）；AgentService 持有该实现并调用其方法 |
| 3.3 | **表驱动：method → wrap 函数注册** | 同上 + main 或 init | 定义 `agentCapabilities` 表：`{ method, wrapFn }`；`wrapListFiles` 从 params 取 `dir_path`/`dirPath`，调 `fileService.ListFiles`，将返回转为 map/可序列化结构；循环 `RegisterRPCHandler(method, wrapFn)` |
| 3.4 | **params 解包与命名统一** | Agent 侧 wrap 函数 | 从 bidi 收到的 params（如 snake_case）在 wrap 内解包为 Go 参数，调用业务接口；返回结果打包为 map 或 spec 中 Resp 结构再序列化；与 Controller/OneOPS 的约定一致（snake/camel 在 2.4 中已约定） |
| 3.5 | **兼容现有 handler** | 同上 | 现有 `handleListFiles` 等可先改为「从 params 解包 → 调 FileOperator.ListFiles → 打包返回」；再在 3.3 中改为表驱动注册，去掉重复的 handler 注册代码 |

### 4.2 依赖与顺序

- 3.1、3.2 可先做（先接口化、再表驱动）；3.3、3.4、3.5 随后，最终收敛到「仅表驱动 + 能力接口」。

### 4.3 验收

- 新增能力时：在 spec 加方法名与 Req/Resp；在 Agent 侧实现接口方法 + 在表驱动中加一行 wrap；Controller/OneOPS 无改动（或仅 OneOPS 加能力方法）。

---

## 五、Phase 4：可选 — IDL/代码生成与 bidi 库增强

**产出**：新增能力 = 改 IDL + 实现接口 + 生成代码；类型安全与跨端一致由工具链保证。

### 5.1 任务清单

| 序号 | 任务 | 涉及模块/路径 | 验收标准 |
|------|------|----------------|----------|
| 4.1 | **能力描述 IDL/YAML** | 新建 `bidi/spec/*.yaml` 或等价 | 用 YAML 描述能力：name、method、request、response 结构；与现有 spec 包能力列表对齐 |
| 4.2 | **代码生成器** | 新建 `scripts/` 或 `tools/codegen/` | 根据 IDL 生成：Go Req/Resp 结构体、Controller 白名单列表、OneOPS convert 桩、Agent 侧 wrap 桩（可选）；集成到 make/build 或 CI |
| 4.3 | **bidi 库增强（可选）** | bidi 库仓库/目录 | Typed RPC（泛型 Register）、RequestID/超时透传、Stream 协议等；与现有 `RegisterRPCHandler` 并存，不破坏兼容 |
| 4.4 | **迁移现有能力到 IDL** | spec + 各端 | 将 Phase 2 中手写 spec 能力逐步迁入 IDL，再通过生成替换手写结构体与部分 convert/wrap |

### 5.2 依赖与顺序

- Phase 1～3 完成后再做 Phase 4；4.1 → 4.2 → 4.4；4.3 可与 4.1、4.2 并行（独立于能力契约）。

### 5.3 验收

- 新增能力流程：只改 IDL → 运行 codegen → 实现 Agent 接口（及 OneOPS 能力方法若未完全生成）；Controller 无业务代码变更。

### 5.4 Phase 4 已落地项

| 项 | 状态 | 说明 |
|----|------|------|
| 4.1 能力 IDL | ✅ | `docs/bidi/agent_capabilities.yaml`，与 spec 对齐 |
| 4.2 代码生成器 | ✅ | `OneOPS/tools/bidi_codegen`，从 YAML 生成 Controller 白名单（`agent_whitelist_generated.go`） |
| 4.3 bidi 库增强 | 可选 | Typed RPC、RequestID 透传、Stream 等，见设计文档「十」 |
| 4.4 迁移到 IDL | 进行中 | spec 仍手写；新增能力时改 YAML → codegen → spec/Agent/OneOPS |

---

## 六、与现有代码的兼容（执行时注意点）

- **Controller**：保留现有 `QueryAgentListFiles` 等 RPC 名时，其 handler 内部改为调 `handleQueryAgent` 或统一路由，避免重复逻辑；待 OneOPS 全量切到 `QueryAgent` 后，可考虑废弃旧 RPC 名。
- **OneOPS**：现有 `ListFiles`/`CreateDirectory` 等对外 API 不变，仅内部改为 `CallAgent` 或能力封装 + spec 类型；若存在 `BidiPlatformService.CallAgentRPC` 等，可逐步收敛到 `OneOpsBidiService.CallAgent`。
- **Agent**：先保留现有 `handleListFiles` 等注册，内部改为调 `FileOperator`；再引入表驱动，逐步把 handler 注册改为表驱动，避免大爆炸式替换。

---

## 七、建议排期与里程碑

| 里程碑 | 内容 | 建议工期（参考） |
|--------|------|------------------|
| M1 | Phase 1 完成：Controller 通用 QueryAgent + OneOPS CallAgent，文件/系统指标能力切到 CallAgent | 3～5 天 |
| M2 | Phase 2 完成：spec 包就绪、白名单与 convert 统一、文档能力清单 | 2～4 天 |
| M3 | Phase 3 完成：Agent 能力接口 + 表驱动，新增能力仅改 spec + 实现 + OneOPS 封装 | 3～5 天 |
| M4 | Phase 4（可选）：IDL + 代码生成 + bidi 增强 | 按需排期 |

**建议**：M1 完成后即可在新增能力时采用「OneOPS 只加一层 CallAgent 封装、Controller 零代码」；M2 完成后新增能力改为「改 spec + 实现 + 封装」；M3 完成后 Agent 侧也收敛到接口 + 表驱动，全链路易用性达标。

---

## 八、文档与设计引用

- 设计目标、易用性边界、能力原语、技术背景：见 **`docs/BIDI_MAJOR_UPGRADE_DESIGN.md`**。
- 易用性痛点与短期改进：见 **`OneOPS/docs/BIDI_USABILITY_ANALYSIS.md`**。
- 本执行方案对应设计文档中的「十一、实施阶段建议」，拆解为可执行任务与验收标准。
