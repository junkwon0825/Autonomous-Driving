import csv
import io
import zipfile

import numpy as np
import pytest
import torch
from PIL import Image, ImageDraw

from lane_segmentation.data import LaneSegmentationDataset, validate_split
from lane_segmentation.evaluate import evaluate_thresholds, save_visualization
from lane_segmentation.inference import predict_image
from lane_segmentation.metrics import binary_metrics, binary_metrics_from_counts, mean_image_dice
from lane_segmentation.model import UNet
from lane_segmentation.prepare_data import prepare_data
from lane_segmentation.submission import encode_rle, generate_submission
from lane_segmentation.train import save_loss_curve


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
    np.testing.assert_array_equal(mask[0].numpy(), (np.asarray(expected) > 127).astype(np.float32))


def test_dataset_ignores_jpeg_background_artifacts_below_threshold(tmp_path):
    image_path = tmp_path / "image.png"
    mask_path = tmp_path / "mask.png"
    Image.new("RGB", (5, 1)).save(image_path)
    Image.fromarray(np.array([[0, 1, 127, 128, 255]], dtype=np.uint8)).save(mask_path)
    manifest = tmp_path / "manifest.csv"
    write_manifest(manifest, [{"image": "image.png", "mask": "mask.png", "sequence_id": "clip"}])

    _, mask = LaneSegmentationDataset(manifest, tmp_path, image_size=(1, 5), mask_threshold=127)[0]

    np.testing.assert_array_equal(mask[0].numpy(), [[0, 0, 0, 1, 1]])


def test_prepare_data_creates_date_group_holdout_and_report(tmp_path):
    archive_path = tmp_path / "dataset.zip"

    def jpeg_bytes(image):
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG")
        return buffer.getvalue()

    with zipfile.ZipFile(archive_path, "w") as archive:
        for filename in ("0313-1_1.jpg", "0313-2_2.jpg", "0531_3.jpg", "0601_4.jpg"):
            archive.writestr(f"train/train/frames/{filename}", jpeg_bytes(Image.new("RGB", (16, 8))))
            archive.writestr(
                f"train/train/lane-masks/{filename}",
                jpeg_bytes(Image.fromarray(np.pad(np.full((4, 2), 255, dtype=np.uint8), ((4, 0), (0, 14))))),
            )
        archive.writestr("test/test/frames/test.jpg", jpeg_bytes(Image.new("RGB", (16, 8))))
        archive.writestr("sample_submission.csv", "image_id,encoded_pixels\ntest.jpg,\n")

    report = prepare_data(
        archive_path,
        tmp_path / "raw",
        tmp_path / "processed",
        seed=42,
    )

    assert report["train_images"] == 3
    assert report["validation_images"] == 1
    assert report["validation_group"] == "0601"
    assert report["sequence_groups"] == {"0313": 2, "0531": 1, "0601": 1}
    assert (tmp_path / "processed" / "train_smoke.csv").is_file()
    assert (tmp_path / "processed" / "val_smoke.csv").is_file()


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


def test_mean_image_dice_matches_average_per_image_score():
    logits = torch.full((2, 1, 1, 10), -10.0)
    logits[0, 0, 0, 0] = 10.0
    targets = torch.zeros_like(logits)
    targets[0, 0, 0, 0] = 1.0
    targets[1] = 1.0

    assert mean_image_dice(logits, targets) == 0.5
    assert binary_metrics(logits, targets)["dice"] == pytest.approx(1 / 6)


def test_threshold_sweep_selects_best_mean_image_dice():
    logits = torch.tensor([[[[-2.0, 2.0]]]])
    targets = torch.tensor([[[[1.0, 0.0]]]])

    scores = evaluate_thresholds(
        torch.nn.Identity(),
        torch.utils.data.DataLoader(torch.utils.data.TensorDataset(logits, targets), batch_size=1),
        torch.device("cpu"),
        (0.1, 0.5),
    )

    assert scores[0.1]["mean_image_dice"] == pytest.approx(2 / 3)
    assert scores[0.5]["mean_image_dice"] == 0.0


def test_split_rejects_shared_sequence(tmp_path):
    train_manifest = tmp_path / "train.csv"
    val_manifest = tmp_path / "val.csv"
    write_manifest(train_manifest, [{"image": "a.png", "mask": "a_mask.png", "sequence_id": "clip"}])
    write_manifest(val_manifest, [{"image": "b.png", "mask": "b_mask.png", "sequence_id": "clip"}])

    with pytest.raises(ValueError, match="Video sequences"):
        validate_split(train_manifest, val_manifest)


def test_loss_curve_is_saved_as_png(tmp_path):
    metrics = tmp_path / "metrics.csv"
    metrics.write_text("epoch,train_loss,val_loss\n1,0.8,0.9\n2,0.5,0.6\n", encoding="utf-8")
    output = save_loss_curve(metrics, tmp_path / "loss.png")

    with Image.open(output) as curve:
        assert curve.format == "PNG"
        assert curve.size == (1000, 600)


def test_inference_returns_original_image_size(tmp_path):
    image_path, _ = create_pair(tmp_path, "sample", size=(80, 40))
    prediction = predict_image(UNet(), image_path, image_size=(32, 64))

    assert prediction.shape == (40, 80)
    assert set(np.unique(prediction)).issubset({0, 1})


def test_visualization_preserves_original_resolution(tmp_path):
    image_path, mask_path = create_pair(tmp_path, "sample", size=(80, 40))
    output = tmp_path / "visualization.png"

    save_visualization(image_path, mask_path, np.zeros((40, 80), dtype=np.uint8), output)

    with Image.open(output) as visualization:
        assert visualization.size == (80 * 4, 40 + 24)


@pytest.mark.parametrize("order", ("C", "F"))
@pytest.mark.parametrize("index_base", (0, 1))
def test_rle_round_trip(order, index_base):
    mask = np.array([[0, 1, 1], [1, 0, 1]], dtype=np.uint8)
    encoded = encode_rle(mask, order, index_base)
    values = np.asarray(mask).ravel(order=order)
    decoded = np.zeros_like(values)
    runs = [int(value) for value in encoded.split()]
    for start, length in zip(runs[::2], runs[1::2]):
        start -= index_base
        decoded[start : start + length] = 1

    np.testing.assert_array_equal(decoded.reshape(mask.shape, order=order), mask)
    assert encode_rle(np.zeros_like(mask), order, index_base) == "0"


def test_submission_uses_template_order_and_rle(tmp_path):
    class PositiveModel(torch.nn.Module):
        def forward(self, inputs):
            return torch.full((inputs.shape[0], 1, 8, 12), 10.0, device=inputs.device)

    test_root = tmp_path / "test"
    test_root.mkdir()
    Image.new("RGB", (12, 8), (20, 30, 40)).save(test_root / "second.jpg")
    Image.new("RGB", (12, 8), (40, 30, 20)).save(test_root / "first.jpg")
    template = tmp_path / "sample_submission.csv"
    template.write_text("image_id,encoded_pixels\nsecond.jpg,\nfirst.jpg,\n", encoding="utf-8")
    legacy_template = tmp_path / "historical_template.csv"
    legacy_template.write_text("filename,rle\nsecond.jpg,\nfirst.jpg,\n", encoding="utf-8")
    output = tmp_path / "submission.csv"
    legacy_output = tmp_path / "submission_legacy.csv"

    generate_submission(
        PositiveModel(),
        template,
        test_root,
        output,
        image_size=(8, 12),
        threshold=0.5,
        device="cpu",
        rle_order="C",
        index_base=1,
        legacy_template=legacy_template,
        legacy_output_path=legacy_output,
    )

    with output.open("r", newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))
    assert [row["image_id"] for row in rows] == ["second.jpg", "first.jpg"]
    assert all(row["encoded_pixels"] == "1 96" for row in rows)
    with legacy_output.open("r", newline="", encoding="utf-8") as file:
        legacy_rows = list(csv.DictReader(file))
    assert legacy_rows == [
        {"filename": "second.jpg", "rle": "1 96"},
        {"filename": "first.jpg", "rle": "1 96"},
    ]


def test_submission_supports_historical_filename_rle_template(tmp_path):
    class PositiveModel(torch.nn.Module):
        def forward(self, inputs):
            return torch.full((inputs.shape[0], 1, 8, 12), 10.0, device=inputs.device)

    test_root = tmp_path / "test"
    test_root.mkdir()
    Image.new("RGB", (12, 8)).save(test_root / "frame.jpg")
    template = tmp_path / "historical.csv"
    template.write_text("filename,rle\nframe.jpg,\n", encoding="utf-8")
    output = tmp_path / "submission.csv"

    generate_submission(
        PositiveModel(),
        template,
        test_root,
        output,
        image_size=(8, 12),
        threshold=0.5,
        device="cpu",
        rle_order="C",
        index_base=1,
    )

    with output.open("r", newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))
    assert rows == [{"filename": "frame.jpg", "rle": "1 96"}]
