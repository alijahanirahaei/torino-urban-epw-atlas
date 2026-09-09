# Changelog

## 0.2.0 - 2026-09-09

- Updated fixed-template representatives to C1/C2/C4/C6; reassigned morphology
  C3 to weather C. Alenia now receives C, subject to its existing edge warning.
- Withheld location recommendations for the diagnosed 20-support C6 density
  tail; retained category labels and expert-access raw files.
- Corrected canopy-dependent fields, two k4 and three k8 fixed assignments;
  retained the original scaler, medoid identities and archived fields.
- Rebuilt all spatial formats, profiles, distances, UHI summaries and figures.
- Added named morphology and weather layers to the seven-layer GeoPackage.
- Added portable release reconstruction, reduction reproduction, seven exact
  UWG configurations, a reusable runner and curated validation evidence.
- Updated public guides, authorship/citation version, tests, map rendering and
  allowlisted GitHub Pages deployment. No change to the shared UWG physics setup.

The previous prototype is preserved in Git history at commit `9fac500` and in
the `v0.1.0` tag. Its assignments are superseded, not deleted from the record.

## Unreleased - 2026-07-27

- Added an explicit asterisk and disclosure stating that displayed UHI values are
  UWG-modeled differences from AvMY Caselle, not measured local UHI.
- Made the CC BY 4.0 license for derived data, figures, UWG configurations, and
  generated EPWs visible in the application and expanded the attribution guide.
- Extended browser QA to verify the disclosure, data-license page, candidate EPW
  download, and exact UWG JSON-configuration download at desktop and mobile sizes.
- Regenerated the desktop and mobile interface screenshots used by the public
  project documentation.
- Added Giacomo Chiesa as an atlas author in the About dialog, authors file,
  citation metadata, software copyright, data attribution, release manifest, web
  metadata, and reproducible build script.
- Added complete local-use, repository automation, maintenance, and
  file-by-file repository documentation in `docs/repository-guide.md` and its
  browser-readable HTML companion.
- Gated GitHub Pages deployment on release validation and added automated checks
  for authorship consistency and file-catalog completeness.
- Added a publication-safety audit for ignored dependencies, sensitive file
  types, private filesystem paths, repository placeholders, and archive members.
- Removed one-time repository bootstrap instructions from public documentation
  and aligned OpenStreetMap tile requests with the current service policy.

## 0.1.0 - 2026-07-23

- Added 12,997-location morphology and EPW assignment atlas.
- Added candidate k=4, k=7, and k=8 classification layers.
- Added four accepted Zone 4A / 3.05 m-floor-height annual UWG EPWs.
- Added GeoPackage, zipped GeoJSON, zipped shapefile, and CSV distributions.
- Added browser and command-line coordinate lookup.
- Added source lineage, SHA-256 checksums, release validation, and known-station tests.
- Marked municipal-edge supports, morphology outliers, and unassigned locations.
