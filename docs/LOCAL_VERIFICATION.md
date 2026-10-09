# Local Verification — 2026-10-09

## Current locally observed status

- `OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python -m pytest -q`: **20 passed**.
- `python -m scripts.run_demo`: completed with local TF-IDF B0–B3 fitting, `.joblib` artifacts, paired bootstrapped comparison, CSV and PNG outputs.
- `python predict.py --model results/demo/lexical/B2.joblib --answer ... --question ...`: completed using stored local sklearn model.
- A deterministic `FakeEncoder` validates S1/S2 software flow only; actual `all-MiniLM-L6-v2` weights are **not downloaded/tested yet**.
- All demo scores, including illustrative macro-F1=1.00, are **SYNTHETIC and NOT research evidence**.
- No actual SciEntsBank data audited; no actual Test-UQ scientific result.
- No GitHub push / cloud CI yet; needs a repository.
