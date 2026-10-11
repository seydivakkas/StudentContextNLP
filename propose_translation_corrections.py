"""Build auditable scientific-term repair SUGGESTIONS, never rewrite student answers.

Input: offline audit_translation_quality.py/translation_flags.csv
Output: proposals and aggregate manifest in a NEW reports/ directory.

These are deterministic concept-level suggestions, not sentence-level corrections,
not human labels, and not evidence that the projected original class is correct.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import json
from pathlib import Path

SUGGESTIONS = {
    "CALCITE_AS_ANALYSIS": ("calcite", "kalsit", "Mineral adını koru, anlamı 'analiz'e dönüştürme."),
    "BULB_AS_BUS": ("bulb", "ampul / lamba", "Elektrik devresindeki ampulü otobüs olarak çevirme."),
    "NAIL_AS_FINGERNAIL": ("nail", "metal çivi", "Mıknatıs bağlamında tırnak yerine çivi kullan."),
    "SQUARE_AS_CHALLENGE": ("square", "kare biçiminde", "Şekil bilgisini 'meydan okuma'ya dönüştürme."),
    "PLANT_POT_AS_SAUCEPAN": ("pot", "saksı", "Bitki ekilen kabı tencere olarak ifade etme."),
    "CHEMICAL_SOLID_AS_STURDY": ("solid", "katı madde / katı tanecikler", "Fiziksel halin 'sağlam' sıfatına dönüşmesini incele."),
    "FOGGED_GLASS_AS_SHINY": ("fogged up", "buğulandı / buharlandı", "Camın buğulanması, parlaması değildir."),
    "NO_SLOPE_AS_NONSENSE": ("no slope", "eğimsiz / eğim yok", "Yer şekli kavramını anlamlı biçimde koru."),
    "STORE_FOOD_AS_SHOP": ("store food", "yiyecek depolamak", "Fiil 'store' mağaza değil depolamaktır."),
    "SKINNY_AS_SKIN": ("skinny", "ince / zayıf", "Nesnenin niteliği cilt değil inceliktir."),
    "EVAPORATE_AS_DISCHARGE": ("evaporate", "buharlaşmak", "Buharlaşmayı boşaltma/tahliye etme olarak ifade etme."),
    "ERODE_AS_ENGLISH_REMNANT": ("erode", "aşınmak / erozyona uğramak", "İngilizce fiil kökünü çevirmeden bırakma."),
    "JUICE_AS_WATER": ("juice", "meyve suyu / özsu", "Sıvının özgül anlamını genel 'su'ya indirgeme; kaynak bağlamını koru."),
    "SATURATION_POLARITY_REVERSED": ("saturated", "doymuş", "Doymuş ile doymamış kavramları birbirinin tersidir."),
    "MILLILITER_AS_LITER": ("millilitre", "mililitre (mL)", "mL→L 1000 kat birim değişimidir; sayı ve birimi birlikte doğrula."),
}
MANDATORY = {"item_key", "field", "priority", "rule", "reason_tr", "source_en", "target_tr", "status"}
OUTPUT_FIELDS = [
    "item_key", "field", "rule", "priority", "source_term", "candidate_tr_term",
    "reason_tr", "source_en", "target_tr", "proposal_state", "auto_apply",
    "human_reviewed", "derived_label_validated", "source_target_sha256",
]


def _sha(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def analyze(flags: list[dict]) -> tuple[list[dict], dict]:
    proposals = []
    for f in flags:
        rule = f["rule"]
        if rule not in SUGGESTIONS or f["priority"] != "HIGH":
            continue
        origin = f.get("status", "")
        if origin != "AUTOMATIC_CANDIDATE_NOT_HUMAN_VERIFIED":
            raise ValueError(f"Unexpected source verification state: {origin!r}")
        source_term, replacement, note = SUGGESTIONS[rule]
        evidence = (f["source_en"] + "\0" + f["target_tr"]).encode("utf-8")
        proposals.append({
            "item_key": f["item_key"], "field": f["field"],
            "rule": rule, "priority": "HIGH",
            "source_term": source_term, "candidate_tr_term": replacement,
            "reason_tr": note, "source_en": f["source_en"],
            "target_tr": f["target_tr"],
            "proposal_state": "LEXICAL_CORRECTION_SUGGESTION_UNVERIFIED",
            "auto_apply": "false", "human_reviewed": "false",
            "derived_label_validated": "false", "source_target_sha256": _sha(evidence),
        })

    proposals.sort(key=lambda p: (p["item_key"], p["field"], p["rule"]))
    by_rule = Counter(p["rule"] for p in proposals)
    by_field = Counter(p["field"] for p in proposals)
    unique_evidence = {(p["field"], p["rule"], p["source_target_sha256"]) for p in proposals}
    summary = {
        "stage": "T3_AUTO_REPAIR_PROPOSAL_ONLY",
        "status": "UNVERIFIED_LEXICAL_SUGGESTIONS",
        "candidate_proposals": len(proposals),
        "unique_rule_field_source_target_cases": len(unique_evidence),
        "distinct_item_keys": len({p["item_key"] for p in proposals}),
        "rules": dict(sorted(by_rule.items())),
        "fields": dict(sorted(by_field.items())),
        "auto_applied_changes": 0, "source_rows_modified": 0,
        "human_reviewers": 0, "cohen_kappa": None, "verified_corrections": 0,
        "no_gold_label_claim": True, "caveat": "Term replacements are concept-level suggestions; not grammatical rewrites. Preserve original student misconceptions and original translations.",
    }
    return proposals, summary


def _write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--flags", type=Path, default=Path("reports/tr_auto_qa_v03/translation_flags.csv"))
    parser.add_argument("--out", type=Path, default=Path("reports/tr_auto_repair_v01"))
    args = parser.parse_args()

    if not args.flags.is_file():
        raise FileNotFoundError(args.flags)
    out = args.out.resolve()
    if out == args.flags.parent.resolve():
        raise ValueError("Output directory cannot be the input QA directory")
    targets = (out / "repair_suggestions.csv", out / "repair_manifest.json")
    if any(p.exists() for p in targets):
        raise FileExistsError("Refusing to overwrite pre-existing suggestions or manifest")
    with args.flags.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames or not MANDATORY.issubset(reader.fieldnames):
            raise ValueError("Invalid QA evidence schema")
        flags = list(reader)
    proposals, summary = analyze(flags)
    summary["input_flags_file"] = args.flags.name
    summary["input_flags_sha256"] = _sha(args.flags.read_bytes())
    summary["algorithm_version"] = "1.0.0"
    out.mkdir(parents=True, exist_ok=True)
    _write_csv(targets[0], proposals)
    summary["proposals_sha256"] = _sha(targets[0].read_bytes())
    targets[1].write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Correction suggestions (NOT applied): {len(proposals)}")
    print(f"Unique field/rule/source-target cases: {summary['unique_rule_field_source_target_cases']}")
    print(f"Distinct review items: {summary['distinct_item_keys']}")
    print(f"Actual source or translation changes: {summary['auto_applied_changes']}")
    print("Outputs:", *targets)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
