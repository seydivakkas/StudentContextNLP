"""Safely import a PRIVATE AI_DRAFT zip as a separate frozen exploratory patch plan.

Never overwrite the 37 original PENDING candidates, original TR corpus, gold
labels, A/B reviewer forms or any GitHub files. The ZIP is read, not extracted.
"""
from __future__ import annotations
import argparse
from collections import Counter
import csv
import hashlib
import io
import json
from pathlib import Path
import zipfile

from prioritize_translation_issues import file_sha

ORIGINAL_FIELDS = (
    "cluster_id", "concept", "field", "priority_tier", "rule_types",
    "affected_distinct_rows", "source_en", "target_tr",
    "source_target_sha256",
)
CHANGE_FIELDS = ("proposed_tr", "decision", "curation_origin", "evidence_note")
CSV_FILE = "patch_candidates_AI_DRAFT.csv"
MANIFEST_FILE = "AI_DRAFT_manifest.json"
STAGE = "T3_AUTO_V0_6_AI_DRAFT_CURATED_TRANSLATION_PROPOSALS"
STATUS = "AI_DRAFT_SUGGESTIONS_NOT_APPLIED_NOT_HUMAN_VERIFIED"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _rows(blob: bytes) -> tuple[list[str], list[dict[str, str]]]:
    decoded = blob.decode("utf-8-sig")
    f = io.StringIO(decoded, newline="")
    reader = csv.DictReader(f)
    names = list(reader.fieldnames or [])
    needed = set(ORIGINAL_FIELDS) | set(CHANGE_FIELDS)
    if not needed.issubset(names) or len(names) != len(set(names)):
        raise ValueError("AI_DRAFT missing or duplicated columns")
    rows = list(reader)
    if any(None in row for row in rows):
        raise ValueError("CSV has malformed lines or mismatched delimiters")
    return names, rows


def validate(plan_dir: Path, csv_blob: bytes, draft_manifest: dict) -> dict:
    plan_csv = plan_dir / "patch_candidates.csv"
    plan_manifest = plan_dir / "patch_plan_manifest.json"
    if not plan_csv.is_file() or not plan_manifest.is_file():
        raise FileNotFoundError("Original frozen patch candidates and manifest are required")
    frozen = json.loads(plan_manifest.read_text(encoding="utf-8"))
    if (frozen.get("stage") != "SCIENTSBANK_TR_V0_2_1_PATCH_PLANNING"
            or frozen.get("applied_edits") != 0
            or frozen.get("candidate_count") != 37):
        raise ValueError("Not the expected frozen 37-candidate plan")
    if frozen.get("candidate_file_sha256") != file_sha(plan_csv):
        raise ValueError("Original frozen candidate SHA-256 mismatch")
    if (draft_manifest.get("stage") != STAGE or draft_manifest.get("status") != STATUS
            or draft_manifest.get("source_manifest_sha256") != file_sha(plan_manifest)
            or draft_manifest.get("source_candidates_sha256") != file_sha(plan_csv)
            or draft_manifest.get("source_expected_manifest_sha256") != file_sha(plan_csv)
            or draft_manifest.get("outputs", {}).get(CSV_FILE) != sha(csv_blob)
            or draft_manifest.get("not_human_review") is not True
            or draft_manifest.get("projected_labels_are_gold") is not False
            or draft_manifest.get("applied_edits") != 0):
        raise ValueError("AI_DRAFT package SHA-256/provenance mismatch")
    _, original = _rows(plan_csv.read_bytes())
    _, edited = _rows(csv_blob)
    if len(original) != len(edited) or len(edited) != 37:
        raise ValueError("Candidate row count differs")
    frozen_ids = frozen.get("selected_cluster_ids")
    if ([x["cluster_id"] for x in original] != frozen_ids
            or [x["cluster_id"] for x in edited] != frozen_ids
            or draft_manifest.get("source_selected_cluster_ids") != frozen_ids):
        raise ValueError("Candidate identity/order changed")
    decisions = Counter()
    for i, (raw, mod) in enumerate(zip(original, edited), 1):
        if any(raw[k] != mod[k] for k in ORIGINAL_FIELDS):
            raise ValueError(f"Immutable source/target evidence was edited: candidate #{i}")
        if (raw["decision"] != "PENDING" or raw["proposed_tr"]
                or raw["curation_origin"] or raw["evidence_note"]):
            raise ValueError("Original plan is not blank/PENDING")
        decision = mod["decision"]
        if decision not in {"APPLY_EXPLORATORY", "PENDING", "SKIP"}:
            raise ValueError(f"Unexpected candidate decision #{i}")
        if mod["curation_origin"] != "AI_DRAFT":
            raise ValueError(f"Improper curation origin #{i}")
        if decision == "APPLY_EXPLORATORY":
            if (not mod["proposed_tr"].strip()
                    or mod["proposed_tr"].strip() == raw["target_tr"].strip()
                    or len(mod["evidence_note"].strip()) < 12):
                raise ValueError(f"Incomplete full sentence/evidence note #{i}")
        decisions[decision] += 1
    if dict(decisions) != draft_manifest.get("decision_counts"):
        raise ValueError("AI_DRAFT manifest decision counts differ")
    if decisions["APPLY_EXPLORATORY"] != 34 or decisions["PENDING"] != 3:
        raise ValueError("Expected exactly 34 proposed exploratory corrections and 3 PENDING")
    return {
        "stage": "T3_AUTO_V021_IMPORTED_DRAFT_PLAN",
        "status": "EXPLORATORY_AI_DRAFT_UNVERIFIED",
        "frozen_original_candidate_sha256": file_sha(plan_csv),
        "frozen_original_plan_sha256": file_sha(plan_manifest),
        "ai_draft_csv_sha256": sha(csv_blob),
        "candidate_count": len(edited),
        "decision_counts": dict(decisions),
        "human_validated": False,
        "english_or_existing_tr_dataset_modified": False,
        "applied_edits": 0,
    }


def import_plan(package: Path, source_plan: Path, out: Path) -> dict:
    package, source_plan, out = package.resolve(), source_plan.resolve(), out.resolve()
    if not package.is_file():
        raise FileNotFoundError(package)
    if out.is_relative_to(source_plan) or source_plan.is_relative_to(out):
        raise ValueError("The imported plan cannot overwrite or nest inside the original plan")
    stage = out.with_name(out.name + ".part")
    if out.exists() or stage.exists():
        raise FileExistsError("Output or partial plan exists; never overwrite")
    with zipfile.ZipFile(package) as archive:
        if archive.testzip():
            raise ValueError("ZIP CRC failed")
        listing = {Path(name).name: name for name in archive.namelist() if not name.endswith("/")}
        if CSV_FILE not in listing or MANIFEST_FILE not in listing:
            raise ValueError("Missing AI_DRAFT CSV or provenance manifest in ZIP")
        if archive.getinfo(listing[CSV_FILE]).file_size > 2_000_000:
            raise ValueError("Unexpected oversized CSV in ZIP")
        if archive.getinfo(listing[MANIFEST_FILE]).file_size > 200_000:
            raise ValueError("Unexpected oversized manifest in ZIP")
        csv_blob = archive.read(listing[CSV_FILE])
        draft_manifest = json.loads(archive.read(listing[MANIFEST_FILE]).decode("utf-8-sig"))
    result = validate(source_plan, csv_blob, draft_manifest)
    result["input_package_sha256"] = file_sha(package)
    stage.mkdir(parents=True)
    try:
        (stage / "patch_candidates.csv").write_bytes(csv_blob)
        original_manifest = source_plan / "patch_plan_manifest.json"
        (stage / "patch_plan_manifest.json").write_bytes(original_manifest.read_bytes())
        (stage / "import_manifest.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        stage.rename(out)
    except BaseException:
        print("Import was interrupted; inspect:", stage)
        raise
    print("AI_DRAFT import: 37 candidates; 34 APPLY_EXPLORATORY; 3 PENDING")
    print("Original plan and data untouched; destination:", out)
    return result


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--package", type=Path, required=True)
    p.add_argument("--source-plan", type=Path, default=Path("reports/tr_patch_plan_v021"))
    p.add_argument("--out", type=Path, default=Path("reports/tr_patch_plan_v021_ai_draft"))
    a = p.parse_args()
    import_plan(a.package, a.source_plan, a.out)


if __name__ == "__main__":
    main()
