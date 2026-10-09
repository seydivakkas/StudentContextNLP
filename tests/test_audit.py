from pathlib import Path
import sys

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from audit_dataset import LABEL_MAP, SPLITS, audit, canonical_label, normalize


def test_labels():
    assert canonical_label(0) == 'correct'
    assert canonical_label('2') == 'partially_correct_incomplete'
    assert LABEL_MAP[canonical_label('non-domain')] == 'Other'
    with pytest.raises((ValueError, KeyError)):
        canonical_label('unsupported')


def fake_frame(question: str, answer: str = 'Answer', label: int = 0) -> pd.DataFrame:
    return pd.DataFrame([{'id': 'id1', 'question': question, 'reference_answer': 'Reference', 'student_answer': answer, 'label': label}])


def test_question_split_overlap_detected():
    frames = {k: fake_frame(f'Q_{k}') for k in SPLITS}
    frames['test_uq'] = fake_frame('Q_train')
    result = audit(frames)
    assert result['status'] == 'FAIL'
    assert result['cross_split']['test_uq']['question_overlap_with_train'] == 1


def test_no_question_overlap():
    frames = {k: fake_frame(f'Q_{k}') for k in SPLITS}
    result = audit(frames)
    assert not result['fatal_errors']
    assert result['unique_questions_all_splits'] == 4


def test_duplicate_and_conflict():
    frames = {k: fake_frame(f'Q_{k}') for k in SPLITS}
    frames['train'] = pd.concat([fake_frame('Q_train', 'Same', 0), fake_frame('Q_train', 'Same', 1)], ignore_index=True)
    result = audit(frames)
    assert result['summary']['train']['exact_duplicate_triples_extra_rows'] == 1
    assert result['summary']['train']['conflicting_answer_triples'] == 1


def test_normalization():
    assert normalize('  HELLO\n World  ') == 'hello world'
