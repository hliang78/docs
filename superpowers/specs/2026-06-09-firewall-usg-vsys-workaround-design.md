# USG Vsys Imported Config Workaround Design

Date: 2026-06-09

## Purpose

Support firewall module testing for Huawei USG configurations that contain multiple VSYS/VRF contexts without doing the full multi-vsys platform model yet.

The short-term behavior is: one uploaded physical USG configuration can be imported as one selected logical firewall context by passing a target vsys/VRF name in device metadata.

## Scope

This workaround applies only to offline uploaded USG/HuaWei configurations. It does not change live collection behavior.

The selected logical context is configured through:

```yaml
metadata:
  firewall_vsys: vsys_vrouteshzjhapomcpr_10018_1
```

The value may also be a VPN instance name such as `ext_Internet9297` or `MGMT` when the test target is a VRF-style context rather than a `switch vsys` block.

## NodeMap Behavior

Before `NewAdapter` is called, `NewNodeMapFromNetwork` should normalize device metadata and detect the selected USG context.

When `DeviceConfig.Mode` is `USG` or `HuaWei`, `DeviceConfig.Config` is not empty, and `metadata.firewall_vsys` is set:

1. Build a filtered config view for the selected context.
2. Use that filtered config for adapter parsing.
3. Preserve the original physical host IP in `DeviceConfig.Host`.
4. Add the selected context to the logical node name to avoid collisions.

Suggested logical node name:

```text
<sysname>/<firewall_vsys>
```

Example:

```text
SH-HAP-ZJIDC-CORE-FW-HW-E8000E-X8-1/vsys_vrouteshzjhapomcpr_10018_1
```

## Filtered Config View

The filtered config must preserve enough global configuration for USG parsers to work, while limiting context-specific firewall behavior.

Keep:

- `sysname` and device identity lines.
- Global object definitions used by policy/NAT parsing.
- `ip vpn-instance <target>` block.
- Interfaces whose `ip binding vpn-instance` equals the target.
- Firewall zone definitions that include retained interfaces.
- Static routes where source VRF is the target.
- Static routes that point from or to the target through `vpn-instance`.
- The `switch vsys <target> ... return` block when present.

Drop:

- Other `switch vsys` blocks.
- Interfaces bound to other vpn-instances, unless they are needed as shared/global interfaces for the selected context.
- Routes whose source and next-hop VRF are both unrelated to the target.

## Route Handling

Routes like this must not be treated as normal next-hop IP routes:

```text
ip route-static vpn-instance ext_Internet9297 172.21.128.200 255.255.255.255 vpn-instance vsys_vrouteshzjhapomcpr_10018_1
```

They represent a cross-context dependency. For the workaround, keep only the route records related to the selected context, and continue using the existing USG static route parser behavior that resolves cross-table routes without panicking.

## Metadata

Store context metadata on the generated node/device config so downstream firewall policy generation can know which logical context it is operating on.

Required keys:

```yaml
firewall_vsys: <selected context>
firewall_vsys_workaround: true
physical_firewall_host: <DeviceConfig.Host>
```

Optional key:

```yaml
physical_firewall_name: <sysname>
```

## UI Expectations

For this workaround, the platform may show each selected context as a separate firewall node row.

Expected columns:

- Host name: `<sysname>/<firewall_vsys>`
- Firewall platform: USG/HuaWei
- Interfaces: only retained interfaces
- Routes: only selected-context routes
- Zones: selected-context zones
- Status: normal if parsing succeeds

The UI does not need to render a physical-device tree yet.

## Testing

Add regression tests for:

1. Uploaded USG config with `Host`, `Config`, and `metadata.firewall_vsys` builds without live SSH.
2. The generated node name includes the selected context.
3. Other vsys blocks are not included in the selected context view.
4. Routes with `vpn-instance <target> ... vpn-instance <other>` do not panic.
5. Existing imported firewall corpus tests still pass when no `firewall_vsys` metadata is provided.

## Known Limitations

This is not full multi-vsys support. To test multiple contexts, upload the same physical config multiple times with different `metadata.firewall_vsys` values.

Full support should later auto-discover all vsys contexts and create a physical firewall container with multiple logical firewall children.
