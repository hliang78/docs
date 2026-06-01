# OneOPS 问题知识库索引

本目录记录 OneOPS 测试和优化阶段发现的所有问题和优化方案。

## 目录结构

```
docs/
├── issues/              # Bug 和问题记录
│   ├── ISSUE-20260506-001-controller-inventory-sync.md
│   ├── ISSUE-20260506-002-credential-ref-validation.md
│   └── ...
├── optimizations/       # 优化提案
│   ├── OPT-20260506-monitoring-query-performance.md
│   ├── OPT-20260506-frontend-bundle-size.md
│   └── ...
└── knowledge/          # 通用知识和模式
    ├── common-pitfalls.md
    ├── performance-patterns.md
    └── testing-strategies.md
```

## 问题文件模板

```markdown
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

## 影响范围
- 影响的功能：<列表>
- 影响的用户：<用户群>
- 数据风险：有/无

## 修复方案
<修复方案描述>

## 相关文件
- <文件路径1>
- <文件路径2>

## 验证方法
<如何验证修复成功>

## 相关问题
- 关联 ISSUE-xxx
- 类似 ISSUE-yyy
```

## 优化提案模板

```markdown
# OPT-YYYYMMDD-模块-优化点

## 基本信息
- 提出时间：YYYY-MM-DD
- 优化模块：<模块名>
- 优先级：高/中/低
- 状态：提案/实施中/已完成

## 当前问题
<描述当前存在的问题或瓶颈>

## 优化方案
<详细的优化方案>

## 预期收益
- 性能提升：<具体指标>
- 代码质量：<改进点>
- 用户体验：<改进点>

## 影响评估
- 修改范围：<文件数量和范围>
- 兼容性：是否影响现有功能
- 风险等级：低/中/高

## 实施计划
1. <步骤1>
2. <步骤2>

## 回滚方案
<如果出问题如何回滚>

## 验证方法
<如何验证优化效果>
```

## 使用指南

### 提交 Bug 修复任务

```
任务：修复 ISSUE-20260506-001

要求：
1. 读取 docs/issues/ISSUE-20260506-001-controller-inventory-sync.md
2. 按照问题文件中的修复方案实施
3. 执行验证方法确认修复成功
4. 更新问题文件状态为"已修复"
```

### 提交优化任务

```
任务：实施 OPT-20260506-monitoring-query-performance

要求：
1. 读取 docs/optimizations/OPT-20260506-monitoring-query-performance.md
2. 按照实施计划执行
3. 进行性能对比测试
4. 更新提案状态为"已完成"
```

## Token 节约效果

**传统方式（每次 ~15000 tokens）：**
- 用户描述问题（1000 tokens）
- AI 读取相关代码定位问题（8000 tokens）
- AI 分析根因（3000 tokens）
- AI 提出方案（2000 tokens）
- AI 实施修复（1000 tokens）

**知识库方式（每次 ~3000 tokens）：**
- 用户引用问题文件（100 tokens）
- AI 读取问题文件（500 tokens）
- AI 读取相关文件（1500 tokens）
- AI 实施修复（900 tokens）

**效率提升：5倍**

## 维护规则

1. **每周回顾**：识别高频问题，提取到 `docs/knowledge/common-pitfalls.md`
2. **问题归档**：已修复超过1个月的问题移到 `docs/issues/archived/`
3. **知识提取**：每10个类似问题，提取通用模式到知识库
4. **索引更新**：本文件保持最新的问题和优化清单
