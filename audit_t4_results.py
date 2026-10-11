"""Verify real T4 lexical proxy metrics arithmetically and export aggregate-only tables.

No refitting, no test tuning, no row-level student data, no uploads, no gold claims.
The English P1 baseline must reproduce to 1e-8 before accepted results export.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from collections import defaultdict

from audit_translation_corpus import sha256
from train_lexical import LABELS, CONDITIONS

SPLIT_ROWS = {"test_ua": 540, "test_uq": 733, "test_ud": 4562}
VARIANTS = ("en", "tr_v0_2", "tr_v0_2_1")
EXPECTED_SEED = 20261009
CI_REPS = 1000
TOL = 1e-8

MODEL_FIELDS = ("split", "variant", "model", "macro_f1", "weighted_f1",
                "accuracy", "n_rows", "n_english_question_groups")
CLASS_FIELDS = ("variant", "model", "class_label", "support",
                "precision", "recall", "f1_score")
DELTA_FIELDS = ("model", "tr_v021_minus_tr_v02_macro_f1",
                "paired_ci_low", "paired_ci_high", "cluster_count",
                "bootstrap_iterations")


def demand(ok: bool, why: str):
    if not ok:
        raise RuntimeError(why)


def close(actual: float, desired: float, context: str, tol: float = TOL):
    demand(math.isfinite(float(actual)) and
           abs(float(actual) - float(desired)) <= tol,
           f"Metric inconsistency: {context}, observed={actual}, expected={desired}")


def metrics_from_matrix(cm, context: str):
    demand(isinstance(cm, list) and len(cm) == 4 and all(
        isinstance(row, list) and len(row) == 4 for row in cm),
        "Expected fixed 4x4 confusion matrix: " + context)
    demand(all(isinstance(x, int) and not isinstance(x, bool) and x >= 0
               for row in cm for x in row),
           "Invalid confusion matrix counts: " + context)
    support = [sum(cm[i]) for i in range(4)]
    predicted = [sum(cm[i][j] for i in range(4)) for j in range(4)]
    total = sum(support)
    demand(total > 0, "Empty test confusion matrix: " + context)
    per_class = {}
    f_scores = []
    for i, label in enumerate(LABELS):
        true_pos = cm[i][i]
        precision = true_pos / predicted[i] if predicted[i] else 0.0
        recall = true_pos / support[i] if support[i] else 0.0
        denom = support[i] + predicted[i]
        f1 = 2 * true_pos / denom if denom else 0.0
        per_class[label] = {
            "support": support[i], "precision": precision,
            "recall": recall, "f1_score": f1,
        }
        f_scores.append(f1)
    return {
        "per_class": per_class,
        "macro_f1": sum(f_scores) / 4,
        "weighted_f1": sum(support[i] * f_scores[i]
                           for i in range(4)) / total,
        "accuracy": sum(cm[i][i] for i in range(4)) / total,
        "total": total, "support": tuple(support),
    }


def csv_out(path: Path, rows: list[dict], fields: tuple[str, ...]):
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def audit(t4_file: Path, p1_file: Path, out: Path) -> dict:
    t4_file, p1_file, out = (x.resolve() for x in (t4_file, p1_file, out))
    demand(t4_file.is_file() and p1_file.is_file(),
           "Existing real T4 and English P1 JSON reports required")
    demand(not out.is_relative_to(t4_file.parent) and
           not out.is_relative_to(p1_file.parent) and
           out != t4_file.parent and out != p1_file.parent,
           "Output cannot overlap input reports or earlier results")
    stage = out.with_name(out.name + ".part")
    demand(not out.exists() and not stage.exists(),
           "Audit output or unfinished staging exists; no overwrite")
    report = json.loads(t4_file.read_text(encoding="utf-8"))
    prior = json.loads(p1_file.read_text(encoding="utf-8"))
    demand(report.get("stage") == "T4_EN_TR_02_TR_021_LEXICAL_PROXY" and
           report.get("research_status") ==
           "EXPLORATORY_PROJECTED_LABEL_NOT_TURKISH_GOLD" and
           report.get("primary_split") == "test_uq" and
           report.get("cluster_bootstrap_iterations") == CI_REPS and
           report.get("original_english_labels_used_as_proxy_in_all_languages") is True
           and report.get("english_test_question_grouping") is True,
           "Wrong T4 experiment provenance or falsely claimed gold labels")
    selection = report["training_selection"]
    demand(selection.get("seed") == EXPECTED_SEED
           and selection.get("group_basis") ==
           "Original English normalized question for all variants"
           and selection.get("translation_repair_C_frozen_from_original_TR") is True
           and selection.get("hyperparameter_selection_locked_before_any_test_metrics_computed") is True,
           "T4 model selection protocol differs from preregistration")
    demand(report.get("english_baseline_reproduction", {}).get(
        "prior_local_baseline_available") is True,
        "T4 English reproduction did not have an earlier local P1 report")
    demand(prior.get("seed") == EXPECTED_SEED
           and report.get("english_baseline_reproduction", {}).get("same_seed") is True,
           "Prior P1 seed mismatch")
    chosen = selection["condition_selected_C"]
    for cond in CONDITIONS:
        demand(float(chosen["tr_v0_2_1"][cond]["selected_C"]) ==
               float(chosen["tr_v0_2"][cond]["selected_C"]),
               "TR v0.2.1 hyperparameter was reselected after translation changes: " + cond)
        if cond != "B0":
            demand(float(chosen["tr_v0_2"][cond]["selected_C"]) in (0.1, 1.0, 10.0),
                   "Unexpected C hyperparameter: " + cond)
    demand(prior.get("synthetic_data") is False and
           report["source_provenance"]["original_qa_rule_flags"] == 7412 and
           report["source_provenance"]["patched_qa_rule_flags"] == 4926,
           "Synthetic or changed v0.2.1 research sources")

    metric_rows, class_rows = [], []
    matrices = {}
    support_by_split = {}
    for split, expected in SPLIT_ROWS.items():
        support_by_split[split] = None
        for variant in VARIANTS:
            for model in CONDITIONS:
                obj = report["metrics"][split][variant][model]
                context = f"{split}/{variant}/{model}"
                demand(obj["n_rows"] == expected,
                       "Wrong number of records: " + context)
                if split == "test_uq":
                    demand(obj["n_english_question_groups"] == 15,
                           "Test-UQ should have 15 original English question clusters")
                matrix = metrics_from_matrix(obj["confusion_matrix"], context)
                demand(matrix["total"] == expected,
                       "Matrix support does not cover all expected records: " + context)
                if support_by_split[split] is None:
                    support_by_split[split] = matrix["support"]
                demand(matrix["support"] == support_by_split[split],
                       "Label support differs across languages/model conditions: " + context)
                for name in ("macro_f1", "weighted_f1", "accuracy"):
                    close(obj[name], matrix[name], context+"/"+name)
                for label in LABELS:
                    actual = obj["per_class"][label]
                    expected_class = matrix["per_class"][label]
                    for column in ("support", "precision", "recall", "f1_score"):
                        close(actual[column], expected_class[column],
                              context+"/"+label+"/"+column)
                    if split == "test_uq":
                        class_rows.append({
                            "variant": variant, "model": model,
                            "class_label": label,
                            **expected_class,
                        })
                matrices[context] = obj["confusion_matrix"]
                metric_rows.append({
                    "split": split, "variant": variant, "model": model,
                    **{key: obj[key] for key in
                       ("macro_f1", "weighted_f1", "accuracy",
                        "n_rows", "n_english_question_groups")},
                })

    demand(sum(support_by_split["test_uq"]) == 733,
           "Primary test label support mismatch")
    uq = report["metrics"]["test_uq"]
    for model in CONDITIONS:
        close(uq["en"][model]["macro_f1"],
              prior["metrics"]["test_uq"][model]["macro_f1"],
              "English P1 exact reproduction/B"+model, tol=TOL)
    repro = report["english_baseline_reproduction"]
    demand(repro.get("all_within_1e-8") is True,
           "Frozen 1e-8 English reproduction flag is not True; HOLD and investigate")
    for model in CONDITIONS:
        close(repro["test_uq_macro_f1_absolute_differences"][model],
              abs(uq["en"][model]["macro_f1"] -
                  prior["metrics"]["test_uq"][model]["macro_f1"]),
              "Reported P1 reproduced difference "+model)
        demand(repro["test_uq_macro_f1_absolute_differences"][model] <= TOL,
               "English P1 reproduced difference larger than 1e-8")
    for variant in VARIANTS:
        m = uq[variant]
        close(m["B2_minus_B1"]["delta_B2_minus_B1"],
              m["B2"]["macro_f1"]-m["B1"]["macro_f1"],
              "B2-B1 ablation/"+variant)
        ci = m["B2_minus_B1"]["percentile_95_ci"]
        demand(len(ci) == 2 and -1 <= ci[0] <= ci[1] <= 1
               and m["B2_minus_B1"]["cluster_count"] == 15
               and m["B2_minus_B1"]["bootstrap_iterations"] == CI_REPS,
               "Invalid paired B2/B1 cluster bootstrap: " + variant)
    paired = uq["paired_TR_revision_deltas"]
    delta_rows = []
    for model in CONDITIONS:
        x = paired[model]
        observed = uq["tr_v0_2_1"][model]["macro_f1"] - uq["tr_v0_2"][model]["macro_f1"]
        close(x["delta_B2_minus_B1"], observed, "TR revision paired diff/"+model)
        ci = x["percentile_95_ci"]
        demand(len(ci) == 2 and -1 <= ci[0] <= ci[1] <= 1
               and x["cluster_count"] == 15
               and x["bootstrap_iterations"] == CI_REPS,
               "Invalid TR revision paired cluster CI: "+model)
        delta_rows.append({
            "model": model, "tr_v021_minus_tr_v02_macro_f1": observed,
            "paired_ci_low": ci[0], "paired_ci_high": ci[1],
            "cluster_count": 15, "bootstrap_iterations": CI_REPS
        })
    did = uq["repair_effect_on_context_gain"]
    did_point = ((uq["tr_v0_2_1"]["B2"]["macro_f1"] -
                  uq["tr_v0_2_1"]["B1"]["macro_f1"]) -
                 (uq["tr_v0_2"]["B2"]["macro_f1"] -
                  uq["tr_v0_2"]["B1"]["macro_f1"]))
    close(did["point"], did_point, "TR revision difference in context ablation")
    demand(len(did["percentile_95_ci"]) == 2
           and -2 <= did["percentile_95_ci"][0] <= did["percentile_95_ci"][1] <= 2
           and did["cluster_count"] == 15
           and did["bootstrap_iterations"] == CI_REPS,
           "Invalid difference-in-context bootstrap estimate")

    stage.mkdir(parents=True)
    try:
        csv_out(stage / "all_model_metrics.csv", metric_rows, MODEL_FIELDS)
        csv_out(stage / "test_uq_per_class_f1.csv", class_rows, CLASS_FIELDS)
        csv_out(stage / "test_uq_paired_tr_deltas.csv", delta_rows, DELTA_FIELDS)
        summary = {
            "stage": "T4_OFFLINE_LEXICAL_PROXY_METRIC_ACCEPTANCE",
            "status": "EXPLORATORY_PROJECTED_LABEL_NOT_TURKISH_GOLD",
            "t4_results_sha256": sha256(t4_file),
            "english_p1_results_sha256": sha256(p1_file),
            "software_evaluation_split_counts": SPLIT_ROWS,
            "test_uq_rows": 733, "test_uq_english_question_clusters": 15,
            "english_p1_reproduced_within_1e_8": True,
            "all_3x4x3_model_confusion_matrices_verified": True,
            "all_variant_per_class_support_identical": True,
            "tr_v021_C_frozen_from_tr_v02": True,
            "primary_difference_in_context_ablation": {
                "point": did_point,
                "percentile_95_ci": did["percentile_95_ci"],
                "question_cluster_count": 15,
                "bootstrap_iterations": 1000,
            },
            "test_uq_english_support_per_class": {
                label: support_by_split["test_uq"][i]
                for i, label in enumerate(LABELS)
            },
            "human_gold_labels": False,
            "no_text_or_row_predictions_exported": True,
            "caveat": ("Arithmetic consistency of offline metrics is not an independent "
                       "Turkish translation or scientific meaning validation."),
        }
        (stage / "t4_metrics_audit.json").write_text(
            json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        md = [
            "# T4 lexical projected-label Test-UQ — Arithmetic acceptance and aggregate review",
            "",
            "Original English P1 exact comparison (1e-8): **PASS**",
            "All confusion matrices, accuracy, macro/weighted F1 and per-class F1 checked: **PASS**",
            "All 3 variants share identical original English question-cluster identities and label supports.",
            "",
            "| Model | EN | TR v0.2 | TR v0.2.1 |",
            "|---|---:|---:|---:|",
        ]
        for model in CONDITIONS:
            md.append("| "+model+" | "+" | ".join(
                f"{uq[v][model]['macro_f1']:.6f}" for v in VARIANTS)+" |")
        md += [
            "", "## TR revision-paired cluster differences (v0.2.1 minus v0.2)", "",
            "| Model | Macro-F1 delta | 95% percentile CI |",
            "|---|---:|---|",
        ]
        for x in delta_rows:
            md.append(f"| {x['model']} | {x['tr_v021_minus_tr_v02_macro_f1']:+.6f} "
                      f"| [{x['paired_ci_low']:+.6f}, {x['paired_ci_high']:+.6f}] |")
        md += [
            "", f"Difference of context-gain differences: {did_point:+.8f}, "
            f"CI [{did['percentile_95_ci'][0]:+.8f}, "
            f"{did['percentile_95_ci'][1]:+.8f}] (15 English question groups).",
            "",
            "Per-class precision, recall, F1 and supports in test_uq_per_class_f1.csv.",
            "Only aggregate counts/metrics are exported. Never share student texts or IDs.",
            "No Turkish human-reviewed gold; repeated Test-UQ reuse and small cluster count limit inference.",
            "No causal inference; no parameter tuning from held-out scores.", "",
        ]
        (stage / "t4_metrics_summary.md").write_text("\n".join(md), encoding="utf-8")
        stage.rename(out)
    except BaseException:
        print("Metric audit incomplete; partial output preserved at", stage)
        raise
    print("T4 METRIC AUDIT PASS: 36 confusion matrices, all class metrics, P1 exact match.")
    print("T4 UQ label support:", summary["test_uq_english_support_per_class"])
    print("TR revision context-gain DID:", did_point, "CI:", did["percentile_95_ci"])
    for x in delta_rows:
        print("TR revision", x["model"], "delta:", round(x["tr_v021_minus_tr_v02_macro_f1"], 6),
              "CI:", [round(x["paired_ci_low"], 6), round(x["paired_ci_high"], 6)])
    print("Aggregate-only reports:", out)
    return summary


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--t4", type=Path, default=Path(
        "results/t4_proxy_v021/t4_proxy_results.json"))
    p.add_argument("--prior-en", type=Path, default=Path(
        "results/lexical/baseline_results.json"))
    p.add_argument("--out", type=Path, default=Path(
        "reports/tr_t4_metric_audit_v01"))
    a = p.parse_args()
    audit(a.t4, a.prior_en, a.out)


if __name__ == "__main__":
    main()
