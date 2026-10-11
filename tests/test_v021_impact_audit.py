"""Synthetic pre-T4 impact audit: 10,804 fabricated rows and no raw text outputs."""
import csv
import json

import pytest

from audit_v021_effects import audit
from compare_translation_versions import scan
from test_translation_version_comparison import prepare_full_fixture


def test_impact_audit_reports_edited_fields_labels_and_priority_transitions(tmp_path):
    old, new, full, plan, manifest, original = prepare_full_fixture(tmp_path)
    comparison = tmp_path / "reports" / "comparison"
    compare_report = scan(old, new, full, plan, comparison)
    old_hash = (old / "train.csv").read_bytes()
    new_hash = (new / "train.csv").read_bytes()
    out = tmp_path / "reports" / "impact"
    result = audit(old, new, comparison, out)
    assert result["input_rows"] == 10804
    assert result["edited_distinct_rows"] == 2
    assert result["edited_field_occurrences"] == 2
    assert result["changed_fields_by_split"]["train"] == {
        "question": 2, "reference_answer": 0, "student_answer": 0}
    assert result["changed_fields_by_split"]["test_uq"] == {
        "question": 0, "reference_answer": 0, "student_answer": 0}
    assert result["original_priority_counts"]["HIGH"] == 2
    assert result["candidate_priority_counts"]["HIGH"] == 0
    assert result["human_validated"] is False
    assert result["gold_translation_quality_claim"] is False
    assert (old / "train.csv").read_bytes() == old_hash
    assert (new / "train.csv").read_bytes() == new_hash
    with (out / "row_priority_transitions.csv").open(
            newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 4 * 9
    assert next(x for x in rows if x["split"] == "train"
                and x["old_priority"] == "HIGH"
                and x["new_priority"] == "UNFLAGGED")["row_count"] == "2"
    with (out / "label_edit_counts.csv").open(newline="", encoding="utf-8-sig") as f:
        labels = list(csv.DictReader(f))
    assert len(labels) == 4  # synthetic all labels are 0, per split
    assert next(x for x in labels if x["split"] == "train")["edited_rows"] == "2"
    assert "source_en" not in (out / "impact_manifest.json").read_text(encoding="utf-8")
    assert "The bulb lights" not in (out / "impact_summary.md").read_text(encoding="utf-8")
    with pytest.raises(RuntimeError, match="exists"):
        audit(old, new, comparison, out)


def test_deny_tampered_synthetic_compare_manifest_before_output(tmp_path):
    old, new, full, plan, manifest, original = prepare_full_fixture(tmp_path)
    comparison = tmp_path / "reports" / "comparison"
    scan(old, new, full, plan, comparison)
    path = old / "translation_manifest.json"
    with path.open("a", encoding="utf-8") as f:
        f.write(" ")
    out = tmp_path / "reports" / "impact"
    with pytest.raises(RuntimeError, match="manifest SHA mismatch"):
        audit(old, new, comparison, out)
    assert not out.exists()
