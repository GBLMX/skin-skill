# 看与筛:生成材质的预览手法

生成完贴图,要回答的不是「好不好看」,而是三条**可判定**的问题:

1. **剪影可读吗**(物品图标:形状撑不撑得住 16×16)
2. **明度关系读起来像立方体吗**(方块:顶亮/底暗有没有出来)
3. **tint 灰度、自发光、透明对不对**(灰度是否真的 R=G=B、发光面是否被提亮)

这三条**都能在 2D 像素层判定**。真 3D 渲染只服务第四个问题:「要像游戏里一样」。

## 1. 接触表:批量筛 AI 产物(主战场)

几十张产物一屏看完,先扔掉配色跑偏/剪影糊掉的那些。纯 Pillow,零依赖:

```python
from pathlib import Path
from PIL import Image

def contact_sheet(paths, cols=8, cell=64, pad=8, bg=(24, 24, 28, 255)):
    """把一批贴图放大拼成一张联络表,按文件名排序。"""
    paths = sorted(Path(p) for p in paths)
    rows = (len(paths) + cols - 1) // cols
    sheet = Image.new("RGBA", (cols * (cell + pad) + pad,
                               rows * (cell + pad) + pad), bg)
    for i, p in enumerate(paths):
        img = Image.open(p).convert("RGBA").resize((cell, cell), Image.NEAREST)
        sheet.alpha_composite(img, (pad + (i % cols) * (cell + pad),
                                    pad + (i // cols) * (cell + pad)))
    return sheet, [p.name for p in paths]
```

要点:**`NEAREST` 放大**(像素艺术上双线性会骗你);背景给中性深色(否则透明像素看不见);
**务必把「第几张 = 哪个文件」对上** —— 否则筛出来也不会知道该去改哪张。

## 2. 等轴测立方体:看明度关系(次战场)

`block()` 的三张面单独看都不错,只有拼成立方体才看得出「顶亮/底暗」到底读不读得出来。
工具只有一个:把矩形贴图**仿射贴到平行四边形**(正交投影下,一个面就是一次仿射,无畸变)。

```python
def _paste_quad(canvas, tex, tl, tr, bl, br):
    (x0, y0), (x1, y1), (x2, y2), (x3, y3) = tl, tr, bl, br
    w, h = tex.size
    den = (x1 - x0) * (y2 - y0) - (x2 - x0) * (y1 - y0)
    if abs(den) < 1e-9:
        return
    a, b = w * (y2 - y0) / den, -w * (x2 - x0) / den
    d, e = -h * (y1 - y0) / den, h * (x1 - x0) / den
    c, f = -a * x0 - b * y0, -d * x0 - e * y0
    mnx, mny = int(min(x0, x1, x2, x3)), int(min(y0, y1, y2, y3))
    mxx, mxy = int(max(x0, x1, x2, x3)) + 1, int(max(y0, y1, y2, y3)) + 1
    mapped = tex.transform((mxx - mnx, mxy - mny), Image.AFFINE,
                           (a, b, a * mnx + b * mny + c,
                            d, e, d * mnx + e * mny + f), Image.NEAREST)
    canvas.alpha_composite(mapped, (mnx, mny))
```

完整可跑版本(含坐标摆放、两侧明暗、自检输出):`examples/texture_preview.py`

```bash
python examples/texture_preview.py --color 42,77,74              # 自造方块
python examples/texture_preview.py --name sculk_sensor --color 42,77,74
python examples/texture_preview.py --input out/*.png -o previews # 只拼接触表
```

**自检不变量**:立方体上色像素数必须**恰好等于 3×面宽²** —— 多了说明面叠了,少了说明有缝。
实测(16px 面 ×10 放大 → 面宽 160):**76 800 = 3×160×160** ✓,
且顶面中心取到 top 贴图的原始像素、西面 = side×0.72、东面 = side×1.0 ✓。
库里的 `render._paste_affine` 是同一套数学(皮肤 3D 在用),但它是私有的 —— 示例自带一份,
好让装了 PyPI 版 `mc-skin` 的人也能直接跑。

## 3. 只有要「像游戏里一样」时,才上外部渲染器

**唯一推荐:[block-model-renderer](https://github.com/ewanhowell5195/block-model-renderer)**
—— 浏览器/Node,**能渲染任意自定义模型 JSON 并吃自带贴图**,生态成熟。最小用法:
我们的 PNG + 一个立方体模型 JSON(十几行)→ 浏览器里喂给它 → 转/导出 PNG。

**不要**为了这个把 Node 引进 Python 包:它是**人工确认**工具,不是流程依赖。

| 工具 | 输入 | 为什么(不)选 |
|------|------|---------------|
| `block-model-renderer` | 任意模型 JSON + 贴图 | 唯一「吃我们自己的 PNG」且成熟的 |
| `cubane` | 整套原版资源包 | 要方块状态/动画时才值得 |
| `minecraft-render` | **只能是 .jar** | 出原版方块画廊极好(`npx ... -f <regex>` + 多进程),对我们生成的裸 PNG 无效 |
| `mantle-renderer` | 模型 JSON + 贴图 URL | API 最贴(`parseJavaBlockModel` + `screenshot()`),但仅 2⭐、无头要 Xvfb |
| `minecraft-render-py` | jar | Python 只是薄壳,引擎仍是 Node+THREE,无头要 Xvfb —— 更重 |
| `skinview3d` | 皮肤/披风 | 重复:皮肤我们有 `render_3d` |
| `Lodestone` | `.litematic` | 结构与贴图无关 |
| 各类 viewer / Resource Pack Creator | 人工点选 | 无自动化接口:抽查可以,不进流程 |

## 4. 给 agent 的三条纪律

- **能用数值判定就别靠眼睛**:明度顺序(顶>侧>底)、`r==g==b`(tint 灰度)、alpha 值、
  立方体像素数 —— 这些是断言,不是印象。
- **看不到图像时不要写「我看过了」**。图像常被工具链丢弃;要把「看图」这件事交给用户,
  agent 的结论只能建立在可复现的数值上。
- **预览产物要留住**:`contact.png` / `cube.png` 连同面文件一起给出,用户才能复核你的判断。
