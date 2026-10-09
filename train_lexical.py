"""CPU-only four-class lexical baselines on SciEntsBank.

Run only after examining the full P0 audit. No LLM or API calls.
The official Test-UQ remains unseen until every model and C is frozen.
"""
from __future__ import annotations
import argparse
import json
import time
from pathlib import Path

import numpy as np
import joblib
import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.linear_model import LogisticRegression

from audit_dataset import LABEL_MAP, SPLITS, audit, canonical_label, normalize, read_split

LABELS = ('Correct', 'Incomplete', 'Contradictory', 'Other')
CONDITIONS = ('B0', 'B1', 'B2', 'B3')


def prepare(raw: pd.DataFrame) -> pd.DataFrame:
    d = raw.copy()
    d['target'] = d['label'].map(lambda x: LABEL_MAP[canonical_label(x)])
    d['group'] = d['question'].map(normalize)
    d['answer_text'] = d['student_answer'].fillna('').astype(str)
    d['question_text'] = d['question'].fillna('').astype(str)
    if any(d['group'].eq('')):
        raise ValueError('Boş soru metni var')
    if any(d['answer_text'].str.strip().eq('')):
        raise ValueError('Boş öğrenci cevabı var')
    return d


def input_text(df: pd.DataFrame, condition: str) -> list[str]:
    if condition in ('B0', 'B1'):
        return df['answer_text'].tolist()
    if condition == 'B2':
        return ('student: ' + df['answer_text'] + ' question: ' + df['question_text']).tolist()
    if condition == 'B3':
        return df['question_text'].tolist()
    raise ValueError(condition)


def create_model(condition: str, C: float = 1.0):
    if condition == 'B0':
        return DummyClassifier(strategy='most_frequent')
    features = FeatureUnion([
        ('words', TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_features=25000, sublinear_tf=True)),
        ('chars', TfidfVectorizer(analyzer='char_wb', ngram_range=(3, 5), min_df=2,
                                  max_features=35000, sublinear_tf=True)),
    ])
    return Pipeline([('tfidf', features), ('logreg', LogisticRegression(C=C, max_iter=1200, random_state=42))])


def score(y_true, y_pred) -> dict:
    return {'macro_f1': float(f1_score(y_true, y_pred, labels=LABELS, average='macro', zero_division=0)),
            'weighted_f1': float(f1_score(y_true, y_pred, labels=LABELS, average='weighted', zero_division=0)),
            'accuracy': float(accuracy_score(y_true, y_pred))}


def grouped_bootstrap_delta(df: pd.DataFrame, pred_a: np.ndarray, pred_b: np.ndarray,
                             samples: int = 1000, seed: int = 20261009) -> dict:
    """Paired cluster bootstrap, with fast numpy confusion-based macro-F1."""
    groups = df['group'].to_numpy()
    uniq = np.unique(groups)
    rng = np.random.default_rng(seed)
    indices = [np.flatnonzero(groups == g) for g in uniq]
    label_ids = {name: k for k, name in enumerate(LABELS)}
    target = np.fromiter((label_ids[x] for x in df['target']), dtype=np.int16)
    pa = np.fromiter((label_ids[x] for x in pred_a), dtype=np.int16)
    pb = np.fromiter((label_ids[x] for x in pred_b), dtype=np.int16)
    k = len(LABELS)
    def macro(actual, predicted):
        confusion = np.bincount(actual.astype(np.int64) * k + predicted,
                                minlength=k * k).reshape(k, k)
        tp = confusion.diagonal().astype(float)
        denom = confusion.sum(axis=0) + confusion.sum(axis=1)
        f = np.divide(2 * tp, denom, out=np.zeros(k, dtype=float), where=denom != 0)
        return float(f.mean())
    values = np.empty(samples, dtype=float)
    for j in range(samples):
        sampled = rng.integers(len(uniq), size=len(uniq))
        idx = np.concatenate([indices[t] for t in sampled])
        values[j] = macro(target[idx], pb[idx]) - macro(target[idx], pa[idx])
    point = macro(target, pb) - macro(target, pa)
    return {'delta_B2_minus_B1': point, 'cluster_count': int(len(uniq)),
            'bootstrap_iterations': samples,
            'percentile_95_ci': [float(np.quantile(values, 0.025)), float(np.quantile(values, 0.975))],
            'interpretation': 'Descriptive paired question-cluster bootstrap CI; not a causal effect.'}


def run(data_dir: Path, out: Path, seed: int = 20261009,
        allow_warnings: bool = False) -> dict:
    frames, paths = {}, {}
    for split in SPLITS:
        frames[split], paths[split] = read_split(data_dir, split)
    check = audit(frames, paths)
    if check['fatal_errors']:
        raise RuntimeError('P0 FAIL: ' + '; '.join(check['fatal_errors']))
    if check['warnings'] and not allow_warnings:
        raise RuntimeError('P0 WARNINGS: önce P0_audit.md dosyasını incele ve gerekçeli olarak --allow-audit-warnings kullan: '
                           + '; '.join(check['warnings']))
    train = prepare(frames['train'])
    # Selection validation: question-grouped, with fixed seed. Never use test splits for model selection.
    splitter = GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=seed)
    ti, vi = next(splitter.split(train, groups=train['group']))
    sub, val = train.iloc[ti], train.iloc[vi]
    if set(sub['group']) & set(val['group']):
        raise AssertionError('Validation group leakage')
    if set(sub['target']) != set(LABELS) or set(val['target']) != set(LABELS):
        raise RuntimeError('Soru bazlı validation bölümünde dört sınıfın tamamı yok; split stratejisini yeniden değerlendir.')
    out.mkdir(parents=True, exist_ok=True)
    # Record decisions before test evaluation.
    fitted = {}
    decisions = {}
    for cond in CONDITIONS:
        candidates = [1.0] if cond == 'B0' else [0.1, 1.0, 10.0]
        tried = []
        for c in candidates:
            model = create_model(cond, c)
            model.fit(input_text(sub, cond), sub['target'].tolist())
            preds = model.predict(input_text(val, cond))
            tried.append({'C': c, 'validation_macro_f1': score(val['target'], preds)['macro_f1']})
        best = sorted(tried, key=lambda x: (-x['validation_macro_f1'], x['C']))[0]
        model = create_model(cond, best['C'])
        started = time.perf_counter()
        model.fit(input_text(train, cond), train['target'].tolist())
        fitted_seconds = time.perf_counter() - started
        fitted[cond] = model
        joblib.dump(model, out / f'{cond}.joblib')
        decisions[cond] = {'hyperparameters': tried, 'selected_C': best['C'], 'validation_macro_f1': best['validation_macro_f1'], 'final_fit_seconds': fitted_seconds}
    (out / 'selection_before_test.json').write_text(
        json.dumps({'seed': seed, 'train_question_groups': train['group'].nunique(),
                    'fit_groups': sub['group'].nunique(), 'validation_groups': val['group'].nunique(),
                    'decisions': decisions}, indent=2), encoding='utf-8')
    # Only now open the official test evaluations.
    metrics, predictions = {}, {}
    for split in ('test_ua', 'test_uq', 'test_ud'):
        test = prepare(frames[split])
        metrics[split] = {}
        predictions[split] = {}
        if split in ('test_uq', 'test_ud') and set(train['group']) & set(test['group']):
            raise RuntimeError(f'{split} unexpectedly overlaps train questions')
        for cond, model in fitted.items():
            start = time.perf_counter()
            pred = np.asarray(model.predict(input_text(test, cond)))
            elapsed = time.perf_counter() - start
            predictions[split][cond] = pred
            metrics[split][cond] = {**score(test['target'], pred),
                     'n_rows': len(test), 'n_question_groups': test['group'].nunique(),
                     'prediction_seconds': elapsed,
                     'confusion_matrix': confusion_matrix(test['target'], pred, labels=LABELS).tolist(),
                     'per_class': classification_report(test['target'], pred, labels=LABELS,
                                                      output_dict=True, zero_division=0)}
            pd.DataFrame({'id': test['id'].astype(str), 'true': test['target'], 'predicted': pred}).to_csv(out / f'predictions_{split}_{cond}.csv', index=False)
        metrics[split]['paired_context_gain'] = grouped_bootstrap_delta(
            test, predictions[split]['B1'], predictions[split]['B2'], seed=seed)
    result = {'dataset': 'SciEntsBank', 'target': 'derived-4-class', 'labels': LABELS,
              'seed': seed, 'synthetic_data': (data_dir / 'SYNTHETIC_DEMO.json').exists(),
              'audit_status': check['status'], 'audit_warnings': check['warnings'],
              'test_locked_until_after_validation': True,
              'model_selection': decisions, 'metrics': metrics,
              'limits': ['No model-based cognitive-state inference',
                         'Question context is an input ablation, not a causal educational treatment',
                         'Label Other merges irrelevant and non_domain',
                         'Test UQ is the predeclared primary split; avoid tuning on any official test']}
    (out / 'baseline_results.json').write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding='utf-8')
    return result


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--data-dir', type=Path, default=Path('data/raw'))
    p.add_argument('--out', type=Path, default=Path('results/lexical'))
    p.add_argument('--seed', type=int, default=20261009)
    p.add_argument('--allow-audit-warnings', action='store_true')
    a = p.parse_args()
    r = run(a.data_dir, a.out, a.seed, a.allow_audit_warnings)
    print('TEST-UQ (' + ('SYNTHETIC TEST, NOT SCIENCE' if r.get('synthetic_data') else 'input dataset') + '):', {k: v['macro_f1'] for k,v in r['metrics']['test_uq'].items() if k in CONDITIONS})
    print('B2-B1:', r['metrics']['test_uq']['paired_context_gain'])
