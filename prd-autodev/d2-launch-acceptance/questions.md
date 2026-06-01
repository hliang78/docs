# Device V2 上线验收问题轮

UpdatedAt: 2026-05-14T13:25:00+0800

## Round 001

这些问题会决定 PRD 和第一批 OpenClaw stories 是否可以安全发布。

1. DB 抽样规模和条件怎么定？
   - Confirmed: 5 台真实 Device V2 设备，每种类型优先选 1 台；只选管理地址/access points 可用、已有凭证引用、采集协议明确的记录。

2. 导入使用克隆 code 还是同 code 更新？
   - Confirmed: 默认 `D2LA_<orig_code>` 克隆导入，保留原始 code 映射，这样可以用真实 IP 和凭证引用采集，但不覆盖原记录。
   - 如果需要验收同 code update，请先确认允许对哪 1 台设备做快照后更新。

3. 凭证信息怎么处理？
   - Confirmed: 只导出 credential refs、协议、端口、access point 关系，不导出明文密码、token、community secret、private key。
   - 如果你确认系统采集必须依赖某类 secret，请通过已有凭证管理系统引用，不能贴到聊天或 story 里。

4. 真实采集机制怎么定？
   - Confirmed: 不指定 SNMP/SSH/WinRM/DC2；采集通过 controller detect 机制实现，验收只需准备好凭证引用和 access_points。

5. store story 粒度是否按单设备、单阶段执行？
   - Confirmed: 开始测试 1 台设备；单设备打通后，再做 5 台并行采集测试。每个阶段仍拆 story。

6. 测试数据是否允许删除？
   - Confirmed: exact-code 删除全部 `D2LA_*` 克隆样本。
   - Confirmed: 原始真实设备记录禁止删除；Import Batch 保留证据，不 purge。

7. 上线验收的 go/no-go 标准是什么？
   - Confirmed: P0 可带明确 `ACCEPTED RISK` 上线，但必须列出残余风险并由人工接受。

## Round 002

WS2 DB-derived Excel import decisions are confirmed:

1. Import entry: use the "Device V2 入库工作台" upload UI.
2. Field scope: include code/name/type/platform/status/管理 IP/access_points/credential refs/协议端口/labels/metadata/orig mapping.
3. Original-code mapping: use `labels.d2la_orig_code`.
4. Incomplete data: allowed for validation testing; skipped unusable device types must be recorded as exclusions.
5. Lifecycle: upload/validate first; apply only after validation succeeds or expected validation failures are documented.

## Round 003

WS3 Backend contract/test gate decisions are confirmed:

1. d2-be may run `go test ./app/device/v2/...` and `go test ./app/device/v2/ingest/...`.
2. Small Device V2 backend fixes are allowed for field/DTO/mapping/error/read-only export gaps.
3. Writes are limited to Device V2 backend paths unless further approval is granted.
4. Contract evidence should include `backend-contract-snapshot.md` and API example responses where useful.
5. Real DB or external collection environment failures should be marked `environment-blocked`.

## Round 004

WS4 Real collection evidence decisions are confirmed:

1. Collection is controller detect based; stories should not force a protocol.
2. First prove the path with 1 imported cloned device, then run 5-device parallel collection.
3. Prefer store/start from the management UI; API trigger is allowed if UI is blocked and reason is recorded.
4. If polling exceeds the story budget, persist task status and next polling step.
5. Empty observations/DC2 should be classified as business-empty, credential-blocked, network-blocked, backend-contract-blocked, environment-blocked, or unknown.

## Round 005

WS5 Edit/delete/cleanup policy decisions are confirmed:

1. `D2LA_*` cloned devices may be deleted.
2. Original real Device V2 records must not be deleted.
3. Edit/update testing is required and should target cloned devices only.
4. Import Batch records should not be purged; keep them as acceptance evidence.
5. Desired final state is clean teardown: all cloned devices deleted after evidence is captured.

## Round 006

WS6 Launch readiness report decisions are confirmed:

1. P0 may launch with explicit human-accepted `ACCEPTED RISK`.
2. Report artifacts should include `evidence-index.md`, `launch-readiness-report.md`, risk table, and PASS/BLOCKED/ACCEPTED RISK status.
3. Final conclusions must distinguish Device V2 入库工作台 and 设备 V2 清册管理.
4. If 5-device parallel collection partially fails, human decides final PASS/BLOCKED/ACCEPTED RISK.
5. Final report must include must-fix-before-launch and post-launch-watch-list.
