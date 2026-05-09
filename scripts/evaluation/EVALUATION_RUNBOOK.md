# Translation Evaluation Runbook

This project now separates the two evaluation concerns:

- `scripts/evaluation/reliability/run_reliability_evaluation.py`
  - execution-based reliability checks for translated snippets
- `scripts/evaluation/maintainability/run_maintainability_evaluation.py`
  - SonarQube-based maintainability checks for Python and R slices
## 1) Start SonarQube (Docker)

```bash
cd scripts/evaluation/maintainability
docker compose -f docker-compose.sonarqube.yml up -d
```

SonarQube UI: `http://localhost:9000`

## 2) Prepare auth token

Create a user token in SonarQube and export:

```bash
export SONAR_TOKEN="<your_token>"
export SONAR_HOST_URL="http://localhost:9000"
```

## 3) Run Reliability Checks

```bash
cd /Users/romankrutsko/PycharmProjects/MastersThesis
.venv/bin/python scripts/evaluation/reliability/run_reliability_evaluation.py
```

## 4) Run Maintainability Checks

```bash
.venv/bin/python scripts/evaluation/maintainability/run_maintainability_evaluation.py
```

## 5) Outputs

Outputs are written to:

```text
task_equivalents/evaluation_outputs/<run_id>/
```

Key files:
- `execution_scores.csv` and `execution_scores.json`
- `static_sonar_results.csv` and `static_sonar_results.json`
- `run_manifest.json`
- `static/<model>__<prompt_type>__<language>/sonar-scanner.log`

## Reliability score columns

Execution reliability is a behavioral similarity score, not an exact unit-test
result. For each translated candidate, the evaluator runs the original reference
script and the candidate script, summarizes the objects created by each run, and
compares those summaries.

The `execution_scores.csv` component columns mean:

- `object_structures`: overlap in broad object categories, such as table,
  vector, matrix, model, scalar, or other.
- `table_matrix_dimensions`: overlap in table/matrix dimensions, such as
  number of rows and columns.
- `vector_lengths`: overlap in lengths of one-dimensional objects, such as
  pandas Series or R vectors.
- `model_structure`: overlap in rough model complexity, such as number of
  fitted parameters, coefficients, or model fields.
- `numeric_summaries`: overlap in rounded numeric summaries, such as means,
  standard deviations, sums, minima, maxima, or model-related numeric values.

The final `score` is a weighted average of these components:

```text
object_structures       0.25
table_matrix_dimensions 0.25
vector_lengths          0.15
model_structure         0.20
numeric_summaries       0.15
```

If the original/reference script has no data for a component, that component is
ignored for that row instead of being counted as a match or mismatch. Numeric
values are matched with the configured tolerances `--atol` and `--rtol`.

## Optional filters

Run a subset:

```bash
.venv/bin/python scripts/evaluation/reliability/run_reliability_evaluation.py \
  --models starcoder,gpt \
  --prompt-types base,optimized \
  --languages python,r
```

Blacklist failing or expensive candidates:

```bash
.venv/bin/python scripts/evaluation/reliability/run_reliability_evaluation.py \
  --blacklist-file scripts/evaluation/helpers/evaluation_blacklist.txt
```

The blacklist file uses one repo-relative candidate path per line. By default, the evaluator reads `scripts/evaluation/helpers/evaluation_blacklist.txt`.

## Notes

- Execution scoring does not enforce a fail threshold. It always records scores in `[0.0, 1.0]`.
- For R maintainability checks, `lintr` findings are converted to Sonar external issues and imported during scanner runs.
- Required local tools: `sonar-scanner`, `Rscript` (with `lintr` and `jsonlite`), Python dependencies used by scripts.
