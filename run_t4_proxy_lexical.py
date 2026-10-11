"""T4 offline exploratory EN vs TR v0.2/v0.2.1 B0-B3 lexical comparison.

Reuses v0.1 TF-IDF+LR model specification; projected Turkish labels are NOT gold.
English question identities freeze all train-only GroupShuffleSplit and test-UQ
cluster-bootstrap groups. Turkish v0.2.1 reuses v0.2 C selections, so changes
in hyperparameter selection cannot be misreported as effects of translation edits.
No hosted models, no raw student text/row-level predictions in output.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import GroupShuffleSplit

from audit_dataset import SPLITS, LABEL_MAP, canonical_label, normalize, read_split, audit as source_audit
from audit_translation_corpus import sha256
from tr_adaptation.pipeline import OUT_STEM
from train_lexical import (
    LABELS, CONDITIONS, create_model, prepare, input_text, score, grouped_bootstrap_delta
)

VARIANTS = ("en", "tr_v0_2", "tr_v0_2_1")
CANDIDATE_C = (0.1, 1.0, 10.0)
SEED = 20261009
BOOTSTRAPS = 1000
REQUIRED_TR = {
    "id", "label", "label_status", "translation_scope",
    "source_question_en", "source_reference_answer_en",
    "source_student_answer_en", "question", "reference_answer",
    "student_answer",
}


def require(flag: bool, message: str) -> None:
    if not flag:
        raise RuntimeError(message)


def _read_meta(data_dirs: dict[str, Path], comparison: Path, original_dir: Path) -> dict:
    comparison_file = comparison / "comparison_manifest.json"
    require(comparison_file.is_file(), "T3 real comparative QA manifest required")
    qa = json.loads(comparison_file.read_text(encoding="utf-8"))
    base_manifest_file = data_dirs["tr_v0_2"] / "translation_manifest.json"
    new_manifest_file = data_dirs["tr_v0_2_1"] / "translation_manifest.json"
    old = json.loads(base_manifest_file.read_text(encoding="utf-8"))
    new = json.loads(new_manifest_file.read_text(encoding="utf-8"))
    require(
        qa.get("stage") == "T3_AUTO_TR_V021_COMPARATIVE_QA"
        and qa.get("status") == "EXPLORATORY_RULE_COMPARISON_NOT_HUMAN_VERIFIED"
        and qa.get("human_validation") is False
        and qa.get("projected_labels_are_gold") is False
        and qa.get("original_rows") == qa.get("candidate_rows") == 10804
        and qa.get("original_total_rule_flags") == 7412
        and qa.get("candidate_total_rule_flags") == 4926
        and qa.get("all_original_english_id_label_preserved") is True
        and qa.get("all_changes_from_evidence_pinned_patches") is True,
        "Real 10,804-row v0.2/v0.2.1 comparison not accepted"
    )
    require(
        sha256(base_manifest_file) == qa["original_manifest_sha256"]
        and sha256(new_manifest_file) == qa["candidate_manifest_sha256"],
        "TR dataset manifests differ from previously accepted QA"
    )
    require(old.get("total_translated_rows") == 10804
            and old.get("scope") == "FULL_CANDIDATE"
            and old.get("validation_state") == "UNVERIFIED_MACHINE_TRANSLATION"
            and old.get("projected_labels_are_gold") is False,
            "Original TR translation provenance invalid")
    require(new.get("total_translated_rows") == 10804
            and new.get("scope") == "FULL_CANDIDATE"
            and new.get("validation_state") == "UNVERIFIED_EXPLORATORY_AI_ASSISTED_PATCH"
            and new.get("projected_labels_are_gold") is False
            and new.get("human_validated") is False,
            "Patched TR variant falsely suggests gold or human validation")
    require(new.get("parent_translation_manifest_sha256") == sha256(base_manifest_file),
            "TR v0.2.1 did not preserve original parent manifest")
    for split in SPLITS:
        for name, manifest in (("tr_v0_2", old), ("tr_v0_2_1", new)):
            path = data_dirs[name] / f"{OUT_STEM[split]}.csv"
            require(path.is_file() and sha256(path) ==
                    manifest["splits"][split]["output_sha256"],
                    f"TR {name} split changed: {split}")
        require(old["splits"][split]["source_rows"] ==
                new["splits"][split]["rows"] ==
                qa["by_split_original"][split]["rows"],
                f"Unexpected TR split size: {split}")
    for split in SPLITS:
        _, source_path = read_split(original_dir, split)
        require(sha256(source_path) == old["source_file_sha256"][split],
                f"Original pinned English split changed: {split}")
    return {"input_comparison_sha256": sha256(comparison_file),
            "source_tr_v0_2_manifest_sha256": sha256(base_manifest_file),
            "source_tr_v0_2_1_manifest_sha256": sha256(new_manifest_file),
            "original_qa_rule_flags": qa["original_total_rule_flags"],
            "patched_qa_rule_flags": qa["candidate_total_rule_flags"]}


def validate_tr_frame(original: pd.DataFrame, tr: pd.DataFrame, split: str) -> pd.DataFrame:
    """Align by *row position and id*, never translate-derived question groups."""
    require(len(original) == len(tr), f"Rows differ: {split}")
    require(REQUIRED_TR.issubset(tr.columns), f"TR columns missing: {split}")
    for field in ("question", "reference_answer", "student_answer"):
        a = original[field].fillna("").astype(str).tolist()
        b = tr[f"source_{field}_en"].fillna("").astype(str).tolist()
        require(a == b, f"English source differs: {split}/{field}")
    ids = original["id"].astype(str).tolist()
    require(ids == tr["id"].astype(str).tolist(), f"Original IDs changed: {split}")
    originals = original["label"].map(canonical_label).tolist()
    transferred = tr["label"].map(canonical_label).tolist()
    require(originals == transferred, f"Projected labels changed: {split}")
    require(set(tr["label_status"].tolist()) == {"UNVERIFIED_TRANSFER"}
            and set(tr["translation_scope"].tolist()) == {"FULL_CANDIDATE"},
            f"False gold label or unsupported translation scope: {split}")
    require(all(tr[x].fillna("").astype(str).str.strip().ne("").all()
                for x in ("question", "student_answer")),
            f"Blank TR question/student feature: {split}")
    result = tr.copy()
    # English-only cluster keys stay identical across language and translation revisions.
    result["target"] = [LABEL_MAP[x] for x in originals]
    result["group"] = original["question"].map(normalize).tolist()
    result["answer_text"] = tr["student_answer"].fillna("").astype(str)
    result["question_text"] = tr["question"].fillna("").astype(str)
    require(all(result["group"].ne("")), f"Blank original English question: {split}")
    return result


def _load_split(original_dir: Path, data_dirs: dict[str, Path], split: str) -> dict:
    english, _ = read_split(original_dir, split)
    result = {"en": prepare(english)}
    for variant in ("tr_v0_2", "tr_v0_2_1"):
        tr = pd.read_csv(data_dirs[variant] / f"{OUT_STEM[split]}.csv",
                         dtype={"id": str, "label": str}, keep_default_na=False)
        result[variant] = validate_tr_frame(english, tr, split)
        require(result[variant]["target"].tolist() == result["en"]["target"].tolist(),
                f"Four-class projected targets differ: {variant}/{split}")
    return result


def fixed_group_partition(en_train: pd.DataFrame, seed: int = SEED):
    require(en_train["group"].nunique() >= 4, "Too few question clusters")
    splitter = GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=seed)
    tr_idx, val_idx = next(splitter.split(en_train, groups=en_train["group"]))
    require(not (set(en_train.iloc[tr_idx]["group"]) &
                 set(en_train.iloc[val_idx]["group"])), "Train/validation group leakage")
    require(set(en_train.iloc[tr_idx]["target"]) == set(LABELS)
            and set(en_train.iloc[val_idx]["target"]) == set(LABELS),
            "Train-only grouped validation does not contain all four classes")
    return tr_idx, val_idx


def _macro_by_clusters(y: np.ndarray, predictions: dict[str, np.ndarray],
                       english_groups: np.ndarray, reps: int, seed: int) -> dict:
    """Paired, fixed English question cluster bootstrap for context DID."""
    groups = np.unique(english_groups)
    require(len(groups) > 1, "No independent test question clusters")
    indices = [np.flatnonzero(english_groups == g) for g in groups]
    integer = {name: i for i, name in enumerate(LABELS)}
    true = np.asarray([integer[z] for z in y], dtype=np.int64)
    mapped = {k: np.asarray([integer[z] for z in a], dtype=np.int64)
              for k, a in predictions.items()}
    def mf(indices_for_resample: np.ndarray, p: np.ndarray) -> float:
        mat = np.bincount(true[indices_for_resample] * 4 + p[indices_for_resample],
                          minlength=16).reshape(4, 4)
        tp = np.diag(mat)
        denominator = mat.sum(0) + mat.sum(1)
        return float(np.divide(2 * tp, denominator,
                               out=np.zeros(4, dtype=float),
                               where=denominator != 0).mean())
    def did(ids) -> float:
        return (mf(ids, mapped["tr_v0_2_1:B2"]) -
                mf(ids, mapped["tr_v0_2_1:B1"]) -
                mf(ids, mapped["tr_v0_2:B2"]) +
                mf(ids, mapped["tr_v0_2:B1"]))
    rng = np.random.default_rng(seed)
    all_indices = np.arange(len(true))
    bootstrap = []
    for _ in range(reps):
        samples = rng.integers(len(groups), size=len(groups))
        bootstrap.append(did(np.concatenate([indices[s] for s in samples])))
    return {
        "estimand": "Difference in (B2 - B1) macro-F1, TR v0.2.1 minus TR v0.2",
        "point": did(all_indices), "cluster_count": len(groups),
        "bootstrap_iterations": reps, "seed": seed,
        "percentile_95_ci": [float(np.quantile(bootstrap, 0.025)),
                             float(np.quantile(bootstrap, 0.975))],
        "caveat": "Paired question-cluster resampling, English group IDs; "
                  "no causal effect and no independent Turkish gold.",
    }


def run(original_dir: Path, old_tr: Path, new_tr: Path, comparison: Path, out: Path,
        seed: int = SEED, bootstraps: int = BOOTSTRAPS,
        allow_p0_warnings: bool = False, previous_en: Path | None = None) -> dict:
    original_dir, old_tr, new_tr, comparison, out = (
        x.resolve() for x in (original_dir, old_tr, new_tr, comparison, out)
    )
    require(seed == SEED and bootstraps == BOOTSTRAPS,
            "This protocol freezes seed=20261009, bootstrap iterations=1000")
    require(not any(out == p or out.is_relative_to(p) or p.is_relative_to(out)
                    for p in (original_dir, old_tr, new_tr, comparison)),
            "Output directory overlaps immutable data or comparison")
    stage = out.with_name(out.name + ".part")
    require(not out.exists() and not stage.exists(),
            "T4 output or partial output already exists")
    inputs = {"tr_v0_2": old_tr, "tr_v0_2_1": new_tr}
    provenance = _read_meta(inputs, comparison, original_dir)
    original_frames, paths = {}, {}
    for split in SPLITS:
        original_frames[split], paths[split] = read_split(original_dir, split)
    p0 = source_audit(original_frames, paths)
    require(not p0["fatal_errors"], "Fatal English P0 audit errors")
    require(allow_p0_warnings or not p0["warnings"],
            "Original P0 audit warnings must be explicitly accepted with --allow-p0-warnings")

    train = _load_split(original_dir, inputs, "train")
    train_en = train["en"]
    base_y = train_en["target"].tolist()
    indices, validation_indices = fixed_group_partition(train_en, seed)
    for v in VARIANTS:
        require(train[v]["group"].tolist() == train_en["group"].tolist(),
                f"Train original English question groups do not match: {v}")
        require(train[v]["target"].tolist() == base_y,
                f"Train projected targets not aligned: {v}")

    selected, fitted = {}, {}
    for variant in VARIANTS:
        selected[variant] = {}
        fitted[variant] = {}
        sub = train[variant].iloc[indices]
        val = train[variant].iloc[validation_indices]
        for cond in CONDITIONS:
            if variant == "tr_v0_2_1":
                candidate_cs = [selected["tr_v0_2"][cond]["selected_C"]]
                policy = "FROZEN_FROM_TR_V0_2_TRAIN_VALIDATION"
            else:
                candidate_cs = [1.0] if cond == "B0" else list(CANDIDATE_C)
                policy = "SELECTED_ON_THIS_VARIANT_TRAIN_GROUP_VALIDATION"
            tried = []
            for C in candidate_cs:
                m = create_model(cond, C)
                m.fit(input_text(sub, cond), sub["target"])
                pred = m.predict(input_text(val, cond))
                tried.append({"C": float(C),
                              "validation_macro_f1": score(val["target"], pred)["macro_f1"]})
            chosen = sorted(tried,
                            key=lambda x: (-x["validation_macro_f1"], x["C"]))[0]
            model = create_model(cond, chosen["C"])
            model.fit(input_text(train[variant], cond), train[variant]["target"])
            fitted[variant][cond] = model
            selected[variant][cond] = {
                "selected_C": chosen["C"], "validation_results": tried,
                "selection_policy": policy,
            }
        print(f"TRAIN {variant}: selected B1/B2/B3 C = " +
              ", ".join(f"{c}:{selected[variant][c]['selected_C']}"
                        for c in ("B1", "B2", "B3")), flush=True)
    selection = {
        "seed": seed,
        "group_basis": "Original English normalized question for all variants",
        "train_question_groups": int(train_en["group"].nunique()),
        "train_fit_groups": int(train_en.iloc[indices]["group"].nunique()),
        "validation_question_groups": int(
            train_en.iloc[validation_indices]["group"].nunique()),
        "train_rows": len(train_en),
        "train_fit_rows": len(indices), "train_validation_rows": len(validation_indices),
        "target_classes": LABELS,
        "hyperparameter_selection_locked_before_any_test_metrics_computed": True,
        "condition_selected_C": selected,
        "translation_repair_C_frozen_from_original_TR": True,
    }
    stage.mkdir(parents=True)
    try:
        (stage / "selection_before_test.json").write_text(
            json.dumps(selection, ensure_ascii=False, indent=2), encoding="utf-8")

        metrics = {}
        primary_predictions = {}
        primary_groups = None
        primary_y = None
        for split in ("test_ua", "test_uq", "test_ud"):
            test = _load_split(original_dir, inputs, split)
            en_test = test["en"]
            for variant in VARIANTS:
                require(test[variant]["group"].tolist() == en_test["group"].tolist(),
                        f"Original EN question grouping differs: {split}/{variant}")
            if split in ("test_uq", "test_ud"):
                require(not set(train_en["group"]).intersection(en_test["group"]),
                        f"Original EN question leakage into {split}")
            if split == "test_uq":
                require(len(test["en"]) == 733 and en_test["group"].nunique() == 15,
                        "Official Test-UQ shape/group count changed")
                require(test["tr_v0_2"]["answer_text"].tolist() ==
                        test["tr_v0_2_1"]["answer_text"].tolist(),
                        "Test-UQ student explanations should be identical across TR revisions")
                primary_y = en_test["target"].to_numpy()
                primary_groups = en_test["group"].to_numpy()
            metrics[split] = {}
            split_pred = {}
            for variant in VARIANTS:
                metrics[split][variant] = {}
                for cond in CONDITIONS:
                    prediction = np.asarray(fitted[variant][cond].predict(
                        input_text(test[variant], cond)), dtype=str)
                    split_pred[(variant, cond)] = prediction
                    stats = score(test[variant]["target"], prediction)
                    stats.update({
                        "n_rows": len(test[variant]),
                        "n_english_question_groups": int(test[variant]["group"].nunique()),
                        "confusion_matrix": confusion_matrix(
                            test[variant]["target"], prediction, labels=LABELS).tolist(),
                        "per_class": classification_report(
                            test[variant]["target"], prediction, labels=LABELS,
                            output_dict=True, zero_division=0),
                    })
                    metrics[split][variant][cond] = stats
                if split == "test_uq":
                    primary_predictions.update({
                        f"{variant}:{cond}": split_pred[(variant, cond)]
                        for cond in CONDITIONS
                    })
            if split == "test_uq":
                for variant in VARIANTS:
                    ci = grouped_bootstrap_delta(
                        en_test, split_pred[(variant, "B1")],
                        split_pred[(variant, "B2")], samples=bootstraps, seed=seed)
                    metrics[split][variant]["B2_minus_B1"] = ci
                metrics[split]["repair_effect_on_context_gain"] = _macro_by_clusters(
                    primary_y, primary_predictions, primary_groups, bootstraps, seed)
                paired = {}
                for cond in CONDITIONS:
                    paired[cond] = grouped_bootstrap_delta(
                        en_test, split_pred[("tr_v0_2", cond)],
                        split_pred[("tr_v0_2_1", cond)],
                        samples=bootstraps, seed=seed)
                    paired[cond]["estimand"] = f"TR v0.2.1 minus TR v0.2 for {cond}"
                metrics[split]["paired_TR_revision_deltas"] = paired
            print(f"EVAL {split}: rows={len(en_test)} EN/TRv0.2/TRv0.2.1 done",
                  flush=True)

        # Original English B0-B3 baseline is a reproducibility check, never re-tuned on Test-UQ.
        en_reproduction = {"prior_local_baseline_available": False}
        if previous_en is not None and previous_en.is_file():
            baseline = json.loads(previous_en.read_text(encoding="utf-8"))
            prior_seed = baseline.get("seed")
            en_reproduction = {
                "prior_local_baseline_available": True,
                "prior_seed": prior_seed,
                "same_seed": prior_seed == seed,
                "test_uq_macro_f1_absolute_differences": {
                    cond: abs(metrics["test_uq"]["en"][cond]["macro_f1"] -
                              baseline["metrics"]["test_uq"][cond]["macro_f1"])
                    for cond in CONDITIONS
                },
            }
            en_reproduction["all_within_1e-8"] = (
                en_reproduction["same_seed"] and
                all(z <= 1e-8 for z in
                    en_reproduction["test_uq_macro_f1_absolute_differences"].values())
            )
        summary = {
            "stage": "T4_EN_TR_02_TR_021_LEXICAL_PROXY",
            "research_status": "EXPLORATORY_PROJECTED_LABEL_NOT_TURKISH_GOLD",
            "original_english_labels_used_as_proxy_in_all_languages": True,
            "english_test_question_grouping": True,
            "source_provenance": provenance,
            "english_p0_status": p0["status"],
            "english_p0_warnings_acknowledged": bool(allow_p0_warnings),
            "models": "B0 majority, B1 student TF-IDF+LR, B2 student+question TF-IDF+LR, B3 question TF-IDF+LR",
            "training_selection": selection,
            "primary_split": "test_uq", "primary_metric": "macro_f1",
            "cluster_bootstrap_iterations": bootstraps,
            "metrics": metrics, "english_baseline_reproduction": en_reproduction,
            "limitations": [
                "No human-reviewed Turkish gold data; inherited English projected labels only.",
                "No causal impact or scientific semantic quality proof from translated-text corrections.",
                "TR v0.2.1 validation Cs frozen from v0.2 to isolate corpus edit, not re-selected.",
                "15 Test-UQ English question groups; descriptive paired cluster bootstrap only.",
                "Only lexical TF-IDF baselines, not general language/context effectiveness.",
                "Original datasets, patch files and P1 models are not modified.",
            ],
        }
        (stage / "t4_proxy_results.json").write_text(
            json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        lines = [
            "# T4 Test-UQ — English versus Turkish lexical projected-label proxy", "",
            "| Variant | B0 | B1 | B2 | B3 | B2−B1 |",
            "|---|---:|---:|---:|---:|---:|",
        ]
        for variant in VARIANTS:
            m = metrics["test_uq"][variant]
            lines.append("| " + variant + " | " +
                         " | ".join(f"{m[c]['macro_f1']:.4f}" for c in CONDITIONS) +
                         f" | {m['B2_minus_B1']['delta_B2_minus_B1']:+.4f} |")
        did = metrics["test_uq"]["repair_effect_on_context_gain"]
        lines += [
            "", "## Exploratory TR revision difference-in-context-ablation",
            f"Point: {did['point']:+.6f}, English-question cluster bootstrap "
            f"95% CI: [{did['percentile_95_ci'][0]:+.6f}, "
            f"{did['percentile_95_ci'][1]:+.6f}].", "",
            "## Protocol limits", "",
            "ALL Turkish labels are projected from original English SciEntsBank, not Turkish gold.",
            "C was selected with a fixed train-only English-question group split;",
            "TR v0.2.1 reuse C selected for original TR v0.2.",
            "Test-UQ was evaluated after model-selection decisions were frozen.",
            "No source/reference/student text, IDs or per-row predictions are exported.",
            "Differences do not prove genuine educational benefit or correct translations.", "",
        ]
        (stage / "t4_proxy_summary.md").write_text("\n".join(lines), encoding="utf-8")
        stage.rename(out)
        print("T4 EXPLORATORY PROXY COMPLETE; Test-UQ Macro-F1:")
        for variant in VARIANTS:
            print(variant, {cond: round(metrics["test_uq"][variant][cond]["macro_f1"], 6)
                            for cond in CONDITIONS})
        print("TR repair context-gain diff:", round(did["point"], 6),
              "CI:", did["percentile_95_ci"])
        print("Output:", out)
        return summary
    except BaseException:
        print("T4 incomplete; evidence preserved at:", stage)
        raise


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--original-dir", type=Path, default=Path("data/raw"))
    p.add_argument("--tr-02", type=Path, default=Path("data/tr_v0_2"))
    p.add_argument("--tr-021", type=Path, default=Path("data/tr_v0_2_1"))
    p.add_argument("--comparison", type=Path, default=Path("reports/tr_compare_v021"))
    p.add_argument("--out", type=Path, default=Path("results/t4_proxy_v021"))
    p.add_argument("--seed", type=int, default=SEED)
    p.add_argument("--bootstraps", type=int, default=BOOTSTRAPS)
    p.add_argument("--allow-p0-warnings", action="store_true")
    p.add_argument("--prior-english", type=Path,
                   default=Path("results/lexical/baseline_results.json"))
    a = p.parse_args()
    run(a.original_dir, a.tr_02, a.tr_021, a.comparison, a.out, a.seed,
        a.bootstraps, a.allow_p0_warnings, a.prior_english)


if __name__ == "__main__":
    main()
