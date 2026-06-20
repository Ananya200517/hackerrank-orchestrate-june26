from __future__ import annotations

import base64
import io
from pathlib import Path

from PIL import Image


def encode_image_base64(path: Path) -> tuple[str, str]:
    """Normalize all images to JPEG for reliable VLM provider support."""
    with Image.open(path) as img:
        rgb = img.convert("RGB")
        buffer = io.BytesIO()
        rgb.save(buffer, format="JPEG", quality=92)
        payload = buffer.getvalue()
    return "image/jpeg", base64.standard_b64encode(payload).decode("ascii")
