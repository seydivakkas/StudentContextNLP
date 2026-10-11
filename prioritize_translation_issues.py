"""Offline source-concept root-cause triage for frozen SciEntsBank-TR full QA.

Does not edit source, labels, review forms or translated outputs. Grouping
identifies repeated candidate *patterns*, not validated translation defects.
No network, API keys, hosted models, or gold-label claims.

python prioritize_translation_issues.py \
  --qa-dir reports/tr_auto_full_v01 \
  --out reports/tr_auto_priority_v01
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import json
from pathlib import Path

from audit_dataset import SPLITS
from audit_translation_corpus import concept_of

REQUIRED = frozenset({"item_key", "split", "field", "priority", "rule", "concept",
                      "reason_tr", "source_en", "target_tr", "status"})
FIELDS = {"question", "reference_answer", "student_answer"}
STATE = "AUTOMATIC_CANDIDATE_NOT_HUMAN_VERIFIED"

# Priority describes potential *scientific impact*, never statistical confidence.
CRITICAL = {"SATURATION_POLARITY_REVERSED", "MILLILITER_AS_LITER"}
TECHNICAL = {
    "CALCITE_AS_ANALYSIS", "BULB_AS_BUS", "NAIL_AS_FINGERNAIL",
    "SQUARE_AS_CHALLENGE", "PLANT_POT_AS_SAUCEPAN",
    "CHEMICAL_SOLID_AS_STURDY", "FOGGED_GLASS_AS_SHINY",
    "NO_SLOPE_AS_NONSENSE", "STORE_FOOD_AS_SHOP", "SKINNY_AS_SKIN",
    "EVAPORATE_AS_DISCHARGE", "ERODE_AS_ENGLISH_REMNANT", "JUICE_AS_WATER",
}
LEVEL = {"P1_SCIENTIFIC_POLARITY_OR_UNITS": 0,
         "P2_SPECIFIC_TECHNICAL_TERM": 1,
         "P3_SURFACE_HEURISTIC": 2}
CLUSTER_FIELDS = ["cluster_id", "concept", "field", "priority_tier",
                  "source_en", "target_tr", "source_target_sha256",
                  "rule_types", "rule_occurrences", "affected_distinct_rows",
                  "affected_splits", "split_counts", "high_rule_occurrences",
                  "candidate_state", "auto_apply"]
CONCEPT_FIELDS = ["concept", "priority_tier", "rule_occurrences",
                  "affected_distinct_rows", "distinct_source_target_field_pairs",
                  "repeated_clusters", "high_rule_occurrences",
                  "question_clusters", "reference_clusters", "student_clusters",
                  "top_rule_types", "candidate_state"]


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for part in iter(lambda: f.read(1024 * 1024), b""):
            h.update(part)
    return h.hexdigest()


def tier(rules: set[str]) -> str:
    if rules & CRITICAL:
        return "P1_SCIENTIFIC_POLARITY_OR_UNITS"
    if rules & TECHNICAL:
        return "P2_SPECIFIC_TECHNICAL_TERM"
    return "P3_SURFACE_HEURISTIC"


def _csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def aggregate(flags: list[dict], summary: dict) -> tuple[list[dict], list[dict], dict]:
    if summary.get("stage") != "T3_AUTO_FULL_CORPUS_TRIAGE":
        raise ValueError("Expected full-corpus QA summary")
    if summary.get("status") != STATE or not summary.get("no_gold_data") or not summary.get("no_corrections_applied"):
        raise ValueError("Unverified, read-only full QA provenance is mandatory")
    if summary.get("input_rows") != 10804:
        raise ValueError("Expected complete 10,804-row source corpus")

    clusters: dict[tuple[str, str, str], dict] = {}
    rules, concepts, fields, splits = Counter(), Counter(), Counter(), Counter()
    row_high, row_any = set(), set()

    for f in flags:
        if not REQUIRED.issubset(f):
            raise ValueError("Missing full QA flag columns")
        if f["status"] != STATE or f["priority"] not in ("HIGH", "MEDIUM"):
            raise ValueError("Unexpected flag provenance or priority")
        if f["field"] not in FIELDS or f["split"] not in SPLITS:
            raise ValueError("Invalid source field or split")
        if concept_of(f["rule"]) != f["concept"]:
            raise ValueError(f"Corrupt rule/concept mapping: {f['rule']}")
        if not f["item_key"].startswith(f["split"] + ":"):
            raise ValueError("Mismatch between split and item_key")
        index = f["item_key"].split(":", 1)[1]
        if not index.isdecimal() or int(index) >= summary["input_splits"][f["split"]]["rows"]:
            raise ValueError("Out-of-range item index")
        rules[f["rule"]] += 1
        concepts[f["concept"]] += 1
        fields[f["field"]] += 1
        splits[f["split"]] += 1
        row_any.add(f["item_key"])
        if f["priority"] == "HIGH":
            row_high.add(f["item_key"])

        source_hash = digest(
            (f["field"] + "\0" + f["source_en"] + "\0" + f["target_tr"]).encode("utf-8"))
        key = (f["concept"], f["field"], source_hash)
        if key not in clusters:
            clusters[key] = {
                "concept": f["concept"], "field": f["field"],
                "source_en": f["source_en"], "target_tr": f["target_tr"],
                "source_target_sha256": source_hash,
                "rules": Counter(), "split_counts": Counter(),
                "rows": set(), "high_occurrences": 0,
            }
        group = clusters[key]
        if group["source_en"] != f["source_en"] or group["target_tr"] != f["target_tr"]:
            raise ValueError("SHA256 collision in source/target evidence")
        group["rules"][f["rule"]] += 1
        group["split_counts"][f["split"]] += 1
        group["rows"].add(f["item_key"])
        group["high_occurrences"] += int(f["priority"] == "HIGH")

    if len(flags) != summary["total_flags"] or dict(rules) != summary.get("rule_counts"):
        raise ValueError("Full QA total/rule counts changed")
    if dict(concepts) != summary.get("concept_counts") or dict(fields) != summary.get("source_field_counts"):
        raise ValueError("Full QA concept/field counts changed")
    for split in SPLITS:
        expected = summary["input_splits"][split]
        if splits[split] != expected["flags"]:
            raise ValueError(f"Split flag count changed: {split}")
        found_high = sum(key.startswith(split + ":") for key in row_high)
        found_medium = sum(key.startswith(split + ":") for key in (row_any - row_high))
        if found_high != expected["high_priority_rows"] or found_medium != expected["medium_priority_rows"]:
            raise ValueError(f"Split row priority counts changed: {split}")
    if len(row_any) != summary["candidate_flagged_rows"]:
        raise ValueError("Full QA distinct candidate count changed")

    cluster_rows = []
    by_concept = defaultdict(lambda: {
        "occurrences": 0, "rows": set(), "pairs": 0, "repeated": 0,
        "high": 0, "rules": Counter(), "fields": Counter(), "rule_set": set()
    })
    for group in clusters.values():
        rules_set = set(group["rules"])
        prio = tier(rules_set)
        occurrences = sum(group["rules"].values())
        unique_rows = len(group["rows"])
        cluster_id = digest(
            (group["concept"] + "\0" + group["field"] + "\0" +
             group["source_target_sha256"]).encode("utf-8"))
        cluster_rows.append({
            "cluster_id": cluster_id,
            "concept": group["concept"], "field": group["field"],
            "priority_tier": prio,
            "source_en": group["source_en"], "target_tr": group["target_tr"],
            "source_target_sha256": group["source_target_sha256"],
            "rule_types": "|".join(sorted(rules_set)),
            "rule_occurrences": occurrences,
            "affected_distinct_rows": unique_rows,
            "affected_splits": "|".join(sorted(group["split_counts"])),
            "split_counts": json.dumps(dict(sorted(group["split_counts"].items()))),
            "high_rule_occurrences": group["high_occurrences"],
            "candidate_state": STATE, "auto_apply": "false",
        })
        g = by_concept[group["concept"]]
        g["occurrences"] += occurrences
        g["rows"].update(group["rows"])
        g["pairs"] += 1
        g["repeated"] += int(unique_rows > 1)
        g["high"] += group["high_occurrences"]
        g["rules"].update(group["rules"])
        g["fields"][group["field"]] += 1
        g["rule_set"].update(rules_set)
    cluster_rows.sort(key=lambda x: (LEVEL[x["priority_tier"]],
                                      -x["affected_distinct_rows"],
                                      -x["rule_occurrences"], x["cluster_id"]))
    concepts_out = []
    for concept, group in by_concept.items():
        concepts_out.append({
            "concept": concept,
            "priority_tier": tier(group["rule_set"]),
            "rule_occurrences": group["occurrences"],
            "affected_distinct_rows": len(group["rows"]),
            "distinct_source_target_field_pairs": group["pairs"],
            "repeated_clusters": group["repeated"],
            "high_rule_occurrences": group["high"],
            "question_clusters": group["fields"]["question"],
            "reference_clusters": group["fields"]["reference_answer"],
            "student_clusters": group["fields"]["student_answer"],
            "top_rule_types": "|".join(r for r, _ in group["rules"].most_common(5)),
            "candidate_state": STATE,
        })
    concepts_out.sort(key=lambda x: (LEVEL[x["priority_tier"]],
                                     -x["affected_distinct_rows"],
                                     -x["distinct_source_target_field_pairs"],
                                     x["concept"]))

    result = {
        "stage": "T3_AUTO_ROOT_CAUSE_PRIORITIZATION",
        "status": STATE,
        "full_corpus_rows": 10804, "full_corpus_flagged_candidates": len(row_any),
        "full_corpus_flags": len(flags),
        "source_concepts": len(concepts_out),
        "distinct_concept_field_source_target_clusters": len(cluster_rows),
        "clusters_with_repeated_rows": sum(x["affected_distinct_rows"] > 1 for x in cluster_rows),
        "priority_tier_cluster_counts": dict(sorted(Counter(
            x["priority_tier"] for x in cluster_rows).items())),
        "no_source_changes": True, "no_gold_labels": True,
        "no_human_rating_or_kappa": True,
        "note": "Risk categories are engineering heuristics, NOT calibrated probabilities or validated error labels. Source and translation examples remain local.",
    }
    return cluster_rows, concepts_out, result


def run(qa_dir: Path, out: Path) -> dict:
    qa_dir = qa_dir.resolve()
    out = out.resolve()
    stage = out.with_name(out.name + ".part")
    if out == qa_dir or out.is_relative_to(qa_dir) or qa_dir.is_relative_to(out):
        raise ValueError("Output must not overwrite full QA inputs")
    if out.parent != qa_dir.parent:
        raise ValueError("Output must be a separate sibling folder inside the same reports directory")
    if out.exists() or stage.exists():
        raise FileExistsError("Existing reports will not be overwritten")
    summary_file = qa_dir / "full_qa_summary.json"
    flags_file = qa_dir / "full_translation_flags.csv"
    summary = json.loads(summary_file.read_text(encoding="utf-8"))
    pinned_sha = summary.get("outputs", {}).get(flags_file.name)
    if not pinned_sha or pinned_sha != file_sha(flags_file):
        raise ValueError("Full QA flag CSV SHA-256 mismatch with source report manifest")
    with flags_file.open("r", encoding="utf-8-sig", newline="") as fp:
        reader = csv.DictReader(fp)
        if not reader.fieldnames or not REQUIRED.issubset(reader.fieldnames):
            raise ValueError("Full QA flag CSV schema mismatch")
        flags = list(reader)
    cluster_rows, concepts_out, result = aggregate(flags, summary)
    result["input_full_qa_sha256"] = file_sha(summary_file)
    result["input_full_flags_sha256"] = pinned_sha
    result["algorithm_version"] = "0.1.0"
    stage.mkdir(parents=True)
    try:
        _csv(stage / "root_cause_clusters.csv", cluster_rows, CLUSTER_FIELDS)
        _csv(stage / "concept_priority.csv", concepts_out, CONCEPT_FIELDS)
        lines = [
            "# T3-AUTO — Kaynak kavrama göre hata *adayı* önceliklendirme", "",
            f"- Tam kaynak kayıt: **{result['full_corpus_rows']}**",
            f"- İnceleme adayı kayıt: **{result['full_corpus_flagged_candidates']}**",
            f"- Kural bulgusu: **{result['full_corpus_flags']}**",
            f"- Farklı kavram+alan+kaynak/hedef grubu: **{len(cluster_rows)}**",
            f"- Birden fazla kayıtla ilişkili grup: **{result['clusters_with_repeated_rows']}**",
            "",
            "## Öncelikli kavramlar (risk sınıfı, farklı kayıt ve benzersiz metin kanıtı)", "",
            "| Kavram | Risk | Ayrı kayıt | Farklı alan/metin | Kural bulgusu |",
            "|---|---|---:|---:|---:|",
        ]
        for item in concepts_out[:20]:
            lines.append(
                f"| {item['concept']} | {item['priority_tier']} | "
                f"{item['affected_distinct_rows']} | "
                f"{item['distinct_source_target_field_pairs']} | "
                f"{item['rule_occurrences']} |")
        lines += [
            "", "## Metodoloji", "",
            "Tüm risk sınıfları yalnız mühendislik önceliği ifade eder; gerçek hata olasılığı değildir.",
            "Bir kayıt birden fazla kavramla ilişkilendirilebilir; kavramların kayıt sayıları toplanmaz.",
            "Aynı kavram/alan/kaynak/hedef çifti tek kök neden adayı altında gruplanır.",
            "Hiçbir öneri kaynak metinlere, etiketlere, mevcut çeviri veya A/B formlarına uygulanmadı.",
            "İşaretsiz kayıtlar da doğrulanmış doğru değildir. Cohen kappa/gold doğrulama yoktur.",
            "root_cause_clusters.csv tam kaynak ve çevrilmiş öğrenci metinleri içerebilir: GitHub'a yüklemeyin.",
            "",
        ]
        (stage / "root_cause_summary.md").write_text("\n".join(lines), encoding="utf-8")
        result["outputs"] = {
            f.name: file_sha(f) for f in stage.iterdir() if f.is_file()
        }
        (stage / "root_cause_manifest.json").write_text(
            json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        stage.rename(out)
    except BaseException:
        # Keep staged evidence for debugging, never claim finished result.
        raise
    print("Root-cause candidate groups:", len(cluster_rows))
    print("Repeated root-cause groups:", result["clusters_with_repeated_rows"])
    print("Concepts:", result["source_concepts"])
    print("Automatic changes: 0")
    print("Report:", out)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--qa-dir", type=Path, default=Path("reports/tr_auto_full_v01"))
    parser.add_argument("--out", type=Path, default=Path("reports/tr_auto_priority_v01"))
    args = parser.parse_args()
    run(args.qa_dir, args.out)


if __name__ == "__main__":
    main()
