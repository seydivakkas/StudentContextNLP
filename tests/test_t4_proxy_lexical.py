"""Synthetic T4 protocol tests. No model-performance or student-data claims."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from train_lexical import LABELS
from run_t4_proxy_lexical import (
    validate_tr_frame, fixed_group_partition, _macro_by_clusters,
)


def toy_frames():
    en = pd.DataFrame({
        "id": ["a", "b", "c", "d"],
        "label": [0, 1, 2, 3],
        "question": ["Which wire?", "Which bulb?", "Why evaporate?", "Why erosion?"],
        "reference_answer": ["wire", "bulb", "evaporate", "erosion"],
        "student_answer": ["copper", "no", "warmth", "wind"],
    })
    tr = pd.DataFrame({
        "id": en["id"].tolist(),
        "label": ["0", "1", "2", "3"],
        "label_status": ["UNVERIFIED_TRANSFER"] * 4,
        "translation_scope": ["FULL_CANDIDATE"] * 4,
        "question": ["Hangi tel?", "Hangi ampul?", "Neden buharlaşır?", "Neden aşınır?"],
        "reference_answer": ["tel", "ampul", "buharlaşır", "aşınır"],
        "student_answer": ["bakır", "hayır", "ısı", "rüzgâr"],
        "source_question_en": en["question"].tolist(),
        "source_reference_answer_en": en["reference_answer"].tolist(),
        "source_student_answer_en": en["student_answer"].tolist(),
    })
    return en, tr


def test_transferred_labels_and_english_group_alignment_not_turkish():
    en, tr = toy_frames()
    frame = validate_tr_frame(en, tr, "train")
    assert frame["target"].tolist() == [
        "Correct", "Contradictory", "Incomplete", "Other"]
    assert frame["group"].tolist() == [q.lower() for q in en["question"]]
    assert frame["answer_text"].tolist()[1] == "hayır"


def test_changed_labels_source_text_or_gold_claim_are_rejected():
    en, tr = toy_frames()
    scenarios = [
        ("label", "4"), ("source_student_answer_en", "not actually in source"),
        ("source_question_en", "different English question"),
        ("label_status", "HUMAN_GOLD"),
        ("translation_scope", "PARTIAL_SMOKE"),
        ("student_answer", ""),
    ]
    for col, replacement in scenarios:
        bad = tr.copy()
        bad.loc[0, col] = replacement
        with pytest.raises(RuntimeError):
            validate_tr_frame(en, bad, "test_uq")


def test_question_group_partition_is_fixed_and_has_zero_overlap():
    rng = np.random.default_rng(20261011)
    # Large synthetic set to ensure each label appears in both partitions.
    q = [f"group {i}" for i in range(80)]
    df = pd.DataFrame({
        "group": [x for x in q for _ in range(3)],
        "target": [LABELS[i % 4] for i in range(80) for _ in range(3)],
    })
    ti, vi = fixed_group_partition(df)
    tj, vj = fixed_group_partition(df)
    assert np.array_equal(ti, tj)
    assert np.array_equal(vi, vj)
    assert not set(df.iloc[ti]["group"]) & set(df.iloc[vi]["group"])
    assert set(df.iloc[ti]["target"]) == set(LABELS)
    assert set(df.iloc[vi]["target"]) == set(LABELS)


def test_paired_cluster_context_gain_difference_in_difference():
    y = np.asarray(["Correct", "Correct", "Incomplete", "Incomplete",
                    "Contradictory", "Contradictory", "Other", "Other"])
    groups = np.asarray(["q1", "q1", "q2", "q2", "q3", "q3", "q4", "q4"])
    unchanged = np.asarray(["Correct"] * len(y))
    p = {
        "tr_v0_2:B1": unchanged,
        "tr_v0_2:B2": unchanged,
        "tr_v0_2_1:B1": unchanged,
        "tr_v0_2_1:B2": y,
    }
    a = _macro_by_clusters(y, p, groups, reps=40, seed=1)
    b = _macro_by_clusters(y, p, groups, reps=40, seed=1)
    assert abs(a["point"] - (1.0 - 0.1 * 2 / 5)) > 0  # no hard-coded F1 shortcut
    assert a["point"] > 0.6
    assert a == b
    assert a["cluster_count"] == 4
    assert len(a["percentile_95_ci"]) == 2
    assert a["percentile_95_ci"][0] <= a["percentile_95_ci"][1]


def test_only_original_english_labels_define_targets_even_if_tr_text_changes():
    en, tr = toy_frames()
    old = validate_tr_frame(en, tr, "train")
    revised = tr.copy()
    revised.loc[0, "question"] = "Başka sözcüklerle aynı bilim sorusu?"
    new = validate_tr_frame(en, revised, "train")
    assert old["target"].tolist() == new["target"].tolist()
    assert old["group"].tolist() == new["group"].tolist()
    assert old["question_text"].tolist() != new["question_text"].tolist()
