# P0.1 — Real SciEntsBank Dataset Audit: Observed Windows Results

> **Source provenance:** Values below come from the researcher's Windows PowerShell output on 10 October 2026, after running the repository's real `download_data.py` and `audit_dataset.py`. The raw dataset, the full JSON and the file SHA256 manifest are **local-only**; GitHub does not contain or independently verify those bytes. **Status: PASS_WITH_WARNINGS.**

## Dataset integrity observed

| Split | Rows | Normalized unique questions | Extra duplicate triples | Conflicting triples (original 5 labels) | Conflicting triples (derived 4 labels) | Rows affected by conflicting triples | Published original label distribution |
|---|---:|---:|---:|---:|---:|---:|---|
| train | 4,969 | 135 | 143 | 6 | 6 | 15 | match |
| test_ua | 540 | 135 | 1 | 0 | 0 | 0 | match |
| test_uq | 733 | 15 | 30 | 0 | 0 | 0 | match |
| test_ud | 4,562 | 45 | 333 | 1 | 1 | 6 | match |
| **total** | **10,804** | **195 across all splits** | **507** | **7** | **7** | **21** | |

**Cross-split overlap with training:**

| Split | Normalized question overlap | Exact normalized question+reference+answer overlap |
|---|---:|---:|
| test_ua | 135 | 24 |
| **test_uq** | **0** | **0** |
| test_ud | 0 | 0 |

**Observed original five-label conflicts:**
- train: 3 groups correct vs partially_correct_incomplete; 2 groups contradictory vs irrelevant; 1 group correct vs irrelevant.
- test_ud: 1 group correct vs partially_correct_incomplete.
- All 7 groups remain disagreements after the four-label mapping; this is **not** eliminated by merging irrelevant and non_domain into Other.
- Fatal errors: 0; dataset audit status: PASS_WITH_WARNINGS.

## Research handling decision for first baseline

**Conditional approval was enacted on the researcher's Windows computer** after verifying local SHA-256 hashes and generating `reports/P0_DECISION.md`; the first descriptive original-data B0–B3 baseline was run:

1. Do not modify original Parquet files or resolve contradictory labels by guesswork.
2. Include all 4,969 original training rows in the primary fixed-dataset benchmark; later run a **separately identified sensitivity analysis** excluding or grouping contradictory records and compare against the frozen primary result.
3. Official **Test-UQ remains the single primary test**; no parameter tuning or threshold selection on any official test. Question-cluster bootstrap uses 15 groups and may yield a wide confidence interval. A within-Test-UQ count of 30 extra duplicates may affect instance-weighted statistics; disclose this limitation.
4. Test-UA is secondary and **has 24 overlapping exact normalized triples with train**; do not claim its answers are all unique relative to train. Test-UD is secondary and contains one contradictory label triple.
5. Preserve `PASS_WITH_WARNINGS` in final reports, with reviewed warnings and explicit `--allow-audit-warnings` for the baseline. This does *not* mean warnings were removed or dataset quality certified.
6. Keep raw student-answer rows, trained models, predictions and audit CSVs out of GitHub. Record only aggregate metrics, code and reproducibility information.

## Still to check locally

- [x] Researcher locally verified SHA-256 for all four Parquet files against the pinned source manifest.
- [x] Researcher wrote `reports/P0_DECISION.md` with an explicit conditional warning acceptance.
- [x] Researcher ran B0–B3 original-data baseline on Windows; result files are in locally ignored `results/lexical/`.
- [x] Researcher provided actual Test-UQ aggregate metrics (see [research report](RESEARCH_DRAFT_TR.md)).
- [ ] Independent run on the same source bytes and conflict/duplicate sensitivity analysis (future confirmation).

**No translation quality can be inferred from this P0 audit.** For model performance, see the separately documented real Test-UQ experiment and its limitations.
