#!/usr/bin/env python3
"""Validate the structure, files, lineage, and lookup behavior of a release."""

from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
import zipfile
import numpy as np
import pandas as pd
from pathlib import Path

import geopandas as gpd
import pyogrio

from lookup import lookup

EXPECTED_COUNT = 12997
EXPECTED_CATEGORIES = {"A", "B", "C", "D"}
EXPECTED_REPOSITORY_URL = "https://github.com/alijahanirahaei/torino-urban-epw-atlas"
EXPECTED_SITE_URL = "https://alijahanirahaei.github.io/torino-urban-epw-atlas/"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    repo = Path(__file__).resolve().parents[1]
    failures: list[str] = []
    passes: list[str] = []

    def check(condition: bool, name: str, detail: str = "") -> None:
        if condition:
            passes.append(name)
        else:
            failures.append(f"{name}: {detail}" if detail else name)

    required = [
        "README.md",
        "AUTHORS.md",
        "LICENSE",
        "DATA_LICENSE.md",
        "CITATION.cff",
        "docs/repository-guide.md",
        "docs/repository-guide.html",
        "index.html",
        "assets/app.js",
        "assets/styles.css",
        "web/data/metadata.json",
        "web/data/torino_lookup.geojson",
        "data/spatial/torino_urban_morphology_epw_atlas.gpkg",
        "data/tables/grid_assignments.csv",
        "data/tables/epw_library_manifest.csv",
        "checksums.sha256",
    ]
    for relative in required:
        path = repo / relative
        check(path.is_file() and path.stat().st_size > 0, f"required:{relative}")

    metadata = json.loads((repo / "web/data/metadata.json").read_text(encoding="utf-8"))
    lookup_geojson = json.loads(
        (repo / "web/data/torino_lookup.geojson").read_text(encoding="utf-8")
    )
    check(metadata["location_count"] == EXPECTED_COUNT, "metadata_location_count")
    check(
        metadata.get("authors") == ["Ali JahaniRahaei", "Giacomo Chiesa"],
        "metadata_authors",
        str(metadata.get("authors")),
    )
    check(
        metadata.get("licenses")
        == {"software": "MIT", "derived_research_outputs": "CC BY 4.0"},
        "metadata_licenses",
        str(metadata.get("licenses")),
    )
    check(
        metadata.get("repository_url") == EXPECTED_REPOSITORY_URL,
        "metadata_repository_url",
    )
    check(metadata.get("site_url") == EXPECTED_SITE_URL, "metadata_site_url")
    check(len(lookup_geojson["features"]) == EXPECTED_COUNT, "web_feature_count")
    check(set(metadata["categories"]) == EXPECTED_CATEGORIES, "metadata_categories")
    category_total = sum(
        value["location_count"] for value in metadata["categories"].values()
    )
    check(
        category_total + metadata["unassigned_location_count"] == EXPECTED_COUNT,
        "category_count_balance",
    )

    with (repo / "data/tables/grid_assignments.csv").open(
        newline="", encoding="utf-8"
    ) as handle:
        row_count = sum(1 for _ in csv.DictReader(handle))
    check(row_count == EXPECTED_COUNT, "csv_row_count", str(row_count))

    gpkg = repo / "data/spatial/torino_urban_morphology_epw_atlas.gpkg"
    layer_names = set(pyogrio.list_layers(gpkg)[:, 0])
    check(
        layer_names
        == {
            "grid_assignments",
            "cluster_medoids",
            "city_boundary",
            "morphology_k4",
            "morphology_k7",
            "morphology_k8",
            "weather_categories",
        },
        "gpkg_layers",
        str(layer_names),
    )
    grid = gpd.read_file(gpkg, layer="grid_assignments")
    check(len(grid) == EXPECTED_COUNT, "gpkg_grid_count")
    check(str(grid.crs).upper() == "EPSG:3003", "gpkg_grid_crs", str(grid.crs))
    check(grid.geometry.is_valid.all(), "gpkg_valid_geometries")
    check(not grid["grid_id"].duplicated().any(), "gpkg_unique_grid_ids")

    table = (
        pd.read_csv(repo / "data/tables/grid_assignments.csv")
        .sort_values("grid_id")
        .reset_index(drop=True)
    )
    grid = grid.sort_values("grid_id").reset_index(drop=True)
    check(metadata["version"] == "0.2.0", "release_version")
    check(
        table.epw_category.value_counts().to_dict()
        == {"C": 6662, "A": 4697, "B": 1090, "D": 413},
        "revised_category_counts",
    )
    check(int(table.epw_category.isna().sum()) == 135, "unassigned_135")
    check(int(table.c6_out_of_domain.sum()) == 20, "c6_guard_20")
    check(int(table.canopy_corrected_gt_2p5_m2.sum()) == 75, "canopy_75_supports")
    corrected = (
        pd.read_csv(repo / "research/inputs/diagnostic_corrected_features.csv")
        .set_index("grid_id")
        .loc[table.grid_id]
    )
    for field, source in {
        "building_fraction": "built_frac",
        "avg_height_m": "avg_height_m",
        "facade_to_site_ratio": "facade_to_site_ratio",
        "uwg_tree_cover_fraction": "uwg_treecover",
        "uwg_grass_cover_fraction": "uwg_grasscover",
    }.items():
        check(
            np.allclose(
                table[field], corrected[source], equal_nan=True, atol=1e-12, rtol=1e-12
            ),
            f"independent_corrected_features:{field}",
        )
    check(
        table.loc[~table.epw_recommendation_available, "epw_filename"].isna().all(),
        "restricted_filenames_absent",
    )
    for field in [
        "grid_id",
        "epw_category",
        "recommendation_status",
        "epw_filename",
        "epw_recommendation_available",
        "c6_out_of_domain",
    ]:
        check(
            table[field]
            .fillna("")
            .astype(str)
            .equals(grid[field].fillna("").astype(str)),
            f"csv_gpkg:{field}",
        )
    web_rows = (
        pd.DataFrame([f["properties"] for f in lookup_geojson["features"]])
        .sort_values("id")
        .reset_index(drop=True)
    )
    for short, full in {
        "id": "grid_id",
        "cat": "epw_category",
        "recommendation": "recommendation_status",
        "epw": "epw_filename",
        "available": "epw_recommendation_available",
        "outside_domain": "c6_out_of_domain",
    }.items():
        check(
            web_rows[short]
            .fillna("")
            .astype(str)
            .equals(table[full].fillna("").astype(str)),
            f"web_csv:{short}",
        )
    for k, expected_changes in [(4, 2), (7, 0), (8, 3)]:
        field = f"cluster_k{k}_provisional"
        check(
            np.allclose(table[field], grid[field], equal_nan=True),
            f"labels_csv_gpkg:k{k}",
        )
        check(
            np.allclose(table[field], web_rows[f"k{k}"], equal_nan=True),
            f"labels_web:k{k}",
        )
        valid = table[field].notna()
        check(
            int((table.loc[valid, field] != table.loc[valid, f"archived_k{k}"]).sum())
            == expected_changes,
            f"bounded_canopy_labels:k{k}",
        )
        thematic = (
            gpd.read_file(gpkg, layer=f"morphology_k{k}")
            .sort_values("grid_id")
            .reset_index(drop=True)
        )
        check(
            np.allclose(table[field], thematic[field], equal_nan=True), f"thematic:k{k}"
        )
    weather_layer = (
        gpd.read_file(gpkg, layer="weather_categories")
        .sort_values("grid_id")
        .reset_index(drop=True)
    )
    check(
        weather_layer.epw_filename.fillna("").equals(table.epw_filename.fillna("")),
        "weather_thematic_filenames",
    )
    for f in [
        "building_fraction",
        "avg_height_m",
        "facade_to_site_ratio",
        "uwg_tree_cover_fraction",
        "uwg_grass_cover_fraction",
        "tree_canopy_pct",
    ]:
        check(
            np.allclose(table[f], grid[f], equal_nan=True), f"morphology_csv_gpkg:{f}"
        )

    for stem in [
        "torino_clusters_k4",
        "torino_clusters_k7",
        "torino_clusters_k8",
        "torino_epw_categories",
    ]:
        archive = next((repo / "data/spatial").glob(f"{stem}_epsg3003.zip"), None)
        check(archive is not None, f"shapefile_archive:{stem}")
        if archive:
            with zipfile.ZipFile(archive) as zipped:
                suffixes = {Path(name).suffix.lower() for name in zipped.namelist()}
            check(
                {".shp", ".shx", ".dbf", ".prj"}.issubset(suffixes),
                f"shapefile_parts:{stem}",
            )
            frame = (
                gpd.read_file(f"zip://{archive}")
                .sort_values("GRID_ID")
                .reset_index(drop=True)
            )
            check(frame.GRID_ID.equals(table.grid_id), f"shapefile_ids:{stem}")
            check(
                frame.REC_STATUS.equals(table.recommendation_status),
                f"shapefile_domain:{stem}",
            )
            if "EPW_FILE" in frame:
                check(
                    frame.EPW_FILE.fillna("").equals(table.epw_filename.fillna("")),
                    "shapefile_epw_guard",
                )
            else:
                k = int(stem[-1])
                check(
                    np.allclose(
                        frame.CLUSTER,
                        table[f"cluster_k{k}_provisional"],
                        equal_nan=True,
                    ),
                    f"shapefile_labels:k{k}",
                )

    zipped = (
        gpd.read_file(
            f"zip://{repo/'data/spatial/torino_urban_morphology_epw_atlas_wgs84.geojson.zip'}"
        )
        .sort_values("grid_id")
        .reset_index(drop=True)
    )
    check(
        zipped.epw_filename.fillna("").equals(table.epw_filename.fillna("")),
        "full_geojson_guard",
    )

    manifest_rows = list(
        csv.DictReader(
            (repo / "data/tables/epw_library_manifest.csv").open(encoding="utf-8")
        )
    )
    check(
        {row["category"] for row in manifest_rows} == EXPECTED_CATEGORIES,
        "epw_manifest_categories",
    )
    for row in manifest_rows:
        category = row["category"]
        check(
            int(row["representative_k7_cluster"]) == dict(A=1, B=2, C=4, D=6)[category],
            f"revised_representative:{category}",
        )
        epw = repo / row["epw_file"]
        config = repo / row["config_file"]
        check(epw.is_file(), f"epw_exists:{category}")
        if epw.is_file():
            lines = epw.read_text(encoding="utf-8", errors="replace").splitlines()
            check(len(lines) == 8768, f"epw_line_count:{category}", str(len(lines)))
            check(
                all(len(line.split(",")) == 35 for line in lines[8:]),
                f"epw_field_count:{category}",
            )
            check(sha256(epw) == row["epw_sha256"], f"epw_hash:{category}")
            weather = pd.read_csv(epw, skiprows=8, header=None)
            check(weather[8].between(0, 100).all(), f"rh_range:{category}")
            check((weather[7] <= weather[6] + 0.1).all(), f"dewpoint:{category}")
            check(weather[9].between(80000, 110000).all(), f"pressure_pa:{category}")
        check(config.is_file(), f"config_exists:{category}")
        if config.is_file():
            payload = json.loads(config.read_text(encoding="utf-8"))
            check(payload.get("zone") == "4A", f"config_zone:{category}")
            check(
                float(payload.get("flr_h")) == 3.05, f"config_floor_height:{category}"
            )
            check(
                float(payload.get("charlength")) == 500.0,
                f"config_charlength:{category}",
            )
            check(sha256(config) == row["config_sha256"], f"config_hash:{category}")

    checksum_rows = []
    for line in (repo / "checksums.sha256").read_text(encoding="utf-8").splitlines():
        checksum, relative = line.split("  ", 1)
        checksum_rows.append((checksum, relative))
    for expected, relative in checksum_rows:
        path = repo / relative
        check(
            path.is_file() and sha256(path) == expected, f"release_checksum:{relative}"
        )

    known_locations = [
        (45.07573950763745, 7.678542597506742, 7096, "C", 5),
        (45.071654970061005, 7.691154385858236, 6455, "C", 4),
        (45.08168097268994, 7.61225301548547, 7925, "C", 3),
        (45.112335622274664, 7.671744288136738, 11464, "D", 6),
    ]
    for lat, lon, grid_id, category, k7 in known_locations:
        result = lookup(repo, lat, lon)
        check(result is not None, f"lookup_exists:{grid_id}")
        if result:
            check(
                result["grid_id"] == grid_id,
                f"lookup_grid:{grid_id}",
                str(result["grid_id"]),
            )
            check(result["epw_category"] == category, f"lookup_category:{grid_id}")
            check(result["clusters"]["k7"] == k7, f"lookup_k7:{grid_id}")
    check(lookup(repo, 45.5, 8.0) is None, "lookup_outside_city")
    for row in table.loc[table.c6_out_of_domain].itertuples():
        result = lookup(repo, row.center_lat, row.center_lon)
        check(
            result is not None
            and result["epw_file"] is None
            and result["recommendation_status"] == "out_of_domain",
            f"c6_lookup_guard:{row.grid_id}",
        )

    excluded_parts = {
        ".git",
        ".idea",
        ".npm",
        ".pytest_cache",
        ".venv",
        ".vscode",
        "__pycache__",
        "coverage",
        "node_modules",
        "playwright-report",
        "test-results",
        "venv",
        "_site",
    }
    text_suffixes = {
        ".cff",
        ".cpg",
        ".css",
        ".csv",
        ".epw",
        ".geojson",
        ".html",
        ".ini",
        ".js",
        ".json",
        ".md",
        ".prj",
        ".py",
        ".toml",
        ".txt",
        ".yaml",
        ".yml",
    }
    public_text_paths = []
    for path in repo.rglob("*"):
        if not path.is_file() or path.resolve() == Path(__file__).resolve():
            continue
        relative = path.relative_to(repo)
        if any(part in excluded_parts for part in relative.parts):
            continue
        if relative.parts[:2] == ("assets", "vendor"):
            continue
        if path.suffix.lower() in text_suffixes or path.name in {"LICENSE", "Makefile"}:
            public_text_paths.append(path)
    public_text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore") for path in public_text_paths
    )

    absolute_path_patterns = {
        "macos_home": r"/Users/[^/\s]+/",
        "linux_home": r"/home/[^/\s]+/",
        "windows_home": r"[A-Za-z]:\\Users\\[^\\\s]+\\",
    }
    for label, pattern in absolute_path_patterns.items():
        check(
            re.search(pattern, public_text) is None,
            f"no_private_absolute_paths:{label}",
        )

    for token in ["USER" + "NAME", "REPOSITORY" + "-NAME"]:
        check(token not in public_text, f"no_repository_placeholder:{token}")

    secret_patterns = {
        "github_classic_token": r"ghp_[A-Za-z0-9]{20,}",
        "github_fine_grained_token": r"github_pat_[A-Za-z0-9_]{20,}",
        "openai_token": r"sk-[A-Za-z0-9_-]{20,}",
        "aws_access_key": r"AKIA[0-9A-Z]{16}",
        "private_key": r"BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY",
    }
    for label, pattern in secret_patterns.items():
        check(re.search(pattern, public_text) is None, f"no_embedded_secret:{label}")

    gitignore_lines = {
        line.strip()
        for line in (repo / ".gitignore").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }
    for required_ignore in {
        "node_modules/",
        ".env",
        "*.pem",
        "*.key",
        ".vscode/",
        ".idea/",
    }:
        check(required_ignore in gitignore_lines, f"gitignore:{required_ignore}")

    for archive in sorted((repo / "data/spatial").glob("*.zip")):
        with zipfile.ZipFile(archive) as zipped:
            unsafe_members = [
                name
                for name in zipped.namelist()
                if name.startswith(("/", "\\"))
                or ".." in Path(name).parts
                or any(part in {"__MACOSX", ".DS_Store"} for part in Path(name).parts)
            ]
        check(
            not unsafe_members,
            f"safe_archive_members:{archive.name}",
            ", ".join(unsafe_members),
        )

    citation_text = (repo / "CITATION.cff").read_text(encoding="utf-8")
    data_license_text = (repo / "DATA_LICENSE.md").read_text(encoding="utf-8")
    authors_text = (repo / "AUTHORS.md").read_text(encoding="utf-8")
    citation_authors = {
        "Ali JahaniRahaei": ('given-names: "Ali"', 'family-names: "JahaniRahaei"'),
        "Giacomo Chiesa": ('given-names: "Giacomo"', 'family-names: "Chiesa"'),
    }
    for author, cff_parts in citation_authors.items():
        check(
            all(part in citation_text for part in cff_parts),
            f"citation_author:{author}",
        )
        check(author in data_license_text, f"data_license_author:{author}")
        check(author in authors_text, f"authors_file:{author}")
    check(EXPECTED_REPOSITORY_URL in citation_text, "citation_repository_url")
    check(EXPECTED_SITE_URL in citation_text, "citation_site_url")

    release_manifest = json.loads(
        (repo / "release_manifest.json").read_text(encoding="utf-8")
    )
    check(
        release_manifest.get("authors") == ["Ali JahaniRahaei", "Giacomo Chiesa"],
        "release_manifest_authors",
        str(release_manifest.get("authors")),
    )
    check(
        release_manifest.get("repository_url") == EXPECTED_REPOSITORY_URL,
        "release_manifest_repository_url",
    )
    check(
        release_manifest.get("site_url") == EXPECTED_SITE_URL,
        "release_manifest_site_url",
    )
    source_records = release_manifest.get("source_files", {}).values()
    check(
        all(
            "repository_path" in record
            and (repo / record["repository_path"]).is_file()
            and sha256(repo / record["repository_path"]) == record["sha256"]
            for record in source_records
        ),
        "release_manifest_source_paths",
    )

    guide_text = (repo / "docs/repository-guide.md").read_text(encoding="utf-8")
    release_files = []
    for path in repo.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(repo)
        if any(part in excluded_parts for part in relative.parts):
            continue
        if relative.name == ".DS_Store" or relative.suffix in {".pyc", ".log"}:
            continue
        release_files.append(relative.as_posix())
    sensitive_names = {
        ".env",
        "credentials",
        "credentials.json",
        "id_rsa",
        "id_ed25519",
    }
    sensitive_suffixes = {".key", ".p12", ".pem", ".pfx"}
    sensitive_files = sorted(
        path
        for path in release_files
        if Path(path).name.lower() in sensitive_names
        or Path(path).suffix.lower() in sensitive_suffixes
    )
    check(not sensitive_files, "no_sensitive_release_files", ", ".join(sensitive_files))
    undocumented = sorted(
        path for path in release_files if f"`{path}`" not in guide_text
    )
    check(not undocumented, "repository_guide_complete", ", ".join(undocumented))

    report = {
        "status": "PASS" if not failures else "FAIL",
        "passed_checks": len(passes),
        "failed_checks": failures,
    }
    (repo / "validation_report.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
