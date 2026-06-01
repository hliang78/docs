# D2ON Test Targets

These devices are authorized by the user for Device V2 onboarding helper-tool
testing and discovery.

This authorization is only for development/testing tools. It does not authorize
business code to bypass controller-provided APIs for remote server operations.

| Role | Address | Purpose |
| --- | --- | --- |
| Server | `192.168.100.7` | Explore Linux system-log files and server log-forwarding commands. |
| Network device | `172.32.2.14` | Explore syslog and SNMP trap command families. |

Rules:

- Do not store credentials in this file.
- Discovery may run read-only remote inspection commands.
- Business remote-server operations must go through controller-provided APIs.
- Configuration-changing commands require an explicit ensure/apply story.
- Fail loudly on login, privilege, command, vendor, or template errors.
