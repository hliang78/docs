# OneOPS 测试策略和回归框架

## 1. 测试分层策略

### 1.1 测试金字塔

```
           E2E Tests (少量，关键路径)
          /                          \
    Integration Tests (适量，模块间)
   /                                    \
Unit Tests (大量，函数级)   Smoke Tests (快速验证)
```

### 1.2 各层测试的 Token 消耗策略

#### Unit Tests（单元测试）
- **特点**：数量多，但每个测试范围小
- **Token 策略**：AI 只需读取单个函数和测试文件
- **消耗**：~500 tokens/测试
- **适用场景**：工具函数、数据转换、业务逻辑

#### Smoke Tests（冒烟测试）
- **特点**：快速验证核心功能可用
- **Token 策略**：使用固定的测试脚本，AI 只需执行和分析结果
- **消耗**：~1000 tokens/测试套件
- **适用场景**：每次部署后快速验证

#### Integration Tests（集成测试）
- **特点**：验证模块间协作
- **Token 策略**：AI 读取接口定义和测试用例，不读取实现细节
- **消耗**：~2000 tokens/测试
- **适用场景**：API 测试、数据库交互、Bidi 通信

#### E2E Tests（端到端测试）
- **特点**：验证完整业务流程
- **Token 策略**：使用录制的测试脚本，AI 只负责分析失败原因
- **消耗**：~3000 tokens/测试（仅失败时）
- **适用场景**：关键业务流程（部署、监控、任务执行）

## 2. 回归测试框架

### 2.1 自动化回归测试清单

创建 `scripts/regression-tests.sh`：

```bash
#!/bin/bash
# OneOPS 回归测试套件

echo "=== OneOPS Regression Tests ==="

# 1. Backend API Tests
echo "[1/5] Running Backend API Tests..."
cd OneOPS
go test ./app/platform2/... -short -v > ../test-results/backend-api.log 2>&1
BACKEND_RESULT=$?

# 2. Bidi Communication Tests
echo "[2/5] Running Bidi Communication Tests..."
cd ../bidi
go test ./... -v > ../test-results/bidi.log 2>&1
BIDI_RESULT=$?

# 3. Frontend Smoke Tests
echo "[3/5] Running Frontend Smoke Tests..."
cd ../OneOPS-UI
yarn smoke:platform2-production-monitoring > ../test-results/frontend-smoke.log 2>&1
FRONTEND_RESULT=$?

# 4. Database Schema Validation
echo "[4/5] Running Database Schema Validation..."
cd ../OneOPS
go run scripts/validate_platform2_schema.go > ../test-results/schema-validation.log 2>&1
SCHEMA_RESULT=$?

# 5. E2E Critical Path Tests
echo "[5/5] Running E2E Critical Path Tests..."
./scripts/e2e-critical-paths.sh > ../test-results/e2e.log 2>&1
E2E_RESULT=$?

# Summary
echo ""
echo "=== Test Results Summary ==="
echo "Backend API: $([ $BACKEND_RESULT -eq 0 ] && echo '✅ PASS' || echo '❌ FAIL')"
echo "Bidi Communication: $([ $BIDI_RESULT -eq 0 ] && echo '✅ PASS' || echo '❌ FAIL')"
echo "Frontend Smoke: $([ $FRONTEND_RESULT -eq 0 ] && echo '✅ PASS' || echo '❌ FAIL')"
echo "Schema Validation: $([ $SCHEMA_RESULT -eq 0 ] && echo '✅ PASS' || echo '❌ FAIL')"
echo "E2E Critical Paths: $([ $E2E_RESULT -eq 0 ] && echo '✅ PASS' || echo '❌ FAIL')"

# Exit with failure if any test failed
[ $BACKEND_RESULT -eq 0 ] && [ $BIDI_RESULT -eq 0 ] && [ $FRONTEND_RESULT -eq 0 ] && [ $SCHEMA_RESULT -eq 0 ] && [ $E2E_RESULT -eq 0 ]
```

### 2.2 关键路径 E2E 测试

创建 `scripts/e2e-critical-paths.sh`：

```bash
#!/bin/bash
# 关键业务路径 E2E 测试

# Path 1: Agent Deployment
echo "Testing: Agent Deployment Path"
curl -X POST http://localhost:3001/api/v2/platform2/agent/deployments:plan \
  -H "Authorization: Bearer $TOKEN" \
  -d @test-data/deployment-plan.json > /tmp/deployment-result.json
# 验证结果...

# Path 2: Monitoring Apply
echo "Testing: Monitoring Apply Path"
curl -X POST http://localhost:3001/api/v2/platform2/monitoring/plans:apply \
  -H "Authorization: Bearer $TOKEN" \
  -d @test-data/monitoring-plan.json > /tmp/monitoring-result.json
# 验证结果...

# Path 3: Task Execution
echo "Testing: Task Execution Path"
curl -X POST http://localhost:3001/api/v2/platform2/taskcenter/tasks \
  -H "Authorization: Bearer $TOKEN" \
  -d @test-data/task-create.json > /tmp/task-result.json
# 验证结果...
```

### 2.3 AI 辅助的测试失败分析

当测试失败时，使用这个工作流：

```
任务：分析回归测试失败

输入：
- 测试日志：test-results/backend-api.log
- 失败的测试：TestMonitoringApply

要求：
1. 只读取失败测试的日志（不要读取所有日志）
2. 定位失败原因（代码变更、环境问题、数据问题）
3. 如果是代码问题，创建 ISSUE 文件
4. 如果是环境问题，给出修复建议
5. 如果是测试用例问题，给出修复建议

输出：
- 失败原因分析
- 修复建议
- 是否需要创建 ISSUE
```

## 3. 增量测试策略

### 3.1 基于变更的测试范围

```bash
# 获取变更的文件
CHANGED_FILES=$(git diff --name-only HEAD~1)

# 只测试受影响的模块
if echo "$CHANGED_FILES" | grep -q "app/platform2/monitoring"; then
  echo "Running monitoring tests..."
  go test ./app/platform2/monitoring/...
fi

if echo "$CHANGED_FILES" | grep -q "OneOPS-UI/src/views/platform"; then
  echo "Running frontend platform2 tests..."
  yarn smoke:platform2-production-monitoring
fi
```

### 3.2 测试优先级

**P0 测试（每次提交必跑）：**
- Platform2 验收门禁测试
- Bidi 通信基础测试
- 关键 API 冒烟测试

**P1 测试（每日构建）：**
- 完整的单元测试
- 集成测试
- 前端 smoke tests

**P2 测试（每周构建）：**
- 完整的 E2E 测试
- 性能测试
- 压力测试

## 4. 测试数据管理

### 4.1 测试数据集

创建 `test-data/` 目录：

```
test-data/
├── credentials/
│   ├── ssh-credential.json
│   └── api-credential.json
├── agents/
│   ├── linux-agent.json
│   └── windows-agent.json
├── deployments/
│   ├── deployment-plan.json
│   └── deployment-tool.json
├── monitoring/
│   ├── monitoring-plan.json
│   └── strategy-intent.json
└── tasks/
    ├── task-create.json
    └── scheduled-task.json
```

### 4.2 测试数据生成脚本

```bash
# scripts/generate-test-data.sh
# 生成一致的测试数据，避免每次手动创建
```

## 5. Token 节约的测试工作流

### 5.1 失败驱动的测试修复

```
# 传统方式（高 token 消耗）
1. 运行所有测试
2. AI 读取所有测试代码
3. AI 分析所有失败
4. AI 修复所有问题

# 优化方式（低 token 消耗）
1. 运行测试，只输出失败摘要
2. 逐个修复失败测试
3. 每次只让 AI 读取单个失败测试的代码
4. 修复后立即验证，不等待全部完成
```

### 5.2 测试修复任务模板

```
任务：修复失败的测试 - TestMonitoringApply

失败信息：
```
=== RUN   TestMonitoringApply
    apply_test.go:45: Expected status 'success', got 'timeout_unknown'
--- FAIL: TestMonitoringApply (2.34s)
```

要求：
1. 只读取 app/platform2/monitoring/service/impl/apply_test.go
2. 只读取 app/platform2/monitoring/service/impl/apply.go
3. 定位失败原因
4. 修复代码或修复测试用例
5. 运行测试验证

不要：
- 不要读取其他测试文件
- 不要重构无关代码
- 不要添加新功能
```

## 6. 持续集成建议

### 6.1 CI Pipeline 设计

```yaml
# .github/workflows/ci.yml
name: OneOPS CI

on: [push, pull_request]

jobs:
  quick-check:
    runs-on: ubuntu-latest
    steps:
      - name: P0 Tests
        run: ./scripts/p0-tests.sh
      # 5分钟内完成，快速反馈

  full-test:
    runs-on: ubuntu-latest
    needs: quick-check
    steps:
      - name: Full Regression
        run: ./scripts/regression-tests.sh
      # 30分钟内完成

  nightly:
    runs-on: ubuntu-latest
    schedule:
      - cron: '0 2 * * *'
    steps:
      - name: E2E Tests
        run: ./scripts/e2e-full.sh
      # 2小时内完成
```

## 7. 测试覆盖率追踪

### 7.1 关键模块覆盖率目标

- Platform2 核心 API：> 80%
- Bidi 通信层：> 90%
- 前端关键页面：> 70%（通过 smoke tests）

### 7.2 覆盖率报告

```bash
# 生成覆盖率报告
go test ./app/platform2/... -coverprofile=coverage.out
go tool cover -html=coverage.out -o coverage.html
```

## 使用指南

### 日常开发流程

```bash
# 1. 修改代码
vim OneOPS/app/platform2/monitoring/service/impl/apply.go

# 2. 运行相关测试
go test ./app/platform2/monitoring/... -v

# 3. 如果失败，使用 AI 分析
# 提交任务：分析测试失败 TestMonitoringApply

# 4. 修复后，运行 P0 测试
./scripts/p0-tests.sh

# 5. 提交代码
git commit -m "fix: monitoring apply ledger commit"
```

### 每周回归流程

```bash
# 1. 运行完整回归测试
./scripts/regression-tests.sh

# 2. 查看测试报告
cat test-results/summary.txt

# 3. 对于失败的测试，逐个修复
# 使用 AI 辅助分析和修复

# 4. 更新测试覆盖率报告
./scripts/generate-coverage-report.sh
```
