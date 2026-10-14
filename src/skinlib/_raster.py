"""Internal per-face raster helpers for skinlib.

Every shading / pattern / grain pass used to hand-write the same skeleton::

    for face in canvas_faces(skin):
        x, y, w, h = skin.region(part, layer, face)
        for i in range(w):
            for j in range(h):
                ... putpixel / getpixel ...

These helpers centralize that iteration so the math lives alone in each
callback. Pixel semantics are **physical**: faces are rasterized at the
skin's real resolution (64 or 128), so a converted pass produces
byte-identical output to the hand-written loop it replaces. Callbacks that
need the 64px design grid index it via ``i // skin.scale``.

This module is private (underscore) and never re-exported by
``skinlib.__init__``.
"""

from __future__ import annotations

from typing import Callable, Iterable, Optional, Tuple

from .model import canvas_faces
from .skin import Skin

Face = str
Color = Tuple[int, int, int, int]

# Callbacks receive face-local physical offsets plus the face's physical
# width/height so per-face falloff math stays a pure function of (i, j, w, h).
RowColor = Callable[[int, int, int, str], Optional[Color]]
PxColor = Callable[[int, int, int, int, str], Optional[Color]]
PxTransform = Callable[[int, int, Color, int, int, str], Color]


def face_boxes(skin: Skin, part: str, layer: str = "base",
               faces: Optional[Iterable[str]] = None):
    """Yield (face, x, y, w, h) physical regions for part/layer faces.

    ``faces=None`` (the default) means "every face this canvas has", i.e.
    ``canvas_faces(skin)`` — six for a skin, fewer for a standalone texture.
    """
    for face in (canvas_faces(skin) if faces is None else faces):
        x, y, w, h = skin.region(part, layer, face)
        yield face, x, y, w, h


def rows(skin: Skin, part: str, layer: str, row_color: RowColor,
         faces: Optional[Iterable[str]] = None) -> Skin:
    """Paint each face row-by-row; ``row_color(j, w, h, face)`` gives color.

    ``None`` skips that row. Byte-equivalent to drawing a full-width
    horizontal line per row.
    """
    for face, x, y, w, h in face_boxes(skin, part, layer, faces):
        for j in range(h):
            c = row_color(j, w, h, face)
            if c is None:
                continue
            for i in range(w):
                skin.img.putpixel((x + i, y + j), c)
    return skin


def cols(skin: Skin, part: str, layer: str, col_color: RowColor,
         faces: Optional[Iterable[str]] = None) -> Skin:
    """Paint each face column-by-column; ``col_color(i, w, h, face)``."""
    for face, x, y, w, h in face_boxes(skin, part, layer, faces):
        for i in range(w):
            c = col_color(i, w, h, face)
            if c is None:
                continue
            for j in range(h):
                skin.img.putpixel((x + i, y + j), c)
    return skin


def pixels(skin: Skin, part: str, layer: str, color_for: PxColor,
           faces: Optional[Iterable[str]] = None) -> Skin:
    """Paint every pixel of each face with ``color_for(i, j, w, h, face)``.

    ``None`` skips the write (transparent areas stay untouched). Single-pass
    pure-write variant; later calls may overwrite earlier ones.
    """
    for face, x, y, w, h in face_boxes(skin, part, layer, faces):
        for i in range(w):
            for j in range(h):
                c = color_for(i, j, w, h, face)
                if c is not None:
                    skin.img.putpixel((x + i, y + j), c)
    return skin


def transform(skin: Skin, part: str, layer: str, op: PxTransform,
              faces: Optional[Iterable[str]] = None) -> Skin:
    """Read-modify-write each **opaque** pixel: ``op(i, j, px, w, h, face)``.

    Transparent pixels are left alone (checked before calling ``op``).
    """
    for face, x, y, w, h in face_boxes(skin, part, layer, faces):
        for i in range(w):
            for j in range(h):
                px = skin.img.getpixel((x + i, y + j))
                if px[3] == 0:
                    continue
                skin.img.putpixel((x + i, y + j), op(i, j, px, w, h, face))
    return skin
