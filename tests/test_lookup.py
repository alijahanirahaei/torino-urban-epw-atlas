import json
import sys
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from lookup import lookup  # noqa: E402


class LookupTests(unittest.TestCase):
    def test_consolata(self):
        result = lookup(REPO, 45.07573950763745, 7.678542597506742)
        self.assertIsNotNone(result)
        self.assertEqual(result["grid_id"], 7096)
        self.assertEqual(result["clusters"]["k7"], 5)
        self.assertEqual(result["epw_category"], "C")

    def test_giardini_reali(self):
        result = lookup(REPO, 45.071654970061005, 7.691154385858236)
        self.assertIsNotNone(result)
        self.assertEqual(result["grid_id"], 6455)
        self.assertEqual(result["clusters"]["k7"], 4)
        self.assertEqual(result["epw_category"], "C")

    def test_reiss_romoli(self):
        result = lookup(REPO, 45.112335622274664, 7.671744288136738)
        self.assertIsNotNone(result)
        self.assertEqual(result["grid_id"], 11464)
        self.assertEqual(result["clusters"]["k7"], 6)
        self.assertEqual(result["epw_category"], "D")

    def test_outside_city(self):
        self.assertIsNone(lookup(REPO, 45.5, 8.0))


if __name__ == "__main__":
    unittest.main()
