# OneOPS Device V2 导入模板多形态下载 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 Device V2 导入页增加 3 类下载模板（全量字段、凭证引用、账密），并保持中英文表头切换与现有上传兼容性。

**Architecture:** 后端继续作为模板字段事实源，在 `dto` 中增加模板类型和字段分组，由下载服务按 `template_type + header_lang` 动态投影表头、示例行和文件名。前端只扩展 URL builder 与下载菜单，不复制字段定义；测试采用后端 `go test` 锁定模板边界，前端用现有 smoke 脚本校验菜单与 URL 拼接。

**Tech Stack:** Go 1.25, Gin, tealeg/xlsx, Vue 3, TypeScript, Ant Design Vue, esbuild-based smoke scripts

---

### Task 1: 锁定后端模板类型合同

**Files:**
- Modify: `OneOps/app/device/v2/ingest/api/device_v2_ingest_test.go`
- Modify: `OneOps/app/device/v2/ingest/service/impl/device_v2_ingest_excel_test.go`

- [ ] **Step 1: Write the failing API download tests**

```go
func TestDeviceV2IngestAPI_DownloadExcelTemplateCredentialRefVariant(t *testing.T) {
	engine, _ := newDeviceV2IngestTestEngine(t)

	req := httptest.NewRequest(http.MethodGet, "/api/v1/device/v2/ingest/template/excel?template_type=credential_ref", nil)
	rec := httptest.NewRecorder()
	engine.ServeHTTP(rec, req)

	if rec.Code != http.StatusOK {
		t.Fatalf("unexpected http status: %d body=%s", rec.Code, rec.Body.String())
	}
	workbook, err := xlsx.OpenBinary(rec.Body.Bytes())
	if err != nil {
		t.Fatalf("open template xlsx failed: %v", err)
	}
	headers := firstSheetHeaders(t, workbook, "devices")
	assertHeadersContainAll(t, headers, []string{"credential_ref_in_band", "snmp_credential_ref", "credential_ref_out_band"})
	assertHeadersAbsent(t, headers, []string{"in_band_username", "in_band_password", "out_band_username", "out_band_password", "ipmi_username", "ipmi_password"})
}

func TestDeviceV2IngestAPI_DownloadExcelTemplateAccountPasswordVariant(t *testing.T) {
	engine, _ := newDeviceV2IngestTestEngine(t)

	req := httptest.NewRequest(http.MethodGet, "/api/v1/device/v2/ingest/template/excel?template_type=account_password", nil)
	rec := httptest.NewRecorder()
	engine.ServeHTTP(rec, req)

	if rec.Code != http.StatusOK {
		t.Fatalf("unexpected http status: %d body=%s", rec.Code, rec.Body.String())
	}
	workbook, err := xlsx.OpenBinary(rec.Body.Bytes())
	if err != nil {
		t.Fatalf("open template xlsx failed: %v", err)
	}
	headers := firstSheetHeaders(t, workbook, "devices")
	assertHeadersContainAll(t, headers, []string{"in_band_username", "in_band_password", "out_band_username", "out_band_password"})
	assertHeadersAbsent(t, headers, []string{"credential_ref_in_band", "credential_ref_out_band", "snmp_credential_ref", "winrm_credential_ref", "credential_refs"})
}
```

- [ ] **Step 2: Write the failing service-level projection tests**

```go
func TestResolveDeviceV2IngestExcelTemplateHeadersUsesCredentialRefSubset(t *testing.T) {
	headers, filename := resolveDeviceV2IngestExcelTemplateHeaders("en", "credential_ref")
	if filename != ingestdto.DeviceV2IngestExcelCredentialRefTemplateFilename {
		t.Fatalf("unexpected filename: %s", filename)
	}
	assertSliceContainsAll(t, headers, []string{"credential_ref_in_band", "credential_ref_out_band", "snmp_credential_ref"})
	assertSliceAbsent(t, headers, []string{"in_band_username", "out_band_password", "ipmi_username"})
}

func TestResolveDeviceV2IngestExcelTemplateHeadersUsesAccountPasswordSubset(t *testing.T) {
	headers, filename := resolveDeviceV2IngestExcelTemplateHeaders("zh", "account_password")
	if filename != ingestdto.DeviceV2IngestExcelChineseAccountPasswordTemplateFilename {
		t.Fatalf("unexpected filename: %s", filename)
	}
	assertSliceContainsAll(t, headers, []string{"带内用户名", "带内密码", "带外用户名", "带外密码"})
	assertSliceAbsent(t, headers, []string{"带内凭据引用", "带外凭据引用", "SNMP 凭据引用", "凭据引用明细"})
}
```

- [ ] **Step 3: Run tests to verify they fail**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps && go test ./app/device/v2/ingest/api ./app/device/v2/ingest/service/impl -run 'Template|resolveDeviceV2IngestExcelTemplateHeaders' -count=1
```

Expected:

- FAIL because `template_type` is ignored
- FAIL because new filenames/constants/helpers do not exist yet

- [ ] **Step 4: Commit checkpoint**

```bash
git add OneOps/app/device/v2/ingest/api/device_v2_ingest_test.go OneOps/app/device/v2/ingest/service/impl/device_v2_ingest_excel_test.go
git commit -m "test: lock device v2 ingest template variants"
```

### Task 2: 实现后端模板类型与文件名投影

**Files:**
- Modify: `OneOps/app/device/v2/ingest/dto/device_v2_ingest_excel.go`
- Modify: `OneOps/app/device/v2/ingest/service/i_device_v2_ingest.go`
- Modify: `OneOps/app/device/v2/ingest/service/impl/device_v2_ingest_excel.go`
- Modify: `OneOps/app/device/v2/ingest/api/device_v2_ingest.go`

- [ ] **Step 1: Add template-type constants and header grouping**

```go
const (
	DeviceV2IngestExcelTemplateTypeFull            = "full"
	DeviceV2IngestExcelTemplateTypeCredentialRef   = "credential_ref"
	DeviceV2IngestExcelTemplateTypeAccountPassword = "account_password"
)

var deviceV2IngestExcelBaseHeaders = []string{ /* shared identity, location, access, asset fields */ }
var deviceV2IngestExcelCredentialRefHeaders = []string{
	"credential_ref_in_band", "snmp_credential_ref", "winrm_credential_ref", "credential_ref_out_band", "credential_refs",
}
var deviceV2IngestExcelAccountPasswordHeaders = []string{
	"in_band_username", "in_band_password", "out_band_username", "out_band_password", "snmp_username", "snmp_auth_password",
	"snmp_priv_password", "ipmi_username", "ipmi_password", "redfish_username", "redfish_password",
}
var deviceV2IngestExcelFullOnlyHeaders = []string{
	"access_points", "system_version", "patch_version", "firmware_version", "kernel_version", "os_name", "os_version",
	"architecture", "cpu_arch", "cpu_model", "cpu_cores", "cpu_sockets", "memory_total", "memory_total_bytes", "memory_slots", "hardware",
}
```

- [ ] **Step 2: Add helper functions for header projection and example-row projection**

```go
func ResolveDeviceV2IngestExcelHeaderKeys(templateType string) []string {
	switch normalizeDeviceV2IngestExcelTemplateType(templateType) {
	case DeviceV2IngestExcelTemplateTypeCredentialRef:
		return append(append([]string{}, deviceV2IngestExcelBaseHeaders...), deviceV2IngestExcelCredentialRefHeaders...)
	case DeviceV2IngestExcelTemplateTypeAccountPassword:
		return append(append([]string{}, deviceV2IngestExcelBaseHeaders...), deviceV2IngestExcelAccountPasswordHeaders...)
	default:
		out := append([]string{}, deviceV2IngestExcelBaseHeaders...)
		out = append(out, deviceV2IngestExcelCredentialRefHeaders...)
		out = append(out, deviceV2IngestExcelAccountPasswordHeaders...)
		out = append(out, deviceV2IngestExcelFullOnlyHeaders...)
		return out
	}
}

func DeviceV2IngestExcelHeadersForLang(headerLang, templateType string) []string { /* map keys to zh/en labels */ }
func DeviceV2IngestExcelExampleRowsForKeys(keys []string) [][]string { /* project map-based examples by key */ }
```

- [ ] **Step 3: Thread `templateType` through API and service**

```go
type IDeviceV2Ingest interface {
	DownloadExcelTemplate(ctx context.Context, headerLang, templateType string) ([]byte, string, error)
}

func (a *DeviceV2IngestAPI) DownloadExcelTemplate(ctx *gin.Context) {
	content, filename, err := a.DeviceV2IngestSrv.DownloadExcelTemplate(
		ctx.Request.Context(),
		strings.TrimSpace(ctx.Query("header_lang")),
		strings.TrimSpace(ctx.Query("template_type")),
	)
	// ...
}
```

- [ ] **Step 4: Generate the workbook from projected headers**

```go
func (s *DeviceV2IngestSrv) DownloadExcelTemplate(ctx context.Context, headerLang, templateType string) ([]byte, string, error) {
	_ = ctx
	headers, filename := resolveDeviceV2IngestExcelTemplateHeaders(headerLang, templateType)
	rows := dto.DeviceV2IngestExcelExampleRowsForKeys(dto.ResolveDeviceV2IngestExcelHeaderKeys(templateType))
	workbook := xlsx.NewFile()
	sheet, err := workbook.AddSheet(dto.DeviceV2IngestExcelSheetName)
	if err != nil {
		return nil, "", fmt.Errorf("创建模板 Sheet 失败: %w", err)
	}
	headerRow := sheet.AddRow()
	for _, header := range headers {
		headerRow.AddCell().SetString(header)
	}
	for _, values := range rows {
		row := sheet.AddRow()
		for _, value := range values {
			row.AddCell().SetString(strings.TrimSpace(value))
		}
	}
	// write buffer...
}
```

- [ ] **Step 5: Run tests to verify they pass**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps && go test ./app/device/v2/ingest/api ./app/device/v2/ingest/service/impl -run 'Template|resolveDeviceV2IngestExcelTemplateHeaders' -count=1
```

Expected:

- PASS
- No header-misalignment failures

- [ ] **Step 6: Commit checkpoint**

```bash
git add OneOps/app/device/v2/ingest/dto/device_v2_ingest_excel.go OneOps/app/device/v2/ingest/service/i_device_v2_ingest.go OneOps/app/device/v2/ingest/service/impl/device_v2_ingest_excel.go OneOps/app/device/v2/ingest/api/device_v2_ingest.go
git commit -m "feat: add device v2 ingest template variants"
```

### Task 3: 扩展前端下载参数与菜单

**Files:**
- Modify: `OneOPS-UI/src/api/device/device-v2-ingest.ts`
- Modify: `OneOPS-UI/src/views/device/DeviceV2IngestPipelineRedesign.vue`
- Create: `OneOPS-UI/scripts/d2-ingest-template-variants-smoke.ts`

- [ ] **Step 1: Write the failing frontend smoke**

```ts
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

import { buildDeviceV2IngestExcelTemplateURL } from '../src/api/device/device-v2-ingest';

const page = readFileSync('src/views/device/DeviceV2IngestPipelineRedesign.vue', 'utf8');
assert.equal(page.includes('下载凭证引用模板（中文）'), true);
assert.equal(page.includes('下载账密模板（英文）'), true);

const originalWindow = globalThis.window;
const originalLocation = globalThis.location;
Object.assign(globalThis, {
	window: { location: { origin: 'http://localhost:3000' } },
	location: { origin: 'http://localhost:3000' },
});

const url = buildDeviceV2IngestExcelTemplateURL('zh', 'credential_ref');
assert.equal(url.includes('header_lang=zh'), true);
assert.equal(url.includes('template_type=credential_ref'), true);
```

- [ ] **Step 2: Run smoke to verify it fails**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOPS-UI && npx esbuild scripts/d2-ingest-template-variants-smoke.ts --bundle --platform=node --format=esm --outfile=.tmp/d2-ingest-template-variants-smoke.mjs >/dev/null && node .tmp/d2-ingest-template-variants-smoke.mjs
```

Expected:

- FAIL because the builder only accepts `headerLang`
- FAIL because the menu text does not exist yet

- [ ] **Step 3: Implement minimal frontend support**

```ts
export type DeviceV2IngestExcelTemplateType = 'full' | 'credential_ref' | 'account_password';

export const buildDeviceV2IngestExcelTemplateURL = (
	headerLang: DeviceV2IngestExcelHeaderLang = 'en',
	templateType: DeviceV2IngestExcelTemplateType = 'full',
): string => {
	// existing token logic
	url.searchParams.set('header_lang', headerLang);
	url.searchParams.set('template_type', templateType);
	return url.toString();
};
```

```vue
<a-menu-item key="full-en" @click="downloadTemplate('en', 'full')">下载全量字段模板（英文）</a-menu-item>
<a-menu-item key="full-zh" @click="downloadTemplate('zh', 'full')">下载全量字段模板（中文）</a-menu-item>
<a-menu-item key="ref-en" @click="downloadTemplate('en', 'credential_ref')">下载凭证引用模板（英文）</a-menu-item>
<a-menu-item key="ref-zh" @click="downloadTemplate('zh', 'credential_ref')">下载凭证引用模板（中文）</a-menu-item>
<a-menu-item key="acct-en" @click="downloadTemplate('en', 'account_password')">下载账密模板（英文）</a-menu-item>
<a-menu-item key="acct-zh" @click="downloadTemplate('zh', 'account_password')">下载账密模板（中文）</a-menu-item>
```

- [ ] **Step 4: Run smoke and typecheck to verify they pass**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOPS-UI && npx esbuild scripts/d2-ingest-template-variants-smoke.ts --bundle --platform=node --format=esm --outfile=.tmp/d2-ingest-template-variants-smoke.mjs >/dev/null && node .tmp/d2-ingest-template-variants-smoke.mjs
cd /home/jacky/project/OneOPS-ALL/OneOPS-UI && npm run typecheck:d2
```

Expected:

- smoke prints `d2 ingest template variants smoke passed`
- `typecheck:d2` exits 0

- [ ] **Step 5: Commit checkpoint**

```bash
git add OneOPS-UI/src/api/device/device-v2-ingest.ts OneOPS-UI/src/views/device/DeviceV2IngestPipelineRedesign.vue OneOPS-UI/scripts/d2-ingest-template-variants-smoke.ts
git commit -m "feat: add ingest template variant download menu"
```

### Task 4: 全链路验证与文档收口

**Files:**
- Modify: `docs/user-manual/device-ingest-collection-monitoring.md`

- [ ] **Step 1: Update user-facing download guidance**

```md
5. 如果从 Excel 导入，点击“下载导入模板”，按实际场景选择：
   - 全量字段模板：一次性补齐更多字段
   - 凭证引用模板：只填写凭证引用，不填写账号密码
   - 账密模板：直接填写账号密码，不填写凭证引用
```

- [ ] **Step 2: Run focused verification**

Run:

```bash
cd /home/jacky/project/OneOPS-ALL/OneOps && go test ./app/device/v2/ingest/api ./app/device/v2/ingest/service/impl -count=1
cd /home/jacky/project/OneOPS-ALL/OneOPS-UI && npm run typecheck:d2
cd /home/jacky/project/OneOPS-ALL/OneOPS-UI && npx esbuild scripts/d2-ingest-template-variants-smoke.ts --bundle --platform=node --format=esm --outfile=.tmp/d2-ingest-template-variants-smoke.mjs >/dev/null && node .tmp/d2-ingest-template-variants-smoke.mjs
```

Expected:

- All commands exit 0

- [ ] **Step 3: Commit final checkpoint**

```bash
git add docs/user-manual/device-ingest-collection-monitoring.md
git commit -m "docs: clarify device ingest template variants"
```
