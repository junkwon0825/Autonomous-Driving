"""#3.compile,train: BCE baseline, validation, early stopping and checkpointing."""

import argparse
import csv
import random
import shutil
from pathlib import Path

import numpy as np
import torch
import yaml
from torch import nn
from torch.utils.data import DataLoader

from lane_segmentation.data import LaneSegmentationDataset, validate_split
from lane_segmentation.metrics import binary_metrics_from_counts, count_binary_predictions, mean_image_dice
from lane_segmentation.model import UNet


def select_device(requested):
    if requested == "auto":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    device = torch.device(requested)
    if device.type == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA was requested but torch.cuda.is_available() is False")
    return device


def set_seed(seed):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


def _run_epoch(model, loader, loss_fn, device, optimizer=None, threshold=0.5):
    training = optimizer is not None
    model.train(training)
    total_loss = 0.0
    sample_count = 0
    image_dice_total = 0.0
    counts = [0, 0, 0]
    context = torch.enable_grad if training else torch.inference_mode

    with context():
        for images, masks in loader:
            images = images.to(device, non_blocking=device.type == "cuda")
            masks = masks.to(device, non_blocking=device.type == "cuda")
            logits = model(images)
            loss = loss_fn(logits, masks)
            if training:
                optimizer.zero_grad(set_to_none=True)
                loss.backward()
                optimizer.step()

            batch_size = images.shape[0]
            total_loss += loss.item() * batch_size
            sample_count += batch_size
            batch_counts = count_binary_predictions(logits, masks, threshold)
            counts = [total + current for total, current in zip(counts, batch_counts)]
            image_dice_total += mean_image_dice(logits, masks, threshold) * batch_size

    if sample_count == 0:
        raise ValueError("Cannot run an epoch with an empty data loader")
    metrics = binary_metrics_from_counts(*counts)
    metrics["mean_image_dice"] = image_dice_total / sample_count
    return total_loss / sample_count, metrics


def train(config_path):
    config_path = Path(config_path).resolve()
    with config_path.open("r", encoding="utf-8") as file:
        config = yaml.safe_load(file)
    if not isinstance(config, dict):
        raise ValueError("Training config must be a YAML mapping")

    set_seed(int(config["seed"]))
    project_dir = config_path.parent.parent
    resolve = lambda value: (project_dir / value).resolve()
    train_manifest = resolve(config["train_manifest"])
    val_manifest = resolve(config["val_manifest"])
    data_root = resolve(config["data_root"])
    validate_split(train_manifest, val_manifest)

    image_size = tuple(int(value) for value in config["image_size"])
    train_set = LaneSegmentationDataset(train_manifest, data_root, image_size)
    val_set = LaneSegmentationDataset(val_manifest, data_root, image_size)
    device = select_device(config.get("device", "auto"))
    loader_options = {
        "batch_size": int(config["batch_size"]),
        "num_workers": int(config.get("num_workers", 0)),
        "pin_memory": device.type == "cuda",
    }
    train_loader = DataLoader(train_set, shuffle=True, **loader_options)
    val_loader = DataLoader(val_set, shuffle=False, **loader_options)

    model = UNet().to(device)
    loss_fn = nn.BCEWithLogitsLoss()
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=float(config["learning_rate"]),
        weight_decay=float(config.get("weight_decay", 0.0)),
    )
    run_dir = resolve(config["checkpoint_dir"])
    run_dir.mkdir(parents=True, exist_ok=True)
    log_path = run_dir / config.get("log_file", "metrics.csv")
    checkpoint_path = run_dir / "best.pt"
    saved_config = run_dir / "config.yaml"
    shutil.copyfile(config_path, saved_config)

    best_loss = float("inf")
    stale_epochs = 0
    patience = int(config["early_stopping_patience"])
    with log_path.open("w", newline="", encoding="utf-8") as log_file:
        writer = csv.DictWriter(
            log_file,
            fieldnames=(
                "epoch",
                "train_loss",
                "val_loss",
                "val_mean_image_dice",
                "val_pixel_dice",
                "val_iou",
                "val_precision",
                "val_recall",
            ),
        )
        writer.writeheader()
        for epoch in range(1, int(config["epochs"]) + 1):
            train_loss, _ = _run_epoch(model, train_loader, loss_fn, device, optimizer, float(config["threshold"]))
            val_loss, val_metrics = _run_epoch(model, val_loader, loss_fn, device, threshold=float(config["threshold"]))
            row = {
                "epoch": epoch,
                "train_loss": train_loss,
                "val_loss": val_loss,
                "val_mean_image_dice": val_metrics["mean_image_dice"],
                "val_pixel_dice": val_metrics["dice"],
                **{
                    f"val_{name}": value
                    for name, value in val_metrics.items()
                    if name not in ("mean_image_dice", "dice")
                },
            }
            writer.writerow(row)
            log_file.flush()
            print(
                f"epoch={epoch} train_loss={train_loss:.5f} val_loss={val_loss:.5f} "
                f"mean_image_dice={val_metrics['mean_image_dice']:.5f} "
                f"pixel_dice={val_metrics['dice']:.5f} iou={val_metrics['iou']:.5f}"
            )

            if val_loss < best_loss:
                best_loss = val_loss
                stale_epochs = 0
                torch.save(
                    {
                        "model_state_dict": model.state_dict(),
                        "optimizer_state_dict": optimizer.state_dict(),
                        "epoch": epoch,
                        "best_val_loss": best_loss,
                        "config": config,
                    },
                    checkpoint_path,
                )
            else:
                stale_epochs += 1
                if stale_epochs >= patience:
                    print(f"early stopping after {epoch} epochs")
                    break

    if not checkpoint_path.is_file():
        raise RuntimeError("Training completed without saving a best checkpoint")
    return checkpoint_path


def main():
    parser = argparse.ArgumentParser(description="Train the U-Net BCE lane segmentation baseline")
    parser.add_argument("--config", default="configs/baseline.yaml")
    args = parser.parse_args()
    train(args.config)


if __name__ == "__main__":
    main()
