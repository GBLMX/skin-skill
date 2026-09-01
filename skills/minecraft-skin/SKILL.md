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

## 皮肤美学参考（风格基因）

| 风格 | 入口 | 配色 | 光影档案 |
|------|------|------|----------|
| Noob（极简黑灰） | `template noob` | 黑灰（`CLOTHING` gray/dark_gray/black） | `minimal`（flat，无褶皱无噪点） |
| Herobrine（白瞳） | `template herobrine` | Steve 青衫 + 荚蓝裤 | `clean`（轻圆柱） + 白瞳 `face` |
| 中世纪骑士 | `template medieval_knight` | 金属灰 + 红 + 金 | `metal` 材质 + 红 tunic + 金腰带 |
| 金属高光 | `apply_style(..., "metal")` | 任意 | artistic 强边缘压暗 + 顶部提亮，无褶皱 |
| 斑驳旧化 | `apply_style(..., "mottled")` | 任意 | artistic 褶皱 + 噪点(noise_var=8) |
| 极简无细节 | `apply_style(..., "minimal")` | 任意 | flat |

光影档案 `STYLE_PROFILES` / `apply_style()`：`minimal` / `clean` / `metal` /
`mottled` / `leathery`。材质 `apply_material()`：`cloth` / `leather` / `metal` /
`bone` / `glow_crystal`。

**参考图源**：Noob / Herobrine 等标准 64×64 皮肤可在
[The Skindex](https://www.minecraftskins.com/) 或 [NameMC](https://namemc.com/)
搜索下载，用作算法训练与风格参考素材。本 skill 的 `examples/` 已内置
`reference_noob.png` / `reference_herobrine.png` / `reference_medieval_knight.png`
（由模板生成）。

The full API lives in the library's `skinlib/__init__.py` and README; run
`mc-skin --help` for the CLI. See `references/skin_layout.md` for the UV
coordinate map, and `references/blockbench_mcp_workflow.md` for driving
Blockbench via MCP.
