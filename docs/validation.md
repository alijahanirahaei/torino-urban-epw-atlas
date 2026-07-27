# Release Validation

`scripts/validate_release.py` checks:

- required repository files;
- 12,997-row agreement among metadata, CSV, GeoPackage, and web GeoJSON;
- GeoPackage layers, CRS, geometry validity, and unique identifiers;
- zipped shapefile components;
- EPW dimensions, 35-field weather rows, and SHA-256 hashes;
- accepted `zone`, `flr_h`, and `charlength` JSON values;
- every distributed checksum;
- known coordinate assignments for Consolata, Giardini Reali, Alenia, and Reiss
  Romoli; and
- absence of private absolute filesystem paths;
- absence of repository placeholders, common secret patterns, sensitive key or
  environment files, unsafe archive members, and unignored local dependencies;
- presence of Ali JahaniRahaei and Giacomo Chiesa in citation, attribution, web,
  and release metadata; and
- complete file-by-file coverage in `docs/repository-guide.md`.

The report is written to `validation_report.json`. A public release should be made
only when its status is `PASS`.
