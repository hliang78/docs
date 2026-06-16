# 上海移动研究院 POC 测试用例截图索引

- 源测试报告: `/OneOPS/docs/副本上海移动研究院自动化运维平台POC测试方案_V1.1(1).docx`
- 生成时间: 2026-06-16T06:52:39.116Z
- 前端地址: http://10.0.110.251:3001
- 后端地址: http://10.0.110.251:8080/api/v1
- 登录账号: admin
- 说明：本清单按新报告《副本上海移动研究院自动化运维平台POC测试方案_V1.1(1).docx》中的测试用例组织。
- 状态口径：`matched` = 页面与用例高度对应；`partial` = 页面可支撑部分验证；`fallback` = 仅能作为近似入口；`route-missing` = 当前直达页面缺失。
- 结论口径：`通过（按当前前端取证）` 表示页面与流程入口已形成可用前端证据；`不通过` 表示当前截图无法完成关键闭环或页面数据不足。

## TC-01 设备入库测试

- 路由: `/device/device-v2-management`
- 状态: matched
- 适配度: direct
- 前端取证结论: 通过（按当前前端取证）
- 截图: `docs/poc-deliverables/2026-06-16-sh-mobile-poc/testcase-screenshots/tc-01-device-onboarding.png`
- 取证理由: 设备管理页直接展示区域、机房、机柜树和设备清单，可作为入库与字段核对的主页面证据。
- 关联支撑页: `/device/device_inventory`、`/base/site`、`/base/rack`
- 实际结果填写建议: 设备管理页可见区域/机房/机柜分层和设备清单，当前平台已具备设备入库后的列表化核查入口，可支撑设备编码、位置与基础字段的前端核对。
- 页面标题: OneOPS / 首页/设备管理/ / 设备分组 / 设备清单
- 页面摘要: OneOPS 统一运维管理平台 仪表盘 监控面板 防火墙管理 采集管理 AIOPS 计划任务 观测处理 智算管理 设备巡检 基础数据 设备管理 设备管理 交换机入库 服务器入库 专线 带外日志 库存设备 变更历史 资源清册 终端管理 应用管理 PON管理 标签管理 报表管理 配置管理 服务管理 虚机管理 工单管理 告警管理 IPAM 运维管理 补丁管理 采集测试 系统管理 首页/ 设备管理 设备管理 设备分组 展 开 收 起 当前分层 编 辑 区域 > 机房 > 机架 全部设备 51 上海 51 张江IDC机房 2

## TC-02 自动监控测试

- 路由: `/platform/monitoring-tasks`
- 状态: matched
- 适配度: direct
- 前端取证结论: 通过（按当前前端取证）
- 截图: `docs/poc-deliverables/2026-06-16-sh-mobile-poc/testcase-screenshots/tc-02-auto-monitoring.png`
- 取证理由: 监控任务管理页直接对应自动监控任务、执行 Agent 与任务运行态，是自动采集主线的核心入口。
- 关联支撑页: `/monitor-panel/monitoring-center`、`/platform/monitoring-metric-assets`
- 实际结果填写建议: 监控任务管理页已具备任务列表、执行 Agent、运行工具和任务态势视图；结合设备监控页，当前平台具备自动监控任务的前端承载能力。
- 页面标题: OneOPS / 首页/监控任务管理/ / 监控任务工作台 / 任务态势 / 筛选 / 任务列表
- 页面摘要: OneOPS 统一运维管理平台 仪表盘 监控面板 防火墙管理 采集管理 监控指标资产 策略模版 应用管理 分组管理 设备管理 区域控制器 Agent列表 文件管理 部署管理 升级管理 托管标签 监控输出 监控任务 仓库 定时任务 任务模版 变量集 任务管理 设备适配 日志转发 日志解析 日志文件 AIOPS 计划任务 观测处理 智算管理 设备巡检 基础数据 设备管理 终端管理 应用管理 PON管理 标签管理 报表管理 配置管理 服务管理 虚机管理 工单管理 告警管理 IPAM 运维管理 补丁管理 采集测试 系统管理

## TC-03 日志监听测试

- 路由: `/platform/area-listener-services`
- 状态: matched
- 适配度: direct
- 前端取证结论: 通过（按当前前端取证）
- 截图: `docs/poc-deliverables/2026-06-16-sh-mobile-poc/testcase-screenshots/tc-03-log-listening.png`
- 取证理由: 区域日志接入服务页直接面向区域 Agent 的 syslog/snmp trap 监听配置，最贴近日志监听任务下发场景。
- 关联支撑页: `/platform/log-forward-plans`、`/dashboard/log`
- 实际结果填写建议: 区域日志接入服务页可见监听服务管理入口；同时日志中心已可打开并展示交换机日志样本，说明当前平台已具备日志监听与集中接入的前端链路。
- 页面标题: OneOPS / 首页/区域日志接入服务/ / 区域日志接入服务
- 页面摘要: OneOPS 统一运维管理平台 仪表盘 监控面板 防火墙管理 采集管理 监控指标资产 策略模版 应用管理 分组管理 设备管理 区域控制器 Agent列表 文件管理 部署管理 升级管理 托管标签 监控输出 监控任务 仓库 定时任务 任务模版 变量集 任务管理 设备适配 日志转发 日志解析 日志文件 AIOPS 计划任务 观测处理 智算管理 设备巡检 基础数据 设备管理 终端管理 应用管理 PON管理 标签管理 报表管理 配置管理 服务管理 虚机管理 工单管理 告警管理 IPAM 运维管理 补丁管理 采集测试 系统管理

## TC-04 集中监控测试

- 路由: `/monitor-panel/monitoring-center`
- 状态: matched
- 适配度: direct
- 前端取证结论: 通过（按当前前端取证）
- 截图: `docs/poc-deliverables/2026-06-16-sh-mobile-poc/testcase-screenshots/tc-04-centralized-monitoring.png`
- 取证理由: 设备监控页直接承载按设备筛选和查看监控详情的集中监控入口。
- 关联支撑页: `/dashboard/monitor`、`/platform/monitoring-tasks`
- 实际结果填写建议: 已在设备监控页选中设备 `张江IDC机房-D05-40-40`（`DVCEFB68A85655D` / `172.21.165.17`），右侧成功加载该设备对应的 Grafana 监控仪表盘。截图中可直接看到 `CPU Now`、`Memory Now`、`Traffic Throughput`、`Packets Per Second` 等监控图表，能够证明平台已支持按设备集中查看监控面板。
- 页面标题: OneOPS / 首页/监控面板/设备监控/ / 设备导航已加载 50 / 51 台
- 页面摘要: OneOPS 统一运维管理平台 仪表盘 监控面板 数据源管理 仪表盘管理 设备监控 防火墙管理 采集管理 AIOPS 计划任务 观测处理 智算管理 设备巡检 基础数据 设备管理 终端管理 应用管理 PON管理 标签管理 报表管理 配置管理 服务管理 虚机管理 工单管理 告警管理 IPAM 运维管理 补丁管理 采集测试 系统管理 首页/ 监控面板/ 设备监控 设备监控 设备导航 已加载 50 / 51 台 筛选条件 关键词 功能区域 全部 平台 全部 刷新列表 重置条件 51 当前匹配 50 设备总计 设备列表 张江

## TC-05 集中日志测试

- 路由: `/dashboard/log`
- 状态: matched
- 适配度: direct
- 前端取证结论: 通过（按当前前端取证）
- 截图: `docs/poc-deliverables/2026-06-16-sh-mobile-poc/testcase-screenshots/tc-05-centralized-log-search.png`
- 取证理由: 日志中心页直接对应平台内日志过滤、检索与查看详情的场景。
- 关联支撑页: `/platform/log-forward-plans`、`/platform/area-listener-services`
- 实际结果填写建议: 日志中心页面可正常打开，能看到时间窗、日志级别、高级过滤和日志内容区域，当前平台已具备集中日志检索的前端入口。
- 页面标题: OneOPS / 首页/仪表盘/日志中心/ / 交换机日志 / 日志等级分布
- 页面摘要: OneOPS 统一运维管理平台 仪表盘 监控中心 日志中心 网络拓扑 监控面板 防火墙管理 采集管理 AIOPS 计划任务 观测处理 智算管理 设备巡检 基础数据 设备管理 终端管理 应用管理 PON管理 标签管理 报表管理 配置管理 服务管理 虚机管理 工单管理 告警管理 IPAM 运维管理 补丁管理 采集测试 系统管理 首页/ 仪表盘/ 日志中心 设备管理 监控任务管理 区域日志接入服务 设备监控 日志中心 5分钟 297s 日志级别 高级过滤 重置过滤 租户视图 全屏 编辑 交换机日志 2026/06/16 

## TC-06 网络拓扑测试

- 路由: `/dashboard/topology`
- 状态: partial
- 适配度: partial
- 前端取证结论: 不通过（需补充现场或后端联调）
- 截图: `docs/poc-deliverables/2026-06-16-sh-mobile-poc/testcase-screenshots/tc-06-network-topology.png`
- 取证理由: 网络拓扑页是拓扑与钻取的唯一直接页面，但当前页面未呈现有效拓扑数据。
- 关联支撑页: `/device/device-v2-management`
- 实际结果填写建议: 网络拓扑页面可以打开，但当前取证时页面显示“暂无拓扑数据”，未形成可用于比对链路关系与钻取路径的现网前端证据。
- 页面标题: OneOPS / 首页/仪表盘/网络拓扑/
- 页面摘要: OneOPS 统一运维管理平台 仪表盘 监控中心 日志中心 网络拓扑 监控面板 防火墙管理 采集管理 AIOPS 计划任务 观测处理 智算管理 设备巡检 基础数据 设备管理 终端管理 应用管理 PON管理 标签管理 报表管理 配置管理 服务管理 虚机管理 工单管理 告警管理 IPAM 运维管理 补丁管理 采集测试 系统管理 首页/ 仪表盘/ 网络拓扑 设备管理 监控任务管理 区域日志接入服务 设备监控 日志中心 网络拓扑 上海移动研究院 节点 6/39 链路 26 显示孤点 聚焦连边 概览 设备聚焦 全量 图例 对

## TC-07 Agent 部署测试

- 路由: `/platform/deployment`
- 状态: matched
- 适配度: direct
- 前端取证结论: 通过（按当前前端取证）
- 截图: `docs/poc-deliverables/2026-06-16-sh-mobile-poc/testcase-screenshots/tc-07-agent-deployment.png`
- 取证理由: 部署管理页直接面向 Agent 批量部署、状态跟踪与诊断日志下载。
- 关联支撑页: `/platform/agent_management`
- 实际结果填写建议: 部署管理页可正常打开，当前平台具备 Agent 部署看板、历史记录和诊断下载入口，前端流程完整。
- 页面标题: OneOPS / 首页/采集管理/部署管理/ / 批量部署编排器
- 页面摘要: OneOPS 统一运维管理平台 仪表盘 监控面板 防火墙管理 采集管理 监控指标资产 策略模版 应用管理 分组管理 设备管理 区域控制器 Agent列表 文件管理 部署管理 升级管理 托管标签 监控输出 监控任务 仓库 定时任务 任务模版 变量集 任务管理 设备适配 日志转发 日志解析 日志文件 AIOPS 计划任务 观测处理 智算管理 设备巡检 基础数据 设备管理 终端管理 应用管理 PON管理 标签管理 报表管理 配置管理 服务管理 虚机管理 工单管理 告警管理 IPAM 运维管理 补丁管理 采集测试 系统管理

## TC-08 Agent 与 Controller 运维测试

- 路由: `/platform/agent_management`
- 状态: matched
- 适配度: direct
- 前端取证结论: 通过（按当前前端取证）
- 截图: `docs/poc-deliverables/2026-06-16-sh-mobile-poc/testcase-screenshots/tc-08-agent-controller-ops.png`
- 取证理由: Agent 列表页与区域控制器页共同组成 Agent/Controller 运维主入口，其中 Agent 列表页更贴近在线状态与详情核对。
- 关联支撑页: `/platform/controller_management`、`/platform/deployment`
- 实际结果填写建议: Agent 列表页可正常访问，当前平台已具备 Agent 在线状态、详情查看及与部署链路联动的前端入口，可作为 Agent/Controller 运维测试主取证页面。
- 页面标题: OneOPS / 首页/采集管理/Agent列表/
- 页面摘要: OneOPS 统一运维管理平台 仪表盘 监控面板 防火墙管理 采集管理 监控指标资产 策略模版 应用管理 分组管理 设备管理 区域控制器 Agent列表 文件管理 部署管理 升级管理 托管标签 监控输出 监控任务 仓库 定时任务 任务模版 变量集 任务管理 设备适配 日志转发 日志解析 日志文件 AIOPS 计划任务 观测处理 智算管理 设备巡检 基础数据 设备管理 终端管理 应用管理 PON管理 标签管理 报表管理 配置管理 服务管理 虚机管理 工单管理 告警管理 IPAM 运维管理 补丁管理 采集测试 系统管理

## TC-09 告警触发、列表呈现与通知送达

- 路由: `/alert/alarm`
- 状态: partial
- 适配度: partial
- 前端取证结论: 不通过（需补充现场或后端联调）
- 截图: `docs/poc-deliverables/2026-06-16-sh-mobile-poc/testcase-screenshots/tc-09-alert-trigger-notify.png`
- 取证理由: 告警列表页可作为告警呈现证据，但通知送达属于站外链路，无法仅凭当前前端截图完成闭环验证。
- 关联支撑页: `/alert/receiver`、`/alert/group`、`/alert/strategy`
- 实际结果填写建议: 告警列表页面已具备告警检索与列表展示能力，但邮件/IM 等通知送达结果未在当前截图链路中形成直接证据，需现场联调补测。
- 页面标题: OneOPS / 首页/告警管理/告警列表/ / 条件过滤 / 告警列表
- 页面摘要: OneOPS 统一运维管理平台 仪表盘 监控面板 防火墙管理 采集管理 AIOPS 计划任务 观测处理 智算管理 设备巡检 基础数据 设备管理 终端管理 应用管理 PON管理 标签管理 报表管理 配置管理 服务管理 虚机管理 工单管理 告警管理 数据源 接收者 接收组 维护组 告警规则 告警策略 告警抑制 告警列表 IPAM 运维管理 补丁管理 采集测试 系统管理 首页/ 告警管理/ 告警列表 设备管理 监控任务管理 区域日志接入服务 设备监控 日志中心 网络拓扑 部署管理 Agent列表 告警列表 告警列表 发送

## TC-10 分责订阅

- 路由: `/alert/strategy`
- 状态: matched
- 适配度: direct
- 前端取证结论: 通过（按当前前端取证）
- 截图: `docs/poc-deliverables/2026-06-16-sh-mobile-poc/testcase-screenshots/tc-10-alert-subscription-strategy.png`
- 取证理由: 告警策略页直接对应责任分层、接收策略与升级规则配置。
- 关联支撑页: `/alert/group`、`/alert/receiver`
- 实际结果填写建议: 告警策略页可见策略集与策略列表，当前平台已具备分责订阅与分层策略配置的前端入口。
- 页面标题: OneOPS / 首页/告警管理/告警策略/ / 策略集 / 条件过滤 / 策略列表
- 页面摘要: OneOPS 统一运维管理平台 仪表盘 监控面板 防火墙管理 采集管理 AIOPS 计划任务 观测处理 智算管理 设备巡检 基础数据 设备管理 终端管理 应用管理 PON管理 标签管理 报表管理 配置管理 服务管理 虚机管理 工单管理 告警管理 数据源 接收者 接收组 维护组 告警规则 告警策略 告警抑制 告警列表 IPAM 运维管理 补丁管理 采集测试 系统管理 首页/ 告警管理/ 告警策略 设备管理 监控任务管理 区域日志接入服务 设备监控 日志中心 网络拓扑 部署管理 Agent列表 告警列表 告警策略 策略

## TC-11 告警抑制

- 路由: `/alert/inhibit`
- 状态: matched
- 适配度: direct
- 前端取证结论: 通过（按当前前端取证）
- 截图: `docs/poc-deliverables/2026-06-16-sh-mobile-poc/testcase-screenshots/tc-11-alert-inhibit.png`
- 取证理由: 告警抑制页直接展示抑制规则与抑制日志，是该测试用例最直接的页面。
- 关联支撑页: `/alert/alarm`
- 实际结果填写建议: 告警抑制页面可见抑制规则与抑制日志两类对象，当前平台已具备告警抑制配置与查看入口。
- 页面标题: OneOPS / 首页/告警管理/告警抑制/ / 条件过滤 / 抑制规则列表
- 页面摘要: OneOPS 统一运维管理平台 仪表盘 监控面板 防火墙管理 采集管理 AIOPS 计划任务 观测处理 智算管理 设备巡检 基础数据 设备管理 终端管理 应用管理 PON管理 标签管理 报表管理 配置管理 服务管理 虚机管理 工单管理 告警管理 数据源 接收者 接收组 维护组 告警规则 告警策略 告警抑制 告警列表 IPAM 运维管理 补丁管理 采集测试 系统管理 首页/ 告警管理/ 告警抑制 设备管理 监控任务管理 区域日志接入服务 设备监控 日志中心 网络拓扑 部署管理 Agent列表 告警列表 告警策略 告警

## TC-12 维护窗口支持

- 路由: `/alert/maintain`
- 状态: partial
- 适配度: partial
- 前端取证结论: 通过（按当前前端取证）
- 截图: `docs/poc-deliverables/2026-06-16-sh-mobile-poc/testcase-screenshots/tc-12-maintain-window.png`
- 取证理由: 当前告警域最接近维护窗口场景的入口是维护组页面，可作为维护对象与维护范围配置证据。
- 关联支撑页: `/alert/strategy`
- 实际结果填写建议: 维护组页面可正常打开，可作为维护对象管理的前端入口；是否完全覆盖维护窗口静默语义仍需结合策略联调确认。
- 页面标题: OneOPS / 首页/告警管理/维护组/ / 条件过滤 / 维护组列表
- 页面摘要: OneOPS 统一运维管理平台 仪表盘 监控面板 防火墙管理 采集管理 AIOPS 计划任务 观测处理 智算管理 设备巡检 基础数据 设备管理 终端管理 应用管理 PON管理 标签管理 报表管理 配置管理 服务管理 虚机管理 工单管理 告警管理 数据源 接收者 接收组 维护组 告警规则 告警策略 告警抑制 告警列表 IPAM 运维管理 补丁管理 采集测试 系统管理 首页/ 告警管理/ 维护组 设备管理 监控任务管理 区域日志接入服务 设备监控 日志中心 网络拓扑 部署管理 Agent列表 告警列表 告警策略 告警抑

## TC-13 故障恢复后的告警闭环

- 路由: `/alert/alarm`
- 状态: partial
- 适配度: partial
- 前端取证结论: 不通过（需补充现场或后端联调）
- 截图: `docs/poc-deliverables/2026-06-16-sh-mobile-poc/testcase-screenshots/tc-13-alert-recovery-closure.png`
- 取证理由: 告警列表页可作为活跃/历史告警入口，但自动恢复闭环需要告警源恢复后的时序结果，当前截图无法直接证明。
- 关联支撑页: `/alert/strategy`、`/alert/inhibit`
- 实际结果填写建议: 当前平台具备告警列表与历史告警入口，但“故障恢复后自动收口”这一时序闭环未在当前取证中直接呈现，需现场补测。
- 页面标题: OneOPS / 首页/告警管理/告警列表/ / 条件过滤 / 告警列表
- 页面摘要: OneOPS 统一运维管理平台 仪表盘 监控面板 防火墙管理 采集管理 AIOPS 计划任务 观测处理 智算管理 设备巡检 基础数据 设备管理 终端管理 应用管理 PON管理 标签管理 报表管理 配置管理 服务管理 虚机管理 工单管理 告警管理 数据源 接收者 接收组 维护组 告警规则 告警策略 告警抑制 告警列表 IPAM 运维管理 补丁管理 采集测试 系统管理 首页/ 告警管理/ 告警列表 设备管理 监控任务管理 区域日志接入服务 设备监控 日志中心 网络拓扑 部署管理 Agent列表 告警列表 告警策略 告警

## TC-14 凭据引用驱动远程任务

- 路由: `/setting/credential-unified`
- 状态: matched
- 适配度: direct
- 前端取证结论: 通过（按当前前端取证）
- 截图: `docs/poc-deliverables/2026-06-16-sh-mobile-poc/testcase-screenshots/tc-14-credential-reference-task.png`
- 取证理由: 统一凭证工作台是凭据引用、绑定与版本管理的主页面，直接对应“平台只绑定凭证引用”的场景。
- 关联支撑页: `/platform/task-center`
- 实际结果填写建议: 统一凭证页面可正常访问，页面明确承载凭证引用、绑定和工作台操作，当前平台已具备凭据引用的前端入口。
- 页面标题: OneOPS / 首页/统一凭证（列表与绑定）/ / 凭证列表（无明文） / Vault Catalog 管理
- 页面摘要: OneOPS 统一运维管理平台 仪表盘 监控面板 防火墙管理 采集管理 AIOPS 计划任务 观测处理 智算管理 设备巡检 基础数据 设备管理 终端管理 应用管理 PON管理 标签管理 报表管理 配置管理 统一凭证 Secret Community 服务管理 虚机管理 工单管理 告警管理 IPAM 运维管理 补丁管理 采集测试 系统管理 首页/ 统一凭证（列表与绑定） 设备管理 监控任务管理 区域日志接入服务 设备监控 日志中心 网络拓扑 部署管理 Agent列表 告警列表 告警策略 告警抑制 维护组 统一凭证（列

## TC-15 操作日志检索与导出审计抽样

- 路由: `/sys/LogRecord`
- 状态: matched
- 适配度: direct
- 前端取证结论: 通过（按当前前端取证）
- 截图: `docs/poc-deliverables/2026-06-16-sh-mobile-poc/testcase-screenshots/tc-15-operation-audit.png`
- 取证理由: 系统管理中的操作审计页面直接提供责任主体、时间与业务对象等维度检索，并展示已有审计记录。
- 实际结果填写建议: 操作审计页面已加载并显示总命中记录数与当前页数据，当前平台已形成统一操作审计入口，可支撑检索类取证。
- 页面标题: OneOPS / 首页/系统管理/操作审计/ / 条件过滤 / 操作审计
- 页面摘要: OneOPS 统一运维管理平台 仪表盘 监控面板 防火墙管理 采集管理 AIOPS 计划任务 观测处理 智算管理 设备巡检 基础数据 设备管理 终端管理 应用管理 PON管理 标签管理 报表管理 配置管理 服务管理 虚机管理 工单管理 告警管理 IPAM 运维管理 补丁管理 采集测试 系统管理 组织管理 账户管理 操作审计 用户管理 授权信息 菜单管理 LLM Provider 消息管理 首页/ 系统管理/ 操作审计 设备管理 监控任务管理 区域日志接入服务 设备监控 日志中心 网络拓扑 部署管理 Agent列表 

## TC-16 模板与变量集驱动的例行巡检

- 路由: `/platform/task-center`
- 状态: matched
- 适配度: direct
- 前端取证结论: 通过（按当前前端取证）
- 截图: `docs/poc-deliverables/2026-06-16-sh-mobile-poc/testcase-screenshots/tc-16-template-variable-inspection.png`
- 补充截图: 执行日志=`docs/poc-deliverables/2026-06-16-sh-mobile-poc/testcase-screenshots/tc-16-template-variable-inspection-logs.png`；配置下载=`docs/poc-deliverables/2026-06-16-sh-mobile-poc/testcase-screenshots/tc-16-template-variable-inspection-download.png`
- 已下载产物: 配置产物=`docs/poc-deliverables/2026-06-16-sh-mobile-poc/downloads/tc-16-server-config-DVCF2B08FF8702C.txt`
- 取证理由: 任务中心可直接基于已发布模板创建服务器巡检/采集任务；本次取证使用已发布的 `task-center-ansible-server-config-collection` 模板，页面自动带出变量组 `task-center-ansible-server-config-collection-defaults`，随后在任务日志与配置管理页形成执行和下载闭环。
- 关联支撑页: `/platform/task-templates`、`/platform/variable-sets`、`/device/config-management`
- 实际结果填写建议: 已在任务中心通过已发布模板 `task-center-ansible-server-config-collection` 打开创建任务弹窗，并预填项目 `project-server-config-management`，页面可见模板来源、Playbook 路径 `ansible/server-config-collection/site.yml` 与变量组 `task-center-ansible-server-config-collection-defaults`。随后定位到同模板子任务 `2cf1c705-1280-4edd-b288-390179c1f77c` 的执行日志，日志中可见 Agent 执行 `ansible-playbook` 成功；最后在配置管理页定位到资产 `DVCF2B08FF8702C` 的版本 `v3`，并已实际下载产物 `server-config-DVCF2B08FF8702C.txt`，形成创建、执行、下载三段证据链。
- 页面标题: OneOPS / 首页/任务中心/ / 任务列表
- 页面摘要: OneOPS 统一运维管理平台 仪表盘 监控面板 防火墙管理 采集管理 监控指标资产 策略模版 应用管理 分组管理 设备管理 区域控制器 Agent列表 文件管理 部署管理 升级管理 托管标签 监控输出 监控任务 仓库 定时任务 任务模版 变量集 任务管理 设备适配 日志转发 日志解析 日志文件 AIOPS 计划任务 观测处理 智算管理 设备巡检 基础数据 设备管理 终端管理 应用管理 PON管理 标签管理 报表管理 配置管理 服务管理 虚机管理 工单管理 告警管理 IPAM 运维管理 补丁管理 采集测试 系统管理

## TC-17 定时任务

- 路由: `/platform/scheduled-tasks`
- 状态: matched
- 适配度: direct
- 前端取证结论: 通过（按当前前端取证）
- 截图: `docs/poc-deliverables/2026-06-16-sh-mobile-poc/testcase-screenshots/tc-17-scheduled-tasks.png`
- 取证理由: 定时任务管理页直接对应计划策略、触发时刻和运行记录查看。
- 关联支撑页: `/platform/task-center`
- 实际结果填写建议: 定时任务管理页可正常访问，页面提供定时作业主线与运行观察入口，当前平台具备定时任务前端承载能力。
- 页面标题: OneOPS / 首页/定时任务管理/ / 定时任务
- 页面摘要: OneOPS 统一运维管理平台 仪表盘 监控面板 防火墙管理 采集管理 监控指标资产 策略模版 应用管理 分组管理 设备管理 区域控制器 Agent列表 文件管理 部署管理 升级管理 托管标签 监控输出 监控任务 仓库 定时任务 任务模版 变量集 任务管理 设备适配 日志转发 日志解析 日志文件 AIOPS 计划任务 观测处理 智算管理 设备巡检 基础数据 设备管理 终端管理 应用管理 PON管理 标签管理 报表管理 配置管理 服务管理 虚机管理 工单管理 告警管理 IPAM 运维管理 补丁管理 采集测试 系统管理

## TC-18 智能辅助脚本

- 路由: `/platform/script-template-studio`
- 状态: matched
- 适配度: direct
- 前端取证结论: 通过（按当前前端取证）
- 截图: `docs/poc-deliverables/2026-06-16-sh-mobile-poc/testcase-screenshots/tc-18-ai-script-assistant.png`
- 取证理由: 脚本模板工作台直接承载 AI 对话生成脚本的流程；本次取证以“AI 已返回内容，且生成草稿已进入脚本编辑器”为准。
- 关联支撑页: `/platform/task-templates`
- 实际结果填写建议: 已完成一次真实 AI 对话生成：左侧显示用户指令与 LLM 回复，右侧生成草稿版本，中间脚本编辑器已加载生成的 shell 巡检脚本内容，可直接作为智能辅助脚本的前端证据。
- 页面标题: OneOPS / 首页/脚本模板工作台/
- 页面摘要: OneOPS 统一运维管理平台 仪表盘 监控面板 防火墙管理 采集管理 监控指标资产 策略模版 应用管理 分组管理 设备管理 区域控制器 Agent列表 文件管理 部署管理 升级管理 托管标签 监控输出 监控任务 仓库 定时任务 任务模版 变量集 任务管理 设备适配 日志转发 日志解析 日志文件 AIOPS 计划任务 观测处理 智算管理 设备巡检 基础数据 设备管理 终端管理 应用管理 PON管理 标签管理 报表管理 配置管理 服务管理 虚机管理 工单管理 告警管理 IPAM 运维管理 补丁管理 采集测试 系统管理

## TC-19 凭证驱动的远程任务

- 路由: `/platform/script-template-studio`
- 状态: matched
- 适配度: direct
- 前端取证结论: 通过（按当前前端取证）
- 截图: `docs/poc-deliverables/2026-06-16-sh-mobile-poc/testcase-screenshots/tc-19-credential-driven-remote-task.png`
- 补充截图: 执行成功=`docs/poc-deliverables/2026-06-16-sh-mobile-poc/testcase-screenshots/tc-19-credential-driven-remote-task-success.png`
- 已下载产物: Run明细=`docs/poc-deliverables/2026-06-16-sh-mobile-poc/downloads/tc-19-credential-driven-remote-task-run.json`
- 取证理由: 脚本模板工作台的“执行测试”弹窗可直接指定 Agent、Inventory 与执行凭证；本次取证主图保留“执行凭证下拉已展开、目标凭证可见”，并补充同一条成功远程测试记录与请求载荷文件，形成“选择凭证 + 远程执行成功”的闭环。
- 关联支撑页: `/setting/credential-unified`、`/platform/task-center`
- 实际结果填写建议: 已基于 Ansible 远程任务打开脚本工作台执行测试弹窗，页面中已预填并展开执行凭证下拉，目标凭证 `vault_ssh_inband_sy_cmsr_oneops_secrets` 在候选列表中可见。补充取证中同时定位到同一会话下的成功测试记录 `dcd54140-63c1-11f1-8d5d-fa163e7745bf`，日志可见远程任务已准备 SSH 凭据并执行成功；并已落地保存该次 run 明细 JSON，可直接对应“凭证驱动的远程任务”。
- 页面标题: OneOPS / 首页/脚本模板工作台/
- 页面摘要: OneOPS 统一运维管理平台 仪表盘 监控面板 防火墙管理 采集管理 监控指标资产 策略模版 应用管理 分组管理 设备管理 区域控制器 Agent列表 文件管理 部署管理 升级管理 托管标签 监控输出 监控任务 仓库 定时任务 任务模版 变量集 任务管理 设备适配 日志转发 日志解析 日志文件 AIOPS 计划任务 观测处理 智算管理 设备巡检 基础数据 设备管理 终端管理 应用管理 PON管理 标签管理 报表管理 配置管理 服务管理 虚机管理 工单管理 告警管理 IPAM 运维管理 补丁管理 采集测试 系统管理

## TC-20 沙箱环境中的脚本草稿试跑

- 路由: `/platform/script-template-studio`
- 状态: matched
- 适配度: direct
- 前端取证结论: 通过（按当前前端取证）
- 截图: `docs/poc-deliverables/2026-06-16-sh-mobile-poc/testcase-screenshots/tc-20-sandbox-draft-run.png`
- 补充截图: 日志细节=`docs/poc-deliverables/2026-06-16-sh-mobile-poc/testcase-screenshots/tc-20-sandbox-draft-run-log-detail.png`
- 已下载产物: 任务日志=`docs/poc-deliverables/2026-06-16-sh-mobile-poc/downloads/tc-20-sandbox-draft-run-logs.txt`
- 取证理由: 脚本模板工作台中的测试详情直接呈现远程执行结果；本次取证主图保留“执行测试成功、task_id 已生成、日志可查看”的成功态，并补充更聚焦的日志细节图和日志导出文件。
- 关联支撑页: `/platform/task-center`
- 实际结果填写建议: 已定位到一条真实执行成功的远程测试记录：页面右侧可见成功状态、task_id、执行模式、Agent 与任务日志，能够证明脚本草稿已完成远程调试/沙箱试跑并通过。补充取证进一步保留同一测试详情中的日志细节画面，并已导出日志文本文件，形成“脚本工作台成功 + 日志细节 + 日志落地”的闭环。
- 页面标题: OneOPS / 首页/脚本模板工作台/
- 页面摘要: OneOPS 统一运维管理平台 仪表盘 监控面板 防火墙管理 采集管理 监控指标资产 策略模版 应用管理 分组管理 设备管理 区域控制器 Agent列表 文件管理 部署管理 升级管理 托管标签 监控输出 监控任务 仓库 定时任务 任务模版 变量集 任务管理 设备适配 日志转发 日志解析 日志文件 AIOPS 计划任务 观测处理 智算管理 设备巡检 基础数据 设备管理 终端管理 应用管理 PON管理 标签管理 报表管理 配置管理 服务管理 虚机管理 工单管理 告警管理 IPAM 运维管理 补丁管理 采集测试 系统管理

## TC-21 防火墙策略工单

- 路由: `/ticket/firewall`
- 状态: matched
- 适配度: direct
- 前端取证结论: 通过（按当前前端取证）
- 截图: `docs/poc-deliverables/2026-06-16-sh-mobile-poc/testcase-screenshots/tc-21-firewall-ticket.png`
- 取证理由: 防火墙工单页直接提供工单上传、工单列表和执行入口，是工单主链路页面。
- 关联支撑页: `/firewall/security_planning`
- 实际结果填写建议: 防火墙工单页面可正常访问，已具备工单上传、工单项查看与执行入口，当前平台已形成工单链路的前端承载页面。
- 页面标题: OneOPS / 首页/防火墙管理/防火墙工单/ / 条件过滤 / 工单列表
- 页面摘要: OneOPS 统一运维管理平台 仪表盘 监控面板 防火墙管理 安全规划 黑白名单 策略校验 防火墙工单 策略查询 采集管理 AIOPS 计划任务 观测处理 智算管理 设备巡检 基础数据 设备管理 终端管理 应用管理 PON管理 标签管理 报表管理 配置管理 服务管理 虚机管理 工单管理 告警工单 告警管理 IPAM 运维管理 补丁管理 采集测试 系统管理 首页/ 防火墙管理/ 防火墙工单 脚本模板工作台 防火墙工单 条件过滤 工单号 工单状态 请选择执行状态查询 查询重置展开 工单列表 新增 工单名称 工单号 创建

## TC-22 策略查询与对账

- 路由: `/l3/nodemap`
- 状态: matched
- 适配度: direct
- 前端取证结论: 通过（按当前前端取证）
- 截图: `docs/poc-deliverables/2026-06-16-sh-mobile-poc/testcase-screenshots/tc-22-policy-query-reconciliation.png`
- 补充截图: 查询结果=`docs/poc-deliverables/2026-06-16-sh-mobile-poc/testcase-screenshots/tc-22-policy-query-reconciliation-result.png`；策略详情=`docs/poc-deliverables/2026-06-16-sh-mobile-poc/testcase-screenshots/tc-22-policy-query-reconciliation-policy-detail.png`
- 取证理由: 策略查询页直接面向多条件策略查询、节点选择和查询结果展示。
- 关联支撑页: `/ticket/firewall`
- 实际结果填写建议: 已通过策略查询页实际发起蓝图标签“RBM_S<SH-HAP-ZQIDC-CMNET-FW-H3C-M9016-2>”的查询任务 L3QueryTask202606160009，查询条件为源目地址 172.22.166.14 且匹配模式为 contains。任务执行成功，并在结果弹窗中返回设备“SH-HAP-ZQIDC-CMNET-FW-H3C-M9016-2”上的 7 条匹配策略；同时已展开首条策略详情，展示源/目地址、CLI 配置与对象关系，可作为“策略查询与对账”的真实前端证据。
- 页面标题: OneOPS / 首页/防火墙管理/策略查询/ / 条件过滤 / 防火墙策略查询任务列表 / 防火墙策略查询结果 / 选择防火墙节点 / 策略列表 / 源地址 / 目标地址 / CLI 配置 / 对象关系
- 页面摘要: OneOPS 统一运维管理平台 仪表盘 监控面板 防火墙管理 安全规划 黑白名单 策略校验 防火墙工单 策略查询 采集管理 AIOPS 计划任务 观测处理 智算管理 设备巡检 基础数据 设备管理 终端管理 应用管理 PON管理 标签管理 报表管理 配置管理 服务管理 虚机管理 工单管理 告警管理 IPAM 运维管理 补丁管理 采集测试 系统管理 首页/ 防火墙管理/ 策略查询 策略查询 条件过滤 任务名称 任务编码 查询重置展开 防火墙策略查询任务列表 策略查询 状态 任务ID 查询条件 执行耗时 创建时间 完成时
