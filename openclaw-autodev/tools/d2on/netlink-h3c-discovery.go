package main

import (
	"context"
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"regexp"
	"strings"
	"time"

	"github.com/netxops/netlink/dispatch"
	"github.com/netxops/netlink/mode"
	"github.com/netxops/netlink/netdevice"
	"go.uber.org/zap"
)

const h3cReadOnlyModeConfig = `
prompts:
  - "[\\r\\n]?[^\\n]+(]|#|>)[ ]?$"
err_prompts:
  - "(?i)error:"
  - "(?i)does not exist"
  - "(?i)unrecognized"
  - "(?i)incomplete"
  - "command not found"
  - "No such file or directory"
ignore_prompts:
  - "\\[SubSlot \\d+\\]"
pager_prompts:
  - "^\\s*---- More ----\\s*$"
  - "^\\s*\\-{4}\\s*More\\s*\\-{4}\\s*$"
pager_command: " "
init_commands:
  - "screen-length 0 temporary"
  - "screen-length disable"
save_commands: []
first_chain:
  - "display current-configuration"
last_chain:
  - "display current-configuration"
auth_cmd: ""
`

const hubConfig = `
dispatches:
  - name: SSHShellError
    regex:
      - "ssh: handshake failed"
      - "ssh: unable to authenticate"
    action: ssh_shell_error
  - name: TelnetShellError
    regex:
      - "telnet: connection refused"
      - "telnet: unable to connect"
    action: telnet_shell_error
  - name: SendPassword
    regex:
      - "(?i)password:"
      - "(?i)enter password:"
    action: send_password
  - name: UnknownHost
    regex:
      - "(?i)are you sure you want to continue connecting"
      - "(?i)the authenticity of host .* can't be established"
    action: unknown_host
  - name: SendUsername
    regex:
      - "(?i)login:"
      - "(?i)username:"
    action: send_username
  - name: InitCompleted
    regex:
      - "^(<|\\[)[\\S ]+(?:>|\\])$"
      - ".*<[^>]+>\\s*$"
      - ".*\\[[^\\]]+\\]\\s*$"
      - "\\$ $"
    action: init_completed
  - name: Authorize
    regex:
      - "(?i)enter configuration mode"
      - "(?i)enable password:"
    action: authorize
`

type commandResult struct {
	Command       string `json:"remote_command"`
	ExitStatus    int    `json:"exit_status"`
	StdoutSummary string `json:"stdout_summary"`
	StderrSummary string `json:"stderr_summary"`
}

type payload struct {
	Kind                 string          `json:"kind"`
	Mode                 string          `json:"mode"`
	Target               map[string]any  `json:"target"`
	Status               string          `json:"status"`
	Summary              string          `json:"summary"`
	VendorPlatformClues  []string        `json:"vendor_platform_clues"`
	ConfigurationApplied bool            `json:"configuration_applied"`
	Commands             []commandResult `json:"commands"`
}

var redactions = []*regexp.Regexp{
	regexp.MustCompile(`(?i)(password\s+)(\S+)`),
	regexp.MustCompile(`(?i)(community\s+(?:read|write)\s+)(\S+)`),
	regexp.MustCompile(`(?i)(community\s+)(\S+)`),
	regexp.MustCompile(`(?i)(securityname\s+)(\S+)`),
	regexp.MustCompile(`(?i)(secret\s+)(\S+)`),
}

func summarize(text string) string {
	text = strings.TrimSpace(text)
	for _, re := range redactions {
		text = re.ReplaceAllString(text, `${1}<redacted>`)
	}
	if len(text) > 2000 {
		return text[:2000] + fmt.Sprintf("\n... <truncated %d chars>", len(text)-2000)
	}
	return text
}

func main() {
	host := flag.String("host", "", "target host")
	user := flag.String("user", "", "username")
	port := flag.Int("port", 22, "ssh port")
	passwordEnv := flag.String("password-env", "D2ON_NETWORK_SSH_PASSWORD", "environment variable containing password")
	timeout := flag.Int("timeout", 30, "timeout seconds")
	flag.Parse()

	if *host == "" || *user == "" {
		fmt.Fprintln(os.Stderr, "host and user are required")
		os.Exit(2)
	}
	password := os.Getenv(*passwordEnv)
	if password == "" {
		fmt.Fprintf(os.Stderr, "missing password environment variable: %s\n", *passwordEnv)
		os.Exit(2)
	}

	logger := zap.NewNop()
	modeCfg, err := mode.NewModeFromYAML(h3cReadOnlyModeConfig)
	if err != nil {
		fmt.Fprintf(os.Stderr, "parse mode config: %v\n", err)
		os.Exit(2)
	}
	hubCfg, err := dispatch.LoadConfig(hubConfig)
	if err != nil {
		fmt.Fprintf(os.Stderr, "parse hub config: %v\n", err)
		os.Exit(2)
	}
	base := dispatch.BaseInfo{
		Host:            *host,
		Port:            *port,
		Username:        *user,
		Password:        password,
		AuthPass:        password,
		Telnet:          false,
		DailTimeout:     10,
		DispatchTimeOut: 30,
	}
	device, err := netdevice.NewBaseNetworkDevice(&base, modeCfg, hubCfg, logger)
	if err != nil {
		fmt.Fprintf(os.Stderr, "create device: %v\n", err)
		os.Exit(2)
	}
	defer device.Close()

	ctx, cancel := device.BuildLoginCtx(15, *timeout+30)
	defer cancel()
	if err := device.LoginAndInit(ctx); err != nil {
		fmt.Fprintf(os.Stderr, "login/init failed: %v\n", err)
		os.Exit(3)
	}

	commands := []string{
		"display version",
		"display current-configuration | include info-center",
		"display current-configuration | include snmp-agent",
		"display current-configuration | include trap",
	}
	results := make([]commandResult, 0, len(commands))
	successes := 0
	for _, command := range commands {
		cmdCtx, cmdCancel := context.WithTimeout(context.Background(), time.Duration(*timeout)*time.Second)
		output, err := device.ExecuteCommand(cmdCtx, command)
		cmdCancel()
		item := commandResult{Command: command, StdoutSummary: summarize(output)}
		if err != nil {
			item.ExitStatus = 1
			item.StderrSummary = summarize(err.Error())
		} else {
			successes += 1
		}
		results = append(results, item)
	}

	status := "success"
	summary := "H3C/Comware read-only netlink discovery succeeded"
	if successes == 0 {
		status = "failed"
		summary = "all H3C/Comware read-only netlink commands failed"
	}
	out := payload{
		Kind: "network-inspection",
		Mode: "Compare",
		Target: map[string]any{
			"host":          *host,
			"port":          *port,
			"user_provided": true,
			"vendor":        "H3C",
			"library":       "netlink/netdevice",
		},
		Status:               status,
		Summary:              summary,
		VendorPlatformClues:  []string{"h3c/comware"},
		ConfigurationApplied: false,
		Commands:             results,
	}
	encoded, err := json.MarshalIndent(out, "", "  ")
	if err != nil {
		fmt.Fprintf(os.Stderr, "encode result: %v\n", err)
		os.Exit(2)
	}
	fmt.Println(string(encoded))
	if status != "success" {
		os.Exit(5)
	}
}
