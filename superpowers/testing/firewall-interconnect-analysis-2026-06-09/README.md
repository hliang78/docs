# 防火墙互联关系推断（2026-06-09）

- 节点数：17
- 接口地址数：42
- 路由数：160
- 高置信互联证据：31
- 中置信互联证据：170

## 推断规则

- high/shared_connected_subnet：两台防火墙接口 IP 位于同一较小网段。
- high/route_next_hop_peer_ip：某台防火墙路由下一跳精确命中另一台防火墙接口 IP。
- medium/route_next_hop_in_peer_subnet：下一跳落在另一台防火墙接口网段内，但不是该接口 IP，可能中间还有路由器/交换机 SVI。

## 设备对汇总
- FW-172.21.166.35-H3C-M9008-BORDER <-> VSYS-SPLIT-MGMT: high=1, medium=2, networks=172.21.166.0/24
- FW-172.31.131.106-DP-BEIDOU-BORDER <-> VSYS-172.31.131.5-default: high=1, medium=5, networks=172.31.131.0/24
- VSYS-SPLIT-ext_Internet9297 <-> VSYS-SPLIT-vsys_vroute_shzj_hap_bs_10014_1: high=1, medium=10, networks=172.21.251.4/30
- VSYS-SPLIT-ext_Internet9297 <-> VSYS-SPLIT-vsys_vrouteshzjhapbacku_10029_1: high=1, medium=10, networks=172.21.251.4/30
- VSYS-SPLIT-ext_Internet9297 <-> VSYS-SPLIT-vsys_vrouteshzjhapbsspp_10027_1: high=2, medium=14, networks=172.21.251.4/30; 2409:871e:8f01:20a2:300:0:ac15:fb00/126
- VSYS-SPLIT-ext_Internet9297 <-> VSYS-SPLIT-vsys_vrouteshzjhapcorsp_10005_1: high=1, medium=10, networks=172.21.251.4/30
- VSYS-SPLIT-ext_Internet9297 <-> VSYS-SPLIT-vsys_vrouteshzjhapcorsp_10023_1: high=1, medium=10, networks=172.21.251.4/30
- VSYS-SPLIT-ext_Internet9297 <-> VSYS-SPLIT-vsys_vrouteshzjhapiotpr_10033_1: high=1, medium=11, networks=172.21.251.4/30; 2409:871e:8f01:20a2:300:0:ac15:fb00/126
- VSYS-SPLIT-ext_Internet9297 <-> VSYS-SPLIT-vsys_vrouteshzjhapomcpr_10018_1: high=1, medium=12, networks=172.21.251.4/30; 2409:871e:8f01:20a2:300:0:ac15:fb00/126; 2409:871e:8f01:20a2:300:0:ac15:fb78/126
- VSYS-SPLIT-vsys_vroute_shzj_hap_bs_10014_1 <-> VSYS-SPLIT-vsys_vrouteshzjhapbacku_10029_1: high=1, medium=4, networks=172.21.251.4/30
- VSYS-SPLIT-vsys_vroute_shzj_hap_bs_10014_1 <-> VSYS-SPLIT-vsys_vrouteshzjhapbsspp_10027_1: high=1, medium=4, networks=172.21.251.4/30
- VSYS-SPLIT-vsys_vroute_shzj_hap_bs_10014_1 <-> VSYS-SPLIT-vsys_vrouteshzjhapcorsp_10005_1: high=1, medium=4, networks=172.21.251.4/30
- VSYS-SPLIT-vsys_vroute_shzj_hap_bs_10014_1 <-> VSYS-SPLIT-vsys_vrouteshzjhapcorsp_10023_1: high=1, medium=4, networks=172.21.251.4/30
- VSYS-SPLIT-vsys_vroute_shzj_hap_bs_10014_1 <-> VSYS-SPLIT-vsys_vrouteshzjhapiotpr_10033_1: high=1, medium=4, networks=172.21.251.4/30
- VSYS-SPLIT-vsys_vroute_shzj_hap_bs_10014_1 <-> VSYS-SPLIT-vsys_vrouteshzjhapomcpr_10018_1: high=1, medium=4, networks=172.21.251.4/30
- VSYS-SPLIT-vsys_vrouteshzjhapbacku_10029_1 <-> VSYS-SPLIT-vsys_vrouteshzjhapbsspp_10027_1: high=1, medium=4, networks=172.21.251.4/30
- VSYS-SPLIT-vsys_vrouteshzjhapbacku_10029_1 <-> VSYS-SPLIT-vsys_vrouteshzjhapcorsp_10005_1: high=1, medium=4, networks=172.21.251.4/30
- VSYS-SPLIT-vsys_vrouteshzjhapbacku_10029_1 <-> VSYS-SPLIT-vsys_vrouteshzjhapcorsp_10023_1: high=1, medium=4, networks=172.21.251.4/30
- VSYS-SPLIT-vsys_vrouteshzjhapbacku_10029_1 <-> VSYS-SPLIT-vsys_vrouteshzjhapiotpr_10033_1: high=1, medium=4, networks=172.21.251.4/30
- VSYS-SPLIT-vsys_vrouteshzjhapbacku_10029_1 <-> VSYS-SPLIT-vsys_vrouteshzjhapomcpr_10018_1: high=1, medium=4, networks=172.21.251.4/30
- VSYS-SPLIT-vsys_vrouteshzjhapbsspp_10027_1 <-> VSYS-SPLIT-vsys_vrouteshzjhapcorsp_10005_1: high=1, medium=4, networks=172.21.251.4/30
- VSYS-SPLIT-vsys_vrouteshzjhapbsspp_10027_1 <-> VSYS-SPLIT-vsys_vrouteshzjhapcorsp_10023_1: high=1, medium=4, networks=172.21.251.4/30
- VSYS-SPLIT-vsys_vrouteshzjhapbsspp_10027_1 <-> VSYS-SPLIT-vsys_vrouteshzjhapiotpr_10033_1: high=1, medium=5, networks=172.21.251.4/30; 2409:871e:8f01:20a2:300:0:ac15:fb00/126
- VSYS-SPLIT-vsys_vrouteshzjhapbsspp_10027_1 <-> VSYS-SPLIT-vsys_vrouteshzjhapomcpr_10018_1: high=1, medium=5, networks=172.21.251.4/30; 2409:871e:8f01:20a2:300:0:ac15:fb00/126
- VSYS-SPLIT-vsys_vrouteshzjhapcorsp_10005_1 <-> VSYS-SPLIT-vsys_vrouteshzjhapcorsp_10023_1: high=1, medium=4, networks=172.21.251.4/30
- VSYS-SPLIT-vsys_vrouteshzjhapcorsp_10005_1 <-> VSYS-SPLIT-vsys_vrouteshzjhapiotpr_10033_1: high=1, medium=4, networks=172.21.251.4/30
- VSYS-SPLIT-vsys_vrouteshzjhapcorsp_10005_1 <-> VSYS-SPLIT-vsys_vrouteshzjhapomcpr_10018_1: high=1, medium=4, networks=172.21.251.4/30
- VSYS-SPLIT-vsys_vrouteshzjhapcorsp_10023_1 <-> VSYS-SPLIT-vsys_vrouteshzjhapiotpr_10033_1: high=1, medium=4, networks=172.21.251.4/30
- VSYS-SPLIT-vsys_vrouteshzjhapcorsp_10023_1 <-> VSYS-SPLIT-vsys_vrouteshzjhapomcpr_10018_1: high=1, medium=4, networks=172.21.251.4/30
- VSYS-SPLIT-vsys_vrouteshzjhapiotpr_10033_1 <-> VSYS-SPLIT-vsys_vrouteshzjhapomcpr_10018_1: high=1, medium=4, networks=172.21.251.4/30
