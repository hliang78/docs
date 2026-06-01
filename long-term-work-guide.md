# OneOPS 长期工作推进方案 - 实施指南

## 概述

本文档整合了 OneOPS 进入成熟期后的两大长期工作：
1. **测试、Bug修复和局部优化**
2. **文档化和用户手册生成**

并提供了**AI分层成本优化策略**，实现高效率、低成本的持续维护。

## 核心策略总结

### 1. 问题知识库系统（降低重复分析成本）

```
问题发现 → 创建 ISSUE 文件 → AI 修复 → 归档到知识库 → 未来直接引用
```

**Token 节约：** 从每次 15000 tokens 降低到 3000 tokens（**5倍提升**）

### 2. 分层测试框架（降低测试成本）

```
P0 测试（每次提交）→ P1 测试（每日）→ P2 测试（每周）
失败驱动修复 → 只修复失败的测试 → 避免全量分析
```

**Token 节约：** 从每次 20000 tokens 降低到 5000 tokens（**4倍提升**）

### 3. 文档自动生成（降低文档维护成本）

```
代码 → 脚本提取 → AI 转换 → 用户手册
增量更新 → 只更新变更部分 → 避免全量重写
```

**Token 节约：** 从每次 60000 tokens 降低到 8000 tokens（**7.5倍提升**）

### 4. AI 分层成本优化（降低 AI 使用成本）

```
Haiku（低成本）→ 分类、提取、格式化
Sonnet（中成本）→ 实现、修复、审查
Opus（高成本）→ 架构、决策、复杂分析
```

**成本节约：** 从每月 $40.5 降低到 $7.05（**82%节约**）

## 快速启动指南

### 第1步：建立基础设施（第1周）

```bash
# 1. 创建目录结构
mkdir -p docs/{issues,optimizations,knowledge,architecture,api,deployment,configuration,troubleshooting,user-manual,tutorials,faq}
mkdir -p scripts/{manual-generators,regression-tests}
mkdir -p test-data/{credentials,agents,deployments,monitoring,tasks}

# 2. 复制模板文件
cp docs/issues/README.md docs/issues/
cp docs/knowledge/common-pitfalls.md docs/knowledge/
cp docs/knowledge/testing-strategies.md docs/knowledge/

# 3. 创建问题文件模板
cat > docs/issues/ISSUE-TEMPLATE.md << 'EOF'
# ISSUE-YYYYMMDD-序号-简短描述

## 基本信息
- 发现时间：YYYY-MM-DD
- 影响模块：<模块名>
- 严重程度：P0/P1/P2/P3
- 状态：待修复/修复中/已修复/已验证

## 问题描述
<一句话描述问题>

## 复现步骤
1. <步骤1>
2. <步骤2>
3. <观察到的错误>

## 错误信息
```
<粘贴错误日志>
```

## 根因分析
<问题的根本原因>

## 修复方案
<修复方案描述>

## 相关文件
- <文件路径1>
- <文件路径2>

## 验证方法
<如何验证修复成功>
EOF

# 4. 创建 AI 任务路由器
cat > scripts/ai-router.sh << 'EOF'
#!/bin/bash
# AI 任务路由器

TASK_TYPE=$1
shift
TASK_DESC="$@"

case $TASK_TYPE in
  "bug-classify"|"doc-generate"|"test-summary")
    echo "使用 Haiku（低成本）"
    claude-code --model haiku << PROMPT
$TASK_DESC
PROMPT
    ;;
    
  "bug-fix"|"code-review"|"doc-convert")
    echo "使用 Sonnet（中成本）"
    claude-code --model sonnet << PROMPT
$TASK_DESC
PROMPT
    ;;
    
  "architecture-review"|"complex-debug"|"design-decision")
    echo "使用 Opus（高成本）"
    claude-code --model opus << PROMPT
$TASK_DESC
PROMPT
    ;;
    
  *)
    echo "错误：未知任务类型 $TASK_TYPE"
    echo "支持的类型："
    echo "  低成本：bug-classify, doc-generate, test-summary"
    echo "  中成本：bug-fix, code-review, doc-convert"
    echo "  高成本：architecture-review, complex-debug, design-decision"
    exit 1
    ;;
esac
EOF

chmod +x scripts/ai-router.sh

# 5. 创建回归测试脚本
cat > scripts/regression-tests.sh << 'EOF'
#!/bin/bash
# OneOPS 回归测试套件

echo "=== OneOPS Regression Tests ==="
mkdir -p test-results

# P0 测试（快速验证）
echo "[1/3] Running P0 Tests..."
./scripts/p0-tests.sh > test-results/p0.log 2>&1
P0_RESULT=$?

# P1 测试（完整单元测试）
echo "[2/3] Running P1 Tests..."
cd OneOPS && go test ./app/platform2/... -short > ../test-results/p1.log 2>&1
P1_RESULT=$?

# P2 测试（集成测试）
echo "[3/3] Running P2 Tests..."
./scripts/integration-tests.sh > test-results/p2.log 2>&1
P2_RESULT=$?

# 汇总
echo ""
echo "=== Test Results ==="
echo "P0: $([ $P0_RESULT -eq 0 ] && echo '✅ PASS' || echo '❌ FAIL')"
echo "P1: $([ $P1_RESULT -eq 0 ] && echo '✅ PASS' || echo '❌ FAIL')"
echo "P2: $([ $P2_RESULT -eq 0 ] && echo '✅ PASS' || echo '❌ FAIL')"

exit $([ $P0_RESULT -eq 0 ] && [ $P1_RESULT -eq 0 ] && [ $P2_RESULT -eq 0 ] && echo 0 || echo 1)
EOF

chmod +x scripts/regression-tests.sh

echo "✅ 基础设施创建完成"
```

### 第2步：清理现有文档（第1周）

```bash
# 1. 备份现有文档
mkdir -p .backup/design-$(date +%Y%m%d)
cp -r design/* .backup/design-$(date +%Y%m%d)/

# 2. 分类现有文档
# 使用 AI 辅助分类
./scripts/ai-router.sh doc-classify "
任务：分类 design/ 目录下的文档

要求：
1. 扫描 design/ 目录所有 .md 文件
2. 分类为：
   - 架构设计（移到 docs/architecture/）
   - API 文档（移到 docs/api/）
   - 问题记录（移到 docs/issues/）
   - 中间态文档（标记为待删除）
3. 输出分类清单

输出格式：
- 文件路径 | 分类 | 建议操作
"

# 3. 手动审核和移动
# 根据 AI 的分类建议，手动移动文件

# 4. 删除中间态文档
# 谨慎删除，确认无价值后再删
```

### 第3步：建立工作流（第2周）

#### Bug 修复工作流

```bash
# 1. 发现 Bug
# 用户报告或测试发现

# 2. 创建 ISSUE 文件
cp docs/issues/ISSUE-TEMPLATE.md docs/issues/ISSUE-20260507-001-monitoring-apply-timeout.md
vim docs/issues/ISSUE-20260507-001-monitoring-apply-timeout.md
# 填写问题信息

# 3. 分类问题（使用 Haiku）
./scripts/ai-router.sh bug-classify "
任务：分类 Bug

问题文件：docs/issues/ISSUE-20260507-001-monitoring-apply-timeout.md

要求：
1. 读取问题文件
2. 分类问题类型
3. 评估严重程度
4. 给出初步判断

输出：
- 问题类型：<类型>
- 严重程度：<P0/P1/P2/P3>
- 可能模块：<模块>
- 建议操作：<下一步>
"

# 4. 修复问题（使用 Sonnet）
./scripts/ai-router.sh bug-fix "
任务：修复 ISSUE-20260507-001

要求：
1. 读取 docs/issues/ISSUE-20260507-001-monitoring-apply-timeout.md
2. 按照问题文件中的修复方案实施
3. 添加测试用例
4. 验证修复成功

输出：
- 修复的文件列表
- 测试结果
"

# 5. 更新问题文件
vim docs/issues/ISSUE-20260507-001-monitoring-apply-timeout.md
# 更新状态为"已修复"

# 6. 如果是通用问题，补充到知识库
vim docs/knowledge/common-pitfalls.md
# 添加新的问题模式
```

#### 文档生成工作流

```bash
# 1. 生成 API 文档（使用 Haiku）
./scripts/ai-router.sh doc-generate "
任务：生成 API 文档

源代码：OneOPS/app/platform2/monitoring/handler/monitoring.go

要求：
1. 提取所有 API 接口定义
2. 生成 API 文档（Markdown）
3. 包含：路径、方法、参数、响应、示例

输出：
- docs/api/platform2-monitoring.md
"

# 2. 转换为用户手册（使用 Haiku）
./scripts/ai-router.sh doc-convert "
任务：将 API 文档转换为用户手册

源文档：docs/api/platform2-monitoring.md

要求：
1. 将 API 调用转换为 UI 操作步骤
2. 使用用户友好的语言
3. 添加截图占位符

输出：
- docs/user-manual/monitoring-tasks.md
"

# 3. 质量审核（使用 Sonnet，抽样）
./scripts/ai-router.sh code-review "
任务：审核用户手册质量

文档：docs/user-manual/monitoring-tasks.md

要求：
1. 检查语言是否用户友好
2. 检查操作步骤是否清晰
3. 给出改进建议

输出：
- 质量评分（1-10）
- 问题清单
- 改进建议
"
```

### 第4步：日常使用（持续）

#### 每日工作流

```bash
# 1. 运行 P0 测试
./scripts/p0-tests.sh

# 2. 如果有失败，分析原因（使用 Haiku）
./scripts/ai-router.sh test-summary "
任务：分析测试失败

测试日志：test-results/p0.log

要求：
1. 提取失败的测试
2. 分类失败原因
3. 给出修复建议

输出：
- 失败测试清单
- 失败原因分类
- 修复优先级
"

# 3. 逐个修复失败测试（使用 Sonnet）
./scripts/ai-router.sh bug-fix "
任务：修复失败测试 - TestMonitoringApply

失败信息：<从日志提取>

要求：
1. 定位失败原因
2. 修复代码或测试用例
3. 验证修复成功
"

# 4. 提交代码
git add .
git commit -m "fix: monitoring apply timeout issue"
```

#### 每周工作流

```bash
# 1. 运行完整回归测试
./scripts/regression-tests.sh

# 2. 生成测试报告
./scripts/generate-test-report.sh

# 3. 回顾问题知识库
# 识别高频问题，提取通用模式

# 4. 更新文档
# 根据本周的代码变更，增量更新文档

# 5. 成本分析
./scripts/generate-ai-usage-report.sh
# 查看 AI 使用成本，优化任务分层
```

#### 每月工作流

```bash
# 1. 完整文档重新生成
./scripts/generate-user-manual.sh

# 2. 人工审核文档
# 审核生成的用户手册，调整不准确的部分

# 3. 补充截图
# 替换截图占位符为真实截图

# 4. 发布新版本
git tag -a user-manual-v2.1.0 -m "User manual for OneOPS v2.1.0"
./scripts/publish-manual.sh

# 5. 归档旧问题
# 将已修复超过1个月的问题移到 archived/

# 6. 优化知识库
# 删除过时的条目，补充新的模式
```

## 效果预期

### Token 消耗对比

| 工作类型 | 传统方式 | 优化方式 | 节约 |
|---------|---------|---------|------|
| Bug 修复 | 15000 tokens | 3000 tokens | 80% |
| 回归测试 | 20000 tokens | 5000 tokens | 75% |
| API 文档 | 8000 tokens | 1000 tokens | 87% |
| 用户手册 | 60000 tokens | 8000 tokens | 87% |
| **总计** | **103000 tokens** | **17000 tokens** | **83%** |

### 成本对比（每月）

| 模型 | 传统方式 | 优化方式 | 节约 |
|------|---------|---------|------|
| Opus | $40.5 | $7.05 | 82% |
| 时间成本 | 100小时 | 30小时 | 70% |

### 质量提升

- **问题重复率降低**：知识库避免重复分析
- **文档一致性提升**：自动生成保证格式统一
- **测试覆盖率提升**：分层测试覆盖更全面
- **响应速度提升**：低成本模型响应更快

## 常见问题

### Q1：如何判断使用哪个模型？

**A：** 使用决策树：
```
任务是否需要架构决策或复杂分析？
  └─ YES → Opus
  └─ NO → 继续

任务是否需要代码实现或方案设计？
  └─ YES → Sonnet
  └─ NO → 继续

任务是否是格式转换或信息提取？
  └─ YES → Haiku
  └─ NO → 使用脚本
```

### Q2：低成本模型质量不够怎么办？

**A：** 采用两阶段策略：
1. 先用 Haiku 生成初稿
2. 如果质量不满意，用 Sonnet 优化
3. 关键任务直接用 Sonnet，不降级

### Q3：如何避免文档过时？

**A：** 建立触发机制：
1. 代码变更时，自动标记相关文档需要更新
2. 每周增量更新变更部分
3. 每月完整重新生成一次
4. 文档添加版本标记和更新时间

### Q4：问题知识库会不会太大？

**A：** 定期维护：
1. 每10个类似问题，提取一个通用模式
2. 每月归档已修复超过1个月的问题
3. 每季度删除过时的条目
4. 保持知识库在 50-100 个条目

## 下一步行动

### 立即行动（今天）

- [ ] 创建基础目录结构
- [ ] 复制模板文件
- [ ] 创建第一个 ISSUE 文件（练习）
- [ ] 测试 AI 任务路由器

### 本周完成

- [ ] 清理 design/ 目录
- [ ] 迁移有价值的文档到新结构
- [ ] 建立回归测试脚本
- [ ] 编写第一个文档生成脚本

### 本月完成

- [ ] 完成所有基础设施建设
- [ ] 团队培训（如何使用新工作流）
- [ ] 生成第一版用户手册
- [ ] 建立成本监控机制

### 长期目标

- [ ] 问题知识库达到 50+ 条目
- [ ] 用户手册覆盖所有核心功能
- [ ] AI 使用成本降低 80%
- [ ] 文档维护时间降低 70%

## 总结

通过**问题知识库 + 分层测试 + 文档自动生成 + AI 成本优化**四大策略，OneOPS 可以实现：

1. **高效维护**：Token 消耗降低 83%
2. **低成本运营**：AI 成本降低 82%
3. **高质量输出**：知识沉淀避免重复工作
4. **快速响应**：低成本模型提升吞吐量

这套方案适合大型项目的长期维护，可以持续优化和调整。
