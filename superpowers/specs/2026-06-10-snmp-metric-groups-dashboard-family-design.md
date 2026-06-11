# SNMP Metric Groups And Dashboard Family Design

Date: 2026-06-10

## Purpose

Make SNMP performance monitoring a first-class configuration experience while preserving a clean path to future Grafana dashboard generation.

The current phase focuses on SNMP strategy configuration. Grafana generation is not implemented in this phase, but the SNMP strategy must store enough metric-group and panel semantics so a later Grafana integration can generate, update, diff, and trace dashboards without reverse-engineering low-level collection configuration.

## Current System Facts

The existing system already has the right high-level objects:

- Teleabs strategies support parent and child strategies.
- Child strategies can bind manufacturer, device model, catalog, platform, and version range.
- Strategy sets compose strategies into a monitoring solution.
- Strategy sets bind to root Grafana dashboards through `platform_teleabs_strategy_set_dashboard_binding`.
- Grafana dashboards support root and child dashboards via `parent_id`.
- Grafana dashboard variants already support manufacturer, device model, catalog, and platform fields.
- Device dashboard lookup already resolves from applied strategy set to root dashboard, then chooses a matching child dashboard by device profile.
- Metric assets already track declared metrics at template, strategy, or task-manifest scope.

The main gap is between strategy metrics and dashboard panels. The platform can find which dashboard a device should open, but cannot yet trace which dashboard panel comes from which strategy, metric group, or metric asset.

## Correct Relationship Model

The system should use these boundaries:

```text
StrategySet
  = one monitoring solution
  = binds one root dashboard, which acts as the dashboard family entry

DashboardFamily
  = one root dashboard name/code plus its child variants
  = contains root and child dashboard variants

DashboardVariant
  = one concrete Grafana dashboard JSON
  = optional manufacturer/platform/model/catalog match conditions

Strategy
  = one monitoring capability source
  = provides metric groups
  = does not directly bind a dashboard

MetricGroup
  = a semantic group of metrics
  = maps to one or more panel specs

PanelSpec
  = a stable panel generation contract
  = can later become a Grafana panel
```

The full trace should be:

```text
strategy_set_id
  -> root_dashboard_code
    -> dashboard_code
      -> panel_key / panel_id
        -> metric_group_key
          -> strategy_id
            -> metric_key / metric_asset_id
```

This means:

- A strategy set maps to one root dashboard family entry, not to a single dashboard variant.
- A strategy contributes metric groups to the strategy set.
- Metric groups define panel contracts.
- Concrete dashboard variants carry the final panels.
- Panels must remain traceable back to strategy set, strategy, metric group, and metrics.

## Page Design

The SNMP strategy editor should be planned as a three-area workspace.

### Left: Strategy Context

Show only information the user needs to make configuration decisions:

- parent strategy
- current strategy
- inheritance mode
- manufacturer
- platform
- model
- matched MIB metric library
- metric group list
- group action state: inherit, add, override, disable

Connection and low-frequency technical fields must not be displayed by default. They belong in advanced settings:

- credential binding
- SNMP version
- timeout
- retries
- collection interval
- MIB tree file override
- manual base selection

The UI should not expose implementation-specific collection engine terms.

### Center: Metric Group Editor

The main editing surface focuses on one metric group at a time.

For each group, users can configure:

- `metric_group_key`
- display name
- entity type, such as device, interface, sensor, module
- inherited, added, overridden, or disabled status
- fields
- field role: dimension or metric
- metric key
- display name
- unit
- value type
- calculation mode
- data shape
- panel specs

Preset vendor groups should provide defaults. Users should not need to process every default field. Custom groups expose more choices because their shape cannot be inferred safely.

### Right: Strategy Set And Dashboard Impact

This panel is an impact preview, not a Grafana editor.

It shows:

- strategy sets that include this strategy
- root dashboard family bound to each strategy set
- current device profile match context
- metric groups affected by the change
- panel specs affected by the change
- whether a future dashboard variant can be generated or diffed

This keeps Grafana integration visible as an outcome without forcing users to edit dashboard JSON during SNMP strategy work.

## Metric Group Contract

The SNMP strategy should save a metric group contract. The first implementation may store it inside strategy parameters JSON; later it can be promoted to tables.

Example shape:

```json
{
  "metric_groups": [
    {
      "group_key": "interface_basic",
      "name": "接口基础指标",
      "entity": "interface",
      "action": "inherit",
      "source": {
        "manufacturer_id": "h3c",
        "platform_id": "comware",
        "mib_profile_key": "h3c_comware"
      },
      "fields": [
        {
          "metric_key": "if_name",
          "name": "接口名称",
          "role": "dimension",
          "value_type": "string"
        },
        {
          "metric_key": "if_in_rate",
          "name": "入方向流量",
          "role": "metric",
          "unit": "bps",
          "value_type": "number",
          "calculation": "rate",
          "visual_hint": "timeseries"
        }
      ],
      "panel_specs": [
        {
          "panel_key": "interface_basic.traffic",
          "title": "接口流量",
          "visual_type": "timeseries",
          "metrics": ["if_in_rate", "if_out_rate"],
          "dimensions": ["if_name"],
          "unit": "bps"
        },
        {
          "panel_key": "interface_basic.status",
          "title": "接口状态",
          "visual_type": "table",
          "metrics": ["if_admin_status", "if_oper_status"],
          "dimensions": ["if_name"]
        }
      ]
    }
  ]
}
```

Stable keys are mandatory:

- `metric_group_key`
- `metric_key`
- `panel_key`

Do not use Chinese display names, Grafana panel titles, or Grafana numeric panel IDs as stable identity.

## Inheritance Rules

Parent and child strategies inherit at metric-group level.

Allowed group actions:

- `inherit`: child uses the parent group unchanged.
- `add`: child adds a group not present in the parent.
- `override`: child replaces or patches a parent group.
- `disable`: child suppresses a parent group.

Override scope should be explicit:

- group-level override
- field-level override
- panel-level override

Example:

```json
{
  "group_key": "system_health",
  "action": "override",
  "override_scope": ["field", "panel"]
}
```

The effective strategy contract is computed as:

```text
effective_groups = parent_groups
  - disabled_groups
  + added_groups
  + overridden_groups
```

## Vendor And MIB Loading

Vendor selection should drive MIB simplification:

1. User selects manufacturer, platform, and optional model.
2. UI resolves a MIB profile.
3. MIB profile points to supported metric groups and base OID entries.
4. Existing MIB field API loads children from the configured Nacos MIB tree file.
5. User selects fields and roles only where necessary.

The default Nacos-configured MIB tree file should be used without asking the user to choose it. MIB file override belongs in advanced settings.

When no vendor profile matches:

- fall back to a generic SNMP profile
- allow custom group creation
- keep advanced manual selection available

## Panel Spec Semantics

Panel specs are not Grafana panels yet. They are platform-owned display contracts.

Supported visual types:

- `stat`
- `gauge`
- `timeseries`
- `table`
- `pie`
- `bar`
- `topn`

Supported data shapes:

- `single`
- `timeseries`
- `table`
- `category`
- `topn`
- `table_timeseries`

Preset metric groups should define panel specs automatically. Custom groups should ask users for the minimum extra information needed:

- data shape
- field roles
- unit
- calculation
- grouping dimension
- enum mapping when needed
- default visual type

## Future Grafana Integration

Future Grafana integration should consume the stored contracts rather than parsing low-level collection configuration.

Generation flow:

```text
1. Resolve applied strategy set for a device.
2. Resolve the root dashboard family bound to the strategy set.
3. Resolve matching child dashboard variant using manufacturer/platform/model/catalog.
4. Resolve effective strategies and metric groups for the device.
5. Convert panel specs into Grafana panels.
6. Record panel bindings for traceability.
7. Preview diff before writing dashboard JSON.
8. Sync to Grafana only after user confirmation or configured automation.
```

Panel binding should eventually record:

```text
strategy_set_id
dashboard_code
panel_key
panel_id or panel_uid
strategy_id
metric_group_key
metric_keys
managed_state
content_hash
```

Managed state:

- `managed`: platform may update this panel.
- `manual`: user-managed panel; platform must not overwrite automatically.
- `detached`: generated before, but no longer tied to an active contract.

## Phase Scope

This phase implements SNMP strategy configuration and contract persistence only.

In scope:

- SNMP-specific strategy form replacing the generic parameter-only experience for SNMP.
- Manufacturer/platform/model driven MIB profile selection.
- MIB field loading using the existing MIB tree file behavior.
- Metric group editing.
- Field role, unit, value type, calculation, and visual hints.
- Panel spec preview.
- Parent/child metric group inheritance states.
- Strategy set and dashboard family impact preview based on existing bindings.
- Saving metric group and panel spec contracts in strategy parameters.

Out of scope:

- Generating Grafana dashboard JSON.
- Updating existing Grafana panels.
- Creating panel binding tables.
- Full dashboard diff and rollback.
- Data source query builder beyond enough metadata for future generation.

## Risks And Controls

Risk: users are overwhelmed by too many defaults.

Control: preset vendor groups hide defaults unless the user chooses to override. Custom groups show more fields because they need explicit semantics.

Risk: future Grafana generation cannot identify panels.

Control: require stable `panel_key`, `metric_group_key`, and `metric_key` now.

Risk: generated panels overwrite user edits later.

Control: future phase must use managed/manual panel state and content hashes.

Risk: strategy matching and dashboard variant matching diverge.

Control: both must use the same match context: manufacturer, platform, model, catalog, and version.

Risk: raw metric names change.

Control: metric keys remain stable at the strategy contract level and map to concrete metric assets.

## Acceptance Criteria

- User can configure SNMP strategy without seeing low-level collection implementation details.
- User can select manufacturer/platform/model and get a matched MIB profile.
- User can manage metric groups as inherit/add/override/disable.
- User can configure custom metric groups with data shape and visual hints.
- Saved strategy parameters contain metric groups and panel specs with stable keys.
- UI can show which strategy sets and root dashboard families will be affected.
- No Grafana generation is required in this phase, but stored data is sufficient for later panel generation and traceability.

## Self-Review Notes

- No implementation-specific UI labels are required in the proposed page.
- The design distinguishes strategy, strategy set, dashboard family, dashboard variant, metric group, and panel spec.
- The first phase is limited to SNMP and contract persistence.
- Future Grafana integration has a clear data path but is explicitly out of scope for this phase.
