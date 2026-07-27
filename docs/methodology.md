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
products. Their cardinalities need not be equal. The four-file result remains a
medoid-level candidate pending stratified within-class UWG sampling.

UHI values shown by the atlas are outputs of the fixed UWG framework relative to
AvMY Caselle. They are not measured local UHI values, calibrated corrections, or
guarantees of point-scale meteorological accuracy.
