# OneOPS 用户手册自动生成机制

## 概述

本文档描述如何从开发者文档自动生成用户手册，实现文档的增量维护和快速发布。

## 生成流程

```
开发者文档（源）          转换规则              用户手册（目标）
    ↓                      ↓                      ↓
架构设计文档  ──→  提取功能概述  ──→  功能介绍章节
API 文档      ──→  转换为操作步骤 ──→  操作指南章节
配置文档      ──→  提取关键配置   ──→  配置说明章节
问题知识库    ──→  提取常见问题   ──→  FAQ 章节
```

## 自动生成脚本

### 1. 主生成脚本

创建 `scripts/generate-user-manual.sh`：

```bash
#!/bin/bash
# OneOPS 用户手册生成脚本

OUTPUT_DIR="docs/user-manual"
TEMP_DIR=".tmp/manual-generation"

mkdir -p $OUTPUT_DIR $TEMP_DIR

echo "=== OneOPS User Manual Generation ==="

# 1. 生成目录结构
echo "[1/6] Generating table of contents..."
./scripts/manual-generators/generate-toc.sh > $OUTPUT_DIR/README.md

# 2. 生成入门指南（从部署文档提取）
echo "[2/6] Generating getting started guide..."
./scripts/manual-generators/generate-getting-started.sh > $OUTPUT_DIR/getting-started.md

# 3. 生成功能章节（从架构文档和 API 文档提取）
echo "[3/6] Generating feature chapters..."
./scripts/manual-generators/generate-agent-management.sh > $OUTPUT_DIR/agent-management.md
./scripts/manual-generators/generate-monitoring-tasks.sh > $OUTPUT_DIR/monitoring-tasks.md
./scripts/manual-generators/generate-task-center.sh > $OUTPUT_DIR/task-center.md

# 4. 生成配置参考（从配置文档提取）
echo "[4/6] Generating configuration reference..."
./scripts/manual-generators/generate-config-reference.sh > $OUTPUT_DIR/configuration.md

# 5. 生成故障排查（从问题知识库提取）
echo "[5/6] Generating troubleshooting guide..."
./scripts/manual-generators/generate-troubleshooting.sh > $OUTPUT_DIR/troubleshooting.md

# 6. 生成 FAQ（从问题知识库提取）
echo "[6/6] Generating FAQ..."
./scripts/manual-generators/generate-faq.sh > $OUTPUT_DIR/faq.md

echo ""
echo "✅ User manual generated successfully!"
echo "Output: $OUTPUT_DIR/"
```

### 2. 功能章节生成器示例

创建 `scripts/manual-generators/generate-agent-management.sh`：

```bash
#!/bin/bash
# 从开发者文档生成"Agent 管理"用户手册章节

cat << 'EOF'
# Agent 管理

## 功能概述

Agent 是部署在目标设备上的轻量级代理程序，负责执行监控任务、部署操作和命令执行。

## Agent 列表

### 查看 Agent 列表

1. 登录 OneOPS 平台
2. 点击左侧菜单 **Agent 管理** → **Agent 列表**
3. 查看所有已注册的 Agent

![Agent 列表页面](../screenshots/agent-list.png)

### Agent 状态说明

| 状态 | 说明 | 操作建议 |
|------|------|----------|
| 在线 | Agent 正常运行，可以接收任务 | 无需操作 |
| 离线 | Agent 未连接到 Controller | 检查网络连接和 Agent 进程 |
| 异常 | Agent 连接异常或功能受限 | 查看 Agent 日志排查问题 |

EOF

# 从 API 文档提取操作步骤
echo ""
echo "## Agent 详情"
echo ""
echo "### 查看 Agent 详细信息"
echo ""
echo "1. 在 Agent 列表中，点击 Agent 名称"
echo "2. 查看 Agent 的详细信息："
echo "   - 基本信息：Agent 代码、名称、版本"
echo "   - 连接信息：Controller、连接状态、最后心跳时间"
echo "   - 能力信息：支持的任务类型、已安装的工具"
echo ""

# 从问题知识库提取常见问题
echo "## 常见问题"
echo ""
grep -A 5 "Agent.*offline" docs/knowledge/common-pitfalls.md | \
  sed 's/^### /### 问题：/' | \
  sed 's/^**根因：**/解决方案：/'
```

### 3. AI 辅助生成器

创建 `scripts/manual-generators/ai-assisted-generator.sh`：

```bash
#!/bin/bash
# 使用 AI 辅助生成用户手册章节

CHAPTER=$1
SOURCE_DOCS=$2

# 调用 AI 生成
claude-code << EOF
任务：生成用户手册章节 - $CHAPTER

源文档：
- $SOURCE_DOCS

要求：
1. 使用用户友好的语言（避免技术术语）
2. 包含操作步骤（带编号）
3. 添加注意事项和常见问题
4. 使用表格和列表提高可读性
5. 不超过 2000 字

输出格式：
- Markdown 格式
- 包含标题层级
- 包含示例和截图占位符

模板：
- 使用 docs/user-manual-template.md 作为参考
EOF
```

## 增量更新机制

### 1. 变更检测

```bash
#!/bin/bash
# 检测哪些文档需要更新

# 获取最近修改的源文档
CHANGED_DOCS=$(git diff --name-only HEAD~1 docs/architecture/ docs/api/)

# 映射到需要更新的用户手册章节
if echo "$CHANGED_DOCS" | grep -q "monitoring"; then
  echo "需要更新：monitoring-tasks.md"
  ./scripts/manual-generators/generate-monitoring-tasks.sh > docs/user-manual/monitoring-tasks.md
fi

if echo "$CHANGED_DOCS" | grep -q "agent"; then
  echo "需要更新：agent-management.md"
  ./scripts/manual-generators/generate-agent-management.sh > docs/user-manual/agent-management.md
fi
```

### 2. 版本标记

在每个生成的文档中添加版本信息：

```markdown
---
生成时间: 2026-05-06
源文档版本: v2.0.0
适用版本: OneOPS v2.0.0+
---

# Agent 管理

...
```

## AI 辅助的文档转换

### 任务模板：开发者文档 → 用户手册

```
任务：将开发者文档转换为用户手册

源文档：docs/architecture/monitoring-system.md

要求：
1. 提取用户关心的功能点（忽略技术实现细节）
2. 将 API 调用转换为 UI 操作步骤
3. 将技术术语转换为用户友好的语言
4. 添加操作截图占位符
5. 添加常见问题和注意事项

转换规则：
- "调用 API" → "点击按钮"
- "返回 200" → "操作成功"
- "bidi 通信" → "与 Agent 通信"
- "ledger commit" → "任务状态更新"

输出：
- 用户手册章节（Markdown）
- 不超过 2000 字
- 使用 docs/user-manual-template.md 格式
```

### 任务模板：API 文档 → 操作步骤

```
任务：将 API 文档转换为用户操作步骤

源文档：docs/api/platform2-monitoring.md
接口：POST /api/v2/platform2/monitoring/plans:apply

要求：
1. 识别这个 API 对应的 UI 操作
2. 将请求参数转换为表单字段
3. 将响应结果转换为用户可见的反馈
4. 添加操作步骤编号
5. 添加截图占位符

输出格式：
### 创建监控任务

1. 打开 **监控管理** → **监控任务**
2. 点击 **新建任务** 按钮
3. 填写任务信息：
   - 任务名称：<对应 API 的 name 参数>
   - 目标设备：<对应 API 的 target 参数>
   - 监控策略：<对应 API 的 strategy 参数>
4. 点击 **确定** 按钮
5. 等待任务创建完成

[截图：监控任务创建页面]
```

## 文档质量检查

### 1. 自动化检查脚本

```bash
#!/bin/bash
# 检查用户手册质量

echo "=== User Manual Quality Check ==="

# 检查必需章节
REQUIRED_CHAPTERS=(
  "getting-started.md"
  "agent-management.md"
  "monitoring-tasks.md"
  "task-center.md"
  "faq.md"
)

for chapter in "${REQUIRED_CHAPTERS[@]}"; do
  if [ ! -f "docs/user-manual/$chapter" ]; then
    echo "❌ 缺少章节: $chapter"
  else
    echo "✅ 章节存在: $chapter"
  fi
done

# 检查截图占位符
echo ""
echo "检查截图占位符..."
grep -r "\[截图:" docs/user-manual/ | wc -l | xargs echo "截图占位符数量:"

# 检查链接有效性
echo ""
echo "检查内部链接..."
# TODO: 实现链接检查逻辑

# 检查文档长度
echo ""
echo "检查文档长度..."
for file in docs/user-manual/*.md; do
  words=$(wc -w < "$file")
  if [ $words -gt 3000 ]; then
    echo "⚠️  文档过长: $file ($words 字)"
  fi
done
```

### 2. AI 辅助的质量审核

```
任务：审核用户手册质量

文档：docs/user-manual/monitoring-tasks.md

检查项：
1. 语言是否用户友好（无技术黑话）
2. 操作步骤是否清晰（有编号、有截图占位符）
3. 是否包含常见问题
4. 是否包含注意事项
5. 文档长度是否合适（1000-2000字）

输出：
- 质量评分（1-10分）
- 问题清单
- 改进建议
```

## 发布流程

### 1. 生成完整手册

```bash
# 生成所有章节
./scripts/generate-user-manual.sh

# 质量检查
./scripts/check-manual-quality.sh

# 生成 PDF（可选）
./scripts/generate-manual-pdf.sh
```

### 2. 版本发布

```bash
# 标记版本
git tag -a user-manual-v2.0.0 -m "User manual for OneOPS v2.0.0"

# 发布到文档站点
./scripts/publish-manual.sh
```

## Token 节约效果

### 传统方式（手写用户手册）

```
1. 阅读所有开发者文档（30000 tokens）
2. 理解功能和操作流程（10000 tokens）
3. 编写用户手册（20000 tokens）
总计：60000 tokens
```

### 自动生成方式

```
1. 脚本提取关键信息（0 tokens，脚本执行）
2. AI 转换语言风格（5000 tokens）
3. AI 补充操作步骤（3000 tokens）
总计：8000 tokens
```

**效率提升：7.5倍**

## 维护计划

### 每周维护

```bash
# 1. 检测变更
git diff --name-only HEAD~7 docs/architecture/ docs/api/

# 2. 增量更新
./scripts/update-manual-incremental.sh

# 3. 质量检查
./scripts/check-manual-quality.sh
```

### 每月维护

```bash
# 1. 完整重新生成
./scripts/generate-user-manual.sh

# 2. 人工审核
# 审核生成的内容，调整不准确的部分

# 3. 补充截图
# 替换截图占位符为真实截图

# 4. 发布新版本
./scripts/publish-manual.sh
```

## 下一步行动

1. **创建生成脚本**：实现 `scripts/generate-user-manual.sh`
2. **编写转换规则**：定义开发者文档到用户手册的转换规则
3. **测试生成流程**：生成第一版用户手册
4. **人工审核优化**：调整生成质量
5. **建立发布流程**：自动化发布到文档站点
