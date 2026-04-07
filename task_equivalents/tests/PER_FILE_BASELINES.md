# Per-File Baselines

## Setup
```bash
cd /Users/romankrutsko/PycharmProjects/MastersThesis
source .venv/bin/activate
```

## Generate Per-File Baselines

### Python only
```bash
python3 task_equivalents/tests/generate_per_file_baselines.py \
  --skip-r \
  --output-dir task_equivalents/baselines/per_file_generated_python
```

### R only
```bash
python3 task_equivalents/tests/generate_per_file_baselines.py \
  --skip-python \
  --output-dir task_equivalents/baselines/per_file_generated_r
```

### Python + R
```bash
python3 task_equivalents/tests/generate_per_file_baselines.py \
  --output-dir task_equivalents/baselines/per_file_generated_all
```

## Verify Existing File Against Baseline

### Python
```bash
python3 task_equivalents/tests/check_per_file_baseline.py \
  --baseline-file task_equivalents/baselines/per_file_generated_python/python/task_equivalents__python__machine_learning_workflows__02_regression_workflow_feature_importance.py.json \
  --candidate task_equivalents/python/machine_learning_workflows/02_regression_workflow_feature_importance.py \
  --atol 1e-4 \
  --rtol 1e-3
```

### R
```bash
python3 task_equivalents/tests/check_per_file_baseline.py \
  --baseline-file task_equivalents/baselines/per_file_generated_r/r/task_equivalents__r__machine_learning_workflows__02_regression_workflow_feature_importance.R.json \
  --candidate task_equivalents/r/machine_learning_workflows/02_regression_workflow_feature_importance.R \
  --atol 1e-4 \
  --rtol 1e-3
```
