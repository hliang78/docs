# GPU 服务器巡检与上线检查设计

Date: 2026-06-21

## 目标

补一份 OneOPS 风格的 GPU 服务器标准巡检与上线检查 runbook，用于承接原始 SOP 中的：

- 服务器检查项
- NCCL 测试
- GPU 压测
- CPU / 内存测试
- DCGM 检测
- 初始化后的验收判断

## 设计选择

采用“三段式”结构，而不是只做日常巡检或只做交付验收：

1. 静态检查
2. 运行态检查
3. 压测与上线验收

这样一份文档就能同时服务于：

- 新机器上线前验收
- 重装后的恢复验收
- 扩容后的节点检查
- 日常巡检中的深度确认

## 边界

这份 runbook 不展开：

- 系统重装过程
- IB / ROCE 专项恢复细节
- 带外取证和厂商报障流程

这些都链接到现有专题 runbook。

## 产出文件

- `docs/runbooks/gpu-server-inspection-and-go-live-readiness.md`

并同步更新：

- `docs/knowledge/gpu-ops-sop-source-map-2026-06-21.md`
- `docs/runbooks/gpu-server-fault-response.md`
- `docs/runbooks/gpu-server-os-reinstall-and-baseline.md`

## 验收标准

文档完成后应满足：

1. 能覆盖原 SOP 的检查项和测试项核心内容
2. 用 OneOPS 主线来组织巡检与验收
3. 不直接抄入原文中的明文口令、下载地址或敏感环境细节
4. 读者能据此判断一台 GPU 服务器是“可上线 / 限制上线 / 不可上线”
