"""Optionally download a PUBLIC small encoder for local use. No auth, no inference API.

Running this script is a one-time public artifact download over HTTPS.
All future feature extraction is offline (`local_files_only=True`).
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

REPOSITORY = 'sentence-transformers/all-MiniLM-L6-v2'


def download(target: Path, revision: str = 'main'):
    try:
        from huggingface_hub import snapshot_download
    except ImportError as exc:
        raise RuntimeError('Önce pip install -r requirements-semantic.txt') from exc
    target.mkdir(parents=True, exist_ok=True)
    snapshot_download(repo_id=REPOSITORY, revision=revision, local_dir=str(target),
                      token=False, ignore_patterns=['*.onnx', '*.h5', '*.ot', '*.msgpack', '*.tflite', '*.openvino'])
    if not (target / 'modules.json').exists():
        raise RuntimeError('Model indirmesi eksik: modules.json bulunamadı')
    (target / 'download_source.json').write_text(json.dumps({'repository': REPOSITORY,
       'requested_revision': revision, 'authentication': 'none', 'use': 'local frozen encoder only'}, indent=2), encoding='utf-8')
    return target


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out', type=Path, default=Path('models/local_encoder'))
    p.add_argument('--revision', default='main', help='Hedef proje için mümkünse sabit commit SHA kullan')
    a = p.parse_args()
    print('Downloaded public model to:', download(a.out, a.revision))
