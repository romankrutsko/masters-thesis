# Translation Evaluation Runbook

This project includes `task_equivalents/tests/run_translation_evaluation.py` to run:
- Execution-based reliability checks for all translated snippets, scored `0.0` to `1.0` (default one decimal).
- Static analysis in SonarQube for Python and R slices.

## 1) Start SonarQube (Docker)

```bash
cd task_equivalents/tests
docker compose -f docker-compose.sonarqube.yml up -d
```

SonarQube UI: `http://localhost:9000`

## 2) Prepare auth token

Create a user token in SonarQube and export:

```bash
export SONAR_TOKEN="<your_token>"
export SONAR_HOST_URL="http://localhost:9000"
```

## 3) Run execution checks + static checks

```bash
cd /Users/romankrutsko/PycharmProjects/MastersThesis
.venv/bin/python task_equivalents/tests/run_translation_evaluation.py --mode all
```

## 4) Outputs

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
.venv/bin/python task_equivalents/tests/run_translation_evaluation.py \
  --mode all \
  --models starcoder,gpt \
  --prompt-types base,optimized \
  --languages python,r
```

Blacklist failing or expensive candidates:

```bash
.venv/bin/python task_equivalents/tests/run_translation_evaluation.py \
  --mode all \
  --blacklist-file task_equivalents/tests/evaluation_blacklist.txt
```

The blacklist file uses one repo-relative candidate path per line. By default, the evaluator reads `task_equivalents/tests/evaluation_blacklist.txt`.

## Notes

- Execution scoring does not enforce a fail threshold. It always records scores in `[0.0, 1.0]`.
- For R static analysis, `lintr` findings are converted to Sonar external issues and imported during scanner runs.
- Required local tools: `sonar-scanner`, `Rscript` (with `lintr` and `jsonlite`), Python dependencies used by scripts.
