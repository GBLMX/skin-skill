#!/usr/bin/env python3
"""曹操 x 阿拉纳克 风格皮肤 —— 使用新版 skinlib API。

融合王者荣耀曹操（暗红袍、金纹）与星际2阿拉纳克（塔达林装甲、血红能量）。
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from skinlib import Skin, apply_shading, render_3d

# ---- 配色 ----
DARK_RED     = (120, 20, 25, 255)
BLOOD_RED    = (220, 40, 40, 255)
DARK_METAL   = (45, 45, 55, 255)
DARKER_METAL = (30, 30, 38, 255)
GOLD         = (210, 170, 60, 255)
GOLD_BRIGHT  = (240, 200, 90, 255)
GRAY_CLOTH   = (80, 70, 70, 255)
SKIN_PALE    = (170, 150, 145, 255)

s = Skin(size=64, model="steve")

# ============================================
# BASE 层：真实感着色
# ============================================
apply_shading(s, "head", SKIN_PALE, "base", style="combined")
apply_shading(s, "body", DARK_RED, "base", style="combined", noise=True, noise_var=4)
apply_shading(s, "right_arm", GRAY_CLOTH, "base", style="cylindrical")
apply_shading(s, "left_arm", GRAY_CLOTH, "base", style="cylindrical")
apply_shading(s, "right_leg", DARK_METAL, "base", style="cylindrical")
apply_shading(s, "left_leg", DARK_METAL, "base", style="cylindrical")

# ============================================
# OVERLAY 层：尖刺装甲
# ============================================
apply_shading(s, "head", DARK_METAL, "overlay", style="combined")
apply_shading(s, "body", DARKER_METAL, "overlay", style="combined")
apply_shading(s, "right_arm", DARK_RED, "overlay", style="cylindrical")
apply_shading(s, "left_arm", DARK_RED, "overlay", style="cylindrical")
apply_shading(s, "right_leg", DARK_RED, "overlay", style="cylindrical")
apply_shading(s, "left_leg", DARK_RED, "overlay", style="cylindrical")

# ============================================
# 细节：金纹 + 血红能量
# ============================================
# 头盔王冠金纹
for u in range(1, 7):
    s.pixel("head", "overlay", "front", u, 1, GOLD)
    s.pixel("head", "overlay", "front", u, 2, GOLD)
for v in range(0, 4):
    s.pixel("head", "overlay", "front", 4, v, GOLD_BRIGHT)

# 头盔顶部尖刺
for u in range(0, 8):
    s.pixel("head", "overlay", "top", u, 0, GOLD)
    s.pixel("head", "overlay", "top", u, 7, GOLD)
for u in (3, 4):
    s.pixel("head", "overlay", "top", u, 3, GOLD_BRIGHT)
    s.pixel("head", "overlay", "top", u, 4, BLOOD_RED)

# 面部血红能量纹
for u in (2, 5):
    for v in (4, 5):
        s.pixel("head", "overlay", "front", u, v, BLOOD_RED)
for u in (2, 5):
    s.pixel("head", "overlay", "front", u, 6, (255, 90, 60, 255))

# 胸口金色徽记 + 血红核心
for u in range(3, 5):
    s.pixel("body", "overlay", "front", u, 6, GOLD)
    s.pixel("body", "overlay", "front", u, 7, GOLD)
for u in range(3, 5):
    s.pixel("body", "overlay", "front", u, 3, BLOOD_RED)
    s.pixel("body", "overlay", "front", u, 4, (255, 90, 60, 255))

# 身体两侧金色装甲边 + 尖刺
for v in range(0, 12):
    s.pixel("body", "overlay", "right", 0, v, GOLD)
    s.pixel("body", "overlay", "left", 0, v, GOLD)
for v in (2, 5, 8):
    s.pixel("body", "overlay", "right", 3, v, GOLD_BRIGHT)
    s.pixel("body", "overlay", "left", 3, v, GOLD_BRIGHT)

# 臂甲金纹 + 能量
for arm in ("right_arm", "left_arm"):
    for u in range(1, 3):
        s.pixel(arm, "overlay", "front", u, 2, GOLD)
        s.pixel(arm, "overlay", "front", u, 3, GOLD)
        s.pixel(arm, "overlay", "front", u, 5, BLOOD_RED)

# 腿甲护膝金纹 + 能量线
for leg in ("right_leg", "left_leg"):
    for u in range(1, 3):
        s.pixel(leg, "overlay", "front", u, 4, GOLD)
        s.pixel(leg, "overlay", "front", u, 5, GOLD)
        s.pixel(leg, "overlay", "front", u, 8, BLOOD_RED)

s.save("cao_alarak.png")
render_3d(s, scale=6).save("cao_alarak_3d.png")
s.img.resize((512, 512), __import__("PIL").Image.NEAREST).save("cao_alarak_large.png")
print("生成 cao_alarak.png / cao_alarak_3d.png / cao_alarak_large.png")
