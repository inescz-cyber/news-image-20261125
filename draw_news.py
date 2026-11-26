#!/usr/bin/env python3
"""Draw the supplied 25 November news brief locally using Pillow and shapes."""

from pathlib import Path
import json
import math

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
SIZE = (1024, 1024)
NAVY = "#0F1B2D"
INK = "#142136"
BODY = "#25364A"
TITLE = "THE WORLD IN ONE DAY"
DATE = "Wednesday, 25 November 2026"
STORIES = (
    {
        "tag": "TRADE",
        "headline": "US proposes tariffs on 14 major economies",
        "subline": "Targets factory overcapacity; highest rates hit China.",
        "accent": "#176C83",
        "icon": "bars",
    },
    {
        "tag": "MIDDLE EAST",
        "headline": "Houthis hit tower in Riyadh’s financial district",
        "subline": "11 wounded; also claim Saudi Arabia’s largest oil refinery, Ras Tanura, attacked.",
        "accent": "#9D3E29",
        "icon": "tower",
    },
    {
        "tag": "SPACE",
        "headline": "China launches Shenzhou-24 with Pakistani astronaut",
        "subline": "Muhammad Zeeshan Ali set to be Tiangong’s first foreign crew member.",
        "accent": "#355CAC",
        "icon": "rocket",
    },
    {
        "tag": "TECH & LAW",
        "headline": "Huawei convicted in US criminal trial",
        "subline": "Iran business case: reportedly convicted on 10 of 12 counts.",
        "accent": "#75458B",
        "icon": "court",
    },
    {
        "tag": "PACIFIC",
        "headline": "Solomon Islands signs Australia security treaty",
        "subline": "Treaty names Australia its primary security partner.",
        "accent": "#24694E",
        "icon": "treaty",
    },
)
FOOTER_LABEL = "Also on 25 Nov:"
FOOTER_ITEMS = (
    "At least 30 killed in a fuel-tanker fire on Cairo’s ring road.",
    "Bangladesh raises garment workers’ minimum wage 36% after protests.",
)


def font(size, bold=False):
    """Prefer installed Liberation Sans, then DejaVu, then Pillow's fallback."""
    name = "Bold" if bold else "Regular"
    candidates = (
        f"/usr/share/fonts/truetype/liberation/LiberationSans-{name}.ttf",
        f"/usr/share/fonts/truetype/liberation2/LiberationSans-{name}.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold
        else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    )
    for candidate in candidates:
        if Path(candidate).is_file():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default(size=size)


def wrap(draw, text, face, width):
    """Wrap at word boundaries and reject words that cannot fit."""
    lines = []
    current = ""
    for word in text.split():
        if draw.textlength(word, font=face) > width:
            raise ValueError(f"Word exceeds text area: {word}")
        trial = f"{current} {word}".strip()
        if current and draw.textlength(trial, font=face) > width:
            lines.append(current)
            current = word
        else:
            current = trial
    if current:
        lines.append(current)
    return lines


def text_block(draw, text, xy, face, color, width, line_height, bounds, audit):
    """Measure every rendered line, checking containment and text collisions."""
    x, y = xy
    lines = wrap(draw, text, face, width)
    for index, line in enumerate(lines):
        at = (x, y + index * line_height)
        box = draw.textbbox(at, line, font=face, anchor="lt")
        assert bounds[0] <= box[0] and bounds[1] <= box[1], (text, box)
        assert box[2] <= bounds[2] and box[3] <= bounds[3], (text, box)
        for previous in audit:
            old = previous["box"]
            overlaps = box[0] < old[2] and box[2] > old[0] and box[1] < old[3] and box[3] > old[1]
            assert not overlaps, (line, previous["line"])
        draw.text(at, line, font=face, fill=color, anchor="lt")
        audit.append({"line": line, "box": box})
    return y + len(lines) * line_height


def icon(draw, kind, x, y, color):
    """Draw small geometric symbols; icons stay in the reserved tag row."""
    if kind == "bars":
        draw.line((x, y + 80, x + 94, y + 80), fill=color, width=4)
        for offset, height in ((8, 28), (37, 49), (66, 72)):
            draw.rectangle((x + offset, y + 80 - height, x + offset + 18, y + 75), fill=color)
    elif kind == "tower":
        draw.rectangle((x + 10, y + 8, x + 32, y + 51), outline=color, width=3)
        draw.line((x + 21, y + 2, x + 21, y + 8), fill=color, width=3)
        for row in (17, 27, 37):
            draw.line((x + 17, y + row, x + 25, y + row), fill=color, width=3)
        for angle in range(0, 360, 45):
            a = math.radians(angle)
            draw.line((x + 47 + 6 * math.cos(a), y + 14 + 6 * math.sin(a),
                       x + 47 + 12 * math.cos(a), y + 14 + 12 * math.sin(a)), fill=color, width=2)
    elif kind == "rocket":
        draw.polygon(((x + 30, y), (x + 16, y + 24), (x + 44, y + 24)), fill=color)
        draw.rectangle((x + 16, y + 23, x + 44, y + 40), fill=color)
        draw.polygon(((x + 16, y + 29), (x + 7, y + 46), (x + 16, y + 41)), fill=color)
        draw.polygon(((x + 44, y + 29), (x + 53, y + 46), (x + 44, y + 41)), fill=color)
        draw.polygon(((x + 22, y + 44), (x + 30, y + 56), (x + 38, y + 44)), fill="#C05A20")
        draw.ellipse((x + 25, y + 22, x + 35, y + 32), fill="white")
    elif kind == "court":
        draw.polygon(((x + 2, y + 15), (x + 30, y + 1), (x + 58, y + 15)), fill=color)
        for column in (10, 27, 44):
            draw.rectangle((x + column, y + 21, x + column + 6, y + 45), fill=color)
        draw.line((x + 5, y + 49, x + 57, y + 49), fill=color, width=4)
        draw.line((x + 1, y + 55, x + 61, y + 55), fill=color, width=3)
    elif kind == "treaty":
        # A folded document with a seal reads clearly as a treaty.
        draw.line(((x + 12, y + 1), (x + 37, y + 1), (x + 50, y + 14),
                   (x + 50, y + 55), (x + 12, y + 55), (x + 12, y + 1)),
                  fill=color, width=3)
        draw.line(((x + 37, y + 1), (x + 37, y + 14), (x + 50, y + 14)),
                  fill=color, width=3)
        draw.ellipse((x + 24, y + 33, x + 38, y + 47), outline=color, width=3)


def draw_card(draw, story, box, wide, audit):
    x0, y0, x1, y1 = box
    draw.rounded_rectangle(box, radius=14, fill="white")
    inner = (x0 + 22, y0 + 18, x1 - 22, y1 - 18)
    text_block(draw, story["tag"], (inner[0], y0 + 21), font(22, True),
               story["accent"], 300, 27, inner, audit)
    if wide:
        icon(draw, story["icon"], x1 - 125, y0 + 41, story["accent"])
        width = x1 - x0 - 172
        bottom = text_block(draw, story["headline"], (inner[0], y0 + 58),
                            font(36, True), INK, width, 41, inner, audit)
        text_block(draw, story["subline"], (inner[0], bottom + 12), font(24),
                   BODY, width, 28, inner, audit)
    else:
        icon(draw, story["icon"], x1 - 86, y0 + 14, story["accent"])
        width = x1 - x0 - 44
        bottom = text_block(draw, story["headline"], (inner[0], y0 + 75),
                            font(34, True), INK, width, 38, inner, audit)
        text_block(draw, story["subline"], (inner[0], bottom + 13), font(25),
                   BODY, width, 30, inner, audit)


def labels():
    """Expose exactly the printed labels for reproducible editorial review."""
    return {
        "title": TITLE,
        "date": DATE,
        "stories": [{key: s[key] for key in ("tag", "headline", "subline")} for s in STORIES],
        "footer_label": FOOTER_LABEL,
        "footer_items": FOOTER_ITEMS,
    }


def main():
    canvas = Image.new("RGB", SIZE, NAVY)
    draw = ImageDraw.Draw(canvas)
    audit = []
    page = (28, 20, 996, 1020)
    text_block(draw, TITLE, (28, 30), font(64, True), "white", 968, 72, page, audit)
    text_block(draw, DATE, (30, 112), font(40, True), "#D7E8F4", 966, 46, page, audit)
    boxes = ((28, 180, 996, 341), (28, 357, 504, 631),
             (520, 357, 996, 631), (28, 647, 504, 921), (520, 647, 996, 921))
    for index, (story, box) in enumerate(zip(STORIES, boxes)):
        assert len(story["headline"].split()) <= 8
        assert len(story["subline"].split()) <= 12
        draw_card(draw, story, box, index == 0, audit)
    draw.line((30, 938, 994, 938), fill="#496079", width=1)
    text_block(draw, FOOTER_LABEL, (30, 950), font(20, True), "white", 964, 24, page, audit)
    for index, item in enumerate(FOOTER_ITEMS):
        text_block(draw, item, (30, 976 + index * 23), font(20), "#E0E8F0", 964, 23, page, audit)
    output = ROOT / "entry.png"
    canvas.save(output, format="PNG", optimize=True, compress_level=9)
    with Image.open(output) as check:
        check.load()
        assert check.format == "PNG" and check.size == SIZE
    assert output.stat().st_size <= 1_048_576
    print(json.dumps(labels(), ensure_ascii=False, indent=2))
    print(f"PASS: {len(audit)} text lines contained and non-overlapping")
    print(f"PNG: {SIZE[0]}x{SIZE[1]}; {output.stat().st_size} bytes")


if __name__ == "__main__":
    main()
