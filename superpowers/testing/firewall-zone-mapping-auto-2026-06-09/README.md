# Firewall Zone Mapping Auto Seed

从 `firewall_node.config_fact_snapshot` 自动推导接口到安全区域的映射。

- 数据中心: `FW-VSYS-SPLIT-20260609` (`baa0f9bb-63ec-11f1-99fe-fa163e7745bf`)
- 节点数: 17
- 安全区域数: 34
- 可自动映射: 44
- 未匹配: 0
- 冲突: 0

匹配规则：`安全区域名称 = 节点派生前缀 + "::" + 配置区域名`，例如 `VSYS-SPLIT-vsys_vrouteshzjhapcorsp_10005_1` 的 `trust` 会匹配 `172.21.166.19-vsys_vrouteshzjhapcorsp_10005_1::trust`。
