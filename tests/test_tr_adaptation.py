"""No actual student data or downloaded translation model used by these tests."""
import json
from pathlib import Path
import sys

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from audit_dataset import SPLITS
from tr_adaptation.quality import review_flags
from tr_adaptation.pipeline import translate_frames
from sample_translation_review import build_sample
from evaluate_translation_reviews import evaluate


def make_frames(n=12):
    frames = {}
    for split in SPLITS:
        prefix = {'train': 'train', 'test_ua': 'train', 'test_uq': 'unseen', 'test_ud': 'other'}[split]
        frames[split] = pd.DataFrame([{
            'id': f'{split}_{i}', 'question': f'{prefix}_question_{i%4}',
            'reference_answer': 'Water does not evaporate at a fixed temperature. 12 degrees.',
            'student_answer': f'Evaporation happens {i} times.',
            'label': i % 5,
        } for i in range(n)])
    return frames


MODEL = {'source_code': 'en', 'target_code': 'tr', 'package_sha256': '1234567890abcdef',
         'package_version': 'test0', 'package_name': 'FAKE-NOT-A-MODEL'}


def fake_tr(s):
    return 'Türkçe çeviri: ' + s


def test_flags_are_advisory():
    assert 'NEGATION_REVIEW' in review_flags('This is not hot.', 'Bu sıcaktır.')
    assert 'NUMBER_MISMATCH_REVIEW' in review_flags('12 degrees', 'on iki derece')
    assert review_flags('Hello', 'Merhaba') == []
    assert 'EMPTY_TRANSLATION' in review_flags('Hello', '')


def test_full_four_splits_with_provenance(tmp_path):
    frames = make_frames()
    # Synthetic labels deliberately differ from publication -> warnings explicitly reviewed.
    result = translate_frames(frames, {}, tmp_path, fake_tr, MODEL, allow_audit_warnings=True)
    assert result['total_translated_rows'] == sum(map(len, frames.values()))
    assert result['scope'] == 'FULL_CANDIDATE'
    assert result['projected_labels_are_gold'] is False
    for split, stem in [('train','train'),('test_ua','test-ua'),('test_uq','test-uq'),('test_ud','test-ud')]:
        d = pd.read_csv(tmp_path / f'{stem}.csv')
        assert len(d) == len(frames[split])
        assert set(d.label_status) == {'UNVERIFIED_TRANSFER'}
        assert (d.student_answer.str.startswith('Türkçe çeviri: ')).all()
    previous_count = result['unique_cached_texts']
    rerun = translate_frames(frames, {}, tmp_path, fake_tr, MODEL, allow_audit_warnings=True)
    assert rerun['new_unique_translations'] == 0
    assert rerun['unique_cached_texts'] == previous_count


def test_partial_output_does_not_claim_full(tmp_path):
    result = translate_frames(make_frames(), {}, tmp_path, fake_tr, MODEL,
                              limit_per_split=2, allow_audit_warnings=True)
    assert result['scope'] == 'PARTIAL_SMOKE'
    assert result['total_translated_rows'] == 8
    with pytest.raises(RuntimeError, match='tam aday veri'):
        build_sample(tmp_path, tmp_path / 'review', n=4)


def test_audit_fatal_is_not_bypassable(tmp_path):
    frames = make_frames()
    frames['test_uq'].loc[0, 'question'] = frames['train'].iloc[0]['question']
    with pytest.raises(RuntimeError, match='P0 fatal'):
        translate_frames(frames, {}, tmp_path, fake_tr, MODEL, allow_audit_warnings=True)


def test_different_model_refuses_resume(tmp_path):
    translate_frames(make_frames(), {}, tmp_path, fake_tr, MODEL, allow_audit_warnings=True)
    new = dict(MODEL, package_sha256='different')
    with pytest.raises(RuntimeError, match='farklı model'):
        translate_frames(make_frames(), {}, tmp_path, fake_tr, new, allow_audit_warnings=True)


def test_full_review_templates_are_independent(tmp_path):
    translate_frames(make_frames(20), {}, tmp_path / 'tr', fake_tr, MODEL, allow_audit_warnings=True)
    result = build_sample(tmp_path / 'tr', tmp_path / 'review', n=24, seed=4)
    assert result['actual_n'] == 24
    a = pd.read_csv(tmp_path / 'review' / 'review_A.csv', keep_default_na=False)
    b = pd.read_csv(tmp_path / 'review' / 'review_B.csv', keep_default_na=False)
    assert len(a) == len(b) == 24
    assert list(a.item_key) == list(b.item_key)
    assert (a.meaning_preserved == '').all()


def test_review_agreement_requires_complete_forms():
    a = pd.DataFrame({'item_key': ['x', 'y', 'z'], 'meaning_preserved': ['yes', 'no', 'yes'],
                      'error_preserved': ['yes', 'yes', 'no'],
                      'label_still_applicable': ['no', 'yes', 'yes'],
                      'correction_needed': ['no', 'yes', 'yes']})
    b = a.copy()
    result = evaluate(a, b)
    assert result['fields']['meaning_preserved']['agreement'] == 1
    assert result['validation_state'] != 'FULLY_VALIDATED'
    b.loc[0, 'meaning_preserved'] = ''
    with pytest.raises(ValueError, match='missing/invalid'):
        evaluate(a, b)


def test_no_external_inference_in_engine():
    from tr_adaptation.engine import ensure_model_manifest
    with pytest.raises(RuntimeError, match='manifesti eksik'):
        ensure_model_manifest(Path('/path/that/does/not/exist.json'), {})
