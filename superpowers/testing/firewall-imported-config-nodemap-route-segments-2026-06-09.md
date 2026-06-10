# Firewall Imported Config NodeMap Route Segments

Source: `/OneOPS/ctrlhub/controller/pkg/nodemap/tests/firewall/testdata/imported-configs`
Parser: `nodemap.NewNodeMapFromNetwork` + `AddressTable.ToSliceMap()`

| File | Platform | Node | Route rows | Unique destination segments | IPv4 | IPv6 | Examples |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| `172.21.166.19-SH-HAP-ZJIDC-CORE-FW-HW-E8000E-X8-120260527_162627.log` | `USG/HuaWei` | `SH-HAP-ZJIDC-CORE-FW-HW-E8000E-X8-1` | 119 | 59 | 113 | 6 | `0.0.0.0/0, 10.81.0.0/22, 10.81.100.0/22, 10.81.104.0/22, 10.81.12.0/22, 10.81.4.0/22, 10.81.8.0/22, 172.21.128.102/32, ...` |
| `172.21.166.35-SH-HAP-ZJIDC-BORDER-FW-H3C-M9008-1&220260527_162629.log` | `SecPath` | `SH-HAP-ZJIDC-BORDER-FW-H3C-M9008-1&2` | 21 | 20 | 21 | 0 | `0.0.0.0/0, 10.150.161.11/32, 10.150.161.125/32, 10.150.161.173/32, 10.150.161.185/32, 10.25.35.0/24, 10.25.50.0/24, 10.25.51.0/24, ...` |
| `172.22.166.14-SH-HAP-ZQIDC-CMNET-FW-H3C-M9016-220260527_162631.log` | `SecPath` | `SH-HAP-ZQIDC-CMNET-FW-H3C-M9016-2` | 4 | 2 | 2 | 2 | `0.0.0.0/0, ::/0` |
| `172.31.131.106-北斗短报文专用边界防火墙-0120260527_162634.log` | `Dptech` | `SH-CMSR-ZJIDC-BEIDOU-BORDER-DP-FW1000-1` | 1 | 1 | 1 | 0 | `0.0.0.0/0` |
| `172.31.131.5-20260527_162629.log` | `USG/HuaWei` | `SH-CMSR-ZJIDC_3F_G04_2U-ISP-FW-HW_E8KE-X16-1` | 4 | 4 | 4 | 0 | `0.0.0.0/0, 172.31.192.0/24, 172.31.192.244/32, 172.40.50.0/24` |
| `172.31.188.11120260527_162634.log` | `USG/HuaWei` | `ZQ01-mgt-fw-01-E9000E-F55-12-17-05U` | 9 | 8 | 6 | 3 | `0.0.0.0/0, 10.175.1.0/24, 100.64.0.0/17, 172.31.184.0/22, 172.31.189.0/24, 2409:8c1e:68e0::/96, 2409:8c1e:68e0::ff:0:0/96, ::/0` |

Full detail CSV: `firewall-imported-config-nodemap-route-segments-2026-06-09.csv`

Columns: `file`, `sample`, `platform`, `parser_mode`, `node`, `family`, `vrf`, `destination_cidr`, `next_hop`, `out_interface`, `zone`, `connected`, `default_gw`.

Note: this file uses parsed route-table semantics, so it can include connected/default route entries that are not literal `route-static` command lines.
