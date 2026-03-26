# Template Debug V3 结构化重构方案（2026-03-19）

适用范围：`OneOps`（后端主链路）

## 1. 目标对齐

本轮重构将当前实现视为原型收敛，遵循以下约束：

1. 不做过度设计，不引入主体功能外的新能力。
2. 只做内聚化与结构化编程改造。
3. 消除冗余、降级、兜底、智能推断。
4. 保持现有核心能力：`前端 -> oneops -> controller -> templates`，并维持 strict field dependency 连线规则。

## 2. 结构化编程约束

## 2.1 单主流程

`LoadV3PipelineTemplate` 固定为线性流程：

1. `validate request/session state`
2. `resolve explicit target context`
3. `build rpc params`
4. `call controller rpc`
5. `decode + normalize rpc payload`
6. `build attention graph (strict)`
7. `compose final response`

禁止在流程中插入隐式回退路径（fallback branch）。

## 2.2 单一职责函数

每个函数只做一件事，建议命名：

1. `validateLoadTemplateRequest`
2. `resolveLoadTemplateContext`
3. `buildLoadTemplateRPCParams`
4. `decodeLoadTemplateRPCResponse`
5. `overlayLoadTemplateAttentionGraph`

## 2.3 显式失败

缺少必要输入或命中失败时，返回结构化错误，禁止静默补全。

## 3. 去除项清单（必须执行）

## 3.1 去冗余

1. 删除未使用函数与重复解析分支。
2. 合并重复的 map 默认化逻辑，避免散落赋值。

## 3.2 去降级

1. 去掉 RPC `按 area 失败后自动降级调用首个 controller` 的路径。
2. 去掉 `attention 不命中时自动回退 controller graph` 的路径。

## 3.3 去兜底

1. 不再自动补默认 `target_type`、`graph_scope`、`timeout`。
2. 不再在核心流程中自动补 vendor/platform/version（除非来源显式可追溯且在上下文约定内）。
3. `trace_id` 自动生成保留（用于链路追踪，不属于业务语义兜底）。

## 3.4 去智能

1. 去除 collect 模板中基于字符串形态猜测 `OID/command` 类型的逻辑。
2. 去除宽松 alias/canonical 模糊匹配，改为显式精确匹配。
3. 保留 strict edge inference：仅字段交集产生连线。

## 4. 分阶段实施

## Phase 1（本轮）

1. 完成文档化 + 入口重构（`LoadV3PipelineTemplate` 流程结构化）。
2. 抽离主流程私有函数，消除重复代码。
3. 保持对外接口不变。

## Phase 2

1. 删除 RPC 降级路径。
2. 删除 graph fallback 路径。
3. 补齐对应失败场景单测。

## Phase 3

1. 清理 collect 推断中的智能分支。
2. 清理 alias 模糊匹配。
3. 收敛 attention graph 为显式映射。

## 5. 验收标准

1. 代码结构：主流程函数长度与圈复杂度明显下降。
2. 行为语义：strict edge + 节点 input/output 同步保持不变。
3. 失败显式：不再出现静默降级/静默回退。
4. 测试：
   - 现有核心测试通过。
   - 新增“无降级/无兜底/无智能”测试通过。

## 6. 风险与注意项

1. 当前仓库处于 dirty 状态，重构仅修改 V3 相关文件。
2. 优先保证 `LoadV3PipelineTemplate` 语义可回归验证。
3. 每一阶段都先补测试再扩大改动面，避免一次性大改。

## 7. 执行进展（2026-03-19）

1. Phase 1 已完成：`LoadV3PipelineTemplate` 已按结构化步骤拆分到独立文件。
2. Phase 2 已完成：
   - RPC 路由已禁用自动降级到首个 controller，要求按 `function_area` 显式路由。
   - graph 结果已禁用 no-attention fallback 到 controller graph。
3. Phase 3 首批已完成：
   - collect 解析移除基于 target 形态的协议猜测（SNMP/SSH）。
   - collect detail 查找移除 canonical 模糊匹配，仅保留 normalize 后精确匹配。
   - collect stage method 生成移除协议前缀智能补齐，改为显式 method 传递。
4. Phase 3 第二批已完成：
   - collect timeout 移除默认 `30` 与 controller 回填兜底，未显式提供时保持 `0`。
   - `selected_target_type` 移除“默认选首项”兜底，未请求时保持空值。
5. Phase 3 第三批已完成：
   - `LoadV3PipelineTemplate` 中 vendor/platform 不再从 detect/session 隐式补齐，改为请求显式必填。
6. Phase 3 第四批已完成：
   - attention collect detail 解析不再基于 `method` 前缀猜测 `OID/command`，仅接受模板显式 `oid/command` 字段。
   - `LoadV3PipelineTemplate` 响应解码不再兜底补全 `session_id/vendor/platform`，改为缺失即失败。
7. Phase 3 第五批已完成：
   - attention collect detail 解析不再对 `output_field` 做默认回退（未显式声明时保持空值）。
8. Phase 3 第六批已完成：
   - collect detail 解析要求模板显式 `name`，不再回退 `file.Name/file.Path`。
   - collect plan stage method 不再从 detail 回退，必须来自 attention stage 显式 method。
9. Phase 3 第七批已完成：
   - collect detail alias 合并移除 score 智能优先级，改为“仅补空字段、不覆盖既有显式值”的确定性合并。
10. Phase 3 第八批已完成：
   - template file I/O alias 解析要求模板显式 `name`，不再回退 `file.Name/file.Path`。
11. Phase 3 第九批已完成：
   - template file I/O 解析移除未知 stage type 的 generic `input/output` 回退映射，仅白名单 stage type 参与 I/O 推断。
   - template file I/O 索引构建不再写入空 I/O meta，避免未知 stage 形成 method 命中。
12. Phase 3 第十批已完成：
   - `LoadV3PipelineTemplate` 请求 `target.ip` 改为显式必填，不再回退会话 target.ip。
   - `LoadV3PipelineTemplate` RPC `target.vendor/platform/version_hint` 改为仅来自请求显式上下文（`target.*_hint` 或顶层 `vendor/platform/version`），不再继承 session 旧 hint。
13. Phase 3 第十一批已完成：
   - template file I/O 索引构建在重复 alias 冲突时改为“首个显式定义生效”，移除后写覆盖前写的隐式覆盖行为。
14. Phase 3 第十二批已完成：
   - attention stage type 归一化对未知类型不再回退保留原值，改为忽略未知 stage，仅白名单 stage type 参与 attention 图构建。
15. Phase 3 第十三批已完成：
   - `LoadV3PipelineTemplate` 响应解码移除非必要 `slice` 默认化，仅在 overlay attention graph 前保留 `summary map` 最小初始化，避免空指针写入。
16. Phase 3 第十四批已完成：
   - collect detail 映射构建仅接收 controller `stage=collect` 且 `method` 非空的条目，移除非 collect/空 method 条目的隐式混入。
17. Phase 3 第十五批已完成：
   - attention `method` 归一化移除 `filepath/base + 去扩展名` 隐式兼容，仅保留 `trim + lower`。
   - collect detail 与 template I/O 命中改为依赖 method 显式精确 token，不再对“路径式/带扩展名 method”做隐式同名兜底匹配。
18. Phase 3 第十六批已完成：
   - `LoadV3PipelineTemplate` 响应解码新增一致性校验：`session_id/vendor/platform` 必须与请求上下文一致（缺失或不一致均失败）。
19. Phase 3 第十七批已完成：
   - attention stage type 归一化移除短别名/旧别名兼容（`alive/snmp/tabletransform`）与 `_` 归一化，仅接受白名单显式 stage type token。
   - `snmp/tabletransform` 不再隐式映射为 `snmpprocess/transform`，未显式命中时按未知 stage 忽略。
20. Phase 3 第十八批已完成：
   - `LoadV3PipelineTemplate` 响应解码在“请求显式提供 version”时新增强一致约束：响应 `version` 必须存在且与请求一致（缺失或不一致均失败）。
21. Phase 3 第十九批已完成：
   - `compareLooseVersion` 移除“不可解析版本串按字典序比较”的智能兜底；当版本串不含可比较 token 时直接判定不可比较并匹配失败。
22. Phase 3 第二十批已完成：
   - `matchAttentionVersionRange` 移除“空分段静默跳过”行为；逗号分段为空时视为非法表达式并直接匹配失败。
23. Phase 3 第二十一批已完成：
   - `matchAttentionVersionRange` 移除“裸版本分段默认按等号比较”的隐式兼容；每个分段必须显式声明比较运算符（`= / > / >= / < / <=`），否则视为非法表达式并匹配失败。
24. Phase 3 第二十二批已完成：
   - `compareLooseVersion` 移除“缺失版本段自动补 0 比较”的隐式兜底；分段前缀相等时按显式 token 长度决定大小（不再将 `16` 与 `16.0` 视为相等）。
25. Phase 3 第二十三批已完成：
   - `compareLooseVersion` 移除“数字 token 与字母 token 混比按字典序兜底”行为；当同一位置 token 类型不一致（numeric vs non-numeric）时直接判定不可比较并匹配失败。
26. Phase 3 第二十四批已完成：
   - `compareLooseVersion` 移除“纯字母 token 按字典序比较”的智能兜底；当同一位置字母 token 不相等时直接判定不可比较（仅在字母骨架一致时继续比较后续 numeric token）。
27. Phase 3 第二十五批已完成：
   - `matchAttentionVersionRange` 新增“operator 后 target 不能为空”显式校验（如 `>=`/`<=`/`=`），命中即视为非法表达式并匹配失败。
28. Phase 3 第二十六批已完成：
   - `matchAttentionVersionRange` 新增“无有效分段”显式失败规则：仅真正空字符串表示“无约束”，纯空白表达式视为非法并匹配失败。
29. Phase 3 第二十七批已完成：
   - `matchAttentionVersionRange` 新增“重复/冲突运算符”显式失败规则：当 operator 解析后 target 仍以 `>`/`<`/`=` 开头（如 `>>16`、`==16`、`<>16`）时视为非法表达式并匹配失败。
30. Phase 3 第二十八批已完成：
   - `matchAttentionVersionRange` 已将单分段约束解析抽离为 `parseAttentionVersionRangeConstraint`，统一“显式 operator + 非空 target + 禁止重复/冲突 operator”校验，行为语义保持不变。
31. Phase 3 第二十九批已完成：
   - `PreviewV3Pipeline` 响应解码移除 `pipeline_id/snapshot_id/previewed_at` 回填兜底，改为显式必填与一致性校验（`snapshot_id` 仅在请求显式提供时强校验）。
   - `ValidateV3Pipeline` 响应解码移除 `pipeline_id/snapshot_id/validated_at` 回填兜底，改为显式必填与一致性校验（`snapshot_id` 仅在请求显式提供时强校验）。
32. Phase 3 第三十批已完成：
   - `GetV3LatestPreview` 响应解码移除 `pipeline_id/previewed_at` 回填兜底，改为显式必填与一致性校验（缺失或与请求 `pipeline_id` 不一致均失败）。
33. Phase 3 第三十一批已完成：
   - `CollectV3Session` 响应解码移除 `status` 本地默认 `collected` 回填，改为缺失即失败。
   - `CollectV3Session` 响应解码移除 `trace/summary` 本地构造回填，改为缺失即失败（且在事务前校验，避免无效响应落库）。
34. Phase 3 第三十二批已完成：
   - `CollectV3Session` 响应解码移除 `collected_at` 时间缺失兜底（不再回退 `time.Now()`），改为缺失即失败。
   - `CollectV3Session` 响应解码移除 `structured_fields` 为空 map 兜底（不再回退空结构），改为缺失即失败。
35. Phase 3 第三十三批已完成：
   - `CollectV3Session` 响应解码收紧 `collected_at` 时间格式：无效时间串不再回退 `time.Now()`，改为显式失败。
36. Phase 3 第三十四批已完成：
   - `readV3MapString` 已移除“缺失 key / nil 值字符串化为 `<nil>`”副作用，改为显式返回空串；非字符串标量仍保持字符串化行为。
37. Phase 3 第三十五批已完成：
   - `normalizeV3CollectSnapshotStatus` 已收紧为白名单归一化（`completed/partial_failed/failed`），未知状态不再透传。
   - `CollectV3Session` 对响应 `status` 新增显式合法性校验，未知值改为失败（避免异常状态落库）。
38. Phase 3 第三十六批已完成：
   - `buildV3FinalResultFromStructured` 已移除旧探测结果回填，改为仅接受本次 `structured_fields` 显式值。
   - `buildV3FinalResultFromStructured` 已移除 `Catalog=UNKNOWN` 默认化，`manufacturer/platform/version/catalog` 缺失任一即失败。
39. Phase 3 第三十七批已完成：
   - `CollectV3Session` 已移除从 `detect_result` 对 `target.vendor/platform/version_hint` 的隐式回填，RPC target hints 仅接受请求显式输入（或会话 target 原值）。
40. Phase 3 第三十八批已完成：
   - `CollectV3Session` 已移除 `raw_fragments` 从 `structured_fields` 反推构造的兜底路径；响应缺失 `raw_fragments` 时改为显式失败。
41. Phase 3 第三十九批已完成：
   - `CollectV3Session` 已收紧 `raw_fragments` 条目级校验：`name` 为空不再静默跳过，改为显式失败（包含条目索引定位）。
42. Phase 3 第四十批已完成：
   - `CollectV3Session` 已新增 `raw_fragments` 空数组显式失败规则（不再接受空列表）。
43. Phase 3 第四十一批已完成：
   - `CollectV3Session` 已新增 `raw_fragments` 类型显式校验：当字段存在但值非数组/切片时直接失败（`collect 响应 raw_fragments 类型非法`），不再被吞并为“空数组”错误。
44. Phase 3 第四十二批已完成：
   - `CollectV3Session` 已新增 `raw_fragments` 条目类型显式校验：当 `raw_fragments[i]` 非对象/结构体时直接失败（`collect 响应 raw_fragments[i] 类型非法`），不再降级为 `name` 缺失错误。
45. Phase 3 第四十三批已完成：
   - `CollectV3Session` 已将 `structured_fields/trace/summary` 收敛为主线严格 map 解码：字段缺失与字段类型非法分离报错（`缺少 ...` vs `... 类型非法`），不再把类型错误吞并为缺失错误。
46. Phase 3 第四十四批已完成：
   - `CollectV3Session` 已将 `status/collected_at` 收敛为主线严格 string 解码：字段缺失与字段类型非法分离报错（`缺少 ...` vs `... 类型非法`），空串保持“缺少字段”语义，非字符串不再吞并为缺失错误。
47. Phase 3 第四十五批已完成：
   - `CollectV3Session` 已将 `data/structured_fields/trace/summary` 的空对象语义收敛为显式结构错误（`... 不能为空`），不再吞并为“缺少字段”错误。
48. Phase 3 第四十六批已完成：
   - `CollectV3Session` 已收紧 `raw_fragments` 条目字段解码：`content/truncated` 不再做宽松类型转换，改为“字段缺失或类型非法即失败”。
49. Phase 3 第四十七批已完成：
   - `CollectV3Session` 已完成错误文案分层一致性收敛：`raw_fragments[i].content/truncated` 缺失提示统一由“缺失”改为“缺少”，与主链路其余字段保持一致。
50. Phase 3 第四十八批已完成：
   - `LoadV3PipelineTemplate / PreviewV3Pipeline / ValidateV3Pipeline / GetV3LatestPreview` 已统一引入“缺少 vs 类型非法”错误分层解码，非字符串关键字段不再吞并为“缺少”错误。
51. Phase 3 第四十九批已完成：
   - `LoadV3PipelineTemplate / PreviewV3Pipeline / ValidateV3Pipeline` 已将 `data` 空对象语义收敛为显式结构错误（`data 不能为空`），与 `CollectV3Session` 保持一致，不再吞并为“缺少 data”错误。
52. Phase 3 第五十批已完成：
   - `PreviewV3Pipeline / ValidateV3Pipeline` 已补齐“请求显式提供 `snapshot_id`”场景的严格分层校验回归：缺少/类型非法/与请求不一致三类错误均已显式断言并统一文案粒度。
53. 当前相关定向测试已通过（含上述“无智能/无兜底”新增场景、`TestParseAttentionVersionRangeConstraint`、Load/Preview/Validate/LatestPreview/Collect 响应严格校验、`readV3MapString` 缺失/nil 场景、collect target hint 去回填与 raw_fragments 去兜底/条目校验/空数组校验/字段类型校验/条目类型校验、`structured_fields/trace/summary` 类型非法校验、`status/collected_at` 类型非法校验、`data/structured_fields/trace/summary` 空对象校验、`raw_fragments.content/truncated` 类型与缺失校验、Load/Preview/Validate/LatestPreview 关键字段类型非法校验、Load/Preview/Validate `data` 空对象校验、Preview/Validate `snapshot_id` 缺少/类型非法/一致性校验新增测试）。

---

最后更新：2026-03-19
