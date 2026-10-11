"""Synthetic tests: blinded reviewer forms must never leak projected labels."""
import json

import pandas as pd
import pytest

from prepare_blinded_reviews import prepare_blind_forms


def _fixture(tmp_path, n=4):
    folder = tmp_path / "reviews"
    folder.mkdir()
    rows = []
    for i in range(n):
        rows.append({
            "item_key": f"train:{i}", "split": "train", "class4": "Correct",
            "id": str(i), "source_question_en": "Is water liquid?",
            "question": "Su sıvı mıdır?", "source_reference_answer_en": "Yes.",
            "reference_answer": "Evet.", "source_student_answer_en": f"Yes. {i}",
            "student_answer": f"Evet. {i}", "quality_flags": '["NEGATION_REVIEW"]',
            "meaning_preserved": "", "error_preserved": "",
            "label_still_applicable": "", "correction_needed": "", "notes": "",
        })
    for reviewer in ("A", "B"):
        pd.DataFrame(rows).to_csv(folder / f"review_{reviewer}.csv", index=False)
    (folder / "review_manifest.json").write_text(
        json.dumps({"seed": 20261010, "actual_n": n,
                    "validation_state": "AWAITING_INDEPENDENT_HUMAN_REVIEW",
                    "source_manifest_model_key": "synthetic-key"}), encoding="utf-8"
    )
    return folder


def test_blind_forms_no_label_flags_or_id(tmp_path):
    folder = _fixture(tmp_path)
    r = prepare_blind_forms(folder, expected_n=4)
    assert r["n_items"] == 4
    assert r["stage"] == "BLIND_STAGE1"
    for reviewer in ("A", "B"):
        df = pd.read_csv(folder / "blind_stage1" / f"review_{reviewer}_blind.csv",
                         dtype=str, keep_default_na=False)
        assert len(df) == 4
        assert "class4" not in df and "quality_flags" not in df
        assert "id" not in df and "split" not in df
        assert "label" not in df
        assert df["meaning_preserved"].eq("").all()
        assert df["error_preserved"].eq("").all()
        assert df["notes"].eq("").all()
    assert "class4" in pd.read_csv(folder / "review_A.csv").columns


def test_existing_blind_forms_must_not_be_overwritten(tmp_path):
    folder = _fixture(tmp_path)
    prepare_blind_forms(folder, expected_n=4)
    path = folder / "blind_stage1" / "review_A_blind.csv"
    before = path.read_bytes()
    with pytest.raises(FileExistsError):
        prepare_blind_forms(folder, expected_n=4)
    assert path.read_bytes() == before


def test_inconsistent_review_sources_fail_before_writing(tmp_path):
    folder = _fixture(tmp_path)
    b = pd.read_csv(folder / "review_B.csv", dtype=str, keep_default_na=False)
    b.loc[0, "student_answer"] = "ALTERED"
    b.to_csv(folder / "review_B.csv", index=False)
    with pytest.raises(ValueError, match="differ"):
        prepare_blind_forms(folder, expected_n=4)
    assert not (folder / "blind_stage1").exists()


def test_manifest_mismatch_fails_before_writing(tmp_path):
    folder = _fixture(tmp_path)
    p = folder / "review_manifest.json"
    m = json.loads(p.read_text(encoding="utf-8"))
    m["actual_n"] = 239
    p.write_text(json.dumps(m), encoding="utf-8")
    with pytest.raises(ValueError, match="sample manifest"):
        prepare_blind_forms(folder, expected_n=4)
    assert not (folder / "blind_stage1").exists()
