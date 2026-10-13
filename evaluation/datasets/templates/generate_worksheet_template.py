"""Generates a standardized printable worksheet template for ClassLens evaluation."""

import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


def generate_template() -> Path:
    out_dir = Path("evaluation/datasets/templates")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "blank_worksheet_template.png"

    width, height = 1400, 900
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)

    # Outer border
    draw.rectangle([(20, 20), (width - 20, height - 20)], outline="#2B2D42", width=3)

    # Header section
    draw.rectangle([(20, 20), (width - 20, 110)], fill="#F8F9FA", outline="#2B2D42", width=2)
    draw.text((40, 35), "ClassLens Assessment Platform — Secondary 1 Mathematics", fill="#1D3557")
    draw.text((40, 65), "Topic: Integer Addition & Subtraction on Number Lines | Problem Ref: #1065658", fill="#457B9D")
    draw.text((1000, 45), "Sample ID: _______________", fill="#2B2D42")
    draw.text((1000, 75), "Date: _______________", fill="#2B2D42")

    # Problem statement
    draw.rectangle([(40, 130), (width - 40, 210)], fill="#EBF4F6", outline="#077A90", width=2)
    draw.text((60, 145), "PROBLEM STATEMENT:", fill="#077A90")
    draw.text((60, 175), "Evaluate the following expression using the number line below:   -6 + 12 - 4", fill="#1D3557")

    # Working instructions
    draw.text(
        (40, 230),
        "Instructions: Draw clear arc hops on the number line to show your working. Write your final answer in the box.",
        fill="#555555",
    )

    # Number line geometry
    # Spanning -10 to +10 (21 tick marks)
    nl_y = 520
    nl_x_start = 100
    nl_x_end = width - 100
    step_px = (nl_x_end - nl_x_start) / 20.0

    # Main horizontal axis with arrows
    draw.line([(nl_x_start - 20, nl_y), (nl_x_end + 20, nl_y)], fill="#1D3557", width=4)
    # Left arrow
    draw.polygon([(nl_x_start - 25, nl_y), (nl_x_start - 10, nl_y - 8), (nl_x_start - 10, nl_y + 8)], fill="#1D3557")
    # Right arrow
    draw.polygon([(nl_x_end + 25, nl_y), (nl_x_end + 10, nl_y - 8), (nl_x_end + 10, nl_y + 8)], fill="#1D3557")

    # Tick marks and labels
    for i, val in enumerate(range(-10, 11)):
        x = nl_x_start + i * step_px
        is_major = (val % 2 == 0)
        tick_h = 24 if is_major else 14
        draw.line([(x, nl_y - tick_h), (x, nl_y + tick_h)], fill="#1D3557", width=3 if is_major else 2)

        # Label
        lbl = str(val)
        lbl_x = x - (len(lbl) * 4)
        draw.text((lbl_x, nl_y + 28), lbl, fill="#1D3557")

    # Light dashed guide area above number line for hops
    draw.text((nl_x_start, 300), "[ Working Area: Draw your hops here ]", fill="#CCCCCC")

    # Answer box
    box_x1 = width - 360
    box_y1 = height - 160
    box_x2 = width - 60
    box_y2 = height - 50
    draw.rectangle([(box_x1, box_y1), (box_x2, box_y2)], fill="#FAFAFA", outline="#1D3557", width=3)
    draw.text((box_x1 + 20, box_y1 + 40), "Final Answer:", fill="#1D3557")
    draw.rectangle([(box_x1 + 140, box_y1 + 15), (box_x2 - 20, box_y2 - 15)], fill="white", outline="#E63946", width=2)

    image.save(out_path, "PNG")
    print(f"Generated template at: {out_path}")
    return out_path


if __name__ == "__main__":
    generate_template()
