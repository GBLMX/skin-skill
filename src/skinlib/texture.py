"""Textures that are not player skins: block faces, item icons, any sprite.

The painting primitives in this package (``shading``, ``patterns``,
``materials``, ``overlay``, ``decoration``) never needed a *skin* -- they need a
canvas that can answer ``region``/``box``/``pixel``/``get_pixel`` and say which
faces it stores (see :func:`skinlib.model.canvas_faces`).  :class:`Texture` is
that canvas, so all of those primitives paint any texture, not just a 64x64
skin.  :func:`block` and :func:`icon` are generators on top of it that encode
the vanilla art conventions:

* **Blocks and items are 16x16**; capes, elytra and armor layers are 64x32.
  Sheets with per-entity sizes (mobs, paintings, GUI widgets) are not listed --
  pass their size to :class:`Texture` directly.
* **A cube needs three textures**: top (lightest), side (mid, reused by all four
  sides), bottom (darkest).  That top-light/bottom-dark rule is what makes a
  flat 16x16 read as a cube before anything renders it in 3D.
* **Biome-tinted sheets are greyscale.**  Grass, foliage and water textures are
  painted in greyscale and multiplied by a biome colour at runtime, so
  generating them in colour double-tints them in game (``tint_ready=True``).
* **Emissive sheets carry their own light.**  A block whose ``emitLight > 0``
  (see :mod:`skinlib.gamedata`) only reads as a light source once the bright
  pixels are pushed past the base colour (``glow=True``).
* **Items are silhouettes, not rectangles.**  An item's readability comes from
  its outline, so :func:`icon` paints through a mask with a 1px transparent
  margin -- one of the ``ICON_ART`` archetypes, or your own callable.

Rendering (``render_*``) and validation stay skin-only: they need the 64x64
body layout, which a flat sheet does not have.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence, Tuple

from PIL import Image, ImageDraw

from . import colors, materials, shading
from ._raster import transform
from .model import Box, Color

# Vanilla texture sizes, in pixels.
TEXTURE_SIZES: Dict[str, Tuple[int, int]] = {
    "block": (16, 16),
    "item": (16, 16),
    "particle": (8, 8),
    "cape": (64, 32),
    "elytra": (64, 32),
    "armor_layer": (64, 32),
}

_ICON_ART_EDGE = 16


def texture_size(kind: str) -> Tuple[int, int]:
    """Return the vanilla ``(width, height)`` for a texture kind."""
    try:
        return TEXTURE_SIZES[kind]
    except KeyError:
        raise ValueError(f"unknown texture kind {kind!r}; "
                         f"choices: {sorted(TEXTURE_SIZES)}") from None


# ---------------------------------------------------------------------------
# Canvas
# ---------------------------------------------------------------------------
class Texture:
    """A paint canvas holding one or more faces, side by side in a row.

    >>> t = Texture(16, 16, faces=("top", "side", "bottom"))   # a 48x16 sheet
    >>> t.region("all", "base", "top")
    (0, 0, 16, 16)

    ``part`` and ``layer`` are accepted and ignored: a texture has no body
    parts and no overlay layer.  A single-face texture answers to *any* face
    name; a multi-face texture raises for a face it does not store.
    """

    def __init__(self, width: int, height: Optional[int] = None, *,
                 faces: Sequence[str] = ("front",),
                 fill: Color = (0, 0, 0, 0)) -> None:
        self.width = int(width)
        self.height = self.width if height is None else int(height)
        self.faces: Tuple[str, ...] = tuple(faces)
        if not self.faces:
            raise ValueError("a texture needs at least one face")
        self.img = Image.new(
            "RGBA", (self.width * len(self.faces), self.height), fill)
        self.draw = ImageDraw.Draw(self.img)
        # Logical pixel == physical pixel; the primitives read ``scale`` to
        # convert their 64px design grid, and a texture has no design grid.
        self.scale = 1

    # -- geometry: the interface the painting primitives use ----------------
    def _offset(self, face: str) -> int:
        """Left edge of ``face``'s tile."""
        try:
            return self.faces.index(face) * self.width
        except ValueError:
            if len(self.faces) == 1:
                return 0
            raise KeyError(f"texture has no face {face!r}; "
                           f"faces: {list(self.faces)}") from None

    def region(self, part, layer, face) -> Tuple[int, int, int, int]:
        return (self._offset(face), 0, self.width, self.height)

    def box(self, part, layer, face) -> Box:
        return Box(*self.region(part, layer, face))

    def pixel(self, part, layer, face, u: int, v: int, color: Color) -> None:
        if not (0 <= u < self.width and 0 <= v < self.height):
            raise ValueError(f"({u},{v}) outside {face} "
                             f"({self.width}x{self.height})")
        self.img.putpixel((self._offset(face) + u, v), color)

    def get_pixel(self, part, layer, face, u: int, v: int) -> Color:
        return self.img.getpixel((self._offset(face) + u, v))

    def paint_face(self, part, layer, face, color: Color) -> None:
        x = self._offset(face)
        self.draw.rectangle(
            (x, 0, x + self.width - 1, self.height - 1), fill=color)

    def paint_part(self, part, color: Color, layer: str = "base") -> None:
        for face in self.faces:
            self.paint_face(part, layer, face, color)

    def face_image(self, part, layer, face) -> Image.Image:
        x = self._offset(face)
        return self.img.crop((x, 0, x + self.width, self.height))

    # -- IO -----------------------------------------------------------------
    def save(self, path) -> Path:
        """Write the sheet (all faces in a row) to one PNG."""
        self.img.save(path)
        return Path(path)

    def save_faces(self, outdir, prefix: str = "texture", *,
                   scale: int = 1) -> List[Path]:
        """Write one PNG per face as ``<outdir>/<prefix>_<face>.png``."""
        out = Path(outdir)
        out.mkdir(parents=True, exist_ok=True)
        written: List[Path] = []
        for face in self.faces:
            img = self.face_image("all", "base", face)
            if scale != 1:
                img = img.resize(
                    (self.width * scale, self.height * scale), Image.NEAREST)
            path = out / f"{prefix}_{face}.png"
            img.save(path)
            written.append(path)
        return written

    @classmethod
    def load(cls, path, faces: Sequence[str] = ("front",)) -> "Texture":
        """Load a texture sheet as one face, or as ``len(faces)`` tiles."""
        img = Image.open(path).convert("RGBA")
        faces = tuple(faces)
        if len(faces) > 1 and img.width != img.height * len(faces):
            raise ValueError(f"{path}: {img.width}x{img.height} is not "
                             f"{len(faces)} tiles wide")
        tex = cls(img.width // len(faces), img.height, faces=faces)
        tex.img = img
        tex.draw = ImageDraw.Draw(img)
        return tex

    def copy(self) -> "Texture":
        tex = Texture(self.width, self.height, faces=self.faces)
        tex.img = self.img.copy()
        tex.draw = ImageDraw.Draw(tex.img)
        return tex

    def __repr__(self) -> str:
        return (f"Texture({self.width}x{self.height}, "
                f"faces={list(self.faces)})")


# ---------------------------------------------------------------------------
# Generators
# ---------------------------------------------------------------------------
BLOCK_FACES: Tuple[str, ...] = ("top", "side", "bottom")

# Vanilla cube lighting, applied before any shading style: the top face catches
# the light, the bottom sits in shadow, the sides fall between.
_FACE_LIGHT: Dict[str, float] = {"top": 1.15, "side": 1.0, "bottom": 0.8}

# Archetype silhouettes for item icons: 16x16, ``#`` = painted.  minebase knows
# an item's name, never its sprite, so these are the honest starting point --
# they are shapes, not any particular vanilla sprite.
ICON_ART: Dict[str, Tuple[str, ...]] = {
    "gem": (
        "................",
        "................",
        ".....######.....",
        "....########....",
        "...##########...",
        "..############..",
        "..############..",
        "..############..",
        "...##########...",
        "...##########...",
        "....########....",
        ".....######.....",
        "......####......",
        ".......##.......",
        "................",
        "................",
    ),
    "shard": (
        "................",
        "......####......",
        ".....######.....",
        "....########....",
        "....########....",
        "....########....",
        "....########....",
        ".....######.....",
        ".....######.....",
        "......####......",
        "......####......",
        ".......##.......",
        ".......##.......",
        "................",
        "................",
        "................",
    ),
    "ingot": (
        "................",
        "................",
        "................",
        ".....########...",
        "....##########..",
        "...############.",
        "..##############",
        "..##############",
        "..##############",
        "...############.",
        "....##########..",
        ".....########...",
        "................",
        "................",
        "................",
        "................",
    ),
    "dust": (
        "................",
        "................",
        "...##......##...",
        "..####....####..",
        "..####....####..",
        "...##......##...",
        "................",
        "......####......",
        ".....######.....",
        ".....######.....",
        "......####......",
        "................",
        "...##.....###...",
        "..####...#####..",
        "..####...#####..",
        "...##.....###...",
    ),
    "orb": (
        "................",
        "................",
        ".....######.....",
        "...##########...",
        "..############..",
        "..############..",
        ".##############.",
        ".##############.",
        ".##############.",
        ".##############.",
        "..############..",
        "..############..",
        "...##########...",
        ".....######.....",
        "................",
        "................",
    ),
}


def _archetype(shape: str, size: int) -> Callable[[int, int], bool]:
    """Return a mask callable for a named archetype, resampled to ``size``."""
    art = ICON_ART.get(shape)
    if art is None:
        raise ValueError(f"unknown icon shape {shape!r}; "
                         f"choices: {sorted(ICON_ART)}")
    edge = _ICON_ART_EDGE
    return lambda u, v: art[min(edge - 1, v * edge // size)][
        min(edge - 1, u * edge // size)] == "#"


def _base_sheet(base: Color, *, faces: Sequence[str], size: int, style: str,
                material: Optional[str], seed: int = 0) -> Texture:
    """Start a sheet: either a named material recipe or a shading style."""
    tex = Texture(size, size, faces=faces, fill=base)
    if material is None:
        if style in shading.STYLE_PROFILES:
            shading.apply_style(tex, "all", base, style, "base", seed=seed)
        else:
            shading.apply_shading(tex, "all", base, "base", style=style)
    else:
        materials.apply_material(tex, "all", material, color=base, seed=seed)
    return tex


def _glow(tex: Texture, strength: float) -> None:
    """Lift an emissive sheet by a flat factor, keeping its structure.

    A *proportional* lift (not a luma ramp, not a screen) preserves the sheet's
    relative structure -- the per-face lighting and grain survive, the top end
    simply clips -- while the sheet as a whole reads as brighter than lit rock.
    ``materials.glow_center`` is the wrong pass here: it overwrites pixels with a
    radial ramp of one colour, which would flatten the per-face lighting this
    module just applied.  The game renders emissive faces full-bright, so this is
    a readability lift, not simulated light.
    """
    transform(tex, "all", "base",
              lambda i, j, px, w, h, f: colors.shade(px, 1.0 + strength))


def _tint_ready(tex: Texture) -> None:
    """Flatten to greyscale so a runtime biome tint multiplies it correctly."""
    transform(tex, "all", "base", lambda i, j, px, w, h, f: colors.gray(px))


def _set_alpha(tex: Texture, alpha: int) -> None:
    """Give every painted pixel one flat alpha (see-through blocks/items)."""
    if alpha >= 255:
        return
    transform(tex, "all", "base",
              lambda i, j, px, w, h, f: (px[0], px[1], px[2], alpha))


def _finish(tex: Texture, *, tint_ready: bool, noise: int, seed: int,
            glow: bool, glow_strength: float, alpha: int) -> Texture:
    """The whole-sheet pass order: tint, grain, bloom, then alpha."""
    if tint_ready:
        _tint_ready(tex)
    if noise:
        shading.fabric_noise(tex, "all", "base", variance=noise, seed=seed)
    if glow:
        _glow(tex, glow_strength)
    _set_alpha(tex, alpha)
    return tex


def block(base: Color, *, faces: Sequence[str] = BLOCK_FACES,
          style: str = "combined", material: Optional[str] = None,
          size: int = 16, noise: int = 0, seed: int = 0, glow: bool = False,
          glow_strength: float = 0.35, tint_ready: bool = False,
          alpha: int = 255) -> Texture:
    """Generate a block's texture sheet from one base colour.

    ``faces`` defaults to the three a cube needs (``top``/``side``/``bottom``);
    pass e.g. ``("top", "side", "bottom", "front")`` when the model has its own
    front texture.  ``style`` is a shading style (``flat``/``vertical``/
    ``cylindrical``/``combined``/``artistic``) or a style profile from
    ``shading.STYLE_PROFILES`` (``minimal``/``clean``/``metal``/``mottled``/
    ``leathery``); ``material`` names a recipe from ``materials.MATERIALS`` and
    overrides ``style``.

    ``noise`` adds fabric grain, ``glow`` blooms the sheet (emissive block),
    ``tint_ready`` returns it greyscale for a runtime biome tint, and ``alpha``
    makes it see-through.
    """
    tex = _base_sheet(base, faces=faces, size=size, style=style,
                      material=material, seed=seed)
    for face, factor in _FACE_LIGHT.items():
        if face in tex.faces:
            transform(tex, "all", "base",
                      lambda i, j, px, w, h, f, k=factor: colors.shade(px, k),
                      faces=(face,))
    return _finish(tex, tint_ready=tint_ready, noise=noise, seed=seed,
                   glow=glow, glow_strength=glow_strength, alpha=alpha)


def icon(base: Color, *, shape: str = "gem",
         mask: Optional[Callable[[int, int], bool]] = None,
         size: int = 16, style: str = "combined",
         material: Optional[str] = None, noise: int = 0, seed: int = 0,
         glow: bool = False, glow_strength: float = 0.35,
         tint_ready: bool = False, alpha: int = 255) -> Texture:
    """Generate a 16x16 item icon: one sprite with a 1px transparent margin.

    The silhouette comes from ``mask`` -- a callable ``(u, v) -> bool`` -- or
    from a named ``ICON_ART`` archetype (``gem``/``shard``/``ingot``/``dust``/
    ``orb``).  Only masked pixels survive; the rest stays transparent, and every
    later pass (tint, grain, bloom, alpha) skips them automatically.
    """
    tex = _base_sheet(base, faces=("front",), size=size, style=style,
                      material=material, seed=seed)
    inside = mask or _archetype(shape, size)
    transform(tex, "all", "base",
              lambda i, j, px, w, h, f: px if (
                  0 < i < size - 1 and 0 < j < size - 1 and inside(i, j)
              ) else (0, 0, 0, 0))
    return _finish(tex, tint_ready=tint_ready, noise=noise, seed=seed,
                   glow=glow, glow_strength=glow_strength, alpha=alpha)


def from_spec(spec, color: Color, *, style: str = "combined",
              material: Optional[str] = None, shape: str = "gem", mask=None,
              size: Optional[int] = None, noise: int = 0, seed: int = 0,
              glow: Optional[bool] = None, glow_strength: float = 0.35,
              tint_ready: Optional[bool] = None, alpha: int = 255) -> Texture:
    """Generate a texture from a :class:`skinlib.gamedata.TextureSpec`.

    The spec carries what minebase actually records -- kind, emit light, biome
    tint group, states -- while the caller supplies the art decision (``color``,
    ``style``/``material``, and for items the silhouette).  ``glow`` and
    ``tint_ready`` default to the registry: emissive blocks bloom, biome-tinted
    blocks (grass/foliage/water) come out greyscale so a runtime tint lands
    right.

    ``spec`` is duck-typed, so this module never imports the optional minebase
    dependency; :func:`generate` is the lazy bridge that looks a name up.
    """
    glow = spec.emissive if glow is None else glow
    tint_ready = bool(spec.tint_group) if tint_ready is None else tint_ready
    size = size or getattr(spec, "size", None) or 16
    common = dict(size=size, style=style, material=material, noise=noise,
                  seed=seed, glow=glow, glow_strength=glow_strength,
                  tint_ready=tint_ready, alpha=alpha)
    if spec.kind == "item":
        return icon(color, shape=shape, mask=mask, **common)
    return block(color, **common)


def generate(name: str, color: Color, *, version: Optional[str] = None,
             edition: Optional[str] = None, **kwargs) -> Texture:
    """Generate the texture for a vanilla registry name (needs minebase).

    Lazy bridge to :mod:`skinlib.gamedata`: look the name up, hand its spec to
    :func:`from_spec`.  ``kwargs`` go to :func:`from_spec`.
    """
    from . import gamedata

    if not gamedata.available():
        raise RuntimeError(gamedata.INSTALL_HINT)
    spec = gamedata.texture_spec(
        name, version, **({} if edition is None else {"edition": edition}))
    return from_spec(spec, color, **kwargs)
