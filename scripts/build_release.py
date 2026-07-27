#!/usr/bin/env python3
"""Build the public Torino Urban EPW Atlas release from validated project outputs."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely.geometry import mapping


VERSION = "0.1.0"
REPOSITORY_URL = "https://github.com/alijahanirahaei/torino-urban-epw-atlas"
SITE_URL = "https://alijahanirahaei.github.io/torino-urban-epw-atlas/"

CATEGORY_META = {
    "A": {
        "name": "Open low-rise",
        "slug": "open_lowrise",
        "description": "Open, predominantly low-rise urban fabric",
        "source_clusters": [0, 1],
        "representative_cluster": 1,
        "representative_grid_id": 3788,
        "color": "#2A9D8F",
    },
    "B": {
        "name": "Mid-rise mixed",
        "slug": "midrise_mixed",
        "description": "Mixed mid-rise urban fabric",
        "source_clusters": [2, 3],
        "representative_cluster": 3,
        "representative_grid_id": 10925,
        "color": "#E9C46A",
    },
    "C": {
        "name": "Tall/dense",
        "slug": "tall_dense",
        "description": "Taller and denser urban fabric",
        "source_clusters": [4, 5],
        "representative_cluster": 5,
        "representative_grid_id": 4849,
        "color": "#E76F51",
    },
    "D": {
        "name": "Large-footprint",
        "slug": "large_footprint",
        "description": "Dense, large-footprint, low-facade urban fabric",
        "source_clusters": [6],
        "representative_cluster": 6,
        "representative_grid_id": 1524,
        "color": "#6D597A",
    },
}

EPW_SOURCE_NAMES = {
    "A": "torino_urban_epw_A_open_lowrise_zone4A_flrh305.epw",
    "B": "torino_urban_epw_B_midrise_mixed_zone4A_flrh305.epw",
    "C": "torino_urban_epw_C_tall_dense_zone4A_flrh305.epw",
    "D": "torino_urban_epw_D_large_footprint_zone4A_flrh305.epw",
}

CONFIG_SOURCE_NAMES = {
    "A": "category_a_open_lowrise.json",
    "B": "category_b_midrise_mixed.json",
    "C": "category_c_tall_dense.json",
    "D": "category_d_large_footprint.json",
}

K_COLORS = {
    4: ["#57A773", "#A8DADC", "#F4A261", "#D1495B"],
    7: ["#5AB4AC", "#A8DADC", "#80B918", "#FFD166", "#F4A261", "#D1495B", "#6D597A"],
    8: ["#4EA8DE", "#72EFDD", "#80B918", "#FFD166", "#E9C46A", "#F4A261", "#D1495B", "#6D597A"],
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def clean_number(value, digits: int = 6):
    if pd.isna(value):
        return None
    return round(float(value), digits)


def clean_int(value):
    if pd.isna(value):
        return None
    return int(value)


def json_geometry(geometry):
    geom = mapping(geometry)

    def rounded(value):
        if isinstance(value, (list, tuple)):
            return [rounded(item) for item in value]
        return round(float(value), 6)

    geom["coordinates"] = rounded(geom["coordinates"])
    return geom


def validate_epw(path: Path) -> dict:
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        lines = handle.read().splitlines()
    if len(lines) != 8768:
        raise ValueError(f"{path.name}: expected 8,768 lines, found {len(lines)}")
    weather = lines[8:]
    bad_rows = [index + 9 for index, line in enumerate(weather) if len(line.split(",")) != 35]
    if bad_rows:
        raise ValueError(f"{path.name}: weather rows with non-35-field shape: {bad_rows[:5]}")
    return {"line_count": len(lines), "weather_rows": len(weather), "sha256": sha256(path)}


def make_public_table(grid: gpd.GeoDataFrame, assignments: pd.DataFrame, descriptors: pd.DataFrame) -> gpd.GeoDataFrame:
    if grid["grid_id"].duplicated().any() or assignments["grid_id"].duplicated().any():
        raise ValueError("Grid identifiers must be unique in both source tables")

    add_cols = [
        "grid_id",
        "merged_epw_category",
        "merged_epw_category_name",
        "representative_k7_cluster",
        "representative_grid_id",
        "recommended_epw_filename",
    ]
    public = grid.merge(assignments[add_cols], on="grid_id", how="left", validate="one_to_one")
    if len(public) != 12997:
        raise ValueError(f"Expected 12,997 grid locations, found {len(public):,}")

    descriptor_map = {
        (int(row.k), int(row.cluster)): str(row.descriptor)
        for row in descriptors.itertuples(index=False)
    }
    for k in (4, 7, 8):
        source = f"cluster_k{k}_provisional"
        public[f"cluster_k{k}_label"] = public[source].map(
            lambda value: descriptor_map.get((k, int(value))) if pd.notna(value) else None
        )

    public = public.rename(
        columns={
            "built_frac": "building_fraction",
            "uwg_treecover": "uwg_tree_cover_fraction",
            "uwg_grasscover": "uwg_grass_cover_fraction",
            "road_frac": "road_fraction",
            "merged_epw_category": "epw_category",
            "merged_epw_category_name": "epw_category_name",
            "recommended_epw_filename": "epw_filename",
        }
    )
    public["release_version"] = VERSION

    columns = [
        "grid_id",
        "grid_row",
        "grid_col",
        "center_x_3003",
        "center_y_3003",
        "center_lon",
        "center_lat",
        "fit_eligible",
        "edge_support",
        "qa_score",
        "qa_reasons",
        "exclusion_reason",
        "assignment_status",
        "building_fraction",
        "avg_height_m",
        "facade_to_site_ratio",
        "uwg_tree_cover_fraction",
        "uwg_grass_cover_fraction",
        "road_fraction",
        "green_pct",
        "tree_canopy_pct",
        "tree_count",
        "tree_density_ha",
        "tree_mean_height_m",
        "building_count",
        "height_valid_footprint_frac",
        "cluster_k4_provisional",
        "cluster_k4_label",
        "distance_to_medoid_k4",
        "distance_ratio_p95_k4",
        "outlier_gt_cluster_p99_k4",
        "cluster_k7_provisional",
        "cluster_k7_label",
        "distance_to_medoid_k7",
        "distance_ratio_p95_k7",
        "outlier_gt_cluster_p99_k7",
        "cluster_k8_provisional",
        "cluster_k8_label",
        "distance_to_medoid_k8",
        "distance_ratio_p95_k8",
        "outlier_gt_cluster_p99_k8",
        "epw_category",
        "epw_category_name",
        "representative_k7_cluster",
        "representative_grid_id",
        "epw_filename",
        "release_version",
        "geometry",
    ]
    return gpd.GeoDataFrame(public[columns], geometry="geometry", crs=grid.crs)


def write_zip_shapefile(gdf: gpd.GeoDataFrame, output: Path, layer_kind: str, k: int | None = None) -> None:
    with tempfile.TemporaryDirectory(prefix="torino_epw_shp_") as tmp:
        tmp_path = Path(tmp)
        if layer_kind == "cluster" and k is not None:
            cluster_col = f"cluster_k{k}_provisional"
            label_col = f"cluster_k{k}_label"
            frame = gdf[
                [
                    "grid_id",
                    cluster_col,
                    label_col,
                    "assignment_status",
                    "edge_support",
                    "qa_score",
                    "building_fraction",
                    "avg_height_m",
                    "facade_to_site_ratio",
                    "uwg_tree_cover_fraction",
                    "uwg_grass_cover_fraction",
                    "geometry",
                ]
            ].rename(
                columns={
                    "grid_id": "GRID_ID",
                    cluster_col: "CLUSTER",
                    label_col: "LABEL",
                    "assignment_status": "STATUS",
                    "edge_support": "EDGE",
                    "qa_score": "QA_SCORE",
                    "building_fraction": "BLD_FRAC",
                    "avg_height_m": "AVG_H_M",
                    "facade_to_site_ratio": "FAC_SITE",
                    "uwg_tree_cover_fraction": "TREE_FRAC",
                    "uwg_grass_cover_fraction": "GRASS_FRAC",
                }
            )
            stem = f"torino_clusters_k{k}"
        else:
            frame = gdf[
                [
                    "grid_id",
                    "epw_category",
                    "epw_category_name",
                    "epw_filename",
                    "cluster_k7_provisional",
                    "assignment_status",
                    "edge_support",
                    "qa_score",
                    "geometry",
                ]
            ].rename(
                columns={
                    "grid_id": "GRID_ID",
                    "epw_category": "EPW_CAT",
                    "epw_category_name": "EPW_NAME",
                    "epw_filename": "EPW_FILE",
                    "cluster_k7_provisional": "K7_CLASS",
                    "assignment_status": "STATUS",
                    "edge_support": "EDGE",
                    "qa_score": "QA_SCORE",
                }
            )
            stem = "torino_epw_categories"

        shp_path = tmp_path / f"{stem}.shp"
        gpd.GeoDataFrame(frame, geometry="geometry", crs=gdf.crs).to_file(
            shp_path, driver="ESRI Shapefile", encoding="UTF-8"
        )
        with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for part in sorted(tmp_path.glob(f"{stem}.*")):
                archive.write(part, arcname=part.name)


def write_web_geojson(gdf: gpd.GeoDataFrame, output: Path) -> None:
    web = gdf.to_crs(4326)
    features = []
    for row in web.itertuples(index=False):
        props = {
            "id": int(row.grid_id),
            "lon": clean_number(row.center_lon),
            "lat": clean_number(row.center_lat),
            "k4": clean_int(row.cluster_k4_provisional),
            "k7": clean_int(row.cluster_k7_provisional),
            "k8": clean_int(row.cluster_k8_provisional),
            "cat": None if pd.isna(row.epw_category) else str(row.epw_category),
            "status": str(row.assignment_status),
            "edge": bool(row.edge_support),
            "qa": clean_int(row.qa_score),
            "reason": "" if pd.isna(row.qa_reasons) else str(row.qa_reasons),
            "bld": clean_number(row.building_fraction, 4),
            "h": clean_number(row.avg_height_m, 2),
            "fs": clean_number(row.facade_to_site_ratio, 3),
            "tree": clean_number(row.uwg_tree_cover_fraction, 4),
            "grass": clean_number(row.uwg_grass_cover_fraction, 4),
            "green": clean_number(row.green_pct, 2),
            "road": clean_number(row.road_fraction, 4),
            "d7": clean_number(row.distance_to_medoid_k7, 3),
            "out7": bool(row.outlier_gt_cluster_p99_k7),
            "epw": None if pd.isna(row.epw_filename) else str(row.epw_filename),
        }
        features.append({"type": "Feature", "geometry": json_geometry(row.geometry), "properties": props})
    payload = {"type": "FeatureCollection", "features": features}
    output.write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")


def build_metadata(
    public: gpd.GeoDataFrame,
    medoids: gpd.GeoDataFrame,
    descriptors: pd.DataFrame,
    period_metrics: pd.DataFrame,
    epw_validation: dict,
) -> dict:
    descriptor_map = {
        str(k): {
            str(int(row.cluster)): str(row.descriptor)
            for row in descriptors.loc[descriptors["k"] == k].itertuples(index=False)
        }
        for k in (4, 7, 8)
    }
    medoid_rows = medoids.drop(columns="geometry").copy()
    medoid_lookup = {
        (int(row.k), int(row.cluster)): row._asdict()
        for row in medoid_rows.itertuples(index=False)
    }
    library_metrics = period_metrics.loc[period_metrics["case_type"] == "library"].copy()

    categories = {}
    for category, meta in CATEGORY_META.items():
        representative = medoid_lookup[(7, meta["representative_cluster"])]
        metrics = {
            str(row.period): clean_number(row.new_uhi_mean_c, 3)
            for row in library_metrics.loc[library_metrics["category_id"] == category].itertuples(index=False)
        }
        categories[category] = {
            **meta,
            "epw_filename": EPW_SOURCE_NAMES[category],
            "config_filename": CONFIG_SOURCE_NAMES[category],
            "location_count": int((public["epw_category"] == category).sum()),
            "uhi_mean_c": metrics,
            "representative_inputs": {
                "building_fraction": clean_number(representative["built_frac"], 4),
                "average_height_m": clean_number(representative["avg_height_m"], 2),
                "facade_to_site_ratio": clean_number(representative["facade_to_site_ratio"], 3),
                "tree_cover_fraction": clean_number(representative["uwg_treecover"], 4),
                "grass_cover_fraction": clean_number(representative["uwg_grasscover"], 4),
            },
            "epw_validation": epw_validation[category],
        }

    bounds = public.to_crs(4326).total_bounds.tolist()
    return {
        "title": "Torino Urban EPW Atlas",
        "authors": ["Ali JahaniRahaei", "Giacomo Chiesa"],
        "licenses": {
            "software": "MIT",
            "derived_research_outputs": "CC BY 4.0",
        },
        "repository_url": REPOSITORY_URL,
        "site_url": SITE_URL,
        "version": VERSION,
        "status": "candidate research release",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "crs": {"canonical": "EPSG:3003", "web": "EPSG:4326"},
        "bounds_wgs84": [round(value, 6) for value in bounds],
        "location_count": int(len(public)),
        "fit_location_count": int(public["fit_eligible"].sum()),
        "edge_location_count": int(public["edge_support"].sum()),
        "unassigned_location_count": int(public["epw_category"].isna().sum()),
        "support": {"assignment_grid_m": 100, "morphology_support_m": 500},
        "cluster_descriptors": descriptor_map,
        "cluster_colors": {str(k): colors for k, colors in K_COLORS.items()},
        "categories": categories,
        "limitations": [
            "The four EPWs are a medoid-level candidate library pending within-cluster UWG sampling.",
            "The library reproduces the fixed UWG setup; it is not a guarantee of local observational accuracy.",
            "Municipal-edge supports are provisional because no external GIS halo was used.",
            "The workflow does not generate morphology-dependent humidity-ratio changes.",
        ],
    }


def write_data_dictionary(path: Path) -> None:
    rows = [
        ("grid_id", "integer", "Stable identifier of the 100 m assignment location"),
        ("center_lon", "decimal degrees", "Assignment-cell center longitude, WGS84"),
        ("center_lat", "decimal degrees", "Assignment-cell center latitude, WGS84"),
        ("fit_eligible", "boolean", "True when the support entered clustering model fitting"),
        ("edge_support", "boolean", "True when the 500 m support crosses the municipal boundary"),
        ("qa_score", "integer", "Count of active morphology QA flags"),
        ("qa_reasons", "text", "Semicolon-delimited QA reasons"),
        ("assignment_status", "text", "clean_fit_member, edge_provisional, or another documented status"),
        ("building_fraction", "0-1 fraction", "Unioned building footprint area divided by 250,000 m2"),
        ("avg_height_m", "m", "Building-footprint-area-weighted mean valid height"),
        ("facade_to_site_ratio", "ratio", "Exposed compound perimeter times mean height divided by support area"),
        ("uwg_tree_cover_fraction", "0-1 fraction", "Constrained tree-canopy fraction passed to UWG"),
        ("uwg_grass_cover_fraction", "0-1 fraction", "Constrained residual grass fraction passed to UWG"),
        ("green_pct", "percent", "Mapped green area as a percentage of the support"),
        ("tree_canopy_pct", "percent", "Estimated unioned tree-canopy area as a percentage of the support"),
        ("road_fraction", "0-1 fraction", "Unioned road-surface area divided by support area"),
        ("cluster_k4_provisional", "integer", "Raw CLARA k=4 morphology assignment"),
        ("cluster_k7_provisional", "integer", "Raw CLARA k=7 retained morphology assignment"),
        ("cluster_k8_provisional", "integer", "Raw CLARA k=8 sensitivity assignment"),
        ("distance_to_medoid_k7", "robust-scaled distance", "Euclidean distance to the assigned k=7 medoid"),
        ("outlier_gt_cluster_p99_k7", "boolean", "True above the fitted class 99th-percentile distance"),
        ("epw_category", "A-D", "Reduced weather-output category derived from the k=7 medoids"),
        ("epw_filename", "text", "Recommended candidate EPW filename for the location"),
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["field", "unit_or_type", "definition"])
        writer.writerows(rows)


def write_checksums(repo: Path) -> None:
    included_roots = [repo / "data", repo / "web" / "data"]
    files = []
    for root in included_roots:
        files.extend(path for path in root.rglob("*") if path.is_file())
    checksum_path = repo / "checksums.sha256"
    with checksum_path.open("w", encoding="utf-8") as handle:
        for path in sorted(files):
            handle.write(f"{sha256(path)}  {path.relative_to(repo).as_posix()}\n")


def build(workspace: Path, repo: Path) -> None:
    clustering = workspace / "outputs/clustering_torino_regular_grid_20260713"
    extraction = workspace / "outputs/torino_full_regular_grid_100m_support_500m_20260713"
    accepted = workspace / "outputs/uwg_zone4a_flrh305_library_stations_20260714"

    source_gpkg = clustering / "spatial/torino_regular_grid_cluster_candidates.gpkg"
    grid = gpd.read_file(source_gpkg, layer="all_city_candidate_assignments")
    medoids = gpd.read_file(source_gpkg, layer="candidate_medoids")
    boundary = gpd.read_file(source_gpkg, layer="boundary_exact")
    assignments = pd.read_csv(accepted / "torino_grid_zone4a_flrh305_epw_assignments.csv")
    descriptors = pd.read_csv(clustering / "data/candidate_cluster_descriptors.csv")
    period_metrics = pd.read_csv(accepted / "analysis/period_metrics.csv")

    public = make_public_table(grid, assignments, descriptors)

    spatial_dir = repo / "data/spatial"
    tables_dir = repo / "data/tables"
    epw_dir = repo / "data/epw"
    configs_dir = repo / "data/configs"
    figures_dir = repo / "data/figures"
    web_data_dir = repo / "web/data"
    for directory in (spatial_dir, tables_dir, epw_dir, configs_dir, figures_dir, web_data_dir):
        directory.mkdir(parents=True, exist_ok=True)

    canonical = spatial_dir / "torino_urban_morphology_epw_atlas.gpkg"
    canonical.unlink(missing_ok=True)
    public.to_file(canonical, layer="grid_assignments", driver="GPKG")
    medoids.to_file(canonical, layer="cluster_medoids", driver="GPKG", mode="a")
    boundary.to_file(canonical, layer="city_boundary", driver="GPKG", mode="a")

    public.drop(columns="geometry").to_csv(tables_dir / "grid_assignments.csv", index=False)
    medoids.drop(columns="geometry").to_csv(tables_dir / "cluster_medoids_k4_k7_k8.csv", index=False)
    shutil.copy2(clustering / "data/candidate_cluster_profiles_long.csv", tables_dir / "cluster_profiles_k4_k7_k8.csv")
    shutil.copy2(clustering / "data/kmeans_k2_12_metrics.csv", tables_dir / "cluster_selection_metrics_k2_k12.csv")
    period_metrics.loc[period_metrics["case_type"] == "library"].to_csv(
        tables_dir / "epw_period_metrics.csv", index=False
    )
    write_data_dictionary(tables_dir / "data_dictionary.csv")

    geojson_path = spatial_dir / "torino_urban_morphology_epw_atlas_wgs84.geojson"
    public.to_crs(4326).to_file(geojson_path, driver="GeoJSON")
    with zipfile.ZipFile(str(geojson_path) + ".zip", "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.write(geojson_path, arcname=geojson_path.name)
    geojson_path.unlink()

    for k in (4, 7, 8):
        write_zip_shapefile(
            public,
            spatial_dir / f"torino_clusters_k{k}_epsg3003.zip",
            layer_kind="cluster",
            k=k,
        )
    write_zip_shapefile(
        public,
        spatial_dir / "torino_epw_categories_epsg3003.zip",
        layer_kind="epw",
    )

    epw_validation = {}
    manifest_rows = []
    for category in "ABCD":
        source_epw = accepted / "epw/library" / EPW_SOURCE_NAMES[category]
        target_epw = epw_dir / source_epw.name
        shutil.copy2(source_epw, target_epw)
        epw_validation[category] = validate_epw(target_epw)

        source_config = accepted / "configs/library" / CONFIG_SOURCE_NAMES[category]
        target_config = configs_dir / source_config.name
        shutil.copy2(source_config, target_config)
        manifest_rows.append(
            {
                "category": category,
                "category_name": CATEGORY_META[category]["name"],
                "source_k7_clusters": ";".join(map(str, CATEGORY_META[category]["source_clusters"])),
                "representative_k7_cluster": CATEGORY_META[category]["representative_cluster"],
                "representative_grid_id": CATEGORY_META[category]["representative_grid_id"],
                "epw_file": f"data/epw/{target_epw.name}",
                "epw_sha256": sha256(target_epw),
                "config_file": f"data/configs/{target_config.name}",
                "config_sha256": sha256(target_config),
                "source_forcing": "AvMY_CASELLE.epw",
                "source_forcing_doi": "10.5281/zenodo.14905721",
                "uwg_version": "5.3.4",
                "zone": "4A",
                "floor_height_m": 3.05,
                "characteristic_length_m": 500,
            }
        )
    pd.DataFrame(manifest_rows).to_csv(tables_dir / "epw_library_manifest.csv", index=False)

    figure_sources = {
        "map_clusters_k4.png": clustering / "figures/map_all_city_provisional_k4.png",
        "map_clusters_k7.png": clustering / "figures/map_all_city_provisional_k7.png",
        "map_clusters_k8.png": clustering / "figures/map_all_city_provisional_k8.png",
        "cluster_profiles_k4.png": clustering / "figures/cluster_profiles_k4.png",
        "cluster_profiles_k7.png": clustering / "figures/cluster_profiles_k7.png",
        "cluster_profiles_k8.png": clustering / "figures/cluster_profiles_k8.png",
        "cluster_selection_diagnostics.png": clustering / "figures/k_selection_diagnostics.png",
        "epw_uhi_by_period.png": workspace / "outputs/uwg_k7_merged_4_epw_comparison_20260713/figures/mean_uhi_by_period.png",
        "morphology_support_method.png": extraction / "figures/method_sampling_and_support.png",
    }
    for target_name, source in figure_sources.items():
        shutil.copy2(source, figures_dir / target_name)

    write_web_geojson(public, web_data_dir / "torino_lookup.geojson")
    boundary_web = boundary.to_crs(4326)
    boundary_web.to_file(web_data_dir / "torino_boundary.geojson", driver="GeoJSON")
    metadata = build_metadata(public, medoids, descriptors, period_metrics, epw_validation)
    (web_data_dir / "metadata.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=True) + "\n", encoding="utf-8"
    )

    source_manifest = {
        "release_version": VERSION,
        "authors": ["Ali JahaniRahaei", "Giacomo Chiesa"],
        "licenses": {
            "software": "MIT",
            "derived_research_outputs": "CC BY 4.0",
        },
        "repository_url": REPOSITORY_URL,
        "site_url": SITE_URL,
        "generated_at_utc": metadata["generated_at_utc"],
        "source_files": {
            "cluster_geopackage": {
                "source_workspace_path": source_gpkg.relative_to(workspace).as_posix(),
                "sha256": sha256(source_gpkg),
            },
            "epw_assignment_table": {
                "source_workspace_path": (accepted / "torino_grid_zone4a_flrh305_epw_assignments.csv").relative_to(workspace).as_posix(),
                "sha256": sha256(accepted / "torino_grid_zone4a_flrh305_epw_assignments.csv"),
            },
            "accepted_run_validation": {
                "source_workspace_path": (accepted / "VALIDATION_REPORT.json").relative_to(workspace).as_posix(),
                "sha256": sha256(accepted / "VALIDATION_REPORT.json"),
            },
        },
        "record_counts": {
            "grid_assignments": len(public),
            "cluster_medoids": len(medoids),
            "city_boundaries": len(boundary),
            "epw_files": 4,
        },
    }
    (repo / "release_manifest.json").write_text(
        json.dumps(source_manifest, indent=2) + "\n", encoding="utf-8"
    )
    write_checksums(repo)


def parse_args() -> argparse.Namespace:
    script = Path(__file__).resolve()
    default_repo = script.parents[1]
    default_workspace = default_repo.parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, default=default_workspace)
    parser.add_argument("--repo", type=Path, default=default_repo)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    build(args.workspace.resolve(), args.repo.resolve())
    print(f"Built Torino Urban EPW Atlas v{VERSION} in {args.repo.resolve()}")
