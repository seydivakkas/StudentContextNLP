"""SciEntsBank P0 data audit. No API keys, remote inference or model use.

Usage: python audit_dataset.py --data-dir data/raw --output-dir reports
Accepts CSV or Parquet: train, test-ua, test-uq and test-ud.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import pandas as pd

SPLITS = ("train", "test_ua", "test_uq", "test_ud")
REQUIRED = ("id", "question", "reference_answer", "student_answer", "label")
LABEL_NAMES = {0: "correct", 1: "contradictory", 2: "partially_correct_incomplete", 3: "irrelevant", 4: "non_domain"}
LABEL_MAP = {
    "correct": "Correct",
    "partially_correct_incomplete": "Incomplete",
    "contradictory": "Contradictory",
    "irrelevant": "Other",
    "non_domain": "Other",
}
EXPECTED = {
    "train": {"correct": 2008, "contradictory": 499, "partially_correct_incomplete": 1324, "irrelevant": 1115, "non_domain": 23},
    "test_ua": {"correct": 233, "contradictory": 58, "partially_correct_incomplete": 113, "irrelevant": 133, "non_domain": 3},
    "test_uq": {"correct": 301, "contradictory": 64, "partially_correct_incomplete": 175, "irrelevant": 193, "non_domain": 0},
    "test_ud": {"correct": 1917, "contradictory": 417, "partially_correct_incomplete": 986, "irrelevant": 1222, "non_domain": 20},
}


def canonical_label(v: Any) -> str:
    if pd.isna(v):
        raise ValueError("Boş label")
    if isinstance(v, (int, float)) and float(v).is_integer():
        return LABEL_NAMES[int(v)]
    s = str(v).strip().lower().replace(" ", "_").replace("-", "_")
    if s.isdigit():
        return LABEL_NAMES[int(s)]
    if s in LABEL_MAP:
        return s
    raise ValueError(f"Bilinmeyen etiket: {v!r}")


def normalize(v: Any) -> str:
    if pd.isna(v):
        return ""
    return re.sub(r"\s+", " ", str(v).strip().casefold())


def read_split(data_dir: Path, split: str) -> tuple[pd.DataFrame, Path]:
    stem = split.replace("_", "-")
    candidates = [
        data_dir / f"{stem}-00001.parquet", data_dir / f"{stem}-00001.csv",
        data_dir / f"{stem}.parquet", data_dir / f"{stem}.csv",
        data_dir / f"{split}.parquet", data_dir / f"{split}.csv",
    ]
    existing = [p for p in dict.fromkeys(candidates) if p.exists()]
    if len(existing) != 1:
        raise FileNotFoundError(f"{split}: beklenen tek dosya, bulunan={len(existing)}; adaylar: {', '.join(map(str,candidates))}")
    path = existing[0]
    if path.suffix == ".parquet":
        frame = pd.read_parquet(path)
    else:
        frame = pd.read_csv(path, dtype={"id": str}, keep_default_na=False)
    missing = sorted(set(REQUIRED) - set(frame.columns))
    if missing:
        raise ValueError(f"{path}: eksik sütunlar: {missing}")
    return frame.loc[:, REQUIRED].copy(), path


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def audit(frames: dict[str, pd.DataFrame], paths: dict[str, Path] | None = None) -> dict:
    paths = paths or {}
    norms = {}
    summaries = {}
    fatal_errors = []
    warnings = []
    for split in SPLITS:
        if split not in frames:
            fatal_errors.append(f"Eksik split: {split}")
            continue
        df = frames[split].copy()
        if not set(REQUIRED).issubset(df.columns):
            fatal_errors.append(f"{split}: gerekli alanlardan en az biri yok")
            continue
        try:
            df["_original_label"] = df["label"].map(canonical_label)
        except (ValueError, KeyError) as exc:
            fatal_errors.append(f"{split}: etiket hatası: {exc}")
            continue
        df["_four_class"] = df["_original_label"].map(LABEL_MAP)
        for field in ("id", "question", "reference_answer", "student_answer"):
            df[f"_norm_{field}"] = df[field].map(normalize)
        key_cols = ["_norm_question", "_norm_reference_answer", "_norm_student_answer"]
        blank = {k: int((df[f"_norm_{k}"] == "").sum()) for k in ("id", "question", "reference_answer", "student_answer")}
        original_counts = dict(sorted(Counter(df["_original_label"]).items()))
        four_counts = dict(sorted(Counter(df["_four_class"]).items()))
        conflict = df.groupby(key_cols, dropna=False)["_original_label"].nunique()
        expected_ok = {key: int(original_counts.get(key, 0)) == count for key, count in EXPECTED[split].items()}
        if not all(expected_ok.values()):
            warnings.append(f"{split}: resmi veri kartındaki 5 sınıf dağılımıyla uyuşmuyor")
        if any(blank.values()):
            warnings.append(f"{split}: boş id/soru/referans/öğrenci alanı var")
        if (conflict > 1).any():
            warnings.append(f"{split}: aynı normalize soru+referans+cevap için çelişkili orijinal etiket")
        summaries[split] = {
            "rows": int(len(df)),
            "unique_questions_normalized": int(df["_norm_question"].nunique()),
            "unique_ids": int(df["_norm_id"].nunique()),
            "duplicate_ids": int(df["_norm_id"].duplicated().sum()),
            "exact_duplicate_triples_extra_rows": int(df.duplicated(subset=key_cols).sum()),
            "conflicting_answer_triples": int((conflict > 1).sum()),
            "empty_fields": blank,
            "original_five_class": original_counts,
            "derived_four_class": four_counts,
            "matches_published_distribution": all(expected_ok.values()),
        }
        if split in paths:
            summaries[split]["file_sha256"] = sha256(paths[split])
            summaries[split]["file_name"] = paths[split].name
        norms[split] = df
    cross = {}
    for split in ("test_ua", "test_uq", "test_ud"):
        if split not in norms or "train" not in norms:
            continue
        tr, te = norms["train"], norms[split]
        trq = set(tr["_norm_question"])
        teq = set(te["_norm_question"])
        triples = ["_norm_question", "_norm_reference_answer", "_norm_student_answer"]
        trtr = set(map(tuple, tr[triples].itertuples(index=False, name=None)))
        tetr = set(map(tuple, te[triples].itertuples(index=False, name=None)))
        cross[split] = {"question_overlap_with_train": len(trq & teq), "exact_triple_overlap_with_train": len(trtr & tetr),
                        "question_set_train": len(trq), "question_set_test": len(teq)}
    if cross.get("test_uq", {}).get("question_overlap_with_train", 0) > 0:
        fatal_errors.append("test_uq: train ile sorular çakışıyor; yeni soru testi geçersiz olabilir")
    allq = set().union(*(set(x["_norm_question"]) for x in norms.values())) if norms else set()
    return {"dataset": "nkazi/SciEntsBank", "audit_version": "P0.1", "status": "FAIL" if fatal_errors else "PASS_WITH_WARNINGS" if warnings else "PASS",
            "summary": summaries, "cross_split": cross, "unique_questions_all_splits": len(allq),
            "fatal_errors": fatal_errors, "warnings": warnings,
            "caveat": "Bu denetim veri tutarlılığını ölçer; etiketlerin uzman doğruluğunu ya da model performansını doğrulamaz."}


def markdown(result: dict) -> str:
    lines = ["# SciEntsBank P0 — Ham Veri Denetimi", "", f"Durum: **{result['status']}**", "",
             "## Split bazında sayılar", "", "| Bölüm | Satır | Benzersiz soru | Tekrarlanan üçlü | Etiket çatışması | Veri kartıyla uyum |", "|---|---:|---:|---:|---:|---|"]
    for s, v in result["summary"].items():
        lines.append(f"| {s} | {v['rows']} | {v['unique_questions_normalized']} | {v['exact_duplicate_triples_extra_rows']} | {v['conflicting_answer_triples']} | {'Evet' if v['matches_published_distribution'] else 'Hayır'} |")
    lines += ["", "## Dört sınıflı dönüşüm", "", "| Bölüm | Correct | Incomplete | Contradictory | Other |", "|---|---:|---:|---:|---:|"]
    for s, v in result["summary"].items():
        cc = v["derived_four_class"]
        lines.append(f"| {s} | {cc.get('Correct',0)} | {cc.get('Incomplete',0)} | {cc.get('Contradictory',0)} | {cc.get('Other',0)} |")
    lines += ["", "## Train–test çakışması", "", "| Test | Ortak soru | Ortak normalize soru+referans+yanıt |", "|---|---:|---:|"]
    for s, v in result["cross_split"].items():
        lines.append(f"| {s} | {v['question_overlap_with_train']} | {v['exact_triple_overlap_with_train']} |")
    lines += ["", f"Tüm bölümlerde benzersiz soru: **{result['unique_questions_all_splits']}**", "",
              "## Hatalar", ""] + [f"- {x}" for x in result["fatal_errors"] or ["Yok"]]
    lines += ["", "## Uyarılar", ""] + [f"- {x}" for x in result["warnings"] or ["Yok"]]
    lines += ["", "## Yorum sınırı", "", result["caveat"], ""]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, default=Path("data/raw"))
    parser.add_argument("--output-dir", type=Path, default=Path("reports"))
    args = parser.parse_args()
    frames, paths = {}, {}
    try:
        for split in SPLITS:
            frames[split], paths[split] = read_split(args.data_dir, split)
    except Exception as exc:
        print(f"BLOCKED: veri dosyası okunamadı: {exc}")
        return 2
    result = audit(frames, paths)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "P0_audit.json").write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    (args.output_dir / "P0_audit.md").write_text(markdown(result), encoding="utf-8")
    print(f"{result['status']} — {args.output_dir / 'P0_audit.md'}")
    return 1 if result["fatal_errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
