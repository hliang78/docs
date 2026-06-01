# OneOPS 文档体系架构

## 文档分层设计

OneOPS 文档分为4层，每层服务不同的目标受众和用途：

```
Layer 1: 开发者文档（Developer Docs）
  ├─ CLAUDE.md                    # AI 协作指南
  ├─ docs/development/            # 开发流程、规范、模板
  ├─ docs/architecture/           # 架构设计文档
  ├─ docs/api/                    # API 参考文档
  └─ docs/knowledge/              # 开发知识库

Layer 2: 运维文档（Operations Docs）
  ├─ docs/deployment/             # 部署指南
  ├─ docs/configuration/          # 配置参考
  └─ docs/troubleshooting/        # 故障排查

Layer 3: 用户手册（User Manual）
  ├─ docs/user-manual/            # 用户操作手册
  ├─ docs/tutorials/              # 教程和示例
  └─ docs/faq/                    # 常见问题

Layer 4: 产品文档（Product Docs）
  ├─ PRODUCT.md                   # 产品定位
  ├─ DESIGN.md                    # 设计原则
  └─ docs/roadmap/                # 产品路线图
```

## 文档生命周期

```
代码实现 → 开发者文档 → 运维文档 → 用户手册 → 产品文档
   ↓           ↓            ↓           ↓           ↓
 实时更新   功能完成后   测试通过后   发布前     版本发布时
```

## 文档维护原则

### 1. 单一数据源（Single Source of Truth）

- **代码即文档**：API 定义、配置结构从代码生成
- **设计文档驱动**：重大功能先写设计文档，再实现
- **用户手册最后**：从开发者文档和运维文档提取生成

### 2. 增量更新策略

- **小步更新**：每次只更新变更相关的文档
- **版本标记**：文档标注适用的版本范围
- **废弃标记**：过时内容标记 `[已废弃]` 而不是删除

### 3. AI 辅助生成

- **自动生成**：API 文档、配置参考从代码生成
- **AI 辅助**：用户手册从开发者文档转换生成
- **人工审核**：生成后必须人工审核和调整

## 目录结构

```
docs/
├── development/               # 开发流程、规范、模板
│   ├── README.md
│   ├── development-process.md
│   ├── documentation-standard.md
│   ├── backend-development-standard.md
│   ├── api-documentation-standard.md
│   ├── testing-standard.md
│   ├── templates.md
│   └── prompt-assets-analysis.md
│
├── architecture/              # 架构设计文档
│   ├── platform2-overview.md
│   ├── bidi-communication.md
│   ├── monitoring-system.md
│   └── taskcenter-design.md
│
├── api/                       # API 参考文档（自动生成）
│   ├── platform2-agent.md
│   ├── platform2-monitoring.md
│   ├── platform2-taskcenter.md
│   └── platform2-credential.md
│
├── knowledge/                 # 开发知识库
│   ├── common-pitfalls.md
│   ├── testing-strategies.md
│   ├── performance-patterns.md
│   └── security-guidelines.md
│
├── deployment/                # 部署指南
│   ├── installation.md
│   ├── upgrade.md
│   ├── backup-restore.md
│   └── high-availability.md
│
├── configuration/             # 配置参考（部分自动生成）
│   ├── oneops-config.md
│   ├── controller-config.md
│   ├── agent-config.md
│   └── telegraf-config.md
│
├── troubleshooting/           # 故障排查
│   ├── common-issues.md
│   ├── performance-tuning.md
│   └── log-analysis.md
│
├── user-manual/               # 用户手册（从其他文档生成）
│   ├── getting-started.md
│   ├── agent-management.md
│   ├── monitoring-tasks.md
│   ├── task-center.md
│   └── credential-management.md
│
├── tutorials/                 # 教程和示例
│   ├── first-deployment.md
│   ├── create-monitoring-task.md
│   └── scheduled-task-setup.md
│
├── faq/                       # 常见问题
│   └── faq.md
│
├── roadmap/                   # 产品路线图
│   └── roadmap.md
│
└── issues/                    # 问题跟踪（已创建）
    ├── README.md
    └── ISSUE-*.md
```

## 文档模板

### 架构设计文档模板

```markdown
# <功能名称> 架构设计

## 概述
<一句话描述这个功能>

## 背景和目标
- 为什么需要这个功能
- 要解决什么问题
- 设计目标

## 架构设计

### 系统架构图
```
[架构图]
```

### 核心组件
- 组件1：职责和接口
- 组件2：职责和接口

### 数据流转
1. 步骤1
2. 步骤2

## 关键设计决策
- 决策1：为什么这样设计
- 决策2：权衡和取舍

## 接口定义
<API 接口或 RPC 接口>

## 数据模型
<数据库表结构或数据结构>

## 实现要点
- 要点1
- 要点2

## 测试策略
- 单元测试覆盖
- 集成测试场景
- E2E 测试路径

## 运维考虑
- 监控指标
- 告警规则
- 故障恢复

## 未来优化
- 已知限制
- 优化方向
```

### API 文档模板（自动生成）

```markdown
# <API 名称>

## 基本信息
- 路径：`/api/v2/platform2/...`
- 方法：`POST`
- 认证：需要 Bearer Token

## 请求参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| param1 | string | 是 | 参数说明 |

## 请求示例

```json
{
  "param1": "value1"
}
```

## 响应格式

```json
{
  "code": 200,
  "data": { ... }
}
```

## 错误码

| 错误码 | 说明 | 解决方案 |
|--------|------|----------|
| 400 | 参数错误 | 检查请求参数 |

## 使用示例

```bash
curl -X POST http://localhost:3001/api/v2/platform2/... \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"param1": "value1"}'
```
```

### 用户手册模板

```markdown
# <功能名称> 使用指南

## 功能概述
<用户视角的功能描述>

## 使用场景
- 场景1：什么时候用
- 场景2：解决什么问题

## 操作步骤

### 步骤1：<操作名称>
1. 打开 <页面名称>
2. 点击 <按钮名称>
3. 填写 <表单字段>

[截图]

### 步骤2：<操作名称>
...

## 注意事项
- 注意事项1
- 注意事项2

## 常见问题

### 问题1：<问题描述>
**解决方案：** <解决方案>

### 问题2：<问题描述>
**解决方案：** <解决方案>

## 相关功能
- 相关功能1
- 相关功能2
```

## 文档更新工作流

### 1. 功能开发时

```
开发者：
1. 在 docs/architecture/ 创建设计文档
2. 实现功能
3. 更新 API 文档（或自动生成）
4. 添加代码注释

AI 辅助：
- 从代码生成 API 文档
- 检查文档完整性
```

### 2. 测试通过后

```
开发者：
1. 更新 docs/deployment/ 部署文档（如有变更）
2. 更新 docs/configuration/ 配置文档（如有变更）
3. 添加故障排查条目到 docs/troubleshooting/

AI 辅助：
- 从配置结构生成配置文档
- 从测试用例生成故障排查指南
```

### 3. 发布前

```
技术写作：
1. 从开发者文档提取用户手册内容
2. 编写教程和示例
3. 更新 FAQ

AI 辅助：
- 从架构文档生成用户手册草稿
- 从 API 文档生成操作步骤
- 从问题库生成 FAQ
```

## Token 节约策略

### 1. 文档生成的 Token 消耗

**传统方式（高消耗）：**
- AI 读取所有代码（50000+ tokens）
- AI 理解业务逻辑（10000+ tokens）
- AI 生成完整文档（5000+ tokens）
- **总计：65000+ tokens**

**优化方式（低消耗）：**
- AI 只读取接口定义和注释（2000 tokens）
- AI 使用文档模板（500 tokens）
- AI 生成文档片段（1000 tokens）
- **总计：3500 tokens**

**效率提升：18倍**

### 2. 增量更新策略

```
# 不要：重新生成整个文档
任务：更新 API 文档

# 要：只更新变更的部分
任务：更新 API 文档 - 新增 credential 参数

文件：docs/api/platform2-agent.md
位置：第45行，deployments:plan 接口
变更：新增 credential_ref 参数说明

要求：
1. 只读取该接口的定义
2. 只更新该接口的文档
3. 不要重新生成整个文档
```

## 下一步行动

1. **清理现有文档**：整理 design/ 目录的中间态文档
2. **建立文档结构**：按照本架构创建目录
3. **迁移现有内容**：将有价值的内容迁移到新结构
4. **建立生成机制**：实现自动生成脚本
5. **制定维护计划**：每周/每月的文档维护任务
