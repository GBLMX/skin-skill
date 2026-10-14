#!/usr/bin/env python3
"""配色统一示例：先量出色差，再把一张皮肤的色系并到参考图上。

参考图只被读「用了哪些颜色」的统计量 —— 大小随意，小到一条 1px 色条都行，
所以「披风/logo」不需要是同尺寸贴图；没有参考贴图时，用调色板常量拼一条色条即可。

输入是 examples/ 里两张库自生成图（MIT 覆盖，见 examples/README.md），
输出写当前目录：`matched_retheme.png` / `matched_soft.png` / `matched_palette.png`
（各带一张 512×512 的 `_large` 预览）+ `matched_palette_strip.png`。

读法：ΔE < 2 基本看不出，> 5 明显。`retheme` 只换色度、保住明暗层次；
`palette` 让颜色精确等于参考色号，但会压平层次。
"""

from pathlib import Path

from PIL import Image

from skinlib import color_difference, harmonize, harmonize_report, region_mask
from skinlib.palette import CLOTHING, ENERGY

HERE = Path(__file__).resolve().parent
TARGET = HERE / "reference_noob.png"                # 要被统一的那张
REFERENCE = HERE / "reference_medieval_knight.png"  # 参考图（另一张皮肤）


def swatch(colors):
    """一组色号 → 1px 高的参考色条：没有参考贴图时拿它当参考图。"""
    img = Image.new("RGBA", (len(colors), 1))
    for i, color in enumerate(colors):
        img.putpixel((i, 0), (*color[:3], 255))
    return img


def main():
    print(f"目标 {TARGET.name} ← 参考 {REFERENCE.name}")
    print(f"  原始色差 ΔE {color_difference(TARGET, REFERENCE):.1f}")

    for suffix, kwargs in (("retheme", {}),                       # 默认：保梯度
                           ("soft", {"strength": 0.6}),           # 轻一点
                           ("palette", {"mode": "palette"})):     # 硬统一
        out = harmonize(TARGET, REFERENCE, **kwargs)
        out.save(f"matched_{suffix}.png")
        out.resize((512, 512), Image.Resampling.NEAREST).save(
            f"matched_{suffix}_large.png")
        print(f"  {suffix:<8} → matched_{suffix}.png   "
              f"ΔE {color_difference(out, REFERENCE):.1f}")

    # 只改看得见的地方：例如披风挂在背后就只改背面 faces=("back",)
    size = Image.open(TARGET).size[0]
    mask = region_mask("steve", size, parts=("body",))
    report = harmonize_report(TARGET, REFERENCE, mask=mask)
    print(f"  只改躯干：ΔE {report['delta_before']:.1f} → "
          f"{report['delta_after']:.1f}（都在躯干内测）")

    # 没有参考贴图时：用调色板常量拼一条色条当参考
    strip = swatch([CLOTHING["black"], CLOTHING["dark_gray"],
                    CLOTHING["gray"], ENERGY["ice"]])
    out = harmonize(TARGET, strip)
    out.save("matched_palette_strip.png")
    print(f"  按色号统一（无参考图）→ matched_palette_strip.png   "
          f"ΔE {color_difference(out, strip):.1f}")


if __name__ == "__main__":
    main()
