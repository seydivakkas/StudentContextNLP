"""Create a NEW SciEntsBank-TR v0.2.1 exploratory dataset from explicit exact-pair edits.

DEFAULT: nothing is approved; this program refuses to create a new corpus until
some reviewer-curated full-sentence changes carry an APPLY_EXPLORATORY decision,
curation origin and detailed evidence. It NEVER treats an AI draft as human gold.

python apply_translation_patch_plan.py \
  --priority-dir reports/tr_auto_priority_v01 \
  --plan-dir reports/tr_patch_plan_v021 \
  --data-dir data/tr_v0_2 --out data/tr_v0_2_1
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path

from audit_dataset import SPLITS, EXPECTED
from audit_translation_quality import analyze_pair
from prioritize_translation_issues import CLUSTER_FIELDS, file_sha
from tr_adaptation.pipeline import OUT_STEM
from tr_adaptation.quality import review_flags

EDIT_FIELDS = ("question", "reference_answer", "student_answer")
ORIG_COLS = ("id", "label", "question", "reference_answer", "student_answer",
             "source_question_en", "source_reference_answer_en", "source_student_answer_en",
             "quality_flags", "label_status", "translation_scope")
APPROVAL = "APPLY_EXPLORATORY"
NOTE_MIN_CHARS = 12
DECISIONS = {"PENDING", "SKIP", APPROVAL}


def sha_pair(field: str, en: str, tr: str) -> str:
    return hashlib.sha256((field + "\0" + en + "\0" + tr).encode("utf-8")).hexdigest()


def _require(condition: bool, message: str):
    if not condition:
        raise ValueError(message)


def load_patch_proposals(priority_dir: Path, plan_dir: Path, data_dir: Path):
    priority_dir, plan_dir, data_dir = priority_dir.resolve(), plan_dir.resolve(), data_dir.resolve()
    pmfile = priority_dir / "root_cause_manifest.json"
    cfile = priority_dir / "root_cause_clusters.csv"
    formfile = plan_dir / "patch_candidates.csv"
    planfile = plan_dir / "patch_plan_manifest.json"
    pmeta = json.loads(pmfile.read_text(encoding="utf-8"))
    plan = json.loads(planfile.read_text(encoding="utf-8"))
    _require(plan.get("stage") == "SCIENTSBANK_TR_V0_2_1_PATCH_PLANNING",
             "Unexpected candidate plan stage")
    _require(not plan.get("human_verified") and not plan.get("projected_labels_are_gold")
             and plan.get("applied_edits") == 0, "Unverified patch status required")
    _require(plan["source_priority_manifest_sha256"] == file_sha(pmfile),
             "Priority manifest changed since plan creation")
    _require(plan["source_priority_clusters_sha256"] == file_sha(cfile),
             "Root-cause evidence changed since plan creation")
    _require(pmeta["outputs"]["root_cause_clusters.csv"] == file_sha(cfile),
             "Cluster evidence SHA mismatch")
    with cfile.open(newline="", encoding="utf-8-sig") as fp:
        reader = csv.DictReader(fp)
        _require(reader.fieldnames is not None and set(CLUSTER_FIELDS).issubset(reader.fieldnames),
                 "Priority evidence schema mismatch")
        clusters = {r["cluster_id"]: r for r in reader}
    with formfile.open(newline="", encoding="utf-8-sig") as fp:
        reader = csv.DictReader(fp)
        required = {"cluster_id", "field", "concept", "priority_tier",
                    "source_en", "target_tr", "source_target_sha256", "affected_distinct_rows",
                    "rule_types", "proposed_tr", "decision", "curation_origin", "evidence_note"}
        _require(reader.fieldnames is not None and required.issubset(reader.fieldnames),
                 "Patch plan schema mismatch")
        rows = list(reader)
    _require(len(rows) == plan["candidate_count"], "Number of patch candidates was modified")
    seen_ids, seen_pairs, patches = set(), set(), {}
    for r in rows:
        cid = r["cluster_id"]
        _require(cid and cid not in seen_ids and cid in clusters,
                 "Unknown or duplicate evidence cluster")
        seen_ids.add(cid)
        frozen = clusters[cid]
        evidence_fields = ("concept", "field", "priority_tier", "source_en", "target_tr",
                           "source_target_sha256", "affected_distinct_rows", "rule_types")
        _require(all(r[k] == frozen[k] for k in evidence_fields),
                 "Patch candidate evidence changed since original frozen report")
        _require(sha_pair(r["field"], r["source_en"], r["target_tr"])
                 == r["source_target_sha256"], "Patch target SHA mismatch")
        _require(r["field"] in EDIT_FIELDS, "Unknown source text field")
        decision = r["decision"].strip()
        _require(decision in DECISIONS, "Unsupported patch decision")
        if decision != APPROVAL:
            continue
        new_tr = r["proposed_tr"].strip()
        origin = r["curation_origin"].strip()
        explanation = r["evidence_note"].strip()
        _require(origin in {"AI_DRAFT", "RESEARCHER_EDITED"},
                 "Explicit non-gold origin required for exploratory patch")
        _require(len(explanation) >= NOTE_MIN_CHARS,
                 "Explain scientific meaning and original translation defect")
        _require(bool(new_tr) and new_tr != r["target_tr"].strip()
                 and "\0" not in new_tr, "A distinct full-sentence proposed translation is required")
        _require(len(new_tr) < 20000, "Unreasonably large replacement")
        before = {x["rule"] for x in analyze_pair(cid, r["field"],
                                                 r["source_en"], r["target_tr"])}
        after = {x["rule"] for x in analyze_pair(cid, r["field"],
                                                r["source_en"], new_tr)}
        required_rules = set(r["rule_types"].split("|"))
        _require(required_rules.issubset(before),
                 "Frozen source QA trigger no longer matches input evidence")
        _require(not required_rules.intersection(after),
                 "Proposed text still triggers the selected scientific error")
        before_high = {x["rule"] for x in analyze_pair(
            cid, r["field"], r["source_en"], r["target_tr"]) if x["priority"] == "HIGH"}
        after_high = {x["rule"] for x in analyze_pair(
            cid, r["field"], r["source_en"], new_tr) if x["priority"] == "HIGH"}
        _require(not after_high.difference(before_high),
                 "Patch creates a new high-priority error flag")
        key = (r["field"], r["source_en"], r["target_tr"])
        _require(key not in seen_pairs, "Conflicting patches for same exact pair")
        seen_pairs.add(key)
        patches[key] = {
            "cluster_id": cid, "concept": r["concept"], "field": r["field"],
            "source_en": r["source_en"], "original_tr": r["target_tr"],
            "replacement_tr": new_tr, "affected_distinct_rows": int(r["affected_distinct_rows"]),
            "priority_tier": r["priority_tier"], "curation_origin": origin,
            "evidence_note": explanation, "source_target_sha256": r["source_target_sha256"],
            "matched_rows": 0, "matched_splits": Counter(),
        }
    _require(bool(patches), "No APPLY_EXPLORATORY entries; no modified corpus will be created")

    # The exact English/translated v0.2 source and the audited 10,804-row QA are pinned.
    qa_file = priority_dir.parent / "tr_auto_full_v01" / "full_qa_summary.json"
    qa = json.loads(qa_file.read_text(encoding="utf-8"))
    source_manifest_file = data_dir / "translation_manifest.json"
    src = json.loads(source_manifest_file.read_text(encoding="utf-8"))
    _require(file_sha(qa_file) == pmeta["input_full_qa_sha256"],
             "Source full QA summary has changed")
    _require(file_sha(source_manifest_file) == qa["source_translation_manifest_sha256"],
             "Original translation manifest differs from 10,804-row QA")
    _require(src.get("total_translated_rows") == 10804
             and src.get("scope") == "FULL_CANDIDATE"
             and src.get("validation_state") == "UNVERIFIED_MACHINE_TRANSLATION"
             and src.get("projected_labels_are_gold") is False,
             "Expected frozen, unverified, complete v0.2 source corpus")
    for split in SPLITS:
        infile = data_dir / (OUT_STEM[split] + ".csv")
        _require(file_sha(infile) == src["splits"][split]["output_sha256"]
                 and file_sha(infile) == qa["source_csv_sha256"][split],
                 "Original translated split SHA mismatch: " + split)
    return patches, src, plan, pmeta


def _quality(row: dict) -> str:
    checks = []
    for name in EDIT_FIELDS:
        en = row["source_" + name + "_en"]
        tr = row[name]
        if not en.strip():
            checks.append(name + ":EMPTY_SOURCE")
        else:
            checks.extend(name + ":" + rule for rule in review_flags(en, tr))
    return json.dumps(sorted(set(checks)), ensure_ascii=False)


def apply(priority_dir: Path, plan_dir: Path, data_dir: Path, out: Path) -> dict:
    data_dir, out = data_dir.resolve(), out.resolve()
    if out.is_relative_to(data_dir) or data_dir.is_relative_to(out):
        raise ValueError("Original and output candidate datasets cannot overlap")
    stage = out.with_name(out.name + ".part")
    if out.exists() or stage.exists():
        raise FileExistsError("Output exists or an incomplete staging directory exists")
    patches, original, plan, pmeta = load_patch_proposals(priority_dir, plan_dir, data_dir)
    stage.mkdir(parents=True)
    totals = Counter()
    by_split = {}
    try:
        for split in SPLITS:
            infile = data_dir / (OUT_STEM[split] + ".csv")
            dest = stage / infile.name
            with infile.open(newline="", encoding="utf-8-sig") as inp, \
                 dest.open("w", newline="", encoding="utf-8-sig") as output:
                reader = csv.DictReader(inp)
                _require(reader.fieldnames is not None
                         and set(ORIG_COLS).issubset(reader.fieldnames),
                         "Translation row schema mismatch")
                writer = csv.DictWriter(output, fieldnames=reader.fieldnames)
                writer.writeheader()
                count = changes = 0
                for row in reader:
                    count += 1
                    _require(row["label_status"] == "UNVERIFIED_TRANSFER"
                             and row["translation_scope"] == "FULL_CANDIDATE",
                             "Original source label provenance changed")
                    touched = False
                    for field in EDIT_FIELDS:
                        key = (field, row["source_" + field + "_en"], row[field])
                        patch = patches.get(key)
                        if patch is not None:
                            row[field] = patch["replacement_tr"]
                            patch["matched_rows"] += 1
                            patch["matched_splits"][split] += 1
                            totals[field] += 1
                            touched = True
                    if touched:
                        row["quality_flags"] = _quality(row)
                        changes += 1
                    writer.writerow(row)
            _require(count == original["splits"][split]["source_rows"]
                     and count == original["splits"][split]["translated_rows"],
                     "Original and output row count differ")
            by_split[split] = {
                "rows": count, "edited_rows": changes,
                "output_sha256": file_sha(dest),
            }
        for patch in patches.values():
            _require(patch["matched_rows"] == patch["affected_distinct_rows"],
                     "A patch affected a different count than frozen root-cause evidence: "
                     + patch["cluster_id"])
        # No sentence-level correctness proof is inferred from successful rules.
        audit = []
        for p in sorted(patches.values(), key=lambda x: x["cluster_id"]):
            audit.append({
                **{key: value for key, value in p.items()
                   if key != "matched_splits"},
                "matched_splits": json.dumps(dict(p["matched_splits"]), sort_keys=True),
                "status": "UNVERIFIED_EXPLORATORY_AI_ASSISTED_PATCH",
            })
        auditfile = stage / "patch_audit.csv"
        with auditfile.open("w", newline="", encoding="utf-8-sig") as fp:
            writer = csv.DictWriter(fp, fieldnames=list(audit[0].keys()))
            writer.writeheader()
            writer.writerows(audit)
        manifest = {
            "pipeline_version": "0.2.1",
            "source_dataset": original["source_dataset"],
            "model": original["model"], "model_key": original["model_key"],
            "source_file_sha256": original["source_file_sha256"],
            "source_p0_status": original["source_p0_status"],
            "scope": "FULL_CANDIDATE",
            "validation_state": "UNVERIFIED_EXPLORATORY_AI_ASSISTED_PATCH",
            "projected_labels_are_gold": False,
            "label_status": "UNVERIFIED_TRANSFER",
            "total_source_rows": original["total_source_rows"],
            "total_translated_rows": sum(x["rows"] for x in by_split.values()),
            "splits": by_split,
            "approved_exploratory_pair_patches": len(patches),
            "edited_distinct_rows": sum(x["edited_rows"] for x in by_split.values()),
            "edited_field_occurrences": sum(totals.values()),
            "edited_fields": dict(sorted(totals.items())),
            "parent_translation_manifest_sha256": file_sha(
                data_dir / "translation_manifest.json"),
            "plan_candidate_file_sha256": file_sha(
                plan_dir / "patch_candidates.csv"),
            "priority_manifest_sha256": file_sha(
                priority_dir / "root_cause_manifest.json"),
            "patch_audit_sha256": file_sha(auditfile),
            "human_validated": False, "independent_human_review": False,
            "english_baseline_modified": False,
            "description": "Non-gold, explicit exact-pair, exploratory corrections. "
                           "Original EN, labels and parent TR data untouched.",
        }
        _require(manifest["total_translated_rows"] == 10804,
                 "New candidate dataset has incomplete coverage")
        (stage / "translation_manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        stage.rename(out)
    except BaseException:
        print("FAILED: incomplete staging preserved at", stage)
        raise
    print("Versioned v0.2.1 candidate created:", out)
    print("Exact-pair patches:", len(patches))
    print("Edited distinct rows:", manifest["edited_distinct_rows"])
    print("Edited field occurrences:", manifest["edited_field_occurrences"])
    print("Original 10,804-row dataset untouched; gold labels not claimed.")
    return manifest


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--priority-dir", type=Path, default=Path("reports/tr_auto_priority_v01"))
    p.add_argument("--plan-dir", type=Path, default=Path("reports/tr_patch_plan_v021"))
    p.add_argument("--data-dir", type=Path, default=Path("data/tr_v0_2"))
    p.add_argument("--out", type=Path, default=Path("data/tr_v0_2_1"))
    a = p.parse_args()
    apply(a.priority_dir, a.plan_dir, a.data_dir, a.out)


if __name__ == "__main__":
    main()
