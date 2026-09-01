#!/usr/bin/env python3
"""灵能_吸血鬼（Psionic Vampire）—— 基于 cao_alarak 用新 skill 生成。

在曹操×阿拉纳克（cao_alarak）的设计语言基础上，改用 mc-skin 的材质系统
(apply_material)、遮罩叠加 (apply_overlay)、光影档案 (apply_style) 重新实现，
主题转为「灵能吸血鬼」：苍白亡者肤色 + 暗红长袍 + 铁黑护甲 + 血红 + 灵能紫
（发光紫瞳、符文、能量线）。

输出：psionic_vampire.png / psionic_vampire_3d.png / psionic_vampire_large.png。
"""

from PIL import Image

from skinlib import (
    Skin, apply_shading, apply_style, apply_material, apply_overlay,
    face, hair, band, render_3d,
)

# ============================================================
# 配色
# ============================================================
PALE_SKIN   = (170, 150, 145, 255)   # 苍白亡者肤色
ROBE        = (60, 22, 34, 255)      # 暗红长袍
ROBE_DARK   = (42, 14, 24, 255)
BLOOD_RED   = (180, 30, 40, 255)     # 血红
BLOOD_HOT   = (240, 60, 60, 255)     # 血红高光
IRON        = (45, 45, 55, 255)      # 铁黑护甲
IRON_DARK   = (28, 28, 38, 255)
BONE        = (210, 200, 180, 255)   # 骨白
PSIONIC     = (120, 60, 160, 255)    # 灵能紫
PSIONIC_HOT = (190, 100, 230, 255)   # 灵能紫高光

s = Skin(size=64, model="steve")

# ============================================================
# BASE 层：材质着色
# ============================================================
apply_shading(s, "head", PALE_SKIN, "base", style="combined")
apply_material(s, "body", "leather", color=ROBE)          # 暗红袍（皮革褶皱）
apply_material(s, "right_arm", "metal", color=IRON)       # 铁臂甲
apply_material(s, "left_arm", "metal", color=IRON)
apply_material(s, "right_leg", "metal", color=IRON)
apply_material(s, "left_leg", "metal", color=IRON)

# 脸（灵能紫瞳）+ 暗紫黑发
face(s, eye_color=PSIONIC, brow_color=(50, 32, 46, 255),
     mouth_color=(110, 54, 66, 255))
hair(s, (44, 32, 52, 255), light=(70, 50, 80, 255), dark=(20, 15, 30, 255))

# ============================================================
# OVERLAY 层：护甲
# ============================================================
apply_material(s, "body", "metal", layer="overlay", color=IRON_DARK)  # 铁胸甲
apply_material(s, "right_arm", "metal", layer="overlay", color=BLOOD_RED)
apply_material(s, "left_arm", "metal", layer="overlay", color=BLOOD_RED)
apply_material(s, "right_leg", "bone", layer="overlay", color=BONE)    # 骨护膝
apply_material(s, "left_leg", "bone", layer="overlay", color=BONE)

# ============================================================
# 灵能符文（遮罩叠加）+ 血红细节
# ============================================================
apply_overlay(s, "body", "runes", color=PSIONIC_HOT, layer="overlay", seed=6)
apply_overlay(s, "head", "runes", color=PSIONIC_HOT, layer="overlay", seed=3)

# 血红发箍（环绕头部）
band(s, "head", 1, 2, BLOOD_RED, layer="overlay")

# 胸口血红能量核心
for u in (3, 4):
    s.pixel("body", "overlay", "front", u, 6, BLOOD_HOT)
    s.pixel("body", "overlay", "front", u, 7, BLOOD_RED)

# 高领血红袍领
for u in range(8):
    s.pixel("body", "overlay", "front", u, 0, BLOOD_RED)
    s.pixel("body", "overlay", "back", u, 0, BLOOD_RED)

# 臂甲灵能符文
for arm in ("right_arm", "left_arm"):
    for u in (1, 2):
        s.pixel(arm, "overlay", "front", u, 6, PSIONIC)
        s.pixel(arm, "overlay", "front", u, 7, PSIONIC_HOT)

# 骨护膝灵能符文
for leg in ("right_leg", "left_leg"):
    s.pixel(leg, "overlay", "front", 1, 4, PSIONIC)
    s.pixel(leg, "overlay", "front", 2, 4, PSIONIC_HOT)

# ============================================================
# 输出
# ============================================================
s.save("psionic_vampire.png")
render_3d(s, scale=6, pose="natural").save("psionic_vampire_3d.png")
s.img.resize((512, 512), Image.Resampling.NEAREST).save("psionic_vampire_large.png")

print("生成 psionic_vampire.png / psionic_vampire_3d.png / psionic_vampire_large.png")
