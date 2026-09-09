# Data Guide

## Recommended Formats

- Use the GeoPackage for QGIS, ArcGIS Pro, Python, and other modern GIS software.
- Use the zipped shapefiles for software requiring the legacy ESRI format.
- Use the CSV when geometry is unnecessary.
- Use the WGS84 GeoJSON for web mapping.

The GeoPackage and shapefiles use EPSG:3003 to preserve the 100 m metric grid. The
GeoJSON and browser lookup use EPSG:4326.

## Assignment Fields

- `cluster_k4_provisional`, `cluster_k7_provisional`, and
  `cluster_k8_provisional` are corrected fixed-medoid morphology labels, not a new fit.
- `epw_category` is the reduced A-D weather category derived from the k=7 medoid
  weather outputs.
- `epw_filename` identifies the candidate annual EPW, or is null when withheld.
- `recommendation_status` is candidate, provisional, out_of_domain or unassigned.
- `epw_recommendation_available` is false for the 20 C6-domain exclusions and
  135 incomplete-feature locations. Retained category labels are not approval.
- `fit_eligible` indicates whether the row entered model fitting.
- `edge_support` marks 500 m supports extending beyond the municipal GIS.
- `qa_score` and `qa_reasons` expose data-quality conditions.
- `distance_to_medoid_k7` measures morphology distance in robust-scaled input
  space; `outlier_gt_cluster_p99_k7` flags extreme class members. Both use
  corrected inputs and corrected strict-fit class distance percentiles.
- `archived_*` fields retain original values/labels, while displayed canopy and
  UWG tree/grass fields include the bounded correction described in methodology.

See `data/tables/data_dictionary.csv` for definitions and units.

## GeoPackage Layers

| Layer | Records | Purpose |
|---|---:|---|
| grid_assignments | 12,997 | Canonical full attributes, corrected features and domain flags |
| cluster_medoids | 19 | Medoids for k4, k7 and k8; corrected display metrics |
| city_boundary | 1 | Exact municipal study boundary |
| morphology_k4 | 12,997 | Convenient k4 thematic view |
| morphology_k7 | 12,997 | Convenient k7 thematic view |
| morphology_k8 | 12,997 | Convenient k8 thematic view |
| weather_categories | 12,997 | Weather assignments and recommendation availability |

In QGIS, open the GeoPackage and select the desired layers; they are not separate
files. In Python:

```python
import geopandas as gpd
import pyogrio
path = "data/spatial/torino_urban_morphology_epw_atlas.gpkg"
print(pyogrio.list_layers(path))
grid = gpd.read_file(path, layer="grid_assignments")
k7 = gpd.read_file(path, layer="morphology_k7")
```

Shapefile equivalents abbreviate fields: GRID_ID, CLUSTER/LABEL or EPW_CAT,
EPW_FILE, REC_STATUS, EPW_AVAIL, OUT_DOMAIN, EDGE and QA_SCORE. Preserve these
flags in downstream analyses. The four-file library remains available for expert
inspection, but a withheld location has no recommended filename in any format.

## Coordinate Lookup

The web application performs point-in-polygon lookup against the 100 m assignment
geometry. The CLI equivalent is:

```bash
python3 scripts/lookup.py LATITUDE LONGITUDE
```

Coordinates outside a published assignment polygon are not silently snapped to a
neighboring cell.
Municipal coverage is checked first. On a shared assignment boundary the first
covering grid in ascending grid-ID order is selected. Polygon holes are excluded.

## Weather And Configuration Downloads

Each A-D category links to one annual candidate EPW and the exact UWG JSON
configuration used to generate it. The EPW is a modeled research output, not a
measured local weather record. Displayed UHI values are UWG-simulated differences
from AvMY Caselle and may differ from observations at the queried location.

## License

Repository code is MIT licensed. Derived spatial data, tables, figures, UWG
configurations, and generated EPWs are available under CC BY 4.0. Reuse and
adaptation require attribution, a link to the license, and an indication of any
changes; see `DATA_LICENSE.md` for the recommended credit and source notices.
