# ZB Agent Telegraf-Style Scale Refactor Notes

- Primary implementation plan: [2026-06-01-agent-telegraf-style-input-scheduler.md](/home/jacky/project/OneOPS-ALL/docs/superpowers/plans/2026-06-01-agent-telegraf-style-input-scheduler.md)
- Why this exists:
  - 当前 agent 已把单设备 replay 的 `snmp` 首轮窗口压到约 `6~7s`
  - 但容量问题仍然存在：collector 还是全局串行扫 input
  - 如果挂几千个 SNMP 任务，吞吐瓶颈会重新出现，只是症状会从“单设备排队”升级成“整台 agent 跨周期积压”
- 本轮对 Telegraf 的借鉴结论：
  - Telegraf 官方 agent 不是全局串行扫 input，而是每个 input 独立 `gatherLoop()`
  - `gatherOnce()` 有 overrun skip 语义：上次没跑完时不会无限重入
  - `inputs.snmp` 一个插件实例可以挂多个 `agents`
  - `collection_jitter` / `collection_offset` / `flush_jitter` 用来错峰
  - 这些都比“继续修全局 priority 队列”更接近容量解法
- 交接给下一位 AI 时，建议默认从计划文档 Task 1 开始，而不是再回到 `REAL-075/076` 那套旧 global queue 假设
