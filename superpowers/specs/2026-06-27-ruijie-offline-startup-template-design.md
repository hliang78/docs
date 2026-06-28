# Ruijie Offline Startup Template Design

Date: 2026-06-27

## Purpose

Define the first reusable OneOPS-standard way to initialize the current Ruijie firewall image offline.

The immediate goal is not full device automation. The immediate goal is to turn the already-proven Ruijie `LYB` startup-file path into a stable, repeatable asset that can be used by later real-device tests while meeting the same management baseline used for other validated devices.

## Background

Current verified facts on `Ruijiefirewall-V1.03`:

1. The device boots stably in EVE.
2. Default management is on `Ge0/0`.
3. `flash:/sysrepo/startup/*.startup` is stored as `LYB`.
4. The `LYB` files can be decoded and regenerated offline inside the vendor rootfs toolchain.
5. Replacing `ntos-interface.startup` offline has already been proven to bring the node up on `172.32.2.11/24`.
6. `admin / admin@123` SSH login has already been proven after that replacement.

This means Ruijie is no longer blocked on basic initialization feasibility. It is now ready for standardization.

## User Goal

The user wants:

1. A script plus manual path, not a one-off experiment.
2. A common documentation baseline that can later guide more device families.
3. A first version that is stable, evidence-driven, and narrow enough to trust.
4. Ruijie should not be considered complete unless it reaches the same management baseline as other devices:
   - independent management VRF
   - management default route
   - SSH
   - standard management address

## Scope

In scope for this design:

1. Generate new Ruijie startup files from an existing validated baseline.
2. Use a common parameter model with a Ruijie-specific adapter.
3. Output new `LYB` startup files without directly modifying EVE node disks.
4. Provide an operator runbook for replacement, reboot, and verification.
5. Render management VRF and management default route as first-class goals, not future placeholders.
6. Reserve structured extension points for business interfaces and OSPF.

Out of scope for this first version:

1. Direct modification of EVE node `qcow2` or overlay disks.
2. Direct modification of the encrypted Ruijie backup package.
3. Full topology deployment automation.
4. Full business-interface rendering.
5. Full firewall policy, object, NAT, or OSPF generation.
6. A vendor-neutral implementation for all device families in this round.

## Approaches Considered

### 1. Ruijie-only direct script

Pros:

1. Fastest to build.
2. Lowest first-round complexity.

Cons:

1. Harder to reuse when the same pattern is needed for Huawei or H3C.
2. Encourages vendor details to leak into the main workflow.

### 2. Common parameter model plus Ruijie adapter

Pros:

1. Best fit for the user's long-term multi-device testing target.
2. Keeps the operator interface stable while letting vendor mappings differ.
3. Makes later devices an adapter problem instead of a workflow rewrite.

Cons:

1. Slightly more design work up front.

Recommendation:

Use this approach.

### 3. Fixed string-replacement template

Pros:

1. Fastest possible proof-of-concept.

Cons:

1. Fragile against structure changes.
2. Poor fit for a long-lived testing baseline.
3. Hard to explain and maintain safely.

This approach is rejected for the mainline path.

## Recommended Design

Use a two-layer generator:

1. A common input model that defines what the operator wants.
2. A Ruijie adapter that knows how to map those values into specific startup modules.

The script generates startup files only. The manual handles file replacement, node restart, and evidence collection.

For Ruijie in this phase:

1. The management interface is fixed to `Ge0/0`.
2. This is an accepted Ruijie-specific exception to the wider "last interface as management interface" rule.
3. The template is not considered complete unless independent management VRF and management default route are also proven on top of that `Ge0/0` model.

## Deliverables

### 1. Script

Create:

`scripts/ruijie-startup-template.py`

Purpose:

1. Read validated baseline startup files.
2. Decode `LYB` to XML through the vendor toolchain environment.
3. Apply requested parameter changes through structured mappings.
4. Re-encode the result to `LYB`.
5. Write a new output directory containing rendered startup files and a summary manifest.

### 2. Runbook

Create:

`docs/testing/eve-ng-ruijie-firewall-offline-startup-template-standard.md`

Purpose:

1. Define baseline prerequisites.
2. Explain how to run the script.
3. Explain how to replace startup files in EVE manually.
4. Explain reboot and verification steps.
5. Record supported fields and known boundaries.

### 3. Existing boundary doc updates

Update:

`docs/testing/eve-ng-ruijie-firewall-initialization-boundary.md`

Purpose:

1. Keep the exploration history.
2. Link to the new standard runbook.
3. Keep tested and untested boundaries explicit.

## Script Architecture

### 1. Common parameter layer

The operator-facing input model should support:

1. `hostname`
2. `mgmt_interface`
3. `mgmt_ip`
4. `mgmt_prefix`
5. `mgmt_gateway`
6. `ssh_enabled`
7. `admin_password`
8. `mgmt_vrf_name`
9. `business_l3_links`
10. `ospf`

Not all of these need active rendering in version 1, but all should exist in the contract so the interface does not churn later.

### 2. Ruijie adapter layer

The Ruijie adapter is responsible for:

1. Loading required YANG modules.
2. Decoding baseline `LYB` startup files.
3. Mapping common parameters into Ruijie XML trees.
4. Emitting only the modules that were changed.

Initial module ownership:

1. `ntos-interface.startup`
   - management interface IP
   - management interface SSH enable
   - management interface selection
2. `ntos-system.startup`
   - hostname
   - optional admin password handling, if safely implemented
3. `ntos-routing.startup`
   - management default route
   - route placement relative to management VRF
4. `ntos-xvrf.startup`
   - independent management VRF
   - management VRF bindings if the image truly supports them

### 3. Output layer

The script should write to a fresh output directory, for example:

`tmp/ruijie-startup-output/<timestamp>/`

That directory should contain:

1. rendered `*.startup` files
2. a `render-summary.json`
3. a `render-input.json`
4. optional readable XML snapshots for audit/debug

The script must not overwrite EVE node disks in version 1.

## Input and Output Contract

### Input

The first version should support:

1. a baseline directory containing validated Ruijie startup files
2. a JSON input file describing requested parameter values

Optional CLI flags may override selected fields, but the JSON file should be the main contract because it is easier to archive with test evidence.

### Output

The output contract should guarantee:

1. no in-place modification of baseline files
2. deterministic output directory content
3. explicit reporting of which startup modules changed
4. explicit reporting of fields accepted but not yet rendered

## Version 1 Rendering Scope

### Must support

1. management interface selection, fixed to `Ge0/0` for the current Ruijie image
2. management IPv4 address and prefix
3. management-plane SSH enable or disable
4. independent management VRF rendering
5. management default route rendering
6. new `LYB` output generation
7. render summary generation

### May support if implementation stays clean

1. hostname
2. admin password replacement

### Reserved but not claimed as complete

1. business interface bulk rendering
2. OSPF rendering

These fields should stay in the common contract but be reported as `reserved_not_rendered` until proven.

## Operational Flow

The standard operator flow should be:

1. Export or collect a validated Ruijie startup-file baseline.
2. Prepare a parameter JSON file.
3. Run the generator script.
4. Review the summary and optional XML diff.
5. Replace the target startup files in EVE manually.
6. Reboot the node.
7. Verify management IP, SSH, and minimal config state.
8. Archive generated files and verification evidence with the test record.

## Error Handling

The script should fail hard and clearly when:

1. required startup files are missing
2. required YANG modules cannot load
3. baseline `LYB` cannot be decoded
4. a requested parameter targets a path the current Ruijie adapter does not support
5. validation fails before re-encoding

The script should not silently skip a requested field unless it is explicitly marked as reserved and reported in the summary.

## Verification Standard

Version 1 should only be considered successful if all of these are true:

1. The script produces a fresh output directory with new `LYB` files.
2. The changed startup files can be substituted into a Ruijie node without boot failure.
3. The node comes up on the rendered management IP.
4. The node presents an independent management VRF, not just the default `main` table.
5. The management default route is present in the expected VRF.
6. SSH login succeeds with the expected credentials when SSH is rendered on.
7. The render summary matches the actual observed device state.

## Risks and Boundaries

Known risks:

1. Ruijie backup packages remain encrypted and are not the right standardization surface for version 1.
2. The current image still behaves as a first-port management model, not a last-port management model.
3. `ethernet=20` still exposes only the first 8 ports as standard firewall interfaces.
4. Independent management VRF and default-route placement are now mandatory goals, but they are not yet proven in startup modules.
5. Password rendering may require special handling to avoid weak or image-specific hashing assumptions.

## Documentation Standard

The runbook must explicitly separate:

1. proven fields
2. reserved fields
3. unsupported fields
4. validated operator steps
5. evidence that must be captured

This is important because the same document pattern is intended to expand later to other device families.

## Implementation Readiness

This design is ready to move into a written implementation plan.

The first implementation slice should focus on:

1. baseline directory contract
2. JSON input contract
3. `ntos-interface.startup` rendering
4. `ntos-routing.startup` rendering investigation and mapping
5. `ntos-xvrf.startup` rendering investigation and mapping
6. output directory generation
7. summary manifest generation
8. standard runbook draft
