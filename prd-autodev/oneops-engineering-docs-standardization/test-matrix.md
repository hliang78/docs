# OneOPS 工程文档标准化 Test Matrix

## 测试目标

验证工程文档标准化体系与 `dev-docs` loop 是否满足独立 PRD、人工确认门禁、不可直接执行、evidence 回写，以及从当前真实代码反推标准文档的要求。

## Matrix

| ID | 检查项 | 证据 | 状态 |
|---|---|---|---|
| DOC-GATE-001 | 存在独立 PRD 目录 | `docs/prd-autodev/oneops-engineering-docs-standardization` | PASS |
| DOC-GATE-002 | POC PRD 不承担工程文档治理 | `dev-docs.conf` 不引用 `oneops-poc-concern-autotest` | PASS |
| DOC-GATE-003 | 文档状态包含 `blocked-human-confirmation` | `docs/development/documentation-standard.md` | PASS |
| DOC-GATE-004 | 模板默认不可直接使用 | `docs/development/templates.md` | PASS |
| DOC-GATE-005 | API/测试文档有使用门禁 | `api-documentation-standard.md`, `testing-standard.md` | PASS |
| DOC-GATE-006 | 自动化只写允许范围 | `dev-docs.conf` `ALLOWED_WRITES` | PASS |
| DOC-GATE-007 | 自动化 evidence 已产出 | `docs/openclaw-autodev/evidence/dev-docs/DEV-DOCS-001-human-confirmation-gates.md` | PASS |
| DOC-GATE-008 | 工程文档产物中文优先 | `documentation-standard.md`, `templates.md`, `dev-docs.conf` | PASS |
| DOC-GATE-009 | 反向文档必须从 `docs/development-doc-templates/01-07` 选择标准结构 | `prd.md`, `program-plan.md`, `dev-docs.conf` | PASS |
| DOC-GATE-010 | 自动化规则要求区分 `标准文档结构`、`当前真实代码事实`、`候选文档内容`、`AI 推导建议`、`规划缺口` | `SKILL.md`, `backend-flow.md`, `dev-docs.conf` | PASS |
| DOC-GATE-011 | Device V2 候选文档必须按标准结构填充真实建模、真实逻辑、真实 API | `story-packages/batch-003-device-v2-code-fact-standard-docs.json` | PASS |
| DOC-GATE-012 | 后续文档生成应按标准结构、源码事实、需求/功能候选文档、实体/原型候选文档、数据库/API候选文档、后端设计候选文档拆小 story | `program-plan.md`, `story-packages/batch-003-device-v2-code-fact-standard-docs.json` | PASS |
| DOC-GATE-013 | 新方向必须先形成方向包，再生成 `dev-docs` story package | `prd.md`, `program-plan.md`, `story-generation-guide.md` | PASS |
| DOC-GATE-014 | story package 默认只覆盖 `01-07`，且显式排除 `08-11` | `story-generation-guide.md`, `batch-003-device-v2-code-fact-standard-docs.json` | PASS |
| DOC-GATE-015 | 每个方向默认拆为 A-D 四个小 story，使用 `dependency-chain` | `program-plan.md`, `story-generation-guide.md` | PASS |
| DOC-GATE-016 | story validation 必须检查文件存在、模板标题/状态/待确认占位和 diff check | `story-generation-guide.md` | PASS |
| DOC-GATE-017 | 代码事实提取阶段必须阅读 route、handler、DTO、model、service、DAO/GORM、前端 wrapper、页面、测试/evidence 等足够源码 | `prd.md`, `program-plan.md`, `story-generation-guide.md`, `dev-docs.conf` | PASS |
| DOC-GATE-018 | 候选文档或 evidence 必须包含 `代码事实来源清单` | `prd.md`, `program-plan.md`, `story-generation-guide.md` | PASS |
| DOC-GATE-019 | 历史粗粒度 batch 不应作为后续发布入口 | `story-packages/batch-002-device-v2-engineering-docs.json`, `program-plan.md` | PASS |

## Remaining Manual Checks

- `[待人工确认: 项目负责人]` 是否接受本 PRD 作为工程文档标准化的长期归属。
- `[待人工确认: 项目负责人]` 是否允许后续将 `dev-docs` 纳入常驻 task pool。
- `[待人工确认: 产品/架构/测试负责人]` 是否接受 Device V2 真实代码事实盘点作为反推标准文档的第一批输入。
- `[待人工确认: 产品/架构/测试负责人]` 是否允许下一轮按模型、API、业务流程、测试证据拆分生成标准文档草稿。
- `[待人工确认: 项目负责人]` 是否接受方向包作为后续更多方向进入 `dev-docs` 的固定输入。
- `[待人工确认: 项目负责人]` 是否接受 `代码事实来源清单` 作为候选文档进入人工定稿的前置条件。
