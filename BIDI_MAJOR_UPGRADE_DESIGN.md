# Bidi 重大升级设计方案

## 一、升级目标

- **业务开发者只写两件事**：Agent 侧「能力实现」、OneOPS 侧「API 与 DTO」；Controller 与 bidi 透传**零业务代码**。
- **新增能力 = 改一处定义 + 实现一个接口**，无需在三端各写 handler、转发、转换。
- **类型安全、可生成**：入参/出参有明确类型或 IDL，减少 map/interface{} 与手写转换。
- **与现有 bidi 兼容**：升级层建在现有 `Communicator` 之上，可渐进迁移。

---

## 二、易用性提炼：专注业务开发的边界

在「OneOPS ↔ Controller ↔ Agent」多角色、单机/批量/本机执行等复杂场景下，易用性的目标是：**你只写业务逻辑与对外 API，其余由平台与约定承担**。下面用「谁写什么」和「新增能力清单」把边界说清。

### 2.1 开发者只写什么 / 平台负责什么

| 维度 | 开发者只做（业务） | 平台/框架负责（非业务） |
|------|-------------------|-------------------------|
| **Agent 能力**（单机查询/管控） | ① 在 spec 中增加方法名 + 请求/响应结构（或改 IDL）；② 在 Agent 侧实现**业务接口**（如 `FileOperator.ListFiles`）；③ 在 OneOPS 侧增加**对前端的 API** 与 **DTO**，内部调平台 SDK（如 `CallAgent` 或封装好的 `ListFiles(agentCode, dirPath)`） | Controller 的**转发**（QueryAgent 通用 handler、按 agent_code 路由、白名单校验）；OneOPS 的**查 controller、发 RPC、转 DTO**（CallAgent、convert）；Agent 的 **RPC 绑定**（表驱动或生成：params 解包 → 调你实现的接口 → 打包返回） |
| **Controller 能力**（本机执行，如批量部署） | ① 在 spec 中增加方法名 + 请求/响应结构；② 在 Controller 侧实现**本机业务逻辑**（如 DeploymentManager.CreateDeployment）；③ 在 OneOPS 侧增加 API + DTO，内部调 `CallController(controllerID, method, req)` 或封装 | OneOPS 的**选 Controller、发 RPC、转 DTO**；Controller 的**方法路由**（统一入口按 method 调你的实现）；连接、超时、重试由 bidi/平台处理 |
| **对 Agent 列表下发**（策略/批量管控） | ① 复用已有 **Agent 能力**（单机 method）；② 在 OneOPS 侧增加「批量」API，内部调 `CallAgentBatch` 或具名封装（如 `ApplyTeleabsStrategyToAgents(controllerID, agentCodes, strategyID)`） | Controller 的**按 agent_codes 循环转发**（QueryAgentBatch 或具名 handler）；Agent 侧**无需新增**，只实现单机能力 |

**一句话**：你只关心「能力叫什么、入参出参是什么、在谁身上执行、对外 API 长什么样」；路由、转发、参数映射、序列化/反序列化、超时与错误处理由平台和契约统一做。

### 2.2 新增能力操作清单（我只需这几步）

按能力类型，你只需要完成下表里的「开发者步骤」；「平台已提供」无需再写。

| 能力类型 | 开发者步骤 | 平台已提供 |
|----------|------------|------------|
| **单 Agent 能力**（如新加「读某配置」） | 1. spec：加方法名 + Req/Resp 结构<br>2. Agent：实现业务接口（如 `ConfigReader.Read(path)`），并在能力表里挂上 method → 该实现<br>3. OneOPS：加 HTTP API + 调 `CallAgent(agentCode, "ReadConfig", params)` 或封装 `ReadConfig(ctx, agentCode, path)`，结果转 DTO | QueryAgent 通用转发、CallAgent、白名单、Agent 侧 params 解包/回包（表驱动或生成） |
| **Controller 能力**（如新加「批量巡检」） | 1. spec：加方法名 + Req/Resp 结构<br>2. Controller：实现本机逻辑（如 `InspectionService.BatchInspect(req)`），并在 Controller 能力路由里注册该方法<br>3. OneOPS：加 API + 调 `CallController(controllerID, "BatchInspect", req)` 或封装 | CallController、Controller 方法路由、连接与超时 |
| **对 Agent 列表下发**（如新加「批量拉日志」） | 1. 复用已有 Agent 能力（如 `CollectLogs`）；若没有则先按「单 Agent 能力」加上<br>2. OneOPS：加「批量」API，调 `CallAgentBatch(controllerID, "CollectLogs", agentCodes, params)` 或封装 `CollectLogsBatch(ctx, controllerID, agentCodes, params)` | QueryAgentBatch（Controller 内按列表转发）、单机能力已在 Agent 实现 |

**心智负担**：升级前「加一个能力」要在 OneOPS、Controller、Agent 各写 handler/转发/转换；升级后你只做 **spec + 一端或两端的业务实现 + OneOPS 对前端的 API**，Controller 转发层零业务代码、可生成或表驱动。

### 2.3 复杂场景下的易用性原则（小结）

- **单点定义**：能力名、入参、出参在 spec（或 IDL）里只写一次，三端一致；避免在三处各写一遍参数名与类型。
- **一端实现**：单 Agent 能力只在 **Agent** 实现；Controller 能力只在 **Controller** 实现；批量到多 Agent 不要求 Agent 理解「批量」，只在 Controller 做循环转发。
- **平台兜底**：路由、转发、查 controller_id、参数 snake/camel 映射、超时与错误返回、可选重试，由平台层和 bidi 统一处理；业务只处理「成功时返回什么、失败时返回什么错误信息」。
- **SDK 优先**：OneOPS 侧通过 `CallAgent` / `CallController` / `CallAgentBatch` 及封装好的能力方法（如 `ListFiles`、`DeployAgentToDevices`）与下游交互，而不是手写 HTTP 到 Controller、手拼 RPC 包。

按上述边界落地后，在复杂链路下你仍可**更专注于业务功能开发**，把「谁连谁、怎么转、怎么序列化」交给平台与能力原语。

### 2.4 复杂场景下的易用性对照（你只做哪几件事）

针对三种典型复杂场景，下面直接给出「你只做」与「平台负责」的对照，方便在实现时只盯业务、不碰透传。

| 复杂场景 | 你只做（业务） | 平台/原语负责（不用你写） |
|----------|----------------|---------------------------|
| **批量部署 Agent**（OneOPS 选目标设备 → Controller 对本机/网络执行部署） | ① spec：定义部署方法名 + 请求（含 target_devices 等）、响应（如 task_id / 进度）；② Controller 侧实现**本机部署逻辑**（如调 ansible/脚本、写 DB 状态）；③ OneOPS 侧提供「批量部署」API，调 `CallController(controllerID, "CreateDeployment", req)` 或封装 `DeployAgentToDevices(...)`；④ 若需进度：再提供「查状态」API，调 `CallController(..., "GetDeploymentStatus", ...)` | 选 Controller、发 RPC、超时重试；Controller 内方法路由；连接、序列化、错误统一返回 |
| **Teleabs / 监控任务**（选 Agent 列表 → 对每台执行同一策略或监控任务） | ① 复用已有 **Agent 能力**（如 `ApplyTeleabsStrategy`、`StartMonitor`）；若没有则先按「单 Agent 能力」在 spec + Agent 实现；② OneOPS 侧提供「对 Agent 列表执行」API，调 `CallAgentBatch(controllerID, method, agentCodes, params)` 或封装（如 `ApplyTeleabsToAgents(controllerID, agentCodes, strategyID)`） | Controller 按 agent_codes 循环转发（QueryAgentBatch）、汇总结果；单机能力已在 Agent 实现，无需再写批量逻辑 |
| **日常管理**（Controller/Agent 的查询、启停、配置等） | ① **Controller 管理**：若仅「查列表/心跳」用平台 DB+心跳即可；若需「本机能力」（如 SelfUpgrade），按「Controller 能力」在 spec + Controller 实现 + OneOPS API；② **Agent 查询/单机管控**：用 `CallAgent(agentCode, method, params)` + 已有或新增 Agent 能力；③ **Agent 批量管控**：用 `CallAgentBatch`，同上表「Teleabs/监控」 | 路由、转发、CallAgent/CallController/CallAgentBatch、白名单、超时与错误；Agent/Controller 侧表驱动绑定 |

**记忆口诀**：  
- **单机问 Agent** → 你写 Agent 能力 + OneOPS API，用 **QueryAgent**（CallAgent）。  
- **本机干一件事（含批量 payload）** → 你写 Controller 能力 + OneOPS API，用 **CallController**。  
- **对多台 Agent 干同一件事** → 你写/复用 Agent 能力 + OneOPS 批量 API，用 **QueryAgentBatch**（CallAgentBatch）。

---

## 三、技术背景与假设

以下为 bidi 链路所依赖或假定的技术背景，便于理解原语语义、实现边界与运维特性。

### 3.1 进程、连接与拓扑

- **进程模型**：OneOPS、Controller、Agent 分别为独立进程（可多实例部署）。Controller 主动连接 OneOPS（OneOPS 监听）；Agent 主动连接 Controller（Controller 监听）。形成「星形」：多 Agent 连到同一 Controller，多 Controller 连到同一 OneOPS。
- **连接与会话**：基于 TCP 长连接，上层经 yamux 等多路复用拆成多条逻辑 stream。一条连接上一个「会话」内可并发多路 RPC（不同 stream），单路 RPC 的请求与响应在**同一 stream** 上完成，保证响应能正确回传到发起方。
- **生命周期**：连接断开后由主动方（Controller / Agent）重连；重连后重新注册或心跳，状态由 OneOPS/Controller 根据心跳或注册信息维护（如在线列表、agent 归属 controller）。

### 3.2 线程与并发

- **Go 协程**：bidi 库与各端均在 Go 中实现，请求处理、心跳、重连、消息收发等由 goroutine 承载；无共享内存下的线程安全由 channel、sync 等保证。
- **RPC 处理**：收到 RPC 请求后，handler 可在**当前 goroutine** 内同步执行（bidi 中 `dispatchRequestOnStream` 在 stream 的读协程里直接调 handler），也可在**新 goroutine** 中执行以不阻塞同一连接上的其他请求；当前 bidi 为同步执行 handler，完成后在同一 stream 上写回响应。
- **调用方阻塞**：OneOPS 侧 `CallAgent` / `CallController` 为**同步**调用：发起请求后阻塞直至收到响应或超时，不默认提供异步回调；若业务需要「异步化」，由上层封装（如发请求后轮询状态、或通过事件/Webhook 接收结果）。

### 3.3 同步、异步与消息类型

- **同步 RPC（Request-Response）**：能力原语中的 QueryAgent、CallController、QueryAgentBatch 均以**同步请求-响应**方式使用：一发一收、按 seq 配对，响应即对该请求的**确认**与结果（或错误）。超时由调用方或底层设置，超时后视为失败，可重试或降级。
- **异步/单向**：心跳、注册、部分通知为**单向发送**（fire-and-forget），不要求对端返回业务响应；底层可能仍有 TCP/应用层 ack，但不作为业务语义的「确认」。长时任务（如批量部署）的进度/结果通过**轮询**（如 GetDeploymentStatus）或**心跳/事件上报**反馈，不依赖「一次 RPC 等到底」。
- **消息类型**：bidi 消息分为 Request、Response、Notification 等。能力原语建立在 Request-Response 之上；Notification 可用于订阅/发布、事件推送等扩展，不改变三种调用原语的语义。

### 3.4 确认、超时与重试

- **确认**：RPC 的 **Response** 即对 **Request** 的确认——要么返回 result，要么返回 error；调用方收到 Response 后即可结束本次调用。不要求应用层再发 ACK；若连接在响应写出前断开，调用方将收不到响应，通过超时感知失败。
- **超时**：每次 RPC 应有合理超时（如 30s）；Controller 转发到 Agent 时，若 Agent 长时间不响应，Controller 可先超时并返回错误给 OneOPS，避免无限阻塞。
- **重试**：连接断开后由 bidi 或各端做**重连**；业务层对**幂等**操作（如查询、按 id 更新）可安全重试；对非幂等操作（如「重启」）需由业务约定是否允许重复执行或做幂等键控制。

### 3.5 顺序、乱序与背压

- **顺序**：同一 stream 上请求与响应严格配对、按序回写；不同 stream 之间无全局顺序保证。QueryAgentBatch 中 Controller 对多台 Agent 的多次转发可**并发**（多 goroutine），各 Agent 返回顺序与 agent_codes 顺序不必一致，汇总时按 agent_code 映射即可。
- **背压**：若 OneOPS 或 Controller 短时间内发起大量 RPC，可能占满连接/stream 或对端处理能力；可通过限流（如 semaphore）、队列或批量合并（QueryAgentBatch）缓解，具体由实现与运维配置决定。

### 3.6 与能力原语的关系

- **QueryAgent / CallController**：同步 RPC；调用方阻塞至响应或超时；响应即确认。
- **QueryAgentBatch**：一次同步 RPC，Controller 内对多 Agent 的转发可并发执行，整体响应时间受最慢的一台或聚合逻辑影响；若需「先提交、后查结果」，可拆成 CallController（提交任务）+ 轮询/心跳（查状态）。
- 上述技术背景不改变「三种调用原语 + 两项支撑约定」的抽象；实现时需遵守超时、错误处理与并发约定，以便平台层行为可预期、可运维。

---

## 四、Bidi 能力原语（提炼）

平台层在「OneOPS ↔ Controller ↔ Agent」链路上抽象出**三种调用原语**与**两项支撑约定**，所有业务能力（单 Agent 查询/管控、批量部署、策略下发、日常管理等）均由此组合而成。

### 4.1 三种调用原语

| 原语 | 方向与语义 | 请求形态 | 响应形态 | 典型用途 |
|------|------------|----------|----------|----------|
| **QueryAgent** | OneOPS → Controller（转发）→ **单个 Agent** 执行并返回 | `(agent_code, method, params)`；Controller 按 agent_code 路由，将 method+params 转发至该 Agent | Agent 执行结果，原样回传 OneOPS | 单机查询（ListFiles、GetSystemMetrics）、单机管控（RestartAgent、UpdateConfig） |
| **CallController** | OneOPS → **Controller 本机**执行并返回 | `(controller_id, method, params)`；Controller 在本机执行 method，不转发到 Agent | Controller 执行结果 | 批量部署（DeployAgent、CreateDeployment）、部署状态（GetDeploymentStatus）、Controller 查询（GetControllerInfo）、设备列表（ListDevices）等 |
| **QueryAgentBatch** | OneOPS → Controller；Controller **对多个 Agent 分别执行同一 method** 并汇总 | `(controller_id, method, agent_codes[], params)`；Controller 遍历 agent_codes，对每个调用「单 Agent 转发」，可选聚合结果 | 如 `map[agent_code]result` 或 `[]{agent_code, result, error}` | 对 Agent 列表应用策略（ApplyTeleabsStrategy）、批量执行监控任务、批量管控（BatchRestartAgents、BatchUpdateConfig） |

**关系小结**：

- **QueryAgent**：单 Agent、单次 RPC、Controller 只做路由与转发。
- **CallController**：Controller 本机执行，payload 可含批量（如 target_devices），不按 agent 转发。
- **QueryAgentBatch**：单次 RPC 带 agent 列表，Controller 内循环「单 Agent 转发」，不引入新传输语义；Agent 侧仍只实现单机能力。

### 4.2 两项支撑约定

| 约定 | 内容 | 作用 |
|------|------|------|
| **能力契约（Capability Contract）** | 在 spec 中单点定义：方法名、请求/响应结构（或 Req/Resp 类型）；区分 **Agent 能力**（由 Agent 实现，经 QueryAgent / QueryAgentBatch 调用）与 **Controller 能力**（由 Controller 实现，经 CallController 调用） | 白名单校验、参数映射、类型转换、代码生成；新增能力时只改契约与实现，Controller 转发零业务代码 |
| **参数与返回约定** | 平台边界统一 **snake_case**（agent_code, dir_path）；Agent 边界可用 **camelCase**（agentCode, dirPath），在 Controller 或平台层做一次映射；响应统一为 `result` + `error` 形态 | 三端命名一致、减少手写 map 与重复转换 |

### 4.3 原语与业务场景的对应

| 业务场景 | 使用原语 | 说明 |
|----------|----------|------|
| 单 Agent 查询/管控（文件、指标、重启、升级、标签等） | **QueryAgent** | 每次一个 agent_code，Controller 转发到该 Agent |
| 批量部署 Agent（多台设备） | **CallController** | 一次 RPC，payload 含 target_devices，Controller 本机执行部署 |
| 对 Agent 列表应用策略 / 执行监控任务 / 批量管控 | **QueryAgentBatch** | 一次 RPC，payload 含 agent_codes + method + params，Controller 按列表转发 |
| Controller 列表/详情/状态、部署状态查询 | **CallController** 或 DB/心跳 | 查询类由 Controller 本机或 DB 响应 |

以下各节（五～十二）为上述原语的具体设计、实现要点及与现有代码的兼容方式。

**原语小结（一句话）**：  
- **QueryAgent**：对单台 Agent 发一条 RPC，Controller 只转发。  
- **CallController**：对 Controller 发一条 RPC，Controller 本机执行（可带批量 payload）。  
- **QueryAgentBatch**：对 Controller 发一条 RPC 带 agent 列表，Controller 对每台转发同一种 method 并可选汇总。

---

## 五、整体架构：三层模型

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    业务层（开发者只写这里）                                │
│  OneOPS: API + DTO  │  Agent: 能力接口实现（如 FileOperator.ListFiles）    │
└─────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│              Bidi 平台层（bidi/platform 或 oneops-bidi-sdk）              │
│  • 能力契约（IDL/Registry）  • 统一转发  • 参数/结果映射  • 类型转换       │
└─────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    现有 bidi 库（Communicator）                           │
│  RPC(method, params)  • 连接/会话  • 心跳  • 多路复用                     │
└─────────────────────────────────────────────────────────────────────────┘
```

- **bidi 库**：保持为通用双向 RPC + 连接管理，不关心 OneOPS/Controller/Agent 语义。
- **Bidi 平台层**：约定「能力名 ↔ 方法名 ↔ 参数/返回结构」，提供 Controller 统一转发、OneOPS 调用封装、Agent 端绑定，并可对接代码生成。
- **业务层**：只实现 Agent 能力接口、定义/使用 OneOPS DTO，必要时扩展 API。

---

## 六、核心设计（基于能力原语）

### 6.1 能力契约（单点定义）

**目标**：所有「经 Controller 到 Agent」的能力在一处定义，三端据此生成或驱动逻辑。

**方式 A：Go 优先（推荐先做）**

- 在仓库内建 `bidi/platform` 或 `OneOPS/app/platform/bidi/spec` 包。
- 为每种能力定义「请求/响应类型」与「方法名」常量，例如：

```go
// spec/capabilities.go
package spec

const MethodListFiles = "ListFiles"
const MethodCreateDirectory = "CreateDirectory"
// ...

// 请求/响应用 struct，便于后续生成 JSON 标签与转换
type ListFilesReq struct {
    AgentCode string `json:"agent_code"`
    DirPath   string `json:"dir_path"`
}
type ListFilesResp struct {
    Path  string       `json:"path"`
    Files []FileInfo   `json:"files"`
}
type FileInfo struct {
    Path    string `json:"path"`
    Size    int64  `json:"size"`
    IsDir   bool   `json:"is_dir"`
    Mode    string `json:"mode"`
    ModTime string `json:"mod_time"`
}
```

- 维护一份「能力列表」：方法名 + 请求/响应类型（或仅方法名，其余用 map），供 Controller 白名单与 OneOPS 转换使用。

**方式 B：IDL/YAML（中期）**

- 用 YAML 描述能力，例如：

```yaml
capabilities:
  - name: ListFiles
    method: ListFiles
    request:  { agent_code: string, dir_path: string }
    response: { path: string, files: []FileInfo }
  - name: CreateDirectory
    method: CreateDirectory
    request:  { agent_code: string, dir_path: string, mode: uint32 }
    response: {}
```

- 代码生成器根据 IDL 生成：Go 的 Req/Resp 结构体、Controller 的转发表、OneOPS 的 CallXxx + convert。

**统一约定**：

- 所有「平台 → Agent」的请求都带 `agent_code`（或 `agentCode`，由平台层统一做一次映射）。
- 响应统一为 `{ "result": T, "error": string }` 或当前 bidi 的 RPCResponse，便于一层解析。

### 6.2 Controller：通用 QueryAgent 转发

**目标**：Controller 不再为每个能力写一个 `handleQueryAgentXxx`，只保留「按 agent_code 路由 + 按 method 转发」。

**做法**：

- OneOPS 调用 Controller 时使用**单一 RPC 方法名**，例如 `QueryAgent`，payload 为：

```json
{
  "method": "ListFiles",
  "agent_code": "bidi-agent-001",
  "dir_path": "/"
}
```

- Controller 只注册一个 handler：

```go
oneOpsCommunicator.RegisterRPCHandler("QueryAgent", cs.handleQueryAgent)
```

- `handleQueryAgent(ctx, params)` 逻辑：

  1. 从 params 取出 `method`、`agent_code`（兼容 `agentCode`）。
  2. 校验 method 在白名单内（来自 spec 或配置）。
  3. 从 params 去掉或保留 `agent_code`，构造发给 Agent 的 params（可在这里做 snake → camel 统一映射）。
  4. `forwardToAgentByCode(agentCode, method, params)`，将结果原样返回给 OneOPS。

这样新增能力时，Controller **零代码**：只需在能力契约里加入 method，OneOPS 侧调用 `CallAgent(agentCode, "ListFiles", req)` 即可。

**兼容**：若暂时保留「每个能力一个 RPC 名」（如 `QueryAgentListFiles`），可在 Controller 内做一个路由表：`QueryAgentListFiles` → method=`ListFiles`，再走同一套 `handleQueryAgent` 逻辑，逐步收敛到单一 `QueryAgent`。

### 6.3 OneOPS：Agent 调用 SDK

**目标**：平台侧「查 controller、发 RPC、转 DTO」封装成统一 API，业务只关心「调哪个能力、传什么、得到什么类型」。

**在 OneOpsBidiService 或独立 package 中提供**：

```go
// CallAgent 通用调用：查 controller、发 QueryAgent、返回原始 result
func (s *OneOpsBidiService) CallAgent(ctx context.Context, agentCode string, method string, params map[string]interface{}) (interface{}, error)

// 能力封装（内部 CallAgent + 类型转换）
func (s *OneOpsBidiService) ListFiles(ctx context.Context, agentCode string, dirPath string) (*dto.FileListResp, error)
func (s *OneOpsBidiService) CreateDirectory(ctx context.Context, agentCode string, dirPath string, mode uint32) error
// ...
```

- `CallAgent` 内部：`getControllerIDByAgentCode(agentCode, ctx)` → `CallController(controllerID, "QueryAgent", map["method"]=method, map["agent_code"]=agentCode + params)`。
- 各能力方法内：组 params、调 `CallAgent`、用 `convertToFileListResp` 等转成 dto（可集中到 `spec` 或生成的转换函数）。

**效果**：新增能力时，OneOPS 只需加一个「能力方法 + 对应 dto 转换」，不再手写 controller 查库、RPC 名、错误处理重复逻辑。

### 6.4 Agent：能力接口 + 自动绑定

**目标**：Agent 侧业务逻辑实现「能力接口」，RPC 层只做「反序列化 → 调接口 → 序列化」，且可与契约一致。

**定义能力接口（与 spec 对应）**：

```go
// 在 agent 侧或公共 spec 包
type FileOperator interface {
    ListFiles(ctx context.Context, dirPath string) (*ListFilesResp, error)
    CreateDirectory(ctx context.Context, dirPath string, mode uint32) error
    DeleteFile(ctx context.Context, filePath string, recursive bool) error
    // ...
}
```

**Agent 启动时**：

- 实现类（如 `fileService`）注入到 `AgentService`。
- 用**表驱动**或**生成代码**把「方法名 → 实现」绑到 bidi：

```go
// 表驱动示例
var agentCapabilities = []struct {
    method string
    call   func(ctx context.Context, params map[string]interface{}) (interface{}, error)
}{
    { spec.MethodListFiles, wrapListFiles(fileService.ListFiles) },
    { spec.MethodCreateDirectory, wrapCreateDirectory(fileService.CreateDirectory) },
}
for _, cap := range agentCapabilities {
    comm.RegisterRPCHandler(cap.method, cap.call)
}
```

- `wrapListFiles` 只做：从 params 取 `dirPath`/`dir_path` → 调 `ListFiles(ctx, dirPath)` → 把返回转成 map 或 JSON 可序列化结构。

这样「列目录」等逻辑完全在 `FileOperator` 实现里，可单测；RPC 层薄且可自动生成。

### 6.5 参数/返回命名与转换统一

- **约定**：平台层对外（API、OneOPS 内部）统一用 **snake_case**（agent_code, dir_path）；Agent 与 bidi 传输可约定用 **camelCase**（agentCode, dirPath），在 Controller 或平台层边界做**一次**转换。
- **实现**：在 Controller 的 `handleQueryAgent` 内，用一张「snake → camel」表或反射，把 OneOPS 传来的 params 转成发给 Agent 的 params；Agent 返回的 result 若为 map，在 OneOPS 的 convert 里统一按 snake 或 dto 的 json 标签处理。
- **可选**：若采用 IDL/代码生成，可为每种能力生成「In/Out 结构体 + JSON 标签」，序列化/反序列化由生成代码完成，避免手写 map 取值。

### 6.6 两类能力：Agent 能力 vs Controller 能力

升级后的平台层需要**显式区分**两种 RPC 语义，才能同时覆盖「单 Agent 查询/操作」和「OneOPS 经 Controller 对批量目标设备部署 Agent」：

| 类型 | 调用关系 | 典型方法 | 批量？ |
|------|----------|----------|--------|
| **Agent 能力** | OneOPS → Controller（转发）→ **单个 Agent** | ListFiles, GetSystemMetrics, CreateDirectory, ... | 否，每次带一个 agent_code |
| **Controller 能力** | OneOPS → **Controller（执行）** | DeployAgent, CreateDeployment, GetDeploymentStatus, CancelDeployment, ListDevices, ... | 可带批量（payload 内多台设备） |

- **Agent 能力**：用前面的 `QueryAgent(agent_code, method, params)`，Controller 只做按 agent_code 路由并转发，不执行业务。
- **Controller 能力**：OneOPS 对**某个 Controller** 发 RPC（如 `DeployAgent`、`CreateDeployment`），**由 Controller 本机执行**（例如对多台设备 SSH、下发安装包、执行脚本），请求体里直接带**批量目标**（设备列表、版本、配置等），无需也不应对「多个 Agent」逐个转发。

这样设计后，「OneOPS 通过 Controller 对批量目标设备部署 Agent」**天然被涵盖**：属于 Controller 能力，一次 RPC、批量在 payload 内。

---

## 七、「批量部署 Agent」在升级方案中的位置

### 6.1 流程对应

- **OneOPS**：选好目标设备列表、版本、配置后，调用平台层封装，例如  
  `DeployAgentToDevices(ctx, controllerID, req)` 或 `CreateDeployment(ctx, controllerID, req)`，  
  其中 `req` 内包含 `target_devices` / `target_devices` 等批量信息。
- **平台层**：根据 controllerID 拿到与 Controller 的 bidi 连接，发**单次** RPC，例如  
  `CallController(controllerID, "DeployAgent", req)` 或 `"CreateDeployment", req`，  
  不按设备拆成多次、也不走 `QueryAgent`。
- **Controller**：注册一个 handler（如 `DeployAgent` 或 `CreateDeployment`），在**本机**执行批量逻辑：遍历目标设备、SSH/脚本/下发包、写库、上报状态等；可选通过心跳或单独 RPC（如 `HandleControllerStatusUpdate`、`GetDeploymentStatus`）把进度/结果回传给 OneOPS。

与「单 Agent 能力」的对比：

- 单 Agent：OneOPS 指定 **agent_code** → Controller 只做**转发**到该 Agent → Agent 执行并返回。
- 批量部署：OneOPS 指定 **controller_id + 批量目标** → Controller **自己执行**部署逻辑，payload 里已是多台设备，无需再按设备拆成多路 Agent RPC（部署前目标机上可能还没有 Agent）。

### 6.2 契约与 SDK 的统一

- **能力契约**：在 spec 里除 Agent 能力外，增加 **Controller 能力** 列表，例如  
  `DeployAgent` / `CreateDeployment`（Req 含 target_devices）、`GetDeploymentStatus`、`CancelDeployment` 等，请求/响应结构体与现有 DTO 对齐。
- **OneOPS SDK**：  
  - Agent 能力：`CallAgent(ctx, agentCode, method, params)` 或 `ListFiles(ctx, agentCode, dirPath)` 等，内部走 `QueryAgent`。  
  - Controller 能力：`DeployAgentToDevices(ctx, controllerID, req)`、`GetDeploymentStatus(ctx, controllerID, deploymentID)` 等，内部走 `CallController(controllerID, method, req)`。
- **Controller 注册**：  
  - 对 OneOPS 的连接上，除 `QueryAgent` 外，继续注册 `DeployAgent`、`CreateDeployment`、`GetDeploymentStatus` 等；每个能力一个 handler，或对「Controller 能力」也做一层**统一入口 + 方法路由**（类似 QueryAgent 的 method 分发），由 Controller 内部按 method 调用 DeploymentManager 等现有实现。

### 6.3 状态与进度

- 批量部署的**进度/结果**可按现有方式：Controller 在心跳里带 `deployment_status`，或 OneOPS 轮询 `GetDeploymentStatus(deployment_id)`（仍为 OneOPS → Controller 的 RPC），无需经 bidi 对「多台 Agent」做批量状态查询。
- 若未来有「已装 Agent 的设备批量执行某操作」，可拆成：OneOPS 对多台设备循环调用 `CallAgent(agentCode, method, params)`，或由平台层提供 `CallAgentBatch`（内部多路并发 CallAgent），仍不改变「单次 RPC 对单 Agent」的语义。

结论：升级后的 bidi 设计**能很好涵盖**「OneOPS 通过 Controller 对批量目标设备部署 Agent」，只要在平台层把 **Controller 能力**（含 DeployAgent/CreateDeployment）与 **Agent 能力**（QueryAgent）并列纳入契约、SDK 和注册表即可；批量信息放在单次 RPC 的 payload 中，由 Controller 本机执行。

---

## 八、「选择目标列表 + 应用 Teleabs 策略 / 对 Agent 列表执行监控任务」在升级方案中的位置

### 7.1 业务场景

- **OneOPS**：选择目标列表（设备或 Agent）、选择 Teleabs 监控策略 → 下发「对这批目标应用策略 / 执行监控任务」。
- **实际执行**：任务要在 **Agent（或 Agent 列表）** 上执行（例如 SyncAgentTasks、ApplyStrategy、StartMonitoringTask），而不是在 Controller 本机完成。
- **路径**：OneOPS → Controller → **单个或多个 Agent** 分别执行各自任务。

与「批量部署」的区别：部署是 **Controller 本机**对多台设备执行（SSH、装包）；这里是 **多个 Agent** 各自执行监控/策略任务，Controller 只做**按 agent 列表转发**。

### 7.2 模型：Controller 的「按 Agent 列表分发」能力

升级后的 bidi 可以**很好支持**该场景，无需新 transport 能力，只需在平台层把「**对 Agent 列表下发同一类任务**」做成一种 **Controller 能力**：

| 角色 | 行为 |
|------|------|
| **OneOPS** | 发**一次** RPC 到 Controller，payload 带 **agent_codes（列表）** + 策略/任务参数（如 strategy_id、task_type、params）。 |
| **Controller** | 注册一个 handler（如 `ApplyTeleabsStrategyToAgents`、`DispatchMonitoringTasks` 或通用 `QueryAgentBatch`）。Handler 内**遍历 agent_codes**，对每个 agent_code 调用现有 **forwardToAgentByCode(agentCode, method, params)**（例如 method=`SyncAgentTasks`、`ApplyStrategy`、`StartMonitoringTask`），可汇总每台结果或仅做 fire-and-forget。 |
| **Agent** | 只暴露**单 Agent 能力**（如 `SyncAgentTasks`、`ApplyStrategy`），无需感知「批量」；批量由 Controller 的「按列表转发」完成。 |

也就是说：

- **OneOPS → Controller**：仍是**单次 RPC**，payload 里带 **agent 列表 + 策略/任务参数**。
- **Controller → 多个 Agent**：在**一个** Controller 能力 handler 里**循环**调用已有的「单 Agent 转发」逻辑（forwardToAgentByCode），不新增 bidi 原语。
- **Agent**：继续只实现「单机」能力（如执行监控任务、应用策略），与现有 Agent 能力契约一致。

### 7.3 两种实现方式（按需选一或并存）

**方式 A：按业务拆 RPC（易与现有 API 对齐）**

- Controller 注册具体能力，如 `ApplyTeleabsStrategyToAgents`、`DispatchMonitoringTasks`。
- 请求体示例：`{ "agent_codes": ["a1","a2",...], "strategy_id": "xxx", "params": {...} }`。
- Controller 的 handler 内：解析 agent_codes，对每个调用 `forwardToAgentByCode(agentCode, "SyncAgentTasks" 或 "ApplyStrategy", params)`，可选汇总每台状态后返回 OneOPS。

**方式 B：通用「对 Agent 列表转发」（复用高、扩展方便）**

- Controller 注册一个通用 RPC，如 `QueryAgentBatch`，请求体：`{ "method": "SyncAgentTasks", "agent_codes": ["a1","a2",...], "params": {...} }`。
- Controller 的 handler：对每个 agent_code 调用 `forwardToAgentByCode(agentCode, method, params)`，将每台结果放入 map（agent_code → result）或列表返回。
- OneOPS 侧对「应用策略 / 执行监控任务」的 API 只需组好 agent_codes + method + params，调一次 `CallController(controllerID, "QueryAgentBatch", req)` 即可。

两种方式都只复用现有「单 Agent 转发」与 Agent 能力，不要求 bidi 或 Agent 支持「一对多」RPC。

### 7.4 与能力契约、SDK 的衔接

- **能力契约**：在 spec 中为「对 Agent 列表下发」类能力定义 Req/Resp（如 `ApplyTeleabsStrategyToAgentsReq` 含 agent_codes、strategy_id 等），或复用通用 `QueryAgentBatchReq`（method + agent_codes + params）。
- **OneOPS SDK**：提供如 `ApplyTeleabsStrategyToAgents(ctx, controllerID, agentCodes, strategyID, params)` 或通用 `CallAgentBatch(ctx, controllerID, method, agentCodes, params)`，内部走 `CallController(controllerID, "ApplyTeleabsStrategyToAgents" 或 "QueryAgentBatch", req)`。
- **目标解析**：若 OneOPS 侧选的是「目标设备列表」而非 agent_code 列表，可由 OneOPS 或平台层先根据设备解析出 agent_code 列表，再调用上述 Controller 能力；Controller 仍只按 agent_codes 转发。

### 7.5 小结

- 升级后的 bidi **能很好支持**「OneOPS 选择目标列表、应用 Teleabs 策略；选择 Agent/Agent 列表 → Controller → Agent/Agent 列表执行监控任务」。
- 做法是：把「**对 Agent 列表下发并执行某任务**」建模为 **Controller 能力**（单次 RPC，payload 含 agent_codes + 策略/任务参数），Controller 在该能力的 handler 内**按列表循环调用现有 forwardToAgentByCode**；Agent 侧只实现单机能力（如 SyncAgentTasks、ApplyStrategy）即可，无需为「批量」增加新协议或新原语。

---

## 九、Agent 与 Controller 日常管理在升级方案中的支持

### 8.1 典型日常管理诉求

| 类别 | 典型操作 | 说明 |
|------|----------|------|
| **Controller 管理** | 列表、详情、按区域查询、状态/健康、下属 Agent 数量 | 以「查询」为主，数据来自心跳落库或 Controller 连接 |
| **Agent 管理** | 列表（筛选/分页）、详情、健康/告警、系统指标、文件、服务列表 | 部分查 DB，部分需实时问 Agent 或经 Controller 转发 |
| **Agent 管控** | 单机/批量：重启、升级、更新配置、更新能力、更新标签；批量启停服务 | 需下发到目标 Agent（或经 Controller 触发），支持单机与批量 |

升级后的 bidi 通过**统一的能力分类与 OneOPS 侧 SDK**，为上述日常管理提供一致、可扩展的支持，避免每类操作各写一套透传与转换。

### 8.2 Controller 日常管理

- **列表 / 详情 / 按区域**：数据来自 OneOPS 侧 DB（Controller 注册与心跳落库），或通过已有「Controller 连接」做查询类 RPC（如 Controller 暴露 `GetControllerInfo`）。  
  **升级支持**：在平台层把「Controller 查询类」统一为 **Controller 能力**（如 `GetControllerInfo`、`ListConnectedAgents`），OneOPS 通过 `CallController(controllerID, method, params)` 或封装好的 `GetControllerDetail(ctx, controllerID)` 调用；若数据已落库，可直接查库，无需走 bidi。
- **状态 / 健康 / 下属 Agent 数**：由 Controller 心跳或 OneOPS 根据心跳/连接状态计算。  
  **升级支持**：心跳与连接状态保持现有机制；若需「实时一问一答」，可增加 Controller 能力（如 `Ping`、`GetStatus`），由平台层统一封装。

结论：Controller 日常管理 = **以 DB/心跳为主 + 少量 Controller 能力（可选）**，升级后的契约与 `CallController` SDK 可统一入口，便于扩展和运维视图一致。

### 8.3 Agent 日常管理（查询类）

- **列表（筛选/分页）**：来自 OneOPS DB（Agent 心跳/注册落库）。  
  **升级支持**：保持现有「列表查库」；若某次需要「某 Controller 下实时在线列表」，可增加 Controller 能力 `QueryAgents`（Controller 返回本机连接的 agent 列表），由 OneOPS 封装为 `ListAgentsByController(ctx, controllerID)` 等。
- **详情 / 健康 / 告警**：部分字段来自 DB，部分需实时（如指标、进程状态）。  
  **升级支持**：详情 = 库内基础信息 + 可选 `QueryAgent(agentCode, "GetAgentDetail", nil)` 或 `GetSystemMetrics` 等 **Agent 能力** 补全实时部分；健康/告警可继续用 DB 或通过 Agent 能力 `GetHealthAlerts` 等。平台层统一用 `CallAgent` / 能力封装（如 `GetAgentDetail(ctx, agentCode)`、`GetSystemMetrics(ctx, agentCode, duration)`），便于前后端与运维统一。
- **系统指标 / 文件 / 服务列表**：已属于 **Agent 能力**（ListFiles、GetSystemMetrics、ListPackages 等）。  
  **升级支持**：全部走 `QueryAgent` + 能力契约 + OneOPS SDK 封装，命名与类型统一，日常运维只调 SDK 即可。

### 8.4 Agent 日常管理（管控类：单机与批量）

- **单机**：重启、升级、更新配置/能力/标签等，均为「对单个 Agent 下发指令」。  
  **升级支持**：每类操作对应一个 **Agent 能力**（如 `RestartAgent`、`UpgradeAgent`、`UpdateCapabilities`、`UpdateAgentLabels`、`UpdateConfig`）；OneOPS 通过 `CallAgent(ctx, agentCode, method, params)` 或封装好的 `RestartAgent(ctx, agentCode)`、`UpdateAgentLabels(ctx, agentCode, labels)` 等下发，Controller 仅做 `QueryAgent` 转发。
- **批量**：批量重启、批量启停服务、批量更新配置等，即「对 Agent 列表下发同一类管控」。  
  **升级支持**：与「五、Teleabs / 监控任务」同一模式，视为 **Controller 的「按 Agent 列表分发」能力**：OneOPS 一次 RPC，payload 带 `agent_codes` + 管控参数（如 method=`RestartAgent`、params=...）；Controller 的 handler 遍历 `agent_codes`，对每个调用 `forwardToAgentByCode(agentCode, method, params)`，并可选汇总每台结果（成功/失败/原因）。  
  - 可复用通用 `QueryAgentBatch`，或为运维习惯提供具名能力如 `BatchRestartAgents`、`BatchUpdateConfig`，内部仍按列表转发。

这样，Agent 侧只需实现**单机**管控能力；批量由平台层 + Controller 的「按列表转发」统一支持，日常管理界面可一致地使用「单机 API」与「批量 API」。

### 8.5 升级后对日常管理的整体好处

- **统一入口**：Controller 管理走 `CallController` 与 Controller 能力契约；Agent 查询/管控走 `CallAgent` 与 Agent 能力契约；批量管控走「对 Agent 列表分发的 Controller 能力」。
- **类型与命名一致**：能力契约（spec）中统一定义请求/响应与方法名，OneOPS SDK 提供强类型封装（如 `GetAgentDetail`、`RestartAgent`、`BatchRestartAgents`），减少手写 map 与重复错误处理。
- **易扩展**：新增一种日常管理操作 = 在契约中增加一项 Agent/Controller 能力（或复用 QueryAgentBatch），Agent/Controller 实现对应 handler，OneOPS 增加一条 SDK 封装；Controller 转发层无需为每种操作写重复透传。
- **运维与前端**：列表/筛选/详情/健康/批量操作等，都可对应到同一套能力与 API 语义，便于统一权限、审计与监控。

结论：升级后的 bidi 通过 **Agent 能力（单机）+ Controller 能力（本机执行 + 按 Agent 列表分发）+ 统一契约与 OneOPS SDK**，可对 Agent、Controller 的日常管理需求提供**更好、一致且可扩展**的支持。

---

## 十、bidi 库本身的可选增强（不破坏兼容）

- **泛型 RPC 注册**（Go 1.18+）：  
  `RegisterRPCHandlerTyped[TReq, TResp](method string, handler func(context.Context, *TReq) (*TResp, error))`  
  库内完成 JSON 反序列化 params → TReq、TResp → JSON 作为 result，减少业务侧类型断言和 map 操作。
- **RequestID / 超时透传**：在 RPC 的 payload 或 envelope 中带 `request_id`、`timeout_ms`，Controller 转发时原样透传，便于全链路日志与取消。
- **Stream 能力**：大文件、长日志等若需流式，可在现有 stream 之上约定「流式 RPC 方法名 + 首帧参数 + 后续二进制块」的协议，平台层只负责路由与 session 绑定，业务层仍只写「读/写流」的逻辑。

以上可在 bidi 库内做成可选 API，与现有 `RegisterRPCHandler(func(ctx, interface{})(interface{}, error))` 并存。

---

## 十一、实施阶段建议

| 阶段 | 内容 | 产出 |
|------|------|------|
| **Phase 1** | Controller 通用 `QueryAgent` + 白名单；OneOPS 统一 `CallAgent(agentCode, method, params)` | 新增能力时 Controller 零代码，OneOPS 只加一层封装 |
| **Phase 2** | 能力契约（Go 优先）：spec 包（方法名 + Req/Resp 结构体）；Controller 使用白名单；OneOPS 能力方法 + 统一 convert | 单点定义、三端一致命名与类型 |
| **Phase 3** | Agent 能力接口化 + 表驱动/生成绑定；wrap 函数从 params 解包并调接口 | Agent 只实现业务接口，RPC 绑定可生成 |
| **Phase 4** | 可选：IDL/YAML + 代码生成；bidi 库 Typed RPC、RequestID、Stream 等增强 | 新增能力 = 改 IDL + 实现接口 + 生成代码 |

先完成 Phase 1～2，即可显著减少重复与心智负担；Phase 3～4 再进一步把「定义一处、生成三端」和「类型安全」做到位。

**可执行拆解**：上述阶段已转化为《Bidi 重大升级 — 执行方案》**`docs/BIDI_UPGRADE_EXECUTION_PLAN.md`**，内含按阶段的任务清单、涉及路径、依赖顺序、验收标准与建议排期，便于按步骤落地。

---

## 十二、与现有代码的兼容与迁移

- **Controller**：保留现有 `QueryAgentListFiles` 等 handler，内部改为调用通用 `handleQueryAgent`（根据当前 RPC 方法名映射到 `method`），或逐步把调用方改为统一走 `QueryAgent`。
- **OneOPS**：现有 `ListFiles`/`CreateDirectory` 等仍可保留，内部改为调用新的 `CallAgent` 或能力方法，对外 API 不变。
- **Agent**：现有 `handleListFiles` 等可先改为「从 params 解包 → 调 FileOperator.ListFiles → 打包返回」，再逐步把注册改为表驱动或生成；业务逻辑收口到 `FileOperator` 实现类。

这样可以在不中断现有功能的前提下，按模块、按能力逐步切换到「契约 + 通用转发 + 能力接口」模型，最终实现只写关键业务、其余由平台层和生成代码承担的目标。
