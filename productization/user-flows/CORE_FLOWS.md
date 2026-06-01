# OneOPS 核心用户流程

基于 PRODUCT.md 的用户角色，识别关键流程：

## 1. 设备管理流程（Platform Operator）
- [ ] 导入设备（批量/单个）
- [ ] 查看设备清单
- [ ] 设备分组和标签
- [ ] 设备凭证配置
- [ ] 设备状态监控
- [ ] 设备历史追溯

## 2. 监控任务管理流程（Platform Operator）
- [ ] 创建监控任务
- [ ] 配置 Telegraf 策略
- [ ] 下发到 Agent
- [ ] 查看执行状态
- [ ] 处理失败和重试

## 3. 平台状态观察流程（SRE）
- [ ] 查看 Platform2 Ledger
- [ ] 对比 Agent Snapshot
- [ ] 识别 Drift
- [ ] 查看 Governance Case
- [ ] 追踪 Mutation Log

## 4. Agent 部署流程（Platform Operator）
- [ ] 选择部署目标（租户/VRF/站点）
- [ ] 配置 Agent 参数
- [ ] 执行部署
- [ ] 验证连接状态
- [ ] 查看 Agent 指标

## 5. 告警处理流程
- [ ] 查看告警列表
- [ ] 告警详情和上下文
- [ ] 告警确认和处理
- [ ] 告警规则配置
- [ ] 告警历史追溯

## 6. 设备采集流程
- [ ] 配置采集任务
- [ ] 选择采集目标
- [ ] 执行采集
- [ ] 查看采集结果
- [ ] 调试采集问题
