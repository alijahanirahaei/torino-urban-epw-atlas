#!/usr/bin/env python3
"""Exhaustive minimax dry-bulb representative selection, then weighted-mean tie break."""

import argparse
import itertools
from pathlib import Path
import numpy as np
import pandas as pd


def reduce(series, weights):
    distance = np.sqrt(np.mean((series[:, :, None] - series[:, None, :]) ** 2, axis=0))
    rows = []
    for size in range(1, 8):
        candidates = []
        for subset in itertools.combinations(range(7), size):
            nearest = distance[:, subset].min(axis=1)
            candidates.append((float(nearest.max()), float(nearest @ weights), subset))
        maximum, mean, subset = min(candidates)
        rows.append(
            dict(
                epw_count=size,
                representatives=";".join(f"C{c}" for c in subset),
                maximum_medoid_rmse_c=maximum,
                weighted_mean_medoid_rmse_c=mean,
            )
        )
    return pd.DataFrame(rows), distance


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[1]
    frame = pd.read_csv(
        repo / "research/inputs/k7_hourly_temperature_precision3.csv.gz"
    )
    manifest = pd.read_csv(repo / "research/uwg/run_manifest.csv").sort_values(
        "cluster"
    )
    weights = manifest.cluster_share.to_numpy()
    weights = weights / weights.sum()
    table, distance = reduce(
        frame[[f"C{c}_dry_bulb_c" for c in range(7)]].to_numpy(), weights
    )
    print(table.to_string(index=False))
    if args.check:
        chosen = table.loc[table.epw_count == 4].iloc[0]
        assert chosen.representatives == "C1;C2;C4;C6"
        assert abs(chosen.maximum_medoid_rmse_c - 0.04019) < 0.00001
        assigned = np.array([1, 1, 2, 4, 4, 4, 6])
        assert np.array_equal(
            np.array([1, 2, 4, 6])[distance[:, [1, 2, 4, 6]].argmin(axis=1)], assigned
        )
        print("PASS: accepted four representatives and assignments reproduced.")
    if args.output:
        if args.output.exists():
            raise FileExistsError(
                "Choose a new output path; existing evidence is not overwritten."
            )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        table.to_csv(args.output, index=False)


if __name__ == "__main__":
    main()
