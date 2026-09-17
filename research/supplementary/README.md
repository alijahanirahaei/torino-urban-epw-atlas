# Supplementary Material

Ali JahaniRahaei and Giacomo Chiesa

Version 1.0.0, 17 September 2026.

This package accompanies **Morphology-based classification and error-controlled
reduction of urban weather files with Torino as a case study**, by Ali
JahaniRahaei and Giacomo Chiesa.

Read [supplementary_material.pdf](supplementary_material.pdf) for the complete
methods and diagnostic results. An [editable Word copy](supplementary_material.docx)
and [Markdown copy](SUPPLEMENTARY_MATERIAL.md) are also provided.
Sections S1-S6 cover spatial inputs, classification, UWG execution, evaluation
and reuse; S7 covers the traffic and HVAC heat experiment. All 13 supplementary
tables have CSV versions; S1, S2 and S10-S12 are also printed in the document.

The [versioned release](https://github.com/alijahanirahaei/torino-urban-epw-atlas/releases/tag/supplement-v1.0.0)
provides the complete ZIP and separate PDF/Word downloads. This supplement uses
the unchanged atlas v0.2.0 weather library and classifications. Its release
does not introduce new EPWs, classes or simulation results.

The four-file library represents the tested UWG outputs, not validated local
weather at every location. Recommendations exclude the diagnosed high-density
industrial tail. The heat scenarios are sensitivity tests, not observed traffic
or a calibrated heat map.

## File Contents

- `supplementary_material.docx`: readable Sections S1-S7, Tables S1-S13 and
  Figures S1-S6. Large detailed tables are companion CSVs rather than printed
  in full; their paths and interpretation are specified in the document.
- `supplementary_material.pdf`: fixed-layout reading copy of the Word document.
- `SUPPLEMENTARY_MATERIAL.md`: the same text, with relative figure links.
- `tables/`: labelled supplementary CSVs S1-S13. Their explicit metric, period,
  population, precision and scenario columns are part of the data definitions.
- `figures/`: S1-S6 in PNG; S3-S6 also have vector PDF copies. These are
  supplementary figures, not replacements for the main manuscript figures.
- `configs/category_A.json` to `category_D.json`: executed annual representative
  configurations, using 500 m supports and 365 days.
- `configs/common_template.json`: inherited configuration scaffold, retaining
  31-day and 1000 m placeholders. Do not run this file as the annual experiment.
- `configuration_provenance.json`: inherited baseline key/provenance record.
- `source_hashes.json`: descriptive identifiers and hashes of source analysis
  artifacts. These identifiers are not paths to files in this package.
- `heat_sensitivity/`: exact additional-experiment configurations, portable
  run provenance, input selection and schedule audits, detailed result CSVs and
  a resumable annual simulation runner. See its README for execution instructions.
- `CHECKSUMS.sha256`: hashes of all other packaged files for integrity checks.
- `FILE_INDEX.csv`: path, format, purpose and SHA-256 for each content file.
- `CITATION.cff`: authorship and version metadata for this supplement.
- `LICENSE.md` and `LICENSES/`: terms for the text, derived data and software,
  with separate acknowledgement of upstream rights.

The package deliberately omits raw weather and generated EPWs. Weather forcing
is obtained separately from the companion dataset, DOI
[10.5281/zenodo.14905721](https://doi.org/10.5281/zenodo.14905721), described by
JahaniRahaei, Milelli and Chiesa (2025), DOI
[10.1016/j.dib.2025.111708](https://doi.org/10.1016/j.dib.2025.111708).
Obtain the exact AvMY Caselle file; its hash must match the documented one.
The runner never overwrites that source. Redistribution and reuse of source
datasets remain subject to their original terms.

## Interpretation

Temperature errors in the heat extension distinguish source-relative modelled
UHI, response relative to the same support's baseline, and representation error
relative to another model output. None is automatically measured-station error.
The heat tests use DJF/JJA and clock hours 07-18/19-06; main-text Table 9 uses October-March and April-September half-years. Writer decimals distinguish
serialization effects, not physical accuracy. The heat test's 14 non-medoids
are purposive selections and cannot supply population percentiles.

The executable extension reproduces the heat integrations, but not the entire
city GIS extraction, clustering and all scientific experiments. The
[atlas v0.2.0 release](https://github.com/alijahanirahaei/torino-urban-epw-atlas/releases/tag/v0.2.0)
provides fixed-classifier reconstruction, seven-medoid reduction and annual UWG
tools. See Section S6 for their scope and limitations.

## Verify And Cite

After extracting the ZIP, run `shasum -a 256 -c CHECKSUMS.sha256` from its root
on macOS, or `sha256sum -c CHECKSUMS.sha256` on Linux. No weather simulation is
needed to read the document or tables. The heat runner's separate `--check-only`
option checks configurations and forcing before simulation.

Cite both authors, the supplement version and its release URL. When the journal
article is published, also cite its bibliographic reference. The source-weather
DOI identifies the companion dataset, not this supplement or the atlas.
