"""Minecraft vanilla color palette and skin-tone presets.

Provides ready-made colors drawn from the game's mature art direction, so
skins can match the vanilla aesthetic. Includes skin tones, hair colors, and
common clothing/material colors.
"""

from __future__ import annotations

from typing import Dict, Tuple

Color = Tuple[int, int, int, int]


def _rgb(r, g, b, a=255) -> Color:
    return (r, g, b, a)


# ---------------------------------------------------------------------------
# Skin tones (vanilla player + common skin shades)
# ---------------------------------------------------------------------------
SKIN_TONES: Dict[str, Color] = {
    "alex_pale":     _rgb(240, 214, 190),
    "steve_classic": _rgb(255, 222, 173),
    "tan":           _rgb(222, 170, 130),
    "olive":         _rgb(180, 140, 110),
    "brown":         _rgb(140, 100, 70),
    "dark":          _rgb(110, 75, 50),
    "pale_blue":     _rgb(170, 150, 145),   # 星灵苍白（阿拉纳克）
}

# ---------------------------------------------------------------------------
# Hair colors
# ---------------------------------------------------------------------------
HAIR_COLORS: Dict[str, Color] = {
    "black":   _rgb(30, 25, 25),
    "brown":   _rgb(70, 45, 30),
    "blonde":  _rgb(220, 180, 90),
    "red":     _rgb(160, 60, 40),
    "white":   _rgb(230, 230, 225),
    "blue":    _rgb(40, 60, 130),
    "purple":  _rgb(100, 60, 140),
    "pink":    _rgb(220, 130, 150),
}

# ---------------------------------------------------------------------------
# Clothing / material colors (vanilla-flavored)
# ---------------------------------------------------------------------------
CLOTHING: Dict[str, Color] = {
    "white":     _rgb(240, 240, 240),
    "gray":      _rgb(150, 150, 155),
    "dark_gray": _rgb(60, 60, 65),
    "black":     _rgb(30, 30, 35),
    "red":       _rgb(180, 40, 40),
    "dark_red":  _rgb(120, 20, 25),    # 塔达林深红
    "orange":    _rgb(220, 120, 40),
    "yellow":    _rgb(220, 200, 60),
    "green":     _rgb(60, 140, 60),
    "dark_green": _rgb(40, 90, 45),
    "blue":      _rgb(40, 80, 180),
    "dark_blue": _rgb(25, 45, 100),
    "purple":    _rgb(120, 60, 160),
    "brown":     _rgb(100, 70, 40),
    "gold":      _rgb(210, 170, 60),   # 曹操金
    "silver":    _rgb(200, 200, 210),
    "iron":      _rgb(45, 45, 55),     # 黑灰金属
}

# ---------------------------------------------------------------------------
# Energy / glow colors
# ---------------------------------------------------------------------------
ENERGY: Dict[str, Color] = {
    "blood_red": _rgb(220, 40, 40),       # 血红
    "lava":      _rgb(255, 100, 20),
    "ender":     _rgb(120, 60, 160),      # 末影紫
    "ice":       _rgb(120, 200, 255),
    "gold_glow": _rgb(255, 220, 90),
}


def all_palettes() -> Dict[str, Dict[str, Color]]:
    return {
        "skin_tones": SKIN_TONES,
        "hair": HAIR_COLORS,
        "clothing": CLOTHING,
        "energy": ENERGY,
    }
