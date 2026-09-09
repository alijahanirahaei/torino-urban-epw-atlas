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

Version 0.2.0 additionally checks the revised representative identities, exact
category counts, the seven-layer inventory, every k4/k7/k8 label across spatial
formats, corrected canopy fields, the 20 C6-domain restrictions, missing
download filenames, RH/dew-point/pressure plausibility, Alenia's revised C
assignment and repository-contained source hashes. Unit tests cover missing
inputs, polygon holes and shared boundaries. The subset-search replay is tested
separately. Browser QA checks desktop/mobile layouts, actual loaded map tiles,
restricted and ordinary lookups, errors and download routes.

These are technical and consistency checks. They do not turn modeled weather
into locally validated observations. The scientific caveats in methodology and
the research evidence guide remain applicable after all tests pass.
