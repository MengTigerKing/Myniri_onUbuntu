#!/usr/bin/env python3
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import tarfile
import tempfile
import time


ROOT = Path(__file__).resolve().parents[1]


def run(arguments, **options):
    subprocess.run(arguments, check=True, **options)


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def packages():
    names = set()
    for filename in ('desktop-apt.txt', 'runtime-apt.txt'):
        for line in (ROOT / 'manifests' / filename).read_text().splitlines():
            if line and not line.startswith('#'):
                names.add(line)
    return sorted(names)


def prepare(stage, home):
    with tarfile.open(ROOT / 'artifacts/ubuntu24.04-x86_64-runtime.tar.gz') as archive:
        archive.extractall(stage, filter='data')
    target = stage / 'home'
    shutil.copytree(ROOT / 'home', target, dirs_exist_ok=True)
    shutil.copytree(ROOT / 'sources/clavis', target / 'Applications/clavis-source', dirs_exist_ok=True)
    shutil.copytree(ROOT / 'sources/key-cli', target / 'Applications/key-cli', dirs_exist_ok=True)
    for template in (ROOT / 'home').rglob('*'):
        if not template.is_file():
            continue
        output = target / template.relative_to(ROOT / 'home')
        try:
            content = template.read_text()
        except UnicodeError:
            continue
        output.write_text(content.replace('@HOME@', str(home)))
    for name in ('kitty', 'kitten'):
        link = target / '.local/bin' / name
        link.symlink_to('../kitty.app/bin/' + name)
    icon = target / '.local/share/icons/hicolor/256x256/apps/kitty.png'
    icon.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(target / '.local/kitty.app/share/icons/hicolor/256x256/apps/kitty.png', icon)
    link = target / '.config/quickshell/clavis'
    link.parent.mkdir(parents=True, exist_ok=True)
    link.symlink_to('../../Applications/clavis-source')
    for path in (target / '.local/bin').iterdir():
        if not path.is_symlink():
            path.chmod(0o755)
    for path in (target / 'Applications/clavis/bin').iterdir():
        path.chmod(0o755)
    return target


def install_home(source, home, backup):
    def save(path):
        destination = backup / path.relative_to(home)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(path), str(destination))

    for directory, directories, filenames in os.walk(source, followlinks=False):
        origin = Path(directory)
        destination = home / origin.relative_to(source)
        if destination.is_symlink() or (destination.exists() and not destination.is_dir()):
            save(destination)
        destination.mkdir(parents=True, exist_ok=True)
        for name in directories + filenames:
            input_path = origin / name
            output_path = destination / name
            if input_path.is_dir() and not input_path.is_symlink():
                continue
            if output_path.exists() or output_path.is_symlink():
                if not output_path.is_symlink() and output_path.is_file() and not input_path.is_symlink():
                    if digest(input_path) == digest(output_path):
                        continue
                save(output_path)
            if input_path.is_symlink():
                output_path.symlink_to(os.readlink(input_path))
            else:
                shutil.copy2(input_path, output_path)


def main():
    parser = argparse.ArgumentParser(description='Deploy the Ubuntu 24.04 desktop snapshot. Default: check only.')
    parser.add_argument('--apply', action='store_true', help='Install user files and enable the Niri shell service')
    parser.add_argument('--install-deps', action='store_true', help='With --apply: install APT dependencies using sudo')
    parser.add_argument('--system', action='store_true', help='With --apply: install compositor and login session using sudo')
    parser.add_argument('--stage', type=Path, help='Extract into a new directory; do not change the current desktop')
    args = parser.parse_args()
    if os.geteuid() == 0:
        parser.error('Run as your normal desktop user, not sudo. Only system operations invoke sudo.')
    if args.stage and args.apply:
        parser.error('--stage and --apply are mutually exclusive')
    if (args.install_deps or args.system) and not args.apply:
        parser.error('--install-deps and --system require --apply')
    release = platform.freedesktop_os_release()
    if release.get('ID') != 'ubuntu' or release.get('VERSION_ID') != '24.04' or platform.machine() != 'x86_64':
        parser.error('This runtime supports Ubuntu 24.04 x86_64 only.')
    manifest = json.loads((ROOT / 'manifests/runtime.json').read_text())
    archive = ROOT / 'artifacts' / manifest['file']
    if not archive.is_file():
        parser.error('Missing runtime archive. Copy the matching Release asset into artifacts/. See README.md.')
    if digest(archive) != manifest['sha256']:
        parser.error('Runtime SHA-256 mismatch; deployment stopped.')
    print('Runtime checksum and platform verified.', flush=True)
    if not (ROOT / 'sources/clavis/scripts/install/arch.py').is_file():
        parser.error('Incomplete Clavis source snapshot.')
    missing = []
    for package in packages():
        result = subprocess.run(['dpkg-query', '-W', '-f=${db:Status-Status}', package], capture_output=True, text=True)
        if result.returncode or result.stdout != 'installed':
            missing.append(package)
    print('Missing APT dependencies:', ', '.join(missing) if missing else 'none', flush=True)
    if args.stage:
        stage = args.stage.resolve()
        stage.mkdir(parents=True, exist_ok=False)
        prepare(stage, stage / 'home')
        print('Staged for inspection:', stage)
        return
    if not args.apply:
        print('Check only. To deploy: python3 scripts/deploy.py --apply --install-deps --system')
        return
    if missing and not args.install_deps:
        parser.error('Dependencies missing. Add --install-deps.')
    if args.install_deps or args.system:
        run(['sudo', '-v'])
    if args.install_deps:
        run(['sudo', 'apt-get', 'update'])
        run(['sudo', 'apt-get', 'install', '--no-remove', '-y', *packages()])
    home = Path.home()
    backup = home / '.local/share/myniri-backups' / time.strftime('%Y%m%d-%H%M%S')
    with tempfile.TemporaryDirectory(prefix='myniri-deploy-') as temporary:
        stage = Path(temporary)
        prepared = prepare(stage, home)
        run([str(stage / 'system/usr/local/bin/niri'), 'validate', '-c', str(prepared / '.config/niri/config.kdl')])
        if args.system:
            for source in sorted((stage / 'system').rglob('*')):
                if not source.is_file():
                    continue
                relative = source.relative_to(stage / 'system')
                destination = Path('/') / relative
                if destination.exists():
                    saved = backup / 'system' / relative
                    run(['sudo', 'install', '-D', '-m', '0644', str(destination), str(saved)])
                mode = '0755' if '/bin/' in str(source) else '0644'
                run(['sudo', 'install', '-D', '-m', mode, str(source), str(destination)])
        install_home(prepared, home, backup)
    bashrc = home / '.bashrc'
    line = '[ -f "$HOME/.config/myniri/bash.sh" ] && source "$HOME/.config/myniri/bash.sh"'
    content = bashrc.read_text() if bashrc.exists() else ''
    if line not in content:
        backup.mkdir(parents=True, exist_ok=True)
        if bashrc.exists():
            shutil.copy2(bashrc, backup / '.bashrc')
        bashrc.write_text(content + '\n' + line + '\n')
    for directory in ('Pictures/Screenshots', 'Videos/Recordings'):
        (home / directory).mkdir(parents=True, exist_ok=True)
    run(['fc-cache', '-f'])
    run(['systemctl', '--user', 'daemon-reload'])
    run(['systemctl', '--user', 'enable', 'clavis-shell.service'])
    run(['systemctl', '--user', 'enable', 'clavis-bluetooth-agent.service'])
    run(['systemctl', '--user', 'add-wants', 'niri.service', 'niri-polkit.service'])
    for service in ('niri-waybar.service', 'niri-mako.service', 'niri-background.service', 'niri-idle.service'):
        subprocess.run(['systemctl', '--user', 'disable', service], check=False, capture_output=True)
    print('Installed. Existing files backed up to:', backup)
    print('Save your work, log out, then select Niri at the login screen. No session was restarted.')
    print('Set your own keyring/API credentials in the new session; credentials are not bundled.')


if __name__ == '__main__':
    main()
