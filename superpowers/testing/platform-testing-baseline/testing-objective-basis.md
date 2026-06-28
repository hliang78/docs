# Testing Objective Basis

Purpose: record the user's original testing concern and the agreed interpretation as the highest-priority basis for Phase 1 testing decisions.

## User Original Statement

The user's original goal is:

> 我有一个明确的目标就是，希望尽量多的适配更多的设备。针对设备采集、监控推送、防火墙配置解析、策略生成、策略查询、拓扑生成、自动化脚本等过程需要测试覆盖。我希望交付给客户的平台具有稳定性、鲁棒性、可靠性、可用性、健壮性。

The user's additional clarification is:

> 第一阶段是围绕我的目标进行测试。

The user's latest emphasis is:

> 具体到测试我希望是针对一系列真实设备通过各种数据组合来验证各种场景，关键是分析薄弱环节，进行测试。需要有针对性的设计测试。

The user's additional constraint is:

> 允许不同设备有不同的登录账号

## Agreed Interpretation

The core concern is not simply "more tests", but "more delivery certainty".

What the testing baseline must prove:

- AI-accumulated functionality is not only present, but trustworthy under real data, edge cases, and scale.
- A device is not considered "supported" because one API succeeds once; it is only considered supported when its full capability chain is understood and verified.
- Device adaptation is inherently non-standard, so the platform must verify both support breadth and clear unsupported boundaries.
- Login credentials are part of device reality, not a forced unification target. Different device families may keep different standard login accounts as long as they are documented, reproducible, and explicitly included in the test evidence.
- Customer delivery risk is the real reference point: support scope, behavior stability, failure clarity, and large-scale operability must all be explainable with evidence.
- Phase 1 should not spread effort evenly across modules. It should use real-device samples, data combinations, and weak-link analysis to design deliberately targeted tests.

## Highest-Priority Testing Basis

Phase 1 testing decisions should always prefer the following questions over module-oriented coverage:

1. Which device families are truly supported?
2. For each supported family, which capability chains are actually verified end to end?
3. For each unsupported or partial case, is the boundary explicit and observable?
4. Can the platform remain stable, robust, reliable, usable, and resilient when data shape, protocol behavior, or scale changes?
5. Which real-device and data-combination scenarios expose the current weakest links first?
6. For each device family, are the real usable login entry and credential baseline clearly recorded, instead of being assumed to be globally uniform?

## Decision Rule

If a proposed test task improves customer-facing certainty about device adaptation, chain completeness, boundary clarity, or large-scale operability, it belongs in Phase 1.

If a proposed test task improves only local implementation confidence but does not strengthen delivery certainty, it is lower priority than the items above.
