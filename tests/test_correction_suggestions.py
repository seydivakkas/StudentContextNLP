"""Synthetic tests for safe, provenance-preserving candidate term repair suggestions."""
import csv
import json
import sys

import pytest

from propose_translation_corrections import analyze, main


def _flag(rule, key="test_uq:12", field="student_answer", priority="HIGH"):
    return {
        "item_key": key, "field": field, "priority": priority,
        "rule": rule, "source_en": "Calcite crystals are square.",
        "target_tr": "Analiz kristalleri meydan okuyorlar.",
        "status": "AUTOMATIC_CANDIDATE_NOT_HUMAN_VERIFIED",
        "reason_tr": "Synthetic fixture only",
    }


def test_supported_high_priority_term_proposals_are_never_applied():
    p, summary = analyze([_flag("CALCITE_AS_ANALYSIS"), _flag("SQUARE_AS_CHALLENGE")])
    assert len(p) == 2 and summary["candidate_proposals"] == 2
    assert summary["distinct_item_keys"] == 1
    assert all(row["auto_apply"] == "false" for row in p)
    assert all(row["human_reviewed"] == "false" for row in p)
    assert all(row["derived_label_validated"] == "false" for row in p)
    assert summary["source_rows_modified"] == 0
    assert summary["verified_corrections"] == 0
    assert {row["candidate_tr_term"] for row in p} == {"kalsit", "kare biçiminde"}


def test_medium_or_unknown_rules_not_misrepresented_as_corrections():
    suggestions, summary = analyze([
        _flag("NEGATION_NOT_EVIDENT", priority="MEDIUM"),
        _flag("SQUARE_AS_CHALLENGE", priority="MEDIUM"),
    ])
    assert suggestions == []
    assert summary["candidate_proposals"] == 0


def test_unknown_source_state_fails_closed():
    x = _flag("BULB_AS_BUS")
    x["status"] = "HUMAN_VERIFIED"
    with pytest.raises(ValueError, match="verification"):
        analyze([x])


def test_cli_separate_path_and_no_overwrite(tmp_path, monkeypatch):
    original = tmp_path / "translation_flags.csv"
    f = _flag("CALCITE_AS_ANALYSIS")
    with original.open("w", newline="", encoding="utf-8-sig") as out:
        writer = csv.DictWriter(out, fieldnames=list(f))
        writer.writeheader()
        writer.writerow(f)
    before = original.read_bytes()
    destination = tmp_path / "suggestions"
    monkeypatch.setattr(sys, "argv", ["propose", "--flags", str(original), "--out", str(destination)])
    assert main() == 0
    assert original.read_bytes() == before
    summary = json.loads((destination / "repair_manifest.json").read_text(encoding="utf-8"))
    assert summary["candidate_proposals"] == 1
    assert summary["auto_applied_changes"] == 0
    with pytest.raises(FileExistsError):
        main()
