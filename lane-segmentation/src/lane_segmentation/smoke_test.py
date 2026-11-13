"""Run one tiny synthetic train/evaluate/predict cycle without external data."""

import csv
import tempfile
from pathlib import Path

import numpy as np
import torch
import yaml
from PIL import Image, ImageDraw

from lane_segmentation.evaluate import load_checkpoint, run_evaluation
from lane_segmentation.inference import predict_image
from lane_segmentation.train import train


def run_smoke_test():
    with tempfile.TemporaryDirectory(prefix="lane-seg-smoke-") as temporary_dir:
        root = Path(temporary_dir)
        data_root = root / "data"
        data_root.mkdir()
        rows = []
        for index in range(4):
            image = Image.new("RGB", (128, 64), (35, 40, 45))
            mask = Image.new("L", (128, 64), 0)
            ImageDraw.Draw(image).line((20 + index, 63, 64, 5), fill=(220, 220, 220), width=3)
            ImageDraw.Draw(mask).line((20 + index, 63, 64, 5), fill=255, width=5)
            image_name = f"image_{index}.png"
            mask_name = f"mask_{index}.png"
            image.save(data_root / image_name)
            mask.save(data_root / mask_name)
            rows.append({"image": image_name, "mask": mask_name, "sequence_id": f"sequence_{index}"})

        for name, selected_rows in (("train", rows[:2]), ("val", rows[2:])):
            manifest = root / f"{name}.csv"
            with manifest.open("w", newline="", encoding="utf-8") as file:
                writer = csv.DictWriter(file, fieldnames=("image", "mask", "sequence_id"))
                writer.writeheader()
                writer.writerows(selected_rows)

        config_dir = root / "configs"
        config_dir.mkdir()
        config_path = config_dir / "baseline.yaml"
        config = {
            "seed": 42,
            "device": "auto",
            "image_size": [64, 128],
            "data_root": "data",
            "train_manifest": "train.csv",
            "val_manifest": "val.csv",
            "batch_size": 1,
            "num_workers": 0,
            "learning_rate": 0.001,
            "weight_decay": 0.0001,
            "epochs": 1,
            "early_stopping_patience": 1,
            "threshold": 0.5,
            "checkpoint_dir": "experiments/smoke",
            "log_file": "metrics.csv",
        }
        config_path.write_text(yaml.safe_dump(config), encoding="utf-8")
        checkpoint_path = train(config_path)
        output_dir = root / "results"
        run_evaluation(config_path, checkpoint_path, output_dir, num_visualizations=1)

        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        model, _ = load_checkpoint(checkpoint_path, device)
        sample_prediction = predict_image(
            model,
            data_root / rows[0]["image"],
            image_size=(64, 128),
            device=device,
        )
        if sample_prediction.shape != (64, 128):
            raise AssertionError(f"Unexpected prediction shape: {sample_prediction.shape}")
        if not (output_dir / "metrics.json").is_file() or not (output_dir / "sample_000.png").is_file():
            raise AssertionError("Smoke test did not produce metrics and a visualization")
        print(f"smoke test passed using {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'}")


if __name__ == "__main__":
    run_smoke_test()
