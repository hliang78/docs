# Platform Coverage Matrix

This matrix captures the agreed baseline dimensions for the first shared platform testing pass. It is intentionally small and opinionated so later gate work can attach concrete checks without redefining the axes.

| Domain | Chain | Entry | Protocol | State | Truth Layer | Gate Level | Current Coverage | Owner |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Network | ingest -> collect -> monitor | ZB | SNMP | success | source + projection + runtime | PR core | backend + frontend repo core gates landed | network owner |
| Server | ingest -> collect -> monitor | page store/start | SSH/IPMI | blocked | source + detail + runtime | nightly / docs partial | nightly-led, no PR core gate | server owner |
| Firewall | import -> collect -> config facts | page import | SSH/API | success | source + detail | nightly / docs partial | smoke/docs led, no PR core gate | firewall owner |

## Notes

- `Truth Layer` distinguishes whether the current checks only prove source records, include user-facing detail views, or also validate runtime outcomes.
- `Gate Level` is the strongest currently landed execution tier for the row, not a promise that every repo runs the same depth in PR.
- `Current Coverage` points at the strongest asset we already have at HEAD, even when that asset is partial or documentation-led.
