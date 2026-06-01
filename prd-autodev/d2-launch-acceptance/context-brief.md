# Device V2 上线验收测试闭环 Context Brief

UpdatedAt: 2026-05-14T13:25:00+0800
Kind: full-stack
Status: analysis-draft-db-derived-real-device

## 原始诉求

上线前验收 Device V2 入库工作台和设备 V2 清册管理。验收必须尽量接近真实生产：真实导入设备、真实驱动采集入库，并覆盖编辑、修改、删除等操作。

## 最新澄清

数据库中当前 Device V2 数据是真实设备。上线验收不再等待外部清单，而是从现有 Device V2 数据中抽样，导出关键设备信息和凭证引用，再通过入库界面重新导入，随后真实触发采集并做清册管理验收。

凭证处理边界：

- 允许导出和使用凭证引用、凭证角色、协议类型、端口、access point 关系，例如 `credential_ref_in_band`、`credential_ref_out_band`、`snmp_credential_ref`、`winrm_credential_ref`、`credential_refs`、`access_points[].credential_ref`。
- 不允许把明文密码、token、community secret、private key 写入 PRD、Excel 证据、日志或 OpenClaw evidence。
- 如果真实采集需要 secret material，必须通过系统已有凭证管理能力引用，不能在自动化任务文本中暴露。

## 初步分类

这是 full-stack 上线验收 program，不是单一前端 story。

- 前端范围：Device V2 入库工作台、设备 V2 清册管理、任务证据抽屉、Import Batch 生命周期面板、错误/空态/禁用态、按钮行为、响应式可用性。
- 后端范围：Device V2 CRUD、ingest tasks、import batches、store/start、store/retry、task summary/runs/observations/collection-plans、latest DC2、失败语义、数据抽样导出和清理策略。
- 验收范围：从 DB 真实设备抽样、脱敏导出、Excel 导入、真实采集、清册管理、证据回放，而不是只看页面打开、HTTP 200、截图或 typecheck。

## 已有基础

- Phase 2 real-operability gate 已完成本地确定性 smoke：`npm run smoke:d2-real-ops`。
- 已有后端合同表，包含 Device V2 list/create/update/delete、manual ingest、Excel upload、import batch、store/start/retry、task summary/runs/observations/plans/latest DC2。
- UI polish 已完成，入库工作台和管理页有 story-local responsive evidence。
- 前端 ingest 类型已经覆盖凭证引用和 access points 字段，可承接 DB-derived import。
- 当前 d2-fe story 队列无 open story，适合开始新的验收 program。

## 关键差异

已有 smoke 证明的是“本地后端 + D2P2_SMOKE 测试夹具 + 自动化 UI 链路可运行”。上线验收现在要证明：

- DB 中选出的真实设备能被导出为入库工作台可接受的清单。
- 导出的凭证信息是可执行的引用关系，而不是泄露明文 secret。
- 重新导入后，清册管理能查到导入/更新结果，并能和原始 DB 样本做字段对账。
- store/start 能触发真实设备采集，并在 task、runs、observations、collection plans、latest DC2 中留下证据。
- 编辑、修改、删除需要有明确策略：优先克隆测试 code，不直接覆盖/删除原生产记录；如必须同 code 更新，需先做快照和明确授权。
- 测试数据如何隔离、回滚、删除，避免污染正式资产清册。

## 推荐验收流

1. DB 只读抽样：选 5 台真实 Device V2 设备，每种设备类型优先选 1 台；要求字段完整、管理 IP 或 access point 可用、凭证引用存在、采集协议明确。
2. 脱敏导出：生成设备关键字段和凭证引用映射，屏蔽明文 secret。
3. 生成 Excel：转成入库工作台模板字段，默认使用 `D2LA_<orig_code>` 克隆 code，并用 `labels.d2la_orig_code` 保留原始 code 映射。
4. UI 导入：必须通过“Device V2 入库工作台”上传入口；upload/validate 本身是验收项目，validate 成功后再 apply，记录 task/result/handoff。
5. 清册对账：用管理页/API 对比导入记录和 DB 原样本关键字段。
6. 真实采集：对导入样本触发 store/start，采集协议由 controller detect 机制决定；先 1 台打通，再 5 台并行采集，验证 task、runs、observations、collection plans、latest DC2。
7. 编辑/修改/删除：只对克隆样本执行受控变更；原始真实设备禁止删除。
8. 清理：验收后 exact-code 删除全部 `D2LA_*` 克隆设备；Import Batch 不 purge，作为验收证据保留。

## 当前未决问题

No unresolved workstream policy questions remain. WS6 confirms P0 can go live with explicit human-accepted `ACCEPTED RISK`; final readiness must distinguish Device V2 入库工作台 and 设备 V2 清册管理.
