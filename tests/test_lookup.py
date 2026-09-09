import json
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from lookup import lookup, find_feature  # noqa: E402


class LookupTests(unittest.TestCase):
    def test_alenia_revised_category(self):
        result = lookup(REPO, 45.08168097268994, 7.61225301548547)
        self.assertEqual(result["epw_category"], "C")
        self.assertEqual(result["recommendation_status"], "provisional")

    def test_invalid_coordinates(self):
        for lat, lon in [(float("nan"), 7), (45, float("inf")), (91, 7), (45, 181)]:
            with self.assertRaises(ValueError):
                lookup(REPO, lat, lon)

    def test_restricted_and_unassigned(self):
        collection = json.loads((REPO / "web/data/torino_lookup.geojson").read_text())
        for status in ["out_of_domain", "unassigned"]:
            props = next(
                f["properties"]
                for f in collection["features"]
                if f["properties"]["recommendation"] == status
                and not f["properties"]["edge"]
            )
            result = lookup(REPO, props["lat"], props["lon"])
            self.assertIsNotNone(result)
            self.assertFalse(result["epw_recommendation_available"])
            self.assertIsNone(result["epw_file"])
            self.assertIsNone(result["uwg_config"])
            self.assertEqual(result["recommendation_status"], status)

    def test_polygon_holes_and_shared_edge(self):
        outer = [[0, 0], [2, 0], [2, 2], [0, 2], [0, 0]]
        hole = [[0.5, 0.5], [1.5, 0.5], [1.5, 1.5], [0.5, 1.5], [0.5, 0.5]]
        first = {
            "geometry": {"type": "Polygon", "coordinates": [outer, hole]},
            "properties": {"id": 1},
        }
        second = {
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[2, 0], [3, 0], [3, 2], [2, 2], [2, 0]]],
            },
            "properties": {"id": 2},
        }
        collection = {"features": [first, second]}
        self.assertIsNone(find_feature(collection, 1, 1))
        self.assertEqual(find_feature(collection, 1, 2)["properties"]["id"], 1)

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
