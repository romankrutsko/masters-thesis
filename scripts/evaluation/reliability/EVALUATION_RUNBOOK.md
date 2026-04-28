# Translation Evaluation Runbook

This project now separates the two evaluation concerns:

- `scripts/evaluation/reliability/run_reliability_evaluation.py`
  - execution-based reliability checks for translated snippets
- `scripts/evaluation/reliability/run_maintainability_evaluation.py`
  - SonarQube-based maintainability checks for Python and R slices
- `scripts/evaluation/reliability/run_translation_evaluation.py`
  - compatibility wrapper that can still run both from one command

## 1) Start SonarQube (Docker)

```bash
cd scripts/evaluation/reliability
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
.venv/bin/python scripts/evaluation/reliability/run_maintainability_evaluation.py
```

## 5) Optional Compatibility Wrapper

If you still want the old single entry point:

```bash
.venv/bin/python scripts/evaluation/reliability/run_translation_evaluation.py --mode all
```

## 6) Outputs

Outputs are written to:

```text
task_equivalents/evaluation_outputs/<run_id>/
```

Key files:
- `execution_scores.csv` and `execution_scores.json`
- `static_sonar_results.csv` and `static_sonar_results.json`
- `run_manifest.json`
- `static/<model>__<prompt_type>__<language>/sonar-scanner.log`

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
  --blacklist-file scripts/evaluation/reliability/evaluation_blacklist.txt
```

The blacklist file uses one repo-relative candidate path per line. By default, the evaluator reads `scripts/evaluation/reliability/evaluation_blacklist.txt`.

## Notes

- Execution scoring does not enforce a fail threshold. It always records scores in `[0.0, 1.0]`.
- For R maintainability checks, `lintr` findings are converted to Sonar external issues and imported during scanner runs.
- Required local tools: `sonar-scanner`, `Rscript` (with `lintr` and `jsonlite`), Python dependencies used by scripts.
