# OneOPS 问题发现和录入机制

## 问题来源渠道

OneOPS 的问题（ISSUE）来自多个渠道，需要建立统一的发现和录入机制。

## 1. 问题发现的6大来源

### 来源1：自动化测试失败（最主要）

```
触发时机：
- 每次代码提交后的 CI/CD
- 每日定时回归测试
- 每周完整测试套件

发现流程：
1. 测试运行器执行测试
2. 测试失败，生成日志
3. AI 自动分析失败原因
4. 自动创建 ISSUE 文件（或提示人工创建）

示例：
```bash
# CI/CD 流程中
./scripts/regression-tests.sh
if [ $? -ne 0 ]; then
  # 测试失败，触发问题录入
  ./scripts/auto-create-issue-from-test-failure.sh
fi
```
```

**自动化程度：高（80%可自动创建）**

### 来源2：用户反馈（重要）

```
触发时机：
- 用户在使用过程中遇到问题
- 用户提交工单或反馈
- 用户在群里报告问题

发现流程：
1. 用户描述问题（文字/截图/日志）
2. 技术支持或开发人员接收反馈
3. 人工判断是否是 bug
4. 创建 ISSUE 文件

示例：
用户反馈："创建监控任务时，点击确定后页面卡住"
→ 技术支持确认可复现
→ 创建 ISSUE-20260507-001-monitoring-task-ui-freeze.md
```

**自动化程度：低（需要人工判断和录入）**

### 来源3：代码审查（Code Review）

```
触发时机：
- Pull Request 代码审查
- 定期代码质量检查
- 架构审查

发现流程：
1. 审查者发现潜在问题
2. 在 PR 中标记问题
3. 如果是需要修复的 bug，创建 ISSUE
4. 如果是优化建议，创建 OPT 文件

示例：
审查者发现："这里的 SQL 查询没有索引，会导致性能问题"
→ 创建 OPT-20260507-monitoring-query-index.md
```

**自动化程度：中（可以用 AI 辅助审查）**

### 来源4：监控告警（生产环境）

```
触发时机：
- 生产环境性能告警
- 错误率告警
- 资源使用告警

发现流程：
1. 监控系统触发告警
2. 运维人员查看告警详情
3. 如果是代码问题，创建 ISSUE
4. 如果是配置问题，记录到运维文档

示例：
Prometheus 告警："API 响应时间超过 5s"
→ 运维人员排查，发现是代码问题
→ 创建 ISSUE-20260507-002-api-performance-degradation.md
```

**自动化程度：中（告警自动，但需要人工判断）**

### 来源5：日志分析（主动发现）

```
触发时机：
- 定期日志分析（每日/每周）
- 错误日志聚合分析
- 异常模式识别

发现流程：
1. 日志收集系统（Loki）聚合日志
2. AI 分析日志，识别异常模式
3. 发现高频错误或新错误
4. 自动创建 ISSUE 或提示人工确认

示例：
日志分析发现："过去24小时，'credential not found' 错误出现 500 次"
→ AI 判断为异常
→ 创建 ISSUE-20260507-003-credential-resolution-failure.md
```

**自动化程度：高（可以用 AI 自动分析）**

### 来源6：开发过程中发现（即时）

```
触发时机：
- 开发新功能时发现旧代码问题
- 重构时发现设计缺陷
- 调试时发现边界情况

发现流程：
1. 开发者在工作中发现问题
2. 立即创建 ISSUE 文件
3. 继续当前工作或立即修复

示例：
开发者在实现新功能时发现："旧的 credential resolver 不支持新的凭证类型"
→ 立即创建 ISSUE-20260507-004-credential-resolver-extension.md
→ 决定是否立即修复或稍后处理
```

**自动化程度：低（依赖开发者主动性）**

---

## 2. 自动化问题发现脚本

### 脚本1：从测试失败自动创建 ISSUE

```bash
#!/bin/bash
# scripts/auto-create-issue-from-test-failure.sh

TEST_LOG=$1
ISSUE_DIR="docs/issues"

# 提取失败的测试
FAILED_TESTS=$(grep "FAIL" $TEST_LOG | awk '{print $2}')

if [ -z "$FAILED_TESTS" ]; then
  echo "没有失败的测试"
  exit 0
fi

echo "发现 $(echo "$FAILED_TESTS" | wc -l) 个失败的测试"

# 对每个失败的测试，检查是否已有 ISSUE
for test in $FAILED_TESTS; do
  # 检查是否已存在相关 ISSUE
  EXISTING=$(grep -r "$test" $ISSUE_DIR/*.md 2>/dev/null)
  
  if [ -n "$EXISTING" ]; then
    echo "测试 $test 已有 ISSUE，跳过"
    continue
  fi
  
  # 使用 AI 分析失败原因（Haiku - 低成本）
  echo "分析测试失败：$test"
  
  # 提取失败日志
  FAILURE_LOG=$(grep -A 10 "$test" $TEST_LOG)
  
  # 调用 AI 分析
  ANALYSIS=$(claude-code --model haiku << EOF
任务：分析测试失败原因

测试名称：$test
失败日志：
$FAILURE_LOG

要求：
1. 判断失败原因（代码问题/环境问题/测试用例问题）
2. 如果是代码问题，给出简短描述
3. 评估严重程度（P0/P1/P2/P3）

输出格式（JSON）：
{
  "is_code_issue": true/false,
  "description": "简短描述",
  "severity": "P0/P1/P2/P3",
  "module": "模块名"
}
EOF
)
  
  # 解析 AI 输出
  IS_CODE_ISSUE=$(echo "$ANALYSIS" | jq -r '.is_code_issue')
  
  if [ "$IS_CODE_ISSUE" = "true" ]; then
    # 创建 ISSUE 文件
    ISSUE_ID="ISSUE-$(date +%Y%m%d)-$(ls $ISSUE_DIR/ISSUE-*.md 2>/dev/null | wc -l | xargs printf "%03d")"
    DESCRIPTION=$(echo "$ANALYSIS" | jq -r '.description')
    SEVERITY=$(echo "$ANALYSIS" | jq -r '.severity')
    MODULE=$(echo "$ANALYSIS" | jq -r '.module')
    
    ISSUE_FILE="$ISSUE_DIR/${ISSUE_ID}-${test}.md"
    
    cat > "$ISSUE_FILE" << ISSUE_EOF
# $ISSUE_ID - $test 测试失败

## 基本信息
- 发现时间：$(date +%Y-%m-%d)
- 影响模块：$MODULE
- 严重程度：$SEVERITY
- 状态：待修复
- 来源：自动化测试

## 问题描述
$DESCRIPTION

## 复现步骤
1. 运行测试：\`go test -run $test\`
2. 观察失败

## 错误信息
\`\`\`
$FAILURE_LOG
\`\`\`

## 根因分析
待分析

## 修复方案
待确定

## 相关文件
待确定

## 验证方法
重新运行测试：\`go test -run $test\`
ISSUE_EOF
    
    echo "✅ 创建 ISSUE：$ISSUE_FILE"
  else
    echo "⚠️  测试 $test 失败，但不是代码问题，跳过创建 ISSUE"
  fi
done
```

### 脚本2：从日志分析自动创建 ISSUE

```bash
#!/bin/bash
# scripts/auto-create-issue-from-logs.sh

LOG_DIR="/var/log/oneops"
ISSUE_DIR="docs/issues"
LOOKBACK_HOURS=24

# 收集最近的错误日志
echo "分析最近 $LOOKBACK_HOURS 小时的日志..."

# 提取错误日志
ERROR_LOGS=$(find $LOG_DIR -name "*.log" -mtime -1 | xargs grep "ERROR\|FATAL" | tail -1000)

# 使用 AI 分析日志模式（Haiku - 低成本）
ANALYSIS=$(claude-code --model haiku << EOF
任务：分析错误日志，识别异常模式

日志内容（最近1000条错误）：
$ERROR_LOGS

要求：
1. 识别高频错误（出现次数 > 10）
2. 识别新出现的错误（之前没见过）
3. 判断是否需要创建 ISSUE

输出格式（JSON数组）：
[
  {
    "error_pattern": "错误模式",
    "count": 次数,
    "severity": "P0/P1/P2/P3",
    "is_new": true/false,
    "should_create_issue": true/false,
    "description": "问题描述"
  }
]
EOF
)

# 解析 AI 输出，创建 ISSUE
echo "$ANALYSIS" | jq -c '.[]' | while read item; do
  SHOULD_CREATE=$(echo "$item" | jq -r '.should_create_issue')
  
  if [ "$SHOULD_CREATE" = "true" ]; then
    ERROR_PATTERN=$(echo "$item" | jq -r '.error_pattern')
    DESCRIPTION=$(echo "$item" | jq -r '.description')
    SEVERITY=$(echo "$item" | jq -r '.severity')
    COUNT=$(echo "$item" | jq -r '.count')
    
    # 检查是否已存在相关 ISSUE
    EXISTING=$(grep -r "$ERROR_PATTERN" $ISSUE_DIR/*.md 2>/dev/null)
    
    if [ -n "$EXISTING" ]; then
      echo "错误模式 '$ERROR_PATTERN' 已有 ISSUE，跳过"
      continue
    fi
    
    # 创建 ISSUE
    ISSUE_ID="ISSUE-$(date +%Y%m%d)-$(ls $ISSUE_DIR/ISSUE-*.md 2>/dev/null | wc -l | xargs printf "%03d")"
    ISSUE_FILE="$ISSUE_DIR/${ISSUE_ID}-log-analysis-$(echo $ERROR_PATTERN | tr ' ' '-' | cut -c1-30).md"
    
    cat > "$ISSUE_FILE" << ISSUE_EOF
# $ISSUE_ID - 日志分析发现高频错误

## 基本信息
- 发现时间：$(date +%Y-%m-%d)
- 影响模块：待确定
- 严重程度：$SEVERITY
- 状态：待分析
- 来源：日志分析

## 问题描述
$DESCRIPTION

错误模式：\`$ERROR_PATTERN\`
出现次数：$COUNT 次（最近 $LOOKBACK_HOURS 小时）

## 复现步骤
待确定

## 错误信息
\`\`\`
$(echo "$ERROR_LOGS" | grep "$ERROR_PATTERN" | head -5)
\`\`\`

## 根因分析
待分析

## 修复方案
待确定

## 相关文件
待确定

## 验证方法
待确定
ISSUE_EOF
    
    echo "✅ 创建 ISSUE：$ISSUE_FILE"
  fi
done
```

### 脚本3：定期问题发现任务

```bash
#!/bin/bash
# scripts/scheduled-issue-discovery.sh
# 定期运行，主动发现问题

echo "=== OneOPS 问题发现任务 ==="

# 1. 分析测试结果
echo "[1/4] 分析测试结果..."
if [ -f "test-results/latest.log" ]; then
  ./scripts/auto-create-issue-from-test-failure.sh test-results/latest.log
fi

# 2. 分析日志
echo "[2/4] 分析错误日志..."
./scripts/auto-create-issue-from-logs.sh

# 3. 检查性能指标
echo "[3/4] 检查性能指标..."
# 查询 Prometheus，检查是否有性能告警
# 如果有，创建 ISSUE

# 4. 生成问题发现报告
echo "[4/4] 生成报告..."
ISSUE_COUNT=$(ls docs/issues/ISSUE-*.md 2>/dev/null | wc -l)
NEW_ISSUES=$(find docs/issues -name "ISSUE-*.md" -mtime -1 | wc -l)

cat > docs/issues/discovery-report-$(date +%Y%m%d).md << EOF
# 问题发现报告 - $(date +%Y-%m-%d)

## 统计
- 总问题数：$ISSUE_COUNT
- 新增问题：$NEW_ISSUES（最近24小时）

## 新增问题清单
$(find docs/issues -name "ISSUE-*.md" -mtime -1 -exec basename {} \; | sed 's/^/- /')

## 待处理问题
$(grep -l "状态：待修复\|状态：待分析" docs/issues/ISSUE-*.md | wc -l) 个

## 建议
$(if [ $NEW_ISSUES -gt 5 ]; then echo "⚠️  新增问题较多，建议优先处理高优先级问题"; fi)
EOF

echo ""
echo "✅ 问题发现任务完成"
echo "新增问题：$NEW_ISSUES 个"
echo "报告：docs/issues/discovery-report-$(date +%Y%m%d).md"
```

---

## 3. 人工问题录入流程

### 场景1：用户反馈问题

```
步骤1：接收反馈
- 用户通过工单/群聊/邮件反馈问题
- 技术支持记录问题描述、截图、日志

步骤2：初步判断（使用 Haiku）
任务：判断是否是 bug

输入：
- 用户描述
- 错误截图
- 相关日志

输出：
- 是否是 bug（是/否/不确定）
- 如果是 bug，给出严重程度
- 如果不是 bug，给出原因（用户误操作/配置问题/功能缺失）

步骤3：创建 ISSUE（如果是 bug）
- 使用模板创建 ISSUE 文件
- 填写用户反馈的信息
- 标记来源为"用户反馈"

步骤4：通知开发团队
- 在团队群里通知
- 或者在项目管理工具中创建任务
```

### 场景2：开发者发现问题

```
步骤1：发现问题
- 开发者在工作中发现问题
- 判断是否需要立即修复

步骤2：快速创建 ISSUE
# 使用快捷命令
./scripts/quick-create-issue.sh "monitoring apply timeout" "P1" "monitoring"

# 脚本会自动生成 ISSUE 文件，填充基本信息

步骤3：决定处理时机
- 如果是 P0，立即修复
- 如果是 P1/P2，加入待办列表
- 如果是 P3，记录后继续当前工作
```

### 场景3：代码审查发现问题

```
步骤1：审查者标记问题
- 在 PR 中添加评论
- 标记为 "bug" 或 "optimization"

步骤2：PR 作者确认
- 如果同意是 bug，创建 ISSUE
- 如果是优化建议，创建 OPT 文件

步骤3：关联 PR 和 ISSUE
- 在 ISSUE 文件中添加 PR 链接
- 在 PR 中引用 ISSUE 编号
```

---

## 4. 问题优先级判断

### 自动判断规则

```
P0（紧急）：
- 生产环境崩溃
- 数据丢失风险
- 安全漏洞
- 核心功能完全不可用

P1（高优先级）：
- 核心功能部分不可用
- 性能严重下降（>50%）
- 影响多个用户
- 测试失败率 >20%

P2（中优先级）：
- 非核心功能不可用
- 性能轻微下降（10-50%）
- 影响少数用户
- 测试失败率 5-20%

P3（低优先级）：
- UI 小问题
- 文档错误
- 优化建议
- 测试失败率 <5%
```

### AI 辅助判断

```
任务：判断问题优先级

问题描述：<问题描述>
影响范围：<影响范围>
错误日志：<错误日志>

要求：
1. 根据问题描述判断严重程度
2. 考虑影响范围
3. 给出优先级（P0/P1/P2/P3）
4. 给出判断理由

输出格式：
{
  "priority": "P1",
  "reason": "核心功能部分不可用，影响监控任务创建",
  "estimated_impact": "影响所有需要创建监控任务的用户",
  "suggested_action": "24小时内修复"
}
```

---

## 5. 问题发现的自动化程度

| 来源 | 自动化程度 | 实施难度 | 优先级 |
|------|-----------|---------|--------|
| 测试失败 | 80% | 低 | 高 |
| 日志分析 | 70% | 中 | 高 |
| 监控告警 | 60% | 中 | 中 |
| 代码审查 | 40% | 中 | 中 |
| 用户反馈 | 20% | 低 | 高 |
| 开发发现 | 10% | 低 | 低 |

---

## 6. 实施路线图

### 第1周：建立基础

```bash
# 1. 创建问题发现脚本
./scripts/auto-create-issue-from-test-failure.sh
./scripts/auto-create-issue-from-logs.sh

# 2. 配置定时任务
crontab -e
# 每天凌晨2点运行问题发现任务
0 2 * * * /path/to/OneOPS-ALL/scripts/scheduled-issue-discovery.sh
```

### 第2周：接入测试系统

```bash
# 1. 修改 CI/CD 流程
# 在 .github/workflows/ci.yml 中添加
- name: Auto Create Issues
  if: failure()
  run: ./scripts/auto-create-issue-from-test-failure.sh test-results/latest.log
```

### 第3周：接入日志系统

```bash
# 1. 配置日志收集
# 确保所有日志都写入统一目录

# 2. 配置日志分析定时任务
# 每小时分析一次日志
0 * * * * /path/to/OneOPS-ALL/scripts/auto-create-issue-from-logs.sh
```

### 第4周：培训和推广

```
# 1. 培训团队
- 如何手动创建 ISSUE
- 如何使用快捷命令
- 如何判断问题优先级

# 2. 建立规范
- 什么情况下必须创建 ISSUE
- 什么情况下可以直接修复
- 如何关联 ISSUE 和 PR
```

---

## 7. 总结

**问题发现的完整流程：**

```
问题来源（6个渠道）
    ↓
自动/人工判断（是否是 bug）
    ↓
创建 ISSUE 文件（自动/人工）
    ↓
优先级判断（AI 辅助）
    ↓
分配和修复（工作流）
    ↓
验证和归档（知识库）
```

**自动化程度：**
- 测试失败：80%自动
- 日志分析：70%自动
- 其他来源：需要人工参与

**关键点：**
1. 不是所有问题都需要创建 ISSUE（小问题直接修复）
2. 自动创建的 ISSUE 需要人工审核
3. 定期回顾，避免 ISSUE 堆积
4. 建立闭环，修复后归档到知识库
