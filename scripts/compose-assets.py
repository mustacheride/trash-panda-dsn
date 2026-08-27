#!/usr/bin/env python3
"""Compose runtime dice faces and the dumpster wrap from assets/sources."""

from __future__ import annotations

import random
from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter, ImageOps

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "assets" / "sources"
SIZE = 256
CREAM = (245, 240, 230)
WHITE = (255, 255, 255)
DUMPSTER = (61, 92, 74)
TRASH_CAN = (255, 48, 130)
ORANGE = (196, 92, 38)
FACE_ICON_BOX = 128
RESERVED_ICONS = {"gi-raccoon-head.png", "gi-trash-can.png"}
DIE_COUNTS = {
    "d4": 4,
    "d6": 6,
    "d8": 8,
    "d10": 10,
    "d12": 12,
    "d20": 20,
    "d100": 10,
}
DIE_SEEDS = {
    "d4": 4,
    "d6": 6,
    "d8": 8,
    "d10": 10,
    "d12": 12,
    "d20": 20,
    "d100": 100,
}


def clamp(value: int) -> int:
    return max(0, min(255, value))


def save_webp(image: Image.Image, relative: str) -> None:
    path = ROOT / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    image.convert("RGBA").save(path, "WEBP", quality=92, method=4)


def save_png(image: Image.Image, relative: str) -> None:
    path = ROOT / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    image.convert("RGBA").save(path, "PNG", optimize=True)


def noise(base: tuple[int, int, int], variation: int, seed: int) -> Image.Image:
    rng = random.Random(seed)
    image = Image.new("RGB", (SIZE, SIZE))
    pixels = image.load()
    for y in range(SIZE):
        for x in range(SIZE):
            jitter = rng.randint(-variation, variation)
            pixels[x, y] = (
                clamp(base[0] + jitter),
                clamp(base[1] + jitter),
                clamp(base[2] + jitter),
            )
    return image.filter(ImageFilter.GaussianBlur(radius=0.7))


def load_rgba(name: str) -> Image.Image:
    return Image.open(SRC / name).convert("RGBA")


def tint_white_icon(image: Image.Image, color: tuple[int, int, int] = WHITE) -> Image.Image:
    image = image.convert("RGBA")
    tinted = Image.new("RGBA", image.size, (*color, 0))
    tinted.putalpha(image.getchannel("A"))
    return tinted


def fit_on_canvas(image: Image.Image, box: int, opacity: float = 1.0) -> Image.Image:
    fitted = ImageOps.contain(image, (box, box), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    x = (SIZE - fitted.width) // 2
    y = (SIZE - fitted.height) // 2
    if opacity < 1:
        alpha = fitted.getchannel("A").point(lambda v: int(v * opacity))
        fitted.putalpha(alpha)
    canvas.paste(fitted, (x, y), fitted)
    return canvas


def bump_from(image: Image.Image) -> Image.Image:
    gray = ImageOps.grayscale(image.convert("RGB"))
    gray = ImageEnhance.Contrast(gray).enhance(1.4)
    return Image.merge("RGB", (gray, gray, gray))


def dumpster_texture(trash: Image.Image) -> Image.Image:
    base = noise(DUMPSTER, 18, seed=365).convert("RGBA")
    base.alpha_composite(fit_on_canvas(trash, 190, opacity=0.16))
    return base.convert("RGB")


def load_middle_pool() -> list[Image.Image]:
    pool = []
    for path in sorted(SRC.glob("gi-*.png")):
        if path.name in RESERVED_ICONS:
            continue
        pool.append(tint_white_icon(load_rgba(path.name), WHITE))
    if len(pool) < 18:
        raise RuntimeError(f"Need at least 18 scavenger icons for a d20, found {len(pool)}")
    return pool


def icon_face(icon: Image.Image) -> Image.Image:
    return fit_on_canvas(icon, FACE_ICON_BOX, opacity=1.0)


def faces_for(die: str, min_icon: Image.Image, max_icon: Image.Image, pool: list[Image.Image]) -> list[Image.Image]:
    count = DIE_COUNTS[die]
    rng = random.Random(DIE_SEEDS[die])
    bag = pool[:]
    rng.shuffle(bag)
    needed = count - 2
    while len(bag) < needed:
        extra = pool[:]
        rng.shuffle(extra)
        bag.extend(extra)
    return [min_icon, *bag[:needed], max_icon]


def main() -> None:
    raccoon_head = tint_white_icon(load_rgba("gi-raccoon-head.png"), ORANGE)
    trash_mark = tint_white_icon(load_rgba("gi-trash-can.png"), CREAM)
    trash = tint_white_icon(load_rgba("gi-trash-can.png"), TRASH_CAN)
    pool = load_middle_pool()

    dumpster = dumpster_texture(trash_mark)
    save_webp(dumpster, "assets/textures/trash-panda-dumpster.webp")
    save_webp(bump_from(dumpster), "assets/textures/trash-panda-dumpster-bump.webp")

    for die in DIE_COUNTS:
        faces = faces_for(die, trash, raccoon_head, pool)
        for index, icon in enumerate(faces, start=1):
            save_png(icon_face(icon), f"assets/faces/{die}/{index:02d}.png")

    print(f"Composed icon-only faces for {', '.join(DIE_COUNTS)} using {len(pool)} scavenger icons")


if __name__ == "__main__":
    main()
