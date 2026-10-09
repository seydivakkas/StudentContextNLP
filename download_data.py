"""Download *public dataset files* (not AI/LLM APIs), without API keys.

python download_data.py --data-dir data/raw
The transfer needs Internet once; afterward training and inference are offline.
"""
import argparse
import hashlib
import json
import time
import urllib.error
import urllib.request
from pathlib import Path

FILES = ('train-00001.parquet', 'test-ua-00001.parquet',
         'test-uq-00001.parquet', 'test-ud-00001.parquet')
REVISION = 'a8edbd1bd2b3128a6c400a85040d17ad46a6dd42'
BASE = 'https://huggingface.co/datasets/nkazi/SciEntsBank/resolve/{revision}/data/{name}?download=true'


def download(data_dir: Path, revision: str = REVISION) -> list[dict]:
    data_dir.mkdir(parents=True, exist_ok=True)
    manifest = []
    for name in FILES:
        dest = data_dir / name
        url = BASE.format(revision=revision, name=name)
        if not dest.exists():
            tmp = dest.with_name(dest.name + '.part')
            for attempt in range(3):
                try:
                    req = urllib.request.Request(url, headers={'User-Agent': 'StudentContextNLP/0.1 data-download'})
                    with urllib.request.urlopen(req, timeout=60) as resp, tmp.open('wb') as out:
                        while True:
                            chunk = resp.read(1024 * 128)
                            if not chunk:
                                break
                            out.write(chunk)
                    if tmp.stat().st_size < 100 or tmp.read_bytes()[:4] != b'PAR1':
                        raise ValueError(f'{name} geçerli Parquet dosyası gibi görünmüyor')
                    tmp.replace(dest)
                    break
                except Exception as exc:
                    tmp.unlink(missing_ok=True)
                    if attempt == 2:
                        raise RuntimeError(f'{name} indirilemedi. Tarayıcıdan manuel indirmeyi dene: {url} ({exc})') from exc
                    time.sleep(attempt + 1)
        data = dest.read_bytes()
        if data[:4] != b'PAR1' or data[-4:] != b'PAR1':
            raise ValueError(f'{name} geçerli Parquet değil')
        manifest.append({'filename': name, 'source': url, 'bytes': len(data),
                         'sha256': hashlib.sha256(data).hexdigest()})
        print(f'OK {name}: {len(data)} bytes')
    (data_dir / 'file_manifest.json').write_text(
        json.dumps({'dataset': 'nkazi/SciEntsBank', 'revision': revision, 'files': manifest}, indent=2),
        encoding='utf-8')
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--data-dir', type=Path, default=Path('data/raw'))
    parser.add_argument('--revision', default=REVISION, help='Hugging Face git commit SHA (sabitlenmiş varsayılan)')
    args = parser.parse_args()
    download(args.data_dir, args.revision)
