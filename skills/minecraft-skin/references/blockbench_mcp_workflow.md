# Blockbench MCP × skinlib — End-to-End Workflow

Generate a Minecraft skin with `skinlib` (Python), then load it into Blockbench
for 3D preview / manual editing / saving as `.bbmodel` — all driven through the
Blockbench MCP (`blockbench_*` tools).

## Prerequisites

- Python 3 + Pillow (`pip install pillow`)
- Blockbench (desktop) running with `blockbench-mcp-plugin` loaded
- pi connected to the MCP server at `http://localhost:3000/bb-mcp`
- skinlib importable (skill dir `skills/minecraft-skin` on `sys.path`)

## Phase 1 — Generate the skin (skinlib)

Write one script that does everything (avoid stacking separate scripts — that
creates hard seams between hair/hood/armor).

Quality rules learned in practice:

- Use `apply_shading(..., style="artistic")` for a hand-drawn look (top-highlight
  → bottom-shadow + collar highlight + fabric folds). Add `noise=True,
  noise_var=4` on the torso for cloth texture.
- Keep clothing **readable** in-game: a near-black base (e.g. `(22,20,28)`)
  reads as pure black at distance. Use a richer mid-tone (e.g. `(70,50,92)` for
  dark purple) and let `artistic` push the top brighter / bottom darker.
- `bottom_dark=0.45` (instead of the default `0.35`) avoids near-black bottoms.
- Output 64 native + 128 HD:
  `img.resize((128,128), Image.Resampling.NEAREST)` (note: `Image.NEAREST` is
  deprecated in Pillow 10+).

```python
import sys
sys.path.insert(0, r"<skill>/skills/minecraft-skin")
from skinlib import Skin, apply_shading, render_3d
from PIL import Image

s = Skin(size=64, model="steve")               # or "alex"
apply_shading(s, "head", (192,186,178,255), "base", style="artistic")
apply_shading(s, "body", (70,50,92,255), "base", style="artistic",
              bottom_dark=0.45, noise=True, noise_var=4)
# ... face / hair / outfit details via s.pixel(part, layer, face, u, v, rgba)
s.save("skin.png")
s.img.resize((128,128), Image.Resampling.NEAREST).save("skin_128.png")
render_3d(s, scale=6).save("preview_3d.png")
```

## Phase 2 — Validate

```python
from skinlib import validate_report
print(validate_report("skin.png"))    # expect "[OK] No blocking errors"
```

## Phase 3 — Load into Blockbench (MCP) — order matters

Three calls, in this exact order:

1. **Create the project (this is EMPTY — no player model yet):**
   `blockbench_create_project {name: "my_skin", format: "skin"}`

2. **Load the texture.** `data` is a file path or a `data:image/...` URL —
   **never raw base64** (raw base64 is mis-parsed as a path → garbage name):
   `blockbench_create_texture {name: "my_skin", width: 64, height: 64, data: "C:/path/skin.png"}`

3. **Generate the 3D player model (the critical, easily-missed step):**
   `blockbench_risky_eval {code: 'Codecs.skin_model.rebuild("steve")'}`
   - Variants: `"steve"` (4px arms) / `"alex"` (3px slim arms).

## Phase 4 — Verify

- `blockbench_get_project_info` → `cubes: 12`, `groups: 7`, `textures: 1`,
  `texture_width: 64`.
- `blockbench_list_outline` → `Waist` → (`Head`, `Body`, `Right Arm`,
  `Left Arm`), plus `Right Leg`, `Left Leg` (each base + layer cube).
- `blockbench_list_textures` → texture with correct 64×64 name.

If `cubes` is 0, you forgot step 3. If `cubes` is 24 / `groups` 14, `rebuild`
ran twice — see Gotchas.

## Phase 5 — Save / export

Save `.bbmodel` (compile returns a **string**; write it directly):

```js
const data = Codecs.project.compile({});              // string, already JSON
await Blockbench.writeFile("E:/Documents/model.bbmodel", {content: data});
```

The skin-format `.bbmodel` embeds the texture as base64 `source` and stores
`skin_model: "steve"` (the player model is rebuilt on open), so the file is
fully self-contained.

Export the flat texture PNG if needed (or just keep the Phase-1 `skin.png`).

## Gotchas (learned the hard way)

| Symptom | Cause | Fix |
|---|---|---|
| MCP reports "No project is open" | `skin_tool.py open` spawned a second Blockbench instance | Use MCP tools, not the CLI `open` |
| Texture name is a base64 tail | `create_texture` `data` was raw base64 | Pass a file path or `data:image/...` URL |
| Texture loads but no 3D model | `Codecs.skin_model.rebuild()` never called | Call `rebuild("steve")` after loading texture |
| Model duplicated (14 groups / 24 cubes) | `rebuild` appends; called twice | `for (const g of [...Outliner.root]) g.remove()` first |
| `.bbmodel` content is a quoted JSON string | `compile()` returns a string, then re-`JSON.stringify`-ed | Write `compile()` output directly |

## Runtime reference (via `blockbench_risky_eval`)

```js
Texture.all            // loaded textures (name/width/height/mode)
Group.all / Cube.all   // model parts
Outliner.root          // root groups — clear these before a clean rebuild
Texture.getDefault()   // single_texture format default
Codecs.skin_model      // .rebuild("steve" | "alex") generates the player model
Codecs.project.compile({})     // → JSON string of the .bbmodel
Blockbench.writeFile(path, {content})   // write files from the agent
Formats.skin           // the "Minecraft 皮肤" format object
```

## Real example

`E:\necromancer\scripts\v3_optimize_necromancer.py` — necromancer v3 skin with
four optimization passes (readable dark-purple palette, artistic shading,
necromancer theme details: skull emblem / runes / bone armor, hood+white-hair
fusion). Full version archive at `E:\necromancer\README.md`. Loaded into
Blockbench via the Phase-3 steps and saved to `E:\necromancer\model.bbmodel`.
