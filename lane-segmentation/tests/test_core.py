import csv

import numpy as np
import pytest
import torch
from PIL import Image, ImageDraw

from lane_segmentation.data import LaneSegmentationDataset, validate_split
from lane_segmentation.inference import predict_image
from lane_segmentation.metrics import binary_metrics, binary_metrics_from_counts
from lane_segmentation.model import UNet


def create_pair(root, name, size=(64, 32)):
    image = Image.new("RGB", size, (50, 80, 110))
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).line((4, size[1] - 1, size[0] // 2, 1), fill=255, width=3)
    image_path = root / f"{name}.png"
    mask_path = root / f"{name}_mask.png"
    image.save(image_path)
    mask.save(mask_path)
    return image_path, mask_path


def write_manifest(path, rows):
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=("image", "mask", "sequence_id"))
        writer.writeheader()
        writer.writerows(rows)


def test_dataset_shapes_ranges_and_nearest_mask(tmp_path):
    create_pair(tmp_path, "sample")
    manifest = tmp_path / "manifest.csv"
    write_manifest(manifest, [{"image": "sample.png", "mask": "sample_mask.png", "sequence_id": "clip-a"}])
    dataset = LaneSegmentationDataset(manifest, tmp_path, image_size=(16, 32))
    image, mask = dataset[0]

    assert image.shape == (3, 16, 32)
    assert mask.shape == (1, 16, 32)
    assert image.dtype == torch.float32 and mask.dtype == torch.float32
    assert torch.all((image >= 0) & (image <= 1))
    assert set(torch.unique(mask).tolist()).issubset({0.0, 1.0})
    with Image.open(tmp_path / "sample_mask.png") as source:
        expected = source.convert("L").resize((32, 16), Image.Resampling.NEAREST)
    np.testing.assert_array_equal(mask[0].numpy(), (np.asarray(expected) > 0).astype(np.float32))


def test_model_forward_and_bce_logits():
    model = UNet()
    inputs = torch.rand(2, 3, 32, 48)
    targets = torch.zeros(2, 1, 32, 48)
    logits = model(inputs)
    loss = torch.nn.BCEWithLogitsLoss()(logits, targets)

    assert logits.shape == targets.shape
    assert torch.isfinite(loss)


def test_binary_metrics_and_empty_target_conventions():
    logits = torch.tensor([[[[10.0, -10.0], [10.0, -10.0]]]])
    targets = torch.tensor([[[[1.0, 0.0], [0.0, 0.0]]]])
    assert binary_metrics(logits, targets) == {
        "dice": 2 / 3,
        "iou": 0.5,
        "precision": 0.5,
        "recall": 1.0,
    }
    assert binary_metrics_from_counts(0, 0, 0) == {
        "dice": 1.0,
        "iou": 1.0,
        "precision": 0.0,
        "recall": 0.0,
    }


def test_split_rejects_shared_sequence(tmp_path):
    train_manifest = tmp_path / "train.csv"
    val_manifest = tmp_path / "val.csv"
    write_manifest(train_manifest, [{"image": "a.png", "mask": "a_mask.png", "sequence_id": "clip"}])
    write_manifest(val_manifest, [{"image": "b.png", "mask": "b_mask.png", "sequence_id": "clip"}])

    with pytest.raises(ValueError, match="Video sequences"):
        validate_split(train_manifest, val_manifest)


def test_inference_returns_original_image_size(tmp_path):
    image_path, _ = create_pair(tmp_path, "sample", size=(80, 40))
    prediction = predict_image(UNet(), image_path, image_size=(32, 64))

    assert prediction.shape == (40, 80)
    assert set(np.unique(prediction)).issubset({0, 1})
