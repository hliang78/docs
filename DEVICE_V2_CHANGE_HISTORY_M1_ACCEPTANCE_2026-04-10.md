# Device V2 Change History M1 验收清单

日期：2026-04-10

## 标准闭环节点

`Device V2 Change History M1 可上线`

满足以下 6 条，视为标准闭环：

1. 所有核心写路径都写入 `change-history`
2. 前端完整支持处理闭环
3. 关键业务维度可筛选
4. 关系和来源链路具备业务可读性
5. 数据库和接口可稳定上线
6. 自动化回归与端到端走查通过

## 当前结果

### 1. 核心写路径

- [x] 手工新增设备
- [x] 手工编辑设备
- [x] 手工删除设备
- [x] 批量导入 apply
- [x] 批量导入 retry
- [x] V1 全量同步
- [x] V1 按编码同步
- [x] Store Pipeline 启动
- [x] Store Pipeline 重试
- [x] Controller Collect 写回
- [x] 关系新增
- [x] 关系删除

说明：
- `EntityV2Srv` 分支下的 `store/start` 与 `store/retry` 也已补齐审计上下文，避免不同部署模式下出现来源链路缺失。

### 2. 前端处理闭环

- [x] 查看变更列表
- [x] 查看字段差异
- [x] 修改状态
- [x] 填写处理备注
- [x] 关系变更后即时刷新历史

### 3. 筛选能力

- [x] 时间范围
- [x] 变更类型
- [x] 业务域
- [x] 变更来源
- [x] 风险等级
- [x] 状态
- [x] 仅关键字段

### 4. 业务可读性

- [x] 变更来源标签
- [x] 风险标签
- [x] 状态标签
- [x] 业务动作标签
- [x] 关系类型业务化文案

### 5. 上线前置

- [ ] 执行 migration：`OneOps/migrations/add_device_v2_change_history_status_columns.sql`
- [x] 前后端统一切到新 change-history 结构

### 6. 回归结果

已通过：

- `go test ./app/device/v2/api -run 'TestDeviceV2API_(ListChangeHistory|ListChangeHistory_WithFilters|ListChangeHistory_WithTimeRange|UpdateChangeHistoryStatus)'`
- `go test ./app/platform/api -run 'TestEntityRelationAPI_RecordRelationChangeHistory'`
- `go test ./app/device/v2/service/impl -run 'TestDeviceV2ChangeHistory'`
- `yarn --cwd OneOPS-UI vue-tsc --noEmit --skipLibCheck`

## 端到端走查步骤

### 场景 A：手工编辑闭环

1. 打开 Device V2 详情页
2. 编辑设备名称、管理地址或凭证字段并保存
3. 进入“变更记录”页签
4. 确认出现新的 change-history 记录
5. 打开详情面板，填写处理备注
6. 点击“标记已知晓”或“标记已闭环”
7. 确认状态与备注更新成功

### 场景 B：关系变更闭环

1. 在 Device V2 详情页新增一条关系
2. 确认“关系”列表即时刷新
3. 切到“变更记录”或保持当前页等待刷新
4. 确认出现关系新增事件
5. 删除该关系
6. 确认出现关系删除事件，且风险高于新增

### 场景 C：导入/同步来源闭环

1. 执行批量导入 apply 或 retry
2. 执行 V1 同步或 Store Pipeline
3. 在设备详情“变更记录”中筛选对应来源
4. 确认可看到来源、风险、状态、差异字段

## 结论

除 migration 执行外，`Device V2 Change History M1` 已达到代码层面的标准闭环。
