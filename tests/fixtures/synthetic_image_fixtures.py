"""Programmatic generators for synthetic test images (clean, corrupt, and adversarial fixtures)."""

from __future__ import annotations

import io
import struct
import zlib
from typing import Dict, Optional, Tuple
from PIL import Image, ImageDraw, ImageFilter


def create_test_jpeg(
    dimensions: Tuple[int, int] = (800, 600),
    exif_tags: Optional[Dict[int, str]] = None,
    text: str = "-6 + 12 - 4 = 2",
) -> bytes:
    """Generates a synthetic JPEG image with drawn handwriting lines and optional EXIF."""
    w, h = dimensions
    img = Image.new("RGB", (w, h), color=(250, 250, 250))
    draw = ImageDraw.Draw(img)

    # Draw simulated number line and arrows
    draw.line([(50, h // 2), (w - 50, h // 2)], fill=(20, 20, 20), width=4)
    for x in range(100, w - 50, 60):
        draw.line([(x, h // 2 - 15), (x, h // 2 + 15)], fill=(20, 20, 20), width=3)

    # Draw simulated handwriting text
    draw.text((100, 80), text, fill=(10, 10, 10))

    bio = io.BytesIO()
    if exif_tags:
        exif = img.getexif()
        for tag_id, val in exif_tags.items():
            exif[tag_id] = val
        img.save(bio, format="JPEG", quality=90, exif=exif)
    else:
        img.save(bio, format="JPEG", quality=90)

    return bio.getvalue()


def create_test_png(
    dimensions: Tuple[int, int] = (800, 600),
    with_alpha: bool = False,
    text: str = "ClassLens Math",
) -> bytes:
    """Generates a synthetic PNG image, optionally with alpha transparency."""
    w, h = dimensions
    mode = "RGBA" if with_alpha else "RGB"
    bg_color = (255, 255, 255, 0) if with_alpha else (255, 255, 255)
    ink_color = (0, 0, 0, 255) if with_alpha else (0, 0, 0)

    img = Image.new(mode, (w, h), color=bg_color)
    draw = ImageDraw.Draw(img)
    draw.line([(60, h // 2), (w - 60, h // 2)], fill=ink_color, width=4)
    draw.text((80, 80), text, fill=ink_color)

    bio = io.BytesIO()
    img.save(bio, format="PNG")
    return bio.getvalue()


def create_test_webp(
    dimensions: Tuple[int, int] = (800, 600),
) -> bytes:
    """Generates a synthetic WebP image."""
    w, h = dimensions
    img = Image.new("RGB", (w, h), color=(240, 240, 240))
    draw = ImageDraw.Draw(img)
    draw.line([(50, h // 2), (w - 50, h // 2)], fill=(30, 30, 30), width=4)

    bio = io.BytesIO()
    img.save(bio, format="WEBP")
    return bio.getvalue()


def create_decompression_bomb() -> bytes:
    """Builds a valid 69-byte PNG file header claiming 20,000 x 20,000 dimensions (400 MP)."""
    header = b"\x89PNG\r\n\x1a\n"
    # IHDR chunk: 20000x20000 pixels
    ihdr_data = struct.pack(">IIBBBBB", 20000, 20000, 8, 2, 0, 0, 0)
    ihdr_crc = struct.pack(">I", zlib.crc32(b"IHDR" + ihdr_data) & 0xFFFFFFFF)
    ihdr = struct.pack(">I", 13) + b"IHDR" + ihdr_data + ihdr_crc

    # Minimal compressed IDAT chunk
    compressed = zlib.compress(b"\x00" * 100)
    idat = (
        struct.pack(">I", len(compressed))
        + b"IDAT"
        + compressed
        + struct.pack(">I", zlib.crc32(b"IDAT" + compressed) & 0xFFFFFFFF)
    )

    # IEND chunk
    iend = struct.pack(">I", 0) + b"IEND" + struct.pack(">I", zlib.crc32(b"IEND") & 0xFFFFFFFF)

    return header + ihdr + idat + iend


def create_blurred_image(
    dimensions: Tuple[int, int] = (800, 600),
    blur_radius: float = 12.0,
) -> bytes:
    """Generates a heavily Gaussian-blurred image yielding Laplacian variance < 80."""
    w, h = dimensions
    img = Image.new("RGB", (w, h), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.line([(50, h // 2), (w - 50, h // 2)], fill=(0, 0, 0), width=5)
    draw.text((100, 100), "Blurred Handwriting", fill=(0, 0, 0))

    # Apply heavy blur
    blurred = img.filter(ImageFilter.GaussianBlur(radius=blur_radius))
    bio = io.BytesIO()
    blurred.save(bio, format="JPEG", quality=85)
    return bio.getvalue()


def create_faint_image(
    dimensions: Tuple[int, int] = (800, 600),
) -> bytes:
    """Generates a low-contrast image simulating sharp but faint pencil marks on white paper."""
    w, h = dimensions
    img = Image.new("RGB", (w, h), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    # Faint pencil strokes in light gray (e.g. 185 on 255)
    for y in range(100, 500, 50):
        draw.line([(50, y), (750, y)], fill=(185, 185, 185), width=2)
    for x in range(100, 750, 40):
        draw.line([(x, 280), (x, 320)], fill=(185, 185, 185), width=2)
    draw.text((100, 60), "Faint pencil: -6 + 12 - 4 = 2", fill=(180, 180, 180))

    bio = io.BytesIO()
    img.save(bio, format="JPEG", quality=90)
    return bio.getvalue()
