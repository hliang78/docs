# EVE Mainline Topology Script Live Validation

验证时间：`2026-06-29`  
验证环境：`192.168.100.20` 上的 EVE-NG Community `6.2.0-4`

## 1. 目的

这份回执只回答一件事：

当前本地脚本 `scripts/eve_mainline_topology.py` 是否已经可以不依赖大模型 agent，直接通过 EVE API 完成一次真实 Lab 的 `plan -> apply -> destroy` 闭环。

补充：

当前它是否已经可以在不破坏现有主线 Lab 的前提下，先对主线执行一次只读 `preflight` 判定。

以及：

当目标 Lab 已经存在时，CLI `apply` 是否已经具备“默认拦截，显式确认后才允许 destructive 重建”的保护能力。

## 2. 本轮验证对象

本轮没有直接动现有主线 `oneops-network-mainline-v1`，而是使用一次性临时 Lab：

1. Lab 名：`oneops-cli-live-probe`
2. 节点：`PC1`、`PC2`
3. 网络：`1 x bridge`
4. 验证路径：CLI 入口直接执行 `apply`，随后执行 `destroy`

## 3. 实际执行命令

```bash
python3 scripts/eve_mainline_topology.py preflight --spec scripts/eve_mainline_topology.yaml
python3 scripts/eve_mainline_topology.py apply --spec /tmp/oneops-eve-cli-probe.yaml
python3 scripts/eve_mainline_topology.py destroy --spec /tmp/oneops-eve-cli-probe.yaml
```

补充验证命令：

```bash
python3 scripts/eve_mainline_topology.py apply --spec /tmp/oneops-cli-confirm-probe.yaml
python3 scripts/eve_mainline_topology.py apply --spec /tmp/oneops-cli-confirm-probe.yaml
python3 scripts/eve_mainline_topology.py apply \
  --spec /tmp/oneops-cli-confirm-probe.yaml \
  --confirm-destructive oneops-cli-confirm-probe
python3 scripts/eve_mainline_topology.py destroy --spec /tmp/oneops-cli-confirm-probe.yaml
```

### 3.1 主线只读 `preflight`

实际返回：

```json
{
  "status": "blocked",
  "checks": {
    "lab_exists": true,
    "destructive_apply_required": true,
    "spec_nodes": 10,
    "spec_links": 22,
    "current_nodes": 10,
    "current_networks": 22,
    "node_names_match_spec": true,
    "network_names_match_spec": false
  },
  "blockers": [
    "target-lab-exists"
  ],
  "warnings": [
    "current-network-set-differs-from-spec"
  ]
}
```

结论：

1. 主线 `preflight` 已经可以只读执行
2. 当前主线 `oneops-network-mainline-v1` 已存在，因此不应直接盲目执行 destructive `apply`
3. 当前 live 主线的节点集合与冻结 YAML 一致
4. 当前 live 主线的网络命名集合与冻结 YAML 不一致
5. 因此脚本已经能在真正执行前，把“需要人工确认”的风险显式报出来

### 3.2 destructive `apply` 确认闸门

使用一次性 Lab `oneops-cli-confirm-probe` 实测得到：

1. 第一次 `apply` 正常创建
2. 第二次 `apply` 在 Lab 已存在时，默认返回 `blocked`
3. 只有显式传入 `--confirm-destructive oneops-cli-confirm-probe` 后，才允许继续 destructive 重建
4. 随后 `destroy` 仍可正常完成

这说明当前 CLI 入口已经具备：

1. 默认保护现有 Lab
2. 明确的人为确认动作
3. 可审计的 destructive 入口

## 4. 实际结果

### 4.2 临时 Lab `apply`

实际返回：

```json
{
  "status": "ok",
  "lab": "oneops-cli-live-probe",
  "nodes": {
    "PC1": {
      "logical_id": 11,
      "eve_id": 1,
      "console": "telnet://192.168.100.20:32769"
    },
    "PC2": {
      "logical_id": 12,
      "eve_id": 2,
      "console": "telnet://192.168.100.20:32770"
    }
  },
  "networks": {
    "L01": {
      "id": 1,
      "name": "PC1-PC2"
    }
  },
  "warnings": []
}
```

结论：

1. CLI 入口已能真实登录 EVE API
2. 已能新建 Lab
3. 已能新建节点
4. 已能新建网络
5. 已能挂接接口
6. 已能完成创建后回读校验
7. 已能启动节点并输出控制台信息

### 4.3 临时 Lab `destroy`

实际返回：

```json
{
  "status": "destroyed",
  "lab": "oneops-cli-live-probe",
  "warnings": []
}
```

结论：

1. 已能停机
2. 已能断开接口
3. 已能删除网络
4. 已能删除节点
5. 已能删除 Lab

## 5. 本轮确认的真实边界

### 5.1 EVE 运行时节点 ID 不可预设

即使在创建节点时传入了逻辑 ID，EVE 仍会按 Lab 内顺序分配自己的运行时节点 ID。  
因此脚本中 YAML 的 `id` 现在只作为 OneOps 逻辑设备 ID 使用，不再假设它等于 EVE 节点 ID。

### 5.2 API 创建 `bridge` 时应统一使用 `visibility: 1`

本轮最小探测已复现：

1. `POST /api/labs/<lab>/networks` 返回 `201 success`
2. 但如果 `bridge` 使用 `visibility: 0`
3. 紧接着 `GET /api/labs/<lab>/networks` 可能读不到这条网络

因此当前脚本统一将 API 创建网络的 `visibility` 固定为 `1`。

### 5.3 接口断线必须使用空字符串，而不是 `0`

本轮最小探测已复现：

1. `PUT /api/labs/<lab>/nodes/<id>/interfaces` 传 `{ "0": "0" }` 会报无效网络 ID
2. 传 `{ "0": "" }` 才能正确断线
3. 回读后 `network_id` 为 `0`

因此脚本已把“挂线”和“断线”拆成两个不同动作：

1. `attach_interface`
2. `detach_interface`

### 5.4 非登录接口必须带 `X-Requested-With: XMLHttpRequest`

在当前环境中：

1. 登录接口可直接成功
2. 但后续普通 API 请求如果不带 `X-Requested-With: XMLHttpRequest`
3. 可能被 EVE 判定为未登录

因此 live client 已固定携带这个头。

### 5.5 `iol` 接口需要做“逻辑口 -> EVE 内部接口 ID”映射

本轮主线实跑又确认了一个 EVE 真实边界：

1. `qemu` 节点的接口回读通常是数组
2. 但 `iol` 节点的接口回读是一个对象
3. 其中键值不是顺序 `0,1,2,3...`
4. 当前环境里会出现类似 `0,16,32,48,1,17...` 这样的内部接口 ID

因此：

1. YAML 中的接口编号继续表示“第几个逻辑口”
2. 脚本在真正 `attach` 前，必须先读取接口表
3. 再把逻辑口序号换算成 EVE 内部接口 ID

这一步已经被固化进当前实现，否则主线里的 `GW/ACC1/ACC2` 挂线会失败。

### 5.6 “link 语义”在当前 EVE 上需要通过独占 network 来表达

本轮继续核实了一个容易混淆的边界：

1. `GET /api/labs/<lab>/links` 可以读出现有链路视图
2. 但当前环境下没有找到已验证可用的 `POST /api/labs/<lab>/links` 建链写接口
3. EVE 前后端实际可写模型仍然是 `POST /api/labs/<lab>/networks`
4. 前端“连接两个节点”的实际动作也是：
   `POST /networks(type=bridge)` + 两次 `PUT /nodes/<id>/interfaces`
5. 后端 `api_topology.php` 明确规定：
   当 `count==2 && visibility==0 && 非cloud` 时，拓扑输出会从 `node -> network` 折叠成真正的 `node -> node`

因此当前可交付的正确说法是：

1. 主线采用的是点对点 `link` 语义
2. 落地形式是“每条链路独占一个 `network type=bridge`”
3. 但最终应切成 `visibility=0`
4. 这样 EVE 画布会显示成真正的 node-to-node link
5. 不是很多设备共享同一个 bridge

为避免再次混淆，脚本已新增只读校验：

1. `preflight` 会计算每条 network 当前实际挂了哪些节点接口
2. 如果某条 network 被意外挂了额外端点
3. 就会返回 `shared-network-detected:*`
4. 如果某条 P2P bridge 仍然是可见状态
5. 就会返回 `visible-p2p-network:*`
6. 当前主线实测结果为 `exclusive_link_semantics: true`
7. 当前主线实测结果为 `hidden_p2p_visual_mode: true`

### 5.7 旧 Lab 残留会造成 console 端口串线

`2026-06-30` 又补做了一轮真实环境核查，确认了一个更危险的边界：

1. `oneops-network-mainline-v1` 与 `oneops-gateway-switch-20260627-082039.unl` 同时处于运行态
2. 两个 Lab 都声称自己在使用 `32769-32777`
3. 其中旧 Lab 的真实进程仍然监听这些端口
4. 因此即使主线 `.unl` 的节点名、网络名、独占链路语义都正确，Web console 仍可能连到旧设备

这说明：

1. “拓扑结构正确”不等于“console 一定正确”
2. 主线重建前必须额外检查其他运行中 Lab 的 console 端口占用
3. 否则会出现非常隐蔽的错连现象

基于这个边界，脚本已新增：

1. `checks.console_ports_exclusive`
2. `current.console_port_conflicts`
3. `blockers` 中的 `conflicting-running-labs`

当这类冲突存在时，即使传了 `--confirm-destructive <lab-name>`，CLI `apply` 也会继续阻断。

### 5.8 旧 Lab 清理后的目标状态

在 `2026-06-30` 后续清理中，已执行以下动作：

1. 停止并删除旧 Lab `oneops-gateway-switch-20260627-082039`
2. 清掉该 Lab 残留占用的 console 监听进程
3. 复核 `/opt/unetlab/tmp`，确认只剩当前主线 Lab 的运行目录
4. 将当前主线 `oneops-network-mainline-v1` 的全部 10 台节点恢复到运行态
5. 将主线 21 条点对点 `bridge` 全部切换为 `visibility=0`

清理完成后的验证结果是：

1. `preflight` 仍然返回 `blocked`
2. 但唯一 blocker 只剩 `target-lab-exists`
3. `console_ports_exclusive: true`
4. `hidden_p2p_visual_mode: true`
5. `exclusive_link_semantics: true`
6. `32769-32778` 全部由当前主线节点占用

这说明当前环境已经从“结构正确但 console 可能串线”的危险状态，恢复到了“结构正确且 console 独占”的可继续测试状态。

## 6. 当前结论

截至 `2026-06-29`，`scripts/eve_mainline_topology.py` 已经具备“作为 OneOps 第一阶段真实设备测试底座脚本”的最小可用能力：

1. 能独立完成 `plan / preflight / apply / destroy`
2. 能对现有主线 Lab 做只读安全判定
3. 能在真实 EVE 环境里完成 destructive `apply` 的确认闸门验证
4. 能在真实 EVE 环境里完成一次性临时 Lab 的创建与销毁闭环
5. 能在真实主线场景中正确处理 `iol` 接口内部 ID 映射
6. 已把本轮踩到的几个关键 API 边界固化进实现
7. 已能在真实环境中识别“旧 Lab 占用相同 console 端口”的错连风险

但它目前仍然只是“拓扑底座脚本”，还没有进入下面这些更高层能力：

1. 设备初始化模板下发
2. SSH / SNMP 就绪验证
3. OBS `controller + agent` 部署
4. 主线设备采集、监控、拓扑联动校验
5. 宿主机残留 `tap/tmp` 清理

## 7. 下一步最顺动作

基于这份回执，下一步最顺的推进方式是：

1. 先把 `oneops-network-mainline-v1` 的真实主线拓扑生成也接到这套脚本上
2. 但首次不要直接对现网主线 Lab 做 destructive apply
3. 现在“人工确认后才允许主线 apply”的切换规则已经落地
4. 下一步可以继续补“主线网络命名对齐”或“主线初始化模板下发”
