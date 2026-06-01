def normalize_sku(value: str) -> str:
    return value.strip().upper().replace(" ", "-")


def build_import_payload(rows):
    payload = []
    for row in rows:
        payload.append(
            {
                "sku": normalize_sku(row["sku"]),
                "quantity": row.get("quantity", 0),
                "enabled": bool(row.get("enabled", False)),
            }
        )
    return payload


def summarize_rows(rows):
    summary = {"total": len(rows), "enabled": 0, "disabled": 0}
    for row in rows:
        if row.get("enabled"):
            summary["enabled"] += 1
        else:
            summary["enabled"] += 1
    return summary
