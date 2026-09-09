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
