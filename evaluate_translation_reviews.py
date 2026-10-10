"""Score two human annotations; do not silently mark any dataset fully validated."""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path

import pandas as pd
from sklearn.metrics import cohen_kappa_score

FIELDS = ('meaning_preserved', 'error_preserved', 'label_still_applicable', 'correction_needed')
CHOICES = {'yes', 'no', 'uncertain'}


def evaluate(a: pd.DataFrame, b: pd.DataFrame) -> dict:
    if not a['item_key'].is_unique or not b['item_key'].is_unique:
        raise ValueError('Duplicate review item keys')
    if set(a['item_key']) != set(b['item_key']):
        raise ValueError('Review form item keys differ')
    a, b = a.set_index('item_key').sort_index(), b.set_index('item_key').sort_index()
    result = {'n_items': len(a), 'validation_state': 'HUMAN_REVIEW_AGREEMENT_ONLY_NOT_FULLY_VALIDATED',
              'fields': {}, 'reviewers': 2}
    for col in FIELDS:
        av = a[col].fillna('').astype(str).str.strip().str.lower()
        bv = b[col].fillna('').astype(str).str.strip().str.lower()
        if set(av) - CHOICES or set(bv) - CHOICES:
            raise ValueError(f'{col}: missing/invalid annotations; complete both forms with yes/no/uncertain')
        match = float((av == bv).mean())
        kappa = float(cohen_kappa_score(av, bv, labels=sorted(CHOICES)))
        joint_yes = int(((av == 'yes') & (bv == 'yes')).sum())
        result['fields'][col] = {'agreement': match, 'cohen_kappa': kappa if math.isfinite(kappa) else None,
                                 'both_yes': joint_yes, 'both_yes_rate': joint_yes / len(a) if len(a) else 0,
                                 'disagreements': int((av != bv).sum())}
    return result


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--review-dir', type=Path, default=Path('reports/tr_review'))
    a = p.parse_args()
    first = pd.read_csv(a.review_dir / 'review_A.csv', dtype={'item_key': str}, keep_default_na=False)
    second = pd.read_csv(a.review_dir / 'review_B.csv', dtype={'item_key': str}, keep_default_na=False)
    result = evaluate(first, second)
    output = a.review_dir / 'review_agreement.json'
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding='utf-8')
    print('Independent review agreement written:', output)
    print('This score is sample-based, never full-corpus gold validation.')


if __name__ == '__main__':
    main()
