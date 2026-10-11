"""Prepare immutable-evidence v0.2.1 *candidate* review plan; never rewrite text.

From full real T3-AUTO v0.4 root-cause clusters, choose repeated P1/P2 evidence
and generate a separate EMPTY curation form. This is not human annotation/gold.

python prepare_translation_patch_plan.py \
    --priority-dir reports/tr_auto_priority_v01 \
    --out reports/tr_patch_plan_v021 --limit 100
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

from prioritize_translation_issues import CLUSTER_FIELDS, file_sha, LEVEL

FORM_FIELDS = [
    "cluster_id", "concept", "field", "priority_tier", "rule_types",
    "affected_distinct_rows", "source_en", "target_tr", "source_target_sha256",
    "proposed_tr", "decision", "curation_origin", "evidence_note",
]
STATES = {"P1_SCIENTIFIC_POLARITY_OR_UNITS", "P2_SPECIFIC_TECHNICAL_TERM"}


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def prepare(priority_dir: Path, out: Path, limit: int = 100, min_rows: int = 2):
    priority_dir, out = priority_dir.resolve(), out.resolve()
    if limit < 1 or min_rows < 1:
        raise ValueError("limit and min_rows must be positive")
    stage = out.with_name(out.name + ".part")
    if out.exists() or stage.exists():
        raise FileExistsError("Existing output will not be overwritten")
    if out.is_relative_to(priority_dir) or priority_dir.is_relative_to(out):
        raise ValueError("Output must not overlap root-cause evidence")
    meta_file = priority_dir / "root_cause_manifest.json"
    clusters_file = priority_dir / "root_cause_clusters.csv"
    meta = json.loads(meta_file.read_text(encoding="utf-8"))
    if (meta.get("stage") != "T3_AUTO_ROOT_CAUSE_PRIORITIZATION"
            or meta.get("status") != "AUTOMATIC_CANDIDATE_NOT_HUMAN_VERIFIED"
            or meta.get("full_corpus_rows") != 10804
            or meta.get("full_corpus_flags") != 7412
            or not meta.get("no_source_changes")
            or not meta.get("no_gold_labels")):
        raise ValueError("Expected untouched real 10,804-row automatic priority report")
    pinned = meta.get("outputs", {}).get("root_cause_clusters.csv")
    if not pinned or pinned != file_sha(clusters_file):
        raise ValueError("Root-cause evidence SHA-256 differs from its manifest")
    with clusters_file.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or not set(CLUSTER_FIELDS).issubset(reader.fieldnames):
            raise ValueError("Unexpected root-cause schema")
        source_clusters = list(reader)
    if len(source_clusters) != meta.get("distinct_concept_field_source_target_clusters"):
        raise ValueError("Root-cause cluster count mismatch")
    unique_ids = set()
    candidates = []
    for r in source_clusters:
        cid = r["cluster_id"]
        if cid in unique_ids:
            raise ValueError("Duplicate root cause cluster id")
        unique_ids.add(cid)
        if not r["affected_distinct_rows"].isdigit():
            raise ValueError("Invalid affected-row count")
        expected = _hash(r["field"] + "\0" + r["source_en"] + "\0" + r["target_tr"])
        cluster = _hash(r["concept"] + "\0" + r["field"] + "\0" + expected)
        if expected != r["source_target_sha256"] or cluster != cid:
            raise ValueError("Root-cause cluster/source/target evidence SHA mismatch")
        if (r["priority_tier"] not in STATES
                or int(r["affected_distinct_rows"]) < min_rows):
            continue
        candidates.append(r)
    candidates.sort(key=lambda r: (
        LEVEL[r["priority_tier"]],
        -int(r["affected_distinct_rows"]),
        -int(r["rule_occurrences"]), r["cluster_id"],
    ))
    seen_pairs = set()
    forms = []
    duplicate_concept_pairs_skipped = 0
    for r in candidates:
        # Multiple concepts may flag the same exact source-target text.
        # Choose the highest-ranked cluster; never allow competing replacements.
        key = (r["field"], r["source_en"], r["target_tr"])
        if key in seen_pairs:
            duplicate_concept_pairs_skipped += 1
            continue
        seen_pairs.add(key)
        forms.append({
            **{x: r[x] for x in FORM_FIELDS if x in r},
            "proposed_tr": "", "decision": "PENDING",
            "curation_origin": "", "evidence_note": "",
        })
        if len(forms) == limit:
            break
    stage.mkdir(parents=True)
    try:
        candidate_file = stage / "patch_candidates.csv"
        with candidate_file.open("w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=FORM_FIELDS, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(forms)
        result = {
            "stage": "SCIENTSBANK_TR_V0_2_1_PATCH_PLANNING",
            "validation_state": "UNVERIFIED_CANDIDATES_NO_EDITS",
            "source_priority_manifest_sha256": file_sha(meta_file),
            "source_priority_clusters_sha256": pinned,
            "candidate_file_sha256": file_sha(candidate_file),
            "candidate_count": len(forms),
            "selected_cluster_ids": [r["cluster_id"] for r in forms],
            "eligible_repeated_p1_p2_clusters": len(candidates),
            "duplicate_concept_pairs_skipped": duplicate_concept_pairs_skipped,
            "limit": limit, "min_rows": min_rows,
            "candidate_affected_rows_sum_not_distinct": sum(
                int(x["affected_distinct_rows"]) for x in forms),
            "applied_edits": 0, "human_verified": False,
            "projected_labels_are_gold": False,
            "instructions": {
                "decision": "PENDING (default), SKIP, APPLY_EXPLORATORY",
                "proposed_tr": "For APPLY_EXPLORATORY write a COMPLETE faithful Turkish sentence, not only a glossary word.",
                "curation_origin": "AI_DRAFT or RESEARCHER_EDITED; neither is an independent human validation",
                "evidence_note": "For APPLY_EXPLORATORY explain the precise source meaning and why the old translation is wrong.",
                "privacy": "CSV contains actual student text; do not commit it to GitHub.",
            },
        }
        (stage / "patch_plan_manifest.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        stage.rename(out)
    except BaseException:
        # Keep staging material for inspection; never claim successful activation.
        raise
    print("Patch candidates (nothing applied):", len(forms))
    print("Repeated P1/P2 eligible groups:", len(candidates))
    print("All decisions: PENDING; source rows changed: 0")
    print("Plan:", out)
    return result


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--priority-dir", type=Path, default=Path("reports/tr_auto_priority_v01"))
    p.add_argument("--out", type=Path, default=Path("reports/tr_patch_plan_v021"))
    p.add_argument("--limit", type=int, default=100)
    p.add_argument("--min-rows", type=int, default=2)
    a = p.parse_args()
    prepare(a.priority_dir, a.out, a.limit, a.min_rows)


if __name__ == "__main__":
    main()
