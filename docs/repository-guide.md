# Torino Urban EPW Atlas: Repository, Use, and Maintenance Guide

**Authors:** Ali JahaniRahaei and Giacomo Chiesa

**Release status:** Candidate research release, version 0.1.0

- **Published atlas:** https://alijahanirahaei.github.io/torino-urban-epw-atlas/
- **Source repository:** https://github.com/alijahanirahaei/torino-urban-epw-atlas

This public guide explains how different users should work with the atlas, how
the release is maintained and validated, and what every distributed file does.

## Which Workflow Do I Need?

| User | What to do |
|---|---|
| Architect, planner, or simulation user | Open the published GitHub Pages atlas, query a Torino coordinate, and download the assigned candidate EPW. No installation is needed. |
| UWG user | Query a coordinate and download both the EPW and the braces-icon JSON file containing the exact UWG configuration. |
| GIS or urban-climate researcher | Download the GeoPackage or another spatial distribution and use the morphology, cluster, EPW-category, medoid-distance, edge, and QA fields. |
| Command-line user | Run `python3 scripts/lookup.py LATITUDE LONGITUDE`. No third-party Python packages are required for lookup. |
| Repository maintainer | Serve the site locally, run validation and tests, update source workflows rather than generated files, and push the checked release to `main`. |

## Use the Published Atlas

1. Open the [published atlas](https://alijahanirahaei.github.io/torino-urban-epw-atlas/).
2. Click a Torino location or enter latitude and longitude.
3. Read the assigned A-D candidate weather category and k=4, k=7, and k=8
   morphology classes.
4. Review the 500 m-support morphology values and any edge or QA warning.
5. Select **Download EPW** for the annual candidate weather file.
6. Select the braces icon for the exact UWG JSON configuration.
7. Use the database icon in the header to download the canonical GeoPackage.

The displayed UHI values are UWG-modeled differences from AvMY Caselle, not
measured local UHI or guaranteed point corrections.

## Run the Browser Atlas Locally

The site has no database, backend, build step, or login. It must be served over
HTTP because browser security rules can block `fetch()` requests to local
GeoJSON files when `index.html` is opened with `file://`.

From the repository root:

```bash
python3 -m http.server 8000
```

Then open:

```text
http://localhost:8000
```

Stop the server with `Ctrl+C`.

The equivalent Make target is:

```bash
make serve
```

## Run a Coordinate Lookup Without a Browser

```bash
python3 scripts/lookup.py 45.0757395 7.6785426
```

The result is JSON containing the grid ID, k=4/k=7/k=8 classes, A-D EPW
category, EPW and configuration paths, morphology values, and quality warning.
Use `--compact` for one-line JSON.

## Use the Data in GIS

Open `data/spatial/torino_urban_morphology_epw_atlas.gpkg`. Its layers are:

| Layer | Contents |
|---|---|
| `grid_assignments` | All 12,997 assignment polygons and their morphology, QA, cluster, medoid-distance, and EPW fields. |
| `cluster_medoids` | The 19 medoids across k=4, k=7, and k=8. |
| `city_boundary` | The municipal study boundary used by the extraction. |

The GeoPackage and shapefiles use EPSG:3003. The web GeoJSON uses EPSG:4326.

## Repository Automation

The public repository contains two transparent automation workflows:

- `.github/workflows/validate.yml` runs release validation and coordinate-lookup
  tests on every push and pull request.
- `.github/workflows/pages.yml` repeats those checks before deploying the static
  atlas from `main`; it can also be started manually by a maintainer.

Maintainers of forks can use GitHub Actions as the Pages publishing source. The
workflow relies only on GitHub's scoped Pages permissions and stores no
credentials or access tokens. All application paths are relative, so the atlas
works under a project-site subpath as well as on localhost.

## Validate or Rebuild the Release

End users do not need the packages in `requirements.txt`. Maintainers who need to
validate GIS and EPW contents should run:

```bash
python3 -m pip install -r requirements.txt
python3 scripts/validate_release.py
python3 -m unittest discover -s tests -v
```

For browser QA:

```bash
npm install
python3 -m http.server 8000
```

In another terminal:

```bash
npm run test:browser
```

`scripts/build_release.py` is only for maintainers who have the validated source
artifacts named in `release_manifest.json`. Normal users should not run it. Files
under `data/` and `web/data/` are generated release artifacts and should not be
edited manually.

## Complete File Catalog

Local `.git/`, `node_modules/`, virtual environments, caches, and operating-system
metadata are not release files and are intentionally excluded.

### Root Files

| File | Purpose |
|---|---|
| `.gitattributes` | Declares text line endings and identifies GeoPackage, ZIP, and PNG files as binary. |
| `.gitignore` | Excludes dependencies, credentials, keys, editor state, caches, test artifacts, virtual environments, logs, and macOS metadata. |
| `.nojekyll` | Tells GitHub Pages to serve the static files directly without Jekyll processing. |
| `AUTHORS.md` | Human-readable atlas authorship and citation responsibility. |
| `CHANGELOG.md` | Versioned record of release and documentation changes. |
| `CITATION.cff` | Machine-readable GitHub/Zenodo citation metadata for both authors. |
| `CONTRIBUTING.md` | Rules for proposing changes and regenerating derived outputs. |
| `DATA_LICENSE.md` | CC BY 4.0 scope, required attribution, source credits, and research-output disclaimer. |
| `LICENSE` | MIT license for repository software. |
| `Makefile` | Short commands for serving, validating, testing, and rebuilding. |
| `README.md` | Main project overview, scientific status, use, automation, citation, and license entry point. |
| `THIRD_PARTY_NOTICES.md` | Leaflet, Lucide, OpenStreetMap, and external-service license notices. |
| `browser_qa_report.json` | Latest desktop/mobile browser-test result and measured layout geometry. |
| `checksums.sha256` | SHA-256 hashes for every distributed file under `data/` and `web/data/`. |
| `index.html` | Entry page and semantic structure of the browser atlas. |
| `package.json` | Node metadata and the `test:browser` command. The atlas itself does not need Node. |
| `package-lock.json` | Exact lock for the Playwright browser-QA dependency. |
| `release_manifest.json` | Release version, authors, licenses, source lineage hashes, and expected record counts. |
| `requirements.txt` | Python GIS packages needed only for rebuild and full release validation. |
| `validation_report.json` | Latest result from `scripts/validate_release.py`. |

### GitHub Automation

| File | Purpose |
|---|---|
| `.github/workflows/pages.yml` | Validates and deploys the static atlas to GitHub Pages on `main` or manual dispatch. |
| `.github/workflows/validate.yml` | Runs release validation and Python lookup tests on every push and pull request. |

### Browser Application

| File | Purpose |
|---|---|
| `assets/app.js` | Loads map data, performs point lookup, changes k/EPW layers, populates metrics, and wires downloads and sharing. |
| `assets/styles.css` | Responsive layout, map panel, sidebar, controls, warnings, dialogs, and mobile styles. |
| `assets/vendor/leaflet.css` | Bundled Leaflet map styling for offline-stable application assets. |
| `assets/vendor/leaflet.js` | Bundled Leaflet 1.9.4 map library. |
| `assets/vendor/leaflet-LICENSE.txt` | Leaflet BSD 2-Clause license text. |
| `assets/vendor/lucide.min.js` | Bundled Lucide icon library used by the controls. |
| `assets/vendor/lucide-LICENSE.txt` | Lucide ISC license text. |

### Human Documentation and Screenshots

| File | Purpose |
|---|---|
| `docs/atlas-preview.png` | Verified 1440 x 900 desktop screenshot used in public project documentation. |
| `docs/atlas-mobile.png` | Verified 390 x 844 mobile screenshot used in public project documentation. |
| `docs/data-guide.md` | Markdown guide to formats, fields, downloads, modeled-output scope, and licensing. |
| `docs/data-guide.html` | Browser-readable data guide linked from the atlas footer. |
| `docs/methodology.md` | Markdown summary of supports, clustering, UWG reduction, and interpretation. |
| `docs/methodology.html` | Browser-readable method summary linked from the atlas footer. |
| `docs/repository-guide.md` | This exhaustive public use, maintenance, automation, and file-catalog document. |
| `docs/repository-guide.html` | Concise browser-readable version of this guide linked from the About dialog. |
| `docs/validation.md` | Explanation of automated release checks and release-readiness rule. |

### Maintainer Scripts and Tests

| File | Purpose |
|---|---|
| `scripts/build_release.py` | Rebuilds public spatial data, tables, web payloads, EPWs, configs, metadata, lineage, and checksums from validated source artifacts. |
| `scripts/lookup.py` | Standard-library command-line point-in-polygon lookup returning JSON. |
| `scripts/validate_release.py` | Checks files, authorship metadata, catalog completeness, counts, geometry, CRS, EPWs, configs, checksums, and known locations. |
| `tests/browser_qa.cjs` | Headless-Chrome desktop/mobile functional, download, disclosure, authorship, and layout test. |
| `tests/test_lookup.py` | Python unit tests for known stations and an outside-city coordinate. |

### Compact Web Runtime Data

| File | Purpose |
|---|---|
| `web/data/metadata.json` | Web labels, authors, licenses, colors, category descriptions, filenames, counts, bounds, medoid inputs, and modeled UHI values. |
| `web/data/torino_boundary.geojson` | Lightweight WGS84 municipal outline used by the map. |
| `web/data/torino_lookup.geojson` | Compact WGS84 polygons and abbreviated properties used for browser and CLI lookup. |

### Data Package Overview

| File | Purpose |
|---|---|
| `data/README.md` | Entry point for canonical and convenience data formats and their license. |

### Spatial Data

| File | Purpose |
|---|---|
| `data/spatial/torino_urban_morphology_epw_atlas.gpkg` | Canonical EPSG:3003 GeoPackage with grid assignments, all medoids, and city boundary. |
| `data/spatial/torino_urban_morphology_epw_atlas_wgs84.geojson.zip` | Complete WGS84 GeoJSON distribution for software preferring web coordinates. |
| `data/spatial/torino_clusters_k4_epsg3003.zip` | EPSG:3003 shapefile distribution of k=4 morphology classes. |
| `data/spatial/torino_clusters_k7_epsg3003.zip` | EPSG:3003 shapefile distribution of the retained k=7 morphology classes. |
| `data/spatial/torino_clusters_k8_epsg3003.zip` | EPSG:3003 shapefile distribution of the k=8 sensitivity solution. |
| `data/spatial/torino_epw_categories_epsg3003.zip` | EPSG:3003 shapefile distribution of A-D EPW assignments. |

### UWG Configurations

| File | Purpose |
|---|---|
| `data/configs/category_a_open_lowrise.json` | Exact annual UWG input for category A, open low-rise. |
| `data/configs/category_b_midrise_mixed.json` | Exact annual UWG input for category B, mid-rise mixed. |
| `data/configs/category_c_tall_dense.json` | Exact annual UWG input for category C, tall/dense. |
| `data/configs/category_d_large_footprint.json` | Exact annual UWG input for category D, large-footprint. |

### Candidate EPW Library

| File | Purpose |
|---|---|
| `data/epw/torino_urban_epw_A_open_lowrise_zone4A_flrh305.epw` | Annual candidate EPW for category A. |
| `data/epw/torino_urban_epw_B_midrise_mixed_zone4A_flrh305.epw` | Annual candidate EPW for category B. |
| `data/epw/torino_urban_epw_C_tall_dense_zone4A_flrh305.epw` | Annual candidate EPW for category C. |
| `data/epw/torino_urban_epw_D_large_footprint_zone4A_flrh305.epw` | Annual candidate EPW for category D. |

### Research Figures

| File | Purpose |
|---|---|
| `data/figures/morphology_support_method.png` | Diagram of the 100 m assignment grid and overlapping 500 m morphology support. |
| `data/figures/cluster_selection_diagnostics.png` | k=2-12 cluster-number diagnostic comparison. |
| `data/figures/map_clusters_k4.png` | Citywide k=4 morphology map. |
| `data/figures/map_clusters_k7.png` | Citywide retained k=7 morphology map. |
| `data/figures/map_clusters_k8.png` | Citywide k=8 sensitivity map. |
| `data/figures/cluster_profiles_k4.png` | Robust-scaled morphology profiles for k=4. |
| `data/figures/cluster_profiles_k7.png` | Robust-scaled morphology profiles for k=7. |
| `data/figures/cluster_profiles_k8.png` | Robust-scaled morphology profiles for k=8. |
| `data/figures/epw_uhi_by_period.png` | Annual, seasonal, daytime, and nighttime modeled UHI comparison for A-D. |

### Research Tables

| File | Purpose |
|---|---|
| `data/tables/data_dictionary.csv` | Field definitions, units, and interpretation for the public assignment data. |
| `data/tables/grid_assignments.csv` | Complete 12,997-row non-spatial assignment and morphology table. |
| `data/tables/cluster_medoids_k4_k7_k8.csv` | Medoid records and representative inputs for k=4, k=7, and k=8. |
| `data/tables/cluster_profiles_k4_k7_k8.csv` | Cluster-level morphology summaries and descriptors. |
| `data/tables/cluster_selection_metrics_k2_k12.csv` | Diagnostic metrics for candidate cluster counts k=2-12. |
| `data/tables/epw_library_manifest.csv` | A-D representatives, file paths, hashes, common UWG settings, and source classes. |
| `data/tables/epw_period_metrics.csv` | Annual, winter, summer, daytime, and nighttime modeled metrics for the library. |

## Licensing and Citation

Repository software is MIT licensed. Derived spatial data, tables, figures, UWG
configurations, and generated EPWs are CC BY 4.0. Reuse must credit **Ali
JahaniRahaei and Giacomo Chiesa**, link to the license, and identify changes. See
`DATA_LICENSE.md`, `CITATION.cff`, and `THIRD_PARTY_NOTICES.md` before
redistribution.
