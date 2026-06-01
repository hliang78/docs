---
topic: oneops-operation-audit
kind: backend
title: OneOPS 统一操作审计切换方案
createdAt: 2026-05-21T16:15:00+0800
---

# 切换方案

## 当前状态

- 正式菜单标题已收敛为 `操作审计`
- 正式菜单入口由动态路由重写到 [OperationAudit.vue](/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/views/sys/OperationAudit.vue)
- 旧日志页已降级为兼容页 [LegacyLogRecord.vue](/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/views/sys/LegacyLogRecord.vue)
- 兼容隐藏路由为 `/#/sys/log-record-legacy`

## 推荐切换节奏

### 阶段 1：预览验证

目标：

- 验证新页是否更适合回答“谁改了什么”
- 验证五类来源的混合展示是否清晰
- 收集字段和摘要文案反馈

动作：

- 保持数据库菜单数据不变
- 通过前端动态路由把旧菜单无感切到新页
- 通过 legacy 隐藏路由回看旧页

通过标准：

- 主要使用者认可新页列表比旧页更容易理解
- 详情卡片能支撑日常排查
- 没有出现明显误导性的聚合字段

### 阶段 2：灰度替换菜单

目标：

- 不删除旧页，但让主入口开始指向新页

动作：

- 菜单 `LogRecord` 继续保留原 name/code/path
- 前端路由层重写标题为 `操作审计`
- 前端路由层重写组件为 `../views/sys/OperationAudit.vue`
- 在新页顶部保留“返回旧日志页”入口
- 旧页继续保留为隐藏兼容页

通过标准：

- 日常使用者可以在不培训或极少培训情况下使用新页
- 没有因切换造成旧日志排障能力丢失

### 阶段 3：正式收口

目标：

- 统一把“日志管理”心智迁移成“统一操作审计”

动作：

- 根据灰度结果决定是否同步修改数据库菜单标题
- 旧页继续保留为只读兼容页，或在后续放到更深隐藏入口

## 推荐保守策略

我更推荐：

1. 先不改数据库初始化 SQL 菜单定义
2. 由前端动态路由先完成切换
3. 测试稳定后再决定是否同步 DB 菜单数据

原因：

- 风险最小
- 用户习惯影响最小
- 回退最容易

## 切菜单时需要一起确认的点

### 1. 菜单标题

已确认为：

- `操作审计`

### 2. 旧页是否保留

已确认：

- 保留为隐藏回退页

### 3. 旧页能力是否要在新页补齐

建议至少确认这三项：

- `request_info/response_info` 是否够看
- 旧 `module` 维度是否还需要更细
- `log_record` 的失败原因是否要在列表更直观展示

## 回退策略

如果切换后体验不理想：

1. 关闭路由重写或将其切回旧页组件
2. 保留 [OperationAudit.vue](/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/views/sys/OperationAudit.vue) 继续迭代
3. legacy 页继续保留

## 上线前检查清单

- 新页查询性能可接受
- Device V2 / terminal / credential / task / system 五类来源都能查到样例
- 详情卡片字段能覆盖主要排障问题
- 旧页和新页都能互相跳转
- 回退路径明确
