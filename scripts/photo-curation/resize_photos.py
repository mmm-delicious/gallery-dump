#!/usr/bin/env python3
"""
Batch resize photos to a manageable size for faster processing.

Usage:
    python3 resize_photos.py <source_dir> <output_dir> [max_size] [quality]

Arguments:
    source_dir   Path to folder with original photos (supports subdirectories)
    output_dir   Path to output folder for resized images
    max_size     Max pixel size on longest side (default: 1920)
    quality      JPEG quality 1-100 (default: 90)

Examples:
    python3 resize_photos.py ~/Downloads/MyEvent ~/tmp/MyEvent_resized
    python3 resize_photos.py ~/Photos/Wedding ~/tmp/wedding_work 2560 85
"""

import os
import sys
from pathlib import Path
from PIL import Image

def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    source_dir = sys.argv[1]
    output_dir = sys.argv[2]
    max_size = int(sys.argv[3]) if len(sys.argv) > 3 else 1920
    quality = int(sys.argv[4]) if len(sys.argv) > 4 else 90

    # Validate inputs
    source_path = Path(source_dir)
    if not source_path.is_dir():
        print(f"❌ Error: Source directory not found: {source_dir}")
        sys.exit(1)

    if quality < 1 or quality > 100:
        print(f"❌ Error: Quality must be 1-100, got {quality}")
        sys.exit(1)

    # Create output
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    print(f"📸 Resizing photos from {source_dir}")
    print(f"   Max size: {max_size}px | Quality: {quality}%")
    print()

    count = 0
    errors = 0
    supported = ('.jpg', '.jpeg', '.png', '.heic')

    # Recursively find all photos in source and subdirs
    for src_file in source_path.rglob('*'):
        if not src_file.is_file():
            continue

        if not src_file.suffix.lower() in supported:
            continue

        dst_filename = src_file.name.replace('.HEIC', '.jpg').replace('.heic', '.jpg')
        dst_path = output_path / dst_filename

        try:
            img = Image.open(src_file)
            img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
            img.save(dst_path, 'JPEG', quality=quality)
            count += 1

            if count % 100 == 0:
                print(f"  ✓ {count} photos resized...")
        except Exception as e:
            print(f"  ⚠️  {src_file.name}: {e}")
            errors += 1

    print()
    print(f"✓ Resized {count} photos")
    if errors > 0:
        print(f"⚠️  {errors} errors")
    print(f"✓ Output: {output_dir}")

if __name__ == '__main__':
    main()
