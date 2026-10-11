"""Synthetic v0.2.1 patch planning and exact-pair application regression tests.

Artificial text and labels only; NO real students or translation weights.
"""
from __future__ import annotations

import csv
import hashlib
import json

import pytest

from audit_dataset import SPLITS, EXPECTED
from prioritize_translation_issues import CLUSTER_FIELDS, STATE, file_sha
from prepare_translation_patch_plan import prepare
from apply_translation_patch_plan import apply, load_patch_proposals

STEMS = {"train": "train", "test_ua": "test-ua",
         "test_uq": "test-uq", "test_ud": "test-ud"}
FIELDS = [
    "id", "question", "reference_answer", "student_answer", "label",
    "source_question_en", "source_reference_answer_en", "source_student_answer_en",
    "quality_flags", "label_status", "translation_scope",
]
OLD = "Otobüs yanar."
SOURCE = "The bulb lights."
NEW = "Ampul yanar."


def hashed(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def make_fixtures(tmp_path):
    base = tmp_path / "reports"
    priority = base / "tr_auto_priority_v01"
    full = base / "tr_auto_full_v01"
    data_dir = tmp_path / "data" / "tr_v0_2"
    for d in (priority, full, data_dir):
        d.mkdir(parents=True)

    sha_pair = hashed("question\0" + SOURCE + "\0" + OLD)
    cluster_id = hashed("bulb\0question\0" + sha_pair)
    cluster = {
        "cluster_id": cluster_id, "concept": "bulb", "field": "question",
        "priority_tier": "P2_SPECIFIC_TECHNICAL_TERM",
        "source_en": SOURCE, "target_tr": OLD,
        "source_target_sha256": sha_pair, "rule_types": "BULB_AS_BUS",
        "rule_occurrences": "2", "affected_distinct_rows": "2",
        "affected_splits": "train", "split_counts": '{"train":2}',
        "high_rule_occurrences": "2", "candidate_state": STATE,
        "auto_apply": "false",
    }
    p = priority / "root_cause_clusters.csv"
    with p.open("w", newline="", encoding="utf-8-sig") as fp:
        w = csv.DictWriter(fp, fieldnames=CLUSTER_FIELDS)
        w.writeheader()
        w.writerow(cluster)

    split_info = {}
    for split in SPLITS:
        n = sum(EXPECTED[split].values())
        file = data_dir / (STEMS[split] + ".csv")
        with file.open("w", newline="", encoding="utf-8-sig") as fp:
            w = csv.DictWriter(fp, fieldnames=FIELDS)
            w.writeheader()
            for i in range(n):
                affected = split == "train" and i < 2
                w.writerow({
                    "id": f"{split}:{i}",
                    "question": OLD if affected else "Su akışkandır.",
                    "reference_answer": "Ampul ışık verir.",
                    "student_answer": "Evet.",
                    "label": "0",
                    "source_question_en": SOURCE if affected else "Water is liquid.",
                    "source_reference_answer_en": "The bulb lights.",
                    "source_student_answer_en": "Yes.",
                    "quality_flags": "[]",
                    "label_status": "UNVERIFIED_TRANSFER",
                    "translation_scope": "FULL_CANDIDATE",
                })
        split_info[split] = {"source_rows": n, "translated_rows": n,
                             "output_sha256": file_sha(file)}
    src = {
        "scope": "FULL_CANDIDATE",
        "validation_state": "UNVERIFIED_MACHINE_TRANSLATION",
        "projected_labels_are_gold": False,
        "total_translated_rows": 10804, "total_source_rows": 10804,
        "splits": split_info, "source_dataset": "FAKE-SYNTHETIC",
        "model": {"package_sha256": "TEST-ONLY"},
        "model_key": "FAKE-MODEL",
        "source_file_sha256": {k: "SYNTHETIC" for k in SPLITS},
        "source_p0_status": "PASS_WITH_WARNINGS",
    }
    src_file = data_dir / "translation_manifest.json"
    src_file.write_text(json.dumps(src), encoding="utf-8")
    qa_file = full / "full_qa_summary.json"
    qa_file.write_text(json.dumps({
        "source_translation_manifest_sha256": file_sha(src_file),
        "source_csv_sha256": {s: split_info[s]["output_sha256"] for s in SPLITS},
    }), encoding="utf-8")
    priority_meta = {
        "stage": "T3_AUTO_ROOT_CAUSE_PRIORITIZATION",
        "status": STATE, "full_corpus_rows": 10804,
        "full_corpus_flags": 7412,
        "no_source_changes": True, "no_gold_labels": True,
        "outputs": {"root_cause_clusters.csv": file_sha(p)},
        "distinct_concept_field_source_target_clusters": 1,
        "input_full_qa_sha256": file_sha(qa_file),
    }
    (priority / "root_cause_manifest.json").write_text(
        json.dumps(priority_meta), encoding="utf-8")
    return priority, full, data_dir, cluster


def annotate_patch(plan_dir, replacement=NEW):
    file = plan_dir / "patch_candidates.csv"
    with file.open(newline="", encoding="utf-8-sig") as fp:
        reader = csv.DictReader(fp)
        rows, names = list(reader), reader.fieldnames
    rows[0]["decision"] = "APPLY_EXPLORATORY"
    rows[0]["proposed_tr"] = replacement
    rows[0]["curation_origin"] = "AI_DRAFT"
    rows[0]["evidence_note"] = "English bulb is a lamp, not a vehicle."
    with file.open("w", newline="", encoding="utf-8-sig") as fp:
        writer = csv.DictWriter(fp, fieldnames=names)
        writer.writeheader()
        writer.writerows(rows)


def test_patch_plan_only_blank_and_safe(tmp_path):
    priority, full, data, evidence = make_fixtures(tmp_path)
    plan = tmp_path / "reports" / "plan"
    meta = prepare(priority, plan, limit=10, min_rows=2)
    assert meta["candidate_count"] == 1
    assert meta["applied_edits"] == 0 and not meta["human_verified"]
    with (plan / "patch_candidates.csv").open(newline="", encoding="utf-8-sig") as fp:
        rows = list(csv.DictReader(fp))
    assert rows[0]["decision"] == "PENDING"
    assert rows[0]["proposed_tr"] == ""
    assert rows[0]["cluster_id"] == evidence["cluster_id"]
    with pytest.raises(FileExistsError):
        prepare(priority, plan)
    with pytest.raises(ValueError, match="No APPLY_EXPLORATORY"):
        apply(priority, plan, data, tmp_path / "data" / "tr_v0_2_1")


def test_exact_pair_patch_only_new_version_and_label_integrity(tmp_path):
    priority, full, data, evidence = make_fixtures(tmp_path)
    plan = tmp_path / "reports" / "plan"
    prepare(priority, plan)
    annotate_patch(plan)
    orig = {s: file_sha(data / (STEMS[s] + ".csv")) for s in SPLITS}
    output = tmp_path / "data" / "tr_v0_2_1"
    result = apply(priority, plan, data, output)
    assert result["approved_exploratory_pair_patches"] == 1
    assert result["edited_distinct_rows"] == 2
    assert result["edited_field_occurrences"] == 2
    assert result["total_translated_rows"] == 10804
    assert result["projected_labels_are_gold"] is False
    assert not result["human_validated"]
    assert {s: file_sha(data / (STEMS[s] + ".csv")) for s in SPLITS} == orig
    with (output / "train.csv").open(newline="", encoding="utf-8-sig") as fp:
        rows = list(csv.DictReader(fp))
    assert len(rows) == 4969
    assert [rows[0]["question"], rows[1]["question"]] == [NEW, NEW]
    assert rows[2]["question"] == "Su akışkandır."
    assert rows[0]["source_question_en"] == SOURCE
    assert rows[0]["label"] == "0"
    assert rows[0]["label_status"] == "UNVERIFIED_TRANSFER"
    assert (output / "patch_audit.csv").is_file()
    with pytest.raises(FileExistsError):
        apply(priority, plan, data, output)


def test_unfixed_scientific_rule_is_rejected(tmp_path):
    priority, full, data, evidence = make_fixtures(tmp_path)
    plan = tmp_path / "reports" / "plan"
    prepare(priority, plan)
    annotate_patch(plan, replacement="Otobüs bir araçtır.")
    out = tmp_path / "data" / "tr_v0_2_1"
    with pytest.raises(ValueError, match="still triggers"):
        apply(priority, plan, data, out)
    assert not out.exists()


def test_tampering_and_unexpected_inputs_fail_closed(tmp_path):
    priority, full, data, evidence = make_fixtures(tmp_path)
    plan = tmp_path / "reports" / "plan"
    prepare(priority, plan)
    annotate_patch(plan)
    target = data / "train.csv"
    with target.open("a", encoding="utf-8") as fp:
        fp.write("\n")
    out = tmp_path / "data" / "v2_1"
    with pytest.raises(ValueError, match="SHA mismatch"):
        apply(priority, plan, data, out)
    assert not out.exists()


def test_no_approved_patch_when_annotation_is_blank(tmp_path):
    priority, full, data, evidence = make_fixtures(tmp_path)
    plan = tmp_path / "reports" / "plan"
    prepare(priority, plan)
    with pytest.raises(ValueError, match="No APPLY_EXPLORATORY"):
        load_patch_proposals(priority, plan, data)
