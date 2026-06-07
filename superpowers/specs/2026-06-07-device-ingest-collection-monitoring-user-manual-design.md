# Device ingest, collection, and monitoring user manual design

## 1. Goal

Create a customer-facing user manual for the OneOps device flow:

```text
prepare device data
  -> import or create device
  -> find the device in Device V2 management
  -> run device collection
  -> review collection result and logs
  -> run monitoring onboarding
  -> review monitoring push result
  -> confirm task state in monitoring task management
```

The manual must help a first-time customer complete the main task without needing to understand backend services, API contracts, or internal development tools.

## 2. Audience

Primary audience:

1. Customer operations engineers who are using OneOps for the first time.
2. Platform operators who need to import devices, collect device facts, and enable monitoring.

Assumed knowledge:

1. They know the target device IP address and login method.
2. They know whether the target is a server, network device, firewall, or generic device.
3. They may not know OneOps concepts such as Device V2, collection target, monitoring task, strategy set, Agent, or syslog listener.

The manual must explain these terms only when they affect an operation. It must not introduce implementation concepts unless the UI itself exposes the term.

## 3. Source boundaries

Use these source areas as the product truth:

1. Device management page: `/#/device/device-v2-management`.
2. Device import page: `/#/device/device-v2-ingest-pipeline-redesign`.
3. Collection target management page: `/#/platform/collection-target-management`.
4. Monitoring task management page: `/#/platform/monitoring-tasks`.
5. Existing Device V2 onboarding observability docs under `docs/development/device-v2-onboarding-observability/`.
6. Existing frontend code and Playwright tests under `OneOPS-UI/src/views/device/` and `OneOps/scripts/platform2_multi_agent_test/`.

Do not present deprecated onboarding APIs or development-only tools as customer operations.

## 4. Deliverables

### 4.1 User manual

Create:

```text
docs/user-manual/device-ingest-collection-monitoring.md
```

This file is the main readable manual.

### 4.2 Screenshot assets

Create:

```text
docs/user-manual/assets/device-ingest-collection-monitoring/raw/
docs/user-manual/assets/device-ingest-collection-monitoring/annotated/
```

Raw screenshots are kept for maintenance. Annotated screenshots are used in the manual.

### 4.3 Screenshot manifest

Create:

```text
docs/user-manual/assets/device-ingest-collection-monitoring/screenshot-manifest.md
```

The manifest records screenshot name, page route, capture condition, annotation targets, and whether the screenshot is required for the first release.

### 4.4 Review checklist

Create:

```text
docs/user-manual/device-ingest-collection-monitoring-review.md
```

This file contains the novice review checklist and final handoff checks.

## 5. Manual structure

Use this table of contents for the first version:

```markdown
# 设备入库、采集和监控纳管使用手册

## 1. 新手先看：这三件事分别是什么
## 2. 准备设备资料
## 3. 导入或创建设备
## 4. 在设备清单中找到设备
## 5. 执行设备采集
## 6. 查看采集结果和采集日志
## 7. 执行监控纳管
## 8. 查看监控下发结果
## 9. 在监控任务管理中确认状态
## 10. 批量操作怎么用
## 11. 常见问题
## 12. 完成检查清单
```

The manual should stay close to the main path. Advanced topics belong in small optional sections, not in the main flow.

## 6. Per-section format

Each operation section uses the same structure:

```markdown
## N. Section title

你会完成什么：
用一句话说明这一节结束后，用户能完成什么可见结果。

开始前确认：
- 用户需要准备的输入、权限或前置状态。
- 如果没有这些条件，本节先不继续操作。

操作步骤：
1. 打开页面或菜单。
2. 点击界面上可见的按钮或菜单项。
3. 填写必填字段。
4. 提交、保存或启动动作。

怎么看是否成功：
- 写出用户能看到的状态、列表行、标签、抽屉或提示消息。

如果失败：
- 写出错误出现在哪里。
- 给出最先检查的一两项，例如凭据、网络、端口、设备类型或必填字段。

截图：
![一句话说明截图目的](assets/device-ingest-collection-monitoring/annotated/xx-name.png)

可选：
- 只放和当前步骤直接相关的增强能力。
```

This format is intentionally repetitive. A new user should not need to relearn the manual pattern in each chapter.

## 7. Screenshot policy

### 7.1 Required screenshots

The first version should include annotated screenshots for:

1. Device management entry and device list.
2. Device import entry.
3. Device list search or filter.
4. Single device action menu with `采集`.
5. Collection result drawer.
6. Structured collection result or collection log entry.
7. Single device action menu with `监控`.
8. Monitoring result drawer.
9. Monitoring task management page.
10. Monitoring task detail or sync status.

### 7.2 Optional screenshots

Add only if the relevant UI is stable and useful to a new user:

1. Batch collection confirmation.
2. Batch monitoring confirmation.
3. Edit device drawer for missing monitoring fields.
4. Download collection log.

### 7.3 Screenshots to avoid

Avoid screenshots for:

1. Pagination, refresh, and ordinary table sorting.
2. Every dropdown expanded state.
3. Every field being typed.
4. Development or debug-only pages.
5. Similar result drawers that repeat the same idea.

## 8. Screenshot annotation rules

Use red boxes and numbered markers to highlight important choices.

Rules:

1. Keep one raw screenshot and one annotated screenshot.
2. Use red boxes for exact buttons, menu items, important status badges, and critical fields.
3. Use numbered circles when a screenshot has more than one action point.
4. A single screenshot may have at most three highlighted points.
5. If more than three points are needed, split the step into multiple screenshots.
6. Do not cover values that the user must read.
7. Mask or replace sensitive values before publishing: IP address, device code, account name, credential reference, real organization name, and internal hostnames.
8. The caption explains the operation purpose, not the UI design.

Suggested file naming:

```text
raw/01-device-list.png
annotated/01-device-list-key-actions.png
raw/02-device-import-entry.png
annotated/02-device-import-entry.png
```

The first implementation may use manual annotation. If the screenshot set grows or needs frequent refresh, add a repeatable annotation script later.

## 9. Language rules

Use direct user-facing Chinese.

Preferred style:

1. Use "你需要填写设备 IP" instead of "用户需完成资源实例属性配置".
2. Use "看到状态为成功，说明这一步已经完成" instead of "链路闭环已完成".
3. Use "检查账号、密码、端口和网络连通性" instead of "排查协议层连接异常".
4. Explain terms on first use, for example: "监控模板：一组预设的监控指标和阈值。"
5. Keep steps short: where to go, what to click, what to fill, how to judge the result.

Avoid:

1. Internal implementation terms such as model, orchestration, pipeline, DTO, controller-backed, ledger, runtime projector, unless the UI displays them.
2. Broad claims such as "形成完整闭环" unless followed by concrete user-visible checks.
3. Long paragraphs that mix goal, operation, and troubleshooting.
4. AI-sounding filler, promotional language, or vague statements.

After drafting the manual, apply the `humanizer` process:

1. Scan for AI writing patterns.
2. Rewrite into natural, plain Chinese.
3. Check again for remaining tells.
4. Produce the final manual text without over-polishing it into developer documentation.

## 10. Novice review checklist

Use this checklist after the first draft:

1. Does each chapter start by saying what the user will accomplish?
2. Does each workflow have a prerequisite list?
3. Does each step name the page, button, field, and success state?
4. Does the manual avoid "configure related parameters" without saying which parameters matter?
5. Does every main operation have a visible success standard?
6. Does every failure path tell the user where to see the error and what to check first?
7. Does the manual separate required steps from optional capabilities?
8. Does it tell the user when to use single-device operation and when to use batch operation?
9. Are terms explained the first time they appear?
10. Can a first-time user finish one full device path without jumping across unrelated chapters?
11. Do screenshots appear where the user may lose their place?
12. Does the final checklist confirm device imported, collection result visible, monitoring pushed, and task state traceable?

## 11. Acceptance criteria

The documentation work is complete when:

1. The main manual exists and follows the approved structure.
2. The screenshot manifest lists all required screenshots and annotation targets.
3. Required screenshots are either present or have explicit placeholders with capture instructions.
4. The manual has gone through the `humanizer` review.
5. The novice checklist has been applied, with remaining issues documented.
6. No development-only route, deprecated API, or internal-only tool is presented as a customer path.

## 12. Implementation stages

Stage 1: Write the manual skeleton and screenshot manifest.

Stage 2: Fill the first draft from current UI and docs.

Stage 3: Capture or reuse screenshots, then create annotated versions.

Stage 4: Run the novice review checklist and revise.

Stage 5: Apply `humanizer` and produce the final manual.

Stage 6: Run a final link and asset check.

Stage 7: If the manual generation flow passes review and can be repeated, extract it into a reusable Codex skill.

## 13. Reusable skill plan

Create a reusable skill only after the first manual passes implementation review. The skill should capture the repeatable method, not this one manual's final text.

Recommended skill name:

```text
oneops-user-manual-generator
```

Recommended location:

```text
$CODEX_HOME/skills/oneops-user-manual-generator/
```

Use the skill when a future task asks to create or update a OneOps customer-facing user manual, especially for workflows that need UI screenshots, red-box annotations, novice review, and `humanizer` cleanup.

The skill should include:

1. A short `SKILL.md` with trigger conditions and the core workflow.
2. A reusable manual section template.
3. A screenshot manifest template.
4. A novice review checklist.
5. A screenshot annotation checklist.
6. Optional helper scripts only after the annotation process becomes repetitive enough to justify automation.

The skill should not include:

1. The full generated manual text.
2. Project-specific screenshots.
3. Large UI source excerpts.
4. One-time implementation notes.

Skill validation should follow the `writing-skills` approach:

1. Try a small manual-generation prompt without the skill and record where the result is weak.
2. Create the skill to address those weaknesses.
3. Run a fresh prompt with the skill enabled.
4. Check whether the result follows the manual template, creates screenshot instructions, avoids internal implementation language, and includes novice review gates.

## 14. Fixed decisions for implementation

1. The first draft may reuse existing Playwright and UX screenshots only when they match the current page. Missing screenshots must be represented by explicit capture instructions in the manifest.
2. The first publishable version should use annotated screenshots for the required screenshot list. If a local environment is not available, the manual may keep visible screenshot placeholders, but the review file must mark them as release blockers.
3. Firewall-specific collection and monitoring notes stay out of the first manual. Add them later as a small addendum after the firewall platform upgrade MVP stabilizes.
4. The first implementation will not add an annotation script. Manual annotation is acceptable for the first version because the screenshot set is small.
