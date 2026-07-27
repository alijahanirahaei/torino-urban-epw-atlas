# Contributing

Issues and pull requests should identify the affected release version, grid IDs,
and reproducible steps. Changes to assignments, morphology values, EPWs, or UWG
configurations must include updated provenance, checksums, validation output, and
tests.

Before proposing a release change, run:

```bash
python3 scripts/validate_release.py
python3 -m unittest discover -s tests -v
```

Before staging files, also run `git status --short --ignored` and confirm that
dependencies, editor settings, credentials, keys, caches, and local test outputs
remain ignored.

Do not manually edit generated files under `data/` or `web/data/`. Update the
validated source workflow or `scripts/build_release.py`, rebuild, and document the
change in `CHANGELOG.md`.

When adding, renaming, or removing a release file, update the complete catalog in
`docs/repository-guide.md`; release validation checks that every distributed file
is documented.
