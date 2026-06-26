# OneOPS Platform Testing Baseline Design

## Goal

为 `OneOPS + OneOPS-UI` 建立一套共享、系统化、可逐步扩展的平台测试基线，不再停留在“若干冒烟脚本”层面，而是形成：

- 平台统一测试语言与风险分级
- 统一的覆盖矩阵与证据标准
- 可执行的 `PR core / nightly / manual` 分层门禁
- 可供网络设备、服务器设备、防火墙设备等领域共同使用的文档与协作框架
- Phase 1 可在 `10 分钟内` 卡住关键回归的核心门禁集

本设计首先服务平台当前最关键的主链路：

`设备入库 -> 采集 -> 监控下发 -> 读模型 / 运行态收敛`

## Scope

### In Scope

- 仓库范围：
  - `OneOPS`
  - `OneOPS-UI`
- Phase 1 工作范围：
  - 平台测试总纲
  - 领域附录骨架
  - 平台总覆盖矩阵
  - 首批 P0/P1 场景识别
  - `GitHub private + self-hosted runner` 的 `PR core` 核心门禁集
  - 统一证据标准与问题沉淀机制
- 首批业务主线：
  - 设备入库
  - 采集
  - 监控

### Out Of Scope

- `agent`、`dagengine`、`teleabs`、`protocol` 等多仓生态的全面纳入
- 全量真实设备门禁
- 大规模性能与容量压测的完整落地
- 追求一次性高覆盖率

这些内容作为 Phase 2+ 的扩展方向，通过本设计建立的框架继续推进。

## Why Now

平台当前已经进入“功能趋稳、需要系统验证和持续收敛”的阶段，核心风险集中在以下三类：

1. AI 累积开发形成了大量功能代码，需要有结构地梳理和验证，而不是靠零散人工经验判断。
2. 设备入库、采集、监控推送是平台核心价值链，需要达到“100% 能采集/能监控，或命中清晰边界”的状态。
3. 后续性能、规模和真实环境验证，都需要一套统一的测试语言、证据口径和门禁底座，否则无法持续推进。

仓库中已经存在不少可复用测试资产：

- `OneOPS` 后端已有大量单元测试与部分 fixture 测试
- `OneOPS-UI` 已有大量 smoke 脚本
- `docs/superpowers/testing` 已积累 `device v2` 的 harnessed integration 与真实联调资产
- `OneOPS/tools/device_v2_envtest` 已具备远程环境回放与报告雏形

当前问题不是“从零做测试”，而是“缺少统一基线，把现有资产组织成一个可执行系统”。

## Success Criteria

Phase 1 的完成标准定义为：

1. 有一份平台级共享总纲，统一术语、风险分级、测试分层、证据判定和门禁规则。
2. 有三份领域附录骨架，供网络设备、服务器设备、防火墙设备并行推进准备工作。
3. 有一张平台总覆盖矩阵，能看清“已覆盖、缺失、边界、待补”。
4. 有一套 `10 分钟内` 的 `PR core` 核心集，真实挂到 `GitHub private + self-hosted runner` 的 PR 流程上。
5. 有统一证据目录与结果状态，不再让“测过了但说不清测了什么”继续发生。
6. 首批高风险 `P0/P1` 场景真实纳入基线，而不是只写规范不补测试。

## Design Principles

### 1. Risk-First, Not Script-First

测试基线按风险暴露面组织，而不是按脚本文件堆叠。

### 2. Shared Framework, Domain Appendices

平台共用规则放在总纲，设备领域特殊性放在附录，避免“一份大文档写尽一切”或“每个领域各写一套语言”。

### 3. Evidence Before Claims

没有标准化证据的“通过”不算通过。任何 P0/P1 结论都必须能指出结果证据和真值证据来源。

### 4. Layered Validation

不同测试类型进入不同层级：

- `PR core` 保护主干
- `nightly` 承担更重的扩展回归
- `manual / real-world` 负责真实性背书

### 5. Boundaries Are First-Class Outcomes

“当前不支持但边界清晰”是合法结果；“无法采集/无法监控且无法解释”不是合法结果。

### 6. Reuse Existing Assets First

优先收编已有单测、smoke、fixture、envtest 和真实联调资产，而不是重造平行体系。

## Documentation Architecture

平台测试基线文档采用 `1 份总纲 + N 份领域附录 + 运行证据目录` 的结构。

### Platform-Level Main Document

主文档承载所有共用规则，至少覆盖：

- 目标与范围
- 统一术语
- 风险分级
- 测试分层
- 门禁分层
- 证据标准
- 覆盖矩阵方法
- 新功能接入要求
- 例外机制

### Domain Appendices

首批附录建议包括：

- 网络设备测试附录
- 服务器设备测试附录
- 防火墙设备测试附录
- 设备入库/采集/监控主链路附录
- 性能与规模测试附录

Phase 1 至少需要先落网络设备、服务器设备、防火墙设备三份附录骨架。

### Evidence And Reporting Directories

建议统一沉淀到平台测试基线目录下，至少能够稳定归档：

- `coverage-matrix`
- `core-suite-reports`
- `nightly-reports`
- `real-world-evidence`
- `perf-baselines`
- `findings-and-boundaries`

## Platform Coverage Matrix

覆盖矩阵不按“脚本清单”组织，而按风险维度组织。平台统一采用至少 7 个维度：

1. `设备域`
   - 网络设备
   - 服务器设备
   - 防火墙设备
2. `业务链路`
   - 入库
   - 采集
   - 存储决策
   - 同步
   - 监控下发
   - 运行态观察
   - 读模型展示
3. `入口来源`
   - 外部入口 / ZB
   - 页面导入
   - 页面单设备操作
   - 批量任务
   - 系统内部重试 / 恢复
4. `能力与协议`
   - SNMP
   - SSH
   - API
   - Telnet
   - IPMI
   - 日志采集
   - 被动监控
   - 主动探测
5. `状态类型`
   - 正常成功
   - 部分成功
   - 阻断
   - 失败
   - 回滚
   - 恢复后成功
   - 陈旧状态污染
6. `数据真值层`
   - 源数据
   - 投影数据
   - 读模型
   - agent runtime
   - 监控指标资产
   - 外部回调
7. `规模与负载`
   - 单设备
   - 批量设备
   - 单 agent
   - 多 agent
   - 大量任务
   - 大量监控目标

### Matrix Outputs

矩阵至少产出两类视图：

- `平台总覆盖矩阵`
  - 横向显示领域、链路、协议、状态、真值层覆盖情况
- `领域作战矩阵`
  - 纵向指导每个领域下一步补哪些夹具、哪些样本、哪些真实验证

## Test Layering

平台统一分为 5 层测试：

### L1 Unit / Pure Logic

覆盖解析、映射、状态收敛、聚合、错误码、契约转换等快且稳定的逻辑。

### L2 Fixture Integration

用固定夹具验证主链路关键节点，是 Phase 1 的核心层。

### L3 Local Integration

拉起本地依赖或轻量服务，验证多组件协同行为。

### L4 Workflow / Scenario Validation

强调端到端页面与业务流，但仍以可重复、可控为前提。

### L5 Real-World Validation

负责真实设备、真实协议、真实监控和真实运行态背书。

## Gate Layering

测试层和门禁层分开定义。平台统一采用 3 级门禁：

### PR Core

- 触发方式：PR
- 环境：`GitHub private + 单台 self-hosted runner`
- 时长目标：`10 分钟内`
- 内容：
  - `L1 + L2 + 少量 L4`
- 目标：
  - 强力保护主干，挡住关键回归

### Nightly Regression

- 触发方式：定时或手动
- 内容：
  - 扩展 `L2 + L3 + L4`
- 目标：
  - 承接更重、更广的组合验证

### Manual / Real-World

- 触发方式：里程碑、关键修复、重要版本
- 内容：
  - `L5` 真实环境验证
- 目标：
  - 为离线与本地结果提供真实性校正

## Phase 1 Core Scope

Phase 1 的首批核心集围绕一条主线展开：

`设备入库 -> 采集 -> 监控下发 -> 读模型 / 运行态收敛`

建议拆成 6 个用例族：

### 1. Entry Consistency

不同入口进入同一设备主链时，关键结果应一致。

至少覆盖：

- 外部入口 / ZB
- 页面导入
- 页面单设备 `store/start`
- 必要时补一个批量入口

### 2. Precheck And Blocking

验证“不能采”的设备会被清晰阻断，而不是脏写或假成功。

至少覆盖：

- 缺凭据
- 协议不匹配
- detect 成功但 collect 前置条件不足
- facts 缺关键 identity 锚
- 目标不可达 / 控制器不可用

### 3. Success Path Correctness

不只验证 success，还验证内容是否正确。

至少覆盖：

- 网络设备正常成功
- 服务器设备正常成功
- 监控下发成功

### 4. Partial Success And Recovery

验证 partial、恢复重试、旧状态清理是否可信。

至少覆盖：

- mixed batch：一部分成功、一部分阻断
- monitor push 失败但 store 成功
- 修复条件后重试成功
- 旧成功态 / 旧 process result 不污染恢复结果

### 5. Read Model Consistency

专门防止“源数据对了，页面错了”。

至少覆盖：

- detail vs list 一致性
- task summary vs runs vs observation 一致性
- runtime_health 与运行态、指标资产的一致性

### 6. Monitoring Runtime Truth

防止把 `monitor_push success` 错当成“监控已经正常运行”。

至少覆盖：

- 下发成功且 runtime healthy
- 下发成功但 runtime failed
- 下发成功但 runtime stale / unknown
- 指标声明存在但部分未观测到

### PR Core Minimum Set

第一版 `PR core` 不追求广度，优先包含：

- 2-3 组后端主链路关键夹具集
- 1 组 blocked / partial / recovery 夹具集
- 1 组前端读模型与状态展示核心 smoke
- 1 组监控运行态聚合逻辑验证

## Domain Appendix Template

每个设备领域附录建议固定采用同一结构：

1. `领域范围与对象定义`
2. `关键主链路`
3. `设备 / 协议 / 接入矩阵`
4. `失败模式与边界定义`
5. `P0 / P1 / P2 场景清单`
6. `夹具与样本准备要求`
7. `本地集成与真实验证要求`
8. `进入 PR core / nightly / manual 的准入条件`

### First Three Appendices

#### 网络设备附录

优先覆盖：

- 交换机 / 路由器
- SNMP / SSH
- 设备画像纠偏
- 监控 runtime
- 指标覆盖

#### 服务器设备附录

优先覆盖：

- SSH / IPMI
- 系统画像
- 带外信息
- 监控模板匹配
- 凭据解析

#### 防火墙设备附录

优先覆盖：

- 导入 / 在线采集
- 厂商差异
- 对象 / 策略 / zone / config 事实
- 页面工作流
- 配置相关验证

## Evidence Model

所有测试结果都必须回答四个问题：

1. 测的是什么场景
2. 是否符合预期
3. 证据落在哪几层
4. 如果失败，失败属于缺陷、环境问题还是已声明边界

### Evidence Types

#### 1. Result Evidence

最小字段建议包含：

- case id
- 领域
- 设备类型
- 入口
- 协议 / 能力组合
- 预期结果
- 实际结果
- 时间
- 执行环境

#### 2. Truth Evidence

对于主链路至少需要核对这些层：

- `entity_instance`
- `platform_devices_v2`
- 页面 `detail / list / summary`
- `task / run / observation`
- `monitoring task runtime / agent runtime`
- 必要时 `device_v1`、回调记录、监控指标资产

#### 3. Diagnostic Evidence

失败或 finding 至少要包含：

- request id / task id / device code
- 关键错误码
- 关键日志位置
- 相关截图或 API 返回
- 失败阶段
- 是否可复现
- 是否已有明确边界定义

### Result Status

统一使用 5 种状态：

- `passed`
- `passed-with-boundary`
- `failed`
- `finding`
- `invalid`

### Additional Rules

- 任何 P0/P1 结论，如果没有至少一层结果证据和一层真值证据，不得标记为 `passed`。
- 任何真实环境验证，如果没有 `request/task/device/time` 四元组，不得标记为 `passed-real` 或 `finding-real`。

## Phase 1 Deliverables

Phase 1 的交付物不是单份方案，而是一套共享资产：

1. `平台测试基线总纲`
2. `网络设备 / 服务器设备 / 防火墙设备附录骨架`
3. `平台总覆盖矩阵`
4. `Phase 1 核心集`
5. `GitHub private + self-hosted runner` 的 PR 核心门禁基线
6. `证据、finding、边界、缺口` 的标准化沉淀路径

## Roles And Collaboration

建议建立以下角色分工：

### Platform Testing Baseline Owner

负责：

- 平台总纲
- 总覆盖矩阵
- 门禁层规则
- 证据标准
- CI / core suite 落地
- 跨领域共性问题收敛

### Domain Owners

首批至少包括：

- 网络设备 owner
- 服务器设备 owner
- 防火墙设备 owner

负责：

- 领域附录
- 协议 / 能力矩阵
- P0/P1 场景
- 失败边界
- 夹具与样本准备
- 真实验证候选

### Backend Owners

负责：

- 补关键单测 / fixture test
- 整理后端测试入口
- 提供 testdata / seed / mock 点
- 修复脆弱回归点

### Frontend Owners

负责：

- 收编 smoke 脚本
- 补读模型、一致性、状态展示测试
- 统一脚本入口与报告输出

### Environment / Runner Owner

负责：

- self-hosted runner 机器
- GitHub private workflow 运行条件
- 本地集成环境依赖
- nightly / real-world 运行支持
- 样本与回放数据支持

### Workstreams

Phase 1 建议按四条并行泳道推进：

- `文档泳道`
- `测试资产泳道`
- `执行机制泳道`
- `问题收敛泳道`

## Milestones

### M1: Shared Framework

交付：

- 总纲初版
- 三份领域附录骨架
- 覆盖矩阵骨架
- 门禁分层规则
- 证据状态规则

### M2: Asset Takeover

交付：

- 现有测试资产盘点表
- 首批 P0/P1 场景映射
- 首批夹具 / 样本清单
- 已知 finding 与边界清单

### M3: PR Core Online

交付：

- `OneOPS + OneOPS-UI` 统一核心集入口
- GitHub private + self-hosted runner PR workflow
- 10 分钟内核心门禁集
- 标准化 core suite 报告

### M4: Domain Expansion Ready

交付：

- 网络设备附录初版
- 服务器设备附录初版
- 防火墙设备附录初版
- 各领域 P0/P1、夹具需求、真实验证候选
- Phase 2 backlog

## Suggested Phase 1 Timeline

- `第 1 周`
  - 总纲
  - 附录模板
  - 覆盖矩阵骨架
  - 测试资产盘点
- `第 2 周`
  - 首批 P0/P1 场景归类
  - 夹具与样本清单
  - 核心集设计
- `第 3 周`
  - 核心集接线
  - self-hosted runner / workflow 打通
  - PR core 试跑
- `第 4 周`
  - 修核心集稳定性
  - 补首批高风险测试
  - 发布 Phase 1 基线初版

## Phase 2 Direction

在本设计完成后，建议自然推进以下扩展方向：

1. `采集覆盖闭环`
   - 设备类型 / 厂商 / 协议矩阵扩展
2. `监控覆盖闭环`
   - 监控模板、任务下发、runtime、指标覆盖扩展
3. `性能与规模测试`
   - 大量设备
   - 大量 agent
   - 大量监控任务
   - 大量监控目标
   - 大量监控数据查询

## Decision Summary

本设计基于以下已确认决策：

- Phase 1 聚焦 `平台测试基线`
- 范围收敛为 `OneOPS + OneOPS-UI`
- 完成标准为 `标准 + 补齐首批高风险测试`
- 首批主线为 `设备入库 + 采集 + 监控`
- 环境策略为 `离线夹具 + 本地集成优先`
- 门禁采用 `GitHub private + 单台 self-hosted runner`
- 门禁触发时机为 `PR`
- `PR core` 目标时长为 `10 分钟内`

## Open Follow-Ups

本设计确认后，下一阶段需要继续落地：

1. 平台总覆盖矩阵初版文件
2. 三份领域附录骨架文件
3. 现有测试资产盘点文档
4. `PR core` 统一执行入口与 workflow 设计
5. 首批 P0/P1 场景到具体测试入口的映射
