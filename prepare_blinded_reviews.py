"""Create label-blinded stage-1 review forms from an existing T3 sample.

Human ratings are never inferred, copied from labels, or filled automatically.
The original review_A.csv and review_B.csv are preserved for stage-2 label review.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd

SOURCE_COLUMNS = (
    "item_key",
    "source_question_en", "question",
    "source_reference_answer_en", "reference_answer",
    "source_student_answer_en", "student_answer",
)
RATING_COLUMNS = ("meaning_preserved", "error_preserved", "notes")
REVIEWERS = ("A", "B")


def prepare_blind_forms(review_dir: Path, out_dir: Path | None = None, expected_n: int = 240) -> dict:
    """Fail closed on mismatched forms, duplicate keys, or any existing output."""
    if expected_n < 1:
        raise ValueError("expected_n must be positive")
    review_dir = review_dir.resolve()
    out_dir = (out_dir or review_dir / "blind_stage1").resolve()
    if out_dir == review_dir:
        raise ValueError("Blind forms must use a separate output directory")

    frames = {}
    for reviewer in REVIEWERS:
        path = review_dir / f"review_{reviewer}.csv"
        df = pd.read_csv(path, dtype=str, keep_default_na=False)
        missing = set(SOURCE_COLUMNS) - set(df.columns)
        if missing:
            raise ValueError(f"{path}: missing required fields {sorted(missing)}")
        if len(df) != expected_n or not df["item_key"].is_unique:
            raise ValueError(f"{path}: expected {expected_n} distinct review items")
        if df["item_key"].eq("").any():
            raise ValueError(f"{path}: blank item keys")
        frames[reviewer] = df

    a = frames["A"].loc[:, SOURCE_COLUMNS].reset_index(drop=True)
    b = frames["B"].loc[:, SOURCE_COLUMNS].reset_index(drop=True)
    if not a.equals(b):
        raise ValueError("A/B forms differ in selected items or ordering")

    manifest_path = review_dir / "review_manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Sample manifest not found: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("actual_n") != expected_n or manifest.get("validation_state") != "AWAITING_INDEPENDENT_HUMAN_REVIEW":
        raise ValueError("Unexpected sample manifest size or state")

    targets = [out_dir / f"review_{reviewer}_blind.csv" for reviewer in REVIEWERS]
    targets.append(out_dir / "blind_manifest.json")
    if any(path.exists() for path in targets):
        raise FileExistsError("Existing blind review files will not be overwritten")

    out_dir.mkdir(parents=True, exist_ok=True)
    outputs = {}
    for reviewer in REVIEWERS:
        # Explicit allow-list: source label, class4, quality_flags, split and id never appear.
        blind = a.copy()
        for rating in RATING_COLUMNS:
            blind[rating] = ""
        path = out_dir / f"review_{reviewer}_blind.csv"
        blind.to_csv(path, index=False, encoding="utf-8-sig")
        outputs[reviewer] = {
            "filename": path.name,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }

    result = {
        "stage": "BLIND_STAGE1",
        "validation_state": "AWAITING_INDEPENDENT_HUMAN_REVIEW",
        "sample_seed": manifest.get("seed"),
        "sample_model_key": manifest.get("source_manifest_model_key"),
        "n_items": expected_n,
        "allowed_columns": list(SOURCE_COLUMNS + RATING_COLUMNS),
        "instructions": {
            "meaning_preserved": "yes/no/uncertain — compare original and translation",
            "error_preserved": "yes/no/uncertain — same scientific error if present; correct stays correct",
            "notes": "explain ambiguities and translation issues without student identifiers",
            "privacy": "forms and original student explanations are local only; do not upload to GitHub",
            "stage2": "reveal original projected class only after both stage-1 forms are finalized",
        },
        "outputs": outputs,
    }
    (out_dir / "blind_manifest.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return result


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--review-dir", type=Path, default=Path("reports/tr_review"))
    p.add_argument("--out", type=Path, default=None)
    p.add_argument("--expected-n", type=int, default=240)
    args = p.parse_args()
    result = prepare_blind_forms(args.review_dir, args.out, args.expected_n)
    print("Independent label-blinded stage-1 forms:", result["n_items"])
    print("Manifest:", (args.out or args.review_dir / "blind_stage1") / "blind_manifest.json")
    print("Original review_A.csv and review_B.csv remain untouched.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
