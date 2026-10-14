# 皮肤设计经验手册（通用技法）

> 从「死灵法师」项目多代迭代（v1→…→v5.3，以及幽匿主题版 / 披风配色统一 / 服装提亮）
> 沉淀的通用经验。
> 这些不是某个主题专属，而是任何 Minecraft 皮肤都适用的**可复用心法**。
> 配合 `skin_layout.md`（UV 坐标）和 SKILL.md 的「风格基因」表一起读。

---

## 0. 心智模型：皮肤 = base 贴肉 + overlay 罩壳

Minecraft 皮肤每部位有两层，**用途明确分工**：

| 层 | 角色 | 典型用途 |
|----|------|---------|
| `base` | 贴肉的内层（皮肤/肉体） | 肤色、脸部五官、骷髅、露出的骨头/腐肉 |
| `overlay` | 罩在外面的壳（帽/衣/袖/裤） | 兜帽、长袍、护甲、配饰、**3D 体积** |

核心推论：
- **overlay 才做 3D 体积，且会真「浮起」**。Java 版把 overlay 渲染在 base 外面
  （head 外扩 0.5、躯干四肢 0.25 voxel），画在 overlay 上的兜帽/肩甲/护腕在游戏里
  会真的鼓起来——这是皮肤唯一的原生立体机制（见 §11）。
- **透明 = 挖洞**。overlay 像素设 `Alpha=0`，游戏就不渲染，露出下面的 base（见 §8 挖洞）。
- base 里要「藏内容」：挖洞前，先把想透出的东西（骨头/腐肉/符文）画进 base，否则洞里只是平坦底色。

---

> **版权边界（红线）**：skill 只沉淀**通用手法**，不沉淀**特定皮肤/团队的配色+造型**。
> 参考他人皮肤只能学「手法/结构」，不能照抄具体配色、造型、徽记；团队/UP主皮肤
> （如 XTeamY「双色卫衣」）有版权，不可复制或沉淀成模板。
> 学习 → 提炼可迁移手法（见 §14），而非搬运成品。

---

## 1. 环绕（wrap-around）pattern

任何**绕身体一圈**的配件（腰带、护腕、护膝、肋骨、绑带），必须在**所有 4 个侧面**用**相同的 v 坐标**画，3D 视角下才会连成环：

```python
FB = ("front", "back")   # 8 宽
SD = ("left", "right")   # 4 宽
AF = ("front", "back", "left", "right")  # 全部 4 面

# 腰带环绕（body，v10-11）
for face in FB:
    for u in range(8):
        s.pixel("body", "overlay", face, u, 10, GOLD)
        s.pixel("body", "overlay", face, u, 11, GOLD_DARK)
for face in SD:
    for u in range(4):
        s.pixel("body", "overlay", face, u, 10, GOLD)
        s.pixel("body", "overlay", face, u, 11, GOLD_DARK)
```

各部位每面尺寸（64 逻辑格，128 时 ×2）：
`head` 8×8 · `body` 前/后 8×12、两侧 4×12 · `arm`/`leg` 4×12。

---

## 2. 配色纪律（最常见翻车点）

1. **近黑不可读**。`(22,20,28)` 这种近黑在游戏里糊成一团，必须提亮到可读深色
   （死灵袍从近黑 → `(70,50,92)` 可读深紫）。暗色也要保留色相，别直接用黑。
2. **每个材质配 3 档色**（亮/中/暗），再加 1 档深影，才能画光影：
   ```
   BONE       = (210,216,222)  # 中（主色）
   BONE_LIGHT = (238,242,246)  # 亮（高光）
   BONE_DARK  = (158,166,176)  # 暗（阴影）
   BONE_SHAD  = (126,134,146)  # 深影（缝/最深）
   ```
3. **单一能量强调色**，少量点缀（眼/符文/能量线），配 HOT/DIM 两档：
   ```
   CYAN     = (64,224,232)   # 主
   CYAN_HOT = (210,250,255)  # 高光（发光核心）
   CYAN_DIM = (30,130,148)   # 暗（发光衰减）
   ```
4. **配色放文件顶部命名常量**，全脚本复用，别散落魔法数字。
5. **换主题 = 整体改色温**：暖（亡魂绿/骨白米黄）↔ 冷（荧光青/冷银骨白）一套换掉，
   是比逐点重画高效得多的「reteme」。
6. **强调色要和主体拉开色相**：发光/能量色（眼/符文）不能和袍色同色相——
   蓝紫袍配青、红袍配橙火（不是正红）、绿袍配黄绿（不是正绿），否则发光「糊」进主体。
   做配色变体时最常踩：换主体色时，能量色要跟着换到**相邻色相**，不是同色相的亮版。

> 要提亮近黑、或统一两套配色的色差时，**先量再改** —— 见 §16（配色测量与统一）
> 和 §17（服装提亮）：这两件事都有实测出来的坑，凭手感改十有八九翻车。

---

## 3. 着色风格（何时用哪种）

| 风格 | 效果 | 适用 |
|------|------|------|
| `combined` | 头/身基础圆柱 | 起步/简单 |
| `cylindrical` | 四肢圆柱渐变 | 简单四肢 |
| `artistic` | 顶高光 → 底重阴影 + 布褶 + 噪点 | **手绘质感**（推荐） |
| `minimal` | 纯平无褶皱 | 极简 Noob 风 |

死灵法师最终统一到 `artistic`（`bottom_dark=0.45, noise=True`），
追求「手绘」而非「算法」感。**要点：全皮肤统一用同一种风格**，别混。

---

## 4. 光影三原则（任何细节通用）

1. **高光朝上**：任何突起物（骨头、兜帽褶皱、护甲）顶部/受光面画 `*_LIGHT`。
2. **阴影朝下**：底部/背光面画 `*_DARK`，缝隙画 `*_SHAD`。
3. **内陷加暗边**：眼窝、帽沿内、伤口边缘用深色描一圈，制造「凹进去」。

实例——骷髅脸（§5）和挖洞阴影（§8）都是这三条的应用。

---

## 5. 骷髅脸 recipe（亡灵/骷髅主题）

面部「骷髅化」三个元素缺一不可：

```python
# ① 深眼窝：近黑包围双眼（上缘+外缘+下缘）
SOCKET = (24, 26, 38, 255)
# ② 倒三角鼻影：上宽下窄指向鼻尖
# ③ 白骨下巴：牙床骨白 + 高光/阴影
```

发光眼嵌在深眼窝里才「透」，否则只是贴了两个色块。

**枯骨材质**（非纯白，更真实）：
```
SKEL      = (198,192,178)  # 米黄底
SKEL_DARK = (138,132,120)  # 中灰阴影
SKEL_GAP  = (42,38,34)     # 骨缝黑
SKEL_AGE  = (92,72,52)     # 陈年深棕污垢
```

---

## 6. 非对称制造性格

左右臂/腿**故意不同**，比对称更有「角色感」：
- 死灵法师：右手施法（袍 + 发光裂纹符文 + 手心灵魂球），左手枯骨（指骨节 + 骨护腕 + 利爪）。
- 破洞也可以只挖一边（§8 的颞骨洞只挖左脸）。

**灵魂球/发光物**：2×2 亮色块 + 中心 1 个 HOT 高光 = 托举的光球。

---

## 7. 分辨率 & HD 工作流（64 原生 + 128 HD 可选）

> **方向**：Java 原版 64 原生优先，128 是 OptiFine HD 可选升级（64 vs 128 详见 §11）。

原生 128 皮肤用两个 helper 做精细像素，**别用 `s.pixel` 画 HD 细节**（它会写 2×2 块）：

```python
def px(part, layer, face, u, v, color):
    """128 原生分辨率单像素（u/v 为精细坐标）。"""
    b = s.box(part, layer, face)
    if 0 <= u < b.w and 0 <= v < b.h:
        s.img.putpixel((b.x + u, b.y + v), color)

def rect(part, layer, face, u0, v0, u1, v1, color):
    """精细矩形 [u0,u1)×[v0,v1)。"""
    for u in range(u0, u1):
        for v in range(v0, v1):
            px(part, layer, face, u, v, color)
```

- 粗结构（大块、环绕）用 `s.pixel`（64 逻辑格，自动 ×2）。
- 精细细节（颅缝、齿、符文连笔、发丝）用 `px`/`rect`。
- **下采样到 64 用 `Image.Resampling.BOX`**（面积平均，保留细节过渡），
  不要用 `NEAREST`（会丢细节/产生锯齿）。放大预览才用 `NEAREST`。

---

## 8. 挖洞（透明透内层）—— 最进阶的「亡灵感」技法

> **玩家皮肤 alpha 三规则**（做任何透明/挖洞前必读）：
> 1. **base 层不支持透明**：透明像素游戏里渲染成**黑**（不是透出背景）。
> 2. **overlay 层半透明（alpha 1–254）不可靠**：会触发「看穿角色」渲染 bug
>    （角度相关，[MC-260451](https://bugs-legacy.mojang.com/browse/MC-260451)，1.19.4 才部分修复）；
>    Bedrock 直接强制不透明（[MCPE-46484](https://bugs-legacy.mojang.com/browse/MCPE-46484)）。
> 3. **可靠手段只有 alpha=0（全透明挖洞）和 alpha=255（不透明）二值**。
>    想「半透明」→ 用不透明色阶模拟（见 §12），别用 alpha 1–254。

用透明制造「外层破洞透出内层」的悬浮立体感，三步走：

**第一步 · 先画内层**（base 里画好要透出的内容）：
```python
# 左腰肋骨（BASE），伤口透出枯骨 + 腐肉
for v in range(4, 9):
    s.pixel("body", "base", "left", 1, v, BONE)
    s.pixel("body", "base", "left", 2, v, BONE_DARK)
```

**第二步 · 挖洞**（overlay 设透明，锯齿状不规则，别挖整齐矩形）：
**第三步 · 加阴影**（骗过眼睛的立体感）：

```python
TRANSPARENT = (0, 0, 0, 0)

def punch_hole(part, face, cells, rim, base_top=None, base_bottom=None):
    """挖洞：overlay 破洞透明 + 边缘暗线 + 内层上下投影。"""
    b = s.box(part, "overlay", face)
    w, h = b.w // s.scale, b.h // s.scale
    cells = set(cells)
    for u, v in cells:                       # ① 破洞 → 透明
        s.pixel(part, "overlay", face, u, v, TRANSPARENT)
    for u, v in cells:                       # ② 边缘暗线 = 布料厚度
        for du, dv in ((1,0),(-1,0),(0,1),(0,-1)):
            nu, nv = u + du, v + dv
            if (nu, nv) not in cells and 0 <= nu < w and 0 <= nv < h:
                s.pixel(part, "overlay", face, nu, nv, rim)
    if base_top is not None:                 # ③ 内层投影：上沿暗
        vmin = min(v for _, v in cells)
        for u, v in cells:
            if v == vmin:
                s.pixel(part, "base", face, u, v, base_top)
    if base_bottom is not None:              # ④ 内层受光：下沿亮
        vmax = max(v for _, v in cells)
        for u, v in cells:
            if v == vmax:
                s.pixel(part, "base", face, u, v, base_bottom)

# 调用：兜帽顶破洞（透出颅顶），rim=HOOD_DARK，上暗下亮
punch_hole("head", "top",
    [(2,1),(3,1),(4,1),(3,2),(4,2),(5,2),(3,3),(4,3),(5,3),(4,4)],
    HOOD_DARK, BONE_SHAD, BONE_LIGHT)
```

要点：
- **破洞形状用手排的锯齿/斜向坐标**，模拟撕裂，不要矩形。
- **内层别画满纯色**：洞下面要有具体细节（骨节/腐肉/符文），否则只是「深色平地」。
- 高对比拉开层次：外层暗（暗袍）+ 内层亮（骨白）= 强烈悬浮感。
- 高光可只露在破洞边缘（如青色水晶），光像从里面透出来。

---

## 9. 迭代工程学（过程经验）

1. **整合进单一脚本**：v1/v2 两代分脚本，主题衔接生硬；v3 起整合进一个脚本，
   每次迭代复制上一版、整体改，主题一致。
2. **配色放顶部命名常量**（§2），改主题只动配色块。
3. **固定输出集**：64 主皮肤（原生）+ 512 放大（NEAREST）
   + 4 个 3D 预览（natural / back=yaw180 / side=yaw90 / aiming）；
   128 HD 是 OptiFine 可选，非默认。
4. **每个版本存档**：`vN_xxx/` 目录 + 版本前缀脚本 + README 时间线，可回滚可对比。
5. **对称补完**：定向 patch 只做半边（如只优化右腿）会烂尾成「没做完」，迭代要左右对称收尾。
6. **配色变体用源码字符串替换**：换主题色改顶部常量重跑（`apply_shading` 会按新色重生成渐变），
   别对最终 PNG 像素级替换（渐变中间色对不上）；外部 paste 的像素（如从旧版提取的 face）
   不在常量替换范围，需额外做像素级 remap。

---

## 10. 常见坑速查

| 坑 | 症状 | 解法 |
|----|------|------|
| 近黑配色 | 游戏里糊成一团 | 提亮到可读深色，保留色相 |
| `NEAREST` 下采样 | 64 版丢细节/锯齿 | 用 `Resampling.BOX` |
| 挖洞下面没内容 | 洞透出平坦底色 | 先画 base 内层（§8 第一步） |
| 配件只画一面 | 3D 视角断开 | 环绕 pattern（§1）全 4 面 |
| 破洞是整齐矩形 | 不像撕裂 | 手排锯齿坐标 |
| 骨头纯白 | 塑料感 | 米黄/冷灰 + 污垢 + 骨缝 |
| 发光物无 HOT 高光 | 不「亮」 | 中心加 `*_HOT` |
| 混合着色风格 | 风格割裂 | 全皮肤统一一种 style |

---

## 11. Java 版 3D（overlay 浮起）—— 皮肤唯一的原生立体

Java 版皮肤没有模型/动效，「立体感」只来自一个机制：**第二层（overlay）浮起**。

- 64×64 皮肤每个部位有 `base`（贴肉）+ `overlay`（hat/jacket/sleeve/pants）两层。
- 游戏渲染时 overlay 浮在 base 外面：**head 外扩约 0.5 voxel，body/arm/leg 约 0.25**。
- 想「鼓起来」的东西（兜帽、肩甲、护腕、骨刺角、悬空灵魂球）画 overlay；
  「贴肉」的东西（骷髅脸、骨头、腐肉、皮肤）画 base。分错层 = 3D 全没。

**渲染器陷阱**：skinlib 早期 `render_3d` 把 overlay `alpha_composite` 平铺回 base，
预览图是「贴平」的假 3D。现已改为双层渲染（overlay 外扩后单独投影），预览能反映
真实浮起。若预览看不出立体，先查渲染器是否真浮起了 overlay，而不是盲目改纹理。

**64 vs 128**：Java 原版只认 64×64，128 是 OptiFine HD。做「Java 版皮肤」用
`Skin(size=64)` 原生设计；128 只是可选 HD 升级，别用「128 原生→64 下采样」反向流程。

**3D Skin Layers（mod）**：把第二层 extrud 成真 3D voxel（比原版 0.5px 浮起更立体）。
- **只支持 64**（官方 FAQ「Does this work with HD Skins? No」）——又一个必须 64 原生的理由。
- overlay 配件要**四面环绕完整**，extrud 后才是立体块，不是碎面。
- 12 blocks 外自动切回 vanilla 2D，所以 overlay 在 vanilla 渲染下也要自洽（分好 base/overlay）。
- 已知 issue：破洞锯齿角落会「连起来」（ZigZag join up），可用半透明像素填充缓解——
  但半透明又踩 §8 规则 2，权衡时优先保 vanilla 兼容（用 0/255）。

---

## 12. 半透明替代：不透明色阶消散

玩家皮肤做不了半透明（§8 规则 3），想表现「幽灵化 / 消散 / 淡出」，用**不透明色阶渐变**
模拟：从实体色逐级过渡到「幽灵色」，靠明度台阶制造淡出感，而不是降 alpha。

```python
# 死灵法师 5.0：双腿小腿「消散成灵体」（4 个不透明台阶，自下而上变虚）
GHOST_3 = (70, 74, 104, 255)     # 深灰蓝（最实，接近袍）
GHOST_2 = (100, 106, 138, 255)   # 中灰蓝
GHOST_1 = (150, 156, 180, 255)   # 幽灵白（最虚）
for v, c in ((8, ROBE_LIMB), (9, GHOST_3), (10, GHOST_2), (11, GHOST_1)):
    for face in ("front", "back", "left", "right"):
        for u in range(4):
            s.pixel(leg, "base", face, u, v, c)
```

要点：
- 消散色阶每材质 **2–4 个不透明台阶**，明度单调变化（实体→虚），别跳变。
- 消散方向自下而上（脚底最虚）最自然，模拟「正在化为灵体 / 消散」。
- 消散色阶保留材质色相（红袍→红灰、绿袍→绿灰），别换色相。
- 色阶消散和挖洞（§8）可叠加：挖洞透骨 = 实体破损，色阶消散 = 灵体淡出。

---

## 13. 头发 & 帽子 3D（双层发 + 发丝分离）

头发/帽子的立体感，核心手法（从 The Skindex 参考皮肤提炼）：

1. **双层头发**：`base` 贴肉发（内层）+ `overlay` 浮起发束（外层）。
   overlay 发束在 3D Skin Layers 下 extrud 成真 3D 发量，两层重叠才「厚」。

2. **发梢渐深（不是消散）**：发束末端用**深色**（发色暗档）表现垂落阴影，不是变淡消散。
   参考：yyy 发色青 `(36,144,155)` → 发梢深青 `(25,100,108)`。
   消散（§12）适合「身体化为灵体」，发梢垂落用「渐深」更自然。

3. **发丝挖空分离**：overlay 发束间挖透明缝（如每隔 2 列挖 1 列透明），
   让 base 发透出，形成「一缕缕」而非「一整块」的发束。参考 steve(4) 的断续发丝。

4. **帽子不包死**：帽子画在 overlay（浮起），但别把 head 包满——留四周头发垂落空间。
   参考 yyy：帽子只在 overlay top 一顶，四周全露头发。

5. **发色和帽色分色相**：发色、帽色用不同色系（青发+金帽 / 绿发+粉饰 / 青发+紫帽），
   层次靠色相对比，不是靠明暗硬分。

---

## 14. 参考图逆向学习（学手法，不照抄）

从参考皮肤提炼可迁移手法的流程（版权边界见 §0 总则）：

1. **逐面逐 v 提取主色**：用 skinlib 或 PIL 打印 head/body 各面主色，识别
   「发色 / 帽色 / 肤 / 衣 / 裤」分别是什么、画在哪层。
2. **识别分层**：看「头发/帽子」画在 base 还是 overlay——浮起的在 overlay，贴肉的在 base。
3. **提炼手法，不是配色**：抄「双层发 + 发梢渐深 + 发丝挖空」这类**结构手法**，
   不抄对方的「青色+金色」具体配色。手法可迁移，配色是别人的创作。
4. **归纳共性**：看 2-3 个参考图，找共同手法（如都「发梢渐深」），共性才是可复用经验。

```python
# 逆向分析参考图的 head base front 主色
from PIL import Image
from collections import Counter
im = Image.open("ref.png").convert("RGBA")
for v in range(8):
    row = [im.getpixel((8+u, 8+v))[:3] for u in range(8)]
    print(v, Counter(row).most_common(2))
```

---

## 15. 像素逐行诊断（定位层次冲突）

层次出问题（谁遮了谁、挖洞漏了、颜色不对）时别猜，逐面逐 v 打印 base/overlay 实际像素：

```python
from skinlib import Skin
s = Skin.load("skin_64.png")
for face in ("front", "back", "left", "right"):
    print(face, "base ", [s.get_pixel("left_arm", "base", face, 1, v)[:3] for v in range(12)])
    print(face, "over ", [s.get_pixel("left_arm", "overlay", face, 1, v)[:3] for v in range(12)])
```

要点：
- base 和 overlay **并排对比**，才能看出 overlay 遮没遮 base。
- 查透明：`[3]==0` 是挖洞，`0<[3]<255` 是半透明（§8 规则 2 会看穿）。
- 常见冲突：挖洞覆盖了发梢/配件、护腕只画单面（环绕不完整）、base 留了肤色而非该有的内层。

---

## 16. 配色测量与统一（先量再改）

「这个皮肤和披风不搭」是**可测量的**，别凭肉眼猜。库里有现成工具：

```python
from skinlib import color_difference, harmonize, harmonize_report, region_mask

color_difference("skin.png", "cape.png")                # 8.1 —— 平均 ΔE（CIE76）
harmonize("skin.png", "cape.png").save("matched.png")   # → 4.3
```

`ΔE` 读法：**< 2 基本看不出，> 5 明显**。

### 三条测量纪律（都踩过坑）

1. **参考色板取精确色，不要量化。** `palette_of_image(..., quantize=False)`；`harmonize`
   和 `color_difference` 内部已经这样。默认的 16 级合并会把披风的 `#FDFB9A` 压成
   `#F0F090`（整体偏暗），统一效果实测量差一档（6.2 → 4.3）。
2. **两边色数要对等。**「到最近参考色的平均 ΔE」会随图像色数增多而变小 —— 184 色的
   皮肤和 12 色的披风直接比，皮肤必然"看起来更忠实"（1.8 vs 9.8，**假象**）；各取前
   12 个主色再比才站得住（3.1 vs 9.4，**真象**）。这是最容易骗到自己的一个陷阱。
3. **两条轴都量**：目标 ↔ 参考（要统一的），以及各自 ↔ **原版基准**（要保血统的）。
   改 A 去就 B 一定在另一条轴付代价，量清楚才好取舍。

### 两种模式：换色度 vs 换色板

| mode | 允许动什么 | 用在 |
|------|-----------|------|
| `retheme`（默认） | **只换色度，明度不动** | 手绘分层皮肤 —— 4 档梯度原样保留（实测最大 \|ΔL\| 0.7） |
| `palette` | 整体贴到参考色号（含明度） | 就要颜色**等于**参考色号；层次被压平（实测最大 \|ΔL\| 20.6） |

`strength` 0~1 连续可调；不够就调，不用重画。

**方向要想清楚**：色差大的一方通常是"偏离方"，把忠实的一方拉过去会洗掉它的身份。
偏离方若在你手上（自己的披风/logo），改它往往两条轴同时变好。

### 只改看得见的地方

```python
back = region_mask("steve", 64, parts=("body", "left_leg", "right_leg"),
                   layers=("base",), faces=("back",))
report = harmonize_report("skin.png", "cape.png", mode="retheme", mask=back)
report["delta_before"], report["delta_after"]   # 6.3 → 2.4（都在该区域内测）
report["image"].save("back_matched.png")
```

披风挂在背后就只改背面；护腕/护膝只改 overlay 层。`harmonize_report` 的前后值按同一个
mask 测，可直接比较。CLI：`mc-skin harmonize skin.png --reference cape.png [--mode palette]
[--strength 0.6] [--faces back]`。

---

## 17. 服装提亮（把「近黑不可读」救回来）

§2 第 1 条说近黑不可读，但**改法本身有两个坑**（幽匿版实战）：

### 坑 1：明度要「整体偏移」，不要往目标值挤压

```
L* 4 / 5 / 9 / 15 / 25  →  挤向目标 L*29：17 / 18 / 20 / 23 / 27  ✗ 每档只差 1~2，梯度没了
L* 4 / 5 / 9 / 15 / 25  →  整体 +16：     20 / 21 / 25 / 31 / 41  ✓ 梯度原样保留
```

```python
from skinlib.harmonize import lab_to_rgb, rgb_to_lab

def lift(rgb, delta, blue, ref=(9, 47, 70)):
    """整体上移 L*，色度按 blue 混向参考色（此处用披风的偏蓝暗色）。"""
    light, a, b = rgb_to_lab(rgb)
    _, ra, rb = rgb_to_lab(ref)
    return lab_to_rgb((light + delta, a + (ra - a) * blue, b + (rb - b) * blue))[:3]
```

### 坑 2：按色号换会漏掉大半

实测：躯干+四肢 1701 个不透明像素里**只有 16% 精确等于那 5 个服装常量**，71% 是
着色器算出来的**渐变混合色**（`artistic` 是连续色阶）。按色号换漏掉 56% 的袍面，
结果「看着几乎没变」。

**正解：按「离哪一档调色板常量最近」（Lab）给像素贴标签**，只提目标材质那几档 ——
渐变色跟着它所属的材质走，兄弟材质（甲片/腰带/腐肉）由各自的标签护住：

```python
PALETTE = {(6,14,16): "garment", (13,18,23): "garment", (17,27,33): "garment",
           (5,42,50): "garment", (3,65,80): "garment",
           (64,87,108): "plate",   (40,54,68): "plate",    # 甲片 + 它的阴影
           (187,195,155): "bone",  (0,146,149): "glow",     # …其余照常列全
           }
LAB = [(rgb_to_lab(c), name) for c, name in PALETTE.items()]

def label(rgb):
    lab = rgb_to_lab(rgb)
    return min(LAB, key=lambda p: sum((x - y) ** 2 for x, y in zip(lab, p[0])))[1]
```

### 两个边界（实测出来的）

- **同一色号跨材质就分不开**：`#0D1217` 既是袍体阴影又是**骨缝**，`#060E10` 既是袍体
  深影又是**眼窝**。眼窝靠**区域**保护（head/base 整块跳过），骨缝只能接受一起变亮
  （L*5→21；骨头在 L*60+，缝隙照读得出）。
- **别让兄弟材质被「抬过头」**：单靠「L* < 34 且 b* < 0」这种亮度条件，会把甲片阴影
  `#283644`（L*22）也抬到 L*38，**反超甲片本体** `#40576C`（L*36），立体感倒置。
  按标签归类自然避开。

### 收尾：用不变量验，别只看图

```python
changed = [(x, y) for y in range(64) for x in range(64) if a[x, y] != b[x, y]]
assert changed                                            # 该动的真动了
assert all(a[p] == b[p] for p in face_pixels)             # 脸 0 改动
assert all(a[x, y][3] == b[x, y][3] for x, y in changed)  # alpha 不变
```

三档实测验收（每档改 1313 像素）：脸 0 / 骨头 0 / 荧光 0 / 甲片 0 / 腰带 0 / 腐肉 0
改动，alpha 一致，单像素最大 ΔL* = 请求值（10.2 / 16.2 / 22.2）。

## 18. 通用材质生成（非皮肤贴图）

皮肤之外的一切贴图 —— 方块面、物品图标、披风、盔甲层 —— 用的是**同一套绘制原语**。
`shading`/`patterns`/`materials`/`overlay`/`decoration` 从来不需要「皮肤」，只需要一块能回答
`region`/`box`/`pixel`/`get_pixel` 并且说明自己**有哪些面**的画布：`Texture` 就是这块画布。

```python
from skinlib import Texture, block, icon
from skinlib.overlay import runes

# 一个立方体真正要画的三张（side 四面复用）
t = block((42, 77, 74, 255), style="combined", noise=4)   # 48x16: top/side/bottom
runes(t, "all", (127, 255, 212, 255), count=2, seed=3)    # 原语直接作用在上面
t.save_faces("out", "sculk", scale=1)                     # out/sculk_top.png ...

icon((41, 223, 235, 255), shape="shard", glow=True).save_faces("out", "echo_shard")

# 已有的贴图也能当画布用
cape = Texture.load("cape.png", faces=("front",))
```

原版约定（是画法规则，不是注册表数据）：

| 约定 | 做法 |
|------|------|
| 尺寸 | 方块/物品 16×16；披风/鞘翅/盔甲层 64×32；`texture_size(kind)` 查表 |
| 立方体三面 | `top` 最亮（×1.15）、`side` 居中（×1.0）、`bottom` 最暗（×0.8）。**先按面压明度，再上风格** —— 扁平的 16×16 才有立体感 |
| 生物群系 tint 贴图 | 画成**灰度**，运行时由游戏乘 tint。画成彩色 = 游戏里被二次染色（`tint_ready=True`） |
| 自发光贴图 | 整体等比抬亮（`glow=True`）。游戏对这些面本来就不做光照，所以这是**可读性**提亮，不是模拟光照 |
| 物品图标 | 形状来自**剪影**而非矩形，留 1px 透明边距；只有遮罩内的像素参与后续所有 pass |

**坑**（实测）：

- **面集必须跟着画布走**。原语是「逐面」绘制的；一块单面画布若被当成 6 面画，同一片像素会被
  叠画 6 遍（噪点/划痕密度直接 ×6）。`model.canvas_faces()` 让画布声明自己的面，`Skin` 仍是
  6 面 —— 新增画布类型时必须尊重它。
- **自发光不是「中心加亮」**。`glow_center` 用径向渐变**整体替换**像素：皮肤上做水晶可以，
  拿它当自发光会把刚画好的面间明暗关系清零。要等比提亮（保比例、顶端自然截断）。
- **tint 灰度要在自发光/噪点之前做**，否则 glow 的颜色会被灰度抹平（反了就等于白做）。
- **单面画布对任何面名都应答**（`paint_face(part, layer, "all", ...)` 这类写法才顺手），
  多面画布遇到未声明的面会 `KeyError` —— 这是故意的，别用 `try` 兜住。

注册表侧（`gamedata`）不给颜色、也不给贴图路径，只给**事实**：`texture_spec(name)` 返回
kind / 尺寸 / 自发光 / 透明 / tint 组 / 材质组 / 风格族 / state 列表。完整生成入口：

```bash
mc-skin gamedata spec grass_block                     # 先看事实：tint=grass
mc-skin texture grass_block --color 124,189,74 -o out --scale 8
```

`--color` 必须自己给（方块没有颜色数据）；tint 组存在时自动输出灰度。state 列表提示
「这个方块有几套变体」，但**变体贴图的文件名不在数据里**，别去猜。

