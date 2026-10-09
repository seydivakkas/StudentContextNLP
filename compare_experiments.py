"""Generate a compact experiment table. Reads results from prior *local* runs."""
from __future__ import annotations
import argparse
import csv
import json
from pathlib import Path

ROWS = (('B0', 'lexical'), ('B1', 'lexical'), ('B2', 'lexical'), ('B3', 'lexical'),
        ('S1', 'semantic'), ('S2', 'semantic'))


def load(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding='utf-8'))


def report(lexical_file: Path, semantic_file: Path, output: Path) -> dict:
    lexical = load(lexical_file)
    semantic = load(semantic_file)
    if not lexical and not semantic:
        raise FileNotFoundError('Hiçbir sonuç dosyası mevcut değil')
    if lexical and semantic:
        if lexical.get('seed') != semantic.get('seed'):
            raise ValueError('Lexical/Semantic seed farklı; karşılaştırma yasak')
        if bool(lexical.get('synthetic_data')) != bool(semantic.get('synthetic_data')):
            raise ValueError('Sentetik ve gerçek veriler bir arada karşılaştırılamaz')
    rows = []
    for split in ('test_ua', 'test_uq', 'test_ud'):
        for cond, source in ROWS:
            obj = lexical if source == 'lexical' else semantic
            item = obj.get('metrics', {}).get(split, {}).get(cond)
            if item:
                rows.append({'split': split, 'condition': cond, 'representation': source,
                             'macro_f1': item['macro_f1'], 'weighted_f1': item['weighted_f1'],
                             'accuracy': item['accuracy'], 'n_rows': item['n_rows']})
    output.mkdir(parents=True, exist_ok=True)
    with (output / 'model_comparison.csv').open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    def gain(artifact, a, b):
        m = artifact.get('metrics', {}).get('test_uq', {})
        if not m or a not in m or b not in m:
            return None
        return m[b]['macro_f1'] - m[a]['macro_f1']
    summary = {'data_kind': 'SYNTHETIC_SOFTWARE_TEST' if (lexical or semantic).get('synthetic_data') else 'INPUT_DATA_NOT_INDEPENDENTLY_VERIFIED',
               'primary_metric': 'macro_f1_on_test_uq', 'lexical_question_context_gain': gain(lexical, 'B1', 'B2'),
               'semantic_question_context_gain': gain(semantic, 'S1', 'S2'),
               'note': 'Never claim that software smoke-test scores are real research results.'}
    (output / 'comparison_summary.json').write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding='utf-8')
    title = '# Model Comparison — ' + summary['data_kind']
    md = [title, '', '| Split | Model | Representation | Macro-F1 | Weighted-F1 | Accuracy |', '|---|---|---|---:|---:|---:|']
    for r in rows:
        md.append(f"| {r['split']} | {r['condition']} | {r['representation']} | {r['macro_f1']:.4f} | {r['weighted_f1']:.4f} | {r['accuracy']:.4f} |")
    md.extend(['', '## Primary test-UQ context gains', '',
               f"- Lexical B2−B1: {summary['lexical_question_context_gain']}",
               f"- Semantic S2−S1: {summary['semantic_question_context_gain']}", '', summary['note'], ''])
    (output / 'model_comparison.md').write_text('\n'.join(md), encoding='utf-8')
    return summary


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--lexical', type=Path, default=Path('results/lexical/baseline_results.json'))
    p.add_argument('--semantic', type=Path, default=Path('results/semantic/semantic_results.json'))
    p.add_argument('--out', type=Path, default=Path('results/combined'))
    args = p.parse_args()
    print(json.dumps(report(args.lexical, args.semantic, args.out), indent=2))
