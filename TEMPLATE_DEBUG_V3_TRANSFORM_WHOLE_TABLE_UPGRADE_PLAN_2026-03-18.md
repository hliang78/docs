# Template Debug V3 / Transform V3 整表输入升级方案

更新时间：2026-03-18  
适用范围：`netlink`、`OneOps`、`OneOPS-UI`

## 1. 背景与目标

当前 Transform V3 的 `mapping.inputField` 主要按 `source#subField` 使用。虽然现有实现已支持“单源 + 单 mapping + 整表 `[]map` 输入”的基础路径，但仍缺少产品级语义与多源合并规范，导致可用性与可维护性不足。

本方案目标：

1. 支持整表输入下的三种列变换模式（用户可视化配置，不依赖手写复杂表达式）。
2. 定义整表输入与其他数据源混合时的合并语义。
3. 保持向后兼容：已有 `inputField=source#col` 与 `expr:` 行为不变。

---

## 2. 目标能力定义（产品语义）

以输入 `snmpProcessOutput: []map[string]string` 为例，支持：

1. 列投影输出（column_project）
- 对 `source_column` 应用表达式。
- 输出仅该列（可选输出为 `[]string` 或单列 `[]map`，建议统一为单列 `[]map` 以减少类型分叉）。

2. 列原位替换（column_inplace）
- 对 `source_column` 应用表达式。
- 输出仍是整表，`source_column` 的值被替换。

3. 列追加输出（column_append）
- 对 `source_column` 应用表达式。
- 输出仍是整表，并新增 `target_column`。

---

## 3. 当前实现差距分析

## 3.1 netlink 当前能力

- `TransformStageV3` 现有主路径：`string` / `map` / `[]map`。
- `[]map` 路径对 `source#subField` 支持稳定；不带 `#` 的整表输入仅在单 mapping 路径可用。
- 多源 mixed 路径尚无“整表 + 其他源”明确语义。

已存在可复用基础：
- `msTransformField`：支持原位与目标字段写入。  
  参考：`netlink/pipeline/expr_functions_mapslice.go`
- `msCopyAndTransform`：天然匹配“列追加”模式。  
- `msPluck`：可用于“列投影”模式基础实现。

## 3.2 OneOPS-UI 当前能力

- UI 支持 mapping 调试，且已支持 `[]map` 根字段整表输入。
- 仍以 `inputField/outputField/regex(expr)` 为主，缺少显式“整表模式”配置 UI。

## 3.3 OneOps 当前能力

- 可透传 transform 配置到 controller/netlink。
- 无针对整表模式的结构化校验与错误提示规则。

---

## 4. 推荐设计（兼容优先）

## 4.1 配置扩展（建议）

在 `FieldMapping` 增加可选扩展对象（兼容旧字段）：

```yaml
mappings:
  - inputField: snmpProcessOutput
    outputField: snmp_process_item
    regex: "" # 旧字段保留
    tableTransform:
      mode: column_inplace        # column_project | column_inplace | column_append
      sourceColumn: mac
      targetColumn: mac_norm      # 仅 append 需要
      expr: strToUpper(value)     # 仅表达式体，不含 expr: 前缀
      projectAs: table            # project 模式可选: table | values
```

说明：
- `tableTransform` 存在时，优先走整表模式执行器。
- `tableTransform` 不存在时，保持旧逻辑（完全兼容）。

## 4.2 执行语义

前置约束：
- `inputField` 必须指向 `[]map[string]string` 根字段（不含 `#`）。
- `expr` 以行级变量执行：`value` 表示当前列值，`row` 表示当前行 map（可选扩展）。

三种模式：

1. `column_project`
- 对每行 `sourceColumn` 执行表达式。
- `projectAs=table`：输出 `[]map[{sourceColumn|targetColumn: transformed}]`。
- `projectAs=values`：输出 `[]string`（可选，若要简化，V1 可先不开放）。

2. `column_inplace`
- 对每行 `sourceColumn` 执行表达式并覆盖原值。
- 输出整表。

3. `column_append`
- 对每行 `sourceColumn` 执行表达式写入 `targetColumn`。
- 输出整表。

## 4.3 多源合并策略（重点）

新增 item 级可选配置 `tableMergePolicy`（V1 可先限制场景，V1.1 再全面开放）：

```yaml
tableMergePolicy:
  strategy: row_align          # row_align | row_align_max | aggregate | key_join
  key: interface_id            # key_join 需要
  side: left                   # key_join: left | inner | full
  conflict: right_override     # left_keep | right_override | error
```

建议分期：
- V1：整表模式仅允许单源单 mapping（规避歧义，快速可交付）。
- V1.1：开放与其他 mapping 混合，支持 `row_align/aggregate`。
- V1.2：开放 `key_join`。

---

## 5. 分阶段实施计划

## 阶段 A（最小可用，1~2 天）

目标：稳定交付 3 种整表模式（单源单 mapping）。

netlink：
- 扩展 `FieldMapping` 结构（新增 `TableTransform` 可选字段）。
- 在 `processSliceValue` 增加 `tableTransform` 执行分支。
- 增加参数校验（缺 `sourceColumn` / `targetColumn` / 非 []map 时报结构化错误）。
- 新增单测：三种模式 + 错误场景。

OneOPS-UI：
- mapping 编辑区增加“整表模式开关 + mode/source/target/expr 配置”。
- 调试弹窗支持整表模式编辑与执行。
- “应用到当前 Mapping”回写 `tableTransform`。

OneOps：
- DTO / decode 结构支持新字段透传。
- `validate` 增加 tableTransform 结构校验与错误码。

## 阶段 B（混合源，2~3 天）

目标：整表结果与其他源稳定合并。

- item 级新增 `tableMergePolicy`。
- 实现 `row_align` / `row_align_max` / `aggregate`。
- 明确空值填充与冲突策略。
- 增加回归测试矩阵。

## 阶段 C（键合并，2~3 天）

目标：支持 key 语义合并（适合跨表 enrichment）。

- 实现 `key_join`（left/inner/full）。
- 明确 key 缺失、重复 key 行为。
- 增加性能与边界测试。

---

## 6. 测试与验收标准

## 6.1 单测（netlink）

必测：
- `column_project` / `column_inplace` / `column_append`。
- `expr` 正常/异常。
- `sourceColumn` 不存在、输入非 `[]map`。
- 向后兼容：旧 `source#col` 与旧 `expr:` 用例全部通过。

## 6.2 集成（OneOps + UI）

- 调试弹窗编辑 -> 执行 -> 回写 mapping -> 再次 preview 一致。
- 快照保存/恢复后，整表模式配置不丢失。
- 错误提示可定位到具体 mapping 字段。

## 6.3 性能

- 10k 行 `[]map` 下，单次调试执行时间与内存可控（给基线）。

---

## 7. 风险与规避

1. 风险：表达式自由度过高，行为不可预测。  
规避：V1 限制整表模式仅单 mapping；逐步开放。

2. 风险：多源语义不清导致线上不可解释结果。  
规避：先定义 `tableMergePolicy`，默认值严格且可见。

3. 风险：配置膨胀影响老模板。  
规避：新字段全部可选；无新字段时走旧路径。

---

## 8. 版本兼容与发布建议

- Feature Flag：`transform_v3_table_transform_enabled`。
- 灰度顺序：netlink -> OneOps -> UI。
- 回滚策略：关闭开关后全部回落旧逻辑。

---

## 9. 下一步执行建议（给新会话）

1. 先落地阶段 A（单源单 mapping 三模式）。
2. 先补 netlink 单测再改执行器，保证语义可锁定。
3. UI 先做“向导化配置 + 回写”，再做高级合并策略入口。

