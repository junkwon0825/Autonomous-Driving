"""#4.evaluate,predict: validation metrics, sample predictions and overlays."""

import argparse
import json
from pathlib import Path

import numpy as np
import torch
import yaml
from PIL import Image, ImageDraw
from torch import nn
from torch.utils.data import DataLoader

from lane_segmentation.data import LaneSegmentationDataset, validate_split
from lane_segmentation.inference import predict_image
from lane_segmentation.metrics import binary_metrics_from_counts, count_binary_predictions, mean_image_dice
from lane_segmentation.model import UNet
from lane_segmentation.train import select_device


def load_checkpoint(checkpoint_path, device):
    checkpoint = torch.load(checkpoint_path, map_location=device, weights_only=True)
    model = UNet().to(device)
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()
    return model, checkpoint


@torch.inference_mode()
def evaluate(model, loader, device, threshold=0.5):
    model.eval()
    loss_fn = nn.BCEWithLogitsLoss()
    total_loss = 0.0
    sample_count = 0
    image_dice_total = 0.0
    counts = [0, 0, 0]
    for images, masks in loader:
        images = images.to(device, non_blocking=device.type == "cuda")
        masks = masks.to(device, non_blocking=device.type == "cuda")
        logits = model(images)
        total_loss += loss_fn(logits, masks).item() * images.shape[0]
        sample_count += images.shape[0]
        counts = [total + current for total, current in zip(counts, count_binary_predictions(logits, masks, threshold))]
        image_dice_total += mean_image_dice(logits, masks, threshold) * images.shape[0]
    if sample_count == 0:
        raise ValueError("Cannot evaluate an empty validation dataset")
    return {
        "val_loss": total_loss / sample_count,
        "mean_image_dice": image_dice_total / sample_count,
        **binary_metrics_from_counts(*counts),
    }


def save_visualization(image_path, mask_path, prediction, destination, image_size):
    with Image.open(image_path) as source:
        original = source.convert("RGB").resize((image_size[1], image_size[0]), Image.Resampling.BILINEAR)
    with Image.open(mask_path) as source:
        ground_truth = source.convert("L").resize((image_size[1], image_size[0]), Image.Resampling.NEAREST)

    original_array = np.asarray(original).copy()
    target = np.asarray(ground_truth) > 0
    prediction_image = Image.fromarray(prediction.astype(np.uint8) * 255).resize(
        (image_size[1], image_size[0]), Image.Resampling.NEAREST
    )
    predicted = np.asarray(prediction_image) > 0
    target_image = np.repeat((target * 255).astype(np.uint8)[..., None], 3, axis=2)
    predicted_image = np.repeat((predicted * 255).astype(np.uint8)[..., None], 3, axis=2)
    overlay = original_array.copy()
    overlay[target] = (overlay[target] * 0.45 + np.array((0, 255, 0)) * 0.55).astype(np.uint8)
    overlay[predicted] = (overlay[predicted] * 0.45 + np.array((255, 0, 0)) * 0.55).astype(np.uint8)

    panels = [
        Image.fromarray(original_array),
        Image.fromarray(target_image),
        Image.fromarray(predicted_image),
        Image.fromarray(overlay),
    ]
    panel_width, panel_height = panels[0].size
    canvas = Image.new("RGB", (panel_width * 4, panel_height + 24), "white")
    draw = ImageDraw.Draw(canvas)
    for index, (label, panel) in enumerate(zip(("Original", "Ground Truth", "Prediction", "Overlay"), panels)):
        x = index * panel_width
        canvas.paste(panel, (x, 24))
        draw.text((x + 4, 5), label, fill="black")
    destination.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(destination)


def run_evaluation(config_path, checkpoint_path, output_dir, num_visualizations=8):
    config_path = Path(config_path).resolve()
    project_dir = config_path.parent.parent
    with config_path.open("r", encoding="utf-8") as file:
        config = yaml.safe_load(file)
    resolve = lambda value: (project_dir / value).resolve()
    device = select_device(config.get("device", "auto"))
    model, checkpoint = load_checkpoint(checkpoint_path, device)
    image_size = tuple(int(value) for value in config["image_size"])
    val_manifest = resolve(config["val_manifest"])
    validate_split(resolve(config["train_manifest"]), val_manifest)
    dataset = LaneSegmentationDataset(val_manifest, resolve(config["data_root"]), image_size)
    loader = DataLoader(dataset, batch_size=int(config["batch_size"]), shuffle=False, num_workers=0)
    metrics = evaluate(model, loader, device, float(config["threshold"]))
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    metrics["checkpoint_epoch"] = int(checkpoint["epoch"])
    with (output_dir / "metrics.json").open("w", encoding="utf-8") as file:
        json.dump(metrics, file, indent=2)

    for index, row in enumerate(dataset.rows[:num_visualizations]):
        prediction = predict_image(
            model,
            resolve(config["data_root"]) / row["image"],
            image_size=image_size,
            threshold=float(config["threshold"]),
            device=device,
        )
        save_visualization(
            resolve(config["data_root"]) / row["image"],
            resolve(config["data_root"]) / row["mask"],
            prediction,
            output_dir / f"sample_{index:03d}.png",
            image_size,
        )
    print(json.dumps(metrics, indent=2))
    return metrics


def main():
    parser = argparse.ArgumentParser(description="Evaluate a saved lane segmentation checkpoint")
    parser.add_argument("--config", default="configs/baseline.yaml")
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--output-dir", default="results/predictions")
    parser.add_argument("--num-visualizations", type=int, default=8)
    args = parser.parse_args()
    run_evaluation(args.config, args.checkpoint, args.output_dir, args.num_visualizations)


if __name__ == "__main__":
    main()
