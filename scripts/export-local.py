#!/usr/bin/env python3
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tarfile


ROOT = Path(__file__).resolve().parents[1]
HOME = Path.home()
OMIT = shutil.ignore_patterns('.git', '__pycache__', '*.pyc', '.venv', 'target',
                              'build', 'build610', 'build610b', 'cache.d', 'run')


def copy(source, target):
    target.parent.mkdir(parents=True, exist_ok=True)
    if source.is_dir():
        shutil.copytree(source, target, ignore=OMIT, dirs_exist_ok=True, ignore_dangling_symlinks=True)
    else:
        shutil.copy2(source, target)


def normalize(path):
    try:
        content = path.read_text()
    except (UnicodeError, IsADirectoryError):
        return
    path.write_text(content.replace(str(HOME), '@HOME@'))


def snapshot(source, name, manifests):
    target = ROOT / 'sources' / name
    if target.exists():
        shutil.rmtree(target)
    if (source / '.git').exists():
        paths = subprocess.check_output(
            ['git', '-C', str(source), 'ls-files', '-z', '--cached', '--others', '--exclude-standard']
        ).decode().split('\0')
        for relative in paths:
            if not relative or any(part in ('.venv', '__pycache__', 'build610', 'build610b', 'install610') for part in Path(relative).parts):
                continue
            if name == 'quickshell' and Path(relative).parts[0] == 'install':
                continue
            origin = source / relative
            if origin.is_file():
                copy(origin, target / relative)
        revision = subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip()
        remote = subprocess.check_output(['git', '-C', str(source), 'remote', 'get-url', 'origin'], text=True).strip()
        changes = subprocess.check_output(['git', '-C', str(source), 'diff', 'HEAD', '--binary'])
        if changes:
            (ROOT / 'manifests' / (name + '.patch')).write_bytes(changes)
        manifests[name] = {'revision': revision, 'upstream': remote, 'workingTreeIncluded': True}
    else:
        copy(source, target)
        manifests[name] = {'sourceDirectory': source.name, 'workingTreeIncluded': True}


def main():
    parser = argparse.ArgumentParser(description='Export this configured Ubuntu host; not a generic installer.')
    parser.add_argument('--clavis-source', required=True, type=Path)
    args = parser.parse_args()
    if (ROOT / 'manifests/runtime.json').exists():
        raise SystemExit('Snapshot already exists. Export into a fresh copy to avoid stale files.')
    (ROOT / 'manifests').mkdir(exist_ok=True)
    sources = {}
    for source, name in (
        (args.clavis_source, 'clavis'),
        (HOME / 'Applications/key-cli', 'key-cli'),
        (HOME / 'Applications/quickshell-0.3.1', 'quickshell'),
        (HOME / 'Applications/niri-trial/niri-26.04', 'niri'),
        (HOME / 'Applications/niri-trial/xwayland-satellite-0.8.3', 'xwayland-satellite'),
    ):
        snapshot(source, name, sources)
    (ROOT / 'manifests/sources.json').write_text(json.dumps(sources, indent=2) + '\n')
    config_paths = [
        '.config/niri/config.kdl', '.config/niri/clavis',
        '.config/clavis/config.json', '.config/clavis/dock.json',
        '.config/clavis/quick-toggles.json', '.config/clavis/idle-policy.json',
        '.config/clavis/ui-preferences.json', '.config/clavis/matugen',
        '.config/kitty/kitty.conf', '.config/kitty/current-theme.conf', '.config/kitty/themes',
        '.config/blesh/init.sh', '.config/neofetch/clavis.conf', '.config/starship.toml',
        '.config/fcitx5/config', '.config/fcitx5/profile',
        '.config/fcitx5/conf/pinyin.conf', '.config/fcitx5/conf/classicui.conf',
        '.config/systemd/user/clavis-shell.service',
        '.config/systemd/user/clavis-shell.service.d', '.config/systemd/user/niri-polkit.service',
        '.config/systemd/user/clavis-bluetooth-agent.service', '.config/autostart/blueman.desktop',
        '.local/bin/clavis-bluetooth-agent',
        '.local/bin/clavis-files', '.local/bin/clavis-reversal-icons',
        '.local/bin/clavis-chrome', '.local/share/applications/google-chrome.desktop',
        '.local/share/icons/breeze_cursors', '.icons/breeze_cursors',
        '.local/share/themes/ClavisNiri', '.local/share/clavis/reversal-icons/palette.json',
        '.local/share/applications/kitty.desktop', '.local/share/applications/kitty-open.desktop',
    ]
    for relative in config_paths:
        copy(HOME / relative, ROOT / 'home' / relative)
    for path in (ROOT / 'home').rglob('*'):
        if path.is_file():
            normalize(path)
    config_path = ROOT / 'home/.config/clavis/config.json'
    config = json.loads(config_path.read_text())
    current = json.loads((HOME / '.config/clavis/config.json').read_text())['wallpaper']
    config['wallpaper']['folder'] = '@HOME@/Pictures/Wallpapers'
    config['wallpaper']['path'] = '@HOME@/Pictures/Wallpapers/' + Path(current['path']).name
    config_path.write_text(json.dumps(config, ensure_ascii=False, indent=2) + '\n')
    stage = ROOT / '.staging'
    stage.mkdir(exist_ok=True)
    for relative in (
        'Applications/quickshell-0.3.1/install610', 'Applications/clavis610',
        'Applications/fcitx5-qt610', '.local/kitty.app', '.local/share/blesh',
        '.local/share/fonts', '.local/libexec/key-cli',
    ):
        copy(HOME / relative, stage / 'home' / relative)
    for name in ('matugen', 'starship'):
        copy(HOME / '.local/bin' / name, stage / 'home/.local/bin' / name)
    for name in ('ClavisReversal', 'ClavisReversal-Alt', 'Reversal-red-dark'):
        target = stage / 'home/.local/share/icons' / name
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(HOME / '.local/share/icons' / name, target, symlinks=True)
    copy(Path(current['folder']), stage / 'home/Pictures/Wallpapers')
    qt = Path('Applications/Qt/6.10.3/gcc_64')
    for name in ('qml', 'plugins', 'translations'):
        copy(HOME / qt / name, stage / 'home' / qt / name)
    plugins = stage / 'home' / qt / 'plugins'
    for source in (plugins / 'sqldrivers').glob('*.so'):
        if source.name != 'libqsqlite.so':
            source.unlink()
    (plugins / 'position/libqtposition_nmea.so').unlink(missing_ok=True)
    for source in (HOME / qt / 'lib').glob('*.so*'):
        copy(source, stage / 'home' / qt / 'lib' / source.name)
    for dependency in ('qtkeychain', 'libcava', 'iniparser', 'wayland125', 'm3shapes'):
        base = Path('Applications/deps') / dependency
        for directory in ('lib', 'lib64'):
            origin = HOME / base / directory
            if not origin.exists():
                continue
            for source in origin.glob('*.so*'):
                copy(source, stage / 'home' / base / directory / source.name)
        qml = HOME / base / 'lib/qt6/qml'
        if qml.exists():
            copy(qml, stage / 'home' / base / 'lib/qt6/qml')
    system_paths = [
        '/usr/local/bin/niri', '/usr/local/bin/niri-session', '/usr/local/bin/xwayland-satellite',
        '/etc/systemd/user/niri.service', '/etc/systemd/user/niri-shutdown.target',
        '/usr/share/wayland-sessions/niri.desktop', '/usr/share/xdg-desktop-portal/niri-portals.conf',
    ]
    for absolute in system_paths:
        copy(Path(absolute), stage / 'system' / absolute.lstrip('/'))
    local_niri = HOME / '.local/libexec/niri/niri'
    if local_niri.is_file():
        copy(local_niri, stage / 'system/usr/local/bin/niri')
    for name in ('clavis-shell', 'qs'):
        relative = Path('Applications/clavis/bin') / name
        copy(HOME / relative, ROOT / 'home' / relative)
        normalize(ROOT / 'home' / relative)
    for name in ('qs', 'key-sysmon'):
        relative = Path('.local/bin') / name
        copy(HOME / relative, ROOT / 'home' / relative)
        normalize(ROOT / 'home' / relative)
    environment = dict(os.environ)
    libraries = [str(stage / 'home' / qt / 'lib')]
    libraries += [str(path) for path in (stage / 'home/Applications/deps').glob('*/lib*')]
    libraries += [str(path.parent) for path in (stage / 'home/Applications/clavis610').rglob('*.so')]
    environment['LD_LIBRARY_PATH'] = ':'.join(libraries)
    system_libraries = set()
    unresolved = set()
    for path in stage.rglob('*'):
        if not path.is_file():
            continue
        with path.open('rb') as stream:
            if stream.read(4) != b'\x7fELF':
                continue
        scoped_environment = dict(environment)
        if path.is_relative_to(stage / 'home/.local/kitty.app'):
            scoped_environment['LD_LIBRARY_PATH'] = str(stage / 'home/.local/kitty.app/lib')
        result = subprocess.run(['ldd', str(path)], env=scoped_environment, capture_output=True, text=True)
        for line in result.stdout.splitlines():
            match = re.search(r'=> (/\S+)', line)
            if match and not match[1].startswith(str(stage)):
                system_libraries.add(match[1])
            if 'not found' in line:
                unresolved.add(line.strip())
    packages = set()
    for library in sorted(system_libraries):
        resolved = Path(library).resolve()
        result = subprocess.run(['dpkg-query', '-S', str(resolved)], capture_output=True, text=True)
        if result.returncode:
            result = subprocess.run(['dpkg-query', '-S', library], capture_output=True, text=True)
        for line in result.stdout.splitlines():
            packages.add(line.split(': ', 1)[0])
    (ROOT / 'manifests/runtime-apt.txt').write_text('\n'.join(sorted(packages)) + '\n')
    if unresolved:
        raise SystemExit('Unresolved runtime libraries: ' + ', '.join(sorted(unresolved)))
    artifacts = ROOT / 'artifacts'
    artifacts.mkdir(exist_ok=True)
    archive = artifacts / 'ubuntu24.04-x86_64-runtime.tar.gz'
    print('Compressing runtime and wallpapers...', flush=True)
    with tarfile.open(archive, 'w:gz', compresslevel=3) as output:
        for name in ('home', 'system'):
            output.add(stage / name, arcname=name)
    digest = hashlib.file_digest(archive.open('rb'), 'sha256').hexdigest()
    manifest = {'file': archive.name, 'sha256': digest, 'bytes': archive.stat().st_size,
                'os': 'ubuntu', 'version': '24.04', 'arch': 'x86_64',
                'versions': {'niri': '26.04', 'quickshell': '0.3.1', 'qt': '6.10.3', 'kitty': '0.49.2'}}
    if local_niri.is_file() and (ROOT / 'manifests/niri.patch').is_file():
        manifest['niriPatch'] = 'niri.patch'
    (ROOT / 'manifests/runtime.json').write_text(json.dumps(manifest, indent=2) + '\n')
    (artifacts / (archive.name + '.sha256')).write_text(digest + '  ' + archive.name + '\n')
    shutil.rmtree(stage)
    print('Export complete:', archive)


if __name__ == '__main__':
    main()
