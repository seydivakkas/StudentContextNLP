"""Deterministic, offline EN->TR translation QA triage. NOT human review or gold labels.

python audit_translation_quality.py --input reports/tr_review/blind_stage1/review_A_blind.csv --out reports/tr_auto_qa_v01

No network or API calls. Never modifies review_A/B or translation files.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import re

PAIRS = (
    ('question', 'source_question_en', 'question'),
    ('reference_answer', 'source_reference_answer_en', 'reference_answer'),
    ('student_answer', 'source_student_answer_en', 'student_answer'),
)
MIN_COLS = frozenset(['item_key'] + [c for _, e, t in PAIRS for c in (e, t)])
SUSPICION_STATE = 'AUTOMATIC_CANDIDATE_NOT_HUMAN_VERIFIED'
GLOSSARY = (
    ('calcite', r'\bcalcite\b', r'\bkalsit\w*\b|\bkalsiyum\s+karbonat\b'),
    ('fulcrum', r'\bfulcrum\b', r'\bdayanak\w*\b|\bdestek\s+nokta\w*\b|\bdönme\s+nokta\w*\b'),
    ('pebbles', r'\bpebbles?\b', r'\bçakıl\w*\b'),
    ('clay', r'\bclay\b', r'\bkil\w*\b'),
    ('salt', r'\bsalt\b', r'\btuz\w*\b'),
    ('nail_in_magnets', r'\bnails?\b', r'\bçivi\w*\b'),
    ('bulb_in_circuits', r'\bbulbs?\b', r'\bampul\w*\b|\blamba\w*\b'),
    ('square', r'\bsquares?\b', r'\bkare\w*\b|\bdörtgen\w*\b'),
    ('slope', r'\bslope\b', r'\beğim\w*\b|\byokuş\w*\b|\bmeğil\w*\b'),
    ('erosion', r'\berosion\b', r'\berozyon\w*\b|\başın\w*\b'),
    ('mirror', r'\bmirrors?\b', r'\bayna\w*\b'),
    ('wire', r'\bwires?\b', r'\btel\w*\b|\bkablo\w*\b'),
)
BAD_PAIRS = (
    ('CALCITE_AS_ANALYSIS', r'\bcalcite\b', r'\banaliz\s+kristal\w*\b|\banaliz\s+taş\w*\b'),
    ('BULB_AS_BUS', r'\bbulbs?\b', r'\botobüs\w*\b'),
    ('NAIL_AS_FINGERNAIL', r'\bnails?\b', r'\btırnak\w*\b'),
    ('SQUARE_AS_CHALLENGE', r'\bsquares?\b', r'\bmeydan\s+ok\w*\b'),
    ('PLANT_POT_AS_SAUCEPAN', r'\bpots?\b', r'\btencere\w*\b'),
    ('CHEMICAL_SOLID_AS_STURDY', r'\bsolids?\b', r'\bsağlam\b'),
    ('FOGGED_GLASS_AS_SHINY', r'\bfogg?ed\s+up\b', r'\bparlak\b'),
    ('NO_SLOPE_AS_NONSENSE', r'\bno\s+slope\b', r'\bgöçücü\b'),
)
LEFTOVER = re.compile(r'\b(?:flaky|pebbles|fulcrum|slope|scratch|calcite|salt|bulb)\b', re.I)
NUM = re.compile(r'(?<!\w)\d+(?:[.,]\d+)?%?(?!\w)')
EN_NEG = re.compile(r"\b(?:not|never|no|without|cannot|can't|doesn't|don't|isn't|aren't|wasn't|weren't|won't|couldn't|shouldn't)\b", re.I)
TR_NEG = re.compile(r'\b(?:değil|yok|asla|hiç|hayır|olmaz|olamaz|olmayan|olmuyor|olmadı|yapamaz|olmaksızın)\b|\b\w+(?:mıyor|miyor|muyor|müyor|madı|medi|maz|mez|mayacak|meyecek|mamak|memek|madan|meden|madığı|mediği|mayan|meyen)\b', re.I)
EN_ONLY = re.compile(r'\b(?:only|solely|exclusively)\b', re.I)
TR_ONLY = re.compile(r'\b(?:sadece|yalnız\w*|ancak|tek|salt)\b', re.I)
EN_MORE = re.compile(r'\b(?:more|greater|higher|faster|heavier)\b', re.I)
EN_LESS = re.compile(r'\b(?:less|lower|slower|lighter)\b', re.I)
TR_MORE = re.compile(r'\b(?:daha\s+(?:fazla|çok|büyük|yüksek|hızlı|ağır)|artar\w*|yüksel\w*)\b', re.I)
TR_LESS = re.compile(r'\b(?:daha\s+(?:az|küçük|düşük|yavaş|hafif)|azal\w*|düşer\w*)\b', re.I)
RANK = {'HIGH': 3, 'MEDIUM': 2, 'LOW': 1}


def _contains(pattern: str | re.Pattern, text: str) -> bool:
    return bool(re.search(pattern, text, re.IGNORECASE) if isinstance(pattern, str) else pattern.search(text))


def _num_list(text: str) -> list[str]:
    return sorted(i.replace(',', '.') for i in NUM.findall(text))


def _flag(item_key: str, field: str, severity: str, code: str, reason: str,
          source: str, target: str) -> dict:
    return {'item_key': item_key, 'field': field, 'priority': severity, 'rule': code,
            'reason_tr': reason, 'source_en': source, 'target_tr': target,
            'status': SUSPICION_STATE}


def analyze_pair(item_key: str, field: str, source: str, target: str) -> list[dict]:
    flags = []

    def add(priority: str, code: str, reason: str) -> None:
        flags.append(_flag(item_key, field, priority, code, reason, source, target))

    en, tr = source.strip(), target.strip()
    if en and not tr:
        add('HIGH', 'EMPTY_TRANSLATION', 'Kaynak metin var ama hedef metin boş.')
        return flags
    if not en:
        return flags
    if en.casefold() == tr.casefold():
        add('MEDIUM', 'UNCHANGED', 'İngilizce kaynak Türkçe alanda aynen kalmış.')
    if tr and (len(tr) < 0.25 * len(en) or len(tr) > 4.0 * len(en)):
        add('MEDIUM', 'LENGTH_OUTLIER', 'İngilizce/Türkçe metin uzunluğu olağandışı; olası eksilme/ekleme.')
    if _num_list(en) != _num_list(tr):
        add('HIGH', 'NUMBER_CHANGED', 'Kaynak ve çevirideki sayısal değerler farklı; sayı yazıyla çevrildiyse elle denetlenmeli.')
    if EN_NEG.search(en) and not TR_NEG.search(tr):
        add('MEDIUM', 'NEGATION_NOT_EVIDENT', 'İngilizce olumsuzluk Türkçede yüzeysel olarak bulunamadı; ekli olumsuzlukları gözden geçir.')
    if EN_ONLY.search(en) and not TR_ONLY.search(tr):
        add('MEDIUM', 'EXCLUSIVITY_NOT_EVIDENT', '"Only/solely" kısıtlaması Türkçede görünmüyor olabilir.')
    if EN_MORE.search(en) and not EN_LESS.search(en) and TR_LESS.search(tr) and not TR_MORE.search(tr):
        add('MEDIUM', 'COMPARATIVE_DIRECTION', 'Artış/çokluk karşılaştırması Türkçede azlık/yavaşlık yönüne kaymış olabilir.')
    if EN_LESS.search(en) and not EN_MORE.search(en) and TR_MORE.search(tr) and not TR_LESS.search(tr):
        add('MEDIUM', 'COMPARATIVE_DIRECTION', 'Azlık/yavaşlık karşılaştırması Türkçede çokluk/hız yönüne kaymış olabilir.')

    for term, en_pat, tr_pat in GLOSSARY:
        if term == 'nail_in_magnets' and not _contains(r'\bmagnet\w*\b|\bmetal\b|\biron\b', en):
            continue
        if term == 'bulb_in_circuits' and not _contains(r'\bcircuit\w*\b|\blight\b|\bwire\w*\b|\belectric\w*\b', en):
            continue
        if _contains(en_pat, en) and not _contains(tr_pat, tr):
            add('MEDIUM', 'TERM_NOT_EVIDENT:' + term,
                f'Bilimsel terimin Türkçe karşılığı açıkça görülmüyor: {term}. Eşanlam/parafraz olabilir.')
    for code, en_pat, tr_pat in BAD_PAIRS:
        if _contains(en_pat, en) and _contains(tr_pat, tr):
            add('HIGH', code, 'Bilimsel anlamı bozabilecek yanlış terim karşılığı bulundu.')
    if LEFTOVER.search(tr):
        tokens = sorted(set(s.lower() for s in LEFTOVER.findall(tr)))
        add('MEDIUM', 'ENGLISH_TERM_LEFTOVER',
            'Türkçe metinde İngilizce terim kaldı: ' + ', '.join(tokens))
    return flags


def scan_rows(rows: list[dict]) -> tuple[list[dict], list[dict], dict]:
    seen = set()
    all_flags = []
    queue = []
    for row in rows:
        key = str(row.get('item_key', '')).strip()
        if not key or key in seen:
            raise ValueError('Boş veya tekrar eden item_key: ' + key)
        seen.add(key)
        flags = []
        for field, en_col, tr_col in PAIRS:
            flags.extend(analyze_pair(key, field, row[en_col], row[tr_col]))
        all_flags.extend(flags)
        high = sum(x['priority'] == 'HIGH' for x in flags)
        med = sum(x['priority'] == 'MEDIUM' for x in flags)
        queue.append({'item_key': key, 'priority': 'HIGH' if high else 'MEDIUM' if med else 'UNFLAGGED',
                      'high_flag_count': high, 'medium_flag_count': med,
                      'rules': '|'.join(sorted(set(f['rule'] for f in flags))),
                      'finding_count': len(flags),
                      'source_student_answer_en': row['source_student_answer_en'],
                      'student_answer_tr': row['student_answer'],
                      'source_question_en': row['source_question_en'],
                      'question_tr': row['question'],
                      'status': SUSPICION_STATE})
    counts = Counter(f['rule'] for f in all_flags)
    high_rows = sum(x['priority'] == 'HIGH' for x in queue)
    medium_rows = sum(x['priority'] == 'MEDIUM' for x in queue)
    summary = {'analysis_type': 'OFFLINE_HEURISTIC_TRANSLATION_TRIAGE',
               'verification_state': SUSPICION_STATE, 'rows': len(rows),
               'candidate_flagged_rows': high_rows + medium_rows,
               'high_priority_rows': high_rows, 'medium_priority_rows': medium_rows,
               'unflagged_rows': len(rows) - high_rows - medium_rows,
               'total_flags': len(all_flags), 'rule_counts': dict(sorted(counts.items())),
               'not_human_review': True, 'not_gold_data': True,
               'no_flags_does_not_prove_correctness': True,
               'interpretation': 'Surface rules flag candidates, not confirmed errors. Distinct flags may concern question, reference, or student answer. No independent reviewers, Cohen kappa or corpus-wide error-rate estimate.'}
    return all_flags, queue, summary


def write_csv(path: Path, rows: list[dict], names: list[str]) -> None:
    with path.open('w', encoding='utf-8-sig', newline='') as fp:
        writer = csv.DictWriter(fp, fieldnames=names, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument('--input', type=Path, default=Path('reports/tr_review/blind_stage1/review_A_blind.csv'))
    p.add_argument('--out', type=Path, default=Path('reports/tr_auto_qa'))
    args = p.parse_args()
    if not args.input.exists():
        raise FileNotFoundError(f'Input not found: {args.input}')
    if args.out.resolve() == args.input.parent.resolve():
        raise ValueError('Output directory must be separate from reviewer form location')
    with args.input.open('r', newline='', encoding='utf-8-sig') as fp:
        reader = csv.DictReader(fp)
        if not reader.fieldnames or not MIN_COLS.issubset(reader.fieldnames):
            raise ValueError('Invalid blind CSV schema; expected source/target text and item_key')
        rows = list(reader)
    flags, queue, summary = scan_rows(rows)
    summary['input_file'] = args.input.name
    summary['input_sha256'] = hashlib.sha256(args.input.read_bytes()).hexdigest()
    summary['rule_version'] = '0.1.0'
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    targets = [out / 'translation_flags.csv', out / 'review_queue.csv', out / 'qa_summary.json', out / 'qa_summary.md']
    if any(x.exists() for x in targets):
        raise FileExistsError('QA output exists. Choose a fresh --out to keep previous evidence.')
    flags.sort(key=lambda r: (-RANK[r['priority']], r['item_key'], r['field'], r['rule']))
    queue.sort(key=lambda r: (0 if r['priority'] == 'HIGH' else 1 if r['priority'] == 'MEDIUM' else 2,
                              -r['finding_count'], r['item_key']))
    write_csv(targets[0], flags,
              ['item_key', 'field', 'priority', 'rule', 'reason_tr', 'source_en', 'target_tr', 'status'])
    write_csv(targets[1], queue,
              ['item_key', 'priority', 'high_flag_count', 'medium_flag_count', 'rules', 'finding_count',
               'source_student_answer_en', 'student_answer_tr', 'source_question_en', 'question_tr', 'status'])
    targets[2].write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    lines = ['# T3 — Yerel Otomatik Çeviri Ön İncelemesi', '',
             f'- Kayıt: **{summary["rows"]}**',
             f'- Yüksek öncelikli aday: **{summary["high_priority_rows"]}**',
             f'- Orta öncelikli aday: **{summary["medium_priority_rows"]}**',
             f'- Kuralca işaretlenmeyen: **{summary["unflagged_rows"]}**',
             f'- Toplam kural bulgusu: **{summary["total_flags"]}**',
             '', '## Kural sayıları', '']
    lines += [f'- {rule}: {count}' for rule, count in sorted(summary['rule_counts'].items(),
                                                           key=lambda it: (-it[1], it[0]))]
    lines += ['', '## Yöntem ve sınır',
              'Bu yalnızca deterministik yerel şüphe taramasıdır. İşaretlenmiş kayıtların hatalı olduğu **kanıtlanmış değildir**; işaretlenmeyenler de doğrulanmış doğru değildir.',
              'Kaynak öğrenci hatasının korunumu, iki bağımsız insan incelemesi, Cohen kappa veya Türkçe gold etiketler otomatik üretilmemiştir.',
              'İnceleme sıra listesi review_queue.csv dosyasındadır; hücre düzeyi sebepler translation_flags.csv içindedir.',
              "Ham metinleri GitHub'a yüklemeyin. Değerlendirici A/B formları değiştirilmedi.", '']
    targets[3].write_text('\n'.join(lines), encoding='utf-8')
    print('Translation triage:', summary['rows'], 'rows')
    print('High:', summary['high_priority_rows'], 'Medium:', summary['medium_priority_rows'],
          'No rule flag:', summary['unflagged_rows'])
    print('Flags:', summary['total_flags'], '(NOT confirmed errors)')
    print('QA outputs:', out)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
