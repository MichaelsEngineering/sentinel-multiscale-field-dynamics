# Run Manifest Rules

Tracked runs must write the following files under `runs/<date>/<problem>/<workspace>_<confighash>_<seed>/`:

- `run_manifest.json`
- `run_summary.json`
- `trace.jsonl`

## Required fields

- explicit seed
- config path
- config hash
- command name
- runtime label
- problem name
- artifact path

## Policy

- Benchmark and tracked rollout commands must emit these files.
- Missing manifest or trace output is a failed tracked run.
- Benchmark comparisons should be made against config-backed thresholds, not ad hoc human judgment.
