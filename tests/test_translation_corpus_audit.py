"""Synthetic, offline regression tests for the 10,804-row translation corpus scan.

These fixtures are fabricated and must NEVER be used as scientific results.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import pandas as pd
import pytest

from audit_dataset import SPLITS, EXPECTED
from download_data import REVISION
from audit_translation_quality import scan_rows
from audit_translation_corpus import concept_of, Group, _compare_sample, run

STEM = {'train': 'train', 'test_ua': 'test-ua', 'test_uq': 'test-uq',
        'test_ud': 'test-ud'}
FIELDS = ('question', 'reference_answer', 'student_answer')


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _make_fixture(root: Path):
    source = root / 'data' / 'raw'
    translated = root / 'data' / 'tr_v0_2'
    review = root / 'reports' / 'tr_review'
    blind = review / 'blind_stage1'
    qa = root / 'reports' / 'tr_auto_qa_v03'
    for folder in (source, translated, blind, qa):
        folder.mkdir(parents=True)
    sample = []
    source_hashes, split_info = {}, {}

    for split in SPLITS:
        n = sum(EXPECTED[split].values())
        frame = pd.DataFrame({
            'id': [f'{split}_{i}' for i in range(n)],
            'question': ['Does the bulb light up?'] * n,
            'reference_answer': ['The bulb lights in a circuit.'] * n,
            'student_answer': ['The bulb is not on.'] * n,
            'label': [0] * n,
        })
        src_file = source / f'{STEM[split]}-00001.csv'
        frame.to_csv(src_file, index=False)
        source_hashes[split] = _sha(src_file)
        output = translated / f'{STEM[split]}.csv'
        rows = []
        for i, row in frame.iterrows():
            item = {
                'id': row['id'], 'question': 'Otobüs yanıyor mu?',
                'reference_answer': 'Otobüs devrede yanar.',
                'student_answer': 'Otobüs yanmıyor.',
                'label': '0',
                'source_question_en': row['question'],
                'source_reference_answer_en': row['reference_answer'],
                'source_student_answer_en': row['student_answer'],
                'label_status': 'UNVERIFIED_TRANSFER',
                'translation_scope': 'FULL_CANDIDATE',
                'quality_flags': '[]'
            }
            rows.append(item)
            if i < 60:
                sample.append({'item_key': f'{split}:{i}',
                               **{x: item[x] for x in (
                                   'source_question_en', 'question',
                                   'source_reference_answer_en', 'reference_answer',
                                   'source_student_answer_en', 'student_answer')}})
        pd.DataFrame(rows).to_csv(output, index=False)
        split_info[split] = {
            'source_rows': n, 'translated_rows': n,
            'output_sha256': _sha(output)
        }

    (source / 'file_manifest.json').write_text(
        json.dumps({'revision': REVISION,
                    'files': [{'filename': f'{STEM[s]}-00001.csv',
                               'sha256': source_hashes[s]} for s in SPLITS]}),
        encoding='utf-8'
    )
    model_key = 'FAKE_SYNTHETIC_MODEL_KEY'
    (translated / 'translation_manifest.json').write_text(
        json.dumps({
            'scope': 'FULL_CANDIDATE',
            'validation_state': 'UNVERIFIED_MACHINE_TRANSLATION',
            'projected_labels_are_gold': False,
            'total_translated_rows': 10804,
            'model': {'package_sha256': 'synthetic-not-a-real-model'},
            'model_key': model_key,
            'source_file_sha256': source_hashes,
            'splits': split_info,
        }), encoding='utf-8'
    )
    (review / 'review_manifest.json').write_text(
        json.dumps({'source_manifest_model_key': model_key}), encoding='utf-8'
    )
    blind_file = blind / 'review_A_blind.csv'
    pd.DataFrame(sample).to_csv(blind_file, index=False, encoding='utf-8-sig')
    flags, queue, summary = scan_rows(sample)
    summary['analysis_type'] = 'OFFLINE_HEURISTIC_TRANSLATION_TRIAGE'
    summary['input_sha256'] = _sha(blind_file)
    summary_path = qa / 'qa_summary.json'
    summary_path.write_text(json.dumps(summary), encoding='utf-8')
    blind_manifest = blind / 'blind_manifest.json'
    blind_manifest.write_text(json.dumps({
        'n_items': 240, 'outputs': {'A': {'sha256': _sha(blind_file)}}
    }), encoding='utf-8')
    return source, translated, blind_file, summary_path, blind_manifest


def test_source_concept_merges_related_rules():
    assert concept_of('BULB_AS_BUS') == 'bulb'
    assert concept_of('TERM_NOT_EVIDENT:bulb_in_circuits') == 'bulb'
    assert concept_of('MILLILITER_AS_LITER') == 'milliliter'
    assert concept_of('NUMBER_CHANGED') == 'numbers'
    assert concept_of('CUSTOM_RULE') == 'other:CUSTOM_RULE'


def test_group_separates_occurrences_from_distinct_evidence():
    group = Group()
    flag = {
        'item_key': 'train:0', 'field': 'question', 'priority': 'HIGH',
        'rule': 'BULB_AS_BUS', 'source_en': 'The bulb.', 'target_tr': 'Otobüs.'
    }
    group.record(flag)
    group.record({**flag, 'item_key': 'train:1'})
    result = group.result('bulb')
    assert result['flag_occurrences'] == 2
    assert result['distinct_review_rows'] == 2
    assert result['distinct_source_target_field_pairs'] == 1


def test_frozen_sample_rule_drift_fails_closed():
    previous = dict(rows=240, high_priority_rows=50, medium_priority_rows=60,
                    unflagged_rows=130, total_flags=200,
                    rule_counts={'BULB_AS_BUS': 200})
    _compare_sample(previous, previous)
    with pytest.raises(RuntimeError, match='drift'):
        _compare_sample({**previous, 'total_flags': 201}, previous)


def test_full_offline_synthetic_pipeline_and_no_overwrite(tmp_path):
    source, translated, sample, summary, manifest = _make_fixture(tmp_path)
    tracked = [sample, summary, manifest, translated / 'train.csv']
    original = [_sha(x) for x in tracked]
    out = tmp_path / 'reports' / 'full_qa'
    data = run(translated, source, sample, summary, out, manifest)
    assert data['input_rows'] == 10804
    assert data['frozen_sample_recheck']['rows'] == 240
    assert data['no_corrections_applied'] is True
    assert data['no_gold_data'] is True
    assert data['high_priority_rows'] == 10804
    assert data['medium_priority_rows'] == 0
    assert data['concept_counts']['bulb'] >= 10804
    assert data['repeated_evidence_cases'] >= 1
    assert [_sha(x) for x in tracked] == original
    assert (out / 'concept_summary.csv').is_file()
    assert (out / 'concept_by_split.csv').is_file()
    assert (out / 'repeated_evidence.csv').is_file()
    assert (out / 'full_translation_flags.csv').is_file()
    with pytest.raises(RuntimeError, match='Output or staging'):
        run(translated, source, sample, summary, out, manifest)


def test_deny_output_inside_translation_or_source(tmp_path):
    source, translated, sample, summary, manifest = _make_fixture(tmp_path)
    with pytest.raises(RuntimeError, match='Output'):
        run(translated, source, sample, summary, translated / 'wrong', manifest)


def test_source_csv_hash_tampering_blocks_before_output(tmp_path):
    source, translated, sample, summary, manifest = _make_fixture(tmp_path)
    with (translated / 'train.csv').open('a', encoding='utf-8') as fp:
        fp.write('\n')
    out = tmp_path / 'reports' / 'tampered'
    with pytest.raises(RuntimeError, match='Translation hash changed'):
        run(translated, source, sample, summary, out, manifest)
    assert not out.exists()
