"""Build a Kaggle submission CSV from test images and a trained checkpoint."""

import argparse
import csv
from pathlib import Path

import numpy as np
import yaml

from lane_segmentation.evaluate import load_checkpoint
from lane_segmentation.inference import predict_image
from lane_segmentation.train import select_device


def encode_rle(mask, order, index_base):
    if order not in ("C", "F"):
        raise ValueError("RLE order must be 'C' (row-major) or 'F' (column-major)")
    if index_base not in (0, 1):
        raise ValueError("RLE index base must be 0 or 1")
    if mask.ndim != 2:
        raise ValueError(f"Expected a 2D binary mask, got shape {mask.shape}")

    flattened = (mask > 0).ravel(order=order)
    if not flattened.any():
        return "0"
    transitions = flattened.astype("int8")
    transitions = np.diff(np.pad(transitions, (1, 1)))
    starts = np.flatnonzero(transitions == 1)
    ends = np.flatnonzero(transitions == -1)
    lengths = ends - starts
    starts = starts + index_base
    return " ".join(str(value) for pair in zip(starts.tolist(), lengths.tolist()) for value in pair)


def _read_template(template_path):
    with Path(template_path).open("r", newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        if reader.fieldnames != ["filename", "rle_mask"]:
            raise ValueError(
                f"Expected sample submission columns ['filename', 'rle_mask'], got {reader.fieldnames}"
            )
        rows = list(reader)
    if not rows or any(not row["filename"] for row in rows):
        raise ValueError("Sample submission must contain at least one row with a filename")
    if len({row["filename"] for row in rows}) != len(rows):
        raise ValueError("Sample submission contains duplicate filenames")
    return rows


def generate_submission(
    model,
    sample_submission,
    test_root,
    output_path,
    image_size,
    threshold,
    device,
    rle_order,
    index_base,
):
    rows = _read_template(sample_submission)
    test_root = Path(test_root).resolve()
    predictions = []
    for row in rows:
        image_path = (test_root / row["filename"]).resolve()
        if not image_path.is_relative_to(test_root):
            raise ValueError(f"Test filename escapes the test image directory: {row['filename']}")
        if not image_path.is_file():
            raise FileNotFoundError(f"Test image listed in sample submission was not found: {image_path}")
        mask = predict_image(
            model,
            image_path,
            image_size=image_size,
            threshold=threshold,
            device=device,
        )
        row["rle_mask"] = encode_rle(mask, rle_order, index_base)
        predictions.append(row)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=("filename", "rle_mask"), lineterminator="\n")
        writer.writeheader()
        writer.writerows(predictions)
    return output_path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/baseline.yaml")
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--sample-submission", required=True)
    parser.add_argument("--test-root", required=True)
    parser.add_argument("--output", default="data/submissions/submission.csv")
    parser.add_argument("--rle-order", choices=("C", "F"), required=True)
    parser.add_argument("--index-base", type=int, choices=(0, 1), required=True)
    args = parser.parse_args()

    config_path = Path(args.config).resolve()
    project_dir = config_path.parent.parent
    with config_path.open("r", encoding="utf-8") as file:
        config = yaml.safe_load(file)
    resolve = lambda value: (project_dir / value).resolve()
    device = select_device(config.get("device", "auto"))
    model, _ = load_checkpoint(args.checkpoint, device)
    output_path = generate_submission(
        model=model,
        sample_submission=args.sample_submission,
        test_root=args.test_root,
        output_path=resolve(args.output) if not Path(args.output).is_absolute() else args.output,
        image_size=tuple(config["image_size"]),
        threshold=float(config["threshold"]),
        device=device,
        rle_order=args.rle_order,
        index_base=args.index_base,
    )
    print(f"Submission saved: {output_path}")


if __name__ == "__main__":
    main()
