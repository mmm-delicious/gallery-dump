# Photo Curation Scripts

Smart photo curation tools for selecting and optimizing the best images from large photo sets.

## Overview

This toolkit helps curate large photo collections (hundreds or thousands of photos) by:
- **Detecting and removing duplicate burst sequences** (photographers often shoot 10+ identical frames)
- **Prioritizing people-focused images** (face detection to count faces per image)
- **Filtering empty-space photos** (composition analysis to avoid sparse images)
- **Optimizing for web** (resize, compress, maintain quality)

## Scripts

### 1. `resize_photos.py`
Batch resize all photos to a manageable size (max 1920px) before curation analysis.

**Why separate steps?** Processing large original files for face detection is very slow. Resizing first makes the curation script 10x+ faster.

**Usage:**
```bash
python3 resize_photos.py <source_dir> <output_dir> [max_size] [quality]
```

**Arguments:**
- `source_dir` — folder containing photos (searches subdirectories recursively)
- `output_dir` — where to save resized copies
- `max_size` — max pixels on longest side (default: 1920)
- `quality` — JPEG quality 1-100 (default: 90)

**Examples:**
```bash
python3 resize_photos.py ~/Downloads/MyEvent ~/tmp/MyEvent_work
python3 resize_photos.py ~/Photos/Wedding ~/tmp/wedding_work 2560 85
```

**Output:** Resized JPGs in output directory

---

### 2. `curate_fast.py`
Smart curation: evaluates all photos, scores by quality/faces/composition, selects best, prevents duplicates.

**Features:**
- **Face detection** (OpenCV cascade classifier) — counts faces in center region of image
- **Duplicate prevention** — uses perceptual hashing to skip burst sequences
- **Composition scoring** — analyzes brightness variation
- **Quality scoring** — combines resolution, faces, composition, aspect ratio
- **Configurable weights** — adjust how much weight face detection gets

**Usage:**
```bash
python3 curate_fast.py <input_dir> <output_dir> [count] [face_weight]
```

**Arguments:**
- `input_dir` — folder with resized photos (from resize_photos.py)
- `output_dir` — destination for curated gallery
- `count` — number of images to select (default: 170)
- `face_weight` — weight for face detection 0.0-1.0 (default: 0.45)

**Examples:**
```bash
python3 curate_fast.py ~/tmp/wedding_work ~/Gallery/wedding_final 200
python3 curate_fast.py ~/tmp/photos ~/final_gallery 150 0.5
```

**Output:** Selected images copied to output directory

**Scoring Formula:**
```
quality = (resolution_score × 0.2) + (face_score × 0.45) + (composition × 0.25) + (aspect_ratio × 0.1)
```

The high weight on face_score (45%) prioritizes people-focused images.

---

## Typical Workflow

```bash
# Step 1: Resize all originals (does NOT delete originals)
python3 resize_photos.py

# Step 2: Curate on resized versions (fast, with face detection)
python3 curate_fast.py

# Result: /path/to/Gallery_Curated/ contains selected images
```

## Requirements

```bash
pip install pillow opencv-python numpy
```

## Key Decisions

- **Why face detection?** Counts visible faces per image, heavily weighs crowd shots (3+ faces) over isolated people.
- **Why perceptual hashing?** Detects near-identical burst sequences; photographers often shoot 8-10 frames of the same moment.
- **Why composition analysis?** Brightness variation is a proxy for crowds vs. empty space—varied brightness suggests multiple subjects, uniform brightness suggests empty areas.
- **Why resize first?** Face detection on full-resolution photos (4000×6000px) is slow; resized versions are 50-100× faster.

## Customization

Adjust the scoring weights in `curate_fast.py` for different priorities:
- Increase `face_score` weight to prioritize crowd shots
- Increase `composition` weight to avoid sparse images
- Increase `res_score` weight to prioritize high-resolution originals
- Adjust `target_count` to select more/fewer images

## Performance

On a typical laptop:
- **Resize 774 photos:** ~2-3 minutes
- **Curate 774 resized photos:** ~5-10 minutes (depends on face detection speed)

Total: 10-15 minutes for full workflow on 700+ photos.
