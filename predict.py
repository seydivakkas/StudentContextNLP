"""Predict from saved local sklearn models. No internet and no inference endpoints."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from train_semantic import embedding_features, load_local_encoder


def predict(model_file: Path, answer: str, question: str = '', model_dir: Path | None = None) -> dict:
    if not answer.strip():
        raise ValueError('Öğrenci açıklaması boş olamaz')
    cond = model_file.stem.upper()
    if cond not in ('B0', 'B1', 'B2', 'B3', 'S1', 'S2'):
        raise ValueError(f'Bilinmeyen model: {cond}')
    if cond in ('B2', 'B3', 'S2') and not question.strip():
        raise ValueError('Bu model için soru metni zorunlu')
    model = joblib.load(model_file)  # trusted local artifacts only; joblib/pickle executes code
    if cond.startswith('B'):
        from train_lexical import input_text
        df = pd.DataFrame({'answer_text': [answer], 'question_text': [question]})
        feat = input_text(df, cond)
    else:
        if model_dir is None:
            raise ValueError('Semantic model için --model-dir gerekli')
        encoder = load_local_encoder(model_dir)
        df = pd.DataFrame({'answer_text': [answer], 'question_text': [question]})
        feat = embedding_features(df, encoder)[cond]
    predicted = str(model.predict(feat)[0])
    result = {'model': cond, 'prediction': predicted, 'source': 'local_cpu'}
    if hasattr(model, 'predict_proba'):
        prob = np.asarray(model.predict_proba(feat)[0], dtype=float)
        if hasattr(model, 'classes_'):
            classes = list(model.classes_)
        else:
            classes = list(model.named_steps['logreg'].classes_)
        result['ranking'] = [{'label': str(classes[i]), 'probability': float(prob[i])}
                             for i in np.argsort(prob)[::-1]]
    return result


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--model', type=Path, required=True)
    p.add_argument('--answer', required=True)
    p.add_argument('--question', default='')
    p.add_argument('--model-dir', type=Path)
    a = p.parse_args()
    print(json.dumps(predict(a.model, a.answer, a.question, a.model_dir), indent=2, ensure_ascii=False))
