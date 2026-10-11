"""P0-gated full SciEntsBank-TR offline QA scan and source-concept grouping.

Never changes source/target CSVs or labels; candidate flags are NOT verified errors.
No network, API keys, hosted models or human review impersonation.

Example:
 python audit_translation_corpus.py --data-dir data/tr_v0_2 --source-dir data/raw --out reports/tr_auto_full_v01 --sample reports/tr_review/blind_stage1/review_A_blind.csv --sample-summary reports/tr_auto_qa_v03/qa_summary.json
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from contextlib import ExitStack
import csv
import hashlib
from itertools import zip_longest
import json
from pathlib import Path

import pandas as pd

from audit_dataset import SPLITS, EXPECTED, read_split
from download_data import REVISION
from audit_translation_quality import analyze_pair
from tr_adaptation.pipeline import OUT_STEM, TEXT_COLUMNS

FIELDS = (
    ("question", "source_question_en", "question"),
    ("reference_answer", "source_reference_answer_en", "reference_answer"),
    ("student_answer", "source_student_answer_en", "student_answer"),
)
CHECK_FIELDS = ("item_key",) + tuple(c for _, en, tr in FIELDS for c in (en, tr))
CSV_FIELDS = ("item_key", "split", "field", "priority", "rule", "concept",
              "reason_tr", "source_en", "target_tr", "status")
CONCEPTS = {
    "CALCITE_AS_ANALYSIS": "calcite",
    "BULB_AS_BUS": "bulb", "NAIL_AS_FINGERNAIL": "nail",
    "SQUARE_AS_CHALLENGE": "square", "PLANT_POT_AS_SAUCEPAN": "plant_pot",
    "CHEMICAL_SOLID_AS_STURDY": "solid",
    "FOGGED_GLASS_AS_SHINY": "fogged_glass", "NO_SLOPE_AS_NONSENSE": "slope",
    "STORE_FOOD_AS_SHOP": "store_food", "SKINNY_AS_SKIN": "skinny",
    "EVAPORATE_AS_DISCHARGE": "evaporate", "ERODE_AS_ENGLISH_REMNANT": "erosion",
    "JUICE_AS_WATER": "juice", "SATURATION_POLARITY_REVERSED": "saturation",
    "MILLILITER_AS_LITER": "milliliter",
    "NUMBER_CHANGED": "numbers", "NEGATION_NOT_EVIDENT": "negation",
    "EXCLUSIVITY_NOT_EVIDENT": "exclusivity",
    "COMPARATIVE_DIRECTION": "comparative",
    "LENGTH_OUTLIER": "length", "UNCHANGED": "untranslated_whole_text",
    "EMPTY_TRANSLATION": "empty_translation", "ENGLISH_TERM_LEFTOVER": "english_lexeme",
}


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fp:
        for chunk in iter(lambda: fp.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def concept_of(rule: str) -> str:
    if rule.startswith("TERM_NOT_EVIDENT:"):
        value = rule.partition(":")[2]
        return {"bulb_in_circuits": "bulb", "nail_in_magnets": "nail"}.get(value, value)
    return CONCEPTS.get(rule, "other:" + rule)


def pair_digest(flag: dict) -> str:
    payload = (flag["field"] + "\0" + flag["source_en"] +
               "\0" + flag["target_tr"]).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def sample_check(sample: Path, qa_summary: Path, blind_manifest: Path | None):
    require(sample.is_file() and qa_summary.is_file(),
            "Both prior T3.1 blind sample and T3-AUTO v0.2 summary are required")
    summary = json.loads(qa_summary.read_text(encoding="utf-8"))
    require(summary.get("analysis_type") == "OFFLINE_HEURISTIC_TRANSLATION_TRIAGE",
            "Not an automatic QA summary")
    require(sha256(sample) == summary.get("input_sha256"),
            "Sample changed since the previously reported QA scan")
    if blind_manifest:
        meta = json.loads(blind_manifest.read_text(encoding="utf-8"))
        require(meta.get("n_items") == 240, "Blind manifest sample size differs")
        if sample.name == "review_A_blind.csv":
            require(meta["outputs"]["A"]["sha256"] == sha256(sample),
                    "Blind sample differs from original manifest")
    with sample.open("r", encoding="utf-8-sig", newline="") as fp:
        reader = csv.DictReader(fp)
        require(reader.fieldnames is not None and set(CHECK_FIELDS).issubset(reader.fieldnames),
                "Blind sample missing source/target fields")
        rows = list(reader)
    require(len(rows) == 240, "Expected the frozen 240-row T3 sample")
    d = {}
    for row in rows:
        key = row["item_key"]
        require(key not in d and key, "Duplicate or blank sample key")
        d[key] = row
    return d, summary


class Group:
    def __init__(self):
        self.flags = 0
        self.high = 0
        self.medium = 0
        self.rows = set()
        self.pairs = set()
        self.rules = Counter()
        self.fields = Counter()

    def record(self, flag: dict):
        self.flags += 1
        self.high += flag["priority"] == "HIGH"
        self.medium += flag["priority"] == "MEDIUM"
        self.rows.add(flag["item_key"])
        self.pairs.add(pair_digest(flag))
        self.rules[flag["rule"]] += 1
        self.fields[flag["field"]] += 1

    def result(self, concept: str, split: str = "ALL") -> dict:
        return {
            "concept": concept, "split": split, "flag_occurrences": self.flags,
            "high_occurrences": self.high, "medium_occurrences": self.medium,
            "distinct_review_rows": len(self.rows),
            "distinct_source_target_field_pairs": len(self.pairs),
            "rule_counts": json.dumps(dict(sorted(self.rules.items())), ensure_ascii=False),
            "field_counts": json.dumps(dict(sorted(self.fields.items())), ensure_ascii=False),
        }


def write_table(path: Path, rows: list[dict], fields: list[str]):
    with path.open("w", newline="", encoding="utf-8-sig") as fp:
        writer = csv.DictWriter(fp, fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _compare_sample(found: dict, previous: dict):
    checks = ("rows", "high_priority_rows", "medium_priority_rows", "unflagged_rows",
              "total_flags", "rule_counts")
    mismatch = {k: {"old": previous.get(k), "recomputed": found.get(k)}
                for k in checks if previous.get(k) != found.get(k)}
    require(not mismatch, "QA rule drift relative to frozen T3 sample: " + str(mismatch))
    return {k: found.get(k) for k in checks}


def run(data_dir: Path, source_dir: Path, sample: Path, sample_summary: Path,
        out: Path, blind_manifest: Path | None = None) -> dict:
    data_dir, source_dir, out = data_dir.resolve(), source_dir.resolve(), out.resolve()
    require(not out.is_relative_to(data_dir) and not out.is_relative_to(source_dir),
            "Output cannot be within original data/translation directories")
    stage = out.with_name(out.name + ".part")
    require(not out.exists() and not stage.exists(),
            "Output or staging directory exists; use a new --out")
    samples, previous = sample_check(sample, sample_summary, blind_manifest)

    manifest = json.loads((data_dir / "translation_manifest.json").read_text(encoding="utf-8"))
    require(manifest.get("scope") == "FULL_CANDIDATE", "Partial translation not allowed")
    require(manifest.get("validation_state") == "UNVERIFIED_MACHINE_TRANSLATION",
            "Unexpected translation status")
    require(manifest.get("projected_labels_are_gold") is False,
            "Source labels must NOT be claimed as Turkish gold")
    require(manifest.get("total_translated_rows") == 10804,
            "Expected complete 10804-row source translation")
    if (source_dir / "file_manifest.json").exists():
        # Original downloader revision and hashes remain pinned by P0.
        orig_manifest = json.loads((source_dir / "file_manifest.json").read_text(encoding="utf-8"))
        require(orig_manifest.get("revision") == REVISION,
                "Source dataset pinned revision differs from official downloader")
        original_files = {item["filename"]: item["sha256"]
                          for item in orig_manifest.get("files", [])}
        require(len(original_files) == 4, "Original source file manifest is incomplete")
    else:
        raise RuntimeError("Original source file_manifest.json required")

    for split in SPLITS:
        source, source_path = read_split(source_dir, split)
        translated_path = data_dir / f"{OUT_STEM[split]}.csv"
        require(translated_path.is_file(), f"Missing translated split {split}")
        require(len(source) == sum(EXPECTED[split].values()),
                f"Unexpected official source split rows: {split}")
        require(manifest["splits"][split]["source_rows"] == len(source) and
                manifest["splits"][split]["translated_rows"] == len(source),
                f"Split {split} is not 1:1")
        require(sha256(source_path) == manifest["source_file_sha256"][split]
                and sha256(source_path) == original_files.get(source_path.name),
                f"Source hash changed or not listed in pinned source manifest: {split}")
        require(sha256(translated_path) == manifest["splits"][split]["output_sha256"],
                f"Translation hash changed: {split}")
    require(manifest["model_key"] == json.loads(
            (sample.parent.parent / "review_manifest.json").read_text(encoding="utf-8")
        )["source_manifest_model_key"],
        "Sample and full candidate corpus model keys differ")

    from audit_translation_quality import scan_rows
    sample_flags, sample_queue, sample_recomputed = scan_rows(list(samples.values()))
    frozen_sample = _compare_sample(sample_recomputed, previous)
    sample_rules = Counter(f["rule"] for f in sample_flags)
    sample_concepts = Counter(concept_of(f["rule"]) for f in sample_flags)

    summary_splits = {}
    all_rules, all_fields, all_concepts = Counter(), Counter(), Counter()
    by_concept, by_concept_split = defaultdict(Group), defaultdict(Group)
    repeated = {}
    sample_ids_in_full = set()
    full_all_rows = 0
    full_high, full_medium, full_none, all_flags = 0, 0, 0, 0
    stage.mkdir(parents=True)
    try:
        with (stage / "full_translation_flags.csv").open("w", encoding="utf-8-sig", newline="") as handle:
            output = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
            output.writeheader()
            for split in SPLITS:
                source, _ = read_split(source_dir, split)
                source_iter = source.itertuples(index=False)
                fn = data_dir / f"{OUT_STEM[split]}.csv"
                split_total = high_rows = med_rows = unflagged_rows = split_flag_count = 0
                with fn.open("r", newline="", encoding="utf-8-sig") as infile:
                    reader = csv.DictReader(infile)
                    need = {"id", "label", "label_status", "translation_scope"} | set(
                        c for _, e, t in FIELDS for c in (e, t))
                    require(reader.fieldnames is not None and need.issubset(reader.fieldnames),
                            f"Invalid TR CSV schema: {split}")
                    for i, (row, original) in enumerate(zip_longest(reader, source_iter)):
                        require(row is not None and original is not None,
                                f"Translation split row length mismatch: {split}")
                        item_key = f"{split}:{i}"
                        require(row["id"] == str(original.id) and row["label"] == str(original.label),
                                f"Original ID or source label changed: {item_key}")
                        require(row["label_status"] == "UNVERIFIED_TRANSFER" and
                                row["translation_scope"] == "FULL_CANDIDATE",
                                f"Invalid projected-label scope: {item_key}")
                        row_flags = []
                        for field, en_col, tr_col in FIELDS:
                            val = getattr(original, field)
                            en = "" if pd.isna(val) else str(val)
                            require(row[en_col] == en,
                                    f"English source text changed: {item_key}/{field}")
                            row_flags.extend(analyze_pair(item_key, field, en, row[tr_col]))
                        if item_key in samples:
                            for field, en_col, tr_col in FIELDS:
                                require(row[en_col] == samples[item_key][en_col]
                                        and row[tr_col] == samples[item_key][tr_col],
                                        f"Sample and full data mismatch: {item_key}/{field}")
                            sample_ids_in_full.add(item_key)
                        high = any(f["priority"] == "HIGH" for f in row_flags)
                        medium = bool(row_flags) and not high
                        high_rows += int(high)
                        med_rows += int(medium)
                        unflagged_rows += int(not row_flags)
                        split_total += 1
                        for f in row_flags:
                            concept = concept_of(f["rule"])
                            output.writerow({**f, "split": split, "concept": concept})
                            split_flag_count += 1
                            all_rules[f["rule"]] += 1
                            all_fields[f["field"]] += 1
                            all_concepts[concept] += 1
                            by_concept[concept].record(f)
                            by_concept_split[(concept, split)].record(f)
                            pair = (concept, f["rule"], pair_digest(f))
                            if pair not in repeated:
                                repeated[pair] = {"concept": concept,
                                                  "field": f["field"], "rule": f["rule"],
                                                  "source_target_sha256": pair[2],
                                                  "occurrences": 0,
                                                  "source_en": f["source_en"],
                                                  "target_tr": f["target_tr"]}
                            repeated[pair]["occurrences"] += 1
                require(split_total == len(source), f"Unexpected translated row count {split}")
                summary_splits[split] = {
                    "rows": split_total,
                    "high_priority_rows": high_rows,
                    "medium_priority_rows": med_rows,
                    "unflagged_rows": unflagged_rows, "flags": split_flag_count
                }
                full_all_rows += split_total
                full_high += high_rows
                full_medium += med_rows
                full_none += unflagged_rows
                all_flags += split_flag_count
                print(f"{split}: {split_total} scanned; {high_rows} HIGH; {med_rows} MEDIUM; "
                      f"{unflagged_rows} unflagged; {split_flag_count} flags", flush=True)
        require(full_all_rows == 10804, "Full candidate corpus coverage incomplete")
        require(sample_ids_in_full == set(samples), "Missing selected T3 sample rows in full corpus")
        fieldnames = ["concept", "split", "flag_occurrences", "high_occurrences",
                      "medium_occurrences", "distinct_review_rows",
                      "distinct_source_target_field_pairs", "rule_counts", "field_counts"]
        groups = [g.result(concept) for concept, g in by_concept.items()]
        groups.sort(key=lambda r: (-r["flag_occurrences"], r["concept"]))
        write_table(stage / "concept_summary.csv", groups, fieldnames)
        by_split = [g.result(concept, split) for (concept, split), g in by_concept_split.items()]
        by_split.sort(key=lambda r: (r["concept"], r["split"]))
        write_table(stage / "concept_by_split.csv", by_split, fieldnames)
        repeat_cases = [r for r in repeated.values() if r["occurrences"] > 1]
        repeat_cases.sort(key=lambda x: (-x["occurrences"], x["concept"], x["source_target_sha256"]))
        write_table(stage / "repeated_evidence.csv", repeat_cases,
                    ["concept", "field", "rule", "source_target_sha256",
                     "occurrences", "source_en", "target_tr"])
        report = {
            "stage": "T3_AUTO_FULL_CORPUS_TRIAGE",
            "status": "AUTOMATIC_CANDIDATE_NOT_HUMAN_VERIFIED",
            "input_rows": full_all_rows, "input_splits": summary_splits,
            "high_priority_rows": full_high,
            "medium_priority_rows": full_medium, "unflagged_rows": full_none,
            "candidate_flagged_rows": full_high + full_medium,
            "total_flags": all_flags, "rule_counts": dict(sorted(all_rules.items())),
            "concept_counts": dict(sorted(all_concepts.items())),
            "source_field_counts": dict(sorted(all_fields.items())),
            "distinct_concepts": len(groups),
            "repeated_evidence_cases": len(repeat_cases),
            "input_model_key": manifest["model_key"],
            "input_model_sha256": manifest["model"]["package_sha256"],
            "source_translation_manifest_sha256": sha256(data_dir / "translation_manifest.json"),
            "qa_rules_sha256": sha256(Path(__import__("audit_translation_quality").__file__)),
            "source_csv_sha256": {split: manifest["splits"][split]["output_sha256"]
                                  for split in SPLITS},
            "frozen_sample_recheck": frozen_sample,
            "sample_rule_counts": dict(sorted(sample_rules.items())),
            "sample_concept_counts": dict(sorted(sample_concepts.items())),
            "sample_vs_full_warning": "240-row balanced review sample is not a random probability sample; do not estimate full error rate from flags.",
            "no_human_labels": True, "no_corrections_applied": True,
            "no_gold_data": True, "no_flags_does_not_prove_correctness": True,
        }
        (stage / "full_qa_summary.json").write_text(
            json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        summary_md = [
            "# Full SciEntsBank TR candidate QA — Offline deterministic triage", "",
            f"- 10,804 source-to-translation rows: **{full_all_rows} scanned**",
            f"- High-priority candidate rows: **{full_high}**",
            f"- Medium-priority candidate rows: **{full_medium}**",
            f"- Rule-unflagged rows: **{full_none}**",
            f"- Field-level rule triggers: **{all_flags}**",
            "- T3.0 240-sample re-check: **PASS** (identical records, same rules and aggregate counters)",
            "",
            "## Most frequent concept groups", "",
            "| Source concept | Trigger occurrences | Distinct review rows | Unique field/text pairs |",
            "|---|---:|---:|---:|",
        ]
        for group in groups[:30]:
            summary_md.append("| {concept} | {flag_occurrences} | {distinct_review_rows} | "
                              "{distinct_source_target_field_pairs} |".format(**group))
        summary_md += [
            "", "## Interpretation limits", "",
            "All flags are *unverified* translation error hypotheses and may be false positives.",
            "No rule flag does NOT establish correctness. Repeated rows/translation pairs are counted separately.",
            "All four splits and three text fields were examined; reference, question and student answer flags must not be mixed.",
            "The 240 review sample is balanced, not a probability sample; prevalence cannot be inferred.",
            "No source labels or translated student text were rewritten; no human review/kappa/gold claims.",
            "Raw examples in full_translation_flags.csv and repeated_evidence.csv must remain local.", "",
        ]
        (stage / "full_qa_summary.md").write_text("\n".join(summary_md), encoding="utf-8")
        report["outputs"] = {
            f.name: sha256(f) for f in stage.iterdir()
            if f.is_file() and f.name != "full_qa_summary.json"
        }
        (stage / "full_qa_summary.json").write_text(
            json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        stage.rename(out)
        print(f"COMPLETE: {full_all_rows} rows, {full_high} HIGH, {full_medium} MEDIUM, "
              f"{all_flags} flags; output={out}")
        return report
    except BaseException:
        # Keep .part for forensic inspection, never pretend a partial run completed.
        print(f"INCOMPLETE: partial output preserved at {stage}")
        raise


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--data-dir", type=Path, default=Path("data/tr_v0_2"))
    p.add_argument("--source-dir", type=Path, default=Path("data/raw"))
    p.add_argument("--sample", type=Path, default=Path(
        "reports/tr_review/blind_stage1/review_A_blind.csv"))
    p.add_argument("--sample-summary", type=Path, default=Path(
        "reports/tr_auto_qa_v03/qa_summary.json"))
    p.add_argument("--blind-manifest", type=Path, default=Path(
        "reports/tr_review/blind_stage1/blind_manifest.json"))
    p.add_argument("--out", type=Path, default=Path("reports/tr_auto_full_v01"))
    args = p.parse_args()
    run(args.data_dir, args.source_dir, args.sample, args.sample_summary,
        args.out, args.blind_manifest)


if __name__ == "__main__":
    main()
