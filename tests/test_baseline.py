import json
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from train_lexical import (LABELS, create_model, grouped_bootstrap_delta,
                           input_text, prepare, run, score)

LABEL_IDS = (0, 2, 1, 3)
TOKENS = ('salt evaporates in water', 'has some half correct elements',
          'impossible contradicts facts', 'another unrelated topic')


def data_for_question(question, repeats=6):
    rows = []
    for c, text in zip(LABEL_IDS, TOKENS):
        for j in range(repeats):
            rows.append({'id': f'{question}-{c}-{j}', 'question': question,
                         'reference_answer': 'Reference text',
                         'student_answer': f'{text} unique {j} {question}', 'label': c})
    return pd.DataFrame(rows)


def test_label_mapping_and_context():
    f = prepare(data_for_question('A question?'))
    assert set(f.target) == set(LABELS)
    assert input_text(f, 'B1')[0] != input_text(f, 'B2')[0]
    assert all('A question?' in x for x in input_text(f, 'B3'))


def test_unseen_question_bootstrap_identical_models_zero_delta():
    f = prepare(data_for_question('Q1') )
    pred = f.target.to_numpy()
    out = grouped_bootstrap_delta(f, pred, pred, samples=60)
    assert out['delta_B2_minus_B1'] == 0
    assert out['percentile_95_ci'] == [0., 0.]


def test_same_four_classes_macro_f1_perfect():
    y = np.array(LABELS * 4)
    assert score(y, y)['macro_f1'] == 1.


def test_models_predict_local_text():
    f = prepare(data_for_question('Question one?'))
    for kind in ('B0','B1','B2','B3'):
        m = create_model(kind)
        m.fit(input_text(f,kind),f.target)
        assert len(m.predict(input_text(f,kind))) == len(f)


def test_p0_blocks_training_on_missing_files(tmp_path):
    with pytest.raises(FileNotFoundError):
        run(tmp_path/'missing', tmp_path/'out')


def test_p0_blocks_warnings_without_approval(tmp_path):
    raw = tmp_path/'raw'
    raw.mkdir()
    for sp,qs in [('train',('T1','T2','T3','T4','T5','T6','T7','T8')),
                  ('test_ua',('T1',)),('test_uq',('U1',)),('test_ud',('D1',))]:
        pd.concat([data_for_question(q,3) for q in qs]).to_csv(raw/f'{sp}.csv', index=False)
    with pytest.raises(RuntimeError,match='P0 WARNINGS'):
        run(raw,tmp_path/'results')


def test_full_synthetic_execution_and_group_safety(tmp_path):
    raw = tmp_path/'raw'
    raw.mkdir()
    for sp,qs in [('train',tuple(f'T{i}' for i in range(12))),
                  ('test_ua',('T0',)),('test_uq',('U0','U1')),('test_ud',('D0','D1'))]:
        pd.concat([data_for_question(q,3) for q in qs]).to_csv(raw/f'{sp}.csv',index=False)
    out = tmp_path/'results'
    r = run(raw,out,allow_warnings=True)
    assert set(r['metrics']) == {'test_ua','test_uq','test_ud'}
    assert r['test_locked_until_after_validation']
    assert set(r['metrics']['test_uq']) == {'B0','B1','B2','B3','paired_context_gain'}
    assert (out/'selection_before_test.json').exists()
    assert (out/'baseline_results.json').exists()
    assert (out/'B2.joblib').exists()
    assert r['metrics']['test_uq']['B2']['n_question_groups'] == 2
