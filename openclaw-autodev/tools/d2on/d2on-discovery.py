#!/usr/bin/env python3
"""
Device V2 onboarding remote discovery helper.

Development/test only. This script must not be imported or called by business
code. It reads real device candidates from a test database and can run bounded
read-only remote inspection commands against explicitly selected devices.
"""
from __future__ import annotations

import argparse
import copy
import csv
import datetime as dt
import json
import os
import pathlib
import re
import shlex
import ssl
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, Iterable, List, Optional

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
EVIDENCE_ROOT = REPO_ROOT / "docs/openclaw-autodev/evidence/d2on/discovery"
SUMMARY_PATH = REPO_ROOT / "docs/openclaw-autodev/evidence/d2on/D2ON-000.md"
SYSTEM_LOG_PATHS = ["/var/log/syslog", "/var/log/auth.log", "/var/log/messages", "/var/log/secure"]

NETWORK_READ_ONLY_PROBES = [
    {
        "family": "h3c/huawei display",
        "commands": [
            "display version",
            "display current-configuration | include info-center|snmp-agent target-host|trap",
        ],
        "syslog_candidates": ["info-center loghost <listener-ip> port <listener-port>"],
        "snmp_trap_candidates": ["snmp-agent target-host trap address udp-domain <listener-ip> params securityname <community>"],
    },
    {
        "family": "cisco-like show",
        "commands": [
            "show version",
            "show running-config | include logging host|snmp-server host|trap",
        ],
        "syslog_candidates": ["logging host <listener-ip> transport udp port <listener-port>"],
        "snmp_trap_candidates": ["snmp-server host <listener-ip> traps version 2c <community>"],
    },
]

NETLINK_H3C_HELPER = REPO_ROOT / "docs/openclaw-autodev/tools/d2on/netlink-h3c-discovery.go"


def utcnow() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def fail(message: str, code: int = 2) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(code)


def run_local(argv: List[str], timeout: int, env: Optional[Dict[str, str]] = None, summary_limit: int = 2000) -> Dict[str, Any]:
    started = utcnow()
    try:
        proc = subprocess.run(argv, text=True, capture_output=True, timeout=timeout, env=env)
        return {
            "command": shlex.join(argv),
            "started_at": started,
            "finished_at": utcnow(),
            "exit_status": proc.returncode,
            "stdout_summary": summarize(proc.stdout, summary_limit),
            "stderr_summary": summarize(proc.stderr, summary_limit),
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "command": shlex.join(argv),
            "started_at": started,
            "finished_at": utcnow(),
            "exit_status": 124,
            "stdout_summary": summarize(exc.stdout or "", summary_limit),
            "stderr_summary": f"timeout after {timeout}s; {summarize(exc.stderr or '', summary_limit)}",
        }


SECRET_REDACTIONS = [
    # Common CLI/config key-value forms.
    (re.compile(r"(?i)(password\s+)(\S+)"), r"\1<redacted>"),
    (re.compile(r"(?i)(passwd\s+)(\S+)"), r"\1<redacted>"),
    (re.compile(r"(?i)(secret\s+)(\S+)"), r"\1<redacted>"),
    (re.compile(r"(?i)(community\s+(?:read|write)\s+)(\S+)"), r"\1<redacted>"),
    (re.compile(r"(?i)(read\s+community\s+)(\S+)"), r"\1<redacted>"),
    (re.compile(r"(?i)(write\s+community\s+)(\S+)"), r"\1<redacted>"),
    (re.compile(r"(?i)(community\s+)(\S+)"), r"\1<redacted>"),
    (re.compile(r"(?i)(securityname\s+)(\S+)"), r"\1<redacted>"),
    # SSH diagnostics can echo the runtime username; evidence only records whether one was provided.
    (re.compile(r"(?i)([A-Za-z0-9._-]+)@((?:\d{1,3}\.){3}\d{1,3})"), r"<user>@\2"),
    # JSON/YAML-ish forms that may appear in inventory or debug errors.
    (re.compile(r"(?i)([\"']?(?:password|passwd|secret|token|community)[\"']?\s*[:=]\s*)[\"']?[^\"'\s,}]+"), r"\1<redacted>"),
]


def redact_secrets(text: str) -> str:
    redacted = text or ""
    for pattern, replacement in SECRET_REDACTIONS:
        redacted = pattern.sub(replacement, redacted)
    return redacted


def summarize(text: str, limit: int = 2000) -> str:
    text = redact_secrets(text or "")
    clean = "\n".join(line.rstrip() for line in text.splitlines())
    if len(clean) <= limit:
        return clean
    return clean[:limit] + f"\n... <truncated {len(clean) - limit} chars>"


def evidence_path(kind: str, target: str) -> pathlib.Path:
    safe = "".join(ch if ch.isalnum() or ch in ".-_" else "_" for ch in target)
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    return EVIDENCE_ROOT / kind / f"{stamp}-{safe}.json"


def write_json(path: pathlib.Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_leading_json_object(text: str) -> Dict[str, Any]:
    stripped = text.lstrip()
    if not stripped:
        return {}
    try:
        value, _ = json.JSONDecoder().raw_decode(stripped)
    except json.JSONDecodeError:
        return {}
    if not isinstance(value, dict):
        return {}
    return value


def append_summary(entry: Dict[str, Any], evidence_file: pathlib.Path) -> None:
    SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not SUMMARY_PATH.exists():
        SUMMARY_PATH.write_text(
            "# D2ON-000 Remote discovery helper tools\n\n"
            "This summary intentionally keeps durable discovery context compact. "
            "Credentials, tokens, and secret values are never recorded here.\n\n"
            "## Runs\n\n",
            encoding="utf-8",
        )
    status = entry.get("status", "unknown")
    target = entry.get("target", {})
    target_text = target.get("host") or entry.get("query", "unknown")
    rel = evidence_file.relative_to(REPO_ROOT)
    lines = [
        f"- `{entry.get('created_at', utcnow())}` `{entry.get('kind')}` target `{target_text}` status `{status}` evidence `{rel}`",
    ]
    if entry.get("summary"):
        lines.append(f"  - {entry['summary']}")
    SUMMARY_PATH.write_text(SUMMARY_PATH.read_text(encoding="utf-8") + "\n".join(lines) + "\n", encoding="utf-8")


def env_truthy(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in {"1", "true", "yes", "on"}


def deep_redact(value: Any) -> Any:
    if isinstance(value, str):
        return summarize(value, limit=20000)
    if isinstance(value, list):
        return [deep_redact(item) for item in value]
    if isinstance(value, dict):
        redacted: Dict[str, Any] = {}
        for key, item in value.items():
            normalized = key.strip().lower()
            if normalized in {"password", "private_key", "auth_password", "token", "authorization"}:
                redacted[key] = "<redacted>" if item else ""
                continue
            redacted[key] = deep_redact(item)
        return redacted
    return value


def resolve_username(cli_value: Optional[str], env_name: str, purpose: str) -> str:
    value = (cli_value or os.getenv(env_name, "")).strip()
    if not value:
        fail(f"{purpose} requires --user or environment variable {env_name}")
    return value


def controller_runtime(args: argparse.Namespace) -> Dict[str, Any]:
    controller_url = (getattr(args, "controller_url", None) or os.getenv("D2ON_CONTROLLER_URL", "")).strip().rstrip("/")
    if not controller_url:
        fail("missing controller URL; set --controller-url or D2ON_CONTROLLER_URL")
    auth_token_env = getattr(args, "auth_token_env", "D2ON_X_AUTH_TOKEN")
    token = os.getenv(auth_token_env, "").strip()
    insecure_skip_verify = env_truthy("D2ON_CONTROLLER_INSECURE_SKIP_VERIFY")
    if getattr(args, "insecure_skip_verify", False):
        insecure_skip_verify = True
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    if token:
        headers["X-Auth-Token"] = token
    return {
        "base_url": controller_url,
        "path": "/api/v1/remote/run",
        "headers": headers,
        "auth_token_env": auth_token_env,
        "auth_token_provided": bool(token),
        "insecure_skip_verify": insecure_skip_verify,
    }


def post_json(url: str, payload: Dict[str, Any], timeout: int, headers: Dict[str, str], insecure_skip_verify: bool) -> Dict[str, Any]:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(url, data=body, headers=headers, method="POST")
    context = None
    if urllib.parse.urlparse(url).scheme == "https" and insecure_skip_verify:
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
    started = utcnow()
    try:
        with urllib.request.urlopen(request, timeout=timeout, context=context) as response:
            raw_body = response.read().decode("utf-8", errors="replace")
            status_code = response.getcode()
    except urllib.error.HTTPError as exc:
        raw_body = exc.read().decode("utf-8", errors="replace")
        status_code = exc.code
    except urllib.error.URLError as exc:
        return {
            "started_at": started,
            "finished_at": utcnow(),
            "status_code": 0,
            "transport_error": summarize(str(exc.reason), 4000),
            "body_summary": "",
            "body_json": {},
        }
    body_json: Dict[str, Any] = {}
    try:
        loaded = json.loads(raw_body) if raw_body.strip() else {}
        if isinstance(loaded, dict):
            body_json = loaded
    except json.JSONDecodeError:
        body_json = {}
    return {
        "started_at": started,
        "finished_at": utcnow(),
        "status_code": status_code,
        "transport_error": "",
        "body_summary": summarize(raw_body, 12000),
        "body_json": body_json,
    }


def controller_remote_run(args: argparse.Namespace, payload: Dict[str, Any], timeout: int) -> Dict[str, Any]:
    runtime = controller_runtime(args)
    url = runtime["base_url"] + runtime["path"]
    response = post_json(url, payload, timeout, runtime["headers"], runtime["insecure_skip_verify"])
    return {
        "controller": {
            "base_url": runtime["base_url"],
            "path": runtime["path"],
            "auth_token_env": runtime["auth_token_env"],
            "auth_token_provided": runtime["auth_token_provided"],
            "insecure_skip_verify": runtime["insecure_skip_verify"],
        },
        "request": deep_redact(copy.deepcopy(payload)),
        "response": deep_redact(response),
    }


def collect_existing_missing_from_results(results: Iterable[Dict[str, Any]]) -> tuple[List[str], List[str]]:
    existing: List[str] = []
    missing: List[str] = []
    for result in results:
        stdout = result.get("stdout", "") or ""
        for line in stdout.splitlines():
            if line.startswith("exists:"):
                existing.append(line.removeprefix("exists:"))
            if line.startswith("missing:"):
                missing.append(line.removeprefix("missing:"))
    return existing, missing


def network_probe_family(vendor: str, platform: str) -> Dict[str, Any]:
    vendor_norm = vendor.strip().lower()
    platform_norm = platform.strip().lower()
    if vendor_norm == "h3c" and platform_norm == "comware":
        return {
            "family": "h3c/comware controller remote api",
            "commands": [
                "display version",
                "display current-configuration | include info-center|snmp-agent target-host|trap",
            ],
            "syslog_candidates": ["info-center loghost <listener-ip> port <listener-port>"],
            "snmp_trap_candidates": ["snmp-agent target-host trap address udp-domain <listener-ip> params securityname <community>"],
        }
    if vendor_norm == "huawei" and platform_norm == "vrp":
        return {
            "family": "huawei/vrp controller remote api",
            "commands": [
                "display version",
                "display current-configuration | include info-center|snmp-agent target-host|trap",
            ],
            "syslog_candidates": ["info-center loghost <listener-ip> port <listener-port>"],
            "snmp_trap_candidates": ["snmp-agent target-host trap address udp-domain <listener-ip> params securityname <community>"],
        }
    if vendor_norm == "cisco" and platform_norm in {"ios", "iosxe", "nxos"}:
        return {
            "family": "cisco-like controller remote api",
            "commands": [
                "show version",
                "show running-config | include logging host|snmp-server host|trap",
            ],
            "syslog_candidates": ["logging host <listener-ip> transport udp port <listener-port>"],
            "snmp_trap_candidates": ["snmp-server host <listener-ip> traps version 2c <community>"],
        }
    fail(f"unsupported vendor/platform for controller-backed network discovery: {vendor}/{platform}")
    return {}


def collect_vendor_platform_clues(results: Iterable[Dict[str, Any]]) -> List[str]:
    clues: List[str] = []
    seen = set()
    markers = ("h3c", "comware", "huawei", "vrp", "cisco", "ios", "nx-os")
    for result in results:
        stdout = result.get("stdout", "") or ""
        for line in stdout.splitlines():
            stripped = line.strip()
            lowered = stripped.lower()
            if stripped and any(marker in lowered for marker in markers):
                redacted = summarize(stripped, 400)
                if redacted not in seen:
                    seen.add(redacted)
                    clues.append(redacted)
            if len(clues) >= 10:
                return clues
    return clues


def mysql_base_args() -> tuple[List[str], Dict[str, str]]:
    host = os.getenv("D2ON_MYSQL_HOST")
    database = os.getenv("D2ON_MYSQL_DATABASE")
    user = os.getenv("D2ON_MYSQL_USER")
    password = os.getenv("D2ON_MYSQL_PASSWORD")
    port = os.getenv("D2ON_MYSQL_PORT", "3306")
    missing = [name for name, value in {
        "D2ON_MYSQL_HOST": host,
        "D2ON_MYSQL_DATABASE": database,
        "D2ON_MYSQL_USER": user,
        "D2ON_MYSQL_PASSWORD": password,
    }.items() if not value]
    if missing:
        fail("missing database environment variables: " + ", ".join(missing))
    env = os.environ.copy()
    env["MYSQL_PWD"] = password or ""
    return [
        "mysql",
        f"--host={host}",
        f"--port={port}",
        f"--user={user}",
        "--database", database or "",
        "--batch",
        "--raw",
        "--skip-column-names",
    ], env


def query_candidates(targets: List[str], limit: int, timeout: int) -> pathlib.Path:
    clauses = []
    for target in targets:
        esc = target.replace("'", "''")
        clauses.append(f"attributes_json LIKE '%{esc}%' OR metadata_json LIKE '%{esc}%' OR code = '{esc}' OR name = '{esc}'")
    where = " OR ".join(f"({c})" for c in clauses) if clauses else "1=1"
    sql = (
        "SELECT code,name,platform_code,status "
        f"FROM platform_devices_v2 WHERE {where} ORDER BY updated_at DESC LIMIT {int(limit)}"
    )
    mysql_args, mysql_env = mysql_base_args()
    result = run_local(mysql_args + ["--execute", sql], timeout, env=mysql_env)
    rows = []
    if result["exit_status"] == 0 and result["stdout_summary"].strip():
        reader = csv.reader(result["stdout_summary"].splitlines(), dialect="excel-tab")
        for row in reader:
            # Candidate evidence intentionally records only stable identifiers.
            # attributes_json/metadata_json are queried for target matching but
            # not persisted because real inventory blobs may contain secrets,
            # SNMP communities, tokens, or credentials.
            rows.append({
                "code": row[0] if len(row) > 0 else "",
                "name": row[1] if len(row) > 1 else "",
                "platform_code": row[2] if len(row) > 2 else "",
                "status": row[3] if len(row) > 3 else "",
                "attributes_json_recorded": False,
                "metadata_json_recorded": False,
            })
    payload = {
        "kind": "db-candidates",
        "created_at": utcnow(),
        "query": "platform_devices_v2 candidate lookup",
        "targets": targets,
        "status": "success" if result["exit_status"] == 0 and rows else "failed",
        "summary": f"{len(rows)} candidate row(s) returned" if rows else "database query failed or returned no candidates",
        "database": {
            "host": os.getenv("D2ON_MYSQL_HOST"),
            "port": os.getenv("D2ON_MYSQL_PORT", "3306"),
            "database": os.getenv("D2ON_MYSQL_DATABASE"),
            "user": os.getenv("D2ON_MYSQL_USER"),
            "password_recorded": False,
        },
        "command_result": {k: v for k, v in result.items() if k not in {"command", "stdout_summary"}} | {
            "command": "mysql <redacted-password> --execute <candidate-query>",
            "stdout_summary": "<omitted: raw database output may contain inventory metadata>",
        },
        "rows": rows,
    }
    path = evidence_path("db", "candidates")
    write_json(path, payload)
    append_summary(payload, path)
    if payload["status"] != "success":
        fail(f"database candidate lookup failed; evidence={path}", 3)
    print(path)
    return path


def expect_ssh_command(host: str, command: str, user: str, port: int, timeout: int, password_env: str) -> Dict[str, Any]:
    if not user:
        fail("password SSH mode requires --user")
    if not os.getenv(password_env):
        fail(f"missing SSH password environment variable: {password_env}")
    expect_script = r'''
set timeout $env(D2ON_EXPECT_TIMEOUT)
set password $env(D2ON_EXPECT_PASSWORD)
set command $env(D2ON_EXPECT_REMOTE_COMMAND)
set host $env(D2ON_EXPECT_HOST)
set port $env(D2ON_EXPECT_PORT)
set user $env(D2ON_EXPECT_USER)
spawn ssh -p $port -o StrictHostKeyChecking=accept-new -o PreferredAuthentications=password -o PubkeyAuthentication=no -- "$user@$host" "$command"
expect {
  -re "(?i)password:" {
    send -- "$password\r"
    exp_continue
  }
  eof
}
catch wait result
exit [lindex $result 3]
'''
    env = os.environ.copy()
    env.update({
        "D2ON_EXPECT_TIMEOUT": str(timeout),
        "D2ON_EXPECT_PASSWORD": os.getenv(password_env, ""),
        "D2ON_EXPECT_REMOTE_COMMAND": command,
        "D2ON_EXPECT_HOST": host,
        "D2ON_EXPECT_PORT": str(port),
        "D2ON_EXPECT_USER": user,
    })
    result = run_local(["expect", "-c", expect_script], timeout + 5, env=env)
    result["target"] = {"host": host, "port": port, "user_provided": True, "auth_method": "password-env"}
    result["remote_command"] = command
    result["command"] = f"expect ssh -p {port} <target> {shlex.quote(command)}"
    return result


def ssh_command(host: str, command: str, user: Optional[str], port: int, timeout: int, password_env: Optional[str] = None) -> Dict[str, Any]:
    if password_env:
        return expect_ssh_command(host, command, user or "", port, timeout, password_env)
    target = f"{user}@{host}" if user else host
    argv = [
        "ssh",
        "-p", str(port),
        "-o", "BatchMode=yes",
        "-o", "StrictHostKeyChecking=accept-new",
        "-o", f"ConnectTimeout={min(timeout, 15)}",
        target,
        command,
    ]
    result = run_local(argv, timeout)
    result["target"] = {"host": host, "port": port, "user_provided": bool(user)}
    result["remote_command"] = command
    # Do not record the full ssh target username in evidence command.
    result["command"] = f"ssh -p {port} <target> {shlex.quote(command)}"
    return result


def inspect_server(args: argparse.Namespace) -> pathlib.Path:
    checks = " ; ".join([f"if [ -e {shlex.quote(p)} ]; then echo exists:{p}; else echo missing:{p}; fi" for p in SYSTEM_LOG_PATHS])
    commands = [
        "uname -a",
        "id -un",
        checks,
        "command -v rsyslogd || command -v syslog-ng || true",
    ]
    results = [ssh_command(args.host, cmd, args.user, args.port, args.timeout, args.password_env) for cmd in commands]
    existing = []
    missing = []
    for result in results:
        for line in result.get("stdout_summary", "").splitlines():
            if line.startswith("exists:"):
                existing.append(line.removeprefix("exists:"))
            if line.startswith("missing:"):
                missing.append(line.removeprefix("missing:"))
    failed = [r for r in results if r["exit_status"] != 0]
    payload = {
        "kind": "server-inspection",
        "created_at": utcnow(),
        "target": {"host": args.host, "port": args.port, "user_provided": bool(args.user)},
        "status": "failed" if failed else "success",
        "summary": f"system logs existing={existing}; missing={missing}" if not failed else "one or more read-only server commands failed",
        "system_log_strategy": {"mode": "first_existing", "configured_paths": SYSTEM_LOG_PATHS, "existing_paths": existing, "missing_paths": missing},
        "server_log_forwarding_clues": "rsyslogd/syslog-ng command lookup is read-only; configuration commands are out of scope for D2ON-000",
        "commands": results,
    }
    path = evidence_path("server", args.host)
    write_json(path, payload)
    append_summary(payload, path)
    if failed:
        fail(f"server remote inspection failed; evidence={path}", 4)
    print(path)
    return path


def inspect_server_via_controller(args: argparse.Namespace) -> pathlib.Path:
    user = resolve_username(args.user, "D2ON_SERVER_SSH_USER", "controller-backed server discovery")
    if not os.getenv(args.password_env):
        fail(f"missing controller-backed server password environment variable: {args.password_env}")
    checks = " ; ".join([f"if [ -e {shlex.quote(p)} ]; then echo exists:{p}; else echo missing:{p}; fi" for p in SYSTEM_LOG_PATHS])
    commands = [
        "uname -a",
        "id -un",
        checks,
        "command -v rsyslogd || command -v syslog-ng || true",
    ]
    controller_result = controller_remote_run(
        args,
        {
            "target": {
                "type": "server",
                "host": args.host,
                "port": args.port,
            },
            "auth": {
                "username": user,
                "password": os.getenv(args.password_env, ""),
            },
            "commands": commands,
            "login_timeout_sec": args.timeout,
            "command_timeout_sec": args.timeout,
        },
        timeout=max(args.timeout + 10, 20),
    )
    response = controller_result["response"]
    body_json = response.get("body_json", {}) or {}
    results = body_json.get("results", []) or []
    meta = body_json.get("meta", {}) or {}
    existing, missing = collect_existing_missing_from_results(results)
    failed_commands = [result for result in results if not result.get("success", False)]
    transport_error = response.get("transport_error", "")
    failed = bool(transport_error) or response.get("status_code") != 200 or not meta.get("success", False) or bool(failed_commands)
    payload = {
        "kind": "server-inspection-via-controller",
        "created_at": utcnow(),
        "target": {
            "host": args.host,
            "port": args.port,
            "user_provided": True,
        },
        "status": "failed" if failed else "success",
        "summary": (
            f"system logs existing={existing}; missing={missing}"
            if not failed else
            (meta.get("message") or transport_error or "controller-backed read-only server discovery failed")
        ),
        "access_path": "controller_remote_api",
        "system_log_strategy": {
            "mode": "first_existing",
            "configured_paths": SYSTEM_LOG_PATHS,
            "existing_paths": existing,
            "missing_paths": missing,
        },
        "server_log_forwarding_clues": "controller /api/v1/remote/run is used only for read-only verification; configuration commands remain out of scope for D2ON-000",
        "controller_run": controller_result,
        "commands": results,
    }
    path = evidence_path("server", f"{args.host}-controller")
    write_json(path, payload)
    append_summary(payload, path)
    if failed:
        fail(f"controller-backed server remote inspection failed; evidence={path}", 4)
    print(path)
    return path


def inspect_network(args: argparse.Namespace) -> pathlib.Path:
    if args.vendor.lower() != "h3c":
        fail("D2ON-000 network discovery currently requires --vendor h3c; do not infer vendor")
    if not args.user:
        fail("netlink H3C discovery requires --user")
    if not os.getenv(args.password_env):
        fail(f"missing network-device password environment variable: {args.password_env}")
    helper_cmd = (
        f"cd {shlex.quote(str(REPO_ROOT / 'netlink'))} && "
        f"GOSUMDB=off go run -mod=mod {shlex.quote(str(NETLINK_H3C_HELPER))} "
        f"--host {shlex.quote(args.host)} "
        f"--port {int(args.port)} "
        f"--user {shlex.quote(args.user)} "
        f"--password-env {shlex.quote(args.password_env)} "
        f"--timeout {int(args.timeout)}"
    )
    helper_result = run_local(["bash", "-lc", helper_cmd], args.timeout + 60, env=os.environ.copy(), summary_limit=20000)
    helper_payload = parse_leading_json_object(helper_result.get("stdout_summary") or "")
    status = helper_payload.get("status") if helper_result["exit_status"] == 0 else "failed"
    payload = {
        "kind": "network-inspection",
        "created_at": utcnow(),
        "target": {
            "host": args.host,
            "port": args.port,
            "user_provided": bool(args.user),
            "vendor": "H3C",
            "library": "netlink/netdevice",
            "mode": "Compare",
        },
        "status": status,
        "summary": helper_payload.get("summary") or "netlink H3C discovery failed",
        "vendor_platform_clues": helper_payload.get("vendor_platform_clues") or [],
        "candidate_command_families": [
            {
                "family": "h3c/comware netlink",
                "mode": "Compare",
                "syslog_candidates": ["info-center loghost <listener-ip> port <listener-port>"],
                "snmp_trap_candidates": ["snmp-agent target-host trap address udp-domain <listener-ip> params securityname <community>"],
            }
        ],
        "configuration_applied": False,
        "commands": helper_payload.get("commands") or [],
        "helper_result": {k: v for k, v in helper_result.items() if k != "command"} | {"command": "cd netlink && go run <netlink-h3c-discovery.go> <redacted-password-env>"},
    }
    path = evidence_path("network", args.host)
    write_json(path, payload)
    append_summary(payload, path)
    if status != "success":
        fail(f"network device unsupported, login failed, or command templates ambiguous; evidence={path}", 5)
    print(path)
    return path


def inspect_network_via_controller(args: argparse.Namespace) -> pathlib.Path:
    user = resolve_username(args.user, "D2ON_NETWORK_SSH_USER", "controller-backed network discovery")
    if not os.getenv(args.password_env):
        fail(f"missing controller-backed network password environment variable: {args.password_env}")
    probe_family = network_probe_family(args.vendor, args.platform)
    auth: Dict[str, Any] = {
        "username": user,
        "password": os.getenv(args.password_env, ""),
    }
    auth_password = os.getenv(args.auth_password_env, "")
    if auth_password:
        auth["auth_password"] = auth_password
    controller_result = controller_remote_run(
        args,
        {
            "target": {
                "type": "network_device",
                "host": args.host,
                "port": args.port,
                "protocol": args.protocol,
            },
            "auth": auth,
            "profile": {
                "vendor": args.vendor,
                "platform": args.platform,
            },
            "commands": probe_family["commands"],
            "login_timeout_sec": args.timeout,
            "command_timeout_sec": args.timeout,
            "no_output_timeout_sec": min(args.timeout, 10),
        },
        timeout=max(args.timeout + 10, 20),
    )
    response = controller_result["response"]
    body_json = response.get("body_json", {}) or {}
    results = body_json.get("results", []) or []
    meta = body_json.get("meta", {}) or {}
    failed_commands = [result for result in results if not result.get("success", False)]
    transport_error = response.get("transport_error", "")
    failed = bool(transport_error) or response.get("status_code") != 200 or not meta.get("success", False) or bool(failed_commands)
    payload = {
        "kind": "network-inspection-via-controller",
        "created_at": utcnow(),
        "target": {
            "host": args.host,
            "port": args.port,
            "protocol": args.protocol,
            "user_provided": True,
            "vendor": args.vendor,
            "platform": args.platform,
            "library": "ctrlhub/controller /api/v1/remote/run",
        },
        "status": "failed" if failed else "success",
        "summary": meta.get("message") if meta.get("message") else "controller-backed network discovery completed",
        "access_path": "controller_remote_api",
        "vendor_platform_clues": collect_vendor_platform_clues(results),
        "candidate_command_families": [
            {
                "family": probe_family["family"],
                "mode": "controller-remote-run",
                "syslog_candidates": probe_family["syslog_candidates"],
                "snmp_trap_candidates": probe_family["snmp_trap_candidates"],
            }
        ],
        "configuration_applied": False,
        "controller_run": controller_result,
        "commands": results,
    }
    path = evidence_path("network", f"{args.host}-controller")
    write_json(path, payload)
    append_summary(payload, path)
    if failed:
        fail(f"controller-backed network inspection failed; evidence={path}", 5)
    print(path)
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description="D2ON development/test remote discovery helper")
    sub = parser.add_subparsers(dest="command", required=True)

    db = sub.add_parser("db-candidates", help="Query platform_devices_v2 candidates from a real MySQL database")
    db.add_argument("--target", action="append", default=[], help="Device code/name/IP to search. Repeatable.")
    db.add_argument("--limit", type=int, default=20)
    db.add_argument("--timeout", type=int, default=20)

    srv = sub.add_parser("inspect-server", help="Run read-only Linux server discovery over SSH")
    srv.add_argument("--host", required=True)
    srv.add_argument("--user", help="SSH username; omit to use local ssh default")
    srv.add_argument("--port", type=int, default=22)
    srv.add_argument("--timeout", type=int, default=20)
    srv.add_argument("--password-env", help="Environment variable containing SSH password; enables expect-based password SSH")

    srvc = sub.add_parser("inspect-server-via-controller", help="Run read-only Linux server discovery through controller /api/v1/remote/run")
    srvc.add_argument("--host", required=True)
    srvc.add_argument("--user", help="SSH username; falls back to D2ON_SERVER_SSH_USER")
    srvc.add_argument("--port", type=int, default=22)
    srvc.add_argument("--timeout", type=int, default=20)
    srvc.add_argument("--password-env", default="D2ON_SERVER_SSH_PASSWORD", help="Environment variable containing the remote SSH password")
    srvc.add_argument("--controller-url", help="Controller base URL; falls back to D2ON_CONTROLLER_URL")
    srvc.add_argument("--auth-token-env", default="D2ON_X_AUTH_TOKEN", help="Environment variable containing controller X-Auth-Token")
    srvc.add_argument("--insecure-skip-verify", action="store_true", help="Skip TLS verification for HTTPS controller URLs")

    net = sub.add_parser("inspect-network", help="Run read-only network-device command-family discovery over SSH")
    net.add_argument("--host", required=True)
    net.add_argument("--user", help="SSH username; omit to use local ssh default")
    net.add_argument("--port", type=int, default=22)
    net.add_argument("--timeout", type=int, default=20)
    net.add_argument("--vendor", default="h3c")
    net.add_argument("--password-env", default="D2ON_NETWORK_SSH_PASSWORD")

    netc = sub.add_parser("inspect-network-via-controller", help="Run read-only network-device discovery through controller /api/v1/remote/run")
    netc.add_argument("--host", required=True)
    netc.add_argument("--user", help="SSH username; falls back to D2ON_NETWORK_SSH_USER")
    netc.add_argument("--port", type=int, default=22)
    netc.add_argument("--timeout", type=int, default=20)
    netc.add_argument("--vendor", default="h3c")
    netc.add_argument("--platform", default="comware")
    netc.add_argument("--protocol", default="ssh", choices=["ssh", "telnet"])
    netc.add_argument("--password-env", default="D2ON_NETWORK_SSH_PASSWORD", help="Environment variable containing the remote login password")
    netc.add_argument("--auth-password-env", default="D2ON_NETWORK_AUTH_PASSWORD", help="Optional environment variable for enable/auth password")
    netc.add_argument("--controller-url", help="Controller base URL; falls back to D2ON_CONTROLLER_URL")
    netc.add_argument("--auth-token-env", default="D2ON_X_AUTH_TOKEN", help="Environment variable containing controller X-Auth-Token")
    netc.add_argument("--insecure-skip-verify", action="store_true", help="Skip TLS verification for HTTPS controller URLs")

    args = parser.parse_args()
    if args.command == "db-candidates":
        query_candidates(args.target, args.limit, args.timeout)
    elif args.command == "inspect-server":
        inspect_server(args)
    elif args.command == "inspect-server-via-controller":
        inspect_server_via_controller(args)
    elif args.command == "inspect-network":
        inspect_network(args)
    elif args.command == "inspect-network-via-controller":
        inspect_network_via_controller(args)
    else:
        fail("unknown command")


if __name__ == "__main__":
    main()
