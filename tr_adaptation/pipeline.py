"""Full-coverage SciEntsBank EN->TR adaptation, with resumable cache and audit gates.

Translation is NOT human validated and projected labels are NOT Turkish gold labels.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
from collections import Counter
from pathlib import Path
from typing import Callable

import pandas as pd

from audit_dataset import SPLITS, audit, read_split
from .quality import review_flags

TEXT_COLUMNS = ('question', 'reference_answer', 'student_answer')
OUT_STEM = {'train': 'train', 'test_ua': 'test-ua', 'test_uq': 'test-uq', 'test_ud': 'test-ud'}


def _digest(obj: object) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False).encode('utf-8')).hexdigest()


def _cache_path(output: Path) -> Path:
    return output / '_cache' / 'translations.jsonl'


def _read_cache(path: Path, model_key: str) -> dict[str, str]:
    cache = {}
    if not path.exists():
        return cache
    with path.open(encoding='utf-8') as handle:
        for line in handle:
            if not line.strip():
                continue
            obj = json.loads(line)
            if obj['model_key'] != model_key:
                raise RuntimeError('Cache farklı modelden üretilmiş; farklı --output-dir kullan.')
            old = cache.get(obj['source'])
            if old is not None and old != obj['target']:
                raise ValueError('Çeviri önbelleğinde tutarsız çıktı')
            cache[obj['source']] = obj['target']
    return cache


def translate_frames(
    frames: dict[str, pd.DataFrame], source_paths: dict[str, Path], output: Path,
    translator: Callable[[str], str], model_manifest: dict,
    *, limit_per_split: int | None = None, allow_audit_warnings: bool = False,
) -> dict:
    """Transform four actual splits, preserve label provenance, and write local CSVs.

    A limited run is explicitly marked PARTIAL_SMOKE, never a scientific corpus.
    """
    if limit_per_split is not None and limit_per_split < 1:
        raise ValueError('limit_per_split pozitif olmalı')
    check = audit(frames, source_paths)
    if check['fatal_errors']:
        raise RuntimeError('İngilizce P0 fatal: ' + '; '.join(check['fatal_errors']))
    if check['warnings'] and not allow_audit_warnings:
        raise RuntimeError('İngilizce P0 uyarıları incelenmeli: ' + '; '.join(check['warnings']))
    model_key = _digest({k: model_manifest.get(k) for k in ('package_sha256', 'package_version', 'source_code', 'target_code')})
    if not model_manifest.get('package_sha256'):
        raise RuntimeError('Kaynak modelin SHA-256 özeti zorunlu')
    output.mkdir(parents=True, exist_ok=True)
    cache_file = _cache_path(output)
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    cache = _read_cache(cache_file, model_key)
    original_cache_count = len(cache)
    scope = 'FULL_CANDIDATE' if limit_per_split is None else 'PARTIAL_SMOKE'
    manifest_file = output / 'translation_manifest.json'
    if manifest_file.exists():
        previous = json.loads(manifest_file.read_text(encoding='utf-8'))
        if previous.get('model_key') != model_key or previous.get('scope') != scope:
            raise RuntimeError('Manifest model veya kapsam uyuşmazlığı: yeni output klasörü kullan')
        for k, v in previous.get('source_file_sha256', {}).items():
            if k in source_paths and hashlib.sha256(source_paths[k].read_bytes()).hexdigest() != v:
                raise RuntimeError('Kaynak dosya SHA değişmiş; yeni output klasörü kullan')
    source_hashes = {k: hashlib.sha256(v.read_bytes()).hexdigest() for k, v in source_paths.items()}
    summary = {}
    total_rows = 0
    with cache_file.open('a', encoding='utf-8', newline='\n') as fp:
        for split in SPLITS:
            if split not in frames:
                raise RuntimeError(f'Kaynak bölümü eksik: {split}')
            original = frames[split]
            frame = original if limit_per_split is None else original.head(limit_per_split)
            rendered = []
            flag_counter = Counter()
            for row in frame.itertuples(index=False):
                source = {key: str(getattr(row, key)) if not pd.isna(getattr(row, key)) else '' for key in TEXT_COLUMNS}
                translated = {}
                combined_flags = []
                for key, en in source.items():
                    if not en.strip():
                        translated[key] = ''
                        combined_flags.append(f'{key}:EMPTY_SOURCE')
                        continue
                    if en not in cache:
                        tr = translator(en)
                        if not isinstance(tr, str):
                            raise TypeError('Çeviri motoru string döndürmedi')
                        # Keep untranslated/empty candidates only as flagged entries; no silent scientific correction.
                        fp.write(json.dumps({'model_key': model_key, 'source': en, 'target': tr}, ensure_ascii=False) + '\n')
                        fp.flush()
                        cache[en] = tr
                    translated[key] = cache[en]
                    combined_flags.extend(f'{key}:{flag}' for flag in review_flags(en, translated[key]))
                flag_counter.update(combined_flags)
                rendered.append({
                    'id': str(row.id), 'question': translated['question'],
                    'reference_answer': translated['reference_answer'],
                    'student_answer': translated['student_answer'],
                    'label': getattr(row, 'label'),
                    'source_question_en': source['question'],
                    'source_reference_answer_en': source['reference_answer'],
                    'source_student_answer_en': source['student_answer'],
                    'quality_flags': json.dumps(sorted(set(combined_flags)), ensure_ascii=False),
                    'label_status': 'UNVERIFIED_TRANSFER',
                    'translation_scope': scope,
                })
            result_frame = pd.DataFrame(rendered)
            target = output / f'{OUT_STEM[split]}.csv'
            part = target.with_suffix('.csv.part')
            result_frame.to_csv(part, index=False)
            os.replace(part, target)
            rows = len(result_frame)
            total_rows += rows
            summary[split] = {'source_rows': len(original), 'translated_rows': rows,
                              'candidate_coverage': rows / len(original) if len(original) else 0,
                              'flagged_rows': int(result_frame['quality_flags'].ne('[]').sum()),
                              'flags': dict(sorted(flag_counter.items())),
                              'output_sha256': hashlib.sha256(target.read_bytes()).hexdigest()}
            print(f'{split}: {rows}/{len(original)} translated; flags on {summary[split]["flagged_rows"]} rows')
    manifest = {'pipeline_version': '0.2.0', 'source_dataset': 'nkazi/SciEntsBank',
                'model': model_manifest, 'model_key': model_key,
                'scope': scope, 'validation_state': 'UNVERIFIED_MACHINE_TRANSLATION',
                'projected_labels_are_gold': False, 'source_p0_status': check['status'],
                'source_p0_warnings': check['warnings'],
                'source_file_sha256': source_hashes, 'splits': summary,
                'total_source_rows': sum(len(frames[k]) for k in SPLITS),
                'total_translated_rows': total_rows,
                'new_unique_translations': len(cache) - original_cache_count,
                'unique_cached_texts': len(cache),
                'warning': 'Full translation coverage is NOT expert validation or real Turkish student data.'}
    tmp = manifest_file.with_suffix('.json.part')
    tmp.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding='utf-8')
    os.replace(tmp, manifest_file)
    return manifest


def run_data_dir(data_dir: Path, out: Path, translator, manifest: dict, *, limit_per_split=None, allow_audit_warnings=False):
    frames, paths = {}, {}
    for split in SPLITS:
        frames[split], paths[split] = read_split(data_dir, split)
    return translate_frames(frames, paths, out, translator, manifest,
                            limit_per_split=limit_per_split, allow_audit_warnings=allow_audit_warnings)
