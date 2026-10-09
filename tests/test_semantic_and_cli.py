import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from audit_dataset import LABEL_MAP
from train_semantic import embedding_features, load_local_encoder, run as semantic_run
from compare_experiments import report
from predict import predict
from scripts.create_synthetic_fixture import build


class LocalFakeEncoder:
    """Deterministic offline encoder for architecture tests; no pretrained model claim."""
    def encode(self, sentences, **kwargs):
        def vec(s):
            out = np.zeros(12, dtype=np.float32)
            for token in s.lower().split():
                hashed = hashlib.sha256(token.encode()).digest()
                out[hashed[0] % 12] += 1 + (hashed[1] % 5) / 5
            return out / (np.linalg.norm(out) + 1e-8)
        return np.stack([vec(s) for s in sentences])


def test_local_encoder_missing_files_fail_closed(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_local_encoder(tmp_path / 'not-there')


def test_no_label_or_reference_in_semantic_features():
    encoder = LocalFakeEncoder()
    d = pd.DataFrame({'answer_text': ['hello there'], 'question_text': ['what is the process'],
                      'target': ['Correct'], 'reference_answer': ['SECRET_LABEL_SHOULD_NOT_BE_USED']})
    x = embedding_features(d, encoder)
    assert x['S1'].shape == (1, 12)
    assert x['S2'].shape == (1, 24)
    changed = d.copy()
    changed['target'] = 'Other'; changed['reference_answer'] = 'SOME COMPLETELY DIFFERENT REFERENCE'
    xx = embedding_features(changed, encoder)
    np.testing.assert_allclose(x['S1'], xx['S1'])
    np.testing.assert_allclose(x['S2'], xx['S2'])


def test_semantic_end_to_end_synthetic_without_model_download(tmp_path):
    raw = tmp_path / 'demo'
    build(raw, repeats=3)
    out = tmp_path / 'semantic'
    x = semantic_run(raw, out, tmp_path / 'not-really-used', encoder=LocalFakeEncoder(),
                     allow_warnings=True, candidates=(0.1, 1.0))
    assert x['synthetic_data']
    assert x['selected_before_official_tests']
    assert set(x['metrics']['test_uq']) == {'S1', 'S2', 'paired_context_gain'}
    assert (out / 'selection_before_test.json').exists()
    assert (out / 'S2.joblib').exists()
    assert x['metrics']['test_uq']['S1']['n_question_groups'] == 3


def test_cannot_predict_context_model_without_question(tmp_path):
    with pytest.raises(ValueError, match='soru'):
        predict(tmp_path / 'B2.joblib', 'My short answer', question='')


def test_compare_blocks_mixed_synthetic_real(tmp_path):
    a = tmp_path/'a.json'; b = tmp_path/'b.json'
    a.write_text(json.dumps({'seed': 5, 'synthetic_data': True, 'metrics': {'test_uq': {'B1': {'macro_f1': .3}, 'B2': {'macro_f1': .5}}}}))
    b.write_text(json.dumps({'seed': 5, 'synthetic_data': False, 'metrics': {}}))
    with pytest.raises(ValueError, match='Sentetik'):
        report(a, b, tmp_path/'out')


def test_compare_output_for_single_run(tmp_path):
    obj = {'seed': 10, 'synthetic_data': True, 'metrics': {}}
    for split in ['test_ua','test_uq','test_ud']:
        obj['metrics'][split] = {k: {'macro_f1': .3, 'weighted_f1': .4,
            'accuracy': .5, 'n_rows': 12} for k in ('B0','B1','B2','B3')}
    src = tmp_path / 'baseline_results.json'; src.write_text(json.dumps(obj))
    res = report(src, tmp_path/'missing.json', tmp_path/'out')
    assert res['data_kind'] == 'SYNTHETIC_SOFTWARE_TEST'
    assert (tmp_path/'out/model_comparison.csv').exists()
    assert res['lexical_question_context_gain'] == 0.0
