"""Synthetic end-to-end 10,804-row candidate comparison test (no real student text)."""
from __future__ import annotations
from collections import Counter
import csv
import json
from pathlib import Path

import pytest

from test_translation_patchset import (
    make_fixtures, annotate_patch, STEMS,
)
from audit_dataset import SPLITS
from audit_translation_quality import analyze_pair
from prepare_translation_patch_plan import prepare
from apply_translation_patch_plan import apply
from compare_translation_versions import scan
from prioritize_translation_issues import file_sha


def prepare_full_fixture(tmp_path):
    priority, full, data, _ = make_fixtures(tmp_path)
    source_manifest_path = data / "translation_manifest.json"
    base = json.loads(source_manifest_path.read_text(encoding="utf-8"))
    base["pipeline_version"] = "0.2.0"
    source_manifest_path.write_text(json.dumps(base), encoding="utf-8")
    qa = full / "full_qa_summary.json"
    summary = json.loads(qa.read_text(encoding="utf-8"))
    summary["input_rows"] = 10804
    rules = Counter()
    splits = {}
    for split in SPLITS:
        counts = Counter()
        with (data / (STEMS[split] + ".csv")).open(newline="", encoding="utf-8-sig") as fp:
            for idx, row in enumerate(csv.DictReader(fp)):
                flags = []
                for field in ("question", "reference_answer", "student_answer"):
                    fs = analyze_pair(f"{split}:{idx}", field,
                                      row["source_" + field + "_en"], row[field])
                    flags.extend(fs)
                    rules.update(x["rule"] for x in fs)
                priority_code = "HIGH" if any(x["priority"] == "HIGH" for x in flags) else (
                    "MEDIUM" if flags else "UNFLAGGED")
                counts[priority_code] += 1
        splits[split] = {
            "rows": base["splits"][split]["source_rows"],
            "high_priority_rows": counts["HIGH"],
            "medium_priority_rows": counts["MEDIUM"],
            "unflagged_rows": counts["UNFLAGGED"],
        }
    summary["input_splits"] = splits
    summary["rule_counts"] = dict(sorted(rules.items()))
    summary["total_flags"] = sum(rules.values())
    summary["source_translation_manifest_sha256"] = file_sha(source_manifest_path)
    qa.write_text(json.dumps(summary), encoding="utf-8")
    pmeta_file = priority / "root_cause_manifest.json"
    pmeta = json.loads(pmeta_file.read_text(encoding="utf-8"))
    pmeta["input_full_qa_sha256"] = file_sha(qa)
    pmeta_file.write_text(json.dumps(pmeta), encoding="utf-8")
    plan = tmp_path / "reports" / "tr_patch_plan_v021_ai_draft"
    prepare(priority, plan)
    annotate_patch(plan)
    (plan / "import_manifest.json").write_text(
        json.dumps({"ai_draft_csv_sha256": file_sha(plan / "patch_candidates.csv")}),
        encoding="utf-8",
    )
    new = tmp_path / "data" / "tr_v0_2_1"
    manifest = apply(priority, plan, data, new)
    return data, new, full, plan, manifest, summary


def test_full_comparison_is_read_only_and_matches_provenance(tmp_path):
    old, new, full, plan, manifest, baseline = prepare_full_fixture(tmp_path)
    tracked = {
        "old": file_sha(old / "train.csv"),
        "new": file_sha(new / "train.csv"),
        "plan": file_sha(plan / "patch_candidates.csv"),
    }
    out = tmp_path / "reports" / "comparison"
    results = scan(old, new, full, plan, out)
    assert results["original_rows"] == results["candidate_rows"] == 10804
    assert results["patch_count"] == 1
    assert results["edited_distinct_rows"] == 2
    assert results["edited_field_occurrences"] == 2
    assert results["original_total_rule_flags"] == baseline["total_flags"]
    assert results["candidate_total_rule_flags"] < baseline["total_flags"]
    assert results["new_high_rule_regressions_on_patched_fields"] == 0
    assert results["human_validation"] is False
    assert (out / "comparison_summary.md").exists()
    assert (out / "rule_delta.csv").exists()
    assert (out / "changed_field_comparison.csv").exists()
    assert tracked == {
        "old": file_sha(old / "train.csv"),
        "new": file_sha(new / "train.csv"),
        "plan": file_sha(plan / "patch_candidates.csv"),
    }
    with pytest.raises(RuntimeError, match="exists"):
        scan(old, new, full, plan, out)


def test_comparison_fails_closed_on_tampered_candidate_file(tmp_path):
    old, new, full, plan, _, _ = prepare_full_fixture(tmp_path)
    with (new / "train.csv").open("a", encoding="utf-8") as fp:
        fp.write("\n")
    out = tmp_path / "reports" / "comparison"
    with pytest.raises(RuntimeError, match="candidate SHA"):
        scan(old, new, full, plan, out)
    assert not out.exists()
