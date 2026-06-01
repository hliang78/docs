# OneOPS Call Tree 快速参考

## 🚀 快速开始

### 静态分析（查看所有 API 路由）

```bash
cd tools/route-analyzer
go run main.go ../../OneOPS
open route-map.md
```

### 运行时追踪（查看实际调用链）

```bash
# 1. 启动 Jaeger
./scripts/start-tracing.sh

# 2. 启动 OneOPS（新终端）
cd OneOPS
export OTEL_EXPORTER_TYPE=jaeger
export OTEL_EXPORTER_JAEGER_ENDPOINT=http://localhost:14268/api/traces
export OTEL_SAMPLER_TYPE=always_on
go run cmd/app.go

# 3. 测试追踪（新终端）
./scripts/test-tracing.sh

# 4. 查看追踪
open http://localhost:16686
```

## 📊 输出示例

### 静态分析输出

```
Total Routes: 1523

### device (100 routes)
| Method | Path | Handler | Service Calls |
| GET | /api/v1/device/:code | DeviceAPI.FindByCode | DeviceSrv.FindByCode |
```

### 运行时追踪输出

```
GET /api/v1/device/:code (125ms)
├─ DeviceAPI.FindByCode (120ms)
│  └─ DeviceService.GetByCode (115ms)
│     └─ DeviceRepository.FindByCode (80ms)
```

## 🔧 常用命令

```bash
# 启动追踪环境
./scripts/start-tracing.sh

# 测试追踪
./scripts/test-tracing.sh

# 停止追踪环境
docker-compose -f docker-compose.tracing.yml down

# 重新分析路由
cd tools/route-analyzer && go run main.go ../../OneOPS

# 查看 Jaeger 日志
docker logs oneops-jaeger
```

## 🌐 访问地址

- **Jaeger UI**: http://localhost:16686
- **Jaeger Health**: http://localhost:14269/health
- **OneOPS API**: http://localhost:3001

## 📝 环境变量

```bash
# Jaeger 导出器（推荐）
export OTEL_EXPORTER_TYPE=jaeger
export OTEL_EXPORTER_JAEGER_ENDPOINT=http://localhost:14268/api/traces

# 标准输出导出器（调试用）
export OTEL_EXPORTER_TYPE=stdout

# 禁用追踪
export OTEL_EXPORTER_TYPE=none

# 采样策略
export OTEL_SAMPLER_TYPE=always_on        # 100% 采样（开发）
export OTEL_SAMPLER_TYPE=traceidratio     # 10% 采样（生产）
export OTEL_SAMPLER_TYPE=always_off       # 不采样
```

## 💡 使用技巧

### 在 Jaeger UI 中查找慢请求

1. 选择服务: `github.com/netxops/OneOps`
2. 设置最小持续时间: `100ms`
3. 点击 "Find Traces"
4. 按持续时间排序

### 在 Jaeger UI 中查找错误

1. 选择服务: `github.com/netxops/OneOps`
2. 在 Tags 中添加: `error=true`
3. 点击 "Find Traces"

### 追踪特定请求

```bash
# 生成一个 trace ID
TRACE_ID=$(openssl rand -hex 16)

# 发送带追踪头的请求
curl -H "traceparent: 00-${TRACE_ID}-$(openssl rand -hex 8)-01" \
  http://localhost:3001/api/v1/device/list
```

## 📚 文档链接

- **完整文档**: [docs/CALL_TREE_TOOLS.md](CALL_TREE_TOOLS.md)
- **追踪指南**: [OneOPS/docs/TRACING.md](../OneOPS/docs/TRACING.md)
- **代码示例**: 
  - [API 层示例](../OneOPS/app/device/api/device_with_tracing_example.go)
  - [Service 层示例](../OneOPS/app/device/service/impl/tracing_example.go)

## 🐛 常见问题

**Q: Jaeger UI 中看不到追踪？**
```bash
# 检查 Jaeger 状态
curl http://localhost:14269/health

# 检查环境变量
echo $OTEL_EXPORTER_TYPE

# 查看 OneOPS 日志
# 应该看到: "OpenTelemetry tracing initialized successfully"
```

**Q: 路由分析器找不到某些路由？**
- 检查路由是否使用标准的 Gin 方法（GET, POST, PUT, DELETE）
- 查看 `initialize/routers.go` 中的路由注册

**Q: 追踪影响性能？**
- 开发环境: 使用 `always_on` 采样（100%）
- 生产环境: 使用 `traceidratio` 采样（10%）
- 性能开销: < 5%（10% 采样率）

## 🎯 下一步

1. ✅ 运行静态分析器，了解 API 结构
2. ✅ 启动追踪环境，查看实际调用链
3. 📖 阅读 [TRACING.md](../OneOPS/docs/TRACING.md) 了解如何在代码中添加追踪
4. 🔧 在关键路径上添加自定义 span
5. 📊 在生产环境启用追踪（记得设置采样率）
