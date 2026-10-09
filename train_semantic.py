"""Frozen local-encoder sentence embeddings + trainable logistic regression.

NO external inference, auth, API key, generative LLM or large-model fine tuning.
The encoder must already exist on local disk. All fitting happens on CPU.
"""
from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import GroupShuffleSplit

from audit_dataset import SPLITS, audit, read_split
from train_lexical import LABELS, grouped_bootstrap_delta, prepare, score

SEM_CONDITIONS = ('S1', 'S2')


def load_local_encoder(path: Path):
    """Fail closed if model weights absent. Network forbidden even by dependencies."""
    if not path.is_dir() or not (path / 'modules.json').exists():
        raise FileNotFoundError(f'Yerel SentenceTransformer bulunamadı: {path}. Önce model ağırlıklarını indir.')
    os.environ['HF_HUB_OFFLINE'] = '1'
    os.environ['TRANSFORMERS_OFFLINE'] = '1'
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise RuntimeError('Opsiyonel bağımlılık eksik: pip install -r requirements-semantic.txt') from exc
    return SentenceTransformer(str(path.resolve()), device='cpu', local_files_only=True, trust_remote_code=False)


def embedding_features(df: pd.DataFrame, encoder, batch_size: int = 32) -> dict[str, np.ndarray]:
    """Encode explanation and question separately, never use labels or references as features."""
    answers = encoder.encode(df['answer_text'].tolist(), batch_size=batch_size,
                             convert_to_numpy=True, normalize_embeddings=True, show_progress_bar=False)
    questions = encoder.encode(df['question_text'].tolist(), batch_size=batch_size,
                               convert_to_numpy=True, normalize_embeddings=True, show_progress_bar=False)
    a = np.asarray(answers, dtype=np.float32)
    q = np.asarray(questions, dtype=np.float32)
    if a.ndim != 2 or q.shape != a.shape or a.shape[0] != len(df):
        raise ValueError('Encoder beklenmedik embedding şekli döndürdü')
    if not np.isfinite(a).all() or not np.isfinite(q).all():
        raise ValueError('Encoder NaN/inf üretti')
    return {'S1': a, 'S2': np.concatenate((a, q), axis=1)}


def fitted_classifier(C: float, seed: int = 20261009) -> LogisticRegression:
    return LogisticRegression(C=C, max_iter=1200, random_state=seed)


def run(data_dir: Path, out: Path, local_model_dir: Path, seed: int = 20261009,
        allow_warnings: bool = False, encoder=None, candidates=(0.1, 1.0, 10.0)) -> dict:
    frames, paths = {}, {}
    for sp in SPLITS:
        frames[sp], paths[sp] = read_split(data_dir, sp)
    checked = audit(frames, paths)
    if checked['fatal_errors']:
        raise RuntimeError('P0 FAIL: ' + '; '.join(checked['fatal_errors']))
    if checked['warnings'] and not allow_warnings:
        raise RuntimeError('P0 WARNINGS: explicit approval required; ' + '; '.join(checked['warnings']))
    if encoder is None:
        encoder = load_local_encoder(local_model_dir)
    train = prepare(frames['train'])
    splitter = GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=seed)
    fit_idx, val_idx = next(splitter.split(train, groups=train['group']))
    if set(train.iloc[fit_idx].group) & set(train.iloc[val_idx].group):
        raise AssertionError('Question-group leakage in validation')
    if set(train.iloc[fit_idx].target) != set(LABELS) or set(train.iloc[val_idx].target) != set(LABELS):
        raise RuntimeError('Validation split has missing class; redesign grouping within train only')

    # Embed training text first. No test set used for C selection.
    features = embedding_features(train, encoder)
    decisions, fitted = {}, {}
    out.mkdir(parents=True, exist_ok=True)
    for cond in SEM_CONDITIONS:
        trials = []
        for c in candidates:
            clf = fitted_classifier(c, seed)
            clf.fit(features[cond][fit_idx], train.iloc[fit_idx].target)
            pred = clf.predict(features[cond][val_idx])
            trials.append({'C': float(c), 'validation_macro_f1': score(train.iloc[val_idx].target, pred)['macro_f1']})
        selected = sorted(trials, key=lambda x: (-x['validation_macro_f1'], x['C']))[0]
        begin = time.perf_counter()
        clf = fitted_classifier(selected['C'], seed)
        clf.fit(features[cond], train.target)
        seconds = time.perf_counter() - begin
        joblib.dump(clf, out / f'{cond}.joblib')
        fitted[cond] = clf
        decisions[cond] = {'validation_scores': trials, 'selected_C': selected['C'],
                           'validation_macro_f1': selected['validation_macro_f1'], 'classifier_fit_seconds': seconds}

    meta = {'seed': seed, 'data_version': 'nkazi/SciEntsBank', 'encoding': 'separate normalized embeddings',
            'model_dir': str(local_model_dir), 'train_groups': int(train.group.nunique()),
            'validation_groups': int(train.iloc[val_idx].group.nunique()), 'decisions': decisions,
            'synthetic_data': (data_dir / 'SYNTHETIC_DEMO.json').exists()}
    (out / 'selection_before_test.json').write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding='utf-8')

    test_metrics, predicts = {}, {}
    for sp in ('test_ua', 'test_uq', 'test_ud'):
        test = prepare(frames[sp])
        if sp in ('test_uq', 'test_ud') and set(train.group) & set(test.group):
            raise RuntimeError(f'{sp}: unseen-question assumption failed; train overlaps test')
        feats = embedding_features(test, encoder)
        test_metrics[sp], predicts[sp] = {}, {}
        for cond in SEM_CONDITIONS:
            started = time.perf_counter()
            pred = np.asarray(fitted[cond].predict(feats[cond]))
            duration = time.perf_counter() - started
            predicts[sp][cond] = pred
            test_metrics[sp][cond] = {**score(test.target, pred), 'n_rows': len(test),
                'n_question_groups': int(test.group.nunique()), 'prediction_seconds': duration,
                'confusion_matrix': confusion_matrix(test.target, pred, labels=LABELS).tolist(),
                'per_class': classification_report(test.target, pred, labels=LABELS,
                                                   output_dict=True, zero_division=0)}
            pd.DataFrame({'id': test.id.astype(str), 'true': test.target,
                          'predicted': pred}).to_csv(out / f'predictions_{sp}_{cond}.csv', index=False)
        gain = grouped_bootstrap_delta(test, predicts[sp]['S1'], predicts[sp]['S2'], seed=seed)
        test_metrics[sp]['paired_context_gain'] = {
            'delta_S2_minus_S1': gain['delta_B2_minus_B1'],
            'cluster_count': gain['cluster_count'], 'bootstrap_iterations': gain['bootstrap_iterations'],
            'percentile_95_ci': gain['percentile_95_ci'], 'interpretation': gain['interpretation']}
    result = {'dataset': 'SciEntsBank', 'target': 'derived-4-class', 'seed': seed,
        'model_type': 'frozen_local_embeddings_plus_logistic_regression',
        'model_dir': str(local_model_dir), 'synthetic_data': meta['synthetic_data'],
        'audit_status': checked['status'], 'audit_warnings': checked['warnings'],
        'selected_before_official_tests': True, 'model_selection': decisions,
        'metrics': test_metrics, 'limitations': ['No LLM API or hosted inference',
        'Context ablation is not a causal intervention', 'Encoder is frozen, only LR fitted',
        'Official tests are not for selecting models or hyperparameters']}
    (out / 'semantic_results.json').write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding='utf-8')
    return result


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--data-dir', type=Path, default=Path('data/raw'))
    p.add_argument('--out', type=Path, default=Path('results/semantic'))
    p.add_argument('--model-dir', type=Path, required=True)
    p.add_argument('--seed', type=int, default=20261009)
    p.add_argument('--allow-audit-warnings', action='store_true')
    args = p.parse_args()
    result = run(args.data_dir, args.out, args.model_dir, args.seed, args.allow_audit_warnings)
    print('Test-UQ S2-S1:', result['metrics']['test_uq']['paired_context_gain'])
