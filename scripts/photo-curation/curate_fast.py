#!/usr/bin/env python3
"""
Smart photo curation: select best images using face detection, composition analysis, and burst prevention.

Usage:
    python3 curate_fast.py <input_dir> <output_dir> [count] [face_weight]

Arguments:
    input_dir      Path to folder with resized photos (from resize_photos.py)
    output_dir     Path to output folder for curated gallery
    count          Number of images to select (default: 170)
    face_weight    Weight for face detection 0.0-1.0 (default: 0.45)

Examples:
    python3 curate_fast.py ~/tmp/wedding_work ~/Gallery/wedding_curated 200
    python3 curate_fast.py ~/tmp/photos ~/final_gallery 150 0.5
"""

import os
import sys
from pathlib import Path
from PIL import Image
import numpy as np
import cv2

def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    input_dir = sys.argv[1]
    output_dir = sys.argv[2]
    target_count = int(sys.argv[3]) if len(sys.argv) > 3 else 170
    face_weight = float(sys.argv[4]) if len(sys.argv) > 4 else 0.45

    # Validate inputs
    input_path = Path(input_dir)
    if not input_path.is_dir():
        print(f"❌ Error: Input directory not found: {input_dir}")
        sys.exit(1)

    if face_weight < 0 or face_weight > 1:
        print(f"❌ Error: face_weight must be 0.0-1.0, got {face_weight}")
        sys.exit(1)

    work_dir = input_dir
    output_dir = output_dir

# Load face cascade
face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
)

def get_image_hash(filepath, hash_size=8):
    """Perceptual hash for duplicate detection"""
    try:
        img = Image.open(filepath)
        img = img.resize((hash_size, hash_size), Image.Resampling.LANCZOS)
        img_arr = np.array(img.convert('L'))
        avg = img_arr.mean()
        return (img_arr > avg).flatten()
    except:
        return None

def hamming_distance(h1, h2):
    if h1 is None or h2 is None:
        return 100
    return np.sum(h1 != h2)

def count_faces_fast(filepath):
    """Fast face detection - only scan center region"""
    try:
        img = cv2.imread(filepath)
        if img is None:
            return 0
        h, w = img.shape[:2]
        # Only scan center 70% of image (faster)
        y1, y2 = int(h * 0.15), int(h * 0.85)
        x1, x2 = int(w * 0.15), int(w * 0.85)
        center_roi = img[y1:y2, x1:x2]
        gray = cv2.cvtColor(center_roi, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.2, 5)
        return len(faces)
    except:
        return 0

def analyze_composition(filepath):
    """Brightness variation - crowds have more variation"""
    try:
        img = Image.open(filepath)
        arr = np.array(img)
        if len(arr.shape) == 3:
            gray = np.mean(arr, axis=2)
        else:
            gray = arr
        std = np.std(gray)
        return min(1.0, std / 50.0)
    except:
        return 0.5

def evaluate_image(filepath):
    """Score image"""
    try:
        img = Image.open(filepath)
        w, h = img.size
        res = w * h

        res_score = min(1.0, (res / 10000000) ** 0.5)
        face_count = count_faces_fast(filepath)
        face_score = min(1.0, face_count / 5.0)
        composition = analyze_composition(filepath)
        aspect = w / h
        aspect_score = 1.0 if 0.5 <= aspect <= 1.5 else 0.7

        other_weight = (1 - face_weight) / 3
        quality = (res_score * other_weight) + (face_score * face_weight) + (composition * other_weight) + (aspect_score * other_weight)

        return {
            'path': filepath,
            'filename': os.path.basename(filepath),
            'quality': quality,
            'faces': face_count,
            'comp': composition,
            'hash': get_image_hash(filepath)
        }
    except:
        return None

def is_duplicate(img, prev_imgs, threshold=10):
    """Skip similar images (burst prevention)"""
    if img['hash'] is None:
        return False
    for p in prev_imgs[-5:]:
        if p['hash'] is None:
            continue
        if hamming_distance(img['hash'], p['hash']) < threshold:
            return True
    return False

    print("🎯 Smart Photo Curation (Fast Mode)", flush=True)
    print("=" * 50, flush=True)
    print(f"Face weight: {face_weight} | Target: {target_count} images", flush=True)
    print()

    # Evaluate all images
    print("1️⃣  Evaluating images...", flush=True)
    all_imgs = []
    count = 0

    for filename in sorted(Path(work_dir).glob('*.jpg')) + sorted(Path(work_dir).glob('*.jpeg')):
        result = evaluate_image(str(filename))
        if result:
            all_imgs.append(result)
            count += 1
            if count % 50 == 0:
                print(f"  ✓ {count} evaluated", flush=True)

    if count == 0:
        print(f"❌ No images found in {work_dir}")
        sys.exit(1)

    print(f"✓ Done: {len(all_imgs)} images", flush=True)
    print()

    # Sort by quality
    all_imgs.sort(key=lambda x: x['quality'], reverse=True)

    # Select, avoiding duplicates
    print("2️⃣  Selecting best (avoiding bursts)...", flush=True)
    selected = []
    for img in all_imgs:
        if not is_duplicate(img, selected):
            selected.append(img)
        if len(selected) >= target_count:
            break

    print(f"✓ Selected {len(selected)} images", flush=True)
    if selected:
        print(f"  Quality: {selected[0]['quality']:.3f} to {selected[-1]['quality']:.3f}", flush=True)
    print()

    # Statistics
    if selected:
        faces_list = [img['faces'] for img in selected]
        print("📊 Stats:", flush=True)
        print(f"  Avg faces: {np.mean(faces_list):.1f}", flush=True)
        print(f"  3+ faces: {sum(1 for f in faces_list if f >= 3)}", flush=True)
        print(f"  1-2 faces: {sum(1 for f in faces_list if 1 <= f < 3)}", flush=True)
        print(f"  0 faces: {sum(1 for f in faces_list if f == 0)}", flush=True)
        print()

    # Copy to gallery
    print("3️⃣  Copying to gallery...", flush=True)
    import shutil
    output_path = Path(output_dir)
    if output_path.exists():
        shutil.rmtree(output_path)
    output_path.mkdir(parents=True, exist_ok=True)

    for i, img in enumerate(selected, 1):
        shutil.copy2(img['path'], output_path / img['filename'])
        if i % 50 == 0:
            print(f"  ✓ {i}/{len(selected)}", flush=True)

    print()
    print("=" * 50, flush=True)
    print(f"✨ Done! {len(selected)} images in {output_dir}", flush=True)

if __name__ == '__main__':
    main()
