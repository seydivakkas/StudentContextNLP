# StudentContextNLP — English v0.1 baseline + exploratory TR v0.2.1

**Research:** The Effect of Question Context on Classifying Semantic Inconsistencies in Student Explanations.

**Türkçe:** Öğrenci Açıklamalarındaki Anlamsal ve Bağlamsal Tutarsızlıkların Sınıflandırılmasında Soru Bağlamının Etkisi.

[**Türkçe kullanım ve araştırma protokolü**](README_TR.md)

This research-code repository compares four-class SciEntsBank student response assessment under **explanation-only vs explanation+question** inputs. It runs locally on CPU with lexical TF-IDF baselines and optional frozen local MiniLM sentence representations followed by Logistic Regression. No API keys, hosted LLM inference, agent, database, or LLM training.

**Research status (11 October 2026):** Real SciEntsBank English and exploratory machine-translated Turkish B0–B3 results have been obtained **locally by the researcher** and summarized in GitHub. Latest Windows regression suite: **76 passed**; original English P1 metrics reproduced at 1e-8; all 36 four-class confusion matrices audited. **No independently human-verified Turkish gold labels, no validated educational deployment, and no S1/S2 empirical result are claimed.** CI runs synthetic fixtures, not the private original student corpus.

**Current project report:** [TEKNOFEST 2242 Education research report](paper/TEKNOFEST_2242_EGITIM_RAPORU_TR.md). **Independent validation plan:** [TR_INDEPENDENT_VALIDATION_PLAN](docs/TR_INDEPENDENT_VALIDATION_PLAN.md). **Detailed T4 outputs:** [T4_REAL_PROXY](paper/T4_REAL_PROXY_2026-10-11.md).

## Quick start (no data download)

```bash
python -m pip install -r requirements.txt
python -m pytest -q
python -m scripts.run_demo
```

Demo labels and scores must never be cited as real student outcomes.

## Real data (researcher-local workflow; keep originals unchanged)

```bash
python download_data.py --data-dir data/raw
python audit_dataset.py --data-dir data/raw --output-dir reports
# Review the audit; only continue if acceptable
python train_lexical.py --data-dir data/raw --out results/lexical
python plot_results.py --results results/lexical/baseline_results.json --output results/figures
```

Optional frozen local sentence encoder:

```bash
python -m pip install -r requirements-semantic.txt
python download_encoder.py --out models/local_encoder
python train_semantic.py --data-dir data/raw --out results/semantic --model-dir models/local_encoder
python compare_experiments.py --out results/combined
python plot_comparison.py --csv results/combined/model_comparison.csv --out results/figures/test_uq_macro_f1.png
```

SciEntsBank: https://huggingface.co/datasets/nkazi/SciEntsBank . **Data is not redistributed in this repository**. Software MIT, dataset and pretrained model have independent licenses. Read the research protocol before using test data.
