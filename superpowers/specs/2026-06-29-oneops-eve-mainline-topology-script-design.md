# OneOps EVE Mainline Topology Script Design

## Goal

把当前第一阶段网络设备主线测试拓扑，固化成一个不依赖大模型 agent 的本地可执行脚本。

第一版目标非常明确：

1. 在本地仓库里直接执行
2. 通过 EVE API 连接 `192.168.100.20`
3. 对当前主线 Lab 执行：
   - 同名拓扑安全删除
   - 重建拓扑
   - 启动节点
4. 输出可读摘要和可机读结果

这份设计不追求“通用 EVE 编排平台”，而是先做成“当前主线拓扑重建器”。

## Scope

本次范围包含：

1. 提供一个本地 CLI 脚本
2. 把当前 `oneops-network-mainline-v1` 主线拓扑冻结成 YAML 清单
3. 通过 EVE API 创建 Lab、节点、网络和链路
4. 支持 `plan / apply / destroy` 三个命令
5. 在执行过程中做必要的回读校验
6. 在 `apply` 成功后输出节点 ID、网络 ID、控制台端口

本次范围不包含：

1. 设备初始化配置下发
2. 设备管理地址、SSH、SNMP、OSPF、VRF 等配置验证
3. `OBS controller + agent` 部署
4. 宿主机孤儿 `tap` 口或 `tmp` 覆盖目录的自动清理
5. 任意新场景的通用自动推导

## User-Facing Interface

### Script files

第一版固定新增以下文件：

1. `scripts/eve_mainline_topology.py`
   CLI 入口
2. `scripts/eve_mainline_topology_lib.py`
   EVE API 客户端、拓扑解析和执行逻辑
3. `scripts/eve_mainline_topology.yaml`
   当前主线拓扑冻结清单

### Runtime commands

第一版固定提供 3 个命令：

1. `plan`
   只读取 YAML，并打印将要创建的 Lab、节点、网络和链路，不对 EVE 写入
2. `apply`
   若同名 Lab 已存在，则先安全删除，再重建拓扑并启动节点
3. `destroy`
   按安全顺序删除当前主线 Lab

推荐运行方式：

```bash
python3 scripts/eve_mainline_topology.py plan
python3 scripts/eve_mainline_topology.py apply
python3 scripts/eve_mainline_topology.py destroy
```

### Connection settings

连接信息默认从环境变量读取：

1. `EVE_HOST`
2. `EVE_USER`
3. `EVE_PASS`

第一版默认值直接兼容当前环境：

1. `EVE_HOST = 192.168.100.20`
2. `EVE_USER = admin`
3. `EVE_PASS = eve`

### Safety guard

第一版增加一个保守保护：

1. 默认只允许操作 `oneops-` 前缀的 Lab
2. 若用户指定其它 Lab 名，必须显式传 `--force`

## Architecture

### Design choice

第一版采用：

1. `Python CLI`
2. `YAML` 作为拓扑冻结清单
3. EVE API 作为唯一写入入口

选择这条路线的原因：

1. 本地已有 `requests` 和 `PyYAML`，第一版不需要额外引入重依赖
2. YAML 更适合承载“冻结真值”，后续要增加第二条场景时不需要先改代码结构
3. 相比 `shell + curl`，Python 更容易把错误处理、回读校验和摘要输出做清楚
4. 相比直接生成 `.unl XML`，EVE API 路径更贴近当前已经验证过的生命周期动作

### Internal modules

`scripts/eve_mainline_topology_lib.py` 建议拆成下面几个职责块：

1. `EveClient`
   - 登录 EVE API
   - 统一发请求
   - 统一处理返回值和错误
2. `TopologySpec`
   - 读取 YAML
   - 解析 Lab、节点、链路定义
   - 负责基础字段校验
3. `TopologyPlanner`
   - 把 YAML 转成“待创建节点 / 待创建网络 / 待挂线关系”
4. `TopologyApplier`
   - 执行创建
   - 执行挂线
   - 执行启动
   - 执行回读校验
5. `TopologyDestroyer`
   - 按安全顺序停机、断线、删网络、删节点、删 Lab

这样拆的目的是让第一版虽然只服务当前主线，但内部结构已经能承受后续扩展。

## Topology Spec Format

### YAML top-level structure

第一版 YAML 固定包含 3 个主块：

1. `lab`
2. `nodes`
3. `links`

示意结构：

```yaml
lab:
  path: /opt/unetlab/labs/oneops-network-mainline-v1.unl
  name: oneops-network-mainline-v1
  description: OneOps phase1 mainline topology

nodes:
  - name: GW
    id: 101
    template: iol
    type: iol
    ethernet: 5
    cpu: 1
    ram: 1024
    left: 120
    top: 80
  - name: OBS
    id: 110
    template: linux
    type: qemu
    image: linux-ubuntu-server-20.04
    ethernet: 1
    cpu: 8
    ram: 16384
    left: 760
    top: 80

links:
  - id: L01
    type: pnet0
    name: GW-pnet0
    endpoints:
      - node: GW
        interface: 0
      - pnet: 0
  - id: L02
    type: bridge
    name: GW-ACC1-MGT
    endpoints:
      - node: GW
        interface: 1
      - node: ACC1
        interface: 0
```

### Nodes block rules

`nodes` 中保留 EVE 创建节点所需的真实参数，不把模板差异硬编码进逻辑。

第一版固定要求：

1. 每个节点必须有 `name`
2. 每个节点必须有固定高位 `id`
3. 每个节点必须声明 `template`
4. 每个节点必须声明 `type`
5. 每个节点必须声明 `ethernet`
6. 坐标 `left/top` 必须显式写入，避免脚本隐式决定布局
7. `OBS` 的 `cpu=8`、`ram=16384` 直接写进 YAML，不靠文档提醒

### Links block rules

`links` 直接表达双端真值，不在代码里硬编码 `L01-L22` 逻辑。

第一版固定要求：

1. 每条链路必须有 `id`
2. 每条链路必须有 `type`
3. 每条链路必须有 `name`
4. 每条链路必须有 `endpoints`
5. `endpoints` 只允许两端
6. 节点接口统一使用 EVE API 的接口索引，不混用 CLI 接口名

链路类型第一版只支持：

1. `bridge`
2. `pnet0`

## Execution Flow

### `plan`

`plan` 只做静态解析，不写 EVE。

固定流程：

1. 读取 YAML
2. 校验字段完整性
3. 计算将要创建的节点、网络、挂线动作
4. 输出人可读摘要
5. 输出 JSON 规划结果

### `apply`

`apply` 固定流程：

1. 读取 YAML
2. 检查同名 Lab 是否存在
3. 若存在，先调用安全删除链路
4. 创建 Lab
5. 按 YAML 中固定高位节点 ID 创建设备
6. 为每条链路创建网络
7. 把节点接口挂到对应网络
8. 回读节点、网络和接口，确认结果与 YAML 一致
9. 启动节点
10. 输出创建摘要

### `destroy`

`destroy` 固定流程：

1. 定位目标 Lab
2. 逐节点发停机动作
3. 逐接口断线
4. 删除网络
5. 删除节点
6. 删除 Lab
7. 输出清理摘要

第一版只做 API 侧安全删除。
若 API 删除后宿主机仍残留孤儿 `tap/tmp`，脚本只打印提示，不自动做宿主机清理。

## Required Read-Back Validation

第一版必须固化下面 5 条回读校验，不能只信 API 返回码：

1. `Lab` 创建后，必须能被 `GET /api/labs/<lab>` 回读
2. `network` 创建后，必须能在 `GET /api/labs/<lab>/networks` 中真实出现
3. 每次挂线后，必须回读两端接口，确认 `network_id` 一致
4. 所有节点创建完后，节点名到节点 ID 的映射必须和 YAML 完全一致
5. 启动后必须输出控制台端口摘要，供人工二次验证

如果任何一条校验不通过，第一版都应立即停止后续步骤。

## Error Handling

第一版固定采用“失败即停、保留现场、明确归因”的策略。

### `apply` error policy

1. `Lab` 创建失败：立即退出
2. 单个 `node` 创建失败：立即退出，并输出已成功创建节点
3. `network` 创建后回读不到：立即退出，不继续挂线
4. 单条 `link` 挂线后两端回读不一致：立即退出，并打印两端详情
5. 节点启动失败：不回滚已创建拓扑，只报告“拓扑已建成但启动未完成”

### `destroy` error policy

1. 某个停机动作失败：记录失败并继续尝试后续节点
2. 某个网络或节点删除失败：记录失败并继续
3. 最终如果存在残留项，命令返回非 `0`

这样做的原因是：

1. 删除类动作更适合“尽量清”
2. 创建类动作更适合“尽快停”
3. 启动失败不应掩盖已经成功建好的拓扑现场

## Output Contract

第一版输出分两层：

### Human-readable summary

示例：

```text
LAB created: oneops-network-mainline-v1
NODE created: GW -> 101
LINK attached: L02 -> GW:1 <-> ACC1:0
NODE started: R1 -> console 32872
```

### Machine-readable JSON summary

在命令结尾固定打印 JSON：

```json
{
  "lab": "oneops-network-mainline-v1",
  "status": "ok",
  "nodes": {
    "GW": {"id": 101, "console": 32869},
    "R1": {"id": 104, "console": 32872}
  },
  "networks": {
    "L02": {"id": 1, "type": "bridge"}
  },
  "warnings": []
}
```

这样后续若要接 OneOps、CI 或别的自动化入口，不需要重写解析逻辑。

## Current Mainline Mapping

第一版只服务当前冻结主线。

节点范围固定为：

1. `GW`
2. `ACC1`
3. `ACC2`
4. `R1`
5. `R2`
6. `R3`
7. `R4`
8. `S1`
9. `S2`
10. `OBS`

链路真值固定直接复用：

1. [第一阶段网络设备主线地址与端口分配](/Users/huangliang/project/OneOPS-ALL/docs/testing/phase1-network-mainline-addressing-and-port-map.md)
2. [第一阶段网络设备主线标准场景](/Users/huangliang/project/OneOPS-ALL/docs/testing/phase1-network-mainline-standard-scenario.md)
3. [EVE-NG 拓扑生命周期操作验证记录](/Users/huangliang/project/OneOPS-ALL/docs/testing/eve-ng-topology-lifecycle-validation.md)

## Testing Strategy

第一版不做 TDD 级别的全量模拟，但至少需要下面两层验证：

1. 本地静态验证
   - YAML 解析
   - 链路端点完整性
   - 节点名唯一
   - 节点 ID 唯一
2. EVE 实机验证
   - `plan` 可输出正确摘要
   - `apply` 能完整重建当前主线
   - `destroy` 能安全删除同名主线

第一版成功标准不是“所有设备都启动且配置完成”，而是：

1. 拓扑结构可稳定重建
2. 节点、网络、挂线关系与冻结表一致
3. 节点启动动作已下发且控制台端口摘要可回读

## Non-Goals

第一版明确不做：

1. 设备初始化下发
2. SSH 登录验证
3. SNMP 验证
4. OSPF 和业务地址配置验证
5. `OBS controller + agent` 部署
6. 通用多场景推导
7. 宿主机孤儿 `tap/tmp` 自动清理

## Recommendation

这套脚本的最合适定位是：

1. 主线拓扑重建器
2. 当前主线测试的可重复底座工具
3. 后续更大编排能力的前置基础

不建议第一版就把它做成“通用 EVE 编排平台”。
先把当前主线打实，后面再沿着 YAML 清单能力扩展到第二条、第三条场景。

## Immediate Next Step

设计确认后，下一步应直接进入实现计划，产出：

1. `scripts/eve_mainline_topology.py`
2. `scripts/eve_mainline_topology_lib.py`
3. `scripts/eve_mainline_topology.yaml`
4. 一份最小使用说明
