# 防火墙安全区域与网段导入清单（2026-06-09）

来源：本地平台 `firewall_node.config_fact_snapshot`，机房 `FW-VSYS-SPLIT-20260609`。

## 文件

- `firewall-security-zone-segments-direct-import.csv`：主文件，按“防火墙节点 + 配置区域”生成安全区域，并直接携带 CIDR 网段。适合 `OneOps/cmd/firewall_csv_import` 或后续 API 批量创建使用。
- `firewall-security-zone-ui-excel-import.csv` / `.xlsx`：兼容当前前端“安全区域规划 -> 批量导入”的列名。注意：当前后端会把“网段名称”当作 Prefix.name 反查；如果基础 Prefix 表里没有同名 CIDR，该文件只能导入区域，不能直接落网段。
- `firewall-security-zone-api-payload.json`：`POST /api/v1/firewall/planning/zone` 的请求草稿数组，保留 `network_segments`。
- `firewall-security-zone-summary.csv`：区域级汇总，用于核对。

## 统计

- 防火墙节点：17
- 安全区域：34
- 直接导入行：195
- 前端 Excel 行：195
- 无网段区域：9
- 默认路由网段行：18

## 约定

安全区域名称格式：`<节点/VSYS标识>::<配置区域名>`，避免不同防火墙上的 `Trust`、`Untrust` 等区域互相覆盖。

网段来源：

- `interface`：接口 IP 推导出的直连网段；
- `route`：配置快照中的非默认路由目的网段；
- `route_default`：默认路由 `0.0.0.0/0` 或 `::/0`。管理类区域的默认路由已跳过，只保留管理直连网段；若管理 VSYS 未解析出配置区域名，则 `UNMAPPED` 也按管理区处理。
