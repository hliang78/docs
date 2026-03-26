# AI 交接文档（Template Debug V3 - 下一轮 Stage 开发）

更新时间：2026-03-19（含 target.type 单组调试对齐）  
适用范围：`OneOPS-UI`（`src/views/platform/template-debug-v3`）

## 1. 文档目的

本文件用于指导下一位 AI 在当前基线下继续进行 **Stage 扩展开发**，并避免把新逻辑回灌到超大文件。

核心目标：
1. 新增 Stage 时保持入口统一（registry-first）。
2. 保持 `usePageState.ts` 继续减重，不做反向膨胀。  
3. Stage 行为可验证（apply/payload/preview 全链路可测）。

### 1.1 2026-03-19 增量对齐（必须先读）

1. `Attentions` 不是单 pipeline，而是按 `target.type` 维护多组标准化 pipeline。
2. V3 调试主流程要切换为“单组调试”：每次只加载一个 `target.type` 对应 graph，不再混合展示全量 type。
3. UI 需要新增 `target.type` 下拉，切换时重新调用 load 接口并携带 `target_type`。
4. 当所选 `target_type` 缺失时，必须进入空态提示，不回退成混合 graph。
5. 统一设计与契约文档：`docs/TEMPLATE_DEBUG_V3_TARGET_TYPE_SINGLE_PIPELINE_PLAN_2026-03-19.md`。

### 1.2 2026-03-19 当前落地状态（已完成）

1. OneOps `LoadV3PipelineTemplate` 已支持 `target_type` 入参透传 Controller，并在 attention graph 层做单组过滤。
2. 响应 `summary` 已补齐：`target_types / selected_target_type / target_type_missing / graph_scope`。
3. 当请求了 `target_type` 但当前厂商不命中时，返回空 graph（`pipeline_graph/ui_graph/collect_params` 为空），不回退混合图。
4. UI 已增加 `target.type` 下拉与自动二次加载（首次拿列表后自动按单组重载）。
5. UI 已增加“参考厂商模板图加载 + 回填为当前厂商草稿（仅切上下文，不改画布）”能力。
6. 已新增并通过后端核心单测：
   - `TemplateDebugSessionSrv_LoadV3PipelineTemplate_*`
   - `BuildTemplateDebugV3AttentionGraph_*`
7. 前端关键文件已通过 `eslint` 与 `vue-tsc`（见文末验证命令）。
8. 新增前端行为 smoke：
   - `npm run -s smoke:template-debug-v3-runtime`
   - 覆盖：`target.type` 自动二次加载、`target_type_missing` 空态、参考图回填主上下文。

### 1.3 2026-03-19 架构基线文档（重构前必读）

1. 后端当前真实架构、链路时序与重构边界已落盘：
   - `docs/TEMPLATE_DEBUG_V3_CURRENT_ARCHITECTURE_REFACTOR_BASELINE_2026-03-19.md`
2. 结构化重构方案与“去冗余/去降级/去兜底/去智能”执行基线：
   - `docs/TEMPLATE_DEBUG_V3_STRUCTURED_REFACTOR_PLAN_2026-03-19.md`
3. 下一轮开始代码重构前，先按该文档确认以下约束不变：
   - `target_type` 单组语义不变。
   - strict 连线推断（无兜底/无默认/无智能）不变。
   - 连线与 stage `input/output` 同步语义不变。

### 1.4 2026-03-19 结构化重构执行进展（已开始）

1. 已新增 `LoadV3PipelineTemplate` 结构化编排文件：
   - `OneOps/app/platform/service/impl/template_debug_v3_load_template.go`
2. `LoadV3PipelineTemplate` 已改为主流程 + 步骤函数（校验/上下文解析/RPC 参数/响应解码/graph overlay）。
3. 已清理 attention graph 冗余死代码（未使用函数/未使用类型）。
4. 当前定向测试已通过：
   - `TemplateDebugSessionSrv_LoadV3PipelineTemplate*`
   - `BuildTemplateDebugV3AttentionGraph*`
   - `BuildAttentionUIGraphStrict*`
   - `InferAttentionPipelineEdgesByTemplateFieldsStrict*`
5. 已完成 Phase 2（去降级/去兜底）：
   - `callTemplateDebugV3ControllerRPC` 已禁用自动降级到首个 controller，改为必须按 `function_area` 路由。
   - `LoadV3PipelineTemplate` 已禁用 no-attention 时回退 controller graph，统一返回 attention graph（不匹配则空图）。
6. 已新增并通过测试：
   - `TestTemplateDebugSessionSrv_LoadV3PipelineTemplate_NoAttentionMatchReturnsEmptyGraph`
   - `TestTemplateDebugSessionSrv_LoadV3PipelineTemplate_RequireFunctionArea_NoRPCRouteFallback`
7. Phase 3 首批已落地：
   - collect 解析已移除 target 形态猜测协议（SNMP/SSH）。
   - collect detail 查找已移除 canonical 模糊 alias。
   - collect stage method 生成已移除协议前缀智能补齐。
8. Phase 3 第二批已落地：
   - collect timeout 已移除默认 `30` 与 controller timeout 回填，未显式提供时保持 `0`。
   - `selected_target_type` 已移除“默认首项”兜底，未请求时保持空值。
9. Phase 3 第三批已落地：
   - `LoadV3PipelineTemplate` 已移除 vendor/platform 的 detect/session 隐式补齐，改为请求显式必填。
10. Phase 3 第四批已落地：
   - collect detail 解析已移除 `method` 前缀驱动的 `OID/command` 智能猜测，改为仅读取显式 `oid/command` 字段。
   - `LoadV3PipelineTemplate` 响应解码已移除 `session_id/vendor/platform` 自动补全，改为缺失即失败。
11. Phase 3 第五批已落地：
   - collect detail 解析已移除 `output_field` 默认回退（未显式声明时保持空值）。
12. Phase 3 第六批已落地：
   - collect detail 解析已要求模板显式 `name`，不再回退 `file.Name/file.Path`。
   - collect plan stage method 已移除从 detail 的回退，必须来自 attention stage 显式 method。
13. Phase 3 第七批已落地：
   - collect detail alias 合并已移除 score 智能优先级，改为“仅补空字段，不覆盖既有显式值”的确定性合并。
14. Phase 3 第八批已落地：
   - template file I/O alias 解析已要求模板显式 `name`，不再回退 `file.Name/file.Path`。
15. Phase 3 第九批已落地：
   - template file I/O 解析已移除未知 stage type 的 generic `input/output` 回退映射，仅白名单 stage type 参与 I/O 推断。
   - template file I/O 索引构建已移除空 I/O meta 写入，避免未知 stage 形成 method 命中。
16. Phase 3 第十批已落地：
   - `LoadV3PipelineTemplate` 请求 `target.ip` 已改为显式必填，不再回退会话 target.ip。
   - `LoadV3PipelineTemplate` RPC target hints 已改为仅来自请求显式上下文，不再继承 session 旧 hint。
17. Phase 3 第十一批已落地：
   - template file I/O 索引构建在重复 alias 冲突时已改为“首个显式定义生效”，移除后写覆盖前写的隐式覆盖行为。
18. Phase 3 第十二批已落地：
   - attention stage type 归一化对未知类型已移除回退保留原值，改为忽略未知 stage，仅白名单 stage type 参与 attention 图构建。
19. Phase 3 第十三批已落地：
   - `LoadV3PipelineTemplate` 响应解码已移除非必要 `slice` 默认化，仅保留 `summary map` 的最小初始化以支持 attention overlay 写入。
20. Phase 3 第十四批已落地：
   - collect detail 映射构建已限制为仅接收 controller `stage=collect` 且 `method` 非空条目，移除非 collect/空 method 条目的隐式混入。
21. Phase 3 第十五批已落地：
   - attention `method` 归一化已移除 `filepath/base + 去扩展名` 隐式兼容，仅保留 `trim + lower`。
   - collect detail / template I/O 命中改为依赖 method 显式精确 token，不再对“路径式或带扩展名 method”做同名兜底匹配。
22. Phase 3 第十六批已落地：
   - `LoadV3PipelineTemplate` 响应解码新增一致性校验：`session_id/vendor/platform` 必须与请求上下文一致（缺失或不一致均失败）。
23. Phase 3 第十七批已落地：
   - attention stage type 归一化已移除短别名/旧别名兼容（`alive/snmp/tabletransform`）与 `_` 归一化，仅接受白名单显式 stage type token。
   - `snmp/tabletransform` 不再隐式映射为 `snmpprocess/transform`，未显式命中时按未知 stage 忽略。
24. Phase 3 第十八批已落地：
   - `LoadV3PipelineTemplate` 响应解码在“请求显式提供 version”时新增强一致约束：响应 `version` 必须存在且与请求一致（缺失或不一致均失败）。
25. Phase 3 第十九批已落地：
   - `compareLooseVersion` 已移除“不可解析版本串按字典序比较”的智能兜底；当版本串不含可比较 token 时直接判定不可比较并匹配失败。
26. Phase 3 第二十批已落地：
   - `matchAttentionVersionRange` 已移除“空分段静默跳过”行为；逗号分段为空时视为非法表达式并直接匹配失败。
27. Phase 3 第二十一批已落地：
   - `matchAttentionVersionRange` 已移除“裸版本分段默认按等号比较”的隐式兼容；每个分段必须显式声明比较运算符（`= / > / >= / < / <=`），否则视为非法表达式并匹配失败。
28. Phase 3 第二十二批已落地：
   - `compareLooseVersion` 已移除“缺失版本段自动补 0 比较”的隐式兜底；分段前缀相等时按显式 token 长度决定大小（不再将 `16` 与 `16.0` 视为相等）。
29. Phase 3 第二十三批已落地：
   - `compareLooseVersion` 已移除“数字 token 与字母 token 混比按字典序兜底”行为；当同一位置 token 类型不一致（numeric vs non-numeric）时直接判定不可比较并匹配失败。
30. Phase 3 第二十四批已落地：
   - `compareLooseVersion` 已移除“纯字母 token 按字典序比较”的智能兜底；当同一位置字母 token 不相等时直接判定不可比较（仅在字母骨架一致时继续比较后续 numeric token）。
31. Phase 3 第二十五批已落地：
   - `matchAttentionVersionRange` 已新增“operator 后 target 不能为空”显式校验（如 `>=`/`<=`/`=`），命中即视为非法表达式并匹配失败。
32. Phase 3 第二十六批已落地：
   - `matchAttentionVersionRange` 已新增“无有效分段”显式失败规则：仅真正空字符串表示“无约束”，纯空白表达式视为非法并匹配失败。
33. Phase 3 第二十七批已落地：
   - `matchAttentionVersionRange` 已新增“重复/冲突运算符”显式失败规则：当 operator 解析后 target 仍以 `>`/`<`/`=` 开头（如 `>>16`、`==16`、`<>16`）时视为非法表达式并匹配失败。
34. 已新增并通过测试：
   - `TestBuildTemplateDebugV3AttentionGraph_CollectDetailFromTemplateFiles_NoMethodPrefixInference`
   - `TestBuildTemplateDebugV3AttentionGraph_CollectDetailFromTemplateFiles_NoMethodPathExtensionFallback`
   - `TestBuildTemplateDebugV3AttentionGraph_CollectDetailFromTemplateFiles_NoOutputFieldFallback`
   - `TestBuildTemplateDebugV3AttentionGraph_CollectDetailFromTemplateFiles_RequireExplicitName`
   - `TestBuildAttentionCollectPlanStage_NoDetailMethodFallback`
   - `TestAddAttentionCollectDetailAlias_MergeOnlyEmptyFields`
   - `TestAddAttentionCollectDetailAlias_DoNotOverrideExistingExplicitFields`
   - `TestBuildAttentionTemplateFileIOMetaIndex_RequireExplicitTemplateNameAlias`
   - `TestBuildAttentionTemplateFileIOMetaIndex_NoGenericFallbackForUnknownStageType`
   - `TestBuildAttentionTemplateFileIOMetaIndex_DuplicateAlias_FirstDefinitionWins`
   - `TestBuildTemplateDebugV3AttentionGraph_NoFallbackForUnknownAttentionStageType`
   - `TestBuildAttentionCollectDetailMap_IgnoreNonCollectAndEmptyMethodStages`
   - `TestTemplateDebugSessionSrv_LoadV3PipelineTemplate_RequireTargetIP_NoSessionFallback`
   - `TestTemplateDebugSessionSrv_LoadV3PipelineTemplate_TargetHintsUseExplicitRequestContext`
   - `TestTemplateDebugSessionSrv_LoadV3PipelineTemplate_ResponseRequireVendorAndPlatform_NoDecodeFallback`
   - `TestTemplateDebugSessionSrv_LoadV3PipelineTemplate_ResponseRequireSessionID_NoDecodeFallback`
   - `TestTemplateDebugSessionSrv_LoadV3PipelineTemplate_ResponseRequireSessionIDConsistency_NoDecodeFallback`
   - `TestTemplateDebugSessionSrv_LoadV3PipelineTemplate_ResponseRequireVendorAndPlatformConsistency_NoDecodeFallback`
   - `TestBuildAttentionTemplateFileIOMetaIndex_NoAliasForTableTransformStageType`
   - `TestBuildTemplateDebugV3AttentionGraph_NoAliasForShortAttentionStageType`
   - `TestTemplateDebugSessionSrv_LoadV3PipelineTemplate_ResponseRequireVersionConsistency_WhenRequestVersionProvided`
   - `TestTemplateDebugSessionSrv_LoadV3PipelineTemplate_ResponseRequireVersionPresence_WhenRequestVersionProvided`
   - `TestCompareLooseVersion_NoLexicalFallbackForNonTokenStrings`
   - `TestMatchAttentionVersionRange_NoLexicalFallbackForNonTokenVersion`
   - `TestMatchAttentionVersionRange_InvalidExpressionWithEmptySegments`
   - `TestMatchAttentionVersionRange_RequireExplicitOperator`
   - `TestCompareLooseVersion_NoImplicitZeroPadding`
   - `TestMatchAttentionVersionRange_NoImplicitZeroPaddingForEquality`
   - `TestCompareLooseVersion_NoNumericAlphaMixedFallback`
   - `TestMatchAttentionVersionRange_NoNumericAlphaMixedFallback`
   - `TestCompareLooseVersion_NoLexicalOrderingForAlphaTokens`
   - `TestMatchAttentionVersionRange_NoLexicalOrderingForAlphaTokens`
   - `TestMatchAttentionVersionRange_InvalidExpressionWithEmptyTargetAfterOperator`
   - `TestMatchAttentionVersionRange_InvalidExpressionWithNoEffectiveSegments`
   - `TestMatchAttentionVersionRange_InvalidExpressionWithChainedOrConflictingOperators`
   - `TestParseAttentionVersionRangeConstraint`
   - `TestTemplateDebugSessionSrv_PreviewV3Pipeline_ResponseRequirePipelineID_NoDecodeFallback`
   - `TestTemplateDebugSessionSrv_PreviewV3Pipeline_ResponseRequirePipelineIDConsistency_NoDecodeFallback`
   - `TestTemplateDebugSessionSrv_PreviewV3Pipeline_ResponseRequirePreviewedAt_NoDecodeFallback`
   - `TestTemplateDebugSessionSrv_ValidateV3Pipeline_ResponseRequirePipelineID_NoDecodeFallback`
   - `TestTemplateDebugSessionSrv_ValidateV3Pipeline_ResponseRequireValidatedAt_NoDecodeFallback`
   - `TestTemplateDebugSessionSrv_GetV3LatestPreview_ResponseRequirePipelineID_NoDecodeFallback`
   - `TestTemplateDebugSessionSrv_GetV3LatestPreview_ResponseRequirePipelineIDConsistency_NoDecodeFallback`
   - `TestTemplateDebugSessionSrv_GetV3LatestPreview_ResponseRequirePreviewedAt_NoDecodeFallback`
   - `TestTemplateDebugSessionSrv_CollectV3Session_ResponseRequireStatus_NoDecodeFallback`
   - `TestTemplateDebugSessionSrv_CollectV3Session_ResponseRequireTrace_NoDecodeFallback`
   - `TestTemplateDebugSessionSrv_CollectV3Session_ResponseRequireSummary_NoDecodeFallback`
   - `TestTemplateDebugSessionSrv_CollectV3Session_ResponseRequireCollectedAt_NoDecodeFallback`
   - `TestTemplateDebugSessionSrv_CollectV3Session_ResponseRequireStructuredFields_NoDecodeFallback`
   - `TestTemplateDebugSessionSrv_CollectV3Session_ResponseRejectInvalidCollectedAt_NoDecodeFallback`
   - `TestReadV3MapString_MissingAndNilReturnEmptyString`
   - `TestTemplateDebugSessionSrv_CollectV3Session_ResponseRejectUnknownStatus_NoDecodeFallback`
   - `TestTemplateDebugSessionSrv_CollectV3Session_ResponseRequireManufacturer_NoDetectResultFallback`
   - `TestTemplateDebugSessionSrv_CollectV3Session_ResponseRequireCatalog_NoUnknownFallback`
   - `TestTemplateDebugSessionSrv_CollectV3Session_TargetHintsDoNotUseDetectResultFallback`
   - `TestTemplateDebugSessionSrv_CollectV3Session_ResponseRequireRawFragments_NoStructuredFallback`
   - `TestTemplateDebugSessionSrv_CollectV3Session_ResponseRejectRawFragmentMissingName_NoSilentSkip`
   - `TestTemplateDebugSessionSrv_CollectV3Session_ResponseRejectEmptyRawFragments_NoDecodeFallback`
   - `TestTemplateDebugSessionSrv_CollectV3Session_ResponseRejectRawFragmentsInvalidType_NoDecodeFallback`
   - `TestTemplateDebugSessionSrv_CollectV3Session_ResponseRejectRawFragmentItemInvalidType_NoDecodeFallback`
   - `TestTemplateDebugSessionSrv_CollectV3Session_ResponseRejectStructuredFieldsInvalidType_NoDecodeFallback`
   - `TestTemplateDebugSessionSrv_CollectV3Session_ResponseRejectTraceInvalidType_NoDecodeFallback`
   - `TestTemplateDebugSessionSrv_CollectV3Session_ResponseRejectSummaryInvalidType_NoDecodeFallback`
   - `TestTemplateDebugSessionSrv_CollectV3Session_ResponseRejectStatusInvalidType_NoDecodeFallback`
   - `TestTemplateDebugSessionSrv_CollectV3Session_ResponseRejectCollectedAtInvalidType_NoDecodeFallback`
   - `TestTemplateDebugSessionSrv_CollectV3Session_ResponseRejectDataEmptyObject_NoDecodeFallback`
   - `TestTemplateDebugSessionSrv_CollectV3Session_ResponseRejectStructuredFieldsEmptyObject_NoDecodeFallback`
   - `TestTemplateDebugSessionSrv_CollectV3Session_ResponseRejectTraceEmptyObject_NoDecodeFallback`
   - `TestTemplateDebugSessionSrv_CollectV3Session_ResponseRejectSummaryEmptyObject_NoDecodeFallback`
   - `TestTemplateDebugSessionSrv_CollectV3Session_ResponseRejectRawFragmentMissingContent_NoDecodeFallback`
   - `TestTemplateDebugSessionSrv_CollectV3Session_ResponseRejectRawFragmentContentInvalidType_NoDecodeFallback`
   - `TestTemplateDebugSessionSrv_CollectV3Session_ResponseRejectRawFragmentMissingTruncated_NoDecodeFallback`
   - `TestTemplateDebugSessionSrv_CollectV3Session_ResponseRejectRawFragmentTruncatedInvalidType_NoDecodeFallback`
   - `TestTemplateDebugSessionSrv_PreviewV3Pipeline_ResponseRejectPipelineIDInvalidType_NoDecodeFallback`
   - `TestTemplateDebugSessionSrv_PreviewV3Pipeline_ResponseRejectPreviewedAtInvalidType_NoDecodeFallback`
   - `TestTemplateDebugSessionSrv_ValidateV3Pipeline_ResponseRejectPipelineIDInvalidType_NoDecodeFallback`
   - `TestTemplateDebugSessionSrv_ValidateV3Pipeline_ResponseRejectValidatedAtInvalidType_NoDecodeFallback`
   - `TestTemplateDebugSessionSrv_GetV3LatestPreview_ResponseRejectPipelineIDInvalidType_NoDecodeFallback`
   - `TestTemplateDebugSessionSrv_GetV3LatestPreview_ResponseRejectPreviewedAtInvalidType_NoDecodeFallback`
   - `TestTemplateDebugSessionSrv_LoadV3PipelineTemplate_ResponseRejectDataInvalidType_NoDecodeFallback`
   - `TestTemplateDebugSessionSrv_LoadV3PipelineTemplate_ResponseRejectSessionIDInvalidType_NoDecodeFallback`
   - `TestTemplateDebugSessionSrv_PreviewV3Pipeline_ResponseRejectDataEmptyObject_NoDecodeFallback`
   - `TestTemplateDebugSessionSrv_ValidateV3Pipeline_ResponseRejectDataEmptyObject_NoDecodeFallback`
   - `TestTemplateDebugSessionSrv_LoadV3PipelineTemplate_ResponseRejectDataEmptyObject_NoDecodeFallback`
   - `TestTemplateDebugSessionSrv_PreviewV3Pipeline_ResponseRequireSnapshotID_WhenRequestSnapshotProvided_NoDecodeFallback`
   - `TestTemplateDebugSessionSrv_PreviewV3Pipeline_ResponseRejectSnapshotIDInvalidType_WhenRequestSnapshotProvided_NoDecodeFallback`
   - `TestTemplateDebugSessionSrv_PreviewV3Pipeline_ResponseRequireSnapshotIDConsistency_WhenRequestSnapshotProvided_NoDecodeFallback`
   - `TestTemplateDebugSessionSrv_ValidateV3Pipeline_ResponseRequireSnapshotID_WhenRequestSnapshotProvided_NoDecodeFallback`
   - `TestTemplateDebugSessionSrv_ValidateV3Pipeline_ResponseRejectSnapshotIDInvalidType_WhenRequestSnapshotProvided_NoDecodeFallback`
   - `TestTemplateDebugSessionSrv_ValidateV3Pipeline_ResponseRequireSnapshotIDConsistency_WhenRequestSnapshotProvided_NoDecodeFallback`
35. Phase 3 第二十八批已落地：
   - `matchAttentionVersionRange` 已将单分段约束解析抽离为 `parseAttentionVersionRangeConstraint`，统一“显式 operator + 非空 target + 禁止重复/冲突 operator”校验，行为语义保持不变。
36. Phase 3 第二十九批已落地：
   - `PreviewV3Pipeline` 响应解码已移除 `pipeline_id/snapshot_id/previewed_at` 回填兜底，改为显式必填与一致性校验（`snapshot_id` 仅在请求显式提供时强校验）。
   - `ValidateV3Pipeline` 响应解码已移除 `pipeline_id/snapshot_id/validated_at` 回填兜底，改为显式必填与一致性校验（`snapshot_id` 仅在请求显式提供时强校验）。
37. Phase 3 第三十批已落地：
   - `GetV3LatestPreview` 响应解码已移除 `pipeline_id/previewed_at` 回填兜底，改为显式必填与一致性校验（缺失或与请求 `pipeline_id` 不一致均失败）。
38. Phase 3 第三十一批已落地：
   - `CollectV3Session` 响应解码已移除 `status` 默认 `collected` 回填，改为缺失即失败。
   - `CollectV3Session` 响应解码已移除 `trace/summary` 本地构造回填，改为缺失即失败（且在事务前校验，避免无效响应落库）。
39. Phase 3 第三十二批已落地：
   - `CollectV3Session` 响应解码已移除 `collected_at` 缺失兜底（不再回退 `time.Now()`），改为缺失即失败。
   - `CollectV3Session` 响应解码已移除 `structured_fields` 为空 map 兜底，改为缺失即失败。
40. Phase 3 第三十三批已落地：
   - `CollectV3Session` 响应解码已收紧 `collected_at` 时间格式：无效时间串不再回退 `time.Now()`，改为显式失败。
41. Phase 3 第三十四批已落地：
   - `readV3MapString` 已移除“缺失 key / nil 值字符串化为 `<nil>`”副作用，改为显式返回空串；非字符串标量保持字符串化行为。
42. Phase 3 第三十五批已落地：
   - `normalizeV3CollectSnapshotStatus` 已收紧为白名单归一化（`completed/partial_failed/failed`），未知状态不再透传。
   - `CollectV3Session` 对响应 `status` 已新增显式合法性校验，未知值改为失败（避免异常状态落库）。
43. Phase 3 第三十六批已落地：
   - `buildV3FinalResultFromStructured` 已移除旧探测结果回填，改为仅接受本次 `structured_fields` 显式值。
   - `buildV3FinalResultFromStructured` 已移除 `Catalog=UNKNOWN` 默认化，`manufacturer/platform/version/catalog` 缺失任一即失败。
44. Phase 3 第三十七批已落地：
   - `CollectV3Session` 已移除从 `detect_result` 对 `target.vendor/platform/version_hint` 的隐式回填，RPC target hints 仅接受请求显式输入（或会话 target 原值）。
45. Phase 3 第三十八批已落地：
   - `CollectV3Session` 已移除 `raw_fragments` 从 `structured_fields` 反推构造的兜底路径；响应缺失 `raw_fragments` 时改为显式失败。
46. Phase 3 第三十九批已落地：
   - `CollectV3Session` 已收紧 `raw_fragments` 条目级校验：`name` 为空不再静默跳过，改为显式失败（包含条目索引定位）。
47. Phase 3 第四十批已落地：
   - `CollectV3Session` 已新增 `raw_fragments` 空数组显式失败规则（不再接受空列表）。
48. Phase 3 第四十一批已落地：
   - `CollectV3Session` 已新增 `raw_fragments` 类型显式校验：当字段存在但值非数组/切片时直接失败（`collect 响应 raw_fragments 类型非法`），不再被吞并为“空数组”错误。
49. Phase 3 第四十二批已落地：
   - `CollectV3Session` 已新增 `raw_fragments` 条目类型显式校验：当 `raw_fragments[i]` 非对象/结构体时直接失败（`collect 响应 raw_fragments[i] 类型非法`），不再降级为 `name` 缺失错误。
50. Phase 3 第四十三批已落地：
   - `CollectV3Session` 已将 `structured_fields/trace/summary` 收敛为主线严格 map 解码：字段缺失与字段类型非法分离报错（`缺少 ...` vs `... 类型非法`），不再把类型错误吞并为缺失错误。
51. Phase 3 第四十四批已落地：
   - `CollectV3Session` 已将 `status/collected_at` 收敛为主线严格 string 解码：字段缺失与字段类型非法分离报错（`缺少 ...` vs `... 类型非法`），空串保持“缺少字段”语义，非字符串不再吞并为缺失错误。
52. Phase 3 第四十五批已落地：
   - `CollectV3Session` 已将 `data/structured_fields/trace/summary` 的空对象语义收敛为显式结构错误（`... 不能为空`），不再吞并为“缺少字段”错误。
53. Phase 3 第四十六批已落地：
   - `CollectV3Session` 已收紧 `raw_fragments` 条目字段解码：`content/truncated` 不再做宽松类型转换，改为“字段缺失或类型非法即失败”。
54. Phase 3 第四十七批已落地：
   - `CollectV3Session` 已完成错误文案分层一致性收敛：`raw_fragments[i].content/truncated` 缺失提示统一由“缺失”改为“缺少”，与主链路其余字段保持一致。
55. Phase 3 第四十八批已落地：
   - `LoadV3PipelineTemplate / PreviewV3Pipeline / ValidateV3Pipeline / GetV3LatestPreview` 已统一引入“缺少 vs 类型非法”错误分层解码，非字符串关键字段不再吞并为“缺少”错误。
56. Phase 3 第四十九批已落地：
   - `LoadV3PipelineTemplate / PreviewV3Pipeline / ValidateV3Pipeline` 已将 `data` 空对象语义收敛为显式结构错误（`data 不能为空`），与 `CollectV3Session` 保持一致，不再吞并为“缺少 data”错误。
57. Phase 3 第五十批已落地：
   - `PreviewV3Pipeline / ValidateV3Pipeline` 已补齐“请求显式提供 `snapshot_id`”场景的严格分层校验回归：缺少/类型非法/与请求不一致三类错误均已显式断言并统一文案粒度。
58. 下一步继续 Phase 3 收尾（Phase 51 推荐）：
   - 审计 `GetV3LatestPreview` 是否需要将 `snapshot_id` 纳入同等严格解码（缺少/类型非法），并评估与现有对外语义兼容性后决定是否纳入强约束。
59. 例外约束（已确认）：
   - `trace_id` 必须保留自动生成（用于链路追踪），不可在“去兜底”中移除。

---

## 2. 当前代码基线（截至 2026-03-18）

仓库：`/home/jacky/project/OneOPS-ALL/OneOPS-UI`  
工作区：**dirty（存在未提交改动）**

当前体量：
- `src/views/platform/template-debug-v3/usePageState.ts`: **803 行**
- `src/views/platform/TemplateDebugPipelineEditorV3.vue`: **656 行**

说明：`usePageState.ts` 已从 1200+ 持续拆到 803，后续请继续沿用 facade/composable 分层，不要把 Stage 新逻辑直接堆回该文件。

---

## 3. 已完成的结构化重构（可直接复用）

### 3.1 Stage 入口统一
- `stageRegistry.ts`（已接入）
  - `STAGE_TYPE_*`
  - `stageTypeOptions`
  - `getStageDefaultConfig`
  - `normalizeStageType`
  - `isDataRefStage/isSnmpProcessStage/isTransformStage`
  - `isExecutableStage`、`runtimeKind`

### 3.2 组件拆分（页面层）
- `TemplateDebugNodeInspector.vue`
- `TransformMappingDebugModal.vue`
- `SnmpProcessPreviewModal.vue`
- `NodeDataPreviewModal.vue`

### 3.3 composable/facade 拆分（状态层）
- `usePageSnapshotState.ts`
- `usePageSnapshotCodec.ts`
- `usePreviewGraphBuilder.ts`
- `useInspectorPanelState.ts`
- `useInspectorResizeState.ts`
- `usePreviewRuntimeState.ts`
- `useSnmpProcessPreviewState.ts`
- `useGraphAutoSyncActions.ts`
- `useDataRefFieldSync.ts`
- `useRuntimeDebugActionsFacade.ts`
- `useRuntimePreviewFacade.ts`
- `useSnmpInspectorFacade.ts`
- `useTransformEditorFacade.ts`

当前 `usePageState.ts` 主要职责是组装以上模块并对外暴露状态/动作。

---

## 4. 下一轮 Stage 开发总原则（必须遵守）

1. **先入口，后功能，最后 UI**
- 顺序固定：`stageRegistry -> useNodeEditorActions -> stageGraph/useStageIOTypeTracker -> previewPayload -> UI inspector`。

2. **不做 silent fallback**
- 解析/校验/运行错误必须可见（toast + 结构化错误）。

3. **不破坏 transform/tableTransform 既有行为**
- 这是已有高复杂区域，新增 Stage 不得引入兼容性回退。

4. **保持搬运式重构思路**
- 新逻辑进新 composable/facade，不回灌 `usePageState.ts`。

5. **先接口契约，后 UI 行为**
- 先确保 `target_type` 请求/响应契约打通，再做 inspector 或新 Stage 细节，避免前端状态与后端 graph 语义错位。

---

## 5. 下一轮 Stage 开发执行清单（AI 可直接照做）

## 阶段 A：定义 Stage 元信息（registry-first）

1. 在 `stageRegistry.ts` 新增 descriptor：
- `type`
- `label`
- `inspectorKind`
- `runtimeKind`
- `executable`
- `createDefaultConfig`

2. 同步默认配置来源：
- `stageNodeDefaults.ts`（若仍有分支）
- 依赖 `stageTypeOptions` 的 UI 选择器无需额外写死。

验收：新增 Stage 能在“添加 Stage”下拉里出现，且新增节点时配置结构正确。

## 阶段 A0：先完成 target.type 单组调试接线（本轮优先）

1. 扩展调试页 load 请求参数，确保支持传递 `target_type`。
2. 接入并维护以下响应字段：
- `summary.target_types`
- `summary.selected_target_type`
- `summary.target_type_missing`
3. 在页面顶部提供 `target.type` 选择器：
- 默认选择 `selected_target_type`（或列表首项）。
- 切换后立即重载 pipeline graph。
4. 缺失处理：
- `target_type_missing=true` 时显示明确空态，不渲染旧图，不回退成全量图。

验收：同 vendor/platform 下切换 `target.type` 时，节点与连线可切换且互不混杂。

## 阶段 B：编辑器 apply 与字段推断

1. `useNodeEditorActions.ts`
- 为新 Stage 增加 apply 分支（结构化配置请走专门分支）。

2. `stageGraph.ts`
- 增加 output field 推断规则。

3. `useStageIOTypeTracker.ts`
- 增加类型传播提示（必要时）。

验收：编辑后点“应用”可稳定写回节点，in/out 推断正确。

## 阶段 C：Preview payload 与执行语义

1. `previewPayload.ts`
- 明确新 Stage 是否 executable。
- 若伪节点，统一走集中过滤逻辑（禁止调用侧散落判断）。

2. 运行链路自检
- `buildPreviewPayloadGraph` 输出图结构正确；断链裁剪提示不受破坏。

验收：Preview 请求体正确，后端返回节点结果与前端映射一致。

## 阶段 D：UI Inspector 接入

1. 简单 Stage：在现有 `TemplateDebugNodeInspector.vue` 接入。  
2. 复杂 Stage：新建独立 composable + 子组件，不新增 `usePageState` 业务逻辑。

验收：Inspector 可编辑、保存、回显，且不影响现有 snmp/transform 区块。

---

## 6. 推荐触点矩阵（新增 Stage 时按此检查）

- 注册与默认配置：`stageRegistry.ts`
- target.type 接口/类型：`src/api/platform/template-debug-v3.ts`、`src/typings/platform/template-debug-v3.ts`
- target.type 选择与重载：`TemplateDebugPipelineEditorV3.vue`、`usePageState.ts`（仅接线）
- 节点创建默认值：`useCanvasInteraction.ts` / `stageNodeDefaults.ts`
- 应用节点改动：`useNodeEditorActions.ts`
- 字段推断：`stageGraph.ts`
- 类型传播：`useStageIOTypeTracker.ts`
- payload 语义：`previewPayload.ts`
- inspector UI：`TemplateDebugNodeInspector.vue`（或新增子组件）
- 页面组装：`usePageState.ts`（仅接线，不堆业务）

---

## 7. 验证命令（下一轮必须执行）

在 `OneOPS-UI` 目录：

1. `npx eslint src/views/platform/template-debug-v3/*.ts src/views/platform/template-debug-v3/*.vue src/views/platform/TemplateDebugPipelineEditorV3.vue`
2. `NODE_OPTIONS=--max-old-space-size=8192 npx vue-tsc --noEmit --skipLibCheck`
3. `npm run -s smoke:template-debug-v3-runtime`

说明：历史 warning（`snmpProcessForm.ts` non-null assertion）可暂保留；新增改动不允许引入新的 eslint error / tsc error。

---

## 8. 下一轮建议优先级（按收益）

1. 基于当前已落地的 `target.type` 单组闭环，补 UI 单测（至少覆盖自动二次加载/缺失空态/参考回填上下文切换）。  
2. 再完成一个最小新 Stage 的全链路（A+B+C），暂不做视觉优化。  
3. 最后做 Inspector 细节（D）并补充 smoke 场景（新增节点 -> apply -> preview payload -> preview result）。

---

## 9. 给下一位 AI 的启动指令模板

可直接用以下方式开工：

1. “先读取本文件与 `AI_HANDOFF_TEMPLATE_DEBUG_V3_STAGE_SPLIT_2026-03-18.md`，基于 registry-first 方式新增 `<STAGE_NAME>`，先完成 apply + payload + 字段推断，不做 UI 花活。”
2. “先按 `docs/TEMPLATE_DEBUG_V3_TARGET_TYPE_SINGLE_PIPELINE_PLAN_2026-03-19.md` 完成 `target.type` 单组调试接线（A0），再继续 `<STAGE_NAME>` 开发。”
3. “完成后运行 eslint + vue-tsc，并输出修改触点矩阵与剩余风险。”
