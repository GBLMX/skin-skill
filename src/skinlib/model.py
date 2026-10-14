"""Core data model: pure UV layout data and region types.

This module holds only data and layout geometry — no rendering, painting, or
image logic. The region types (Part/Layer/Face/Color), the region constants
(PARTS/LAYERS/FACES), the UV region ``Box``, and the Steve/Alex layouts
(``SteveLayout``, ``_slim_arms``, ``make_layout``) live here.

Painting lives in ``skin.py`` (the Skin object), pure-PIL image transforms
(matte stripping, legacy conversion, model detection) in ``transforms.py``,
and color parsing in ``colors.py``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Literal, Tuple

# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------
Part = Literal["head", "body", "right_arm", "left_arm", "right_leg", "left_leg"]
Layer = Literal["base", "overlay"]
Face = Literal["front", "right", "top", "bottom", "back", "left"]
Color = Tuple[int, int, int, int]  # RGBA

PARTS: Tuple[Part, ...] = (
    "head", "body", "right_arm", "left_arm", "right_leg", "left_leg",
)
LAYERS: Tuple[Layer, ...] = ("base", "overlay")
FACES: Tuple[Face, ...] = ("front", "right", "top", "bottom", "back", "left")


def canvas_faces(canvas) -> Tuple[str, ...]:
    """Return the faces a paint canvas actually stores.

    A ``Skin`` covers all six faces of every part and therefore answers
    ``FACES``. A standalone texture (one block side, an item icon, a cape
    sheet) declares only the faces it really has, and every per-face pass must
    iterate *those*: painting six faces onto a one-face canvas would stack six
    passes on the same pixels.
    """
    return tuple(getattr(canvas, "faces", FACES))


@dataclass(frozen=True)
class Box:
    """A texture region (x, y, width, height) in UV space."""
    x: int
    y: int
    w: int
    h: int

    @property
    def xyxy(self) -> Tuple[int, int, int, int]:
        """Return (x0, y0, x1, y1) for Pillow rectangle."""
        return (self.x, self.y, self.x + self.w, self.y + self.h)


# ---------------------------------------------------------------------------
# Layouts
# ---------------------------------------------------------------------------
SteveLayout: Dict[str, Dict[str, Dict[str, Box]]] = {
    "head": {
        "base": {
            "front": Box(8, 8, 8, 8), "right": Box(0, 8, 8, 8),
            "top": Box(8, 0, 8, 8), "bottom": Box(16, 0, 8, 8),
            "back": Box(24, 8, 8, 8), "left": Box(16, 8, 8, 8),
        },
        "overlay": {
            "front": Box(40, 8, 8, 8), "right": Box(32, 8, 8, 8),
            "top": Box(40, 0, 8, 8), "bottom": Box(48, 0, 8, 8),
            "back": Box(56, 8, 8, 8), "left": Box(48, 8, 8, 8),
        },
    },
    "body": {
        "base": {
            "front": Box(20, 20, 8, 12), "right": Box(16, 20, 4, 12),
            "top": Box(20, 16, 8, 4), "bottom": Box(28, 16, 8, 4),
            "back": Box(32, 20, 8, 12), "left": Box(28, 20, 4, 12),
        },
        "overlay": {
            "front": Box(20, 36, 8, 12), "right": Box(16, 36, 4, 12),
            "top": Box(20, 32, 8, 4), "bottom": Box(28, 32, 8, 4),
            "back": Box(32, 36, 8, 12), "left": Box(28, 36, 4, 12),
        },
    },
    "right_arm": {
        "base": {
            "front": Box(44, 20, 4, 12), "right": Box(40, 20, 4, 12),
            "top": Box(44, 16, 4, 4), "bottom": Box(48, 16, 4, 4),
            "back": Box(52, 20, 4, 12), "left": Box(48, 20, 4, 12),
        },
        "overlay": {
            "front": Box(44, 36, 4, 12), "right": Box(40, 36, 4, 12),
            "top": Box(44, 32, 4, 4), "bottom": Box(48, 32, 4, 4),
            "back": Box(52, 36, 4, 12), "left": Box(48, 36, 4, 12),
        },
    },
    "left_arm": {
        "base": {
            "front": Box(36, 52, 4, 12), "right": Box(32, 52, 4, 12),
            "top": Box(36, 48, 4, 4), "bottom": Box(40, 48, 4, 4),
            "back": Box(44, 52, 4, 12), "left": Box(40, 52, 4, 12),
        },
        "overlay": {
            "front": Box(52, 52, 4, 12), "right": Box(48, 52, 4, 12),
            "top": Box(52, 48, 4, 4), "bottom": Box(56, 48, 4, 4),
            "back": Box(60, 52, 4, 12), "left": Box(56, 52, 4, 12),
        },
    },
    "right_leg": {
        "base": {
            "front": Box(4, 20, 4, 12), "right": Box(0, 20, 4, 12),
            "top": Box(4, 16, 4, 4), "bottom": Box(8, 16, 4, 4),
            "back": Box(12, 20, 4, 12), "left": Box(8, 20, 4, 12),
        },
        "overlay": {
            "front": Box(4, 36, 4, 12), "right": Box(0, 36, 4, 12),
            "top": Box(4, 32, 4, 4), "bottom": Box(8, 32, 4, 4),
            "back": Box(12, 36, 4, 12), "left": Box(8, 36, 4, 12),
        },
    },
    "left_leg": {
        "base": {
            "front": Box(20, 52, 4, 12), "right": Box(16, 52, 4, 12),
            "top": Box(20, 48, 4, 4), "bottom": Box(24, 48, 4, 4),
            "back": Box(28, 52, 4, 12), "left": Box(24, 52, 4, 12),
        },
        "overlay": {
            "front": Box(4, 52, 4, 12), "right": Box(0, 52, 4, 12),
            "top": Box(4, 48, 4, 4), "bottom": Box(8, 48, 4, 4),
            "back": Box(12, 52, 4, 12), "left": Box(8, 52, 4, 12),
        },
    },
}


def _slim_arms() -> Dict[str, Dict[str, Dict[str, Box]]]:
    """Alex slim arms: 3px wide instead of 4."""
    return {
        "right_arm": {
            "base": {
                "front": Box(44, 20, 3, 12), "right": Box(40, 20, 3, 12),
                "top": Box(44, 16, 3, 4), "bottom": Box(47, 16, 3, 4),
                "back": Box(51, 20, 3, 12), "left": Box(47, 20, 3, 12),
            },
            "overlay": {
                "front": Box(44, 36, 3, 12), "right": Box(40, 36, 3, 12),
                "top": Box(44, 32, 3, 4), "bottom": Box(47, 32, 3, 4),
                "back": Box(51, 36, 3, 12), "left": Box(47, 36, 3, 12),
            },
        },
        "left_arm": {
            "base": {
                "front": Box(36, 52, 3, 12), "right": Box(32, 52, 3, 12),
                "top": Box(36, 48, 3, 4), "bottom": Box(39, 48, 3, 4),
                "back": Box(43, 52, 3, 12), "left": Box(39, 52, 3, 12),
            },
            "overlay": {
                "front": Box(52, 52, 3, 12), "right": Box(48, 52, 3, 12),
                "top": Box(52, 48, 3, 4), "bottom": Box(55, 48, 3, 4),
                "back": Box(59, 52, 3, 12), "left": Box(55, 52, 3, 12),
            },
        },
    }


def make_layout(model: str = "steve") -> Dict[str, Dict[str, Dict[str, Box]]]:
    """Return a full layout dict for the given model ('steve' or 'alex')."""
    import copy
    layout = copy.deepcopy(SteveLayout)
    if model == "alex":
        layout.update(_slim_arms())
    return layout
