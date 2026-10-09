"""SYNTHETIC smoke test fixture. Never represents real students or research evidence."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import pandas as pd

CATEGORIES = (
    (0, 'evaporation turns liquid water into vapor', 'water changes into vapor and leaves the surface'),
    (1, 'evaporation is not a nuclear reaction', 'water turns into a nuclear reaction in the container'),
    (2, 'evaporation depends on temperature and exposure', 'heat can help the water change'),
    (3, 'evaporation is the name of a physical process', 'today I went swimming and ate lunch'),
)


def build(out: Path, repeats: int = 5) -> None:
    out.mkdir(parents=True, exist_ok=True)
    for split, questions in {
        'train': [f'topic_{i}' for i in range(20)],
        'test_ua': ['topic_0', 'topic_1'],
        'test_uq': ['novel_0', 'novel_1', 'novel_2'],
        'test_ud': ['transfer_0', 'transfer_1', 'transfer_2'],
    }.items():
        rows = []
        for question in questions:
            for category, reference, answer in CATEGORIES:
                for n in range(repeats):
                    rows.append({'id': f'{split}_{question}_{category}_{n}',
                                 'question': f'Explain science concept {question} in words.',
                                 'reference_answer': reference,
                                 'student_answer': f'{answer}. Variation {n} for concept {question}.',
                                 'label': category})
        pd.DataFrame(rows).to_csv(out / f'{split}.csv', index=False)
    (out / 'SYNTHETIC_DEMO.json').write_text(json.dumps({
        'synthetic': True, 'warning': 'Fabricated data for software validation only, not academic results.'}, indent=2), encoding='utf-8')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, default=Path('data/demo'))
    parser.add_argument('--repeats', type=int, default=5)
    args = parser.parse_args()
    build(args.out, args.repeats)
    print('SYNTHETIC fixtures created:', args.out)
