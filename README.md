# mc-skin

Programmatic Minecraft player skin generation and editing for Python.

Create, paint, shade, and 3D-render Minecraft skins with a clean, dependency-light
API. Full double-layer (hat/jacket/sleeve/pants) and Steve/Alex model support,
realistic shading (gradient + cylindrical lighting + Perlin/fabric grain), a
material system, patterns, preset templates, reference-image color sampling, and
orthographic 3D rendering with body poses.

## Install

```bash
pip install mc-skin
```

Requires Python 3.9+. The only hard dependency is [Pillow](https://python-pillow.org).
Grain textures use [opensimplex](https://pypi.org/project/opensimplex/) (Simplex noise)
when it is installed, and otherwise fall back to a built-in pure-Python Perlin
implementation — so the package works either way. Install the Simplex backend with
`pip install mc-skin[noise]`.

## CLI

```bash
mc-skin create -o skin.png --size 64 --model steve
mc-skin paint skin.png --part head --layer base --color 240,190,150
mc-skin shading skin.png --part body --color 120,20,25 --style combined --noise
mc-skin material skin.png --part body --material leather
mc-skin template knight -o knight.png
mc-skin render skin.png --outdir previews
mc-skin pose skin.png --pose walking
mc-skin validate skin.png
```

Run `mc-skin --help` for every subcommand and option.

## Python API

```python
from skinlib import Skin, apply_shading, apply_material, render_3d

s = Skin(size=64, model="steve")               # or "alex"
apply_shading(s, "head", (240, 190, 150, 255), "base", style="combined")
apply_material(s, "body", "leather")           # one-call material recipe
apply_material(s, "head", "glow_crystal", color=(120, 60, 160, 255))
s.save("skin.png")

render_3d(s, pose="walking").save("preview.png")
```

### Materials

| Name | Look |
|------|------|
| `cloth` | matte fabric with per-pixel weave |
| `leather` | artistic folds + fine grain + faint sheen |
| `metal` | cylindrical edge-darkening + specular streak |
| `bone` | pale, subtle grain |
| `glow_crystal` | emissive center that fades to the edges |

```python
from skinlib import MATERIALS, apply_material
apply_material(skin, "body", "metal", color=(200, 200, 210, 255), seed=7)
```

### Overlays & masks

Composite battle damage, cracks, or glowing runes onto a part without touching
its base color:

```python
from skinlib import apply_overlay, overlay_pattern, rect_mask

apply_overlay(skin, "body", "scratches", seed=3)          # battle damage
apply_overlay(skin, "body", "runes", color=(120, 220, 255, 255))

# general: composite a pattern through a mask with a blend mode
overlay_pattern(skin, "body", (0, 0, 0, 255), mode="multiply",
                mask=rect_mask(0, 0, 4, 4))
```

Effects: `scratches`, `cracks`, `runes`. Blend modes: `blend`, `multiply`,
`add`, `replace`. Masks: `rect_mask`, `random_mask`.

### Recipes

Describe a skin declaratively as JSON and build it (or emit a Python script):

```python
from skinlib import generate_from_recipe, recipe_to_python

recipe = {
    "size": 64, "model": "steve",
    "steps": [
        {"op": "material", "part": "body", "material": "metal"},
        {"op": "overlay", "part": "body", "overlay": "cracks", "seed": 2},
        {"op": "material", "part": "head", "material": "glow_crystal"},
    ],
    "output": "skin.png",
}
skin = generate_from_recipe(recipe)     # build + save
print(recipe_to_python(recipe))         # emit equivalent script
```

Ops: `shading`, `material`, `pattern`, `overlay`, `decorate`, `face`, `hair`,
`band`, `outline`, `pixel`, `paint`. Colors can be `"R,G,B"` / `"#RRGGBB"`
strings or `[r, g, b]` lists.

### More

- **Shading styles**: `flat`, `vertical`, `cylindrical`, `combined`, `artistic`
- **Patterns**: `stripes`, `checker`, `camouflage`, `border_trim`
- **Templates**: `knight`, `villager`, `astronaut`, `noob`, `herobrine`, `medieval_knight`
- **Style profiles**: `apply_style(skin, part, color, "metal"|"mottled"|"minimal"|"clean"|"leathery")`
- **Features**: `face()`, `hair()`, `band()`, 3D decoration
- **Sampling**: `sample_palette("ref.png", 6)` to match a reference image
- **Poses**: `natural`, `walking`, `sitting`, `crouching`, `jumping`, `aiming`
- **Loading**: legacy 64×32 auto-converts to 64×64; Mojang matte (solid-color
  transparency keyed on the top-left pixel) is auto-stripped on load

See the full public API in `skinlib/__init__.py`, and `examples/` for a complete
character built with the shading API.

## License

MIT — see [LICENSE](LICENSE).
