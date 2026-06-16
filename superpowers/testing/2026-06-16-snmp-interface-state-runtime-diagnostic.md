# SNMP Interface State Runtime Diagnostic

Date: 2026-06-16

## Purpose

This note records the current evidence for why `Interface State by Module`
still looks abnormal on some `Maipu / MyPower` and `H3C / SecPath` devices
even after the generic panel logic was unified.

## Confirmed Codegen State

The dashboard generator now materializes the same `Interface State by Module`
panel behavior for:

- `Huawei / VRP`
- `H3C / Comware`
- `Maipu / MyPower`
- `H3C / SecPath`

Shared behavior:

- shared generic expression path
- `ifDescr -> ifName` fallback when `ifName=""`
- shared logical-interface exclude regex
- `sort_by_label_numeric(..., "ifIndex")`
- `orientation=horizontal`
- `textMode=value_and_name`
- `displayName=${__series.name}`

Conclusion:

`Comware` being normal while `MyPower` or `SecPath` look abnormal is no longer
a generator-branch problem. The remaining difference is runtime label shape.

## Runtime Evidence

### Maipu / MyPower

Sample inventory context already exists:

- device code: `DVCF21C6B43350C`
- manufacturer/platform: `Maipu / MyPower`
- model: `S4320`
- version: `9.5.0.3`

By-target panel preview acceptance already shows that this sample resolves the
interface status capability as supported:

- source: [snmp-by-target-panel-preview-acceptance-2026-06-11.md](/OneOPS/docs/superpowers/testing/snmp-by-target-panel-preview-acceptance-2026-06-11.md:784)

But several diagnostic logs also show repeated profile/detect mismatch for the
same vendor family:

- `config matching failed: no matching device config found for manufacturer=Maipu, platform=MyPower, version=9.5.0.3`
- source: [task-diagnostic-89c26b4d-c417-4ee7-a09d-dfb005e9d155.txt](/OneOPS/task-diagnostic-89c26b4d-c417-4ee7-a09d-dfb005e9d155.txt:1148)

Interpretation:

- the SNMP dashboard path can already resolve enough capability for MyPower
- but the wider device detect/profile path still has gaps for `MyPower 9.5.0.3`
- this makes it more likely that interface labels are inconsistent or less
  normalized than the `Comware` sample

### H3C / SecPath

`SecPath` is a firewall family, not a switch-first family. Existing corpus
already shows interface names that are structurally different from a clean
switch port list:

- `Vlan-interface100`
- source: [firewall-imported-config-route-segments-2026-06-09.csv](/OneOPS/docs/superpowers/testing/firewall-imported-config-route-segments-2026-06-09.csv:152)

- `Route-Aggregation1`
- source: [task-diagnostic-61be8458-eba1-491a-8bde-114271856f3e.txt](/OneOPS/task-diagnostic-61be8458-eba1-491a-8bde-114271856f3e.txt:40)

There is also prior strategy evidence confirming the sample family is a
firewall:

- `DVC65F6466753AB is FIREWALL + H3C SecPath`
- source: [2026-06-03-server-oob-real-device-test-handoff.md](/OneOPS/docs/superpowers/specs/2026-06-03-server-oob-real-device-test-handoff.md:275)

Interpretation:

- even after shared filtering, `SecPath` is still more likely to expose
  non-switch interface families than `Comware`
- `ifIndex` ordering improves stability, but it does not make a firewall
  interface table visually resemble a chassis switch module layout

## What To Inspect In Prometheus / Grafana Explore

Prefer `agent_host` when the dashboard already has that variable. The same
queries can be rewritten with `device_code`.

Replace `$agent_host` with the target host if needed.

Helper script:

```bash
python3 /OneOPS/quick_env/scripts/render_snmp_interface_state_diagnostic.py --agent-host 172.22.166.14
python3 /OneOPS/quick_env/scripts/render_snmp_interface_state_diagnostic.py --device-code DVCF21C6B43350C
python3 /OneOPS/quick_env/scripts/query_snmp_interface_state_diagnostic.py --prometheus-url http://127.0.0.1:9091 --agent-host 172.22.166.14
python3 /OneOPS/quick_env/scripts/query_snmp_interface_state_diagnostic.py --prometheus-url http://127.0.0.1:9091 --device-code DVCF21C6B43350C
```

If `--device-code` returns all-zero results, rerun with `--agent-host`. The
query helper now tries to resolve that host from local obsflow artifacts and
prints an exact `--agent-host` hint when available. It also appends a
`fallback_report` section automatically when that fallback query succeeds. Some
live series still expose `agent_host` but do not carry `device_code`.

### 1. Raw interface labels

```promql
sort_by_label_numeric(oneops:if_oper_status{agent_host="$agent_host"}, "ifIndex")
```

Check for:

- `ifName`
- `ifDescr`
- `ifAlias`
- `ifIndex`

### 2. Raw logical/noisy interfaces that still exist

```promql
sort_by_label_numeric(
  (
    oneops:if_oper_status{
      agent_host="$agent_host",
      ifName=~"(?i).*(Vlan|Aggregation|Loop|NULL|Tunnel|Dialer|Cellular|BVI|Virtual).*"
    }
    or
    label_replace(
      oneops:if_oper_status{
        agent_host="$agent_host",
        ifName="",
        ifDescr=~"(?i).*(Vlan|Aggregation|Loop|NULL|Tunnel|Dialer|Cellular|BVI|Virtual).*"
      },
      "ifName",
      "$1",
      "ifDescr",
      "(.*)"
    )
  ),
  "ifIndex"
)
```

If this still returns many series, the device family is inherently exposing a
lot of non-physical interfaces, either directly in `ifName` or only through
`ifDescr`, and the panel will look less like `Comware`.

### 3. Current physical-path branch with `ifName`

```promql
sort_by_label_numeric(
  (oneops:if_oper_status{
    agent_host="$agent_host",
    ifName!="",
    ifName!~"(?i)^(Vlanif|Vlan-interface|Vlan[0-9]+|Eth-Trunk|Bridge-Aggregation|Route-Aggregation|Link-Aggregation|LoopBack|Loopback|NULL|NULL0|InLoopBack|InLoop|MEth|M-GigabitEthernet|Sip|Tunnel|Nve|Dialer|Cellular|BVI|Virtual-Template|Virtual-Access).*$"
  } == bool 1),
  "ifIndex"
)
```

This shows the current direct branch for interfaces whose `ifName` is already
present.

### 4. Current fallback branch with `ifDescr -> ifName`

```promql
sort_by_label_numeric(
  (
    label_replace(
      oneops:if_oper_status{
        agent_host="$agent_host",
        ifName="",
        ifDescr!="",
        ifDescr!~"(?i)^(Vlanif|Vlan-interface|Vlan[0-9]+|Eth-Trunk|Bridge-Aggregation|Route-Aggregation|Link-Aggregation|LoopBack|Loopback|NULL|NULL0|InLoopBack|InLoop|MEth|M-GigabitEthernet|Sip|Tunnel|Nve|Dialer|Cellular|BVI|Virtual-Template|Virtual-Access).*$"
      },
      "ifName",
      "$1",
      "ifDescr",
      "(.*)"
    ) == bool 1
  ),
  "ifIndex"
)
```

If `Comware` looks good but `MyPower` or `SecPath` do not, compare the series
names returned by this query first.

## Decision Rule

If the raw label sample shows:

- mostly clean physical `ifName` values
- small amount of logical-port noise

then the current generic panel is already sufficient and no further backend
change is needed.

If the raw label sample shows:

- many firewall/logical interfaces surviving the filter
- irregular `ifName` values that are non-empty but not useful for display
- `ifIndex` order that still does not resemble module order

then the next step is not “copy Comware expression again”. The next step is one
of:

1. expand the shared logical-interface filter again
2. add a generic display-name cleanup layer
3. implement real module grouping instead of flat status strips
