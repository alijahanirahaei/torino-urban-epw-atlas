# Additional diagnostic tables

These files document the interpretation of existing experiments. No additional
weather simulations or classifier fits were performed for this package version.
CSV and JSON values retain computational precision; rounded summaries appear
in the supplementary document. Additional digits do not imply physical accuracy.

- `scale_estimands_reconciled.csv`: total, within-class and between-class
  weighted variances at 250, 500 and 1000 m, for the same 304 quality-qualified
  probability-sample centres and design weights. Height variances are in m2;
  facade/site variances are squared ratios. Class labels are fixed at 500 m.
  Reductions are percentages relative to 250 m. This supplements Table S8;
  it does not replace its original values.
- `c6_threshold_sensitivity.csv`: changes in restriction counts when the
  strict-fitting C6 95th-percentile threshold is rounded or perturbed. Added and
  removed grid IDs are semicolon-separated. These are sensitivity diagnostics,
  not confidence intervals or evidence of accuracy at the boundary.
- `c6_applicability_by_grid.csv`: the 413 assigned C6 supports, their building
  fraction and restriction/caution flags. The exact thresholds come from 390
  original strict-fitting C6 supports. The flags identify 20 restrictions and
  19 caution cases; overlapping supports are not independent neighbourhoods.
- `elbow_threshold_diagnostic.csv`: the three-to-four gain divided by the
  four-to-five gain, using three-decimal simulation outputs. Boolean columns
  indicate whether that ratio meets 1.5, 2 or 3. This varies one engineering
  criterion, not all selection criteria or the number of morphology classes.
- `year2022_selection.json`: rank, population, date interval, mean temperature
  and anomaly for the 2022 selection. Temperatures and anomalies are in degC.
  The four station series are processed, measurement-derived data, not an
  independently audited raw-sensor-only record.

The original tables S1-S13 and heat-sensitivity results retain their exact
numerical contents. Package file hashes and descriptions are in
`../CHECKSUMS.sha256` and `../FILE_INDEX.csv`.
