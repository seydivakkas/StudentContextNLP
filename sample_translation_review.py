"""Prepare reproducible independent review templates for TR adaptation.

The reviewer sees English source, Turkish translation and original category. Each
reviewer completes their own form; original projected label is NOT proof of truth.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from audit_dataset import SPLITS, LABEL_MAP, canonical_label, normalize
from tr_adaptation.pipeline import OUT_STEM

REVIEW_FIELDS = ('meaning_preserved', 'error_preserved', 'label_still_applicable',
                 'correction_needed', 'notes')


def build_sample(data_dir: Path, out: Path, n: int = 240, seed: int = 20261010) -> dict:
    if n < 4:
        raise ValueError('n >= 4 gerekli')
    manifest = json.loads((data_dir / 'translation_manifest.json').read_text(encoding='utf-8'))
    if manifest['scope'] != 'FULL_CANDIDATE' or manifest['validation_state'] != 'UNVERIFIED_MACHINE_TRANSLATION':
        raise RuntimeError('İnsan doğrulaması örneklemesi tam aday veri kümesini gerektirir')
    sections = []
    for split in SPLITS:
        frame = pd.read_csv(data_dir / f'{OUT_STEM[split]}.csv', keep_default_na=False, dtype={'id': str})
        frame['split'] = split
        frame['class4'] = frame['label'].map(lambda v: LABEL_MAP[canonical_label(v)])
        frame['question_group'] = frame['source_question_en'].map(normalize)
        frame['item_key'] = [f'{split}:{i}' for i in range(len(frame))]
        sections.append(frame)
    all_rows = pd.concat(sections, ignore_index=True)
    if any(x not in all_rows.columns for x in ('label_status', 'quality_flags')) or set(all_rows['label_status']) != {'UNVERIFIED_TRANSFER'}:
        raise RuntimeError('Kaynak veri etiketi/provenance uygun değil')
    rng = np.random.default_rng(seed)
    # Stratify across split and class without claiming a statistical probability sample.
    strata = list(all_rows.groupby(['split', 'class4'], sort=True))
    quota = {key: min(len(part), n // len(strata)) for key, part in strata}
    selected = []
    for key, part in strata:
        amount = quota[key]
        if amount:
            # Prefer diverse questions by randomized round-robin over question groups.
            groups = [g for _, g in part.groupby('question_group', sort=True)]
            rng.shuffle(groups)
            buckets = [g.index.to_numpy()[rng.permutation(len(g))].tolist() for g in groups]
            pool = []
            depth = 0
            while len(pool) < amount:
                added = False
                for bucket in buckets:
                    if depth < len(bucket):
                        pool.append(bucket[depth])
                        added = True
                        if len(pool) >= amount:
                            break
                if not added:
                    break
                depth += 1
            selected.extend(pool[:amount])
    remainder = n - len(selected)
    if remainder:
        remaining = np.setdiff1d(all_rows.index.to_numpy(), np.array(selected, dtype=int))
        if len(remaining) < remainder:
            raise ValueError('Örnek sayısı aday veri sayısından büyük')
        selected.extend(rng.choice(remaining, size=remainder, replace=False).tolist())
    picked = all_rows.loc[selected].copy().sort_values('item_key')
    cols = ['item_key', 'split', 'class4', 'id', 'source_question_en', 'question',
            'source_reference_answer_en', 'reference_answer', 'source_student_answer_en',
            'student_answer', 'quality_flags']
    out.mkdir(parents=True, exist_ok=True)
    for reviewer in ('A', 'B'):
        template = picked[cols].copy()
        for f in REVIEW_FIELDS:
            template[f] = ''
        template.to_csv(out / f'review_{reviewer}.csv', index=False)
    output = {'seed': seed, 'requested_n': n, 'actual_n': len(picked),
              'sampling': 'split+class coverage then random fill; not random probability inference',
              'source_manifest_model_key': manifest['model_key'],
              'splits': picked['split'].value_counts().to_dict(),
              'classes': picked['class4'].value_counts().to_dict(),
              'validation_state': 'AWAITING_INDEPENDENT_HUMAN_REVIEW',
              'instructions': {'meaning_preserved': 'yes/no/uncertain',
                               'error_preserved': 'yes/no/uncertain',
                               'label_still_applicable': 'yes/no/uncertain',
                               'correction_needed': 'yes/no/uncertain',
                               'notes': 'Only reviewer observations, no student identifiers'}}
    (out / 'review_manifest.json').write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding='utf-8')
    return output


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--data-dir', type=Path, default=Path('data/tr_v0_2'))
    p.add_argument('--out', type=Path, default=Path('reports/tr_review'))
    p.add_argument('--n', type=int, default=240)
    p.add_argument('--seed', type=int, default=20261010)
    a = p.parse_args()
    print(json.dumps(build_sample(a.data_dir, a.out, a.n, a.seed), indent=2, ensure_ascii=False))
