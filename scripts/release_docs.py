"""Generate public field definitions, a complete file catalog and HTML guides."""

import csv
import html
from pathlib import Path
import markdown

EXCLUDED = {
    ".git",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    ".idea",
    ".vscode",
    ".npm",
    "test-results",
    "playwright-report",
    "_site",
}


def write_dictionary(repo, grid):
    definitions = {
        "grid_id": (
            "integer",
            "Stable ID of the 100 m assignment cell; not a building-block ID",
        ),
        "grid_row": ("integer", "Row in the projected regular lattice"),
        "grid_col": ("integer", "Column in the projected regular lattice"),
        "center_x_3003": ("m", "Assignment centre easting, EPSG:3003"),
        "center_y_3003": ("m", "Assignment centre northing, EPSG:3003"),
        "center_lon": ("degrees", "Assignment centre longitude, WGS84"),
        "center_lat": ("degrees", "Assignment centre latitude, WGS84"),
        "fit_eligible": (
            "boolean",
            "Membership of the archived strict-fit population; no new fitting",
        ),
        "edge_support": (
            "boolean",
            "500 m support crosses the municipal boundary; no external GIS halo",
        ),
        "qa_score": (
            "integer",
            "Count of extraction QA flags, separate from the physical domain guard",
        ),
        "qa_reasons": ("text", "Recorded extraction QA reasons"),
        "exclusion_reason": (
            "text",
            "Reason for exclusion from archived strict fitting, if any",
        ),
        "assignment_status": (
            "text",
            "Archived extraction/fitting status; see separate recommendation_status",
        ),
        "building_fraction": (
            "fraction",
            "Unioned footprint area / 250000 m2 support area",
        ),
        "avg_height_m": ("m", "Footprint-area-weighted valid building height"),
        "facade_to_site_ratio": (
            "ratio",
            "Exposed compound perimeter times compound mean height / support area; shared walls excluded",
        ),
        "uwg_tree_cover_fraction": (
            "fraction",
            "Corrected unioned canopy / support area, capped at 1 - building fraction",
        ),
        "uwg_grass_cover_fraction": (
            "fraction",
            "max(mapped green fraction - tree cover, 0), capped at remaining nonbuilt area",
        ),
        "road_fraction": ("fraction", "Unioned mapped street area / support area"),
        "green_pct": (
            "percent",
            "Mapped green polygon union / support area; not tree canopy",
        ),
        "tree_canopy_pct": (
            "percent",
            "Corrected estimated canopy union / support area, before UWG cap",
        ),
        "tree_count": ("integer", "Recorded tree count in support"),
        "tree_density_ha": ("trees/ha", "Recorded tree count / support hectares"),
        "tree_mean_height_m": ("m", "Mean available tree height in support"),
        "building_count": ("integer", "Recorded intersecting building feature count"),
        "height_valid_footprint_frac": (
            "fraction",
            "Share of footprint area with a valid building height",
        ),
        "epw_category": (
            "A-D",
            "Weather category of k7 class, retained even if recommendation withheld",
        ),
        "epw_category_name": (
            "text",
            "Descriptive weather category name; not a formal LCZ classification",
        ),
        "representative_k7_cluster": (
            "integer",
            "Selected fixed-template weather representative class",
        ),
        "representative_grid_id": (
            "integer",
            "Grid ID of the selected weather representative",
        ),
        "epw_filename": (
            "text/null",
            "Candidate download filename; null for unassigned and out-of-domain locations",
        ),
        "release_version": ("text", "Version of these assignments and derived fields"),
        "canopy_area_delta_m2": (
            "m2",
            "Corrected minus archived union canopy area, including GeometryCollection polygons",
        ),
        "canopy_corrected_gt_2p5_m2": (
            "boolean",
            "Absolute canopy-area correction exceeds 2.5 m2",
        ),
        "c6_out_of_domain": (
            "boolean",
            "k7=C6 and unrounded building fraction >= 0.7951808541001185",
        ),
        "epw_recommendation_available": (
            "boolean",
            "False for missing assignment or the diagnosed C6 high-density domain",
        ),
        "recommendation_status": (
            "text",
            "candidate, provisional (edge/QA/distance), out_of_domain, or unassigned",
        ),
    }
    for k in (4, 7, 8):
        definitions.update(
            {
                f"cluster_k{k}_provisional": (
                    "integer/null",
                    f"Corrected nearest-medoid k={k} label using archived scaler and medoid IDs; not a refit",
                ),
                f"cluster_k{k}_label": (
                    "text",
                    "Descriptive morphology name, not formal LCZ",
                ),
                f"distance_to_medoid_k{k}": (
                    "scaled distance",
                    "Euclidean five-feature distance after archived median/IQR scaling, using corrected inputs",
                ),
                f"distance_ratio_p95_k{k}": (
                    "ratio",
                    "Corrected distance / corrected strict-fit class 95th-percentile distance",
                ),
                f"outlier_gt_cluster_p99_k{k}": (
                    "boolean",
                    "Corrected distance exceeds corrected strict-fit class 99th percentile",
                ),
                f"archived_k{k}": (
                    "integer/null",
                    "Unchanged original class label before bounded canopy correction",
                ),
            }
        )
    for field in list(definitions):
        if "archived_" + field in grid:
            unit, definition = definitions[field]
            definitions["archived_" + field] = (
                unit,
                "Frozen v0.1 training/display value before correction: " + definition,
            )
    missing = set(grid.columns) - set(definitions) - {"geometry"}
    if missing:
        raise ValueError(f"Missing field definitions: {missing}")
    with (repo / "data/tables/data_dictionary.csv").open("w", newline="") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(["field", "unit_or_type", "definition"])
        writer.writerows((c, *definitions[c]) for c in grid.columns if c != "geometry")


def describe(path):
    p = Path(path)
    if p.parts[:2] == ("research", "inputs"):
        return "Frozen reconstruction input; historical fields are evidence, not current recommendations."
    if p.parts[:2] == ("research", "evidence"):
        return "Curated scientific diagnostic table; interpretation and populations in research/README.md."
    if p.parts[:3] == ("research", "uwg", "configs"):
        return "Exact annual k7-medoid UWG configuration, indexed and hashed in the run manifest."
    if p.suffix == ".epw":
        return "Annual representative modeled weather; category and hashes in epw_library_manifest.csv."
    if p.parts[:2] == ("data", "configs"):
        return "Exact annual UWG JSON for the named released weather category."
    if p.parts[:2] == ("data", "figures"):
        return "Research figure; corrected maps/profiles and source-relative UHI, with method/selection figures retained."
    if p.parts[:2] == ("assets", "vendor"):
        return "Bundled third-party browser asset; see THIRD_PARTY_NOTICES.md."
    if p.suffix == ".gpkg":
        return "Seven-layer EPSG:3003 GIS package, including canonical grid and named thematic views."
    if p.suffix == ".zip":
        return "Spatial exchange archive; CRS and fields documented in data-guide.md."
    if p.parts[:2] == ("web", "data"):
        return "Browser lookup geometry, metadata or boundary generated from the canonical grid."
    if p.suffix == ".csv":
        return "Tabular research export; field names, units and population identified in data/research guides."
    if p.name == "reproduce_uwg.py":
        return "Pinned UWG 5.3.4 runner with forcing preparation, hashes, resume and heartbeat."
    if p.name == "build_release.py":
        return "Portable reconstruction of assignments, spatial exports, metrics and figures from supplied inputs."
    if p.name == "reproduce_reduction.py":
        return "Exhaustive representative subset search from seven supplied hourly temperature series."
    if p.name == "lookup.py":
        return "Standard-library coordinate lookup with explicit domain and outside-city handling."
    if p.name == "release_docs.py":
        return "Builds complete field dictionary, file catalog and browser-readable guides."
    if p.name == "release_figures.py":
        return "Regenerates corrected maps, profiles and released EPW UHI chart."
    if "test" in p.name or "qa" in p.name or "validat" in p.name:
        return "Automated quality checks, tests or their recorded technical results; not proof of local weather accuracy."
    if p.parts[0] == "docs":
        return "Public user/research documentation or verified desktop/mobile atlas screenshot."
    if p.parts[0] == ".github":
        return (
            "Repository validation and allowlisted GitHub Pages deployment automation."
        )
    return (
        "Repository application, licensing, attribution, dependency, release or contributor metadata: "
        + p.name
    )


def write_catalog(repo):
    files = []
    for p in repo.rglob("*"):
        rel = p.relative_to(repo)
        if (
            p.is_file()
            and not any(s in EXCLUDED for s in rel.parts)
            and p.name != ".DS_Store"
            and p.suffix not in {".pyc", ".log"}
        ):
            files.append(rel.as_posix())
    files = sorted(
        set(files)
        | {
            "validation_report.json",
            "browser_qa_report.json",
            "docs/repository-guide.html",
        }
    )
    intro = (repo / "docs/repository-guide-intro.md").read_text()
    catalog = "\n## Complete File Catalog\n\n| File | Purpose |\n|---|---|\n"
    catalog += "\n".join(f"| `{p}` | {describe(p)} |" for p in files) + "\n"
    (repo / "docs/repository-guide.md").write_text(intro + catalog)
    for name in ["methodology", "data-guide", "repository-guide", "validation"]:
        source = (repo / f"docs/{name}.md").read_text()
        content = markdown.markdown(source, extensions=["tables", "fenced_code", "toc"])
        style = "html,body{height:auto;overflow:auto}main{max-width:960px;margin:auto;padding:32px 24px 60px}h1{font-size:28px}h2{font-size:22px;margin-top:32px}p,li{line-height:1.65}table{border-collapse:collapse;width:100%;table-layout:fixed}td,th{border:1px solid #ccd3cf;padding:10px;vertical-align:top;text-align:left}td,code,a{overflow-wrap:anywhere}pre{overflow:auto;padding:16px;background:#f1f4f2}pre code{overflow-wrap:normal}img{max-width:100%}"
        (repo / f"docs/{name}.html").write_text(
            f'<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(name)} | Torino Urban EPW Atlas</title><link rel="icon" href="data:,"><link rel="stylesheet" href="../assets/styles.css"><style>{style}</style><main><a href="../index.html">Back to atlas</a>{content}</main></html>'
        )


if __name__ == "__main__":
    write_catalog(Path(__file__).resolve().parents[1])
