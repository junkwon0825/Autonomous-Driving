"""Binary segmentation losses and pixel-level metrics."""

import torch


def binary_metrics_from_counts(true_positive, false_positive, false_negative):
    tp = float(true_positive)
    fp = float(false_positive)
    fn = float(false_negative)
    predicted_positive = tp + fp
    actual_positive = tp + fn
    union = tp + fp + fn

    return {
        "dice": 1.0 if union == 0 else 2.0 * tp / (2.0 * tp + fp + fn),
        "iou": 1.0 if union == 0 else tp / union,
        "precision": 0.0 if predicted_positive == 0 else tp / predicted_positive,
        "recall": 0.0 if actual_positive == 0 else tp / actual_positive,
    }


@torch.no_grad()
def count_binary_predictions(logits, targets, threshold=0.5):
    if logits.shape != targets.shape:
        raise ValueError(f"Logit/target shapes differ: {tuple(logits.shape)} != {tuple(targets.shape)}")
    predictions = torch.sigmoid(logits) >= threshold
    targets = targets >= 0.5
    true_positive = torch.count_nonzero(predictions & targets).item()
    false_positive = torch.count_nonzero(predictions & ~targets).item()
    false_negative = torch.count_nonzero(~predictions & targets).item()
    return true_positive, false_positive, false_negative


def binary_metrics(logits, targets, threshold=0.5):
    return binary_metrics_from_counts(*count_binary_predictions(logits, targets, threshold))


@torch.no_grad()
def mean_image_dice(logits, targets, threshold=0.5):
    if logits.shape != targets.shape:
        raise ValueError(f"Logit/target shapes differ: {tuple(logits.shape)} != {tuple(targets.shape)}")
    predictions = torch.sigmoid(logits) >= threshold
    targets = targets >= 0.5
    reduce_dims = tuple(range(1, predictions.ndim))
    true_positive = torch.count_nonzero(predictions & targets, dim=reduce_dims).float()
    false_positive = torch.count_nonzero(predictions & ~targets, dim=reduce_dims).float()
    false_negative = torch.count_nonzero(~predictions & targets, dim=reduce_dims).float()
    denominator = 2 * true_positive + false_positive + false_negative
    dice = torch.where(denominator == 0, 1.0, 2 * true_positive / denominator)
    return dice.mean().item()
