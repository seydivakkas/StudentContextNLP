"""Synthetic grouping tests, not evidence of real translation error rates."""
from __future__ import annotations

from collections import Counter
import csv
import json
import hashlib

import pytest

from prioritize_translation_issues import aggregate, run, STATE


def row(key, rule, concept, field="question", source="The bulb.",
        target="Otobüs.", priority="HIGH"):
    split = key.split(":")[0]
    return {
        "item_key": key, "split": split, "field": field,
        "priority": priority, "rule": rule, "concept": concept,
        "reason_tr": "Synthetic suspected mistake",
        "source_en": source, "target_tr": target, "status": STATE,
    }


def fake_report(flags, high_rows, med_rows):
    rules = Counter(f["rule"] for f in flags)
    concepts = Counter(f["concept"] for f in flags)
    fields = Counter(f["field"] for f in flags)
    by_split = {}
    for split, n in (("train", 4969), ("test_ua", 540),
                     ("test_uq", 733), ("test_ud", 4562)):
        ss = [x for x in flags if x["split"] == split]
        by_split[split] = {
            "rows": n, "flags": len(ss),
            "high_priority_rows": len({x["item_key"] for x in ss
                                       if x["item_key"] in high_rows}),
            "medium_priority_rows": len({x["item_key"] for x in ss
                                         if x["item_key"] in med_rows}),
        }
    return {
        "stage": "T3_AUTO_FULL_CORPUS_TRIAGE",
        "status": STATE, "input_rows": 10804,
        "input_splits": by_split,
        "high_priority_rows": len(high_rows),
        "medium_priority_rows": len(med_rows),
        "candidate_flagged_rows": len(high_rows | med_rows),
        "total_flags": len(flags),
        "rule_counts": dict(rules), "concept_counts": dict(concepts),
        "source_field_counts": dict(fields),
        "no_gold_data": True, "no_corrections_applied": True,
    }


def example():
    flags = [
        row("train:1", "BULB_AS_BUS", "bulb"),
        row("train:1", "TERM_NOT_EVIDENT:bulb_in_circuits", "bulb"),
        row("train:2", "BULB_AS_BUS", "bulb"),
        row("test_uq:0", "MILLILITER_AS_LITER", "milliliter",
            source="Two milliliters.", target="İki litre."),
        row("test_ud:6", "NEGATION_NOT_EVIDENT", "negation",
            source="It is not solid.", target="Sağlamdır.", priority="MEDIUM"),
    ]
    return flags, fake_report(flags, {"train:1", "train:2", "test_uq:0"}, {"test_ud:6"})


def test_root_cause_groups_repeated_rows_and_multiple_rules():
    flags, report = example()
    clusters, concepts, manifest = aggregate(flags, report)
    assert manifest["full_corpus_flags"] == 5
    assert manifest["full_corpus_flagged_candidates"] == 4
    assert manifest["no_source_changes"] and manifest["no_gold_labels"]
    assert len(clusters) == 3
    bulb = next(x for x in clusters if x["concept"] == "bulb")
    assert bulb["rule_occurrences"] == 3
    assert bulb["affected_distinct_rows"] == 2
    assert set(bulb["rule_types"].split("|")) == {
        "BULB_AS_BUS", "TERM_NOT_EVIDENT:bulb_in_circuits"}
    assert bulb["priority_tier"] == "P2_SPECIFIC_TECHNICAL_TERM"
    assert next(x for x in concepts if x["concept"] == "bulb")[
        "distinct_source_target_field_pairs"] == 1
    assert clusters[0]["concept"] == "milliliter"
    assert manifest["clusters_with_repeated_rows"] == 1


def test_split_mismatch_or_rule_drift_is_blocked():
    flags, report = example()
    changed = [dict(x) for x in flags]
    changed[0]["concept"] = "numbers"
    with pytest.raises(ValueError, match="mapping"):
        aggregate(changed, report)
    changed = [dict(x) for x in flags]
    changed[0]["item_key"] = "test_uq:1"
    with pytest.raises(ValueError, match="split"):
        aggregate(changed, report)
    changed = [dict(x) for x in flags]
    changed[0]["priority"] = "MEDIUM"
    with pytest.raises(ValueError, match="priority"):
        aggregate(changed, report)


def test_full_report_integrity_no_overwrites(tmp_path):
    flags, report = example()
    qa = tmp_path / "full_qa"
    qa.mkdir()
    flag_file = qa / "full_translation_flags.csv"
    with flag_file.open("w", encoding="utf-8-sig", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=list(flags[0]))
        writer.writeheader()
        writer.writerows(flags)
    digest = hashlib.sha256(flag_file.read_bytes()).hexdigest()
    report["outputs"] = {"full_translation_flags.csv": digest}
    (qa / "full_qa_summary.json").write_text(json.dumps(report), encoding="utf-8")
    pristine = flag_file.read_bytes()
    out = tmp_path / "priority"
    result = run(qa, out)
    assert result["full_corpus_flags"] == 5
    assert result["no_source_changes"] is True
    assert flag_file.read_bytes() == pristine
    assert (out / "root_cause_clusters.csv").is_file()
    assert (out / "concept_priority.csv").is_file()
    assert (out / "root_cause_manifest.json").is_file()
    with pytest.raises(FileExistsError):
        run(qa, out)
    assert flag_file.read_bytes() == pristine


def test_bad_sha_blocks_before_writing(tmp_path):
    flags, report = example()
    qa = tmp_path / "full_qa"
    qa.mkdir()
    with (qa / "full_translation_flags.csv").open("w", encoding="utf-8-sig", newline="") as fp:
        w = csv.DictWriter(fp, fieldnames=list(flags[0]))
        w.writeheader()
        w.writerows(flags)
    report["outputs"] = {"full_translation_flags.csv": "wrong-sha256"}
    (qa / "full_qa_summary.json").write_text(json.dumps(report), encoding="utf-8")
    out = tmp_path / "priority"
    with pytest.raises(ValueError, match="SHA-256"):
        run(qa, out)
    assert not out.exists()
