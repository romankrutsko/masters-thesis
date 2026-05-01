# Evaluation Scripts

This directory groups the repository's evaluation tooling in one place.

## Layout

- `reliability/`
  - translation reliability scoring
- `maintainability/`
  - SonarQube static-analysis config
- `helpers/`
  - shared Python/R helper scripts, common evaluation code, and blacklist
- `perf/`
  - runtime and energy benchmarking
  - original-code benchmark wrapper
  - downstream perf/energy analysis scripts

## Main Entry Points

- `scripts/evaluation/reliability/run_reliability_evaluation.py`
- `scripts/evaluation/maintainability/run_maintainability_evaluation.py`
- `scripts/evaluation/perf/measure_perf_energy.py`
- `scripts/evaluation/perf/run_original_perf_energy.py`
- `scripts/evaluation/perf/run_perf_energy_nonparametric_analysis.py`
