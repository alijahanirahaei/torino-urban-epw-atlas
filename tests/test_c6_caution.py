import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from lookup import lookup


class CautionTests(unittest.TestCase):
    def test_all_exported_counts_and_boundary_warnings(self):
        data = json.loads((ROOT / 'web/data/torino_lookup.geojson').read_text())
        props = [x['properties'] for x in data['features']]
        flagged = [p for p in props if p['caution']]
        self.assertEqual(len(flagged), 19)
        self.assertEqual(sum(p['outside_domain'] for p in props), 20)
        for p in flagged:
            self.assertEqual(p['k7'], 6)
            self.assertEqual(p['recommendation'], 'caution')
            self.assertTrue(p['available'])
            self.assertFalse(p['outside_domain'])
        p = flagged[0]
        result = lookup(ROOT, p['lat'], p['lon'])
        self.assertTrue(result['c6_caution'])
        self.assertIn('not validated', result['warning'])

    def test_ab_observational_caveat(self):
        data = json.loads((ROOT / 'web/data/torino_lookup.geojson').read_text())
        for category in ('A', 'B'):
            p = next(f['properties'] for f in data['features']
                     if f['properties']['cat'] == category and not f['properties']['edge'])
            self.assertIn('observational accuracy', lookup(ROOT, p['lat'], p['lon'])['warning'])


if __name__ == '__main__':
    unittest.main()
