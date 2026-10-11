"""Offline read-only v0.2 -> v0.2.1 patch impact preflight before any T4 models.

Outputs ONLY aggregated data; never raw student text, IDs or row-level predictions.
No model fitting, API calls or human-gold claims.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
from itertools import zip_longest
import json
from pathlib import Path

from audit_dataset import SPLITS
from audit_translation_quality import analyze_pair
from audit_translation_corpus import sha256
from tr_adaptation.pipeline import OUT_STEM

TEXT_FIELDS = ("question", "reference_answer", "student_answer")
UNCHANGED = ("id", "label", "label_status", "translation_scope") + tuple(
    f"source_{field}_en" for field in TEXT_FIELDS
)
PRIORITIES = ("HIGH", "MEDIUM", "UNFLAGGED")
OUTPUT_FIELDS = ("split", "old_priority", "new_priority", "row_count",
                 "edited_row_count")


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def row_priority(key: str, row: dict) -> str:
    flags = []
    for field in TEXT_FIELDS:
        flags += analyze_pair(key, field, row[f"source_{field}_en"], row[field])
    return "HIGH" if any(x["priority"] == "HIGH" for x in flags) else (
        "MEDIUM" if flags else "UNFLAGGED"
    )


def save_csv(path: Path, rows: list[dict], fields: tuple[str, ...]):
    with path.open("w", newline="", encoding="utf-8-sig") as fp:
        writer = csv.DictWriter(fp, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def audit(old_dir: Path, new_dir: Path, comparison: Path, out: Path) -> dict:
    old_dir, new_dir, comparison, out = (
        x.resolve() for x in (old_dir, new_dir, comparison, out)
    )
    require(not any(out == p or out.is_relative_to(p) or p.is_relative_to(out)
                    for p in (old_dir, new_dir, comparison)),
            "Output overlaps immutable input evidence")
    stage = out.with_name(out.name + ".part")
    require(not out.exists() and not stage.exists(),
            "Aggregate output exists; cannot overwrite previous evidence")
    compare_file = comparison / "comparison_manifest.json"
    base_file = old_dir / "translation_manifest.json"
    new_file = new_dir / "translation_manifest.json"
    cmp = json.loads(compare_file.read_text(encoding="utf-8"))
    base = json.loads(base_file.read_text(encoding="utf-8"))
    new = json.loads(new_file.read_text(encoding="utf-8"))
    require(cmp.get("stage") == "T3_AUTO_TR_V021_COMPARATIVE_QA"
            and cmp.get("status") == "EXPLORATORY_RULE_COMPARISON_NOT_HUMAN_VERIFIED"
            and cmp.get("all_original_english_id_label_preserved") is True
            and cmp.get("all_changes_from_evidence_pinned_patches") is True
            and cmp.get("human_validation") is False
            and cmp.get("projected_labels_are_gold") is False,
            "Unverified completed, fail-closed comparison required")
    require(sha256(base_file) == cmp.get("original_manifest_sha256")
            and sha256(new_file) == cmp.get("candidate_manifest_sha256"),
            "Original or patched version manifest SHA mismatch")
    require(base.get("total_translated_rows") == 10804
            and new.get("total_translated_rows") == 10804
            and base.get("projected_labels_are_gold") is False
            and new.get("projected_labels_are_gold") is False,
            "Expected original/projected 10,804 labels, not gold data")

    counts: dict[str, Counter] = defaultdict(Counter)
    transitions: dict[tuple[str, str, str], Counter] = defaultdict(Counter)
    field_changes = Counter()
    rows_changed = Counter()
    label_counts = Counter()
    label_edited = Counter()
    label_priority_transitions = Counter()
    changed_by_split = Counter()
    for split in SPLITS:
        orig_path = old_dir / f"{OUT_STEM[split]}.csv"
        new_path = new_dir / f"{OUT_STEM[split]}.csv"
        require(sha256(orig_path) == base["splits"][split]["output_sha256"],
                f"Original split hash changed: {split}")
        require(sha256(new_path) == new["splits"][split]["output_sha256"],
                f"Candidate split hash changed: {split}")
        with orig_path.open(newline="", encoding="utf-8-sig") as f1, \
             new_path.open(newline="", encoding="utf-8-sig") as f2:
            a_rows = csv.DictReader(f1)
            b_rows = csv.DictReader(f2)
            require(a_rows.fieldnames == b_rows.fieldnames,
                    f"Split schema mismatch: {split}")
            for i, (a, b) in enumerate(zip_longest(a_rows, b_rows)):
                require(a is not None and b is not None, f"Split length mismatch: {split}")
                require(all(a[c] == b[c] for c in UNCHANGED),
                        f"Label, ID or original English text changed: {split}/{i}")
                row_key = f"{split}:{i}"
                label = a["label"]
                label_counts[(split, label)] += 1
                changed = tuple(field for field in TEXT_FIELDS if a[field] != b[field])
                for field in changed:
                    field_changes[(split, field)] += 1
                old_p = row_priority(row_key, a)
                new_p = row_priority(row_key, b)
                counts[(split, "before")][old_p] += 1
                counts[(split, "after")][new_p] += 1
                transitions[(split, old_p, new_p)]["rows"] += 1
                if changed:
                    changed_by_split[split] += 1
                    label_edited[(split, label)] += 1
                    transitions[(split, old_p, new_p)]["edited"] += 1
                    label_priority_transitions[(label, old_p, new_p)] += 1

    summary_old = cmp["by_split_original"]
    summary_new = cmp["by_split_candidate"]
    for split in SPLITS:
        before = counts[(split, "before")]
        after = counts[(split, "after")]
        require(sum(before.values()) == sum(after.values())
                == summary_old[split]["rows"] == summary_new[split]["rows"],
                f"Split count mismatch: {split}")
        for key in PRIORITIES:
            require(before[key] == summary_old[split][key]
                    and after[key] == summary_new[split][key],
                    f"Priority counts diverged from verified comparison: {split}/{key}")
    require(sum(changed_by_split.values()) == cmp["edited_distinct_rows"],
            "Changed distinct row count changed since accepted comparison")
    require(sum(field_changes.values()) == cmp["edited_field_occurrences"],
            "Changed field occurrence count changed since accepted comparison")
    require(sum(x["rows"] for x in summary_new.values()) == 10804,
            "Corpus coverage mismatch")

    movement_rows = [
        {
            "split": split, "old_priority": before, "new_priority": after,
            "row_count": transitions[(split, before, after)]["rows"],
            "edited_row_count": transitions[(split, before, after)]["edited"],
        }
        for split in SPLITS for before in PRIORITIES for after in PRIORITIES
    ]
    field_rows = [
        {"split": split, "field": field, "changed_field_occurrences": field_changes[(split, field)]}
        for split in SPLITS for field in TEXT_FIELDS
    ]
    label_rows = [
        {"split": split, "original_label": label,
         "source_rows": label_counts[(split, label)],
         "edited_rows": label_edited[(split, label)]}
        for split, label in sorted(label_counts)
    ]
    totals_before = Counter()
    totals_after = Counter()
    for split in SPLITS:
        totals_before.update(counts[(split, "before")])
        totals_after.update(counts[(split, "after")])
    result = {
        "stage": "T3_AUTO_V021_PRE_T4_IMPACT_AUDIT",
        "status": "OFFLINE_PROJECTED_LABELS_AGGREGATE_ONLY",
        "input_rows": 10804,
        "original_priority_counts": {p: totals_before[p] for p in PRIORITIES},
        "candidate_priority_counts": {p: totals_after[p] for p in PRIORITIES},
        "edited_distinct_rows": sum(changed_by_split.values()),
        "edited_field_occurrences": sum(field_changes.values()),
        "edited_by_split": dict(changed_by_split),
        "changed_fields_by_split": {
            split: {field: field_changes[(split, field)] for field in TEXT_FIELDS}
            for split in SPLITS
        },
        "label_count_groups": len(label_rows),
        "original_source_and_projected_labels_unchanged": True,
        "input_comparison_manifest_sha256": sha256(compare_file),
        "input_original_manifest_sha256": sha256(base_file),
        "input_candidate_manifest_sha256": sha256(new_file),
        "human_validated": False,
        "gold_translation_quality_claim": False,
        "note": "Transitions in heuristic QA priority are not validated translation quality; label counts are inherited from English.",
    }
    stage.mkdir(parents=True)
    try:
        save_csv(stage / "row_priority_transitions.csv", movement_rows, OUTPUT_FIELDS)
        save_csv(stage / "field_changes_by_split.csv", field_rows,
                 ("split", "field", "changed_field_occurrences"))
        save_csv(stage / "label_edit_counts.csv", label_rows,
                 ("split", "original_label", "source_rows", "edited_rows"))
        lines = [
            "# T3-AUTO v0.2.1 — Pre-T4 exploratory impact audit", "",
            "Original and candidate: 10,804 projected-label SciEntsBank records",
            f"Edited distinct records: {result['edited_distinct_rows']}",
            f"Edited translated text-field occurrences: {result['edited_field_occurrences']}",
            "English originals, IDs and projected labels preserved; no human gold review.", "",
            "## Changed field counts by split", "",
            "| Split | Question | Reference | Student answer | Edited rows |",
            "|---|---:|---:|---:|---:|",
        ]
        for split in SPLITS:
            by_field = result["changed_fields_by_split"][split]
            lines.append(
                f"| {split} | {by_field['question']} | {by_field['reference_answer']} | "
                f"{by_field['student_answer']} | {changed_by_split[split]} |")
        lines += ["", "## Heuristic priority transition counts", "",
                  "The full 3×3 HIGH/MEDIUM/UNFLAGGED matrices are in row_priority_transitions.csv.",
                  "Changes in priority are heuristic warnings, not proof of meaning preservation.",
                  "Original student misconceptions may still have been altered; no individual claims are made.",
                  "No student text or IDs are written to these aggregate output files.", ""]
        (stage / "impact_summary.md").write_text("\n".join(lines), encoding="utf-8")
        result["outputs"] = {
            f.name: sha256(f) for f in stage.iterdir() if f.is_file()
        }
        (stage / "impact_manifest.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        stage.rename(out)
        print("PRE-T4 IMPACT AUDIT PASS")
        print("Edited rows:", result["edited_distinct_rows"])
        print("Changed field occurrences:", result["edited_field_occurrences"])
        for split in SPLITS:
            print(split, result["changed_fields_by_split"][split])
        print("Output:", out)
        return result
    except BaseException:
        print("Incomplete aggregate output kept at", stage)
        raise


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--old-dir", type=Path, default=Path("data/tr_v0_2"))
    p.add_argument("--new-dir", type=Path, default=Path("data/tr_v0_2_1"))
    p.add_argument("--comparison", type=Path, default=Path("reports/tr_compare_v021"))
    p.add_argument("--out", type=Path, default=Path("reports/tr_impact_v021"))
    a = p.parse_args()
    audit(a.old_dir, a.new_dir, a.comparison, a.out)


if __name__ == "__main__":
    main()
