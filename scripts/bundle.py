#!/usr/bin/env python3
import hashlib
import json
from pathlib import Path
import tarfile
import tempfile


ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    manifest = json.loads((ROOT / 'manifests/runtime.json').read_text())
    runtime = ROOT / 'artifacts' / manifest['file']
    if runtime.parent != ROOT / 'artifacts' or digest(runtime) != manifest['sha256']:
        raise SystemExit('Runtime SHA-256 mismatch or invalid path; packaging stopped.')
    checksum = runtime.with_name(runtime.name + '.sha256')
    if checksum.read_text().strip() != manifest['sha256'] + '  ' + runtime.name:
        raise SystemExit('Runtime checksum file does not match the manifest.')
    entries = [ROOT / name for name in (
        '.gitignore', 'README.md', 'THIRD_PARTY.md',
        'home', 'manifests', 'scripts', 'sources',
    )] + [runtime, checksum]
    output = ROOT / 'artifacts/Myniri_onUbuntu-ubuntu24.04-x86_64-full.tar.gz'

    def include(member):
        parts = Path(member.name).parts
        if any(part in ('.git', '__pycache__', '.venv', '.staging') for part in parts):
            return None
        if member.name.endswith(('.pyc', '.pyo')):
            return None
        return member

    with tempfile.NamedTemporaryFile(dir=output.parent, suffix='.partial', delete=False) as stream:
        temporary = Path(stream.name)
    try:
        with tarfile.open(temporary, 'w:gz', compresslevel=1) as archive:
            for entry in entries:
                print('Packaging:', entry.relative_to(ROOT), flush=True)
                archive.add(entry, arcname='Myniri_onUbuntu/' + str(entry.relative_to(ROOT)), filter=include)
        checksum_value = digest(temporary)
        temporary.replace(output)
        output.with_name(output.name + '.sha256').write_text(checksum_value + '  ' + output.name + '\n')
    finally:
        temporary.unlink(missing_ok=True)
    print('Complete bundle:', output)
    print('SHA-256:', checksum_value)


if __name__ == '__main__':
    main()
