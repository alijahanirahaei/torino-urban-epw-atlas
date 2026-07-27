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
  `cluster_k8_provisional` are raw candidate morphology labels.
- `epw_category` is the reduced A-D weather category derived from the k=7 medoid
  weather outputs.
- `epw_filename` identifies the candidate annual EPW.
- `fit_eligible` indicates whether the row entered model fitting.
- `edge_support` marks 500 m supports extending beyond the municipal GIS.
- `qa_score` and `qa_reasons` expose data-quality conditions.
- `distance_to_medoid_k7` measures morphology distance in robust-scaled input
  space; `outlier_gt_cluster_p99_k7` flags extreme class members.

See `data/tables/data_dictionary.csv` for definitions and units.

## Coordinate Lookup

The web application performs point-in-polygon lookup against the 100 m assignment
geometry. The CLI equivalent is:

```bash
python3 scripts/lookup.py LATITUDE LONGITUDE
```

Coordinates outside a published assignment polygon are not silently snapped to a
neighboring cell.

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
