# OneOPS AI 分层成本优化策略

## 核心理念：任务分层 + 模型分层 + 成本优化

```
高成本 AI (Claude Opus/Sonnet)     低成本 AI (Claude Haiku/GPT-3.5)
        ↓                                    ↓
  分析、决策、架构设计              执行、转换、格式化
  复杂问题诊断                      简单重复任务
  代码审查                          文档生成
  方案设计                          测试执行
```

## 任务分层矩阵

| 任务类型 | 复杂度 | 推荐模型 | 成本 | 使用场景 |
|---------|--------|----------|------|----------|
| **战略层** | 高 | Opus 4.7 | $$$ | 架构设计、技术选型、复杂问题根因分析 |
| **战术层** | 中 | Sonnet 4.6 | $$ | 代码实现、Bug修复、方案评审 |
| **执行层** | 低 | Haiku 4.5 | $ | 文档生成、格式转换、测试执行 |
| **自动化层** | 极低 | 脚本/工具 | 免费 | 代码格式化、静态检查、文档提取 |

## 具体实施方案

### 1. 测试和Bug修复的分层策略

#### 场景1：Bug 诊断和修复

```
阶段1：问题分类（Haiku - 低成本）
任务：分析 bug 报告，分类问题类型

输入：
- Bug 描述
- 错误日志（前100行）

输出：
- 问题类型：前端/后端/数据库/配置/网络
- 严重程度：P0/P1/P2/P3
- 初步判断：可能的模块

成本：~500 tokens

---

阶段2：根因分析（Sonnet - 中成本）
任务：定位问题根因

输入：
- 阶段1的分类结果
- 相关代码文件（精确定位）
- 相关日志（完整）

输出：
- 根因分析
- 修复方案
- 影响评估

成本：~3000 tokens

---

阶段3：方案审核（Opus - 高成本，仅复杂问题）
任务：审核修复方案的正确性和影响

输入：
- 阶段2的修复方案
- 相关架构文档

输出：
- 方案评审意见
- 潜在风险
- 优化建议

成本：~5000 tokens
仅在：P0问题、架构变更、跨模块影响时使用

---

阶段4：修复实施（Sonnet - 中成本）
任务：实施修复

输入：
- 审核通过的方案
- 目标文件

输出：
- 修复代码
- 测试用例

成本：~2000 tokens

---

阶段5：验证报告（Haiku - 低成本）
任务：生成验证报告

输入：
- 测试结果
- 修复前后对比

输出：
- 验证报告（Markdown）

成本：~500 tokens
```

**成本对比：**
- 传统方式（全程 Opus）：~15000 tokens × $15/M = $0.225
- 分层方式：~6000 tokens × 平均 $5/M = $0.03
- **节约：87%**

#### 场景2：回归测试失败分析

```
阶段1：测试结果汇总（脚本 - 免费）
#!/bin/bash
# 提取失败的测试
grep "FAIL" test-results/*.log > failed-tests-summary.txt

---

阶段2：失败分类（Haiku - 低成本）
任务：分类失败原因

输入：failed-tests-summary.txt

输出：
- 代码问题：需要修复的测试列表
- 环境问题：需要调整环境的测试列表
- 测试用例问题：需要更新测试的列表

成本：~800 tokens

---

阶段3：逐个修复（Sonnet - 中成本）
任务：修复单个失败测试

输入：
- 单个测试的失败信息
- 相关代码文件

输出：
- 修复代码

成本：~2000 tokens/测试
```

**成本对比：**
- 传统方式（Opus 分析所有测试）：~20000 tokens × $15/M = $0.30
- 分层方式：800 + (2000 × 失败数) tokens × $5/M ≈ $0.05
- **节约：83%**

### 2. 文档化工作的分层策略

#### 场景1：API 文档生成

```
阶段1：提取接口定义（脚本 - 免费）
#!/bin/bash
# 从代码提取 API 定义
grep -A 20 "@router" OneOPS/app/platform2/**/*.go > api-definitions.txt

---

阶段2：生成文档框架（Haiku - 低成本）
任务：生成 API 文档框架

输入：api-definitions.txt

输出：
- API 文档（Markdown）
- 包含：路径、方法、参数、响应格式

成本：~1000 tokens

---

阶段3：补充示例和说明（Sonnet - 中成本，可选）
任务：补充使用示例和详细说明

输入：
- 阶段2的文档框架
- 相关测试用例

输出：
- 完整的 API 文档
- 包含：使用示例、错误处理、最佳实践

成本：~2000 tokens
仅在：核心 API、复杂 API 时使用
```

**成本对比：**
- 传统方式（Opus 从头生成）：~8000 tokens × $15/M = $0.12
- 分层方式：~1000 tokens × $1/M = $0.001
- **节约：99%**

#### 场景2：用户手册生成

```
阶段1：提取关键信息（脚本 - 免费）
#!/bin/bash
# 从开发者文档提取标题和关键段落
grep "^#" docs/architecture/*.md > manual-outline.txt

---

阶段2：转换语言风格（Haiku - 低成本）
任务：将技术文档转换为用户友好语言

输入：
- 开发者文档片段
- 用户手册模板

输出：
- 用户手册章节草稿

成本：~1500 tokens/章节

---

阶段3：补充操作步骤（Haiku - 低成本）
任务：从 API 文档生成操作步骤

输入：
- API 文档
- UI 页面结构

输出：
- 操作步骤（带编号）

成本：~1000 tokens/功能

---

阶段4：质量审核（Sonnet - 中成本，抽样）
任务：审核用户手册质量

输入：
- 生成的用户手册章节

输出：
- 质量评分
- 改进建议

成本：~2000 tokens/章节
仅审核：20%的章节（抽样）
```

**成本对比：**
- 传统方式（Opus 手写）：~50000 tokens × $15/M = $0.75
- 分层方式：~15000 tokens × $1/M = $0.015
- **节约：98%**

### 3. 代码优化的分层策略

#### 场景1：性能优化

```
阶段1：性能分析（脚本 - 免费）
# 使用 pprof 或其他工具生成性能报告
go test -bench=. -cpuprofile=cpu.prof

---

阶段2：识别瓶颈（Haiku - 低成本）
任务：从性能报告识别瓶颈

输入：
- 性能报告
- 慢查询日志

输出：
- 瓶颈清单（按影响排序）
- 初步优化建议

成本：~1000 tokens

---

阶段3：优化方案设计（Sonnet - 中成本）
任务：设计优化方案

输入：
- 瓶颈清单
- 相关代码

输出：
- 优化方案
- 预期收益
- 风险评估

成本：~3000 tokens

---

阶段4：方案审核（Opus - 高成本，仅关键优化）
任务：审核优化方案

输入：
- 优化方案
- 架构文档

输出：
- 审核意见
- 潜在风险
- 替代方案

成本：~5000 tokens
仅在：核心路径优化、架构调整时使用

---

阶段5：实施优化（Sonnet - 中成本）
任务：实施优化

输入：
- 审核通过的方案

输出：
- 优化代码
- 性能测试用例

成本：~2000 tokens
```

### 4. 工作流自动化

#### 创建任务路由器

```bash
#!/bin/bash
# AI 任务路由器 - 根据任务类型选择合适的模型

TASK_TYPE=$1
TASK_DESC=$2

case $TASK_TYPE in
  "bug-classify")
    # 使用 Haiku
    claude-code --model haiku << EOF
任务：分类 Bug
$TASK_DESC
EOF
    ;;
    
  "bug-fix")
    # 使用 Sonnet
    claude-code --model sonnet << EOF
任务：修复 Bug
$TASK_DESC
EOF
    ;;
    
  "architecture-review")
    # 使用 Opus
    claude-code --model opus << EOF
任务：架构审核
$TASK_DESC
EOF
    ;;
    
  "doc-generate")
    # 使用 Haiku
    claude-code --model haiku << EOF
任务：生成文档
$TASK_DESC
EOF
    ;;
    
  *)
    echo "未知任务类型"
    exit 1
    ;;
esac
```

#### 使用示例

```bash
# 低成本任务
./ai-router.sh bug-classify "API 返回 500 错误"
./ai-router.sh doc-generate "生成 agent API 文档"

# 中成本任务
./ai-router.sh bug-fix "修复 ISSUE-20260506-001"
./ai-router.sh code-review "审核 monitoring apply 实现"

# 高成本任务（仅必要时）
./ai-router.sh architecture-review "审核 platform2 迁移方案"
./ai-router.sh complex-debug "分析 bidi 通信死锁问题"
```

## 成本监控和优化

### 1. Token 使用追踪

```bash
#!/bin/bash
# 追踪 AI 使用成本

LOG_FILE=".ai-usage-log.csv"

# 记录每次 AI 调用
log_usage() {
  local model=$1
  local task=$2
  local tokens=$3
  local timestamp=$(date +%Y-%m-%d\ %H:%M:%S)
  
  echo "$timestamp,$model,$task,$tokens" >> $LOG_FILE
}

# 生成成本报告
generate_report() {
  echo "=== AI Usage Report ==="
  echo ""
  
  # 按模型统计
  echo "By Model:"
  awk -F',' '{model[$2]+=$4} END {for (m in model) print m": "model[m]" tokens"}' $LOG_FILE
  
  echo ""
  
  # 按任务类型统计
  echo "By Task Type:"
  awk -F',' '{task[$3]+=$4} END {for (t in task) print t": "task[t]" tokens"}' $LOG_FILE
  
  echo ""
  
  # 估算成本
  echo "Estimated Cost:"
  # Opus: $15/M, Sonnet: $3/M, Haiku: $0.25/M
  awk -F',' '
    {
      if ($2 == "opus") opus+=$4;
      else if ($2 == "sonnet") sonnet+=$4;
      else if ($2 == "haiku") haiku+=$4;
    }
    END {
      printf "Opus: $%.2f\n", opus/1000000*15;
      printf "Sonnet: $%.2f\n", sonnet/1000000*3;
      printf "Haiku: $%.2f\n", haiku/1000000*0.25;
      printf "Total: $%.2f\n", opus/1000000*15 + sonnet/1000000*3 + haiku/1000000*0.25;
    }
  ' $LOG_FILE
}
```

### 2. 成本优化建议

```
每周回顾：
1. 运行 generate_report 查看成本分布
2. 识别高成本任务
3. 评估是否可以降级到低成本模型
4. 优化任务描述，减少 token 消耗

每月优化：
1. 分析重复任务模式
2. 将重复任务脚本化（零成本）
3. 更新任务路由规则
4. 培训团队使用低成本模型
```

## 实施路线图

### 第1周：建立基础设施

```
1. 创建任务路由器脚本
2. 配置多模型访问
3. 建立成本追踪机制
4. 编写使用指南
```

### 第2周：迁移高频任务

```
1. 识别高频低复杂度任务
2. 迁移到 Haiku 模型
3. 验证输出质量
4. 调整提示词
```

### 第3周：优化工作流

```
1. 建立分层工作流模板
2. 培训团队使用
3. 收集反馈
4. 调整策略
```

### 第4周：全面推广

```
1. 所有任务使用分层策略
2. 监控成本变化
3. 持续优化
4. 文档化最佳实践
```

## 预期效果

### 成本节约

```
传统方式（全程 Opus）：
- Bug 修复：100次/月 × $0.225 = $22.5
- 文档生成：50次/月 × $0.12 = $6
- 代码审查：80次/月 × $0.15 = $12
- 总计：$40.5/月

分层方式：
- Bug 修复：100次/月 × $0.03 = $3
- 文档生成：50次/月 × $0.001 = $0.05
- 代码审查：80次/月 × $0.05 = $4
- 总计：$7.05/月

节约：82%
```

### 效率提升

```
- 低复杂度任务响应更快（Haiku 速度快）
- 高复杂度任务质量更高（Opus 能力强）
- 整体吞吐量提升（并行处理更多任务）
```

## 注意事项

1. **质量优先**：不要为了省钱牺牲质量，关键任务仍用高成本模型
2. **持续监控**：定期检查低成本模型的输出质量
3. **灵活调整**：根据实际效果调整任务分层策略
4. **团队培训**：确保团队理解何时使用哪个模型
