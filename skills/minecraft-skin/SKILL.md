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

## 通用技法（跨主题可复用）

从「死灵法师」项目六代迭代沉淀的通用经验，任何皮肤都适用：

- **分层**：`base`=贴肉内层（皮肤/骷髅/露出的骨头），`overlay`=罩壳（帽/衣/护甲/3D 体积）
- **环绕**：腰带/护腕/护膝/肋骨等配件要在 4 个侧面用相同 v 坐标画，才连成环
- **配色纪律**：近黑不可读；每材质配亮/中/暗/深影 4 档；单一能量强调色（眼/符文）
- **光影三原则**：高光朝上、阴影朝下、内陷加暗边
- **骷髅脸**：深眼窝 + 倒三角鼻影 + 白骨下巴；枯骨非纯白（米黄 + 污垢 + 骨缝）
- **非对称**：左右臂/腿故意不同，制造角色性格
- **HD 工作流**：原生 128 用 `px`/`rect` 精细像素，64 下采样用 `BOX`
- **挖洞（透明透内层）**：overlay 像素 Alpha=0 挖洞 → 透出 base 画好的骷髅/枯骨，
  边缘描暗线 + 内层上沿暗/下沿亮 = 悬浮立体感

完整心法、代码模板、常见坑 → `references/techniques.md`。

**参考图源**：Noob / Herobrine 等标准 64×64 皮肤可在
[The Skindex](https://www.minecraftskins.com/) 或 [NameMC](https://namemc.com/)
搜索下载，用作算法训练与风格参考素材。本 skill 的 `examples/` 已内置
`reference_noob.png` / `reference_herobrine.png` / `reference_medieval_knight.png`
（由模板生成）。

The full API lives in the library's `skinlib/__init__.py` and README; run
`mc-skin --help` for the CLI. See `references/skin_layout.md` for the UV
coordinate map, `references/techniques.md` for the design playbook（分层/环绕/
配色/光影/骷髅/非对称/挖洞/HD 工作流）, and `references/blockbench_mcp_workflow.md`
for driving Blockbench via MCP.
