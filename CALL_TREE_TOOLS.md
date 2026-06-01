# OneOPS Call Tree 分析工具集

本工具集提供了两种方式来分析 OneOPS 的调用链：

1. **静态分析** - 扫描代码生成 API 路由映射
2. **运行时追踪** - 使用 OpenTelemetry 追踪实际的调用链

## 📊 工具 1: 静态路由分析器

### 功能

- 扫描所有路由注册代码
- 分析 API Handler 到 Service 的调用关系
- 生成详细的路由映射文档

### 使用方法

```bash
cd tools/route-analyzer
go run main.go ../../OneOPS
```

### 输出文件

1. **route-map.json** - 完整的路由信息（JSON 格式）
2. **call-chains.json** - 调用链信息（JSON 格式）
3. **route-map.md** - 人类可读的路由映射文档

### 示例输出

```markdown
### device (100 routes)

| Method | Path | Handler | Service Calls |
|--------|------|---------|---------------|
| GET | `/api/v1/device/:code` | DeviceAPI.FindByCode | DeviceSrv.FindByCode, CacheSrv.Get |
| POST | `/api/v1/device/list` | DeviceAPI.PageList | DeviceSrv.PageList, TenantSrv.Validate |
```

### 当前统计

- **总路由数**: 1523
- **覆盖模块**: 40+
- **分析的调用链**: 数百条

## 🔍 工具 2: 运行时追踪系统

### 功能

- 实时追踪 HTTP 请求的完整调用链
- 记录每个 span 的执行时间
- 捕获错误和异常
- 可视化调用关系

### 快速开始

#### 1. 启动追踪环境

```bash
./scripts/start-tracing.sh
```

这会启动 Jaeger 并设置环境变量。

#### 2. 启动 OneOPS（带追踪）

```bash
cd OneOPS

# 设置环境变量
export OTEL_EXPORTER_TYPE=jaeger
export OTEL_EXPORTER_JAEGER_ENDPOINT=http://localhost:14268/api/traces
export OTEL_SAMPLER_TYPE=always_on

# 启动应用
go run cmd/app.go
```

#### 3. 测试追踪功能

```bash
./scripts/test-tracing.sh
```

#### 4. 查看追踪数据

打开浏览器访问: http://localhost:16686

### 追踪示例

```
GET /api/v1/device/:code (125ms)
├─ DeviceAPI.FindByCode (120ms)
│  ├─ DeviceService.GetByCode (115ms)
│  │  ├─ DeviceRepository.FindByCode (80ms)
│  │  │  └─ MySQL Query (75ms)
│  │  ├─ TenantService.ValidateAccess (20ms)
│  │  └─ CacheService.Set (10ms)
│  └─ Response: 200 OK (5ms)
```

### 环境变量配置

| 变量 | 值 | 说明 |
|------|-----|------|
| `OTEL_EXPORTER_TYPE` | `jaeger` / `stdout` / `none` | 导出器类型 |
| `OTEL_EXPORTER_JAEGER_ENDPOINT` | `http://localhost:14268/api/traces` | Jaeger 端点 |
| `OTEL_SAMPLER_TYPE` | `always_on` / `traceidratio` / `always_off` | 采样策略 |

### 生产环境配置

```bash
# 使用采样，减少性能开销
export OTEL_EXPORTER_TYPE=jaeger
export OTEL_EXPORTER_JAEGER_ENDPOINT=http://jaeger-collector:14268/api/traces
export OTEL_SAMPLER_TYPE=traceidratio  # 默认 10% 采样
```

## 📁 文件结构

```
OneOPS-ALL/
├── tools/
│   └── route-analyzer/          # 静态路由分析工具
│       ├── main.go
│       ├── route-map.json       # 生成的路由映射
│       ├── call-chains.json     # 生成的调用链
│       └── route-map.md         # 生成的文档
├── scripts/
│   ├── start-tracing.sh         # 启动追踪环境
│   └── test-tracing.sh          # 测试追踪功能
├── docker-compose.tracing.yml   # Jaeger Docker 配置
└── OneOPS/
    ├── middleware/
    │   └── tracing.go           # 追踪中间件
    ├── initialize/
    │   └── tracing.go           # 追踪初始化
    ├── app/common/service/
    │   └── tracing_helper.go    # 追踪辅助函数
    ├── app/device/api/
    │   └── device_with_tracing_example.go  # API 层示例
    ├── app/device/service/impl/
    │   └── tracing_example.go   # Service 层示例
    └── docs/
        └── TRACING.md           # 详细文档
```

## 🎯 使用场景

### 场景 1: 了解 API 结构

使用**静态分析器**快速了解系统有哪些 API：

```bash
cd tools/route-analyzer
go run main.go ../../OneOPS
cat route-map.md
```

### 场景 2: 性能分析

使用**运行时追踪**找出慢请求：

1. 启动追踪环境
2. 发送请求
3. 在 Jaeger UI 中按响应时间排序
4. 查看最慢的 span

### 场景 3: 调试问题

使用**运行时追踪**定位错误：

1. 重现问题
2. 在 Jaeger UI 中搜索错误的 trace
3. 查看错误发生在哪个 span
4. 检查 span 的属性和事件

### 场景 4: 理解调用关系

结合两种工具：

1. 用静态分析器了解代码结构
2. 用运行时追踪验证实际调用

## 📚 详细文档

- **追踪使用指南**: [OneOPS/docs/TRACING.md](../OneOPS/docs/TRACING.md)
- **代码示例**: 
  - API 层: [OneOPS/app/device/api/device_with_tracing_example.go](../OneOPS/app/device/api/device_with_tracing_example.go)
  - Service 层: [OneOPS/app/device/service/impl/tracing_example.go](../OneOPS/app/device/service/impl/tracing_example.go)

## 🔧 集成到现有代码

### 步骤 1: 在 cmd/app.go 中初始化追踪

```go
import "github.com/netxops/OneOps/initialize"

func main() {
    // 初始化追踪
    shutdown, err := initialize.InitTracing("github.com/netxops/OneOps", logger)
    if err != nil {
        logger.Fatal("failed to initialize tracing", zap.Error(err))
    }
    defer shutdown(context.Background())
    
    // ... 其他初始化代码
}
```

### 步骤 2: 在路由中添加追踪中间件

```go
import "github.com/netxops/OneOps/middleware"

func (r *Router) initRouter(engine *gin.Engine) {
    // 添加追踪中间件
    engine.Use(middleware.TracingMiddleware())
    
    // ... 其他中间件和路由
}
```

### 步骤 3: 在代码中添加追踪

参考示例文件：
- `app/device/api/device_with_tracing_example.go`
- `app/device/service/impl/tracing_example.go`

## 🚀 性能影响

### 静态分析器

- **运行时间**: ~2-5 秒（扫描整个代码库）
- **性能影响**: 无（离线工具）

### 运行时追踪

- **HTTP 中间件开销**: < 1ms
- **Span 创建开销**: < 0.1ms
- **总开销**: < 5%（10% 采样率）
- **推荐采样率**: 
  - 开发环境: 100% (`always_on`)
  - 生产环境: 10% (`traceidratio`)

## 🐛 故障排查

### 问题 1: 静态分析器找不到路由

**原因**: 路由注册方式不标准

**解决**: 检查路由注册代码是否使用标准的 Gin 方法（GET, POST, PUT, DELETE）

### 问题 2: Jaeger UI 中看不到追踪

**检查清单**:
1. Jaeger 是否运行: `curl http://localhost:14269/health`
2. 环境变量是否设置: `echo $OTEL_EXPORTER_TYPE`
3. OneOPS 是否启用追踪: 查看启动日志
4. 是否发送了请求: 至少发送一个 API 请求

### 问题 3: 追踪数据不完整

**原因**: Context 没有正确传递

**解决**: 确保在所有层级都使用 `ctx context.Context` 参数

## 📞 支持

如有问题，请查看：
- [TRACING.md](../OneOPS/docs/TRACING.md) - 详细的追踪文档
- [OpenTelemetry Go 文档](https://opentelemetry.io/docs/instrumentation/go/)
- [Jaeger 文档](https://www.jaegertracing.io/docs/)

## 🎉 总结

现在你有两个强大的工具来分析 OneOPS 的调用链：

1. **静态分析器** - 快速了解代码结构
2. **运行时追踪** - 深入了解实际执行

结合使用这两个工具，你可以：
- 快速定位性能瓶颈
- 理解复杂的调用关系
- 调试生产问题
- 优化系统架构
