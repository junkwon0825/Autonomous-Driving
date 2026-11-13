"""Extract and validate the Kaggle archive, then create sequence-grouped manifests."""

import argparse
import csv
import json
import random
import shutil
import zipfile
from collections import Counter
from pathlib import Path, PurePosixPath

import numpy as np
from PIL import Image

from lane_segmentation.data import validate_split


TRAIN_FRAMES = "train/train/frames/"
TRAIN_MASKS = "train/train/lane-masks/"
TEST_FRAMES = "test/test/frames/"
SAMPLE_SUBMISSION = "sample_submission.csv"


def _safe_destination(root, member):
    path = PurePosixPath(member)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"Unsafe archive member path: {member}")
    destination = (root / Path(*path.parts)).resolve()
    if not destination.is_relative_to(root.resolve()):
        raise ValueError(f"Archive member escapes the output directory: {member}")
    return destination


def _sequence_group(filename):
    prefix = Path(filename).stem.split("_", 1)[0]
    return prefix.split("-", 1)[0]


def _write_manifest(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=("image", "mask", "sequence_id"), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def prepare_data(archive_path, data_root, processed_root, seed=42):
    archive_path = Path(archive_path).resolve()
    data_root = Path(data_root).resolve()
    processed_root = Path(processed_root).resolve()
    if not archive_path.is_file():
        raise FileNotFoundError(f"Kaggle archive not found: {archive_path}")
    data_root.mkdir(parents=True, exist_ok=True)

    prefixes = (TRAIN_FRAMES, TRAIN_MASKS, TEST_FRAMES)
    with zipfile.ZipFile(archive_path) as archive:
        for info in archive.infolist():
            member = info.filename
            if info.is_dir() or not (member == SAMPLE_SUBMISSION or member.startswith(prefixes)):
                continue
            destination = _safe_destination(data_root, member)
            destination.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(info) as source, destination.open("wb") as target:
                shutil.copyfileobj(source, target)

    frame_dir = data_root / TRAIN_FRAMES.rstrip("/")
    mask_dir = data_root / TRAIN_MASKS.rstrip("/")
    test_dir = data_root / TEST_FRAMES.rstrip("/")
    if not frame_dir.is_dir() or not mask_dir.is_dir() or not test_dir.is_dir():
        raise ValueError("Archive is missing an expected train frame, lane-mask, or test frame directory")

    frames = {path.name: path for path in frame_dir.glob("*.jpg")}
    masks = {path.name: path for path in mask_dir.glob("*.jpg")}
    if not frames or frames.keys() != masks.keys():
        missing_masks = sorted(frames.keys() - masks.keys())[:5]
        missing_frames = sorted(masks.keys() - frames.keys())[:5]
        raise ValueError(f"Train image/mask filenames do not match; missing masks={missing_masks}, missing images={missing_frames}")

    rows = []
    mask_values = set()
    foreground_pixels = 0
    total_pixels = 0
    image_sizes = Counter()
    mask_sizes = Counter()
    for filename in sorted(frames):
        image_path = frames[filename]
        mask_path = masks[filename]
        with Image.open(image_path) as image:
            image.load()
            image_sizes[image.size] += 1
        with Image.open(mask_path) as mask:
            mask.load()
            mask_sizes[mask.size] += 1
            grayscale = np.asarray(mask.convert("L"), dtype=np.uint8)
        if image.size != mask.size:
            raise ValueError(f"Image/mask size mismatch for {filename}: {image.size} != {mask.size}")
        mask_values.update(np.unique(grayscale).tolist())
        foreground_pixels += int(np.count_nonzero(grayscale > 127))
        total_pixels += grayscale.size
        rows.append(
            {
                "image": image_path.relative_to(data_root).as_posix(),
                "mask": mask_path.relative_to(data_root).as_posix(),
                "sequence_id": _sequence_group(filename),
            }
        )

    groups = sorted({row["sequence_id"] for row in rows})
    if len(groups) < 2:
        raise ValueError(f"At least two sequence groups are required for validation, found {groups}")
    validation_group = random.Random(seed).choice(groups)
    train_rows = [row for row in rows if row["sequence_id"] != validation_group]
    val_rows = [row for row in rows if row["sequence_id"] == validation_group]
    _write_manifest(processed_root / "train.csv", train_rows)
    _write_manifest(processed_root / "val.csv", val_rows)
    _write_manifest(processed_root / "train_smoke.csv", train_rows[:8])
    _write_manifest(processed_root / "val_smoke.csv", val_rows[:8])
    validate_split(processed_root / "train.csv", processed_root / "val.csv")

    test_images = sorted(test_dir.glob("*.jpg"))
    if not test_images:
        raise ValueError(f"No test JPEG images found in {test_dir}")
    sample_path = data_root / SAMPLE_SUBMISSION
    if not sample_path.is_file():
        raise ValueError(f"Sample submission not found: {sample_path}")

    report = {
        "archive": archive_path.name,
        "archive_bytes": archive_path.stat().st_size,
        "train_images": len(train_rows),
        "validation_images": len(val_rows),
        "test_images": len(test_images),
        "sequence_groups": {group: sum(row["sequence_id"] == group for row in rows) for group in groups},
        "validation_group": validation_group,
        "image_sizes": {f"{width}x{height}": count for (width, height), count in image_sizes.items()},
        "mask_sizes": {f"{width}x{height}": count for (width, height), count in mask_sizes.items()},
        "mask_grayscale_values": sorted(mask_values),
        "mask_threshold": 127,
        "foreground_fraction": foreground_pixels / total_pixels,
        "sample_submission": sample_path.relative_to(data_root).as_posix(),
    }
    report_path = processed_root / "dataset_report.json"
    with report_path.open("w", encoding="utf-8") as file:
        json.dump(report, file, indent=2)
    print(json.dumps(report, indent=2))
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", default="data/lanesegmentationchallenge.zip")
    parser.add_argument("--data-root", default="data/raw/lanesegmentationchallenge")
    parser.add_argument("--processed-root", default="data/processed")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    prepare_data(args.archive, args.data_root, args.processed_root, args.seed)


if __name__ == "__main__":
    main()
