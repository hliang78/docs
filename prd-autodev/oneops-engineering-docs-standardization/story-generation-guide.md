# 工程文档候选稿 Story 生成指南

## 1. 目的

本指南用于把一个明确的业务方向，转化为可交给 `dev-docs` loop 执行的自动化 story package。

目标不是让 AI 确认需求，而是让 AI 基于真实源码事实，按 `docs/development-doc-templates/01-07` 生成中文候选标准文档，供人工确认、修改和定稿。

## 2. 输入：方向包

每个方向进入自动化前，先形成方向包：

```json
{
  "directionSlug": "device-v2",
  "directionName": "Device V2 入库与设备管理",
  "businessScope": "基于当前代码反向整理 Device V2 入库、管理、store/start、观测和 latest DC2 相关能力。",
  "sourceScopes": {
    "backend": [
      "OneOPS/app/device/v2/**"
    ],
    "frontend": [
      "OneOPS-UI/src/api/device/device-v2*.ts",
      "OneOPS-UI/src/views/**/DeviceV2*"
    ],
    "existingDocs": [
      "docs/development/device-v2/**",
      "docs/prd-autodev/oneops-engineering-docs-standardization/**"
    ],
    "evidence": [
      "docs/openclaw-autodev/evidence/dev-docs/**"
    ]
  },
  "outputDir": "docs/development/device-v2",
  "templateRange": "01-07",
  "excludedTemplates": [
    "08-测试用例模板.md",
    "09-接口调用文档模板.md",
    "10-自动化测试脚本说明模板.md",
    "11-Service代码审查报告模板.md"
  ],
  "targetTaskId": "dev-docs",
  "humanConfirmationRoles": [
    "产品负责人",
    "后端负责人",
    "前端负责人",
    "测试负责人",
    "安全/权限负责人"
  ]
}
```

方向包只限制自动化范围，不代表正式业务结论。

## 2.1 代码事实提取深度

生成候选文档前，worker 必须阅读足够代码，形成对当前实现的真实理解。允许先用 `rg` 定位入口，但不能只凭搜索结果填文档。

每个方向至少阅读：

| 范围 | 目的 |
|---|---|
| route/router | 确认真实 method/path/handler 和入口范围 |
| API handler/controller | 确认请求绑定、响应、错误处理和 service 调用 |
| request/response DTO | 确认 JSON 字段、校验标签、分页/过滤参数 |
| model/entity | 确认真实表名、字段、状态字段、关联字段 |
| service interface | 确认能力边界和方法契约 |
| service implementation | 确认真实业务流程、状态变化、事务、幂等、重试、外部依赖 |
| repository/DAO/GORM 调用 | 确认查询条件、更新语义、删除语义、聚合逻辑 |
| frontend API wrapper | 确认前端真实调用 method/path/参数 |
| frontend page/component | 确认页面入口、操作、表单、列表、弹窗、状态展示 |
| tests/scripts/evidence | 确认已有验证、缺失验证、历史样本 |
| existing docs/PRD | 确认人工约束、历史规划和源码差异 |

每个 story 必须产出或更新 `代码事实来源清单`。来源清单可放在目标候选文档末尾，也可放在 `docs/openclaw-autodev/evidence/dev-docs/<story-id>-code-facts.md`。

来源清单至少包含：

- 已读取关键文件。
- 文件对应的事实类型。
- 仍未读取或无法确认的范围。
- 因无法确认而保留的 `[待人工确认]`。

## 3. 输出文件约定

默认输出 7 份候选文档：

| 模板 | 输出文件 |
|---|---|
| 01-需求概要模板 | `candidate-01-requirements-summary.md` |
| 02-功能清单模板 | `candidate-02-function-list.md` |
| 03-实体属性清单模板 | `candidate-03-entity-attribute-list.md` |
| 04-原型清单模板 | `candidate-04-prototype-list.md` |
| 05-数据库设计模板 | `candidate-05-database-design.md` |
| 06-接口文档模板 | `candidate-06-api-documentation.md` |
| 07-后端开发设计模板 | `candidate-07-backend-development-design.md` |

所有候选文档必须：

- 使用中文主体。
- 保留原模板的核心标题、章节顺序和表格结构。
- 标记为 `blocked-human-confirmation`。
- 对无法从代码确认的内容使用 `[待人工确认:<role>]`。
- 明确区分 `当前真实代码事实`、`候选文档内容`、`AI 推导建议`、`规划缺口`。
- 为模型、表、接口、页面、服务流程提供源码路径或明确标记为未确认。
- 包含或链接对应的 `代码事实来源清单`。

## 4. 默认 Story 拆分

每个方向默认生成 4 个 story，使用 `executionMode: "dependency-chain"`。

| Story | 模板 | 输出 |
|---|---|---|
| A | 01-02 | 需求概要、功能清单 |
| B | 03-04 | 实体属性清单、原型清单 |
| C | 05-06 | 数据库设计、接口文档 |
| D | 07 | 后端开发设计、方向 README |

拆分原则：

- 一个 story 只覆盖一个模板或相邻模板组合。
- 如果方向过大，先拆方向，再生成 story。
- 不把 08-11 混入默认 batch。
- 不让 story 修改产品代码、migration、生产配置、凭证或其他 PRD。

## 5. Story Package 骨架

```json
{
  "program": "oneops-engineering-docs-standardization",
  "batch": "batch-004-<directionSlug>-standard-docs",
  "title": "<directionName> 01-07 候选标准文档生成",
  "status": "draft",
  "executionMode": "dependency-chain",
  "targetTaskIds": [
    "dev-docs"
  ],
  "direction": {
    "slug": "<directionSlug>",
    "name": "<directionName>",
    "businessScope": "<businessScope>",
    "sourceScopes": {
      "backend": [],
      "frontend": [],
      "existingDocs": [],
      "evidence": []
    },
    "outputDir": "docs/development/<directionSlug>",
    "templateRange": "01-07",
    "humanConfirmationRoles": [
      "产品负责人",
      "后端负责人",
      "前端负责人",
      "测试负责人",
      "安全/权限负责人"
    ]
  },
  "templateRange": "01-07",
  "releaseGate": "本批仅用于按 docs/development-doc-templates/01-07 反向生成 <directionName> 候选标准文档；不生成 08-11；不得确认产品需求、架构决策、API 契约、数据库字段语义、权限或验收标准。",
  "storySizingRule": "每个 story 只覆盖一类模板文档或一个相邻模板组合；不得把测试、接口调用、自动化脚本或代码审查文档纳入本批。",
  "pipeline": [
    "选择 docs/development-doc-templates/01-07 中的具体模板",
    "阅读方向包限定的 route、handler、DTO、model、service、DAO/GORM、前端 wrapper、页面、测试/evidence，提取真实结构体/字段/API/流程/页面",
    "产出代码事实来源清单",
    "按模板结构填充候选文档",
    "人工确认、修改候选文档后再定稿"
  ],
  "excludedTemplates": [
    "08-测试用例模板.md",
    "09-接口调用文档模板.md",
    "10-自动化测试脚本说明模板.md",
    "11-Service代码审查报告模板.md"
  ],
  "stories": []
}
```

## 6. Story 骨架

```json
{
  "id": "DEV-DOCS-<batchNo>A",
  "status": "draft",
  "lanes": [
    "dev-docs"
  ],
  "title": "生成 <directionName> 需求与功能候选文档",
  "priority": 40,
  "risk": "Low",
  "scope": "按 01-需求概要模板和 02-功能清单模板，阅读 <directionName> route、handler、DTO、model、service、前端 wrapper、页面和 evidence，基于真实事实生成候选文档并记录代码事实来源清单。",
  "nonGoals": "不生成测试文档，不确认业务范围、优先级、验收标准或上线范围。",
  "allowedPaths": [
    "docs/development/<directionSlug>/**",
    "docs/openclaw-autodev/evidence/dev-docs/**"
  ],
  "acceptance": [
    "生成 candidate-01-requirements-summary.md。",
    "生成 candidate-02-function-list.md。",
    "两份文档保留模板章节并含 blocked-human-confirmation。",
    "未确认内容保留待确认占位。",
    "文档或 evidence 包含代码事实来源清单。"
  ],
  "validation": [
    "test -f docs/development/<directionSlug>/candidate-01-requirements-summary.md",
    "test -f docs/development/<directionSlug>/candidate-02-function-list.md",
    "rg -n \"【需求概要】|【功能清单】|blocked-human-confirmation|待确认\" docs/development/<directionSlug>/candidate-01-requirements-summary.md docs/development/<directionSlug>/candidate-02-function-list.md",
    "rg -n \"代码事实来源清单|已读取关键文件|源码路径\" docs/development/<directionSlug> docs/openclaw-autodev/evidence/dev-docs",
    "git diff --check -- docs/development/<directionSlug> docs/openclaw-autodev/evidence/dev-docs"
  ]
}
```

## 7. 发布前检查

story package 从 `draft` 进入 `reviewed` 前，至少检查：

- 方向包是否只覆盖一个方向。
- `templateRange` 是否符合用户要求。
- `excludedTemplates` 是否显式列出本轮不需要的模板。
- `allowedPaths` 是否只包含目标输出目录和 evidence 目录。
- 每个 story 是否能在一个 worker turn 内完成。
- 每个 story 是否有文件存在性、关键标题/状态/待确认占位和 `git diff --check` 校验。
- 每个 story 是否要求阅读足够源码，而不是只扫 router/model。
- 每个 story 是否要求输出或链接 `代码事实来源清单`。
- 是否没有把候选文档提升为 `reviewed` 或 `active`。
