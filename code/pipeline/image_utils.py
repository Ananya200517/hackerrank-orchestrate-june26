from __future__ import annotations

import base64
import mimetypes
from pathlib import Path

MIME_BY_SUFFIX = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
    ".gif": "image/gif",
}


def guess_mime_type(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in MIME_BY_SUFFIX:
        return MIME_BY_SUFFIX[suffix]
    guessed, _ = mimetypes.guess_type(path.name)
    return guessed or "image/jpeg"


def encode_image_base64(path: Path) -> tuple[str, str]:
    mime_type = guess_mime_type(path)
    data = base64.standard_b64encode(path.read_bytes()).decode("ascii")
    return mime_type, data
