# Device V2 纳管观测开发文档

本文档集按 `docs/development-doc-templates` 的标准模板生成，用于支撑
`d2on` OpenClaw 自动化开发任务。

## 文档清单

| 阶段 | 文档 | 模板 |
| --- | --- | --- |
| 需求 | `01-需求概要-OneOPS_DeviceV2纳管观测_v0.1.md` | `01-需求概要模板.md` |
| 需求 | `02-功能清单-OneOPS_DeviceV2纳管观测_v0.1.md` | `02-功能清单模板.md` |
| 设计 | `05-数据库设计-OneOPS_DeviceV2纳管观测_v0.1.md` | `05-数据库设计模板.md` |
| 开发 | `06-接口文档-OneOPS_DeviceV2纳管观测_v0.1.md` | `06-接口文档模板.md` |
| 开发 | `07-后端开发设计-OneOPS_DeviceV2纳管观测_v0.1.md` | `07-后端开发设计模板.md` |
| 测试 | `08-测试用例-OneOPS_DeviceV2纳管观测_v0.1.md` | `08-测试用例模板.md` |
| 联调 | `09-接口调用文档-OneOPS_DeviceV2纳管观测_v0.1.md` | `09-接口调用文档模板.md` |

## 维护规则

- 业务代码变更必须同步更新对应开发文档。
- `D2ON-003` 的前端交互必须体现单台继续纳管、server monitor mode 显式选择、以及 backend error 直显，不得回退成批量采集验证语义。
- 继续纳管 UI 只允许单设备执行；批量选择仅能展示计划或结果摘要。
- 开发测试工具文档必须明确“仅用于开发测试，不是业务功能路径”。
- 业务远程服务器操作必须通过 controller 提供的 API，不得调用
  `docs/openclaw-autodev/tools/d2on/` 下的探索工具。
- 未确认事项必须保留为“待确认”，不得用推断补齐。
- 对于 D2ON-015 这类 bounded probe 结论，开发文档与 evidence 必须明确区分：
  - 本地 contract/test validation
  - 真实单台继续纳管执行结果或其具体 blocker
  - 任何 non-success 结果都要保留，不得改写成泛化成功
- 对于 D2ON-018 / D2ON-019 这轮结果，readiness 与 review 文档必须明确写出：本轮只补齐了可复用的文档边界，真实 controller-backed 单台执行结果仍缺失；不要把它写成已完成执行。
