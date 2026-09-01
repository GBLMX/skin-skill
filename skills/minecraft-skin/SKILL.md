---
name: minecraft-skin
description: "创建、编辑和渲染 Minecraft 玩家皮肤（薄适配层，包装 mc-skin Python 库）。先 pip install mc-skin，再用 Python API 或 mc-skin CLI。当用户想以编程方式生成或自定义 Minecraft 皮肤 PNG 时使用。"
---

# Minecraft Skin — pi skill adapter

This skill is a thin adapter over the **`mc-skin` Python library**. The
library is a standalone PyPI package (not pi-specific) — install it first:

```bash
pip install mc-skin
```

Then use either the `mc-skin` CLI or the `skinlib` Python API.

## Quick reference

```bash
mc-skin create -o skin.png --size 64 --model steve
mc-skin shading skin.png --part body --color 120,20,25 --style combined --noise
mc-skin material skin.png --part body --material leather
mc-skin overlay skin.png --part body --overlay scratches --seed 3
mc-skin recipe recipe.json -o skin.png
mc-skin template knight -o knight.png
mc-skin render skin.png --outdir previews
```

```python
from skinlib import Skin, apply_shading, apply_material, render_3d

s = Skin(size=64, model="steve")          # or "alex"
apply_shading(s, "head", (240, 190, 150, 255), "base", style="combined")
apply_material(s, "body", "leather")
s.save("skin.png")
render_3d(s, pose="walking").save("preview.png")
```

The full API lives in the library's `skinlib/__init__.py` and README; run
`mc-skin --help` for the CLI. See `references/skin_layout.md` for the UV
coordinate map, and `references/blockbench_mcp_workflow.md` for driving
Blockbench via MCP.
