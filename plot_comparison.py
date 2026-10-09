"""Simple headless matplotlib plots from persisted benchmark results."""
from __future__ import annotations
import argparse
import csv
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def make_plot(csv_path: Path, output: Path, synthetic: bool = False) -> None:
    with csv_path.open(encoding='utf-8', newline='') as f:
        rows = list(csv.DictReader(f))
    sel = [r for r in rows if r['split'] == 'test_uq']
    if not sel:
        raise ValueError('test_uq sonucu bulunamadı')
    output.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(8, 4))
    xs = list(range(len(sel)))
    ax.bar(xs, [float(r['macro_f1']) for r in sel])
    ax.set_xticks(xs, [r['condition'] for r in sel]); ax.set_ylim(0, 1)
    ax.set_ylabel('Macro-F1'); ax.set_xlabel('Model')
    ax.set_title(('SYNTHETIC SOFTWARE TEST — ' if synthetic else '') + 'Test-UQ Macro-F1')
    fig.tight_layout()
    fig.savefig(output, dpi=160)
    plt.close(fig)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--csv', type=Path, default=Path('results/combined/model_comparison.csv'))
    p.add_argument('--out', type=Path, default=Path('results/figures/test_uq_macro_f1.png'))
    args = p.parse_args()
    make_plot(args.csv, args.out, synthetic=('demo' in args.csv.parts))
