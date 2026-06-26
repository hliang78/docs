# Platform Coverage Matrix

This matrix captures the agreed baseline dimensions for the first shared platform testing pass. It is intentionally small and opinionated so later gate work can attach concrete checks without redefining the axes.

| Domain | Chain | Entry | Protocol | State | Truth Layer | Gate Level | Current Coverage | Owner |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Network | ingest -> collect -> monitor | ZB | SNMP | success | source + projection + runtime | PR core candidate | existing device-v2 harness | network owner |
| Server | ingest -> collect -> monitor | page store/start | SSH/IPMI | blocked | source + detail + runtime | nightly | gap | server owner |
| Firewall | import -> collect -> config facts | page import | SSH/API | success | source + detail | nightly | existing smoke/docs | firewall owner |

## Notes

- `Truth Layer` distinguishes whether the current checks only prove source records, include user-facing detail views, or also validate runtime outcomes.
- `Gate Level` is the intended execution tier, not a promise that the gate already exists in CI today.
- `Current Coverage` points at the strongest asset we already have at HEAD, even when that asset is partial or documentation-led.
