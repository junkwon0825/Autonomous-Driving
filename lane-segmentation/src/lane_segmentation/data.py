"""#1.data: paired image/mask loading and split validation."""

import csv
from pathlib import Path

import numpy as np
import torch
from PIL import Image
from torch.utils.data import Dataset


class LaneSegmentationDataset(Dataset):
    def __init__(self, manifest, data_root, image_size=(256, 512), mask_threshold=127):
        self.manifest = Path(manifest)
        self.data_root = Path(data_root)
        self.height, self.width = image_size
        if self.height <= 0 or self.width <= 0:
            raise ValueError("image_size dimensions must be positive")
        if not 0 <= mask_threshold <= 255:
            raise ValueError("mask_threshold must be between 0 and 255")
        self.mask_threshold = mask_threshold
        if not self.manifest.is_file():
            raise FileNotFoundError(f"Manifest not found: {self.manifest}")

        with self.manifest.open("r", newline="", encoding="utf-8-sig") as file:
            reader = csv.DictReader(file)
            if not reader.fieldnames or not {"image", "mask"}.issubset(reader.fieldnames):
                raise ValueError("Manifest must contain image and mask columns")
            self.rows = [row for row in reader if row.get("image") and row.get("mask")]
        if not self.rows:
            raise ValueError(f"No image/mask pairs found in {self.manifest}")

    def __len__(self):
        return len(self.rows)

    def __getitem__(self, index):
        row = self.rows[index]
        image_path = self.data_root / row["image"]
        mask_path = self.data_root / row["mask"]
        if not image_path.is_file() or not mask_path.is_file():
            raise FileNotFoundError(f"Missing image or mask for manifest row {index}: {image_path}, {mask_path}")

        with Image.open(image_path) as source:
            image = source.convert("RGB")
        with Image.open(mask_path) as source:
            mask = source.convert("L")
        if image.size != mask.size:
            raise ValueError(f"Image/mask size mismatch for {image_path}: {image.size} != {mask.size}")

        size = (self.width, self.height)
        image = image.resize(size, Image.Resampling.BILINEAR)
        mask = mask.resize(size, Image.Resampling.NEAREST)
        image_array = np.asarray(image, dtype=np.float32) / 255.0
        mask_array = (np.asarray(mask, dtype=np.uint8) > self.mask_threshold).astype(np.float32)
        image_tensor = torch.from_numpy(image_array).permute(2, 0, 1).contiguous()
        mask_tensor = torch.from_numpy(mask_array).unsqueeze(0).contiguous()

        if image_tensor.shape != (3, self.height, self.width):
            raise ValueError(f"Unexpected image tensor shape: {tuple(image_tensor.shape)}")
        if mask_tensor.shape != (1, self.height, self.width):
            raise ValueError(f"Unexpected mask tensor shape: {tuple(mask_tensor.shape)}")
        if not torch.isfinite(image_tensor).all() or image_tensor.min() < 0 or image_tensor.max() > 1:
            raise ValueError(f"Image values must be finite and in [0, 1]: {image_path}")
        return image_tensor, mask_tensor


def validate_split(train_manifest, val_manifest):
    def read_rows(path):
        with Path(path).open("r", newline="", encoding="utf-8-sig") as file:
            reader = csv.DictReader(file)
            if not reader.fieldnames or not {"image", "mask"}.issubset(reader.fieldnames):
                raise ValueError(f"Manifest must contain image and mask columns: {path}")
            return list(reader)

    train_rows = read_rows(train_manifest)
    val_rows = read_rows(val_manifest)
    train_images = {row["image"] for row in train_rows if row.get("image")}
    val_images = {row["image"] for row in val_rows if row.get("image")}
    overlap = train_images & val_images
    if overlap:
        raise ValueError(f"Image paths occur in both train and validation manifests: {sorted(overlap)[:3]}")

    if any(row.get("sequence_id") for row in train_rows + val_rows):
        train_sequences = {row["sequence_id"] for row in train_rows if row.get("sequence_id")}
        val_sequences = {row["sequence_id"] for row in val_rows if row.get("sequence_id")}
        overlap = train_sequences & val_sequences
        if overlap:
            raise ValueError(f"Video sequences occur in both splits: {sorted(overlap)[:3]}")
