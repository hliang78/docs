# Device V2 入库工程文档初稿

| 项目 | 内容 |
| --- | --- |
| 文档状态 | `blocked-human-confirmation` |
| 人工确认人 | `[待人工确认: 项目负责人]` |
| 人工确认日期 | `[待人工确认: 项目负责人]` |
| 适用范围 | Device V2 入库工作台、Excel/import batch、upload/validate/apply、handoff、field reconciliation 的文档整理 |

> 本文仅用于汇总 Device V2 入库方向的已记录证据、缺口和人工确认项。当前状态为 `blocked-human-confirmation`，**不可直接**作为开发、测试、上线、story 发布或验收依据。

## 1. 文档边界

本文只整理来源材料，不确认以下内容：

- 不确认产品需求、页面交互、业务规则、错误文案或验收标准。
- 不确认 API path、DTO、数据库字段、fixture、权限模型、性能目标或采集协议。
- 不把 D2 launch evidence 中的阶段性结果提升为长期工程规范。
- 不推导删除、清理、批次保留或源记录安全策略；相关内容均保留为人工确认项。

## 2. 来源材料索引

| 来源 | 可提炼内容 | 使用限制 |
| --- | --- | --- |
| `docs/prd-autodev/oneops-engineering-docs-standardization/idea.md` | AI/autodev 只能整理、提炼、占位、标风险 | 不可反推需求、设计、业务规则、架构、API、数据模型或验收标准 |
| `docs/development/prompt-assets-analysis.md` | prompt assets 到正式工程文档的治理链路 | prompt 内容不能直接变成开发依据 |
| `docs/prd-autodev/d2-launch-acceptance/evidence-index.md` | 入库 upload/validate/apply、batch、handoff、field reconciliation 的 launch evidence 摘要 | 只记录 evidence 状态，不自动确认 launch PASS |
| `docs/prd-autodev/d2-launch-acceptance/launch-readiness-report.md` | 入库工作台页级 BLOCKED 结论与人工决策点 | 不可替代正式产品或验收确认 |
| `docs/openclaw-autodev/shared-d2.md` | D2 FE/BE 协作记录、backend import 修复、样本导出、测试门禁等路径 | 只作为 evidence 路径索引，不复制凭证、不执行生产动作 |

## 3. 入库流程草图（不可直接执行）

以下流程只是从 evidence 和协作记录中整理出的候选叙述，当前**不可直接**用于开发、联调、测试或验收。每一步的输入、输出、字段、权限、错误状态和重试策略都需要人工确认。

| 阶段 | 候选说明 | 当前状态 |
| --- | --- | --- |
| 来源样本准备 | `[候选方案: AI 提炼]` 从已有 Device V2 记录中选择候选设备，并以脱敏方式记录来源、身份线索和 credential reference 存在性。 | `[待人工确认: 产品负责人]` 样本范围、选择规则和权威 enrichment 来源未确认。 |
| Excel/import 文件生成 | `[候选方案: AI 提炼]` 将可安全入库的候选行生成 Excel/import artifact；缺少 platform/catalog/rack 等权威信息的行保持 skipped/blocker，而不是默认补值。 | `[待人工确认: 技术负责人]` 模板字段、必填项、字段类型和跳过规则未确认。 |
| import batch 创建与上传 | `[候选方案: AI 提炼]` evidence 中存在 batch、upload 和 artifact lifecycle 记录。 | `[待人工确认: 技术负责人]` batch 生命周期、命名、幂等、权限和审计规则未确认。 |
| validate | `[候选方案: AI 提炼]` evidence 中记录过 validate 阶段和显式失败/跳过结果。 | `[待人工确认: 测试负责人]` 校验失败分类、错误文案、阻断/警告边界未确认。 |
| apply | `[候选方案: AI 提炼]` approved 2-row fresh batch 曾 validate/apply 成功，并保留 batch/record 证据。 | `[待人工确认: 技术负责人]` apply 的新增/更新语义、失败回滚、重试与源记录安全未确认。 |
| handoff 到设备管理 | `[候选方案: AI 提炼]` approved clones 曾通过管理页/清册路径完成 handoff 检查。 | `[待人工确认: 产品负责人]` handoff 成功定义、用户可见状态和后续操作入口未确认。 |
| field reconciliation | `[候选方案: AI 提炼]` approved 2-row path 曾核对 endpoint/protocol/port 与 credential-ref preservation；3 个候选仍 blocked。 | `[待人工确认: 测试负责人]` 字段核对清单、差异接受规则和验收口径未确认。 |

## 4. 已记录的入库证据事实

以下内容仅表示“已有 evidence 记录过”，不得直接扩展为正式规则：

- `[候选方案: AI 提炼]` DB-derived sample/export 曾记录 5 个真实 Device V2 候选，credential reference 仅以 set/unset 或 hash/marker 形式出现。
- `[候选方案: AI 提炼]` Excel/import evidence 曾记录 5 source rows、2 import rows、3 skipped rows，并保留 `labels.d2la_orig_code` 等 traceability 线索。
- `[候选方案: AI 提炼]` approved 2-row fresh batch 有 upload、validate、apply、batch retention、handoff、field reconciliation 相关 evidence。
- `[候选方案: AI 提炼]` backend evidence 曾修复/记录 row-level executor failure 不应伪装为成功、batch record/list namespace filtering、credential-ref preservation 等入库相关问题。
- `[候选方案: AI 提炼]` launch readiness 对 Device V2 入库工作台的页级结论仍是 `BLOCKED`，原因包括完整 5-device scope 不完整、3 个候选缺少权威 enrichment、final cleanup/delete report 不完整。

## 5. 风险与缺口

| 风险/缺口 | 当前记录 | 处理要求 |
| --- | --- | --- |
| 完整 5-device scope 未完成 | 2/5 approved clones 有入库和后续证据；3/5 仍缺少权威 enrichment/import readiness。 | `[待人工确认: 产品负责人]` 补齐、替换或显式接受 reduced-scope 风险。 |
| skipped/failed rows 语义未确认 | evidence 中存在 skipped rows 和失败状态记录。 | `[待人工确认: 产品负责人]` 不得把 evidence 中的处理方式直接定为正式产品规则。 |
| credential-ref preservation 边界敏感 | fresh approved 2-row path 记录过 ref preservation；不得暴露 credential plaintext。 | `[待人工确认: 安全/技术负责人]` 正式契约、脱敏表达和安全边界。 |
| batch retention / cleanup 未确认 | evidence 要求保留 import batch/task/row；clone cleanup/delete report 未完成。 | `[待人工确认: 技术负责人]` 保留周期、清理触发、禁止删除边界和审计要求。 |
| handoff 成功定义未确认 | evidence 记录过管理清册可见性与字段核对。 | `[待人工确认: 测试负责人]` 正式 handoff 验收口径需另行确认。 |

## 6. 不得从 evidence 反推的内容

- 不得把 2 个 approved imported `D2LA_*` clones 的证据反推为完整 5 设备上线通过。
- 不得把 skipped rows 的处理反推为正式跳过策略、错误状态模型或业务规则。
- 不得把 batch retention 的 evidence 反推为正式保留周期、清理策略或审计政策。
- 不得把字段核对 evidence 反推为 API/DTO/数据库字段契约。
- 不得把 backend test gate 反推为完整测试覆盖或验收通过。

## 7. 待人工确认清单

### 7.1 产品负责人

- `[待人工确认: 产品负责人]` Device V2 入库工作台的正式业务范围、上线范围和用户角色范围。
- `[待人工确认: 产品负责人]` 5-device 样本是否必须补齐，或是否接受 reduced 2/5 evidence 作为显式风险。
- `[待人工确认: 产品负责人]` 3 个 blocked candidates 的处理方式：补充权威 platform/catalog/rack enrichment、替换设备，或记录 accepted risk。
- `[待人工确认: 产品负责人]` skipped rows、失败 rows、错误提示和人工修正路径的正式产品口径。

### 7.2 技术负责人

- `[待人工确认: 技术负责人]` upload、validate、apply、batch、handoff 的正式工程边界和责任分层。
- `[待人工确认: 技术负责人]` 哪些 launch evidence 可转入工程约束，哪些只能保留为阶段性证据。
- `[待人工确认: 技术负责人]` import batch/task/row records 的保留、清理、安全和审计规则。
- `[待人工确认: 技术负责人]` credential reference preservation 的正式契约表达；本文不确认字段名、存储结构或协议细节。

### 7.3 测试负责人

- `[待人工确认: 测试负责人]` upload/validate/apply/handoff/field reconciliation 的正式测试用例和验收口径。
- `[待人工确认: 测试负责人]` full 5-device scope、reduced 2/5 scope、blocked candidates 的测试状态表达。
- `[待人工确认: 测试负责人]` cleanup report 缺失时入库方向能否进入后续阶段，以及需要补哪些 evidence。

## 8. 后续文档化建议

- `[待人工确认: 项目负责人]` 是否允许继续拆分 `ingest-source-materials.md`、`ingest-human-gates.md`、`ingest-evidence-map.md`。
- `[待补充]` 若允许拆分，所有子文档仍必须默认 `blocked-human-confirmation`。
- `[待补充]` 若后续人工确认部分内容，应逐项记录确认人、日期、范围和仍未确认的保留项。
