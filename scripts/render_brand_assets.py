"""Render the approved ButtumAI vector mark into transparent PNG assets."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_ROOT / "assets" / "brand"
FONT_PATH = Path(r"C:\Windows\Fonts\malgunbd.ttf")

GREEN = "#176b4d"
MINT = "#68bd94"
INK = "#17211d"
DARK = "#101512"
WHITE = "#ffffff"
OFF_WHITE = "#eef4f0"


def cubic_point(points: tuple[tuple[float, float], ...], t: float) -> tuple[float, float]:
    p0, p1, p2, p3 = points
    u = 1 - t
    return (
        u**3 * p0[0] + 3 * u**2 * t * p1[0] + 3 * u * t**2 * p2[0] + t**3 * p3[0],
        u**3 * p0[1] + 3 * u**2 * t * p1[1] + 3 * u * t**2 * p2[1] + t**3 * p3[1],
    )


def draw_mark(size: int, fill: str, line: str) -> Image.Image:
    scale = size / 64
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((0, 0, size - 1, size - 1), radius=round(14 * scale), fill=fill)
    width = max(1, round(4 * scale))
    curve = ((13, 32), (22, 32), (28, 30), (35, 27))
    curve2 = ((35, 27), (42, 24), (47, 19), (52, 14))
    points = [cubic_point(curve, i / 32) for i in range(33)]
    points.extend(cubic_point(curve2, i / 32) for i in range(1, 33))
    draw.line([(round(x * scale), round(y * scale)) for x, y in points], fill=line, width=width, joint="curve")
    for segment in (((20, 49), (30, 49)), ((25, 49), (25, 32)), ((36, 49), (46, 49)), ((41, 49), (41, 24))):
        draw.line(
            [(round(x * scale), round(y * scale)) for x, y in segment],
            fill=line,
            width=width,
        )
    radius = width // 2
    for x, y in ((13, 32), (52, 14), (20, 49), (30, 49), (25, 32), (36, 49), (46, 49), (41, 24)):
        cx, cy = round(x * scale), round(y * scale)
        draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), fill=line)
    return image


def draw_lockup(fill: str, line: str, text_fill: str) -> Image.Image:
    width, height = 1600, 427
    image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    mark_size = 320
    image.alpha_composite(draw_mark(mark_size, fill, line), (40, 54))
    font = ImageFont.truetype(str(FONT_PATH), 208)
    draw = ImageDraw.Draw(image)
    text = "버팀AI"
    text_box = draw.textbbox((0, 0), text, font=font)
    text_height = text_box[3] - text_box[1]
    text_y = (height - text_height) // 2 - text_box[1]
    draw.text((420, text_y), text, font=font, fill=text_fill)
    return image


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    draw_mark(1024, GREEN, WHITE).save(OUTPUT_DIR / "buteomai-mark.png", optimize=True)
    draw_mark(1024, MINT, DARK).save(OUTPUT_DIR / "buteomai-mark-dark.png", optimize=True)
    draw_lockup(GREEN, WHITE, INK).save(OUTPUT_DIR / "buteomai-logo-horizontal.png", optimize=True)
    draw_lockup(MINT, DARK, OFF_WHITE).save(OUTPUT_DIR / "buteomai-logo-horizontal-dark.png", optimize=True)


if __name__ == "__main__":
    main()
