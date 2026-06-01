import unittest

from inventory import build_import_payload, summarize_rows


class InventoryTests(unittest.TestCase):
    def test_build_import_payload_normalizes_sku(self):
        payload = build_import_payload(
            [
                {"sku": "  rack a 01 ", "quantity": 2, "enabled": True},
                {"sku": "leaf-9", "quantity": 1, "enabled": False},
            ]
        )
        self.assertEqual(payload[0]["sku"], "RACK-A-01")
        self.assertEqual(payload[1]["sku"], "LEAF-9")

    def test_summarize_rows_counts_enabled_and_disabled(self):
        summary = summarize_rows(
            [
                {"enabled": True},
                {"enabled": False},
                {"enabled": False},
            ]
        )
        self.assertEqual(summary["total"], 3)
        self.assertEqual(summary["enabled"], 1)
        self.assertEqual(summary["disabled"], 2)


if __name__ == "__main__":
    unittest.main()
