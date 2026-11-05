#!/usr/bin/env python3
"""Synchronize client cursor settings with the compositor's selected cursor."""
import json
import shutil
import subprocess
import sys


def sync(theme, size):
    size = int(size)
    if not 12 <= size <= 128 or any(char in theme for char in '\n\r\0'):
        raise ValueError('Invalid cursor theme or size')
    if shutil.which('gsettings'):
        settings = [('cursor-size', str(size))]
        if theme:
            settings.append(('cursor-theme', json.dumps(theme, ensure_ascii=False)))
        for key, value in settings:
            subprocess.run(['gsettings', 'set', 'org.gnome.desktop.interface', key, value],
                           check=True, timeout=5)
    if shutil.which('systemctl'):
        values = [f'XCURSOR_SIZE={size}']
        if theme:
            values.append(f'XCURSOR_THEME={theme}')
        subprocess.run(['systemctl', '--user', 'set-environment', *values], check=True, timeout=5)


if __name__ == '__main__':
    try:
        sync(*sys.argv[1:])
    except (ValueError, TypeError, OSError, subprocess.SubprocessError) as error:
        print(error, file=sys.stderr)
        sys.exit(1)
