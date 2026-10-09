"""Generate figures from REAL lexical evaluation results. Does not train or download data."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

MODELS = ('B0','B1','B2','B3')
LABELS = ('Correct', 'Incomplete', 'Contradictory', 'Other')


def build(src: Path, output: Path) -> None:
    if not src.exists():
        raise FileNotFoundError('Gerçek eğitim sonuçları yok; figür üretimi engellendi: ' + str(src))
    result = json.loads(src.read_text(encoding='utf-8'))
    output.mkdir(parents=True, exist_ok=True)
    for split, details in result['metrics'].items():
        vals = [details[m]['macro_f1'] for m in MODELS]
        fig, ax = plt.subplots(figsize=(7,4))
        bars = ax.bar(MODELS, vals)
        ax.set_title(f'{split}: Macro-F1 (4-class)')
        ax.set_ylim(0, 1)
        ax.set_xlabel('Model')
        ax.set_ylabel('Macro-F1')
        for b, val in zip(bars, vals):
            ax.text(b.get_x() + b.get_width()/2, min(val+.02,.97), f'{val:.3f}', ha='center', fontsize=9)
        fig.tight_layout()
        fig.savefig(output/f'{split}_macro_f1.png', dpi=170)
        plt.close(fig)
    uq = result['metrics']['test_uq']
    for model in ('B1','B2'):
        cm = np.asarray(uq[model]['confusion_matrix'])
        fig, ax = plt.subplots(figsize=(6,5))
        im = ax.imshow(cm)
        fig.colorbar(im,ax=ax)
        ax.set_xticks(range(4), LABELS, rotation=25, ha='right')
        ax.set_yticks(range(4), LABELS)
        ax.set_xlabel('Predicted')
        ax.set_ylabel('Actual')
        ax.set_title(f'Test-UQ: {model} confusion matrix')
        for (i,j), v in np.ndenumerate(cm):
            ax.text(j,i,str(v),ha='center',va='center',color='white' if v>cm.max()/2 else 'black')
        fig.tight_layout()
        fig.savefig(output/f'test_uq_{model}_cm.png',dpi=170)
        plt.close(fig)
    print('Saved figures:',output)


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--results',type=Path,default=Path('results/lexical/baseline_results.json'))
    p.add_argument('--output',type=Path,default=Path('results/figures'))
    a=p.parse_args()
    build(a.results,a.output)
