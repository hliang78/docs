# Device V2 Change History 前端实测报告

日期：2026-04-10

关联文档：

- [DEVICE_V2_CHANGE_HISTORY_FRONTEND_TEST_PLAN_2026-04-10.md](./DEVICE_V2_CHANGE_HISTORY_FRONTEND_TEST_PLAN_2026-04-10.md)
- [DEVICE_V2_CHANGE_HISTORY_M1_ACCEPTANCE_2026-04-10.md](./DEVICE_V2_CHANGE_HISTORY_M1_ACCEPTANCE_2026-04-10.md)

---

## 一、执行范围与环境

执行方式：

- 全程基于真实前端页面操作与浏览器自动化验证
- 页面地址：`http://127.0.0.1:3001`
- 后端地址：`http://127.0.0.1:8080`
- 测试账号：`admin / admin@123`

主要测试对象：

- `DEV20260401000032`
  - 作为主验证设备
  - 已覆盖编辑、状态流转、备注、关系新增/删除、关系筛选、关系状态矩阵、边界回归
- `DEV20260401000033`
  - 作为关系目标设备
  - 同时用于跨设备切换验证

执行方式说明：

- 对常规交互直接走真实 UI
- 对 Ant Select 等自动化稳定性较差的筛选交互，使用页面自身的响应式状态与 `loadDetailHistory()` 驱动，仍属于同一真实前端页面的功能验证，不绕过前端逻辑

---

## 二、总体结论

结论：

- `Device V2 Change History` 前端主流程已形成可用闭环
- 设备编辑、历史展示、差异抽屉、状态流转、备注持久化、关系新增/删除、关系记录筛选、关系状态矩阵均已通过真实页面验证
- 在测试推进过程中已修复多处前端阻断与体验一致性问题，当前页面可用性明显提升

当前仍需关注：

- `Device V2 Schema` 正式保存仍会被后端预检查门禁阻断，这属于环境/样本数据问题，不是当前前端页面逻辑错误
- 状态更新接口失败时仍存在重复错误提示问题，此项仍为待跟进的 P2 UX 问题

---

## 三、本轮已落地修复

### 1. 设备详情拉取修复

文件：

- `OneOPS-UI/src/api/device/device-v2.ts`

结果：

- 修复详情页数据获取返回值问题
- 解决编辑弹窗字段为空、保存后联动异常、路由深链打开详情不稳定

### 2. 处理备注输入框渲染修复

文件：

- `OneOPS-UI/src/views/device/DeviceV2Management.vue`

结果：

- 将历史处理备注控件修正为可正常渲染
- 使状态流转与备注持久化可以在真实页面完成

### 3. 关系列表接口解包修复

文件：

- `OneOPS-UI/src/api/platform/entity-relation.ts`

结果：

- 修复 `by-source/by-target` 结果被多取一层 `.data` 的问题
- 解决“后端已有关系但前端关系列表始终为空”

### 4. Schema 保存失败提示修复

文件：

- `OneOPS-UI/src/views/device/DeviceV2SchemaDesign.vue`

结果：

- 页面不再错误提示“后端未返回有效 schema”
- 现在会保留并展示真实失败原因，例如 `Schema 预检查未通过，禁止保存`

### 5. 关系类型手工输入兜底

文件：

- `OneOPS-UI/src/views/device/DeviceV2Management.vue`

结果：

- 当 schema 未配置 `relation_types` 时，关系页签仍可手工输入 `connected_to`
- 解除纯前端页面关系新增测试阻塞

### 6. “仅看未确认”筛选修复

文件：

- `OneOPS-UI/src/views/device/DeviceV2Management.vue`

结果：

- 已知晓/已忽略/已闭环的关系事件不再错误出现在“仅看未确认”中

### 7. 统计卡与说明文案口径统一

文件：

- `OneOPS-UI/src/views/device/DeviceV2Management.vue`

结果：

- 顶部统计卡与当前可见列表保持一致
- 标题、风险分布、筛选说明不再在本地过滤后引用全量结果
- 空结果场景下会明确提示“当前筛选下暂无匹配的台账变更”

### 8. 历史抽屉状态清理修复

文件：

- `OneOPS-UI/src/views/device/DeviceV2Management.vue`

结果：

- 离开“变更记录”页签时，差异抽屉、当前事件与未提交备注会立即清空
- 切换到其他设备后，旧设备历史上下文不再残留

---

## 四、详细测试结果

以下场景均按照测试计划要求记录。

### 场景 1：冒烟与空态

1. 场景名称

变更记录页签冒烟与空态

2. 前置条件

- 已登录前端
- 可打开设备详情页

3. 操作步骤

- 打开设备详情
- 切换到“变更记录”
- 观察有数据设备与无数据状态的展示

4. 实际结果

- 有数据设备可正常展示列表
- 空态场景正确显示 `暂无变更记录`

5. 预期结果

- 无白屏
- 有数据展示列表
- 无数据展示空态

6. 是否通过

- 通过

7. 截图建议

- [./assets/device-v2-frontend-test-2026-04-10/91-empty-history.png](./assets/device-v2-frontend-test-2026-04-10/91-empty-history.png)

8. 问题列表

- 无

### 场景 2：手工编辑生成变更记录

1. 场景名称

设备手工编辑闭环

2. 前置条件

- 主设备 `DEV20260401000032`

3. 操作步骤

- 修改设备名称
- 保存
- 进入“变更记录”
- 打开差异抽屉

4. 实际结果

- 页面成功新增变更记录
- 差异抽屉可看到设备名称前后变化

5. 预期结果

- 手工编辑应即时生成 change-history

6. 是否通过

- 通过

7. 截图建议

- [./assets/device-v2-frontend-test-2026-04-10/30-before-history.png](./assets/device-v2-frontend-test-2026-04-10/30-before-history.png)
- [./assets/device-v2-frontend-test-2026-04-10/31-edit-before-save.png](./assets/device-v2-frontend-test-2026-04-10/31-edit-before-save.png)
- [./assets/device-v2-frontend-test-2026-04-10/32-after-history.png](./assets/device-v2-frontend-test-2026-04-10/32-after-history.png)
- [./assets/device-v2-frontend-test-2026-04-10/33-diff-open.png](./assets/device-v2-frontend-test-2026-04-10/33-diff-open.png)

8. 问题列表

- 已在推进过程中修复详情拉取异常

### 场景 3：状态流转与备注持久化

1. 场景名称

历史处理闭环

2. 前置条件

- 历史详情抽屉可打开

3. 操作步骤

- 打开历史记录差异抽屉
- 输入备注
- 依次执行 `已知晓 / 需处理 / 忽略 / 已闭环`
- 刷新页面后再次确认

4. 实际结果

- 各状态切换成功
- 备注持久化成功
- 刷新后列表与抽屉状态一致

5. 预期结果

- 状态更新成功
- 备注保留

6. 是否通过

- 通过

7. 截图建议

- [./assets/device-v2-frontend-test-2026-04-10/50-status-drawer-open.png](./assets/device-v2-frontend-test-2026-04-10/50-status-drawer-open.png)
- [./assets/device-v2-frontend-test-2026-04-10/51-status-after-flow.png](./assets/device-v2-frontend-test-2026-04-10/51-status-after-flow.png)
- [./assets/device-v2-frontend-test-2026-04-10/52-status-refresh.png](./assets/device-v2-frontend-test-2026-04-10/52-status-refresh.png)
- [./assets/device-v2-frontend-test-2026-04-10/150-relation-delete-status-before.png](./assets/device-v2-frontend-test-2026-04-10/150-relation-delete-status-before.png)
- [./assets/device-v2-frontend-test-2026-04-10/151-relation-delete-status-after.png](./assets/device-v2-frontend-test-2026-04-10/151-relation-delete-status-after.png)
- [./assets/device-v2-frontend-test-2026-04-10/152-relation-delete-status-after-refresh.png](./assets/device-v2-frontend-test-2026-04-10/152-relation-delete-status-after-refresh.png)

8. 问题列表

- 存在一项待跟进 UX 问题：模拟接口失败时会出现重复错误提示

问题等级

- P2

复现概率

- 高概率

影响范围

- 变更状态更新失败反馈

初步怀疑点

- 请求拦截器与调用方同时弹错

### 场景 4：筛选器详细验证

1. 场景名称

变更记录筛选器验证

2. 前置条件

- 主设备已存在多条台账与关系记录

3. 操作步骤

- 依次验证来源、风险、状态、业务域、时间范围、仅关键字段、仅看未确认及组合筛选

4. 实际结果

- 单项与组合筛选均正常收敛
- 关系类记录可稳定按业务域、风险、状态筛出
- 重置筛选后可恢复全量结果

5. 预期结果

- 各筛选项单独和组合均生效

6. 是否通过

- 通过

7. 截图建议

- [./assets/device-v2-frontend-test-2026-04-10/72-filter-base-state.png](./assets/device-v2-frontend-test-2026-04-10/72-filter-base-state.png)
- [./assets/device-v2-frontend-test-2026-04-10/73-filter-confirmedOnly.png](./assets/device-v2-frontend-test-2026-04-10/73-filter-confirmedOnly.png)
- [./assets/device-v2-frontend-test-2026-04-10/74-filter-status-resolved.png](./assets/device-v2-frontend-test-2026-04-10/74-filter-status-resolved.png)
- [./assets/device-v2-frontend-test-2026-04-10/75-filter-risk-high.png](./assets/device-v2-frontend-test-2026-04-10/75-filter-risk-high.png)
- [./assets/device-v2-frontend-test-2026-04-10/76-filter-domain-management.png](./assets/device-v2-frontend-test-2026-04-10/76-filter-domain-management.png)
- [./assets/device-v2-frontend-test-2026-04-10/77-filter-source-manual.png](./assets/device-v2-frontend-test-2026-04-10/77-filter-source-manual.png)
- [./assets/device-v2-frontend-test-2026-04-10/78-filter-time7d.png](./assets/device-v2-frontend-test-2026-04-10/78-filter-time7d.png)
- [./assets/device-v2-frontend-test-2026-04-10/79-filter-keyfield.png](./assets/device-v2-frontend-test-2026-04-10/79-filter-keyfield.png)
- [./assets/device-v2-frontend-test-2026-04-10/80-filter-combo-source-status.png](./assets/device-v2-frontend-test-2026-04-10/80-filter-combo-source-status.png)
- [./assets/device-v2-frontend-test-2026-04-10/81-filter-combo-risk-domain.png](./assets/device-v2-frontend-test-2026-04-10/81-filter-combo-risk-domain.png)
- [./assets/device-v2-frontend-test-2026-04-10/82-filter-reset-state.png](./assets/device-v2-frontend-test-2026-04-10/82-filter-reset-state.png)
- [./assets/device-v2-frontend-test-2026-04-10/140-history-filter-base.png](./assets/device-v2-frontend-test-2026-04-10/140-history-filter-base.png)
- [./assets/device-v2-frontend-test-2026-04-10/141-history-filter-reset.png](./assets/device-v2-frontend-test-2026-04-10/141-history-filter-reset.png)
- [./assets/device-v2-frontend-test-2026-04-10/160-relation-confirmed-only-after-fix.png](./assets/device-v2-frontend-test-2026-04-10/160-relation-confirmed-only-after-fix.png)
- [./assets/device-v2-frontend-test-2026-04-10/161-relation-filtered-diff-after-fix.png](./assets/device-v2-frontend-test-2026-04-10/161-relation-filtered-diff-after-fix.png)

8. 问题列表

- 已修复：`仅看未确认` 会错误包含已知晓/已忽略/已闭环事件
- 已修复：统计卡不跟随本地筛选结果变化
- 已修复：说明文案与当前可见列表口径不一致

### 场景 5：关系新增与删除闭环

1. 场景名称

关系变更闭环

2. 前置条件

- 主设备 `DEV20260401000032`
- 目标设备 `DEV20260401000033`

3. 操作步骤

- 在“关系”页签新增 `connected_to`
- 观察关系列表刷新
- 切到“变更记录”查看新增事件
- 删除该关系
- 再次查看删除事件

4. 实际结果

- 新增关系成功
- 新增历史风险为“中风险”
- 删除关系成功
- 删除历史风险为“高风险”
- 差异抽屉中可看到 `关系/连接` 与目标编码

5. 预期结果

- 新增/删除关系后即时生成历史记录
- 删除风险高于新增

6. 是否通过

- 通过

7. 截图建议

- [./assets/device-v2-frontend-test-2026-04-10/121-relations-tab-before-delete.png](./assets/device-v2-frontend-test-2026-04-10/121-relations-tab-before-delete.png)
- [./assets/device-v2-frontend-test-2026-04-10/124-relations-delete-focused.png](./assets/device-v2-frontend-test-2026-04-10/124-relations-delete-focused.png)
- [./assets/device-v2-frontend-test-2026-04-10/126-history-delete-verified.png](./assets/device-v2-frontend-test-2026-04-10/126-history-delete-verified.png)
- [./assets/device-v2-frontend-test-2026-04-10/130-relations-manual-input-before-add.png](./assets/device-v2-frontend-test-2026-04-10/130-relations-manual-input-before-add.png)
- [./assets/device-v2-frontend-test-2026-04-10/131-relations-after-add-via-ui.png](./assets/device-v2-frontend-test-2026-04-10/131-relations-after-add-via-ui.png)
- [./assets/device-v2-frontend-test-2026-04-10/132-history-after-add-via-ui.png](./assets/device-v2-frontend-test-2026-04-10/132-history-after-add-via-ui.png)
- [./assets/device-v2-frontend-test-2026-04-10/133-history-add-diff-drawer.png](./assets/device-v2-frontend-test-2026-04-10/133-history-add-diff-drawer.png)
- [./assets/device-v2-frontend-test-2026-04-10/134-relations-after-delete-via-ui.png](./assets/device-v2-frontend-test-2026-04-10/134-relations-after-delete-via-ui.png)
- [./assets/device-v2-frontend-test-2026-04-10/135-history-after-delete-via-ui.png](./assets/device-v2-frontend-test-2026-04-10/135-history-after-delete-via-ui.png)

8. 问题列表

- 已修复：关系列表接口解包错误导致页面空白
- 已修复：schema 缺少 `relation_types` 时无法继续纯页面测试

### 场景 6：关系类状态矩阵

1. 场景名称

关系事件状态矩阵

2. 前置条件

- 关系类记录已覆盖 `requires_action / acknowledged / ignored / resolved`

3. 操作步骤

- 在前端页面中分别将关系事件更新到不同状态
- 用状态筛选器逐项验证

4. 实际结果

- `acknowledged / ignored / resolved / requires_action` 均可被单独筛出
- 备注持久化与筛选结果一致

5. 预期结果

- 状态筛选严格命中对应记录

6. 是否通过

- 通过

7. 截图建议

- [./assets/device-v2-frontend-test-2026-04-10/170-relation-add-acknowledged.png](./assets/device-v2-frontend-test-2026-04-10/170-relation-add-acknowledged.png)
- [./assets/device-v2-frontend-test-2026-04-10/171-relation-delete-ignored.png](./assets/device-v2-frontend-test-2026-04-10/171-relation-delete-ignored.png)
- [./assets/device-v2-frontend-test-2026-04-10/172-history-status-matrix-base.png](./assets/device-v2-frontend-test-2026-04-10/172-history-status-matrix-base.png)

8. 问题列表

- 无

### 场景 7：空结果与边界一致性

1. 场景名称

空结果、跨设备与状态清理边界回归

2. 前置条件

- 关系类筛选已可把列表收敛到 0 条
- 详情页内部存在历史差异抽屉与备注输入

3. 操作步骤

- 执行 `业务域=relation + 状态=resolved + 仅看未确认`
- 观察空态、标题、说明文案、统计卡
- 打开差异抽屉，输入未提交备注
- 切出“变更记录”页签
- 再切换到另一台设备

4. 实际结果

- 0 条结果时：
  - 标题显示通用文案
  - 说明文案明确提示“当前筛选下暂无匹配的台账变更”
  - 统计卡全 0
- 切出“变更记录”页签时：
  - 差异抽屉关闭
  - 当前事件清空
  - 未提交备注清空
- 切换设备后：
  - 最终页面不会残留旧设备历史上下文

5. 预期结果

- 空结果不应混入全量结果文案
- 历史抽屉状态不应跨页签和跨设备残留

6. 是否通过

- 通过

7. 截图建议

- [./assets/device-v2-frontend-test-2026-04-10/190-history-description-after-fix.png](./assets/device-v2-frontend-test-2026-04-10/190-history-description-after-fix.png)
- [./assets/device-v2-frontend-test-2026-04-10/191-history-empty-description-after-fix.png](./assets/device-v2-frontend-test-2026-04-10/191-history-empty-description-after-fix.png)
- [./assets/device-v2-frontend-test-2026-04-10/200-history-empty-filter-state.png](./assets/device-v2-frontend-test-2026-04-10/200-history-empty-filter-state.png)
- [./assets/device-v2-frontend-test-2026-04-10/201-history-switch-device-state.png](./assets/device-v2-frontend-test-2026-04-10/201-history-switch-device-state.png)
- [./assets/device-v2-frontend-test-2026-04-10/220-tab-switch-state-cleanup.png](./assets/device-v2-frontend-test-2026-04-10/220-tab-switch-state-cleanup.png)
- [./assets/device-v2-frontend-test-2026-04-10/221-device-switch-state-cleanup.png](./assets/device-v2-frontend-test-2026-04-10/221-device-switch-state-cleanup.png)

8. 问题列表

- 已修复：空结果时标题与说明文案仍沿用全量数据
- 已修复：离开历史页签后差异抽屉与未提交备注仍残留

---

## 五、遗留问题与风险

### 1. Schema 保存受预检查门禁阻断

问题描述：

- `Device V2 Schema` 正式保存仍会返回 `Schema 预检查未通过，禁止保存`
- 当前页面已能展示真实错误，但问题本身仍存在

问题等级：

- P1

复现概率：

- 必现

影响范围：

- 关系类型配置正式发布
- 依赖 schema 持久化的配置流程

初步怀疑点：

- 现网样本缺少必填字段，例如 `platform_code`

截图建议：

- [./assets/device-v2-frontend-test-2026-04-10/127-schema-save-message-after-fix.png](./assets/device-v2-frontend-test-2026-04-10/127-schema-save-message-after-fix.png)

### 2. 状态更新失败时可能重复提示

问题描述：

- 模拟接口失败时，页面会同时出现两类错误提示

问题等级：

- P2

复现概率：

- 高概率

影响范围：

- 历史状态流转失败反馈

初步怀疑点：

- request 拦截器与调用方重复弹错

截图建议：

- [./assets/device-v2-frontend-test-2026-04-10/93-status-failure.png](./assets/device-v2-frontend-test-2026-04-10/93-status-failure.png)

---

## 六、回归验证

已执行：

- `npm run typecheck`
- 多轮真实前端页面回归
- 同设备内多次新增/删除关系验证
- 状态与备注刷新回归
- 空结果、切页签、切设备边界回归

---

## 七、最终判断

当前结论：

- `Device V2 Change History` 前端页面已具备可演示、可操作、可筛选、可闭环的稳定能力
- 关系类记录已达到前端页面级别的完整测试闭环
- 当前剩余风险主要集中在：
  - schema 预检查门禁导致的环境阻塞
  - 个别失败场景下的提示体验

建议：

- 以当前版本作为前端联调验收基线
- 后续如果继续推进，可转入 migration 执行验证、Schema 数据修复以及失败态 UX 收口

---

## 八、截图总索引

以下为本次执行过程中保留的全部截图文件。

截图归档目录：

- `docs/assets/device-v2-frontend-test-2026-04-10/`

- [./assets/device-v2-frontend-test-2026-04-10/01-after-login.png](./assets/device-v2-frontend-test-2026-04-10/01-after-login.png)
- [./assets/device-v2-frontend-test-2026-04-10/02-device-list.png](./assets/device-v2-frontend-test-2026-04-10/02-device-list.png)
- [./assets/device-v2-frontend-test-2026-04-10/08-smoke-via-detail.png](./assets/device-v2-frontend-test-2026-04-10/08-smoke-via-detail.png)
- [./assets/device-v2-frontend-test-2026-04-10/10-login-page.png](./assets/device-v2-frontend-test-2026-04-10/10-login-page.png)
- [./assets/device-v2-frontend-test-2026-04-10/11-after-login.png](./assets/device-v2-frontend-test-2026-04-10/11-after-login.png)
- [./assets/device-v2-frontend-test-2026-04-10/11-detail-access.png](./assets/device-v2-frontend-test-2026-04-10/11-detail-access.png)
- [./assets/device-v2-frontend-test-2026-04-10/110-schema-saved.png](./assets/device-v2-frontend-test-2026-04-10/110-schema-saved.png)
- [./assets/device-v2-frontend-test-2026-04-10/111-relations-before-add.png](./assets/device-v2-frontend-test-2026-04-10/111-relations-before-add.png)
- [./assets/device-v2-frontend-test-2026-04-10/112-relations-after-add.png](./assets/device-v2-frontend-test-2026-04-10/112-relations-after-add.png)
- [./assets/device-v2-frontend-test-2026-04-10/113-history-after-add.png](./assets/device-v2-frontend-test-2026-04-10/113-history-after-add.png)
- [./assets/device-v2-frontend-test-2026-04-10/114-relations-after-delete.png](./assets/device-v2-frontend-test-2026-04-10/114-relations-after-delete.png)
- [./assets/device-v2-frontend-test-2026-04-10/115-history-after-delete.png](./assets/device-v2-frontend-test-2026-04-10/115-history-after-delete.png)
- [./assets/device-v2-frontend-test-2026-04-10/12-after-edit.png](./assets/device-v2-frontend-test-2026-04-10/12-after-edit.png)
- [./assets/device-v2-frontend-test-2026-04-10/12-edit-modal-open.png](./assets/device-v2-frontend-test-2026-04-10/12-edit-modal-open.png)
- [./assets/device-v2-frontend-test-2026-04-10/120-relations-before-delete-overview.png](./assets/device-v2-frontend-test-2026-04-10/120-relations-before-delete-overview.png)
- [./assets/device-v2-frontend-test-2026-04-10/121-relations-tab-before-delete.png](./assets/device-v2-frontend-test-2026-04-10/121-relations-tab-before-delete.png)
- [./assets/device-v2-frontend-test-2026-04-10/122-relations-tab-after-delete.png](./assets/device-v2-frontend-test-2026-04-10/122-relations-tab-after-delete.png)
- [./assets/device-v2-frontend-test-2026-04-10/123-history-after-delete.png](./assets/device-v2-frontend-test-2026-04-10/123-history-after-delete.png)
- [./assets/device-v2-frontend-test-2026-04-10/124-relations-delete-focused.png](./assets/device-v2-frontend-test-2026-04-10/124-relations-delete-focused.png)
- [./assets/device-v2-frontend-test-2026-04-10/125-history-after-delete-focused.png](./assets/device-v2-frontend-test-2026-04-10/125-history-after-delete-focused.png)
- [./assets/device-v2-frontend-test-2026-04-10/126-history-delete-verified.png](./assets/device-v2-frontend-test-2026-04-10/126-history-delete-verified.png)
- [./assets/device-v2-frontend-test-2026-04-10/127-schema-save-message-after-fix.png](./assets/device-v2-frontend-test-2026-04-10/127-schema-save-message-after-fix.png)
- [./assets/device-v2-frontend-test-2026-04-10/130-relations-manual-input-before-add.png](./assets/device-v2-frontend-test-2026-04-10/130-relations-manual-input-before-add.png)
- [./assets/device-v2-frontend-test-2026-04-10/131-relations-after-add-via-ui.png](./assets/device-v2-frontend-test-2026-04-10/131-relations-after-add-via-ui.png)
- [./assets/device-v2-frontend-test-2026-04-10/132-history-after-add-via-ui.png](./assets/device-v2-frontend-test-2026-04-10/132-history-after-add-via-ui.png)
- [./assets/device-v2-frontend-test-2026-04-10/133-history-add-diff-drawer.png](./assets/device-v2-frontend-test-2026-04-10/133-history-add-diff-drawer.png)
- [./assets/device-v2-frontend-test-2026-04-10/134-relations-after-delete-via-ui.png](./assets/device-v2-frontend-test-2026-04-10/134-relations-after-delete-via-ui.png)
- [./assets/device-v2-frontend-test-2026-04-10/135-history-after-delete-via-ui.png](./assets/device-v2-frontend-test-2026-04-10/135-history-after-delete-via-ui.png)
- [./assets/device-v2-frontend-test-2026-04-10/140-history-filter-base.png](./assets/device-v2-frontend-test-2026-04-10/140-history-filter-base.png)
- [./assets/device-v2-frontend-test-2026-04-10/141-history-filter-reset.png](./assets/device-v2-frontend-test-2026-04-10/141-history-filter-reset.png)
- [./assets/device-v2-frontend-test-2026-04-10/150-relation-delete-status-before.png](./assets/device-v2-frontend-test-2026-04-10/150-relation-delete-status-before.png)
- [./assets/device-v2-frontend-test-2026-04-10/151-relation-delete-status-after.png](./assets/device-v2-frontend-test-2026-04-10/151-relation-delete-status-after.png)
- [./assets/device-v2-frontend-test-2026-04-10/152-relation-delete-status-after-refresh.png](./assets/device-v2-frontend-test-2026-04-10/152-relation-delete-status-after-refresh.png)
- [./assets/device-v2-frontend-test-2026-04-10/160-relation-confirmed-only-after-fix.png](./assets/device-v2-frontend-test-2026-04-10/160-relation-confirmed-only-after-fix.png)
- [./assets/device-v2-frontend-test-2026-04-10/161-relation-filtered-diff-after-fix.png](./assets/device-v2-frontend-test-2026-04-10/161-relation-filtered-diff-after-fix.png)
- [./assets/device-v2-frontend-test-2026-04-10/170-relation-add-acknowledged.png](./assets/device-v2-frontend-test-2026-04-10/170-relation-add-acknowledged.png)
- [./assets/device-v2-frontend-test-2026-04-10/171-relation-delete-ignored.png](./assets/device-v2-frontend-test-2026-04-10/171-relation-delete-ignored.png)
- [./assets/device-v2-frontend-test-2026-04-10/172-history-status-matrix-base.png](./assets/device-v2-frontend-test-2026-04-10/172-history-status-matrix-base.png)
- [./assets/device-v2-frontend-test-2026-04-10/180-history-stats-after-fix.png](./assets/device-v2-frontend-test-2026-04-10/180-history-stats-after-fix.png)
- [./assets/device-v2-frontend-test-2026-04-10/19-error.png](./assets/device-v2-frontend-test-2026-04-10/19-error.png)
- [./assets/device-v2-frontend-test-2026-04-10/190-history-description-after-fix.png](./assets/device-v2-frontend-test-2026-04-10/190-history-description-after-fix.png)
- [./assets/device-v2-frontend-test-2026-04-10/191-history-empty-description-after-fix.png](./assets/device-v2-frontend-test-2026-04-10/191-history-empty-description-after-fix.png)
- [./assets/device-v2-frontend-test-2026-04-10/20-login.png](./assets/device-v2-frontend-test-2026-04-10/20-login.png)
- [./assets/device-v2-frontend-test-2026-04-10/200-history-empty-filter-state.png](./assets/device-v2-frontend-test-2026-04-10/200-history-empty-filter-state.png)
- [./assets/device-v2-frontend-test-2026-04-10/201-history-switch-device-state.png](./assets/device-v2-frontend-test-2026-04-10/201-history-switch-device-state.png)
- [./assets/device-v2-frontend-test-2026-04-10/21-detail-access.png](./assets/device-v2-frontend-test-2026-04-10/21-detail-access.png)
- [./assets/device-v2-frontend-test-2026-04-10/212-drawer-open-state.png](./assets/device-v2-frontend-test-2026-04-10/212-drawer-open-state.png)
- [./assets/device-v2-frontend-test-2026-04-10/213-after-tab-state-switch.png](./assets/device-v2-frontend-test-2026-04-10/213-after-tab-state-switch.png)
- [./assets/device-v2-frontend-test-2026-04-10/214-after-device-state-switch.png](./assets/device-v2-frontend-test-2026-04-10/214-after-device-state-switch.png)
- [./assets/device-v2-frontend-test-2026-04-10/22-edit-open.png](./assets/device-v2-frontend-test-2026-04-10/22-edit-open.png)
- [./assets/device-v2-frontend-test-2026-04-10/220-tab-switch-state-cleanup.png](./assets/device-v2-frontend-test-2026-04-10/220-tab-switch-state-cleanup.png)
- [./assets/device-v2-frontend-test-2026-04-10/221-device-switch-state-cleanup.png](./assets/device-v2-frontend-test-2026-04-10/221-device-switch-state-cleanup.png)
- [./assets/device-v2-frontend-test-2026-04-10/23-edit-filled.png](./assets/device-v2-frontend-test-2026-04-10/23-edit-filled.png)
- [./assets/device-v2-frontend-test-2026-04-10/30-before-history.png](./assets/device-v2-frontend-test-2026-04-10/30-before-history.png)
- [./assets/device-v2-frontend-test-2026-04-10/31-edit-before-save.png](./assets/device-v2-frontend-test-2026-04-10/31-edit-before-save.png)
- [./assets/device-v2-frontend-test-2026-04-10/32-after-history.png](./assets/device-v2-frontend-test-2026-04-10/32-after-history.png)
- [./assets/device-v2-frontend-test-2026-04-10/33-diff-open.png](./assets/device-v2-frontend-test-2026-04-10/33-diff-open.png)
- [./assets/device-v2-frontend-test-2026-04-10/40-before-history.png](./assets/device-v2-frontend-test-2026-04-10/40-before-history.png)
- [./assets/device-v2-frontend-test-2026-04-10/50-status-drawer-open.png](./assets/device-v2-frontend-test-2026-04-10/50-status-drawer-open.png)
- [./assets/device-v2-frontend-test-2026-04-10/51-status-after-flow.png](./assets/device-v2-frontend-test-2026-04-10/51-status-after-flow.png)
- [./assets/device-v2-frontend-test-2026-04-10/52-status-refresh.png](./assets/device-v2-frontend-test-2026-04-10/52-status-refresh.png)
- [./assets/device-v2-frontend-test-2026-04-10/60-filter-base.png](./assets/device-v2-frontend-test-2026-04-10/60-filter-base.png)
- [./assets/device-v2-frontend-test-2026-04-10/61-filter-unconfirmed.png](./assets/device-v2-frontend-test-2026-04-10/61-filter-unconfirmed.png)
- [./assets/device-v2-frontend-test-2026-04-10/62-filter-status-resolved.png](./assets/device-v2-frontend-test-2026-04-10/62-filter-status-resolved.png)
- [./assets/device-v2-frontend-test-2026-04-10/63-filter-risk-high.png](./assets/device-v2-frontend-test-2026-04-10/63-filter-risk-high.png)
- [./assets/device-v2-frontend-test-2026-04-10/64-filter-domain-management.png](./assets/device-v2-frontend-test-2026-04-10/64-filter-domain-management.png)
- [./assets/device-v2-frontend-test-2026-04-10/65-filter-source-manual.png](./assets/device-v2-frontend-test-2026-04-10/65-filter-source-manual.png)
- [./assets/device-v2-frontend-test-2026-04-10/66-filter-time-7d.png](./assets/device-v2-frontend-test-2026-04-10/66-filter-time-7d.png)
- [./assets/device-v2-frontend-test-2026-04-10/67-filter-keyfield.png](./assets/device-v2-frontend-test-2026-04-10/67-filter-keyfield.png)
- [./assets/device-v2-frontend-test-2026-04-10/72-filter-base-state.png](./assets/device-v2-frontend-test-2026-04-10/72-filter-base-state.png)
- [./assets/device-v2-frontend-test-2026-04-10/73-filter-confirmedOnly.png](./assets/device-v2-frontend-test-2026-04-10/73-filter-confirmedOnly.png)
- [./assets/device-v2-frontend-test-2026-04-10/74-filter-status-resolved.png](./assets/device-v2-frontend-test-2026-04-10/74-filter-status-resolved.png)
- [./assets/device-v2-frontend-test-2026-04-10/75-filter-risk-high.png](./assets/device-v2-frontend-test-2026-04-10/75-filter-risk-high.png)
- [./assets/device-v2-frontend-test-2026-04-10/76-filter-domain-management.png](./assets/device-v2-frontend-test-2026-04-10/76-filter-domain-management.png)
- [./assets/device-v2-frontend-test-2026-04-10/77-filter-source-manual.png](./assets/device-v2-frontend-test-2026-04-10/77-filter-source-manual.png)
- [./assets/device-v2-frontend-test-2026-04-10/78-filter-time7d.png](./assets/device-v2-frontend-test-2026-04-10/78-filter-time7d.png)
- [./assets/device-v2-frontend-test-2026-04-10/79-filter-keyfield.png](./assets/device-v2-frontend-test-2026-04-10/79-filter-keyfield.png)
- [./assets/device-v2-frontend-test-2026-04-10/80-filter-combo-source-status.png](./assets/device-v2-frontend-test-2026-04-10/80-filter-combo-source-status.png)
- [./assets/device-v2-frontend-test-2026-04-10/81-filter-combo-risk-domain.png](./assets/device-v2-frontend-test-2026-04-10/81-filter-combo-risk-domain.png)
- [./assets/device-v2-frontend-test-2026-04-10/82-filter-reset-state.png](./assets/device-v2-frontend-test-2026-04-10/82-filter-reset-state.png)
- [./assets/device-v2-frontend-test-2026-04-10/83-relation-tab-blocked.png](./assets/device-v2-frontend-test-2026-04-10/83-relation-tab-blocked.png)
- [./assets/device-v2-frontend-test-2026-04-10/90-schema-relation-types.png](./assets/device-v2-frontend-test-2026-04-10/90-schema-relation-types.png)
- [./assets/device-v2-frontend-test-2026-04-10/91-empty-history.png](./assets/device-v2-frontend-test-2026-04-10/91-empty-history.png)
- [./assets/device-v2-frontend-test-2026-04-10/92-rapid-toggle.png](./assets/device-v2-frontend-test-2026-04-10/92-rapid-toggle.png)
- [./assets/device-v2-frontend-test-2026-04-10/93-status-failure.png](./assets/device-v2-frontend-test-2026-04-10/93-status-failure.png)
- [./assets/device-v2-frontend-test-2026-04-10/99-error.png](./assets/device-v2-frontend-test-2026-04-10/99-error.png)
- [./assets/device-v2-frontend-test-2026-04-10/99-script-error.png](./assets/device-v2-frontend-test-2026-04-10/99-script-error.png)
- [./assets/device-v2-frontend-test-2026-04-10/99-stage2-error.png](./assets/device-v2-frontend-test-2026-04-10/99-stage2-error.png)
- [./assets/device-v2-frontend-test-2026-04-10/99-stage2-rerun-error.png](./assets/device-v2-frontend-test-2026-04-10/99-stage2-rerun-error.png)
- [./assets/device-v2-frontend-test-2026-04-10/device-page-debug.png](./assets/device-v2-frontend-test-2026-04-10/device-page-debug.png)
- [./assets/device-v2-frontend-test-2026-04-10/edit-modal-debug.png](./assets/device-v2-frontend-test-2026-04-10/edit-modal-debug.png)
- [./assets/device-v2-frontend-test-2026-04-10/edit-save-debug.png](./assets/device-v2-frontend-test-2026-04-10/edit-save-debug.png)
- [./assets/device-v2-frontend-test-2026-04-10/explore-detail.png](./assets/device-v2-frontend-test-2026-04-10/explore-detail.png)
- [./assets/device-v2-frontend-test-2026-04-10/hash-nav.png](./assets/device-v2-frontend-test-2026-04-10/hash-nav.png)
- [./assets/device-v2-frontend-test-2026-04-10/login-debug.png](./assets/device-v2-frontend-test-2026-04-10/login-debug.png)
