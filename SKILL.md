---
name: minecraft-skin
description: Create, edit, and render Minecraft player skins with full double-layer (hat/jacket/sleeve/pants) and Steve/Alex model support. Features realistic shading (gradient + cylindrical lighting + fabric noise), patterns, preset templates, reference-image color sampling, and 3D rendering. Use when the user wants to generate or customize Minecraft skin PNG files programmatically.
---

# Minecraft Skin Library

A clean, professional Python library (`skinlib`) for creating and editing
Minecraft player skins, with double-layer and dual-model support.

## Architecture

```
skinlib/
├── __init__.py      # public API, version 2.2
├── model.py         # UV layouts (Steve/Alex) + Skin object + color parsing
├── colors.py        # pure color math (mix/shade/gray/blend/gradient/palette)
├── shading.py       # realistic shading (gradient/cylinder/combined/artistic/noise)
├── artistic.py      # observed artistic lighting (top-highlight, bottom-shadow, folds)
├── patterns.py      # stripes/checker/camouflage/border_trim
├── sampling.py      # reference-image palette extraction
├── render.py        # flat/isometric/orthographic-3D rendering (with poses)
├── poses.py         # body poses (natural/walking/sitting/crouching/jumping/aiming)
├── palette.py       # vanilla color palettes (skin/hair/clothing/energy)
├── decoration.py    # 3D decoration (hat/jacket/pants + highlight/shadow accents)
├── features.py      # face details + 3D hair + wrap-around bands
├── validate.py      # skin validation (dimensions/opacity/colors)
└── templates.py     # knight/villager/astronaut presets
```

Single CLI entry point: `skin_tool.py`.

## Setup

Requires Python 3 + Pillow (standard library otherwise):

```bash
python -m pip install pillow
```

## Quick Start (CLI)

```bash
# Create / paint / shade
python skin_tool.py create -o skin.png --size 64 --model steve
python skin_tool.py paint skin.png --part head --layer base --color 240,190,150
python skin_tool.py shading skin.png --part body --color 120,20,25 --style combined --noise

# Patterns & templates
python skin_tool.py pattern skin.png --part body --pattern stripes --c1 200,0,0 --c2 255,255,255
python skin_tool.py template knight -o knight.png

# 3D decoration (sparse overlay: hat/jacket/pants)
python skin_tool.py decorate skin.png --hat 200,30,30 --jacket 30,30,40 --pants 20,40,90

# Character features (face / hair / bands)
python skin_tool.py hair skin.png --color 198,196,190
python skin_tool.py face skin.png --eyes 96,226,140
python skin_tool.py band skin.png --part body --v0 9 --v1 10 --color 176,146,60

# Sample a palette from a reference image
python skin_tool.py sample character.png --colors 6

# Render (flat + isometric + 3D) & inspect
python skin_tool.py render skin.png --outdir previews
python skin_tool.py info skin.png
python skin_tool.py flatten skin.png

# Pose rendering & validation & palettes
python skin_tool.py pose skin.png --pose walking
python skin_tool.py validate skin.png
python skin_tool.py palette --category clothing
```

## Python API

```python
from skinlib import Skin, apply_shading, sample_palette, render_3d

s = Skin(size=64, model="steve")            # or "alex"
apply_shading(s, "body", (120, 20, 25, 255), "base", style="combined", noise=True)
apply_shading(s, "head", (170, 150, 145, 255), "base", style="combined")
s.pixel("head", "overlay", "front", 3, 3, (0, 0, 0, 255))
s.save("skin.png")

render_3d(s).save("preview_3d.png")
palette = sample_palette("ref.png", 6)       # extract colors from art

# 3D decoration (sparse overlay layer)
from skinlib import apply_3d_decoration
apply_3d_decoration(s, hat_color=(200, 30, 30, 255),
                    jacket_color=(30, 30, 40, 255),
                    pants_color=(20, 40, 90, 255))

# character features (face / hair / wrap-around bands)
from skinlib import face, hair, band
hair(s, (198, 196, 190, 255))               # 3D two-layer hair
face(s, eye_color=(96, 226, 140, 255))      # facial details
band(s, "body", 9, 10, (176, 146, 60, 255)) # wrap-around belt
```

## Body Poses (borrowed from Blockbench)

`natural`, `walking`, `sitting`, `crouching`, `jumping`, `aiming`

```python
from skinlib import render_3d
render_3d(skin, pose="walking").save("walk.png")
```

## Built-in Palettes (vanilla art direction)

`SKIN_TONES` (7), `HAIR_COLORS` (8), `CLOTHING` (17), `ENERGY` (5)

```python
from skinlib import SKIN_TONES, CLOTHING
skin.paint_part("head", SKIN_TONES["steve_classic"], "base")
```

## Validation

```python
from skinlib import validate_report
print(validate_report("skin.png"))
```

Legacy 64x32 skins are auto-converted to the modern 64x64 layout on load
(single arm/leg texture mirrored to both sides, no overlay).

## Shading Styles

| Style | Effect |
|-------|--------|
| `flat` | Solid fill |
| `vertical` | Top-light -> bottom-dark gradient |
| `cylindrical` | Edges dark, center light (3D tube) |
| `combined` | Gradient + cylinder + optional noise |
| `artistic` | Observed realistic lighting: strong top-highlight -> heavy bottom-shadow, symmetric edge falloff, collar highlight, fabric folds (closest to hand-drawn skins) |

## Body Parts, Layers, Faces

- Parts: `head`, `body`, `right_arm`, `left_arm`, `right_leg`, `left_leg`
- Layers: `base` (inner), `overlay` (hat/jacket/sleeve/pants)
- Faces: `front`, `right`, `top`, `bottom`, `back`, `left`

## Examples

See `examples/cao_alarak.py` for a full character skin (曹操 × 阿拉纳克 fusion)
built with the shading API. Reference UV coordinates are in
`references/skin_layout.md`.

### Reference skins (quality examples)

Real skins bundled under `examples/` as style references:

- `reference_steve.png` — default vanilla player skin (facial-detail convention)
- `reference_zombie.png` — vanilla zombie (green skin, simple face)
- `reference_hoodie_xty.png` — 双色卫衣 (two-color hoodie) with 3D overlay depth
