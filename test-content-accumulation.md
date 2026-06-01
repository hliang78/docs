# OneOPS 前端测试内容长期沉淀机制

## 核心问题

你说得对！当前的脚本只是**触发测试**，但真正重要的是：

1. **测试用例本身**：测什么？怎么测？
2. **测试覆盖**：哪些功能有测试？哪些没有？
3. **测试质量**：测试是否有效？是否会漏掉问题？
4. **测试维护**：功能变更后，测试如何同步更新？
5. **知识沉淀**：如何让测试成为可复用的知识资产？

## 当前状态分析

### 你已经有的测试（OneOPS-UI/scripts/）

```
✅ firewall-object-management-smoke.ts        (30526 行)
✅ firewall-online-collection-config-smoke.ts (2590 行)
✅ firewall-precheck-pages-smoke.ts           (8283 行)
✅ platform2-monitoring-workbench-smoke.ts    (32934 行)
✅ platform2-agent-deployment-preflight-smoke.ts (26142 行)
✅ task-center-smoke.ts                       (11110 行)
```

**问题：**
- 这些测试是**一次性编写**的，缺乏持续维护机制
- 测试覆盖不完整，很多功能没有测试
- 测试知识分散，没有形成体系
- 新功能开发后，测试没有同步更新

## 解决方案：测试内容的三层沉淀机制

```
Layer 1: 测试用例库（Test Case Library）
  ├─ 功能测试用例（按模块组织）
  ├─ 回归测试用例（核心路径）
  └─ 边界测试用例（异常场景）

Layer 2: 测试模式库（Test Pattern Library）
  ├─ 通用测试模式（可复用）
  ├─ 断言模式（验证方法）
  └─ 数据准备模式（测试数据）

Layer 3: 测试知识库（Test Knowledge Base）
  ├─ 测试策略文档
  ├─ 测试最佳实践
  └─ 测试问题记录
```

---

## 实施方案

### 1. 建立测试用例库

#### 目录结构

```
OneOPS-UI/
├── tests/
│   ├── test-cases/                    # 测试用例库（核心）
│   │   ├── firewall/
│   │   │   ├── object-management/
│   │   │   │   ├── test-cases.md     # 测试用例清单
│   │   │   │   ├── create-policy.test.ts
│   │   │   │   ├── edit-policy.test.ts
│   │   │   │   └── delete-policy.test.ts
│   │   │   ├── online-collection/
│   │   │   └── precheck/
│   │   ├── platform2/
│   │   │   ├── monitoring/
│   │   │   ├── agent-deployment/
│   │   │   └── task-center/
│   │   └── README.md                  # 测试用例库索引
│   │
│   ├── test-patterns/                 # 测试模式库
│   │   ├── form-validation.pattern.ts
│   │   ├── api-call.pattern.ts
│   │   ├── table-operation.pattern.ts
│   │   └── README.md
│   │
│   ├── test-data/                     # 测试数据
│   │   ├── firewall/
│   │   ├── platform2/
│   │   └── README.md
│   │
│   └── test-knowledge/                # 测试知识库
│       ├── testing-strategy.md
│       ├── best-practices.md
│       ├── common-issues.md
│       └── coverage-report.md
│
└── scripts/                           # 现有的 smoke 测试
    └── *-smoke.ts
```

#### 测试用例清单模板

```markdown
# Firewall 对象管理 - 测试用例清单

## 功能概述
防火墙对象管理功能，包括策略创建、编辑、删除、查询等操作。

## 测试覆盖矩阵

| 功能点 | 测试用例 | 优先级 | 状态 | 最后更新 | 负责人 |
|--------|---------|--------|------|----------|--------|
| 创建策略 | TC-FW-001 | P0 | ✅ 已实现 | 2026-05-06 | - |
| 编辑策略 | TC-FW-002 | P0 | ✅ 已实现 | 2026-05-06 | - |
| 删除策略 | TC-FW-003 | P0 | ✅ 已实现 | 2026-05-06 | - |
| 查询策略 | TC-FW-004 | P1 | ✅ 已实现 | 2026-05-06 | - |
| 批量操作 | TC-FW-005 | P1 | ⏳ 待实现 | - | - |
| 导入导出 | TC-FW-006 | P2 | ⏳ 待实现 | - | - |
| 权限控制 | TC-FW-007 | P1 | ❌ 未实现 | - | - |
| 异常处理 | TC-FW-008 | P1 | ⏳ 部分实现 | 2026-05-06 | - |

## 测试用例详情

### TC-FW-001: 创建策略

**前置条件：**
- 用户已登录
- 有创建策略的权限

**测试步骤：**
1. 打开防火墙对象管理页面
2. 点击"新建策略"按钮
3. 填写策略信息：
   - 策略名称：test-policy-001
   - 源地址：192.168.1.0/24
   - 目标地址：10.0.0.0/8
   - 端口：80,443
   - 动作：允许
4. 点击"确定"按钮

**预期结果：**
- 策略创建成功
- 页面显示成功提示
- 策略列表中出现新创建的策略
- 策略状态为"已生效"

**实际结果：**
- ✅ 符合预期

**测试数据：**
- 参考：`tests/test-data/firewall/create-policy-001.json`

**相关代码：**
- 页面：`src/views/firewall/firewall_object_management_ui.ts`
- API：`src/api/firewall/policy.ts`
- 测试：`tests/test-cases/firewall/object-management/create-policy.test.ts`

**备注：**
- 需要测试各种边界情况（空值、特殊字符、超长输入）
- 需要测试并发创建场景

---

### TC-FW-002: 编辑策略

（类似格式）

---

## 测试覆盖率

- 功能覆盖：60%（6/10 个功能点）
- 代码覆盖：待统计
- 场景覆盖：40%（正常场景为主，异常场景不足）

## 待补充的测试

### 高优先级（P0/P1）
1. 权限控制测试（TC-FW-007）
2. 异常处理完整测试（TC-FW-008）
3. 批量操作测试（TC-FW-005）

### 中优先级（P2）
1. 导入导出测试（TC-FW-006）
2. 性能测试（大量数据场景）
3. 兼容性测试（不同浏览器）

## 维护记录

| 日期 | 变更内容 | 变更原因 | 负责人 |
|------|---------|---------|--------|
| 2026-05-06 | 初始创建 | 建立测试用例库 | - |
| 2026-05-10 | 新增 TC-FW-009 | 新功能上线 | - |
```

---

### 2. 建立测试模式库

#### 通用测试模式

```typescript
// tests/test-patterns/form-validation.pattern.ts

/**
 * 表单验证测试模式
 * 可复用的表单测试逻辑
 */

export interface FormValidationTestCase {
  fieldName: string;
  label: string;
  validValues: any[];
  invalidValues: Array<{
    value: any;
    expectedError: string;
  }>;
  required: boolean;
}

export class FormValidationPattern {
  /**
   * 测试必填字段
   */
  static testRequiredField(
    fieldName: string,
    label: string,
    submitAction: () => void
  ) {
    // 1. 不填写该字段
    // 2. 点击提交
    // 3. 验证显示错误提示："{label} 不能为空"
  }

  /**
   * 测试字段格式验证
   */
  static testFieldFormat(
    fieldName: string,
    validValues: any[],
    invalidValues: Array<{ value: any; expectedError: string }>
  ) {
    // 测试有效值
    for (const value of validValues) {
      // 填写有效值
      // 验证无错误提示
    }

    // 测试无效值
    for (const { value, expectedError } of invalidValues) {
      // 填写无效值
      // 验证显示预期的错误提示
    }
  }

  /**
   * 测试字段长度限制
   */
  static testFieldLength(
    fieldName: string,
    minLength: number,
    maxLength: number
  ) {
    // 测试边界值
    // minLength - 1, minLength, maxLength, maxLength + 1
  }

  /**
   * 批量测试表单字段
   */
  static testFormFields(testCases: FormValidationTestCase[]) {
    for (const testCase of testCases) {
      if (testCase.required) {
        this.testRequiredField(testCase.fieldName, testCase.label, () => {});
      }
      this.testFieldFormat(
        testCase.fieldName,
        testCase.validValues,
        testCase.invalidValues
      );
    }
  }
}

// 使用示例
const firewallPolicyFormTests: FormValidationTestCase[] = [
  {
    fieldName: 'policyName',
    label: '策略名称',
    required: true,
    validValues: ['test-policy', 'policy_001', 'POLICY-TEST'],
    invalidValues: [
      { value: '', expectedError: '策略名称不能为空' },
      { value: 'a'.repeat(256), expectedError: '策略名称不能超过255个字符' },
      { value: 'policy@#$', expectedError: '策略名称只能包含字母、数字、下划线和连字符' }
    ]
  },
  {
    fieldName: 'sourceAddress',
    label: '源地址',
    required: true,
    validValues: ['192.168.1.0/24', '10.0.0.1', 'any'],
    invalidValues: [
      { value: '256.1.1.1', expectedError: 'IP地址格式不正确' },
      { value: '192.168.1.0/33', expectedError: '子网掩码范围应为0-32' }
    ]
  }
];

// 在测试中使用
FormValidationPattern.testFormFields(firewallPolicyFormTests);
```

#### API 调用测试模式

```typescript
// tests/test-patterns/api-call.pattern.ts

/**
 * API 调用测试模式
 */

export class ApiCallPattern {
  /**
   * 测试 API 成功场景
   */
  static testApiSuccess(
    apiName: string,
    apiCall: () => Promise<any>,
    expectedResponse: any
  ) {
    // 1. 调用 API
    // 2. 验证返回状态码 200
    // 3. 验证返回数据结构
    // 4. 验证返回数据内容
  }

  /**
   * 测试 API 失败场景
   */
  static testApiFailure(
    apiName: string,
    apiCall: () => Promise<any>,
    expectedErrorCode: number,
    expectedErrorMessage: string
  ) {
    // 1. 调用 API
    // 2. 验证返回错误码
    // 3. 验证错误信息
    // 4. 验证页面显示错误提示
  }

  /**
   * 测试 API 超时
   */
  static testApiTimeout(apiName: string, apiCall: () => Promise<any>) {
    // 1. 模拟网络延迟
    // 2. 调用 API
    // 3. 验证超时处理
    // 4. 验证页面显示超时提示
  }

  /**
   * 测试 API 权限
   */
  static testApiPermission(apiName: string, apiCall: () => Promise<any>) {
    // 1. 使用无权限的用户
    // 2. 调用 API
    // 3. 验证返回 403
    // 4. 验证页面显示权限不足提示
  }
}
```

---

### 3. 建立测试知识库

#### 测试策略文档

```markdown
# OneOPS 前端测试策略

## 测试金字塔

```
       E2E Tests (10%)
      /              \
  Integration (30%)
 /                    \
Unit Tests (60%)
```

## 测试分层

### Unit Tests（单元测试）- 60%
- **目标**：测试单个函数、组件
- **工具**：Vitest + Vue Test Utils
- **覆盖**：工具函数、数据转换、业务逻辑
- **示例**：
  - 表单验证函数
  - 数据格式化函数
  - 状态管理逻辑

### Integration Tests（集成测试）- 30%
- **目标**：测试组件间交互、API 调用
- **工具**：Vitest + MSW（Mock Service Worker）
- **覆盖**：页面交互、API 集成、路由跳转
- **示例**：
  - 表单提交 → API 调用 → 页面更新
  - 列表查询 → 数据展示 → 分页
  - 权限控制 → 页面访问限制

### E2E Tests（端到端测试）- 10%
- **目标**：测试完整业务流程
- **工具**：Playwright / Cypress
- **覆盖**：核心业务路径
- **示例**：
  - 用户登录 → 创建策略 → 查看列表 → 编辑 → 删除
  - 部署流程：选择 Agent → 配置参数 → 执行部署 → 查看结果

## 测试优先级

### P0（必须测试）
- 核心业务流程
- 数据安全相关
- 权限控制
- 支付/计费相关

### P1（应该测试）
- 常用功能
- 数据展示
- 表单验证
- 错误处理

### P2（可以测试）
- 辅助功能
- UI 细节
- 性能优化
- 兼容性

### P3（暂不测试）
- 实验性功能
- 临时功能
- 极少使用的功能

## 测试覆盖目标

| 模块 | 单元测试 | 集成测试 | E2E测试 | 总覆盖率 |
|------|---------|---------|---------|---------|
| Firewall | 70% | 50% | 核心路径 | 60% |
| Platform2 | 80% | 60% | 核心路径 | 70% |
| Task Center | 70% | 50% | 核心路径 | 60% |

## 测试维护策略

### 新功能开发
1. 编写测试用例清单
2. 实现功能代码
3. 编写测试代码
4. 代码审查（包括测试）
5. 合并代码

### 功能变更
1. 更新测试用例清单
2. 修改功能代码
3. 更新测试代码
4. 运行回归测试
5. 合并代码

### 测试失败处理
1. 分析失败原因
2. 如果是代码问题 → 修复代码
3. 如果是测试问题 → 更新测试
4. 如果是需求变更 → 更新测试用例清单
5. 重新运行测试验证

## 测试数据管理

### 测试数据原则
- 使用固定的测试数据（可预测）
- 测试数据与生产数据隔离
- 测试后清理数据（避免污染）
- 敏感数据脱敏

### 测试数据组织
```
tests/test-data/
├── firewall/
│   ├── policies.json          # 策略测试数据
│   ├── addresses.json         # 地址测试数据
│   └── users.json             # 用户测试数据
├── platform2/
│   ├── agents.json
│   ├── deployments.json
│   └── monitoring-tasks.json
└── common/
    ├── users.json             # 通用用户数据
    └── credentials.json       # 通用凭证数据
```

## 测试环境

### 本地开发环境
- 使用 Mock 数据
- 快速反馈
- 不依赖后端

### CI/CD 环境
- 使用测试数据库
- 完整测试
- 自动化运行

### 预发布环境
- 使用真实数据（脱敏）
- 手动测试
- 验收测试
```

---

### 4. 测试内容沉淀的工作流

#### 工作流1：新功能开发

```
产品需求
    ↓
编写测试用例清单（在 tests/test-cases/）
    ↓
评审测试用例（确保覆盖完整）
    ↓
实现功能代码
    ↓
编写测试代码（参考测试模式库）
    ↓
运行测试
    ↓
代码审查（包括测试代码）
    ↓
合并代码
    ↓
更新测试覆盖率报告
```

#### 工作流2：测试失败处理

```
测试失败
    ↓
创建 ISSUE（自动）
    ↓
AI 分析失败原因（Haiku）
    ↓
判断失败类型：
  ├─ 代码问题 → 修复代码 → 重新测试
  ├─ 测试问题 → 更新测试 → 重新测试
  └─ 需求变更 → 更新测试用例清单 → 更新测试 → 重新测试
    ↓
更新测试知识库（记录问题模式）
    ↓
关闭 ISSUE
```

#### 工作流3：定期测试审查

```
每月一次
    ↓
生成测试覆盖率报告
    ↓
识别测试覆盖不足的模块
    ↓
识别过时的测试用例
    ↓
制定测试补充计划
    ↓
更新测试策略文档
```

---

### 5. AI 辅助测试内容沉淀

#### 场景1：从现有测试提取测试用例清单

```
任务：从现有测试代码提取测试用例清单

输入：
- 测试文件：OneOPS-UI/scripts/firewall-object-management-smoke.ts

要求：
1. 分析测试代码，识别测试场景
2. 提取测试步骤和预期结果
3. 生成测试用例清单（Markdown格式）
4. 识别测试覆盖的功能点
5. 识别缺失的测试场景

输出格式：
- 使用测试用例清单模板
- 保存到：tests/test-cases/firewall/object-management/test-cases.md
```

#### 场景2：生成测试模式

```
任务：从测试代码中提取可复用的测试模式

输入：
- 多个测试文件

要求：
1. 识别重复的测试逻辑
2. 提取为可复用的测试模式
3. 生成测试模式代码（TypeScript）
4. 添加使用示例

输出：
- 测试模式文件：tests/test-patterns/xxx.pattern.ts
```

#### 场景3：补充缺失的测试

```
任务：为功能补充测试用例

输入：
- 功能代码：src/views/firewall/firewall_object_management_ui.ts
- 现有测试：tests/test-cases/firewall/object-management/test-cases.md

要求：
1. 分析功能代码，识别所有功能点
2. 对比现有测试用例清单
3. 识别缺失的测试场景
4. 生成测试用例（包括边界情况、异常情况）
5. 生成测试代码

输出：
- 更新测试用例清单
- 新的测试代码文件
```

---

## 实施路线图

### 第1周：建立基础结构

```bash
# 1. 创建目录结构
mkdir -p OneOPS-UI/tests/{test-cases,test-patterns,test-data,test-knowledge}

# 2. 创建测试用例清单模板
# 3. 创建测试模式库框架
# 4. 创建测试策略文档
```

### 第2周：提取现有测试内容

```bash
# 使用 AI 从现有测试提取内容
# 1. 提取 firewall 测试用例清单
# 2. 提取 platform2 测试用例清单
# 3. 识别可复用的测试模式
```

### 第3周：补充缺失的测试

```bash
# 1. 识别测试覆盖不足的模块
# 2. 编写测试用例清单
# 3. 实现测试代码
```

### 第4周：建立维护机制

```bash
# 1. 制定测试维护规范
# 2. 培训团队
# 3. 集成到开发流程
```

---

## 总结

**测试内容沉淀的核心：**

1. **测试用例库**：记录"测什么"
2. **测试模式库**：记录"怎么测"
3. **测试知识库**：记录"为什么这样测"

**关键点：**
- 测试用例清单是**活文档**，随功能变更持续更新
- 测试模式是**可复用资产**，避免重复编写
- 测试知识是**团队财富**，避免重复踩坑

**下一步：**
让我帮你从现有的测试代码中提取测试用例清单？
