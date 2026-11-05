#!/usr/bin/env python3
"""Add HiDPI raster sizes to a user copy of an installed Xcursor theme."""
import argparse
from pathlib import Path
import shutil
import struct

from PIL import Image


IMAGE_TYPE = 0xFFFD0002


def expand(data):
    magic, header, version, count = struct.unpack_from('<4I', data)
    if magic != 0x72756358:
        raise ValueError('Not an Xcursor file')
    entries = [struct.unpack_from('<3I', data, header + index * 12) for index in range(count)]
    sizes = {size for kind, size, offset in entries if kind == IMAGE_TYPE}
    largest = max(sizes)
    additions = []
    for kind, size, offset in entries:
        if kind != IMAGE_TYPE or size != largest:
            continue
        chunk_header, _, _, chunk_version, width, height, xhot, yhot, delay = struct.unpack_from('<9I', data, offset)
        pixels = data[offset + chunk_header:offset + chunk_header + width * height * 4]
        rgba = Image.frombytes('RGBA', (width, height), pixels, 'raw', 'BGRA')
        source = Image.frombytes('RGBa', (width, height), rgba.tobytes())
        for target_size in (64, 72, 96, 128, 192, 256):
            if target_size in sizes or target_size <= largest:
                continue
            ratio = target_size / size
            target_width = round(width * ratio)
            target_height = round(height * ratio)
            resized = source.resize((target_width, target_height), Image.Resampling.LANCZOS)
            pixels = Image.frombytes('RGBA', resized.size, resized.tobytes()).tobytes('raw', 'BGRA')
            chunk = struct.pack('<9I', 36, IMAGE_TYPE, target_size, chunk_version,
                                target_width, target_height, round(xhot * ratio), round(yhot * ratio), delay)
            additions.append((target_size, chunk + pixels))
    if not additions:
        return data
    table_end = header + count * 12
    shift = len(additions) * 12
    table = b''.join(struct.pack('<3I', kind, size, offset + shift) for kind, size, offset in entries)
    position = len(data) + shift
    chunks = []
    for size, chunk in additions:
        table += struct.pack('<3I', IMAGE_TYPE, size, position)
        chunks.append(chunk)
        position += len(chunk)
    return (struct.pack('<4I', magic, header, version, count + len(additions))
            + data[16:header] + table + data[table_end:] + b''.join(chunks))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('destination', type=Path)
    args = parser.parse_args()
    if args.destination.exists():
        parser.error('Destination must not exist')
    shutil.copytree(args.source, args.destination, symlinks=True)
    for cursor in (args.destination / 'cursors').iterdir():
        if cursor.is_file() and not cursor.is_symlink():
            cursor.write_bytes(expand(cursor.read_bytes()))


if __name__ == '__main__':
    main()
