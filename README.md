# StudentContextNLP (v0.1)

**Research:** The Effect of Question Context on Classifying Semantic Inconsistencies in Student Explanations.

**Türkçe:** Öğrenci Açıklamalarındaki Anlamsal ve Bağlamsal Tutarsızlıkların Sınıflandırılmasında Soru Bağlamının Etkisi.

[**Türkçe kullanım ve araştırma protokolü**](README_TR.md)

This research-code repository compares four-class SciEntsBank student response assessment under **explanation-only vs explanation+question** inputs. It runs locally on CPU with lexical TF-IDF baselines and optional frozen local MiniLM sentence representations followed by Logistic Regression. No API keys, hosted LLM inference, agent, database, or LLM training.

**Results policy:** There are no validated SciEntsBank results in this repository yet. All locally generated smoke fixtures and scores are **synthetic software tests**, never research evidence. Real results must be produced separately after the source is published and the official data audit has passed.

## Quick start (no data download)

```bash
python -m pip install -r requirements.txt
python -m pytest -q
python -m scripts.run_demo
```

Demo labels and scores must never be cited as real student outcomes.

## Real data (later phase)

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