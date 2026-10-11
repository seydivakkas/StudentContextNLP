"""Synthetic-only tests for arithmetic and privacy of T4 metric audit."""
from __future__ import annotations

import json

import pytest

from audit_t4_results import audit, metrics_from_matrix
from train_lexical import LABELS, CONDITIONS


def fake_reports(tmp_path):
    original = tmp_path / "results" / "lexical" / "baseline_results.json"
    t4 = tmp_path / "results" / "t4_proxy_v021" / "t4_proxy_results.json"
    original.parent.mkdir(parents=True)
    t4.parent.mkdir(parents=True)
    supports = {
        "test_ua": [233, 113, 58, 136],
        "test_uq": [301, 175, 64, 193],
        "test_ud": [1917, 986, 417, 1242]
    }
    metrics = {}
    for split, ns in supports.items():
        cm = [[ns[i] if i == j else 0 for j in range(4)] for i in range(4)]
        derived = metrics_from_matrix(cm, "synthetic")
        metrics[split] = {}
        for variant in ("en", "tr_v0_2", "tr_v0_2_1"):
            values = {}
            for model in CONDITIONS:
                values[model] = {
                    "n_rows": sum(ns), "n_english_question_groups": 15,
                    "confusion_matrix": cm,
                    "per_class": {
                        label: dict(derived["per_class"][label]) for label in LABELS},
                    **{key: derived[key] for key in (
                        "macro_f1", "weighted_f1", "accuracy")},
                }
            if split == "test_uq":
                values["B2_minus_B1"] = {
                    "delta_B2_minus_B1": 0.0, "cluster_count": 15,
                    "bootstrap_iterations": 1000, "percentile_95_ci": [0.0, 0.0]
                }
            metrics[split][variant] = values
        if split == "test_uq":
            metrics[split]["repair_effect_on_context_gain"] = {
                "point": 0.0, "cluster_count": 15,
                "bootstrap_iterations": 1000, "percentile_95_ci": [0.0, 0.0]
            }
            metrics[split]["paired_TR_revision_deltas"] = {
                cond: {"delta_B2_minus_B1": 0.0, "cluster_count": 15,
                       "bootstrap_iterations": 1000,
                       "percentile_95_ci": [0.0, 0.0]}
                for cond in CONDITIONS
            }
    previous = {
        "seed": 20261009, "synthetic_data": False,  # fixture for guard ONLY
        "metrics": {"test_uq": {"B0": metrics["test_uq"]["en"]["B0"],
                                 "B1": metrics["test_uq"]["en"]["B1"],
                                 "B2": metrics["test_uq"]["en"]["B2"],
                                 "B3": metrics["test_uq"]["en"]["B3"]}}
    }
    selection = {
        "seed": 20261009,
        "group_basis": "Original English normalized question for all variants",
        "translation_repair_C_frozen_from_original_TR": True,
        "hyperparameter_selection_locked_before_any_test_metrics_computed": True,
        "condition_selected_C": {
            variant: {cond: {"selected_C": 1.0} for cond in CONDITIONS}
            for variant in ("en", "tr_v0_2", "tr_v0_2_1")
        },
    }
    report = {
        "stage": "T4_EN_TR_02_TR_021_LEXICAL_PROXY",
        "research_status": "EXPLORATORY_PROJECTED_LABEL_NOT_TURKISH_GOLD",
        "primary_split": "test_uq",
        "cluster_bootstrap_iterations": 1000,
        "original_english_labels_used_as_proxy_in_all_languages": True,
        "english_test_question_grouping": True,
        "training_selection": selection,
        "source_provenance": {"original_qa_rule_flags": 7412,
                               "patched_qa_rule_flags": 4926},
        "english_baseline_reproduction": {
            "prior_local_baseline_available": True,
            "same_seed": True, "all_within_1e-8": True,
            "test_uq_macro_f1_absolute_differences": {c: 0.0 for c in CONDITIONS},
        },
        "metrics": metrics,
    }
    original.write_text(json.dumps(previous), encoding="utf-8")
    t4.write_text(json.dumps(report), encoding="utf-8")
    return t4, original, report, previous


def test_synthetic_all_36_confusions_and_source_files_unchanged(tmp_path):
    t4, prior, *_ = fake_reports(tmp_path)
    before = (t4.read_bytes(), prior.read_bytes())
    out = tmp_path / "reports" / "metric_audit"
    result = audit(t4, prior, out)
    assert result["english_p1_reproduced_within_1e_8"] is True
    assert result["all_3x4x3_model_confusion_matrices_verified"] is True
    assert result["test_uq_english_support_per_class"]["Correct"] == 301
    assert result["primary_difference_in_context_ablation"]["point"] == 0
    assert (out / "test_uq_per_class_f1.csv").is_file()
    assert (out / "test_uq_paired_tr_deltas.csv").is_file()
    assert before == (t4.read_bytes(), prior.read_bytes())
    with pytest.raises(RuntimeError, match="exists"):
        audit(t4, prior, out)


def test_corrupted_macro_f1_rejected_before_writes(tmp_path):
    t4, prior, report, _ = fake_reports(tmp_path)
    report["metrics"]["test_uq"]["tr_v0_2_1"]["B2"]["macro_f1"] = 0.2
    t4.write_text(json.dumps(report), encoding="utf-8")
    out = tmp_path / "reports" / "metric_audit"
    with pytest.raises(RuntimeError, match="Metric inconsistency"):
        audit(t4, prior, out)
    assert not out.exists()


def test_false_p1_1e8_flag_rejected(tmp_path):
    t4, prior, report, _ = fake_reports(tmp_path)
    report["english_baseline_reproduction"]["all_within_1e-8"] = False
    t4.write_text(json.dumps(report), encoding="utf-8")
    with pytest.raises(RuntimeError, match="P1.*flag"):
        audit(t4, prior, tmp_path / "reports" / "metric_audit")


def test_label_support_mismatch_rejected(tmp_path):
    t4, prior, report, _ = fake_reports(tmp_path)
    mat = report["metrics"]["test_ua"]["tr_v0_2"]["B2"]["confusion_matrix"]
    mat[0][0] -= 1
    mat[1][1] += 1
    t4.write_text(json.dumps(report), encoding="utf-8")
    with pytest.raises(RuntimeError, match="Label support differs"):
        audit(t4, prior, tmp_path / "reports" / "metric_audit")


def test_t4_json_indicates_no_human_gold():
    cm = [[1, 1, 0, 0], [0, 2, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]
    d = metrics_from_matrix(cm, "synthetic")
    assert d["macro_f1"] == pytest.approx(((2 / 3) + 0.8 + 1.0 + 1.0) / 4)
    assert d["total"] == 6
