# IPAM Address Management Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build enterprise-wide IP address planning, statistics, collection audit, and request/reclaim workflow capabilities in OneOPS IPAM without changing existing platform VRF semantics.

**Architecture:** Extend the existing `OneOPS/app/ipam` module with focused domain models for address pools, reserved ranges, requests, audit logs, observed facts, and audit findings. Keep existing `IPAddress`, `Prefix`, `Vrf`, `Mac`, `IPAMAgg`, and firewall security-zone models compatible, and expose new APIs under `/ipam/*`.

**Tech Stack:** Go, Gin, GORM/gen DAO, Wire providers, existing OneOPS DTO/service/api/router conventions, Ant Design Vue frontend API typings for IPAM pages.

---

## File Structure

### Backend Models

- Modify: `OneOPS/app/ipam/ipam_model/ip_address.go`
- Create: `OneOPS/app/ipam/ipam_model/address_pool.go`
- Create: `OneOPS/app/ipam/ipam_model/reserved_range.go`
- Create: `OneOPS/app/ipam/ipam_model/ip_address_request.go`
- Create: `OneOPS/app/ipam/ipam_model/ip_address_audit.go`
- Create: `OneOPS/app/ipam/ipam_model/ip_address_fact.go`
- Create: `OneOPS/app/ipam/ipam_model/ip_address_audit_finding.go`
- Modify: `OneOPS/initialize/mysql.go`
- Modify: `OneOPS/cmd/gen/mysql/gen.go`

### Backend DTOs and Enums

- Modify: `OneOPS/app/ipam/enum/ip_address.go`
- Create: `OneOPS/app/ipam/enum/ipam_process.go`
- Create: `OneOPS/app/ipam/dto/address_pool.go`
- Create: `OneOPS/app/ipam/dto/reserved_range.go`
- Create: `OneOPS/app/ipam/dto/ip_address_request.go`
- Create: `OneOPS/app/ipam/dto/ip_address_audit.go`
- Create: `OneOPS/app/ipam/dto/ip_address_fact.go`
- Create: `OneOPS/app/ipam/dto/ip_address_audit_finding.go`
- Create: `OneOPS/app/ipam/dto/ipam_statistics.go`
- Modify: `OneOPS/app/ipam/dto/ip_address.go`

### Backend Services and APIs

- Create: `OneOPS/app/ipam/service/i_address_pool.go`
- Create: `OneOPS/app/ipam/service/i_reserved_range.go`
- Create: `OneOPS/app/ipam/service/i_ip_address_request.go`
- Create: `OneOPS/app/ipam/service/i_ip_address_audit.go`
- Create: `OneOPS/app/ipam/service/i_ip_address_fact.go`
- Create: `OneOPS/app/ipam/service/i_ip_address_audit_finding.go`
- Create: `OneOPS/app/ipam/service/i_ipam_statistics.go`
- Create: `OneOPS/app/ipam/service/impl/ipam_address_math.go`
- Create: `OneOPS/app/ipam/service/impl/address_pool.go`
- Create: `OneOPS/app/ipam/service/impl/reserved_range.go`
- Create: `OneOPS/app/ipam/service/impl/ip_address_request.go`
- Create: `OneOPS/app/ipam/service/impl/ip_address_audit.go`
- Create: `OneOPS/app/ipam/service/impl/ip_address_fact.go`
- Create: `OneOPS/app/ipam/service/impl/ip_address_audit_finding.go`
- Create: `OneOPS/app/ipam/service/impl/ipam_statistics.go`
- Modify: `OneOPS/app/ipam/service/impl/ip_address.go`
- Create: `OneOPS/app/ipam/api/address_pool.go`
- Create: `OneOPS/app/ipam/api/reserved_range.go`
- Create: `OneOPS/app/ipam/api/ip_address_request.go`
- Create: `OneOPS/app/ipam/api/ip_address_audit_finding.go`
- Create: `OneOPS/app/ipam/api/ipam_statistics.go`
- Create: `OneOPS/app/ipam/router/address_pool.go`
- Create: `OneOPS/app/ipam/router/reserved_range.go`
- Create: `OneOPS/app/ipam/router/ip_address_request.go`
- Create: `OneOPS/app/ipam/router/ip_address_audit_finding.go`
- Create: `OneOPS/app/ipam/router/ipam_statistics.go`
- Modify: `OneOPS/initialize/routers.go`
- Modify: `OneOPS/boot/provider/service_groups.go`
- Modify: `OneOPS/boot/provider/api.go`

### Generated DAO

- Regenerate: `OneOPS/dal/mysql/*.gen.go`

### Tests

- Create: `OneOPS/app/ipam/service/impl/ipam_address_math_test.go`
- Create: `OneOPS/app/ipam/service/impl/address_pool_test.go`
- Create: `OneOPS/app/ipam/service/impl/reserved_range_test.go`
- Create: `OneOPS/app/ipam/service/impl/ip_address_request_test.go`
- Create: `OneOPS/app/ipam/service/impl/ip_address_audit_finding_test.go`
- Create: `OneOPS/app/ipam/service/impl/ipam_statistics_test.go`

### Frontend API Hooks

- Create: `OneOPS-UI/src/api/ipam/address_pool.ts`
- Create: `OneOPS-UI/src/api/ipam/reserved_range.ts`
- Create: `OneOPS-UI/src/api/ipam/ip_address_request.ts`
- Create: `OneOPS-UI/src/api/ipam/ip_address_audit_finding.ts`
- Create: `OneOPS-UI/src/api/ipam/ipam_statistics.ts`
- Create: `OneOPS-UI/src/typings/ipam/address_pool.ts`
- Create: `OneOPS-UI/src/typings/ipam/reserved_range.ts`
- Create: `OneOPS-UI/src/typings/ipam/ip_address_request.ts`
- Create: `OneOPS-UI/src/typings/ipam/ip_address_audit_finding.ts`
- Create: `OneOPS-UI/src/typings/ipam/ipam_statistics.ts`
- Modify: `OneOPS-UI/src/typings/ipam/ip_address.ts`

---

### Task 1: Add IPAM Lifecycle Enums and Models

**Files:**
- Modify: `OneOPS/app/ipam/enum/ip_address.go`
- Create: `OneOPS/app/ipam/enum/ipam_process.go`
- Modify: `OneOPS/app/ipam/ipam_model/ip_address.go`
- Create: `OneOPS/app/ipam/ipam_model/address_pool.go`
- Create: `OneOPS/app/ipam/ipam_model/reserved_range.go`
- Create: `OneOPS/app/ipam/ipam_model/ip_address_request.go`
- Create: `OneOPS/app/ipam/ipam_model/ip_address_audit.go`
- Create: `OneOPS/app/ipam/ipam_model/ip_address_fact.go`
- Create: `OneOPS/app/ipam/ipam_model/ip_address_audit_finding.go`
- Modify: `OneOPS/initialize/mysql.go`
- Modify: `OneOPS/cmd/gen/mysql/gen.go`
- Test: `OneOPS/app/ipam/service/impl/ipam_address_math_test.go`

- [ ] **Step 1: Extend IP address enums**

Add this to `OneOPS/app/ipam/enum/ip_address.go` below the existing `IPAddressStatus` constants:

```go
type IPAddressLifecycleStatus string

const (
	IPAddressLifecycleAvailable  IPAddressLifecycleStatus = "available"
	IPAddressLifecycleReserved   IPAddressLifecycleStatus = "reserved"
	IPAddressLifecycleAssigned   IPAddressLifecycleStatus = "assigned"
	IPAddressLifecycleReleasing  IPAddressLifecycleStatus = "releasing"
	IPAddressLifecycleReclaimed  IPAddressLifecycleStatus = "reclaimed"
	IPAddressLifecycleConflict   IPAddressLifecycleStatus = "conflict"
	IPAddressLifecycleUnknown    IPAddressLifecycleStatus = "unknown"
)

type IPAddressSource string

const (
	IPAddressSourceManual     IPAddressSource = "manual"
	IPAddressSourceImport     IPAddressSource = "import"
	IPAddressSourceDiscovered IPAddressSource = "discovered"
	IPAddressSourceWorkflow   IPAddressSource = "workflow"
)
```

- [ ] **Step 2: Add process enums**

Create `OneOPS/app/ipam/enum/ipam_process.go`:

```go
package enum

type IPAddressRequestType string

const (
	IPAddressRequestAllocate IPAddressRequestType = "allocate"
	IPAddressRequestReserve  IPAddressRequestType = "reserve"
	IPAddressRequestRelease  IPAddressRequestType = "release"
	IPAddressRequestReclaim  IPAddressRequestType = "reclaim"
)

type IPAddressRequestStatus string

const (
	IPAddressRequestDraft     IPAddressRequestStatus = "draft"
	IPAddressRequestSubmitted IPAddressRequestStatus = "submitted"
	IPAddressRequestApproved  IPAddressRequestStatus = "approved"
	IPAddressRequestRejected  IPAddressRequestStatus = "rejected"
	IPAddressRequestCompleted IPAddressRequestStatus = "completed"
	IPAddressRequestCanceled  IPAddressRequestStatus = "canceled"
)

type IPAuditFindingStatus string

const (
	IPAuditFindingOpen         IPAuditFindingStatus = "open"
	IPAuditFindingAcknowledged IPAuditFindingStatus = "acknowledged"
	IPAuditFindingIgnored      IPAuditFindingStatus = "ignored"
	IPAuditFindingResolved     IPAuditFindingStatus = "resolved"
)

type IPAuditFindingSeverity string

const (
	IPAuditFindingInfo     IPAuditFindingSeverity = "info"
	IPAuditFindingWarning  IPAuditFindingSeverity = "warning"
	IPAuditFindingCritical IPAuditFindingSeverity = "critical"
)
```

- [ ] **Step 3: Extend IPAddress model without changing existing VRF meaning**

Add these fields to `OneOPS/app/ipam/ipam_model/ip_address.go` after `Status`:

```go
	LifecycleStatus enum.IPAddressLifecycleStatus `gorm:"default:'unknown';type:varchar(32);comment:IPAM生命周期状态"`
	PoolCode        string                        `gorm:"type:varchar(32);index;comment:地址池编码"`
	RequestCode     string                        `gorm:"type:varchar(32);index;comment:申请单编码"`
	OwnerType       string                        `gorm:"type:varchar(32);comment:拥有者类型"`
	OwnerCode       string                        `gorm:"type:varchar(64);comment:拥有者编码"`
	SecurityZoneID  string                        `gorm:"type:varchar(36);index;comment:安全区域ID覆盖"`
	LastSeenAt      *time.Time                    `gorm:"comment:最近现网发现时间"`
	Source          enum.IPAddressSource          `gorm:"default:'manual';type:varchar(32);comment:数据来源"`
```

Also add `time` to the import block:

```go
import (
	"time"

	baseModel "github.com/netxops/OneOps/app/base/base_model"
	commonModel "github.com/netxops/OneOps/app/common/model"
	"github.com/netxops/OneOps/app/ipam/enum"
)
```

- [ ] **Step 4: Create AddressPool model**

Create `OneOPS/app/ipam/ipam_model/address_pool.go`:

```go
package ipam_model

import commonModel "github.com/netxops/OneOps/app/common/model"

type AddressPool struct {
	commonModel.Common
	Code              string `gorm:"type:varchar(32);unique;not null;comment:地址池编码"`
	Name              string `gorm:"type:varchar(64);not null;comment:地址池名称"`
	PrefixCode        string `gorm:"type:varchar(128);index;not null;comment:网段编码"`
	StartIP           string `gorm:"type:varchar(64);not null;comment:起始IP"`
	EndIP             string `gorm:"type:varchar(64);not null;comment:结束IP"`
	Purpose           string `gorm:"type:varchar(64);comment:用途"`
	TenantCode        string `gorm:"type:varchar(32);index;comment:租户编码"`
	PlatformVrfCode   string `gorm:"type:varchar(32);index;comment:平台VRF编码"`
	SecurityZoneID    string `gorm:"type:varchar(36);index;comment:安全区域ID"`
	SiteCode          string `gorm:"type:varchar(32);index;comment:站点编码"`
	AllocationPolicy  string `gorm:"type:varchar(32);default:'first_available';comment:分配策略"`
	CapacityThreshold int    `gorm:"type:int;default:80;comment:容量阈值百分比"`
	Status            string `gorm:"type:varchar(32);default:'enabled';comment:状态"`
	Description       string `gorm:"type:varchar(255);comment:描述"`
}

func (*AddressPool) TableName() string {
	return "ipam_address_pool"
}
```

- [ ] **Step 5: Create ReservedRange model**

Create `OneOPS/app/ipam/ipam_model/reserved_range.go`:

```go
package ipam_model

import commonModel "github.com/netxops/OneOps/app/common/model"

type ReservedRange struct {
	commonModel.Common
	Code                   string `gorm:"type:varchar(32);unique;not null;comment:保留段编码"`
	PrefixCode             string `gorm:"type:varchar(128);index;not null;comment:网段编码"`
	PoolCode               string `gorm:"type:varchar(32);index;comment:地址池编码"`
	StartIP                string `gorm:"type:varchar(64);not null;comment:起始IP"`
	EndIP                  string `gorm:"type:varchar(64);not null;comment:结束IP"`
	Reason                 string `gorm:"type:varchar(64);not null;comment:保留原因"`
	AllowSpecialAllocation bool   `gorm:"type:tinyint(1);default:0;comment:是否允许特殊分配"`
	Description            string `gorm:"type:varchar(255);comment:描述"`
}

func (*ReservedRange) TableName() string {
	return "ipam_reserved_range"
}
```

- [ ] **Step 6: Create request, audit, fact, and finding models**

Create `OneOPS/app/ipam/ipam_model/ip_address_request.go`:

```go
package ipam_model

import (
	"time"

	commonModel "github.com/netxops/OneOps/app/common/model"
	"github.com/netxops/OneOps/app/ipam/enum"
)

type IPAddressRequest struct {
	commonModel.Common
	Code            string                      `gorm:"type:varchar(32);unique;not null;comment:申请单编码"`
	RequestType     enum.IPAddressRequestType   `gorm:"type:varchar(32);not null;comment:申请类型"`
	Requester       string                      `gorm:"type:varchar(64);comment:申请人"`
	TenantCode      string                      `gorm:"type:varchar(32);index;comment:租户编码"`
	SiteCode        string                      `gorm:"type:varchar(32);index;comment:站点编码"`
	SecurityZoneID  string                      `gorm:"type:varchar(36);index;comment:安全区域ID"`
	PlatformVrfCode string                      `gorm:"type:varchar(32);index;comment:平台VRF编码"`
	PoolCode        string                      `gorm:"type:varchar(32);index;comment:地址池编码"`
	Quantity        int                         `gorm:"type:int;default:1;comment:申请数量"`
	PreferredIP     string                      `gorm:"type:varchar(64);comment:期望IP"`
	Purpose         string                      `gorm:"type:varchar(64);comment:用途"`
	BusinessSystem  string                      `gorm:"type:varchar(128);comment:业务系统"`
	Status          enum.IPAddressRequestStatus `gorm:"type:varchar(32);default:'draft';comment:申请状态"`
	ApprovedBy      string                      `gorm:"type:varchar(64);comment:审批人"`
	ApprovedAt      *time.Time                  `gorm:"comment:审批时间"`
	CompletedAt     *time.Time                  `gorm:"comment:完成时间"`
	Description     string                      `gorm:"type:varchar(255);comment:描述"`
}

func (*IPAddressRequest) TableName() string {
	return "ipam_address_request"
}
```

Create `OneOPS/app/ipam/ipam_model/ip_address_audit.go`:

```go
package ipam_model

import commonModel "github.com/netxops/OneOps/app/common/model"

type IPAddressAudit struct {
	commonModel.Common
	Code          string `gorm:"type:varchar(32);unique;not null;comment:审计编码"`
	IPAddressCode string `gorm:"type:varchar(32);index;comment:IP地址编码"`
	RequestCode   string `gorm:"type:varchar(32);index;comment:申请单编码"`
	Action        string `gorm:"type:varchar(64);not null;comment:动作"`
	BeforeValue   string `gorm:"type:text;comment:变更前"`
	AfterValue    string `gorm:"type:text;comment:变更后"`
	Operator      string `gorm:"type:varchar(64);comment:操作者"`
	Source        string `gorm:"type:varchar(32);comment:来源"`
	Description   string `gorm:"type:varchar(255);comment:描述"`
}

func (*IPAddressAudit) TableName() string {
	return "ipam_address_audit"
}
```

Create `OneOPS/app/ipam/ipam_model/ip_address_fact.go`:

```go
package ipam_model

import (
	"time"

	commonModel "github.com/netxops/OneOps/app/common/model"
)

type IPAddressFact struct {
	commonModel.Common
	Code               string     `gorm:"type:varchar(32);unique;not null;comment:现网事实编码"`
	IPAddress          string     `gorm:"type:varchar(64);index;not null;comment:IP地址"`
	IPVersion          int        `gorm:"type:int;default:4;comment:IP版本"`
	DeviceCode         string     `gorm:"type:varchar(32);index;comment:设备编码"`
	DeviceName         string     `gorm:"type:varchar(255);comment:设备名称"`
	InterfaceCode      string     `gorm:"type:varchar(32);index;comment:接口编码"`
	InterfaceName      string     `gorm:"type:varchar(128);comment:接口名称"`
	MacCode            string     `gorm:"type:varchar(32);index;comment:MAC编码"`
	MacAddress         string     `gorm:"type:varchar(64);comment:MAC地址"`
	PlatformVrfCode    string     `gorm:"type:varchar(32);index;comment:平台VRF编码"`
	DeviceLocalVrfCode string     `gorm:"type:varchar(32);index;comment:设备本地VRF编码"`
	SecurityZoneID     string     `gorm:"type:varchar(36);index;comment:安全区域ID"`
	Source             string     `gorm:"type:varchar(64);index;comment:采集来源"`
	FirstSeenAt        *time.Time `gorm:"comment:首次发现时间"`
	LastSeenAt         *time.Time `gorm:"comment:最近发现时间"`
	Confidence         int        `gorm:"type:int;default:100;comment:置信度"`
	RawRef             string     `gorm:"type:varchar(255);comment:原始数据引用"`
}

func (*IPAddressFact) TableName() string {
	return "ipam_address_fact"
}
```

Create `OneOPS/app/ipam/ipam_model/ip_address_audit_finding.go`:

```go
package ipam_model

import (
	"time"

	commonModel "github.com/netxops/OneOps/app/common/model"
	"github.com/netxops/OneOps/app/ipam/enum"
)

type IPAddressAuditFinding struct {
	commonModel.Common
	Code                  string                      `gorm:"type:varchar(32);unique;not null;comment:稽核发现编码"`
	FindingType           string                      `gorm:"type:varchar(64);index;not null;comment:发现类型"`
	Severity              enum.IPAuditFindingSeverity `gorm:"type:varchar(32);default:'warning';comment:严重级别"`
	IPAddress             string                      `gorm:"type:varchar(64);index;not null;comment:IP地址"`
	IPAddressCode         string                      `gorm:"type:varchar(32);index;comment:IP地址编码"`
	PrefixCode            string                      `gorm:"type:varchar(128);index;comment:网段编码"`
	PoolCode              string                      `gorm:"type:varchar(32);index;comment:地址池编码"`
	SecurityZoneID        string                      `gorm:"type:varchar(36);index;comment:安全区域ID"`
	ObservedDeviceCode    string                      `gorm:"type:varchar(32);index;comment:现网设备编码"`
	ObservedInterfaceCode string                      `gorm:"type:varchar(32);index;comment:现网接口编码"`
	ObservedMacCode       string                      `gorm:"type:varchar(32);index;comment:现网MAC编码"`
	Status                enum.IPAuditFindingStatus   `gorm:"type:varchar(32);default:'open';comment:处理状态"`
	SuggestedAction       string                      `gorm:"type:varchar(255);comment:建议动作"`
	FirstDetectedAt       *time.Time                  `gorm:"comment:首次发现时间"`
	LastDetectedAt        *time.Time                  `gorm:"comment:最近发现时间"`
}

func (*IPAddressAuditFinding) TableName() string {
	return "ipam_address_audit_finding"
}
```

- [ ] **Step 7: Register new models for AutoMigrate and gen**

In `OneOPS/initialize/mysql.go`, add these models immediately after `ipam_model.Mac{}`:

```go
		ipam_model.AddressPool{},
		ipam_model.ReservedRange{},
		ipam_model.IPAddressRequest{},
		ipam_model.IPAddressAudit{},
		ipam_model.IPAddressFact{},
		ipam_model.IPAddressAuditFinding{},
```

In `OneOPS/cmd/gen/mysql/gen.go`, add the same model entries immediately after `ipam_model.Mac{}`.

- [ ] **Step 8: Regenerate DAO**

Run:

```bash
cd /Users/huangliang/project/OneOPS-ALL/OneOPS
go run ./cmd/gen/mysql/gen.go
```

Expected: generated DAO files include `address_pool.gen.go`, `reserved_range.gen.go`, `ip_address_request.gen.go`, `ip_address_audit.gen.go`, `ip_address_fact.gen.go`, and `ip_address_audit_finding.gen.go`.

- [ ] **Step 9: Commit model foundation**

```bash
cd /Users/huangliang/project/OneOPS-ALL
git add OneOPS/app/ipam/enum OneOPS/app/ipam/ipam_model OneOPS/initialize/mysql.go OneOPS/cmd/gen/mysql/gen.go OneOPS/dal/mysql
git commit -m "feat(ipam): add address planning domain models"
```

---

### Task 2: Add Address Math Utilities and Validation Tests

**Files:**
- Create: `OneOPS/app/ipam/service/impl/ipam_address_math.go`
- Create: `OneOPS/app/ipam/service/impl/ipam_address_math_test.go`

- [ ] **Step 1: Write failing tests**

Create `OneOPS/app/ipam/service/impl/ipam_address_math_test.go`:

```go
package impl

import "testing"

func TestIPAMAddressMathContainsAndRange(t *testing.T) {
	if !ipInCIDR("10.20.1.5", "10.20.1.0/24") {
		t.Fatalf("expected IP to be inside CIDR")
	}
	if ipInCIDR("10.20.2.5", "10.20.1.0/24") {
		t.Fatalf("expected IP to be outside CIDR")
	}
	if !ipRangeContains("10.20.1.10", "10.20.1.1", "10.20.1.20") {
		t.Fatalf("expected IP to be inside range")
	}
	if ipRangeContains("10.20.1.21", "10.20.1.1", "10.20.1.20") {
		t.Fatalf("expected IP to be outside range")
	}
}

func TestIPAMAddressMathOverlap(t *testing.T) {
	if !cidrOverlaps("10.20.1.0/24", "10.20.1.128/25") {
		t.Fatalf("expected overlapping CIDRs")
	}
	if cidrOverlaps("10.20.1.0/24", "10.20.2.0/24") {
		t.Fatalf("expected non-overlapping CIDRs")
	}
	if !ipRangeOverlaps("10.20.1.1", "10.20.1.10", "10.20.1.5", "10.20.1.20") {
		t.Fatalf("expected overlapping ranges")
	}
	if ipRangeOverlaps("10.20.1.1", "10.20.1.10", "10.20.1.11", "10.20.1.20") {
		t.Fatalf("expected non-overlapping ranges")
	}
}
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
cd /Users/huangliang/project/OneOPS-ALL/OneOPS
go test ./app/ipam/service/impl -run TestIPAMAddressMath -count=1
```

Expected: FAIL because `ipInCIDR`, `ipRangeContains`, `cidrOverlaps`, and `ipRangeOverlaps` are undefined.

- [ ] **Step 3: Implement address math**

Create `OneOPS/app/ipam/service/impl/ipam_address_math.go`:

```go
package impl

import (
	"bytes"
	"math/big"
	"net"
)

func parseIPBytes(value string) []byte {
	ip := net.ParseIP(value)
	if ip == nil {
		return nil
	}
	if v4 := ip.To4(); v4 != nil {
		return v4
	}
	return ip.To16()
}

func ipInCIDR(ipValue, cidr string) bool {
	ip := net.ParseIP(ipValue)
	if ip == nil {
		return false
	}
	_, network, err := net.ParseCIDR(cidr)
	if err != nil {
		return false
	}
	return network.Contains(ip)
}

func ipRangeContains(ipValue, startValue, endValue string) bool {
	ip := parseIPBytes(ipValue)
	start := parseIPBytes(startValue)
	end := parseIPBytes(endValue)
	if ip == nil || start == nil || end == nil || len(ip) != len(start) || len(ip) != len(end) {
		return false
	}
	return bytes.Compare(ip, start) >= 0 && bytes.Compare(ip, end) <= 0
}

func cidrOverlaps(left, right string) bool {
	_, leftNet, leftErr := net.ParseCIDR(left)
	_, rightNet, rightErr := net.ParseCIDR(right)
	if leftErr != nil || rightErr != nil {
		return false
	}
	return leftNet.Contains(rightNet.IP) || rightNet.Contains(leftNet.IP)
}

func ipRangeOverlaps(leftStartValue, leftEndValue, rightStartValue, rightEndValue string) bool {
	leftStart := parseIPBytes(leftStartValue)
	leftEnd := parseIPBytes(leftEndValue)
	rightStart := parseIPBytes(rightStartValue)
	rightEnd := parseIPBytes(rightEndValue)
	if leftStart == nil || leftEnd == nil || rightStart == nil || rightEnd == nil {
		return false
	}
	if len(leftStart) != len(leftEnd) || len(leftStart) != len(rightStart) || len(leftStart) != len(rightEnd) {
		return false
	}
	return bytes.Compare(leftStart, rightEnd) <= 0 && bytes.Compare(rightStart, leftEnd) <= 0
}

func ipToBigInt(value string) *big.Int {
	ip := parseIPBytes(value)
	if ip == nil {
		return nil
	}
	return new(big.Int).SetBytes(ip)
}
```

- [ ] **Step 4: Run tests to verify pass**

Run:

```bash
cd /Users/huangliang/project/OneOPS-ALL/OneOPS
go test ./app/ipam/service/impl -run TestIPAMAddressMath -count=1
```

Expected: PASS.

- [ ] **Step 5: Commit address math**

```bash
cd /Users/huangliang/project/OneOPS-ALL
git add OneOPS/app/ipam/service/impl/ipam_address_math.go OneOPS/app/ipam/service/impl/ipam_address_math_test.go
git commit -m "feat(ipam): add address validation helpers"
```

---

### Task 3: Implement AddressPool CRUD and Validation

**Files:**
- Create: `OneOPS/app/ipam/dto/address_pool.go`
- Create: `OneOPS/app/ipam/service/i_address_pool.go`
- Create: `OneOPS/app/ipam/service/impl/address_pool.go`
- Create: `OneOPS/app/ipam/api/address_pool.go`
- Create: `OneOPS/app/ipam/router/address_pool.go`
- Modify: `OneOPS/boot/provider/service_groups.go`
- Modify: `OneOPS/boot/provider/api.go`
- Modify: `OneOPS/initialize/routers.go`
- Test: `OneOPS/app/ipam/service/impl/address_pool_test.go`

- [ ] **Step 1: Write failing service tests**

Create `OneOPS/app/ipam/service/impl/address_pool_test.go`:

```go
package impl

import (
	"testing"

	"github.com/netxops/OneOps/app/ipam/dto"
)

func TestAddressPoolValidateRangeInsidePrefix(t *testing.T) {
	srv := &AddressPoolSrv{}
	req := dto.AddressPoolReq{
		PrefixCIDR: "10.20.1.0/24",
		StartIP:    "10.20.1.10",
		EndIP:      "10.20.1.20",
	}
	if err := srv.validateRange(req); err != nil {
		t.Fatalf("expected valid range: %v", err)
	}
	req.EndIP = "10.20.2.20"
	if err := srv.validateRange(req); err == nil {
		t.Fatalf("expected range outside prefix to fail")
	}
}
```

- [ ] **Step 2: Add DTO**

Create `OneOPS/app/ipam/dto/address_pool.go`:

```go
package dto

import (
	commonDTO "github.com/netxops/OneOps/app/common/dto"
	"github.com/netxops/OneOps/app/common/pagination"
)

type AddressPoolReq struct {
	commonDTO.Common
	Code              string `json:"code" validate:"max=32"`
	Name              string `json:"name" validate:"required,max=64"`
	PrefixCode        string `json:"prefix_code" validate:"required,max=128"`
	PrefixCIDR        string `json:"prefix_cidr" validate:"-"`
	StartIP           string `json:"start_ip" validate:"required,max=64"`
	EndIP             string `json:"end_ip" validate:"required,max=64"`
	Purpose           string `json:"purpose" validate:"max=64"`
	TenantCode        string `json:"tenant_code" validate:"max=32"`
	PlatformVrfCode   string `json:"platform_vrf_code" validate:"max=32"`
	SecurityZoneID    string `json:"security_zone_id" validate:"max=36"`
	SiteCode          string `json:"site_code" validate:"max=32"`
	AllocationPolicy  string `json:"allocation_policy" validate:"max=32"`
	CapacityThreshold int    `json:"capacity_threshold"`
	Status            string `json:"status" validate:"max=32"`
	Description       string `json:"description" validate:"max=255"`
}

type AddressPoolResp struct {
	commonDTO.Common
	Code              string `json:"code"`
	Name              string `json:"name"`
	PrefixCode        string `json:"prefix_code"`
	StartIP           string `json:"start_ip"`
	EndIP             string `json:"end_ip"`
	Purpose           string `json:"purpose"`
	TenantCode        string `json:"tenant_code"`
	PlatformVrfCode   string `json:"platform_vrf_code"`
	SecurityZoneID    string `json:"security_zone_id"`
	SiteCode          string `json:"site_code"`
	AllocationPolicy  string `json:"allocation_policy"`
	CapacityThreshold int    `json:"capacity_threshold"`
	Status            string `json:"status"`
	Description       string `json:"description"`
}

type AddressPoolPage struct {
	pagination.Page
	AddressPoolReq
}
```

- [ ] **Step 3: Add service interface**

Create `OneOPS/app/ipam/service/i_address_pool.go`:

```go
package service

import (
	"context"

	"github.com/netxops/OneOps/app/common/pagination"
	"github.com/netxops/OneOps/app/ipam/dto"
)

type IAddressPool interface {
	Create(r dto.AddressPoolReq, ctx context.Context) (*dto.AddressPoolResp, error)
	Update(r dto.AddressPoolReq, ctx context.Context) (*dto.AddressPoolResp, error)
	DeleteByCode(code string, ctx context.Context) error
	FindByCode(code string, ctx context.Context) (*dto.AddressPoolResp, error)
	PageList(r dto.AddressPoolPage, ctx context.Context) (pagination.Page, error)
}
```

- [ ] **Step 4: Implement service skeleton and validation**

Create `OneOPS/app/ipam/service/impl/address_pool.go`:

```go
package impl

import (
	"context"
	"fmt"
	"strings"

	"github.com/google/wire"
	"github.com/jinzhu/copier"
	baseSrv "github.com/netxops/OneOps/app/base/service/impl"
	"github.com/netxops/OneOps/app/common/codec"
	"github.com/netxops/OneOps/app/common/pagination"
	"github.com/netxops/OneOps/app/common/proxy"
	"github.com/netxops/OneOps/app/common/validate"
	"github.com/netxops/OneOps/app/ipam/dto"
	ipamModel "github.com/netxops/OneOps/app/ipam/ipam_model"
	"github.com/netxops/OneOps/app/ipam/service"
	"github.com/pkg/errors"
	"go.uber.org/zap"
	"gorm.io/gorm"
)

var _ service.IAddressPool = (*AddressPoolSrv)(nil)

var AddressPoolSet = wire.NewSet(
	NewAddressPoolSrv,
	wire.Bind(new(service.IAddressPool), new(*AddressPoolSrv)),
)

type AddressPoolSrv struct {
	Logger            *zap.Logger
	GenerateCodeSrv   *codec.GenerateCodeSrv
	FieldValidatorSrv *validate.FieldValidatorSrv
	PrefixSrv         *baseSrv.PrefixSrv
	ProxySrv          *proxy.TxProxySrv
}

func NewAddressPoolSrv(logger *zap.Logger, generateCodeSrv *codec.GenerateCodeSrv, fieldValidatorSrv *validate.FieldValidatorSrv, prefixSrv *baseSrv.PrefixSrv, proxySrv *proxy.TxProxySrv) *AddressPoolSrv {
	return &AddressPoolSrv{Logger: logger, GenerateCodeSrv: generateCodeSrv, FieldValidatorSrv: fieldValidatorSrv, PrefixSrv: prefixSrv, ProxySrv: proxySrv}
}

func (s *AddressPoolSrv) validateRange(r dto.AddressPoolReq) error {
	if strings.TrimSpace(r.PrefixCIDR) == "" {
		return errors.New("网段CIDR不能为空")
	}
	if !ipInCIDR(r.StartIP, r.PrefixCIDR) || !ipInCIDR(r.EndIP, r.PrefixCIDR) {
		return fmt.Errorf("地址池范围[%s-%s]必须在网段[%s]内", r.StartIP, r.EndIP, r.PrefixCIDR)
	}
	if !ipRangeContains(r.StartIP, r.StartIP, r.EndIP) {
		return errors.New("地址池起始IP不能大于结束IP")
	}
	return nil
}

func (s *AddressPoolSrv) Create(r dto.AddressPoolReq, ctx context.Context) (*dto.AddressPoolResp, error) {
	if strings.TrimSpace(r.ID) != "" {
		return nil, errors.New("地址池ID不能有值")
	}
	if strings.TrimSpace(r.Code) != "" {
		return nil, errors.New("地址池编码不能有值")
	}
	prefix, err := s.PrefixSrv.FindByCode(r.PrefixCode, ctx)
	if err != nil {
		return nil, err
	}
	r.PrefixCIDR = prefix.Name
	if err = s.validateRange(r); err != nil {
		return nil, err
	}
	if r.Code, err = s.GenerateCodeSrv.GenerateCode("POOL", 6); err != nil {
		return nil, err
	}
	t := s.ProxySrv.Query(ctx).AddressPool
	q := t.WithContext(ctx)
	existing, err := q.Where(t.Code.Eq(r.Code)).FirstOrInit()
	if err != nil {
		return nil, err
	}
	if existing.ID != "" {
		return nil, errors.New("地址池编码重复")
	}
	model := &ipamModel.AddressPool{}
	if err = copier.Copy(model, &r); err != nil {
		return nil, err
	}
	model.Code = r.Code
	if model.AllocationPolicy == "" {
		model.AllocationPolicy = "first_available"
	}
	if model.Status == "" {
		model.Status = "enabled"
	}
	if model.CapacityThreshold == 0 {
		model.CapacityThreshold = 80
	}
	if err = q.Create(model); err != nil {
		return nil, err
	}
	resp := &dto.AddressPoolResp{}
	if err = copier.Copy(resp, model); err != nil {
		return nil, err
	}
	return resp, nil
}

func (s *AddressPoolSrv) Update(r dto.AddressPoolReq, ctx context.Context) (*dto.AddressPoolResp, error) {
	if strings.TrimSpace(r.Code) == "" {
		return nil, errors.New("地址池编码不能为空")
	}
	prefix, err := s.PrefixSrv.FindByCode(r.PrefixCode, ctx)
	if err != nil {
		return nil, err
	}
	r.PrefixCIDR = prefix.Name
	if err = s.validateRange(r); err != nil {
		return nil, err
	}
	t := s.ProxySrv.Query(ctx).AddressPool
	q := t.WithContext(ctx)
	model, err := q.Where(t.Code.Eq(r.Code)).First()
	if err != nil {
		return nil, err
	}
	if err = copier.Copy(model, &r); err != nil {
		return nil, err
	}
	if err = q.Save(model); err != nil {
		return nil, err
	}
	resp := &dto.AddressPoolResp{}
	if err = copier.Copy(resp, model); err != nil {
		return nil, err
	}
	return resp, nil
}

func (s *AddressPoolSrv) DeleteByCode(code string, ctx context.Context) error {
	if strings.TrimSpace(code) == "" {
		return errors.New("地址池编码不能为空")
	}
	t := s.ProxySrv.Query(ctx).AddressPool
	q := t.WithContext(ctx)
	_, err := q.Where(t.Code.Eq(code)).First()
	if errors.Is(err, gorm.ErrRecordNotFound) {
		return nil
	}
	if err != nil {
		return err
	}
	_, err = q.Where(t.Code.Eq(code)).Delete()
	return err
}

func (s *AddressPoolSrv) FindByCode(code string, ctx context.Context) (*dto.AddressPoolResp, error) {
	if strings.TrimSpace(code) == "" {
		return nil, errors.New("地址池编码不能为空")
	}
	t := s.ProxySrv.Query(ctx).AddressPool
	model, err := t.WithContext(ctx).Where(t.Code.Eq(code)).First()
	if err != nil {
		return nil, err
	}
	resp := &dto.AddressPoolResp{}
	if err = copier.Copy(resp, model); err != nil {
		return nil, err
	}
	return resp, nil
}

func (s *AddressPoolSrv) PageList(r dto.AddressPoolPage, ctx context.Context) (pagination.Page, error) {
	t := s.ProxySrv.Query(ctx).AddressPool
	q := t.WithContext(ctx)
	if strings.TrimSpace(r.Name) != "" {
		q = q.Where(t.Name.Like("%" + r.Name + "%"))
	}
	if strings.TrimSpace(r.PrefixCode) != "" {
		q = q.Where(t.PrefixCode.Eq(r.PrefixCode))
	}
	result, count, err := q.Order(t.CreatedAt.Desc()).FindByPage(r.Offset(), r.Limit())
	if err != nil {
		return pagination.Page{}, err
	}
	var list []*dto.AddressPoolResp
	if err = copier.Copy(&list, &result); err != nil {
		return pagination.Page{}, err
	}
	var page pagination.Page
	page.Page(list, count, r.Offset(), r.Limit())
	return page, nil
}
```

- [ ] **Step 5: Add API and router**

Create API and router files using the existing `IPAddressAPI` pattern:

```go
// OneOPS/app/ipam/router/address_pool.go
package router

import (
	"github.com/gin-gonic/gin"
	"github.com/netxops/OneOps/app/ipam/api"
)

func AddressPool(r *gin.RouterGroup, api *api.AddressPoolAPI) {
	g := r.Group("ipam/address-pools")
	g.POST("", api.Create)
	g.POST("list", api.PageList)
	g.DELETE(":code", api.DeleteByCode)
	g.GET(":code", api.FindByCode)
	g.PUT("", api.Update)
}
```

```go
// OneOPS/app/ipam/api/address_pool.go
package api

import (
	"github.com/gin-gonic/gin"
	"github.com/google/wire"
	"github.com/netxops/OneOps/app/ipam/dto"
	"github.com/netxops/OneOps/app/ipam/service/impl"
	"github.com/netxops/OneOps/pkg/bind"
	"github.com/netxops/OneOps/pkg/response"
	"go.uber.org/zap"
)

var AddressPoolAPISet = wire.NewSet(wire.Struct(new(AddressPoolAPI), "*"))

type AddressPoolAPI struct {
	Logger         *zap.Logger
	AddressPoolSrv *impl.AddressPoolSrv
}

func (a *AddressPoolAPI) Create(ctx *gin.Context) {
	var r dto.AddressPoolReq
	if ok := bind.JSON(&r, ctx); !ok {
		return
	}
	resp, err := a.AddressPoolSrv.Create(r, ctx)
	if err != nil {
		response.FailWithMsg(err.Error(), ctx)
		a.Logger.Error("地址池创建失败", zap.Error(err))
		return
	}
	response.OkWithDetailed("创建成功", resp, ctx)
}

func (a *AddressPoolAPI) PageList(ctx *gin.Context) {
	var r dto.AddressPoolPage
	if ok := bind.JSON(&r, ctx); !ok {
		return
	}
	page, err := a.AddressPoolSrv.PageList(r, ctx)
	if err != nil {
		response.FailWithMsg("地址池列表获取失败", ctx)
		a.Logger.Error("地址池列表获取失败", zap.Error(err))
		return
	}
	response.OkWithPage(page, ctx)
}

func (a *AddressPoolAPI) DeleteByCode(ctx *gin.Context) {
	if err := a.AddressPoolSrv.DeleteByCode(ctx.Param("code"), ctx); err != nil {
		response.FailWithMsg(err.Error(), ctx)
		return
	}
	response.OkWithMsg("删除成功", ctx)
}

func (a *AddressPoolAPI) FindByCode(ctx *gin.Context) {
	resp, err := a.AddressPoolSrv.FindByCode(ctx.Param("code"), ctx)
	if err != nil {
		response.FailWithMsg(err.Error(), ctx)
		return
	}
	response.OkWithData(resp, ctx)
}

func (a *AddressPoolAPI) Update(ctx *gin.Context) {
	var r dto.AddressPoolReq
	if ok := bind.JSON(&r, ctx); !ok {
		return
	}
	resp, err := a.AddressPoolSrv.Update(r, ctx)
	if err != nil {
		response.FailWithMsg(err.Error(), ctx)
		return
	}
	response.OkWithDetailed("更新成功", resp, ctx)
}
```

- [ ] **Step 6: Register providers and routes**

Add `ipamSrv.AddressPoolSet` to `OneOPS/boot/provider/service_groups.go` after `ipamSrv.MacSet`.

Add `ipamAPI.AddressPoolAPISet` to `OneOPS/boot/provider/api.go` after `ipamAPI.MacSet`.

In `OneOPS/initialize/routers.go`, add route registration after existing `ipamRouter.IPAddress(private, r.IPAddressAPI)`:

```go
		ipamRouter.AddressPool(private, r.AddressPoolAPI)
```

- [ ] **Step 7: Run focused tests**

```bash
cd /Users/huangliang/project/OneOPS-ALL/OneOPS
go test ./app/ipam/service/impl -run 'Test(AddressPool|IPAMAddressMath)' -count=1
```

Expected: PASS.

- [ ] **Step 8: Commit address pool**

```bash
cd /Users/huangliang/project/OneOPS-ALL
git add OneOPS/app/ipam/dto/address_pool.go OneOPS/app/ipam/service/i_address_pool.go OneOPS/app/ipam/service/impl/address_pool.go OneOPS/app/ipam/api/address_pool.go OneOPS/app/ipam/router/address_pool.go OneOPS/boot/provider/service_groups.go OneOPS/boot/provider/api.go OneOPS/initialize/routers.go OneOPS/app/ipam/service/impl/address_pool_test.go
git commit -m "feat(ipam): add address pool management"
```

---

### Task 4: Implement ReservedRange CRUD and Allocation Guard

**Files:**
- Create: `OneOPS/app/ipam/dto/reserved_range.go`
- Create: `OneOPS/app/ipam/service/i_reserved_range.go`
- Create: `OneOPS/app/ipam/service/impl/reserved_range.go`
- Create: `OneOPS/app/ipam/api/reserved_range.go`
- Create: `OneOPS/app/ipam/router/reserved_range.go`
- Modify: provider and route files from Task 3
- Test: `OneOPS/app/ipam/service/impl/reserved_range_test.go`

- [ ] **Step 1: Create ReservedRange DTO**

Create `OneOPS/app/ipam/dto/reserved_range.go`:

```go
package dto

import (
	commonDTO "github.com/netxops/OneOps/app/common/dto"
	"github.com/netxops/OneOps/app/common/pagination"
)

type ReservedRangeReq struct {
	commonDTO.Common
	Code                   string `json:"code" validate:"max=32"`
	PrefixCode             string `json:"prefix_code" validate:"required,max=128"`
	PrefixCIDR             string `json:"prefix_cidr" validate:"-"`
	PoolCode               string `json:"pool_code" validate:"max=32"`
	StartIP                string `json:"start_ip" validate:"required,max=64"`
	EndIP                  string `json:"end_ip" validate:"required,max=64"`
	Reason                 string `json:"reason" validate:"required,max=64"`
	AllowSpecialAllocation bool   `json:"allow_special_allocation"`
	Description            string `json:"description" validate:"max=255"`
}

type ReservedRangeResp struct {
	commonDTO.Common
	Code                   string `json:"code"`
	PrefixCode             string `json:"prefix_code"`
	PoolCode               string `json:"pool_code"`
	StartIP                string `json:"start_ip"`
	EndIP                  string `json:"end_ip"`
	Reason                 string `json:"reason"`
	AllowSpecialAllocation bool   `json:"allow_special_allocation"`
	Description            string `json:"description"`
}

type ReservedRangePage struct {
	pagination.Page
	ReservedRangeReq
}
```

- [ ] **Step 2: Implement service, API, router using AddressPool pattern**

Implement `ReservedRangeSrv` with the same CRUD shape as `AddressPoolSrv`, using:

```go
func (s *ReservedRangeSrv) IsAddressReserved(ipValue string, prefixCode string, ctx context.Context) (bool, *dto.ReservedRangeResp, error) {
	t := s.ProxySrv.Query(ctx).ReservedRange
	ranges, err := t.WithContext(ctx).Where(t.PrefixCode.Eq(prefixCode)).Find()
	if err != nil {
		return false, nil, err
	}
	for _, item := range ranges {
		if ipRangeContains(ipValue, item.StartIP, item.EndIP) {
			resp := &dto.ReservedRangeResp{}
			if copyErr := copier.Copy(resp, item); copyErr != nil {
				return false, nil, copyErr
			}
			return true, resp, nil
		}
	}
	return false, nil, nil
}
```

Expose routes:

```text
POST   /ipam/reserved-ranges
POST   /ipam/reserved-ranges/list
GET    /ipam/reserved-ranges/:code
PUT    /ipam/reserved-ranges
DELETE /ipam/reserved-ranges/:code
```

- [ ] **Step 3: Register providers and routes**

Add:

```go
ipamSrv.ReservedRangeSet
ipamAPI.ReservedRangeAPISet
ipamRouter.ReservedRange(private, r.ReservedRangeAPI)
```

- [ ] **Step 4: Run focused tests**

```bash
cd /Users/huangliang/project/OneOPS-ALL/OneOPS
go test ./app/ipam/service/impl -run 'Test(ReservedRange|AddressPool|IPAMAddressMath)' -count=1
```

Expected: PASS.

- [ ] **Step 5: Commit reserved ranges**

```bash
cd /Users/huangliang/project/OneOPS-ALL
git add OneOPS/app/ipam/dto/reserved_range.go OneOPS/app/ipam/service/i_reserved_range.go OneOPS/app/ipam/service/impl/reserved_range.go OneOPS/app/ipam/api/reserved_range.go OneOPS/app/ipam/router/reserved_range.go OneOPS/boot/provider/service_groups.go OneOPS/boot/provider/api.go OneOPS/initialize/routers.go OneOPS/app/ipam/service/impl/reserved_range_test.go
git commit -m "feat(ipam): add reserved range management"
```

---

### Task 5: Add IP Request, Allocation, Release, and Reclaim

**Files:**
- Create: `OneOPS/app/ipam/dto/ip_address_request.go`
- Create: `OneOPS/app/ipam/service/i_ip_address_request.go`
- Create: `OneOPS/app/ipam/service/impl/ip_address_request.go`
- Create: `OneOPS/app/ipam/api/ip_address_request.go`
- Create: `OneOPS/app/ipam/router/ip_address_request.go`
- Modify: `OneOPS/app/ipam/service/impl/ip_address.go`
- Test: `OneOPS/app/ipam/service/impl/ip_address_request_test.go`

- [ ] **Step 1: Create request DTO**

Create `OneOPS/app/ipam/dto/ip_address_request.go` with request fields matching the model and response fields including allocated addresses:

```go
package dto

import (
	commonDTO "github.com/netxops/OneOps/app/common/dto"
	"github.com/netxops/OneOps/app/common/pagination"
	"github.com/netxops/OneOps/app/ipam/enum"
)

type IPAddressRequestReq struct {
	commonDTO.Common
	Code            string                    `json:"code" validate:"max=32"`
	RequestType     enum.IPAddressRequestType `json:"request_type" validate:"required"`
	Requester       string                    `json:"requester" validate:"max=64"`
	TenantCode      string                    `json:"tenant_code" validate:"max=32"`
	SiteCode        string                    `json:"site_code" validate:"max=32"`
	SecurityZoneID  string                    `json:"security_zone_id" validate:"max=36"`
	PlatformVrfCode string                    `json:"platform_vrf_code" validate:"max=32"`
	PoolCode        string                    `json:"pool_code" validate:"max=32"`
	Quantity        int                       `json:"quantity"`
	PreferredIP     string                    `json:"preferred_ip" validate:"max=64"`
	Purpose         string                    `json:"purpose" validate:"max=64"`
	BusinessSystem  string                    `json:"business_system" validate:"max=128"`
	Description     string                    `json:"description" validate:"max=255"`
}

type IPAddressRequestResp struct {
	commonDTO.Common
	Code               string                      `json:"code"`
	RequestType        enum.IPAddressRequestType   `json:"request_type"`
	Requester          string                      `json:"requester"`
	TenantCode         string                      `json:"tenant_code"`
	SiteCode           string                      `json:"site_code"`
	SecurityZoneID     string                      `json:"security_zone_id"`
	PlatformVrfCode    string                      `json:"platform_vrf_code"`
	PoolCode           string                      `json:"pool_code"`
	Quantity           int                         `json:"quantity"`
	PreferredIP        string                      `json:"preferred_ip"`
	Purpose            string                      `json:"purpose"`
	BusinessSystem     string                      `json:"business_system"`
	Status             enum.IPAddressRequestStatus `json:"status"`
	AllocatedAddresses []IPAddressResp             `json:"allocated_addresses"`
	Description        string                      `json:"description"`
}

type IPAddressRequestPage struct {
	pagination.Page
	IPAddressRequestReq
	Status enum.IPAddressRequestStatus `json:"status"`
}
```

- [ ] **Step 2: Implement allocation service**

Create `IPAddressRequestSrv` with these public methods:

```go
type IIPAddressRequest interface {
	Create(r dto.IPAddressRequestReq, ctx context.Context) (*dto.IPAddressRequestResp, error)
	ApproveAndAllocate(code string, ctx context.Context) (*dto.IPAddressRequestResp, error)
	Release(ipCode string, ctx context.Context) error
	Reclaim(ipCode string, force bool, ctx context.Context) error
	PageList(r dto.IPAddressRequestPage, ctx context.Context) (pagination.Page, error)
}
```

Allocation algorithm:

```go
func (s *IPAddressRequestSrv) findFirstAvailableAddress(pool *ipamModel.AddressPool, ctx context.Context) (string, error) {
	start := ipToBigInt(pool.StartIP)
	end := ipToBigInt(pool.EndIP)
	if start == nil || end == nil || start.Cmp(end) > 0 {
		return "", errors.New("地址池范围不合法")
	}
	for current := new(big.Int).Set(start); current.Cmp(end) <= 0; current.Add(current, big.NewInt(1)) {
		candidate := intToIPv4(current)
		used, err := s.isAddressUsed(candidate, pool.Code, ctx)
		if err != nil {
			return "", err
		}
		if used {
			continue
		}
		reserved, reservedRange, err := s.ReservedRangeSrv.IsAddressReserved(candidate, pool.PrefixCode, ctx)
		if err != nil {
			return "", err
		}
		if reserved && !reservedRange.AllowSpecialAllocation {
			continue
		}
		return candidate, nil
	}
	return "", errors.New("地址池无可用地址")
}
```

Add helper:

```go
func intToIPv4(value *big.Int) string {
	bytes := value.Bytes()
	padded := make([]byte, 4)
	copy(padded[4-len(bytes):], bytes)
	return net.IP(padded).String()
}
```

- [ ] **Step 3: Extend IPAddress service for lifecycle updates**

Add to `OneOPS/app/ipam/service/impl/ip_address.go`:

```go
func (s *IPAddressSrv) UpdateLifecycle(code string, lifecycle enum.IPAddressLifecycleStatus, ctx context.Context) error {
	if strings.TrimSpace(code) == "" {
		return errors.New("ip编码不能为空")
	}
	t := s.ProxySrv.Query(ctx).IPAddress
	_, err := t.WithContext(ctx).Where(t.Code.Eq(code)).UpdateColumn(t.LifecycleStatus, lifecycle)
	return err
}
```

Add the method to `OneOPS/app/ipam/service/i_ip_address.go`.

- [ ] **Step 4: Add request API routes**

Expose:

```text
POST /ipam/address-requests
POST /ipam/address-requests/list
POST /ipam/address-requests/:code/approve-allocate
POST /ipam/address-requests/release/:ip_code
POST /ipam/address-requests/reclaim/:ip_code
```

- [ ] **Step 5: Run focused tests**

```bash
cd /Users/huangliang/project/OneOPS-ALL/OneOPS
go test ./app/ipam/service/impl -run 'Test(IPAddressRequest|ReservedRange|AddressPool|IPAMAddressMath)' -count=1
```

Expected: PASS.

- [ ] **Step 6: Commit request workflow**

```bash
cd /Users/huangliang/project/OneOPS-ALL
git add OneOPS/app/ipam/dto/ip_address_request.go OneOPS/app/ipam/service/i_ip_address_request.go OneOPS/app/ipam/service/i_ip_address.go OneOPS/app/ipam/service/impl/ip_address_request.go OneOPS/app/ipam/service/impl/ip_address.go OneOPS/app/ipam/api/ip_address_request.go OneOPS/app/ipam/router/ip_address_request.go OneOPS/boot/provider/service_groups.go OneOPS/boot/provider/api.go OneOPS/initialize/routers.go OneOPS/app/ipam/service/impl/ip_address_request_test.go
git commit -m "feat(ipam): add IP request allocation and reclaim"
```

---

### Task 6: Add Observed Facts and Audit Findings

**Files:**
- Create: `OneOPS/app/ipam/dto/ip_address_fact.go`
- Create: `OneOPS/app/ipam/dto/ip_address_audit_finding.go`
- Create: `OneOPS/app/ipam/service/i_ip_address_fact.go`
- Create: `OneOPS/app/ipam/service/i_ip_address_audit_finding.go`
- Create: `OneOPS/app/ipam/service/impl/ip_address_fact.go`
- Create: `OneOPS/app/ipam/service/impl/ip_address_audit_finding.go`
- Create: `OneOPS/app/ipam/api/ip_address_audit_finding.go`
- Create: `OneOPS/app/ipam/router/ip_address_audit_finding.go`
- Test: `OneOPS/app/ipam/service/impl/ip_address_audit_finding_test.go`

- [ ] **Step 1: Implement fact sync from IPAMAgg**

In `IPAddressFactSrv`, implement:

```go
func (s *IPAddressFactSrv) SyncFromIPAMAgg(ctx context.Context) error {
	aggT := s.ProxySrv.Query(ctx).IPAMAgg
	factT := s.ProxySrv.Query(ctx).IPAddressFact
	items, err := aggT.WithContext(ctx).Find()
	if err != nil {
		return err
	}
	now := time.Now()
	for _, item := range items {
		if strings.TrimSpace(item.IPAddress) == "" {
			continue
		}
		fact, err := factT.WithContext(ctx).Where(factT.IPAddress.Eq(item.IPAddress), factT.Source.Eq("ipam_agg")).FirstOrInit()
		if err != nil {
			return err
		}
		if fact.ID == "" {
			fact.Code, err = s.GenerateCodeSrv.GenerateCode("IPFACT", 6)
			if err != nil {
				return err
			}
			fact.FirstSeenAt = &now
		}
		fact.IPAddress = item.IPAddress
		fact.IPVersion = 4
		fact.DeviceCode = item.DevCode
		fact.DeviceName = item.DevName
		fact.InterfaceCode = item.PortCode
		fact.InterfaceName = item.Port
		fact.MacCode = item.MacAddressCode
		fact.MacAddress = item.MacAddress
		fact.PlatformVrfCode = item.VrfCode
		fact.Source = "ipam_agg"
		fact.LastSeenAt = &now
		fact.Confidence = 90
		if fact.ID == "" {
			if err = factT.WithContext(ctx).Create(fact); err != nil {
				return err
			}
		} else if err = factT.WithContext(ctx).Save(fact); err != nil {
			return err
		}
	}
	return nil
}
```

- [ ] **Step 2: Implement audit finding generation**

In `IPAddressAuditFindingSrv`, implement audit rules:

```go
const (
	findingUnregisteredUsage = "unregistered_usage"
	findingDuplicateUsage    = "duplicate_usage"
	findingOutOfRangeUsage   = "out_of_range_usage"
	findingPlannedUnused     = "planned_unused"
	findingInterfaceDrift    = "interface_drift"
)
```

Implement `RunGlobalAudit(ctx)` that:

- Loads all `IPAddressFact`.
- Loads all `IPAddress`.
- Creates `unregistered_usage` if a fact IP has no matching `IPAddress.Address`.
- Creates `interface_drift` if a matching IP has different `DeviceInterfaceCode` from fact interface.
- Creates `planned_unused` if assigned IP has `LastSeenAt` empty.

- [ ] **Step 3: Add finding API**

Expose:

```text
POST /ipam/audit-findings/run
POST /ipam/audit-findings/list
POST /ipam/audit-findings/:code/acknowledge
POST /ipam/audit-findings/:code/ignore
POST /ipam/audit-findings/:code/resolve
```

- [ ] **Step 4: Run focused tests**

```bash
cd /Users/huangliang/project/OneOPS-ALL/OneOPS
go test ./app/ipam/service/impl -run 'Test(IPAddressAuditFinding|IPAddressRequest|ReservedRange|AddressPool|IPAMAddressMath)' -count=1
```

Expected: PASS.

- [ ] **Step 5: Commit audit facts**

```bash
cd /Users/huangliang/project/OneOPS-ALL
git add OneOPS/app/ipam/dto/ip_address_fact.go OneOPS/app/ipam/dto/ip_address_audit_finding.go OneOPS/app/ipam/service/i_ip_address_fact.go OneOPS/app/ipam/service/i_ip_address_audit_finding.go OneOPS/app/ipam/service/impl/ip_address_fact.go OneOPS/app/ipam/service/impl/ip_address_audit_finding.go OneOPS/app/ipam/api/ip_address_audit_finding.go OneOPS/app/ipam/router/ip_address_audit_finding.go OneOPS/boot/provider/service_groups.go OneOPS/boot/provider/api.go OneOPS/initialize/routers.go OneOPS/app/ipam/service/impl/ip_address_audit_finding_test.go
git commit -m "feat(ipam): add observed IP audit findings"
```

---

### Task 7: Add IPAM Statistics

**Files:**
- Create: `OneOPS/app/ipam/dto/ipam_statistics.go`
- Create: `OneOPS/app/ipam/service/i_ipam_statistics.go`
- Create: `OneOPS/app/ipam/service/impl/ipam_statistics.go`
- Create: `OneOPS/app/ipam/api/ipam_statistics.go`
- Create: `OneOPS/app/ipam/router/ipam_statistics.go`
- Test: `OneOPS/app/ipam/service/impl/ipam_statistics_test.go`

- [ ] **Step 1: Add statistics DTO**

Create `OneOPS/app/ipam/dto/ipam_statistics.go`:

```go
package dto

type IPAMStatisticsReq struct {
	TenantCode      string `json:"tenant_code"`
	PlatformVrfCode string `json:"platform_vrf_code"`
	SecurityZoneID  string `json:"security_zone_id"`
	PrefixCode      string `json:"prefix_code"`
	PoolCode        string `json:"pool_code"`
	SiteCode        string `json:"site_code"`
}

type IPAMStatisticsResp struct {
	TotalAddresses       int64   `json:"total_addresses"`
	UsableAddresses      int64   `json:"usable_addresses"`
	ReservedAddresses    int64   `json:"reserved_addresses"`
	AssignedAddresses    int64   `json:"assigned_addresses"`
	ReleasingAddresses   int64   `json:"releasing_addresses"`
	AvailableAddresses   int64   `json:"available_addresses"`
	ObservedUnmanaged    int64   `json:"observed_unmanaged"`
	ConflictCount        int64   `json:"conflict_count"`
	UtilizationPercent   float64 `json:"utilization_percent"`
	CapacityThresholdHit bool    `json:"capacity_threshold_hit"`
}
```

- [ ] **Step 2: Implement statistics service**

Create `IPAMStatisticsSrv.Summary(r dto.IPAMStatisticsReq, ctx context.Context)` using `IPAddress`, `AddressPool`, `ReservedRange`, and `IPAddressAuditFinding` queries. Count lifecycle statuses with existing `LifecycleStatus` values.

Utilization formula:

```go
func utilization(assigned int64, reserved int64, usable int64) float64 {
	if usable <= 0 {
		return 0
	}
	return float64(assigned+reserved) * 100 / float64(usable)
}
```

- [ ] **Step 3: Expose statistics route**

Expose:

```text
POST /ipam/statistics/summary
```

- [ ] **Step 4: Run focused tests**

```bash
cd /Users/huangliang/project/OneOPS-ALL/OneOPS
go test ./app/ipam/service/impl -run 'Test(IPAMStatistics|IPAddressAuditFinding|IPAddressRequest|ReservedRange|AddressPool|IPAMAddressMath)' -count=1
```

Expected: PASS.

- [ ] **Step 5: Commit statistics**

```bash
cd /Users/huangliang/project/OneOPS-ALL
git add OneOPS/app/ipam/dto/ipam_statistics.go OneOPS/app/ipam/service/i_ipam_statistics.go OneOPS/app/ipam/service/impl/ipam_statistics.go OneOPS/app/ipam/api/ipam_statistics.go OneOPS/app/ipam/router/ipam_statistics.go OneOPS/boot/provider/service_groups.go OneOPS/boot/provider/api.go OneOPS/initialize/routers.go OneOPS/app/ipam/service/impl/ipam_statistics_test.go
git commit -m "feat(ipam): add address utilization statistics"
```

---

### Task 8: Add Frontend API Types and Request Functions

**Files:**
- Create: `OneOPS-UI/src/typings/ipam/address_pool.ts`
- Create: `OneOPS-UI/src/api/ipam/address_pool.ts`
- Create: `OneOPS-UI/src/typings/ipam/reserved_range.ts`
- Create: `OneOPS-UI/src/api/ipam/reserved_range.ts`
- Create: `OneOPS-UI/src/typings/ipam/ip_address_request.ts`
- Create: `OneOPS-UI/src/api/ipam/ip_address_request.ts`
- Create: `OneOPS-UI/src/typings/ipam/ip_address_audit_finding.ts`
- Create: `OneOPS-UI/src/api/ipam/ip_address_audit_finding.ts`
- Create: `OneOPS-UI/src/typings/ipam/ipam_statistics.ts`
- Create: `OneOPS-UI/src/api/ipam/ipam_statistics.ts`
- Modify: `OneOPS-UI/src/typings/ipam/ip_address.ts`

- [ ] **Step 1: Add AddressPool typings and API**

Create `OneOPS-UI/src/typings/ipam/address_pool.ts`:

```ts
import { Common } from '../common/common';
import { PaginationReq } from '../common/pagination';

export interface AddressPoolPageReq extends PaginationReq {
  code?: string;
  name?: string;
  prefix_code?: string;
  tenant_code?: string;
  platform_vrf_code?: string;
  security_zone_id?: string;
  site_code?: string;
}

export interface AddressPoolResp extends Common {
  code: string;
  name: string;
  prefix_code: string;
  start_ip: string;
  end_ip: string;
  purpose: string;
  tenant_code: string;
  platform_vrf_code: string;
  security_zone_id: string;
  site_code: string;
  allocation_policy: string;
  capacity_threshold: number;
  status: string;
  description: string;
}

export interface AddressPoolReq extends Common {
  code?: string;
  name: string;
  prefix_code: string;
  start_ip: string;
  end_ip: string;
  purpose?: string;
  tenant_code?: string;
  platform_vrf_code?: string;
  security_zone_id?: string;
  site_code?: string;
  allocation_policy?: string;
  capacity_threshold?: number;
  status?: string;
  description?: string;
}
```

Create `OneOPS-UI/src/api/ipam/address_pool.ts`:

```ts
import { AddressPoolPageReq, AddressPoolReq, AddressPoolResp } from '@/typings/ipam/address_pool';
import { PaginationResp } from '@/typings/common/pagination';
import request, { HTTP_DELETE, HTTP_GET, HTTP_POST, HTTP_PUT } from '@/utils/request';

export const addressPoolPageReq = async (data: AddressPoolPageReq) => {
  return request<PaginationResp<AddressPoolResp>>({
    url: '/ipam/address-pools/list',
    method: HTTP_POST,
    data,
  });
};

export const addressPoolCreateReq = async (data: AddressPoolReq) => {
  return request<AddressPoolResp>({
    url: '/ipam/address-pools',
    method: HTTP_POST,
    data,
  });
};

export const addressPoolUpdateReq = async (data: AddressPoolReq) => {
  return request<AddressPoolResp>({
    url: '/ipam/address-pools',
    method: HTTP_PUT,
    data,
  });
};

export const addressPoolFindReq = async (code: string) => {
  return request<AddressPoolResp>({
    url: `/ipam/address-pools/${code}`,
    method: HTTP_GET,
  });
};

export const addressPoolDeleteReq = async (code: string) => {
  return request({
    url: `/ipam/address-pools/${code}`,
    method: HTTP_DELETE,
  });
};
```

- [ ] **Step 2: Add remaining frontend API files**

Create these API wrappers with the same `request` utility style as `address_pool.ts`:

```ts
// OneOPS-UI/src/api/ipam/reserved_range.ts
export const reservedRangePageReq = async (data: ReservedRangePageReq) => request<PaginationResp<ReservedRangeResp>>({ url: '/ipam/reserved-ranges/list', method: HTTP_POST, data });
export const reservedRangeCreateReq = async (data: ReservedRangeReq) => request<ReservedRangeResp>({ url: '/ipam/reserved-ranges', method: HTTP_POST, data });
export const reservedRangeUpdateReq = async (data: ReservedRangeReq) => request<ReservedRangeResp>({ url: '/ipam/reserved-ranges', method: HTTP_PUT, data });
export const reservedRangeFindReq = async (code: string) => request<ReservedRangeResp>({ url: `/ipam/reserved-ranges/${code}`, method: HTTP_GET });
export const reservedRangeDeleteReq = async (code: string) => request({ url: `/ipam/reserved-ranges/${code}`, method: HTTP_DELETE });
```

```ts
// OneOPS-UI/src/api/ipam/ip_address_request.ts
export const ipAddressRequestPageReq = async (data: IPAddressRequestPageReq) => request<PaginationResp<IPAddressRequestResp>>({ url: '/ipam/address-requests/list', method: HTTP_POST, data });
export const ipAddressRequestCreateReq = async (data: IPAddressRequestReq) => request<IPAddressRequestResp>({ url: '/ipam/address-requests', method: HTTP_POST, data });
export const ipAddressRequestApproveAllocateReq = async (code: string) => request<IPAddressRequestResp>({ url: `/ipam/address-requests/${code}/approve-allocate`, method: HTTP_POST });
export const ipAddressReleaseReq = async (ipCode: string) => request({ url: `/ipam/address-requests/release/${ipCode}`, method: HTTP_POST });
export const ipAddressReclaimReq = async (ipCode: string) => request({ url: `/ipam/address-requests/reclaim/${ipCode}`, method: HTTP_POST });
```

```ts
// OneOPS-UI/src/api/ipam/ip_address_audit_finding.ts
export const ipAddressAuditRunReq = async () => request({ url: '/ipam/audit-findings/run', method: HTTP_POST });
export const ipAddressAuditFindingPageReq = async (data: IPAddressAuditFindingPageReq) => request<PaginationResp<IPAddressAuditFindingResp>>({ url: '/ipam/audit-findings/list', method: HTTP_POST, data });
export const ipAddressAuditFindingAcknowledgeReq = async (code: string) => request({ url: `/ipam/audit-findings/${code}/acknowledge`, method: HTTP_POST });
export const ipAddressAuditFindingIgnoreReq = async (code: string) => request({ url: `/ipam/audit-findings/${code}/ignore`, method: HTTP_POST });
export const ipAddressAuditFindingResolveReq = async (code: string) => request({ url: `/ipam/audit-findings/${code}/resolve`, method: HTTP_POST });
```

```ts
// OneOPS-UI/src/api/ipam/ipam_statistics.ts
export const ipamStatisticsSummaryReq = async (data: IPAMStatisticsReq) => request<IPAMStatisticsResp>({ url: '/ipam/statistics/summary', method: HTTP_POST, data });
```

Create typings that match the DTO names and JSON fields from Tasks 4-7:

```text
ReservedRangePageReq, ReservedRangeReq, ReservedRangeResp
IPAddressRequestPageReq, IPAddressRequestReq, IPAddressRequestResp
IPAddressAuditFindingPageReq, IPAddressAuditFindingResp
IPAMStatisticsReq, IPAMStatisticsResp
```

- [ ] **Step 3: Extend IPAddress frontend typing**

In `OneOPS-UI/src/typings/ipam/ip_address.ts`, add fields to `IPAddressResp`:

```ts
  lifecycle_status: string;
  pool_code: string;
  request_code: string;
  owner_type: string;
  owner_code: string;
  security_zone_id: string;
  last_seen_at: string;
  source: string;
```

Add these writable fields to `IPAddressReq`:

```ts
  lifecycle_status?: string;
  pool_code?: string;
  request_code?: string;
  owner_type?: string;
  owner_code?: string;
  security_zone_id?: string;
  source?: string;
```

- [ ] **Step 4: Commit frontend contracts**

```bash
cd /Users/huangliang/project/OneOPS-ALL
git add OneOPS-UI/src/api/ipam OneOPS-UI/src/typings/ipam
git commit -m "feat(ui): add IPAM address management API contracts"
```

---

## Final Verification

- [ ] **Run focused backend tests**

```bash
cd /Users/huangliang/project/OneOPS-ALL/OneOPS
go test ./app/ipam/service/impl -count=1
```

Expected: PASS.

- [ ] **Run DAO generation check**

```bash
cd /Users/huangliang/project/OneOPS-ALL/OneOPS
go run ./cmd/gen/mysql/gen.go
```

Expected: generated files are stable or only expected IPAM DAO files change.

- [ ] **Run frontend type check if project command exists**

Inspect `OneOPS-UI/package.json` scripts and run the type-check or build command that the project already uses.

Expected: frontend API typings compile.

## Spec Coverage Review

- Enterprise-wide address planning: covered by `AddressPool`, `ReservedRange`, prefix binding, and security-zone context.
- IP address statistics: covered by `IPAMStatisticsSrv`.
- Automatic collection and audit: covered by `IPAddressFactSrv.SyncFromIPAMAgg` and `IPAddressAuditFindingSrv`.
- IP request/reclaim workflow: covered by `IPAddressRequestSrv`.
- Existing platform VRF compatibility: `VrfCode` remains platform VRF; new fields do not reinterpret it.
- Security-zone association: `SecurityZoneID` exists on address pool and address records; `NetworkSegment.PrefixCode` remains reusable.
- Topology diagrams: out of implementation scope; data relationships are prepared through fact and binding models.

## Execution Choice

Plan complete and saved to `docs/superpowers/plans/2026-06-18-ipam-address-management.md`. Two execution options:

**1. Subagent-Driven (recommended)** - Dispatch a fresh subagent per task, review between tasks, fast iteration.

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints.

Which approach?
