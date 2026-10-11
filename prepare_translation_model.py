"""One-time public EN->TR Argos model acquisition. No API key or hosted inference.

Use --package-path path/to/file.argosmodel for fully local installation,
or --download-public to fetch an open model from the Argos package index.
No network access is performed without --download-public.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path


def prepare(package_path: Path, out: Path):
    import argostranslate.package as pkg
    package_path = package_path.resolve()
    if package_path.suffix != '.argosmodel' or not package_path.is_file():
        raise ValueError('Mevcut .argosmodel paketi gerekiyor')
    blob = package_path.read_bytes()
    digest = hashlib.sha256(blob).hexdigest()
    # Explicit local install, no remote inference.
    pkg.install_from_path(package_path)
    matches = [p for p in pkg.get_installed_packages() if p.from_code == 'en' and p.to_code == 'tr']
    if len(matches) != 1:
        raise RuntimeError('Yüklenmiş doğrudan EN->TR paketi doğrulanamadı')
    m = matches[0]
    out.parent.mkdir(parents=True, exist_ok=True)
    data = {'source_code': 'en', 'target_code': 'tr', 'package_sha256': digest,
            'package_version': str(getattr(m, 'package_version', 'unknown')),
            'package_name': str(getattr(m, 'package_name', 'unknown')),
            'origin': 'local-package', 'model_file': package_path.name}
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    print('Installed direct EN->TR model; SHA-256:', digest)
    print('Manifest:', out)


def main():
    p = argparse.ArgumentParser()
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument('--package-path', type=Path)
    g.add_argument('--download-public', action='store_true')
    p.add_argument('--out', type=Path, default=Path('models/argos_en_tr_manifest.json'))
    args = p.parse_args()
    if args.download_public:
        import argostranslate.package as pkg
        pkg.update_package_index()  # Explicit download mode only.
        candidates = [v for v in pkg.get_available_packages() if v.from_code == 'en' and v.to_code == 'tr']
        if not candidates:
            raise RuntimeError('Argos paket dizininde doğrudan en->tr modeli yok; alternatif bir doğrudan model dosyası sağla.')
        candidates.sort(key=lambda v: str(v.package_version), reverse=True)
        package_path = Path(candidates[0].download())
    else:
        package_path = args.package_path
    prepare(package_path, args.out)


if __name__ == '__main__':
    main()
