"""Generate 3 realistic synthetic number-line worksheet PNG images for Gate 3 evaluation.

Case 1: Canonical Correct — Legible ticks, clear arcs (0 -> -6 -> 6 -> 2), clear arrowheads, final answer 2.
Case 2: Procedural Error — Legible ticks, arc 0 -> -6, arc -6 -> 5 (off-by-one count error), arc 5 -> 1, final answer 1.
Case 3: Ambiguous / Incomplete — Faint ink, missing arrowheads, incomplete stroke ending near 1-2, blank answer.
"""

from __future__ import annotations

import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


def draw_arrowhead(draw: ImageDraw.ImageDraw, tip: tuple[int, int], direction: str, size: int = 10, fill: tuple = (20, 20, 20)):
    x, y = tip
    if direction == "left":
        draw.polygon([(x, y), (x + size, y - size // 2), (x + size, y + size // 2)], fill=fill)
    elif direction == "right":
        draw.polygon([(x, y), (x - size, y - size // 2), (x - size, y + size // 2)], fill=fill)


def draw_arc_with_arrow(
    draw: ImageDraw.ImageDraw,
    x_start: int,
    x_end: int,
    y_baseline: int,
    height: int,
    direction: str,
    width: int = 3,
    fill: tuple = (20, 40, 160),
    draw_arrow: bool = True,
):
    """Draw a parabolic-style arc jump between x_start and x_end above the baseline."""
    left = min(x_start, x_end)
    right = max(x_start, x_end)
    bbox = [left, y_baseline - height, right, y_baseline + height]
    draw.arc(bbox, start=180, end=360, fill=fill, width=width)
    if draw_arrow:
        tip = (x_end, y_baseline)
        arrow_dir = "right" if x_end > x_start else "left"
        draw_arrowhead(draw, tip, arrow_dir, size=12, fill=fill)


def generate_case_01(output_path: Path):
    """Case 1: Canonical Correct (0 -> -6 -> 6 -> 2, final answer 2)."""
    w, h = 1000, 500
    img = Image.new("RGB", (w, h), color=(252, 252, 252))
    draw = ImageDraw.Draw(img)

    # Title & Problem Statement
    draw.text((60, 40), "Math Worksheet: Problem #1065658", fill=(30, 30, 30))
    draw.text((60, 70), "Calculate: -6 + 12 - 4 using the number line.", fill=(70, 70, 70))

    # Number line coordinates
    y_axis = 320
    x_min, x_max = 80, 920
    draw.line([(x_min, y_axis), (x_max, y_axis)], fill=(40, 40, 40), width=4)

    # Ticks from -12 to +12 (step 2)
    ticks = list(range(-12, 14, 2))
    num_ticks = len(ticks)
    dx = (x_max - x_min) / (num_ticks - 1)
    tick_coords = {}
    for i, val in enumerate(ticks):
        x = int(x_min + i * dx)
        tick_coords[val] = x
        draw.line([(x, y_axis - 12), (x, y_axis + 12)], fill=(40, 40, 40), width=3)
        draw.text((x - 8, y_axis + 18), str(val), fill=(40, 40, 40))

    # Hop 1: 0 to -6 (left, height 70)
    draw_arc_with_arrow(draw, tick_coords[0], tick_coords[-6], y_axis, height=80, direction="left", fill=(20, 60, 180))
    mid_x1 = (tick_coords[0] + tick_coords[-6]) // 2
    draw.text((mid_x1 - 10, y_axis - 95), "-6", fill=(20, 60, 180))

    # Hop 2: -6 to +6 (right, height 130)
    draw_arc_with_arrow(draw, tick_coords[-6], tick_coords[6], y_axis, height=140, direction="right", fill=(20, 60, 180))
    mid_x2 = (tick_coords[-6] + tick_coords[6]) // 2
    draw.text((mid_x2 - 14, y_axis - 155), "+12", fill=(20, 60, 180))

    # Hop 3: +6 to +2 (left, height 60)
    draw_arc_with_arrow(draw, tick_coords[6], tick_coords[2], y_axis, height=70, direction="left", fill=(20, 60, 180))
    mid_x3 = (tick_coords[6] + tick_coords[2]) // 2
    draw.text((mid_x3 - 10, y_axis - 85), "-4", fill=(20, 60, 180))

    # Circle terminal position at 2
    x2 = tick_coords[2]
    draw.ellipse([x2 - 14, y_axis - 14, x2 + 14, y_axis + 14], outline=(200, 20, 20), width=3)

    # Answer box
    draw.rectangle([760, 50, 920, 110], outline=(40, 40, 40), width=2)
    draw.text((770, 55), "Answer:", fill=(60, 60, 60))
    draw.text((840, 65), "2", fill=(20, 20, 180))

    img.save(output_path, "PNG")


def generate_case_02(output_path: Path):
    """Case 2: Procedural Error (Off-by-one tick count error landing on 5 instead of 6, final answer 1)."""
    w, h = 1000, 500
    img = Image.new("RGB", (w, h), color=(252, 252, 252))
    draw = ImageDraw.Draw(img)

    draw.text((60, 40), "Math Worksheet: Problem #1065658", fill=(30, 30, 30))
    draw.text((60, 70), "Calculate: -6 + 12 - 4 using the number line.", fill=(70, 70, 70))

    y_axis = 320
    x_min, x_max = 100, 900
    draw.line([(x_min, y_axis), (x_max, y_axis)], fill=(40, 40, 40), width=4)

    # Ticks from -10 to +10 (step 1 for granular off-by-one demonstration)
    ticks = list(range(-10, 11))
    num_ticks = len(ticks)
    dx = (x_max - x_min) / (num_ticks - 1)
    tick_coords = {}
    for i, val in enumerate(ticks):
        x = int(x_min + i * dx)
        tick_coords[val] = x
        is_major = (val % 2 == 0)
        t_len = 12 if is_major else 7
        draw.line([(x, y_axis - t_len), (x, y_axis + t_len)], fill=(40, 40, 40), width=2)
        if is_major:
            draw.text((x - 8, y_axis + 16), str(val), fill=(40, 40, 40))

    # Hop 1: 0 to -6 (correct first step)
    draw_arc_with_arrow(draw, tick_coords[0], tick_coords[-6], y_axis, height=75, direction="left", fill=(20, 60, 180))
    draw.text(((tick_coords[0] + tick_coords[-6]) // 2 - 8, y_axis - 90), "-6", fill=(20, 60, 180))

    # Hop 2: -6 to +5 (miscounted 11 ticks instead of 12, labeled +12)
    draw_arc_with_arrow(draw, tick_coords[-6], tick_coords[5], y_axis, height=135, direction="right", fill=(20, 60, 180))
    draw.text(((tick_coords[-6] + tick_coords[5]) // 2 - 12, y_axis - 150), "+12", fill=(20, 60, 180))

    # Hop 3: +5 to +1 (correct -4 from the errant position 5)
    draw_arc_with_arrow(draw, tick_coords[5], tick_coords[1], y_axis, height=65, direction="left", fill=(20, 60, 180))
    draw.text(((tick_coords[5] + tick_coords[1]) // 2 - 8, y_axis - 80), "-4", fill=(20, 60, 180))

    # Circle terminal position at 1
    x1 = tick_coords[1]
    draw.ellipse([x1 - 12, y_axis - 12, x1 + 12, y_axis + 12], outline=(200, 20, 20), width=3)

    # Answer box with incorrect answer 1
    draw.rectangle([760, 50, 920, 110], outline=(40, 40, 40), width=2)
    draw.text((770, 55), "Answer:", fill=(60, 60, 60))
    draw.text((840, 65), "1", fill=(20, 60, 180))

    img.save(output_path, "PNG")


def generate_case_03(output_path: Path):
    """Case 3: Ambiguous / Incomplete / Faint (Faint strokes, missing arrows, unclear terminus, blank answer)."""
    w, h = 1000, 500
    img = Image.new("RGB", (w, h), color=(248, 248, 245))
    draw = ImageDraw.Draw(img)

    # Faint title
    draw.text((60, 40), "Math Worksheet: Problem #1065658", fill=(120, 120, 120))
    draw.text((60, 70), "Calculate: -6 + 12 - 4 using the number line.", fill=(140, 140, 140))

    y_axis = 320
    x_min, x_max = 120, 880
    draw.line([(x_min, y_axis), (x_max, y_axis)], fill=(130, 130, 130), width=2)

    # Ticks from -8 to +8
    ticks = list(range(-8, 9))
    num_ticks = len(ticks)
    dx = (x_max - x_min) / (num_ticks - 1)
    tick_coords = {}
    for i, val in enumerate(ticks):
        x = int(x_min + i * dx)
        tick_coords[val] = x
        draw.line([(x, y_axis - 8), (x, y_axis + 8)], fill=(130, 130, 130), width=2)
        if val % 2 == 0:
            draw.text((x - 8, y_axis + 14), str(val), fill=(130, 130, 130))

    # Faint Hop 1: 0 to -6, NO ARROWHEAD, faint ink
    draw_arc_with_arrow(
        draw,
        tick_coords[0],
        tick_coords[-6],
        y_axis,
        height=65,
        direction="left",
        width=2,
        fill=(170, 180, 205),
        draw_arrow=False,
    )

    # Incomplete stroke from -6 heading right but terminating in blank space between ticks 1 and 2, NO ARROWHEAD
    mid_ambiguous_x = int(tick_coords[1] + 0.4 * dx)
    draw.arc(
        [tick_coords[-6], y_axis - 110, mid_ambiguous_x, y_axis + 110],
        start=180,
        end=340,
        fill=(160, 170, 195),
        width=2,
    )

    # Smudged/erased pencil marks near center
    for offset in range(-15, 20, 5):
        draw.line(
            [(tick_coords[0] + offset, y_axis - 20), (tick_coords[0] + offset + 8, y_axis + 20)],
            fill=(220, 220, 215),
            width=2,
        )

    # Blank answer box (no number written)
    draw.rectangle([760, 50, 920, 110], outline=(150, 150, 150), width=2)
    draw.text((770, 55), "Answer:", fill=(150, 150, 150))

    img.save(output_path, "PNG")


def main():
    target_dir = Path("tests/fixtures/synthetic_evaluation_cases")
    target_dir.mkdir(parents=True, exist_ok=True)

    case_01 = target_dir / "case_01_canonical_correct.png"
    case_02 = target_dir / "case_02_off_by_one_error.png"
    case_03 = target_dir / "case_03_ambiguous_incomplete.png"

    generate_case_01(case_01)
    generate_case_02(case_02)
    generate_case_03(case_03)

    print(f"Generated synthetic test cases:")
    print(f" - {case_01} ({case_01.stat().st_size} bytes)")
    print(f" - {case_02} ({case_02.stat().st_size} bytes)")
    print(f" - {case_03} ({case_03.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
