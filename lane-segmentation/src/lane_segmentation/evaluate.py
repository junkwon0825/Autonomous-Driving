"""#4.evaluate,predict: validation metrics, sample predictions and overlays."""

import argparse
import csv
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


@torch.inference_mode()
def evaluate_thresholds(model, loader, device, thresholds):
    thresholds = tuple(float(value) for value in thresholds)
    if not thresholds or any(not 0 < value < 1 for value in thresholds):
        raise ValueError("Threshold candidates must be a non-empty sequence within (0, 1)")
    model.eval()
    loss_fn = nn.BCEWithLogitsLoss()
    results = {
        threshold: {
            "loss": 0.0,
            "dice_sum": 0.0,
            "sample_count": 0,
            "counts": [0, 0, 0],
            "per_image_dice": [],
        }
        for threshold in thresholds
    }

    for images, masks in loader:
        images = images.to(device, non_blocking=device.type == "cuda")
        masks = masks.to(device, non_blocking=device.type == "cuda") >= 0.5
        logits = model(images)
        probabilities = torch.sigmoid(logits)
        batch_size = images.shape[0]
        batch_loss = loss_fn(logits, masks.float()).item() * batch_size
        reduce_dims = tuple(range(1, masks.ndim))
        for threshold, current in results.items():
            predictions = probabilities >= threshold
            true_positive = torch.count_nonzero(predictions & masks, dim=reduce_dims).float()
            false_positive = torch.count_nonzero(predictions & ~masks, dim=reduce_dims).float()
            false_negative = torch.count_nonzero(~predictions & masks, dim=reduce_dims).float()
            denominator = 2 * true_positive + false_positive + false_negative
            dice = torch.where(denominator == 0, 1.0, 2 * true_positive / denominator)
            current["dice_sum"] += dice.sum().item()
            current["per_image_dice"].extend(dice.cpu().tolist())
            current["sample_count"] += batch_size
            current["counts"] = [
                total + int(value)
                for total, value in zip(
                    current["counts"],
                    (
                        torch.count_nonzero(predictions & masks).item(),
                        torch.count_nonzero(predictions & ~masks).item(),
                        torch.count_nonzero(~predictions & masks).item(),
                    ),
                )
            ]
            current["loss"] += batch_loss

    if not next(iter(results.values()))["sample_count"]:
        raise ValueError("Cannot evaluate thresholds on an empty data loader")
    return {
        threshold: {
            "val_loss": values["loss"] / values["sample_count"],
            "mean_image_dice": values["dice_sum"] / values["sample_count"],
            **binary_metrics_from_counts(*values["counts"]),
            "per_image_dice": values["per_image_dice"],
        }
        for threshold, values in results.items()
    }


def save_visualization(image_path, mask_path, prediction, destination, mask_threshold=127):
    with Image.open(image_path) as source:
        original = source.convert("RGB")
    with Image.open(mask_path) as source:
        ground_truth = source.convert("L")
    if original.size != ground_truth.size:
        raise ValueError(f"Image/mask size mismatch for visualization: {image_path}, {mask_path}")

    original_array = np.asarray(original).copy()
    target = np.asarray(ground_truth) > mask_threshold
    if prediction.shape != (original.height, original.width):
        prediction_image = Image.fromarray(prediction.astype(np.uint8)).resize(original.size, Image.Resampling.NEAREST)
        prediction = np.asarray(prediction_image)
    predicted = prediction > 0
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
    dataset = LaneSegmentationDataset(
        val_manifest,
        resolve(config["data_root"]),
        image_size,
        int(config.get("mask_threshold", 127)),
    )
    loader = DataLoader(dataset, batch_size=int(config["batch_size"]), shuffle=False, num_workers=0)
    metrics = evaluate(model, loader, device, float(config["threshold"]))
    threshold_metrics = evaluate_thresholds(
        model,
        loader,
        device,
        config.get("threshold_candidates", (0.25, 0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7, 0.75)),
    )
    best_threshold = max(
        threshold_metrics,
        key=lambda threshold: (
            threshold_metrics[threshold]["mean_image_dice"],
            -abs(threshold - float(config["threshold"])),
        ),
    )
    metrics["recommended_threshold"] = best_threshold
    metrics["recommended_threshold_mean_image_dice"] = threshold_metrics[best_threshold]["mean_image_dice"]
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    metrics["checkpoint_epoch"] = int(checkpoint["epoch"])
    with (output_dir / "metrics.json").open("w", encoding="utf-8") as file:
        json.dump(metrics, file, indent=2)
    with (output_dir / "threshold_sweep.json").open("w", encoding="utf-8") as file:
        json.dump(
            {
                str(threshold): {
                    name: value
                    for name, value in values.items()
                    if name != "per_image_dice"
                }
                for threshold, values in threshold_metrics.items()
            },
            file,
            indent=2,
        )

    ranked_scores = sorted(
        enumerate(threshold_metrics[best_threshold]["per_image_dice"]),
        key=lambda item: item[1],
    )
    sample_count = max(1, num_visualizations // 2)
    selected = [
        ("failure", index, score)
        for index, score in ranked_scores[:sample_count]
    ] + [
        ("best", index, score)
        for index, score in ranked_scores[-sample_count:]
    ]
    with (output_dir / "validation_image_scores.csv").open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=("image", "sequence_id", "mean_image_dice"), lineterminator="\n")
        writer.writeheader()
        for index, score in enumerate(threshold_metrics[best_threshold]["per_image_dice"]):
            row = dataset.rows[index]
            writer.writerow(
                {
                    "image": row["image"],
                    "sequence_id": row.get("sequence_id", ""),
                    "mean_image_dice": score,
                }
            )

    written = set()
    for label, index, score in selected:
        if index in written:
            continue
        written.add(index)
        row = dataset.rows[index]
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
            output_dir / f"{label}_{index:03d}_dice_{score:.3f}.png",
            int(config.get("mask_threshold", 127)),
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
