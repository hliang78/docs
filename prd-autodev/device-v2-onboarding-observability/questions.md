---
topic: device-v2-onboarding-observability
kind: full-stack
title: Device V2 纳管观测闭环
status: draft
---

# Question Round 001

1. 网络设备远程配置 syslog/trap 时，是否必须先进入人工审批？建议默认先实现 dry-run + evidence，不直接下发。
2. 区域 agent 的权威来源是什么：FunctionArea 配置、Agent heartbeat metadata、Topology，还是监控任务当前运行态？
3. 服务器日志默认采集范围是什么：系统日志、auth/security、应用日志，还是按设备模板选择？
4. Loki 标签契约是否已有标准？至少需要 device_code/ip/agent_code/source 中的哪些字段？
5. Prometheus 验证要验证哪类指标最小集：up、ping、snmp/interface、agent 自身采集成功计数？
6. “纳管完成”是否必须 Prometheus 与 Loki 都成功，还是允许 `partial_managed` 进入后续人工处理？

# Question Round 002: Independent Syslog/SNMP Trap Management Page

1. 新页面的主目标是否是“管理区域 agent 上的监听服务”，而不是“直接管理设备侧远程 syslog target 下发”？我当前理解是前者为主，设备侧 target 下发能力只复用现有链路，不作为这页的主语义。
2. `服务器 syslog 监听` 与 `网络设备 syslog 监听` 的区别，是否主要体现在表单默认值、监听端口/协议、Grok/标签策略、以及后续 target/source 选择规则上？还是你还希望它们最终走不同的后端配置模型？
3. SNMP trap 这一轮是否只要求独立管理页支持 agent 选择与 listener 下发，不要求补齐设备侧完整 trap target 远程配置？这和当前 onboarding PRD 的“trap 先保留模板缺口”需要保持一致还是要升级范围？
4. 独立管理页是否应该直接复用现有 `platform_log_forward_plan` / `remote_syslog` 模型做包装，还是你更希望它有独立名称、独立列表、独立接口，只是在发布阶段复用现有下发过程？

## Round 002 Answers

1. 主目标确认是“管理区域 agent 上的监听服务”。
2. `服务器 syslog 监听` 与 `网络设备 syslog 监听` 首期只做表单与默认值差异，不拆不同后端模型。
3. 已明确确认：本轮 `snmp trap` 只做 listener 管理，不扩到设备侧完整 trap target 远程下发。
4. 新页面可以包装复用现有 `remote_syslog` / `log_forward_plan` 模型与发布过程。
