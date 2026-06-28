---
topic: aidc-business-workbench-rollout
kind: frontend
title: AIDC 全业务页面工作台统一改造
createdAt: 2026-06-25T11:11:00+0800
program: true
---

# Program Context Brief

## Goal

将 `aidc-web` 的全部业务页面统一为专业、简洁、列表优先的工作台形态，并把已经完成的页面纳入同一轮一致性回归。

## Scope

已完成工作台化的页面：

1. `companies`
2. `messages`
3. `hunts`
4. `contracts`

本轮继续完成的页面：

1. `collections`
2. `outreach`
3. `radar`
4. `supply`
5. `workflows`

## Boundaries

1. 以现有前端能力和已有接口为基础，不主动发明新后端契约。
2. 后端不可用时要如实暴露真实错误，不引入 mock、伪成功、静默 fallback。
3. 优先复用已有工作台语言，但不强行抽成过度通用的大组件。
4. 本轮重点是业务页内部结构统一，不重做登录页、系统设置页或全局壳层。

## Priority Focus

1. 让剩余 5 个页面进入统一工作台节奏。
2. 保住原有深链、筛选参数和关键操作。
3. 为自动化执行准备可分批、可验证的故事包。

## Background

用户已经明确确认目标风格为“专业、简洁、以列表为主的工作台”，并且此前已经按 `消息中心 -> 猎单管理 -> 合同回款` 的顺序完成了重点页面改造。当前需要把剩余页面和整体一致性一起收口。

## Concerns

1. `outreach` 与 `radar` 页面的交互较重，容易把结构改造做成大杂糅。
2. 后端代理错误会影响浏览器验证节奏。
3. 如果共性抽象过早，可能拖慢页面逐个落地。

## Open Questions

当前没有阻塞问题，默认继续生成 program、story batches 与禁用态 OpenClaw 任务。
