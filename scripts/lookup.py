#!/usr/bin/env python3
"""Look up a Torino morphology class and candidate EPW from latitude/longitude."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def point_in_ring(lon: float, lat: float, ring: list[list[float]]) -> bool:
    inside = False
    j = len(ring) - 1
    for i in range(len(ring)):
        xi, yi = ring[i]
        xj, yj = ring[j]
        crosses = (yi > lat) != (yj > lat) and lon < ((xj - xi) * (lat - yi)) / (yj - yi) + xi
        if crosses:
            inside = not inside
        j = i
    return inside


def find_feature(collection: dict, lat: float, lon: float) -> dict | None:
    for feature in collection["features"]:
        ring = feature["geometry"]["coordinates"][0]
        lons = [point[0] for point in ring]
        lats = [point[1] for point in ring]
        if not (min(lons) <= lon <= max(lons) and min(lats) <= lat <= max(lats)):
            continue
        if point_in_ring(lon, lat, ring):
            return feature
    return None


def lookup(repo: Path, lat: float, lon: float) -> dict | None:
    lookup_path = repo / "web/data/torino_lookup.geojson"
    metadata_path = repo / "web/data/metadata.json"
    collection = json.loads(lookup_path.read_text(encoding="utf-8"))
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    feature = find_feature(collection, lat, lon)
    if feature is None:
        return None
    props = feature["properties"]
    category = metadata["categories"].get(props["cat"]) if props["cat"] else None
    return {
        "query": {"latitude": lat, "longitude": lon},
        "grid_id": props["id"],
        "assignment_status": props["status"],
        "edge_support": props["edge"],
        "qa_score": props["qa"],
        "clusters": {"k4": props["k4"], "k7": props["k7"], "k8": props["k8"]},
        "epw_category": props["cat"],
        "epw_category_name": category["name"] if category else None,
        "epw_file": f"data/epw/{category['epw_filename']}" if category else None,
        "uwg_config": f"data/configs/{category['config_filename']}" if category else None,
        "morphology": {
            "building_fraction": props["bld"],
            "average_height_m": props["h"],
            "facade_to_site_ratio": props["fs"],
            "tree_cover_fraction": props["tree"],
            "grass_cover_fraction": props["grass"],
            "green_percent": props["green"],
            "road_fraction": props["road"],
        },
        "warning": props["reason"] or None,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("latitude", type=float)
    parser.add_argument("longitude", type=float)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--compact", action="store_true")
    args = parser.parse_args()
    result = lookup(args.repo, args.latitude, args.longitude)
    if result is None:
        print(json.dumps({"error": "No Torino assignment cell covers this coordinate."}))
        return 2
    print(json.dumps(result, indent=None if args.compact else 2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
