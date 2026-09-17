# Heat Sensitivity Reproduction

This folder contains the exact 105 configurations underlying Supplementary
Section S7: 84 new annual alternatives and 21 reused baselines. Running all
configurations produces 210 EPWs, one- and three-decimal outputs from each
annual integration. Baseline files are regenerated only when executing this
reproduction package; the original experiment reused their archived outputs.

## Requirements

Use Python 3.10 and UWG 5.3.4 for the closest match to the archived execution.
The runner uses the Python standard library and UWG. A fresh virtual environment
is recommended. Run these commands in this folder:

```bash
python3.10 -m venv .venv
source .venv/bin/activate
python -m pip install uwg==5.3.4
```

Obtain `AvMY_CASELLE.epw` from the companion weather dataset,
DOI [10.5281/zenodo.14905721](https://doi.org/10.5281/zenodo.14905721).
Its raw SHA-256 must be:

```text
3430967c3faa30aa3512a34c8fb636003458f162b50c2d2b5ded70707f76a71a
```

The runner accepts only this file or its already pressure-prepared derivative:

```text
39c5c8cb90b39fefdfb531ade96700e9436d4df9c8fca3a57191f820d135e5a9
```

For the raw file, it creates a copy in the output folder and converts pressure
from hPa to Pa in field 10 only. It verifies the resulting hash and never applies
this conversion twice. Source weather must remain outside the package.

## Run

Replace the example weather path with the location of the obtained file. Choose
an output directory outside `heat_sensitivity/` and preferably outside the whole
research package. First check all configurations and the input, without a run:

```bash
python reproduce_heat.py --forcing /path/to/AvMY_CASELLE.epw \
  --output ../../heat_outputs --check-only
```

An optional two-case annual smoke test is:

```bash
python reproduce_heat.py --forcing /path/to/AvMY_CASELLE.epw \
  --output ../../heat_outputs --workers 2 \
  --jobs baseline__C0__grid_12618,heat_40__C0__grid_12618
```

Run all configurations, resuming any verified completed cases:

```bash
python reproduce_heat.py --forcing /path/to/AvMY_CASELLE.epw \
  --output ../../heat_outputs --workers 4
```

One to four workers are supported. The archived 84 new cases took about 16
minutes with four workers on the authors' machine; a full reproduction includes
21 additional baseline integrations, and runtime varies with hardware. Allow
several hundred megabytes for outputs and logs. Interrupting a run does not
make partial EPWs successful: only completed, hash-verified cases are skipped
on restart. Wait for the previous coordinator to exit before restarting. Do
not start two runs in the same output directory.

Progress is printed as cases finish. In a second terminal:

```bash
cat ../../heat_outputs/heartbeat.json
cat ../../heat_outputs/run_status.json
```

`heartbeat.json` is refreshed about every 30 seconds and at completions.
`run_status.json` records status, duration, hashes and output paths for every
completed attempt. Each case has a log. Failed-attempt records and logs are
archived before a retry. Successful EPWs are checked before any resume.

## Outputs And Verification

- `precision1/JOB_ID.epw` and `precision3/JOB_ID.epw`: two serializations of the
  same completed annual integration, not two separate simulations.
- Output normalization is restricted to the documented UWG 5.3.4 duplicated
  final-field issue. Eight headers, 8760 records and 35 columns are required.
- Every result contains `matches_archived_epw1` and `matches_archived_epw3`.
  `true` means a byte-identical file. A completed model run with `false` requires
  numerical inspection before claiming exact reproduction; differing software
  platforms can affect floating-point calculations.
- Exact per-run JSONs are authoritative. The inherited common template one
  folder above is a scaffold and is never read by this runner.

## Data Dictionary

`run_manifest.csv` maps each job to its scenario, support and relative config,
with config, forcing and expected EPW hashes. `fit_support_share` is defined
only for medoids; selected non-medoids have no probability weights in this test.
All `config_file` paths are relative to this folder.

`configs/` contains 105 immutable annual JSONs. `changed_keys.csv` identifies
each intended change against its support baseline. `schedule_audit.json`
contains exact model timestep counts, profile normalization and annual heat.
`fit_population_heat_scenarios.csv` contains the 10,593 support road ranks and
opposing amplitudes. `nonmedoid_selection_frozen.csv` records GIS-only selection
of 14 road-share extremes; they are not a new probability sample.

`results/` contains:

- `scenario_summary.csv`: both precisions, count-selection criteria, identities, maps and
  unchanged versus rerun maximum errors.
- `reduction_curves.csv`: best subset for every count from one to seven.
- `all_127_subsets.csv`: every nonempty subset for every state and precision.
- `support_characteristics.csv`: all 21 supports and baseline UWG descriptors;
  `baseline_json` is relative to this folder, not to `results/`.
- `support_responses.csv`: source-relative and same-support-baseline KPIs.
- `medoid_compression_errors.csv`: representation errors under the different
  identity, assignment and file-content options.
- `nonmedoid_errors.csv`: own-class and inherited four-file errors by period.
- `medoid_pairwise_periods.csv`: medoid-to-medoid comparisons by period.
- `monthly_day_night_medoid_response.csv`: monthly day/night model responses.
- `epw_field_scope.csv`: which EPW fields are identical among medoids.
- `output_quality.csv`: annual length and humidity/dew-point physical checks.

`precision` is the writer decimal count. Temperature quantities use degrees
Celsius; RH changes use percentage points. `delta_t_c` is candidate minus the
named reference, not an absolute UHI unless the reference is Caselle.
`winter` means DJF and `summer` JJA here; day hours are EPW labels 07-18 and
night hours 19-06. All fraction inputs are ratios, not percentages. Road fraction
is a hypothetical heat-ordering proxy, not measured traffic intensity.

The result tables contain the archived comparisons. The runner regenerates
their EPW inputs; it does not rerun the entire GIS pipeline or evaluate accuracy
against observed station data. See Section S7 for the subset objective,
weighting, thresholds and seasonal comparison definitions.
