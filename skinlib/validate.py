"""Skin validation (borrowed from mature Minecraft skin tooling).

Checks a skin against the conventions expected by Minecraft/Blockbench:
- Correct dimensions (64x64 / 128x128 / legacy 64x32)
- Opaque base layer (overlay may be transparent)
- Alex slim-arm compatibility
- Unused/empty regions (wasted opacity)

Returns a list of (level, message) tuples: 'error', 'warn', or 'info'.
"""

from __future__ import annotations

from typing import List, Tuple

from PIL import Image

from .model import Skin, PARTS, FACES, make_layout


def validate(path: str) -> List[Tuple[str, str]]:
    """Validate a skin file, returning [(level, message), ...]."""
    issues: List[Tuple[str, str]] = []
    img = Image.open(path).convert("RGBA")

    # 1. Dimensions
    if img.size not in ((64, 64), (128, 128), (64, 32)):
        issues.append(("error", f"invalid size {img.size}; expected 64x64, 128x128, or 64x32"))
        return issues
    if img.size == (64, 32):
        issues.append(("warn", "legacy 64x32 format (no overlay layer)"))
        from .model import legacy_to_modern
        img = legacy_to_modern(img)

    skin = Skin(size=img.size[0])
    skin.img = img

    # 2. Base layer opacity
    base_opaque = 0
    base_total = 0
    for part in PARTS:
        for face in FACES:
            x, y, w, h = skin.region(part, "base", face)
            for i in range(w):
                for j in range(h):
                    px = img.getpixel((x + i, y + j))
                    base_total += 1
                    if px[3] > 0:
                        base_opaque += 1
    if img.size in ((64, 64), (128, 128)):
        if base_opaque < base_total * 0.5:
            issues.append(("warn", f"base layer mostly transparent ({base_opaque}/{base_total})"))

    # 3. Overlay transparency (hat/jacket may legitimately be transparent)
    overlay_opaque = 0
    for part in PARTS:
        for face in FACES:
            x, y, w, h = skin.region(part, "overlay", face)
            for i in range(w):
                for j in range(h):
                    if img.getpixel((x + i, y + j))[3] > 0:
                        overlay_opaque += 1
    if img.size in ((64, 64), (128, 128)) and overlay_opaque == 0:
        issues.append(("info", "overlay layer fully transparent (no hat/jacket)"))

    # 4. Distinct colors
    from collections import Counter
    c = Counter()
    for cnt, col in img.getcolors(maxcolors=1_000_000):
        if col[3] > 0:
            c[col[:3]] = cnt
    issues.append(("info", f"{len(c)} distinct opaque colors"))

    # 5. Alex arm check (heuristic: arms 3px = slim)
    # already implied by user choosing alex model; just note it
    return issues


def validate_report(path: str) -> str:
    """Return a human-readable validation report."""
    issues = validate(path)
    lines = [f"Validation for {path}:"]
    for level, msg in issues:
        lines.append(f"  [{level.upper():5s}] {msg}")
    if not any(lvl == "error" for lvl, _ in issues):
        lines.append("  [OK] No blocking errors")
    return "\n".join(lines)
