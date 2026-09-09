# Reproducibility And Evidence

This directory contains versioned inputs, configurations and evidence supporting
the atlas. Derived data are CC BY 4.0; code is MIT licensed.
Credit Ali JahaniRahaei and Giacomo Chiesa, together with the upstream sources.

## Reproduction Levels

1. **Use:** serve the static atlas or query coordinates without GIS/UWG installs.
2. **Rebuild from supplied features:** install `requirements.txt`, then run
   `python3 scripts/build_release.py` and `python3 scripts/validate_release.py`.
   This recomputes corrected nearest-medoid assignments, distance flags, profiles,
   all spatial exports, released-EPW period summaries and related figures.
3. **Repeat weather reduction:** run `python3 scripts/reproduce_reduction.py --check`.
   The bundled gzip CSV contains all 8,760 hourly temperatures for seven medoids
   at three-decimal serialization, plus Caselle temperatures and calendar fields.
4. **Repeat UWG:** acquire the source EPW using the dataset DOI below, install
   `uwg==5.3.4` in Python 3.10 or later, and use the exact runner/configurations.

```bash
python3 -m pip install uwg==5.3.4
python3 research/uwg/reproduce_uwg.py --forcing path/to/AvMY_CASELLE.epw --output ../uwg-reproduction --jobs C1,C2,C4,C6 --check-only
python3 research/uwg/reproduce_uwg.py --forcing path/to/AvMY_CASELLE.epw --output ../uwg-reproduction --jobs C1,C2,C4,C6 --workers 4
```

Omit `--jobs` to run all seven medoids. The runner refuses an unexpected UWG
version, forcing hash or configuration hash. It produces both one- and
three-decimal outputs, exact-match checks, a resumable ledger, logs and
`heartbeat.json` every 30 seconds. Outputs must be outside the immutable UWG
package. This is an annual simulation, not a fast browser calculation.

**Not claimed:** the repository does not reconstruct the original upstream GIS
extraction, CLARA-style fitting, all refit experiments or all station/uncertainty
analyses from raw observations. The supplied immutable feature/classifier archive
enables fixed-classifier reproduction, not a fresh fit. Original 250/500/1000 m
support and shifting experiments are methodological evidence, not automatic
choices recomputed by the browser. CAD/Grasshopper/Dragonfly imports are untested.

## Source Acquisition And Preparation

- Weather: [Torino-EPW dataset](https://doi.org/10.5281/zenodo.14905721),
  documented by [JahaniRahaei, Milelli and Chiesa (2025)](https://doi.org/10.1016/j.dib.2025.111708).
  Obtain `AvMY_CASELLE.epw`; original license CC BY 4.0.
- Municipal buildings/heights, roads, green polygons and tree inventory came
  from the Citta di Torino Geoportal. Consult the
  [municipal portal](https://geoportale.comune.torino.it/) and
  [source notices](../THIRD_PARTY_NOTICES.md). Live municipal layers may change;
  the release's frozen derived archive, not a current download, defines its inputs.
- Raw AvMY pressure is in hPa. Only EPW field 10 (zero-based index 9) is converted
  to Pa by multiplying by 100. Every other source field is unchanged.
- Raw SHA-256: `3430967c3faa30aa3512a34c8fb636003458f162b50c2d2b5ded70707f76a71a`.
- Prepared SHA-256: `39c5c8cb90b39fefdfb531ade96700e9436d4df9c8fca3a57191f820d135e5a9`.
- The UWG 5.3.4 writer's duplicated final field is removed only when the final
  two fields are equal. Unknown schema differences are errors, not silently fixed.

## Frozen Inputs

`inputs/archived_atlas_v0.1.gpkg.zip` is an immutable historical classifier/input
archive. Its old EPW assignments are **superseded and not recommendations**.
It supplies geometry, the archived training feature values, strict-fit membership
and 19 medoid IDs. `robust_scale_stats.csv` contains the original five medians/IQRs.
`canopy_corrected_fixed_assignments.csv` records old/new canopy features and class
labels; `diagnostic_corrected_features.csv` is the independent five-feature replay
target. `library_provenance.csv` identifies exact current JSON/EPW pairs.

`uwg/run_manifest.csv` indexes seven jobs, cluster shares and configuration/output
hashes. The fixed common setup uses Zone4A, floor height3.05 m, charlength500 m,
h_mix1 and sensanth20 W/m2 schedule amplitude. No local traffic inventory is
inferred from roads or morphology. Common non-morphology assumptions remain an
important source of uncertainty; representative labels are not local calibrations.

## Diagnostic Tables

- `nonmedoid_sampling.csv`: frozen sampling roles, morphology, strata and weights.
  105 stratified supports and additional deliberate stress cases are distinct.
  The historical `inclusion_probability` field is a nominal stratum sampling
  fraction, not an exact inclusion probability after spatial selection constraints.
  `within_cluster_weight` and `citywide_nonmedoid_weight` are post-stratification
  analysis weights. Stress cases do not enter the weighted city summary.
- `nonmedoid_annual_results.csv`: selected support versus its class medoid,
  assigned four-file representative, and oracle representative. Precision1 and
  precision3 columns are explicitly distinguished. Oracle comparisons diagnose
  representational error; the atlas cannot choose the oracle without simulating.
- `nonmedoid_weighted_summary.csv`: period/variable/comparator/population-specific
  support RMSE summaries. Weighted mean of support RMSE differs from pooled-hourly
  RMSE. Retain the population and comparator columns when quoting values.
- `hdbscan_sweep.csv`: 12 density-clustering settings; coverage/noise, agreement
  and C6 recovery. This is a robustness diagnostic, not the adopted classifier.
- `buffered_spatial_stability.csv`: spatial holdout summaries by k and buffered/
  unbuffered arm. Overlapping 500 m supports require spatial separation.
- `feature_sensitivity.csv`: feature-set perturbations and C6 recovery. These
  are alternatives for sensitivity assessment, not revised atlas assignments.

These tables preserve their frozen experiment definitions. Current release
display distances/profiles are recomputed with the bounded canopy correction;
experimental results are not silently refitted or recalculated on a different model.

## Interpretation

Temperature-compression fidelity is not observed-weather accuracy, full-EPW
equivalence, an LCZ classification, or validation for every microclimate process.
The high-density C6 warning is a diagnosed common-stock limitation. Below its
cutoff does not mean validated. The four files are a pragmatic compromise; the
0.1 C medoid tolerance alone does not uniquely require four files.

The atlas version DOI is not yet assigned. The weather dataset DOI above must
not be cited as the DOI of this atlas.
