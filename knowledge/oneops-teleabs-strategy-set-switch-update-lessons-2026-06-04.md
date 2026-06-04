# OneOps Teleabs 策略集开关更新问题经验

日期：2026-06-04

## 背景

在“监控策略与 Teleabs 模板”页面编辑服务器带外 Redfish 策略集时，用户开启“自动入库”和“启用状态”两个开关并确认，前端提示更新成功，但刷新页面和查询数据库后发现：

- `auto_apply_on_store` 仍为 `0`
- `enabled` 仍为 `0`
- `updated_at` 没有变化

这类问题容易被误判为前端开关组件、列表缓存或页面刷新问题，但真实根因在后端持久化层。

## 关键判断

排查时先绕过前端，直接调用后端 API：

```bash
curl -sS -H 'X-Auth-Token: abc123' \
  'http://127.0.0.1:8080/api/v1/platform/metrics/teleabs/strategy-sets/server_oob_redfish' \
| jq '.data | .auto_apply_on_store=true | .enabled=true |
  {name,description,mode,catalog,catalogs,collection_mode,function_area,
   auto_apply_on_store,enabled,output_ids,attach_processor_strategy_id,
   dashboard_codes,items}' \
| curl -sS -i -X PUT \
  -H 'X-Auth-Token: abc123' \
  -H 'Content-Type: application/json' \
  --data-binary @- \
  'http://127.0.0.1:8080/api/v1/platform/metrics/teleabs/strategy-sets/server_oob_redfish'
```

如果 API 返回 `更新成功`，但随后 API 和数据库仍未变化，说明问题不在前端，而在后端 update 链路或运行时代码。

数据库回查：

```sql
SELECT id,name,enabled,auto_apply_on_store,updated_at
FROM platform_teleabs_strategy_set
WHERE id='server_oob_redfish';
```

## 根因

`proxyTeleabsStrategySetStore.UpdateStrategySet` 使用 GORM `Updates(map[string]interface{})` 时，实际没有可靠持久化 `auto_apply_on_store=false -> true` 这类布尔开关变化。

同时旧实现只返回 `tx.Error`，没有检查 `RowsAffected`。当 SQL 影响 0 行或没有有效变化时，API 仍可能返回“更新成功”，造成“假成功”。

## 修复原则

策略集这类配置保存属于管理面强一致写入，不能只看 ORM error：

1. 对需要显式写入 `false/true` 的配置字段，使用能直写零值的更新方式。
2. 显式更新 `updated_at`，方便用户和排查工具确认写入发生过。
3. 检查 `RowsAffected`。如果目标行不存在，返回明确错误，避免 API 假成功。
4. 用回归测试覆盖“开关能落库”和“缺失行不能静默成功”。

修复后的核心形态：

```go
tx := db.Where("id = ?", m.ID).UpdateColumns(map[string]interface{}{
    "auto_apply_on_store": m.AutoApplyOnStore,
    "enabled":             m.Enabled,
    "updated_at":          time.Now(),
    // other fields...
})
if tx.Error != nil {
    return tx.Error
}
if tx.RowsAffected == 0 {
    var count int64
    if err := db.Where("id = ?", m.ID).Count(&count).Error; err != nil {
        return err
    }
    if count == 0 {
        return fmt.Errorf("teleabs strategy set not found: %s", m.ID)
    }
}
```

## 推荐排查路径

遇到“页面提示成功但数据没变”时，按下面顺序切层：

1. 前端 GET 当前详情，记录真实值。
2. 直接 PUT 后端 API，排除前端表单和代理问题。
3. 立即 GET 后端 API 和查数据库，确认是否真正持久化。
4. 如果 API 成功但 DB 不变，检查后端 store 的更新方式、零值字段写入、`RowsAffected`、租户过滤条件。
5. 加最小回归测试，先复现红点，再改实现。
6. 重启运行中的后端进程，用真实 API 再验证一次。

## 本次验证

修复后执行：

```bash
go test ./app/platform/service/impl \
  -run 'TestProxyTeleabsStrategySetStore_UpdateStrategySet|TestTeleabsStrategySetSrv_|TestServerOOB(IPMI|Redfish|SNMP)|TestGenerateFromStrategy_UsesConfiguredTemplateRegistryForRedfish|TestTargetResolverRegistryV2_ResolveTargets_ServerOOB(IPMI|Redfish)' \
  -count=1
```

结果通过。

真实 API 验证后，数据库中 `server_oob_redfish` 已更新为：

- `enabled = 1`
- `auto_apply_on_store = 1`
- `updated_at = 2026-06-04 20:19:13.746`

## 经验沉淀

- “接口成功”不等于“数据写入成功”，配置管理接口要把 `RowsAffected` 纳入语义。
- 布尔开关、空字符串、空 JSON 等零值字段，不能使用会跳过零值的 ORM 更新路径。
- 对用户可见的开关类配置，必须有覆盖 `false -> true` 和 `true -> false` 的持久化测试。
- 重启服务只能排除旧二进制问题，不能替代数据层验证。
- 排查多组件链路时，优先用 API 和 DB 双重证据定位断点，少猜前端。
