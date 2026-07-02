# OBS `controller + agent` 部署前置检查清单

更新时间：2026-06-29  
适用环境：`192.168.100.20` 上的 EVE-NG Community `6.2.0-4`

## 1. 目的

这份清单只回答一件事：

在第一阶段网络设备主线里，`OBS` 是否已经具备承载 `controller + agent` 的前置条件。

它不是部署手册，也不替代后续监控回执。
它的作用是把“部署前必须先确认什么”固定下来，避免现场一边装、一边猜环境。

## 2. 适用对象

本清单固定只适用于：

1. 节点名称：`OBS`
2. 节点角色：观测服务器
3. 当前管理地址：`172.32.2.71/24`
4. 管理网关：`172.32.2.254`
5. 固定资源规格：`8 vCPU / 16G RAM`

## 3. 部署前门禁

只有下面 5 组门禁都通过，才进入 `controller + agent` 实际部署。

### 3.1 节点规格门禁

必须确认：

1. `OBS` 当前节点规格仍是 `8 vCPU / 16G RAM`
2. `OBS` 没有被误替换成普通轻量业务服务器规格
3. `OBS` 仍然是单管理口模型，不额外引入观测网口

最小核对项：

```text
EVE 节点 CPU
EVE 节点 Memory
EVE 节点接口数
```

### 3.2 系统基础门禁

必须确认：

1. 主机名固定为 `OBS`
2. 管理口地址固定为 `172.32.2.71/24`
3. 默认路由固定指向 `172.32.2.254`
4. `admin/admin@123` 可稳定登录
5. `sudo` 可正常使用

最小核对项：

```text
hostname
ip -br a
ip route
printf 'admin@123\n' | sudo -S whoami
```

### 3.3 管理面连通性门禁

必须确认：

1. `OBS -> GW` 管理地址可达
2. `OBS -> ACC1/ACC2/R1/R2/R3/R4/S1/S2` 管理地址可达
3. `OBS` 到全体受管节点都只经过管理平面

最小核对项：

```text
ping -c 2 172.32.2.254
ping -c 2 172.32.2.10
ping -c 2 172.32.2.20
ping -c 2 172.32.2.31
ping -c 2 172.32.2.32
ping -c 2 172.32.2.33
ping -c 2 172.32.2.34
ping -c 2 172.32.2.61
ping -c 2 172.32.2.62
```

### 3.4 接入入口门禁

必须确认：

1. `OBS` 本机 `SSH` 已稳定
2. `OBS` 本机 `SNMP v2c` 已稳定
3. 后续若 `controller + agent` 依赖远程登录或指标回读，当前入口已具备最小可用性

最小核对项：

```text
systemctl is-active ssh
systemctl is-active snmpd
ss -lun | grep :161
snmpwalk -v2c -c admin@123 172.32.2.71 1.3.6.1.2.1.1.1.0
```

### 3.5 软件源与安装路径门禁

必须确认：

1. 当前 Ubuntu 20.04 环境没有可直接依赖的公网 DNS / 在线软件源时，不能把在线安装当默认前提
2. 若部署依赖额外软件包，必须先明确“在线安装”还是“离线分发”
3. 若采用离线路径，离线包来源、临时服务端口和落盘目录都要先固定

当前已知现实约束：

1. `OBS` 所在主线环境不能默认假设能直接访问公网仓库
2. `snmpd` 已通过离线包路径成功落地
3. `controller + agent` 若有额外依赖，也应优先沿用“先确认安装路径，再执行部署”的方法

## 4. 推荐前置检查顺序

建议顺序固定为：

1. 先核对 EVE 节点规格
2. 再核对 `OBS` 主机基础配置
3. 再核对到全部节点的管理面连通性
4. 再核对 `SSH + SNMP` 本机入口
5. 最后确认部署依赖的安装路径

这样做的原因是：

1. 如果规格不对，后面所有部署结果都不应直接复用
2. 如果系统基础不对，部署问题会和初始化问题混在一起
3. 如果管理面不通，后续监控链问题会失真
4. 如果安装路径没先说明，现场很容易把“依赖下载失败”误判成“平台部署失败”

## 5. 通过标准

`OBS` 只有满足下面 6 条，才算通过前置检查：

1. 资源规格 = `8 vCPU / 16G RAM`
2. 主机名、管理地址、默认路由正确
3. `admin/admin@123` 与 `sudo` 可用
4. 到 `GW/ACC1/ACC2/R1/R2/R3/R4/S1/S2` 的管理面连通
5. 本机 `SSH` 与 `SNMP v2c` 可用
6. 部署依赖的安装路径已明确

## 6. 不通过时的优先归因

如果前置检查失败，优先按下面口径归因：

1. 规格不对：环境准备问题
2. 管理地址、路由或主机名不对：初始化问题
3. 管理面不通：拓扑或地址面问题
4. `SSH` / `SNMP` 不通：服务器标准化问题
5. 软件包安装路径不明：部署前准备问题

## 7. 与主线文档的关系

这份清单服务于以下主线文档：

1. [EVE-NG Linux Server 标准操作手册](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-linux-server-standard-operation.md)
2. [第一阶段网络设备主线地址与端口分配](/Users/huangliang/project/OneOPS-ALL/docs/testing/phase1-network-mainline-addressing-and-port-map.md)
3. [第一阶段网络设备主线标准场景](/Users/huangliang/project/OneOPS-ALL/docs/testing/phase1-network-mainline-standard-scenario.md)
4. [第一阶段网络设备主线执行 Runbook](/Users/huangliang/project/OneOPS-ALL/docs/testing/phase1-network-mainline-execution-runbook.md)

## 8. 当前结论

当前这份清单已经把 `OBS` 进入 `controller + agent` 部署前最容易漏掉的前置项固定下来了：

1. `OBS` 是高规格观测节点，不是普通业务服务器
2. 只要这张清单没打勾完成，就不要把后续部署失败直接归因到 OneOps
3. 后续部署时，应先回写这份清单，再进入正式部署和监控回执
