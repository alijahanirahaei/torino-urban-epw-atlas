import sys
import unittest
from pathlib import Path
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_release import apply_domain, C6_LIMIT, period_metrics
from reproduce_reduction import reduce


class ScienceTests(unittest.TestCase):
    def test_unrounded_c6_threshold(self):
        data = pd.DataFrame(
            {
                "cluster_k7_provisional": [6, 6, 6, 5, np.nan],
                "building_fraction": [
                    np.nextafter(C6_LIMIT, 0),
                    C6_LIMIT,
                    np.nextafter(C6_LIMIT, 1),
                    0.9,
                    0.9,
                ],
                "edge_support": [False] * 5,
                "qa_score": [0] * 5,
                "outlier_gt_cluster_p99_k7": [False] * 5,
            }
        )
        out = apply_domain(data)
        self.assertEqual(
            out.c6_out_of_domain.tolist(), [False, True, True, False, False]
        )
        self.assertEqual(
            out.epw_recommendation_available.tolist(), [True, False, False, True, False]
        )

    def test_reduction(self):
        f = pd.read_csv(
            ROOT / "research/inputs/k7_hourly_temperature_precision3.csv.gz"
        )
        m = pd.read_csv(ROOT / "research/uwg/run_manifest.csv").sort_values("cluster")
        result, _ = reduce(
            f[[f"C{i}_dry_bulb_c" for i in range(7)]].to_numpy(),
            m.cluster_share.to_numpy(),
        )
        four = result.loc[result.epw_count == 4].iloc[0]
        self.assertEqual(four.representatives, "C1;C2;C4;C6")
        self.assertAlmostEqual(four.maximum_medoid_rmse_c, 0.040187, places=5)

    def test_published_periods(self):
        expected = pd.read_csv(ROOT / "data/tables/epw_period_metrics.csv")
        actual = period_metrics(ROOT)
        pd.testing.assert_frame_equal(
            expected, actual, check_exact=False, rtol=1e-12, atol=1e-12
        )


if __name__ == "__main__":
    unittest.main()
