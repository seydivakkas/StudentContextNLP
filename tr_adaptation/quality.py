"""Conservative translation review *flags*, never semantic correctness claims."""
import re

_NUMBER = re.compile(r"(?<!\w)\d+(?:[.,]\d+)?%?(?!\w)")
_EN_NEGATION = re.compile(r"\b(?:not|no|never|without|neither|cannot|can't|doesn't|don't|isn't|aren't|won't)\b", re.I)
_TR_NEGATION = re.compile(r"\b(?:değil|yok|hayır|asla|hiç|olmaz|olamaz|olmayan|olmuyor|olmadı|yapamaz|yapmadı)\b|\b\w+(?:mıyor|miyor|muyor|müyor|madı|medi|maz|mez)\b", re.I)


def _nums(s: str) -> list[str]:
    # Locale-agnostic numeric presence check; decimal punctuation can change.
    return sorted(x.replace(',', '.') for x in _NUMBER.findall(s))


def review_flags(source: str, target: str) -> list[str]:
    """Flags suggest review, not proof of mistranslation or preserved meaning."""
    flags = []
    source, target = (source or '').strip(), (target or '').strip()
    if source and not target:
        return ['EMPTY_TRANSLATION']
    if source and source.casefold() == target.casefold():
        flags.append('UNCHANGED_TEXT_REVIEW')
    if source and target and (len(target) / max(len(source), 1) < .25 or len(target) / len(source) > 4.0):
        flags.append('LENGTH_RATIO_REVIEW')
    if _nums(source) != _nums(target):
        flags.append('NUMBER_MISMATCH_REVIEW')
    if _EN_NEGATION.search(source) and not _TR_NEGATION.search(target):
        flags.append('NEGATION_REVIEW')
    return flags
