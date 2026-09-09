# Use, data, and repository structure

**Authors: Ali JahaniRahaei and Giacomo Chiesa.**

The [published atlas](https://alijahanirahaei.github.io/torino-urban-epw-atlas/)
needs no installation. Enter a location, inspect its morphology and applicability
flags, and download its candidate EPW and exact UWG JSON when available.
This is modeled weather, not a measurement or certified local correction.

## Run Locally

Download or clone the public repository, open a terminal in its root, then run:

```bash
python3 -m http.server 8000
```

Open `http://localhost:8000`; stop with Ctrl+C. No database or backend is needed.
Only basemap tiles require an external service. Avoid opening index.html as a
file URL because browsers restrict local data loading.

The Python standard-library equivalent is:

```bash
python3 scripts/lookup.py 45.0757395 7.6785426
```

## Research Downloads

The [GeoPackage](../data/spatial/torino_urban_morphology_epw_atlas.gpkg) contains
seven named layers. Open `morphology_k4`, `morphology_k7`, `morphology_k8` or
`weather_categories` for convenient thematic maps, and `grid_assignments` for
the full canonical attributes. See [data-guide.md](data-guide.md).

Four exact JSON/EPW pairs, shapefiles, CSV, GeoJSON, field definitions and figures
are listed below. The [research guide](../research/README.md) describes supplied
scientific evidence, portable reconstruction and the limits of reproducibility.

## Repository Automation

GitHub Actions validates pull requests and validates `main` before deploying
GitHub Pages. The site is staged from an explicit public-file allowlist; local
environments, Git internals and research execution logs are never staged.
Contributors can fork the repository and configure Pages to use GitHub Actions.
No deployment token needs to be embedded in this project.

## Attribution

Code is MIT licensed. Derived research outputs are CC BY 4.0 with attribution to
both authors and the stated upstream sources. See [DATA_LICENSE.md](../DATA_LICENSE.md)
and [THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md). The source weather DOI is
not an atlas DOI; no atlas archival identifier is claimed until one is issued.

## Complete File Catalog

| File | Purpose |
|---|---|
| `.gitattributes` | Repository application, licensing, attribution, dependency, release or contributor metadata: .gitattributes |
| `.github/workflows/pages.yml` | Repository validation and allowlisted GitHub Pages deployment automation. |
| `.github/workflows/release.yml` | Repository validation and allowlisted GitHub Pages deployment automation. |
| `.github/workflows/validate.yml` | Automated quality checks, tests or their recorded technical results; not proof of local weather accuracy. |
| `.gitignore` | Repository application, licensing, attribution, dependency, release or contributor metadata: .gitignore |
| `.nojekyll` | Repository application, licensing, attribution, dependency, release or contributor metadata: .nojekyll |
| `AUTHORS.md` | Repository application, licensing, attribution, dependency, release or contributor metadata: AUTHORS.md |
| `CHANGELOG.md` | Repository application, licensing, attribution, dependency, release or contributor metadata: CHANGELOG.md |
| `CITATION.cff` | Repository application, licensing, attribution, dependency, release or contributor metadata: CITATION.cff |
| `CONTRIBUTING.md` | Repository application, licensing, attribution, dependency, release or contributor metadata: CONTRIBUTING.md |
| `DATA_LICENSE.md` | Repository application, licensing, attribution, dependency, release or contributor metadata: DATA_LICENSE.md |
| `LICENSE` | Repository application, licensing, attribution, dependency, release or contributor metadata: LICENSE |
| `Makefile` | Repository application, licensing, attribution, dependency, release or contributor metadata: Makefile |
| `README.md` | Repository application, licensing, attribution, dependency, release or contributor metadata: README.md |
| `THIRD_PARTY_NOTICES.md` | Repository application, licensing, attribution, dependency, release or contributor metadata: THIRD_PARTY_NOTICES.md |
| `assets/app.js` | Repository application, licensing, attribution, dependency, release or contributor metadata: app.js |
| `assets/styles.css` | Repository application, licensing, attribution, dependency, release or contributor metadata: styles.css |
| `assets/vendor/leaflet-LICENSE.txt` | Bundled third-party browser asset; see THIRD_PARTY_NOTICES.md. |
| `assets/vendor/leaflet.css` | Bundled third-party browser asset; see THIRD_PARTY_NOTICES.md. |
| `assets/vendor/leaflet.js` | Bundled third-party browser asset; see THIRD_PARTY_NOTICES.md. |
| `assets/vendor/lucide-LICENSE.txt` | Bundled third-party browser asset; see THIRD_PARTY_NOTICES.md. |
| `assets/vendor/lucide.min.js` | Bundled third-party browser asset; see THIRD_PARTY_NOTICES.md. |
| `browser_qa_report.json` | Automated quality checks, tests or their recorded technical results; not proof of local weather accuracy. |
| `checksums.sha256` | Repository application, licensing, attribution, dependency, release or contributor metadata: checksums.sha256 |
| `data/README.md` | Repository application, licensing, attribution, dependency, release or contributor metadata: README.md |
| `data/configs/category_a_v0.2.0.json` | Exact annual UWG JSON for the named released weather category. |
| `data/configs/category_b_v0.2.0.json` | Exact annual UWG JSON for the named released weather category. |
| `data/configs/category_c_v0.2.0.json` | Exact annual UWG JSON for the named released weather category. |
| `data/configs/category_d_v0.2.0.json` | Exact annual UWG JSON for the named released weather category. |
| `data/epw/torino_urban_epw_A_v0.2.0.epw` | Annual representative modeled weather; category and hashes in epw_library_manifest.csv. |
| `data/epw/torino_urban_epw_B_v0.2.0.epw` | Annual representative modeled weather; category and hashes in epw_library_manifest.csv. |
| `data/epw/torino_urban_epw_C_v0.2.0.epw` | Annual representative modeled weather; category and hashes in epw_library_manifest.csv. |
| `data/epw/torino_urban_epw_D_v0.2.0.epw` | Annual representative modeled weather; category and hashes in epw_library_manifest.csv. |
| `data/figures/cluster_profiles_k4.png` | Research figure; corrected maps/profiles and source-relative UHI, with method/selection figures retained. |
| `data/figures/cluster_profiles_k7.png` | Research figure; corrected maps/profiles and source-relative UHI, with method/selection figures retained. |
| `data/figures/cluster_profiles_k8.png` | Research figure; corrected maps/profiles and source-relative UHI, with method/selection figures retained. |
| `data/figures/cluster_selection_diagnostics.png` | Research figure; corrected maps/profiles and source-relative UHI, with method/selection figures retained. |
| `data/figures/epw_uhi_by_period.png` | Research figure; corrected maps/profiles and source-relative UHI, with method/selection figures retained. |
| `data/figures/map_clusters_k4.png` | Research figure; corrected maps/profiles and source-relative UHI, with method/selection figures retained. |
| `data/figures/map_clusters_k7.png` | Research figure; corrected maps/profiles and source-relative UHI, with method/selection figures retained. |
| `data/figures/map_clusters_k8.png` | Research figure; corrected maps/profiles and source-relative UHI, with method/selection figures retained. |
| `data/figures/morphology_support_method.png` | Research figure; corrected maps/profiles and source-relative UHI, with method/selection figures retained. |
| `data/spatial/torino_clusters_k4_epsg3003.zip` | Spatial exchange archive; CRS and fields documented in data-guide.md. |
| `data/spatial/torino_clusters_k7_epsg3003.zip` | Spatial exchange archive; CRS and fields documented in data-guide.md. |
| `data/spatial/torino_clusters_k8_epsg3003.zip` | Spatial exchange archive; CRS and fields documented in data-guide.md. |
| `data/spatial/torino_epw_categories_epsg3003.zip` | Spatial exchange archive; CRS and fields documented in data-guide.md. |
| `data/spatial/torino_urban_morphology_epw_atlas.gpkg` | Seven-layer EPSG:3003 GIS package, including canonical grid and named thematic views. |
| `data/spatial/torino_urban_morphology_epw_atlas_wgs84.geojson.zip` | Spatial exchange archive; CRS and fields documented in data-guide.md. |
| `data/tables/cluster_medoids_k4_k7_k8.csv` | Tabular research export; field names, units and population identified in data/research guides. |
| `data/tables/cluster_profiles_k4_k7_k8.csv` | Tabular research export; field names, units and population identified in data/research guides. |
| `data/tables/cluster_selection_metrics_k2_k12.csv` | Tabular research export; field names, units and population identified in data/research guides. |
| `data/tables/corrected_distance_thresholds.csv` | Tabular research export; field names, units and population identified in data/research guides. |
| `data/tables/data_dictionary.csv` | Tabular research export; field names, units and population identified in data/research guides. |
| `data/tables/epw_library_manifest.csv` | Tabular research export; field names, units and population identified in data/research guides. |
| `data/tables/epw_period_metrics.csv` | Tabular research export; field names, units and population identified in data/research guides. |
| `data/tables/grid_assignments.csv` | Tabular research export; field names, units and population identified in data/research guides. |
| `docs/atlas-mobile.png` | Public user/research documentation or verified desktop/mobile atlas screenshot. |
| `docs/atlas-preview.png` | Public user/research documentation or verified desktop/mobile atlas screenshot. |
| `docs/data-guide.html` | Public user/research documentation or verified desktop/mobile atlas screenshot. |
| `docs/data-guide.md` | Public user/research documentation or verified desktop/mobile atlas screenshot. |
| `docs/methodology.html` | Public user/research documentation or verified desktop/mobile atlas screenshot. |
| `docs/methodology.md` | Public user/research documentation or verified desktop/mobile atlas screenshot. |
| `docs/release-notes-v0.2.0.md` | Public user/research documentation or verified desktop/mobile atlas screenshot. |
| `docs/repository-guide-intro.md` | Public user/research documentation or verified desktop/mobile atlas screenshot. |
| `docs/repository-guide.html` | Public user/research documentation or verified desktop/mobile atlas screenshot. |
| `docs/repository-guide.md` | Public user/research documentation or verified desktop/mobile atlas screenshot. |
| `docs/validation.html` | Automated quality checks, tests or their recorded technical results; not proof of local weather accuracy. |
| `docs/validation.md` | Automated quality checks, tests or their recorded technical results; not proof of local weather accuracy. |
| `index.html` | Repository application, licensing, attribution, dependency, release or contributor metadata: index.html |
| `package-lock.json` | Repository application, licensing, attribution, dependency, release or contributor metadata: package-lock.json |
| `package.json` | Repository application, licensing, attribution, dependency, release or contributor metadata: package.json |
| `release_manifest.json` | Repository application, licensing, attribution, dependency, release or contributor metadata: release_manifest.json |
| `requirements.txt` | Repository application, licensing, attribution, dependency, release or contributor metadata: requirements.txt |
| `research/README.md` | Repository application, licensing, attribution, dependency, release or contributor metadata: README.md |
| `research/evidence/buffered_spatial_stability.csv` | Curated scientific diagnostic table; interpretation and populations in research/README.md. |
| `research/evidence/feature_sensitivity.csv` | Curated scientific diagnostic table; interpretation and populations in research/README.md. |
| `research/evidence/hdbscan_sweep.csv` | Curated scientific diagnostic table; interpretation and populations in research/README.md. |
| `research/evidence/nonmedoid_annual_results.csv` | Curated scientific diagnostic table; interpretation and populations in research/README.md. |
| `research/evidence/nonmedoid_sampling.csv` | Curated scientific diagnostic table; interpretation and populations in research/README.md. |
| `research/evidence/nonmedoid_weighted_summary.csv` | Curated scientific diagnostic table; interpretation and populations in research/README.md. |
| `research/inputs/archived_atlas_v0.1.gpkg.zip` | Frozen reconstruction input; historical fields are evidence, not current recommendations. |
| `research/inputs/candidate_cluster_descriptors.csv` | Frozen reconstruction input; historical fields are evidence, not current recommendations. |
| `research/inputs/canopy_corrected_fixed_assignments.csv` | Frozen reconstruction input; historical fields are evidence, not current recommendations. |
| `research/inputs/diagnostic_corrected_features.csv` | Frozen reconstruction input; historical fields are evidence, not current recommendations. |
| `research/inputs/k7_hourly_temperature_precision3.csv.gz` | Frozen reconstruction input; historical fields are evidence, not current recommendations. |
| `research/inputs/library_provenance.csv` | Frozen reconstruction input; historical fields are evidence, not current recommendations. |
| `research/inputs/robust_scale_stats.csv` | Frozen reconstruction input; historical fields are evidence, not current recommendations. |
| `research/uwg/configs/k7_cluster_00_grid_12618.json` | Exact annual k7-medoid UWG configuration, indexed and hashed in the run manifest. |
| `research/uwg/configs/k7_cluster_01_grid_3788.json` | Exact annual k7-medoid UWG configuration, indexed and hashed in the run manifest. |
| `research/uwg/configs/k7_cluster_02_grid_10026.json` | Exact annual k7-medoid UWG configuration, indexed and hashed in the run manifest. |
| `research/uwg/configs/k7_cluster_03_grid_10925.json` | Exact annual k7-medoid UWG configuration, indexed and hashed in the run manifest. |
| `research/uwg/configs/k7_cluster_04_grid_5210.json` | Exact annual k7-medoid UWG configuration, indexed and hashed in the run manifest. |
| `research/uwg/configs/k7_cluster_05_grid_4849.json` | Exact annual k7-medoid UWG configuration, indexed and hashed in the run manifest. |
| `research/uwg/configs/k7_cluster_06_grid_1524.json` | Exact annual k7-medoid UWG configuration, indexed and hashed in the run manifest. |
| `research/uwg/reproduce_uwg.py` | Pinned UWG 5.3.4 runner with forcing preparation, hashes, resume and heartbeat. |
| `research/uwg/run_manifest.csv` | Tabular research export; field names, units and population identified in data/research guides. |
| `scripts/build_release.py` | Portable reconstruction of assignments, spatial exports, metrics and figures from supplied inputs. |
| `scripts/lookup.py` | Standard-library coordinate lookup with explicit domain and outside-city handling. |
| `scripts/release_docs.py` | Builds complete field dictionary, file catalog and browser-readable guides. |
| `scripts/release_figures.py` | Regenerates corrected maps, profiles and released EPW UHI chart. |
| `scripts/reproduce_reduction.py` | Exhaustive representative subset search from seven supplied hourly temperature series. |
| `scripts/stage_site.py` | Repository application, licensing, attribution, dependency, release or contributor metadata: stage_site.py |
| `scripts/validate_release.py` | Automated quality checks, tests or their recorded technical results; not proof of local weather accuracy. |
| `tests/browser_qa.cjs` | Automated quality checks, tests or their recorded technical results; not proof of local weather accuracy. |
| `tests/test_lookup.py` | Automated quality checks, tests or their recorded technical results; not proof of local weather accuracy. |
| `tests/test_release_science.py` | Automated quality checks, tests or their recorded technical results; not proof of local weather accuracy. |
| `validation_report.json` | Automated quality checks, tests or their recorded technical results; not proof of local weather accuracy. |
| `web/data/metadata.json` | Browser lookup geometry, metadata or boundary generated from the canonical grid. |
| `web/data/torino_boundary.geojson` | Browser lookup geometry, metadata or boundary generated from the canonical grid. |
| `web/data/torino_lookup.geojson` | Browser lookup geometry, metadata or boundary generated from the canonical grid. |
