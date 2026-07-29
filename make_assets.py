#!/usr/bin/env python3
"""Generate the app icons and the social share image.

    python make_assets.py

Run this on a dev machine after changing BRAND or the palette, then commit what
it writes. The cloud routines never call it — they only ever touch add.py, which
stays stdlib. That is deliberate: asset generation needs Pillow and a font, and
neither of those should be a dependency of the 4:50am news run.

The mark is a sun clearing the horizon. It reads at 16px, it survives being
masked into a circle or a squircle on Android, and it says the one thing the
brand is about without needing a letterform.
"""

import os

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ICONS = os.path.join(HERE, "icons")

BRAND = "Brighter"
TAGLINE = "news for a brighter future"

PAPER = (251, 250, 248)
INK = (27, 26, 24)
MUTED = (108, 104, 98)
ACCENT = (180, 83, 31)
ACCENT_LIGHT = (224, 138, 81)
LINE = (230, 226, 220)

SERIF = r"C:\Windows\Fonts\georgiab.ttf"
SANS = r"C:\Windows\Fonts\segoeui.ttf"


def lerp(a, b, t):
    return tuple(round(x + (y - x) * t) for x, y in zip(a, b))


def sun_mark(size, inset=0.0):
    """The icon artwork at any size.

    `inset` shrinks the artwork toward the centre. Android maskable icons can
    have up to 20% cropped off every edge, so the maskable variant is drawn
    small inside a full-bleed field rather than risking a clipped sun.
    """
    # Supersample, then downscale. Cheaper than writing an antialiaser.
    s = size * 4
    img = Image.new("RGB", (s, s), ACCENT)
    d = ImageDraw.Draw(img)

    # Vertical warm gradient: deeper at the top, lighter toward the horizon.
    for y in range(s):
        d.line([(0, y), (s, y)], fill=lerp(ACCENT, ACCENT_LIGHT, y / s))

    scale = 1.0 - inset
    cx, cy = s / 2, s * 0.5
    r = s * 0.195 * scale

    # The sun itself.
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=PAPER)

    # Horizon rule, broken either side of the disc so the sun reads as rising
    # through it rather than sitting on a shelf. It has to be long enough to
    # read as a horizon — short stubs just look like stray marks.
    hy = cy + r * 0.82
    w = s * 0.032 * scale
    ext = s * 0.40 * scale
    gap = r * 1.02
    for x0, x1 in [(cx - ext, cx - gap), (cx + gap, cx + ext)]:
        d.rounded_rectangle([x0, hy - w / 2, x1, hy + w / 2], radius=w / 2,
                            fill=PAPER)

    return img.resize((size, size), Image.LANCZOS)


def write_icons():
    os.makedirs(ICONS, exist_ok=True)
    written = []
    for size in (180, 192, 512):
        p = os.path.join(ICONS, "icon-%d.png" % size)
        sun_mark(size).save(p, optimize=True)
        written.append(p)
    for size in (192, 512):
        p = os.path.join(ICONS, "maskable-%d.png" % size)
        sun_mark(size, inset=0.22).save(p, optimize=True)
        written.append(p)

    # Favicon, multi-resolution so browser tabs and bookmarks both look right.
    p = os.path.join(HERE, "favicon.ico")
    sun_mark(64).save(p, sizes=[(16, 16), (32, 32), (48, 48), (64, 64)])
    written.append(p)
    return written


def write_og():
    """1200x630 card for links pasted into socials and chat."""
    W, H = 1200, 630
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)

    mark = sun_mark(150)
    img.paste(mark, (96, 150))

    brand_f = ImageFont.truetype(SERIF, 96)
    tag_f = ImageFont.truetype(SANS, 34)
    foot_f = ImageFont.truetype(SANS, 26)

    d.text((286, 168), BRAND, font=brand_f, fill=INK)
    d.text((290, 286), TAGLINE, font=tag_f, fill=ACCENT)

    d.line([(96, 470), (W - 96, 470)], fill=LINE, width=2)
    d.text((96, 500), "Good news, three times a day. Every story links to the "
                      "outlet that reported it.", font=foot_f, fill=MUTED)

    p = os.path.join(HERE, "og.png")
    img.save(p, optimize=True)
    return p


if __name__ == "__main__":
    for path in write_icons() + [write_og()]:
        print("wrote", os.path.relpath(path, HERE))
