---
topic: oneops-operation-audit
kind: backend
title: OneOPS 操作审计切换决议
createdAt: 2026-05-21T16:35:00+0800
---

# 切换决议

## 已确认决策

1. 正式菜单标题采用 `操作审计`
2. 旧页保留，但改名为 legacy 兼容页
3. 新页改为正式 `OperationAudit.vue`
4. 现有 `LogRecord` 菜单入口完成切换

## 本次实现方式

- 旧页：
  - [LegacyLogRecord.vue](/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/views/sys/LegacyLogRecord.vue)
- 新页：
  - [OperationAudit.vue](/Users/huangliang/project/OneOPS-ALL/OneOPS-UI/src/views/sys/OperationAudit.vue)
- 动态路由层对 `LogRecord` 菜单进行重写：
  - 标题重写为 `操作审计`
  - 组件重写为 `../views/sys/OperationAudit.vue`
- 同时保留隐藏兼容路由：
  - `sys/log-record-legacy`

## 结果

- 用户从原来的 `LogRecord` 菜单进入时，会直接看到新操作审计页
- 旧日志页仍然可访问，用于回退和对照
- 数据库菜单初始化 SQL 暂不强制变更，先由前端动态路由兼容切换

## 后续建议

- 如果灰度稳定，再考虑把 DB 菜单标题和组件路径也一并改到正式值
- 如果后续要进一步产品化，可以把 legacy 页标题明确成 `旧日志`
