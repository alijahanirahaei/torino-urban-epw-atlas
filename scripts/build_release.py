#!/usr/bin/env python3
"""Rebuild atlas exports from repository-contained, frozen research inputs."""

from __future__ import annotations
import argparse
import hashlib
import json
import tempfile
import zipfile
from pathlib import Path
import geopandas as gpd
import numpy as np
import pandas as pd

VERSION = "0.2.0"
REPOSITORY_URL = "https://github.com/alijahanirahaei/torino-urban-epw-atlas"
SITE_URL = "https://alijahanirahaei.github.io/torino-urban-epw-atlas/"
C6_LIMIT = 0.7951808541001185
FEATURES = [
    "building_fraction",
    "avg_height_m",
    "facade_to_site_ratio",
    "uwg_tree_cover_fraction",
    "uwg_grass_cover_fraction",
]
SOURCE_FEATURES = [
    "built_frac",
    "avg_height_m",
    "facade_to_site_ratio",
    "uwg_treecover",
    "uwg_grasscover",
]
CATEGORIES = {
    "A": dict(
        name="Open low-rise",
        source_clusters=[0, 1],
        representative_cluster=1,
        representative_grid_id=3788,
        color="#2A9D8F",
    ),
    "B": dict(
        name="Tree-rich mid-rise",
        source_clusters=[2],
        representative_cluster=2,
        representative_grid_id=10026,
        color="#E9C46A",
    ),
    "C": dict(
        name="Mixed/tall urban",
        source_clusters=[3, 4, 5],
        representative_cluster=4,
        representative_grid_id=5210,
        color="#E76F51",
    ),
    "D": dict(
        name="Large-footprint",
        source_clusters=[6],
        representative_cluster=6,
        representative_grid_id=1524,
        color="#6D597A",
    ),
}
K_COLORS = {
    4: ["#57A773", "#A8DADC", "#F4A261", "#D1495B"],
    7: ["#5AB4AC", "#A8DADC", "#80B918", "#FFD166", "#F4A261", "#D1495B", "#6D597A"],
    8: [
        "#4EA8DE",
        "#72EFDD",
        "#80B918",
        "#FFD166",
        "#E9C46A",
        "#F4A261",
        "#D1495B",
        "#6D597A",
    ],
}


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump(path, value):
    Path(path).write_text(
        json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )


def assign_corrected(archived, medoids, corrections, stats):
    """Fixed medoid identities and archived scaler; no new model fitting."""
    grid = archived.sort_values("grid_id").reset_index(drop=True).copy()
    correction = corrections.set_index("grid_id").loc[grid.grid_id].reset_index()
    for field, raw in zip(FEATURES, SOURCE_FEATURES):
        grid[f"archived_{field}"] = grid[field]
        if raw in {"uwg_treecover", "uwg_grasscover"}:
            grid[field] = correction[f"corrected_{raw}"].to_numpy()
    grid["canopy_area_delta_m2"] = correction.canopy_area_delta_m2.to_numpy()
    grid["tree_canopy_pct"] += grid.canopy_area_delta_m2 / 250000 * 100
    grid["canopy_corrected_gt_2p5_m2"] = grid.canopy_area_delta_m2.abs() > 2.5
    scaled = (
        grid[FEATURES].to_numpy() - stats["median"].to_numpy()
    ) / stats.iqr.to_numpy()
    valid = np.isfinite(scaled).all(axis=1)
    profiles, thresholds = [], []
    updated = medoids.copy()
    by_id = dict(zip(grid.grid_id, grid.index))
    for k in (4, 7, 8):
        label = f"cluster_k{k}_provisional"
        grid[f"archived_k{k}"] = grid[label]
        selected = medoids.loc[medoids.k == k].sort_values("cluster")
        indices = [by_id[i] for i in selected.medoid_grid_id]
        distance = np.linalg.norm(
            scaled[:, None, :] - scaled[indices][None, :, :], axis=2
        )
        labels = np.full(len(grid), np.nan)
        labels[valid] = distance[valid].argmin(axis=1)
        if not np.array_equal(
            labels[valid], correction[f"corrected_fixed_k{k}"].to_numpy()[valid]
        ):
            raise ValueError(
                f"k={k}: fixed classifier differs from frozen canopy audit"
            )
        grid[label] = labels
        grid[f"distance_to_medoid_k{k}"] = np.nan
        grid.loc[valid, f"distance_to_medoid_k{k}"] = distance[
            valid, labels[valid].astype(int)
        ]
        grid[f"distance_ratio_p95_k{k}"] = np.nan
        grid[f"outlier_gt_cluster_p99_k{k}"] = False
        for c, med_idx in enumerate(indices):
            mask = grid[label] == c
            fit = mask & grid.fit_eligible.astype(bool)
            d = grid.loc[fit, f"distance_to_medoid_k{k}"]
            p95, p99 = d.quantile([0.95, 0.99]).to_numpy()
            grid.loc[mask, f"distance_ratio_p95_k{k}"] = (
                grid.loc[mask, f"distance_to_medoid_k{k}"] / p95
            )
            grid.loc[mask, f"outlier_gt_cluster_p99_k{k}"] = (
                grid.loc[mask, f"distance_to_medoid_k{k}"] > p99
            )
            thresholds.append(
                dict(k=k, cluster=c, strict_fit_n=int(fit.sum()), p95=p95, p99=p99)
            )
            medmask = (updated.k == k) & (updated.cluster == c)
            for field, raw in zip(FEATURES, SOURCE_FEATURES):
                updated.loc[medmask, raw] = grid.loc[med_idx, field]
                values = grid.loc[fit, field]
                profiles.append(
                    dict(
                        k=k,
                        cluster=c,
                        variable=raw,
                        population="corrected_strict_fit",
                        n=int(fit.sum()),
                        mean=values.mean(),
                        q25=values.quantile(0.25),
                        median=values.median(),
                        q75=values.quantile(0.75),
                        scaled_median=(values.median() - stats.loc[raw, "median"])
                        / stats.loc[raw, "iqr"],
                    )
                )
            updated.loc[medmask, "cluster_size"] = fit.sum()
            updated.loc[medmask, "cluster_share"] = fit.sum() / grid.fit_eligible.sum()
            updated.loc[medmask, "mean_distance"] = d.mean()
            updated.loc[medmask, "p95_distance"] = p95
    return grid, updated, pd.DataFrame(profiles), pd.DataFrame(thresholds)


def apply_domain(grid):
    mapping = {
        c: cat for cat, meta in CATEGORIES.items() for c in meta["source_clusters"]
    }
    grid["epw_category"] = grid.cluster_k7_provisional.map(mapping)
    grid["c6_out_of_domain"] = (grid.cluster_k7_provisional == 6) & (
        grid.building_fraction >= C6_LIMIT
    )
    grid["epw_recommendation_available"] = (
        grid.epw_category.notna() & ~grid.c6_out_of_domain
    )
    provisional = (
        grid.edge_support | (grid.qa_score > 0) | grid.outlier_gt_cluster_p99_k7
    )
    grid["recommendation_status"] = np.select(
        [grid.epw_category.isna(), grid.c6_out_of_domain, provisional],
        ["unassigned", "out_of_domain", "provisional"],
        default="candidate",
    )
    grid["epw_category_name"] = grid.epw_category.map(
        {c: m["name"] for c, m in CATEGORIES.items()}
    )
    for col, key in [
        ("representative_k7_cluster", "representative_cluster"),
        ("representative_grid_id", "representative_grid_id"),
    ]:
        grid[col] = grid.epw_category.map({c: m[key] for c, m in CATEGORIES.items()})
    grid["epw_filename"] = grid.epw_category.map(
        {c: f"torino_urban_epw_{c}_v{VERSION}.epw" for c in CATEGORIES}
    )
    grid.loc[~grid.epw_recommendation_available, "epw_filename"] = None
    grid["release_version"] = VERSION
    return grid


def period_metrics(repo):
    source = pd.read_csv(
        repo / "research/inputs/k7_hourly_temperature_precision3.csv.gz"
    )
    month, hour = source.month, source.hour
    seasons = {
        "annual": np.ones(len(source), dtype=bool),
        "summer_apr_sep": month.between(4, 9),
        "winter_oct_mar": ~month.between(4, 9),
    }
    dayparts = {
        "all": np.ones(len(source), dtype=bool),
        "daytime_07_18": hour.between(7, 18),
        "nighttime_19_06": ~hour.between(7, 18),
    }
    rows = []
    for cat in CATEGORIES:
        frame = pd.read_csv(
            repo / f"data/epw/torino_urban_epw_{cat}_v{VERSION}.epw",
            skiprows=8,
            header=None,
        )
        if frame.shape != (8760, 35) or not np.array_equal(
            frame[[1, 2, 3]].to_numpy(), source[["month", "day", "hour"]].to_numpy()
        ):
            raise ValueError("EPW schema/chronology mismatch")
        if (
            not frame[8].between(0, 100).all()
            or (frame[7] > frame[6] + 0.1).any()
            or not frame[9].between(80000, 110000).all()
        ):
            raise ValueError("EPW physical screening failed")
        delta = frame[6].to_numpy() - source.caselle_dry_bulb_c.to_numpy()
        for season, smask in seasons.items():
            for daypart, dmask in dayparts.items():
                mask = smask & dmask
                name = (
                    season
                    if daypart == "all"
                    else daypart if season == "annual" else f"{season}_{daypart}"
                )
                rows.append(
                    dict(
                        category=cat,
                        period=name,
                        hours=int(mask.sum()),
                        precision_decimals=1,
                        uhi_mean_c=float(delta[mask].mean()),
                        rmse_vs_caselle_c=float(np.sqrt(np.mean(delta[mask] ** 2))),
                    )
                )
    return pd.DataFrame(rows)


def write_shapefile(grid, path, k=None):
    names = {
        "grid_id": "GRID_ID",
        "recommendation_status": "REC_STATUS",
        "epw_recommendation_available": "EPW_AVAIL",
        "c6_out_of_domain": "OUT_DOMAIN",
        "edge_support": "EDGE",
        "qa_score": "QA_SCORE",
    }
    if k:
        names.update(
            {
                f"cluster_k{k}_provisional": "CLUSTER",
                f"cluster_k{k}_label": "LABEL",
                "building_fraction": "BLD_FRAC",
                "avg_height_m": "AVG_H_M",
                "facade_to_site_ratio": "FAC_SITE",
                "uwg_tree_cover_fraction": "TREE_FRAC",
                "uwg_grass_cover_fraction": "GRASS_FRAC",
            }
        )
    else:
        names.update(
            {
                "epw_category": "EPW_CAT",
                "epw_category_name": "EPW_NAME",
                "epw_filename": "EPW_FILE",
                "cluster_k7_provisional": "K7_CLASS",
            }
        )
    with tempfile.TemporaryDirectory() as tmp:
        frame = grid[[*names, "geometry"]].rename(columns=names)
        shp = Path(tmp) / f"{path.stem.removesuffix('_epsg3003')}.shp"
        frame.to_file(shp, driver="ESRI Shapefile", encoding="UTF-8")
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
            for part in sorted(Path(tmp).iterdir()):
                z.write(part, part.name)


def write_checksums(repo):
    paths = sorted(
        p
        for folder in ["data", "web/data", "research"]
        for p in (repo / folder).rglob("*")
        if p.is_file() and not any(x in {"__pycache__", ".DS_Store"} for x in p.parts)
    )
    (repo / "checksums.sha256").write_text(
        "".join(f"{sha256(p)}  {p.relative_to(repo).as_posix()}\n" for p in paths)
    )


def build(repo):
    inputs = repo / "research/inputs"
    with tempfile.TemporaryDirectory() as tmp:
        with zipfile.ZipFile(inputs / "archived_atlas_v0.1.gpkg.zip") as z:
            z.extract("archived_atlas.gpkg", tmp)
        src = Path(tmp) / "archived_atlas.gpkg"
        archived = gpd.read_file(src, layer="grid_assignments")
        medoids = gpd.read_file(src, layer="cluster_medoids")
        boundary = gpd.read_file(src, layer="city_boundary")
    corrections = pd.read_csv(inputs / "canopy_corrected_fixed_assignments.csv")
    stats = (
        pd.read_csv(inputs / "robust_scale_stats.csv")
        .set_index("variable")
        .loc[SOURCE_FEATURES]
    )
    grid, medoids, profiles, thresholds = assign_corrected(
        archived, medoids, corrections, stats
    )
    grid = apply_domain(grid)
    descriptors = pd.read_csv(inputs / "candidate_cluster_descriptors.csv")
    for k in (4, 7, 8):
        grid[f"cluster_k{k}_label"] = grid[f"cluster_k{k}_provisional"].map(
            descriptors.loc[descriptors.k == k].set_index("cluster").descriptor
        )
    spatial, tables, web = (
        repo / "data/spatial",
        repo / "data/tables",
        repo / "web/data",
    )
    for folder in (spatial, tables, web):
        folder.mkdir(parents=True, exist_ok=True)
    canonical = spatial / "torino_urban_morphology_epw_atlas.gpkg"
    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp) / canonical.name
        grid.to_file(target, layer="grid_assignments", driver="GPKG")
        medoids.to_file(target, layer="cluster_medoids", driver="GPKG", mode="a")
        boundary.to_file(target, layer="city_boundary", driver="GPKG", mode="a")
        for k in (4, 7, 8):
            grid[
                [
                    "grid_id",
                    f"cluster_k{k}_provisional",
                    f"cluster_k{k}_label",
                    "recommendation_status",
                    "geometry",
                ]
            ].to_file(target, layer=f"morphology_k{k}", driver="GPKG", mode="a")
        grid[
            [
                "grid_id",
                "epw_category",
                "representative_grid_id",
                "epw_filename",
                "recommendation_status",
                "epw_recommendation_available",
                "geometry",
            ]
        ].to_file(target, layer="weather_categories", driver="GPKG", mode="a")
        canonical.write_bytes(target.read_bytes())
    grid.drop(columns="geometry").to_csv(tables / "grid_assignments.csv", index=False)
    medoids.drop(columns="geometry").to_csv(
        tables / "cluster_medoids_k4_k7_k8.csv", index=False
    )
    profiles.to_csv(tables / "cluster_profiles_k4_k7_k8.csv", index=False)
    thresholds.to_csv(tables / "corrected_distance_thresholds.csv", index=False)
    for k in (4, 7, 8):
        write_shapefile(grid, spatial / f"torino_clusters_k{k}_epsg3003.zip", k)
    write_shapefile(grid, spatial / "torino_epw_categories_epsg3003.zip")
    with zipfile.ZipFile(
        spatial / "torino_urban_morphology_epw_atlas_wgs84.geojson.zip",
        "w",
        zipfile.ZIP_DEFLATED,
    ) as z:
        z.writestr(
            "torino_urban_morphology_epw_atlas_wgs84.geojson",
            grid.to_crs(4326).to_json(drop_id=True),
        )
    short = {
        "grid_id": "id",
        "center_lon": "lon",
        "center_lat": "lat",
        "epw_category": "cat",
        "assignment_status": "status",
        "recommendation_status": "recommendation",
        "c6_out_of_domain": "outside_domain",
        "epw_recommendation_available": "available",
        "edge_support": "edge",
        "qa_score": "qa",
        "qa_reasons": "reason",
        "building_fraction": "bld",
        "avg_height_m": "h",
        "facade_to_site_ratio": "fs",
        "uwg_tree_cover_fraction": "tree",
        "uwg_grass_cover_fraction": "grass",
        "green_pct": "green",
        "road_fraction": "road",
        "distance_to_medoid_k7": "d7",
        "outlier_gt_cluster_p99_k7": "out7",
        "epw_filename": "epw",
        **{f"cluster_k{k}_provisional": f"k{k}" for k in (4, 7, 8)},
    }
    grid[[*short, "geometry"]].rename(columns=short).to_crs(4326).to_file(
        web / "torino_lookup.geojson", driver="GeoJSON"
    )
    boundary.to_crs(4326).to_file(web / "torino_boundary.geojson", driver="GeoJSON")
    metrics = period_metrics(repo)
    metrics.to_csv(tables / "epw_period_metrics.csv", index=False)
    manifest = pd.read_csv(inputs / "library_provenance.csv")
    for r in manifest.itertuples():
        if (
            sha256(repo / r.epw_file) != r.epw_sha256
            or sha256(repo / r.config_file) != r.config_sha256
        ):
            raise ValueError("Frozen JSON/EPW hash mismatch")
    manifest.to_csv(tables / "epw_library_manifest.csv", index=False)
    categories = {}
    for cat, meta in CATEGORIES.items():
        row = manifest.loc[manifest.category == cat].iloc[0]
        categories[cat] = {
            **meta,
            "epw_filename": Path(row.epw_file).name,
            "config_filename": Path(row.config_file).name,
            "location_count": int((grid.epw_category == cat).sum()),
            "available_location_count": int(
                ((grid.epw_category == cat) & grid.epw_recommendation_available).sum()
            ),
            "uhi_mean_c": metrics.loc[metrics.category == cat]
            .set_index("period")
            .uhi_mean_c.to_dict(),
        }
    metadata = dict(
        title="Torino Urban EPW Atlas",
        authors=["Ali JahaniRahaei", "Giacomo Chiesa"],
        licenses={"software": "MIT", "derived_research_outputs": "CC BY 4.0"},
        repository_url=REPOSITORY_URL,
        site_url=SITE_URL,
        version=VERSION,
        status="candidate research release",
        released="2026-09-09",
        location_count=len(grid),
        fit_location_count=int(grid.fit_eligible.sum()),
        edge_location_count=int(grid.edge_support.sum()),
        unassigned_location_count=int(grid.epw_category.isna().sum()),
        out_of_domain_count=int(grid.c6_out_of_domain.sum()),
        support={"assignment_grid_m": 100, "morphology_support_m": 500},
        c6_building_fraction_limit=C6_LIMIT,
        categories=categories,
        cluster_colors={str(k): v for k, v in K_COLORS.items()},
        cluster_descriptors={
            str(k): {
                str(int(r.cluster)): r.descriptor
                for r in descriptors.loc[descriptors.k == k].itertuples()
            }
            for k in (4, 7, 8)
        },
        limitations=[
            "Modeled, not measured local weather; observation agreement is location dependent.",
            "High-density C6 recommendations are withheld; below-threshold membership is not an accuracy guarantee.",
            "Overlapping supports are not independent neighborhoods or 100 m climate resolution.",
            "No resolved morphology-dependent humidity-ratio response in this workflow.",
        ],
    )
    dump(web / "metadata.json", metadata)
    source_files = {
        p.name: {"repository_path": p.relative_to(repo).as_posix(), "sha256": sha256(p)}
        for p in sorted(inputs.iterdir())
    }
    dump(
        repo / "release_manifest.json",
        dict(
            release_version=VERSION,
            authors=metadata["authors"],
            licenses=metadata["licenses"],
            repository_url=REPOSITORY_URL,
            site_url=SITE_URL,
            source_files=source_files,
            public_epw_precision_decimals=1,
            canopy_policy="Archived scaler and medoid identities, corrected fixed assignments; not a refit",
            record_counts={
                "grid_assignments": len(grid),
                "cluster_medoids": len(medoids),
                "city_boundaries": len(boundary),
                "gpkg_layers": 7,
                "epw_files": 4,
            },
        ),
    )
    from release_docs import write_dictionary, write_catalog
    from release_figures import generate

    write_dictionary(repo, grid)
    generate(repo, grid, profiles, metrics, boundary)
    write_catalog(repo)
    write_checksums(repo)
    print(
        f"Rebuilt atlas {VERSION}: {len(grid)} locations, {int(grid.c6_out_of_domain.sum())} domain exclusions"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo", type=Path, default=Path(__file__).resolve().parents[1]
    )
    build(parser.parse_args().repo.resolve())
