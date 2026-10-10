"""Offline Argos EN->TR translation. No network operations in this module."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def load_argos_translation():
    """Require a *direct* locally installed EN->TR package: prohibit pivoting."""
    try:
        import argostranslate.package as pkg
        import argostranslate.translate as tr
    except ImportError as exc:
        raise RuntimeError('Argos Translate kurulu değil: pip install -r requirements-translation.txt') from exc
    direct = [p for p in pkg.get_installed_packages() if p.from_code == 'en' and p.to_code == 'tr']
    if len(direct) != 1:
        raise RuntimeError('Tam olarak bir doğrudan en->tr .argosmodel paketi kurulu olmalı; önce prepare_translation_model.py çalıştır.')
    model = direct[0]
    translate = tr.get_translation_from_codes('en', 'tr')
    metadata = {'engine': 'argos-translate', 'from': 'en', 'to': 'tr',
                'package_version': str(getattr(model, 'package_version', 'unknown')),
                'package_name': str(getattr(model, 'package_name', 'unknown'))}
    # A manifest of the installed model is required for reproducible runs.
    return translate.translate, metadata


def ensure_model_manifest(manifest_path: Path, metadata: dict) -> dict:
    if not manifest_path.is_file():
        raise RuntimeError(f'Model köken manifesti eksik: {manifest_path}. Önce prepare_translation_model.py ile modeli kur.')
    d = json.loads(manifest_path.read_text(encoding='utf-8'))
    if d.get('source_code') != 'en' or d.get('target_code') != 'tr' or not d.get('package_sha256'):
        raise ValueError('Manifest en->tr ve SHA-256 bilgisi sağlamıyor')
    if str(d.get('package_version')) != metadata['package_version']:
        raise RuntimeError('Kurulu Argos model sürümü manifestle eşleşmiyor')
    return d
