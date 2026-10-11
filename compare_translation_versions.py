"""Full 10,804-row, 3-field QA comparison of immutable v0.2 and candidate v0.2.1.

Reports *heuristic triggers*, never semantic accuracy. Offline and read-only.
python compare_translation_versions.py --old-dir data/tr_v0_2 --new-dir data/tr_v0_2_1 --full-qa reports/tr_auto_full_v01 --plan-dir reports/tr_patch_plan_v021_ai_draft --out reports/tr_compare_v021
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
from itertools import zip_longest
import hashlib
import json
from pathlib import Path

from audit_dataset import SPLITS
from audit_translation_quality import analyze_pair
from audit_translation_corpus import concept_of, sha256
from tr_adaptation.pipeline import OUT_STEM
from tr_adaptation.quality import review_flags

FIELDS = ("question", "reference_answer", "student_answer")
UNCHANGED_COLUMNS = ("id", "label", "label_status", "translation_scope") + tuple(
    "source_" + field + "_en" for field in FIELDS
)
DETAIL_FIELDS = ("item_key", "split", "field", "source_en", "original_tr", "patched_tr",
                 "original_tr_sha256", "patched_tr_sha256", "previous_rules",
                 "candidate_rules", "rules_removed", "rules_introduced", "ai_draft_status")


def require(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def write_csv(path: Path, rows: list[dict], names: tuple[str, ...]):
    with path.open("w", newline="", encoding="utf-8-sig") as fp:
        writer = csv.DictWriter(fp, fieldnames=names, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def flagset(key: str, field: str, en: str, tr: str) -> list[dict]:
    return analyze_pair(key, field, en, tr)


def _tier(flags: list[dict]) -> str:
    return "HIGH" if any(x["priority"] == "HIGH" for x in flags) else (
        "MEDIUM" if flags else "UNFLAGGED"
    )


def scan(old_dir: Path, new_dir: Path, full_qa: Path, plan_dir: Path, out: Path) -> dict:
    old_dir, new_dir, full_qa, plan_dir, out = (
        x.resolve() for x in (old_dir, new_dir, full_qa, plan_dir, out)
    )
    require(old_dir != new_dir and not new_dir.is_relative_to(old_dir)
            and not old_dir.is_relative_to(new_dir), "Source and candidate datasets overlap")
    require(not any(out.is_relative_to(x) or x.is_relative_to(out)
                    for x in (old_dir, new_dir, full_qa, plan_dir)),
            "Output cannot overlap source/evidence directories")
    stage = out.with_name(out.name + ".part")
    require(not out.exists() and not stage.exists(), "Comparison report already exists")
    base_manifest_file = old_dir / "translation_manifest.json"
    candidate_manifest_file = new_dir / "translation_manifest.json"
    base_manifest = json.loads(base_manifest_file.read_text(encoding="utf-8"))
    version_manifest = json.loads(candidate_manifest_file.read_text(encoding="utf-8"))
    original_qa = json.loads((full_qa / "full_qa_summary.json").read_text(encoding="utf-8"))
    imported = json.loads((plan_dir / "import_manifest.json").read_text(encoding="utf-8"))
    require(base_manifest.get("pipeline_version") == "0.2.0"
            and base_manifest.get("scope") == "FULL_CANDIDATE"
            and base_manifest.get("validation_state") == "UNVERIFIED_MACHINE_TRANSLATION"
            and base_manifest.get("projected_labels_are_gold") is False,
            "Expected complete, unverified original v0.2 source")
    require(version_manifest.get("pipeline_version") == "0.2.1"
            and version_manifest.get("validation_state") == "UNVERIFIED_EXPLORATORY_AI_ASSISTED_PATCH"
            and version_manifest.get("projected_labels_are_gold") is False
            and version_manifest.get("human_validated") is False
            and version_manifest.get("english_baseline_modified") is False,
            "Expected unverified exploratory v0.2.1 provenance")
    require(sha256(base_manifest_file) == version_manifest.get("parent_translation_manifest_sha256")
            == original_qa.get("source_translation_manifest_sha256"),
            "Original manifest SHA changed since full QA")
    require(version_manifest.get("plan_candidate_file_sha256") ==
            sha256(plan_dir / "patch_candidates.csv") ==
            imported.get("ai_draft_csv_sha256"),
            "AI_DRAFT plan and applied patch provenance differ")
    require(version_manifest.get("priority_manifest_sha256") ==
            sha256(plan_dir.parent / "tr_auto_priority_v01" / "root_cause_manifest.json"),
            "Source root-cause manifest changed since candidate plan")
    require(sha256(new_dir / "patch_audit.csv") ==
            version_manifest.get("patch_audit_sha256"), "Patch audit SHA mismatch")
    require(original_qa.get("input_rows") == 10804 and
            version_manifest.get("total_translated_rows") == 10804,
            "10,804-row source/candidate scope required")

    # Cross-check that only the frozen full-sentence approved source-target pairs are edited.
    audit_file = new_dir / "patch_audit.csv"
    with audit_file.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        needed = {"cluster_id", "field", "source_en", "original_tr", "replacement_tr",
                  "matched_rows", "source_target_sha256", "curation_origin", "status"}
        require(reader.fieldnames is not None and needed.issubset(reader.fieldnames),
                "Patch audit schema missing")
        audit_rows = list(reader)
    require(len(audit_rows) == version_manifest["approved_exploratory_pair_patches"],
            "Approved patch count and audit rows differ")
    approved = {}
    for r in audit_rows:
        require(r["curation_origin"] in {"AI_DRAFT", "RESEARCHER_EDITED"} and
                r["status"] == "UNVERIFIED_EXPLORATORY_AI_ASSISTED_PATCH",
                "Patch origin changed or human provenance falsely asserted")
        proof = hashlib.sha256((r["field"] + "\0" + r["source_en"] + "\0"
                                + r["original_tr"]).encode("utf-8")).hexdigest()
        require(proof == r["source_target_sha256"], "Patch audit source/target SHA mismatch")
        key = (r["field"], r["source_en"], r["original_tr"], r["replacement_tr"])
        require(key not in approved, "Duplicate patch audit pair")
        approved[key] = r
    observed_patch_matches = Counter()
    changed_rows, changed_fields = 0, 0
    introduced_high_cases = []
    qa_old_by_split, qa_new_by_split = {}, {}
    rules_old, rules_new, concepts_old, concepts_new = (
        Counter(), Counter(), Counter(), Counter()
    )
    detail = []
    stage.mkdir(parents=True)
    try:
        for split in SPLITS:
            src_path = old_dir / f"{OUT_STEM[split]}.csv"
            dst_path = new_dir / f"{OUT_STEM[split]}.csv"
            require(sha256(src_path) == base_manifest["splits"][split]["output_sha256"]
                    == original_qa["source_csv_sha256"][split],
                    f"Original source SHA mismatch: {split}")
            require(sha256(dst_path) == version_manifest["splits"][split]["output_sha256"],
                    f"New candidate SHA mismatch: {split}")
            old_row_counts = Counter()
            new_row_counts = Counter()
            split_rows = 0
            with src_path.open(newline="", encoding="utf-8-sig") as fa, \
                 dst_path.open(newline="", encoding="utf-8-sig") as fb:
                reader_a, reader_b = csv.DictReader(fa), csv.DictReader(fb)
                require(reader_a.fieldnames is not None and
                        reader_b.fieldnames == reader_a.fieldnames, "Unexpected CSV columns")
                for i, (a, b) in enumerate(zip_longest(reader_a, reader_b)):
                    require(a is not None and b is not None,
                            f"Versioned split lengths differ: {split}")
                    key = f"{split}:{i}"
                    require(all(a[col] == b[col] for col in UNCHANGED_COLUMNS),
                            f"Original English/labels/id/provenance modified: {key}")
                    require(a["label_status"] == "UNVERIFIED_TRANSFER" and
                            b["label_status"] == "UNVERIFIED_TRANSFER",
                            "Original projected label status was changed")
                    require(a["translation_scope"] == "FULL_CANDIDATE" and
                            b["translation_scope"] == "FULL_CANDIDATE",
                            "Translation scope changed")
                    require(set(a) == set(b), "Source and candidate schema mismatch")
                    altered_fields = []
                    flags_a, flags_b = [], []
                    for field in FIELDS:
                        en = a["source_" + field + "_en"]
                        old_flags = flagset(key, field, en, a[field])
                        new_flags = flagset(key, field, en, b[field])
                        flags_a.extend(old_flags)
                        flags_b.extend(new_flags)
                        rules_old.update(x["rule"] for x in old_flags)
                        rules_new.update(x["rule"] for x in new_flags)
                        concepts_old.update(concept_of(x["rule"]) for x in old_flags)
                        concepts_new.update(concept_of(x["rule"]) for x in new_flags)
                        if a[field] != b[field]:
                            altered_fields.append(field)
                            pair = (field, en, a[field], b[field])
                            require(pair in approved,
                                    f"Unapproved or unintended changed translation: {key}/{field}")
                            observed_patch_matches[pair] += 1
                            changed_fields += 1
                            before_rules = {x["rule"] for x in old_flags}
                            after_rules = {x["rule"] for x in new_flags}
                            new_high = {x["rule"] for x in new_flags
                                        if x["priority"] == "HIGH"} - {
                                        x["rule"] for x in old_flags if x["priority"] == "HIGH"}
                            if new_high:
                                introduced_high_cases.append((key, field, sorted(new_high)))
                            detail.append({
                                "item_key": key, "split": split, "field": field,
                                "source_en": en, "original_tr": a[field], "patched_tr": b[field],
                                "original_tr_sha256": hashlib.sha256(a[field].encode("utf-8")).hexdigest(),
                                "patched_tr_sha256": hashlib.sha256(b[field].encode("utf-8")).hexdigest(),
                                "previous_rules": "|".join(sorted(before_rules)),
                                "candidate_rules": "|".join(sorted(after_rules)),
                                "rules_removed": "|".join(sorted(before_rules-after_rules)),
                                "rules_introduced": "|".join(sorted(after_rules-before_rules)),
                                "ai_draft_status": "UNVERIFIED_EXPLORATORY_AI_ASSISTED_PATCH",
                            })
                    touched = bool(altered_fields)
                    if touched:
                        changed_rows += 1
                        expected_flags = []
                        for field in FIELDS:
                            english = b["source_" + field + "_en"]
                            if english.strip():
                                expected_flags += [field + ":" + q for q in review_flags(english, b[field])]
                            else:
                                expected_flags.append(field + ":EMPTY_SOURCE")
                        require(b["quality_flags"] == json.dumps(
                            sorted(set(expected_flags)), ensure_ascii=False),
                            f"Revised quality_flags not recomputed consistently: {key}")
                    else:
                        require(a["quality_flags"] == b["quality_flags"],
                                f"Quality flags changed without translation change: {key}")
                    unexpected = [name for name in a if name not in FIELDS
                                  and name != "quality_flags" and a[name] != b[name]]
                    require(not unexpected, "Unexpected non-translation column change: "
                            + key + " -> " + str(unexpected))
                    old_row_counts[_tier(flags_a)] += 1
                    new_row_counts[_tier(flags_b)] += 1
                    split_rows += 1
            require(split_rows == base_manifest["splits"][split]["source_rows"]
                    == version_manifest["splits"][split]["rows"],
                    f"Split row count mismatch: {split}")
            qa_old_by_split[split] = {
                "rows": split_rows, "HIGH": old_row_counts["HIGH"],
                "MEDIUM": old_row_counts["MEDIUM"],
                "UNFLAGGED": old_row_counts["UNFLAGGED"],
            }
            qa_new_by_split[split] = {
                "rows": split_rows, "HIGH": new_row_counts["HIGH"],
                "MEDIUM": new_row_counts["MEDIUM"],
                "UNFLAGGED": new_row_counts["UNFLAGGED"],
            }
            print(f"{split}: {split_rows} rows; HIGH {old_row_counts['HIGH']}→{new_row_counts['HIGH']}; "
                  f"MEDIUM {old_row_counts['MEDIUM']}→{new_row_counts['MEDIUM']}", flush=True)
        require(sum(x["rows"] for x in qa_old_by_split.values()) == 10804,
                "Full dataset rows missing")
        for split in SPLITS:
            check = original_qa["input_splits"][split]
            before = qa_old_by_split[split]
            require(before["HIGH"] == check["high_priority_rows"] and
                    before["MEDIUM"] == check["medium_priority_rows"] and
                    before["UNFLAGGED"] == check["unflagged_rows"],
                    "Original full QA row totals no longer reproducible: " + split)
        require(dict(sorted(rules_old.items())) == original_qa.get("rule_counts"),
                "Original full QA rule distribution changed")
        require(sum(rules_old.values()) == original_qa["total_flags"],
                "Original full QA count differs")
        require(changed_fields == version_manifest["edited_field_occurrences"]
                and changed_rows == version_manifest["edited_distinct_rows"],
                "Manifest edited row/field counts inconsistent with real CSVs")
        require(len(observed_patch_matches) == len(approved) and
                all(observed_patch_matches[entry] == int(audit["matched_rows"])
                    for entry, audit in approved.items()),
                "Reported patch occurrences differ from actual modified rows")
        require(not introduced_high_cases,
                f"New HIGH scientific-error rule introduced: {introduced_high_cases[:5]}")
        deltas = []
        for rule in sorted(set(rules_old) | set(rules_new)):
            before, after = rules_old[rule], rules_new[rule]
            deltas.append({"rule": rule, "before": before, "after": after,
                           "delta": after-before})
        concept_delta = []
        for concept in sorted(set(concepts_old) | set(concepts_new)):
            before, after = concepts_old[concept], concepts_new[concept]
            concept_delta.append({"concept": concept, "before": before,
                                  "after": after, "delta": after-before})
        summary = {
            "stage": "T3_AUTO_TR_V021_COMPARATIVE_QA",
            "status": "EXPLORATORY_RULE_COMPARISON_NOT_HUMAN_VERIFIED",
            "original_rows": 10804, "candidate_rows": 10804,
            "patch_count": len(approved),
            "edited_distinct_rows": changed_rows, "edited_field_occurrences": changed_fields,
            "original_total_rule_flags": sum(rules_old.values()),
            "candidate_total_rule_flags": sum(rules_new.values()),
            "rule_flags_delta": sum(rules_new.values()) - sum(rules_old.values()),
            "by_split_original": qa_old_by_split, "by_split_candidate": qa_new_by_split,
            "new_high_rule_regressions_on_patched_fields": len(introduced_high_cases),
            "original_manifest_sha256": sha256(base_manifest_file),
            "candidate_manifest_sha256": sha256(candidate_manifest_file),
            "source_qa_sha256": sha256(full_qa / "full_qa_summary.json"),
            "source_patch_audit_sha256": sha256(audit_file),
            "all_original_english_id_label_preserved": True,
            "all_changes_from_evidence_pinned_patches": True,
            "projected_labels_are_gold": False, "human_validation": False,
            "note": "A reduction in heuristic flags does not prove translation meaning is preserved or that classifier metrics will improve.",
        }
        write_csv(stage / "changed_field_comparison.csv", detail, DETAIL_FIELDS)
        write_csv(stage / "rule_delta.csv", deltas, ("rule", "before", "after", "delta"))
        write_csv(stage / "concept_delta.csv", concept_delta,
                  ("concept", "before", "after", "delta"))
        text = [
            "# SciEntsBank-TR v0.2 → v0.2.1 — OFFLINE exploratory comparison", "",
            f"- 10,804 records in both versions; verified original ID, source EN and projected labels unchanged.",
            f"- Approved exact-pair patches: {len(approved)}",
            f"- Distinct records with a change: {changed_rows}",
            f"- Changed translation field occurrences: {changed_fields}",
            f"- Baseline rule triggers: {sum(rules_old.values())}",
            f"- Candidate rule triggers: {sum(rules_new.values())}",
            f"- Rule trigger delta: {summary['rule_flags_delta']:+d}",
            f"- Newly introduced HIGH flags: {len(introduced_high_cases)}", "",
            "## Crucial limitations", "",
            "These are deterministic heuristic trigger counts, not verified error rate, precision, recall or semantic quality.",
            "The proposed corrections came from AI_DRAFT without independent human review.",
            "Fewer flags can arise from lexical changes and do not prove all original scientific misconceptions survived.",
            "Original split CSV and v0.2.1 CSV contain private student text; keep detailed comparison local.",
            "Turkish projected labels remain UNVERIFIED_TRANSFER, never gold.", "",
        ]
        (stage / "comparison_summary.md").write_text("\n".join(text), encoding="utf-8")
        summary["outputs"] = {f.name: sha256(f) for f in stage.iterdir() if f.is_file()}
        (stage / "comparison_manifest.json").write_text(
            json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        stage.rename(out)
        print(f"COMPARE COMPLETE: {changed_rows} changed rows, {changed_fields} field edits, "
              f"{sum(rules_old.values())}→{sum(rules_new.values())} heuristic flags")
        return summary
    except BaseException:
        print("COMPARISON FAILED, partial files kept at", stage)
        raise


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--old-dir", type=Path, default=Path("data/tr_v0_2"))
    p.add_argument("--new-dir", type=Path, default=Path("data/tr_v0_2_1"))
    p.add_argument("--full-qa", type=Path, default=Path("reports/tr_auto_full_v01"))
    p.add_argument("--plan-dir", type=Path, default=Path("reports/tr_patch_plan_v021_ai_draft"))
    p.add_argument("--out", type=Path, default=Path("reports/tr_compare_v021"))
    args = p.parse_args()
    scan(args.old_dir, args.new_dir, args.full_qa, args.plan_dir, args.out)


if __name__ == "__main__":
    main()
