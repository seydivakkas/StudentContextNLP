"""No real student texts: regression tests for provenance-locked AI_DRAFT ZIP import."""
from __future__ import annotations

import csv
import hashlib
import io
import json
from pathlib import Path
import zipfile

import pytest
from import_ai_draft_patch import import_plan, sha


FIELDS = [
    "cluster_id", "concept", "field", "priority_tier", "rule_types",
    "affected_distinct_rows", "source_en", "target_tr", "source_target_sha256",
    "proposed_tr", "decision", "curation_origin", "evidence_note",
]


def make_zip_fixture(tmp_path: Path):
    source = tmp_path / "reports" / "tr_patch_plan_v021"
    source.mkdir(parents=True)
    original = []
    draft = []
    for n in range(37):
        en = f"The bulb lights in circuit {n}."
        tr = f"Otobus devrede {n} yanar."
        proof = hashlib.sha256(("question\0" + en + "\0" + tr).encode()).hexdigest()
        row = {
            "cluster_id": hashlib.sha256((str(n) + proof).encode()).hexdigest(),
            "concept": "bulb", "field": "question",
            "priority_tier": "P2_SPECIFIC_TECHNICAL_TERM",
            "rule_types": "BULB_AS_BUS",
            "affected_distinct_rows": "2",
            "source_en": en, "target_tr": tr,
            "source_target_sha256": proof,
            "proposed_tr": "", "decision": "PENDING", "curation_origin": "",
            "evidence_note": "",
        }
        original.append(row)
        new = dict(row)
        new["curation_origin"] = "AI_DRAFT"
        new["proposed_tr"] = f"Devre {n} icindeki ampul yanar."
        new["evidence_note"] = "Bulb means lamp, not a vehicle. Preserve exact circuit."
        if n < 34:
            new["decision"] = "APPLY_EXPLORATORY"
        draft.append(new)

    def csv_bytes(rows):
        f = io.StringIO(newline="")
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
        return ("\ufeff" + f.getvalue()).encode("utf-8")

    old_bytes, draft_bytes = csv_bytes(original), csv_bytes(draft)
    (source / "patch_candidates.csv").write_bytes(old_bytes)
    plan = {
        "stage": "SCIENTSBANK_TR_V0_2_1_PATCH_PLANNING",
        "applied_edits": 0,
        "candidate_count": 37,
        "candidate_file_sha256": sha(old_bytes),
        "selected_cluster_ids": [x["cluster_id"] for x in original],
    }
    (source / "patch_plan_manifest.json").write_text(
        json.dumps(plan, ensure_ascii=False), encoding="utf-8")
    draft_manifest = {
        "stage": "T3_AUTO_V0_6_AI_DRAFT_CURATED_TRANSLATION_PROPOSALS",
        "status": "AI_DRAFT_SUGGESTIONS_NOT_APPLIED_NOT_HUMAN_VERIFIED",
        "source_manifest_sha256": sha((source / "patch_plan_manifest.json").read_bytes()),
        "source_candidates_sha256": sha(old_bytes),
        "source_expected_manifest_sha256": sha(old_bytes),
        "outputs": {"patch_candidates_AI_DRAFT.csv": sha(draft_bytes)},
        "not_human_review": True,
        "projected_labels_are_gold": False,
        "applied_edits": 0,
        "source_selected_cluster_ids": [x["cluster_id"] for x in original],
        "decision_counts": {"APPLY_EXPLORATORY": 34, "PENDING": 3},
    }
    package = tmp_path / "package.zip"
    with zipfile.ZipFile(package, "w") as z:
        z.writestr("patch_candidates_AI_DRAFT.csv", draft_bytes)
        z.writestr("AI_DRAFT_manifest.json", json.dumps(draft_manifest))
    return source, package, original, draft


def test_import_frozen_package_keeps_original_and_creates_new_plan(tmp_path):
    source, package, _, _ = make_zip_fixture(tmp_path)
    old_hash = sha((source / "patch_candidates.csv").read_bytes())
    new = tmp_path / "reports" / "tr_patch_plan_v021_ai_draft"
    result = import_plan(package, source, new)
    assert result["candidate_count"] == 37
    assert result["decision_counts"] == {"APPLY_EXPLORATORY": 34, "PENDING": 3}
    assert result["applied_edits"] == 0
    assert sha((source / "patch_candidates.csv").read_bytes()) == old_hash
    assert (new / "patch_plan_manifest.json").read_bytes() == (
        source / "patch_plan_manifest.json").read_bytes()
    assert b"APPLY_EXPLORATORY" in (new / "patch_candidates.csv").read_bytes()
    with pytest.raises(FileExistsError):
        import_plan(package, source, new)


def test_tampered_ai_draft_csv_is_rejected_before_writes(tmp_path):
    source, package, _, _ = make_zip_fixture(tmp_path)
    with zipfile.ZipFile(package) as zin:
        z = {k: zin.read(k) for k in zin.namelist()}
    z["patch_candidates_AI_DRAFT.csv"] = z[
        "patch_candidates_AI_DRAFT.csv"].replace(b"ampul", b"otobus", 1)
    with zipfile.ZipFile(package, "w") as zout:
        for k, v in z.items():
            zout.writestr(k, v)
    out = tmp_path / "reports" / "new"
    with pytest.raises(ValueError, match="SHA-256"):
        import_plan(package, source, out)
    assert not out.exists()


def test_source_evidence_column_mutation_rejected(tmp_path):
    source, package, _, _ = make_zip_fixture(tmp_path)
    with zipfile.ZipFile(package) as zin:
        z = {k: zin.read(k) for k in zin.namelist()}
    broken = z["patch_candidates_AI_DRAFT.csv"].replace(
        b"The bulb lights", b"The bus lights", 1)
    z["patch_candidates_AI_DRAFT.csv"] = broken
    manifest = json.loads(z["AI_DRAFT_manifest.json"])
    manifest["outputs"]["patch_candidates_AI_DRAFT.csv"] = sha(broken)
    z["AI_DRAFT_manifest.json"] = json.dumps(manifest).encode()
    with zipfile.ZipFile(package, "w") as zout:
        for k, v in z.items():
            zout.writestr(k, v)
    out = tmp_path / "reports" / "new"
    with pytest.raises(ValueError, match="Immutable"):
        import_plan(package, source, out)
    assert not out.exists()


def test_original_frozen_plan_tamper_blocks(tmp_path):
    source, package, _, _ = make_zip_fixture(tmp_path)
    with (source / "patch_candidates.csv").open("ab") as f:
        f.write(b"\n")
    with pytest.raises(ValueError, match="Original frozen candidate SHA"):
        import_plan(package, source, tmp_path / "out")
