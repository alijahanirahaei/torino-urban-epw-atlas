# Torino Urban EPW Atlas v0.3.0

This version adds explicit applicability information without changing the four
weather files, exact UWG configurations, morphology classes or representatives.

- Nineteen C6 supports between the original strict-fit 90th and 95th building
  fraction percentiles carry a caution flag. Candidate downloads remain available.
- Twenty C6 supports at or above the 95th percentile remain restricted, and
  135 incomplete locations remain unassigned.
- Browser and command-line lookup, GeoPackage, shapefiles, GeoJSON and CSV
  expose the caution flag consistently. Existing edge and quality flags remain.
- Categories A and B explicitly identify the absence of an urban evaluation
  station. Modelled UHI is not a measured local correction.
- Supplement v1.1.0 accompanies the atlas, with revised figures, readable
  numerical summaries and additional audit tables.

These are conservative post hoc safeguards, not validated physical boundaries.
All 12,997 grid geometries and existing scientific assignments are retained.
The four EPWs and configurations keep their v0.2.0 filenames and hashes.
Software is MIT licensed; derived research outputs are CC BY 4.0. Credit
Ali JahaniRahaei and Giacomo Chiesa and the stated upstream sources.
