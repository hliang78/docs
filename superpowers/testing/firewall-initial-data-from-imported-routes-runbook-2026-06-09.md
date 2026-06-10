# Firewall Initial Data From Imported Routes Runbook

## 目标

利用 `imported-configs` 配置文件和已提取的路由网段，为防火墙模块准备一套可测试的初始数据：

- 基础资料：机房、安全区域、网段、Connector。
- 节点纳管与区域映射：防火墙节点、配置上传、配置解析、接口到安全区域映射。
- 连接规划：节点到外部网络/Internet/专线 Connector 的连接关系。
- 校验入口：readiness、接口路由与区域网段对比、管理习惯反推、策略概览。

推荐主数据源：

```text
docs/superpowers/testing/firewall-imported-config-nodemap-route-segments-2026-06-09.csv
```

这份 CSV 使用 `nodemap.NewNodeMapFromNetwork` + `AddressTable.ToSliceMap()` 导出，和平台配置快照/路由对比更接近。`firewall-imported-config-route-segments-2026-06-09.csv` 是原始 `route-static` 命令口径，只用于排查配置文本。

## 数据分层

### 1. 机房规划

先创建 1 个测试机房即可，建议：

```text
Name: 防火墙导入测试机房
Code: FW_IMPORT_DC
SiteCode: FW_IMPORT_SITE
```

对应接口：

```http
POST /firewall/planning/datacenter
```

用途：

- 所有导入的防火墙节点归属同一个测试机房。
- 安全区域和 Connector 也绑定到这个机房，方便页面筛选。

### 2. 防火墙节点

每个配置文件准备一个 `firewall_node`：

| CSV 字段 | 节点字段 |
| --- | --- |
| `node` | `name` |
| 文件名开头 IP | `ip` |
| `platform` | `platform`，OneOPS 页面用 `USG` / `SecPath` / `Dptech` |
| 测试机房 ID | `datacenter_id` |

接口顺序：

```http
POST /firewall/planning/firewall-node
POST /firewall/planning/firewall-node/:id/update-config-file
POST /firewall/planning/firewall-node/:id/parse-config-text
```

关键点：

- 上传配置只生成配置文件对象和 `config_fact_snapshot`。
- 还要调用 `parse-config-text`，它会根据配置解析出的接口、zone、IP 自动创建或更新 `firewall_zone_mapping`。
- 后续安全区域能自动匹配 `mapping.config_zone == security_zone.name/security_zone_code`。

### 3. 安全区域与网段

安全区域由两类数据生成：

1. 配置解析出来的接口 zone：来自 `firewall_zone_mapping.config_zone`。
2. 路由目的网段：来自 NodeMap 路由 CSV 的 `destination_cidr`。

建议规则：

| 路由特征 | 初始区域建议 |
| --- | --- |
| `destination_cidr = 0.0.0.0/0` 或 `::/0` | 外部区域，如 `INTERNET` / `CMNET`，`zone_type=external`，`zone_role=internet` |
| `vrf = MGMT` | 管理区域，如 `MGMT`，`zone_type=internal`，`zone_role=internal` |
| 有 `zone` 字段 | 用 `zone` 创建或匹配安全区域 |
| `zone` 为空但有 `vrf` | 用 `vrf` 创建临时安全区域，后续人工改名 |
| `/32` 或 `/128` 主机路由 | 测试阶段保留；生产资料可在业务确认后聚合 |

接口：

```http
POST /firewall/planning/zone
POST /firewall/planning/zone/segment-mode-list
```

网段字段映射：

| CSV 字段 | NetworkSegment 字段 |
| --- | --- |
| `destination_cidr` | `cidr` |
| `vrf` | `vrf_code` |
| `next_hop` | `gateway` |
| `platform/node/out_interface` | `description` |
| 固定 `DEFAULT` | `segment_type` |

注意：

- 为了让“接口路由与区域网段对比”准确，初始测试数据建议先保留所有唯一 `destination_cidr`。
- 如果只是为了页面有基础资料，可按业务大段聚合，但聚合后 route compare 会出现 route-only/zone-only 差异。

### 4. 节点与区域映射

优先让平台自己产生映射：

```http
POST /firewall/planning/firewall-node/:id/parse-config-text
POST /firewall/planning/firewall-zone-mapping/list
```

然后处理未绑定区域的映射：

```http
POST /firewall/planning/firewall-zone-mapping/quick-create-zone
```

适用场景：

- 某个接口有 `config_zone`，但系统里还没有对应安全区域。
- 快速创建会从该接口的非直连路由推导 `network_segments`。

推荐流程：

1. 先上传并解析配置。
2. 打开“节点纳管与区域映射”。
3. 对未绑定的接口用“快速创建区域”。
4. 用路由 CSV 检查它生成的网段是否覆盖该接口相关路由。

### 5. Connector 与连接规划

从默认路由和外部区域准备 Connector：

| 路由特征 | Connector 建议 |
| --- | --- |
| `destination_cidr=0.0.0.0/0` 或 `::/0` | `INTERNET`，`connector_type=internet` |
| 下一跳指向运营商/CMNET/边界 | `CMNET` 或 `BORDER_NETWORK`，`connector_type=network_region` |
| 管理 VRF 默认路由 | `MGMT_NETWORK`，`connector_type=network_region` |

接口：

```http
POST /firewall/planning/connector
POST /firewall/planning/connection-planning/node-connector-connection
GET  /firewall/planning/connection-planning/data
```

节点到 Connector 连接字段：

| CSV 字段 | 连接字段 |
| --- | --- |
| 防火墙节点 ID | `node_id` |
| Connector ID | `connector_id` |
| `zone` 或外部区域名 | `zone_name` |
| `vrf` | `vrf_name` |
| 默认 `direct` | `connection_type` |

## 推荐落地顺序

1. 创建测试机房。
2. 创建 6 个防火墙节点。
3. 上传 6 份配置文件。
4. 对每个节点调用 `parse-config-text`，生成接口映射。
5. 从 NodeMap 路由 CSV 生成安全区域候选和网段候选。
6. 先创建外部区域和管理区域，再创建业务 VRF/zone 区域。
7. 用 `quick-create-zone` 或手动更新，把接口映射绑定到安全区域。
8. 用默认路由创建 Connector 和节点连接。
9. 跑 readiness 和 route compare。

## 验收检查

节点纳管：

```http
POST /firewall/planning/firewall-node/list
GET  /firewall/planning/firewall-node/:id/config-snapshot
GET  /firewall/planning/firewall-node/:id/readiness
```

区域与网段：

```http
POST /firewall/planning/zone/list
POST /firewall/planning/zone/segment-mode-list
```

映射与路由对比：

```http
POST /firewall/planning/firewall-zone-mapping/list
GET  /firewall/planning/firewall-zone-mapping/:id/route-compare
POST /firewall/planning/firewall-zone-mapping/interface-route-compare
```

连接规划：

```http
GET /firewall/planning/connection-planning/data
```

通过标准：

- 节点总数为 6。
- 每个节点都有 `config_file_object_name` 和 `config_fact_snapshot`。
- 每个节点 `parse-config-text` 后能看到接口映射。
- 网段模式列表能看到从 CSV 派生出的 `destination_cidr`。
- 默认路由对应外部 Connector。
- `route-compare` 中 matched 数逐步增加，route-only 项可追踪到 CSV 原始路由。

## 不建议直接做的事

- 不建议只写 SQL 插入 `firewall_node.config_fact_snapshot`，因为配置文件还需要 MinIO 对象，页面“配置回读”会缺数据。
- 不建议跳过 `parse-config-text` 手工灌 `firewall_zone_mapping`，否则接口、zone、IP 变化不会被解析器校正。
- 不建议一开始就聚合 `/32` 主机路由；先保留明细，等 route compare 跑通后再做业务归并。

