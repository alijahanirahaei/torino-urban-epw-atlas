# Data Package

The canonical distribution is
`spatial/torino_urban_morphology_epw_atlas.gpkg` in EPSG:3003. It contains:

- `grid_assignments`: 12,997 assignment polygons and morphology/cluster/EPW fields;
- `cluster_medoids`: the 19 medoids across k=4, k=7, and k=8; and
- `city_boundary`: the exact municipal study boundary.

Convenience distributions include:

- one zipped WGS84 GeoJSON containing the complete grid table;
- separate EPSG:3003 zipped shapefiles for k=4, k=7, k=8, and EPW A-D;
- `tables/grid_assignments.csv` without geometry; and
- the compact WGS84 GeoJSON used by the browser in `../web/data/`.

The derived spatial data, tables, figures, exact UWG JSON configurations, and
generated candidate EPWs are distributed under CC BY 4.0 with the attribution
and source notices in `../DATA_LICENSE.md`. The repository software is separately
licensed under MIT.

The raw CLARA labels are published. Suggested isolated-component cleanup labels
were not applied. Rows that did not enter clustering retain provisional or blank
assignments as documented by `assignment_status`, `edge_support`, and QA fields.

Definitions are in `tables/data_dictionary.csv`. File integrity can be verified
against `../checksums.sha256`.
