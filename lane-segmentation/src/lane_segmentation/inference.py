"""Single-image prediction helpers."""

import numpy as np
import torch
from PIL import Image
from torch.nn import functional as F


@torch.inference_mode()
def predict_image(model, image_path, image_size=(256, 512), threshold=0.5, device="cpu"):
    with Image.open(image_path) as source:
        image = source.convert("RGB")
    original_size = image.size
    height, width = image_size
    resized = image.resize((width, height), Image.Resampling.BILINEAR)
    array = np.asarray(resized, dtype=np.float32) / 255.0
    inputs = torch.from_numpy(array).permute(2, 0, 1).unsqueeze(0).to(device)
    model.eval()
    logits = model(inputs)
    logits = F.interpolate(logits, size=(original_size[1], original_size[0]), mode="bilinear", align_corners=False)
    return (torch.sigmoid(logits)[0, 0] >= threshold).to(torch.uint8).cpu().numpy()
