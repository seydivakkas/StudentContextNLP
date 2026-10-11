"""Translate entire SciEntsBank dataset using a locally installed EN->TR Argos model."""
import argparse
import json
from pathlib import Path

from tr_adaptation.engine import ensure_model_manifest, load_argos_translation
from tr_adaptation.pipeline import run_data_dir


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--data-dir', type=Path, default=Path('data/raw'))
    p.add_argument('--output-dir', type=Path, default=Path('data/tr_v0_2'))
    p.add_argument('--model-manifest', type=Path, default=Path('models/argos_en_tr_manifest.json'))
    p.add_argument('--limit-per-split', type=int, help='Only local smoke verification; default = ALL ROWS')
    p.add_argument('--allow-audit-warnings', action='store_true', help='Only after reviewing source P0')
    args = p.parse_args()
    translator, metadata = load_argos_translation()
    model_info = ensure_model_manifest(args.model_manifest, metadata)
    result = run_data_dir(args.data_dir, args.output_dir, translator, model_info,
                          limit_per_split=args.limit_per_split,
                          allow_audit_warnings=args.allow_audit_warnings)
    print('Candidate rows:', result['total_translated_rows'])
    print('State:', result['validation_state'], '/ scope:', result['scope'])
    print('Manifest:', args.output_dir / 'translation_manifest.json')


if __name__ == '__main__':
    main()
