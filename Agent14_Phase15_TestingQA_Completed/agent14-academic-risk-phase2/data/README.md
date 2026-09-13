# Agent 14 Synthetic Data

The repository contains deterministic synthetic demo/training data only.

```powershell
cd data/generators
python generate_all.py
cd ../..
python scripts/validate_phase1_data.py
```

The generated data is designed around an early-warning boundary: week-6 checkpoint features predict end-of-semester outcomes.
