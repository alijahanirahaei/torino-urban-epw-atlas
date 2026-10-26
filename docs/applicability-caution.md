# Applicability safeguards

The four candidate weather files compress UWG temperature outputs; they are not
validated local weather for every Torino address. No urban station evaluates
the observational accuracy of categories A or B.

Two conservative post hoc safeguards use building fraction in the same original
population of 390 strict-fitting C6 supports. Linear quantiles define the 90th
percentile (approximately 0.755) and the 95th percentile (approximately 0.795).
The exact quantiles are retained in `web/data/metadata.json` and in code.

- At or above the 95th percentile: 20 assigned locations remain restricted;
  coordinate-specific EPW recommendations are withheld.
- From the 90th percentile to below the 95th: 19 assigned locations carry a
  caution flag. Downloads remain available as candidates, not unqualified
  recommendations.
- The other 12,823 assigned locations are outside these two C6 flags. Existing
  edge, data-quality and morphology-distance warnings still apply.
- A further 135 locations lack usable inputs and remain unassigned.

The counts refer to 12,862 assigned locations, not 10,593 fitting supports.
Overlapping support windows are not independent neighbourhoods. Neither threshold
is a validated boundary of physical model accuracy. The restriction was introduced
after an industrial-tail failure and does not turn that failed test into a pass.

For readable prose, the restriction is approximately 0.795. That rounded value
produces the same restricted set in the frozen data; the implementation retains
the exact value. Perturbing the exact restriction by -0.005 or +0.005 produces
22 or 19 restricted locations respectively. This checks assignment sensitivity,
not predictive accuracy at the boundary.

Atlas v0.3.0 preserves all v0.2.0 class assignments, representative identities
and EPW bytes. Supplement v1.1.0 supplies the threshold sensitivity and
per-location flags in its `diagnostics/` directory.
