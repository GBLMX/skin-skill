# mc-skin

Programmatic Minecraft player skin and texture generation for Python.

Create, paint, shade, and 3D-render Minecraft skins with a clean, dependency-light
API. Full double-layer (hat/jacket/sleeve/pants) and Steve/Alex model support,
realistic shading (gradient + cylindrical lighting + Perlin/fabric grain), a
material system, patterns, preset templates, reference-image color sampling, and
orthographic 3D rendering with body poses. The same painting primitives also draw
everything that is *not* a skin — block sheets, item icons, capes, armor layers
(see [Generic textures](#generic-textures)).

## Install

```bash
pip install mc-skin
```

Requires Python 3.9+. The only hard dependency is [Pillow](https://python-pillow.org).
Grain textures use [opensimplex](https://pypi.org/project/opensimplex/) (Simplex noise)
when it is installed, and otherwise fall back to a built-in pure-Python Perlin
implementation — so the package works either way. Install the Simplex backend with
`pip install mc-skin[noise]`.

The vanilla game-data layer ([minecraft-data](https://github.com/PrismarineJS/minecraft-data)
via [minebase](https://pypi.org/project/minebase/)) is a separate extra because it
embeds the whole dataset (~330 MB installed): `pip install mc-skin[gamedata]`.
See [Vanilla game data](#vanilla-game-data) below.

## CLI

```bash
mc-skin create -o skin.png --size 64 --model steve
mc-skin paint skin.png --part head --layer base --color 240,190,150
mc-skin shading skin.png --part body --color 120,20,25 --style combined --noise
mc-skin material skin.png --part body --material leather
mc-skin template knight -o knight.png
mc-skin harmonize skin.png --reference cape.png
mc-skin render skin.png --outdir previews
mc-skin pose skin.png --pose walking
mc-skin validate skin.png
mc-skin gamedata styles --version 1.21.6
mc-skin gamedata style sculk
mc-skin gamedata theme sculk
mc-skin gamedata formats
mc-skin gamedata spec grass_block
mc-skin texture sculk_sensor --color 42,77,74 -o out --scale 8
mc-skin texture echo_shard --color '#29dfeb' --shape shard --glow
mc-skin texture --family sculk --color 42,77,74 -o out/sculk
mc-skin texture --family sculk --color 42,77,74 --pack sculk-pack.zip
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

A recipe whose **first step is `texture`** builds a texture instead of a skin --
a block sheet or an item icon -- and may then use the canvas-generic ops. The
skin-only ops (`face`, `hair`, `band`, `decorate`) refuse it, and `output_dir`
writes one PNG per face:

```python
recipe = {
    "steps": [
        {"op": "texture", "name": "sculk_sensor", "color": "#2a4d4a",
         "noise": 4, "seed": 1},
        {"op": "overlay", "part": "all", "overlay": "runes",
         "color": "#7fffd4", "seed": 3},
    ],
    "output_dir": "out/sculk",     # out/sculk/sculk_sensor_top.png, _side, _bottom
}
generate_from_recipe(recipe)
```

### Generic textures

A skin is not the only canvas. `shading`, `patterns`, `materials`, `overlay` and
`decoration` only ever needed a canvas that answers `region`/`box`/`pixel`/
`get_pixel` and declares which faces it stores -- that is `Texture`, so every one
of those primitives paints block sheets, item icons, capes and armor layers too.

```python
from skinlib import Texture, block, icon, generate, from_spec
from skinlib.overlay import scratches

block((42, 77, 74, 255), style="combined", noise=4).save_faces("out", "sculk")
# out/sculk_top.png, out/sculk_side.png, out/sculk_bottom.png

t = block((42, 77, 74, 255), glow=True)          # emissive: a proportional lift
scratches(t, "all", (0, 0, 0, 255), count=8)     # the primitives apply as-is

icon((41, 223, 235, 255), shape="shard", glow=True).save_faces("out", "echo_shard")
icon((255, 0, 0, 255), mask=lambda u, v: u == v) # or your own silhouette

cape = Texture.load("cape.png", faces=("front",))  # edit any existing sheet
```

The vanilla conventions are built in:

- blocks and items are 16x16; capes, elytra and armor layers are 64x32
  (`texture_size(kind)`), anything else takes an explicit size;
- a cube needs three textures, and they are lit by the cube rule --
  top brightest (x1.15), side mid (x1.0), bottom darkest (x0.8) -- before the
  shading style is applied, which is what makes a flat 16x16 read as 3D;
- biome-tinted sheets (grass, foliage, water) come out **greyscale** with
  `tint_ready=True`, because the game multiplies them by a biome colour at
  runtime and painting them in colour double-tints them;
- emissive sheets (`glow=True`, or the block's own `emitLight`) get a
  proportional lift that keeps their structure -- `materials.glow_center` is
  deliberately *not* used, since it overwrites pixels with a radial ramp;
- item icons paint through a mask with a 1px transparent margin, from the
  `ICON_ART` archetypes (`gem`, `shard`, `ingot`, `dust`, `orb`) or your own
  `mask=(u, v) -> bool`.

`generate(name, color)` looks the name up in the registries and hands its
`TextureSpec` to `from_spec`, so an emissive block blooms and a biome-tinted one
comes out greyscale without being told. Colour is always yours to supply: blocks
carry no colour data (see the caveat below). A `Texture` is a row of faces
side by side, and its painting primitives run once per face it declares --
rendering (`render_3d`) and validation stay skin-only, since they need the 64x64
body layout.

### Resource packs

`build_pack` turns generated textures into a resource pack Minecraft can load:
the PNGs at the paths the client reads, plus the models, block states and
`pack.mcmeta` that make it use them.

```python
from skinlib import block, build_pack, pack_format

pack_format("1.21.6")                     # 63 — looked up in the version table
build_pack("sculk-pack.zip",              # a .zip or a directory
           blocks={"sculk": block((42, 77, 74, 255))},
           version="1.21.6")
```

The layout is `assets/<namespace>/textures/block/<name>_<face>.png` with
`models/block/<name>.json` and `blockstates/<name>.json` for blocks, and
`textures/item/<name>.png` with `models/item/<name>.json` for icons. Three things
worth knowing:

- a resource pack cannot *add* blocks or items, only replace shipped assets, so
  the default namespace is `minecraft`: the pack overrides vanilla models and
  block states too, which is what makes the generated textures show up;
- a block whose vanilla model depends on block states (stairs, doors, ...) loses
  those state variants in the pack — every state renders the generated model;
- `pack_format` is version-dependent; the table in `skinlib.pack` is transcribed
  from the Minecraft Wiki (resource packs) and a version it does not list — a
  snapshot — needs the number passed explicitly (`format=`).

### Vanilla game data

`skinlib.gamedata` exposes the real game registries (minecraft-data) so
generation can line up with an actual version instead of a hard-coded guess.
Install the extra with `pip install mc-skin[gamedata]`; nothing else in the
package depends on it, and importing `skinlib` never loads it.

```python
from skinlib import gamedata as G

G.latest()                          # '1.21.6'
G.info("1.21.6").protocol           # 771
G.blocks("1.21.6")                  # 1105 Block records
G.find_block("sculk_sensor").glows  # True — an emissive texture target
G.biome_colors("grass")             # {'badlands': '#90814d', 'cherry_grove': '#b6db61', ...}
G.tints("1.21.6")["water"]          # biome-tint rules for water
G.theme("sculk")                    # one topic, grouped across registries
G.texture_spec("sculk_sensor")      # facts for drawing its texture: emissive,
                                    # material group, style family, states
```

**Style families** are what "match the vanilla look" means in practice:

```python
s = G.styles("1.21.6")["sculk"]
s.block_names   # ('calibrated_sculk_sensor', 'sculk', 'sculk_catalyst', 'sculk_sensor', ...)
s.items         # the matching item records
s.glow          # ('calibrated_sculk_sensor', 'sculk_catalyst', 'sculk_sensor')
s.materials     # ('mineable/hoe',)
```

Families are derived from the registries themselves, so `copper`, `oak`, `glass`,
`terracotta`, `deepslate`, `cherry`, `nether`, `end` and friends are whatever the
version actually ships rather than a hand-maintained list. `G.search("sculk")`
searches one phrase across every registry, and `G.skin_formats()` reports the
skin format facts (Bedrock's serialized-skin schema with its sample image size,
arm model, cape and geometry version; Java's profile/property schema).

A **theme** reaches the other way: `G.theme("sculk")` takes one curated topic and
gathers it from every registry at once. The `sculk` style family is six blocks;
the theme also finds the warden, the deep dark, the Darkness effect, Swift Sneak,
echo shards, music disc 5 and reinforced deepslate -- none of which carries the
word. The matching vocabulary lives in `gamedata.THEMES` and is additive: extend
the tuple to reach more.

The same views are on the CLI: `mc-skin gamedata styles`, `mc-skin gamedata
style sculk`, `mc-skin gamedata theme sculk`, `mc-skin gamedata formats`,
`mc-skin gamedata spec sculk_sensor`.

Two data caveats worth knowing:

- **Biome tints are verified; biome `color` is not.** `biome_colors()` returns
  the tint table the game really multiplies grass/foliage/water by — badlands
  `#90814d`, cherry grove `#b6db61`, water `#3f76e4`, all matching vanilla. The
  `color` field on a `Biome` record is passed through from the dataset but does
  *not* match the vanilla biome colors, so don't paint with it.
- **Blocks carry no color data** — only names, material groups, light emission,
  transparency and states. Texture color has to come from the textures.

Everything is cached per `(edition, version)`, and `G.dataset(kind)` / `G.raw()`
expose the untransformed datasets (`recipes`, `protocol`, `sounds`, …). Both
editions work: `G.styles("1.21.70", "bedrock")`.

### Matching a reference

`harmonize` moves one texture's colors into another's family -- a skin onto its
cape, a build onto its logo -- and measures how far apart they were:

```python
from skinlib import harmonize, harmonize_report, color_difference, region_mask

color_difference("skin.png", "cape.png")        # 8.1 — obvious side by side
harmonize("skin.png", "cape.png").save("matched.png")   # retheme: 8.1 -> 4.3
```

Two modes, because a shaded skin and a flat logo want different things:

| mode | what moves | use it when |
|------|-----------|-------------|
| `retheme` (default) | the color only; every shading step keeps its lightness | the target was hand-shaded — a four-tone ramp stays four-tone |
| `palette` | onto the nearest reference color, lightness included | you want the colors to *be* the reference's and can lose tonal steps |

`strength` runs 0 (unchanged) to 1 (fully matched) in both.

Keep a fix where it shows by masking the region — `faces=("back",)` touches only
the faces a cape hangs over:

```python
back = region_mask("steve", 64, parts=("body", "left_leg", "right_leg"),
                   layers=("base",), faces=("back",))
report = harmonize_report("skin.png", "cape.png", mode="retheme", mask=back)
report["delta_before"], report["delta_after"]   # 6.3, 2.4 — both in that region
report["image"].save("back_matched.png")
```

CLI: `mc-skin harmonize skin.png --reference cape.png` (plus `--mode`,
`--strength`, `--parts`, `--layers`, `--faces`).

### More

- **Shading styles**: `flat`, `vertical`, `cylindrical`, `combined`, `artistic`
- **Patterns**: `stripes`, `checker`, `camouflage`, `border_trim`
- **Templates**: `knight`, `villager`, `astronaut`, `noob`, `herobrine`, `medieval_knight`
- **Style profiles**: `apply_style(skin, part, color, "metal"|"mottled"|"minimal"|"clean"|"leathery")`
- **Features**: `face()`, `hair()`, `band()`, 3D decoration
- **Sampling**: `sample_palette("ref.png", 6)` to match a reference image
- **Matching**: `harmonize()`, `color_difference()`, `region_mask()` — see
  [Matching a reference](#matching-a-reference)
- **Poses**: `natural`, `walking`, `sitting`, `crouching`, `jumping`, `aiming`
- **Textures**: `block()`, `icon()`, `Texture`, `from_spec()`, `generate()` —
  non-skin sheets on the same primitives, see [Generic textures](#generic-textures)
- **Loading**: legacy 64×32 auto-converts to 64×64; Mojang matte (solid-color
  transparency keyed on the top-left pixel) is auto-stripped on load

See the full public API in `skinlib/__init__.py`, and `examples/` for a complete
character built with the shading API.

## License

MIT — see [LICENSE](LICENSE).
