---
topic: obsflow-l2-association-upgrade
kind: backend
title: obsflow DevicePorts/ArpTableServer/L2NodeMapServer 升级
createdAt: 2026-05-25T01:20:53+0800
program: true
---

# Idea

## Original Input

对 obsflow 进行深入分析，整理旧 DevicePorts、ArpTableServer、L2NodeMapServer 的执行链并在 obsflow 中复刻逻辑；同时围绕主机名、接口、MAC、IP、IFINDEX 等少数核心概念，提升域名追加、接口简写、空格、大小写、MAC 格式等多种字符串形态下的匹配成功率。

## Known Constraints

- TBD
