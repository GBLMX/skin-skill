---
name: minecraft-skin
description: "创建、编辑、渲染 Minecraft 玩家皮肤 + 皮肤设计经验手册。含 mc-skin 库的 CLI/API 适配，以及沉淀的可复用设计技法（分层/环绕/配色纪律/光影三原则/骷髅脸/非对称/挖洞/HD 工作流）。当用户想编程生成或自定义皮肤 PNG，或需要皮肤美学/技法指导时使用。"
type: tool
---

# Minecraft Skin — 皮肤生成 + 设计经验

本 skill 是 **`mc-skin` Python 库**的适配层 + 皮肤设计经验手册。库是独立 PyPI 包（不绑定 pi）——先安装：

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
- **HD 工作流**：Java 原版 64 原生（`Skin(size=64)`）；128 是 OptiFine HD 可选升级，
  精细细节用 `px`/`rect`，64 下采样用 `BOX`
- **Java 3D 浮起**：皮肤唯一原生立体 = overlay 层浮起（head +0.5 / 躯干四肢 +0.25 voxel），
  鼓起的配件画 overlay、贴肉画 base；渲染器须外扩 overlay 而非平铺
- **挖洞（透明透内层）**：overlay 像素 Alpha=0 挖洞 → 透出 base 画好的骷髅/枯骨，
  边缘描暗线 + 内层上沿暗/下沿亮 = 悬浮立体感
- **alpha 三规则**：base 透明=黑、overlay 半透明=看穿 bug（Bedrock 强制不透明），
  可靠手段只有 alpha 0/255 二值
- **色阶消散**：半透明不可靠 → 用不透明色阶渐变（实体色→幽灵色）模拟消散/幽灵化
- **3D Skin Layers 友好**：64 原生 + overlay 配件四面环绕完整 → mod extrud 成真 3D 立体块
- **头发 3D**：双层发（base 贴肉 + overlay 浮起）+ 发梢渐深 + 发丝透明缝分离；帽子 overlay 不包死

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
