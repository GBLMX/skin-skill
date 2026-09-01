---
name: minecraft-skin
description: "创建、编辑和渲染 Minecraft 玩家皮肤，支持完整的双层（帽子/外套/袖子/裤子）和 Steve/Alex 模型。特性包括真实着色（渐变 + 圆柱光照 + 布料噪点）、图案、预设模板、参考图像颜色采样和 3D 渲染。当用户想以编程方式生成或自定义 Minecraft 皮肤 PNG 文件时使用。"
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
python skin_tool.py outline skin.png --part body --color 0,0,0 --width 1

# Sample a palette from a reference image
python skin_tool.py sample character.png --colors 6

# Render (flat + isometric + 3D) & inspect
python skin_tool.py render skin.png --outdir previews
python skin_tool.py info skin.png
python skin_tool.py flatten skin.png
python skin_tool.py open skin.png

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

## Models, Auto-detect & HD

- Load commands default to `--model auto`: Steve (4px arms) vs Alex (3px slim
  arms) is detected from the arm texture. Override with `--model steve` / `alex`;
  `create` still defaults to `steve`.
- HD 128x128 skins are fully supported: feature/decoration coordinates are
  logical (64px grid) and scale automatically. Legacy 64x32 auto-converts.
- Fabric-noise seed is deterministic via `--seed` (shading command).

## Examples

See `examples/cao_alarak.py` for a full character skin (曹操 × 阿拉纳克 fusion)
built with the shading API. Reference UV coordinates are in
`references/skin_layout.md`.

### Reference skins (quality examples)

Real skins bundled under `examples/` as style references:

- `reference_steve.png` — default vanilla player skin (facial-detail convention)
- `reference_zombie.png` — vanilla zombie (green skin, simple face)
- `reference_hoodie_xty.png` — 双色卫衣 (two-color hoodie) with 3D overlay depth
- `reference_gawrgura.png` — Gawr Gura (VTuber) character skin
- `reference_pc_man.png` — 电脑人 (computer person) skin
- `reference_sasuke.png` — 宇智波佐助 (Uchiha Sasuke) character skin

## Blockbench Integration

### Open in the desktop editor (manual tweaks)

```bash
python skin_tool.py open skin.png              # opens C:\Program Files\Blockbench\Blockbench.exe
BLOCKBENCH=/path/to/Blockbench.exe python skin_tool.py open skin.png
```

### Drive Blockbench programmatically via MCP

Blockbench can act as an MCP server (via `blockbench-mcp-plugin`), letting an
AI agent drive it directly. With Blockbench running and the plugin loaded, pi
connects at `http://localhost:3000/bb-mcp` (Streamable HTTP). Tools are the
`blockbench_*` family. Full end-to-end recipe:
`references/blockbench_mcp_workflow.md`. The three non-obvious steps:

1. **`blockbench_create_project {format: "skin"}` creates an EMPTY project** —
   no player model yet. Load the texture, then generate the model explicitly.
2. **Load the texture** — `data` is a **file path** or a **`data:image/...` URL**,
   never raw base64 (raw base64 is mis-parsed as a path → garbage texture name):
   `blockbench_create_texture {name, width:64, height:64, data:"C:/path/skin.png"}`
3. **Generate the 3D player model** — the step that is almost always missed;
   without it the viewport stays empty:
   `blockbench_risky_eval {code: 'Codecs.skin_model.rebuild("steve")'}`
   - Variants: `"steve"` (4px arms) / `"alex"` (3px slim arms).
   - `rebuild` **appends** — calling it twice duplicates the model. To rebuild
     cleanly, clear first: `for (const g of [...Outliner.root]) g.remove();`

A correct skin project shows 7 groups / 12 cubes (`Waist`, `Head`, `Body`,
`Right Arm`, `Left Arm`, `Right Leg`, `Left Leg`, each base+layer). Verify with
`blockbench_get_project_info` (counts) and `blockbench_list_outline` (tree).

### Saving a .bbmodel project

`Codecs.project.compile({})` returns a **JSON string**, not an object — write it
directly (re-stringifying double-encodes the file):

```js
const data = Codecs.project.compile({});               // string
await Blockbench.writeFile("E:/path/model.bbmodel", {content: data});
```

A skin-format `.bbmodel` stores `skin_model: "steve"` plus the texture as an
embedded base64 `source` — **not** an `elements` array (the player model is
regenerated from the built-in template on load), so the file is self-contained.

### Pitfalls

- `skin_tool.py open` spawns `Blockbench.exe` as a subprocess, which can open a
  second instance and desync the MCP session. Prefer the MCP tools directly.
- `blockbench_risky_eval` runs arbitrary JS via `eval()` in Blockbench's scope —
  use it for inspection/manipulation the read-only tools (`get_project_info`,
  `list_outline`, `list_textures`) don't expose (e.g. `Texture.all`,
  `Group.all`, `Outliner.root`, `Codecs`, `Formats`, `Project`).
