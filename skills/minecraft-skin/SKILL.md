---
name: minecraft-skin
description: "创建、编辑、渲染 Minecraft 玩家皮肤与通用材质（方块面/物品图标/披风/盔甲层等非皮肤贴图）+ 皮肤设计经验手册。含 mc-skin 库的 CLI/API 适配、可选的 minecraft-data 原版数据接入（风格族/主题/原版配色/皮肤格式对齐/贴图事实 texture_spec）、参考配色统一（把皮肤并到披风/logo 的色系并量出 ΔE），以及沉淀的可复用设计技法（分层/环绕/配色纪律/光影三原则/骷髅脸/非对称/挖洞/HD 工作流/通用材质约定）。当用户想编程生成或自定义皮肤、或生成方块/物品贴图 PNG，需要皮肤美学/技法指导，或要让生成结果与原版风格/配色对齐、或要与参考图统一配色时使用。"
type: tool
---

# Minecraft Skin — 皮肤与通用材质生成 + 设计经验

本 skill 是 **`mc-skin` Python 库**的适配层 + 皮肤设计经验手册。画布不限于玩家皮肤：
方块面、物品图标、披风、盔甲层都走**同一套绘制原语**（见「通用材质生成」一节）。
库是独立 PyPI 包（不绑定 pi）——先安装：

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
mc-skin harmonize skin.png --reference cape.png   # 皮肤配色并入参考图色系
mc-skin render skin.png --outdir previews
mc-skin gamedata spec sculk_sensor                # 贴图该按什么事实画
mc-skin texture sculk_sensor --color 42,77,74 -o out --scale 8   # 方块三面
mc-skin texture echo_shard --color '#29dfeb' --shape shard       # 物品图标
```

```python
from skinlib import Skin, apply_shading, apply_material, render_3d

s = Skin(size=64, model="steve")          # or "alex"
apply_shading(s, "head", (240, 190, 150, 255), "base", style="combined")
apply_material(s, "body", "leather")
s.save("skin.png")
render_3d(s, pose="walking").save("preview.png")

from skinlib import block, icon, Texture  # 非皮肤贴图，同一套原语
block((42, 77, 74, 255), noise=4).save_faces("out", "sculk")        # top/side/bottom
icon((41, 223, 235, 255), shape="shard", glow=True).save_faces("out", "echo_shard")
```

配色统一（先量再改；`retheme` 保明暗层次、`palette` 精确贴参考色号）：

```python
from skinlib import color_difference, harmonize, region_mask

color_difference("skin.png", "cape.png")                # 8.1 —— 先量
harmonize("skin.png", "cape.png").save("matched.png")   # → 4.3 —— 再改
harmonize("skin.png", "cape.png", mask=region_mask(
    "steve", 64, faces=("back",))).save("back_matched.png")   # 只改背面
```

## 原版风格对齐（可选数据层）

要让生成结果对上原版（"照原版 sculk / copper / 樱花木来"），用 `skinlib.gamedata`
—— 读的是 minecraft-data 的真实注册表，随版本走，不是硬编码猜测：

```bash
pip install "mc-skin[gamedata]"            # 可选：内嵌整个 minecraft-data，约 330 MB
mc-skin gamedata styles --version 1.21.6   # 原版风格族清单
mc-skin gamedata style sculk               # 单个族的方块/物品/自发光/粒子
mc-skin gamedata palette grass             # 各生物群系的草色（已验证的原版值）
mc-skin gamedata theme sculk               # 一个主题跨注册表全量（含不叫 sculk 的）
mc-skin gamedata formats                   # 皮肤格式事实（尺寸/模型/披风/几何）
mc-skin gamedata spec sculk_sensor         # 贴图事实：自发光/透明/tint 组/材质组/族/state
```

```python
from skinlib import gamedata as G

s = G.styles("1.21.6")["sculk"]     # 族的成员、发光项、材质组、tint
s.block_names                       # ('calibrated_sculk_sensor', 'sculk', ...)
s.glow                              # 该族里应当画成自发光的方块
G.find_block("sculk_sensor").glows  # True
G.biome_colors("grass")             # {'badlands': '#90814d', 'cherry_grove': '#b6db61', ...}
G.theme("sculk")                    # {'block': (7,), 'item': (12,), 'entity': (warden,), ...}
G.texture_spec("grass_block")       # 生成贴图要的事实：tint=grass / material / style / states
```

**配色取用纪律**：`biome_colors()` / `tints()` 是已核对原版值的 tint
（badlands 草 `#90814d`、樱花木 `#b6db61`、水 `#3f76e4`、红石按充能 `#4c0000`→`#990000`），
可直接进配色；但 `Biome.color` 字段与原版生物群系色**不符**（各主世界群系都报 `~#78a7ff`），
别拿来画。方块没有颜色数据，只有名称/材质组/发光/透明/state —— 纹理颜色得从纹理取。
`G.texture_spec(name)` 把这些事实打包好交给生成器（`mc-skin texture` 用它自动开自发光/灰度）。

未装 minebase 时库照常工作，只有取数才提示安装。

## 通用材质生成（方块 / 物品 / 披风）

皮肤之外的一切贴图共用**同一套绘制原语** —— `Texture` 是 `shading`/`patterns`/`materials`/
`overlay`/`decoration` 都接受的画布，所以不需要为贴图另写一套 API：

```python
from skinlib import Texture, block, icon, generate, from_spec

block((42, 77, 74, 255), noise=4).save_faces("out", "sculk")
# out/sculk_{top,side,bottom}.png —— 原版立方体约定：top 最亮 / bottom 最暗

icon((41, 223, 235, 255), shape="shard", glow=True).save_faces("out", "echo_shard")
# 形状来自 ICON_ART 剪影（gem/shard/ingot/dust/orb）或自备 mask=(u, v) -> bool

generate("grass_block", (124, 189, 74, 255))       # 走注册表事实：tint=grass → 自动灰度
from_spec(spec, color, style="mottled", noise=8)   # 已拿到 spec 时直接画
```

- **三面约定**：`top`×1.15 / `side`×1.0 / `bottom`×0.8 —— 先按面压明度，再上 `style=`/`material=`
- **tint 组存在时自动出灰度**（也可 `tint_ready=True` 强制）；彩色会被游戏二次染色
- **`glow=True` 是等比提亮**（游戏对发光面不做光照），不是「中心加亮」
- 常用旗标：`--style` `--material` `--shape` `--noise` `--glow/--no-glow` `--tint-ready` `--scale`
- 已有贴图直接当画布：`Texture.load("cape.png", faces=("front",))`
- **单面画布对任何面名都应答**；多面画布对未声明的面 `KeyError`（故意的，别 try 兜住）

完整约定与坑（面集必须跟着画布走、自发光不等于径向加亮、tint 灰度要在 glow 之前）→
`references/techniques.md` §18。

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
- **强调色色相分离**：能量/发光色要和主体袍色拉开色相（蓝紫配青、红配橙火、绿配黄绿），
  变体配色尤其别用同色相亮版
- **参考配色统一**：已有皮肤要和参考图（披风/logo）并色差时用 `harmonize(皮肤, 参考图)`。
  默认 `retheme` 只换色度、保住明暗 4 档（明度位移 ≈0，实测最大 |ΔL| 0.7）；`palette` 全量
  贴到参考色（ΔE→0）但会压平色阶。`region_mask(faces=("back",))` 只修实际可见的面，
  `color_difference()` 给出统一前后的 ΔE —— 先量再改，别凭肉眼猜
- **版权边界**：只沉淀通用手法，不沉淀特定皮肤/团队的配色+造型；参考图学手法不照抄

完整心法、代码模板、常见坑 → `references/techniques.md`。

**参考图源**：Noob / Herobrine 等标准 64×64 皮肤可在
[The Skindex](https://www.minecraftskins.com/) 或 [NameMC](https://namemc.com/)
搜索下载，用作算法训练与风格参考素材。本 skill 的 `examples/` 已内置
`reference_noob.png` / `reference_herobrine.png` / `reference_medieval_knight.png`
（由模板生成）。

The full API lives in the library's `skinlib/__init__.py` and README; run
`mc-skin --help` for the CLI. See `references/skin_layout.md` for the UV
coordinate map, `references/techniques.md` for the design playbook（分层/环绕/
配色/光影/骷髅/非对称/挖洞/HD 工作流/配色测量/服装提亮/§18 通用材质生成）, and
`references/blockbench_mcp_workflow.md` for driving Blockbench via MCP.
`examples/harmonize_reference.py` is a runnable measure-then-match demo.
