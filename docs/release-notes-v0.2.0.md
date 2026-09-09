# Torino Urban EPW Atlas v0.2.0

By Ali JahaniRahaei and Giacomo Chiesa.

Updated research release: fixed-template C1/C2/C4/C6 representatives; weather
categories A=C0+C1, B=C2, C=C3+C4+C5, D=C6. Category B/C files and 2,445 C3
assignments are updated. Canopy correction changes two k4 and three k8 labels,
but no k7 labels. Original training/scaler/medoid identities are retained.

The seven-layer GeoPackage includes canonical grid, medoids, city boundary and
named k4/k7/k8/weather views. CSV, GeoJSON, shapefiles, configuration manifests,
plots and browser metadata are rebuilt consistently. Portable fixed-classifier
reconstruction, seven-medoid weather reduction, exact annual UWG configurations,
a hash-checked UWG runner and curated scientific evidence are included.

**Applicability:** modeled weather is not measured local weather. Location EPW
recommendations are withheld for 20 diagnosed high-density C6 supports and 135
incomplete assignments. Other edge/QA/outlier results remain provisional. Four
files are a practical compromise, not a unique minimum or a local accuracy guarantee.

Public EPWs use one-decimal serialization. Three-decimal temperature diagnostics
are supplied separately for reproducibility, not as a claim of greater accuracy.

Code: MIT. Stated derived data: CC BY 4.0, subject to source notices. No atlas DOI
is claimed yet; the cited source-weather DOI identifies a different dataset.
