"""Synthetic regression tests for offline EN->TR QA candidate triage."""
import csv
import json
import sys
from pathlib import Path

import pytest
from audit_translation_quality import analyze_pair, scan_rows, main


def test_specific_scientific_false_friends():
    examples = [
        ("Calcite crystals are flaky.", "Analiz kristalleri flaky.", "CALCITE_AS_ANALYSIS"),
        ("Only one circuit will light the bulb.", "Bir devre otobüsü aydınlatacaktır.", "BULB_AS_BUS"),
        ("The nail stuck to a magnet.", "Tırnak mıknatısa yapıştı.", "NAIL_AS_FINGERNAIL"),
        ("They are square.", "Bunun yerine meydan okuyorlar.", "SQUARE_AS_CHALLENGE"),
        ("Alice grew seedlings in five pots.", "Alice beş tencerede tohum yetiştirdi.", "PLANT_POT_AS_SAUCEPAN"),
        ("Mix a solid in water.", "Suya sağlam katın.", "CHEMICAL_SOLID_AS_STURDY"),
        ("The windows fogged up.", "Pencereler parlak oldu.", "FOGGED_GLASS_AS_SHINY"),
        ("Use no slope.", "Göçücü kullanın.", "NO_SLOPE_AS_NONSENSE"),
    ]
    for en, tr, rule in examples:
        flags = analyze_pair("x", "question", en, tr)
        assert rule in {f["rule"] for f in flags}
        assert next(f["priority"] for f in flags if f["rule"] == rule) == "HIGH"
        assert all(f["status"] == "AUTOMATIC_CANDIDATE_NOT_HUMAN_VERIFIED" for f in flags)


def test_obviously_faithful_translation_has_no_surface_flags():
    assert analyze_pair("z", "student_answer", "The water is hot.", "Su sıcaktır.") == []


def test_numeric_and_negation_suspicions_are_not_human_labels():
    flags = analyze_pair("z", "student_answer",
                         "Water will not freeze at 3 degrees.", "Su 4 derecede donar.")
    assert {"NUMBER_CHANGED", "NEGATION_NOT_EVIDENT"} <= {f["rule"] for f in flags}
    assert all(f["status"].startswith("AUTOMATIC") for f in flags)


def test_duplicate_ids_fail_closed():
    row = {"item_key": "same", "source_question_en": "Hello", "question": "Merhaba",
           "source_reference_answer_en": "Yes", "reference_answer": "Evet",
           "source_student_answer_en": "No", "student_answer": "Hayır"}
    with pytest.raises(ValueError, match="tekrar"):
        scan_rows([row, row])


def test_original_review_file_not_modified_and_report_not_overwritten(tmp_path, monkeypatch):
    row = {"item_key": "x", "source_question_en": "One circuit lights the bulb.",
           "question": "Bir devre otobüsü aydınlatır.",
           "source_reference_answer_en": "It is a bulb.", "reference_answer": "Bu bir ampuldür.",
           "source_student_answer_en": "No.", "student_answer": "Hayır.",
           "meaning_preserved": "", "error_preserved": "", "notes": ""}
    source = tmp_path / "review_A_blind.csv"
    with source.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(row))
        writer.writeheader()
        writer.writerow(row)
    original = source.read_bytes()
    monkeypatch.setattr(sys, "argv", ["qa", "--input", str(source), "--out", str(tmp_path / "qa")])
    assert main() == 0
    assert original == source.read_bytes()
    summary = json.loads((tmp_path / "qa" / "qa_summary.json").read_text(encoding="utf-8"))
    assert summary["rows"] == 1 and summary["not_gold_data"] is True
    assert summary["high_priority_rows"] == 1
    with pytest.raises(FileExistsError):
        main()
