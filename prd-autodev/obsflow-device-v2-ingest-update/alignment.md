---
topic: obsflow-device-v2-ingest-update
kind: backend
title: obsflow 基于 Device V2 入库候选源更新
createdAt: 2026-05-19T07:49:09+0800
---

# Alignment

## Proposed Direction

- 在 `DeviceCollectionCandidateSource` 内增加 Device V2 候选读取路径。
- 若 `platform_devices_v2` 存在，先读取 Device V2 候选；再读取旧 `device` 表候选作为补位。
- 以 `device_code` 去重，相同 code 时 Device V2 候选优先。
- 从 `attributes_json/metadata_json/platform_code` 提取 obsflow 所需的最小字段，不引入完整 Device V2 模型依赖。
- 非网络 catalog 继续过滤，只允许 `switch/router/firewall` 进入候选。

## Options

- 方案 A：完全切换到 Device V2。风险是未迁移旧资产会从 obsflow workflow 中消失。
- 方案 B：V2 优先、旧表补位。能承接入库新设备，同时保留迁移期兼容性。
- 方案 C：只保留旧表，并要求 Device V2 入库同步旧表。会把入库和 obsflow 耦合回旧资产表。

选择方案 B。

## User Decisions

- 用户明确要求：该更新不通过自动化机制实现，在当前 Codex 会话中实现。
- 本轮不发布 OpenClaw stories，不启动 loop。
