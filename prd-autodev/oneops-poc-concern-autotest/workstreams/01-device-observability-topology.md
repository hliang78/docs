# WS-01 设备纳管、监控日志与拓扑

## Focus

覆盖 PoC TC-01 到 TC-06：设备对象基础、自动监控、日志监听、集中看板、集中日志、网络拓扑。

2026-05-14 confirmed: split this area into four independent online quality sub-gates:

- Device: use each device's maximum verifiable field set from collected evidence plus platform fields to judge collection, parsing and storage correctness; avoid one-size-fits-all field requirements.
- Monitoring: task delivery, task governance, Prometheus data, and correct metric labels.
- Topology: Device V2 onboarding data + collection method -> obsflow L2 snapshot -> frontend topology display/drill-down.
- Logging: log-forward apply -> device-side log trigger -> Loki receives correct log.

## Repository Anchors

- Frontend: `OneOPS-UI/src/views/device`, `OneOPS-UI/src/views/platform/Monitoring*`, `OneOPS-UI/src/views/dashboard`, `OneOPS-UI/src/api/topology`.
- Backend: `OneOPS/app/device`, `OneOPS/app/device_collection`, `OneOPS/app/device_collection2`, `OneOPS/app/obsflow`, `OneOPS/app/monitor`, `OneOPS/app/topology`.
- Scripts/tests: D2 smoke scripts, monitoring/log/topology scripts under `OneOPS/scripts`.

## Draft Acceptance Shape

- 设备入库/导入有字段一致性和唯一性证据。
- 设备字段门禁按每台设备的最大可验证字段集判断，不同设备允许字段差异。
- 监控/日志不只验证页面可达，还能证明任务、数据或查询结果存在。
- 拓扑能说明节点、链路、钻取或差异记录。

## Confirmed Planning Decisions

- Fixture source: use existing MySQL test database at `192.168.0.199:3306`, database `zb_firewall_199`, user `root`, `autoMigrate=true`. Do not persist the database password in PRD artifacts; automation should receive it from environment variables or a local secret source.
- Fixture preparation: `ONEOPS_GATE_*` fixtures must be prepared before publishing OpenClaw automation stories.
- Monitoring P0 metric set: network devices only, using `ping`, `snmp`, and `snmp_interface`.
- Deferred metrics: NVR metrics are out of scope until NVR test devices exist; server SNMP is deferred until server-side configuration is prepared.
- Monitoring governance P0: delivery, status, retry/sync, Prometheus queryability, and correct labels.
- Deferred monitoring governance: drift/diff/repair requires prepared drift data and is P1+.
- Tail log paths: `/var/log/messages` and `/var/log/syslog`.
- Syslog trigger: build an SSH/netlink-based utility that enters network-device config mode and triggers deterministic syslog through config save. Cisco uses `wr`; H3C and Huawei use `save`.
- Topology drill-down: first story may mark drill-down as `BLOCKED` if fixture interfaces are not ready, but final WS-01 Done requires drill-down evidence.

## Remaining Open Questions

- 首批是否允许启动本地后端和前端服务做浏览器证据？
- 需要列出数据库中实际可用的 `ONEOPS_GATE_*` fixture 设备、服务器、tenant、IP、厂商和型号。
- 详细发现见 `../discovery-device-observability-topology.md`。
