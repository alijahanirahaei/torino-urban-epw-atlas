# Method Summary

Torino was sampled with deterministic 100 x 100 m assignment cells. Each cell
center received an overlapping 500 x 500 m morphology support. The assignment cell
answers where a category applies; the larger support supplies the neighborhood
statistics passed to UWG.

Five primary variables were robust-scaled and clustered: building fraction,
area-weighted building height, facade-to-site ratio, UWG tree-cover fraction, and
UWG grass-cover fraction. K-means diagnostics scanned k=2-12. CLARA-style
k-medoids was then used for candidate k=4, k=7, and k=8 solutions. The raw k=7
solution was retained for physical resolution and interpretability.

One annual UWG output was generated for each k=7 medoid using AvMY Caselle as
common forcing. Exhaustive subset selection minimized the maximum hourly dry-bulb
RMSE across represented medoids, followed by the cluster-share-weighted mean
RMSE. Four representatives were retained at the current evidence level.

The adopted common UWG configuration uses version 5.3.4, `charlength=500 m`, DOE
reference zone `4A`, and `flr_h=3.05 m`. All non-morphology assumptions remain
common across categories.

## Interpretation

The seven classes describe morphology; A-D describe reduced modeled weather
products. Their cardinalities need not be equal. Four files are a practical
fidelity/complexity choice, not a uniquely necessary minimum. The final-template
representatives are C1/C2/C4/C6: A=C0+C1, B=C2, C=C3+C4+C5 and D=C6.

UHI values shown by the atlas are outputs of the fixed UWG framework relative to
AvMY Caselle. They are not measured local UHI values, calibrated corrections, or
guarantees of point-scale meteorological accuracy.

## Versioned Canopy Correction

The archive filtered polygonal components inside some GeometryCollections.
Correcting this affects canopy union areas by more than 2.5 m2 in 75 supports.
The original training values, scaler and medoid IDs are retained. Corrected
five-feature vectors are assigned to the fixed medoid identities; there is no
new fit. Two k4 and three k8 labels change, and no k7 labels change. Corrected
distances, class percentiles and profiles are rebuilt together. No meaningful
medoid input change required a UWG rerun.

Tree cover is canopy fraction capped at nonbuilt area. Grass cover is residual
mapped green after subtracting tree cover, capped at remaining nonbuilt area.
Canopy percentage and mapped green percentage are distinct fields and can overlap.

## Evidence And Applicability

105 stratified non-medoid supports give small typical temperature-compression
errors (weighted mean about 0.05 C and weighted P95 about 0.10 C). Stress testing
reveals an industrial tail error up to 1.33 C even relative to its own C6 medoid.
Accordingly, k7=C6 supports with unrounded building fraction at or above
0.7951808541001185 have no location EPW recommendation. There are 20 overlapping
supports at two industrial sites, not 20 independent neighborhoods. The cutoff
is an empirical guard for this setup, not a universal physical threshold.

Classifications have moderate feature/spatial robustness. k4 was strongest on
the statistical ranking; k7 was retained to distinguish useful morphology strata.
k8 is a sensitivity alternative. No manual cluster-island cleanup was adopted.
Buffer-based spatial and HDBSCAN diagnostics are supplied in `research/evidence/`.

Agreement with observed urban weather remains location dependent. The four
station supports map to C (Consolata, Giardini Reali, Alenia) and D (Reiss Romoli);
they do not evaluate A/B. Alenia is at the municipal edge. In the separate 2022
temperature test, annual improvement over Caselle occurred only at Consolata.
No claim of validated morphology-dependent moisture or UDI response is made.

## Reproduction And Precision

`scripts/build_release.py` reconstructs this release from supplied frozen
features and artifacts. `scripts/reproduce_reduction.py` repeats exhaustive
minimax subset selection. `research/uwg/reproduce_uwg.py` reruns the seven exact
annual UWG configurations with separately acquired, hash-checked AvMY Caselle.
See `research/README.md` for the distinction between these reproduction levels
and fresh reconstruction from upstream municipal GIS.

Public files use one-decimal EPW serialization. The three-decimal diagnostics
are supplied separately; the maximum four-file medoid RMSE is respectively
0.05820 and 0.04019 C. Extra serialization digits do not imply weather accuracy.
Temperature-series compression is not equivalence of every EPW variable.

Period summaries use Apr-Sep and Oct-Mar seasons and EPW clock hours 07-18
and 19-06. They are not astronomical day/night definitions. Every displayed UHI
is mean representative dry-bulb temperature minus the common AvMY Caselle source.
