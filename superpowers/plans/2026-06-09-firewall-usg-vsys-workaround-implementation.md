# Firewall USG Vsys Workaround Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let uploaded Huawei USG configs be imported as one selected vsys/VRF logical firewall node through `metadata.firewall_vsys`.

**Architecture:** Add a small NodeMap preparation layer that creates a filtered USG config view before adapter construction. The filtered view keeps target-context config plus shadow route dependencies for cross-vsys resolution, while NodeMap exposes only the selected logical node and selected route table.

**Tech Stack:** Go, existing `nodemap` package, USG adapter, Go unit tests.

---

### Task 1: Regression Test For Vsys Import

**Files:**
- Modify: `controller/pkg/nodemap/tests/firewall/imported_config_corpus_test.go`

- [ ] **Step 1: Add a failing test**

Add a test that imports the E8000E corpus config with:

```go
MetaData: map[string]interface{}{
	"firewall_vsys": "vsys_vrouteshzjhapomcpr_10018_1",
}
```

Assert:

```go
strings.HasSuffix(nm.Nodes[0].Name(), "/vsys_vrouteshzjhapomcpr_10018_1")
nm.Nodes[0].Ipv4RouteTable("vsys_vrouteshzjhapomcpr_10018_1") != nil
nm.Nodes[0].Ipv4RouteTable("ext_Internet9297") == nil
```

- [ ] **Step 2: Run the test and verify it fails**

Run:

```bash
cd /OneOPS/ctrlhub/controller
go test ./pkg/nodemap/tests/firewall -run TestUploadedHuaweiConfigWithVsysMetadataBuildsLogicalNode -count=1 -v
```

Expected: FAIL because node name is not suffixed and non-target route tables are still visible.

### Task 2: Add USG Vsys Config View Helper

**Files:**
- Create: `controller/pkg/nodemap/usg_vsys_workaround.go`
- Test through: `controller/pkg/nodemap/tests/firewall/imported_config_corpus_test.go`

- [ ] **Step 1: Implement metadata detection**

Create helper functions in package `nodemap`:

```go
const firewallVsysMetadataKey = "firewall_vsys"

func firewallVsysFromMetadata(conf config.DeviceConfig) string {
	if conf.MetaData == nil {
		return ""
	}
	value, ok := conf.MetaData[firewallVsysMetadataKey]
	if !ok {
		return ""
	}
	return strings.TrimSpace(fmt.Sprint(value))
}
```

- [ ] **Step 2: Implement config preparation**

Add:

```go
func prepareUSGVsysWorkaroundConfig(conf config.DeviceConfig) (config.DeviceConfig, string) {
	target := firewallVsysFromMetadata(conf)
	if target == "" || strings.TrimSpace(conf.Config) == "" || !isUSGMode(conf.Mode) {
		return conf, ""
	}
	conf.Config = filterUSGConfigForVsys(conf.Config, target)
	if conf.MetaData == nil {
		conf.MetaData = map[string]interface{}{}
	}
	conf.MetaData["firewall_vsys"] = target
	conf.MetaData["firewall_vsys_workaround"] = true
	conf.MetaData["physical_firewall_host"] = conf.Host
	return conf, target
}
```

- [ ] **Step 3: Implement filtering**

Filtering keeps:

```text
sysname
ip vpn-instance blocks
target-bound interface blocks
firewall zone blocks
all top-level static route lines with source or next-hop VRF equal to target
switch vsys <target> ... return
global object definition blocks
```

It drops unrelated `switch vsys` blocks.

### Task 3: Wire Helper Into NewNodeMapFromNetwork

**Files:**
- Modify: `controller/pkg/nodemap/nodemap.go`

- [ ] **Step 1: Prepare config before adapter construction**

Inside the `for index, conf := range deviceList` loop:

```go
conf, selectedFirewallVsys := prepareUSGVsysWorkaroundConfig(conf)
deviceList[index] = conf
```

- [ ] **Step 2: Suffix logical node name**

After `node := NewNodeFromAdapter(adapter, name, force)`:

```go
if selectedFirewallVsys != "" {
	node.WithName(node.Name() + "/" + selectedFirewallVsys)
}
```

- [ ] **Step 3: Expose only target route tables**

When route tables are returned, only call `SetIpv4RouteTable` and `SetIpv6RouteTable` for `selectedFirewallVsys` if it is set.

### Task 4: Verify Regression And Existing Corpus

**Files:**
- Verify only.

- [ ] **Step 1: Run focused tests**

```bash
cd /OneOPS/ctrlhub/controller
go test ./pkg/nodemap/tests/firewall -run 'TestUploadedHuaweiConfigWithVsysMetadataBuildsLogicalNode|TestUploadedHuaweiConfigWithHostBuildsOfflineNodeMap|TestImportedFirewallConfigsBuildOfflineNodeMap' -count=1 -v
```

Expected: PASS.

- [ ] **Step 2: Run USG route parser tests**

```bash
cd /OneOPS/ctrlhub/controller
go test ./pkg/nodemap/adapter/fw/usg -run 'TestParseIpv6RouteFromConfigSkipsVpnInstanceRecursiveNextHop|TestParseUsgStaticRoutesFromConfigKeepsRealRouteForms' -count=1 -v
```

Expected: PASS.
