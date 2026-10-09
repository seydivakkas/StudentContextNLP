# v0.1 Research Protocol — Frozen Before Real Data

## Target

Four derived SciEntsBank classes (`Correct`, `Incomplete`, `Contradictory`, `Other`) for English science student short answers.

## Primary estimand (descriptive ablation)

`MacroF1(Test-UQ, B2: explanation+question) - MacroF1(Test-UQ, B1: explanation)`. Paired percentile 95% question-cluster bootstrap CI (1000 resamples), seed 20261009. This is an input-ablation contrast, **not causal effect of an intervention on learning**.

## Secondary estimand

`MacroF1(Test-UQ, S2) - MacroF1(Test-UQ, S1)` with the encoder frozen and separate concatenated normalized embeddings.

## Fixed model families and hyperparameters

- B0: majority class.
- B1: explanation TF-IDF word bigrams + char_wb ngrams 3–5, Logistic Regression.
- B2: explanation+question, identical vectorizer settings and classifier family.
- B3: question-only shortcut control.
- S1: local frozen all-MiniLM-L6-v2 explanation embedding, Logistic Regression.
- S2: separate local frozen question + explanation embeddings concatenated, Logistic Regression.
- `C ∈ {0.1, 1, 10}` chosen on a single fixed train-only GroupShuffleSplit of normalized question, 25% validation groups, random seed 20261009.
- Full training split used to refit each fixed selected model. No official test rows used in hyperparameter selection.

## Metrics

- Primary test `test_uq`, primary metric `macro_f1`, 4 defined classes with 0 for no-support/no-prediction class.
- Secondary `test_ua`, `test_ud`; weighted F1, accuracy, per-class breakdown, confusion matrix, runtime.
- New-domain generalization has different distribution and is exploratory.
- Report feature-only shortcut B3.
- Confidence intervals are uncertainty descriptions, not conclusive significance in all conditions.

## Scope/limitations

- Original 5-class labels are merged to an explicitly **derived** 4-class benchmark.
- Question grouping by normalized question text is proxy for true question ID; audit cross-split and normalized text duplicates.
- Question-to-label shortcuts may remain even when overlaps are zero.
- Multiple student answers to the same question are not independent; use paired question-cluster resampling.
- Assessing a student answer against a reference is not diagnosing a stable cognitive misconception.
- No conclusion for Turkish text until an appropriately annotated Turkish dataset exists and a multilingual encoder is evaluated.
- No claims of results before real data audited and models run. No hosted inference or keys.
