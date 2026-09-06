"""Pure-PIL image transforms for Minecraft skins.

Functions here operate directly on a raw PIL image with zero dependencies on
the rest of skinlib: stripping solid-color alpha mattes, converting legacy
64x32 skins to the modern 64x64 layout, and heuristically detecting the
steve/alex model. The Skin object (``skin.py``) and the validator use these;
painting and rendering never do.
"""

from __future__ import annotations

from PIL import Image


def legacy_to_modern(img: Image.Image) -> Image.Image:
    """Convert a legacy 64x32 skin to the modern 64x64 layout.

    Legacy skins store a single (right) arm and leg texture, which the game
    mirrors onto both sides, and have no overlay layer. The head/body base
    faces already share coordinates with the modern layout, so the 64x32
    sheet is pasted into the top half, and the right arm/leg blocks are
    copied into the left arm/leg base regions.
    """
    out = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    out.paste(img, (0, 0))                              # head, body, right arm/leg
    out.paste(img.crop((40, 16, 56, 32)), (32, 48))     # right arm -> left arm
    out.paste(img.crop((0, 16, 16, 32)), (16, 48))      # right leg -> left leg
    return out


def detect_model(img: Image.Image) -> str:
    """Detect 'steve' (4px arms) vs 'alex' (3px slim arms) heuristically.

    Slim (Alex) skins leave a 1px transparent column in the right-arm band —
    the gap between the left and back faces — while Steve skins fill all 16
    columns. Sample column x=50 across the vertical arm faces.
    """
    opaque = 0
    for y in (22, 24, 26, 28, 30):
        if img.getpixel((50, y))[3] > 16:
            opaque += 1
    return "steve" if opaque >= 3 else "alex"


def strip_matte(img: Image.Image) -> Image.Image:
    """Remove a solid-color alpha matte, per the Minecraft skin convention.

    Mojang serves many skins with a *matte*: the exact RGBA of the top-left
    pixel marks "transparent" instead of a real alpha channel (see
    https://github.com/minotar/skin-spec). If the top-left pixel is opaque,
    every pixel equal to it becomes fully transparent. No-op for skins that
    already use a real alpha channel (top-left alpha == 0).
    """
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    key = img.getpixel((0, 0))
    if key[3] == 0:
        return img
    px = img.load()
    for y in range(img.height):
        for x in range(img.width):
            if px[x, y] == key:
                px[x, y] = (key[0], key[1], key[2], 0)
    return img
