"""The Skin object: pixel access and high-level painting on a Minecraft skin.

A Skin wraps an RGBA image plus a UV layout. All mutation happens through
methods on this class or the functional modules (shading/patterns/...);
rendering and sampling live elsewhere. Pure UV layouts and the region types
live in ``model.py``; the pure-PIL image transforms used by ``Skin.load``
(matte stripping, legacy conversion, model detection) live in
``transforms.py``; color parsing lives in ``colors.py``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Tuple

from PIL import Image, ImageDraw

from .model import Box, Color, Face, FACES, Layer, PARTS, Part, make_layout
from .transforms import detect_model, legacy_to_modern, strip_matte


class Skin:
    """A Minecraft skin. Provides pixel access and high-level painting.

    All mutation happens through methods here or the functional modules
    (shading/patterns). Rendering and sampling live elsewhere.
    """

    def __init__(self, size: int = 64, model: str = "steve",
                 transparent: bool = True):
        if size not in (64, 128):
            raise ValueError("size must be 64 or 128")
        self.size = size
        self.model = model
        self.scale = size // 64
        self.layout = make_layout(model)
        bg = (0, 0, 0, 0) if transparent else (255, 255, 255, 255)
        self.img = Image.new("RGBA", (size, size), bg)
        self.draw = ImageDraw.Draw(self.img)

    # -- region access ------------------------------------------------------
    def box(self, part: Part, layer: Layer, face: Face) -> Box:
        """Return the (scaled) Box for a part/layer/face."""
        b = self.layout[part][layer][face]
        return Box(b.x * self.scale, b.y * self.scale,
                   b.w * self.scale, b.h * self.scale)

    def region(self, part: Part, layer: Layer, face: Face) -> Tuple[int, int, int, int]:
        """Return (x, y, w, h) for a part/layer/face (scaled)."""
        b = self.box(part, layer, face)
        return (b.x, b.y, b.w, b.h)

    # -- pixel access -------------------------------------------------------
    def pixel(self, part: Part, layer: Layer, face: Face, u: int, v: int, color):
        """Paint one logical pixel (64px grid) as a scale-aware block.

        u/v are logical coordinates in the 64px skin layout. On 128px skins
        each logical pixel expands to a ``scale x scale`` block, so callers
        can keep 64px coordinates regardless of resolution.
        """
        x, y, w, h = self.region(part, layer, face)
        lw, lh = w // self.scale, h // self.scale
        if not (0 <= u < lw and 0 <= v < lh):
            raise ValueError(f"({u},{v}) outside {part}/{layer}/{face}")
        x0, y0 = x + u * self.scale, y + v * self.scale
        for du in range(self.scale):
            for dv in range(self.scale):
                self.img.putpixel((x0 + du, y0 + dv), color)

    def get_pixel(self, part: Part, layer: Layer, face: Face, u: int, v: int) -> Color:
        """Return the color of a logical pixel (top-left of its block)."""
        x, y, w, h = self.region(part, layer, face)
        return self.img.getpixel((x + u * self.scale, y + v * self.scale))

    def dump(self, part: Part, face: Face = "front",
             layers: Tuple[Layer, ...] = ("base", "overlay")) -> None:
        """逐 v 打印 part/face 的 base/overlay 像素，调试层次冲突（techniques §15）。

        透明像素显示为 ``·``，不透明显示 R 通道值（3 位对齐），base/overlay 两行
        并排对比，一眼看出谁遮了谁。
        """
        b = self.box(part, "base", face)
        lw, lh = b.w // self.scale, b.h // self.scale
        u = lw // 2
        for layer in layers:
            cells = []
            for v in range(lh):
                c = self.get_pixel(part, layer, face, u, v)
                cells.append(" · " if c[3] == 0 else f"{c[0]:3d}")
            print(f"{part}/{layer}/{face}: " + " ".join(cells))

    # -- face / part painting ----------------------------------------------
    def paint_face(self, part: Part, layer: Layer, face: Face, color):
        x, y, w, h = self.region(part, layer, face)
        # PIL rectangle endpoints are inclusive, so subtract 1 to fill exactly w x h.
        self.draw.rectangle((x, y, x + w - 1, y + h - 1), fill=color)

    def paint_part(self, part: Part, color, layer: Layer = "base"):
        for face in FACES:
            self.paint_face(part, layer, face, color)

    def fill_parts(self, color, parts=PARTS, layer: Layer = "base"):
        for p in parts:
            self.paint_part(p, color, layer)

    # -- face image I/O -----------------------------------------------------
    def face_image(self, part: Part, layer: Layer, face: Face) -> Image.Image:
        x, y, w, h = self.region(part, layer, face)
        return self.img.crop((x, y, x + w, y + h))

    def paste_face(self, part: Part, layer: Layer, face: Face, image: Image.Image):
        x, y, w, h = self.region(part, layer, face)
        if image.size != (w, h):
            image = image.resize((w, h), Image.NEAREST)
        self.img.paste(image, (x, y), image if image.mode == "RGBA" else None)

    # -- layer operations ---------------------------------------------------
    def layer_image(self, layer: Layer) -> Image.Image:
        """Extract one layer (other areas transparent)."""
        out = Image.new("RGBA", (self.size, self.size), (0, 0, 0, 0))
        for part in PARTS:
            for face in FACES:
                x, y, w, h = self.region(part, layer, face)
                out.paste(self.img.crop((x, y, x + w, y + h)), (x, y))
        return out

    def flatten(self) -> "Skin":
        """Bake overlay onto base into a new single-layer skin."""
        flat = Skin(size=self.size, model=self.model)
        base = self.layer_image("base")
        over = self.layer_image("overlay")
        flat.img = Image.alpha_composite(base, over)
        flat.draw = ImageDraw.Draw(flat.img)
        # clear overlay in flat result
        for part in PARTS:
            for face in FACES:
                flat.paint_face(part, "overlay", face, (0, 0, 0, 0))
        return flat

    # -- IO -----------------------------------------------------------------
    def save(self, path: str) -> Path:
        self.img.save(path)
        return Path(path)

    @classmethod
    def load(cls, path: str, model: str = "auto") -> "Skin":
        img = Image.open(path).convert("RGBA")
        if img.size not in ((64, 64), (128, 128), (64, 32)):
            raise ValueError("skin must be 64x64, 128x128, or 64x32")
        img = strip_matte(img)
        if img.size == (64, 32):
            img = legacy_to_modern(img)
        if model == "auto":
            model = detect_model(img)
        s = cls(size=img.size[0], model=model)
        s.img = img
        s.draw = ImageDraw.Draw(img)
        return s


# Convenience aliases
def create(size: int = 64, model: str = "steve") -> Skin:
    return Skin(size=size, model=model)


def load(path: str, model: str = "auto") -> Skin:
    return Skin.load(path, model)
